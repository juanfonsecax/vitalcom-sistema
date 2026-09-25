#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_validar_parametros.py — CONGELA el gate de PARAMETRIZACION (T6).

Un alias sucio normal (ej. "1-2" -> "2") solo fragmenta el corte: se reporta blando y no
bloquea. Un alias AMBIGUO (`mapea_a` == REVISAR, ej. nivel_conciencia "3" sin distinguir
3A de 3B) no tiene reemplazo automatico posible -- requiere que un humano decida el
criterio, asi que es una VIOLACION DURA (exit 1), no un aviso mas. Un valor que ya esta en
el vocabulario pasa sin avisos.

USO:  python Ads/_TOOLS/test_validar_parametros.py     (exit 0 = pasa, 1 = falla)
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import validar_parametros as V  # noqa: E402

FALLAS = []


def check(nombre, cond, detalle=""):
    if cond:
        print("  ok   %s" % nombre)
    else:
        print("  FALLA %s  %s" % (nombre, detalle))
        FALLAS.append(nombre)


VOC_BASE = [
    {"eje": "nivel_conciencia", "valor": "1", "etiqueta": "No sabe la causa",
     "tipo_eje": "TESTEABLE", "mapea_a": "", "definicion": "", "dueno_del_vocabulario": "",
     "estado": "VIGENTE"},
    {"eje": "nivel_conciencia", "valor": "2", "etiqueta": "Sabe el problema, no la solucion",
     "tipo_eje": "TESTEABLE", "mapea_a": "", "definicion": "", "dueno_del_vocabulario": "",
     "estado": "VIGENTE"},
    {"eje": "nivel_conciencia", "valor": "3A", "etiqueta": "Conoce el producto, teme comprar",
     "tipo_eje": "TESTEABLE", "mapea_a": "", "definicion": "", "dueno_del_vocabulario": "",
     "estado": "VIGENTE"},
    {"eje": "nivel_conciencia", "valor": "3B", "etiqueta": "Conoce el producto, compara ofertas",
     "tipo_eje": "TESTEABLE", "mapea_a": "", "definicion": "", "dueno_del_vocabulario": "",
     "estado": "VIGENTE"},
    {"eje": "nivel_conciencia", "valor": "1-2", "etiqueta": "alias sucio",
     "tipo_eje": "TESTEABLE", "mapea_a": "2", "definicion": "Valor legado a normalizar a 2.",
     "dueno_del_vocabulario": "", "estado": "VIGENTE"},
    {"eje": "nivel_conciencia", "valor": "3", "etiqueta": "alias sucio AMBIGUO",
     "tipo_eje": "TESTEABLE", "mapea_a": "REVISAR",
     "definicion": "3 a secas no distingue 3A de 3B.", "dueno_del_vocabulario": "",
     "estado": "VIGENTE"},
]


def _fila_anuncio(nivel_conciencia):
    return {"anuncio_norm": "PRODUCTO_TEST", "nivel_conciencia": nivel_conciencia}


def test_alias_revisar_es_violacion_dura():
    """Un alias cuyo mapea_a es REVISAR (ambiguo, sin reemplazo automatico) es DURO."""
    validos, alias, _ = V.cargar_vocabulario(VOC_BASE)
    duros, blandos = V.validar_filas(
        [_fila_anuncio("3")], validos, alias, lambda r: r["anuncio_norm"], "_DIM_ANUNCIOS.csv")
    check("'3' (mapea_a=REVISAR) es violacion dura, no alias sucio",
          len(duros) == 1 and not blandos, (duros, blandos))
    check("el mensaje explica que requiere decision de criterio",
          duros and "REVISAR" in duros[0] and "criterio" in duros[0], duros)


def test_alias_normal_sigue_blando():
    """Un alias con reemplazo mecanico conocido (mapea_a != REVISAR) sigue siendo blando."""
    validos, alias, _ = V.cargar_vocabulario(VOC_BASE)
    duros, blandos = V.validar_filas(
        [_fila_anuncio("1-2")], validos, alias, lambda r: r["anuncio_norm"], "_DIM_ANUNCIOS.csv")
    check("'1-2' (mapea_a=2) sigue siendo alias sucio blando, no duro",
          not duros and len(blandos) == 1, (duros, blandos))
    check("el aviso blando propone el valor de reemplazo",
          blandos and "'2'" in blandos[0], blandos)


def test_valor_valido_pasa_sin_avisos():
    """Un valor ya vigente en el vocabulario (sin alias) no genera ni duro ni blando."""
    validos, alias, _ = V.cargar_vocabulario(VOC_BASE)
    duros, blandos = V.validar_filas(
        [_fila_anuncio("3A")], validos, alias, lambda r: r["anuncio_norm"], "_DIM_ANUNCIOS.csv")
    check("'3A' (valor vigente, no alias) pasa limpio", not duros and not blandos,
          (duros, blandos))


def main():
    for fn in (test_alias_revisar_es_violacion_dura,
               test_alias_normal_sigue_blando,
               test_valor_valido_pasa_sin_avisos):
        print("\n%s" % (fn.__doc__ or fn.__name__).splitlines()[0])
        fn()
    print("\n%s" % ("TODO PASA" if not FALLAS else "FALLAN %d: %s"
                    % (len(FALLAS), ", ".join(FALLAS))))
    return 1 if FALLAS else 0


if __name__ == "__main__":
    sys.exit(main())
