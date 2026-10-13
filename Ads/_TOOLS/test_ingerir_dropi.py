#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_ingerir_dropi.py — gate de ingerir_dropi.py.

Un export de Dropi es una ventana movil: cada ingesta hace UPSERT por ID de orden en
`_FACT_ORDENES_DROPI.csv` (el export mas nuevo pisa estatus y montos; las ordenes que el export
nuevo ya no trae se conservan). Re-ingerir el mismo archivo no cambia nada. Corre sobre un Dropi de
juguete y una carpeta temporal: nunca toca PRODUCTOS/.
"""
import csv
import os
import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ingerir_dropi as idr  # noqa: E402


def _orden(id_, estatus="ENTREGADO", fecha="03-09-2026", producto="CLEARSTEM.VT",
           total=239.0, flete=38.05, proveedor=82.0, reporte="13-10-2026"):
    ganancia = total - flete - proveedor if estatus == "ENTREGADO" else None
    return {"FECHA DE REPORTE": reporte, "ID": id_, "FECHA": fecha,
            "FECHA DE ÚLTIMO MOVIMIENTO": fecha, "ESTATUS": estatus,
            "TOTAL DE LA ORDEN": total, "GANANCIA": ganancia, "PRECIO FLETE": flete,
            "PRECIO PROVEEDOR X CANTIDAD": proveedor, "PRODUCTO": producto, "CANTIDAD": 2}


def _xlsx(ruta, filas):
    pd.DataFrame(filas).to_excel(ruta, index=False)
    return ruta


def _leer(ruta):
    with open(ruta, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


class IngestaDropi(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.destino = self.dir / "_FACT_ORDENES_DROPI.csv"

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _ingerir(self, nombre, filas, escribir=True):
        ruta = _xlsx(self.dir / nombre, filas)
        return idr.ingerir(str(ruta), destino=str(self.destino), escribir=escribir)

    def test_una_fila_por_orden_con_producto_y_mercado(self) -> None:
        self._ingerir("ordenes_productos_20261013_083238.xlsx", [
            _orden(1), _orden(2, producto="Spray para Oídos (Tinnidrop / Alivio)"),
            _orden(3, estatus="DEVOLUCION")])
        filas = {f["orden_id"]: f for f in _leer(self.destino)}
        self.assertEqual(set(filas), {"1", "2", "3"})
        self.assertEqual(filas["1"]["producto_key"], "CLEARSTEM")
        self.assertEqual(filas["2"]["producto_key"], "TINNIDROP")
        self.assertEqual(filas["1"]["mercado"], "GT")
        self.assertEqual(filas["1"]["fecha_orden"], "2026-09-03")
        self.assertEqual(filas["1"]["total_q"], "239.00")
        self.assertEqual(filas["1"]["costo_proveedor_q"], "82.00")
        self.assertEqual(filas["1"]["ganancia_q"], "118.95")
        self.assertEqual(filas["3"]["ganancia_q"], "")
        self.assertEqual(filas["1"]["fecha_reporte"], "2026-10-13")

    def test_la_orden_repetida_dentro_del_export_cuenta_una_vez(self) -> None:
        resumen = self._ingerir("ordenes_productos_20261013_083238.xlsx",
                                [_orden(7, estatus="CANCELADO"), _orden(7, estatus="CANCELADO")])
        self.assertEqual(len(_leer(self.destino)), 1)
        self.assertEqual(resumen["nuevas"], 1)

    def test_reingerir_el_mismo_archivo_no_cambia_nada(self) -> None:
        filas = [_orden(1), _orden(2, estatus="DEVOLUCION")]
        self._ingerir("ordenes_productos_20261013_083238.xlsx", filas)
        antes = self.destino.read_bytes()
        resumen = self._ingerir("ordenes_productos_20261013_083238.xlsx", filas)
        self.assertEqual(self.destino.read_bytes(), antes)
        self.assertEqual((resumen["nuevas"], resumen["actualizadas"]), (0, 0))

    def test_export_mas_nuevo_pisa_estatus_y_montos_y_conserva_las_que_ya_no_trae(self) -> None:
        self._ingerir("ordenes_productos_20261013_083238.xlsx",
                      [_orden(1, estatus="EN RUTA"), _orden(2)])
        resumen = self._ingerir("ordenes_productos_20261020_090000.xlsx",
                                [_orden(1, estatus="ENTREGADO", reporte="20-10-2026"),
                                 _orden(3, reporte="20-10-2026")])
        filas = {f["orden_id"]: f for f in _leer(self.destino)}
        self.assertEqual(set(filas), {"1", "2", "3"})
        self.assertEqual(filas["1"]["estatus"], "ENTREGADO")
        self.assertEqual(filas["1"]["fecha_reporte"], "2026-10-20")
        self.assertEqual(filas["2"]["fecha_reporte"], "2026-10-13")
        self.assertEqual((resumen["nuevas"], resumen["actualizadas"]), (1, 1))

    def test_un_export_mas_viejo_no_pisa_a_uno_mas_nuevo(self) -> None:
        self._ingerir("ordenes_productos_20261020_090000.xlsx",
                      [_orden(1, estatus="ENTREGADO", reporte="20-10-2026")])
        resumen = self._ingerir("ordenes_productos_20261013_083238.xlsx",
                                [_orden(1, estatus="EN RUTA")])
        self.assertEqual(_leer(self.destino)[0]["estatus"], "ENTREGADO")
        self.assertEqual(resumen["actualizadas"], 0)
        self.assertEqual(resumen["omitidas_por_viejas"], 1)

    def test_sin_columna_de_reporte_usa_la_fecha_del_nombre_del_archivo(self) -> None:
        fila = _orden(1)
        del fila["FECHA DE REPORTE"]
        self._ingerir("ordenes_productos_20261013_083238.xlsx", [fila])
        self.assertEqual(_leer(self.destino)[0]["fecha_reporte"], "2026-10-13")

    def test_sin_escribir_solo_mira(self) -> None:
        resumen = self._ingerir("ordenes_productos_20261013_083238.xlsx", [_orden(1)],
                                escribir=False)
        self.assertFalse(self.destino.exists())
        self.assertEqual(resumen["nuevas"], 1)

    def test_un_export_sin_las_columnas_esperadas_se_rechaza(self) -> None:
        ruta = _xlsx(self.dir / "ordenes_productos_20261013_083238.xlsx",
                     [{"ID": 1, "ESTATUS": "ENTREGADO"}])
        with self.assertRaises(idr.ExportInvalido):
            idr.ingerir(str(ruta), destino=str(self.destino), escribir=True)
        self.assertFalse(self.destino.exists())

    def test_una_orden_sin_producto_conocido_queda_otro_en_el_mercado_dado(self) -> None:
        self._ingerir("ordenes_productos_20261013_083238.xlsx",
                      [_orden(9, producto="Cosa rara")])
        fila = _leer(self.destino)[0]
        self.assertEqual((fila["producto_key"], fila["mercado"]), ("OTRO", "GT"))


if __name__ == "__main__":
    unittest.main()
