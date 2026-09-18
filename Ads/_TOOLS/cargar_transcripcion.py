#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""cargar_transcripcion.py — guarda UNA transcripcion TXT de un video de la competencia en la
carpeta de transcripciones del producto.

Dato de DOCTRINA/FLUJO.json F1.congelar_inputs: «≥6 transcripciones TXT» (predicado glob sobre
`Ads/1.2 Transcripcion videos/{carpeta_transcripciones}/*.txt`). Es la OPCION 1 de la skill
fase-1-angulos: el operador trae el TXT (por ejemplo, el que le devuelve Gemini con
`Ads/Prompt-Gemini.txt`). Si trae el VIDEO, el camino es transcribir_videos.py.

Que escribe
-----------
  Ads/1.2 Transcripcion videos/{carpeta}/{N}. {titulo}.txt — N es el siguiente numero libre de la
  carpeta (la numeracion es la de siempre: «5. Nusava B12.txt»). El contenido se guarda tal cual.

Que bloquea (exit 1)
--------------------
  · un producto sin fila (eso es alta_producto.py);
  · un archivo que no es texto UTF-8, vacio o de mas de 1 MB (una transcripcion de un video de
    un minuto son unos pocos KB: un archivo de 1 MB no es una transcripcion);
  · un titulo con caracteres que no van en un nombre de archivo.

Lo que NO repite
----------------
Un TXT con el mismo contenido que otro de la carpeta no se guarda dos veces: contaria doble para
el minimo de 6 y etapa-0 clasificaria el mismo video como dos.

Uso
---
    python Ads/_TOOLS/cargar_transcripcion.py --producto TURMERIC --origen C:/.../subida.txt --titulo "Turmeric rodillas mama"
"""

import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import editar_producto as ep  # noqa: E402
from editar_producto import Rechazo  # noqa: E402

CARPETA = ("Ads", "1.2 Transcripcion videos")
TOPE = 1024 * 1024
RE_TITULO = re.compile(r"[\w áéíóúÁÉÍÓÚñÑüÜ.,()'-]{1,80}")
RE_NUMERADO = re.compile(r"^(\d+)\.")


def planear(args):
    base = args.base
    titulo = (args.titulo or "transcripcion").strip()
    if not RE_TITULO.fullmatch(titulo) or titulo.startswith("."):
        raise Rechazo(f"el titulo «{titulo}» no sirve como nombre de archivo: letras, numeros, espacios y "
                      "- _ . , ( ), hasta 80 caracteres.")
    encabezado, filas, indice = ep.buscar_producto(base, args.producto)
    fila = ep.fila_dict(encabezado, filas, indice)
    subcarpeta = (fila.get("carpeta_transcripciones") or "").strip() or args.producto
    carpeta = os.path.join(base, *CARPETA, subcarpeta)

    if not os.path.isfile(args.origen):
        raise Rechazo(f"no encuentro el archivo a cargar ({args.origen}).")
    with open(args.origen, "rb") as fh:
        contenido = fh.read()
    if len(contenido) > TOPE:
        raise Rechazo("el archivo pasa de 1 MB: no es la transcripcion de un video corto.")
    try:
        texto = contenido.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise Rechazo("el archivo no es texto UTF-8. Guardalo como .txt (UTF-8) y volvé a subirlo.")
    if not texto.strip():
        raise Rechazo("el archivo esta vacio.")

    existentes = sorted(n for n in os.listdir(carpeta) if n.lower().endswith(".txt")) if os.path.isdir(carpeta) else []
    for nombre in existentes:
        with open(os.path.join(carpeta, nombre), "rb") as fh:
            if fh.read() == contenido:
                return {"producto_key": args.producto, "archivo": f"{'/'.join(CARPETA)}/{subcarpeta}/{nombre}",
                        "total_en_carpeta": len(existentes), "sin_cambios": True, "cambios": [],
                        "avisos": [f"ya estaba cargada como «{nombre}»: no se guarda dos veces."],
                        "_escrituras": {}}

    numeros = [int(m.group(1)) for m in (RE_NUMERADO.match(n) for n in existentes) if m]
    siguiente = max(numeros, default=0) + 1
    nombre = f"{siguiente}. {titulo}.txt"
    relativa = f"{'/'.join(CARPETA)}/{subcarpeta}/{nombre}"
    return {
        "producto_key": args.producto,
        "archivo": relativa,
        "total_en_carpeta": len(existentes) + 1,
        "sin_cambios": False,
        "cambios": [{"archivo": relativa, "campo": "transcripcion", "antes": "(no existia)",
                     "despues": f"{len(texto)} caracteres"}],
        "avisos": [],
        "_escrituras": {os.path.join(carpeta, nombre): contenido},
    }


def salida_legible(plan, aplicado):
    cabecera = (f"SIN CAMBIOS: {plan['archivo']}" if plan["sin_cambios"]
                else f"{'CARGADA' if aplicado else 'SE CARGARIA'}: {plan['archivo']}")
    return "\n".join([cabecera, f"  transcripciones en la carpeta: {plan['total_en_carpeta']} (FASE 1 pide 6 o mas)"]
                     + ep.lineas_de_avisos(plan))


def main(argv=None):
    ap = argparse.ArgumentParser(description="Guarda una transcripcion TXT en la carpeta del producto")
    ep.argumentos_comunes(ap)
    ap.add_argument("--origen", required=True, help="el TXT que entrega el operador")
    ap.add_argument("--titulo", default=None, help="de que es el video (va en el nombre del archivo)")
    return ep.ejecutar(ap.parse_args(argv), planear, salida_legible)


if __name__ == "__main__":
    sys.exit(main())
