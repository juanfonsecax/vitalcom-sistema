#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_multimercado_d3.py — GATE: el dinero no se mezcla entre mercados y no hay tasa GT por defecto.

Congela lo que D3 (multi-mercado) no puede romper:
  · un producto sin `tasa` no se convierte con 7.62: `mercado.tasa_de_fila` falla nombrandolo;
  · decidir.py OMITE (con aviso) al producto sin tasa y usa la tasa PROPIA de cada producto;
  · atribuir.py se detiene si un corte mezcla mercados o si falta una tasa;
  · gen_finanzas.py / gen_testeos.py / gen_pl.py agrupan por mercado (un TOTAL por mercado), usan la
    tasa del producto y nombran al producto sin tasa.

Corre con pytest (tmp dirs) o directo:  python Ads/_TOOLS/test_multimercado_d3.py
"""

import contextlib
import csv
import io
import os
import shutil
import subprocess
import sys
import tempfile

TOOLS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TOOLS)
import mercado  # noqa: E402

GT_TASA, CO_TASA = 7.62, 4000.0


def _csv(base, nombre, encabezado, filas):
    with io.open(os.path.join(base, "PRODUCTOS", nombre), "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(encabezado)
        w.writerows(filas)


def _arbol(productos, ventas, testeos=None):
    """Arbol temporal con las herramientas que leen sus CSV desde su propia ubicacion."""
    base = tempfile.mkdtemp(prefix="d3_test_")
    os.makedirs(os.path.join(base, "PRODUCTOS"))
    os.makedirs(os.path.join(base, "Ads", "_TOOLS"))
    for f in ("gen_finanzas.py", "gen_testeos.py", "mercado.py"):
        shutil.copy(os.path.join(TOOLS, f), os.path.join(base, "Ads", "_TOOLS", f))
    _csv(base, "_DIM_PRODUCTOS.csv", ["producto_key", "moneda", "tasa", "cpa_be_q", "mercado"], productos)
    _csv(base, "_DIM_MERCADOS.csv",
         ["mercado", "pais", "moneda", "simbolo", "persona", "registro_sanitario"],
         [["GT", "Guatemala", "GTQ", "Q", "voseo", "MSPAS"], ["CO", "Colombia", "COP", "$", "tuteo", "INVIMA"]])
    _csv(base, "_PARAMETROS_FINANZAS.csv", ["parametro", "valor"],
         [["tasa_usd_gtq", "7.62"], ["tasa_cop_usd", "4000"]])
    _csv(base, "_DIM_PRECIOS.csv",
         ["producto_key", "unidades", "precio_q", "costo_proveedor_total_q", "flete_q", "estado"],
         [["GTP", "1", "200", "40", "34", "OK"], ["COP_P", "1", "80000", "20000", "9000", "OK"]])
    _csv(base, "_FACT_VENTAS.csv",
         ["ventana_ini", "ventana_fin", "dias", "rol_ventana", "producto_key", "conjunto", "ventas",
          "total_q", "spend_usd"], ventas)
    if testeos is not None:
        _csv(base, "_TESTEOS.csv",
             ["test_id", "test_nombre", "producto_key", "variable", "hipotesis", "angulo_fijo", "formato_fijo",
              "fecha_inicio", "estado", "brazo_key", "brazo_nombre", "concepto_key", "variante",
              "conjuntos_meta", "creativo_ref", "notas"], testeos)
    return base


def _correr(base, script, *args):
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    return subprocess.run([sys.executable, os.path.join(base, "Ads", "_TOOLS", script), *args],
                          cwd=base, env=env, capture_output=True, text=True, encoding="utf-8",
                          errors="replace", timeout=120)


VENTAS = [["2026-09-07", "2026-09-07", "1", "BASE", "GTP", "GTP_A_R1", "2", "400", "10"],
          ["2026-09-07", "2026-09-07", "1", "BASE", "COP_P", "COP_A_R1", "3", "240000", "10"]]


def _prod(tasa_co=str(CO_TASA), tasa_gt=str(GT_TASA)):
    return [["GTP", "USD", tasa_gt, "90", "GT"], ["COP_P", "COP", tasa_co, "30000", "CO"]]


# ── mercado.tasa_de_fila ─────────────────────────────────────────────────────
def test_tasa_de_fila():
    assert mercado.tasa_de_fila({"producto_key": "A", "tasa": "7.62"}) == 7.62
    for crudo in ("", "  ", "abc", "0", "-3"):
        try:
            mercado.tasa_de_fila({"producto_key": "SIN_TASA", "tasa": crudo})
        except mercado.TasaFaltante as error:
            assert "SIN_TASA" in str(error), str(error)
        else:
            raise AssertionError("tasa «%s» tenia que fallar" % crudo)


# ── decidir.py ───────────────────────────────────────────────────────────────
def test_decidir_sin_tasa_por_defecto():
    import decidir
    assert not hasattr(decidir, "TASA_Q_USD_DEFAULT")
    try:
        decidir.ic_cpa(3, 10.0, 0.95)
    except ValueError:
        pass
    else:
        raise AssertionError("ic_cpa sin tasa tenia que fallar")
    lo, _, hi = decidir.ic_cpa(3, 10.0, 0.95, tasa=7.62)
    assert lo < hi

    base = tempfile.mkdtemp(prefix="d3_dec_")
    try:
        ruta = os.path.join(base, "_DIM_PRODUCTOS.csv")
        with io.open(ruta, "w", encoding="utf-8", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["producto_key", "cpa_be_q", "cpa_base_q", "tasa"])
            w.writerow(["CON", "90", "30", "7.62"])
            w.writerow(["SIN", "90", "30", ""])
        previo = decidir.DIM_PROD_PATH
        decidir.DIM_PROD_PATH = ruta
        try:
            prods = decidir.cargar_productos()
        finally:
            decidir.DIM_PROD_PATH = previo
        assert prods["CON"]["tasa"] == 7.62 and prods["SIN"]["tasa"] is None, prods
    finally:
        shutil.rmtree(base)


def test_decidir_omite_producto_sin_tasa_y_usa_la_propia():
    import pandas as pd
    import decidir

    fila = dict(conjuntos=1, ventas=3.0, mensajes=40.0, spend_usd=10.0, ventas_3d=1.0, mensajes_3d=10.0,
                spend_3d=3.0, ventas_acum=3.0, mensajes_acum=40.0, spend_acum=10.0,
                link_clicks_acum=None, mensajes_enlace_acum=None,
                desde=pd.Timestamp("2026-09-01"), hasta=pd.Timestamp("2026-09-07"),
                desde_acum=pd.Timestamp("2026-09-01"), hasta_acum=pd.Timestamp("2026-09-07"),
                banda_ok=True, nombres_ok=True)
    df = pd.DataFrame([dict(fila, producto_key="GTP", celda="A"),
                       dict(fila, producto_key="COP_P", celda="A"),
                       dict(fila, producto_key="SIN_TASA", celda="A")])
    prods = {
        "GTP": {"producto_key": "GTP", "nombre": "GTP", "estado": "VIVO", "cpa_base_q": 30.0,
                "cpa_be_q": 90.0, "tasa": 7.62},
        "COP_P": {"producto_key": "COP_P", "nombre": "COP_P", "estado": "VIVO", "cpa_base_q": 10000.0,
                  "cpa_be_q": 30000.0, "tasa": 4000.0},
        "SIN_TASA": {"producto_key": "SIN_TASA", "nombre": "SIN_TASA", "estado": "VIVO", "cpa_base_q": 30.0,
                     "cpa_be_q": 90.0, "tasa": None},
    }
    guardado = (decidir.cargar_productos, decidir.cargar_fases, decidir.cargar_datos_duckdb,
                decidir._activar_fuente_db_si_corresponde)
    decidir.cargar_productos = lambda: prods
    decidir.cargar_fases = lambda: {}
    decidir.cargar_datos_duckdb = lambda **kw: df
    decidir._activar_fuente_db_si_corresponde = lambda: None
    err = io.StringIO()
    try:
        with contextlib.redirect_stderr(err):
            res = decidir.analizar_portafolio()
    finally:
        (decidir.cargar_productos, decidir.cargar_fases, decidir.cargar_datos_duckdb,
         decidir._activar_fuente_db_si_corresponde) = guardado
    evaluados = {p["producto_key"]: p for p in res["productos"]}
    assert set(evaluados) == {"GTP", "COP_P"}, sorted(evaluados)
    assert [o["producto_key"] for o in res["omitidos"]] == ["SIN_TASA"], res.get("omitidos")
    assert "SIN_TASA" in err.getvalue()
    # cada producto convierte con SU tasa: nunca 7.62 para el de Colombia
    assert evaluados["GTP"]["celdas"][0]["spend_q"] == round(10.0 * 7.62, 1)
    assert evaluados["COP_P"]["celdas"][0]["spend_q"] == round(10.0 * 4000.0, 1)


# ── atribuir.py ──────────────────────────────────────────────────────────────
def test_atribuir_no_mezcla_mercados_ni_asume_tasa():
    import atribuir
    prods = {"GTP": {"producto_key": "GTP", "mercado": "GT", "tasa": "7.62"},
             "COP_P": {"producto_key": "COP_P", "mercado": "CO", "tasa": "3152.5"},
             "SIN": {"producto_key": "SIN", "mercado": "GT", "tasa": ""}}
    assert atribuir.q({"producto_key": "GTP", "spend_usd": "10"}, prods) == 76.2
    try:
        atribuir.q({"producto_key": "SIN", "spend_usd": "10"}, prods)
    except mercado.TasaFaltante as error:
        assert "SIN" in str(error)
    else:
        raise AssertionError("atribuir.q sin tasa tenia que fallar")
    assert atribuir.un_solo_mercado([{"producto_key": "GTP"}], prods) == "GT"
    try:
        atribuir.un_solo_mercado([{"producto_key": "GTP"}, {"producto_key": "COP_P"}], prods)
    except mercado.MercadoError as error:
        assert "GTP" in str(error) and "COP_P" in str(error)
    else:
        raise AssertionError("un corte GT+CO tenia que fallar")


# ── gen_finanzas.py ──────────────────────────────────────────────────────────
def _semanal(base):
    with io.open(os.path.join(base, "PRODUCTOS", "_FACT_SEMANAL.csv"), encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def test_gen_finanzas_un_total_por_mercado():
    base = _arbol(_prod(), VENTAS)
    try:
        r = _correr(base, "gen_finanzas.py")
        assert r.returncode == 0, r.stderr + r.stdout
        filas = _semanal(base)
        totales = {x["mercado"]: x for x in filas if x["producto_key"] == "TOTAL"}
        assert set(totales) == {"GT", "CO"}, totales
        assert totales["GT"]["moneda"] == "GTQ" and totales["CO"]["moneda"] == "COP"
        assert float(totales["GT"]["pauta_q"]) == round(10 * GT_TASA, 2)      # 76.2
        assert float(totales["CO"]["pauta_q"]) == round(10 * CO_TASA, 2)      # 40000
        assert float(totales["GT"]["ventas"]) == 2 and float(totales["CO"]["ventas"]) == 3
        # nunca una cifra que sume las dos monedas
        assert all(abs(float(x["pauta_q"]) - (10 * GT_TASA + 10 * CO_TASA)) > 1 for x in filas)
        por_prod = {x["producto_key"]: x["mercado"] for x in filas if x["producto_key"] != "TOTAL"}
        assert por_prod == {"GTP": "GT", "COP_P": "CO"}, por_prod
        txt = io.open(os.path.join(base, "PRODUCTOS", "_REPORTE_SEMANAL.txt"), encoding="utf-8").read()
        assert "MERCADO GT (GTQ)" in txt and "MERCADO CO (COP)" in txt
    finally:
        shutil.rmtree(base)


def test_gen_finanzas_producto_sin_tasa_se_detiene_nombrandolo():
    base = _arbol(_prod(tasa_co=""), VENTAS)
    try:
        r = _correr(base, "gen_finanzas.py")
        assert r.returncode == 1, (r.returncode, r.stderr)
        assert "COP_P" in r.stderr and "tasa" in r.stderr, r.stderr
    finally:
        shutil.rmtree(base)


# ── gen_testeos.py ───────────────────────────────────────────────────────────
def _brazos(pk, conj):
    return ["T_" + pk, "Test " + pk, pk, "concepto", "h", "ANG", "IMAGEN", "2026-09-01", "EN CURSO", "A",
            "Brazo A", "C1", "v1", conj, "", ""]


def test_gen_testeos_cpa_con_la_tasa_del_producto_de_cada_test():
    base = _arbol(_prod(), VENTAS, testeos=[_brazos("GTP", "GTP_A_R1"), _brazos("COP_P", "COP_A_R1")])
    try:
        r = _correr(base, "gen_testeos.py", "--liviano")
        assert r.returncode == 0, r.stderr + r.stdout
        html = io.open(os.path.join(base, "PRODUCTOS", "_TESTEOS.html"), encoding="utf-8").read()
        assert "Q%.0f" % (10 / 2 * GT_TASA) in html, "CPA GT = 5 USD x 7.62"
        assert "$%.0f" % (10 / 3 * CO_TASA) in html, "CPA CO = 3.33 USD x 4000, con el simbolo de su mercado"
    finally:
        shutil.rmtree(base)


def test_gen_testeos_sin_tasa_avisa_y_no_inventa_cpa():
    base = _arbol(_prod(tasa_co=""), VENTAS, testeos=[_brazos("COP_P", "COP_A_R1")])
    try:
        r = _correr(base, "gen_testeos.py", "--liviano")
        assert r.returncode == 0, r.stderr + r.stdout
        assert "COP_P" in r.stderr and "sin CPA" in r.stderr, r.stderr
        html = io.open(os.path.join(base, "PRODUCTOS", "_TESTEOS.html"), encoding="utf-8").read()
        assert "sin tasa" in html and "$%.0f" % (10 / 3 * GT_TASA) not in html
    finally:
        shutil.rmtree(base)


# ── gen_pl.py ────────────────────────────────────────────────────────────────
def test_gen_pl_es_explicitamente_gt():
    import gen_pl
    previo = (gen_pl._prods, gen_pl._merc)
    gen_pl._prods = {"GTP": {"producto_key": "GTP", "mercado": "GT", "tasa": "7.62"},
                     "COP_P": {"producto_key": "COP_P", "mercado": "CO", "tasa": "3152.5"},
                     "SIN": {"producto_key": "SIN", "mercado": "GT", "tasa": ""}}
    gen_pl._merc = {}
    try:
        assert gen_pl.MERCADO_PL == "GT"
        assert gen_pl.es_mercado_pl({"producto_key": "GTP"}) is True
        assert gen_pl.es_mercado_pl({"producto_key": "COP_P"}) is False
        assert gen_pl.pauta_local({"producto_key": "GTP", "spend_usd": "10"}) == 10 * 7.62
        try:
            gen_pl.pauta_local({"producto_key": "SIN", "spend_usd": "10"})
        except mercado.TasaFaltante as error:
            assert "SIN" in str(error)
        else:
            raise AssertionError("gen_pl sin tasa tenia que fallar")
    finally:
        gen_pl._prods, gen_pl._merc = previo


TESTS = [test_tasa_de_fila, test_decidir_sin_tasa_por_defecto,
         test_decidir_omite_producto_sin_tasa_y_usa_la_propia,
         test_atribuir_no_mezcla_mercados_ni_asume_tasa, test_gen_finanzas_un_total_por_mercado,
         test_gen_finanzas_producto_sin_tasa_se_detiene_nombrandolo,
         test_gen_testeos_cpa_con_la_tasa_del_producto_de_cada_test,
         test_gen_testeos_sin_tasa_avisa_y_no_inventa_cpa, test_gen_pl_es_explicitamente_gt]


def main():
    fallas = 0
    for t in TESTS:
        try:
            t()
            print("  OK     %s" % t.__name__)
        except Exception as error:  # noqa: BLE001 — se reporta y se cuenta
            fallas += 1
            print("  FALLA  %s: %s: %s" % (t.__name__, type(error).__name__, error))
    print("\n%d de %d casos pasan." % (len(TESTS) - fallas, len(TESTS)))
    return 1 if fallas else 0


if __name__ == "__main__":
    sys.exit(main())
