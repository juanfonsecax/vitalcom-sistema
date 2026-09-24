#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_mapear_ad_id_hist.py — GATE del mapeo de ad_id historico verificado por gasto
(P1-cimientos T2, 23-sep-2026). Todas las pruebas son PURAS: nunca llaman a la Graph API.

USO:  python Ads/_TOOLS/test_mapear_ad_id_hist.py     (exit 0 = pasa, 1 = falla)
"""
import csv
import hashlib
import os
import sys
import tempfile

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mapear_ad_id_hist as m  # noqa: E402


def _venta(**kw):
    r = {"ventana_ini": "2026-07-17", "ventana_fin": "2026-07-17", "dias": "1",
         "rol_ventana": "BASE", "cuenta_id": "598687956219141.0", "cuenta_alias": "GTR7",
         "conjunto": "CONJ_A", "anuncio": "ANU_A", "spend_usd": "10.0", "ad_id": ""}
    r.update(kw)
    return r


def _meta(ad_id, ad_name, spend):
    return {"ad_id": ad_id, "ad_name": ad_name, "adset_name": "", "spend": spend}


# ── ad_id_valido ─────────────────────────────────────────────────────────────────────────────

def test_ad_id_valido_exige_solo_digitos_y_largo():
    casos = [("1234567890", True), ("123", False), ("1.2024737592740078e+17", False),
             ("", False), ("  1234567890  ", True), ("abc1234567", False)]
    ok = all(m.ad_id_valido(v) == esperado for v, esperado in casos)
    print(("  OK     " if ok else "  FALLA  ") + "ad_id_valido() exige solo digitos y largo >= 10")
    return 0 if ok else 1


# ── emparejar (la regla dura) ────────────────────────────────────────────────────────────────

def test_match_unico_dentro_de_tolerancia_se_acepta():
    ad_id, metodo, motivo, spend_meta = m.emparejar(10.0, {"111": 10.01})
    ok = ad_id == "111" and metodo == "ad_id_verificado_gasto" and motivo == "" and spend_meta == 10.01
    print(("  OK     " if ok else "  FALLA  ") + "un unico candidato dentro de tolerancia se acepta")
    return 0 if ok else 1


def test_match_fuera_de_tolerancia_se_rechaza():
    ad_id, metodo, motivo, spend_meta = m.emparejar(10.0, {"111": 12.50})
    ok = ad_id == "" and metodo == "nombre" and motivo == "gasto_no_coincide"
    print(("  OK     " if ok else "  FALLA  ") + "un candidato fuera de tolerancia queda "
          "gasto_no_coincide, nunca se inventa" + ("" if ok else f"\n         {(ad_id, metodo, motivo)}"))
    return 0 if ok else 1


def test_dos_candidatos_mismo_nombre_y_gasto_da_ambiguo():
    ad_id, metodo, motivo, _ = m.emparejar(10.0, {"111": 10.0, "222": 10.01})
    ok = ad_id == "" and metodo == "nombre" and motivo == "ambiguo"
    print(("  OK     " if ok else "  FALLA  ") + "dos candidatos dentro de tolerancia -> ambiguo, "
          "nunca se elige al azar" + ("" if ok else f"\n         {(ad_id, metodo, motivo)}"))
    return 0 if ok else 1


def test_gasto_cero_nunca_se_acepta():
    ad_id, metodo, motivo, _ = m.emparejar(0.0, {"111": 0.0})
    ok = ad_id == "" and metodo == "nombre" and motivo == "sin_gasto"
    print(("  OK     " if ok else "  FALLA  ") + "spend_usd 0/vacio nunca se acepta (sin_gasto)")
    return 0 if ok else 1


def test_sin_candidatos_da_sin_candidato():
    ad_id, metodo, motivo, _ = m.emparejar(10.0, {})
    ok = ad_id == "" and metodo == "nombre" and motivo == "sin_candidato"
    print(("  OK     " if ok else "  FALLA  ") + "sin ningun candidato de Meta -> sin_candidato")
    return 0 if ok else 1


def test_tolerancia_minima_es_2_centavos():
    # 1% de 1.00 = 0.01 < 0.02: la tolerancia minima (0.02) debe mandar, no el 1%.
    ad_id, metodo, _, _ = m.emparejar(1.00, {"111": 1.02})
    ok = ad_id == "111" and metodo == "ad_id_verificado_gasto"
    print(("  OK     " if ok else "  FALLA  ") + "la tolerancia minima de 0.02 manda sobre el 1% "
          "en montos chicos")
    return 0 if ok else 1


# ── candidatos_de / dias_de ──────────────────────────────────────────────────────────────────

def test_candidatos_de_suma_gasto_multi_dia():
    meta_por_dia = {
        "2026-07-17": [_meta("111", "ANU_A", 5.0)],
        "2026-07-18": [_meta("111", "ANU_A", 5.0)],
        "2026-07-19": [_meta("222", "OTRO", 99.0)],
    }
    cand = m.candidatos_de(meta_por_dia, ["2026-07-17", "2026-07-18", "2026-07-19"], "ANU_A")
    ok = cand == {"111": 10.0}
    print(("  OK     " if ok else "  FALLA  ") + "candidatos_de() suma el spend del mismo ad_id "
          "sobre TODOS los dias de la ventana" + ("" if ok else f"\n         {cand}"))
    return 0 if ok else 1


def test_candidatos_de_prueba_el_alias_canonico():
    meta_por_dia = {"2026-07-17": [_meta("111", "ANU_A_NUEVO", 10.0)]}
    cand = m.candidatos_de(meta_por_dia, ["2026-07-17"], "ANU_A_VIEJO", nombre_alt="ANU_A_NUEVO")
    ok = cand == {"111": 10.0}
    print(("  OK     " if ok else "  FALLA  ") + "candidatos_de() encuentra el ad renombrado via "
          "el alias-canonico" + ("" if ok else f"\n         {cand}"))
    return 0 if ok else 1


def test_dias_de_ventana_de_un_dia():
    ok = m.dias_de("2026-07-17", "2026-07-17") == ["2026-07-17"]
    print(("  OK     " if ok else "  FALLA  ") + "dias_de() con ventana de 1 dia devuelve ese dia")
    return 0 if ok else 1


def test_dias_de_ventana_multi_dia():
    ok = m.dias_de("2026-07-17", "2026-07-19") == ["2026-07-17", "2026-07-18", "2026-07-19"]
    print(("  OK     " if ok else "  FALLA  ") + "dias_de() enumera cada dia de una ventana de 3")
    return 0 if ok else 1


# ── mapear_fila (integra rango autorizado + match) ──────────────────────────────────────────────

def test_mapear_fila_fuera_de_rango_autorizado_no_intenta_red():
    fila = _venta(ventana_ini="2026-09-10", ventana_fin="2026-09-10")
    r = m.mapear_fila(fila, {}, {})
    ok = r["ad_id"] == "" and r["motivo"] == "sin_candidato"
    print(("  OK     " if ok else "  FALLA  ") + "una ventana fuera del rango autorizado "
          "(2026-07-01..2026-09-05) nunca dispara match: sin_candidato directo")
    return 0 if ok else 1


def test_mapear_fila_ventana_multi_dia_suma_dias_y_verifica():
    fila = _venta(ventana_ini="2026-07-17", ventana_fin="2026-07-19", dias="3", spend_usd="15.0")
    indice = {
        ("598687956219141", "2026-07-17"): [_meta("111", "ANU_A", 5.0)],
        ("598687956219141", "2026-07-18"): [_meta("111", "ANU_A", 5.0)],
        ("598687956219141", "2026-07-19"): [_meta("111", "ANU_A", 5.0)],
    }
    r = m.mapear_fila(fila, indice, {})
    ok = r["ad_id"] == "111" and r["metodo"] == "ad_id_verificado_gasto" and r["spend_meta"] == 15.0
    print(("  OK     " if ok else "  FALLA  ") + "mapear_fila() suma los 3 dias de la ventana "
          "antes de comparar contra spend_usd" + ("" if ok else f"\n         {r}"))
    return 0 if ok else 1


def test_mapear_fila_cuenta_id_normaliza_notacion_cientifica():
    fila = _venta(cuenta_id="598687956219141.0")
    indice = {("598687956219141", "2026-07-17"): [_meta("111", "ANU_A", 10.0)]}
    r = m.mapear_fila(fila, indice, {})
    ok = r["ad_id"] == "111"
    print(("  OK     " if ok else "  FALLA  ") + "mapear_fila() normaliza el cuenta_id en notacion "
          "cientifica de _FACT_VENTAS.csv antes de buscar en el indice")
    return 0 if ok else 1


# ── construir_mapa / escritura CSV ──────────────────────────────────────────────────────────────

def test_construir_mapa_es_deterministico_reordena_igual():
    filas = [_venta(anuncio="ANU_Z", conjunto="C2"), _venta(anuncio="ANU_A", conjunto="C1")]
    salida1 = m.construir_mapa(filas, {}, {})
    salida2 = m.construir_mapa(list(reversed(filas)), {}, {})
    ok = salida1 == salida2
    print(("  OK     " if ok else "  FALLA  ") + "construir_mapa() ordena de forma deterministica "
          "sin importar el orden de entrada (idempotente)")
    return 0 if ok else 1


def test_escribir_mapa_csv_roundtrip_con_dictwriter():
    filas_out = m.construir_mapa([_venta(anuncio="Con, coma")], {}, {})
    with tempfile.TemporaryDirectory() as tmp:
        ruta = os.path.join(tmp, "_MAPA_AD_ID_HIST.csv")
        m.escribir_mapa_csv(filas_out, ruta)
        with open(ruta, encoding="utf-8") as f:
            leidas = list(csv.DictReader(f))
        ok = (len(leidas) == 1 and leidas[0]["anuncio"] == "Con, coma"
              and list(leidas[0].keys()) == m.COLS)
    print(("  OK     " if ok else "  FALLA  ") + "escribir_mapa_csv() usa csv.DictWriter real y "
          "un campo con coma sobrevive el roundtrip" + ("" if ok else f"\n         {leidas}"))
    return 0 if ok else 1


def test_rerun_produce_archivo_identico():
    filas_out = m.construir_mapa(
        [_venta(anuncio="ANU_A"), _venta(anuncio="ANU_B", spend_usd="0")], {}, {})
    with tempfile.TemporaryDirectory() as tmp:
        r1 = os.path.join(tmp, "a.csv")
        r2 = os.path.join(tmp, "b.csv")
        m.escribir_mapa_csv(filas_out, r1)
        m.escribir_mapa_csv(filas_out, r2)
        h1 = hashlib.sha256(open(r1, "rb").read()).hexdigest()
        h2 = hashlib.sha256(open(r2, "rb").read()).hexdigest()
    ok = h1 == h2
    print(("  OK     " if ok else "  FALLA  ") + "rerun con el mismo input produce un CSV "
          "byte-identico")
    return 0 if ok else 1


def test_facts_nunca_se_tocan():
    """Corre construir_mapa()/escribir_mapa_csv() sobre fixtures y verifica que los tres _FACT_*.csv
    reales quedan byte-identicos (hash antes/despues). No usa red: es la prueba de que la ESCRITURA
    de este modulo nunca alcanza esos archivos, sin importar el escenario de match."""
    raiz = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    rutas = [os.path.join(raiz, "PRODUCTOS", n) for n in
             ("_FACT_VENTAS.csv", "_FACT_ENTREGA.csv", "_FACT_ENTREGA_ANUNCIO.csv")]
    antes = {}
    for r in rutas:
        if os.path.exists(r):
            antes[r] = hashlib.sha256(open(r, "rb").read()).hexdigest()

    filas_out = m.construir_mapa([_venta(spend_usd="0"), _venta(anuncio="SIN_MATCH")], {}, {})
    with tempfile.TemporaryDirectory() as tmp:
        m.escribir_mapa_csv(filas_out, os.path.join(tmp, "salida.csv"))

    despues = {}
    for r in rutas:
        if os.path.exists(r):
            despues[r] = hashlib.sha256(open(r, "rb").read()).hexdigest()
    ok = antes == despues
    print(("  OK     " if ok else "  FALLA  ") + "los _FACT_*.csv reales quedan byte-identicos: "
          "este modulo nunca escribe ahi")
    return 0 if ok else 1


class _ModuloMetaFalso:
    """Simula bajar_meta_insights: una cuenta+dia falla (permiso denegado), el resto responde OK.
    Nunca toca la red de verdad."""

    def num(self, v):
        return float(v) if v not in (None, "") else 0.0

    def insights_de(self, cuenta_id, fecha, token):
        if cuenta_id == "1":
            raise SystemExit("(#200) Ad account owner has NOT grant ads_read permission")
        return [{"ad_id": "111", "ad_name": "ANU_A", "adset_name": "", "spend": "5.0"}]


def test_construir_indice_meta_aisla_una_cuenta_que_falla():
    filas = [_venta(cuenta_id="598687956219141.0", ventana_ini="2026-07-17",
                     ventana_fin="2026-07-17"),
             _venta(cuenta_id="1.0", ventana_ini="2026-07-17", ventana_fin="2026-07-17")]
    cuentas = [{"cuenta_id": "598687956219141", "cuenta_alias": "GTR7"},
               {"cuenta_id": "1", "cuenta_alias": "CUENTA_SIN_PERMISO"}]
    with tempfile.TemporaryDirectory() as tmp:
        indice, fallidas = m.construir_indice_meta(
            filas, cuentas, "tok", staging_dir=tmp, fetch=True, modulo=_ModuloMetaFalso())
    ok = (len(fallidas) == 1 and fallidas[0][0] == "CUENTA_SIN_PERMISO"
          and indice[("598687956219141", "2026-07-17")] != []
          and indice[("1", "2026-07-17")] == [])
    print(("  OK     " if ok else "  FALLA  ") + "una cuenta que la Graph API rechaza no tumba el "
          "resto del mapeo (aislamiento de fallas)" + ("" if ok else f"\n         {indice} {fallidas}"))
    return 0 if ok else 1


def test_dias_necesarios_ignora_cuentas_no_reconocidas():
    filas = [_venta(cuenta_id="999999999999999.0")]
    necesarios = m.dias_necesarios(filas, {"598687956219141": {}})
    ok = necesarios == set()
    print(("  OK     " if ok else "  FALLA  ") + "dias_necesarios() no pide red para una cuenta "
          "que no esta en _DIM_CUENTAS.csv")
    return 0 if ok else 1


def main():
    pruebas = [
        test_ad_id_valido_exige_solo_digitos_y_largo,
        test_match_unico_dentro_de_tolerancia_se_acepta,
        test_match_fuera_de_tolerancia_se_rechaza,
        test_dos_candidatos_mismo_nombre_y_gasto_da_ambiguo,
        test_gasto_cero_nunca_se_acepta,
        test_sin_candidatos_da_sin_candidato,
        test_tolerancia_minima_es_2_centavos,
        test_candidatos_de_suma_gasto_multi_dia,
        test_candidatos_de_prueba_el_alias_canonico,
        test_dias_de_ventana_de_un_dia,
        test_dias_de_ventana_multi_dia,
        test_mapear_fila_fuera_de_rango_autorizado_no_intenta_red,
        test_mapear_fila_ventana_multi_dia_suma_dias_y_verifica,
        test_mapear_fila_cuenta_id_normaliza_notacion_cientifica,
        test_construir_mapa_es_deterministico_reordena_igual,
        test_escribir_mapa_csv_roundtrip_con_dictwriter,
        test_rerun_produce_archivo_identico,
        test_facts_nunca_se_tocan,
        test_construir_indice_meta_aisla_una_cuenta_que_falla,
        test_dias_necesarios_ignora_cuentas_no_reconocidas,
    ]
    fallas = sum(p() for p in pruebas)
    print(f"\n{'0 fallas' if not fallas else str(fallas) + ' falla(s)'}.")
    return 1 if fallas else 0


if __name__ == "__main__":
    sys.exit(main())
