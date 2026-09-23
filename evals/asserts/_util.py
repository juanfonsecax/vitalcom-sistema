"""Utilidades compartidas por los asserts de evals/. No es un stage: es soporte.

Cada assert de este directorio sigue la firma python-assert de promptfoo:
    def get_assert(output: str, context: dict) -> dict
donde `output` es el contenido crudo del fixture (tal como lo entrega el
provider `echo` sobre `vars.content`) y `context` es un dict con, al menos,
`vars` (las variables del test). Devolvemos siempre
`{"pass": bool, "score": 0.0|1.0, "reason": str}` — el shape que promptfoo
entiende nativamente para un GradingResult.
"""
from __future__ import annotations

import os

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def resultado(ok: bool, razon: str) -> dict:
    return {"pass": bool(ok), "score": 1.0 if ok else 0.0, "reason": razon}


def leer_doctrina(ruta_relativa: str) -> str:
    """Lee un archivo de doctrina/agente del repo (solo lectura) para
    cross-check — nunca un CSV de datos de PRODUCTOS/."""
    ruta = os.path.join(REPO_ROOT, ruta_relativa)
    with open(ruta, "r", encoding="utf-8") as fh:
        return fh.read()
