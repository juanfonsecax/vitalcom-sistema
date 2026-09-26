#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ciclo_diario.py — CORREDOR DETERMINÍSTICO del ciclo nocturno, para Task Scheduler.

NO usa LLM. Encadena, en el mismo intérprete que lo invoca (`sys.executable`), los mismos
comandos que hoy documentan las skills `recopilar-lucidsales` y `ciclo-diario`:

    bajar_lucidsales.py -> ingerir_lucidsales.py
    [solo lunes] bajar_lucidsales.py --dias 7 -> ingerir_lucidsales.py --rol CONTROL
    bajar_meta_insights.py
    ciclo_hoy.py        (gen_decisiones -> flujo --todo --escribir -> gen_lanzador -> gen_app)
    gen_dashboard.py

POR QUÉ EXISTE (P3 T6, 25-sep-2026): la tarea programada de Claude Code (`auditoria-vitalcom-
diaria`) se corta a los ~5s de emitir su primer Bash: una sesión desatendida no tiene a nadie que
apruebe el permiso de la herramienta. Este script hace la parte DETERMINÍSTICA (bajar, ingerir,
decidir, regenerar) sin necesitar ningún permiso interactivo; Claude solo entra DESPUÉS, en modo
lectura, a interpretar lo que este script ya dejó escrito (ver T8b: el prompt de la tarea
programada).

FALLBACK MANUAL DE LUCIDSALES (T4, 26-sep-2026): `Ads/_TOOLS/recopilar_lucidsales.py` corre SOLO
los pasos de `pasos_lucidsales()` (bajar + ingerir, y el control semanal los lunes) — es el botón
"Traer las ventas de LucidSales" de la app, ahora `ejecutor_tipo: script` en vez de una sesión de
Claude para dos comandos deterministas. Comparte la lista de pasos con este módulo (`pasos_lucidsales()`
es su única fuente); no corre el preflight/postcheck de Postgres de este archivo ni escribe fila en
`_CORRIDAS_DIARIAS.csv` (ver el docstring de `recopilar_lucidsales.py` para el porqué).

DUPLICACIÓN CONOCIDA (reportada, no resuelta acá): `app/backend/vitalcom_app/workflows.py`
(`PASOS_CICLO_NOCTURNO`/`ejecutar_ciclo_nocturno`) ya modela una cadena nocturna casi idéntica
(`nodo.ciclo.datos` -> `ciclo.bajar_meta` -> `nodo.ciclo.motor` -> `sistema.refrescar_flujo` ->
`sistema.gen_app`), pero corre DENTRO del runtime DBOS de la app web: resuelve cada paso contra
`acciones.py` (el manifiesto), lo encola en la cola `escritura` y espera con `esperar_resultado()`.
Ese camino exige la app (`app/backend`) levantada; este script es standalone, a propósito, para
que Task Scheduler lo dispare sin depender de que la app esté corriendo. Fusionar los dos motores
de pasos queda fuera de este cambio — este docstring es el registro de la duplicación.

PREFLIGHT (obligatorio, nunca se salta): Postgres es la VERDAD (P3). Antes de tocar nada se
verifica que se puede conectar y que cada tabla de `db.tables.TABLAS_MIGRADAS_DB` y
`_DECISIONES.json` están sincronizadas con su CSV espejo (`db.escribir.verificar_csv_sincronizado`/
`verificar_decision_sincronizada`). Cualquier falla ahí es ROJO inmediato: nunca se cae a leer o
escribir el CSV directo (invariante P3: Postgres nunca se bypassea en silencio).

POSTCHECK: al terminar la cadena se repite el mismo preflight y además una PARIDAD: `decidir.py
--json` con la fuente por defecto (Postgres) tiene que dar EXACTAMENTE lo mismo que
`VITALCOM_FUENTE=csv decidir.py --json`, descontando la clave `generado` (that trae la fecha de
hoy y cambiaría entre dos corridas del mismo instante). Un `DISTINTO` es ROJO: significa que el
espejo CSV y Postgres divergen para el motor de decisión.

CLASIFICACIÓN DE UN DÍA (T6, decidida y justificada acá — no se repite en otro lado):
  VERDE     — todos los pasos en 0, paridad IGUAL.
  AMARILLO  — la cadena llegó al final (paridad IGUAL) pero al menos un paso salió con un código
              de AVISO. Hoy el único caso es `bajar_meta_insights.py` código 2 (PARCIAL: al menos
              una cuenta de Meta OK y al menos una falló). Se decide que AMARILLO SÍ CUENTA como
              día verde para el conteo de 7 días consecutivos de T7: las filas de las cuentas que
              sí respondieron ya quedaron escritas (ver bajar_meta_insights.py, contrato de
              salida), LucidSales (la fuente de VENTAS, que es lo que `decidir.py` mide) llegó
              completo, y el propio `ejecutar_ciclo_nocturno` del backend ya trata el código 2
              como aviso que no corta la cadena (mismo precedente, ver workflows.py). Si en el
              futuro un PARCIAL de Meta implicara ventas sin CPA calculable (spend ausente para un
              producto vivo), esa sería una razón para revisar este criterio — hoy no es el caso
              porque el motor de decisión agrega por ángulo/producto, no por cuenta.
  ROJO      — falló un paso fatal, el preflight o el postcheck (incluida una PARIDAD DISTINTA).

EL LOG (`_RESPALDOS/logs/ciclo_diario_YYYYMMDD.log`, gitignored) es el detalle completo: stdout +
stderr de cada paso. `_CORRIDAS_DIARIAS.csv` es el resumen de una línea que cuenta T7; no
reemplaza al log.

Uso:
    python Ads/_TOOLS/ciclo_diario.py                  # corre la cadena completa
    python Ads/_TOOLS/ciclo_diario.py --si-falta-hoy   # sale en 0 sin hacer nada si hoy ya está
                                                        # VERDE o AMARILLO (dispara doble sin daño)
    python Ads/_TOOLS/ciclo_diario.py --dry-run        # imprime el plan, no corre ni escribe nada

CÓDIGO DE SALIDA: 0 en VERDE o AMARILLO (o con --si-falta-hoy si ya había fila hoy) · 1 en ROJO.
"""
from __future__ import annotations

import argparse
import csv
import datetime
import json
import os
import subprocess
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except (AttributeError, OSError):
    pass

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOOLS = os.path.join(BASE, "Ads", "_TOOLS")
PROD = os.path.join(BASE, "PRODUCTOS")
LOGDIR = os.path.join(BASE, "_RESPALDOS", "logs")
CORRIDAS_CSV = os.path.join(PROD, "_CORRIDAS_DIARIAS.csv")
TENANT_ID = "vitalcom"

COLUMNAS = ["fecha", "inicio", "fin", "estado", "paso_fallido", "paridad", "detalle"]

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "db"))


def _ahora():
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


# ── plan de pasos (dict de datos: nombre, argv, códigos fatales/aviso) ──────────────────────────

def _paso(nombre, argv, codigos_aviso=()):
    return {"nombre": nombre, "argv": argv, "codigos_aviso": tuple(codigos_aviso)}


def pasos_lucidsales(hoy):
    """Los pasos de LucidSales de la cadena nocturna, en orden. `hoy` decide el control semanal
    (lunes). ÚNICA fuente de esta sub-secuencia: la reusa también `recopilar_lucidsales.py`, el
    fallback manual del botón "Traer las ventas de LucidSales" (T4, 26-sep-2026) — un dato, un
    dueño, para no tener dos copias de la cadena que puedan divergir."""
    py = sys.executable
    ingesta_dir = os.path.join(BASE, "Ads", "_INGESTA", "LUCIDSALES")
    pasos = [
        _paso("bajar_lucidsales", [py, os.path.join(TOOLS, "bajar_lucidsales.py")]),
        _paso("ingerir_lucidsales",
              [py, os.path.join(TOOLS, "ingerir_lucidsales.py"), "--dir", ingesta_dir]),
    ]
    if hoy.weekday() == 0:  # lunes: control semanal, SIEMPRE --rol CONTROL (nunca se suma a BASE)
        pasos.append(_paso("bajar_lucidsales_control",
                            [py, os.path.join(TOOLS, "bajar_lucidsales.py"), "--dias", "7"]))
        pasos.append(_paso("ingerir_lucidsales_control",
                            [py, os.path.join(TOOLS, "ingerir_lucidsales.py"),
                             "--dir", ingesta_dir, "--rol", "CONTROL"]))
    return pasos


def pasos_reales(hoy):
    """La cadena de la corrida nocturna real, en orden. `hoy` decide el control semanal (lunes)."""
    py = sys.executable
    pasos = list(pasos_lucidsales(hoy))
    pasos.append(_paso("bajar_meta_insights", [py, os.path.join(TOOLS, "bajar_meta_insights.py")],
                        codigos_aviso=(2,)))
    pasos.append(_paso("ciclo_hoy", [py, os.path.join(TOOLS, "ciclo_hoy.py")]))
    pasos.append(_paso("gen_dashboard", [py, os.path.join(TOOLS, "gen_dashboard.py")]))
    return pasos


def _clasificar(paso, codigo):
    if codigo == 0:
        return "OK"
    if codigo in paso["codigos_aviso"]:
        return "AVISO"
    return "FATAL"


# ── ejecución de un paso (inyectable para tests: nunca se llama directo desde afuera) ───────────

def ejecutar_paso_real(paso, log_fh):
    log_fh.write(("$ " + " ".join(paso["argv"]) + "\n").encode("utf-8"))
    log_fh.flush()
    entorno = dict(os.environ, PYTHONIOENCODING="utf-8")
    r = subprocess.run(paso["argv"], cwd=BASE, env=entorno,
                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    log_fh.write(r.stdout or b"")
    log_fh.write(("\n[exit %d]\n" % r.returncode).encode("utf-8"))
    log_fh.flush()
    return r.returncode


# ── preflight / postcheck (inyectables: los tests nunca tocan Postgres real) ────────────────────

def preflight_real(etapa="preflight"):
    """Conecta a Postgres y verifica que cada tabla migrada y `_DECISIONES.json` están
    sincronizados con su CSV espejo. Nunca cae a CSV: una falla acá es ROJO, punto.
    `etapa` solo nombra en el mensaje dónde falló (preflight o postcheck)."""
    import cargar as db_cargar  # noqa: E402  (db/cargar.py)
    import escribir as db_escribir  # noqa: E402  (db/escribir.py)
    import tables as db_tables  # noqa: E402  (db/tables.py)
    try:
        con = db_cargar.conectar()
    except Exception as exc:  # noqa: BLE001 — cualquier fallo de conexión es preflight ROJO
        return False, "Postgres no disponible: %s" % exc
    try:
        for tabla in sorted(db_tables.TABLAS_MIGRADAS_DB):
            db_escribir.verificar_csv_sincronizado(con, tabla, PROD, tenant_id=TENANT_ID)
        db_escribir.verificar_decision_sincronizada(con, PROD, tenant_id=TENANT_ID)
    except db_escribir.ErrorEscritura as exc:
        return False, "Guardia de drift falló en %s: %s" % (etapa, exc)
    finally:
        con.close()
    return True, ""


def _decidir_json(env_extra):
    entorno = dict(os.environ, PYTHONIOENCODING="utf-8", **env_extra)
    r = subprocess.run([sys.executable, os.path.join(TOOLS, "decidir.py"), "--json"],
                        cwd=BASE, env=entorno, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if r.returncode != 0:
        raise RuntimeError((r.stderr or r.stdout or b"").decode("utf-8", "replace")[-500:])
    datos = json.loads(r.stdout.decode("utf-8"))
    datos.pop("generado", None)
    return datos


def postcheck_real():
    """Repite el preflight y compara `decidir.py --json` en Postgres vs `VITALCOM_FUENTE=csv`.

    Devuelve (ok, paridad, detalle) donde paridad es IGUAL / DISTINTO / NO_CORRIDA.
    """
    ok, detalle = preflight_real(etapa="postcheck")
    if not ok:
        return False, "NO_CORRIDA", detalle
    try:
        db = _decidir_json({})
        csv_ = _decidir_json({"VITALCOM_FUENTE": "csv"})
    except Exception as exc:  # noqa: BLE001
        return False, "NO_CORRIDA", "No se pudo correr decidir.py --json para la paridad: %s" % exc
    if db == csv_:
        return True, "IGUAL", ""
    return False, "DISTINTO", "decidir.py --json difiere entre Postgres y VITALCOM_FUENTE=csv."


# ── el CSV de corridas (SOLO este archivo: es log operativo, no espejo de Postgres) ─────────────
#
# A propósito NO pasa por db/escribir.py: tiene que poder registrar un día ROJO incluso cuando
# Postgres está caído (esa es justamente la mitad de los días que le importan a T7). Es el único
# CSV del sistema que se escribe siempre en disco, sin pasar por la verdad de Postgres.

def _leer_corridas(ruta_csv):
    if not os.path.isfile(ruta_csv):
        return []
    with open(ruta_csv, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def fila_de_hoy(ruta_csv, hoy_iso):
    filas = [f for f in _leer_corridas(ruta_csv) if f.get("fecha") == hoy_iso]
    return filas[-1] if filas else None


# ── racha de días verdes (P3 T7): el criterio de cierre de P3 ─────────────────────────────────
#
# Un día es VERDE si su ÚLTIMA corrida es VERDE o AMARILLO (un ROJO corregido el mismo día con
# una corrida verde posterior cuenta: el ciclo del día terminó completo). Un día faltante o que
# termina en ROJO corta la racha. Si hoy todavía no corrió, la racha que llega a ayer sigue viva.

DIAS_PARA_CERRAR_P3 = 7


def racha_verde(ruta_csv, hoy):
    """Devuelve (dias, ultimo_dia_iso) de la racha de días verdes consecutivos que termina hoy,
    o ayer si hoy todavía no tiene fila. (0, None) si no hay racha."""
    ultimo_por_dia = {}
    for f in _leer_corridas(ruta_csv):
        ultimo_por_dia[f.get("fecha", "")] = f.get("estado", "")
    dia = hoy if hoy.isoformat() in ultimo_por_dia else hoy - datetime.timedelta(days=1)
    dias, ultimo = 0, None
    while ultimo_por_dia.get(dia.isoformat()) in ("VERDE", "AMARILLO"):
        ultimo = ultimo or dia.isoformat()
        dias += 1
        dia -= datetime.timedelta(days=1)
    return dias, ultimo


def texto_racha(ruta_csv, hoy):
    dias, ultimo = racha_verde(ruta_csv, hoy)
    if dias >= DIAS_PARA_CERRAR_P3:
        return "Racha: %d días verdes seguidos (hasta %s) — criterio de cierre de P3 cumplido." % (
            dias, ultimo)
    return "Racha: %d/%d días verdes seguidos%s." % (
        dias, DIAS_PARA_CERRAR_P3, " (hasta %s)" % ultimo if ultimo else "")


def _escribir_fila(ruta_csv, fila):
    nuevo = not os.path.isfile(ruta_csv)
    os.makedirs(os.path.dirname(ruta_csv), exist_ok=True)
    with open(ruta_csv, "a", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        if nuevo:
            w.writerow(COLUMNAS)
        # Una fila = una línea: los saltos dentro del detalle mezclaban CRLF y LF en el CSV.
        w.writerow([" ".join(str(fila.get(c, "")).split()) for c in COLUMNAS])


# ── el corredor: puro en su lógica de estados, inyectado en I/O para que los tests no toquen disco real ──

def correr(*, pasos, ejecutar_paso, preflight, postcheck, log_fh, hoy_iso):
    """Corre la cadena y devuelve la fila de `_CORRIDAS_DIARIAS.csv` (dict). Nunca lanza: cualquier
    excepción de un paso ya la captura el subprocess (código de salida != 0); una excepción de
    preflight/postcheck se atrapa acá para que la fila SIEMPRE se pueda escribir."""
    inicio = _ahora()
    estado = "VERDE"
    paso_fallido = ""
    paridad = "NO_CORRIDA"
    detalles = []

    try:
        ok, detalle = preflight()
    except Exception as exc:  # noqa: BLE001 — un preflight roto es ROJO, no un crash del runner
        ok, detalle = False, "Preflight lanzó una excepción: %r" % exc
    if not ok:
        return {
            "fecha": hoy_iso, "inicio": inicio, "fin": _ahora(), "estado": "ROJO",
            "paso_fallido": "preflight", "paridad": "NO_CORRIDA", "detalle": detalle[:500],
        }

    for paso in pasos:
        try:
            codigo = ejecutar_paso(paso, log_fh)
        except Exception as exc:  # noqa: BLE001 — un paso que revienta el runner también es ROJO
            codigo, veredicto = -1, "FATAL"
            detalles.append("%s: excepción del runner: %r" % (paso["nombre"], exc))
        else:
            veredicto = _clasificar(paso, codigo)
        if veredicto == "AVISO":
            estado = "AMARILLO" if estado != "ROJO" else estado
            detalles.append("%s: código de aviso %s" % (paso["nombre"], codigo))
        elif veredicto == "FATAL":
            estado = "ROJO"
            paso_fallido = paso["nombre"]
            detalles.append("%s: código fatal %s" % (paso["nombre"], codigo))
            break

    if estado != "ROJO":
        try:
            ok, paridad, detalle = postcheck()
        except Exception as exc:  # noqa: BLE001
            ok, paridad, detalle = False, "NO_CORRIDA", "Postcheck lanzó una excepción: %r" % exc
        if not ok:
            estado = "ROJO"
            paso_fallido = paso_fallido or "postcheck"
            detalles.append(detalle)

    return {
        "fecha": hoy_iso, "inicio": inicio, "fin": _ahora(), "estado": estado,
        "paso_fallido": paso_fallido, "paridad": paridad, "detalle": " | ".join(detalles)[:800],
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description="Corredor determinístico del ciclo diario (T6).")
    ap.add_argument("--si-falta-hoy", action="store_true",
                     help="Sale en 0 sin hacer nada si hoy ya tiene una fila VERDE/AMARILLO.")
    ap.add_argument("--dry-run", action="store_true",
                     help="Imprime el plan de pasos y no corre ni escribe nada.")
    ap.add_argument("--racha", action="store_true",
                     help="Solo imprime la racha de días verdes seguidos (criterio de cierre de P3).")
    a = ap.parse_args(argv)

    hoy = datetime.date.today()
    hoy_iso = hoy.isoformat()

    if a.racha:
        print(texto_racha(CORRIDAS_CSV, hoy))
        return 0

    pasos = pasos_reales(hoy)

    if a.dry_run:
        print("PLAN ciclo_diario.py para %s (lunes=%s):" % (hoy_iso, hoy.weekday() == 0))
        for i, paso in enumerate(pasos, 1):
            print("  %d. %s -> %s" % (i, paso["nombre"], " ".join(paso["argv"])))
        print("Preflight: Postgres + drift guard sobre TABLAS_MIGRADAS_DB + _DECISIONES.json.")
        print("Postcheck: mismo guard + paridad decidir.py --json (Postgres vs VITALCOM_FUENTE=csv).")
        print("[dry-run] no se corrió ni se escribió nada.")
        return 0

    if a.si_falta_hoy:
        fila = fila_de_hoy(CORRIDAS_CSV, hoy_iso)
        if fila is not None and fila.get("estado") in ("VERDE", "AMARILLO"):
            print("Ya hay una corrida %s para %s (%s): no se repite." %
                  (fila.get("estado"), hoy_iso, fila.get("fin")))
            print(texto_racha(CORRIDAS_CSV, hoy))
            return 0

    os.makedirs(LOGDIR, exist_ok=True)
    log_path = os.path.join(LOGDIR, "ciclo_diario_%s.log" % hoy.strftime("%Y%m%d"))
    with open(log_path, "ab") as log_fh:
        fila = correr(pasos=pasos, ejecutar_paso=ejecutar_paso_real, preflight=preflight_real,
                      postcheck=postcheck_real, log_fh=log_fh, hoy_iso=hoy_iso)

    _escribir_fila(CORRIDAS_CSV, fila)
    print("%s %s · paso_fallido=%s · paridad=%s · %s" % (
        fila["fecha"], fila["estado"], fila["paso_fallido"] or "-", fila["paridad"], fila["detalle"]))
    print("Log completo: %s" % os.path.relpath(log_path, BASE))
    print(texto_racha(CORRIDAS_CSV, hoy))
    return 0 if fila["estado"] in ("VERDE", "AMARILLO") else 1


if __name__ == "__main__":
    sys.exit(main())
