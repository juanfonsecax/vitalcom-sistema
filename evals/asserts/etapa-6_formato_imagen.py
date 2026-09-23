"""etapa-6 — regla dura de FASE 1 (CLAUDE.md, decisión operador 22-sep-2026):
"FASE 1 corre TODO EN IMAGEN". Un `_PLAN.json` con fase=1 y algún conjunto en
VIDEO viola esa regla. Los planes escritos ANTES de esa fecha (CLEARSTEM,
NusavaB12, TINNIDROP — todos v1, sin fecha posterior a la decisión) quedan
documentados como fallo conocido en promptfooconfig.yaml (expected_fail),
exactamente los mismos que reporta `gen_plan.py --validar` hoy. No se debilita
este assert para que pasen: la regla es real y su violación real."""
from __future__ import annotations

import json

from _util import resultado


def get_assert(output: str, context: dict) -> dict:
    try:
        plan = json.loads(output)
    except json.JSONDecodeError as exc:
        return resultado(False, f"_PLAN.json no es JSON válido: {exc}")

    if str(plan.get("fase")) not in ("1", "F1", "FASE1"):
        return resultado(True, "no es un plan de FASE 1 — la regla todo-en-imagen no aplica")

    conjuntos = plan.get("conjuntos") or []
    no_imagen = [c.get("angulo_key") for c in conjuntos if c.get("formato") != "IMAGEN"]
    if no_imagen:
        return resultado(False, f"FASE 1 con conjunto(s) fuera de IMAGEN: {no_imagen}")
    return resultado(True, "todos los conjuntos de FASE 1 están en IMAGEN")
