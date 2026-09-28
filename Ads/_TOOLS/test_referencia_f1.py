#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_referencia_f1.py — GATE del dueño de _DIM_REFERENCIA_F1.csv (A3, 28-sep-2026).

Congela: la lista de referencias `ligera` permitidas se lee del disco (nunca hardcoded);
--elegir rechaza un producto_key sin fila en _DIM_PRODUCTOS.csv, una referencia que no
existe en el banco, y un motivo vacío; una elección válida escribe/reemplaza UNA fila por
producto_key (upsert, nunca duplica); --ver y --listar nunca escriben. Todo corre sobre
directorios temporales — nunca toca PRODUCTOS/_DIM_REFERENCIA_F1.csv real.

USO:  python -m pytest Ads/_TOOLS/test_referencia_f1.py -q
"""

import csv
import io
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import referencia_f1 as rf  # noqa: E402

REF_A = "ligera__Camila-Recomienda__15_1364693855873597.jpg"
REF_B = "ligera__Camila-Recomienda__25_1019494497528403.jpg"
REF_C = "ligera__Tiendas-KetsalStore__14_1779511049710752.jpg"


@pytest.fixture
def banco(tmp_path):
    """Banco de referencias falso con las 3 imágenes `ligera` + una que NO lo es."""
    d = tmp_path / "C2_BENEFICIOS"
    d.mkdir()
    for nombre in (REF_A, REF_B, REF_C, "otro_concepto__algo__1_999.jpg"):
        (d / nombre).write_bytes(b"fake")
    return str(d)


@pytest.fixture
def dim_productos(tmp_path):
    ruta = tmp_path / "_DIM_PRODUCTOS.csv"
    with io.open(ruta, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["producto_key", "nombre_display"])
        w.writerow(["CLEARSTEM", "ClearStem"])
    return str(ruta)


@pytest.fixture
def csv_path(tmp_path):
    return str(tmp_path / "_DIM_REFERENCIA_F1.csv")


@pytest.fixture
def bkdir(tmp_path):
    return str(tmp_path / "_RESPALDOS" / "backups_csv")


# ─────────────────────────────────────────────────────────────────────────────
# LECTURA — nunca escribe
# ─────────────────────────────────────────────────────────────────────────────

def test_referencias_permitidas_lee_del_disco_no_hardcodea(banco):
    permitidas = rf.referencias_permitidas(banco)
    assert permitidas == sorted([REF_A, REF_B, REF_C])


def test_referencias_permitidas_ignora_otros_conceptos(banco):
    permitidas = rf.referencias_permitidas(banco)
    assert "otro_concepto__algo__1_999.jpg" not in permitidas


def test_referencias_permitidas_banco_inexistente_devuelve_vacio(tmp_path):
    assert rf.referencias_permitidas(str(tmp_path / "no_existe")) == []


def test_leer_csv_archivo_inexistente_devuelve_vacio(csv_path):
    assert rf.leer_csv(csv_path) == []


def test_fila_de_sin_eleccion_devuelve_none(csv_path):
    assert rf.fila_de("CLEARSTEM", csv_path) is None


# ─────────────────────────────────────────────────────────────────────────────
# --elegir — validaciones que rechazan sin escribir
# ─────────────────────────────────────────────────────────────────────────────

def test_elegir_rechaza_producto_sin_fila_en_dim_productos(csv_path, dim_productos, banco, bkdir):
    with pytest.raises(rf.Rechazo, match="DIM_PRODUCTOS"):
        rf.elegir("NO_EXISTE", REF_A, "motivo", path=csv_path,
                  dim_productos_path=dim_productos, banco_dir=banco, bkdir=bkdir)
    assert not os.path.exists(csv_path)


def test_elegir_rechaza_referencia_que_no_existe_en_el_banco(csv_path, dim_productos, banco, bkdir):
    with pytest.raises(rf.Rechazo, match="ligera"):
        rf.elegir("CLEARSTEM", "ligera__fantasma__1_000.jpg", "motivo", path=csv_path,
                  dim_productos_path=dim_productos, banco_dir=banco, bkdir=bkdir)
    assert not os.path.exists(csv_path)


def test_elegir_rechaza_referencia_de_otro_concepto(csv_path, dim_productos, banco, bkdir):
    with pytest.raises(rf.Rechazo, match="ligera"):
        rf.elegir("CLEARSTEM", "otro_concepto__algo__1_999.jpg", "motivo", path=csv_path,
                  dim_productos_path=dim_productos, banco_dir=banco, bkdir=bkdir)


def test_elegir_rechaza_motivo_vacio(csv_path, dim_productos, banco, bkdir):
    with pytest.raises(rf.Rechazo, match="motivo"):
        rf.elegir("CLEARSTEM", REF_A, "", path=csv_path,
                  dim_productos_path=dim_productos, banco_dir=banco, bkdir=bkdir)
    assert not os.path.exists(csv_path)


# ─────────────────────────────────────────────────────────────────────────────
# --elegir — escritura real (upsert)
# ─────────────────────────────────────────────────────────────────────────────

def test_elegir_valido_escribe_una_fila(csv_path, dim_productos, banco, bkdir):
    fila = rf.elegir("CLEARSTEM", REF_A, "avatar mujer 25-40, dolor de piel", path=csv_path,
                      dim_productos_path=dim_productos, banco_dir=banco, bkdir=bkdir,
                      hoy="2026-09-28")
    assert fila == {
        "producto_key": "CLEARSTEM", "referencia": REF_A,
        "motivo": "avatar mujer 25-40, dolor de piel", "elegido_el": "2026-09-28",
    }
    filas = rf.leer_csv(csv_path)
    assert len(filas) == 1
    assert filas[0]["referencia"] == REF_A


def test_elegir_dos_veces_reemplaza_no_duplica(csv_path, dim_productos, banco, bkdir):
    rf.elegir("CLEARSTEM", REF_A, "primera razon", path=csv_path,
              dim_productos_path=dim_productos, banco_dir=banco, bkdir=bkdir, hoy="2026-09-28")
    rf.elegir("CLEARSTEM", REF_B, "segunda razon, mejor calce", path=csv_path,
              dim_productos_path=dim_productos, banco_dir=banco, bkdir=bkdir, hoy="2026-09-29")
    filas = rf.leer_csv(csv_path)
    assert len(filas) == 1
    assert filas[0]["referencia"] == REF_B
    assert filas[0]["elegido_el"] == "2026-09-29"


def test_elegir_dos_productos_distintos_conviven(csv_path, dim_productos, banco, bkdir):
    with io.open(dim_productos, "a", newline="", encoding="utf-8") as fh:
        csv.writer(fh).writerow(["TINNIDROP", "Tinnidrop"])
    rf.elegir("CLEARSTEM", REF_A, "motivo A", path=csv_path,
              dim_productos_path=dim_productos, banco_dir=banco, bkdir=bkdir, hoy="2026-09-28")
    rf.elegir("TINNIDROP", REF_C, "motivo C", path=csv_path,
              dim_productos_path=dim_productos, banco_dir=banco, bkdir=bkdir, hoy="2026-09-28")
    filas = rf.leer_csv(csv_path)
    assert len(filas) == 2
    assert rf.fila_de("CLEARSTEM", csv_path)["referencia"] == REF_A
    assert rf.fila_de("TINNIDROP", csv_path)["referencia"] == REF_C


def test_elegir_hace_backup_antes_de_reescribir(csv_path, dim_productos, banco, bkdir):
    rf.elegir("CLEARSTEM", REF_A, "motivo", path=csv_path,
              dim_productos_path=dim_productos, banco_dir=banco, bkdir=bkdir, hoy="2026-09-28")
    rf.elegir("CLEARSTEM", REF_B, "motivo nuevo", path=csv_path,
              dim_productos_path=dim_productos, banco_dir=banco, bkdir=bkdir, hoy="2026-09-29")
    assert os.path.isdir(bkdir)
    assert len(os.listdir(bkdir)) >= 1


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def test_cli_listar_exit_0(banco, monkeypatch):
    monkeypatch.setattr(rf, "BANCO_DIR", banco)
    assert rf.main(["--listar"]) == 0


def test_cli_ver_sin_eleccion_no_falla(tmp_path, monkeypatch):
    monkeypatch.setattr(rf, "CSV_PATH", str(tmp_path / "_DIM_REFERENCIA_F1.csv"))
    assert rf.main(["--ver", "CLEARSTEM"]) == 0


def test_cli_elegir_referencia_invalida_exit_1(tmp_path, banco, dim_productos, monkeypatch):
    monkeypatch.setattr(rf, "CSV_PATH", str(tmp_path / "_DIM_REFERENCIA_F1.csv"))
    monkeypatch.setattr(rf, "BANCO_DIR", banco)
    monkeypatch.setattr(rf, "DIM_PRODUCTOS_PATH", dim_productos)
    assert rf.main(["--elegir", "CLEARSTEM", "ligera__fantasma.jpg", "--motivo", "x"]) == 1
