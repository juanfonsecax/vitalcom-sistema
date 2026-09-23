"""etapa-8 — plan de escalado (DOCTRINA/ESCALADO_PLAYBOOK.md, CALENDARIO_ESCALADO.md).
Chequeo mecánico de las piezas que la doctrina exige en cualquier plan de
escalado real: Break-Even citado, la regla de oro (se escala lo que YA
vende), el tope de surfing +20%/día, y una lista de conjuntos ganadores con
evidencia numérica (no una recomendación sin data detrás)."""
from __future__ import annotations

import re

from _util import resultado

REQUISITOS = {
    "Break-Even declarado": re.compile(r"(?i)break-even"),
    "Regla de oro (se escala lo que YA vende)": re.compile(r"(?i)regla de oro"),
    "Tope de surfing +20%/día": re.compile(r"(?i)surfing.{0,20}20\s*%"),
    "Ganadores con evidencia de ventas": re.compile(r"(?i)ganador"),
}
VENTA_RE = re.compile(r"(?i)\d+\s*ventas?\b")


def get_assert(output: str, context: dict) -> dict:
    faltantes = [nombre for nombre, patron in REQUISITOS.items() if not patron.search(output)]
    if faltantes:
        return resultado(False, f"faltan piezas obligatorias del plan de escalado: {faltantes}")
    if not VENTA_RE.search(output):
        return resultado(False, "no hay evidencia numérica de ventas detrás de los conjuntos ganadores")
    return resultado(True, "Break-Even, regla de oro, tope de surfing y evidencia de ventas presentes")
