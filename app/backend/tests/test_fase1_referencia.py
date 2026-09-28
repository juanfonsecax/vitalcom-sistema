"""test_fase1_referencia.py — la referencia `ligera` fija de FASE 1 (A3, 28-sep-2026).

`contratos.referencia_f1` lee `PRODUCTOS/_DIM_REFERENCIA_F1.csv` (dueño único
`Ads/_TOOLS/referencia_f1.py`) y arma la URL servida por `GET /api/swipe/...`. Nunca fabrica
una referencia: sin fila, devuelve `referencia: None` + el comando exacto para elegirla.

Corre sobre un sistema mínimo de mentira, mismo patrón que test_fase2_prompt.py.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def sistema_min(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from vitalcom_app import config

    (tmp_path / "DOCTRINA").mkdir()
    (tmp_path / "DOCTRINA" / "FLUJO.json").write_text("{}", encoding="utf-8")
    (tmp_path / "PRODUCTOS").mkdir()
    banco = tmp_path / "Ads" / "_SWIPE" / "_BANCO_CREATIVOS" / "C2_BENEFICIOS"
    banco.mkdir(parents=True)
    (banco / "ligera__Camila-Recomienda__15_1364693855873597.jpg").write_bytes(b"\xff\xd8\xff\xe0fake-jpeg")
    monkeypatch.setenv("VITALCOM_BASE", str(tmp_path))
    config.base.cache_clear()
    try:
        yield tmp_path
    finally:
        config.base.cache_clear()


def _escribir_dim_referencia_f1(base: Path, filas: list[tuple[str, str, str, str]]) -> None:
    ruta = base / "PRODUCTOS" / "_DIM_REFERENCIA_F1.csv"
    lineas = ["producto_key,referencia,motivo,elegido_el"]
    lineas += [",".join(f'"{v}"' if "," in v else v for v in fila) for fila in filas]
    ruta.write_text("\r\n".join(lineas) + "\r\n", encoding="utf-8")


def test_referencia_f1_sin_fila_devuelve_null_y_el_comando(sistema_min: Path):
    from vitalcom_app import contratos

    resultado = contratos.referencia_f1("CLEARSTEM")
    assert resultado["referencia"] is None
    assert resultado["comando_elegir"] == (
        'python Ads/_TOOLS/referencia_f1.py --elegir CLEARSTEM <REFERENCIA> --motivo "..."'
    )


def test_referencia_f1_archivo_inexistente_devuelve_null(sistema_min: Path):
    """`_leer_csv` no explota si el CSV directamente no existe todavía (sin filas cargadas)."""
    from vitalcom_app import contratos

    (sistema_min / "PRODUCTOS" / "_DIM_REFERENCIA_F1.csv").unlink(missing_ok=True)
    resultado = contratos.referencia_f1("CLEARSTEM")
    assert resultado["referencia"] is None


def test_referencia_f1_con_fila_arma_la_url_de_swipe(sistema_min: Path):
    from vitalcom_app import contratos

    _escribir_dim_referencia_f1(sistema_min, [
        ("CLEARSTEM", "ligera__Camila-Recomienda__15_1364693855873597.jpg",
         "avatar mujer 25-40, dolor de piel", "2026-09-28"),
    ])
    resultado = contratos.referencia_f1("CLEARSTEM")
    assert resultado["comando_elegir"] is None
    referencia = resultado["referencia"]
    assert referencia["archivo"] == "ligera__Camila-Recomienda__15_1364693855873597.jpg"
    assert referencia["motivo"] == "avatar mujer 25-40, dolor de piel"
    assert referencia["elegido_el"] == "2026-09-28"
    assert referencia["url"] == (
        "/api/swipe/_BANCO_CREATIVOS/C2_BENEFICIOS/"
        "ligera__Camila-Recomienda__15_1364693855873597.jpg"
    )


def test_referencia_f1_solo_lee_la_fila_del_producto_pedido(sistema_min: Path):
    from vitalcom_app import contratos

    _escribir_dim_referencia_f1(sistema_min, [
        ("CLEARSTEM", "ligera__Camila-Recomienda__15_1364693855873597.jpg", "motivo A", "2026-09-28"),
        ("OTRO", "ligera__Tiendas-KetsalStore__14_1779511049710752.jpg", "motivo B", "2026-09-28"),
    ])
    resultado = contratos.referencia_f1("OTRO")
    assert resultado["referencia"]["archivo"] == "ligera__Tiendas-KetsalStore__14_1779511049710752.jpg"
    assert resultado["referencia"]["motivo"] == "motivo B"


def test_endpoint_swipe_sirve_la_referencia_f1(sistema_min: Path):
    from vitalcom_app.main import app

    cliente = TestClient(app)
    res = cliente.get(
        "/api/swipe/_BANCO_CREATIVOS/C2_BENEFICIOS/ligera__Camila-Recomienda__15_1364693855873597.jpg"
    )
    assert res.status_code == 200


def test_campana_de_fase1_trae_la_referencia(sistema_min: Path, monkeypatch: pytest.MonkeyPatch):
    from vitalcom_app import fase1

    (sistema_min / "PRODUCTOS" / "_DIM_PRODUCTOS.csv").write_text(
        "producto_key,slug_carpeta,carpeta_media\nCLEARSTEM,CLEARSTEM,MEDIA_CLEARSTEM\n",
        encoding="utf-8",
    )
    _escribir_dim_referencia_f1(sistema_min, [
        ("CLEARSTEM", "ligera__Camila-Recomienda__15_1364693855873597.jpg",
         "avatar mujer 25-40", "2026-09-28"),
    ])
    resultado = fase1.campana("CLEARSTEM")
    assert resultado["referencia_f1"]["archivo"] == "ligera__Camila-Recomienda__15_1364693855873597.jpg"
    assert resultado["comando_elegir_referencia_f1"] is None


def test_campana_de_fase1_sin_referencia_trae_el_comando(sistema_min: Path):
    from vitalcom_app import fase1

    (sistema_min / "PRODUCTOS" / "_DIM_PRODUCTOS.csv").write_text(
        "producto_key,slug_carpeta,carpeta_media\nCLEARSTEM,CLEARSTEM,MEDIA_CLEARSTEM\n",
        encoding="utf-8",
    )
    resultado = fase1.campana("CLEARSTEM")
    assert resultado["referencia_f1"] is None
    assert resultado["comando_elegir_referencia_f1"] == (
        'python Ads/_TOOLS/referencia_f1.py --elegir CLEARSTEM <REFERENCIA> --motivo "..."'
    )
