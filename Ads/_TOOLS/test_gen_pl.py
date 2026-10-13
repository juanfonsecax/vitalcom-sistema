#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_gen_pl.py — Pruebas de `gen_pl.py --json` (T4a, 24-sep-2026).

Congela que el `--json` agregado es ADITIVO: los mismos números que ya se calculaban e
imprimían en el `.txt` (VISTA A · COHORTE — DOCTRINA/CONTABILIDAD.md §3) quedan serializados
en `_AUDITORIAS/_PL_<ini>_<fin>.json`, sin inventar ni recalcular nada, y la bandera de
cohorte PRELIMINAR (`dias_cohorte_maduro` de `_PARAMETROS_FINANZAS.csv`) viaja en el JSON
exactamente como decide el script.

Corre contra un Dropi de juguete (`ordenes.xlsx`) armado en el test con pandas/openpyxl, nunca
contra datos reales. Los parámetros de costo (`C_DEVOL`, `C_ADMIN`, `C_OTROS`,
`DIAS_MADURO`) SÍ salen del `_PARAMETROS_FINANZAS.csv` real del repo (gen_pl.py resuelve su
`ROOT` desde su propia ubicación en disco, no es inyectable) — el test los lee del propio
módulo importado, nunca los hardcodea, para no desincronizarse si el parámetro cambia.
"""
from __future__ import annotations

import datetime
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent.parent
SCRIPT = RAIZ / "Ads" / "_TOOLS" / "gen_pl.py"
AUD = RAIZ / "PRODUCTOS" / "_AUDITORIAS"

if str(SCRIPT.parent) not in sys.path:
    sys.path.insert(0, str(SCRIPT.parent))

import gen_pl  # noqa: E402


def _fila(id_, producto, estatus, fecha, total, flete, proveedor):
    ganancia = total - flete - proveedor if estatus == "ENTREGADO" else 0.0
    return {
        "ID": id_, "PRODUCTO": producto, "ESTATUS": estatus,
        "FECHA": fecha.strftime("%d-%m-%Y"),
        "FECHA DE ÚLTIMO MOVIMIENTO": fecha.strftime("%d-%m-%Y"),
        "TOTAL DE LA ORDEN": total, "PRECIO FLETE": flete,
        "PRECIO PROVEEDOR X CANTIDAD": proveedor, "GANANCIA": ganancia,
    }


def _dropi_de_juguete(ruta_xlsx, desde: datetime.date):
    """2 ENTREGADO + 1 DEVOLUCION, todas dentro de la ventana [desde, desde+2]."""
    filas = [
        _fila(1, "PRODUCTO DE PRUEBA", "ENTREGADO", desde, 250.0, 30.0, 60.0),
        _fila(2, "PRODUCTO DE PRUEBA", "ENTREGADO", desde + datetime.timedelta(days=1), 300.0, 30.0, 70.0),
        _fila(3, "PRODUCTO DE PRUEBA", "DEVOLUCION", desde + datetime.timedelta(days=2), 250.0, 30.0, 60.0),
    ]
    pd.DataFrame(filas).to_excel(ruta_xlsx, index=False)


def _correr(dropi_xlsx, ini, fin):
    cmd = [sys.executable, str(SCRIPT), "--dropi", str(dropi_xlsx),
           "--desde", ini, "--hasta", fin, "--json"]
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    return subprocess.run(cmd, cwd=str(RAIZ), env=env, capture_output=True,
                           text=True, encoding="utf-8", errors="replace", timeout=120)


class TestGenPlJson(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.dropi_xlsx = Path(self.temp_dir.name) / "ordenes.xlsx"
        self.escritos_antes = set(AUD.glob("_PL_*.json")) if AUD.is_dir() else set()

    def tearDown(self) -> None:
        # Limpia SOLO los .json que este test haya escrito de más (comparte _AUDITORIAS con
        # el sistema real: nunca se borra algo que no se creó en este test).
        for p in (set(AUD.glob("_PL_*.json")) if AUD.is_dir() else set()) - self.escritos_antes:
            p.unlink()
            txt_hermano = p.with_suffix(".txt")
            if txt_hermano.is_file():
                txt_hermano.unlink()
        self.temp_dir.cleanup()

    def test_cohorte_vieja_no_es_preliminar_y_los_numeros_cuadran_con_la_formula(self) -> None:
        """Ventana de hace años: madura. Los números del JSON son EXACTAMENTE la fórmula de
        VISTA A (§3), no un cálculo aparte — se recomponen acá con los parámetros reales del
        módulo, nunca hardcodeados."""
        ini_d = datetime.date(2024, 1, 1)
        fin_d = ini_d + datetime.timedelta(days=2)
        _dropi_de_juguete(self.dropi_xlsx, ini_d)
        proc = _correr(self.dropi_xlsx, ini_d.isoformat(), fin_d.isoformat())
        self.assertEqual(proc.returncode, 0, f"stdout={proc.stdout!r} stderr={proc.stderr!r}")

        datos = json.loads(proc.stdout)
        vista_a = datos["vista_a_cohorte"]
        self.assertFalse(vista_a["preliminar"])
        self.assertEqual(vista_a["dias_maduro_umbral"], gen_pl.DIAS_MADURO)
        self.assertGreaterEqual(vista_a["edad_dias"], gen_pl.DIAS_MADURO)
        self.assertEqual(vista_a["entregadas"], 2)
        self.assertEqual(vista_a["devueltas"], 1)

        er = vista_a["estado_de_resultados"]
        venta, costo, flete = 550.0, 130.0, 60.0
        margen_logistico = venta - costo - flete
        c_dev = 1 * gen_pl.C_DEVOL
        c_adm = 2 * gen_pl.C_ADMIN
        c_otr = 2 * gen_pl.C_OTROS
        margen_contribucion = margen_logistico - c_dev - c_adm - c_otr
        self.assertAlmostEqual(er["venta_bruta_entregada_q"], venta)
        self.assertAlmostEqual(er["costo_producto_q"], costo)
        self.assertAlmostEqual(er["flete_q"], flete)
        self.assertAlmostEqual(er["margen_logistico_q"], margen_logistico)
        self.assertAlmostEqual(er["costo_devoluciones_q"], c_dev)
        self.assertAlmostEqual(er["costo_personal_q"], c_adm)
        self.assertAlmostEqual(er["otros_gastos_q"], c_otr)
        self.assertAlmostEqual(er["margen_contribucion_q"], margen_contribucion)

        # el .json quedó escrito junto al .txt, con el mismo nombre base (T4a)
        base = "_PL_%s_%s" % (ini_d.isoformat().replace("-", ""), fin_d.isoformat().replace("-", ""))
        self.assertTrue((AUD / (base + ".json")).is_file())
        self.assertTrue((AUD / (base + ".txt")).is_file())
        en_disco = json.loads((AUD / (base + ".json")).read_text(encoding="utf-8"))
        self.assertEqual(en_disco, datos)

    def test_cohorte_reciente_se_marca_preliminar(self) -> None:
        """Ventana que termina hace 2 días: por debajo del umbral -> preliminar=True."""
        fin_d = datetime.date.today() - datetime.timedelta(days=2)
        ini_d = fin_d - datetime.timedelta(days=2)
        _dropi_de_juguete(self.dropi_xlsx, ini_d)
        proc = _correr(self.dropi_xlsx, ini_d.isoformat(), fin_d.isoformat())
        self.assertEqual(proc.returncode, 0, f"stdout={proc.stdout!r} stderr={proc.stderr!r}")

        datos = json.loads(proc.stdout)
        vista_a = datos["vista_a_cohorte"]
        self.assertTrue(vista_a["preliminar"])
        self.assertLess(vista_a["edad_dias"], gen_pl.DIAS_MADURO)

    def test_sin_flag_json_no_escribe_el_json(self) -> None:
        """Sin `--json` el comportamiento de siempre no cambia: solo el .txt, nunca el .json."""
        ini_d = datetime.date(2024, 2, 1)
        fin_d = ini_d + datetime.timedelta(days=2)
        _dropi_de_juguete(self.dropi_xlsx, ini_d)
        cmd = [sys.executable, str(SCRIPT), "--dropi", str(self.dropi_xlsx),
               "--desde", ini_d.isoformat(), "--hasta", fin_d.isoformat()]
        env = dict(os.environ, PYTHONIOENCODING="utf-8")
        proc = subprocess.run(cmd, cwd=str(RAIZ), env=env, capture_output=True,
                               text=True, encoding="utf-8", errors="replace", timeout=120)
        self.assertEqual(proc.returncode, 0, f"stdout={proc.stdout!r} stderr={proc.stderr!r}")
        base = "_PL_%s_%s" % (ini_d.isoformat().replace("-", ""), fin_d.isoformat().replace("-", ""))
        self.assertFalse((AUD / (base + ".json")).is_file())
        self.assertTrue((AUD / (base + ".txt")).is_file())
        (AUD / (base + ".txt")).unlink()


EXTRACTO_CON_SIGNO = """Business Checking Account Statement
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
"""

EXTRACTO_SIN_SIGNO = """Opening Balance Closing Balance Deposits Withdrawals
$500.00 $400.00 $0.00 $100.00
Facebook
Aug 3, 2026 Settled $100.00 $400.00
"""


class LecturaDelExtracto(unittest.TestCase):
    def test_formato_con_signo_lee_solo_salidas_y_el_control_de_withdrawals(self) -> None:
        mov, control = gen_pl.movimientos_del_extracto(EXTRACTO_CON_SIGNO)
        self.assertEqual([(m["nombre"], m["monto"]) for m in mov],
                         [("Facebook", 30.64), ("THE LUCID HOLDING", 1044.00)])
        self.assertEqual(mov[0]["fecha"], datetime.date(2026, 10, 1))
        self.assertEqual(control, 2414.48)

    def test_formato_viejo_sin_signo_sigue_funcionando(self) -> None:
        mov, control = gen_pl.movimientos_del_extracto(EXTRACTO_SIN_SIGNO)
        self.assertEqual([(m["nombre"], m["monto"]) for m in mov], [("Facebook", 100.00)])
        self.assertEqual(control, 100.00)


if __name__ == "__main__":
    unittest.main()
