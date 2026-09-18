#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_ingerir_lucidsales.py — GATE DE LA INGESTA DE LUCIDSALES.

Congela lo que la simulación de Turmeric (22-sep-2026) encontró roto en
ingerir_lucidsales.py: un producto sin fila en _DIM_PRODUCTOS.csv caía en
SIN_CLASIFICAR con el diccionario PROD_KEY cableado a mano, y el chequeo de
integridad imprimía "JOIN cierra al 100%" igual — 120 filas, 35 ventas y
$165.69 perdidos en silencio, sin una sola alerta.

Dos arreglos, dos gates:
  1. producto_key() y el alias de cuenta salen de _DIM_PRODUCTOS.csv y
     _DIM_CUENTAS.csv (los dueños del dato), no de un diccionario aparte.
  2. Una fila SIN_CLASIFICAR o un conjunto huérfano hacen FALLAR la corrida
     (SystemExit, exit != 0) — pero DESPUÉS de escribir lo que sí se pudo
     clasificar: perder una venta real es peor que un aviso.

USO:  python Ads/_TOOLS/test_ingerir_lucidsales.py     (exit 0 = pasa, 1 = falla)
"""
import csv
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ingerir_lucidsales as ing  # noqa: E402


def _escribir_csv(path, header, filas):
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(filas)
    return path


def _escribir_export(path, filas):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump({"insights": filas}, fh)
    return path


def _fila_lucidsales(producto, cuenta_id, ad_set, ad_title, ad_id, sells=1, spend=10.0):
    return {
        "accountTitle": cuenta_id, "campaignTitle": "CAMPANA_TEST",
        "adSetTitle": ad_set, "adTitle": ad_title, "producto": producto,
        "messages": 5, "clicks": 3, "impressions": 100,
        "spend": spend, "sells": sells, "total": sells * 200, "adId": ad_id,
    }


def test_producto_key_variantes_reales(tmp):
    """Las keywords se derivan de _DIM_PRODUCTOS.csv, sobre nombres REALES vistos
    en _FACT_VENTAS.csv (LucidSales nunca manda el mismo nombre dos veces igual)."""
    dimp = _escribir_csv(
        os.path.join(tmp, "_DIM_PRODUCTOS.csv"),
        ["producto_key", "nombre_display", "slug_carpeta"],
        [["TINNIDROP", "Tinnidrop Importado Original", "TINNIDROP"],
         ["NUSAVA", "NUSAVA B12", "NusavaB12"],
         ["CLEARSTEM", "Clearstem Mindbodyskin", "CLEARSTEM"],
         ["VARICOSE", "Varicose Veins Ointment", "VARICOSE"]])
    productos = ing.cargar_productos(dimp)

    casos = [
        ("Tinnidrop", "TINNIDROP"),
        ("Tinnidrop Importado Original", "TINNIDROP"),
        ("NUSAVA B12", "NUSAVA"),
        ("NUSAVA B12 oferta original importado", "NUSAVA"),
        ("NusavaB12", "NUSAVA"),
        ("Clearstem", "CLEARSTEM"),
        ("Clearstem Mindbodyskin Suplemento 90 Cápsulas Importado USA", "CLEARSTEM"),
        ("Varicose", "VARICOSE"),
        ("Varicose 2x1 oferta VER", "VARICOSE"),
        ("Turmeric Curcumin Importado", "SIN_CLASIFICAR"),
    ]
    fallas = 0
    for nombre, esperado in casos:
        obtenido = ing.producto_key(nombre, productos)
        if obtenido == esperado:
            print(f"  OK     producto_key({nombre!r}) = {esperado}")
        else:
            fallas += 1
            print(f"  FALLA  producto_key({nombre!r}) esperado={esperado} obtenido={obtenido}")
    return fallas


def test_cargar_cuentas_alias_compacto(tmp):
    """cuenta_alias pierde el espacio: el resto del sistema usa 'GTR7', no 'GTR 7'."""
    dimc = _escribir_csv(
        os.path.join(tmp, "_DIM_CUENTAS.csv"),
        ["cuenta_alias", "cuenta_id", "moneda"],
        [["GTR 7", "598687956219141", "USD"],
         ["CP1", "1346891653335162", "COP"]])
    cuentas = ing.cargar_cuentas(dimc)
    ok = (cuentas["598687956219141"]["alias"] == "GTR7"
          and cuentas["598687956219141"]["moneda"] == "USD"
          and cuentas["1346891653335162"]["alias"] == "CP1"
          and cuentas["1346891653335162"]["moneda"] == "COP")
    print(("  OK     " if ok else "  FALLA  ")
          + "cuenta_alias 'GTR 7' -> 'GTR7' (sin espacio), moneda por cuenta"
          + ("" if ok else f"\n         {cuentas}"))
    return 0 if ok else 1


def test_moneda_sin_tasa_bloquea(tmp):
    """Una cuenta nueva que factura en una moneda sin tasa declarada NO se ingiere
    como si fuera USD en silencio: bloquea con el nombre de la cuenta y la moneda."""
    export = _escribir_export(
        os.path.join(tmp, "sim-2026-09-14.json"),
        [_fila_lucidsales("Tinnidrop", "111", "CONJ_X", "AD_X", "ad_111")])
    cuentas = {"111": {"alias": "CUENTA_NUEVA", "moneda": "GTQ"}}
    try:
        ing.leer_export(export, "BASE", "LucidSales", {"TINNIDROP": ["tinnidrop"]}, cuentas)
        print("  FALLA  moneda GTQ sin tasa declarada no bloqueó (se habría costeado mal en silencio)")
        return 1
    except SystemExit as e:
        ok = "GTQ" in str(e) and "TASAS_A_USD" in str(e)
        print(("  OK     " if ok else "  FALLA  ")
              + "moneda sin tasa declarada bloquea con el nombre de la moneda y dónde arreglarlo"
              + ("" if ok else f"\n         mensaje: {e}"))
        return 0 if ok else 1


def _fixture_flujo(tmp, filas_export, conjuntos_conocidos):
    dimp = _escribir_csv(
        os.path.join(tmp, "_DIM_PRODUCTOS.csv"),
        ["producto_key", "nombre_display", "slug_carpeta"],
        [["TINNIDROP", "Tinnidrop Importado Original", "TINNIDROP"]])
    dimctas = _escribir_csv(
        os.path.join(tmp, "_DIM_CUENTAS.csv"),
        ["cuenta_alias", "cuenta_id", "moneda"],
        [["GTR 0", "1665221077707961", "USD"]])
    fact = _escribir_csv(os.path.join(tmp, "_FACT_VENTAS.csv"), ing.COLS, [])
    dimc = _escribir_csv(
        os.path.join(tmp, "_DIM_CONJUNTOS.csv"),
        ["conjunto_meta"], [[c] for c in conjuntos_conocidos])
    export = _escribir_export(os.path.join(tmp, "sim-2026-09-14.json"), filas_export)
    bkdir = os.path.join(tmp, "backups_csv")
    return dict(DIMP=dimp, DIMCTAS=dimctas, FACT=fact, DIMC=dimc, BKDIR=bkdir), export


def _correr_main(rutas, argv):
    previo = {k: getattr(ing, k) for k in rutas}
    prev_argv = sys.argv
    try:
        for k, v in rutas.items():
            setattr(ing, k, v)
        sys.argv = ["ingerir_lucidsales.py"] + argv
        ing.main()
        return None
    except SystemExit as e:
        return e
    finally:
        for k, v in previo.items():
            setattr(ing, k, v)
        sys.argv = prev_argv


def test_gate_bloquea_sin_perder_las_filas_buenas(tmp):
    """Turmeric (SIN_CLASIFICAR) mezclado con una fila buena de TINNIDROP: el proceso
    tiene que SALIR EN ROJO, pero las dos filas quedan escritas en _FACT_VENTAS.csv."""
    filas = [
        _fila_lucidsales("Tinnidrop", "1665221077707961", "CONJ_CONOCIDO", "AD_1", "ad_1"),
        _fila_lucidsales("Turmeric Curcumin Importado", "1665221077707961", "CONJ_CONOCIDO", "AD_2", "ad_2"),
    ]
    rutas, export = _fixture_flujo(tmp, filas, conjuntos_conocidos=["CONJ_CONOCIDO"])
    salida = _correr_main(rutas, [export])

    escritas = list(csv.DictReader(open(rutas["FACT"], newline="", encoding="utf-8")))
    bloqueo = salida is not None and salida.code != 0
    no_perdio_data = len(escritas) == 2
    ok = bloqueo and no_perdio_data
    print(("  OK     " if ok else "  FALLA  ")
          + "SIN_CLASIFICAR bloquea la corrida (exit != 0) sin perder las filas ya escritas"
          + ("" if ok else f"\n         bloqueo={bloqueo} filas_escritas={len(escritas)} salida={salida}"))
    return 0 if ok else 1


def test_gate_bloquea_por_conjunto_huerfano(tmp):
    """Un conjunto que no está en _DIM_CONJUNTOS.csv también bloquea, aunque el
    producto sí esté clasificado — antes solo emitía una advertencia y seguía verde."""
    filas = [_fila_lucidsales("Tinnidrop", "1665221077707961", "CONJ_HUERFANO", "AD_1", "ad_1")]
    rutas, export = _fixture_flujo(tmp, filas, conjuntos_conocidos=["OTRO_CONJUNTO"])
    salida = _correr_main(rutas, [export])
    ok = salida is not None and salida.code != 0
    print(("  OK     " if ok else "  FALLA  ")
          + "conjunto huérfano bloquea la corrida (exit != 0)"
          + ("" if ok else f"\n         salida={salida}"))
    return 0 if ok else 1


def test_corrida_limpia_no_bloquea(tmp):
    """Regresión: cuando todo clasifica y el conjunto es conocido, la corrida sigue
    pasando sin bloquear — el gate nuevo no puede convertirse en un falso rojo."""
    filas = [_fila_lucidsales("Tinnidrop", "1665221077707961", "CONJ_CONOCIDO", "AD_1", "ad_1")]
    rutas, export = _fixture_flujo(tmp, filas, conjuntos_conocidos=["CONJ_CONOCIDO"])
    salida = _correr_main(rutas, [export])
    ok = salida is None
    print(("  OK     " if ok else "  FALLA  ")
          + "una corrida limpia (todo clasificado, conjunto conocido) NO bloquea"
          + ("" if ok else f"\n         salida={salida}"))
    return 0 if ok else 1


def main():
    fallas = 0
    with tempfile.TemporaryDirectory() as tmp:
        fallas += test_producto_key_variantes_reales(tmp)
    with tempfile.TemporaryDirectory() as tmp:
        fallas += test_cargar_cuentas_alias_compacto(tmp)
    with tempfile.TemporaryDirectory() as tmp:
        fallas += test_moneda_sin_tasa_bloquea(tmp)
    with tempfile.TemporaryDirectory() as tmp:
        fallas += test_gate_bloquea_sin_perder_las_filas_buenas(tmp)
    with tempfile.TemporaryDirectory() as tmp:
        fallas += test_gate_bloquea_por_conjunto_huerfano(tmp)
    with tempfile.TemporaryDirectory() as tmp:
        fallas += test_corrida_limpia_no_bloquea(tmp)
    print(f"\n{'0 fallas' if not fallas else str(fallas) + ' falla(s)'}.")
    return 1 if fallas else 0


if __name__ == "__main__":
    sys.exit(main())
