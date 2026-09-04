#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ingerir_meta.py — carga exports de Ads Manager a _FACT_ENTREGA.csv

Uso:
    python Ads/_TOOLS/ingerir_meta.py <archivo.xlsx> [<archivo2.xlsx> ...]
    python Ads/_TOOLS/ingerir_meta.py --dir <carpeta>          (toma Informe-*.xlsx)
    ... [--dry-run]

POR QUE EXISTE (03-sep-2026): la capa de ENTREGA se llenaba SOLO por el MCP de Meta. Cuando el MCP
dejo de correr, _FACT_ENTREGA.csv quedo congelada en el 25-ago mientras el operador seguia bajando
los xlsx de Ads Manager. Sin esta capa no se puede separar el problema PRE-CLIC del POST-CLIC, que
es exactamente lo que dejo a etapa-11 con 53.8% de cobertura. El xlsx tiene la misma informacion
que el MCP: este script la carga sin depender de que el conector funcione.

Reglas que implementa (DOCTRINA/DATA_PLAYBOOK.md §1):
  · La FECHA sale de las columnas 'Inicio/Fin del informe', NO del nombre (los exports se llaman
    todos "Informe-sin-titulo"). Un archivo multi-dia se carga con dias>1 y NO es contiguo con las
    diarias: se marca fuente 'AdsManager-export-Nd' para que se vea.
  · Descarta la fila de TOTAL DE CUENTA (la que viene sin nombre de campana).
  · mensajes = round(TASA DE CONVERSION A WHATSAPP x Clics en el enlace). Verificado 01-sep:
    da 106, identico a los mensajes de LucidSales del mismo dia.
  · CP1 (1346891653335162) factura en COP -> spend_COP / 3152.5 = spend_USD (APR-028).
  · ANTI-DUPLICADO por (ventana_ini, ventana_fin, cuenta_alias, campana, conjunto, fuente).
  · Llave = nombre del conjunto EXACTO como quedo en Meta, con tildes y sufijos. No normalizar.
  · Escribe con csv writer real (regla 11 de CLAUDE.md). Backup previo en _ARCHIVO/backups_csv/.
  · Reporta el JOIN contra _DIM_CONJUNTOS.csv; un conjunto sin dimension se REPORTA, no se descarta.
"""
import sys, io, os, re, csv, glob, shutil, datetime, warnings

# Windows abre la consola en cp1252: un print con un simbolo fuera de ese mapa revienta con
# UnicodeEncodeError y el script sale con exit 1 AUNQUE el trabajo ya se completo (bug real del
# 18-ago en gen_dashboard.py, y sigue vivo en ingerir_lucidsales.py). Forzar UTF-8 lo cubre.
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
warnings.filterwarnings("ignore")

import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROD = os.path.join(BASE, "PRODUCTOS")
FACT = os.path.join(PROD, "_FACT_ENTREGA.csv")
DIMC = os.path.join(PROD, "_DIM_CONJUNTOS.csv")
BKDIR = os.path.join(BASE, "_ARCHIVO", "backups_csv")

TASA_COP_USD = 3152.5          # APR-028, medida contra el banco
CP1 = "1346891653335162"

ALIAS = {
    "GTR7": "598687956219141",
    "GTR0": "1665221077707961",
    "GTR1": "824783947334627",
    "GTR13": "916746367261028",
    "CP1": "1346891653335162",
    "GTR3": "581490137794343",
}

PROD_KEY = {
    "TINNIDROP": "TINNIDROP", "CLEARSTEM": "CLEARSTEM", "NUSAVA": "NUSAVA",
    "VARICOSE": "VARICOSE", "VARICES": "VARICOSE",
}

COLS = ["ventana_ini", "ventana_fin", "dias", "producto_key", "cuenta_id", "cuenta_alias",
        "campana", "conjunto", "mensajes", "clicks_totales", "link_clicks", "impresiones",
        "spend_usd", "pct_conv_clic_enlace", "fuente"]

# nombre de columna -> las variantes que ha usado el exportador
COLMAP = {
    "campana":     ["Nombre de la campaña"],
    "conjunto":    ["Nombre del conjunto de anuncios"],
    "divisa":      ["Divisa"],
    "spend":       ["Importe gastado", "Importe gastado (USD)"],
    "impresiones": ["Impresiones"],
    "link_clicks": ["Clics en el enlace"],
    "clicks_tot":  ["Clics (todos)"],
    "conv_wa":     ["TASA DE CONVERSION A WHATSAPP", "TASA DE CONVERSIÓN A WHATSAPP"],
    "ini":         ["Inicio del informe"],
    "fin":         ["Fin del informe"],
}


def col(df, key):
    for c in COLMAP[key]:
        if c in df.columns:
            return c
    return None


def num(v, default=0.0):
    try:
        if v is None or (isinstance(v, float) and v != v):
            return default
        return float(v)
    except (TypeError, ValueError):
        return default


def alias_de(conjunto, campana):
    """El alias de cuenta es el prefijo del nombre (GTR7_..., GTR7-MA7-...)."""
    for txt in (str(conjunto or ""), str(campana or "")):
        m = re.match(r"^(GTR\d+|CP\d+)[_\-\s]", txt.strip())
        if m and m.group(1) in ALIAS:
            return m.group(1)
    return ""


def producto_de(campana, conjunto, dim):
    """Primero la dimension (dueno del dato); si no esta, el nombre."""
    k = str(conjunto or "").strip()
    if k in dim:
        return dim[k]
    txt = (str(campana or "") + "_" + str(conjunto or "")).upper()
    for pat, pk in PROD_KEY.items():
        if pat in txt:
            return pk
    return "SIN_CLASIFICAR"


def leer_dim():
    """conjunto_meta -> producto_key, y el set de conjuntos con angulo declarado."""
    dim, con_angulo = {}, set()
    if os.path.exists(DIMC):
        for r in csv.DictReader(open(DIMC, encoding="utf-8")):
            c = (r.get("conjunto_meta") or "").strip()
            if not c:
                continue
            dim[c] = r.get("producto_key") or "SIN_CLASIFICAR"
            if (r.get("angulo_key") or "").strip():
                con_angulo.add(c)
    return dim, con_angulo


def fecha(v):
    try:
        return pd.to_datetime(v).strftime("%Y-%m-%d")
    except Exception:
        return str(v)[:10]


def procesar(path, dim):
    df = pd.read_excel(path)
    c_camp = col(df, "campana")
    if c_camp is None:
        return None, f"sin columna de campana (columnas: {list(df.columns)[:4]}...)"
    c_ini, c_fin = col(df, "ini"), col(df, "fin")
    if c_ini is None or c_fin is None:
        return None, "sin columnas 'Inicio/Fin del informe'"

    det = df[df[c_camp].notna()].copy()          # descarta la fila de TOTAL DE CUENTA
    if det.empty:
        return None, "sin filas de detalle"

    ini, fin = fecha(df[c_ini].iloc[0]), fecha(df[c_fin].iloc[0])
    dias = (datetime.date.fromisoformat(fin) - datetime.date.fromisoformat(ini)).days + 1
    fuente = f"AdsManager-export-{dias}d"

    c_conj, c_div = col(df, "conjunto"), col(df, "divisa")
    c_sp, c_imp = col(df, "spend"), col(df, "impresiones")
    c_lc, c_ct, c_wa = col(df, "link_clicks"), col(df, "clicks_tot"), col(df, "conv_wa")

    out = []
    for _, r in det.iterrows():
        conjunto = str(r[c_conj]).strip() if c_conj and pd.notna(r[c_conj]) else ""
        campana = str(r[c_camp]).strip()
        al = alias_de(conjunto, campana)
        sp = num(r[c_sp]) if c_sp else 0.0
        div = str(r[c_div]).strip().upper() if c_div and pd.notna(r[c_div]) else "USD"
        if div == "COP" or al == "CP1":
            sp = sp / TASA_COP_USD
        lc = int(num(r[c_lc])) if c_lc else 0
        wa = num(r[c_wa]) if c_wa else 0.0
        out.append({
            "ventana_ini": ini, "ventana_fin": fin, "dias": dias,
            "producto_key": producto_de(campana, conjunto, dim),
            "cuenta_id": ALIAS.get(al, ""), "cuenta_alias": al,
            "campana": campana, "conjunto": conjunto,
            "mensajes": int(round(wa * lc)),
            "clicks_totales": int(num(r[c_ct])) if c_ct else 0,
            "link_clicks": lc,
            "impresiones": int(num(r[c_imp])) if c_imp else 0,
            "spend_usd": round(sp, 2),
            "pct_conv_clic_enlace": round(wa * 100, 1),
            "fuente": fuente,
        })
    return out, None


def main():
    args = sys.argv[1:]
    dry = "--dry-run" in args
    args = [a for a in args if a != "--dry-run"]
    if "--dir" in args:
        i = args.index("--dir")
        carpeta = args[i + 1]
        archivos = sorted(glob.glob(os.path.join(carpeta, "Informe-*.xlsx")))
        args = args[:i] + args[i + 2:]
    else:
        archivos = []
    archivos += [a for a in args if a.lower().endswith((".xlsx", ".xls"))]
    if not archivos:
        print(__doc__)
        return 2

    dim, con_angulo = leer_dim()
    existentes = list(csv.DictReader(open(FACT, encoding="utf-8"))) if os.path.exists(FACT) else []
    llaves = {(r["ventana_ini"], r["ventana_fin"], r["cuenta_alias"], r["campana"],
               r["conjunto"], r["fuente"]) for r in existentes}

    nuevas, dup, errores, sin_dim, sin_cuenta = [], 0, [], set(), set()
    for f in archivos:
        filas, err = procesar(f, dim)
        if err:
            errores.append((os.path.basename(f), err))
            continue
        n0 = len(nuevas)
        for r in filas:
            k = (r["ventana_ini"], r["ventana_fin"], r["cuenta_alias"], r["campana"],
                 r["conjunto"], r["fuente"])
            if k in llaves:
                dup += 1
                continue
            llaves.add(k)
            nuevas.append(r)
            if r["conjunto"] and r["conjunto"] not in con_angulo:
                sin_dim.add(r["conjunto"])
            if not r["cuenta_alias"]:
                sin_cuenta.add(r["campana"])
        agg = nuevas[n0:]
        print(f"  {os.path.basename(f)[:44]:46} {agg[0]['ventana_ini'] if agg else '-':10} "
              f"{len(agg):3} filas · {sum(x['mensajes'] for x in agg):4} msj · "
              f"${sum(x['spend_usd'] for x in agg):8.2f}")

    print(f"\narchivos: {len(archivos)} · filas nuevas: {len(nuevas)} · duplicados omitidos: {dup}")
    for f, e in errores:
        print(f"  ! {f}: {e}")
    if sin_cuenta:
        print(f"\n! {len(sin_cuenta)} campañas sin alias de cuenta reconocible: {sorted(sin_cuenta)[:5]}")
    if sin_dim:
        print(f"\n! {len(sin_dim)} conjuntos SIN angulo_key en _DIM_CONJUNTOS.csv "
              f"(hueco de tracking, se reporta y se corrige — no se descarta el dato):")
        for c in sorted(sin_dim)[:15]:
            print(f"    {c}")
    else:
        print("\nJOIN con _DIM_CONJUNTOS cierra al 100%")

    if dry:
        print("\n[dry-run] no se escribio nada.")
        return 0
    if not nuevas:
        print("\nnada que escribir.")
        return 0

    os.makedirs(BKDIR, exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    shutil.copy2(FACT, os.path.join(BKDIR, f"_FACT_ENTREGA_{stamp}.csv"))
    with open(FACT, "a", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=COLS)
        for r in nuevas:
            w.writerow(r)
    print(f"\nescritas {len(nuevas)} filas en {os.path.relpath(FACT, BASE)}")
    print(f"backup: _ARCHIVO/backups_csv/_FACT_ENTREGA_{stamp}.csv")
    return 0


if __name__ == "__main__":
    sys.exit(main())
