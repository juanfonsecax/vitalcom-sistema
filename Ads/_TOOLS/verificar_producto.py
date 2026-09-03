#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""verificar_producto.py — el GATE DE RECONCILIACION, ejecutable.

Por que existe
--------------
El invariante 9 de CLAUDE.md prohibe declarar un producto completo hasta
verificar que costo, precio, dosis, pagina y campaign_id coinciden identicos
entre archivos. Estaba escrito en prosa, asi que se verificaba a ojo — y a ojo
se pasa por alto justo lo que hay que atrapar. Esto lo convierte en un pase o un
fallo que el sistema puede leer.

`etapa-guardar-producto` lo ejecuta y NO cierra hasta que salga con codigo 0.

Que compara
-----------
  1. El encabezado de 1_/2_/3_ entre si (coherencia interna del paquete).
  2. Esos encabezados contra PRODUCTOS/_DIM_PRODUCTOS.csv (la fuente estructurada).
  3. Que su fila del registro maestro declare estado y fase — sin eso la
     auditoria diaria no sabe si auditarlo (invariante 8).

La carpeta del producto NUNCA se adivina por el nombre: se resuelve por
`slug_carpeta` de _DIM_PRODUCTOS.csv (invariante 10).

Tolerancia: un archivo que ANOTA el mismo valor no es una discrepancia.
"Q7.000 COP" vs "Q7.000 COP/paquete" es el mismo dato con contexto. Solo cuenta
una diferencia de sustancia. Un gate con falsos positivos se termina ignorando,
y entonces deja de ser un gate.

Uso
---
    python Ads/_TOOLS/verificar_producto.py NUSAVA
    python Ads/_TOOLS/verificar_producto.py --todos
    python Ads/_TOOLS/verificar_producto.py TINNIDROP --json

Codigo de salida: 0 si todo reconcilia, 1 si hay al menos una discrepancia.
"""

import argparse
import csv
import io
import json
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, OSError):
    pass

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROD = os.path.join(BASE, "PRODUCTOS")
DIM = os.path.join(PROD, "_DIM_PRODUCTOS.csv")
PORTAFOLIO = os.path.join(PROD, "_PORTAFOLIO.txt")

# Caracteres del encabezado, por codepoint: escribirlos literales hace que
# cualquier edicion posterior via shell los pueda corromper por el locale.
SEP = "·"        # el punto medio que separa los campos
BARRA = "═"      # la doble raya de los delimitadores
FLECHA = "→"
COMILLA_A, COMILLA_B = "«", "»"

# Archivos por rol. Los dos primeros son obligatorios (invariante 8); 3_ solo
# existe si hubo MCP, y 4_/5_ llevan plantilla propia y no encabezado canonico.
OBLIGATORIOS = ["1_HACER_MANUAL.txt", "2_DATA_PRODUCTO.txt"]
OPCIONALES = ["3_CAMPAÑA_META.txt"]

CAMPOS = {
    "VERSION": re.compile(r"^VERSION\s+(\S+)", re.I),
    "COSTO": re.compile(r"^COSTO\s+(.+)$", re.I),
    "DOSIS": re.compile(r"^DOSIS\s+(.+)$", re.I),
    "page_id": re.compile(r"^page_id\s+(.+)$", re.I),
    "campaign_id": re.compile(r"^campaign_id\s+(.+)$", re.I),
}
RE_FECHA = re.compile(r"^(?:FECHA\s+)?(\d{4}-\d{2}-\d{2})$", re.I)
RE_NUM = re.compile(r"\d[\d.,]*")
RE_CAMPO_CONOCIDO = re.compile(r"(VERSION|COSTO|DOSIS|page_id|campaign_id)", re.I)
COMPARACION_ESTRICTA = ("VERSION", "FECHA")


def norm(s):
    return re.sub(r"\s+", " ", (s or "").strip())


def primer_numero(s):
    """El primer numero del campo. 'Q45/u (Q90 el par)' -> 45.0 · 'PENDIENTE' -> None."""
    m = RE_NUM.search(s or "")
    if not m:
        return None
    try:
        return float(m.group(0).replace(",", ""))
    except ValueError:
        return None


def equivalentes(campo, a, b):
    """Dos valores del mismo campo, dicen lo mismo?"""
    na, nb = norm(a).lower(), norm(b).lower()
    if na == nb:
        return True
    if na and nb and (na in nb or nb in na):    # uno extiende al otro
        return True
    if campo in COMPARACION_ESTRICTA:           # aca el string ES el dato
        return False
    ca, cb = primer_numero(a), primer_numero(b)
    if ca is not None and cb is not None:
        return abs(ca - cb) < 0.01
    return False


def parsear_encabezado(ruta):
    """Campos de la primera linea. None si no es un encabezado reconocible.

    Los delimitadores de doble raya son la convencion, pero varios paquetes
    (CLEARSTEM, VITAMINA D3+K2) los omiten y traen igual todos los campos. Se
    acepta la linea si es reconocible; la falta de delimitadores se reporta como
    aviso, que es otra cosa que una discrepancia de reconciliacion.
    """
    try:
        with io.open(ruta, encoding="utf-8", errors="replace") as fh:
            linea = fh.readline()
    except OSError:
        return None
    cuerpo = linea.strip().strip(BARRA).strip()
    if not cuerpo or SEP not in cuerpo or not RE_CAMPO_CONOCIDO.search(cuerpo):
        return None
    campos = {"_nombre": None, "FECHA": None}
    for i, parte in enumerate(p.strip() for p in cuerpo.split(SEP)):
        if i == 0:
            campos["_nombre"] = parte
            continue
        mf = RE_FECHA.match(parte)
        if mf:
            campos["FECHA"] = mf.group(1)
            continue
        for clave, rx in CAMPOS.items():
            m = rx.match(parte)
            if m:
                campos[clave] = norm(m.group(1))
                break
    return campos


def tiene_delimitadores(ruta):
    try:
        return BARRA * 3 in io.open(ruta, encoding="utf-8", errors="replace").readline()
    except OSError:
        return True


def cargar_dim():
    if not os.path.exists(DIM):
        sys.exit("ERROR: no existe %s. Sin el no se puede resolver la carpeta." % DIM)
    with io.open(DIM, encoding="utf-8") as fh:
        return {r["producto_key"]: r for r in csv.DictReader(fh) if r.get("producto_key")}


def verificar(key, dim):
    """Devuelve (discrepancias, avisos, detalle)."""
    disc, avisos = [], []
    fila = dim.get(key)
    if not fila:
        return (["'%s' no tiene fila en _DIM_PRODUCTOS.csv, el sistema no puede resolver "
                 "su carpeta (invariante 10). Claves validas: %s"
                 % (key, ", ".join(sorted(dim)))], [], {})

    slug = (fila.get("slug_carpeta") or "").strip()
    carpeta = os.path.join(PROD, slug)
    if not os.path.isdir(carpeta):
        return (["la carpeta PRODUCTOS/%s/ no existe en disco" % slug], [], {})

    heads = {}
    for nombre in OBLIGATORIOS:
        ruta = os.path.join(carpeta, nombre)
        if not os.path.exists(ruta):
            disc.append("falta %s (obligatorio, invariante 8)" % nombre)
            continue
        h = parsear_encabezado(ruta)
        if h is None:
            disc.append("%s no tiene encabezado con campos en la primera linea" % nombre)
        else:
            heads[nombre] = h
            if not tiene_delimitadores(ruta):
                avisos.append("%s no usa los delimitadores de la convencion" % nombre)
    for nombre in OPCIONALES:
        ruta = os.path.join(carpeta, nombre)
        if os.path.exists(ruta):
            h = parsear_encabezado(ruta)
            if h is None:
                avisos.append("%s existe pero no tiene encabezado reconocible" % nombre)
            else:
                heads[nombre] = h

    # Coherencia entre archivos del paquete
    for campo in ["VERSION", "FECHA", "COSTO", "DOSIS", "page_id", "campaign_id"]:
        vistos = sorted((n, h[campo]) for n, h in heads.items() if h.get(campo))
        choca = any(not equivalentes(campo, a[1], b[1])
                    for i, a in enumerate(vistos) for b in vistos[i + 1:])
        if choca:
            detalle = " | ".join("%s: %s%s%s" % (n, COMILLA_A, v, COMILLA_B)
                                 for n, v in vistos)
            disc.append("%s no coincide entre archivos %s %s" % (campo, FLECHA, detalle))

    # Coherencia contra la fuente estructurada
    costo_dim = primer_numero(fila.get("costo_q"))
    page_dim = norm(fila.get("page_id"))
    for nombre, h in sorted(heads.items()):
        c = primer_numero(h.get("COSTO"))
        if costo_dim is not None and c is not None and abs(c - costo_dim) > 0.01:
            disc.append("COSTO de %s (%s%s%s = %g) no coincide con costo_q de "
                        "_DIM_PRODUCTOS.csv (%g)"
                        % (nombre, COMILLA_A, h["COSTO"], COMILLA_B, c, costo_dim))
        p = h.get("page_id") or ""
        if p and "PENDIENTE" in p.upper():
            avisos.append("%s tiene page_id PENDIENTE, no se puede pautar asi" % nombre)
        elif page_dim and p and page_dim not in p:
            disc.append("page_id de %s (%s%s%s) no coincide con page_id de "
                        "_DIM_PRODUCTOS.csv (%s)"
                        % (nombre, COMILLA_A, p, COMILLA_B, page_dim))

    # Registro maestro (invariante 8). Desde 2026-09-02 la auditoria diaria recorre
    # _DIM_PRODUCTOS.csv, no _PORTAFOLIO.txt: tener fila aqui ya es condicion de
    # existir para el sistema, asi que lo que se comprueba es que este completa.
    estado = (fila.get("estado") or "").strip()
    if not estado:
        disc.append("la fila de _DIM_PRODUCTOS.csv no declara 'estado', la auditoria "
                    "diaria no sabe si auditarlo (invariante 8)")
    # La fase solo se exige a los VIVOS: un producto LISTO todavia no lanzado no
    # tiene fase de testeo/definicion/escalado, y exigirsela era un falso positivo.
    elif estado.upper() == "VIVO" and not (fila.get("fase") or "").strip().strip("-"):
        disc.append("esta en estado VIVO pero su fila no declara 'fase' "
                    "(TESTEO / DEFINICION / ESCALADO): la auditoria diaria no sabe "
                    "que umbrales aplicarle")

    return disc, avisos, {"producto_key": key, "carpeta": "PRODUCTOS/" + slug,
                          "archivos": sorted(heads), "encabezados": heads}


def main():
    ap = argparse.ArgumentParser(description="Gate de reconciliacion por producto")
    ap.add_argument("producto", nargs="?", help="producto_key de _DIM_PRODUCTOS.csv")
    ap.add_argument("--todos", action="store_true", help="verificar todo el portafolio")
    ap.add_argument("--json", action="store_true", help="salida JSON")
    args = ap.parse_args()

    dim = cargar_dim()
    if args.todos:
        claves = sorted(dim)
    elif args.producto:
        claves = [args.producto.strip()]
    else:
        ap.error("indica un producto_key o usa --todos")

    resultados, fallidos = [], 0
    for k in claves:
        disc, avisos, det = verificar(k, dim)
        if disc:
            fallidos += 1
        resultados.append({"producto": k, "pasa": not disc, "discrepancias": disc,
                           "avisos": avisos, "detalle": det})

    if args.json:
        print(json.dumps(resultados, ensure_ascii=False, indent=2))
    else:
        for r in resultados:
            print("\n%s  %s  %s  (%s)" % ("PASA" if r["pasa"] else "FALLA", SEP,
                                          r["producto"], r["detalle"].get("carpeta", "?")))
            for d in r["discrepancias"]:
                print("    [x] " + d)
            for a in r["avisos"]:
                print("    [!] " + a)
            if r["pasa"] and not r["avisos"]:
                print("    todo reconcilia")
        total = len(resultados)
        print("\n" + "-" * 66)
        print("%d/%d pasan el gate. %s" % (
            total - fallidos, total,
            "Ningun producto puede declararse completo con discrepancias."
            if fallidos else "Sin discrepancias."))

    return 1 if fallidos else 0


if __name__ == "__main__":
    sys.exit(main())
