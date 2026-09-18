"""Un «Meta» de mentira para probar `wf_meta`: ni una llamada real.

  * `gen_publicacion.py` falso: emite el paquete de `PRODUCTOS/_paquete_falso.json` y marca `omitir`
    lo que el snapshot ya tiene (igual que el real). Sale con 1 si el paquete trae bloqueantes.
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

ESCRITURA = ("ads_create_campaign", "ads_create_ad_set", "ads_create_creative", "ads_create_ad")


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
    return [f for f in filas if f["herramienta"] in ESCRITURA]
