# -*- coding: utf-8 -*-
"""test_db.py — pruebas de db/ (P1-cimientos T5/T6/T2b/T5b).

Tres grupos:
  1. Pruebas PURAS de las funciones de mapeo (enriquecer_venta, ad_id_valido, columnas_tabla):
     no tocan disco ni red, corren siempre.
  2. Pruebas de INTEGRACIÓN sobre `raw`/`core` (carga, idempotencia, reconciliación, conservación
     de hechos): se saltan con un mensaje claro si no hay Postgres accesible.
  3. Prueba de PARIDAD (T6, desde T5b sobre `core`): carga -> exporta core.* a los 9 CSV que
     decidir.py lee -> corre decidir.py sobre ambas bases -> compara. Se salta igual sin Postgres.

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
import escribir as W  # noqa: E402
import nucleo as N  # noqa: E402

TOOLS_DIR = os.path.join(T.BASE_DIR, "Ads", "_TOOLS")
sys.path.insert(0, TOOLS_DIR)
import upsert_fact as UF  # noqa: E402


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


def _fila_mapa(venta_uid, ad_id="", metodo="nombre", **kw):
    m = {"ventana_ini": "2026-07-01", "cuenta_alias": "CTA1", "conjunto": "CONJ1",
         "anuncio": "AD1", "ad_id": ad_id, "metodo": metodo, "venta_uid": venta_uid}
    m.update(kw)
    return m


def test_enriquecer_venta_ad_id_original_valido_gana():
    filas = [_fila_venta("BASE", "120248199666460784")]
    out = C.enriquecer_venta(filas, filas_mapa=[])
    assert out == [("120248199666460784", "ad_id")]


def test_enriquecer_venta_mapa_verificado_por_gasto():
    filas = [_fila_venta("BASE", "")]
    uid = C.asignar_venta_uids(filas)[0]
    mapa = [_fila_mapa(uid, ad_id="999888777666", metodo="ad_id_verificado_gasto")]
    out = C.enriquecer_venta(filas, mapa)
    assert out == [("999888777666", "ad_id_verificado_gasto")]


def test_enriquecer_venta_mapa_solo_nombre_no_inventa_ad_id():
    filas = [_fila_venta("BASE", "")]
    uid = C.asignar_venta_uids(filas)[0]
    mapa = [_fila_mapa(uid, ad_id="", metodo="nombre")]
    out = C.enriquecer_venta(filas, mapa)
    assert out == [(None, "nombre")]


def test_enriquecer_venta_sin_match_en_mapa_es_sin_atribuir():
    filas = [_fila_venta("BASE", "")]
    out = C.enriquecer_venta(filas, filas_mapa=[])
    assert out == [(None, "sin_atribuir")]


def test_enriquecer_venta_control_nunca_pasa_por_el_mapa():
    # Una fila CONTROL sin ad_id nunca debe intentar resolverse por el mapa (el mapa solo
    # cubrió filas BASE — T2): aunque exista una entrada que matchee por casualidad, la regla es
    # "solo BASE entra al mapa".
    filas = [_fila_venta("CONTROL", "")]
    uid = C.asignar_venta_uids(filas)[0]
    mapa = [_fila_mapa(uid, ad_id="999888777666", metodo="ad_id_verificado_gasto")]
    out = C.enriquecer_venta(filas, mapa)
    assert out == [(None, "sin_atribuir")]


# ── T2b: join por venta_uid, no por posición ────────────────────────────────

def test_enriquecer_venta_llave_repetida_se_distingue_por_venta_uid():
    """_MAPA_AD_ID_HIST.csv repite la llave natural (ventana_ini, cuenta_alias, conjunto,
    anuncio) en 150 grupos reales: dos ventas con la MISMA llave pero contenido distinto
    (ad_id ya presente en una de ellas, por ejemplo) deben resolver cada una a SU propia entrada
    del mapa por venta_uid, no por posición de aparición."""
    filas = [
        _fila_venta("BASE", "", anuncio="AD_DUP"),
        dict(_fila_venta("BASE", "", anuncio="AD_DUP"), extra="distingue-el-contenido"),
    ]
    uids = C.asignar_venta_uids(filas)
    mapa = [
        _fila_mapa(uids[0], ad_id="111111111111", metodo="ad_id_verificado_gasto", conjunto="CONJ1"),
        _fila_mapa(uids[1], ad_id="", metodo="nombre", conjunto="CONJ1"),
    ]
    out = C.enriquecer_venta(filas, mapa)
    assert out == [("111111111111", "ad_id_verificado_gasto"), (None, "nombre")]


def test_enriquecer_venta_estable_ante_reordenamiento():
    """Reordenar _FACT_VENTAS.csv no debe cambiar ninguna atribución (T2b): el join es por
    venta_uid (contenido), no por posición."""
    filas = [
        _fila_venta("BASE", "120248199666460784", anuncio="AD1"),
        _fila_venta("BASE", "", anuncio="AD2"),
        _fila_venta("BASE", "", anuncio="AD2"),  # duplicado exacto de la anterior
        _fila_venta("CONTROL", "", anuncio="AD3"),
    ]
    uids = C.asignar_venta_uids(filas)
    mapa = [
        _fila_mapa(uids[1], ad_id="222222222222", metodo="ad_id_verificado_gasto", anuncio="AD2"),
        _fila_mapa(uids[2], ad_id="", metodo="nombre", anuncio="AD2"),
    ]
    out_fwd = C.enriquecer_venta(filas, mapa)

    orden = [3, 1, 0, 2]
    filas_rev = [filas[i] for i in orden]
    out_rev = C.enriquecer_venta(filas_rev, mapa)

    # cada fila (por su índice ORIGINAL) debe resolver igual sin importar en qué orden llegó
    for nuevo_idx, idx_original in enumerate(orden):
        assert out_rev[nuevo_idx] == out_fwd[idx_original], (
            "la fila %d cambió de atribución al reordenar" % idx_original)


def test_asignar_venta_uids_expuesta_en_cargar():
    """db/cargar.py reexporta asignar_venta_uids desde Ads/_TOOLS/venta_identidad.py: un dato,
    un dueño (la función vive en un solo lugar, sin duplicarse)."""
    uids = C.asignar_venta_uids([{"x": "1"}, {"x": "1"}])
    assert uids[0] != uids[1] and uids[1] == uids[0] + "-1"


def test_extra_columns_vacio_raw_es_espejo_puro():
    """T5b: `raw` ya no tiene columnas de enriquecimiento (eso vive solo en `core`)."""
    assert T.EXTRA_COLUMNS == {}


def test_nombre_columna_sql_rechaza_columna_invalida():
    with pytest.raises(ValueError):
        T.nombre_columna_sql("nombre; drop table")


def test_columnas_tabla_conjunto_incluye_header_real():
    cols = T.columnas_tabla("conjunto", "_DIM_CONJUNTOS.csv", False)
    assert "producto_key" in cols
    assert "angulo_key" in cols


def test_columnas_tabla_venta_es_verbatim_sin_extras():
    cols = T.columnas_tabla("venta", "_FACT_VENTAS.csv", False)
    assert cols[-1] == "ad_id"
    assert "ad_id_resuelto" not in cols and "metodo_atribucion" not in cols


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
    r1 = C.cargar_todo()
    r2 = C.cargar_todo()
    assert r1["raw"] == r2["raw"]
    assert r1["core"]["tablas"] == r2["core"]["tablas"]
    assert r1["core"]["fk_sin_resolver"] == r2["core"]["fk_sin_resolver"]
    assert r1["core"]["conservacion"] == r2["core"]["conservacion"]
    # El conteo de cada tabla espejo `raw` coincide con las filas reales del CSV (menos header).
    for tabla, archivo, opcional in T.TABLE_SPECS:
        path = os.path.join(T.PRODUCTOS_DIR, archivo)
        if not os.path.exists(path):
            assert r1["raw"][tabla] == 0
            continue
        with open(path, encoding="utf-8-sig") as f:
            n = sum(1 for _ in f) - 1
        assert r1["raw"][tabla] == n, "conteo distinto en raw.%s" % tabla


@requiere_db
def test_core_conserva_todas_las_filas_raw_de_los_3_hechos():
    """T5b: cada fila `raw` de venta/entrega_anuncio_dia/entrega_conjunto_dia aterriza EXACTAMENTE
    una vez en `core` (nunca se descarta por no resolver un FK)."""
    r = C.cargar_todo()
    for tabla in ("venta", "entrega_anuncio_dia", "entrega_conjunto_dia"):
        c = r["core"]["conservacion"][tabla]
        assert c["igual"], "%s: raw=%s core=%s" % (tabla, c["raw"], c["core"])


@requiere_db
def test_venta_metodo_atribucion_coincide_con_T2():
    """Verificación de odd/tasks/p1-cimientos.md: ad_id válido + 670 verificados por gasto +
    resto nombre/sin_atribuir, sin inventar ni un ad_id. Vive en core.venta desde T5b."""
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
    assert conteos.get("nombre") == 724
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
    """El override (Ads/_TOOLS/decidir.py, T6) no cambia nada sin la variable de entorno: misma
    ruta PROD de siempre. Y con la variable, apunta exactamente a lo que se le pase."""
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
    """T6 (reprobado sobre `core` desde T5b): exporta core.* -> los 9 CSV que decidir.py lee, a
    una base temporal, y corre `decidir.py --json` (en un subproceso con scipy+duckdb, vía
    DECIDIR_PROD_DIR) sobre esa base y sobre el repo real. Compara ambos resultados ignorando
    solo 'generado'. Cualquier otra diferencia es FAIL, no se enmascara. NUNCA usa --escribir ni
    toca PRODUCTOS/_DECISIONES.json real. NUNCA cae de vuelta a exportar desde `raw`."""
    python_exe = _python_con_scipy_y_duckdb()
    if not python_exe:
        pytest.skip("no se encontró un intérprete con scipy+duckdb para correr decidir.py")

    C.cargar_todo()
    tmp = tempfile.mkdtemp(prefix="vitalcom_parity_core_")
    try:
        E.exportar_core_decidir(tmp)

        resultado_real = _correr_decidir_json(python_exe)
        resultado_exportado = _correr_decidir_json(python_exe, prod_dir=tmp)

        a = _quitar_generado(resultado_real)
        b = _quitar_generado(resultado_exportado)
        assert a == b, "el resultado de decidir.py difiere entre la base real y la exportada desde core"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


@requiere_db
def test_exportar_raw_todo_sigue_disponible_para_auditoria():
    """El exportador raw completo (T5) sigue existiendo como capa de auditoría/staging, separado
    del exportador core/decidir (T5b)."""
    C.cargar_todo()
    tmp = tempfile.mkdtemp(prefix="vitalcom_raw_export_")
    try:
        conteos = E.exportar_raw_todo(tmp)
        assert conteos["venta"] == sum(
            1 for _ in open(os.path.join(T.PRODUCTOS_DIR, "_FACT_VENTAS.csv"),
                             encoding="utf-8-sig")) - 1
        with open(os.path.join(tmp, "_FACT_VENTAS.csv"), encoding="utf-8") as f:
            header = f.readline().strip().split(",")
        assert "ad_id_resuelto" not in header and "metodo_atribucion" not in header
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ── grupo 3: db/escribir.py — capa de escritura Postgres (P3 T2) ────────────

# tabla `raw`/`core` -> archivo CSV, para las 6 de las 7 del set DB-truth (T1) que sí tienen fila
# en TABLE_SPECS. La séptima, `_DECISIONES.json`, no tiene tabla `raw` columna-por-columna (vive
# en `raw.decisiones_json`, un blob) y se prueba aparte.
DB_TRUTH_CSVS = {
    "venta": "_FACT_VENTAS.csv",
    "entrega_conjunto_dia": "_FACT_ENTREGA.csv",
    "entrega_anuncio_dia": "_FACT_ENTREGA_ANUNCIO.csv",
    "evento": "_EVENTOS.csv",
    "estado_flujo": "_ESTADO_FLUJO.csv",
    "producto": "_DIM_PRODUCTOS.csv",
}

TENANT_TEST_T2 = "test_p3_t2"


def test_fusionar_es_la_misma_semantica_que_upsert_sobre_un_csv(tmp_path):
    """P3 T2: `upsert_fact.fusionar()` (la mecánica pura que ahora comparten `upsert_fact.upsert()`
    y `db/escribir.py`) debe producir exactamente el mismo resultado, sobre los mismos datos, que
    `upsert()` sobre un CSV real — es la garantía de que extraer la función no cambió nada."""
    cols = ["dia", "cuenta", "ad_id", "spend"]
    key = ("dia", "cuenta")
    filas = [{"dia": "2026-09-20", "cuenta": "A", "ad_id": "1", "spend": "10.0"}]

    resultado, reemp, nuevas, sc, elim = UF.fusionar([], filas, cols, key)
    assert (reemp, nuevas, sc, elim) == (0, 1, 0, 0)

    path = str(tmp_path / "hechos.csv")
    bkdir = str(tmp_path / "bk")
    reemp2, nuevas2, sc2 = UF.upsert(path, cols, key, filas, bkdir)
    assert (reemp2, nuevas2, sc2) == (0, 1, 0)
    assert UF.leer_migrado(path, cols) == resultado


def _limpiar_tenant_test(tenant_id=TENANT_TEST_T2):
    """Deja las tablas DB-truth (raw + core) sin filas de `tenant_id`, para que cada prueba de
    `db/escribir.py` arranque de un estado conocido sin depender del orden de ejecución."""
    con = C.conectar()
    try:
        with con:
            with con.cursor() as cur:
                for tabla in T.TABLAS_VERDAD_DB:
                    cur.execute("DELETE FROM raw.%s WHERE tenant_id = %%s" % tabla, (tenant_id,))
                cur.execute("DELETE FROM raw.decisiones_json WHERE tenant_id = %s", (tenant_id,))
                N.construir_core(cur, tenant_id)
    finally:
        con.close()


def _cols_venta():
    return T.columnas_tabla("venta", "_FACT_VENTAS.csv", False)


def _fila_venta_completa(**over):
    cols = _cols_venta()
    base = {c: "" for c in cols}
    base.update({
        "ventana_ini": "2026-09-01", "ventana_fin": "2026-09-01", "dias": "1",
        "rol_ventana": "BASE", "producto_key": "TESTP3", "producto": "Test P3",
        "cuenta_id": "1", "cuenta_alias": "TESTCTA", "campana": "CAMP", "conjunto": "CONJ",
        "anuncio": "AD1", "mensajes": "1", "clicks": "1", "impresiones": "10",
        "spend_usd": "1.0", "ventas": "1", "total_q": "10", "moneda_origen": "GTQ",
        "fuente": "test", "ad_id": "",
    })
    base.update(over)
    return {c: base.get(c, "") for c in cols}


@requiere_db
def test_espejo_es_byte_identico_a_los_7_archivos_db_truth():
    """P3 T2, check central de T2: sobre la data REAL ya cargada a Postgres, el espejo que
    regenera `db/escribir.py` debe reproducir byte a byte cada uno de los 7 archivos del set
    DB-truth (T1) — mismo header, mismo orden de filas y columnas, mismo terminador de línea,
    mismo encoding. Si un archivo no calza, el hallazgo es del EXPORTADOR o del archivo fuente,
    nunca algo que este test deba ocultar."""
    C.cargar_todo()
    con = C.conectar()
    try:
        with tempfile.TemporaryDirectory() as tmp:
            for tabla, archivo in DB_TRUTH_CSVS.items():
                W._regenerar_espejo_csv(con, "vitalcom", tabla, tmp)
                with open(os.path.join(tmp, archivo), "rb") as f:
                    espejo = f.read()
                with open(os.path.join(T.PRODUCTOS_DIR, archivo), "rb") as f:
                    real = f.read()
                assert espejo == real, "%s: el espejo difiere byte a byte del real" % archivo

            payload = W.leer_decision_actual(con, "vitalcom")
            assert payload, "raw.decisiones_json debería tener contenido tras cargar_todo()"
            W._escribir_json_atomico(os.path.join(tmp, "_DECISIONES.json"), payload)
            with open(os.path.join(tmp, "_DECISIONES.json"), "rb") as f:
                espejo = f.read()
            with open(os.path.join(T.PRODUCTOS_DIR, "_DECISIONES.json"), "rb") as f:
                real = f.read()
            assert espejo == real, "_DECISIONES.json: el espejo difiere byte a byte del real"
    finally:
        con.close()


@requiere_db
def test_escribir_upsert_idempotente_y_conserva_posicion():
    """`escribir.upsert()` sobre `raw.venta` se comporta EXACTAMENTE como `upsert_fact.upsert()`
    sobre el CSV equivalente: reemplaza por llave conservando la POSICIÓN de la fila (no la manda
    al final), agrega al final las llaves nuevas, y repetir la misma corrida es idempotente (0
    reemplazos / 0 altas) sin cambiar el conteo de filas en `raw` NI en `core`."""
    _limpiar_tenant_test()
    con = C.conectar()
    key = ("ventana_ini", "cuenta_alias", "conjunto", "anuncio")
    cols = _cols_venta()
    try:
        f1 = _fila_venta_completa(anuncio="AD1", spend_usd="1.0")
        f2 = _fila_venta_completa(anuncio="AD2", spend_usd="2.0")

        with tempfile.TemporaryDirectory() as tmp:
            path_ref = os.path.join(tmp, "ref.csv")
            bkdir = os.path.join(tmp, "bk")
            UF.upsert(path_ref, cols, key, [f1, f2], bkdir)

            reemp, nuevas, sc = W.upsert(con, "venta", [f1, f2], key, tenant_id=TENANT_TEST_T2)
            assert (reemp, nuevas, sc) == (0, 2, 0)

            f1_corregida = _fila_venta_completa(anuncio="AD1", spend_usd="9.0")
            UF.upsert(path_ref, cols, key, [f1_corregida], bkdir)
            reemp2, nuevas2, sc2 = W.upsert(con, "venta", [f1_corregida], key,
                                             tenant_id=TENANT_TEST_T2)
            assert (reemp2, nuevas2, sc2) == (1, 0, 0)

            with con.cursor() as cur:
                filas_db = W._leer_raw(cur, TENANT_TEST_T2, "venta", cols)
            filas_ref = UF.leer_migrado(path_ref, cols)
            assert [f["anuncio"] for f in filas_db] == ["AD1", "AD2"]
            assert [f["anuncio"] for f in filas_db] == [f["anuncio"] for f in filas_ref]
            assert filas_db[0]["spend_usd"] == "9.0"

            with con.cursor() as cur:
                cur.execute("SELECT count(*) FROM raw.venta WHERE tenant_id = %s",
                            (TENANT_TEST_T2,))
                n_raw_antes = cur.fetchone()[0]
                cur.execute("SELECT count(*) FROM core.venta WHERE tenant_id = %s",
                            (TENANT_TEST_T2,))
                n_core_antes = cur.fetchone()[0]

            reemp3, nuevas3, sc3 = W.upsert(con, "venta", [f1_corregida, f2], key,
                                             tenant_id=TENANT_TEST_T2)
            assert (reemp3, nuevas3, sc3) == (0, 0, 2)

            with con.cursor() as cur:
                cur.execute("SELECT count(*) FROM raw.venta WHERE tenant_id = %s",
                            (TENANT_TEST_T2,))
                n_raw_despues = cur.fetchone()[0]
                cur.execute("SELECT count(*) FROM core.venta WHERE tenant_id = %s",
                            (TENANT_TEST_T2,))
                n_core_despues = cur.fetchone()[0]
            assert n_raw_antes == n_raw_despues == 2
            assert n_core_antes == n_core_despues == 2
    finally:
        con.close()
        _limpiar_tenant_test()


@requiere_db
def test_escribir_upsert_mirror_byte_identico_al_de_upsert_fact():
    """El espejo que regenera `escribir.upsert(prod_dir=...)` debe ser byte-idéntico al CSV que
    produce `upsert_fact.upsert()` sobre los mismos datos y el mismo `key`."""
    _limpiar_tenant_test()
    con = C.conectar()
    key = ("ventana_ini", "cuenta_alias", "conjunto", "anuncio")
    cols = _cols_venta()
    try:
        filas = [_fila_venta_completa(anuncio="AD1"), _fila_venta_completa(anuncio="AD2")]
        with tempfile.TemporaryDirectory() as tmp:
            path_ref = os.path.join(tmp, "_FACT_VENTAS.csv")
            bkdir = os.path.join(tmp, "bk")
            UF.upsert(path_ref, cols, key, filas, bkdir)

            prod_dir = os.path.join(tmp, "mirror")
            os.makedirs(prod_dir, exist_ok=True)
            W.upsert(con, "venta", filas, key, prod_dir=prod_dir, tenant_id=TENANT_TEST_T2)

            with open(path_ref, "rb") as f:
                ref_bytes = f.read()
            with open(os.path.join(prod_dir, "_FACT_VENTAS.csv"), "rb") as f:
                espejo_bytes = f.read()
            assert espejo_bytes == ref_bytes
    finally:
        con.close()
        _limpiar_tenant_test()


@requiere_db
def test_escribir_particion_elimina_igual_que_upsert_fact():
    """`particion` en `escribir.upsert()` se comporta igual que en `upsert_fact.upsert()`: un
    re-pull declara su ámbito como la verdad completa y elimina lo que ese ámbito ya no trae."""
    _limpiar_tenant_test()
    con = C.conectar()
    key = ("ventana_ini", "cuenta_alias", "conjunto", "anuncio")
    particion = ("ventana_ini", "cuenta_alias", "conjunto")
    cols = _cols_venta()
    try:
        dos = [_fila_venta_completa(anuncio="AD1"), _fila_venta_completa(anuncio="AD2")]
        W.upsert(con, "venta", dos, key, tenant_id=TENANT_TEST_T2)

        solo_uno = [_fila_venta_completa(anuncio="AD1")]
        reemp, nuevas, sc, elim = W.upsert(con, "venta", solo_uno, key, particion=particion,
                                            tenant_id=TENANT_TEST_T2)
        assert elim == 1
        with con.cursor() as cur:
            filas = W._leer_raw(cur, TENANT_TEST_T2, "venta", cols)
        assert [f["anuncio"] for f in filas] == ["AD1"]
    finally:
        con.close()
        _limpiar_tenant_test()


@requiere_db
def test_escribir_falla_a_mitad_hace_rollback_y_no_toca_el_espejo(monkeypatch):
    """Si algo falla DESPUÉS de reescribir `raw` pero antes de terminar la transacción (acá:
    `construir_core` simulado a propósito), `escribir.upsert()` debe (a) levantar
    `ErrorEscritura`, (b) dejar `raw` como estaba ANTES del intento (rollback real de Postgres,
    no un rollback simulado) y (c) NUNCA tocar el archivo de espejo — el commit nunca ocurrió."""
    _limpiar_tenant_test()
    con = C.conectar()
    key = ("ventana_ini", "cuenta_alias", "conjunto", "anuncio")
    cols = _cols_venta()
    try:
        f1 = _fila_venta_completa(anuncio="AD1")
        W.upsert(con, "venta", [f1], key, tenant_id=TENANT_TEST_T2)

        with tempfile.TemporaryDirectory() as tmp:
            mirror_path = os.path.join(tmp, "_FACT_VENTAS.csv")
            assert not os.path.exists(mirror_path)

            def _rompe(*a, **kw):
                raise RuntimeError("boom-test (P3 T2, rollback esperado)")

            monkeypatch.setattr(W.N, "construir_core", _rompe)
            f2 = _fila_venta_completa(anuncio="AD2")
            with pytest.raises(W.ErrorEscritura):
                W.upsert(con, "venta", [f2], key, prod_dir=tmp, tenant_id=TENANT_TEST_T2)
            monkeypatch.undo()  # restaurar YA: la limpieza de más abajo vuelve a llamar construir_core

            assert not os.path.exists(mirror_path), "el espejo no debe existir tras un rollback"

        with con.cursor() as cur:
            filas = W._leer_raw(cur, TENANT_TEST_T2, "venta", cols)
        assert [f["anuncio"] for f in filas] == ["AD1"], (
            "raw.venta debe quedar como antes del intento fallido (rollback)")
    finally:
        con.close()
        _limpiar_tenant_test()


@requiere_db
def test_cargar_todo_incluir_verdad_db_false_deja_intactas_las_tablas_verdad():
    """P3 T2: `cargar_todo(incluir_verdad_db=False)` no debe disparar el TRUNCATE de ninguna
    tabla de `tables.TABLAS_VERDAD_DB` — se prueba con una fila de otro tenant (`test_p3_t2`)
    porque `cargar_tabla()` hace `TRUNCATE TABLE raw.<tabla>` (sin filtrar por tenant, el sistema
    es single-tenant hoy): si `incluir_verdad_db=False` no la protegiera, esa fila desaparecería
    aunque pertenezca a un tenant distinto del que carga `cargar_todo()`."""
    _limpiar_tenant_test()
    con = C.conectar()
    key = ("ventana_ini", "cuenta_alias", "conjunto", "anuncio")
    try:
        f1 = _fila_venta_completa(anuncio="AD1")
        W.upsert(con, "venta", [f1], key, tenant_id=TENANT_TEST_T2)
    finally:
        con.close()

    C.cargar_todo(incluir_verdad_db=False)

    con2 = C.conectar()
    try:
        with con2.cursor() as cur:
            cur.execute("SELECT count(*) FROM raw.venta WHERE tenant_id = %s",
                        (TENANT_TEST_T2,))
            n = cur.fetchone()[0]
    finally:
        con2.close()
    assert n == 1, "cargar_todo(incluir_verdad_db=False) truncó una tabla DB-truth"
    _limpiar_tenant_test()
