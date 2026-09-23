# -*- coding: utf-8 -*-
"""gasto.py — FUENTE UNICA DEL GASTO para todo consumidor de CPA (g07-cimientos T2, 22-sep-2026).

POR QUE EXISTE. `_FACT_VENTAS.csv` (LucidSales) trae su propia columna `spend_usd`, y hasta esta
fecha cada consumidor de CPA la usaba tal cual. Evidencia del audit 22-sep: en 06, 14, 15, 16 y
20-sep el `spend_usd` de LucidSales queda CONGELADO a 0.65-0.75 del gasto real de Meta, por
ANUNCIO, el dia entero. En 07-11 y 17-19-sep coincide al centavo. LucidSales mide bien la VENTA;
el GASTO que factura y que de verdad se gastó es el que reporta Meta.

DECISION DE DUEÑO DE DATO: spend/impresiones/clicks/mensajes -> Meta Graph API
(`_FACT_ENTREGA.csv` grano CONJUNTO, `_FACT_ENTREGA_ANUNCIO.csv` grano ANUNCIO, fuente in
{"MetaAPI-directo", "AdsManager-export-1d"}); ventas -> LucidSales (`_FACT_VENTAS.csv`,
rol_ventana=BASE); fallback de spend (días sin cobertura Meta) -> spend_usd de la propia fila
LucidSales.

DISEÑO (rediseñado 22-sep-2026 tras encontrar un defecto de conteo en la primera versión — ver
abajo "POR QUÉ NO UN RESOLVEDOR POR FILA"): el gasto de Meta y las ventas de LucidSales se
AGREGAN POR SEPARADO, cada uno por su cuenta, a un grano donde cada dólar de Meta se cuenta
EXACTAMENTE UNA VEZ, y LUEGO se cruzan con un FULL OUTER JOIN sobre esa llave. Dos grados:

  1. CONJUNTO-VENTANA (`gasto_por_conjunto_ventana`): la llave es (producto_key, cuenta_id,
     ventana_ini, ventana_fin, conjunto canónico). Es lo que necesitan decidir.py y los gates de
     ganador de flujo.py (que agregan por angulo_key, que a su vez agrega por conjunto).
     - Gasto Meta = SUMA de `_FACT_ENTREGA.csv` (grano conjunto) para esa llave. Una sola fuente,
       una sola suma: nunca se reparte ni se copia entre las filas de venta que caen en esa
       celda.
     - Ventas/mensajes = SUMA de `_FACT_VENTAS.csv` (BASE) para esa misma llave.
     - FULL OUTER JOIN: una llave con gasto de Meta y CERO filas de venta sigue contando su gasto
       (ventas=0, no se descarta — invariante 2, "nunca inventar cifras" también significa nunca
       *perder* las reales). Una llave con ventas pero SIN cobertura de Meta para esa cuenta+día
       cae al fallback de LucidSales, marcado.

  2. ANUNCIO-VENTANA (`gasto_por_anuncio_ventana`): la llave es ad_id cuando existe en ambos
     lados, si no (cuenta_id, ventana, conjunto canónico, anuncio). Es lo que necesita el análisis
     de CONCEPTO (una fila de venta por anuncio dentro de un conjunto de FASE 2/3;
     `sembrar_anuncios.py`). Un anuncio de Meta sin venta atribuida sigue contando su gasto
     (ventas=0). Un anuncio SIN match de Meta (ad_id nuevo, o el export de ese día no lo trae)
     quntf NO hereda el gasto del conjunto completo -- eso es exactamente lo que causaba conteo
     múltiple (ver abajo) -- se queda con el fallback de LucidSales, marcado.

POR QUÉ NO UN RESOLVEDOR POR FILA (defecto encontrado en review, 22-sep-2026): la primera versión
de este módulo resolvía el gasto FILA POR FILA de `_FACT_VENTAS.csv`, y cuando ninguna fila de
Meta a nivel anuncio matcheaba, le devolvía a esa fila el spend_usd COMPLETO del conjunto
(`_FACT_ENTREGA.csv`). Un conjunto con N anuncios sin match a nivel anuncio ese día (renombrados,
"- Copia", multi-anuncio) hacía que las N filas de venta se sumaran cada una el gasto COMPLETO del
conjunto -> N× el gasto real. Y a la inversa: el gasto de Meta de un anuncio SIN ninguna fila de
venta ese día nunca aparecía en ningún lado (se perdía, violando "nunca inventar/perder plata").
Con la agregación separada + full outer join, cada dólar de Meta vive en UNA sola fila del
resultado, sin importar cuántas filas de venta o de Meta lo describan por dentro.

ESPEJO EN dbt: `warehouse/models/marts/fct_gasto_dia.sql` implementa la MISMA regla (agregación
por separado + full outer join) en SQL. Si la regla cambia, cambia en los dos lugares.

USO:
    from gasto import gasto_por_conjunto_ventana, gasto_por_anuncio_ventana

    filas = gasto_por_conjunto_ventana()   # una fila por (producto,cuenta,ventana,conjunto)
    filas = gasto_por_anuncio_ventana()    # una fila por (cuenta,ventana,ad_id-o-nombre)

    # Para alimentar un motor que lee _FACT_VENTAS.csv por su cuenta (decidir.py):
    ruta, cobertura = escribir_conjunto_ventana_csv()   # CSV con esquema de _FACT_VENTAS.csv
"""
import os
import csv
import io
import sys
import tempfile
import collections

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from alias import canonico  # noqa: E402

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROD = os.path.join(BASE, "PRODUCTOS")
FACT_ENTREGA_PATH = os.path.join(PROD, "_FACT_ENTREGA.csv")
FACT_ENTREGA_ANUNCIO_PATH = os.path.join(PROD, "_FACT_ENTREGA_ANUNCIO.csv")
FACT_VENTAS_PATH = os.path.join(PROD, "_FACT_VENTAS.csv")

# Fuentes reconocidas como "esto es Meta Graph/export, no un fallback". Un valor de `fuente`
# fuera de este conjunto (p.ej. una fila sembrada a mano) nunca gana sobre LucidSales.
FUENTES_META = {"MetaAPI-directo", "AdsManager-export-1d"}

# Antes de esta fecha no existe pull de Meta en el sistema (ver g06/g07): cualquier venta con
# ventana anterior cae directo al fallback, sin intentar match de Meta.
COBERTURA_META_DESDE = "2026-09-06"

FUENTE_CONJUNTO = "MetaAPI-conjunto"   # match (o suma) contra _FACT_ENTREGA.csv, grano conjunto
FUENTE_AD_ID = "MetaAPI-ad_id"         # match contra _FACT_ENTREGA_ANUNCIO.csv por ad_id
FUENTE_NOMBRE = "MetaAPI-nombre"       # match contra _FACT_ENTREGA_ANUNCIO.csv por nombre
FUENTE_FALLBACK = "LucidSales-fallback"


def _leer_csv(path):
    if not path or not os.path.exists(path):
        return []
    with io.open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def _num(v, default=0.0):
    try:
        if v is None or v == "":
            return default
        return float(v)
    except (TypeError, ValueError):
        return default


def _ad_id_norm(v):
    """'1.2024737592740078e+17' (float mal serializado) -> '120247375927400780'.

    _FACT_VENTAS.csv trae ad_id como texto de un float de Excel/Sheets en filas viejas; las
    nuevas (bajar_meta_insights.py, T1) lo traen como entero. Normalizamos ambas al mismo texto
    entero para que el join no falle por formato.
    """
    v = (v or "").strip()
    if not v:
        return ""
    try:
        return str(int(float(v)))
    except (TypeError, ValueError):
        return v


def _strip(v):
    return (v or "").strip()


# ─────────────────────────────────────────────────────────────────────────────────────────────
# GRANO CONJUNTO-VENTANA — decidir.py, flujo.py (gates de ganador por ángulo)
# ─────────────────────────────────────────────────────────────────────────────────────────────

def _clave_conjunto(r, canon):
    return (_strip(r.get("producto_key")), _strip(r.get("cuenta_id")),
            _strip(r.get("ventana_ini")), _strip(r.get("ventana_fin")),
            canon(_strip(r.get("conjunto"))))


def gasto_por_conjunto_ventana(filas_venta=None, filas_entrega_conjunto=None, alias_fn=None,
                                ruta_ventas=None, ruta_entrega=None, solo_base=True):
    """FULL OUTER JOIN, a grano (producto_key, cuenta_id, ventana_ini, ventana_fin, conjunto
    canónico), entre las VENTAS agregadas de LucidSales y el GASTO agregado de Meta. Devuelve una
    lista de dicts — una fila por llave, nunca una por fila de entrada.

    `solo_base`: filtra `_FACT_VENTAS.csv` a rol_ventana=BASE antes de agregar (default True,
    coincide con la regla de siempre: CONTROL solapa a propósito y nunca suma).
    """
    canon = alias_fn or canonico
    ventas_rows = filas_venta if filas_venta is not None else _leer_csv(ruta_ventas or FACT_VENTAS_PATH)
    meta_rows = (filas_entrega_conjunto if filas_entrega_conjunto is not None
                 else _leer_csv(ruta_entrega or FACT_ENTREGA_PATH))

    ventas_agg = {}
    for r in ventas_rows:
        if solo_base and _strip(r.get("rol_ventana") or "BASE").upper() != "BASE":
            continue
        k = _clave_conjunto(r, canon)
        a = ventas_agg.setdefault(k, {"ventas": 0.0, "mensajes": 0.0, "spend_lucidsales": 0.0})
        a["ventas"] += _num(r.get("ventas"))
        a["mensajes"] += _num(r.get("mensajes"))
        a["spend_lucidsales"] += _num(r.get("spend_usd"))

    meta_agg = {}
    for r in meta_rows:
        if _strip(r.get("fuente")) not in FUENTES_META:
            continue
        k = _clave_conjunto(r, canon)
        meta_agg[k] = meta_agg.get(k, 0.0) + _num(r.get("spend_usd"))

    filas = []
    for k in set(ventas_agg) | set(meta_agg):
        pk, cuenta_id, vi, vf, conj = k
        v = ventas_agg.get(k, {"ventas": 0.0, "mensajes": 0.0, "spend_lucidsales": 0.0})
        if k in meta_agg:
            spend, fuente = meta_agg[k], FUENTE_CONJUNTO
        else:
            spend, fuente = v["spend_lucidsales"], FUENTE_FALLBACK
        filas.append({
            "producto_key": pk, "cuenta_id": cuenta_id, "ventana_ini": vi, "ventana_fin": vf,
            "conjunto": conj, "ventas": v["ventas"], "mensajes": v["mensajes"],
            "spend_usd": spend, "spend_usd_lucidsales": v["spend_lucidsales"],
            "fuente_gasto": fuente,
        })
    return filas


def cobertura_conjunto(filas):
    """{fuente_gasto: n_llaves} sobre el resultado de gasto_por_conjunto_ventana()."""
    return dict(collections.Counter(f["fuente_gasto"] for f in filas))


def escribir_conjunto_ventana_csv(ruta_salida=None, filas_venta=None, filas_entrega_conjunto=None,
                                   alias_fn=None, ruta_ventas=None, ruta_entrega=None):
    """Escribe gasto_por_conjunto_ventana() como un CSV con el esquema mínimo que decidir.py
    necesita de `_FACT_VENTAS.csv` (una fila por llave, no por venta original). Devuelve
    (ruta, cobertura)."""
    filas = gasto_por_conjunto_ventana(filas_venta, filas_entrega_conjunto, alias_fn,
                                        ruta_ventas, ruta_entrega)
    cobertura = cobertura_conjunto(filas)

    if ruta_salida is None:
        fd, ruta_salida = tempfile.mkstemp(prefix="gasto_conjunto_ventana_", suffix=".csv")
        os.close(fd)

    cols = ["ventana_ini", "ventana_fin", "rol_ventana", "producto_key", "cuenta_id", "conjunto",
            "ventas", "mensajes", "spend_usd", "spend_usd_lucidsales", "fuente_gasto"]
    with io.open(ruta_salida, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in filas:
            r2 = dict(r)
            r2["rol_ventana"] = "BASE"
            w.writerow(r2)

    return ruta_salida, cobertura


# ─────────────────────────────────────────────────────────────────────────────────────────────
# GRANO ANUNCIO-VENTANA — sembrar_anuncios.py / _DIM_ANUNCIOS.csv, análisis de CONCEPTO
# ─────────────────────────────────────────────────────────────────────────────────────────────

def _clave_ventana(r):
    return (_strip(r.get("cuenta_id")), _strip(r.get("ventana_ini")), _strip(r.get("ventana_fin")))


def _clave_anuncio(r, canon):
    """(tipo, ...) — ad_id si existe en la fila, si no (campaña, conjunto canónico, anuncio). El
    tipo va en la llave para que un ad_id y un nombre nunca colisionen entre sí por casualidad.

    La CAMPAÑA entra en la llave-por-nombre a propósito: el mismo texto de anuncio (mismo
    blueprint/concepto) se repite DELIBERADAMENTE en más de una campaña de FASE 2 para probar
    replicación (invariante de `_ev_concepto_2de2`) — sin la campaña en la llave, dos campañas
    distintas con el mismo anuncio colapsarían en una sola fila y el gate de 2-de-2 nunca vería
    la segunda ocurrencia. Un consumidor que SÍ quiere sumar a través de campañas (p.ej.
    `sembrar_anuncios.py` agregando réplicas) reagrupa estas filas por su cuenta -- cada una ya
    trae el gasto de Meta contado una sola vez, así que reagrupar nunca duplica ni pierde plata."""
    aid = _ad_id_norm(r.get("ad_id"))
    if aid:
        return ("AD",) + _clave_ventana(r) + (aid,)
    return ("NOM",) + _clave_ventana(r) + (_strip(r.get("campana")),
                                            canon(_strip(r.get("conjunto"))), _strip(r.get("anuncio")))


def gasto_por_anuncio_ventana(filas_venta=None, filas_entrega_anuncio=None, alias_fn=None,
                               ruta_ventas=None, ruta_entrega_anuncio=None, solo_base=True):
    """FULL OUTER JOIN a grano ANUNCIO (ad_id si existe de los dos lados, si no conjunto+anuncio
    canónicos) entre las ventas de LucidSales y el gasto de Meta. Sin fallback a grano conjunto:
    copiar el gasto del conjunto en cada anuncio sin match fue el defecto que este módulo corrige
    (ver docstring del archivo) -- un anuncio sin match individual se queda con el fallback de
    LucidSales, nunca con la porción no-suya de otro anuncio."""
    canon = alias_fn or canonico
    ventas_rows = filas_venta if filas_venta is not None else _leer_csv(ruta_ventas or FACT_VENTAS_PATH)
    meta_rows = (filas_entrega_anuncio if filas_entrega_anuncio is not None
                 else _leer_csv(ruta_entrega_anuncio or FACT_ENTREGA_ANUNCIO_PATH))

    ventas_agg = {}
    for r in ventas_rows:
        if solo_base and _strip(r.get("rol_ventana") or "BASE").upper() != "BASE":
            continue
        if not _strip(r.get("anuncio")):
            continue
        k = _clave_anuncio(r, canon)
        a = ventas_agg.setdefault(k, {
            "ventas": 0.0, "mensajes": 0.0, "spend_lucidsales": 0.0,
            "producto_key": _strip(r.get("producto_key")), "campana": _strip(r.get("campana")),
            "conjunto": canon(_strip(r.get("conjunto"))), "anuncio": _strip(r.get("anuncio")),
            "ad_id": _ad_id_norm(r.get("ad_id")),
        })
        a["ventas"] += _num(r.get("ventas"))
        a["mensajes"] += _num(r.get("mensajes"))
        a["spend_lucidsales"] += _num(r.get("spend_usd"))

    meta_agg = {}
    for r in meta_rows:
        if _strip(r.get("fuente")) not in FUENTES_META:
            continue
        if not _strip(r.get("anuncio")):
            continue
        k = _clave_anuncio(r, canon)
        m = meta_agg.setdefault(k, {
            "spend": 0.0, "producto_key": _strip(r.get("producto_key")),
            "campana": _strip(r.get("campana")), "conjunto": canon(_strip(r.get("conjunto"))),
            "anuncio": _strip(r.get("anuncio")), "ad_id": _ad_id_norm(r.get("ad_id")),
        })
        m["spend"] += _num(r.get("spend_usd"))

    filas = []
    for k in set(ventas_agg) | set(meta_agg):
        v = ventas_agg.get(k)
        m = meta_agg.get(k)
        base = v or m
        if m is not None:
            spend, fuente = m["spend"], (FUENTE_AD_ID if k[0] == "AD" else FUENTE_NOMBRE)
        else:
            spend, fuente = v["spend_lucidsales"], FUENTE_FALLBACK
        filas.append({
            "_clave": k,   # uso interno de indice_gasto_por_anuncio() -- no depender de esto fuera del módulo
            "producto_key": base["producto_key"], "campana": base["campana"],
            "conjunto": base["conjunto"], "anuncio": base["anuncio"], "ad_id": base["ad_id"],
            "cuenta_id": k[1], "ventana_ini": k[2], "ventana_fin": k[3],
            "ventas": v["ventas"] if v else 0.0, "mensajes": v["mensajes"] if v else 0.0,
            "spend_usd": spend,
            "spend_usd_lucidsales": v["spend_lucidsales"] if v else 0.0,
            "fuente_gasto": fuente,
        })
    return filas


def clave_anuncio(r, alias_fn=None):
    """La misma llave de grano ANUNCIO que usa gasto_por_anuncio_ventana(), expuesta para que un
    consumidor con su propia fila (sembrar_anuncios.py) pueda resolver su gasto sin recorrer todo
    el resultado. Debe llamarse con el MISMO `alias_fn` que se usó para construir el índice."""
    return _clave_anuncio(r, alias_fn or canonico)


def indice_gasto_por_anuncio(filas_venta=None, filas_entrega_anuncio=None, alias_fn=None,
                              ruta_ventas=None, ruta_entrega_anuncio=None, solo_base=True):
    """{clave_anuncio(r): (spend_usd, fuente_gasto)} — para un consumidor que resuelve el gasto
    de SUS PROPIAS filas de venta (sembrar_anuncios.py) sin reimplementar el join. Cada valor ya
    salió de gasto_por_anuncio_ventana(): agregado una sola vez, nunca copiado de otro anuncio ni
    del conjunto completo. Un lookup por llave es seguro incluso si dos filas de entrada
    comparten la misma llave (ambas obtienen el mismo total correcto, ninguna sobre-cuenta)."""
    filas = gasto_por_anuncio_ventana(filas_venta, filas_entrega_anuncio, alias_fn,
                                       ruta_ventas, ruta_entrega_anuncio, solo_base)
    return {f["_clave"]: (f["spend_usd"], f["fuente_gasto"]) for f in filas}


def cobertura_anuncio(filas):
    return dict(collections.Counter(f["fuente_gasto"] for f in filas))


if __name__ == "__main__":
    filas_c = gasto_por_conjunto_ventana()
    cob_c = cobertura_conjunto(filas_c)
    total_c = sum(cob_c.values()) or 1
    print("Grano CONJUNTO-VENTANA: %d llaves" % len(filas_c))
    for fuente, n in sorted(cob_c.items(), key=lambda kv: -kv[1]):
        print("  %-22s %5d llaves (%.1f%%)" % (fuente, n, 100.0 * n / total_c))

    filas_a = gasto_por_anuncio_ventana()
    cob_a = cobertura_anuncio(filas_a)
    total_a = sum(cob_a.values()) or 1
    print("\nGrano ANUNCIO-VENTANA: %d llaves" % len(filas_a))
    for fuente, n in sorted(cob_a.items(), key=lambda kv: -kv[1]):
        print("  %-22s %5d llaves (%.1f%%)" % (fuente, n, 100.0 * n / total_a))
