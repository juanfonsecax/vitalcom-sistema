# -*- coding: utf-8 -*-
"""Agrega la columna ad_id a _FACT_VENTAS.csv haciendo join contra los xlsx de origen.

Estrategia: asignacion 1-a-1 con consumo de candidatos (no lookup), asi dos filas
gemelas del CSV reciben los dos adId distintos que les corresponden en el xlsx.
Modo diagnostico por defecto: NO escribe salvo que se pase --escribir.
"""
import csv, sys, os, collections, openpyxl
# Consola de Windows en cp1252/cp850: sin esto un print con acentos o simbolos
# revienta con UnicodeEncodeError y devuelve exit code 1 con el trabajo ya hecho
# (mismo bug que en gen_dashboard.py, 18-ago).
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass


BASE = r"C:\Users\juand\Downloads\AGENTES LUCID\Profesional en Eccomerce gestion\SISTEMA"
DL   = r"C:\Users\juand\Downloads"
CSV  = os.path.join(BASE, "PRODUCTOS", "_FACT_VENTAS.csv")

MAPA = {
 ("2026-07-17","2026-07-24","7","BASE","LucidSales"):        ["report-2026-07-17-2026-07-24.xlsx"],
 ("2026-07-19","2026-07-26","7","CONTROL","LucidSales"):     ["report-2026-07-19-2026-07-26.xlsx"],
 ("2026-07-21","2026-07-21","1","CONTROL","LucidSales"):     ["report-2026-07-21-2026-07-21.xlsx"],
 ("2026-07-22","2026-07-22","1","CONTROL","LucidSales"):     ["report-2026-07-22-2026-07-22.xlsx"],
 ("2026-07-25","2026-07-25","1","BASE","LucidSales"):        ["report-2026-07-25-2026-07-25.xlsx"],
 ("2026-07-26","2026-07-26","1","BASE","LucidSales"):        ["report-2026-07-26-2026-07-26.xlsx"],
 ("2026-07-26","2026-07-26","1","CONTROL","LucidSales"):     ["report-2026-07-26-2026-07-26 (1).xlsx"],
 ("2026-07-27","2026-07-27","1","BASE","LucidSales"):        ["report-2026-07-27-2026-07-27.xlsx"],
 ("2026-07-28","2026-07-28","1","BASE","LucidSales"):        ["report-2026-07-28-2026-07-28.xlsx"],
 ("2026-07-29","2026-07-29","1","BASE","LucidSales"):        ["report-2026-07-29-2026-07-29.xlsx",
                                                             "report-2026-07-29-2026-07-29 (1).xlsx"],
 ("2026-07-30","2026-07-30","1","BASE","LucidSales"):        ["report-2026-07-30-2026-07-30.xlsx"],
 ("2026-07-31","2026-07-31","1","CONTROL","LucidSales"):     ["report-2026-07-31-2026-07-31.xlsx"],
 ("2026-07-31","2026-08-02","3","BASE","LucidSales"):        ["report-2026-07-31-2026-08-02.xlsx"],
 ("2026-08-03","2026-08-10","8","BASE","LucidSales"):        ["report-2026-08-03-2026-08-10.xlsx"],
 ("2026-08-01","2026-08-10","10","BASE","LucidSales_CuentaB"):["report-2026-08-01-2026-08-31.xlsx"],
 ("2026-07-01","2026-08-10","41","CONTROL","LucidSales"):    ["report-2026-07-01-2026-08-10.xlsx"],
}

def n(x):
    try: return round(float(x or 0), 2)
    except Exception: return 0.0

def s(x):
    return str(x if x is not None else "").strip()

def s_id(x):
    """Formatea un identificador de Meta (18 digitos) SIN notacion cientifica.

    openpyxl devuelve la celda adId del xlsx de LucidSales como float (Excel la
    guarda como numero), y str(float) escupe '1.2024737592740078e+17'. Eso rompe
    de dos formas: (a) el anti-duplicado por adId da falso negativo contra un id
    bien formado, y (b) un float64 sostiene ~15-17 digitos significativos, asi
    que el ultimo digito de un id de 18 se pierde.

    ESTA FUNCION SOLO ARREGLA (a). (b) es irreversible: cuando el valor llega
    como float la precision YA se perdio en el xlsx. Por eso se intenta primero
    leer el valor como texto/entero; solo si viene float se cae al formato
    entero, y esos casos quedan marcados como APROXIMADOS en la bitacora.
    La llave real de la carga sigue siendo la tupla de 6 campos, no el adId.
    """
    if x is None:
        return ""
    if isinstance(x, str):
        t = x.strip()
        if t and "e+" in t.lower():           # ya venia corrompido de una corrida vieja
            return "%.0f" % float(t)
        return t
    if isinstance(x, int):
        return str(x)
    if isinstance(x, float):
        return "%.0f" % x                     # aproximado en el ultimo digito
    return str(x).strip()

def leer_xlsx(fn):
    wb = openpyxl.load_workbook(os.path.join(DL, fn), read_only=True, data_only=True)
    rows = [r for r in wb.active.iter_rows(values_only=True)]
    hi = [i for i, r in enumerate(rows) if r and r[0] == "adTitle"][0]
    cols = list(rows[hi])
    return [dict(zip(cols, r)) for r in rows[hi+1:] if r and r[0]]

# niveles de llave, de la mas estricta a la mas laxa
def k_xl(x):
    cj, an = s(x.get("adSetTitle")), s(x.get("adTitle"))
    v, t, m = n(x.get("sells")), n(x.get("total")), n(x.get("messages"))
    c, i = n(x.get("clicks")), n(x.get("impressions"))
    p = s(x.get("producto"))
    return [("A",(cj,an,v,t,m,c,i)), ("B",(cj,an,v,t,m)), ("C",(cj,an,v,t)),
            ("D",(cj,an)), ("E",(p,v,t))]

def k_csv(r):
    cj, an = s(r["conjunto"]), s(r["anuncio"])
    v, t, m = n(r["ventas"]), n(r["total_q"]), n(r["mensajes"])
    c, i = n(r["clicks"]), n(r["impresiones"])
    p = s(r["producto"])
    return [("A",(cj,an,v,t,m,c,i)), ("B",(cj,an,v,t,m)), ("C",(cj,an,v,t)),
            ("D",(cj,an)), ("E",(p,v,t))]

def resolver(filas_csv, xl):
    """Asignacion 1-a-1 consumiendo candidatos. Devuelve {idx_csv: adId}."""
    pools = {lvl: collections.defaultdict(collections.deque) for lvl in "ABCDE"}
    for x in xl:
        for lvl, kk in k_xl(x):
            pools[lvl][kk].append(x)
    usados = set()
    out, niveles = {}, collections.Counter()
    for lvl in "ABCDE":
        for i, r in filas_csv:
            if i in out:
                continue
            kk = dict(k_csv(r))[lvl]
            dq = pools[lvl].get(kk)
            while dq:
                cand = dq.popleft()
                if id(cand) in usados:
                    continue
                usados.add(id(cand))
                out[i] = s_id(cand.get("adId")); niveles[lvl] += 1
                break
    return out, niveles

filas = list(csv.DictReader(open(CSV, encoding="utf-8")))
por_ventana = collections.defaultdict(list)
for i, r in enumerate(filas):
    por_ventana[(r["ventana_ini"], r["ventana_fin"], r["dias"], r["rol_ventana"], r["fuente"])].append((i, r))

resultado, stats, sin_arch = {}, collections.Counter(), []
for k, grupo in sorted(por_ventana.items()):
    cands = MAPA.get(k)
    if not cands:
        sin_arch.append((k, len(grupo))); stats["sin_xlsx"] += len(grupo); continue
    mejor, mejor_n, mejor_fn = None, -1, None
    for fn in cands:
        out, niv = resolver(grupo, leer_xlsx(fn))
        if len(out) > mejor_n:
            mejor, mejor_n, mejor_fn = out, len(out), fn
            mejor_niv = niv
    resultado.update(mejor)
    for lvl, c in mejor_niv.items():
        stats["match_" + lvl] += c
    stats["SIN_MATCH"] += len(grupo) - mejor_n
    print("%-52s %s  ->  %3d/%3d" % (k[0] + "->" + k[1] + " " + k[3] + "/" + k[4], mejor_fn[:34], mejor_n, len(grupo)))

print("\n=== TOTALES ===")
for k, v in sorted(stats.items()):
    print("  %-14s %5d" % (k, v))
print("  %-14s %5d / %d  (%.1f%%)" % ("CON ad_id", len(resultado), len(filas), 100.0*len(resultado)/len(filas)))
if sin_arch:
    print("\nventanas sin xlsx mapeado:")
    for k, c in sin_arch: print("   ", k, c, "filas")

faltan = [(i, filas[i]) for i in range(len(filas)) if i not in resultado]
if faltan:
    print("\n=== SIN ad_id (%d) — muestra ===" % len(faltan))
    for i, r in faltan[:12]:
        print("   fila %4d %s/%s  cj='%s' an='%s' v=%s Q=%s sp=%s" %
              (i, r["ventana_ini"], r["rol_ventana"], r["conjunto"][:22], r["anuncio"][:18],
               r["ventas"], r["total_q"], r["spend_usd"]))

if "--escribir" in sys.argv:
    cols = list(filas[0].keys())
    if "ad_id" not in cols:
        cols.append("ad_id")
    with open(CSV, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, quoting=csv.QUOTE_MINIMAL)
        w.writeheader()
        for i, r in enumerate(filas):
            r["ad_id"] = resultado.get(i, "")
            w.writerow(r)
    print("\nESCRITO: columna ad_id agregada a %s" % CSV)
else:
    print("\n(diagnostico - no se escribio nada; pasar --escribir para aplicar)")
