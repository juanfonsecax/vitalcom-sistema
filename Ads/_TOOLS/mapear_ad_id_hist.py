#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""mapear_ad_id_hist.py — recupera `ad_id` histórico de _FACT_VENTAS.csv, SOLO cuando lo puede
VERIFICAR contra el gasto real de Meta (P1-cimientos T2, 23-sep-2026).

POR QUÉ EXISTE. 1394 filas BASE de _FACT_VENTAS.csv no traen un `ad_id` válido (todo dígitos,
largo >= 10): llegaron corruptas en notación científica o vacías. El JOIN histórico de esas filas
es por NOMBRE (`alias.py`), pero un nombre de anuncio se reutiliza entre productos y entre
réplicas — inventar un `ad_id` a partir del nombre solo sería otra versión de la verdad. Este
script SOLO acepta un `ad_id` cuando el gasto de Meta para ese anuncio, sumado sobre la ventana
exacta de la fila, coincide con `spend_usd` dentro de una tolerancia chica. Toda fila que no
verifique queda con `ad_id` vacío y un `motivo` explícito: nunca se inventa.

NUNCA escribe en `_FACT_VENTAS.csv`, `_FACT_ENTREGA.csv` ni `_FACT_ENTREGA_ANUNCIO.csv`. El único
output es `PRODUCTOS/_MAPA_AD_ID_HIST.csv`, una tabla de mapeo aparte (invariante 11: CSV real,
nunca a mano).

ALCANCE DE RED (autorizado 23-sep-2026, operador): Graph API de Meta, SOLO LECTURA, solo para el
rango 2026-07-01..2026-09-05. Una fila cuya ventana se sale de ese rango nunca dispara una llamada
de red: queda `motivo=sin_candidato` (no se buscó, no se inventó). El re-pull de Jul-Ago NUNCA debe
llegar a `_FACT_ENTREGA*.csv`: `gasto.py` es dueño del gasto histórico (con fallback a LucidSales
antes de 2026-09-06) y una fila vieja de Meta ahí cambiaría el gasto en silencio. Por eso este
script nunca llama a `upsert_fact.upsert`: guarda el crudo de Meta en un STAGING aparte,
`Ads/_INGESTA/META_HIST/<cuenta_alias>_<fecha>.json`, uno por cuenta+día, y lo reutiliza en
corridas siguientes (idempotente, sin re-pedirle nada a Meta que ya se bajó).

REGLA DE MATCH (el corazón del script, no se afloja):
  candidatos = anuncios de Meta en la MISMA cuenta y el/los MISMO(S) día(s) de la ventana, cuyo
  `ad_name` sea EXACTAMENTE `anuncio` (o su alias-canónico via `alias.py`, por si el nombre del
  anuncio cambió con el mismo renombrado que canonicaliza conjuntos). Se suma el spend de Meta por
  `ad_id` sobre TODOS los días de la ventana (una ventana de `dias` > 1 es una fila, no un
  promedio). Se acepta el `ad_id` solo si exactamente UN candidato cae dentro de
  max(0.02, 1% de spend_usd). Si `spend_usd` es 0/vacío nunca se acepta (no hay evidencia).
  En cualquier otro caso: metodo=nombre, ad_id vacío, motivo en
  {sin_candidato, ambiguo, gasto_no_coincide, sin_gasto}.

USO:
    python Ads/_TOOLS/mapear_ad_id_hist.py --fetch     # trae de Meta lo que falte en staging y mapea
    python Ads/_TOOLS/mapear_ad_id_hist.py              # solo mapea con el staging que ya exista
    python Ads/_TOOLS/mapear_ad_id_hist.py --dry-run    # imprime cobertura, no escribe el CSV

CREDENCIALES: mismas que bajar_meta_insights.py (META_SYSTEM_USER_TOKEN o ~/.config/meta/.env).
Este script nunca imprime el token.
"""
import argparse
import csv
import datetime
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import alias as al  # noqa: E402
import bajar_meta_insights as bmi  # noqa: E402

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROD = os.path.join(BASE, "PRODUCTOS")
VENTAS_CSV = os.path.join(PROD, "_FACT_VENTAS.csv")
CUENTAS_CSV = os.path.join(PROD, "_DIM_CUENTAS.csv")
MAPA_CSV = os.path.join(PROD, "_MAPA_AD_ID_HIST.csv")
STAGING_DIR = os.path.join(BASE, "Ads", "_INGESTA", "META_HIST")

# Rango autorizado por el operador para este re-pull (23-sep-2026). Fuera de este rango el script
# NUNCA llama a la Graph API: la fila queda sin_candidato.
RANGO_AUTORIZADO_INI = "2026-07-01"
RANGO_AUTORIZADO_FIN = "2026-09-05"

COLS = ["ventana_ini", "ventana_fin", "cuenta_alias", "conjunto", "anuncio", "ad_id",
        "metodo", "motivo", "spend_lucid", "spend_meta"]

MOTIVOS = ("sin_candidato", "ambiguo", "gasto_no_coincide", "sin_gasto")


# ── lectura ──────────────────────────────────────────────────────────────────────────────────

def ad_id_valido(v):
    """Válido = solo dígitos y largo >= 10 (el mismo corte que usa esta migración en g06/T2)."""
    v = (v or "").strip()
    return v.isdigit() and len(v) >= 10


def num(v):
    try:
        return float(v) if v not in (None, "") else 0.0
    except (TypeError, ValueError):
        return 0.0


def cuenta_id_de(fila):
    """_FACT_VENTAS.csv trae cuenta_id como texto de float ("598687956219141.0"): normaliza a
    el mismo entero-string que usa _DIM_CUENTAS.csv."""
    v = (fila.get("cuenta_id") or "").strip()
    if not v:
        return ""
    try:
        return str(int(float(v)))
    except ValueError:
        return v


def leer_ventas_sin_ad_id(path=VENTAS_CSV):
    with open(path, encoding="utf-8") as f:
        filas = list(csv.DictReader(f))
    return [r for r in filas
            if r.get("rol_ventana") == "BASE" and not ad_id_valido(r.get("ad_id"))]


def leer_cuentas(path=CUENTAS_CSV):
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def cuenta_por_id(cuentas):
    out = {}
    for c in cuentas:
        cid = (c.get("cuenta_id") or "").strip()
        if cid:
            out[cid] = c
    return out


def dias_de(ini, fin):
    d0 = datetime.date.fromisoformat(ini)
    d1 = datetime.date.fromisoformat(fin)
    if d1 < d0:
        return [ini]
    out, d = [], d0
    while d <= d1:
        out.append(d.isoformat())
        d += datetime.timedelta(days=1)
    return out


def dentro_de_rango_autorizado(fila, ini=RANGO_AUTORIZADO_INI, fin=RANGO_AUTORIZADO_FIN):
    return fila["ventana_ini"] >= ini and fila["ventana_fin"] <= fin


# ── staging (nunca toca los _FACT_*.csv) ────────────────────────────────────────────────────────

def ruta_staging(cuenta_alias, fecha, staging_dir=STAGING_DIR):
    return os.path.join(staging_dir, f"{cuenta_alias}_{fecha}.json")


def cargar_staging(cuenta_alias, fecha, staging_dir=STAGING_DIR):
    ruta = ruta_staging(cuenta_alias, fecha, staging_dir)
    if not os.path.exists(ruta):
        return None
    with open(ruta, encoding="utf-8") as f:
        return json.load(f)


def guardar_staging(cuenta_alias, fecha, filas, staging_dir=STAGING_DIR):
    os.makedirs(staging_dir, exist_ok=True)
    ruta = ruta_staging(cuenta_alias, fecha, staging_dir)
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(filas, f, ensure_ascii=False, indent=2, sort_keys=True)
    return ruta


def fetch_meta_dia(cuenta, fecha, token, staging_dir=STAGING_DIR, modulo=bmi):
    """Trae insights nivel-anuncio de UNA cuenta+día por la Graph API (reusa
    bajar_meta_insights.insights_de, que ya trae reintento de rate-limit y paginación), los reduce
    a lo que hace falta para el match (ad_id/ad_name/spend) y los guarda en staging. NUNCA llama a
    upsert_fact.upsert ni toca _FACT_ENTREGA*.csv."""
    crudos = modulo.insights_de(cuenta["cuenta_id"], fecha, token)
    filas = [{
        "ad_id": r.get("ad_id") or "",
        "ad_name": r.get("ad_name") or "",
        "adset_name": r.get("adset_name") or "",
        "spend": modulo.num(r.get("spend")),
    } for r in crudos]
    alias_c = cuenta["cuenta_alias"].replace(" ", "")
    guardar_staging(alias_c, fecha, filas, staging_dir)
    return filas


# ── el match (funciones puras, sin red — esto es lo que testea el gate) ────────────────────────

def candidatos_de(meta_por_dia, dias, nombre_objetivo, nombre_alt=None):
    """Suma el spend de Meta por ad_id, sobre `dias`, de anuncios cuyo ad_name calce exacto con
    `nombre_objetivo` o con su alias-canónico `nombre_alt`. {} si no hay ninguno."""
    nombres = {n for n in (nombre_objetivo, nombre_alt) if n}
    acc = {}
    for d in dias:
        for r in meta_por_dia.get(d, []):
            aid = r.get("ad_id")
            if aid and r.get("ad_name") in nombres:
                acc[aid] = acc.get(aid, 0.0) + num(r.get("spend"))
    return acc


def emparejar(spend_lucid, candidatos):
    """La regla dura: único ad_id dentro de max(0.02, 1%) de spend_lucid -> verificado.
    Devuelve (ad_id, metodo, motivo, spend_meta) — motivo es "" cuando metodo=verificado."""
    spend_lucid = num(spend_lucid)
    if spend_lucid <= 0:
        return "", "nombre", "sin_gasto", ""
    if not candidatos:
        return "", "nombre", "sin_candidato", ""
    tol = round(max(0.02, 0.01 * spend_lucid), 2)
    # redondeado a centavo: evita que el error de punto flotante (1.02 - 1.00 == 0.020000000000000018)
    # rechace un match que a nivel de plata real es exacto.
    dentro = [(aid, sp) for aid, sp in candidatos.items() if round(abs(sp - spend_lucid), 2) <= tol]
    if len(dentro) == 1:
        aid, sp = dentro[0]
        return aid, "ad_id_verificado_gasto", "", round(sp, 2)
    cercano = min(candidatos.items(), key=lambda kv: abs(kv[1] - spend_lucid))
    if len(dentro) > 1:
        return "", "nombre", "ambiguo", round(cercano[1], 2)
    return "", "nombre", "gasto_no_coincide", round(cercano[1], 2)


def mapear_fila(fila, meta_por_cuenta_dia, alias_map,
                 rango=(RANGO_AUTORIZADO_INI, RANGO_AUTORIZADO_FIN)):
    """fila: una fila BASE de _FACT_VENTAS.csv sin ad_id válido.
    meta_por_cuenta_dia: {(cuenta_id_normalizado, fecha): [ {ad_id, ad_name, spend}, ... ]}.
    alias_map: {nombre_viejo: nombre_nuevo} de alias.mapa()/mapa_de().
    Devuelve el dict con las columnas ad_id/metodo/motivo/spend_meta de _MAPA_AD_ID_HIST.csv."""
    ini, fin = fila["ventana_ini"], fila["ventana_fin"]
    if not (ini >= rango[0] and fin <= rango[1]):
        return {"ad_id": "", "metodo": "nombre", "motivo": "sin_candidato", "spend_meta": ""}
    dias = dias_de(ini, fin)
    cid = cuenta_id_de(fila)
    meta_por_dia = {d: meta_por_cuenta_dia.get((cid, d), []) for d in dias}
    nombre = (fila.get("anuncio") or "").strip()
    nombre_alt = alias_map.get(nombre)
    if nombre_alt == nombre:
        nombre_alt = None
    candidatos = candidatos_de(meta_por_dia, dias, nombre, nombre_alt)
    ad_id, metodo, motivo, spend_meta = emparejar(fila.get("spend_usd"), candidatos)
    return {"ad_id": ad_id, "metodo": metodo, "motivo": motivo, "spend_meta": spend_meta}


# ── orquestación (red solo con --fetch; SIEMPRE staging, nunca los _FACT_*.csv) ─────────────────

def dias_necesarios(filas, cid_map):
    """{(cuenta_id, fecha)} de toda fila en rango autorizado con cuenta_id reconocido."""
    necesarios = set()
    for f in filas:
        if not dentro_de_rango_autorizado(f):
            continue
        cid = cuenta_id_de(f)
        if not cid or cid not in cid_map:
            continue
        for d in dias_de(f["ventana_ini"], f["ventana_fin"]):
            necesarios.add((cid, d))
    return necesarios


def construir_indice_meta(filas, cuentas, token, staging_dir=STAGING_DIR, fetch=False, modulo=bmi):
    """{(cuenta_id, fecha): [filas de Meta]}. Usa el staging si ya existe; con `fetch=True` baja
    de la Graph API lo que falte y lo guarda en staging. Sin `fetch`, un día sin staging queda con
    lista vacía (se reporta como sin_candidato, nunca se inventa).

    AISLAMIENTO DE FALLAS (mismo patron que bajar_meta_insights.main()): una cuenta+dia que la
    Graph API rechaza (ej. sin permiso ads_read sobre esa cuenta puntual) NUNCA tumba el resto del
    mapeo — queda sin staging (lista vacia, sin_candidato) y se reporta al final."""
    cid_map = cuenta_por_id(cuentas)
    indice, fallidas = {}, []
    for cid, d in sorted(dias_necesarios(filas, cid_map)):
        cuenta = cid_map[cid]
        alias_c = cuenta["cuenta_alias"].replace(" ", "")
        cache = cargar_staging(alias_c, d, staging_dir)
        if cache is None:
            if not fetch:
                cache = []
            else:
                try:
                    cache = fetch_meta_dia(cuenta, d, token, staging_dir, modulo=modulo)
                    time.sleep(0.2)  # cortesia con el rate limit de la Graph API
                except (SystemExit, Exception) as e:
                    msg = str(e) or repr(e)
                    print(f"    ! FALLO {alias_c} {d}: {msg}", file=sys.stderr)
                    fallidas.append((alias_c, d, msg))
                    cache = []
        indice[(cid, d)] = cache
    if fallidas:
        print(f"cuenta+dia con error ({len(fallidas)}): "
              + ", ".join(f"{a}@{d}" for a, d, _ in fallidas), file=sys.stderr)
    return indice, fallidas


def construir_mapa(filas, indice_meta, alias_map):
    filas_out = []
    for f in filas:
        r = mapear_fila(f, indice_meta, alias_map)
        filas_out.append({
            "ventana_ini": f["ventana_ini"], "ventana_fin": f["ventana_fin"],
            "cuenta_alias": f.get("cuenta_alias", ""), "conjunto": f.get("conjunto", ""),
            "anuncio": f.get("anuncio", ""), "ad_id": r["ad_id"], "metodo": r["metodo"],
            "motivo": r["motivo"], "spend_lucid": f.get("spend_usd", ""),
            "spend_meta": r["spend_meta"],
        })
    # Orden determinista: mismo input -> mismo CSV byte a byte (idempotente).
    filas_out.sort(key=lambda r: (r["ventana_ini"], r["cuenta_alias"], r["conjunto"], r["anuncio"]))
    return filas_out


def escribir_mapa_csv(filas_out, ruta=MAPA_CSV):
    with open(ruta, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLS, quoting=csv.QUOTE_MINIMAL)
        w.writeheader()
        for r in filas_out:
            w.writerow(r)
    return ruta


def cobertura_por_mes(filas_out):
    """{mes: {"total": n, "verificado": n, motivo: n, ...}} para el reporte de consola."""
    out = {}
    for r in filas_out:
        mes = r["ventana_ini"][:7]
        c = out.setdefault(mes, {"total": 0, "verificado": 0})
        c["total"] += 1
        if r["metodo"] == "ad_id_verificado_gasto":
            c["verificado"] += 1
        else:
            c[r["motivo"]] = c.get(r["motivo"], 0) + 1
    return out


def main():
    p = argparse.ArgumentParser(
        description="Mapea ad_id historico verificado por gasto, sin tocar los _FACT_*.csv.")
    p.add_argument("--fetch", action="store_true",
                    help="baja de la Graph API lo que falte en staging (red, rango autorizado)")
    p.add_argument("--dry-run", action="store_true", help="no escribe _MAPA_AD_ID_HIST.csv")
    p.add_argument("--env", default=bmi.ENV_DEFAULT)
    p.add_argument("--staging-dir", default=STAGING_DIR)
    p.add_argument("--ventas", default=VENTAS_CSV)
    p.add_argument("--cuentas", default=CUENTAS_CSV)
    p.add_argument("--out", default=MAPA_CSV)
    a = p.parse_args()

    filas = leer_ventas_sin_ad_id(a.ventas)
    print(f"filas BASE sin ad_id valido: {len(filas)}")
    if not filas:
        return 0

    cuentas = leer_cuentas(a.cuentas)
    token = bmi.token_de(a.env) if a.fetch else ""
    indice, fallidas = construir_indice_meta(filas, cuentas, token, staging_dir=a.staging_dir,
                                              fetch=a.fetch)
    alias_map = al.mapa()
    filas_out = construir_mapa(filas, indice, alias_map)

    for mes, c in sorted(cobertura_por_mes(filas_out).items()):
        detalle = ", ".join(f"{k}={v}" for k, v in sorted(c.items()) if k not in ("total",))
        print(f"  {mes}: {c['total']} filas — {detalle}")

    if a.dry_run:
        print(f"\n[dry-run] {len(filas_out)} filas listas — no se escribio {a.out}.")
        return 0

    escribir_mapa_csv(filas_out, a.out)
    print(f"\n{a.out}: {len(filas_out)} filas escritas.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
