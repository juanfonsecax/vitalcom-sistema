"""La cola de escritura con latido y la bitácora de corridas (diseño Hito 3, §3.3 y §3.9)."""

from __future__ import annotations

import ast
import os
import threading
import time
from pathlib import Path

import pytest

from vitalcom_app import bitacora, escrituras

PAQUETE = Path(__file__).resolve().parents[1] / "vitalcom_app"


@pytest.fixture()
def ritmo_rapido(monkeypatch):
    monkeypatch.setattr(escrituras, "SONDEO_S", 0.02)
    monkeypatch.setattr(escrituras, "LATIDO_S", 0.02)


# ── la cola ───────────────────────────────────────────────────────────────────

def test_lock_con_latido(sistema_de_juguete):
    """Un candado vivo no se borra aunque lleve 150 s; uno sin latido por más de 120 s sí."""
    candado = escrituras._archivo_de_lock()
    with escrituras.Cola():
        ahora = time.time()
        # el dueño late: el candado tiene un mtime reciente, aunque «desde» sea de hace mucho
        assert not escrituras.candado_abandonado(candado, ahora + 100)
        assert escrituras.candado_abandonado(candado, ahora + 150), (
            "sin latido por más de 120 s se considera de un proceso muerto"
        )
    assert not candado.exists()


def test_el_latido_toca_el_candado_mientras_dura_el_turno(sistema_de_juguete, ritmo_rapido):
    with escrituras.Cola():
        candado = escrituras._archivo_de_lock()
        primero = candado.stat().st_mtime_ns
        time.sleep(0.3)
        assert candado.stat().st_mtime_ns > primero


def test_un_candado_sin_latido_lo_toma_el_siguiente(sistema_de_juguete):
    candado = escrituras._archivo_de_lock()
    candado.write_text("{}", encoding="utf-8")
    viejo = time.time() - 200
    os.utime(candado, (viejo, viejo))
    with escrituras.Cola():
        assert candado.exists()


def test_un_candado_con_latido_reciente_no_se_le_quita_al_dueno(sistema_de_juguete):
    candado = escrituras._archivo_de_lock()
    candado.write_text("{}", encoding="utf-8")
    with pytest.raises(escrituras.SistemaOcupado):
        with escrituras.Cola():
            pass
    assert candado.exists(), "el candado del otro no se toca"
    candado.unlink()


def test_sin_esperar_falla_enseguida_y_diciendolo(sistema_de_juguete):
    with escrituras.Cola():
        with pytest.raises(escrituras.SistemaOcupado):
            with escrituras.Cola():
                pass


def test_esperar_toma_el_turno_cuando_el_otro_termina(sistema_de_juguete, ritmo_rapido):
    ocupado = threading.Event()
    orden: list[str] = []

    def primero():
        with escrituras.Cola(job_id="a" * 32):
            ocupado.set()
            orden.append("a-adentro")
            time.sleep(0.3)
            orden.append("a-sale")

    hilo = threading.Thread(target=primero)
    hilo.start()
    ocupado.wait(2)
    with escrituras.Cola(esperar=True, tope_s=5, job_id="b" * 32):
        orden.append("b-adentro")
    hilo.join()
    assert orden == ["a-adentro", "a-sale", "b-adentro"], "los turnos no se solapan"


def test_esperar_tiene_tope(sistema_de_juguete, ritmo_rapido):
    with escrituras.Cola():
        with pytest.raises(escrituras.SistemaOcupado):
            with escrituras.Cola(esperar=True, tope_s=0.2):
                pass


def test_la_ficha_del_candado_dice_quien_escribe(sistema_de_juguete):
    with escrituras.Cola(job_id="c" * 32):
        ficha = escrituras.quien_escribe()
        assert ficha["job_id"] == "c" * 32 and ficha["pid"] == os.getpid()
    assert escrituras.quien_escribe() is None


# ── la bitácora ───────────────────────────────────────────────────────────────

INICIADO = "2026-09-18T10:15:02-06:00"


def _corrida(base):
    return bitacora.carpeta_de_corrida("3f2a1c9e" + "0" * 24, "nodo.F2.plan", "TINNIDROP", INICIADO)


def test_la_carpeta_de_la_corrida_tiene_el_nombre_del_diseno(sistema_de_juguete):
    carpeta = _corrida(sistema_de_juguete)
    assert bitacora.ruta_relativa(carpeta) == (
        "PRODUCTOS/_AUDITORIAS/app_runs/2026-09/20260918-101502_nodo.F2.plan_TINNIDROP_3f2a1c9e"
    )
    assert carpeta.is_dir()
    assert _corrida(sistema_de_juguete) == carpeta, "al retomar es la misma carpeta"


def test_una_unidad_que_empezo_y_no_termino_se_reconoce(sistema_de_juguete):
    marca = bitacora.Marca(_corrida(sistema_de_juguete), 1)
    assert not marca.inicio_sin_fin()
    marca.iniciar("t1")
    assert marca.inicio_sin_fin(), "empezó y no terminó: se cayó a mitad"
    marca.cerrar_intento_roto("t2")
    marca.iniciar("t3")
    marca.terminar("t4", {"ok": True})
    assert not marca.inicio_sin_fin()
    assert marca.intentos() == 2, "el reintento de una unidad idempotente queda anotado"


def test_los_logs_y_las_aprobaciones_solo_se_agregan(sistema_de_juguete):
    carpeta = _corrida(sistema_de_juguete)
    bitacora.anotar_linea(carpeta, "1_x.log", "uno")
    bitacora.anotar_linea(carpeta, "1_x.log", "dos")
    bitacora.registrar_aprobacion(carpeta, {"hash": "abc", "decision": "APROBADA"})
    assert (carpeta / "1_x.log").read_text(encoding="utf-8") == "uno\ndos\n"
    assert '"hash": "abc"' in (carpeta / "aprobaciones.jsonl").read_text(encoding="utf-8")


def test_trabajo_json_se_reescribe_completo(sistema_de_juguete):
    carpeta = _corrida(sistema_de_juguete)
    bitacora.reescribir_trabajo(carpeta, {"estado": "CORRIENDO"})
    bitacora.reescribir_trabajo(carpeta, {"estado": "EXITO"})
    assert bitacora.leer_trabajo(carpeta) == {"estado": "EXITO"}
    assert not (carpeta / "trabajo.json.nuevo").exists(), "no queda el archivo provisorio"


def test_no_escribe_fuera_de_app_runs(sistema_de_juguete):
    afuera = sistema_de_juguete / "PRODUCTOS" / "_DIM_PRODUCTOS.csv"
    with pytest.raises(bitacora.FueraDeLaBitacora):
        bitacora.anotar_linea(afuera.parent, "_DIM_PRODUCTOS.csv", "x")
    with pytest.raises(bitacora.FueraDeLaBitacora):
        bitacora.reescribir_trabajo(sistema_de_juguete, {"x": 1})
    with pytest.raises(bitacora.FueraDeLaBitacora):
        bitacora.abrir_log(bitacora.raiz() / ".." / "..", "x.log")
    assert "x" not in afuera.read_text(encoding="utf-8").splitlines()[-1:], "el CSV no se tocó"


def test_toda_escritura_de_la_bitacora_pasa_por_dentro():
    """Estructural: las primitivas de escritura solo viven en las funciones que llaman a `_dentro`."""
    archivo = PAQUETE / "bitacora.py"
    arbol = ast.parse(archivo.read_text(encoding="utf-8"), filename=str(archivo))
    permitidas = {"_crear_carpeta", "_abrir", "reescribir_trabajo", "reescribir_en_corrida"}
    primitivas = ("open", "os.replace", ".mkdir", ".write_text", ".unlink", "json.dump")
    for funcion in (n for n in ast.walk(arbol) if isinstance(n, ast.FunctionDef)):
        for nodo in ast.walk(funcion):
            if isinstance(nodo, ast.Call):
                llamada = ast.unparse(nodo.func)
                if llamada == "open" or llamada in primitivas or llamada.endswith((".mkdir", ".write_text", ".unlink")):
                    assert funcion.name in permitidas, (
                        f"bitacora.py:{nodo.lineno} «{llamada}» en {funcion.name}: solo {sorted(permitidas)}"
                    )
                    assert "_dentro(" in ast.unparse(funcion), f"{funcion.name} escribe sin pasar por _dentro"
