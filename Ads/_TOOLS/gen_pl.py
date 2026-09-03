# -*- coding: utf-8 -*-
"""gen_pl.py — Estado de resultados del sistema. Implementa CONTABILIDAD.md.

  python Ads/_TOOLS/gen_pl.py --dropi <ordenes.xlsx> [--banco <extracto.pdf>]
                              [--desde YYYY-MM-DD] [--hasta YYYY-MM-DD]

Determinista por diseño: mismos archivos de entrada -> mismos números de salida.
Ningún parámetro vive acá dentro: todos salen de `_PARAMETROS_FINANZAS.csv`.

Produce, en este orden fijo (CONTABILIDAD.md §3):
    venta bruta entregada · costo de producto · flete
    = MARGEN LOGÍSTICO   (lo que Dropi llama "Ganancias")
    − devoluciones · personal · otros
    = MARGEN DE CONTRIBUCIÓN
    − publicidad
    = MARGEN OPERATIVO
    − gastos fijos
    = RESULTADO NETO

Y la economía unitaria por producto, con el break-even DERIVADO (§4).

Verifica las 5 reglas de integridad de §6 y ABORTA si alguna falla: es preferible
no dar un número a dar uno que no cuadra.
"""
import csv, io, os, re, sys, collections, datetime

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
P    = os.path.join(ROOT, "PRODUCTOS")
AUD  = os.path.join(P, "_AUDITORIAS")


def load(name):
    p = os.path.join(P, name)
    return list(csv.DictReader(io.open(p, encoding="utf-8"))) if os.path.exists(p) else []


def fl(x, d=0.0):
    try:    return float(x)
    except (TypeError, ValueError): return d


def q(n): return "Q{:>12,.2f}".format(n)


# ─────────────── parámetros: dueño único, cero números en el código ───────────────
_par = {r["parametro"]: r for r in load("_PARAMETROS_FINANZAS.csv")}
if not _par:
    sys.exit("FALTA PRODUCTOS/_PARAMETROS_FINANZAS.csv — sin parámetros no se calcula nada.")


def par(nombre, default=None):
    r = _par.get(nombre)
    if r is None or r["valor"] == "":
        if default is None:
            sys.exit("Parámetro '%s' sin valor en _PARAMETROS_FINANZAS.csv" % nombre)
        return default
    return fl(r["valor"])


TASA_Q     = par("tasa_usd_gtq")
C_DEVOL    = par("costo_devolucion_evento_q")
C_ADMIN    = par("costo_admin_q")
C_OTROS    = par("otros_gastos_q")
DIAS_MADURO = int(par("dias_cohorte_maduro"))

RESUELTOS = ("ENTREGADO", "DEVOLUCION", "CANCELADO")


def pk_dropi(nombre):
    n = str(nombre).lower()
    if "tinnidrop" in n or "spray" in n:  return "TINNIDROP"
    if "clearstem" in n:                  return "CLEARSTEM"
    if "vitamin b" in n or "nusava" in n: return "NUSAVA"
    if "varice" in n or "varicose" in n:  return "VARICOSE"
    return "OTRO"


def leer_dropi(path):
    import pandas as pd
    df = pd.read_excel(path)
    df["pk"]      = df["PRODUCTO"].map(pk_dropi)
    df["f_orden"] = pd.to_datetime(df["FECHA"], format="%d-%m-%Y", errors="coerce")
    df["f_mov"]   = pd.to_datetime(df["FECHA DE ÚLTIMO MOVIMIENTO"],
                                   format="%d-%m-%Y", errors="coerce")
    return df


def leer_cartera(path):
    """Historial de cartera de Dropi = el LIBRO DE CAJA del negocio.

    Cada fila es un movimiento real de dinero:
      ENTRADA POR GANANCIA EN LA ORDEN  -> Dropi acredita la ganancia NETA de una
                                           orden entregada (no el recaudo bruto)
      SALIDA DE COBRO DE DEVOLUCION     -> el costo REAL de una entrega no efectiva,
                                           que NO aparece en el export de órdenes
    Trae `ORDEN ID`, así que cruza uno a uno contra el export.
    """
    import pandas as pd
    c = pd.read_excel(path)
    c["f"] = pd.to_datetime(c["FECHA"], format="%d-%m-%Y %H:%M", errors="coerce")

    def cat(d):
        d = str(d).upper()
        if "NO EFECTIVA" in d:            return "COBRO_DEVOLUCION"
        if "GANANCIA EN LA ORDEN" in d:   return "GANANCIA_ORDEN"
        if "RETIRO" in d:                 return "RETIRO"
        return "OTRO"

    c["cat"] = c["DESCRIPCIÓN"].map(cat)
    return c


def leer_banco(path):
    import pdfplumber
    txt = ""
    with pdfplumber.open(path) as pdf:
        for pg in pdf.pages:
            txt += (pg.extract_text() or "") + "\n"
    # El PDF de Relay antepone glifos de uso privado (U+E000-U+F8FF) a los
    # montos para marcar entradas/salidas. Se limpian antes de parsear: depender
    # de ellos hace el regex frágil e ilegible.
    txt = re.sub(r"[\ue000-\uf8ff]", "", txt)
    lines = [l.strip() for l in txt.split("\n")]
    pat = re.compile(r"^(\w{3} \d{1,2}, \d{4})\s+(\w+)\s+"
                     r"\$([\d,]+\.\d{2})\s+\$([\d,]+\.\d{2})$")
    mov, control = [], None
    for n, l in enumerate(lines):
        m = pat.match(l)
        if m:
            mov.append({"nombre": lines[n - 1] if n else "",
                        "fecha": datetime.datetime.strptime(m.group(1), "%b %d, %Y").date(),
                        "monto": float(m.group(3).replace(",", ""))})
        mc = re.search(r"\$[\d,]+\.\d{2}\s+\$[\d,]+\.\d{2}\s+"
                       r"\$[\d,]+\.\d{2}\s+\$([\d,]+\.\d{2})", l)
        if mc and control is None:
            control = float(mc.group(1).replace(",", ""))
    return mov, control


# ──────────────────────────────── main ────────────────────────────────
def main():
    a = sys.argv[1:]
    def opt(flag, d=None):
        return a[a.index(flag) + 1] if flag in a else d
    dropi = opt("--dropi"); banco = opt("--banco"); cartera = opt("--cartera")
    ini   = opt("--desde", "2026-08-01"); fin = opt("--hasta", "2026-08-31")
    if not dropi:
        sys.exit("Falta --dropi <ordenes.xlsx>. Es la fuente de la venta real (CONTABILIDAD.md §5).")

    import pandas as pd
    df = leer_dropi(dropi)
    alertas, fallos = [], []

    # ── integridad 1: el cuadre interno de Dropi ──
    chk = df[df.ESTATUS == "ENTREGADO"]
    calc = (chk["TOTAL DE LA ORDEN"] - chk["PRECIO FLETE"] - chk["PRECIO PROVEEDOR X CANTIDAD"]).sum()
    if abs(calc - chk["GANANCIA"].sum()) > 1.0:
        fallos.append("El cuadre de Dropi NO da: venta−producto−flete = Q%.2f pero la columna "
                      "GANANCIA suma Q%.2f. El export cambió de formato." % (calc, chk["GANANCIA"].sum()))

    # ── ventana: VISTA A (cohorte por fecha de ORDEN) ──
    m   = df[(df.f_orden >= ini) & (df.f_orden <= fin)]
    if not len(m):
        sys.exit("Sin órdenes de Dropi en %s → %s" % (ini, fin))
    ent = m[m.ESTATUS == "ENTREGADO"]
    dev = m[m.ESTATUS == "DEVOLUCION"]
    tra = m[~m.ESTATUS.isin(RESUELTOS)]

    # ── maduración del cohorte (§1) ──
    hoy  = datetime.date.today()
    edad = (hoy - datetime.date.fromisoformat(fin)).days
    maduro = edad >= DIAS_MADURO
    pct_res = 100.0 * (len(m) - len(tra)) / len(m)

    # ── rango de órdenes que trae el export: ¿alcanza para la vista de CAJA? ──
    trae_previo = df.f_orden.min() < pd.Timestamp(ini)

    L = []
    W = 68
    L += ["═" * W,
          "ESTADO DE RESULTADOS — %s → %s" % (ini, fin),
          "VISTA A · COHORTE (por fecha de ORDEN) — «¿rindió la pauta de esta ventana?»",
          "Generado %s · norma: CONTABILIDAD.md · parámetros: _PARAMETROS_FINANZAS.csv" % hoy,
          "═" * W, ""]
    if not maduro:
        L += ["🟡 COHORTE PRELIMINAR — el último día tiene %d días de edad y la norma pide %d."
              % (edad, DIAS_MADURO),
              "   Las devoluciones tardan ~8 días en confirmarse, así que este resultado",
              "   está SOBRESTIMADO. No declarar ganador ni mandar apagar con esto.", ""]
    else:
        L += ["✅ COHORTE MADURO (%d días de edad ≥ %d de la norma) — resultado concluyente."
              % (edad, DIAS_MADURO), ""]
    L += ["   %d órdenes · %d entregadas · %d devueltas · %d sin resolver (%.1f%% resuelto)"
          % (len(m), len(ent), len(dev), len(tra), pct_res), ""]

    # ── el estado de resultados, orden fijo §3 ──
    venta   = float(ent["TOTAL DE LA ORDEN"].sum())
    costo   = float(ent["PRECIO PROVEEDOR X CANTIDAD"].sum())
    flete   = float(ent["PRECIO FLETE"].sum())
    m_log   = venta - costo - flete

    # ── costo de devolución: REAL orden por orden si hay cartera, si no el parámetro ──
    # Nunca sale del export de órdenes (ahí COSTO DEVOLUCION FLETE = 0 siempre), así
    # que SIEMPRE se suma aparte: una vez por cada orden en estado DEVOLUCION.
    car = leer_cartera(cartera) if cartera else None
    dev_ids = set(dev["ID"])
    if car is not None:
        cob = car[(car.cat == "COBRO_DEVOLUCION") & (car["ORDEN ID"].isin(dev_ids))]
        c_dev = float(cob["MONTO"].sum())
        n_cob = len(cob)
        sin_cobrar = len(dev) - n_cob
        # las devoluciones aún sin cobrar se estiman al promedio medido
        c_dev += max(sin_cobrar, 0) * C_DEVOL
        origen_dev = ("REAL: %d cobros del historial de cartera%s"
                      % (n_cob, " + %d aún sin cobrar al promedio Q%.2f" % (sin_cobrar, C_DEVOL)
                         if sin_cobrar > 0 else ""))
    else:
        c_dev = len(dev) * C_DEVOL
        origen_dev = "estimado: %d devoluciones × Q%.2f (sin historial de cartera)" % (len(dev), C_DEVOL)

    c_adm   = len(ent) * C_ADMIN
    c_otr   = len(ent) * C_OTROS
    m_contr = m_log - c_dev - c_adm - c_otr

    L += ["─" * W]
    L += ["  (+) VENTA BRUTA ENTREGADA               %s" % q(venta),
          "  (−) Costo de producto                   %s" % q(-costo),
          "  (−) Flete de entrega                    %s" % q(-flete),
          "      " + "·" * 56,
          "  (=) MARGEN LOGÍSTICO                    %s" % q(m_log),
          "      ↑ esto es lo que muestra el panel de Dropi. NO es tu ganancia.",
          "",
          "  (−) Costo de devoluciones (%3d devol.)  %s" % (len(dev), q(-c_dev)),
          "      %s" % origen_dev,
          "  (−) Costo de personal     (%3d × Q%.2f)  %s" % (len(ent), C_ADMIN, q(-c_adm)),
          "  (−) Otros gastos operativos(%3d × Q%.2f)  %s" % (len(ent), C_OTROS, q(-c_otr)),
          "      " + "·" * 56,
          "  (=) MARGEN DE CONTRIBUCIÓN              %s" % q(m_contr)]

    # ── publicidad: se toma de _FACT_VENTAS (devengada) y se contrasta con banco ──
    v = [r for r in load("_FACT_VENTAS.csv")
         if r.get("rol_ventana") == "BASE" and ini <= r["ventana_ini"] <= fin]
    pauta_usd = sum(fl(r["spend_usd"]) for r in v)
    pauta_q   = pauta_usd * TASA_Q
    m_oper    = m_contr - pauta_q
    L += ["",
          "  (−) Publicidad Meta ($%.2f × %.2f)    %s" % (pauta_usd, TASA_Q, q(-pauta_q)),
          "      " + "·" * 56,
          "  (=) MARGEN OPERATIVO                    %s" % q(m_oper)]

    # ── clasificación de cargos del banco (CONTABILIDAD.md §3-ter) ──
    #   NEGOCIO_PAUTA  -> ya contado en la línea de Publicidad, no se resta otra vez
    #   NEGOCIO_FIJO   -> resta del RESULTADO (software, herramientas)
    #   PERSONAL       -> RETIRO DE SOCIO: NO toca el resultado, sí la caja
    #   SIN_CLASIFICAR -> no entra a nada; se lista y se pregunta (APR-030)
    reglas = load("_DIM_GASTOS.csv")

    def clasificar(nombre):
        for g in reglas:
            if g["patron"] and g["patron"].lower() in nombre.lower():
                return g["clasificacion"], g.get("categoria", "")
        return "SIN_CLASIFICAR", ""

    fijos, retiros, sin_confirmar = 0.0, 0.0, []
    det_fijos, det_retiros = [], []
    if banco:
        mov, control = leer_banco(banco)
        if control is not None and abs(sum(x["monto"] for x in mov) - control) > 0.02:
            fallos.append("El extracto no cuadra: los movimientos suman $%.2f y el resumen dice "
                          "$%.2f." % (sum(x["monto"] for x in mov), control))
        agr = collections.defaultdict(float)
        for t in mov:
            if ini <= str(t["fecha"]) <= fin:
                agr[t["nombre"]] += t["monto"]
        pend = collections.defaultdict(float)
        for nom, val in agr.items():
            cl, cat = clasificar(nom)
            if cl == "NEGOCIO_FIJO":
                fijos += val * TASA_Q
                det_fijos.append((nom, val, cat))
            elif cl == "PERSONAL":
                retiros += val * TASA_Q
                det_retiros.append((nom, val, cat))
            elif cl == "SIN_CLASIFICAR":
                pend[nom] += val
        sin_confirmar = sorted(pend.items(), key=lambda kv: -kv[1])
        # Cobertura SOLO sobre el tramo alineado (APR-070): Meta cobra por umbral
        # y con retraso, así que el mes calendario mezcla dos preguntas. Se compara
        # la intersección de las dos series, y se excluye CP1 (factura en COP por
        # otro medio de pago).
        fbm = [t for t in mov if "Facebook" in t["nombre"]]
        if fbm:
            d_ini = min(t["fecha"] for t in fbm).isoformat()
            d_fin = max(t["fecha"] for t in fbm).isoformat()
            fb_al = sum(t["monto"] for t in fbm)
            tr_al = sum(fl(r["spend_usd"]) for r in load("_FACT_VENTAS.csv")
                        if r.get("rol_ventana") == "BASE"
                        and d_ini <= r["ventana_ini"] <= d_fin
                        and r.get("cuenta_alias") != "CP1")
            cob = 100 * tr_al / fb_al if fb_al else 0
            alertas.append("Cobertura de pauta en el tramo ALINEADO %s→%s (el único comparable, "
                           "APR-070): el banco cobró $%.2f y LucidSales atribuye $%.2f = %.1f%%. "
                           "Faltan %s de gasto real en el P&L."
                           % (d_ini, d_fin, fb_al, tr_al, cob, q((fb_al - tr_al) * TASA_Q).strip()))
            if df.f_orden.min() >= pd.Timestamp(ini):
                alertas.append("El extracto arranca antes que los cargos de Meta: los primeros días "
                               "del mes se cobraron en el extracto ANTERIOR. Para cerrar el arrastre "
                               "hace falta el extracto del mes previo.")
    neto = m_oper - fijos
    L += ["", "  (−) Gastos fijos del negocio            %s" % q(-fijos)]
    for nom, val, cat in sorted(det_fijos, key=lambda x: -x[1]):
        L.append("        {:<24} ${:>8,.2f}  {}".format(nom[:24], val, cat))
    if not det_fijos:
        L.append("        (ninguno confirmado en esta ventana)")
    L += ["      " + "═" * 56,
          "  (=) RESULTADO NETO DEL NEGOCIO          %s" % q(neto),
          "─" * W, ""]

    if det_retiros:
        L += ["RETIROS PERSONALES — salieron de la cuenta pero NO son del negocio.",
              "No reducen la ganancia (no es plata que el negocio gastó en operar);",
              "sí reducen la CAJA disponible. Contablemente es un retiro de socio."]
        for nom, val, cat in sorted(det_retiros, key=lambda x: -x[1]):
            L.append("     {:<26} ${:>8,.2f} = {}".format(nom[:26], val, q(val * TASA_Q)))
        L += ["     " + "·" * 52,
              "     Total retirado                       %s" % q(retiros),
              "",
              "     El negocio ganó %s y vos sacaste %s → quedaron %s"
              % (q(neto), q(retiros), q(neto - retiros)),
              ""]

    if sin_confirmar:
        L += ["🔴 CARGOS SIN CLASIFICAR — NO entraron a ninguna línea de arriba.",
              "   No se atribuyen por descarte (APR-030): confirmá si son del negocio",
              "   y se agregan a `PRODUCTOS/_DIM_GASTOS.csv`. Si lo son, el resultado baja."]
        for k, val in sin_confirmar:
            L.append("     {:<26} ${:>8,.2f} = {}".format(k[:26], val, q(val * TASA_Q)))
        L.append("")

    # ── economía unitaria por producto (§4) ──
    L += ["═" * W, "ECONOMÍA UNITARIA — cuánto deja CADA VENTA, por producto", "═" * W, ""]
    cpa_prod = collections.defaultdict(float)
    ven_prod = collections.Counter()
    for r in v:
        cpa_prod[r["producto_key"]] += fl(r["spend_usd"]) * TASA_Q
        ven_prod[r["producto_key"]] += int(fl(r["ventas"]))
    for pk, g in sorted(ent.groupby("pk"), key=lambda kv: -len(kv[1])):
        n_e = len(g)
        n_d = len(dev[dev.pk == pk])
        te  = n_e / (n_e + n_d) if (n_e + n_d) else 1.0
        tick = float(g["TOTAL DE LA ORDEN"].mean())
        cos  = float(g["PRECIO PROVEEDOR X CANTIDAD"].mean())
        fle  = float(g["PRECIO FLETE"].mean())
        dev_amort = ((1 - te) / te) * C_DEVOL if te else 0.0
        be   = tick - cos - fle - dev_amort - C_ADMIN - C_OTROS
        cpa  = cpa_prod[pk] / ven_prod[pk] if ven_prod[pk] else 0.0
        L += ["  %s   (entrega %.1f%% · %d entregadas / %d devueltas)" % (pk, 100 * te, n_e, n_d),
              "     Precio de venta (ticket promedio)      %s" % q(tick),
              "     − Costo del producto                   %s" % q(-cos),
              "     − Flete                                %s" % q(-fle),
              "     − Devolución amortizada                %s" % q(-dev_amort),
              "     − Admin y otros                        %s" % q(-(C_ADMIN + C_OTROS)),
              "       " + "·" * 54,
              "     = MARGEN ANTES DE PUBLICIDAD           %s  ← break-even del CPA" % q(be),
              "     − CPA real (pauta ÷ ventas)            %s" % q(-cpa),
              "       " + "·" * 54,
              "     = GANANCIA POR VENTA                   %s  %s" % (
                  q(be - cpa), "🔴 PIERDE en cada venta" if be - cpa < 0 else "✅"),
              ""]

    # ── VISTA B — CAJA (por fecha del movimiento de dinero, §2) ──
    L += ["═" * W, "VISTA B — CAJA (¿cuánto dinero entró de verdad en la ventana?)", "═" * W]
    if car is None:
        L += ["🔴 NO SE PUEDE CALCULAR: falta el HISTORIAL DE CARTERA de Dropi (--cartera).",
              "   Lo de arriba es COHORTE: mide si la pauta rindió, no el saldo de la cuenta.", ""]
    else:
        cv = car[(car.f >= ini) & (car.f <= fin + " 23:59")]
        e_gan = cv[cv.cat == "GANANCIA_ORDEN"]
        s_dev = cv[cv.cat == "COBRO_DEVOLUCION"]
        s_otr = cv[~cv.cat.isin(("GANANCIA_ORDEN", "COBRO_DEVOLUCION", "RETIRO"))]
        entra  = float(e_gan["MONTO"].sum())
        sale_d = float(s_dev["MONTO"].sum())
        sale_o = float(s_otr["MONTO"].sum())
        caja_dropi = entra - sale_d - sale_o
        adm_caja = len(e_gan) * (C_ADMIN + C_OTROS)
        pauta_caja = (sum(t["monto"] for t in mov if "Facebook" in t["nombre"]
                          and ini <= str(t["fecha"]) <= fin) * TASA_Q) if banco else None
        L += ["  Fuente: historial de cartera de Dropi — movimientos REALES de dinero,",
              "  fechados por cuándo ocurrieron (no por cuándo se tomó la orden).", "",
              "  (+) Entradas por ganancia de órdenes (%3d)  %s" % (len(e_gan), q(entra)),
              "  (−) Cobros de devolución (%3d)              %s" % (len(s_dev), q(-sale_d))]
        if len(s_otr):
            L.append("  (−) Otras salidas (%d)                       %s" % (len(s_otr), q(-sale_o)))
        L += ["      " + "·" * 56,
              "  (=) NETO ACREDITADO EN LA CARTERA           %s" % q(caja_dropi),
              "  (−) Personal y otros (%3d × Q%.2f)          %s" % (len(e_gan), C_ADMIN + C_OTROS, q(-adm_caja))]
        if pauta_caja is not None:
            L += ["  (−) Publicidad cobrada por el banco         %s" % q(-pauta_caja)]
            if fijos:
                L.append("  (−) Gastos fijos del negocio                %s" % q(-fijos))
            caja_neg = caja_dropi - adm_caja - pauta_caja - fijos
            L += ["      " + "═" * 56,
                  "  (=) CAJA QUE GENERÓ EL NEGOCIO              %s" % q(caja_neg)]
            if retiros:
                L += ["  (−) Retiros personales (no son del negocio) %s" % q(-retiros),
                      "      " + "═" * 56,
                      "  (=) CAJA QUE QUEDÓ EN LA CUENTA             %s" % q(caja_neg - retiros)]
            L.append("")
        else:
            L += ["      " + "═" * 56,
                  "  (=) CAJA ANTES DE PUBLICIDAD                %s" % q(caja_dropi - adm_caja), ""]
        # el arrastre: cuántos movimientos vienen de órdenes de ANTES de la ventana
        prev = e_gan.merge(df[["ID", "f_orden"]], left_on="ORDEN ID", right_on="ID", how="left")
        n_prev = int((prev.f_orden < pd.Timestamp(ini)).sum())
        d_prev = float(prev[prev.f_orden < pd.Timestamp(ini)]["MONTO"].sum())
        L += ["  ARRASTRE: %d de las %d acreditaciones (%s) vienen de órdenes tomadas ANTES"
              % (n_prev, len(e_gan), q(d_prev)),
              "  del %s. Eso es exactamente lo que la vista de COHORTE no ve: se vendió un" % ini,
              "  mes y se cobró al siguiente.", ""]
        L += ["  COHORTE vs CAJA en esta ventana: %s vs %s"
              % (q(m_contr), q(caja_dropi - adm_caja)),
              "  No tienen por qué coincidir y ninguna está mal: miden cosas distintas.", ""]

    if alertas:
        L += ["─" * W, "NOTAS"] + ["  ⚠ " + x for x in alertas] + [""]

    # ── integridad (§6) ──
    L += ["─" * W, "VERIFICACIÓN DE INTEGRIDAD"]
    L.append("  %s Cuadre de Dropi (venta−producto−flete = GANANCIA)"
             % ("✅" if not any("cuadre de Dropi" in x for x in fallos) else "❌"))
    if banco:
        L.append("  %s Cuadre del extracto (movimientos = total del resumen)"
                 % ("✅" if not any("extracto" in x for x in fallos) else "❌"))
    L.append("  %s Maduración del cohorte (≥ %d días)" % ("✅" if maduro else "🟡", DIAS_MADURO))
    if car is not None:
        # Cada ENTRADA de la cartera debe coincidir al céntimo con la columna
        # GANANCIA de su orden. Si no, una de las dos fuentes cambió.
        cr = car[car.cat == "GANANCIA_ORDEN"].merge(
            df[["ID", "GANANCIA"]], left_on="ORDEN ID", right_on="ID", how="left")
        hay = cr["GANANCIA"].notna()
        difs = int(((cr.loc[hay, "MONTO"] - cr.loc[hay, "GANANCIA"]).abs() > 0.01).sum())
        huerf = int((~hay).sum())
        ok = (difs == 0 and huerf == 0)
        L.append("  %s Cruce cartera↔órdenes (%d movimientos, %d descuadres, %d sin orden)"
                 % ("✅" if ok else "❌", len(cr), difs, huerf))
        if difs:
            fallos.append("%d entradas de cartera no coinciden con la GANANCIA de su orden." % difs)
        if huerf:
            alertas.append("%d movimientos de cartera apuntan a órdenes que no están en el export "
                           "— pedilo con más días de ventana." % huerf)
    for x in fallos:
        L.append("  ❌ " + x)
    L.append("─" * W)

    txt = "\n".join(L) + "\n"
    os.makedirs(AUD, exist_ok=True)
    out = os.path.join(AUD, "_PL_%s_%s.txt" % (ini.replace("-", ""), fin.replace("-", "")))
    io.open(out, "w", encoding="utf-8").write(txt)
    print(txt)
    print("escrito:", out)
    if fallos:
        sys.exit("\n❌ INTEGRIDAD FALLIDA — los números de arriba NO son confiables.")


if __name__ == "__main__":
    main()
