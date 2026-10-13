# -*- coding: utf-8 -*-
"""ingerir_dropi.py — persiste el export de órdenes de Dropi en `PRODUCTOS/_FACT_ORDENES_DROPI.csv`.

  python Ads/_TOOLS/ingerir_dropi.py --archivo <ordenes.xlsx> [--mercado GT] [--escribir] [--json]

Sin `--escribir` solo MIRA: cuenta cuántas órdenes entrarían (nuevas / actualizadas) y no toca
disco (DOCTRINA/DATA_PLAYBOOK.md §7). Con `--json` el stdout es SOLO el resumen en JSON (para el
runner de la app).

El export de Dropi es una ventana móvil, no el historial: por eso cada ingesta hace UPSERT por ID
de orden. Una fila ya guardada se reemplaza solo si el export nuevo es del mismo día de reporte o
posterior (estatus y montos cambian mientras la orden avanza); un export más viejo no pisa a uno
más nuevo. Las órdenes que el export nuevo ya no trae se conservan. Re-ingerir el mismo archivo no
cambia nada.

Una fila por orden, en quetzales tal cual los trae Dropi (DOCTRINA/CONTABILIDAD.md §3-bis). El
producto se clasifica con `gen_pl.pk_dropi` (la misma regla del estado de resultados) y el mercado
sale de `_DIM_PRODUCTOS.csv`; un producto que Dropi trae pero el sistema no conoce queda `OTRO` en
el mercado de `--mercado` (GT: Dropi GT es la única fuente hoy).

La fecha de reporte sale de la columna FECHA DE REPORTE; si el export no la trae, de la fecha en el
nombre del archivo (`ordenes_productos_YYYYMMDD_HHMMSS.xlsx`), y como último recurso de la fecha de
modificación del archivo.
"""
import argparse
import datetime
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import csv_hechos  # noqa: E402
import gen_pl      # noqa: E402
import mercado     # noqa: E402

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

DESTINO = os.path.join(gen_pl.P, "_FACT_ORDENES_DROPI.csv")

COLUMNAS = ["orden_id", "fecha_orden", "fecha_movimiento", "estatus", "producto", "producto_key",
            "mercado", "cantidad", "total_q", "flete_q", "costo_proveedor_q", "ganancia_q",
            "fecha_reporte", "archivo_origen"]

REQUERIDAS = ["ID", "FECHA", "ESTATUS", "PRODUCTO", "TOTAL DE LA ORDEN", "PRECIO FLETE",
              "PRECIO PROVEEDOR X CANTIDAD", "GANANCIA", "FECHA DE ÚLTIMO MOVIMIENTO"]


class ExportInvalido(Exception):
    """El archivo no tiene el formato del export de órdenes de Dropi."""


def _fecha(ts):
    return "" if ts is None or ts != ts else ts.date().isoformat()


def fecha_de_reporte(df, archivo):
    """Día del reporte (ISO): columna FECHA DE REPORTE > nombre del archivo > mtime."""
    import pandas as pd
    if "FECHA DE REPORTE" in df.columns:
        f = pd.to_datetime(df["FECHA DE REPORTE"], format="%d-%m-%Y", errors="coerce").dropna()
        if len(f):
            return f.max().date().isoformat()
    m = re.search(r"(\d{4})(\d{2})(\d{2})_\d{6}", os.path.basename(archivo))
    if m:
        return "%s-%s-%s" % m.groups()
    return datetime.date.fromtimestamp(os.path.getmtime(archivo)).isoformat()


def producto_y_mercado(nombre, mercado_defecto):
    pk = gen_pl.pk_dropi(nombre)
    fila = gen_pl._prods.get(pk)
    if fila is None:
        return pk, mercado_defecto
    return pk, mercado.mercado_de_fila(fila, gen_pl.ROOT)


def filas_del_export(archivo, mercado_defecto="GT"):
    """(filas, fecha_reporte): una fila por ID de orden (si el export la repite, gana la última)."""
    try:
        df = gen_pl.leer_dropi(archivo)
    except KeyError as e:
        raise ExportInvalido("el archivo no parece un export de órdenes de Dropi (falta %s)." % e)
    faltan = [c for c in REQUERIDAS if c not in df.columns]
    if faltan:
        raise ExportInvalido("el archivo no parece un export de órdenes de Dropi: faltan las "
                             "columnas %s." % ", ".join(faltan))
    reporte = fecha_de_reporte(df, archivo)
    por_id = {}
    for _, r in df.iterrows():
        if r["ID"] != r["ID"]:
            continue
        pk, merc = producto_y_mercado(r["PRODUCTO"], mercado_defecto)
        cantidad = r["CANTIDAD"] if "CANTIDAD" in df.columns else None
        por_id[str(int(r["ID"]))] = {
            "orden_id": str(int(r["ID"])),
            "fecha_orden": _fecha(r["f_orden"]),
            "fecha_movimiento": _fecha(r["f_mov"]),
            "estatus": str(r["ESTATUS"]),
            "producto": str(r["PRODUCTO"]),
            "producto_key": pk,
            "mercado": merc,
            "cantidad": "" if cantidad is None or cantidad != cantidad else str(int(cantidad)),
            "total_q": csv_hechos.monto(r["TOTAL DE LA ORDEN"]),
            "flete_q": csv_hechos.monto(r["PRECIO FLETE"]),
            "costo_proveedor_q": csv_hechos.monto(r["PRECIO PROVEEDOR X CANTIDAD"]),
            "ganancia_q": csv_hechos.monto(r["GANANCIA"]),
            "fecha_reporte": reporte,
            "archivo_origen": os.path.basename(archivo),
        }
    return list(por_id.values()), reporte


def fusionar(existentes, nuevas):
    """UPSERT por orden_id. Devuelve (filas, resumen)."""
    por_id = {r["orden_id"]: r for r in existentes}
    res = {"nuevas": 0, "actualizadas": 0, "sin_cambio": 0, "omitidas_por_viejas": 0}
    for n in nuevas:
        previa = por_id.get(n["orden_id"])
        if previa is None:
            por_id[n["orden_id"]] = n
            res["nuevas"] += 1
        elif (n["fecha_reporte"] or "") < (previa.get("fecha_reporte") or ""):
            res["omitidas_por_viejas"] += 1
        elif all((previa.get(c) or "") == (n.get(c) or "") for c in COLUMNAS):
            res["sin_cambio"] += 1
        else:
            por_id[n["orden_id"]] = n
            res["actualizadas"] += 1
    filas = sorted(por_id.values(), key=lambda r: (r["fecha_orden"], int(r["orden_id"])))
    return filas, res


def ingerir(archivo, destino=DESTINO, escribir=False, mercado_defecto="GT"):
    nuevas, reporte = filas_del_export(archivo, mercado_defecto)
    filas, res = fusionar(csv_hechos.leer(destino), nuevas)
    res.update({"fecha_reporte": reporte, "ordenes_en_el_export": len(nuevas),
                "ordenes_guardadas": len(filas), "escrito": False})
    if escribir:
        csv_hechos.escribir(destino, COLUMNAS, filas)
        res["escrito"] = True
    return res


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--archivo", required=True, help="export de órdenes de Dropi (.xlsx)")
    ap.add_argument("--mercado", default="GT",
                    help="mercado de las órdenes de un producto que el sistema no conoce (GT)")
    ap.add_argument("--escribir", action="store_true", help="persistir (sin esto solo mira)")
    ap.add_argument("--json", action="store_true", help="imprime solo el resumen en JSON")
    a = ap.parse_args(argv)
    try:
        res = ingerir(a.archivo, escribir=a.escribir, mercado_defecto=a.mercado)
    except (ExportInvalido, mercado.MercadoError) as e:
        print("BLOQUEANTE: %s" % e, file=sys.stderr)
        return 1
    if a.json:
        print(json.dumps(res, ensure_ascii=False))
        return 0
    print("Dropi %s · reporte %s · %d órdenes en el export" % (
        os.path.basename(a.archivo), res["fecha_reporte"], res["ordenes_en_el_export"]))
    print("  nuevas %d · actualizadas %d · sin cambio %d · omitidas por export más viejo %d" % (
        res["nuevas"], res["actualizadas"], res["sin_cambio"], res["omitidas_por_viejas"]))
    if res["escrito"]:
        print("escrito: %s (%d órdenes)" % (DESTINO, res["ordenes_guardadas"]))
    else:
        print("(solo mirar: no se escribió nada; --escribir para persistir)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
