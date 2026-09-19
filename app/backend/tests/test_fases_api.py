"""test_fases_api.py — pruebas de los endpoints de FASE 2, FASE 3 y reingreso."""

from __future__ import annotations

from unittest.mock import patch
from fastapi.testclient import TestClient

from vitalcom_app.main import app

cliente = TestClient(app)


def test_api_fase2_tinnidrop():
    res = cliente.get("/api/productos/TINNIDROP/fase2")
    assert res.status_code == 200
    data = res.json()
    assert data["producto_key"] == "TINNIDROP"
    assert data["fase"] == "F2"
    assert "angulo_ganador" in data
    assert "conceptos" in data
    assert len(data["conceptos"]) == 10
    # Cada concepto debe traer blueprint y prompt
    for c in data["conceptos"]:
        assert "canonico_id" in c
        assert "blueprint_nombre" in c
        assert "prompt" in c
        assert "estado" in c
    # Módulo de fatiga
    assert "fatiga" in data
    assert "angulos_probados" in data["fatiga"]
    assert "ACCESIBILIDAD_MEDICO" in data["fatiga"]["angulos_probados"]


def test_api_fase3_tinnidrop():
    res = cliente.get("/api/productos/TINNIDROP/fase3")
    assert res.status_code == 200
    data = res.json()
    assert data["producto_key"] == "TINNIDROP"
    assert "gate_2de2" in data
    assert "ok" in data["gate_2de2"]
    assert "observado" in data["gate_2de2"]
    assert "plan_cbo" in data
    assert data["plan_cbo"]["estructura"] == "1-1-7 CBO"
    assert "expansion" in data
    assert "cuentas_activas" in data["expansion"]


def test_api_reingreso_f1_endpoint():
    with patch("vitalcom_app.contratos.reingreso_f1") as mock_reingreso:
        mock_reingreso.return_value = {
            "ok": True,
            "producto_key": "TINNIDROP",
            "evento": "REINGRESO_F1",
            "fase_origen": "F2",
            "fase_destino": "F1",
            "angulos_excluidos": ["ACCESIBILIDAD_MEDICO"],
            "motivo": "Fatiga probada",
            "dry_run": False
        }
        res = cliente.post("/api/productos/TINNIDROP/reingreso-f1", json={"motivo": "Fatiga probada"})
        assert res.status_code == 200
        data = res.json()
        assert data["ok"] is True
        assert data["producto_key"] == "TINNIDROP"
        assert data["fase_destino"] == "F1"
        assert "ACCESIBILIDAD_MEDICO" in data["angulos_excluidos"]
