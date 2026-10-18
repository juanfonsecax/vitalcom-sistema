"""`fase2_detalle.publicaciones`: un botón «Ya publiqué la campaña — verificar» por brazo con paquete.

El brazo lo decide la existencia de `PRODUCTOS/<carpeta>/_PUBLICACION_F2<brazo>.json`; la pantalla no
adivina brazos ni arma parámetros.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from test_fase2_angulos import PARAMETROS, sistema_angulos  # noqa: F401

ACCION = "publicacion.verificar_publicada"


@pytest.fixture()
def habilitada(monkeypatch: pytest.MonkeyPatch):
    from vitalcom_app import contratos

    monkeypatch.setattr(contratos, "_accion_habilitada", lambda accion_id: True)
    monkeypatch.setattr(contratos, "_trabajo_en_curso", lambda accion_id, pk, angulo: None)


def _detalle() -> dict:
    from vitalcom_app import contratos
    from vitalcom_app.modelos import Fase2Detalle

    detalle = contratos.fase2_detalle("PX")
    Fase2Detalle(**detalle)
    return detalle


def _paquete(base: Path, brazo: str) -> None:
    carpeta = base / "PRODUCTOS" / "PX"
    carpeta.mkdir(parents=True, exist_ok=True)
    (carpeta / f"_PUBLICACION_F2{brazo}.json").write_text("{}", encoding="utf-8")


def test_un_boton_por_brazo_con_paquete(sistema_angulos: Path, habilitada):
    (sistema_angulos / "PRODUCTOS" / "_PARAMETROS_PUBLICACION.csv").write_text(PARAMETROS, encoding="utf-8")
    _paquete(sistema_angulos, "A")
    _paquete(sistema_angulos, "C")
    pub = _detalle()["publicaciones"]
    assert [p["brazo"] for p in pub] == ["A", "C"]
    assert pub[1] == {
        "brazo": "C", "accion_id": ACCION, "habilitada": True,
        "parametros": {"producto_key": "PX", "fase": "2", "brazo": "C"},
    }


def test_sin_paquetes_no_hay_botones(sistema_angulos: Path, habilitada):
    assert _detalle()["publicaciones"] == []


def test_accion_deshabilitada_se_dice(sistema_angulos: Path, monkeypatch: pytest.MonkeyPatch):
    from vitalcom_app import contratos

    monkeypatch.setattr(contratos, "_accion_habilitada", lambda accion_id: False)
    monkeypatch.setattr(contratos, "_trabajo_en_curso", lambda accion_id, pk, angulo: None)
    _paquete(sistema_angulos, "B")
    assert [p["habilitada"] for p in _detalle()["publicaciones"]] == [False]
