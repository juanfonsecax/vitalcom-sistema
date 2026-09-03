# -*- coding: utf-8 -*-
"""Genera el MANIFIESTO DE FICHAS: las 111 favoritas ordenadas por score y repartidas en tandas.

Fuentes (un dato, un dueño -- no se copia nada que ya viva en otro CSV):
  _CLASIF_FAVORITOS.csv   archivo, concepto_final, dias, replicas, anunciante   <- las 111
  _ETIQUETAS_MANUALES.csv ad_archive_id por archivo                             <- para volver al origen
  _BANCO_CREATIVOS/_INDICE.csv  variante_operador                               <- 2a opinion del operador

Escribe Ads/_SWIPE/_BLUEPRINTS/FICHAS/_MANIFIESTO.csv

score = dias + replicas*25   (la misma formula de gen_winners.py -- no se inventa otra)
"""
import csv, io, os, sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # .../Ads
SWIPE = os.path.join(BASE, "_SWIPE")
SALIDA = os.path.join(SWIPE, "_BLUEPRINTS", "FICHAS", "_MANIFIESTO.csv")
TANDA = 10


def leer(p):
    with io.open(p, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


favs = leer(os.path.join(SWIPE, "_CLASIF_FAVORITOS.csv"))

# ad_archive_id por ruta de archivo
ids = {}
for r in leer(os.path.join(SWIPE, "_ETIQUETAS_MANUALES.csv")):
    ids[r["archivo"].replace("\\", "/")] = r["ad_archive_id"]

# variante del operador, por ruta de origen
variantes = {}
for r in leer(os.path.join(SWIPE, "_BANCO_CREATIVOS", "_INDICE.csv")):
    variantes[r["origen_img"].replace("\\", "/")] = r["variante_operador"]

filas = []
for r in favs:
    a = r["archivo"].replace("\\", "/")
    dias = int(r["dias"] or 0)
    rep = int(r["replicas"] or 0)
    filas.append({
        "archivo": a,
        "concepto_key": r["concepto_final"],
        "anunciante": r["anunciante"],
        "dias": dias,
        "replicas": rep,
        "score": dias + rep * 25,
        "ad_archive_id": ids.get(a, ""),
        "variante_operador": variantes.get(a, ""),
        "en_banco": "SI" if a in variantes else "NO",
    })

filas.sort(key=lambda x: (-x["score"], x["concepto_key"], x["archivo"]))

for i, f in enumerate(filas):
    f["ficha_id"] = "F%03d" % (i + 1)
    f["tanda"] = i // TANDA + 1
    f["ruta_json"] = "FICHAS/%s.json" % f["ficha_id"]

cols = ["ficha_id", "tanda", "score", "concepto_key", "variante_operador",
        "anunciante", "dias", "replicas", "en_banco", "ad_archive_id",
        "archivo", "ruta_json"]

with io.open(SALIDA, "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols)
    w.writeheader()
    for r in filas:
        w.writerow({k: r[k] for k in cols})

print("escritas %d fichas en %d tandas -> %s" % (len(filas), filas[-1]["tanda"], SALIDA))
from collections import Counter
for k, v in Counter(f["concepto_key"] for f in filas).most_common():
    print("  %-18s %d" % (k, v))
