"""test_config.py -- la resolucion automatica de VITALCOM_BASE nunca acepta un worktree
vinculado de git como carpeta del sistema (g07-cimientos T8-1, 23-sep-2026).

`DOCTRINA/FLUJO.json` esta versionado: cualquier worktree vinculado (ej. SISTEMA-app, donde
se desarrolla) lo tiene tambien, asi que la deteccion automatica de `config._subiendo()` podia
terminar aceptando ESE worktree en vez de la carpeta principal duena de los datos reales
(PRODUCTOS/, Ads/MEDIA_*). Estas pruebas fabrican un repo git real con un worktree vinculado
(sin tocar el repo de este proyecto) y comprueban que la deteccion lo rechaza, mientras que la
carpeta principal y una carpeta sin git en absoluto siguen funcionando igual que antes.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from vitalcom_app import config


def _git(*args: str, cwd: Path) -> None:
    subprocess.run(["git", *args], cwd=str(cwd), check=True, capture_output=True, text=True)


@pytest.fixture()
def repo_con_worktree(tmp_path: Path):
    """Un repo git minimo con DOCTRINA/FLUJO.json commiteado, mas un worktree vinculado."""
    principal = tmp_path / "principal"
    principal.mkdir()
    _git("init", "-q", cwd=principal)
    _git("config", "user.email", "test@test.local", cwd=principal)
    _git("config", "user.name", "Test", cwd=principal)
    (principal / "DOCTRINA").mkdir()
    (principal / "DOCTRINA" / "FLUJO.json").write_text("{}", encoding="utf-8")
    _git("add", "-A", cwd=principal)
    _git("commit", "-q", "-m", "inicial", cwd=principal)

    vinculado = tmp_path / "vinculado"
    _git("worktree", "add", "-q", str(vinculado), "-b", "otra-rama", cwd=principal)

    return principal, vinculado


def test_worktree_vinculado_se_detecta(repo_con_worktree):
    _principal, vinculado = repo_con_worktree
    es, _principal_detectado = config._es_worktree_vinculado(vinculado)
    assert es is True


def test_carpeta_principal_no_es_worktree_vinculado(repo_con_worktree):
    principal, _vinculado = repo_con_worktree
    es, _ = config._es_worktree_vinculado(principal)
    assert es is False


def test_carpeta_sin_git_no_bloquea(tmp_path: Path):
    """Una carpeta que ni siquiera es un repo git (ej. el fixture de sistema_de_juguete) no debe
    fallar por falta de git -- solo se bloquea un worktree VINCULADO real."""
    es, principal = config._es_worktree_vinculado(tmp_path)
    assert es is False
    assert principal is None


def test_subiendo_se_niega_sobre_worktree_vinculado(repo_con_worktree):
    principal, vinculado = repo_con_worktree
    with pytest.raises(RuntimeError, match="worktree vinculado"):
        config._subiendo(vinculado)
    # y el mensaje nombra la carpeta principal para que el operador sepa donde correr la app
    try:
        config._subiendo(vinculado)
    except RuntimeError as exc:
        assert Path(principal).name in str(exc)


def test_subiendo_acepta_la_carpeta_principal(repo_con_worktree):
    principal, _vinculado = repo_con_worktree
    assert config._subiendo(principal) == principal
