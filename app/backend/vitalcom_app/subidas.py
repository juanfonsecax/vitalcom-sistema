"""subidas.py — lo que el operador arrastra a la pantalla, guardado en el temporal.

Es el ÚNICO módulo de la app que escribe archivos, y solo dentro de una carpeta temporal
del sistema operativo que se borra sola. Nunca toca la carpeta del sistema: quien copia la
imagen adentro del repo es `alta_producto.py`, que además declara el packshot en
`_DIM_ENVASE.csv`. Por eso este módulo no importa `config`: no sabe dónde vive el sistema.
"""

from __future__ import annotations

import shutil
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import IO, Iterator

TAMANO_MAXIMO = 25 * 1024 * 1024  # una foto de producto; los videos van por carpeta, no por acá


class SubidaRechazada(ValueError):
    """El archivo no sirve. Se dice antes de tocar nada."""


@contextmanager
def carpeta_temporal() -> Iterator[Path]:
    carpeta = tempfile.mkdtemp(prefix="vitalcom-subida-")
    try:
        yield Path(carpeta)
    finally:
        shutil.rmtree(carpeta, ignore_errors=True)


def guardar(flujo_de_bytes: IO[bytes], nombre: str, destino: Path) -> Path:
    """Copia el archivo subido al temporal, con su extensión original."""
    sufijo = Path(nombre).suffix.lower()
    if not sufijo:
        raise SubidaRechazada(f"«{nombre}» no tiene extensión; no sé qué tipo de archivo es.")
    salida = destino / f"subida{sufijo}"
    with open(salida, "wb") as archivo:
        copiados = 0
        while True:
            pedazo = flujo_de_bytes.read(1024 * 1024)
            if not pedazo:
                break
            copiados += len(pedazo)
            if copiados > TAMANO_MAXIMO:
                raise SubidaRechazada(
                    f"«{nombre}» pasa de {TAMANO_MAXIMO // (1024 * 1024)} MB."
                )
            archivo.write(pedazo)
    return salida


def guardar_texto(texto: str, destino: Path, nombre: str = "descripcion.txt") -> Path:
    salida = destino / nombre
    with open(salida, "w", encoding="utf-8") as archivo:
        archivo.write(texto)
    return salida
