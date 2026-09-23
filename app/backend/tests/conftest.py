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


@pytest.fixture()
def sistema_de_juguete(tmp_path: Path, base_declarada: Path, monkeypatch, request):
    """Un sistema de mentira (ver `sistema_de_juguete.py`) con el manifiesto v7 real adentro.

    La base de datos de la app (DBOS) va a otra carpeta temporal: nunca dentro del sistema.
    Con `@pytest.mark.parametrize("sistema_de_juguete", [{"manifiesto": ..., "flujo": ...}],
    indirect=True)` una prueba puede instalar su propio manifiesto y/o `FLUJO.json` (autoconsistentes
    entre sí: V20 exige que coincidan) en vez de los reales — p. ej. para conservar la cobertura de
    un paso de tipo script sin atarla a la secuencia real de una fase.
    """
    import json
    import sys

    import sistema_de_juguete as juguete
    from vitalcom_app import acciones, claude, config

    sistema = tmp_path / "sistema"
    sistema.mkdir()
    personalizado = getattr(request, "param", None) or {}
    juguete.crear(sistema, manifiesto=personalizado.get("manifiesto"), flujo=personalizado.get("flujo"))
    monkeypatch.setenv("VITALCOM_BASE", str(sistema))
    monkeypatch.setenv("VITALCOM_DATOS", str(tmp_path / "datos"))
    # Ninguna prueba llama al Claude real: el falso habla el mismo stream-json.
    monkeypatch.setenv("VITALCOM_CLAUDE_CMD", json.dumps([sys.executable, str(Path(__file__).with_name("fake_claude.py"))]))
    for prohibida in ("ANTHROPIC_API_KEY", "CLAUDE_CODE_OAUTH_TOKEN"):
        monkeypatch.delenv(prohibida, raising=False)
    config.base.cache_clear()
    acciones.olvidar_cache()
    claude.olvidar_sesion()
    try:
        yield sistema
    finally:
        monkeypatch.setenv("VITALCOM_BASE", str(base_declarada))
        config.base.cache_clear()
        acciones.olvidar_cache()
        claude.olvidar_sesion()


@pytest.fixture()
def cliente_juguete(sistema_de_juguete: Path):
    """La app completa sobre el sistema de juguete, con DBOS lanzado (lifespan)."""
    from vitalcom_app.main import app

    with TestClient(app) as cliente:
        yield cliente
