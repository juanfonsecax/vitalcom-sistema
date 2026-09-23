#!/usr/bin/env python3
"""Runner puro-Python de la baseline de evals (T11).

No depende de que promptfoo esté instalado: lee el mismo
`promptfooconfig.yaml` que un `npx promptfoo eval` real consumiría (el
provider `echo` + prompt `"{{content}}"` + asserts `type: python` con
`value: file://...` es exactamente el shape que promptfoo espera), resuelve
cada `vars.content` como el contenido del fixture, importa el módulo de
assert señalado y llama a `get_assert(output, context)` con la misma firma
que usaría promptfoo. Así este runner y una corrida real de promptfoo miden
lo mismo.

Salida: tabla con PASS/FAIL/FALLO-CONOCIDO por test, y exit code != 0 si
algún test NO marcado como `expected_fail` falla.
"""
from __future__ import annotations

import importlib.util
import os
import sys

import yaml  # PyYAML: ya es dependencia transitiva de dbt-core (requirements.txt) en este repo.

EVALS_DIR = os.path.dirname(os.path.abspath(__file__))

# La consola de Windows (cp1252) no puede imprimir tildes/emojis de los
# fixtures reales sin esto — reconfigurar en vez de fallar a mitad de tabla.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def _cargar_config(ruta: str) -> dict:
    with open(ruta, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def _resolver_file_uri(valor: str) -> str:
    if valor.startswith("file://"):
        return os.path.join(EVALS_DIR, valor[len("file://"):])
    return valor


def _leer_texto(ruta: str) -> str:
    with open(ruta, "r", encoding="utf-8") as fh:
        return fh.read()


def _importar_assert(ruta_py: str):
    """Importa un módulo de assert por ruta, dejando `evals/asserts/` en
    sys.path para que `from _util import ...` funcione igual que dentro de
    promptfoo (que ejecuta el archivo standalone)."""
    asserts_dir = os.path.dirname(ruta_py)
    if asserts_dir not in sys.path:
        sys.path.insert(0, asserts_dir)
    nombre_mod = os.path.splitext(os.path.basename(ruta_py))[0].replace("-", "_")
    spec = importlib.util.spec_from_file_location(nombre_mod, ruta_py)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


def ejecutar(ruta_config: str) -> int:
    config = _cargar_config(ruta_config)
    tests = config.get("tests", [])
    if not tests:
        print("SIN TESTS en la config — nada que correr.")
        return 1

    filas = []
    fallos_reales = 0
    fallos_conocidos_que_ahora_pasan = []

    for test in tests:
        desc = test.get("description", "(sin descripción)")
        meta = test.get("metadata", {}) or {}
        esperado_fail = bool(meta.get("expected_fail", False))
        razon_conocida = meta.get("reason", "")

        content_var = (test.get("vars") or {}).get("content", "")
        fixture_path = _resolver_file_uri(content_var)
        try:
            output = _leer_texto(fixture_path)
        except OSError as exc:
            filas.append((desc, "ERROR", f"no se pudo leer el fixture: {exc}"))
            fallos_reales += 1
            continue

        asserts = test.get("assert", [])
        ok_total = True
        razon_total = []
        for a in asserts:
            if a.get("type") != "python":
                continue
            ruta_assert = _resolver_file_uri(a["value"])
            mod = _importar_assert(ruta_assert)
            context = {"vars": test.get("vars", {}), "test": test}
            resultado = mod.get_assert(output, context)
            if isinstance(resultado, dict):
                ok = bool(resultado.get("pass"))
                razon_total.append(str(resultado.get("reason", "")))
            else:
                ok = bool(resultado)
            ok_total = ok_total and ok

        if ok_total:
            estado = "FALLO-CONOCIDO-AHORA-PASA" if esperado_fail else "PASS"
            if esperado_fail:
                fallos_conocidos_que_ahora_pasan.append(desc)
        else:
            if esperado_fail:
                estado = "FALLO-CONOCIDO"
            else:
                estado = "FAIL"
                fallos_reales += 1

        razon = " / ".join(r for r in razon_total if r) or razon_conocida
        filas.append((desc, estado, razon))

    ancho_desc = max(len(f[0]) for f in filas)
    print(f"{'TEST'.ljust(ancho_desc)}  ESTADO                      RAZÓN")
    print("-" * (ancho_desc + 90))
    for desc, estado, razon in filas:
        print(f"{desc.ljust(ancho_desc)}  {estado.ljust(26)}  {razon}")

    total = len(filas)
    passed = sum(1 for _, e, _ in filas if e == "PASS")
    fallos_conocidos = sum(1 for _, e, _ in filas if e == "FALLO-CONOCIDO")
    print("-" * (ancho_desc + 90))
    print(f"TOTAL={total}  PASS={passed}  FALLO-CONOCIDO(documentado)={fallos_conocidos}  FAIL={fallos_reales}")

    if fallos_conocidos_que_ahora_pasan:
        print()
        print("NOTA — estos tests estaban marcados expected_fail pero ahora PASAN:")
        for d in fallos_conocidos_que_ahora_pasan:
            print(f"  - {d}")
        print("  (buena noticia: alguien corrigió el fallo. Quitar su 'expected_fail' de promptfooconfig.yaml.)")

    return 1 if fallos_reales else 0


if __name__ == "__main__":
    ruta = sys.argv[1] if len(sys.argv) > 1 else os.path.join(EVALS_DIR, "promptfooconfig.yaml")
    sys.exit(ejecutar(ruta))
