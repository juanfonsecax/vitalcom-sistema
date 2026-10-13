# -*- coding: utf-8 -*-
"""tasa_fx.py — la tasa efectiva con la que el operador convierte quetzales a dólares.

Cada fila de `PRODUCTOS/_FACT_TRANSFERENCIAS_FX.csv` es un par medido: los quetzales que salieron de
la billetera de Dropi (`monto_q`) y los dólares que llegaron al banco (`monto_usd`). La tasa de la
fila NO se guarda: se deriva al leer (`tasa_de` = monto_q / monto_usd), así no puede contradecir a
las dos cifras que la producen.

La tasa de un mes (`tasa_del_mes`, regla en DOCTRINA/CONTABILIDAD.md):
  VENTANA          promedio ponderado por USD de las transferencias que salieron en los
                   `ventana_dias` que terminan el último día del mes;
  ULTIMA_CONOCIDA  si la ventana no tiene ninguna, la última que salió antes de ese día;
  PARAMETRO        si no existe ninguna, `tasa_usd_gtq` de `_PARAMETROS_FINANZAS.csv`.
Una transferencia posterior al cierre del mes nunca cuenta para ese mes.
"""
import datetime
import os

import csv_hechos

RUTA = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                    "PRODUCTOS", "_FACT_TRANSFERENCIAS_FX.csv")

COLUMNAS = ["fecha_salida", "monto_q", "fecha_llegada", "monto_usd", "banco_destino",
            "origen_salida", "origen_llegada", "confirmado_por"]


def leer(ruta=None):
    return csv_hechos.leer(ruta or RUTA)


def _num(v):
    try:
        x = float(v)
    except (TypeError, ValueError):
        return None
    return x if x == x else None


def tasa_de(fila):
    """Quetzales por dólar de un par, o None si le falta una de las dos cifras."""
    q, usd = _num(fila.get("monto_q")), _num(fila.get("monto_usd"))
    return q / usd if q and usd and q > 0 and usd > 0 else None


def tasa_del_mes(fin, transferencias, tasa_parametro, ventana_dias):
    """Tasa USD -> Q que le toca al mes que termina el `fin` (YYYY-MM-DD). Devuelve un dict con
    `valor`, `regla`, `transferencias` (cuántas pesan), `usd`, `q`, `desde` y `hasta` (fechas de
    salida de las que pesan)."""
    validas = sorted((t for t in transferencias if tasa_de(t) and t.get("fecha_salida")),
                     key=lambda t: t["fecha_salida"])
    hasta_fin = [t for t in validas if t["fecha_salida"] <= fin]
    inicio = (datetime.date.fromisoformat(fin) - datetime.timedelta(days=ventana_dias - 1)).isoformat()
    en_ventana = [t for t in hasta_fin if t["fecha_salida"] >= inicio]
    if en_ventana:
        pesan, regla = en_ventana, "VENTANA"
    elif hasta_fin:
        pesan, regla = [hasta_fin[-1]], "ULTIMA_CONOCIDA"
    else:
        return {"valor": tasa_parametro, "regla": "PARAMETRO", "transferencias": 0, "usd": 0.0,
                "q": 0.0, "desde": None, "hasta": None}
    usd = sum(_num(t["monto_usd"]) for t in pesan)
    q = sum(_num(t["monto_q"]) for t in pesan)
    return {"valor": q / usd, "regla": regla, "transferencias": len(pesan), "usd": usd, "q": q,
            "desde": pesan[0]["fecha_salida"], "hasta": pesan[-1]["fecha_salida"]}
