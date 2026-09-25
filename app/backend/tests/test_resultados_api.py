"""`/api/resultados` corre el `gen_pl.py` REAL sobre un Dropi de juguete (T4b, 24-sep-2026).

Mismo criterio que `test_alta_por_la_app.py`: el sistema de juguete trae el manifiesto v7 real
(así que `resultados.cargar_pl` pasa por las 21 reglas de verdad), pero se le copia encima el
`gen_pl.py` de ESTE repositorio en vez del stub genérico — la prueba ejercita el script real, no
un `{"ok": true}` de mentira.
"""

from __future__ import annotations

import csv
import datetime
import io
import shutil
from pathlib import Path

import openpyxl
import pytest
from fastapi.testclient import TestClient

PARAMETROS_FINANZAS = [
    {"parametro": "tasa_usd_gtq", "valor": "7.62", "unidad": "", "origen": "", "medido_el": "", "n_evidencia": "", "notas": ""},
    {"parametro": "costo_devolucion_evento_q", "valor": "28.02", "unidad": "", "origen": "", "medido_el": "", "n_evidencia": "", "notas": ""},
    {"parametro": "costo_admin_q", "valor": "4.00", "unidad": "", "origen": "", "medido_el": "", "n_evidencia": "", "notas": ""},
    {"parametro": "otros_gastos_q", "valor": "2.08", "unidad": "", "origen": "", "medido_el": "", "n_evidencia": "", "notas": ""},
    {"parametro": "dias_cohorte_maduro", "valor": "10", "unidad": "", "origen": "", "medido_el": "", "n_evidencia": "", "notas": ""},
]


def _script_del_repo(nombre: str) -> Path:
    repo = Path(__file__).resolve().parents[3]
    return repo / "Ads" / "_TOOLS" / nombre


@pytest.fixture()
def sistema_falso(sistema_de_juguete: Path) -> Path:
    """El sistema de juguete con el `gen_pl.py` REAL adentro y `_PARAMETROS_FINANZAS.csv` seteado."""
    shutil.copy2(_script_del_repo("gen_pl.py"), sistema_de_juguete / "Ads" / "_TOOLS" / "gen_pl.py")
    with io.open(sistema_de_juguete / "PRODUCTOS" / "_PARAMETROS_FINANZAS.csv", "w",
                 encoding="utf-8", newline="") as fh:
        escritor = csv.DictWriter(fh, fieldnames=list(PARAMETROS_FINANZAS[0]))
        escritor.writeheader()
        escritor.writerows(PARAMETROS_FINANZAS)
    return sistema_de_juguete


@pytest.fixture()
def cliente_falso(sistema_falso: Path, cliente_juguete: TestClient) -> TestClient:
    return cliente_juguete


COLUMNAS_DROPI = [
    "ID", "PRODUCTO", "ESTATUS", "FECHA", "FECHA DE ÚLTIMO MOVIMIENTO",
    "TOTAL DE LA ORDEN", "PRECIO FLETE", "PRECIO PROVEEDOR X CANTIDAD", "GANANCIA",
]


def _dropi_xlsx_bytes(desde: datetime.date) -> bytes:
    filas = [
        {"ID": 1, "PRODUCTO": "PRODUCTO DE PRUEBA", "ESTATUS": "ENTREGADO",
         "FECHA": desde.strftime("%d-%m-%Y"), "FECHA DE ÚLTIMO MOVIMIENTO": desde.strftime("%d-%m-%Y"),
         "TOTAL DE LA ORDEN": 250.0, "PRECIO FLETE": 30.0, "PRECIO PROVEEDOR X CANTIDAD": 60.0,
         "GANANCIA": 160.0},
        {"ID": 2, "PRODUCTO": "PRODUCTO DE PRUEBA", "ESTATUS": "DEVOLUCION",
         "FECHA": (desde + datetime.timedelta(days=1)).strftime("%d-%m-%Y"),
         "FECHA DE ÚLTIMO MOVIMIENTO": (desde + datetime.timedelta(days=1)).strftime("%d-%m-%Y"),
         "TOTAL DE LA ORDEN": 250.0, "PRECIO FLETE": 30.0, "PRECIO PROVEEDOR X CANTIDAD": 60.0,
         "GANANCIA": 0.0},
    ]
    libro = openpyxl.Workbook()
    hoja = libro.active
    hoja.append(COLUMNAS_DROPI)
    for fila in filas:
        hoja.append([fila[c] for c in COLUMNAS_DROPI])
    salida = io.BytesIO()
    libro.save(salida)
    return salida.getvalue()


def test_sin_carga_previa_da_404(cliente_falso: TestClient) -> None:
    respuesta = cliente_falso.get("/api/resultados")
    assert respuesta.status_code == 404
    assert "cargar" in respuesta.json()["detail"].lower()


def test_cargar_y_leer_el_pl_real(cliente_falso: TestClient, sistema_falso: Path) -> None:
    ini = datetime.date(2024, 3, 1)
    fin = ini + datetime.timedelta(days=1)
    respuesta = cliente_falso.post(
        "/api/resultados/cargar",
        data={"desde": ini.isoformat(), "hasta": fin.isoformat()},
        files={"dropi": ("ordenes.xlsx", _dropi_xlsx_bytes(ini),
                          "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )
    assert respuesta.status_code == 201, respuesta.text
    cuerpo = respuesta.json()
    assert cuerpo["ok"] is True
    vista_a = cuerpo["vista_a_cohorte"]
    assert vista_a["entregadas"] == 1
    assert vista_a["devueltas"] == 1
    assert vista_a["preliminar"] is False  # el período (2024) es viejo: ya pasó dias_cohorte_maduro=10

    # el .json quedó en _AUDITORIAS/, igual que lo prueba T4a sobre el script solo
    base = "_PL_%s_%s" % (ini.isoformat().replace("-", ""), fin.isoformat().replace("-", ""))
    assert (sistema_falso / "PRODUCTOS" / "_AUDITORIAS" / (base + ".json")).is_file()
    assert (sistema_falso / "PRODUCTOS" / "_AUDITORIAS" / (base + ".txt")).is_file()

    # GET /api/resultados sirve exactamente lo que gen_pl.py acaba de escribir
    leido = cliente_falso.get("/api/resultados")
    assert leido.status_code == 200
    assert leido.json() == cuerpo


def test_dropi_faltante_es_422(cliente_falso: TestClient) -> None:
    respuesta = cliente_falso.post("/api/resultados/cargar", data={})
    assert respuesta.status_code == 422


def test_historial_acumula_cada_periodo_cargado(cliente_falso: TestClient) -> None:
    assert cliente_falso.get("/api/resultados/historial").json() == []

    for mes in (3, 4):
        ini = datetime.date(2024, mes, 1)
        fin = ini + datetime.timedelta(days=1)
        respuesta = cliente_falso.post(
            "/api/resultados/cargar",
            data={"desde": ini.isoformat(), "hasta": fin.isoformat()},
            files={"dropi": ("ordenes.xlsx", _dropi_xlsx_bytes(ini),
                              "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        )
        assert respuesta.status_code == 201, respuesta.text

    historial = cliente_falso.get("/api/resultados/historial").json()
    assert len(historial) == 2
    assert [h["periodo"]["desde"] for h in historial] == ["2024-03-01", "2024-04-01"]
