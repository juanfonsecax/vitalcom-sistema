#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_cargar_estado.py — GATE DE LA CARGA DEL ESTADO DEL PRODUCTO.

Congela lo que cargar_estado.py no puede romper nunca:
  · un estado fuera de NUEVO / VIVO / PAUSADO se rechaza, diciendo cuales valen;
  · NUEVO -> VIVO escribe solo la columna estado de esa fila, nada mas, y el
    aviso trae el comando exacto de registrar_evento.py para dejar el motivo
    en _EVENTOS.csv (el evento no se registra solo);
  · pedir el estado que ya tiene es «sin cambios»: no rechaza y no escribe;
  · --dry-run no toca el disco.

Aislamiento CRÍTICO (mismo patrón que test_cargar_moneda_cuenta.py): fuerza
`PGDATABASE=vitalcom_test` ANTES de conectar, bootstrapea raw.producto/raw.raw_import en su
PROPIO tenant único para esta corrida y nunca toca `vitalcom` real. Se salta con aviso si
`vitalcom_test` no está disponible en este entorno.

USO:  python Ads/_TOOLS/test_cargar_estado.py     (exit 0 = pasa/salta, 1 = falla)
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
import cargar_estado  # noqa: E402

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
            "test_cargar_estado.py intentó conectarse a 'vitalcom' en vez de 'vitalcom_test'. "
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
    return "test_estado_%s" % uuid.uuid4().hex[:8]


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


def _leer(base, relativa):
    with io.open(os.path.join(base, *relativa.split("/")), "rb") as fh:
        return fh.read().decode("utf-8")


def _fixture(base):
    columnas = _columnas_reales()
    os.makedirs(os.path.join(base, "PRODUCTOS"))
    _escribir_csv(os.path.join(base, "PRODUCTOS", "_DIM_PRODUCTOS.csv"), columnas, [
        _fila_producto(columnas, producto_key="PX_NUEVO", slug_carpeta="PX_NUEVO",
                       estado="NUEVO", mercado="GT", costo_q="60"),
        _fila_producto(columnas, producto_key="PX_VIVO", slug_carpeta="PX_VIVO",
                       estado="VIVO", mercado="GT", costo_q="60"),
        _fila_producto(columnas, producto_key="PX_DRY", slug_carpeta="PX_DRY",
                       estado="NUEVO", mercado="GT", costo_q="60"),
        _fila_producto(columnas, producto_key="OTRO", slug_carpeta="OTRO",
                       estado="VIVO", mercado="GT", costo_q="50"),
    ])
    tenant = _tenant_unico()
    cargar_estado.ep.TENANT_ID = tenant
    _bootstrap_producto(os.path.join(base, "PRODUCTOS"), tenant)


def _filas(base):
    contenido = _leer(base, "PRODUCTOS/_DIM_PRODUCTOS.csv")
    filas = list(csv.reader(io.StringIO(contenido, newline="")))
    return filas[0], filas[1:]


def _fila(base, clave):
    encabezado, filas = _filas(base)
    return dict(zip(encabezado, next(f for f in filas if f and f[0] == clave)))


def _correr(base, producto, estado, motivo, *extra):
    return cargar_estado.main(["--producto", producto, "--estado", estado,
                               "--motivo", motivo, "--base", base, *extra])


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
        print("GATE DE LA CARGA DEL ESTADO DEL PRODUCTO")
        print("  SKIP   Postgres/vitalcom_test no disponible en este entorno")
        return 0
    fallas = []
    base = tempfile.mkdtemp(prefix="estado_test_")
    try:
        _fixture(base)

        def rechaza_un_estado_invalido_diciendo_cuales_valen():
            antes = _leer(base, "PRODUCTOS/_DIM_PRODUCTOS.csv")
            codigo, salida = _en_silencio(
                lambda: _correr(base, "PX_NUEVO", "MALO", "prueba", "--json"))
            assert codigo == 1, salida
            detalle = json.loads(salida)["detalle"]
            assert "MALO" in detalle and "NUEVO" in detalle and "VIVO" in detalle \
                and "PAUSADO" in detalle, detalle
            assert _leer(base, "PRODUCTOS/_DIM_PRODUCTOS.csv") == antes

        def nuevo_a_vivo_escribe_y_avisa_el_evento():
            encabezado, filas_antes = _filas(base)
            col_estado = encabezado.index("estado")
            codigo, salida = _en_silencio(
                lambda: _correr(base, "PX_NUEVO", "VIVO", "reingreso", "--json"))
            assert codigo == 0, salida
            resultado = json.loads(salida)
            assert resultado["sin_cambios"] is False and resultado["aplicado"] is True, resultado
            assert _fila(base, "PX_NUEVO")["estado"] == "VIVO"
            assert len(resultado["avisos"]) == 1, resultado
            aviso = resultado["avisos"][0]
            assert "registrar_evento.py" in aviso and "CAMBIO_ESTADO" in aviso, aviso
            assert "--producto PX_NUEVO" in aviso and '--motivo "reingreso"' in aviso, aviso
            assert "--antes NUEVO" in aviso and "--despues VIVO" in aviso, aviso
            encabezado_desp, filas_desp = _filas(base)
            assert encabezado_desp == encabezado
            assert len(filas_desp) == len(filas_antes)
            for antes_f, desp_f in zip(filas_antes, filas_desp):
                if desp_f[0] == "PX_NUEVO":
                    assert desp_f[col_estado] == "VIVO", desp_f
                    assert [c for i, c in enumerate(desp_f) if i != col_estado] == \
                        [c for i, c in enumerate(antes_f) if i != col_estado]
                else:
                    assert desp_f == antes_f, desp_f[0]

        def pedir_el_mismo_estado_es_sin_cambios_y_no_escribe():
            antes = _leer(base, "PRODUCTOS/_DIM_PRODUCTOS.csv")
            codigo, salida = _en_silencio(
                lambda: _correr(base, "PX_VIVO", "VIVO", "da igual", "--json"))
            assert codigo == 0, salida
            resultado = json.loads(salida)
            assert resultado["sin_cambios"] is True and resultado["aplicado"] is False, resultado
            assert _leer(base, "PRODUCTOS/_DIM_PRODUCTOS.csv") == antes

        def dry_run_no_toca_el_disco():
            antes = _leer(base, "PRODUCTOS/_DIM_PRODUCTOS.csv")
            codigo, salida = _en_silencio(
                lambda: _correr(base, "PX_DRY", "VIVO", "prueba", "--dry-run", "--json"))
            assert codigo == 0, salida
            resultado = json.loads(salida)
            assert resultado["sin_cambios"] is False and resultado["aplicado"] is False, resultado
            assert _leer(base, "PRODUCTOS/_DIM_PRODUCTOS.csv") == antes
            assert _fila(base, "PX_DRY")["estado"] == "NUEVO"

        print("GATE DE LA CARGA DEL ESTADO DEL PRODUCTO")
        for nombre, funcion in (
            ("rechaza un estado invalido diciendo cuales valen",
             rechaza_un_estado_invalido_diciendo_cuales_valen),
            ("NUEVO -> VIVO escribe y el aviso trae el comando de evento",
             nuevo_a_vivo_escribe_y_avisa_el_evento),
            ("pedir el mismo estado es sin cambios y no escribe",
             pedir_el_mismo_estado_es_sin_cambios_y_no_escribe),
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
