#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""cargar_imagen_concepto.py — guarda la imagen que el operador renderizo a mano para UN concepto.

El operador baja la imagen de ChatGPT con un nombre cualquiera y la carga sobre la tarjeta del
concepto. Este escritor la deja con el nombre canonico de su fila de PRODUCTOS/_DIM_CREATIVOS.csv
(columna `archivo`) en Ads/<carpeta_media>/ y pasa SOLO esa fila a GENERADO con
`marcar_generados.py`. El nombre de lo que se subio no importa y nunca llega al disco.

Que bloquea (exit 1)
--------------------
  · un producto sin fila en _DIM_PRODUCTOS.csv o un creativo que no esta en _DIM_CREATIVOS.csv;
  · una fila que no es formato IMAGEN (el video pasa por LAVADO.md);
  · una fila ya PUBLICADA: su imagen es la que corre en Meta y no se pisa;
  · un `archivo` de la fila que no es un nombre simple .png/.jpg/.jpeg (nunca sale de la carpeta);
  · un archivo vacio, de mas de 25 MB, o que no es PNG/JPEG por su CONTENIDO.

Si la imagen subida es de otro tipo que el de la fila (JPEG en una fila .png, o al reves) se
convierte al tipo de la fila con Pillow: el nombre y el contenido siguen coincidiendo, que es lo
que Meta y los gates miran. Volver a cargar sobre un concepto GENERADO reemplaza el archivo.

Uso
---
    python Ads/_TOOLS/cargar_imagen_concepto.py --producto PK --creativo PK_R1_X --origen C:/.../a.png
    python Ads/_TOOLS/cargar_imagen_concepto.py ... --dry-run --json
"""

import argparse
import csv
import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import editar_producto as ep  # noqa: E402
import marcar_generados as mg  # noqa: E402
from cargar_pieza import tipo_por_contenido  # noqa: E402
from editar_producto import Rechazo  # noqa: E402

MB = 1024 * 1024
TOPE = 25 * MB
FORMATO_PIL = {".png": "PNG", ".jpg": "JPEG", ".jpeg": "JPEG"}
ESTADOS_EDITABLES = (mg.PENDIENTE, mg.GENERADO)


def _fila_del_creativo(base, producto, creativo):
    ruta = os.path.join(base, "PRODUCTOS", "_DIM_CREATIVOS.csv")
    if not os.path.isfile(ruta):
        raise Rechazo("no existe PRODUCTOS/_DIM_CREATIVOS.csv.")
    with io.open(ruta, encoding="utf-8-sig", newline="") as fh:
        for fila in csv.DictReader(fh):
            if fila.get("producto_key") == producto and fila.get("creativo_id") == creativo:
                return fila
    raise Rechazo(f"«{creativo}» no es un concepto de {producto} en _DIM_CREATIVOS.csv.")


def _convertir(contenido, extension):
    try:
        from PIL import Image
    except ImportError as error:
        raise Rechazo("hace falta Pillow para convertir la imagen al tipo de la fila.") from error
    formato = FORMATO_PIL[extension]
    try:
        with Image.open(io.BytesIO(contenido)) as imagen:
            if formato == "JPEG" and imagen.mode != "RGB":
                imagen = imagen.convert("RGB")
            salida = io.BytesIO()
            imagen.save(salida, formato, **({"quality": 95} if formato == "JPEG" else {}))
    except Exception as error:  # imagen corrupta o truncada
        raise Rechazo("no se pudo leer la imagen: esta corrupta o incompleta.") from error
    return salida.getvalue()


def planear(args):
    base, producto, creativo = args.base, args.producto, args.creativo
    carpeta = mg._carpeta_media(producto)
    if carpeta is None:
        raise Rechazo(f"«{producto}» no tiene fila en _DIM_PRODUCTOS.csv.")
    fila = _fila_del_creativo(base, producto, creativo)
    formato = (fila.get("formato") or "").strip().upper()
    if formato != "IMAGEN":
        raise Rechazo(f"«{creativo}» es {formato or 'de formato desconocido'}: solo se cargan imagenes "
                      "en conceptos IMAGEN (el video pasa por LAVADO.md).")
    estado = (fila.get("estado") or "").strip()
    if estado not in ESTADOS_EDITABLES:
        raise Rechazo(f"«{creativo}» esta {estado}: su imagen ya corre en Meta y no se pisa.")
    archivo = (fila.get("archivo") or "").strip()
    extension = os.path.splitext(archivo)[1].lower()
    if not archivo or archivo != os.path.basename(archivo) or extension not in FORMATO_PIL:
        raise Rechazo(f"el archivo de la fila («{archivo}») no es un nombre .png/.jpg valido.")

    if not os.path.isfile(args.origen):
        raise Rechazo(f"no encuentro el archivo a cargar ({args.origen}).")
    with io.open(args.origen, "rb") as fh:
        contenido = fh.read()
    if not contenido:
        raise Rechazo("la imagen esta vacia.")
    if len(contenido) > TOPE:
        raise Rechazo(f"la imagen pesa {len(contenido) // MB} MB y se aceptan hasta {TOPE // MB} MB.")
    por_contenido = tipo_por_contenido(contenido[:16])
    if por_contenido not in (".png", ".jpg"):
        raise Rechazo("el archivo no es una imagen PNG o JPEG (se mira el contenido, no el nombre).")
    tipo_de_la_fila = ".png" if extension == ".png" else ".jpg"
    convertida = tipo_de_la_fila != por_contenido
    if convertida:
        contenido = _convertir(contenido, extension)

    destino = os.path.join(base, "Ads", carpeta, archivo)
    reemplazo = os.path.isfile(destino)
    cambios = [{"archivo": f"Ads/{carpeta}/{archivo}", "campo": "imagen",
                "antes": "otra imagen" if reemplazo else "(no existia)", "despues": f"{len(contenido)} bytes"}]
    if estado == mg.PENDIENTE:
        cambios.append({"archivo": "PRODUCTOS/_DIM_CREATIVOS.csv", "campo": f"estado de {creativo}",
                        "antes": mg.PENDIENTE, "despues": mg.GENERADO})
    return {"producto_key": producto, "creativo_id": creativo, "archivo": archivo,
            "angulo_key": fila.get("angulo_key") or "", "carpeta_media": carpeta,
            "convertida": convertida, "reemplazo": reemplazo, "cambios": cambios, "avisos": [],
            "sin_cambios": False, "_contenido": contenido, "_destino": destino}


def aplicar(plan):
    """Imagen a un .tmp junto a su destino y `os.replace` (atomico); recien despues la fila."""
    destino, temporal = plan["_destino"], plan["_destino"] + ".tmp"
    try:
        with io.open(temporal, "wb") as fh:
            fh.write(plan["_contenido"])
        os.replace(temporal, destino)
    finally:
        if os.path.exists(temporal):
            os.remove(temporal)
    mg.marcar(plan["producto_key"], plan["angulo_key"] or None, True, plan["creativo_id"])


def main(argv=None):
    ap = argparse.ArgumentParser(description="Guarda la imagen renderizada a mano de un concepto y lo marca GENERADO")
    ep.argumentos_comunes(ap)
    ap.add_argument("--creativo", required=True, help="creativo_id de _DIM_CREATIVOS.csv")
    ap.add_argument("--origen", required=True, help="la imagen que entrega el operador")
    args = ap.parse_args(argv)
    mg.BASE = args.base
    try:
        plan = planear(args)
        aplicado = not args.dry_run
        if aplicado:
            aplicar(plan)
    except Rechazo as rechazo:
        if args.json:
            print(json.dumps({"ok": False, "detalle": str(rechazo)}, ensure_ascii=False))
        else:
            print(f"BLOQUEANTE: {rechazo}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(ep.plan_publico(plan, aplicado), ensure_ascii=False, indent=2))
    else:
        print(("GUARDADA" if aplicado else "SE GUARDARIA") + f": Ads/{plan['carpeta_media']}/{plan['archivo']}")
        print("\n".join(ep.lineas_de_cambios(plan)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
