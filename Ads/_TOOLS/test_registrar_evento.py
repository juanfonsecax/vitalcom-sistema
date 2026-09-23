#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_registrar_evento.py — GATE DE registrar_evento.py: P5, un LANZAMIENTO no se registra si
el gate de entrada de su fase (flujo.gate_entrada) no está cumplido, salvo `--excepcion "motivo"`.

Congela:
  · fase resuelta por --fase explícito, o por el token TEST/CONCEPTOS/ESCALA en --campana;
    sin ninguna de las dos, se detiene y pide --fase (nada se escribe).
  · gate cumplido -> LANZAMIENTO se registra normal, sin fila EXCEPCION.
  · gate incumplido sin --excepcion -> se detiene, EXIT != 0, nada se escribe (ni LANZAMIENTO ni
    EXCEPCION).
  · gate incumplido + --excepcion "motivo" -> LANZAMIENTO se registra Y queda EXACTAMENTE una
    fila EXCEPCION (valor_antes=el gate refusado, valor_despues=LANZAMIENTO).
  · --excepcion "" (vacío) se trata como si no se hubiera pasado: refusa igual que sin la flag.
  · eventos que no son LANZAMIENTO (p.ej. CAMBIO_PRESUPUESTO) no piden fase ni gate: sin cambios
    de comportamiento respecto de antes de P5.

USO:  python Ads/_TOOLS/test_registrar_evento.py     (exit 0 = pasa, 1 = falla)
"""
import contextlib
import csv
import datetime
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import registrar_evento as re_  # noqa: E402
import test_flujo as tf  # noqa: E402

EVENTOS_COLS = ["fecha", "producto_key", "cuenta_alias", "campana_clave", "conjunto_meta", "evento",
                "valor_antes", "valor_despues", "motivo", "fuente_decision"]


def _informe(ok, texto, detalle=""):
    print(("  OK     " if ok else "  FALLA  ") + texto + ("" if ok else "\n         %r" % (detalle,)))
    return 0 if ok else 1


def _fixture_lanzamiento(gate_cumplido):
    """PX en FASE 1, con (o sin) ángulo ganador confirmado — el gate real de entrada a F2."""
    tmp = tf.fixture_escalar_flaco(ventas_nuevo=3, con_probado=gate_cumplido)
    tf._escribir_csv(os.path.join(tmp, "PRODUCTOS"), "_EVENTOS.csv", EVENTOS_COLS, [])
    return tmp


def _leer_eventos(base):
    ruta = os.path.join(base, "PRODUCTOS", "_EVENTOS.csv")
    if not os.path.exists(ruta):
        return []
    with io.open(ruta, encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def _correr_main(base, argv):
    previo = (re_.BASE, re_.PROD, re_.EVENTOS, sys.argv)
    re_.BASE = base
    re_.PROD = os.path.join(base, "PRODUCTOS")
    re_.EVENTOS = os.path.join(re_.PROD, "_EVENTOS.csv")
    sys.argv = ["registrar_evento.py"] + argv
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            code = re_.main()
        return code, buf.getvalue(), None
    except Exception as e:                       # noqa: BLE001 — el test reporta el crash, no lo esconde
        return None, buf.getvalue(), e
    finally:
        re_.BASE, re_.PROD, re_.EVENTOS, sys.argv = previo


def test_lanzamiento_gate_cumplido_registra_sin_excepcion():
    base = _fixture_lanzamiento(gate_cumplido=True)
    code, out, err = _correr_main(base, ["--producto", "PX", "--evento", "LANZAMIENTO", "--fase", "2",
                                          "--motivo", "lanzamiento normal", "--fuente", "test",
                                          "--fecha", "2026-09-14"])
    filas = _leer_eventos(base)
    ok = (err is None and code == 0 and len(filas) == 1 and filas[0]["evento"] == "LANZAMIENTO"
          and not any(f["evento"] == "EXCEPCION" for f in filas))
    return _informe(ok, "gate cumplido: LANZAMIENTO se registra y no hay EXCEPCION",
                     (code, err, [f["evento"] for f in filas]))


def test_lanzamiento_gate_incumplido_sin_excepcion_refusa():
    base = _fixture_lanzamiento(gate_cumplido=False)
    code, out, err = _correr_main(base, ["--producto", "PX", "--evento", "LANZAMIENTO", "--fase", "2",
                                          "--motivo", "intento sin gate", "--fuente", "test",
                                          "--fecha", "2026-09-14"])
    filas = _leer_eventos(base)
    ok = err is None and code == 1 and not filas and "gate de entrada" in out
    return _informe(ok, "gate incumplido sin --excepcion: refusa, nada se escribe",
                     (code, err, filas, out[:200]))


def test_lanzamiento_gate_incumplido_excepcion_vacia_refusa_igual():
    base = _fixture_lanzamiento(gate_cumplido=False)
    code, out, err = _correr_main(base, ["--producto", "PX", "--evento", "LANZAMIENTO", "--fase", "2",
                                          "--motivo", "intento", "--fuente", "test",
                                          "--fecha", "2026-09-14", "--excepcion", ""])
    filas = _leer_eventos(base)
    ok = err is None and code == 1 and not filas
    return _informe(ok, "--excepcion \"\" (vacío) se trata como ausente: refusa igual", (code, err, filas))


def test_lanzamiento_gate_incumplido_con_excepcion_procede_y_registra_una_fila():
    base = _fixture_lanzamiento(gate_cumplido=False)
    code, out, err = _correr_main(base, ["--producto", "PX", "--evento", "LANZAMIENTO", "--fase", "2",
                                          "--motivo", "escalar igual", "--fuente", "test",
                                          "--fecha", "2026-09-14", "--excepcion", "decisión del operador"])
    filas = _leer_eventos(base)
    lanz = [f for f in filas if f["evento"] == "LANZAMIENTO"]
    exc = [f for f in filas if f["evento"] == "EXCEPCION"]
    ok = (err is None and code == 0 and len(lanz) == 1 and len(exc) == 1
          and exc[0]["valor_antes"] == "F2.entrada" and exc[0]["valor_despues"] == "LANZAMIENTO"
          and exc[0]["motivo"] == "decisión del operador"
          and exc[0]["fuente_decision"] == "Ads/_TOOLS/registrar_evento.py")
    return _informe(ok, "gate incumplido + --excepcion: procede y anexa EXACTAMENTE una fila EXCEPCION",
                     (code, err, filas))


def test_lanzamiento_fase_por_token_de_campana():
    base = _fixture_lanzamiento(gate_cumplido=True)
    code, out, err = _correr_main(base, ["--producto", "PX", "--evento", "LANZAMIENTO",
                                          "--campana", "GTR7_PX_CONCEPTOS-A_20260924",
                                          "--motivo", "sin --fase, lo trae la campaña", "--fuente", "test",
                                          "--fecha", "2026-09-14"])
    filas = _leer_eventos(base)
    ok = err is None and code == 0 and len(filas) == 1
    return _informe(ok, "sin --fase: se resuelve del token CONCEPTOS en --campana (fase 2)",
                     (code, err, out[:200]))


def test_lanzamiento_sin_fase_ni_token_pide_fase():
    base = _fixture_lanzamiento(gate_cumplido=True)
    code, out, err = _correr_main(base, ["--producto", "PX", "--evento", "LANZAMIENTO",
                                          "--motivo", "sin pista de fase", "--fuente", "test",
                                          "--fecha", "2026-09-14"])
    filas = _leer_eventos(base)
    ok = err is None and code == 1 and not filas and "--fase" in out
    return _informe(ok, "sin --fase ni token en --campana: se detiene y pide --fase", (code, err, out[:200]))


def test_evento_no_lanzamiento_no_exige_fase_ni_gate():
    base = _fixture_lanzamiento(gate_cumplido=False)   # gate F2 incumplido a propósito: no debe importar
    code, out, err = _correr_main(base, ["--producto", "PX", "--evento", "CAMBIO_PRESUPUESTO",
                                          "--conjunto", "GTR7_PX_NUEVO_R1", "--antes", "5", "--despues", "5.5",
                                          "--motivo", "surfing", "--fuente", "test", "--fecha", "2026-09-14"])
    filas = _leer_eventos(base)
    ok = err is None and code == 0 and len(filas) == 1 and filas[0]["evento"] == "CAMBIO_PRESUPUESTO"
    return _informe(ok, "un evento que no es LANZAMIENTO no pide fase ni consulta el gate",
                     (code, err, filas))


def main():
    pruebas = [
        test_lanzamiento_gate_cumplido_registra_sin_excepcion,
        test_lanzamiento_gate_incumplido_sin_excepcion_refusa,
        test_lanzamiento_gate_incumplido_excepcion_vacia_refusa_igual,
        test_lanzamiento_gate_incumplido_con_excepcion_procede_y_registra_una_fila,
        test_lanzamiento_fase_por_token_de_campana,
        test_lanzamiento_sin_fase_ni_token_pide_fase,
        test_evento_no_lanzamiento_no_exige_fase_ni_gate,
    ]
    fallas = sum(p() for p in pruebas)
    print(f"\n{'0 fallas' if not fallas else str(fallas) + ' falla(s)'}.")
    return 1 if fallas else 0


if __name__ == "__main__":
    sys.exit(main())
