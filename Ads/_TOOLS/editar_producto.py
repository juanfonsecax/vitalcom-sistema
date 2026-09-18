#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""editar_producto.py — base comun de los escritores que completan o corrigen la fila de un
producto que YA existe en _DIM_PRODUCTOS.csv.

No se ejecuta solo. La usan tres escritores, cada uno dueno de UN dato:

    cargar_cuenta.py    cuenta_alias + cuenta_id   (de _DIM_CUENTAS.csv)
    cargar_page_id.py   page_id de la FanPage
    cambiar_costo.py    costo_q, antes de cerrar el paquete de FASE 1

Por que existe
--------------
alta_producto.py crea la fila; nada la completaba despues. Esos tres datos los pide
DOCTRINA/FLUJO.json (F1.congelar_inputs y F1.publicar) y hasta hoy se cargaban editando el CSV
a mano, que es lo que prohibe la invariante 11. Lo que comparten es lo que hace peligroso ese
CSV: reescribirlo entero sin perder una coma, y que el mismo dato vive tambien en el
ENCABEZADO de los TXT del producto, donde el gate de reconciliacion
(verificar_producto.py, invariante 9) lo compara contra el CSV. Un escritor que solo tocara el
CSV dejaria el TXT "viejo" y romperia ese gate en el primer uso.

Reglas de todo escritor de esta familia
---------------------------------------
  · TODO O NADA: valida primero (planear) y solo despues escribe. --dry-run no toca el disco.
  · Si la escritura falla a mitad, se restauran los archivos como estaban.
  · Bloquea con exit 1 y dice quien produce lo que falta; nunca asume (invariante 4).
  · Un dato, un dueno: no escribe cifras de costeo (las calcula costear.py y las guarda
    etapa-guardar-producto) ni la fase (la deriva flujo.py).
  · --json: la salida que consume la app (contrato en `plan_publico`).
"""

import csv
import io
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from alta_producto import BASE_POR_DEFECTO, Rechazo, leer_csv  # noqa: E402,F401

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# Los tres archivos que verificar_producto.py lee. Solo su PRIMERA linea (el encabezado con
# COSTO / page_id / campaign_id) se compara contra el CSV.
ARCHIVOS_DEL_PAQUETE = ("1_HACER_MANUAL.txt", "2_DATA_PRODUCTO.txt", "3_CAMPAÑA_META.txt")

# Lo que verificar_producto.py trata como "todavia no hay dato".
VALORES_PENDIENTES = ("", "PENDIENTE", "SIN_MCP", "N/A", "-")


def es_pendiente(valor):
    v = (valor or "").strip().upper()
    return v in VALORES_PENDIENTES or v.startswith("PENDIENTE")


# ------------------------------------------------------------------ la fila

def buscar_producto(base, clave):
    """(encabezado, filas, indice) de la fila del producto. Rechaza si no existe."""
    ruta = os.path.join(base, "PRODUCTOS", "_DIM_PRODUCTOS.csv")
    encabezado, filas = leer_csv(ruta)
    columna = encabezado.index("producto_key")
    for indice, fila in enumerate(filas):
        if fila and fila[columna].strip() == clave:
            if len(fila) != len(encabezado):
                raise Rechazo(
                    f"la fila de «{clave}» tiene {len(fila)} campos y el encabezado de "
                    f"_DIM_PRODUCTOS.csv {len(encabezado)}: se arregla primero (invariante 11)."
                )
            return encabezado, filas, indice
    raise Rechazo(
        f"«{clave}» no tiene fila en _DIM_PRODUCTOS.csv. Un producto nuevo se da de alta con "
        "alta_producto.py; este script solo completa filas que ya existen."
    )


def fila_dict(encabezado, filas, indice):
    return dict(zip(encabezado, filas[indice]))


def csv_con_cambios(encabezado, filas, indice, cambios):
    """Los bytes del CSV con `cambios` ({columna: valor}) aplicados a UNA fila. CRLF, como el
    resto del sistema; el resto de filas pasa intacto."""
    faltan = [c for c in cambios if c not in encabezado]
    if faltan:
        raise Rechazo(f"_DIM_PRODUCTOS.csv ya no tiene la columna {', '.join(faltan)}: hay que "
                      "actualizar este escritor (y su test) antes de usarlo.")
    nuevas = [list(f) for f in filas]
    for columna, valor in cambios.items():
        nuevas[indice][encabezado.index(columna)] = valor
    salida = io.StringIO(newline="")
    escritor = csv.writer(salida)
    escritor.writerow(encabezado)
    escritor.writerows(nuevas)
    return salida.getvalue().encode("utf-8")


# ------------------------------------------------------------- los TXT

def leer_texto(ruta):
    """El texto del archivo, o None si no existe. Estricto: un TXT que no es UTF-8 se dice,
    no se reescribe a ciegas."""
    if not os.path.isfile(ruta):
        return None
    with io.open(ruta, "rb") as fh:
        crudo = fh.read()
    try:
        return crudo.decode("utf-8")
    except UnicodeDecodeError:
        raise Rechazo(f"«{os.path.basename(ruta)}» no es UTF-8: no lo reescribo a ciegas.")


def archivos_del_paquete(base, slug):
    """[(ruta_relativa, ruta_absoluta, texto)] de los TXT del producto que existen."""
    encontrados = []
    for nombre in ARCHIVOS_DEL_PAQUETE:
        relativa = os.path.join("PRODUCTOS", slug, nombre)
        absoluta = os.path.join(base, relativa)
        texto = leer_texto(absoluta)
        if texto is not None:
            encontrados.append((relativa.replace(os.sep, "/"), absoluta, texto))
    return encontrados


def editar_primera_linea(texto, editar):
    """Aplica `editar(linea)` a la primera linea, sin tocar el fin de linea ni el resto."""
    cabeza, separador, resto = texto.partition("\n")
    return editar(cabeza) + separador + resto


# --------------------------------------------------------------- escribir

def a_bytes(texto):
    return texto.encode("utf-8")


def aplicar_escrituras(escrituras):
    """Escribe {ruta: bytes} todo o nada: si una falla, las que ya se escribieron vuelven a
    como estaban. Cada archivo se escribe a un temporal y se reemplaza de una vez."""
    originales = {}
    try:
        for ruta, contenido in escrituras.items():
            originales[ruta] = None
            if os.path.isfile(ruta):
                with io.open(ruta, "rb") as fh:
                    originales[ruta] = fh.read()
            os.makedirs(os.path.dirname(ruta), exist_ok=True)
            temporal = ruta + ".tmp"
            with io.open(temporal, "wb") as fh:
                fh.write(contenido)
            os.replace(temporal, ruta)
    except Exception:
        for ruta, antes in originales.items():
            try:
                if antes is None:
                    if os.path.isfile(ruta):
                        os.remove(ruta)
                else:
                    with io.open(ruta, "wb") as fh:
                        fh.write(antes)
            except OSError:
                pass
            try:
                os.remove(ruta + ".tmp")
            except OSError:
                pass
        raise


# ------------------------------------------------------------------ la CLI

def argumentos_comunes(ap):
    ap.add_argument("--producto", required=True, help="producto_key de _DIM_PRODUCTOS.csv")
    ap.add_argument("--dry-run", action="store_true", help="dice que haria y no toca nada")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--base", default=BASE_POR_DEFECTO, help="raiz alternativa (tests)")


def plan_publico(plan, aplicado):
    """El contrato --json: ok, aplicado, producto_key, sin_cambios, cambios, avisos + lo propio."""
    publico = {k: v for k, v in plan.items() if not k.startswith("_")}
    publico["ok"] = True
    publico["aplicado"] = aplicado
    return publico


def ejecutar(args, planear, salida_legible):
    """El ciclo de todo escritor: planear (valida, no escribe) -> aplicar salvo --dry-run -> salida.
    `planear(args)` devuelve un dict con `_escrituras` ({ruta: bytes}) y los campos publicos."""
    try:
        plan = planear(args)
        aplicado = bool(plan["_escrituras"]) and not args.dry_run
        if aplicado:
            aplicar_escrituras(plan["_escrituras"])
    except Rechazo as rechazo:
        if args.json:
            print(json.dumps({"ok": False, "detalle": str(rechazo)}, ensure_ascii=False))
        else:
            print(f"BLOQUEANTE: {rechazo}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(plan_publico(plan, aplicado), ensure_ascii=False, indent=2))
    else:
        print(salida_legible(plan, aplicado))
    return 0


def lineas_de_cambios(plan):
    return [f"  {c['archivo']}  ·  {c['campo']}: «{c['antes']}» -> «{c['despues']}»"
            for c in plan["cambios"]]


def lineas_de_avisos(plan):
    if not plan["avisos"]:
        return []
    return ["", "AVISOS"] + [f"  · {a}" for a in plan["avisos"]]
