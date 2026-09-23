#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_verificar_voz.py — GATE del dueño de _VOZ_CLIENTE.csv (T10, g07-cimientos, 23-sep-2026).

Congela: violaciones de esquema, verificación con fetch inyectado (encontrada / no
encontrada / falla de descarga), normalización de acentos/HTML, conteo de citas
casi-idénticas, el contrato de lectura-por-defecto (nunca toca el CSV sin --escribir), el
backup real bajo _RESPALDOS/ al escribir, y el escritor `--agregar-json` (agrega PENDIENTE,
rechaza duplicados). Nunca toca la red ni el _VOZ_CLIENTE.csv real: todo corre sobre
directorios temporales y un `fetch` inyectado.

USO:  python Ads/_TOOLS/test_verificar_voz.py     (exit 0 = pasa, 1 = falla)
"""
import csv
import io
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import verificar_voz as vv  # noqa: E402


def _fila(**over):
    base = {
        "producto_key": "TINNIDROP", "voz_id": "V001", "variable": "dolor",
        "cita_textual": "siento que boto el dinero en pastillas que no me hacen nada",
        "url": "https://reddit.com/r/tinnitus/comments/abc123",
        "fuente_tipo": "reddit", "fecha_captura": "2026-09-20", "pais": "GT", "idioma": "es",
        "nivel_conciencia": "2", "embudo": "TOFU", "angulo_key": "PERDIDA_AUDITIVA",
        "estado": "PENDIENTE", "verificado_el": "",
    }
    base.update(over)
    return base


# ─────────────────────────────────────────────────────────────────────────────
# ESQUEMA
# ─────────────────────────────────────────────────────────────────────────────

def test_fila_valida_no_genera_problemas():
    problemas = vv.validar_filas([_fila()])
    ok = problemas == []
    print(("  OK     " if ok else "  FALLA  ") + "una fila completa y válida no genera error"
          + ("" if ok else f"\n         problemas={problemas}"))
    return 0 if ok else 1


def test_url_vacia_o_sin_esquema_falla():
    p1 = vv.validar_filas([_fila(url="")])
    p2 = vv.validar_filas([_fila(url="reddit.com/sin/esquema")])
    ok = len(p1) == 1 and "url" in p1[0] and len(p2) == 1 and "http" in p2[0]
    print(("  OK     " if ok else "  FALLA  ") + "url vacía o sin http(s) falla"
          + ("" if ok else f"\n         p1={p1} p2={p2}"))
    return 0 if ok else 1


def test_cita_vacia_falla():
    problemas = vv.validar_filas([_fila(cita_textual="")])
    ok = len(problemas) == 1 and "cita_textual" in problemas[0]
    print(("  OK     " if ok else "  FALLA  ") + "cita_textual vacía falla")
    return 0 if ok else 1


def test_enums_invalidos_fallan():
    problemas = vv.validar_filas([_fila(variable="rabia", fuente_tipo="tiktok", embudo="X",
                                        estado="OTRO")])
    ok = len(problemas) == 4
    print(("  OK     " if ok else "  FALLA  ")
          + "variable/fuente_tipo/embudo/estado fuera de vocabulario fallan los 4"
          + ("" if ok else f"\n         problemas={problemas}"))
    return 0 if ok else 1


def test_voz_id_duplicado_por_producto_falla():
    filas = [_fila(voz_id="V001"), _fila(voz_id="V001")]
    problemas = vv.validar_filas(filas)
    ok = any("duplicado" in p for p in problemas)
    print(("  OK     " if ok else "  FALLA  ")
          + "voz_id repetido para el mismo producto_key falla"
          + ("" if ok else f"\n         problemas={problemas}"))
    return 0 if ok else 1


def test_voz_id_repetido_en_otro_producto_no_falla():
    filas = [_fila(producto_key="A", voz_id="V001"), _fila(producto_key="B", voz_id="V001")]
    problemas = vv.validar_filas(filas)
    ok = problemas == []
    print(("  OK     " if ok else "  FALLA  ")
          + "el mismo voz_id en dos productos distintos no es un duplicado"
          + ("" if ok else f"\n         problemas={problemas}"))
    return 0 if ok else 1


# ─────────────────────────────────────────────────────────────────────────────
# NORMALIZACIÓN
# ─────────────────────────────────────────────────────────────────────────────

def test_normalizar_quita_acentos_html_y_tags():
    cruda = "Sentí <b>much&iacute;simo</b> dolor,  ¡de verdad!"
    normalizada = vv.normalizar(cruda)
    ok = normalizada == "senti muchisimo dolor de verdad"
    print(("  OK     " if ok else "  FALLA  ")
          + "normalizar() quita tags, des-escapa HTML, quita acentos/puntuación y colapsa espacios"
          + ("" if ok else f"\n         obtenido={normalizada!r}"))
    return 0 if ok else 1


# ─────────────────────────────────────────────────────────────────────────────
# VERIFICACIÓN (fetch inyectado — nunca red real)
# ─────────────────────────────────────────────────────────────────────────────

def test_verificar_fila_encontrada():
    fila = _fila(cita_textual="me siento agotada todo el día")
    fetch = lambda url: "<p>Comentario: ME SIENTO AGOTADA TODO EL DÍA, ya no sé qué hacer.</p>"
    estado, motivo = vv.verificar_fila(fila, fetch=fetch)
    ok = estado == "VERIFICADA" and motivo == ""
    print(("  OK     " if ok else "  FALLA  ")
          + "la cita se encuentra (normalizada) en el contenido -> VERIFICADA"
          + ("" if ok else f"\n         estado={estado!r} motivo={motivo!r}"))
    return 0 if ok else 1


def test_verificar_fila_no_encontrada():
    fila = _fila(cita_textual="me siento agotada todo el día")
    fetch = lambda url: "esta página no menciona nada parecido"
    estado, motivo = vv.verificar_fila(fila, fetch=fetch)
    ok = estado == "NO_VERIFICADA" and "no aparece" in motivo
    print(("  OK     " if ok else "  FALLA  ")
          + "la cita no está en el contenido -> NO_VERIFICADA con motivo explícito"
          + ("" if ok else f"\n         estado={estado!r} motivo={motivo!r}"))
    return 0 if ok else 1


def test_verificar_fila_error_de_fetch():
    fila = _fila()

    def fetch_roto(url):
        raise OSError("timeout")

    estado, motivo = vv.verificar_fila(fila, fetch=fetch_roto)
    ok = estado == "NO_VERIFICADA" and "descargar" in motivo
    print(("  OK     " if ok else "  FALLA  ")
          + "un fetch que lanza excepción -> NO_VERIFICADA (nunca crashea, nunca VERIFICADA "
          + "por omisión)"
          + ("" if ok else f"\n         estado={estado!r} motivo={motivo!r}"))
    return 0 if ok else 1


# ─────────────────────────────────────────────────────────────────────────────
# FRECUENCIA / DEDUPE
# ─────────────────────────────────────────────────────────────────────────────

def test_contar_frecuencia_agrupa_citas_casi_identicas():
    filas = [
        _fila(voz_id="V001", cita_textual="Siento que boto el dinero"),
        _fila(voz_id="V002", cita_textual="siento que BOTO el dinero!!"),
        _fila(voz_id="V003", cita_textual="un dolor totalmente distinto"),
    ]
    conteo = vv.contar_frecuencia(filas)
    llave_repetida = ("TINNIDROP", "dolor", vv.normalizar("siento que boto el dinero"))
    ok = conteo.get(llave_repetida) == 2
    print(("  OK     " if ok else "  FALLA  ")
          + "dos citas casi-idénticas (may/punct) se cuentan como la misma"
          + ("" if ok else f"\n         conteo={conteo}"))
    return 0 if ok else 1


# ─────────────────────────────────────────────────────────────────────────────
# CLI: LEER ES EL DEFAULT, --escribir ES LO ÚNICO QUE ESCRIBE
# ─────────────────────────────────────────────────────────────────────────────

def test_main_sin_escribir_no_toca_el_csv(tmp):
    ruta = os.path.join(tmp, "_VOZ_CLIENTE.csv")
    with io.open(ruta, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=vv.COLS)
        w.writeheader()
        w.writerow(_fila())
    antes = io.open(ruta, "rb").read()
    previo_voz, previo_params = vv.VOZ_PATH, vv.PARAMS_PATH
    vv.VOZ_PATH = ruta
    vv.PARAMS_PATH = os.path.join(tmp, "no_existe.csv")
    try:
        rc = vv.main(["--producto", "TINNIDROP"])
    finally:
        vv.VOZ_PATH, vv.PARAMS_PATH = previo_voz, previo_params
    despues = io.open(ruta, "rb").read()
    ok = rc == 0 and antes == despues and not os.path.isdir(os.path.join(tmp, "_RESPALDOS"))
    print(("  OK     " if ok else "  FALLA  ")
          + "main() sin --escribir deja el CSV byte-idéntico y no crea _RESPALDOS/"
          + ("" if ok else f"\n         rc={rc}"))
    return 0 if ok else 1


def test_persistir_verificaciones_escribe_y_respalda(tmp):
    ruta = os.path.join(tmp, "_VOZ_CLIENTE.csv")
    bkdir = vv.upsert_fact.respaldos_dir(tmp, "backups_csv")
    fila = _fila()
    with io.open(ruta, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=vv.COLS)
        w.writeheader()
        w.writerow(fila)
    resultado = vv.persistir_verificaciones([(fila, "VERIFICADA", "")], path=ruta, bkdir=bkdir)
    filas_despues = vv.leer_csv(ruta)
    ok = (resultado[0] == 1  # 1 reemplazada
          and filas_despues[0]["estado"] == "VERIFICADA"
          and filas_despues[0]["verificado_el"]
          and os.path.isdir(bkdir) and len(os.listdir(bkdir)) == 1)
    print(("  OK     " if ok else "  FALLA  ")
          + "persistir_verificaciones() actualiza estado/verificado_el y deja backup en "
          + "_RESPALDOS/"
          + ("" if ok else f"\n         resultado={resultado} filas={filas_despues}"))
    return 0 if ok else 1


# ─────────────────────────────────────────────────────────────────────────────
# --agregar-json
# ─────────────────────────────────────────────────────────────────────────────

def test_agregar_pendientes_agrega_filas_validas(tmp):
    ruta = os.path.join(tmp, "_VOZ_CLIENTE.csv")
    bkdir = vv.upsert_fact.respaldos_dir(tmp, "backups_csv")
    nueva = _fila(voz_id="V099", estado="")
    problemas, resultado = vv.agregar_pendientes([nueva], path=ruta, bkdir=bkdir)
    filas = vv.leer_csv(ruta)
    ok = (problemas == [] and resultado[1] == 1  # 1 nueva
          and len(filas) == 1 and filas[0]["estado"] == "PENDIENTE")
    print(("  OK     " if ok else "  FALLA  ")
          + "agregar_pendientes() agrega una fila nueva forzada a estado PENDIENTE"
          + ("" if ok else f"\n         problemas={problemas} filas={filas}"))
    return 0 if ok else 1


def test_agregar_pendientes_rechaza_fila_invalida(tmp):
    ruta = os.path.join(tmp, "_VOZ_CLIENTE.csv")
    bkdir = vv.upsert_fact.respaldos_dir(tmp, "backups_csv")
    invalida = _fila(url="no-es-una-url")
    problemas, resultado = vv.agregar_pendientes([invalida], path=ruta, bkdir=bkdir)
    ok = problemas != [] and resultado is None and not os.path.exists(ruta)
    print(("  OK     " if ok else "  FALLA  ")
          + "una fila con esquema inválido se rechaza completa y no escribe nada"
          + ("" if ok else f"\n         problemas={problemas} resultado={resultado}"))
    return 0 if ok else 1


def test_agregar_pendientes_rechaza_voz_id_ya_existente(tmp):
    ruta = os.path.join(tmp, "_VOZ_CLIENTE.csv")
    bkdir = vv.upsert_fact.respaldos_dir(tmp, "backups_csv")
    existente = _fila(voz_id="V001")
    with io.open(ruta, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=vv.COLS)
        w.writeheader()
        w.writerow(existente)
    repetida = _fila(voz_id="V001", cita_textual="otra cita distinta")
    problemas, resultado = vv.agregar_pendientes([repetida], path=ruta, bkdir=bkdir)
    filas = vv.leer_csv(ruta)
    ok = (problemas != [] and any("ya existe" in p for p in problemas) and resultado is None
          and filas[0]["cita_textual"] == existente["cita_textual"])
    print(("  OK     " if ok else "  FALLA  ")
          + "un voz_id ya existente para el mismo producto_key se rechaza (no pisa evidencia)"
          + ("" if ok else f"\n         problemas={problemas} filas={filas}"))
    return 0 if ok else 1


# ─────────────────────────────────────────────────────────────────────────────
# min_voz_requerido
# ─────────────────────────────────────────────────────────────────────────────

def test_min_voz_requerido_default_sin_csv(tmp):
    valor = vv.min_voz_requerido(os.path.join(tmp, "no_existe.csv"))
    ok = valor == vv.MIN_VOZ_VERIFICADA_POR_ANGULO
    print(("  OK     " if ok else "  FALLA  ")
          + "sin fila en _PARAMETROS_DECISION.csv, usa el default del módulo")
    return 0 if ok else 1


def test_min_voz_requerido_lee_override(tmp):
    ruta = os.path.join(tmp, "_PARAMETROS_DECISION.csv")
    with io.open(ruta, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["parametro", "valor", "unidad", "dueno", "por_que"])
        w.writerow(["min_voz_verificada_por_angulo", "5", "voz_id", "orquestador", "prueba"])
    valor = vv.min_voz_requerido(ruta)
    ok = valor == 5
    print(("  OK     " if ok else "  FALLA  ")
          + "una fila min_voz_verificada_por_angulo en _PARAMETROS_DECISION.csv la overridea"
          + ("" if ok else f"\n         valor={valor}"))
    return 0 if ok else 1


def main():
    fallas = 0
    fallas += test_fila_valida_no_genera_problemas()
    fallas += test_url_vacia_o_sin_esquema_falla()
    fallas += test_cita_vacia_falla()
    fallas += test_enums_invalidos_fallan()
    fallas += test_voz_id_duplicado_por_producto_falla()
    fallas += test_voz_id_repetido_en_otro_producto_no_falla()
    fallas += test_normalizar_quita_acentos_html_y_tags()
    fallas += test_verificar_fila_encontrada()
    fallas += test_verificar_fila_no_encontrada()
    fallas += test_verificar_fila_error_de_fetch()
    fallas += test_contar_frecuencia_agrupa_citas_casi_identicas()
    with tempfile.TemporaryDirectory() as tmp:
        fallas += test_main_sin_escribir_no_toca_el_csv(tmp)
    with tempfile.TemporaryDirectory() as tmp:
        fallas += test_persistir_verificaciones_escribe_y_respalda(tmp)
    with tempfile.TemporaryDirectory() as tmp:
        fallas += test_agregar_pendientes_agrega_filas_validas(tmp)
    with tempfile.TemporaryDirectory() as tmp:
        fallas += test_agregar_pendientes_rechaza_fila_invalida(tmp)
    with tempfile.TemporaryDirectory() as tmp:
        fallas += test_agregar_pendientes_rechaza_voz_id_ya_existente(tmp)
    with tempfile.TemporaryDirectory() as tmp:
        fallas += test_min_voz_requerido_default_sin_csv(tmp)
    with tempfile.TemporaryDirectory() as tmp:
        fallas += test_min_voz_requerido_lee_override(tmp)
    print(f"\n{'0 fallas' if not fallas else str(fallas) + ' falla(s)'}.")
    return 1 if fallas else 0


if __name__ == "__main__":
    sys.exit(main())
