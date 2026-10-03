#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_cargar_costeo.py — GATE DE LA CARGA DE LAS CIFRAS DE COSTEO.

Congela lo que cargar_costeo.py no puede romper nunca:
  · un producto GT con costo_q escribe las 4 columnas con los valores que da
    costear.costear para ese costo (se comparan llamando a la funcion, no con
    numeros fijos);
  · --costo-pedido distinto de costo_q usa el del flag, no el de la fila;
  · un mercado sin tabla de costeo se rechaza nombrando el mercado;
  · una cifra ya cargada no se pisa sin --reemplazar; con --reemplazar solo
    cambian esas columnas de esa fila, nada mas;
  · --dry-run no toca el disco.

Aislamiento CRÍTICO (mismo patrón que test_cargar_moneda_cuenta.py): fuerza
`PGDATABASE=vitalcom_test` ANTES de conectar, bootstrapea raw.producto/raw.raw_import en su
PROPIO tenant único para esta corrida y nunca toca `vitalcom` real. Se salta con aviso si
`vitalcom_test` no está disponible en este entorno.

USO:  python Ads/_TOOLS/test_cargar_costeo.py     (exit 0 = pasa/salta, 1 = falla)
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
import cargar_costeo  # noqa: E402
import costear  # noqa: E402

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
            "test_cargar_costeo.py intentó conectarse a 'vitalcom' en vez de 'vitalcom_test'. "
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
    return "test_costeo_%s" % uuid.uuid4().hex[:8]


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


def _esperadas(costo, mercado):
    crudo = costear.costear(costo, mercado=mercado)
    return {
        "fila_costeo_q": str(int(round(float(crudo["fila_usada"])))),
        "precio_base_q": str(int(round(float(crudo["precio_1u"])))),
        "cpa_base_q": "%.2f" % float(crudo["cpa_base"]),
        "cpa_be_q": "%.2f" % float(crudo["cpa_break_even"]),
    }


def _fixture(base):
    columnas = _columnas_reales()
    os.makedirs(os.path.join(base, "PRODUCTOS"))
    _escribir_csv(os.path.join(base, "PRODUCTOS", "_DIM_PRODUCTOS.csv"), columnas, [
        _fila_producto(columnas, producto_key="PX_GT", slug_carpeta="PX_GT", estado="NUEVO",
                       costo_q="60", mercado="GT"),
        _fila_producto(columnas, producto_key="PX_FLAG", slug_carpeta="PX_FLAG", estado="NUEVO",
                       costo_q="60", mercado="GT"),
        _fila_producto(columnas, producto_key="PX_SINTABLA", slug_carpeta="PX_SINTABLA",
                       estado="NUEVO", costo_q="60", mercado="MX"),
        _fila_producto(columnas, producto_key="PX_CONCIFRAS", slug_carpeta="PX_CONCIFRAS",
                       estado="NUEVO", costo_q="60", mercado="GT", cpa_be_q="0.01"),
        _fila_producto(columnas, producto_key="PX_DRY", slug_carpeta="PX_DRY", estado="NUEVO",
                       costo_q="60", mercado="GT"),
        _fila_producto(columnas, producto_key="OTRO", slug_carpeta="OTRO", estado="VIVO",
                       costo_q="50", mercado="GT"),
    ])
    _escribir_csv(os.path.join(base, "PRODUCTOS", "_DIM_MERCADOS.csv"),
                  ["mercado", "moneda"],
                  [["GT", "GTQ"],
                   ["CO", "COP"],
                   ["MX", "MXN"]])
    tenant = _tenant_unico()
    cargar_costeo.ep.TENANT_ID = tenant
    _bootstrap_producto(os.path.join(base, "PRODUCTOS"), tenant)


def _filas(base):
    contenido = _leer(base, "PRODUCTOS/_DIM_PRODUCTOS.csv")
    filas = list(csv.reader(io.StringIO(contenido, newline="")))
    return filas[0], filas[1:]


def _fila(base, clave):
    encabezado, filas = _filas(base)
    return dict(zip(encabezado, next(f for f in filas if f and f[0] == clave)))


def _correr(base, producto, *extra):
    return cargar_costeo.main(["--producto", producto, "--base", base, *extra])


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
        print("GATE DE LA CARGA DE LAS CIFRAS DE COSTEO")
        print("  SKIP   Postgres/vitalcom_test no disponible en este entorno")
        return 0
    fallas = []
    base = tempfile.mkdtemp(prefix="costeo_test_")
    try:
        _fixture(base)

        def escribe_las_4_columnas_con_costear():
            codigo, salida = _en_silencio(lambda: _correr(base, "PX_GT", "--json"))
            assert codigo == 0, salida
            fila = _fila(base, "PX_GT")
            esperadas = _esperadas("60", "GT")
            for columna, valor in esperadas.items():
                assert fila[columna] == valor, (columna, fila[columna], valor)

        def costo_pedido_distinto_usa_el_flag():
            codigo, salida = _en_silencio(
                lambda: _correr(base, "PX_FLAG", "--costo-pedido", "90", "--json"))
            assert codigo == 0, salida
            fila = _fila(base, "PX_FLAG")
            esperadas_90 = _esperadas("90", "GT")
            esperadas_60 = _esperadas("60", "GT")
            assert esperadas_90 != esperadas_60, (esperadas_90, esperadas_60)
            for columna, valor in esperadas_90.items():
                assert fila[columna] == valor, (columna, fila[columna], valor)

        def mercado_sin_tabla_rechaza_nombrando_el_mercado():
            antes = _leer(base, "PRODUCTOS/_DIM_PRODUCTOS.csv")
            codigo, salida = _en_silencio(lambda: _correr(base, "PX_SINTABLA", "--json"))
            assert codigo == 1, salida
            detalle = json.loads(salida)["detalle"]
            assert "MX" in detalle and "no hay tabla" in detalle, detalle
            assert _leer(base, "PRODUCTOS/_DIM_PRODUCTOS.csv") == antes

        def sin_reemplazar_no_pisa_cifras_cargadas():
            antes = _leer(base, "PRODUCTOS/_DIM_PRODUCTOS.csv")
            codigo, salida = _en_silencio(lambda: _correr(base, "PX_CONCIFRAS", "--json"))
            assert codigo == 1, salida
            assert "reemplazar" in json.loads(salida)["detalle"], salida
            assert _leer(base, "PRODUCTOS/_DIM_PRODUCTOS.csv") == antes
            assert _fila(base, "PX_CONCIFRAS")["cpa_be_q"] == "0.01"

        def con_reemplazar_solo_cambia_esas_columnas_de_esa_fila():
            encabezado, filas_antes = _filas(base)
            cols = ("fila_costeo_q", "precio_base_q", "cpa_base_q", "cpa_be_q")
            indices = [encabezado.index(c) for c in cols]
            codigo, salida = _en_silencio(
                lambda: _correr(base, "PX_CONCIFRAS", "--reemplazar", "--json"))
            assert codigo == 0, salida
            esperadas = _esperadas("60", "GT")
            fila = _fila(base, "PX_CONCIFRAS")
            for columna, valor in esperadas.items():
                assert fila[columna] == valor, (columna, fila[columna], valor)
            encabezado_desp, filas_desp = _filas(base)
            assert encabezado_desp == encabezado
            assert len(filas_desp) == len(filas_antes)
            for antes_f, desp_f in zip(filas_antes, filas_desp):
                if desp_f[0] == "PX_CONCIFRAS":
                    for i, c in enumerate(desp_f):
                        if i in indices:
                            continue
                        assert c == antes_f[i], (encabezado[i], antes_f[i], c)
                else:
                    assert desp_f == antes_f, desp_f[0]

        def dry_run_no_toca_el_disco():
            antes = _leer(base, "PRODUCTOS/_DIM_PRODUCTOS.csv")
            codigo, salida = _en_silencio(
                lambda: _correr(base, "PX_DRY", "--dry-run", "--json"))
            assert codigo == 0, salida
            resultado = json.loads(salida)
            assert resultado["aplicado"] is False, resultado
            assert _leer(base, "PRODUCTOS/_DIM_PRODUCTOS.csv") == antes
            fila = _fila(base, "PX_DRY")
            assert fila["cpa_be_q"] == "" and fila["precio_base_q"] == "", fila

        print("GATE DE LA CARGA DE LAS CIFRAS DE COSTEO")
        for nombre, funcion in (
            ("escribe las 4 columnas con lo que da costear", escribe_las_4_columnas_con_costear),
            ("--costo-pedido distinto usa el del flag", costo_pedido_distinto_usa_el_flag),
            ("mercado sin tabla rechaza nombrando el mercado",
             mercado_sin_tabla_rechaza_nombrando_el_mercado),
            ("sin --reemplazar no pisa cifras cargadas", sin_reemplazar_no_pisa_cifras_cargadas),
            ("con --reemplazar solo cambia esas columnas de esa fila",
             con_reemplazar_solo_cambia_esas_columnas_de_esa_fila),
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
