"""Pruebas para la acción y workflow de respaldo de PRODUCTOS/ (Hito 7)."""

from __future__ import annotations

from unittest.mock import patch
from vitalcom_app import acciones, workflows


def test_accion_respaldo_declarada_y_valida():
    man = acciones.cargar()
    assert man.estado == "ok", f"Manifiesto no ok: {man.problemas}"
    acc = acciones.por_id_para_el_runner("sistema.respaldo_productos")
    assert acc["id"] == "sistema.respaldo_productos"
    assert acc["ejecutor_tipo"] == "script"
    assert "respaldo_productos.py" in acc["comando"][1]


def test_argv_de_accion_respaldo():
    acc = acciones.por_id_para_el_runner("sistema.respaldo_productos")
    argv = acciones.resolver(acc, {"dry_run": True})
    assert any("respaldo_productos.py" in arg for arg in argv)
    assert "--dry-run" in argv
    assert "--json" in argv


def test_ejecutar_respaldo_productos_retorna_estructura():
    with patch("vitalcom_app.workflows.encolar") as mock_encolar, \
         patch("vitalcom_app.workflows.esperar_resultado") as mock_wait:
        mock_encolar.return_value = ("test-jid", False)
        mock_wait.return_value = {
            "estado": "EXITO",
            "salida_estructurada": {"ok": True, "archivos_incluidos": 10},
        }
        res = workflows.ejecutar_respaldo_productos("test-respaldo-001")
        assert res["estado"] == "EXITO"
        assert res["job_id"] == "test-respaldo-001"
