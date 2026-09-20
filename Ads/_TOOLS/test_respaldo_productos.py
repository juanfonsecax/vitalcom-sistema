#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_respaldo_productos.py — Pruebas unitarias para Ads/_TOOLS/respaldo_productos.py."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPT = os.path.join(BASE, "Ads", "_TOOLS", "respaldo_productos.py")

if BASE not in sys.path:
    sys.path.insert(0, BASE)

import respaldo_productos  # noqa: E402


class TestRespaldoProductos(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.origen = self.root / "PRODUCTOS"
        self.destino = self.root / "RESPALDOS"
        self.origen.mkdir(parents=True, exist_ok=True)

        # Crear estructura de prueba simulando PRODUCTOS/
        (self.origen / "_DIM_PRODUCTOS.csv").write_text("producto_key,nombre\nP1,Producto 1\n", encoding="utf-8")
        sub = self.origen / "P1"
        sub.mkdir(parents=True, exist_ok=True)
        (sub / "1_HACER_MANUAL.txt").write_text("datos manuales", encoding="utf-8")

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_crear_respaldo_exitoso(self) -> None:
        res = respaldo_productos.crear_respaldo(
            origen=self.origen,
            destino_dir=self.destino,
            limite=30,
            dry_run=False,
        )
        self.assertTrue(res["ok"])
        self.assertEqual(res["archivos_incluidos"], 2)
        zip_path = Path(str(res["archivo"]))
        self.assertTrue(zip_path.is_file())
        self.assertGreater(zip_path.stat().st_size, 0)

        # Validar contenido del zip
        with zipfile.ZipFile(zip_path, "r") as zf:
            nombres = zf.namelist()
            self.assertIn("_DIM_PRODUCTOS.csv", [n.replace("\\", "/") for n in nombres])
            self.assertIn("P1/1_HACER_MANUAL.txt", [n.replace("\\", "/") for n in nombres])

    def test_dry_run_no_escribe(self) -> None:
        res = respaldo_productos.crear_respaldo(
            origen=self.origen,
            destino_dir=self.destino,
            limite=30,
            dry_run=True,
        )
        self.assertTrue(res["ok"])
        self.assertTrue(res["dry_run"])
        self.assertFalse(self.destino.exists())

    def test_rotacion_30_copias(self) -> None:
        self.destino.mkdir(parents=True, exist_ok=True)
        # Crear 35 archivos previos simulando días anteriores
        for i in range(1, 36):
            # Nombres con fecha ascendente PRODUCTOS_20260101_010000.zip ...
            p = self.destino / f"PRODUCTOS_202601{i:02d}_120000.zip"
            p.write_bytes(b"dummy zip content")

        # Crear nuevo respaldo con límite 30
        res = respaldo_productos.crear_respaldo(
            origen=self.origen,
            destino_dir=self.destino,
            limite=30,
            dry_run=False,
        )
        self.assertTrue(res["ok"])
        # Deben haberse eliminado los 6 más antiguos (35 previos + 1 nuevo = 36 total -> eliminar 6)
        self.assertEqual(len(res["eliminados"]), 6)
        restantes = list(self.destino.glob("PRODUCTOS_*.zip"))
        self.assertEqual(len(restantes), 30)

        # Los más antiguos eliminados deben ser del 1 al 6 de enero
        for i in range(1, 7):
            antiguo = self.destino / f"PRODUCTOS_202601{i:02d}_120000.zip"
            self.assertFalse(antiguo.exists())

    def test_origen_inexistente_falla(self) -> None:
        no_existe = self.root / "NO_EXISTE"
        with self.assertRaises(FileNotFoundError):
            respaldo_productos.crear_respaldo(
                origen=no_existe,
                destino_dir=self.destino,
            )

    def test_cli_json(self) -> None:
        cmd = [
            sys.executable,
            SCRIPT,
            "--origen",
            str(self.origen),
            "--destino",
            str(self.destino),
            "--limite",
            "10",
            "--json",
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(proc.returncode, 0, f"Error: {proc.stderr}")
        data = json.loads(proc.stdout)
        self.assertTrue(data["ok"])
        self.assertEqual(data["archivos_incluidos"], 2)
        self.assertTrue(Path(data["archivo"]).is_file())


if __name__ == "__main__":
    unittest.main()
