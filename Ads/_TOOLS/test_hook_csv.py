#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_hook_csv.py — GATE del contrato de atribucion F1/F2 en _DIM_CONJUNTOS.csv.

Congela la regla del 22-sep-2026 (decision operador: FASE 1 corre TODO EN IMAGEN): toda fila
NUEVA de _DIM_CONJUNTOS.csv (fecha_alta >= hook_csv.CUTOFF_ATRIBUCION_CONJUNTOS, origen_angulo
que no empieza con HEREDADO) tiene que declarar formato en {IMAGEN, VIDEO} y un concepto_key ya
clasificado; una fila FASE1 ademas tiene que ser IMAGEN. Las filas anteriores al cutoff, o
HEREDADO_*, nunca se marcan.

USO:  python Ads/_TOOLS/test_hook_csv.py     (exit 0 = pasa, 1 = falla)
"""
import csv
import io
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hook_csv  # noqa: E402

ENCABEZADO = ["producto_key", "conjunto_meta", "cuenta_alias", "campana_clave", "fase",
              "angulo_key", "angulo_nombre", "avatar", "dolor_nucleo", "emocion_dominante",
              "avatar_edad", "avatar_genero", "formato", "concepto_key", "tipo_hook",
              "nivel_conciencia", "rol_embudo", "rol_embudo_origen", "lleva_precio",
              "creativo_id", "origen_angulo", "estado", "verificado_en_csv", "fecha_alta",
              "notas"]

BASE_FILA = {c: "" for c in ENCABEZADO}


def _fila(**over):
    f = dict(BASE_FILA)
    f.update(over)
    return f


def _escribir(carpeta, filas):
    ruta = os.path.join(carpeta, "_DIM_CONJUNTOS.csv")
    with io.open(ruta, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=ENCABEZADO)
        w.writeheader()
        for f in filas:
            w.writerow(f)
    return ruta


def test_fila_post_cutoff_sin_clasificar_se_marca(tmp):
    ruta = _escribir(tmp, [_fila(
        producto_key="X", angulo_key="A", fase="FASE1", formato="IMAGEN",
        concepto_key="SIN_CLASIFICAR", origen_angulo="VOZ_REAL",
        fecha_alta="2026-09-23")])
    error = hook_csv.atribucion_conjuntos_invalida(ruta)
    ok = error is not None and "SIN_CLASIFICAR" in error
    print(("  OK     " if ok else "  FALLA  ")
          + "fila post-cutoff con concepto_key SIN_CLASIFICAR se marca")
    return 0 if ok else 1


def test_fila_pre_cutoff_no_se_marca(tmp):
    ruta = _escribir(tmp, [_fila(
        producto_key="X", angulo_key="A", fase="FASE1", formato="VIDEO",
        concepto_key="SIN_CLASIFICAR", origen_angulo="TRANSCRIPCION",
        fecha_alta="2026-09-16")])
    error = hook_csv.atribucion_conjuntos_invalida(ruta)
    ok = error is None
    print(("  OK     " if ok else "  FALLA  ")
          + "fila anterior al cutoff nunca se marca, aunque este SIN_CLASIFICAR"
          + ("" if ok else f"\n         error={error}"))
    return 0 if ok else 1


def test_fila_heredada_post_cutoff_no_se_marca(tmp):
    ruta = _escribir(tmp, [_fila(
        producto_key="X", angulo_key="A", fase="FASE2_ESCALA", formato="VIDEO",
        concepto_key="SIN_CLASIFICAR", origen_angulo="HEREDADO_JOIN_ENTREGA",
        fecha_alta="2026-09-25")])
    error = hook_csv.atribucion_conjuntos_invalida(ruta)
    ok = error is None
    print(("  OK     " if ok else "  FALLA  ")
          + "fila HEREDADO_* nunca se marca, sea cual sea su fecha_alta"
          + ("" if ok else f"\n         error={error}"))
    return 0 if ok else 1


def test_fila_fase1_post_cutoff_con_video_se_marca(tmp):
    ruta = _escribir(tmp, [_fila(
        producto_key="X", angulo_key="A", fase="FASE1", formato="VIDEO",
        concepto_key="C2_BENEFICIOS", origen_angulo="VOZ_REAL",
        fecha_alta="2026-09-23")])
    error = hook_csv.atribucion_conjuntos_invalida(ruta)
    ok = error is not None and "FASE1" in error
    print(("  OK     " if ok else "  FALLA  ")
          + "fila FASE1 post-cutoff con formato VIDEO se marca (F1 es todo IMAGEN)"
          + ("" if ok else f"\n         error={error}"))
    return 0 if ok else 1


def test_fila_post_cutoff_completa_no_se_marca(tmp):
    ruta = _escribir(tmp, [_fila(
        producto_key="X", angulo_key="A", fase="FASE1", formato="IMAGEN",
        concepto_key="C2_BENEFICIOS", origen_angulo="VOZ_REAL",
        fecha_alta="2026-09-23")])
    error = hook_csv.atribucion_conjuntos_invalida(ruta)
    ok = error is None
    print(("  OK     " if ok else "  FALLA  ")
          + "fila post-cutoff con formato y concepto_key completos no se marca"
          + ("" if ok else f"\n         error={error}"))
    return 0 if ok else 1


def test_ruta_que_no_es_dim_conjuntos_se_ignora(tmp):
    ruta = os.path.join(tmp, "_OTRA_COSA.csv")
    with io.open(ruta, "w", encoding="utf-8-sig", newline="") as fh:
        fh.write("a,b\n1,2\n")
    error = hook_csv.atribucion_conjuntos_invalida(ruta)
    ok = error is None
    print(("  OK     " if ok else "  FALLA  ") + "un CSV que no es _DIM_CONJUNTOS.csv se ignora")
    return 0 if ok else 1


def main():
    fallas = 0
    with tempfile.TemporaryDirectory() as tmp:
        fallas += test_fila_post_cutoff_sin_clasificar_se_marca(tmp)
    with tempfile.TemporaryDirectory() as tmp:
        fallas += test_fila_pre_cutoff_no_se_marca(tmp)
    with tempfile.TemporaryDirectory() as tmp:
        fallas += test_fila_heredada_post_cutoff_no_se_marca(tmp)
    with tempfile.TemporaryDirectory() as tmp:
        fallas += test_fila_fase1_post_cutoff_con_video_se_marca(tmp)
    with tempfile.TemporaryDirectory() as tmp:
        fallas += test_fila_post_cutoff_completa_no_se_marca(tmp)
    with tempfile.TemporaryDirectory() as tmp:
        fallas += test_ruta_que_no_es_dim_conjuntos_se_ignora(tmp)
    print(f"\n{'0 fallas' if not fallas else str(fallas) + ' falla(s)'}.")
    return 1 if fallas else 0


if __name__ == "__main__":
    sys.exit(main())
