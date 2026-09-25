#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""registrar_evento.py — el único escritor de PRODUCTOS/_EVENTOS.csv (CLI del operador/agentes) y,
desde P3 T4, el ÚNICO punto de escritura del sistema entero: `anexar()` la usan también
`flujo.py`, `perfilar_angulos.py` y `reingreso_f1.py` en vez de reescribir el CSV cada uno por su
cuenta (antes había cinco copias del mismo `csv.DictWriter`+CRLF).

Todo cambio que se ejecuta en Meta o en el bot deja una fila: sin ella el cambio no se puede
evaluar después. El caso que obliga a tener esta herramienta es el surfing: es la acción diaria
por defecto y `_EVENTOS.csv` no tenía un solo CAMBIO_PRESUPUESTO, así que la elasticidad del CPA
al presupuesto no se puede medir y ninguna política de asignación se puede validar.

`anexar()` (P3 T4) escribe SIEMPRE por Postgres (`db/escribir.py`): la verdad vive en
`raw.evento`, `_EVENTOS.csv` es el ESPEJO regenerado tras el commit — nunca se cae de vuelta a
escribir el CSV a mano si Postgres falla. Ver su docstring para el guardia de drift.

Valida antes de escribir (invariante 11):
    · producto_key existe en _DIM_PRODUCTOS.csv (o GLOBAL)
    · evento es una palabra en MAYÚSCULAS_CON_GUION_BAJO
    · motivo y fuente_decision no vacíos
    · CAMBIO_PRESUPUESTO: valor_antes y valor_despues numéricos, un conjunto o campaña, y la
      subida no supera surfing_pct de _PARAMETROS_DECISION.csv salvo --forzar

GATES SON CANDADO (P5, ver flujo.gate_entrada)
-----------------------------------------------
`--evento LANZAMIENTO` exige que el gate de ENTRADA de la fase que se lanza esté cumplido
(DOCTRINA/FLUJO.json, evaluado por `flujo.gate_entrada`). La fase sale de `--fase`, o si no se
pasa, del token de fase (`TOKEN_FASE` de flujo.py: TEST/CONCEPTOS/ESCALA·EXPLORA — fase 3 tiene
los dos últimos, P12) dentro de `--campana`; si ninguna resuelve, se detiene y pide `--fase`.
Un LANZAMIENTO de EXPLORA solo pasa el gate de ENTRADA a F3 (ya cumplido si el producto está en
F3); el gate propio de F3.exploracion (F3 rentable, `flujo.gate_nodo`) lo exige
`gen_publicacion.py --fase 3 --brazo EXPLORACION`, no este script. Con el gate incumplido, se
detiene (nada se escribe) salvo que se pase `--excepcion "motivo"`: entonces el LANZAMIENTO se
registra igual Y además queda una fila EXCEPCION en `_EVENTOS.csv` (mismo escritor, una sola
llamada a `anexar()` por fila — invariante 11).

USO
    python Ads/_TOOLS/registrar_evento.py --producto TINNIDROP --evento CAMBIO_PRESUPUESTO \\
        --cuenta GTR0 --conjunto GTR0_TINNIDROP_PERDIDA-AUDITIVA_R1 --antes 4.49 --despues 5.39 \\
        --motivo "ESCALAR del motor: surfing +20%" --fuente "decidir.py 2026-09-11 · confirmado operador"
    python Ads/_TOOLS/registrar_evento.py --producto TINNIDROP --evento LANZAMIENTO --fase 3 \\
        --motivo "..." --fuente "..." --excepcion "el operador decide escalar sin el gate"
    ... --dry-run      # muestra la fila y no escribe
"""
import argparse
import csv
import datetime
import io
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except (AttributeError, OSError):
    pass

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROD = os.path.join(BASE, "PRODUCTOS")
EVENTOS = os.path.join(PROD, "_EVENTOS.csv")
TOOLS = os.path.join(BASE, "Ads", "_TOOLS")
if TOOLS not in sys.path:
    sys.path.insert(0, TOOLS)
import flujo  # gate_entrada: el único juez de "¿se cumple el gate de entrada a la fase N?"
import upsert_fact  # respaldos_dir(): mismo nombrado/patrón de backup que el resto de P3

sys.path.insert(0, os.path.join(BASE, "db"))
import cargar as db_cargar      # noqa: E402
import escribir as db_escribir  # noqa: E402

COLS = ["fecha", "producto_key", "cuenta_alias", "campana_clave", "conjunto_meta", "evento",
        "valor_antes", "valor_despues", "motivo", "fuente_decision"]

# P3 T4: la VERDAD de _EVENTOS.csv pasa a vivir en Postgres (raw.evento / core.evento); el CSV en
# PRODUCTOS/ se vuelve el ESPEJO, regenerado por db/escribir.py DESPUÉS del commit. TENANT_ID/
# BKDIR son puntos de override para pruebas (mismo patrón que ingerir_lucidsales.py, T3): aíslan
# cada escenario en su propio tenant dentro de `vitalcom_test`, nunca tocan `vitalcom` real.
TENANT_ID = "vitalcom"
BKDIR = upsert_fact.respaldos_dir(BASE, "backups_csv")


def leer(nombre):
    ruta = os.path.join(PROD, nombre)
    if not os.path.exists(ruta):
        return []
    with io.open(ruta, encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def surfing_pct():
    for r in leer("_PARAMETROS_DECISION.csv"):
        if (r.get("parametro") or "").strip() == "surfing_pct":
            try:
                return float(r.get("valor"))
            except (TypeError, ValueError):
                return None
    return None


def validar(fila, forzar):
    errores = []
    try:
        datetime.date.fromisoformat(fila["fecha"])
    except ValueError:
        errores.append("fecha '%s' no es YYYY-MM-DD" % fila["fecha"])
    productos = {(r.get("producto_key") or "").strip() for r in leer("_DIM_PRODUCTOS.csv")}
    if fila["producto_key"] != "GLOBAL" and fila["producto_key"] not in productos:
        errores.append("producto_key '%s' no tiene fila en _DIM_PRODUCTOS.csv" % fila["producto_key"])
    if not re.fullmatch(r"[A-Z][A-Z0-9_]*", fila["evento"]):
        errores.append("evento '%s' debe ir en MAYÚSCULAS_CON_GUION_BAJO" % fila["evento"])
    for campo in ("motivo", "fuente_decision"):
        if not fila[campo].strip():
            errores.append("%s vacío: un evento sin por qué no se puede evaluar" % campo)

    if fila["evento"] == "CAMBIO_PRESUPUESTO":
        try:
            antes, despues = float(fila["valor_antes"]), float(fila["valor_despues"])
        except ValueError:
            errores.append("CAMBIO_PRESUPUESTO exige --antes y --despues numéricos (USD/día)")
            return errores
        if fila["conjunto_meta"] in ("", "*") and fila["campana_clave"] in ("", "*"):
            errores.append("CAMBIO_PRESUPUESTO exige --conjunto o --campana: sin objeto no hay elasticidad que medir")
        tope = surfing_pct()
        if antes > 0 and tope is not None and not forzar:
            pct = (despues / antes - 1) * 100
            if pct > tope + 0.5:
                errores.append("subida de %.1f %% supera surfing_pct = %g %%; si es deliberado, usar --forzar"
                               % (pct, tope))
    return errores


def anexar(filas):
    """ÚNICO escritor de _EVENTOS.csv (P3 T4, invariante 11 + "un dato, un dueño"): antes había
    CINCO copias independientes de este mismo CRLF+DictWriter (acá, flujo.py:escribir_estado,
    perfilar_angulos.py:registrar_transiciones, reingreso_f1.py:anexar_evento, y esta misma
    función llamada por gen_publicacion.py vía registrar_excepcion()). Los otros tres módulos
    ahora llaman esta función en vez de reescribir el CSV por su cuenta.

    Acepta UNA fila (dict) o VARIAS (list[dict]) — flujo.py y perfilar_angulos.py pueden anexar
    varias transiciones de una sola corrida; se escriben todas en UNA sola transacción. Escribe
    SIEMPRE por Postgres (db/escribir.py): la verdad vive en `raw.evento`, el CSV en PRODUCTOS/ es
    el ESPEJO regenerado después del commit. Postgres no disponible, o falla el guardia de
    drift/la transacción -> SystemExit con mensaje claro; NUNCA se cae de vuelta a escribir el CSV
    a mano (ver db/escribir.py, punto 4 de su docstring). Devuelve la cantidad de filas escritas."""
    if isinstance(filas, dict):
        filas = [filas]
    if not filas:
        return 0
    prod_dir = os.path.dirname(EVENTOS)
    try:
        con = db_cargar.conectar()
    except Exception as exc:
        raise SystemExit(
            "\n⛔ Postgres no disponible: no se pudo escribir _EVENTOS.csv (nunca se escribe "
            "el CSV directo). Detalle: %s" % exc)
    try:
        db_escribir.verificar_csv_sincronizado(con, "evento", prod_dir, tenant_id=TENANT_ID)
        n = db_escribir.anexar(con, "evento", filas, prod_dir=prod_dir, bkdir=BKDIR,
                                tenant_id=TENANT_ID)
    except db_escribir.ErrorEscritura as exc:
        raise SystemExit("\n⛔ %s" % exc)
    finally:
        con.close()
    return n


def resolver_fase(fase_arg, campana):
    """La fase de un LANZAMIENTO: `--fase` explícito, o el token de flujo.TOKEN_FASE
    (TEST/CONCEPTOS/ESCALA·EXPLORA) que aparezca en `--campana`. Fase 3 tiene DOS tokens posibles
    (ESCALA y EXPLORA, P12) — ambos resuelven a fase '3', el mismo gate de entrada.
    Ninguna de las dos -> (None, motivo)."""
    if fase_arg:
        return str(fase_arg).strip(), "explícita (--fase)"
    camp = (campana or "").upper()
    vistos = [(f, t) for f, toks in flujo.TOKEN_FASE.items() for t in toks if t in camp]
    fases_vistas = sorted({f for f, _ in vistos})
    if len(fases_vistas) == 1:
        toks_hallados = [t for f, t in vistos]
        return fases_vistas[0], "token '%s' en --campana" % "/".join(toks_hallados)
    if not vistos:
        return None, "--campana '%s' no trae ningún token de fase (%s)" % (
            campana, "/".join(t for toks in flujo.TOKEN_FASE.values() for t in toks))
    return None, "--campana '%s' trae más de un token de fase (%s): ambigua" % (
        campana, ", ".join("%s=%s" % (f, t) for f, t in vistos))


def registrar_excepcion(producto_key, gate, accion, motivo, fuente, fecha=None):
    """La ÚNICA forma de anexar una fila EXCEPCION: reusa `validar()`/`anexar()`, el mismo
    escritor de todo `_EVENTOS.csv` (invariante 11) — no se duplica la escritura de CSV.
    `gate` es el gate incumplido (p.ej. 'F3.entrada'); `accion` es lo que procedió igual
    (p.ej. 'LANZAMIENTO' o 'gen_publicacion --fase 3'). Devuelve (ok, errores)."""
    fila = {"fecha": fecha or datetime.date.today().isoformat(), "producto_key": producto_key.strip(),
            "cuenta_alias": "*", "campana_clave": "*", "conjunto_meta": "*", "evento": "EXCEPCION",
            "valor_antes": gate, "valor_despues": accion, "motivo": (motivo or "").strip(),
            "fuente_decision": fuente}
    errores = validar(fila, forzar=True)
    if errores:
        return False, errores
    anexar(fila)
    return True, []


def main():
    ap = argparse.ArgumentParser(description="Anexa un evento validado a PRODUCTOS/_EVENTOS.csv")
    ap.add_argument("--producto", required=True, help="producto_key o GLOBAL")
    ap.add_argument("--evento", required=True)
    ap.add_argument("--motivo", required=True)
    ap.add_argument("--fuente", required=True, help="fuente_decision: quién decidió y con qué")
    ap.add_argument("--fecha", default=datetime.date.today().isoformat())
    ap.add_argument("--cuenta", default="*")
    ap.add_argument("--campana", default="*")
    ap.add_argument("--conjunto", default="*")
    ap.add_argument("--antes", default="")
    ap.add_argument("--despues", default="")
    ap.add_argument("--forzar", action="store_true", help="acepta una subida mayor a surfing_pct")
    ap.add_argument("--fase", help="fase del LANZAMIENTO (1/2/3); si falta, se deriva del token "
                                    "TEST/CONCEPTOS/ESCALA en --campana")
    ap.add_argument("--excepcion", help="motivo para proceder pese a un gate de fase incumplido "
                                         "(queda una fila EXCEPCION en _EVENTOS.csv)")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    fila = {"fecha": a.fecha, "producto_key": a.producto.strip(), "cuenta_alias": a.cuenta.strip(),
            "campana_clave": a.campana.strip(), "conjunto_meta": a.conjunto.strip(),
            "evento": a.evento.strip().upper(), "valor_antes": a.antes.strip(),
            "valor_despues": a.despues.strip(), "motivo": a.motivo.strip(),
            "fuente_decision": a.fuente.strip()}

    # -- P5: el gate de fase es un candado, no una sugerencia (invariante: gates de FLUJO.json) --
    fase, excepcion = None, (a.excepcion or "").strip()
    ok_gate = True
    if fila["evento"] == "LANZAMIENTO":
        fase, motivo_fase = resolver_fase(a.fase, fila["campana_clave"])
        if fase is None:
            print("NO SE REGISTRÓ: no se pudo resolver la fase del LANZAMIENTO (%s)." % motivo_fase)
            print("               Pasar --fase explícito.")
            return 1
        ok_gate, obs_gate = flujo.gate_entrada(fila["producto_key"], fase, flujo.Entorno(base=BASE))
        if not ok_gate and not excepcion:
            print("NO SE REGISTRÓ: el gate de entrada a F%s no está cumplido: %s" % (fase, obs_gate))
            print("               Invariante: la fase se abre por el gate declarado en DOCTRINA/FLUJO.json, "
                  "nunca por decisión del operador o del modelo.")
            print("               Si es deliberado, repetir con --excepcion \"motivo\": queda una fila "
                  "EXCEPCION en _EVENTOS.csv y el LANZAMIENTO se registra igual.")
            return 1

    errores = validar(fila, a.forzar)
    if errores:
        print("NO SE REGISTRÓ:\n  · " + "\n  · ".join(errores))
        return 1
    if a.dry_run:
        print("[dry-run] se anexaría:", fila)
        if not ok_gate:
            print("[dry-run] se anexaría también: EXCEPCION F%s.entrada -> LANZAMIENTO (%s)" % (fase, excepcion))
        return 0
    anexar(fila)
    print("registrado en PRODUCTOS/_EVENTOS.csv: %s %s %s" % (fila["fecha"], fila["producto_key"], fila["evento"]))

    if not ok_gate:   # gate incumplido pero con --excepcion no vacío (si no, ya se detuvo arriba)
        ok_ev, errores_ev = registrar_excepcion(fila["producto_key"], "F%s.entrada" % fase, "LANZAMIENTO",
                                                 excepcion, "Ads/_TOOLS/registrar_evento.py", fecha=a.fecha)
        if not ok_ev:
            print("AVISO: el LANZAMIENTO quedó registrado pero la EXCEPCION no se pudo anexar:\n  · "
                  + "\n  · ".join(errores_ev))
            return 1
        print("EXCEPCION registrada: F%s.entrada -> LANZAMIENTO (%s)" % (fase, excepcion))
    return 0


if __name__ == "__main__":
    sys.exit(main())
