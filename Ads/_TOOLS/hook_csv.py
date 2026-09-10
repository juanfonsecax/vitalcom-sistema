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
cuadra, regenera el dashboard y la app unificada (VISTAS/APP.html) y sale 0.

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
APP = os.path.join(BASE, "Ads", "_TOOLS", "gen_app.py")
FLUJO = os.path.join(BASE, "Ads", "_TOOLS", "flujo.py")

# gen_app.py refresca PRODUCTOS/_LANZADOR.json y reescribe VISTAS/APP.html y
# VISTAS/LANZADOR.html de una sola pasada, asi que el hook llama a uno solo.
# Antes llamaba a gen_lanzador.py directo y la app unificada quedaba atras.

# El dashboard solo se regenera si cambio uno de los CSV que lo alimentan.
# Tocar _DIM_COSTEO.csv no mueve el dashboard de ventas, pero es barato incluirlo.
PREFIJOS_QUE_ALIMENTAN_DASHBOARD = ("_FACT_", "_DIM_", "_EVENTOS", "_TASA_",
                                    "_PARAMETROS_", "_APRENDIZAJES", "_TESTEOS")


def finales_de_linea(ruta):
    """CRLF y LF sueltos en el mismo archivo -> el CSV deja de ser legible por motores estrictos.

    Python lo tolera, y por eso vivio meses sin que nadie lo viera. DuckDB ni siquiera puede
    inferir el dialecto y falla el build entero. Aparecio el 06-sep-2026 en _FACT_ENTREGA.csv
    (405 lineas CRLF + 233 LF), producto de mezclar escrituras con y sin newline="" en open().
    La convencion de la casa es CRLF, que es lo que emite csv.writer en Windows.
    """
    try:
        b = io.open(ruta, "rb").read()
    except OSError:
        return None
    crlf = b.count(b"\r\n")
    lf = b.count(b"\n") - crlf
    if crlf and lf:
        return ("FINALES DE LINEA MEZCLADOS: %s\n"
                "%d lineas terminan en CRLF y %d en LF suelto. Un CSV asi lo lee Python pero lo "
                "rechaza cualquier motor estricto.\n"
                "Causa: escribir el archivo sin newline=\"\" en open(). Reescribilo con "
                "csv.DictWriter y newline=\"\" (invariante 11 de CLAUDE.md)."
                % (os.path.basename(ruta), crlf, lf))
    return None


def validar(ruta):
    """Devuelve None si el CSV esta bien formado, o el mensaje de error."""
    malos_finales = finales_de_linea(ruta)
    if malos_finales:
        return malos_finales
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


ESTADO = os.path.join(BASE, "PRODUCTOS", ".hook_csv_mtimes.json")


def barrido():
    """Valida los CSV de PRODUCTOS/ que cambiaron desde la ultima pasada.

    Cierra el hueco del modo por-archivo: ese solo ve escrituras hechas con Write
    o Edit, y varios scripts del sistema escriben CSV por su cuenta —
    ingerir_lucidsales.py toca _FACT_VENTAS.csv, que es la fuente de verdad de
    las ventas. Con esto, cualquier comando que deje un CSV malformado se detecta
    en el mismo turno, venga de donde venga.

    Se compara por mtime para que el caso normal (nada cambio) no cueste nada.
    """
    try:
        previo = json.load(io.open(ESTADO, encoding="utf-8"))
    except (OSError, ValueError):
        previo = {}

    actual, malos = {}, []
    try:
        nombres = [n for n in os.listdir(PROD) if n.lower().endswith(".csv")]
    except OSError:
        return 0
    for n in nombres:
        ruta = os.path.join(PROD, n)
        try:
            mt = os.path.getmtime(ruta)
        except OSError:
            continue
        actual[n] = mt
        if previo.get(n) == mt:
            continue                      # sin cambios desde la ultima pasada
        err = validar(ruta)
        if err:
            malos.append(err)

    try:
        json.dump(actual, io.open(ESTADO, "w", encoding="utf-8"))
    except OSError:
        pass

    if malos:
        sys.stderr.write("\n\n".join(malos) + "\n")
        return 2
    return 0


def main():
    if "--barrido" in sys.argv:
        return barrido()

    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0

    ruta = ((payload.get("tool_input") or {}).get("file_path") or "").strip()

    # El texto madre y el CSV de decision son dos caras del MISMO dato: si uno se
    # mueve sin el otro, el sistema queda diciendo una cosa y haciendo otra sin que
    # nadie se entere. Paso el 07-sep-2026 con la ventana (Guia 3, docstring 14).
    error = desincronizacion_guia_madre(ruta)
    if error:
        sys.stderr.write(error + "\n")
        return 2                         # bloquea y el mensaje llega a Claude

    # El grafo declarado: si se toca, se valida contra el disco y BLOQUEA si un ejecutor o un
    # archivo citado no existe. Un flujo que apunta a un subagente borrado dicta pasos imposibles.
    error = flujo_invalido(ruta)
    if error:
        sys.stderr.write(error + "\n")
        return 2

    # Un _PLAN.json nuevo o corregido cambia lo que el Lanzador tiene que dictar y el nodo en que
    # esta el producto. Sin esto, etapa-6 escribe el plan y la consola sigue mostrando el anterior.
    if os.path.basename(ruta).lower().startswith("_plan") and ruta.lower().endswith(".json"):
        regenerar(APP, os.path.basename(ruta), "lanzador y app")
        regenerar(FLUJO, os.path.basename(ruta), "flujo", ["--todo", "--silencioso"])
        return 0

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
    regenerar(DASHBOARD, nombre, "dashboard")
    # La app deriva presupuesto y break-even de estos mismos CSV: si cambian, la
    # consola tiene que volver a calcular o dicta plata vieja. gen_app.py corre el
    # lanzador y reescribe la app unificada, que lleva la data incrustada.
    regenerar(APP, nombre, "lanzador y app")
    # Y el flujo: un CSV que cambia puede mover a un producto de nodo (un ad_id escrito, un
    # evento LANZAMIENTO, una fila GENERADO). El estado se deriva, nunca se declara.
    if not nombre.startswith(("_ESTADO_FLUJO", "_FLUJO")):
        regenerar(FLUJO, nombre, "flujo", ["--todo", "--silencioso"])
    return 0


GATE_GUIA = os.path.join(BASE, "Ads", "_TOOLS", "verificar_guia_madre.py")

# Tocar cualquiera de estos dos puede desincronizar el texto madre de lo que corre.
ARCHIVOS_QUE_DISPARAN_GATE = ("_parametros_decision.csv", "guia_madre_parametrizada.md", "decidir.py")


def desincronizacion_guia_madre(ruta):
    """Devuelve el mensaje de falla si el texto madre dejo de coincidir con su ejecutor."""
    if not ruta or not os.path.exists(GATE_GUIA):
        return None
    if not ruta.lower().replace("\\", "/").endswith(ARCHIVOS_QUE_DISPARAN_GATE):
        return None
    try:
        r = subprocess.run([sys.executable, GATE_GUIA], cwd=BASE,
                           capture_output=True, timeout=120)
    except (subprocess.TimeoutExpired, OSError):
        return None                      # el gate caido no frena el trabajo
    if r.returncode == 0:
        print("hook: %s tocado, texto madre coherente con sus ejecutores."
              % os.path.basename(ruta))
        return None
    salida = (r.stdout or b"").decode("utf-8", "replace")
    detalle = salida[salida.find(" FALLAS"):].strip() if " FALLAS" in salida else salida.strip()
    return ("DESINCRONIZACION DEL TEXTO MADRE tras tocar %s.\n"
            "DOCTRINA/GUIA_MADRE_PARAMETRIZADA.md ya no coincide con lo que corre.\n"
            "Corregi el valor en la Guia Madre O en su ejecutor, para que digan lo mismo:\n\n%s"
            % (os.path.basename(ruta), detalle))


def flujo_invalido(ruta):
    """Devuelve el mensaje de falla si DOCTRINA/FLUJO.json quedo apuntando a algo que no existe."""
    if not ruta or not os.path.exists(FLUJO):
        return None
    if not ruta.lower().replace(chr(92), "/").endswith("doctrina/flujo.json"):
        return None
    try:
        r = subprocess.run([sys.executable, FLUJO, "--validar"], cwd=BASE,
                           capture_output=True, timeout=120)
    except (subprocess.TimeoutExpired, OSError):
        return None
    if r.returncode == 0:
        print("hook: FLUJO.json tocado y valido: cada ejecutor y archivo citado existe.")
        return None
    salida = (r.stdout or b"").decode("utf-8", "replace").strip()
    return ("FLUJO DECLARADO INVALIDO tras tocar DOCTRINA/FLUJO.json.\n"
            "Corregi el nodo o el predicado para que apunte a algo que exista:\n\n%s" % salida)


def regenerar(script, nombre, etiqueta, args=None):
    """Corre un generador. Un render que falla nunca bloquea: el CSV ya quedo bien."""
    if not os.path.exists(script):
        return
    try:
        r = subprocess.run([sys.executable, script] + list(args or []), cwd=BASE,
                           capture_output=True, timeout=120)
        if r.returncode == 0:
            print("hook: %s validado, %s regenerado." % (nombre, etiqueta))
        else:
            cola = (r.stderr or b"").decode("utf-8", "replace").strip().splitlines()
            print("hook: %s validado, pero %s fallo (exit %d). %s"
                  % (nombre, os.path.basename(script), r.returncode, cola[-1] if cola else ""))
    except (subprocess.TimeoutExpired, OSError) as e:
        print("hook: %s validado; no se pudo regenerar el %s (%s)." % (nombre, etiqueta, e))


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)                      # un hook roto no frena el trabajo
