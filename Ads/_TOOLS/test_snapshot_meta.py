# -*- coding: utf-8 -*-
"""test_snapshot_meta.py — pruebas de snapshot_meta.py con la red simulada (sin red real).

USO:  python Ads/_TOOLS/test_snapshot_meta.py     (exit 0 = pasa)
"""
import io, os, sys, json, tempfile, unittest, contextlib
from unittest import mock

os.environ.setdefault("PGDATABASE", "vitalcom_test")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import snapshot_meta as sm  # noqa: E402
import verificar_publicacion as vp  # noqa: E402

TOKEN = "TOKEN_SECRETO_123"
CAMP = "GTR7_PROD_CONCEPTOS-C_20261017"


def _fake_graph(paginas_ads=2):
    """Devuelve (pedir_fn, urls_vistas). Cuenta con 2 campanas; los anuncios van paginados."""
    vistos = []
    ads = [{"id": "ad%d" % i, "name": "ANUNCIO %d" % i, "effective_status": "ACTIVE",
            "campaign_id": "c1" if i % 2 == 0 else "c2"} for i in range(4)]

    def pedir_fn(url):
        vistos.append(url)
        if "/campaigns?" in url:
            return {"data": [{"id": "c1", "name": CAMP, "effective_status": "ACTIVE", "campaign_id": "c1"},
                             {"id": "c2", "name": "OTRA_CAMPANA", "effective_status": "ACTIVE", "campaign_id": "c2"}]}
        if "/adsets?" in url:
            return {"data": [{"id": "s1", "name": "CONJ1", "effective_status": "ACTIVE", "campaign_id": "c1"},
                             {"id": "s2", "name": "CONJ2", "effective_status": "PAUSED", "campaign_id": "c2"}]}
        if "/ads?" in url:
            return {"data": ads[:2], "paging": {"next": "https://graph.test/pag2?access_token=" + TOKEN}}
        if url.startswith("https://graph.test/pag2"):
            return {"data": ads[2:]}
        raise AssertionError("url inesperada " + url)
    return pedir_fn, vistos


class SnapshotTests(unittest.TestCase):
    def test_pagina_y_filtra_por_nombre_de_campana(self):
        fn, vistos = _fake_graph()
        s = sm.construir_snapshot("act_123", "CONCEPTOS-C", TOKEN, "GTR7", pedir_fn=fn, api="https://g.test/v1")
        nombres = {o["name"] for o in s["ad_entities"]}
        self.assertEqual(nombres, {CAMP, "CONJ1", "ANUNCIO 0", "ANUNCIO 2"})
        self.assertEqual(s["cuenta_id"], "123")
        self.assertEqual(s["cuenta_alias"], "GTR7")
        self.assertTrue(any(u.startswith("https://graph.test/pag2") for u in vistos), "no siguio paging.next")
        niveles = {o["nivel"] for o in s["ad_entities"]}
        self.assertEqual(niveles, {"campaign", "adset", "ad"})

    def test_forma_aceptada_por_cargar_snapshot(self):
        fn, _ = _fake_graph()
        s = sm.construir_snapshot("123", CAMP, TOKEN, "GTR7", pedir_fn=fn, api="https://g.test/v1")
        with tempfile.TemporaryDirectory() as d:
            ruta = os.path.join(d, "sub", "snap.json")
            sm.escribir_atomico(ruta, s)
            self.assertEqual(os.listdir(os.path.dirname(ruta)), ["snap.json"])
            meta = vp.cargar_snapshot(ruta)
        self.assertEqual(meta[CAMP]["nivel"], "campaign")
        self.assertEqual(meta["ANUNCIO 0"]["campaign_id"], "c1")
        self.assertEqual(meta["CONJ1"]["status"], "ACTIVE")

    def test_error_de_graph_no_filtra_el_token(self):
        def fn(url):
            return {"error": {"code": 190, "message": "token %s vencido" % TOKEN}}
        with self.assertRaises(sm.SnapshotError) as cm:
            sm.construir_snapshot("123", CAMP, TOKEN, pedir_fn=fn, api="https://g.test/v1")
        self.assertIn("190", str(cm.exception))
        buf = io.StringIO()
        with mock.patch.object(sm, "construir_snapshot", side_effect=sm.SnapshotError(str(cm.exception))), \
             mock.patch("bajar_meta_insights.token_de", return_value=TOKEN), \
             contextlib.redirect_stdout(buf):
            rc = sm.main(["--cuenta", "1", "--campana", "x", "--salida", os.path.join(tempfile.gettempdir(), "x.json")])
        self.assertEqual(rc, 1)
        self.assertNotIn(TOKEN, buf.getvalue())

    def test_main_ok_no_imprime_token(self):
        fn, _ = _fake_graph()
        buf = io.StringIO()
        with tempfile.TemporaryDirectory() as d, \
             mock.patch.object(sm, "pedir", fn), \
             mock.patch("bajar_meta_insights.token_de", return_value=TOKEN), \
             contextlib.redirect_stdout(buf):
            salida = os.path.join(d, "s.json")
            rc = sm.main(["--cuenta", "123", "--campana", CAMP, "--salida", salida, "--alias", "GTR7"])
            self.assertTrue(os.path.exists(salida))
            contenido = open(salida, encoding="utf-8").read()
        self.assertEqual(rc, 0)
        self.assertNotIn(TOKEN, buf.getvalue())
        self.assertNotIn(TOKEN, contenido)

    def test_sin_token_mensaje_claro_y_exit_1(self):
        buf = io.StringIO()
        with tempfile.TemporaryDirectory() as d, \
             mock.patch.dict(os.environ, {}, clear=False), \
             contextlib.redirect_stdout(buf):
            os.environ.pop("META_SYSTEM_USER_TOKEN", None)
            rc = sm.main(["--cuenta", "1", "--campana", "x", "--salida", os.path.join(d, "s.json"),
                          "--env", os.path.join(d, "no_existe.env")])
            self.assertFalse(os.path.exists(os.path.join(d, "s.json")))
        self.assertEqual(rc, 1)
        self.assertIn("FALTA EL TOKEN", buf.getvalue())

    def test_help_no_hace_nada_mas(self):
        buf = io.StringIO()
        with mock.patch.object(sm, "pedir", side_effect=AssertionError("red")), \
             contextlib.redirect_stdout(buf), self.assertRaises(SystemExit) as cm:
            sm.main(["--help"])
        self.assertEqual(cm.exception.code, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
