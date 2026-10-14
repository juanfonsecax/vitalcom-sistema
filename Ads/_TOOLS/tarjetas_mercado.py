# -*- coding: utf-8 -*-
"""tarjetas_mercado.py — la tarjeta (últimos 4) dice a qué BM y mercado va cada cargo de Mercury.

Dueño: `PRODUCTOS/_DIM_TARJETAS_MERCADO.csv` (una tarjeta por BM, confirmada por el
operador). Una tarjeta sin fila nunca se reparte por adivinanza: sale en faltantes.
"""
import os

import csv_hechos

RUTA = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                    "PRODUCTOS", "_DIM_TARJETAS_MERCADO.csv")

COLUMNAS = ["banco", "ultimos4", "bm", "mercado", "uso", "cuentas_publicitarias", "estado",
            "confirmado_por", "fecha", "notas"]

MERCADOS = ("GT", "CO", "COMPARTIDO", "SIN_USO", "")


def cargar(ruta=None):
    return csv_hechos.leer(ruta or RUTA)


def validar(filas):
    """Errores de la dimensión (lista vacía = válida): últimos 4 únicos y no vacíos,
    mercado dentro del vocabulario."""
    errores, vistos = [], set()
    for f in filas or []:
        u4 = (f.get("ultimos4") or "").strip()
        if not u4:
            errores.append("fila sin ultimos4")
            continue
        if u4 in vistos:
            errores.append("ultimos4 repetido: %s" % u4)
        vistos.add(u4)
        if (f.get("mercado") or "") not in MERCADOS:
            errores.append("mercado no declarado en %s: «%s»" % (u4, f.get("mercado") or ""))
    return errores


def mercado_de(ultimos4, filas=None):
    """El mercado de una tarjeta (últimos 4), o "" si no tiene fila o no tiene mercado.
    Una tarjeta sin mercado nunca se reparte por adivinanza."""
    u4 = (ultimos4 or "").strip()
    if not u4:
        return ""
    for f in filas if filas is not None else cargar():
        if (f.get("ultimos4") or "").strip() == u4:
            return (f.get("mercado") or "")
    return ""
