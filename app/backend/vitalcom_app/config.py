"""config.py — dónde vive el sistema que la app mira.

La app corre SOBRE la carpeta real (`SISTEMA/`), no sobre el worktree donde se desarrolla:
las `Ads/MEDIA_*` están en .gitignore y un worktree da estados falsos (el 17-sep-2026
OVULOS_PURITY apareció BLOQUEADO en worktree y LISTO en la carpeta real).

La base se resuelve así, en orden:
  1. La variable de entorno `VITALCOM_BASE` (override explícito: si el operador la declaró
     a mano, se respeta tal cual — igual que la salida de escape de `iniciar.bat`).
  2. Subiendo desde este archivo hasta encontrar una carpeta con `DOCTRINA/FLUJO.json`.
  3. Subiendo igual desde el directorio de trabajo.
Si ninguna da, se levanta un error con el nombre de la variable: la app no adivina.

BASE AMBIGUA (T8, 23-sep-2026): `DOCTRINA/FLUJO.json` está versionado, así que CUALQUIER
worktree vinculado de git (ej. `SISTEMA-app`, donde se desarrolla) también lo tiene — el
candidato de los pasos 2/3 puede terminar siendo ese worktree en vez de la carpeta PRINCIPAL
dueña de `PRODUCTOS/` y `Ads/MEDIA_*` reales. La detección automática por eso NUNCA acepta un
candidato que sea un worktree vinculado: si lo encuentra, se niega con un error que nombra la
carpeta principal (misma regla que `iniciar.bat`). El paso 1 (`VITALCOM_BASE` explícito) es la
única forma de apuntar a propósito a un worktree.
"""

from __future__ import annotations

import os
import subprocess
from functools import lru_cache
from pathlib import Path

MARCA = Path("DOCTRINA") / "FLUJO.json"


def _es_base(ruta: Path) -> bool:
    return (ruta / MARCA).is_file()


def _git_rev_parse(ruta: Path, *args: str) -> str | None:
    try:
        r = subprocess.run(
            ["git", "-C", str(ruta), "rev-parse", "--path-format=absolute", *args],
            capture_output=True, text=True, timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if r.returncode != 0:
        return None
    return r.stdout.strip() or None


def _worktree_principal(ruta: Path) -> str | None:
    """Primera entrada de `git worktree list --porcelain`: la carpeta principal del repo."""
    try:
        r = subprocess.run(
            ["git", "-C", str(ruta), "worktree", "list", "--porcelain"],
            capture_output=True, text=True, timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if r.returncode != 0:
        return None
    for linea in r.stdout.splitlines():
        if linea.startswith("worktree "):
            return linea[len("worktree "):].strip()
    return None


def _es_worktree_vinculado(ruta: Path) -> tuple[bool, str | None]:
    """True si `ruta` es un worktree vinculado (git-dir != git-common-dir), con la carpeta
    principal cuando se puede derivar. Si no hay git o no aplica, (False, None) — nunca bloquea
    una carpeta que simplemente no tiene git."""
    git_dir = _git_rev_parse(ruta, "--git-dir")
    if git_dir is None:
        return False, None
    git_comun = _git_rev_parse(ruta, "--git-common-dir")
    if git_comun is None or git_dir == git_comun:
        return False, None
    return True, _worktree_principal(ruta)


def _subiendo(desde: Path) -> Path | None:
    for candidata in [desde, *desde.parents]:
        if _es_base(candidata):
            vinculado, principal = _es_worktree_vinculado(candidata)
            if vinculado:
                mensaje = (
                    f"La carpeta detectada automáticamente ({candidata}) es un worktree "
                    "vinculado de git, no la carpeta principal del sistema. Un worktree "
                    "vinculado nunca se actualiza con los datos reales (PRODUCTOS/, "
                    "Ads/MEDIA_*): la app leería CSV viejos sin avisarlo."
                )
                if principal:
                    mensaje += f" Corré la app desde la carpeta principal: {principal}."
                mensaje += " Para forzar esta carpeta a propósito, declará VITALCOM_BASE."
                raise RuntimeError(mensaje)
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
