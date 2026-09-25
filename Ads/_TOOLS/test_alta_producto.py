#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_alta_producto.py — GATE DEL ALTA DE PRODUCTOS.

Congela lo que el alta no puede romper nunca:
  · una clave duplicada se rechaza (invariante 8: un producto = una fila = una carpeta);
  · el CSV queda con el MISMO numero de columnas que su encabezado (invariante 11: el bug
    de NUSAVA del 31-jul dejo una fila de 20 campos en un CSV de 17 y nadie lo vio);
  · el packshot queda DECLARADO en _DIM_ENVASE.csv y el archivo existe en el disco
    (07-sep-2026: sin declararlo, el generador eligio un anuncio verde de otra marca);
  · el alta NO escribe precio, CPA ni break-even: esos los produce costear.py y los guarda
    etapa-guardar-producto;
  · --dry-run no toca nada;
  · si algo falla a mitad, no queda medio producto escrito.

P3 T4 (continuación parte 2) — `alta_producto.aplicar()` escribe la fila del producto por
Postgres (db/escribir.py): la VERDAD de _DIM_PRODUCTOS.csv pasa a raw.producto/core.producto.
Aislamiento CRÍTICO (mismo patrón que test_registrar_evento.py): fuerza `PGDATABASE=vitalcom_test`
ANTES de conectar, bootstrapea raw.producto/raw.raw_import en su PROPIO tenant único para esta
corrida y nunca toca `vitalcom` real. Se salta con aviso si `vitalcom_test` no está disponible en
este entorno (defecto de entorno documentado en db/README.md: rol sin CREATEDB).

USO:  python Ads/_TOOLS/test_alta_producto.py     (exit 0 = pasa/salta, 1 = falla)
"""

import csv
import io
import os
import shutil
import sys
import tempfile
import uuid

# Aislamiento CRÍTICO: forzar vitalcom_test ANTES de conectar -- nunca debe conectar a `vitalcom`
# real durante estas pruebas.
os.environ["PGDATABASE"] = "vitalcom_test"

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import alta_producto  # noqa: E402

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
            "test_alta_producto.py intentó conectarse a 'vitalcom' en vez de 'vitalcom_test'. "
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
    return "test_alta_%s" % uuid.uuid4().hex[:8]


def _bootstrap_producto(prod_dir, tenant):
    """Carga el _DIM_PRODUCTOS.csv YA escrito por el fixture en raw.producto, bajo `tenant`, y
    deja el registro en raw.raw_import -- para que verificar_csv_sincronizado() no aborte por
    "nunca se importó" en la primera escritura real de la prueba. Mismo patrón que
    test_registrar_evento.py::_bootstrap_evento()."""
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
]
COLUMNAS_ENVASE = [
    "producto_key", "packshot", "color_envase", "color_hex", "marca_impresa",
    "formato_envase", "verificado_el", "fuente", "notas",
]
DESCRIPCION = (
    "Serum facial con vitamina C al 20% y acido hialuronico, frasco de 30 ml con gotero. "
    "Uso: 3 gotas por la noche sobre rostro limpio. Registro sanitario MSPAS en tramite. "
    "Proveedor local con entrega en 48 horas y garantia de 30 dias contra defectos."
)


def _fixture(carpeta):
    """Una copia minima del sistema: los dos CSV con su encabezado y una imagen. Bootstrapea
    raw.producto (P3 T4 continuación parte 2) en un tenant único para esta corrida y apunta
    alta_producto.TENANT_ID ahí -- nunca toca `vitalcom` real."""
    os.makedirs(os.path.join(carpeta, "PRODUCTOS"))
    os.makedirs(os.path.join(carpeta, "Ads"))
    for nombre, columnas, filas in (
        ("_DIM_PRODUCTOS.csv", COLUMNAS_PRODUCTOS, [["TINNIDROP"] + [""] * (len(COLUMNAS_PRODUCTOS) - 1)]),
        ("_DIM_ENVASE.csv", COLUMNAS_ENVASE, []),
    ):
        with io.open(os.path.join(carpeta, "PRODUCTOS", nombre), "w", encoding="utf-8", newline="") as fh:
            escritor = csv.writer(fh)
            escritor.writerow(columnas)
            escritor.writerows(filas)
    imagen = os.path.join(carpeta, "foto.png")
    with io.open(imagen, "wb") as fh:
        fh.write(b"\x89PNG\r\n\x1a\n" + b"0" * 64)
    descripcion = os.path.join(carpeta, "desc.txt")
    with io.open(descripcion, "w", encoding="utf-8") as fh:
        fh.write(DESCRIPCION)
    tenant = _tenant_unico()
    alta_producto.TENANT_ID = tenant
    _bootstrap_producto(os.path.join(carpeta, "PRODUCTOS"), tenant)
    return imagen, descripcion


def _correr(base, imagen, descripcion, extra=()):
    return alta_producto.main([
        "--nombre", "Serum Vitamina C", "--costo", "60",
        "--descripcion-archivo", descripcion, "--imagen", imagen,
        "--base", base, "--hoy", "2026-09-17", *extra,
    ])


def _leer(base, nombre):
    with io.open(os.path.join(base, "PRODUCTOS", nombre), encoding="utf-8", newline="") as fh:
        return list(csv.reader(fh))


def caso(nombre, funcion, fallas):
    try:
        funcion()
        print(f"  OK   {nombre}")
    except AssertionError as error:
        fallas.append(nombre)
        print(f"  FALLA {nombre}: {error}")


def main():
    if not DB_DISPONIBLE:
        print("GATE DEL ALTA DE PRODUCTOS")
        print("  SKIP   Postgres/vitalcom_test no disponible en este entorno")
        return 0
    fallas = []
    base = tempfile.mkdtemp(prefix="alta_test_")
    try:
        imagen, descripcion = _fixture(base)

        def alta_normal():
            assert _correr(base, imagen, descripcion) == 0, "el alta valida tiene que salir 0"
            filas = _leer(base, "_DIM_PRODUCTOS.csv")
            encabezado, nueva = filas[0], filas[-1]
            assert len(nueva) == len(encabezado), (
                f"la fila tiene {len(nueva)} campos y el encabezado {len(encabezado)}")
            fila = dict(zip(encabezado, nueva))
            assert fila["producto_key"] == "SERUM_VITAMINA_C", fila["producto_key"]
            assert fila["estado"] == "NUEVO", fila["estado"]
            assert fila["costo_q"] == "60", fila["costo_q"]
            assert fila["carpeta_media"] == "MEDIA_SERUMVITAMINAC", fila["carpeta_media"]

        def no_escribe_cifras_de_costeo():
            fila = dict(zip(*[_leer(base, "_DIM_PRODUCTOS.csv")[i] for i in (0, -1)]))
            for columna in ("precio_base_q", "cpa_base_q", "cpa_be_q", "fila_costeo_q"):
                assert fila[columna] == "", (
                    f"{columna} lo calcula costear.py y lo escribe etapa-guardar-producto, "
                    f"no el alta; llego «{fila[columna]}»")

        def la_fase_no_se_declara():
            fila = dict(zip(*[_leer(base, "_DIM_PRODUCTOS.csv")[i] for i in (0, -1)]))
            assert fila["fase"] == "", "la fase se deriva de la data (flujo.py), no se escribe"

        def packshot_declarado_y_en_disco():
            filas = _leer(base, "_DIM_ENVASE.csv")
            fila = dict(zip(filas[0], filas[-1]))
            assert fila["producto_key"] == "SERUM_VITAMINA_C"
            esperado = "Ads/MEDIA_SERUMVITAMINAC/SERUM_VITAMINA_C_PACKSHOT.png"
            assert fila["packshot"] == esperado, fila["packshot"]
            assert os.path.isfile(os.path.join(base, esperado.replace("/", os.sep))), \
                "el packshot declarado tiene que existir en el disco"

        def guarda_la_descripcion():
            ruta = os.path.join(base, "PRODUCTOS", "SERUM_VITAMINA_C", "2_DATA_PRODUCTO.txt")
            assert os.path.isfile(ruta), "falta 2_DATA_PRODUCTO.txt"
            texto = io.open(ruta, encoding="utf-8").read()
            assert DESCRIPCION[:60] in texto, "la descripcion del operador tiene que quedar guardada"

        def rechaza_duplicado():
            assert _correr(base, imagen, descripcion) == 1, "una clave repetida se rechaza"
            claves = [f[0] for f in _leer(base, "_DIM_PRODUCTOS.csv")[1:]]
            assert claves.count("SERUM_VITAMINA_C") == 1, "no puede quedar duplicada"

        def rechaza_descripcion_corta():
            corta = os.path.join(base, "corta.txt")
            io.open(corta, "w", encoding="utf-8").write("sirve para la piel")
            antes = len(_leer(base, "_DIM_PRODUCTOS.csv"))
            assert alta_producto.main([
                "--nombre", "Otro Producto", "--costo", "60", "--descripcion-archivo", corta,
                "--imagen", imagen, "--base", base]) == 1
            assert len(_leer(base, "_DIM_PRODUCTOS.csv")) == antes, "no se escribe nada al rechazar"

        def rechaza_imagen_inexistente():
            assert alta_producto.main([
                "--nombre", "Otro Producto", "--costo", "60", "--descripcion-archivo", descripcion,
                "--imagen", os.path.join(base, "no_existe.png"), "--base", base]) == 1

        def rechaza_costo_no_numerico():
            assert alta_producto.main([
                "--nombre", "Otro Producto", "--costo", "sesenta", "--descripcion-archivo",
                descripcion, "--imagen", imagen, "--base", base]) == 1

        def dry_run_no_toca_nada():
            antes_productos = _leer(base, "_DIM_PRODUCTOS.csv")
            antes_envase = _leer(base, "_DIM_ENVASE.csv")
            assert alta_producto.main([
                "--nombre", "Producto En Seco", "--costo", "45", "--descripcion-archivo",
                descripcion, "--imagen", imagen, "--base", base, "--dry-run"]) == 0
            assert _leer(base, "_DIM_PRODUCTOS.csv") == antes_productos
            assert _leer(base, "_DIM_ENVASE.csv") == antes_envase
            assert not os.path.isdir(os.path.join(base, "PRODUCTOS", "PRODUCTO_EN_SECO"))

        def la_clave_se_deriva_sin_acentos():
            assert alta_producto.clave_desde_nombre("Óvulos Purity Hernatura") == \
                "OVULOS_PURITY_HERNATURA"
            assert alta_producto.clave_desde_nombre("Té Chino  del  Dr. Ming") == \
                "TE_CHINO_DEL_DR_MING"

        def falla_antes_de_postgres_no_deja_producto_a_medias():
            """P3 T4 continuación parte 2: si un artefacto de disco (acá, _DIM_ENVASE.csv) no se
            puede STAGEAR (fase 1, antes de tocar Postgres), la base nunca se toca: no queda ni
            la fila en raw.producto ni ningún .tmp."""
            antes = _leer(base, "_DIM_PRODUCTOS.csv")
            original = alta_producto.escribir_csv

            def escribir_que_falla(ruta, encabezado, filas):
                raise OSError("disco lleno (simulado)")

            alta_producto.escribir_csv = escribir_que_falla
            try:
                plan = alta_producto.planear(base, {
                    "nombre": "Producto Roto", "clave": "PRODUCTO_ROTO", "costo": "60",
                    "descripcion": DESCRIPCION, "imagen": imagen, "cuenta": "", "moneda": "GTQ",
                    "tasa": "", "color_envase": "", "color_hex": "", "marca": "", "formato": "",
                    "notas": "", "hoy": "2026-09-17"})
                try:
                    alta_producto.aplicar(base, plan)
                    raise AssertionError("tenia que fallar")
                except OSError:
                    pass
            finally:
                alta_producto.escribir_csv = original
            assert _leer(base, "_DIM_PRODUCTOS.csv") == antes, \
                "_DIM_PRODUCTOS.csv tiene que volver a como estaba"
            carpeta_media = os.path.join(base, "Ads", "MEDIA_PRODUCTOROTO")
            assert not os.path.isfile(os.path.join(carpeta_media, "PRODUCTO_ROTO_PACKSHOT.png")), \
                "el packshot copiado tiene que borrarse"
            if os.path.isdir(carpeta_media):
                assert not any(n.endswith(".tmp") for n in os.listdir(carpeta_media)), \
                    "no puede quedar un .tmp"
            con = _conectar_seguro()
            try:
                with con.cursor() as cur:
                    cur.execute(
                        "SELECT count(*) FROM raw.producto WHERE tenant_id=%s AND producto_key=%s",
                        (alta_producto.TENANT_ID, "PRODUCTO_ROTO"))
                    assert cur.fetchone()[0] == 0, "Postgres nunca se tenia que tocar"
            finally:
                con.close()

        def falla_despues_de_postgres_es_recuperable():
            """P3 T4 continuación parte 2: si Postgres YA comiteó la fila y el os.replace() final
            falla, el alta NO se deshace (la verdad ya vive en raw.producto): sale con exit 1 y un
            mensaje de RECUPERACIÓN explícito, dejando el .tmp para terminar a mano."""
            import json as _json
            original = alta_producto.os.replace

            def replace_que_falla_para_los_tmp_del_alta(origen, destino):
                # Filtra por el sufijo ".tmp" propio de este módulo (nunca el ".tmp-escribir" de
                # db/escribir.py, que corre ANTES, dentro del commit): solo intercepta el
                # os.replace() de la fase 3 (posterior al commit), nunca el mirror interno.
                if str(origen).endswith(".tmp"):
                    raise OSError("disco lleno (simulado)")
                return original(origen, destino)

            alta_producto.os.replace = replace_que_falla_para_los_tmp_del_alta
            salida = io.StringIO()
            real_stdout, sys.stdout = sys.stdout, salida
            try:
                codigo = alta_producto.main([
                    "--nombre", "Producto Recuperable", "--costo", "60",
                    "--descripcion-archivo", descripcion, "--imagen", imagen,
                    "--base", base, "--hoy", "2026-09-17", "--json"])
            finally:
                sys.stdout = real_stdout
                alta_producto.os.replace = original
            assert codigo == 1, salida.getvalue()
            detalle = _json.loads(salida.getvalue())["detalle"]
            assert "ya quedó de alta en Postgres" in detalle, detalle
            con = _conectar_seguro()
            try:
                with con.cursor() as cur:
                    cur.execute(
                        "SELECT count(*) FROM raw.producto WHERE tenant_id=%s AND producto_key=%s",
                        (alta_producto.TENANT_ID, "PRODUCTO_RECUPERABLE"))
                    assert cur.fetchone()[0] == 1, "Postgres SI tenia que quedar con la fila"
            finally:
                con.close()
            tmp_restantes = [os.path.join(r, n) for r, _, fs in os.walk(base) for n in fs
                              if n.endswith(".tmp")]
            assert tmp_restantes, "tiene que quedar al menos un .tmp para terminar a mano"
            for ruta_tmp in tmp_restantes:
                os.remove(ruta_tmp)  # limpieza de la corrida (la recuperación real seria renombrar)

        print("GATE DEL ALTA DE PRODUCTOS")
        for nombre, funcion in (
            ("alta valida escribe la fila completa", alta_normal),
            ("no escribe precio, CPA ni break-even", no_escribe_cifras_de_costeo),
            ("no declara la fase", la_fase_no_se_declara),
            ("declara el packshot y lo copia", packshot_declarado_y_en_disco),
            ("guarda la descripcion del operador", guarda_la_descripcion),
            ("rechaza la clave duplicada", rechaza_duplicado),
            ("rechaza una descripcion pobre", rechaza_descripcion_corta),
            ("rechaza una imagen que no existe", rechaza_imagen_inexistente),
            ("rechaza un costo que no es numero", rechaza_costo_no_numerico),
            ("--dry-run no toca el disco", dry_run_no_toca_nada),
            ("la clave se deriva sin acentos", la_clave_se_deriva_sin_acentos),
            ("una falla ANTES de Postgres no deja restos", falla_antes_de_postgres_no_deja_producto_a_medias),
            ("una falla DESPUES de Postgres es recuperable, no se deshace", falla_despues_de_postgres_es_recuperable),
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
