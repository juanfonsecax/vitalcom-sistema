"""etapa-9 — fábrica de conceptos (ETAPA-9.md "REGLAS" 3/4/6). El fixture es
una tanda real de filas escritas en `PRODUCTOS/_DIM_CREATIVOS.csv` (mismo
producto_key + fecha_alta = una tanda del día). No hay prosa libre propia de
esta etapa persistida en disco (su output narrativo vive en sesión); lo que
SÍ persiste, y es su contrato verificable, son las filas del CSV. Chequeo
mecánico:

1. `canonico_id` obligatorio en toda fila (regla 6).
2. Balance de embudo: no todas las filas comparten el mismo `rol_embudo`
   (regla 3 — "ninguna tanda sale con un solo rol").
3. Máximo 2 ejecuciones por `concepto_key` en la tanda (regla 4).
4. Todas las filas comparten `producto_key` — es una tanda de un solo
   producto, no una mezcla accidental de dos corridas.
"""
from __future__ import annotations

import csv
import io
from collections import Counter

from _util import resultado


def get_assert(output: str, context: dict) -> dict:
    try:
        filas = list(csv.DictReader(io.StringIO(output)))
    except csv.Error as exc:
        return resultado(False, f"CSV inválido: {exc}")

    if not filas:
        return resultado(False, "la tanda no trae ninguna fila")

    productos = {f.get("producto_key", "").strip() for f in filas}
    if len(productos) != 1 or "" in productos:
        return resultado(False, f"la tanda mezcla producto_key distintos o vacíos: {sorted(productos)}")

    sin_canonico = [f["creativo_id"] for f in filas if not f.get("canonico_id", "").strip()]
    if sin_canonico:
        return resultado(False, f"filas sin canonico_id: {sin_canonico}")

    roles = {f.get("rol_embudo", "").strip() for f in filas}
    if len(roles) < 2:
        return resultado(False, f"toda la tanda comparte un solo rol_embudo ({roles}) — falta balance de embudo")

    conteo_concepto = Counter(f.get("concepto_key", "").strip() for f in filas)
    excedidos = {k: v for k, v in conteo_concepto.items() if v > 2}
    if excedidos:
        return resultado(False, f"concepto_key con más de 2 ejecuciones en la tanda: {excedidos}")

    return resultado(
        True,
        f"{len(filas)} fila(s) de 1 tanda: canonico_id completo, {len(roles)} roles de embudo, ningún concepto repetido >2 veces",
    )
