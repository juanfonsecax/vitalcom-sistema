#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_verificar_activacion.py — Pruebas unitarias de verificar_activacion.py.

Verifica:
  · Campaña en Meta con status ACTIVE -> verificación exitosa (exit 0).
  · Campaña en Meta con status PAUSED u otro -> falla (exit 1).
  · Campaña no presente en snapshot -> falla (exit 1).
  · Producto sin campaign_id -> falla (exit 1).
  · Snapshot no existe -> falla (exit 1).

USO:  python Ads/_TOOLS/test_verificar_activacion.py     (exit 0 = pasa, 1 = falla)
"""
import csv
import io
import json
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import verificar_activacion as va  # noqa: E402


class EntornoPrueba:
    def __init__(self):
        self.tmp = tempfile.mkdtemp(prefix="test_va_")
        self.prod_dir = os.path.join(self.tmp, "PRODUCTOS")
        os.makedirs(self.prod_dir, exist_ok=True)
        self.orig_base = va.BASE

    def __enter__(self):
        va.BASE = self.tmp
        return self

    def __exit__(self, *exc):
        va.BASE = self.orig_base
        shutil.rmtree(self.tmp, ignore_errors=True)

    def escribir_productos(self, filas):
        cols = ["producto_key", "cuenta_alias", "campaign_id"]
        ruta = os.path.join(self.prod_dir, "_DIM_PRODUCTOS.csv")
        with io.open(ruta, "w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=cols)
            w.writeheader()
            for f in filas:
                w.writerow(f)

    def escribir_snapshot(self, entidades):
        ruta = os.path.join(self.tmp, "snapshot.json")
        with io.open(ruta, "w", encoding="utf-8") as fh:
            json.dump({"ad_entities": entidades}, fh)
        return ruta


def test_campana_active_pasa_con_exito():
    with EntornoPrueba() as env:
        env.escribir_productos([{"producto_key": "PROD_OK", "cuenta_alias": "GTR7", "campaign_id": "camp_200"}])
        snap = env.escribir_snapshot([{"id": "camp_200", "name": "GTR7_PROD_OK_F1", "nivel": "campaign", "status": "ACTIVE"}])
        sys.argv = ["verificar_activacion.py", "--producto", "PROD_OK", "--fase", "1", "--snapshot", snap]
        ret = va.main()
        assert ret == 0, f"Retorno inesperado: {ret}"
        print("  OK     campaña ACTIVE en Meta pasa con exit 0")


def test_campana_paused_falla():
    with EntornoPrueba() as env:
        env.escribir_productos([{"producto_key": "PROD_PAUSE", "cuenta_alias": "GTR7", "campaign_id": "camp_201"}])
        snap = env.escribir_snapshot([{"id": "camp_201", "name": "GTR7_PROD_PAUSE_F1", "nivel": "campaign", "status": "PAUSED"}])
        sys.argv = ["verificar_activacion.py", "--producto", "PROD_PAUSE", "--fase", "1", "--snapshot", snap]
        ret = va.main()
        assert ret == 1, f"Retorno inesperado: {ret}"
        print("  OK     campaña PAUSED en Meta falla con exit 1")


def test_campana_no_encontrada_en_snapshot_falla():
    with EntornoPrueba() as env:
        env.escribir_productos([{"producto_key": "PROD_LOST", "cuenta_alias": "GTR7", "campaign_id": "camp_999"}])
        snap = env.escribir_snapshot([{"id": "camp_otra", "name": "OTRA", "nivel": "campaign", "status": "ACTIVE"}])
        sys.argv = ["verificar_activacion.py", "--producto", "PROD_LOST", "--fase", "1", "--snapshot", snap]
        ret = va.main()
        assert ret == 1, f"Retorno inesperado: {ret}"
        print("  OK     campaña no encontrada en snapshot falla con exit 1")


def test_producto_sin_campaign_id_falla():
    with EntornoPrueba() as env:
        env.escribir_productos([{"producto_key": "PROD_NO_ID", "cuenta_alias": "GTR7", "campaign_id": ""}])
        snap = env.escribir_snapshot([])
        sys.argv = ["verificar_activacion.py", "--producto", "PROD_NO_ID", "--fase", "1", "--snapshot", snap]
        ret = va.main()
        assert ret == 1, f"Retorno inesperado: {ret}"
        print("  OK     producto sin campaign_id falla con exit 1")


def test_snapshot_no_existe_falla():
    with EntornoPrueba() as env:
        env.escribir_productos([{"producto_key": "PROD_SNAP_NO", "cuenta_alias": "GTR7", "campaign_id": "camp_1"}])
        sys.argv = ["verificar_activacion.py", "--producto", "PROD_SNAP_NO", "--fase", "1", "--snapshot", "inexistente.json"]
        ret = va.main()
        assert ret == 1, f"Retorno inesperado: {ret}"
        print("  OK     snapshot inexistente falla con exit 1")


def main():
    print("test_verificar_activacion.py:")
    fallas = 0
    pruebas = [
        test_campana_active_pasa_con_exito,
        test_campana_paused_falla,
        test_campana_no_encontrada_en_snapshot_falla,
        test_producto_sin_campaign_id_falla,
        test_snapshot_no_existe_falla,
    ]
    for p in pruebas:
        try:
            p()
        except Exception as e:
            print(f"  FALLA  {p.__name__}: {e}")
            fallas += 1
    return 1 if fallas else 0


if __name__ == "__main__":
    sys.exit(main())
