"""bitacora.py — el rastro de cada corrida, y lo ÚNICO que la app escribe dentro del sistema.

Cada trabajo deja una carpeta bajo `PRODUCTOS/_AUDITORIAS/app_runs/` (fuera de git):

    app_runs/2026-09/20260918-101502_nodo.F2.plan_TINNIDROP_3f2a1c9e/
        trabajo.json        el sello del trabajo + su estado final
        1.inicio / 1.fin    una línea por intento de la unidad 1
        1_claude.jsonl      salida completa de Claude
        2_gen_publicacion.log
        aprobaciones.jsonl  cada aprobación o rechazo, con hash, hora y nota

Reglas que este módulo hace cumplir (y una prueba estructural verifica):
  * Todo lo que abre o crea pasa por `_dentro`: nunca fuera de `app_runs/`.
  * Los logs se abren en modo `a` (agregar) y las marcas también: se agrega, no se reescribe.
    La única reescritura es `trabajo.json`, atómica (archivo aparte + `os.replace`).
  * No escribe CSV ni toca doctrina. Los CSV son de los scripts del motor.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, BinaryIO

from .config import ruta

RAIZ = ("PRODUCTOS", "_AUDITORIAS", "app_runs")
_SEGURO = re.compile(r"[^A-Za-z0-9._-]+")


class FueraDeLaBitacora(ValueError):
    """Se intentó escribir fuera de `app_runs/`. Es un defecto del código, no del operador."""


def raiz() -> Path:
    return ruta(*RAIZ)


def _dentro(destino: Path) -> Path:
    """`destino` resuelto, si está dentro de `app_runs/`; si no, se niega."""
    resuelto = destino.resolve()
    if not resuelto.is_relative_to(raiz().resolve()):
        raise FueraDeLaBitacora(f"«{destino}» está fuera de {'/'.join(RAIZ)}/.")
    return resuelto


def _limpio(texto: str) -> str:
    return _SEGURO.sub("_", texto).strip("._") or "x"


def _crear_carpeta(carpeta: Path) -> Path:
    destino = _dentro(carpeta)
    destino.mkdir(parents=True, exist_ok=True)
    return destino


def _abrir(archivo: Path, modo: str) -> BinaryIO:
    destino = _dentro(archivo)
    return open(destino, modo)


def carpeta_de_corrida(job_id: str, accion_id: str, producto_key: str | None, iniciado: str) -> Path:
    """`app_runs/<AAAA-MM>/<AAAAMMDD-HHMMSS>_<acción>_<producto>_<job8>/`.

    `iniciado` es el ISO-8601 sellado en el primer paso del workflow (`2026-09-18T10:15:02-06:00`),
    no la hora de ahora: al retomar tras una caída la carpeta tiene que ser la misma.
    """
    fecha, _, resto = iniciado.partition("T")
    hora = re.sub(r"[^0-9]", "", resto)[:6].ljust(6, "0")
    nombre = "_".join([
        f"{fecha.replace('-', '')}-{hora}", _limpio(accion_id), _limpio(producto_key or "global"), job_id[:8],
    ])
    return _crear_carpeta(raiz() / fecha[:7] / nombre)


def ruta_relativa(carpeta: Path) -> str:
    """La carpeta como el operador la ve: relativa a la base del sistema."""
    return carpeta.resolve().relative_to(ruta().resolve()).as_posix()


# ── trabajo.json (el sello y el estado final) ─────────────────────────────────

def reescribir_trabajo(carpeta: Path, contenido: dict[str, Any]) -> None:
    """Reescritura atómica de `trabajo.json`: un lector nunca ve un archivo a medias."""
    destino = _dentro(carpeta / "trabajo.json")
    provisorio = _dentro(carpeta / "trabajo.json.nuevo")
    with open(provisorio, "wb") as archivo:
        archivo.write(json.dumps(contenido, ensure_ascii=False, indent=1, default=str).encode("utf-8"))
    os.replace(provisorio, destino)


def leer_trabajo(carpeta: Path) -> dict[str, Any] | None:
    try:
        return json.loads(_dentro(carpeta / "trabajo.json").read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return None


# ── marcas de una unidad: `<n>.inicio` y `<n>.fin` ────────────────────────────

class Marca:
    """Cuántas veces empezó y cuántas terminó la unidad `n`. Empezó más veces que terminó = se cayó."""

    def __init__(self, carpeta: Path, n: int) -> None:
        self.carpeta = carpeta
        self.n = n

    def _lineas(self, sufijo: str) -> int:
        try:
            return len(_dentro(self.carpeta / f"{self.n}.{sufijo}").read_text(encoding="utf-8").splitlines())
        except FileNotFoundError:
            return 0

    def inicio_sin_fin(self) -> bool:
        return self._lineas("inicio") > self._lineas("fin")

    def intentos(self) -> int:
        return self._lineas("inicio")

    def _anotar(self, sufijo: str, dato: dict[str, Any]) -> None:
        with _abrir(self.carpeta / f"{self.n}.{sufijo}", "ab") as archivo:
            archivo.write((json.dumps(dato, ensure_ascii=False, default=str) + "\n").encode("utf-8"))

    def iniciar(self, ahora: str) -> None:
        self._anotar("inicio", {"intento": self.intentos() + 1, "ts": ahora})

    def terminar(self, ahora: str, resumen: dict[str, Any] | None = None) -> None:
        self._anotar("fin", {"ts": ahora, **(resumen or {})})

    def cerrar_intento_roto(self, ahora: str) -> None:
        """Una unidad idempotente que se cayó: se deja escrito y se vuelve a correr."""
        self._anotar("fin", {"ts": ahora, "roto": True})


# ── logs y aprobaciones (siempre agregando) ───────────────────────────────────

def abrir_log(carpeta: Path, nombre: str) -> BinaryIO:
    """Un log para que el subproceso escriba su salida. Modo `ab`: los reintentos se suman."""
    return _abrir(carpeta / _limpio(nombre), "ab")


def anotar_linea(carpeta: Path, nombre: str, texto: str) -> None:
    with _abrir(carpeta / _limpio(nombre), "ab") as archivo:
        archivo.write((texto.rstrip("\n") + "\n").encode("utf-8"))


def registrar_aprobacion(carpeta: Path, dato: dict[str, Any]) -> None:
    """`aprobaciones.jsonl`: quién aprobó o rechazó qué orden (hash) y cuándo. Solo se agrega."""
    anotar_linea(carpeta, "aprobaciones.jsonl", json.dumps(dato, ensure_ascii=False, default=str))
