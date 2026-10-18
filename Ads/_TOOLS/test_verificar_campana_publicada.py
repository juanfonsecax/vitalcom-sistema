# -*- coding: utf-8 -*-
"""test_verificar_campana_publicada.py — pruebas del wrapper con el snapshot simulado y una copia
temporal de los CSV (nunca toca PRODUCTOS/ real).

USO:  python Ads/_TOOLS/test_verificar_campana_publicada.py     (exit 0 = pasa)
"""
import csv, io, os, sys, json, shutil, tempfile, unittest, contextlib
from unittest import mock

os.environ.setdefault("PGDATABASE", "vitalcom_test")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import verificar_campana_publicada as vcp  # noqa: E402
import verificar_publicacion as vp         # noqa: E402

CAMP = "GTR7_PROD_CONCEPTOS-C_20261017"
CONJ = ["PROD_ANG_C1", "PROD_ANG_C2"]
ADS = {"PROD_ANG_C1": ["C1 A ~ X", "C1 B ~ X"], "PROD_ANG_C2": ["C2 A ~ X", "C2 B ~ X"]}
COLS_CJ = ["conjunto_meta", "producto_key", "angulo_key", "cuenta_alias", "campana_clave", "fase",
           "formato", "concepto_key", "creativo_id", "estado", "verificado_en_csv", "fecha_alta",
           "origen_angulo", "notas"]


def _csv(ruta, cols, filas):
    with io.open(ruta, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(filas)


def _paquete():
    conjuntos = []
    for i, cj in enumerate(CONJ):
        conjuntos.append({"nombre": cj, "anuncios": [
            {"nombre": ADS[cj][0], "creativo_id": "CR%d" % i, "letra": "A"},
            {"nombre": ADS[cj][1], "creativo_id": "CR%d" % i, "letra": "B"}]})
    return {"cuenta_alias": "GTR7", "cuenta_id": "999", "producto_key": "PROD", "angulo": "ANG",
            "fase": 2, "manifiesto": {"campana": CAMP, "conjuntos": conjuntos}}


def _entidades(extra_ads=(), omitir=()):
    ents = [{"id": "c", "nivel": "campaign", "name": CAMP, "effective_status": "ACTIVE", "campaign_id": "c"}]
    n = 0
    for cj in CONJ:
        ents.append({"id": "s_" + cj, "nivel": "adset", "name": cj, "effective_status": "ACTIVE", "campaign_id": "c"})
        for a in ADS[cj]:
            n += 1
            ents.append({"id": "ad%d" % n, "nivel": "ad", "name": a, "effective_status": "ACTIVE", "campaign_id": "c"})
    for nombre in extra_ads:
        ents.append({"id": "adX", "nivel": "ad", "name": nombre, "effective_status": "ACTIVE", "campaign_id": "c"})
    return [e for e in ents if e["name"] not in omitir]


class WrapperTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        base = self.tmp
        prod = os.path.join(base, "PRODUCTOS")
        os.makedirs(os.path.join(prod, "CARPETA"))
        os.makedirs(os.path.join(base, "Ads", "_INGESTA", "META"))
        _csv(os.path.join(prod, "_DIM_PRODUCTOS.csv"), ["producto_key", "slug_carpeta"],
             [{"producto_key": "PROD", "slug_carpeta": "CARPETA"}])
        with io.open(os.path.join(prod, "CARPETA", "_PUBLICACION_F2C.json"), "w", encoding="utf-8") as f:
            json.dump(_paquete(), f)
        _csv(os.path.join(prod, "_DIM_CREATIVOS.csv"), ["creativo_id", "estado", "ad_id", "notas"],
             [{"creativo_id": "CR0", "estado": "GENERADO", "ad_id": "", "notas": ""},
              {"creativo_id": "CR1", "estado": "GENERADO", "ad_id": "", "notas": ""}])
        # C1 ya esta dado de alta; C2 falta -> debe dar de alta 1 conjunto
        plantilla = {c: "" for c in COLS_CJ}
        plantilla.update({"conjunto_meta": "PROD_ANG_C1", "producto_key": "PROD", "angulo_key": "ANG"})
        _csv(os.path.join(prod, "_DIM_CONJUNTOS.csv"), COLS_CJ, [plantilla])
        self.prod = prod
        self.patches = [
            mock.patch.object(vp, "BASE", base),
            mock.patch.object(vp, "P", lambda *a: os.path.join(prod, *a)),
            mock.patch.object(vp, "CREATIVOS", os.path.join(prod, "_DIM_CREATIVOS.csv")),
        ]
        for p in self.patches:
            p.start()

    def tearDown(self):
        for p in self.patches:
            p.stop()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _snapshot(self, entidades, rc=0):
        def falso(cuenta_id, alias, campana, ruta):
            self.assertEqual((cuenta_id, alias, campana), ("999", "GTR7", CAMP))
            if rc == 0:
                with io.open(ruta, "w", encoding="utf-8") as f:
                    json.dump({"ad_entities": entidades}, f)
            return rc, "snapshot simulado" if rc == 0 else "FALTA EL TOKEN.\n  Ponelo en el .env"
        return mock.patch.object(vcp, "tomar_snapshot", falso)

    def _creativos(self):
        with io.open(os.path.join(self.prod, "_DIM_CREATIVOS.csv"), encoding="utf-8-sig", newline="") as f:
            return list(csv.DictReader(f))

    def test_todo_en_orden_escribe_ids_y_altas(self):
        with self._snapshot(_entidades()):
            res, _ = vcp.verificar("PROD", 2, "C")
        self.assertTrue(res["ok"], res)
        self.assertEqual((res["objetos_declarados"], res["objetos_ok"]), (7, 7))
        self.assertEqual(res["copias"], [])
        self.assertEqual(res["altas"], ["PROD_ANG_C2"])
        self.assertEqual(res["ad_ids_escritos"], 4)
        self.assertIn("7 de 7", res["mensaje_operador"])
        filas = self._creativos()
        self.assertTrue(all(f["estado"] == "PUBLICADO" and f["ad_id"] for f in filas))
        with io.open(os.path.join(self.prod, "_DIM_CONJUNTOS.csv"), encoding="utf-8-sig", newline="") as f:
            filas_cj = list(csv.DictReader(f))
        self.assertEqual(len(filas_cj), 2)
        self.assertEqual(filas_cj[1]["estado"], "ACTIVO")   # --ya-activo

    def test_sin_escribir_no_toca_csv(self):
        antes = self._creativos()
        with self._snapshot(_entidades()):
            res, _ = vcp.verificar("PROD", 2, "C", escribir=False)
        self.assertTrue(res["ok"])
        self.assertEqual(res["ad_ids_escritos"], 0)
        self.assertEqual(self._creativos(), antes)

    def test_copia_bloquea_y_dice_cual_renombrar(self):
        ents = _entidades(extra_ads=["C1 A ~ X - Copia"], omitir=["C1 A ~ X"])
        with self._snapshot(ents):
            res, _ = vcp.verificar("PROD", 2, "C")
        self.assertFalse(res["ok"])
        self.assertEqual([c["nombre"] for c in res["copias"]], ["C1 A ~ X - Copia"])
        self.assertIn("C1 A ~ X - Copia", res["mensaje_operador"])
        self.assertTrue(all(f["ad_id"] == "" for f in self._creativos()))

    def test_faltante_bloquea(self):
        with self._snapshot(_entidades(omitir=["C2 B ~ X"])):
            res, _ = vcp.verificar("PROD", 2, "C")
        self.assertFalse(res["ok"])
        self.assertEqual(res["objetos_ok"], 6)
        self.assertIn("Faltan 1 de 7", res["mensaje_operador"])

    def test_snapshot_falla_da_mensaje_y_no_corre_el_gate(self):
        with self._snapshot([], rc=1), mock.patch.object(vcp, "correr_gate") as gate:
            res, _ = vcp.verificar("PROD", 2, "C")
        gate.assert_not_called()
        self.assertFalse(res["ok"])
        self.assertIn("No pude leer Meta", res["mensaje_operador"])

    def test_paquete_inexistente(self):
        res, _ = vcp.verificar("PROD", 1, "C")
        self.assertFalse(res["ok"])
        self.assertIn("paquete", res["mensaje_operador"])

    def test_main_json_imprime_solo_json_y_exit_code(self):
        buf = io.StringIO()
        with self._snapshot(_entidades()), contextlib.redirect_stdout(buf):
            rc = vcp.main(["--producto", "PROD", "--fase", "2", "--brazo", "C", "--json"])
        self.assertEqual(rc, 0)
        salida = json.loads(buf.getvalue())
        self.assertEqual(set(salida), {"ok", "objetos_declarados", "objetos_ok", "copias", "altas",
                                       "ad_ids_escritos", "mensaje_operador", "detalle"})
        buf = io.StringIO()
        with self._snapshot(_entidades(omitir=["C2 B ~ X"])), contextlib.redirect_stdout(buf):
            rc = vcp.main(["--producto", "PROD", "--fase", "2", "--brazo", "C", "--json", "--sin-escribir"])
        self.assertEqual(rc, 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
