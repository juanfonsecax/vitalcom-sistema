#!/usr/bin/env python3
"""
ingerir_lucidsales.py — carga exports diarios de LucidSales a _FACT_VENTAS.csv

Uso:
    python Ads/_TOOLS/ingerir_lucidsales.py <archivo.xlsx> [<archivo2.xlsx> ...]
    python Ads/_TOOLS/ingerir_lucidsales.py --dir <carpeta>        (toma report-*.xlsx)
    ... [--rol BASE|CONTROL] [--fuente LucidSales|LucidSales_CuentaB] [--dry-run]

Reglas que implementa (DOCTRINA/DATA_PLAYBOOK.md + runbook de la auditoría):
  · header en la FILA 4 (header=3); descarta filas de "Resumen" (accountTitle vacío).
  · mapeo adSetTitle->conjunto · adTitle->anuncio · sells->ventas · total->total_q · spend->spend_usd.
  · CP1 (1346891653335162) factura en COP -> spend_COP / 3152.5 = spend_USD (APR-028).
  · ANTI-DUPLICADO por (ventana_ini, producto_key, conjunto, anuncio, fuente, rol_ventana).
  · La fecha sale del NOMBRE del archivo (report-YYYY-MM-DD-YYYY-MM-DD.xlsx), no del contenido.
  · Escribe con csv writer real (regla 22 de CLAUDE.md). Backup previo en _ARCHIVO/backups_csv/.
  · ad_id se formatea con s_id() (no notación científica cuando se puede).
"""
import sys, os, re, csv, shutil, datetime
import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROD = os.path.join(BASE, "PRODUCTOS")
FACT = os.path.join(PROD, "_FACT_VENTAS.csv")
DIMC = os.path.join(PROD, "_DIM_CONJUNTOS.csv")
BKDIR = os.path.join(BASE, "_ARCHIVO", "backups_csv")

TASA_COP_USD = 3152.5          # APR-028, medida contra banco
CP1 = "1346891653335162"

ALIAS = {
    "598687956219141": "GTR7",
    "1665221077707961": "GTR0",
    "824783947334627": "GTR1",
    "916746367261028": "GTR13",
    "1346891653335162": "CP1",
    "581490137794343": "GTR3",
}

# producto (LucidSales) -> producto_key del sistema
PROD_KEY = {
    "tinnidrop": "TINNIDROP",
    "clearstem": "CLEARSTEM",
    "nusava": "NUSAVA",
    "varicose": "VARICOSE",
    "varices": "VARICOSE",
}

COLS = ["ventana_ini","ventana_fin","dias","rol_ventana","producto_key","producto",
        "cuenta_id","cuenta_alias","campana","conjunto","anuncio","mensajes","clicks",
        "impresiones","spend_usd","ventas","total_q","moneda_origen","fuente","ad_id"]


def s_id(v):
    """Formatea un id sin notación científica cuando se puede (bug adId, 21-ago)."""
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return ""
    if isinstance(v, float):
        if v != v or v in (float("inf"), float("-inf")):
            return ""
        return repr(v) if v > 1e15 else str(int(v))
    return str(v).strip()


def s_num(v, default=0):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return default
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def producto_key(nombre):
    n = (nombre or "").lower()
    for k, v in PROD_KEY.items():
        if k in n:
            return v
    return "SIN_CLASIFICAR"


def fecha_de_nombre(path):
    m = re.search(r"(\d{4}-\d{2}-\d{2})", os.path.basename(path))
    if not m:
        raise SystemExit(f"No pude leer la fecha del nombre: {path}")
    return m.group(1)


def leer_export(path, rol, fuente):
    fecha = fecha_de_nombre(path)
    df = pd.read_excel(path, header=3)
    # filas de resumen al final: accountTitle vacío
    df = df[df["accountTitle"].notna()].copy()
    filas = []
    for _, r in df.iterrows():
        cuenta_id = s_id(r.get("accountTitle"))
        # accountTitle viene como float grande -> reconstruir el id entero
        if cuenta_id and "." in cuenta_id:
            cuenta_id = str(int(float(cuenta_id)))
        alias = ALIAS.get(cuenta_id, cuenta_id)
        spend = s_num(r.get("spend"))
        moneda = "USD"
        if cuenta_id == CP1:
            moneda = "COP"
            spend = spend / TASA_COP_USD
        filas.append({
            "ventana_ini": fecha, "ventana_fin": fecha, "dias": 1, "rol_ventana": rol,
            "producto_key": producto_key(r.get("producto")),
            "producto": str(r.get("producto") or "").strip(),
            "cuenta_id": cuenta_id, "cuenta_alias": alias,
            "campana": str(r.get("campaignTitle") or "").strip(),
            "conjunto": str(r.get("adSetTitle") or "").strip(),
            "anuncio": str(r.get("adTitle") or "").strip(),
            "mensajes": int(s_num(r.get("messages"))),
            "clicks": int(s_num(r.get("clicks"))),
            "impresiones": int(s_num(r.get("impressions"))),
            "spend_usd": round(spend, 4),
            "ventas": int(s_num(r.get("sells"))),
            "total_q": round(s_num(r.get("total")), 2),
            "moneda_origen": moneda, "fuente": fuente,
            "ad_id": s_id(r.get("adId")),
        })
    return filas


def llave(f):
    return (f["ventana_ini"], f["producto_key"], f["conjunto"], f["anuncio"],
            f["fuente"], f["rol_ventana"])


def main():
    args = sys.argv[1:]
    rol, fuente, dry = "BASE", "LucidSales", False
    archivos = []
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--rol":
            i += 1; rol = args[i]
        elif a == "--fuente":
            i += 1; fuente = args[i]
        elif a == "--dry-run":
            dry = True
        elif a == "--dir":
            i += 1
            d = args[i]
            archivos += sorted(
                os.path.join(d, f) for f in os.listdir(d)
                if f.startswith("report-") and f.endswith(".xlsx")
                and not re.search(r"-[0-9a-f]{8}\.xlsx$", f)   # ignora copias con hash
            )
        else:
            archivos.append(a)
        i += 1

    if not archivos:
        raise SystemExit("Sin archivos. Uso: ingerir_lucidsales.py <xlsx...> | --dir <carpeta>")

    existentes = []
    if os.path.exists(FACT):
        with open(FACT, newline="", encoding="utf-8") as fh:
            existentes = list(csv.DictReader(fh))
    ya = {llave(f) for f in existentes}

    nuevas, dup, resumen = [], 0, {}
    for path in archivos:
        filas = leer_export(path, rol, fuente)
        n_ok = 0
        for f in filas:
            if llave(f) in ya:
                dup += 1
                continue
            ya.add(llave(f))
            nuevas.append(f)
            n_ok += 1
        d = fecha_de_nombre(path)
        resumen[d] = {
            "filas": n_ok,
            "ventas": sum(x["ventas"] for x in filas),
            "total_q": round(sum(x["total_q"] for x in filas), 2),
            "spend_usd": round(sum(x["spend_usd"] for x in filas), 2),
            "mensajes": sum(x["mensajes"] for x in filas),
        }

    # verificación de JOIN contra _DIM_CONJUNTOS
    dim = pd.read_csv(DIMC)
    conocidos = set(dim["conjunto_meta"].astype(str).str.strip())
    sin_dim = sorted({f["conjunto"] for f in nuevas
                      if f["conjunto"] and f["conjunto"] not in conocidos})

    print(f"archivos: {len(archivos)} · filas nuevas: {len(nuevas)} · duplicados omitidos: {dup}")
    for d in sorted(resumen):
        r = resumen[d]
        print(f"  {d}: {r['filas']:>3} filas · {r['ventas']:>3} ventas · "
              f"Q{r['total_q']:>9,.2f} · ${r['spend_usd']:>7,.2f} · {r['mensajes']:>4} msj")
    if sin_dim:
        print(f"\n⚠ {len(sin_dim)} conjuntos SIN dimensión (dar de alta en _DIM_CONJUNTOS.csv):")
        for c in sin_dim:
            print("   -", c)
    else:
        print("\n✅ JOIN con _DIM_CONJUNTOS cierra al 100%")

    if dry:
        print("\n[dry-run] no se escribió nada")
        return

    if nuevas:
        os.makedirs(BKDIR, exist_ok=True)
        stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        shutil.copy2(FACT, os.path.join(BKDIR, f"_FACT_VENTAS_{stamp}_pre-ingesta.csv.bak"))
        with open(FACT, "a", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=COLS)
            for f in nuevas:
                w.writerow(f)
        print(f"\n✅ {len(nuevas)} filas anexadas a _FACT_VENTAS.csv (backup en _ARCHIVO/backups_csv/)")


if __name__ == "__main__":
    main()
