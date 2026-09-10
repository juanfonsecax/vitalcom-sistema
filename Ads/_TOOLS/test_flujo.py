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
import datetime
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from flujo import Entorno, cargar_flujo, correr, evaluar, validar, BASE_REAL  # noqa: E402

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


def main():
    global fallas
    # ── A. el grafo real es válido ─────────────────────────────────────────────
    env_real = Entorno()
    problemas = validar(cargar_flujo(env_real), env_real)
    check(not problemas, "DOCTRINA/FLUJO.json apunta solo a ejecutores y archivos que existen",
          "; ".join(problemas[:3]))

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

    total = 17
    print("\n%d de %d comprobaciones pasan." % (total - fallas, total))
    return 1 if fallas else 0


if __name__ == "__main__":
    sys.exit(main())
