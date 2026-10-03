#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""cargar_costeo.py — carga las 4 cifras de costeo de un producto que ya tiene fila.

Que escribe
-----------
SOLO las columnas de costeo de la fila del producto en PRODUCTOS/_DIM_PRODUCTOS.csv, con los
valores que calcula costear.py (este script no calcula nada propio):

    fila_costeo_q   <-  fila_usada (la fila de la tabla del mercado que uso costear)
    precio_base_q   <-  precio_1u
    cpa_base_q      <-  cpa_base
    cpa_be_q        <-  cpa_break_even

Sin cpa_be_q el gate de FASE 1 bloquea al producto (exige cpa_be_q >= 1). Los numeros van con
el formato de las filas de GT: fila y precio enteros sin decimales, los cpa_* con 2.

El costo del pedido
-------------------
`--costo-pedido` es el costo del PEDIDO que decidio etapa-1 cuando difiere del costo_q de la
fila (p. ej. las 2 unidades de un producto 2x1). Sin el flag se usa la columna costo_q. El
mercado sale de la columna mercado de la fila (mercado.mercado_de_fila, como gen_publicacion.py)
y con el mercado se elige la tabla: _DIM_COSTEO.csv en GT, _DIM_COSTEO_CO.csv en CO.

Que bloquea (exit 1)
--------------------
  · un producto sin fila (eso es alta_producto.py);
  · un costo que no es un numero positivo;
  · un mercado sin tabla de costeo: costear hace sys.exit y aca es un rechazo que nombra el
    mercado;
  · un costo que supera el techo de la tabla (costear devuelve «alerta»): las cifras no valen;
  · una cifra que costear no devolvio (None): se nombra y no se escribe nada;
  · cambiar una cifra ya cargada sin --reemplazar.

Uso
---
    python Ads/_TOOLS/cargar_costeo.py --producto NUSAVA
    python Ads/_TOOLS/cargar_costeo.py --producto X --costo-pedido 90 --reemplazar
    python Ads/_TOOLS/cargar_costeo.py --producto X --dry-run --json
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import costear  # noqa: E402
import mercado  # noqa: E402
import editar_producto as ep  # noqa: E402
from editar_producto import Rechazo  # noqa: E402

COLUMNAS = ("fila_costeo_q", "precio_base_q", "cpa_base_q", "cpa_be_q")


def normalizar_costo(crudo):
    costo = str(crudo).strip().replace(",", ".")
    try:
        valor = float(costo)
    except ValueError:
        valor = -1.0
    if not costo or valor <= 0:
        raise Rechazo(f"el costo «{crudo}» no es un numero positivo. Va del pedido completo, "
                      "en la moneda del mercado del producto.")
    return costo


def _entero(valor):
    return str(int(round(float(valor))))


def _dos_decimales(valor):
    return "%.2f" % float(valor)


def _mismo_numero(a, b):
    try:
        return float(str(a).replace(",", ".")) == float(str(b).replace(",", "."))
    except ValueError:
        return False


def cifras_de_costear(costo, mkt):
    """Las 4 columnas ya formateadas, o Rechazo si costear no las puede dar."""
    try:
        resultado = costear.costear(costo, mercado=mkt)
    except SystemExit:
        raise Rechazo(f"no hay tabla de costeo para el mercado {mkt}.")
    if "alerta" in resultado:
        raise Rechazo(resultado["alerta"])
    brutos = {"fila_costeo_q": resultado["fila_usada"],
              "precio_base_q": resultado["precio_1u"],
              "cpa_base_q": resultado["cpa_base"],
              "cpa_be_q": resultado["cpa_break_even"]}
    faltan = [c for c in COLUMNAS if brutos[c] is None]
    if faltan:
        raise Rechazo("costear no devolvio " + ", ".join(faltan)
                      + f" para el costo {costo} del mercado {mkt}: falta en la tabla "
                      "y no se escribe nada.")
    return {"fila_costeo_q": _entero(brutos["fila_costeo_q"]),
            "precio_base_q": _entero(brutos["precio_base_q"]),
            "cpa_base_q": _dos_decimales(brutos["cpa_base_q"]),
            "cpa_be_q": _dos_decimales(brutos["cpa_be_q"])}


def planear(args):
    base = args.base
    encabezado, filas, indice = ep.buscar_producto(base, args.producto)
    fila = ep.fila_dict(encabezado, filas, indice)

    if (args.costo_pedido or "").strip():
        costo = normalizar_costo(args.costo_pedido)
    elif not ep.es_pendiente(fila["costo_q"]):
        costo = normalizar_costo(fila["costo_q"])
    else:
        raise Rechazo(f"{args.producto} no tiene costo_q: sin costo no hay costeo. Pasalo con "
                      "--costo-pedido (el costo del PEDIDO que decidio etapa-1).")

    try:
        mkt = mercado.mercado_de_fila(fila, base)
    except mercado.MercadoError as exc:
        raise Rechazo(str(exc))

    nuevos = cifras_de_costear(costo, mkt)

    en_conflicto = [c for c in COLUMNAS
                    if fila[c].strip() and not ep.es_pendiente(fila[c])
                    and not _mismo_numero(fila[c], nuevos[c])]
    if en_conflicto and not args.reemplazar:
        detalle = "; ".join(f"{c}: «{fila[c].strip()}» -> «{nuevos[c]}»" for c in en_conflicto)
        raise Rechazo(f"{args.producto} ya tiene cifras de costeo que no son las de la tabla "
                      f"({detalle}). Si el costo cambio de verdad o las anteriores estaban mal, "
                      "repetilo con --reemplazar; si no, revisa el costo antes de cargar.")

    cambios = [{"archivo": "PRODUCTOS/_DIM_PRODUCTOS.csv", "campo": c,
                "antes": fila[c].strip(), "despues": nuevos[c]}
               for c in COLUMNAS if not _mismo_numero(fila[c], nuevos[c])]
    escrituras = {}
    if cambios:
        escrituras[os.path.join(base, "PRODUCTOS", "_DIM_PRODUCTOS.csv")] = \
            ep.csv_con_cambios(encabezado, filas, indice, {c["campo"]: c["despues"] for c in cambios})

    plan = {"producto_key": args.producto, "mercado": mkt, "costo_usado": costo,
            "sin_cambios": not cambios, "cambios": cambios, "avisos": [],
            "_escrituras": escrituras}
    plan.update(nuevos)
    return plan


def salida_legible(plan, aplicado):
    if plan["sin_cambios"]:
        cabecera = (f"SIN CAMBIOS: las cifras de costeo de {plan['producto_key']} ya son las de "
                    f"la fila {plan['fila_costeo_q']} del mercado {plan['mercado']}.")
    else:
        verbo = "COSTEO CARGADO" if aplicado else "SE CARGARIA EL COSTEO"
        cabecera = (f"{verbo}: {plan['producto_key']}  ->  fila {plan['fila_costeo_q']} "
                    f"(mercado {plan['mercado']}, costo {plan['costo_usado']})")
    return "\n".join([cabecera] + ep.lineas_de_cambios(plan) + ep.lineas_de_avisos(plan)
                     + ["", "SIGUIENTE PASO", f"  python Ads/_TOOLS/flujo.py {plan['producto_key']}"])


def main(argv=None):
    ap = argparse.ArgumentParser(description="Carga las cifras de costeo que calcula costear.py")
    ep.argumentos_comunes(ap)
    ap.add_argument("--costo-pedido",
                    help="costo del PEDIDO que decidio etapa-1 (default: costo_q de la fila)")
    ap.add_argument("--reemplazar", action="store_true",
                    help="permite sobreescribir cifras de costeo ya cargadas")
    return ep.ejecutar(ap.parse_args(argv), planear, salida_legible)


if __name__ == "__main__":
    sys.exit(main())
