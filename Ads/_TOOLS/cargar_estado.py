#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""cargar_estado.py — carga el estado (NUEVO / VIVO / PAUSADO) de un producto que ya tiene fila.

El estado es el dato que DOCTRINA/FLUJO.json lee para la excepcion PAUSADO y el que decide si
la corrida nocturna audita y ordena ese producto. _DIM_PRODUCTOS.csv es espejo de Postgres:
tocarlo a mano frena la noche, asi que el estado se carga por aca.

Que escribe
-----------
SOLO la columna `estado` de la fila del producto en PRODUCTOS/_DIM_PRODUCTOS.csv.

Lo que NO hace
--------------
No registra el evento: al final imprime el comando exacto de registrar_evento.py para dejar
el cambio con su motivo en PRODUCTOS/_EVENTOS.csv. El evento lo corre quien decidio el cambio.

Que bloquea (exit 1)
--------------------
  · un producto sin fila (eso es alta_producto.py);
  · un estado fuera de NUEVO / VIVO / PAUSADO (los unicos que el sistema compara);
  · un motivo vacio: es lo que explica el cambio en _EVENTOS.csv.
Pedir el estado que ya tiene es «sin cambios»: no rechaza y no escribe.

Uso
---
    python Ads/_TOOLS/cargar_estado.py --producto VARICOSE --estado VIVO --motivo "reingreso"
    python Ads/_TOOLS/cargar_estado.py --producto X --estado PAUSADO --motivo "..." --dry-run --json
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import editar_producto as ep  # noqa: E402
from editar_producto import Rechazo  # noqa: E402

VALIDOS = ("NUEVO", "VIVO", "PAUSADO")


def comando_evento(producto, motivo, antes, despues):
    return (f"python Ads/_TOOLS/registrar_evento.py --producto {producto} --evento CAMBIO_ESTADO "
            f"--motivo \"{motivo}\" --fuente operador --antes {antes} --despues {despues}")


def planear(args):
    base = args.base
    estado = (args.estado or "").strip().upper()
    if estado not in VALIDOS:
        raise Rechazo(f"«{args.estado}» no es un estado de producto. Los que valen: "
                      + ", ".join(VALIDOS) + ".")
    motivo = (args.motivo or "").strip()
    if not motivo:
        raise Rechazo("el motivo no puede quedar vacio: es lo que explica el cambio en "
                      "_EVENTOS.csv.")

    encabezado, filas, indice = ep.buscar_producto(base, args.producto)
    fila = ep.fila_dict(encabezado, filas, indice)
    actual = (fila["estado"] or "").strip().upper()

    cambios, escrituras, avisos = [], {}, []
    if actual != estado:
        cambios.append({"archivo": "PRODUCTOS/_DIM_PRODUCTOS.csv", "campo": "estado",
                        "antes": actual, "despues": estado})
        escrituras[os.path.join(base, "PRODUCTOS", "_DIM_PRODUCTOS.csv")] = \
            ep.csv_con_cambios(encabezado, filas, indice, {"estado": estado})
        avisos.append(comando_evento(args.producto, motivo, actual, estado))

    return {"producto_key": args.producto, "estado": estado, "estado_anterior": actual,
            "sin_cambios": not cambios, "cambios": cambios, "avisos": avisos,
            "_escrituras": escrituras}


def salida_legible(plan, aplicado):
    if plan["sin_cambios"]:
        return f"SIN CAMBIOS: {plan['producto_key']} ya esta en estado {plan['estado']}."
    verbo = "ESTADO CAMBIADO" if aplicado else "SE CAMBIARIA EL ESTADO"
    return "\n".join([f"{verbo}: {plan['producto_key']}  ->  {plan['estado']}"]
                     + ep.lineas_de_cambios(plan)
                     + ["", "EL EVENTO NO SE REGISTRA SOLO — ejecuta:"]
                     + [f"  {a}" for a in plan["avisos"]])


def main(argv=None):
    ap = argparse.ArgumentParser(description="Carga el estado de un producto con fila")
    ep.argumentos_comunes(ap)
    ap.add_argument("--estado", required=True, help="NUEVO, VIVO o PAUSADO")
    ap.add_argument("--motivo", required=True, help="por que cambia el estado (va a _EVENTOS.csv)")
    return ep.ejecutar(ap.parse_args(argv), planear, salida_legible)


if __name__ == "__main__":
    sys.exit(main())
