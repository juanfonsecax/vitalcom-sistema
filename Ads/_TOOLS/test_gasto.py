#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_gasto.py — GATE del helper de gasto compartido (g07-cimientos T2, 22-sep-2026).

Congela la regla de gasto.IndiceGasto: ad_id gana sobre nombre, nombre gana sobre conjunto,
conjunto gana sobre el fallback de LucidSales; una ventana sin ninguna fila de Meta cae directo
al fallback; y la canonicalizacion de alias.py se aplica de los dos lados del join.

USO:  python Ads/_TOOLS/test_gasto.py     (exit 0 = pasa, 1 = falla)
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gasto  # noqa: E402


VENTANA = {"cuenta_id": "CTA1", "ventana_ini": "2026-09-10", "ventana_fin": "2026-09-10"}


def _venta(**kw):
    r = {"conjunto": "CONJ_A", "anuncio": "ANU_A", "ad_id": "", "spend_usd": "10.0"}
    r.update(VENTANA)
    r.update(kw)
    return r


def _fila_anuncio(**kw):
    r = {"conjunto": "CONJ_A", "anuncio": "ANU_A", "ad_id": "999", "spend_usd": "50.0",
         "fuente": "MetaAPI-directo"}
    r.update(VENTANA)
    r.update(kw)
    return r


def _fila_conjunto(**kw):
    r = {"conjunto": "CONJ_A", "spend_usd": "80.0", "fuente": "MetaAPI-directo"}
    r.update(VENTANA)
    r.update(kw)
    return r


def test_ad_id_gana_sobre_todo():
    idx = gasto.IndiceGasto(
        filas_anuncio=[_fila_anuncio(ad_id="999", spend_usd="50.0")],
        filas_conjunto=[_fila_conjunto(spend_usd="999.0")],
    )
    venta = _venta(ad_id="999", spend_usd="10.0")
    sp, f = idx.gasto_de(venta)
    ok = (sp, f) == (50.0, gasto.FUENTE_AD_ID)
    print(("  OK     " if ok else "  FALLA  ") + "ad_id gana sobre nombre y sobre conjunto"
          + ("" if ok else f"\n         obtenido={(sp, f)}"))
    return 0 if ok else 1


def test_ad_id_normaliza_notacion_cientifica():
    idx = gasto.IndiceGasto(filas_anuncio=[_fila_anuncio(ad_id="120247375927400780")],
                             filas_conjunto=[])
    venta = _venta(ad_id="1.2024737592740078e+17")
    sp, f = idx.gasto_de(venta)
    ok = f == gasto.FUENTE_AD_ID and sp == 50.0
    print(("  OK     " if ok else "  FALLA  ") + "ad_id en notacion cientifica de _FACT_VENTAS "
          "cruza con el entero de _FACT_ENTREGA_ANUNCIO" + ("" if ok else f"\n         {(sp, f)}"))
    return 0 if ok else 1


def test_nombre_gana_sobre_conjunto_sin_ad_id():
    idx = gasto.IndiceGasto(
        filas_anuncio=[_fila_anuncio(ad_id="", spend_usd="42.0")],
        filas_conjunto=[_fila_conjunto(spend_usd="999.0")],
    )
    venta = _venta(ad_id="", spend_usd="10.0")
    sp, f = idx.gasto_de(venta)
    ok = (sp, f) == (42.0, gasto.FUENTE_NOMBRE)
    print(("  OK     " if ok else "  FALLA  ") + "nombre canonico (conjunto+anuncio) gana sobre "
          "el grano conjunto" + ("" if ok else f"\n         obtenido={(sp, f)}"))
    return 0 if ok else 1


def test_grano_conjunto_cuando_el_anuncio_no_aparece_en_meta():
    # El anuncio de LucidSales no tiene fila propia en _FACT_ENTREGA_ANUNCIO (pausado, split
    # distinto): la plata de Meta a nivel conjunto se cuenta completa, no se descarta.
    idx = gasto.IndiceGasto(filas_anuncio=[], filas_conjunto=[_fila_conjunto(spend_usd="80.0")])
    venta = _venta(anuncio="ANU_QUE_NO_ESTA_EN_META", spend_usd="10.0")
    sp, f = idx.gasto_de(venta)
    ok = (sp, f) == (80.0, gasto.FUENTE_CONJUNTO)
    print(("  OK     " if ok else "  FALLA  ") + "sin match a nivel anuncio, cae al grano "
          "conjunto en vez de perder la plata" + ("" if ok else f"\n         obtenido={(sp, f)}"))
    return 0 if ok else 1


def test_fallback_lucidsales_sin_cobertura_meta():
    idx = gasto.IndiceGasto(filas_anuncio=[], filas_conjunto=[])
    venta = _venta(spend_usd="10.0")
    sp, f = idx.gasto_de(venta)
    ok = (sp, f) == (10.0, gasto.FUENTE_FALLBACK)
    print(("  OK     " if ok else "  FALLA  ") + "sin ninguna fila de Meta para esa ventana, "
          "usa el spend_usd de LucidSales" + ("" if ok else f"\n         obtenido={(sp, f)}"))
    return 0 if ok else 1


def test_fuente_no_reconocida_no_cuenta_como_meta():
    # Una fila sembrada a mano (fuente != MetaAPI-directo/AdsManager-export-1d) nunca gana
    # sobre el fallback: sin esto, cualquier siembra de prueba contaminaria el CPA real.
    idx = gasto.IndiceGasto(
        filas_anuncio=[_fila_anuncio(fuente="SIEMBRA_MANUAL", spend_usd="999.0")],
        filas_conjunto=[],
    )
    venta = _venta(ad_id="999", spend_usd="10.0")
    sp, f = idx.gasto_de(venta)
    ok = (sp, f) == (10.0, gasto.FUENTE_FALLBACK)
    print(("  OK     " if ok else "  FALLA  ") + "fuente fuera de FUENTES_META no compite, "
          "cae al fallback" + ("" if ok else f"\n         obtenido={(sp, f)}"))
    return 0 if ok else 1


def test_alias_canonicaliza_los_dos_lados_del_join():
    # gasto.py usa alias.canonico() sobre ambos lados: un conjunto renombrado en Meta debe
    # seguir cruzando con el nombre viejo que trae la venta (o viceversa).
    import alias

    viejo = "GTR0_TEST_CONJ_VIEJO"
    nuevo = "GTR0_TEST_CONJ_NUEVO"
    mapa_original = dict(alias._MAPA or {})
    try:
        alias._MAPA = {viejo: nuevo}
        idx = gasto.IndiceGasto(
            filas_anuncio=[],
            filas_conjunto=[_fila_conjunto(conjunto=nuevo, spend_usd="33.0")],
        )
        venta = _venta(conjunto=viejo, anuncio="ANU_SIN_MATCH", spend_usd="1.0")
        sp, f = idx.gasto_de(venta)
        ok = (sp, f) == (33.0, gasto.FUENTE_CONJUNTO)
        print(("  OK     " if ok else "  FALLA  ") + "un conjunto renombrado sigue cruzando via "
              "alias.canonico()" + ("" if ok else f"\n         obtenido={(sp, f)}"))
        return 0 if ok else 1
    finally:
        alias._MAPA = mapa_original if mapa_original else None


def test_cobertura_cuenta_por_fuente():
    idx = gasto.IndiceGasto(
        filas_anuncio=[_fila_anuncio(ad_id="999")],
        filas_conjunto=[],
    )
    ventas = [_venta(ad_id="999"), _venta(ad_id="", anuncio="OTRO", spend_usd="5.0")]
    cob = idx.cobertura(ventas)
    ok = cob.get(gasto.FUENTE_AD_ID) == 1 and cob.get(gasto.FUENTE_FALLBACK) == 1
    print(("  OK     " if ok else "  FALLA  ") + "cobertura() cuenta filas por fuente_gasto"
          + ("" if ok else f"\n         obtenido={cob}"))
    return 0 if ok else 1


def test_filas_con_gasto_efectivo_preserva_el_original():
    idx = gasto.IndiceGasto(filas_anuncio=[_fila_anuncio(ad_id="999", spend_usd="50.0")],
                             filas_conjunto=[])
    filas = [_venta(ad_id="999", spend_usd="10.0")]
    salida = gasto.filas_con_gasto_efectivo(filas, idx)
    r = salida[0]
    ok = (r["spend_usd"] == 50.0 and r["spend_usd_lucidsales"] == "10.0"
          and r["fuente_gasto"] == gasto.FUENTE_AD_ID and filas[0]["spend_usd"] == "10.0")
    print(("  OK     " if ok else "  FALLA  ") + "filas_con_gasto_efectivo() no muta la entrada "
          "y guarda el spend_usd original de LucidSales" + ("" if ok else f"\n         {r}"))
    return 0 if ok else 1


def test_escribir_ventas_con_gasto_efectivo_roundtrip():
    import csv
    import tempfile

    idx = gasto.IndiceGasto(filas_anuncio=[_fila_anuncio(ad_id="999", spend_usd="50.0")],
                             filas_conjunto=[])
    filas = [_venta(ad_id="999", spend_usd="10.0")]
    with tempfile.TemporaryDirectory() as tmp:
        ruta = os.path.join(tmp, "salida.csv")
        ruta_out, cobertura = gasto.escribir_ventas_con_gasto_efectivo(ruta, filas, idx)
        with open(ruta_out, encoding="utf-8") as f:
            leidas = list(csv.DictReader(f))
        ok = (ruta_out == ruta and len(leidas) == 1
              and leidas[0]["spend_usd"] == "50.0"
              and leidas[0]["fuente_gasto"] == gasto.FUENTE_AD_ID
              and cobertura == {gasto.FUENTE_AD_ID: 1})
        print(("  OK     " if ok else "  FALLA  ") + "escribir_ventas_con_gasto_efectivo() "
              "produce un CSV leible con spend_usd corregido" + ("" if ok else f"\n         {leidas}"))
        return 0 if ok else 1


def main():
    pruebas = [
        test_ad_id_gana_sobre_todo,
        test_ad_id_normaliza_notacion_cientifica,
        test_nombre_gana_sobre_conjunto_sin_ad_id,
        test_grano_conjunto_cuando_el_anuncio_no_aparece_en_meta,
        test_fallback_lucidsales_sin_cobertura_meta,
        test_fuente_no_reconocida_no_cuenta_como_meta,
        test_alias_canonicaliza_los_dos_lados_del_join,
        test_cobertura_cuenta_por_fuente,
        test_filas_con_gasto_efectivo_preserva_el_original,
        test_escribir_ventas_con_gasto_efectivo_roundtrip,
    ]
    fallas = sum(p() for p in pruebas)
    print(f"\n{'0 fallas' if not fallas else str(fallas) + ' falla(s)'}.")
    return 1 if fallas else 0


if __name__ == "__main__":
    sys.exit(main())
