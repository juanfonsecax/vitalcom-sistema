# -*- coding: utf-8 -*-
"""Genera el dashboard HTML del portafolio desde la capa de data.

  python Ads/_TOOLS/gen_dashboard.py

Lee   PRODUCTOS/_FACT_VENTAS.csv · _FACT_ENTREGA.csv · _DIM_CONJUNTOS.csv
      _EVENTOS.csv · _APRENDIZAJES.csv · _BITACORA_DATA.txt
Escribe PRODUCTOS/_DASHBOARD.html

Es la CAPA HUMANA: lo unico que el operador lee a diario. Todo sale calculado
de los CSV — nunca se escribe un numero a mano acá.
"""
import csv, io, os, re, sys, collections, datetime, html, hashlib
# Windows abre la consola en cp1252/cp850: un print con un simbolo fuera de ese
# mapa (⚠, ─, −) revienta con UnicodeEncodeError y el script sale con exit code 1
# AUNQUE el trabajo ya se completo (bug real 18-ago: el aviso de filas sin
# atribucion tumbaba la cadena de la auditoria programada, que lee el exit code).
# Forzar UTF-8 en la salida cubre TODOS los prints, no solo el que fallo.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass


ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
P    = os.path.join(ROOT, "PRODUCTOS")
OUT  = os.path.join(P, "_DASHBOARD.html")

# ── TASA USD→Q: sale de _PARAMETROS_FINANZAS.csv, NUNCA hardcodeada ──────
# Regla 20 de CLAUDE.md: un dato, un dueño. Si la tasa cambia se toca UN csv
# y todos los scripts la toman; hardcodearla en tres lugares garantiza que un
# dia digan cosas distintas.
def _tasa_usd_gtq(_default=7.62):
    import csv as _csv, io as _io, os as _os
    _p = _os.path.join(P, "_PARAMETROS_FINANZAS.csv")
    if _os.path.exists(_p):
        for _r in _csv.DictReader(_io.open(_p, encoding="utf-8")):
            if _r.get("parametro") == "tasa_usd_gtq" and _r.get("valor"):
                return float(_r["valor"])
    return _default


TASA = _tasa_usd_gtq()


def load(name):
    p = os.path.join(P, name)
    if not os.path.exists(p):
        return []
    return list(csv.DictReader(io.open(p, encoding="utf-8")))


def f(x, d=0.0):
    try:
        return float(x)
    except (TypeError, ValueError):
        return d


def i(x, d=0):
    # int("1.0") revienta con ValueError. Si un CSV se reescribe con pandas los
    # enteros salen como "1.0" y el contador de ventas se iba a CERO en silencio
    # (bug real 16-ago: el dashboard mostró 0 ventas y ganancia negativa con la
    # data intacta). Pasar por float primero es lo único que lo hace robusto.
    try:
        return int(float(x))
    except (TypeError, ValueError):
        return d


# ── umbrales por producto: salen de _DIM_PRODUCTOS.csv, nunca hardcodeados ──
prods = {p_["producto_key"]: p_ for p_ in load("_DIM_PRODUCTOS.csv")}
BE = {k: float(v["cpa_be_q"]) for k, v in prods.items() if v.get("cpa_be_q")}
BASE_CPA = {k: float(v["cpa_base_q"]) for k, v in prods.items() if v.get("cpa_base_q")}
BE_ANT = {k: float(v["cpa_be_anterior_q"]) for k, v in prods.items() if v.get("cpa_be_anterior_q")}
costeo = load("_DIM_COSTEO.csv")
tasa_ent = load("_TASA_ENTREGA.csv")

# ═════════════════════════════════════════════════════════════════════════
# ECONOMÍA UNITARIA REAL — desde _DIM_PRECIOS.csv + _TASA_ENTREGA.csv
# ─────────────────────────────────────────────────────────────────────────
# Antes: la ganancia era `ventas × break-even fijo − pauta`. Contaba VENTAS,
# no quetzales, así que un pedido de 3 frascos a Q299 valía igual que uno de
# 1 a Q179 → subestimaba la ganancia ~73% (todo el upsell del bot invisible).
#
# Ahora, por cada venta se infiere el escalón desde el ticket y se calcula:
#   contribución = TE × (precio − costo prod − flete − admin − otros)
#                − (1−TE) × costo del evento de devolución
# Medido sobre 102 órdenes reales de Dropi (25-31 jul): flete Q31.42+Q2.70/u,
# comisión de plataforma 0%, devolución Q27.16 (sale en el estado de cuenta,
# no en la orden). La escalera de cada producto vive en _DIM_PRECIOS.csv y es
# FLEXIBLE: un producto barato puede arrancar en 2x1 y no tener 1u.
# ═════════════════════════════════════════════════════════════════════════
# ⚠️ NO se toma "la ultima fila": se toma la de MAS ORDENES RESUELTAS.
# Por que (11-ago): al cargar Dropi de agosto, esa ventana daba 95.7% de entrega
# sobre 46 resueltos, contra 85.1% sobre 121 de julio. Tomar la ultima habria
# subido la TE de golpe e inflado la ganancia de TODO el portafolio con una
# ventana chica y sin madurar (8 de 54 ordenes aun en transito; si todas cayeran
# a devolucion la tasa real seria 81.5%). Manda la evidencia, no la fecha: la
# fila con mas casos resueltos. Cuando agosto madure y acumule, gana sola.
def _resueltos(r):
    return i(r.get("entregado")) + i(r.get("devolucion")) + i(r.get("cancelado"))


_glob = [r for r in tasa_ent if (r.get("producto_key") or "GLOBAL") == "GLOBAL"]
_te = max(_glob or tasa_ent, key=_resueltos) if tasa_ent else {}
TE       = f(_te.get("pct_entrega_resueltos"), 85.1) / 100.0
C_DEVOL  = f(_te.get("costo_devolucion_evento_q"), 27.16)
C_ADMIN  = f(_te.get("costos_admin_q"), 4.0)
C_OTROS  = f(_te.get("otros_gastos_q"), 2.08)
FLETE_A, FLETE_B = 31.42, 2.70          # flete = A + B×unidades (regresión, R²=.44)

# ── TASA DE ENTREGA POR PRODUCTO (11-ago) ────────────────────────────────
# La serie completa de Dropi (304 ordenes, 01-jul a 07-ago) mostro que la
# entrega NO es homogenea: CLEARSTEM 95.8% contra NUSAVA 71.7% = 24 puntos.
# Costear todo con la global (86.2%) movia el break-even real hasta -19.5% en
# NUSAVA y +16.3% en CLEARSTEM, e INVERTIA el ranking de productos. Cada
# producto usa su propia tasa cuando tiene >=20 resueltos; si no, la global.
TE_PROD = {}
for _r in tasa_ent:
    _pk = _r.get("producto_key") or "GLOBAL"
    if _pk == "GLOBAL":
        continue
    if _resueltos(_r) >= 20 and (_pk not in TE_PROD or _resueltos(_r) > TE_PROD[_pk][1]):
        TE_PROD[_pk] = (f(_r["pct_entrega_resueltos"]) / 100.0, _resueltos(_r))


def te_de(pk):
    """Tasa de entrega del producto; cae a la global si no hay evidencia propia."""
    return TE_PROD.get(pk, (TE, 0))[0]


precios = collections.defaultdict(list)
for r in load("_DIM_PRECIOS.csv"):
    if (r.get("estado") or "").upper() in ("SIN_REGISTRAR",):
        continue
    u = i(r["unidades"], 1)
    fl = f(r.get("flete_q")) or (FLETE_A + FLETE_B * u)
    p = f(r["precio_q"])
    _tep = te_de(r["producto_key"])
    contrib = _tep * (p - f(r["costo_proveedor_total_q"]) - fl - C_ADMIN - C_OTROS) - (1 - _tep) * C_DEVOL
    precios[r["producto_key"]].append({
        "u": u, "precio": p, "etiqueta": r.get("etiqueta") or "{}x".format(u),
        "costo": f(r["costo_proveedor_total_q"]), "flete": fl,
        "contrib": contrib, "n": i(r.get("n_ordenes")), "estado": r.get("estado", "")})
for k in precios:
    precios[k].sort(key=lambda x: x["precio"])


_PRECIO_TABLA, _CPA_BASE_TABLA = {}, {}
_P2U_TABLA, _P3U_TABLA, _ORIGEN_ESC = {}, {}, {}
for _x in costeo:
    _c = int(f(_x["costo_producto"]))
    _c = 55 if _c == 54 else _c          # la fila Q54 del xlsx = el escalón Q55
    _PRECIO_TABLA[_c] = int(f(_x["precio_establecido"]))
    _CPA_BASE_TABLA[_c] = f(_x["cpa_base"])
    # Escalera del operador (unificada 2026-09-02). Ver escalera_sugerida.
    if _x.get("precio_2u"):
        _P2U_TABLA[_c] = int(f(_x["precio_2u"]))
    if _x.get("precio_3u"):
        _P3U_TABLA[_c] = int(f(_x["precio_3u"]))
    _ORIGEN_ESC[_c] = (_x.get("origen_escalera") or "OPERADOR").strip()


def contrib_tier(precio, costo_total, u):
    """Contribución esperada de un pedido de u unidades a ese precio."""
    fl = FLETE_A + FLETE_B * u
    return TE * (precio - costo_total - fl - C_ADMIN - C_OTROS) - (1 - TE) * C_DEVOL


def precio_1u(costo_u):
    """Precio de 1 unidad. MANDA la decisión del operador en _DIM_COSTEO.csv.

    Solo se extrapola para los costos que esa tabla no cubre (Q30 y Q35): ahí
    se extiende el patrón del extremo barato, donde el margen sobre el costo es
    de Q139 (Q40→179). El Q54 de la tabla se lee como Q55 para que la grilla
    quede en múltiplos de 5 limpios.
    """
    if costo_u in _PRECIO_TABLA:
        return _PRECIO_TABLA[costo_u]
    return int(round((costo_u + 139 - 9) / 10.0) * 10) + 9


def arranque_recomendado(costo_u, cpa_peor=63.0):
    """¿El producto arranca en 1 unidad o directo en 2x1?

    El criterio NO es el margen (a cualquier costo el margen cierra), es el
    MÚLTIPLO que habría que cobrar por una sola unidad para que aguante el CPA
    que realmente se paga. Los ~Q40 fijos de logística (flete + admin + otros)
    no bajan con el precio, así que en un producto barato ese múltiplo se
    dispara y el precio deja de ser creíble para la categoría.

        P1u mínimo = (CPA + costo devolución amortizado)/TE + costo + fijos
        múltiplo   = P1u mínimo / costo

    Con múltiplo ≥ 4× la venta de 1u es frágil → arrancar en 2x1. Usando el
    PEOR CPA observado (no el promedio) la frontera cae en Q40.
    """
    fijos = (FLETE_A + FLETE_B) + C_ADMIN + C_OTROS
    p_min = (cpa_peor + (1 - TE) * C_DEVOL) / TE + costo_u + fijos
    mult = p_min / costo_u if costo_u else 99
    if mult >= 4.0:
        return "2X1", mult
    if mult >= 3.4:
        return "CRITERIO", mult
    return "1U", mult


def escalera_sugerida(costo_u, precio_1u, n=4):
    """Precios sugeridos para 1..n unidades.

    FUENTE: `precio_2u` y `precio_3u` de _DIM_COSTEO.csv — los precios que fijó
    el operador. La regla `costo × 1.7` quedó como extrapolación para los costos
    Q85-Q130 que él nunca fijó (marcados `origen_escalera = EXTRAPOLADO`). La unidad extra casi no agrega costo logístico (solo Q2.70 de
    flete: mismo envío, mismo riesgo de devolución, mismo admin), así que es
    el escalón donde vive el margen.
    ⚠️ Es una SUGERENCIA de precio, no una predicción de conversión: subir el
    precio puede bajar la tasa de cierre. Se testea, no se aplica a ciegas.
    """
    # UNIFICADO 2026-09-02: la escalera sale de _DIM_COSTEO.csv, no de la fórmula.
    # _DIM_PRECIOS.csv desempató con datos de Dropi: TINNIDROP en la fila Q40 vende
    # a 179/239/299 con n=102/42/18 órdenes reales, que es la tabla del operador.
    # La fórmula habría dado 179/249/319. Ahora solo extrapola donde no hay dato.
    p2, p3 = _P2U_TABLA.get(costo_u), _P3U_TABLA.get(costo_u)
    if p2 and p3:
        precios = [precio_1u, p2, p3]
        salto = p3 - p2
        precios += [p3 + salto * i for i in range(1, max(0, n - 3) + 1)]
    else:
        inc = round(costo_u * 1.7 / 10.0) * 10
        precios = [precio_1u + (u - 1) * inc for u in range(1, n + 1)]
    return [(u, precios[u - 1], costo_u * u) for u in range(1, min(n, len(precios)) + 1)]


def escalon(pk, ticket):
    """Devuelve el escalón cuyo precio más se parece al ticket.

    El reporte trae el ticket PROMEDIO cuando una fila agrupa varias ventas
    (una de 1u + una de 2u → Q209). Como las escaleras son lineales, se
    interpola: el promedio de tickets da el promedio de contribuciones.
    """
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
    """Contribución esperada de una fila de ventas (ya neta de todo menos pauta)."""
    v = i(r["ventas"])
    if not v:
        return 0.0
    c = escalon(r["producto_key"], f(r["total_q"]) / v)
    if c is None:                                   # producto sin escalera aún
        return v * BE.get(r["producto_key"], 60.5)
    return v * c


# break-even real por producto = contribución ponderada por el mix VENDIDO
_mix = collections.defaultdict(lambda: [0.0, 0])
for r in load("_FACT_VENTAS.csv"):
    if r.get("rol_ventana") != "BASE" or not i(r["ventas"]):
        continue
    _mix[r["producto_key"]][0] += contribucion(r); _mix[r["producto_key"]][1] += i(r["ventas"])
BE_REAL = {k: (s / v) for k, (s, v) in _mix.items() if v}
BE_VIEJO = dict(BE)
for k, v in BE_REAL.items():                        # el BE real manda
    BE[k] = v

ventas   = [r for r in load("_FACT_VENTAS.csv") if r.get("rol_ventana") == "BASE"]
entrega  = load("_FACT_ENTREGA.csv")
dim      = {(d["producto_key"], d["conjunto_meta"]): d for d in load("_DIM_CONJUNTOS.csv")}
eventos  = load("_EVENTOS.csv")
aprend   = [a for a in load("_APRENDIZAJES.csv") if a.get("estado") in ("VIGENTE", "EN_OBSERVACION")]

# ── integridad de ventana (de la bitacora) ───────────────────────────────
bit = ""
bp = os.path.join(P, "_BITACORA_DATA.txt")
if os.path.exists(bp):
    bit = io.open(bp, encoding="utf-8").read()
dias_ok  = len(re.findall(r"\|\s*✅\s*\|", bit))
dias_bad = len(re.findall(r"\|\s*🔴\s*\|", bit))

ventana = ("—", "—")
if ventas:
    ventana = (min(r["ventana_ini"] for r in ventas), max(r["ventana_fin"] for r in ventas))

# ── P&L por producto ─────────────────────────────────────────────────────
pl = collections.defaultdict(lambda: [0.0, 0, 0.0, 0.0])
for r in ventas:
    k = r["producto_key"]
    pl[k][0] += f(r["spend_usd"]); pl[k][1] += i(r["ventas"])
    pl[k][2] += f(r["total_q"]); pl[k][3] += contribucion(r)

filas_pl, T = [], [0.0, 0, 0.0, 0.0]
for k, (s, v, ing, contrib) in pl.items():
    g = s * TASA
    be = BE.get(k, 60.5)
    gan = contrib - g          # contribución real de cada pedido − pauta
    cpa = g / v if v else None
    filas_pl.append({"producto": k, "ventas": v, "pauta": g, "ingreso": ing,
                     "cpa": cpa, "be": be, "base": BASE_CPA.get(k, 30.8), "ganancia": gan})
    T[0] += g; T[1] += v; T[2] += ing; T[3] += gan
filas_pl.sort(key=lambda x: -x["ganancia"])

# ── ranking por ANGULO (unidad de decision del sistema) ──────────────────
ang = collections.defaultdict(lambda: [0.0, 0, 0.0, set(), set()])
# sin_dim   = conjunto REAL que le falta fila en _DIM_CONJUNTOS -> hay que darlo de alta.
# sin_atrib = venta que LucidSales no pudo atribuir a ningun anuncio (cuenta_alias
#             SIN_ATRIBUCION, campana y conjunto vacios). NO es un hueco de dimension:
#             es tracking roto (ver APR-035). Contarlas juntas hacia creer que faltaban
#             conjuntos por registrar cuando lo que falta es la atribucion.
sin_dim = 0
sin_atrib = 0
sin_atrib_ventas = 0
for r in ventas:
    if not r.get("conjunto") and r.get("cuenta_alias") == "SIN_ATRIBUCION":
        sin_atrib += 1
        sin_atrib_ventas += i(r["ventas"])
        continue
    d = dim.get((r["producto_key"], r["conjunto"]))
    if not d:
        sin_dim += 1
        continue
    k = (r["producto_key"], d["angulo_key"])
    ang[k][0] += f(r["spend_usd"]); ang[k][1] += i(r["ventas"]); ang[k][2] += f(r["total_q"])
    ang[k][3].add(r["cuenta_alias"]); ang[k][4].add(d["tipo_hook"])

filas_ang = []
for (pk, ak), (s, v, ing, ctas, hooks) in ang.items():
    g = s * TASA
    be, base = BE.get(pk, 60.5), BASE_CPA.get(pk, 30.8)
    cpa = g / v if v else None
    if cpa is None:
        est = "sub-testeado" if g < be else "sin ventas"
        sev = "warn" if g < be else "crit"
    elif cpa <= base:
        est, sev = "ganador", "good"
    elif cpa <= be:
        est, sev = "rentable", "warn"
    else:
        est, sev = "sobre break-even", "crit"
    filas_ang.append({"producto": pk, "angulo": ak, "ventas": v, "pauta": g, "cpa": cpa,
                      "be": be, "pd": min(100, round(100 * g / be)), "estado": est, "sev": sev,
                      "cuentas": len(ctas), "hook": sorted(hooks)[0] if hooks else "—",
                      "n_bajo": v < 5})
filas_ang.sort(key=lambda x: (x["cpa"] is None, x["cpa"] or 0))

# ── sangrado: conjuntos con 0 ventas que YA pasaron su PD ────────────────
conj = collections.defaultdict(lambda: [0.0, 0])
for r in ventas:
    k = (r["producto_key"], r["cuenta_alias"], r["conjunto"])
    conj[k][0] += f(r["spend_usd"]); conj[k][1] += i(r["ventas"])
sangrado, sub = [], []
for (pk, ca, cj), (s, v) in conj.items():
    if v:
        continue
    g, be = s * TASA, BE.get(pk, 60.5)
    d = dim.get((pk, cj), {})
    row = {"producto": pk, "cuenta": ca, "conjunto": cj, "pauta": g,
           "pd": round(100 * g / be), "angulo": d.get("angulo_key", "—")}
    (sangrado if g >= be else sub).append(row)
sangrado.sort(key=lambda x: -x["pauta"]); sub.sort(key=lambda x: -x["pauta"])
q_sangrado = sum(x["pauta"] for x in sangrado)
q_sub = sum(x["pauta"] for x in sub)

# ── CORTE SEMANAL (02-sep) ───────────────────────────────────────────────
# El operador pidió ver el resultado POR SEMANA además del general: la decisión
# de CPA es semanal (el COD madura ~3 días), así que la semana es la unidad
# natural de lectura del negocio — el día suelto es ruido y el acumulado esconde
# la tendencia. Las filas de ventana multi-día se PRORRATEAN entre sus días:
# el total del tramo queda exacto y el reparto entre semanas es interpolado.
def _semana_de(fecha):
    d = datetime.date.fromisoformat(fecha)
    return d - datetime.timedelta(days=d.weekday())


def calcular_semanas(filas_base):
    sem = collections.defaultdict(lambda: {"tot": [0.0, 0.0, 0.0, 0.0],
                                           "prod": collections.defaultdict(lambda: [0.0, 0.0, 0.0, 0.0]),
                                           "dias": set(), "estimada": False})
    for r in filas_base:
        ini = r.get("ventana_ini") or ""
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", ini):
            continue
        n = max(i(r.get("dias"), 1), 1)
        d0 = datetime.date.fromisoformat(ini)
        parte = (i(r["ventas"]) / n, f(r["total_q"]) / n,
                 f(r["spend_usd"]) * TASA / n, contribucion(r) / n)
        for k in range(n):
            s = sem[_semana_de((d0 + datetime.timedelta(days=k)).isoformat())]
            s["dias"].add((d0 + datetime.timedelta(days=k)).isoformat())
            if n > 1:
                s["estimada"] = True
            for tgt in (s["tot"], s["prod"][r["producto_key"]]):
                for j in range(4):
                    tgt[j] += parte[j]
    return dict(sorted(sem.items(), reverse=True))


def q(n):   return "Q{:,.0f}".format(n)
def q1(n):  return "Q{:,.1f}".format(n)
def esc(s): return html.escape(str(s))


# ═════════════════════════════════════════════════════════════════════════
# MOTOR DE ACCIONES — "qué tengo que hacer"
# ─────────────────────────────────────────────────────────────────────────
# Todo se DERIVA de los CSV. Ninguna acción se escribe a mano: si la data
# cambia, el plan cambia solo. Las reglas son las del ESCALADO_PLAYBOOK:
#   A) matar-por-ventas   (0 ventas con el PD cumplido)
#   B) matar-por-conversación (0 ventas + conversación en el fondo, aún sub-PD)
#   C) rebalancear cuenta saturada (mismo ángulo, CPA ≥2× peor en una cuenta)
#   D) surfing +20% sobre el ganador
#   E) ganador infra-financiado (buen CPA pero casi sin presupuesto)
#   F) renovar creativo (el ángulo comunica, el creativo se gastó)
#   G) producto VIVO que dejó de gastar
#   H) huecos de data
#   I) cuenta con historial que amaneció en CERO (UNSETTLED / pago caído)
#   J) cuenta que SÍ gasta pero SANGRA en la ventana reciente
#   K) el portafolio pasó su techo de gasto demostrado y el CPA se deterioró
#   L) ángulo que SÍ vende pero sangra en la ventana reciente (CPA > break-even)
#   O) cuenta apagada, leída desde LucidSales (cubre las cuentas sin MCP)
#   P) el hueco de data cruzó el ciclo de maduración de la COD (~3d)
#   Q) el lado-ads se congeló: MCP caído, _FACT_ENTREGA sin actualizar
# ═════════════════════════════════════════════════════════════════════════
# ⚠️ NO filtrar por dias==1. Cuando el operador entrega exports AGREGADOS
# (ventanas de 3, 8 o 10 días, como al volver de una ausencia), ese filtro deja
# fuera toda la data reciente y el motor decide con la última ventana de 1 día,
# que puede tener semanas de viejo. Bug real 11-ago: ult_dia quedó en 2026-07-30
# habiendo data hasta el 10-ago → pedía "reactivar VARICOSE" (que sí gastaba, en
# la 2ª cuenta de LucidSales) y "pegar el export, 11 días sin cargar" (falso).
# `ult3` = los últimos 3 PUNTOS de data, sean días sueltos o ventanas agregadas.
dias_data = sorted({r["ventana_fin"] for r in ventas})
ult_dia = dias_data[-1] if dias_data else None
ult3 = set(dias_data[-3:])

# agregados por conjunto (con detalle por día para calcular ritmo y antigüedad)
cj = collections.defaultdict(lambda: {"sp": 0.0, "v": 0, "msj": 0, "clk": 0,
                                      "dias": collections.defaultdict(lambda: [0.0, 0]),
                                      "campana": ""})
for r in ventas:
    k = (r["producto_key"], r["cuenta_alias"], r["conjunto"])
    c = cj[k]
    c["sp"] += f(r["spend_usd"]); c["v"] += i(r["ventas"])
    c["msj"] += i(r["mensajes"]); c["clk"] += i(r["clicks"])
    c["campana"] = r.get("campana") or c["campana"]
    dd = c["dias"][r["ventana_fin"]]
    dd[0] += f(r["spend_usd"]); dd[1] += i(r["ventas"])


def ritmo_sem(c):
    """Q/semana al ritmo de los últimos 3 días con data."""
    d = [v[0] for k_, v in c["dias"].items() if k_ in ult3]
    return (sum(d) / max(len(d), 1)) * 7 * TASA if d else 0.0


def dias_sobre_pd(c, be):
    """Cuántos días lleva gastando por encima de su PD sin vender."""
    acum, n = 0.0, 0
    for dd in sorted(c["dias"]):
        acum += c["dias"][dd][0] * TASA
        if acum >= be and c["v"] == 0:
            n += 1
    return n


def conv(c):
    return (100.0 * c["msj"] / c["clk"]) if c["clk"] else None


# mediana de conversación por producto (referencia relativa: el CSV trae clics
# TOTALES, no clics-de-enlace, así que el 35% del playbook no es comparable)
conv_prod = collections.defaultdict(list)
for (pk, ca, cn), c in cj.items():
    x = conv(c)
    if x is not None and c["sp"] * TASA > 20:
        conv_prod[pk].append(x)


def mediana(xs):
    if not xs:
        return None
    xs = sorted(xs); n = len(xs)
    return xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2.0


acciones = []

# ── UBICACIÓN EXACTA ──────────────────────────────────────────────────────
# El operador no ejecuta sobre "el ángulo DETERIORO COGNITIVO en GTR7": ejecuta
# sobre UNA campaña y UNOS conjuntos que tiene que encontrar en Ads Manager.
# Decirle el ángulo y la cuenta lo obliga a traducir a mano, y ahí es donde se
# equivoca o directamente no lo hace. Cada acción tiene que nombrar la campaña
# y los conjuntos tal cual se llaman en Meta.
_camp_de = {}       # (pk, cuenta, conjunto) -> campaña más reciente donde vive
for _r in sorted(ventas, key=lambda x: x.get("ventana_fin", "")):
    if _r.get("campana"):
        _camp_de[(_r["producto_key"], _r["cuenta_alias"], _r["conjunto"])] = _r["campana"]

_conj_de_ang = collections.defaultdict(dict)   # (pk, angulo, cuenta) -> {conjunto: campaña}
for _r in ventas:
    _d = dim.get((_r["producto_key"], _r["conjunto"]))
    if not _d:
        continue
    _k = (_r["producto_key"], _d["angulo_key"], _r["cuenta_alias"])
    _conj_de_ang[_k][_r["conjunto"]] = _r.get("campana") or "—"


def _camp(pk, cta, conj):
    return _camp_de.get((pk, cta, conj), "—")


def donde_conjunto(pk, cta, conj):
    """Ubicación de UN conjunto: cuenta → campaña → conjunto."""
    return "{} · {} → campaña «{}» → conjunto «{}»".format(pk, cta, _camp(pk, cta, conj), conj)


def donde_angulo(pk, ak, cta, maxn=4):
    """Ubicación de un ÁNGULO: se listan los conjuntos reales que lo componen."""
    m = _conj_de_ang.get((pk, ak, cta), {})
    if not m:
        return "{} · ángulo {} · {}".format(pk, ak.replace("_", " ").title(), cta)
    camps = sorted(set(m.values()))
    cs = sorted(m)
    lista = ", ".join("«{}»".format(c) for c in cs[:maxn])
    if len(cs) > maxn:
        lista += " y {} más".format(len(cs) - maxn)
    return "{} · {} → campaña{} {} → conjunto{}: {}".format(
        pk, cta, "s" if len(camps) > 1 else "",
        ", ".join("«{}»".format(c) for c in camps), "s" if len(cs) > 1 else "", lista)


# ── VIGENCIA: no volver a pedir lo que el operador YA hizo ────────────────
# Bug real (16-ago): el operador pausó las 3 campañas viejas duplicadas por la
# mañana y el dashboard seguía diciéndole "apagá esto" — porque las acciones se
# derivan de la data de ventas, que va unos días atrás. Pedir algo ya hecho hace
# que el operador deje de confiar en la lista entera. Se cruza contra _EVENTOS.
_PAUSAS_CAMP, _PAUSAS_CONJ = set(), set()
try:
    for _e in load("_EVENTOS.csv"):
        if "PAUSA" not in (_e.get("evento") or "").upper():
            continue
        if _e.get("fecha", "") < (ult_dia or ""):
            continue                       # pausa vieja: la data ya la refleja
        _cv, _cj = (_e.get("campana_clave") or "").strip(), (_e.get("conjunto_meta") or "").strip()
        if _cj in ("", "*"):
            for _p in [x.strip() for x in _cv.split("/")]:
                if _p:
                    _PAUSAS_CAMP.add(_p)
        else:
            _PAUSAS_CONJ.add(_cj)
except Exception:
    pass


def _norm(s):
    """Compara nombres de Meta ignorando emojis, acentos y espacios de más.
    El operador pone 🟩/🟦 al inicio y los quita cuando le parece; sin esto el
    cruce contra _EVENTOS falla y la acción se muestra como pendiente igual."""
    s = "".join(ch for ch in str(s) if ord(ch) < 0x2190)
    return re.sub(r"\s+", " ", s).strip().lower()


_PAUSAS_CAMP_N = {_norm(c) for c in _PAUSAS_CAMP if len(c) > 6}
_PAUSAS_CONJ_N = {_norm(c) for c in _PAUSAS_CONJ if len(c) > 6}

# Campañas que SIGUEN CORRIENDO.
# Fuente 1 (manda): _ESTADO_META.csv — el operador enumera qué está encendido.
#   Es la única fuente confiable para GTR13 y CP1, que NO tienen MCP y donde el
#   sistema es ciego por definición. Entre las dos juntan el 30% de las ventas,
#   así que no leerlas no es una opción.
# Fuente 2 (fallback): gasto en el último día de data. Sirve mientras el estado
#   no esté declarado, pero va 1-3 días atrás y por eso el dashboard llegó a
#   pedir apagar campañas ya pausadas.
_camp_viva, _estado_declarado = set(), False
try:
    _em = load("_ESTADO_META.csv")
except Exception:
    _em = []
if _em:
    _estado_declarado = True
    for _r in _em:
        if (_r.get("estado") or "").strip().upper() == "ON" and _r.get("campana"):
            _camp_viva.add(_norm(_r["campana"]))
else:
    for _r in ventas:
        if _r.get("ventana_fin") == ult_dia and f(_r["spend_usd"]) > 0 and _r.get("campana"):
            _camp_viva.add(_norm(_r["campana"]))


def _inactivo(donde):
    d = _norm(donde)
    if any(c in d for c in _PAUSAS_CAMP_N) or any(c in d for c in _PAUSAS_CONJ_N):
        return "✓ ya pausado — nada que hacer"
    # ¿la acción apunta a alguna campaña que sí está viva?
    tocadas = [c for c in _camp_viva if c and c in d]
    if _camp_viva and not tocadas and "campaña" in donde.lower():
        return ("apagada — sin efecto" if _estado_declarado
                else "no corre desde el {} — sin efecto".format(ult_dia))
    return None


def add(pri, tipo, sev, que, donde, porque, impacto, estado):
    # Ninguna acción sobre algo apagado es accionable, salvo las que existen
    # justamente para volver a prenderlo o para revisar la cuenta.
    if tipo not in ("REACTIVAR", "REVISAR", "DATA"):
        m = _inactivo(donde)
        if m:
            pri, sev, estado, impacto = 4, "done", m, 0
    acciones.append({"pri": pri, "tipo": tipo, "sev": sev, "que": que, "donde": donde,
                     "porque": porque, "impacto": impacto, "estado": estado})


# ── G) productos VIVOS que dejaron de gastar ─────────────────────────────
gasto_ult = collections.defaultdict(float)
ult_gasto_dia = {}
for r in ventas:
    pk = r["producto_key"]
    if f(r["spend_usd"]) > 0:
        ult_gasto_dia[pk] = max(ult_gasto_dia.get(pk, ""), r["ventana_fin"])
    if r["ventana_fin"] in ult3:
        gasto_ult[pk] += f(r["spend_usd"])

for pk, meta in prods.items():
    if (meta.get("estado") or "").upper() != "VIVO":
        continue
    if gasto_ult.get(pk, 0) > 0.5:
        continue
    hist = [x for x in filas_pl if x["producto"] == pk]
    cpa_h = hist[0]["cpa"] if hist and hist[0]["cpa"] else None
    be = BE.get(pk, 60.5)
    desde = ult_gasto_dia.get(pk)
    ndias = "—"
    if desde and ult_dia:
        try:
            ndias = (datetime.date(*map(int, ult_dia.split("-")))
                     - datetime.date(*map(int, desde.split("-")))).days
        except Exception:
            ndias = "—"
    porque = ("marcado VIVO pero sin gasto hace {} días".format(ndias) if ndias != "—"
              else "marcado VIVO pero sin gasto en la ventana")
    if cpa_h:
        porque += " · su CPA histórico es {} contra un break-even de {}".format(q1(cpa_h), q1(be))
    imp = (be - cpa_h) * (hist[0]["ventas"] or 1) if cpa_h else 0
    add(1, "REACTIVAR", "crit", "Reactivar la campaña",
        "{} · toda la cuenta".format(pk), porque,
        imp, "sin correr")

# ── I) CUENTA con historial de gasto que amanecio en CERO ────────────────
# Una cuenta puede tener todas sus campanas en ACTIVE y no gastar un centavo:
# pasa cuando queda en account_status=UNSETTLED (saldo sin liquidar) o se le cae
# el metodo de pago. No se ve a nivel campana ni conjunto, y la regla G) tampoco
# lo agarra porque el PRODUCTO sigue gastando en las otras cuentas. Detectado el
# 15-ago con GTR0 (3 campanas ACTIVE, 18 conjuntos, $0.00) y ya insinuado el
# 12-ago. Ver APR-037.
try:
    ent = load("_FACT_ENTREGA.csv")
except Exception:
    ent = []
if ent:
    dias_ent = sorted({r["ventana_ini"] for r in ent if r.get("ventana_ini")})
    if dias_ent:
        ult_ent = dias_ent[-1]
        gasto_dia = collections.defaultdict(float)     # cuenta -> gasto del ultimo dia
        gasto_hist = collections.defaultdict(float)    # cuenta -> gasto historico
        prods_cta = collections.defaultdict(set)
        for r in ent:
            ca = r.get("cuenta_alias") or "?"
            sp = f(r["spend_usd"])
            gasto_hist[ca] += sp
            if r["ventana_ini"] == ult_ent:
                gasto_dia[ca] += sp
                if sp > 0:
                    prods_cta[ca].add(r["producto_key"])
        for ca, hist_sp in sorted(gasto_hist.items(), key=lambda x: -x[1]):
            # solo cuentas que SI saben gastar (>$20 historicos) y hoy estan en cero
            if hist_sp < 20 or gasto_dia.get(ca, 0) > 0.5:
                continue
            add(1, "REVISAR", "crit", "Revisar facturación de la cuenta",
                "{} · toda la cuenta".format(ca),
                "gastó $0.00 el {} pese a tener ${:,.0f} de historial — revisar si quedó "
                "en UNSETTLED o se le cayó el método de pago (las campañas siguen en ACTIVE)"
                .format(ult_ent, hist_sp),
                0, "sin correr")

# ── O) CUENTA QUE VENIA GASTANDO Y SE APAGO — VISTA DESDE LUCIDSALES ─────
# La regla I) lee `_FACT_ENTREGA.csv`, que se llena SOLO por MCP. Las cuentas
# sin conector (GTR13 y CP1) no aparecen nunca ahi, asi que para ellas I) es
# ciega por construccion; y cuando el MCP se cae, `_FACT_ENTREGA` se congela y
# I) queda muerta para TODAS. Hueco real: CP1 (1346891653335162) estaba en la
# ventana 11-16 con Q198 de pauta, 6 ventas y CPA Q33.1 -- la cuenta MAS BARATA
# del portafolio -- y desaparecio por completo del 17 al 20-ago. Nadie lo vio
# hasta que se pidio el export de Ads Manager cuatro dias despues, y para
# entonces ya se habian perdido ~4 dias de la pauta mas eficiente que habia.
# Esta regla mira la MISMA senal desde `_FACT_VENTAS.csv`, que si cubre a todas
# las cuentas porque LucidSales reporta sin depender del MCP.
# Por que es REVISAR y no REACTIVAR: la caida a cero puede ser deliberada (el
# operador la apago) o un problema de cobro. No se atribuye por descarte
# (APR-030) -- se pregunta.
# GUARDARRAILES: (1) compara la ventana reciente contra una ventana previa de
# IGUAL cantidad de puntos de data, para que no la dispare un simple hueco de
# calendario; (2) exige que la ventana previa tenga gasto material (>=1
# break-even del portafolio) -- una cuenta que gastaba $3 y paro no es noticia;
# (3) exige CERO gasto en la reciente, no "menos gasto" (eso ya lo cubre J);
# (4) el impacto es la CONTRIBUCION que la cuenta dejaba neta de su pauta en la
# ventana previa, no el ingreso bruto: si estaba perdiendo plata, apagarla fue
# correcto y la accion sale con impacto 0.
if len(dias_data) >= 2:
    _n = len(ult3)
    _prev = set(dias_data[-(2 * _n):-_n]) or set(dias_data[:-_n])
    _cta_now = collections.defaultdict(float)
    _cta_prev = collections.defaultdict(lambda: [0.0, 0, 0.0])   # [gasto Q, ventas, contrib]
    for r in ventas:
        ca = r.get("cuenta_alias") or "?"
        if r["ventana_fin"] in ult3:
            _cta_now[ca] += f(r["spend_usd"])
        elif r["ventana_fin"] in _prev:
            x = _cta_prev[ca]
            x[0] += f(r["spend_usd"]) * TASA
            x[1] += i(r["ventas"])
            x[2] += contribucion(r)
    _be_med = mediana(list(BE.values())) or 60.5
    for ca, (_gq, _v, _c) in sorted(_cta_prev.items(), key=lambda x: -x[1][0]):
        if _gq < _be_med:                      # no gastaba de verdad
            continue
        if _cta_now.get(ca, 0) > 0.5:          # sigue gastando: no es esta regla
            continue
        _cpa = _gq / _v if _v else 0
        _neto = _c - _gq
        _det = ("venía dando {} venta{} a CPA {}".format(_v, "s" if _v != 1 else "", q1(_cpa))
                if _v else "venía sin cerrar ventas")
        _cierre = ("" if _neto <= 0 else
                   " · te dejaba {} netos en esos días".format(q(_neto)))
        add(1, "REVISAR", "crit", "Preguntar por qué esta cuenta dejó de gastar",
            "{} · toda la cuenta".format(ca),
            "gastó {} en los puntos de data previos ({}){} y CERO en los últimos {} — "
            "confirmar si la apagaste vos o si se le cayó el cobro; no atribuir por descarte"
            .format(q(_gq), _det, _cierre, _n),
            max(_neto, 0), "sin correr")

# ── EL ÁNGULO MANDA SOBRE EL CONJUNTO ────────────────────────────────────
# CLAUDE.md regla 6 y la doctrina de la auditoría: el veredicto se declara
# agregando por `angulo_key`, NUNCA por conjunto, y las réplicas R[N] se SUMAN,
# nunca se comparan — la diferencia entre réplicas idénticas es ruido de Poisson
# (índice de dispersión 1.12 por conjunto vs 2.99 por ángulo, medido sobre data
# propia). El motor estaba matando por conjunto y contradecía al propio sistema:
# el 16-ago mandó apagar NUSAVA_ARDOR_R1 (0 ventas) siendo que el ángulo ARDOR
# lleva 41 ventas a CPA Q58 contra un break-even de Q93, y CLEARSTEM
# ANTI-FALSIFICACION_R12 cuando ese ángulo lleva 15 ventas a CPA Q73 vs Q106.
# Un conjunto de un ángulo que vende bajo break-even NO se mata: es ruido.
_ang_tot = collections.defaultdict(lambda: [0.0, 0])      # (pk, angulo) -> [gasto, ventas]
for r in ventas:
    d = dim.get((r["producto_key"], r["conjunto"]))
    if not d:
        continue
    k = (r["producto_key"], d["angulo_key"])
    _ang_tot[k][0] += f(r["spend_usd"]) * TASA
    _ang_tot[k][1] += i(r["ventas"])


def _angulo_de(pk, cn):
    d = dim.get((pk, cn))
    return d["angulo_key"] if d else None


def _angulo_sano(pk, cn):
    """True si el ÁNGULO al que pertenece el conjunto vende por debajo del
    break-even. En ese caso el cero de una réplica suelta no es veredicto."""
    ak = _angulo_de(pk, cn)
    if not ak:
        return False
    g, v = _ang_tot.get((pk, ak), [0.0, 0])
    return bool(v) and (g / v) < BE.get(pk, 60.5)


# ── A) matar-por-ventas ──────────────────────────────────────────────────
for (pk, ca, cn), c in sorted(cj.items(), key=lambda x: -x[1]["sp"]):
    if c["v"] or c["sp"] * TASA < BE.get(pk, 60.5):
        continue
    if _angulo_sano(pk, cn):
        continue          # el ángulo vende bajo BE: este cero es Poisson, no señal
    be = BE.get(pk, 60.5)
    activo = any(d in ult3 and c["dias"][d][0] > 0 for d in c["dias"])
    nd = dias_sobre_pd(c, be)
    add(1 if activo else 3, "APAGAR", "crit", "Apagar este conjunto",
        donde_conjunto(pk, ca, cn),
        "gastó {} (={}% de su presupuesto de decisión) y no vendió ni una vez"
        .format(q(c["sp"] * TASA), round(100 * c["sp"] * TASA / be)),
        ritmo_sem(c),
        "sigue gastando · {} día{} así".format(nd, "s" if nd != 1 else "") if activo else "ya no gasta")

# ── B) matar-por-conversación ────────────────────────────────────────────
for (pk, ca, cn), c in sorted(cj.items(), key=lambda x: -x[1]["sp"]):
    if c["v"] or c["sp"] * TASA >= BE.get(pk, 60.5) or c["sp"] * TASA < 20:
        continue
    x, med = conv(c), mediana(conv_prod.get(pk, []))
    if x is None or med is None or x >= med * 0.6:
        continue
    if not any(d in ult3 and c["dias"][d][0] > 0 for d in c["dias"]):
        continue
    if _angulo_sano(pk, cn):
        continue
    add(2, "APAGAR", "crit", "Apagar este conjunto (conversación floja)",
        donde_conjunto(pk, ca, cn),
        "{:.1f}% de conversación por clic contra {:.1f}% de mediana del producto, y 0 ventas"
        .format(x, med),
        ritmo_sem(c), "sigue gastando · aún sub-PD")

# ── C) cuenta saturada para un ángulo ────────────────────────────────────
ang_cta = collections.defaultdict(lambda: [0.0, 0])
for r in ventas:
    d = dim.get((r["producto_key"], r["conjunto"]))
    if not d:
        continue
    k = (r["producto_key"], d["angulo_key"], r["cuenta_alias"])
    ang_cta[k][0] += f(r["spend_usd"]); ang_cta[k][1] += i(r["ventas"])

# COBERTURA POR CUENTA: un CPA calculado sobre una cuenta mal trackeada SIEMPRE
# parece mejor, porque el numerador (gasto) está incompleto y el denominador
# (ventas) no. El 16-ago el motor mandó mover plata de GTR0 a CP1 porque CP1
# "pagaba Q27 contra Q60" — pero CP1 solo trackea el 27% de su gasto: corregido
# da Q100 contra Q111, prácticamente empate y ambos SOBRE el break-even.
# Comparar cuentas sin normalizar por cobertura es comparar peras con manzanas.
_cob_cta = {}
try:
    _pr_early = load("_FACT_PAUTA_REAL.csv")
except Exception:
    _pr_early = []
for _r in _pr_early:
    _re_, _tr_ = f(_r.get("spend_real_usd")), f(_r.get("spend_trackeado_usd"))
    if _re_ > 0:
        _cob_cta[_r.get("cuenta_alias")] = max(min(_tr_ / _re_, 1.0), 0.05)

por_ang = collections.defaultdict(list)
for (pk, ak, ca), (s, v) in ang_cta.items():
    g = s * TASA
    if g < 0.5 * BE.get(pk, 60.5):
        continue
    cob = _cob_cta.get(ca, 1.0)
    g_real = g / cob                       # gasto que Meta cobró de verdad
    por_ang[(pk, ak)].append({"cta": ca, "g": g, "v": v, "cob": cob,
                              "cpa": (g_real / v) if v else None,
                              "cpa_trk": (g / v) if v else None})

for (pk, ak), lst in por_ang.items():
    con = [x for x in lst if x["cpa"]]
    if len(con) < 2:
        continue
    mejor = min(con, key=lambda x: x["cpa"]); peor = max(con, key=lambda x: x["cpa"])
    if peor["cta"] == mejor["cta"] or peor["cpa"] < 2 * mejor["cpa"]:
        continue
    ahorro = peor["g"] - peor["v"] * mejor["cpa"]
    add(1, "REBALANCEAR", "crit", "Bajar a piso acá y mover el presupuesto a {}".format(mejor["cta"]),
        donde_angulo(pk, ak, peor["cta"]),
        "el MISMO ángulo paga {} en {} y {} en {} (CPA corregido por cobertura de "
        "tracking: {} ve el {}% de su gasto, {} el {}%) · {} se llevó {} para {} venta{}"
        .format(q1(peor["cpa"]), peor["cta"], q1(mejor["cpa"]), mejor["cta"],
                peor["cta"], round(peor["cob"] * 100), mejor["cta"], round(mejor["cob"] * 100),
                peor["cta"], q(peor["g"]), peor["v"], "s" if peor["v"] != 1 else ""),
        ahorro, "cuenta saturada")

# ── D) surfing sobre ganadores ───────────────────────────────────────────
for (pk, ca, cn), c in sorted(cj.items(), key=lambda x: -x[1]["v"]):
    if c["v"] < 2:
        continue
    g = c["sp"] * TASA; cpa = g / c["v"]
    be, base = BE.get(pk, 60.5), BASE_CPA.get(pk, 30.8)
    if cpa > base:
        continue
    if not any(d in ult3 and c["dias"][d][0] > 0 for d in c["dias"]):
        continue
    add(2, "ESCALAR", "good", "Subir +20% el presupuesto de este conjunto",
        donde_conjunto(pk, ca, cn),
        "CPA {} contra un break-even de {} · te deja {} limpios por venta"
        .format(q1(cpa), q1(be), q1(be - cpa)),
        (be - cpa) * c["v"], "listo para escalar")

# ── E) ganador infra-financiado ──────────────────────────────────────────
pauta_prod = collections.defaultdict(float)
for x in filas_ang:
    pauta_prod[x["producto"]] += x["pauta"]
for x in filas_ang:
    if not x["cpa"] or x["cpa"] > BASE_CPA.get(x["producto"], 30.8) or x["ventas"] < 3:
        continue
    share = x["pauta"] / pauta_prod[x["producto"]] if pauta_prod[x["producto"]] else 1
    if share >= 0.15:
        continue
    add(1, "ESCALAR", "good", "Meterle presupuesto — está asfixiado",
        " ; ".join(donde_angulo(x["producto"], x["angulo"], _c) for _c in sorted(
            {k[2] for k in _conj_de_ang if k[0] == x["producto"] and k[1] == x["angulo"]})) or
        "{} · ángulo {}".format(x["producto"], x["angulo"].replace("_", " ").title()),
        "el mejor CPA del producto ({}) y solo se lleva el {}% de la pauta"
        .format(q1(x["cpa"]), round(100 * share)),
        (x["be"] - x["cpa"]) * x["ventas"], "infra-financiado")

# ── F) renovar creativo ──────────────────────────────────────────────────
for x in filas_ang:
    if not x["cpa"] or x["ventas"] < 1 or x["cpa"] <= x["be"]:
        continue
    add(3, "RENOVAR", "warn", "Creativo nuevo del MISMO ángulo",
        " ; ".join(donde_angulo(x["producto"], x["angulo"], _c) for _c in sorted(
            {k[2] for k in _conj_de_ang if k[0] == x["producto"] and k[1] == x["angulo"]})) or
        "{} · ángulo {}".format(x["producto"], x["angulo"].replace("_", " ").title()),
        "vendió {} {} pero a {} (break-even {}) · el ángulo comunica, el creativo se gastó"
        .format(x["ventas"], "veces" if x["ventas"] != 1 else "vez", q1(x["cpa"]), q1(x["be"])),
        (x["cpa"] - x["be"]) * x["ventas"], "fatiga de creativo")

# ── I) diversidad conceptual (Andromeda) ─────────────────────────────────
# Meta ya no segmenta por audiencia: el CREATIVO es el targeting. Andromeda
# premia conceptos DISTINTOS — cada uno es una entrada de recuperación más.
# Un creativo duplicado ("- Copia") no cuenta: es el mismo anuncio dos veces.
# Benchmark 2026: 8-12 conceptos conceptualmente distintos por campaña.
_COPIA = re.compile(r"\s*-\s*Copia(\s*\d+)?\s*$", re.I)
camp = collections.defaultdict(lambda: {"conc": set(), "ads": set(), "sp": 0.0, "pk": ""})
for r in ventas:
    k = (r["producto_key"], r["campana"])
    c = camp[k]
    c["conc"].add(_COPIA.sub("", str(r["anuncio"])).strip().lower())
    c["ads"].add(str(r["anuncio"])); c["sp"] += f(r["spend_usd"]); c["pk"] = r["producto_key"]

# Solo las campañas que SIGUEN CORRIENDO y solo las 3 más flacas: esta regla
# aplica a casi todas las campañas a la vez, y diez filas iguales de prioridad
# baja tapan las dos acciones que de verdad mueven plata. Se prioriza por
# cuántos conceptos faltan, ponderado por lo que la campaña gasta.
_cand = []
for (pk, cam), c in camp.items():
    n = len(c["conc"])
    if c["sp"] * TASA < 150 or n >= 8:
        continue
    if _camp_viva and _norm(cam) not in _camp_viva:
        continue                      # campaña apagada: sumarle creativos no hace nada
    if _norm(cam) in _PAUSAS_CAMP_N:
        continue
    _cand.append(((8 - n) * c["sp"] * TASA, pk, cam, c, n))

for _, pk, cam, c, n in sorted(_cand, reverse=True)[:3]:
    add(3, "CREATIVOS", "warn", "Sumar {} concepto{} distinto{}".format(
            8 - n, "" if 8 - n == 1 else "s", "" if 8 - n == 1 else "s"),
        "{} → campaña «{}»".format(pk, cam),
        "corre con {} concepto{} distinto{} ({} anuncios, el resto son duplicados) · "
        "Andromeda premia 8-12 — cada concepto es una entrada más de recuperación, un duplicado no cuenta"
        .format(n, "" if n == 1 else "s", "" if n == 1 else "s", len(c["ads"])),
        0, "{} para llegar a 8".format(8 - n))
if len(_cand) > 3:
    add(3, "CREATIVOS", "warn", "Otras {} campañas también están por debajo de 8 conceptos".format(len(_cand) - 3),
        " · ".join("«{}»".format(x[2]) for x in sorted(_cand, reverse=True)[3:]),
        "mismo diagnóstico que las de arriba, pero mueven menos plata — atacalas después",
        0, "en cola")

# ── J) CUENTA QUE SI GASTA PERO SANGRA EN LA VENTANA RECIENTE ────────────
# La regla C) compara el mismo angulo entre cuentas sobre TODA la serie, asi que
# una cuenta que fue sana un mes y se rompio esta semana queda diluida y no sale.
# La regla I) solo agarra la cuenta que gasta CERO. Entre las dos quedaba un
# hueco: la cuenta que sigue gastando fuerte y ya no convierte.
# Caso 17-ago (GTR0): Q490 de pauta en la ventana 14-16 para 2 ventas -> CPA
# Q244.8 y Q-302 de ganancia, mientras GTR7 pagaba Q39 por el MISMO angulo
# PERDIDA_AUDITIVA. Ni C) ni I) lo veian. Causa probable: la cuenta arrastra
# rechazos de cobro (APR-049) y la entrega se le corta a cada rato.
# GUARDARRAIL: solo dispara con gasto material (>=1 break-even) y comparando
# contra el resto del portafolio EN LA MISMA VENTANA, para que la falta de
# maduracion COD afecte a todos por igual y no invente un culpable.
_cta_ult = collections.defaultdict(lambda: [0.0, 0, 0.0])   # cuenta -> [gasto Q, ventas, contribucion]
for r in ventas:
    if r["ventana_fin"] not in ult3:
        continue
    a = _cta_ult[r.get("cuenta_alias") or "?"]
    a[0] += f(r["spend_usd"]) * TASA
    a[1] += i(r["ventas"])
    a[2] += contribucion(r)

_g_tot = sum(x[0] for x in _cta_ult.values())
_v_tot = sum(x[1] for x in _cta_ult.values())
_cpa_port = (_g_tot / _v_tot) if _v_tot else None
for _ca, (_g, _v, _c) in sorted(_cta_ult.items(), key=lambda x: x[1][2] - x[1][0]):
    if _g < 60.5 or _c - _g >= 0:              # gasta poco, o no pierde plata
        continue
    if not _cpa_port:
        continue
    _cpa_ca = (_g / _v) if _v else None
    # tiene que ser peor que el portafolio de la MISMA ventana, no peor a secas
    if _cpa_ca is not None and _cpa_ca < 2 * _cpa_port:
        continue
    _det = ("CPA {} contra {} del portafolio en la misma ventana".format(q1(_cpa_ca), q1(_cpa_port))
            if _cpa_ca else "ni una venta en la ventana")
    add(1, "REBALANCEAR", "crit", "Bajar a piso esta cuenta y mover su presupuesto a las sanas",
        "{} · toda la cuenta".format(_ca),
        "gastó {} para {} venta{} y perdió {} · {} · revisar primero el método de pago "
        "y los rechazos de cobro antes de culpar al creativo (APR-049)"
        .format(q(_g), _v, "s" if _v != 1 else "", q(_g - _c), _det),
        _g - _c, "sangrando")

# ── L) ANGULO QUE VENDE PERO SANGRA EN LA VENTANA RECIENTE ───────────────
# Hueco real detectado el 18-ago. El motor solo sabe matar en CERO: la regla A)
# exige `not c["v"]` y la B) tambien. Un angulo que SI vende pero a 1.7x su
# break-even no lo agarra nadie -- y es peor que un cero, porque el cero al menos
# se detecta rapido mientras que este sigue comprando ventas caras en silencio.
# Ademas `_angulo_sano()` mide sobre TODA la serie, asi que un angulo que fue
# rentable un mes y se deterioro esta semana queda blindado por su propio pasado.
# El caso que la destapo (CLEARSTEM / ANTI_FALSIFICACION en GTR13) NO la dispara,
# y eso es CORRECTO: leido sobre los ultimos 6 dias da CPA Q159.8 contra un
# break-even de ~Q95 y parece que sangra, pero leido sobre la ventana ponderada
# del motor da Q102.9 -- practicamente en break-even. La diferencia es maduracion:
# la COD tarda ~3 dias y LucidSales reajusta retroactivo, asi que en el tramo mas
# reciente las VENTAS son un piso y el CPA es un techo (regla 5). Una regla que
# disparara con la lectura de 6 dias estaria matando angulos por data inmadura.
# Por eso L) lee la MISMA ventana que el resto del motor y exige 1.25x BE: quiere
# el angulo que sangra de forma sostenida, no el que todavia no termino de madurar.
# Es la version por ANGULO de la regla J) (que hace lo mismo por CUENTA).
# GUARDARRAILES: (1) agrega por `angulo_key`, nunca por conjunto -- las replicas
# R[N] se suman (regla 1, dispersion de Poisson); (2) exige gasto material
# (>=1 break-even) para no reaccionar a ruido; (3) exige perdida real en Q sobre
# la contribucion, no solo CPA feo; (4) exige que el CPA de la ventana supere el
# break-even con margen, no que empate.
_ang_ult = collections.defaultdict(lambda: [0.0, 0, 0.0])   # (pk, angulo) -> [gasto Q, ventas, contrib]
_ang_ult_cta = collections.defaultdict(lambda: collections.defaultdict(float))
for r in ventas:
    if r["ventana_fin"] not in ult3:
        continue
    d = dim.get((r["producto_key"], r["conjunto"]))
    if not d:
        continue
    _gq = f(r["spend_usd"]) * TASA
    a = _ang_ult[(r["producto_key"], d["angulo_key"])]
    a[0] += _gq
    a[1] += i(r["ventas"])
    a[2] += contribucion(r)
    _ang_ult_cta[(r["producto_key"], d["angulo_key"])][r.get("cuenta_alias") or "?"] += _gq

for (_pk, _ak), (_g, _v, _c) in sorted(_ang_ult.items(), key=lambda x: x[1][2] - x[1][0]):
    _be = BE.get(_pk, 60.5)
    if _v <= 0:                       # el cero ya lo cubren A) y B)
        continue
    if _g < _be:                      # gasto no material todavia: sigue bajo su PD
        continue
    _perdida = _g - _c
    if _perdida < 50:                 # no pierde plata de verdad en la ventana
        continue
    _cpa = _g / _v
    if _cpa < _be * 1.25:             # empata o roza el break-even: no es veredicto
        continue
    _g_ser, _v_ser = _ang_tot.get((_pk, _ak), [0.0, 0])
    _hist = ""
    if _v_ser and (_g_ser / _v_ser) < _be:
        _hist = (" · ojo: sobre toda la serie este ángulo da {} y parece sano — "
                 "lo que se rompió es la ventana reciente, no el ángulo entero"
                 .format(q1(_g_ser / _v_ser)))
    _cta_dom = max(_ang_ult_cta[(_pk, _ak)].items(), key=lambda x: x[1])[0] \
        if _ang_ult_cta.get((_pk, _ak)) else None
    add(1, "APAGAR", "crit", "Apagar este ángulo — vende, pero cada venta cuesta más de lo que deja",
        donde_angulo(_pk, _ak, _cta_dom),
        "gastó {} para {} venta{} = CPA {} contra un break-even de {} · te quitó {} "
        "en la ventana{}"
        .format(q(_g), _v, "s" if _v != 1 else "", q1(_cpa), q1(_be), q(_perdida), _hist),
        _perdida, "sangrando con ventas")

# ── N) BANDA DE EDAD QUE TRAE CONVERSACION Y NO CIERRA ───────────────────
# Hueco real detectado el 21-ago con el export de Ads Manager (APR-060). La
# banda de edad nunca se habia medido: el motor cortaba por angulo, cuenta,
# conjunto y concepto, pero no por `avatar_edad`. Resulta ser la variable mas
# cara del sistema. El experimento natural: PERDIDA_AUDITIVA, MISMO angulo,
# producto y creativo, a 25+ en GTR0 dio CPA Q473.6 (126 msj, 1 venta) y a
# 45-60 en GTR7 dio Q30.6 (90 msj, 11 ventas). Y con control DENTRO de la misma
# cuenta (GTR13, mismo producto y angulo): RESISTENCIA_INSULINA_SOP a 25-35
# vendio 3 sobre 21 mensajes y a 25+ vendio CERO sobre 33 -- la banda ancha
# genera MAS conversacion y MENOS venta.
# Por que compara CIERRE (ventas/mensajes) y no CPA: la banda mala no se delata
# por precio -- compra conversaciones igual de baratas (Q3.91 vs Q3.86 el
# mensaje). Se delata en el paso conversacion->venta. Es la regla 2 del sistema
# hecha rutina: la conversacion sirve para CORTAR, nunca para CORONAR.
# GUARDARRAILES: (1) compara bandas DENTRO del mismo producto -- entre productos
# no es comparable (en NUSAVA el 25+ rinde igual que el resto, y esta bien:
# su comprador si es transversal); (2) exige gasto >=1 break-even y >=25
# mensajes en la banda mala, para no reaccionar a ruido de Poisson; (3) exige
# que la banda buena tenga >=25 mensajes tambien; (4) la accion es CAMBIAR LA
# BANDA, nunca apagar el angulo -- por eso es REBALANCEAR y no APAGAR: el
# angulo puede estar sano y estar hablandole a quien no compra.
_edad = collections.defaultdict(lambda: [0.0, 0, 0])        # (pk, edad) -> [gasto Q, msj, ventas]
for r in ventas:
    if r["ventana_fin"] not in ult3:
        continue
    d = dim.get((r["producto_key"], r["conjunto"]))
    if not d:
        continue
    _e = (d.get("avatar_edad") or "").strip()
    if not _e or _e == "—":
        continue
    x = _edad[(r["producto_key"], _e)]
    x[0] += f(r["spend_usd"]) * TASA
    x[1] += i(r["mensajes"])
    x[2] += i(r["ventas"])

_por_prod = collections.defaultdict(list)
for (_pk, _e), v in _edad.items():
    _por_prod[_pk].append((_e, v))

for _pk, _bandas in sorted(_por_prod.items()):
    if len(_bandas) < 2:
        continue
    _be = BE.get(_pk, 60.5)
    _val = [(e, v) for e, v in _bandas if v[1] >= 25]       # bandas con muestra
    if len(_val) < 2:
        continue
    _cierre = lambda v: (v[2] / v[1]) if v[1] else 0.0
    _peor = min(_val, key=lambda x: _cierre(x[1]))
    _mejor = max(_val, key=lambda x: _cierre(x[1]))
    if _peor[0] == _mejor[0]:
        continue
    _cp, _cm = _cierre(_peor[1]), _cierre(_mejor[1])
    if _peor[1][0] < _be:                                   # gasto no material
        continue
    if _cm <= 0 or _cp > _cm / 2:                           # no es 2x peor
        continue
    # Impacto = las ventas que esas MISMAS conversaciones habrian dado al cierre
    # de la banda buena, menos las que dieron. No es "lo que gasto de mas": es lo
    # que la banda mala deja sobre la mesa con el trafico que ya pago.
    _perd = max((_peor[1][1] * _cm) - _peor[1][2], 0) * _be
    add(1, "REBALANCEAR", "crit",
        "Cambiar la banda de edad de {} a {} — trae conversación y no cierra".format(
            _peor[0], _mejor[0]),
        "{} · conjuntos segmentados {}".format(_pk, _peor[0]),
        "a {} cierra {}% de las conversaciones ({} venta{} sobre {} mensajes) y a {} "
        "cierra {}% ({} sobre {}) · misma plata por mensaje, {} de pauta en la banda "
        "que no compra"
        .format(_peor[0], round(100 * _cp, 1), _peor[1][2], "s" if _peor[1][2] != 1 else "",
                _peor[1][1], _mejor[0], round(100 * _cm, 1), _mejor[1][2], _mejor[1][1],
                q(_peor[1][0])),
        max(_perd, 0), "banda que no compra")

# ── K) EL PORTAFOLIO PASO SU TECHO DE GASTO DEMOSTRADO ───────────────────
# Escalar no es subir el numero: es subir el numero SIN que el CPA se vaya.
# Cuando el gasto/dia sube y el CPA sube con el, se esta comprando volumen que
# no existe. Caso 17-ago: la ventana 11-13 corrio Q597/dia con CPA Q47 y dejo
# Q+652/dia; la 14-16 corrio Q974/dia (+63%) con CPA Q75 y dejo Q+317/dia --
# 63% mas de plata compro 0.3 ventas mas por dia y la ganancia se partio al medio.
if len(dias_data) >= 2:
    _w = collections.defaultdict(lambda: [0.0, 0, 0.0, 1])
    for r in ventas:
        k = (r["ventana_ini"], r["ventana_fin"])
        a = _w[k]
        a[0] += f(r["spend_usd"]) * TASA
        a[1] += i(r["ventas"])
        a[2] += contribucion(r)
        a[3] = max(a[3], i(r.get("dias"), 1) or 1)
    _ord = [(k, v) for k, v in sorted(_w.items()) if v[0] > 0]
    if len(_ord) >= 2:
        (_ka, _a), (_kb, _b) = _ord[-2], _ord[-1]
        _ga, _gb = _a[0] / _a[3], _b[0] / _b[3]            # gasto/dia
        _va, _vb = _a[1] / _a[3], _b[1] / _b[3]            # ventas/dia
        _pa, _pb = (_a[2] - _a[0]) / _a[3], (_b[2] - _b[0]) / _b[3]   # ganancia/dia
        if _ga > 0 and _gb > _ga * 1.15 and _pb < _pa:
            add(1, "FRENAR", "crit", "Bajar el gasto a la banda que sí rendía, no subirlo",
                "portafolio · todas las cuentas",
                "la ventana {}→{} corrió {}/día y dejó {}/día · la {}→{} corrió {}/día "
                "(+{}%) y dejó {}/día · {} más de pauta compró {} ventas más por día"
                .format(_ka[0], _ka[1], q(_ga), q(_pa), _kb[0], _kb[1], q(_gb),
                        round(100 * (_gb / _ga - 1)), q(_pb),
                        q(_gb - _ga), round(_vb - _va, 1)),
                (_pa - _pb) * _b[3], "sobre el techo")

# ── M) TEST CONFIRMADO QUE NO ARRANCO ────────────────────────────────────
# Hueco real detectado el 21-ago. T01 estaba CONFIRMADO en `_TESTEOS.csv` con
# fecha_inicio 2026-08-20 y su angulo (ME_DIJERON_NO_CURA) gasto Q0 ese dia y
# los tres anteriores: el test no arranco Y el angulo que lo iba a alojar se
# apago. Ninguna regla lo agarraba — el motor mira gasto/ventas, nunca miro
# `_TESTEOS.csv`. Es una comprobacion DETERMINISTA (arranco o no arranco): no
# depende de maduracion ni de tamano de muestra, asi que no arrastra el riesgo
# de las reglas de matar.
try:
    _testeos = load("_TESTEOS.csv")
except Exception:
    _testeos = []
_hoy_iso = datetime.date.today().isoformat()
_tests = {}
for _t in _testeos:
    if (_t.get("estado") or "").strip().upper() != "CONFIRMADO":
        continue
    _fi = (_t.get("fecha_inicio") or "").strip()
    if not _fi or _fi > _hoy_iso:
        continue
    _k = (_t.get("test_id"), _t.get("producto_key"), _t.get("angulo_fijo"), _fi,
          _t.get("test_nombre"))
    _tests.setdefault(_k, set()).add(_t.get("brazo_key"))

for (_tid, _tpk, _tang, _tfi, _tnom), _brazos in sorted(_tests.items()):
    _sp = 0.0
    for r in ventas:
        if r["producto_key"] != _tpk or r["ventana_ini"] < _tfi:
            continue
        d = dim.get((r["producto_key"], r["conjunto"]))
        if d and d.get("angulo_key") == _tang:
            _sp += f(r["spend_usd"]) * TASA
    if _sp >= 1.0:                                  # arranco: hay gasto real
        continue
    _dias = 0
    try:
        _dias = (datetime.date.today() - datetime.date(*map(int, _tfi.split("-")))).days
    except Exception:
        pass
    add(1, "REVISAR", "bad",
        "El test {} figura CONFIRMADO pero no arrancó — o lanzalo o cambiale la fecha".format(_tid),
        "{} · ángulo {} · {} brazo{}".format(_tpk, _tang, len(_brazos),
                                             "s" if len(_brazos) != 1 else ""),
        "arrancaba el {}{} y su ángulo lleva Q0 de gasto desde esa fecha · "
        "«{}» · mientras figure CONFIRMADO sin correr, el sistema te cuenta un "
        "test que no existe y el ángulo que lo aloja está apagado"
        .format(_tfi, " (hace {} día{})".format(_dias, "s" if _dias != 1 else "") if _dias > 0 else "", _tnom),
        0, "no arrancó")

# ── H) data ──────────────────────────────────────────────────────────────
falt = 0
if ult_dia:
    try:
        falt = (datetime.date.today() - datetime.date(*map(int, ult_dia.split("-")))).days - 1
    except Exception:
        falt = 0
    if falt > 0:
        add(2, "DATA", "warn", "Pegar el export de LucidSales",
            "{} día{} sin cargar".format(falt, "s" if falt != 1 else ""),
            "el último día cerrado es {} · sin eso el CPA semanal queda incompleto".format(ult_dia),
            0, "pendiente")

# ── P) el hueco de data cruzó el ciclo de maduración de la COD ───────────
# Hueco real detectado el 24-ago, en la 4ª noche seguida sin export.
#
# La regla H) trata un hueco de 1 día y uno de 4 exactamente igual: prioridad 2,
# impacto Q0, y por eso se hunde al fondo de la lista. Pero el costo de un hueco
# NO es lineal — tiene un punto de quiebre concreto:
#
#   La venta COD madura ~3 días (memoria: guatemala-entrega-cod-3-dias) y
#   LucidSales la reajusta retroactivo. Mientras el hueco es < 3 días, el último
#   export todavía describe algo real. En cuanto el hueco IGUALA al ciclo de
#   maduración, el sistema pierde la capacidad de distinguir "todavía no maduró"
#   de "está cayendo": las dos hipótesis producen exactamente la misma tabla.
#   Ahí el dashboard deja de ser una lectura vieja y pasa a ser una lectura
#   AMBIGUA — y todas las demás acciones de la lista se apoyan en ella.
#
# El impacto NO es "ventas perdidas" (la plata se gastó y las ventas ocurrieron;
# lo que se perdió es la capacidad de decidir). Se cuantifica como el dinero que
# pasó por el portafolio SIN MEDIRSE: días de hueco × pauta/día del último ritmo
# conocido. Ese es el tamaño de la apuesta a ciegas, y es la única cifra honesta
# que justifica subir esto a prioridad 1.
#
# ⚠️ CORRECCIÓN 25-ago (APR-068) — POR QUÉ ESTA ACCIÓN VA EN UNA BANDA APARTE.
# El 24-ago esta regla salió PRIMERA y se dio por resuelto el problema. Salió
# primera por casualidad: la lista ordena por (prioridad, -impacto) y ese día su
# Q1,420 le ganaba a todo lo demás. Al día siguiente, con el hueco MÁS GRANDE
# (4d, Q1,893), cayó al segundo puesto porque una acción de TINNIDROP subió a
# Q2,363. O sea: la posición de la alerta de ceguera se movía por razones que no
# tienen NADA que ver con qué tan ciego está el sistema.
#
# La causa es que se estaban comparando dos magnitudes que no viven en el mismo
# eje. El impacto de las demás reglas es dinero RECUPERABLE por semana si el
# operador actúa. El de ésta es dinero YA GASTADO sin medirse — no se recupera
# tocándola; es el tamaño de la incertidumbre. Ordenarlas juntas es sumar peras
# con manzanas y dejar que el resultado decida qué se lee primero.
#
# Una acción de GATE no compite por la plata: la CONDICIONA. Todas las filas de
# abajo se calculan sobre la ventana que esta regla declara ambigua, así que
# leerlas antes que a ella es actuar sobre números cuya confiabilidad todavía no
# se evaluó. Por eso va a prioridad 0, una banda por ENCIMA de "hoy", donde no
# ordena por magnitud y no puede ser desplazada por ninguna cifra.
if falt >= 3 and ult3:
    _sp = sum(f(r["spend_usd"]) for r in ventas if r["ventana_fin"] in ult3)
    _dd = sum(i(r["dias"], 1) for r in ventas if r["ventana_fin"] in ult3 and r["conjunto"])
    _pts = sum(i(d, 1) for d in
               {r["ventana_fin"]: r["dias"] for r in ventas if r["ventana_fin"] in ult3}.values())
    _pauta_dia = (_sp * TASA / _pts) if _pts else 0.0
    add(0, "DATA", "crit", "El dashboard ya no distingue maduración de caída",
        "{} días sin export · último cierre {}".format(falt, ult_dia),
        "el hueco ({}d) igualó al ciclo de maduración de la COD (~3d): un ángulo en cero "
        "puede ser una venta que no maduró o una que dejó de entrar, y las dos se ven igual. "
        "Pasaron ~Q{:,.0f} de pauta sin medirse (Q{:,.0f}/día del último ritmo). Todas las "
        "demás acciones de esta lista se apoyan en esa ventana".format(
            falt, falt * _pauta_dia, _pauta_dia),
        round(falt * _pauta_dia), "pendiente")

# ── Q) la tabla del lado-ads se congeló (MCP caído) ──────────────────────
# Mismo principio que APR-066: una regla que no puede avisar de su propia
# ceguera está mal construida. `_FACT_ENTREGA.csv` es la ÚNICA fuente de
# frecuencia/fatiga, estado de cuenta y verificación de ejecución. Cuando el
# MCP se cae la tabla no se vacía — se queda quieta, y nada en el dashboard
# lo dice. Impacto Q0 a propósito: no hay plata directa en juego, pero sí
# tres reglas del motor corriendo sobre data vieja sin declararlo.
if entrega:
    _ent_dia = max((r.get("ventana_fin") or "" for r in entrega), default="")
    try:
        _ent_falt = (datetime.date.today() -
                     datetime.date(*map(int, _ent_dia.split("-")))).days - 1
    except Exception:
        _ent_falt = 0
    if _ent_falt >= 2:
        add(2, "DATA", "warn", "Reconectar Meta Ads (lado-ads congelado)",
            "{} días sin lectura · última {}".format(_ent_falt, _ent_dia),
            "sin _FACT_ENTREGA fresco no hay frecuencia (no se detecta fatiga), no se "
            "verifica ACTIVE/UNSETTLED de ninguna cuenta y no se confirma si las acciones "
            "de abajo ya se ejecutaron. Las reglas C), I) y F) corren sobre data de {}".format(_ent_dia),
            0, "pendiente")

acciones.sort(key=lambda a: (a["pri"], -a["impacto"]))
q_juego = sum(a["impacto"] for a in acciones if a["tipo"] in ("APAGAR", "REBALANCEAR", "REACTIVAR"))
n_urgentes = sum(1 for a in acciones if a["pri"] <= 1)


# ── cortes por dimension ─────────────────────────────────────────────────
def corte(col, pk=None):
    a = collections.defaultdict(lambda: [0.0, 0])
    for r in ventas:
        if pk and r["producto_key"] != pk:
            continue
        d = dim.get((r["producto_key"], r["conjunto"]))
        if not d:
            continue
        k = d.get(col) or "—"
        a[k][0] += f(r["spend_usd"]); a[k][1] += i(r["ventas"])
    out = [{"k": k, "v": v, "g": s * TASA, "cpa": (s * TASA / v) if v else None} for k, (s, v) in a.items()]
    return sorted(out, key=lambda x: (x["cpa"] is None, x["cpa"] or 0))

cortes = [("Emoción dominante", "emocion_dominante", "qué SIENTE el que compra"),
          ("Tipo de hook", "tipo_hook", "cómo se le entra"),
          ("A quién le habla", "avatar_genero", "el creativo elige la audiencia"),
          ("Edad del avatar", "avatar_edad", "a qué edad le pega"),
          ("Formato", "formato", "¿video o imagen?"),
          ("Rol de embudo", "rol_embudo", "dónde está el cuello"),
          ("Precio en el ad", "lleva_precio", "¿filtra o espanta?")]

# ── vista DIARIA (una fila por dia x producto) ───────────────────────────
# Se llena con los exports de 1 dia. Mientras solo haya ventanas agregadas,
# muestra la ventana entera y lo dice.
dia = collections.defaultdict(lambda: [0.0, 0, 0.0, 0.0])
for r in ventas:
    k = (r["ventana_fin"], r["producto_key"], r["dias"])
    dia[k][0] += f(r["spend_usd"]); dia[k][1] += i(r["ventas"])
    dia[k][2] += f(r["total_q"]); dia[k][3] += contribucion(r)

filas_dia = []
for (fecha, pk, dias), (sp, v, ing, contrib) in sorted(dia.items(), reverse=True):
    g = sp * TASA
    be, base = BE.get(pk, 60.5), BASE_CPA.get(pk, 30.8)
    cpa = g / v if v else None
    gan = contrib - g
    if cpa is None:
        sev, vs = "crit", "sin ventas"
    elif cpa <= base:
        sev, vs = "good", "bajo el objetivo"
    elif cpa <= be:
        sev, vs = "warn", "bajo break-even"
    else:
        sev, vs = "crit", "sobre break-even"
    filas_dia.append({"fecha": fecha, "producto": pk, "dias": i(dias, 1), "ventas": v,
                      "usd": sp, "gtq": g, "cpa": cpa, "be": be, "base": base,
                      "gan_und": (be - cpa) if cpa else None, "gan": gan,
                      "sev": sev, "vs": vs, "ingreso": ing})
agregadas = sum(1 for x in filas_dia if x["dias"] > 1)
# la tabla día-a-día crece para siempre: se muestran los últimos 14 días
_dias_vis = sorted({x["fecha"] for x in filas_dia}, reverse=True)[:14]
filas_dia_ocultas = len([x for x in filas_dia if x["fecha"] not in _dias_vis])
filas_dia = [x for x in filas_dia if x["fecha"] in _dias_vis]

# ── HTML ─────────────────────────────────────────────────────────────────
hoy = datetime.date.today().isoformat()

def sev_chip(sev, txt):
    return '<span class="chip chip--{}">{}</span>'.format(sev, esc(txt))

rows_pl = "".join(
    '<tr><th scope="row">{p}</th><td class="num">{v}</td><td class="num">{pa}</td>'
    '<td class="num">{ing}</td><td class="num">{cpa}</td><td class="num muted">{be}</td>'
    '<td class="num strong {cls}">{gan}</td></tr>'.format(
        p=esc(r["producto"]), v=r["ventas"], pa=q(r["pauta"]), ing=q(r["ingreso"]),
        cpa=q1(r["cpa"]) if r["cpa"] else "—", be=q1(r["be"]),
        cls="pos" if r["ganancia"] >= 0 else "neg",
        gan=("+" if r["ganancia"] >= 0 else "") + q(r["ganancia"]))
    for r in filas_pl)

rows_ang = "".join(
    '<tr><td><span class="ang">{a}</span><span class="sub">{p} · {h}{c}</span></td>'
    '<td class="num">{v}{nb}</td><td class="num">{pa}</td><td class="num strong">{cpa}</td>'
    '<td><div class="bar" style="--pct:{pd}%"><span></span></div><span class="sub">{pd}% PD</span></td>'
    '<td>{chip}</td></tr>'.format(
        a=esc(r["angulo"].replace("_", " ").title()), p=esc(r["producto"]), h=esc(r["hook"].replace("_", " ").lower()),
        c=" · {} cuentas".format(r["cuentas"]) if r["cuentas"] > 1 else "",
        v=r["ventas"], nb='<span class="flag" title="n bajo: IC ±88% o peor">n bajo</span>' if r["n_bajo"] else "",
        pa=q(r["pauta"]), cpa=q1(r["cpa"]) if r["cpa"] else "—", pd=r["pd"],
        chip=sev_chip(r["sev"], r["estado"]))
    for r in filas_ang)

_TIPO_ICON = {"APAGAR": "⏻", "REACTIVAR": "▶", "REBALANCEAR": "⇄", "CREATIVOS": "✦",
              "ESCALAR": "▲", "RENOVAR": "↻", "DATA": "◧"}
_PRI_TXT = {0: "primero", 1: "hoy", 2: "esta semana", 3: "cuando puedas", 4: "hecho"}

rows_acc = "".join(
    '<tr class="acc acc--{sev}" data-k="{key}">'
    '<td class="accx"><button class="tick" title="Marcar como hecho">✓</button></td>'
    '<td class="accp"><span class="prio prio--{pri}">{pt}</span></td>'
    '<td><span class="accq">{ic} {que}</span><span class="sub">{donde}</span></td>'
    '<td class="accw"><span class="sub">{porque}</span></td>'
    '<td class="num strong {icls}">{imp}</td>'
    '<td><span class="chip chip--{sev}">{est}</span></td></tr>'.format(
        sev=a["sev"], pri=a["pri"], pt=esc(_PRI_TXT[a["pri"]]),
        key=esc(hashlib.md5((a["tipo"] + "|" + a["donde"]).encode("utf-8")).hexdigest()[:10]),
        ic=_TIPO_ICON.get(a["tipo"], "•"), que=esc(a["que"]), donde=esc(a["donde"]),
        porque=esc(a["porque"]),
        icls="pos" if a["tipo"] in ("ESCALAR",) else ("neg" if a["impacto"] else "muted"),
        imp=(q(a["impacto"]) + "<small>/sem</small>") if a["impacto"] >= 1 else "—",
        est=esc(a["estado"]))
    for a in acciones) or ('<tr><td colspan="6" class="sub">Nada pendiente: ningún conjunto pasó '
                           'su PD sin vender, ninguna cuenta está saturada y no hay ganadores sin presupuesto.</td></tr>')

rows_sang = "".join(
    '<tr><th scope="row">{c}</th><td class="sub">{p} · {ct}</td>'
    '<td class="num strong neg">{g}</td><td class="num">{pd}%</td></tr>'.format(
        c=esc(r["conjunto"][:44]), p=esc(r["producto"]), ct=esc(r["cuenta"]),
        g=q(r["pauta"]), pd=r["pd"])
    for r in sangrado) or '<tr><td colspan="4" class="sub">Sin sangrado — ningún conjunto pasó su PD con 0 ventas.</td></tr>'

def bloque_corte(titulo, col, hint, pk=None):
    d = [x for x in corte(col, pk) if x["v"] or x["g"] > 30]
    mx = max([x["cpa"] for x in d if x["cpa"]] or [1])
    filas = "".join(
        '<li><span class="ck">{k}</span>'
        '<span class="cbar"><span style="--w:{w}%"></span></span>'
        '<span class="cv">{cpa}<small>{v}v</small></span></li>'.format(
            k=esc(x["k"].replace("_", " ").lower()),
            w=round(100 * x["cpa"] / mx) if x["cpa"] else 100,
            cpa=q1(x["cpa"]) if x["cpa"] else "0 ventas", v=x["v"])
        for x in d)
    return ('<article class="corte"><h3>{t}</h3><p class="sub">{h}</p><ul class="clist">{f}</ul></article>'
            .format(t=esc(titulo), h=esc(hint), f=filas or '<li class="sub">sin data</li>'))


def veredicto_producto(pk):
    """Una frase por producto: qué tipo de hook, formato y embudo le funciona."""
    partes = []
    for col, etq in (("emocion_dominante", ""), ("avatar_genero", ""),
                     ("avatar_edad", "años"), ("formato", "")):
        d = [x for x in corte(col, pk) if x["cpa"] and x["v"] >= 2]
        if not d:
            continue
        mejor = d[0]
        txt = mejor["k"].replace("_", " ").lower()
        partes.append('<strong>{}</strong>{} <span class="vq">{}</span>'.format(
            esc(txt), (" (" + etq + ")") if etq else "", q1(mejor["cpa"])))
    return " · ".join(partes) if partes else "todavía sin ventas suficientes para cortar"

rows_dia = "".join(
    '<tr><th scope="row">{fe}{tag}</th><td>{p}</td><td class="num">{v}</td>'
    '<td class="num muted">${usd}</td><td class="num">{gtq}</td>'
    '<td class="num strong">{cpa}</td><td class="num muted">{base}</td><td class="num muted">{be}</td>'
    '<td class="num {gc}">{gu}</td><td class="num strong {gc}">{gan}</td><td>{chip}</td></tr>'.format(
        fe=esc(r["fecha"]),
        tag='<span class="flag">{}d</span>'.format(r["dias"]) if r["dias"] > 1 else "",
        p=esc(r["producto"]), v=r["ventas"], usd="{:,.2f}".format(r["usd"]), gtq=q(r["gtq"]),
        cpa=q1(r["cpa"]) if r["cpa"] else "—", base=q1(r["base"]), be=q1(r["be"]),
        gu=q1(r["gan_und"]) if r["gan_und"] is not None else "—",
        gc="pos" if r["gan"] >= 0 else "neg",
        gan=("+" if r["gan"] >= 0 else "") + q(r["gan"]),
        chip=sev_chip(r["sev"], r["vs"]))
    for r in filas_dia)

_fila_de = {}
for k, v_ in prods.items():
    if v_.get("fila_costeo_q"):
        _fila_de.setdefault(v_["fila_costeo_q"], []).append(k)

_ARR_CHIP = {"2X1": ("crit", "arrancar en 2x1"),
             "CRITERIO": ("warn", "según categoría"),
             "1U": ("good", "1 unidad")}


def _celda_tier(t, atenuar=False):
    u, precio, costo_tot = t
    c = contrib_tier(precio, costo_tot, u)
    return ('<td class="num{off}"><span class="tp">Q{p:.0f}</span>'
            '<span class="tb">Q{b:.0f}</span></td>').format(
                p=precio, b=c, off=" tier-off" if atenuar else "")


rows_cost = ""
for costo_u in range(30, 135, 5):
    arr, mult = arranque_recomendado(costo_u)
    sev, txt = _ARR_CHIP[arr]
    tiers = escalera_sugerida(costo_u, precio_1u(costo_u))
    base = _CPA_BASE_TABLA.get(costo_u, _CPA_BASE_TABLA.get(
        min(_CPA_BASE_TABLA, key=lambda k: abs(k - costo_u)), 30.8))
    rows_cost += (
        '<tr class="{cls}"><th scope="row">Q{c}{us}</th>'
        '{celdas}'
        '<td class="num muted">{mult:.1f}×</td>'
        '<td>{chip}</td><td class="num strong">{base}</td></tr>'.format(
            cls="hl" if str(costo_u) in _fila_de else "",
            c=costo_u,
            us='<span class="use">{}</span>'.format(" · ".join(_fila_de[str(costo_u)])) if str(costo_u) in _fila_de else "",
            celdas="".join(_celda_tier(t, atenuar=(arr == "2X1" and t[0] == 1)) for t in tiers),
            mult=mult, chip=sev_chip(sev, txt), base=q1(base)))

te = tasa_ent[-1] if tasa_ent else None
te_html = ""
if te:
    te_html = (
        '<div class="card" style="padding:16px 18px;display:grid;gap:12px;'
        'grid-template-columns:repeat(auto-fit,minmax(150px,1fr))">'
        '<div><div class="k2">Entrega (sobre resueltos)</div><div class="v2 pos">{ent}%</div></div>'
        '<div><div class="k2">Devolución real</div><div class="v2">{dev}%</div></div>'
        '<div><div class="k2">Devolución asumida</div><div class="v2 muted">{asu}%</div></div>'
        '<div><div class="k2">En tránsito</div><div class="v2 muted">{tr}</div></div>'
        '<div><div class="k2">Mes</div><div class="v2 muted">{mes}</div></div>'
        '</div>'
        '<p class="sub" style="margin:9px 0 0">⚠️ El % de «ENTREGADO» que muestra Dropi es sobre el TOTAL e '
        'incluye pedidos <strong>en tránsito</strong> — leerlo como tasa de entrega subestima el negocio. '
        'La cifra que importa se calcula sobre estados <strong>resueltos</strong>.</p>'
    ).format(ent=te["pct_entrega_resueltos"], dev=te["pct_devolucion_resueltos"],
             asu=te["pct_devolucion_asumido"], tr=te["en_transito"], mes=esc(te["mes"]))

bloques = "".join(bloque_corte(t, c, h) for t, c, h in cortes)

# mismo corte pero POR PRODUCTO — "¿este producto vende por miedo o por oferta?"
_orden_pk = [x["producto"] for x in filas_pl]
bloques_pk = "".join(
    '<details class="prodcut"><summary><span class="pkn">{pk}</span>'
    '<span class="pkv">{ver}</span></summary><div class="cortes">{b}</div></details>'.format(
        pk=esc(pk), ver=veredicto_producto(pk),
        b="".join(bloque_corte(t, c, h, pk) for t, c, h in cortes))
    for pk in _orden_pk)

rows_apr = "".join(
    '<li class="apr apr--{cf}"><div class="aprh"><code>{id}</code>{chip}'
    '<span class="sub">{sc}</span></div><p>{regla}</p><p class="ev">{ev}</p></li>'.format(
        cf=a["confianza"].lower(), id=esc(a["id"]),
        chip='<span class="chip chip--{}">{}</span>'.format(
            {"ALTA": "good", "MEDIA": "warn", "BAJA": "muted"}[a["confianza"]], a["confianza"].lower()),
        sc=esc(a["producto_key"] or a["alcance"].lower()),
        regla=esc(a["regla"]), ev=esc(a["evidencia_metrica"][:190]))
    for a in sorted(aprend, key=lambda x: {"ALTA": 0, "MEDIA": 1, "BAJA": 2}[x["confianza"]]))

# integridad = SOLO los últimos 7 días (antes contaba toda la historia y
# arrastraba días viejos que ya no se pueden ni recuperar)
_hoy = datetime.date.today()
_ult7 = [(_hoy - datetime.timedelta(d)).isoformat() for d in range(1, 8)]
# un día está CUBIERTO si tiene export diario propio o si cae dentro de una
# ventana agregada ya cargada (el baseline de 7 días también cuenta)
_con = set(dias_data)
for r in ventas:
    n = i(r["dias"], 1)
    if n <= 1:
        continue
    try:
        fin = datetime.date(*map(int, r["ventana_fin"].split("-")))
    except Exception:
        continue
    for k in range(n):
        _con.add((fin - datetime.timedelta(k)).isoformat())
faltan7 = [d for d in _ult7 if d not in _con]


def _dm(s):
    return "{}/{}".format(int(s[8:10]), int(s[5:7]))


integridad_sev = "good" if not faltan7 else ("warn" if len(faltan7) <= 2 else "crit")
integridad_txt = ("últimos 7 días completos" if not faltan7 else
                  "faltan {} de los últimos 7: <strong>{}</strong>".format(
                      len(faltan7), " · ".join(_dm(x) for x in sorted(faltan7))))

DOC = u"""<title>Portafolio VitalCom · Panel</title>
<style>
:root{
  --ground:#F4F6FA; --surface:#FFFFFF; --line:#DDE2EC; --line-soft:#EBEEF5;
  --ink:#1A2338; --ink-2:#5A657F; --ink-3:#8892A8;
  --accent:#3B4E8C; --accent-soft:#EDF0F9;
  --good:#1F7A4D; --good-bg:#E6F2EA;
  --warn:#8A6100; --warn-bg:#F7EFDC;
  --crit:#AE3A31; --crit-bg:#F8E8E6;
  --radius:10px;
  --serif:ui-serif,Georgia,'Iowan Old Style','Times New Roman',serif;
  --sans:system-ui,-apple-system,'Segoe UI',Roboto,sans-serif;
  --mono:ui-monospace,'SF Mono','Cascadia Code','Roboto Mono',monospace;
}
@media (prefers-color-scheme:dark){
  :root{
    --ground:#0E1220; --surface:#161B2C; --line:#2A3145; --line-soft:#212739;
    --ink:#DFE4F0; --ink-2:#9BA5BF; --ink-3:#6E7893;
    --accent:#93A6E0; --accent-soft:#1D2438;
    --good:#5FBF8A; --good-bg:#152A20;
    --warn:#D6A63F; --warn-bg:#2B2415;
    --crit:#E0776C; --crit-bg:#2E1B19;
  }
}
:root[data-theme="dark"]{
  --ground:#0E1220; --surface:#161B2C; --line:#2A3145; --line-soft:#212739;
  --ink:#DFE4F0; --ink-2:#9BA5BF; --ink-3:#6E7893;
  --accent:#93A6E0; --accent-soft:#1D2438;
  --good:#5FBF8A; --good-bg:#152A20;
  --warn:#D6A63F; --warn-bg:#2B2415;
  --crit:#E0776C; --crit-bg:#2E1B19;
}
:root[data-theme="light"]{
  --ground:#F4F6FA; --surface:#FFFFFF; --line:#DDE2EC; --line-soft:#EBEEF5;
  --ink:#1A2338; --ink-2:#5A657F; --ink-3:#8892A8;
  --accent:#3B4E8C; --accent-soft:#EDF0F9;
  --good:#1F7A4D; --good-bg:#E6F2EA;
  --warn:#8A6100; --warn-bg:#F7EFDC;
  --crit:#AE3A31; --crit-bg:#F8E8E6;
}
*{box-sizing:border-box}
body{margin:0;background:var(--ground);color:var(--ink);font-family:var(--sans);
  font-size:15px;line-height:1.55;-webkit-font-smoothing:antialiased}
.wrap{max-width:1080px;margin:0 auto;padding:28px 20px 72px;
  display:flex;flex-direction:column;gap:34px}
.num{font-family:var(--mono);font-variant-numeric:tabular-nums;text-align:right;white-space:nowrap}
.strong{font-weight:600}
.muted{color:var(--ink-3)}
.sub{color:var(--ink-2);font-size:12.5px}
.pos{color:var(--good)} .neg{color:var(--crit)} .warn{color:#b7791f}
.ajuste{display:flex;align-items:center;gap:22px;margin-top:14px;padding:16px 18px;
  border:1px solid var(--line);border-radius:12px;background:var(--card);flex-wrap:wrap}
.ajuste .lbl{font-size:12px;text-transform:uppercase;letter-spacing:.06em;color:var(--muted)}
.ajuste .v{font-size:26px;font-weight:700;line-height:1.25}
.ajuste .arrow{font-size:24px;color:var(--muted)}
.ajuste .sub{margin:2px 0 0}

/* encabezado */
header{display:flex;flex-wrap:wrap;align-items:baseline;gap:10px 16px;
  padding-bottom:18px;border-bottom:2px solid var(--ink)}
header h1{font-family:var(--serif);font-size:23px;font-weight:600;margin:0;letter-spacing:-.01em}
header .meta{color:var(--ink-2);font-size:13px;font-family:var(--mono)}
.spacer{flex:1}
a.nav{text-decoration:none;color:var(--accent);border:1px solid var(--line);border-radius:99px;
  padding:5px 13px;font-size:13px;background:var(--accent-soft);white-space:nowrap}
a.nav:hover{border-color:var(--accent)}

/* barra de integridad */
.integridad{display:flex;align-items:center;gap:10px;padding:11px 14px;border-radius:var(--radius);
  border:1px solid var(--line);background:var(--surface);font-size:13.5px}
.integridad .dot{width:9px;height:9px;border-radius:50%;flex:none}
.integridad--good .dot{background:var(--good)} .integridad--good{border-left:3px solid var(--good)}
.integridad--warn .dot{background:var(--warn)} .integridad--warn{border-left:3px solid var(--warn)}
.integridad--crit .dot{background:var(--crit)} .integridad--crit{border-left:3px solid var(--crit)}

/* hero */
.hero{background:var(--surface);border:1px solid var(--line);border-radius:var(--radius);
  padding:26px 24px;display:grid;grid-template-columns:minmax(0,1.15fr) minmax(0,1fr);gap:28px;align-items:center}
.hero .big{font-family:var(--serif);font-size:clamp(40px,8vw,60px);line-height:1;font-weight:600;
  letter-spacing:-.02em;font-variant-numeric:tabular-nums}
.hero .lbl{text-transform:uppercase;letter-spacing:.09em;font-size:11px;color:var(--ink-2);
  font-weight:600;margin-bottom:6px}
.kpis{display:grid;grid-template-columns:repeat(3,1fr);gap:18px}
.kpi .v{font-family:var(--mono);font-size:20px;font-variant-numeric:tabular-nums;font-weight:600}
.kpi .k{font-size:11.5px;color:var(--ink-2);text-transform:uppercase;letter-spacing:.05em}

/* secciones */
tr.wk td{border-top:2px solid var(--line);background:rgba(0,0,0,.02)}
section h2{font-family:var(--serif);font-size:18px;font-weight:600;margin:0 0 3px;letter-spacing:-.01em}
section > .sub{margin:0 0 14px}
.card{background:var(--surface);border:1px solid var(--line);border-radius:var(--radius);overflow:hidden}
.scroll{overflow-x:auto}
table{width:100%;border-collapse:collapse;font-size:14px;min-width:520px}
th,td{padding:10px 14px;text-align:left;border-bottom:1px solid var(--line-soft)}
thead th{font-size:11px;text-transform:uppercase;letter-spacing:.07em;color:var(--ink-2);
  font-weight:600;background:var(--accent-soft);border-bottom:1px solid var(--line)}
thead th.num{text-align:right}
tbody tr:last-child td,tbody tr:last-child th{border-bottom:none}
tbody th{font-weight:600}
tfoot td,tfoot th{border-top:2px solid var(--line);font-weight:700;background:var(--accent-soft)}

.chip{display:inline-block;padding:2px 9px;border-radius:99px;font-size:11.5px;font-weight:600;white-space:nowrap}
.chip--good{background:var(--good-bg);color:var(--good)}
.chip--warn{background:var(--warn-bg);color:var(--warn)}
.chip--crit{background:var(--crit-bg);color:var(--crit)}
.chip--muted{background:var(--accent-soft);color:var(--ink-2)}
.flag{display:inline-block;margin-left:6px;font-size:10px;color:var(--warn);
  border:1px solid var(--warn);border-radius:3px;padding:0 4px;font-family:var(--sans);vertical-align:1px}
.ang{display:block;font-weight:600;font-size:14px}

/* barra de PD */
.bar{width:72px;height:5px;border-radius:3px;background:var(--line);overflow:hidden;margin-bottom:3px}
.bar span{display:block;height:100%;width:var(--pct);background:var(--accent);border-radius:3px}

/* cortes */
.cortes{display:grid;grid-template-columns:repeat(auto-fit,minmax(248px,1fr));gap:14px}
.corte{background:var(--surface);border:1px solid var(--line);border-radius:var(--radius);padding:16px 18px}
.corte h3{font-size:13px;margin:0;text-transform:uppercase;letter-spacing:.06em;color:var(--accent)}
.corte .sub{margin:2px 0 12px}
.clist{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:9px}
.clist li{display:grid;grid-template-columns:1fr 52px auto;gap:9px;align-items:center;font-size:13px}
.ck{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.cbar{height:4px;background:var(--line);border-radius:2px;overflow:hidden}
.cbar span{display:block;height:100%;width:var(--w);background:var(--accent);opacity:.75}
.cv{font-family:var(--mono);font-variant-numeric:tabular-nums;font-size:12.5px;text-align:right;white-space:nowrap}
.cv small{color:var(--ink-3);margin-left:5px;font-size:11px}

/* aprendizajes */
.aprs{list-style:none;margin:0;padding:0;display:grid;gap:10px}
.apr{background:var(--surface);border:1px solid var(--line);border-left:3px solid var(--ink-3);
  border-radius:var(--radius);padding:13px 16px}
.apr--alta{border-left-color:var(--good)}
.apr--media{border-left-color:var(--warn)}
.apr--baja{border-left-color:var(--ink-3)}
.aprh{display:flex;align-items:center;gap:9px;flex-wrap:wrap;margin-bottom:5px}
.apr code{font-family:var(--mono);font-size:11.5px;color:var(--accent);font-weight:600}
.apr p{margin:0;font-size:13.5px}
.apr .ev{color:var(--ink-2);font-size:11.5px;font-family:var(--mono);margin-top:5px;line-height:1.45}

/* plan de acción */
.plan{border:2px solid var(--ink);border-radius:var(--radius);background:var(--surface);overflow:hidden}
.planh{display:flex;flex-wrap:wrap;align-items:baseline;gap:8px 14px;padding:15px 18px;
  border-bottom:1px solid var(--line);background:var(--accent-soft)}
.planh h2{margin:0;font-family:var(--serif);font-size:18px;font-weight:600}
.planh .n{font-family:var(--mono);font-size:13px;font-weight:600;color:var(--crit)}
.plan table{min-width:640px}
.plan thead th{background:transparent}
tr.acc td{vertical-align:top;border-left:3px solid transparent}
tr.acc--crit td:first-child{border-left-color:var(--crit)}
tr.acc--warn td:first-child{border-left-color:var(--warn)}
tr.acc--good td:first-child{border-left-color:var(--good)}
tr.acc--done td:first-child{border-left-color:var(--mut,#c9c9c9)}
tr.acc--done{opacity:.45}
.prio--4{background:#eee;color:#777}
.chip--done{background:#eee;color:#666}
.accp{width:1%;white-space:nowrap;padding-right:4px}
.prio{display:inline-block;font-size:10.5px;font-weight:700;text-transform:uppercase;
  letter-spacing:.06em;padding:2px 7px;border-radius:4px;white-space:nowrap}
.prio--0{background:var(--crit);color:#fff;font-weight:700}
.prio--1{background:var(--crit-bg);color:var(--crit)}
.prio--2{background:var(--warn-bg);color:var(--warn)}
.prio--3{background:var(--accent-soft);color:var(--ink-2)}
.accq{display:block;font-weight:600;font-size:14px;margin-bottom:2px}
.accw{max-width:34ch}
.acc .num small{color:var(--ink-3);font-weight:400;margin-left:3px;font-size:10px}
@media (max-width:720px){.accw{max-width:none}}

/* tabla maestra de precios: precio arriba, break-even abajo */
.tp{display:block;font-weight:600}
.tier-off{opacity:.32}
.tier-off .tp{text-decoration:line-through}
.tb{display:block;font-size:11.5px;color:var(--good);font-weight:600;margin-top:1px}
.notas{margin-top:12px;font-size:12.5px;color:var(--ink-2);line-height:1.6}
.notas p{margin:0 0 8px}
.notas ul{margin:0 0 8px;padding-left:18px}
.notas li{margin-bottom:4px}
.notas code{font-family:var(--mono);font-size:11.5px;background:var(--accent-soft);padding:1px 5px;border-radius:3px}
.notas strong{color:var(--ink)}

tr.hl{background:var(--accent-soft)}
tr.hl th{position:relative}
.use{display:block;font-size:10.5px;font-weight:600;color:var(--accent);letter-spacing:.02em;margin-top:1px}
.accent{color:var(--accent)}
.k2{font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:var(--ink-2);font-weight:600}
.v2{font-family:var(--mono);font-size:19px;font-variant-numeric:tabular-nums;font-weight:600;margin-top:2px}
/* marcar acción como hecha */
.accx{width:1%;padding-right:0}
.tick{background:none;border:1.5px solid var(--line);color:var(--ink-3);width:24px;height:24px;
  border-radius:6px;cursor:pointer;font-size:13px;line-height:1;padding:0;transition:.12s}
.tick:hover{border-color:var(--good);color:var(--good)}
tr.done{opacity:.4}
tr.done .accq,tr.done .accw{text-decoration:line-through}
tr.done .tick{background:var(--good-bg);border-color:var(--good);color:var(--good)}
.lnk{background:none;border:none;color:var(--accent);cursor:pointer;font:inherit;font-size:12px;
  text-decoration:underline;padding:0;margin-left:8px}

/* secciones plegables */
details.fold{background:var(--surface);border:1px solid var(--line);border-radius:var(--radius);padding:0 18px}
details.fold > summary{cursor:pointer;padding:15px 0;display:flex;flex-wrap:wrap;align-items:baseline;gap:4px 12px;list-style:none}
details.fold > summary::-webkit-details-marker{display:none}
details.fold > summary::before{content:"▸";color:var(--ink-3);font-size:12px;margin-right:2px}
details.fold[open] > summary::before{content:"▾"}
details.fold[open] > summary{border-bottom:1px solid var(--line-soft);margin-bottom:14px}
details.fold > summary h2{margin:0;font-family:var(--serif);font-size:18px;font-weight:600}
details.fold > *:last-child{margin-bottom:16px}

/* cortes por producto */
details.prodcut{border:1px solid var(--line);border-radius:var(--radius);background:var(--surface);
  margin-bottom:9px;padding:0 16px}
details.prodcut > summary{cursor:pointer;padding:13px 0;display:flex;flex-wrap:wrap;align-items:baseline;
  gap:4px 12px;list-style:none}
details.prodcut > summary::-webkit-details-marker{display:none}
details.prodcut > summary::before{content:"▸";color:var(--ink-3);font-size:11px;margin-right:2px}
details.prodcut[open] > summary::before{content:"▾"}
.pkn{font-weight:700;font-size:14px;letter-spacing:.01em}
.pkv{font-size:12.5px;color:var(--ink-2)}
.vq{font-family:var(--mono);font-size:11.5px;color:var(--good);font-weight:600}
details.prodcut[open] .cortes{padding-bottom:16px}

footer{color:var(--ink-3);font-size:12px;border-top:1px solid var(--line);padding-top:16px}
footer code{font-family:var(--mono)}

@media (max-width:720px){
  .wrap{padding:20px 14px 56px;gap:26px}
  .hero{grid-template-columns:1fr;gap:22px;padding:22px 18px}
  .kpis{grid-template-columns:repeat(3,1fr);gap:12px}
  .clist li{grid-template-columns:1fr auto;}
  .cbar{display:none}
}
@media (prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}
</style>

<div class="wrap">

<header>
  <h1>Portafolio VitalCom</h1>
  <span class="meta">__VENTANA__</span>
  <span class="spacer"></span>
  <a class="nav" href="../VISTAS/PANEL.html" target="_top">&uarr; Panel del sistema</a>
  <span class="meta muted">generado __HOY__</span>
</header>

<div class="integridad integridad--__INTSEV__">
  <span class="dot"></span>
  <strong>Integridad de data:</strong>&nbsp;__INTTXT__ &nbsp;<span class="sub">· __DIASOK__ entregas cargadas · __SINDIM__ filas sin ángulo asignado</span>
</div>

<div class="hero">
  <div>
    <div class="lbl">Ganancia neta · __VENTANACORTA__</div>
    <div class="big pos">__GANANCIA__</div>
    <p class="sub" style="margin:8px 0 0;max-width:44ch">Es la suma de lo que dejó cada pedido según las unidades que llevaba,
      menos la pauta. Ya descuenta producto, flete, admin y las devoluciones del contraentrega.
      <strong>__PROMDIA__ por día.</strong></p>
  </div>
  <div class="kpis">
    <div class="kpi"><div class="v">__VENTAS__</div><div class="k">ventas</div></div>
    <div class="kpi"><div class="v">__CPA__</div><div class="k">CPA global</div></div>
    <div class="kpi"><div class="v">__ROAS__</div><div class="k">ROAS</div></div>
    <div class="kpi"><div class="v">__PAUTA__</div><div class="k">pauta</div></div>
    <div class="kpi"><div class="v">__INGRESO__</div><div class="k">ingreso</div></div>
    <div class="kpi"><div class="v neg">__SANGRADO__</div><div class="k">sangrado</div></div>
  </div>
</div>

<div class="plan">
  <div class="planh">
    <h2>Qué tenés que hacer</h2>
    <span class="n">__NURGENTES__ para hoy</span>
    <span class="spacer"></span>
    <span class="meta sub">__QJUEGO__ en juego por semana</span>
  </div>
  <p class="sub" style="margin:0;padding:11px 18px;border-bottom:1px solid var(--line-soft)">
    Sale de las mismas reglas del playbook aplicadas a la data de hoy — no es una opinión.
    <strong>Apagar</strong> = ya gastó su presupuesto de decisión sin vender ·
    <strong>rebalancear</strong> = el mismo ángulo rinde el doble en otra cuenta ·
    <strong>escalar</strong> = vende bajo el objetivo y le sobra colchón ·
    <strong>renovar</strong> = el ángulo comunica pero el creativo se gastó.
    La columna de la derecha es lo que ese renglón te cuesta (o te deja) por semana si no lo tocás.
  </p>
  <div class="scroll"><table>
    <thead><tr><th></th><th>Cuándo</th><th>Qué y dónde</th><th>Por qué</th>
      <th class="num">Impacto</th><th>Estado</th></tr></thead>
    <tbody>__ROWSACC__</tbody>
  </table></div>
  <p class="sub hechas-nota" style="margin:0;padding:10px 18px;border-top:1px solid var(--line-soft)">
    Tocá el <strong>✓</strong> cuando hagas una. Se tacha y se va al fondo.
    <span class="muted">No hace falta marcarlas: la acción desaparece sola cuando la data del día siguiente
    muestra que el conjunto dejó de gastar o que el presupuesto se movió. El ✓ es solo para que no te
    estorbe mientras tanto.</span>
    <button id="reset" class="lnk">reiniciar marcas</button>
  </p>
</div>

<section>
  <h2>Qué te dejó cada producto</h2>
  <p class="sub">Ordenado por ganancia. El CPA se compara contra su break-even, no entre productos.</p>
  <div class="card scroll"><table>
    <thead><tr><th>Producto</th><th class="num">Ventas</th><th class="num">Pauta</th>
      <th class="num">Ingreso</th><th class="num">CPA</th><th class="num">Break-even</th><th class="num">Ganancia</th></tr></thead>
    <tbody>__ROWSPL__</tbody>
    <tfoot><tr><th>Total</th><td class="num">__VENTAS__</td><td class="num">__PAUTA__</td>
      <td class="num">__INGRESO__</td><td class="num">__CPA__</td><td class="num">—</td>
      <td class="num pos">__GANANCIA__</td></tr></tfoot>
  </table></div>
</section>

<section>
  <h2>¿Estamos contando toda la pauta?</h2>
  <p class="sub">Lo que <strong>LucidSales atribuye</strong> a un anuncio contra lo que <strong>Meta efectivamente cobró</strong>,
    medido sobre la misma ventana (__PRVENTANA__). Un conjunto sin tracking gasta igual y no aparece en el P&amp;L —
    por eso la ganancia de arriba está inflada mientras la cobertura no sea ~100%.
    Verificado contra la facturación de Meta y los extractos de tarjeta el 15-ago.</p>
  <div class="card scroll"><table>
    <thead><tr><th>Cuenta</th><th class="num">Pauta que ve el sistema</th><th class="num">Pauta que cobró Meta</th>
      <th class="num">Cobertura</th><th class="num">Sin contar</th><th>Nota</th></tr></thead>
    <tbody>__ROWSCOB__</tbody>
    <tfoot><tr><th>Total</th><td class="num">__PRTRK__</td><td class="num">__PRREAL__</td>
      <td class="num __PRCLS__">__PRCOB__</td><td class="num neg">__PRFALTA__</td><td></td></tr></tfoot>
  </table></div>
  <div class="ajuste">
    <div><div class="lbl">Ganancia que muestra el P&amp;L</div><div class="v">__GANANCIA__</div>
      <div class="sub">usa solo la pauta trackeada</div></div>
    <div class="arrow">→</div>
    <div><div class="lbl">Ganancia ajustada a la pauta real</div><div class="v __GANAJCLS__">__GANAJ__</div>
      <div class="sub">CPA real __CPAAJ__ (el P&amp;L muestra __CPA__)</div></div>
  </div>
</section>

<section>
  <h2>Qué pegar los domingos</h2>
  <p class="sub">Para que la cobertura de arriba llegue a ~100% y la conciliación de facturación verifique de verdad.
    <strong>Extracto &gt; pantallazo:</strong> un pantallazo se lee bien pero nunca prueba que esté completo.
    Detalle en <code>DOCTRINA/PROTOCOLO_FACTURACION.md</code>.</p>
  <div class="card scroll"><table>
    <thead><tr><th>Qué</th><th>De dónde</th><th>Formato</th><th>Para qué</th></tr></thead>
    <tbody>
      <tr><td><strong>Extracto de Facturación de Meta</strong><br><span class="sub">una por cuenta (las 6)</span></td>
          <td>Administrador comercial → Facturación → Transacciones</td><td>CSV o captura completa</td>
          <td>Lo único que dice <strong>qué tarjeta pagó cada cargo</strong> y cuál fue rechazado</td></tr>
      <tr><td><strong>Saldo «gastado sin facturar»</strong></td><td>misma pantalla, arriba</td><td>un número por cuenta</td>
          <td>Hace <strong>cerrar la ecuación</strong>; sin él la semana siguiente no verifica nada</td></tr>
      <tr><td><strong>Export de Relay</strong></td><td>Relay → Transactions</td><td>CSV</td>
          <td>Relay ya <strong>etiqueta cada cargo con su BM</strong> — resuelve solo el mapa tarjeta→BM</td></tr>
      <tr><td><strong>Ads Manager nivel conjunto</strong><br><span class="sub">GTR13 y CP1</span></td>
          <td>Ads Manager → exportar</td><td>CSV / xlsx</td>
          <td>Las 2 cuentas <strong>sin MCP</strong>: concentran casi toda la fuga</td></tr>
      <tr><td><strong>LucidSales</strong><br><span class="sub">cada día que falte</span></td>
          <td>Métricas de Facebook Ads</td><td>xlsx, <strong>1 día por archivo</strong></td>
          <td>El P&amp;L. Nunca agregado: un agregado no se descompone</td></tr>
      <tr><td colspan="4" class="sub"><strong>Mensual:</strong> extracto bancario completo (Nu y tarjetas USD) + export de órdenes de Dropi.</td></tr>
    </tbody>
  </table></div>
  <p class="sub"><strong>Si tiene que ser pantallazo:</strong> el método del solape es correcto — repetir a propósito
    la última fila de una captura como primera de la siguiente prueba que no quedó nada en el hueco.
    Se deduplica por el <strong>código del cargo</strong> (<code>Facebk *Grdauyd4n2</code>), que es único.
    Nunca por fecha+monto: dos cargos legítimos pueden coincidir y se borraría uno real.
    Que la captura no corte la <strong>etiqueta de cuenta</strong>, o el cargo entra como <code>POR_ATRIBUIR</code>.</p>
</section>

<section>
  <h2>Dónde está la plata hoy</h2>
  <p class="sub">Estado real de los pedidos en Dropi. La ganancia de arriba <strong>proyecta</strong> que lo que está
    en tránsito se entregue a la tasa histórica de cada producto — todavía no es plata en la mano.</p>
  <div class="card scroll"><table>
    <thead><tr><th>Producto</th><th class="num">Entregado</th><th class="num">Devuelto</th>
      <th class="num">En tránsito</th><th class="num">Total</th><th class="num">% entrega</th></tr></thead>
    <tbody>__ROWSMAD__</tbody>
    <tfoot><tr><th>Total</th><td class="num">__MADE__</td><td class="num neg">__MADD__</td>
      <td class="num warn">__MADT__</td><td class="num">__MADTOT__</td><td class="num">__MADPCT__</td></tr></tfoot>
  </table></div>
  <p class="sub" style="margin-top:10px"><strong>__MADTPCT__ de los pedidos sigue en tránsito.</strong>
    Punto de quiebre: la operación empata a una tasa de entrega del <strong>__TEBE__</strong>.
    El histórico del portafolio es __TEHIST__ sobre 289 órdenes resueltas — hay colchón, pero el número
    de arriba se mueve hasta que ese tránsito madure.</p>
</section>

<details>
  <summary><h2>Qué está en quetzales y qué en dólares</h2><span class="sub">la regla de moneda del sistema · abrilo si dudás de una cifra</span></summary>
  <p class="sub">El negocio <b>cobra en quetzales</b> (Guatemala) y <b>paga la publicidad en dólares</b> (Meta).
  Un número convertido de más o de menos se ve plausible y no lo nota nadie: por eso la regla está
  escrita y se verifica sola en cada corrida con <code>verificar_monedas.py</code>. __VERIFMON__</p>
  <div class="card scroll"><table>
    <thead><tr><th>De dónde viene</th><th>Qué trae</th><th>Moneda</th><th>Qué le hace el sistema</th></tr></thead>
    <tbody>
      <tr><td><b>Dropi</b> — órdenes</td><td>total de la orden · flete · costo proveedor · ganancia</td>
          <td><b>QUETZALES</b></td><td>nada: entra tal cual</td></tr>
      <tr><td><b>Dropi</b> — historial de cartera</td><td>entradas por ganancia · cobros de devolución</td>
          <td><b>QUETZALES</b></td><td>nada: entra tal cual</td></tr>
      <tr><td><b>LucidSales</b></td><td><code>total</code> — la venta</td>
          <td><b>QUETZALES</b></td><td>nada: entra tal cual</td></tr>
      <tr><td><b>LucidSales</b></td><td><code>spend</code> — la pauta</td>
          <td><b>DÓLARES</b></td><td>× __TASA__ para pasarlo a Q</td></tr>
      <tr><td><b>Banco</b> (Relay)</td><td>cargos de Meta y todo lo demás</td>
          <td><b>DÓLARES</b></td><td>× __TASA__ para pasarlo a Q</td></tr>
      <tr><td><b>Cuenta CP1</b> — la excepción</td><td><code>spend</code> de esa cuenta sola</td>
          <td><b>PESOS COLOMBIANOS</b></td><td>÷ __TASACOP__ para pasarlo a USD, después × __TASA__</td></tr>
    </tbody>
  </table></div>
  <p class="sub" style="margin-top:10px">⚠️ <b>Dos trampas visuales.</b> (1) El panel de Dropi muestra sus totales
  con el símbolo <code>$</code>, pero <b>son quetzales</b> — no son dólares. (2) La cuenta del banco es
  en dólares, así que un gasto hecho en Guatemala aparece ahí <b>ya convertido a USD</b>: para leerlo en
  quetzales hay que volver a multiplicarlo por __TASA__.</p>
  <p class="sub">La tasa Q__TASA__/USD vive en <code>_PARAMETROS_FINANZAS.csv</code>, en un solo lugar —
  ningún script la tiene escrita adentro. Está marcada <b>DECLARADA</b>, no medida: la cuenta de Relay
  es en dólares y el negocio cobra en quetzales, así que la conversión real recién se puede medir
  cuando cambiés divisa. Si cambia, se toca ese CSV y todo el sistema recalcula solo.</p>
</details>

<section>
  <h2>Semana por semana</h2>
  <p class="sub">Cuánto facturaste y cuánto te quedó cada semana (lunes a domingo), y de qué producto vino. __NOTASEM__</p>
  <div class="card scroll"><table>
    <thead><tr><th>Semana</th><th>Producto</th><th class="num">Ventas</th>
      <th class="num">Facturado</th><th class="num">Pauta</th><th class="num">Ganancia</th>
      <th class="num">CPA</th><th class="num">ROAS</th><th class="num">Gan./día</th></tr></thead>
    <tbody>__ROWSSEM__</tbody>
  </table></div>
</section>

<section>
  <h2>Día por día</h2>
  <p class="sub">Cuánto entró y cuánto salió cada día. __NOTADIA__</p>
  <div class="card scroll"><table>
    <thead><tr><th>Fecha</th><th>Producto</th><th class="num">Ventas</th>
      <th class="num">Inv. USD</th><th class="num">Inv. GTQ</th><th class="num">CPA real</th>
      <th class="num">CPA objetivo</th><th class="num">Break-even</th>
      <th class="num">Gan./venta</th><th class="num">Ganancia</th><th>Veredicto</th></tr></thead>
    <tbody>__ROWSDIA__</tbody>
  </table></div>
</section>

<section>
  <h2>Ranking por ángulo</h2>
  <p class="sub">La unidad de decisión del sistema. Agregado por <code>angulo_key</code> sobre todas las cuentas — nunca por conjunto suelto, que es ruido de muestreo.</p>
  <div class="card scroll"><table>
    <thead><tr><th>Ángulo</th><th class="num">Ventas</th><th class="num">Pauta</th>
      <th class="num">CPA</th><th>Presup. de decisión</th><th>Estado</th></tr></thead>
    <tbody>__ROWSANG__</tbody>
  </table></div>
</section>

<section>
  <h2>Plata sobre la mesa</h2>
  <p class="sub">Conjuntos con 0 ventas que <strong>ya pasaron su presupuesto de decisión</strong> — su cero es veredicto, no falta de exposición. Apagarlos recupera __RECUPERA__ de ganancia.</p>
  <div class="card scroll"><table>
    <thead><tr><th>Conjunto</th><th>Dónde</th><th class="num">Gastado</th><th class="num">% de su PD</th></tr></thead>
    <tbody>__ROWSSANG__</tbody>
  </table></div>
  <p class="sub" style="margin-top:10px">__SUBTXT__</p>
</section>

<section>
  <h2>Por qué funciona — cada producto</h2>
  <p class="sub">Qué vena compra la gente de <em>este</em> producto. Al lado del nombre, lo que mejor le rinde;
    abrí para ver el detalle. Barra más corta = mejor CPA.</p>
  __BLOQUESPK__
  <details class="prodcut">
    <summary><span class="pkn">TODO EL PORTAFOLIO</span><span class="pkv muted">agregado de los 4 productos</span></summary>
    <div class="cortes">__BLOQUES__</div>
  </details>
</section>

<details class="fold">
  <summary><h2>Lo que el sistema ya aprendió</h2><span class="sub">__NAPR__ reglas vigentes · abrilo solo si querés revisarlas</span></summary>
  <p class="sub">Memoria acumulada. <strong>Alta</strong> = restricción dura · <strong>media</strong> = prior fuerte · <strong>baja</strong> = solo seguir midiendo, nunca cambiar una regla.
    Esto lo lee el sistema solo (ETAPA-2 y ETAPA-4 al diseñar, ETAPA-7 y ETAPA-8 al leer) — no hace falta que vos lo repases.</p>
  <ul class="aprs">__ROWSAPR__</ul>
</details>

<details class="fold">
  <summary><h2>Tabla maestra de precios</h2><span class="sub">a qué vender 1, 2, 3 o 4 unidades según el costo · abrilo cuando costees un producto nuevo</span></summary>
  <p class="sub">Vale para cualquier producto. Buscá lo que te cuesta la unidad en la primera columna y leé la fila.
    En cada celda: <strong>arriba el precio de venta</strong>, <strong>abajo en verde lo máximo que podés pagar por esa venta</strong>.
    Resaltadas, las filas que tus productos están usando hoy.</p>
  <div class="card scroll"><table>
    <thead><tr><th>Costo 1x</th>
      <th class="num">1 unidad</th><th class="num">2 unidades</th>
      <th class="num">3 unidades</th><th class="num">4 unidades</th>
      <th class="num">Múltiplo 1u</th><th>Arranque</th><th class="num">CPA objetivo</th></tr></thead>
    <tbody>__ROWSCOST__</tbody>
  </table></div>
  <div class="notas">
    <p><strong>¿1 unidad o directo 2x1?</strong> Lo decide el <strong>múltiplo</strong>, no el margen — a cualquier costo el margen cierra.
      Los ~Q40 fijos de logística (flete + admin + otros) no bajan con el precio, así que en un producto barato el múltiplo que
      tendrías que cobrar por UNA unidad se dispara y el precio deja de ser creíble para la categoría.
      Un producto de Q30 hay que venderlo a <strong>4.6× su costo</strong> para que una unidad sola aguante tu peor CPA; uno de Q100, a 2.1×.
      Con múltiplo ≥4× la venta de 1u es frágil → <strong>arrancar en 2x1</strong>. La frontera cae en <strong>Q40</strong>.
      Entre Q45 y Q55 es zona de criterio: si la categoría tiene un ancla de precio conocida (una crema, un repelente),
      el 2x1 juega a favor; si no, 1 unidad funciona.</p>
    <p><strong>Cómo se arma el precio.</strong> Cada unidad extra se cobra a <code>costo unitario × 1.7</code> redondeado a la decena.
      No es una fórmula inventada: reproduce las escaleras que ya usás (costo Q60 → 199/299/399 = CLEARSTEM · costo Q40 → 179/249/319/389 = VARICOSE).
      La unidad extra casi no agrega costo — mismo envío, mismo riesgo de devolución, mismo admin, solo Q2.70 más de flete — así que ahí es donde vive el margen.
      ⚠️ Es una sugerencia de <em>precio</em>, no una predicción de <em>conversión</em>: subir el precio puede bajar el cierre. Se testea, no se aplica a ciegas.</p>
    <p><strong>Los tres números de CPA, y cuál usar.</strong></p>
    <ul>
      <li><strong>CPA objetivo</strong> — lo que <em>querés</em> pagar. Sale de la tabla de costeo.</li>
      <li><strong>Piso</strong> = el break-even del escalón más barato (la columna de 1 unidad). Por arriba de esto,
        una venta de una sola unidad <em>individualmente</em> pierde plata. <strong>Usalo para decidir a nivel de CONJUNTO</strong>:
        con 1-3 ventas la mezcla es azar puro y no tenés derecho a asumir el upsell.</li>
      <li><strong>Ponderado</strong> = el break-even de tu mezcla real de ventas (el que aparece arriba, por producto).
        <strong>Usalo para medir ganancia y para decidir a nivel de ÁNGULO o producto</strong>, donde hay ventas suficientes
        para que la mezcla se cumpla.</li>
    </ul>
    <p>Entre el piso y el ponderado hay una zona donde ganás <em>solo si el upsell se sostiene</em>. Es el mismo principio
      de «agregar por <code>angulo_key</code>, nunca por conjunto»: lo que es cierto en agregado no es cierto en una muestra chica.</p>
    <p><strong>Break-even de cada escalón</strong> = <code>85.1% × (precio − costo producto − flete − admin − otros) − 14.9% × Q27.16</code>.
      Todo medido sobre 102 órdenes reales de Dropi: comisión de plataforma 0%, flete = Q31.42 + Q2.70 × unidades,
      y la distancia no mueve el flete (Guatemala −Q0.33 vs Petén +Q1.15 — FORZA cobra casi tarifa plana nacional).</p>
    <p>Productos en combo entran por el costo del <strong>pedido</strong>: un producto que se vende 2x1 con frascos de Q45 entra por la fila Q90.</p>
  </div>
</details>

<details class="fold">
  <summary><h2>Tasa de entrega y costos de logística</h2><span class="sub">de acá salen el flete, la devolución y el break-even · se refresca una vez al mes contra Dropi</span></summary>
  __TEHTML__
</details>

<footer>
  Generado por <code>Ads/_TOOLS/gen_dashboard.py</code> desde <code>_FACT_VENTAS.csv</code>,
  <code>_DIM_PRECIOS.csv</code>, <code>_DIM_CONJUNTOS.csv</code>, <code>_EVENTOS.csv</code> y <code>_APRENDIZAJES.csv</code>.
  Ningún número está escrito a mano. Tasa USD→GTQ __TASA__.
</footer>

</div>

<script>
(function () {
  var K = 'vitalcom_hechas';
  function leer() { try { return JSON.parse(localStorage.getItem(K)) || {}; } catch (e) { return {}; } }
  function guardar(o) { try { localStorage.setItem(K, JSON.stringify(o)); } catch (e) {} }
  var hechas = leer(), hoy = new Date().toISOString().slice(0, 10);
  // las marcas caducan a los 3 días: para entonces la data ya reflejó el cambio
  Object.keys(hechas).forEach(function (k) {
    if ((new Date(hoy) - new Date(hechas[k])) / 864e5 > 3) delete hechas[k];
  });
  guardar(hechas);
  var tbody = document.querySelector('.plan tbody');
  if (!tbody) return;
  function pintar() {
    Array.prototype.slice.call(tbody.querySelectorAll('tr[data-k]')).forEach(function (tr) {
      tr.classList.toggle('done', !!hechas[tr.dataset.k]);
    });
    // las hechas se van al fondo
    Array.prototype.slice.call(tbody.querySelectorAll('tr.done')).forEach(function (tr) {
      tbody.appendChild(tr);
    });
  }
  tbody.addEventListener('click', function (e) {
    var b = e.target.closest ? e.target.closest('.tick') : null;
    if (!b) return;
    var k = b.closest('tr').dataset.k;
    if (hechas[k]) { delete hechas[k]; } else { hechas[k] = hoy; }
    guardar(hechas); pintar();
  });
  var r = document.getElementById('reset');
  if (r) r.addEventListener('click', function () { hechas = {}; guardar(hechas); pintar(); });
  pintar();
})();
</script>
"""

try:
    _a = datetime.date(*map(int, ventana[0].split("-")))
    _b = datetime.date(*map(int, ventana[1].split("-")))
    _ndias_ventana = (_b - _a).days + 1
except Exception:
    _ndias_ventana = max(len(dias_data), 1)

roas = (T[2] / T[0]) if T[0] else 0
recupera = q(q_sangrado)
subtxt = ("Otros {} conjuntos con 0 ventas siguen <strong>sub-testeados</strong> (aún no gastan su PD): {} en total. "
          "No se apagan por ventas todavía — sí pueden apagarse antes por conversación floja."
          ).format(len(sub), q(q_sub)) if sub else "No hay conjuntos sub-testeados pendientes."

# ═════════════════════════════════════════════════════════════════════════
# COBERTURA DE PAUTA — ¿el sistema está contando TODO lo que Meta cobra?
# ─────────────────────────────────────────────────────────────────────────
# `spend_usd` de _FACT_VENTAS es lo que LucidSales ATRIBUYE a un anuncio.
# No es lo que Meta cobra: un conjunto sin tracking gasta igual y no aparece.
# Descubierto el 15-ago cruzando facturación de Meta + extractos bancarios
# (APR-031/033/035). Sin esta corrección el P&L infla la ganancia.
# _FACT_PAUTA_REAL.csv guarda ambas columnas medidas sobre la MISMA ventana.
# ═════════════════════════════════════════════════════════════════════════
pauta_real = load("_FACT_PAUTA_REAL.csv")
_pr_trk = sum(f(r["spend_trackeado_usd"]) for r in pauta_real)
_pr_real = sum(f(r["spend_real_usd"]) for r in pauta_real)
COBERTURA = (_pr_trk / _pr_real) if _pr_real else 1.0
_pr_ventana = ("{} → {}".format(pauta_real[0]["ventana_ini"], pauta_real[0]["ventana_fin"])
               if pauta_real else "—")

rows_cob = ""
for r in sorted(pauta_real, key=lambda x: -f(x["spend_real_usd"])):
    tk, rl = f(r["spend_trackeado_usd"]), f(r["spend_real_usd"])
    if rl <= 0 and tk <= 0:
        cls, cob, falta = "muted", "—", "—"
    else:
        c = tk / rl if rl else 0
        cls = "pos" if c >= .88 else ("warn" if c >= .70 else "neg")
        cob, falta = "{:.0f}%".format(c * 100), q((rl - tk) * TASA)
    rows_cob += (
        '<tr><td><strong>{}</strong><div class="sub">{}</div></td>'
        '<td class="num">{}</td><td class="num">{}</td>'
        '<td class="num {}">{}</td><td class="num {}">{}</td>'
        '<td class="sub">{}</td></tr>').format(
        esc(r["cuenta_alias"]), esc(r["fuente"]), q(tk * TASA), q(rl * TASA),
        cls, cob, "neg" if (rl - tk) > 1 else "muted", falta, esc(r["notas"][:150]))

_pauta_aj = T[0] / COBERTURA if COBERTURA else T[0]
_gan_aj = T[3] - (_pauta_aj - T[0])
_cpa_aj = (_pauta_aj / T[1]) if T[1] else 0

# ── maduración del contraentrega: dónde está la plata hoy ────────────────
_ago = [r for r in tasa_ent if r.get("producto_key") != "GLOBAL"]
_ago = [r for r in _ago if r.get("mes", "").startswith("2026-08")] or []
_E = sum(i(r["entregado"]) for r in _ago)
_D = sum(i(r["devolucion"]) for r in _ago)
_TR = sum(i(r["en_transito"]) for r in _ago)
_TOT = _E + _D + _TR
rows_mad = ""
for r in sorted(_ago, key=lambda x: -i(x["total"])):
    tt = i(r["entregado"]) + i(r["devolucion"]) + i(r["en_transito"])
    rows_mad += ('<tr><td><strong>{}</strong></td><td class="num">{}</td>'
                 '<td class="num neg">{}</td><td class="num warn">{}</td>'
                 '<td class="num">{}</td><td class="num">{}%</td></tr>').format(
        esc(r["producto_key"]), r["entregado"], r["devolucion"],
        r["en_transito"], tt, r["pct_entrega_resueltos"])

# punto de quiebre: a qué tasa de entrega la operación empata.
# contribución = TE·M − (1−TE)·C_DEVOL·V  →  M = (contrib + (1−TE)·C_DEVOL·V) / TE
# Igualando contribución a la pauta real y despejando TE.
_contrib_tot = T[3] + T[0]
_M_bruto = (_contrib_tot + (1 - TE) * C_DEVOL * T[1]) / TE if TE else 0
_te_be = ((_pauta_aj + C_DEVOL * T[1]) / (_M_bruto + C_DEVOL * T[1])) if _M_bruto else 0

_tc = 3152.5
for _r in load("_PARAMETROS_FINANZAS.csv"):
    if _r.get("parametro") == "tasa_cop_usd" and _r.get("valor"):
        _tc = float(_r["valor"])
# ── veredicto del verificador de monedas (se corre solo en cada build) ────
import subprocess as _sub
try:
    _vm = _sub.run([sys.executable, os.path.join(ROOT, "Ads", "_TOOLS", "verificar_monedas.py")],
                   capture_output=True, text=True, timeout=60)
    _vm_ok = (_vm.returncode == 0)
    _vm_n = _vm.stdout.count("\u2705")
    verifmon = ('<b style="color:var(--good)">\u2705 Las {} verificaciones de moneda pasan</b> '
                '(revisado hoy: tickets dentro de la escalera, gasto diario plausible en USD, '
                'CP1 normalizada, ROAS coherente).').format(_vm_n) if _vm_ok else \
               ('<b style="color:var(--bad)">\u274c El verificador de monedas ENCONTR\u00d3 un problema</b> '
                '\u2014 hay una cifra en la moneda equivocada. Corr\u00e9 '
                '<code>python Ads/_TOOLS/verificar_monedas.py</code> para ver cu\u00e1l.')
except Exception:
    verifmon = '<i>(el verificador de monedas no pudo correr en este build)</i>'

# ── filas de la tabla SEMANAL ────────────────────────────────────────────
_sem = calcular_semanas(ventas)
_rows_sem, _sem_estimadas = [], 0
for _lun, _d in list(_sem.items())[:10]:
    _dom = _lun + datetime.timedelta(days=6)
    _v, _fac, _pa, _co = _d["tot"]
    _nd = len(_d["dias"])
    _gan = _co - _pa
    if _d["estimada"]:
        _sem_estimadas += 1
    _flags = ""
    if _nd < 7:
        _flags += ' <span class="flag">%dd</span>' % _nd
    if _d["estimada"]:
        _flags += ' <span class="flag">≈</span>'
    _rows_sem.append(
        '<tr class="wk"><td><b>{a} → {b}</b>{fl}</td><td><b>TOTAL</b></td>'
        '<td class="num"><b>{v:.0f}</b></td><td class="num"><b>{fa}</b></td>'
        '<td class="num"><b>{pa}</b></td><td class="num"><b style="color:{c}">{g}</b></td>'
        '<td class="num">{cpa}</td><td class="num">{ro}</td><td class="num">{gd}</td></tr>'.format(
            a=_lun, b=_dom, fl=_flags, v=_v, fa=q(_fac), pa=q(_pa),
            c="var(--bad)" if _gan < 0 else "var(--good)", g=q(_gan),
            cpa=q(_pa / _v) if _v else "—", ro="{:.2f}x".format(_fac / _pa) if _pa else "—",
            gd=q(_gan / max(_nd, 1))))
    for _pk, _x in sorted(_d["prod"].items(), key=lambda kv: -(kv[1][3] - kv[1][2])):
        _v2, _fac2, _pa2, _co2 = _x
        _g2 = _co2 - _pa2
        _rows_sem.append(
            '<tr><td></td><td>{p}</td><td class="num">{v:.0f}</td><td class="num">{fa}</td>'
            '<td class="num">{pa}</td><td class="num" style="color:{c}">{g}</td>'
            '<td class="num">{cpa}</td><td class="num">{ro}</td><td class="num"></td></tr>'.format(
                p=esc(_pk), v=_v2, fa=q(_fac2), pa=q(_pa2),
                c="var(--bad)" if _g2 < 0 else "inherit", g=q(_g2),
                cpa=q(_pa2 / _v2) if _v2 else "—",
                ro="{:.2f}x".format(_fac2 / _pa2) if _pa2 else "—"))
rows_sem = "".join(_rows_sem)
nota_sem = ("Últimas 10 semanas. <span class=\"flag\">Nd</span> = la semana tiene menos de 7 días "
            "de data, su total es un PISO. <span class=\"flag\">≈</span> = incluye tramos cargados "
            "como ventana de varios días, repartidos día a día (el total del tramo es exacto, el "
            "corte del lunes es interpolado).")

rep = {
    "__VENTANA__": "{} → {}".format(*ventana),
    "__VENTANACORTA__": "{} al {}  ·  {} días".format(_dm(ventana[0]), _dm(ventana[1]), _ndias_ventana),
    "__PROMDIA__": q(T[3] / max(_ndias_ventana, 1)),
    "__HOY__": hoy,
    "__INTSEV__": integridad_sev,
    "__INTTXT__": integridad_txt,
    "__DIASOK__": str(dias_ok),
    "__SINDIM__": str(sin_dim),
    "__GANANCIA__": ("+" if T[3] >= 0 else "") + q(T[3]),
    "__VENTAS__": str(T[1]),
    "__PAUTA__": q(T[0]),
    "__INGRESO__": q(T[2]),
    "__CPA__": q1(T[0] / T[1]) if T[1] else "—",
    "__ROAS__": "{:.1f}×".format(roas),
    "__SANGRADO__": q(q_sangrado),
    "__ROWSACC__": rows_acc,
    "__NURGENTES__": "{} {}".format(n_urgentes, "acciones" if n_urgentes != 1 else "acción"),
    "__QJUEGO__": q(q_juego),
    "__RECUPERA__": recupera,
    "__SUBTXT__": subtxt,
    "__ROWSPL__": rows_pl,
    "__ROWSCOB__": rows_cob or '<tr><td colspan="6" class="sub">Sin _FACT_PAUTA_REAL.csv cargado.</td></tr>',
    "__PRVENTANA__": _pr_ventana,
    "__PRTRK__": q(_pr_trk * TASA),
    "__PRREAL__": q(_pr_real * TASA),
    "__PRCOB__": "{:.0f}%".format(COBERTURA * 100),
    "__PRCLS__": "pos" if COBERTURA >= .88 else ("warn" if COBERTURA >= .70 else "neg"),
    "__PRFALTA__": q((_pr_real - _pr_trk) * TASA),
    "__GANAJ__": ("+" if _gan_aj >= 0 else "") + q(_gan_aj),
    "__GANAJCLS__": "pos" if _gan_aj >= 0 else "neg",
    "__CPAAJ__": q1(_cpa_aj) if T[1] else "—",
    "__ROWSMAD__": rows_mad or '<tr><td colspan="6" class="sub">Sin data de Dropi del mes.</td></tr>',
    "__MADE__": str(_E), "__MADD__": str(_D), "__MADT__": str(_TR), "__MADTOT__": str(_TOT),
    "__MADPCT__": "{:.0f}%".format(_E / (_E + _D) * 100) if (_E + _D) else "—",
    "__MADTPCT__": "{:.0f}%".format(_TR / _TOT * 100) if _TOT else "—",
    "__TEBE__": "{:.0f}%".format(_te_be * 100),
    "__TEHIST__": "{:.1f}%".format(TE * 100),
    "__ROWSANG__": rows_ang,
    "__ROWSSANG__": rows_sang,
    "__BLOQUES__": bloques,
    "__ROWSAPR__": rows_apr,
    "__BLOQUESPK__": bloques_pk,
    "__NAPR__": str(len(aprend)),
    "__NDIASOCULTOS__": str(filas_dia_ocultas),
    "__ROWSDIA__": rows_dia,
    "__ROWSSEM__": rows_sem,
    "__VERIFMON__": verifmon,
    "__TASACOP__": "{:,.1f}".format(_tc),
    "__NOTASEM__": nota_sem,
    "__ROWSCOST__": rows_cost,
    "__TEHTML__": te_html or '<p class="sub">Sin data de entrega cargada todavía.</p>',
    "__NOTADIA__": ("Últimos 14 días, una fila por día y producto."
                    + (" Las filas <span class=\"flag\">Nd</span> son ventanas agregadas de varios días."
                       if agregadas else "")
                    + (" ({} filas más viejas ocultas — siguen en el CSV.)".format(filas_dia_ocultas)
                       if filas_dia_ocultas else "")),
    "__TASA__": "{:.2f}".format(TASA),
}
doc = DOC
for k, v in rep.items():
    doc = doc.replace(k, v)

io.open(OUT, "w", encoding="utf-8").write(doc)
print("escrito:", OUT)
print("  ventana {} -> {} · {} ventas · ganancia {} · sangrado {}".format(
    ventana[0], ventana[1], T[1], q(T[3]), q(q_sangrado)))
print("  {} productos · {} angulos · {} aprendizajes · {} filas sin dimension".format(
    len(filas_pl), len(filas_ang), len(aprend), sin_dim))
if sin_atrib:
    print("  ⚠ {} filas SIN ATRIBUCION ({} ventas) — tracking, no dimension. Ver APR-035.".format(
        sin_atrib, sin_atrib_ventas))
