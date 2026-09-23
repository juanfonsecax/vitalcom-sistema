"""etapa-fanpage — contrato: la página asignada debe existir en el catálogo
cerrado de las 10 FanPages que declara ETAPA-FANPAGE.md (cross-check real
contra la doctrina, no un valor libre inventado por el producto)."""
from __future__ import annotations

import re

from _util import resultado, leer_doctrina

NOMBRE_RE = re.compile(r"(?m)^\*\*\d+\.\s*(.+?)\*\*\s*$")


def _catalogo_fanpages() -> list[str]:
    doctrina = leer_doctrina(".claude/agents/ETAPA-FANPAGE.md")
    return [m.strip() for m in NOMBRE_RE.findall(doctrina)]


def get_assert(output: str, context: dict) -> dict:
    catalogo = _catalogo_fanpages()
    if not catalogo:
        return resultado(False, "no se pudo leer el catálogo de FanPages desde ETAPA-FANPAGE.md")
    encontrada = [nombre for nombre in catalogo if nombre in output]
    if not encontrada:
        return resultado(False, f"ninguna de las {len(catalogo)} FanPages del catálogo aparece citada en el fixture")
    return resultado(True, f"FanPage asignada coincide con el catálogo: {encontrada[0]!r}")
