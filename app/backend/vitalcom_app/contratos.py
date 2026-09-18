"""contratos.py — lectura de los contratos del sistema. NO calcula nada.

Regla de oro de la app (hoja de ruta §0.1): la app no calcula, no decide y no escribe CSV.
Todo número que se muestra sale tal cual de un CSV o de un script del motor. Acá no hay
aritmética de negocio: ni CPA, ni break-even, ni márgenes, ni edades de data. Si falta un
dato, se crea el script que lo produce en `Ads/_TOOLS/`, no una cuenta en este archivo.
`tests/test_sin_aritmetica.py` lo verifica sobre el árbol de sintaxis del paquete.
"""

from __future__ import annotations

import csv
import json
import subprocess
from pathlib import Path
from typing import Any

from .config import python_del_sistema, ruta

DIM_PRODUCTOS = ("PRODUCTOS", "_DIM_PRODUCTOS.csv")
DIM_CUENTAS = ("PRODUCTOS", "_DIM_CUENTAS.csv")
ESTADO_FLUJO = ("PRODUCTOS", "_ESTADO_FLUJO.csv")
DECISIONES = ("PRODUCTOS", "_DECISIONES.json")
ESTADO_VISTAS = ("VISTAS", "_ESTADO.json")
FLUJO_PY = ("Ads", "_TOOLS", "flujo.py")
COSTEAR_PY = ("Ads", "_TOOLS", "costear.py")

# Lo que la pantalla necesita de _DIM_PRODUCTOS.csv. El resto de las columnas (notas de
# auditoría, alias de carpetas, tasas) no se sirven: la app muestra, no vuelca el CSV.
COLUMNAS_PRODUCTO = (
    "producto_key",
    "nombre_display",
    "slug_carpeta",
    "estado",
    "fase",
    "cuenta_alias",
    "cuenta_id",
    "moneda",
    "costo_q",
    "precio_base_q",
    "cpa_base_q",
    "cpa_be_q",
    "campaign_id",
)


class ContratoAusente(RuntimeError):
    """Falta un archivo que produce el motor. La app lo dice; no lo inventa ni lo crea."""


def _leer_csv(partes: tuple[str, ...]) -> list[dict[str, str]]:
    archivo = ruta(*partes)
    if not archivo.is_file():
        raise ContratoAusente(f"falta {Path(*partes)}")
    with archivo.open(encoding="utf-8-sig", newline="") as fh:
        return [dict(fila) for fila in csv.DictReader(fh)]


def _leer_json(partes: tuple[str, ...]) -> Any:
    archivo = ruta(*partes)
    if not archivo.is_file():
        raise ContratoAusente(f"falta {Path(*partes)}")
    with archivo.open(encoding="utf-8") as fh:
        return json.load(fh)


def productos() -> list[dict[str, str]]:
    """Las filas de `_DIM_PRODUCTOS.csv`, recortadas a las columnas que la pantalla usa."""
    return [{c: fila.get(c, "") for c in COLUMNAS_PRODUCTO} for fila in _leer_csv(DIM_PRODUCTOS)]


def fila_de_producto(producto_key: str) -> dict[str, str]:
    """La fila COMPLETA de un producto (carpetas incluidas), o {} si no tiene. Solo para el runner y
    las pantallas de FASE 1, que necesitan saber dónde viven sus transcripciones y su media."""
    return next((fila for fila in _leer_csv(DIM_PRODUCTOS) if fila.get("producto_key") == producto_key), {})


def cuentas() -> list[dict[str, str]]:
    """Las cuentas publicitarias de `_DIM_CUENTAS.csv`: alias, moneda y qué permite cada una."""
    columnas = ("cuenta_alias", "cuenta_id", "moneda", "mcp_habilitado", "sube_media_local", "estado_cuenta")
    return [{c: fila.get(c, "") for c in columnas} for fila in _leer_csv(DIM_CUENTAS)]


def estado_flujo() -> dict[str, dict[str, str]]:
    """`_ESTADO_FLUJO.csv` por producto_key: fase y nodo vigentes, derivados por flujo.py.

    La fase que manda es esta, no la columna `fase` de `_DIM_PRODUCTOS.csv`, que quedó como
    bitácora (CLAUDE.md, ARRANQUE DE SESIÓN).
    """
    return {fila["producto_key"]: fila for fila in _leer_csv(ESTADO_FLUJO)}


def decisiones() -> dict[str, Any]:
    """`_DECISIONES.json` tal cual lo dejó `decidir.py`: el único reglamento (invariante 13)."""
    return _leer_json(DECISIONES)


def salud() -> dict[str, Any]:
    """`VISTAS/_ESTADO.json`: qué vista existe, de cuándo es y quién la produce.

    La frescura la calcula `gen_app.py` desde el `mtime` del archivo. La app no la recalcula.
    """
    return _leer_json(ESTADO_VISTAS)


def flujo(producto_key: str, hoy: str | None = None) -> dict[str, Any]:
    """Corre `flujo.py <pk> --json --sin-escribir` y devuelve su salida.

    `--sin-escribir` es obligatorio acá: una consulta de lectura no toca `_ESTADO_FLUJO.csv`
    ni anota un evento. Lo que escribe el estado derivado es `flujo.py --todo`, que corre
    como acción declarada (Hito 3), no como efecto de abrir una pantalla.
    """
    comando = [
        python_del_sistema(),
        str(ruta(*FLUJO_PY)),
        producto_key,
        "--json",
        "--sin-escribir",
        "--silencioso",
    ]
    if hoy:
        comando += ["--hoy", hoy]
    completado = subprocess.run(
        comando,
        cwd=str(ruta()),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
    )
    if completado.returncode != 0 or not completado.stdout.strip():
        detalle = (completado.stderr or completado.stdout or "sin salida").strip()
        raise ContratoAusente(f"flujo.py falló para «{producto_key}»: {detalle[-600:]}")
    return json.loads(completado.stdout)


def costear(costo_q: str) -> dict[str, Any]:
    """Corre `costear.py <costo> --json`: la tabla de precios de Guatemala.

    El costo llega como texto y se pasa como texto: el script valida y decide qué fila de
    `_DIM_COSTEO.csv` corresponde. La app no interpreta ni redondea el número.
    """
    completado = subprocess.run(
        [python_del_sistema(), str(ruta(*COSTEAR_PY)), costo_q, "--json"],
        cwd=str(ruta()), capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=60,
    )
    if completado.returncode != 0 or not completado.stdout.strip():
        detalle = (completado.stderr or completado.stdout or "sin salida").strip()
        raise ContratoAusente(f"costear.py no pudo costear «{costo_q}»: {detalle[-400:]}")
    return json.loads(completado.stdout)
