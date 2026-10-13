#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_gasto.py — GATE del helper de gasto compartido (g07-cimientos T2, 22-sep-2026).

Rediseñado tras un defecto de conteo encontrado en review: una primera versión resolvía el gasto
FILA POR FILA de _FACT_VENTAS.csv, y cuando ninguna fila de Meta a nivel anuncio matcheaba le
copiaba a esa fila el spend_usd COMPLETO del conjunto. Un conjunto con N anuncios sin match
individual multiplicaba su gasto real por N; y el gasto de Meta de un anuncio SIN ninguna venta
atribuida nunca aparecía en ningún lado. Este archivo congela el diseño correcto: Meta y
LucidSales se agregan POR SEPARADO a un grano donde cada dólar de Meta se cuenta una sola vez, y
se cruzan con un FULL OUTER JOIN.

USO:  python Ads/_TOOLS/test_gasto.py     (exit 0 = pasa, 1 = falla)
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gasto  # noqa: E402


VENTANA = {"cuenta_id": "CTA1", "ventana_ini": "2026-09-10", "ventana_fin": "2026-09-10"}


def _venta(**kw):
    r = {"producto_key": "PX", "conjunto": "CONJ_A", "anuncio": "ANU_A", "campana": "CAMP",
         "ad_id": "", "ventas": "1", "mensajes": "5", "spend_usd": "10.0"}
    r.update(VENTANA)
    r.update(kw)
    return r


def _fila_entrega_conjunto(**kw):
    r = {"producto_key": "PX", "conjunto": "CONJ_A", "spend_usd": "80.0", "fuente": "MetaAPI-directo"}
    r.update(VENTANA)
    r.update(kw)
    return r


def _fila_entrega_anuncio(**kw):
    r = {"producto_key": "PX", "conjunto": "CONJ_A", "anuncio": "ANU_A", "campana": "CAMP",
         "ad_id": "999", "spend_usd": "50.0", "fuente": "MetaAPI-directo"}
    r.update(VENTANA)
    r.update(kw)
    return r


def _una_celda(filas, **filtro):
    cand = [f for f in filas if all(f.get(k) == v for k, v in filtro.items())]
    return cand[0] if len(cand) == 1 else cand


# ── grano CONJUNTO-VENTANA (decidir.py, flujo.py) ───────────────────────────────────────────────

def test_conjunto_meta_gana_y_se_cuenta_una_sola_vez():
    filas = gasto.gasto_por_conjunto_ventana(
        filas_venta=[_venta(spend_usd="10.0")],
        filas_entrega_conjunto=[_fila_entrega_conjunto(spend_usd="80.0")],
    )
    ok = len(filas) == 1 and filas[0]["spend_usd"] == 80.0 and filas[0]["fuente_gasto"] == gasto.FUENTE_CONJUNTO
    print(("  OK     " if ok else "  FALLA  ") + "una celda conjunto+ventana con cobertura Meta "
          "usa el gasto de Meta" + ("" if ok else f"\n         {filas}"))
    return 0 if ok else 1


def test_n_anuncios_sin_match_no_multiplican_el_gasto_del_conjunto():
    """EL DEFECTO ORIGINAL: 3 anuncios distintos del mismo conjunto+ventana, ninguno con match
    individual a nivel anuncio. El gasto del conjunto (Meta) debe contarse UNA vez, no 3."""
    ventas = [_venta(anuncio="ANU_%d" % i, spend_usd="10.0") for i in range(3)]
    filas = gasto.gasto_por_conjunto_ventana(
        filas_venta=ventas,
        filas_entrega_conjunto=[_fila_entrega_conjunto(spend_usd="80.0")],
    )
    ok = len(filas) == 1 and filas[0]["spend_usd"] == 80.0 and filas[0]["ventas"] == 3.0
    print(("  OK     " if ok else "  FALLA  ") + "3 anuncios sin match individual en el mismo "
          "conjunto+ventana NO multiplican el gasto de Meta (antes: 3x $80 = $240)"
          + ("" if ok else f"\n         {filas}"))
    return 0 if ok else 1


def test_meta_sin_ninguna_venta_se_cuenta_igual():
    """Full outer join: un conjunto con gasto de Meta pero SIN ninguna fila de venta atribuida
    sigue apareciendo, con ventas=0 — no se pierde la plata."""
    filas = gasto.gasto_por_conjunto_ventana(
        filas_venta=[],
        filas_entrega_conjunto=[_fila_entrega_conjunto(spend_usd="80.0")],
    )
    ok = len(filas) == 1 and filas[0]["spend_usd"] == 80.0 and filas[0]["ventas"] == 0.0
    print(("  OK     " if ok else "  FALLA  ") + "gasto de Meta sin ninguna venta atribuida se "
          "cuenta igual (full outer join), no se pierde" + ("" if ok else f"\n         {filas}"))
    return 0 if ok else 1


def test_conjunto_sin_dim_todavia_cuenta_a_nivel_producto():
    """Un conjunto NUESTRO (producto_key ya clasificado por producto_de(), via patron de nombre
    o DIM) que TODAVIA no tiene fila de angulo_key en
    _DIM_CONJUNTOS.csv sigue apareciendo en el gasto de su producto_key — esta funcion trabaja
    al grano (producto_key, cuenta_id, ventana, conjunto), nunca consulta _DIM_CONJUNTOS.csv, asi
    que un conjunto sin dimension NO se pierde ni se excluye: solo le falta el angulo, que es un
    problema de REGISTRO (lo cierra ETAPA-6), no de conteo de plata."""
    filas = gasto.gasto_por_conjunto_ventana(
        filas_venta=[_venta(conjunto="CONJUNTO_SIN_DIM_TODAVIA", spend_usd="10.0")],
        filas_entrega_conjunto=[_fila_entrega_conjunto(conjunto="CONJUNTO_SIN_DIM_TODAVIA",
                                                        spend_usd="80.0")],
    )
    ok = (len(filas) == 1 and filas[0]["producto_key"] == "PX" and filas[0]["spend_usd"] == 80.0
          and filas[0]["conjunto"] == "CONJUNTO_SIN_DIM_TODAVIA")
    print(("  OK     " if ok else "  FALLA  ") + "un conjunto sin fila en _DIM_CONJUNTOS.csv sigue "
          "contando su gasto bajo su producto_key (no se descarta por falta de registro)"
          + ("" if ok else f"\n         {filas}"))
    return 0 if ok else 1


def test_conjunto_sin_cobertura_meta_cae_a_lucidsales():
    filas = gasto.gasto_por_conjunto_ventana(
        filas_venta=[_venta(spend_usd="7.0"), _venta(anuncio="ANU_B", spend_usd="3.0")],
        filas_entrega_conjunto=[],
    )
    ok = len(filas) == 1 and filas[0]["spend_usd"] == 10.0 and filas[0]["fuente_gasto"] == gasto.FUENTE_FALLBACK
    print(("  OK     " if ok else "  FALLA  ") + "sin cobertura de Meta, se suma el spend_usd de "
          "LucidSales de todas las ventas de esa celda" + ("" if ok else f"\n         {filas}"))
    return 0 if ok else 1


def test_conjunto_sin_fila_propia_en_una_cuenta_cubierta_por_meta_no_suma_su_gasto():
    """Mismo dia y misma cuenta que una fila de Meta, pero un conjunto que Meta no lista: su gasto
    ya esta en Meta (con otro nombre) o fue cero. LucidSales conserva las ventas, no el gasto."""
    filas = gasto.gasto_por_conjunto_ventana(
        filas_venta=[_venta(conjunto="CONJ_A"), _venta(conjunto="CONJ_B", anuncio="ANU_B")],
        filas_entrega_conjunto=[_fila_entrega_conjunto(conjunto="CONJ_A", spend_usd="80.0")],
    )
    b = _una_celda(filas, conjunto="CONJ_B")
    ok = (len(filas) == 2 and b["spend_usd"] == 0.0 and b["ventas"] == 1.0
          and b["fuente_gasto"] == gasto.FUENTE_CUBIERTO and abs(sum(x["spend_usd"] for x in filas) - 80.0) < 1e-9)
    print(("  OK     " if ok else "  FALLA  ") + "un conjunto sin fila de Meta en una cuenta-dia cubierta "
          "conserva sus ventas y aporta gasto 0" + ("" if ok else f"\n         {filas}"))
    return 0 if ok else 1


def test_conjuntos_distintos_no_se_mezclan():
    filas = gasto.gasto_por_conjunto_ventana(
        filas_venta=[_venta(conjunto="CONJ_A"), _venta(conjunto="CONJ_B", anuncio="ANU_B", cuenta_id="CTA2")],
        filas_entrega_conjunto=[_fila_entrega_conjunto(conjunto="CONJ_A", spend_usd="80.0")],
    )
    a = _una_celda(filas, conjunto="CONJ_A")
    b = _una_celda(filas, conjunto="CONJ_B")   # su cuenta (CTA2) no tiene cobertura de Meta
    ok = (len(filas) == 2 and a["spend_usd"] == 80.0 and a["fuente_gasto"] == gasto.FUENTE_CONJUNTO
          and b["spend_usd"] == 10.0 and b["fuente_gasto"] == gasto.FUENTE_FALLBACK)
    print(("  OK     " if ok else "  FALLA  ") + "dos conjuntos distintos resuelven su gasto por "
          "separado (uno con Meta, otro con fallback)" + ("" if ok else f"\n         {filas}"))
    return 0 if ok else 1


def test_alias_canonicaliza_los_dos_lados_del_join():
    import alias
    viejo, nuevo = "GTR0_TEST_CONJ_VIEJO", "GTR0_TEST_CONJ_NUEVO"
    mapa_original = dict(alias._MAPA or {})
    try:
        alias._MAPA = {viejo: nuevo}
        filas = gasto.gasto_por_conjunto_ventana(
            filas_venta=[_venta(conjunto=viejo, spend_usd="1.0")],
            filas_entrega_conjunto=[_fila_entrega_conjunto(conjunto=nuevo, spend_usd="33.0")],
        )
        ok = len(filas) == 1 and filas[0]["conjunto"] == nuevo and filas[0]["spend_usd"] == 33.0
        print(("  OK     " if ok else "  FALLA  ") + "un conjunto renombrado sigue cruzando via "
              "alias.canonico()" + ("" if ok else f"\n         {filas}"))
        return 0 if ok else 1
    finally:
        alias._MAPA = mapa_original if mapa_original else None


def test_dos_grafias_meta_que_canonicalizan_igual_no_duplican_con_fila_de_anuncio_presente():
    """Regresion de review round 2 (22-sep-2026, caso real CLEARSTEM/MEDICOS_FALLARON): DOS filas
    de _FACT_ENTREGA.csv con grafias DISTINTAS que canonicalizan al MISMO conjunto (p.ej. una
    grafia vieja pre-rename y su "- Copia"), MAS una fila de _FACT_ENTREGA_ANUNCIO.csv para ese
    mismo conjunto -- el grano CONJUNTO debe sumar las dos grafias exactamente una vez cada una
    (nunca tres), y nunca sumarle encima el gasto del grano ANUNCIO (son dos funciones separadas,
    gasto_por_conjunto_ventana() ni siquiera lee el fact de anuncio)."""
    import alias
    viejo, nuevo = "GTR13_TEST_R1 + 25ANOS - Copia", "GTR13_TEST_R1"
    mapa_original = dict(alias._MAPA or {})
    try:
        alias._MAPA = {viejo: nuevo}
        filas_conjunto = [
            _fila_entrega_conjunto(conjunto=viejo, spend_usd="30.0"),   # grafia vieja
            _fila_entrega_conjunto(conjunto=nuevo, spend_usd="20.0"),   # grafia ya canonica
        ]
        filas_anuncio = [_fila_entrega_anuncio(conjunto=nuevo, spend_usd="999.0")]  # otro grano
        filas = gasto.gasto_por_conjunto_ventana(
            filas_venta=[_venta(conjunto=nuevo, spend_usd="1.0")],
            filas_entrega_conjunto=filas_conjunto,
        )
        ok = len(filas) == 1 and filas[0]["conjunto"] == nuevo and filas[0]["spend_usd"] == 50.0
        print(("  OK     " if ok else "  FALLA  ") + "dos grafias Meta que canonicalizan al mismo "
              "conjunto se suman UNA vez cada una (30+20=50), sin importar que exista una fila de "
              "anuncio para el mismo conjunto (grano separado)" + ("" if ok else f"\n         {filas}"))
        return 0 if ok else 1
    finally:
        alias._MAPA = mapa_original if mapa_original else None


def test_fuente_no_reconocida_no_cuenta_como_meta():
    filas = gasto.gasto_por_conjunto_ventana(
        filas_venta=[_venta(spend_usd="10.0")],
        filas_entrega_conjunto=[_fila_entrega_conjunto(fuente="SIEMBRA_MANUAL", spend_usd="999.0")],
    )
    ok = len(filas) == 1 and filas[0]["spend_usd"] == 10.0 and filas[0]["fuente_gasto"] == gasto.FUENTE_FALLBACK
    print(("  OK     " if ok else "  FALLA  ") + "fuente fuera de FUENTES_META no compite, cae al "
          "fallback" + ("" if ok else f"\n         {filas}"))
    return 0 if ok else 1


# ── grano ANUNCIO-VENTANA (sembrar_anuncios.py, análisis de concepto) ──────────────────────────

def test_anuncio_ad_id_gana_y_se_cuenta_una_vez():
    filas = gasto.gasto_por_anuncio_ventana(
        filas_venta=[_venta(ad_id="999")],
        filas_entrega_anuncio=[_fila_entrega_anuncio(ad_id="999", spend_usd="50.0")],
    )
    ok = len(filas) == 1 and filas[0]["spend_usd"] == 50.0 and filas[0]["fuente_gasto"] == gasto.FUENTE_AD_ID
    print(("  OK     " if ok else "  FALLA  ") + "match por ad_id usa el gasto de Meta a nivel "
          "anuncio" + ("" if ok else f"\n         {filas}"))
    return 0 if ok else 1


def test_anuncio_ad_id_normaliza_notacion_cientifica():
    filas = gasto.gasto_por_anuncio_ventana(
        filas_venta=[_venta(ad_id="1.2024737592740078e+17")],
        filas_entrega_anuncio=[_fila_entrega_anuncio(ad_id="120247375927400780", spend_usd="50.0")],
    )
    ok = len(filas) == 1 and filas[0]["spend_usd"] == 50.0 and filas[0]["fuente_gasto"] == gasto.FUENTE_AD_ID
    print(("  OK     " if ok else "  FALLA  ") + "ad_id en notación científica cruza con el "
          "entero de Meta" + ("" if ok else f"\n         {filas}"))
    return 0 if ok else 1


def test_anuncio_renombrado_no_duplica_bajo_ad_id():
    """Un anuncio renombrado ('- Copia') en Meta pero con el MISMO ad_id no debe generar una
    segunda celda ni sumarse dos veces: el ad_id manda sobre el nombre."""
    filas = gasto.gasto_por_anuncio_ventana(
        filas_venta=[_venta(ad_id="999", anuncio="ANU_A - Copia")],
        filas_entrega_anuncio=[_fila_entrega_anuncio(ad_id="999", anuncio="ANU_A", spend_usd="50.0")],
    )
    ok = len(filas) == 1 and filas[0]["spend_usd"] == 50.0
    print(("  OK     " if ok else "  FALLA  ") + "un anuncio renombrado ('- Copia') con el mismo "
          "ad_id no duplica la celda" + ("" if ok else f"\n         {filas}"))
    return 0 if ok else 1


def test_anuncio_sin_ad_id_usa_nombre_pero_no_hereda_el_conjunto():
    """Sin ad_id, el match es por (campaña, conjunto, anuncio) exacto -- nunca cae al total del
    conjunto (ESE fue el defecto: acá simplemente no hay match y se va a LucidSales)."""
    filas = gasto.gasto_por_anuncio_ventana(
        filas_venta=[_venta(ad_id="", anuncio="ANU_DISTINTO", spend_usd="10.0", cuenta_id="CTA2")],
        filas_entrega_anuncio=[_fila_entrega_anuncio(ad_id="", anuncio="ANU_A", spend_usd="50.0")],
    )
    ok = len(filas) == 2  # dos anuncios distintos, ninguno hereda el gasto del otro
    fila_venta = _una_celda(filas, anuncio="ANU_DISTINTO")
    ok = ok and fila_venta["spend_usd"] == 10.0 and fila_venta["fuente_gasto"] == gasto.FUENTE_FALLBACK
    print(("  OK     " if ok else "  FALLA  ") + "un anuncio sin ad_id y sin nombre que matchee "
          "cae a LucidSales, nunca hereda el gasto de otro anuncio" + ("" if ok else f"\n         {filas}"))
    return 0 if ok else 1


def test_anuncio_meta_sin_venta_se_cuenta_igual():
    filas = gasto.gasto_por_anuncio_ventana(
        filas_venta=[],
        filas_entrega_anuncio=[_fila_entrega_anuncio(ad_id="999", spend_usd="50.0")],
    )
    ok = len(filas) == 1 and filas[0]["spend_usd"] == 50.0 and filas[0]["ventas"] == 0.0
    print(("  OK     " if ok else "  FALLA  ") + "un anuncio de Meta sin ninguna venta atribuida "
          "sigue contando su gasto" + ("" if ok else f"\n         {filas}"))
    return 0 if ok else 1


def test_misma_campana_conjunto_anuncio_en_dos_campanas_no_colisiona():
    """El mismo texto de anuncio se repite a propósito en dos campañas de FASE 2 (replicación de
    concepto, ver test_flujo.py fixture_conceptos_al_filo) -- deben quedar en celdas separadas."""
    filas = gasto.gasto_por_anuncio_ventana(
        filas_venta=[_venta(campana="CAMP_B", ad_id="", spend_usd="5.0"),
                     _venta(campana="CAMP_C", ad_id="", spend_usd="7.0")],
        filas_entrega_anuncio=[],
    )
    b = _una_celda(filas, campana="CAMP_B")
    c = _una_celda(filas, campana="CAMP_C")
    ok = len(filas) == 2 and b["spend_usd"] == 5.0 and c["spend_usd"] == 7.0
    print(("  OK     " if ok else "  FALLA  ") + "el mismo anuncio+conjunto en dos campañas "
          "distintas no colapsa en una sola celda" + ("" if ok else f"\n         {filas}"))
    return 0 if ok else 1


# ── INVARIANTE (requerido en review): ni se pierde ni se inventa un centavo ────────────────────

def test_invariante_conservacion_de_plata_grano_conjunto():
    """SUM(gasto efectivo) == SUM(gasto Meta de las celdas cubiertas) + SUM(fallback LucidSales
    de las celdas sin cobertura) -- para cualquier mezcla de filas, al centavo."""
    ventas = [
        _venta(conjunto="CONJ_A", anuncio="A1", spend_usd="10.0"),
        _venta(conjunto="CONJ_A", anuncio="A2", spend_usd="8.0"),   # mismo conjunto, sin match individual
        _venta(conjunto="CONJ_A", anuncio="A3", spend_usd="6.0"),
        _venta(conjunto="CONJ_B", anuncio="B1", spend_usd="15.0", cuenta_id="CTA2"),  # sin cobertura Meta
        _venta(conjunto="CONJ_C", anuncio="C1", spend_usd="1.0"),
    ]
    entrega = [
        _fila_entrega_conjunto(conjunto="CONJ_A", spend_usd="80.0"),
        _fila_entrega_conjunto(conjunto="CONJ_C", spend_usd="45.0"),  # CONJ_C: Meta > LucidSales
        _fila_entrega_conjunto(conjunto="CONJ_D", spend_usd="12.0"),  # Meta-only, ninguna venta
    ]
    filas = gasto.gasto_por_conjunto_ventana(filas_venta=ventas, filas_entrega_conjunto=entrega)

    efectivo = sum(f["spend_usd"] for f in filas)
    meta_cubierto = sum(f["spend_usd"] for f in filas if f["fuente_gasto"] == gasto.FUENTE_CONJUNTO)
    fallback = sum(f["spend_usd"] for f in filas if f["fuente_gasto"] == gasto.FUENTE_FALLBACK)
    meta_esperado = 80.0 + 45.0 + 12.0     # CONJ_A + CONJ_C + CONJ_D, cada uno UNA vez
    fallback_esperado = 15.0               # CONJ_B, LucidSales

    ok = (abs(efectivo - (meta_esperado + fallback_esperado)) < 1e-9
          and abs(meta_cubierto - meta_esperado) < 1e-9
          and abs(fallback - fallback_esperado) < 1e-9)
    print(("  OK     " if ok else "  FALLA  ") + "INVARIANTE: efectivo == Meta(cubierto) + "
          "LucidSales(fallback), al centavo, con conjuntos multi-anuncio y Meta-only mezclados"
          + ("" if ok else f"\n         efectivo={efectivo} meta={meta_cubierto} fallback={fallback}"))
    return 0 if ok else 1


def test_invariante_conservacion_de_plata_grano_anuncio():
    ventas = [
        _venta(ad_id="1", anuncio="A1", spend_usd="10.0"),
        _venta(ad_id="", anuncio="A2", campana="CAMP", spend_usd="8.0", cuenta_id="CTA2"),   # sin Meta -> fallback
        _venta(ad_id="", anuncio="A3", campana="CAMP", spend_usd="6.0", cuenta_id="CTA2"),   # sin Meta -> fallback
    ]
    entrega = [
        _fila_entrega_anuncio(ad_id="1", anuncio="A1", spend_usd="50.0"),
        _fila_entrega_anuncio(ad_id="2", anuncio="A4", spend_usd="20.0"),  # Meta-only, sin venta
    ]
    filas = gasto.gasto_por_anuncio_ventana(filas_venta=ventas, filas_entrega_anuncio=entrega)

    efectivo = sum(f["spend_usd"] for f in filas)
    meta_cubierto = sum(f["spend_usd"] for f in filas
                         if f["fuente_gasto"] in (gasto.FUENTE_AD_ID, gasto.FUENTE_NOMBRE))
    fallback = sum(f["spend_usd"] for f in filas if f["fuente_gasto"] == gasto.FUENTE_FALLBACK)
    meta_esperado = 50.0 + 20.0
    fallback_esperado = 8.0 + 6.0

    ok = (abs(efectivo - (meta_esperado + fallback_esperado)) < 1e-9
          and abs(meta_cubierto - meta_esperado) < 1e-9
          and abs(fallback - fallback_esperado) < 1e-9)
    print(("  OK     " if ok else "  FALLA  ") + "INVARIANTE (grano anuncio): efectivo == "
          "Meta(cubierto) + LucidSales(fallback), al centavo"
          + ("" if ok else f"\n         efectivo={efectivo} meta={meta_cubierto} fallback={fallback}"))
    return 0 if ok else 1


# ── indice_gasto_por_anuncio() / clave_anuncio() (usado por sembrar_anuncios.py) ───────────────

def test_indice_gasto_por_anuncio_resuelve_por_llave():
    ventas = [_venta(ad_id="999")]
    entrega = [_fila_entrega_anuncio(ad_id="999", spend_usd="50.0")]
    idx = gasto.indice_gasto_por_anuncio(filas_venta=ventas, filas_entrega_anuncio=entrega)
    k = gasto.clave_anuncio(ventas[0])
    ok = idx.get(k) == (50.0, gasto.FUENTE_AD_ID)
    print(("  OK     " if ok else "  FALLA  ") + "indice_gasto_por_anuncio()[clave_anuncio(r)] "
          "resuelve el mismo valor que gasto_por_anuncio_ventana()" + ("" if ok else f"\n         {idx}"))
    return 0 if ok else 1


def test_escribir_conjunto_ventana_csv_roundtrip():
    import csv
    import tempfile
    ventas = [_venta(spend_usd="10.0")]
    entrega = [_fila_entrega_conjunto(spend_usd="50.0")]
    with tempfile.TemporaryDirectory() as tmp:
        ruta = os.path.join(tmp, "salida.csv")
        ruta_out, cobertura = gasto.escribir_conjunto_ventana_csv(
            ruta, filas_venta=ventas, filas_entrega_conjunto=entrega)
        with open(ruta_out, encoding="utf-8") as f:
            leidas = list(csv.DictReader(f))
        ok = (ruta_out == ruta and len(leidas) == 1 and leidas[0]["spend_usd"] == "50.0"
              and leidas[0]["rol_ventana"] == "BASE" and cobertura == {gasto.FUENTE_CONJUNTO: 1})
        print(("  OK     " if ok else "  FALLA  ") + "escribir_conjunto_ventana_csv() produce un "
              "CSV leíble, una fila por celda" + ("" if ok else f"\n         {leidas}"))
        return 0 if ok else 1


def test_conjunto_api_directa_supera_export_del_mismo_dia_aunque_cambie_el_nombre():
    """Doble conteo real (13-oct-2026): el export de Ads Manager y la API directa describen el
    MISMO dia de la MISMA cuenta con otro nombre de conjunto. Solo cuenta la API directa."""
    filas = gasto.gasto_por_conjunto_ventana(
        filas_venta=[],
        filas_entrega_conjunto=[
            _fila_entrega_conjunto(conjunto="CONJ_A", spend_usd="80.0"),
            _fila_entrega_conjunto(conjunto="CONJ_A viejo", spend_usd="60.0", fuente="AdsManager-export-1d"),
        ],
    )
    total = sum(f["spend_usd"] for f in filas)
    ok = abs(total - 80.0) < 1e-9
    print(("  OK     " if ok else "  FALLA  ") + "grano conjunto: dos fuentes para la misma cuenta-dia no se suman"
          + ("" if ok else f"\n         {filas}"))
    return 0 if ok else 1


def test_conjunto_export_sin_cobertura_api_sigue_contando():
    filas = gasto.gasto_por_conjunto_ventana(
        filas_venta=[],
        filas_entrega_conjunto=[
            _fila_entrega_conjunto(conjunto="CONJ_A", spend_usd="80.0"),
            _fila_entrega_conjunto(conjunto="CONJ_A", spend_usd="60.0", fuente="AdsManager-export-1d",
                                   ventana_ini="2026-09-05", ventana_fin="2026-09-05"),
        ],
    )
    total = sum(f["spend_usd"] for f in filas)
    ok = abs(total - 140.0) < 1e-9
    print(("  OK     " if ok else "  FALLA  ") + "grano conjunto: un dia sin API directa conserva el export"
          + ("" if ok else f"\n         {filas}"))
    return 0 if ok else 1


def test_anuncio_api_directa_supera_export_del_mismo_dia():
    filas = gasto.gasto_por_anuncio_ventana(
        filas_venta=[],
        filas_entrega_anuncio=[
            _fila_entrega_anuncio(ad_id="999", spend_usd="50.0"),
            _fila_entrega_anuncio(ad_id="", anuncio="ANU viejo", spend_usd="40.0",
                                  fuente="AdsManager-export-1d"),
        ],
    )
    total = sum(f["spend_usd"] for f in filas)
    ok = abs(total - 50.0) < 1e-9
    print(("  OK     " if ok else "  FALLA  ") + "grano anuncio: dos fuentes para la misma cuenta-dia no se suman"
          + ("" if ok else f"\n         {filas}"))
    return 0 if ok else 1


def test_ventas_de_ventana_multidia_cubierta_por_meta_no_suman_su_gasto_de_lucidsales():
    """Doble conteo real (13-oct-2026): LucidSales trae ventanas de 3-8 dias que nunca calzan con las
    filas diarias de Meta, asi que caian al fallback y su spend_usd se SUMABA al de Meta, que ya
    cubria esos dias. Las ventas se conservan; el gasto lo pone Meta una sola vez."""
    meta = [_fila_entrega_conjunto(ventana_ini="2026-07-10", ventana_fin="2026-07-10", spend_usd="30.0"),
            _fila_entrega_conjunto(ventana_ini="2026-07-11", ventana_fin="2026-07-11", spend_usd="40.0")]
    venta = _venta(ventana_ini="2026-07-10", ventana_fin="2026-07-11", spend_usd="55.0", ventas="2")
    filas = gasto.gasto_por_conjunto_ventana(filas_venta=[venta], filas_entrega_conjunto=meta)
    total = sum(f["spend_usd"] for f in filas)
    ventas = sum(f["ventas"] for f in filas)
    cub = [f for f in filas if f["fuente_gasto"] == gasto.FUENTE_CUBIERTO]
    ok = abs(total - 70.0) < 1e-9 and ventas == 2 and len(cub) == 1 and cub[0]["spend_usd"] == 0.0
    print(("  OK     " if ok else "  FALLA  ") + "ventana de LucidSales cubierta por Meta: ventas si, gasto no"
          + ("" if ok else f"\n         {filas}"))
    return 0 if ok else 1


def test_cuenta_con_api_sin_filas_un_dia_en_que_otra_cuenta_si_tuvo_es_dia_sin_gasto():
    """La API se consulta cuenta por cuenta, dia por dia: si otra cuenta tiene filas ese dia y esta
    cuenta (que la API si cubre otros dias) no, ese dia no tuvo gasto. Una cuenta que la API nunca
    consulto (CTA3) si cae al fallback de LucidSales."""
    meta = [_fila_entrega_conjunto(cuenta_id="CTA1", ventana_ini="2026-07-10", ventana_fin="2026-07-10"),
            _fila_entrega_conjunto(cuenta_id="CTA2", ventana_ini="2026-07-10", ventana_fin="2026-07-10"),
            _fila_entrega_conjunto(cuenta_id="CTA2", ventana_ini="2026-07-20", ventana_fin="2026-07-20")]
    ventas = [_venta(cuenta_id="CTA1", ventana_ini="2026-07-20", ventana_fin="2026-07-20", spend_usd="9.0"),
              _venta(cuenta_id="CTA3", ventana_ini="2026-07-20", ventana_fin="2026-07-20", spend_usd="7.0")]
    filas = gasto.gasto_por_conjunto_ventana(filas_venta=ventas, filas_entrega_conjunto=meta)
    uno = _una_celda(filas, cuenta_id="CTA1", ventana_ini="2026-07-20")
    tres = _una_celda(filas, cuenta_id="CTA3")
    ok = (uno["fuente_gasto"] == gasto.FUENTE_CUBIERTO and uno["spend_usd"] == 0.0
          and tres["fuente_gasto"] == gasto.FUENTE_FALLBACK and tres["spend_usd"] == 7.0)
    print(("  OK     " if ok else "  FALLA  ") + "dia sin filas de una cuenta que la API cubre = sin gasto; "
          "una cuenta que la API nunca consulto cae al fallback" + ("" if ok else f"\n         {filas}"))
    return 0 if ok else 1


def test_ventana_sin_cobertura_de_meta_sigue_cayendo_al_fallback():
    meta = [_fila_entrega_conjunto(ventana_ini="2026-07-10", ventana_fin="2026-07-10", spend_usd="30.0")]
    venta = _venta(ventana_ini="2026-07-20", ventana_fin="2026-07-21", spend_usd="55.0", ventas="2")
    filas = gasto.gasto_por_conjunto_ventana(filas_venta=[venta], filas_entrega_conjunto=meta)
    fb = [f for f in filas if f["fuente_gasto"] == gasto.FUENTE_FALLBACK]
    ok = len(fb) == 1 and fb[0]["spend_usd"] == 55.0
    print(("  OK     " if ok else "  FALLA  ") + "una ventana que Meta no cubre conserva el gasto de LucidSales"
          + ("" if ok else f"\n         {filas}"))
    return 0 if ok else 1


def test_cuenta_id_con_sufijo_punto_cero_calza_con_el_de_meta():
    """LucidSales viejo guarda la cuenta como float ('598687956219141.0'); Meta como entero."""
    venta = _venta(cuenta_id="123.0", spend_usd="10.0")
    meta = _fila_entrega_conjunto(cuenta_id="123", spend_usd="80.0")
    filas = gasto.gasto_por_conjunto_ventana(filas_venta=[venta], filas_entrega_conjunto=[meta])
    ok = len(filas) == 1 and filas[0]["fuente_gasto"] == gasto.FUENTE_CONJUNTO and filas[0]["spend_usd"] == 80.0
    print(("  OK     " if ok else "  FALLA  ") + "cuenta_id '123.0' (LucidSales) y '123' (Meta) son la misma cuenta"
          + ("" if ok else f"\n         {filas}"))
    return 0 if ok else 1


def test_anuncio_de_ventana_cubierta_por_meta_no_suma_gasto_de_lucidsales():
    meta = [_fila_entrega_anuncio(ad_id="999", ventana_ini="2026-07-10", ventana_fin="2026-07-10", spend_usd="30.0"),
            _fila_entrega_anuncio(ad_id="999", ventana_ini="2026-07-11", ventana_fin="2026-07-11", spend_usd="40.0")]
    venta = _venta(ventana_ini="2026-07-10", ventana_fin="2026-07-11", anuncio="OTRO", spend_usd="55.0")
    filas = gasto.gasto_por_anuncio_ventana(filas_venta=[venta], filas_entrega_anuncio=meta)
    total = sum(f["spend_usd"] for f in filas)
    ok = abs(total - 70.0) < 1e-9
    print(("  OK     " if ok else "  FALLA  ") + "grano anuncio: ventana de LucidSales cubierta por Meta no suma su gasto"
          + ("" if ok else f"\n         {filas}"))
    return 0 if ok else 1


def main():
    pruebas = [
        test_conjunto_meta_gana_y_se_cuenta_una_sola_vez,
        test_n_anuncios_sin_match_no_multiplican_el_gasto_del_conjunto,
        test_meta_sin_ninguna_venta_se_cuenta_igual,
        test_conjunto_sin_dim_todavia_cuenta_a_nivel_producto,
        test_conjunto_sin_cobertura_meta_cae_a_lucidsales,
        test_conjunto_sin_fila_propia_en_una_cuenta_cubierta_por_meta_no_suma_su_gasto,
        test_conjuntos_distintos_no_se_mezclan,
        test_alias_canonicaliza_los_dos_lados_del_join,
        test_dos_grafias_meta_que_canonicalizan_igual_no_duplican_con_fila_de_anuncio_presente,
        test_fuente_no_reconocida_no_cuenta_como_meta,
        test_anuncio_ad_id_gana_y_se_cuenta_una_vez,
        test_anuncio_ad_id_normaliza_notacion_cientifica,
        test_anuncio_renombrado_no_duplica_bajo_ad_id,
        test_anuncio_sin_ad_id_usa_nombre_pero_no_hereda_el_conjunto,
        test_anuncio_meta_sin_venta_se_cuenta_igual,
        test_misma_campana_conjunto_anuncio_en_dos_campanas_no_colisiona,
        test_invariante_conservacion_de_plata_grano_conjunto,
        test_invariante_conservacion_de_plata_grano_anuncio,
        test_indice_gasto_por_anuncio_resuelve_por_llave,
        test_escribir_conjunto_ventana_csv_roundtrip,
        test_conjunto_api_directa_supera_export_del_mismo_dia_aunque_cambie_el_nombre,
        test_conjunto_export_sin_cobertura_api_sigue_contando,
        test_anuncio_api_directa_supera_export_del_mismo_dia,
        test_ventas_de_ventana_multidia_cubierta_por_meta_no_suman_su_gasto_de_lucidsales,
        test_cuenta_con_api_sin_filas_un_dia_en_que_otra_cuenta_si_tuvo_es_dia_sin_gasto,
        test_ventana_sin_cobertura_de_meta_sigue_cayendo_al_fallback,
        test_cuenta_id_con_sufijo_punto_cero_calza_con_el_de_meta,
        test_anuncio_de_ventana_cubierta_por_meta_no_suma_gasto_de_lucidsales,
    ]
    fallas = sum(p() for p in pruebas)
    print(f"\n{'0 fallas' if not fallas else str(fallas) + ' falla(s)'}.")
    return 1 if fallas else 0


if __name__ == "__main__":
    sys.exit(main())
