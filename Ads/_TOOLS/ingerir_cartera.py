# -*- coding: utf-8 -*-
"""ingerir_cartera.py — persiste el historial de cartera de Dropi en `PRODUCTOS/_FACT_CARTERA_DROPI.csv`.

  python Ads/_TOOLS/ingerir_cartera.py --archivo <historial.xlsx> [--mercado GT] [--escribir] [--json]

Sin `--escribir` solo MIRA: cuenta cuántos movimientos entrarían (nuevos / actualizados) y no toca
disco (DOCTRINA/DATA_PLAYBOOK.md §7). Con `--json` el stdout es SOLO el resumen en JSON (para el
runner de la app).

La cartera de Dropi es el LIBRO DE CAJA de la billetera: una fila por movimiento real de dinero,
con su ID único. Cada ingesta hace UPSERT por ID de movimiento; un movimiento ya guardado solo se
reemplaza si el archivo nuevo lo trae distinto, y los que el archivo nuevo ya no trae se conservan.
Re-ingerir el mismo archivo no cambia nada.

Una fila por movimiento, en quetzales tal cual los trae Dropi. Categorías (las mismas de
`gen_pl.leer_cartera`): GANANCIA_ORDEN, COBRO_DEVOLUCION, RETIRO y OTRO. `saldo_despues_q` sale de
`MONTO PREVIO` ± `MONTO`. El destino de cada RETIRO no se guarda: se deriva al leer con
`_DIM_RETIROS.csv` (`gen_pl.clasificar_retiro`), así corregir una regla corrige todo el historial.
Los retiros que ninguna regla clasifica quedan SIN_CLASIFICAR y se listan en el resumen.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import csv_hechos  # noqa: E402
import gen_pl      # noqa: E402

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

DESTINO = os.path.join(gen_pl.P, "_FACT_CARTERA_DROPI.csv")

COLUMNAS = ["mov_id", "fecha", "hora", "tipo", "monto_q", "saldo_previo_q", "saldo_despues_q",
            "orden_id", "guia", "categoria", "descripcion", "concepto_retiro", "mercado",
            "archivo_origen"]

REQUERIDAS = ["ID", "FECHA", "TIPO", "MONTO", "MONTO PREVIO", "ORDEN ID", "DESCRIPCIÓN",
              "CONCEPTO DE RETIRO"]


class ExportInvalido(Exception):
    """El archivo no tiene el formato del historial de cartera de Dropi."""


def _texto(v):
    return "" if v is None or v != v else str(v).strip()


def _num(v):
    try:
        x = float(v)
    except (TypeError, ValueError):
        return None
    return None if x != x else x


def filas_del_historial(archivo, mercado_defecto="GT"):
    """Una fila por ID de movimiento (si el archivo lo repite, gana la última)."""
    try:
        c = gen_pl.leer_cartera(archivo)
    except KeyError as e:
        raise ExportInvalido("el archivo no parece un historial de cartera de Dropi (falta %s)." % e)
    faltan = [k for k in REQUERIDAS if k not in c.columns]
    if faltan:
        raise ExportInvalido("el archivo no parece un historial de cartera de Dropi: faltan las "
                             "columnas %s." % ", ".join(faltan))
    por_id = {}
    for _, r in c.iterrows():
        if r["ID"] != r["ID"] or r["f"] != r["f"]:
            continue
        monto, previo = _num(r["MONTO"]), _num(r["MONTO PREVIO"])
        entra = str(r["TIPO"]).strip().upper() == "ENTRADA"
        despues = None if monto is None or previo is None else previo + (monto if entra else -monto)
        orden = _num(r["ORDEN ID"])
        por_id[str(int(r["ID"]))] = {
            "mov_id": str(int(r["ID"])),
            "fecha": r["f"].date().isoformat(),
            "hora": r["f"].strftime("%H:%M"),
            "tipo": str(r["TIPO"]).strip().upper(),
            "monto_q": csv_hechos.monto(monto),
            "saldo_previo_q": csv_hechos.monto(previo),
            "saldo_despues_q": csv_hechos.monto(despues),
            "orden_id": "" if orden is None else str(int(orden)),
            "guia": _texto(r["NUMERO DE GUIA"]) if "NUMERO DE GUIA" in c.columns else "",
            "categoria": r["cat"],
            "descripcion": _texto(r["DESCRIPCIÓN"]),
            "concepto_retiro": _texto(r["CONCEPTO DE RETIRO"]),
            "mercado": mercado_defecto,
            "archivo_origen": os.path.basename(archivo),
        }
    return list(por_id.values())


def fusionar(existentes, nuevas):
    """UPSERT por mov_id. Devuelve (filas, resumen)."""
    por_id = {r["mov_id"]: r for r in existentes}
    res = {"nuevas": 0, "actualizadas": 0, "sin_cambio": 0}
    cmp_cols = [c for c in COLUMNAS if c != "archivo_origen"]
    for n in nuevas:
        previa = por_id.get(n["mov_id"])
        if previa is None:
            por_id[n["mov_id"]] = n
            res["nuevas"] += 1
        elif all((previa.get(c) or "") == (n.get(c) or "") for c in cmp_cols):
            res["sin_cambio"] += 1
        else:
            por_id[n["mov_id"]] = n
            res["actualizadas"] += 1
    filas = sorted(por_id.values(), key=lambda r: int(r["mov_id"]))
    return filas, res


def retiros_sin_clasificar(filas, reglas):
    """Los retiros que ninguna regla de `_DIM_RETIROS.csv` clasifica (se listan, no se adivinan)."""
    return [{"mov_id": f["mov_id"], "fecha": f["fecha"], "monto_q": f["monto_q"],
             "concepto_retiro": f["concepto_retiro"]}
            for f in filas if f["categoria"] == "RETIRO"
            and gen_pl.clasificar_retiro(f["concepto_retiro"], reglas) == "SIN_CLASIFICAR"]


def ingerir(archivo, destino=DESTINO, escribir=False, mercado_defecto="GT", reglas=None):
    nuevas = filas_del_historial(archivo, mercado_defecto)
    filas, res = fusionar(csv_hechos.leer(destino), nuevas)
    if reglas is None:
        reglas = gen_pl.load("_DIM_RETIROS.csv")
    res.update({"movimientos_en_el_archivo": len(nuevas), "movimientos_guardados": len(filas),
                "desde": min((f["fecha"] for f in filas), default=None),
                "hasta": max((f["fecha"] for f in filas), default=None),
                "retiros_sin_clasificar": retiros_sin_clasificar(filas, reglas), "escrito": False})
    if escribir:
        csv_hechos.escribir(destino, COLUMNAS, filas)
        res["escrito"] = True
    return res


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--archivo", required=True, help="historial de cartera de Dropi (.xlsx)")
    ap.add_argument("--mercado", default="GT", help="mercado de la cartera (GT: Dropi GT es la única hoy)")
    ap.add_argument("--escribir", action="store_true", help="persistir (sin esto solo mira)")
    ap.add_argument("--json", action="store_true", help="imprime solo el resumen en JSON")
    a = ap.parse_args(argv)
    try:
        res = ingerir(a.archivo, escribir=a.escribir, mercado_defecto=a.mercado.upper())
    except ExportInvalido as e:
        print("BLOQUEANTE: %s" % e, file=sys.stderr)
        return 1
    if a.json:
        print(json.dumps(res, ensure_ascii=False))
        return 0
    print("Cartera %s · %d movimientos en el archivo" % (os.path.basename(a.archivo),
                                                          res["movimientos_en_el_archivo"]))
    print("  nuevos %d · actualizados %d · sin cambio %d" % (res["nuevas"], res["actualizadas"],
                                                            res["sin_cambio"]))
    for r in res["retiros_sin_clasificar"]:
        print("  ⚠ retiro SIN CLASIFICAR: %s Q%s «%s» (agregá su regla a _DIM_RETIROS.csv)" % (
            r["fecha"], r["monto_q"], r["concepto_retiro"]))
    if res["escrito"]:
        print("escrito: %s (%d movimientos, %s a %s)" % (DESTINO, res["movimientos_guardados"],
                                                          res["desde"], res["hasta"]))
    else:
        print("(solo mirar: no se escribió nada; --escribir para persistir)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
