#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""presupuesto_meta.py — Dueño único de las unidades de presupuesto de Meta.

Meta LEE `daily_budget` como objeto en unidades mayores: {"value": "3.99", "unit": "USD"}.
Meta ESCRIBE `daily_budget` como entero en la unidad menor de la moneda (USD 50.00 -> 5000).
Todo el sistema (gen_publicacion, gen_ordenes, verificar_orden) convierte por acá.
"""

# Unidades menores por unidad de moneda en el daily_budget de Meta. COP va en pesos
# enteros: el mínimo diario medido de las cuentas COP es 3154 (~1 USD) en
# _DIM_CUENTAS.csv.min_daily_budget_cents.
UNIDAD_MENOR = {"USD": 100, "COP": 1}


def leer_presupuesto(valor, moneda_defecto=None):
    """Devuelve (monto_en_unidades_mayores, moneda) o (None, None) si no hay presupuesto real.

    Acepta el objeto de Meta {"value","unit"} o un número / string numérico (la moneda sale
    entonces de `moneda_defecto`). Vacío, inválido o <= 0 -> (None, None).
    """
    moneda = moneda_defecto
    if isinstance(valor, dict):
        moneda = (valor.get("unit") or moneda_defecto or None)
        valor = valor.get("value")
    if isinstance(valor, bool):
        return None, None
    try:
        monto = float(valor)
    except (TypeError, ValueError):
        return None, None
    if monto != monto or monto <= 0:   # NaN or non-positive
        return None, None
    if isinstance(moneda, str):
        moneda = moneda.strip().upper() or None
    return monto, moneda


def a_unidad_menor(mayor, moneda):
    """Monto en unidades mayores -> entero en unidad menor; None si la moneda no se conoce."""
    factor = UNIDAD_MENOR.get(moneda)
    if factor is None:
        return None
    return int(round(mayor * factor))
