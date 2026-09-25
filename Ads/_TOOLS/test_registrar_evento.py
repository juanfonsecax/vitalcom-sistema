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

T7 (auditoría 22-sep-2026) agrega las reglas de `validar()` que el archivo original no cubría,
todas con eventos que NO son LANZAMIENTO (para no volver a pasar por flujo.gate_entrada):
  · producto_key sin fila en _DIM_PRODUCTOS.csv se refusa; GLOBAL se acepta siempre.
  · evento debe cumplir MAYÚSCULAS_CON_GUION_BAJO (regex `[A-Z][A-Z0-9_]*`) — `main()` ya
    mayusculiza lo que llega por --evento, así que la refusión real solo se ve con un carácter
    fuera del alfabeto (guion medio, espacio), no con minúsculas.
  · motivo y fuente_decision vacíos se refusan.
  · CAMBIO_PRESUPUESTO exige --antes/--despues numéricos.
  · una subida de presupuesto por encima de surfing_pct se refusa salvo --forzar.
  · --dry-run no escribe nada, ni siquiera cuando la fila sería válida.
  · una fila con coma en el motivo hace round-trip exacto por csv (queda entre comillas en el
    archivo, invariante 11).

P3 T4 — `anexar()` escribe siempre por Postgres (db/escribir.py): la VERDAD de _EVENTOS.csv pasa a
`raw.evento`/`core.evento`. Aislamiento CRÍTICO (mismo patrón que db/test_db_write_path.py): fuerza
`PGDATABASE=vitalcom_test` ANTES de importar registrar_evento, cada escenario bootstrapea
raw.evento/raw.raw_import en su PROPIO tenant único, y nunca toca `vitalcom` real. Se salta con
aviso si `vitalcom_test` no está disponible en este entorno.

USO:  python Ads/_TOOLS/test_registrar_evento.py     (exit 0 = pasa, 1 = falla)
"""
import contextlib
import csv
import datetime
import io
import os
import sys
import tempfile
import uuid

# Aislamiento CRÍTICO: forzar vitalcom_test ANTES de importar registrar_evento (que a su vez
# importa db/cargar.py) — nunca debe conectar a `vitalcom` real durante estas pruebas.
os.environ["PGDATABASE"] = "vitalcom_test"

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import registrar_evento as re_  # noqa: E402
import test_flujo as tf  # noqa: E402

# registrar_evento.py ya insertó BASE/db en sys.path al importarse; estos quedan disponibles
# directo, sin repetir la ruta.
import nucleo as db_nucleo  # noqa: E402

EVENTOS_COLS = ["fecha", "producto_key", "cuenta_alias", "campana_clave", "conjunto_meta", "evento",
                "valor_antes", "valor_despues", "motivo", "fuente_decision"]


def _preparar_base_de_pruebas():
    try:
        if re_.db_cargar.asegurar_base_de_datos("vitalcom_test"):
            re_.db_cargar.aplicar_schema(dbname="vitalcom_test")
    except Exception:
        pass


_preparar_base_de_pruebas()


def _conectar_seguro():
    con = re_.db_cargar.conectar()
    if con.info.dbname == "vitalcom":
        con.close()
        raise RuntimeError(
            "test_registrar_evento.py intentó conectarse a 'vitalcom' en vez de 'vitalcom_test'. "
            "Abortado antes de tocar nada.")
    return con


def _db_disponible():
    try:
        con = _conectar_seguro()
        con.close()
        return True
    except Exception:
        return False


DB_DISPONIBLE = _db_disponible()


def _tenant_unico(nombre):
    return "test_regev_%s_%s" % (nombre, uuid.uuid4().hex[:8])


def _bootstrap_evento(prod_dir, tenant):
    """Carga el _EVENTOS.csv YA escrito por el fixture en raw.evento, bajo `tenant`, y deja el
    registro en raw.raw_import -- para que verificar_csv_sincronizado() no aborte por "nunca se
    importó" en la primera escritura real de la prueba. Mismo patrón que
    db/test_db_write_path.py::_fixture()."""
    con = _conectar_seguro()
    try:
        with con:
            with con.cursor() as cur:
                n, sha = re_.db_cargar.cargar_tabla(cur, tenant, "evento", "_EVENTOS.csv", False, prod_dir)
                cur.execute(
                    "INSERT INTO raw.raw_import (tenant_id, archivo, sha256, filas) "
                    "VALUES (%s, %s, %s, %s)", (tenant, "_EVENTOS.csv", sha, n))
                db_nucleo.construir_core(cur, tenant)
    finally:
        con.close()


def _informe(ok, texto, detalle=""):
    print(("  OK     " if ok else "  FALLA  ") + texto + ("" if ok else "\n         %r" % (detalle,)))
    return 0 if ok else 1


def _fixture_lanzamiento(gate_cumplido):
    """PX en FASE 1, con (o sin) ángulo ganador confirmado — el gate real de entrada a F2.
    Devuelve (base, tenant); bootstrapea raw.evento en un tenant único para esta corrida."""
    tmp = tf.fixture_escalar_flaco(ventas_nuevo=3, con_probado=gate_cumplido)
    tf._escribir_csv(os.path.join(tmp, "PRODUCTOS"), "_EVENTOS.csv", EVENTOS_COLS, [])
    tenant = _tenant_unico("lanzamiento")
    if DB_DISPONIBLE:
        _bootstrap_evento(os.path.join(tmp, "PRODUCTOS"), tenant)
    return tmp, tenant


def _leer_eventos(base):
    ruta = os.path.join(base, "PRODUCTOS", "_EVENTOS.csv")
    if not os.path.exists(ruta):
        return []
    with io.open(ruta, encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def _fixture_validacion(surfing=None):
    """Base mínima para probar `validar()` con eventos que NO son LANZAMIENTO: no toca
    _DIM_CONJUNTOS.csv ni _FACT_VENTAS.csv porque flujo.gate_entrada nunca se consulta acá.
    Devuelve (base, tenant); bootstrapea raw.evento en un tenant único para esta corrida."""
    tmp = tempfile.mkdtemp(prefix="re_valid_")
    prod = os.path.join(tmp, "PRODUCTOS")
    os.makedirs(prod)
    tf._escribir_csv(prod, "_DIM_PRODUCTOS.csv", ["producto_key", "nombre_display", "estado", "fase"],
                      [["PX", "PX", "VIVO", "F1"]])
    filas_params = [["min_ventas_ganador", "5", "ventas", "test", "piso del ganador"]]
    if surfing is not None:
        filas_params.append(["surfing_pct", str(surfing), "%", "test", "tope de subida diaria"])
    tf._escribir_csv(prod, "_PARAMETROS_DECISION.csv", ["parametro", "valor", "unidad", "dueno", "por_que"],
                      filas_params)
    tf._escribir_csv(prod, "_EVENTOS.csv", EVENTOS_COLS, [])
    tenant = _tenant_unico("validacion")
    if DB_DISPONIBLE:
        _bootstrap_evento(prod, tenant)
    return tmp, tenant


def _correr_main(base, argv, tenant):
    previo = (re_.BASE, re_.PROD, re_.EVENTOS, re_.TENANT_ID, re_.BKDIR, sys.argv)
    re_.BASE = base
    re_.PROD = os.path.join(base, "PRODUCTOS")
    re_.EVENTOS = os.path.join(re_.PROD, "_EVENTOS.csv")
    re_.TENANT_ID = tenant
    re_.BKDIR = os.path.join(base, "backups_csv")
    sys.argv = ["registrar_evento.py"] + argv
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            code = re_.main()
        return code, buf.getvalue(), None
    except Exception as e:                       # noqa: BLE001 — el test reporta el crash, no lo esconde
        return None, buf.getvalue(), e
    finally:
        re_.BASE, re_.PROD, re_.EVENTOS, re_.TENANT_ID, re_.BKDIR, sys.argv = previo


def test_lanzamiento_gate_cumplido_registra_sin_excepcion():
    if not DB_DISPONIBLE:
        print("  SKIP   Postgres/vitalcom_test no disponible en este entorno")
        return 0
    base, tenant = _fixture_lanzamiento(gate_cumplido=True)
    code, out, err = _correr_main(base, ["--producto", "PX", "--evento", "LANZAMIENTO", "--fase", "2",
                                          "--motivo", "lanzamiento normal", "--fuente", "test",
                                          "--fecha", "2026-09-14"], tenant)
    filas = _leer_eventos(base)
    ok = (err is None and code == 0 and len(filas) == 1 and filas[0]["evento"] == "LANZAMIENTO"
          and not any(f["evento"] == "EXCEPCION" for f in filas))
    return _informe(ok, "gate cumplido: LANZAMIENTO se registra y no hay EXCEPCION",
                     (code, err, [f["evento"] for f in filas]))


def test_lanzamiento_gate_incumplido_sin_excepcion_refusa():
    if not DB_DISPONIBLE:
        print("  SKIP   Postgres/vitalcom_test no disponible en este entorno")
        return 0
    base, tenant = _fixture_lanzamiento(gate_cumplido=False)
    code, out, err = _correr_main(base, ["--producto", "PX", "--evento", "LANZAMIENTO", "--fase", "2",
                                          "--motivo", "intento sin gate", "--fuente", "test",
                                          "--fecha", "2026-09-14"], tenant)
    filas = _leer_eventos(base)
    ok = err is None and code == 1 and not filas and "gate de entrada" in out
    return _informe(ok, "gate incumplido sin --excepcion: refusa, nada se escribe",
                     (code, err, filas, out[:200]))


def test_lanzamiento_gate_incumplido_excepcion_vacia_refusa_igual():
    if not DB_DISPONIBLE:
        print("  SKIP   Postgres/vitalcom_test no disponible en este entorno")
        return 0
    base, tenant = _fixture_lanzamiento(gate_cumplido=False)
    code, out, err = _correr_main(base, ["--producto", "PX", "--evento", "LANZAMIENTO", "--fase", "2",
                                          "--motivo", "intento", "--fuente", "test",
                                          "--fecha", "2026-09-14", "--excepcion", ""], tenant)
    filas = _leer_eventos(base)
    ok = err is None and code == 1 and not filas
    return _informe(ok, "--excepcion \"\" (vacío) se trata como ausente: refusa igual", (code, err, filas))


def test_lanzamiento_gate_incumplido_con_excepcion_procede_y_registra_una_fila():
    if not DB_DISPONIBLE:
        print("  SKIP   Postgres/vitalcom_test no disponible en este entorno")
        return 0
    base, tenant = _fixture_lanzamiento(gate_cumplido=False)
    code, out, err = _correr_main(base, ["--producto", "PX", "--evento", "LANZAMIENTO", "--fase", "2",
                                          "--motivo", "escalar igual", "--fuente", "test",
                                          "--fecha", "2026-09-14", "--excepcion", "decisión del operador"], tenant)
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
    if not DB_DISPONIBLE:
        print("  SKIP   Postgres/vitalcom_test no disponible en este entorno")
        return 0
    base, tenant = _fixture_lanzamiento(gate_cumplido=True)
    code, out, err = _correr_main(base, ["--producto", "PX", "--evento", "LANZAMIENTO",
                                          "--campana", "GTR7_PX_CONCEPTOS-A_20260924",
                                          "--motivo", "sin --fase, lo trae la campaña", "--fuente", "test",
                                          "--fecha", "2026-09-14"], tenant)
    filas = _leer_eventos(base)
    ok = err is None and code == 0 and len(filas) == 1
    return _informe(ok, "sin --fase: se resuelve del token CONCEPTOS en --campana (fase 2)",
                     (code, err, out[:200]))


def test_lanzamiento_sin_fase_ni_token_pide_fase():
    if not DB_DISPONIBLE:
        print("  SKIP   Postgres/vitalcom_test no disponible en este entorno")
        return 0
    base, tenant = _fixture_lanzamiento(gate_cumplido=True)
    code, out, err = _correr_main(base, ["--producto", "PX", "--evento", "LANZAMIENTO",
                                          "--motivo", "sin pista de fase", "--fuente", "test",
                                          "--fecha", "2026-09-14"], tenant)
    filas = _leer_eventos(base)
    ok = err is None and code == 1 and not filas and "--fase" in out
    return _informe(ok, "sin --fase ni token en --campana: se detiene y pide --fase", (code, err, out[:200]))


def test_resolver_fase_token_explora_resuelve_a_fase_3():
    """P12/T12: fase 3 tiene DOS tokens (ESCALA y EXPLORA) — el mini-F1 de F3.exploracion nace
    EXPLORA, no ESCALA-{angulo}, y tiene que resolver a la MISMA fase 3 que el escalado."""
    fase, motivo = re_.resolver_fase(None, "GTR7_TURMERIC_EXPLORA_20260929")
    ok = fase == "3" and "EXPLORA" in motivo
    return _informe(ok, "el token EXPLORA en --campana resuelve a fase 3, igual que ESCALA", (fase, motivo))


def test_resolver_fase_escala_sigue_resolviendo_a_fase_3():
    fase, motivo = re_.resolver_fase(None, "GTR7_TURMERIC_ESCALA-C6-UNBOXING_20260910")
    ok = fase == "3" and "ESCALA" in motivo
    return _informe(ok, "el token ESCALA sigue resolviendo a fase 3 (regresión: no se rompió al agregar EXPLORA)",
                     (fase, motivo))


def test_resolver_fase_escala_y_explora_en_la_misma_campana_no_es_ambigua():
    """Los dos tokens de fase 3 en el MISMO nombre resuelven a la MISMA fase — no es la
    ambigüedad de "dos fases distintas" que sí detiene el registro (esa es entre fases
    DIFERENTES, p.ej. TEST y CONCEPTOS a la vez)."""
    fase, motivo = re_.resolver_fase(None, "GTR7_TURMERIC_ESCALA-EXPLORA_20260929")
    ok = fase == "3"
    return _informe(ok, "ESCALA y EXPLORA en el mismo nombre (mismo caso de fase 3) no son ambiguos",
                     (fase, motivo))


def test_resolver_fase_dos_fases_distintas_sigue_siendo_ambigua():
    fase, motivo = re_.resolver_fase(None, "GTR7_TURMERIC_TEST_CONCEPTOS-A_20260924")
    ok = fase is None and "ambigua" in motivo
    return _informe(ok, "dos fases DISTINTAS (TEST y CONCEPTOS) en el mismo nombre siguen siendo ambiguas",
                     (fase, motivo))


def test_evento_no_lanzamiento_no_exige_fase_ni_gate():
    if not DB_DISPONIBLE:
        print("  SKIP   Postgres/vitalcom_test no disponible en este entorno")
        return 0
    base, tenant = _fixture_lanzamiento(gate_cumplido=False)   # gate F2 incumplido a propósito: no debe importar
    code, out, err = _correr_main(base, ["--producto", "PX", "--evento", "CAMBIO_PRESUPUESTO",
                                          "--conjunto", "GTR7_PX_NUEVO_R1", "--antes", "5", "--despues", "5.5",
                                          "--motivo", "surfing", "--fuente", "test", "--fecha", "2026-09-14"], tenant)
    filas = _leer_eventos(base)
    ok = err is None and code == 0 and len(filas) == 1 and filas[0]["evento"] == "CAMBIO_PRESUPUESTO"
    return _informe(ok, "un evento que no es LANZAMIENTO no pide fase ni consulta el gate",
                     (code, err, filas))


def test_producto_desconocido_se_refusa():
    if not DB_DISPONIBLE:
        print("  SKIP   Postgres/vitalcom_test no disponible en este entorno")
        return 0
    base, tenant = _fixture_validacion()
    code, out, err = _correr_main(base, ["--producto", "NOPE", "--evento", "CAMBIO_BOT",
                                          "--motivo", "ajuste", "--fuente", "test", "--fecha", "2026-09-23"], tenant)
    filas = _leer_eventos(base)
    ok = err is None and code == 1 and not filas and "NOPE" in out
    return _informe(ok, "producto_key sin fila en _DIM_PRODUCTOS.csv: se refusa, nada se escribe",
                     (code, err, out[:200]))


def test_producto_global_se_acepta():
    if not DB_DISPONIBLE:
        print("  SKIP   Postgres/vitalcom_test no disponible en este entorno")
        return 0
    base, tenant = _fixture_validacion()
    code, out, err = _correr_main(base, ["--producto", "GLOBAL", "--evento", "CAMBIO_BOT",
                                          "--motivo", "ajuste global", "--fuente", "test", "--fecha", "2026-09-23"], tenant)
    filas = _leer_eventos(base)
    ok = err is None and code == 0 and len(filas) == 1 and filas[0]["producto_key"] == "GLOBAL"
    return _informe(ok, "producto_key GLOBAL se acepta siempre, aunque no tenga fila en _DIM_PRODUCTOS.csv",
                     (code, err, filas))


def test_evento_con_caracter_invalido_se_refusa():
    # main() ya hace .upper() sobre --evento antes de validar, así que una minúscula normal
    # nunca llega a fallar la regex; hace falta un carácter fuera de [A-Z0-9_] (acá, un guion).
    if not DB_DISPONIBLE:
        print("  SKIP   Postgres/vitalcom_test no disponible en este entorno")
        return 0
    base, tenant = _fixture_validacion()
    code, out, err = _correr_main(base, ["--producto", "PX", "--evento", "cambio-bot",
                                          "--motivo", "ajuste", "--fuente", "test", "--fecha", "2026-09-23"], tenant)
    filas = _leer_eventos(base)
    ok = err is None and code == 1 and not filas and "MAYÚSCULAS" in out
    return _informe(ok, "evento 'CAMBIO-BOT' (guion, no MAYÚSCULAS_CON_GUION_BAJO): se refusa",
                     (code, err, out[:200]))


def test_motivo_vacio_se_refusa():
    if not DB_DISPONIBLE:
        print("  SKIP   Postgres/vitalcom_test no disponible en este entorno")
        return 0
    base, tenant = _fixture_validacion()
    code, out, err = _correr_main(base, ["--producto", "PX", "--evento", "CAMBIO_BOT",
                                          "--motivo", "", "--fuente", "test", "--fecha", "2026-09-23"], tenant)
    filas = _leer_eventos(base)
    ok = err is None and code == 1 and not filas and "motivo" in out
    return _informe(ok, "motivo vacío: se refusa, nada se escribe", (code, err, out[:200]))


def test_fuente_vacia_se_refusa():
    if not DB_DISPONIBLE:
        print("  SKIP   Postgres/vitalcom_test no disponible en este entorno")
        return 0
    base, tenant = _fixture_validacion()
    code, out, err = _correr_main(base, ["--producto", "PX", "--evento", "CAMBIO_BOT",
                                          "--motivo", "ajuste", "--fuente", "", "--fecha", "2026-09-23"], tenant)
    filas = _leer_eventos(base)
    ok = err is None and code == 1 and not filas and "fuente_decision" in out
    return _informe(ok, "fuente_decision vacía: se refusa, nada se escribe", (code, err, out[:200]))


def test_cambio_presupuesto_no_numerico_se_refusa():
    if not DB_DISPONIBLE:
        print("  SKIP   Postgres/vitalcom_test no disponible en este entorno")
        return 0
    base, tenant = _fixture_validacion()
    code, out, err = _correr_main(base, ["--producto", "PX", "--evento", "CAMBIO_PRESUPUESTO",
                                          "--conjunto", "GTR7_PX_NUEVO_R1", "--antes", "abc", "--despues", "5",
                                          "--motivo", "ajuste", "--fuente", "test", "--fecha", "2026-09-23"], tenant)
    filas = _leer_eventos(base)
    ok = err is None and code == 1 and not filas and "numéricos" in out
    return _informe(ok, "CAMBIO_PRESUPUESTO con --antes no numérico: se refusa", (code, err, out[:200]))


def test_cambio_presupuesto_dentro_de_surfing_se_acepta():
    if not DB_DISPONIBLE:
        print("  SKIP   Postgres/vitalcom_test no disponible en este entorno")
        return 0
    base, tenant = _fixture_validacion(surfing=20.0)
    code, out, err = _correr_main(base, ["--producto", "PX", "--evento", "CAMBIO_PRESUPUESTO",
                                          "--conjunto", "GTR7_PX_NUEVO_R1", "--antes", "10", "--despues", "11.5",
                                          "--motivo", "surfing", "--fuente", "test", "--fecha", "2026-09-23"], tenant)
    filas = _leer_eventos(base)
    ok = err is None and code == 0 and len(filas) == 1
    return _informe(ok, "subida de 15% con surfing_pct=20%: dentro de tolerancia, se acepta",
                     (code, err, filas))


def test_cambio_presupuesto_sobre_surfing_se_refusa_sin_forzar():
    if not DB_DISPONIBLE:
        print("  SKIP   Postgres/vitalcom_test no disponible en este entorno")
        return 0
    base, tenant = _fixture_validacion(surfing=20.0)
    code, out, err = _correr_main(base, ["--producto", "PX", "--evento", "CAMBIO_PRESUPUESTO",
                                          "--conjunto", "GTR7_PX_NUEVO_R1", "--antes", "10", "--despues", "13",
                                          "--motivo", "subida grande", "--fuente", "test", "--fecha", "2026-09-23"], tenant)
    filas = _leer_eventos(base)
    ok = err is None and code == 1 and not filas and "surfing_pct" in out
    return _informe(ok, "subida de 30% con surfing_pct=20% y SIN --forzar: se refusa",
                     (code, err, out[:200]))


def test_cambio_presupuesto_sobre_surfing_con_forzar_se_acepta():
    if not DB_DISPONIBLE:
        print("  SKIP   Postgres/vitalcom_test no disponible en este entorno")
        return 0
    base, tenant = _fixture_validacion(surfing=20.0)
    code, out, err = _correr_main(base, ["--producto", "PX", "--evento", "CAMBIO_PRESUPUESTO",
                                          "--conjunto", "GTR7_PX_NUEVO_R1", "--antes", "10", "--despues", "13",
                                          "--motivo", "subida grande deliberada", "--fuente", "test",
                                          "--fecha", "2026-09-23", "--forzar"], tenant)
    filas = _leer_eventos(base)
    ok = err is None and code == 0 and len(filas) == 1
    return _informe(ok, "subida de 30% con surfing_pct=20% y --forzar: se acepta", (code, err, filas))


def test_dry_run_no_escribe():
    base, tenant = _fixture_validacion()
    code, out, err = _correr_main(base, ["--producto", "PX", "--evento", "CAMBIO_BOT",
                                          "--motivo", "ajuste", "--fuente", "test", "--fecha", "2026-09-23",
                                          "--dry-run"], tenant)
    filas = _leer_eventos(base)
    ok = err is None and code == 0 and not filas and "dry-run" in out
    return _informe(ok, "--dry-run: muestra la fila y NO escribe nada, ni siendo válida",
                     (code, err, filas, out[:200]))


def test_motivo_con_coma_hace_round_trip_por_csv():
    if not DB_DISPONIBLE:
        print("  SKIP   Postgres/vitalcom_test no disponible en este entorno")
        return 0
    base, tenant = _fixture_validacion()
    motivo = "ajuste, revisado por el operador"
    code, out, err = _correr_main(base, ["--producto", "PX", "--evento", "CAMBIO_BOT",
                                          "--motivo", motivo, "--fuente", "test", "--fecha", "2026-09-23"], tenant)
    filas = _leer_eventos(base)
    ok = err is None and code == 0 and len(filas) == 1 and filas[0]["motivo"] == motivo
    with io.open(os.path.join(base, "PRODUCTOS", "_EVENTOS.csv"), encoding="utf-8") as fh:
        crudo = fh.read()
    ok = ok and ('"%s"' % motivo) in crudo
    return _informe(ok, "motivo con coma: round-trip exacto por csv, entre comillas en el archivo (invariante 11)",
                     (filas, crudo))


def main():
    pruebas = [
        test_lanzamiento_gate_cumplido_registra_sin_excepcion,
        test_lanzamiento_gate_incumplido_sin_excepcion_refusa,
        test_lanzamiento_gate_incumplido_excepcion_vacia_refusa_igual,
        test_lanzamiento_gate_incumplido_con_excepcion_procede_y_registra_una_fila,
        test_lanzamiento_fase_por_token_de_campana,
        test_lanzamiento_sin_fase_ni_token_pide_fase,
        test_resolver_fase_token_explora_resuelve_a_fase_3,
        test_resolver_fase_escala_sigue_resolviendo_a_fase_3,
        test_resolver_fase_escala_y_explora_en_la_misma_campana_no_es_ambigua,
        test_resolver_fase_dos_fases_distintas_sigue_siendo_ambigua,
        test_evento_no_lanzamiento_no_exige_fase_ni_gate,
        test_producto_desconocido_se_refusa,
        test_producto_global_se_acepta,
        test_evento_con_caracter_invalido_se_refusa,
        test_motivo_vacio_se_refusa,
        test_fuente_vacia_se_refusa,
        test_cambio_presupuesto_no_numerico_se_refusa,
        test_cambio_presupuesto_dentro_de_surfing_se_acepta,
        test_cambio_presupuesto_sobre_surfing_se_refusa_sin_forzar,
        test_cambio_presupuesto_sobre_surfing_con_forzar_se_acepta,
        test_dry_run_no_escribe,
        test_motivo_con_coma_hace_round_trip_por_csv,
    ]
    fallas = sum(p() for p in pruebas)
    print(f"\n{'0 fallas' if not fallas else str(fallas) + ' falla(s)'}.")
    return 1 if fallas else 0


if __name__ == "__main__":
    sys.exit(main())
