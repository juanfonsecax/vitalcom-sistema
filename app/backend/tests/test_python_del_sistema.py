"""python_del_sistema: los scripts de Ads/_TOOLS nunca corren con el venv de la app."""

from __future__ import annotations

import os
import sys

from vitalcom_app import config


def _ejecutable(carpeta, nombre="python.exe" if os.name == "nt" else "python"):
    carpeta.mkdir(parents=True, exist_ok=True)
    archivo = carpeta / nombre
    archivo.write_text("", encoding="utf-8")
    archivo.chmod(0o755)
    return archivo


def test_salta_el_python_del_venv_de_la_app(monkeypatch, tmp_path):
    venv = tmp_path / "venv"
    _ejecutable(venv / ("Scripts" if os.name == "nt" else "bin"))
    sistema = _ejecutable(tmp_path / "sistema")
    monkeypatch.delenv("VITALCOM_PYTHON", raising=False)
    monkeypatch.setattr(sys, "prefix", str(venv))
    monkeypatch.setenv("PATH", os.pathsep.join([str(venv / ("Scripts" if os.name == "nt" else "bin")), str(sistema.parent)]))
    assert os.path.normcase(config.python_del_sistema()) == os.path.normcase(str(sistema))


def test_salta_el_alias_de_la_microsoft_store(monkeypatch, tmp_path):
    alias = _ejecutable(tmp_path / "Microsoft" / "WindowsApps")
    sistema = _ejecutable(tmp_path / "sistema")
    monkeypatch.delenv("VITALCOM_PYTHON", raising=False)
    monkeypatch.setattr(sys, "prefix", str(tmp_path / "venv"))
    monkeypatch.setenv("PATH", os.pathsep.join([str(alias.parent), str(sistema.parent)]))
    assert os.path.normcase(config.python_del_sistema()) == os.path.normcase(str(sistema))


def test_vitalcom_python_declarado_manda(monkeypatch, tmp_path):
    monkeypatch.setenv("VITALCOM_PYTHON", "C:/otro/python.exe")
    assert config.python_del_sistema() == "C:/otro/python.exe"


def test_sin_otro_python_cae_al_nombre(monkeypatch, tmp_path):
    venv = tmp_path / "venv"
    _ejecutable(venv / ("Scripts" if os.name == "nt" else "bin"))
    monkeypatch.delenv("VITALCOM_PYTHON", raising=False)
    monkeypatch.setattr(sys, "prefix", str(venv))
    monkeypatch.setenv("PATH", str(venv / ("Scripts" if os.name == "nt" else "bin")))
    assert config.python_del_sistema() == "python"
