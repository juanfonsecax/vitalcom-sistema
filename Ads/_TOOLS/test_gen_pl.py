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


class LecturaCompletaDelExtracto(unittest.TestCase):
    """`movimientos_completos_del_extracto` agrega depositos y saldo SIN tocar el contrato de
    `movimientos_del_extracto` (solo salidas)."""

    def test_trae_salidas_y_depositos_con_tipo_y_saldo(self) -> None:
        mov, resumen = gen_pl.movimientos_completos_del_extracto(EXTRACTO_CON_SIGNO)
        self.assertEqual(
            [(m["nombre"], m["monto"], m["tipo"], m["saldo"]) for m in mov],
            [("Facebook", 30.64, "SALIDA", 111.25),
             ("RUBI WEALTH CORPORATION", 1000.00, "ENTRADA", 1015.49),
             ("THE LUCID HOLDING", 1044.00, "SALIDA", 958.80)])
        self.assertEqual(resumen, {"apertura": 1525.73, "cierre": 111.25,
                                   "depositos": 1000.00, "retiros": 2414.48})

    def test_formato_sin_signo_todo_es_salida(self) -> None:
        mov, resumen = gen_pl.movimientos_completos_del_extracto(EXTRACTO_SIN_SIGNO)
        self.assertEqual([(m["tipo"], m["saldo"]) for m in mov], [("SALIDA", 400.00)])
        self.assertEqual(resumen["retiros"], 100.00)

    def test_el_contrato_de_solo_salidas_no_cambia(self) -> None:
        mov, _ = gen_pl.movimientos_del_extracto(EXTRACTO_CON_SIGNO)
        self.assertEqual(set(mov[0]), {"nombre", "fecha", "monto"})
        self.assertEqual(len(mov), 2)


def _gasto(pk, ini, spend, ventas=0.0, fuente="MetaAPI-conjunto", cuenta="598687956219141"):
    return {"producto_key": pk, "cuenta_id": cuenta, "ventana_ini": ini, "ventana_fin": ini,
            "conjunto": "C", "ventas": ventas, "mensajes": 0.0, "spend_usd": spend,
            "spend_usd_lucidsales": 0.0, "fuente_gasto": fuente, "tiene_fila_ventas": True}


class PautaDeMeta(unittest.TestCase):
    """La pauta sale de gasto.py (Meta), con LucidSales solo donde Meta no cubre."""

    def test_suma_meta_y_fallback_por_separado_y_convierte_con_la_tasa_del_producto(self) -> None:
        filas = [_gasto("TINNIDROP", "2026-09-02", 100.0, ventas=2),
                 _gasto("CLEARSTEM", "2026-09-03", 50.0, ventas=1),
                 _gasto("CLEARSTEM", "2026-09-04", 20.0, fuente="LucidSales-fallback")]
        p = gen_pl.pauta_de_la_ventana("2026-09-01", "2026-09-30", filas)
        self.assertAlmostEqual(p["usd"], 170.0)
        self.assertAlmostEqual(p["meta_usd"], 150.0)
        self.assertAlmostEqual(p["fallback_usd"], 20.0)
        self.assertAlmostEqual(p["q"], 170.0 * gen_pl.TASA_Q)
        self.assertEqual(p["ventas_por_producto"]["TINNIDROP"], 2)
        self.assertAlmostEqual(p["q_por_producto"]["CLEARSTEM"], 70.0 * gen_pl.TASA_Q)

    def test_ignora_otras_ventanas_y_otros_mercados(self) -> None:
        filas = [_gasto("TINNIDROP", "2026-08-31", 10.0), _gasto("TINNIDROP", "2026-10-01", 10.0),
                 _gasto("OVULOS_PURITY", "2026-09-05", 99.0), _gasto("TINNIDROP", "2026-09-05", 5.0)]
        p = gen_pl.pauta_de_la_ventana("2026-09-01", "2026-09-30", filas)
        self.assertAlmostEqual(p["usd"], 5.0)

    def test_excluye_las_cuentas_pedidas(self) -> None:
        filas = [_gasto("TINNIDROP", "2026-09-05", 5.0, cuenta="1346891653335162.0"),
                 _gasto("TINNIDROP", "2026-09-05", 7.0)]
        p = gen_pl.pauta_de_la_ventana("2026-09-01", "2026-09-30", filas,
                                       excluir_cuentas=("1346891653335162",))
        self.assertAlmostEqual(p["usd"], 7.0)

    def test_un_producto_sin_fila_en_el_sistema_bloquea(self) -> None:
        with self.assertRaises(gen_pl.mercado.MercadoError):
            gen_pl.pauta_de_la_ventana("2026-09-01", "2026-09-30",
                                       [_gasto("NO_EXISTE", "2026-09-05", 5.0)])


class ReparteDeGastosCompartidos(unittest.TestCase):
    def test_un_gasto_de_un_mercado_va_entero_a_ese_mercado(self) -> None:
        self.assertEqual(gen_pl.parte_de_mercado("GT", "GT", {"GT", "CO"}), 1.0)
        self.assertEqual(gen_pl.parte_de_mercado("GT", "CO", {"GT", "CO"}), 0.0)

    def test_compartido_se_reparte_en_partes_iguales_entre_los_mercados_activos(self) -> None:
        self.assertEqual(gen_pl.parte_de_mercado("COMPARTIDO", "GT", {"GT"}), 1.0)
        self.assertEqual(gen_pl.parte_de_mercado("COMPARTIDO", "GT", {"GT", "CO"}), 0.5)
        self.assertEqual(gen_pl.parte_de_mercado("COMPARTIDO", "CO", {"GT"}), 0.0)

    def test_sin_mercado_declarado_cuenta_como_compartido(self) -> None:
        self.assertEqual(gen_pl.parte_de_mercado("", "GT", {"GT", "CO"}), 0.5)


def _ordenes_df(desde):
    import pandas as pd
    filas = [_fila(1, "CLEARSTEM.VT", "ENTREGADO", desde, 250.0, 30.0, 60.0),
             _fila(2, "CLEARSTEM.VT", "ENTREGADO", desde, 300.0, 30.0, 70.0),
             _fila(3, "CLEARSTEM.VT", "DEVOLUCION", desde, 250.0, 30.0, 60.0)]
    df = pd.DataFrame(filas)
    df["pk"] = df["PRODUCTO"].map(gen_pl.pk_dropi)
    df["f_orden"] = pd.to_datetime(df["FECHA"], format="%d-%m-%Y")
    df["f_mov"] = df["f_orden"]
    return df


REGLAS = [
    {"patron": "Facebook", "clasificacion": "NEGOCIO_PAUTA", "categoria": "publicidad", "mercado": "COMPARTIDO"},
    {"patron": "LUCIDSALES", "clasificacion": "NEGOCIO_FIJO", "categoria": "software", "mercado": "COMPARTIDO"},
    {"patron": "SOLO_CO", "clasificacion": "NEGOCIO_FIJO", "categoria": "software", "mercado": "CO"},
    {"patron": "MINIMED", "clasificacion": "PERSONAL", "categoria": "retiro_socio", "mercado": "COMPARTIDO"},
]
MOV = [
    {"nombre": "Facebook", "fecha": datetime.date(2024, 1, 2), "monto": 100.0},
    {"nombre": "LUCIDSALES, LLC", "fecha": datetime.date(2024, 1, 2), "monto": 26.0},
    {"nombre": "SOLO_CO", "fecha": datetime.date(2024, 1, 2), "monto": 10.0},
    {"nombre": "MINIMED X", "fecha": datetime.date(2024, 1, 2), "monto": 50.0},
    {"nombre": "COSA NUEVA", "fecha": datetime.date(2024, 1, 2), "monto": 3.0},
    {"nombre": "LUCIDSALES, LLC", "fecha": datetime.date(2024, 2, 2), "monto": 26.0},
]


class FormulaDeLaVentana(unittest.TestCase):
    def _calcular(self, activos):
        pauta = gen_pl.pauta_de_la_ventana("2024-01-01", "2024-01-31", [])
        return gen_pl.calcular_vista_a(_ordenes_df(datetime.date(2024, 1, 1)), "2024-01-01",
                                       "2024-01-31", datetime.date(2024, 6, 1), pauta,
                                       mov=MOV, reglas=REGLAS, activos=activos)

    def test_los_fijos_compartidos_se_reparten_y_los_de_otro_mercado_no_entran(self) -> None:
        r = self._calcular({"GT", "CO"})
        self.assertAlmostEqual(r.fijos, 26.0 * 0.5 * gen_pl.TASA_Q)
        self.assertEqual([d["nombre"] for d in r.det_fijos], ["LUCIDSALES, LLC"])

    def test_con_un_solo_mercado_activo_el_fijo_entra_entero(self) -> None:
        r = self._calcular({"GT"})
        self.assertAlmostEqual(r.fijos, 26.0 * gen_pl.TASA_Q)

    def test_el_retiro_personal_no_toca_el_resultado_y_la_pauta_del_banco_no_se_resta_dos_veces(self) -> None:
        r = self._calcular({"GT"})
        self.assertAlmostEqual(r.retiros, 50.0 * gen_pl.TASA_Q)
        self.assertAlmostEqual(r.neto, r.m_oper - r.fijos)
        self.assertEqual([n for n, _ in r.sin_confirmar], ["COSA NUEVA"])

    def test_la_formula_es_la_de_siempre(self) -> None:
        r = self._calcular({"GT"})
        venta, costo, flete = 550.0, 130.0, 60.0
        contrib = venta - costo - flete - gen_pl.C_DEVOL - 2 * gen_pl.C_ADMIN - 2 * gen_pl.C_OTROS
        self.assertAlmostEqual(r.m_contr, contrib)
        self.assertEqual((len(r.ent), len(r.dev)), (2, 1))

    def test_sin_ordenes_en_la_ventana_devuelve_none(self) -> None:
        pauta = gen_pl.pauta_de_la_ventana("2023-01-01", "2023-01-31", [])
        self.assertIsNone(gen_pl.calcular_vista_a(_ordenes_df(datetime.date(2024, 1, 1)),
                                                  "2023-01-01", "2023-01-31",
                                                  datetime.date(2024, 6, 1), pauta))


class ReportePorCli(unittest.TestCase):
    def test_el_json_declara_de_donde_sale_la_pauta(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            xlsx = Path(d) / "ordenes.xlsx"
            ini_d = datetime.date(2024, 3, 1)
            _dropi_de_juguete(xlsx, ini_d)
            proc = _correr(xlsx, ini_d.isoformat(), (ini_d + datetime.timedelta(days=2)).isoformat())
            try:
                self.assertEqual(proc.returncode, 0, proc.stderr)
                er = json.loads(proc.stdout)["vista_a_cohorte"]["estado_de_resultados"]
                self.assertEqual(set(er["publicidad_fuente"]), {"meta_usd", "lucidsales_fallback_usd"})
                self.assertAlmostEqual(er["publicidad_fuente"]["meta_usd"]
                                       + er["publicidad_fuente"]["lucidsales_fallback_usd"],
                                       er["publicidad_usd"])
            finally:
                for suf in ("txt", "json"):
                    f = AUD / ("_PL_20240301_20240303." + suf)
                    if f.is_file():
                        f.unlink()


if __name__ == "__main__":
    unittest.main()
