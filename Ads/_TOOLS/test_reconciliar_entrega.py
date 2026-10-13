#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_reconciliar_entrega.py — congela el diagnostico de reconciliar_entrega.py (T5, 13-oct-2026)."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import reconciliar_entrega as re_  # noqa: E402


def _f(fuente, cuenta, ini, fin=None, spend="10.0"):
    return {"fuente": fuente, "cuenta_id": cuenta, "ventana_ini": ini, "ventana_fin": fin or ini,
            "spend_usd": spend}


class DiagnosticoTest(unittest.TestCase):
    def test_gasto_por_cuenta_mes_antes_y_despues(self):
        filas = [
            _f("MetaAPI-directo", "A", "2026-09-10", spend="100"),
            _f("AdsManager-export-1d", "A", "2026-09-10", spend="90"),
            _f("AdsManager-export-1d", "A", "2026-09-11", spend="5"),
        ]
        cons, sup, parc, antes, despues = re_.diagnosticar(filas)
        self.assertEqual(len(sup), 1)
        self.assertEqual(parc, [])
        self.assertAlmostEqual(antes[("A", "2026-09")], 195.0)
        self.assertAlmostEqual(despues[("A", "2026-09")], 105.0)

    def test_parcial_se_conserva_y_se_lista(self):
        filas = [_f("MetaAPI-directo", "A", "2026-09-10"),
                 _f("MCP-ladoads-7d", "A", "2026-09-10", "2026-09-16", spend="70")]
        cons, sup, parc, _, despues = re_.diagnosticar(filas)
        self.assertEqual((len(cons), len(sup), len(parc)), (2, 0, 1))
        self.assertAlmostEqual(despues[("A", "2026-09")], 80.0)


if __name__ == "__main__":
    unittest.main()
