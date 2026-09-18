#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""cargar_page_id.py — carga el page_id de la FanPage de un producto que ya tiene fila.

Dato de DOCTRINA/FLUJO.json F1.publicar: «page_id de la FanPage». Dueno del dato: etapa-fanpage
(decide QUE pagina le toca al producto) + el operador (que es quien tiene el id en Meta). Este
script no elige la pagina: guarda la que el operador entrega.

Que escribe
-----------
  1. La columna page_id de la fila del producto en PRODUCTOS/_DIM_PRODUCTOS.csv.
  2. El campo `page_id` del ENCABEZADO (primera linea) de 1_HACER_MANUAL.txt, 2_DATA_PRODUCTO.txt
     y 3_CAMPAÑA_META.txt, si el producto ya los tiene. No es capricho: verificar_producto.py
     (invariante 9) compara ese campo contra el CSV, y un encabezado que dice «page_id PENDIENTE»
     con el CSV ya cargado es un fallo del gate («el operador pautaria a ciegas»). Solo se
     reemplaza el valor de ese campo; el resto del archivo no se toca.

Que bloquea (exit 1)
--------------------
  · un producto sin fila (eso es alta_producto.py);
  · un page_id que no es numerico (los de Meta son de 10 a 20 digitos): «PENDIENTE» es
    justamente lo que este script viene a quitar;
  · cambiar un page_id ya cargado sin --reemplazar.

Lo que solo avisa
-----------------
Un _PLAN.json con OTRO page_id: gen_publicacion.py da prioridad al del plan sobre el del producto.

Uso
---
    python Ads/_TOOLS/cargar_page_id.py --producto CLEARSTEM --page-id 823825257480758
    python Ads/_TOOLS/cargar_page_id.py --producto X --page-id 123... --dry-run --json
"""

import argparse
import io
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import editar_producto as ep  # noqa: E402
from editar_producto import Rechazo  # noqa: E402

RE_PAGE_ID = re.compile(r"\d{10,20}")
# El valor del campo `page_id` de un encabezado: hasta el siguiente « · », la doble raya o el fin.
RE_CAMPO_PAGE_ID = re.compile(r"(\bpage_id\s+)(.*?)(?=\s·\s|\s*═|\s*\r?$)")


def valor_en_encabezado(texto):
    m = RE_CAMPO_PAGE_ID.search(texto.partition("\n")[0])
    return m.group(2) if m else None


def planear(args):
    base = args.base
    page_id = str(args.page_id).strip()
    if not RE_PAGE_ID.fullmatch(page_id):
        raise Rechazo(
            f"el page_id «{page_id}» no es un id de Meta: son solo digitos (de 10 a 20). Se ve en "
            "la URL de la pagina o en Configuracion > Informacion de la pagina."
        )
    encabezado, filas, indice = ep.buscar_producto(base, args.producto)
    fila = ep.fila_dict(encabezado, filas, indice)
    slug = fila["slug_carpeta"].strip()

    actual = fila["page_id"].strip()
    tiene_real = not ep.es_pendiente(actual)
    if tiene_real and actual != page_id and not args.reemplazar:
        raise Rechazo(
            f"{args.producto} ya tiene el page_id {actual}. Cambiarlo es cambiar la FanPage con "
            "la que se pauta; si es lo que queres (o el anterior estaba mal), repetilo con --reemplazar."
        )

    cambios, escrituras, avisos = [], {}, []
    if actual != page_id:
        cambios.append({"archivo": "PRODUCTOS/_DIM_PRODUCTOS.csv", "campo": "page_id",
                        "antes": actual, "despues": page_id})
        escrituras[os.path.join(base, "PRODUCTOS", "_DIM_PRODUCTOS.csv")] = \
            ep.csv_con_cambios(encabezado, filas, indice, {"page_id": page_id})

    for relativa, absoluta, texto in ep.archivos_del_paquete(base, slug):
        antes = valor_en_encabezado(texto)
        # Como el gate: un encabezado que ya CONTIENE el id esta bien («823... (Astrid García)»).
        if antes is None or page_id in antes:
            continue
        nuevo = ep.editar_primera_linea(
            texto, lambda linea: RE_CAMPO_PAGE_ID.sub(lambda m: m.group(1) + page_id, linea, count=1))
        escrituras[absoluta] = ep.a_bytes(nuevo)
        cambios.append({"archivo": relativa, "campo": "page_id (encabezado)",
                        "antes": antes, "despues": page_id})

    ruta_plan = os.path.join(base, "PRODUCTOS", slug, "_PLAN.json")
    if os.path.isfile(ruta_plan):
        try:
            with io.open(ruta_plan, encoding="utf-8") as fh:
                plan = json.load(fh)
            del_plan = [str(v).strip() for v in (plan.get("page_id"), (plan.get("pagina") or {}).get("page_id"))
                        if v]
            if any(v != page_id for v in del_plan):
                avisos.append(f"PRODUCTOS/{slug}/_PLAN.json trae el page_id {', '.join(del_plan)}: "
                              "gen_publicacion.py da prioridad al del plan. Se corrige en el plan "
                              "(dueno: etapa-6) o se quita de ahi.")
        except (OSError, ValueError):
            avisos.append(f"no pude leer PRODUCTOS/{slug}/_PLAN.json para compararlo (dueno: etapa-6).")

    return {
        "producto_key": args.producto,
        "page_id": page_id,
        "sin_cambios": not cambios,
        "cambios": cambios,
        "avisos": avisos,
        "_escrituras": escrituras,
    }


def salida_legible(plan, aplicado):
    if plan["sin_cambios"]:
        cabecera = f"SIN CAMBIOS: {plan['producto_key']} ya tiene el page_id {plan['page_id']}."
    else:
        verbo = "CARGADO" if aplicado else "SE CARGARIA"
        cabecera = f"{verbo}: {plan['producto_key']}  ->  page_id {plan['page_id']}"
    return "\n".join([cabecera] + ep.lineas_de_cambios(plan) + ep.lineas_de_avisos(plan)
                     + ["", "SIGUIENTE PASO", f"  python Ads/_TOOLS/verificar_producto.py {plan['producto_key']}"])


def main(argv=None):
    ap = argparse.ArgumentParser(description="Carga el page_id de la FanPage de un producto con fila")
    ep.argumentos_comunes(ap)
    ap.add_argument("--page-id", required=True, help="id numerico de la FanPage en Meta")
    ap.add_argument("--reemplazar", action="store_true",
                    help="permite cambiar un page_id que el producto ya tiene")
    return ep.ejecutar(ap.parse_args(argv), planear, salida_legible)


if __name__ == "__main__":
    sys.exit(main())
