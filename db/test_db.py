# -*- coding: utf-8 -*-
"""test_db.py — pruebas de db/ (P1-cimientos T5/T6).

Dos grupos:
  1. Pruebas PURAS de las funciones de mapeo (enriquecer_venta, ad_id_valido, columnas_tabla):
     no tocan disco ni red, corren siempre.
  2. Prueba de INTEGRACIÓN (carga -> exporta -> corre decidir.py sobre ambas bases -> compara):
     se salta con un mensaje claro si no hay Postgres accesible (variable de entorno o archivo
     ~/.config/vitalcom_db/.env ausente, o conexión rechazada) — nunca falla el suite completo
     por falta de entorno local.

Correr con el intérprete del venv que ya tiene psycopg:
    "../SISTEMA-app/app/backend/.venv/Scripts/python.exe" -m pytest db/test_db.py -q
"""
import copy
import json
import os
import shutil
import subprocess
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tables as T  # noqa: E402
import cargar as C  # noqa: E402
import exportar as E  # noqa: E402

TOOLS_DIR = os.path.join(T.BASE_DIR, "Ads", "_TOOLS")


# ── grupo 1: funciones puras ────────────────────────────────────────────────

def test_ad_id_valido():
    assert C.ad_id_valido("120248199666460784") is True
    assert C.ad_id_valido("1.2024737592740078e+17") is False
    assert C.ad_id_valido("") is False
    assert C.ad_id_valido(None) is False
    assert C.ad_id_valido("123") is False  # menos de 10 dígitos


def _fila_venta(rol_ventana, ad_id, ventana_ini="2026-07-01", cuenta_alias="CTA1",
                 conjunto="CONJ1", anuncio="AD1"):
    return {
        "ventana_ini": ventana_ini, "cuenta_alias": cuenta_alias,
        "conjunto": conjunto, "anuncio": anuncio,
        "rol_ventana": rol_ventana, "ad_id": ad_id,
    }


def test_enriquecer_venta_ad_id_original_valido_gana():
    filas = [_fila_venta("BASE", "120248199666460784")]
    out = C.enriquecer_venta(filas, filas_mapa=[])
    assert out == [("120248199666460784", "ad_id")]


def test_enriquecer_venta_mapa_verificado_por_gasto():
    filas = [_fila_venta("BASE", "")]
    mapa = [{"ventana_ini": "2026-07-01", "cuenta_alias": "CTA1", "conjunto": "CONJ1",
             "anuncio": "AD1", "ad_id": "999888777666", "metodo": "ad_id_verificado_gasto"}]
    out = C.enriquecer_venta(filas, mapa)
    assert out == [("999888777666", "ad_id_verificado_gasto")]


def test_enriquecer_venta_mapa_solo_nombre_no_inventa_ad_id():
    filas = [_fila_venta("BASE", "")]
    mapa = [{"ventana_ini": "2026-07-01", "cuenta_alias": "CTA1", "conjunto": "CONJ1",
             "anuncio": "AD1", "ad_id": "", "metodo": "nombre"}]
    out = C.enriquecer_venta(filas, mapa)
    assert out == [(None, "nombre")]


def test_enriquecer_venta_sin_match_en_mapa_es_sin_atribuir():
    filas = [_fila_venta("BASE", "")]
    out = C.enriquecer_venta(filas, filas_mapa=[])
    assert out == [(None, "sin_atribuir")]


def test_enriquecer_venta_llave_repetida_usa_orden_fifo():
    """_MAPA_AD_ID_HIST.csv repite la llave natural en 150 grupos (confirmado sobre el CSV real):
    la correspondencia correcta es FIFO por orden de aparición, no last-write-wins de un dict."""
    filas = [
        _fila_venta("BASE", "", anuncio="AD_DUP"),
        _fila_venta("BASE", "", anuncio="AD_DUP"),
    ]
    mapa = [
        {"ventana_ini": "2026-07-01", "cuenta_alias": "CTA1", "conjunto": "CONJ1",
         "anuncio": "AD_DUP", "ad_id": "111111111111", "metodo": "ad_id_verificado_gasto"},
        {"ventana_ini": "2026-07-01", "cuenta_alias": "CTA1", "conjunto": "CONJ1",
         "anuncio": "AD_DUP", "ad_id": "", "metodo": "nombre"},
    ]
    out = C.enriquecer_venta(filas, mapa)
    assert out == [("111111111111", "ad_id_verificado_gasto"), (None, "nombre")]


def test_enriquecer_venta_control_nunca_pasa_por_el_mapa():
    # Una fila CONTROL sin ad_id nunca debe intentar resolverse por el mapa (el mapa solo
    # cubrió filas BASE — T2): aunque exista una entrada que matchee por casualidad, la regla es
    # "solo BASE entra al mapa".
    filas = [_fila_venta("CONTROL", "")]
    mapa = [{"ventana_ini": "2026-07-01", "cuenta_alias": "CTA1", "conjunto": "CONJ1",
             "anuncio": "AD1", "ad_id": "999888777666", "metodo": "ad_id_verificado_gasto"}]
    out = C.enriquecer_venta(filas, mapa)
    assert out == [(None, "sin_atribuir")]


def test_nombre_columna_sql_rechaza_columna_invalida():
    with pytest.raises(ValueError):
        T.nombre_columna_sql("nombre; drop table")


def test_columnas_tabla_conjunto_incluye_header_real():
    cols = T.columnas_tabla("conjunto", "_DIM_CONJUNTOS.csv", False)
    assert "producto_key" in cols
    assert "angulo_key" in cols


def test_columnas_tabla_venta_agrega_extras_al_final():
    cols = T.columnas_tabla("venta", "_FACT_VENTAS.csv", False)
    assert cols[-2:] == ["ad_id_resuelto", "metodo_atribucion"]


def test_columnas_tabla_opcional_vacia_si_no_existe():
    cols = T.columnas_tabla("voz_cliente", "_ARCHIVO_QUE_NO_EXISTE.csv", True)
    assert cols == []


def test_columnas_tabla_requerida_explota_si_no_existe():
    with pytest.raises(FileNotFoundError):
        T.columnas_tabla("x", "_ARCHIVO_QUE_NO_EXISTE.csv", False)


# ── grupo 2: integración (requiere Postgres real) ───────────────────────────

def _env_db_disponible():
    ruta = os.path.join(os.path.expanduser("~"), ".config", "vitalcom_db", ".env")
    if not os.path.exists(ruta) and "PGHOST" not in os.environ:
        return False
    try:
        con = C.conectar()
        con.close()
        return True
    except Exception:
        return False


DB_DISPONIBLE = _env_db_disponible()
requiere_db = pytest.mark.skipif(not DB_DISPONIBLE, reason="Postgres no accesible en este entorno "
                                  "(sin ~/.config/vitalcom_db/.env o conexión rechazada)")


@requiere_db
def test_cargar_es_idempotente_en_conteo_de_filas():
    c1 = C.cargar_todo()
    c2 = C.cargar_todo()
    assert c1 == c2
    # El conteo de cada tabla espejo coincide con las filas reales del CSV (menos el header).
    for tabla, archivo, opcional in T.TABLE_SPECS:
        path = os.path.join(T.PRODUCTOS_DIR, archivo)
        if not os.path.exists(path):
            assert c1[tabla] == 0
            continue
        with open(path, encoding="utf-8-sig") as f:
            n = sum(1 for _ in f) - 1
        assert c1[tabla] == n, "conteo distinto en %s" % tabla


@requiere_db
def test_venta_metodo_atribucion_coincide_con_T2():
    """Verificación #2 de odd/tasks/p1-cimientos.md: ad_id válido + 670 verificados por gasto +
    resto nombre/sin_atribuir, sin inventar ni un ad_id."""
    C.cargar_todo()
    con = C.conectar()
    try:
        with con.cursor() as cur:
            cur.execute(
                "SELECT metodo_atribucion, count(*) FROM core.venta "
                "WHERE tenant_id = %s GROUP BY 1 ORDER BY 1",
                ("vitalcom",),
            )
            conteos = dict(cur.fetchall())
    finally:
        con.close()
    assert conteos.get("ad_id_verificado_gasto") == 670
    assert sum(conteos.values()) == sum(1 for _ in open(
        os.path.join(T.PRODUCTOS_DIR, "_FACT_VENTAS.csv"), encoding="utf-8-sig")) - 1


def _quitar_generado(payload):
    p = copy.deepcopy(payload)
    p.pop("generado", None)
    return p


def _python_con_scipy_y_duckdb():
    """decidir.py necesita scipy+duckdb; el venv de psycopg que corre este test no los tiene
    (y no está autorizado instalarlos). Busca un intérprete que sí los tenga, empezando por
    `python` del PATH (confirmado en este entorno: 3.14, scipy 1.18, duckdb 1.5). None si
    ninguno califica — el gate se salta con un mensaje claro, nunca se fuerza."""
    candidatos = []
    encontrado = shutil.which("python")
    if encontrado:
        candidatos.append(encontrado)
    for c in candidatos:
        try:
            r = subprocess.run([c, "-c", "import scipy, duckdb"], capture_output=True, timeout=30)
            if r.returncode == 0:
                return c
        except Exception:
            continue
    return None


def _correr_decidir_json(python_exe, prod_dir=None):
    env = dict(os.environ)
    if prod_dir:
        env["DECIDIR_PROD_DIR"] = prod_dir
    r = subprocess.run(
        [python_exe, os.path.join(TOOLS_DIR, "decidir.py"), "--json"],
        capture_output=True, text=True, encoding="utf-8", env=env, cwd=T.BASE_DIR, timeout=120,
    )
    assert r.returncode == 0, "decidir.py --json salió con error:\n%s" % r.stderr
    return json.loads(r.stdout)


def test_decidir_prod_dir_override_es_retrocompatible():
    """El override nuevo (Ads/_TOOLS/decidir.py, T6) no cambia nada sin la variable de entorno:
    misma ruta PROD de siempre. Y con la variable, apunta exactamente a lo que se le pase."""
    python_exe = _python_con_scipy_y_duckdb()
    if not python_exe:
        pytest.skip("no se encontró un intérprete con scipy+duckdb para importar decidir.py")

    codigo = "import sys; sys.path.insert(0, %r); import decidir; print(decidir.PROD)" % TOOLS_DIR

    env_sin = dict(os.environ)
    env_sin.pop("DECIDIR_PROD_DIR", None)
    r = subprocess.run([python_exe, "-c", codigo], capture_output=True, text=True, env=env_sin)
    assert r.stdout.strip().replace("\\", "/").endswith("PRODUCTOS"), r.stderr

    env_con = dict(os.environ)
    env_con["DECIDIR_PROD_DIR"] = "Z:/fixture-que-no-existe"
    r2 = subprocess.run([python_exe, "-c", codigo], capture_output=True, text=True, env=env_con)
    assert r2.stdout.strip() == "Z:/fixture-que-no-existe", r2.stderr


@requiere_db
def test_parity_gate_decidir_exportado_igual_a_real():
    """T6: exporta Postgres -> CSV a una base temporal y corre `decidir.py --json` (en un
    subproceso con scipy+duckdb, vía DECIDIR_PROD_DIR) sobre esa base y sobre el repo real.
    Compara ambos resultados ignorando solo 'generado' (fecha de hoy, igual en ambas corridas de
    todos modos). Cualquier otra diferencia es FAIL, no se enmascara. NUNCA usa --escribir ni
    toca PRODUCTOS/_DECISIONES.json real."""
    python_exe = _python_con_scipy_y_duckdb()
    if not python_exe:
        pytest.skip("no se encontró un intérprete con scipy+duckdb para correr decidir.py")

    C.cargar_todo()
    tmp = tempfile.mkdtemp(prefix="vitalcom_parity_")
    try:
        E.exportar_todo(tmp)

        resultado_real = _correr_decidir_json(python_exe)
        resultado_exportado = _correr_decidir_json(python_exe, prod_dir=tmp)

        a = _quitar_generado(resultado_real)
        b = _quitar_generado(resultado_exportado)
        assert a == b, "el resultado de decidir.py difiere entre la base real y la exportada"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
