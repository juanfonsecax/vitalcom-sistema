#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_cargar_packshot.py — GATE DEL PACKSHOT (foto del envase + identidad fisica declarada).

Congela: la foto queda en Ads/{carpeta_media}/{PK}_PACKSHOT.{ext} con la extension del CONTENIDO;
la fila de _DIM_ENVASE.csv se upsertea (las otras filas pasan intactas, sin duplicar);
un packshot distinto ya cargado no se cambia sin --reemplazar y, con la bandera, la foto vieja se
conserva con fecha; la misma foto con los mismos datos no cambia nada; --dry-run no toca nada.
Todo corre sobre directorios temporales.

USO:  python -m pytest Ads/_TOOLS/test_cargar_packshot.py -q
"""

import csv
import io
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cargar_packshot as cp  # noqa: E402

COLUMNAS_PRODUCTOS = ["producto_key", "nombre_display", "slug_carpeta", "carpeta_media"]
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
PNG_OTRA = b"\x89PNG\r\n\x1a\n" + b"\x01" * 64
JPG = b"\xff\xd8\xff\xe0" + b"\x00" * 64
DATOS = ["--marca-impresa", "SERUM PRO", "--color-envase", "azul con blanco",
         "--formato-envase", "frasco de 60 ml con gotero", "--color-hex", "#1B4F9C"]


@pytest.fixture
def base(tmp_path):
    (tmp_path / "PRODUCTOS").mkdir()
    (tmp_path / "Ads" / "MEDIA_SERUM").mkdir(parents=True)
    with io.open(tmp_path / "PRODUCTOS" / "_DIM_PRODUCTOS.csv", "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(COLUMNAS_PRODUCTOS)
        w.writerow(["SERUM", "Serum", "SERUM", "MEDIA_SERUM"])
        w.writerow(["SIN_MEDIA", "Sin media", "SIN_MEDIA", "MEDIA_NO_EXISTE"])
    with io.open(tmp_path / "PRODUCTOS" / "_DIM_ENVASE.csv", "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(cp.COLUMNAS)
        w.writerow(["OTRO", "Ads/MEDIA_OTRO/OTRO_PACKSHOT.jpg", "VERDE", "", "OTRA MARCA", "tubo, 30 g",
                    "2026-09-01", "x", "nota, con coma"])
    return tmp_path


def _correr(base, contenido, *extra, producto="SERUM", datos=DATOS, capsys=None):
    origen = base / "subida.bin"
    origen.write_bytes(contenido)
    codigo = cp.main(["--producto", producto, "--origen", str(origen), "--base", str(base),
                      "--hoy", "2026-09-28", "--json", *datos, *extra])
    return codigo, json.loads(capsys.readouterr().out)


def _filas(base):
    with io.open(base / "PRODUCTOS" / "_DIM_ENVASE.csv", encoding="utf-8", newline="") as fh:
        return {f["producto_key"]: f for f in csv.DictReader(fh)}


def test_guarda_la_foto_y_declara_la_fila(base, capsys):
    codigo, r = _correr(base, PNG, capsys=capsys)
    assert codigo == 0 and r["aplicado"] is True and r["packshot"] == "Ads/MEDIA_SERUM/SERUM_PACKSHOT.png"
    assert (base / "Ads" / "MEDIA_SERUM" / "SERUM_PACKSHOT.png").read_bytes() == PNG
    fila = _filas(base)["SERUM"]
    assert fila["packshot"] == r["packshot"] and fila["marca_impresa"] == "SERUM PRO"
    assert fila["color_envase"] == "azul con blanco" and fila["color_hex"] == "#1B4F9C"
    assert fila["formato_envase"] == "frasco de 60 ml con gotero"
    assert fila["verificado_el"] == "2026-09-28" and fila["fuente"] == cp.FUENTE


def test_las_otras_filas_pasan_intactas_y_no_se_duplica(base, capsys):
    _correr(base, PNG, capsys=capsys)
    _correr(base, PNG, "--reemplazar", datos=[*DATOS[:2], "--color-envase", "rojo", *DATOS[4:]], capsys=capsys)
    filas = _filas(base)
    assert sorted(filas) == ["OTRO", "SERUM"]
    assert filas["OTRO"]["formato_envase"] == "tubo, 30 g" and filas["OTRO"]["notas"] == "nota, con coma"
    assert filas["SERUM"]["color_envase"] == "rojo"


def test_la_extension_sale_del_contenido_no_del_nombre(base, capsys):
    codigo, r = _correr(base, JPG, capsys=capsys)
    assert codigo == 0 and r["packshot"].endswith("SERUM_PACKSHOT.jpg")
    assert (base / "Ads" / "MEDIA_SERUM" / "SERUM_PACKSHOT.jpg").read_bytes() == JPG


def test_lo_mismo_otra_vez_no_cambia_nada(base, capsys):
    _correr(base, PNG, capsys=capsys)
    codigo, r = _correr(base, PNG, capsys=capsys)
    assert codigo == 0 and r["sin_cambios"] is True and r["aplicado"] is False


def test_otra_foto_sin_reemplazar_se_rechaza(base, capsys):
    _correr(base, PNG, capsys=capsys)
    codigo, r = _correr(base, PNG_OTRA, capsys=capsys)
    assert codigo == 1 and "--reemplazar" in r["detalle"]
    assert (base / "Ads" / "MEDIA_SERUM" / "SERUM_PACKSHOT.png").read_bytes() == PNG


def test_reemplazar_conserva_la_foto_vieja_con_fecha(base, capsys):
    _correr(base, PNG, capsys=capsys)
    codigo, r = _correr(base, PNG_OTRA, "--reemplazar", capsys=capsys)
    assert codigo == 0 and r["guardadas"] == ["Ads/MEDIA_SERUM/SERUM_PACKSHOT_ANTERIOR_20260928.png"]
    carpeta = base / "Ads" / "MEDIA_SERUM"
    assert (carpeta / "SERUM_PACKSHOT.png").read_bytes() == PNG_OTRA
    assert (carpeta / "SERUM_PACKSHOT_ANTERIOR_20260928.png").read_bytes() == PNG
    _correr(base, PNG, "--reemplazar", capsys=capsys)
    assert (carpeta / "SERUM_PACKSHOT_ANTERIOR_20260928_2.png").read_bytes() == PNG_OTRA


def test_cambiar_de_extension_tambien_pide_reemplazar(base, capsys):
    _correr(base, PNG, capsys=capsys)
    codigo, r = _correr(base, JPG, capsys=capsys)
    assert codigo == 1 and "--reemplazar" in r["detalle"]
    codigo, r = _correr(base, JPG, "--reemplazar", capsys=capsys)
    assert codigo == 0 and _filas(base)["SERUM"]["packshot"].endswith(".jpg")
    assert not (base / "Ads" / "MEDIA_SERUM" / "SERUM_PACKSHOT.png").exists()


def test_dry_run_no_toca_nada(base, capsys):
    antes = (base / "PRODUCTOS" / "_DIM_ENVASE.csv").read_bytes()
    codigo, r = _correr(base, PNG, "--dry-run", capsys=capsys)
    assert codigo == 0 and r["aplicado"] is False and r["cambios"]
    assert not list((base / "Ads" / "MEDIA_SERUM").iterdir())
    assert (base / "PRODUCTOS" / "_DIM_ENVASE.csv").read_bytes() == antes


@pytest.mark.parametrize("contenido,datos,esperado", [
    (b"", DATOS, "vacia"),
    (b"GIF89a" + b"\x00" * 30, DATOS, "PNG o JPG"),
    (PNG, ["--marca-impresa", " ", "--color-envase", "a", "--formato-envase", "b"], "marca impresa"),
    (PNG, ["--marca-impresa", "M", "--color-envase", "", "--formato-envase", "b"], "color envase"),
    (PNG, ["--marca-impresa", "M", "--color-envase", "a", "--formato-envase", ""], "formato envase"),
    (PNG, [*DATOS[:6], "--color-hex", "azul"], "#RRGGBB"),
])
def test_rechaza_lo_invalido_sin_escribir(base, capsys, contenido, datos, esperado):
    codigo, r = _correr(base, contenido, datos=datos, capsys=capsys)
    assert codigo == 1 and esperado in r["detalle"]
    assert not list((base / "Ads" / "MEDIA_SERUM").iterdir())
    assert "SERUM" not in _filas(base)


def test_producto_inexistente_o_sin_carpeta_de_media(base, capsys):
    codigo, r = _correr(base, PNG, producto="NO_EXISTE", capsys=capsys)
    assert codigo == 1 and "no tiene fila" in r["detalle"]
    codigo, r = _correr(base, PNG, producto="SIN_MEDIA", capsys=capsys)
    assert codigo == 1 and "carpeta de media" in r["detalle"]


def test_si_falla_el_csv_se_devuelve_todo(base, capsys, monkeypatch):
    _correr(base, PNG, capsys=capsys)

    def roto(*a, **k):
        raise OSError("disco lleno")
    monkeypatch.setattr(cp.upsert_fact, "upsert", roto)
    origen = base / "otra.bin"
    origen.write_bytes(PNG_OTRA)
    with pytest.raises(OSError):
        cp.main(["--producto", "SERUM", "--origen", str(origen), "--base", str(base), "--reemplazar",
                 "--hoy", "2026-09-28", "--json", *DATOS, "--notas", "cambio"])
    carpeta = base / "Ads" / "MEDIA_SERUM"
    assert (carpeta / "SERUM_PACKSHOT.png").read_bytes() == PNG
    assert sorted(p.name for p in carpeta.iterdir()) == ["SERUM_PACKSHOT.png"]


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q", "-p", "no:cacheprovider", "--noconftest"]))
