#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_gen_orden_activacion.py — Pruebas unitarias de gen_orden_activacion.py.

Verifica:
  · Emisión correcta de ads_activate_entity con entity_id = campaign_id.
  · Invariante 7: hora de activación siempre 4 AM del día siguiente (nunca hoy).
  · Idempotencia: si la campaña ya está ACTIVE en snapshot, marca omitir: True.
  · Bloqueos con nombre del dueño:
      - Producto no existe en _DIM_PRODUCTOS.csv -> bloquea (dueño: alta_producto.py).
      - Falta cuenta publicitaria -> bloquea (dueño: producto.cargar_cuenta).
      - Falta campaign_id -> bloquea (dueño: verificar_publicacion.py / alta_producto.py).
      - Falta ad_id en creativos -> bloquea (dueño: verificar_publicacion.py).
      - Campaña no encontrada en snapshot -> bloquea (dueño: publicacion.paquete / publicar-meta).

USO:  python Ads/_TOOLS/test_gen_orden_activacion.py     (exit 0 = pasa, 1 = falla)
"""
import csv
import datetime
import io
import json
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_orden_activacion as goa  # noqa: E402


class EntornoPrueba:
    def __init__(self):
        self.tmp = tempfile.mkdtemp(prefix="test_goa_")
        self.prod_dir = os.path.join(self.tmp, "PRODUCTOS")
        os.makedirs(self.prod_dir, exist_ok=True)
        self.orig_base = goa.BASE

    def __enter__(self):
        goa.BASE = self.tmp
        return self

    def __exit__(self, *exc):
        goa.BASE = self.orig_base
        shutil.rmtree(self.tmp, ignore_errors=True)

    def escribir_productos(self, filas):
        cols = ["producto_key", "cuenta_alias", "campaign_id"]
        ruta = os.path.join(self.prod_dir, "_DIM_PRODUCTOS.csv")
        with io.open(ruta, "w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=cols)
            w.writeheader()
            for f in filas:
                w.writerow(f)

    def escribir_creativos(self, filas):
        cols = ["producto_key", "creativo_id", "ad_id"]
        ruta = os.path.join(self.prod_dir, "_DIM_CREATIVOS.csv")
        with io.open(ruta, "w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=cols)
            w.writeheader()
            for f in filas:
                w.writerow(f)

    def escribir_parametros(self, fase="1", hora="04:00", tz="-06:00"):
        cols = ["fase", "hora_lanzamiento", "tz_offset"]
        ruta = os.path.join(self.prod_dir, "_PARAMETROS_PUBLICACION.csv")
        with io.open(ruta, "w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=cols)
            w.writeheader()
            w.writerow({"fase": str(fase), "hora_lanzamiento": hora, "tz_offset": tz})

    def escribir_snapshot(self, entidades):
        ruta = os.path.join(self.tmp, "snapshot.json")
        with io.open(ruta, "w", encoding="utf-8") as fh:
            json.dump({"ad_entities": entidades}, fh)
        return ruta


def test_orden_activacion_normal():
    with EntornoPrueba() as env:
        env.escribir_productos([{"producto_key": "PROD_A", "cuenta_alias": "GTR7", "campaign_id": "camp_100"}])
        env.escribir_creativos([{"producto_key": "PROD_A", "creativo_id": "C1", "ad_id": "ad_1;ad_2"}])
        env.escribir_parametros(fase="1", hora="04:00", tz="-06:00")
        snap = env.escribir_snapshot([{"id": "camp_100", "name": "GTR7_PROD_A_F1", "nivel": "campaign", "status": "PAUSED"}])

        salida = os.path.join(env.tmp, "orden.json")
        sys.argv = [
            "gen_orden_activacion.py",
            "--producto", "PROD_A",
            "--fase", "1",
            "--snapshot", snap,
            "--salida", salida,
            "--json",
        ]
        ret = goa.main()
        assert ret == 0, f"Retorno inesperado: {ret}"
        assert os.path.exists(salida), "No escribió salida"
        with io.open(salida, encoding="utf-8") as fh:
            orden = json.load(fh)

        assert orden["producto"] == "PROD_A"
        assert orden["campaign_id"] == "camp_100"
        assert orden["evento"] == "LANZAMIENTO"
        assert len(orden["llamadas"]) == 1
        llamada = orden["llamadas"][0]
        assert llamada["tool"] == "ads_activate_entity"
        assert llamada["args"]["entity_id"] == "camp_100"
        assert llamada["omitir"] is False

        # Invariante 7: fecha posterior a hoy y a las 4 AM
        hoy = datetime.date.today().isoformat()
        assert not orden["hora_activacion"].startswith(hoy), "La fecha debe ser posterior a hoy"
        assert "T04:00:00-06:00" in orden["hora_activacion"]
        print("  OK     orden_activacion_normal emite ads_activate_entity y 4 AM del día siguiente")


def test_idempotencia_campana_ya_active():
    with EntornoPrueba() as env:
        env.escribir_productos([{"producto_key": "PROD_A", "cuenta_alias": "GTR7", "campaign_id": "camp_100"}])
        env.escribir_creativos([{"producto_key": "PROD_A", "creativo_id": "C1", "ad_id": "ad_1"}])
        env.escribir_parametros()
        snap = env.escribir_snapshot([{"id": "camp_100", "name": "GTR7_PROD_A_F1", "nivel": "campaign", "status": "ACTIVE"}])

        salida = os.path.join(env.tmp, "orden.json")
        sys.argv = [
            "gen_orden_activacion.py",
            "--producto", "PROD_A",
            "--fase", "1",
            "--snapshot", snap,
            "--salida", salida,
            "--json",
        ]
        ret = goa.main()
        assert ret == 0
        with io.open(salida, encoding="utf-8") as fh:
            orden = json.load(fh)

        assert orden["llamadas"][0]["omitir"] is True
        assert orden["llamadas"][0]["id_existente"] == "camp_100"
        print("  OK     idempotencia: campaña ya ACTIVE en Meta se marca omitir: True")


def test_bloqueo_producto_inexistente():
    with EntornoPrueba() as env:
        env.escribir_productos([])
        salida = os.path.join(env.tmp, "orden.json")
        sys.argv = ["gen_orden_activacion.py", "--producto", "FANTASMA", "--fase", "1", "--salida", salida, "--json"]
        ret = goa.main()
        assert ret == 1
        with io.open(salida, encoding="utf-8") as fh:
            res = json.load(fh)
        assert any("no tiene fila en _DIM_PRODUCTOS.csv" in b["falta"] for b in res["bloqueantes"])
        print("  OK     producto inexistente bloquea con exit 1 y nombra dueño")


def test_bloqueo_sin_cuenta():
    with EntornoPrueba() as env:
        env.escribir_productos([{"producto_key": "PROD_SIN_CTA", "cuenta_alias": "", "campaign_id": "123"}])
        env.escribir_creativos([{"producto_key": "PROD_SIN_CTA", "creativo_id": "C1", "ad_id": "ad_1"}])
        salida = os.path.join(env.tmp, "orden.json")
        sys.argv = ["gen_orden_activacion.py", "--producto", "PROD_SIN_CTA", "--fase", "1", "--salida", salida, "--json"]
        ret = goa.main()
        assert ret == 1
        with io.open(salida, encoding="utf-8") as fh:
            res = json.load(fh)
        assert any("cuenta" in b.get("clave", "") or "cuenta" in b["falta"] for b in res["bloqueantes"])
        print("  OK     sin cuenta publicitaria bloquea con clave 'cuenta'")


def test_bloqueo_sin_campaign_id():
    with EntornoPrueba() as env:
        env.escribir_productos([{"producto_key": "PROD_B", "cuenta_alias": "GTR7", "campaign_id": ""}])
        env.escribir_creativos([{"producto_key": "PROD_B", "creativo_id": "C1", "ad_id": "ad_1"}])
        salida = os.path.join(env.tmp, "orden.json")
        sys.argv = ["gen_orden_activacion.py", "--producto", "PROD_B", "--fase", "1", "--salida", salida, "--json"]
        ret = goa.main()
        assert ret == 1
        with io.open(salida, encoding="utf-8") as fh:
            res = json.load(fh)
        assert any("campaign_id" in b["falta"] for b in res["bloqueantes"])
        print("  OK     sin campaign_id bloquea nombrando a verificar_publicacion.py")


def test_bloqueo_sin_ad_ids():
    with EntornoPrueba() as env:
        env.escribir_productos([{"producto_key": "PROD_C", "cuenta_alias": "GTR7", "campaign_id": "camp_999"}])
        env.escribir_creativos([{"producto_key": "PROD_C", "creativo_id": "C1", "ad_id": ""}])
        salida = os.path.join(env.tmp, "orden.json")
        sys.argv = ["gen_orden_activacion.py", "--producto", "PROD_C", "--fase", "1", "--salida", salida, "--json"]
        ret = goa.main()
        assert ret == 1
        with io.open(salida, encoding="utf-8") as fh:
            res = json.load(fh)
        assert any("ad_id" in b["falta"] for b in res["bloqueantes"])
        print("  OK     sin creativos con ad_id bloquea nombrando a verificar_publicacion.py")


def main():
    print("test_gen_orden_activacion.py:")
    fallas = 0
    pruebas = [
        test_orden_activacion_normal,
        test_idempotencia_campana_ya_active,
        test_bloqueo_producto_inexistente,
        test_bloqueo_sin_cuenta,
        test_bloqueo_sin_campaign_id,
        test_bloqueo_sin_ad_ids,
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
