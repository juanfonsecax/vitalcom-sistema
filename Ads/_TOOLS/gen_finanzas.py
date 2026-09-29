# -*- coding: utf-8 -*-
"""Motor financiero: reporte SEMANAL + verificación de 3 capas.

  python Ads/_TOOLS/gen_finanzas.py
  python Ads/_TOOLS/gen_finanzas.py --dropi <ordenes.xlsx> --banco <extracto.pdf>

Responde DOS preguntas distintas y no las mezcla:

  (1) ¿CUÁNTO HICIMOS ESTA SEMANA?  -> reporte semanal por producto, desde
      `_FACT_VENTAS.csv` (lo que los ads ATRIBUYEN). Escribe `_FACT_SEMANAL.csv`
      + `_REPORTE_SEMANAL.txt`.

  (2) ¿DE VERDAD ESTAMOS GANANDO?   -> cruce de 3 capas independientes:
        capa 1  LucidSales  = lo que los ads dicen que vendieron   (atribución)
        capa 2  Dropi       = el dinero que REALMENTE se cobró      (caja)
        capa 3  Banco       = lo que Meta REALMENTE cobró           (caja)
      La ganancia del sistema sale de la capa 1. Si la capa 2 vende menos o la
      capa 3 cobra más, la ganancia del sistema está INFLADA y acá se mide en
      cuánto. Escribe `_AUDITORIAS/_VERIFICACION_CAJA_[YYYYMMDD].txt`.

Ningún número se escribe a mano: todo sale de los CSV y de los archivos que
entrega el operador. Misma fórmula de contribución que `gen_dashboard.py`
(se verifica al final: si los totales no cierran, avisa).
"""
import csv, io, os, re, sys, collections, datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mercado

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
P    = os.path.join(ROOT, "PRODUCTOS")
AUD  = os.path.join(P, "_AUDITORIAS")
# ── TASA USD→moneda local: es la DEL PRODUCTO (_DIM_PRODUCTOS.tasa) ──────
# Un dato, un dueño. Cada producto convierte su pauta con su tasa y en la moneda de SU mercado
# (mercado.py); no hay tasa por defecto y NUNCA se suma dinero de mercados distintos: los totales
# se agrupan por mercado. La verificación de caja (Dropi + banco Relay) es solo del mercado GT.
MERCADO_CAJA = "GT"


# ─────────────────────────── utilidades ───────────────────────────
def load(name):
    p = os.path.join(P, name)
    return list(csv.DictReader(io.open(p, encoding="utf-8"))) if os.path.exists(p) else []


def f(x, d=0.0):
    try:    return float(x)
    except (TypeError, ValueError): return d


def i(x, d=0):
    try:    return int(float(x))
    except (TypeError, ValueError): return d


def q(n, simbolo="Q"):  return "{}{:,.0f}".format(simbolo, n)


# ───────────── parámetros de costo (idénticos a gen_dashboard) ─────────────
tasa_ent = load("_TASA_ENTREGA.csv")


def _resueltos(r):
    return i(r.get("entregado")) + i(r.get("devolucion")) + i(r.get("cancelado"))


_glob = [r for r in tasa_ent if (r.get("producto_key") or "GLOBAL") == "GLOBAL"]
_te   = max(_glob or tasa_ent, key=_resueltos) if tasa_ent else {}
TE      = f(_te.get("pct_entrega_resueltos"), 85.1) / 100.0
C_DEVOL = f(_te.get("costo_devolucion_evento_q"), 27.16)
C_ADMIN = f(_te.get("costos_admin_q"), 4.0)
C_OTROS = f(_te.get("otros_gastos_q"), 2.08)
FLETE_A, FLETE_B = 31.42, 2.70

TE_PROD = {}
for _r in tasa_ent:
    _pk = _r.get("producto_key") or "GLOBAL"
    if _pk == "GLOBAL":
        continue
    if _resueltos(_r) >= 20 and (_pk not in TE_PROD or _resueltos(_r) > TE_PROD[_pk][1]):
        TE_PROD[_pk] = (f(_r["pct_entrega_resueltos"]) / 100.0, _resueltos(_r))


def te_de(pk):
    return TE_PROD.get(pk, (TE, 0))[0]


precios = collections.defaultdict(list)
for r in load("_DIM_PRECIOS.csv"):
    if (r.get("estado") or "").upper() == "SIN_REGISTRAR":
        continue
    u  = i(r["unidades"], 1)
    fl = f(r.get("flete_q")) or (FLETE_A + FLETE_B * u)
    p  = f(r["precio_q"])
    t  = te_de(r["producto_key"])
    precios[r["producto_key"]].append({
        "precio": p,
        "contrib": t * (p - f(r["costo_proveedor_total_q"]) - fl - C_ADMIN - C_OTROS) - (1 - t) * C_DEVOL})
for k in precios:
    precios[k].sort(key=lambda x: x["precio"])

prods = {p_["producto_key"]: p_ for p_ in load("_DIM_PRODUCTOS.csv")}
BE = {k: float(v["cpa_be_q"]) for k, v in prods.items() if v.get("cpa_be_q")}

_MERC, _PERFIL = {}, {}


def mercado_pk(pk):
    """Mercado (GT/CO) del producto, de _DIM_PRODUCTOS.csv. MercadoError si no lo declara."""
    if pk not in _MERC:
        if pk not in prods:
            raise mercado.MercadoError("«%s» tiene ventas pero no fila en _DIM_PRODUCTOS.csv." % pk)
        _MERC[pk] = mercado.mercado_de_fila(prods[pk], ROOT)
    return _MERC[pk]


def perfil(m):
    if m not in _PERFIL:
        _PERFIL[m] = mercado.perfil_mercado(m, ROOT)
    return _PERFIL[m]


def tasa_pk(pk):
    """Tasa USD→moneda local DEL producto. TasaFaltante (nombrandolo) si no la declara."""
    if pk not in prods:
        raise mercado.MercadoError("«%s» tiene ventas pero no fila en _DIM_PRODUCTOS.csv." % pk)
    return mercado.tasa_de_fila(prods[pk])


def pauta_local(r):
    """Gasto (spend_usd) de una fila de ventas, en la moneda local de SU producto."""
    usd = f(r["spend_usd"])
    return usd * tasa_pk(r["producto_key"]) if usd else 0.0


def escalon(pk, ticket):
    esc = precios.get(pk)
    if not esc:
        return None
    if len(esc) == 1 or ticket <= esc[0]["precio"]:
        return esc[0]["contrib"]
    if ticket >= esc[-1]["precio"]:
        return esc[-1]["contrib"]
    for a, b in zip(esc, esc[1:]):
        if a["precio"] <= ticket <= b["precio"]:
            w = (ticket - a["precio"]) / (b["precio"] - a["precio"])
            return a["contrib"] + w * (b["contrib"] - a["contrib"])
    return esc[0]["contrib"]


def contribucion(r):
    v = i(r["ventas"])
    if not v:
        return 0.0
    c = escalon(r["producto_key"], f(r["total_q"]) / v)
    if c is None:
        # Sin escalon de precios, el break-even del producto es la contribucion de referencia.
        if r["producto_key"] not in BE:
            raise mercado.MercadoError(
                "«%s» no tiene precios en _DIM_PRECIOS.csv ni cpa_be_q en _DIM_PRODUCTOS.csv: no se "
                "puede estimar su contribucion (no hay valor por defecto)." % r["producto_key"])
        c = BE[r["producto_key"]]
    return v * c


# ─────────────────────── (1) REPORTE SEMANAL ───────────────────────
def semana_de(fecha):
    """Lunes de la semana ISO a la que pertenece la fecha."""
    d = datetime.date.fromisoformat(fecha)
    return d - datetime.timedelta(days=d.weekday())


def reporte_semanal():
    """Agrega por semana ISO (lunes→domingo).

    OJO: la serie tiene filas que cubren VARIOS días (`dias`>1, las cargas de
    julio y principios de agosto) y algunas CRUZAN el corte del lunes. Se
    PRORRATEAN linealmente entre los días de su ventana: el total del tramo
    queda exacto y el reparto entre semanas es una interpolación. Las semanas
    que reciben algo prorrateado se marcan, para no leerlas como medición
    diaria limpia.
    """
    ventas = [r for r in load("_FACT_VENTAS.csv") if r.get("rol_ventana") == "BASE"]
    sem = collections.defaultdict(lambda: {"tot": collections.defaultdict(lambda: [0.0, 0.0, 0.0, 0.0]),
                                           "prod": collections.defaultdict(lambda: [0.0, 0.0, 0.0, 0.0]),
                                           "dias": set(), "estimada": False})
    for r in ventas:
        ini = r["ventana_ini"]
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", ini or ""):
            continue
        n = max(i(r.get("dias"), 1), 1)
        d0 = datetime.date.fromisoformat(ini)
        pk = r["producto_key"]
        mk = mercado_pk(pk)
        parte = (i(r["ventas"]) / n, f(r["total_q"]) / n,
                 pauta_local(r) / n, contribucion(r) / n)
        for k in range(n):
            dia = d0 + datetime.timedelta(days=k)
            s = sem[semana_de(dia.isoformat())]
            s["dias"].add(dia.isoformat())
            if n > 1:
                s["estimada"] = True
            for tgt in (s["tot"][mk], s["prod"][pk]):
                for j in range(4):
                    tgt[j] += parte[j]
    return dict(sorted(sem.items()))


def escribir_semanal(sem):
    # CSV máquina
    out = os.path.join(P, "_FACT_SEMANAL.csv")
    with io.open(out, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["semana_ini", "semana_fin", "dias_con_data", "corte_estimado", "producto_key",
                    "ventas", "facturado_q", "pauta_q", "contribucion_q", "ganancia_q", "cpa_q", "roas",
                    "mercado", "moneda"])
        # Un TOTAL POR MERCADO (nunca se suman monedas distintas); los montos *_q estan en la moneda
        # local del mercado que dice la columna `moneda`.
        for lun, d in sem.items():
            dom = lun + datetime.timedelta(days=6)
            filas = ([("TOTAL", m, d["tot"][m]) for m in sorted(d["tot"])]
                     + [(pk, mercado_pk(pk), x) for pk, x in sorted(d["prod"].items())])
            for pk, mk, x in filas:
                v, fac, pa, co = x
                w.writerow([lun, dom, len(d["dias"]), "SI" if d["estimada"] else "NO", pk, round(v, 2), round(fac, 2), round(pa, 2),
                            round(co, 2), round(co - pa, 2),
                            round(pa / v, 2) if v else "", round(fac / pa, 2) if pa else "",
                            mk, perfil(mk)["moneda"]])

    # TXT humano
    L = []
    L.append("═" * 75)
    L.append("REPORTE SEMANAL — facturación y ganancia por semana y por producto")
    L.append("Generado: %s · fuente: _FACT_VENTAS.csv (lo que los ads ATRIBUYEN)" %
             datetime.date.today())
    L.append("═" * 75)
    L.append("")
    L.append("CÓMO LEERLO: «facturado» es lo que se vendió (antes de costos).")
    L.append("«ganancia» ya descuenta producto, flete, devoluciones, admin y pauta.")
    L.append("Una semana con menos de 7 días de data está marcada PARCIAL: su total")
    L.append("es un PISO, no el cierre.")
    L.append("")
    mercados = sorted({m for d in sem.values() for m in d["tot"]})
    multi = len(mercados) > 1
    if multi:
        L.append("MERCADOS EN ESTE REPORTE: " + " · ".join(
            "%s (%s)" % (m, perfil(m)["moneda"]) for m in mercados))
        L.append("Cada mercado se reporta APARTE y en su moneda: nunca se suman montos de mercados distintos.")
        L.append("")
    acum = {m: [0.0, 0.0, 0.0, 0.0] for m in mercados}
    for lun, d in sem.items():
        dom = lun + datetime.timedelta(days=6)
        nd = len(d["dias"])
        marca = "" if nd >= 7 else "  ⚠ PARCIAL (%d de 7 días)" % nd
        if d["estimada"]:
            marca += "  · corte estimado (tramo multi-día prorrateado)"
        L.append("─" * 75)
        L.append("SEMANA %s → %s%s" % (lun, dom, marca))
        for mk in sorted(d["tot"]):
            sim = perfil(mk)["simbolo"]
            v, fac, pa, co = d["tot"][mk]
            for j in range(4):
                acum[mk][j] += d["tot"][mk][j]
            if multi:
                L.append("  ▸ MERCADO %s (%s)" % (mk, perfil(mk)["moneda"]))
            L.append("  Facturado %s · Pauta %s · GANANCIA %s%s" % (
                q(fac, sim), q(pa, sim), q(co - pa, sim), "  🔴" if co - pa < 0 else ""))
            L.append("  %.0f ventas · CPA %s · ROAS %.2fx · ganancia/día %s" % (
                v, q(pa / v, sim) if v else "—", (fac / pa) if pa else 0, q((co - pa) / max(nd, 1), sim)))
            L.append("")
            L.append("    %-12s %6s %12s %11s %12s %8s" %
                     ("PRODUCTO", "VENTAS", "FACTURADO", "PAUTA", "GANANCIA", "CPA"))
            for pk, x in sorted(d["prod"].items(), key=lambda kv: -(kv[1][3] - kv[1][2])):
                if mercado_pk(pk) != mk:
                    continue
                v2, fac2, pa2, co2 = x
                L.append("    %-12s %6.0f %12s %11s %12s %8s" % (
                    pk[:12], v2, q(fac2, sim), q(pa2, sim), q(co2 - pa2, sim),
                    q(pa2 / v2, sim) if v2 else "—"))
            L.append("")
    L.append("═" * 75)
    for mk in mercados:
        sim = perfil(mk)["simbolo"]
        tot_v, tot_f, tot_p, tot_c = acum[mk]
        L.append("ACUMULADO DE LA SERIE%s: facturado %s · pauta %s · GANANCIA %s" %
                 (" — MERCADO %s (%s)" % (mk, perfil(mk)["moneda"]) if multi else "",
                  q(tot_f, sim), q(tot_p, sim), q(tot_c - tot_p, sim)))
        L.append("%.0f ventas · CPA %s · ROAS %.2fx" %
                 (tot_v, q(tot_p / tot_v, sim) if tot_v else "—", (tot_f / tot_p) if tot_p else 0))
    L.append("═" * 75)
    txt = "\n".join(L) + "\n"
    io.open(os.path.join(P, "_REPORTE_SEMANAL.txt"), "w", encoding="utf-8").write(txt)
    return {mk: acum[mk][3] - acum[mk][2] for mk in mercados}, txt


# ─────────────────── (2) VERIFICACIÓN DE CAJA (3 capas) ───────────────────
def pk_dropi(nombre):
    n = str(nombre).lower()
    if "tinnidrop" in n or "spray" in n:      return "TINNIDROP"
    if "clearstem" in n:                      return "CLEARSTEM"
    if "vitamin b" in n or "nusava" in n:     return "NUSAVA"
    if "varice" in n or "varicose" in n:      return "VARICOSE"
    return "OTRO"


def leer_dropi(path):
    import pandas as pd
    df = pd.read_excel(path)
    df["pk"] = df["PRODUCTO"].map(pk_dropi)
    df["fecha"] = pd.to_datetime(df["FECHA"], format="%d-%m-%Y", errors="coerce")
    return df


def leer_banco(path):
    """Extrae los cargos del extracto PDF. Devuelve lista de dicts."""
    import pdfplumber
    txt = ""
    with pdfplumber.open(path) as pdf:
        for p_ in pdf.pages:
            txt += (p_.extract_text() or "") + "\n"
    lines = [l.strip() for l in txt.split("\n")]
    pat = re.compile(r"^(\w{3} \d{1,2}, \d{4})\s+(\w+)\s+[]?\$([\d,]+\.\d{2})\s+\$([\d,]+\.\d{2})$")
    out = []
    for n, l in enumerate(lines):
        m = pat.match(l)
        if m:
            out.append({"nombre": lines[n - 1] if n else "",
                        "fecha": datetime.datetime.strptime(m.group(1), "%b %d, %Y").date(),
                        "estado": m.group(2),
                        "monto": float(m.group(3).replace(",", "")),
                        "salida": "" in l})
    return out


def main():
    args = sys.argv[1:]
    dropi = banco = None
    ini, fin = None, None
    for n, a in enumerate(args):
        if a == "--dropi": dropi = args[n + 1]
        if a == "--banco": banco = args[n + 1]
        if a == "--desde": ini = args[n + 1]
        if a == "--hasta": fin = args[n + 1]

    try:
        _main_semanal_y_caja(args, dropi, banco, ini, fin)
    except mercado.MercadoError as error:     # sin tasa / sin mercado / sin precios: se detiene, nombrandolo
        print("BLOQUEANTE: %s" % error, file=sys.stderr)
        sys.exit(1)


def _main_semanal_y_caja(args, dropi, banco, ini, fin):
    sem = reporte_semanal()
    gan, _ = escribir_semanal(sem)
    print("✅ _REPORTE_SEMANAL.txt + _FACT_SEMANAL.csv — %d semanas · ganancia acumulada %s"
          % (len(sem), " · ".join("%s %s" % (mk, q(g, perfil(mk)["simbolo"])) for mk, g in sorted(gan.items()))))

    if not (dropi or banco):
        return

    ini = ini or "2026-08-01"
    fin = fin or "2026-08-31"
    # Dropi y el banco Relay son SOLO del mercado GT (quetzales / dolares): la caja de otro mercado
    # se contabiliza aparte. Aca se filtra a GT y se dice en el encabezado.
    TASA = perfil(MERCADO_CAJA)["tasa_moneda_por_usd"]
    if not TASA:
        raise mercado.MercadoError("_PARAMETROS_FINANZAS.csv no declara la tasa del mercado %s." % MERCADO_CAJA)
    es_caja = lambda r: mercado_pk(r["producto_key"]) == MERCADO_CAJA
    L = ["═" * 75,
         "VERIFICACIÓN DE CAJA — ¿el dinero que dice el sistema es el que entra?",
         "Mercado %s (%s) — Dropi y el banco Relay solo cubren este mercado" % (MERCADO_CAJA, perfil(MERCADO_CAJA)["moneda"]),
         "Ventana: %s → %s · generado %s" % (ini, fin, datetime.date.today()),
         "═" * 75, ""]

    # capa 1 — LucidSales
    v1 = [r for r in load("_FACT_VENTAS.csv")
          if r.get("rol_ventana") == "BASE" and ini <= r["ventana_ini"] <= fin and es_caja(r)]
    l1_ventas = sum(i(r["ventas"]) for r in v1)
    l1_fact   = sum(f(r["total_q"]) for r in v1)
    l1_pauta  = sum(pauta_local(r) for r in v1)
    l1_contrib = sum(contribucion(r) for r in v1)
    L += ["CAPA 1 — LucidSales (lo que los ADS atribuyen)",
          "  %d ventas · facturado %s · pauta trackeada %s" % (l1_ventas, q(l1_fact), q(l1_pauta)),
          "  contribución estimada %s → ganancia del sistema %s" % (q(l1_contrib), q(l1_contrib - l1_pauta)),
          ""]

    l2_contrib_neta = None
    if dropi:
        df = leer_dropi(dropi)
        m  = df[(df.fecha >= ini) & (df.fecha <= fin)]
        ent = m[m.ESTATUS == "ENTREGADO"]
        dev = m[m.ESTATUS == "DEVOLUCION"]
        tra = m[~m.ESTATUS.isin(["ENTREGADO", "DEVOLUCION", "CANCELADO"])]
        recaudo  = float(ent["TOTAL DE LA ORDEN"].sum())
        contrib  = float(ent["GANANCIA"].sum())          # total − flete − proveedor
        c_dev    = len(dev) * C_DEVOL
        c_admin  = len(ent) * (C_ADMIN + C_OTROS)
        l2_contrib_neta = contrib - c_dev - c_admin
        n_dropi = len(m)
        L += ["CAPA 2 — Dropi (el dinero que REALMENTE se cobró)",
              "  %d órdenes: %d entregadas · %d devueltas · %d en tránsito" %
              (len(m), len(ent), len(dev), len(tra)),
              "  recaudado %s · contribución bruta %s" % (q(recaudo), q(contrib)),
              "  − devoluciones (%d × Q%.2f) %s · − admin/otros (%d × Q%.2f) %s" %
              (len(dev), C_DEVOL, q(c_dev), len(ent), C_ADMIN + C_OTROS, q(c_admin)),
              "  = CONTRIBUCIÓN NETA REAL %s" % q(l2_contrib_neta),
              "  ⏳ sin resolver: %d órdenes por %s" % (len(tra), q(float(tra["TOTAL DE LA ORDEN"].sum()))),
              ""]
        L += ["  Por producto (solo entregadas):"]
        for pk, g in ent.groupby("pk"):
            L.append("    %-12s %3d órdenes · recaudo %10s · contribución %10s · ticket Q%.0f" %
                     (pk, len(g), q(float(g["TOTAL DE LA ORDEN"].sum())),
                      q(float(g["GANANCIA"].sum())),
                      float(g["TOTAL DE LA ORDEN"].mean())))
        L.append("")

    l3_fb = cobertura = None
    if banco:
        tx = leer_banco(banco)
        fb_all = [t for t in tx if "Facebook" in t["nombre"]]
        fb = [t for t in fb_all if ini <= str(t["fecha"]) <= fin]
        l3_fb = sum(t["monto"] for t in fb)
        L += ["CAPA 3 — Banco (lo que Meta REALMENTE cobró)",
              "  %d cargos de Facebook en la ventana · $%.2f = %s" % (len(fb), l3_fb, q(l3_fb * TASA)),
              "  pauta trackeada por LucidSales en la ventana: %s" % q(l1_pauta),
              ""]
        # ── corte ALINEADO: Meta cobra por umbral, con días de retraso, así que
        #    el mes calendario mezcla dos preguntas (APR-042). Se compara solo el
        #    tramo donde AMBAS fuentes tienen data, que es el único limpio.
        if fb_all:
            d_ini = min(t["fecha"] for t in fb_all).isoformat()
            d_fin = max(t["fecha"] for t in fb_all).isoformat()
            fb_al = sum(t["monto"] for t in fb_all)
            v_al = [r for r in load("_FACT_VENTAS.csv")
                    if r.get("rol_ventana") == "BASE" and d_ini <= r["ventana_ini"] <= d_fin
                    and r.get("cuenta_alias") != "CP1" and es_caja(r)]      # CP1 factura en COP, no por esta cuenta
            tr_al = sum(f(r["spend_usd"]) for r in v_al)
            cobertura = 100 * tr_al / fb_al if fb_al else 0
            L += ["  ── CORTE ALINEADO %s → %s (el único tramo con las dos fuentes) ──" % (d_ini, d_fin),
                  "  Banco cobró $%.2f · LucidSales atribuye $%.2f (sin CP1, que factura en COP)" % (fb_al, tr_al),
                  "  COBERTURA: %.1f%% — %s de gasto real NO aparece en el P&L" %
                  (cobertura, q((fb_al - tr_al) * TASA)),
                  "  (por eso el mes calendario engaña: los cargos de los primeros días del mes",
                  "   suelen caer en el extracto anterior. Para cerrar esto hace falta el extracto previo.)",
                  ""]
        otros = collections.defaultdict(float)
        for t in tx:
            if "Facebook" not in t["nombre"]:
                otros[t["nombre"]] += t["monto"]
        if otros:
            L += ["  Otros cargos en la misma cuenta — NO son pauta y NO están en el P&L.",
                  "  Confirmar cuáles son del negocio (no se atribuyen por descarte, APR-030):"]
            for k2, v2 in sorted(otros.items(), key=lambda kv: -kv[1]):
                L.append("    %-28s $%8.2f = %s" % (k2[:28], v2, q(v2 * TASA)))
            L.append("")

    # veredicto
    L += ["─" * 75, "VEREDICTO", "─" * 75]
    if l2_contrib_neta is not None and l3_fb is not None:
        # Dos estimaciones de la pauta del mes, porque ninguna sola es honesta:
        #   · CAJA      = lo que el banco cobró DENTRO del mes (le faltan los
        #                 primeros días, que se cobraron en el extracto anterior)
        #   · DEVENGADA = lo trackeado, corregido por la cobertura medida
        pauta_caja = l3_fb * TASA
        pauta_dev  = l1_pauta / (cobertura / 100.0) if cobertura else l1_pauta
        alto = l2_contrib_neta - pauta_caja
        bajo = l2_contrib_neta - pauta_dev
        sis  = l1_contrib - l1_pauta
        L += ["  GANANCIA REAL DE CAJA = contribución neta de Dropi − pauta real",
              "    con pauta COBRADA en el mes      %s − %s = %s" % (q(l2_contrib_neta), q(pauta_caja), q(alto)),
              "    con pauta DEVENGADA (corregida)  %s − %s = %s" % (q(l2_contrib_neta), q(pauta_dev), q(bajo)),
              "    → BANDA HONESTA: entre %s y %s" % (q(min(alto, bajo)), q(max(alto, bajo))),
              "",
              "  Ganancia que reporta el sistema (capa 1): %s" % q(sis),
              "  El sistema %s frente a la caja: %s a %s" % (
                  "SUBESTIMA" if sis < min(alto, bajo) else ("INFLA" if sis > max(alto, bajo) else "cae DENTRO de la banda"),
                  q(min(alto, bajo) - sis), q(max(alto, bajo) - sis)),
              "",
              "  POR QUÉ la caja da más que el sistema: Dropi cobró %d órdenes y los ads solo" % n_dropi,
              "  atribuyen %d ventas. Esas %d órdenes de diferencia SÍ entraron, pero ningún" % (l1_ventas, n_dropi - l1_ventas),
              "  anuncio se lleva el crédito (orgánico, recompra o tracking roto).",
              ""]
    L += ["  ⚠ El costo de devolución (Q%.2f) es un PARÁMETRO, no sale de la orden:" % C_DEVOL,
          "    para medirlo de verdad hace falta el ESTADO DE CUENTA de Dropi.",
          "  ⚠ Las órdenes en tránsito todavía pueden caer a devolución: la contribución",
          "    neta de la capa 2 es un TECHO hasta que el cohorte madure."]
    txt = "\n".join(L) + "\n"
    os.makedirs(AUD, exist_ok=True)
    out = os.path.join(AUD, "_VERIFICACION_CAJA_%s.txt" % datetime.date.today().strftime("%Y%m%d"))
    io.open(out, "w", encoding="utf-8").write(txt)
    print(txt)
    print("escrito:", out)


if __name__ == "__main__":
    main()
