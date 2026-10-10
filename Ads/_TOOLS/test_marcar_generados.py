#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_marcar_generados.py — gate de marcar_generados.py.

Un PNG renderizado a mano y guardado con el nombre canonico de su fila debe mover esa fila de
PENDIENTE_GENERAR a GENERADO; nada mas cambia. Se corre con pytest sobre una base temporal.
"""
import csv
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import marcar_generados as mg  # noqa: E402

COLS_CRE = ["producto_key", "creativo_id", "archivo", "angulo_key", "formato", "estado", "notas"]
COLS_PROD = ["producto_key", "slug_carpeta", "carpeta_media"]
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 16
JPG = b"\xff\xd8\xff\xe0" + b"\x00" * 16


def _csv(ruta, cols, filas, fin="\r\n"):
    with open(ruta, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, lineterminator=fin)
        w.writeheader()
        for f in filas:
            w.writerow({c: f.get(c, "") for c in cols})


def _fila(pk, n, ang="ANG_A", formato="IMAGEN", estado="PENDIENTE_GENERAR", ext="png"):
    return {"producto_key": pk, "creativo_id": f"{pk}_{n}", "archivo": f"{pk}_{n}.{ext}",
            "angulo_key": ang, "formato": formato, "estado": estado, "notas": "x, y"}


@pytest.fixture
def base(tmp_path, monkeypatch):
    (tmp_path / "PRODUCTOS").mkdir()
    (tmp_path / "Ads" / "MEDIA_PX").mkdir(parents=True)
    (tmp_path / "Ads" / "MEDIA_OTRO").mkdir(parents=True)
    _csv(tmp_path / "PRODUCTOS" / "_DIM_PRODUCTOS.csv", COLS_PROD,
         [{"producto_key": "PX", "slug_carpeta": "PX", "carpeta_media": ""},
          {"producto_key": "OTRO", "slug_carpeta": "OTRO", "carpeta_media": "MEDIA_OTRO"}])
    monkeypatch.setattr(mg, "BASE", str(tmp_path))
    return tmp_path


def _estados(base):
    with open(base / "PRODUCTOS" / "_DIM_CREATIVOS.csv", newline="", encoding="utf-8") as fh:
        return {r["creativo_id"]: r["estado"] for r in csv.DictReader(fh)}


def _crear(base, filas):
    _csv(base / "PRODUCTOS" / "_DIM_CREATIVOS.csv", COLS_CRE, filas)


def test_dry_run_no_escribe(base):
    _crear(base, [_fila("PX", 1)])
    (base / "Ads" / "MEDIA_PX" / "PX_1.png").write_bytes(PNG)
    antes = (base / "PRODUCTOS" / "_DIM_CREATIVOS.csv").read_bytes()
    r = mg.marcar("PX", None, escribir=False)
    assert r["promovidos"] == ["PX_1"] and r["escribio"] is False
    assert (base / "PRODUCTOS" / "_DIM_CREATIVOS.csv").read_bytes() == antes


def test_promueve_imagen_con_archivo_valido(base):
    _crear(base, [_fila("PX", 1), _fila("PX", 2, ext="jpg")])
    (base / "Ads" / "MEDIA_PX" / "PX_1.png").write_bytes(PNG)
    (base / "Ads" / "MEDIA_PX" / "PX_2.jpg").write_bytes(JPG)
    r = mg.marcar("PX", None, escribir=True)
    assert sorted(r["promovidos"]) == ["PX_1", "PX_2"] and r["escribio"] is True
    assert _estados(base) == {"PX_1": "GENERADO", "PX_2": "GENERADO"}


def test_solo_cambia_el_estado_y_conserva_formato(base):
    _crear(base, [_fila("PX", 1)])
    (base / "Ads" / "MEDIA_PX" / "PX_1.png").write_bytes(PNG)
    antes = (base / "PRODUCTOS" / "_DIM_CREATIVOS.csv").read_bytes()
    mg.marcar("PX", None, escribir=True)
    despues = (base / "PRODUCTOS" / "_DIM_CREATIVOS.csv").read_bytes()
    assert despues == antes.replace(b"PENDIENTE_GENERAR", b"GENERADO")


def test_archivo_faltante_sigue_pendiente(base):
    _crear(base, [_fila("PX", 1)])
    r = mg.marcar("PX", None, escribir=True)
    assert r["promovidos"] == [] and r["faltan_archivo"] == ["PX_1"]
    assert _estados(base) == {"PX_1": "PENDIENTE_GENERAR"}


def test_video_nunca_se_promueve(base):
    _crear(base, [_fila("PX", 1, formato="VIDEO", ext="mp4")])
    (base / "Ads" / "MEDIA_PX" / "PX_1.mp4").write_bytes(b"\x00" * 64)
    r = mg.marcar("PX", None, escribir=True)
    assert r["promovidos"] == [] and _estados(base) == {"PX_1": "PENDIENTE_GENERAR"}


def test_vacio_o_no_imagen_no_se_promueve(base):
    _crear(base, [_fila("PX", 1), _fila("PX", 2)])
    (base / "Ads" / "MEDIA_PX" / "PX_1.png").write_bytes(b"")
    (base / "Ads" / "MEDIA_PX" / "PX_2.png").write_bytes(b"<html>no soy una imagen</html>")
    r = mg.marcar("PX", None, escribir=True)
    assert r["promovidos"] == [] and sorted(r["faltan_archivo"]) == ["PX_1", "PX_2"]
    assert set(_estados(base).values()) == {"PENDIENTE_GENERAR"}


def test_filtro_por_angulo(base):
    _crear(base, [_fila("PX", 1, ang="ANG_A"), _fila("PX", 2, ang="ANG_B")])
    for n in (1, 2):
        (base / "Ads" / "MEDIA_PX" / f"PX_{n}.png").write_bytes(PNG)
    r = mg.marcar("PX", "ANG_B", escribir=True)
    assert r["promovidos"] == ["PX_2"]
    assert _estados(base) == {"PX_1": "PENDIENTE_GENERAR", "PX_2": "GENERADO"}


def test_otros_productos_intactos_y_ya_generados_se_reportan(base):
    _crear(base, [_fila("PX", 1, estado="GENERADO"), _fila("OTRO", 1)])
    (base / "Ads" / "MEDIA_PX" / "PX_1.png").write_bytes(PNG)
    (base / "Ads" / "MEDIA_OTRO" / "OTRO_1.png").write_bytes(PNG)
    r = mg.marcar("PX", None, escribir=True)
    assert r["ya_generados"] == ["PX_1"] and r["promovidos"] == []
    assert _estados(base) == {"PX_1": "GENERADO", "OTRO_1": "PENDIENTE_GENERAR"}


def test_carpeta_media_declarada(base):
    _crear(base, [_fila("OTRO", 1)])
    (base / "Ads" / "MEDIA_OTRO" / "OTRO_1.png").write_bytes(PNG)
    assert mg.marcar("OTRO", None, escribir=True)["promovidos"] == ["OTRO_1"]


def test_producto_desconocido_sale_con_1(base, capsys):
    _crear(base, [])
    assert mg.main(["NOEXISTE"]) == 1
    assert "NOEXISTE" in capsys.readouterr().err


def test_json_un_solo_objeto(base, capsys):
    _crear(base, [_fila("PX", 1)])
    assert mg.main(["PX", "--json"]) == 0
    d = json.loads(capsys.readouterr().out)
    assert d["faltan_archivo"] == ["PX_1"] and d["escribio"] is False


if __name__ == "__main__":
    # el conftest de la carpeta corre cada test_*.py como script; --noconftest evita la recursion
    sys.exit(pytest.main([os.path.abspath(__file__), "-q", "--noconftest", "-p", "no:cacheprovider"]))
