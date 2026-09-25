#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_ingerir_lucidsales.py — GATE DE LA INGESTA DE LUCIDSALES.

Congela lo que la simulación de Turmeric (22-sep-2026) encontró roto en
ingerir_lucidsales.py: un producto sin fila en _DIM_PRODUCTOS.csv caía en
SIN_CLASIFICAR con el diccionario PROD_KEY cableado a mano, y el chequeo de
integridad imprimía "JOIN cierra al 100%" igual — 120 filas, 35 ventas y
$165.69 perdidos en silencio, sin una sola alerta.

Dos arreglos, dos gates:
  1. producto_key() y el alias de cuenta salen de _DIM_PRODUCTOS.csv y
     _DIM_CUENTAS.csv (los dueños del dato), no de un diccionario aparte.
  2. Una fila SIN_CLASIFICAR o un conjunto huérfano hacen FALLAR la corrida
     (SystemExit, exit != 0) — pero DESPUÉS de escribir lo que sí se pudo
     clasificar: perder una venta real es peor que un aviso.

USO:  python Ads/_TOOLS/test_ingerir_lucidsales.py     (exit 0 = pasa, 1 = falla)

P3 T3 — aislamiento de Postgres (CRÍTICO, ver db/README.md "Aislamiento de pruebas"):
`ingerir_lucidsales.py` ahora escribe `_FACT_VENTAS.csv` a través de Postgres
(`db/escribir.py`), nunca directo al CSV. Las pruebas de este archivo NUNCA deben tocar la base
real `vitalcom` (sostiene la verdad real de P3 desde T3): se fuerza `PGDATABASE=vitalcom_test`
ANTES de importar `ingerir_lucidsales` (que a su vez importa `db/cargar.py`/`db/escribir.py`), se
verifica que la conexión resultante NO sea `vitalcom`, y cada escenario usa su propio
`TENANT_ID` (vía `ing.TENANT_ID`, que `_correr_main` ya sabe sobreescribir) para no interferir con
otros escenarios de este mismo archivo. Si `vitalcom_test` no existe y el rol no tiene permiso
`CREATEDB` (caso real de este entorno — ver db/README.md), las pruebas que necesitan Postgres se
SALTAN con aviso, nunca caen de vuelta a `vitalcom`.
"""
import csv
import json
import os
import sys
import tempfile
import uuid

# P3 T3: forzar ANTES de importar ingerir_lucidsales (que importa db/cargar.py -- su
# `cargar_env()` da prioridad a `os.environ` sobre el `.env` de disco, ver su docstring).
os.environ["PGDATABASE"] = "vitalcom_test"

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ingerir_lucidsales as ing  # noqa: E402

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


def _conectar_seguro():
    """GUARDIA (P3 T3, crítico): igual que `db_cargar.conectar()`, pero rehúsa devolver una
    conexión a `vitalcom` -- la base REAL con la verdad de P3. Ninguna prueba de este archivo debe
    escribir ahí."""
    con = db_cargar.conectar()
    if con.info.dbname == "vitalcom":
        con.close()
        raise RuntimeError(
            "P3 T3: una prueba de test_ingerir_lucidsales.py intentó conectarse a 'vitalcom' en "
            "vez de 'vitalcom_test'. Abortado antes de tocar nada.")
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
    return "test_lucidsales_%s_%s" % (nombre, uuid.uuid4().hex[:8])


def _bootstrap_db(prod_dir, tenant_id):
    """Siembra raw.venta (P3 T3) con lo que YA hay en `<prod_dir>/_FACT_VENTAS.csv` -- satisface
    el guardia de drift para la corrida de `ing.main()` que sigue, igual que
    `db/cargar.py --tomar-csv` haría en producción antes de la primera escritura real. Registra
    también en `raw.raw_import` (igual que `tomar_csv()`/`cargar_todo()`): el guardia mide "¿ya se
    importó?" por ese log, no por el conteo de filas (ver `db/escribir.verificar_csv_sincronizado`)."""
    con = _conectar_seguro()
    try:
        with con:
            with con.cursor() as cur:
                n, sha = db_cargar.cargar_tabla(cur, tenant_id, "venta", "_FACT_VENTAS.csv", False,
                                                 prod_dir)
                cur.execute(
                    "INSERT INTO raw.raw_import (tenant_id, archivo, sha256, filas) "
                    "VALUES (%s, %s, %s, %s)", (tenant_id, "_FACT_VENTAS.csv", sha, n))
                db_nucleo.construir_core(cur, tenant_id)
    finally:
        con.close()


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


def test_producto_key_variantes_reales(tmp):
    """Las keywords se derivan de _DIM_PRODUCTOS.csv, sobre nombres REALES vistos
    en _FACT_VENTAS.csv (LucidSales nunca manda el mismo nombre dos veces igual)."""
    dimp = _escribir_csv(
        os.path.join(tmp, "_DIM_PRODUCTOS.csv"),
        ["producto_key", "nombre_display", "slug_carpeta"],
        [["TINNIDROP", "Tinnidrop Importado Original", "TINNIDROP"],
         ["NUSAVA", "NUSAVA B12", "NusavaB12"],
         ["CLEARSTEM", "Clearstem Mindbodyskin", "CLEARSTEM"],
         ["VARICOSE", "Varicose Veins Ointment", "VARICOSE"]])
    productos = ing.cargar_productos(dimp)

    casos = [
        ("Tinnidrop", "TINNIDROP"),
        ("Tinnidrop Importado Original", "TINNIDROP"),
        ("NUSAVA B12", "NUSAVA"),
        ("NUSAVA B12 oferta original importado", "NUSAVA"),
        ("NusavaB12", "NUSAVA"),
        ("Clearstem", "CLEARSTEM"),
        ("Clearstem Mindbodyskin Suplemento 90 Cápsulas Importado USA", "CLEARSTEM"),
        ("Varicose", "VARICOSE"),
        ("Varicose 2x1 oferta VER", "VARICOSE"),
        ("Turmeric Curcumin Importado", "SIN_CLASIFICAR"),
    ]
    fallas = 0
    for nombre, esperado in casos:
        obtenido = ing.producto_key(nombre, productos)
        if obtenido == esperado:
            print(f"  OK     producto_key({nombre!r}) = {esperado}")
        else:
            fallas += 1
            print(f"  FALLA  producto_key({nombre!r}) esperado={esperado} obtenido={obtenido}")
    return fallas


def test_cargar_cuentas_alias_compacto(tmp):
    """cuenta_alias pierde el espacio: el resto del sistema usa 'GTR7', no 'GTR 7'."""
    dimc = _escribir_csv(
        os.path.join(tmp, "_DIM_CUENTAS.csv"),
        ["cuenta_alias", "cuenta_id", "moneda"],
        [["GTR 7", "598687956219141", "USD"],
         ["CP1", "1346891653335162", "COP"]])
    cuentas = ing.cargar_cuentas(dimc)
    ok = (cuentas["598687956219141"]["alias"] == "GTR7"
          and cuentas["598687956219141"]["moneda"] == "USD"
          and cuentas["1346891653335162"]["alias"] == "CP1"
          and cuentas["1346891653335162"]["moneda"] == "COP")
    print(("  OK     " if ok else "  FALLA  ")
          + "cuenta_alias 'GTR 7' -> 'GTR7' (sin espacio), moneda por cuenta"
          + ("" if ok else f"\n         {cuentas}"))
    return 0 if ok else 1


def test_s_id_nunca_notacion_cientifica(tmp):
    """s_id() (22-sep-2026, T2): un id de 18 dígitos no debe salir nunca en notación
    científica, y un float que ya perdió precisión (> 2**53) debe volver "" —
    nunca un id falso — contando el descarte en ids_perdidos()."""
    ing.reiniciar_ids_perdidos()
    casos = [
        # (entrada, esperado, descripcion)
        ("123456789012345678", "123456789012345678", "str de 18 dígitos exacto"),
        (123456789012345678, "123456789012345678", "int de 18 dígitos exacto"),
        (598687956219141.0, "598687956219141", "float integral <= 2**53 (id de cuenta típico)"),
        ("1.2345678901234568e+17", "", "str en notación científica -> irrecuperable"),
        (None, "", "None -> vacío"),
    ]
    fallas = []
    for entrada, esperado, desc in casos:
        obtenido = ing.s_id(entrada)
        if obtenido != esperado:
            fallas.append(f"{desc}: s_id({entrada!r}) = {obtenido!r}, esperaba {esperado!r}")
        if any(c in obtenido for c in ("e+", "e-", "E+", "E-")):
            fallas.append(f"{desc}: {obtenido!r} quedó en notación científica")

    # float > 2**53: no hay dígito correcto que reconstruir (Excel/JS ya lo truncó) -> "".
    grande = float(2 ** 53) * 100  # muy por encima del límite de precisión
    obtenido_grande = ing.s_id(grande)
    if obtenido_grande != "":
        fallas.append(f"float > 2**53 debía dar \"\", dio {obtenido_grande!r}")

    obtenido_nan = ing.s_id(float("nan"))
    if obtenido_nan != "":
        fallas.append(f"NaN debía dar \"\", dio {obtenido_nan!r}")

    perdidos = ing.ids_perdidos()
    if perdidos != 2:  # el str en notación científica + el float > 2**53
        fallas.append(f"ids_perdidos() = {perdidos}, esperaba 2")

    ok = not fallas
    print(("  OK     " if ok else "  FALLA  ") + "s_id() nunca emite notación científica ni un id falso"
          + ("" if ok else "\n         " + "\n         ".join(fallas)))
    return 0 if ok else 1


def test_moneda_sin_tasa_bloquea(tmp):
    """Una cuenta nueva que factura en una moneda sin tasa declarada NO se ingiere
    como si fuera USD en silencio: bloquea con el nombre de la cuenta y la moneda."""
    export = _escribir_export(
        os.path.join(tmp, "sim-2026-09-14.json"),
        [_fila_lucidsales("Tinnidrop", "111", "CONJ_X", "AD_X", "ad_111")])
    cuentas = {"111": {"alias": "CUENTA_NUEVA", "moneda": "GTQ"}}
    try:
        ing.leer_export(export, "BASE", "LucidSales", {"TINNIDROP": ["tinnidrop"]}, cuentas)
        print("  FALLA  moneda GTQ sin tasa declarada no bloqueó (se habría costeado mal en silencio)")
        return 1
    except SystemExit as e:
        ok = "GTQ" in str(e) and "TASAS_A_USD" in str(e)
        print(("  OK     " if ok else "  FALLA  ")
              + "moneda sin tasa declarada bloquea con el nombre de la moneda y dónde arreglarlo"
              + ("" if ok else f"\n         mensaje: {e}"))
        return 0 if ok else 1


def _fixture_flujo(tmp, filas_export, conjuntos_conocidos, nombre="flujo"):
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
        ["conjunto_meta"], [[c] for c in conjuntos_conocidos])
    export = _escribir_export(os.path.join(tmp, "sim-2026-09-14.json"), filas_export)
    bkdir = os.path.join(tmp, "backups_csv")
    tenant = _tenant_unico(nombre)
    _bootstrap_db(tmp, tenant)  # P3 T3: satisface el guardia de drift para el main() que sigue
    return dict(DIMP=dimp, DIMCTAS=dimctas, FACT=fact, DIMC=dimc, BKDIR=bkdir,
                TENANT_ID=tenant), export


def _correr_main(rutas, argv):
    previo = {k: getattr(ing, k) for k in rutas}
    prev_argv = sys.argv
    try:
        for k, v in rutas.items():
            setattr(ing, k, v)
        sys.argv = ["ingerir_lucidsales.py"] + argv
        ing.reiniciar_ids_perdidos()  # cada corrida simulada empieza su propio conteo
        ing.main()
        return None
    except SystemExit as e:
        return e
    finally:
        for k, v in previo.items():
            setattr(ing, k, v)
        sys.argv = prev_argv


def test_gate_bloquea_sin_perder_las_filas_buenas(tmp):
    """Turmeric (SIN_CLASIFICAR) mezclado con una fila buena de TINNIDROP: el proceso
    tiene que SALIR EN ROJO, pero las dos filas quedan escritas en _FACT_VENTAS.csv."""
    if not DB_DISPONIBLE:
        print("  SKIP   Postgres/vitalcom_test no disponible en este entorno")
        return 0
    filas = [
        _fila_lucidsales("Tinnidrop", "1665221077707961", "CONJ_CONOCIDO", "AD_1", "ad_1"),
        _fila_lucidsales("Turmeric Curcumin Importado", "1665221077707961", "CONJ_CONOCIDO", "AD_2", "ad_2"),
    ]
    rutas, export = _fixture_flujo(tmp, filas, conjuntos_conocidos=["CONJ_CONOCIDO"],
                                    nombre="bloquea_sin_perder")
    salida = _correr_main(rutas, [export])

    escritas = list(csv.DictReader(open(rutas["FACT"], newline="", encoding="utf-8")))
    bloqueo = salida is not None and salida.code != 0
    no_perdio_data = len(escritas) == 2
    ok = bloqueo and no_perdio_data
    print(("  OK     " if ok else "  FALLA  ")
          + "SIN_CLASIFICAR bloquea la corrida (exit != 0) sin perder las filas ya escritas"
          + ("" if ok else f"\n         bloqueo={bloqueo} filas_escritas={len(escritas)} salida={salida}"))
    return 0 if ok else 1


def test_gate_bloquea_por_conjunto_huerfano(tmp):
    """Un conjunto que no está en _DIM_CONJUNTOS.csv también bloquea, aunque el
    producto sí esté clasificado — antes solo emitía una advertencia y seguía verde."""
    if not DB_DISPONIBLE:
        print("  SKIP   Postgres/vitalcom_test no disponible en este entorno")
        return 0
    filas = [_fila_lucidsales("Tinnidrop", "1665221077707961", "CONJ_HUERFANO", "AD_1", "ad_1")]
    rutas, export = _fixture_flujo(tmp, filas, conjuntos_conocidos=["OTRO_CONJUNTO"],
                                    nombre="conjunto_huerfano")
    salida = _correr_main(rutas, [export])
    ok = salida is not None and salida.code != 0
    print(("  OK     " if ok else "  FALLA  ")
          + "conjunto huérfano bloquea la corrida (exit != 0)"
          + ("" if ok else f"\n         salida={salida}"))
    return 0 if ok else 1


def test_corrida_limpia_no_bloquea(tmp):
    """Regresión: cuando todo clasifica y el conjunto es conocido, la corrida sigue
    pasando sin bloquear — el gate nuevo no puede convertirse en un falso rojo."""
    if not DB_DISPONIBLE:
        print("  SKIP   Postgres/vitalcom_test no disponible en este entorno")
        return 0
    filas = [_fila_lucidsales("Tinnidrop", "1665221077707961", "CONJ_CONOCIDO", "AD_1", "ad_1")]
    rutas, export = _fixture_flujo(tmp, filas, conjuntos_conocidos=["CONJ_CONOCIDO"],
                                    nombre="corrida_limpia")
    salida = _correr_main(rutas, [export])
    ok = salida is None
    print(("  OK     " if ok else "  FALLA  ")
          + "una corrida limpia (todo clasificado, conjunto conocido) NO bloquea"
          + ("" if ok else f"\n         salida={salida}"))
    return 0 if ok else 1


def test_upsert_reemplaza_dia_parcial_y_es_idempotente(tmp):
    """El caso central de T1 (evidencia g06, 22-sep): un día llega con el gasto/ventas
    CONGELADO a medio día y la corrida siguiente lo trae completo — debe REEMPLAZAR la
    fila vieja (mismo ad_id), no descartarla como duplicado. Re-correr con el mismo
    archivo una tercera vez no debe cambiar nada (idempotencia)."""
    if not DB_DISPONIBLE:
        print("  SKIP   Postgres/vitalcom_test no disponible en este entorno")
        return 0
    dimp = _escribir_csv(
        os.path.join(tmp, "_DIM_PRODUCTOS.csv"), ["producto_key", "nombre_display", "slug_carpeta"],
        [["TINNIDROP", "Tinnidrop Importado Original", "TINNIDROP"]])
    dimctas = _escribir_csv(
        os.path.join(tmp, "_DIM_CUENTAS.csv"), ["cuenta_alias", "cuenta_id", "moneda"],
        [["GTR 0", "1665221077707961", "USD"]])
    fact = _escribir_csv(os.path.join(tmp, "_FACT_VENTAS.csv"), ing.COLS, [])
    dimc = _escribir_csv(os.path.join(tmp, "_DIM_CONJUNTOS.csv"), ["conjunto_meta"],
                          [["CONJ_CONOCIDO"]])
    bkdir = os.path.join(tmp, "backups_csv")
    tenant = _tenant_unico("upsert_parcial")
    _bootstrap_db(tmp, tenant)
    rutas = dict(DIMP=dimp, DIMCTAS=dimctas, FACT=fact, DIMC=dimc, BKDIR=bkdir, TENANT_ID=tenant)

    parcial = _escribir_export(
        os.path.join(tmp, "sim-2026-09-20.json"),
        [_fila_lucidsales("Tinnidrop", "1665221077707961", "CONJ_CONOCIDO", "AD_1", "ad_1",
                          sells=1, spend=7.0)])
    salida1 = _correr_main(rutas, [parcial])
    filas1 = list(csv.DictReader(open(fact, newline="", encoding="utf-8")))
    ok1 = salida1 is None and len(filas1) == 1 and filas1[0]["spend_usd"] == "7.0"

    completo = _escribir_export(
        os.path.join(tmp, "sim-2026-09-20-completo.json"),
        [_fila_lucidsales("Tinnidrop", "1665221077707961", "CONJ_CONOCIDO", "AD_1", "ad_1",
                          sells=1, spend=10.0)])
    salida2 = _correr_main(rutas, [completo])
    filas2 = list(csv.DictReader(open(fact, newline="", encoding="utf-8")))
    ok2 = salida2 is None and len(filas2) == 1 and filas2[0]["spend_usd"] == "10.0"

    salida3 = _correr_main(rutas, [completo])
    filas3 = list(csv.DictReader(open(fact, newline="", encoding="utf-8")))
    ok3 = salida3 is None and filas3 == filas2

    ok = ok1 and ok2 and ok3
    print(("  OK     " if ok else "  FALLA  ")
          + "un día corregido reemplaza la fila parcial (por ad_id) y re-correr es idempotente"
          + ("" if ok else f"\n         ok1={ok1} ok2={ok2} ok3={ok3} "
                            f"filas1={filas1} filas2={filas2} filas3={filas3}"))
    return 0 if ok else 1


def test_control_nunca_reemplaza_base_ni_viceversa(tmp):
    """rol_ventana viaja en la llave natural: un export CONTROL (verificación semanal,
    solapa a propósito) jamás pisa la fila BASE del mismo ad_id/día, y viceversa."""
    if not DB_DISPONIBLE:
        print("  SKIP   Postgres/vitalcom_test no disponible en este entorno")
        return 0
    dimp = _escribir_csv(
        os.path.join(tmp, "_DIM_PRODUCTOS.csv"), ["producto_key", "nombre_display", "slug_carpeta"],
        [["TINNIDROP", "Tinnidrop Importado Original", "TINNIDROP"]])
    dimctas = _escribir_csv(
        os.path.join(tmp, "_DIM_CUENTAS.csv"), ["cuenta_alias", "cuenta_id", "moneda"],
        [["GTR 0", "1665221077707961", "USD"]])
    fact = _escribir_csv(os.path.join(tmp, "_FACT_VENTAS.csv"), ing.COLS, [])
    dimc = _escribir_csv(os.path.join(tmp, "_DIM_CONJUNTOS.csv"), ["conjunto_meta"],
                          [["CONJ_CONOCIDO"]])
    bkdir = os.path.join(tmp, "backups_csv")
    tenant = _tenant_unico("control_vs_base")
    _bootstrap_db(tmp, tenant)
    rutas = dict(DIMP=dimp, DIMCTAS=dimctas, FACT=fact, DIMC=dimc, BKDIR=bkdir, TENANT_ID=tenant)

    base = _escribir_export(
        os.path.join(tmp, "sim-2026-09-20-base.json"),
        [_fila_lucidsales("Tinnidrop", "1665221077707961", "CONJ_CONOCIDO", "AD_1", "ad_1",
                          sells=1, spend=10.0)])
    _correr_main(rutas, [base])

    control = _escribir_export(
        os.path.join(tmp, "sim-2026-09-20-control.json"),
        [_fila_lucidsales("Tinnidrop", "1665221077707961", "CONJ_CONOCIDO", "AD_1", "ad_1",
                          sells=1, spend=10.0)])
    _correr_main(rutas, [control, "--rol", "CONTROL"])

    filas = list(csv.DictReader(open(fact, newline="", encoding="utf-8")))
    roles = sorted(f["rol_ventana"] for f in filas)
    ok = len(filas) == 2 and roles == ["BASE", "CONTROL"]
    print(("  OK     " if ok else "  FALLA  ")
          + "CONTROL y BASE del mismo ad_id/día quedan como DOS filas, ninguna reemplaza a la otra"
          + ("" if ok else f"\n         filas={filas}"))
    return 0 if ok else 1


def main():
    fallas = 0
    with tempfile.TemporaryDirectory() as tmp:
        fallas += test_producto_key_variantes_reales(tmp)
    with tempfile.TemporaryDirectory() as tmp:
        fallas += test_cargar_cuentas_alias_compacto(tmp)
    with tempfile.TemporaryDirectory() as tmp:
        fallas += test_s_id_nunca_notacion_cientifica(tmp)
    with tempfile.TemporaryDirectory() as tmp:
        fallas += test_moneda_sin_tasa_bloquea(tmp)
    with tempfile.TemporaryDirectory() as tmp:
        fallas += test_gate_bloquea_sin_perder_las_filas_buenas(tmp)
    with tempfile.TemporaryDirectory() as tmp:
        fallas += test_gate_bloquea_por_conjunto_huerfano(tmp)
    with tempfile.TemporaryDirectory() as tmp:
        fallas += test_corrida_limpia_no_bloquea(tmp)
    with tempfile.TemporaryDirectory() as tmp:
        fallas += test_upsert_reemplaza_dia_parcial_y_es_idempotente(tmp)
    with tempfile.TemporaryDirectory() as tmp:
        fallas += test_control_nunca_reemplaza_base_ni_viceversa(tmp)
    print(f"\n{'0 fallas' if not fallas else str(fallas) + ' falla(s)'}.")
    return 1 if fallas else 0


if __name__ == "__main__":
    sys.exit(main())
