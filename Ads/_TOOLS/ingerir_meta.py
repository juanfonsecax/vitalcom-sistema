#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ingerir_meta.py — carga exports de Ads Manager a _FACT_ENTREGA.csv

Uso:
    python Ads/_TOOLS/ingerir_meta.py <archivo.xlsx> [<archivo2.xlsx> ...]
    python Ads/_TOOLS/ingerir_meta.py --dir <carpeta>          (toma Informe-*.xlsx)
    ... [--producto PRODUCTO_KEY] [--dry-run]

`--producto` asigna TODO el export a ese producto: es el camino de una cuenta EXTERNA de un solo
producto (mercado CO, export manual del operador). Sin el, cada fila se clasifica por
_DIM_CONJUNTOS y por las palabras que declara _DIM_PRODUCTOS (producto_key, clave_campana, nombre).
La divisa del gasto sale de la columna "Divisa" del export; sin ella, de _DIM_PRODUCTOS.moneda; sin
ninguna de las dos el archivo se rechaza (no se asume USD). `spend_usd` siempre queda en USD.

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
  · Escribe con csv writer real (regla 11 de CLAUDE.md). Backup previo en _RESPALDOS/backups_csv/ (ver
    upsert_fact.respaldos_dir()).
  · Reporta el JOIN contra _DIM_CONJUNTOS.csv; un conjunto sin dimension se REPORTA, no se descarta.

NIVEL ANUNCIO (06-sep-2026)
---------------------------
Si el export trae "Nombre del anuncio", el archivo se ingiere en DOS niveles de una sola pasada:
  · _FACT_ENTREGA.csv          nivel conjunto, agregando los anuncios de cada conjunto (contrato intacto).
  · _FACT_ENTREGA_ANUNCIO.csv  nivel anuncio, con la FIRMA parseada a sus 5 ejes.
Sin el nivel anuncio la FASE 2 no mide nada: el CONCEPTO vive en el anuncio, y hasta hoy la
entrega solo llegaba agregada por conjunto (el eje canonico_id estaba ciego en el 89.3% del gasto).
La firma se lee del nombre — " ~ producto|angulo|concepto.canonico|NC|oferta|destino" — porque el
ad_id llego corrupto en 2006 de 2475 filas historicas y el JOIN por id es irrecuperable.
Un anuncio sin firma NO se descarta: entra con los ejes vacios y se cuenta como deuda.
"""
import sys, io, os, re, csv, glob, datetime, warnings, unicodedata

# Windows abre la consola en cp1252: un print con un simbolo fuera de ese mapa revienta con
# UnicodeEncodeError y el script sale con exit 1 AUNQUE el trabajo ya se completo (bug real del
# 18-ago en gen_dashboard.py, y sigue vivo en ingerir_lucidsales.py). Forzar UTF-8 lo cubre.
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
warnings.filterwarnings("ignore")

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from alias import canonico   # noqa: E402  (un renombrado en Meta no debe partir la serie)
import upsert_fact   # noqa: E402  (UPSERT/migracion de esquema compartida, ver su docstring)

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROD = os.path.join(BASE, "PRODUCTOS")
FACT = os.path.join(PROD, "_FACT_ENTREGA.csv")
FACT_AD = os.path.join(PROD, "_FACT_ENTREGA_ANUNCIO.csv")
DIMC = os.path.join(PROD, "_DIM_CONJUNTOS.csv")
DIMP = os.path.join(PROD, "_DIM_PRODUCTOS.csv")
BKDIR = upsert_fact.respaldos_dir(BASE, "backups_csv")

# P3 T3: _FACT_ENTREGA.csv / _FACT_ENTREGA_ANUNCIO.csv pasan a Postgres (core.entrega_conjunto_dia
# / core.entrega_anuncio_dia); el CSV en PRODUCTOS/ es el ESPEJO, regenerado por db/escribir.py
# despues del commit. Nunca se cae de vuelta al append/upsert directo sobre el archivo si Postgres
# falla. TENANT_ID: punto de override para pruebas, nunca toca `vitalcom` real (ver
# db/README.md, "aislamiento de pruebas").
sys.path.insert(0, os.path.join(BASE, "db"))
import cargar as db_cargar      # noqa: E402
import escribir as db_escribir  # noqa: E402

TENANT_ID = "vitalcom"

# Llave natural del hecho de entrega a nivel CONJUNTO (misma tupla que el set `llaves` de mas
# abajo usaba para el anti-duplicado): P3 T3, ahora tambien la llave de `db_escribir.upsert()`.
LLAVE_CONJUNTO = ("ventana_ini", "ventana_fin", "cuenta_alias", "campana", "conjunto", "fuente")

TASA_COP_USD = 3152.5          # APR-028, medida contra el banco
# Monedas de facturacion con tasa declarada (unidades locales por USD). Una divisa fuera de esta tabla
# y distinta de USD BLOQUEA el archivo: convertir sin tasa es inventar el numero.
TASAS_A_USD = {"COP": TASA_COP_USD}
CP1 = "1346891653335162"

ALIAS = {
    "GTR7": "598687956219141",
    "GTR0": "1665221077707961",
    "GTR1": "824783947334627",
    "GTR13": "916746367261028",
    "CP1": "1346891653335162",
    "GTR3": "581490137794343",
}

# Nombres historicos que Meta todavia trae en campanas viejas y que no son producto_key ni salen de
# _DIM_PRODUCTOS. Solo aliases: los productos y sus palabras salen de la dimension.
ALIAS_NOMBRE = {"VARICES": "VARICOSE"}

COLS = ["ventana_ini", "ventana_fin", "dias", "producto_key", "cuenta_id", "cuenta_alias",
        "campana", "conjunto", "mensajes", "clicks_totales", "link_clicks", "impresiones",
        "spend_usd", "pct_conv_clic_enlace", "fuente"]

# El nivel anuncio lleva los mismos hechos mas el nombre, el ad_id real de Meta y los 5
# ejes que viajan en la firma. `ad_id` se agrego 22-sep-2026 (g07 T1): antes el JOIN con
# _FACT_VENTAS.csv solo podia hacerse por NOMBRE, y un renombrado en Meta lo rompia. Una
# fila escrita antes de este cambio no tiene esta columna en su CSV: leerla pasa por
# upsert_fact.leer_migrado(), que la completa con "" — nunca se inventa el id.
COLS_AD = (COLS[:8] + ["anuncio", "ad_id", "firma", "angulo_key", "concepto_key", "canonico_id",
                       "nivel_conciencia", "oferta_key", "destino_key"] + COLS[8:])

# nombre de columna -> las variantes que ha usado el exportador
COLMAP = {
    "campana":     ["Nombre de la campaña"],
    "conjunto":    ["Nombre del conjunto de anuncios"],
    "divisa":      ["Divisa"],
    "spend":       ["Importe gastado", "Importe gastado (USD)"],
    "impresiones": ["Impresiones"],
    "link_clicks": ["Clics en el enlace"],
    "clicks_tot":  ["Clics (todos)"],
    "anuncio":     ["Nombre del anuncio"],
    "conv_wa":     ["TASA DE CONVERSION A WHATSAPP", "TASA DE CONVERSIÓN A WHATSAPP"],
    "ini":         ["Inicio del informe"],
    "fin":         ["Fin del informe"],
}


EJES = ["angulo_key", "concepto_key", "canonico_id", "nivel_conciencia",
        "oferta_key", "destino_key"]


def parsear_firma(anuncio):
    """'ANGULO_VID_A ~ PROD|ANG|C3.CN07|NC2|2X1|BOT_V1' -> (firma, {ejes}).

    Sin firma devuelve ejes vacios: el dato entra igual y validar_parametros.py lo
    cuenta como deuda. Descartarlo perderia el gasto, que es peor que no clasificarlo.
    """
    vacio = {e: "" for e in EJES}
    txt = str(anuncio or "")
    if " ~ " not in txt:
        return "", vacio
    f = txt.split(" ~ ", 1)[1].strip()
    p = [x.strip() for x in f.split("|")]
    if len(p) < 6:
        p += [""] * (6 - len(p))
    cc = p[2]
    nc = p[3][2:] if p[3].upper().startswith("NC") else p[3]
    limpio = lambda v: "" if v in ("?", "") else v
    return f, {
        "angulo_key":       limpio(p[1]),
        "concepto_key":     limpio(cc.split(".")[0]),
        "canonico_id":      limpio(cc.split(".")[1]) if "." in cc else "",
        "nivel_conciencia": limpio(nc),
        "oferta_key":       limpio(p[4]),
        "destino_key":      limpio(p[5]),
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


def _sin_tildes(txt):
    return "".join(c for c in unicodedata.normalize("NFD", str(txt or ""))
                   if unicodedata.category(c) != "Mn")


def cargar_productos_meta(path=None):
    """producto_key -> {kw, moneda, cuenta_alias} leido de _DIM_PRODUCTOS.csv (el dueno del dato).

    Las palabras que reconocen un producto en el nombre de campana/conjunto salen de lo que la
    dimension ya declara: el producto_key, las partes de `clave_campana` (p.ej. "OVULOS / PURITY") y la
    primera palabra de nombre_display/slug_carpeta (>= 4 letras). Mismo criterio que
    ingerir_lucidsales.cargar_productos, mas clave_campana. Sin tildes y en mayusculas.
    `moneda` es la moneda de la CUENTA publicitaria del producto (no la de venta)."""
    out = {}
    with open(path or DIMP, newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            pk = (r.get("producto_key") or "").strip()
            if not pk:
                continue
            kws = {pk, pk.replace("_", " ")}
            for parte in re.split(r"[/,;|]", r.get("clave_campana") or ""):
                parte = parte.strip()
                if len(parte) >= 4:
                    kws.add(parte)
            for campo in ("nombre_display", "slug_carpeta"):
                v = (r.get(campo) or "").strip()
                if v:
                    primera = re.split(r"[\s_]+", v)[0]
                    if len(primera) >= 4:
                        kws.add(primera)
            out[pk] = {"kw": sorted({_sin_tildes(k).upper() for k in kws if k}),
                       "moneda": (r.get("moneda") or "").strip().upper(),
                       "cuenta_alias": (r.get("cuenta_alias") or "").strip().upper()}
    return out


_CACHE_PRODUCTOS = {}


def _productos_cacheados():
    """cargar_productos_meta() del DIMP vigente, releido si el archivo cambio (bajar_meta_insights
    llama producto_de() por fila)."""
    try:
        marca = (DIMP, os.path.getmtime(DIMP))
    except OSError:
        marca = (DIMP, None)
    if _CACHE_PRODUCTOS.get("marca") != marca:
        _CACHE_PRODUCTOS["marca"] = marca
        _CACHE_PRODUCTOS["valor"] = cargar_productos_meta()
    return _CACHE_PRODUCTOS["valor"]


def productos_externos(productos=None):
    """Conjunto de producto_key cuya cuenta publicitaria es EXTERNA (sin cuenta_id, sin MCP, sin API):
    solo entran por export manual. La corrida nocturna nunca los toca."""
    productos = _productos_cacheados() if productos is None else productos
    return {pk for pk, f in productos.items() if f["cuenta_alias"] == "EXTERNA"}


def producto_de(campana, conjunto, dim, productos=None):
    """Primero la dimension (dueno del dato); si no esta, el nombre contra las palabras de
    _DIM_PRODUCTOS (`productos`, por defecto el archivo vigente)."""
    k = str(conjunto or "").strip()
    if k in dim:
        return dim[k]
    if canonico(k) in dim:
        return dim[canonico(k)]
    productos = _productos_cacheados() if productos is None else productos
    txt = _sin_tildes(str(campana or "") + "_" + str(conjunto or "")).upper()
    for pk, f in productos.items():
        if any(kw in txt for kw in f["kw"]):
            return pk
    for pat, pk in ALIAS_NOMBRE.items():
        if pat in txt:
            return pk
    return "SIN_CLASIFICAR"


def leer_dim():
    """conjunto_meta -> producto_key, y el set de conjuntos con angulo declarado.

    Cada conjunto se indexa por su nombre tal cual y por su nombre canonico, para que un
    export posterior a un renombrado siga cruzando contra la misma fila de dimension.
    """
    dim, con_angulo = {}, set()
    if os.path.exists(DIMC):
        for r in csv.DictReader(open(DIMC, encoding="utf-8")):
            c = (r.get("conjunto_meta") or "").strip()
            if not c:
                continue
            pk = r.get("producto_key") or "SIN_CLASIFICAR"
            for k in {c, canonico(c)}:
                dim[k] = pk
                if (r.get("angulo_key") or "").strip():
                    con_angulo.add(k)
    return dim, con_angulo


def fecha(v):
    try:
        return pd.to_datetime(v).strftime("%Y-%m-%d")
    except Exception:
        return str(v)[:10]


def procesar(path, dim, productos=None, forzar=None):
    """`forzar` = producto_key que se le asigna a TODAS las filas (export de una cuenta EXTERNA de un
    solo producto); si no, cada fila se clasifica por la dimension y por el nombre."""
    productos = _productos_cacheados() if productos is None else productos
    df = pd.read_excel(path)
    c_camp = col(df, "campana")
    if c_camp is None:
        return None, None, f"sin columna de campana (columnas: {list(df.columns)[:4]}...)"
    c_ini, c_fin = col(df, "ini"), col(df, "fin")
    if c_ini is None or c_fin is None:
        return None, None, "sin columnas 'Inicio/Fin del informe'"

    det = df[df[c_camp].notna()].copy()          # descarta la fila de TOTAL DE CUENTA
    if det.empty:
        return None, None, "sin filas de detalle"

    ini, fin = fecha(df[c_ini].iloc[0]), fecha(df[c_fin].iloc[0])
    dias = (datetime.date.fromisoformat(fin) - datetime.date.fromisoformat(ini)).days + 1
    fuente = f"AdsManager-export-{dias}d"

    c_conj, c_div = col(df, "conjunto"), col(df, "divisa")
    c_sp, c_imp = col(df, "spend"), col(df, "impresiones")
    c_lc, c_ct, c_wa = col(df, "link_clicks"), col(df, "clicks_tot"), col(df, "conv_wa")
    c_ad = col(df, "anuncio")               # presente solo en los exports nivel anuncio

    filas = []
    for _, r in det.iterrows():
        conjunto = str(r[c_conj]).strip() if c_conj and pd.notna(r[c_conj]) else ""
        campana = str(r[c_camp]).strip()
        anuncio = str(r[c_ad]).strip() if c_ad and pd.notna(r[c_ad]) else ""
        al = alias_de(conjunto, campana)
        pk = forzar or producto_de(campana, conjunto, dim, productos)
        ficha = productos.get(pk, {})
        if not al and ficha.get("cuenta_alias") == "EXTERNA":
            al = "EXTERNA"
        sp = num(r[c_sp]) if c_sp else 0.0
        # La divisa sale del export; sin esa columna, de la cuenta del producto (_DIM_PRODUCTOS.moneda).
        # Nunca se asume USD: sin ninguna de las dos el archivo se rechaza.
        if c_div and pd.notna(r[c_div]):
            div = str(r[c_div]).strip().upper()
        elif ficha.get("moneda"):
            div = ficha["moneda"]
        elif al == "CP1":
            div = "COP"
        else:
            return None, None, (f"sin columna 'Divisa' y el producto «{pk}» no declara moneda en "
                                f"_DIM_PRODUCTOS.csv: no se sabe en que moneda esta el gasto")
        if div != "USD" or al == "CP1":
            tasa = TASAS_A_USD.get("COP" if al == "CP1" else div)
            if tasa is None:
                return None, None, (f"divisa {div} sin tasa declarada en TASAS_A_USD: convertir a USD "
                                    f"sin tasa es inventar el numero")
            sp = sp / tasa
        lc = int(num(r[c_lc])) if c_lc else 0
        wa = num(r[c_wa]) if c_wa else 0.0
        filas.append({
            "ventana_ini": ini, "ventana_fin": fin, "dias": dias,
            "producto_key": pk,
            "cuenta_id": ALIAS.get(al, ""), "cuenta_alias": al,
            "campana": campana, "conjunto": conjunto, "anuncio": anuncio,
            "mensajes_raw": wa * lc,
            "clicks_totales": int(num(r[c_ct])) if c_ct else 0,
            "link_clicks": lc,
            "impresiones": int(num(r[c_imp])) if c_imp else 0,
            "spend_usd": sp,
            "fuente": fuente,
        })

    def cerrar(d):
        """Redondea al final: sumar valores ya redondeados pierde mensajes."""
        d = dict(d)
        lc = d["link_clicks"]
        d["mensajes"] = int(round(d.pop("mensajes_raw")))
        d["pct_conv_clic_enlace"] = round(d["mensajes"] / lc * 100, 1) if lc else 0.0
        d["spend_usd"] = round(d["spend_usd"], 2)
        return d

    # Nivel ANUNCIO: solo si el export lo trae. La firma sale del nombre, no de una tabla.
    ads = []
    if c_ad:
        for d in filas:
            f, ejes = parsear_firma(d["anuncio"])
            ads.append({**cerrar(d), "firma": f, **ejes})

    # Nivel CONJUNTO: si el export era nivel anuncio, se agrega; si no, ya viene asi.
    # El contrato de _FACT_ENTREGA.csv no cambia, venga el export del nivel que venga.
    if c_ad:
        agg = {}
        for d in filas:
            k = (d["cuenta_alias"], d["campana"], d["conjunto"])
            a = agg.setdefault(k, {**d, "mensajes_raw": 0.0, "clicks_totales": 0,
                                    "link_clicks": 0, "impresiones": 0, "spend_usd": 0.0})
            for c in ("mensajes_raw", "clicks_totales", "link_clicks", "impresiones", "spend_usd"):
                a[c] += d[c]
        base = list(agg.values())
    else:
        base = filas
    out = []
    for d in base:
        d = cerrar(d)
        d.pop("anuncio", None)
        out.append({c: d[c] for c in COLS})
    return out, ads, None


def main():
    args = sys.argv[1:]
    dry = "--dry-run" in args
    args = [a for a in args if a != "--dry-run"]
    forzar = None
    if "--producto" in args:
        i = args.index("--producto")
        if i + 1 >= len(args):
            raise SystemExit("--producto necesita un producto_key.")
        forzar = args[i + 1]
        args = args[:i] + args[i + 2:]
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
    productos = cargar_productos_meta()
    if forzar:
        if forzar not in productos:
            raise SystemExit(f"--producto {forzar}: no tiene fila en _DIM_PRODUCTOS.csv.")
        import mercado
        try:
            perfil = mercado.perfil_de_producto(forzar, BASE)
        except mercado.MercadoError as e:
            raise SystemExit(f"--producto {forzar}: {e}")
        print(f"producto {forzar} · mercado {perfil['mercado']} · venta en {perfil['moneda']} · "
              f"cuenta {productos[forzar]['cuenta_alias'] or '?'}")
    existentes = list(csv.DictReader(open(FACT, encoding="utf-8"))) if os.path.exists(FACT) else []
    llaves = {(r["ventana_ini"], r["ventana_fin"], r["cuenta_alias"], r["campana"],
               r["conjunto"], r["fuente"]) for r in existentes}

    ads_ex = list(csv.DictReader(open(FACT_AD, encoding="utf-8"))) if os.path.exists(FACT_AD) else []
    llaves_ad = {(r["ventana_ini"], r["ventana_fin"], r["cuenta_alias"], r["campana"],
                  r["conjunto"], r["anuncio"], r["fuente"]) for r in ads_ex}

    nuevas, nuevos_ads, dup, dup_ad = [], [], 0, 0
    errores, sin_dim, sin_cuenta, sin_firma = [], set(), set(), []
    for f in archivos:
        filas, ads, err = procesar(f, dim, productos, forzar)
        for r in (ads or []):
            k = (r["ventana_ini"], r["ventana_fin"], r["cuenta_alias"], r["campana"],
                 r["conjunto"], r["anuncio"], r["fuente"])
            if k in llaves_ad:
                dup_ad += 1
                continue
            llaves_ad.add(k)
            nuevos_ads.append(r)
            if not r["firma"]:
                sin_firma.append((r["anuncio"], r["spend_usd"]))
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
            if r["conjunto"] and canonico(r["conjunto"]) not in con_angulo:
                sin_dim.add(r["conjunto"])
            if not r["cuenta_alias"]:
                sin_cuenta.add(r["campana"])
        agg = nuevas[n0:]
        print(f"  {os.path.basename(f)[:44]:46} {agg[0]['ventana_ini'] if agg else '-':10} "
              f"{len(agg):3} filas · {sum(x['mensajes'] for x in agg):4} msj · "
              f"${sum(x['spend_usd'] for x in agg):8.2f}")

    print(f"\narchivos: {len(archivos)} · filas nuevas: {len(nuevas)} · duplicados omitidos: {dup}")
    if nuevos_ads or dup_ad:
        print(f"nivel ANUNCIO: {len(nuevos_ads)} filas nuevas · {dup_ad} duplicados omitidos")
    elif archivos and not errores:
        print("! el export NO trae 'Nombre del anuncio': solo se cargo el nivel conjunto.")
        print("  Bajalo desglosado por ANUNCIO o el eje CONCEPTO sigue ciego (FASE 2 no mide).")
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

    if sin_firma:
        gasto = sum(g for _, g in sin_firma)
        print(f"\n! {len(sin_firma)} anuncios SIN FIRMA en el nombre (${gasto:.2f} de gasto sin ejes).")
        print("  Se cargan igual y cuentan como deuda; el nombre se corrige en Meta, no aca.")
        for a, g in sorted(sin_firma, key=lambda x: -x[1])[:8]:
            print(f"    ${g:7.2f}  {a[:66]}")

    if dry:
        print("\n[dry-run] no se escribio nada.")
        return 0
    if not nuevas and not nuevos_ads:
        print("\nnada que escribir.")
        return 0

    # P3 T3: ambos hechos pasan por Postgres (db/escribir.py), nunca directo al CSV. `nuevas`/
    # `nuevos_ads` ya vienen deduplicados contra `existentes`/`ads_ex` (leidos del CSV mas arriba,
    # que el guardia de drift ya valida como espejo fiel de la base): el upsert por llave sobre
    # `raw.*` reproduce exactamente el mismo resultado que el append/upsert_fact de antes, solo
    # que el almacen cambia. El guardia de drift corre PRIMERO para cada tabla que se vaya a tocar.
    try:
        con = db_cargar.conectar()
    except Exception as exc:
        print(f"\n⛔ Postgres no disponible: no se pudo escribir _FACT_ENTREGA*.csv (nunca se "
              f"escribe el CSV directo). Detalle: {exc}", file=sys.stderr)
        return 1
    # El directorio de escritura sale de FACT/FACT_AD (nunca de la constante PROD): las pruebas
    # monkeypatchean FACT/FACT_AD a un directorio temporal (patch.object(im, "FACT", ...)), y si
    # el mirror se regenerara sobre PROD igual, escribiria en la carpeta PRODUCTOS/ real aunque la
    # prueba haya redirigido FACT -- exactamente el defecto encontrado en vivo durante T3 (una
    # prueba con datos ficticios pisando/mezclando PRODUCTOS/_FACT_ENTREGA*.csv reales).
    prod_dir_conjunto = os.path.dirname(FACT)
    prod_dir_anuncio = os.path.dirname(FACT_AD)
    try:
        if nuevas:
            db_escribir.verificar_csv_sincronizado(con, "entrega_conjunto_dia", prod_dir_conjunto,
                                                    tenant_id=TENANT_ID)
            _, n_nuevas_c, *_ = db_escribir.upsert(
                con, "entrega_conjunto_dia", nuevas, key=LLAVE_CONJUNTO, prod_dir=prod_dir_conjunto,
                bkdir=BKDIR, tenant_id=TENANT_ID, reconciliar=upsert_fact.superar_por_api_directa)
            print(f"\nescritas {n_nuevas_c} filas en {os.path.relpath(FACT, BASE)} "
                  f"(Postgres es la verdad; espejo regenerado)")
        if nuevos_ads:
            # Misma identidad anti-duplicado de siempre (22-sep-2026, g07 T1): `nuevos_ads` ya
            # viene deduplicado contra `ads_ex`, asi que en la practica esto agrega, no reemplaza.
            llave_ad = ("ventana_ini", "ventana_fin", "cuenta_alias", "campana", "conjunto",
                        "anuncio", "fuente")
            db_escribir.verificar_csv_sincronizado(con, "entrega_anuncio_dia", prod_dir_anuncio,
                                                    tenant_id=TENANT_ID)
            _, n_nuevas_a, *_ = db_escribir.upsert(
                con, "entrega_anuncio_dia", nuevos_ads, key=llave_ad, prod_dir=prod_dir_anuncio,
                bkdir=BKDIR, tenant_id=TENANT_ID, reconciliar=upsert_fact.superar_por_api_directa)
            print(f"escritas {n_nuevas_a} filas en {os.path.relpath(FACT_AD, BASE)} "
                  f"(Postgres es la verdad; espejo regenerado)")
    except db_escribir.ErrorEscritura as exc:
        print(f"\n⛔ {exc}", file=sys.stderr)
        return 1
    finally:
        con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
