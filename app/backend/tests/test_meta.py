"""`wf_meta`: publicar en Meta con aprobación por huella — TODO contra fakes (diseño §3.5(e), §3.6).

Ninguna prueba llama a Meta ni al Claude real. El manifiesto real deja `nodo.F1.publicar` DESHABILITADO
(Hito 4, en Opus); acá se habilita solo en el sistema de juguete para probar el MECANISMO. Lo que estas
pruebas garantizan: sin una aprobación sellada, ninguna herramienta de escritura de Meta llega a correr.
"""

from __future__ import annotations

import ast
import copy
import json
import time
from datetime import datetime, timedelta
from pathlib import Path

import meta_falso as meta
import pytest
import sistema_de_juguete as juguete
from fastapi.testclient import TestClient

from vitalcom_app import acciones, workflows

JOB = "a" * 32
PARAMETROS = {"producto_key": "TINNIDROP", "cuenta": "GTR 7"}
PAQUETE = Path(__file__).resolve().parents[1] / "vitalcom_app"


@pytest.fixture()
def publicando(sistema_de_juguete: Path, cliente_juguete: TestClient) -> TestClient:
    """El juguete listo para publicar (F1.publicar habilitada, scripts y Meta falsos)."""
    meta.preparar(sistema_de_juguete)
    meta.habilitar_publicar_f1(sistema_de_juguete)
    acciones.olvidar_cache()
    return cliente_juguete


def _publicar(cliente: TestClient, **extra):
    return cliente.post("/api/acciones/nodo.F1.publicar", json={
        "parametros": PARAMETROS, "confirmado": True, "job_id": JOB, **extra})


def _esperar(job_id: str, estado: str, tope_s: float = 40) -> None:
    limite = time.monotonic() + tope_s
    while time.monotonic() < limite:
        publicado = workflows.publicado(job_id, "estado")
        if publicado and publicado.get("estado") == estado:
            return
        time.sleep(0.1)
    raise AssertionError(f"el trabajo no llegó a {estado} (está en {workflows.publicado(job_id, 'estado')})")


def _pendiente(job_id: str, orden_id: int = 1) -> dict:
    _esperar(job_id, "ESPERA_APROBACION")
    limite = time.monotonic() + 10
    while time.monotonic() < limite:
        pendiente = workflows.publicado(job_id, "pendiente")
        if pendiente and pendiente["orden_id"] == orden_id:
            return pendiente
        time.sleep(0.1)
    raise AssertionError("no apareció la orden pendiente")


def _terminar(job_id: str = JOB, tope_s: float = 60) -> dict:
    resultado = workflows.esperar_resultado(job_id, tope_s)
    assert resultado is not None, "el trabajo no terminó"
    return resultado


def _escrituras(base: Path) -> list[str]:
    return [f["herramienta"] for f in meta.llamadas_de_escritura(base)]


# ── el camino completo ────────────────────────────────────────────────────────

def test_publicar_con_aprobacion_ejecuta_verifica_y_registra(publicando, sistema_de_juguete):
    assert _publicar(publicando).status_code == 202
    pendiente = _pendiente(JOB)
    assert pendiente["tipo"] == "aprobacion" and pendiente["caduca_horas"] == 12
    assert [c["tool"] for c in pendiente["orden"]["llamadas"]] == list(meta.ESCRITURA), "la orden completa a la vista"
    assert _escrituras(sistema_de_juguete) == [], "esperando al operador: nada corrió"

    workflows.enviar_aprobacion(JOB, 1, "APROBADA", pendiente["hash"], nota="dale")
    resultado = _terminar()
    assert resultado["estado"] == "EXITO", resultado
    assert _escrituras(sistema_de_juguete) == list(meta.ESCRITURA), "las cuatro llamadas, en orden"
    assert meta.meta_tiene(sistema_de_juguete) == ["GTR7_TINNIDROP_F1", "CJ1", "AD1"]

    scripts = [c["script"] for c in juguete.llamadas(sistema_de_juguete)]
    assert "verificar_publicacion.py" in scripts, "el gate cerró (escribe los ad_id)"
    evento = next(c for c in juguete.llamadas(sistema_de_juguete) if c["script"] == "registrar_evento.py")
    assert f"app job={JOB} orden=1" in evento["argv"][evento["argv"].index("--fuente") + 1]
    assert evento["argv"][evento["argv"].index("--evento") + 1] == "LANZAMIENTO"

    aprobaciones = (sistema_de_juguete / resultado["run_dir"] / "aprobaciones.jsonl").read_text(encoding="utf-8")
    assert pendiente["hash"] in aprobaciones and '"decision": "APROBADA"' in aprobaciones


# ── sin aprobación, nada se ejecuta ───────────────────────────────────────────

def test_meta_no_ejecuta_sin_aprobacion(publicando, sistema_de_juguete):
    """Sin `send`, el trabajo espera: ni una herramienta de escritura corre."""
    _publicar(publicando)
    _pendiente(JOB)
    time.sleep(1.5)
    assert _escrituras(sistema_de_juguete) == []
    assert workflows.publicado(JOB, "estado")["estado"] == "ESPERA_APROBACION"


def test_una_orden_rechazada_no_ejecuta_nada(publicando, sistema_de_juguete):
    _publicar(publicando)
    pendiente = _pendiente(JOB)
    workflows.enviar_aprobacion(JOB, 1, "RECHAZADA", pendiente["hash"], nota="no")
    resultado = _terminar()
    assert resultado["estado"] == "RECHAZADO"
    assert _escrituras(sistema_de_juguete) == []
    assert '"decision": "RECHAZADA"' in (sistema_de_juguete / resultado["run_dir"] / "aprobaciones.jsonl").read_text(encoding="utf-8")


def test_aprobar_otra_orden_no_aprueba_esta(publicando, sistema_de_juguete):
    """Un mensaje con OTRA huella se ignora: el trabajo sigue esperando y no ejecuta nada."""
    _publicar(publicando)
    pendiente = _pendiente(JOB)
    workflows.enviar_aprobacion(JOB, 1, "APROBADA", "0" * 64)
    time.sleep(1.5)
    assert _escrituras(sistema_de_juguete) == []
    assert workflows.publicado(JOB, "estado")["estado"] == "ESPERA_APROBACION"
    workflows.enviar_aprobacion(JOB, 1, "APROBADA", pendiente["hash"])
    assert _terminar()["estado"] == "EXITO"


def test_una_orden_que_nadie_aprueba_caduca(publicando, sistema_de_juguete):
    meta.habilitar_publicar_f1(sistema_de_juguete, caduca_horas=0.0005)  # 1,8 s
    acciones.olvidar_cache()
    _publicar(publicando)
    resultado = _terminar()
    assert resultado["estado"] == "CADUCADO"
    assert _escrituras(sistema_de_juguete) == []


def test_aprobacion_caducada_no_ejecuta(publicando, sistema_de_juguete, monkeypatch):
    """La aprobación vale 12 h: si al ejecutar ya pasaron, no se llama a nada."""
    _publicar(publicando)
    pendiente = _pendiente(JOB)
    futuro = (datetime.now().astimezone() + timedelta(hours=13)).isoformat(timespec="seconds")
    monkeypatch.setattr(workflows, "_ahora", lambda: futuro)
    workflows.enviar_aprobacion(JOB, 1, "APROBADA", pendiente["hash"])
    resultado = _terminar()
    assert resultado["estado"] == "CADUCADO", resultado
    assert _escrituras(sistema_de_juguete) == []


# ── idempotencia: lo que ya existe no se vuelve a crear ───────────────────────

def test_meta_reintento_no_duplica(publicando, sistema_de_juguete):
    """Entre la aprobación y la ejecución, alguien creó la campaña: el snapshot fresco la ve y no se llama."""
    _publicar(publicando)
    pendiente = _pendiente(JOB)
    meta.poner_en_meta(sistema_de_juguete, [
        {"id": "camp-existente", "nivel": "campaign", "name": "GTR7_TINNIDROP_F1", "status": "PAUSED"}])
    workflows.enviar_aprobacion(JOB, 1, "APROBADA", pendiente["hash"])
    resultado = _terminar()
    assert resultado["estado"] == "EXITO", resultado
    assert _escrituras(sistema_de_juguete) == ["ads_create_ad_set", "ads_create_creative", "ads_create_ad"], (
        "la campaña ya existía: ads_create_campaign no se llamó"
    )
    ejecucion = next(a for a in _argv_de_claude(sistema_de_juguete) if "LLAMADAS_JSON" in a["argv"][a["argv"].index("-p") + 1])
    assert "camp-existente" in ejecucion["argv"][ejecucion["argv"].index("-p") + 1], "el id existente se pasa como variable"


def test_meta_llamada_nueva_pide_reaprobacion(publicando, sistema_de_juguete):
    """Si al regenerar aparece algo que no estaba aprobado, se detiene y vuelve a pedir aprobación."""
    _publicar(publicando)
    primera = _pendiente(JOB)
    ampliado = copy.deepcopy(meta.PAQUETE_FALSO)
    ampliado["llamadas"].append({"n": 5, "tool": "ads_create_ad", "args": {"ad_name": "AD2", "status": "PAUSED"},
                                 "guardar_como": "ad_id_2"})
    meta.escribir_paquete(sistema_de_juguete, ampliado)
    workflows.enviar_aprobacion(JOB, 1, "APROBADA", primera["hash"])

    segunda = _pendiente(JOB, orden_id=2)
    assert segunda["hash"] != primera["hash"] and len(segunda["orden"]["llamadas"]) == 5
    assert _escrituras(sistema_de_juguete) == [], "no se ejecutó nada con la orden vieja"

    workflows.enviar_aprobacion(JOB, 2, "APROBADA", segunda["hash"])
    resultado = _terminar()
    assert resultado["estado"] == "EXITO", resultado
    assert len(_escrituras(sistema_de_juguete)) == 5


def test_una_llamada_que_falla_deja_la_secuencia_a_medias_y_lo_dice(publicando, sistema_de_juguete, monkeypatch):
    monkeypatch.setenv("VITALCOM_FAKE_META_FALLA_EN", "3")
    _publicar(publicando)
    pendiente = _pendiente(JOB)
    workflows.enviar_aprobacion(JOB, 1, "APROBADA", pendiente["hash"])
    resultado = _terminar()
    assert resultado["estado"] == "FALLIDO" and "a medias" in resultado["detalle"]
    assert _escrituras(sistema_de_juguete) == ["ads_create_campaign", "ads_create_ad_set"], "paró en la que falló"
    assert "verificar_publicacion.py" not in [c["script"] for c in juguete.llamadas(sistema_de_juguete)], (
        "con la secuencia a medias no se cierra el gate ni se registra el lanzamiento"
    )


# ── lo que Meta dice de la cuenta y lo que el generador bloquea ───────────────

def test_una_cuenta_sin_mcp_se_pauta_a_mano(publicando, sistema_de_juguete, monkeypatch):
    monkeypatch.setenv("VITALCOM_FAKE_META_SIN_MCP", "1")
    _publicar(publicando)
    resultado = _terminar()
    assert resultado["estado"] == "FALLIDO" and "se pauta a mano" in resultado["detalle"]
    assert "gen_publicacion.py" not in [c["script"] for c in juguete.llamadas(sistema_de_juguete)]


def test_los_bloqueantes_se_dicen_con_el_nombre_de_su_dueno(publicando, sistema_de_juguete):
    bloqueado = copy.deepcopy(meta.PAQUETE_FALSO)
    bloqueado["bloqueantes"] = [{"falta": "page_id de la cuenta", "lo_produce": "operador (_DIM_PRODUCTOS.csv)"}]
    meta.escribir_paquete(sistema_de_juguete, bloqueado)
    _publicar(publicando)
    resultado = _terminar()
    assert resultado["estado"] == "FALLIDO"
    assert "page_id de la cuenta" in resultado["detalle"] and "operador (_DIM_PRODUCTOS.csv)" in resultado["detalle"]
    assert workflows.publicado(JOB, "pendiente") is None, "no se pide aprobación de un paquete bloqueado"


# ── los candados que no dependen del modelo ───────────────────────────────────

def _argv_de_claude(base: Path) -> list[dict]:
    archivo = base / "PRODUCTOS" / "_claude_argv.log"
    return [json.loads(x) for x in archivo.read_text(encoding="utf-8").splitlines() if x]


def test_escritura_meta_solo_en_m3(publicando, sistema_de_juguete):
    """Solo la corrida de ejecución (con LLAMADAS_JSON) recibe herramientas de ESCRITURA de Meta."""
    _publicar(publicando)
    pendiente = _pendiente(JOB)
    workflows.enviar_aprobacion(JOB, 1, "APROBADA", pendiente["hash"])
    _terminar()
    corridas = _argv_de_claude(sistema_de_juguete)
    assert len(corridas) == 4, "snapshot · snapshot fresco · ejecución · snapshot de verificación"
    con_escritura = []
    for corrida in corridas:
        prompt = corrida["argv"][corrida["argv"].index("-p") + 1]
        escribe = [h for h in corrida["permitidas"] if h.split("__")[-1] in meta.ESCRITURA]
        if escribe:
            con_escritura.append(prompt)
            assert "LLAMADAS_JSON:" in prompt and "APROBÓ" in prompt
    assert len(con_escritura) == 1, "una sola corrida tiene herramientas de escritura"


def test_las_herramientas_de_escritura_solo_las_arma_la_ejecucion():
    """Estructural: la clave «escritura» de `herramientas_meta` solo se lee donde nace y donde se usa."""
    arbol = ast.parse((PAQUETE / "workflows.py").read_text(encoding="utf-8"))
    donde = {
        funcion.name
        for funcion in arbol.body if isinstance(funcion, ast.FunctionDef)
        for nodo in ast.walk(funcion)
        if isinstance(nodo, ast.Constant) and nodo.value == "escritura"
    }
    assert donde == {"_sellar_meta", "spec_de_ejecucion", "correr_meta_ejecucion"}, (
        f"las herramientas de escritura de Meta solo pueden pasar por la unidad de ejecución: {donde}"
    )


def test_no_hay_ejecucion_sin_aprobacion_sellada_antes():
    """Estructural: en `wf_meta`, la unidad de ejecución solo se arma DESPUÉS de `paso_sellar_aprobacion`."""
    arbol = ast.parse((PAQUETE / "workflows.py").read_text(encoding="utf-8"))
    cuerpo = next(n for n in ast.walk(arbol) if isinstance(n, ast.FunctionDef) and n.name == "wf_meta")
    lineas = {}
    for nodo in ast.walk(cuerpo):
        if isinstance(nodo, ast.Call):
            lineas.setdefault(ast.unparse(nodo.func), []).append(nodo.lineno)
    assert len(lineas["spec_de_ejecucion"]) == 1
    assert min(lineas["paso_sellar_aprobacion"]) < lineas["spec_de_ejecucion"][0]
    assert min(lineas["_pedir_aprobacion"]) < min(lineas["paso_sellar_aprobacion"])


def test_ninguna_accion_de_meta_esta_habilitada_en_el_manifiesto_real():
    """Hito 4: F1.publicar habilitada con confirmación del operador; todas las demás de Meta siguen deshabilitadas."""
    habilitadas_meta = {
        accion["id"]
        for accion in juguete.manifiesto_real()["acciones"]["lista"]
        if (accion["toca_meta"] or accion["ejecutor_tipo"] == "mcp") and accion["habilitada"]
    }
    assert habilitadas_meta == {"nodo.F1.publicar"}
    for accion in juguete.manifiesto_real()["acciones"]["lista"]:
        if (accion["toca_meta"] or accion["ejecutor_tipo"] == "mcp") and accion["id"] not in habilitadas_meta:
            assert accion["habilitada"] is False and accion["motivo"], accion["id"]


def test_el_evento_no_se_duplica(publicando, sistema_de_juguete):
    """Si la firma del trabajo ya está en `_EVENTOS.csv` (murió después de escribir), no se vuelve a escribir."""
    (sistema_de_juguete / "PRODUCTOS" / "_EVENTOS.csv").write_text(
        f"fecha,producto_key,evento,fuente_decision\n2026-09-18,TINNIDROP,LANZAMIENTO,publicar-meta · app job={JOB} orden=1\n",
        encoding="utf-8")
    _publicar(publicando)
    pendiente = _pendiente(JOB)
    workflows.enviar_aprobacion(JOB, 1, "APROBADA", pendiente["hash"])
    assert _terminar()["estado"] == "EXITO"
    assert "registrar_evento.py" not in [c["script"] for c in juguete.llamadas(sistema_de_juguete)]


def test_la_huella_es_estable_y_cambia_con_cualquier_argumento():
    orden = {"tipo": "paquete_publicacion", "llamadas": [{"n": 1, "tool": "ads_create_campaign", "args": {"a": 1, "b": 2}}]}
    misma_con_otro_orden = {"llamadas": [{"args": {"b": 2, "a": 1}, "tool": "ads_create_campaign", "n": 1}],
                            "tipo": "paquete_publicacion"}
    assert workflows.huella_de_la_orden(orden) == workflows.huella_de_la_orden(misma_con_otro_orden)
    cambiada = copy.deepcopy(orden)
    cambiada["llamadas"][0]["args"]["b"] = 3
    assert workflows.huella_de_la_orden(orden) != workflows.huella_de_la_orden(cambiada)


# ── las imágenes las sube el operador a la biblioteca (decisión del 18-sep-2026) ──

@pytest.fixture()
def con_media(sistema_de_juguete: Path, cliente_juguete: TestClient) -> TestClient:
    """F1.publicar con un paquete de dos piezas que el operador sube a mano."""
    meta.preparar_con_media(sistema_de_juguete)
    meta.habilitar_publicar_f1(sistema_de_juguete)
    acciones.olvidar_cache()
    return cliente_juguete


def _espera_imagenes(job_id: str, vuelta: int = 1) -> dict:
    _esperar(job_id, "ESPERA_MEDIA")
    limite = time.monotonic() + 10
    while time.monotonic() < limite:
        pendiente = workflows.publicado(job_id, "pendiente")
        if pendiente and pendiente.get("tipo") == "subida_media" and pendiente["vuelta"] == vuelta:
            return pendiente
        time.sleep(0.1)
    raise AssertionError("no apareció el pedido de subir imágenes")


def _subidas(nombres_y_hashes: dict[str, str]) -> list[dict[str, str]]:
    return [{"hash": h, "name": f"{n}.png"} for n, h in nombres_y_hashes.items()]


def test_publicar_espera_que_subas_las_imagenes_y_usa_sus_hashes(con_media, sistema_de_juguete):
    assert _publicar(con_media).status_code == 202
    pedido = _espera_imagenes(JOB)
    assert pedido["cuenta"] == "GTR7"
    assert [a["archivo_a_subir"] for a in pedido["archivos"]] == ["PX_1_V2.png", "PX_2_V2.png"]
    carpeta = Path(pedido["carpeta"])
    assert sorted(p.name for p in carpeta.iterdir()) == ["PX_1_V2.png", "PX_2_V2.png"], "listas para arrastrar"
    assert (carpeta / "PX_1_V2.png").read_bytes() == b"imagen 1", "el archivo es la pieza, con el nombre nuevo"
    assert _escrituras(sistema_de_juguete) == [], "esperando al operador: nada escribió en Meta"

    meta.subir_a_biblioteca(sistema_de_juguete, _subidas({"PX_1_V2": "hash-uno", "PX_2_V2": "hash-dos"}))
    assert con_media.post(f"/api/trabajos/{JOB}/media/1").status_code == 202

    orden = _pendiente(JOB)
    creativos = [c["args"]["image_hash"] for c in orden["orden"]["llamadas"] if c["tool"] == "ads_create_creative"]
    assert creativos == ["hash-uno", "hash-dos"], "cada creativo lleva el hash de SU imagen, literal"
    assert [(i["archivo"], i["image_hash"]) for i in orden["orden"]["imagenes"]] == [
        ("PX_1.png", "hash-uno"), ("PX_2.png", "hash-dos")], "la orden muestra qué archivo es cada hash"
    assert "ads_creative_upload_media" not in [c["tool"] for c in orden["orden"]["llamadas"]]

    workflows.enviar_aprobacion(JOB, 1, "APROBADA", orden["hash"])
    resultado = _terminar()
    assert resultado["estado"] == "EXITO", resultado
    assert _escrituras(sistema_de_juguete) == [
        "ads_create_campaign", "ads_create_ad_set", "ads_create_creative", "ads_create_ad",
        "ads_create_creative", "ads_create_ad"]
    assert meta.lecturas(sistema_de_juguete).count("ads_get_ad_images") >= 2, "antes y después de subir"


def test_un_nombre_viejo_no_se_reusa(con_media, sistema_de_juguete):
    """La biblioteca ya tiene un PX_1_V2 (de otra vez): la pieza nueva se pide como PX_1_V3."""
    meta.subir_a_biblioteca(sistema_de_juguete, _subidas({"PX_1_V2": "hash-viejo"}))
    _publicar(con_media)
    pedido = _espera_imagenes(JOB)
    assert [a["nombre_en_biblioteca"] for a in pedido["archivos"]] == ["PX_1_V3", "PX_2_V2"]
    meta.subir_a_biblioteca(sistema_de_juguete, _subidas({"PX_1_V3": "hash-nuevo", "PX_2_V2": "hash-dos"}))
    workflows.avisar_media_subida(JOB, 1)
    orden = _pendiente(JOB)
    creativos = [c["args"]["image_hash"] for c in orden["orden"]["llamadas"] if c["tool"] == "ads_create_creative"]
    assert creativos == ["hash-nuevo", "hash-dos"], "nunca el hash de la imagen vieja"


def test_si_falta_una_imagen_lo_vuelve_a_pedir(con_media, sistema_de_juguete):
    _publicar(con_media)
    _espera_imagenes(JOB)
    meta.subir_a_biblioteca(sistema_de_juguete, _subidas({"PX_1_V2": "hash-uno"}))
    workflows.avisar_media_subida(JOB, 1)

    segundo = _espera_imagenes(JOB, vuelta=2)
    estados = {a["archivo_a_subir"]: a["estado"] for a in segundo["archivos"]}
    assert estados == {"PX_1_V2.png": "OK", "PX_2_V2.png": "POR_SUBIR"}
    assert "PX_2_V2" in segundo["faltan"][0], "dice cuál falta"
    assert _escrituras(sistema_de_juguete) == []

    meta.subir_a_biblioteca(sistema_de_juguete, _subidas({"PX_2_V2": "hash-dos"}))
    workflows.avisar_media_subida(JOB, 2)
    orden = _pendiente(JOB)
    workflows.enviar_aprobacion(JOB, 1, "APROBADA", orden["hash"])
    assert _terminar()["estado"] == "EXITO"


def test_dos_imagenes_con_el_mismo_nombre_no_se_adivinan(con_media, sistema_de_juguete):
    _publicar(con_media)
    _espera_imagenes(JOB)
    meta.subir_a_biblioteca(sistema_de_juguete, _subidas({"PX_1_V2": "hash-uno", "PX_2_V2": "hash-dos"}))
    meta.subir_a_biblioteca(sistema_de_juguete, [{"hash": "hash-otro", "name": "PX_1_V2.png"}])
    workflows.avisar_media_subida(JOB, 1)
    segundo = _espera_imagenes(JOB, vuelta=2)
    repetida = next(a for a in segundo["archivos"] if a["archivo"] == "PX_1.png")
    assert repetida["estado"] == "REPETIDA" and repetida["hashes"] == ["hash-otro", "hash-uno"]
    assert workflows.publicado(JOB, "estado")["estado"] == "ESPERA_MEDIA", "no pide aprobación"


def test_si_nadie_avisa_la_subida_caduca(con_media, sistema_de_juguete):
    meta.con_respuesta_max(sistema_de_juguete, 0.0005)  # 1,8 s
    acciones.olvidar_cache()
    _publicar(con_media)
    resultado = _terminar()
    assert resultado["estado"] == "CADUCADO", resultado
    assert _escrituras(sistema_de_juguete) == []


def test_si_la_lectura_no_quedo_guardada_falla_claro(con_media, sistema_de_juguete, monkeypatch):
    monkeypatch.setenv("VITALCOM_FAKE_NO_GUARDA_IMAGENES", "1")
    _publicar(con_media)
    resultado = _terminar()
    assert resultado["estado"] == "FALLIDO" and "No quedó guardada" in resultado["detalle"], resultado
    assert workflows.publicado(JOB, "pendiente") is None, "no le pide al operador que suba con nombres sin elegir"


def test_ya_las_subi_solo_vale_para_lo_que_se_esta_esperando(con_media, sistema_de_juguete):
    _publicar(con_media)
    _espera_imagenes(JOB)
    assert con_media.post(f"/api/trabajos/{JOB}/media/2").status_code == 409, "otra vuelta"
    assert con_media.post(f"/api/trabajos/{JOB}/aprobaciones/1",
                          json={"decision": "APROBADA", "hash": "x"}).status_code == 409, "no hay orden todavía"


def test_leer_la_biblioteca_solo_usa_ads_get_ad_images(con_media, sistema_de_juguete):
    """La lectura de imágenes recibe UNA herramienta de Meta, de lectura: ni subir ni crear."""
    _publicar(con_media)
    _espera_imagenes(JOB)
    lecturas = [c for c in _argv_de_claude(sistema_de_juguete)
                if "IMAGENES_EN:" in c["argv"][c["argv"].index("-p") + 1]]
    assert lecturas, "leyó la biblioteca"
    for corrida in lecturas:
        de_meta = [h for h in corrida["permitidas"] if h.startswith("mcp__")]
        assert de_meta == ["mcp__claude_ai_META_MCP__ads_get_ad_images"], de_meta


def test_ninguna_accion_declara_la_subida_con_ventana():
    """LOCAL_FILE necesita una pantalla (spike F): ninguna acción de la app la puede recibir."""
    for accion in juguete.manifiesto_real()["acciones"]["lista"]:
        herramientas = accion.get("herramientas_meta") or {}
        assert "ads_creative_upload_media" not in [*herramientas.get("lectura", []), *herramientas.get("escritura", [])]
        if (accion.get("ordenes") or {}).get("tipo") == "paquete_publicacion":
            assert "ads_get_ad_images" in herramientas["lectura"], accion["id"]


def test_activar_con_aprobacion_ejecuta_verifica_y_registra(sistema_de_juguete, cliente_juguete):
    """nodo.F1.activar genera orden de activación, espera aprobación, corre ads_activate_entity, verifica y registra."""
    meta.preparar(sistema_de_juguete)
    meta.habilitar_activar_f1(sistema_de_juguete)
    meta.preparar_activacion(sistema_de_juguete)
    acciones.olvidar_cache()

    resp = cliente_juguete.post("/api/acciones/nodo.F1.activar", json={
        "parametros": {"producto_key": "TINNIDROP"}, "confirmado": True, "job_id": JOB})
    assert resp.status_code == 202

    pendiente = _pendiente(JOB)
    assert pendiente["tipo"] == "aprobacion"
    assert pendiente["orden"]["tipo"] == "orden_activacion"
    assert [c["tool"] for c in pendiente["orden"]["llamadas"]] == ["ads_activate_entity"]
    assert _escrituras(sistema_de_juguete) == [], "esperando al operador: nada corrió"

    workflows.enviar_aprobacion(JOB, 1, "APROBADA", pendiente["hash"], nota="activar ya")
    resultado = _terminar()
    assert resultado["estado"] == "EXITO", resultado
    assert _escrituras(sistema_de_juguete) == ["ads_activate_entity"], "la llamada de activación"

    scripts = [c["script"] for c in juguete.llamadas(sistema_de_juguete)]
    assert "verificar_activacion.py" in scripts, "el gate de activación cerró"
    evento = next(c for c in juguete.llamadas(sistema_de_juguete) if c["script"] == "registrar_evento.py")
    assert f"app job={JOB} orden=1" in evento["argv"][evento["argv"].index("--fuente") + 1]
    assert evento["argv"][evento["argv"].index("--evento") + 1] == "LANZAMIENTO"

