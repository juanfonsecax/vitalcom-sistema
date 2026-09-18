#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_bandas_edad.py — GATE DE LA TABLA UNICA DE BANDA DE EDAD (G0.5 punto 4.2, 15-sep-2026).

Antes de este modulo la tabla vivia triplicada: ETAPA-6.md (4 filas), gen_publicacion.py
BANDA_POR_AVATAR (4 filas) y gen_lanzador.py BANDAS (9 filas) — las dos primeras le
faltaban '35-45'->'35-50' y '30-45'->'30-45'. Este gate congela que:

  · las dos filas que faltaban en la tabla corta siguen presentes;
  · los dos valores que el operador senalo 'del vocabulario sin banda' (25-40 y 30-40,
    los que trae PRODUCTOS/CLEARSTEM/_PLAN.json) tienen fila y no bloquean mas;
  · gen_publicacion.py y gen_lanzador.py leen la MISMA tabla — no pueden volver a
    desincronizarse porque ninguno de los dos la copia.

USO:  python Ads/_TOOLS/test_bandas_edad.py     (exit 0 = pasa, 1 = falla)
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bandas_edad as be  # noqa: E402
import gen_publicacion as gp  # noqa: E402
import gen_lanzador as gl  # noqa: E402


def test_filas_que_antes_faltaban_en_la_tabla_corta():
    ok = be.banda_str("35-45") == "35-50" and be.banda_str("30-45") == "30-45"
    print(("  OK     " if ok else "  FALLA  ")
          + "'35-45'->'35-50' y '30-45'->'30-45' (las que le faltaban a ETAPA-6.md/"
            "gen_publicacion.py frente a gen_lanzador.py) estan en la tabla unica"
          + ("" if ok else f"\n         35-45={be.banda_str('35-45')!r} 30-45={be.banda_str('30-45')!r}"))
    return 0 if ok else 1


def test_valores_del_vocabulario_sin_banda_ya_tienen_fila():
    """25-40 y 30-40: los que CLEARSTEM/_PLAN.json declara para ANTI_FALSIFICACION/
    MEDICOS_FALLARON y TESTIMONIO_RADICAL y que el operador senalo sin fila."""
    ok = be.banda_str("25-40") == "25-40" and be.banda_str("30-40") == "30-40"
    print(("  OK     " if ok else "  FALLA  ")
          + "'25-40' y '30-40' (CLEARSTEM) resuelven a si mismos, ya no faltan en la tabla"
          + ("" if ok else f"\n         25-40={be.banda_str('25-40')!r} 30-40={be.banda_str('30-40')!r}"))
    return 0 if ok else 1


def test_avatar_vacio_es_la_unica_excepcion_amplia():
    ok = be.banda_tupla("") == be.BANDA_AMPLIA_TUPLA == (18, 65)
    print(("  OK     " if ok else "  FALLA  ")
          + "avatar_edad vacio deriva a la banda amplia 18-65, la unica excepcion"
          + ("" if ok else f"\n         obtenido={be.banda_tupla('')!r}"))
    return 0 if ok else 1


def test_valor_no_reconocido_devuelve_none_no_inventa():
    ok = be.banda_str("99-99") is None and be.banda_tupla("99-99") is None
    print(("  OK     " if ok else "  FALLA  ")
          + "un avatar_edad fuera de tabla devuelve None: el llamador decide si bloquea, "
            "el modulo no inventa una banda"
          + ("" if ok else f"\n         str={be.banda_str('99-99')!r} tupla={be.banda_tupla('99-99')!r}"))
    return 0 if ok else 1


def test_gen_publicacion_y_gen_lanzador_leen_la_misma_tabla():
    """El fix real: antes de este modulo, un avatar presente solo en la tabla de
    gen_lanzador.py (p.ej. '35-45') bloqueaba en gen_publicacion.py y viceversa."""
    casos = ["45-65", "45-60", "35-55", "35-45", "25-35", "30-45", "40-55", "45-55",
             "25-45", "25-40", "30-40"]
    fallas = []
    for avatar in casos:
        tup, _ = gp.derivar_banda(avatar, "PRODUCTO_X")
        destino_str, _ = gl.banda_edad(avatar)
        if tup is None:
            fallas.append("gen_publicacion.derivar_banda(%r) bloqueo (None)" % avatar)
            continue
        esperado = "%d-%d" % tup
        if destino_str != esperado:
            fallas.append("%r: gen_publicacion=%s gen_lanzador=%s" % (avatar, esperado, destino_str))
    ok = not fallas
    print(("  OK     " if ok else "  FALLA  ")
          + "gen_publicacion.py y gen_lanzador.py derivan la MISMA banda para los %d avatares "
            "de la tabla" % len(casos)
          + ("" if ok else "\n         " + "; ".join(fallas)))
    return 0 if ok else 1


def main():
    fallas = 0
    fallas += test_filas_que_antes_faltaban_en_la_tabla_corta()
    fallas += test_valores_del_vocabulario_sin_banda_ya_tienen_fila()
    fallas += test_avatar_vacio_es_la_unica_excepcion_amplia()
    fallas += test_valor_no_reconocido_devuelve_none_no_inventa()
    fallas += test_gen_publicacion_y_gen_lanzador_leen_la_misma_tabla()
    print(f"\n{'0 fallas' if not fallas else str(fallas) + ' falla(s)'}.")
    return 1 if fallas else 0


if __name__ == "__main__":
    sys.exit(main())
