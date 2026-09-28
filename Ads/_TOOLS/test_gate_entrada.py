#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_gate_entrada.py — GATE DE flujo.gate_entrada(): el juez único de "¿se cumple el gate de
entrada a la fase N?" que usan gen_publicacion.py y registrar_evento.py para negar una acción
(P5, gates son candado, no aviso). Congela:

  · una fase sin gate de entrada (F1) siempre está cumplida.
  · el gate de F2 (ángulo ganador), de F3 (concepto 2 de 2, SIN exigir CAMBIO_BOT — cuatro fases,
    28-sep-2026) y de F4 (concepto 2 de 2 + CAMBIO_BOT posterior + cierre_post_cambio_bot) se
    evalúan IGUAL que `situar()` los evalúa (mismo `evaluar()`/`Entorno`) — no una copia paralela.
  · un producto sin fila en _DIM_PRODUCTOS.csv, o una fase que no existe en FLUJO.json, refusan
    con un mensaje claro (nunca inventan un "cumplido").
  · gate_entrada es SOLO LECTURA: nunca toca _ESTADO_FLUJO.csv ni _EVENTOS.csv.

Reusa los fixtures de test_flujo.py (fixture_escalar_flaco, fixture_conceptos_al_filo) en vez
de duplicar la construcción de CSV — ya congelan la doctrina real de F2/F3.

USO:  python Ads/_TOOLS/test_gate_entrada.py     (exit 0 = pasa, 1 = falla)
"""
import csv
import datetime
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import flujo  # noqa: E402
import test_flujo as tf  # noqa: E402


def _informe(ok, texto, detalle=""):
    print(("  OK     " if ok else "  FALLA  ") + texto + ("" if ok else "\n         %r" % (detalle,)))
    return 0 if ok else 1


def _con_producto(tmp, pk):
    """Fixtures de F3 (concepto_2de2) no traen _DIM_PRODUCTOS.csv: gate_entrada lo necesita
    para construir el contexto — se lo agrega esta prueba, no el fixture de test_flujo.py."""
    prod = os.path.join(tmp, "PRODUCTOS")
    with io.open(os.path.join(prod, "_DIM_PRODUCTOS.csv"), "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["producto_key", "nombre_display", "estado", "fase"])
        w.writerow([pk, pk, "VIVO", "F2"])
    return tmp


def test_f1_sin_gate_siempre_cumplida():
    tmp = tf.fixture_escalar_flaco(ventas_nuevo=1, con_probado=False)   # data irrelevante para F1
    env = flujo.Entorno(base=tmp, hoy=datetime.date(2026, 9, 14), sin_scripts=True)
    ok, obs = flujo.gate_entrada("PX", "1", env)
    ok2, _ = flujo.gate_entrada("PX", "F1", env)      # "1" y "F1" son el mismo id
    return _informe(ok is True and ok2 is True and "no declara gate" in obs,
                     "F1 no declara gate de entrada: siempre cumplida", (ok, obs))


def test_f2_angulo_ganador_cumplido():
    tmp = tf.fixture_escalar_flaco(ventas_nuevo=3, con_probado=True)
    env = flujo.Entorno(base=tmp, hoy=datetime.date(2026, 9, 14), sin_scripts=True)
    ok, obs = flujo.gate_entrada("PX", 2, env)
    return _informe(ok is True and "ANG_PROBADO" in obs, "F2: ángulo ganador por ESCALAR cumple el gate", obs)


def test_f2_angulo_ganador_incumplido():
    tmp = tf.fixture_escalar_flaco(ventas_nuevo=3, con_probado=False)
    env = flujo.Entorno(base=tmp, hoy=datetime.date(2026, 9, 14), sin_scripts=True)
    ok, obs = flujo.gate_entrada("PX", 2, env)
    return _informe(ok is False and "5" in obs, "F2: sin ningún ángulo con el piso de volumen, el gate NO se cumple", obs)


def test_f3_concepto_2de2_basta_sin_cambio_bot():
    """Cuatro fases (28-sep-2026): F3.entrada es SOLO concepto 2/2 — reescribir el bot es el
    TRABAJO de F3 (F3.reescribir), no su requisito de entrada."""
    tmp = _con_producto(tf.fixture_conceptos_al_filo(), "TURMERIC")
    env = flujo.Entorno(base=tmp, hoy=datetime.date(2026, 9, 28), sin_scripts=True)
    ok, obs = flujo.gate_entrada("TURMERIC", 3, env)
    return _informe(ok is True, "F3: 2 de 2 basta para entrar — SIN exigir CAMBIO_BOT todavía", obs)


def test_f4_sin_cambio_bot_incumplido():
    tmp = _con_producto(tf.fixture_conceptos_al_filo(), "TURMERIC")
    env = flujo.Entorno(base=tmp, hoy=datetime.date(2026, 9, 28), sin_scripts=True)
    ok, obs = flujo.gate_entrada("TURMERIC", 4, env)
    return _informe(ok is False and "CAMBIO_BOT" in obs,
                     "F4: 2 de 2 sin CAMBIO_BOT posterior al ganador NO cumple el gate", obs)


def test_f4_cambio_bot_sin_cierre_incumplido():
    """CAMBIO_BOT posterior al ganador ya no basta solo: hacen falta ≥min_mensajes_cierre
    mensajes con cierre ≥cierre_min_escalar_pct DESPUÉS de ese CAMBIO_BOT (PROHIBIDO_ESCALAR_
    CIERRE_BAJO). Sin ventas posteriores al CAMBIO_BOT, 0 mensajes nunca llega al piso."""
    tmp = _con_producto(tf.fixture_conceptos_al_filo(), "TURMERIC")
    eventos_cols = ["fecha", "producto_key", "cuenta_alias", "campana_clave", "conjunto_meta",
                     "evento", "valor_antes", "valor_despues", "motivo", "fuente_decision"]
    tf._escribir_csv(os.path.join(tmp, "PRODUCTOS"), "_EVENTOS.csv", eventos_cols,
                      [["2026-09-28", "TURMERIC", "GTR7", "*", "*", "CAMBIO_BOT", "", "",
                        "reescritura tras 2 de 2", "test"]])
    env = flujo.Entorno(base=tmp, hoy=datetime.date(2026, 9, 29), sin_scripts=True)
    ok, obs = flujo.gate_entrada("TURMERIC", 4, env)
    return _informe(ok is False and "mensaje" in obs,
                     "F4: CAMBIO_BOT posterior sin mensajes/cierre suficientes NO cumple el gate", obs)


def test_f4_cambio_bot_y_cierre_cumplido():
    tmp = _con_producto(tf.fixture_conceptos_al_filo(), "TURMERIC")
    prod = os.path.join(tmp, "PRODUCTOS")
    eventos_cols = ["fecha", "producto_key", "cuenta_alias", "campana_clave", "conjunto_meta",
                     "evento", "valor_antes", "valor_despues", "motivo", "fuente_decision"]
    tf._escribir_csv(prod, "_EVENTOS.csv", eventos_cols,
                      [["2026-09-28", "TURMERIC", "GTR7", "*", "*", "CAMBIO_BOT", "", "",
                        "reescritura tras 2 de 2", "test"]])
    # Agrega `ventana_ini` a las filas del fixture (vacía: no filtra nada, quedan bajo el piso
    # de replicación) y SUMA una fila nueva con ventana_ini POSTERIOR al CAMBIO_BOT — nunca
    # sobrescribe: la data del concepto ganador (concepto_2de2) tiene que seguir intacta.
    with io.open(os.path.join(prod, "_FACT_VENTAS.csv"), encoding="utf-8-sig", newline="") as fh:
        filas_prev = list(csv.reader(fh))
    header, filas_prev = filas_prev[0], filas_prev[1:]
    header_ini = ["ventana_ini"] + header
    filas_prev = [[""] + r for r in filas_prev]
    # 40 mensajes / 5 ventas = 12.5% de cierre, sobre el piso 10% y el min_mensajes_cierre 30,
    # en una ventana con ventana_ini POSTERIOR al 2026-09-28 del CAMBIO_BOT.
    fila_cierre = ["2026-09-29", "2026-10-06", "BASE", "TURMERIC", "GTR7_TURMERIC_ANG_R1",
                   "GTR7_TURMERIC_F3-BOT_20261006", "ad", "5", "40", "80"]
    tf._escribir_csv(prod, "_FACT_VENTAS.csv", header_ini, filas_prev + [fila_cierre])
    env = flujo.Entorno(base=tmp, hoy=datetime.date(2026, 10, 6), sin_scripts=True)
    ok, obs = flujo.gate_entrada("TURMERIC", 4, env)
    return _informe(ok is True, "F4: 2 de 2 + CAMBIO_BOT posterior + cierre sobre el piso SÍ cumple el gate", obs)


def test_producto_sin_fila_refusa():
    tmp = tf.fixture_escalar_flaco(ventas_nuevo=3, con_probado=True)
    env = flujo.Entorno(base=tmp, hoy=datetime.date(2026, 9, 14), sin_scripts=True)
    ok, obs = flujo.gate_entrada("NO_EXISTE", 2, env)
    return _informe(ok is False and "_DIM_PRODUCTOS.csv" in obs,
                     "producto sin fila en _DIM_PRODUCTOS.csv: refusa, no asume cumplido", obs)


def test_fase_inexistente_refusa():
    tmp = tf.fixture_escalar_flaco(ventas_nuevo=3, con_probado=True)
    env = flujo.Entorno(base=tmp, hoy=datetime.date(2026, 9, 14), sin_scripts=True)
    ok, obs = flujo.gate_entrada("PX", 9, env)
    return _informe(ok is False, "una fase que no existe en FLUJO.json refusa, no revienta", obs)


def test_gate_entrada_no_escribe_nada():
    tmp = tf.fixture_escalar_flaco(ventas_nuevo=3, con_probado=True)
    ruta_estado = os.path.join(tmp, "PRODUCTOS", "_ESTADO_FLUJO.csv")
    ruta_eventos = os.path.join(tmp, "PRODUCTOS", "_EVENTOS.csv")
    env = flujo.Entorno(base=tmp, hoy=datetime.date(2026, 9, 14), sin_scripts=True)
    flujo.gate_entrada("PX", 2, env)
    flujo.gate_entrada("PX", 1, env)
    ok = not os.path.exists(ruta_estado) and not os.path.exists(ruta_eventos)
    return _informe(ok, "gate_entrada() es solo lectura: no crea _ESTADO_FLUJO.csv ni _EVENTOS.csv",
                     (os.path.exists(ruta_estado), os.path.exists(ruta_eventos)))


def main():
    pruebas = [
        test_f1_sin_gate_siempre_cumplida,
        test_f2_angulo_ganador_cumplido,
        test_f2_angulo_ganador_incumplido,
        test_f3_concepto_2de2_basta_sin_cambio_bot,
        test_f4_sin_cambio_bot_incumplido,
        test_f4_cambio_bot_sin_cierre_incumplido,
        test_f4_cambio_bot_y_cierre_cumplido,
        test_producto_sin_fila_refusa,
        test_fase_inexistente_refusa,
        test_gate_entrada_no_escribe_nada,
    ]
    fallas = sum(p() for p in pruebas)
    print(f"\n{'0 fallas' if not fallas else str(fallas) + ' falla(s)'}.")
    return 1 if fallas else 0


if __name__ == "__main__":
    sys.exit(main())
