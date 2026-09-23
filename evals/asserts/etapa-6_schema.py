"""etapa-6 — esquema de `_PLAN.json` (contrato en ETAPA-6.md "OUTPUT OBLIGATORIO").
Chequeo estructural: claves de raíz, 1-6 conjuntos, y que cada conjunto trae
el contenido creativo que el plan SÍ debe llevar (nunca lo que gen_lanzador.py
deriva — ver la tabla de reparto de ETAPA-6.md)."""
from __future__ import annotations

import json

from _util import resultado

CLAVES_RAIZ = {"schema", "producto_key", "fase", "version", "pagina", "oferta", "conjuntos"}
CLAVES_CONJUNTO = {"angulo_key", "avatar_edad", "avatar_genero", "nivel_conciencia", "formato", "copy"}
FORMATOS_VALIDOS = {"IMAGEN", "VIDEO"}


def get_assert(output: str, context: dict) -> dict:
    try:
        plan = json.loads(output)
    except json.JSONDecodeError as exc:
        return resultado(False, f"_PLAN.json no es JSON válido: {exc}")

    faltantes_raiz = CLAVES_RAIZ - plan.keys()
    if faltantes_raiz:
        return resultado(False, f"faltan claves de raíz: {sorted(faltantes_raiz)}")

    conjuntos = plan.get("conjuntos")
    if not isinstance(conjuntos, list) or not conjuntos:
        return resultado(False, "conjuntos debe ser una lista no vacía")
    if len(conjuntos) > 6:
        return resultado(False, f"más de 6 conjuntos ({len(conjuntos)}) — FASE 1 son 6 ángulos, máximo")

    for i, c in enumerate(conjuntos, start=1):
        if not isinstance(c, dict):
            return resultado(False, f"conjunto {i} no es un objeto")
        faltantes = CLAVES_CONJUNTO - c.keys()
        if faltantes:
            return resultado(False, f"conjunto {i} ({c.get('angulo_key', '?')}) sin campos: {sorted(faltantes)}")
        if not str(c.get("angulo_key") or "").strip():
            return resultado(False, f"conjunto {i} con angulo_key vacío")
        if not str(c.get("copy") or "").strip():
            return resultado(False, f"conjunto {i} ({c['angulo_key']}) sin copy")
        if c.get("formato") not in FORMATOS_VALIDOS:
            return resultado(False, f"conjunto {i} ({c['angulo_key']}) con formato fuera de vocabulario: {c.get('formato')!r}")

    return resultado(True, f"_PLAN.json válido: {len(conjuntos)} conjunto(s), esquema completo")
