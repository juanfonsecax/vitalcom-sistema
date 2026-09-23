#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""verificar_voz.py — dueño único de PRODUCTOS/_VOZ_CLIENTE.csv (T10, g07-cimientos, 23-sep-2026).

POR QUE EXISTE (auditoría H5, 22-sep-2026): la investigación de voz del cliente vive como
prosa dentro de `2_DATA_PRODUCTO.txt` — 0 URLs, ningún validador. `ETAPA-1B.md` solo pedía una
"fuente" en texto libre. Un modelo puede inventar un dolor citando "Reddit" sin que nada lo
detecte: la frase [VOZ-REAL] no era verificable. Este módulo hace de la voz del cliente un
DATO con URL y cita textual, y VERIFICA que la cita de verdad esté en la URL — no confía en
que quien la escribió (agente o humano) la copió bien.

ESQUEMA — PRODUCTOS/_VOZ_CLIENTE.csv (columnas exactas, en este orden):
    producto_key    — debe existir en _DIM_PRODUCTOS.csv (no se valida acá: ese dueño es
                       _DIM_PRODUCTOS.csv; acá solo se exige no vacío)
    voz_id          — único POR PRODUCTO (dos productos pueden repetir voz_id, el mismo
                       producto no)
    variable        — dolor | deseo | motivacion | objecion | miedo
    cita_textual    — la frase EXACTA encontrada en la fuente (invariante de ETAPA-1B: no
                       parafrasear)
    url             — http(s) obligatorio; es lo que este módulo re-consulta para verificar
    fuente_tipo     — reddit | foro | youtube | resena | blog | otro
    fecha_captura   — cuándo se minó la frase (texto libre, formato AAAA-MM-DD sugerido)
    pais            — texto libre (GT, CO, ...)
    idioma          — texto libre (es, en, ...)
    nivel_conciencia— texto libre (1/2/3A/3B, igual vocabulario que ETAPA-2)
    embudo          — TOFU | MOFU | BOFU
    angulo_key      — a qué ángulo alimenta esta voz (puede quedar vacío si aún no se asignó)
    estado          — PENDIENTE | VERIFICADA | NO_VERIFICADA (lo escribe este módulo, nunca
                       a mano — invariante 11)
    verificado_el   — fecha de la última verificación (vacío si nunca corrió)

POR QUE NO HAY COLUMNA DE INGRESOS: el ingreso de la persona que escribió la cita no es parte
de la EVIDENCIA de que el dolor es real — un dolor citado con URL y cita textual verificable no
necesita el ingreso de nadie para sostenerse, y agregar esa columna sería juntar un dato
sensible de un tercero (identificable por su propia cita pública) sin que aporte nada a la
verificación. Si algún día se necesita segmentar por poder adquisitivo, ese dato vive en el
AVATAR de ETAPA-2 (rango estimado, nunca la cifra de una persona real), no acá.

VERIFICACIÓN
    Se re-descarga la URL (stdlib `urllib`, timeout, User-Agent normal, GET, sin auth — nunca
    credenciales) y se normalizan AMBOS textos (minúsculas, colapsar espacios, quitar acentos
    y puntuación, des-escapar entidades HTML, quitar tags) antes de buscar la cita dentro del
    contenido. Si aparece -> VERIFICADA + fecha de hoy. Si no aparece, o la descarga falla ->
    NO_VERIFICADA con el motivo impreso (nunca se asume verificada por omisión).
    El fetch es un PARÁMETRO inyectable (`fetch=`) para que los tests nunca toquen la red.

CLI (contrato T6 de este repo: leer es el default, escribir es `--escribir`)
    python Ads/_TOOLS/verificar_voz.py --producto TINNIDROP
        # valida el esquema completo y (re)verifica las filas PENDIENTE de ese producto;
        # solo imprime — no toca el CSV.
    python Ads/_TOOLS/verificar_voz.py --producto TINNIDROP --escribir
        # igual, y además persiste estado/verificado_el (upsert por producto_key+voz_id,
        # con backup en _RESPALDOS/ vía upsert_fact.respaldos_dir).
    python Ads/_TOOLS/verificar_voz.py --agregar-json nuevas.json
        # valida el esquema de las filas nuevas (ETAPA-1B las emite así, nunca a mano) y
        # muestra qué se agregaría, sin escribir.
    python Ads/_TOOLS/verificar_voz.py --agregar-json nuevas.json --escribir
        # agrega esas filas como PENDIENTE (rechaza si algún voz_id ya existe para ese
        # producto_key: evita pisar evidencia ya verificada sin querer).
    Sale con código != 0 si CUALQUIER fila del CSV (no solo las del --producto pedido)
    incumple el esquema — un solo dato, un solo dueño, y el dueño no deja pasar basura.

USO POR gen_plan.py (T10 punto 3): `min_voz_requerido()` es el umbral de voz_id VERIFICADA que
un ángulo de origen VOZ_CLIENTE debe citar en un `_PLAN.json` de FASE 1 (ver ese módulo).
"""
import argparse
import csv
import datetime
import html
import io
import json
import os
import re
import sys
import unicodedata
import urllib.error
import urllib.request

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOOLS = os.path.dirname(os.path.abspath(__file__))
if TOOLS not in sys.path:
    sys.path.insert(0, TOOLS)
import upsert_fact  # respaldos_dir(), upsert() — un solo escritor de CSV de hechos (invariante 11)

PROD = os.path.join(BASE, "PRODUCTOS")
VOZ_PATH = os.path.join(PROD, "_VOZ_CLIENTE.csv")
PARAMS_PATH = os.path.join(PROD, "_PARAMETROS_DECISION.csv")
DIM_PROD_PATH = os.path.join(PROD, "_DIM_PRODUCTOS.csv")

COLS = [
    "producto_key", "voz_id", "variable", "cita_textual", "url", "fuente_tipo",
    "fecha_captura", "pais", "idioma", "nivel_conciencia", "embudo", "angulo_key",
    "estado", "verificado_el",
]

VARIABLES = {"dolor", "deseo", "motivacion", "objecion", "miedo"}
FUENTES = {"reddit", "foro", "youtube", "resena", "blog", "otro"}
EMBUDOS = {"TOFU", "MOFU", "BOFU"}
ESTADOS = {"PENDIENTE", "VERIFICADA", "NO_VERIFICADA"}

# Umbral por defecto de voz_id VERIFICADA que un ángulo de origen VOZ_CLIENTE debe citar
# (T10 punto 3, gen_plan.py). Overrideable por la fila `min_voz_verificada_por_angulo` de
# _PARAMETROS_DECISION.csv — el orquestador la agrega en el checkout real, no este worktree.
MIN_VOZ_VERIFICADA_POR_ANGULO = 3

FETCH_TIMEOUT_SEG = 10
USER_AGENT = "Mozilla/5.0 (compatible; VitalcomVozClienteBot/1.0)"


# ─────────────────────────────────────────────────────────────────────────────
# LECTURA
# ─────────────────────────────────────────────────────────────────────────────

def leer_csv(path=None):
    ruta = path or VOZ_PATH
    if not os.path.exists(ruta):
        return []
    with io.open(ruta, encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def min_voz_requerido(params_path=None):
    """Lee `min_voz_verificada_por_angulo` de _PARAMETROS_DECISION.csv si la fila existe;
    si no, el default de este módulo. Nunca escribe la fila (dato del orquestador, no de
    este validador — CLAUDE.md invariante 11: un escritor real por CSV)."""
    ruta = params_path or PARAMS_PATH
    if os.path.exists(ruta):
        try:
            with io.open(ruta, encoding="utf-8-sig") as fh:
                for r in csv.DictReader(fh):
                    if (r.get("parametro") or "").strip() == "min_voz_verificada_por_angulo":
                        try:
                            return int((r.get("valor") or "").strip())
                        except (TypeError, ValueError):
                            pass
        except OSError:
            pass
    return MIN_VOZ_VERIFICADA_POR_ANGULO


# ─────────────────────────────────────────────────────────────────────────────
# ESQUEMA
# ─────────────────────────────────────────────────────────────────────────────

def validar_filas(filas):
    """Devuelve una lista de problemas de texto, uno por violación. Recorre TODO el CSV
    (no solo un producto): el esquema es la responsabilidad de este módulo entero."""
    problemas = []
    vistos = set()
    for i, f in enumerate(filas):
        etq = "fila %d (%s/%s)" % (i + 1, f.get("producto_key"), f.get("voz_id"))
        if not (f.get("producto_key") or "").strip():
            problemas.append("%s: producto_key vacío" % etq)
        voz_id = (f.get("voz_id") or "").strip()
        if not voz_id:
            problemas.append("%s: voz_id vacío" % etq)
        else:
            llave = ((f.get("producto_key") or "").strip(), voz_id)
            if llave in vistos:
                problemas.append("%s: voz_id duplicado para el mismo producto_key" % etq)
            vistos.add(llave)
        if not (f.get("cita_textual") or "").strip():
            problemas.append("%s: cita_textual vacía" % etq)
        url = (f.get("url") or "").strip()
        if not url:
            problemas.append("%s: url vacía" % etq)
        elif not re.match(r"^https?://", url, re.IGNORECASE):
            problemas.append("%s: url %r no es http(s)" % (etq, url))
        if (f.get("variable") or "").strip() not in VARIABLES:
            problemas.append("%s: variable %r fuera de %s"
                             % (etq, f.get("variable"), sorted(VARIABLES)))
        if (f.get("fuente_tipo") or "").strip() not in FUENTES:
            problemas.append("%s: fuente_tipo %r fuera de %s"
                             % (etq, f.get("fuente_tipo"), sorted(FUENTES)))
        if (f.get("embudo") or "").strip() not in EMBUDOS:
            problemas.append("%s: embudo %r fuera de %s"
                             % (etq, f.get("embudo"), sorted(EMBUDOS)))
        estado = (f.get("estado") or "PENDIENTE").strip() or "PENDIENTE"
        if estado not in ESTADOS:
            problemas.append("%s: estado %r fuera de %s" % (etq, estado, sorted(ESTADOS)))
    return problemas


# ─────────────────────────────────────────────────────────────────────────────
# VERIFICACIÓN (re-fetch + normalización + búsqueda de la cita)
# ─────────────────────────────────────────────────────────────────────────────

_TAG_RE = re.compile(r"<[^>]+>")
_PUNCT_RE = re.compile(r"[^\w\s]", re.UNICODE)
_WS_RE = re.compile(r"\s+")


def normalizar(texto):
    """minúsculas + quita tags + des-escapa HTML + quita acentos/puntuación + colapsa
    espacios. Sin esto una cita real puede no "encontrarse" solo porque la página trae
    comillas curvas, un <b> en medio o un acento distinto (copy/paste desde un PDF, etc.)."""
    if not texto:
        return ""
    t = html.unescape(texto)
    t = _TAG_RE.sub(" ", t)
    t = t.lower()
    t = unicodedata.normalize("NFKD", t)
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = _PUNCT_RE.sub(" ", t)
    t = _WS_RE.sub(" ", t).strip()
    return t


def fetch_default(url):
    """GET simple, sin auth, con User-Agent normal y timeout — nunca credenciales. Único
    fetch de red del módulo; todo lo demás recibe `fetch` como parámetro para no tocar la
    red en los tests (T10)."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=FETCH_TIMEOUT_SEG) as resp:
        charset = resp.headers.get_content_charset() or "utf-8"
        return resp.read().decode(charset, errors="replace")


def verificar_fila(fila, fetch=fetch_default):
    """(estado_nuevo, motivo) para una fila. NO_VERIFICADA con el motivo explícito ante
    cualquier falla — nunca se asume verificada por omisión (regla del docstring del
    módulo)."""
    url = (fila.get("url") or "").strip()
    cita = fila.get("cita_textual") or ""
    if not url or not cita:
        return "NO_VERIFICADA", "sin url o sin cita_textual"
    try:
        contenido = fetch(url)
    except Exception as e:  # noqa: BLE001 — cualquier falla de red es NO_VERIFICADA, no un crash
        return "NO_VERIFICADA", "error al descargar la url: %s" % e
    if normalizar(cita) in normalizar(contenido):
        return "VERIFICADA", ""
    return "NO_VERIFICADA", "la cita no aparece en el contenido de la url"


# ─────────────────────────────────────────────────────────────────────────────
# DEDUPE / FRECUENCIA
# ─────────────────────────────────────────────────────────────────────────────

def contar_frecuencia(filas):
    """Cuenta citas casi-idénticas (mismo producto + variable + texto normalizado) — un
    conteo simple de texto normalizado alcanza para ver qué dolor se repite más, sin
    necesitar similitud difusa. Devuelve {(producto_key, variable, cita_normalizada): n}."""
    conteo = {}
    for f in filas:
        llave = (
            (f.get("producto_key") or "").strip(),
            (f.get("variable") or "").strip(),
            normalizar(f.get("cita_textual") or ""),
        )
        if llave[2]:
            conteo[llave] = conteo.get(llave, 0) + 1
    return conteo


# ─────────────────────────────────────────────────────────────────────────────
# ESCRITURA (upsert_fact — invariante 11, un solo escritor)
# ─────────────────────────────────────────────────────────────────────────────

def persistir_verificaciones(resultados, path=None, bkdir=None):
    """`resultados`: lista de (fila_original, estado_nuevo, motivo). Escribe SOLO estado +
    verificado_el vía upsert_fact (llave producto_key+voz_id) — nunca reescribe a mano."""
    ruta = path or VOZ_PATH
    hoy = datetime.date.today().isoformat()
    filas_nuevas = []
    for fila, estado, _motivo in resultados:
        actualizada = dict(fila)
        actualizada["estado"] = estado
        actualizada["verificado_el"] = hoy
        filas_nuevas.append(actualizada)
    bk = bkdir or upsert_fact.respaldos_dir(BASE, "backups_csv")
    return upsert_fact.upsert(ruta, COLS, ("producto_key", "voz_id"), filas_nuevas, bk)


def agregar_pendientes(filas_nuevas_raw, path=None, bkdir=None):
    """Entrada del escritor para ETAPA-1B (T10 punto 2): agrega filas como PENDIENTE.
    Rechaza (no escribe nada) si el esquema falla o si algún voz_id ya existe para su
    producto_key — nunca pisa evidencia ya cargada en silencio."""
    ruta = path or VOZ_PATH
    existentes = leer_csv(ruta)
    existentes_llaves = {
        ((f.get("producto_key") or "").strip(), (f.get("voz_id") or "").strip())
        for f in existentes
    }
    filas_nuevas = []
    for f in filas_nuevas_raw:
        completa = dict(f)
        completa.setdefault("estado", "PENDIENTE")
        completa["estado"] = "PENDIENTE"
        completa.setdefault("verificado_el", "")
        filas_nuevas.append(completa)

    problemas = list(validar_filas(filas_nuevas))
    for f in filas_nuevas:
        llave = ((f.get("producto_key") or "").strip(), (f.get("voz_id") or "").strip())
        if llave in existentes_llaves:
            problemas.append("voz_id %r ya existe para producto_key %r — no se pisa evidencia "
                             "existente" % (llave[1], llave[0]))
    if problemas:
        return problemas, None

    bk = bkdir or upsert_fact.respaldos_dir(BASE, "backups_csv")
    resultado = upsert_fact.upsert(ruta, COLS, ("producto_key", "voz_id"), filas_nuevas, bk)
    return [], resultado


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def _imprimir_frecuencia(filas):
    conteo = contar_frecuencia(filas)
    repetidas = {k: v for k, v in conteo.items() if v > 1}
    if not repetidas:
        print("  (sin dolores/deseos repetidos detectados)")
        return
    for (producto, variable, _cita), n in sorted(repetidas.items(), key=lambda kv: -kv[1]):
        print("  %dx  %s / %s" % (n, producto, variable))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--producto")
    ap.add_argument("--escribir", action="store_true")
    ap.add_argument("--agregar-json")
    args = ap.parse_args(argv)

    if args.agregar_json:
        with io.open(args.agregar_json, encoding="utf-8") as fh:
            nuevas = json.load(fh)
        if isinstance(nuevas, dict):
            nuevas = [nuevas]
        problemas, resultado = ([], None)
        if args.escribir:
            problemas, resultado = agregar_pendientes(nuevas)
        else:
            # dry-run: valida como si ya tuvieran estado PENDIENTE, sin tocar el CSV.
            previsualizacion = []
            for f in nuevas:
                completa = dict(f)
                completa.setdefault("estado", "PENDIENTE")
                previsualizacion.append(completa)
            problemas = validar_filas(previsualizacion)
        if problemas:
            print("ERRORES en --agregar-json:")
            for p in problemas:
                print("  ERROR  %s" % p)
            return 1
        if args.escribir:
            reemplazadas, nuevas_n, sin_cambio = resultado
            print("agregadas %d filas PENDIENTE (%d sin cambio)" % (nuevas_n, sin_cambio))
        else:
            print("%d filas listas para agregar (dry-run — usar --escribir para persistir)"
                  % len(nuevas))
        return 0

    filas = leer_csv()
    problemas = validar_filas(filas)
    if problemas:
        print("ERRORES de esquema en _VOZ_CLIENTE.csv:")
        for p in problemas:
            print("  ERROR  %s" % p)

    objetivo = [
        f for f in filas
        if (f.get("estado") or "PENDIENTE") == "PENDIENTE"
        and (not args.producto or f.get("producto_key") == args.producto)
    ]
    resultados = []
    for f in objetivo:
        estado, motivo = verificar_fila(f)
        resultados.append((f, estado, motivo))
        print("%s %s: %s%s" % (f.get("producto_key"), f.get("voz_id"), estado,
                               (" — %s" % motivo) if motivo else ""))

    alcance = [f for f in filas if not args.producto or f.get("producto_key") == args.producto]
    print("\nFrecuencia (dolores/deseos casi-idénticos repetidos):")
    _imprimir_frecuencia(alcance)

    if args.escribir and resultados:
        persistir_verificaciones(resultados)
        print("\n%d verificaciones persistidas en %s" % (len(resultados), VOZ_PATH))

    return 1 if problemas else 0


if __name__ == "__main__":
    sys.exit(main())
