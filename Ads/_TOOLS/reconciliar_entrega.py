#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""reconciliar_entrega.py — aplica la precedencia por fuente a la entrega de Meta YA cargada.

REGLA (dueña: `upsert_fact.superar_por_api_directa`): para una misma cuenta y un mismo día,
`MetaAPI-directo` supera a toda otra fuente. Los escritores (`bajar_meta_insights.py`,
`ingerir_meta.py`) la aplican al guardar; este script la aplica de una vez al histórico que ya
estaba en `_FACT_ENTREGA.csv` / `_FACT_ENTREGA_ANUNCIO.csv` (Postgres es la verdad, el CSV es su
espejo) y reporta qué dejó en pie.

CONTRATO DE CLI: un "mirar" nunca escribe. Sin `--escribir` solo informa lo que eliminaría y el
gasto por cuenta y mes antes/después. Con `--escribir` pasa por `db/escribir.py` (guardia de drift
incluida) y regenera el espejo; nunca toca el CSV directo.

Una ventana multidia cubierta por la API solo en parte NO se elimina (es un agregado, no se puede
partir): se lista como PARCIAL para decidirla a mano.

USO:
    python Ads/_TOOLS/reconciliar_entrega.py            # informa
    python Ads/_TOOLS/reconciliar_entrega.py --escribir # aplica
"""
import argparse
import collections
import csv
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import upsert_fact as uf  # noqa: E402

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROD = os.path.join(BASE, "PRODUCTOS")
TABLAS = (("entrega_conjunto_dia", "_FACT_ENTREGA.csv"),
          ("entrega_anuncio_dia", "_FACT_ENTREGA_ANUNCIO.csv"))
TENANT_ID = "vitalcom"


def _leer(path):
    if not os.path.exists(path):
        return []
    with io.open(path, encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def _num(v):
    try:
        return float(v) if v not in (None, "") else 0.0
    except ValueError:
        return 0.0


def gasto_por_cuenta_mes(filas):
    """{(cuenta_id, 'YYYY-MM'): spend_usd} sumando todas las filas recibidas, por mes de inicio."""
    out = collections.defaultdict(float)
    for f in filas:
        out[((f.get("cuenta_id") or "").strip(), (f.get("ventana_ini") or "")[:7])] += _num(f.get("spend_usd"))
    return dict(out)


def diagnosticar(filas):
    """(conservadas, superadas, parciales, antes, despues) para un hecho de entrega."""
    conservadas, superadas, parciales = uf.superar_por_api_directa(filas)
    return conservadas, superadas, parciales, gasto_por_cuenta_mes(filas), gasto_por_cuenta_mes(conservadas)


def _llave(fila):
    return (fila.get("fuente"), fila.get("ventana_ini"), fila.get("ventana_fin"),
            fila.get("cuenta_id"), fila.get("campana"), fila.get("conjunto"), fila.get("anuncio"),
            fila.get("ad_id"))


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--escribir", action="store_true", help="aplica via Postgres (default: solo informa)")
    a = p.parse_args(argv)

    hay_cambio = False
    for tabla, archivo in TABLAS:
        filas = _leer(os.path.join(PROD, archivo))
        cons, sup, parc, antes, despues = diagnosticar(filas)
        por_fuente = collections.Counter(f.get("fuente") for f in sup)
        print(f"\n{archivo}: {len(filas)} filas · {len(sup)} superadas "
              f"(${sum(_num(f.get('spend_usd')) for f in sup):,.2f}) · {len(parc)} parciales")
        for fuente, n in sorted(por_fuente.items()):
            print(f"  superadas {fuente}: {n}")
        grupos = collections.defaultdict(lambda: [0, 0.0])
        for f in parc:
            g = grupos[(f.get("fuente"), f.get("cuenta_alias"), f.get("ventana_ini"), f.get("ventana_fin"))]
            g[0] += 1
            g[1] += _num(f.get("spend_usd"))
        for (fuente, alias, ini, fin), (n, gasto) in sorted(grupos.items()):
            print(f"  PARCIAL conservada: {fuente} {alias} {ini}..{fin} · {n} filas · ${gasto:,.2f}")
        if archivo == "_FACT_ENTREGA.csv":
            print("  gasto por cuenta y mes (antes -> despues):")
            for k in sorted(antes):
                if abs(antes[k] - despues.get(k, 0.0)) > 0.005:
                    print(f"    {k[0]} {k[1]}  ${antes[k]:,.2f} -> ${despues.get(k, 0.0):,.2f}")
        hay_cambio = hay_cambio or bool(sup)

    if not a.escribir:
        print("\n[solo informe] nada escrito. Usa --escribir para aplicar." if hay_cambio
              else "\nNada que reconciliar.")
        return 0
    if not hay_cambio:
        print("\nNada que reconciliar.")
        return 0

    sys.path.insert(0, os.path.join(BASE, "db"))
    import cargar as db_cargar      # noqa: E402
    import escribir as db_escribir  # noqa: E402
    bkdir = uf.respaldos_dir(BASE, "backups_csv")
    try:
        con = db_cargar.conectar()
    except Exception as exc:
        print(f"\nPostgres no disponible: no se escribe nada ({exc}).", file=sys.stderr)
        return 1
    try:
        for tabla, archivo in TABLAS:
            db_escribir.verificar_csv_sincronizado(con, tabla, PROD, tenant_id=TENANT_ID)
            r = db_escribir.upsert(con, tabla, [], key=_llave, prod_dir=PROD, bkdir=bkdir,
                                   tenant_id=TENANT_ID, reconciliar=uf.superar_por_api_directa)
            print(f"{archivo}: {r[3]} eliminadas (superadas por MetaAPI-directo)")
    except db_escribir.ErrorEscritura as exc:
        print(f"\n{exc}", file=sys.stderr)
        return 1
    finally:
        con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
