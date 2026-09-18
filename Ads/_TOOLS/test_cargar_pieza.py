#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_cargar_pieza.py — GATE DE LA CARGA DE UNA PIEZA DE ANUNCIO.

Congela lo que cargar_pieza.py no puede romper nunca:
  · solo se carga una pieza que el plan (o _DIM_CREATIVOS.csv) DECLARA, con su nombre exacto:
    el nombre es el que gen_publicacion.py busca en disco y despues en la biblioteca de Meta;
  · el contenido tiene que ser del tipo que dice el nombre (un JPG no se guarda como .png);
  · un nombre con carpeta no escapa de Ads/{carpeta_media}/;
  · una pieza ya cargada no se cambia sin --reemplazar; la misma pieza otra vez no cambia nada;
  · --dry-run no toca nada y los CSV no se tocan nunca.

USO:  python Ads/_TOOLS/test_cargar_pieza.py     (exit 0 = pasa, 1 = falla)
"""

import csv
import io
import json
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cargar_pieza  # noqa: E402

COLUMNAS = ["producto_key", "nombre_display", "slug_carpeta", "estado", "fase", "cuenta_alias", "cuenta_id",
            "page_id", "moneda", "tasa", "costo_q", "fila_costeo_q", "precio_base_q", "cpa_base_q", "cpa_be_q",
            "cpa_be_anterior_q", "notas", "carpeta_videos", "carpeta_transcripciones", "carpeta_media",
            "carpetas_extra", "clave_campana", "campaign_id"]
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
PNG_OTRA = b"\x89PNG\r\n\x1a\n" + b"\x01" * 64
JPG = b"\xff\xd8\xff\xe0" + b"\x00" * 64
MP4 = b"\x00\x00\x00\x18ftypmp42" + b"\x00" * 64


def _fila(**campos):
    base = {c: "" for c in COLUMNAS}
    base.update(campos)
    return [base[c] for c in COLUMNAS]


def _fixture(base):
    os.makedirs(os.path.join(base, "PRODUCTOS", "SERUM"))
    os.makedirs(os.path.join(base, "Ads", "MEDIA_SERUM"))
    with io.open(os.path.join(base, "PRODUCTOS", "_DIM_PRODUCTOS.csv"), "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(COLUMNAS)
        w.writerow(_fila(producto_key="SERUM", slug_carpeta="SERUM", costo_q="60", carpeta_media="MEDIA_SERUM",
                         notas="con, coma"))
        w.writerow(_fila(producto_key="SIN_MEDIA", slug_carpeta="SIN_MEDIA", costo_q="60",
                         carpeta_media="MEDIA_NO_EXISTE"))
    with io.open(os.path.join(base, "PRODUCTOS", "SERUM", "_PLAN.json"), "w", encoding="utf-8") as fh:
        json.dump({"schema": "plan/1", "conjuntos": [
            {"angulo_key": "A", "archivo_creativo": "SERUM_1_A.png"},
            {"angulo_key": "B", "archivo_creativo": "SERUM_2_B.jpg"},
            {"angulo_key": "C", "archivo_creativo": "SERUM_3_C.mp4"},
        ]}, fh)
    with io.open(os.path.join(base, "PRODUCTOS", "_DIM_CREATIVOS.csv"), "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["creativo_id", "producto_key", "archivo"])
        w.writerow(["SERUM_F2_1", "SERUM", "SERUM_F2_1.png"])
        w.writerow(["OTRO_1", "OTRO", "OTRO_1.png"])


def _origen(base, contenido, nombre="subida.bin"):
    ruta = os.path.join(base, "_subidas", nombre)
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with io.open(ruta, "wb") as fh:
        fh.write(contenido)
    return ruta


def _correr(base, producto, archivo, contenido, *extra):
    salida = io.StringIO()
    real, sys.stdout = sys.stdout, salida
    try:
        codigo = cargar_pieza.main(["--producto", producto, "--archivo", archivo,
                                    "--origen", _origen(base, contenido), "--base", base, "--json", *extra])
    finally:
        sys.stdout = real
    return codigo, json.loads(salida.getvalue())


def _media(base, nombre):
    ruta = os.path.join(base, "Ads", "MEDIA_SERUM", nombre)
    if not os.path.isfile(ruta):
        return None
    with io.open(ruta, "rb") as fh:
        return fh.read()


def _csv(base):
    with io.open(os.path.join(base, "PRODUCTOS", "_DIM_PRODUCTOS.csv"), "rb") as fh:
        return fh.read()


def caso(nombre, funcion, fallas):
    try:
        funcion()
        print(f"  OK   {nombre}")
    except AssertionError as error:
        fallas.append(nombre)
        print(f"  FALLA {nombre}: {error}")


def main():
    fallas = []
    base = tempfile.mkdtemp(prefix="pieza_test_")
    try:
        _fixture(base)
        csv_antes = _csv(base)

        def carga_la_pieza_declarada_con_su_nombre():
            codigo, r = _correr(base, "SERUM", "SERUM_1_A.png", PNG)
            assert codigo == 0 and r["aplicado"] is True, r
            assert _media(base, "SERUM_1_A.png") == PNG
            assert r["ruta"] == "Ads/MEDIA_SERUM/SERUM_1_A.png" and r["declarada_en"].endswith("_PLAN.json"), r

        def la_misma_pieza_otra_vez_no_cambia_nada():
            codigo, r = _correr(base, "SERUM", "SERUM_1_A.png", PNG)
            assert codigo == 0 and r["sin_cambios"] is True and r["aplicado"] is False, r

        def no_cambia_una_pieza_cargada_sin_reemplazar():
            codigo, r = _correr(base, "SERUM", "SERUM_1_A.png", PNG_OTRA)
            assert codigo == 1 and "--reemplazar" in r["detalle"], r
            assert _media(base, "SERUM_1_A.png") == PNG

        def reemplaza_con_la_bandera():
            codigo, r = _correr(base, "SERUM", "SERUM_1_A.png", PNG_OTRA, "--reemplazar")
            assert codigo == 0 and r["aplicado"] is True, r
            assert _media(base, "SERUM_1_A.png") == PNG_OTRA

        def acepta_jpg_y_video_y_las_de_dim_creativos():
            assert _correr(base, "SERUM", "SERUM_2_B.jpg", JPG)[0] == 0
            assert _correr(base, "SERUM", "SERUM_3_C.mp4", MP4)[0] == 0
            assert _correr(base, "SERUM", "SERUM_F2_1.png", PNG)[0] == 0

        def rechaza_un_nombre_que_nadie_declara():
            codigo, r = _correr(base, "SERUM", "SERUM_9_Z.png", PNG)
            assert codigo == 1 and "no esta declarada" in r["detalle"], r
            codigo, r = _correr(base, "SERUM", "OTRO_1.png", PNG)
            assert codigo == 1, "una pieza de OTRO producto no es de este"
            assert _media(base, "SERUM_9_Z.png") is None

        def rechaza_un_contenido_de_otro_tipo():
            codigo, r = _correr(base, "SERUM", "SERUM_2_B.jpg", PNG, "--reemplazar")
            assert codigo == 1 and "formato" in r["detalle"], r
            codigo, r = _correr(base, "SERUM", "SERUM_1_A.png", b"no soy una imagen", "--reemplazar")
            assert codigo == 1, r
            assert _media(base, "SERUM_1_A.png") == PNG_OTRA

        def un_nombre_con_carpeta_no_escapa():
            for malo in ("../SERUM_1_A.png", "sub/SERUM_1_A.png", "..\\SERUM_1_A.png"):
                assert _correr(base, "SERUM", malo, PNG)[0] == 1, malo

        def rechaza_vacio_y_producto_sin_carpeta_o_sin_fila():
            assert _correr(base, "SERUM", "SERUM_1_A.png", b"", "--reemplazar")[0] == 1
            assert _correr(base, "SIN_MEDIA", "SERUM_1_A.png", PNG)[0] == 1
            assert _correr(base, "NO_EXISTE", "SERUM_1_A.png", PNG)[0] == 1

        def dry_run_no_toca_nada():
            os.remove(os.path.join(base, "Ads", "MEDIA_SERUM", "SERUM_2_B.jpg"))
            codigo, r = _correr(base, "SERUM", "SERUM_2_B.jpg", JPG, "--dry-run")
            assert codigo == 0 and r["aplicado"] is False and r["sin_cambios"] is False, r
            assert _media(base, "SERUM_2_B.jpg") is None

        def los_csv_no_se_tocan():
            assert _csv(base) == csv_antes

        for f in (carga_la_pieza_declarada_con_su_nombre, la_misma_pieza_otra_vez_no_cambia_nada,
                  no_cambia_una_pieza_cargada_sin_reemplazar, reemplaza_con_la_bandera,
                  acepta_jpg_y_video_y_las_de_dim_creativos, rechaza_un_nombre_que_nadie_declara,
                  rechaza_un_contenido_de_otro_tipo, un_nombre_con_carpeta_no_escapa,
                  rechaza_vacio_y_producto_sin_carpeta_o_sin_fila, dry_run_no_toca_nada, los_csv_no_se_tocan):
            caso(f.__name__, f, fallas)
    finally:
        shutil.rmtree(base, ignore_errors=True)

    print("\n%s" % ("PASA" if not fallas else "FALLA: %d caso(s)" % len(fallas)))
    return 1 if fallas else 0


if __name__ == "__main__":
    sys.exit(main())
