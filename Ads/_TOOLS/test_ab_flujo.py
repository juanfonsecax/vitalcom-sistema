#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_ab_flujo.py — GATE DEL A/B DE FLUJO (defecto residual de la simulacion TURMERIC, 16-sep-2026).

El PASO 6 de .claude/agents/ETAPA-11.md mandaba al brazo A el trafico de TODOS los angulos vivos y
al brazo B SOLO el del ganador. El ganador ya cierra mejor por ser el ganador: el test comparaba
angulos, no flujos. Con flujos IDENTICOS declaraba "el flujo B gana" el 70 % de las veces — LO MISMO
que cuando el flujo B de verdad mejora (70 %). No media nada.

Congela tres cosas:
  1. la aritmetica del n (ab_flujo.n_por_brazo) contra los seis numeros que ya estaban en juego;
  2. el porque: el diseno viejo inventa ganadores y el de gemelos no, sin perder poder;
  3. que la doctrina (ETAPA-11 y ETAPA-5) no vuelva al reparto por angulos.

USO:  python Ads/_TOOLS/test_ab_flujo.py     (exit 0 = pasa, 1 = falla)
"""
import io
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import ab_flujo as ab  # noqa: E402

BASE = os.path.dirname(os.path.dirname(AQUI))
CIERRE_GANADOR, CIERRE_RESTO, N = 0.153, 0.097, 460      # simulacion TURMERIC


def check(ok, nombre, detalle=""):
    print(("  OK     " if ok else "  FALLA  ") + nombre + ("" if ok else "\n         " + detalle))
    return 0 if ok else 1


def test_n_por_brazo_reproduce_los_numeros_conocidos():
    """Los tres de la tabla vieja de ETAPA-11 (base 9 %) y los tres de la simulacion (base 15.3 %)."""
    casos = [((0.09, 0.15), 460), ((0.09, 0.13), 960), ((0.09, 0.12), 1638),
             ((0.153, 0.25), 268), ((0.153, 0.22), 530), ((0.153, 0.20), 1032)]
    malos = [(b, o, esp, ab.n_por_brazo(b, o)) for (b, o), esp in casos if ab.n_por_brazo(b, o) != esp]
    return check(not malos, "n por brazo: reproduce los 6 numeros conocidos (460/960/1638 · 268/530/1032)",
                 "distintos: %s" % malos)


def test_el_n_depende_del_cierre_base():
    """La tabla vieja asumia 9 % para todos. El mismo salto de +6 puntos pide otro n con otra base."""
    a, b = ab.n_por_brazo(0.09, 0.15), ab.n_por_brazo(0.153, 0.213)
    return check(a != b, "el mismo +6 puntos pide distinto n con base 9 %% (%d) que con 15.3 %% (%d): tabla fija no sirve" % (a, b))


def test_diseno_viejo_inventa_ganadores():
    tasa = ab.tasa_b_gana(CIERRE_RESTO, CIERRE_GANADOR, N)      # flujos IDENTICOS: solo cambia el angulo
    return check(tasa >= 0.55, "diseno viejo (A = otros angulos, B = ganador) con flujos IDENTICOS: 'B gana' %.0f %%" % (100 * tasa),
                 "se esperaba >= 55 %% (medido 70 %%)")


def test_gemelos_no_inventan_ganadores():
    tasa = ab.tasa_b_gana(CIERRE_GANADOR, CIERRE_GANADOR, N)
    return check(tasa <= 0.05, "gemelos del ganador con flujos IDENTICOS: 'B gana' %.1f %% (bajo alfa)" % (100 * tasa),
                 "se esperaba <= 5 %% (medido 1.9 %%)")


def test_gemelos_conservan_el_poder():
    tasa = ab.tasa_b_gana(CIERRE_GANADOR, 0.22, N)
    return check(tasa >= 0.55, "gemelos del ganador con un flujo B que SI mejora (15.3 -> 22 %%): lo detecta %.0f %%" % (100 * tasa),
                 "se esperaba >= 55 %% (medido 70 %%)")


def _leer(rel):
    with io.open(os.path.join(BASE, rel), encoding="utf-8") as fh:
        return fh.read()


def test_doctrina_etapa11_usa_gemelos():
    t = _leer(".claude/agents/ETAPA-11.md")
    ini = t.find("### PASO 6")
    paso6 = t[ini:t.find("### PASO 7", ini)]
    faltan = [x for x in ("GEMELOS", "ab_flujo.py", "_TESTEOS.csv", "test_id") if x not in paso6]
    viejo = "Sigue recibiendo el tráfico de todos los ángulos vivos" in paso6
    return check(ini >= 0 and not faltan and not viejo,
                 "ETAPA-11 PASO 6: brazos gemelos del ganador, n por ab_flujo.py, declarado en _TESTEOS.csv",
                 "faltan %s · diseno viejo presente=%s" % (faltan, viejo))


def test_doctrina_etapa5_no_rutea_todo_el_ganador_a_b():
    t = _leer(".claude/agents/ETAPA-5.md")
    viejo = "al que se rutea por Post ID el tráfico del ángulo\r\n  ganador" in t or \
            "al que se rutea por Post ID el tráfico del ángulo\n  ganador" in t
    return check(not viejo and "gemelo" in t,
                 "ETAPA-5: el brazo B recibe el trafico de SU gemelo, no todo el del angulo ganador",
                 "la frase vieja sigue en ETAPA-5.md")


def main():
    fallas = 0
    fallas += test_n_por_brazo_reproduce_los_numeros_conocidos()
    fallas += test_el_n_depende_del_cierre_base()
    fallas += test_diseno_viejo_inventa_ganadores()
    fallas += test_gemelos_no_inventan_ganadores()
    fallas += test_gemelos_conservan_el_poder()
    fallas += test_doctrina_etapa11_usa_gemelos()
    fallas += test_doctrina_etapa5_no_rutea_todo_el_ganador_a_b()
    print("\n%s." % ("0 fallas" if not fallas else "%d falla(s)" % fallas))
    return 1 if fallas else 0


if __name__ == "__main__":
    sys.exit(main())
