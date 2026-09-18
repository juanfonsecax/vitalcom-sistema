"""config.py — dónde vive el sistema que la app mira.

La app corre SOBRE la carpeta real (`SISTEMA/`), no sobre el worktree donde se desarrolla:
las `Ads/MEDIA_*` están en .gitignore y un worktree da estados falsos (el 17-sep-2026
OVULOS_PURITY apareció BLOQUEADO en worktree y LISTO en la carpeta real).

La base se resuelve así, en orden:
  1. La variable de entorno `VITALCOM_BASE`.
  2. Subiendo desde este archivo hasta encontrar una carpeta con `DOCTRINA/FLUJO.json`.
  3. Subiendo igual desde el directorio de trabajo.
Si ninguna da, se levanta un error con el nombre de la variable: la app no adivina.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

MARCA = Path("DOCTRINA") / "FLUJO.json"


def _es_base(ruta: Path) -> bool:
    return (ruta / MARCA).is_file()


def _subiendo(desde: Path) -> Path | None:
    for candidata in [desde, *desde.parents]:
        if _es_base(candidata):
            return candidata
    return None


@lru_cache(maxsize=1)
def base() -> Path:
    declarada = os.environ.get("VITALCOM_BASE")
    if declarada:
        ruta = Path(declarada).expanduser().resolve()
        if not _es_base(ruta):
            raise RuntimeError(
                f"VITALCOM_BASE apunta a «{ruta}», que no tiene {MARCA}. "
                "Es la carpeta del sistema, la que contiene DOCTRINA/, PRODUCTOS/ y Ads/."
            )
        return ruta

    for punto_de_partida in (Path(__file__).resolve().parent, Path.cwd().resolve()):
        encontrada = _subiendo(punto_de_partida)
        if encontrada is not None:
            return encontrada

    raise RuntimeError(
        "No encuentro la carpeta del sistema (la que tiene DOCTRINA/FLUJO.json). "
        "Declarala en la variable de entorno VITALCOM_BASE."
    )


def ruta(*partes: str) -> Path:
    """Una ruta dentro del sistema. Sirve para leer; la app no escribe acá."""
    return base().joinpath(*partes)


def python_del_sistema() -> str:
    """Con qué intérprete se corren los scripts de `Ads/_TOOLS/`.

    Los scripts del motor son del sistema, no de la app: corren con el Python del sistema,
    no con el venv de la app, salvo que se declare `VITALCOM_PYTHON`.
    """
    return os.environ.get("VITALCOM_PYTHON") or "python"


def datos_de_la_app() -> Path:
    """Dónde guarda la app su propia base de datos (DBOS). Fuera del sistema y del repo.

    `VITALCOM_DATOS`, o `%LOCALAPPDATA%/VitalCom` en Windows (`~/.local/share/vitalcom` en el
    resto). Se crea al pedirla. Nunca queda dentro de la carpeta del sistema: son datos de la
    app, no del negocio.
    """
    declarada = os.environ.get("VITALCOM_DATOS")
    if declarada:
        carpeta = Path(declarada).expanduser().resolve()
    elif os.environ.get("LOCALAPPDATA"):
        carpeta = Path(os.environ["LOCALAPPDATA"]) / "VitalCom"
    else:
        carpeta = Path.home() / ".local" / "share" / "vitalcom"
    if carpeta.is_relative_to(base()):
        raise RuntimeError(f"La base de datos de la app no puede vivir dentro del sistema ({carpeta}).")
    os.makedirs(carpeta, exist_ok=True)
    return carpeta
