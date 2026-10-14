#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""mercado.py — resuelve el MERCADO de un producto y su perfil (moneda, simbolo, tono, registro).

Un dato, un dueño
-----------------
  · `PRODUCTOS/_DIM_PRODUCTOS.csv` columna `mercado` (GT/CO): a que mercado vende el producto.
  · `PRODUCTOS/_DIM_MERCADOS.csv`: pais, moneda de venta, simbolo, persona (voseo/tuteo) y
    registro sanitario de cada mercado.
  · `PRODUCTOS/_PARAMETROS_FINANZAS.csv`: tasa de referencia del mercado (`tasa_usd_gtq`,
    `tasa_cop_usd`: unidades de moneda local por USD).

Este modulo NO guarda ningun dato: solo lee esos tres archivos. Un producto sin `mercado`, o con un
mercado que no existe en `_DIM_MERCADOS.csv`, FALLA con `MercadoError` (invariante 4: nunca se
asume; no hay GT por defecto).

`_DIM_PRODUCTOS.moneda` NO es la moneda de venta: es la moneda de la CUENTA PUBLICITARIA con la que
Meta le cobra la pauta al producto (las cuentas GTR facturan en USD, la cuenta de OVULOS_PURITY en
COP). La moneda en que el producto VENDE sale del mercado (`perfil_mercado(...)["moneda"]`).

`_FACT_VENTAS.total_q` es el monto de la venta en la moneda de venta del mercado del producto (GT: GTQ,
CO: COP), sin etiqueta en la fila: la moneda se lee de aqui (`perfil_de_producto(pk)["moneda"]`). Su
columna `moneda_origen` es la del gasto publicitario, no la de venta.

`_DIM_PRODUCTOS.tasa` sigue siendo la tasa que usan los motores (decidir, atribuir, flujo...). Aca
solo se expone la tasa de referencia del mercado y `avisos_tasa()` marca, en solo lectura, a un
producto cuya tasa se aparta mucho de ella.

Numeros de registro sanitario
-----------------------------
`_DIM_MERCADOS.registro_sanitario` nombra al regulador («registro MSPAS», «registro INVIMA»), no trae el
numero. Los numeros REALES viven en `DOCTRINA/PLANTILLAS_DEFAULTS_OPERADOR.md` (`[REG_MSPAS]`, `[REG_FDA]`,
`[REG_INVIMA]`) y `registro_de_perfil()` los lee de ahi: un valor entre `**` y comillas invertidas es un
numero; cualquier otra cosa (p.ej. «PENDIENTE del operador») es un numero que falta. Falta = `RegistroFaltante`;
nunca se inventa ni se cae al de otro mercado. Quien escribe ese numero es el operador, editando esa fila.
Excepcion por producto: con `registro_sanitario_estado` EN_TRAMITE en `_DIM_PRODUCTOS.csv`,
`registro_de_producto()` devuelve el registro vacio y marcado (`en_tramite=True`) y la pieza sale
sin sello ni numero.

Uso
---
    python Ads/_TOOLS/mercado.py --producto PK     # perfil del producto (JSON, solo lectura)
    python Ads/_TOOLS/mercado.py PRODUCTO_KEY      # igual
    python Ads/_TOOLS/mercado.py --avisos          # tasas que no cuadran con su mercado
"""

import csv
import io
import json
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

BASE_POR_DEFECTO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Un producto cuya tasa se aparta mas de este margen de la tasa de referencia de su mercado se avisa.
TOLERANCIA_TASA = 0.20

CAMPOS_PERFIL = ("mercado", "pais", "moneda", "simbolo", "persona", "registro_sanitario",
                 "tasa_moneda_por_usd")


class MercadoError(Exception):
    """Falta o no cuadra el mercado de un producto. Se dice y se detiene; no se asume."""


class RegistroFaltante(MercadoError):
    """El mercado exige un registro sanitario cuyo numero el operador todavia no entrego."""

    def __init__(self, mensaje, regulador, claves):
        super().__init__(mensaje)
        self.regulador = regulador
        self.claves = list(claves)


class TasaFaltante(MercadoError):
    """Un producto no declara una `tasa` utilizable en _DIM_PRODUCTOS.csv. No hay tasa por defecto."""


def _leer(base, nombre):
    ruta = os.path.join(base or BASE_POR_DEFECTO, "PRODUCTOS", nombre)
    if not os.path.isfile(ruta):
        raise MercadoError("falta PRODUCTOS/%s." % nombre)
    with io.open(ruta, encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def leer_mercados(base=None):
    """{mercado: fila} de _DIM_MERCADOS.csv."""
    return {(f.get("mercado") or "").strip(): f for f in _leer(base, "_DIM_MERCADOS.csv")
            if (f.get("mercado") or "").strip()}


def tasa_de_fila(fila):
    """La `tasa` (moneda local por USD) de una fila de _DIM_PRODUCTOS, o TasaFaltante.

    No hay valor por defecto: un producto sin tasa numerica y > 0 no se convierte a moneda local.
    Cada herramienta decide si se detiene (raise) o salta ese producto avisando."""
    clave = (fila.get("producto_key") or "?").strip()
    crudo = (fila.get("tasa") or "").strip()
    try:
        tasa = float(crudo)
    except ValueError:
        tasa = 0.0
    if tasa <= 0:
        raise TasaFaltante("«%s» no declara `tasa` (moneda local por USD) en _DIM_PRODUCTOS.csv "
                           "(valor: «%s»): sin tasa no se convierte su gasto; no hay tasa por defecto."
                           % (clave, crudo))
    return tasa


def _fila_producto(producto_key, base):
    for fila in _leer(base, "_DIM_PRODUCTOS.csv"):
        if (fila.get("producto_key") or "").strip() == producto_key:
            return fila
    raise MercadoError("«%s» no tiene fila en _DIM_PRODUCTOS.csv." % producto_key)


def estado_registro(fila):
    """`registro_sanitario_estado` de una fila de _DIM_PRODUCTOS: VIGENTE (default, vacío =
    VIGENTE) o EN_TRAMITE. Solo EN_TRAMITE saca la pieza sin sello; cualquier otro valor
    exige el número como siempre."""
    return (fila.get("registro_sanitario_estado") or "").strip().upper() or "VIGENTE"


def mercado_de_fila(fila, base=None):
    """El mercado (`GT`/`CO`) de una fila de _DIM_PRODUCTOS (leida del CSV o de Postgres).
    Falla si no lo declara o si no existe en _DIM_MERCADOS.csv."""
    clave = (fila.get("producto_key") or "?").strip()
    if "mercado" not in fila:
        raise MercadoError("_DIM_PRODUCTOS no tiene la columna `mercado`.")
    mercado = (fila.get("mercado") or "").strip()
    if not mercado:
        raise MercadoError("«%s» no declara `mercado` en _DIM_PRODUCTOS.csv: el operador elige "
                           "GT o CO; no hay un valor por defecto." % clave)
    conocidos = leer_mercados(base)
    if mercado not in conocidos:
        raise MercadoError("«%s» declara mercado «%s», que no existe en _DIM_MERCADOS.csv "
                           "(mercados: %s)." % (clave, mercado, ", ".join(sorted(conocidos))))
    return mercado


def mercado_de(producto_key, base=None):
    """El mercado (`GT`/`CO`) declarado del producto. Falla si no lo tiene o no existe."""
    return mercado_de_fila(_fila_producto(producto_key, base), base)


def _tasa_de_referencia(moneda, base):
    """Tasa de _PARAMETROS_FINANZAS.csv en unidades de `moneda` por USD, o None si no esta declarada.
    Convencion de nombres del CSV: `tasa_usd_<moneda>` (p.ej. tasa_usd_gtq) o `tasa_<moneda>_usd`."""
    m = moneda.strip().lower()
    valores = {(f.get("parametro") or "").strip(): (f.get("valor") or "").strip()
               for f in _leer(base, "_PARAMETROS_FINANZAS.csv")}
    for nombre in ("tasa_usd_%s" % m, "tasa_%s_usd" % m):
        if valores.get(nombre):
            try:
                return float(valores[nombre])
            except ValueError:
                raise MercadoError("_PARAMETROS_FINANZAS.csv: %s = «%s» no es un numero."
                                   % (nombre, valores[nombre]))
    return None


def perfil_mercado(mercado, base=None):
    """{mercado, pais, moneda, simbolo, persona, registro_sanitario, tasa_moneda_por_usd}.

    `tasa_moneda_por_usd` es la tasa de REFERENCIA del mercado (unidades locales por USD) o None si
    _PARAMETROS_FINANZAS.csv no la declara: quien la necesite para un calculo debe fallar, no asumir."""
    conocidos = leer_mercados(base)
    fila = conocidos.get((mercado or "").strip())
    if fila is None:
        raise MercadoError("mercado «%s» no existe en _DIM_MERCADOS.csv (mercados: %s)."
                           % (mercado, ", ".join(sorted(conocidos))))
    moneda = (fila.get("moneda") or "").strip()
    if not moneda:
        raise MercadoError("_DIM_MERCADOS.csv: el mercado %s no declara moneda." % mercado)
    return {
        "mercado": fila["mercado"].strip(),
        "pais": (fila.get("pais") or "").strip(),
        "moneda": moneda,
        "simbolo": (fila.get("simbolo") or "").strip(),
        "persona": (fila.get("persona") or "").strip(),
        "registro_sanitario": (fila.get("registro_sanitario") or "").strip(),
        "tasa_moneda_por_usd": _tasa_de_referencia(moneda, base),
    }


def perfil_de_fila(fila, base=None):
    """El perfil del mercado de una fila de _DIM_PRODUCTOS (falla igual que `mercado_de_fila`)."""
    return perfil_mercado(mercado_de_fila(fila, base), base)


def perfil_de_producto(producto_key, base=None):
    """El perfil del mercado del producto (falla igual que `mercado_de`)."""
    return perfil_mercado(mercado_de(producto_key, base), base)


# Que numeros de DOCTRINA/PLANTILLAS_DEFAULTS_OPERADOR.md lleva el registro de cada regulador.
NUMEROS_POR_REGULADOR = {"MSPAS": ("MSPAS", "FDA"), "INVIMA": ("INVIMA",)}
DOCTRINA_REGISTROS = ("DOCTRINA", "PLANTILLAS_DEFAULTS_OPERADOR.md")
_RE_REGISTRO = re.compile(r"^\|\s*`\[REG_(\w+)\]`\s*\|\s*\*\*`([^`]+)`\*\*", re.M)


def regulador_de(perfil):
    """«MSPAS» / «INVIMA»: la ultima palabra de `registro_sanitario` («registro MSPAS»)."""
    palabras = (perfil.get("registro_sanitario") or "").split()
    return palabras[-1].upper() if palabras else ""


def leer_registros(base=None):
    """{'MSPAS': 'NS...', 'FDA': '...'} con los numeros que la doctrina declara como valor real."""
    ruta = os.path.join(base or BASE_POR_DEFECTO, *DOCTRINA_REGISTROS)
    if not os.path.isfile(ruta):
        raise MercadoError("falta %s." % "/".join(DOCTRINA_REGISTROS))
    with io.open(ruta, encoding="utf-8") as fh:
        return {clave: valor.strip() for clave, valor in _RE_REGISTRO.findall(fh.read())}


def registro_de_perfil(perfil, base=None):
    """{regulador, texto, ajenos} del registro sanitario del mercado, o `RegistroFaltante`.

    `texto` = los numeros del mercado tal como van en una pieza («MSPAS NS02026-GT3147 · FDA 30045469041»).
    `ajenos` = los reguladores de los OTROS mercados, para decirle al modelo que no los use."""
    regulador = regulador_de(perfil)
    claves = NUMEROS_POR_REGULADOR.get(regulador)
    if not claves:
        raise RegistroFaltante("el mercado %s declara el registro «%s», y no se sabe que numeros lleva."
                               % (perfil.get("mercado"), perfil.get("registro_sanitario")), regulador, [])
    registros = leer_registros(base)
    faltan = [c for c in claves if not registros.get(c)]
    if faltan:
        raise RegistroFaltante(
            "falta el numero de registro %s del mercado %s en DOCTRINA/PLANTILLAS_DEFAULTS_OPERADOR.md "
            "([REG_%s]): lo entrega el operador." % (", ".join(faltan), perfil.get("mercado"), faltan[0]),
            regulador, faltan)
    return {"regulador": regulador, "texto": " · ".join("%s %s" % (c, registros[c]) for c in claves),
            "ajenos": _ajenos(perfil, base)}


def _ajenos(perfil, base=None):
    """Los reguladores de los OTROS mercados, para decirle al modelo que no los use."""
    regulador = regulador_de(perfil)
    return sorted({regulador_de(f) for m, f in leer_mercados(base).items()
                   if m != perfil.get("mercado")} - {"", regulador})


def registro_en_tramite(perfil, base=None):
    """El registro de un producto con `registro_sanitario_estado` EN_TRAMITE: vacío y marcado
    con `en_tramite=True`. La pieza sale sin sello ni número, nunca con uno inventado."""
    return {"regulador": regulador_de(perfil), "texto": "", "ajenos": _ajenos(perfil, base),
            "en_tramite": True}


def registro_de_producto(producto_key, base=None):
    """El registro sanitario del producto: con EN_TRAMITE sale vacío y marcado (la pieza no
    lleva sello); sin él exige el número del mercado como siempre (`RegistroFaltante`)."""
    fila = _fila_producto(producto_key, base)
    perfil = perfil_de_fila(fila, base)
    if estado_registro(fila) == "EN_TRAMITE":
        return registro_en_tramite(perfil, base)
    return registro_de_perfil(perfil, base)


def formatear_monto(valor, perfil, decimales=0):
    """Un monto en la notacion de la moneda del mercado: GTQ «Q179» · COP «$ 41.000» (punto de miles)."""
    simbolo = perfil.get("simbolo") or ""
    if perfil.get("moneda") == "COP":
        return "%s %s" % (simbolo, "{:,.{d}f}".format(float(valor), d=decimales).replace(",", "."))
    return "%s%.*f" % (simbolo, decimales, float(valor))


VOSEO_A_TUTEO = [   # pares (voseo, tuteo); frases específicas donde la palabra sola es ambigua
    ("con vos", "contigo"), ("por vos", "por ti"), ("Contame", "Cuéntame"),
    ("escribís", "escribes"), ("Deseás", "Deseas"), ("sabés", "sabes"), ("pagás", "pagas"),
    ("¿Confirmame", "¿Me confirmas"), ("Confirmame", "Confírmame"), ("arriesgás", "arriesgas"),
    ("llevás", "llevas"), ("asegurate", "asegúrate"), ("podés", "puedes"),
    ("indicame", "indícame"), ("o escribí OFICINA", "o escribe OFICINA"),
    ("reclamás", "reclamas"), ("preferís", "prefieres"), ("Confirmás", "Confirmas"),
    ("Recordá", "Recuerda"), ("tenés", "tienes"), ("disfrutés", "disfrutes"),
    ("escribás", "escribas"), ("hacé ", "haz "), ("Indicale", "Indícale"),
    ("corregila", "corrígela"), ("Hacelo", "Hazlo"), ("CAMBIÁ", "CAMBIA"), ("Decime", "Dime"),
    ("persuadilo", "persuádelo"), ("Respondé", "Responde"), ("respondé", "responde"),
    ("No continuás", "No continúes"),
]


def aplicar_persona(texto, persona):
    """Devuelve el texto en la persona del mercado. Solo 'tuteo' transforma."""
    if persona != "tuteo":
        return texto
    for voseo, tuteo in VOSEO_A_TUTEO:
        texto = texto.replace(voseo, tuteo)
    return texto


RE_VOSEO = re.compile(r"\b(vos|sabés|pagás|podés|tenés|querés|llevás|arriesgás|reclamás|"
    r"preferís|escribís|deseás|confirmás|contame|decime|confirmame|indicame|asegurate|"
    r"recordá|respondé|hacelo|indicale|corregila|persuadilo|cambiá|disfrutés|escribás|"
    r"continuás)\b", re.I)


def voseo_restante(texto):
    """Lista ordenada y sin repetir de las formas de voseo que quedan en el texto."""
    return sorted({m.lower() for m in RE_VOSEO.findall(texto)})


_CACHE_PERFIL = {}


def monto_producto(valor, producto_key, decimales=None, base=None):
    """Un monto en la moneda del mercado del producto (solo presentacion).

    COP: formatear_monto(valor, perfil, 0)            → "$ 28.031"
    resto, decimales=None: simbolo + "%s" % valor     → "Q50.1" (el valor tal cual venía)
    resto, decimales=N:    simbolo + "%.*f"           → "Q50.10" con N=2

    Sin mercado declarado se propaga el error de perfil_de_producto (no hay default).
    La caché se indexa por (producto_key, base)."""
    try:
        perfil = _CACHE_PERFIL.get((producto_key, base))
    except TypeError:
        perfil = None
    if perfil is None:
        perfil = perfil_de_producto(producto_key, base)
        try:
            _CACHE_PERFIL[(producto_key, base)] = perfil
        except TypeError:
            pass
    if perfil.get("moneda") == "COP":
        return formatear_monto(valor, perfil, 0)
    simbolo = perfil.get("simbolo") or ""
    if decimales is None:
        return "%s%s" % (simbolo, valor)
    return "%s%.*f" % (simbolo, decimales, float(valor))


def monto_o_q(valor, decimales, producto_key, base=None):
    """El monto en la moneda del producto, para textos del motor.

    Sin producto_key, o si el producto NO tiene fila en _DIM_PRODUCTOS (fixtures de tests,
    backtest): formato Q de siempre. Si el producto SÍ tiene fila pero su mercado no
    resuelve: se propaga MercadoError (un producto real nunca sale en Q por descarte)."""
    if decimales is None:
        q = "Q%s" % valor
    else:
        q = "Q%.*f" % (decimales, float(valor))
    if not producto_key:
        return q
    try:
        _fila_producto(producto_key, base)
    except MercadoError:
        return q
    return monto_producto(valor, producto_key, decimales, base)


def avisos_tasa(base=None, tolerancia=TOLERANCIA_TASA):
    """Solo lectura: lista de textos, uno por producto cuya `tasa` no cuadra con su mercado.

    Se avisa cuando la tasa esta vacia o no es numerica, cuando el mercado no declara tasa de
    referencia, o cuando se aparta de ella mas de `tolerancia` (relativa). Nunca corrige nada."""
    avisos = []
    for fila in _leer(base, "_DIM_PRODUCTOS.csv"):
        clave = (fila.get("producto_key") or "").strip()
        if not clave:
            continue
        try:
            perfil = perfil_de_producto(clave, base)
        except MercadoError as error:
            avisos.append("%s: %s" % (clave, error))
            continue
        referencia = perfil["tasa_moneda_por_usd"]
        if referencia is None:
            avisos.append("%s: el mercado %s no tiene tasa de referencia en _PARAMETROS_FINANZAS.csv."
                          % (clave, perfil["mercado"]))
            continue
        crudo = (fila.get("tasa") or "").strip()
        try:
            tasa = float(crudo)
        except ValueError:
            avisos.append("%s: tasa «%s» vacia o no numerica (referencia %s %s/USD)."
                          % (clave, crudo, perfil["moneda"], referencia))
            continue
        if abs(tasa - referencia) > tolerancia * referencia:
            avisos.append("%s: tasa %s se aparta de la referencia del mercado %s (%s %s/USD) por mas de %d%%."
                          % (clave, crudo, perfil["mercado"], perfil["moneda"], referencia,
                             round(tolerancia * 100)))
    return avisos


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    try:
        if argv == ["--avisos"]:
            avisos = avisos_tasa()
            print("\n".join(avisos) if avisos else "Sin avisos: cada tasa cuadra con su mercado.")
            return 0
        if len(argv) == 2 and argv[0] == "--producto":
            argv = argv[1:]
        if len(argv) == 1 and not argv[0].startswith("-"):
            print(json.dumps(perfil_de_producto(argv[0]), ensure_ascii=False, indent=2))
            return 0
    except MercadoError as error:
        print("BLOQUEANTE: %s" % error, file=sys.stderr)
        return 1
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
