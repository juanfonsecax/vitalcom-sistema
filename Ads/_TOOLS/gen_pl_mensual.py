# -*- coding: utf-8 -*-
"""gen_pl_mensual.py — estado de resultados MES A MES de un mercado. Implementa DOCTRINA/CONTABILIDAD.md.

  python Ads/_TOOLS/gen_pl_mensual.py --mercado GT [--desde YYYY-MM] [--hasta YYYY-MM] [--json]

SOLO LEE (DOCTRINA/DATA_PLAYBOOK.md §7): no escribe nada. Sale de los hechos persistidos —
`_FACT_ORDENES_DROPI.csv` (Dropi), `_FACT_CARTERA_DROPI.csv` (la billetera de Dropi),
`_FACT_BANCO.csv` (banco), el gasto de Meta (`gasto.py` sobre `_FACT_ENTREGA.csv`), `_DIM_GASTOS.csv`
y `_DIM_RETIROS.csv` — con LA MISMA fórmula que `gen_pl.py`
(`gen_pl.calcular_vista_a`): este archivo solo arma las ventanas de cada mes, no recalcula nada.

Los meses son los que aparecen en cualquiera de los hechos. Cada mes trae el estado de resultados
completo (§3), la pauta partida por fuente (Meta / LucidSales donde Meta no cubre), lo que el
banco cobró de Facebook, los gastos fijos con su detalle, los retiros personales APARTE (nunca
entran al resultado), el desglose por producto, la bandera PRELIMINAR (cohorte con menos de
`dias_cohorte_maduro` días, §1) y `faltantes`: lo que no se pudo medir y qué falta cargar. Un mes
sin órdenes de Dropi no inventa ceros: sus líneas de venta quedan en null.

La cartera de Dropi aporta tres cosas, todas bajo la clave `cartera` de cada mes:
  - el costo REAL de cada devolución (el cobro de la billetera), solo en los meses que la cartera
    cubre desde su primer día; los demás usan el promedio del parámetro y lo dicen
    (`cartera.devoluciones.origen`: REAL / MIXTO / ESTIMADO);
  - los retiros de la billetera, clasificados por su concepto con `_DIM_RETIROS.csv`: retiros
    personales, transferencias a cuenta propia y SIN CLASIFICAR (listados, nunca adivinados). Son
    movimientos de caja: NO tocan el resultado, igual que los retiros personales del banco, que
    siguen aparte en `retiros_personales`;
  - el saldo de la billetera al cierre del mes (o al último movimiento si el mes sigue en curso).

Los cargos del banco se cortan por la FECHA del movimiento (mes calendario), no por el período del
extracto: el extracto de agosto trae cargos del 1-sep. Los montos del banco se leen en dólares (la
moneda de la cuenta Relay).

Mercados: GT es el único con Dropi y banco hoy; CO sale vacío con su nota en `faltantes`.
"""
import argparse
import calendar
import datetime
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import csv_hechos  # noqa: E402
import gasto       # noqa: E402
import gen_pl      # noqa: E402
import mercado     # noqa: E402

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

FACT_ORDENES = os.path.join(gen_pl.P, "_FACT_ORDENES_DROPI.csv")
FACT_BANCO = os.path.join(gen_pl.P, "_FACT_BANCO.csv")
FACT_CARTERA = os.path.join(gen_pl.P, "_FACT_CARTERA_DROPI.csv")


def cargar_hechos():
    return {"ordenes": csv_hechos.leer(FACT_ORDENES), "banco": csv_hechos.leer(FACT_BANCO),
            "cartera": csv_hechos.leer(FACT_CARTERA),
            "gasto": gasto.gasto_por_conjunto_ventana(), "reglas": gen_pl.load("_DIM_GASTOS.csv"),
            "reglas_retiros": gen_pl.load("_DIM_RETIROS.csv")}


def df_de_ordenes(filas):
    """Las órdenes persistidas como el DataFrame que `gen_pl.leer_dropi` arma del export."""
    import pandas as pd
    df = pd.DataFrame({
        "ID": [int(f["orden_id"]) for f in filas],
        "ESTATUS": [f["estatus"] for f in filas],
        "TOTAL DE LA ORDEN": [gen_pl.fl(f["total_q"]) for f in filas],
        "PRECIO FLETE": [gen_pl.fl(f["flete_q"]) for f in filas],
        "PRECIO PROVEEDOR X CANTIDAD": [gen_pl.fl(f["costo_proveedor_q"]) for f in filas],
        "GANANCIA": [gen_pl.fl(f["ganancia_q"], float("nan")) for f in filas],
        "pk": [f["producto_key"] for f in filas],
        "f_orden": pd.to_datetime([f["fecha_orden"] for f in filas], errors="coerce"),
        "f_mov": pd.to_datetime([f["fecha_movimiento"] or None for f in filas], errors="coerce"),
    })
    return df


def df_de_cartera(filas):
    """La cartera persistida como el DataFrame que `gen_pl.leer_cartera` arma del export."""
    import pandas as pd
    return pd.DataFrame({
        "cat": [f["categoria"] for f in filas],
        "ORDEN ID": [gen_pl.fl(f["orden_id"], float("nan")) for f in filas],
        "MONTO": [gen_pl.fl(f["monto_q"]) for f in filas],
        "f": pd.to_datetime([f["fecha"] for f in filas], errors="coerce"),
    })


def _cartera_del_mes(ini, fin, cartera, reglas_retiros, cartera_desde):
    """Lo que la billetera de Dropi dice de un mes: retiros clasificados y saldo de cierre.
    Los rubros son null cuando la cartera guardada no llega a ese mes (no se sabe, no es un cero)."""
    con_datos = bool(cartera) and fin >= cartera_desde
    del_mes = sorted((c for c in cartera if ini <= c["fecha"] <= fin), key=lambda c: int(c["mov_id"]))
    retiros = [{"fecha": c["fecha"], "hora": c["hora"], "concepto": c["concepto_retiro"],
                "monto_q": gen_pl.fl(c["monto_q"]),
                "clasificacion": gen_pl.clasificar_retiro(c["concepto_retiro"], reglas_retiros)}
               for c in del_mes if c["categoria"] == "RETIRO"]

    def total(clase):
        return sum(r["monto_q"] for r in retiros if r["clasificacion"] == clase) if con_datos else None

    hasta_fin = [c for c in cartera if c["fecha"] <= fin]
    ultimo = max(hasta_fin, key=lambda c: int(c["mov_id"])) if con_datos and hasta_fin else None
    return {"cubre_mes": bool(cartera) and cartera_desde <= ini,
            "saldo_cierre_q": gen_pl.fl(ultimo["saldo_despues_q"]) if ultimo else None,
            "fecha_corte": ultimo["fecha"] if ultimo else None,
            "retiros_personales_q": total("RETIRO_PERSONAL"),
            "transferencias_propias_q": total("TRANSFERENCIA_PROPIA"),
            "sin_clasificar_q": total("SIN_CLASIFICAR"),
            "retiros": retiros}


def _origen_devoluciones(r, cartera_usada, cartera):
    """De dónde sale el costo de las devoluciones del mes: cobros REALES de la billetera o el
    promedio del parámetro. REAL = todas cobradas; MIXTO = parte cobradas; ESTIMADO = ninguna."""
    if r is None:
        return {"origen": None, "reales": 0, "estimadas": 0}
    ids = {int(i) for i in r.dev["ID"]}
    cobradas = set()
    if cartera_usada:
        cobradas = {int(float(c["orden_id"])) for c in cartera
                    if c["categoria"] == "COBRO_DEVOLUCION" and c["orden_id"]} & ids
    reales, estimadas = len(cobradas), len(ids) - len(cobradas)
    if not ids:
        origen = None
    elif not reales:
        origen = "ESTIMADO"
    elif not estimadas:
        origen = "REAL"
    else:
        origen = "MIXTO"
    return {"origen": origen, "reales": reales, "estimadas": estimadas}


def movimientos_del_banco(filas):
    return [{"nombre": f["nombre"], "fecha": datetime.date.fromisoformat(f["fecha"]),
             "monto": gen_pl.fl(f["monto"]), "tipo": f.get("tipo") or "SALIDA"} for f in filas]


def _ultimo_dia(mes):
    a, m = int(mes[:4]), int(mes[5:7])
    return "%s-%02d" % (mes, calendar.monthrange(a, m)[1])


def _meses_de_los_hechos(mercado_pl, ordenes, banco, filas_gasto, cartera=()):
    meses = set()
    meses |= {o["fecha_orden"][:7] for o in ordenes if o.get("fecha_orden")}
    meses |= {b["fecha"][:7] for b in banco if b.get("fecha")}
    meses |= {c["fecha"][:7] for c in cartera if c.get("fecha")}
    for g in filas_gasto:
        if gen_pl.fl(g["spend_usd"]) > 0 and gen_pl._mercado_de(g["producto_key"]) == mercado_pl:
            meses.add(g["ventana_ini"][:7])
    return sorted(meses)


def _detalle_q(detalle):
    return [{"nombre": d["nombre"], "monto_usd": d["monto_usd"],
             "monto_q": d["monto_usd"] * gen_pl.TASA_Q, "categoria": d["categoria"],
             "mercado": d["mercado"], "parte": d["parte"]} for d in detalle]


def _mes(mes, hoy, df_ord, ordenes_mercado, ordenes_todas, mov, reglas, filas_gasto,
         cartera=(), reglas_retiros=()):
    ini, fin = mes + "-01", _ultimo_dia(mes)
    faltantes = []
    pauta = gen_pl.pauta_de_la_ventana(ini, fin, filas_gasto)
    activos = gen_pl.mercados_activos(ini, fin, filas_gasto, ordenes_todas)
    mov_mes = [t for t in mov if ini <= str(t["fecha"]) <= fin]
    tiene_banco = bool(mov_mes)
    ord_mes = [o for o in ordenes_mercado if ini <= o["fecha_orden"] <= fin]
    ultimo_con_ordenes = max((o["fecha_orden"] for o in ord_mes), default=None)
    cartera = list(cartera)
    cartera_desde = min((c["fecha"] for c in cartera), default=None)
    cartera_cubre = bool(cartera) and cartera_desde <= ini
    df_car = df_de_cartera(cartera) if cartera_cubre else None

    # Un mes aún en curso no tiene cargadas las órdenes que faltan: su cohorte tiene edad 0.
    r = None
    if ord_mes:
        r = gen_pl.calcular_vista_a(df_ord, ini, fin, hoy, pauta, mov=mov, reglas=reglas,
                                    activos=activos | {gen_pl.MERCADO_PL}, car=df_car,
                                    fin_edad=hoy.isoformat() if fin >= hoy.isoformat()
                                    else ultimo_con_ordenes)
        banco = r
        fijos, retiros, det_fijos, det_retiros = r.fijos, r.retiros, r.det_fijos, r.det_retiros
        sin_conf, sin_repartir = r.sin_confirmar, r.sin_repartir
        fb_usd, fb_cargos = r.pauta_banco_usd, r.pauta_banco_cargos
    else:
        b = gen_pl.gastos_del_banco(mov, reglas, ini, fin, activos)
        fijos, retiros, det_fijos, det_retiros = b.fijos, b.retiros, b.det_fijos, b.det_retiros
        sin_conf, sin_repartir = b.sin_confirmar, b.sin_repartir
        fb_usd, fb_cargos = b.pauta_usd, b.pauta_cargos
        faltantes.append("Sin órdenes de Dropi en %s: cargá el export de Dropi que cubra el mes "
                         "(ingerir_dropi.py)." % mes)

    if r is not None:
        primero = min(o["fecha_orden"] for o in ordenes_mercado)
        if ini < primero <= fin:
            faltantes.append("Las órdenes de Dropi guardadas empiezan el %s: faltan los días "
                             "anteriores del mes." % primero)
        ok_cuadre, calc, gan = gen_pl.cuadre_dropi(df_ord[(df_ord.f_orden >= ini) & (df_ord.f_orden <= fin)])
        if not ok_cuadre:
            faltantes.append("El cuadre de Dropi no da en %s: venta−producto−flete = Q%.2f y la "
                             "columna GANANCIA suma Q%.2f. El export cambió de formato."
                             % (mes, calc, gan))
    if fin > hoy.isoformat():
        faltantes.append("Mes en curso (datos hasta el %s): el resultado todavía puede cambiar."
                         % min(fin, hoy.isoformat()))
    info_cartera = _cartera_del_mes(ini, fin, cartera, reglas_retiros, cartera_desde)
    info_cartera["devoluciones"] = _origen_devoluciones(r, cartera_cubre, cartera)
    if not cartera:
        faltantes.append("Sin historial de cartera de Dropi: el costo de las devoluciones es el "
                         "promedio del parámetro y no hay retiros ni saldo de la billetera "
                         "(ingerir_cartera.py).")
    elif fin < cartera_desde:
        faltantes.append("Sin historial de cartera de Dropi en %s (la cartera guardada empieza el "
                         "%s): el costo de las devoluciones es el promedio del parámetro y no hay "
                         "retiros ni saldo de la billetera." % (mes, cartera_desde))
    elif cartera_desde > ini:
        faltantes.append("La cartera de Dropi guardada empieza el %s: faltan los movimientos "
                         "anteriores del mes; el costo de las devoluciones es el promedio del "
                         "parámetro." % cartera_desde)
    sin_clas = [x for x in info_cartera["retiros"] if x["clasificacion"] == "SIN_CLASIFICAR"]
    if sin_clas:
        faltantes.append("Retiros de la cartera sin clasificar (Q%.2f en %d: %s): no entran a "
                         "ninguna línea hasta que el operador confirme qué son (_DIM_RETIROS.csv)."
                         % (sum(x["monto_q"] for x in sin_clas), len(sin_clas),
                            "; ".join("%s «%s»" % (x["fecha"], x["concepto"]) for x in sin_clas)))
    if not tiene_banco:
        faltantes.append("Sin movimientos del banco en %s: cargá el extracto bancario "
                         "(ingerir_banco.py)." % mes)
    if not pauta["usd"]:
        faltantes.append("Sin pauta registrada en %s (ni de Meta ni de LucidSales)." % mes)
    if pauta["fallback_usd"]:
        faltantes.append("$%.2f de la pauta salen de LucidSales porque Meta no tiene cobertura "
                         "esos días." % pauta["fallback_usd"])
    if sin_conf:
        faltantes.append("Cargos del banco sin clasificar ($%.2f en %d): no entran a ninguna línea "
                         "hasta que el operador confirme qué son (_DIM_GASTOS.csv)."
                         % (sum(v for _, v in sin_conf), len(sin_conf)))
    if sin_repartir:
        faltantes.append("Gastos compartidos sin repartir (%s): ningún mercado tuvo actividad "
                         "en %s." % (", ".join(sorted(set(sin_repartir))), mes))

    base = {
        "mes": mes, "desde": ini, "hasta": fin,
        "publicidad": {"usd": pauta["usd"], "q": pauta["q"], "meta_usd": pauta["meta_usd"],
                       "lucidsales_fallback_usd": pauta["fallback_usd"],
                       "tasa": pauta["q"] / pauta["usd"] if pauta["usd"] else gen_pl.TASA_Q},
        "banco_facebook": {"usd": fb_usd if tiene_banco else None,
                           "cargos": fb_cargos if tiene_banco else None},
        # sin extracto del mes no se sabe cuánto fue: null, no un cero (el resultado igual los toma como 0)
        "gastos_fijos": {"q": fijos if tiene_banco else None, "detalle": _detalle_q(det_fijos)},
        "retiros_personales": {"q": retiros if tiene_banco else None, "detalle": _detalle_q(det_retiros)},
        "cargos_sin_clasificar": [{"nombre": n, "monto_usd": v} for n, v in sin_conf],
        # movimientos de caja de la billetera de Dropi: no afectan la ganancia
        "cartera": info_cartera,
    }
    if r is None:
        base.update({
            "preliminar": None, "edad_dias": None,
            "dias_maduro_umbral": gen_pl.DIAS_MADURO,
            "ordenes": {"total": 0, "entregadas": 0, "devueltas": 0, "en_transito": 0,
                        "pct_resuelto": None},
            "venta_entregada_q": None, "costo_producto_q": None, "flete_q": None,
            "margen_logistico_q": None, "devoluciones_q": None, "personal_q": None,
            "otros_q": None, "costos_operativos_q": None, "margen_contribucion_q": None,
            "margen_operativo_q": None,
            "resultado_neto_q": None,
            "por_producto": [{"producto_key": pk, "ordenes": 0, "entregadas": 0, "devueltas": 0,
                              "en_transito": 0, "venta_entregada_q": None,
                              "margen_antes_publicidad_q": None, "pauta_q": q_,
                              "ganancia_q": None}
                             for pk, q_ in sorted(pauta["q_por_producto"].items())],
        })
    else:
        base.update({
            "preliminar": not r.maduro, "edad_dias": r.edad,
            "dias_maduro_umbral": gen_pl.DIAS_MADURO,
            "ordenes": {"total": len(r.m), "entregadas": len(r.ent), "devueltas": len(r.dev),
                        "en_transito": len(r.tra), "pct_resuelto": r.pct_res},
            "venta_entregada_q": r.venta, "costo_producto_q": r.costo, "flete_q": r.flete,
            "margen_logistico_q": r.m_log, "devoluciones_q": r.c_dev, "personal_q": r.c_adm,
            "otros_q": r.c_otr,
            # todo lo que se resta entre la venta y el margen de contribución (para graficar un solo bloque)
            "costos_operativos_q": r.costo + r.flete + r.c_dev + r.c_adm + r.c_otr,
            "margen_contribucion_q": r.m_contr,
            "margen_operativo_q": r.m_oper, "resultado_neto_q": r.neto,
            "por_producto": r.por_producto,
        })
    base["faltantes"] = faltantes
    return base


def pl_mensual(mercado_pl, desde=None, hasta=None, hoy=None, hechos=None):
    """El estado de resultados de cada mes de `mercado_pl` (dict listo para serializar)."""
    hoy = hoy or datetime.date.today()
    perfil = mercado.perfil_mercado(mercado_pl, gen_pl.ROOT)
    out = {"mercado": mercado_pl, "moneda": perfil["moneda"], "generado": hoy.isoformat(),
           "meses": [], "faltantes": [], "cobertura": {}}
    if mercado_pl != gen_pl.MERCADO_PL:
        out["faltantes"].append(
            "%s: sin datos todavía. Hoy solo %s tiene órdenes de Dropi y extracto bancario "
            "cargados; el mercado %s se contabiliza aparte (DOCTRINA/CONTABILIDAD.md §3-bis)."
            % (perfil["pais"] or mercado_pl, gen_pl.MERCADO_PL, mercado_pl))
        return out
    h = hechos if hechos is not None else cargar_hechos()
    ordenes_mercado = sorted((o for o in h["ordenes"] if o.get("mercado") == mercado_pl),
                             key=lambda o: o["fecha_orden"])
    cartera = sorted((c for c in h.get("cartera", []) if (c.get("mercado") or mercado_pl) == mercado_pl),
                     key=lambda c: int(c["mov_id"]))
    reglas_retiros = h.get("reglas_retiros", [])
    mov = movimientos_del_banco(h["banco"])
    df_ord = df_de_ordenes(ordenes_mercado) if ordenes_mercado else None
    meses = _meses_de_los_hechos(mercado_pl, ordenes_mercado, h["banco"], h["gasto"], cartera)
    meses = [m for m in meses if (not desde or m >= desde) and (not hasta or m <= hasta)]
    for mes in meses:
        out["meses"].append(_mes(mes, hoy, df_ord, ordenes_mercado, h["ordenes"], mov,
                                 h["reglas"], h["gasto"], cartera, reglas_retiros))
    if not meses:
        out["faltantes"].append("Todavía no hay órdenes de Dropi, movimientos del banco ni pauta "
                                "cargados para %s." % mercado_pl)
    if ordenes_mercado:
        out["cobertura"]["dropi"] = {"desde": ordenes_mercado[0]["fecha_orden"],
                                     "hasta": ordenes_mercado[-1]["fecha_orden"],
                                     "ordenes": len(ordenes_mercado)}
    if cartera:
        out["cobertura"]["cartera"] = {"desde": min(c["fecha"] for c in cartera),
                                       "hasta": max(c["fecha"] for c in cartera),
                                       "movimientos": len(cartera)}
    if h["banco"]:
        fechas = sorted(b["fecha"] for b in h["banco"])
        out["cobertura"]["banco"] = {"desde": fechas[0], "hasta": fechas[-1],
                                     "movimientos": len(fechas)}
    return out


def _q(v):
    return "—" if v is None else "Q{:>10,.0f}".format(v)


def texto(r):
    L = ["ESTADO DE RESULTADOS MENSUAL — mercado %s (%s)" % (r["mercado"], r["moneda"])]
    for x in r["faltantes"]:
        L.append("  ⚠ " + x)
    for m in r["meses"]:
        L += ["", "%s%s" % (m["mes"], "  [PRELIMINAR]" if m["preliminar"] else ""),
              "  venta entregada %s · pauta %s · fijos %s · NETO %s" % (
                  _q(m["venta_entregada_q"]), _q(m["publicidad"]["q"]),
                  _q(m["gastos_fijos"]["q"]), _q(m["resultado_neto_q"])),
              "  pauta: Meta $%.2f + LucidSales $%.2f · el banco cobró Facebook: %s" % (
                  m["publicidad"]["meta_usd"], m["publicidad"]["lucidsales_fallback_usd"],
                  "—" if m["banco_facebook"]["usd"] is None else "$%.2f" % m["banco_facebook"]["usd"])]
        if m["retiros_personales"]["q"]:
            L.append("  retiros personales del banco (fuera del resultado): %s" % _q(m["retiros_personales"]["q"]))
        c = m["cartera"]
        if c["saldo_cierre_q"] is not None:
            L.append("  billetera de Dropi: saldo %s al %s · retiros personales %s · a cuenta propia %s "
                     "· sin clasificar %s (movimientos de caja: no tocan el resultado)" % (
                         _q(c["saldo_cierre_q"]), c["fecha_corte"], _q(c["retiros_personales_q"]),
                         _q(c["transferencias_propias_q"]), _q(c["sin_clasificar_q"])))
        if c["devoluciones"]["origen"]:
            d = c["devoluciones"]
            L.append("  costo de devoluciones: %s (%d cobros reales, %d estimadas)" % (
                d["origen"], d["reales"], d["estimadas"]))
        for x in m["faltantes"]:
            L.append("  ⚠ " + x)
    return "\n".join(L)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--mercado", required=True, help="GT o CO")
    ap.add_argument("--desde", help="primer mes (YYYY-MM)")
    ap.add_argument("--hasta", help="último mes (YYYY-MM)")
    ap.add_argument("--json", action="store_true", help="imprime el JSON")
    a = ap.parse_args(argv)
    try:
        r = pl_mensual(a.mercado.upper(), a.desde, a.hasta)
    except mercado.MercadoError as e:
        print("BLOQUEANTE: %s" % e, file=sys.stderr)
        return 1
    print(json.dumps(r, ensure_ascii=False) if a.json else texto(r))
    return 0


if __name__ == "__main__":
    sys.exit(main())
