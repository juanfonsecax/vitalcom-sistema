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
import re

from _util import resultado, REPO_ROOT
import os


# La línea que ASIGNA la página, no cualquier mención: "PÁGINA ASIGNADA: 4 Belleza & Piel"
# (bloque <pagina_asignada> de etapa-2) o "- Página 4 ✨ Belleza & Piel" (fixture del agente
# extinto). Una página citada solo para descartarla ("la página 3 dejaría fuera...") no cuenta.
_LINEA_ASIGNADA = re.compile(r"^\s*(?:-\s*)?P[ÁA]GINA(?:\s+ASIGNADA:)?\s+(\d{1,2})\b(.*)$", re.IGNORECASE)


def _catalogo_fanpages() -> dict[str, str]:
    ruta = os.path.join(REPO_ROOT, "PRODUCTOS", "_DIM_FANPAGES.csv")
    with open(ruta, encoding="utf-8", newline="") as fh:
        filas = list(csv.DictReader(fh))
    return {fila["pagina_num"].strip(): fila["pagina_nombre"].strip()
            for fila in filas if fila.get("pagina_num") and fila.get("pagina_nombre")}


def get_assert(output: str, context: dict) -> dict:
    catalogo = _catalogo_fanpages()
    if not catalogo:
        return resultado(False, "no se pudo leer el catálogo de FanPages desde PRODUCTOS/_DIM_FANPAGES.csv")
    if "SIN PÁGINA IDEAL" in output.upper():
        return resultado(True, "Formato B: producto sin página ideal (regla F3)")
    asignadas = [m for m in (_LINEA_ASIGNADA.match(l) for l in output.splitlines()) if m]
    if not asignadas:
        return resultado(False, "no hay una línea que asigne página (ni 'PÁGINA ASIGNADA: N ...' ni '- Página N ...')")
    numero, resto = asignadas[0].group(1), asignadas[0].group(2)
    nombre = catalogo.get(numero)
    if nombre is None:
        return resultado(False, f"la página asignada #{numero} no existe en el catálogo de {len(catalogo)} FanPages")
    if nombre not in resto:
        return resultado(False, f"la página #{numero} se cita con un nombre distinto al del catálogo ({nombre!r})")
    return resultado(True, f"FanPage asignada #{numero} {nombre!r}, presente en el catálogo")
