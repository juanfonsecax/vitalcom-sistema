"""La API de trabajos y el progreso en vivo (diseño §3.6, §3.7, §3.10), sobre el sistema de juguete."""

from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path

import meta_falso as meta
import pytest
import sistema_de_juguete as juguete
from fastapi.testclient import TestClient

from vitalcom_app import acciones, sse, workflows

JOB = "a" * 32
OTRO = "b" * 32
PARLANTE = '''import json, sys, time
for i in range(1, 4):
    print("linea %d" % i, flush=True)
    time.sleep(0.4)
if "--json" in sys.argv:
    print(json.dumps({"ok": True}))
'''
DORMILON = "import time\ntime.sleep(60)\n"


def _pedir(cliente, accion_id, parametros=None, job_id=JOB, **extra):
    return cliente.post(f"/api/acciones/{accion_id}", json={
        "parametros": parametros or {}, "confirmado": True, "job_id": job_id, **extra})


def _terminar(job_id=JOB, tope_s=60):
    resultado = workflows.esperar_resultado(job_id, tope_s)
    assert resultado is not None, "el trabajo no terminó"
    return resultado


def _esperar_estado(cliente, job_id: str, estado: str, tope_s: float = 30) -> dict:
    limite = time.monotonic() + tope_s
    while time.monotonic() < limite:
        detalle = cliente.get(f"/api/trabajos/{job_id}").json()
        if detalle["estado"] == estado:
            return detalle
        time.sleep(0.1)
    raise AssertionError(f"no llegó a {estado}: {cliente.get(f'/api/trabajos/{job_id}').json()['estado']}")


def _eventos(cliente, job_id: str, ultimo_id: str | None = None) -> list[tuple[str, dict, str | None]]:
    """Todos los eventos SSE hasta que el servidor cierra la conexión: (evento, datos, id)."""
    cabeceras = {"Last-Event-ID": ultimo_id} if ultimo_id else {}
    salida, nombre, id_ = [], None, None
    with cliente.stream("GET", f"/api/trabajos/{job_id}/eventos", headers=cabeceras) as respuesta:
        assert respuesta.status_code == 200
        assert respuesta.headers["content-type"].startswith("text/event-stream")
        for linea in respuesta.iter_lines():
            if linea.startswith("id: "):
                id_ = linea[4:]
            elif linea.startswith("event: "):
                nombre = linea[7:]
            elif linea.startswith("data: "):
                salida.append((nombre, json.loads(linea[6:]), id_))
    return salida


@pytest.fixture(autouse=True)
def sondeo_rapido(monkeypatch):
    monkeypatch.setattr(sse, "SONDEO_S", 0.05)


# ── lista y detalle ───────────────────────────────────────────────────────────

def test_la_lista_y_el_detalle_de_un_trabajo(cliente_juguete, sistema_de_juguete):
    _pedir(cliente_juguete, "nodo.ciclo.motor")
    _terminar()
    fila = cliente_juguete.get("/api/trabajos").json()[0]
    assert fila["job_id"] == JOB and fila["estado"] == "EXITO" and fila["accion_id"] == "nodo.ciclo.motor"
    assert fila["rotulo"] == "Correr el motor de decisión" and fila["iniciado"] and fila["terminado"]
    assert fila["otra_version"] is False and fila["pendiente"] is None

    detalle = cliente_juguete.get(f"/api/trabajos/{JOB}").json()
    assert detalle["run_dir"].startswith("PRODUCTOS/_AUDITORIAS/app_runs/")
    assert detalle["sello"]["argv"][1] == "Ads/_TOOLS/gen_decisiones.py"
    assert detalle["sello"]["manifiesto_sha"] and detalle["unidades"][0]["estado"] == "EXITO"


def test_la_lista_se_filtra_por_estado_y_producto(cliente_juguete, sistema_de_juguete):
    juguete.escribir_script(sistema_de_juguete, "transcribir_videos.py", "import sys\nsys.exit(1)\n")
    _pedir(cliente_juguete, "nodo.ciclo.motor", job_id=JOB)
    _terminar(JOB)
    _pedir(cliente_juguete, "producto.transcribir", {"producto_key": "TINNIDROP", "modelo": "small"}, job_id=OTRO)
    _terminar(OTRO)
    assert {f["job_id"] for f in cliente_juguete.get("/api/trabajos").json()} == {JOB, OTRO}
    assert [f["job_id"] for f in cliente_juguete.get("/api/trabajos", params={"estado": "FALLIDO"}).json()] == [OTRO]
    assert [f["job_id"] for f in cliente_juguete.get("/api/trabajos", params={"producto_key": "TINNIDROP"}).json()] == [OTRO]
    assert cliente_juguete.get("/api/trabajos", params={"limite": 1}).json()[0]["job_id"] == OTRO, "los nuevos primero"


def test_un_trabajo_que_no_existe_es_404(cliente_juguete):
    for camino in ("", "/eventos"):
        respuesta = cliente_juguete.get(f"/api/trabajos/{'f' * 32}{camino}")
        assert respuesta.status_code == 404 and respuesta.json()["codigo"] == "TRABAJO_NO_EXISTE"
    assert cliente_juguete.post(f"/api/trabajos/{'f' * 32}/cancelar").status_code == 404


def test_el_estado_de_claude(cliente_juguete, monkeypatch):
    assert cliente_juguete.get("/api/claude/estado").json()["logueado"] is True
    monkeypatch.setenv("VITALCOM_FAKE_SIN_SESION", "1")
    from vitalcom_app import claude

    claude.olvidar_sesion()
    estado = cliente_juguete.get("/api/claude/estado").json()
    assert estado["logueado"] is False and "/login" in estado["detalle"]


# ── aprobar, rechazar, responder ──────────────────────────────────────────────

@pytest.fixture()
def publicando(sistema_de_juguete: Path, cliente_juguete: TestClient) -> TestClient:
    meta.preparar(sistema_de_juguete)
    meta.habilitar_publicar_f1(sistema_de_juguete)
    acciones.olvidar_cache()
    return cliente_juguete


def _publicar(cliente):
    return _pedir(cliente, "nodo.F1.publicar", {"producto_key": "TINNIDROP", "cuenta": "GTR 7"})


def test_aprobar_por_la_api(publicando, sistema_de_juguete):
    _publicar(publicando)
    detalle = _esperar_estado(publicando, JOB, "ESPERA_APROBACION")
    orden = detalle["pendiente_completo"]
    assert orden["tipo"] == "aprobacion" and orden["orden"]["llamadas"], "la orden completa a la vista"
    assert publicando.get("/api/trabajos").json()[0]["pendiente"] == "aprobacion"

    respuesta = publicando.post(f"/api/trabajos/{JOB}/aprobaciones/1", json={"decision": "APROBADA", "hash": orden["hash"]})
    assert respuesta.status_code == 202, respuesta.text
    assert _terminar()["estado"] == "EXITO"
    assert [f["herramienta"] for f in meta.llamadas_de_escritura(sistema_de_juguete)] == list(meta.ESCRITURA)


def test_las_puertas_de_la_aprobacion(publicando, sistema_de_juguete):
    _publicar(publicando)
    orden = _esperar_estado(publicando, JOB, "ESPERA_APROBACION")["pendiente_completo"]
    url = f"/api/trabajos/{JOB}/aprobaciones"

    distinta = publicando.post(f"{url}/1", json={"decision": "APROBADA", "hash": "0" * 64})
    assert distinta.status_code == 409 and distinta.json()["codigo"] == "HASH_DISTINTO"
    otra_orden = publicando.post(f"{url}/2", json={"decision": "APROBADA", "hash": orden["hash"]})
    assert otra_orden.status_code == 409 and otra_orden.json()["codigo"] == "NO_ESPERA_ESA_ORDEN"
    mala = publicando.post(f"{url}/1", json={"decision": "TAL_VEZ", "hash": orden["hash"]})
    assert mala.status_code == 422
    assert publicando.get(f"/api/trabajos/{JOB}").json()["estado"] == "ESPERA_APROBACION", "nada se envió"
    assert meta.llamadas_de_escritura(sistema_de_juguete) == []

    rechazo = publicando.post(f"{url}/1", json={"decision": "RECHAZADA", "hash": orden["hash"], "nota": "no"})
    assert rechazo.status_code == 202
    assert _terminar()["estado"] == "RECHAZADO"
    assert publicando.post(f"{url}/1", json={"decision": "APROBADA", "hash": orden["hash"]}).status_code == 409, (
        "una orden ya resuelta no se aprueba de nuevo"
    )


def test_responder_a_claude_por_la_api(cliente_juguete, sistema_de_juguete, monkeypatch):
    monkeypatch.setenv("VITALCOM_FAKE_MODO", "pregunta")
    juguete.escribir_flujo_falso(sistema_de_juguete, {"*": juguete.flujo_listo("F2.etapa-11", cumplido=True)})
    _pedir(cliente_juguete, "nodo.F2.etapa-11", {"producto_key": "TINNIDROP"})
    detalle = _esperar_estado(cliente_juguete, JOB, "ESPERA_RESPUESTA")
    assert detalle["pendiente_completo"]["tipo"] == "pregunta" and "ángulo A" in detalle["pendiente_completo"]["texto"]

    url = f"/api/trabajos/{JOB}/respuesta"
    assert cliente_juguete.post(url, json={"n": 2, "texto": "A"}).status_code == 409
    assert cliente_juguete.post(url, json={"n": 1, "texto": "  "}).status_code == 422
    assert cliente_juguete.post(url, json={"n": 1, "texto": "Seguí con el A"}).status_code == 202
    assert _terminar()["estado"] == "EXITO"


# ── cancelar ──────────────────────────────────────────────────────────────────

def test_cancelar_corta_el_comando_y_deja_correr_tras_escribir(cliente_juguete, sistema_de_juguete):
    juguete.escribir_script(sistema_de_juguete, "gen_decisiones.py", DORMILON)
    _pedir(cliente_juguete, "nodo.ciclo.motor")
    _esperar_estado(cliente_juguete, JOB, "CORRIENDO")
    time.sleep(1)
    inicio = time.monotonic()
    respuesta = cliente_juguete.post(f"/api/trabajos/{JOB}/cancelar")
    assert respuesta.status_code == 200 and respuesta.json()["estado"] == "CANCELADO"
    assert cliente_juguete.get(f"/api/trabajos/{JOB}").json()["estado"] == "CANCELADO"

    limite = time.monotonic() + 30
    while time.monotonic() < limite and "hook_csv.py" not in [c["script"] for c in juguete.llamadas(sistema_de_juguete)]:
        time.sleep(0.2)
    assert "hook_csv.py" in [c["script"] for c in juguete.llamadas(sistema_de_juguete)], "tras_escribir corrió igual"
    assert time.monotonic() - inicio < 25, "el comando de 60 s se cortó"
    assert cliente_juguete.post(f"/api/trabajos/{JOB}/cancelar").status_code == 409, "ya terminó"


def test_cancelar_una_espera_de_aprobacion_no_ejecuta_nada(publicando, sistema_de_juguete):
    _publicar(publicando)
    _esperar_estado(publicando, JOB, "ESPERA_APROBACION")
    assert publicando.post(f"/api/trabajos/{JOB}/cancelar").status_code == 200
    assert publicando.get(f"/api/trabajos/{JOB}").json()["estado"] == "CANCELADO"
    time.sleep(1)
    assert meta.llamadas_de_escritura(sistema_de_juguete) == []


# ── reintentar ────────────────────────────────────────────────────────────────

def test_reintentar_es_un_trabajo_nuevo_con_las_mismas_puertas(cliente_juguete, sistema_de_juguete, monkeypatch):
    monkeypatch.setenv("VITALCOM_FAKE_MODO", "error")
    _pedir(cliente_juguete, "nodo.F2.etapa-11", {"producto_key": "TINNIDROP"})
    assert _terminar()["estado"] == "FALLIDO"
    url = f"/api/trabajos/{JOB}/reintentar"

    sin_confirmar = cliente_juguete.post(url)
    assert sin_confirmar.status_code == 428, "el reintento pasa por las mismas puertas que un pedido"
    monkeypatch.setenv("VITALCOM_FAKE_MODO", "exito")
    juguete.escribir_flujo_falso(sistema_de_juguete, {"*": juguete.flujo_listo("F2.etapa-11", cumplido=True)})
    nuevo = cliente_juguete.post(url, json={"confirmado": True})
    assert nuevo.status_code == 202, nuevo.text
    assert nuevo.json()["job_id"] != JOB
    assert _terminar(nuevo.json()["job_id"])["estado"] == "EXITO"
    assert cliente_juguete.get(f"/api/trabajos/{JOB}").json()["estado"] == "FALLIDO", "el viejo queda con su rastro"


def test_un_trabajo_exitoso_no_se_reintenta(cliente_juguete):
    _pedir(cliente_juguete, "nodo.ciclo.motor")
    _terminar()
    respuesta = cliente_juguete.post(f"/api/trabajos/{JOB}/reintentar", json={"confirmado": True})
    assert respuesta.status_code == 409 and respuesta.json()["codigo"] == "NO_SE_REINTENTA"


# ── trabajos de otra versión ──────────────────────────────────────────────────

def test_un_trabajo_de_otra_version_se_ve_y_se_descarta(publicando, sistema_de_juguete):
    _publicar(publicando)
    _esperar_estado(publicando, JOB, "ESPERA_APROBACION")
    base_de_datos = sistema_de_juguete.parent / "datos" / "dbos.sqlite"
    with sqlite3.connect(base_de_datos, timeout=30) as conexion:
        conexion.execute("update workflow_status set application_version = 'wf-0' where workflow_uuid = ?", (JOB,))
    fila = publicando.get("/api/trabajos").json()[0]
    assert fila["estado"] == "OTRA_VERSION" and fila["otra_version"] is True and fila["app_version"] == "wf-0"

    assert publicando.post(f"/api/trabajos/{JOB}/descartar").json()["estado"] == "CANCELADO"
    assert publicando.get(f"/api/trabajos/{JOB}").json()["estado"] == "CANCELADO"
    assert publicando.post(f"/api/trabajos/{JOB}/descartar").status_code == 409


# ── el progreso en vivo (SSE) ─────────────────────────────────────────────────

def test_sse_entrega_estado_lineas_y_fin_en_orden(cliente_juguete, sistema_de_juguete):
    juguete.escribir_script(sistema_de_juguete, "gen_decisiones.py", PARLANTE)
    _pedir(cliente_juguete, "nodo.ciclo.motor")
    eventos = _eventos(cliente_juguete, JOB)
    nombres = [e[0] for e in eventos]
    assert nombres[0] == "estado" and nombres[-1] == "fin"
    lineas = [e[1]["texto"] for e in eventos if e[0] == "linea" and e[1]["tipo"] == "salida"]
    assert lineas == ["linea 1", "linea 2", "linea 3"], "cada línea, una vez y en orden"
    assert any(e[0] == "linea" and e[1]["tipo"] == "comando" for e in eventos)
    fin = eventos[-1][1]
    assert fin["estado"] == "EXITO" and fin["resultado"]["estado"] == "EXITO"
    assert all(e[2] for e in eventos if e[0] == "linea"), "cada línea lleva su id, para poder retomar"


def test_sse_retoma_con_last_event_id_sin_repetir(cliente_juguete, sistema_de_juguete):
    juguete.escribir_script(sistema_de_juguete, "gen_decisiones.py", PARLANTE)
    _pedir(cliente_juguete, "nodo.ciclo.motor")
    todos = _eventos(cliente_juguete, JOB)
    lineas = [e for e in todos if e[0] == "linea" and e[1]["tipo"] == "salida"]
    despues_de_la_primera = _eventos(cliente_juguete, JOB, ultimo_id=lineas[0][2])
    restantes = [e[1]["texto"] for e in despues_de_la_primera if e[0] == "linea" and e[1]["tipo"] == "salida"]
    assert restantes == ["linea 2", "linea 3"], "sigue desde donde quedó: no repite la 1 ni pierde las otras"
    assert despues_de_la_primera[-1][0] == "fin"


def test_sse_de_claude_resume_cada_evento(cliente_juguete, sistema_de_juguete):
    juguete.escribir_flujo_falso(sistema_de_juguete, {"*": juguete.flujo_listo("F2.etapa-11", cumplido=True)})
    _pedir(cliente_juguete, "nodo.F2.etapa-11", {"producto_key": "TINNIDROP"})
    eventos = _eventos(cliente_juguete, JOB)
    de_claude = [e[1]["texto"] for e in eventos if e[0] == "linea" and e[1]["tipo"] == "claude"]
    assert "arrancó etapa-fake" in de_claude and "Claude terminó: success" in de_claude
    assert not [t for t in de_claude if t.startswith("{")], "el JSON crudo queda en la bitácora, no en la pantalla"


def test_sse_avisa_lo_pendiente_y_su_desaparicion(publicando, sistema_de_juguete):
    _publicar(publicando)
    orden = _esperar_estado(publicando, JOB, "ESPERA_APROBACION")["pendiente_completo"]
    publicando.post(f"/api/trabajos/{JOB}/aprobaciones/1", json={"decision": "RECHAZADA", "hash": orden["hash"]})
    eventos = _eventos(publicando, JOB)
    pendientes = [e[1] for e in eventos if e[0] == "pendiente"]
    assert eventos[-1][0] == "fin" and eventos[-1][1]["estado"] == "RECHAZADO"
    assert not pendientes or pendientes[-1] == {}, "al resolverse, lo pendiente se limpia"


def test_las_lineas_se_clasifican():
    assert sse.linea_de("1_x.log", "$ python x.py") == {"unidad": 1, "texto": "python x.py", "tipo": "comando"}
    assert sse.linea_de("2_x.log", "[stderr] falló") == {"unidad": 2, "texto": "falló", "tipo": "error"}
    assert sse.linea_de("2_x.log", "hola") == {"unidad": 2, "texto": "hola", "tipo": "salida"}
    assert sse.linea_de("2_x.log", "   ") is None
    assert sse.linea_de("3_claude.jsonl", json.dumps({"type": "user"})) is None
    assert sse._leer_id(sse._id_de({"1_a.log": 10, "2_b.jsonl": 5})) == {"1_a.log": 10, "2_b.jsonl": 5}
