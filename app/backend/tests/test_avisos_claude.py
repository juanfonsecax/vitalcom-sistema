"""test_avisos_claude.py — el campo `avisos_claude` del contrato de la pantalla Hoy (`/api/ordenes`).

Vacío cuando no hace falta Claude (la pantalla no muestra nada); con items cuando el control D+1
(`Ads/_TOOLS/control_d1.py`) encuentra un conjunto ciego. Se aísla del `gen_ordenes.py` real.
"""

from __future__ import annotations

import sys

import pytest
from fastapi.testclient import TestClient

from vitalcom_app import contratos
from vitalcom_app.main import app

cliente = TestClient(app)

AVISO = {
    "codigo": "CONJUNTO_CIEGO",
    "severidad": "alta",
    "motivo": "El conjunto X gastó y Meta registra conversaciones, pero LucidSales no registra ninguna.",
    "pedirle_a_claude": "Pausá por MCP el conjunto X (123): Meta registra conversaciones y LucidSales ninguna, "
    "el tracking está ciego.",
    "objetos": [{"id": "123", "nombre": "X"}],
}


@pytest.fixture()
def ordenes_aisladas(monkeypatch):
    monkeypatch.setattr(contratos, "ordenes", lambda producto_key=None: {"schema": "ordenes/1", "ordenes": []})
    monkeypatch.setattr(contratos, "parametros_decision", lambda: [])


def test_ordenes_sin_avisos_trae_lista_vacia(ordenes_aisladas, monkeypatch):
    monkeypatch.setattr(contratos, "avisos_claude", lambda: [])
    res = cliente.get("/api/ordenes")
    assert res.status_code == 200
    assert res.json()["avisos_claude"] == []


def test_ordenes_con_aviso_lo_trae_completo(ordenes_aisladas, monkeypatch):
    monkeypatch.setattr(contratos, "avisos_claude", lambda: [AVISO])
    res = cliente.get("/api/ordenes")
    assert res.status_code == 200
    assert res.json()["avisos_claude"] == [AVISO]


def test_filtro_por_producto_no_trae_avisos_del_sistema(ordenes_aisladas, monkeypatch):
    monkeypatch.setattr(contratos, "avisos_claude", lambda: [AVISO])
    res = cliente.get("/api/ordenes?producto=TINNIDROP")
    assert res.status_code == 200
    assert res.json()["avisos_claude"] == []


def test_contrato_avisos_claude_delega_en_control_d1(monkeypatch):
    contratos.avisos_claude()  # asegura que control_d1 quedó importado desde Ads/_TOOLS
    control_d1 = sys.modules["control_d1"]
    monkeypatch.setattr(control_d1, "avisos_claude", lambda: [AVISO])
    assert contratos.avisos_claude() == [AVISO]


def test_contrato_avisos_claude_si_el_control_falla_queda_vacio(monkeypatch):
    contratos.avisos_claude()
    control_d1 = sys.modules["control_d1"]

    def roto():
        raise RuntimeError("csv corrupto")

    monkeypatch.setattr(control_d1, "avisos_claude", roto)
    assert contratos.avisos_claude() == []
