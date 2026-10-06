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
                    "args": {"entity_id": "adset_2", "fields": {"daily_budget": 360}},
                    "entidad": {"id": "adset_2", "nombre": "Conjunto 2"},
                },
            ],
        }
        snap_fixture = {
            "moneda": "USD",
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
                    "args": {"entity_id": "adset_2", "fields": {"daily_budget": 500}},
                    "entidad": {"id": "adset_2", "nombre": "Conjunto 2"},
                }
            ],
        }
        snap_fixture = {
            "moneda": "USD",
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

    def _verificar_budget(self, esperado, budget_real, extra=None):
        orden = {"llamadas": [{
            "n": 1, "tool": "ads_update_entity",
            "args": {"entity_id": "adset_2", "fields": {"daily_budget": esperado}},
            "entidad": {"id": "adset_2", "nombre": "Conjunto 2"},
        }]}
        snap = {"ad_entities": [{"id": "adset_2", "name": "Conjunto 2", "status": "ACTIVE",
                                 "daily_budget": budget_real}]}
        snap.update(extra or {})
        snap_path = os.path.join(self.temp_dir, "snap_obj.json")
        with io.open(snap_path, "w", encoding="utf-8") as fh:
            json.dump(snap, fh)
        return verificar_orden.verificar(orden, snap_path)

    def test_budget_objeto_meta_coincide_en_unidad_menor(self):
        ok, fallas = self._verificar_budget(479, {"value": "4.79", "unit": "USD"})
        self.assertTrue(ok, fallas)

    def test_budget_objeto_meta_distinto_es_discrepancia(self):
        ok, fallas = self._verificar_budget(479, {"value": "3.99", "unit": "USD"})
        self.assertFalse(ok)
        self.assertIn("daily_budget", fallas[0])

    def test_budget_sin_moneda_conocida_es_discrepancia(self):
        ok, fallas = self._verificar_budget(479, 4.79)
        self.assertFalse(ok)


if __name__ == "__main__":
    unittest.main()
