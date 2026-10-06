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
        # cargar_pendientes_registro() lee la _FACT_ENTREGA_ANUNCIO.csv REAL del repo (no toma
        # ruta_decisiones). Los tests de este archivo prueban otra cosa y no deben acoplarse a la
        # data real -> se aisla por default; TestPendientesRegistro (mas abajo) la restaura para
        # probarla de verdad con sus propios fixtures.
        self._orig_pendientes = gen_ordenes.cargar_pendientes_registro
        gen_ordenes.cargar_pendientes_registro = lambda: []

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        gen_ordenes.cargar_pendientes_registro = self._orig_pendientes

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
                            "ventas_actual": 3,
                            "ventas_necesarias": 18,
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
            # T7: el umbral que decidir.py aplico viaja intacto en por_que, sin recalcularse acá.
            self.assertEqual(ord_medio["por_que"]["ventas_actual"], 3)
            self.assertEqual(ord_medio["por_que"]["ventas_necesarias"], 18)

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


class TestPlataNuncaInventada(unittest.TestCase):
    """ESCALAR mueve plata: nunca sobre un presupuesto inventado ni sobre data vieja.
    PAUSAR frena gasto y se revierte: sigue saliendo con data vieja, con aviso."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self._orig_pendientes = gen_ordenes.cargar_pendientes_registro
        self._orig_dim = gen_ordenes.cargar_dim_conjuntos
        gen_ordenes.cargar_pendientes_registro = lambda: []
        gen_ordenes.cargar_dim_conjuntos = lambda: {
            ("PX", "ANG_SUBE"): [{"conjunto_meta": "Conjunto Sube", "angulo_nombre": "Sube"}],
            ("PX", "ANG_BAJA"): [{"conjunto_meta": "Conjunto Baja", "angulo_nombre": "Baja"}],
        }

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        gen_ordenes.cargar_pendientes_registro = self._orig_pendientes
        gen_ordenes.cargar_dim_conjuntos = self._orig_dim

    def _correr(self, rezago, budget_sube, con_rezago=True):
        dec = {"generado": "2026-10-05", "productos": [{
            "producto_key": "PX", "break_even_q": 80.0, "cpa_objetivo_q": 35.0,
            "fase_vigente": "F4", "celdas": [
                {"celda": "ANG_SUBE", "estado": "ESCALAR", "ejecutable": True},
                {"celda": "ANG_BAJA", "estado": "PAUSAR", "ejecutable": True},
            ]}]}
        if con_rezago:
            dec["rezago_dias"] = rezago
        sube = {"id": "adset_sube", "name": "Conjunto Sube", "nivel": "adset", "status": "ACTIVE"}
        if budget_sube is not None:
            sube["daily_budget"] = budget_sube
        snap = {"ad_entities": [sube, {"id": "adset_baja", "name": "Conjunto Baja",
                                       "nivel": "adset", "status": "ACTIVE"}]}
        dec_path = os.path.join(self.temp_dir, "dec.json")
        snap_path = os.path.join(self.temp_dir, "snap.json")
        with io.open(dec_path, "w", encoding="utf-8") as fh:
            json.dump(dec, fh)
        with io.open(snap_path, "w", encoding="utf-8") as fh:
            json.dump(snap, fh)
        return gen_ordenes.generar_ordenes(producto_filtro="PX", ruta_decisiones=dec_path,
                                           ruta_snapshot=snap_path)

    def _acciones(self, res):
        return sorted(ll["accion"] for ll in res["llamadas"])

    def test_escalar_sin_daily_budget_bloquea_y_no_inventa(self):
        res = self._correr(rezago=0, budget_sube=None)
        self.assertEqual(self._acciones(res), ["PAUSAR"])
        self.assertTrue(any("daily_budget" in b["falta"] and "Conjunto Sube" in b["falta"]
                            for b in res["bloqueantes"]))

    def test_escalar_con_budget_invalido_o_cero_bloquea(self):
        for malo in ("", "abc", 0, -5):
            res = self._correr(rezago=0, budget_sube=malo)
            self.assertEqual(self._acciones(res), ["PAUSAR"], malo)
            self.assertTrue(res["bloqueantes"], malo)

    def test_escalar_con_budget_real_y_data_fresca_sale(self):
        res = self._correr(rezago=2, budget_sube=15.0)
        self.assertEqual(self._acciones(res), ["ESCALAR", "PAUSAR"])
        sube = next(ll for ll in res["llamadas"] if ll["accion"] == "ESCALAR")
        self.assertEqual(sube["args"]["fields"]["daily_budget"], 18.0)
        self.assertEqual(res["bloqueantes"], [])

    def test_rezago_mayor_al_maximo_bloquea_escalar_y_deja_pausar(self):
        res = self._correr(rezago=3, budget_sube=15.0)
        self.assertEqual(self._acciones(res), ["PAUSAR"])
        self.assertTrue(any("rezago" in b["falta"] for b in res["bloqueantes"]))
        self.assertTrue(any("rezago" in a for a in res["avisos"]))

    def test_rezago_desconocido_bloquea_escalar(self):
        for res in (self._correr(rezago=None, budget_sube=15.0),
                    self._correr(rezago=None, budget_sube=15.0, con_rezago=False)):
            self.assertEqual(self._acciones(res), ["PAUSAR"])
            self.assertTrue(any("rezago" in b["falta"] for b in res["bloqueantes"]))


class TestPendientesRegistro(unittest.TestCase):
    """Conjuntos NUESTROS (producto_key clasificado) sin fila de angulo_key en
    _DIM_CONJUNTOS.csv deben salir como pendiente visible, distintos de un AJENO
    (SIN_CLASIFICAR, que bajar_meta_insights.py ya excluye antes de llegar al CSV)."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self._orig_P = gen_ordenes.P
        gen_ordenes.P = lambda *a: os.path.join(self.temp_dir, *a)

        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import ingerir_meta as im
        self._im = im
        self._orig_leer_dim = im.leer_dim

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        gen_ordenes.P = self._orig_P
        self._im.leer_dim = self._orig_leer_dim

    def _escribir_fact_ad(self, filas):
        cols = ["cuenta_alias", "campana", "conjunto", "producto_key", "spend_usd"]
        ruta = os.path.join(self.temp_dir, "_FACT_ENTREGA_ANUNCIO.csv")
        import csv as _csv
        with io.open(ruta, "w", newline="", encoding="utf-8") as fh:
            w = _csv.DictWriter(fh, fieldnames=cols)
            w.writeheader()
            for f in filas:
                w.writerow(f)

    def test_conjunto_nuestro_sin_dim_sale_pendiente(self):
        # "Conjunto Nuevo" es nuestro (producto_key=TINNIDROP) pero no está en con_angulo.
        self._escribir_fact_ad([
            {"cuenta_alias": "GTR7", "campana": "GTR7_TINNIDROP_TEST", "conjunto": "Conjunto Nuevo",
             "producto_key": "TINNIDROP", "spend_usd": "10.50"},
            {"cuenta_alias": "GTR7", "campana": "GTR7_TINNIDROP_TEST", "conjunto": "Conjunto Nuevo",
             "producto_key": "TINNIDROP", "spend_usd": "4.50"},
        ])
        self._im.leer_dim = lambda: ({}, set())

        pend = gen_ordenes.cargar_pendientes_registro()
        self.assertEqual(len(pend), 1)
        self.assertEqual(pend[0]["conjunto"], "Conjunto Nuevo")
        self.assertEqual(pend[0]["producto_key"], "TINNIDROP")
        self.assertEqual(pend[0]["spend_usd"], 15.0)
        self.assertEqual(pend[0]["anuncios"], 2)
        self.assertEqual(pend[0]["lo_produce"], "ETAPA-6 / _DIM_CONJUNTOS.csv")

    def test_conjunto_ya_registrado_no_sale_pendiente(self):
        self._escribir_fact_ad([
            {"cuenta_alias": "GTR7", "campana": "GTR7_TINNIDROP_TEST", "conjunto": "Conjunto Viejo",
             "producto_key": "TINNIDROP", "spend_usd": "10.00"},
        ])
        self._im.leer_dim = lambda: ({}, {"Conjunto Viejo"})

        pend = gen_ordenes.cargar_pendientes_registro()
        self.assertEqual(pend, [])

    def test_ajeno_sin_clasificar_no_sale_pendiente(self):
        # Un ajeno (cliente de agencia) nunca clasifica producto_key: SIN_CLASIFICAR, o vacio.
        self._escribir_fact_ad([
            {"cuenta_alias": "GTR7", "campana": "DR MELAXIN CAMPAIGN", "conjunto": "DR MELAXIN AD SET",
             "producto_key": "SIN_CLASIFICAR", "spend_usd": "99.00"},
        ])
        self._im.leer_dim = lambda: ({}, set())

        pend = gen_ordenes.cargar_pendientes_registro()
        self.assertEqual(pend, [])

    def test_aviso_y_gasto_llegan_al_resultado_de_generar_ordenes(self):
        self._escribir_fact_ad([
            {"cuenta_alias": "GTR7", "campana": "GTR7_TINNIDROP_TEST", "conjunto": "Conjunto Nuevo",
             "producto_key": "TINNIDROP", "spend_usd": "12.00"},
        ])
        self._im.leer_dim = lambda: ({}, set())

        dec_path = os.path.join(self.temp_dir, "decisiones.json")
        with io.open(dec_path, "w", encoding="utf-8") as fh:
            json.dump({"generado": "2026-09-22", "rezago_dias": 0, "productos": []}, fh)

        orig_dim_conj = gen_ordenes.cargar_dim_conjuntos
        gen_ordenes.cargar_dim_conjuntos = lambda: {}
        try:
            res = gen_ordenes.generar_ordenes(ruta_decisiones=dec_path)
        finally:
            gen_ordenes.cargar_dim_conjuntos = orig_dim_conj

        self.assertEqual(len(res["pendientes_registro"]), 1)
        self.assertEqual(res["pendientes_registro"][0]["spend_usd"], 12.0)
        self.assertTrue(any("Conjunto Nuevo" in a and "ETAPA-6" in a for a in res["avisos"]))


if __name__ == "__main__":
    unittest.main()
