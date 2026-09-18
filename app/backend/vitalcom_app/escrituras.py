"""escrituras.py — lo único que puede cambiar el sistema, y siempre por un script del motor.

Tres reglas que este módulo hace cumplir:
  1. **La app no escribe: ejecuta al que escribe.** Cada cambio pasa por un script de
     `Ads/_TOOLS/` que tiene su propio test. Acá no hay `open(..., "w")` sobre el sistema.
  2. **Un escritor a la vez** (hoja de ruta §2.4). Dos altas simultáneas reescribirían
     `_DIM_PRODUCTOS.csv` pisándose. La cola es un lock de archivo en el temporal del
     sistema operativo, más el lock del proceso; ningún candado se escribe dentro del repo.
  3. **Después de escribir, el estado derivado se regenera** (`flujo.py --todo`). Los hooks
     de `.claude/settings.json` solo corren dentro de Claude Code: fuera, el que los suple
     es este módulo.
"""

from __future__ import annotations

import errno
import hashlib
import json
import os
import subprocess
import tempfile
import threading
import time
from pathlib import Path
from typing import Any

from .config import base, python_del_sistema, ruta

TIEMPO_MAXIMO_LOCK = 15 * 60  # un job colgado no puede dejar la cola trabada para siempre
_lock_del_proceso = threading.Lock()


class ErrorDeEscritura(RuntimeError):
    """El script del motor rechazó el cambio. El mensaje es suyo, no nuestro."""


class SistemaOcupado(RuntimeError):
    """Ya hay una escritura en curso. La app lo dice; no encola en silencio."""


def _archivo_de_lock() -> Path:
    firma = hashlib.sha1(str(base()).encode("utf-8")).hexdigest()[:12]
    return Path(tempfile.gettempdir()) / f"vitalcom-escritura-{firma}.lock"


class Cola:
    """Un escritor a la vez, incluso entre procesos distintos."""

    def __enter__(self) -> "Cola":
        if not _lock_del_proceso.acquire(blocking=False):
            raise SistemaOcupado("ya hay un cambio en curso en esta app.")
        candado = _archivo_de_lock()
        try:
            if candado.exists() and time.time() - candado.stat().st_mtime > TIEMPO_MAXIMO_LOCK:
                candado.unlink(missing_ok=True)  # quedó de un proceso que murió
            descriptor = os.open(candado, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except OSError as error:
            _lock_del_proceso.release()
            if error.errno == errno.EEXIST:
                raise SistemaOcupado(
                    "otro proceso está escribiendo en el sistema. Probá de nuevo en un momento."
                ) from error
            raise
        os.write(descriptor, str(os.getpid()).encode("ascii"))
        os.close(descriptor)
        return self

    def __exit__(self, *_excepcion: object) -> None:
        _archivo_de_lock().unlink(missing_ok=True)
        _lock_del_proceso.release()


def _correr(script: str, argumentos: list[str], tiempo: int = 1800) -> dict[str, Any]:
    """Corre un script del motor con `--json` y devuelve su salida tal cual."""
    comando = [python_del_sistema(), str(ruta("Ads", "_TOOLS", script)), *argumentos, "--json"]
    completado = subprocess.run(
        comando, cwd=str(ruta()), capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=tiempo,
    )
    salida = (completado.stdout or "").strip()
    try:
        respuesta = json.loads(salida) if salida else {}
    except json.JSONDecodeError:
        raise ErrorDeEscritura(
            f"{script} devolvió algo que no es JSON: {salida[-500:] or completado.stderr[-500:]}"
        )
    if completado.returncode != 0 or respuesta.get("ok") is False:
        detalle = respuesta.get("detalle") or completado.stderr.strip() or salida
        raise ErrorDeEscritura(detalle[-800:])
    return respuesta


def refrescar_estado_derivado() -> None:
    """`flujo.py --todo` re-evalúa el grafo y reescribe `_ESTADO_FLUJO.csv` y la vista."""
    subprocess.run(
        [python_del_sistema(), str(ruta("Ads", "_TOOLS", "flujo.py")), "--todo", "--silencioso"],
        cwd=str(ruta()), capture_output=True, text=True, encoding="utf-8",
        errors="replace", timeout=600,
    )


def dar_de_alta(campos: dict[str, str], imagen: Path, descripcion: Path,
                dry_run: bool = False) -> dict[str, Any]:
    """Ejecuta `alta_producto.py`. Los archivos llegan del temporal, no del repo."""
    argumentos = [
        "--nombre", campos["nombre"],
        "--costo", campos["costo"],
        "--descripcion-archivo", str(descripcion),
        "--imagen", str(imagen),
    ]
    for bandera, clave in (
        ("--clave", "clave"), ("--cuenta", "cuenta"), ("--moneda", "moneda"), ("--tasa", "tasa"),
        ("--color-envase", "color_envase"), ("--color-hex", "color_hex"),
        ("--marca", "marca"), ("--formato", "formato"),
    ):
        valor = (campos.get(clave) or "").strip()
        if valor:
            argumentos += [bandera, valor]
    if dry_run:
        argumentos.append("--dry-run")

    with Cola():
        resultado = _correr("alta_producto.py", argumentos)
        if not dry_run:
            refrescar_estado_derivado()
    return resultado


def transcribir(producto_key: str, modelo: str = "small") -> dict[str, Any]:
    """Ejecuta `transcribir_videos.py` para un producto ya dado de alta."""
    with Cola():
        return _correr(
            "transcribir_videos.py",
            ["--producto", producto_key, "--modelo", modelo],
            tiempo=3600,  # la primera corrida baja el modelo
        )
