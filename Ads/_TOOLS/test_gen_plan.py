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
    "schema": "plan/1", "producto_key": "X", "fase": 2,
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
    p3 = _escribir_plan(carpeta, "_PLAN_FASE3.json", dict(PLAN_FASE2_COMPLETO, fase=4))
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


def test_plan_fase2_lean_falla():
    """El esquema fase2_lean/1 (5 conjuntos x 1 concepto) contradice FASE2_ESTRUCTURA de la
    Guia Madre (1-1-5 ABO, Calet 16-ago) y quedo retirado el 17-sep-2026."""
    plan = dict(PLAN_FASE2_COMPLETO, schema="fase2_lean/1")
    problemas = gen_plan.validar_plan_fase2o3(plan)
    ok = len(problemas) == 1 and "plan/1" in problemas[0]
    print(("  OK     " if ok else "  FALLA  ")
          + "un plan de FASE 2 en el esquema retirado fase2_lean/1 falla"
          + ("" if ok else f"\n         problemas={problemas}"))
    return 0 if ok else 1


def test_plan_fase2_no_valida_el_array_conjuntos():
    """La estructura de FASE 2/3 la arma gen_publicacion.py desde _PARAMETROS_PUBLICACION.csv
    y _DIM_CREATIVOS.csv: un array 'conjuntos' de cualquier forma (o vacio) no es error."""
    plan = dict(PLAN_FASE2_COMPLETO, conjuntos=[])
    problemas = gen_plan.validar_plan_fase2o3(plan)
    ok = problemas == []
    print(("  OK     " if ok else "  FALLA  ")
          + "el validador de FASE 2/3 no opina sobre la forma del array 'conjuntos'"
          + ("" if ok else f"\n         problemas={problemas}"))
    return 0 if ok else 1


PLAN_FASE1_BASE = {
    "schema": "plan/1", "producto_key": "X", "fase": 1,
    "oferta": {"oferta_key": "1U"},
    "concepto_control": {"concepto_key": "C2_BENEFICIOS"},
}


def _dim_lanzado(producto):
    """Una fila de _DIM_CONJUNTOS.csv que confirma que `producto` YA lanzo FASE 1 de verdad
    (verificado_en_csv=SI — ver docstring de gen_plan.ya_lanzo_fase1)."""
    return [{"producto_key": producto, "fase": "FASE1", "verificado_en_csv": "SI"}]


def _dim_no_lanzado(producto):
    """Caso real OVULOS_PURITY: la fila EXISTE (FASE 1 la crea como diseño al cerrar) pero
    verificado_en_csv sigue en NO porque todavia no gasto — no cuenta como lanzado."""
    return [{"producto_key": producto, "fase": "FASE1", "verificado_en_csv": "NO"}]


def test_plan_fase1_con_video_falla():
    """Decision del operador 22-sep-2026: FASE 1 corre TODO EN IMAGEN. Un conjunto en VIDEO
    (competidor migrado sin regenerar) tiene que bloquear, no colarse en el paquete."""
    plan = dict(PLAN_FASE1_BASE, conjuntos=[
        {"n": 1, "angulo_key": "A", "nivel_conciencia": "1", "formato": "IMAGEN"},
        {"n": 2, "angulo_key": "B", "nivel_conciencia": "1", "formato": "VIDEO"},
    ])
    problemas = gen_plan.validar_plan_fase1(plan, {}, dim_conjuntos_filas=_dim_lanzado("X"))
    ok = any("formato" in p and "IMAGEN" in p for p in problemas)
    print(("  OK     " if ok else "  FALLA  ")
          + "un plan de FASE 1 con un conjunto en VIDEO falla (F1 es todo IMAGEN)"
          + ("" if ok else f"\n         problemas={problemas}"))
    return 0 if ok else 1


def test_plan_fase1_todo_imagen_no_falla_por_formato():
    plan = dict(PLAN_FASE1_BASE, conjuntos=[
        {"n": i, "angulo_key": "A%d" % i, "nivel_conciencia": "1", "formato": "IMAGEN"}
        for i in range(1, 7)
    ])
    problemas = gen_plan.validar_plan_fase1(plan, {}, dim_conjuntos_filas=_dim_lanzado("X"))
    ok = not any("formato" in p for p in problemas)
    print(("  OK     " if ok else "  FALLA  ")
          + "un plan de FASE 1 con las 6 imagenes no genera error de formato"
          + ("" if ok else f"\n         problemas={problemas}"))
    return 0 if ok else 1


def _conjunto_voz(n, angulo, voz_ids):
    return {"n": n, "angulo_key": angulo, "nivel_conciencia": "1", "formato": "IMAGEN",
            "origen_angulo": "VOZ_CLIENTE", "voz_ids": voz_ids}


def _conjunto_video(n, angulo, fuente):
    return {"n": n, "angulo_key": angulo, "nivel_conciencia": "1", "formato": "IMAGEN",
            "origen_angulo": "VIDEO_COMPETENCIA", "fuente_transcripcion": fuente}


def _voz_fila(producto, voz_id, estado):
    return {"producto_key": producto, "voz_id": voz_id, "estado": estado}


def test_ya_lanzo_fase1_solo_cuenta_verificado_en_csv_si():
    """Caso real OVULOS_PURITY (encontrado al revisar T10): sus 6 conjuntos de FASE 1 ya
    existen en _DIM_CONJUNTOS.csv pero con verificado_en_csv=NO ('SIN PUBLICAR' en las notas
    reales) — eso NO es un lanzamiento, solo diseño. Congela la regla que evita el falso
    positivo de "tiene fila -> ya lanzó"."""
    no_lanzado = gen_plan.ya_lanzo_fase1("OVULOS_PURITY", _dim_no_lanzado("OVULOS_PURITY"))
    lanzado = gen_plan.ya_lanzo_fase1("TINNIDROP", _dim_lanzado("TINNIDROP"))
    ok = no_lanzado is False and lanzado is True
    print(("  OK     " if ok else "  FALLA  ")
          + "verificado_en_csv=NO no cuenta como lanzado; verificado_en_csv=SI si"
          + ("" if ok else f"\n         no_lanzado={no_lanzado} lanzado={lanzado}"))
    return 0 if ok else 1


def test_plan_fase1_producto_lanzado_no_exige_origen_angulo():
    """Un producto que YA lanzó FASE 1 de verdad (data real, no solo un _PLAN.json en disco)
    no se re-castiga retroactivamente: su plan sin origen_angulo/voz_ids no falla por eso."""
    plan = dict(PLAN_FASE1_BASE,
                conjuntos=[{"n": 1, "angulo_key": "A", "nivel_conciencia": "1", "formato": "IMAGEN"}])
    problemas = gen_plan.validar_plan_fase1(plan, {}, [], 3, _dim_lanzado("X"))
    ok = problemas == []
    print(("  OK     " if ok else "  FALLA  ")
          + "un producto que ya lanzó FASE 1 no exige origen_angulo ni voz_ids"
          + ("" if ok else f"\n         problemas={problemas}"))
    return 0 if ok else 1


def test_plan_fase1_producto_no_lanzado_sin_origen_angulo_falla():
    """Caso OVULOS_PURITY: tiene _PLAN.json en disco pero NUNCA lanzó de verdad (sin fila
    verificado_en_csv=SI) — su plan SI debe cumplir la regla de evidencia."""
    plan = dict(PLAN_FASE1_BASE,
                conjuntos=[{"n": 1, "angulo_key": "A", "nivel_conciencia": "1", "formato": "IMAGEN"}])
    problemas = gen_plan.validar_plan_fase1(plan, {}, [], 3, _dim_no_lanzado("X"))
    ok = any("origen_angulo" in p for p in problemas)
    print(("  OK     " if ok else "  FALLA  ")
          + "un producto sin lanzamiento real (aunque tenga _PLAN.json) exige origen_angulo"
          + ("" if ok else f"\n         problemas={problemas}"))
    return 0 if ok else 1


def test_plan_fase1_producto_no_lanzado_sin_registro_en_dim_conjuntos_tambien_falla():
    """Un producto que ni siquiera aparece en _DIM_CONJUNTOS.csv (nunca llegó a ETAPA-GUARDAR-
    PRODUCTO) tampoco escapa la regla — la ausencia total no es evidencia de lanzamiento."""
    plan = dict(PLAN_FASE1_BASE,
                conjuntos=[{"n": 1, "angulo_key": "A", "nivel_conciencia": "1", "formato": "IMAGEN"}])
    problemas = gen_plan.validar_plan_fase1(plan, {}, [], 3, [])
    ok = any("origen_angulo" in p for p in problemas)
    print(("  OK     " if ok else "  FALLA  ")
          + "un producto ausente de _DIM_CONJUNTOS.csv tampoco escapa la regla"
          + ("" if ok else f"\n         problemas={problemas}"))
    return 0 if ok else 1


def test_plan_fase1_no_lanzado_voz_cliente_bajo_el_minimo_falla():
    voz_filas = [_voz_fila("X", "V1", "VERIFICADA"), _voz_fila("X", "V2", "PENDIENTE")]
    plan = dict(PLAN_FASE1_BASE, conjuntos=[_conjunto_voz(1, "A", ["V1", "V2"])])
    problemas = gen_plan.validar_plan_fase1(plan, {}, voz_filas, 3, _dim_no_lanzado("X"))
    ok = any("VOZ_CLIENTE" in p and "1" in p and "3" in p for p in problemas)
    print(("  OK     " if ok else "  FALLA  ")
          + "origen VOZ_CLIENTE con menos voz_id VERIFICADA que el mínimo falla"
          + ("" if ok else f"\n         problemas={problemas}"))
    return 0 if ok else 1


def test_plan_fase1_no_lanzado_voz_cliente_cumple_el_minimo_no_falla():
    voz_filas = [_voz_fila("X", "V%d" % i, "VERIFICADA") for i in range(1, 4)]
    plan = dict(PLAN_FASE1_BASE, conjuntos=[_conjunto_voz(1, "A", ["V1", "V2", "V3"])])
    problemas = gen_plan.validar_plan_fase1(plan, {}, voz_filas, 3, _dim_no_lanzado("X"))
    ok = problemas == []
    print(("  OK     " if ok else "  FALLA  ")
          + "origen VOZ_CLIENTE con exactamente el mínimo de voz_id VERIFICADA no falla"
          + ("" if ok else f"\n         problemas={problemas}"))
    return 0 if ok else 1


def test_plan_fase1_no_lanzado_voz_id_desconocido_falla():
    voz_filas = [_voz_fila("X", "V1", "VERIFICADA")]
    plan = dict(PLAN_FASE1_BASE, conjuntos=[_conjunto_voz(1, "A", ["V1", "V999"])])
    problemas = gen_plan.validar_plan_fase1(plan, {}, voz_filas, 1, _dim_no_lanzado("X"))
    ok = any("V999" in p for p in problemas)
    print(("  OK     " if ok else "  FALLA  ")
          + "citar un voz_id que no existe en _VOZ_CLIENTE.csv para ese producto falla"
          + ("" if ok else f"\n         problemas={problemas}"))
    return 0 if ok else 1


def test_plan_fase1_no_lanzado_video_competencia_sin_fuente_falla():
    plan = dict(PLAN_FASE1_BASE, conjuntos=[_conjunto_video(1, "A", "")])
    problemas = gen_plan.validar_plan_fase1(plan, {}, [], 3, _dim_no_lanzado("X"))
    ok = any("fuente_transcripcion" in p for p in problemas)
    print(("  OK     " if ok else "  FALLA  ")
          + "origen VIDEO_COMPETENCIA sin fuente_transcripcion falla"
          + ("" if ok else f"\n         problemas={problemas}"))
    return 0 if ok else 1


def test_plan_fase1_no_lanzado_video_competencia_con_fuente_no_falla():
    plan = dict(PLAN_FASE1_BASE, conjuntos=[_conjunto_video(1, "A", "NUSAVAB12_2_ARDOR.mp4")])
    problemas = gen_plan.validar_plan_fase1(plan, {}, [], 3, _dim_no_lanzado("X"))
    ok = problemas == []
    print(("  OK     " if ok else "  FALLA  ")
          + "origen VIDEO_COMPETENCIA con fuente_transcripcion no vacía no falla"
          + ("" if ok else f"\n         problemas={problemas}"))
    return 0 if ok else 1


def _plan_exploracion(conjuntos, producto_key="PX"):
    return {"schema": "plan/1", "producto_key": producto_key, "fase": "EXPLORACION",
            "conjuntos": conjuntos}


def _conjunto_exploracion(n, angulo, formato="IMAGEN"):
    return {"n": n, "angulo_key": angulo, "formato": formato}


def test_plan_exploracion_ok_no_falla():
    """F4.exploracion (P12): 3 ángulos nuevos, todos IMAGEN, ninguno ya probado -> sin problemas."""
    plan = _plan_exploracion([_conjunto_exploracion(1, "ANG_UNO"), _conjunto_exploracion(2, "ANG_DOS"),
                               _conjunto_exploracion(3, "ANG_TRES")])
    problemas = gen_plan.validar_plan_exploracion(plan, angulos_probados=["ANG_VIEJO"], n_requerido=3)
    ok = problemas == []
    print(("  OK     " if ok else "  FALLA  ") + "3 ángulos nuevos, todo IMAGEN: el plan de exploración pasa"
          + ("" if ok else f"\n         problemas={problemas}"))
    return 0 if ok else 1


def test_plan_exploracion_menos_angulos_que_los_requeridos_falla():
    plan = _plan_exploracion([_conjunto_exploracion(1, "ANG_UNO"), _conjunto_exploracion(2, "ANG_DOS")])
    problemas = gen_plan.validar_plan_exploracion(plan, angulos_probados=[], n_requerido=3)
    ok = any("3" in p and "2" in p for p in problemas)
    print(("  OK     " if ok else "  FALLA  ")
          + "F4.exploracion pide 3 ángulos (exploracion_n_angulos) y el plan trae 2 -> falla"
          + ("" if ok else f"\n         problemas={problemas}"))
    return 0 if ok else 1


def test_plan_exploracion_angulo_ya_probado_falla():
    """La exclusión de reingreso_f1.angulos_probados() se reusa, no se reinventa: un ángulo que
    el producto ya testeó no puede volver a entrar por F4.exploracion."""
    plan = _plan_exploracion([_conjunto_exploracion(1, "ANG_VIEJO"), _conjunto_exploracion(2, "ANG_DOS"),
                               _conjunto_exploracion(3, "ANG_TRES")])
    problemas = gen_plan.validar_plan_exploracion(plan, angulos_probados=["ANG_VIEJO"], n_requerido=3)
    ok = any("ANG_VIEJO" in p and "ya fue probado" in p for p in problemas)
    print(("  OK     " if ok else "  FALLA  ")
          + "un angulo_key ya probado por el producto es rechazado, no se re-testea a ciegas"
          + ("" if ok else f"\n         problemas={problemas}"))
    return 0 if ok else 1


def test_plan_exploracion_conjunto_video_falla():
    """Misma regla dura que FASE 1: F4.exploracion mide el ángulo, corre TODO EN IMAGEN."""
    plan = _plan_exploracion([_conjunto_exploracion(1, "ANG_UNO"), _conjunto_exploracion(2, "ANG_DOS"),
                               _conjunto_exploracion(3, "ANG_TRES", formato="VIDEO")])
    problemas = gen_plan.validar_plan_exploracion(plan, angulos_probados=[], n_requerido=3)
    ok = any("!= IMAGEN" in p for p in problemas)
    print(("  OK     " if ok else "  FALLA  ")
          + "un conjunto VIDEO en F4.exploracion se rechaza, igual que en FASE 1"
          + ("" if ok else f"\n         problemas={problemas}"))
    return 0 if ok else 1


def test_plan_exploracion_angulo_duplicado_falla():
    plan = _plan_exploracion([_conjunto_exploracion(1, "ANG_UNO"), _conjunto_exploracion(2, "ANG_UNO"),
                               _conjunto_exploracion(3, "ANG_TRES")])
    problemas = gen_plan.validar_plan_exploracion(plan, angulos_probados=[], n_requerido=3)
    ok = any("duplicado" in p for p in problemas)
    print(("  OK     " if ok else "  FALLA  ") + "angulo_key duplicado entre los 3 conjuntos nuevos se rechaza"
          + ("" if ok else f"\n         problemas={problemas}"))
    return 0 if ok else 1


def test_exploracion_n_angulos_requerido_default_y_override():
    previo = gen_plan.PARAMETROS_DECISION
    try:
        gen_plan.PARAMETROS_DECISION = os.path.join(tempfile.mkdtemp(), "no_existe.csv")
        default = gen_plan.exploracion_n_angulos_requerido()
        tmp = tempfile.mkdtemp()
        ruta = os.path.join(tmp, "_PARAMETROS_DECISION.csv")
        with io.open(ruta, "w", encoding="utf-8", newline="") as fh:
            fh.write("parametro,valor,unidad,dueno,por_que\r\nexploracion_n_angulos,5,angulos,test,test\r\n")
        gen_plan.PARAMETROS_DECISION = ruta
        override = gen_plan.exploracion_n_angulos_requerido()
    finally:
        gen_plan.PARAMETROS_DECISION = previo
    ok = default == gen_plan.EXPLORACION_N_ANGULOS == 3 and override == 5
    print(("  OK     " if ok else "  FALLA  ")
          + "exploracion_n_angulos_requerido(): default 3 sin fila, 5 si _PARAMETROS_DECISION.csv la trae"
          + ("" if ok else f"\n         default={default} override={override}"))
    return 0 if ok else 1


def main():
    fallas = 0
    fallas += test_plan_fase1_con_video_falla()
    fallas += test_plan_fase1_todo_imagen_no_falla_por_formato()
    fallas += test_ya_lanzo_fase1_solo_cuenta_verificado_en_csv_si()
    fallas += test_plan_fase1_producto_lanzado_no_exige_origen_angulo()
    fallas += test_plan_fase1_producto_no_lanzado_sin_origen_angulo_falla()
    fallas += test_plan_fase1_producto_no_lanzado_sin_registro_en_dim_conjuntos_tambien_falla()
    fallas += test_plan_fase1_no_lanzado_voz_cliente_bajo_el_minimo_falla()
    fallas += test_plan_fase1_no_lanzado_voz_cliente_cumple_el_minimo_no_falla()
    fallas += test_plan_fase1_no_lanzado_voz_id_desconocido_falla()
    fallas += test_plan_fase1_no_lanzado_video_competencia_sin_fuente_falla()
    fallas += test_plan_fase1_no_lanzado_video_competencia_con_fuente_no_falla()
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
    fallas += test_plan_fase2_lean_falla()
    fallas += test_plan_fase2_no_valida_el_array_conjuntos()
    fallas += test_plan_exploracion_ok_no_falla()
    fallas += test_plan_exploracion_menos_angulos_que_los_requeridos_falla()
    fallas += test_plan_exploracion_angulo_ya_probado_falla()
    fallas += test_plan_exploracion_conjunto_video_falla()
    fallas += test_plan_exploracion_angulo_duplicado_falla()
    fallas += test_exploracion_n_angulos_requerido_default_y_override()
    print(f"\n{'0 fallas' if not fallas else str(fallas) + ' falla(s)'}.")
    return 1 if fallas else 0


if __name__ == "__main__":
    sys.exit(main())
