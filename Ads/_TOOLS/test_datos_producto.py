#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_datos_producto.py — GATE de «datos para arrancar» (solo lectura).

Congela el criterio de cada dato (el mismo del bloqueo que lo exige), que EXTERNA es una cuenta legitima,
que el perfil creativo se juzga solo en FASE 2 contra el #1 y la referencia solo en FASE 1, y que mirar
nunca escribe. Todo sobre directorios temporales.

USO:  python -m pytest Ads/_TOOLS/test_datos_producto.py -q
"""

import csv
import io
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import datos_producto as dp  # noqa: E402

COLS_PRODUCTOS = ["producto_key", "nombre_display", "slug_carpeta", "costo_q", "page_id", "cuenta_alias"]
TEXTOS = {k: "x" for k in ("HOOK_TITULAR", "SUB_HOOK", "ACTIVOS_CLAVE", "GARANTIAS", "CTA")}


def _csv(ruta, columnas, filas):
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with io.open(ruta, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(columnas)
        w.writerows(filas)


@pytest.fixture
def base(tmp_path):
    p = tmp_path / "PRODUCTOS"
    _csv(p / "_DIM_PRODUCTOS.csv", COLS_PRODUCTOS, [
        ["COMPLETO", "Completo", "COMPLETO", "50", "123456", "GTR 7"],
        ["VACIO", "Vacio", "VACIO", "", "PENDIENTE", ""],
        ["EXT", "Externo", "EXT", "7000", "999", "EXTERNA"],
        ["RETIRADA", "Retirada", "RETIRADA", "10", "1", "GTR 2"],
        ["FANTASMA", "Fantasma", "FANTASMA", "10", "1", "GTR 99"],
    ])
    _csv(p / "_DIM_CUENTAS.csv", ["cuenta_alias", "estado_cuenta"],
         [["GTR 7", "ACTIVE"], ["GTR 2", "RETIRADA"]])
    _csv(p / "_DIM_PRECIOS.csv", ["producto_key", "unidades", "etiqueta", "precio_q", "estado"], [
        ["COMPLETO", "2", "2x", "239.00", "ACTIVO"], ["COMPLETO", "1", "1x", "179.00", "ACTIVO"],
        ["EXT", "1", "1x", "99.00", "HISTORICO"], ["VACIO", "1", "1x", "", "ACTIVO"]])
    _csv(p / "_DIM_ENVASE.csv", ["producto_key", "packshot", "color_envase", "marca_impresa"], [
        ["COMPLETO", "Ads/MEDIA_C/COMPLETO_PACKSHOT.png", "AZUL", "MARCA"],
        ["EXT", "Ads/MEDIA_E/EXT_PACKSHOT.png", "AZUL", "MARCA"],
        ["RETIRADA", "Ads/MEDIA_R/R_PACKSHOT.png", "AZUL", ""]])
    (tmp_path / "Ads" / "MEDIA_C").mkdir(parents=True)
    (tmp_path / "Ads" / "MEDIA_C" / "COMPLETO_PACKSHOT.png").write_bytes(b"x")
    (tmp_path / "Ads" / "MEDIA_R").mkdir()
    (tmp_path / "Ads" / "MEDIA_R" / "R_PACKSHOT.png").write_bytes(b"x")
    _csv(p / "_DIM_REFERENCIA_F1.csv", ["producto_key", "referencia"], [["COMPLETO", "ligera__a.jpg"]])
    return tmp_path


def _fila(base, pk):
    return next(f for f in dp._leer_csv(str(base), "_DIM_PRODUCTOS.csv") if f["producto_key"] == pk)


def _estados(r):
    return {i["clave"]: i["estado"] for i in r["items"]}


def test_un_producto_completo_no_tiene_faltantes(base):
    r = dp.revisar_producto(str(base), _fila(base, "COMPLETO"), {"fase": "F1", "angulos_ganadores": []})
    assert r["completo"] and r["faltan"] == 0
    assert r["packshot"]["archivo"] == "COMPLETO_PACKSHOT.png"
    assert all(i["como_resolver"] == "" and i["accion"] is None for i in r["items"])


def test_un_producto_vacio_lista_cada_faltante_con_su_accion(base):
    r = dp.revisar_producto(str(base), _fila(base, "VACIO"), {"fase": "F1", "angulos_ganadores": []})
    acciones = {i["clave"]: i["accion"] for i in r["items"] if i["estado"] == "falta"}
    assert acciones == {"packshot": "producto.cargar_packshot", "costo_q": "producto.cambiar_costo", "precio": None,
                        "page_id": "producto.cargar_page_id", "cuenta": "producto.cargar_cuenta",
                        "referencia_f1": None}
    assert all(i["como_resolver"] for i in r["items"]), "cada faltante trae su frase para el operador"
    assert "python" not in json.dumps(r["items"]).lower(), "nunca se muestra un comando"


def test_externa_es_una_cuenta_valida_y_solo_estado_activo_cuenta_como_precio(base):
    r = dp.revisar_producto(str(base), _fila(base, "EXT"), None)
    assert _estados(r)["cuenta"] == "ok"
    assert _estados(r)["precio"] == "falta", "una fila HISTORICO no es un precio activo"


def test_cuenta_retirada_o_inexistente_falta(base):
    assert _estados(dp.revisar_producto(str(base), _fila(base, "RETIRADA"), None))["cuenta"] == "falta"
    assert _estados(dp.revisar_producto(str(base), _fila(base, "FANTASMA"), None))["cuenta"] == "falta"


def test_packshot_sin_marca_o_sin_archivo_falta(base):
    assert _estados(dp.revisar_producto(str(base), _fila(base, "RETIRADA"), None))["packshot"] == "falta"
    (base / "Ads" / "MEDIA_C" / "COMPLETO_PACKSHOT.png").unlink()
    r = dp.revisar_producto(str(base), _fila(base, "COMPLETO"), None)
    assert _estados(r)["packshot"] == "falta" and r["packshot"] is None


def test_perfil_creativo_se_juzga_solo_en_fase_2_contra_el_numero_1(base):
    fila = _fila(base, "COMPLETO")
    sin_flujo = dp.revisar_producto(str(base), fila, None)
    assert "perfil_creativo" not in _estados(sin_flujo) and sin_flujo["avisos"]
    f2 = {"fase": "F2", "angulos_ganadores": ["ANG_1", "ANG_2"]}
    assert _estados(dp.revisar_producto(str(base), fila, f2))["perfil_creativo"] == "falta"
    ruta = base / "PRODUCTOS" / "COMPLETO" / "_PERFIL_CREATIVO.json"
    ruta.parent.mkdir()
    ruta.write_text(json.dumps({"angulo_key": "ANG_2", "perfil": {}, "textos": TEXTOS}), encoding="utf-8")
    r = dp.revisar_producto(str(base), fila, f2)
    assert _estados(r)["perfil_creativo"] == "falta" and "ANG_1" in r["items"][-1]["detalle"]
    ruta.write_text(json.dumps({"angulo_key": "ANG_1", "perfil": {}, "textos": TEXTOS}), encoding="utf-8")
    r = dp.revisar_producto(str(base), fila, f2)
    assert _estados(r)["perfil_creativo"] == "ok" and r["angulo_1"] == "ANG_1"
    ruta.write_text(json.dumps({"angulo_key": "ANG_1", "perfil": {}, "textos": {"CTA": "x"}}), encoding="utf-8")
    assert _estados(dp.revisar_producto(str(base), fila, f2))["perfil_creativo"] == "falta"
    assert "referencia_f1" not in _estados(dp.revisar_producto(str(base), fila, f2))


def test_mirar_no_escribe_nada(base, capsys):
    antes = {str(p): p.read_bytes() for p in base.rglob("*") if p.is_file()}
    assert dp.main(["--todo", "--sin-flujo", "--base", str(base), "--json"]) == 0
    salida = json.loads(capsys.readouterr().out)
    assert [p["producto_key"] for p in salida["productos"]][:2] == ["COMPLETO", "VACIO"]
    assert dp.main(["VACIO", "--sin-flujo", "--base", str(base)]) == 0
    assert "faltan" in capsys.readouterr().out
    assert {str(p): p.read_bytes() for p in base.rglob("*") if p.is_file()} == antes


def test_producto_inexistente(base, capsys):
    assert dp.main(["NO_EXISTE", "--sin-flujo", "--base", str(base), "--json"]) == 1
    assert json.loads(capsys.readouterr().out)["ok"] is False


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q", "-p", "no:cacheprovider", "--noconftest"]))


def _base_mercados(tmp_path, invima=None):
    """Un producto GT y uno CO con su mercado, y la doctrina real (INVIMA pendiente salvo `invima`)."""
    import re
    import shutil
    real = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    p = tmp_path / "PRODUCTOS"
    _csv(p / "_DIM_PRODUCTOS.csv", COLS_PRODUCTOS + ["mercado"], [
        ["GTP", "Gt", "GTP", "50", "1", "EXTERNA", "GT"], ["COP1", "Co", "COP1", "7000", "1", "EXTERNA", "CO"],
        ["SINM", "Sin", "SINM", "50", "1", "EXTERNA", ""]])
    for nombre in ("_DIM_MERCADOS.csv", "_PARAMETROS_FINANZAS.csv"):
        shutil.copy(os.path.join(real, "PRODUCTOS", nombre), p / nombre)
    with io.open(os.path.join(real, "DOCTRINA", "PLANTILLAS_DEFAULTS_OPERADOR.md"), encoding="utf-8") as fh:
        texto = fh.read()
    if invima:
        texto = re.sub(r"(\| `\[REG_INVIMA\]` \| )\*\*PENDIENTE del operador\*\*", lambda m: m.group(1) + "**`%s`**" % invima, texto)
    (tmp_path / "DOCTRINA").mkdir()
    (tmp_path / "DOCTRINA" / "PLANTILLAS_DEFAULTS_OPERADOR.md").write_text(texto, encoding="utf-8")
    return tmp_path


def test_registro_sanitario_gt_ok_co_falta_sin_accion_y_sin_mercado_no_se_juzga(tmp_path):
    b = _base_mercados(tmp_path)
    gt = dp.revisar_producto(str(b), _fila(b, "GTP"))
    co = dp.revisar_producto(str(b), _fila(b, "COP1"))
    sin = dp.revisar_producto(str(b), _fila(b, "SINM"))
    item = next(i for i in gt["items"] if i["clave"] == "registro_sanitario")
    assert item["estado"] == "ok" and "NS02026-GT3147" in item["detalle"]
    falta = next(i for i in co["items"] if i["clave"] == "registro_sanitario")
    assert falta["estado"] == "falta" and "INVIMA" in falta["detalle"] and "Colombia" in falta["detalle"]
    assert falta["accion"] is None and "número de registro" in falta["como_resolver"]
    assert "python" not in falta["como_resolver"].lower() and "MSPAS" not in falta["detalle"]
    assert "registro_sanitario" not in _estados(sin), "sin mercado valido lo dice mercado.py, no este dato"


def test_registro_sanitario_co_con_numero_queda_ok(tmp_path):
    b = _base_mercados(tmp_path, invima="INVIMA 2026M-0012345")
    co = dp.revisar_producto(str(b), _fila(b, "COP1"))
    assert _estados(co)["registro_sanitario"] == "ok"
