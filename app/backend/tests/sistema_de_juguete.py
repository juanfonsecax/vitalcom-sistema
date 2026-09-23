"""Un sistema de mentira para probar el runner sin tocar el sistema real ni Meta.

Es una carpeta temporal con:
  * el `DOCTRINA/FLUJO.json` y el `VISTAS/_MANIFIESTO.json` REALES de este repositorio (la
    prueba ejercita el contrato de verdad, no uno inventado);
  * el `gen_app.py` real (es quien valida el manifiesto);
  * un script falso por cada `Ads/_TOOLS/*.py` que el manifiesto cita, que solo anota que lo
    llamaron y responde `{"ok": true}`. Cada prueba reemplaza el que necesite con
    `escribir_script`.
Ninguna prueba llama al Claude real ni a Meta.
"""

from __future__ import annotations

import csv
import json
import shutil
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[3]

STUB = '''import json, pathlib, sys
BASE = pathlib.Path(__file__).resolve().parents[2]
with open(BASE / "PRODUCTOS" / "_llamadas.log", "a", encoding="utf-8") as archivo:
    archivo.write(json.dumps({"script": pathlib.Path(__file__).name, "argv": sys.argv[1:]}) + "\\n")
if "--json" in sys.argv:
    print(json.dumps({"ok": True}))
'''

# `flujo.py` falso: dice lo que la prueba declaró en PRODUCTOS/_flujo_falso.json.
FLUJO_FALSO = '''import json, pathlib, sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
BASE = pathlib.Path(__file__).resolve().parents[2]
with open(BASE / "PRODUCTOS" / "_llamadas.log", "a", encoding="utf-8") as archivo:
    archivo.write(json.dumps({"script": "flujo.py", "argv": sys.argv[1:]}) + "\\n")
declarado = json.loads((BASE / "PRODUCTOS" / "_flujo_falso.json").read_text(encoding="utf-8"))
if "--todo" in sys.argv or "--validar" in sys.argv:
    sys.exit(0)
producto = next(a for a in sys.argv[1:] if not a.startswith("--"))
print(json.dumps(declarado.get(producto) or declarado["*"]))
'''

# `gen_app.py` del juguete: valida el manifiesto con el REAL (renombrado `gen_app_real.py`) y, para
# cualquier otra cosa (lo que corre `tras_escribir`), solo anota que lo llamaron.
GEN_APP_ENVOLTORIO = '''import pathlib, runpy, sys
AQUI = pathlib.Path(__file__).resolve().parent
if "--validar-manifiesto" in sys.argv:
    runpy.run_path(str(AQUI / "gen_app_real.py"), run_name="__main__")
else:
    import json
    with open(AQUI.parents[1] / "PRODUCTOS" / "_llamadas.log", "a", encoding="utf-8") as archivo:
        archivo.write(json.dumps({"script": "gen_app.py", "argv": sys.argv[1:]}) + "\\n")
'''

COLUMNAS_PRODUCTOS = [
    "producto_key", "nombre_display", "slug_carpeta", "estado", "fase", "cuenta_alias",
    "cuenta_id", "moneda", "costo_q", "precio_base_q", "cpa_base_q", "cpa_be_q", "campaign_id",
]
COLUMNAS_CUENTAS = ["cuenta_alias", "cuenta_id", "moneda", "mcp_habilitado", "sube_media_local",
                    "estado_cuenta"]


def manifiesto_real() -> dict[str, Any]:
    return json.loads((REPO / "VISTAS" / "_MANIFIESTO.json").read_text(encoding="utf-8"))


def flujo_real() -> dict[str, Any]:
    return json.loads((REPO / "DOCTRINA" / "FLUJO.json").read_text(encoding="utf-8"))


def escribir_manifiesto(base: Path, manifiesto: dict[str, Any]) -> None:
    destino = base / "VISTAS" / "_MANIFIESTO.json"
    destino.write_text(json.dumps(manifiesto, ensure_ascii=False, indent=1), encoding="utf-8")


def escribir_flujo(base: Path, flujo: dict[str, Any]) -> None:
    destino = base / "DOCTRINA" / "FLUJO.json"
    destino.write_text(json.dumps(flujo, ensure_ascii=False, indent=1), encoding="utf-8")


def escribir_script(base: Path, nombre: str, codigo: str) -> None:
    (base / "Ads" / "_TOOLS" / nombre).write_text(codigo, encoding="utf-8")


def escribir_flujo_falso(base: Path, declarado: dict[str, Any]) -> None:
    (base / "PRODUCTOS" / "_flujo_falso.json").write_text(json.dumps(declarado), encoding="utf-8")


def flujo_listo(nodo_actual: str, estado: str = "LISTO_PARA_EJECUTAR", cumplido: bool = False,
                falta: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Lo que `flujo.py` diría de un producto cuyo nodo actual es `nodo_actual`."""
    return {"producto_key": "TINNIDROP", "nodo_actual": nodo_actual, "estado": estado,
            "ejecutor": "subagente `etapa-fake` (Task, subagent_type=etapa-fake)",
            "bloqueantes": [], "falta_para_cumplir": falta or [],
            "nodos": [{"id": nodo_actual, "estado": "CUMPLIDO" if cumplido else estado, "cumplido": cumplido}]}


def llamadas(base: Path) -> list[dict[str, Any]]:
    archivo = base / "PRODUCTOS" / "_llamadas.log"
    if not archivo.is_file():
        return []
    return [json.loads(linea) for linea in archivo.read_text(encoding="utf-8").splitlines() if linea]


def _csv(destino: Path, columnas: list[str], filas: list[dict[str, str]]) -> None:
    with open(destino, "w", encoding="utf-8", newline="") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=columnas)
        escritor.writeheader()
        escritor.writerows(filas)


def crear(destino: Path, manifiesto: dict[str, Any] | None = None, flujo: dict[str, Any] | None = None) -> Path:
    """`flujo` reemplaza el `DOCTRINA/FLUJO.json` real (p. ej. para una prueba que necesita su
    propio `FLUJO.json`, autoconsistente con un `manifiesto` propio — V20 exige que coincidan)."""
    for carpeta in ("DOCTRINA", "VISTAS", "PRODUCTOS", "Ads/_TOOLS", "PRODUCTOS/_AUDITORIAS"):
        (destino / carpeta).mkdir(parents=True, exist_ok=True)
    if flujo is not None:
        escribir_flujo(destino, flujo)
    else:
        shutil.copy2(REPO / "DOCTRINA" / "FLUJO.json", destino / "DOCTRINA" / "FLUJO.json")
    shutil.copy2(REPO / "Ads" / "_TOOLS" / "gen_app.py", destino / "Ads" / "_TOOLS" / "gen_app_real.py")
    escribir_script(destino, "gen_app.py", GEN_APP_ENVOLTORIO)

    # Los agentes (V20 valida que cada paso sea uno) y los pasos que no son .py (el lavado).
    shutil.copytree(REPO / ".claude" / "agents", destino / ".claude" / "agents")
    manifiesto = manifiesto if manifiesto is not None else manifiesto_real()
    escribir_manifiesto(destino, manifiesto)
    for accion in (manifiesto.get("acciones") or {}).get("lista", []):
        for paso in (e for grupo in accion.get("pasos") or [] for e in grupo if "/" in e):
            (destino / paso).parent.mkdir(parents=True, exist_ok=True)
            (destino / paso).write_text("# paso falso del juguete\n", encoding="utf-8")

    scripts = {"flujo.py"}
    for accion in (manifiesto.get("acciones") or {}).get("lista", []):
        comando = accion.get("comando")
        if comando and len(comando) > 1:
            scripts.add(Path(comando[1]).name)
    for nombre in scripts:
        if nombre != "gen_app.py" and not (destino / "Ads" / "_TOOLS" / nombre).exists():
            escribir_script(destino, nombre, FLUJO_FALSO if nombre == "flujo.py" else STUB)
    escribir_flujo_falso(destino, {"*": flujo_listo("F2.etapa-11")})

    _csv(destino / "PRODUCTOS" / "_DIM_PRODUCTOS.csv", COLUMNAS_PRODUCTOS, [
        {"producto_key": "TINNIDROP", "nombre_display": "Tinnidrop", "estado": "VIVO"},
        {"producto_key": "NUSAVA", "nombre_display": "Nusava", "estado": "VIVO"},
    ])
    _csv(destino / "PRODUCTOS" / "_DIM_CUENTAS.csv", COLUMNAS_CUENTAS, [
        {"cuenta_alias": "GTR 7", "moneda": "USD", "mcp_habilitado": "SI", "sube_media_local": "SI"},
        {"cuenta_alias": "GTR 13", "moneda": "USD", "mcp_habilitado": "NO", "sube_media_local": "NO"},
    ])
    _csv(destino / "PRODUCTOS" / "_ESTADO_FLUJO.csv", ["producto_key", "fase", "nodo_actual", "estado"], [])
    return destino
