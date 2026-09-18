"""escrituras.py — el turno de escritura: un escritor a la vez sobre el sistema.

Dos escrituras simultáneas pisarían un mismo CSV (hoja de ruta §2.4). El turno es un candado
de archivo en el temporal del sistema operativo más el candado del proceso; ningún candado se
escribe dentro del repo. Quien usa el turno es el runner (`workflows.py`), una vez por cada
unidad que escribe. Este módulo no ejecuta nada ni escribe nada del sistema.
"""

from __future__ import annotations

import errno
import hashlib
import json
import os
import tempfile
import threading
import time
from pathlib import Path
from typing import Any

from .config import base

# El candado tiene latido: el dueño lo toca cada LATIDO_S; sin latido por CADUCA_SIN_LATIDO_S se
# considera de un proceso muerto. Con el tope fijo de 15 min de antes, una corrida larga de
# Claude (una FASE 1 tarda ~40 min) perdía el candado en plena escritura.
LATIDO_S = 30
CADUCA_SIN_LATIDO_S = 120
SONDEO_S = 2
_lock_del_proceso = threading.Lock()


class ErrorDeEscritura(RuntimeError):
    """El script del motor rechazó el cambio. El mensaje es suyo, no nuestro."""


class SistemaOcupado(RuntimeError):
    """Ya hay una escritura en curso. La app lo dice; no encola en silencio."""


def _archivo_de_lock() -> Path:
    firma = hashlib.sha1(str(base()).encode("utf-8")).hexdigest()[:12]
    return Path(tempfile.gettempdir()) / f"vitalcom-escritura-{firma}.lock"


def _proceso_vivo(pid: int) -> bool:
    """¿Existe ese proceso? (`os.kill(pid, 0)` en Windows MATA al proceso: ahí se pregunta por la API.)"""
    if os.name == "nt":
        import ctypes

        consultar_estado = 0x1000  # PROCESS_QUERY_LIMITED_INFORMATION
        aun_activo = 259           # STILL_ACTIVE
        kernel = ctypes.windll.kernel32  # type: ignore[attr-defined]
        manija = kernel.OpenProcess(consultar_estado, False, pid)
        if not manija:
            return False
        codigo = ctypes.c_ulong()
        try:
            return bool(kernel.GetExitCodeProcess(manija, ctypes.byref(codigo))) and codigo.value == aun_activo
        finally:
            kernel.CloseHandle(manija)
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def candado_abandonado(candado: Path, ahora: float) -> bool:
    """El dueño ya no existe, o lleva más de CADUCA_SIN_LATIDO_S sin latir: quedó de un proceso muerto."""
    try:
        sin_latido = ahora - candado.stat().st_mtime > CADUCA_SIN_LATIDO_S
        ficha = json.loads(candado.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return False
    except (json.JSONDecodeError, OSError):
        return sin_latido
    pid = ficha.get("pid")
    if isinstance(pid, int) and pid != os.getpid() and not _proceso_vivo(pid):
        return True
    return sin_latido


def quien_escribe() -> dict[str, Any] | None:
    """Quién tiene el turno de escritura ({pid, job_id, desde}), para mostrarlo en pantalla."""
    try:
        return json.loads(_archivo_de_lock().read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return None


class Cola:
    """Un escritor a la vez, incluso entre procesos distintos.

    `Cola()` falla enseguida con `SistemaOcupado` si hay otro escribiendo. `Cola(esperar=True,
    tope_s=N)` espera su turno hasta N segundos (lo que usa el runner). Mientras dura el
    turno, un hilo toca el candado cada `LATIDO_S`: mientras haya latido, nadie lo borra.
    """

    def __init__(self, esperar: bool = False, tope_s: float | None = None,
                 job_id: str | None = None) -> None:
        self.esperar = esperar
        self.tope_s = tope_s
        self.job_id = job_id
        self._parar = threading.Event()
        self._latido: threading.Thread | None = None

    def _tomar_el_candado(self) -> None:
        candado = _archivo_de_lock()
        if candado_abandonado(candado, time.time()):
            candado.unlink(missing_ok=True)
        descriptor = os.open(candado, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        ficha = {"pid": os.getpid(), "job_id": self.job_id, "desde": time.time()}
        os.write(descriptor, json.dumps(ficha).encode("utf-8"))
        os.close(descriptor)

    def _latir(self) -> None:
        candado = _archivo_de_lock()
        while not self._parar.wait(LATIDO_S):
            try:
                os.utime(candado)
            except FileNotFoundError:
                return

    def __enter__(self) -> "Cola":
        limite = time.monotonic() + (self.tope_s or 0)
        while True:
            if _lock_del_proceso.acquire(blocking=False):
                try:
                    self._tomar_el_candado()
                    break
                except OSError as error:
                    _lock_del_proceso.release()
                    if error.errno != errno.EEXIST:
                        raise
                    motivo = "otro proceso está escribiendo en el sistema. Probá de nuevo en un momento."
                except BaseException:
                    _lock_del_proceso.release()
                    raise
            else:
                motivo = "ya hay un cambio en curso en esta app."
            if not self.esperar or time.monotonic() >= limite:
                raise SistemaOcupado(motivo)
            time.sleep(SONDEO_S)
        self._parar.clear()
        self._latido = threading.Thread(target=self._latir, daemon=True, name="latido-de-la-cola")
        self._latido.start()
        return self

    def __exit__(self, *_excepcion: object) -> None:
        self._parar.set()
        if self._latido is not None:
            self._latido.join(timeout=2)
        _archivo_de_lock().unlink(missing_ok=True)
        _lock_del_proceso.release()
