#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_upsert_fact.py — GATE del helper de UPSERT compartido (g07-cimientos T1, 22-sep-2026).

Congela el contrato de upsert_fact.upsert(): reemplaza por llave (no anexa a ciegas),
es idempotente al re-correr con el mismo contenido, migra una fila vieja que no trae
una columna nueva del esquema en vez de romperse, y (con `particion`) declara un
re-pull como la verdad completa de su ambito — elimina lo que ese ambito ya no trae,
sin tocar particiones que el re-pull no menciono.

USO:  python Ads/_TOOLS/test_upsert_fact.py     (exit 0 = pasa, 1 = falla)
"""
import csv
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import upsert_fact as uf  # noqa: E402


COLS = ["dia", "cuenta", "ad_id", "spend"]


def _leer(path):
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def test_upsert_agrega_nuevas_y_no_toca_nada_si_no_hay_archivo(tmp):
    path = os.path.join(tmp, "hechos.csv")
    bkdir = os.path.join(tmp, "backups")
    key = ("dia", "cuenta")
    filas = [{"dia": "2026-09-20", "cuenta": "A", "ad_id": "1", "spend": "10.0"}]
    reemp, nuevas, sc = uf.upsert(path, COLS, key, filas, bkdir)
    ok = (reemp, nuevas, sc) == (0, 1, 0) and os.path.exists(path) and len(_leer(path)) == 1
    print(("  OK     " if ok else "  FALLA  ") + "primera corrida: crea el archivo con 1 fila nueva"
          + ("" if ok else f"\n         {(reemp, nuevas, sc)}"))
    return 0 if ok else 1


def test_upsert_reemplaza_un_dia_parcial(tmp):
    """El caso central de T1: un día llegó con el gasto congelado a medio día (0.7 del
    real) y la corrida siguiente lo trae completo — debe REEMPLAZAR, no descartar."""
    path = os.path.join(tmp, "hechos.csv")
    bkdir = os.path.join(tmp, "backups")
    key = ("dia", "cuenta")
    parcial = [{"dia": "2026-09-20", "cuenta": "A", "ad_id": "1", "spend": "7.0"}]
    uf.upsert(path, COLS, key, parcial, bkdir)

    completo = [{"dia": "2026-09-20", "cuenta": "A", "ad_id": "1", "spend": "10.0"}]
    reemp, nuevas, sc = uf.upsert(path, COLS, key, completo, bkdir)
    filas = _leer(path)
    ok = (reemp, nuevas, sc) == (1, 0, 0) and len(filas) == 1 and filas[0]["spend"] == "10.0"
    print(("  OK     " if ok else "  FALLA  ")
          + "un día corregido REEMPLAZA la fila parcial, no queda duplicado ni se descarta"
          + ("" if ok else f"\n         {(reemp, nuevas, sc)} filas={filas}"))
    return 0 if ok else 1


def test_upsert_idempotente(tmp):
    """Re-correr con EXACTAMENTE el mismo contenido dos veces seguidas no debe generar
    ni reemplazos ni filas nuevas la segunda vez (idempotencia, check explícito de T1)."""
    path = os.path.join(tmp, "hechos.csv")
    bkdir = os.path.join(tmp, "backups")
    key = ("dia", "cuenta")
    filas = [{"dia": "2026-09-20", "cuenta": "A", "ad_id": "1", "spend": "10.0"}]
    uf.upsert(path, COLS, key, filas, bkdir)
    reemp, nuevas, sc = uf.upsert(path, COLS, key, filas, bkdir)
    ok = (reemp, nuevas, sc) == (0, 0, 1)
    print(("  OK     " if ok else "  FALLA  ")
          + "re-correr con el mismo contenido es idempotente (0 reemplazos, 0 nuevas)"
          + ("" if ok else f"\n         {(reemp, nuevas, sc)}"))
    return 0 if ok else 1


def test_lectura_retrocompatible_de_un_csv_sin_columna_nueva(tmp):
    """Un CSV escrito ANTES de que existiera `ad_id` en el esquema se lee igual: la
    columna nueva llega en "" en vez de romper con un KeyError."""
    path = os.path.join(tmp, "hechos.csv")
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["dia", "cuenta", "spend"])   # esquema viejo, SIN ad_id
        w.writerow(["2026-09-01", "A", "5.0"])

    filas = uf.leer_migrado(path, COLS)
    ok = len(filas) == 1 and filas[0]["ad_id"] == "" and filas[0]["spend"] == "5.0"
    print(("  OK     " if ok else "  FALLA  ")
          + "leer_migrado() completa una columna nueva con \"\" en vez de romper"
          + ("" if ok else f"\n         {filas}"))
    return 0 if ok else 1


def test_upsert_migra_el_header_al_reescribir(tmp):
    """El UPSERT reescribe el archivo completo con el header NUEVO: una fila vieja sin
    ad_id queda con ad_id="" en el CSV resultante, nunca con un id inventado."""
    path = os.path.join(tmp, "hechos.csv")
    bkdir = os.path.join(tmp, "backups")
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["dia", "cuenta", "spend"])
        w.writerow(["2026-09-01", "A", "5.0"])

    key = ("dia", "cuenta")
    nueva = [{"dia": "2026-09-02", "cuenta": "B", "ad_id": "99", "spend": "3.0"}]
    reemp, nuevas, sc = uf.upsert(path, COLS, key, nueva, bkdir)
    filas = _leer(path)
    vieja = next(f for f in filas if f["dia"] == "2026-09-01")
    ok = (nuevas == 1 and len(filas) == 2 and vieja["ad_id"] == ""
          and set(filas[0].keys()) == set(COLS))
    print(("  OK     " if ok else "  FALLA  ")
          + "al agregar una fila nueva, la fila vieja queda migrada al header nuevo (ad_id=\"\")"
          + ("" if ok else f"\n         {filas}"))
    return 0 if ok else 1


def test_llave_por_funcion(tmp):
    """`key` puede ser una función fila->tupla (no solo nombres de columna literales),
    para llaves con lógica ('ad_id si lo hay, si no la firma')."""
    path = os.path.join(tmp, "hechos.csv")
    bkdir = os.path.join(tmp, "backups")
    cols = ["dia", "ad_id", "firma", "spend"]

    def clave(f):
        return (f["dia"], f.get("ad_id") or f.get("firma") or "")

    sin_ad_id = [{"dia": "2026-09-01", "ad_id": "", "firma": "F1", "spend": "1.0"}]
    uf.upsert(path, cols, clave, sin_ad_id, bkdir)
    correccion = [{"dia": "2026-09-01", "ad_id": "", "firma": "F1", "spend": "2.0"}]
    reemp, nuevas, sc = uf.upsert(path, cols, clave, correccion, bkdir)
    filas = _leer(path)
    ok = (reemp, nuevas) == (1, 0) and len(filas) == 1 and filas[0]["spend"] == "2.0"
    print(("  OK     " if ok else "  FALLA  ")
          + "una llave-función (ad_id o firma) reemplaza por la misma identidad lógica"
          + ("" if ok else f"\n         {(reemp, nuevas, sc)} filas={filas}"))
    return 0 if ok else 1


def test_particion_elimina_fila_vieja_de_identidad_distinta(tmp):
    """Caso central de la segunda vuelta de T1: un backfill viejo SIN ad_id convive con
    un re-pull nuevo CON ad_id — llaves distintas, nunca colisionan por `key`. Con
    `particion` el re-pull de esa cuenta/dia se declara verdad completa: la fila vieja
    se ELIMINA (no queda duplicando el gasto), la nueva entra, y el spend total es
    exactamente el del re-pull."""
    path = os.path.join(tmp, "hechos.csv")
    bkdir = os.path.join(tmp, "backups")
    cols = ["dia", "cuenta", "ad_id", "firma", "spend"]
    key = lambda f: (f["dia"], f["cuenta"], f.get("ad_id") or f.get("firma") or "")
    particion = ("dia", "cuenta")

    viejo_sin_ad_id = [{"dia": "2026-09-06", "cuenta": "GTR7", "ad_id": "",
                        "firma": "ANG_A", "spend": "7.0"}]
    uf.upsert(path, cols, key, viejo_sin_ad_id, bkdir)

    repull_con_ad_id = [{"dia": "2026-09-06", "cuenta": "GTR7", "ad_id": "999",
                         "firma": "ANG_A", "spend": "10.0"}]
    reemp, nuevas, sc, elim = uf.upsert(path, cols, key, repull_con_ad_id, bkdir,
                                         particion=particion)
    filas = _leer(path)
    total_spend = sum(float(f["spend"]) for f in filas)
    ok = ((reemp, nuevas, elim) == (0, 1, 1) and len(filas) == 1
          and filas[0]["ad_id"] == "999" and total_spend == 10.0)
    print(("  OK     " if ok else "  FALLA  ")
          + "particion elimina la fila vieja de identidad distinta; spend = el del re-pull"
          + ("" if ok else f"\n         {(reemp, nuevas, sc, elim)} filas={filas}"))
    return 0 if ok else 1


def test_particion_no_tocada_queda_intacta(tmp):
    """Una particion que `filas_nuevas` no menciona (la cuenta/dia de un intento que
    fallo, o que simplemente no se pidio) no pierde nada — el borrado es SOLO dentro
    del ambito que el re-pull declara cubrir."""
    path = os.path.join(tmp, "hechos.csv")
    bkdir = os.path.join(tmp, "backups")
    key = ("dia", "cuenta")
    particion = ("dia", "cuenta")

    base = [
        {"dia": "2026-09-06", "cuenta": "GTR7", "ad_id": "1", "spend": "5.0"},
        {"dia": "2026-09-07", "cuenta": "GTR7", "ad_id": "2", "spend": "6.0"},
    ]
    uf.upsert(path, COLS, key, base, bkdir)

    repull_solo_06 = [{"dia": "2026-09-06", "cuenta": "GTR7", "ad_id": "1", "spend": "5.5"}]
    reemp, nuevas, sc, elim = uf.upsert(path, COLS, key, repull_solo_06, bkdir,
                                         particion=particion)
    filas = _leer(path)
    dia_07 = next(f for f in filas if f["dia"] == "2026-09-07")
    ok = (elim == 0 and len(filas) == 2 and dia_07["spend"] == "6.0")
    print(("  OK     " if ok else "  FALLA  ")
          + "una particion no mencionada por el re-pull queda intacta"
          + ("" if ok else f"\n         {(reemp, nuevas, sc, elim)} filas={filas}"))
    return 0 if ok else 1


def test_particion_idempotente_no_reescribe(tmp):
    """Re-correr con `particion` y EXACTAMENTE el mismo contenido no debe reemplazar,
    agregar NI eliminar nada — el archivo no se reescribe de mas."""
    path = os.path.join(tmp, "hechos.csv")
    bkdir = os.path.join(tmp, "backups")
    key = ("dia", "cuenta")
    particion = ("dia", "cuenta")
    filas = [{"dia": "2026-09-06", "cuenta": "GTR7", "ad_id": "1", "spend": "5.0"}]
    uf.upsert(path, COLS, key, filas, bkdir, particion=particion)
    antes = os.path.getmtime(path)
    reemp, nuevas, sc, elim = uf.upsert(path, COLS, key, filas, bkdir, particion=particion)
    despues = os.path.getmtime(path)
    ok = (reemp, nuevas, elim) == (0, 0, 0) and sc == 1 and antes == despues
    print(("  OK     " if ok else "  FALLA  ")
          + "particion + mismo contenido es idempotente (0/0/0, archivo no reescrito)"
          + ("" if ok else f"\n         {(reemp, nuevas, sc, elim)} mtime {antes}->{despues}"))
    return 0 if ok else 1


def test_particion_elimina_anuncio_desaparecido(tmp):
    """Un anuncio que existia en la particion y desaparecio del re-pull (Meta lo borro,
    o quedo fuera del filtro de esa cuenta/dia) se ELIMINA — no queda huerfano con el
    gasto de una corrida vieja pesando para siempre."""
    path = os.path.join(tmp, "hechos.csv")
    bkdir = os.path.join(tmp, "backups")
    key = ("dia", "cuenta", "ad_id")
    particion = ("dia", "cuenta")

    dos_anuncios = [
        {"dia": "2026-09-06", "cuenta": "GTR7", "ad_id": "1", "spend": "5.0"},
        {"dia": "2026-09-06", "cuenta": "GTR7", "ad_id": "2", "spend": "3.0"},
    ]
    uf.upsert(path, COLS, key, dos_anuncios, bkdir)

    solo_queda_uno = [{"dia": "2026-09-06", "cuenta": "GTR7", "ad_id": "1", "spend": "5.0"}]
    reemp, nuevas, sc, elim = uf.upsert(path, COLS, key, solo_queda_uno, bkdir,
                                         particion=particion)
    filas = _leer(path)
    ok = (elim == 1 and len(filas) == 1 and filas[0]["ad_id"] == "1")
    print(("  OK     " if ok else "  FALLA  ")
          + "un anuncio que desaparecio del re-pull de su particion se elimina"
          + ("" if ok else f"\n         {(reemp, nuevas, sc, elim)} filas={filas}"))
    return 0 if ok else 1


def main():
    import tempfile as _t
    pruebas = [
        test_upsert_agrega_nuevas_y_no_toca_nada_si_no_hay_archivo,
        test_upsert_reemplaza_un_dia_parcial,
        test_upsert_idempotente,
        test_lectura_retrocompatible_de_un_csv_sin_columna_nueva,
        test_upsert_migra_el_header_al_reescribir,
        test_llave_por_funcion,
        test_particion_elimina_fila_vieja_de_identidad_distinta,
        test_particion_no_tocada_queda_intacta,
        test_particion_idempotente_no_reescribe,
        test_particion_elimina_anuncio_desaparecido,
    ]
    fallas = 0
    for prueba in pruebas:
        with _t.TemporaryDirectory() as tmp:
            fallas += prueba(tmp)
    print(f"\n{'0 fallas' if not fallas else str(fallas) + ' falla(s)'}.")
    return 1 if fallas else 0


if __name__ == "__main__":
    sys.exit(main())
