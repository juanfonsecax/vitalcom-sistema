"""etapa-7 — monitor diario de métricas (ETAPA-7.md, invariante de CLAUDE.md
"mide por CPA, nunca por ROAS"). El fixture es el bloque "Lectura cualitativa
(ETAPA-7)" de una auditoría nocturna real (ciclo-diario invoca a etapa-7 +
etapa-8 en la misma corrida) más el estado del motor que cita. Chequeo
mecánico del contrato de PASO 0/3 de ETAPA-7.md:

1. Nunca aparece la palabra ROAS (regla dura, en ningún lado del informe).
2. Cita el CPA (Q) — la métrica correcta.
3. Declara la integridad de la ventana (día completos / parcial).
4. Cuantifica el SANGRADO (en Q, aunque sea ≈Q0) — PASO 3 obligatorio.
5. Trae una lectura por dimensión que separa cuenta de ángulo (MATRIZ CUENTA /
   DIMENSIÓN) — la regla "cuenta rota ≠ ángulo malo".
"""
from __future__ import annotations

import re

from _util import resultado

ROAS_RE = re.compile(r"(?i)\bROAS\b")
CPA_RE = re.compile(r"(?i)CPA\s*Q?\s*\d")
INTEGRIDAD_RE = re.compile(r"(?i)INTEGRIDAD")
SANGRADO_RE = re.compile(r"(?i)SANGRADO.{0,20}(≈?Q\s*[\d.]+|Q0)")
MATRIZ_O_DIMENSION_RE = re.compile(r"(?i)MATRIZ CUENTA|DIMENSI[OÓ]N")


def get_assert(output: str, context: dict) -> dict:
    if ROAS_RE.search(output):
        return resultado(False, "el informe menciona ROAS — ETAPA-7 mide por CPA, nunca por ROAS")
    if not CPA_RE.search(output):
        return resultado(False, "no se citó ningún CPA en Quetzales")
    if not INTEGRIDAD_RE.search(output):
        return resultado(False, "falta la declaración de integridad de la ventana")
    if not SANGRADO_RE.search(output):
        return resultado(False, "falta el sangrado cuantificado en Q (PASO 3, obligatorio)")
    if not MATRIZ_O_DIMENSION_RE.search(output):
        return resultado(False, "falta la lectura por cuenta/dimensión que separa cuenta rota de ángulo malo")
    return resultado(True, "CPA citado sin ROAS, integridad de ventana, sangrado en Q y lectura por dimensión presentes")
