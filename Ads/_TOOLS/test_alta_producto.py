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

USO:  python Ads/_TOOLS/test_alta_producto.py     (exit 0 = pasa, 1 = falla)
"""

import csv
import io
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import alta_producto  # noqa: E402

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
    """Una copia minima del sistema: los dos CSV con su encabezado y una imagen."""
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

        def falla_a_mitad_no_deja_producto_a_medias():
            """Si el segundo CSV no se puede escribir, el primero vuelve como estaba."""
            antes = _leer(base, "_DIM_PRODUCTOS.csv")
            original = alta_producto.escribir_csv
            estado = {"llamadas": 0}

            def escribir_que_falla(ruta, encabezado, filas):
                estado["llamadas"] += 1
                if estado["llamadas"] == 2:  # el de _DIM_ENVASE.csv
                    raise OSError("disco lleno (simulado)")
                return original(ruta, encabezado, filas)

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
            assert not os.path.isfile(os.path.join(
                base, "Ads", "MEDIA_PRODUCTOROTO", "PRODUCTO_ROTO_PACKSHOT.png")), \
                "el packshot copiado tiene que borrarse"

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
            ("una falla a mitad no deja restos", falla_a_mitad_no_deja_producto_a_medias),
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
