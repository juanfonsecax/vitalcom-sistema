"""Armar FASE 1 de a un paso (Hito 4): una llamada de Claude por etapa, los grupos en paralelo.

Sobre el sistema de juguete, con el manifiesto y el FLUJO.json REALES y el Claude falso: ninguna
prueba llama a Claude ni a Meta. Lo que se congela:
  * los pasos corren en el orden de la secuencia y los de un grupo, a la vez;
  * lo que devolvió cada etapa queda, textual, en `etapas/NN_<etapa>.md`, y la etapa siguiente
    recibe la ruta de esas salidas (no un resumen);
  * una pregunta de una etapa detiene el trabajo hasta la respuesta, y después sigue;
  * un paso que falla corta ahí; «Reintentar» retoma desde ese paso si los insumos no cambiaron,
    y corre completo si cambiaron (invariante 5);
  * ningún paso recibe una herramienta de Meta.
"""

from __future__ import annotations

import csv
import json
import time
from pathlib import Path

import sistema_de_juguete as juguete

from vitalcom_app import claude, workflows

JOB = "a" * 32
PASOS = [["etapa-producto"], ["etapa-0"], ["Ads/_TOOLS/lavar_videos.sh"], ["etapa-1"], ["etapa-1b"],
         ["etapa-2", "etapa-fanpage"], ["etapa-4", "etapa-5"], ["etapa-6"], ["etapa-guardar-producto"]]
SALIDAS = ["01_etapa-producto.md", "02_etapa-0.md", "03_lavar_videos.md", "04_etapa-1.md", "05_etapa-1b.md",
           "06_etapa-2.md", "06_etapa-fanpage.md", "07_etapa-4.md", "07_etapa-5.md", "08_etapa-6.md",
           "09_etapa-guardar-producto.md"]


def _pedir(cliente, job_id=JOB):
    return cliente.post("/api/acciones/nodo.F1.paquete", json={
        "parametros": {"producto_key": "TINNIDROP"}, "confirmado": True, "job_id": job_id})


def _terminar(job_id=JOB, tope_s=120):
    resultado = workflows.esperar_resultado(job_id, tope_s)
    assert resultado is not None, "el trabajo no terminó"
    return resultado


def _listo(base: Path, cumplido: bool = True) -> None:
    juguete.escribir_flujo_falso(base, {"*": juguete.flujo_listo("F1.paquete", cumplido=cumplido)})


def _corridas(base: Path) -> list[dict]:
    archivo = base / "PRODUCTOS" / "_pasos.log"
    return [json.loads(x) for x in archivo.read_text(encoding="utf-8").splitlines() if x] if archivo.is_file() else []


def _argvs(base: Path) -> list[dict]:
    archivo = base / "PRODUCTOS" / "_claude_argv.log"
    return [json.loads(x) for x in archivo.read_text(encoding="utf-8").splitlines() if x]


def _tablero(base: Path, resultado: dict) -> dict:
    return json.loads((base / resultado["run_dir"] / "pasos.json").read_text(encoding="utf-8"))


def test_el_manifiesto_real_declara_los_pasos_de_la_secuencia():
    """Los pasos del manifiesto son la secuencia de FLUJO.json con sus dos paralelos (V20 lo valida)."""
    accion = next(a for a in juguete.manifiesto_real()["acciones"]["lista"] if a["id"] == "nodo.F1.paquete")
    assert accion["pasos"] == PASOS


def test_los_pasos_corren_en_orden_y_los_grupos_a_la_vez(cliente_juguete, sistema_de_juguete, monkeypatch):
    _listo(sistema_de_juguete)
    monkeypatch.setenv("VITALCOM_FAKE_PASO_MODO", json.dumps({"etapa-2": "dormir:1.5", "etapa-fanpage": "dormir:1.5"}))
    assert _pedir(cliente_juguete).status_code == 202
    resultado = _terminar()
    assert resultado["estado"] == "EXITO", resultado

    corridas = _corridas(sistema_de_juguete)
    assert [c["etapa"] for c in corridas if c["etapa"] not in ("etapa-2", "etapa-fanpage", "etapa-4", "etapa-5")] == [
        "etapa-producto", "etapa-0", "Ads/_TOOLS/lavar_videos.sh", "etapa-1", "etapa-1b", "etapa-6",
        "etapa-guardar-producto"]
    por_etapa = {c["etapa"]: c for c in corridas}
    dos, fan = por_etapa["etapa-2"], por_etapa["etapa-fanpage"]
    assert dos["inicio"] < fan["fin"] and fan["inicio"] < dos["fin"], "etapa-2 y etapa-fanpage no corrieron a la vez"
    assert por_etapa["etapa-1b"]["fin"] <= min(dos["inicio"], fan["inicio"]), "un grupo arrancó antes que el paso previo"
    assert max(dos["fin"], fan["fin"]) <= min(por_etapa["etapa-4"]["inicio"], por_etapa["etapa-5"]["inicio"])

    carpeta = sistema_de_juguete / resultado["run_dir"] / "etapas"
    assert sorted(x.name for x in carpeta.iterdir()) == SALIDAS
    assert (carpeta / "06_etapa-2.md").read_text(encoding="utf-8").startswith("SALIDA DE etapa-2 (fake)")
    assert "SCRIPT Ads/_TOOLS/lavar_videos.sh" in (carpeta / "03_lavar_videos.md").read_text(encoding="utf-8")
    tablero = _tablero(sistema_de_juguete, resultado)
    assert [p["estado"] for p in tablero["pasos"]] == ["EXITO"] * len(PASOS)
    assert tablero["producto_key"] == "TINNIDROP" and tablero["retomado_de"] is None


def test_cada_paso_recibe_las_rutas_de_lo_anterior_y_ninguna_herramienta_de_meta(cliente_juguete, sistema_de_juguete):
    _listo(sistema_de_juguete)
    _pedir(cliente_juguete)
    resultado = _terminar()
    assert resultado["estado"] == "EXITO", resultado
    prompts = {}
    for corrida in _argvs(sistema_de_juguete):
        argv = corrida["argv"]
        prompt = argv[argv.index("-p") + 1]
        assert not any(h.startswith("mcp__") for h in corrida["permitidas"]), "un paso recibió una herramienta de Meta"
        assert "WebSearch" in corrida["permitidas"], "las herramientas de la acción llegan a cada paso"
        if "PASO_ETAPA:" in prompt:
            prompts[prompt.split("PASO_ETAPA:", 1)[1].strip()] = prompt
    assert set(prompts) == {e for g in PASOS for e in g}
    etapas_dir = f"{resultado['run_dir']}/etapas"
    uno_b = prompts["etapa-1b"]
    assert f"{etapas_dir}/00_INPUTS_CONGELADOS.md" in uno_b and f"{etapas_dir}/04_etapa-1.md" in uno_b
    assert f"{etapas_dir}/06_etapa-2.md" not in uno_b, "un paso no recibe salidas que todavía no existen"
    assert "En paralelo, en otra llamada, corre `etapa-fanpage`" in prompts["etapa-2"]
    assert "En paralelo" not in prompts["etapa-6"]
    assert "paso 8 de 9" in prompts["etapa-6"]


def test_una_pregunta_de_una_etapa_espera_la_respuesta_y_sigue(cliente_juguete, sistema_de_juguete, monkeypatch):
    _listo(sistema_de_juguete)
    monkeypatch.setenv("VITALCOM_FAKE_PASO_MODO", json.dumps({"etapa-producto": "pregunta"}))
    _pedir(cliente_juguete)
    limite = time.monotonic() + 30
    while cliente_juguete.get(f"/api/trabajos/{JOB}").json()["estado"] != "ESPERA_RESPUESTA":
        assert time.monotonic() < limite, "no llegó a esperar la respuesta"
        time.sleep(0.1)
    pendiente = cliente_juguete.get(f"/api/trabajos/{JOB}").json()["pendiente_completo"]
    assert pendiente["tipo"] == "pregunta" and pendiente["etapa"] == "etapa-producto"
    assert "cambio de producto" in pendiente["texto"] and "NO APTO" in pendiente["contexto"], pendiente
    assert [c["etapa"] for c in _corridas(sistema_de_juguete)] == ["etapa-producto"], "no siguió sin la respuesta"
    assert cliente_juguete.post(f"/api/trabajos/{JOB}/respuesta", json={"n": 1, "texto": "Seguí igual"}).status_code == 202
    resultado = _terminar()
    assert resultado["estado"] == "EXITO", resultado
    continuacion = [c for c in _argvs(sistema_de_juguete) if c["resume"]]
    assert len(continuacion) == 1 and "PASO_ETAPA: etapa-producto" in continuacion[0]["argv"][continuacion[0]["argv"].index("-p") + 1]
    salida = sistema_de_juguete / resultado["run_dir"] / "etapas" / "01_etapa-producto.md"
    assert salida.read_text(encoding="utf-8").startswith("SALIDA DE etapa-producto"), \
        "la salida de la etapa estaba en la vuelta de ANTES de la pregunta"


def test_un_paso_que_falla_corta_y_reintentar_retoma_desde_ahi(cliente_juguete, sistema_de_juguete, monkeypatch):
    _listo(sistema_de_juguete, cumplido=False)
    monkeypatch.setenv("VITALCOM_FAKE_PASO_MODO", json.dumps({"etapa-1b": "error"}))
    _pedir(cliente_juguete)
    primero = _terminar()
    assert primero["estado"] == "FALLIDO" and "etapa-1b" in primero["detalle"], primero
    assert [c["etapa"] for c in _corridas(sistema_de_juguete)][-1] == "etapa-1b", "siguió después del paso que falló"
    tablero = _tablero(sistema_de_juguete, primero)
    assert [p["estado"] for p in tablero["pasos"]][:6] == ["EXITO"] * 4 + ["FALLIDO", "PENDIENTE"]

    monkeypatch.setenv("VITALCOM_FAKE_PASO_MODO", "{}")
    _listo(sistema_de_juguete)
    antes = len(_corridas(sistema_de_juguete))
    respuesta = cliente_juguete.post(f"/api/trabajos/{JOB}/reintentar", json={"confirmado": True})
    assert respuesta.status_code == 202, respuesta.text
    segundo = _terminar(respuesta.json()["job_id"])
    assert segundo["estado"] == "EXITO", segundo
    nuevas = [c["etapa"] for c in _corridas(sistema_de_juguete)[antes:]]
    assert nuevas[0] == "etapa-1b" and "etapa-producto" not in nuevas and "etapa-1" not in nuevas, nuevas
    tablero = _tablero(sistema_de_juguete, segundo)
    assert [p["estado"] for p in tablero["pasos"]] == ["HEREDADO"] * 4 + ["EXITO"] * 5
    assert tablero["retomado_de"] == JOB
    assert "Retoma desde el paso 5" in segundo["unidades"][0]["detalle"]
    assert sorted(x.name for x in (sistema_de_juguete / segundo["run_dir"] / "etapas").iterdir()) == SALIDAS


def test_si_cambian_los_insumos_reintentar_corre_completo(cliente_juguete, sistema_de_juguete, monkeypatch):
    _listo(sistema_de_juguete, cumplido=False)
    monkeypatch.setenv("VITALCOM_FAKE_PASO_MODO", json.dumps({"etapa-2": "error"}))
    _pedir(cliente_juguete)
    assert _terminar()["estado"] == "FALLIDO"

    productos = sistema_de_juguete / "PRODUCTOS" / "_DIM_PRODUCTOS.csv"
    with open(productos, encoding="utf-8", newline="") as archivo:
        filas = list(csv.DictReader(archivo))
    filas[0]["costo_q"] = "75"
    juguete._csv(productos, juguete.COLUMNAS_PRODUCTOS, filas)
    monkeypatch.setenv("VITALCOM_FAKE_PASO_MODO", "{}")
    _listo(sistema_de_juguete)
    antes = len(_corridas(sistema_de_juguete))
    segundo = _terminar(cliente_juguete.post(f"/api/trabajos/{JOB}/reintentar", json={"confirmado": True}).json()["job_id"])
    assert segundo["estado"] == "EXITO", segundo
    assert [c["etapa"] for c in _corridas(sistema_de_juguete)[antes:]][0] == "etapa-producto"
    assert "cambiaron" in segundo["unidades"][0]["detalle"]
    assert _tablero(sistema_de_juguete, segundo)["retomado_de"] is None


def test_si_claude_no_invoca_la_etapa_el_paso_falla(cliente_juguete, sistema_de_juguete, monkeypatch):
    _listo(sistema_de_juguete)
    monkeypatch.setenv("VITALCOM_FAKE_PASO_MODO", json.dumps({"etapa-fanpage": "sin_task"}))
    _pedir(cliente_juguete)
    resultado = _terminar()
    assert resultado["estado"] == "FALLIDO" and "sin invocar `etapa-fanpage`" in resultado["detalle"], resultado
    assert "etapa-4" not in [c["etapa"] for c in _corridas(sistema_de_juguete)]


def test_la_salida_del_subagente_sale_del_registro_textual():
    """`salida_de_subagente`: el tool_result de SU Task, de primer nivel, el último que no fue error."""
    def ev(tipo, contenido, padre=None):
        return json.dumps({"type": tipo, "parent_tool_use_id": padre, "message": {"content": contenido}})
    lineas = [
        ev("assistant", [{"type": "tool_use", "id": "t1", "name": "Task", "input": {"subagent_type": "etapa-2"}}]),
        ev("assistant", [{"type": "tool_use", "id": "x", "name": "Read", "input": {}}], padre="t1"),
        ev("user", [{"type": "tool_result", "tool_use_id": "x", "content": "lo que leyó ADENTRO"}], padre="t1"),
        ev("user", [{"type": "tool_result", "tool_use_id": "t1", "content": [{"type": "text", "text": "PRIMERA"}]}]),
        ev("assistant", [{"type": "tool_use", "id": "t2", "name": "Agent", "input": {"subagent_type": "etapa-2"}}]),
        ev("user", [{"type": "tool_result", "tool_use_id": "t2", "is_error": True, "content": "se cortó"}]),
        ev("assistant", [{"type": "tool_use", "id": "t3", "name": "Task", "input": {"subagent_type": "etapa-fanpage"}}]),
        ev("user", [{"type": "tool_result", "tool_use_id": "t3", "content": "DE OTRA ETAPA"}]),
        "no es json",
    ]
    assert claude.salida_de_subagente(lineas, "etapa-2") == "PRIMERA"
    assert claude.salida_de_subagente(lineas, "etapa-fanpage") == "DE OTRA ETAPA"
    assert claude.salida_de_subagente(lineas, "etapa-6") is None
