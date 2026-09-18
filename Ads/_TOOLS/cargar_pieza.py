#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""cargar_pieza.py — guarda en la carpeta de media del producto la PIEZA (imagen o video) de un
anuncio que el plan ya declara.

Dato de DOCTRINA/FLUJO.json F1.paquete: «paquete LANZABLE» (gen_publicacion.py --solo-paquete).
Uno de sus bloqueantes es «N pieza(s) declaradas no tienen su archivo en disco», con dueno
«etapa-render / el operador»: etapa-4 escribe los prompts de las imagenes, pero en FASE 1 nadie
las fabrica dentro de la skill. Este script es la puerta del operador para ese dato.

Que escribe
-----------
  Ads/{carpeta_media}/{archivo}  — el archivo que el operador entrega, con el nombre EXACTO que
  declara el plan. El nombre no lo elige este script ni el operador: lo declara etapa-6
  (`_PLAN.json` conjuntos[].archivo_creativo) o la fila de `_DIM_CREATIVOS.csv`. Un nombre que
  ninguno de los dos declara se rechaza: una pieza sin dueno es una pieza que gen_publicacion.py
  nunca va a publicar.

Que bloquea (exit 1)
--------------------
  · un producto sin fila, o sin carpeta de media (eso es alta_producto.py);
  · un nombre con carpeta, o que el plan no declara;
  · un archivo cuyo CONTENIDO no es del tipo que dice el nombre (un JPG no se guarda como .png:
    el nombre es el que se busca despues en la biblioteca de Meta);
  · un archivo vacio o demasiado grande (Meta: 30 MB por imagen);
  · cambiar una pieza que ya esta en disco sin --reemplazar.

Uso
---
    python Ads/_TOOLS/cargar_pieza.py --producto TURMERIC --archivo TURMERIC_1_MANOS.png --origen C:/.../subida.png
    python Ads/_TOOLS/cargar_pieza.py --producto X --archivo X_1_A.png --origen ... --dry-run --json
"""

import argparse
import csv
import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import editar_producto as ep  # noqa: E402
from editar_producto import Rechazo  # noqa: E402

MB = 1024 * 1024
# Lo que se reconoce por los primeros bytes: el nombre dice el tipo, el contenido lo confirma.
TIPOS = {
    ".png": ("imagen", 30 * MB),
    ".jpg": ("imagen", 30 * MB),
    ".jpeg": ("imagen", 30 * MB),
    ".mp4": ("video", 1024 * MB),
    ".mov": ("video", 1024 * MB),
}


def tipo_por_contenido(cabeza):
    """La extension que corresponde a los primeros bytes, o None si no se reconoce."""
    if cabeza.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if cabeza.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if len(cabeza) >= 12 and cabeza[4:8] == b"ftyp":
        return ".mov" if cabeza[8:10] == b"qt" else ".mp4"
    return None


def es_compatible(extension, por_contenido):
    grupos = ({".jpg", ".jpeg"}, {".mp4", ".mov"})
    if extension == por_contenido:
        return True
    return any(extension in g and por_contenido in g for g in grupos)


def declaradas(base, fila):
    """{archivo: de_donde} — las piezas que el sistema declara para el producto."""
    slug = fila["slug_carpeta"].strip() or fila["producto_key"]
    salida = {}
    for nombre in ("_PLAN.json", "_PLAN_FASE2.json", "_PLAN_FASE3.json"):
        ruta = os.path.join(base, "PRODUCTOS", slug, nombre)
        if not os.path.isfile(ruta):
            continue
        try:
            with io.open(ruta, encoding="utf-8") as fh:
                plan = json.load(fh)
        except (OSError, ValueError):
            raise Rechazo(f"PRODUCTOS/{slug}/{nombre} no se puede leer: se arregla primero (dueno: etapa-6).")
        for conjunto in plan.get("conjuntos") or []:
            archivo = (conjunto.get("archivo_creativo") or "").strip()
            if archivo:
                salida.setdefault(archivo, f"PRODUCTOS/{slug}/{nombre}")
    ruta = os.path.join(base, "PRODUCTOS", "_DIM_CREATIVOS.csv")
    if os.path.isfile(ruta):
        with io.open(ruta, encoding="utf-8", newline="") as fh:
            for r in csv.DictReader(fh):
                if (r.get("producto_key") or "").strip() == fila["producto_key"] and (r.get("archivo") or "").strip():
                    salida.setdefault(r["archivo"].strip(), "PRODUCTOS/_DIM_CREATIVOS.csv")
    return salida


def planear(args):
    base = args.base
    archivo = (args.archivo or "").strip()
    if not archivo or archivo != os.path.basename(archivo) or "/" in archivo or "\\" in archivo:
        raise Rechazo(f"«{archivo}» tiene que ser solo el nombre del archivo, sin carpeta.")
    extension = os.path.splitext(archivo)[1].lower()
    if extension not in TIPOS:
        raise Rechazo(f"«{archivo}» no termina en {', '.join(sorted(TIPOS))}: no es una pieza de anuncio.")

    encabezado, filas, indice = ep.buscar_producto(base, args.producto)
    fila = ep.fila_dict(encabezado, filas, indice)
    donde = declaradas(base, fila)
    if archivo not in donde:
        raise Rechazo(
            f"«{archivo}» no esta declarada para {args.producto}: el nombre de cada pieza lo pone el plan "
            "(etapa-6, _PLAN.json → archivo_creativo) o _DIM_CREATIVOS.csv. Declaradas: "
            + (", ".join(sorted(donde)) or "ninguna"))

    carpeta_media = (fila.get("carpeta_media") or "").strip() or ("MEDIA_" + args.producto)
    carpeta = os.path.join(base, "Ads", carpeta_media)
    if not os.path.isdir(carpeta):
        raise Rechazo(f"no existe Ads/{carpeta_media}: la carpeta de media la crea el alta del producto.")

    origen = args.origen
    if not os.path.isfile(origen):
        raise Rechazo(f"no encuentro el archivo a cargar ({origen}).")
    with io.open(origen, "rb") as fh:
        contenido = fh.read()
    clase, tope = TIPOS[extension]
    if not contenido:
        raise Rechazo("el archivo esta vacio.")
    if len(contenido) > tope:
        raise Rechazo(f"el archivo pesa {len(contenido) // MB} MB y una {clase} para Meta llega hasta {tope // MB} MB.")
    por_contenido = tipo_por_contenido(contenido[:16])
    if por_contenido is None or not es_compatible(extension, por_contenido):
        raise Rechazo(
            f"el plan pide «{archivo}» ({extension}) y el archivo entregado "
            + (f"es un {por_contenido}" if por_contenido else "no es una imagen PNG/JPG ni un video MP4/MOV")
            + ". Exportalo en el formato que dice el nombre: ese nombre es el que se busca en Meta.")

    destino = os.path.join(carpeta, archivo)
    relativa = f"Ads/{carpeta_media}/{archivo}"
    cambios, escrituras = [], {}
    if os.path.isfile(destino):
        with io.open(destino, "rb") as fh:
            actual = fh.read()
        if actual != contenido:
            if not args.reemplazar:
                raise Rechazo(
                    f"{relativa} ya existe con otro contenido. Cambiar la pieza cambia lo que se publica; si es "
                    "lo que queres, repetilo con --reemplazar.")
            cambios.append({"archivo": relativa, "campo": "pieza", "antes": f"{len(actual)} bytes",
                            "despues": f"{len(contenido)} bytes"})
            escrituras[destino] = contenido
    else:
        cambios.append({"archivo": relativa, "campo": "pieza", "antes": "(no existia)",
                        "despues": f"{len(contenido)} bytes"})
        escrituras[destino] = contenido

    return {
        "producto_key": args.producto,
        "archivo": archivo,
        "ruta": relativa,
        "declarada_en": donde[archivo],
        "sin_cambios": not cambios,
        "cambios": cambios,
        "avisos": [],
        "_escrituras": escrituras,
    }


def salida_legible(plan, aplicado):
    if plan["sin_cambios"]:
        cabecera = f"SIN CAMBIOS: {plan['ruta']} ya es esa pieza."
    else:
        cabecera = f"{'CARGADA' if aplicado else 'SE CARGARIA'}: {plan['ruta']}  (declarada en {plan['declarada_en']})"
    return "\n".join([cabecera] + ep.lineas_de_cambios(plan)
                     + ["", "SIGUIENTE PASO", f"  python Ads/_TOOLS/gen_publicacion.py --producto {plan['producto_key']} --fase 1 --solo-paquete"])


def main(argv=None):
    ap = argparse.ArgumentParser(description="Guarda la pieza de un anuncio con el nombre que declara el plan")
    ep.argumentos_comunes(ap)
    ap.add_argument("--archivo", required=True, help="nombre de la pieza tal como la declara el plan")
    ap.add_argument("--origen", required=True, help="el archivo que entrega el operador")
    ap.add_argument("--reemplazar", action="store_true", help="permite cambiar una pieza que ya esta en disco")
    return ep.ejecutar(ap.parse_args(argv), planear, salida_legible)


if __name__ == "__main__":
    sys.exit(main())
