# -*- coding: utf-8 -*-
"""csv_hechos.py — lectura y escritura de los CSV de hechos de finanzas (`_FACT_ORDENES_DROPI.csv`,
`_FACT_BANCO.csv`) con un escritor CSV real (invariante 11): UTF-8 sin BOM, CRLF, comillas solo
donde hacen falta. Escribe a un temporal y reemplaza, así una corrida cortada nunca deja un
archivo a medias."""
import csv
import io
import os


def leer(ruta):
    if not ruta or not os.path.exists(ruta):
        return []
    with io.open(ruta, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def escribir(ruta, columnas, filas):
    os.makedirs(os.path.dirname(os.path.abspath(ruta)), exist_ok=True)
    tmp = ruta + ".tmp"
    with io.open(tmp, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=columnas, lineterminator="\r\n", extrasaction="ignore")
        w.writeheader()
        for r in filas:
            w.writerow({c: r.get(c, "") for c in columnas})
    os.replace(tmp, ruta)


def monto(valor):
    """Texto de un monto con 2 decimales (`239.0` -> `239.00`); vacío si no hay número."""
    try:
        v = float(valor)
    except (TypeError, ValueError):
        return ""
    return "" if v != v else "%.2f" % v
