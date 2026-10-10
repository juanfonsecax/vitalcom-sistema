#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""marcar_generados.py — pasa a GENERADO los conceptos IMAGEN cuyo archivo ya esta en disco.

Cuando el operador renderiza a mano en ChatGPT y guarda cada imagen en Ads/<carpeta_media>/ con
el nombre exacto de la columna `archivo` de su fila en PRODUCTOS/_DIM_CREATIVOS.csv, esa fila
sigue en PENDIENTE_GENERAR y flujo.py (nodo F2.conceptos) no la cuenta. Este script cierra ese
paso: solo cambia `estado` PENDIENTE_GENERAR -> GENERADO, nada mas de la fila.

Reglas:
  - Solo formato IMAGEN. El video pasa por LAVADO.md y no se promueve aca.
  - El archivo debe existir, pesar > 0 bytes y ser PNG o JPEG de verdad (firma de bytes).
  - La carpeta sale de _DIM_PRODUCTOS.csv (`carpeta_media`; sin valor, MEDIA_<producto_key>).

USO:
  python Ads/_TOOLS/marcar_generados.py PRODUCTO_KEY [--angulo ANGULO_KEY] [--escribir] [--json]

Sin --escribir solo informa. Exit 0 si corrio; 1 si el producto no existe.
"""
import argparse
import csv
import io
import json
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PENDIENTE = "PENDIENTE_GENERAR"
GENERADO = "GENERADO"
FIRMAS = (b"\x89PNG\r\n\x1a\n", b"\xff\xd8\xff")


def _ruta(*a):
    return os.path.join(BASE, *a)


def _imagen_valida(ruta):
    """Existe, pesa > 0 y empieza con la firma de un PNG o un JPEG."""
    try:
        if not os.path.isfile(ruta) or os.path.getsize(ruta) == 0:
            return False
        with open(ruta, "rb") as fh:
            cabecera = fh.read(8)
    except OSError:
        return False
    return any(cabecera.startswith(f) for f in FIRMAS)


def _carpeta_media(producto_key):
    ruta = _ruta("PRODUCTOS", "_DIM_PRODUCTOS.csv")
    with io.open(ruta, encoding="utf-8-sig", newline="") as fh:
        for r in csv.DictReader(fh):
            if r.get("producto_key") == producto_key:
                return (r.get("carpeta_media") or "").strip() or "MEDIA_" + producto_key
    return None


def marcar(producto_key, angulo_key, escribir):
    carpeta = _carpeta_media(producto_key)
    if carpeta is None:
        raise KeyError(producto_key)
    ruta_csv = _ruta("PRODUCTOS", "_DIM_CREATIVOS.csv")
    with open(ruta_csv, "rb") as fh:
        crudo = fh.read()
    fin = "\r\n" if b"\r\n" in crudo else "\n"
    bom = crudo.startswith(b"\xef\xbb\xbf")
    with io.open(ruta_csv, encoding="utf-8-sig", newline="") as fh:
        lector = csv.DictReader(fh)
        columnas = list(lector.fieldnames)
        filas = list(lector)

    promovidos, faltan, ya = [], [], []
    for r in filas:
        if r.get("producto_key") != producto_key:
            continue
        if angulo_key and r.get("angulo_key") != angulo_key:
            continue
        if (r.get("formato") or "").strip().upper() != "IMAGEN":
            continue
        estado = (r.get("estado") or "").strip()
        if estado == GENERADO:
            ya.append(r["creativo_id"])
        elif estado == PENDIENTE:
            if _imagen_valida(_ruta("Ads", carpeta, r.get("archivo") or "")):
                promovidos.append(r["creativo_id"])
                r["estado"] = GENERADO
            else:
                faltan.append(r["creativo_id"])

    escribio = bool(escribir and promovidos)
    if escribio:
        with io.open(ruta_csv, "w", encoding="utf-8-sig" if bom else "utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=columnas, lineterminator=fin)
            w.writeheader()
            w.writerows(filas)
    return {"producto_key": producto_key, "angulo_key": angulo_key, "carpeta_media": carpeta,
            "promovidos": promovidos, "faltan_archivo": faltan, "ya_generados": ya,
            "escribio": escribio}


def main(argv=None):
    ap = argparse.ArgumentParser(description="Marca GENERADO los conceptos IMAGEN que ya tienen su archivo")
    ap.add_argument("producto", help="producto_key")
    ap.add_argument("--angulo", default=None, help="angulo_key; sin el, todos los angulos del producto")
    ap.add_argument("--escribir", action="store_true", help="persiste el cambio de estado (sin esto solo informa)")
    ap.add_argument("--json", action="store_true", help="stdout = un solo JSON")
    args = ap.parse_args(argv)
    try:
        r = marcar(args.producto, args.angulo, args.escribir)
    except KeyError:
        print("BLOQUEANTE: '%s' no tiene fila en PRODUCTOS/_DIM_PRODUCTOS.csv." % args.producto,
              file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(r, ensure_ascii=False))
        return 0
    verbo = "PROMOVIDOS" if r["escribio"] else "SE PROMOVERIAN (falta --escribir)"
    print("%s: %d  | sin archivo valido: %d  | ya GENERADO: %d"
          % (verbo, len(r["promovidos"]), len(r["faltan_archivo"]), len(r["ya_generados"])))
    for cid in r["faltan_archivo"]:
        print("  falta imagen en Ads/%s/ para %s" % (r["carpeta_media"], cid))
    return 0


if __name__ == "__main__":
    sys.exit(main())
