#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_gen_pl_mensual.py — gate de gen_pl_mensual.py (estado de resultados mensual por mercado).

La fórmula es la de `gen_pl.py` (`calcular_vista_a`): el mensual solo arma las ventanas desde los
hechos persistidos (`_FACT_ORDENES_DROPI.csv`, `_FACT_BANCO.csv`, gasto de Meta). Corre sobre
hechos sintéticos inyectados: nunca depende de los datos reales de PRODUCTOS/.
"""
import datetime
import json
import os
import subprocess
import sys
import tempfile
import unittest
import unittest.mock as mock
from pathlib import Path

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_pl                # noqa: E402
import gen_pl_mensual as gpm  # noqa: E402
import ingerir_dropi         # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent.parent
SCRIPT = RAIZ / "Ads" / "_TOOLS" / "gen_pl_mensual.py"
SCRIPT_PL = RAIZ / "Ads" / "_TOOLS" / "gen_pl.py"
AUD = RAIZ / "PRODUCTOS" / "_AUDITORIAS"

HOY = datetime.date(2026, 10, 13)

REGLAS = [
    {"patron": "Facebook", "clasificacion": "NEGOCIO_PAUTA", "categoria": "publicidad", "mercado": "COMPARTIDO"},
    {"patron": "LUCIDSALES", "clasificacion": "NEGOCIO_FIJO", "categoria": "software", "mercado": "COMPARTIDO"},
    {"patron": "MINIMED", "clasificacion": "PERSONAL", "categoria": "retiro_socio", "mercado": "COMPARTIDO"},
]


def _orden(id_, fecha, estatus="ENTREGADO", pk="CLEARSTEM", total=250.0, flete=30.0, prov=60.0,
           mercado="GT"):
    gan = "%.2f" % (total - flete - prov) if estatus == "ENTREGADO" else ""
    return {"orden_id": str(id_), "fecha_orden": fecha, "fecha_movimiento": fecha,
            "estatus": estatus, "producto": pk, "producto_key": pk, "mercado": mercado,
            "cantidad": "1", "total_q": "%.2f" % total, "flete_q": "%.2f" % flete,
            "costo_proveedor_q": "%.2f" % prov, "ganancia_q": gan, "fecha_reporte": "2026-10-13",
            "archivo_origen": "x.xlsx"}


def _mov(fecha, nombre, monto, tipo="SALIDA", saldo="1.00", mercado="", tarjeta="", banco="RELAY"):
    return {"fecha": fecha, "banco": banco, "cuenta": "8889", "nombre": nombre,
            "monto": "%.2f" % monto, "tipo": tipo, "saldo": saldo, "tarjeta": tarjeta,
            "mercado": mercado, "archivo": "a.pdf"}


def _gasto(pk, ini, spend, ventas=0.0, fuente="MetaAPI-conjunto"):
    return {"producto_key": pk, "cuenta_id": "598687956219141", "ventana_ini": ini,
            "ventana_fin": ini, "conjunto": "C", "ventas": ventas, "mensajes": 0.0,
            "spend_usd": spend, "spend_usd_lucidsales": 0.0, "fuente_gasto": fuente,
            "tiene_fila_ventas": True}


def _hechos(ordenes=(), banco=(), gasto=()):
    return {"ordenes": list(ordenes), "banco": list(banco), "gasto": list(gasto), "reglas": REGLAS}


def _enero():
    return _hechos(
        ordenes=[_orden(1, "2024-01-02"), _orden(2, "2024-01-03", total=300.0, prov=70.0),
                 _orden(3, "2024-01-04", estatus="DEVOLUCION")],
        banco=[_mov("2024-01-05", "Facebook", 100.0), _mov("2024-01-06", "LUCIDSALES, LLC", 26.0),
               _mov("2024-01-07", "MINIMED X", 50.0)],
        gasto=[_gasto("CLEARSTEM", "2024-01-05", 20.0, ventas=2),
               _gasto("CLEARSTEM", "2024-01-06", 5.0, fuente="LucidSales-fallback")])


class MesesYFormula(unittest.TestCase):
    def test_los_meses_son_los_que_aparecen_en_cualquier_hecho(self) -> None:
        h = _hechos(ordenes=[_orden(1, "2024-01-02")], banco=[_mov("2024-02-02", "Facebook", 1.0)],
                    gasto=[_gasto("CLEARSTEM", "2024-03-05", 3.0)])
        r = gpm.pl_mensual("GT", hoy=HOY, hechos=h)
        self.assertEqual([m["mes"] for m in r["meses"]], ["2024-01", "2024-02", "2024-03"])

    def test_desde_y_hasta_recortan(self) -> None:
        h = _hechos(ordenes=[_orden(1, "2024-01-02"), _orden(2, "2024-02-02"), _orden(3, "2024-03-02")])
        r = gpm.pl_mensual("GT", desde="2024-02", hasta="2024-02", hoy=HOY, hechos=h)
        self.assertEqual([m["mes"] for m in r["meses"]], ["2024-02"])

    def test_misma_formula_que_gen_pl_sobre_la_misma_ventana(self) -> None:
        """El mensual con pauta y banco da lo mismo que `calcular_vista_a` llamada a mano."""
        h = _enero()
        m = gpm.pl_mensual("GT", hoy=HOY, hechos=h)["meses"][0]
        df = gpm.df_de_ordenes(h["ordenes"])
        pauta = gen_pl.pauta_de_la_ventana("2024-01-01", "2024-01-31", h["gasto"])
        mov = gpm.movimientos_del_banco(h["banco"])
        r = gen_pl.calcular_vista_a(df, "2024-01-01", "2024-01-31", HOY, pauta, mov=mov,
                                    reglas=REGLAS, activos={"GT"}, fin_edad="2024-01-04")
        self.assertAlmostEqual(m["venta_entregada_q"], r.venta)
        self.assertAlmostEqual(m["costo_producto_q"], r.costo)
        self.assertAlmostEqual(m["flete_q"], r.flete)
        self.assertAlmostEqual(m["margen_logistico_q"], r.m_log)
        self.assertAlmostEqual(m["devoluciones_q"], r.c_dev)
        self.assertAlmostEqual(m["margen_contribucion_q"], r.m_contr)
        self.assertAlmostEqual(m["publicidad"]["q"], r.pauta_q)
        self.assertAlmostEqual(m["margen_operativo_q"], r.m_oper)
        self.assertAlmostEqual(m["gastos_fijos"]["q"], r.fijos)
        self.assertAlmostEqual(m["resultado_neto_q"], r.neto)

    def test_paridad_con_el_cli_de_gen_pl_sin_pauta_ni_banco(self) -> None:
        """Un export de juguete: lo que `gen_pl.py --json` dice de enero es lo que dice el mensual."""
        with tempfile.TemporaryDirectory() as d:
            xlsx = Path(d) / "ordenes_productos_20260101_000000.xlsx"
            filas = []
            for i, (est, dia, total, prov) in enumerate(
                    [("ENTREGADO", 2, 250.0, 60.0), ("ENTREGADO", 3, 300.0, 70.0),
                     ("DEVOLUCION", 4, 250.0, 60.0), ("EN RUTA", 5, 250.0, 60.0)], start=1):
                fecha = "%02d-01-2024" % dia
                filas.append({"ID": i, "PRODUCTO": "CLEARSTEM.VT", "ESTATUS": est, "FECHA": fecha,
                              "FECHA DE ÚLTIMO MOVIMIENTO": fecha, "TOTAL DE LA ORDEN": total,
                              "PRECIO FLETE": 30.0, "PRECIO PROVEEDOR X CANTIDAD": prov,
                              "GANANCIA": total - 30.0 - prov if est == "ENTREGADO" else None,
                              "CANTIDAD": 1})
            pd.DataFrame(filas).to_excel(xlsx, index=False)
            destino = Path(d) / "_FACT_ORDENES_DROPI.csv"
            ingerir_dropi.ingerir(str(xlsx), destino=str(destino), escribir=True)
            ordenes = gpm.csv_hechos.leer(str(destino))
            env = dict(os.environ, PYTHONIOENCODING="utf-8")
            p = subprocess.run([sys.executable, str(SCRIPT_PL), "--dropi", str(xlsx), "--desde",
                                "2024-01-01", "--hasta", "2024-01-31", "--json"], cwd=str(RAIZ),
                               env=env, capture_output=True, text=True, encoding="utf-8", timeout=120)
            try:
                self.assertEqual(p.returncode, 0, p.stderr)
                er = json.loads(p.stdout)["vista_a_cohorte"]["estado_de_resultados"]
                cohorte = json.loads(p.stdout)["vista_a_cohorte"]
            finally:
                for suf in ("txt", "json"):
                    f = AUD / ("_PL_20240101_20240131." + suf)
                    if f.is_file():
                        f.unlink()
        m = gpm.pl_mensual("GT", hoy=HOY, hechos=_hechos(ordenes=ordenes))["meses"][0]
        self.assertAlmostEqual(m["venta_entregada_q"], er["venta_bruta_entregada_q"])
        self.assertAlmostEqual(m["costo_producto_q"], er["costo_producto_q"])
        self.assertAlmostEqual(m["flete_q"], er["flete_q"])
        self.assertAlmostEqual(m["margen_logistico_q"], er["margen_logistico_q"])
        self.assertAlmostEqual(m["devoluciones_q"], er["costo_devoluciones_q"])
        self.assertAlmostEqual(m["personal_q"], er["costo_personal_q"])
        self.assertAlmostEqual(m["otros_q"], er["otros_gastos_q"])
        self.assertAlmostEqual(m["margen_contribucion_q"], er["margen_contribucion_q"])
        self.assertAlmostEqual(m["resultado_neto_q"], er["resultado_neto_q"])
        self.assertEqual((m["ordenes"]["entregadas"], m["ordenes"]["devueltas"],
                          m["ordenes"]["en_transito"]),
                         (cohorte["entregadas"], cohorte["devueltas"], cohorte["en_transito"]))

    def test_los_costos_operativos_son_todo_lo_que_hay_entre_la_venta_y_la_contribucion(self) -> None:
        m = gpm.pl_mensual("GT", hoy=HOY, hechos=_enero())["meses"][0]
        self.assertAlmostEqual(m["costos_operativos_q"],
                               m["costo_producto_q"] + m["flete_q"] + m["devoluciones_q"]
                               + m["personal_q"] + m["otros_q"])
        self.assertAlmostEqual(m["venta_entregada_q"] - m["costos_operativos_q"],
                               m["margen_contribucion_q"])

    def test_idempotente(self) -> None:
        h = _enero()
        a = gpm.pl_mensual("GT", hoy=HOY, hechos=h)
        b = gpm.pl_mensual("GT", hoy=HOY, hechos=h)
        self.assertEqual(json.dumps(a, sort_keys=True), json.dumps(b, sort_keys=True))


class Preliminar(unittest.TestCase):
    def _mes(self, fecha, hoy):
        h = _hechos(ordenes=[_orden(1, fecha)])
        return gpm.pl_mensual("GT", hoy=hoy, hechos=h)["meses"][0]

    def test_menos_de_diez_dias_desde_el_ultimo_dia_con_ordenes_es_preliminar(self) -> None:
        self.assertTrue(self._mes("2026-09-25", datetime.date(2026, 10, 3))["preliminar"])

    def test_diez_dias_o_mas_ya_no_es_preliminar(self) -> None:
        m = self._mes("2026-09-25", datetime.date(2026, 10, 5))
        self.assertFalse(m["preliminar"])
        self.assertEqual(m["edad_dias"], 10)

    def test_el_mes_en_curso_es_preliminar_y_lo_dice(self) -> None:
        m = self._mes("2026-10-02", HOY)
        self.assertTrue(m["preliminar"])
        self.assertTrue(any("en curso" in x for x in m["faltantes"]))


class RetirosYFijos(unittest.TestCase):
    def test_el_retiro_personal_no_toca_el_resultado(self) -> None:
        h = _enero()
        con = gpm.pl_mensual("GT", hoy=HOY, hechos=h)["meses"][0]
        sin = _enero()
        sin["banco"] = [b for b in sin["banco"] if "MINIMED" not in b["nombre"]]
        sin = gpm.pl_mensual("GT", hoy=HOY, hechos=sin)["meses"][0]
        self.assertAlmostEqual(con["resultado_neto_q"], sin["resultado_neto_q"])
        self.assertAlmostEqual(con["retiros_personales"]["q"], 50.0 * gen_pl.TASA_Q)
        self.assertEqual(sin["retiros_personales"]["q"], 0.0)

    def test_el_banco_cobro_facebook_se_muestra_y_no_se_resta_dos_veces(self) -> None:
        m = gpm.pl_mensual("GT", hoy=HOY, hechos=_enero())["meses"][0]
        self.assertAlmostEqual(m["banco_facebook"]["usd"], 100.0)
        self.assertEqual(m["banco_facebook"]["cargos"], 1)
        self.assertAlmostEqual(m["resultado_neto_q"],
                               m["margen_operativo_q"] - m["gastos_fijos"]["q"])

    def test_la_fuente_de_la_pauta_se_parte_en_meta_y_lucidsales(self) -> None:
        pub = gpm.pl_mensual("GT", hoy=HOY, hechos=_enero())["meses"][0]["publicidad"]
        self.assertAlmostEqual(pub["meta_usd"], 20.0)
        self.assertAlmostEqual(pub["lucidsales_fallback_usd"], 5.0)
        self.assertAlmostEqual(pub["usd"], 25.0)

    def test_los_productos_suman_el_mes(self) -> None:
        m = gpm.pl_mensual("GT", hoy=HOY, hechos=_enero())["meses"][0]
        self.assertAlmostEqual(sum(p["ganancia_q"] for p in m["por_producto"]), m["margen_operativo_q"])


class Faltantes(unittest.TestCase):
    def test_un_mes_sin_dropi_no_inventa_ceros(self) -> None:
        h = _hechos(banco=[_mov("2024-01-05", "Facebook", 100.0), _mov("2024-01-06", "LUCIDSALES, LLC", 26.0)],
                    gasto=[_gasto("CLEARSTEM", "2024-01-05", 20.0)])
        m = gpm.pl_mensual("GT", hoy=HOY, hechos=h)["meses"][0]
        self.assertIsNone(m["venta_entregada_q"])
        self.assertIsNone(m["resultado_neto_q"])
        self.assertAlmostEqual(m["publicidad"]["usd"], 20.0)
        self.assertAlmostEqual(m["banco_facebook"]["usd"], 100.0)
        self.assertAlmostEqual(m["gastos_fijos"]["q"], 26.0 * gen_pl.TASA_Q)
        self.assertTrue(any("Dropi" in x for x in m["faltantes"]))

    def test_un_mes_sin_banco_lo_dice(self) -> None:
        m = gpm.pl_mensual("GT", hoy=HOY, hechos=_hechos(ordenes=[_orden(1, "2024-01-02")]))["meses"][0]
        self.assertIsNone(m["banco_facebook"]["usd"])
        self.assertIsNone(m["gastos_fijos"]["q"])      # sin extracto no se sabe: no es un cero
        self.assertIsNone(m["retiros_personales"]["q"])
        self.assertTrue(any("banco" in x.lower() for x in m["faltantes"]))

    def test_un_mes_anterior_al_banco_es_informativo_y_no_pide_extracto(self) -> None:
        h = _hechos(ordenes=[_orden(1, "2026-07-02")])
        with mock.patch.object(gen_pl, "BANCO_DESDE", "2026-08-01"):
            m = gpm.pl_mensual("GT", hoy=HOY, hechos=h)["meses"][0]
        self.assertIsNone(m["gastos_fijos"]["q"])
        self.assertTrue(any("otro medio" in x and "2026-07" in x for x in m["faltantes"]))
        self.assertTrue(any("no están medidos" in x for x in m["faltantes"]))
        self.assertFalse(any("cargá el extracto" in x for x in m["faltantes"]))

    def test_un_mes_posterior_al_banco_si_pide_el_extracto(self) -> None:
        h = _hechos(ordenes=[_orden(1, "2026-09-02")])
        with mock.patch.object(gen_pl, "BANCO_DESDE", "2026-08-01"):
            m = gpm.pl_mensual("GT", hoy=HOY, hechos=h)["meses"][0]
        self.assertTrue(any("cargá el extracto" in x.lower() and "2026-09" in x
                            for x in m["faltantes"]))

    def test_sin_parametro_de_banco_se_pide_siempre(self) -> None:
        h = _hechos(ordenes=[_orden(1, "2026-07-02")])
        with mock.patch.object(gen_pl, "BANCO_DESDE", ""):
            m = gpm.pl_mensual("GT", hoy=HOY, hechos=h)["meses"][0]
        self.assertTrue(any("cargá el extracto" in x.lower() and "2026-07" in x
                            for x in m["faltantes"]))

    def test_pauta_de_lucidsales_se_avisa(self) -> None:
        m = gpm.pl_mensual("GT", hoy=HOY, hechos=_enero())["meses"][0]
        self.assertTrue(any("LucidSales" in x for x in m["faltantes"]))

    def test_un_cargo_sin_clasificar_se_lista_y_se_avisa(self) -> None:
        h = _enero()
        h["banco"].append(_mov("2024-01-08", "COSA NUEVA", 3.0))
        m = gpm.pl_mensual("GT", hoy=HOY, hechos=h)["meses"][0]
        self.assertEqual(m["cargos_sin_clasificar"][0]["nombre"], "COSA NUEVA")
        self.assertTrue(any("sin clasificar" in x.lower() for x in m["faltantes"]))

    def test_sin_ningun_hecho_cargado_lo_dice(self) -> None:
        r = gpm.pl_mensual("GT", hoy=HOY, hechos=_hechos())
        self.assertEqual(r["meses"], [])
        self.assertTrue(any("todavía no hay" in x.lower() for x in r["faltantes"]))

    def test_colombia_no_tiene_datos_todavia(self) -> None:
        r = gpm.pl_mensual("CO", hoy=HOY, hechos=_enero())
        self.assertEqual(r["meses"], [])
        self.assertTrue(any("Colombia" in x for x in r["faltantes"]))

    def test_las_ordenes_de_otro_mercado_no_entran(self) -> None:
        h = _hechos(ordenes=[_orden(1, "2024-01-02"), _orden(2, "2024-01-02", mercado="CO")])
        m = gpm.pl_mensual("GT", hoy=HOY, hechos=h)["meses"][0]
        self.assertEqual(m["ordenes"]["total"], 1)

    def test_un_cargo_de_tarjeta_co_no_entra_al_pl_de_gt(self) -> None:
        h = _hechos(ordenes=[_orden(1, "2024-01-02")],
                    banco=[_mov("2024-01-05", "Facebook", 100.0),
                           _mov("2024-01-06", "Facebook CO", 50.0, mercado="CO", tarjeta="9893",
                                banco="MERCURY")])
        m = gpm.pl_mensual("GT", hoy=HOY, hechos=h)["meses"][0]
        self.assertAlmostEqual(m["banco_facebook"]["usd"], 100.0)
        self.assertEqual(m["banco_facebook"]["cargos"], 1)

    def test_un_cargo_sin_mercado_sale_en_faltantes_y_no_entra(self) -> None:
        h = _hechos(ordenes=[_orden(1, "2024-01-02")],
                    banco=[_mov("2024-01-05", "Facebook", 100.0),
                           _mov("2024-01-06", "Facebook", 50.0, tarjeta="0000", banco="MERCURY")])
        m = gpm.pl_mensual("GT", hoy=HOY, hechos=h)["meses"][0]
        self.assertAlmostEqual(m["banco_facebook"]["usd"], 100.0)
        self.assertTrue(any("0000" in x for x in m["faltantes"]))


def _cart(mov_id, fecha, categoria, tipo, monto, despues, orden="", concepto=""):
    previo = despues + monto if tipo == "SALIDA" else despues - monto
    return {"mov_id": str(mov_id), "fecha": fecha, "hora": "10:00", "tipo": tipo,
            "monto_q": "%.2f" % monto, "saldo_previo_q": "%.2f" % previo,
            "saldo_despues_q": "%.2f" % despues, "orden_id": str(orden), "guia": "",
            "categoria": categoria, "descripcion": "x", "concepto_retiro": concepto,
            "mercado": "GT", "archivo_origen": "c.xlsx"}


REGLAS_RETIROS = [
    {"patron": "papa", "clasificacion": "RETIRO_PERSONAL"},
    {"patron": "RETIRO PROPIO", "clasificacion": "TRANSFERENCIA_PROPIA"},
]


def _con_cartera(cartera, ordenes=None, **kw):
    h = _enero() if ordenes is None else _hechos(ordenes=ordenes, **kw)
    h["cartera"] = cartera
    h["reglas_retiros"] = REGLAS_RETIROS
    return h


class CarteraDeDropi(unittest.TestCase):
    """El historial de cartera es el libro de caja: da el costo REAL de cada devolución y los
    retiros, que son movimiento de caja y no tocan el resultado."""

    def _enero_con(self, filas):
        return gpm.pl_mensual("GT", hoy=HOY, hechos=_con_cartera(filas))["meses"][0]

    def test_la_devolucion_usa_el_cobro_real_cuando_la_cartera_cubre_el_mes(self) -> None:
        # la orden 3 de _enero() es la devolución; Dropi cobró Q41.5 (no el promedio)
        m = self._enero_con([_cart(1, "2024-01-01", "GANANCIA_ORDEN", "ENTRADA", 10.0, 510.0, orden=1),
                             _cart(2, "2024-01-09", "COBRO_DEVOLUCION", "SALIDA", 41.5, 468.5, orden=3)])
        self.assertAlmostEqual(m["devoluciones_q"], 41.5)
        self.assertEqual(m["cartera"]["devoluciones"], {"origen": "REAL", "reales": 1, "estimadas": 0})
        self.assertAlmostEqual(m["resultado_neto_q"] - (m["margen_operativo_q"] - m["gastos_fijos"]["q"]), 0.0)

    def test_una_devolucion_aun_sin_cobrar_se_estima(self) -> None:
        h = _con_cartera([_cart(1, "2024-01-01", "GANANCIA_ORDEN", "ENTRADA", 10.0, 510.0, orden=1)])
        m = gpm.pl_mensual("GT", hoy=HOY, hechos=h)["meses"][0]
        self.assertAlmostEqual(m["devoluciones_q"], gen_pl.C_DEVOL)
        self.assertEqual(m["cartera"]["devoluciones"], {"origen": "ESTIMADO", "reales": 0, "estimadas": 1})

    def test_un_mes_anterior_a_la_cartera_se_estima_y_lo_dice(self) -> None:
        h = _con_cartera([_cart(1, "2024-03-01", "GANANCIA_ORDEN", "ENTRADA", 10.0, 510.0, orden=9)])
        m = gpm.pl_mensual("GT", hoy=HOY, hechos=h)["meses"][0]
        self.assertEqual(m["mes"], "2024-01")
        self.assertAlmostEqual(m["devoluciones_q"], gen_pl.C_DEVOL)
        self.assertEqual(m["cartera"]["devoluciones"]["origen"], "ESTIMADO")
        self.assertFalse(m["cartera"]["cubre_mes"])
        self.assertIsNone(m["cartera"]["saldo_cierre_q"])
        self.assertTrue(any("cartera" in x.lower() for x in m["faltantes"]))

    def test_los_retiros_se_clasifican_y_no_tocan_el_resultado(self) -> None:
        base = self._enero_con([_cart(1, "2024-01-01", "GANANCIA_ORDEN", "ENTRADA", 10.0, 9000.0, orden=1)])
        con = self._enero_con([
            _cart(1, "2024-01-01", "GANANCIA_ORDEN", "ENTRADA", 10.0, 9000.0, orden=1),
            _cart(2, "2024-01-10", "RETIRO", "SALIDA", 5000.0, 4000.0, concepto="Retiro papa"),
            _cart(3, "2024-01-11", "RETIRO", "SALIDA", 3000.0, 1000.0, concepto="a LLC RETIRO PROPIO"),
            _cart(4, "2024-01-12", "RETIRO", "SALIDA", 70.0, 930.0, concepto="pago raro")])
        c = con["cartera"]
        self.assertAlmostEqual(c["retiros_personales_q"], 5000.0)
        self.assertAlmostEqual(c["transferencias_propias_q"], 3000.0)
        self.assertAlmostEqual(c["sin_clasificar_q"], 70.0)
        self.assertEqual([r["clasificacion"] for r in c["retiros"]],
                         ["RETIRO_PERSONAL", "TRANSFERENCIA_PROPIA", "SIN_CLASIFICAR"])
        self.assertAlmostEqual(con["resultado_neto_q"], base["resultado_neto_q"])
        self.assertTrue(any("sin clasificar" in x.lower() and "pago raro" in x for x in con["faltantes"]))

    def test_el_saldo_de_cierre_es_el_del_ultimo_movimiento_del_mes(self) -> None:
        m = self._enero_con([_cart(1, "2024-01-01", "GANANCIA_ORDEN", "ENTRADA", 10.0, 510.0, orden=1),
                             _cart(2, "2024-01-20", "GANANCIA_ORDEN", "ENTRADA", 10.0, 520.0, orden=2),
                             _cart(3, "2024-02-02", "GANANCIA_ORDEN", "ENTRADA", 10.0, 530.0, orden=4)])
        self.assertAlmostEqual(m["cartera"]["saldo_cierre_q"], 520.0)
        self.assertEqual(m["cartera"]["fecha_corte"], "2024-01-20")
        self.assertTrue(m["cartera"]["cubre_mes"])

    def test_los_retiros_del_banco_y_los_de_la_cartera_son_rubros_aparte(self) -> None:
        m = self._enero_con([_cart(1, "2024-01-01", "GANANCIA_ORDEN", "ENTRADA", 10.0, 9000.0, orden=1),
                             _cart(2, "2024-01-10", "RETIRO", "SALIDA", 5000.0, 4000.0, concepto="Retiro papa")])
        self.assertAlmostEqual(m["retiros_personales"]["q"], 50.0 * gen_pl.TASA_Q)   # MINIMED, banco
        self.assertAlmostEqual(m["cartera"]["retiros_personales_q"], 5000.0)          # papa, cartera

    def test_sin_cartera_cargada_los_rubros_son_null_y_lo_dice(self) -> None:
        m = gpm.pl_mensual("GT", hoy=HOY, hechos=_enero())["meses"][0]
        self.assertFalse(m["cartera"]["cubre_mes"])
        self.assertIsNone(m["cartera"]["retiros_personales_q"])
        self.assertIsNone(m["cartera"]["saldo_cierre_q"])
        self.assertEqual(m["cartera"]["retiros"], [])

    def test_un_mes_sin_extracto_bancario_lo_dice(self) -> None:
        h = _hechos(ordenes=[_orden(1, "2024-07-02")])
        with mock.patch.object(gen_pl, "BANCO_DESDE", ""):
            m = gpm.pl_mensual("GT", hoy=HOY, hechos=h)["meses"][0]
        self.assertTrue(any("extracto" in x.lower() and "2024-07" in x for x in m["faltantes"]))

    def test_la_cobertura_de_la_cartera_se_reporta(self) -> None:
        r = gpm.pl_mensual("GT", hoy=HOY, hechos=_con_cartera(
            [_cart(1, "2024-01-01", "GANANCIA_ORDEN", "ENTRADA", 10.0, 510.0, orden=1),
             _cart(2, "2024-01-20", "GANANCIA_ORDEN", "ENTRADA", 10.0, 520.0, orden=2)]))
        self.assertEqual(r["cobertura"]["cartera"], {"desde": "2024-01-01", "hasta": "2024-01-20",
                                                     "movimientos": 2})


def _transferencia(salida, q, usd):
    return {"fecha_salida": salida, "monto_q": "%.2f" % q, "fecha_llegada": "", "monto_usd": "%.2f" % usd,
            "banco_destino": "MERCURY", "origen_salida": "1", "origen_llegada": "operador",
            "confirmado_por": "operador"}


class TasaEfectiva(unittest.TestCase):
    """La pauta y los fijos en USD se convierten con la tasa que midieron las transferencias."""

    def _mes(self, transferencias):
        h = _enero()
        h["transferencias"] = transferencias
        return gpm.pl_mensual("GT", hoy=HOY, hechos=h)["meses"][0]

    def test_sin_transferencias_manda_el_parametro_y_no_hay_costo_de_conversion(self) -> None:
        m = self._mes([])
        c = m["conversion"]
        self.assertEqual((c["regla"], c["tasa"], c["tasa_parametro"]), ("PARAMETRO", gen_pl.TASA_Q, gen_pl.TASA_Q))
        self.assertAlmostEqual(c["costo_q"], 0.0)
        self.assertAlmostEqual(m["publicidad"]["tasa"], gen_pl.TASA_Q)

    def test_la_pauta_y_los_fijos_usan_la_tasa_efectiva(self) -> None:
        base = self._mes([])
        m = self._mes([_transferencia("2024-01-10", 80000, 10000)])     # 8.00
        self.assertEqual(m["conversion"]["regla"], "VENTANA")
        self.assertAlmostEqual(m["conversion"]["tasa"], 8.0)
        self.assertAlmostEqual(m["publicidad"]["q"], m["publicidad"]["usd"] * 8.0)
        self.assertAlmostEqual(m["gastos_fijos"]["q"], 26.0 * 8.0)
        self.assertAlmostEqual(m["retiros_personales"]["q"], 50.0 * 8.0)
        self.assertAlmostEqual(base["publicidad"]["q"], base["publicidad"]["usd"] * gen_pl.TASA_Q)

    def test_el_costo_de_conversion_es_informativo_y_ya_esta_dentro_de_la_publicidad(self) -> None:
        base = self._mes([])
        m = self._mes([_transferencia("2024-01-10", 80000, 10000)])
        usd = m["publicidad"]["usd"]
        self.assertAlmostEqual(m["conversion"]["costo_q"], usd * (8.0 - gen_pl.TASA_Q))
        # el neto baja EXACTAMENTE por la publicidad y los fijos mas caros, sin restar el costo aparte
        mas_pauta = m["publicidad"]["q"] - base["publicidad"]["q"]
        mas_fijos = m["gastos_fijos"]["q"] - base["gastos_fijos"]["q"]
        self.assertAlmostEqual(base["resultado_neto_q"] - m["resultado_neto_q"], mas_pauta + mas_fijos)
        self.assertAlmostEqual(mas_pauta, m["conversion"]["costo_q"])

    def test_cada_mes_usa_su_propia_ventana(self) -> None:
        h = _hechos(ordenes=[_orden(1, "2024-01-02"), _orden(2, "2024-05-02")],
                    gasto=[_gasto("CLEARSTEM", "2024-01-05", 20.0), _gasto("CLEARSTEM", "2024-05-05", 20.0)])
        h["transferencias"] = [_transferencia("2024-01-10", 80000, 10000)]
        ene, may = gpm.pl_mensual("GT", hoy=HOY, hechos=h)["meses"]
        self.assertEqual(ene["conversion"]["regla"], "VENTANA")
        self.assertEqual(may["conversion"]["regla"], "ULTIMA_CONOCIDA")     # 112 dias despues
        self.assertAlmostEqual(may["conversion"]["tasa"], 8.0)

    def test_una_transferencia_posterior_al_mes_le_da_su_tasa(self) -> None:
        m = self._mes([_transferencia("2024-02-01", 90000, 11381)])
        self.assertEqual(m["conversion"]["regla"], "PRIMERA_POSTERIOR")
        self.assertAlmostEqual(m["conversion"]["tasa"], 90000 / 11381, places=4)

    def test_la_misma_formula_que_gen_pl_con_la_misma_tasa(self) -> None:
        h = _enero()
        trs = [_transferencia("2024-01-10", 80000, 10000)]
        h["transferencias"] = trs
        m = gpm.pl_mensual("GT", hoy=HOY, hechos=h)["meses"][0]
        pauta = gen_pl.pauta_de_la_ventana("2024-01-01", "2024-01-31", h["gasto"])
        tasa = gen_pl.tasa_del_mes("2024-01-31", trs)
        r = gen_pl.calcular_vista_a(gpm.df_de_ordenes(h["ordenes"]), "2024-01-01", "2024-01-31", HOY,
                                    pauta, mov=gpm.movimientos_del_banco(h["banco"]), reglas=REGLAS,
                                    activos={"GT"}, fin_edad="2024-01-04", tasa=tasa)
        self.assertAlmostEqual(m["resultado_neto_q"], r.neto)
        self.assertAlmostEqual(m["conversion"]["costo_q"], r.costo_conversion_q)


class Cli(unittest.TestCase):
    def test_mirar_no_escribe_y_colombia_sale_vacia(self) -> None:
        antes = sorted((p.name, p.stat().st_mtime_ns) for p in (RAIZ / "PRODUCTOS").iterdir())
        env = dict(os.environ, PYTHONIOENCODING="utf-8")
        p = subprocess.run([sys.executable, str(SCRIPT), "--mercado", "CO", "--json"], cwd=str(RAIZ),
                           env=env, capture_output=True, text=True, encoding="utf-8", timeout=120)
        self.assertEqual(p.returncode, 0, p.stderr)
        r = json.loads(p.stdout)
        self.assertEqual((r["mercado"], r["meses"]), ("CO", []))
        despues = sorted((p.name, p.stat().st_mtime_ns) for p in (RAIZ / "PRODUCTOS").iterdir())
        self.assertEqual(antes, despues)


if __name__ == "__main__":
    unittest.main()
