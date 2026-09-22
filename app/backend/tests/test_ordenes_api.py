"""test_ordenes_api.py — pruebas de los endpoints /api/ordenes y /api/ganadores."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from vitalcom_app.main import app

cliente = TestClient(app)


def test_api_ordenes_devuelve_estructura_valida():
    res = cliente.get("/api/ordenes")
    assert res.status_code == 200
    datos = res.json()
    assert datos.get("schema") == "ordenes/1"
    assert "rezago_dias" in datos
    assert "ordenes" in datos
    assert isinstance(datos["ordenes"], list)
    assert len(datos["ordenes"]) > 0
    # Cada orden debe traer frase_simple y por_que
    primera = datos["ordenes"][0]
    assert "frase_simple" in primera
    assert "por_que" in primera
    assert "estado" in primera
    assert primera["estado"] in ("ESCALAR", "PAUSAR", "RENOVAR", "SEGUIR_MIDIENDO")


def test_api_ordenes_trae_los_relojes_del_motor():
    """`parametros_motor` es `_PARAMETROS_DECISION.csv` tal cual: la pantalla explica, no inventa."""
    res = cliente.get("/api/ordenes")
    assert res.status_code == 200
    parametros = res.json()["parametros_motor"]
    assert isinstance(parametros, list) and len(parametros) > 0
    por_nombre = {p["parametro"]: p for p in parametros}
    for clave in ("ventana_dias", "ventana_fatiga_dias", "duracion_testeo_fase2_dias"):
        assert clave in por_nombre, f"falta «{clave}»: no está en _PARAMETROS_DECISION.csv"
        assert por_nombre[clave]["valor"], f"«{clave}» no trae valor"


def test_api_ordenes_filtro_producto():
    res = cliente.get("/api/ordenes?producto=TINNIDROP")
    assert res.status_code == 200
    datos = res.json()
    assert all(o["producto_key"] == "TINNIDROP" for o in datos["ordenes"])


def test_api_ganadores_detecta_ganadores_fase2():
    res = cliente.get("/api/ganadores")
    assert res.status_code == 200
    ganadores = res.json()
    assert isinstance(ganadores, list)
    # En el estado actual, TINNIDROP y NUSAVA están en F2
    keys = [g["producto_key"] for g in ganadores]
    assert "TINNIDROP" in keys or "NUSAVA" in keys
    for g in ganadores:
        assert g["fase"] == "F2" or g["nodo_actual"].startswith("F2.")
        assert "siguiente_paso" in g
        assert g["siguiente_paso"]["etapa"] == "etapa-11" or "F2" in g["siguiente_paso"]["nodo"]
