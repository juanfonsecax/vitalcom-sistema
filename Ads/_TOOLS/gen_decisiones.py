#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen_decisiones.py — reconstruye el warehouse y corre el motor de decision.

Es el camino COMPLETO por el que una orden de pausar, escalar o renovar llega al operador:
primero refresca la capa analitica (dbt build sobre los CSV), y recien despues corre
Ads/_TOOLS/decidir.py, que escribe PRODUCTOS/_DECISIONES.json. La aplicacion
(VISTAS/APP.html) dibuja ese JSON de forma nativa.

POR QUE EXISTE, si decidir.py ya corre solo:
    decidir.py lee el warehouse. Si nadie lo reconstruye, el motor decide sobre una capa
    analitica vieja mientras la app muestra una fecha fresca. Este archivo es el unico
    lugar donde `dbt build` se invoca, asi que el manifiesto lo declara como el generador
    de la vista `decisiones` — no a decidir.py pelado.

NO DIBUJA HTML. Hasta el 07-sep-2026 tambien renderizaba VISTAS/DECISIONES.html, una
segunda superficie para los mismos datos que quedo a la deriva: seguia pintando el estado
INDECIDIBLE_ESTRUCTURAL que el motor unificado ya no emite, no conocia RENOVAR, y crasheaba
con KeyError('por_que') contra el contrato actual del motor. Nadie lo noto porque solo se
invocaba como fallback. La vista retirada vive en _ARCHIVO/. Un dato, un dueno: las
decisiones se ven en la app.

USO:
    python Ads/_TOOLS/gen_decisiones.py           # warehouse + motor
    python Ads/_TOOLS/gen_decisiones.py --sin-dbt # solo el motor
"""
import os
import sys
import subprocess

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, OSError):
    pass

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WH = os.path.join(BASE, "warehouse")
JSON = os.path.join(BASE, "PRODUCTOS", "_DECISIONES.json")


def correr(cmd, cwd, env=None):
    e = dict(os.environ, PYTHONIOENCODING="utf-8", **(env or {}))
    r = subprocess.run(cmd, cwd=cwd, env=e, shell=True,
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def main():
    if "--sin-dbt" not in sys.argv:
        if os.path.isdir(WH):
            rc, log = correr("python -m dbt.cli.main build --no-use-colors", WH,
                             {"DBT_PROFILES_DIR": "."})
            if rc == 0:
                linea = next((l for l in log.splitlines() if "PASS=" in l), "(sin resumen)")
                print("  dbt build ->", linea.strip()[-70:])
            else:
                # No es fatal: decidir.py cae a los CSV directos. Pero se dice, no se esconde.
                print("  ! aviso: dbt no corrio o fallo. El motor leera los CSV directamente "
                      "y la capa analitica queda VIEJA hasta que se arregle.")
        else:
            print("  ! aviso: no existe warehouse/, se omite dbt build")

    rc, log = correr("python Ads/_TOOLS/decidir.py", BASE)
    if rc != 0:
        print(log[-1500:])
        return 1
    print(log.rstrip())
    print("  escrito PRODUCTOS/_DECISIONES.json  ->  lo dibuja VISTAS/APP.html")
    return 0


if __name__ == "__main__":
    sys.exit(main())
