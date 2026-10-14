#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""datos_producto.py — «datos para arrancar»: que le falta a un producto para que el sistema pueda
trabajar con el. SOLO LECTURA: no escribe nada, nunca (contrato de CLI, DATA_PLAYBOOK §7).

Un dato, un dueno: este script no guarda ni calcula ninguno de los datos que revisa; solo lee a sus
duenos y dice si esta o falta, con la frase para el operador y la accion del manifiesto que lo carga
cuando existe una.

Que revisa (cada uno con el mismo criterio que el bloqueo que hoy lo exige)
---------------------------------------------------------------------------
  packshot         PRODUCTOS/_DIM_ENVASE.csv: fila con packshot + marca y color declarados, y el archivo
                   existe (armar_prompts_fase2.buscar_foto_producto).           accion producto.cargar_packshot
  costo_q          _DIM_PRODUCTOS.csv: numero positivo.                          accion producto.cambiar_costo
  precio           _DIM_PRECIOS.csv: al menos una fila con estado == ACTIVO      (armar_prompts_fase2.leer_escalera)
  registro_sanitario  el mercado del producto exige un numero de registro (MSPAS/FDA en GT, INVIMA en CO) y
                   DOCTRINA/PLANTILLAS_DEFAULTS_OPERADOR.md lo declara (mercado.registro_de_perfil). No se juzga
                   si el producto no declara un mercado valido. No tiene accion escritora: el operador
                   entrega el numero y Claude lo deja en esa fila de la doctrina.
  page_id          _DIM_PRODUCTOS.csv: ni vacio ni PENDIENTE/SIN_MCP/N/A/-       accion producto.cargar_page_id
  cuenta           _DIM_PRODUCTOS.csv cuenta_alias: no pendiente, y si no es EXTERNA, existe en _DIM_CUENTAS.csv y
                   esta ACTIVE. EXTERNA es un valor legitimo (la cuenta es de un tercero y se publica a mano):
                   no se marca.                                                  accion producto.cargar_cuenta
  perfil_creativo  solo en FASE 2: PRODUCTOS/{slug}/_PERFIL_CREATIVO.json declara el angulo_key del #1 de
                   `angulos_ganadores` (flujo.py) y trae sus textos.              lo prepara Claude
  referencia_f1    solo en FASE 1: fila del producto en _DIM_REFERENCIA_F1.csv.  lo elige Claude

La fase y el #1 salen de `flujo.py <pk> --json` (su dueno). Con --sin-flujo o si flujo.py no responde, los
dos datos condicionales no se juzgan y se dice en `avisos`.

Uso
---
    python Ads/_TOOLS/datos_producto.py CLEARSTEM            # resumen legible
    python Ads/_TOOLS/datos_producto.py CLEARSTEM --json
    python Ads/_TOOLS/datos_producto.py --todo [--json] [--sin-flujo]
"""

import argparse
import csv
import io
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import editar_producto as ep  # noqa: E402
import mercado as mc  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

BASE_POR_DEFECTO = ep.BASE_POR_DEFECTO
SIN_ACCION = None


def _leer_csv(base, nombre):
    ruta = os.path.join(base, "PRODUCTOS", nombre)
    if not os.path.isfile(ruta):
        return []
    with io.open(ruta, encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def _corto(alias):
    return (alias or "").replace(" ", "").upper()


def _item(clave, rotulo, ok, detalle, como="", accion=SIN_ACCION):
    return {"clave": clave, "rotulo": rotulo, "estado": "ok" if ok else "falta", "detalle": detalle,
            "como_resolver": "" if ok else como, "accion": None if ok else accion}


def _numero_positivo(texto):
    try:
        return float(str(texto).strip().replace(",", ".")) > 0
    except ValueError:
        return False


# ---------------------------------------------------------------- cada dato

def revisar_packshot(base, fila):
    pk = fila["producto_key"]
    como = ("Subí la foto del producto tal como se ve en la mano y decinos la marca que lleva impresa, el color "
            "del envase y qué tipo de envase es. La IA la usa para que el producto salga igual en todos los anuncios.")
    envase = next((f for f in _leer_csv(base, "_DIM_ENVASE.csv") if (f.get("producto_key") or "").strip() == pk), None)
    if not envase or not (envase.get("packshot") or "").strip():
        return _item("packshot", "Foto del producto (packshot)", False, "No hay foto declarada.", como,
                     "producto.cargar_packshot"), None
    archivo = envase["packshot"].strip()
    if not os.path.isfile(os.path.join(base, *archivo.split("/"))):
        return _item("packshot", "Foto del producto (packshot)", False,
                     f"La fila declara {archivo} pero el archivo no está.", como, "producto.cargar_packshot"), None
    if not (envase.get("marca_impresa") or "").strip() or not (envase.get("color_envase") or "").strip():
        return _item("packshot", "Foto del producto (packshot)", False,
                     "La foto está, pero falta declarar la marca impresa o el color del envase.", como,
                     "producto.cargar_packshot"), None
    publico = {"archivo": os.path.basename(archivo), "marca_impresa": envase["marca_impresa"].strip(),
               "color_envase": envase["color_envase"].strip(), "color_hex": (envase.get("color_hex") or "").strip(),
               "formato_envase": (envase.get("formato_envase") or "").strip(),
               "verificado_el": (envase.get("verificado_el") or "").strip()}
    return _item("packshot", "Foto del producto (packshot)", True, f"{publico['marca_impresa']} · {publico['color_envase']}"), publico


def _perfil_o_none(base, fila):
    """El perfil del mercado del producto, o None si no declara uno valido (ese faltante lo reporta
    `mercado.py`; aca solo decide como se escriben los montos)."""
    try:
        return mc.perfil_de_fila(fila, base)
    except mc.MercadoError:
        return None


def _monto(valor, perfil):
    """El monto en la notacion de la moneda del mercado; sin mercado valido, el numero pelado."""
    valor = float(valor)
    decimales = 0 if valor == int(valor) else 2
    return mc.formatear_monto(valor, perfil, decimales) if perfil else ("%.*f" % (decimales, valor))


def _en_moneda(perfil):
    return f"en {perfil['moneda']}" if perfil else "en la moneda de su mercado"


def revisar_costo(base, fila):
    perfil = _perfil_o_none(base, fila)
    ok = _numero_positivo(fila.get("costo_q"))
    return _item("costo_q", "Costo del producto", ok, _monto(fila["costo_q"], perfil) if ok else "No hay un costo válido.",
                 "Decinos cuánto te cuesta el producto (lo que pagás al proveedor por el pedido completo, "
                 f"{_en_moneda(perfil)}).",
                 "producto.cambiar_costo")


def revisar_precio(base, fila):
    pk = fila["producto_key"]
    perfil = _perfil_o_none(base, fila)
    activas = sorted((f for f in _leer_csv(base, "_DIM_PRECIOS.csv")
                      if (f.get("producto_key") or "").strip() == pk and (f.get("estado") or "").strip() == "ACTIVO"
                      and _numero_positivo(f.get("precio_q"))), key=lambda f: int(f.get("unidades") or 0))
    if activas:
        return _item("precio", "Precio de venta", True, " · ".join(
            f"{f['etiqueta'] or f['unidades'] + 'x'} {_monto(round(float(f['precio_q'])), perfil)}" for f in activas))
    return _item("precio", "Precio de venta", False, "No hay una escalera de precios activa.",
                 f"Pasale a Claude a cuánto vendés 1, 2 y 3 unidades ({_en_moneda(perfil)}) y él la deja cargada.")


def revisar_registro(base, fila):
    """El numero de registro sanitario del mercado del producto, o None si el producto no declara un mercado
    valido (eso lo dice `mercado.py`, no este dato). Con EN_TRAMITE queda ok: la pieza sale sin sello."""
    try:
        perfil = mc.perfil_de_fila(fila, base)
    except mc.MercadoError:
        return None
    rotulo = "Registro sanitario"
    try:
        reg = mc.registro_de_producto(fila["producto_key"], base)
    except mc.RegistroFaltante as falta:
        nombre = ", ".join(falta.claves) or falta.regulador or "?"
        return _item("registro_sanitario", rotulo, False,
                     f"Falta el número de registro {nombre} de {perfil['pais']}.",
                     f"Pasale a Claude el número de registro {nombre}: él lo deja cargado. Sin ese número no se "
                     "generan los prompts (no se inventa uno ni se usa el de otro país).")
    except mc.MercadoError:
        return None
    if reg.get("en_tramite"):
        return _item("registro_sanitario", rotulo, True,
                      "En trámite: las piezas salen sin sello ni número de registro.")
    return _item("registro_sanitario", rotulo, True, reg["texto"])


def revisar_page_id(fila):
    ok = not ep.es_pendiente(fila.get("page_id"))
    return _item("page_id", "Página de Facebook", ok, f"page_id {fila['page_id'].strip()}" if ok else "Falta el page_id.",
                 "Pegá el número (page_id) de la página de Facebook con la que se va a publicar.", "producto.cargar_page_id")


def revisar_cuenta(base, fila):
    alias = (fila.get("cuenta_alias") or "").strip()
    como = "Elegí la cuenta publicitaria donde se va a pautar este producto."
    if ep.es_pendiente(alias):
        return _item("cuenta", "Cuenta publicitaria", False, "No hay cuenta asignada.", como, "producto.cargar_cuenta")
    if _corto(alias) == "EXTERNA":
        return _item("cuenta", "Cuenta publicitaria", True, "Cuenta externa: se publica a mano.")
    cuenta = next((c for c in _leer_csv(base, "_DIM_CUENTAS.csv") if _corto(c.get("cuenta_alias")) == _corto(alias)), None)
    if not cuenta:
        return _item("cuenta", "Cuenta publicitaria", False, f"«{alias}» no está en la lista de cuentas.", como,
                     "producto.cargar_cuenta")
    if (cuenta.get("estado_cuenta") or "").strip() != "ACTIVE":
        return _item("cuenta", "Cuenta publicitaria", False, f"{cuenta['cuenta_alias']} está retirada.", como,
                     "producto.cargar_cuenta")
    return _item("cuenta", "Cuenta publicitaria", True, cuenta["cuenta_alias"])


def revisar_perfil(base, fila, angulo_1):
    ruta = os.path.join(base, "PRODUCTOS", (fila.get("slug_carpeta") or "").strip() or fila["producto_key"],
                        "_PERFIL_CREATIVO.json")
    como = (f"Claude lo prepara para el ángulo {angulo_1} con la skill de conceptos: no necesitás aportar nada, "
            "solo pedirle que lo arme antes de generar los prompts.")
    rotulo = "Perfil creativo del ángulo #1"
    if not os.path.isfile(ruta):
        return _item("perfil_creativo", rotulo, False, f"No hay perfil creativo del ángulo {angulo_1}.", como)
    try:
        with io.open(ruta, encoding="utf-8") as fh:
            doc = json.load(fh)
    except (OSError, ValueError):
        return _item("perfil_creativo", rotulo, False, "El perfil creativo no se puede leer.", como)
    if not isinstance(doc, dict):
        return _item("perfil_creativo", rotulo, False, "El perfil creativo no se puede leer.", como)
    por_angulo = doc.get("textos_por_angulo")
    if isinstance(por_angulo, dict):
        # perfil_creativo/2: cada angulo tiene su entrada de textos.
        if not isinstance(por_angulo.get(angulo_1), dict):
            hay = ", ".join(sorted(por_angulo)) or "(ninguno)"
            return _item("perfil_creativo", rotulo, False,
                         f"El perfil no trae textos del ángulo #1 ({angulo_1}); tiene: {hay}.", como)
        textos = por_angulo[angulo_1].get("textos") or {}
    else:
        declarado = (doc.get("angulo_key") or "").strip()
        if declarado != angulo_1:
            return _item("perfil_creativo", rotulo, False,
                         f"El perfil que hay es del ángulo {declarado or '(sin declarar)'}, no del #1 ({angulo_1}).", como)
        textos = doc.get("textos") or {}
    from armar_prompts_fase2 import TEXTOS_REQUERIDOS
    sin = [k for k in TEXTOS_REQUERIDOS if not textos.get(k)]
    if not isinstance(doc.get("perfil"), dict) or sin:
        return _item("perfil_creativo", rotulo, False, "Al perfil le faltan textos: " + (", ".join(sin) or "el bloque perfil") + ".", como)
    return _item("perfil_creativo", rotulo, True, angulo_1)


def revisar_referencia(base, fila):
    pk = fila["producto_key"]
    hay = next((f for f in _leer_csv(base, "_DIM_REFERENCIA_F1.csv") if (f.get("producto_key") or "").strip() == pk
                and (f.get("referencia") or "").strip()), None)
    return _item("referencia_f1", "Imagen de referencia de FASE 1", bool(hay),
                 hay["referencia"] if hay else "Todavía no se eligió.",
                 "Claude elige la imagen de referencia entre las del banco: no necesitás aportar nada.")


# ------------------------------------------------------------- el conjunto

def revisar_producto(base, fila, flujo=None):
    """El dict de un producto. `flujo` = {fase, angulos_ganadores} de flujo.py, o None si no se consultó."""
    avisos = []
    packshot_item, packshot = revisar_packshot(base, fila)
    items = [packshot_item, revisar_costo(base, fila), revisar_precio(base, fila), revisar_page_id(fila),
             revisar_cuenta(base, fila)]
    registro = revisar_registro(base, fila)
    if registro:
        items.append(registro)
    fase = (flujo or {}).get("fase")
    ganadores = (flujo or {}).get("angulos_ganadores") or []
    if flujo is None:
        avisos.append("No se consultó la fase del producto: el perfil creativo y la referencia de FASE 1 no se juzgaron.")
    elif fase == "F2" and ganadores:
        items.append(revisar_perfil(base, fila, ganadores[0]))
    elif fase == "F1":
        items.append(revisar_referencia(base, fila))
    faltan = [i for i in items if i["estado"] == "falta"]
    return {"producto_key": fila["producto_key"], "nombre": fila.get("nombre_display", ""), "fase": fase,
            "angulo_1": ganadores[0] if fase == "F2" and ganadores else None,
            "completo": not faltan, "faltan": len(faltan), "packshot": packshot, "items": items, "avisos": avisos}


def flujo_de(base, producto_key):
    """{fase, angulos_ganadores} según `flujo.py <pk> --json` (solo lectura), o None si no responde."""
    try:
        completado = subprocess.run(
            [sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "flujo.py"), producto_key,
             "--json", "--silencioso", "--base", base],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
        datos = json.loads(completado.stdout)
    except (OSError, ValueError, subprocess.SubprocessError):
        return None
    return {"fase": datos.get("fase"), "angulos_ganadores": datos.get("angulos_ganadores") or []}


def revisar(base, producto=None, con_flujo=True):
    filas = _leer_csv(base, "_DIM_PRODUCTOS.csv")
    if producto:
        filas = [f for f in filas if (f.get("producto_key") or "").strip() == producto]
        if not filas:
            raise ep.Rechazo(f"«{producto}» no tiene fila en _DIM_PRODUCTOS.csv.")
    return [revisar_producto(base, f, flujo_de(base, f["producto_key"]) if con_flujo else None) for f in filas]


def legible(resultados):
    lineas = []
    for r in resultados:
        cabecera = "completo" if r["completo"] else f"faltan {r['faltan']}"
        lineas.append(f"{r['producto_key']} ({r['fase'] or 'fase sin consultar'}): {cabecera}")
        lineas += [f"   - {i['rotulo']}: {i['detalle']}" + (f" [{i['accion']}]" if i["accion"] else "")
                   for i in r["items"] if i["estado"] == "falta"]
        lineas += [f"   * {a}" for a in r["avisos"]]
    return "\n".join(lineas)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Datos para arrancar de un producto (solo lectura)")
    ap.add_argument("producto", nargs="?", help="producto_key; sin él, usar --todo")
    ap.add_argument("--todo", action="store_true", help="todos los productos de _DIM_PRODUCTOS.csv")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--sin-flujo", action="store_true", help="no consulta flujo.py (fase y ángulo #1)")
    ap.add_argument("--base", default=BASE_POR_DEFECTO, help="raíz alternativa (tests)")
    args = ap.parse_args(argv)
    if not args.producto and not args.todo:
        ap.error("indicá un producto_key o --todo")
    try:
        resultados = revisar(args.base, args.producto, not args.sin_flujo)
    except ep.Rechazo as rechazo:
        print(json.dumps({"ok": False, "detalle": str(rechazo)}, ensure_ascii=False) if args.json
              else f"BLOQUEANTE: {rechazo}", file=sys.stdout if args.json else sys.stderr)
        return 1
    if args.json:
        cuerpo = {"ok": True, "productos": resultados} if args.todo else {"ok": True, **resultados[0]}
        print(json.dumps(cuerpo, ensure_ascii=False, indent=2))
    else:
        print(legible(resultados))
    return 0


if __name__ == "__main__":
    sys.exit(main())
