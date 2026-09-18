"""Las pruebas corren contra la carpeta REAL del sistema.

Es deliberado: el Hito 1 es de solo lectura y lo que se verifica es justamente que la API
diga lo mismo que los CSV del sistema. Un fixture de juguete probaría el fixture. Si algún
día una prueba necesita escribir, usa `--base` sobre una copia, nunca la carpeta real.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


def _base_del_sistema() -> Path:
    declarada = os.environ.get("VITALCOM_BASE")
    if declarada:
        return Path(declarada).resolve()
    # app/backend/tests → app/backend → app → worktree; el sistema real es la carpeta
    # que tenga DOCTRINA/FLUJO.json, empezando por acá.
    for candidata in Path(__file__).resolve().parents:
        if (candidata / "DOCTRINA" / "FLUJO.json").is_file():
            return candidata
    raise RuntimeError("declarar VITALCOM_BASE para correr las pruebas")


@pytest.fixture(scope="session", autouse=True)
def base_declarada() -> Path:
    base = _base_del_sistema()
    os.environ["VITALCOM_BASE"] = str(base)
    return base


@pytest.fixture(scope="session")
def cliente(base_declarada: Path) -> TestClient:
    from vitalcom_app.main import app

    return TestClient(app)
