"""Con VITALCOM_FUENTE=db la API responde EXACTAMENTE lo mismo que con VITALCOM_FUENTE=csv (P3 T5).

`contratos.py` lee producto/estado_flujo/_DECISIONES.json por Postgres cuando VITALCOM_FUENTE=db
(default desde T5) -- estas pruebas siembran un tenant ÚNICO en `vitalcom_test` a partir de un
sistema de juguete y comparan la respuesta de la API en los dos modos. Mismo patrón de aislamiento
que `test_alta_por_la_app.py`: nunca toca `vitalcom` real ni la base real.
"""

from __future__ import annotations

import json
import sys
import uuid
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

DB_DIR = str(Path(__file__).resolve().parents[3] / "db")
if DB_DIR not in sys.path:
    sys.path.insert(0, DB_DIR)
import cargar as db_cargar  # noqa: E402


def _conectar_seguro():
    con = db_cargar.conectar()
    if con.info.dbname == "vitalcom":
        con.close()
        raise RuntimeError(
            "test_lectura_desde_postgres.py intentó conectarse a 'vitalcom' en vez de "
            "'vitalcom_test'. Abortado antes de tocar nada."
        )
    return con


@pytest.fixture()
def sistema_con_postgres(sistema_de_juguete: Path, monkeypatch) -> tuple[Path, str]:
    """El sistema de juguete de `conftest.py`, con producto/estado_flujo/decisiones sembrados
    TAMBIÉN en Postgres (`vitalcom_test`), bajo un tenant único de esta prueba -- nunca el tenant
    "vitalcom" real ni la base real. Se salta con aviso si Postgres/vitalcom_test no está
    disponible en este entorno (mismo criterio que `test_alta_por_la_app.py`)."""
    monkeypatch.setenv("PGDATABASE", "vitalcom_test")
    tenant = "test_t5_%s" % uuid.uuid4().hex[:12]
    try:
        if db_cargar.asegurar_base_de_datos("vitalcom_test"):
            db_cargar.aplicar_schema(dbname="vitalcom_test")
        _conectar_seguro().close()
    except Exception as exc:
        pytest.skip("Postgres/vitalcom_test no disponible en este entorno: %s" % exc)

    # El juguete (`sistema_de_juguete.py:crear()`) no trae `_DECISIONES.json`: `/api/decisiones`
    # lo exige (`contratos.decisiones()` -> `ContratoAusente` si falta), así que esta prueba lo
    # declara -- mínimo válido para el modelo `Decisiones` (ver `vitalcom_app/modelos.py`).
    decisiones_toy = sistema_de_juguete / "PRODUCTOS" / "_DECISIONES.json"
    decisiones_toy.write_text(
        json.dumps(
            {"generado": "2026-09-25", "grano": "angulo", "productos": []},
            ensure_ascii=False, indent=2,
        ),
        encoding="utf-8",
    )
    for tabla in ("producto", "estado_flujo", "_DECISIONES.json"):
        db_cargar.tomar_csv(
            tabla, productos_dir=str(sistema_de_juguete / "PRODUCTOS"), tenant_id=tenant
        )

    monkeypatch.setenv("VITALCOM_DB_TENANT", tenant)
    return sistema_de_juguete, tenant


def _snapshot(cliente: TestClient) -> dict[str, Any]:
    return {
        "productos": cliente.get("/api/productos").json(),
        "producto_tinnidrop": cliente.get("/api/productos/TINNIDROP").json(),
        "decisiones": cliente.get("/api/decisiones").json(),
    }


def test_api_responde_igual_en_modo_db_que_en_modo_csv(
    sistema_con_postgres: tuple[Path, str], cliente_juguete: TestClient, monkeypatch
) -> None:
    monkeypatch.setenv("VITALCOM_FUENTE", "csv")
    esperado = _snapshot(cliente_juguete)

    monkeypatch.setenv("VITALCOM_FUENTE", "db")
    obtenido = _snapshot(cliente_juguete)

    assert obtenido == esperado
