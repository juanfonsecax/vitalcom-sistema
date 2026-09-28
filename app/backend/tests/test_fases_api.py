"""test_fases_api.py — pruebas de los endpoints de FASE 2, FASE 3, FASE 4 y reingreso."""

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


def test_api_fase4_tinnidrop():
    """TINNIDROP hoy está en F2 (real, sin fixture): sin concepto 2de2 todavía, así que F4 nunca
    se evalúa (`entradas` corta en F3) y `fase4_detalle` cae a los defaults — nunca revienta."""
    res = cliente.get("/api/productos/TINNIDROP/fase4")
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


def test_api_fase3_tinnidrop():
    """TINNIDROP en F2 (real): la pantalla F3 igual responde — entrada F3 sin cumplir, sin gate_f4
    (el producto ni siquiera entró a F3 todavía)."""
    res = cliente.get("/api/productos/TINNIDROP/fase3")
    assert res.status_code == 200
    data = res.json()
    assert data["producto_key"] == "TINNIDROP"
    assert "entrada" in data
    assert "ok" in data["entrada"]
    assert "observado" in data["entrada"]
    assert "eventos_cambio_bot" in data
    assert "entrada_f4" in data


def _flujo_fase3(fase, gate_f4, entrada_f3_ok=True, entrada_f4_ok=False):
    """Un `flujo.py --json` de mentira, con la forma exacta que `situar()` produce, para ejercitar
    `fase3_detalle` sin tocar data real (T8: producto con/sin CAMBIO_BOT y bajo/sobre el piso)."""
    return {
        "producto_key": "FIXTURE",
        "fase": fase,
        "nodo_actual": f"{fase}.reescribir" if fase == "F3" else f"{fase}.exploracion",
        "entradas": [
            {"fase": "F2", "ok": True, "observado": "ganador", "regla": ""},
            {"fase": "F3", "ok": entrada_f3_ok, "observado": "concepto 2de2", "regla": ""},
            {"fase": "F4", "ok": entrada_f4_ok, "observado": "gate F4", "regla": ""},
        ],
        "nodos": [
            {"id": "F3.reescribir", "titulo": "Reescribir", "ejecutor": "etapa-5", "ejecutor_tipo": "subagente",
             "como": "", "estado": "CUMPLIDO", "cumplido": True, "ciclo": False, "secuencia": []},
            {"id": "F3.medir_cierre", "titulo": "Medir cierre", "ejecutor": "script", "ejecutor_tipo": "script",
             "como": "", "estado": "PENDIENTE", "cumplido": False, "ciclo": False, "secuencia": []},
        ] if fase == "F3" else [],
        "cierre_post_cambio_bot": gate_f4,
    }


def test_api_fase3_sin_cambio_bot():
    """Producto en F3 sin CAMBIO_BOT todavía: `gate_f4.ok` es False y lo dice en `explicacion`,
    sin mensajes/ventas/cierre_pct (todos None)."""
    gate = {
        "fecha_cambio_bot": None, "mensajes": None, "ventas": None, "cierre_pct": None,
        "min_mensajes": 30, "min_cierre_pct": 10.0, "cierre_meta_min_pct": 15.0, "cierre_meta_max_pct": 20.0,
        "ok": False,
        "explicacion": "sin CAMBIO_BOT (ni EXCEPCION_CAMBIO_BOT) posterior al concepto ganador todavía",
    }
    with patch("vitalcom_app.contratos.flujo", return_value=_flujo_fase3("F3", gate)), \
         patch("vitalcom_app.contratos._leer_csv", return_value=[]):
        res = cliente.get("/api/productos/FIXTURE/fase3")
    assert res.status_code == 200
    data = res.json()
    assert data["fase"] == "F3"
    assert data["eventos_cambio_bot"] == []
    assert data["gate_f4"]["ok"] is False
    assert data["gate_f4"]["fecha_cambio_bot"] is None
    assert data["gate_f4"]["mensajes"] is None
    assert data["entrada_f4"]["ok"] is False


def test_api_fase3_cambio_bot_bajo_el_piso():
    """CAMBIO_BOT registrado, pero cierre (5%) bajo el piso de 10%: `gate_f4.ok` sigue False, el
    producto se queda en F3 (PROHIBIDO_ESCALAR_CIERRE_BAJO)."""
    gate = {
        "fecha_cambio_bot": "2026-09-20", "mensajes": 40.0, "ventas": 2.0, "cierre_pct": 5.0,
        "min_mensajes": 30, "min_cierre_pct": 10.0, "cierre_meta_min_pct": 15.0, "cierre_meta_max_pct": 20.0,
        "ok": False,
        "explicacion": "desde CAMBIO_BOT 2026-09-20: 40 mensaje(s) (≥30) · cierre 5.0% (≥10%)",
    }
    eventos = [{"producto_key": "FIXTURE", "evento": "CAMBIO_BOT", "fecha": "2026-09-20", "motivo": "reescritura etapa-5"}]
    with patch("vitalcom_app.contratos.flujo", return_value=_flujo_fase3("F3", gate)), \
         patch("vitalcom_app.contratos._leer_csv", return_value=eventos):
        res = cliente.get("/api/productos/FIXTURE/fase3")
    assert res.status_code == 200
    data = res.json()
    assert len(data["eventos_cambio_bot"]) == 1
    assert data["eventos_cambio_bot"][0]["evento"] == "CAMBIO_BOT"
    assert data["gate_f4"]["ok"] is False
    assert data["gate_f4"]["cierre_pct"] == 5.0
    assert data["gate_f4"]["min_cierre_pct"] == 10.0
    assert data["gate_f4"]["cierre_meta_min_pct"] == 15.0
    assert data["gate_f4"]["cierre_meta_max_pct"] == 20.0


def test_api_fase3_cambio_bot_sobre_el_piso_desbloquea_f4():
    """CAMBIO_BOT registrado y cierre (15%) sobre el piso de 10%: `gate_f4.ok` es True y el
    producto ya avanzó a F4 (`fase` del flujo)."""
    gate = {
        "fecha_cambio_bot": "2026-09-15", "mensajes": 40.0, "ventas": 6.0, "cierre_pct": 15.0,
        "min_mensajes": 30, "min_cierre_pct": 10.0, "cierre_meta_min_pct": 15.0, "cierre_meta_max_pct": 20.0,
        "ok": True,
        "explicacion": "desde CAMBIO_BOT 2026-09-15: 40 mensaje(s) (≥30) · cierre 15.0% (≥10%)",
    }
    eventos = [{"producto_key": "FIXTURE", "evento": "CAMBIO_BOT", "fecha": "2026-09-15", "motivo": "reescritura etapa-5"}]
    with patch("vitalcom_app.contratos.flujo", return_value=_flujo_fase3("F4", gate, entrada_f4_ok=True)), \
         patch("vitalcom_app.contratos._leer_csv", return_value=eventos):
        res = cliente.get("/api/productos/FIXTURE/fase3")
    assert res.status_code == 200
    data = res.json()
    assert data["fase"] == "F4"
    assert data["gate_f4"]["ok"] is True
    assert data["entrada_f4"]["ok"] is True
    # ya en F4: `nodos` de F3 no viven más en el `flujo.py --json` del producto (fase vigente
    # cambió), así que los nodos de F3 no se pueden mostrar — la pantalla lo tolera con None.
    assert data["nodo_reescribir"] is None
    assert data["nodo_medir_cierre"] is None


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
