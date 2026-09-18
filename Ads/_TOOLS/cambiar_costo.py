#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""cambiar_costo.py — corrige el costo del proveedor de un producto que ya tiene fila.

Dato de DOCTRINA/FLUJO.json F1.congelar_inputs: «COSTO_PROVEEDOR_Q» (costo_q >= 1). Dueno: el
operador. alta_producto.py lo carga al crear la fila; este script es para corregirlo DESPUES,
mientras el producto sigue en F1.congelar_inputs.

Por que solo hasta ahi (invariante 5)
-------------------------------------
«Congelar los inputs antes de arrancar. Si uno cambia a mitad: rerun completo que sobrescribe
los archivos y sube VERSION; nunca un parche parcial.» Cuando el paquete de FASE 1 ya se cerro,
el costo esta repetido en precios, CPA objetivo y break-even (los calculo costear.py y los guardo
etapa-guardar-producto), en el encabezado de los TXT y en el plan. Cambiar solo costo_q los
dejaria contradiciendose. Por eso este script BLOQUEA en cuanto el producto tiene:
  · cifras de costeo en la fila (fila_costeo_q, precio_base_q, cpa_base_q o cpa_be_q), o
  · 1_HACER_MANUAL.txt, o un 2_DATA_PRODUCTO.txt con encabezado de paquete (VERSION · COSTO ...).
Ahi el camino es el rerun completo de fase-1-angulos, que lo hace etapa-guardar-producto.

Que escribe
-----------
  1. costo_q en PRODUCTOS/_DIM_PRODUCTOS.csv.
  2. La linea «costo del pedido . Q<n>» del 2_DATA_PRODUCTO.txt que dejo alta_producto.py.
Y NADA mas: ni precio_base_q, ni cpa_base_q, ni cpa_be_q, ni fila_costeo_q. Esas cifras las
calcula costear.py y las escribe etapa-guardar-producto (un dato, un dueno). La pantalla de
costo las MUESTRA en vivo con `costear.py <costo> --json`, pero no las guarda.

Uso
---
    python Ads/_TOOLS/cambiar_costo.py --producto OVULOS_PURITY --costo 52
    python Ads/_TOOLS/cambiar_costo.py --producto X --costo 52.50 --dry-run --json
"""

import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import editar_producto as ep  # noqa: E402
from editar_producto import Rechazo  # noqa: E402

# Las salidas de costear.py que etapa-guardar-producto escribe en la fila. No las escribe este script.
COLUMNAS_DE_COSTEO = ("fila_costeo_q", "precio_base_q", "cpa_base_q", "cpa_be_q")
RE_LINEA_COSTO = re.compile(r"(costo del pedido \.+ Q)(\S+)")
RE_ENCABEZADO_DE_PAQUETE = re.compile(r"\sCOSTO\s+\S")


def normalizar_costo(crudo):
    costo = str(crudo).strip().replace(",", ".")
    if not re.fullmatch(r"\d+(\.\d+)?", costo) or float(costo) <= 0:
        raise Rechazo(f"el costo «{crudo}» no es un numero positivo. Va del pedido completo, "
                      "en la moneda del mercado del producto.")
    return costo


def mismo_numero(a, b):
    try:
        return float(str(a).replace(",", ".")) == float(str(b).replace(",", "."))
    except ValueError:
        return False


def razones_de_paquete_cerrado(base, fila, slug):
    """Por que ya no se puede cambiar el costo a mano. Lista vacia = todavia se puede."""
    razones = []
    con_cifras = [c for c in COLUMNAS_DE_COSTEO if fila.get(c, "").strip()]
    if con_cifras:
        razones.append("la fila ya tiene cifras de costeo (" + ", ".join(con_cifras) + ")")
    if os.path.isfile(os.path.join(base, "PRODUCTOS", slug, "1_HACER_MANUAL.txt")):
        razones.append("existe PRODUCTOS/%s/1_HACER_MANUAL.txt" % slug)
    ruta_datos = os.path.join(base, "PRODUCTOS", slug, "2_DATA_PRODUCTO.txt")
    texto = ep.leer_texto(ruta_datos)
    if texto is not None and RE_ENCABEZADO_DE_PAQUETE.search(texto.partition("\n")[0]):
        razones.append("el 2_DATA_PRODUCTO.txt ya trae encabezado de paquete (VERSION · COSTO ...)")
    return razones, texto, ruta_datos


def planear(args):
    base = args.base
    costo = normalizar_costo(args.costo)
    encabezado, filas, indice = ep.buscar_producto(base, args.producto)
    fila = ep.fila_dict(encabezado, filas, indice)
    slug = fila["slug_carpeta"].strip()

    razones, texto_datos, ruta_datos = razones_de_paquete_cerrado(base, fila, slug)
    if razones:
        raise Rechazo(
            f"el paquete de {args.producto} ya esta armado ({'; '.join(razones)}): el costo Q"
            f"{fila['costo_q']} esta repetido en precios, CPA objetivo, break-even y encabezados. "
            "Cambiarlo ahora es un rerun completo de fase-1-angulos, que sobrescribe los archivos "
            "y sube VERSION (invariante 5; dueno: etapa-guardar-producto). No se parcha."
        )

    actual = fila["costo_q"].strip()
    if mismo_numero(actual, costo):
        return {"producto_key": args.producto, "costo_q": actual, "sin_cambios": True,
                "cambios": [], "avisos": [], "_escrituras": {}}

    cambios = [{"archivo": "PRODUCTOS/_DIM_PRODUCTOS.csv", "campo": "costo_q",
                "antes": actual, "despues": costo}]
    escrituras = {os.path.join(base, "PRODUCTOS", "_DIM_PRODUCTOS.csv"):
                  ep.csv_con_cambios(encabezado, filas, indice, {"costo_q": costo})}
    avisos = []

    if texto_datos is not None:
        m = RE_LINEA_COSTO.search(texto_datos)
        if m:
            escrituras[ruta_datos] = ep.a_bytes(
                RE_LINEA_COSTO.sub(lambda x: x.group(1) + costo, texto_datos, count=1))
            cambios.append({"archivo": f"PRODUCTOS/{slug}/2_DATA_PRODUCTO.txt",
                            "campo": "costo del pedido", "antes": m.group(2), "despues": costo})
        else:
            avisos.append(f"PRODUCTOS/{slug}/2_DATA_PRODUCTO.txt no trae la linea «costo del pedido»: "
                          "no lo toco. Revisalo (dueno: quien lo escribio).")

    return {
        "producto_key": args.producto,
        "costo_q": costo,
        "sin_cambios": False,
        "cambios": cambios,
        "avisos": avisos,
        "_escrituras": escrituras,
    }


def salida_legible(plan, aplicado):
    if plan["sin_cambios"]:
        cabecera = f"SIN CAMBIOS: {plan['producto_key']} ya tiene el costo {plan['costo_q']}."
    else:
        verbo = "COSTO CAMBIADO" if aplicado else "SE CAMBIARIA EL COSTO"
        cabecera = f"{verbo}: {plan['producto_key']}  ->  {plan['costo_q']}"
    return "\n".join([cabecera] + ep.lineas_de_cambios(plan) + ep.lineas_de_avisos(plan) + [
        "", "SIGUIENTE PASO",
        f"  python Ads/_TOOLS/costear.py {plan['costo_q']}   # precios, CPA y break-even que saldran",
        f"  python Ads/_TOOLS/flujo.py {plan['producto_key']}"])


def main(argv=None):
    ap = argparse.ArgumentParser(description="Corrige el costo de un producto que aun no tiene paquete")
    ep.argumentos_comunes(ap)
    ap.add_argument("--costo", required=True, help="costo del PEDIDO COMPLETO")
    return ep.ejecutar(ap.parse_args(argv), planear, salida_legible)


if __name__ == "__main__":
    sys.exit(main())
