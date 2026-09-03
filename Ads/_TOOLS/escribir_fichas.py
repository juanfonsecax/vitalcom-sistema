# -*- coding: utf-8 -*-
"""Escribe las fichas estructurales JSON de una tanda.

Uso:  python Ads/_TOOLS/escribir_fichas.py 01

Lee   Ads/_SWIPE/_BLUEPRINTS/_datos/tandaNN.py   (el analisis visual, dict FICHAS)
      Ads/_SWIPE/_BLUEPRINTS/FICHAS/_MANIFIESTO.csv  (el bloque `origen` y `clasificacion` base)
Escribe Ads/_SWIPE/_BLUEPRINTS/FICHAS/FNNN.json

El bloque `origen` NUNCA se escribe a mano: se inyecta desde el manifiesto. Asi una ficha no
puede contradecir al CSV (regla 17 del orquestador, gate de reconciliacion).
"""
import csv, io, json, os, sys, importlib

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BP = os.path.join(BASE, "Ads", "_SWIPE", "_BLUEPRINTS")
FICHAS = os.path.join(BP, "FICHAS")
sys.path.insert(0, os.path.join(BP, "_datos"))

tanda = sys.argv[1] if len(sys.argv) > 1 else "01"

# El analisis de una tanda puede venir partido en varios modulos (tanda01.py, tanda01_p2.py...)
# porque un solo archivo de 10 fichas no entra comodo en una escritura. Se fusionan aca.
import glob as _glob
partes = sorted(os.path.basename(p)[:-3]
                for p in _glob.glob(os.path.join(BP, "_datos", "tanda%s*.py" % tanda)))
if not partes:
    raise SystemExit("no hay modulos de datos para la tanda %s" % tanda)
datos = {}
for parte in partes:
    for k, v in importlib.import_module(parte).FICHAS.items():
        if k in datos:
            raise SystemExit("%s duplicada en %s" % (k, parte))
        datos[k] = v
print("partes leidas: %s" % ", ".join(partes))

with io.open(os.path.join(FICHAS, "_MANIFIESTO.csv"), encoding="utf-8") as f:
    man = {r["ficha_id"]: r for r in csv.DictReader(f)}

# `canonico_id` NO vive en los _datos/ ni se escribe a mano: su dueno unico es el mapa FAMILIAS
# de agrupar_canonicos.py. Se importa aca para que reescribir una tanda no lo borre.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from agrupar_canonicos import FAMILIAS as _FAMILIAS
PERTENENCIA = {fid: fam["id"] for fam in _FAMILIAS for fid in fam["miembros"]}

ORDEN = ["ficha_id", "schema_version", "origen", "clasificacion", "dispositivo_dominante",
         "lectura_estrategica", "fondo", "paleta", "sistema_tipografico",
         "condiciones_de_captura", "zonas",
         "secuencia_lectura", "reglas_duras", "variables_requeridas", "cuando_usar",
         "cuando_no_usar", "sellos_y_claims_observados", "canonico_id", "blueprint_equivalente"]

# `condiciones_de_captura` solo existe en las fichas de estetica organico_ugc: ahi lo que se
# replica no es el layout sino COMO se toma la foto (angulo, luz, que imperfeccion se conserva).
# En las de cartel_publicitario la clave se omite del JSON en vez de escribirse vacia.
OPCIONALES = {"condiciones_de_captura"}

n = 0
for fid in sorted(datos):
    m = man[fid]
    d = dict(datos[fid])
    d["ficha_id"] = fid
    d["schema_version"] = "1.0"
    d["origen"] = {
        "archivo": m["archivo"],
        "anunciante": m["anunciante"],
        "ad_archive_id": m["ad_archive_id"],
        "dias_activo": int(m["dias"]),
        "replicas": int(m["replicas"]),
        "score": int(m["score"]),
        "en_banco_creativos": m["en_banco"] == "SI",
        "mercado": "Guatemala",
    }
    cl = d.setdefault("clasificacion", {})
    cl["concepto_key"] = m["concepto_key"]
    cl["variante_operador"] = m["variante_operador"] or None
    d["canonico_id"] = PERTENENCIA.get(fid)
    d.setdefault("blueprint_equivalente", None)
    d.setdefault("sellos_y_claims_observados", [])

    falta = [k for k in ORDEN if k not in d and k not in OPCIONALES]
    if falta:
        raise SystemExit("%s: faltan claves %s" % (fid, falta))
    if cl.get("estetica") == "organico_ugc" and "condiciones_de_captura" not in d:
        raise SystemExit("%s: es organico_ugc y no declara condiciones_de_captura" % fid)

    out = dict((k, d[k]) for k in ORDEN if k in d)
    with io.open(os.path.join(FICHAS, "%s.json" % fid), "w", encoding="utf-8") as f:
        f.write(json.dumps(out, ensure_ascii=False, indent=2))
    n += 1

print("tanda %s: %d fichas escritas en %s" % (tanda, n, FICHAS))
