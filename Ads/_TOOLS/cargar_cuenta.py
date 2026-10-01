#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""cargar_cuenta.py — asigna la cuenta publicitaria a un producto que ya tiene fila.

Dato de DOCTRINA/FLUJO.json F1.publicar: «cuenta publicitaria asignada» (cuenta_alias distinto
de vacio / PENDIENTE / SIN_MCP). Dueno del dato: el operador. Dueno de la LISTA de cuentas:
PRODUCTOS/_DIM_CUENTAS.csv; este script no inventa ninguna, solo elige una de ahi.

Que escribe
-----------
En la fila del producto de _DIM_PRODUCTOS.csv, DOS columnas que salen juntas de la misma fila de
_DIM_CUENTAS.csv:
  · cuenta_alias  en su forma corta («GTR 7» -> «GTR7»), como ya la llevan los productos del
                  portafolio y como la usa gen_publicacion.py en los nombres de Meta.
  · cuenta_id     el id numerico de esa cuenta.
NO toca `moneda` ni `tasa` de la fila: la moneda de la cuenta la lee gen_publicacion.py de
_DIM_CUENTAS.csv, y `tasa` es el tipo de cambio GTQ/USD del producto.

Que bloquea (exit 1)
--------------------
  · un producto sin fila (eso es alta_producto.py);
  · una cuenta que no esta en _DIM_CUENTAS.csv, o que no esta ACTIVE (RETIRADA);
  · cambiar una cuenta ya asignada sin --reemplazar: mover un producto de cuenta es una decision,
    no un descuido.

Lo que solo avisa (la cuenta se asigna igual; F1.publicar lo juzga con su predicado)
--------------------------------------------------------------------------------------
sin MCP habilitado (se pauta a mano), moneda distinta de USD (gen_publicacion.py lo bloquea),
sin metodo de pago, sin subida de media local (solo GTR 7 la tiene, medido el 08-sep).

Uso
---
    python Ads/_TOOLS/cargar_cuenta.py --producto TINNIDROP --cuenta "GTR 7"
    python Ads/_TOOLS/cargar_cuenta.py --producto X --cuenta GTR7 --dry-run --json
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


def buscar_cuenta(base, pedida):
    encabezado, filas = ep.leer_csv(os.path.join(base, "PRODUCTOS", "_DIM_CUENTAS.csv"))
    cuentas = [dict(zip(encabezado, f)) for f in filas if f]
    if ep.es_pendiente(pedida):
        raise Rechazo(f"«{pedida}» no es una cuenta: es la marca de que falta elegir una.")
    for cuenta in cuentas:
        if corto(cuenta["cuenta_alias"]) == corto(pedida):
            return cuenta
    raise Rechazo(
        f"la cuenta «{pedida}» no esta en _DIM_CUENTAS.csv. Las que hay: "
        + ", ".join(c["cuenta_alias"] for c in cuentas if c["estado_cuenta"] == "ACTIVE")
        + ". Una cuenta nueva la registra el operador en _DIM_CUENTAS.csv antes de asignarla."
    )


def avisos_de_la_cuenta(cuenta):
    alias = cuenta["cuenta_alias"]
    avisos = []
    if cuenta["mcp_habilitado"] != "SI":
        avisos.append(f"{alias} no tiene el MCP habilitado: F1.publicar queda bloqueado y se "
                      "pauta a mano (dueno: Meta, rollout; _DIM_CUENTAS.csv).")
    if cuenta["moneda"] != "USD":
        avisos.append(f"{alias} factura en {cuenta['moneda']}: el presupuesto se convierte "
                      "con la tasa del producto (columna tasa).")
    if cuenta["tiene_metodo_pago"] != "SI":
        avisos.append(f"{alias} no tiene metodo de pago: Meta no la deja gastar (dueno: el operador).")
    if cuenta["sube_media_local"] != "SI":
        avisos.append(f"{alias} no sube media local por MCP: las piezas se cargan a mano a la "
                      "biblioteca de la cuenta (solo GTR 7 la sube).")
    return avisos


def planear(args):
    base = args.base
    encabezado, filas, indice = ep.buscar_producto(base, args.producto)
    fila = ep.fila_dict(encabezado, filas, indice)
    cuenta = buscar_cuenta(base, args.cuenta)

    if cuenta["estado_cuenta"] != "ACTIVE":
        raise Rechazo(
            f"{cuenta['cuenta_alias']} esta {cuenta['estado_cuenta']} en _DIM_CUENTAS.csv: no se "
            "puede pautar ahi. Elegi una ACTIVE, o corregi el estado si Meta ya la reactivo."
        )

    actual = fila["cuenta_alias"].strip()
    nuevo_alias, nuevo_id = corto(cuenta["cuenta_alias"]), cuenta["cuenta_id"]
    avisos = avisos_de_la_cuenta(cuenta)
    anterior_real = not ep.es_pendiente(actual) and corto(actual) != "EXTERNA"

    if anterior_real and corto(actual) != nuevo_alias and not args.reemplazar:
        raise Rechazo(
            f"{args.producto} ya tiene la cuenta «{actual}». Cambiarla es mover el producto de "
            "cuenta (la pagina y su WhatsApp tienen que estar asignados a la nueva). Si es lo "
            "que queres, repetilo con --reemplazar."
        )
    if anterior_real and corto(actual) != nuevo_alias and (fila["campaign_id"] or "").strip() \
            and not ep.es_pendiente(fila["campaign_id"]):
        avisos.append(f"el producto ya tiene campaign_id {fila['campaign_id']}, creada en «{actual}»: "
                      "esa campana sigue donde esta.")

    cambios, escrituras = [], {}
    if corto(actual) != nuevo_alias or fila["cuenta_id"].strip() != nuevo_id:
        cambios = [
            {"archivo": "PRODUCTOS/_DIM_PRODUCTOS.csv", "campo": "cuenta_alias",
             "antes": actual, "despues": nuevo_alias},
            {"archivo": "PRODUCTOS/_DIM_PRODUCTOS.csv", "campo": "cuenta_id",
             "antes": fila["cuenta_id"], "despues": nuevo_id},
        ]
        ruta = os.path.join(base, "PRODUCTOS", "_DIM_PRODUCTOS.csv")
        escrituras[ruta] = ep.csv_con_cambios(
            encabezado, filas, indice, {"cuenta_alias": nuevo_alias, "cuenta_id": nuevo_id})

    return {
        "producto_key": args.producto,
        "cuenta_alias": nuevo_alias,
        "cuenta_id": nuevo_id,
        "sin_cambios": not cambios,
        "cambios": cambios,
        "avisos": avisos,
        "_escrituras": escrituras,
    }


def salida_legible(plan, aplicado):
    if plan["sin_cambios"]:
        cabecera = f"SIN CAMBIOS: {plan['producto_key']} ya tiene la cuenta {plan['cuenta_alias']}."
    else:
        verbo = "ASIGNADA" if aplicado else "SE ASIGNARIA"
        cabecera = f"{verbo}: {plan['producto_key']}  ->  {plan['cuenta_alias']} ({plan['cuenta_id']})"
    return "\n".join([cabecera] + ep.lineas_de_cambios(plan) + ep.lineas_de_avisos(plan)
                     + ["", "SIGUIENTE PASO", f"  python Ads/_TOOLS/flujo.py {plan['producto_key']}"])


def main(argv=None):
    ap = argparse.ArgumentParser(description="Asigna la cuenta publicitaria a un producto con fila")
    ep.argumentos_comunes(ap)
    ap.add_argument("--cuenta", required=True, help="cuenta_alias de _DIM_CUENTAS.csv («GTR 7» o «GTR7»)")
    ap.add_argument("--reemplazar", action="store_true",
                    help="permite cambiar una cuenta que el producto ya tiene")
    return ep.ejecutar(ap.parse_args(argv), planear, salida_legible)


if __name__ == "__main__":
    sys.exit(main())
