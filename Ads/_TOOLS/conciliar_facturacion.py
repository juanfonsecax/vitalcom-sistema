#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CONCILIADOR DE FACTURACIÓN — ¿lo que Meta me COBRA = lo que Meta dice que GASTÉ?

Responde DOS preguntas distintas que la gente suele mezclar:

  (A) ¿Meta me cobra de más?   -> ecuación de arrastre, por cuenta.
  (B) ¿Todo lo que me cobran está en mi P&L?  -> cobertura, por cuenta.

La (A) casi siempre da OK. La (B) es donde está la plata que se pierde.

LA ECUACIÓN (única forma correcta de comparar; Meta cobra por UMBRAL, no por fecha):

    cobros_del_periodo  −  saldo_sin_facturar_INICIAL  +  saldo_sin_facturar_FINAL
    ────────────────────────────────────────────────────────────────────────────
                          =  gasto_devengado_del_periodo

  Comparar "gasté del 1 al 15" contra "me cobraron del 1 al 15" SIEMPRE descuadra
  y NO es evidencia de sobrecobro (APR-025).

ADVERTENCIA DE MÉTODO (lo más importante de este script):
  Si el saldo inicial es ESTIMADO (despejado de la propia ecuación), la ecuación
  cierra por construcción y NO VERIFICA NADA. Solo verifica de verdad cuando el
  saldo inicial fue OBSERVADO en el corte anterior. Por eso hay que guardar el
  saldo en CADA corte semanal: a partir del segundo, la conciliación es real.
  El script marca esa diferencia de forma explícita y nunca la disimula.

NINGÚN NÚMERO SE ESCRIBE A MANO. Todo sale de los CSV.

Uso:
    python Ads/_TOOLS/conciliar_facturacion.py                 # última ventana
    python Ads/_TOOLS/conciliar_facturacion.py 2026-08-16 2026-08-22
"""
import csv, os, sys
from datetime import date
# Consola de Windows en cp1252/cp850: sin esto un print con acentos o simbolos
# revienta con UnicodeEncodeError y devuelve exit code 1 con el trabajo ya hecho
# (mismo bug que en gen_dashboard.py, 18-ago).
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass


BASE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "PRODUCTOS")

TOL_ABS = 2.00   # USD: por debajo de esto un descuadre es redondeo/timing
TOL_PCT = 0.02   # 2% del gasto devengado


def load(name):
    p = os.path.join(BASE, name)
    if not os.path.exists(p):
        return []
    with open(p, encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def f(v, default=0.0):
    try:
        s = str(v).strip().replace(",", "").replace("$", "")
        return float(s) if s not in ("", "nan", "None") else default
    except (TypeError, ValueError):
        return default


def money(x):
    return "{:>10,.2f}".format(x)


# ─────────────────────────────────────────────────────────────────────────
# 1. COBROS del período: del detalle si existe, si no del agregado
# ─────────────────────────────────────────────────────────────────────────
def cobros_por_cuenta(ini, fin):
    det = load("_FACT_FACTURACION.csv")
    out, fuente = {}, None
    if det:
        fuente = "detalle"
        for r in det:
            if not (ini <= r.get("fecha", "") <= fin):
                continue
            al = r.get("cuenta_alias", "")
            d = out.setdefault(al, {"cobros": 0.0, "rechazos": 0, "creditos": 0.0,
                                    "bm": r.get("bm_nombre", ""), "n": 0})
            tipo = (r.get("tipo") or "").upper()
            if tipo == "COBRO":
                d["cobros"] += f(r.get("monto_usd")); d["n"] += 1
            elif tipo == "RECHAZO":
                d["rechazos"] += 1
            elif tipo == "CREDITO":
                d["creditos"] += f(r.get("monto_usd"))
    else:
        ag = load("_FACT_FACTURACION_AGREGADO.csv")
        cand = [r for r in ag if r.get("ventana_ini") == ini and r.get("ventana_fin") == fin]
        if not cand and ag:                       # fallback: la ventana más reciente
            ult = max(r.get("ventana_fin", "") for r in ag)
            cand = [r for r in ag if r.get("ventana_fin") == ult]
            ini = cand[0].get("ventana_ini", ini); fin = ult
        if cand:
            fuente = "agregado"
            for r in cand:
                out[r.get("cuenta_alias", "")] = {
                    "cobros": f(r.get("cobros_usd")), "rechazos": int(f(r.get("rechazos_n"))),
                    "creditos": f(r.get("creditos_usd")), "bm": r.get("bm_nombre", ""), "n": 0}
    return out, fuente, ini, fin


# ─────────────────────────────────────────────────────────────────────────
# 2. SALDOS: el corte de la fecha pedida y el corte anterior más cercano
# ─────────────────────────────────────────────────────────────────────────
def saldo_en(alias, fecha_corte, saldos):
    filas = [r for r in saldos
             if r.get("cuenta_alias") == alias and r.get("fecha_corte", "") <= fecha_corte
             and str(r.get("saldo_sin_facturar_usd", "")).strip() != ""]
    if not filas:
        return None, None, None
    r = max(filas, key=lambda x: x.get("fecha_corte", ""))
    return f(r.get("saldo_sin_facturar_usd")), (r.get("estado") or "").upper(), r.get("fecha_corte")


# ─────────────────────────────────────────────────────────────────────────
# 3. GASTO DEVENGADO y COBERTURA
# ─────────────────────────────────────────────────────────────────────────
def pauta(ini, fin):
    pr = load("_FACT_PAUTA_REAL.csv")
    cand = [r for r in pr if r.get("ventana_ini") == ini and r.get("ventana_fin") == fin]
    if not cand and pr:
        ult = max(r.get("ventana_fin", "") for r in pr)
        cand = [r for r in pr if r.get("ventana_fin") == ult]
    return {r.get("cuenta_alias", ""): {"real": f(r.get("spend_real_usd")),
                                        "trk": f(r.get("spend_trackeado_usd")),
                                        "fuente": r.get("fuente", ""),
                                        "ini": r.get("ventana_ini"), "fin": r.get("ventana_fin")}
            for r in cand}


def main():
    hoy = date.today().isoformat()
    if len(sys.argv) >= 3:
        ini, fin = sys.argv[1], sys.argv[2]
    else:
        ag = load("_FACT_FACTURACION_AGREGADO.csv")
        ini = min((r["ventana_ini"] for r in ag), default="")
        fin = max((r["ventana_fin"] for r in ag), default=hoy)

    cob, fuente_cob, ini, fin = cobros_por_cuenta(ini, fin)
    gasto = pauta(ini, fin)
    saldos = load("_FACT_SALDOS.csv")
    bms = {r["bm_nombre"]: r for r in load("_DIM_BM.csv")}
    tarjetas = load("_DIM_TARJETAS.csv")

    L = []
    A = L.append
    A("=" * 75)
    A("CONCILIACION DE FACTURACION — ventana {} -> {}".format(ini, fin))
    A("generada {} · fuente de cobros: {}".format(hoy, fuente_cob or "SIN DATA"))
    A("=" * 75)
    A("")
    A("ECUACION:  cobros - saldo_inicial + saldo_final = gasto devengado")
    A("Meta cobra por UMBRAL acumulado, no por rango de fechas. Un descuadre entre")
    A("'lo gastado' y 'lo cobrado' en las mismas fechas NO es sobrecobro (APR-025).")
    A("")

    if not cob:
        A("SIN DATA DE COBROS para esta ventana.")
        A("Pegar el extracto de Facturacion de Meta por cuenta y volver a correr.")
        return escribir(L, fin)

    # ── (A) ¿me cobran de mas?
    A("-" * 75)
    A("(A) ¿ME COBRAN DE MAS? — ecuacion de arrastre por cuenta")
    A("-" * 75)
    A("{:<7} {:>10} {:>10} {:>10} {:>10} {:>10}  {}".format(
        "CUENTA", "COBRADO", "SALDO_INI", "SALDO_FIN", "GASTO", "DESCUADRE", "VEREDICTO"))

    tot = {"cob": 0.0, "gasto": 0.0, "trk": 0.0}
    verificables = 0
    alertas = []
    for al in sorted(cob, key=lambda x: -cob[x]["cobros"]):
        c = cob[al]["cobros"]
        g = gasto.get(al, {}).get("real")
        s_fin, est_fin, _ = saldo_en(al, fin, saldos)
        prev = [r for r in saldos if r.get("cuenta_alias") == al
                and r.get("fecha_corte", "") < ini
                and str(r.get("saldo_sin_facturar_usd", "")).strip() != ""]
        if prev:
            r = max(prev, key=lambda x: x.get("fecha_corte", ""))
            s_ini, est_ini = f(r.get("saldo_sin_facturar_usd")), (r.get("estado") or "").upper()
        else:
            s_ini, est_ini = None, None

        tot["cob"] += c
        if g is not None:
            tot["gasto"] += g
            tot["trk"] += gasto.get(al, {}).get("trk", 0.0)

        if g is None or s_fin is None or s_ini is None:
            falta = []
            if g is None: falta.append("gasto devengado")
            if s_ini is None: falta.append("saldo inicial")
            if s_fin is None: falta.append("saldo final")
            A("{:<7} {} {:>10} {:>10} {:>10} {:>10}  NO VERIFICABLE (falta {})".format(
                al, money(c), "—" if s_ini is None else money(s_ini).strip(),
                "—" if s_fin is None else money(s_fin).strip(),
                "—" if g is None else money(g).strip(), "—", ", ".join(falta)))
            alertas.append("{}: no se puede conciliar, falta {}.".format(al, " y ".join(falta)))
            continue

        d = c - s_ini + s_fin - g
        tol = max(TOL_ABS, abs(g) * TOL_PCT)
        if est_ini in ("ESTIMADO", "DESPEJADO"):
            ver = "NO VERIFICA (saldo ini estimado)"
        elif abs(d) <= tol:
            ver = "OK"; verificables += 1
        elif d > 0:
            ver = "REVISAR: cobrado de mas"; verificables += 1
            alertas.append("{}: cobrado excede la ecuacion en ${:,.2f}. Revisar el extracto cargo por cargo.".format(al, d))
        else:
            ver = "REVISAR: cobrado de menos"; verificables += 1
            alertas.append("{}: cobrado por debajo de la ecuacion en ${:,.2f} (probable saldo o retencion sin registrar).".format(al, -d))
        A("{:<7} {} {} {} {} {}  {}".format(
            al, money(c), money(s_ini), money(s_fin), money(g), money(d), ver))

    A("")
    A("{:<7} {}".format("TOTAL", money(tot["cob"])))
    if verificables == 0:
        A("")
        A("!! NINGUNA CUENTA ES VERIFICABLE TODAVIA.")
        A("   Los saldos iniciales son ESTIMADOS (despejados de la propia ecuacion),")
        A("   asi que la ecuacion cierra por construccion y no prueba nada.")
        A("   A partir del SEGUNDO corte semanal con saldo OBSERVADO, esto ya verifica.")
    else:
        A("")
        A("{} de {} cuentas verificadas con saldo inicial observado.".format(verificables, len(cob)))

    # ── (B) cobertura
    A("")
    A("-" * 75)
    A("(B) ¿TODO LO QUE ME COBRAN ESTA EN MI P&L? — cobertura")
    A("-" * 75)
    A("{:<7} {:>12} {:>12} {:>10}  {}".format("CUENTA", "TRACKEADO", "REAL", "COBERT.", "VEREDICTO"))
    for al in sorted(gasto, key=lambda x: -gasto[x]["real"]):
        g = gasto[al]
        if g["real"] <= 0:
            A("{:<7} {} {} {:>10}  sin gasto".format(al, money(g["trk"]), money(g["real"]), "—"))
            continue
        pct = g["trk"] / g["real"] * 100
        v = "OK" if pct >= 90 else ("REVISAR" if pct >= 70 else "FUGA GRANDE")
        if pct < 90:
            alertas.append("{}: el P&L solo ve el {:.0f}% de su gasto (${:,.2f} sin contabilizar).".format(
                al, pct, g["real"] - g["trk"]))
        A("{:<7} {} {} {:>9.0f}%  {}".format(al, money(g["trk"]), money(g["real"]), pct, v))
    if tot["gasto"] > 0:
        pct = tot["trk"] / tot["gasto"] * 100
        dias = 1
        A("")
        A("{:<7} {} {} {:>9.0f}%".format("TOTAL", money(tot["trk"]), money(tot["gasto"]), pct))
        A("Gasto NO contabilizado en el P&L: ${:,.2f} USD = Q{:,.0f}".format(
            tot["gasto"] - tot["trk"], (tot["gasto"] - tot["trk"]) * 7.62))
        A("-> Mientras la cobertura no sea ~100%, la ganancia del dashboard esta INFLADA")
        A("   en aproximadamente ese monto. No es que Meta cobre de mas: es gasto real")
        A("   que el P&L no descuenta.")

    # ── (C) salud de tarjetas
    A("")
    A("-" * 75)
    A("(C) SALUD DE TARJETAS — un rechazo no es plata perdida, pero frena entrega")
    A("-" * 75)
    A("{:<7} {:<5} {:<9} {:>5} {:>5} {:>7}  {}".format(
        "ULT.4", "MARCA", "BM", "OK", "RECH", "%FALLA", "VEREDICTO"))
    muertas = []
    for t in sorted(tarjetas, key=lambda x: (-f(x.get("pct_falla")), -f(x.get("rechazos")))):
        ok, re_ = int(f(t.get("cobros_ok"))), int(f(t.get("rechazos")))
        A("{:<7} {:<5} {:<9} {:>5} {:>5} {:>6.0f}%  {}".format(
            t.get("ultimos4", ""), t.get("marca", ""), t.get("bm_nombre", "")[:9],
            ok, re_, f(t.get("pct_falla")), t.get("veredicto", "")))
        if (t.get("veredicto") or "").upper() == "MUERTA":
            muertas.append(t.get("ultimos4"))
    if muertas:
        A("")
        A("ACCION: quitar como metodo de pago las tarjetas MUERTAS (0 cobros exitosos):")
        A("        " + " · ".join("···" + m for m in muertas))
        A("Meta las intenta PRIMERO, falla, y recien despues cae a la buena. Cada")
        A("reintento fallido acerca la cuenta a restriccion. Quitarlas es gratis.")
        alertas.append("{} tarjetas MUERTAS siguen configuradas como metodo de pago: {}.".format(
            len(muertas), ", ".join("···" + m for m in muertas)))
    pend = [t.get("ultimos4") for t in tarjetas if (t.get("bm_nombre") or "") == "PENDIENTE"]
    if pend:
        A("")
        A("{} tarjetas sin BM atribuido: {}".format(len(pend), " · ".join("···" + p for p in pend)))
        A("Se completan solas con el proximo extracto de Facturacion (dice que tarjeta")
        A("pago cada cargo). NUNCA atribuir por descarte -- ese fue el error de APR-030.")

    # ── (D) qué hacer
    A("")
    A("-" * 75)
    A("(D) QUE HACER")
    A("-" * 75)
    if alertas:
        for i, a in enumerate(sorted(set(alertas)), 1):
            A("{}. {}".format(i, a))
    else:
        A("Nada pendiente: la ecuacion cierra y la cobertura esta sana.")
    A("")
    A("RECORDATORIO DE CIERRE: guardar el saldo sin facturar de CADA cuenta en")
    A("_FACT_SALDOS.csv con estado=OBSERVADO. Es lo unico que convierte esta")
    A("conciliacion en una verificacion real la semana que viene.")
    A("=" * 75)
    return escribir(L, fin)


def escribir(L, fin):
    txt = "\n".join(L)
    print(txt)
    d = os.path.join(BASE, "_AUDITORIAS")
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, "_CONCILIACION_{}.txt".format(fin.replace("-", "")))
    with open(p, "w", encoding="utf-8") as fh:
        fh.write(txt + "\n")
    print("\nescrito: " + p)


if __name__ == "__main__":
    main()
