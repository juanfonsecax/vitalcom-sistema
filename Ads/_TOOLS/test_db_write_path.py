#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_db_write_path.py — P3 T3: contrato de escritura por Postgres de los tres llamadores
reales (ingerir_lucidsales.py, ingerir_meta.py, bajar_meta_insights.py).

Cubre, a nivel de LLAMADOR (no solo de db/escribir.py, que ya lo prueba db/test_db.py):
  (a) un día nuevo se escribe en la DB y el espejo es BYTE-IDÉNTICO al que produciría
      `upsert_fact.upsert()` sobre el mismo input.
  (b) re-correr el mismo input -> 0 nuevas/0 reemplazadas, el espejo queda intacto.
  (c) el guardia de drift aborta y NO escribe nada (ni `raw` ni el espejo) si el CSV en disco no
      coincide con lo que la base exportaría.
  (d) `--dry-run` no toca ni la base ni el CSV.
  (e) Postgres caído -> exit != 0, CSV intacto (nunca cae de vuelta a escribir el CSV directo).

P3 T3 — aislamiento de Postgres (CRÍTICO, igual que test_ingerir_lucidsales.py/
test_bajar_meta_insights.py): fuerza `PGDATABASE=vitalcom_test` ANTES de importar los módulos
reales, nunca toca `vitalcom`, y cada escenario usa su propio tenant. Se salta con aviso si
`vitalcom_test` no existe y el rol no tiene `CREATEDB` (ver db/README.md).
"""
import csv
import json
import os
import sys
import tempfile
import uuid

os.environ["PGDATABASE"] = "vitalcom_test"

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ingerir_lucidsales as ing  # noqa: E402
import upsert_fact as UF          # noqa: E402

sys.path.insert(0, os.path.join(ing.BASE, "db"))
import cargar as db_cargar      # noqa: E402
import escribir as db_escribir  # noqa: E402
import nucleo as db_nucleo      # noqa: E402


def _preparar_base_de_pruebas():
    try:
        if db_cargar.asegurar_base_de_datos("vitalcom_test"):
            db_cargar.aplicar_schema(dbname="vitalcom_test")
    except Exception:
        pass


_preparar_base_de_pruebas()


def _conectar_seguro(env=None):
    con = db_cargar.conectar(env)
    if con.info.dbname == "vitalcom":
        con.close()
        raise RuntimeError(
            "P3 T3: test_db_write_path.py intentó conectarse a 'vitalcom' en vez de "
            "'vitalcom_test'. Abortado antes de tocar nada.")
    return con


def _db_disponible():
    try:
        con = _conectar_seguro()
        con.close()
        return True
    except Exception:
        return False


DB_DISPONIBLE = _db_disponible()


def _tenant_unico(nombre):
    return "test_dbwrite_%s_%s" % (nombre, uuid.uuid4().hex[:8])


def _escribir_csv(path, header, filas):
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(filas)
    return path


def _escribir_export(path, filas):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump({"insights": filas}, fh)
    return path


def _fila_lucidsales(producto, cuenta_id, ad_set, ad_title, ad_id, sells=1, spend=10.0):
    return {
        "accountTitle": cuenta_id, "campaignTitle": "CAMPANA_TEST",
        "adSetTitle": ad_set, "adTitle": ad_title, "producto": producto,
        "messages": 5, "clicks": 3, "impressions": 100,
        "spend": spend, "sells": sells, "total": sells * 200, "adId": ad_id,
    }


def _fixture(tmp, tenant):
    dimp = _escribir_csv(
        os.path.join(tmp, "_DIM_PRODUCTOS.csv"),
        ["producto_key", "nombre_display", "slug_carpeta"],
        [["TINNIDROP", "Tinnidrop Importado Original", "TINNIDROP"]])
    dimctas = _escribir_csv(
        os.path.join(tmp, "_DIM_CUENTAS.csv"),
        ["cuenta_alias", "cuenta_id", "moneda"],
        [["GTR 0", "1665221077707961", "USD"]])
    fact = _escribir_csv(os.path.join(tmp, "_FACT_VENTAS.csv"), ing.COLS, [])
    dimc = _escribir_csv(
        os.path.join(tmp, "_DIM_CONJUNTOS.csv"),
        ["conjunto_meta"], [["CONJ_CONOCIDO"]])
    bkdir = os.path.join(tmp, "backups_csv")
    con = _conectar_seguro()
    try:
        with con:
            with con.cursor() as cur:
                n, sha = db_cargar.cargar_tabla(cur, tenant, "venta", "_FACT_VENTAS.csv", False, tmp)
                cur.execute(
                    "INSERT INTO raw.raw_import (tenant_id, archivo, sha256, filas) "
                    "VALUES (%s, %s, %s, %s)", (tenant, "_FACT_VENTAS.csv", sha, n))
                db_nucleo.construir_core(cur, tenant)
    finally:
        con.close()
    return dict(DIMP=dimp, DIMCTAS=dimctas, FACT=fact, DIMC=dimc, BKDIR=bkdir, TENANT_ID=tenant)


def _correr_main(rutas, argv):
    previo = {k: getattr(ing, k) for k in rutas}
    prev_argv = sys.argv
    try:
        for k, v in rutas.items():
            setattr(ing, k, v)
        sys.argv = ["ingerir_lucidsales.py"] + argv
        ing.reiniciar_ids_perdidos()
        ing.main()
        return None
    except SystemExit as e:
        return e
    finally:
        for k, v in previo.items():
            setattr(ing, k, v)
        sys.argv = prev_argv


def test_a_dia_nuevo_escribe_en_db_y_espejo_byte_identico_a_upsert_fact(tmp):
    """(a) Un día nuevo se escribe en Postgres y el espejo resultante es BYTE-IDÉNTICO al que
    produciría `upsert_fact.upsert()` sobre el mismo input, sobre un CSV aparte."""
    if not DB_DISPONIBLE:
        print("  SKIP   Postgres/vitalcom_test no disponible en este entorno")
        return 0
    tenant = _tenant_unico("a_dia_nuevo")
    rutas = _fixture(tmp, tenant)
    fila = _fila_lucidsales("Tinnidrop", "1665221077707961", "CONJ_CONOCIDO", "AD_1", "ad_1")
    export = _escribir_export(os.path.join(tmp, "sim-2026-09-14.json"), [fila])

    # Referencia: el mismo input, sobre un CSV aparte, vía el upsert de siempre.
    productos = ing.cargar_productos(rutas["DIMP"])
    cuentas = ing.cargar_cuentas(rutas["DIMCTAS"])
    filas_ref = ing.leer_export(export, "BASE", "LucidSales", productos, cuentas)
    ref_path = os.path.join(tmp, "ref", "_FACT_VENTAS.csv")
    os.makedirs(os.path.dirname(ref_path), exist_ok=True)
    _escribir_csv(ref_path, ing.COLS, [])
    UF.upsert(ref_path, ing.COLS, ing.clave_natural, filas_ref, os.path.join(tmp, "ref_bk"))

    salida = _correr_main(rutas, [export])
    ok_salida = salida is None

    with open(ref_path, "rb") as f:
        ref_bytes = f.read()
    with open(rutas["FACT"], "rb") as f:
        espejo_bytes = f.read()
    ok_bytes = ref_bytes == espejo_bytes

    ok = ok_salida and ok_bytes
    print(("  OK     " if ok else "  FALLA  ")
          + "día nuevo: escribe en DB y el espejo es byte-idéntico al de upsert_fact.upsert()"
          + ("" if ok else f"\n         salida={salida} ok_bytes={ok_bytes}"))
    return 0 if ok else 1


def test_b_re_correr_mismo_input_es_idempotente_y_no_toca_el_espejo(tmp):
    """(b) Re-correr el MISMO input -> 0 nuevas/0 reemplazadas, el espejo (mtime + contenido)
    queda intacto."""
    if not DB_DISPONIBLE:
        print("  SKIP   Postgres/vitalcom_test no disponible en este entorno")
        return 0
    tenant = _tenant_unico("b_idempotente")
    rutas = _fixture(tmp, tenant)
    fila = _fila_lucidsales("Tinnidrop", "1665221077707961", "CONJ_CONOCIDO", "AD_1", "ad_1")
    export = _escribir_export(os.path.join(tmp, "sim-2026-09-14.json"), [fila])

    salida1 = _correr_main(rutas, [export])
    with open(rutas["FACT"], "rb") as f:
        bytes1 = f.read()
    mtime1 = os.path.getmtime(rutas["FACT"])

    salida2 = _correr_main(rutas, [export])
    with open(rutas["FACT"], "rb") as f:
        bytes2 = f.read()
    mtime2 = os.path.getmtime(rutas["FACT"])

    ok = salida1 is None and salida2 is None and bytes1 == bytes2 and mtime1 == mtime2
    print(("  OK     " if ok else "  FALLA  ")
          + "re-correr el mismo input es idempotente y no vuelve a escribir el espejo"
          + ("" if ok else f"\n         salida1={salida1} salida2={salida2} "
                            f"bytes_iguales={bytes1 == bytes2} mtime_igual={mtime1 == mtime2}"))
    return 0 if ok else 1


def test_c_guardia_de_drift_aborta_y_no_escribe_nada(tmp):
    """(c) El CSV en disco fue editado a mano (deja de coincidir con lo que la base
    exportaría): el guardia aborta con exit != 0, y NO escribe ni una fila nueva."""
    if not DB_DISPONIBLE:
        print("  SKIP   Postgres/vitalcom_test no disponible en este entorno")
        return 0
    tenant = _tenant_unico("c_drift")
    rutas = _fixture(tmp, tenant)
    with open(rutas["FACT"], "a", encoding="utf-8") as f:
        f.write("linea,editada,a,mano\n")
    antes = open(rutas["FACT"], "rb").read()

    fila = _fila_lucidsales("Tinnidrop", "1665221077707961", "CONJ_CONOCIDO", "AD_1", "ad_1")
    export = _escribir_export(os.path.join(tmp, "sim-2026-09-14.json"), [fila])
    salida = _correr_main(rutas, [export])

    despues = open(rutas["FACT"], "rb").read()
    bloqueo = salida is not None and salida.code != 0
    mensaje_ok = salida is not None and "byte-identico" in str(salida)
    no_escribio = antes == despues

    ok = bloqueo and mensaje_ok and no_escribio
    print(("  OK     " if ok else "  FALLA  ")
          + "el guardia de drift aborta (exit != 0) y no escribe nada"
          + ("" if ok else f"\n         bloqueo={bloqueo} mensaje_ok={mensaje_ok} "
                            f"no_escribio={no_escribio} salida={salida}"))
    return 0 if ok else 1


def test_d_dry_run_no_toca_ni_la_db_ni_el_csv(tmp):
    """(d) `--dry-run` no debe tocar ni Postgres ni el CSV -- ni siquiera intenta conectar."""
    dimp = _escribir_csv(
        os.path.join(tmp, "_DIM_PRODUCTOS.csv"),
        ["producto_key", "nombre_display", "slug_carpeta"],
        [["TINNIDROP", "Tinnidrop Importado Original", "TINNIDROP"]])
    dimctas = _escribir_csv(
        os.path.join(tmp, "_DIM_CUENTAS.csv"),
        ["cuenta_alias", "cuenta_id", "moneda"],
        [["GTR 0", "1665221077707961", "USD"]])
    fact = _escribir_csv(os.path.join(tmp, "_FACT_VENTAS.csv"), ing.COLS, [])
    dimc = _escribir_csv(
        os.path.join(tmp, "_DIM_CONJUNTOS.csv"),
        ["conjunto_meta"], [["CONJ_CONOCIDO"]])
    bkdir = os.path.join(tmp, "backups_csv")
    # A PROPÓSITO: PGDATABASE apunta a un puerto inexistente -- si --dry-run intentara conectar,
    # esta prueba lo delataría con un traceback en vez de "no se escribió nada".
    rutas = dict(DIMP=dimp, DIMCTAS=dimctas, FACT=fact, DIMC=dimc, BKDIR=bkdir,
                 TENANT_ID="no-deberia-usarse")

    fila = _fila_lucidsales("Tinnidrop", "1665221077707961", "CONJ_CONOCIDO", "AD_1", "ad_1")
    export = _escribir_export(os.path.join(tmp, "sim-2026-09-14.json"), [fila])
    antes = open(fact, "rb").read()

    salida = _correr_main(rutas, [export, "--dry-run"])

    despues = open(fact, "rb").read()
    ok = salida is None and antes == despues
    print(("  OK     " if ok else "  FALLA  ")
          + "--dry-run no toca ni la DB ni el CSV"
          + ("" if ok else f"\n         salida={salida} csv_intacto={antes == despues}"))
    return 0 if ok else 1


def test_e_postgres_caido_sale_con_error_y_no_toca_el_csv(tmp):
    """(e) Postgres inalcanzable (puerto malo a propósito) -> exit != 0, CSV intacto -- nunca cae
    de vuelta a escribir el CSV directo."""
    dimp = _escribir_csv(
        os.path.join(tmp, "_DIM_PRODUCTOS.csv"),
        ["producto_key", "nombre_display", "slug_carpeta"],
        [["TINNIDROP", "Tinnidrop Importado Original", "TINNIDROP"]])
    dimctas = _escribir_csv(
        os.path.join(tmp, "_DIM_CUENTAS.csv"),
        ["cuenta_alias", "cuenta_id", "moneda"],
        [["GTR 0", "1665221077707961", "USD"]])
    fact = _escribir_csv(os.path.join(tmp, "_FACT_VENTAS.csv"), ing.COLS, [])
    dimc = _escribir_csv(
        os.path.join(tmp, "_DIM_CONJUNTOS.csv"),
        ["conjunto_meta"], [["CONJ_CONOCIDO"]])
    bkdir = os.path.join(tmp, "backups_csv")
    rutas = dict(DIMP=dimp, DIMCTAS=dimctas, FACT=fact, DIMC=dimc, BKDIR=bkdir, TENANT_ID="x")

    fila = _fila_lucidsales("Tinnidrop", "1665221077707961", "CONJ_CONOCIDO", "AD_1", "ad_1")
    export = _escribir_export(os.path.join(tmp, "sim-2026-09-14.json"), [fila])
    antes = open(fact, "rb").read()

    puerto_real = os.environ.get("PGPORT")
    os.environ["PGPORT"] = "1"  # puerto que nunca escucha Postgres, a propósito
    try:
        salida = _correr_main(rutas, [export])
    finally:
        if puerto_real is None:
            os.environ.pop("PGPORT", None)
        else:
            os.environ["PGPORT"] = puerto_real

    despues = open(fact, "rb").read()
    bloqueo = salida is not None and salida.code != 0
    mensaje_ok = salida is not None and "Postgres no disponible" in str(salida)
    no_escribio = antes == despues

    ok = bloqueo and mensaje_ok and no_escribio
    print(("  OK     " if ok else "  FALLA  ")
          + "Postgres caído: exit != 0, mensaje claro, CSV intacto"
          + ("" if ok else f"\n         bloqueo={bloqueo} mensaje_ok={mensaje_ok} "
                            f"no_escribio={no_escribio} salida={salida}"))
    return 0 if ok else 1


def main():
    fallas = 0
    for fn in (
        test_a_dia_nuevo_escribe_en_db_y_espejo_byte_identico_a_upsert_fact,
        test_b_re_correr_mismo_input_es_idempotente_y_no_toca_el_espejo,
        test_c_guardia_de_drift_aborta_y_no_escribe_nada,
        test_d_dry_run_no_toca_ni_la_db_ni_el_csv,
        test_e_postgres_caido_sale_con_error_y_no_toca_el_csv,
    ):
        with tempfile.TemporaryDirectory() as tmp:
            fallas += fn(tmp)
    print(f"\n{'0 fallas' if not fallas else str(fallas) + ' falla(s)'}.")
    return 1 if fallas else 0


if __name__ == "__main__":
    sys.exit(main())
