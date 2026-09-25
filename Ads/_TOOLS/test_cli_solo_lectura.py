#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_cli_solo_lectura.py — CONTRATO DE CLI (T6, 23-sep-2026): "un mirar nunca escribe".

`flujo.py`, `decidir.py` y `gen_grafo.py` calculan sobre la data del sistema. Antes de este
cambio, correrlos para MIRAR algo (`flujo.py --todo`, `decidir.py` a secas, `gen_grafo.py`) tocaba
disco como efecto secundario — toda verificación tenía que `git checkout` los archivos después.
Ahora los tres son SOLO LECTURA por defecto y necesitan `--escribir` explícito para persistir:

    flujo.py --todo              -> no toca _ESTADO_FLUJO.csv/_EVENTOS.csv/_FLUJO.json/FLUJO.html
    flujo.py --todo --escribir   -> sí los toca
    decidir.py                   -> no toca _DECISIONES.json
    decidir.py --escribir        -> sí lo toca
    gen_grafo.py                 -> no toca _LINEA_BASE_SISTEMA.json
    gen_grafo.py --escribir      -> sí lo toca

Este archivo congela las dos mitades (lee/calcula vs escribe) de cada script, más un chequeo
estático de que los callers que SÍ necesitan la escritura (cadena nocturna, acción de manifiesto,
arranque de sesión) piden `--escribir` explícitamente — así un cambio futuro que rompa alguno de
los dos lados sale solo, sin que alguien tenga que notar el `git status` sucio a mano.

P3 T4 (continuación) — `flujo.py --todo --escribir` y `decidir.py --escribir` ahora escriben
PRIMERO en Postgres (`db/escribir.reemplazar()`/`reemplazar_decision()`) y regeneran su mirror
CSV/JSON después del commit. Aislamiento CRÍTICO (mismo patrón que
`Ads/_TOOLS/test_registrar_evento.py`): fuerza `PGDATABASE=vitalcom_test`, y cada escenario de
escritura bootstrapea `raw.estado_flujo`/`raw.decisiones_json` en su PROPIO tenant único (nunca
`vitalcom` real) antes de correr el escritor real. Se salta con aviso si `vitalcom_test` no está
disponible en este entorno.

USO:  python Ads/_TOOLS/test_cli_solo_lectura.py     (exit 0 = pasa, 1 = falla)
"""
import csv
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import uuid

# Aislamiento CRÍTICO: forzar vitalcom_test ANTES de que cualquier prueba de escritura llame a
# `db_cargar.conectar()` (decidir.py/flujo.py importan `db/` de forma LOCAL, recién dentro de
# `--escribir`, así que alcanza con fijarlo acá, a nivel de módulo -- mismo motivo que
# test_registrar_evento.py/db/test_db.py).
os.environ["PGDATABASE"] = "vitalcom_test"

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import decidir  # noqa: E402
import flujo  # noqa: E402
import test_flujo as tf  # noqa: E402

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

sys.path.insert(0, os.path.join(BASE, "db"))
import cargar as db_cargar      # noqa: E402
import nucleo as db_nucleo      # noqa: E402


def _conectar_seguro():
    con = db_cargar.conectar()
    if con.info.dbname == "vitalcom":
        con.close()
        raise RuntimeError(
            "test_cli_solo_lectura.py intento conectarse a 'vitalcom' en vez de 'vitalcom_test'. "
            "Abortado antes de tocar nada.")
    return con


def _db_disponible():
    try:
        con = _conectar_seguro()
        con.close()
        return True
    except Exception:
        return False


DB_DISPONIBLE = _db_disponible()


def _tenant_unico(nombre):
    return "test_cli_%s_%s" % (nombre, uuid.uuid4().hex[:8])


def _informe(ok, texto, detalle=""):
    print(("  OK     " if ok else "  FALLA  ") + texto + ("" if ok else "\n         %r" % (detalle,)))
    return 0 if ok else 1


# ── flujo.py ─────────────────────────────────────────────────────────────────

def _correr_flujo_todo(tmp, extra_argv):
    previo = sys.argv
    try:
        sys.argv = ["flujo.py", "--base", tmp, "--hoy", "2026-09-14", "--sin-scripts",
                    "--todo", "--silencioso"] + extra_argv
        return flujo.main()
    finally:
        sys.argv = previo


def _rutas_flujo(tmp):
    return (os.path.join(tmp, "PRODUCTOS", "_ESTADO_FLUJO.csv"),
            os.path.join(tmp, "PRODUCTOS", "_EVENTOS.csv"),
            os.path.join(tmp, "PRODUCTOS", "_FLUJO.json"),
            os.path.join(tmp, "VISTAS", "FLUJO.html"))


def test_flujo_todo_sin_escribir_no_toca_disco():
    tmp = tf.fixture_escalar_flaco()
    _correr_flujo_todo(tmp, [])
    rutas = _rutas_flujo(tmp)
    ok = not any(os.path.exists(r) for r in rutas)
    return _informe(ok, "flujo.py --todo (sin --escribir) no crea _ESTADO_FLUJO.csv/_EVENTOS.csv/"
                         "_FLUJO.json/FLUJO.html", [r for r in rutas if os.path.exists(r)])


def _bootstrap_estado_flujo(prod_dir, tenant):
    """Deja `raw.estado_flujo`/`raw.raw_import` satisfechos para `tenant` -- equivalente a
    `db/cargar.py --tomar-csv estado_flujo` -- a partir de un `_ESTADO_FLUJO.csv` vacío (solo
    header) recién creado en `prod_dir`, para que `verificar_csv_sincronizado()` no aborte por
    "nunca se importó" en la primera escritura real de la prueba. Mismo patrón que
    `test_registrar_evento.py::_bootstrap_evento()`."""
    ruta = os.path.join(prod_dir, "_ESTADO_FLUJO.csv")
    if not os.path.exists(ruta):
        with io.open(ruta, "w", encoding="utf-8", newline="") as fh:
            csv.writer(fh).writerow(flujo.CAMPOS_ESTADO)
    con = _conectar_seguro()
    try:
        with con:
            with con.cursor() as cur:
                n, sha = db_cargar.cargar_tabla(cur, tenant, "estado_flujo", "_ESTADO_FLUJO.csv",
                                                 False, prod_dir)
                cur.execute(
                    "INSERT INTO raw.raw_import (tenant_id, archivo, sha256, filas) "
                    "VALUES (%s, %s, %s, %s)", (tenant, "_ESTADO_FLUJO.csv", sha, n))
                db_nucleo.construir_core(cur, tenant)
    finally:
        con.close()


def test_flujo_todo_con_escribir_si_escribe():
    if not DB_DISPONIBLE:
        print("  SKIP   Postgres/vitalcom_test no disponible en este entorno")
        return 0
    tmp = tf.fixture_escalar_flaco()
    prod_dir = os.path.join(tmp, "PRODUCTOS")
    tenant = _tenant_unico("flujo_estado")
    _bootstrap_estado_flujo(prod_dir, tenant)
    previo_tenant = flujo.TENANT_ID
    flujo.TENANT_ID = tenant
    try:
        rc = _correr_flujo_todo(tmp, ["--escribir"])
    finally:
        flujo.TENANT_ID = previo_tenant
    estado, eventos, flujo_json, html = _rutas_flujo(tmp)
    ok = (rc == 0 and os.path.isfile(estado) and os.path.isfile(flujo_json) and os.path.isfile(html))
    return _informe(ok, "flujo.py --todo --escribir sí persiste _ESTADO_FLUJO.csv/_FLUJO.json/FLUJO.html",
                     (rc, os.path.exists(estado), os.path.exists(flujo_json), os.path.exists(html)))


def test_flujo_reejecutar_lectura_es_idempotente():
    """Correr --todo (sin --escribir) dos veces seguidas no acumula ni cambia nada en disco."""
    tmp = tf.fixture_escalar_flaco()
    _correr_flujo_todo(tmp, [])
    _correr_flujo_todo(tmp, [])
    rutas = _rutas_flujo(tmp)
    ok = not any(os.path.exists(r) for r in rutas)
    return _informe(ok, "correr flujo.py --todo dos veces sin --escribir sigue sin tocar disco",
                     [r for r in rutas if os.path.exists(r)])


# ── decidir.py ───────────────────────────────────────────────────────────────

def _correr_decidir(tmp_json, extra_argv):
    previo_argv, previo_salida = sys.argv, decidir.SALIDA_JSON
    try:
        decidir.SALIDA_JSON = tmp_json
        sys.argv = ["decidir.py", "--json"] + extra_argv
        buf_out, real_stdout = io.StringIO(), sys.stdout
        sys.stdout = buf_out
        try:
            rc = decidir.main()
        finally:
            sys.stdout = real_stdout
        return rc
    finally:
        sys.argv, decidir.SALIDA_JSON = previo_argv, previo_salida


def test_decidir_sin_escribir_no_toca_disco():
    with tempfile.TemporaryDirectory(prefix="decidir_json_") as tmp:
        destino = os.path.join(tmp, "_DECISIONES.json")
        rc = _correr_decidir(destino, [])
        ok = rc == 0 and not os.path.exists(destino)
        return _informe(ok, "decidir.py (sin --escribir) calcula pero no crea _DECISIONES.json",
                         (rc, os.path.exists(destino)))


def _bootstrap_decision(prod_dir, tenant):
    """Deja `raw.decisiones_json`/`raw.raw_import` satisfechos para `tenant` -- equivalente a
    `db/cargar.py --tomar-csv _DECISIONES.json` -- a partir de un `_DECISIONES.json` mínimo (`{}`)
    recién creado en `prod_dir`, para que `verificar_decision_sincronizada()` no aborte por
    "nunca se importó" en la primera escritura real de la prueba."""
    ruta = os.path.join(prod_dir, "_DECISIONES.json")
    if not os.path.exists(ruta):
        with io.open(ruta, "w", encoding="utf-8") as fh:
            json.dump({}, fh, ensure_ascii=False, indent=2)
    con = _conectar_seguro()
    try:
        with con:
            with con.cursor() as cur:
                db_cargar.cargar_decisiones_json(cur, tenant, ruta, incluir_verdad_db=True)
                cur.execute(
                    "INSERT INTO raw.raw_import (tenant_id, archivo, sha256, filas) "
                    "VALUES (%s, %s, %s, %s)", (tenant, "_DECISIONES.json", None, 1))
                db_nucleo.construir_core(cur, tenant)
    finally:
        con.close()


def test_decidir_con_escribir_si_escribe():
    if not DB_DISPONIBLE:
        print("  SKIP   Postgres/vitalcom_test no disponible en este entorno")
        return 0
    with tempfile.TemporaryDirectory(prefix="decidir_json_") as tmp:
        destino = os.path.join(tmp, "_DECISIONES.json")
        tenant = _tenant_unico("decidir")
        _bootstrap_decision(tmp, tenant)
        previo_tenant = decidir.TENANT_ID
        decidir.TENANT_ID = tenant
        try:
            rc = _correr_decidir(destino, ["--escribir"])
        finally:
            decidir.TENANT_ID = previo_tenant
        ok = rc == 0 and os.path.isfile(destino)
        if ok:
            with io.open(destino, encoding="utf-8") as fh:
                ok = isinstance(json.load(fh), dict)
        return _informe(ok, "decidir.py --escribir sí persiste _DECISIONES.json con JSON válido",
                         (rc, os.path.exists(destino)))


def test_decidir_analizar_portafolio_nunca_escribe():
    """flujo.py, perfilar_angulos.py y backtest_politica.py llaman a analizar_portafolio()
    directo, nunca a main(): confirmar que esa función no toca SALIDA_JSON bajo ningún flag."""
    with tempfile.TemporaryDirectory(prefix="decidir_json_") as tmp:
        destino = os.path.join(tmp, "_DECISIONES.json")
        previo = decidir.SALIDA_JSON
        try:
            decidir.SALIDA_JSON = destino
            decidir.analizar_portafolio()
        finally:
            decidir.SALIDA_JSON = previo
        ok = not os.path.exists(destino)
        return _informe(ok, "decidir.analizar_portafolio() es una función pura: nunca escribe SALIDA_JSON",
                         os.path.exists(destino))


# ── gen_grafo.py ─────────────────────────────────────────────────────────────
# gen_grafo.py mide el repo real (os.chdir(BASE) en el import) — no acepta un fixture. Se corre
# sobre el repo tal cual y se restaura la línea base real al terminar, igual que exige la
# verificación de este feature (`gen_grafo.py` + `git checkout` después).

GEN_GRAFO = os.path.join(BASE, "Ads", "_TOOLS", "gen_grafo.py")
LINEA_BASE = os.path.join(BASE, "PRODUCTOS", "_AUDITORIAS", "_LINEA_BASE_SISTEMA.json")


def _correr_gen_grafo(argv):
    return subprocess.run([sys.executable, GEN_GRAFO] + argv, cwd=BASE,
                           capture_output=True, text=True, encoding="utf-8")


def test_gen_grafo_sin_escribir_no_toca_disco():
    existia = os.path.isfile(LINEA_BASE)
    antes = io.open(LINEA_BASE, "rb").read() if existia else None
    try:
        r = _correr_gen_grafo([])
        despues_existe = os.path.isfile(LINEA_BASE)
        despues = io.open(LINEA_BASE, "rb").read() if despues_existe else None
        ok = (r.returncode == 0) and (existia == despues_existe) and (antes == despues)
        return _informe(ok, "gen_grafo.py (sin --escribir) deja _LINEA_BASE_SISTEMA.json "
                             "byte-identico (o ausente)", (r.returncode, existia, despues_existe))
    finally:
        # por si algo escribió a pesar de todo: nunca dejar el repo sucio.
        if existia:
            with io.open(LINEA_BASE, "wb") as fh:
                fh.write(antes)
        elif os.path.isfile(LINEA_BASE):
            os.remove(LINEA_BASE)


def test_gen_grafo_con_escribir_si_escribe():
    existia = os.path.isfile(LINEA_BASE)
    antes = io.open(LINEA_BASE, "rb").read() if existia else None
    try:
        r = _correr_gen_grafo(["--escribir"])
        ok = r.returncode == 0 and os.path.isfile(LINEA_BASE)
        return _informe(ok, "gen_grafo.py --escribir sí persiste _LINEA_BASE_SISTEMA.json",
                         (r.returncode, os.path.isfile(LINEA_BASE)))
    finally:
        if existia:
            with io.open(LINEA_BASE, "wb") as fh:
                fh.write(antes)
        elif os.path.isfile(LINEA_BASE):
            os.remove(LINEA_BASE)


# ── callers: quién SÍ necesita `--escribir` y lo pide ───────────────────────

def _leer(ruta):
    with io.open(ruta, encoding="utf-8") as fh:
        return fh.read()


def test_gen_decisiones_pide_escribir_a_decidir():
    texto = _leer(os.path.join(BASE, "Ads", "_TOOLS", "gen_decisiones.py"))
    ok = bool(re.search(r"decidir\.py\s+--escribir", texto))
    return _informe(ok, "gen_decisiones.py invoca decidir.py con --escribir (cadena nocturna)", texto[:0])


def test_ciclo_hoy_pide_escribir_a_flujo_todo():
    texto = _leer(os.path.join(BASE, "Ads", "_TOOLS", "ciclo_hoy.py"))
    ok = bool(re.search(r"flujo\.py\s+--todo\s+--escribir", texto))
    return _informe(ok, "ciclo_hoy.py invoca flujo.py --todo --escribir (cadena nocturna)", texto[:0])


def test_gen_app_pide_escribir_a_decidir():
    texto = _leer(os.path.join(BASE, "Ads", "_TOOLS", "gen_app.py"))
    ok = '"python %s --escribir" % GEN_DECISIONES' in texto
    return _informe(ok, "gen_app.py (leer_decisiones, refresco perezoso) invoca decidir.py con --escribir", texto[:0])


def test_manifiesto_pide_escribir_para_refrescar_flujo():
    with io.open(os.path.join(BASE, "VISTAS", "_MANIFIESTO.json"), encoding="utf-8") as fh:
        manifiesto = json.load(fh)

    def buscar(o, encontrados):
        if isinstance(o, dict):
            if o.get("genera") == "python Ads/_TOOLS/flujo.py --todo --escribir":
                encontrados.append("genera")
            if o.get("id") == "sistema.refrescar_flujo":
                if o.get("comando", [])[:4] == ["python", "Ads/_TOOLS/flujo.py", "--todo", "--escribir"]:
                    encontrados.append("accion")
            for v in o.values():
                buscar(v, encontrados)
        elif isinstance(o, list):
            for v in o:
                buscar(v, encontrados)

    encontrados = []
    buscar(manifiesto, encontrados)
    ok = "genera" in encontrados and "accion" in encontrados
    return _informe(ok, "VISTAS/_MANIFIESTO.json pide --escribir tanto en 'genera' de la vista "
                         "flujo como en la acción sistema.refrescar_flujo", encontrados)


def test_claude_md_arranque_de_sesion_pide_escribir():
    texto = _leer(os.path.join(BASE, "CLAUDE.md"))
    ok = "python Ads/_TOOLS/flujo.py --todo --escribir" in texto
    return _informe(ok, "CLAUDE.md (arranque de sesión) invoca flujo.py --todo --escribir", texto[:0])


def test_contratos_backend_nunca_pide_escribir():
    """La consulta de lectura de la app (un producto, sin --todo) no debe pedir --escribir:
    ya es solo lectura por default y pedirlo sería pedir un flag que no existe en ese modo.
    Ignora la prosa del docstring (que sí menciona `--todo --escribir` como contraste) y mira
    solo los literales que el código realmente arma como argv."""
    import ast
    archivo = os.path.join(BASE, "app", "backend", "vitalcom_app", "contratos.py")
    arbol = ast.parse(_leer(archivo), filename=archivo)
    docstrings = {
        cuerpo.body[0].value
        for cuerpo in ast.walk(arbol)
        if isinstance(cuerpo, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        and cuerpo.body and isinstance(cuerpo.body[0], ast.Expr)
        and isinstance(cuerpo.body[0].value, ast.Constant)
    }
    literales = {
        nodo.value for nodo in ast.walk(arbol)
        if isinstance(nodo, ast.Constant) and isinstance(nodo.value, str) and nodo not in docstrings
    }
    ok = "--escribir" not in literales and "--sin-escribir" not in literales
    return _informe(ok, "app/backend/vitalcom_app/contratos.py no arma --escribir ni el --sin-escribir retirado",
                     sorted(literales & {"--escribir", "--sin-escribir"}))


def main():
    pruebas = [
        test_flujo_todo_sin_escribir_no_toca_disco,
        test_flujo_todo_con_escribir_si_escribe,
        test_flujo_reejecutar_lectura_es_idempotente,
        test_decidir_sin_escribir_no_toca_disco,
        test_decidir_con_escribir_si_escribe,
        test_decidir_analizar_portafolio_nunca_escribe,
        test_gen_grafo_sin_escribir_no_toca_disco,
        test_gen_grafo_con_escribir_si_escribe,
        test_gen_decisiones_pide_escribir_a_decidir,
        test_ciclo_hoy_pide_escribir_a_flujo_todo,
        test_gen_app_pide_escribir_a_decidir,
        test_manifiesto_pide_escribir_para_refrescar_flujo,
        test_claude_md_arranque_de_sesion_pide_escribir,
        test_contratos_backend_nunca_pide_escribir,
    ]
    fallas = sum(p() for p in pruebas)
    print(f"\n{'0 fallas' if not fallas else str(fallas) + ' falla(s)'}.")
    return 1 if fallas else 0


if __name__ == "__main__":
    sys.exit(main())
