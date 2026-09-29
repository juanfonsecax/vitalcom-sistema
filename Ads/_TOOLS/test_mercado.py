#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_mercado.py — GATE DEL RESOLVER DE MERCADO.

Congela lo que mercado.py no puede romper nunca:
  · un producto sin mercado, con mercado vacio o con uno que no existe FALLA (no hay GT por defecto);
  · el perfil sale de _DIM_MERCADOS.csv y la tasa de referencia de _PARAMETROS_FINANZAS.csv;
  · `avisos_tasa` es solo lectura y marca la tasa que se aparta de su mercado.

Corre con pytest (tmp dirs) o directo:  python Ads/_TOOLS/test_mercado.py
"""

import csv
import io
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mercado  # noqa: E402


def _csv(base, nombre, encabezado, filas):
    with io.open(os.path.join(base, "PRODUCTOS", nombre), "w", encoding="utf-8", newline="") as fh:
        escritor = csv.writer(fh)
        escritor.writerow(encabezado)
        escritor.writerows(filas)


def _sistema(productos, finanzas=None):
    base = tempfile.mkdtemp(prefix="mercado_test_")
    os.makedirs(os.path.join(base, "PRODUCTOS"))
    _csv(base, "_DIM_PRODUCTOS.csv", ["producto_key", "moneda", "tasa", "mercado"], productos)
    _csv(base, "_DIM_MERCADOS.csv",
         ["mercado", "pais", "moneda", "simbolo", "persona", "registro_sanitario"],
         [["GT", "Guatemala", "GTQ", "Q", "voseo", "registro MSPAS"],
          ["CO", "Colombia", "COP", "$", "tuteo", "registro INVIMA"]])
    _csv(base, "_PARAMETROS_FINANZAS.csv", ["parametro", "valor"],
         finanzas if finanzas is not None else [["tasa_usd_gtq", "7.62"], ["tasa_cop_usd", "3152.5"]])
    return base


def _falla(funcion, *args, **kwargs):
    try:
        funcion(*args, **kwargs)
    except mercado.MercadoError as error:
        return str(error)
    raise AssertionError("tenia que fallar con MercadoError")


def test_mercado_de_devuelve_el_declarado():
    base = _sistema([["A", "USD", "7.62", "GT"], ["B", "COP", "3152.5", "CO"]])
    try:
        assert mercado.mercado_de("A", base) == "GT"
        assert mercado.mercado_de("B", base) == "CO"
    finally:
        shutil.rmtree(base)


def test_sin_mercado_o_desconocido_falla_sin_default():
    base = _sistema([["A", "USD", "7.62", ""], ["B", "USD", "7.62", "  "], ["C", "USD", "7.62", "MX"]])
    try:
        assert "no declara" in _falla(mercado.mercado_de, "A", base)
        assert "no declara" in _falla(mercado.mercado_de, "B", base)
        assert "MX" in _falla(mercado.mercado_de, "C", base)
        assert "no tiene fila" in _falla(mercado.mercado_de, "NO_EXISTE", base)
        assert "no existe" in _falla(mercado.perfil_mercado, "", base)
        assert "no existe" in _falla(mercado.perfil_mercado, "MX", base)
    finally:
        shutil.rmtree(base)


def test_falta_la_columna_mercado_falla():
    base = _sistema([["A", "USD", "7.62", "GT"]])
    try:
        _csv(base, "_DIM_PRODUCTOS.csv", ["producto_key", "moneda", "tasa"], [["A", "USD", "7.62"]])
        assert "columna" in _falla(mercado.mercado_de, "A", base)
    finally:
        shutil.rmtree(base)


def test_perfil_trae_moneda_simbolo_persona_registro_y_tasa():
    base = _sistema([["B", "COP", "3152.5", "CO"]])
    try:
        assert mercado.perfil_de_producto("B", base) == {
            "mercado": "CO", "pais": "Colombia", "moneda": "COP", "simbolo": "$",
            "persona": "tuteo", "registro_sanitario": "registro INVIMA",
            "tasa_moneda_por_usd": 3152.5}
        gt = mercado.perfil_mercado("GT", base)
        assert gt["moneda"] == "GTQ" and gt["simbolo"] == "Q" and gt["tasa_moneda_por_usd"] == 7.62
        assert set(gt) == set(mercado.CAMPOS_PERFIL)
    finally:
        shutil.rmtree(base)


def test_mercado_sin_tasa_de_referencia_da_none_y_avisa():
    base = _sistema([["A", "USD", "7.62", "GT"]], finanzas=[["tasa_cop_usd", "3152.5"]])
    try:
        assert mercado.perfil_mercado("GT", base)["tasa_moneda_por_usd"] is None
        assert any("no tiene tasa de referencia" in a for a in mercado.avisos_tasa(base))
    finally:
        shutil.rmtree(base)


def test_avisos_tasa_marca_solo_la_que_se_aparta_y_no_escribe():
    base = _sistema([["OK", "USD", "7.62", "GT"], ["CERCA", "USD", "8.0", "GT"],
                     ["LEJOS", "USD", "3152.5", "GT"], ["VACIA", "USD", "", "GT"],
                     ["SIN", "USD", "7.62", ""], ["CO_OK", "COP", "3152.5", "CO"]])
    ruta = os.path.join(base, "PRODUCTOS", "_DIM_PRODUCTOS.csv")
    antes = io.open(ruta, "rb").read()
    try:
        avisos = mercado.avisos_tasa(base)
        texto = "\n".join(avisos)
        assert "LEJOS" in texto and "VACIA" in texto and "SIN" in texto, texto
        for limpio in ("OK:", "CERCA", "CO_OK"):
            assert limpio not in texto, texto
        assert io.open(ruta, "rb").read() == antes, "avisos_tasa es de solo lectura"
    finally:
        shutil.rmtree(base)


def test_los_datos_reales_del_sistema_resuelven():
    """El portafolio real: cada producto declara mercado y su tasa cuadra con la del mercado."""
    assert mercado.mercado_de("OVULOS_PURITY") == "CO"
    assert mercado.perfil_de_producto("TINNIDROP")["moneda"] == "GTQ"
    assert mercado.avisos_tasa() == []


if __name__ == "__main__":
    fallas = []
    for nombre, funcion in sorted(globals().items()):
        if nombre.startswith("test_") and callable(funcion):
            try:
                funcion()
                print("  OK    " + nombre)
            except AssertionError as error:
                fallas.append(nombre)
                print("  FALLA %s: %s" % (nombre, error))
    print("\n%d falla(s): %s" % (len(fallas), ", ".join(fallas)) if fallas else "\nTodo en verde.")
    sys.exit(1 if fallas else 0)
