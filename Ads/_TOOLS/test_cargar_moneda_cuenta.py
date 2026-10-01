#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_cargar_moneda_cuenta.py — GATE DE LA CARGA DE LA moneda DE LA CUENTA.

Congela lo que cargar_moneda_cuenta.py no puede romper nunca:
  · una moneda desconocida («ABC») se rechaza, diciendo cuales valen;
  · si la cuenta del producto ESTA en _DIM_CUENTAS.csv, la moneda la dicta ella: pedir otra
    se rechaza nombrando la cuenta (eso es cargar_cuenta.py), aunque venga --reemplazar;
  · una moneda ya cargada no se cambia sin --reemplazar; con --reemplazar solo cambia ese
    campo de esa fila, nada mas;
  · pedir la misma moneda que ya tiene es «sin cambios» y no escribe;
  · --dry-run no toca el disco.

Aislamiento CRÍTICO (mismo patrón que test_cargar_page_id.py): fuerza
`PGDATABASE=vitalcom_test` ANTES de conectar, bootstrapea raw.producto/raw.raw_import en su
PROPIO tenant único para esta corrida y nunca toca `vitalcom` real. Se salta con aviso si
`vitalcom_test` no está disponible en este entorno.

USO:  python Ads/_TOOLS/test_cargar_moneda_cuenta.py     (exit 0 = pasa/salta, 1 = falla)
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
import cargar_moneda_cuenta  # noqa: E402

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
            "test_cargar_moneda_cuenta.py intentó conectarse a 'vitalcom' en vez de 'vitalcom_test'. "
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
    return "test_moneda_%s" % uuid.uuid4().hex[:8]


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


def _columnas_reales():
    ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..",
                        "PRODUCTOS", "_DIM_PRODUCTOS.csv")
    with io.open(os.path.normpath(ruta), encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh).fieldnames)


def _fila_producto(columnas, **campos):
    base = {c: "" for c in columnas}
    base.update(campos)
    return [base[c] for c in columnas]


def _escribir_csv(ruta, columnas, filas):
    with io.open(ruta, "w", encoding="utf-8", newline="") as fh:
        escritor = csv.writer(fh)
        escritor.writerow(columnas)
        escritor.writerows(filas)


def _escribir(base, relativa, texto):
    ruta = os.path.join(base, *relativa.split("/"))
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with io.open(ruta, "wb") as fh:
        fh.write(texto.encode("utf-8"))


def _leer(base, relativa):
    with io.open(os.path.join(base, *relativa.split("/")), "rb") as fh:
        return fh.read().decode("utf-8")


def _fixture(base):
    columnas = _columnas_reales()
    os.makedirs(os.path.join(base, "PRODUCTOS"))
    _escribir_csv(os.path.join(base, "PRODUCTOS", "_DIM_PRODUCTOS.csv"), columnas, [
        _fila_producto(columnas, producto_key="PX_GTR", slug_carpeta="PX_GTR", estado="VIVO",
                       cuenta_alias="GTR 7", moneda="USD", tasa="7.62", mercado="GT"),
        _fila_producto(columnas, producto_key="PX_EXT", slug_carpeta="PX_EXT", estado="NUEVO",
                       cuenta_alias="EXTERNA", moneda="COP", tasa="3152.5", mercado="CO"),
        _fila_producto(columnas, producto_key="PX_DRY", slug_carpeta="PX_DRY", estado="NUEVO",
                       cuenta_alias="EXTERNA", moneda="COP", tasa="3152.5", mercado="CO"),
        _fila_producto(columnas, producto_key="OTRO", slug_carpeta="OTRO", estado="VIVO",
                       cuenta_alias="GTR 7", moneda="USD", tasa="7.62", mercado="GT"),
    ])
    _escribir_csv(os.path.join(base, "PRODUCTOS", "_DIM_CUENTAS.csv"),
                  ["cuenta_alias", "cuenta_id", "moneda", "estado_cuenta"],
                  [["GTR 7", "598687956219141", "USD", "ACTIVE"],
                   ["COB 1", "999", "COP", "ACTIVE"]])
    _escribir_csv(os.path.join(base, "PRODUCTOS", "_DIM_MERCADOS.csv"),
                  ["mercado", "moneda"],
                  [["GT", "GTQ"],
                   ["CO", "COP"]])
    tenant = _tenant_unico()
    cargar_moneda_cuenta.ep.TENANT_ID = tenant
    _bootstrap_producto(os.path.join(base, "PRODUCTOS"), tenant)


def _filas(base):
    contenido = _leer(base, "PRODUCTOS/_DIM_PRODUCTOS.csv")
    filas = list(csv.reader(io.StringIO(contenido, newline="")))
    return filas[0], filas[1:]


def _fila(base, clave):
    encabezado, filas = _filas(base)
    return dict(zip(encabezado, next(f for f in filas if f and f[0] == clave)))


def _correr(base, producto, moneda, *extra):
    return cargar_moneda_cuenta.main(["--producto", producto, "--moneda", moneda,
                                      "--base", base, *extra])


def _en_silencio(funcion):
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
        print("GATE DE LA CARGA DE LA moneda")
        print("  SKIP   Postgres/vitalcom_test no disponible en este entorno")
        return 0
    fallas = []
    base = tempfile.mkdtemp(prefix="moneda_test_")
    try:
        _fixture(base)

        def rechaza_una_moneda_desconocida():
            antes = _leer(base, "PRODUCTOS/_DIM_PRODUCTOS.csv")
            codigo, salida = _en_silencio(lambda: _correr(base, "PX_EXT", "ABC", "--json"))
            assert codigo == 1, salida
            detalle = json.loads(salida)["detalle"]
            assert "ABC" in detalle and "USD" in detalle and "COP" in detalle, detalle
            assert _leer(base, "PRODUCTOS/_DIM_PRODUCTOS.csv") == antes

        def la_cuenta_registrada_dicta_la_moneda():
            codigo, salida = _en_silencio(
                lambda: _correr(base, "PX_GTR", "COP", "--reemplazar", "--json"))
            assert codigo == 1, salida
            detalle = json.loads(salida)["detalle"]
            assert "GTR 7" in detalle and "cargar_cuenta.py" in detalle, detalle
            assert _fila(base, "PX_GTR")["moneda"] == "USD"

        def sin_reemplazar_no_cambia_una_moneda_cargada():
            antes = _leer(base, "PRODUCTOS/_DIM_PRODUCTOS.csv")
            assert _en_silencio(lambda: _correr(base, "PX_EXT", "USD"))[0] == 1
            assert _leer(base, "PRODUCTOS/_DIM_PRODUCTOS.csv") == antes

        def con_reemplazar_solo_cambia_ese_campo_de_esa_fila():
            encabezado, filas_antes = _filas(base)
            col_moneda = encabezado.index("moneda")
            assert _en_silencio(lambda: _correr(base, "PX_EXT", "USD", "--reemplazar"))[0] == 0
            encabezado_desp, filas_desp = _filas(base)
            assert encabezado_desp == encabezado
            assert len(filas_desp) == len(filas_antes)
            for antes_f, desp_f in zip(filas_antes, filas_desp):
                if desp_f[0] == "PX_EXT":
                    assert desp_f[col_moneda] == "USD", desp_f
                    assert [c for i, c in enumerate(desp_f) if i != col_moneda] == \
                           [c for i, c in enumerate(antes_f) if i != col_moneda]
                else:
                    assert desp_f == antes_f, desp_f[0]

        def pedir_la_misma_moneda_es_sin_cambios_y_no_escribe():
            antes = _leer(base, "PRODUCTOS/_DIM_PRODUCTOS.csv")
            codigo, salida = _en_silencio(lambda: _correr(base, "PX_GTR", "USD", "--json"))
            resultado = json.loads(salida)
            assert codigo == 0 and resultado["sin_cambios"] is True \
                and resultado["aplicado"] is False, resultado
            assert _leer(base, "PRODUCTOS/_DIM_PRODUCTOS.csv") == antes

        def dry_run_no_toca_el_disco():
            antes = _leer(base, "PRODUCTOS/_DIM_PRODUCTOS.csv")
            assert _en_silencio(
                lambda: _correr(base, "PX_DRY", "USD", "--reemplazar", "--dry-run"))[0] == 0
            assert _leer(base, "PRODUCTOS/_DIM_PRODUCTOS.csv") == antes
            assert _fila(base, "PX_DRY")["moneda"] == "COP"

        print("GATE DE LA CARGA DE LA moneda")
        for nombre, funcion in (
            ("rechaza una moneda desconocida diciendo cuales valen", rechaza_una_moneda_desconocida),
            ("la cuenta registrada dicta la moneda aunque venga --reemplazar",
             la_cuenta_registrada_dicta_la_moneda),
            ("sin --reemplazar no cambia una moneda cargada", sin_reemplazar_no_cambia_una_moneda_cargada),
            ("con --reemplazar solo cambia ese campo de esa fila",
             con_reemplazar_solo_cambia_ese_campo_de_esa_fila),
            ("pedir la misma moneda es sin cambios y no escribe", pedir_la_misma_moneda_es_sin_cambios_y_no_escribe),
            ("--dry-run no toca el disco", dry_run_no_toca_el_disco),
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
