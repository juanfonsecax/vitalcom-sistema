#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_gen_lanzador.py — GATE DEL PRESUPUESTO POR FASE EN gen_lanzador.py (G0.5 punto 4.4,
15-sep-2026).

Antes de este arreglo, derivar() llamaba presupuesto_conjunto(usd_conv) — la formula
autoajustable de FASE 1 (7 x costo/conversacion, piso $2.99, techo $3.95) — para LAS TRES
FASES por igual. CALENDARIO_ESCALADO.md 1.5 dice explicitamente que esa seccion completa
"gobierna la FASE 1 · ANGULOS" y que "la FASE 2 (conceptos) tiene su propio presupuesto".
El dato real de FASE 2 es $6.00/conjunto (_PARAMETROS_PUBLICACION.csv) — la formula de
FASE 1, alimentada con el usd_por_conversacion tipico del portafolio (~$0.4-0.6), producia
$3.00-$3.95: **la mitad o menos** de lo que la doctrina manda para lanzar conceptos.

USO:  python Ads/_TOOLS/test_gen_lanzador.py     (exit 0 = pasa, 1 = falla)
"""
import csv
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_lanzador as gl  # noqa: E402


def _parametros_publicacion(tmp):
    ruta = os.path.join(tmp, "_PARAMETROS_PUBLICACION.csv")
    filas = [
        {"fase": "1", "brazo": "UNICO", "daily_budget_usd": "2.99", "estado": "VIGENTE",
         "fuente_doctrina": "CALENDARIO_ESCALADO.md 1.5"},
        {"fase": "2", "brazo": "A", "daily_budget_usd": "6.00", "estado": "VIGENTE",
         "fuente_doctrina": "CALENDARIO_ESCALADO.md 1.7.2"},
        {"fase": "2", "brazo": "B", "daily_budget_usd": "6.00", "estado": "VIGENTE",
         "fuente_doctrina": "CALENDARIO_ESCALADO.md 1.7.2"},
        {"fase": "2", "brazo": "C", "daily_budget_usd": "6.00", "estado": "VIGENTE",
         "fuente_doctrina": "CALENDARIO_ESCALADO.md 1.7.2"},
        {"fase": "3", "brazo": "UNICO", "daily_budget_usd": "15.00", "estado": "VIGENTE",
         "fuente_doctrina": "ESCALADO_PLAYBOOK.md"},
    ]
    cols = ["fase", "brazo", "daily_budget_usd", "estado", "fuente_doctrina"]
    with open(ruta, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(filas)
    return ruta


def test_fase2_ya_no_dicta_la_mitad():
    with tempfile.TemporaryDirectory() as tmp:
        ruta = _parametros_publicacion(tmp)
        viejo = gl.PARAMETROS_PUBLICACION
        gl.PARAMETROS_PUBLICACION = ruta
        try:
            presup_formula_fase1, _ = gl.presupuesto_conjunto(0.478)   # lo que el bug usaba
            presup_fase2, por_que = gl.presupuesto_por_fase(2, 0.478)
        finally:
            gl.PARAMETROS_PUBLICACION = viejo
    ok = presup_fase2 == 6.0 and presup_fase2 > presup_formula_fase1 * 1.5
    print(("  OK     " if ok else "  FALLA  ")
          + "FASE 2 dicta $6.00/conjunto (fijo, _PARAMETROS_PUBLICACION.csv), no la formula "
            "de FASE 1 ($%.2f, la mitad o menos)" % presup_formula_fase1
          + ("" if ok else f"\n         fase2={presup_fase2!r} por_que={por_que!r}"))
    return 0 if ok else 1


def test_fase3_lee_el_valor_fijo_de_escalado():
    with tempfile.TemporaryDirectory() as tmp:
        ruta = _parametros_publicacion(tmp)
        viejo = gl.PARAMETROS_PUBLICACION
        gl.PARAMETROS_PUBLICACION = ruta
        try:
            presup, por_que = gl.presupuesto_por_fase(3, 0.478)
        finally:
            gl.PARAMETROS_PUBLICACION = viejo
    ok = presup == 15.0
    print(("  OK     " if ok else "  FALLA  ")
          + "FASE 3 dicta $15.00 (CBO, ESCALADO_PLAYBOOK.md), no la formula autoajustable de FASE 1"
          + ("" if ok else f"\n         obtenido={presup!r} por_que={por_que!r}"))
    return 0 if ok else 1


def test_fase1_sigue_usando_la_formula_autoajustable():
    """FASE 1 NO cambia: sigue siendo la unica fase donde CALENDARIO_ESCALADO.md 1.5
    aplica (formula 7x, piso/techo)."""
    with tempfile.TemporaryDirectory() as tmp:
        ruta = _parametros_publicacion(tmp)
        viejo = gl.PARAMETROS_PUBLICACION
        gl.PARAMETROS_PUBLICACION = ruta
        try:
            directo = gl.presupuesto_conjunto(0.541)
            via_dispatcher = gl.presupuesto_por_fase(1, 0.541)
        finally:
            gl.PARAMETROS_PUBLICACION = viejo
    ok = directo == via_dispatcher
    print(("  OK     " if ok else "  FALLA  ")
          + "FASE 1 sigue derivando del usd_por_conversacion observado, no de un valor fijo"
          + ("" if ok else f"\n         directo={directo!r} dispatcher={via_dispatcher!r}"))
    return 0 if ok else 1


def test_fase_sin_fila_vigente_no_inventa():
    with tempfile.TemporaryDirectory() as tmp:
        ruta = os.path.join(tmp, "_PARAMETROS_PUBLICACION.csv")
        with open(ruta, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=["fase", "brazo", "daily_budget_usd", "estado", "fuente_doctrina"])
            w.writeheader()
        viejo = gl.PARAMETROS_PUBLICACION
        gl.PARAMETROS_PUBLICACION = ruta
        try:
            presup, por_que = gl.presupuesto_por_fase(2, 0.478)
        finally:
            gl.PARAMETROS_PUBLICACION = viejo
    ok = presup is None and "sin fila VIGENTE" in (por_que or "")
    print(("  OK     " if ok else "  FALLA  ")
          + "sin fila VIGENTE para la fase, no inventa un numero: devuelve None con el motivo"
          + ("" if ok else f"\n         presup={presup!r} por_que={por_que!r}"))
    return 0 if ok else 1


def main():
    fallas = 0
    fallas += test_fase2_ya_no_dicta_la_mitad()
    fallas += test_fase3_lee_el_valor_fijo_de_escalado()
    fallas += test_fase1_sigue_usando_la_formula_autoajustable()
    fallas += test_fase_sin_fila_vigente_no_inventa()
    print(f"\n{'0 fallas' if not fallas else str(fallas) + ' falla(s)'}.")
    return 1 if fallas else 0


if __name__ == "__main__":
    sys.exit(main())
