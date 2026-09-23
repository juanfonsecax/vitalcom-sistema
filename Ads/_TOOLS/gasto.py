# -*- coding: utf-8 -*-
"""gasto.py — FUENTE UNICA DEL GASTO para todo consumidor de CPA (g07-cimientos T2, 22-sep-2026).

POR QUE EXISTE. `_FACT_VENTAS.csv` (LucidSales) trae su propia columna `spend_usd`, y hasta esta
fecha cada consumidor de CPA la usaba tal cual. Evidencia del audit 22-sep: en 06, 14, 15, 16 y
20-sep el `spend_usd` de LucidSales queda CONGELADO a 0.65-0.75 del gasto real de Meta, por
ANUNCIO, el dia entero (no depende de la hora de descarga: 06/07/08-sep se bajaron juntos y solo
el 06 esta mal). En 07-11 y 17-19-sep coincide al centavo. LucidSales mide bien la VENTA; el
GASTO que factura y que de verdad se gastó es el que reporta Meta.

DECISION DE DUENO DE DATO (CLAUDE.md ya decía: ventas = LucidSales, Meta = entrega. Spend ES
entrega, y Meta es quien factura):
    spend_usd / impresiones / clicks / mensajes  -> Meta Graph API
        (`_FACT_ENTREGA.csv` grano CONJUNTO, `_FACT_ENTREGA_ANUNCIO.csv` grano ANUNCIO,
         fuente in {"MetaAPI-directo", "AdsManager-export-1d"})
    ventas                                       -> LucidSales (`_FACT_VENTAS.csv`, rol_ventana=BASE)
    fallback de spend (dias sin cobertura Meta, antes de 2026-09-06)
                                                  -> spend_usd de la propia fila LucidSales

REGLA DE JOIN (determinista, en ese orden — nunca se inventa plata, invariante 2):
  1. AD_ID: si la fila de venta trae `ad_id` y existe una fila de `_FACT_ENTREGA_ANUNCIO.csv`
     con el MISMO ad_id para (cuenta_id, ventana_ini, ventana_fin) -> su spend_usd. Sobrevive a
     un renombrado de conjunto o de anuncio; es la coincidencia mas exacta posible.
  2. NOMBRE CANONICO A NIVEL ANUNCIO: sin match de ad_id (dato historico sin la columna, o el
     ad_id no aparece ese dia en el export) -> (cuenta_id, ventana, conjunto canonico via
     `alias.canonico()`, anuncio) contra `_FACT_ENTREGA_ANUNCIO.csv`.
  3. GRANO CONJUNTO: si el anuncio tampoco aparece en el export de Meta de ese dia (pausado,
     variante de split-test que Meta reporta distinto, etc.) -> spend_usd de `_FACT_ENTREGA.csv`
     para (cuenta_id, ventana, conjunto canonico). Es la MISMA plata real, solo que no se pudo
     bajar al anuncio individual: se cuenta completa al conjunto/angulo en vez de descartarla.
  4. FALLBACK LucidSales: si ninguna fila de Meta cubre esa (cuenta_id, ventana) -- antes de
     `COBERTURA_META_DESDE`, o un dia con el pull fallido -- se usa el spend_usd que trae la
     propia fila de LucidSales.

Cada resultado viaja con su `fuente_gasto` ("MetaAPI-ad_id" / "MetaAPI-nombre" /
"MetaAPI-conjunto" / "LucidSales-fallback") para que ningun consumidor mezcle a ciegas.

ESPEJO EN dbt: `warehouse/models/marts/fct_gasto_dia.sql` implementa la MISMA regla en SQL sobre
`stg_entrega_anuncio`, `stg_entrega_conjunto` y `stg_ventas` — ver su docstring, que debe leerse
como la traduccion SQL de este modulo. Si la regla cambia, cambia en los dos lugares.

USO:
    from gasto import IndiceGasto
    idx = IndiceGasto()                          # lee los CSV reales de PRODUCTOS/
    spend, fuente = idx.gasto_de(fila_de_venta)  # fila_de_venta: dict de _FACT_VENTAS.csv

    # Para alimentar un motor que lee _FACT_VENTAS.csv por su cuenta (decidir.py):
    ruta, cobertura = escribir_ventas_con_gasto_efectivo()   # CSV temporal, mismo esquema + fuente_gasto
"""
import os
import csv
import io
import sys
import tempfile

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
# ventana anterior cae directo al fallback, sin intentar los tres pasos de Meta.
COBERTURA_META_DESDE = "2026-09-06"

FUENTE_AD_ID = "MetaAPI-ad_id"
FUENTE_NOMBRE = "MetaAPI-nombre"
FUENTE_CONJUNTO = "MetaAPI-conjunto"
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


class IndiceGasto:
    """Indices de spend_usd de Meta, listos para resolver filas de _FACT_VENTAS.csv.

    Se construye una sola vez (lee los dos FACT de Meta) y se reusa por fila con `gasto_de()`.
    """

    def __init__(self, filas_anuncio=None, filas_conjunto=None, alias_fn=None,
                 ruta_entrega_anuncio=None, ruta_entrega=None):
        """alias_fn: canonicalizador de nombre de conjunto a usar (default: alias.canonico() del
        repo real). Un consumidor que corre sobre un fixture de test (flujo.py sobre `env`, o
        decidir.py con sus rutas de módulo monkey-parcheadas) pasa su propio `alias_fn` y/o sus
        propias `ruta_entrega*` para no cruzar contra los CSV del repo real."""
        self._canon = alias_fn or canonico
        self._por_ad_id = {}
        self._por_nombre_anuncio = {}
        self._por_conjunto = {}
        self._ventanas_meta = set()  # (cuenta_id, ventana_ini, ventana_fin) con cobertura Meta

        for r in (filas_anuncio if filas_anuncio is not None
                  else _leer_csv(ruta_entrega_anuncio or FACT_ENTREGA_ANUNCIO_PATH)):
            if (r.get("fuente") or "").strip() not in FUENTES_META:
                continue
            clave_ventana = self._clave_ventana(r)
            self._ventanas_meta.add(clave_ventana)
            sp = _num(r.get("spend_usd"))
            aid = _ad_id_norm(r.get("ad_id"))
            if aid:
                k = (clave_ventana, aid)
                self._por_ad_id[k] = self._por_ad_id.get(k, 0.0) + sp
            conj = self._canon((r.get("conjunto") or "").strip())
            anu = (r.get("anuncio") or "").strip()
            if conj and anu:
                k = (clave_ventana, conj, anu)
                self._por_nombre_anuncio[k] = self._por_nombre_anuncio.get(k, 0.0) + sp

        for r in (filas_conjunto if filas_conjunto is not None
                  else _leer_csv(ruta_entrega or FACT_ENTREGA_PATH)):
            if (r.get("fuente") or "").strip() not in FUENTES_META:
                continue
            clave_ventana = self._clave_ventana(r)
            self._ventanas_meta.add(clave_ventana)
            conj = self._canon((r.get("conjunto") or "").strip())
            if conj:
                k = (clave_ventana, conj)
                self._por_conjunto[k] = self._por_conjunto.get(k, 0.0) + _num(r.get("spend_usd"))

    @staticmethod
    def _clave_ventana(r):
        return ((r.get("cuenta_id") or "").strip(), (r.get("ventana_ini") or "").strip(),
                 (r.get("ventana_fin") or "").strip())

    def gasto_de(self, fila_venta):
        """(spend_usd_efectivo, fuente_gasto) para una fila de _FACT_VENTAS.csv."""
        clave_ventana = self._clave_ventana(fila_venta)
        conj = self._canon((fila_venta.get("conjunto") or "").strip())
        anu = (fila_venta.get("anuncio") or "").strip()
        aid = _ad_id_norm(fila_venta.get("ad_id"))

        if aid:
            k = (clave_ventana, aid)
            if k in self._por_ad_id:
                return self._por_ad_id[k], FUENTE_AD_ID
        if conj and anu:
            k = (clave_ventana, conj, anu)
            if k in self._por_nombre_anuncio:
                return self._por_nombre_anuncio[k], FUENTE_NOMBRE
        if conj:
            k = (clave_ventana, conj)
            if k in self._por_conjunto:
                return self._por_conjunto[k], FUENTE_CONJUNTO
        return _num(fila_venta.get("spend_usd")), FUENTE_FALLBACK

    def cobertura(self, filas_venta):
        """{fuente_gasto: cantidad_de_filas} — para reportar cobertura en cada corrida."""
        conteo = {}
        for r in filas_venta:
            _, f = self.gasto_de(r)
            conteo[f] = conteo.get(f, 0) + 1
        return conteo


def filas_con_gasto_efectivo(filas_venta, indice=None):
    """Copia de `filas_venta` con `spend_usd` reemplazado por el gasto efectivo (regla de arriba).

    Conserva el spend_usd original de LucidSales en `spend_usd_lucidsales` (auditoria) y agrega
    `fuente_gasto`. No muta las filas de entrada.
    """
    idx = indice or IndiceGasto()
    salida = []
    for r in filas_venta:
        r2 = dict(r)
        efectivo, fuente = idx.gasto_de(r)
        r2["spend_usd_lucidsales"] = r.get("spend_usd", "")
        r2["spend_usd"] = efectivo
        r2["fuente_gasto"] = fuente
        salida.append(r2)
    return salida


def escribir_ventas_con_gasto_efectivo(ruta_salida=None, filas_venta=None, indice=None,
                                        ruta_ventas=None, ruta_entrega_anuncio=None,
                                        ruta_entrega=None, alias_fn=None):
    """Escribe un CSV con el mismo esquema de _FACT_VENTAS.csv + fuente_gasto (spend_usd ya
    corregido), para que un consumidor que lee el CSV por su cuenta (decidir.py, via DuckDB
    read_csv) no tenga que reimplementar la regla. Devuelve (ruta, cobertura).

    `ruta_ventas` / `ruta_entrega_anuncio` / `ruta_entrega` dejan apuntar a un fixture de test en
    vez de a los CSV reales de PRODUCTOS/ (decidir.py los monkey-parchea para correr sobre un
    fixture; ver flujo.py Entorno.motor()).
    """
    idx = indice or IndiceGasto(alias_fn=alias_fn, ruta_entrega_anuncio=ruta_entrega_anuncio,
                                 ruta_entrega=ruta_entrega)
    filas = filas_venta if filas_venta is not None else _leer_csv(ruta_ventas or FACT_VENTAS_PATH)
    corregidas = filas_con_gasto_efectivo(filas, idx)
    cobertura = idx.cobertura(filas)

    if ruta_salida is None:
        fd, ruta_salida = tempfile.mkstemp(prefix="ventas_gasto_efectivo_", suffix=".csv")
        os.close(fd)

    cols = list(filas[0].keys()) if filas else [
        "ventana_ini", "ventana_fin", "dias", "rol_ventana", "producto_key", "producto",
        "cuenta_id", "cuenta_alias", "campana", "conjunto", "anuncio", "mensajes", "clicks",
        "impresiones", "spend_usd", "ventas", "total_q", "moneda_origen", "fuente", "ad_id",
    ]
    for extra in ("spend_usd_lucidsales", "fuente_gasto"):
        if extra not in cols:
            cols.append(extra)

    with io.open(ruta_salida, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in corregidas:
            w.writerow(r)

    return ruta_salida, cobertura


if __name__ == "__main__":
    ruta, cobertura = escribir_ventas_con_gasto_efectivo()
    total = sum(cobertura.values()) or 1
    print("Gasto efectivo escrito en", ruta)
    for fuente, n in sorted(cobertura.items(), key=lambda kv: -kv[1]):
        print("  %-22s %5d filas (%.1f%%)" % (fuente, n, 100.0 * n / total))
