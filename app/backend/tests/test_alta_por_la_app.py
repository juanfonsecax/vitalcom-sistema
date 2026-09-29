"""El alta desde la pantalla escribe lo mismo que el script, y nunca sobre el sistema real.

Estas pruebas corren sobre un sistema de mentira en una carpeta temporal —copiando el
script real de `Ads/_TOOLS/`— justo para demostrar el criterio de aceptación del Hito 2:
"un producto de prueba se da de alta y se borra en el fixture sin tocar los CSV reales".
"""

from __future__ import annotations

import csv
import io
import os
import shutil
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# P3 T4 (continuación parte 2): alta_producto.py real ahora escribe _DIM_PRODUCTOS.csv por
# Postgres (db/escribir.py) -- estas pruebas tienen que aislarse contra `vitalcom_test`, nunca
# tocar `vitalcom` real, mismo patrón que Ads/_TOOLS/test_alta_producto.py.
DB_DIR = str(Path(__file__).resolve().parents[3] / "db")
if DB_DIR not in sys.path:
    sys.path.insert(0, DB_DIR)
import cargar as db_cargar  # noqa: E402
import nucleo as db_nucleo  # noqa: E402

COLUMNAS_PRODUCTOS = [
    "producto_key", "nombre_display", "slug_carpeta", "estado", "fase", "cuenta_alias",
    "cuenta_id", "page_id", "moneda", "tasa", "costo_q", "fila_costeo_q", "precio_base_q",
    "cpa_base_q", "cpa_be_q", "cpa_be_anterior_q", "notas", "carpeta_videos",
    "carpeta_transcripciones", "carpeta_media", "carpetas_extra", "clave_campana", "campaign_id",
    "mercado",
]
COLUMNAS_MERCADOS = ["mercado", "pais", "moneda", "simbolo", "persona", "registro_sanitario"]
FILAS_MERCADOS = [["GT", "Guatemala", "GTQ", "Q", "voseo", "registro MSPAS"],
                  ["CO", "Colombia", "COP", "$", "tuteo", "registro INVIMA"]]
COLUMNAS_ENVASE = [
    "producto_key", "packshot", "color_envase", "color_hex", "marca_impresa",
    "formato_envase", "verificado_el", "fuente", "notas",
]
DESCRIPCION = (
    "Crema para varices con castaño de indias y mentol, pomo de 50 g. Se aplica dos veces "
    "al día con masaje ascendente. Registro sanitario MSPAS vigente. Proveedor nacional, "
    "entrega en 48 horas, garantía de devolución de 30 días."
)


def _script_del_repo(nombre: str) -> Path:
    """El script tal como está en ESTE repositorio, no en la carpeta donde corre la app.

    Importa la distinción: la app corre sobre la carpeta real del sistema, pero el código
    que se está probando es el de este worktree, que todavía puede no estar mergeado ahí.
    """
    repo = Path(__file__).resolve().parents[3]
    return repo / "Ads" / "_TOOLS" / nombre


def _conectar_seguro():
    con = db_cargar.conectar()
    if con.info.dbname == "vitalcom":
        con.close()
        raise RuntimeError(
            "test_alta_por_la_app.py intentó conectarse a 'vitalcom' en vez de 'vitalcom_test'. "
            "Abortado antes de tocar nada.")
    return con


def _bootstrap_producto_vacio(prod_dir: Path) -> None:
    """`raw.producto` (tenant `vitalcom`, el default del script real) queda SINCRONIZADO con el
    _DIM_PRODUCTOS.csv recién escrito (solo encabezado) -- para que el guardia de drift de
    db/escribir.py no aborte en la primera alta de cada prueba. Aísla en `vitalcom_test`, nunca
    toca `vitalcom` real (ver _conectar_seguro)."""
    con = _conectar_seguro()
    try:
        with con:
            with con.cursor() as cur:
                n, sha = db_cargar.cargar_tabla(cur, "vitalcom", "producto", "_DIM_PRODUCTOS.csv",
                                                 False, str(prod_dir))
                cur.execute(
                    "INSERT INTO raw.raw_import (tenant_id, archivo, sha256, filas) "
                    "VALUES (%s, %s, %s, %s)", ("vitalcom", "_DIM_PRODUCTOS.csv", sha, n))
                db_nucleo.construir_core(cur, "vitalcom")
    finally:
        con.close()


@pytest.fixture()
def sistema_falso(sistema_de_juguete: Path, monkeypatch) -> Path:
    """El sistema de juguete con el `alta_producto.py` REAL adentro y los CSV vacíos del alta.

    P3 T4 (continuación parte 2): el script real ahora escribe por Postgres -- fuerza
    `PGDATABASE=vitalcom_test` (heredado por el subproceso que lanza la app) y bootstrapea
    `raw.producto` ahí antes de la primera alta. Se salta con aviso si `vitalcom_test` no está
    disponible en este entorno (mismo criterio que Ads/_TOOLS/test_alta_producto.py).

    `db/` es código REAL versionado (nunca datos): en vez de duplicarlo dentro de la carpeta de
    mentira (que arrastraría también sus dependencias de Ads/_TOOLS, ej. venta_identidad.py,
    upsert_fact.py), se agrega el `db/` de ESTE repositorio a `PYTHONPATH` -- el subproceso que
    corre el `alta_producto.py` copiado encuentra ahí el paquete real, y ese mismo `db/tables.py`
    real resuelve su propia raíz (`BASE_DIR`) desde SU `__file__`, así que también encuentra el
    `Ads/_TOOLS` real para sus propias dependencias."""
    monkeypatch.setenv("PGDATABASE", "vitalcom_test")
    pythonpath_previo = os.environ.get("PYTHONPATH", "")
    monkeypatch.setenv("PYTHONPATH", os.pathsep.join(
        p for p in (DB_DIR, pythonpath_previo) if p))
    try:
        if db_cargar.asegurar_base_de_datos("vitalcom_test"):
            db_cargar.aplicar_schema(dbname="vitalcom_test")
    except Exception:
        pass
    try:
        _conectar_seguro().close()
    except Exception as exc:
        pytest.skip("Postgres/vitalcom_test no disponible en este entorno: %s" % exc)

    shutil.copy2(_script_del_repo("alta_producto.py"), sistema_de_juguete / "Ads" / "_TOOLS" / "alta_producto.py")
    shutil.copy2(_script_del_repo("mercado.py"), sistema_de_juguete / "Ads" / "_TOOLS" / "mercado.py")
    for nombre, columnas in (("_DIM_PRODUCTOS.csv", COLUMNAS_PRODUCTOS),
                             ("_DIM_ENVASE.csv", COLUMNAS_ENVASE)):
        with io.open(sistema_de_juguete / "PRODUCTOS" / nombre, "w", encoding="utf-8", newline="") as fh:
            csv.writer(fh).writerow(columnas)
    with io.open(sistema_de_juguete / "PRODUCTOS" / "_DIM_MERCADOS.csv", "w", encoding="utf-8", newline="") as fh:
        escritor = csv.writer(fh)
        escritor.writerow(COLUMNAS_MERCADOS)
        escritor.writerows(FILAS_MERCADOS)
    _bootstrap_producto_vacio(sistema_de_juguete / "PRODUCTOS")
    return sistema_de_juguete


@pytest.fixture()
def cliente_falso(sistema_falso: Path, cliente_juguete: TestClient) -> TestClient:
    return cliente_juguete


def _alta(cliente: TestClient, **extra):
    datos = {"nombre": "Crema Varices Plus", "costo": "60", "descripcion": DESCRIPCION, "mercado": "GT", **extra}
    return cliente.post(
        "/api/productos",
        data=datos,
        files={"imagen": ("foto.png", b"\x89PNG\r\n\x1a\n" + b"0" * 64, "image/png")},
    )


def _filas(base: Path, nombre: str) -> list[list[str]]:
    with io.open(base / "PRODUCTOS" / nombre, encoding="utf-8", newline="") as fh:
        return list(csv.reader(fh))


def test_el_alta_crea_fila_carpeta_y_packshot(cliente_falso, sistema_falso):
    respuesta = _alta(cliente_falso)
    assert respuesta.status_code == 201, respuesta.text
    cuerpo = respuesta.json()
    assert cuerpo["producto_key"] == "CREMA_VARICES_PLUS"

    filas = _filas(sistema_falso, "_DIM_PRODUCTOS.csv")
    fila = dict(zip(filas[0], filas[1]))
    assert fila["estado"] == "NUEVO"
    assert fila["costo_q"] == "60"
    assert fila["mercado"] == "GT"
    assert len(filas[1]) == len(filas[0]), "la fila tiene que tener las columnas del encabezado"

    packshot = sistema_falso / "Ads" / "MEDIA_CREMAVARICESPLUS" / "CREMA_VARICES_PLUS_PACKSHOT.png"
    assert packshot.is_file(), "la imagen subida termina como packshot declarado"
    envase = _filas(sistema_falso, "_DIM_ENVASE.csv")
    assert dict(zip(envase[0], envase[1]))["packshot"].endswith("CREMA_VARICES_PLUS_PACKSHOT.png")

    datos = sistema_falso / "PRODUCTOS" / "CREMA_VARICES_PLUS" / "2_DATA_PRODUCTO.txt"
    assert DESCRIPCION[:50] in datos.read_text(encoding="utf-8")


def test_el_alta_de_un_producto_de_colombia_guarda_su_mercado(cliente_falso, sistema_falso):
    assert _alta(cliente_falso, mercado="CO").status_code == 201
    filas = _filas(sistema_falso, "_DIM_PRODUCTOS.csv")
    assert dict(zip(filas[0], filas[1]))["mercado"] == "CO"


def test_el_alta_exige_mercado_y_no_asume_uno(cliente_falso, sistema_falso):
    """Sin mercado (o con uno que no existe) no hay alta ni fila: el operador elige GT o CO."""
    datos = {"nombre": "Crema Varices Plus", "costo": "60", "descripcion": DESCRIPCION}
    archivos = {"imagen": ("foto.png", b"\x89PNG\r\n\x1a\n" + b"0" * 64, "image/png")}
    sin = cliente_falso.post("/api/productos", data=datos, files=archivos)
    assert sin.status_code == 422, sin.text
    desconocido = _alta(cliente_falso, mercado="MX")
    assert desconocido.status_code == 422 and "MX" in str(desconocido.json()), desconocido.text
    assert len(_filas(sistema_falso, "_DIM_PRODUCTOS.csv")) == 1, "solo el encabezado"


def test_el_alta_no_escribe_cifras_de_costeo(cliente_falso, sistema_falso):
    _alta(cliente_falso)
    filas = _filas(sistema_falso, "_DIM_PRODUCTOS.csv")
    fila = dict(zip(filas[0], filas[1]))
    for columna in ("precio_base_q", "cpa_base_q", "cpa_be_q", "fila_costeo_q"):
        assert fila[columna] == "", f"{columna} lo escribe etapa-guardar-producto, no el alta"


def test_una_clave_repetida_se_rechaza_con_el_mensaje_del_script(cliente_falso, sistema_falso):
    assert _alta(cliente_falso).status_code == 201
    repetida = _alta(cliente_falso)
    assert repetida.status_code == 422
    assert "ya existe" in repetida.json()["detail"]
    assert len(_filas(sistema_falso, "_DIM_PRODUCTOS.csv")) == 2, "no se duplica la fila"


def test_dry_run_no_escribe_nada(cliente_falso, sistema_falso):
    respuesta = _alta(cliente_falso, dry_run="true")
    assert respuesta.status_code == 201
    assert respuesta.json()["aplicado"] is False
    assert len(_filas(sistema_falso, "_DIM_PRODUCTOS.csv")) == 1, "solo el encabezado"


def test_una_descripcion_pobre_se_rechaza(cliente_falso, sistema_falso):
    respuesta = _alta(cliente_falso, descripcion="sirve para las varices")
    assert respuesta.status_code == 422
    assert "descripcion" in respuesta.json()["detail"].lower()


def test_el_sistema_real_no_se_toco(base_declarada, sistema_falso):
    """Guarda contra el peor error posible: escribir en los CSV de verdad."""
    assert os.environ["VITALCOM_BASE"] == str(sistema_falso)
    assert base_declarada != sistema_falso
    reales = _filas(base_declarada, "_DIM_PRODUCTOS.csv")
    assert all("CREMA_VARICES_PLUS" not in fila[0] for fila in reales[1:])


def test_el_alta_deja_su_rastro_y_regenera_el_estado_derivado(cliente_falso, sistema_falso):
    """El alta pasa por el runner: hay carpeta de corrida y corrió `tras_escribir`."""
    assert _alta(cliente_falso).status_code == 201
    corridas = list((sistema_falso / "PRODUCTOS" / "_AUDITORIAS" / "app_runs").glob("*/*_producto.alta_*"))
    assert len(corridas) == 1
    assert (corridas[0] / "trabajo.json").is_file() and (corridas[0] / "1.fin").is_file()
    from sistema_de_juguete import llamadas

    scripts = [c["script"] for c in llamadas(sistema_falso)]
    assert "hook_csv.py" in scripts and "flujo.py" in scripts and "gen_app.py" in scripts


def test_un_archivo_fuera_de_las_subidas_no_se_acepta_como_imagen(sistema_falso):
    from vitalcom_app import acciones

    accion = acciones.por_id_para_el_runner("producto.alta")
    ajeno = sistema_falso / "PRODUCTOS" / "_DIM_PRODUCTOS.csv"
    with pytest.raises(acciones.ErrorDeAccion) as error:
        acciones.validar_parametros(accion, {
            "nombre": "Crema", "costo": "60", "descripcion": str(ajeno), "imagen": str(ajeno)})
    assert error.value.http == 422 and error.value.extra["campo"] == "descripcion"
