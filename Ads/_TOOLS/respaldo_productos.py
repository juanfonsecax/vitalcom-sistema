#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""respaldo_productos.py — Copia de seguridad automática diaria de PRODUCTOS/.

Genera un archivo zip fechado de la carpeta PRODUCTOS/ fuera del repositorio.
Mantiene las últimas 30 copias eliminando las más antiguas.

Uso:
    python Ads/_TOOLS/respaldo_productos.py
    python Ads/_TOOLS/respaldo_productos.py --json
    python Ads/_TOOLS/respaldo_productos.py --dry-run
    python Ads/_TOOLS/respaldo_productos.py --destino /ruta/externa --limite 30
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
import zipfile
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, OSError):
    pass

BASE_DEFECTO = os.environ.get(
    "VITALCOM_BASE",
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
)


def resolver_destino_por_defecto() -> Path:
    env_dir = os.environ.get("VITALCOM_RESPALDOS_DIR")
    if env_dir:
        return Path(env_dir)
    return Path.home() / "Documents" / "VITALCOM_RESPALDOS"


def crear_respaldo(
    origen: Path,
    destino_dir: Path,
    limite: int = 30,
    dry_run: bool = False,
) -> dict[str, object]:
    if not origen.is_dir():
        raise FileNotFoundError(f"No existe el directorio de origen: {origen}")

    ahora = dt.datetime.now()
    nombre_zip = f"PRODUCTOS_{ahora.strftime('%Y%m%d_%H%M%S')}.zip"
    ruta_zip = destino_dir / nombre_zip

    resultado: dict[str, object] = {
        "ok": True,
        "origen": str(origen),
        "destino_dir": str(destino_dir),
        "archivo": str(ruta_zip),
        "nombre": nombre_zip,
        "fecha": ahora.isoformat(),
        "dry_run": dry_run,
        "archivos_incluidos": 0,
        "bytes_totales": 0,
        "eliminados": [],
        "total_conservados": 0,
    }

    # 1. Contar y simular/escribir el zip
    archivos_a_incluir: list[Path] = []
    for raiz, _, archivos in os.walk(origen):
        for arch in archivos:
            archivos_a_incluir.append(Path(raiz) / arch)

    resultado["archivos_incluidos"] = len(archivos_a_incluir)

    if not dry_run:
        destino_dir.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(ruta_zip, "w", zipfile.ZIP_DEFLATED) as zf:
            for arch_path in archivos_a_incluir:
                arcname = arch_path.relative_to(origen)
                zf.write(arch_path, arcname)
        resultado["bytes_totales"] = ruta_zip.stat().st_size
    else:
        # En dry-run estimamos bytes sumando tamaños
        bytes_est = sum(p.stat().st_size for p in archivos_a_incluir if p.is_file())
        resultado["bytes_totales"] = bytes_est

    # 2. Poda de respaldos viejos (retener últimos `limite`)
    existentes: list[Path] = []
    if destino_dir.is_dir():
        for item in destino_dir.glob("PRODUCTOS_*.zip"):
            if item.is_file():
                existentes.append(item)

    # Ordenar por nombre descendente (los más recientes primero)
    existentes.sort(key=lambda p: p.name, reverse=True)

    eliminados: list[str] = []
    if len(existentes) > limite:
        sobrantes = existentes[limite:]
        for sob in sobrantes:
            eliminados.append(sob.name)
            if not dry_run:
                try:
                    sob.unlink()
                except OSError as err:
                    print(f"Advertencia: no se pudo eliminar {sob}: {err}", file=sys.stderr)

    resultado["eliminados"] = eliminados
    resultado["total_conservados"] = min(len(existentes), limite)
    return resultado


def main() -> int:
    parser = argparse.ArgumentParser(description="Respaldo automático de PRODUCTOS/")
    parser.add_argument(
        "--origen",
        type=Path,
        default=None,
        help="Directorio origen a respaldar (default: PRODUCTOS/ del sistema)",
    )
    parser.add_argument(
        "--destino",
        type=Path,
        default=None,
        help="Directorio destino fuera del repo (default: ~/Documents/VITALCOM_RESPALDOS o VITALCOM_RESPALDOS_DIR)",
    )
    parser.add_argument(
        "--limite",
        type=int,
        default=30,
        help="Cantidad máxima de respaldos a conservar (default: 30)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simula la operación sin crear ni borrar archivos",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Salida en formato JSON estructurado",
    )

    args = parser.parse_args()

    base_dir = Path(BASE_DEFECTO)
    origen = args.origen or (base_dir / "PRODUCTOS")
    destino = args.destino or resolver_destino_por_defecto()

    try:
        res = crear_respaldo(
            origen=origen,
            destino_dir=destino,
            limite=args.limite,
            dry_run=args.dry_run,
        )
    except Exception as exc:
        if args.json:
            print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        else:
            print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        verbo = "Se crearía" if args.dry_run else "Creado"
        print(f"✓ {verbo} respaldo: {res['archivo']}")
        print(f"  Archivos incluidos: {res['archivos_incluidos']}")
        tam_mb = (res["bytes_totales"] or 0) / (1024 * 1024)
        print(f"  Tamaño: {tam_mb:.2f} MB")
        if res["eliminados"]:
            print(f"  Rotación ({len(res['eliminados'])} podados para mantener máx {args.limite}):")
            for el in res["eliminados"]:
                print(f"    - {el}")
        else:
            print(f"  Rotación: {res['total_conservados']} respaldos almacenados (máx {args.limite})")

    return 0


if __name__ == "__main__":
    sys.exit(main())
