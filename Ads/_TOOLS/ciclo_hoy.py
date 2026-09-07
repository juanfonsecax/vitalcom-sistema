#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ciclo_hoy.py — COMANDO ÚNICO DE AUDITORÍA Y OPERACIÓN DIARIA.

El operador ejecuta SOLO este comando cada mañana:
    python Ads/_TOOLS/ciclo_hoy.py

Hace todo en 3 segundos:
  1. Corre el motor de decisiones operativo (reglas deterministas de bankroll).
  2. Reconstruye las vistas y la consola de lanzamiento (VISTAS/APP.html).
  3. Muestra en pantalla el plan de acción resumido del día: qué apagar, qué escalar y qué vigilar.
"""

import os
import sys
import io
import subprocess

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except (AttributeError, OSError):
    pass

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(BASE)


def correr(cmd):
    e = dict(os.environ, PYTHONIOENCODING="utf-8")
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding="utf-8", errors="replace", env=e)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def main():
    print("=" * 80)
    print(" 🚀 VITALCOM GUATEMALA — CICLO OPERATIVO MATUTINO")
    print("=" * 80)

    print("\n[1/3] Evaluando métricas y ejecutando motor de decisiones...")
    rc, out = correr("python Ads/_TOOLS/decidir.py")
    if rc != 0:
        print("  Error al ejecutar decidir.py:\n", out)
        return 1
    print(out)

    print("\n[2/3] Sincronizando consola de lanzamiento y planes...")
    rc, out = correr("python Ads/_TOOLS/gen_lanzador.py")
    if rc != 0:
        print("  Aviso en gen_lanzador:\n", out)

    print("\n[3/3] Actualizando aplicación completa (VISTAS/APP.html)...")
    rc, out = correr("python Ads/_TOOLS/gen_app.py")
    if rc != 0:
        print("  Aviso en gen_app:\n", out)
    else:
        print("  ✅ Aplicación VISTAS/APP.html actualizada al 100%.")

    print("\n" + "=" * 80)
    print(" AUDITORÍA COMPLETADA. Abrí VISTAS/APP.html en tu navegador para ver la interfaz.")
    print("=" * 80)
    return 0


if __name__ == "__main__":
    sys.exit(main())
