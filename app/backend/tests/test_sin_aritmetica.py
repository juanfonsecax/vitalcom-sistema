"""El paquete de la app no hace aritmética de negocio.

Criterio de aceptación del Hito 1 y regla de oro de la hoja de ruta: la app no calcula.
Un CPA, un break-even o un margen que nazca acá es una segunda fuente de verdad, y el
sistema entero está construido sobre que hay una sola.

La prueba recorre el árbol de sintaxis del paquete y falla si encuentra una operación
aritmética o una comparación cuyos operandos mencionen un concepto de negocio. Es más
estricta que un grep: `total = precio * 2` no pasa aunque se llame de otra forma, y un
comentario que diga "cpa" no rompe nada.
"""

from __future__ import annotations

import ast
from pathlib import Path

PAQUETE = Path(__file__).resolve().parents[1] / "vitalcom_app"

# Conceptos que solo el motor puede producir (CSV, costear.py, decidir.py, flujo.py).
CONCEPTOS = (
    "cpa", "break", "be_q", "precio", "costo", "margen", "ganancia", "gasto",
    "venta", "roas", "presupuesto", "utilidad", "ingreso", "tasa", "_q",
)
ARITMETICA = (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Pow, ast.Mod)


def _menciona_concepto(nodo: ast.AST) -> str | None:
    for hijo in ast.walk(nodo):
        texto = ""
        if isinstance(hijo, ast.Name):
            texto = hijo.id
        elif isinstance(hijo, ast.Attribute):
            texto = hijo.attr
        elif isinstance(hijo, ast.Constant) and isinstance(hijo.value, str):
            texto = hijo.value
        bajo = texto.lower()
        for concepto in CONCEPTOS:
            if concepto in bajo:
                return texto
    return None


def test_ningun_calculo_de_negocio_en_el_paquete():
    hallazgos: list[str] = []
    for archivo in sorted(PAQUETE.rglob("*.py")):
        arbol = ast.parse(archivo.read_text(encoding="utf-8"), filename=str(archivo))
        for nodo in ast.walk(arbol):
            if isinstance(nodo, (ast.BinOp, ast.AugAssign)) and isinstance(nodo.op, ARITMETICA):
                culpable = _menciona_concepto(nodo)
                if culpable:
                    hallazgos.append(f"{archivo.name}:{nodo.lineno} aritmética sobre «{culpable}»")
            if isinstance(nodo, ast.Compare) and any(
                isinstance(op, (ast.Lt, ast.LtE, ast.Gt, ast.GtE)) for op in nodo.ops
            ):
                culpable = _menciona_concepto(nodo)
                if culpable:
                    hallazgos.append(f"{archivo.name}:{nodo.lineno} umbral sobre «{culpable}»")
    assert not hallazgos, "la app no decide ni calcula:\n  " + "\n  ".join(hallazgos)


def test_la_app_no_escribe_en_el_sistema():
    """Hito 1 es de solo lectura: ni `open(..., 'w')`, ni escritores CSV, ni mkdir."""
    prohibido = ("csv.writer", "csv.DictWriter", "json.dump", "shutil.copy", "os.remove")
    hallazgos: list[str] = []
    for archivo in sorted(PAQUETE.rglob("*.py")):
        codigo = archivo.read_text(encoding="utf-8")
        arbol = ast.parse(codigo, filename=str(archivo))
        for nodo in ast.walk(arbol):
            if isinstance(nodo, ast.Call):
                llamada = ast.unparse(nodo.func)
                if llamada in prohibido or llamada.endswith((".write_text", ".mkdir", ".unlink")):
                    hallazgos.append(f"{archivo.name}:{nodo.lineno} {llamada}")
                if llamada in ("open", "Path.open") or llamada.endswith(".open"):
                    modos = [
                        a.value for a in list(nodo.args) + [k.value for k in nodo.keywords]
                        if isinstance(a, ast.Constant) and isinstance(a.value, str)
                    ]
                    if any(m for m in modos if set("wax+") & set(m)):
                        hallazgos.append(f"{archivo.name}:{nodo.lineno} open en modo escritura")
    assert not hallazgos, "el Hito 1 no escribe nada:\n  " + "\n  ".join(hallazgos)


def _banderas_en_codigo(archivo: Path) -> set[str]:
    """Las banderas que el código realmente pasa, sin contar las que nombra la prosa."""
    arbol = ast.parse(archivo.read_text(encoding="utf-8"), filename=str(archivo))
    docstrings = {
        cuerpo.body[0].value
        for cuerpo in ast.walk(arbol)
        if isinstance(cuerpo, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        and cuerpo.body
        and isinstance(cuerpo.body[0], ast.Expr)
        and isinstance(cuerpo.body[0].value, ast.Constant)
    }
    return {
        nodo.value
        for nodo in ast.walk(arbol)
        if isinstance(nodo, ast.Constant)
        and isinstance(nodo.value, str)
        and nodo.value.startswith("--")
        and nodo not in docstrings
    }


def test_flujo_se_invoca_siempre_sin_escribir():
    """`flujo.py` sin `--sin-escribir` tocaría `_ESTADO_FLUJO.csv` al abrir una pantalla."""
    banderas = _banderas_en_codigo(PAQUETE / "contratos.py")
    assert "--sin-escribir" in banderas
    assert "--todo" not in banderas, "`--todo` escribe: es acción del Hito 3, no una lectura"
