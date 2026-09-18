#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""alta_producto.py — da de alta un producto nuevo con lo que el operador entrega.

Por que existe
--------------
Dar de alta un producto eran cinco pasos a mano, y cada uno tenia su forma de salir mal:
la fila del CSV escrita a mano (invariante 11), la carpeta con otro nombre que el
`slug_carpeta` declarado (invariante 10), la descripcion perdida en el chat, la imagen
suelta en una carpeta cualquiera y, la peor, el packshot SIN DECLARAR: asi fue como
TINNIDROP heredo un frasco verde de otra marca cuando el generador eligio "el primer
archivo alfabetico" (07-sep-2026). Este script hace los cinco de una sola vez, o ninguno.

Que escribe (todo o nada)
-------------------------
  1. La fila en PRODUCTOS/_DIM_PRODUCTOS.csv, con csv.writer real.
  2. La carpeta PRODUCTOS/[SLUG]/ con 2_DATA_PRODUCTO.txt (la descripcion del operador).
  3. La carpeta Ads/MEDIA_[CLAVE]/ con la imagen copiada como [CLAVE]_PACKSHOT.[ext].
  4. La fila en PRODUCTOS/_DIM_ENVASE.csv que DECLARA ese packshot.

Que NO escribe, a proposito
---------------------------
Ni `precio_base_q`, ni `cpa_base_q`, ni `cpa_be_q`, ni `fila_costeo_q`. Esas cifras las
calcula costear.py y las escribe etapa-guardar-producto al cerrar el paquete de FASE 1
(lo declara DOCTRINA/FLUJO.json en F1.paquete). La pantalla de alta MUESTRA la tabla de
costear.py en vivo para que el operador decida, pero el numero se guarda una sola vez y
lo guarda su dueno. Un dato, un dueno.

Uso
---
    python Ads/_TOOLS/alta_producto.py --nombre "Serum Vitamina C" --costo 60 \
        --descripcion-archivo desc.txt --imagen foto.png
    python Ads/_TOOLS/alta_producto.py ... --dry-run --json   # dice que haria, no toca nada

    --clave         producto_key explicita (por defecto se deriva del nombre)
    --cuenta        cuenta_alias de _DIM_CUENTAS.csv (por defecto vacia: la decide F1)
    --moneda/--tasa por defecto GTQ sin tasa (Guatemala)
    --color-envase --color-hex --marca --formato   identidad fisica, si ya se conoce
    --base          raiz alternativa (fixtures de test)
"""

import argparse
import csv
import datetime
import io
import os
import re
import shutil
import sys
import unicodedata

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

BASE_POR_DEFECTO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

EXTENSIONES_IMAGEN = (".jpg", ".jpeg", ".png", ".webp")
MINIMO_DESCRIPCION = 120  # una descripcion de dos lineas no alcanza para investigar nada


class Rechazo(Exception):
    """Lo que falta o no cuadra. Se dice y se detiene; no se asume (invariante 4)."""


# ---------------------------------------------------------------- derivaciones

def clave_desde_nombre(nombre):
    """«Óvulos Purity Hernatura» -> «OVULOS_PURITY_HERNATURA». Sin acentos ni simbolos."""
    plano = unicodedata.normalize("NFKD", nombre).encode("ascii", "ignore").decode("ascii")
    limpio = re.sub(r"[^A-Za-z0-9]+", "_", plano).strip("_").upper()
    return re.sub(r"_+", "_", limpio)


def carpeta_media_de(clave):
    """MEDIA_[CLAVE] sin guiones bajos, como las del portafolio (MEDIA_OVULOSPURITY)."""
    return "MEDIA_" + clave.replace("_", "")


def validar_clave(clave):
    if not re.fullmatch(r"[A-Z][A-Z0-9_]{2,39}", clave or ""):
        raise Rechazo(
            f"producto_key invalida: «{clave}». Va en MAYUSCULAS, empieza con letra, "
            "solo letras, numeros y guion bajo, entre 3 y 40 caracteres."
        )
    return clave


# ------------------------------------------------------------------- lecturas

def leer_csv(ruta):
    with io.open(ruta, encoding="utf-8-sig", newline="") as fh:
        lector = csv.reader(fh)
        filas = list(lector)
    if not filas:
        raise Rechazo(f"{os.path.basename(ruta)} esta vacio: le falta el encabezado.")
    return filas[0], filas[1:]


def escribir_csv(ruta, encabezado, filas):
    """Escritor CSV real, CRLF, como el resto del sistema (invariante 11)."""
    with io.open(ruta, "w", encoding="utf-8", newline="") as fh:
        escritor = csv.writer(fh)
        escritor.writerow(encabezado)
        escritor.writerows(filas)


# --------------------------------------------------------------------- el alta

def planear(base, datos):
    """Valida todo y devuelve el plan. No toca el disco: por eso --dry-run es honesto."""
    clave = validar_clave(datos["clave"])
    productos_csv = os.path.join(base, "PRODUCTOS", "_DIM_PRODUCTOS.csv")
    envase_csv = os.path.join(base, "PRODUCTOS", "_DIM_ENVASE.csv")

    encabezado, filas = leer_csv(productos_csv)
    columna_clave = encabezado.index("producto_key")
    if any(fila[columna_clave].strip() == clave for fila in filas if fila):
        raise Rechazo(
            f"«{clave}» ya existe en _DIM_PRODUCTOS.csv. Un producto = una fila = una carpeta "
            "(invariante 8). Si querés relanzarlo, se edita su fila; no se da de alta de nuevo."
        )

    descripcion = datos["descripcion"].strip()
    if len(descripcion) < MINIMO_DESCRIPCION:
        raise Rechazo(
            f"la descripcion tiene {len(descripcion)} caracteres y se piden al menos "
            f"{MINIMO_DESCRIPCION}. De ahi salen los angulos: ingredientes, dosis, beneficios, "
            "registro sanitario, proveedor y garantia."
        )

    imagen = datos["imagen"]
    if not os.path.isfile(imagen):
        raise Rechazo(f"no encuentro la imagen «{imagen}».")
    extension = os.path.splitext(imagen)[1].lower()
    if extension not in EXTENSIONES_IMAGEN:
        raise Rechazo(
            f"la imagen es «{extension}» y se aceptan {', '.join(EXTENSIONES_IMAGEN)}."
        )

    costo = str(datos["costo"]).strip()
    if not re.fullmatch(r"\d+(\.\d+)?", costo) or float(costo) <= 0:
        raise Rechazo(f"el costo «{costo}» no es un numero positivo. Va en quetzales, del pedido completo.")

    slug = clave
    carpeta_media = carpeta_media_de(clave)
    packshot_rel = f"Ads/{carpeta_media}/{clave}_PACKSHOT{extension}"
    hoy = datos["hoy"] or datetime.date.today().isoformat()

    fila_producto = {
        "producto_key": clave,
        "nombre_display": datos["nombre"].strip(),
        "slug_carpeta": slug,
        "estado": "NUEVO",
        "fase": "",  # la fase se DERIVA (flujo.py); esta columna quedo como bitacora
        "cuenta_alias": datos["cuenta"],
        "cuenta_id": "",
        "page_id": "",
        "moneda": datos["moneda"],
        "tasa": datos["tasa"],
        "costo_q": costo,
        "fila_costeo_q": "",   # lo escribe etapa-guardar-producto con la salida de costear.py
        "precio_base_q": "",
        "cpa_base_q": "",
        "cpa_be_q": "",
        "cpa_be_anterior_q": "",
        "notas": datos["notas"] or f"Alta por alta_producto.py el {hoy}. Insumos del operador en "
                                   f"PRODUCTOS/{slug}/2_DATA_PRODUCTO.txt.",
        "carpeta_videos": slug,
        "carpeta_transcripciones": slug,
        "carpeta_media": carpeta_media,
        "carpetas_extra": "",
        "clave_campana": clave,
        "campaign_id": "",
    }
    faltantes = [c for c in encabezado if c not in fila_producto]
    if faltantes:
        raise Rechazo(
            "_DIM_PRODUCTOS.csv tiene columnas que este script no sabe llenar: "
            + ", ".join(faltantes)
            + ". Actualizalo antes de dar de alta (y su test)."
        )

    encabezado_envase, filas_envase = leer_csv(envase_csv)
    fila_envase = {
        "producto_key": clave,
        "packshot": packshot_rel,
        "color_envase": datos["color_envase"],
        "color_hex": datos["color_hex"],
        "marca_impresa": datos["marca"],
        "formato_envase": datos["formato"],
        "verificado_el": hoy,
        "fuente": "imagen entregada por el operador en el alta del producto",
        "notas": "El packshot se DECLARA, nunca se adivina: esta fila nace con el producto.",
    }
    faltantes_envase = [c for c in encabezado_envase if c not in fila_envase]
    if faltantes_envase:
        raise Rechazo(
            "_DIM_ENVASE.csv tiene columnas que este script no sabe llenar: "
            + ", ".join(faltantes_envase)
        )

    return {
        "producto_key": clave,
        "nombre_display": fila_producto["nombre_display"],
        "carpeta_producto": os.path.join("PRODUCTOS", slug),
        "archivo_datos": os.path.join("PRODUCTOS", slug, "2_DATA_PRODUCTO.txt"),
        "carpeta_media": os.path.join("Ads", carpeta_media),
        "packshot": packshot_rel,
        "carpeta_transcripciones": os.path.join("Ads", "1.2 Transcripcion videos", slug),
        "costo_q": costo,
        "fila_producto": fila_producto,
        "fila_envase": fila_envase,
        "_encabezados": (encabezado, filas, encabezado_envase, filas_envase),
        "_imagen_origen": imagen,
        "_descripcion": descripcion,
        "_hoy": hoy,
    }


CABECERA_DATOS = """\
============================================================
{nombre}   ·   {clave}
2_DATA_PRODUCTO.txt — memoria del producto
============================================================

ALTA
  fecha ............ {hoy}
  costo del pedido . Q{costo}
  packshot ......... {packshot}

  Las cifras de precio, CPA y break-even NO van acá: las calcula
  Ads/_TOOLS/costear.py y las escribe etapa-guardar-producto al
  cerrar el paquete de FASE 1. Un dato, un dueño.

------------------------------------------------------------
DESCRIPCIÓN ENTREGADA POR EL OPERADOR
(de acá salen los ángulos: etapa-1b y etapa-2 la leen)
------------------------------------------------------------
{descripcion}
"""


def aplicar(base, plan):
    """Escribe el alta. Si algo falla a mitad, deshace lo que ya habia hecho."""
    encabezado, filas, encabezado_envase, filas_envase = plan["_encabezados"]
    hechos = []
    try:
        carpeta_producto = os.path.join(base, plan["carpeta_producto"])
        carpeta_media = os.path.join(base, plan["carpeta_media"])
        for carpeta in (carpeta_producto, carpeta_media):
            if not os.path.isdir(carpeta):
                os.makedirs(carpeta)
                hechos.append(("carpeta", carpeta))

        destino_packshot = os.path.join(base, plan["packshot"].replace("/", os.sep))
        shutil.copy2(plan["_imagen_origen"], destino_packshot)
        hechos.append(("archivo", destino_packshot))

        archivo_datos = os.path.join(base, plan["archivo_datos"])
        with io.open(archivo_datos, "w", encoding="utf-8") as fh:
            fh.write(CABECERA_DATOS.format(
                nombre=plan["nombre_display"], clave=plan["producto_key"], hoy=plan["_hoy"],
                costo=plan["costo_q"], packshot=plan["packshot"],
                descripcion=plan["_descripcion"],
            ))
        hechos.append(("archivo", archivo_datos))

        productos_csv = os.path.join(base, "PRODUCTOS", "_DIM_PRODUCTOS.csv")
        escribir_csv(productos_csv, encabezado,
                     filas + [[plan["fila_producto"][c] for c in encabezado]])
        hechos.append(("csv", productos_csv))

        envase_csv = os.path.join(base, "PRODUCTOS", "_DIM_ENVASE.csv")
        escribir_csv(envase_csv, encabezado_envase,
                     filas_envase + [[plan["fila_envase"][c] for c in encabezado_envase]])
        hechos.append(("csv", envase_csv))
    except Exception:
        for tipo, ruta in reversed(hechos):
            try:
                if tipo == "archivo":
                    os.remove(ruta)
                elif tipo == "carpeta":
                    os.rmdir(ruta)
            except OSError:
                pass
        # Los CSV se reescriben enteros: si el primero quedo escrito y el segundo fallo,
        # se restauran desde lo que se leyo al planear.
        for ruta, cab, fs in ((os.path.join(base, "PRODUCTOS", "_DIM_PRODUCTOS.csv"), encabezado, filas),
                              (os.path.join(base, "PRODUCTOS", "_DIM_ENVASE.csv"), encabezado_envase, filas_envase)):
            if any(h[1] == ruta for h in hechos):
                escribir_csv(ruta, cab, fs)
        raise
    return plan


def salida_legible(plan, aplicado):
    verbo = "CREADO" if aplicado else "SE CREARIA"
    lineas = [
        f"{verbo}: {plan['nombre_display']}  ·  {plan['producto_key']}",
        f"  fila en PRODUCTOS/_DIM_PRODUCTOS.csv ...... estado NUEVO, costo Q{plan['costo_q']}",
        f"  fila en PRODUCTOS/_DIM_ENVASE.csv ......... packshot declarado",
        f"  {plan['archivo_datos']}",
        f"  {plan['packshot']}",
        "",
        "SIGUIENTE PASO",
        f"  python Ads/_TOOLS/flujo.py {plan['producto_key']}",
        f"  Para la FASE 1 con videos: dejá las transcripciones en {plan['carpeta_transcripciones']}/",
    ]
    return "\n".join(lineas)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Da de alta un producto nuevo")
    ap.add_argument("--nombre", required=True)
    ap.add_argument("--costo", required=True, help="costo del PEDIDO COMPLETO en quetzales")
    ap.add_argument("--descripcion-archivo", required=True, help="TXT con la descripcion extensa")
    ap.add_argument("--imagen", required=True, help="foto limpia del producto (el packshot)")
    ap.add_argument("--clave", default=None)
    ap.add_argument("--cuenta", default="")
    ap.add_argument("--moneda", default="GTQ")
    ap.add_argument("--tasa", default="")
    ap.add_argument("--color-envase", default="")
    ap.add_argument("--color-hex", default="")
    ap.add_argument("--marca", default="")
    ap.add_argument("--formato", default="")
    ap.add_argument("--notas", default="")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--base", default=BASE_POR_DEFECTO)
    ap.add_argument("--hoy", default=None, help="fecha de alta (para tests)")
    args = ap.parse_args(argv)

    try:
        with io.open(args.descripcion_archivo, encoding="utf-8") as fh:
            descripcion = fh.read()
    except OSError as error:
        print(f"BLOQUEANTE: no pude leer la descripcion: {error}", file=sys.stderr)
        return 1

    datos = {
        "nombre": args.nombre,
        "clave": args.clave or clave_desde_nombre(args.nombre),
        "costo": args.costo,
        "descripcion": descripcion,
        "imagen": args.imagen,
        "cuenta": args.cuenta,
        "moneda": args.moneda,
        "tasa": args.tasa,
        "color_envase": args.color_envase,
        "color_hex": args.color_hex,
        "marca": args.marca,
        "formato": args.formato,
        "notas": args.notas,
        "hoy": args.hoy,
    }

    try:
        plan = planear(args.base, datos)
        if not args.dry_run:
            aplicar(args.base, plan)
    except Rechazo as rechazo:
        if args.json:
            import json
            print(json.dumps({"ok": False, "detalle": str(rechazo)}, ensure_ascii=False))
        else:
            print(f"BLOQUEANTE: {rechazo}", file=sys.stderr)
        return 1

    if args.json:
        import json
        publico = {k: v for k, v in plan.items() if not k.startswith("_")}
        publico["ok"] = True
        publico["aplicado"] = not args.dry_run
        print(json.dumps(publico, ensure_ascii=False, indent=2))
    else:
        print(salida_legible(plan, not args.dry_run))
    return 0


if __name__ == "__main__":
    sys.exit(main())
