#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_cargar_imagen_concepto.py — gate de cargar_imagen_concepto.py.

La imagen que el operador renderizo a mano queda con el nombre canonico de SU fila en
Ads/<carpeta_media>/ y esa fila (solo esa) pasa a GENERADO. Un archivo que no es PNG/JPEG, una fila
de video, una ya PUBLICADA o un concepto inexistente se rechazan sin tocar nada. Corre sobre una
base temporal.
"""
import csv
import io
import json
import os
import sys

import pytest
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cargar_imagen_concepto as cic  # noqa: E402
import marcar_generados as mg  # noqa: E402

COLS_CRE = ["producto_key", "creativo_id", "archivo", "angulo_key", "formato", "estado", "notas"]
COLS_PROD = ["producto_key", "slug_carpeta", "carpeta_media"]


def _imagen(formato):
    flujo = io.BytesIO()
    Image.new("RGB", (8, 8), (200, 30, 30)).save(flujo, formato)
    return flujo.getvalue()


PNG = _imagen("PNG")
JPG = _imagen("JPEG")


def _csv(ruta, cols, filas):
    with open(ruta, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, lineterminator="\r\n")
        w.writeheader()
        for f in filas:
            w.writerow({c: f.get(c, "") for c in cols})


def _fila(n, ext="png", formato="IMAGEN", estado="PENDIENTE_GENERAR", pk="PX"):
    return {"producto_key": pk, "creativo_id": f"{pk}_{n}", "archivo": f"{pk}_{n}.{ext}",
            "angulo_key": "ANG_A", "formato": formato, "estado": estado, "notas": "x, y"}


@pytest.fixture
def base(tmp_path, monkeypatch):
    (tmp_path / "PRODUCTOS").mkdir()
    (tmp_path / "Ads" / "MEDIA_PX").mkdir(parents=True)
    _csv(tmp_path / "PRODUCTOS" / "_DIM_PRODUCTOS.csv", COLS_PROD,
         [{"producto_key": "PX", "slug_carpeta": "PX", "carpeta_media": ""}])
    monkeypatch.setattr(mg, "BASE", str(tmp_path))
    return tmp_path


def _crear(base, filas):
    _csv(base / "PRODUCTOS" / "_DIM_CREATIVOS.csv", COLS_CRE, filas)


def _estados(base):
    with open(base / "PRODUCTOS" / "_DIM_CREATIVOS.csv", newline="", encoding="utf-8") as fh:
        return {r["creativo_id"]: r["estado"] for r in csv.DictReader(fh)}


def _correr(base, contenido, creativo="PX_1", capsys=None, extra=()):
    origen = base / "subida.bin"
    origen.write_bytes(contenido)
    codigo = cic.main(["--producto", "PX", "--creativo", creativo, "--origen", str(origen),
                       "--base", str(base), "--json", *extra])
    return codigo, json.loads(capsys.readouterr().out)


def test_guarda_con_el_nombre_de_la_fila_y_marca_solo_esa(base, capsys):
    _crear(base, [_fila(1), _fila(2)])
    codigo, salida = _correr(base, PNG, capsys=capsys)
    assert codigo == 0 and salida["ok"] is True and salida["archivo"] == "PX_1.png"
    assert (base / "Ads" / "MEDIA_PX" / "PX_1.png").read_bytes() == PNG
    assert _estados(base) == {"PX_1": "GENERADO", "PX_2": "PENDIENTE_GENERAR"}
    assert not list((base / "Ads" / "MEDIA_PX").glob("*.tmp"))


def test_jpeg_en_fila_png_se_convierte_al_formato_de_la_fila(base, capsys):
    _crear(base, [_fila(1, ext="png")])
    codigo, salida = _correr(base, JPG, capsys=capsys)
    guardado = (base / "Ads" / "MEDIA_PX" / "PX_1.png").read_bytes()
    assert codigo == 0 and salida["convertida"] is True
    assert guardado.startswith(b"\x89PNG\r\n\x1a\n")


def test_png_en_fila_jpg_se_convierte_a_jpeg(base, capsys):
    _crear(base, [_fila(1, ext="jpg")])
    codigo, salida = _correr(base, PNG, capsys=capsys)
    assert codigo == 0 and salida["convertida"] is True
    assert (base / "Ads" / "MEDIA_PX" / "PX_1.jpg").read_bytes().startswith(b"\xff\xd8\xff")


def test_resubir_reemplaza_el_archivo_y_sigue_generado(base, capsys):
    _crear(base, [_fila(1, estado="GENERADO")])
    (base / "Ads" / "MEDIA_PX" / "PX_1.png").write_bytes(JPG)
    otra = io.BytesIO()
    Image.new("RGB", (8, 8), (0, 0, 255)).save(otra, "PNG")
    codigo, salida = _correr(base, otra.getvalue(), capsys=capsys)
    assert codigo == 0 and salida["reemplazo"] is True
    assert (base / "Ads" / "MEDIA_PX" / "PX_1.png").read_bytes() == otra.getvalue()
    assert _estados(base) == {"PX_1": "GENERADO"}


def test_no_imagen_se_rechaza_sin_tocar_nada(base, capsys):
    _crear(base, [_fila(1)])
    antes = (base / "PRODUCTOS" / "_DIM_CREATIVOS.csv").read_bytes()
    codigo, salida = _correr(base, b"<html>no soy imagen</html>", capsys=capsys)
    assert codigo == 1 and salida["ok"] is False
    assert not (base / "Ads" / "MEDIA_PX" / "PX_1.png").exists()
    assert (base / "PRODUCTOS" / "_DIM_CREATIVOS.csv").read_bytes() == antes


def test_vacio_se_rechaza(base, capsys):
    _crear(base, [_fila(1)])
    codigo, salida = _correr(base, b"", capsys=capsys)
    assert codigo == 1 and not (base / "Ads" / "MEDIA_PX" / "PX_1.png").exists()


def test_fila_de_video_se_rechaza(base, capsys):
    _crear(base, [_fila(1, ext="mp4", formato="VIDEO")])
    codigo, salida = _correr(base, PNG, capsys=capsys)
    assert codigo == 1 and "IMAGEN" in salida["detalle"]
    assert not (base / "Ads" / "MEDIA_PX" / "PX_1.mp4").exists()


def test_publicado_no_se_pisa(base, capsys):
    _crear(base, [_fila(1, estado="PUBLICADO")])
    (base / "Ads" / "MEDIA_PX" / "PX_1.png").write_bytes(JPG)
    codigo, salida = _correr(base, PNG, capsys=capsys)
    assert codigo == 1 and "PUBLICADO" in salida["detalle"]
    assert (base / "Ads" / "MEDIA_PX" / "PX_1.png").read_bytes() == JPG


def test_creativo_inexistente(base, capsys):
    _crear(base, [_fila(1)])
    codigo, salida = _correr(base, PNG, creativo="PX_9", capsys=capsys)
    assert codigo == 1 and "PX_9" in salida["detalle"]


def test_archivo_de_la_fila_no_puede_salir_de_la_carpeta(base, capsys):
    fila = _fila(1)
    fila["archivo"] = "../../afuera.png"
    _crear(base, [fila])
    codigo, _ = _correr(base, PNG, capsys=capsys)
    assert codigo == 1 and not (base / "afuera.png").exists()


def test_dry_run_no_escribe(base, capsys):
    _crear(base, [_fila(1)])
    codigo, salida = _correr(base, PNG, capsys=capsys, extra=("--dry-run",))
    assert codigo == 0 and salida["aplicado"] is False
    assert not (base / "Ads" / "MEDIA_PX" / "PX_1.png").exists()
    assert _estados(base) == {"PX_1": "PENDIENTE_GENERAR"}


if __name__ == "__main__":
    sys.exit(pytest.main([os.path.abspath(__file__), "-q", "--noconftest", "-p", "no:cacheprovider"]))
