#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""referencia_f1.py — dueño único de PRODUCTOS/_DIM_REFERENCIA_F1.csv (A3, 28-sep-2026).

POR QUE EXISTE. Decisión del operador (2026-09-28): FASE 1 usa el concepto fijo
C2_BENEFICIOS variante `ligera` (DOCTRINA/CALENDARIO_ESCALADO.md:144,
Ads/_SWIPE/_CATALOGO_CONCEPTOS.md §2) para las 6 fichas de ángulo. Hay 3 imágenes de
referencia `ligera` en el banco; para CADA producto la IA elige UNA sola y esa elección
queda fija como dato de producto — la misma referencia se usa en las 6 fichas de ángulo,
nunca una por ángulo. Sin un dueño único, esa elección viviría suelta en prosa de sesión
y se podría re-elegir distinto cada vez que alguien arma el paquete de F1 (invariante 11:
un dato, un dueño; CSV escrito con un escritor real, nunca a mano).

ESQUEMA — PRODUCTOS/_DIM_REFERENCIA_F1.csv (columnas exactas, en este orden):
    producto_key  — debe existir en _DIM_PRODUCTOS.csv (se valida acá, a diferencia de
                    _VOZ_CLIENTE.csv: acá el universo de valores válidos es chico y barato
                    de verificar)
    referencia    — nombre de archivo exacto bajo
                    Ads/_SWIPE/_BANCO_CREATIVOS/C2_BENEFICIOS/, con prefijo `ligera__` y que
                    EXISTE en disco al momento de elegir (no se guarda un archivo fantasma)
    motivo        — por qué esa referencia calza con el avatar/dolor del producto (texto
                    libre, nunca vacío — la elección sin motivo no es auditable)
    elegido_el    — fecha ISO de la elección (la escribe este módulo, nunca a mano)

Una sola fila por producto_key: una elección nueva REEMPLAZA la anterior (upsert por
`producto_key`, vía upsert_fact.upsert — el mismo mecanismo de escritura que
verificar_voz.py usa para _VOZ_CLIENTE.csv).

REGISTRO EN LA CAPA POSTGRES (P3, db/tables.py): este archivo NO tiene fila en
`db/tables.TABLE_SPECS` a propósito. Agregar una sin aplicar el `schema.sql` regenerado
contra el Postgres real rompería `db/cargar.py` (hace `TRUNCATE TABLE raw.<tabla>`
incondicionalmente para toda fila de TABLE_SPECS, exista o no la tabla) — ver
odd/tasks/referencias-y-prompts-fases.md, A3, para el detalle de por qué se dejó afuera
deliberadamente en vez de adivinar. El archivo funciona standalone: el hook de CSV
(`Ads/_TOOLS/hook_csv.py`) valida su estructura como a cualquier otro CSV de PRODUCTOS/, y
el guardia de drift de `ciclo_diario.py` solo vigila `TABLAS_MIGRADAS_DB` (6 tablas), no la
lista completa de TABLE_SPECS — ninguno de los dos exige que este archivo esté registrado.

CLI (contrato T6 de este repo: leer es el default, escribir es explícito)
    python Ads/_TOOLS/referencia_f1.py --listar
        # imprime las 3 referencias `ligera` permitidas (las que existen en disco). Solo lee.
    python Ads/_TOOLS/referencia_f1.py --ver CLEARSTEM
        # imprime la fila elegida para ese producto, o que no hay ninguna. Solo lee.
    python Ads/_TOOLS/referencia_f1.py --elegir CLEARSTEM \
        ligera__Camila-Recomienda__15_1364693855873597.jpg --motivo "avatar mujer 25-40..."
        # escribe/reemplaza la fila de ese producto. Único comando que toca el CSV.
"""

import argparse
import csv
import datetime
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import upsert_fact  # noqa: E402

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CSV_PATH = os.path.join(BASE, "PRODUCTOS", "_DIM_REFERENCIA_F1.csv")
DIM_PRODUCTOS_PATH = os.path.join(BASE, "PRODUCTOS", "_DIM_PRODUCTOS.csv")
BANCO_DIR = os.path.join(BASE, "Ads", "_SWIPE", "_BANCO_CREATIVOS", "C2_BENEFICIOS")

COLS = ["producto_key", "referencia", "motivo", "elegido_el"]
PREFIJO = "ligera__"


class Rechazo(Exception):
    """El pedido no se puede cumplir tal como vino; el mensaje ya es explicable al operador."""


# ─────────────────────────────────────────────────────────────────────────────
# LECTURA
# ─────────────────────────────────────────────────────────────────────────────

def referencias_permitidas(banco_dir=None):
    """Las referencias `ligera` que de verdad existen en disco, ordenadas — nunca una lista
    fija en código: si el banco cambia, este módulo se entera solo."""
    ruta = banco_dir or BANCO_DIR
    if not os.path.isdir(ruta):
        return []
    return sorted(
        n for n in os.listdir(ruta)
        if n.startswith(PREFIJO) and n.lower().endswith((".jpg", ".jpeg", ".png"))
    )


def leer_csv(path=None):
    ruta = path or CSV_PATH
    if not os.path.exists(ruta):
        return []
    with io.open(ruta, encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def fila_de(producto_key, path=None):
    """La fila elegida para ese producto_key, o None si todavía no eligió ninguna."""
    for f in leer_csv(path):
        if (f.get("producto_key") or "").strip() == producto_key:
            return f
    return None


def _producto_existe(producto_key, dim_productos_path=None):
    ruta = dim_productos_path or DIM_PRODUCTOS_PATH
    if not os.path.exists(ruta):
        return False
    with io.open(ruta, encoding="utf-8-sig", newline="") as fh:
        for f in csv.DictReader(fh):
            if (f.get("producto_key") or "").strip() == producto_key:
                return True
    return False


# ─────────────────────────────────────────────────────────────────────────────
# ESCRITURA (upsert por producto_key — invariante 11, un solo escritor)
# ─────────────────────────────────────────────────────────────────────────────

def elegir(producto_key, referencia, motivo, path=None, dim_productos_path=None,
           banco_dir=None, bkdir=None, hoy=None):
    """Valida y escribe/reemplaza la fila del producto. Devuelve la fila escrita.
    Nunca escribe nada si la validación falla (levanta Rechazo)."""
    producto_key = (producto_key or "").strip()
    referencia = (referencia or "").strip()
    motivo = (motivo or "").strip()

    if not producto_key:
        raise Rechazo("producto_key vacío.")
    if not _producto_existe(producto_key, dim_productos_path):
        raise Rechazo(
            f"«{producto_key}» no tiene fila en _DIM_PRODUCTOS.csv — ese es el dueño de qué "
            "productos existen; primero corre alta_producto.py.")

    permitidas = referencias_permitidas(banco_dir)
    if referencia not in permitidas:
        raise Rechazo(
            f"«{referencia}» no es una de las referencias `ligera` que hoy existen en "
            f"{os.path.relpath(banco_dir or BANCO_DIR, BASE)}: {', '.join(permitidas) or '(ninguna encontrada)'}."
        )
    if not motivo:
        raise Rechazo("motivo vacío — la elección sin motivo no es auditable.")

    ruta = path or CSV_PATH
    bk = bkdir or upsert_fact.respaldos_dir(BASE, "backups_csv")
    fecha = hoy or datetime.date.today().isoformat()
    fila = {
        "producto_key": producto_key,
        "referencia": referencia,
        "motivo": motivo,
        "elegido_el": fecha,
    }
    upsert_fact.upsert(ruta, COLS, ("producto_key",), [fila], bk)
    return fila


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Referencia fija `ligera` de C2_BENEFICIOS para las 6 fichas de FASE 1 de un producto.")
    ap.add_argument("--listar", action="store_true",
                     help="imprime las referencias ligera permitidas (solo lectura)")
    ap.add_argument("--ver", metavar="PRODUCTO", help="imprime la fila elegida de ese producto (solo lectura)")
    ap.add_argument("--elegir", nargs=2, metavar=("PRODUCTO", "REFERENCIA"),
                     help="escribe/reemplaza la elección de ese producto (único flag que escribe)")
    ap.add_argument("--motivo", help="por qué esa referencia calza (requerido con --elegir)")
    args = ap.parse_args(argv)

    if args.elegir:
        producto_key, referencia = args.elegir
        try:
            fila = elegir(producto_key, referencia, args.motivo or "")
        except Rechazo as e:
            print(f"RECHAZADO: {e}")
            return 1
        print(f"ELEGIDO: {fila['producto_key']} -> {fila['referencia']} ({fila['elegido_el']})")
        print(f"  motivo: {fila['motivo']}")
        return 0

    if args.ver:
        fila = fila_de(args.ver)
        if not fila:
            print(f"{args.ver}: sin referencia elegida todavía. Siguiente paso:")
            print(f"  python Ads/_TOOLS/referencia_f1.py --listar")
            print(f"  python Ads/_TOOLS/referencia_f1.py --elegir {args.ver} <REFERENCIA> --motivo \"...\"")
            return 0
        print(f"{fila['producto_key']} -> {fila['referencia']}  (elegido {fila['elegido_el']})")
        print(f"  motivo: {fila['motivo']}")
        return 0

    # default / --listar: solo lectura, nunca toca el CSV.
    permitidas = referencias_permitidas()
    if not permitidas:
        print(f"(sin referencias ligera en {os.path.relpath(BANCO_DIR, BASE)})")
        return 1
    print("Referencias ligera permitidas (C2_BENEFICIOS):")
    for n in permitidas:
        print(f"  {n}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
