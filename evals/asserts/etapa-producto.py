"""etapa-producto — contrato: veredicto APTO/NO APTO + score 0-1 (ETAPA-PRODUCTO.md).

El fixture es el fragmento "VALIDACIÓN DE PRODUCTO (ETAPA-PRODUCTO)" de
2_DATA_PRODUCTO.txt. Chequeo mecánico: el veredicto está escrito (no
implícito) y va acompañado de un score numérico entre 0 y 1 — la etapa
declara "score 0-1" en su propia descripción.
"""
from __future__ import annotations

import re

from _util import resultado

VEREDICTO_RE = re.compile(r"\b(NO APTO|APTO(?:\s+CONDICIONAL)?)\b")
SCORE_RE = re.compile(r"\bscore\s+(?:provisional\s+)?(\d(?:\.\d+)?)\b", re.IGNORECASE)


def get_assert(output: str, context: dict) -> dict:
    m_v = VEREDICTO_RE.search(output)
    if not m_v:
        return resultado(False, "no se encontró un veredicto APTO / NO APTO explícito")
    m_s = SCORE_RE.search(output)
    if not m_s:
        return resultado(False, "veredicto presente pero sin score numérico 0-1 explícito")
    score = float(m_s.group(1))
    if not (0.0 <= score <= 1.0):
        return resultado(False, f"score fuera de rango 0-1: {score}")
    return resultado(True, f"veredicto={m_v.group(1)!r} score={score}")
