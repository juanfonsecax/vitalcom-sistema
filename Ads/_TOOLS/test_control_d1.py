# -*- coding: utf-8 -*-
"""test_control_d1.py — USO:  python Ads/_TOOLS/test_control_d1.py  (exit 0 = pasa)"""
import os, sys, io, json, datetime, unittest, contextlib
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import control_d1 as cd  # noqa: E402
import requiere_claude as rq  # noqa: E402

HOY = datetime.date(2026, 10, 18)


def E(dia, cj, spend, msj, cta="GTR7", camp="CAMP"):
    return {"ventana_ini": dia, "ventana_fin": dia, "cuenta_alias": cta, "campana": camp,
            "conjunto": cj, "spend_usd": str(spend), "mensajes": str(msj), "producto_key": "P"}


def V(dia, cj, msj, ventas, cta="GTR7", camp="CAMP"):
    return {"ventana_ini": dia, "ventana_fin": dia, "cuenta_alias": cta, "campana": camp,
            "conjunto": cj, "mensajes": str(msj), "ventas": str(ventas)}


def ev(entrega, ventas, **kw):
    return cd.evaluar(entrega, ventas, HOY, canon=kw.pop("canon", lambda n: n), **kw)


def veredicto(res, cj):
    return next(c["veredicto"] for c in res["conjuntos"] if c["conjunto"] == cj)


class ControlD1Tests(unittest.TestCase):
    def test_ok_cuando_lucid_tiene_actividad(self):
        r = ev([E("2026-10-17", "A", 4, 5)], [V("2026-10-17", "A", 2, 0)])
        self.assertEqual(veredicto(r, "A"), "OK")
        self.assertEqual(r["requiere_claude"], [])

    def test_ciego_pide_pausar(self):
        r = ev([E("2026-10-17", "A", 4, 5)], [V("2026-10-17", "A", 0, 0), V("2026-10-17", "Z", 3, 1)])
        self.assertEqual(veredicto(r, "A"), "CIEGO")
        (it,) = r["requiere_claude"]
        self.assertEqual((it["codigo"], it["severidad"]), ("CONJUNTO_CIEGO", "alta"))
        self.assertEqual(rq.validar(r["requiere_claude"]), [])
        self.assertEqual(it["pedirle_a_claude"],
                         "Pausá por MCP el conjunto A: Meta registra conversaciones y LucidSales "
                         "ninguna, el tracking está ciego.")

    def test_ciego_sin_ninguna_fila_de_lucid_ese_dia(self):
        # Otro conjunto si tiene data ese dia: LucidSales ya bajo el 17.
        r = ev([E("2026-10-17", "A", 4, 5)], [V("2026-10-17", "Z", 3, 1)])
        self.assertEqual(veredicto(r, "A"), "CIEGO")

    def test_id_se_incluye_si_se_conoce(self):
        r = ev([E("2026-10-17", "A", 4, 5)], [V("2026-10-17", "Z", 3, 1)], ids={("GTR7", "A"): "999"})
        it = r["requiere_claude"][0]
        self.assertIn("conjunto A (999):", it["pedirle_a_claude"])
        self.assertEqual(it["objetos"], [{"id": "999", "nombre": "A"}])

    def test_hoy_nunca_alarma(self):
        r = ev([E("2026-10-18", "A", 4, 5)], [V("2026-10-18", "A", 0, 0)])
        self.assertEqual(veredicto(r, "A"), "EN_CURSO")
        self.assertEqual(r["requiere_claude"], [])

    def test_dia_sin_data_de_lucid_aun_no_es_ciego(self):
        # LucidSales llega solo hasta el 16: el 17 no se puede juzgar.
        r = ev([E("2026-10-16", "A", 4, 5), E("2026-10-17", "A", 4, 5)],
               [V("2026-10-16", "A", 2, 0)])
        self.assertEqual(veredicto(r, "A"), "OK")
        self.assertEqual(r["conjuntos"][0]["dias"][1]["veredicto"], "EN_CURSO")  # el 17
        self.assertEqual(r["requiere_claude"], [])

    def test_sin_entrega_y_sin_mensajes(self):
        r = ev([E("2026-10-17", "A", 0.1, 0), E("2026-10-17", "B", 5, 0), E("2026-10-17", "C", 0, 0)],
               [V("2026-10-17", "Z", 1, 0)])
        self.assertEqual(veredicto(r, "A"), "SIN_ENTREGA")
        self.assertEqual(veredicto(r, "B"), "SIN_MENSAJES")
        self.assertEqual([c["conjunto"] for c in r["conjuntos"]], ["A", "B"])  # C nunca gasto
        self.assertEqual(r["requiere_claude"], [])

    def test_solo_conjuntos_con_primer_gasto_reciente(self):
        r = ev([E("2026-10-10", "VIEJO", 4, 5), E("2026-10-17", "VIEJO", 4, 5),
                E("2026-10-15", "NUEVO", 4, 5)], [V("2026-10-15", "NUEVO", 1, 0)])
        self.assertEqual([c["conjunto"] for c in r["conjuntos"]], ["NUEVO"])

    def test_el_peor_dia_manda(self):
        r = ev([E("2026-10-16", "A", 4, 5), E("2026-10-17", "A", 4, 5)],
               [V("2026-10-16", "A", 2, 0), V("2026-10-17", "A", 0, 0)])
        self.assertEqual(veredicto(r, "A"), "CIEGO")

    def test_alias_colapsa_el_nombre_renombrado(self):
        canon = lambda n: {"A viejo": "A"}.get(n, n)
        r = ev([E("2026-10-17", "A", 4, 5)], [V("2026-10-17", "A viejo", 2, 0)], canon=canon)
        self.assertEqual(veredicto(r, "A"), "OK")

    def test_ventanas_multidia_se_ignoran(self):
        multi = dict(V("2026-10-10", "A", 9, 9), ventana_fin="2026-10-17")
        r = ev([E("2026-10-17", "A", 4, 5)], [multi, V("2026-10-17", "Z", 1, 0)])
        self.assertEqual(veredicto(r, "A"), "CIEGO")

    def test_misma_cuenta_y_nombre_en_otra_campana_no_se_mezcla(self):
        r = ev([E("2026-10-17", "01", 4, 5, camp="X"), E("2026-10-17", "01", 4, 5, camp="Y")],
               [V("2026-10-17", "01", 2, 0, camp="X")])
        por = {c["campana"]: c["veredicto"] for c in r["conjuntos"]}
        self.assertEqual(por, {"X": "OK", "Y": "CIEGO"})

    def test_main_es_solo_lectura_y_exit_code(self):
        buf = io.StringIO()
        leer = lambda ruta: ([E("2026-10-17", "A", 4, 5)] if ruta == cd.ENTREGA
                             else [V("2026-10-17", "Z", 1, 0)])
        with mock.patch.object(cd, "_leer", side_effect=leer), \
                mock.patch.object(cd, "ids_de_conjuntos", return_value={}), \
                mock.patch.object(cd._alias, "canonico", side_effect=lambda n: n), \
                mock.patch("builtins.open", side_effect=AssertionError("no debe abrir archivos")), \
                contextlib.redirect_stdout(buf):
            rc = cd.main(["--hoy", "2026-10-18", "--json"])
        self.assertEqual(rc, 1)
        self.assertEqual(json.loads(buf.getvalue())["conjuntos"][0]["veredicto"], "CIEGO")

    def test_avisos_claude_sin_csv_es_vacio(self):
        with mock.patch.object(cd, "_leer", return_value=[]), \
                mock.patch.object(cd, "ids_de_conjuntos", return_value={}):
            self.assertEqual(cd.avisos_claude(HOY), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
