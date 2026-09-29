#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""cargar_packshot.py — dueno del PACKSHOT de un producto: la foto del envase real y su identidad fisica.

Dato: PRODUCTOS/_DIM_ENVASE.csv (una fila por producto). La identidad fisica se DECLARA, nunca se
adivina (armar_prompts_fase2.py bloquea sin ella): con esta fila la IA hace que el producto salga
igual en todos los anuncios. Antes de este escritor solo `alta_producto.py` la creaba, y solo en el
alta; un producto que llegaba sin foto no tenia como completarla sin editar el CSV a mano.

Que escribe
-----------
  Ads/{carpeta_media}/{producto_key}_PACKSHOT.{png|jpg}   la foto (la extension sale del CONTENIDO)
  PRODUCTOS/_DIM_ENVASE.csv                                UPSERT de la fila del producto:
      packshot, color_envase, color_hex, marca_impresa, formato_envase, notas,
      verificado_el = hoy, fuente = "foto subida por el operador desde la app"
  El resto de filas del CSV pasa intacto (upsert_fact.upsert: escritor CSV real, con respaldo).

Que bloquea (exit 1)
--------------------
  · un producto sin fila en _DIM_PRODUCTOS.csv, o sin carpeta de media (eso es alta_producto.py);
  · marca impresa, color o formato vacios; un color_hex que no es #RRGGBB;
  · un archivo vacio, de mas de 30 MB, o que no es PNG/JPG por su CONTENIDO;
  · CAMBIAR un packshot que ya existe (declarado o en disco) por otra foto sin --reemplazar.
    Con --reemplazar la foto vieja NO se borra: queda en la misma carpeta como
    `{nombre}_ANTERIOR_{AAAAMMDD}.{ext}` (con un numero si ya habia una de ese dia).

La misma foto con los mismos datos otra vez no cambia nada.

Uso
---
    python Ads/_TOOLS/cargar_packshot.py --producto CLEARSTEM --origen C:/.../foto.png \\
        --marca-impresa "CLEARSTEM" --color-envase "blanco con verde" --formato-envase "frasco 60 capsulas"
    python Ads/_TOOLS/cargar_packshot.py ... --reemplazar --dry-run --json
"""

import argparse
import datetime
import io
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import editar_producto as ep  # noqa: E402
import upsert_fact  # noqa: E402
from cargar_pieza import tipo_por_contenido  # noqa: E402
from editar_producto import Rechazo  # noqa: E402

MB = 1024 * 1024
TOPE = 30 * MB
COLUMNAS = ["producto_key", "packshot", "color_envase", "color_hex", "marca_impresa",
            "formato_envase", "verificado_el", "fuente", "notas"]
FUENTE = "foto subida por el operador desde la app"
EXTENSIONES = (".png", ".jpg", ".jpeg")
LIMITES = {"marca_impresa": 80, "color_envase": 60, "formato_envase": 200, "notas": 400}


def _texto(nombre, valor, obligatorio):
    valor = (valor or "").strip()
    if not valor:
        if obligatorio:
            raise Rechazo(f"falta {nombre.replace('_', ' ')}: se declara, no se adivina.")
        return ""
    if re.search(r"[\r\n\t]", valor):
        raise Rechazo(f"{nombre.replace('_', ' ')} no puede tener saltos de linea.")
    if len(valor) > LIMITES[nombre]:
        raise Rechazo(f"{nombre.replace('_', ' ')} pasa de {LIMITES[nombre]} caracteres.")
    return valor


def _leer(ruta):
    with io.open(ruta, "rb") as fh:
        return fh.read()


def _fila_actual(base, producto):
    for fila in upsert_fact.leer_migrado(os.path.join(base, "PRODUCTOS", "_DIM_ENVASE.csv"), COLUMNAS):
        if fila["producto_key"].strip() == producto:
            return fila
    return None


def _archivo_anterior(destino, hoy):
    """`X_PACKSHOT_ANTERIOR_20260928.png`; si ya existe, `..._2.png`, `..._3.png`."""
    raiz, extension = os.path.splitext(destino)
    candidato = f"{raiz}_ANTERIOR_{hoy.replace('-', '')}{extension}"
    n = 1
    while os.path.exists(candidato):
        n += 1
        candidato = f"{raiz}_ANTERIOR_{hoy.replace('-', '')}_{n}{extension}"
    return candidato


def planear(args):
    base = args.base
    producto = args.producto
    encabezado, filas, indice = ep.buscar_producto(base, producto)
    carpeta_media = (ep.fila_dict(encabezado, filas, indice).get("carpeta_media") or "").strip()
    if not carpeta_media or not os.path.isdir(os.path.join(base, "Ads", carpeta_media)):
        raise Rechazo(f"{producto} no tiene carpeta de media en Ads/: la crea el alta del producto.")

    declarado = {
        "marca_impresa": _texto("marca_impresa", args.marca_impresa, True),
        "color_envase": _texto("color_envase", args.color_envase, True),
        "formato_envase": _texto("formato_envase", args.formato_envase, True),
    }
    color_hex = (args.color_hex or "").strip()
    if color_hex and not re.fullmatch(r"#[0-9A-Fa-f]{6}", color_hex):
        raise Rechazo(f"color_hex «{color_hex}» no es #RRGGBB (por ejemplo #1B4F9C).")
    actual = _fila_actual(base, producto)
    notas = _texto("notas", args.notas, False) or (actual["notas"] if actual else "")

    if not os.path.isfile(args.origen):
        raise Rechazo(f"no encuentro el archivo a cargar ({args.origen}).")
    contenido = _leer(args.origen)
    if not contenido:
        raise Rechazo("la foto esta vacia.")
    if len(contenido) > TOPE:
        raise Rechazo(f"la foto pesa {len(contenido) // MB} MB y se aceptan hasta {TOPE // MB} MB.")
    por_contenido = tipo_por_contenido(contenido[:16])
    if por_contenido not in (".png", ".jpg"):
        raise Rechazo("el archivo no es una foto PNG o JPG (se mira el contenido, no el nombre).")

    hoy = args.hoy or datetime.date.today().isoformat()
    relativa = f"Ads/{carpeta_media}/{producto}_PACKSHOT{por_contenido}"
    destino = os.path.join(base, *relativa.split("/"))

    # Lo que ya hay: el packshot declarado y cualquier `{PK}_PACKSHOT.*` en la carpeta.
    existentes = set()
    if actual and actual["packshot"].strip():
        declarada = os.path.join(base, *actual["packshot"].strip().split("/"))
        if os.path.isfile(declarada):
            existentes.add(os.path.normpath(declarada))
    for extension in EXTENSIONES:
        propio = os.path.join(base, "Ads", carpeta_media, f"{producto}_PACKSHOT{extension}")
        if os.path.isfile(propio):
            existentes.add(os.path.normpath(propio))
    distintos = sorted(e for e in existentes if _leer(e) != contenido)
    if distintos and not args.reemplazar:
        raise Rechazo(
            f"{producto} ya tiene packshot ({os.path.relpath(distintos[0], base).replace(os.sep, '/')}) y es otra "
            "foto. Cambiarlo cambia como sale el producto en todos los anuncios nuevos; si es lo que queres, "
            "repetilo con --reemplazar (la foto vieja queda guardada con fecha).")

    fila = {"producto_key": producto, "packshot": relativa, "color_envase": declarado["color_envase"],
            "color_hex": color_hex, "marca_impresa": declarado["marca_impresa"],
            "formato_envase": declarado["formato_envase"], "verificado_el": hoy, "fuente": FUENTE, "notas": notas}
    misma_fila = bool(actual) and all(
        actual[c] == fila[c] for c in COLUMNAS if c not in ("verificado_el", "fuente"))
    foto_ya_esta = os.path.normpath(destino) in existentes and not distintos
    sin_cambios = misma_fila and foto_ya_esta

    cambios = []
    if not foto_ya_esta:
        cambios.append({"archivo": relativa, "campo": "packshot",
                        "antes": "(no existia)" if not existentes else "otra foto",
                        "despues": f"{len(contenido)} bytes"})
    if not misma_fila:
        cambios.append({"archivo": "PRODUCTOS/_DIM_ENVASE.csv", "campo": "fila",
                        "antes": "(sin fila)" if not actual else "datos anteriores", "despues": "datos declarados"})
    return {
        "producto_key": producto, "packshot": relativa, "url_media": f"{producto}_PACKSHOT{por_contenido}",
        "sin_cambios": sin_cambios, "cambios": cambios, "avisos": [],
        "guardadas": [os.path.relpath(_archivo_anterior(e, hoy), base).replace(os.sep, "/") for e in distintos],
        "_contenido": contenido, "_destino": destino, "_distintos": distintos, "_fila": fila,
        "_escribir_foto": not foto_ya_esta, "_escribir_fila": not misma_fila, "_hoy": hoy,
    }


def aplicar(plan, base):
    """Todo o nada: foto a un .tmp, las viejas se apartan con fecha, se instala la nueva y recien
    ahi el CSV; si el CSV falla se devuelve todo como estaba."""
    destino, temporal = plan["_destino"], plan["_destino"] + ".tmp"
    apartadas = []
    escrita = False
    preexistia = os.path.exists(destino) and os.path.normpath(destino) not in map(os.path.normpath, plan["_distintos"])
    if plan["_escribir_foto"]:
        with io.open(temporal, "wb") as fh:
            fh.write(plan["_contenido"])
    try:
        for vieja in plan["_distintos"]:
            nueva = _archivo_anterior(vieja, plan["_hoy"])
            os.rename(vieja, nueva)
            apartadas.append((vieja, nueva))
        if plan["_escribir_foto"]:
            os.replace(temporal, destino)
            escrita = True
        if plan["_escribir_fila"]:
            upsert_fact.upsert(os.path.join(base, "PRODUCTOS", "_DIM_ENVASE.csv"), COLUMNAS, ("producto_key",),
                               [plan["_fila"]], upsert_fact.respaldos_dir(base, "backups_csv"))
    except Exception:
        if escrita and not preexistia:
            os.remove(destino)
        for vieja, nueva in reversed(apartadas):
            if os.path.exists(nueva):
                os.replace(nueva, vieja)
        raise
    finally:
        if os.path.exists(temporal):
            os.remove(temporal)


def salida_legible(plan, aplicado):
    if plan["sin_cambios"]:
        return f"SIN CAMBIOS: {plan['packshot']} ya es ese packshot con esos datos."
    cabecera = f"{'GUARDADO' if aplicado else 'SE GUARDARIA'}: {plan['packshot']}"
    return "\n".join([cabecera] + ep.lineas_de_cambios(plan)
                     + [f"  foto anterior conservada en {g}" for g in plan["guardadas"]])


def main(argv=None):
    ap = argparse.ArgumentParser(description="Guarda el packshot de un producto y declara su identidad fisica")
    ep.argumentos_comunes(ap)
    ap.add_argument("--origen", required=True, help="la foto que entrega el operador")
    ap.add_argument("--marca-impresa", dest="marca_impresa", default="", help="la marca que se lee en el envase")
    ap.add_argument("--color-envase", dest="color_envase", default="", help="color del envase, en palabras")
    ap.add_argument("--color-hex", dest="color_hex", default="", help="#RRGGBB (opcional)")
    ap.add_argument("--formato-envase", dest="formato_envase", default="", help="que es y como se ve el envase")
    ap.add_argument("--notas", default="", help="opcional")
    ap.add_argument("--reemplazar", action="store_true", help="permite cambiar un packshot ya cargado")
    ap.add_argument("--hoy", default="", help=argparse.SUPPRESS)
    args = ap.parse_args(argv)
    try:
        plan = planear(args)
        aplicado = bool(plan["cambios"]) and not args.dry_run
        if aplicado:
            aplicar(plan, args.base)
    except Rechazo as rechazo:
        if args.json:
            print(json.dumps({"ok": False, "detalle": str(rechazo)}, ensure_ascii=False))
        else:
            print(f"BLOQUEANTE: {rechazo}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(ep.plan_publico(plan, aplicado), ensure_ascii=False, indent=2))
    else:
        print(salida_legible(plan, aplicado))
    return 0


if __name__ == "__main__":
    sys.exit(main())
