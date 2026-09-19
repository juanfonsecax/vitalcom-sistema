#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_verificar_orden.py — Pruebas unitarias para verificar_orden.py (Hito 5)."""
import io
import json
import os
import sys
import tempfile
import unittest

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import verificar_orden  # noqa: E402


class TestVerificarOrden(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_verificacion_exitosa(self):
        orden_fixture = {
            "producto": "PROD_OK",
            "llamadas": [
                {
                    "n": 1,
                    "tool": "ads_update_entity",
                    "args": {"entity_id": "adset_1", "fields": {"status": "PAUSED"}},
                    "entidad": {"id": "adset_1", "nombre": "Conjunto 1"},
                },
                {
                    "n": 2,
                    "tool": "ads_update_entity",
                    "args": {"entity_id": "adset_2", "fields": {"daily_budget": 3.60}},
                    "entidad": {"id": "adset_2", "nombre": "Conjunto 2"},
                },
            ],
        }
        snap_fixture = {
            "ad_entities": [
                {"id": "adset_1", "name": "Conjunto 1", "status": "PAUSED"},
                {"id": "adset_2", "name": "Conjunto 2", "status": "ACTIVE", "daily_budget": "3.60"},
            ]
        }
        snap_path = os.path.join(self.temp_dir, "snap_ok.json")
        with io.open(snap_path, "w", encoding="utf-8") as fh:
            json.dump(snap_fixture, fh)

        ok, fallas = verificar_orden.verificar(orden_fixture, snap_path)
        self.assertTrue(ok)
        self.assertEqual(len(fallas), 0)

    def test_verificacion_falla_por_status(self):
        orden_fixture = {
            "producto": "PROD_FALLA",
            "llamadas": [
                {
                    "n": 1,
                    "tool": "ads_update_entity",
                    "args": {"entity_id": "adset_1", "fields": {"status": "PAUSED"}},
                    "entidad": {"id": "adset_1", "nombre": "Conjunto 1"},
                }
            ],
        }
        snap_fixture = {
            "ad_entities": [
                {"id": "adset_1", "name": "Conjunto 1", "status": "ACTIVE"}  # Sigue ACTIVE
            ]
        }
        snap_path = os.path.join(self.temp_dir, "snap_fail.json")
        with io.open(snap_path, "w", encoding="utf-8") as fh:
            json.dump(snap_fixture, fh)

        ok, fallas = verificar_orden.verificar(orden_fixture, snap_path)
        self.assertFalse(ok)
        self.assertEqual(len(fallas), 1)
        self.assertIn("esperado 'PAUSED'", fallas[0])

    def test_verificacion_falla_por_budget(self):
        orden_fixture = {
            "producto": "PROD_FALLA_B",
            "llamadas": [
                {
                    "n": 1,
                    "tool": "ads_update_entity",
                    "args": {"entity_id": "adset_2", "fields": {"daily_budget": 5.00}},
                    "entidad": {"id": "adset_2", "nombre": "Conjunto 2"},
                }
            ],
        }
        snap_fixture = {
            "ad_entities": [
                {"id": "adset_2", "name": "Conjunto 2", "status": "ACTIVE", "daily_budget": 2.99}
            ]
        }
        snap_path = os.path.join(self.temp_dir, "snap_budget.json")
        with io.open(snap_path, "w", encoding="utf-8") as fh:
            json.dump(snap_fixture, fh)

        ok, fallas = verificar_orden.verificar(orden_fixture, snap_path)
        self.assertFalse(ok)
        self.assertEqual(len(fallas), 1)
        self.assertIn("daily_budget", fallas[0])


if __name__ == "__main__":
    unittest.main()
