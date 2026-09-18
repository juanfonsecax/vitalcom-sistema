#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_gen_plan.py — GATE DEL VALIDADOR DE PLANES (gen_plan.py --validar).

Congela dos defectos de la cadena de FASE 2 encontrados en la simulación de Turmeric
(22-sep-2026): `--validar` ignoraba cualquier ruta que se le pasara, y el escaneo por
defecto nunca abría `_PLAN_FASE2.json` (solo `_PLAN.json`) — así que un plan de FASE 2
sin `angulo_ganador` o sin `copy` en la raíz pasaba sin que nadie lo viera, hasta que
gen_publicacion.py bloqueaba cada anuncio con `{{FALTA_COPY}}` mucho más adelante.

USO:  python Ads/_TOOLS/test_gen_plan.py     (exit 0 = pasa, 1 = falla)
"""
import io
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_plan  # noqa: E402


def _escribir_plan(carpeta, nombre, data):
    ruta = os.path.join(carpeta, nombre)
    with io.open(ruta, "w", encoding="utf-8") as fh:
        json.dump(data, fh)
    return ruta


PLAN_FASE2_COMPLETO = {
    "schema": "fase2_lean/1", "producto_key": "X", "fase": 2,
    "angulo_ganador": "UN_ANGULO", "copy": "el copy unico de la fase",
    "conjuntos": [{"n": 1}],
}


def test_ruta_directa_valida_solo_ese_archivo(tmp):
    """--validar <ruta> ya no ignora la ruta: valida SOLO ese archivo, no el escaneo global."""
    carpeta = os.path.join(tmp, "PRODUCTO_A")
    os.makedirs(carpeta)
    bueno = _escribir_plan(carpeta, "_PLAN_FASE2.json", PLAN_FASE2_COMPLETO)
    encontrados = gen_plan.descubrir_planes(bueno)
    ok = encontrados == [bueno]
    print(("  OK     " if ok else "  FALLA  ")
          + "descubrir_planes(ruta) devuelve solo esa ruta, nunca escanea PRODUCTOS/"
          + ("" if ok else f"\n         obtenido={encontrados}"))
    return 0 if ok else 1


def test_ruta_inexistente_no_inventa_nada(tmp):
    encontrados = gen_plan.descubrir_planes(os.path.join(tmp, "no_existe.json"))
    ok = encontrados == []
    print(("  OK     " if ok else "  FALLA  ") + "una ruta que no existe no se inventa como plan valido")
    return 0 if ok else 1


def test_escaneo_encuentra_plan_fase2_y_fase3(tmp):
    """Antes solo se buscaba _PLAN.json: un producto en FASE 2 o 3 quedaba invisible."""
    carpeta = os.path.join(tmp, "PRODUCTO_B")
    os.makedirs(carpeta)
    p1 = _escribir_plan(carpeta, "_PLAN.json", {"schema": "plan/1", "fase": 1, "conjuntos": [],
                                                  "oferta": {"oferta_key": "1U"}})
    p2 = _escribir_plan(carpeta, "_PLAN_FASE2.json", PLAN_FASE2_COMPLETO)
    p3 = _escribir_plan(carpeta, "_PLAN_FASE3.json", dict(PLAN_FASE2_COMPLETO, fase=3))
    previo = gen_plan.PRODUCTOS
    try:
        gen_plan.PRODUCTOS = tmp
        encontrados = set(gen_plan.descubrir_planes())
    finally:
        gen_plan.PRODUCTOS = previo
    ok = encontrados == {p1, p2, p3}
    print(("  OK     " if ok else "  FALLA  ")
          + "el escaneo por defecto encuentra _PLAN.json, _PLAN_FASE2.json y _PLAN_FASE3.json"
          + ("" if ok else f"\n         obtenido={encontrados}"))
    return 0 if ok else 1


def test_plan_fase2_sin_copy_ni_angulo_ganador_falla(tmp):
    """El caso real de CLEARSTEM: plan de FASE 2 sin 'copy' en la raiz. gen_publicacion.py
    bloquearia cada anuncio con {{FALTA_COPY}} — este gate lo tiene que atrapar ANTES."""
    incompleto = dict(PLAN_FASE2_COMPLETO)
    incompleto.pop("copy")
    incompleto.pop("angulo_ganador")
    problemas = gen_plan.validar_plan_fase2o3(incompleto)
    ok = (len(problemas) == 2
          and any("copy" in p for p in problemas)
          and any("angulo_ganador" in p for p in problemas))
    print(("  OK     " if ok else "  FALLA  ")
          + "un plan de FASE 2 sin copy ni angulo_ganador falla con los dos motivos explicitos"
          + ("" if ok else f"\n         problemas={problemas}"))
    return 0 if ok else 1


def test_plan_fase2_completo_no_falla():
    problemas = gen_plan.validar_plan_fase2o3(PLAN_FASE2_COMPLETO)
    ok = problemas == []
    print(("  OK     " if ok else "  FALLA  ")
          + "un plan de FASE 2 con angulo_ganador y copy no genera error: cuenta y page_id "
          + "son de _DIM_PRODUCTOS.csv, no del plan"
          + ("" if ok else f"\n         problemas={problemas}"))
    return 0 if ok else 1


def test_plan_fase2_con_copy_por_conjunto_falla():
    """Lo que escribio etapa-6 en la simulacion de Turmeric siguiendo el esquema de FASE 1:
    el copy dentro de cada conjunto. gen_publicacion.py lo ignora y cada anuncio sale sin copy."""
    plan = dict(PLAN_FASE2_COMPLETO, copy=None,
                conjuntos=[{"n": 1, "copy": {"textos": ["el copy"]}}])
    problemas = gen_plan.validar_plan_fase2o3(plan)
    ok = len(problemas) == 1 and "copy" in problemas[0]
    print(("  OK     " if ok else "  FALLA  ")
          + "un plan de FASE 2 con el copy dentro de los conjuntos y no en la raiz falla"
          + ("" if ok else f"\n         problemas={problemas}"))
    return 0 if ok else 1


def test_plan_fase2_no_valida_el_array_conjuntos_en_disputa():
    """Deuda abierta (HANDOFF 2026-09-09): el esquema fase2_lean/1 (5x1) contradice la
    doctrina 1-1-5+1-1-5+1-2-5 y esa disputa NO se resuelve en este gate — un array
    'conjuntos' de cualquier forma (o vacio) no debe producir un error de este validador."""
    plan = dict(PLAN_FASE2_COMPLETO, conjuntos=[])
    problemas = gen_plan.validar_plan_fase2o3(plan)
    ok = problemas == []
    print(("  OK     " if ok else "  FALLA  ")
          + "el validador de FASE 2/3 no opina sobre la forma del array 'conjuntos'"
          + ("" if ok else f"\n         problemas={problemas}"))
    return 0 if ok else 1


def main():
    fallas = 0
    with tempfile.TemporaryDirectory() as tmp:
        fallas += test_ruta_directa_valida_solo_ese_archivo(tmp)
    with tempfile.TemporaryDirectory() as tmp:
        fallas += test_ruta_inexistente_no_inventa_nada(tmp)
    with tempfile.TemporaryDirectory() as tmp:
        fallas += test_escaneo_encuentra_plan_fase2_y_fase3(tmp)
    with tempfile.TemporaryDirectory() as tmp:
        fallas += test_plan_fase2_sin_copy_ni_angulo_ganador_falla(tmp)
    fallas += test_plan_fase2_completo_no_falla()
    fallas += test_plan_fase2_con_copy_por_conjunto_falla()
    fallas += test_plan_fase2_no_valida_el_array_conjuntos_en_disputa()
    print(f"\n{'0 fallas' if not fallas else str(fallas) + ' falla(s)'}.")
    return 1 if fallas else 0


if __name__ == "__main__":
    sys.exit(main())
