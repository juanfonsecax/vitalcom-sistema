#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""perfilar_angulos.py — EL PERFIL DE ÁNGULO Y SU CICLO DE VIDA.

QUÉ HACE
--------
Le da IDENTIDAD PERSISTENTE e HISTORIAL PROPIO a cada ángulo del portafolio, y deriva
—nunca declara— en qué punto de su vida está: `EN_PRUEBA → MIDIENDO → ESCALANDO →
SOSTENIDO → EN_DECLIVE → RENOVADO → DORMIDO → APAGADO`. Escribe una fila por perfil en
`PRODUCTOS/_ESTADO_ANGULOS.csv`, que `flujo.py` puede leer como predicado `csv_campo`.

POR QUÉ EXISTE
--------------
`decidir.py` responde «¿qué hago HOY con esta celda?» sobre una ventana móvil de 14 días.
Nadie responde «¿qué ha sido este ángulo a lo largo de su vida, y en qué punto de ella
está?». Sin eso el sistema no puede distinguir un ángulo que nunca funcionó de uno que
funcionó y se cansó — que es exactamente la distinción que la regla congelada de
`test_decidir.py` exige: *un ángulo con historia rentable no se APAGA por una mala racha,
se le RENUEVA el concepto*.

EL GRANO ES EL ÁNGULO, NO EL ÁNGULO × CONCEPTO — y no es una preferencia:
  · APR-004 lo midió: índice de dispersión de las ventas por conjunto-cuenta 1.12 (azar de
    Poisson puro, no hay nada que aprender), por conjunto 1.89, por `angulo_key` 2.99
    (sobredispersión = señal real). El grano con señal es el ángulo.
  · Si la entidad fuera ángulo × concepto, RENOVAR el concepto crearía una entidad nueva y
    borraría la historia — justo lo que la regla congelada prohíbe. El concepto es el
    EQUIPAMIENTO del perfil (columna `generacion_creativa`), no su identidad.

QUÉ NO HACE — Y ESTO ES DELIBERADO
----------------------------------
**No emite órdenes.** El invariante 13 dice que ninguna orden de pausar o escalar sale sin
`decidir.py`, y este script no lo reemplaza: lo CONSUME (`decidir.analizar_portafolio()`) y
copia su veredicto en `estado_motor` / `accion_motor` sin recalcularlo. Lo que agrega es el
ORDEN de esa cola (`prioridad_ts`) y el TAMAÑO DEL RIESGO de moverla (`neto_por_q`,
`perdida_q_dia`, `p_rentable`), que el motor no calcula.

Y no ordena porque todavía no puede: el parámetro `elasticidad_cpa_surfing` está en
SIN_MEDIR. `_EVENTOS.csv` tiene 84 eventos y **cero** `CAMBIO_PRESUPUESTO`, así que nadie
sabe cuánto empeora el CPA de una celda al subirle el 20 % — y el backtest del 09-sep-2026
(`backtest_politica.py`) mide que toda la ventaja de rankear por pérdida esperada se evapora
si esa degradación es la que APR-057 estimó. Mientras el parámetro sea SIN_MEDIR, este
script RANKEA y no MANDA.

DE DÓNDE SALE CADA DATO
-----------------------
  ventas · gasto · mensajes .... PRODUCTOS/_FACT_VENTAS.csv  (SOLO `rol_ventana=BASE`)
  ángulo del conjunto .......... PRODUCTOS/_DIM_CONJUNTOS.csv
  break-even · CPA objetivo .... PRODUCTOS/_DIM_PRODUCTOS.csv  (cpa_be_q, cpa_base_q, tasa)
  veredicto del motor .......... Ads/_TOOLS/decidir.py (en proceso; NO se recalcula acá)
  ventanas y guardas ........... PRODUCTOS/_PARAMETROS_DECISION.csv
  umbrales de este script ...... PRODUCTOS/_PARAMETROS_OPTIMIZACION.csv
  renovaciones de creativo ..... PRODUCTOS/_EVENTOS.csv  (evento=CAMBIO_CREATIVO)
  `desde` de cada estado ....... PRODUCTOS/_ESTADO_ANGULOS.csv de la corrida anterior

POR QUÉ SOLO `rol_ventana=BASE`
-------------------------------
`DATA_PLAYBOOK.md` es explícito: BASE suma, **CONTROL solapa a propósito y NUNCA suma**
(APR-020 lo usa como prueba anti-doble-conteo). Medido el 09-sep-2026, sumar CONTROL infla
el acumulado del portafolio de 506 a 904 ventas (+79 %), y de forma desigual por producto
(NUSAVA +100 %, VARICOSE +145 %, CLEARSTEM +59 %, TINNIDROP +69 %). Este script agrega solo
BASE, y para que la diferencia no quede escondida publica `ventas_control` con lo que
descartó. Todos los consumidores de venta filtran BASE (`decidir.py`, `flujo.py`,
`sembrar_anuncios.py`, `stg_ventas.sql`); la columna queda como control de integridad.

USO
---
    python Ads/_TOOLS/perfilar_angulos.py                 # informe + escribe el CSV
    python Ads/_TOOLS/perfilar_angulos.py TINNIDROP       # un solo producto
    python Ads/_TOOLS/perfilar_angulos.py --json          # salida JSON
    python Ads/_TOOLS/perfilar_angulos.py --registrar     # anexa TRANSICION_ANGULO a _EVENTOS
"""

import os
import io
import sys
import csv
import json
import argparse
import datetime
import collections

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except (AttributeError, OSError):
    pass

from scipy.stats import gamma as _gamma

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROD = os.path.join(BASE, "PRODUCTOS")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

SALIDA = os.path.join(PROD, "_ESTADO_ANGULOS.csv")
PARAMS_OPT = os.path.join(PROD, "_PARAMETROS_OPTIMIZACION.csv")
TASA_DEFAULT = 7.62

# El ciclo de vida. El orden de esta lista ES el orden de evaluación de los predicados:
# el primero que se cumple manda. Cambiar el orden cambia la doctrina, no solo el código.
ESTADOS = ["APAGADO_ABANDONO", "APAGADO", "DORMIDO", "EN_DECLIVE",
           "ESCALANDO", "SOSTENIDO", "RENOVADO", "EN_PRUEBA", "MIDIENDO"]


def _num(v, d=0.0):
    try:
        f = float(v)
    except (TypeError, ValueError):
        return d
    return d if f != f else f


def leer_csv(nombre):
    p = os.path.join(PROD, nombre)
    if not os.path.exists(p):
        return []
    with io.open(p, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def cargar_params_opt():
    """Los umbrales de ESTE script. Un valor no numérico (SIN_MEDIR) se conserva como texto."""
    p = {}
    for r in leer_csv("_PARAMETROS_OPTIMIZACION.csv"):
        k = (r.get("parametro") or "").strip()
        v = (r.get("valor") or "").strip()
        if not k:
            continue
        try:
            p[k] = float(v)
        except ValueError:
            p[k] = v
    return p


def riesgo(ventas, gasto_q, be_q):
    """Descompone un quetzal incremental en su valor esperado y su cola mala.

    Mismo posterior que decidir.py — no se inventa un modelo nuevo:
        ventas ~ Poisson(lambda);  lambda | k ~ Gamma(k + 0.5, 1)   (Jeffreys)
        CPA = gasto_q / lambda  ->  margen por quetzal = be*lambda/gasto - 1

    Devuelve (neto_por_q, perdida_por_q, p_rentable), todo en quetzales por quetzal:
        neto     = E[be*lambda/g - 1]                 el valor esperado del movimiento
        perdida  = E[(1 - be*lambda/g)+]              solo la cola que pierde plata
        p_rent   = P(CPA <= be)

    Por qué esto y no el intervalo de credibilidad: el IC es una regla de SIGNIFICANCIA y a
    1-3 ventas/día por celda casi nunca se resuelve — de ahí la parálisis que decidir.py
    resuelve emitiendo SEGUIR_MIDIENDO. La pérdida esperada es una regla de DECISIÓN: dice
    cuántos quetzales cuesta equivocarse, y eso sí es computable con 6 ventas. Las dos
    conviven: el IC sigue gobernando lo irreversible (invariante 13), esto ordena el resto.
    """
    if gasto_q <= 0 or be_q <= 0:
        return None, None, None
    a = ventas + 0.5
    c = gasto_q / be_q                 # lambda por debajo de c = celda sobre el break-even
    r = be_q / gasto_q
    F_a = float(_gamma.cdf(c, a))
    F_a1 = float(_gamma.cdf(c, a + 1))
    neto = r * a - 1.0
    perdida = max(F_a - r * a * F_a1, 0.0)
    return neto, perdida, 1.0 - F_a


def prob_mejor(celdas, n=4000, semilla=20260909):
    """Thompson Sampling honesto: P(esta celda es la de menor CPA del producto).

    Muestrea lambda ~ Gamma(k+0.5, 1) por celda, calcula el CPA muestreado y cuenta cuántas
    veces cada una queda primera. No es un ranking por CPA puntual: una celda con 3 ventas y
    CPA bajo pierde contra una de 30 ventas y CPA parecido, que es el comportamiento correcto.
    Semilla fija: dos corridas del mismo día tienen que dar la misma cola.
    """
    import numpy as np
    vivos = [c for c in celdas if c["gasto_ventana_q"] > 0]
    if not vivos:
        return {}
    rng = np.random.default_rng(semilla)
    m = np.vstack([rng.gamma(c["ventas_ventana"] + 0.5, 1.0, n) / c["gasto_ventana_q"]
                   for c in vivos])          # ventas por quetzal = 1/CPA (mayor es mejor)
    ganador = m.argmax(axis=0)
    cuenta = collections.Counter(ganador.tolist())
    return {vivos[i]["clave"]: cuenta.get(i, 0) / n for i in range(len(vivos))}


def serie_por_angulo(pk_filtro=None):
    """Serie diaria por (producto, angulo_key) desde _FACT_VENTAS, SOLO ventanas BASE.

    Una fila que abarca N días se PRORRATEA en partes iguales sobre esos N días. Es una
    aproximación y se declara: 506 de 2 100 filas BASE son multi-día (3, 7, 8 y 10 días),
    concentradas en jul-ago. Sin prorrateo, una ventana de 10 días entra como un solo día y
    deforma cualquier lectura de recencia; el prorrateo reparte mal DENTRO del tramo pero
    respeta el total y la posición en el calendario, que es lo que el ciclo de vida necesita.
    """
    from alias import mapa_de
    am = mapa_de(leer_csv("_ALIAS_CONJUNTOS.csv"))
    ang = {}
    for r in leer_csv("_DIM_CONJUNTOS.csv"):
        cm = (r.get("conjunto_meta") or "").strip()
        ang[((r.get("producto_key") or "").strip(), am.get(cm, cm))] = (r.get("angulo_key") or "").strip()

    serie = collections.defaultdict(lambda: collections.defaultdict(lambda: [0.0, 0.0, 0.0]))
    control = collections.Counter()
    huerfanos = collections.defaultdict(lambda: [0.0, 0.0])   # (pk, conjunto) -> [gasto$, ventas]
    for r in leer_csv("_FACT_VENTAS.csv"):
        pk = (r.get("producto_key") or "").strip()
        if pk_filtro and pk != pk_filtro:
            continue
        cj = (r.get("conjunto") or "").strip()
        cj = am.get(cj, cj)                 # un renombrado en Meta cruza con su dimensión
        if not cj or cj == "SIN_ATRIBUCION":
            continue                        # filas sintéticas de cuadre: no son una celda
        ak = ang.get((pk, cj))
        if not ak:
            # Grafía que NO cruza con _DIM_CONJUNTOS ni por alias: el gasto existe pero su ÁNGULO se pierde
            # y la celda se cuenta como un ángulo aparte — un ángulo fantasma que compite en el
            # ranking contra el ángulo real del que salió. Es el caso que DATA_PLAYBOOK manda
            # corregir anexando la grafía con el MISMO angulo_key (no normalizando la llave).
            ak = cj
            if (r.get("rol_ventana") or "").strip() == "BASE":
                h = huerfanos[(pk, cj)]
                h[0] += _num(r.get("spend_usd"))
                h[1] += _num(r.get("ventas"))
        if (r.get("rol_ventana") or "").strip() != "BASE":
            control[(pk, ak)] += int(_num(r.get("ventas")))
            continue
        try:
            ini = datetime.date.fromisoformat((r.get("ventana_ini") or "").strip())
            fin = datetime.date.fromisoformat((r.get("ventana_fin") or "").strip())
        except ValueError:
            continue
        n = max((fin - ini).days + 1, 1)
        sp, ve, ms = _num(r.get("spend_usd")), _num(r.get("ventas")), _num(r.get("mensajes"))
        for i in range(n):
            c = serie[(pk, ak)][ini + datetime.timedelta(days=i)]
            c[0] += sp / n
            c[1] += ve / n
            c[2] += ms / n
    return serie, control, huerfanos


def ultimo_cambio_creativo():
    """fecha del último CAMBIO_CREATIVO por (producto, conjunto). El evento es de conjunto;
    el perfil es de ángulo, así que se toma el más reciente de cualquiera de sus conjuntos."""
    out = {}
    for r in leer_csv("_EVENTOS.csv"):
        if (r.get("evento") or "").strip() != "CAMBIO_CREATIVO":
            continue
        try:
            f = datetime.date.fromisoformat((r.get("fecha") or "").strip())
        except ValueError:
            continue
        k = (r.get("producto_key") or "").strip()
        if k not in out or f > out[k]:
            out[k] = f
    return out


def estado_previo():
    """`desde` y `estado` de la corrida anterior: el perfil conserva su reloj propio."""
    prev = {}
    for r in leer_csv("_ESTADO_ANGULOS.csv"):
        prev[((r.get("producto_key") or "").strip(), (r.get("angulo_key") or "").strip())] = r
    return prev


def clasificar(p, par, opt):
    """Deriva el estado del perfil. Cada rama es un PREDICADO sobre data, nunca un juicio."""
    if p["dias_sin_gasto"] is not None and p["dias_sin_gasto"] >= opt["dias_sin_gasto_apagado"]:
        return "APAGADO_ABANDONO", "sin gasto hace %d días (≥ %g)" % (
            p["dias_sin_gasto"], opt["dias_sin_gasto_apagado"])
    if p["estado_motor"] == "PAUSAR":
        return "APAGADO", "el motor ordena PAUSAR (%s)" % p["accion_codigo"]
    if p["dias_sin_gasto"] is not None and p["dias_sin_gasto"] >= opt["dias_sin_gasto_dormido"]:
        return "DORMIDO", "sin gasto hace %d días (≥ %g): no está rindiendo mal, no está corriendo" % (
            p["dias_sin_gasto"], opt["dias_sin_gasto_dormido"])
    if p["estado_motor"] == "RENOVAR":
        return "EN_DECLIVE", "el motor ordena RENOVAR concepto (fatiga con historia rentable)"
    if p["estado_motor"] == "ESCALAR":
        return "ESCALANDO", "el motor ordena ESCALAR (%s)" % p["accion_codigo"]
    if p["ganador_historico"]:
        return "SOSTENIDO", "historia rentable: %g ventas acum a CPA Q%.1f ≤ BE Q%.1f" % (
            p["ventas_acum"], p["cpa_acum_q"], p["be_q"])
    if p["renovado_hace"] is not None and p["renovado_hace"] <= par["ventana_dias"]:
        return "RENOVADO", "CAMBIO_CREATIVO hace %d días, esperando veredicto" % p["renovado_hace"]
    if p["gasto_acum_q"] < p["be_q"]:
        return "EN_PRUEBA", "gastó Q%.0f de su presupuesto de decisión (1×BE Q%.0f)" % (
            p["gasto_acum_q"], p["be_q"])
    return "MIDIENDO", "PD consumido, sin veredicto: %g ventas acum" % p["ventas_acum"]


def construir(pk_filtro=None):
    import decidir
    par = decidir.cargar_parametros()
    opt = cargar_params_opt()
    serie, control, huerfanos = serie_por_angulo(pk_filtro)

    prods = {}
    for r in leer_csv("_DIM_PRODUCTOS.csv"):
        pk = (r.get("producto_key") or "").strip()
        if pk:
            prods[pk] = {"be": _num(r.get("cpa_be_q")), "obj": _num(r.get("cpa_base_q")),
                         "tasa": _num(r.get("tasa"), TASA_DEFAULT) or TASA_DEFAULT,
                         "estado": (r.get("estado") or "").strip()}

    # El veredicto del motor, tal cual. NO se recalcula (invariante 13).
    dec = decidir.analizar_portafolio(producto_filtro=pk_filtro, grano="angulo")
    motor = {}
    for pr in dec.get("productos", []):
        for c in pr.get("celdas", []):
            motor[(pr["producto_key"], c["celda"])] = c

    hoy = datetime.date.today()
    ult_data = None
    for m in serie.values():
        for f in m:
            if ult_data is None or f > ult_data:
                ult_data = f
    ventana = int(par["ventana_dias"])
    cambios = ultimo_cambio_creativo()
    prev = estado_previo()

    perfiles = []
    for (pk, ak), m in serie.items():
        info = prods.get(pk)
        if not info or not info["be"]:
            continue
        tasa, be = info["tasa"], info["be"]
        fechas = sorted(m)
        w0 = ult_data - datetime.timedelta(days=ventana - 1)
        win = [f for f in fechas if f >= w0]
        g_ac = sum(m[f][0] for f in fechas) * tasa
        v_ac = sum(m[f][1] for f in fechas)
        g_wn = sum(m[f][0] for f in win) * tasa
        v_wn = sum(m[f][1] for f in win)
        ms_ac = sum(m[f][2] for f in fechas)
        con_gasto = [f for f in fechas if m[f][0] > 0]
        ult_gasto = max(con_gasto) if con_gasto else None
        cpa_ac = (g_ac / v_ac) if v_ac > 0 else None
        cel = motor.get((pk, ak), {})
        neto, perd, p_rent = riesgo(v_wn, g_wn, be)
        rc = cambios.get(pk)
        p = {
            "clave": ak, "producto_key": pk, "angulo_key": ak, "be_q": be,
            "ventas_acum": round(v_ac, 1), "gasto_acum_q": round(g_ac, 1),
            "cpa_acum_q": round(cpa_ac, 1) if cpa_ac else None,
            "mensajes_acum": round(ms_ac, 0),
            "cierre_acum_pct": round(v_ac / ms_ac * 100, 1) if ms_ac > 0 else None,
            "ventas_ventana": round(v_wn, 1), "gasto_ventana_q": round(g_wn, 1),
            "cpa_ventana_q": round(g_wn / v_wn, 1) if v_wn > 0 else None,
            "pct_pd": round(g_ac / be * 100, 0) if be else None,
            "dias_con_gasto": len(con_gasto),
            "primer_dia": fechas[0].isoformat(), "ultimo_dia_gasto": ult_gasto.isoformat() if ult_gasto else "",
            "dias_sin_gasto": (ult_data - ult_gasto).days if ult_gasto else None,
            "estado_motor": cel.get("estado", "SIN_VENTANA"),
            "accion_codigo": cel.get("accion_codigo", ""),
            "accion_motor": cel.get("accion_sugerida", ""),
            "banda_homogenea": "SI" if cel.get("banda_ok", True) else "NO",
            "ventas_control": control.get((pk, ak), 0),
            "renovado_hace": (ult_data - rc).days if rc else None,
            "neto_por_q": round(neto, 3) if neto is not None else None,
            "perdida_por_q": round(perd, 3) if perd is not None else None,
            "p_rentable": round(p_rent, 3) if p_rent is not None else None,
        }
        p["ganador_historico"] = bool(
            v_ac >= par.get("min_ventas_ganador", 5) and cpa_ac is not None and cpa_ac <= be)
        p["estado"], p["evidencia"] = clasificar(p, par, opt)
        k = (pk, ak)
        antes = prev.get(k, {})
        p["estado_anterior"] = (antes.get("estado") or "").strip()
        p["desde"] = (antes.get("desde") or "").strip() if p["estado_anterior"] == p["estado"] else hoy.isoformat()
        if not p["desde"]:
            p["desde"] = hoy.isoformat()
        perfiles.append(p)

    # Thompson Sampling por producto, y la porción de gasto del día que se lleva cada perfil.
    for pk in {p["producto_key"] for p in perfiles}:
        grupo = [p for p in perfiles if p["producto_key"] == pk]
        pm = prob_mejor(grupo)
        for p in grupo:
            p["prioridad_ts"] = round(pm.get(p["clave"], 0.0), 3)
        gtot = sum(p["gasto_ventana_q"] for p in grupo) or 1.0
        for p in grupo:
            p["pct_gasto_producto"] = round(p["gasto_ventana_q"] / gtot * 100, 1)

    perfiles.sort(key=lambda p: (p["producto_key"], -(p.get("prioridad_ts") or 0), -p["ventas_acum"]))
    return perfiles, opt, par, dec, huerfanos


COLS = ["producto_key", "angulo_key", "estado", "desde", "estado_anterior", "evidencia",
        "estado_motor", "accion_codigo", "ventas_acum", "gasto_acum_q", "cpa_acum_q", "cpa_be_q",
        "pct_pd", "mensajes_acum", "cierre_acum_pct", "ventas_ventana", "gasto_ventana_q",
        "cpa_ventana_q", "p_rentable", "neto_por_q", "perdida_por_q", "prioridad_ts",
        "pct_gasto_producto", "banda_homogenea", "dias_con_gasto", "primer_dia",
        "ultimo_dia_gasto", "dias_sin_gasto", "ventas_control", "accion_motor"]


def escribir(perfiles):
    with io.open(SALIDA, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLS, extrasaction="ignore")
        w.writeheader()
        for p in perfiles:
            r = dict(p)
            r["cpa_be_q"] = p["be_q"]
            w.writerow(r)
    return SALIDA


def registrar_transiciones(perfiles):
    """Anexa TRANSICION_ANGULO a _EVENTOS.csv. Solo con --registrar: una corrida de lectura
    nunca escribe en el log de acciones."""
    ev = os.path.join(PROD, "_EVENTOS.csv")
    if not os.path.exists(ev):
        return 0
    with io.open(ev, encoding="utf-8-sig", newline="") as f:
        cols = next(csv.reader(f))
    nuevas = [p for p in perfiles if p["estado_anterior"] and p["estado_anterior"] != p["estado"]]
    if not nuevas:
        return 0
    hoy = datetime.date.today().isoformat()
    with io.open(ev, "a", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        for p in nuevas:
            w.writerow({"fecha": hoy, "producto_key": p["producto_key"],
                        "conjunto_meta": p["angulo_key"], "evento": "TRANSICION_ANGULO",
                        "valor_antes": p["estado_anterior"], "valor_despues": p["estado"],
                        "motivo": p["evidencia"], "fuente_decision": "perfilar_angulos.py"})
    return len(nuevas)


def imprimir(perfiles, opt, par, dec, huerfanos):
    print("=" * 118)
    print(" PERFILES DE ÁNGULO — ciclo de vida derivado de la data (ventana %g d · fuente: _FACT_VENTAS BASE)"
          % par["ventana_dias"])
    if dec.get("datos_hasta"):
        print(" Data: %s → %s   (rezago %s d)" % (dec.get("datos_desde"), dec["datos_hasta"],
                                                  dec.get("rezago_dias")))
    el = opt.get("elasticidad_cpa_surfing")
    if not isinstance(el, float):
        print(" ⚠️  elasticidad_cpa_surfing = %s → este informe RANKEA, no ordena. La orden sigue"
              % el)
        print("     saliendo de decidir.py (invariante 13). Se mide registrando CAMBIO_PRESUPUESTO.")
    print("=" * 118)
    for pk in sorted({p["producto_key"] for p in perfiles}):
        g = [p for p in perfiles if p["producto_key"] == pk]
        vivos = [p for p in g if p["estado"] in ("ESCALANDO", "SOSTENIDO")]
        print("\n[%s]  BE Q%.2f  ·  %d perfiles  ·  %d vivos (mínimo %g)"
              % (pk, g[0]["be_q"], len(g), len(vivos), opt["min_angulos_vivos"]))
        if len(vivos) < opt["min_angulos_vivos"]:
            print("   🔴 DEPENDENCIA DE UN SOLO PÚBLICO: %d ángulo(s) vivo(s). Generar variante"
                  " (etapa-3 ángulo adyacente · etapa-9 concepto nuevo)." % len(vivos))
        print("   %-18s %-26s %5s %8s %8s %6s %6s %7s %s"
              % ("ESTADO", "ÁNGULO", "V.ac", "CPA.ac", "CPA.win", "P(re)", "TS", "%gasto", "evidencia"))
        print("   " + "-" * 113)
        for p in g:
            print("   %-18s %-26s %5.0f %8s %8s %6s %6s %6.0f%% %s"
                  % (p["estado"], p["angulo_key"][:26], p["ventas_acum"],
                     ("Q%.1f" % p["cpa_acum_q"]) if p["cpa_acum_q"] else "-",
                     ("Q%.1f" % p["cpa_ventana_q"]) if p["cpa_ventana_q"] else "-",
                     ("%.0f%%" % (p["p_rentable"] * 100)) if p["p_rentable"] is not None else "-",
                     ("%.2f" % p["prioridad_ts"]) if p.get("prioridad_ts") is not None else "-",
                     p.get("pct_gasto_producto", 0), p["evidencia"][:38]))
        ctrl = sum(p["ventas_control"] for p in g)
        if ctrl:
            print("   · %d ventas de ventanas CONTROL quedaron FUERA de este acumulado "
                  "(DATA_PLAYBOOK: CONTROL nunca suma)." % ctrl)
        mez = [p for p in g if p["banda_homogenea"] == "NO"]
        if mez:
            print("   ⚠ BANDA DE EDAD MEZCLADA entre réplicas en %d perfil(es): %s."
                  % (len(mez), ", ".join(p["angulo_key"] for p in mez)))
            print("     Su CPA promedia DOS poblaciones. APR-060 midió 15× de diferencia entre "
                  "bandas en el\n     mismo ángulo, producto y creativo: ese CPA no corona nada "
                  "hasta separarlas (_DIM_BANDAS.csv).")

    if huerfanos:
        print("\n   GRAFÍAS SIN DIMENSIÓN — su gasto compite en el ranking como un ÁNGULO FANTASMA:")
        for (pk, cj), (g_usd, v) in sorted(huerfanos.items(), key=lambda x: -x[1][0]):
            print("   🔴 %-11s «%s»  $%.2f · %.0f ventas" % (pk, cj, g_usd, v))
        print("      Arreglo (DATA_PLAYBOOK): anexar la grafía a _DIM_CONJUNTOS.csv con el MISMO")
        print("      angulo_key — nunca normalizar la llave — o registrarla en _ALIAS_CONJUNTOS.csv.")

    print("\n" + "=" * 118)
    c = collections.Counter(p["estado"] for p in perfiles)
    print(" " + "  ·  ".join("%s %d" % (e, c[e]) for e in ESTADOS if c.get(e)))
    print("=" * 118)


COLOR = {"ESCALANDO": "#1a7f37", "SOSTENIDO": "#0969da", "EN_DECLIVE": "#9a6700",
         "RENOVADO": "#8250df", "DORMIDO": "#6e7781", "APAGADO": "#cf222e",
         "APAGADO_ABANDONO": "#82071e", "EN_PRUEBA": "#57606a", "MIDIENDO": "#57606a"}

VISTA = os.path.join(BASE, "VISTAS", "PERFILES.html")


PLANTILLA = """<!doctype html><html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Perfiles de angulo</title>
<style>
:root{--bg:#fff;--fg:#1f2328;--mut:#57606a;--bd:#d0d7de;--card:#f6f8fa;--warn:#fff8c5;--warnbd:#d4a72c}
@media (prefers-color-scheme:dark){:root{--bg:#0d1117;--fg:#e6edf3;--mut:#8b949e;--bd:#30363d;--card:#161b22;--warn:#272115;--warnbd:#9e6a03}}
*{box-sizing:border-box}body{margin:0;padding:20px;background:var(--bg);color:var(--fg);
font:14px/1.5 -apple-system,Segoe UI,Roboto,sans-serif}
h1{font-size:19px;margin:0 0 4px}h2{font-size:15px;margin:26px 0 8px;border-bottom:1px solid var(--bd);padding-bottom:5px}
h2 small{font-weight:400;color:var(--mut);font-size:12px}
.meta{color:var(--mut);font-size:12px;margin-bottom:14px}
.nota{background:var(--warn);border:1px solid var(--warnbd);border-radius:6px;padding:10px 12px;margin:12px 0;font-size:13px}
.alerta{background:var(--warn);border-left:3px solid var(--warnbd);padding:8px 11px;margin:8px 0;font-size:13px;border-radius:0 5px 5px 0}
table{width:100%;border-collapse:collapse;font-size:13px}
th{text-align:left;color:var(--mut);font-weight:600;font-size:11px;text-transform:uppercase;
letter-spacing:.03em;padding:6px 8px;border-bottom:1px solid var(--bd)}
td{padding:6px 8px;border-bottom:1px solid var(--bd);vertical-align:top}
tr:hover td{background:var(--card)}
.n{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
.ang{font-weight:600}.ev{color:var(--mut);font-size:12px}
.e{display:inline-block;color:#fff;padding:1px 7px;border-radius:10px;font-size:10.5px;
font-weight:700;letter-spacing:.02em;white-space:nowrap}
code{background:var(--card);padding:1px 5px;border-radius:4px;font-size:12px}
.wrap{overflow-x:auto}
</style></head><body>
<h1>Perfiles de angulo &mdash; ciclo de vida</h1>
<div class="meta">Ventana @@VENT@@ d &middot; data @@DESDE@@ &rarr; @@HASTA@@ (rezago @@REZ@@ d)
&middot; generado @@HOY@@ &middot; fuente <code>_FACT_VENTAS.csv</code> (solo <code>BASE</code>)</div>
@@NOTA@@
<div class="wrap">@@FILAS@@@@HUER@@</div>
</body></html>"""



def escribir_html(perfiles, opt, par, dec, huerfanos):
    """La vista del ciclo de vida. Declarada en VISTAS/_MANIFIESTO.json como `perfiles`."""
    el = opt.get("elasticidad_cpa_surfing")
    filas = []
    for pk in sorted({p["producto_key"] for p in perfiles}):
        g = [p for p in perfiles if p["producto_key"] == pk]
        vivos = [p for p in g if p["estado"] in ("ESCALANDO", "SOSTENIDO")]
        alerta = ("<div class='alerta'>DEPENDENCIA DE UN SOLO PÚBLICO: %d ángulo(s) vivo(s) "
                  "(mínimo %g). Generar variante: <code>etapa-3</code> ángulo adyacente · "
                  "<code>etapa-9</code> concepto nuevo.</div>" % (len(vivos), opt["min_angulos_vivos"])
                  ) if len(vivos) < opt["min_angulos_vivos"] else ""
        cuerpo = "".join(
            "<tr><td><span class='e' style='background:%s'>%s</span></td><td class='ang'>%s</td>"
            "<td class='n'>%.0f</td><td class='n'>%s</td><td class='n'>%s</td><td class='n'>%s</td>"
            "<td class='n'>%s</td><td class='n'>%.0f%%</td><td class='ev'>%s</td></tr>"
            % (COLOR.get(p["estado"], "#57606a"), p["estado"], p["angulo_key"], p["ventas_acum"],
               ("Q%.1f" % p["cpa_acum_q"]) if p["cpa_acum_q"] else "—",
               ("Q%.1f" % p["cpa_ventana_q"]) if p["cpa_ventana_q"] else "—",
               ("%.0f%%" % (p["p_rentable"] * 100)) if p["p_rentable"] is not None else "—",
               ("%.2f" % p["prioridad_ts"]) if p.get("prioridad_ts") is not None else "—",
               p.get("pct_gasto_producto", 0), p["evidencia"]) for p in g)
        filas.append(
            "<section><h2>%s <small>break-even Q%.2f · %d perfiles</small></h2>%s"
            "<table><thead><tr><th>estado</th><th>ángulo</th><th>ventas</th><th>CPA acum</th>"
            "<th>CPA ventana</th><th>P(rentable)</th><th>P(mejor)</th><th>%% gasto</th>"
            "<th>por qué</th></tr></thead><tbody>%s</tbody></table></section>"
            % (pk, g[0]["be_q"], len(g), alerta, cuerpo))

    huer = ""
    if huerfanos:
        huer = ("<section><h2>Grafías sin dimensión</h2><div class='alerta'>Su gasto compite en el "
                "ranking como un <b>ángulo fantasma</b>. Arreglo: anexar la grafía a "
                "<code>_DIM_CONJUNTOS.csv</code> con el MISMO <code>angulo_key</code>.</div><ul>"
                + "".join("<li><b>%s</b> «%s» — $%.2f · %.0f ventas</li>" % (pk, cj, g_, v)
                          for (pk, cj), (g_, v) in sorted(huerfanos.items(), key=lambda x: -x[1][0]))
                + "</ul></section>")

    nota = ""
    if not isinstance(el, float):
        nota = ("<div class='nota'><b>Este informe rankea, no ordena.</b> "
                "<code>elasticidad_cpa_surfing = " + str(el) + "</code>: nadie midió cuánto "
                "empeora el CPA al subir el presupuesto 20 %, porque <code>_EVENTOS.csv</code> no "
                "tiene un solo <code>CAMBIO_PRESUPUESTO</code>. La orden sigue saliendo de "
                "<code>decidir.py</code> (invariante 13).</div>")

    # Plantilla con marcadores @@…@@: el CSS lleva signos % y no tolera el formateo de Python.
    html = PLANTILLA
    for marca, valor in (
            ("@@VENT@@", "%g" % par["ventana_dias"]),
            ("@@DESDE@@", str(dec.get("datos_desde"))),
            ("@@HASTA@@", str(dec.get("datos_hasta"))),
            ("@@REZ@@", str(dec.get("rezago_dias"))),
            ("@@HOY@@", datetime.date.today().isoformat()),
            ("@@NOTA@@", nota),
            ("@@FILAS@@", "".join(filas)),
            ("@@HUER@@", huer)):
        html = html.replace(marca, valor)
    os.makedirs(os.path.dirname(VISTA), exist_ok=True)
    with io.open(VISTA, "w", encoding="utf-8") as f:
        f.write(html)
    return VISTA


def main():
    ap = argparse.ArgumentParser(description="Perfil de ángulo y su ciclo de vida (VitalCom)")
    ap.add_argument("producto", nargs="?", help="producto_key opcional")
    ap.add_argument("--json", action="store_true", help="emitir JSON por stdout")
    ap.add_argument("--registrar", action="store_true",
                    help="anexar las transiciones a _EVENTOS.csv como TRANSICION_ANGULO")
    ap.add_argument("--silencioso", action="store_true", help="escribir el CSV sin imprimir")
    ap.add_argument("--html", action="store_true", help="además, renderizar VISTAS/PERFILES.html")
    args = ap.parse_args()

    perfiles, opt, par, dec, huerfanos = construir(args.producto)
    escribir(perfiles)
    if args.html:
        escribir_html(perfiles, opt, par, dec, huerfanos)
    n = registrar_transiciones(perfiles) if args.registrar else 0

    if args.json:
        print(json.dumps({"generado": datetime.date.today().isoformat(),
                          "datos_hasta": dec.get("datos_hasta"), "perfiles": perfiles},
                         ensure_ascii=False, indent=2, default=str))
    elif not args.silencioso:
        imprimir(perfiles, opt, par, dec, huerfanos)
        print("escrito %s (%d perfiles)%s"
              % (os.path.relpath(SALIDA, BASE), len(perfiles),
                 " · %d transición(es) registradas" % n if n else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
