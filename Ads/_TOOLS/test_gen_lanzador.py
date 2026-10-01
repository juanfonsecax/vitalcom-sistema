#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_gen_lanzador.py — GATES DE gen_lanzador.py.

Todas las fases leen su presupuesto de la fila VIGENTE en
_PRODUCTOS/_PARAMETROS_PUBLICACION.csv (sin fila: None, no inventa). Un
lanzamiento ya registrado en _EVENTOS.csv fija la fecha del plan. Los montos
también se dan en la moneda de la cuenta (monto_cuenta) y el plan trae la
configuración fija de Meta (CONFIG_META_FIJA).

USO:  python Ads/_TOOLS/test_gen_lanzador.py     (exit 0 = pasa, 1 = falla)
"""
import csv
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_lanzador as gl  # noqa: E402


def _parametros_publicacion(tmp):
    ruta = os.path.join(tmp, "_PARAMETROS_PUBLICACION.csv")
    filas = [
        {"fase": "1", "brazo": "UNICO", "daily_budget_usd": "2.99", "estado": "VIGENTE",
         "fuente_doctrina": "CALENDARIO_ESCALADO.md 1.5"},
        {"fase": "2", "brazo": "A", "daily_budget_usd": "6.00", "estado": "VIGENTE",
         "fuente_doctrina": "CALENDARIO_ESCALADO.md 1.7.2"},
        {"fase": "2", "brazo": "B", "daily_budget_usd": "6.00", "estado": "VIGENTE",
         "fuente_doctrina": "CALENDARIO_ESCALADO.md 1.7.2"},
        {"fase": "2", "brazo": "C", "daily_budget_usd": "6.00", "estado": "VIGENTE",
         "fuente_doctrina": "CALENDARIO_ESCALADO.md 1.7.2"},
        {"fase": "4", "brazo": "UNICO", "daily_budget_usd": "15.00", "estado": "VIGENTE",
         "fuente_doctrina": "ESCALADO_PLAYBOOK.md"},
    ]
    cols = ["fase", "brazo", "daily_budget_usd", "estado", "fuente_doctrina"]
    with open(ruta, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(filas)
    return ruta


def test_fase2_lee_el_valor_fijo_del_csv():
    with tempfile.TemporaryDirectory() as tmp:
        ruta = _parametros_publicacion(tmp)
        viejo = gl.PARAMETROS_PUBLICACION
        gl.PARAMETROS_PUBLICACION = ruta
        try:
            presup_fase2, por_que = gl.presupuesto_por_fase(2, 0.478)
        finally:
            gl.PARAMETROS_PUBLICACION = viejo
    ok = presup_fase2 == 6.0
    print(("  OK     " if ok else "  FALLA  ")
          + "FASE 2 dicta $6.00/conjunto (fijo, _PARAMETROS_PUBLICACION.csv)"
          + ("" if ok else f"\n         fase2={presup_fase2!r} por_que={por_que!r}"))
    return 0 if ok else 1


def test_fase4_lee_el_valor_fijo_de_escalado():
    with tempfile.TemporaryDirectory() as tmp:
        ruta = _parametros_publicacion(tmp)
        viejo = gl.PARAMETROS_PUBLICACION
        gl.PARAMETROS_PUBLICACION = ruta
        try:
            presup, por_que = gl.presupuesto_por_fase(4, 0.478)
        finally:
            gl.PARAMETROS_PUBLICACION = viejo
    ok = presup == 15.0
    print(("  OK     " if ok else "  FALLA  ")
          + "FASE 4 dicta $15.00 (CBO, ESCALADO_PLAYBOOK.md), no la formula autoajustable de FASE 1"
          + ("" if ok else f"\n         obtenido={presup!r} por_que={por_que!r}"))
    return 0 if ok else 1


def test_fase1_lee_el_valor_fijo_del_csv():
    """FASE 1 lee su fila VIGENTE: con el CSV temporal da 2.99 sin importar usd_conv."""
    with tempfile.TemporaryDirectory() as tmp:
        ruta = _parametros_publicacion(tmp)
        viejo = gl.PARAMETROS_PUBLICACION
        gl.PARAMETROS_PUBLICACION = ruta
        try:
            bajo, _ = gl.presupuesto_por_fase(1, 0.1)
            alto, _ = gl.presupuesto_por_fase(1, 0.9)
        finally:
            gl.PARAMETROS_PUBLICACION = viejo
    ok = bajo == 2.99 and alto == 2.99
    print(("  OK     " if ok else "  FALLA  ")
          + "FASE 1 lee el valor fijo del CSV (2.99 con cualquier usd_conv)"
          + ("" if ok else f"\n         bajo={bajo!r} alto={alto!r}"))
    return 0 if ok else 1


def test_fase_sin_fila_vigente_no_inventa():
    with tempfile.TemporaryDirectory() as tmp:
        ruta = os.path.join(tmp, "_PARAMETROS_PUBLICACION.csv")
        with open(ruta, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=["fase", "brazo", "daily_budget_usd", "estado", "fuente_doctrina"])
            w.writeheader()
        viejo = gl.PARAMETROS_PUBLICACION
        gl.PARAMETROS_PUBLICACION = ruta
        try:
            presup, por_que = gl.presupuesto_por_fase(2, 0.478)
        finally:
            gl.PARAMETROS_PUBLICACION = viejo
    ok = presup is None and "sin fila VIGENTE" in (por_que or "")
    print(("  OK     " if ok else "  FALLA  ")
          + "sin fila VIGENTE para la fase, no inventa un numero: devuelve None con el motivo"
          + ("" if ok else f"\n         presup={presup!r} por_que={por_que!r}"))
    return 0 if ok else 1


def _eventos(tmp, filas):
    ruta = os.path.join(tmp, "_EVENTOS.csv")
    cols = ["fecha", "producto_key", "evento", "campana_clave"]
    with open(ruta, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(filas)
    return ruta


def test_token_formato():
    casos = [("IMAGEN", "IMG"), ("", "IMG"), (None, "IMG"), ("VIDEO", "VID")]
    fallas = ["%r -> %r" % (dado, gl.token_formato(dado))
              for dado, esperado in casos if gl.token_formato(dado) != esperado]
    ok = not fallas
    print(("  OK     " if ok else "  FALLA  ")
          + "token_formato: IMAGEN (o vacio) es IMG, el resto es VID"
          + ("" if ok else "\n         " + "\n         ".join(fallas)))
    return 0 if ok else 1


def test_destino_de():
    declarado = gl.destino_de({"destino_key": "BOT_V9"})
    vigente = gl.destino_de({})
    ok = declarado == "BOT_V9" and vigente == gl.destino_actual()
    print(("  OK     " if ok else "  FALLA  ")
          + "destino_de: el plan manda si declara, si no la version vigente del bot"
          + ("" if ok else f"\n         declarado={declarado!r} vigente={vigente!r}"))
    return 0 if ok else 1


def test_monto_cuenta():
    casos = [
        ((2.99, "USD", 7.62), (2.99, "US$2.99")),
        ((2.99, "COP", 3152.5), (9426, "$9.426 COP")),
        ((2.99, "COP", None), (None, None)),
        ((2.99, "", 7.62), (None, None)),
    ]
    fallas = ["%r -> %r" % (args, gl.monto_cuenta(*args))
              for args, esperado in casos if gl.monto_cuenta(*args) != esperado]
    ok = not fallas
    print(("  OK     " if ok else "  FALLA  ")
          + "monto_cuenta da valor y texto en la moneda de la cuenta"
          + ("" if ok else "\n         " + "\n         ".join(fallas)))
    return 0 if ok else 1


def test_lanzamiento_registrado():
    with tempfile.TemporaryDirectory() as tmp:
        ruta = _eventos(tmp, [
            {"fecha": "2026-09-28", "producto_key": "P", "evento": "LANZAMIENTO",
             "campana_clave": "X_P_TEST_20260928"},
            {"fecha": "2026-09-30", "producto_key": "P", "evento": "LANZAMIENTO",
             "campana_clave": "X_P_TEST_20260930"},
            {"fecha": "2026-09-30", "producto_key": "P", "evento": "CAMBIO_BOT",
             "campana_clave": "*"},
        ])
        viejo = gl.EVENTOS
        gl.EVENTOS = ruta
        try:
            f1 = gl.lanzamiento_registrado("P", 1)
            f2 = gl.lanzamiento_registrado("P", 2)
            otro = gl.lanzamiento_registrado("OTRO", 1)
        finally:
            gl.EVENTOS = viejo
    ok = (f1 == ("2026-09-30", "X_P_TEST_20260930") and f2 is None and otro is None)
    print(("  OK     " if ok else "  FALLA  ")
          + "el ultimo LANZAMIENTO de la fase fija fecha y campana; otra fase u otro producto, None"
          + ("" if ok else f"\n         f1={f1!r} f2={f2!r} otro={otro!r}"))
    return 0 if ok else 1


def test_plan_real_de_ovulos():
    planes = {p["producto_key"]: p for p in gl.construir()["productos"]}
    plan = planes["OVULOS_PURITY"]["plan"]
    cheques = [
        ("bloqueantes vacios", plan["bloqueantes"] == []),
        ("presupuesto fijo de fase 1", plan["presupuesto"]["por_conjunto_usd"] == 2.99),
        ("moneda de la cuenta USD", plan["presupuesto"]["moneda_cuenta"] == "USD"),
        ("montos por conjunto en USD",
         all((c.get("presupuesto_cuenta_texto") or "").startswith("US$")
             for c in plan["conjuntos"])),
        ("lanzamiento registrado", plan["lanzamiento"]["registrado"] is True
         and plan["lanzamiento"]["fecha"] == "2026-09-30"),
        ("nombre de campana registrada",
         plan["campanas"][0]["nombre"] == "EXTERNA_OVULOSPURITY_TEST_20260930"),
        ("config de pais", plan["config_meta"][0] == "Ubicación: Colombia · Sin intereses"),
        ("primer conjunto en _R1", plan["conjuntos"][0]["nombre"].endswith("_R1")),
        ("primer anuncio en IMG", "_IMG_A ~ " in plan["conjuntos"][0]["anuncios"][0]["nombre"]),
    ]
    fallas = [nombre for nombre, cond in cheques if not cond]
    ok = not fallas
    print(("  OK     " if ok else "  FALLA  ")
          + "el plan real de OVULOS_PURITY trae presupuesto, moneda, fecha y config"
          + ("" if ok else "\n         fallan: " + ", ".join(fallas)))
    return 0 if ok else 1


def main():
    fallas = 0
    fallas += test_fase2_lee_el_valor_fijo_del_csv()
    fallas += test_fase4_lee_el_valor_fijo_de_escalado()
    fallas += test_fase1_lee_el_valor_fijo_del_csv()
    fallas += test_fase_sin_fila_vigente_no_inventa()
    fallas += test_monto_cuenta()
    fallas += test_token_formato()
    fallas += test_destino_de()
    fallas += test_lanzamiento_registrado()
    fallas += test_plan_real_de_ovulos()
    print(f"\n{'0 fallas' if not fallas else str(fallas) + ' falla(s)'}.")
    return 1 if fallas else 0


if __name__ == "__main__":
    sys.exit(main())
