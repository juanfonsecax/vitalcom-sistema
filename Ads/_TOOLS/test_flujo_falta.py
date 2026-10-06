#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_flujo_falta.py — el texto `falta` que lee el operador (FLUJO.json -> flujo.py).

Cada requisito (`requiere`/`produce`) de DOCTRINA/FLUJO.json declara `falta`: una frase corta
en español, con `{n}` opcional (= esperado - observado, solo si ambos son números) y una forma
singular opcional tras `|`. `flujo.py` es el único dueño: lo renderiza junto al texto técnico
(`dato`/`observado`), y la app solo lo muestra.

USO:  python Ads/_TOOLS/test_flujo_falta.py     (exit 0 = pasa, 1 = falla)
"""
import copy
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import flujo  # noqa: E402

fallas = 0


def check(cond, nombre, detalle=""):
    global fallas
    if cond:
        print("  OK     %s" % nombre)
    else:
        fallas += 1
        print("  FALLA  %s%s" % (nombre, ("\n         %r" % (detalle,)) if detalle else ""))


def main():
    t = flujo.texto_falta
    obs = "5 fila(s) · esperado ≥ 10"
    check(t("faltan {n} conceptos|falta 1 concepto", obs) == "faltan 5 conceptos", "{n} = esperado - observado", t("faltan {n} conceptos|falta 1 concepto", obs))
    check(t("faltan {n} conceptos|falta 1 concepto", "9 fila(s) · esperado ≥ 10") == "falta 1 concepto", "n == 1 usa la forma singular")
    check(t("faltan {n} conceptos", "9 fila(s) · esperado ≥ 10") == "faltan 1 conceptos", "sin forma singular se usa la única")
    check(t("faltan {n} conceptos", "sin fechas en _FACT_VENTAS.csv") is None, "con {n} y observado no numérico: sin texto (cae al técnico)")
    check(t("faltan {n} conceptos", "12 fila(s) · esperado ≥ 10") is None, "con {n} y nada que falte: sin texto")
    check(t("falta el diagnóstico del bot (etapa-11)", "0 evento(s)") == "falta el diagnóstico del bot (etapa-11)", "sin {n} va tal cual")
    check(t(None, obs) is None and t("", obs) is None, "sin plantilla: None")

    # _lista expone `falta` al lado del texto técnico, solo si el requisito la declara.
    env = flujo.Entorno()
    ctx = flujo.contexto({"producto_key": "PX"}, env)
    pred = {"tipo": "archivo", "ruta": "no/existe_%s.txt"}
    items = flujo._lista([
        {"dato": "con falta", "predicado": pred, "falta": "falta el archivo", "dueno": "x", "regla": "y"},
        {"dato": "sin falta", "predicado": pred, "dueno": "x", "regla": "y"},
    ], ctx, env)
    check(items[0].get("falta") == "falta el archivo" and items[0]["dato"] == "con falta", "_lista: expone falta y conserva el dato técnico", items[0])
    check("falta" not in items[1], "_lista: sin plantilla no inventa falta", items[1])

    # El grafo real: TODO requisito lo declara y pasa la validación.
    real = flujo.cargar_flujo(env)
    sin = []
    for bloque in real["fases"] + [{"nodos": real["ciclo"]}]:
        for n in bloque["nodos"]:
            for lista in ("requiere", "produce"):
                for r in n.get(lista, []):
                    if not isinstance(r.get("falta"), str) or not r["falta"].strip():
                        sin.append("%s.%s: %s" % (n["id"], lista, r["dato"][:40]))
    check(not sin, "todo requisito de FLUJO.json declara `falta`", sin[:3])
    check(not flujo.validar(real, env), "FLUJO.json con `falta` sigue siendo válido", flujo.validar(real, env)[:2])
    conceptos = next(n for f in real["fases"] for n in f["nodos"] if n["id"] == "F2.conceptos")
    check(t(conceptos["produce"][0]["falta"], obs) == "faltan 5 conceptos", "F2.conceptos: «faltan 5 conceptos»", conceptos["produce"][0].get("falta"))
    e11 = next(n for f in real["fases"] for n in f["nodos"] if n["id"] == "F2.etapa-11")
    check(t(e11["produce"][0]["falta"], "0 evento(s)") == "falta el diagnóstico del bot (etapa-11)", "F2.etapa-11: «falta el diagnóstico del bot (etapa-11)»")

    # La validación rechaza un `falta` mal formado.
    for malo in (7, "faltan {x} cosas", "  "):
        roto = copy.deepcopy(real)
        roto["fases"][1]["nodos"][1]["produce"][0]["falta"] = malo
        check(any("falta" in p for p in flujo.validar(roto, env)), "validar rechaza falta=%r" % (malo,))

    print("\n%d fallas." % fallas)
    return 1 if fallas else 0


if __name__ == "__main__":
    sys.exit(main())
