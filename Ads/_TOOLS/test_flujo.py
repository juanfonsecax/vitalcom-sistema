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
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from flujo import (Entorno, cargar_flujo, correr, evaluar, situar, validar, BASE_REAL,  # noqa: E402
                   _angulos_acumulados, _ev_angulo_ganador, _ev_concepto_2de2)

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


def fixture_conceptos_al_filo():
    """El corte del 27-sep-2026 de la simulación de TURMERIC, con las tres campañas que manda la
    doctrina de FASE 2 (1-1-5 + 1-1-5 + 1-2-5) y los CPA que hicieron oscilar el gate:

        campaña A   nadie llega al piso de 2 ventas
        campaña B   C2.CN06 gana sola             (CPA 2.27)
        campaña C   C3.CN07 2.30 · C2.CN06 2.34   ← Q0.04 de diferencia: 1.7 %
                    C9.CN14 3.50                  ← 52 % peor: no es empate y no debe contar

    Winner-take-all: C corona solo a C3.CN07, nadie llega a 2 campañas y el producto vuelve de
    FASE 3 a FASE 2. Con empate técnico: C2.CN06 replica en B y C, y el gate deja de depender de
    un centavo. C9.CN14 no entra en ninguno de los dos casos."""
    tmp = tempfile.mkdtemp(prefix="flujo_cpt_")
    prod = os.path.join(tmp, "PRODUCTOS")
    os.makedirs(prod)
    camp = "GTR7_TURMERIC_F2-CONCEPTOS-%s_20260924"

    def fila(c, cpt, ventas, cpa):
        return ["2026-09-27", "BASE", "TURMERIC", "GTR7_TURMERIC_ANG_R1", camp % c,
                "ad ~ TURMERIC|ANG|%s|NC1|x" % cpt, str(ventas), "40", "%.4f" % (ventas * cpa)]

    _escribir_csv(prod, "_FACT_VENTAS.csv",
                  ["ventana_fin", "rol_ventana", "producto_key", "conjunto", "campana", "anuncio",
                   "ventas", "mensajes", "spend_usd"],
                  [fila("A", "C3.CN07", 1, 2.85),          # bajo el piso: no cuenta
                   fila("B", "C2.CN06", 2, 2.27),
                   fila("C", "C3.CN07", 2, 2.30),
                   fila("C", "C2.CN06", 2, 2.34),
                   fila("C", "C9.CN14", 2, 3.50)])
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
    check(any("F3." in a and "sin haber pasado el gate" in a for a in r["avisos"]),
          "los objetos de FASE 3 (4_PLAN_ESCALADO.txt, LANZAMIENTO de escala) se cantan como fuera de gate")

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

    total = 29
    print("\n%d de %d comprobaciones pasan." % (total - fallas, total))
    return 1 if fallas else 0


if __name__ == "__main__":
    sys.exit(main())

