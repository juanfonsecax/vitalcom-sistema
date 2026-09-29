#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_multimercado_d4.py — GATE: el ingreso manual de Colombia y la corrida nocturna de GT no se cruzan.

Congela lo que D4 (multi-mercado) no puede romper:
  · ingerir_meta.py clasifica por _DIM_PRODUCTOS (no por un diccionario) y `--producto` asigna todo
    un export de cuenta EXTERNA a su producto, con la divisa del propio export o la del producto;
  · GT queda igual (mismos productos, misma conversion de COP en CP1, alias de nombre);
  · ingerir_lucidsales.py: un producto de cuenta EXTERNA solo entra con `--producto`/`--mercado`,
    queda con cuenta_alias=EXTERNA y su gasto sale de la moneda del producto;
  · la corrida nocturna (bajar_meta_insights) nunca ingiere un producto EXTERNA.

Corre con pytest (tmp dirs) o directo:  python Ads/_TOOLS/test_multimercado_d4.py
No escribe en PRODUCTOS/ ni toca Postgres: solo lee y usa directorios temporales.
"""

import csv
import io
import json
import os
import sys
import tempfile

os.environ.setdefault("PGDATABASE", "vitalcom_test")   # ningun test de este archivo debe tocar `vitalcom`

TOOLS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TOOLS)
import pandas as pd  # noqa: E402

# Cada herramienta envuelve sys.stdout/sys.stderr al importarse; el envoltorio anterior, si nadie lo
# retiene, se recoge y cierra el buffer real. Se retienen los anteriores mientras se importan las tres.
_RETENIDOS = []
for _modulo in ("ingerir_meta", "ingerir_lucidsales", "bajar_meta_insights"):
    _RETENIDOS.extend([sys.stdout, sys.stderr])
    __import__(_modulo)
im, ils, bmi = sys.modules["ingerir_meta"], sys.modules["ingerir_lucidsales"], sys.modules["bajar_meta_insights"]

COP = 3152.5
PRODUCTOS_ENC = ["producto_key", "nombre_display", "slug_carpeta", "cuenta_alias", "moneda", "clave_campana",
                 "mercado"]
PRODUCTOS_FILAS = [
    ["NUSAVA", "NUSAVA B12", "NusavaB12", "GTR7", "USD", "NUSAVAB12", "GT"],
    ["VARICOSE", "Varicose Veins Ointment", "VARICOSE", "GTR7", "USD", "VARICOSE", "GT"],
    ["OVULOS_PURITY", "Ovulos Purity Hernatura", "OVULOS_PURITY", "EXTERNA", "COP", "OVULOS / PURITY", "CO"],
]


def _csv(ruta, encabezado, filas):
    with io.open(ruta, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(encabezado)
        w.writerows(filas)
    return ruta


def _dim_productos(tmp):
    return _csv(os.path.join(tmp, "_DIM_PRODUCTOS.csv"), PRODUCTOS_ENC, PRODUCTOS_FILAS)


def _xlsx_meta(tmp, filas, con_divisa=True, nombre="Informe-sin-titulo.xlsx"):
    """Export de Ads Manager: una fila por conjunto y la fila de TOTAL DE CUENTA sin campana."""
    filas_df = []
    for camp, conj, gasto, div in filas:
        f = {"Nombre de la campaña": camp, "Nombre del conjunto de anuncios": conj,
             "Importe gastado": gasto, "Impresiones": 1000, "Clics en el enlace": 50, "Clics (todos)": 80,
             "TASA DE CONVERSION A WHATSAPP": 0.1, "Inicio del informe": "2026-09-20",
             "Fin del informe": "2026-09-20"}
        if con_divisa:
            f["Divisa"] = div
        filas_df.append(f)
    total = {"Importe gastado": sum(f["Importe gastado"] for f in filas_df), "Impresiones": 5,
             "Inicio del informe": "2026-09-20", "Fin del informe": "2026-09-20"}
    if con_divisa:
        total["Divisa"] = filas[0][3]
    filas_df.append(total)
    ruta = os.path.join(tmp, nombre)
    pd.DataFrame(filas_df).to_excel(ruta, index=False)
    return ruta


def _productos_meta(tmp):
    return im.cargar_productos_meta(_dim_productos(tmp))


def test_meta_co_export_con_producto_forzado_y_divisa_del_export():
    with tempfile.TemporaryDirectory() as tmp:
        ruta = _xlsx_meta(tmp, [("Campana cualquiera", "Conjunto A", 63050.0, "COP")])
        filas, _, err = im.procesar(ruta, {}, _productos_meta(tmp), forzar="OVULOS_PURITY")
        assert err is None
        assert len(filas) == 1
        f = filas[0]
        assert f["producto_key"] == "OVULOS_PURITY"
        assert f["cuenta_alias"] == "EXTERNA" and f["cuenta_id"] == ""
        assert f["spend_usd"] == round(63050.0 / COP, 2) == 20.0


def test_meta_co_sin_columna_divisa_usa_la_moneda_del_producto():
    with tempfile.TemporaryDirectory() as tmp:
        ruta = _xlsx_meta(tmp, [("OVULOS / PURITY - test", "Conjunto A", 31525.0, None)], con_divisa=False)
        filas, _, err = im.procesar(ruta, {}, _productos_meta(tmp))     # clasifica por nombre
        assert err is None
        assert filas[0]["producto_key"] == "OVULOS_PURITY"
        assert filas[0]["spend_usd"] == 10.0


def test_meta_sin_divisa_y_sin_producto_no_asume_usd():
    with tempfile.TemporaryDirectory() as tmp:
        ruta = _xlsx_meta(tmp, [("Campana ajena", "Conjunto X", 100.0, None)], con_divisa=False)
        filas, _, err = im.procesar(ruta, {}, _productos_meta(tmp))
        assert filas is None and "Divisa" in err


def test_meta_divisa_sin_tasa_rechaza_el_archivo():
    with tempfile.TemporaryDirectory() as tmp:
        ruta = _xlsx_meta(tmp, [("Campana", "Conjunto", 100.0, "EUR")])
        filas, _, err = im.procesar(ruta, {}, _productos_meta(tmp), forzar="OVULOS_PURITY")
        assert filas is None and "EUR" in err and "tasa" in err


def test_meta_gt_igual_que_antes():
    """GT: clasificacion por nombre, alias de cuenta por prefijo, USD sin conversion, COP de CP1 convertido."""
    with tempfile.TemporaryDirectory() as tmp:
        ruta = _xlsx_meta(tmp, [
            ("GTR7_NUSAVAB12_TEST", "GTR7_NUSAVA_ANG1", 12.5, "USD"),
            ("GTR7-VARICES-X", "GTR7-VARICES-CJ", 8.0, "USD"),
            ("CP1_NUSAVA", "CP1_NUSAVA_CJ", 3152.5, "COP")])
        filas, _, err = im.procesar(ruta, {}, _productos_meta(tmp))
        assert err is None
        por = {f["conjunto"]: f for f in filas}
        n = por["GTR7_NUSAVA_ANG1"]
        assert (n["producto_key"], n["cuenta_alias"], n["spend_usd"]) == ("NUSAVA", "GTR7", 12.5)
        assert por["GTR7-VARICES-CJ"]["producto_key"] == "VARICOSE"      # alias historico
        c = por["CP1_NUSAVA_CJ"]
        assert (c["cuenta_alias"], c["spend_usd"]) == ("CP1", 1.0)


def test_meta_gt_clasificacion_identica_a_la_dimension_real():
    """Los productos GT reales siguen resolviendo por los mismos nombres (no hay diccionario aparte)."""
    productos = im.cargar_productos_meta()
    for texto, esperado in [("GTR0_TINNIDROP_A", "TINNIDROP"), ("GTR13_CLEARSTEM_B", "CLEARSTEM"),
                            ("GTR7_NUSAVA_C", "NUSAVA"), ("GTR7_VARICOSE_D", "VARICOSE"),
                            ("GTR7_VARICES_E", "VARICOSE"), ("OVULOS / PURITY_F", "OVULOS_PURITY"),
                            ("GTR7_PRODUCTO_AJENO", "SIN_CLASIFICAR")]:
        assert im.producto_de(texto, "", {}, productos) == esperado, texto


def _export_lucidsales(tmp, filas):
    ruta = os.path.join(tmp, "report-2026-09-20-2026-09-20.json")
    with io.open(ruta, "w", encoding="utf-8") as fh:
        json.dump({"insights": filas}, fh)
    return ruta


def _fila_ls(producto, cuenta, total, spend):
    return {"accountTitle": cuenta, "campaignTitle": "C", "adSetTitle": "CJ", "adTitle": "AD",
            "producto": producto, "messages": 4, "clicks": 3, "impressions": 90, "spend": spend,
            "sells": 1, "total": total, "adId": "ad_1"}


def test_lucidsales_co_forzado_queda_externa_y_convierte_desde_la_moneda_del_producto():
    with tempfile.TemporaryDirectory() as tmp:
        dimp = _dim_productos(tmp)
        productos = ils.cargar_productos(dimp, incluir_externos=True)
        externos = ils.cargar_externos(dimp)
        ruta = _export_lucidsales(tmp, [_fila_ls("Nombre que manda la tienda CO", "", 69000, 31525.0)])
        filas = ils.leer_export(ruta, "BASE", "LucidSales", productos, {}, "OVULOS_PURITY", externos)
        f = filas[0]
        assert f["producto_key"] == "OVULOS_PURITY"
        assert f["cuenta_alias"] == "EXTERNA" and f["moneda_origen"] == "COP"
        assert f["spend_usd"] == 10.0
        assert f["total_q"] == 69000.0          # monto de venta tal cual, en la moneda del mercado CO


def test_lucidsales_externo_sin_flag_no_se_clasifica():
    with tempfile.TemporaryDirectory() as tmp:
        dimp = _dim_productos(tmp)
        assert "OVULOS_PURITY" not in ils.cargar_productos(dimp)
        assert list(ils.cargar_productos(dimp, mercado="CO")) == ["OVULOS_PURITY"]
        assert "OVULOS_PURITY" not in ils.cargar_productos(dimp, mercado="GT")
        ruta = _export_lucidsales(tmp, [_fila_ls("Ovulos Purity", "", 69000, 31525.0)])
        filas = ils.leer_export(ruta, "BASE", "LucidSales", ils.cargar_productos(dimp), {}, None,
                                ils.cargar_externos(dimp))
        assert filas[0]["producto_key"] == "SIN_CLASIFICAR"


def test_lucidsales_gt_sin_cambios():
    with tempfile.TemporaryDirectory() as tmp:
        dimp = _dim_productos(tmp)
        ruta = _export_lucidsales(tmp, [_fila_ls("Nusava B12", "598687956219141", 219, 10.0)])
        cuentas = {"598687956219141": {"alias": "GTR7", "moneda": "USD"}}
        f = ils.leer_export(ruta, "BASE", "LucidSales", ils.cargar_productos(dimp), cuentas, None,
                            ils.cargar_externos(dimp))[0]
        assert (f["producto_key"], f["cuenta_alias"], f["moneda_origen"], f["spend_usd"], f["total_q"]) == \
               ("NUSAVA", "GTR7", "USD", 10.0, 219.0)


def _correr_main_ls(dimp, argv):
    previo, prev_argv = ils.DIMP, sys.argv
    try:
        ils.DIMP = dimp
        sys.argv = ["ingerir_lucidsales.py"] + argv
        ils.main()
        return None
    except SystemExit as e:
        return str(e)
    finally:
        ils.DIMP, sys.argv = previo, prev_argv


def test_lucidsales_producto_desconocido_o_de_otro_mercado_bloquea():
    with tempfile.TemporaryDirectory() as tmp:
        dimp = _dim_productos(tmp)
        ruta = _export_lucidsales(tmp, [_fila_ls("x", "", 1, 1.0)])
        assert "no tiene fila" in _correr_main_ls(dimp, [ruta, "--producto", "NO_EXISTE", "--dry-run"])
        assert "mercado CO" in _correr_main_ls(dimp, [ruta, "--producto", "OVULOS_PURITY",
                                                       "--mercado", "GT", "--dry-run"])
        assert "no existe" in _correr_main_ls(dimp, [ruta, "--mercado", "ZZ", "--dry-run"])


def test_nocturna_no_recoge_productos_externos():
    """La lista de cuentas de la corrida nocturna sale de _DIM_CUENTAS (sin EXTERNA), y aunque una
    cuenta GT devuelva un anuncio con el nombre de un producto CO, se excluye como ajeno."""
    cuentas = bmi.leer_cuentas_activas()
    assert cuentas and all(c["cuenta_id"] and c["cuenta_alias"].upper() != "EXTERNA" for c in cuentas)

    externos = im.productos_externos()
    assert "OVULOS_PURITY" in externos          # el producto CO real esta declarado como EXTERNA

    crudos = [{"ad_name": "AD ~ OVULOS_PURITY|ANG|C1.CN01|NC2|2X1|BOT", "campaign_name": "OVULOS / PURITY",
               "adset_name": "CJ_OVULOS", "spend": "12.0", "impressions": "10"}]
    previo = bmi.insights_de
    try:
        bmi.insights_de = lambda cuenta_id, fecha, token, reintentos=3: crudos
        propios, gasto_excl, n_excl = bmi.procesar_cuenta(
            {"cuenta_alias": "GTR 7", "cuenta_id": "598687956219141", "moneda": "USD"},
            "2026-09-20", "token-falso", {})
    finally:
        bmi.insights_de = previo
    assert propios == [] and n_excl == 1 and gasto_excl == 12.0


def main():
    fallas = 0
    for nombre, fn in sorted(globals().items()):
        if nombre.startswith("test_") and callable(fn):
            try:
                fn()
                print("  OK     " + nombre)
            except Exception as e:   # noqa: BLE001
                fallas += 1
                print("  FALLA  %s: %s: %s" % (nombre, type(e).__name__, e))
    print("\n%s." % ("0 fallas" if not fallas else "%d falla(s)" % fallas))
    return 1 if fallas else 0


if __name__ == "__main__":
    sys.exit(main())
