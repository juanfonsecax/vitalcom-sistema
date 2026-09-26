#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""recopilar_lucidsales.py — corredor DETERMINÍSTICO del fallback manual de LucidSales (T4).

Es el botón "Traer las ventas de LucidSales" de la app (`nodo.ciclo.datos`,
`VISTAS/_MANIFIESTO.json`). Antes ese botón era `ejecutor_tipo: skill` y lanzaba una sesión
de Claude ($5, `presupuesto_usd`) para correr dos comandos deterministas; ahora es
`ejecutor_tipo: script`, igual que `nodo.ciclo.motor` — no hay nada que un modelo tenga que
decidir acá.

PROPÓSITO: fallback manual cuando la corrida de las 5 AM (Task Scheduler, `ciclo_diario.py`)
falló o no corrió — para no esperar hasta la noche siguiente a que LucidSales se pusiera al
día. Corre EXACTAMENTE los mismos pasos de LucidSales que `ciclo_diario.py`, tomados de
`pasos_lucidsales()` (única fuente: nunca se copia la secuencia acá) — bajar + ingerir, y el
control semanal los lunes con `--rol CONTROL`.

QUÉ NO HACE, Y POR QUÉ (a propósito, no un descuido):
  · NO corre el preflight/postcheck de Postgres de `ciclo_diario.py`. `ingerir_lucidsales.py`
    YA verifica el drift contra Postgres antes de escribir una sola fila
    (`db_escribir.verificar_csv_sincronizado`, ver su docstring "P3 T3") y aborta con `SystemExit`
    si el CSV en disco no coincide con lo que la base exportaría. Repetir ese guardia acá no
    agrega seguridad: sería el mismo chequeo dos veces, uno de los cuales sale sobrando.
  · NO escribe fila en `PRODUCTOS/_CORRIDAS_DIARIAS.csv`. Esa fila es el resumen de UNA corrida
    NOCTURNA COMPLETA (T7: VERDE/AMARILLO/ROJO, paridad Postgres↔CSV) — una corrida parcial de
    solo LucidSales no es ese evento, y contarla ahí ensuciaría la racha de 7 días que
    `ciclo_diario.py --racha` mide.
  · NO corre `bajar_meta_insights.py` ni el motor de decisión (`ciclo_hoy.py`): el botón se
    llama "Traer las ventas de LucidSales", no "correr el ciclo nocturno completo". Ese resto
    de la cadena tiene su propio botón (`nodo.ciclo.motor` / `ciclo.bajar_meta`).

Uso:
    python Ads/_TOOLS/recopilar_lucidsales.py             # bajar + ingerir (y control si es lunes)
    python Ads/_TOOLS/recopilar_lucidsales.py --dry-run   # imprime el plan, no corre nada

CÓDIGO DE SALIDA: 0 si todos los pasos salieron en 0 (o en su código de aviso) · 1 si alguno
falló.
"""
from __future__ import annotations

import argparse
import datetime
import os
import subprocess
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except (AttributeError, OSError):
    pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ciclo_diario  # noqa: E402 — única fuente de los pasos: ciclo_diario.pasos_lucidsales()


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Fallback manual de LucidSales (T4): bajar + ingerir, sin el resto del ciclo nocturno.")
    ap.add_argument("--dry-run", action="store_true",
                     help="Imprime el plan de pasos y no corre nada.")
    a = ap.parse_args(argv)

    hoy = datetime.date.today()
    pasos = ciclo_diario.pasos_lucidsales(hoy)

    if a.dry_run:
        print("PLAN recopilar_lucidsales.py para %s (lunes=%s):" %
              (hoy.isoformat(), hoy.weekday() == 0))
        for i, paso in enumerate(pasos, 1):
            print("  %d. %s -> %s" % (i, paso["nombre"], " ".join(paso["argv"])))
        print("[dry-run] no se corrió nada.")
        return 0

    entorno = dict(os.environ, PYTHONIOENCODING="utf-8")
    for paso in pasos:
        print("$ %s" % " ".join(paso["argv"]))
        r = subprocess.run(paso["argv"], cwd=ciclo_diario.BASE, env=entorno)
        if r.returncode != 0 and r.returncode not in paso["codigos_aviso"]:
            print("\n⛔ %s falló (código %s). Revisá el detalle arriba." %
                  (paso["nombre"], r.returncode), file=sys.stderr)
            return 1
    print("\n✅ LucidSales al día.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
