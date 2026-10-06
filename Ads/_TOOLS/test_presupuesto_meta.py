#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_presupuesto_meta.py — Pruebas unitarias para presupuesto_meta.py."""
import os
import sys
import unittest

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import presupuesto_meta as pm  # noqa: E402


class TestLeerPresupuesto(unittest.TestCase):
    def test_objeto_value_unit(self):
        self.assertEqual(pm.leer_presupuesto({"value": "3.99", "unit": "USD"}), (3.99, "USD"))

    def test_numero_usa_moneda_defecto(self):
        self.assertEqual(pm.leer_presupuesto(15.0, "USD"), (15.0, "USD"))
        self.assertEqual(pm.leer_presupuesto("3.5", "USD"), (3.5, "USD"))
        self.assertEqual(pm.leer_presupuesto(3.5), (3.5, None))

    def test_vacio_invalido_o_no_positivo(self):
        for malo in (None, "", "abc", 0, -5, {}, {"value": "0", "unit": "USD"},
                     {"value": "x", "unit": "USD"}):
            self.assertEqual(pm.leer_presupuesto(malo, "USD"), (None, None), repr(malo))


class TestAUnidadMenor(unittest.TestCase):
    def test_usd_y_cop(self):
        self.assertEqual(pm.a_unidad_menor(3.99, "USD"), 399)
        self.assertEqual(pm.a_unidad_menor(4.788, "USD"), 479)
        self.assertEqual(pm.a_unidad_menor(15000, "COP"), 15000)

    def test_moneda_desconocida(self):
        self.assertIsNone(pm.a_unidad_menor(3.99, "EUR"))
        self.assertIsNone(pm.a_unidad_menor(3.99, None))


if __name__ == "__main__":
    unittest.main()
