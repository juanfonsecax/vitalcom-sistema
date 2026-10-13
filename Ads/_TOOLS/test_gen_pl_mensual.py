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


def _mov(fecha, nombre, monto, tipo="SALIDA", saldo="1.00"):
    return {"fecha": fecha, "banco": "RELAY", "cuenta": "8889", "nombre": nombre,
            "monto": "%.2f" % monto, "tipo": tipo, "saldo": saldo, "tarjeta": "", "archivo": "a.pdf"}


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
