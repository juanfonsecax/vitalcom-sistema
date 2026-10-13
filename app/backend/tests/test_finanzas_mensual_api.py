"""`/api/resultados/mensual` y su carga, sobre los scripts REALES de finanzas (T4).

Mismo criterio que `test_resultados_api.py`: el sistema de juguete trae el manifiesto real (así que
las acciones `finanzas.*` pasan por las reglas de verdad) y se le copian encima los scripts del
repositorio. El banco se prueba con el script falso del juguete (un PDF real no se arma acá): lo
que se congela es el cableado, no el parser, que tiene su propio test en `Ads/_TOOLS`.
"""

from __future__ import annotations

import csv
import datetime
import io
import json
import shutil
from pathlib import Path

import openpyxl
import pytest
from fastapi.testclient import TestClient

from sistema_de_juguete import llamadas
from test_resultados_api import COLUMNAS_DROPI, PARAMETROS_FINANZAS

SCRIPTS_REALES = ("gen_pl.py", "gen_pl_mensual.py", "ingerir_dropi.py", "ingerir_banco.py")
XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def _script_del_repo(nombre: str) -> Path:
    return Path(__file__).resolve().parents[3] / "Ads" / "_TOOLS" / nombre


@pytest.fixture()
def sistema_falso(sistema_de_juguete: Path) -> Path:
    for nombre in SCRIPTS_REALES:
        shutil.copy2(_script_del_repo(nombre), sistema_de_juguete / "Ads" / "_TOOLS" / nombre)
    filas = PARAMETROS_FINANZAS + [
        {"parametro": "reparto_gasto_compartido", "valor": "ACTIVOS_IGUAL", "unidad": "", "origen": "",
         "medido_el": "", "n_evidencia": "", "notas": ""}]
    with io.open(sistema_de_juguete / "PRODUCTOS" / "_PARAMETROS_FINANZAS.csv", "w",
                 encoding="utf-8", newline="") as fh:
        escritor = csv.DictWriter(fh, fieldnames=list(PARAMETROS_FINANZAS[0]))
        escritor.writeheader()
        escritor.writerows(filas)
    return sistema_de_juguete


@pytest.fixture()
def cliente_falso(sistema_falso: Path, cliente_juguete: TestClient) -> TestClient:
    return cliente_juguete


def _dropi_xlsx(desde: datetime.date) -> bytes:
    def fila(id_, estatus, fecha, ganancia):
        return {"ID": id_, "PRODUCTO": "PRODUCTO DE PRUEBA", "ESTATUS": estatus,
                "FECHA": fecha.strftime("%d-%m-%Y"), "FECHA DE ÚLTIMO MOVIMIENTO": fecha.strftime("%d-%m-%Y"),
                "TOTAL DE LA ORDEN": 250.0, "PRECIO FLETE": 30.0, "PRECIO PROVEEDOR X CANTIDAD": 60.0,
                "GANANCIA": ganancia}
    filas = [fila(1, "ENTREGADO", desde, 160.0),
             fila(2, "DEVOLUCION", desde + datetime.timedelta(days=1), 0.0)]
    libro = openpyxl.Workbook()
    hoja = libro.active
    hoja.append(COLUMNAS_DROPI)
    for f in filas:
        hoja.append([f[c] for c in COLUMNAS_DROPI])
    salida = io.BytesIO()
    libro.save(salida)
    return salida.getvalue()


def test_sin_datos_el_mensual_sale_vacio_y_lo_dice(cliente_falso: TestClient) -> None:
    r = cliente_falso.get("/api/resultados/mensual", params={"mercado": "GT"})
    assert r.status_code == 200, r.text
    cuerpo = r.json()
    assert cuerpo["mercado"] == "GT"
    assert cuerpo["meses"] == []
    assert any("todavía no hay" in x.lower() for x in cuerpo["faltantes"])


def test_colombia_sale_vacia_con_su_nota(cliente_falso: TestClient) -> None:
    cuerpo = cliente_falso.get("/api/resultados/mensual", params={"mercado": "CO"}).json()
    assert cuerpo["meses"] == []
    assert any("Colombia" in x for x in cuerpo["faltantes"])


def test_un_mercado_que_no_existe_es_422(cliente_falso: TestClient) -> None:
    assert cliente_falso.get("/api/resultados/mensual", params={"mercado": "XX"}).status_code == 422


def test_cargar_un_dropi_lo_guarda_y_el_mensual_lo_muestra(cliente_falso: TestClient, sistema_falso: Path) -> None:
    desde = datetime.date(2024, 3, 1)
    r = cliente_falso.post("/api/resultados/mensual/cargar",
                           files={"dropi": ("ordenes_productos_20240310_090000.xlsx", _dropi_xlsx(desde), XLSX)})
    assert r.status_code == 201, r.text
    assert r.json()["dropi"]["nuevas"] == 2
    assert (sistema_falso / "PRODUCTOS" / "_FACT_ORDENES_DROPI.csv").is_file()

    mes = cliente_falso.get("/api/resultados/mensual", params={"mercado": "GT"}).json()["meses"][0]
    assert mes["mes"] == "2024-03"
    assert mes["ordenes"]["entregadas"] == 1
    assert mes["ordenes"]["devueltas"] == 1
    assert mes["preliminar"] is False


def test_cargar_dos_veces_lo_mismo_no_duplica(cliente_falso: TestClient) -> None:
    desde = datetime.date(2024, 3, 1)
    archivo = {"dropi": ("ordenes_productos_20240310_090000.xlsx", _dropi_xlsx(desde), XLSX)}
    cliente_falso.post("/api/resultados/mensual/cargar", files=archivo)
    otra = cliente_falso.post("/api/resultados/mensual/cargar", files=archivo)
    assert otra.status_code == 201
    assert otra.json()["dropi"]["nuevas"] == 0


def test_cargar_un_extracto_pasa_por_la_accion_con_banco_y_cuenta(cliente_falso: TestClient,
                                                                  sistema_falso: Path) -> None:
    # el script real del banco se reemplaza por el falso: acá se prueba el cableado de la acción
    from sistema_de_juguete import STUB, escribir_script

    escribir_script(sistema_falso, "ingerir_banco.py", STUB)
    r = cliente_falso.post("/api/resultados/mensual/cargar", data={"cuenta": "8889"},
                           files={"banco": ("Relay 2026-09-01 #8889.pdf", b"%PDF-1.4", "application/pdf")})
    assert r.status_code == 201, r.text
    assert r.json()["banco"] == {"ok": True}
    llamada = [x for x in llamadas(sistema_falso) if x["script"] == "ingerir_banco.py"][0]["argv"]
    assert "--escribir" in llamada and "--json" in llamada
    assert llamada[llamada.index("--banco") + 1] == "RELAY"
    assert llamada[llamada.index("--cuenta") + 1] == "8889"


def test_sin_archivos_es_422(cliente_falso: TestClient) -> None:
    assert cliente_falso.post("/api/resultados/mensual/cargar", data={}).status_code == 422


def test_una_cuenta_mal_escrita_es_422(cliente_falso: TestClient) -> None:
    r = cliente_falso.post("/api/resultados/mensual/cargar", data={"cuenta": "88"},
                           files={"banco": ("x.pdf", b"%PDF-1.4", "application/pdf")})
    assert r.status_code == 422


def test_el_export_roto_no_se_guarda_y_el_detalle_llega(cliente_falso: TestClient, sistema_falso: Path) -> None:
    libro = openpyxl.Workbook()
    libro.active.append(["ID", "ESTATUS"])
    libro.active.append([1, "ENTREGADO"])
    salida = io.BytesIO()
    libro.save(salida)
    r = cliente_falso.post("/api/resultados/mensual/cargar", files={"dropi": ("roto.xlsx", salida.getvalue(), XLSX)})
    assert r.status_code == 422
    assert not (sistema_falso / "PRODUCTOS" / "_FACT_ORDENES_DROPI.csv").exists()


def test_el_viejo_cargar_pl_tambien_guarda_el_dropi(cliente_falso: TestClient, sistema_falso: Path) -> None:
    ini = datetime.date(2024, 3, 1)
    r = cliente_falso.post("/api/resultados/cargar",
                           data={"desde": ini.isoformat(), "hasta": (ini + datetime.timedelta(days=1)).isoformat()},
                           files={"dropi": ("ordenes_productos_20240310_090000.xlsx", _dropi_xlsx(ini), XLSX)})
    assert r.status_code == 201, r.text
    assert r.json()["persistido"]["dropi"]["nuevas"] == 2
    assert (sistema_falso / "PRODUCTOS" / "_FACT_ORDENES_DROPI.csv").is_file()


def test_si_guardar_falla_el_pl_igual_se_entrega_y_el_error_se_dice(cliente_falso: TestClient,
                                                                   sistema_falso: Path) -> None:
    from sistema_de_juguete import escribir_script

    escribir_script(sistema_falso, "ingerir_dropi.py", "import sys\nprint('no pude', file=sys.stderr)\nsys.exit(1)\n")
    ini = datetime.date(2024, 3, 1)
    r = cliente_falso.post("/api/resultados/cargar",
                           data={"desde": ini.isoformat(), "hasta": (ini + datetime.timedelta(days=1)).isoformat()},
                           files={"dropi": ("ordenes.xlsx", _dropi_xlsx(ini), XLSX)})
    assert r.status_code == 201, r.text
    assert "error" in r.json()["persistido"]["dropi"]
    assert r.json()["vista_a_cohorte"]["entregadas"] == 1


def test_el_get_de_resultados_no_incluye_lo_persistido(cliente_falso: TestClient) -> None:
    ini = datetime.date(2024, 3, 1)
    cuerpo = cliente_falso.post("/api/resultados/cargar",
                                data={"desde": ini.isoformat(), "hasta": (ini + datetime.timedelta(days=1)).isoformat()},
                                files={"dropi": ("ordenes_productos_20240310_090000.xlsx", _dropi_xlsx(ini), XLSX)}).json()
    leido = cliente_falso.get("/api/resultados").json()
    assert leido == {k: v for k, v in cuerpo.items() if k != "persistido"}
    assert json.dumps(leido)  # serializable
