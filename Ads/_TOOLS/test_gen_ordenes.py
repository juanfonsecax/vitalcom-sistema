#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_gen_ordenes.py — Pruebas unitarias para gen_ordenes.py (Hito 5)."""
import io
import json
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
import gen_ordenes  # noqa: E402


class TestGenOrdenes(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_ordenes_pausar_y_escalar_con_snapshot(self):
        decisiones_fixture = {
            "generado": "2026-09-19",
            "rezago_dias": 1,
            "productos": [
                {
                    "producto_key": "PRODUCTO_TEST",
                    "break_even_q": 80.0,
                    "cpa_objetivo_q": 35.0,
                    "fase_vigente": "F1",
                    "celdas": [
                        {
                            "celda": "ANGULO_MALO",
                            "estado": "PAUSAR",
                            "accion_codigo": "PAUSAR_HOOK_MUERTO",
                            "accion_sugerida": "APAGAR INMEDIATO",
                            "cpa_real_q": None,
                            "ic": [None, None, None],
                            "faltan_ventas": None,
                            "ejecutable": True,
                            "bloqueo_fase": None,
                        },
                        {
                            "celda": "ANGULO_BUENO",
                            "estado": "ESCALAR",
                            "accion_codigo": "ESCALAR_SURFING",
                            "accion_sugerida": "ESCALAR (Calet)",
                            "cpa_real_q": 25.0,
                            "ic": [18.0, 25.0, 32.0],
                            "faltan_ventas": None,
                            "ejecutable": True,
                            "bloqueo_fase": None,
                        },
                        {
                            "celda": "ANGULO_MEDIO",
                            "estado": "SEGUIR_MIDIENDO",
                            "accion_codigo": "MANTENER_Y_MEDIR",
                            "accion_sugerida": "MANTENER PRESUPUESTO",
                            "cpa_real_q": 75.0,
                            "ic": [40.0, 75.0, 120.0],
                            "faltan_ventas": 15,
                            "ejecutable": True,
                            "bloqueo_fase": None,
                        },
                    ],
                }
            ],
        }
        dec_path = os.path.join(self.temp_dir, "decisiones.json")
        with io.open(dec_path, "w", encoding="utf-8") as fh:
            json.dump(decisiones_fixture, fh)

        snapshot_fixture = {
            "ad_entities": [
                {
                    "id": "adset_111",
                    "name": "Conjunto Malo 1",
                    "nivel": "adset",
                    "status": "ACTIVE",
                    "daily_budget": 2.99,
                },
                {
                    "id": "adset_222",
                    "name": "Conjunto Bueno 1",
                    "nivel": "adset",
                    "status": "ACTIVE",
                    "daily_budget": 3.00,
                },
            ]
        }
        snap_path = os.path.join(self.temp_dir, "snapshot.json")
        with io.open(snap_path, "w", encoding="utf-8") as fh:
            json.dump(snapshot_fixture, fh)

        # Mockear cargar_dim_conjuntos para aislar el fixture
        orig_dim = gen_ordenes.cargar_dim_conjuntos
        try:
            gen_ordenes.cargar_dim_conjuntos = lambda: {
                ("PRODUCTO_TEST", "ANGULO_MALO"): [
                    {"conjunto_meta": "Conjunto Malo 1", "angulo_nombre": "Ángulo Malo"}
                ],
                ("PRODUCTO_TEST", "ANGULO_BUENO"): [
                    {"conjunto_meta": "Conjunto Bueno 1", "angulo_nombre": "Ángulo Bueno"}
                ],
                ("PRODUCTO_TEST", "ANGULO_MEDIO"): [
                    {"conjunto_meta": "Conjunto Medio 1", "angulo_nombre": "Ángulo Medio"}
                ],
            }

            res = gen_ordenes.generar_ordenes(
                producto_filtro="PRODUCTO_TEST",
                ruta_decisiones=dec_path,
                ruta_snapshot=snap_path,
            )

            self.assertEqual(res["schema"], "ordenes/1")
            self.assertEqual(res["rezago_dias"], 1)
            self.assertEqual(len(res["bloqueantes"]), 0)

            # Debe haber 2 llamadas a Meta (PAUSAR y ESCALAR); SEGUIR_MIDIENDO no genera llamada
            llamadas = res["llamadas"]
            self.assertEqual(len(llamadas), 2)

            llamada_pausa = next(ll for ll in llamadas if ll["accion"] == "PAUSAR")
            self.assertEqual(llamada_pausa["entidad"]["id"], "adset_111")
            self.assertEqual(llamada_pausa["args"]["fields"]["status"], "PAUSED")
            self.assertEqual(llamada_pausa["omitir"], False)

            llamada_escala = next(ll for ll in llamadas if ll["accion"] == "ESCALAR")
            self.assertEqual(llamada_escala["entidad"]["id"], "adset_222")
            # 3.00 + 20% = 3.60
            self.assertEqual(llamada_escala["args"]["fields"]["daily_budget"], 3.60)
            self.assertEqual(llamada_escala["omitir"], False)

            # Las órdenes de resumen deben contener las 3 celdas
            self.assertEqual(len(res["ordenes"]), 3)
            ord_medio = next(o for o in res["ordenes"] if o["angulo_key"] == "ANGULO_MEDIO")
            self.assertEqual(ord_medio["estado"], "SEGUIR_MIDIENDO")
            self.assertIn("faltan ~15 ventas", ord_medio["frase_simple"])

        finally:
            gen_ordenes.cargar_dim_conjuntos = orig_dim

    def test_idempotencia_si_ya_esta_pausado(self):
        decisiones_fixture = {
            "generado": "2026-09-19",
            "rezago_dias": 0,
            "productos": [
                {
                    "producto_key": "PROD_IDEM",
                    "break_even_q": 80.0,
                    "cpa_objetivo_q": 35.0,
                    "fase_vigente": "F1",
                    "celdas": [
                        {
                            "celda": "ANGULO_YA_PAUSADO",
                            "estado": "PAUSAR",
                            "accion_codigo": "PAUSAR_HOOK_MUERTO",
                            "accion_sugerida": "APAGAR",
                            "ejecutable": True,
                        }
                    ],
                }
            ],
        }
        dec_path = os.path.join(self.temp_dir, "dec.json")
        with io.open(dec_path, "w", encoding="utf-8") as fh:
            json.dump(decisiones_fixture, fh)

        snapshot_fixture = {
            "ad_entities": [
                {
                    "id": "adset_999",
                    "name": "Conjunto Ya Pausado",
                    "nivel": "adset",
                    "status": "PAUSED",  # Ya está en PAUSED
                }
            ]
        }
        snap_path = os.path.join(self.temp_dir, "snap.json")
        with io.open(snap_path, "w", encoding="utf-8") as fh:
            json.dump(snapshot_fixture, fh)

        orig_dim = gen_ordenes.cargar_dim_conjuntos
        try:
            gen_ordenes.cargar_dim_conjuntos = lambda: {
                ("PROD_IDEM", "ANGULO_YA_PAUSADO"): [
                    {"conjunto_meta": "Conjunto Ya Pausado", "angulo_nombre": "Ya Pausado"}
                ]
            }
            res = gen_ordenes.generar_ordenes(
                producto_filtro="PROD_IDEM",
                ruta_decisiones=dec_path,
                ruta_snapshot=snap_path,
            )
            self.assertEqual(len(res["llamadas"]), 1)
            self.assertTrue(res["llamadas"][0]["omitir"])
            self.assertEqual(res["llamadas"][0]["id_existente"], "adset_999")
        finally:
            gen_ordenes.cargar_dim_conjuntos = orig_dim

    def test_bloqueante_si_falta_id_de_meta(self):
        decisiones_fixture = {
            "generado": "2026-09-19",
            "rezago_dias": 0,
            "productos": [
                {
                    "producto_key": "PROD_SIN_ID",
                    "break_even_q": 80.0,
                    "cpa_objetivo_q": 35.0,
                    "fase_vigente": "F1",
                    "celdas": [
                        {
                            "celda": "ANGULO_PERDIDO",
                            "estado": "PAUSAR",
                            "accion_codigo": "PAUSAR_HOOK_MUERTO",
                            "accion_sugerida": "APAGAR",
                            "ejecutable": True,
                        }
                    ],
                }
            ],
        }
        dec_path = os.path.join(self.temp_dir, "dec.json")
        with io.open(dec_path, "w", encoding="utf-8") as fh:
            json.dump(decisiones_fixture, fh)

        # Snapshot vacío (no contiene el conjunto)
        snap_path = os.path.join(self.temp_dir, "snap_vacio.json")
        with io.open(snap_path, "w", encoding="utf-8") as fh:
            json.dump({"ad_entities": []}, fh)

        orig_dim = gen_ordenes.cargar_dim_conjuntos
        try:
            gen_ordenes.cargar_dim_conjuntos = lambda: {
                ("PROD_SIN_ID", "ANGULO_PERDIDO"): [
                    {"conjunto_meta": "Conjunto Desconocido", "angulo_nombre": "Desconocido"}
                ]
            }
            res = gen_ordenes.generar_ordenes(
                producto_filtro="PROD_SIN_ID",
                ruta_decisiones=dec_path,
                ruta_snapshot=snap_path,
            )
            self.assertTrue(len(res["bloqueantes"]) > 0)
            self.assertIn("no existe id de Meta", res["bloqueantes"][0]["falta"])
            self.assertIn("verificar_publicacion.py", res["bloqueantes"][0]["lo_produce"])
        finally:
            gen_ordenes.cargar_dim_conjuntos = orig_dim

    def test_bloqueo_fase_no_genera_orden_de_escalado(self):
        decisiones_fixture = {
            "generado": "2026-09-19",
            "rezago_dias": 0,
            "productos": [
                {
                    "producto_key": "CLEARSTEM",
                    "break_even_q": 105.0,
                    "cpa_objetivo_q": 30.8,
                    "fase_vigente": "F2",
                    "celdas": [
                        {
                            "celda": "RESISTENCIA_INSULINA",
                            "estado": "ESCALAR",
                            "ejecutable": False,
                            "bloqueo_fase": "CLEARSTEM está en F2 (gate de testeo): subir presupuesto sesga medición",
                        }
                    ],
                }
            ],
        }
        dec_path = os.path.join(self.temp_dir, "dec.json")
        with io.open(dec_path, "w", encoding="utf-8") as fh:
            json.dump(decisiones_fixture, fh)

        orig_dim = gen_ordenes.cargar_dim_conjuntos
        try:
            gen_ordenes.cargar_dim_conjuntos = lambda: {
                ("CLEARSTEM", "RESISTENCIA_INSULINA"): [
                    {"conjunto_meta": "Conjunto Insulina", "angulo_nombre": "Resistencia Insulina"}
                ]
            }
            res = gen_ordenes.generar_ordenes(
                producto_filtro="CLEARSTEM",
                ruta_decisiones=dec_path,
            )
            self.assertEqual(len(res["llamadas"]), 0)
            self.assertTrue(any("sesga medición" in a for a in res["avisos"]))
        finally:
            gen_ordenes.cargar_dim_conjuntos = orig_dim


if __name__ == "__main__":
    unittest.main()
