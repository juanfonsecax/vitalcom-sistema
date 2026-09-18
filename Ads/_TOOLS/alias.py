# -*- coding: utf-8 -*-
"""alias.py — colapsa el nombre viejo de un conjunto de Meta en su nombre canonico.

POR QUE EXISTE (06-sep-2026). El JOIN de todo el sistema es por NOMBRE, no por id: el ad_id
llego corrupto en 2006 de 2475 filas de _FACT_VENTAS.csv y es irrecuperable. Eso hace del
nombre la llave real — y significa que un renombrado en Meta parte la serie historica en dos
conjuntos distintos que en realidad son el mismo objeto. Sin esta tabla, limpiar los nombres
costaria todo el historico previo a la limpieza.

PRODUCTOS/_ALIAS_CONJUNTOS.csv es la unica fuente. Los consumidores no deben escribir mapeos
propios: cada mapeo suelto es una version mas de la verdad.

    from alias import canonico
    canonico("GTR0_TINNIDROP_PERDIDA-AUDITIVA_R1 +25ANOS")  -> "GTR0_TINNIDROP_PERDIDA-AUDITIVA_R1"

Un nombre que no esta en la tabla se devuelve tal cual: la tabla solo colapsa lo que fue
renombrado de verdad, nunca adivina por parecido.
"""
import os, csv

_BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_CSV = os.path.join(_BASE, "PRODUCTOS", "_ALIAS_CONJUNTOS.csv")
_MAPA = None


def mapa_de(filas):
    """{nombre_viejo: nombre_nuevo} a partir de filas de _ALIAS_CONJUNTOS.csv, resolviendo cadenas.

    Funcion pura: la usan los consumidores que leen su propia base (flujo.py sobre un fixture,
    decidir.py con sus rutas de modulo). mapa() la aplica sobre el CSV real.
    """
    m = {}
    for r in filas:
        v = (r.get("nombre_viejo") or "").strip()
        n = (r.get("nombre_nuevo") or "").strip()
        if v and n and v != n:
            m[v] = n
    # A renombrado a B y B a C -> A debe resolver a C.
    for k in list(m):
        visto, v = {k}, m[k]
        while v in m and v not in visto:
            visto.add(v)
            v = m[v]
        m[k] = v
    return m


def mapa():
    """{nombre_viejo: nombre_nuevo} del CSV real, resolviendo cadenas de renombrados."""
    global _MAPA
    if _MAPA is None:
        filas = []
        if os.path.exists(_CSV):
            with open(_CSV, encoding="utf-8") as f:
                filas = list(csv.DictReader(f))
        _MAPA = mapa_de(filas)
    return _MAPA


def canonico(nombre):
    return mapa().get((nombre or "").strip(), (nombre or "").strip())
