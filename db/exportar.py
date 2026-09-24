#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""exportar.py — Postgres -> CSV, reconstruye los archivos de PRODUCTOS/ (P1-cimientos T6).

Para cada tabla de `core.*` (ver db/tables.py) escribe de vuelta el CSV con el MISMO nombre,
las MISMAS columnas y el MISMO orden que el original — ordenado por `id` (el orden de inserción
de `cargar.py`, que a su vez es el orden de filas del CSV real: la carga nunca reordena).

`venta` es el único caso especial: escribe la columna `ad_id` verbatim (la original, la que
cargó `cargar.py` sin tocar) y OMITE `ad_id_resuelto`/`metodo_atribucion` del CSV de salida —
esas dos son un enriquecimiento de la base de datos, no parte de `_FACT_VENTAS.csv`. Así el
archivo exportado es, columna por columna, el mismo que `decidir.py` (vía gasto.py) sabe leer.

USO:
    "<venv>/python.exe" db/exportar.py --out DIR              # exporta PRODUCTOS/*.csv a DIR
    "<venv>/python.exe" db/exportar.py --out DIR --decisiones-json DIR/_DECISIONES.json
"""
import argparse
import csv
import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tables as T  # noqa: E402
from cargar import cargar_env, conectar  # noqa: E402


def exportar_tabla(cur, tenant_id, tabla, archivo, opcional, out_dir):
    """Reconstruye el CSV original: header con los nombres CSV reales, valores leídos de las
    columnas SQL (que pueden estar renombradas — ver tables.COLUMN_RENAMES)."""
    pares = T.columnas_csv_y_sql(tabla, archivo, opcional)
    out_path = os.path.join(out_dir, archivo)
    if not pares:
        # Tabla opcional sin CSV fuente (hoy: voz_cliente): no se puede reconstruir un header
        # que nunca existió. No se escribe archivo — igual que hoy no existe en PRODUCTOS/.
        return 0

    header_csv = [csv_col for csv_col, _ in pares]
    header_sql = [sql_col for _, sql_col in pares]
    col_list = ", ".join(['"%s"' % c for c in header_sql])
    cur.execute(
        "SELECT %s FROM core.%s WHERE tenant_id = %%s ORDER BY id" % (col_list, tabla),
        (tenant_id,),
    )
    filas = cur.fetchall()

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with io.open(out_path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(header_csv)
        for fila in filas:
            w.writerow(["" if v is None else v for v in fila])
    return len(filas)


def exportar_decision(cur, tenant_id, out_path):
    cur.execute(
        "SELECT payload FROM core.decision WHERE tenant_id = %s ORDER BY id DESC LIMIT 1",
        (tenant_id,),
    )
    r = cur.fetchone()
    if not r:
        return False
    payload = r[0]
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with io.open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return True


def exportar_todo(out_dir, decisiones_json=None, tenant_id="vitalcom", env=None):
    """Exporta todas las tablas espejo a `out_dir` (misma estructura plana que PRODUCTOS/).
    Devuelve {tabla: n_filas}."""
    os.makedirs(out_dir, exist_ok=True)
    conteos = {}
    con = conectar(env)
    try:
        with con.cursor() as cur:
            for tabla, archivo, opcional in T.TABLE_SPECS:
                conteos[tabla] = exportar_tabla(cur, tenant_id, tabla, archivo, opcional, out_dir)
            decisiones_json = decisiones_json or os.path.join(out_dir, "_DECISIONES.json")
            conteos["decision"] = 1 if exportar_decision(cur, tenant_id, decisiones_json) else 0
    finally:
        con.close()
    return conteos


def main():
    ap = argparse.ArgumentParser(description="Exporta core.* de vuelta a CSV (formato PRODUCTOS/)")
    ap.add_argument("--out", required=True, help="directorio de salida")
    ap.add_argument("--decisiones-json", default=None)
    ap.add_argument("--tenant", default="vitalcom")
    args = ap.parse_args()

    conteos = exportar_todo(args.out, args.decisiones_json, args.tenant)
    total = sum(conteos.values())
    for tabla, n in sorted(conteos.items()):
        print("%-32s %6d" % (tabla, n))
    print("-" * 40)
    print("%-32s %6d" % ("TOTAL", total))
    return 0


if __name__ == "__main__":
    sys.exit(main())
