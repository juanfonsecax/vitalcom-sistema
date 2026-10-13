#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_ingerir_cartera.py — gate de ingerir_cartera.py y de la clasificacion de retiros.

El historial de cartera de Dropi es el libro de caja de la billetera: una fila por movimiento con su
ID. Cada ingesta hace UPSERT por ID de movimiento; re-ingerir el mismo archivo no cambia nada. Los
retiros se clasifican por su CONCEPTO con `_DIM_RETIROS.csv` y lo que no calza queda SIN_CLASIFICAR
(nunca se adivina). Corre sobre un historial de juguete y una carpeta temporal: nunca toca PRODUCTOS/.
"""
import csv
import os
import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_pl            # noqa: E402
import ingerir_cartera as ic  # noqa: E402

DESC_GAN = "ENTRADA POR GANANCIA EN LA ORDEN COMO DROPSHIPPER: %d* GUIA: *FD1*"
DESC_DEV = "SALIDA DE COBRO DE DEVOLUCIÓN POR ENTREGA NO EFECTIVA: %d"
DESC_RET = "SALIDA POR PETICION DE RETIRO DE SALDO EN CARTERA"

REGLAS = [
    {"patron": "papa", "clasificacion": "RETIRO_PERSONAL"},
    {"patron": "RETIRO PROPIO", "clasificacion": "TRANSFERENCIA_PROPIA"},
    {"patron": "DFF VENTURES", "clasificacion": "TRANSFERENCIA_PROPIA"},
]


def _mov(id_, fecha, tipo, monto, previo, orden=None, desc=None, concepto=None):
    if desc is None:
        desc = (DESC_GAN % orden) if tipo == "ENTRADA" else (DESC_DEV % orden)
    return {"ID": id_, "FECHA": fecha, "TIPO": tipo, "MONTO": monto, "MONTO PREVIO": previo,
            "ORDEN ID": orden, "NUMERO DE GUIA": None if orden is None else "FD1",
            "DESCRIPCIÓN": desc, "CUENTA": None, "CONCEPTO DE RETIRO": concepto}


def _historial():
    # el export viene del mas nuevo al mas viejo
    return [
        _mov(30, "09-10-2026 14:38", "SALIDA", 500.0, 1000.0, desc=DESC_RET, concepto="Retiro papa"),
        _mov(20, "05-10-2026 08:00", "SALIDA", 40.0, 1040.0, orden=777),
        _mov(10, "01-10-2026 00:09", "ENTRADA", 140.0, 900.0, orden=555),
    ]


def _xlsx(ruta, filas):
    pd.DataFrame(filas).to_excel(ruta, index=False)
    return ruta


def _leer(ruta):
    with open(ruta, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


class IngestaCartera(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.destino = self.dir / "_FACT_CARTERA_DROPI.csv"

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _ingerir(self, nombre="historial de cartera-13-10-2026 10_05.xlsx", filas=None, escribir=True):
        ruta = _xlsx(self.dir / nombre, filas if filas is not None else _historial())
        return ic.ingerir(str(ruta), destino=str(self.destino), escribir=escribir)

    def test_una_fila_por_movimiento_con_saldo_y_categoria(self) -> None:
        self._ingerir()
        filas = {f["mov_id"]: f for f in _leer(self.destino)}
        self.assertEqual(set(filas), {"10", "20", "30"})
        self.assertEqual(filas["10"]["categoria"], "GANANCIA_ORDEN")
        self.assertEqual(filas["20"]["categoria"], "COBRO_DEVOLUCION")
        self.assertEqual(filas["30"]["categoria"], "RETIRO")
        self.assertEqual((filas["10"]["fecha"], filas["10"]["hora"]), ("2026-10-01", "00:09"))
        self.assertEqual(filas["10"]["saldo_despues_q"], "1040.00")   # 900 + 140
        self.assertEqual(filas["20"]["saldo_despues_q"], "1000.00")   # 1040 - 40
        self.assertEqual(filas["30"]["saldo_despues_q"], "500.00")
        self.assertEqual(filas["30"]["concepto_retiro"], "Retiro papa")
        self.assertEqual(filas["10"]["orden_id"], "555")
        self.assertEqual(filas["30"]["orden_id"], "")
        self.assertEqual(filas["10"]["mercado"], "GT")

    def test_el_archivo_queda_ordenado_por_movimiento(self) -> None:
        self._ingerir()
        self.assertEqual([f["mov_id"] for f in _leer(self.destino)], ["10", "20", "30"])

    def test_reingerir_el_mismo_archivo_no_cambia_nada(self) -> None:
        self._ingerir()
        antes = self.destino.read_bytes()
        res = self._ingerir()
        self.assertEqual(self.destino.read_bytes(), antes)
        self.assertEqual((res["nuevas"], res["actualizadas"], res["sin_cambio"]), (0, 0, 3))

    def test_un_historial_nuevo_suma_movimientos_y_conserva_los_viejos(self) -> None:
        self._ingerir()
        nuevo = [_mov(40, "13-10-2026 00:09", "ENTRADA", 100.0, 500.0, orden=888)] + _historial()[:1]
        res = self._ingerir("otro.xlsx", nuevo)
        self.assertEqual(res["nuevas"], 1)
        self.assertEqual({f["mov_id"] for f in _leer(self.destino)}, {"10", "20", "30", "40"})

    def test_sin_escribir_solo_mira(self) -> None:
        res = self._ingerir(escribir=False)
        self.assertFalse(self.destino.exists())
        self.assertEqual((res["nuevas"], res["escrito"]), (3, False))

    def test_un_archivo_que_no_es_cartera_se_rechaza(self) -> None:
        ruta = _xlsx(self.dir / "ordenes.xlsx", [{"ID": 1, "ESTATUS": "ENTREGADO"}])
        with self.assertRaises(ic.ExportInvalido):
            ic.ingerir(str(ruta), destino=str(self.destino))

    def test_retiros_sin_clasificar_se_listan(self) -> None:
        filas = _historial() + [_mov(31, "10-10-2026 10:00", "SALIDA", 70.0, 500.0, desc=DESC_RET,
                                     concepto="pago algo raro")]
        res = self._ingerir(filas=filas, escribir=False)
        self.assertEqual([r["concepto_retiro"] for r in res["retiros_sin_clasificar"]], ["pago algo raro"])


class ClasificarRetiro(unittest.TestCase):
    def test_calza_por_texto_sin_distinguir_mayusculas(self) -> None:
        self.assertEqual(gen_pl.clasificar_retiro("Retiro PAPA", REGLAS), "RETIRO_PERSONAL")
        self.assertEqual(gen_pl.clasificar_retiro("Retiro a LLC DFF VENTURES RETIRO PROPIO", REGLAS),
                         "TRANSFERENCIA_PROPIA")

    def test_lo_que_no_calza_queda_sin_clasificar(self) -> None:
        self.assertEqual(gen_pl.clasificar_retiro("pago de algo", REGLAS), "SIN_CLASIFICAR")
        self.assertEqual(gen_pl.clasificar_retiro("", REGLAS), "SIN_CLASIFICAR")
        self.assertEqual(gen_pl.clasificar_retiro(None, REGLAS), "SIN_CLASIFICAR")

    def test_sin_reglas_nada_se_adivina(self) -> None:
        self.assertEqual(gen_pl.clasificar_retiro("Retiro papa", []), "SIN_CLASIFICAR")


if __name__ == "__main__":
    unittest.main()
