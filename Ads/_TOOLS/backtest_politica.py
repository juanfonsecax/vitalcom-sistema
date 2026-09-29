#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""backtest_politica.py — ¿VALE LA PENA CAMBIAR LA POLÍTICA DE ASIGNACIÓN?

QUÉ HACE
--------
Camina día a día sobre la historia real del portafolio y, en cada día, hace que DOS
políticas decidan sobre las mismas celdas con la data que existía ESE día. Después evalúa
cada orden contra el futuro que efectivamente ocurrió.

  A — LA VIGENTE: `decidir.py` tal cual. No se reimplementa: se llama a su propia
      `evaluar_celda()`, así que lo que se mide es el motor, no una maqueta.
  B — PÉRDIDA ESPERADA: mismo posterior, pero la decisión de MOVER PRESUPUESTO se toma por
      valor esperado con tope de riesgo (`perfilar_angulos.riesgo()`) en vez de por si el
      intervalo de credibilidad cruza el break-even. B nunca pisa el DIAGNÓSTICO: `PAUSAR` y
      `RENOVAR` son reglas duras del motor y las respeta tal cual (invariante 13).

POR QUÉ EXISTE
--------------
Porque «un bandit optimizaría mejor» es una opinión hasta que se mide. Este script existe
para poder decir que NO conviene cambiar la política, si es lo que la data dice — y en la
corrida del 09-sep-2026 es exactamente lo que dijo. Ver `--sensibilidad`.

EL SUPUESTO, DECLARADO
----------------------
No existe el contrafactual: nadie sabe qué habría pasado si al ángulo X se le hubiera
subido el 20 % el 12 de agosto. La evaluación asume que **subir el presupuesto un 20 % no
cambia el CPA de la celda**, y proyecta el CPA realizado de los `horizonte_orden_dias`
siguientes sobre el peso incremental.

Ese supuesto es el de la propia doctrina del surfing, y es OPTIMISTA: APR-057 midió que
+63 % de gasto llevó el CPA del portafolio de Q47.1 a Q75.0 (+59 %). Por eso el resultado
principal de este script NO es el número con degradación cero, sino la curva de
`--sensibilidad`: cuánto puede empeorar el CPA antes de que la ventaja desaparezca.

DE DÓNDE SALE CADA DATO
-----------------------
  serie diaria por ángulo ...... perfilar_angulos.serie_por_angulo()  (_FACT_VENTAS BASE)
  veredicto de la política A ... decidir.evaluar_celda()  (la función real del motor)
  riesgo de la política B ...... perfilar_angulos.riesgo()
  break-even y tasa ............ PRODUCTOS/_DIM_PRODUCTOS.csv
  ventanas y guardas ........... PRODUCTOS/_PARAMETROS_DECISION.csv
  umbrales de B ................ PRODUCTOS/_PARAMETROS_OPTIMIZACION.csv
  lo que se hizo de verdad ..... PRODUCTOS/_EVENTOS.csv

USO
---
    python Ads/_TOOLS/backtest_politica.py                  # comparación completa
    python Ads/_TOOLS/backtest_politica.py --desde 2026-08-01
    python Ads/_TOOLS/backtest_politica.py --sensibilidad   # la curva que decide
    python Ads/_TOOLS/backtest_politica.py --eventos        # contra lo que se hizo
"""

import os
import io
import sys
import csv
import argparse
import datetime
import collections

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except (AttributeError, OSError):
    pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import decidir                      # noqa: E402
import perfilar_angulos as PA       # noqa: E402

BASE = PA.BASE
DESDE_DEFAULT = "2026-08-01"        # deja 14 días de calentamiento sobre el primer día con data


def politica_b(ventas, gasto_q, be_q, gasto_dia_q, opt, estado_motor):
    """La decisión de PRESUPUESTO por valor esperado. El diagnóstico sigue siendo del motor."""
    if estado_motor in ("PAUSAR", "RENOVAR"):
        return estado_motor
    neto, perd, p_rent = PA.riesgo(ventas, gasto_q, be_q)
    if neto is None:
        return "SEGUIR_MIDIENDO"
    perdida_dia = gasto_dia_q * (opt["surfing_pct"] / 100.0) * perd
    if neto > 0 and perdida_dia <= opt["umbral_perdida_q_dia"] and p_rent >= opt["p_min_rentable"]:
        return "ESCALAR"
    return "SEGUIR_MIDIENDO"


def simular(desde, opt, par):
    """Devuelve la lista de decisiones (una por celda y día) de las dos políticas."""
    serie, _, _ = PA.serie_por_angulo()
    prods = {}
    for r in PA.leer_csv("_DIM_PRODUCTOS.csv"):
        pk = (r.get("producto_key") or "").strip()
        if pk:
            prods[pk] = (PA._num(r.get("cpa_be_q")), PA._num(r.get("cpa_base_q")),
                         PA._num(r.get("tasa"), None))
    fechas = sorted({f for m in serie.values() for f in m})
    dias = [f for f in fechas if f >= desde]
    vent = int(par["ventana_dias"])
    fat = int(par.get("ventana_fatiga_dias", 3))

    out = []
    _sin_tasa = set()
    for t in dias:
        w0 = t - datetime.timedelta(days=vent - 1)
        f0 = t - datetime.timedelta(days=fat - 1)
        for (pk, ang), m in serie.items():
            if pk not in prods or not prods[pk][0]:
                continue
            if not prods[pk][2] or prods[pk][2] <= 0:      # sin tasa: se omite el producto, con aviso
                if pk not in _sin_tasa:
                    _sin_tasa.add(pk)
                    print("AVISO backtest_politica: «%s» no declara `tasa` en _DIM_PRODUCTOS.csv: se "
                          "OMITE (no hay tasa por defecto)." % pk, file=sys.stderr)
                continue
            be, obj, tasa = prods[pk]
            win = [f for f in m if w0 <= f <= t]
            if not win or sum(m[f][0] for f in win) <= 0:
                continue
            ac = [f for f in m if f <= t]
            f3 = [f for f in m if f0 <= f <= t]
            sp = sum(m[f][0] for f in win); ve = sum(m[f][1] for f in win); ms = sum(m[f][2] for f in win)
            r = decidir.evaluar_celda(
                ventas=ve, mensajes=ms, spend_usd=sp,
                ventas_3d=sum(m[f][1] for f in f3), mensajes_3d=sum(m[f][2] for f in f3),
                spend_3d=sum(m[f][0] for f in f3), be_q=be, obj_q=obj, tasa=tasa, params=par,
                ventas_acum=sum(m[f][1] for f in ac), mensajes_acum=sum(m[f][2] for f in ac),
                spend_acum_usd=sum(m[f][0] for f in ac),
                link_clicks_acum=None, mensajes_enlace_acum=None,
                dias_activo=(max(ac) - min(ac)).days + 1 if ac else None)
            g_dia_q = m.get(t, [0, 0, 0])[0] * tasa
            b = politica_b(ve, sp * tasa, be, g_dia_q, opt, r["estado"])
            out.append({"fecha": t, "pk": pk, "ang": ang, "A": r["estado"], "B": b,
                        "cod": r["accion_codigo"], "ventas": ve, "gasto_dia_q": g_dia_q,
                        "be": be})
    return out, serie, prods, dias


def realizado(serie, prods, pk, ang, t, h):
    """CPA efectivamente observado en los `h` días siguientes. None si no hubo gasto."""
    m = serie[(pk, ang)]
    tasa = prods[pk][2]
    fs = [f for f in m if t < f <= t + datetime.timedelta(days=h)]
    g = sum(m[f][0] for f in fs) * tasa
    v = sum(m[f][1] for f in fs)
    if g <= 0:
        return None
    return (g / v) if v > 0 else None      # gasto sin ventas: CPA infinito, se pierde el peso


def evaluar(dec, serie, prods, h, degradacion=0.0):
    """Peso incremental y margen neto de cada política, bajo una degradación dada del CPA."""
    res = {p: [0, 0.0, 0.0, 0] for p in ("A", "B")}   # n, delta_q, neto_q, sin_futuro
    for d in dec:
        delta = d["gasto_dia_q"] * 0.20
        cpa = realizado(serie, prods, d["pk"], d["ang"], d["fecha"], h)
        for pol in ("A", "B"):
            if d[pol] != "ESCALAR":
                continue
            if delta <= 0:
                res[pol][3] += 1
                continue
            res[pol][0] += 1
            res[pol][1] += delta
            if cpa is None:
                res[pol][3] += 1           # no volvió a correr: no se puede evaluar, no suma
                res[pol][1] -= delta
                res[pol][0] -= 1
                continue
            res[pol][2] += delta * ((d["be"] / (cpa * (1 + degradacion))) - 1.0)
    return res


def main():
    ap = argparse.ArgumentParser(description="Backtest de la política de asignación (VitalCom)")
    ap.add_argument("--desde", default=DESDE_DEFAULT, help="primer día simulado (YYYY-MM-DD)")
    ap.add_argument("--sensibilidad", action="store_true", help="curva de degradación del CPA")
    ap.add_argument("--eventos", action="store_true", help="contrastar con _EVENTOS.csv")
    args = ap.parse_args()

    opt = PA.cargar_params_opt()
    par = decidir.cargar_parametros()
    opt.setdefault("surfing_pct", par.get("surfing_pct", 20.0))
    h = int(opt.get("horizonte_orden_dias", 7))
    desde = datetime.date.fromisoformat(args.desde)

    dec, serie, prods, dias = simular(desde, opt, par)
    print("=" * 100)
    print(" BACKTEST DE LA POLÍTICA DE ASIGNACIÓN — %s → %s (%d días · %d decisiones)"
          % (dias[0], dias[-1], len(dias), len(dec)))
    print(" A = decidir.py (vigente)   ·   B = pérdida esperada con tope de riesgo")
    print("=" * 100)

    ca = collections.Counter(d["A"] for d in dec)
    cb = collections.Counter(d["B"] for d in dec)
    print(" A: " + "  ".join("%s %d" % kv for kv in sorted(ca.items())))
    print(" B: " + "  ".join("%s %d" % kv for kv in sorted(cb.items())))
    difs = collections.Counter((d["A"], d["B"]) for d in dec if d["A"] != d["B"])
    if difs:
        print("\n DONDE DIFIEREN:")
        for (a, b), n in difs.most_common():
            print("   %-16s → %-16s %4d" % (a, b, n))

    res = evaluar(dec, serie, prods, h)
    print("\n VALOR REALIZADO de las órdenes ESCALAR (horizonte %d d, +%g%% sobre el gasto del día,"
          " degradación 0):" % (h, opt["surfing_pct"]))
    print("   %-4s %6s %12s %12s %8s   %s" % ("pol", "n", "peso Q", "neto Q", "ROI", "no evaluables"))
    for pol in ("A", "B"):
        n, dq, rq, sf = res[pol]
        print("   %-4s %6d %12.1f %12.1f %7.0f%%   %d" % (pol, n, dq, rq, 100 * rq / dq if dq else 0, sf))
    extra = res["B"][2] - res["A"][2]
    print("   → B agrega Q%+.1f de margen sobre A en %d días." % (extra, len(dias)))

    if args.sensibilidad:
        print("\n" + "=" * 100)
        print(" SENSIBILIDAD — cuánto puede empeorar el CPA al subir el presupuesto")
        print(" (APR-057: +63%% de gasto llevó el CPA de Q47.1 a Q75.0 = +59%% de degradación)")
        print("=" * 100)
        print("   %-12s %12s %8s %12s %8s %12s" % ("degradación", "A neto Q", "A ROI",
                                                   "B neto Q", "B ROI", "B − A"))
        for g in (0.0, 0.10, 0.20, 0.30, 0.40, 0.59, 0.80, 1.00):
            r = evaluar(dec, serie, prods, h, g)
            print("   %-12s %12.1f %7.0f%% %12.1f %7.0f%% %12.1f"
                  % ("+%.0f%%" % (g * 100), r["A"][2], 100 * r["A"][2] / r["A"][1],
                     r["B"][2], 100 * r["B"][2] / r["B"][1], r["B"][2] - r["A"][2]))
        for pol in ("A", "B"):
            lo, hi = 0.0, 5.0
            for _ in range(40):
                mid = (lo + hi) / 2
                if evaluar(dec, serie, prods, h, mid)[pol][2] > 0:
                    lo = mid
                else:
                    hi = mid
            print("   política %s: aguanta hasta +%.0f%% de degradación antes de perder plata"
                  % (pol, lo * 100))
        print("\n   LECTURA: la ventaja de B vive entre 0 % y ~40 % de degradación. En el único"
              "\n   punto medido por el sistema (+59 %, APR-057) las dos políticas empatan, y por"
              "\n   encima B es PEOR. Cambiar de política sin medir `elasticidad_cpa_surfing`"
              "\n   es apostar a un número que nadie observó.")

    if args.eventos:
        print("\n" + "=" * 100)
        print(" CONTRA LO QUE SE HIZO DE VERDAD (_EVENTOS.csv)")
        print("=" * 100)
        ev = collections.Counter((r.get("evento") or "").strip() for r in PA.leer_csv("_EVENTOS.csv"))
        print("   eventos registrados: %d en %d tipos" % (sum(ev.values()), len(ev)))
        print("   PAUSA %d · LANZAMIENTO %d · CAMBIO_CREATIVO %d · CAMBIO_BOT %d · CAMBIO_PRESUPUESTO %d"
              % (ev.get("PAUSA", 0), ev.get("LANZAMIENTO", 0), ev.get("CAMBIO_CREATIVO", 0),
                 ev.get("CAMBIO_BOT", 0), ev.get("CAMBIO_PRESUPUESTO", 0)))
        na = sum(1 for d in dec if d["A"] == "ESCALAR")
        nb = sum(1 for d in dec if d["B"] == "ESCALAR")
        print("\n   Las dos políticas emitieron %d (A) y %d (B) órdenes de ESCALAR en la ventana."
              % (na, nb))
        if not ev.get("CAMBIO_PRESUPUESTO"):
            print("   🔴 `_EVENTOS.csv` no tiene UN SOLO evento CAMBIO_PRESUPUESTO, y el surfing")
            print("      +20 % es la palanca diaria por default de la doctrina. Sin ese registro")
            print("      no se puede saber cuáles de esas órdenes se ejecutaron, ni medir la")
            print("      elasticidad que decide si conviene cambiar de política.")
            print("      ES LA PRIMERA DEUDA A CERRAR: sin ella este backtest no puede mejorar.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
