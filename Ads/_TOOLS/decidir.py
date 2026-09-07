#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""decidir.py — MOTOR DE DECISIÓN UNIFICADO (VITALCOM GUATEMALA).

SÍNTESIS DOCTRINARIA Y OPERATIVA:
Combina el rigor estadístico de los Intervalos de Credibilidad Bayesiana (IC 95%)
con la Gestión de Riesgo Asimétrico (Bankroll, Tolerancia 1x BE y Detector Temprano de Fatiga).

PRINCIPIOS:
  1. LA VENTANA ES FIJA (_PARAMETROS_DECISION.csv, default 14 días móviles).
     No se corta después de ver el dato para evitar p-hacking.
  2. AGREGACIÓN POR ANGULO_KEY (Invariante 1 y 12): Las réplicas R[N] se SUMAN.
  3. CERO PARÁLISIS OPERATIVA:
     Si el intervalo cruza el Break-Even por escasez de muestra o cercanía al BE,
     el sistema NO se congela en parálisis: emite la acción de menor riesgo
     (MANTENER PRESUPUESTO / SEGUIR MIDIENDO) y calcula cuántas ventas faltan
     para resolver la incertidumbre al CPA observado.
  4. BLOQUEO DE ACCIONES IRREVERSIBLES:
     Las decisiones irreversibles (apagar definitivamente un ángulo o escalar fuerte)
     requieren evidencia rigurosa o transgresión de tolerancia máxima (1x BE sin ventas).
  5. DETECTOR TEMPRANO DE FATIGA:
     Si un ángulo ganador histórico decae en los últimos 3 días, la acción es RENOVAR
     el concepto en Fase 2, nunca apagar el ángulo.

ESTADOS:
  [ESCALAR]         CPA bajo objetivo o bajo BE con respaldo -> Subir +10% a +20%
  [PAUSAR]          Gasto sin chats, tolerancia de 1x BE agotada o CPA desbordado
  [RENOVAR]         Ganador histórico con fatiga en los últimos 3 días (Brief Fase 2)
  [SEGUIR_MIDIENDO] Cruza BE en zona de prueba/maduración (Acción: Mantener presupuesto)

USO:
    python Ads/_TOOLS/decidir.py                      # Portafolio completo
    python Ads/_TOOLS/decidir.py CLEARSTEM            # Un solo producto
    python Ads/_TOOLS/decidir.py --grano conjunto     # Desglose por conjunto
    python Ads/_TOOLS/decidir.py --dias 14            # Ventana personalizada
    python Ads/_TOOLS/decidir.py --json               # Salida JSON
"""

import os
import sys
import io
import csv
import json
import argparse
import datetime
import math

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except (AttributeError, OSError):
    pass

from scipy.stats import gamma as _gamma, fisher_exact

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROD = os.path.join(BASE, "PRODUCTOS")
DB_PATH = os.path.join(BASE, "warehouse", "vitalcom.duckdb")
PARAMS_PATH = os.path.join(PROD, "_PARAMETROS_DECISION.csv")
DIM_PROD_PATH = os.path.join(PROD, "_DIM_PRODUCTOS.csv")
DIM_CONJ_PATH = os.path.join(PROD, "_DIM_CONJUNTOS.csv")
FACT_VENTAS_PATH = os.path.join(PROD, "_FACT_VENTAS.csv")
FACT_ENTREGA_PATH = os.path.join(PROD, "_FACT_ENTREGA.csv")
SALIDA_JSON = os.path.join(PROD, "_DECISIONES.json")
SALIDA_HTML = os.path.join(BASE, "VISTAS", "DECISIONES.html")

TASA_Q_USD_DEFAULT = 7.62


def cargar_parametros():
    p = {
        "ventana_dias": 14,
        "maduracion_dias": 10,
        "nivel_confianza": 0.95,
        "alpha_cierre": 0.05,
        "horizonte_ventas": 60,
        "min_mensajes_cierre": 30,
        "agrega_por": "angulo_key",
        "tasa_usd_gtq": TASA_Q_USD_DEFAULT,
        "umbral_gasto_sin_chat_usd": 5.0,
        "factor_tolerancia_pd": 1.0,
        "factor_cpa_desbordado": 1.4,
    }
    if os.path.exists(PARAMS_PATH):
        try:
            with io.open(PARAMS_PATH, encoding="utf-8-sig") as f:
                for r in csv.DictReader(f):
                    k = r.get("parametro", "").strip()
                    v = r.get("valor", "").strip()
                    if k in p:
                        try:
                            p[k] = float(v) if "." in v else int(v)
                        except ValueError:
                            p[k] = v
        except Exception:
            pass
    return p


def ic_cpa(ventas, gasto_usd, conf=0.95, tasa=TASA_Q_USD_DEFAULT):
    """Intervalo de credibilidad Bayesiano del CPA en Quetzales.

    Ventas ~ Poisson(lambda); posterior Jeffreys lambda|k ~ Gamma(k+0.5, 1);
    CPA = gasto_q / lambda. Devuelve (bajo, punto, alto).
    """
    gq = gasto_usd * tasa
    if ventas <= 0:
        a = (1.0 - conf) / 2.0
        hi_lam = _gamma.ppf(1 - a, 0.5)
        bajo = round(gq / hi_lam, 1) if hi_lam > 0 else 0.0
        return bajo, None, None

    a = (1.0 - conf) / 2.0
    hi_lam = _gamma.ppf(1 - a, ventas + 0.5)
    lo_lam = _gamma.ppf(a, ventas + 0.5)
    bajo = round(gq / hi_lam, 1) if hi_lam > 0 else 0.0
    alto = round(gq / lo_lam, 1) if lo_lam > 0 else None
    punto = round(gq / ventas, 1)
    return bajo, punto, alto


def calcular_ventas_faltantes(ventas, gasto_usd, be_q, conf, horizonte, tasa):
    """Calcula cuántas ventas faltan para que el IC se resuelva bajo el BE al CPA observado."""
    if ventas <= 0 or not be_q:
        return None
    cpa_actual = (gasto_usd * tasa) / ventas
    if cpa_actual >= be_q:
        return None
    for n in range(int(ventas) + 1, horizonte + 1):
        g_proj = (gasto_usd / ventas) * n
        b_n, _, a_n = ic_cpa(n, g_proj, conf, tasa)
        if a_n is not None and a_n < be_q:
            return n - int(ventas)
    return None


def comparar_cierre(a_v, a_m, b_v, b_m, alpha):
    """Fisher exacto entre dos tasas de cierre. Corta, nunca corona."""
    if min(a_m, b_m) <= 0:
        return None
    try:
        _, p = fisher_exact([[int(a_v), int(a_m - a_v)], [int(b_v), int(b_m - b_v)]])
        return {
            "p": round(float(p), 4),
            "significativo": bool(p < alpha),
            "cierre_a": round(a_v / a_m * 100, 1),
            "cierre_b": round(b_v / b_m * 100, 1),
        }
    except Exception:
        return None


def cargar_productos():
    prods = {}
    if not os.path.exists(DIM_PROD_PATH):
        return prods
    with io.open(DIM_PROD_PATH, encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            pk = r.get("producto_key", "").strip()
            if not pk:
                continue

            def _flt(val, default=0.0):
                try:
                    return float(val) if val else default
                except ValueError:
                    return default

            prods[pk] = {
                "producto_key": pk,
                "nombre": r.get("nombre_display", pk),
                "estado": r.get("estado", "DESCONOCIDO"),
                "fase": r.get("fase", ""),
                "cpa_base_q": _flt(r.get("cpa_base_q")),
                "cpa_be_q": _flt(r.get("cpa_be_q")),
                "tasa": _flt(r.get("tasa"), TASA_Q_USD_DEFAULT),
            }
    return prods


def cargar_datos_duckdb(dias=14, grano="angulo"):
    import duckdb

    con = duckdb.connect()

    f_ventas = FACT_VENTAS_PATH.replace("\\", "/")
    f_conj = DIM_CONJ_PATH.replace("\\", "/")

    col_agrup = "coalesce(v.angulo_key, v.conjunto)" if grano == "angulo" else "v.conjunto"

    sql = f"""
    with ventas_raw as (
        select
            try_cast(ventana_fin as date) as fecha,
            trim(producto_key) as producto_key,
            trim(conjunto) as conjunto,
            try_cast(spend_usd as double) as spend_usd,
            try_cast(ventas as integer) as ventas,
            try_cast(mensajes as integer) as mensajes
        from read_csv('{f_ventas}', header=true, all_varchar=true)
        where ventana_fin is not null and ventana_fin != ''
    ),
    ult as (
        select max(fecha) as f from ventas_raw
    ),
    dim_conj as (
        select
            trim(producto_key) as producto_key,
            trim(conjunto_meta) as conjunto_meta,
            max(trim(angulo_key)) as angulo_key
        from read_csv('{f_conj}', header=true, all_varchar=true)
        group by 1, 2
    ),
    unidos as (
        select
            v.fecha,
            v.producto_key,
            v.conjunto,
            coalesce(d.angulo_key, v.conjunto) as angulo_key,
            v.ventas,
            v.mensajes,
            v.spend_usd
        from ventas_raw v
        left join dim_conj d
          on d.producto_key = v.producto_key and d.conjunto_meta = v.conjunto
        where v.fecha > (select f from ult) - interval ({dias} - 1) day
    )
    select
        producto_key,
        {col_agrup} as celda,
        count(distinct conjunto) as conjuntos,
        sum(ventas) as ventas,
        sum(mensajes) as mensajes,
        sum(spend_usd) as spend_usd,
        sum(case when fecha > (select f from ult) - interval 3 day then ventas else 0 end) as ventas_3d,
        sum(case when fecha > (select f from ult) - interval 3 day then mensajes else 0 end) as mensajes_3d,
        sum(case when fecha > (select f from ult) - interval 3 day then spend_usd else 0 end) as spend_3d,
        min(fecha) as desde,
        max(fecha) as hasta,
        true as banda_ok,
        true as nombres_ok
    from unidos v
    group by 1, 2
    having sum(spend_usd) > 0
    order by 1, 4 desc
    """
    df = con.execute(sql).fetchdf()
    con.close()
    return df


def evaluar_celda(ventas, mensajes, spend_usd, ventas_3d, mensajes_3d, spend_3d,
                  be_q, obj_q, tasa, params):
    """Evalúa una celda combinando Intervalos de Credibilidad con Reglas Operativas."""
    gasto_q = spend_usd * tasa
    gasto_3d_q = spend_3d * tasa
    cpa_real_q = (gasto_q / ventas) if ventas > 0 else None
    cierre_pct = (ventas / mensajes * 100.0) if mensajes > 0 else None

    # Intervalo de credibilidad Bayesiano
    conf = float(params.get("nivel_confianza", 0.95))
    horizonte = int(params.get("horizonte_ventas", 60))
    bajo_ic, punto_ic, alto_ic = ic_cpa(ventas, spend_usd, conf, tasa)
    ic_res = [bajo_ic, punto_ic, alto_ic]

    # PD = Presupuesto de Decisión (1x Break-Even de tolerancia para testeo)
    pd_q = be_q * params.get("factor_tolerancia_pd", 1.0)
    pct_pd_consumido = (gasto_q / pd_q * 100.0) if pd_q > 0 else 0.0

    # 1. REGLA: HOOK MUERTO / ENLACE CAÍDO
    if spend_usd >= params["umbral_gasto_sin_chat_usd"] and mensajes == 0:
        return {
            "estado": "PAUSAR",
            "accion_codigo": "PAUSAR_HOOK_MUERTO",
            "accion_sugerida": f"APAGAR INMEDIATO: Gastó ${spend_usd:.2f} sin un solo chat. Hook sin atracción o WhatsApp caído.",
            "cpa_real_q": None,
            "cierre_pct": 0.0,
            "pct_pd": round(pct_pd_consumido, 1),
            "ic": ic_res,
            "faltan_ventas": None,
            "nivel_prioridad": 1,
        }

    # 2. REGLA: TOLERANCIA DE DECISIÓN AGOTADA (0 ventas tras 1x BE)
    if ventas == 0 and gasto_q >= pd_q:
        return {
            "estado": "PAUSAR",
            "accion_codigo": "PAUSAR_TOLERANCIA_AGOTADA",
            "accion_sugerida": f"APAGAR: Gastó Q{gasto_q:.1f} (100% de tolerancia BE Q{be_q:.1f}) sin ventas. Cortar pérdida.",
            "cpa_real_q": None,
            "cierre_pct": 0.0,
            "pct_pd": round(pct_pd_consumido, 1),
            "ic": ic_res,
            "faltan_ventas": None,
            "nivel_prioridad": 1,
        }

    # 3. REGLA: CPA DESBORDADO (Destrucción de margen confirmada)
    umbral_desborde = be_q * params.get("factor_cpa_desbordado", 1.4)
    if (ventas >= 2 and cpa_real_q and cpa_real_q > umbral_desborde) or (bajo_ic and bajo_ic > be_q):
        return {
            "estado": "PAUSAR",
            "accion_codigo": "PAUSAR_CPA_DESBORDADO",
            "accion_sugerida": f"APAGAR: CPA Q{cpa_real_q:.1f} desbordado sobre BE Q{be_q:.1f} (IC mín Q{bajo_ic:.0f}). Margen destruido.",
            "cpa_real_q": round(cpa_real_q, 1),
            "cierre_pct": round(cierre_pct, 1) if cierre_pct else None,
            "pct_pd": round(pct_pd_consumido, 1),
            "ic": ic_res,
            "faltan_ventas": None,
            "nivel_prioridad": 2,
        }

    # 4. REGLA: DETECTOR TEMPRANO DE FATIGA (Últimos 3 días)
    if ventas >= 5 and gasto_3d_q >= (0.6 * be_q):
        cpa_3d = (gasto_3d_q / ventas_3d) if ventas_3d > 0 else None
        if ventas_3d == 0 or (cpa_3d and cpa_3d > 1.3 * be_q):
            return {
                "estado": "RENOVAR",
                "accion_codigo": "FATIGA_CREATIVO",
                "accion_sugerida": f"RENOVAR CREATIVO (FASE 2): Ganador histórico ({ventas:.0f} vts) pero últimos 3d sangra (Q{gasto_3d_q:.0f} con {ventas_3d:.0f} vts). Mantener ángulo y rotar concepto.",
                "cpa_real_q": round(cpa_real_q, 1) if cpa_real_q else None,
                "cierre_pct": round(cierre_pct, 1) if cierre_pct else None,
                "pct_pd": round(pct_pd_consumido, 1),
                "ic": ic_res,
                "faltan_ventas": None,
                "nivel_prioridad": 3,
            }

    # 5. REGLA: ESCALAR SURFING (Ganador sólido con CPA <= Objetivo)
    if ventas >= 2 and cpa_real_q and cpa_real_q <= obj_q:
        return {
            "estado": "ESCALAR",
            "accion_codigo": "ESCALAR_SURFING",
            "accion_sugerida": f"SUBIR PRESUPUESTO +20%: CPA excelente Q{cpa_real_q:.1f} (Obj Q{obj_q:.1f}, IC [{bajo_ic:.0f}-{alto_ic if alto_ic else 'inf'}]). Ganador claro.",
            "cpa_real_q": round(cpa_real_q, 1),
            "cierre_pct": round(cierre_pct, 1) if cierre_pct else None,
            "pct_pd": round(pct_pd_consumido, 1),
            "ic": ic_res,
            "faltan_ventas": None,
            "nivel_prioridad": 4,
        }

    # 6. REGLA: ESCALA LEVE / MANTENER (Rentable bajo Break-Even)
    if ventas >= 2 and cpa_real_q and (obj_q < cpa_real_q <= be_q):
        return {
            "estado": "ESCALAR",
            "accion_codigo": "ESCALAR_MODERADO",
            "accion_sugerida": f"MANTENER / ESCALA LEVE (+10%): CPA rentable Q{cpa_real_q:.1f} bajo BE Q{be_q:.1f} (IC [{bajo_ic:.0f}-{alto_ic if alto_ic else 'inf'}]).",
            "cpa_real_q": round(cpa_real_q, 1),
            "cierre_pct": round(cierre_pct, 1) if cierre_pct else None,
            "pct_pd": round(pct_pd_consumido, 1),
            "ic": ic_res,
            "faltan_ventas": None,
            "nivel_prioridad": 3,
        }

    # 7. REGLA: TESTEO ACTIVO / SEGUIR MIDIENDO (El IC cruza BE pero está en tolerancia)
    faltan = calcular_ventas_faltantes(ventas, spend_usd, be_q, conf, horizonte, tasa)
    if ventas == 0:
        disponible_q = pd_q - gasto_q
        return {
            "estado": "SEGUIR_MIDIENDO",
            "accion_codigo": "TESTEO_EN_TOLERANCIA",
            "accion_sugerida": f"MANTENER / MEDIR: Gastó Q{gasto_q:.1f} de Q{pd_q:.1f} ({pct_pd_consumido:.0f}% PD). Margen disponible: Q{disponible_q:.1f}.",
            "cpa_real_q": None,
            "cierre_pct": 0.0,
            "pct_pd": round(pct_pd_consumido, 1),
            "ic": ic_res,
            "faltan_ventas": None,
            "nivel_prioridad": 2,
        }

    if ventas == 1:
        txt_faltan = f" Faltan ~{faltan} ventas para resolver IC." if faltan else ""
        return {
            "estado": "SEGUIR_MIDIENDO",
            "accion_codigo": "TESTEO_PRIMERA_VENTA",
            "accion_sugerida": f"MANTENER / MEDIR: 1 venta a CPA Q{cpa_real_q:.1f} (IC [{bajo_ic:.0f}-{alto_ic if alto_ic else 'inf'}]).{txt_faltan} Mantener presupuesto.",
            "cpa_real_q": round(cpa_real_q, 1),
            "cierre_pct": round(cierre_pct, 1) if cierre_pct else None,
            "pct_pd": round(pct_pd_consumido, 1),
            "ic": ic_res,
            "faltan_ventas": faltan,
            "nivel_prioridad": 2,
        }

    # Muestra moderada cruzando BE: acción conservadora de bajo riesgo
    txt_f = f" Faltan ~{faltan} ventas al CPA actual para resolver IC." if faltan else " El CPA observado está cerca del BE."
    return {
        "estado": "SEGUIR_MIDIENDO",
        "accion_codigo": "MANTENER_Y_MEDIR",
        "accion_sugerida": f"MANTENER PRESUPUESTO: IC [{bajo_ic:.0f} - {alto_ic if alto_ic else 'inf'}] cruza BE Q{be_q:.1f}.{txt_f}",
        "cpa_real_q": round(cpa_real_q, 1) if cpa_real_q else None,
        "cierre_pct": round(cierre_pct, 1) if cierre_pct else None,
        "pct_pd": round(pct_pd_consumido, 1),
        "ic": ic_res,
        "faltan_ventas": faltan,
        "nivel_prioridad": 2,
    }


def analizar_portafolio(producto_filtro=None, grano="angulo", dias=None):
    params = cargar_parametros()
    if dias:
        params["ventana_dias"] = dias
    dias_v = int(params["ventana_dias"])

    prods = cargar_productos()
    df_celdas = cargar_datos_duckdb(dias=dias_v, grano=grano)

    resultado = {
        "generado": datetime.date.today().isoformat(),
        "motor": "decidir v3 (Síntesis: Intervalos de Credibilidad Bayesiana + Riesgo Asimétrico)",
        "grano": grano,
        "ventana_dias": dias_v,
        "nivel_confianza": float(params.get("nivel_confianza", 0.95)),
        "resumen_acciones": {
            "PAUSAR": 0,
            "RENOVAR": 0,
            "ESCALAR": 0,
            "SEGUIR_MIDIENDO": 0,
        },
        "productos": [],
    }

    if df_celdas.empty:
        return resultado

    if producto_filtro:
        df_celdas = df_celdas[df_celdas["producto_key"] == producto_filtro]

    for pk, g in df_celdas.groupby("producto_key"):
        info = prods.get(pk, {})
        be_q = info.get("cpa_be_q", 90.0)
        obj_q = info.get("cpa_base_q", 30.0)
        tasa = info.get("tasa", TASA_Q_USD_DEFAULT)
        estado_prod = info.get("estado", "DESCONOCIDO")

        celdas_eval = []
        for r in g.itertuples():
            eval_res = evaluar_celda(
                ventas=float(r.ventas),
                mensajes=float(r.mensajes),
                spend_usd=float(r.spend_usd),
                ventas_3d=float(r.ventas_3d),
                mensajes_3d=float(r.mensajes_3d),
                spend_3d=float(r.spend_3d),
                be_q=be_q,
                obj_q=obj_q,
                tasa=tasa,
                params=params,
            )
            eval_res.update({
                "celda": str(r.celda),
                "conjuntos": int(r.conjuntos),
                "ventas": float(r.ventas),
                "mensajes": float(r.mensajes),
                "spend_usd": round(float(r.spend_usd), 2),
                "spend_q": round(float(r.spend_usd) * tasa, 1),
                "banda_ok": bool(r.banda_ok),
                "nombres_ok": bool(r.nombres_ok),
            })
            celdas_eval.append(eval_res)
            estado_cat = eval_res["estado"]
            resultado["resumen_acciones"][estado_cat] = resultado["resumen_acciones"].get(estado_cat, 0) + 1

        # Comparación de cierre (Fisher) si aplica
        min_msj = int(params.get("min_mensajes_cierre", 30))
        alpha = float(params.get("alpha_cierre", 0.05))
        elegibles = [f for f in celdas_eval if f["mensajes"] >= min_msj]
        mejor = max(elegibles, key=lambda f: f["cierre_pct"] or 0, default=None)
        if mejor:
            for f in celdas_eval:
                if f is not mejor and f["mensajes"] >= min_msj:
                    cf = comparar_cierre(f["ventas"], f["mensajes"], mejor["ventas"], mejor["mensajes"], alpha)
                    if cf and cf["significativo"]:
                        f["cierre_vs_mejor"] = dict(cf, contra=mejor["celda"])

        # Ordenar: PAUSAR -> RENOVAR -> ESCALAR -> SEGUIR_MIDIENDO
        orden_prio = {"PAUSAR": 0, "RENOVAR": 1, "ESCALAR": 2, "SEGUIR_MIDIENDO": 3}
        celdas_eval.sort(key=lambda x: (orden_prio.get(x["estado"], 9), -x["spend_q"]))

        resultado["productos"].append({
            "producto_key": pk,
            "nombre": info.get("nombre", pk),
            "estado_producto": estado_prod,
            "cpa_objetivo_q": obj_q,
            "break_even_q": be_q,
            "celdas": celdas_eval,
        })

    return resultado


def imprimir_consola(res):
    print("=" * 115)
    print(f" MOTOR DE DECISIÓN UNIFICADO — VITALCOM GUATEMALA (Ventana: {res['ventana_dias']} días | IC 95% | Grano: {res['grano']})")
    print(f" Resumen:  🔴 PAUSAR: {res['resumen_acciones'].get('PAUSAR', 0)}  |  "
          f"🔵 RENOVAR (FATIGA): {res['resumen_acciones'].get('RENOVAR', 0)}  |  "
          f"🟢 ESCALAR: {res['resumen_acciones'].get('ESCALAR', 0)}  |  "
          f"🟡 SEGUIR MIDIENDO: {res['resumen_acciones'].get('SEGUIR_MIDIENDO', 0)}")
    print("=" * 115)

    for p in res["productos"]:
        print(f"\n[{p['producto_key']}]  Estado: {p['estado_producto']} | Break-Even: Q{p['break_even_q']:.2f} | CPA Objetivo: Q{p['cpa_objetivo_q']:.2f}")
        print("-" * 115)
        print(f"  {'ESTADO':<16} {'CELDA / ÁNGULO':<28} {'VTS':>4} {'MSJ':>5} {'GASTO Q':>8} {'CPA REAL':>8} {'IC 95% Q':<15} ACCIÓN INMEDIATA")
        print("-" * 115)

        for c in p["celdas"]:
            est = f"[{c['estado']}]"
            cpa_str = f"Q{c['cpa_real_q']:.1f}" if c['cpa_real_q'] else "-"
            ic = c.get("ic", [0, 0, 0])
            ic_str = f"[{ic[0]:.0f}-{ic[2]:.0f}]" if (ic and ic[2]) else f"[≥{ic[0]:.0f}]" if ic else "-"
            print(f"  {est:<16} {c['celda'][:26]:<28} {c['ventas']:>4.0f} {c['mensajes']:>5.0f} {c['spend_q']:>8.1f} {cpa_str:>8} {ic_str:<15} {c['accion_sugerida']}")

    print("\n" + "=" * 115)
    print(" SÍNTESIS COMPLETA: Cero parálisis por falta de muestra · Cero decisiones irreversibles sin evidencia.")
    print("=" * 115)


def main():
    ap = argparse.ArgumentParser(description="Motor de Decisión Unificado (VitalCom)")
    ap.add_argument("producto", nargs="?", help="producto_key opcional")
    ap.add_argument("--grano", choices=["angulo", "conjunto"], default="angulo", help="Agrupación (angulo por defecto)")
    ap.add_argument("--dias", type=int, default=None, help="Días de ventana móvil")
    ap.add_argument("--json", action="store_true", help="Emitir solo JSON por stdout")
    args = ap.parse_args()

    res = analizar_portafolio(producto_filtro=args.producto, grano=args.grano, dias=args.dias)

    with io.open(SALIDA_JSON, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=2)

    if args.json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        imprimir_consola(res)

    return 0


if __name__ == "__main__":
    sys.exit(main())
