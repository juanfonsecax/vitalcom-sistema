"""etapa-2 — contrato: 6 fichas de ángulo rankeadas (ETAPA-2.md). El formato de
la ficha varía por antigüedad del producto ("1. Nombre · avatar · ..." en
productos viejos, "ÁNGULO N — ..." o "#N ..." en productos nuevos) pero la
CUENTA siempre debe ser 6 (CLAUDE.md: "FASE 1 → 6 ÁNGULOS distintos") y cada
ficha debe traer algo de avatar/nivel de conciencia — no un ángulo sin dueño.
"""
from __future__ import annotations

import re

from _util import resultado

CABECERA_RE = re.compile(r"(?m)^\s*(?:\d+\.\s|ÁNGULO\s+\d+\b|#\d+\b)")
NIVEL_RE = re.compile(r"(?i)\bNC\d+[a-z]?\b|\bN\d\b|nivel de conciencia|\bNivel\b")


def get_assert(output: str, context: dict) -> dict:
    cabeceras = CABECERA_RE.findall(output)
    if len(cabeceras) != 6:
        return resultado(False, f"se esperaban 6 fichas de ángulo, se encontraron {len(cabeceras)}")
    niveles = NIVEL_RE.findall(output)
    if len(niveles) < 6:
        return resultado(False, f"menos de 6 marcadores de nivel de conciencia/avatar ({len(niveles)}) para 6 ángulos")
    return resultado(True, f"6 fichas de ángulo, {len(niveles)} marcadores de nivel de conciencia")
