# -*- coding: utf-8 -*-
"""verificar_monedas.py — audita que ningún número esté en la moneda equivocada.

  python Ads/_TOOLS/verificar_monedas.py

El riesgo real del sistema: el negocio COBRA en quetzales (Guatemala) y PAGA la
publicidad en dólares (Meta). Un valor convertido de más o de menos se ve
plausible y nadie lo nota — un error de factor 7.62 en la pauta convierte una
ganancia en una pérdida sin que ninguna cifra parezca absurda.

Este script no confía en la lectura del código: comprueba INVARIANTES sobre la
data real. Sale con código 1 si alguna falla.

REGLA DE ORO DEL SISTEMA:
    · Todo lo que viene de DROPI          -> QUETZALES (nunca se convierte)
    · Todo lo que viene del BANCO (Relay) -> DÓLARES   (siempre × tasa_usd_gtq)
    · LucidSales es MIXTO: `spend` en USD, `total` (la venta) en QUETZALES
    · La cuenta CP1 es la excepción: su `spend` viene en COP (÷ tasa_cop_usd)
"""
import csv, io, os, sys, collections

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
P    = os.path.join(ROOT, "PRODUCTOS")
TOOLS = os.path.join(ROOT, "Ads", "_TOOLS")


def load(name):
    p = os.path.join(P, name)
    return list(csv.DictReader(io.open(p, encoding="utf-8"))) if os.path.exists(p) else []


def f(x, d=0.0):
    try:    return float(x)
    except (TypeError, ValueError): return d


par = {r["parametro"]: r for r in load("_PARAMETROS_FINANZAS.csv")}
TASA = f(par.get("tasa_usd_gtq", {}).get("valor"), 7.62)
TASA_COP = f(par.get("tasa_cop_usd", {}).get("valor"), 3152.5)

ok, fail, warn = [], [], []


def check(cond, titulo, detalle):
    (ok if cond else fail).append((titulo, detalle))


# ── 1. La tasa no está hardcodeada en ningún motor ────────────────────────
hard = []
for fn in ("gen_dashboard.py", "gen_finanzas.py", "gen_pl.py"):
    p = os.path.join(TOOLS, fn)
    if not os.path.exists(p):
        continue
    for n, l in enumerate(io.open(p, encoding="utf-8"), 1):
        ls = l.strip()
        if ls.startswith("#") or "_default" in ls or "tasa_usd_gtq" in ls:
            continue
        if ls.startswith("TASA") and "=" in ls and any(c.isdigit() for c in ls.split("=")[1]):
            hard.append("%s:%d  %s" % (fn, n, ls))
check(not hard, "La tasa USD→Q no está hardcodeada en ningún motor",
      "\n".join("      " + h for h in hard) or
      "      los 3 motores la leen de _PARAMETROS_FINANZAS.csv (Q%.2f por USD)" % TASA)

# ── 2. El ticket promedio de cada venta cae en el rango de la escalera ────
#    Si `total_q` estuviera en dólares (o convertido dos veces), el ticket se
#    saldría de la escalera de precios por un factor ~7.6.
esc = collections.defaultdict(list)
for r in load("_DIM_PRECIOS.csv"):
    if (r.get("estado") or "").upper() != "SIN_REGISTRAR":
        esc[r["producto_key"]].append(f(r["precio_q"]))
malos = []
for r in load("_FACT_VENTAS.csv"):
    v = f(r.get("ventas"))
    if r.get("rol_ventana") != "BASE" or not v:
        continue
    pk = r["producto_key"]
    if pk not in esc or not esc[pk]:
        continue
    t = f(r["total_q"]) / v
    lo, hi = min(esc[pk]) * 0.5, max(esc[pk]) * 2.0
    if not (lo <= t <= hi):
        malos.append("%s %s ticket Q%.2f fuera de [Q%.0f, Q%.0f]" % (r["ventana_ini"], pk, t, lo, hi))
check(not malos, "Los tickets de venta están en QUETZALES (dentro de la escalera de precios)",
      "\n".join("      " + m for m in malos[:6]) or
      "      revisadas todas las filas BASE con ventas; ninguna fuera de rango")

# ── 3. El gasto diario por cuenta es plausible EN DÓLARES ────────────────
#    Si `spend_usd` viniera en quetzales, el gasto diario saltaría ~7.6×.
dia = collections.defaultdict(float)
for r in load("_FACT_VENTAS.csv"):
    if r.get("rol_ventana") == "BASE" and f(r.get("dias"), 1) == 1:
        dia[(r["ventana_ini"], r.get("cuenta_alias"))] += f(r["spend_usd"])
altos = ["%s %s $%.2f/día" % (k[0], k[1], v) for k, v in dia.items() if v > 500]
check(not altos, "El gasto por cuenta y día es plausible en DÓLARES (< $500/día)",
      "\n".join("      " + a for a in altos[:6]) or
      "      máximo observado: $%.2f/día" % (max(dia.values()) if dia else 0))

# ── 4. CP1 quedó normalizada de COP a USD ────────────────────────────────
cp1 = [f(r["spend_usd"]) for r in load("_FACT_VENTAS.csv")
       if r.get("cuenta_alias") == "CP1" and r.get("rol_ventana") == "BASE"]
check(not cp1 or max(cp1) < 500,
      "CP1 (factura en COP) está normalizada a USD ÷ %.1f" % TASA_COP,
      "      máximo $%.2f por fila — si estuviera en COP crudo sería de miles"
      % (max(cp1) if cp1 else 0))

# ── 5. ROAS del portafolio en un rango sano ──────────────────────────────
#    facturado (Q) ÷ pauta (Q). Si la pauta quedara sin convertir, el ROAS se
#    multiplicaría por ~7.6 y daría un número absurdo (30x+).
fac = sum(f(r["total_q"]) for r in load("_FACT_VENTAS.csv") if r.get("rol_ventana") == "BASE")
sp  = sum(f(r["spend_usd"]) for r in load("_FACT_VENTAS.csv") if r.get("rol_ventana") == "BASE")
roas = fac / (sp * TASA) if sp else 0
check(1.0 <= roas <= 15.0, "El ROAS del portafolio es plausible (facturado Q ÷ pauta Q)",
      "      ROAS {:.2f}x  ·  facturado Q{:,.0f}  ·  pauta Q{:,.0f}"
      "  (si la pauta quedara en USD daría {:.1f}x)".format(roas, fac, sp * TASA, roas * TASA))

# ── 6. Coherencia de _FACT_SEMANAL.csv ───────────────────────────────────
sem = [r for r in load("_FACT_SEMANAL.csv") if r.get("producto_key") == "TOTAL"]
if sem:
    raros = ["%s ROAS %s" % (r["semana_ini"], r["roas"])
             for r in sem if r.get("roas") and not (0.3 <= f(r["roas"]) <= 20)]
    check(not raros, "Cada semana del reporte tiene un ROAS plausible",
          "\n".join("      " + x for x in raros[:6]) or
          "      %d semanas revisadas" % len(sem))

# ── salida ────────────────────────────────────────────────────────────────
W = 70
print("═" * W)
print("VERIFICACIÓN DE MONEDAS — quetzales vs dólares")
print("Tasa vigente: Q%.2f por USD (de _PARAMETROS_FINANZAS.csv)" % TASA)
print("═" * W)
print()
print("  DROPI (órdenes + cartera) ...... QUETZALES · nunca se convierte")
print("  BANCO Relay .................... DÓLARES   · siempre × %.2f" % TASA)
print("  LucidSales `spend` ............. DÓLARES   · siempre × %.2f" % TASA)
print("  LucidSales `total` (la venta) .. QUETZALES · nunca se convierte")
print("  Cuenta CP1 `spend` ............. COP       · ÷ %.1f → USD → × %.2f" % (TASA_COP, TASA))
print()
for t, d in ok:
    print("✅ %s" % t)
    if d:
        print(d)
for t, d in fail:
    print("❌ %s" % t)
    if d:
        print(d)
print()
print("═" * W)
if fail:
    print("%d verificación(es) FALLARON — hay un número en la moneda equivocada." % len(fail))
    sys.exit(1)
print("Las %d verificaciones pasan: no hay conversiones dobles ni faltantes." % len(ok))
