#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_evals_baseline.py — GATE de la baseline de evals (T11, odd/tasks/g07-cimientos.md).

Dos cosas, nunca una sola: (1) que la baseline completa siga en verde sobre los
outputs reales congelados (`evals/run_baseline.py` sale 0), y (2) que los
asserts no sean vacíos — se muta un fixture de verdad y se confirma que el
assert correspondiente SÍ lo detecta y falla. Sin (2), un assert que siempre
devuelve pass=True pasaría esta gate igual que uno real.

USO:  python Ads/_TOOLS/test_evals_baseline.py     (exit 0 = pasa, 1 = falla)
"""
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile

HERRAMIENTAS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(HERRAMIENTAS_DIR, "..", ".."))
EVALS_DIR = os.path.join(REPO_ROOT, "evals")


def _informe(ok, texto, detalle=""):
    print(("  OK     " if ok else "  FALLA  ") + texto + ("" if ok else "\n         %r" % (detalle,)))
    return 0 if ok else 1


def _importar_assert(nombre_archivo):
    ruta = os.path.join(EVALS_DIR, "asserts", nombre_archivo)
    asserts_dir = os.path.dirname(ruta)
    if asserts_dir not in sys.path:
        sys.path.insert(0, asserts_dir)
    spec = importlib.util.spec_from_file_location(nombre_archivo.replace(".py", "").replace("-", "_"), ruta)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_baseline_pasa_sobre_los_outputs_reales():
    """`run_baseline.py` sobre la config real debe salir 0: ningún test NO
    marcado `expected_fail` puede estar en rojo — ese es el piso que protege
    la poda de prosa de ETAPA-*.md (T11 es la razón de existir de esta gate)."""
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    proc = subprocess.run(
        [sys.executable, os.path.join(EVALS_DIR, "run_baseline.py")],
        cwd=EVALS_DIR, env=env, capture_output=True, text=True,
        encoding="utf-8", errors="replace",
    )
    ok = proc.returncode == 0
    return _informe(ok, "run_baseline.py sobre promptfooconfig.yaml sale 0 (sin FAIL reales)",
                     (proc.returncode, proc.stdout[-800:], proc.stderr[-800:]))


def test_assert_etapa6_schema_detecta_un_plan_json_roto():
    """Muta un `_PLAN.json` real (le vacía el angulo_key del primer conjunto) y
    confirma que `etapa-6_schema.py` lo rechaza — si esto pasara en verde, el
    assert sería un sello de goma."""
    mod = _importar_assert("etapa-6_schema.py")
    ruta_fixture = os.path.join(EVALS_DIR, "fixtures", "etapa-6", "CLEARSTEM.json")
    with io.open(ruta_fixture, "r", encoding="utf-8") as fh:
        plan = json.load(fh)
    plan["conjuntos"][0]["angulo_key"] = ""
    mutado = json.dumps(plan, ensure_ascii=False)

    original_ok = mod.get_assert(io.open(ruta_fixture, encoding="utf-8").read(), {})["pass"]
    mutado_ok = mod.get_assert(mutado, {})["pass"]
    ok = original_ok and not mutado_ok
    return _informe(ok, "etapa-6_schema.py: fixture real pasa, la misma copia con angulo_key vacío falla",
                     (original_ok, mutado_ok))


def test_assert_etapa6_formato_imagen_detecta_video_en_fase1():
    """Confirma en sentido inverso: el fixture ya-en-IMAGEN (OVULOS_PURITY)
    pasa, y una copia mutada con un conjunto puesto en VIDEO dentro de la
    misma FASE 1 falla — la regla "todo en imagen" del 22-sep-2026 es real
    para el assert, no solo un texto suelto."""
    mod = _importar_assert("etapa-6_formato_imagen.py")
    ruta_fixture = os.path.join(EVALS_DIR, "fixtures", "etapa-6", "OVULOS_PURITY.json")
    with io.open(ruta_fixture, "r", encoding="utf-8") as fh:
        original = fh.read()
    plan = json.loads(original)
    plan["conjuntos"][0]["formato"] = "VIDEO"
    mutado = json.dumps(plan, ensure_ascii=False)

    original_ok = mod.get_assert(original, {})["pass"]
    mutado_ok = mod.get_assert(mutado, {})["pass"]
    ok = original_ok and not mutado_ok
    return _informe(ok, "etapa-6_formato_imagen.py: OVULOS_PURITY (todo IMAGEN) pasa, un VIDEO inyectado en FASE 1 falla",
                     (original_ok, mutado_ok))


def test_assert_etapa_producto_detecta_veredicto_borrado():
    """El fixture real de OVULOS_PURITY trae veredicto+score; una copia sin
    esa línea debe fallar — nunca "no hay evidencia de que no haya evidencia"."""
    mod = _importar_assert("etapa-producto.py")
    ruta_fixture = os.path.join(EVALS_DIR, "fixtures", "etapa-producto", "OVULOS_PURITY.txt")
    with io.open(ruta_fixture, "r", encoding="utf-8") as fh:
        original = fh.read()
    mutado = "\n".join(l for l in original.splitlines() if "VALIDACION_PRODUCTO" not in l)

    original_ok = mod.get_assert(original, {})["pass"]
    mutado_ok = mod.get_assert(mutado, {})["pass"]
    ok = original_ok and not mutado_ok
    return _informe(ok, "etapa-producto.py: fixture real pasa, sin la línea de veredicto falla",
                     (original_ok, mutado_ok))


def test_assert_etapa_guardar_producto_detecta_archivo_suelto_de_rerun():
    """Invariante 8: 'prohibidos archivos sueltos de reruns'. Un manifiesto
    real más un archivo tipo '... - Copia.txt' debe rechazarse."""
    mod = _importar_assert("etapa-guardar-producto.py")
    ruta_fixture = os.path.join(EVALS_DIR, "fixtures", "etapa-guardar-producto", "CLEARSTEM.json")
    with io.open(ruta_fixture, "r", encoding="utf-8") as fh:
        original = fh.read()
    manifiesto = json.loads(original)
    manifiesto["archivos"].append("2_DATA_PRODUCTO - Copia.txt")
    mutado = json.dumps(manifiesto, ensure_ascii=False)

    original_ok = mod.get_assert(original, {})["pass"]
    mutado_ok = mod.get_assert(mutado, {})["pass"]
    ok = original_ok and not mutado_ok
    return _informe(ok, "etapa-guardar-producto.py: manifiesto real pasa, con un '- Copia' suelto falla",
                     (original_ok, mutado_ok))


def main():
    with tempfile.TemporaryDirectory():  # asserts no deben escribir nada; entorno aislado por si acaso
        pruebas = [
            test_baseline_pasa_sobre_los_outputs_reales,
            test_assert_etapa6_schema_detecta_un_plan_json_roto,
            test_assert_etapa6_formato_imagen_detecta_video_en_fase1,
            test_assert_etapa_producto_detecta_veredicto_borrado,
            test_assert_etapa_guardar_producto_detecta_archivo_suelto_de_rerun,
        ]
        fallas = sum(p() for p in pruebas)
    print(f"\n{'0 fallas' if not fallas else str(fallas) + ' falla(s)'}.")
    return 1 if fallas else 0


if __name__ == "__main__":
    sys.exit(main())
