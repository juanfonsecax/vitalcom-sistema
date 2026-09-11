#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""registrar_evento.py — el único escritor manual de PRODUCTOS/_EVENTOS.csv.

Todo cambio que se ejecuta en Meta o en el bot deja una fila: sin ella el cambio no se puede
evaluar después. El caso que obliga a tener esta herramienta es el surfing: es la acción diaria
por defecto y `_EVENTOS.csv` no tenía un solo CAMBIO_PRESUPUESTO, así que la elasticidad del CPA
al presupuesto no se puede medir y ninguna política de asignación se puede validar.

Valida antes de escribir y escribe con csv.DictWriter (invariante 11):
    · producto_key existe en _DIM_PRODUCTOS.csv (o GLOBAL)
    · evento es una palabra en MAYÚSCULAS_CON_GUION_BAJO
    · motivo y fuente_decision no vacíos
    · CAMBIO_PRESUPUESTO: valor_antes y valor_despues numéricos, un conjunto o campaña, y la
      subida no supera surfing_pct de _PARAMETROS_DECISION.csv salvo --forzar

USO
    python Ads/_TOOLS/registrar_evento.py --producto TINNIDROP --evento CAMBIO_PRESUPUESTO \\
        --cuenta GTR0 --conjunto GTR0_TINNIDROP_PERDIDA-AUDITIVA_R1 --antes 4.49 --despues 5.39 \\
        --motivo "ESCALAR del motor: surfing +20%" --fuente "decidir.py 2026-09-11 · confirmado operador"
    ... --dry-run      # muestra la fila y no escribe
"""
import argparse
import csv
import datetime
import io
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except (AttributeError, OSError):
    pass

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROD = os.path.join(BASE, "PRODUCTOS")
EVENTOS = os.path.join(PROD, "_EVENTOS.csv")
COLS = ["fecha", "producto_key", "cuenta_alias", "campana_clave", "conjunto_meta", "evento",
        "valor_antes", "valor_despues", "motivo", "fuente_decision"]


def leer(nombre):
    ruta = os.path.join(PROD, nombre)
    if not os.path.exists(ruta):
        return []
    with io.open(ruta, encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def surfing_pct():
    for r in leer("_PARAMETROS_DECISION.csv"):
        if (r.get("parametro") or "").strip() == "surfing_pct":
            try:
                return float(r.get("valor"))
            except (TypeError, ValueError):
                return None
    return None


def validar(fila, forzar):
    errores = []
    try:
        datetime.date.fromisoformat(fila["fecha"])
    except ValueError:
        errores.append("fecha '%s' no es YYYY-MM-DD" % fila["fecha"])
    productos = {(r.get("producto_key") or "").strip() for r in leer("_DIM_PRODUCTOS.csv")}
    if fila["producto_key"] != "GLOBAL" and fila["producto_key"] not in productos:
        errores.append("producto_key '%s' no tiene fila en _DIM_PRODUCTOS.csv" % fila["producto_key"])
    if not re.fullmatch(r"[A-Z][A-Z0-9_]*", fila["evento"]):
        errores.append("evento '%s' debe ir en MAYÚSCULAS_CON_GUION_BAJO" % fila["evento"])
    for campo in ("motivo", "fuente_decision"):
        if not fila[campo].strip():
            errores.append("%s vacío: un evento sin por qué no se puede evaluar" % campo)

    if fila["evento"] == "CAMBIO_PRESUPUESTO":
        try:
            antes, despues = float(fila["valor_antes"]), float(fila["valor_despues"])
        except ValueError:
            errores.append("CAMBIO_PRESUPUESTO exige --antes y --despues numéricos (USD/día)")
            return errores
        if fila["conjunto_meta"] in ("", "*") and fila["campana_clave"] in ("", "*"):
            errores.append("CAMBIO_PRESUPUESTO exige --conjunto o --campana: sin objeto no hay elasticidad que medir")
        tope = surfing_pct()
        if antes > 0 and tope is not None and not forzar:
            pct = (despues / antes - 1) * 100
            if pct > tope + 0.5:
                errores.append("subida de %.1f %% supera surfing_pct = %g %%; si es deliberado, usar --forzar"
                               % (pct, tope))
    return errores


def anexar(fila):
    # El archivo termina en CRLF (convención de la casa); si no, la fila nueva quedaría pegada.
    if os.path.exists(EVENTOS):
        with io.open(EVENTOS, "rb") as fh:
            fh.seek(0, os.SEEK_END)
            if fh.tell():
                fh.seek(-1, os.SEEK_END)
                sin_salto = fh.read(1) != b"\n"
        if sin_salto:
            with io.open(EVENTOS, "ab") as fh:
                fh.write(b"\r\n")
    with io.open(EVENTOS, "a", encoding="utf-8", newline="") as fh:
        csv.DictWriter(fh, fieldnames=COLS, lineterminator="\r\n").writerow(fila)


def main():
    ap = argparse.ArgumentParser(description="Anexa un evento validado a PRODUCTOS/_EVENTOS.csv")
    ap.add_argument("--producto", required=True, help="producto_key o GLOBAL")
    ap.add_argument("--evento", required=True)
    ap.add_argument("--motivo", required=True)
    ap.add_argument("--fuente", required=True, help="fuente_decision: quién decidió y con qué")
    ap.add_argument("--fecha", default=datetime.date.today().isoformat())
    ap.add_argument("--cuenta", default="*")
    ap.add_argument("--campana", default="*")
    ap.add_argument("--conjunto", default="*")
    ap.add_argument("--antes", default="")
    ap.add_argument("--despues", default="")
    ap.add_argument("--forzar", action="store_true", help="acepta una subida mayor a surfing_pct")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    fila = {"fecha": a.fecha, "producto_key": a.producto.strip(), "cuenta_alias": a.cuenta.strip(),
            "campana_clave": a.campana.strip(), "conjunto_meta": a.conjunto.strip(),
            "evento": a.evento.strip().upper(), "valor_antes": a.antes.strip(),
            "valor_despues": a.despues.strip(), "motivo": a.motivo.strip(),
            "fuente_decision": a.fuente.strip()}

    errores = validar(fila, a.forzar)
    if errores:
        print("NO SE REGISTRÓ:\n  · " + "\n  · ".join(errores))
        return 1
    if a.dry_run:
        print("[dry-run] se anexaría:", fila)
        return 0
    anexar(fila)
    print("registrado en PRODUCTOS/_EVENTOS.csv: %s %s %s" % (fila["fecha"], fila["producto_key"], fila["evento"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
