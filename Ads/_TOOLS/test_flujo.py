#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_flujo.py — GATE DEL FLUJO DECLARADO.

Congela el caso que le dio origen: la mañana del 08-sep-2026 el sistema tenía cuatro gates
escritos en doctrina y ninguno se disparó. Se publicó FASE 2 con 5 conceptos (R3F-13 pide 10),
en forma de FASE 1 (5 conjuntos × 1 concepto, la doctrina dice 1-1-5 + 1-1-5 + 1-2-5), con un
plan que no cumplía el contrato plan/1, y el CSV decía "cero publicados" mientras Meta llevaba
$23 gastados sirviendo la pieza equivocada. Un modelo leyó la prosa y no lo vio.

Este archivo corre flujo.py sobre ese estado congelado (Ads/_TOOLS/_fixtures/flujo_20260908/)
y exige que los cuatro hallazgos salgan solos. Si pasa, ese día no puede repetirse en silencio.

Además valida que DOCTRINA/FLUJO.json (el grafo real) apunte solo a ejecutores y archivos que
existen, y que el vocabulario de predicados haga lo que dice.

USO:  python Ads/_TOOLS/test_flujo.py     (exit 0 = pasa, 1 = falla)
"""
import csv
import datetime
import io
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from flujo import (Entorno, cargar_flujo, correr, evaluar, situar, validar, BASE_REAL,  # noqa: E402
                   _angulos_acumulados, _ev_angulo_ganador, _ev_concepto_2de2, gate_nodo)

FIXTURE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_fixtures", "flujo_20260908")
HOY = datetime.date(2026, 9, 8)

fallas = 0


def check(cond, nombre, detalle=""):
    global fallas
    if cond:
        print("  OK     %s" % nombre)
    else:
        fallas += 1
        print("  FALLA  %s%s" % (nombre, ("\n         " + detalle) if detalle else ""))


def nodo(r, nid):
    return next((n for n in r["nodos"] if n["id"] == nid), None)


def fixture_renombre_y_control():
    """Un conjunto con dimensión solo en su nombre viejo, ventas bajo los dos nombres y una
    ventana CONTROL que solapa. Lo correcto: 3 + 2 ventas BASE bajo ANG_A; las 5 CONTROL no."""
    tmp = tempfile.mkdtemp(prefix="flujo_g0_")
    prod = os.path.join(tmp, "PRODUCTOS")
    os.makedirs(prod)
    viejo, nuevo = "PX_ANG-A_R1 +25AÑOS", "PX_ANG-A_R1"

    def escribir(nombre, cols, filas):
        with io.open(os.path.join(prod, nombre), "w", encoding="utf-8", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(cols)
            w.writerows(filas)

    escribir("_DIM_CONJUNTOS.csv", ["producto_key", "conjunto_meta", "angulo_key"], [["PX", viejo, "ANG_A"]])
    escribir("_ALIAS_CONJUNTOS.csv", ["nombre_viejo", "nombre_nuevo"], [[viejo, nuevo]])
    escribir("_FACT_VENTAS.csv",
             ["ventana_fin", "rol_ventana", "producto_key", "conjunto", "campana", "anuncio", "ventas", "spend_usd"],
             [["2026-09-01", "BASE", "PX", viejo, "C", "a", "3", "10"],
              ["2026-09-07", "BASE", "PX", nuevo, "C", "a", "2", "8"],
              ["2026-09-07", "CONTROL", "PX", nuevo, "C", "a", "5", "20"]])
    return tmp


def _escribir_csv(prod, nombre, cols, filas):
    with io.open(os.path.join(prod, nombre), "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(cols)
        w.writerows(filas)


def fixture_escalar_flaco(ventas_nuevo=3, con_probado=True):
    """Dos ángulos que el motor manda ESCALAR con el MISMO CPA (Q10.2, IC entero bajo BE Q90),
    y la única diferencia es el VOLUMEN: uno tiene `ventas_nuevo` ventas de un solo día, el otro
    6. Es el caso de TURMERIC: la regla 5 de decidir.py corona desde min_ventas_escalar (2), así
    que un ESCALAR por sí solo no prueba que haya ganador — le falta el piso del ganador (5)."""
    tmp = tempfile.mkdtemp(prefix="flujo_esc_")
    prod = os.path.join(tmp, "PRODUCTOS")
    os.makedirs(prod)
    _escribir_csv(prod, "_DIM_PRODUCTOS.csv",
                  ["producto_key", "nombre_display", "estado", "fase", "cpa_base_q", "cpa_be_q", "tasa"],
                  [["PX", "PX", "VIVO", "F1", "30", "90", "7.62"]])
    _escribir_csv(prod, "_DIM_CONJUNTOS.csv", ["producto_key", "conjunto_meta", "angulo_key"],
                  [["PX", "GTR7_PX_NUEVO_R1", "ANG_NUEVO"], ["PX", "GTR7_PX_PROBADO_R1", "ANG_PROBADO"]])
    _escribir_csv(prod, "_PARAMETROS_DECISION.csv", ["parametro", "valor", "unidad", "dueno", "por_que"],
                  [["min_ventas_ganador", "5", "ventas", "test", "piso del ganador"],
                   ["min_ventas_escalar", "2", "ventas", "test", "piso de la regla 5"]])
    filas = [["2026-09-14", "BASE", "PX", "GTR7_PX_NUEVO_R1", "GTR7_PX_TEST_1", "a",
              str(ventas_nuevo), "20", "%.2f" % (ventas_nuevo * 10.2 / 7.62)]]
    if con_probado:
        filas.append(["2026-09-14", "BASE", "PX", "GTR7_PX_PROBADO_R1", "GTR7_PX_TEST_1", "b", "6", "40", "8.0"])
    _escribir_csv(prod, "_FACT_VENTAS.csv",
                  ["ventana_fin", "rol_ventana", "producto_key", "conjunto", "campana", "anuncio",
                   "ventas", "mensajes", "spend_usd"], filas)
    return tmp


_CAMP_CONCEPTOS_AL_FILO = "GTR7_TURMERIC_F2-CONCEPTOS-%s_20260924"


def _fila_concepto_al_filo(c, cpt, ventas, cpa, fecha_venta="2026-09-27"):
    return [fecha_venta, "BASE", "TURMERIC", "GTR7_TURMERIC_ANG_R1", _CAMP_CONCEPTOS_AL_FILO % c,
            "ad ~ TURMERIC|ANG|%s|NC1|x" % cpt, str(ventas), "40", "%.4f" % (ventas * cpa)]


def fixture_conceptos_al_filo(filas_extra=None):
    """El corte del 27-sep-2026 de la simulación de TURMERIC, con las tres campañas que manda la
    doctrina de FASE 2 (1-1-5 + 1-1-5 + 1-2-5) y los CPA que hicieron oscilar el gate:

        campaña A   nadie llega al piso de 2 ventas
        campaña B   C2.CN06 gana sola             (CPA 2.27)
        campaña C   C3.CN07 2.30 · C2.CN06 2.34   ← Q0.04 de diferencia: 1.7 %
                    C9.CN14 3.50                  ← 52 % peor: no es empate y no debe contar

    Winner-take-all: C corona solo a C3.CN07, nadie llega a 2 campañas y el producto vuelve de
    FASE 3 a FASE 2. Con empate técnico: C2.CN06 replica en B y C, y el gate deja de depender de
    un centavo. C9.CN14 no entra en ninguno de los dos casos.

    `filas_extra` agrega filas de venta adicionales (p.ej. ventas tardías del concepto ganador,
    fechadas después de la confirmación) sin tocar el corte base."""
    tmp = tempfile.mkdtemp(prefix="flujo_cpt_")
    prod = os.path.join(tmp, "PRODUCTOS")
    os.makedirs(prod)
    filas = [_fila_concepto_al_filo("A", "C3.CN07", 1, 2.85),          # bajo el piso: no cuenta
             _fila_concepto_al_filo("B", "C2.CN06", 2, 2.27),
             _fila_concepto_al_filo("C", "C3.CN07", 2, 2.30),
             _fila_concepto_al_filo("C", "C2.CN06", 2, 2.34),
             _fila_concepto_al_filo("C", "C9.CN14", 2, 3.50)]
    if filas_extra:
        filas += filas_extra
    _escribir_csv(prod, "_FACT_VENTAS.csv",
                  ["ventana_fin", "rol_ventana", "producto_key", "conjunto", "campana", "anuncio",
                   "ventas", "mensajes", "spend_usd"], filas)
    return tmp


def main():
    global fallas
    # ── A. el grafo real es válido ─────────────────────────────────────────────
    env_real = Entorno()
    problemas = validar(cargar_flujo(env_real), env_real)
    check(not problemas, "DOCTRINA/FLUJO.json apunta solo a ejecutores y archivos que existen",
          "; ".join(problemas[:3]))

    # Simulación TURMERIC: F1.paquete miraba 5 artefactos y se daba por cumplido sin página, sin
    # piezas en disco ni copy; el bloqueo aparecía recién en F1.publicar, cargando publicar-meta
    # para algo que se arregla en una etapa de fase-1-angulos.
    paquete = next((n for f in cargar_flujo(env_real).get("fases", []) for n in f.get("nodos", [])
                    if n.get("id") == "F1.paquete"), None)
    cmds = [p.get("predicado", {}).get("cmd") or [] for p in (paquete or {}).get("produce", [])]
    check(any("gen_publicacion.py" in " ".join(c) and "--solo-paquete" in c and "--json" not in c
              for c in cmds),
          "F1.paquete exige un paquete LANZABLE (gen_publicacion --solo-paquete), no solo que existan sus archivos",
          str(cmds))

    # ── B. el caso del 08-sep-2026 sale solo ───────────────────────────────────
    if not os.path.isdir(FIXTURE):
        print("  FALLA  no existe el fixture %s" % FIXTURE)
        return 1
    env = Entorno(base=FIXTURE, hoy=HOY, sin_scripts=True)
    _, res = correr(env, ["TINNIDROP"])
    check(len(res) == 1, "el fixture tiene a TINNIDROP")
    r = res[0]

    check(r["fase"] == "F2", "TINNIDROP está en FASE 2 por VENTA (ángulo ganador), no por lo que diga el CSV",
          "fase=%s" % r.get("fase"))
    entrada_f3 = next((e for e in r.get("entradas", []) if e["fase"] == "F3"), None)
    check(entrada_f3 is not None and entrada_f3["ok"] is False,
          "NO está en FASE 3 aunque existan objetos de escalado: sin concepto 2 de 2 no hay gate",
          str(entrada_f3))

    conceptos = nodo(r, "F2.conceptos")
    falta = [x for x in conceptos["produce"] if not x["ok"]] if conceptos else []
    check(bool(falta) and "5 fila" in falta[0]["observado"] and "10" in falta[0]["observado"],
          "HALLAZGO 1 · R3F-13: 5 conceptos GENERADOS de los 10 que pide la doctrina",
          falta[0]["observado"] if falta else "sin faltante")

    plan = nodo(r, "F2.plan")
    check(plan is not None and any("plan/1" in a["dato"] for a in plan["avisos"]),
          "HALLAZGO 3 · el _PLAN_FASE2.json no está en el contrato plan/1 (esquema lean)",
          str([a["dato"] for a in plan["avisos"]]) if plan else "")

    pub = nodo(r, "F2.publicar")
    avisos_pub = [a["dato"] for a in pub["avisos"]] if pub else []
    check(any("YA gastó" in a for a in avisos_pub),
          "HALLAZGO 4 · Meta ya gastó en una campaña de conceptos mientras el CSV decía sin publicar",
          str(avisos_pub))
    check(any("estructura publicada" in a for a in avisos_pub),
          "HALLAZGO 2 · la estructura publicada (5 conjuntos × 1) no es la doctrinal (1-1-5 + 1-1-5 + 1-2-5)",
          str(avisos_pub))
    check(pub is not None and not pub["cumplido"],
          "F2.publicar NO está cumplido: ningún ad_id escrito en _DIM_CREATIVOS.csv")

    check(r["avance"] is not None and r["avance"]["ok"] is False and "2" in r["avance"]["observado"],
          "para pasar a FASE 3 hace falta replicación en 2 campañas, y solo hay 1",
          str(r.get("avance")))
    check(any("F4." in a and "sin haber pasado el gate" in a for a in r["avisos"]),
          "los objetos de FASE 4 (4_PLAN_ESCALADO.txt, LANZAMIENTO de escala) se cantan como fuera de gate — "
          "ex-FASE 3, renombrada por las cuatro fases (28-sep-2026)")

    # ── C. el vocabulario de predicados hace lo que dice ───────────────────────
    ctx = {"pk": "TINNIDROP", "slug": "TINNIDROP", "cuenta": "GTR0"}
    ok, obs = evaluar({"tipo": "csv", "csv": "_DIM_CREATIVOS.csv",
                       "where": {"producto_key": "{pk}", "ad_id": {"no_vacio": True}}, "min": 1}, ctx, env)
    check(ok is False, "csv · where no_vacio: en el fixture ningún creativo tiene ad_id", obs)
    ok, obs = evaluar({"tipo": "csv", "csv": "_FACT_VENTAS.csv",
                       "where": {"producto_key": "{pk}", "campana": {"contiene": "conceptos"}},
                       "sum": "spend_usd", "sum_min": 20}, ctx, env)
    check(ok is True, "csv · contiene (sin distinguir mayúsculas) + sum_min", obs)
    ok, obs = evaluar({"tipo": "json", "ruta": "PRODUCTOS/{slug}/_PLAN.json", "campo": "conjuntos", "min_len": 6}, ctx, env)
    check(ok is True, "json · min_len sobre el plan de FASE 1", obs)
    ok, obs = evaluar({"tipo": "no", "de": {"tipo": "archivo", "ruta": "PRODUCTOS/{slug}/no_existe.txt"}}, ctx, env)
    check(ok is True, "no · niega un archivo ausente", obs)
    ok, obs = evaluar({"tipo": "archivo", "ruta": "PRODUCTOS/{slug}/4_PLAN_ESCALADO.txt",
                       "contiene": "FIXTURE"}, ctx, env)
    check(ok is True, "archivo · contiene (T8-4): encuentra un texto que si esta en el archivo", obs)
    ok, obs = evaluar({"tipo": "archivo", "ruta": "PRODUCTOS/{slug}/4_PLAN_ESCALADO.txt",
                       "contiene": "MICROANGULO"}, ctx, env)
    check(ok is False, "archivo · contiene (T8-4): NO encuentra un texto ausente, no aprueba a ciegas", obs)
    ok, obs = evaluar({"tipo": "script", "cmd": ["python", "x.py"]}, ctx, env)
    check(ok is None, "script · con --sin-scripts devuelve None (no evaluado), nunca un ✓ falso", obs)
    ok, obs = evaluar({"tipo": "csv_campo", "csv": "_DIM_CUENTAS.csv",
                       "where": {"cuenta_alias": {"norm": "{cuenta}"}}, "campo": "mcp_habilitado", "eq": "SI"}, ctx, env)
    check(ok is True, "csv_campo · norm: «GTR 0» del CSV empareja con «GTR0» del contexto", obs)
    ok, obs = evaluar({"tipo": "csv", "csv": "_DIM_PRODUCTOS.csv", "where": {"producto_key": "{pk}"},
                       "min": "@param:no_existe"}, ctx, env)
    check(ok is None, "@param inexistente: el predicado dice que no pudo evaluar, no inventa un límite", obs)

    # ── D. el acumulado que decide las fases suma solo BASE y cruza por nombre canónico ──
    acc = _angulos_acumulados(Entorno(base=fixture_renombre_y_control(), hoy=HOY, sin_scripts=True), "PX")
    check(acc == {"ANG_A": [5.0, 18.0]},
          "acumulado por ángulo: CONTROL no suma y el conjunto renombrado cae en su ángulo, no en uno fantasma",
          str(acc))

    # ── E. el ESCALAR del motor no corona un ángulo sin el piso de ventas del ganador ──
    # TURMERIC, sim del 14-sep-2026: 3 ventas de UN SOLO DÍA con CPA bajo dieron ESCALAR
    # (regla 5, que corona desde min_ventas_escalar = 2) y el producto saltó de fase esa misma
    # noche. min_ventas_ganador (5) lo pedía solo la rama histórica: un reglamento partido.
    HOY_E = datetime.date(2026, 9, 14)
    env_e = Entorno(base=fixture_escalar_flaco(ventas_nuevo=3, con_probado=False), hoy=HOY_E, sin_scripts=True)
    celdas_e, _p = env_e.celdas("PX")
    check([c["estado"] for c in celdas_e] == ["ESCALAR"],
          "el motor SÍ manda ESCALAR con 3 ventas (la regla 5 corona desde min_ventas_escalar)",
          str([(c["celda"], c["estado"], c["ventas"]) for c in celdas_e]))
    # the reentry gate in FLUJO.json declares "estado" as a LIST under the singular key
    pred_reingreso = {"tipo": "decision", "estado": ["ESCALAR", "SEGUIR_MIDIENDO", "RENOVAR"], "max": 0}
    ok_ri, obs_ri = evaluar(pred_reingreso, {"pk": "PX"}, env_e)
    check(ok_ri is False and "error" not in obs_ri and "ESCALAR" in obs_ri,
          "gate de reingreso: 'estado' como lista se evalúa (no revienta) y ve la celda viva",
          obs_ri)
    ok_e, obs_e = _ev_angulo_ganador({}, {"pk": "PX"}, env_e)
    check(ok_e is False and "descartado por volumen" in obs_e,
          "un ESCALAR con 3 ventas NO es ángulo ganador: falta el piso de 5 y el gate lo dice",
          obs_e)

    env_e2 = Entorno(base=fixture_escalar_flaco(ventas_nuevo=3, con_probado=True), hoy=HOY_E, sin_scripts=True)
    ok_e2, obs_e2 = _ev_angulo_ganador({}, {"pk": "PX"}, env_e2)
    check(ok_e2 is True and "ANG_PROBADO" in obs_e2 and "ANG_NUEVO" not in obs_e2,
          "con el mismo CPA, corona el de 6 ventas y no el de 3: el piso filtra por VOLUMEN, no por CPA",
          obs_e2)

    # ── F. el gate de FASE 3 no oscila por un centavo de CPA ──────────────────
    # TURMERIC, sim: 25-sep ✗ · 26-sep ✓ · 27-sep ✗ · 28-sep ✓. El 26 dos conceptos empataban
    # EXACTO (1.75 = 1.75) y desempataba el orden alfabético; el 27 se dieron vuelta por Q0.04.
    env_c = Entorno(base=fixture_conceptos_al_filo(), hoy=datetime.date(2026, 9, 27), sin_scripts=True)
    ok_c0, obs_c0 = _ev_concepto_2de2({"margen_empate_pct": 0}, {"pk": "TURMERIC"}, env_c)
    check(ok_c0 is False,
          "winner-take-all: con Q0.04 de diferencia nadie replica y el producto vuelve de F3 a F2",
          obs_c0)
    ok_c, obs_c = _ev_concepto_2de2({}, {"pk": "TURMERIC"}, env_c)
    check(ok_c is True and obs_c.startswith("C2.CN06") and "empate técnico" in obs_c,
          "empate técnico: los dos conceptos a 1.7% cuentan, C2.CN06 replica en 2 y el gate se sostiene",
          obs_c)
    check("C9.CN14" not in obs_c,
          "el margen no vuelve trivial el gate: el concepto 52% peor no empata con nadie",
          obs_c)
    check("hacen falta 2" in obs_c and "de las 3 campañas" in obs_c,
          "el rótulo dice el umbral (2) aparte del denominador (3 campañas): «2 de 3» no es otra regla",
          obs_c)

    # ── G. la transición de fatiga reingresa el producto a FASE 1 ──────────────
    # Si un producto en F2 se fatiga y el operador dispara REINGRESO_F1, el flujo
    # debe situarlo en F1 reportando los ángulos excluidos para no repetirlos.
    flujo_base = cargar_flujo(Entorno(base=FIXTURE, hoy=HOY, sin_scripts=True))
    f2_def = next((f for f in flujo_base["fases"] if f["id"] == "F2"), {})
    check(f2_def.get("reingreso") is not None and f2_def["reingreso"].get("a") == "F1",
          "DOCTRINA/FLUJO.json declara la transición de fatiga (reingreso a F1) en FASE 2")

    # Simulamos fixture con producto en F2 que recibe REINGRESO_F1
    tmp_fatiga = fixture_escalar_flaco(ventas_nuevo=3, con_probado=True)
    _escribir_csv(os.path.join(tmp_fatiga, "PRODUCTOS"), "_EVENTOS.csv",
                  ["fecha", "producto_key", "cuenta_alias", "campana_clave", "conjunto_meta", "evento",
                   "valor_antes", "valor_despues", "motivo", "fuente_decision"],
                  [["2026-09-14", "PX", "GTR7", "*", "*", "REINGRESO_F1", "F2", "F1",
                    "Fatiga de ángulo. Excluidos: ANG_NUEVO, ANG_PROBADO", "operador (app)"]])

    env_fatiga = Entorno(base=tmp_fatiga, hoy=datetime.date(2026, 9, 15), sin_scripts=True)
    prod_fatiga = next(p for p in env_fatiga.csv("_DIM_PRODUCTOS.csv") if p.get("producto_key") == "PX")
    sit = situar(prod_fatiga, flujo_base, env_fatiga)
    check(sit["fase"] == "F1",
          "producto con ganador histórico pero REINGRESO_F1 activo es situado en FASE 1",
          str(sit.get("fase")))
    check(sit.get("reingreso_activo") is not None and "ANG_PROBADO" in sit["reingreso_activo"].get("angulos_excluidos", []),
          "reingreso_activo reporta los ángulos excluidos para que etapa-2 no los repita",
          str(sit.get("reingreso_activo")))

    # ── H. Cuatro fases (28-sep-2026): F3.entrada ya NO exige CAMBIO_BOT (solo concepto 2/2 —
    # ver test_gate_entrada.py::test_f3_concepto_2de2_basta_sin_cambio_bot); el gate que exige un
    # CAMBIO_BOT POSTERIOR al concepto ganador —y que un relanzamiento viejo (variable de
    # confusión) no lo satisface— se movió a F4.entrada. El F2.etapa-11 real de DOCTRINA/FLUJO.json
    # se leyó para confirmar que quedó como DIAGNÓSTICO, no como reescritura.
    f3_def = next((f for f in flujo_base["fases"] if f["id"] == "F3"), {})
    f4_def = next((f for f in flujo_base["fases"] if f["id"] == "F4"), {})
    gate_f4 = f4_def.get("entrada", {}).get("gate", {})
    eventos_cols = ["fecha", "producto_key", "cuenta_alias", "campana_clave", "conjunto_meta",
                     "evento", "valor_antes", "valor_despues", "motivo", "fuente_decision"]

    def _fila_evento(fecha, evento, motivo="test"):
        return [fecha, "TURMERIC", "GTR7", "*", "*", evento, "", "", motivo, "test"]

    tmp_sin_bot = fixture_conceptos_al_filo()
    env_sin_bot = Entorno(base=tmp_sin_bot, hoy=datetime.date(2026, 9, 28), sin_scripts=True)
    ok_sb, obs_sb = evaluar(gate_f4, {"pk": "TURMERIC"}, env_sin_bot)
    check(ok_sb is False,
          "F4.entrada (doctrina real): concepto 2/2 sin NINGÚN CAMBIO_BOT no basta para entrar a F4",
          obs_sb)

    tmp_bot_viejo = fixture_conceptos_al_filo()
    _escribir_csv(os.path.join(tmp_bot_viejo, "PRODUCTOS"), "_EVENTOS.csv", eventos_cols,
                  [_fila_evento("2026-09-20", "CAMBIO_BOT", "relanzamiento anterior, no relacionado")])
    env_bot_viejo = Entorno(base=tmp_bot_viejo, hoy=datetime.date(2026, 9, 28), sin_scripts=True)
    ok_bv, obs_bv = evaluar(gate_f4, {"pk": "TURMERIC"}, env_bot_viejo)
    check(ok_bv is False,
          "F4.entrada (doctrina real): un CAMBIO_BOT de ANTES del ganador (2026-09-20 < 2026-09-27, "
          "variable de confusión) NO satisface el gate",
          obs_bv)

    tmp_bot_nuevo = fixture_conceptos_al_filo()
    _escribir_csv(os.path.join(tmp_bot_nuevo, "PRODUCTOS"), "_EVENTOS.csv", eventos_cols,
                  [_fila_evento("2026-09-20", "CAMBIO_BOT", "relanzamiento anterior, no relacionado"),
                   _fila_evento("2026-09-28", "CAMBIO_BOT", "reescritura hacia C2.CN06 tras 2 de 2")])
    env_bot_nuevo = Entorno(base=tmp_bot_nuevo, hoy=datetime.date(2026, 9, 29), sin_scripts=True)
    ok_bn, obs_bn = evaluar(gate_f4, {"pk": "TURMERIC"}, env_bot_nuevo)
    check(ok_bn is False and "mensaje" in obs_bn,
          "F4.entrada (doctrina real): un CAMBIO_BOT fechado DESPUÉS del ganador (2026-09-28 > "
          "2026-09-27) satisface (a) pero SIN mensajes/cierre posteriores el gate sigue sin cumplirse",
          obs_bn)

    # ── H2. Regresión: la fecha de confirmación del concepto ganador es ESTABLE (primer cruce
    # del piso de replicación), no "el último día con venta". Con el CAMBIO_BOT del caso anterior
    # (2026-09-28, posterior a la confirmación real del 2026-09-27) ya fijado, sumar ventas
    # TARDÍAS del concepto ganador (C2.CN06), fechadas incluso DESPUÉS del propio CAMBIO_BOT, no
    # debe correr la fecha de confirmación hacia adelante: si la fecha fuera "el último día con
    # venta", esta venta nueva la movería a 2026-09-30 y el CAMBIO_BOT del 2026-09-28 dejaría de
    # ser "posterior". Se comprueba sobre `_fecha_cambio_bot` (la misma fecha que usa
    # cierre_post_cambio_bot), no sobre el gate F4 completo — ese ya quedó cubierto en H.
    from flujo import _fecha_cambio_bot  # noqa: E402 (import local, evita ciclo con el tope del módulo)
    tmp_venta_tardia = fixture_conceptos_al_filo(
        filas_extra=[_fila_concepto_al_filo("B", "C2.CN06", 3, 2.27, fecha_venta="2026-09-30")])
    _escribir_csv(os.path.join(tmp_venta_tardia, "PRODUCTOS"), "_EVENTOS.csv", eventos_cols,
                  [_fila_evento("2026-09-28", "CAMBIO_BOT", "reescritura hacia C2.CN06 tras 2 de 2")])
    env_venta_tardia = Entorno(base=tmp_venta_tardia, hoy=datetime.date(2026, 10, 1), sin_scripts=True)
    fecha_cb_vt = _fecha_cambio_bot({"pk": "TURMERIC"}, env_venta_tardia)
    check(fecha_cb_vt == datetime.date(2026, 9, 28),
          "F4.entrada (regresión fecha estable): ventas tardías del concepto ganador "
          "(2026-09-30, posteriores incluso al propio CAMBIO_BOT) no mueven la fecha de "
          "confirmación hacia adelante — el CAMBIO_BOT del 28 sigue viéndose como posterior",
          str(fecha_cb_vt))

    tmp_excepcion = fixture_conceptos_al_filo()
    _escribir_csv(os.path.join(tmp_excepcion, "PRODUCTOS"), "_EVENTOS.csv", eventos_cols,
                  [_fila_evento("2026-09-28", "EXCEPCION_CAMBIO_BOT",
                                "operador decide saltarse la reescritura, escala igual")])
    env_excepcion = Entorno(base=tmp_excepcion, hoy=datetime.date(2026, 9, 29), sin_scripts=True)
    ok_ex, obs_ex = evaluar(gate_f4, {"pk": "TURMERIC"}, env_excepcion)
    check(ok_ex is False and "mensaje" in obs_ex,
          "F4.entrada (doctrina real): un EXCEPCION_CAMBIO_BOT posterior al ganador (waiver del "
          "operador) satisface (a) sin exigir la reescritura, pero (b)/(c) — mensajes y cierre — "
          "siguen pendientes",
          obs_ex)

    # ── I. F2.etapa-11 (doctrina real): diagnóstico de congruencia POSTERIOR al ángulo ganador,
    # no una reescritura — usa el mismo fixture de la sección E (ANG_PROBADO gana el 2026-09-14).
    diag_f2 = nodo({"nodos": [n for f in flujo_base["fases"] if f["id"] == "F2" for n in f["nodos"]]},
                    "F2.etapa-11")
    pred_diag = diag_f2["produce"][0]["predicado"] if diag_f2 else {}

    tmp_diag_antes = fixture_escalar_flaco(ventas_nuevo=3, con_probado=True)
    _escribir_csv(os.path.join(tmp_diag_antes, "PRODUCTOS"), "_EVENTOS.csv",
                  ["fecha", "producto_key", "cuenta_alias", "campana_clave", "conjunto_meta", "evento",
                   "valor_antes", "valor_despues", "motivo", "fuente_decision"],
                  [["2026-09-10", "PX", "GTR7", "*", "*", "DIAGNOSTICO_CONGRUENCIA", "", "",
                    "diagnóstico corrido ANTES de que el ángulo ganara (2026-09-14)", "etapa-11"]])
    env_diag_antes = Entorno(base=tmp_diag_antes, hoy=datetime.date(2026, 9, 16), sin_scripts=True)
    ok_da, obs_da = evaluar(pred_diag, {"pk": "PX"}, env_diag_antes)
    check(ok_da is False,
          "F2.etapa-11 (doctrina real): un DIAGNOSTICO_CONGRUENCIA de ANTES del ángulo ganador "
          "(2026-09-10 < 2026-09-14) no cumple el nodo — el diagnóstico tiene que probar que se "
          "midió el cierre CON el ganador ya confirmado",
          obs_da)

    tmp_diag_despues = fixture_escalar_flaco(ventas_nuevo=3, con_probado=True)
    _escribir_csv(os.path.join(tmp_diag_despues, "PRODUCTOS"), "_EVENTOS.csv",
                  ["fecha", "producto_key", "cuenta_alias", "campana_clave", "conjunto_meta", "evento",
                   "valor_antes", "valor_despues", "motivo", "fuente_decision"],
                  [["2026-09-15", "PX", "GTR7", "*", "*", "DIAGNOSTICO_CONGRUENCIA", "", "",
                    "diagnóstico corrido DESPUÉS de que el ángulo ganara (2026-09-14)", "etapa-11"]])
    env_diag_despues = Entorno(base=tmp_diag_despues, hoy=datetime.date(2026, 9, 16), sin_scripts=True)
    ok_dd, obs_dd = evaluar(pred_diag, {"pk": "PX"}, env_diag_despues)
    check(ok_dd is True,
          "F2.etapa-11 (doctrina real): un DIAGNOSTICO_CONGRUENCIA de DESPUÉS del ángulo ganador "
          "(2026-09-15 > 2026-09-14) SÍ cumple el nodo — sin exigir ninguna reescritura de flujo",
          obs_dd)

    # ── J. F4.exploracion (P12, T12; ex-F3.exploracion): gate propio (F4 rentable) via
    # flujo.gate_nodo, distinto del gate de ENTRADA a F4 y sin bloquear F4.plan/F4.publicar
    # (paralelo, como F2.etapa-11). Reusa fixture_escalar_flaco: con con_probado=True,
    # ANG_PROBADO llega a ESCALAR con 6 ventas (>= min_ventas_escalar=2 de ese mismo fixture) —
    # "F4 rentable". Sin ese ángulo (con_probado=False, 1 sola venta) ninguna celda llega al
    # piso: "F4 no rentable".
    env_expl_cerrado = Entorno(base=fixture_escalar_flaco(ventas_nuevo=1, con_probado=False),
                                hoy=HOY_E, sin_scripts=True)
    ok_expl_c, obs_expl_c = gate_nodo("PX", "F4.exploracion", env_expl_cerrado)
    check(ok_expl_c is False,
          "F4.exploracion (gate cerrado): sin ninguna celda ESCALAR con el piso de volumen, "
          "el escalado no es rentable todavía", obs_expl_c)

    env_expl_abierto = Entorno(base=fixture_escalar_flaco(ventas_nuevo=3, con_probado=True),
                                hoy=HOY_E, sin_scripts=True)
    ok_expl_a, obs_expl_a = gate_nodo("PX", "F4.exploracion", env_expl_abierto)
    check(ok_expl_a is True and "ANG_PROBADO" in obs_expl_a,
          "F4.exploracion (gate abierto): ANG_PROBADO en ESCALAR con 6 ventas (>= piso) — "
          "el escalado SÍ es rentable, la exploración puede arrancar", obs_expl_a)

    ok_nodo_desconocido, obs_nodo_desconocido = gate_nodo("PX", "F9.no_existe", env_expl_abierto)
    check(ok_nodo_desconocido is False,
          "gate_nodo de un id que no existe en FLUJO.json refusa, no inventa un cumplido",
          obs_nodo_desconocido)

    ok_sin_requiere, obs_sin_requiere = gate_nodo("PX", "F4.plan", env_expl_abierto)
    check(ok_sin_requiere is True and "no declara" in obs_sin_requiere,
          "un nodo sin `requiere` (F4.plan no declara uno) está siempre cumplido para gate_nodo",
          obs_sin_requiere)

    # gate_nodo es SOLO LECTURA, igual que gate_entrada.
    ruta_estado_j = os.path.join(env_expl_abierto.base, "PRODUCTOS", "_ESTADO_FLUJO.csv")
    ruta_eventos_j = os.path.join(env_expl_abierto.base, "PRODUCTOS", "_EVENTOS.csv")
    check(not os.path.exists(ruta_estado_j) and not os.path.exists(ruta_eventos_j),
          "gate_nodo no escribe _ESTADO_FLUJO.csv ni _EVENTOS.csv")

    # F4.exploracion no aparece en ningún predicado de F4.plan/F4.publicar: es paralela, nunca
    # una precondición de los nodos que SÍ miden el escalado (regresión estructural, doctrina real).
    f4_plan_real = next((n for n in f4_def.get("nodos", []) if n["id"] == "F4.plan"), {})
    f4_pub_real = next((n for n in f4_def.get("nodos", []) if n["id"] == "F4.publicar"), {})
    texto_otros_nodos = json.dumps([f4_plan_real, f4_pub_real], ensure_ascii=False)
    check("exploracion" not in texto_otros_nodos.lower(),
          "F4.exploracion (doctrina real): no bloquea F4.plan ni F4.publicar — ninguno de los "
          "dos la cita en su `requiere`/`produce`")

    # ── K. F3 (optimización del flujo del bot): concepto 2/2 basta para entrar, y F3.reescribir/
    # F3.medir_cierre son los nodos que producen lo que antes exigía F3.entrada.
    check(f3_def.get("titulo", "").startswith("FASE 3"),
          "DOCTRINA/FLUJO.json: F3 (ex-escalado) pasa a ser la fase de optimización del flujo",
          f3_def.get("titulo"))
    nodos_f3 = {n["id"] for n in f3_def.get("nodos", [])}
    check(nodos_f3 == {"F3.reescribir", "F3.medir_cierre"},
          "F3 declara exactamente F3.reescribir y F3.medir_cierre", str(nodos_f3))
    check(f3_def.get("salida", {}).get("a") == "F4",
          "F3 sale hacia F4 (no un F3 duplicado)", str(f3_def.get("salida")))

    total = 44
    print("\n%d de %d comprobaciones pasan." % (total - fallas, total))
    return 1 if fallas else 0


if __name__ == "__main__":
    sys.exit(main())

