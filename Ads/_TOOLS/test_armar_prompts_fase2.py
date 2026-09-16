#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_armar_prompts_fase2.py — GATE DE LOS PRECIOS REALES EN armar_prompts_fase2.py
(G0.5 punto 4.5, 15-sep-2026).

leer_escalera() ya leia PRODUCTOS/_DIM_PRECIOS.csv desde el 08-sep-2026 (arreglo previo),
pero cuando devolvia None (sin fila ACTIVA para el producto) el llamador caia en SILENCIO
a un PRECIOS_GT hardcodeado en el codigo — los precios de TINNIDROP (Q179/Q239/Q299) para
CUALQUIER producto sin fila propia, y los de CLEARSTEM (Q199/Q299/Q399) en la adaptacion
de LucidBot, sin condicionar siquiera por producto. Misma clase de bug que
buscar_foto_producto()/leer_envase() (07-sep): sin el dato real, se bloquea, nunca se
asumen los precios de otro producto (invariante 4, CLAUDE.md).

USO:  python Ads/_TOOLS/test_armar_prompts_fase2.py     (exit 0 = pasa, 1 = falla)
"""
import csv
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import armar_prompts_fase2 as ap  # noqa: E402


def _dim_precios(tmp, filas):
    ruta = os.path.join(tmp, "_DIM_PRECIOS.csv")
    cols = ["producto_key", "unidades", "etiqueta", "precio_q", "precio_antes_q", "estado"]
    with open(ruta, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for f in filas:
            w.writerow({**{c: "" for c in cols}, **f})
    return ruta


def test_producto_sin_fila_bloquea_no_hereda_precios_de_otro():
    with tempfile.TemporaryDirectory() as tmp:
        _dim_precios(tmp, [{"producto_key": "TINNIDROP", "unidades": "1",
                            "precio_q": "179", "estado": "ACTIVO"}])
        viejo = ap.PROD_DIR
        ap.PROD_DIR = tmp
        try:
            ap.requerir_precios_reales("PRODUCTO_SIN_FILA")
            ok, msg = False, None
        except SystemExit as e:
            msg = str(e)
            ok = "PRODUCTO_SIN_FILA" in msg and "_DIM_PRECIOS.csv" in msg
        finally:
            ap.PROD_DIR = viejo
    print(("  OK     " if ok else "  FALLA  ")
          + "producto sin fila en _DIM_PRECIOS.csv BLOQUEA (nunca hereda los Q179 de TINNIDROP)"
          + ("" if ok else f"\n         msg={msg!r}"))
    return 0 if ok else 1


def test_producto_solo_inactivo_bloquea_igual():
    with tempfile.TemporaryDirectory() as tmp:
        _dim_precios(tmp, [{"producto_key": "VIEJO", "unidades": "1",
                            "precio_q": "99", "estado": "RETIRADO"}])
        viejo = ap.PROD_DIR
        ap.PROD_DIR = tmp
        try:
            ap.requerir_precios_reales("VIEJO")
            ok = False
        except SystemExit:
            ok = True
        finally:
            ap.PROD_DIR = viejo
    print(("  OK     " if ok else "  FALLA  ")
          + "una fila que existe pero no esta ACTIVA cuenta como 'sin precio real' — bloquea igual")
    return 0 if ok else 1


def test_producto_con_fila_activa_arma_la_escalera_real():
    with tempfile.TemporaryDirectory() as tmp:
        _dim_precios(tmp, [
            {"producto_key": "CLEARSTEM", "unidades": "1", "precio_q": "198.00", "estado": "ACTIVO"},
            {"producto_key": "CLEARSTEM", "unidades": "2", "precio_q": "289.00", "estado": "ACTIVO"},
            {"producto_key": "CLEARSTEM", "unidades": "3", "precio_q": "389.01", "estado": "ACTIVO"},
        ])
        viejo = ap.PROD_DIR
        ap.PROD_DIR = tmp
        try:
            precios = ap.requerir_precios_reales("CLEARSTEM")
        finally:
            ap.PROD_DIR = viejo
    ok = ("Q198" in precios["TIER_1"] and "Q289" in precios["TIER_2"] and "Q389" in precios["TIER_3"])
    print(("  OK     " if ok else "  FALLA  ")
          + "con fila ACTIVA arma la escalera REAL (Q198/Q289/Q389, no Q199/Q299/Q399 hardcodeados)"
          + ("" if ok else f"\n         obtenido={precios!r}"))
    return 0 if ok else 1


def test_no_quedan_diccionarios_precios_gt_hardcodeados():
    """Regresion literal: los tres bloques PRECIOS_GT viejos (CLEARSTEM, TINNIDROP, el
    fallback generico) escribian el TIER directo como string con un Q de por medio —
    p.ej. '"TIER_1": "1 Frasco (1 Mes) por Q199"'. Ninguna linea del modulo debe volver
    a declarar un TIER_1/2/3 así: la escalera SIEMPRE debe salir de precios_reales."""
    with open(ap.__file__, encoding="utf-8") as fh:
        lineas = fh.readlines()
    ofensivas = [l.strip() for l in lineas if ("TIER_1" in l or "TIER_2" in l or "TIER_3" in l)
                 and "por Q" in l]
    ok = not ofensivas
    print(("  OK     " if ok else "  FALLA  ")
          + "ningun TIER_1/2/3 queda declarado como string literal con precio adentro"
          + ("" if ok else f"\n         lineas: {ofensivas}"))
    return 0 if ok else 1


def main():
    fallas = 0
    fallas += test_producto_sin_fila_bloquea_no_hereda_precios_de_otro()
    fallas += test_producto_solo_inactivo_bloquea_igual()
    fallas += test_producto_con_fila_activa_arma_la_escalera_real()
    fallas += test_no_quedan_diccionarios_precios_gt_hardcodeados()
    print(f"\n{'0 fallas' if not fallas else str(fallas) + ' falla(s)'}.")
    return 1 if fallas else 0


if __name__ == "__main__":
    sys.exit(main())
