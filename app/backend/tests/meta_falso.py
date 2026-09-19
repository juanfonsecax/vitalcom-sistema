"""Un «Meta» de mentira para probar `wf_meta`: ni una llamada real.

  * `gen_publicacion.py` falso: emite el paquete de `PRODUCTOS/_paquete_falso.json` y marca `omitir`
    lo que el snapshot ya tiene (igual que el real). Sale con 1 si el paquete trae bloqueantes.
    Si el paquete trae `media` y se pide `--media biblioteca`, hace lo que el real: elige para cada
    pieza el primer `_V2`, `_V3`… libre en el volcado de ANTES y busca su hash en el de DESPUÉS.
    Lo que falta sale como bloqueante de ámbito `media`.
  * La «biblioteca de imágenes» de la cuenta vive en `PRODUCTOS/_meta_imagenes.json`: el operador
    «sube» con `subir_a_biblioteca()` y `fake_claude.py` la lee cuando le piden `IMAGENES_EN:`.
  * `verificar_publicacion.py` falso: exit 0 si «Meta» tiene todos los objetos que el paquete crea.
  * `fake_claude.py` es quien «llama» a las herramientas de Meta y anota lo que corrió en
    `PRODUCTOS/_meta_llamadas.log`; lo que «existe en Meta» vive en `PRODUCTOS/_meta_existente.json`.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import sistema_de_juguete as juguete

GEN_PUBLICACION_FALSO = '''import json, pathlib, sys
BASE = pathlib.Path(__file__).resolve().parents[2]
with open(BASE / "PRODUCTOS" / "_llamadas.log", "a", encoding="utf-8") as archivo:
    archivo.write(json.dumps({"script": "gen_publicacion.py", "argv": sys.argv[1:]}) + "\\n")
def valor(bandera):
    return sys.argv[sys.argv.index(bandera) + 1] if bandera in sys.argv else None
paquete = json.loads((BASE / "PRODUCTOS" / "_paquete_falso.json").read_text(encoding="utf-8"))
snapshot = valor("--snapshot")
existentes = {}
if snapshot and pathlib.Path(snapshot).is_file():
    for e in json.loads(pathlib.Path(snapshot).read_text(encoding="utf-8"))["ad_entities"]:
        existentes[e["name"]] = e["id"]
for llamada in paquete["llamadas"]:
    a = llamada["args"]
    nombre = a.get("campaign_name") or a.get("ad_set_name") or a.get("ad_name") or ""
    llamada["omitir"] = nombre in existentes
    if llamada["omitir"]:
        llamada["id_existente"] = existentes[nombre]
def listado(bandera):
    ruta = valor(bandera)
    if not ruta or not pathlib.Path(ruta).is_file():
        return None
    return json.loads(pathlib.Path(ruta).read_text(encoding="utf-8"))["imagenes"]
def normal(nombre):
    n = nombre.strip()
    return (n.rsplit(".", 1)[0] if n.lower().endswith((".png", ".jpg", ".jpeg")) else n).lower()
media = paquete.get("media")
if media and valor("--media") == "biblioteca":
    antes, despues = listado("--imagenes-antes"), listado("--imagenes-despues")
    media["listado_antes"], media["listado_despues"] = antes is not None, despues is not None
    ocupados = {normal(i["name"]) for i in antes or []}
    hash_de = {}
    for pieza in media["piezas"]:
        base = pieza["archivo"].rsplit(".", 1)[0]
        pieza.update({"nombre_en_biblioteca": None, "image_hash": None, "estado": "SIN_LISTADO", "hashes": []})
        if antes is not None:
            k = 2
            while normal(f"{base}_V{k}") in ocupados:
                k += 1
            pieza["nombre_en_biblioteca"] = f"{base}_V{k}"
            pieza["estado"] = "POR_SUBIR"
            if despues is not None:
                hashes = sorted({i["hash"] for i in despues if normal(i["name"]) == normal(pieza["nombre_en_biblioteca"])})
                pieza["hashes"] = hashes
                pieza["estado"] = "OK" if len(hashes) == 1 else "REPETIDA" if hashes else "POR_SUBIR"
                pieza["image_hash"] = hashes[0] if len(hashes) == 1 else None
        hash_de[pieza["archivo"]] = pieza["image_hash"] or "{{FALTA_HASH}}"
    for llamada in paquete["llamadas"]:
        if llamada["tool"] == "ads_create_creative":
            llamada["args"]["image_hash"] = hash_de[llamada["archivo"]]
    faltan = [p for p in media["piezas"] if p["estado"] != "OK"]
    if antes is None:
        paquete["bloqueantes"] = [{"falta": "falta leer la biblioteca", "lo_produce": "publicar-meta", "ambito": "media"}]
    elif faltan:
        paquete["bloqueantes"] = [{"falta": "falta subir: " + ", ".join(p["nombre_en_biblioteca"] for p in faltan),
                                   "lo_produce": "el operador", "ambito": "media"}]
salida = valor("--salida")
if salida:
    pathlib.Path(salida).write_text(json.dumps(paquete), encoding="utf-8")
print(json.dumps(paquete))
sys.exit(1 if paquete.get("bloqueantes") else 0)
'''

VERIFICAR_FALSO = '''import json, pathlib, sys
BASE = pathlib.Path(__file__).resolve().parents[2]
with open(BASE / "PRODUCTOS" / "_llamadas.log", "a", encoding="utf-8") as archivo:
    archivo.write(json.dumps({"script": "verificar_publicacion.py", "argv": sys.argv[1:]}) + "\\n")
paquete = json.loads((BASE / "PRODUCTOS" / "_paquete_falso.json").read_text(encoding="utf-8"))
existe = pathlib.Path(BASE / "PRODUCTOS" / "_meta_existente.json")
nombres = {e["name"] for e in json.loads(existe.read_text(encoding="utf-8"))} if existe.is_file() else set()
falta = []
for c in paquete["llamadas"]:
    if c["tool"] in ("ads_create_campaign", "ads_create_ad_set", "ads_create_ad"):
        a = c["args"]
        nombre = a.get("campaign_name") or a.get("ad_set_name") or a.get("ad_name")
        if nombre not in nombres:
            falta.append(nombre)
if falta:
    print("FALTA en Meta: " + ", ".join(falta))
    sys.exit(1)
'''

GEN_ACTIVACION_FALSO = '''import json, pathlib, sys
BASE = pathlib.Path(__file__).resolve().parents[2]
with open(BASE / "PRODUCTOS" / "_llamadas.log", "a", encoding="utf-8") as archivo:
    archivo.write(json.dumps({"script": "gen_orden_activacion.py", "argv": sys.argv[1:]}) + "\\n")
def valor(bandera):
    return sys.argv[sys.argv.index(bandera) + 1] if bandera in sys.argv else None
paquete = json.loads((BASE / "PRODUCTOS" / "_paquete_activacion_falso.json").read_text(encoding="utf-8"))
snapshot = valor("--snapshot")
if snapshot and pathlib.Path(snapshot).is_file():
    for e in json.loads(pathlib.Path(snapshot).read_text(encoding="utf-8"))["ad_entities"]:
        if e.get("id") == "120251463036910595" and e.get("status") == "ACTIVE":
            paquete["llamadas"][0]["omitir"] = True
            paquete["llamadas"][0]["id_existente"] = "120251463036910595"
salida = valor("--salida")
if salida:
    pathlib.Path(salida).write_text(json.dumps(paquete), encoding="utf-8")
print(json.dumps(paquete))
sys.exit(1 if paquete.get("bloqueantes") else 0)
'''

VERIFICAR_ACTIVACION_FALSO = '''import json, pathlib, sys
BASE = pathlib.Path(__file__).resolve().parents[2]
with open(BASE / "PRODUCTOS" / "_llamadas.log", "a", encoding="utf-8") as archivo:
    archivo.write(json.dumps({"script": "verificar_activacion.py", "argv": sys.argv[1:]}) + "\\n")
def valor(bandera):
    return sys.argv[sys.argv.index(bandera) + 1] if bandera in sys.argv else None
snapshot = valor("--snapshot")
if snapshot and pathlib.Path(snapshot).is_file():
    entidades = json.loads(pathlib.Path(snapshot).read_text(encoding="utf-8"))["ad_entities"]
    activa = any(e.get("id") == "120251463036910595" and e.get("status") == "ACTIVE" for e in entidades)
    if activa:
        print("OK: ACTIVE")
        sys.exit(0)
print("FALLA: no está ACTIVE")
sys.exit(1)
'''

PAQUETE_ACTIVACION_FALSO: dict[str, Any] = {
    "bloqueantes": [],
    "manifiesto": {"campana_id": "120251463036910595", "evento": "LANZAMIENTO"},
    "llamadas": [
        {"n": 1, "tool": "ads_activate_entity", "args": {"entity_id": "120251463036910595"}},
    ],
}


PAQUETE_FALSO: dict[str, Any] = {
    "bloqueantes": [],
    "manifiesto": {"campana": "GTR7_TINNIDROP_F1", "total_conjuntos": 1, "total_anuncios": 1},
    "llamadas": [
        {"n": 1, "tool": "ads_create_campaign", "args": {"campaign_name": "GTR7_TINNIDROP_F1", "status": "PAUSED"},
         "guardar_como": "campaign_id"},
        {"n": 2, "tool": "ads_create_ad_set",
         "args": {"ad_set_name": "CJ1", "campaign_id": "{{campaign_id}}", "status": "PAUSED"},
         "guardar_como": "adset_id_1"},
        {"n": 3, "tool": "ads_create_creative", "args": {"name": "CR1", "page_id": "123"},
         "guardar_como": "creative_id_1"},
        {"n": 4, "tool": "ads_create_ad",
         "args": {"ad_name": "AD1", "adset_id": "{{adset_id_1}}", "status": "PAUSED"}, "guardar_como": "ad_id_1"},
    ],
}

# El mismo paquete, pero con dos piezas que el operador sube a mano a la biblioteca (--media biblioteca).
PAQUETE_CON_MEDIA: dict[str, Any] = {
    "bloqueantes": [],
    "manifiesto": {"campana": "GTR7_PX_F1", "total_conjuntos": 1, "total_anuncios": 2},
    "media": {"modo": "biblioteca", "cuenta_alias": "GTR7", "cuenta_id": "598687956219141", "piezas": [
        {"archivo": "PX_1.png", "ruta": "Ads/MEDIA_PX/PX_1.png"},
        {"archivo": "PX_2.png", "ruta": "Ads/MEDIA_PX/PX_2.png"}]},
    "llamadas": [
        {"n": 1, "tool": "ads_create_campaign", "args": {"campaign_name": "GTR7_PX_F1", "status": "PAUSED"},
         "guardar_como": "campaign_id"},
        {"n": 2, "tool": "ads_create_ad_set",
         "args": {"ad_set_name": "CJ1", "campaign_id": "{{campaign_id}}", "status": "PAUSED"},
         "guardar_como": "adset_id_1"},
        {"n": 3, "tool": "ads_create_creative", "archivo": "PX_1.png",
         "args": {"name": "CR1", "page_id": "123", "image_hash": "{{FALTA_HASH}}"}, "guardar_como": "creative_id_1"},
        {"n": 4, "tool": "ads_create_ad",
         "args": {"ad_name": "AD1", "adset_id": "{{adset_id_1}}", "status": "PAUSED"}, "guardar_como": "ad_id_1"},
        {"n": 5, "tool": "ads_create_creative", "archivo": "PX_2.png",
         "args": {"name": "CR2", "page_id": "123", "image_hash": "{{FALTA_HASH}}"}, "guardar_como": "creative_id_2"},
        {"n": 6, "tool": "ads_create_ad",
         "args": {"ad_name": "AD2", "adset_id": "{{adset_id_1}}", "status": "PAUSED"}, "guardar_como": "ad_id_2"},
    ],
}

ESCRITURA = ("ads_create_campaign", "ads_create_ad_set", "ads_create_creative", "ads_create_ad")
ESCRITURA_ACTIVACION = ("ads_activate_entity",)
TODAS_LAS_ESCRITURAS = (*ESCRITURA, *ESCRITURA_ACTIVACION)


def preparar(base: Path) -> None:
    """Deja el sistema de juguete listo para publicar: scripts falsos, paquete y el flujo en F1.publicar."""
    juguete.escribir_script(base, "gen_publicacion.py", GEN_PUBLICACION_FALSO)
    juguete.escribir_script(base, "verificar_publicacion.py", VERIFICAR_FALSO)
    escribir_paquete(base, PAQUETE_FALSO)
    juguete.escribir_flujo_falso(base, {"*": juguete.flujo_listo("F1.publicar", cumplido=True)})


def habilitar_publicar_f1(base: Path, **cambios_a_ordenes: Any) -> None:
    """El manifiesto real deja `nodo.F1.publicar` deshabilitado; el juguete lo habilita para probar el MECANISMO."""
    manifiesto = juguete.manifiesto_real()
    for accion in manifiesto["acciones"]["lista"]:
        if accion["id"] == "nodo.F1.publicar":
            accion["habilitada"] = True
            accion.pop("motivo", None)
            accion["ordenes"].update(cambios_a_ordenes)
    juguete.escribir_manifiesto(base, manifiesto)


def habilitar_activar_f1(base: Path, **cambios_a_ordenes: Any) -> None:
    """Habilita nodo.F1.activar en el juguete para probar el mecanismo de activación."""
    manifiesto = json.loads((base / "VISTAS" / "_MANIFIESTO.json").read_text(encoding="utf-8"))
    for accion in manifiesto["acciones"]["lista"]:
        if accion["id"] == "nodo.F1.activar":
            accion["habilitada"] = True
            accion.pop("motivo", None)
            if cambios_a_ordenes:
                accion["ordenes"].update(cambios_a_ordenes)
    juguete.escribir_manifiesto(base, manifiesto)


def preparar_activacion(base: Path, campaign_id: str = "120251463036910595") -> None:
    """Prepara el juguete para F1.activar: scripts falsos, flujo en F1.activar y campaña PAUSED en Meta existente."""
    juguete.escribir_script(base, "gen_orden_activacion.py", GEN_ACTIVACION_FALSO)
    juguete.escribir_script(base, "verificar_activacion.py", VERIFICAR_ACTIVACION_FALSO)
    (base / "PRODUCTOS" / "_paquete_activacion_falso.json").write_text(json.dumps(PAQUETE_ACTIVACION_FALSO), encoding="utf-8")
    poner_en_meta(base, [{"id": campaign_id, "name": "GTR0_TINNIDROP_F1", "nivel": "campaign", "status": "PAUSED"}])
    juguete.escribir_flujo_falso(base, {"*": juguete.flujo_listo("F1.activar", cumplido=True)})
    juguete._csv(base / "PRODUCTOS" / "_DIM_PRODUCTOS.csv", juguete.COLUMNAS_PRODUCTOS, [
        {"producto_key": "TINNIDROP", "nombre_display": "Tinnidrop", "estado": "VIVO", "cuenta_alias": "GTR 7", "campaign_id": campaign_id},
        {"producto_key": "NUSAVA", "nombre_display": "Nusava", "estado": "VIVO", "cuenta_alias": "GTR 7"},
    ])


def escribir_paquete(base: Path, paquete: dict[str, Any]) -> None:
    (base / "PRODUCTOS" / "_paquete_falso.json").write_text(json.dumps(paquete), encoding="utf-8")


def meta_tiene(base: Path) -> list[str]:
    archivo = base / "PRODUCTOS" / "_meta_existente.json"
    return [e["name"] for e in json.loads(archivo.read_text(encoding="utf-8"))] if archivo.is_file() else []


def poner_en_meta(base: Path, entidades: list[dict[str, str]]) -> None:
    """Simula que algo YA existe en Meta (lo que un snapshot fresco va a ver)."""
    (base / "PRODUCTOS" / "_meta_existente.json").write_text(json.dumps(entidades), encoding="utf-8")


def llamadas_de_escritura(base: Path) -> list[dict[str, Any]]:
    """Las llamadas de ESCRITURA que «Meta» recibió, en orden."""
    archivo = base / "PRODUCTOS" / "_meta_llamadas.log"
    if not archivo.is_file():
        return []
    filas = [json.loads(x) for x in archivo.read_text(encoding="utf-8").splitlines() if x]
    return [f for f in filas if f["herramienta"] in TODAS_LAS_ESCRITURAS]


def preparar_con_media(base: Path) -> None:
    """El juguete con un paquete que necesita dos imágenes subidas a mano, y esas imágenes en disco."""
    preparar(base)
    escribir_paquete(base, PAQUETE_CON_MEDIA)
    carpeta = base / "Ads" / "MEDIA_PX"
    carpeta.mkdir(parents=True, exist_ok=True)
    for i in (1, 2):
        (carpeta / f"PX_{i}.png").write_bytes(b"imagen %d" % i)


def subir_a_biblioteca(base: Path, imagenes: list[dict[str, str]]) -> None:
    """Simula que el operador subió estas imágenes a la biblioteca de la cuenta ({hash, name})."""
    archivo = base / "PRODUCTOS" / "_meta_imagenes.json"
    previas = json.loads(archivo.read_text(encoding="utf-8")) if archivo.is_file() else []
    archivo.write_text(json.dumps([*previas, *imagenes]), encoding="utf-8")


def con_respuesta_max(base: Path, horas: float) -> None:
    """Otro tope para esperar al operador (el bloque `claude` del manifiesto del juguete)."""
    manifiesto = json.loads((base / "VISTAS" / "_MANIFIESTO.json").read_text(encoding="utf-8"))
    manifiesto["acciones"]["claude"]["respuesta_max_horas"] = horas
    juguete.escribir_manifiesto(base, manifiesto)


def lecturas(base: Path) -> list[str]:
    """Las herramientas de LECTURA de Meta que se llamaron, en orden."""
    archivo = base / "PRODUCTOS" / "_meta_llamadas.log"
    if not archivo.is_file():
        return []
    filas = [json.loads(x) for x in archivo.read_text(encoding="utf-8").splitlines() if x]
    return [f["herramienta"] for f in filas if f.get("lectura")]
