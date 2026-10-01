#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""cargar_moneda_cuenta.py — carga la moneda de la CUENTA publicitaria de un producto que ya tiene fila.

`moneda` es la moneda con que Meta COBRA la cuenta publicitaria (USD, COP): es la que
decide en que unidad menor va el daily_budget en Meta. No es la moneda de venta del
producto (esa es del mercado: GTQ en Guatemala, COP en Colombia) ni el simbolo con que se
muestra un precio.

Que escribe
-----------
SOLO la columna `moneda` de la fila del producto en PRODUCTOS/_DIM_PRODUCTOS.csv. Ningun
encabezado de TXT la lleva (1_HACER_MANUAL.txt, 2_DATA_PRODUCTO.txt y 3_CAMPAÑA_META.txt
no tienen campo moneda), asi que no se toca ningun otro archivo.

Que bloquea (exit 1)
--------------------
  · un producto sin fila (eso es alta_producto.py);
  · una moneda que no es un codigo conocido: los valores de la columna `moneda` de
    PRODUCTOS/_DIM_CUENTAS.csv unidos a los de PRODUCTOS/_DIM_MERCADOS.csv;
  · pedir una moneda distinta de la que factura la cuenta del producto: la moneda la dicta
    la cuenta (eso es cargar_cuenta.py), no este script;
  · cambiar una moneda ya cargada sin --reemplazar.

Lo que solo avisa
-----------------
Pedir una moneda distinta de USD con la columna `tasa` del producto vacia: sin tasa
gen_publicacion.py no puede convertir el presupuesto a esa moneda.

Uso
---
    python Ads/_TOOLS/cargar_moneda_cuenta.py --producto OVULOS_PURITY --moneda USD --reemplazar
    python Ads/_TOOLS/cargar_moneda_cuenta.py --producto X --moneda COP --dry-run --json
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import editar_producto as ep  # noqa: E402
from editar_producto import Rechazo  # noqa: E402


def corto(alias):
    """'GTR 7' -> 'GTR7'. Misma regla que gen_publicacion.corto_alias."""
    return (alias or "").replace(" ", "").upper()


def monedas_conocidas(base):
    """Los codigos de moneda que valen: columna `moneda` de _DIM_CUENTAS.csv mas la de
    _DIM_MERCADOS.csv. Se leen, no se escriben fijos."""
    conocidas = set()
    for nombre in ("_DIM_CUENTAS.csv", "_DIM_MERCADOS.csv"):
        encabezado, filas = ep.leer_csv(os.path.join(base, "PRODUCTOS", nombre))
        columna = encabezado.index("moneda")
        for fila in filas:
            if fila and len(fila) > columna:
                valor = fila[columna].strip().upper()
                if valor:
                    conocidas.add(valor)
    return conocidas


def buscar_cuenta(base, alias):
    """La fila de _DIM_CUENTAS.csv con ese cuenta_alias (sin espacios, en mayusculas),
    o None si la cuenta del producto no esta registrada ahi (p. ej. EXTERNA)."""
    encabezado, filas = ep.leer_csv(os.path.join(base, "PRODUCTOS", "_DIM_CUENTAS.csv"))
    cuentas = [dict(zip(encabezado, f)) for f in filas if f]
    for cuenta in cuentas:
        if corto(cuenta["cuenta_alias"]) == corto(alias):
            return cuenta
    return None


def planear(args):
    base = args.base
    moneda = (args.moneda or "").strip().upper()

    conocidas = monedas_conocidas(base)
    if moneda not in conocidas:
        raise Rechazo(
            f"«{args.moneda}» no es un codigo de moneda conocido. Los que valen: "
            + ", ".join(sorted(conocidas))
            + " (columna `moneda` de _DIM_CUENTAS.csv y _DIM_MERCADOS.csv)."
        )

    encabezado, filas, indice = ep.buscar_producto(base, args.producto)
    fila = ep.fila_dict(encabezado, filas, indice)

    cuenta = buscar_cuenta(base, fila["cuenta_alias"])
    if cuenta is not None and cuenta["moneda"].strip().upper() != moneda:
        raise Rechazo(
            f"la moneda la dicta la cuenta {cuenta['cuenta_alias']} ({cuenta['moneda'].strip()}): "
            f"{args.producto} factura por ahi; si cambió de cuenta, eso es cargar_cuenta.py."
        )

    actual = fila["moneda"].strip()
    if actual.strip().upper() and actual.strip().upper() != moneda and not args.reemplazar:
        raise Rechazo(
            f"{args.producto} ya tiene la moneda {actual}. Cambiarla es cambiar en que moneda "
            "cobra Meta esa cuenta; si es lo que queres (o la anterior estaba mal), repetilo "
            "con --reemplazar."
        )

    cambios, escrituras, avisos = [], {}, []
    if actual.strip().upper() != moneda:
        cambios.append({"archivo": "PRODUCTOS/_DIM_PRODUCTOS.csv", "campo": "moneda",
                        "antes": actual, "despues": moneda})
        escrituras[os.path.join(base, "PRODUCTOS", "_DIM_PRODUCTOS.csv")] = \
            ep.csv_con_cambios(encabezado, filas, indice, {"moneda": moneda})

    if moneda != "USD" and not (fila["tasa"] or "").strip():
        avisos.append(f"{args.producto} queda en {moneda} sin tasa declarada (columna `tasa` "
                      "vacia): gen_publicacion.py no puede convertir el presupuesto a esa "
                      "moneda hasta que se cargue la tasa.")

    return {
        "producto_key": args.producto,
        "moneda": moneda,
        "sin_cambios": not cambios,
        "cambios": cambios,
        "avisos": avisos,
        "_escrituras": escrituras,
    }


def salida_legible(plan, aplicado):
    if plan["sin_cambios"]:
        cabecera = f"SIN CAMBIOS: {plan['producto_key']} ya tiene la moneda {plan['moneda']}."
    else:
        verbo = "CARGADA" if aplicado else "SE CARGARIA"
        cabecera = f"{verbo}: {plan['producto_key']}  ->  moneda {plan['moneda']}"
    return "\n".join([cabecera] + ep.lineas_de_cambios(plan) + ep.lineas_de_avisos(plan)
                     + ["", "SIGUIENTE PASO", f"  python Ads/_TOOLS/gen_manual.py {plan['producto_key']} --validar"])


def main(argv=None):
    ap = argparse.ArgumentParser(description="Carga la moneda de la cuenta publicitaria de un producto con fila")
    ep.argumentos_comunes(ap)
    ap.add_argument("--moneda", required=True, help="codigo de moneda con que Meta cobra la cuenta (USD, COP)")
    ap.add_argument("--reemplazar", action="store_true",
                    help="permite cambiar una moneda que el producto ya tiene")
    return ep.ejecutar(ap.parse_args(argv), planear, salida_legible)


if __name__ == "__main__":
    sys.exit(main())
