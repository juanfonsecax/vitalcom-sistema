#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ab_flujo.py — LA ARITMETICA DEL A/B DE FLUJO: cuantos mensajes por brazo y cuanto tarda.

POR QUE EXISTE (16-sep-2026, defecto residual de la simulacion TURMERIC)
-----------------------------------------------------------------------
El PASO 6 de .claude/agents/ETAPA-11.md mandaba al brazo A (paraguas optimizado) el trafico de
TODOS los angulos vivos y al brazo B (flujo dedicado) SOLO el del angulo ganador. Pero el ganador
ya cierra mejor por ser el ganador, asi que el test comparaba ANGULOS, no flujos. Medido con el
mismo Fisher que usa decidir.py (comparar_cierre), 460 mensajes por brazo, cierres de TURMERIC:

    diseno viejo, flujos IDENTICOS (no cambio nada)          -> "el flujo B gana"  70 %
    diseno corregido, flujos IDENTICOS                       -> "el flujo B gana"   1.9 %
    diseno corregido, el flujo B SI mejora (15.3 % -> 22 %)  -> "el flujo B gana"  70 %

El diseno viejo daba LO MISMO si el flujo nuevo mejoraba que si no cambiaba nada.
(1000 tests simulados, semilla 7: los reproduce Ads/_TOOLS/test_ab_flujo.py.)

Y la tabla de tamano de muestra de la doctrina estaba calculada sobre un cierre base FIJO de 9 %.
El n depende del cierre REAL del angulo ganador (TURMERIC/MANOS: 15.3 %): una tabla fija no sirve.
Este script lo calcula con el dato de cada test — aritmetica, no criterio.

USO
    python Ads/_TOOLS/ab_flujo.py --base 0.153 --objetivo 0.25 --msj-dia 19
    python Ads/_TOOLS/ab_flujo.py --base 0.153 --objetivo 0.22 --msj-dia 19 --simular
"""
import argparse
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from decidir import comparar_cierre  # noqa: E402  — el mismo Fisher del motor: una sola estadistica

try:
    from scipy.stats import norm as _norm

    def _z(q):
        return float(_norm.ppf(q))
except ImportError:                     # sin scipy: los dos cuantiles que se usan de verdad
    def _z(q):
        tabla = {0.975: 1.959964, 0.8: 0.841621, 0.9: 1.281552, 0.95: 1.644854}
        return tabla[round(q, 3)]


def n_por_brazo(base, objetivo, alfa=0.05, poder=0.80):
    """Mensajes por brazo para distinguir un cierre `base` de uno `objetivo` (dos colas).

    Formula clasica para dos proporciones. Verificada contra la doctrina: 9 % -> 15 % = 460."""
    if not (0 < base < 1 and 0 < objetivo < 1) or base == objetivo:
        raise ValueError("base y objetivo tienen que ser proporciones distintas entre 0 y 1")
    za, zb = _z(1 - alfa / 2), _z(poder)
    pm = (base + objetivo) / 2
    num = (za * math.sqrt(2 * pm * (1 - pm))
           + zb * math.sqrt(base * (1 - base) + objetivo * (1 - objetivo))) ** 2
    return int(math.ceil(num / (base - objetivo) ** 2))


def tasa_b_gana(cierre_a, cierre_b, n, alfa=0.05, sims=1000, semilla=7):
    """Fraccion de tests simulados que declararian 'el brazo B gana' (Fisher p<alfa y B>A).

    Con cierre_a == cierre_b es la tasa de FALSO ganador del diseno."""
    rnd = random.Random(semilla)
    try:
        import numpy as np
        gen = np.random.default_rng(semilla)
        va_s = gen.binomial(n, cierre_a, sims)
        vb_s = gen.binomial(n, cierre_b, sims)
    except ImportError:
        va_s = [sum(rnd.random() < cierre_a for _ in range(n)) for _ in range(sims)]
        vb_s = [sum(rnd.random() < cierre_b for _ in range(n)) for _ in range(sims)]
    gana = 0
    for va, vb in zip(va_s, vb_s):
        c = comparar_cierre(int(va), n, int(vb), n, alfa)
        if c and c["significativo"] and vb > va:
            gana += 1
    return gana / float(sims)


def main():
    ap = argparse.ArgumentParser(description="Tamano de muestra del A/B de flujo (ETAPA-11 PASO 6)")
    ap.add_argument("--base", type=float, required=True,
                    help="cierre REAL del angulo ganador (ventas/mensajes), p.ej. 0.153")
    ap.add_argument("--objetivo", type=float, required=True, help="cierre que el flujo nuevo deberia lograr")
    ap.add_argument("--msj-dia", type=float, help="mensajes por dia que recibira CADA brazo")
    ap.add_argument("--alfa", type=float, default=0.05)
    ap.add_argument("--poder", type=float, default=0.80)
    ap.add_argument("--simular", action="store_true", help="ademas, simula falso ganador y poder real")
    a = ap.parse_args()

    n = n_por_brazo(a.base, a.objetivo, a.alfa, a.poder)
    print("A/B DE FLUJO · cierre base %.1f %% -> objetivo %.1f %% · alfa %.2f · poder %.0f %%"
          % (a.base * 100, a.objetivo * 100, a.alfa, a.poder * 100))
    print("  n minimo por brazo : %d mensajes" % n)
    if a.msj_dia:
        dias = int(math.ceil(n / a.msj_dia))
        print("  a %.0f msj/dia/brazo: %d dias + la maduracion COD antes de leer" % (a.msj_dia, dias))
    if a.simular:
        print("  falso ganador (flujos identicos) : %.1f %%" % (100 * tasa_b_gana(a.base, a.base, n, a.alfa)))
        print("  poder real con ese n             : %.0f %%" % (100 * tasa_b_gana(a.base, a.objetivo, n, a.alfa)))
    print("  Se lee UNA vez, al llegar al n: mirar antes y decidir en lecturas intermedias infla el falso ganador.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
