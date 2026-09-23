"""Las pantallas de FASE 1 (Hito 4) y la carga de un dato desde el checklist, sobre el sistema de juguete.

Lo que se congela:
  * la corrida muestra el avance por paso y lo que devolvió cada etapa, textual;
  * el flujo del bot y el checklist son lo que dicen sus scripts dueños, con el escritor de cada bloqueo
    tomado del manifiesto (`escritores_de_bloqueo`, `datos_del_operador`);
  * cargar un dato solo acepta las acciones escritoras que el manifiesto nombra, y el archivo entra por
    el temporal de la subida, nunca directo al sistema;
  * la media se sirve solo desde la carpeta de media del producto.
"""

from __future__ import annotations

import json
from pathlib import Path

import sistema_de_juguete as juguete

from vitalcom_app import fase1, workflows

JOB = "a" * 32

FLUJO_BOT_FALSO = '''import json, sys
print(json.dumps({"producto_key": sys.argv[1], "ok": True, "faltan": [], "avisos": [], "prohibiciones": [],
    "encabezado": {"lineas": ["FLUJO"], "instrucciones": []},
    "secciones": [{"titulo": "INTERACCIONES", "instrucciones": [], "bloques": [
        {"titulo": "INTERACCIÓN 1 — X", "pegar": "Hola", "instrucciones": ["no se pega"], "pendientes": []}]}]}))
'''

GEN_PUBLICACION_FALSO = '''import json, sys
print(json.dumps({"bloqueantes": [
    {"falta": "no hay page_id", "lo_produce": "etapa-fanpage", "ambito": "paquete", "clave": "page_id"},
    {"falta": "2 pieza(s) sin archivo", "lo_produce": "etapa-render / el operador", "ambito": "paquete",
     "clave": "piezas", "archivos": ["TINNIDROP_1_A.png", "TINNIDROP_2_B.png"]},
    {"falta": "la firma sale con ?", "lo_produce": "etapa-6", "ambito": "paquete"}],
  "avisos": ["un aviso"], "preflight": [{"verificar": "que la pagina tenga WhatsApp"}]}))
sys.exit(1)
'''


def _preparar(base: Path, nodo: str = "F1.paquete") -> None:
    juguete.escribir_flujo_falso(base, {"*": juguete.flujo_listo(nodo, cumplido=True)})
    juguete.escribir_script(base, "gen_flujo_bot.py", FLUJO_BOT_FALSO)
    juguete.escribir_script(base, "gen_publicacion.py", GEN_PUBLICACION_FALSO)


def test_la_corrida_muestra_el_avance_y_lo_que_devolvio_cada_etapa(cliente_juguete, sistema_de_juguete):
    _preparar(sistema_de_juguete)
    assert cliente_juguete.get("/api/productos/TINNIDROP/fase1/corrida").json()["corrida"] is None
    cliente_juguete.post("/api/acciones/nodo.F1.paquete", json={
        "parametros": {"producto_key": "TINNIDROP"}, "confirmado": True, "job_id": JOB})
    resultado = workflows.esperar_resultado(JOB, 120)
    assert resultado["estado"] == "EXITO", (resultado["detalle"], resultado["unidades"][-1])
    datos = cliente_juguete.get("/api/productos/TINNIDROP/fase1/corrida").json()
    # F1.paquete corre TODO EN IMAGEN (decisión operador 22-sep-2026): 8 pasos, sin ningún script.
    assert datos["corrida"]["job_id"] == JOB and len(datos["corrida"]["pasos"]) == 8
    por_etapa = {e["etapa"]: e for e in datos["etapas"]}
    assert por_etapa["etapa-1b"]["texto"].startswith("SALIDA DE etapa-1b (fake)")
    assert por_etapa["etapa-2"]["paso"] == por_etapa["etapa-fanpage"]["paso"] == 5


def test_flujo_bot_y_checklist_son_los_de_sus_scripts(cliente_juguete, sistema_de_juguete):
    _preparar(sistema_de_juguete)
    flujo = cliente_juguete.get("/api/productos/TINNIDROP/flujo-bot").json()
    bloque = flujo["secciones"][0]["bloques"][0]
    assert bloque["pegar"] == "Hola" and bloque["instrucciones"] == ["no se pega"]

    checklist = cliente_juguete.get("/api/productos/TINNIDROP/checklist").json()
    assert checklist["nodo_actual"] == "F1.paquete"
    por_clave = {b.get("clave"): b for b in checklist["paquete"]["bloqueantes"]}
    assert por_clave["page_id"]["escritor"] == "producto.cargar_page_id"
    assert por_clave["piezas"]["escritor"] == "producto.cargar_pieza"
    assert por_clave["piezas"]["archivos"] == ["TINNIDROP_1_A.png", "TINNIDROP_2_B.png"]
    assert por_clave[None]["escritor"] is None, "un bloqueo que produce una etapa no ofrece campo"
    assert checklist["paquete"]["preflight"] == [{"verificar": "que la pagina tenga WhatsApp"}]


def test_los_datos_del_nodo_traen_su_escritor_y_sus_alternativas(cliente_juguete, sistema_de_juguete):
    juguete.escribir_flujo_falso(sistema_de_juguete, {"*": juguete.flujo_listo(
        "F1.congelar_inputs", estado="BLOQUEADO",
        falta=[{"dato": "≥6 transcripciones TXT", "ok": False, "observado": "2 archivo(s)"}])})
    checklist = cliente_juguete.get("/api/productos/TINNIDROP/checklist").json()
    assert checklist["faltan"][0]["escritores"] == ["producto.transcribir", "producto.cargar_transcripcion"]
    assert checklist["paquete"] is None, "gen_publicacion solo se consulta desde que hay paquete que juzgar"


def test_cargar_un_dato_pasa_por_la_accion_escritora_y_el_temporal(cliente_juguete, sistema_de_juguete):
    _preparar(sistema_de_juguete)
    respuesta = cliente_juguete.post(
        "/api/productos/TINNIDROP/cargar/producto.cargar_pieza",
        data={"datos": json.dumps({"archivo": "TINNIDROP_1_A.png"})},
        files={"archivo": ("mi foto.png", b"\x89PNG\r\n\x1a\nxx", "image/png")})
    assert respuesta.status_code == 200, respuesta.text
    llamada = [c for c in juguete.llamadas(sistema_de_juguete) if c["script"] == "cargar_pieza.py"][-1]["argv"]
    assert llamada[:4] == ["--producto", "TINNIDROP", "--archivo", "TINNIDROP_1_A.png"]
    origen = llamada[llamada.index("--origen") + 1]
    assert "vitalcom-subida-" in origen and not Path(origen).exists(), "el temporal se borra al terminar"

    respuesta = cliente_juguete.post("/api/productos/TINNIDROP/cargar/producto.cargar_page_id",
                                     data={"datos": json.dumps({"page_id": "1279576438561754"})})
    assert respuesta.status_code == 200, respuesta.text


def test_cargar_rechaza_lo_que_no_es_un_escritor_del_checklist(cliente_juguete, sistema_de_juguete):
    for accion in ("nodo.ciclo.motor", "producto.alta", "sistema.gen_app", "no.existe"):
        respuesta = cliente_juguete.post(f"/api/productos/TINNIDROP/cargar/{accion}", data={"datos": "{}"})
        assert respuesta.status_code == 403 and respuesta.json()["codigo"] == "NO_ES_UN_ESCRITOR", accion
    faltante = cliente_juguete.post("/api/productos/TINNIDROP/cargar/producto.cargar_pieza",
                                    data={"datos": json.dumps({"archivo": "X.png"})})
    assert faltante.status_code == 422, "sin archivo no se carga una pieza"
    assert cliente_juguete.post("/api/productos/NO_EXISTE/cargar/producto.cargar_page_id",
                                data={"datos": "{}"}).status_code == 404


def test_los_escritores_permitidos_son_los_que_nombra_el_manifiesto(sistema_de_juguete):
    assert fase1.escritores_permitidos() == {
        "producto.cambiar_costo", "producto.cargar_transcripcion", "producto.cargar_pieza",
        "producto.cargar_cuenta", "producto.cargar_page_id"}


def test_la_media_se_sirve_solo_desde_su_carpeta(cliente_juguete, sistema_de_juguete):
    productos = sistema_de_juguete / "PRODUCTOS" / "_DIM_PRODUCTOS.csv"
    juguete._csv(productos, [*juguete.COLUMNAS_PRODUCTOS, "carpeta_media"], [
        {"producto_key": "TINNIDROP", "nombre_display": "Tinnidrop", "estado": "VIVO", "carpeta_media": "MEDIA_T"}])
    (sistema_de_juguete / "Ads" / "MEDIA_T").mkdir()
    (sistema_de_juguete / "Ads" / "MEDIA_T" / "T_1.png").write_bytes(b"\x89PNG")
    (sistema_de_juguete / "Ads" / "secreto.png").write_bytes(b"no")
    assert cliente_juguete.get("/api/productos/TINNIDROP/media/T_1.png").content == b"\x89PNG"
    for malo in ("T_1.txt", "no_existe.png"):
        assert cliente_juguete.get(f"/api/productos/TINNIDROP/media/{malo}").status_code == 404, malo
    # `..` lo normaliza el cliente y la ruta ya no es la de media: lo que importa es que nunca sale de la carpeta
    assert cliente_juguete.get("/api/productos/TINNIDROP/media/..%2Fsecreto.png").content != b"no"
    assert fase1.ruta_de_media("TINNIDROP", "../secreto.png") is None
    assert fase1.ruta_de_media("TINNIDROP", "..\\secreto.png") is None
