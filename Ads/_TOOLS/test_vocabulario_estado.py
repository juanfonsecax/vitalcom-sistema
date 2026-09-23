#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_vocabulario_estado.py — GATE del dueño único del vocabulario de estado_producto
(g07-cimientos T2 ALSO-a, 22-sep-2026).

Antes de esta fila, el estado NUEVO de _DIM_PRODUCTOS.csv (OVULOS_PURITY) no tenia dueño en
ningun vocabulario, y el test dbt `accepted_values` de _models.yml repetia la lista aparte
(VIVO/PAUSADO/LISTO/ARCHIVADO) -- dos versiones de la misma verdad, y la real (NUEVO incluido)
rompia el build. Este test congela: (1) que gen_vocabulario.py declara las 5 filas del eje
estado_producto, (2) que todo estado que aparece hoy en _DIM_PRODUCTOS.csv tiene fila en ese eje,
y (3) que _models.yml ya no hardcodea la lista (lee de stg_vocabulario_estado_producto).

USO:  python Ads/_TOOLS/test_vocabulario_estado.py     (exit 0 = pasa, 1 = falla)
"""
import csv
import io
import os
import re
import sys

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROD = os.path.join(BASE, "PRODUCTOS")
WH = os.path.join(BASE, "warehouse")

ESPERADOS = {"NUEVO", "VIVO", "PAUSADO", "LISTO", "ARCHIVADO"}


def _leer_csv(path):
    with io.open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def test_vocabulario_declara_los_5_estados():
    filas = _leer_csv(os.path.join(PROD, "_DIM_VOCABULARIO.csv"))
    valores = {r["valor"] for r in filas if r.get("eje") == "estado_producto"}
    ok = valores == ESPERADOS
    print(("  OK     " if ok else "  FALLA  ") + "_DIM_VOCABULARIO.csv declara los 5 estados de "
          "_DIM_PRODUCTOS.csv en el eje estado_producto" + ("" if ok else f"\n         {valores}"))
    return 0 if ok else 1


def test_ningun_producto_usa_un_estado_sin_dueno():
    filas_prod = _leer_csv(os.path.join(PROD, "_DIM_PRODUCTOS.csv"))
    en_uso = {(r.get("estado") or "").strip().upper() for r in filas_prod if r.get("estado")}
    huerfanos = en_uso - ESPERADOS
    ok = not huerfanos
    print(("  OK     " if ok else "  FALLA  ") + "todo estado de _DIM_PRODUCTOS.csv tiene fila en "
          "el vocabulario" + ("" if ok else f"\n         huerfanos={huerfanos}"))
    return 0 if ok else 1


def test_models_yml_no_hardcodea_la_lista():
    ruta = os.path.join(WH, "models", "_models.yml")
    txt = io.open(ruta, encoding="utf-8").read()
    sin_hardcode = "accepted_values" not in txt.split("name: estado")[1].split("- name:")[0]
    usa_vocabulario = "stg_vocabulario_estado_producto" in txt
    ok = sin_hardcode and usa_vocabulario
    print(("  OK     " if ok else "  FALLA  ") + "_models.yml lee el vocabulario de estado desde "
          "stg_vocabulario_estado_producto, no una lista hardcodeada"
          + ("" if ok else f"\n         sin_hardcode={sin_hardcode} usa_vocabulario={usa_vocabulario}"))
    return 0 if ok else 1


def test_stg_vocabulario_estado_producto_filtra_el_eje_correcto():
    ruta = os.path.join(WH, "models", "staging", "stg_vocabulario_estado_producto.sql")
    ok = os.path.exists(ruta)
    if ok:
        txt = io.open(ruta, encoding="utf-8").read()
        ok = bool(re.search(r"eje\s*=\s*'estado_producto'", txt))
    print(("  OK     " if ok else "  FALLA  ") + "stg_vocabulario_estado_producto.sql existe y "
          "filtra eje = 'estado_producto'")
    return 0 if ok else 1


def main():
    pruebas = [
        test_vocabulario_declara_los_5_estados,
        test_ningun_producto_usa_un_estado_sin_dueno,
        test_models_yml_no_hardcodea_la_lista,
        test_stg_vocabulario_estado_producto_filtra_el_eje_correcto,
    ]
    fallas = sum(p() for p in pruebas)
    print(f"\n{'0 fallas' if not fallas else str(fallas) + ' falla(s)'}.")
    return 1 if fallas else 0


if __name__ == "__main__":
    sys.exit(main())
