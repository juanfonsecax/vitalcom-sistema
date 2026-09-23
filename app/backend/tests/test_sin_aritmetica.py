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
    """La app ejecuta al que escribe; no escribe ella.

    Ningún módulo abre un archivo para escribir, ni usa un escritor CSV, ni crea carpetas.
    Quien toca el sistema es siempre un script de `Ads/_TOOLS/` con su propio test.
    La única excepción es `subidas.py`, que guarda lo que el operador arrastra a la pantalla
    dentro de una carpeta temporal del sistema operativo; el test de abajo la acota.
    """
    prohibido = ("csv.writer", "csv.DictWriter", "json.dump", "shutil.copy", "os.remove")
    hallazgos: list[str] = []
    for archivo in sorted(PAQUETE.rglob("*.py")):
        # `subidas.py` escribe en el temporal, `escrituras.py` maneja el candado de la cola
        # (también en el temporal) y `bitacora.py` escribe SOLO bajo `app_runs/`. Cada uno
        # tiene su prueba estructural.
        if archivo.name in ("subidas.py", "escrituras.py", "bitacora.py"):
            continue
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


def test_las_subidas_solo_tocan_el_temporal():
    """`subidas.py` escribe, pero nunca dentro del sistema.

    Se verifica estructuralmente: usa `tempfile` y no sabe dónde vive el sistema, porque no
    importa `config`. Así, una subida no puede escribir en `PRODUCTOS/` ni en `Ads/` aunque
    alguien se equivoque más adelante.
    """
    archivo = PAQUETE / "subidas.py"
    arbol = ast.parse(archivo.read_text(encoding="utf-8"), filename=str(archivo))
    importados = {
        (nodo.module or "") if isinstance(nodo, ast.ImportFrom) else alias.name
        for nodo in ast.walk(arbol)
        if isinstance(nodo, (ast.Import, ast.ImportFrom))
        for alias in nodo.names
    }
    assert "tempfile" in importados, "las subidas van a una carpeta temporal"
    assert not any("config" in nombre for nombre in importados), (
        "subidas.py no puede conocer la carpeta del sistema: si no la conoce, no la escribe"
    )


# Los scripts que se corren y el turno de escritura se prueban en `test_workflows.py`:
# ningún literal `.py` en el runner (todo argv sale del manifiesto) y cada unidad que escribe
# toma `Cola()`.


def test_escrituras_solo_escribe_su_candado_en_el_temporal():
    """`escrituras.py` no toca archivos del sistema: lo único que abre es el lock de la cola.

    Se verifica que toda llamada de escritura viva dentro de la clase `Cola` y que el
    candado salga de `tempfile.gettempdir()`. Los cambios reales los hacen los scripts.
    """
    archivo = PAQUETE / "escrituras.py"
    codigo = archivo.read_text(encoding="utf-8")
    arbol = ast.parse(codigo, filename=str(archivo))
    assert "tempfile.gettempdir()" in codigo, "el candado vive en el temporal, no en el repo"

    cola = next(n for n in ast.walk(arbol) if isinstance(n, ast.ClassDef) and n.name == "Cola")
    lock = next(
        n for n in ast.walk(arbol)
        if isinstance(n, ast.FunctionDef) and n.name == "_archivo_de_lock"
    )
    permitidas = {id(n) for zona in (cola, lock) for n in ast.walk(zona)}
    escrituras = ("os.open", "os.write", "os.close")
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Call):
            llamada = ast.unparse(nodo.func)
            if llamada in escrituras or llamada.endswith((".unlink", ".write_text", ".mkdir")):
                assert id(nodo) in permitidas, (
                    f"escrituras.py:{nodo.lineno} escribe «{llamada}» fuera del candado de la cola"
                )


def test_flujo_se_invoca_siempre_sin_escribir():
    """`flujo.py` sin `--todo`/`--escribir` (T6: contrato de CLI) no toca `_ESTADO_FLUJO.csv`."""
    banderas = _banderas_en_codigo(PAQUETE / "contratos.py")
    assert "--todo" not in banderas, "`--todo` es acción del Hito 3, no una lectura de pantalla"
    assert "--escribir" not in banderas, "una consulta de lectura nunca pide el flag de escritura"
