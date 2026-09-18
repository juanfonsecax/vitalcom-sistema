#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_cargar_transcripcion.py — GATE DE LA CARGA DE UNA TRANSCRIPCION TXT.

Congela lo que cargar_transcripcion.py no puede romper nunca:
  · el TXT va a Ads/1.2 Transcripcion videos/{carpeta_transcripciones}/ con el siguiente numero
    libre («N. titulo.txt»), que es lo que cuenta el predicado de F1.congelar_inputs;
  · el contenido se guarda byte a byte (acentos incluidos);
  · el mismo TXT no se guarda dos veces (contaria doble para el minimo de 6);
  · lo que no es texto UTF-8, esta vacio o es enorme se rechaza; un titulo no escapa de la carpeta;
  · --dry-run no toca nada y el CSV de productos no se toca.

USO:  python Ads/_TOOLS/test_cargar_transcripcion.py     (exit 0 = pasa, 1 = falla)
"""

import csv
import io
import json
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cargar_transcripcion  # noqa: E402

COLUMNAS = ["producto_key", "slug_carpeta", "costo_q", "carpeta_transcripciones", "carpeta_media", "notas"]
CARPETA = ("Ads", "1.2 Transcripcion videos", "SERUM_TXT")


def _fixture(base):
    os.makedirs(os.path.join(base, "PRODUCTOS"))
    with io.open(os.path.join(base, "PRODUCTOS", "_DIM_PRODUCTOS.csv"), "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(COLUMNAS)
        w.writerow(["SERUM", "SERUM", "60", "SERUM_TXT", "MEDIA_SERUM", "una, con coma"])


def _correr(base, contenido, *extra):
    origen = os.path.join(base, "_subida.txt")
    with io.open(origen, "wb") as fh:
        fh.write(contenido)
    salida = io.StringIO()
    real, sys.stdout = sys.stdout, salida
    try:
        codigo = cargar_transcripcion.main(["--producto", "SERUM", "--origen", origen, "--base", base, "--json", *extra])
    finally:
        sys.stdout = real
    return codigo, json.loads(salida.getvalue())


def _archivos(base):
    carpeta = os.path.join(base, *CARPETA)
    return sorted(os.listdir(carpeta)) if os.path.isdir(carpeta) else []


def caso(nombre, funcion, fallas):
    try:
        funcion()
        print(f"  OK   {nombre}")
    except AssertionError as error:
        fallas.append(nombre)
        print(f"  FALLA {nombre}: {error}")


def main():
    fallas = []
    base = tempfile.mkdtemp(prefix="txt_test_")
    try:
        _fixture(base)
        with io.open(os.path.join(base, "PRODUCTOS", "_DIM_PRODUCTOS.csv"), "rb") as fh:
            csv_antes = fh.read()
        uno = "Mirá, te cuento lo de mi mamá: le dolían las rodillas.\r\n".encode("utf-8")

        def crea_la_carpeta_y_numera_desde_uno():
            codigo, r = _correr(base, uno, "--titulo", "Rodillas mamá")
            assert codigo == 0 and r["aplicado"] is True, r
            assert _archivos(base) == ["1. Rodillas mamá.txt"], _archivos(base)
            with io.open(os.path.join(base, *CARPETA, "1. Rodillas mamá.txt"), "rb") as fh:
                assert fh.read() == uno, "el contenido va byte a byte"

        def el_mismo_texto_no_se_guarda_dos_veces():
            codigo, r = _correr(base, uno, "--titulo", "otra vez")
            assert codigo == 0 and r["sin_cambios"] is True and r["avisos"], r
            assert len(_archivos(base)) == 1

        def sigue_el_numero_mas_alto():
            with io.open(os.path.join(base, *CARPETA, "7. Ya estaba.txt"), "wb") as fh:
                fh.write(b"otro video")
            codigo, r = _correr(base, "tercero".encode("utf-8"))
            assert codigo == 0 and r["archivo"].endswith("/8. transcripcion.txt"), r
            assert r["total_en_carpeta"] == 3, r

        def rechaza_lo_que_no_es_texto_utf8_o_esta_vacio():
            assert _correr(base, b"\xff\xfe\x00d\x00a")[0] == 1
            assert _correr(base, b"   \r\n ")[0] == 1
            assert _correr(base, b"x" * (1024 * 1024 + 1))[0] == 1

        def un_titulo_no_escapa_de_la_carpeta():
            for malo in ("../fuera", "sub/dir", "a" * 81, ".oculto", "con:dos"):
                assert _correr(base, "nuevo".encode("utf-8"), "--titulo", malo)[0] == 1, malo

        def dry_run_no_toca_nada():
            antes = _archivos(base)
            codigo, r = _correr(base, "cuarto".encode("utf-8"), "--dry-run")
            assert codigo == 0 and r["aplicado"] is False, r
            assert _archivos(base) == antes

        def el_csv_no_se_toca():
            with io.open(os.path.join(base, "PRODUCTOS", "_DIM_PRODUCTOS.csv"), "rb") as fh:
                assert fh.read() == csv_antes

        for f in (crea_la_carpeta_y_numera_desde_uno, el_mismo_texto_no_se_guarda_dos_veces,
                  sigue_el_numero_mas_alto, rechaza_lo_que_no_es_texto_utf8_o_esta_vacio,
                  un_titulo_no_escapa_de_la_carpeta, dry_run_no_toca_nada, el_csv_no_se_toca):
            caso(f.__name__, f, fallas)
    finally:
        shutil.rmtree(base, ignore_errors=True)

    print("\n%s" % ("PASA" if not fallas else "FALLA: %d caso(s)" % len(fallas)))
    return 1 if fallas else 0


if __name__ == "__main__":
    sys.exit(main())
