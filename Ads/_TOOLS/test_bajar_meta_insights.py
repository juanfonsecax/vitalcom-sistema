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
        filas de la cuenta sana se escriben igual y el codigo de salida queda en 2 (PARCIAL: al
        menos una OK, al menos una fallo), nunca se toca la red real."""
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

        self.assertEqual(codigo, 2, "una falla parcial (1 de 2 cuentas) debe dejar el codigo en 2")
        self.assertTrue(os.path.exists(fact_ad), "las filas de la cuenta sana se escriben igual")
        with open(fact_ad, encoding="utf-8") as fh:
            filas = list(csv.DictReader(fh))
        self.assertEqual(len(filas), 1)
        self.assertEqual(filas[0]["cuenta_alias"], "GTR7")
        self.assertEqual(filas[0]["fuente"], "MetaAPI-directo")

    def test_main_todas_las_cuentas_fallan_devuelve_1(self):
        """Si NINGUNA cuenta respondio, no hay nada parcial que rescatar: codigo 1, la cadena
        nocturna debe detenerse aca."""
        fact = os.path.join(self.temp_dir, "_FACT_ENTREGA.csv")
        fact_ad = os.path.join(self.temp_dir, "_FACT_ENTREGA_ANUNCIO.csv")
        bkdir = os.path.join(self.temp_dir, "backups_csv")

        cuentas_fake = [
            {"cuenta_alias": "GTR 13", "cuenta_id": "916746367261028", "moneda": "USD"},
            {"cuenta_alias": "GTR 7", "cuenta_id": "598687956219141", "moneda": "USD"},
        ]

        def procesar_cuenta_falla_siempre(cuenta, fecha, token, dim):
            raise SystemExit(f"Graph API error en cuenta {cuenta['cuenta_id']}: (#10) Permission denied")

        argv_fake = ["bajar_meta_insights.py", "--fecha", "2026-09-21"]
        with patch.object(bmi, "FACT", fact), \
             patch.object(bmi, "FACT_AD", fact_ad), \
             patch.object(bmi, "BKDIR", bkdir), \
             patch.object(bmi, "token_de", return_value="tok_falso"), \
             patch.object(bmi, "leer_cuentas_activas", return_value=cuentas_fake), \
             patch.object(bmi.im, "leer_dim", return_value=({}, {})), \
             patch.object(bmi, "procesar_cuenta", side_effect=procesar_cuenta_falla_siempre), \
             patch.object(sys, "argv", argv_fake):
            codigo = bmi.main()

        self.assertEqual(codigo, 1, "si todas las cuentas fallan el codigo debe quedar en 1")
        self.assertFalse(os.path.exists(fact_ad), "no hay filas sanas que escribir")

    def test_mensajes_de_prefiere_la_variante_7d(self):
        actions = [
            {"action_type": "onsite_conversion.messaging_conversation_started_7d", "value": "5"},
            {"action_type": "onsite_conversion.messaging_conversation_started", "value": "99"},
        ]
        self.assertEqual(bmi.mensajes_de(actions), 5)

    def test_mensajes_de_acepta_la_variante_sin_sufijo_si_falta_la_7d(self):
        actions = [{"action_type": "onsite_conversion.messaging_conversation_started", "value": "3"}]
        self.assertEqual(bmi.mensajes_de(actions), 3)

    def test_mensajes_de_sin_action_type_de_mensajeria_da_cero(self):
        actions = [{"action_type": "link_click", "value": "40"}]
        self.assertEqual(bmi.mensajes_de(actions), 0)

    def test_mensajes_de_sin_actions_da_cero(self):
        self.assertEqual(bmi.mensajes_de(None), 0)
        self.assertEqual(bmi.mensajes_de([]), 0)

    def test_procesar_cuenta_lleva_ad_id_y_mensajes_reales(self):
        """procesar_cuenta() ya no hardcodea mensajes=0: sale de 'actions', y ad_id sale
        del campo real de la Graph API (g07-cimientos T1, 22-sep-2026)."""
        crudo = [{
            "ad_id": "120210000000001", "ad_name": "ANGULO_A ~ PROD|ANG|C1.CN01|NC2|2X1|BOT_V1",
            "campaign_name": "Camp 1", "adset_name": "Conj 1", "spend": "5.00",
            "impressions": "100", "clicks": "10", "inline_link_clicks": "8",
            "actions": [{"action_type": "onsite_conversion.messaging_conversation_started_7d",
                         "value": "4"}],
        }]
        with patch.object(bmi, "insights_de", return_value=crudo):
            propios, gx, nx = bmi.procesar_cuenta(
                {"cuenta_alias": "GTR 7", "cuenta_id": "598687956219141", "moneda": "USD"},
                "2026-09-21", "tok", {"Conj 1": "PROD"})
        self.assertEqual(len(propios), 1)
        self.assertEqual(propios[0]["ad_id"], "120210000000001")
        self.assertEqual(propios[0]["mensajes"], 4)

    def test_rango_fechas_itera_dia_por_dia(self):
        self.assertEqual(bmi._rango_fechas("2026-09-14", "2026-09-16"),
                          ["2026-09-14", "2026-09-15", "2026-09-16"])
        self.assertEqual(bmi._rango_fechas("2026-09-14", "2026-09-14"), ["2026-09-14"])
        with self.assertRaises(SystemExit):
            bmi._rango_fechas("2026-09-16", "2026-09-14")

    def test_default_sin_argumentos_es_la_ventana_de_liquidacion(self):
        """Sin --fecha/--desde/--hasta, main() debe consultar upsert_fact.SETTLEMENT_WINDOW_DIAS
        dias terminando ayer — no un solo dia (T1: ventana de liquidacion nocturna)."""
        fact = os.path.join(self.temp_dir, "_FACT_ENTREGA.csv")
        fact_ad = os.path.join(self.temp_dir, "_FACT_ENTREGA_ANUNCIO.csv")
        bkdir = os.path.join(self.temp_dir, "backups_csv")
        llamadas = []

        def procesar_cuenta_registra(cuenta, fecha, token, dim):
            llamadas.append(fecha)
            return [], 0.0, 0

        argv_fake = ["bajar_meta_insights.py"]
        with patch.object(bmi, "FACT", fact), \
             patch.object(bmi, "FACT_AD", fact_ad), \
             patch.object(bmi, "BKDIR", bkdir), \
             patch.object(bmi, "token_de", return_value="tok_falso"), \
             patch.object(bmi, "leer_cuentas_activas",
                          return_value=[{"cuenta_alias": "GTR 7", "cuenta_id": "1", "moneda": "USD"}]), \
             patch.object(bmi.im, "leer_dim", return_value=({}, {})), \
             patch.object(bmi, "procesar_cuenta", side_effect=procesar_cuenta_registra), \
             patch.object(sys, "argv", argv_fake):
            bmi.main()

        self.assertEqual(len(llamadas), bmi.uf.SETTLEMENT_WINDOW_DIAS)
        self.assertEqual(len(set(llamadas)), bmi.uf.SETTLEMENT_WINDOW_DIAS,
                          "cada dia de la ventana se consulta una sola vez")

    def test_desde_hasta_consulta_cada_dia_del_tramo(self):
        fact = os.path.join(self.temp_dir, "_FACT_ENTREGA.csv")
        fact_ad = os.path.join(self.temp_dir, "_FACT_ENTREGA_ANUNCIO.csv")
        bkdir = os.path.join(self.temp_dir, "backups_csv")
        llamadas = []

        def procesar_cuenta_registra(cuenta, fecha, token, dim):
            llamadas.append(fecha)
            return [], 0.0, 0

        argv_fake = ["bajar_meta_insights.py", "--desde", "2026-09-10", "--hasta", "2026-09-12"]
        with patch.object(bmi, "FACT", fact), \
             patch.object(bmi, "FACT_AD", fact_ad), \
             patch.object(bmi, "BKDIR", bkdir), \
             patch.object(bmi, "token_de", return_value="tok_falso"), \
             patch.object(bmi, "leer_cuentas_activas",
                          return_value=[{"cuenta_alias": "GTR 7", "cuenta_id": "1", "moneda": "USD"}]), \
             patch.object(bmi.im, "leer_dim", return_value=({}, {})), \
             patch.object(bmi, "procesar_cuenta", side_effect=procesar_cuenta_registra), \
             patch.object(sys, "argv", argv_fake):
            bmi.main()

        self.assertEqual(llamadas, ["2026-09-10", "2026-09-11", "2026-09-12"])

    def test_re_correr_el_mismo_dia_es_idempotente(self):
        """Correr bajar_meta_insights.py dos veces con la MISMA fila no debe crecer el
        CSV: es el check de idempotencia explicito de T1."""
        fact = os.path.join(self.temp_dir, "_FACT_ENTREGA.csv")
        fact_ad = os.path.join(self.temp_dir, "_FACT_ENTREGA_ANUNCIO.csv")
        bkdir = os.path.join(self.temp_dir, "backups_csv")
        fila_sana = {
            "ventana_ini": "2026-09-21", "ventana_fin": "2026-09-21", "dias": 1,
            "producto_key": "PROD", "cuenta_id": "598687956219141", "cuenta_alias": "GTR7",
            "campana": "Camp 1", "conjunto": "Conj 1", "anuncio": "Ad 1", "ad_id": "999",
            "mensajes": 2, "clicks_totales": 3, "link_clicks": 2, "impresiones": 40,
            "spend_usd": 1.0, "pct_conv_clic_enlace": 0.0, "fuente": "MetaAPI-directo",
            "firma": "", "angulo_key": "", "concepto_key": "", "canonico_id": "",
            "nivel_conciencia": "", "oferta_key": "", "destino_key": "",
        }

        def procesar_cuenta_ok(cuenta, fecha, token, dim):
            return [dict(fila_sana)], 0.0, 0

        argv_fake = ["bajar_meta_insights.py", "--fecha", "2026-09-21"]
        with patch.object(bmi, "FACT", fact), \
             patch.object(bmi, "FACT_AD", fact_ad), \
             patch.object(bmi, "BKDIR", bkdir), \
             patch.object(bmi, "token_de", return_value="tok_falso"), \
             patch.object(bmi, "leer_cuentas_activas",
                          return_value=[{"cuenta_alias": "GTR 7", "cuenta_id": "598687956219141",
                                         "moneda": "USD"}]), \
             patch.object(bmi.im, "leer_dim", return_value=({}, {})), \
             patch.object(bmi, "procesar_cuenta", side_effect=procesar_cuenta_ok), \
             patch.object(sys, "argv", argv_fake):
            bmi.main()
            bmi.main()

        with open(fact_ad, encoding="utf-8") as fh:
            filas = list(csv.DictReader(fh))
        self.assertEqual(len(filas), 1, "re-correr el mismo dia no debe duplicar la fila")
        self.assertEqual(filas[0]["ad_id"], "999")

    def test_particion_elimina_backfill_viejo_sin_ad_id(self):
        """Reproduce el defecto real observado en vivo (22-sep-2026, segunda vuelta de T1):
        _FACT_ENTREGA_ANUNCIO.csv ya tenia ~710 filas de un backfill SIN ad_id para una
        cuenta/dia; el re-pull nuevo trae la MISMA cuenta/dia CON ad_id. Antes de `particion`
        las dos convivian (llaves distintas: firma vs ad_id) y el gasto por anuncio se
        duplicaba. Con `particion` la fila vieja debe desaparecer y solo queda la del re-pull."""
        fact = os.path.join(self.temp_dir, "_FACT_ENTREGA.csv")
        fact_ad = os.path.join(self.temp_dir, "_FACT_ENTREGA_ANUNCIO.csv")
        bkdir = os.path.join(self.temp_dir, "backups_csv")

        # Backfill viejo, escrito ANTES de que existiera ad_id: la llave real de esa fila
        # (ver bmi._clave_anuncio) cae en la FIRMA porque ad_id llega "".
        campos = list(bmi.im.COLS_AD)
        fila_vieja = {c: "" for c in campos}
        fila_vieja.update({
            "ventana_ini": "2026-09-06", "ventana_fin": "2026-09-06", "dias": "1",
            "producto_key": "PROD", "cuenta_id": "598687956219141", "cuenta_alias": "GTR7",
            "campana": "Camp 1", "conjunto": "Conj 1", "anuncio": "ANGULO_A ~ PROD|ANG|C1.CN01|NC2|2X1|BOT_V1",
            "ad_id": "", "firma": "PROD|ANG|C1.CN01|NC2|2X1|BOT_V1",
            "mensajes": "0", "clicks_totales": "10", "link_clicks": "8", "impresiones": "100",
            "spend_usd": "5.0", "pct_conv_clic_enlace": "0.0", "fuente": "MetaAPI-directo",
        })
        with open(fact_ad, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=campos)
            w.writeheader()
            w.writerow(fila_vieja)

        fila_repull = {
            "ventana_ini": "2026-09-06", "ventana_fin": "2026-09-06", "dias": 1,
            "producto_key": "PROD", "cuenta_id": "598687956219141", "cuenta_alias": "GTR7",
            "campana": "Camp 1", "conjunto": "Conj 1", "anuncio": "ANGULO_A ~ PROD|ANG|C1.CN01|NC2|2X1|BOT_V1",
            "ad_id": "120210000000001",
            "mensajes": 0, "clicks_totales": 10, "link_clicks": 8, "impresiones": 100,
            "spend_usd": 8.0, "pct_conv_clic_enlace": 0.0, "fuente": "MetaAPI-directo",
            "firma": "", "angulo_key": "", "concepto_key": "", "canonico_id": "",
            "nivel_conciencia": "", "oferta_key": "", "destino_key": "",
        }

        def procesar_cuenta_repull(cuenta, fecha, token, dim):
            return [dict(fila_repull)], 0.0, 0

        argv_fake = ["bajar_meta_insights.py", "--fecha", "2026-09-06"]
        with patch.object(bmi, "FACT", fact), \
             patch.object(bmi, "FACT_AD", fact_ad), \
             patch.object(bmi, "BKDIR", bkdir), \
             patch.object(bmi, "token_de", return_value="tok_falso"), \
             patch.object(bmi, "leer_cuentas_activas",
                          return_value=[{"cuenta_alias": "GTR 7", "cuenta_id": "598687956219141",
                                         "moneda": "USD"}]), \
             patch.object(bmi.im, "leer_dim", return_value=({}, {})), \
             patch.object(bmi, "procesar_cuenta", side_effect=procesar_cuenta_repull), \
             patch.object(sys, "argv", argv_fake):
            bmi.main()

        with open(fact_ad, encoding="utf-8") as fh:
            filas = list(csv.DictReader(fh))
        self.assertEqual(len(filas), 1, "la fila vieja sin ad_id debe desaparecer, no convivir")
        self.assertEqual(filas[0]["ad_id"], "120210000000001")
        self.assertEqual(float(filas[0]["spend_usd"]), 8.0, "el gasto no debe duplicarse")

    def test_main_todas_las_cuentas_ok_devuelve_0(self):
        """Sin ninguna falla el codigo de salida debe ser 0 (exito total)."""
        fact = os.path.join(self.temp_dir, "_FACT_ENTREGA.csv")
        fact_ad = os.path.join(self.temp_dir, "_FACT_ENTREGA_ANUNCIO.csv")
        bkdir = os.path.join(self.temp_dir, "backups_csv")

        cuentas_fake = [
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

        def procesar_cuenta_ok(cuenta, fecha, token, dim):
            return [fila_sana], 0.0, 0

        argv_fake = ["bajar_meta_insights.py", "--fecha", "2026-09-21"]
        with patch.object(bmi, "FACT", fact), \
             patch.object(bmi, "FACT_AD", fact_ad), \
             patch.object(bmi, "BKDIR", bkdir), \
             patch.object(bmi, "token_de", return_value="tok_falso"), \
             patch.object(bmi, "leer_cuentas_activas", return_value=cuentas_fake), \
             patch.object(bmi.im, "leer_dim", return_value=({}, {})), \
             patch.object(bmi, "procesar_cuenta", side_effect=procesar_cuenta_ok), \
             patch.object(sys, "argv", argv_fake):
            codigo = bmi.main()

        self.assertEqual(codigo, 0, "sin fallas el codigo de salida debe ser 0")


if __name__ == "__main__":
    unittest.main()
