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
import json
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


def test_cli_producto_imprime_el_perfil_y_falla_si_no_existe():
    """`--producto PK` y la forma posicional imprimen el mismo perfil; un producto sin fila sale 1."""
    import contextlib
    salida = io.StringIO()
    with contextlib.redirect_stdout(salida):
        assert mercado.main(["--producto", "OVULOS_PURITY"]) == 0
    perfil = json.loads(salida.getvalue())
    assert perfil["mercado"] == "CO" and perfil["moneda"] == "COP" and perfil["persona"] == "tuteo"
    posicional = io.StringIO()
    with contextlib.redirect_stdout(posicional):
        assert mercado.main(["OVULOS_PURITY"]) == 0
    assert posicional.getvalue() == salida.getvalue()
    errores = io.StringIO()
    with contextlib.redirect_stderr(errores):
        assert mercado.main(["--producto", "NO_EXISTE_XYZ"]) == 1
    assert "BLOQUEANTE" in errores.getvalue()


def test_registro_de_perfil_gt_trae_mspas_y_fda_y_co_pendiente_falla():
    gt = mercado.registro_de_perfil(mercado.perfil_mercado("GT"))
    assert gt == {"regulador": "MSPAS", "texto": "MSPAS NS02026-GT3147 · FDA 30045469041", "ajenos": ["INVIMA"]}
    try:
        mercado.registro_de_perfil(mercado.perfil_mercado("CO"))
    except mercado.RegistroFaltante as falta:
        assert falta.regulador == "INVIMA" and falta.claves == ["INVIMA"]
    else:
        raise AssertionError("CO sin numero INVIMA debe fallar")


def test_estado_registro_vacio_es_vigente_y_en_tramite_opta():
    assert mercado.estado_registro({}) == "VIGENTE"
    assert mercado.estado_registro({"registro_sanitario_estado": ""}) == "VIGENTE"
    assert mercado.estado_registro({"registro_sanitario_estado": "VIGENTE"}) == "VIGENTE"
    assert mercado.estado_registro({"registro_sanitario_estado": "EN_TRAMITE"}) == "EN_TRAMITE"


def test_registro_en_tramite_vacio_y_marcado():
    base = _sistema([["B", "COP", "3152.5", "CO"]])
    try:
        reg = mercado.registro_en_tramite(mercado.perfil_de_producto("B", base), base)
        assert reg == {"regulador": "INVIMA", "texto": "", "ajenos": ["MSPAS"], "en_tramite": True}
    finally:
        shutil.rmtree(base)


def test_registro_de_producto_en_tramite_no_bloquea_y_sin_el_sigue_bloqueando():
    ovulos = mercado.registro_de_producto("OVULOS_PURITY")
    assert ovulos["en_tramite"] is True and ovulos["texto"] == "" and ovulos["regulador"] == "INVIMA"
    try:
        mercado.registro_de_producto("GAFAS")
    except mercado.RegistroFaltante as falta:
        assert falta.claves == ["INVIMA"]
    else:
        raise AssertionError("GAFAS sin EN_TRAMITE y sin numero debe seguir bloqueando")
    gt = mercado.registro_de_producto("TINNIDROP")
    assert "en_tramite" not in gt and gt["regulador"] == "MSPAS"


def test_formatear_monto_por_moneda():
    assert mercado.formatear_monto(179, mercado.perfil_mercado("GT")) == "Q179"
    assert mercado.formatear_monto(30.8, mercado.perfil_mercado("GT"), 2) == "Q30.80"
    assert mercado.formatear_monto(41000, mercado.perfil_mercado("CO")) == "$ 41.000"


def test_monto_producto_gt_queda_como_hoy():
    base = _sistema([["GTP", "USD", "7.62", "GT"]])
    try:
        assert mercado.monto_producto(50.123, "GTP", 1, base) == "Q50.1"
        assert mercado.monto_producto("50.1", "GTP", None, base) == "Q50.1"
        assert mercado.monto_producto(93, "GTP", 2, base) == "Q93.00"
    finally:
        shutil.rmtree(base)


def test_monto_producto_co_usa_pesos_sin_decimales():
    base = _sistema([["COP1", "COP", "3152.5", "CO"]])
    try:
        assert mercado.monto_producto(28031.11, "COP1", 2, base) == "$ 28.031"
        assert mercado.monto_producto(9426, "COP1", None, base) == "$ 9.426"
    finally:
        shutil.rmtree(base)


def test_monto_producto_sin_mercado_falla():
    base = _sistema([["GTP", "USD", "7.62", "GT"]])
    try:
        assert _falla(mercado.monto_producto, 10, "NO_EXISTE", base=base) == \
            _falla(mercado.mercado_de, "NO_EXISTE", base)
    finally:
        shutil.rmtree(base)


def test_monto_o_q_producto_inexistente_sale_en_q():
    base = _sistema([["GTP", "USD", "7.62", "GT"]])
    try:
        assert mercado.monto_o_q(50.123, 1, "NO_EXISTE", base) == "Q50.1"
        assert mercado.monto_o_q(50.1, None, None, base) == "Q50.1"
    finally:
        shutil.rmtree(base)


def test_monto_o_q_producto_real_sin_mercado_falla():
    base = _sistema([["SIN", "USD", "7.62", ""]])
    try:
        try:
            mercado.monto_o_q(10, 1, "SIN", base)
        except mercado.MercadoError as error:
            assert "no declara" in str(error), str(error)
        else:
            raise AssertionError("producto real sin mercado tenia que fallar")
    finally:
        shutil.rmtree(base)


def test_monto_o_q_producto_co():
    base = _sistema([["COP1", "COP", "3152.5", "CO"]])
    try:
        assert mercado.monto_o_q(28031.11, 2, "COP1", base) == "$ 28.031"
    finally:
        shutil.rmtree(base)


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
