# -*- coding: utf-8 -*-
"""test_requiere_claude.py — USO:  python Ads/_TOOLS/test_requiere_claude.py  (exit 0 = pasa)"""
import os, sys, unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import requiere_claude as rc  # noqa: E402


class RequiereClaudeTests(unittest.TestCase):
    def test_item_valido_normaliza_objetos(self):
        it = rc.item("RENOMBRAR_COPIA", "alta", "Hay un anuncio '- Copia'.", "Renombrá X.",
                     [{"id": 123, "nombre": "X - Copia"}])
        self.assertEqual(it["objetos"], [{"id": "123", "nombre": "X - Copia"}])
        self.assertEqual(rc.validar([it]), [])

    def test_lista_vacia_es_valida(self):
        self.assertEqual(rc.validar([]), [])

    def test_item_invalido_lanza(self):
        with self.assertRaises(ValueError):
            rc.item("renombrar", "alta", "m", "p")          # codigo en minusculas
        with self.assertRaises(ValueError):
            rc.item("X_Y", "baja", "m", "p")                # severidad fuera de dominio
        with self.assertRaises(ValueError):
            rc.item("X_Y", "alta", "", "p")                 # motivo vacio

    def test_validar_detecta_faltantes(self):
        errs = rc.validar([{"codigo": "A_B", "severidad": "media", "motivo": "m"}])
        self.assertTrue(any("pedirle_a_claude" in e for e in errs))
        self.assertTrue(any("objetos" in e for e in errs))
        self.assertTrue(rc.validar("no es lista"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
