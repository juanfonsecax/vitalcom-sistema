#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_reingreso_f1.py — Pruebas unitarias para reingreso_f1.py."""
import csv
import io
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from reingreso_f1 import ejecutar_reingreso, angulos_probados


class TestReingresoF1(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="test_reingreso_")
        self.prod_dir = os.path.join(self.tmp, "PRODUCTOS")
        os.makedirs(self.prod_dir, exist_ok=True)

        def escribir(nombre, cols, filas):
            with io.open(os.path.join(self.prod_dir, nombre), "w", encoding="utf-8", newline="") as fh:
                w = csv.writer(fh)
                w.writerow(cols)
                w.writerows(filas)

        escribir("_DIM_PRODUCTOS.csv",
                 ["producto_key", "nombre_display", "estado", "fase", "cuenta_alias"],
                 [["TEST_PROD", "Test Producto", "VIVO", "F2", "GTR0"]])

        escribir("_DIM_CONJUNTOS.csv",
                 ["producto_key", "conjunto_meta", "angulo_key"],
                 [["TEST_PROD", "GTR0_TEST_ANG1_R1", "ANG_GANADOR"],
                  ["TEST_PROD", "GTR0_TEST_ANG2_R1", "ANG_SECUNDARIO"]])

        escribir("_FACT_VENTAS.csv",
                 ["ventana_fin", "rol_ventana", "producto_key", "conjunto", "campana", "anuncio", "ventas", "spend_usd"],
                 [["2026-09-01", "BASE", "TEST_PROD", "GTR0_TEST_ANG1_R1", "C", "a", "10", "50"]])

        escribir("_EVENTOS.csv",
                 ["fecha", "producto_key", "cuenta_alias", "campana_clave", "conjunto_meta", "evento", "valor_antes", "valor_despues", "motivo", "fuente_decision"],
                 [["2026-08-01", "TEST_PROD", "GTR0", "*", "*", "LANZAMIENTO", "", "1.59", "FASE 1 test", "ETAPA-6"]])

    def test_angulos_probados(self):
        ang = angulos_probados(self.tmp, "TEST_PROD")
        self.assertEqual(ang, ["ANG_GANADOR", "ANG_SECUNDARIO"])

    def test_dry_run_no_escribe(self):
        res = ejecutar_reingreso("TEST_PROD", motivo="Fatiga", base_dir=self.tmp, dry_run=True)
        self.assertTrue(res["ok"])
        self.assertEqual(res["producto_key"], "TEST_PROD")
        self.assertEqual(res["fase_destino"], "F1")
        self.assertIn("ANG_GANADOR", res["angulos_excluidos"])
        # Verificar que _EVENTOS.csv sigue teniendo 1 sola fila de datos
        with io.open(os.path.join(self.prod_dir, "_EVENTOS.csv"), encoding="utf-8") as fh:
            filas = list(csv.DictReader(fh))
        self.assertEqual(len(filas), 1)

    def test_ejecucion_real_anexa_evento(self):
        res = ejecutar_reingreso("TEST_PROD", motivo="Fatiga probada", base_dir=self.tmp, dry_run=False)
        self.assertTrue(res["ok"])
        with io.open(os.path.join(self.prod_dir, "_EVENTOS.csv"), encoding="utf-8") as fh:
            filas = list(csv.DictReader(fh))
        self.assertEqual(len(filas), 2)
        ult = filas[-1]
        self.assertEqual(ult["producto_key"], "TEST_PROD")
        self.assertEqual(ult["evento"], "REINGRESO_F1")
        self.assertEqual(ult["valor_despues"], "F1")
        self.assertIn("ANG_GANADOR", ult["motivo"])

    def test_producto_inexistente(self):
        res = ejecutar_reingreso("NO_EXISTE", base_dir=self.tmp, dry_run=True)
        self.assertFalse(res["ok"])
        self.assertIn("no existe", res["error"])


if __name__ == "__main__":
    unittest.main()
