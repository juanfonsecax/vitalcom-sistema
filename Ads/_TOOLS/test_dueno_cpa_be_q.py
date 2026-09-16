#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_dueno_cpa_be_q.py — GATE DEL PUNTERO "DUENO" DE cpa_be_q EN FLUJO.json
(G0.5 punto 4.6, 15-sep-2026).

DOCTRINA/FLUJO.json declaraba, en el nodo F1.paquete, que "break-even calculado
(cpa_be_q)" lo produce "etapa-1 · Ads/_TOOLS/costear.py". Falso en los dos sentidos:
costear.py NUNCA escribe ningun CSV (es puro calculo, stdout/JSON) y el numero que SI
calcula sale de la tabla ESTATICA de _DIM_COSTEO.csv, no del "ponderado real por mix
vendido" que las notas de _DIM_PRODUCTOS.csv describen (BE v3/v4). El escritor real de
_DIM_PRODUCTOS.csv — incluido cpa_be_q — es el subagente etapa-guardar-producto (su
propia doc, SALIDA 5, dice explicitamente que rellena "los umbrales cpa_be_q,
cpa_base_q..."), exactamente como TODOS los demas items de esa misma lista `produce`
en FLUJO.json (2_DATA_PRODUCTO.txt, 1_HACER_MANUAL.txt, los conjuntos en
_DIM_CONJUNTOS.csv) ya declaraban.

Este archivo es deliberadamente independiente de test_flujo.py (que se edita en otra
rama en paralelo, G0.5 punto 3) para no competir por el mismo archivo.

USO:  python Ads/_TOOLS/test_dueno_cpa_be_q.py     (exit 0 = pasa, 1 = falla)
"""
import io
import json
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FLUJO_JSON = os.path.join(BASE, "DOCTRINA", "FLUJO.json")


def _nodo_cpa_be_q():
    with io.open(FLUJO_JSON, encoding="utf-8") as fh:
        data = json.load(fh)
    for fase in data["fases"]:
        for nodo in fase["nodos"]:
            for item in nodo.get("produce", []):
                if item.get("campo") == "cpa_be_q" or "cpa_be_q" in item.get("dato", ""):
                    return item
    return None


def test_dueno_apunta_a_etapa_guardar_producto():
    item = _nodo_cpa_be_q()
    ok = item is not None and "etapa-guardar-producto" in item.get("dueno", "")
    print(("  OK     " if ok else "  FALLA  ")
          + "cpa_be_q declara a etapa-guardar-producto como dueno (quien de verdad escribe "
            "_DIM_PRODUCTOS.csv), no a costear.py (que solo calcula, nunca escribe CSV)"
          + ("" if ok else f"\n         item={item!r}"))
    return 0 if ok else 1


def test_predicado_no_se_toco():
    """El fix es SOLO el texto de 'dueno' — el predicado que flujo.py evalua de verdad
    sigue exactamente igual (csv_campo sobre _DIM_PRODUCTOS.csv, campo cpa_be_q, num_min 1)."""
    item = _nodo_cpa_be_q()
    pred = item.get("predicado", {}) if item else {}
    ok = (pred.get("tipo") == "csv_campo" and pred.get("csv") == "_DIM_PRODUCTOS.csv"
          and pred.get("campo") == "cpa_be_q" and pred.get("num_min") == 1
          and pred.get("where") == {"producto_key": "{pk}"})
    print(("  OK     " if ok else "  FALLA  ")
          + "el predicado evaluado por flujo.py no cambio, solo la atribucion de 'dueno'"
          + ("" if ok else f"\n         predicado={pred!r}"))
    return 0 if ok else 1


def main():
    fallas = 0
    fallas += test_dueno_apunta_a_etapa_guardar_producto()
    fallas += test_predicado_no_se_toco()
    print(f"\n{'0 fallas' if not fallas else str(fallas) + ' falla(s)'}.")
    return 1 if fallas else 0


if __name__ == "__main__":
    sys.exit(main())
