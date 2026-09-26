#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_ciclo_diario.py — GATE de ciclo_diario.py (P3 T6): pruebas de LÓGICA PURA sobre `correr()`.

Nunca tocan red, Postgres real (`vitalcom`) ni `PRODUCTOS/` real: cada escenario inyecta sus propios
pasos falsos (comandos `python -c ...` de una línea, o funciones), su propio preflight/postcheck
falsos, y escribe en un directorio temporal. `correr()` es la única función que estas pruebas
ejercitan de punta a punta; `main()` (CLI, disco real, subprocess real) queda fuera a propósito.

USO:  python -m pytest Ads/_TOOLS/test_ciclo_diario.py -q
"""
import csv
import datetime
import io
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ciclo_diario as cd  # noqa: E402


def _preflight_ok():
    return True, ""


def _preflight_falla(detalle="preflight roto"):
    return lambda: (False, detalle)


def _postcheck_ok():
    return True, "IGUAL", ""


def _postcheck_distinto():
    return False, "DISTINTO", "decidir.py --json difiere entre Postgres y csv."


def _paso_ok(nombre, codigos_aviso=()):
    return {"nombre": nombre, "argv": ["true"], "codigos_aviso": tuple(codigos_aviso)}


def _ejecutar_con_codigos(mapa_codigos):
    """Fabrica un `ejecutar_paso` falso: cada paso devuelve el código que le tocó por nombre."""
    def _ejecutar(paso, log_fh):
        log_fh.write(("corrida falsa de %s\n" % paso["nombre"]).encode("utf-8"))
        return mapa_codigos[paso["nombre"]]
    return _ejecutar


def _log_temporal():
    return io.BytesIO()


def _correr(pasos, mapa_codigos, preflight=_preflight_ok, postcheck=_postcheck_ok, hoy_iso="2026-09-25"):
    return cd.correr(
        pasos=pasos, ejecutar_paso=_ejecutar_con_codigos(mapa_codigos), preflight=preflight,
        postcheck=postcheck, log_fh=_log_temporal(), hoy_iso=hoy_iso,
    )


# ── clasificación de un paso ──────────────────────────────────────────────────────────────────

def test_clasificar_ok_cero():
    assert cd._clasificar(_paso_ok("x"), 0) == "OK"


def test_clasificar_fatal_no_declarado_como_aviso():
    assert cd._clasificar(_paso_ok("x"), 1) == "FATAL"


def test_clasificar_aviso_declarado():
    assert cd._clasificar(_paso_ok("x", codigos_aviso=(2,)), 2) == "AVISO"


# ── correr(): todo verde ──────────────────────────────────────────────────────────────────────

def test_todos_los_pasos_en_cero_da_verde():
    pasos = [_paso_ok("uno"), _paso_ok("dos")]
    fila = _correr(pasos, {"uno": 0, "dos": 0})
    assert fila["estado"] == "VERDE"
    assert fila["paso_fallido"] == ""
    assert fila["paridad"] == "IGUAL"


# ── correr(): un paso fatal corta la cadena ──────────────────────────────────────────────────

def test_paso_fatal_corta_la_cadena_y_da_rojo():
    llamado = {"uno": False, "dos": False}

    def _ejecutar(paso, log_fh):
        llamado[paso["nombre"]] = True
        return 1 if paso["nombre"] == "uno" else 0

    fila = cd.correr(pasos=[_paso_ok("uno"), _paso_ok("dos")], ejecutar_paso=_ejecutar,
                      preflight=_preflight_ok, postcheck=_postcheck_ok, log_fh=_log_temporal(),
                      hoy_iso="2026-09-25")
    assert fila["estado"] == "ROJO"
    assert fila["paso_fallido"] == "uno"
    assert llamado["uno"] is True
    assert llamado["dos"] is False  # el paso siguiente al fatal NUNCA corre


# ── correr(): código de aviso da amarillo, pero sigue la cadena y corre el postcheck ─────────

def test_codigo_de_aviso_da_amarillo_y_sigue_la_cadena():
    pasos = [_paso_ok("bajar_meta_insights", codigos_aviso=(2,)), _paso_ok("ciclo_hoy")]
    fila = _correr(pasos, {"bajar_meta_insights": 2, "ciclo_hoy": 0})
    assert fila["estado"] == "AMARILLO"
    assert fila["paridad"] == "IGUAL"
    assert "bajar_meta_insights" in fila["detalle"]


def test_amarillo_cuenta_como_dia_verde_para_t7():
    """Documenta la decisión T6: el código de salida final (0) es el mismo para VERDE y AMARILLO."""
    pasos = [_paso_ok("bajar_meta_insights", codigos_aviso=(2,))]
    fila = _correr(pasos, {"bajar_meta_insights": 2})
    assert fila["estado"] in ("VERDE", "AMARILLO")


# ── correr(): un runner que revienta (excepción, no código de salida) también es ROJO ────────

def test_runner_que_lanza_excepcion_es_rojo_no_crash():
    def _ejecutar(paso, log_fh):
        raise RuntimeError("el subprocess nunca arrancó")

    fila = cd.correr(pasos=[_paso_ok("uno")], ejecutar_paso=_ejecutar, preflight=_preflight_ok,
                      postcheck=_postcheck_ok, log_fh=_log_temporal(), hoy_iso="2026-09-25")
    assert fila["estado"] == "ROJO"
    assert fila["paso_fallido"] == "uno"


# ── correr(): preflight falla -> rojo, ningún paso corre ─────────────────────────────────────

def test_preflight_falla_no_corre_ningun_paso():
    llamado = []

    def _ejecutar(paso, log_fh):
        llamado.append(paso["nombre"])
        return 0

    fila = cd.correr(pasos=[_paso_ok("uno")], ejecutar_paso=_ejecutar,
                      preflight=_preflight_falla("Postgres caído"), postcheck=_postcheck_ok,
                      log_fh=_log_temporal(), hoy_iso="2026-09-25")
    assert fila["estado"] == "ROJO"
    assert fila["paso_fallido"] == "preflight"
    assert llamado == []


def test_preflight_que_lanza_excepcion_tambien_es_rojo():
    def _preflight():
        raise RuntimeError("conexión reventada")

    fila = cd.correr(pasos=[_paso_ok("uno")], ejecutar_paso=_ejecutar_con_codigos({"uno": 0}),
                      preflight=_preflight, postcheck=_postcheck_ok, log_fh=_log_temporal(),
                      hoy_iso="2026-09-25")
    assert fila["estado"] == "ROJO"
    assert fila["paso_fallido"] == "preflight"


# ── correr(): paridad DISTINTO en el postcheck es rojo aunque la cadena haya salido verde ────

def test_paridad_distinta_es_rojo():
    fila = _correr([_paso_ok("uno")], {"uno": 0}, postcheck=_postcheck_distinto)
    assert fila["estado"] == "ROJO"
    assert fila["paridad"] == "DISTINTO"


def test_postcheck_no_corre_si_ya_hubo_un_fatal():
    """El postcheck es caro (dos corridas de decidir.py): no tiene sentido pagarlo si ya es ROJO."""
    llamado = {"n": 0}

    def _postcheck():
        llamado["n"] += 1
        return True, "IGUAL", ""

    fila = _correr([_paso_ok("uno")], {"uno": 1}, postcheck=_postcheck)
    assert fila["estado"] == "ROJO"
    assert llamado["n"] == 0


# ── --si-falta-hoy: lectura de la última fila del día ────────────────────────────────────────

def test_fila_de_hoy_ninguna_fila_da_none():
    with tempfile.TemporaryDirectory() as tmp:
        ruta = os.path.join(tmp, "_CORRIDAS_DIARIAS.csv")
        assert cd.fila_de_hoy(ruta, "2026-09-25") is None


def test_fila_de_hoy_toma_la_ultima_del_dia():
    with tempfile.TemporaryDirectory() as tmp:
        ruta = os.path.join(tmp, "_CORRIDAS_DIARIAS.csv")
        cd._escribir_fila(ruta, {"fecha": "2026-09-24", "inicio": "a", "fin": "b", "estado": "ROJO",
                                  "paso_fallido": "x", "paridad": "NO_CORRIDA", "detalle": ""})
        cd._escribir_fila(ruta, {"fecha": "2026-09-25", "inicio": "a", "fin": "b", "estado": "VERDE",
                                  "paso_fallido": "", "paridad": "IGUAL", "detalle": ""})
        cd._escribir_fila(ruta, {"fecha": "2026-09-25", "inicio": "c", "fin": "d", "estado": "AMARILLO",
                                  "paso_fallido": "", "paridad": "IGUAL", "detalle": "segunda corrida"})
        fila = cd.fila_de_hoy(ruta, "2026-09-25")
        assert fila["estado"] == "AMARILLO"
        assert fila["detalle"] == "segunda corrida"


# ── racha de días verdes (T7) ─────────────────────────────────────────────────────────────────

def _corridas(tmp, filas):
    ruta = os.path.join(tmp, "_CORRIDAS_DIARIAS.csv")
    for fecha, estado in filas:
        cd._escribir_fila(ruta, {"fecha": fecha, "inicio": "a", "fin": "b", "estado": estado,
                                  "paso_fallido": "", "paridad": "IGUAL", "detalle": ""})
    return ruta


def test_racha_sin_archivo_es_cero():
    with tempfile.TemporaryDirectory() as tmp:
        ruta = os.path.join(tmp, "_CORRIDAS_DIARIAS.csv")
        assert cd.racha_verde(ruta, datetime.date(2026, 9, 25)) == (0, None)


def test_racha_cuenta_dias_consecutivos_y_amarillo_suma():
    with tempfile.TemporaryDirectory() as tmp:
        ruta = _corridas(tmp, [("2026-09-23", "VERDE"), ("2026-09-24", "AMARILLO"),
                               ("2026-09-25", "VERDE")])
        assert cd.racha_verde(ruta, datetime.date(2026, 9, 25)) == (3, "2026-09-25")


def test_racha_rojo_corregido_el_mismo_dia_cuenta():
    with tempfile.TemporaryDirectory() as tmp:
        ruta = _corridas(tmp, [("2026-09-25", "ROJO"), ("2026-09-25", "VERDE")])
        assert cd.racha_verde(ruta, datetime.date(2026, 9, 25)) == (1, "2026-09-25")


def test_racha_dia_que_termina_en_rojo_corta():
    with tempfile.TemporaryDirectory() as tmp:
        ruta = _corridas(tmp, [("2026-09-23", "VERDE"), ("2026-09-24", "VERDE"),
                               ("2026-09-24", "ROJO"), ("2026-09-25", "VERDE")])
        assert cd.racha_verde(ruta, datetime.date(2026, 9, 25)) == (1, "2026-09-25")


def test_racha_dia_faltante_corta():
    with tempfile.TemporaryDirectory() as tmp:
        ruta = _corridas(tmp, [("2026-09-22", "VERDE"), ("2026-09-23", "VERDE"),
                               ("2026-09-25", "VERDE")])
        assert cd.racha_verde(ruta, datetime.date(2026, 9, 25)) == (1, "2026-09-25")


def test_racha_hoy_sin_correr_mantiene_la_de_ayer():
    with tempfile.TemporaryDirectory() as tmp:
        ruta = _corridas(tmp, [("2026-09-23", "VERDE"), ("2026-09-24", "VERDE")])
        assert cd.racha_verde(ruta, datetime.date(2026, 9, 25)) == (2, "2026-09-24")


def test_racha_hoy_en_rojo_es_cero():
    with tempfile.TemporaryDirectory() as tmp:
        ruta = _corridas(tmp, [("2026-09-24", "VERDE"), ("2026-09-25", "ROJO")])
        assert cd.racha_verde(ruta, datetime.date(2026, 9, 25)) == (0, None)


def test_texto_racha_anuncia_cierre_con_siete_dias():
    with tempfile.TemporaryDirectory() as tmp:
        inicio = datetime.date(2026, 9, 19)
        ruta = _corridas(tmp, [((inicio + datetime.timedelta(days=i)).isoformat(), "VERDE")
                               for i in range(7)])
        texto = cd.texto_racha(ruta, datetime.date(2026, 9, 25))
        assert "7 días" in texto and "cumplido" in texto, texto


# ── plan de pasos: lunes agrega el control semanal, el resto de días no ─────────────────────

def test_pasos_reales_entre_semana_no_trae_control():
    martes = datetime.date(2026, 9, 22)
    nombres = [p["nombre"] for p in cd.pasos_reales(martes)]
    assert "bajar_lucidsales_control" not in nombres
    assert "ingerir_lucidsales_control" not in nombres


def test_pasos_reales_lunes_agrega_control_con_rol_control():
    lunes = datetime.date(2026, 9, 21)
    pasos = cd.pasos_reales(lunes)
    nombres = [p["nombre"] for p in pasos]
    assert "bajar_lucidsales_control" in nombres
    control = next(p for p in pasos if p["nombre"] == "ingerir_lucidsales_control")
    assert "--rol" in control["argv"] and "CONTROL" in control["argv"]


def test_pasos_reales_bajar_meta_insights_declara_aviso_2():
    pasos = cd.pasos_reales(datetime.date(2026, 9, 22))
    meta = next(p for p in pasos if p["nombre"] == "bajar_meta_insights")
    assert meta["codigos_aviso"] == (2,)


# ── pasos_lucidsales: única fuente compartida con recopilar_lucidsales.py (T4) ───────────────

def test_pasos_lucidsales_es_el_mismo_arranque_de_pasos_reales():
    martes = datetime.date(2026, 9, 22)
    solo_lucidsales = cd.pasos_lucidsales(martes)
    nombres_lucidsales = [p["nombre"] for p in solo_lucidsales]
    nombres_reales = [p["nombre"] for p in cd.pasos_reales(martes)]
    assert nombres_lucidsales == nombres_reales[:len(nombres_lucidsales)]
    assert "bajar_meta_insights" not in nombres_lucidsales
    assert "ciclo_hoy" not in nombres_lucidsales
    assert "gen_dashboard" not in nombres_lucidsales


def test_pasos_lucidsales_lunes_agrega_control_con_rol_control():
    lunes = datetime.date(2026, 9, 21)
    pasos = cd.pasos_lucidsales(lunes)
    nombres = [p["nombre"] for p in pasos]
    assert nombres == ["bajar_lucidsales", "ingerir_lucidsales",
                       "bajar_lucidsales_control", "ingerir_lucidsales_control"]
    control = next(p for p in pasos if p["nombre"] == "ingerir_lucidsales_control")
    assert "--rol" in control["argv"] and "CONTROL" in control["argv"]


# ── el CSV: header se crea una sola vez ──────────────────────────────────────────────────────

def test_escribir_fila_crea_header_una_sola_vez():
    with tempfile.TemporaryDirectory() as tmp:
        ruta = os.path.join(tmp, "sub", "_CORRIDAS_DIARIAS.csv")
        fila = {"fecha": "2026-09-25", "inicio": "a", "fin": "b", "estado": "VERDE",
                "paso_fallido": "", "paridad": "IGUAL", "detalle": ""}
        cd._escribir_fila(ruta, fila)
        cd._escribir_fila(ruta, fila)
        with open(ruta, encoding="utf-8", newline="") as fh:
            lineas = list(csv.reader(fh))
        assert lineas[0] == cd.COLUMNAS
        assert len(lineas) == 3  # header + 2 filas, ningún header repetido


def main():
    """Corre cada `test_*` de este módulo a mano (conftest.py de esta carpeta ejecuta el archivo
    COMO SCRIPT, con este intérprete, en vez de dejar que pytest lo importe y lo colecte: no hay
    que invocar `pytest.main()` acá adentro, o cada corrida se vuelve a colectar a sí misma)."""
    pruebas = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    fallas = 0
    for prueba in pruebas:
        try:
            prueba()
        except AssertionError as exc:
            fallas += 1
            print(f"  FALLA  {prueba.__name__}: {exc}")
        except Exception as exc:  # noqa: BLE001 — cualquier otra excepción también cuenta como falla
            fallas += 1
            print(f"  ERROR  {prueba.__name__}: {exc!r}")
        else:
            print(f"  OK     {prueba.__name__}")
    print(f"\n{'0 fallas' if not fallas else str(fallas) + ' falla(s)'} de {len(pruebas)} pruebas.")
    return 1 if fallas else 0


if __name__ == "__main__":
    sys.exit(main())
