#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_ingerir_banco.py — gate de ingerir_banco.py.

Cada movimiento de un extracto (salidas Y depositos) queda en `_FACT_BANCO.csv`. Un extracto cuyo
resumen no cuadra con sus movimientos, o que es de otra cuenta que la declarada, se rechaza sin
escribir. La llave de dedupe es (banco, cuenta, fecha, nombre, monto, saldo): re-ingerir el mismo
extracto no cambia nada. Corre sobre texto sintetico y una carpeta temporal: nunca toca PRODUCTOS/.
"""
import csv
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ingerir_banco as ib  # noqa: E402

EXTRACTO = """Business Checking Account Statement
DFF TEST LLC | Sep 1 - Sep 30, 2026
Account Number: XXXXXX-8889
SUMMARY
Opening Balance Closing Balance Deposits Withdrawals
$1,525.73 $111.25 +$1,000.00 -$2,414.48
Name Date Status Amount Balance
Facebook
Oct 1, 2026 Settled -$30.64 $111.25
VISA
RUBI WEALTH CORPORATION
Sep 21, 2026 Settled +$1,000.00 $1,015.49
Wire
THE LUCID HOLDING
Sep 22, 2026 Settled -$1,044.00 $958.80
VISA
Facebook
Sep 5, 2026 Settled -$1,339.84 $1,002.20
VISA
"""

# Mismo extracto con el resumen que de verdad cuadra: 30.64 + 1044.00 + 1339.84 = 2414.48
assert abs(30.64 + 1044.00 + 1339.84 - 2414.48) < 0.001


def _leer(ruta):
    with open(ruta, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


class IngestaBanco(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.destino = Path(self.tmp.name) / "_FACT_BANCO.csv"

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _ingerir(self, texto=EXTRACTO, cuenta="8889", escribir=True, nombre="Relay 2026-09-01 #8889.pdf"):
        return ib.ingerir_texto(texto, archivo=nombre, banco="RELAY", cuenta=cuenta,
                                destino=str(self.destino), escribir=escribir)

    def test_guarda_salidas_y_depositos_con_su_saldo(self) -> None:
        res = self._ingerir()
        filas = _leer(self.destino)
        self.assertEqual(len(filas), 4)
        self.assertEqual((res["nuevas"], res["salidas"], res["entradas"]), (4, 3, 1))
        d = {(f["fecha"], f["nombre"]): f for f in filas}
        fb = d[("2026-10-01", "Facebook")]
        self.assertEqual((fb["banco"], fb["cuenta"], fb["monto"], fb["tipo"], fb["saldo"]),
                         ("RELAY", "8889", "30.64", "SALIDA", "111.25"))
        self.assertEqual(fb["tarjeta"], "")
        self.assertEqual(fb["archivo"], "Relay 2026-09-01 #8889.pdf")
        dep = d[("2026-09-21", "RUBI WEALTH CORPORATION")]
        self.assertEqual((dep["tipo"], dep["monto"]), ("ENTRADA", "1000.00"))

    def test_reingerir_el_mismo_extracto_no_cambia_nada(self) -> None:
        self._ingerir()
        antes = self.destino.read_bytes()
        res = self._ingerir()
        self.assertEqual(self.destino.read_bytes(), antes)
        self.assertEqual((res["nuevas"], res["duplicadas"]), (0, 4))

    def test_dos_cargos_iguales_el_mismo_dia_se_distinguen_por_el_saldo(self) -> None:
        texto = """Account Number: XXXXXX-8889
Opening Balance Closing Balance Deposits Withdrawals
$100.00 $80.00 +$0.00 -$20.00
Facebook
Sep 5, 2026 Settled -$10.00 $90.00
VISA
Facebook
Sep 5, 2026 Settled -$10.00 $80.00
VISA
"""
        self._ingerir(texto)
        self.assertEqual(len(_leer(self.destino)), 2)

    def test_un_extracto_que_no_cuadra_con_su_resumen_se_rechaza_sin_escribir(self) -> None:
        roto = EXTRACTO.replace("-$2,414.48", "-$2,000.00")
        with self.assertRaises(ib.ExtractoInvalido):
            self._ingerir(roto)
        self.assertFalse(self.destino.exists())

    def test_un_extracto_de_otra_cuenta_se_rechaza(self) -> None:
        with self.assertRaises(ib.ExtractoInvalido):
            self._ingerir(cuenta="8890")
        self.assertFalse(self.destino.exists())

    def test_extracto_sin_movimientos_no_escribe_filas_y_lo_dice(self) -> None:
        vacio = """Account Number: XXXXXX-8890
Opening Balance Closing Balance Deposits Withdrawals
$0.00 $0.00 +$0.00 -$0.00
Name Date Status Amount Balance
"""
        res = self._ingerir(vacio, cuenta="8890", nombre="Relay 2026-09-01 #8890.pdf")
        self.assertEqual(res["nuevas"], 0)
        self.assertEqual(_leer(self.destino), [])

    def test_sin_cuenta_declarada_la_toma_del_extracto(self) -> None:
        res = self._ingerir(cuenta=None)
        self.assertEqual(res["cuenta"], "8889")
        self.assertEqual({f["cuenta"] for f in _leer(self.destino)}, {"8889"})

    def test_sin_cuenta_y_sin_numero_en_el_extracto_se_rechaza(self) -> None:
        sin_numero = "\n".join(l for l in EXTRACTO.split("\n") if not l.startswith("Account Number"))
        with self.assertRaises(ib.ExtractoInvalido):
            self._ingerir(sin_numero, cuenta=None)
        self.assertFalse(self.destino.exists())

    def test_json_imprime_solo_el_resumen(self) -> None:
        import contextlib, io, json
        from unittest import mock
        with tempfile.TemporaryDirectory() as d:
            pdf = Path(d) / "Relay 2026-09-01 #8889.pdf"
            pdf.write_bytes(b"%PDF")
            salida = io.StringIO()
            with mock.patch.object(ib, "texto_del_pdf", return_value=EXTRACTO),                     mock.patch.object(ib.csv_hechos, "leer", return_value=[]),                     contextlib.redirect_stdout(salida):
                rc = ib.main(["--archivo", str(pdf), "--banco", "relay", "--json"])
        self.assertEqual(rc, 0)
        resumen = json.loads(salida.getvalue())
        self.assertEqual((resumen["nuevas"], resumen["cuenta"], resumen["escrito"]), (4, "8889", False))

    def test_sin_escribir_solo_mira(self) -> None:
        res = self._ingerir(escribir=False)
        self.assertFalse(self.destino.exists())
        self.assertEqual(res["nuevas"], 4)

    def test_extracto_sin_resumen_no_se_puede_validar_y_se_rechaza(self) -> None:
        sin_resumen = "\n".join(l for l in EXTRACTO.split("\n") if not l.startswith("$1,525.73"))
        with self.assertRaises(ib.ExtractoInvalido):
            self._ingerir(sin_resumen)


if __name__ == "__main__":
    unittest.main()
