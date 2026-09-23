#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_decidir.py — GATE DEL MOTOR DE DECISIÓN.

Congela las reglas que se rompieron el 07-sep-2026 al colapsar los tres relojes del
motor en una sola ventana de 3 días. Cada caso es una orden que el sistema TIENE que
saber emitir, y una que NO tiene que emitir nunca.

El caso que da nombre a este archivo: un ángulo con historia de rentabilidad
(TINNIDROP/PERDIDA_AUDITIVA, 38 ventas a CPA Q69.9 bajo BE Q93.4) recibió la orden
APAGAR porque la ventana de 3 días solo veía su peor racha. La orden correcta es
RENOVAR el concepto. Si este archivo pasa, ese error no puede volver.

USO:  python Ads/_TOOLS/test_decidir.py     (exit 0 = pasa, 1 = falla)
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from decidir import evaluar_celda, cargar_parametros  # noqa: E402

BE, OBJ, TASA = 93.41, 30.80, 7.62

# (nombre, kwargs de la celda, estado esperado, por qué importa)
CASOS = [
    ("Quemando sin ventas: el acumulado supera 1x BE",
     dict(ventas=0, mensajes=20, spend_usd=4.0, ventas_3d=0, mensajes_3d=5, spend_3d=1.0,
          ventas_acum=0, mensajes_acum=60, spend_acum_usd=13.0),
     "PAUSAR",
     "La tolerancia se mide sobre el gasto acumulado. Con ventana movil nunca se alcanzaba."),

    ("FASE 1 lento: el acumulado AUN no llega a 1x BE",
     dict(ventas=0, mensajes=8, spend_usd=4.0, ventas_3d=0, mensajes_3d=3, spend_3d=1.0,
          ventas_acum=0, mensajes_acum=8, spend_acum_usd=4.0),
     "SEGUIR_MIDIENDO",
     "Un angulo dentro de su margen de prueba no se apaga antes de tiempo."),

    ("Enlace caido: ni un chat en toda su historia",
     dict(ventas=0, mensajes=0, spend_usd=2.0, ventas_3d=0, mensajes_3d=0, spend_3d=0.5,
          ventas_acum=0, mensajes_acum=0, spend_acum_usd=9.0),
     "PAUSAR",
     "Hook muerto se mide acumulado: si alguna vez trajo un chat, el enlace no esta caido."),

    ("Angulo nuevo con CPA desbordado y SIN historia rentable",
     dict(ventas=3, mensajes=40, spend_usd=60.0, ventas_3d=1, mensajes_3d=10, spend_3d=15.0,
          ventas_acum=3, mensajes_acum=40, spend_acum_usd=60.0),
     "PAUSAR",
     "Sin historia que lo respalde, el CPA desbordado si corta."),

    ("Ganador probado con mala racha: NO se apaga, se renueva",
     dict(ventas=3, mensajes=40, spend_usd=60.0, ventas_3d=1, mensajes_3d=10, spend_3d=15.0,
          ventas_acum=40, mensajes_acum=600, spend_acum_usd=360.0),
     "RENOVAR",
     "EL CASO PERDIDA_AUDITIVA. PAUSAR se evalua antes que FATIGA: sin la guarda de "
     "ganador_historico, un angulo con 40 ventas rentables recibe APAGAR."),

    ("Ganador limpio con IC entero bajo el BE",
     dict(ventas=26, mensajes=190, spend_usd=97.0, ventas_3d=6, mensajes_3d=40, spend_3d=20.0,
          ventas_acum=26, mensajes_acum=190, spend_acum_usd=97.0),
     "ESCALAR",
     "Con evidencia solida la orden de escalar si sale."),

    ("Conversacion floja por clic-ENLACE con 0 ventas: se mata SIN esperar el PD",
     dict(ventas=0, mensajes=10, spend_usd=6.0, ventas_3d=0, mensajes_3d=3, spend_3d=2.0,
          ventas_acum=0, mensajes_acum=10, spend_acum_usd=6.0,
          link_clicks_acum=60, mensajes_enlace_acum=10, dias_activo=2),
     "PAUSAR",
     "17% de conversacion por clic-enlace (<35%) es problema anuncio->bot (Joaquin, clases 7 y 15). "
     "Hasta el 09-sep-2026 esta regla vivia solo en prosa."),

    ("Conversacion floja pero SIN el piso de clics de enlace: no se juzga",
     dict(ventas=0, mensajes=2, spend_usd=2.0, ventas_3d=0, mensajes_3d=1, spend_3d=1.0,
          ventas_acum=0, mensajes_acum=2, spend_acum_usd=2.0,
          link_clicks_acum=8, mensajes_enlace_acum=1, dias_activo=1),
     "SEGUIR_MIDIENDO",
     "Con 8 clics la proporcion es ruido binomial: matar por conversacion seria matar por azar."),

    ("PD agotado sin ventas pero con 1 solo dia con data: esperar la maduracion COD",
     dict(ventas=0, mensajes=20, spend_usd=13.0, ventas_3d=0, mensajes_3d=20, spend_3d=13.0,
          ventas_acum=0, mensajes_acum=20, spend_acum_usd=13.0, dias_activo=1),
     "SEGUIR_MIDIENDO",
     "El 0 ventas de un conjunto de 1 dia no es veredicto (ESCALADO_PLAYBOOK 1.5: ~3 dias COD)."),

    ("PD agotado sin ventas y la maduracion COD cumplida: ahora si se apaga",
     dict(ventas=0, mensajes=20, spend_usd=13.0, ventas_3d=0, mensajes_3d=5, spend_3d=3.0,
          ventas_acum=0, mensajes_acum=40, spend_acum_usd=13.0, dias_activo=4),
     "PAUSAR",
     "Mismo caso, 4 dias con data: el veredicto ya vale."),
]


def test_tope_pausas(params):
    """max_pausas_por_dia: se difieren las pausas que sobran, de menor gasto; el hook muerto nunca."""
    from decidir import aplicar_tope_pausas
    celdas = [
        {"celda": "A", "estado": "PAUSAR", "accion_codigo": "PAUSAR_CPA_DESBORDADO", "spend_q": 300.0, "accion_sugerida": "x"},
        {"celda": "B", "estado": "PAUSAR", "accion_codigo": "PAUSAR_TOLERANCIA_AGOTADA", "spend_q": 200.0, "accion_sugerida": "x"},
        {"celda": "C", "estado": "PAUSAR", "accion_codigo": "PAUSAR_CONVERSACION_FLOJA", "spend_q": 100.0, "accion_sugerida": "x"},
        {"celda": "D", "estado": "PAUSAR", "accion_codigo": "PAUSAR_HOOK_MUERTO", "spend_q": 5.0, "accion_sugerida": "x"},
        {"celda": "E", "estado": "ESCALAR", "accion_codigo": "ESCALAR_SURFING", "spend_q": 50.0, "accion_sugerida": "x"},
    ]
    diferidas = aplicar_tope_pausas(celdas, dict(params, max_pausas_por_dia=2))
    est = {c["celda"]: (c["estado"], c["accion_codigo"]) for c in celdas}
    ok = (diferidas == 1 and est["A"][0] == "PAUSAR" and est["B"][0] == "PAUSAR"
          and est["C"] == ("SEGUIR_MIDIENDO", "PAUSAR_DIFERIDA")
          and est["D"] == ("PAUSAR", "PAUSAR_HOOK_MUERTO") and est["E"][0] == "ESCALAR")
    print(("  OK     " if ok else "  FALLA  ") + "Tope de pausas por dia: 2 de mayor gasto + el hook muerto; la tercera queda diferida")
    return 0 if ok else 1


def test_gate_fase():
    """GATE #2: en fase de testeo un ESCALAR vale como EVIDENCIA pero no es EJECUTABLE.

    TURMERIC, sim del 14-sep-2026: el motor ordenó escalar un conjunto el día 1, en plena
    FASE 1. Ejecutarlo rompe el invariante 6 (mismo presupuesto en todos los conjuntos de la
    etapa): gana el que recibió más plata, no el mejor.

    Lo que este caso congela, y es lo contraintuitivo: el ESTADO NO se degrada a
    SEGUIR_MIDIENDO. flujo.py corona el ángulo ganador por el ESCALAR del motor
    (_ev_angulo_ganador); si el motor se lo callara en F1, el producto no podría salir de F1
    por esa rama y el gate se mordería la cola. Se bloquea la ACCIÓN, no la evidencia."""
    from decidir import aplicar_gate_fase

    def celdas():
        return [{"celda": "A", "estado": "ESCALAR", "accion_sugerida": "ESCALAR (Calet): duplicar campaña"},
                {"celda": "B", "estado": "PAUSAR", "accion_sugerida": "APAGAR: quemó su PD"},
                {"celda": "C", "estado": "SEGUIR_MIDIENDO", "accion_sugerida": "MANTENER"}]

    fallas = 0
    for fase, esperado, nombre in [
        ("F1", False, "en FASE 1 (testeo de ángulos) el ESCALAR no se ejecuta"),
        ("F2", False, "en FASE 2 (testeo de conceptos) tampoco"),
        ("F3", True, "en FASE 3 (escalado) sí se ejecuta: ahí se compra volumen"),
        ("", None, "sin fase derivada: ni bloquea ni aprueba, dice que no pudo evaluarlo"),
    ]:
        cs = celdas()
        aplicar_gate_fase(cs, fase, "TURMERIC")
        a = cs[0]
        ok = (a["ejecutable"] is esperado and a["estado"] == "ESCALAR"
              and (esperado is True or a["bloqueo_fase"])
              and cs[1]["ejecutable"] is True and cs[2]["ejecutable"] is True)
        if esperado is False:
            ok = ok and a["accion_sugerida"].startswith("NO SUBIR PRESUPUESTO")
        print(("  OK     " if ok else "  FALLA  ") + "Gate de fase: " + nombre
              + ("" if ok else "\n         " + str(a)))
        fallas += 0 if ok else 1

    # El estado sobrevive al bloqueo: es lo que flujo.py necesita para coronar el ángulo.
    cs = celdas()
    aplicar_gate_fase(cs, "F1", "TURMERIC")
    ok = cs[0]["estado"] == "ESCALAR" and cs[0]["ejecutable"] is False
    print(("  OK     " if ok else "  FALLA  ")
          + "Gate de fase: el ESCALAR bloqueado SIGUE siendo ESCALAR — flujo.py corona por él"
          + ("" if ok else "\n         " + str(cs[0])))
    return fallas + (0 if ok else 1)


def test_cierre_meta_benchmark():
    """UMBRAL_CIERRE_MINIMO_BOT es BENCHMARK, no gate (GUIA_MADRE_PARAMETRIZADA.md, T3 auditoria
    21-sep-2026): no decide ningun ESTADO, pero el motor lo expone (cierre_meta_min_pct/max_pct)
    para que la app muestre "cierre actual vs meta" sin inventarse el rango. Si este test se
    rompiera porque alguien lo usó para pausar o escalar, ese es el bug: solo prueba que el
    numero SIGUE llegando desde el contrato, nunca que decide algo."""
    import decidir

    # 1) Sin el parametro en el CSV, el motor no se queda sin meta: usa el default de la doctrina.
    previo_path = decidir.PARAMS_PATH
    try:
        decidir.PARAMS_PATH = os.path.join(os.path.dirname(previo_path), "no_existe_este_archivo.csv")
        p_sin_csv = decidir.cargar_parametros()
    finally:
        decidir.PARAMS_PATH = previo_path
    ok_default = (p_sin_csv.get("cierre_meta_min_pct") == 15.0
                  and p_sin_csv.get("cierre_meta_max_pct") == 20.0)

    # 2) El _PARAMETROS_DECISION.csv real del sistema declara el mismo rango (fila agregada en T3):
    # si alguien lo cambia ahí, el motor lo respeta, igual que cualquier otro parametro del CSV.
    p_real = decidir.cargar_parametros()
    ok_csv = (p_real.get("cierre_meta_min_pct") == 15.0
              and p_real.get("cierre_meta_max_pct") == 20.0)

    ok = ok_default and ok_csv
    print(("  OK     " if ok else "  FALLA  ")
          + "Benchmark de cierre: default 15/20 sin CSV, y _PARAMETROS_DECISION.csv los declara "
            "igual (nunca decide un ESTADO, solo se expone en el nivel superior del portafolio)")
    return 0 if ok else 1


def test_progreso_ventas(params):
    """ventas_actual/ventas_necesarias (T7, auditoria 21-sep-2026): el umbral que la app pinta
    como barra de progreso tiene que ser EXACTAMENTE el que decidir.py aplico, nunca uno inventado
    en el frontend. (a) en las dos ramas SEGUIR_MIDIENDO que proyectan ventana (TESTEO_PRIMERA_VENTA,
    MANTENER_Y_MEDIR), ventas_necesarias == ventas_actual + faltan_ventas y siempre > actual: si no
    fuera mayor la barra pintaria progreso al reves. (b) en cualquier otro estado decidido
    (PAUSAR, ESCALAR) ambos campos son None: el motor no proyecto ese umbral ahi y no se inventa."""
    fallas = 0

    # (a) TESTEO_PRIMERA_VENTA: CPA muy por debajo del BE con 1 sola venta, la ventana SI proyecta.
    obtenido = evaluar_celda(
        ventas=1, mensajes=10, spend_usd=2.0, ventas_3d=1, mensajes_3d=10, spend_3d=2.0,
        ventas_acum=1, mensajes_acum=10, spend_acum_usd=2.0,
        be_q=BE, obj_q=OBJ, tasa=TASA, params=params)
    ok_a1 = (obtenido["accion_codigo"] == "TESTEO_PRIMERA_VENTA"
              and obtenido["faltan_ventas"] is not None
              and obtenido["ventas_actual"] == 1
              and obtenido["ventas_necesarias"] == 1 + obtenido["faltan_ventas"]
              and obtenido["ventas_necesarias"] > obtenido["ventas_actual"])
    print(("  OK     " if ok_a1 else "  FALLA  ")
          + "Progreso (TESTEO_PRIMERA_VENTA): ventas_necesarias == ventas_actual + faltan_ventas, y mayor"
          + ("" if ok_a1 else "\n         " + str(obtenido)))
    fallas += 0 if ok_a1 else 1

    # (a) MANTENER_Y_MEDIR: muestra moderada (>1 venta) con IC que aun cruza el BE.
    obtenido2 = evaluar_celda(
        ventas=2, mensajes=30, spend_usd=6.0, ventas_3d=2, mensajes_3d=30, spend_3d=6.0,
        ventas_acum=2, mensajes_acum=30, spend_acum_usd=6.0,
        be_q=BE, obj_q=OBJ, tasa=TASA, params=params)
    ok_a2 = (obtenido2["accion_codigo"] == "MANTENER_Y_MEDIR"
              and obtenido2["faltan_ventas"] is not None
              and obtenido2["ventas_actual"] == 2
              and obtenido2["ventas_necesarias"] == 2 + obtenido2["faltan_ventas"]
              and obtenido2["ventas_necesarias"] > obtenido2["ventas_actual"])
    print(("  OK     " if ok_a2 else "  FALLA  ")
          + "Progreso (MANTENER_Y_MEDIR): ventas_necesarias == ventas_actual + faltan_ventas, y mayor"
          + ("" if ok_a2 else "\n         " + str(obtenido2)))
    fallas += 0 if ok_a2 else 1

    # (b) PAUSAR y ESCALAR: el motor no proyecto ventana ahi, los dos campos salen None.
    pausar = evaluar_celda(
        ventas=3, mensajes=40, spend_usd=60.0, ventas_3d=1, mensajes_3d=10, spend_3d=15.0,
        ventas_acum=3, mensajes_acum=40, spend_acum_usd=60.0,
        be_q=BE, obj_q=OBJ, tasa=TASA, params=params)
    escalar = evaluar_celda(
        ventas=26, mensajes=190, spend_usd=97.0, ventas_3d=6, mensajes_3d=40, spend_3d=20.0,
        ventas_acum=26, mensajes_acum=190, spend_acum_usd=97.0,
        be_q=BE, obj_q=OBJ, tasa=TASA, params=params)
    ok_b = (pausar["estado"] == "PAUSAR" and pausar["ventas_actual"] is None
            and pausar["ventas_necesarias"] is None
            and escalar["estado"] == "ESCALAR" and escalar["ventas_actual"] is None
            and escalar["ventas_necesarias"] is None)
    print(("  OK     " if ok_b else "  FALLA  ")
          + "Progreso (PAUSAR/ESCALAR): ventas_actual y ventas_necesarias en None, el motor no proyecto ahi"
          + ("" if ok_b else "\n         pausar=%s\n         escalar=%s" % (pausar, escalar)))
    fallas += 0 if ok_b else 1

    return fallas


def test_carga_base_y_alias():
    """La carga del motor suma solo BASE y cruza conjunto y banda por nombre canónico."""
    import csv
    import io
    import tempfile
    import decidir

    tmp = tempfile.mkdtemp(prefix="decidir_g0_")
    viejo, nuevo = "PX_ANG-A_R1 +25AÑOS", "PX_ANG-A_R1"

    def escribir(nombre, cols, filas):
        ruta = os.path.join(tmp, nombre)
        with io.open(ruta, "w", encoding="utf-8", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(cols)
            w.writerows(filas)
        return ruta

    rutas = {
        "FACT_VENTAS_PATH": escribir(
            "_FACT_VENTAS.csv",
            ["ventana_fin", "rol_ventana", "producto_key", "conjunto", "ventas", "mensajes", "spend_usd"],
            [["2026-09-01", "BASE", "PX", viejo, "3", "30", "10"],
             ["2026-09-07", "BASE", "PX", nuevo, "2", "20", "8"],
             ["2026-09-07", "CONTROL", "PX", nuevo, "5", "50", "20"]]),
        "DIM_CONJ_PATH": escribir("_DIM_CONJUNTOS.csv", ["producto_key", "conjunto_meta", "angulo_key"],
                                  [["PX", viejo, "ANG_A"]]),
        "DIM_BANDAS_PATH": escribir("_DIM_BANDAS.csv", ["conjunto_meta", "coincide"], [[viejo, "NO"]]),
        "ALIAS_PATH": escribir("_ALIAS_CONJUNTOS.csv", ["nombre_viejo", "nombre_nuevo"], [[viejo, nuevo]]),
        "FACT_ENTREGA_ANUNCIO_PATH": os.path.join(tmp, "no_existe.csv"),
        "FACT_ENTREGA_PATH": os.path.join(tmp, "no_existe2.csv"),
    }
    previo = {k: getattr(decidir, k) for k in rutas}
    try:
        for k, v in rutas.items():
            setattr(decidir, k, v)
        filas = decidir.cargar_datos_duckdb(dias=14, grano="angulo").to_dict("records")
    finally:
        for k, v in previo.items():
            setattr(decidir, k, v)

    ok = (len(filas) == 1 and filas[0]["celda"] == "ANG_A"
          and int(filas[0]["ventas_acum"]) == 5 and not bool(filas[0]["banda_ok"]))
    print(("  OK     " if ok else "  FALLA  ")
          + "Carga: CONTROL no suma y el conjunto renombrado conserva su ángulo y su banda"
          + ("" if ok else "\n         " + str(filas)))
    return 0 if ok else 1


def test_carga_usa_el_gasto_efectivo_de_meta():
    """g07-cimientos T2: el CPA que arma cargar_datos_duckdb() ya NO es el spend_usd de
    LucidSales tal cual -- pasa por gasto.py, que lo reemplaza por el de Meta cuando hay
    cobertura. Sin esto, decidir.py seguiria decidiendo sobre un gasto que puede estar congelado
    a 0.65-0.75x del real (evidencia 06/14/15/16/20-sep-2026)."""
    import csv
    import io
    import tempfile
    import decidir

    tmp = tempfile.mkdtemp(prefix="decidir_g07t2_")

    def escribir(nombre, cols, filas):
        ruta = os.path.join(tmp, nombre)
        with io.open(ruta, "w", encoding="utf-8", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(cols)
            w.writerows(filas)
        return ruta

    # LucidSales dice $10 de gasto; Meta (MetaAPI-directo, mismo conjunto/ventana) dice $50.
    # decidir.py tiene que usar los $50 -- eso es exactamente lo que rompio el CPA de NUSAVA/ARDOR.
    rutas = {
        "FACT_VENTAS_PATH": escribir(
            "_FACT_VENTAS.csv",
            ["ventana_ini", "ventana_fin", "rol_ventana", "producto_key", "cuenta_id",
             "conjunto", "anuncio", "ad_id", "ventas", "mensajes", "spend_usd"],
            [["2026-09-10", "2026-09-10", "BASE", "PY", "CTA1", "PY_ANG-B_R1", "ANU1", "",
              "1", "10", "10.0"]]),
        "DIM_CONJ_PATH": escribir("_DIM_CONJUNTOS.csv", ["producto_key", "conjunto_meta", "angulo_key"],
                                  [["PY", "PY_ANG-B_R1", "ANG_B"]]),
        "DIM_BANDAS_PATH": os.path.join(tmp, "sin_bandas.csv"),
        "ALIAS_PATH": os.path.join(tmp, "sin_alias.csv"),
        "FACT_ENTREGA_ANUNCIO_PATH": os.path.join(tmp, "sin_entrega_anuncio.csv"),
        "FACT_ENTREGA_PATH": escribir(
            "_FACT_ENTREGA.csv",
            ["ventana_ini", "ventana_fin", "producto_key", "cuenta_id", "conjunto", "spend_usd", "fuente"],
            [["2026-09-10", "2026-09-10", "PY", "CTA1", "PY_ANG-B_R1", "50.0", "MetaAPI-directo"]]),
    }
    previo = {k: getattr(decidir, k) for k in rutas}
    try:
        for k, v in rutas.items():
            setattr(decidir, k, v)
        filas = decidir.cargar_datos_duckdb(dias=14, grano="angulo").to_dict("records")
        cobertura = dict(decidir.COBERTURA_GASTO)
    finally:
        for k, v in previo.items():
            setattr(decidir, k, v)

    ok = (len(filas) == 1 and float(filas[0]["spend_usd"]) == 50.0
          and cobertura == {"MetaAPI-conjunto": 1})
    print(("  OK     " if ok else "  FALLA  ")
          + "cargar_datos_duckdb() usa el gasto de Meta ($50), no el de LucidSales ($10)"
          + ("" if ok else "\n         filas=%s cobertura=%s" % (filas, cobertura)))
    return 0 if ok else 1


def test_dia_meta_only_no_corre_la_ventana_de_evaluacion():
    """Regresion de review round 2 (22-sep-2026): gasto.py agrega una celda por Meta aunque
    LucidSales no haya escrito ninguna fila ese dia (full outer join). Si `ult` ("ultimo dia CON
    DATA", que corta la ventana) se calculara sobre ESA celda, un dia donde Meta gasto pero nadie
    vendio corria la ventana un dia y le sumaba su gasto de mas -- eso fue exactamente el CPA mal
    calculado de CLEARSTEM/MEDICOS_FALLARON (Q174.8 en vez de Q116.5) en la ronda anterior de
    review. `ult` tiene que seguir anclado al ultimo dia con una fila REAL de LucidSales, y la
    ventana no debe colar ningun dia posterior a ese."""
    import csv
    import io
    import tempfile
    import decidir

    tmp = tempfile.mkdtemp(prefix="decidir_g07t2_ventana_")

    def escribir(nombre, cols, filas):
        ruta = os.path.join(tmp, nombre)
        with io.open(ruta, "w", encoding="utf-8", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(cols)
            w.writerows(filas)
        return ruta

    # Una sola venta el 09-10 ($10 Meta). Meta TAMBIEN gasto $99 el 09-12 -- DOS dias despues,
    # sin ninguna fila de venta ese dia. Con dias=1, la ventana debe ser SOLO 09-10: el gasto del
    # 09-12 no debe aparecer en spend_usd ni correr "hasta" mas alla de 09-10.
    rutas = {
        "FACT_VENTAS_PATH": escribir(
            "_FACT_VENTAS.csv",
            ["ventana_ini", "ventana_fin", "rol_ventana", "producto_key", "cuenta_id",
             "conjunto", "anuncio", "ad_id", "ventas", "mensajes", "spend_usd"],
            [["2026-09-10", "2026-09-10", "BASE", "PZ", "CTA1", "PZ_ANG-C_R1", "ANU1", "",
              "1", "10", "10.0"]]),
        "DIM_CONJ_PATH": escribir("_DIM_CONJUNTOS.csv", ["producto_key", "conjunto_meta", "angulo_key"],
                                  [["PZ", "PZ_ANG-C_R1", "ANG_C"]]),
        "DIM_BANDAS_PATH": os.path.join(tmp, "sin_bandas.csv"),
        "ALIAS_PATH": os.path.join(tmp, "sin_alias.csv"),
        "FACT_ENTREGA_ANUNCIO_PATH": os.path.join(tmp, "sin_entrega_anuncio.csv"),
        "FACT_ENTREGA_PATH": escribir(
            "_FACT_ENTREGA.csv",
            ["ventana_ini", "ventana_fin", "producto_key", "cuenta_id", "conjunto", "spend_usd", "fuente"],
            [["2026-09-10", "2026-09-10", "PZ", "CTA1", "PZ_ANG-C_R1", "10.0", "MetaAPI-directo"],
             ["2026-09-12", "2026-09-12", "PZ", "CTA1", "PZ_ANG-C_R1", "99.0", "MetaAPI-directo"]]),
    }
    previo = {k: getattr(decidir, k) for k in rutas}
    try:
        for k, v in rutas.items():
            setattr(decidir, k, v)
        filas = decidir.cargar_datos_duckdb(dias=1, grano="angulo").to_dict("records")
    finally:
        for k, v in previo.items():
            setattr(decidir, k, v)

    ok = (len(filas) == 1 and filas[0]["spend_usd"] == 10.0
          and str(filas[0]["hasta"])[:10] == "2026-09-10")
    print(("  OK     " if ok else "  FALLA  ")
          + "un dia Meta-only DESPUES del ultimo dia con venta no corre la ventana ni le suma su "
            "gasto ($99 del 09-12 excluido, spend_usd sigue en $10)"
          + ("" if ok else f"\n         {filas}"))
    return 0 if ok else 1


def main():
    params = cargar_parametros()

    if int(params.get("ventana_fatiga_dias", 3)) >= int(params.get("ventana_dias", 14)):
        print("FALLA  ventana_fatiga_dias debe ser MENOR que ventana_dias: si son iguales "
              "la celda se compara consigo misma y RENOVAR nunca se emite.")
        return 1

    fallas = 0
    for nombre, kw, esperado, porque in CASOS:
        obtenido = evaluar_celda(be_q=BE, obj_q=OBJ, tasa=TASA, params=params, **kw)
        estado = obtenido["estado"]
        if estado == esperado:
            print("  OK     %s" % nombre)
        else:
            fallas += 1
            print("  FALLA  %s\n         esperado=%s  obtenido=%s (%s)\n         %s"
                  % (nombre, esperado, estado, obtenido["accion_codigo"], porque))

    fallas += test_tope_pausas(params)
    fallas += test_gate_fase()          # 5 comprobaciones
    fallas += test_cierre_meta_benchmark()
    fallas += test_progreso_ventas(params)  # 3 comprobaciones
    fallas += test_carga_base_y_alias()
    fallas += test_carga_usa_el_gasto_efectivo_de_meta()
    fallas += test_dia_meta_only_no_corre_la_ventana_de_evaluacion()
    total = len(CASOS) + 13
    print("\n%d de %d casos pasan." % (total - fallas, total))
    return 1 if fallas else 0


if __name__ == "__main__":
    sys.exit(main())
