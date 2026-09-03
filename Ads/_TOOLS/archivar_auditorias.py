#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""archivar_auditorias.py — retencion de informes fechados, ejecutable.

Por que existe
--------------
El invariante 8 de CLAUDE.md manda todo informe fechado a PRODUCTOS/_AUDITORIAS/,
y la regla de retencion dice: los ultimos 30 dias sueltos, lo anterior colapsado
a subcarpeta mensual, nunca borrado. Esa regla estaba en prosa y jamas se
ejecuto: al 2026-09-02 habia 45 informes sueltos, 14 de julio y 27 de agosto,
sin una sola subcarpeta.

Nada se borra. Los archivos se MUEVEN a su subcarpeta AAAA-MM.

Uso
---
    python Ads/_TOOLS/archivar_auditorias.py            # aplica
    python Ads/_TOOLS/archivar_auditorias.py --dry-run  # solo dice que haria
    python Ads/_TOOLS/archivar_auditorias.py --dias 60  # otra ventana

Corre como hook de SessionStart, asi que es silencioso cuando no hay nada que
mover: no tiene sentido saludar con un informe vacio en cada sesion.
"""

import argparse
import datetime as dt
import os
import re
import shutil
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, OSError):
    pass

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
AUD = os.path.join(BASE, "PRODUCTOS", "_AUDITORIAS")

# Las fechas en los nombres vienen en dos formas: 20260821 y 2026-08-21.
RE_FECHA = re.compile(r"(20\d{2})-?(\d{2})-?(\d{2})")


def fecha_de(nombre):
    m = RE_FECHA.search(nombre)
    if not m:
        return None
    try:
        return dt.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError:
        return None


def main():
    ap = argparse.ArgumentParser(description="Colapsa informes viejos a subcarpeta mensual")
    ap.add_argument("--dias", type=int, default=30, help="ventana suelta (default 30)")
    ap.add_argument("--dry-run", action="store_true", help="no mueve nada")
    args = ap.parse_args()

    if not os.path.isdir(AUD):
        return 0

    corte = dt.date.today() - dt.timedelta(days=args.dias)
    movidos, sin_fecha = [], []

    for nombre in sorted(os.listdir(AUD)):
        ruta = os.path.join(AUD, nombre)
        if not os.path.isfile(ruta):
            continue
        f = fecha_de(nombre)
        if f is None:
            sin_fecha.append(nombre)
            continue
        if f >= corte:
            continue
        destino_dir = os.path.join(AUD, "%04d-%02d" % (f.year, f.month))
        destino = os.path.join(destino_dir, nombre)
        if os.path.exists(destino):
            continue                       # ya archivado: no se toca
        if args.dry_run:
            movidos.append((nombre, "%04d-%02d/" % (f.year, f.month)))
            continue
        os.makedirs(destino_dir, exist_ok=True)
        shutil.move(ruta, destino)
        movidos.append((nombre, "%04d-%02d/" % (f.year, f.month)))

    if movidos:
        verbo = "se moverian" if args.dry_run else "movidos"
        print("retencion de _AUDITORIAS: %d informes %s (mas de %d dias)"
              % (len(movidos), verbo, args.dias))
        porcarpeta = {}
        for _, sub in movidos:
            porcarpeta[sub] = porcarpeta.get(sub, 0) + 1
        for sub in sorted(porcarpeta):
            print("  %s  %d archivos" % (sub, porcarpeta[sub]))
        print("  nada se borro: los archivos siguen consultables en su subcarpeta.")
    if sin_fecha and args.dry_run:
        print("sin fecha en el nombre (se quedan sueltos): %s" % ", ".join(sin_fecha))
    return 0


if __name__ == "__main__":
    sys.exit(main())
