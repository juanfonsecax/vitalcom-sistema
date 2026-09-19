#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_bajar_meta_insights.py — Pruebas unitarias para bajar_meta_insights.py (Hito 5)."""
import os
import sys
import tempfile
import unittest

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
        cuentas = bmi.leer_cuentas_activas()
        self.assertIsInstance(cuentas, list)
        for c in cuentas:
            self.assertEqual(c.get("mcp_habilitado"), "SI")
            self.assertEqual(c.get("estado_cuenta"), "ACTIVE")
            self.assertEqual(c.get("tiene_metodo_pago"), "SI")

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


if __name__ == "__main__":
    unittest.main()
