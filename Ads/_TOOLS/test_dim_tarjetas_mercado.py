# -*- coding: utf-8 -*-
"""test_dim_tarjetas_mercado.py — gate de la dimensión tarjeta -> BM -> mercado.

Cada cargo de Mercury se asigna a su mercado por los últimos 4 de la tarjeta
(`PRODUCTOS/_DIM_TARJETAS_MERCADO.csv`): los últimos 4 no se repiten y el mercado
es uno de los declarados. Corre sobre juguete más el archivo real: nunca lo escribe.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tarjetas_mercado  # noqa: E402


def _fila(ultimos4, mercado="GT", estado="ACTIVA", uso="PAUTA"):
    return {"banco": "MERCURY", "ultimos4": ultimos4, "bm": "AMG 2", "mercado": mercado,
            "uso": uso, "cuentas_publicitarias": "GTR0", "estado": estado,
            "confirmado_por": "operador", "fecha": "2026-10-14", "notas": ""}


class Validar(unittest.TestCase):
    def test_filas_de_juguete_validas_pasan(self) -> None:
        filas = [_fila("4232"), _fila("9893", mercado="CO"),
                 _fila("1077", mercado="SIN_USO"), _fila("9282", mercado="COMPARTIDO")]
        self.assertEqual(tarjetas_mercado.validar(filas), [])

    def test_mercado_vacio_pasa_para_las_muertas(self) -> None:
        fila = _fila("2479", mercado="", estado="MUERTA", uso="")
        self.assertEqual(tarjetas_mercado.validar([fila]), [])

    def test_ultimos4_repetidos_se_rechazan(self) -> None:
        errores = tarjetas_mercado.validar([_fila("4232"), _fila("4232", mercado="CO")])
        self.assertEqual(len(errores), 1)
        self.assertIn("4232", errores[0])

    def test_mercado_fuera_del_vocabulario_se_rechaza(self) -> None:
        errores = tarjetas_mercado.validar([_fila("4232", mercado="MX")])
        self.assertEqual(len(errores), 1)
        self.assertIn("MX", errores[0])

    def test_fila_sin_ultimos4_se_rechaza(self) -> None:
        fila = _fila("", mercado="GT")
        self.assertEqual(len(tarjetas_mercado.validar([fila])), 1)


class ArchivoReal(unittest.TestCase):
    def test_el_archivo_carga_con_ultimos4_unicos_y_mercado_declarado(self) -> None:
        filas = tarjetas_mercado.cargar()
        self.assertTrue(filas, "sin filas en _DIM_TARJETAS_MERCADO.csv")
        self.assertEqual(tarjetas_mercado.validar(filas), [])


class MercadoDe(unittest.TestCase):
    FILAS = [_fila("4232", mercado="GT"), _fila("9893", mercado="CO"),
             _fila("2479", mercado="", estado="MUERTA", uso="")]

    def test_la_tarjeta_conocida_da_su_mercado(self) -> None:
        self.assertEqual(tarjetas_mercado.mercado_de("4232", self.FILAS), "GT")
        self.assertEqual(tarjetas_mercado.mercado_de("9893", self.FILAS), "CO")

    def test_la_desconocida_o_sin_mercado_da_vacio(self) -> None:
        self.assertEqual(tarjetas_mercado.mercado_de("0000", self.FILAS), "")
        self.assertEqual(tarjetas_mercado.mercado_de("2479", self.FILAS), "")
        self.assertEqual(tarjetas_mercado.mercado_de("", self.FILAS), "")


if __name__ == "__main__":
    unittest.main()
