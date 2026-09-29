#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_cargar_cuenta.py — GATE DE LA ASIGNACION DE CUENTA.

Congela lo que cargar_cuenta.py no puede romper nunca:
  · la cuenta sale de _DIM_CUENTAS.csv (una que no existe se rechaza) y se guarda en la forma
    corta («GTR 7» -> «GTR7») con SU cuenta_id, como ya la llevan los productos del portafolio;
  · una cuenta RETIRADA se rechaza; una sin MCP o en otra moneda se asigna y se AVISA;
  · una cuenta ya asignada no se cambia sin --reemplazar (mover de cuenta es una decision);
  · solo se toca la fila del producto: el resto del CSV queda byte a byte igual (invariante 11);
  · no inventa columnas: no toca moneda, tasa ni cifras de costeo;
  · --dry-run no toca nada y volver a correrlo no cambia nada.

P3 T4 (continuación parte 2) — `editar_producto.aplicar_escrituras()` escribe la fila de
_DIM_PRODUCTOS.csv por Postgres (db/escribir.py): la VERDAD pasa a raw.producto/core.producto.
Aislamiento CRÍTICO (mismo patrón que test_registrar_evento.py/test_alta_producto.py): fuerza
`PGDATABASE=vitalcom_test` ANTES de conectar, bootstrapea raw.producto/raw.raw_import en su
PROPIO tenant único para esta corrida y nunca toca `vitalcom` real. Se salta con aviso si
`vitalcom_test` no está disponible en este entorno.

USO:  python Ads/_TOOLS/test_cargar_cuenta.py     (exit 0 = pasa/salta, 1 = falla)
"""

import csv
import io
import json
import os
import shutil
import sys
import tempfile
import uuid

# Aislamiento CRÍTICO: forzar vitalcom_test ANTES de conectar.
os.environ["PGDATABASE"] = "vitalcom_test"

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cargar_cuenta  # noqa: E402

DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "db")
sys.path.insert(0, DB_DIR)
import cargar as db_cargar  # noqa: E402
import nucleo as db_nucleo  # noqa: E402


def _preparar_base_de_pruebas():
    try:
        if db_cargar.asegurar_base_de_datos("vitalcom_test"):
            db_cargar.aplicar_schema(dbname="vitalcom_test")
    except Exception:
        pass


_preparar_base_de_pruebas()


def _conectar_seguro():
    con = db_cargar.conectar()
    if con.info.dbname == "vitalcom":
        con.close()
        raise RuntimeError(
            "test_cargar_cuenta.py intentó conectarse a 'vitalcom' en vez de 'vitalcom_test'. "
            "Abortado antes de tocar nada.")
    return con


def _db_disponible():
    try:
        con = _conectar_seguro()
        con.close()
        return True
    except Exception:
        return False


DB_DISPONIBLE = _db_disponible()


def _tenant_unico():
    return "test_cuenta_%s" % uuid.uuid4().hex[:8]


def _bootstrap_producto(prod_dir, tenant):
    con = _conectar_seguro()
    try:
        with con:
            with con.cursor() as cur:
                n, sha = db_cargar.cargar_tabla(cur, tenant, "producto", "_DIM_PRODUCTOS.csv",
                                                 False, prod_dir)
                cur.execute(
                    "INSERT INTO raw.raw_import (tenant_id, archivo, sha256, filas) "
                    "VALUES (%s, %s, %s, %s)", (tenant, "_DIM_PRODUCTOS.csv", sha, n))
                db_nucleo.construir_core(cur, tenant)
    finally:
        con.close()

COLUMNAS_PRODUCTOS = [
    "producto_key", "nombre_display", "slug_carpeta", "estado", "fase", "cuenta_alias",
    "cuenta_id", "page_id", "moneda", "tasa", "costo_q", "fila_costeo_q", "precio_base_q",
    "cpa_base_q", "cpa_be_q", "cpa_be_anterior_q", "notas", "carpeta_videos",
    "carpeta_transcripciones", "carpeta_media", "carpetas_extra", "clave_campana", "campaign_id",
    "mercado",
]
COLUMNAS_CUENTAS = [
    "cuenta_alias", "cuenta_id", "negocio_id", "negocio", "moneda", "min_daily_budget_cents",
    "mcp_habilitado", "consultable", "tiene_metodo_pago", "sube_media_local", "estado_cuenta",
    "verificado_el", "fuente", "notas",
]
CUENTAS = [
    ["GTR 7", "598687956219141", "1", "AMG 5", "USD", "100", "SI", "SI", "SI", "SI", "ACTIVE", "", "", ""],
    ["GTR 0", "1665221077707961", "2", "AMG 2", "USD", "100", "SI", "SI", "SI", "NO", "ACTIVE", "", "", ""],
    ["GTR 13", "916746367261028", "3", "AMG 9", "USD", "100", "NO", "SI", "SI", "NO", "ACTIVE", "", "", ""],
    ["GTR 2", "1680252426660775", "2", "AMG 2", "USD", "100", "NO", "SI", "SI", "NO", "RETIRADA", "", "", ""],
    ["Cuenta COP", "332010724162945", "", "", "COP", "3154", "SI", "SI", "NO", "NO", "ACTIVE", "", "", ""],
]


def _fila_producto(**campos):
    base = {c: "" for c in COLUMNAS_PRODUCTOS}
    base["mercado"] = "GT"  # el mercado es obligatorio: los productos del fixture venden en Guatemala
    base.update(campos)
    return [base[c] for c in COLUMNAS_PRODUCTOS]


def _escribir_csv(ruta, columnas, filas):
    with io.open(ruta, "w", encoding="utf-8", newline="") as fh:
        escritor = csv.writer(fh)
        escritor.writerow(columnas)
        escritor.writerows(filas)


def _fixture(carpeta):
    os.makedirs(os.path.join(carpeta, "PRODUCTOS"))
    _escribir_csv(os.path.join(carpeta, "PRODUCTOS", "_DIM_PRODUCTOS.csv"), COLUMNAS_PRODUCTOS, [
        _fila_producto(producto_key="TINNIDROP", cuenta_alias="GTR0", cuenta_id="1665221077707961",
                       moneda="USD", tasa="7.62", costo_q="41", campaign_id="120251463036910595",
                       notas='una nota, con coma\ny salto de linea'),
        _fila_producto(producto_key="NUEVO_UNO", cuenta_alias="PENDIENTE", moneda="GTQ", costo_q="60"),
        _fila_producto(producto_key="NUEVO_DOS", cuenta_alias="", moneda="GTQ", costo_q="45"),
        _fila_producto(producto_key="EXTERNO", cuenta_alias="EXTERNA", moneda="COP", costo_q="7000", mercado="CO"),
    ])
    _escribir_csv(os.path.join(carpeta, "PRODUCTOS", "_DIM_CUENTAS.csv"), COLUMNAS_CUENTAS, CUENTAS)
    tenant = _tenant_unico()
    cargar_cuenta.ep.TENANT_ID = tenant
    _bootstrap_producto(os.path.join(carpeta, "PRODUCTOS"), tenant)


def _bytes(base, nombre="_DIM_PRODUCTOS.csv"):
    with io.open(os.path.join(base, "PRODUCTOS", nombre), "rb") as fh:
        return fh.read()


def _fila(base, clave):
    filas = list(csv.reader(io.StringIO(_bytes(base).decode("utf-8"), newline="")))
    return dict(zip(filas[0], next(f for f in filas[1:] if f and f[0] == clave)))


def _correr(base, producto, cuenta, *extra):
    return cargar_cuenta.main(["--producto", producto, "--cuenta", cuenta, "--base", base, *extra])


def _en_silencio_json(funcion):
    salida = io.StringIO()
    real, sys.stdout = sys.stdout, salida
    try:
        codigo = funcion()
    finally:
        sys.stdout = real
    return codigo, salida.getvalue()


def caso(nombre, funcion, fallas):
    try:
        funcion()
        print(f"  OK   {nombre}")
    except AssertionError as error:
        fallas.append(nombre)
        print(f"  FALLA {nombre}: {error}")


def main():
    if not DB_DISPONIBLE:
        print("GATE DE LA ASIGNACION DE CUENTA")
        print("  SKIP   Postgres/vitalcom_test no disponible en este entorno")
        return 0
    fallas = []
    base = tempfile.mkdtemp(prefix="cuenta_test_")
    try:
        _fixture(base)

        def asigna_forma_corta_con_su_id():
            assert _correr(base, "NUEVO_UNO", "GTR 7") == 0
            fila = _fila(base, "NUEVO_UNO")
            assert fila["cuenta_alias"] == "GTR7", fila["cuenta_alias"]
            assert fila["cuenta_id"] == "598687956219141", fila["cuenta_id"]

        def acepta_el_alias_sin_espacio_y_en_minuscula():
            assert _correr(base, "NUEVO_DOS", "gtr13") == 0
            fila = _fila(base, "NUEVO_DOS")
            assert (fila["cuenta_alias"], fila["cuenta_id"]) == ("GTR13", "916746367261028"), fila

        def solo_toca_la_fila_del_producto():
            antes = _bytes(base)
            assert _correr(base, "EXTERNO", "GTR 0") == 0
            despues = _bytes(base)
            lineas_a = antes.decode("utf-8").split("\r\n")
            lineas_d = despues.decode("utf-8").split("\r\n")
            # La fila de TINNIDROP lleva un salto de linea dentro de una nota: sigue entera.
            assert _fila(base, "TINNIDROP")["notas"] == "una nota, con coma\ny salto de linea"
            assert b"\r\n" in despues and len(lineas_a) == len(lineas_d)
            distintas = [i for i, (a, d) in enumerate(zip(lineas_a, lineas_d)) if a != d]
            assert len(distintas) == 1 and lineas_d[distintas[0]].startswith("EXTERNO,"), \
                f"se tocaron lineas ajenas: {distintas}"

        def no_toca_moneda_tasa_ni_costeo():
            fila = _fila(base, "EXTERNO")
            assert fila["moneda"] == "COP" and fila["costo_q"] == "7000", fila
            for columna in ("tasa", "fila_costeo_q", "precio_base_q", "cpa_base_q", "cpa_be_q", "fase"):
                assert fila[columna] == "", f"{columna} no es de este escritor: «{fila[columna]}»"

        def rechaza_cuenta_que_no_existe():
            antes = _bytes(base)
            assert _correr(base, "NUEVO_UNO", "GTR 99", "--reemplazar") == 1
            assert _bytes(base) == antes, "al rechazar no se escribe nada"

        def rechaza_las_marcas_de_pendiente():
            for marca in ("PENDIENTE", "SIN_MCP", "-"):
                assert _correr(base, "NUEVO_DOS", marca, "--reemplazar") == 1, marca

        def rechaza_cuenta_retirada():
            assert _correr(base, "NUEVO_DOS", "GTR 2", "--reemplazar") == 1

        def rechaza_producto_sin_fila():
            assert _correr(base, "NO_EXISTE", "GTR 7") == 1

        def no_cambia_una_cuenta_asignada_sin_reemplazar():
            antes = _bytes(base)
            assert _correr(base, "TINNIDROP", "GTR 7") == 1
            assert _bytes(base) == antes
            assert _fila(base, "TINNIDROP")["cuenta_alias"] == "GTR0"

        def reemplaza_con_bandera_y_avisa_de_la_campana():
            salida = io.StringIO()
            real, sys.stdout = sys.stdout, salida
            try:
                assert _correr(base, "TINNIDROP", "GTR 7", "--reemplazar", "--json") == 0
            finally:
                sys.stdout = real
            resultado = json.loads(salida.getvalue())
            assert _fila(base, "TINNIDROP")["cuenta_alias"] == "GTR7"
            assert any("campaign_id" in a for a in resultado["avisos"]), resultado["avisos"]

        def avisa_de_lo_que_no_impide_asignar():
            salida = io.StringIO()
            real, sys.stdout = sys.stdout, salida
            try:
                assert _correr(base, "NUEVO_UNO", "GTR 13", "--reemplazar", "--json") == 0
                sin_mcp = json.loads(salida.getvalue())
                salida.seek(0), salida.truncate()
                assert _correr(base, "NUEVO_UNO", "Cuenta COP", "--reemplazar", "--json") == 0
                en_cop = json.loads(salida.getvalue())
            finally:
                sys.stdout = real
            assert any("MCP" in a for a in sin_mcp["avisos"]), sin_mcp["avisos"]
            assert any("COP" in a for a in en_cop["avisos"]), en_cop["avisos"]
            assert any("metodo de pago" in a for a in en_cop["avisos"]), en_cop["avisos"]

        def volver_a_correr_no_cambia_nada():
            _correr(base, "NUEVO_DOS", "GTR 7", "--reemplazar")
            antes = _bytes(base)
            salida = io.StringIO()
            real, sys.stdout = sys.stdout, salida
            try:
                assert _correr(base, "NUEVO_DOS", "GTR 7", "--json") == 0
            finally:
                sys.stdout = real
            resultado = json.loads(salida.getvalue())
            assert resultado["sin_cambios"] is True and resultado["aplicado"] is False, resultado
            assert _bytes(base) == antes

        def dry_run_no_toca_nada():
            antes = _bytes(base)
            assert _correr(base, "EXTERNO", "GTR 7", "--dry-run", "--reemplazar") == 0
            assert _bytes(base) == antes

        def una_falla_de_postgres_no_deja_restos():
            """P3 T4 continuación parte 2: cargar_cuenta.py solo toca _DIM_PRODUCTOS.csv (nada
            de TXT) -- todo el batch va a Postgres. Si el guardia de drift lo rechaza (acá,
            simulado con un tenant que nunca se bootstrapeó), no se escribe nada: ni el CSV
            (Postgres nunca comitea) ni un .tmp perdido."""
            antes = _bytes(base)
            real_tenant = cargar_cuenta.ep.TENANT_ID
            cargar_cuenta.ep.TENANT_ID = "test_cuenta_nunca_importado_%s" % uuid.uuid4().hex[:8]
            try:
                codigo, salida = _en_silencio_json(lambda: _correr(base, "EXTERNO", "GTR 13", "--reemplazar", "--json"))
            finally:
                cargar_cuenta.ep.TENANT_ID = real_tenant
            assert codigo == 1, salida
            assert "nunca se importo" in json.loads(salida)["detalle"], salida
            assert _bytes(base) == antes, "el CSV tiene que quedar como estaba"
            assert not any(n.endswith(".tmp") for n in os.listdir(os.path.join(base, "PRODUCTOS"))), \
                "no puede quedar un temporal"

        print("GATE DE LA ASIGNACION DE CUENTA")
        for nombre, funcion in (
            ("asigna la forma corta con su cuenta_id", asigna_forma_corta_con_su_id),
            ("acepta «gtr13» sin espacio ni mayuscula", acepta_el_alias_sin_espacio_y_en_minuscula),
            ("solo toca la fila del producto", solo_toca_la_fila_del_producto),
            ("no toca moneda, tasa ni cifras de costeo", no_toca_moneda_tasa_ni_costeo),
            ("rechaza una cuenta que no esta en _DIM_CUENTAS", rechaza_cuenta_que_no_existe),
            ("rechaza PENDIENTE / SIN_MCP como cuenta", rechaza_las_marcas_de_pendiente),
            ("rechaza una cuenta RETIRADA", rechaza_cuenta_retirada),
            ("rechaza un producto sin fila", rechaza_producto_sin_fila),
            ("no cambia una cuenta ya asignada sin --reemplazar", no_cambia_una_cuenta_asignada_sin_reemplazar),
            ("--reemplazar la cambia y avisa de la campana", reemplaza_con_bandera_y_avisa_de_la_campana),
            ("avisa sin MCP, moneda y metodo de pago", avisa_de_lo_que_no_impide_asignar),
            ("volver a correr no cambia nada", volver_a_correr_no_cambia_nada),
            ("--dry-run no toca el disco", dry_run_no_toca_nada),
            ("una falla de Postgres no deja restos", una_falla_de_postgres_no_deja_restos),
        ):
            caso(nombre, funcion, fallas)
    finally:
        shutil.rmtree(base, ignore_errors=True)

    if fallas:
        print(f"\n{len(fallas)} falla(s): " + ", ".join(fallas))
        return 1
    print("\nTodo en verde.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
