# -*- coding: utf-8 -*-
"""ingerir_banco.py — persiste los movimientos de un extracto bancario en `PRODUCTOS/_FACT_BANCO.csv`.

  python Ads/_TOOLS/ingerir_banco.py --archivo <extracto.pdf> --banco RELAY --cuenta 8889 [--escribir]

`--cuenta` son los últimos 4 dígitos (el PDF de Relay los imprime como `Account Number: XXXXXX-8889`).
Sin `--escribir` solo MIRA y no toca disco (DOCTRINA/DATA_PLAYBOOK.md §7).

Guarda las salidas Y los depósitos (`tipo` SALIDA/ENTRADA): un depósito no es gasto, pero sin él el
saldo de la cuenta no se puede reconstruir. Los montos van en la moneda de la cuenta (Relay: USD),
siempre positivos; `saldo` es la columna Balance del extracto. `tarjeta` queda vacía mientras el
banco no la imprima (Relay no la imprime).

Antes de escribir se valida el extracto contra su propio resumen (DOCTRINA/CONTABILIDAD.md §6,
regla 2): las salidas suman el Withdrawals, los depósitos suman el Deposits y Opening + Deposits −
Withdrawals da el Closing. Si no cuadra, o si el PDF es de otra cuenta que la declarada, se rechaza
sin escribir nada.

Dedupe: la llave es (banco, cuenta, fecha, nombre, monto, saldo). Dos cargos idénticos el mismo día
se distinguen por el saldo corrido, y re-ingerir un extracto no cambia nada. Los extractos de Relay
traen movimientos de los primeros días del mes siguiente (el de agosto trae el 1-sep): se ingieren
tal cual vienen, y los reportes cortan por la fecha del movimiento.
"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import csv_hechos  # noqa: E402
import gen_pl      # noqa: E402

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

DESTINO = os.path.join(gen_pl.P, "_FACT_BANCO.csv")

COLUMNAS = ["fecha", "banco", "cuenta", "nombre", "monto", "tipo", "saldo", "tarjeta", "archivo"]

TOLERANCIA = 0.02


class ExtractoInvalido(Exception):
    """El extracto no cuadra con su resumen, es de otra cuenta o no se puede leer."""


def texto_del_pdf(ruta):
    import pdfplumber
    txt = ""
    with pdfplumber.open(ruta) as pdf:
        for pg in pdf.pages:
            txt += (pg.extract_text() or "") + "\n"
    return txt


def cuenta_del_extracto(txt):
    """Últimos 4 dígitos de `Account Number: XXXXXX-8889`, o None si el texto no la trae."""
    m = re.search(r"Account Number:\s*[X*]*-?(\d{4})\b", txt)
    return m.group(1) if m else None


def llave(f):
    return (f["banco"], f["cuenta"], f["fecha"], f["nombre"], f["monto"], f["saldo"])


def validar(mov, resumen, cuenta, cuenta_pdf):
    if cuenta_pdf is not None and cuenta_pdf != cuenta:
        raise ExtractoInvalido("el extracto es de la cuenta %s y se declaró --cuenta %s."
                               % (cuenta_pdf, cuenta))
    if resumen is None:
        raise ExtractoInvalido("no encontré el resumen (Opening/Closing/Deposits/Withdrawals): "
                               "sin él no se puede validar el extracto.")
    salidas = sum(m["monto"] for m in mov if m["tipo"] == "SALIDA")
    entradas = sum(m["monto"] for m in mov if m["tipo"] == "ENTRADA")
    if abs(salidas - resumen["retiros"]) > TOLERANCIA:
        raise ExtractoInvalido("las salidas suman $%.2f y el resumen dice Withdrawals $%.2f."
                               % (salidas, resumen["retiros"]))
    if abs(entradas - resumen["depositos"]) > TOLERANCIA:
        raise ExtractoInvalido("los depósitos suman $%.2f y el resumen dice Deposits $%.2f."
                               % (entradas, resumen["depositos"]))
    cierre = resumen["apertura"] + resumen["depositos"] - resumen["retiros"]
    if abs(cierre - resumen["cierre"]) > TOLERANCIA:
        raise ExtractoInvalido("Opening + Deposits − Withdrawals da $%.2f y el Closing dice $%.2f."
                               % (cierre, resumen["cierre"]))


def ingerir_texto(txt, archivo, banco, cuenta, destino=DESTINO, escribir=False):
    mov, resumen = gen_pl.movimientos_completos_del_extracto(txt)
    validar(mov, resumen, cuenta, cuenta_del_extracto(txt))
    nuevas = [{
        "fecha": m["fecha"].isoformat(), "banco": banco, "cuenta": cuenta, "nombre": m["nombre"],
        "monto": csv_hechos.monto(m["monto"]), "tipo": m["tipo"],
        "saldo": csv_hechos.monto(m["saldo"]), "tarjeta": "", "archivo": os.path.basename(archivo),
    } for m in mov]
    existentes = csv_hechos.leer(destino)
    vistas = {llave(f) for f in existentes}
    agregar, duplicadas = [], 0
    for f in nuevas:
        if llave(f) in vistas:
            duplicadas += 1
            continue
        vistas.add(llave(f))
        agregar.append(f)
    filas = sorted(existentes + agregar, key=lambda f: (f["fecha"], f["banco"], f["cuenta"],
                                                        f["nombre"], f["monto"], f["saldo"]))
    res = {"movimientos_en_el_extracto": len(nuevas), "nuevas": len(agregar),
           "duplicadas": duplicadas,
           "salidas": sum(1 for f in nuevas if f["tipo"] == "SALIDA"),
           "entradas": sum(1 for f in nuevas if f["tipo"] == "ENTRADA"),
           "retiros_usd": resumen["retiros"], "depositos_usd": resumen["depositos"],
           "filas_guardadas": len(filas), "escrito": False}
    if escribir:
        csv_hechos.escribir(destino, COLUMNAS, filas)
        res["escrito"] = True
    return res


def ingerir(archivo, banco, cuenta, destino=DESTINO, escribir=False):
    return ingerir_texto(texto_del_pdf(archivo), archivo, banco, cuenta, destino, escribir)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--archivo", required=True, help="extracto bancario (.pdf)")
    ap.add_argument("--banco", required=True, help="banco del extracto (RELAY)")
    ap.add_argument("--cuenta", required=True, help="últimos 4 dígitos de la cuenta")
    ap.add_argument("--escribir", action="store_true", help="persistir (sin esto solo mira)")
    a = ap.parse_args(argv)
    try:
        res = ingerir(a.archivo, a.banco.upper(), a.cuenta, escribir=a.escribir)
    except ExtractoInvalido as e:
        print("BLOQUEANTE: %s: %s" % (os.path.basename(a.archivo), e), file=sys.stderr)
        return 1
    print("%s · %s ····%s · %d movimientos (%d salidas, %d depósitos) · Withdrawals $%.2f" % (
        os.path.basename(a.archivo), a.banco.upper(), a.cuenta, res["movimientos_en_el_extracto"],
        res["salidas"], res["entradas"], res["retiros_usd"]))
    print("  nuevas %d · ya estaban %d" % (res["nuevas"], res["duplicadas"]))
    if res["escrito"]:
        print("escrito: %s (%d movimientos)" % (DESTINO, res["filas_guardadas"]))
    else:
        print("(solo mirar: no se escribió nada; --escribir para persistir)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
