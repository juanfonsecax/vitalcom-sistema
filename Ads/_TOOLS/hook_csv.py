#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""hook_csv.py — PostToolUse: valida el CSV escrito y regenera el dashboard.

Por que existe
--------------
Dos reglas del sistema eran consejos en prosa que dependian de que el modelo se
acordara en el momento justo:

  · Invariante 11: los CSV se editan con un escritor CSV real. El bug de NUSAVA
    (31-jul) dejo una fila con 20 campos en vez de 17 y la nota truncada. Nadie
    lo vio hasta que el dashboard mostro cifras raras.
  · Regla del ciclo diario: despues de anexar a un CSV se regenera el dashboard.
    Si no, el operador lee data vieja creyendo que es de hoy.

Un hook las vuelve deterministas: ocurren siempre, sin depender de la memoria.

Contrato
--------
Lee el JSON de PostToolUse por stdin. Si el archivo tocado es un CSV de
PRODUCTOS/, cuenta las columnas de cada fila contra el encabezado. Si alguna no
cuadra, sale con codigo 2 y el mensaje llega a Claude para que lo corrija. Si
cuadra, regenera el dashboard (774 ms medidos) y sale 0.

PRINCIPIO: un hook que falla nunca debe bloquear el trabajo. Cualquier error
inesperado del propio hook sale 0 en silencio.
"""

import csv
import io
import json
import os
import subprocess
import sys

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROD = os.path.join(BASE, "PRODUCTOS")
DASHBOARD = os.path.join(BASE, "Ads", "_TOOLS", "gen_dashboard.py")

# El dashboard solo se regenera si cambio uno de los CSV que lo alimentan.
# Tocar _DIM_COSTEO.csv no mueve el dashboard de ventas, pero es barato incluirlo.
PREFIJOS_QUE_ALIMENTAN_DASHBOARD = ("_FACT_", "_DIM_", "_EVENTOS", "_TASA_",
                                    "_PARAMETROS_", "_APRENDIZAJES", "_TESTEOS")


def validar(ruta):
    """Devuelve None si el CSV esta bien formado, o el mensaje de error."""
    try:
        with io.open(ruta, encoding="utf-8", errors="replace", newline="") as fh:
            filas = list(csv.reader(fh))
    except OSError as e:
        return None                      # no se puede leer: no es asunto del hook
    filas = [f for f in filas if f]
    if len(filas) < 2:
        return None
    n = len(filas[0])
    malas = [(i + 1, len(f)) for i, f in enumerate(filas) if len(f) != n]
    if not malas:
        return None
    det = ", ".join("linea %d tiene %d" % (ln, c) for ln, c in malas[:8])
    if len(malas) > 8:
        det += " (y %d mas)" % (len(malas) - 8)
    return ("CSV MALFORMADO: %s\n"
            "El encabezado declara %d columnas pero %s.\n"
            "Causa habitual: un campo de texto libre con comas escrito sin comillas dobles.\n"
            "Reescribi el archivo con csv.DictWriter (invariante 11 de CLAUDE.md), "
            "nunca a mano." % (os.path.basename(ruta), n, det))


def main():
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0

    ruta = ((payload.get("tool_input") or {}).get("file_path") or "").strip()
    if not ruta or not ruta.lower().endswith(".csv"):
        return 0

    ruta_abs = os.path.abspath(ruta)
    if os.path.dirname(ruta_abs) != os.path.abspath(PROD):
        return 0                         # solo la capa de data de PRODUCTOS/
    if not os.path.exists(ruta_abs):
        return 0

    error = validar(ruta_abs)
    if error:
        sys.stderr.write(error + "\n")
        return 2                         # bloquea y el mensaje llega a Claude

    nombre = os.path.basename(ruta_abs)
    if not nombre.startswith(PREFIJOS_QUE_ALIMENTAN_DASHBOARD):
        return 0
    if not os.path.exists(DASHBOARD):
        return 0
    try:
        r = subprocess.run([sys.executable, DASHBOARD], cwd=BASE,
                           capture_output=True, timeout=120)
        if r.returncode == 0:
            print("hook: %s validado, dashboard regenerado." % nombre)
        else:
            # No se bloquea: el CSV quedo bien, solo el render fallo.
            cola = (r.stderr or b"").decode("utf-8", "replace").strip().splitlines()
            print("hook: %s validado, pero gen_dashboard.py fallo (exit %d). %s"
                  % (nombre, r.returncode, cola[-1] if cola else ""))
    except (subprocess.TimeoutExpired, OSError) as e:
        print("hook: %s validado; no se pudo regenerar el dashboard (%s)." % (nombre, e))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)                      # un hook roto no frena el trabajo
