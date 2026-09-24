"""etapa-fanpage (retargeted T1 p2-simplificacion) — contrato: la página asignada
debe existir en el catálogo cerrado de las 10 FanPages, hoy DATA en
`PRODUCTOS/_DIM_FANPAGES.csv` (cross-check real contra el CSV, no un valor libre
inventado por el producto).

Este fixture es anterior a la fusión: lo produjo el extinto agente
`etapa-fanpage` (eliminado T1 p2-simplificacion), corriendo en paralelo con
`etapa-2`. El JUICIO de asignación (reglas F1-F5) vive ahora en
`.claude/agents/ETAPA-2.md` §ASIGNACIÓN DE FANPAGE, que emite el mismo bloque
`<pagina_asignada>` — este assert por eso ya no lee la doctrina de un agente
(no existe más), sino el catálogo de datos que ambos, viejo y nuevo dueño,
comparten. Ver evals/README.md para el detalle del retargeting.
"""
from __future__ import annotations

import csv

from _util import resultado, REPO_ROOT
import os


def _catalogo_fanpages() -> list[str]:
    ruta = os.path.join(REPO_ROOT, "PRODUCTOS", "_DIM_FANPAGES.csv")
    with open(ruta, encoding="utf-8", newline="") as fh:
        filas = list(csv.DictReader(fh))
    return [fila["pagina_nombre"].strip() for fila in filas if fila.get("pagina_nombre")]


def get_assert(output: str, context: dict) -> dict:
    catalogo = _catalogo_fanpages()
    if not catalogo:
        return resultado(False, "no se pudo leer el catálogo de FanPages desde PRODUCTOS/_DIM_FANPAGES.csv")
    encontrada = [nombre for nombre in catalogo if nombre in output]
    if not encontrada:
        return resultado(False, f"ninguna de las {len(catalogo)} FanPages del catálogo aparece citada en el fixture")
    return resultado(True, f"FanPage asignada coincide con el catálogo: {encontrada[0]!r}")
