#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_tasa_fx.py — gate de la tasa efectiva Dropi -> banco y de su registro.

La tasa de un mes sale de las transferencias propias (quetzales retirados de la billetera de Dropi
contra los dólares que llegaron al banco): promedio ponderado por USD de las que salieron en la
ventana que termina el último día del mes; si no hay, la última anterior; si no hay ninguna
previa, la primera posterior; si no existe ninguna, el parámetro. Corre sobre datos de juguete y
carpetas temporales: nunca toca PRODUCTOS/.
"""
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import csv_hechos                       # noqa: E402
import registrar_transferencia_fx as rt  # noqa: E402
import tasa_fx                          # noqa: E402

PARAM = 7.62


def _par(salida, q, usd, llegada="", mov="1"):
    return {"fecha_salida": salida, "monto_q": "%.2f" % q, "fecha_llegada": llegada,
            "monto_usd": "%.2f" % usd, "banco_destino": "MERCURY", "origen_salida": mov,
            "origen_llegada": "operador", "confirmado_por": "operador"}


class TasaDelMes(unittest.TestCase):
    def test_la_tasa_de_una_transferencia_es_q_sobre_usd(self) -> None:
        self.assertAlmostEqual(tasa_fx.tasa_de(_par("2026-10-01", 90000, 11381)), 7.9079, places=4)

    def test_sin_transferencias_manda_el_parametro(self) -> None:
        t = tasa_fx.tasa_del_mes("2026-10-31", [], PARAM, 90)
        self.assertEqual((t["valor"], t["regla"], t["transferencias"]), (PARAM, "PARAMETRO", 0))

    def test_ventana_pondera_por_usd_las_que_salieron_en_los_ultimos_dias(self) -> None:
        trs = [_par("2026-09-10", 7800, 1000, mov="1"),      # 7.80
               _par("2026-10-01", 39000, 5000, mov="2")]     # 7.80 -> mismo; distinta para ver el peso
        trs[0]["monto_q"] = "8000.00"                         # 8.00 con 1,000
        trs[1]["monto_q"] = "38000.00"                        # 7.60 con 5,000
        t = tasa_fx.tasa_del_mes("2026-10-31", trs, PARAM, 90)
        self.assertEqual(t["regla"], "VENTANA")
        self.assertAlmostEqual(t["valor"], (8000 + 38000) / 6000, places=6)
        self.assertEqual((t["transferencias"], t["usd"]), (2, 6000.0))

    def test_una_transferencia_fuera_de_la_ventana_no_pesa_pero_sirve_de_ultima_conocida(self) -> None:
        trs = [_par("2026-05-01", 8000, 1000)]
        t = tasa_fx.tasa_del_mes("2026-10-31", trs, PARAM, 90)
        self.assertEqual((t["regla"], t["valor"], t["transferencias"]), ("ULTIMA_CONOCIDA", 8.0, 1))
        self.assertEqual(t["desde"], "2026-05-01")

    def test_la_ventana_termina_el_ultimo_dia_del_mes_y_una_posterior_no_entra_en_ventana(self) -> None:
        trs = [_par("2026-10-01", 90000, 11381)]
        t = tasa_fx.tasa_del_mes("2026-09-30", trs, PARAM, 90)
        self.assertEqual((t["regla"], t["valor"]), ("PRIMERA_POSTERIOR", 90000 / 11381))

    def test_mes_sin_previas_usa_la_primera_posterior(self) -> None:
        trs = [_par("2026-10-01", 90000, 11381)]
        t = tasa_fx.tasa_del_mes("2026-09-30", trs, PARAM, 90)
        self.assertEqual(t["regla"], "PRIMERA_POSTERIOR")
        self.assertAlmostEqual(t["valor"], 90000 / 11381, places=4)
        self.assertEqual((t["transferencias"], t["desde"], t["hasta"]), (1, "2026-10-01", "2026-10-01"))

    def test_con_varias_posteriores_manda_la_primera(self) -> None:
        trs = [_par("2026-11-01", 8000, 1000), _par("2026-10-01", 90000, 11381)]
        t = tasa_fx.tasa_del_mes("2026-09-30", trs, PARAM, 90)
        self.assertEqual((t["regla"], t["desde"]), ("PRIMERA_POSTERIOR", "2026-10-01"))
        self.assertAlmostEqual(t["valor"], 90000 / 11381, places=4)

    def test_una_anterior_manda_sobre_una_posterior(self) -> None:
        trs = [_par("2026-05-01", 8000, 1000), _par("2026-10-01", 90000, 11381)]
        t = tasa_fx.tasa_del_mes("2026-09-30", trs, PARAM, 90)
        self.assertEqual((t["regla"], t["valor"]), ("ULTIMA_CONOCIDA", 8.0))

    def test_una_posterior_sin_usd_no_cuenta_y_cae_al_parametro(self) -> None:
        malo = _par("2026-10-01", 90000, 1)
        malo["monto_usd"] = ""
        t = tasa_fx.tasa_del_mes("2026-09-30", [malo], PARAM, 90)
        self.assertEqual(t["regla"], "PARAMETRO")

    def test_el_dia_final_de_la_ventana_entra_y_el_dia_anterior_al_inicio_no(self) -> None:
        # ventana de 90 dias que termina el 2026-10-31 -> 2026-08-03 .. 2026-10-31
        dentro = tasa_fx.tasa_del_mes("2026-10-31", [_par("2026-08-03", 8000, 1000)], PARAM, 90)
        fuera = tasa_fx.tasa_del_mes("2026-10-31", [_par("2026-08-02", 8000, 1000)], PARAM, 90)
        self.assertEqual(dentro["regla"], "VENTANA")
        self.assertEqual(fuera["regla"], "ULTIMA_CONOCIDA")

    def test_una_fila_sin_usd_no_se_toma(self) -> None:
        malo = _par("2026-10-01", 90000, 1)
        malo["monto_usd"] = ""
        t = tasa_fx.tasa_del_mes("2026-10-31", [malo], PARAM, 90)
        self.assertEqual(t["regla"], "PARAMETRO")


def _cart(mov_id, fecha, monto, concepto="Retiro a LLC DFF VENTURES RETIRO PROPIO", cat="RETIRO"):
    return {"mov_id": str(mov_id), "fecha": fecha, "hora": "08:28", "tipo": "SALIDA",
            "monto_q": "%.2f" % monto, "categoria": cat, "concepto_retiro": concepto, "mercado": "GT"}


def _ban(fecha, monto, nombre="Mercury in", tipo="ENTRADA", cuenta="1234", banco="MERCURY"):
    return {"fecha": fecha, "banco": banco, "cuenta": cuenta, "nombre": nombre,
            "monto": "%.2f" % monto, "tipo": tipo, "saldo": "", "tarjeta": "", "archivo": "m.csv"}


REGLAS = [{"patron": "DFF VENTURES", "clasificacion": "TRANSFERENCIA_PROPIA"},
          {"patron": "papa", "clasificacion": "RETIRO_PERSONAL"}]


class EmparejarConElBanco(unittest.TestCase):
    def test_una_entrada_en_banda_y_en_plazo_se_empareja(self) -> None:
        r = rt.parear_automatico([_cart(10, "2026-10-01", 90000)], [_ban("2026-10-05", 11381)], REGLAS, [])
        self.assertEqual(len(r["pares"]), 1)
        p = r["pares"][0]
        self.assertEqual((p["origen_salida"], p["fecha_llegada"], p["monto_usd"], p["confirmado_por"]),
                         ("10", "2026-10-05", "11381.00", "auto"))
        self.assertIn("MERCURY", p["origen_llegada"])

    def test_los_retiros_personales_no_se_emparejan(self) -> None:
        r = rt.parear_automatico([_cart(10, "2026-10-01", 5000, concepto="Retiro papa")],
                                 [_ban("2026-10-02", 650)], REGLAS, [])
        self.assertEqual((r["pares"], r["ambiguos"], r["sin_par"]), ([], [], []))

    def test_fuera_de_la_banda_de_tasa_no_se_empareja(self) -> None:
        r = rt.parear_automatico([_cart(10, "2026-10-01", 90000)], [_ban("2026-10-03", 5000)], REGLAS, [])
        self.assertEqual(r["pares"], [])
        self.assertEqual([x["mov_id"] for x in r["sin_par"]], ["10"])

    def test_fuera_del_plazo_no_se_empareja(self) -> None:
        # 2026-10-01 es jueves: 5 dias habiles llegan hasta el 2026-10-08
        ok = rt.parear_automatico([_cart(10, "2026-10-01", 90000)], [_ban("2026-10-08", 11381)], REGLAS, [])
        tarde = rt.parear_automatico([_cart(10, "2026-10-01", 90000)], [_ban("2026-10-09", 11381)], REGLAS, [])
        antes = rt.parear_automatico([_cart(10, "2026-10-01", 90000)], [_ban("2026-09-30", 11381)], REGLAS, [])
        self.assertEqual((len(ok["pares"]), len(tarde["pares"]), len(antes["pares"])), (1, 0, 0))

    def test_dos_candidatas_es_ambiguo_y_no_se_empareja(self) -> None:
        r = rt.parear_automatico([_cart(10, "2026-10-01", 90000)],
                                 [_ban("2026-10-03", 11300), _ban("2026-10-04", 11400)], REGLAS, [])
        self.assertEqual(r["pares"], [])
        self.assertEqual(len(r["ambiguos"]), 1)
        self.assertEqual(len(r["ambiguos"][0]["candidatas"]), 2)

    def test_una_entrada_que_dos_retiros_reclaman_no_se_asigna_a_ninguno(self) -> None:
        r = rt.parear_automatico([_cart(10, "2026-10-01", 90000), _cart(11, "2026-10-02", 90000)],
                                 [_ban("2026-10-05", 11381)], REGLAS, [])
        self.assertEqual(r["pares"], [])
        self.assertEqual(len(r["ambiguos"]), 2)

    def test_un_retiro_ya_emparejado_no_se_toca(self) -> None:
        previo = [_par("2026-10-01", 90000, 11381, mov="10")]
        r = rt.parear_automatico([_cart(10, "2026-10-01", 90000)], [_ban("2026-10-05", 11000)], REGLAS, previo)
        self.assertEqual((r["pares"], r["ambiguos"], r["sin_par"]), ([], [], []))

    def test_una_salida_del_banco_no_cuenta_como_llegada(self) -> None:
        r = rt.parear_automatico([_cart(10, "2026-10-01", 90000)],
                                 [_ban("2026-10-03", 11381, tipo="SALIDA")], REGLAS, [])
        self.assertEqual(r["pares"], [])


class ParManual(unittest.TestCase):
    def test_el_par_del_operador_toma_la_salida_de_la_billetera(self) -> None:
        f = rt.par_manual([_cart(10, "2026-10-01", 90000)], REGLAS, "10", 11381.0, "", "MERCURY", "operador")
        self.assertEqual((f["fecha_salida"], f["monto_q"], f["monto_usd"], f["fecha_llegada"],
                          f["origen_llegada"], f["confirmado_por"]),
                         ("2026-10-01", "90000.00", "11381.00", "", "operador", "operador"))

    def test_un_retiro_que_no_es_transferencia_propia_se_rechaza(self) -> None:
        with self.assertRaises(rt.ErrorFx):
            rt.par_manual([_cart(10, "2026-10-01", 5000, concepto="Retiro papa")], REGLAS, "10", 650.0,
                          "", "MERCURY", "operador")

    def test_un_id_que_no_existe_se_rechaza(self) -> None:
        with self.assertRaises(rt.ErrorFx):
            rt.par_manual([_cart(10, "2026-10-01", 90000)], REGLAS, "99", 11381.0, "", "MERCURY", "operador")

    def test_una_tasa_fuera_de_banda_se_rechaza(self) -> None:
        with self.assertRaises(rt.ErrorFx):
            rt.par_manual([_cart(10, "2026-10-01", 90000)], REGLAS, "10", 1138.0, "", "MERCURY", "operador")


class Persistencia(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.dest = os.path.join(self.tmp.name, "_FACT_TRANSFERENCIAS_FX.csv")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_escribir_es_idempotente_y_el_operador_pisa_a_lo_automatico(self) -> None:
        a = _par("2026-10-01", 90000, 11381)
        a["confirmado_por"] = "auto"
        filas, r1 = rt.fusionar([], [a])
        self.assertEqual(r1["nuevas"], 1)
        csv_hechos.escribir(self.dest, rt.COLUMNAS, filas)
        antes = Path(self.dest).read_bytes()
        filas2, r2 = rt.fusionar(csv_hechos.leer(self.dest), [a])
        csv_hechos.escribir(self.dest, rt.COLUMNAS, filas2)
        self.assertEqual((r2["nuevas"], r2["sin_cambio"]), (0, 1))
        self.assertEqual(Path(self.dest).read_bytes(), antes)
        b = _par("2026-10-01", 90000, 11380, llegada="2026-10-03")
        filas3, r3 = rt.fusionar(filas2, [b])
        self.assertEqual((r3["actualizadas"], filas3[0]["monto_usd"]), (1, "11380.00"))

    def test_registrar_mirar_no_escribe_y_con_escribir_guarda(self) -> None:
        cartera = [_cart(10, "2026-10-01", 90000)]
        r = rt.registrar(cartera, [], REGLAS, self.dest, salida="10", usd=11381.0, escribir=False)
        self.assertFalse(os.path.exists(self.dest))
        self.assertEqual(len(r["pares"]), 1)
        rt.registrar(cartera, [], REGLAS, self.dest, salida="10", usd=11381.0, escribir=True)
        filas = csv_hechos.leer(self.dest)
        self.assertEqual([f["origen_salida"] for f in filas], ["10"])
        self.assertEqual(filas[0]["monto_usd"], "11381.00")


if __name__ == "__main__":
    unittest.main()
