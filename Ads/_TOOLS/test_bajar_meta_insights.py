#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_bajar_meta_insights.py — Pruebas unitarias para bajar_meta_insights.py (Hito 5)."""
import csv
import os
import sys
import tempfile
import unittest
from unittest.mock import patch

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bajar_meta_insights as bmi  # noqa: E402


class TestBajarMetaInsights(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_cargar_env(self):
        env_file = os.path.join(self.temp_dir, "test.env")
        with open(env_file, "w", encoding="utf-8") as f:
            f.write("# comentario\n")
            f.write("META_SYSTEM_USER_TOKEN=tok_12345\n")
            f.write("OTRA_VAR='valor'\n")

        d = bmi.cargar_env(env_file)
        self.assertEqual(d.get("META_SYSTEM_USER_TOKEN"), "tok_12345")
        self.assertEqual(d.get("OTRA_VAR"), "valor")

    def test_token_de_falta_token(self):
        env_vacio = os.path.join(self.temp_dir, "no_existe.env")
        ant = os.environ.pop("META_SYSTEM_USER_TOKEN", None)
        try:
            with self.assertRaises(SystemExit) as ctx:
                bmi.token_de(env_vacio)
            self.assertIn("FALTA EL TOKEN", str(ctx.exception))
        finally:
            if ant:
                os.environ["META_SYSTEM_USER_TOKEN"] = ant

    def test_token_de_desde_env_var(self):
        ant = os.environ.get("META_SYSTEM_USER_TOKEN")
        try:
            os.environ["META_SYSTEM_USER_TOKEN"] = "token_de_prueba"
            tok = bmi.token_de(os.path.join(self.temp_dir, "inexistente.env"))
            self.assertEqual(tok, "token_de_prueba")
        finally:
            if ant is not None:
                os.environ["META_SYSTEM_USER_TOKEN"] = ant
            else:
                os.environ.pop("META_SYSTEM_USER_TOKEN", None)

    def test_leer_cuentas_activas(self):
        # No filtra por mcp_habilitado (22-sep-2026): esta lectura es Graph API directa, ajena al
        # conector interactivo. Solo importan estado_cuenta y tiene_metodo_pago.
        cuentas = bmi.leer_cuentas_activas()
        self.assertIsInstance(cuentas, list)
        for c in cuentas:
            self.assertEqual(c.get("estado_cuenta"), "ACTIVE")
            self.assertEqual(c.get("tiene_metodo_pago"), "SI")

    def test_leer_cuentas_activas_incluye_mcp_no_y_excluye_retirada_y_sin_pago(self):
        """Filtro aislado sobre un CSV propio: ACTIVE+pago=SI con mcp_habilitado=NO entra (caso
        GTR13/CLEARSTEM); RETIRADA y pago=NO quedan afuera aunque tengan mcp_habilitado=SI."""
        csv_path = os.path.join(self.temp_dir, "_DIM_CUENTAS.csv")
        campos = ["cuenta_alias", "cuenta_id", "moneda", "mcp_habilitado",
                  "estado_cuenta", "tiene_metodo_pago"]
        filas = [
            {"cuenta_alias": "GTR 13", "cuenta_id": "916746367261028", "moneda": "USD",
             "mcp_habilitado": "NO", "estado_cuenta": "ACTIVE", "tiene_metodo_pago": "SI"},
            {"cuenta_alias": "GTR 2", "cuenta_id": "1680252426660775", "moneda": "USD",
             "mcp_habilitado": "SI", "estado_cuenta": "RETIRADA", "tiene_metodo_pago": "SI"},
            {"cuenta_alias": "Margarita", "cuenta_id": "332010724162945", "moneda": "COP",
             "mcp_habilitado": "SI", "estado_cuenta": "ACTIVE", "tiene_metodo_pago": "NO"},
        ]
        with open(csv_path, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=campos)
            w.writeheader()
            w.writerows(filas)

        dimcu_original = bmi.DIMCU
        bmi.DIMCU = csv_path
        try:
            cuentas = bmi.leer_cuentas_activas()
        finally:
            bmi.DIMCU = dimcu_original

        alias = {c["cuenta_alias"] for c in cuentas}
        self.assertIn("GTR 13", alias)
        self.assertNotIn("GTR 2", alias)
        self.assertNotIn("Margarita", alias)

    def test_agregar_a_conjunto(self):
        ads = [
            {
                "cuenta_alias": "GTR7", "campana": "Camp 1", "conjunto": "Conj 1", "anuncio": "Ad 1",
                "clicks_totales": 10, "link_clicks": 8, "impresiones": 100, "spend_usd": 2.50,
                "producto_key": "PROD", "ventana_ini": "2026-09-18", "ventana_fin": "2026-09-18",
                "dias": 1, "cuenta_id": "123", "mensajes": 0, "pct_conv_clic_enlace": 0.0, "fuente": "Meta",
                "formato": "IMG", "avatar": "AV", "angulo": "ANG", "tipo_hook": "HK",
                "concepto": "CP", "rol_embudo": "TOFU", "lleva_precio": "NO",
            },
            {
                "cuenta_alias": "GTR7", "campana": "Camp 1", "conjunto": "Conj 1", "anuncio": "Ad 2",
                "clicks_totales": 5, "link_clicks": 4, "impresiones": 50, "spend_usd": 1.25,
                "producto_key": "PROD", "ventana_ini": "2026-09-18", "ventana_fin": "2026-09-18",
                "dias": 1, "cuenta_id": "123", "mensajes": 0, "pct_conv_clic_enlace": 0.0, "fuente": "Meta",
                "formato": "IMG", "avatar": "AV", "angulo": "ANG", "tipo_hook": "HK",
                "concepto": "CP", "rol_embudo": "TOFU", "lleva_precio": "NO",
            },
        ]
        res = bmi.agregar_a_conjunto(ads)
        self.assertEqual(len(res), 1)
        c = res[0]
        self.assertEqual(c["clicks_totales"], 15)
        self.assertEqual(c["link_clicks"], 12)
        self.assertEqual(c["impresiones"], 150)
        self.assertEqual(c["spend_usd"], 3.75)

    def test_main_aisla_falla_de_una_cuenta_y_sigue_con_las_demas(self):
        """Una cuenta que revienta (permiso denegado, ej. GTR13) no debe tumbar el proceso: las
        filas de la cuenta sana se escriben igual y el codigo de salida queda en 1 (no 0), nunca
        se toca la red real."""
        fact = os.path.join(self.temp_dir, "_FACT_ENTREGA.csv")
        fact_ad = os.path.join(self.temp_dir, "_FACT_ENTREGA_ANUNCIO.csv")
        bkdir = os.path.join(self.temp_dir, "backups_csv")

        cuentas_fake = [
            {"cuenta_alias": "GTR 13", "cuenta_id": "916746367261028", "moneda": "USD"},
            {"cuenta_alias": "GTR 7", "cuenta_id": "598687956219141", "moneda": "USD"},
        ]

        fila_sana = {
            "ventana_ini": "2026-09-21", "ventana_fin": "2026-09-21", "dias": 1,
            "producto_key": "PROD", "cuenta_id": "598687956219141", "cuenta_alias": "GTR7",
            "campana": "Camp 1", "conjunto": "Conj 1", "anuncio": "Ad 1",
            "mensajes": 0, "clicks_totales": 3, "link_clicks": 2, "impresiones": 40,
            "spend_usd": 1.0, "pct_conv_clic_enlace": 0.0, "fuente": "MetaAPI-directo",
            "firma": "", "angulo_key": "", "concepto_key": "", "canonico_id": "",
            "nivel_conciencia": "", "oferta_key": "", "destino_key": "",
        }

        def procesar_cuenta_fake(cuenta, fecha, token, dim):
            if cuenta["cuenta_alias"] == "GTR 13":
                raise SystemExit("Graph API error en cuenta 916746367261028: (#10) Permission denied")
            return [fila_sana], 0.0, 0

        argv_fake = ["bajar_meta_insights.py", "--fecha", "2026-09-21"]
        with patch.object(bmi, "FACT", fact), \
             patch.object(bmi, "FACT_AD", fact_ad), \
             patch.object(bmi, "BKDIR", bkdir), \
             patch.object(bmi, "token_de", return_value="tok_falso"), \
             patch.object(bmi, "leer_cuentas_activas", return_value=cuentas_fake), \
             patch.object(bmi.im, "leer_dim", return_value=({}, {})), \
             patch.object(bmi, "procesar_cuenta", side_effect=procesar_cuenta_fake), \
             patch.object(sys, "argv", argv_fake):
            codigo = bmi.main()

        self.assertEqual(codigo, 1, "una cuenta fallida debe dejar el proceso en codigo != 0")
        self.assertTrue(os.path.exists(fact_ad), "las filas de la cuenta sana se escriben igual")
        with open(fact_ad, encoding="utf-8") as fh:
            filas = list(csv.DictReader(fh))
        self.assertEqual(len(filas), 1)
        self.assertEqual(filas[0]["cuenta_alias"], "GTR7")
        self.assertEqual(filas[0]["fuente"], "MetaAPI-directo")


if __name__ == "__main__":
    unittest.main()
