# -*- coding: utf-8 -*-
"""ingerir_banco.py — persiste los movimientos de un banco en `PRODUCTOS/_FACT_BANCO.csv`.

  python Ads/_TOOLS/ingerir_banco.py --archivo <extracto.pdf> --banco RELAY [--cuenta 8889]
                                      [--escribir] [--json]
  python Ads/_TOOLS/ingerir_banco.py --archivo <movimientos.csv> --banco MERCURY [--escribir] [--json]

RELAY (`--cuenta` = últimos 4 dígitos del PDF) valida el extracto contra su propio resumen
(DOCTRINA/CONTABILIDAD.md §6, regla 2). MERCURY lee el CSV de transacciones tal cual se descarga
(columnas `Date (UTC)`, `Description`, `Amount`, `Status`, `Source Account`; opcionales `Bank
Description`, `Last Four Digits`, `Original Currency`): solo entran los `Sent` (los `Pending` y
`Failed` se cuentan y se reportan, no entran). Guarda las salidas, los depósitos (`tipo`
SALIDA/ENTRADA) y los traspasos entre cuentas propias (`tipo` INTERNO: transferencias entre
cuentas, autopago de la tarjeta de crédito y cashback): un depósito o traspaso no es gasto, pero
sin ellos el saldo no se puede reconstruir ni se emparejan los retiros de Dropi. Cada fila guarda
su cuenta (últimos 4 del checking o `CREDIT`) y, en los cargos con tarjeta, sus últimos 4 y el
mercado de `_DIM_TARJETAS_MERCADO.csv` (vacío si la tarjeta no tiene mercado: no se adivina).

Sin `--escribir` solo MIRA y no toca disco (DOCTRINA/DATA_PLAYBOOK.md §7). Con `--json` el stdout es
SOLO el resumen en JSON (para el runner de la app).

Los montos van en la moneda de la cuenta (USD), siempre positivos; `saldo` es la columna Balance
del extracto (el CSV de Mercury no trae saldo). `tarjeta` queda vacía mientras el banco no la
imprima (Relay no la imprime).

Dedupe: la llave es (banco, cuenta, fecha, nombre, monto, saldo). Dos cargos idénticos el mismo día
se distinguen por el saldo corrido (Relay) o por la referencia del banco (Mercury, que va en el
nombre); re-ingerir no cambia nada. Los extractos traen movimientos de los primeros días del mes
siguiente: se ingieren tal cual vienen, y los reportes cortan por la fecha del movimiento.
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
import tarjetas_mercado  # noqa: E402

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

DESTINO = os.path.join(gen_pl.P, "_FACT_BANCO.csv")

COLUMNAS = ["fecha", "banco", "cuenta", "nombre", "monto", "tipo", "saldo", "tarjeta", "mercado",
            "archivo"]

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


def _fusionar(existentes, nuevas):
    """Agrega las que no están (por llave) y ordena. Devuelve (filas, agregar, duplicadas)."""
    vistas = {llave(f) for f in existentes}
    agregar, duplicadas = [], 0
    for f in nuevas:
        if llave(f) in vistas:
            duplicadas += 1
            continue
        vistas.add(llave(f))
        agregar.append(f)
    filas = sorted(existentes + agregar, key=lambda f: (f["fecha"], f["banco"], f["cuenta"],
                                                        f["nombre"], f["monto"], f["saldo"],
                                                        f.get("tarjeta") or "",
                                                        f.get("mercado") or ""))
    return filas, agregar, duplicadas


def validar(mov, resumen, cuenta, cuenta_pdf):
    if cuenta_pdf is not None and cuenta is not None and cuenta_pdf != cuenta:
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


def ingerir_texto(txt, archivo, banco, cuenta=None, destino=DESTINO, escribir=False):
    mov, resumen = gen_pl.movimientos_completos_del_extracto(txt)
    cuenta_pdf = cuenta_del_extracto(txt)
    cuenta = cuenta or cuenta_pdf
    if not cuenta:
        raise ExtractoInvalido("el extracto no trae el número de cuenta: pasá --cuenta con los "
                               "últimos 4 dígitos.")
    validar(mov, resumen, cuenta, cuenta_pdf)
    nuevas = [{
        "fecha": m["fecha"].isoformat(), "banco": banco, "cuenta": cuenta, "nombre": m["nombre"],
        "monto": csv_hechos.monto(m["monto"]), "tipo": m["tipo"],
        "saldo": csv_hechos.monto(m["saldo"]), "tarjeta": "", "mercado": "",
        "archivo": os.path.basename(archivo),
    } for m in mov]
    existentes = csv_hechos.leer(destino)
    filas, agregar, duplicadas = _fusionar(existentes, nuevas)
    res = {"banco": banco, "cuenta": cuenta, "archivo": os.path.basename(archivo),
           "movimientos_en_el_extracto": len(nuevas), "nuevas": len(agregar),
           "duplicadas": duplicadas,
           "salidas": sum(1 for f in nuevas if f["tipo"] == "SALIDA"),
           "entradas": sum(1 for f in nuevas if f["tipo"] == "ENTRADA"),
           "retiros_usd": resumen["retiros"], "depositos_usd": resumen["depositos"],
           "filas_guardadas": len(filas), "escrito": False}
    if escribir:
        csv_hechos.escribir(destino, COLUMNAS, filas)
        res["escrito"] = True
    return res


def ingerir(archivo, banco, cuenta=None, destino=DESTINO, escribir=False):
    if banco == "MERCURY":
        if cuenta is not None:
            raise ExtractoInvalido("--cuenta no aplica a Mercury: cada fila trae su cuenta.")
        return ingerir_mercury(archivo, destino=destino, escribir=escribir)
    return ingerir_texto(texto_del_pdf(archivo), archivo, banco, cuenta, destino, escribir)


MERCURY_REQUERIDAS = ["Date (UTC)", "Description", "Amount", "Status", "Source Account"]

MERCURY_INTERNO = ("transfer between your mercury accounts", "transfer to your new mercury account",
                   "io autopay", "mercury io cashback", "transfer in", "transfer out",
                   "credit account payment", "credit cashback deposit")


def cuenta_mercury(source):
    """La cuenta de una fila de Mercury: últimos 4 del checking o CREDIT."""
    m = re.search(r"xx(\d{4})", source or "")
    if m:
        return m.group(1)
    if (source or "").strip().lower() == "mercury credit":
        return "CREDIT"
    return ""


def tipo_mercury(descripcion, bank_desc, monto):
    """INTERNO si la descripción o la del banco es un traspaso entre cuentas propias; si no,
    ENTRADA o SALIDA por el signo."""
    textos = ((descripcion or "") + " " + (bank_desc or "")).strip().lower()
    if any(m in textos for m in MERCURY_INTERNO):
        return "INTERNO"
    if monto > 0:
        return "ENTRADA"
    if monto < 0:
        return "SALIDA"
    raise ExtractoInvalido("movimiento con monto 0: «%s»." % (descripcion or ""))


def fecha_mercury(fecha):
    """MM-DD-YYYY (como lo descarga Mercury) a YYYY-MM-DD."""
    try:
        return datetime.datetime.strptime((fecha or "").strip(), "%m-%d-%Y").date().isoformat()
    except ValueError:
        raise ExtractoInvalido("fecha que no es MM-DD-YYYY: «%s»." % (fecha or ""))


def nombre_mercury(descripcion, bank_desc):
    """La descripción tal cual, más la referencia del banco cuando trae una (es lo que distingue
    dos cargos iguales del mismo día)."""
    nombre = (descripcion or "").strip()
    ref = (bank_desc or "").strip()
    if ref and ref != nombre:
        nombre = "%s · %s" % (nombre, ref) if nombre else ref
    return nombre


def ingerir_mercury(archivo, destino=DESTINO, escribir=False, tarjetas=None):
    """Persiste los movimientos `Sent` del CSV de Mercury. `tarjetas` son las filas de
    `_DIM_TARJETAS_MERCADO.csv` (por defecto se leen); cada cargo con tarjeta guarda su mercado."""
    import csv as _csv
    import io as _io
    with _io.open(archivo, encoding="utf-8-sig", newline="") as f:
        lector = _csv.DictReader(f)
        faltan = [c for c in MERCURY_REQUERIDAS if c not in (lector.fieldnames or [])]
        if faltan:
            raise ExtractoInvalido("el CSV no trae las columnas %s." % ", ".join(faltan))
        crudo = list(lector)
    dim = tarjetas if tarjetas is not None else tarjetas_mercado.cargar()
    nuevas, excluidas = [], {"Pending": 0, "Failed": 0}
    no_usd = 0
    for r in crudo:
        estado = (r.get("Status") or "").strip()
        if estado != "Sent":
            excluidas[estado] = excluidas.get(estado, 0) + 1
            continue
        try:
            monto = float((r.get("Amount") or "").strip())
        except ValueError:
            raise ExtractoInvalido("monto que no es número: «%s»." % (r.get("Amount") or ""))
        moneda = (r.get("Original Currency") or "").strip()
        if moneda not in ("", "USD"):
            no_usd += 1
        tarjeta = (r.get("Last Four Digits") or "").strip()
        nuevas.append({
            "fecha": fecha_mercury(r.get("Date (UTC)")), "banco": "MERCURY",
            "cuenta": cuenta_mercury(r.get("Source Account")),
            "nombre": nombre_mercury(r.get("Description"), r.get("Bank Description")),
            "monto": csv_hechos.monto(abs(monto)),
            "tipo": tipo_mercury(r.get("Description"), r.get("Bank Description"), monto),
            "saldo": "", "tarjeta": tarjeta,
            "mercado": tarjetas_mercado.mercado_de(tarjeta, dim),
            "archivo": os.path.basename(archivo),
        })
    for f in nuevas:
        if not f["cuenta"]:
            raise ExtractoInvalido("fila Sent sin cuenta reconocible: %s %s %s."
                                   % (f["fecha"], f["nombre"], f["monto"]))
    existentes = csv_hechos.leer(destino)
    filas, agregar, duplicadas = _fusionar(existentes, nuevas)
    res = {"banco": "MERCURY", "archivo": os.path.basename(archivo),
           "filas_en_el_csv": len(crudo), "nuevas": len(agregar), "duplicadas": duplicadas,
           "salidas": sum(1 for f in nuevas if f["tipo"] == "SALIDA"),
           "entradas": sum(1 for f in nuevas if f["tipo"] == "ENTRADA"),
           "internos": sum(1 for f in nuevas if f["tipo"] == "INTERNO"),
           "excluidas_pending": excluidas.get("Pending", 0),
           "excluidas_failed": excluidas.get("Failed", 0),
           "excluidas_otras": sum(n for e, n in excluidas.items() if e not in ("Pending", "Failed")),
           "no_usd": no_usd, "filas_guardadas": len(filas), "escrito": False}
    if escribir:
        csv_hechos.escribir(destino, COLUMNAS, filas)
        res["escrito"] = True
    return res


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--archivo", required=True, help="extracto bancario (.pdf de Relay o .csv de Mercury)")
    ap.add_argument("--banco", required=True, help="banco del extracto (RELAY|MERCURY)")
    ap.add_argument("--cuenta", help="últimos 4 dígitos de la cuenta (solo Relay; default: la del extracto)")
    ap.add_argument("--escribir", action="store_true", help="persistir (sin esto solo mira)")
    ap.add_argument("--json", action="store_true", help="imprime solo el resumen en JSON")
    a = ap.parse_args(argv)
    try:
        res = ingerir(a.archivo, a.banco.upper(), a.cuenta, escribir=a.escribir)
    except ExtractoInvalido as e:
        print("BLOQUEANTE: %s: %s" % (os.path.basename(a.archivo), e), file=sys.stderr)
        return 1
    if a.json:
        print(json.dumps(res, ensure_ascii=False))
        return 0
    if res["banco"] == "MERCURY":
        print("%s · MERCURY · %d filas en el CSV (%d salidas, %d entradas, %d internas) · "
              "fuera %d Pending y %d Failed" % (
                  res["archivo"], res["filas_en_el_csv"], res["salidas"], res["entradas"],
                  res["internos"], res["excluidas_pending"], res["excluidas_failed"]))
        if res["no_usd"]:
            print("  ⚠ %d Sent no son USD: entran con su monto tal cual, revisar." % res["no_usd"])
    else:
        print("%s · %s ····%s · %d movimientos (%d salidas, %d depósitos) · Withdrawals $%.2f" % (
            os.path.basename(a.archivo), a.banco.upper(), res["cuenta"], res["movimientos_en_el_extracto"],
            res["salidas"], res["entradas"], res["retiros_usd"]))
    print("  nuevas %d · ya estaban %d" % (res["nuevas"], res["duplicadas"]))
    if res["escrito"]:
        print("escrito: %s (%d movimientos)" % (DESTINO, res["filas_guardadas"]))
    else:
        print("(solo mirar: no se escribió nada; --escribir para persistir)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
