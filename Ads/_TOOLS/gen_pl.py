# -*- coding: utf-8 -*-
"""gen_pl.py — Estado de resultados del sistema. Implementa DOCTRINA/CONTABILIDAD.md.

  python Ads/_TOOLS/gen_pl.py --dropi <ordenes.xlsx> [--banco <extracto.pdf>]
                              [--desde YYYY-MM-DD] [--hasta YYYY-MM-DD] [--json]

Determinista por diseño: mismos archivos de entrada -> mismos números de salida.
Ningún parámetro vive acá dentro: todos salen de `_PARAMETROS_FINANZAS.csv`.

La publicidad sale de Meta (`gasto.py` sobre `_FACT_ENTREGA.csv`); el `spend_usd` de LucidSales
entra SOLO donde Meta no tiene cobertura, y el reporte dice cuánta pauta vino de cada fuente. Los
gastos fijos y retiros del banco llevan su mercado (`_DIM_GASTOS.csv`): los COMPARTIDO se reparten
con `parte_de_mercado`. `calcular_vista_a` es la fórmula de una ventana y la comparte
`gen_pl_mensual.py`.

Con `--json`: además del reporte de siempre (que igual se escribe en
`_AUDITORIAS/_PL_<ini>_<fin>.txt`), serializa EXACTAMENTE los mismos números —
ningún cálculo nuevo — en `_AUDITORIAS/_PL_<ini>_<fin>.json` y los imprime en
stdout (para el runner de la app, que lee `salida: "json"`). Con `--json` el
stdout es SOLO el JSON: el reporte humano no se imprime dos veces, ya quedó
en el .txt.

Produce, en este orden fijo (DOCTRINA/CONTABILIDAD.md §3):
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
import csv, io, json, os, re, sys, collections, datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gasto
import mercado
import tasa_fx

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


_prods = {(r.get("producto_key") or "").strip(): r for r in load("_DIM_PRODUCTOS.csv")}
_merc = {}


def _mercado_de(pk):
    """Mercado (`GT`/`CO`) de un producto de _DIM_PRODUCTOS.csv; MercadoError si no existe."""
    if pk not in _prods:
        raise mercado.MercadoError("«%s» tiene ventas o gasto pero no fila en _DIM_PRODUCTOS.csv." % pk)
    if pk not in _merc:
        _merc[pk] = mercado.mercado_de_fila(_prods[pk], ROOT)
    return _merc[pk]


def es_mercado_pl(r):
    """La fila (de ventas o de gasto) es de un producto del mercado de este estado de resultados (GT)."""
    return _mercado_de(r["producto_key"]) == MERCADO_PL


def pauta_local(r):
    """spend_usd de la fila en quetzales, con la tasa DEL producto (TasaFaltante si no la declara)."""
    usd = fl(r["spend_usd"])
    return usd * mercado.tasa_de_fila(_prods[r["producto_key"]]) if usd else 0.0


def _cuenta_norm(v):
    """'598687956219141.0' -> '598687956219141' (el id de cuenta viene a veces como float de Excel)."""
    v = (v or "").strip()
    try:
        return str(int(float(v)))
    except ValueError:
        return v


def pauta_de_la_ventana(ini, fin, filas=None, excluir_cuentas=()):
    """Pauta del mercado de este estado de resultados con `ventana_ini` en [ini, fin].

    El dueño del gasto es Meta (`_FACT_ENTREGA.csv`), vía `gasto.gasto_por_conjunto_ventana()`:
    LucidSales aporta su `spend_usd` SOLO donde Meta no tiene cobertura (`fuente_gasto`
    LucidSales-fallback), y la fuente se reporta aparte. Cada fila se convierte con la tasa DEL
    producto. `filas` permite pasar el resultado ya calculado de gasto.py (una sola lectura para
    varias ventanas); `excluir_cuentas` saca cuentas por id (p.ej. CP1, que el banco no ve)."""
    filas = gasto.gasto_por_conjunto_ventana() if filas is None else filas
    excluidas = {_cuenta_norm(c) for c in excluir_cuentas}
    out = {"usd": 0.0, "q": 0.0, "meta_usd": 0.0, "fallback_usd": 0.0,
           "ventas_por_producto": collections.Counter(),
           "q_por_producto": collections.defaultdict(float),
           "usd_por_producto": collections.defaultdict(float)}
    for r in filas:
        if not (ini <= r["ventana_ini"] <= fin):
            continue
        if _cuenta_norm(r.get("cuenta_id")) in excluidas:
            continue
        if not es_mercado_pl(r):
            continue
        usd, local, pk = fl(r["spend_usd"]), pauta_local(r), r["producto_key"]
        out["usd"] += usd
        out["q"] += local
        out["fallback_usd" if r["fuente_gasto"] == gasto.FUENTE_FALLBACK else "meta_usd"] += usd
        out["q_por_producto"][pk] += local
        out["usd_por_producto"][pk] += usd
        out["ventas_por_producto"][pk] += int(fl(r["ventas"]))
    return out


def mercados_activos(ini, fin, filas_gasto=None, ordenes=None):
    """Mercados con actividad en [ini, fin]: órdenes de Dropi (por fecha de orden) o pauta de Meta."""
    activos = set()
    ordenes = load("_FACT_ORDENES_DROPI.csv") if ordenes is None else ordenes
    for o in ordenes:
        if ini <= (o.get("fecha_orden") or "") <= fin and o.get("mercado"):
            activos.add(o["mercado"])
    filas_gasto = gasto.gasto_por_conjunto_ventana() if filas_gasto is None else filas_gasto
    for r in filas_gasto:
        if ini <= r["ventana_ini"] <= fin and fl(r["spend_usd"]) > 0:
            activos.add(_mercado_de(r["producto_key"]))
    return activos


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


def par_texto(nombre, default):
    """Parámetro no numérico (una regla) de _PARAMETROS_FINANZAS.csv."""
    r = _par.get(nombre)
    return r["valor"].strip() if r is not None and r["valor"].strip() else default


# El export de Dropi y el banco Relay son SOLO del mercado GT (quetzales): este estado de resultados
# es explicitamente GT. La pauta se toma de las ventas de productos GT y se convierte con la tasa de
# CADA producto; el dinero de otro mercado no entra (se contabiliza aparte, no aca).
MERCADO_PL = "GT"
TASA_Q     = par("tasa_usd_gtq")      # referencia GT para el banco Relay (USD -> Q)
VENTANA_TASA_FX = int(par("ventana_tasa_fx_dias", 90))
C_DEVOL    = par("costo_devolucion_evento_q")
C_ADMIN    = par("costo_admin_q")
C_OTROS    = par("otros_gastos_q")
DIAS_MADURO = int(par("dias_cohorte_maduro"))
REPARTO_COMPARTIDO = par_texto("reparto_gasto_compartido", "ACTIVOS_IGUAL")
BANCO_DESDE = par_texto("banco_desde", "")   # primer día con banco (Relay); "" = siempre hubo
CUENTA_CP1 = next((_cuenta_norm(r["cuenta_id"]) for r in load("_DIM_CUENTAS.csv")
                   if r["cuenta_alias"] == "CP1"), "")

RESUELTOS = ("ENTREGADO", "DEVOLUCION", "CANCELADO")


def parte_de_mercado(mercado_gasto, mercado_pl, activos):
    """Fracción (0-1) de un gasto que le toca a `mercado_pl`.

    Un gasto declarado de un mercado va entero a ese mercado. Uno COMPARTIDO (o sin mercado
    declarado) se reparte según `reparto_gasto_compartido` de _PARAMETROS_FINANZAS.csv:
    ACTIVOS_IGUAL = partes iguales entre los mercados con actividad, y 0 a uno sin actividad."""
    g = (mercado_gasto or "COMPARTIDO").strip().upper()
    if g != "COMPARTIDO":
        return 1.0 if g == mercado_pl else 0.0
    if REPARTO_COMPARTIDO != "ACTIVOS_IGUAL":
        sys.exit("Parámetro reparto_gasto_compartido = «%s»: solo existe ACTIVOS_IGUAL." % REPARTO_COMPARTIDO)
    return 1.0 / len(activos) if mercado_pl in activos else 0.0


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
    return movimientos_del_extracto(txt)


def movimientos_completos_del_extracto(txt):
    """(movimientos, resumen) del texto de un extracto de Relay, con salidas Y depositos.

    Cada movimiento: nombre, fecha, monto (positivo), tipo (`SALIDA`/`ENTRADA`) y saldo (la
    columna Balance, que sirve de llave de dedupe). `resumen`: apertura, cierre, depositos y
    retiros del bloque SUMMARY, o None si el texto no lo trae. Acepta los dos formatos de Relay:
    montos con signo (`-$30.64`, `+$1,000.00`) y montos sin signo marcados con glifos de uso
    privado (U+E000-U+F8FF), que se limpian antes de parsear; sin signo, todo movimiento es
    salida."""
    txt = re.sub("[\ue000-\uf8ff]", "", txt)
    lines = [l.strip() for l in txt.split("\n")]
    pat = re.compile(r"^(\w{3} \d{1,2}, \d{4})\s+(\w+)\s+"
                     r"([+-]?)\$([\d,]+\.\d{2})\s+\$([\d,]+\.\d{2})$")
    pat_resumen = re.compile(r"\$([\d,]+\.\d{2})\s+\$([\d,]+\.\d{2})\s+"
                             r"[+-]?\$([\d,]+\.\d{2})\s+-?\$([\d,]+\.\d{2})")
    num = lambda g: float(g.replace(",", ""))
    mov, resumen = [], None
    for n, l in enumerate(lines):
        m = pat.match(l)
        if m:
            mov.append({"nombre": lines[n - 1] if n else "",
                        "fecha": datetime.datetime.strptime(m.group(1), "%b %d, %Y").date(),
                        "monto": num(m.group(4)),
                        "tipo": "ENTRADA" if m.group(3) == "+" else "SALIDA",
                        "saldo": num(m.group(5))})
        mr = pat_resumen.search(l)
        if mr and resumen is None:
            resumen = {"apertura": num(mr.group(1)), "cierre": num(mr.group(2)),
                       "depositos": num(mr.group(3)), "retiros": num(mr.group(4))}
    return mov, resumen


def movimientos_del_extracto(txt):
    """(salidas, total de Withdrawals del resumen) del texto de un extracto de Relay.

    Solo las SALIDAS: un deposito (`+$`) no es gasto. Mismos dos formatos de Relay que
    `movimientos_completos_del_extracto`, de donde sale."""
    mov, resumen = movimientos_completos_del_extracto(txt)
    salidas = [{"nombre": x["nombre"], "fecha": x["fecha"], "monto": x["monto"]}
               for x in mov if x["tipo"] == "SALIDA"]
    return salidas, (resumen["retiros"] if resumen else None)


# ──────────────────────── la fórmula (reutilizable por ventana) ────────────────────────
def cuadre_dropi(df):
    """(ok, calculado, columna GANANCIA) — integridad 1 de §6: venta − producto − flete = GANANCIA."""
    chk = df[df.ESTATUS == "ENTREGADO"]
    calc = float((chk["TOTAL DE LA ORDEN"] - chk["PRECIO FLETE"]
                  - chk["PRECIO PROVEEDOR X CANTIDAD"]).sum())
    gan = float(chk["GANANCIA"].sum())
    return abs(calc - gan) <= 1.0, calc, gan


def clasificar(nombre, reglas):
    """(clasificación, categoría, mercado del gasto) de un cargo del banco, o SIN_CLASIFICAR."""
    for g in reglas:
        if g["patron"] and g["patron"].lower() in nombre.lower():
            return g["clasificacion"], g.get("categoria", ""), (g.get("mercado") or "")
    return "SIN_CLASIFICAR", "", ""


def clasificar_retiro(concepto, reglas):
    """Clasificación de un RETIRO de la cartera de Dropi por su CONCEPTO de retiro, con las reglas de
    `_DIM_RETIROS.csv` (la primera cuyo patrón aparece en el concepto gana):

      TRANSFERENCIA_PROPIA -> el dinero pasa a una cuenta del propio operador (su LLC): no es gasto
      RETIRO_PERSONAL      -> el operador lo saca para pagar algo personal o familiar: retiro de socio
      SIN_CLASIFICAR       -> ninguna regla calza: se lista y se pregunta, nunca se adivina (APR-030)

    Ninguna de las tres toca el resultado: es movimiento de caja."""
    texto = str(concepto or "").lower()
    if texto:
        for g in reglas:
            if g.get("patron") and g["patron"].lower() in texto:
                return g["clasificacion"]
    return "SIN_CLASIFICAR"


def tasa_del_mes(fin, transferencias=None):
    """Tasa USD -> Q de la ventana que termina el `fin`: la efectiva de las transferencias Dropi ->
    banco (`tasa_fx.tasa_del_mes`) y, sin ninguna, el parámetro `tasa_usd_gtq`."""
    if transferencias is None:
        transferencias = tasa_fx.leer()
    return tasa_fx.tasa_del_mes(fin, transferencias, TASA_Q, VENTANA_TASA_FX)


def pauta_con_tasa(pauta, tasa):
    """La pauta de `pauta_de_la_ventana` con sus quetzales recalculados a la tasa de `tasa_del_mes`
    (sin `tasa` queda como está: cada fila con la tasa de su producto)."""
    if tasa is None:
        return pauta
    return dict(pauta, q=pauta["usd"] * tasa["valor"],
                q_por_producto=collections.defaultdict(
                    float, {pk: u * tasa["valor"] for pk, u in pauta["usd_por_producto"].items()}))


def gastos_del_banco(mov, reglas, ini, fin, activos, tasa_usd=None):
    """Cargos del banco de [ini, fin] clasificados con `_DIM_GASTOS.csv` (CONTABILIDAD.md §3-ter).

      NEGOCIO_PAUTA  -> ya contado en la línea de Publicidad, no se resta otra vez (se reporta
                        aparte como lo que el banco cobró)
      NEGOCIO_FIJO   -> resta del RESULTADO (software, herramientas)
      PERSONAL       -> RETIRO DE SOCIO: NO toca el resultado, sí la caja
      SIN_CLASIFICAR -> no entra a nada; se lista y se pregunta (APR-030)
    Un gasto COMPARTIDO se reparte entre los mercados `activos` (`parte_de_mercado`); si ningún
    mercado está activo queda en `sin_repartir`. `mov` None = sin extracto."""
    from types import SimpleNamespace
    tasa_usd = TASA_Q if tasa_usd is None else tasa_usd
    fijos, retiros, sin_confirmar = 0.0, 0.0, []
    det_fijos, det_retiros, sin_repartir = [], [], []
    pauta_usd, pauta_cargos = 0.0, 0
    if mov is not None:
        agr = collections.defaultdict(float)
        cargos = collections.Counter()
        for t in mov:
            if t.get("tipo", "SALIDA") == "SALIDA" and ini <= str(t["fecha"]) <= fin:
                agr[t["nombre"]] += t["monto"]
                cargos[t["nombre"]] += 1
        pend = collections.defaultdict(float)
        for nom, val in agr.items():
            cl, cat, merc_gasto = clasificar(nom, reglas)
            if cl in ("NEGOCIO_FIJO", "PERSONAL", "NEGOCIO_PAUTA"):
                parte = parte_de_mercado(merc_gasto, MERCADO_PL, activos)
                if not parte:
                    if (merc_gasto or "COMPARTIDO").upper() == "COMPARTIDO" and cl != "NEGOCIO_PAUTA":
                        sin_repartir.append(nom)
                    continue
                if cl == "NEGOCIO_PAUTA":
                    pauta_usd += val * parte
                    pauta_cargos += cargos[nom]
                    continue
                det = {"nombre": nom, "monto_usd": val * parte, "categoria": cat,
                       "mercado": merc_gasto or "COMPARTIDO", "parte": parte}
                if cl == "NEGOCIO_FIJO":
                    fijos += val * parte * tasa_usd
                    det_fijos.append(det)
                else:
                    retiros += val * parte * tasa_usd
                    det_retiros.append(det)
            elif cl == "SIN_CLASIFICAR":
                pend[nom] += val
        sin_confirmar = sorted(pend.items(), key=lambda kv: -kv[1])
    return SimpleNamespace(fijos=fijos, retiros=retiros, det_fijos=det_fijos,
                           det_retiros=det_retiros, sin_confirmar=sin_confirmar,
                           sin_repartir=sin_repartir, pauta_usd=pauta_usd,
                           pauta_cargos=pauta_cargos)


def calcular_vista_a(df, ini, fin, hoy, pauta, mov=None, reglas=(), activos=None, car=None,
                     fin_edad=None, tasa=None):
    """VISTA A (cohorte por fecha de ORDEN) de la ventana [ini, fin]: el estado de resultados de §3.

    Función pura sobre los datos que recibe, para que el reporte de una corrida y el mensual por
    mercado usen LA MISMA fórmula. `df` trae las órdenes (columnas de `leer_dropi`), `pauta` es el
    resultado de `pauta_de_la_ventana`, `mov` las salidas del banco, `reglas` las filas de
    `_DIM_GASTOS.csv`, `activos` los mercados con actividad en la ventana (reparto de los gastos
    COMPARTIDO) y `car` el historial de cartera. `fin_edad` es el último día con órdenes cuando la
    ventana aún no terminó. `tasa` es el dict de `tasa_del_mes`: con él la pauta y los gastos en USD de
    la ventana se convierten a quetzales con ESA tasa (sin él, cada fila con la tasa de su producto y
    los gastos con el parámetro). Devuelve un SimpleNamespace, o None si la ventana no tiene órdenes."""
    from types import SimpleNamespace
    m = df[(df.f_orden >= ini) & (df.f_orden <= fin)]
    if not len(m):
        return None
    ent = m[m.ESTATUS == "ENTREGADO"]
    dev = m[m.ESTATUS == "DEVOLUCION"]
    tra = m[~m.ESTATUS.isin(RESUELTOS)]

    # ── maduración del cohorte (§1) ──
    edad = (hoy - datetime.date.fromisoformat(fin_edad or fin)).days
    maduro = edad >= DIAS_MADURO
    pct_res = 100.0 * (len(m) - len(tra)) / len(m)

    venta = float(ent["TOTAL DE LA ORDEN"].sum())
    costo = float(ent["PRECIO PROVEEDOR X CANTIDAD"].sum())
    flete = float(ent["PRECIO FLETE"].sum())
    m_log = venta - costo - flete

    # ── costo de devolución: REAL orden por orden si hay cartera, si no el parámetro ──
    # Nunca sale del export de órdenes (ahí COSTO DEVOLUCION FLETE = 0 siempre), así
    # que SIEMPRE se suma aparte: una vez por cada orden en estado DEVOLUCION.
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

    c_adm = len(ent) * C_ADMIN
    c_otr = len(ent) * C_OTROS
    m_contr = m_log - c_dev - c_adm - c_otr

    # ── publicidad: de Meta (gasto.py), LucidSales solo donde Meta no cubre ──
    pauta = pauta_con_tasa(pauta, tasa)
    pauta_usd, pauta_q = pauta["usd"], pauta["q"]
    tasa_pauta = pauta_q / pauta_usd if pauta_usd else TASA_Q      # tasa efectiva (la de cada producto)
    # Informativo: lo que la tasa real suma sobre el parámetro. Ya está dentro de la publicidad.
    costo_conversion = pauta_usd * (tasa["valor"] - TASA_Q) if tasa is not None else 0.0
    m_oper = m_contr - pauta_q

    activos = set(activos) if activos else {MERCADO_PL}
    banco = gastos_del_banco(mov, reglas, ini, fin, activos,
                             tasa["valor"] if tasa is not None else None)
    fijos, retiros = banco.fijos, banco.retiros
    det_fijos, det_retiros, sin_confirmar = banco.det_fijos, banco.det_retiros, banco.sin_confirmar
    neto = m_oper - fijos

    # ── economía unitaria por producto (§4) ──
    economia = []
    for pk, g in sorted(ent.groupby("pk"), key=lambda kv: -len(kv[1])):
        n_e = len(g)
        n_d = len(dev[dev.pk == pk])
        te = n_e / (n_e + n_d) if (n_e + n_d) else 1.0
        tick = float(g["TOTAL DE LA ORDEN"].mean())
        cos = float(g["PRECIO PROVEEDOR X CANTIDAD"].mean())
        fle = float(g["PRECIO FLETE"].mean())
        dev_amort = ((1 - te) / te) * C_DEVOL if te else 0.0
        be = tick - cos - fle - dev_amort - C_ADMIN - C_OTROS
        ven = pauta["ventas_por_producto"][pk]
        cpa = pauta["q_por_producto"][pk] / ven if ven else 0.0
        economia.append({
            "producto_key": pk,
            "pct_entrega": 100 * te,
            "entregadas": n_e,
            "devueltas": n_d,
            "ticket_promedio_q": tick,
            "costo_producto_q": cos,
            "flete_q": fle,
            "devolucion_amortizada_q": dev_amort,
            "admin_y_otros_q": C_ADMIN + C_OTROS,
            "margen_antes_publicidad_q": be,
            "cpa_real_q": cpa,
            "ganancia_por_venta_q": be - cpa,
        })

    # ── desglose por producto: la misma fórmula, partida por `pk` (suma al total) ──
    por_producto = []
    for pk in sorted(set(m["pk"]) | set(pauta["q_por_producto"])):
        mp = m[m.pk == pk]
        ep, dp = mp[mp.ESTATUS == "ENTREGADO"], mp[mp.ESTATUS == "DEVOLUCION"]
        v_p = float(ep["TOTAL DE LA ORDEN"].sum())
        c_p = float(ep["PRECIO PROVEEDOR X CANTIDAD"].sum())
        f_p = float(ep["PRECIO FLETE"].sum())
        if car is not None:
            cob_p = car[(car.cat == "COBRO_DEVOLUCION") & (car["ORDEN ID"].isin(set(dp["ID"])))]
            dev_p = float(cob_p["MONTO"].sum()) + max(len(dp) - len(cob_p), 0) * C_DEVOL
        else:
            dev_p = len(dp) * C_DEVOL
        marg_p = v_p - c_p - f_p - dev_p - len(ep) * (C_ADMIN + C_OTROS)
        pauta_p = pauta["q_por_producto"][pk]
        por_producto.append({
            "producto_key": pk, "ordenes": len(mp), "entregadas": len(ep), "devueltas": len(dp),
            "en_transito": int((~mp.ESTATUS.isin(RESUELTOS)).sum()),
            "venta_entregada_q": v_p, "costo_producto_q": c_p, "flete_q": f_p,
            "devoluciones_q": dev_p, "personal_y_otros_q": len(ep) * (C_ADMIN + C_OTROS),
            "margen_antes_publicidad_q": marg_p, "pauta_q": pauta_p,
            "ganancia_q": marg_p - pauta_p})

    return SimpleNamespace(
        pauta_banco_usd=banco.pauta_usd, pauta_banco_cargos=banco.pauta_cargos,
        sin_repartir=banco.sin_repartir, por_producto=por_producto,
        m=m, ent=ent, dev=dev, tra=tra, edad=edad, maduro=maduro, pct_res=pct_res,
        venta=venta, costo=costo, flete=flete, m_log=m_log, c_dev=c_dev, origen_dev=origen_dev,
        c_adm=c_adm, c_otr=c_otr, m_contr=m_contr, pauta=pauta, pauta_usd=pauta_usd,
        pauta_q=pauta_q, tasa_pauta=tasa_pauta, m_oper=m_oper, fijos=fijos, det_fijos=det_fijos,
        retiros=retiros, det_retiros=det_retiros, sin_confirmar=sin_confirmar, neto=neto,
        economia=economia, tasa=tasa, costo_conversion_q=costo_conversion)


def cobertura_de_pauta(mov, filas_gasto=None):
    """Texto de la cobertura de pauta en el tramo ALINEADO del banco (APR-070), o None sin cargos.

    Meta cobra por umbral y con retraso, así que el mes calendario mezcla dos preguntas: se compara
    la intersección de las dos series, y se excluye CP1 (factura en COP por otro medio de pago)."""
    fbm = [t for t in mov if "Facebook" in t["nombre"]]
    if not fbm:
        return None
    d_ini = min(t["fecha"] for t in fbm).isoformat()
    d_fin = max(t["fecha"] for t in fbm).isoformat()
    fb_al = sum(t["monto"] for t in fbm)
    p = pauta_de_la_ventana(d_ini, d_fin, filas_gasto, excluir_cuentas=(CUENTA_CP1,))
    tr_al = p["usd"]
    cob = 100 * tr_al / fb_al if fb_al else 0
    return (d_ini, d_fin, fb_al, tr_al, cob, p)


# ──────────────────────────────── main ────────────────────────────────
def main():
    try:
        _main()
    except mercado.MercadoError as error:     # sin tasa / sin mercado: se detiene, nombrandolo
        print("BLOQUEANTE: %s" % error, file=sys.stderr)
        sys.exit(1)


def _main():
    a = sys.argv[1:]
    def opt(flag, d=None):
        return a[a.index(flag) + 1] if flag in a else d
    dropi = opt("--dropi"); banco = opt("--banco"); cartera = opt("--cartera")
    ini   = opt("--desde", "2026-08-01"); fin = opt("--hasta", "2026-08-31")
    quiere_json = "--json" in a
    if not dropi:
        sys.exit("Falta --dropi <ordenes.xlsx>. Es la fuente de la venta real (DOCTRINA/CONTABILIDAD.md §5).")

    import pandas as pd
    df = leer_dropi(dropi)
    alertas, fallos = [], []

    # ── integridad 1: el cuadre interno de Dropi ──
    ok_cuadre, calc, gan = cuadre_dropi(df)
    if not ok_cuadre:
        fallos.append("El cuadre de Dropi NO da: venta−producto−flete = Q%.2f pero la columna "
                      "GANANCIA suma Q%.2f. El export cambió de formato." % (calc, gan))

    hoy = datetime.date.today()
    filas_gasto = gasto.gasto_por_conjunto_ventana()
    pauta = pauta_de_la_ventana(ini, fin, filas_gasto)
    activos = mercados_activos(ini, fin, filas_gasto) | {MERCADO_PL}
    reglas = load("_DIM_GASTOS.csv")
    car = leer_cartera(cartera) if cartera else None
    mov, control = leer_banco(banco) if banco else (None, None)
    if mov is not None and control is not None and abs(sum(x["monto"] for x in mov) - control) > 0.02:
        fallos.append("El extracto no cuadra: los movimientos suman $%.2f y el resumen dice "
                      "$%.2f." % (sum(x["monto"] for x in mov), control))

    # ── ventana: VISTA A (cohorte por fecha de ORDEN) ──
    tasa = tasa_del_mes(fin)
    r = calcular_vista_a(df, ini, fin, hoy, pauta, mov=mov, reglas=reglas, activos=activos, car=car,
                         tasa=tasa)
    if r is None:
        sys.exit("Sin órdenes de Dropi en %s → %s" % (ini, fin))
    m, ent, dev, tra = r.m, r.ent, r.dev, r.tra
    edad, maduro, pct_res = r.edad, r.maduro, r.pct_res
    venta, costo, flete, m_log = r.venta, r.costo, r.flete, r.m_log
    c_dev, origen_dev, c_adm, c_otr, m_contr = r.c_dev, r.origen_dev, r.c_adm, r.c_otr, r.m_contr
    pauta_usd, pauta_q, tasa_pauta, m_oper = r.pauta_usd, r.pauta_q, r.tasa_pauta, r.m_oper
    fijos, retiros, neto = r.fijos, r.retiros, r.neto
    det_fijos, det_retiros, sin_confirmar = r.det_fijos, r.det_retiros, r.sin_confirmar

    # ── js: mismos números que L, para --json (T4a) — nunca un cálculo aparte ──
    js = {
        "mercado": MERCADO_PL,
        "moneda": mercado.perfil_mercado(MERCADO_PL, ROOT)["moneda"],
        "periodo": {"desde": ini, "hasta": fin, "generado": hoy.isoformat()},
        "vista_a_cohorte": {
            "preliminar": not maduro,
            "edad_dias": edad,
            "dias_maduro_umbral": DIAS_MADURO,
            "ordenes_total": len(m),
            "entregadas": len(ent),
            "devueltas": len(dev),
            "en_transito": len(tra),
            "pct_resuelto": pct_res,
        },
    }

    L = []
    W = 68
    L += ["═" * W,
          "ESTADO DE RESULTADOS — %s → %s" % (ini, fin),
          "MERCADO %s (%s) — Dropi y el banco Relay solo cubren este mercado" % (MERCADO_PL, js["moneda"]),
          "VISTA A · COHORTE (por fecha de ORDEN) — «¿rindió la pauta de esta ventana?»",
          "Generado %s · norma: DOCTRINA/CONTABILIDAD.md · parámetros: _PARAMETROS_FINANZAS.csv" % hoy,
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
    js["vista_a_cohorte"]["estado_de_resultados"] = {
        "venta_bruta_entregada_q": venta,
        "costo_producto_q": costo,
        "flete_q": flete,
        "margen_logistico_q": m_log,
        "costo_devoluciones_q": c_dev,
        "origen_costo_devoluciones": origen_dev,
        "costo_personal_q": c_adm,
        "otros_gastos_q": c_otr,
        "margen_contribucion_q": m_contr,
    }

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

    js["vista_a_cohorte"]["estado_de_resultados"].update({
        "publicidad_usd": pauta_usd,
        "publicidad_fuente": {"meta_usd": pauta["meta_usd"],
                              "lucidsales_fallback_usd": pauta["fallback_usd"]},
        "tasa_usd_gtq": tasa["valor"],
        "tasa_fuente": dict(tasa, tasa_parametro=TASA_Q, ventana_dias=VENTANA_TASA_FX),
        "costo_conversion_q": r.costo_conversion_q,
        "publicidad_q": pauta_q,
        "margen_operativo_q": m_oper,
    })
    L += ["",
          "  (−) Publicidad Meta ($%.2f × %.2f)    %s" % (pauta_usd, tasa_pauta, q(-pauta_q)),
          "      Fuente: Meta $%.2f · LucidSales donde Meta no cubre $%.2f"
          % (pauta["meta_usd"], pauta["fallback_usd"]),
          "      Tasa %.4f · %s%s · sobre el parámetro %.2f suma %s (ya está en la línea de arriba)"
          % (tasa["valor"], tasa["regla"],
             " (%d transferencias Dropi→banco, $%.2f)" % (tasa["transferencias"], tasa["usd"])
             if tasa["transferencias"] else "", TASA_Q, q(r.costo_conversion_q).strip()),
          "      " + "·" * 56,
          "  (=) MARGEN OPERATIVO                    %s" % q(m_oper)]

    if mov is not None:
        cob_txt = cobertura_de_pauta(mov, filas_gasto)
        if cob_txt:
            d_ini, d_fin, fb_al, tr_al, cob, _ = cob_txt
            alertas.append("Cobertura de pauta en el tramo ALINEADO %s→%s (el único comparable, "
                           "APR-070): el banco cobró $%.2f y Meta atribuye $%.2f = %.1f%%. "
                           "Faltan %s de gasto real en el P&L."
                           % (d_ini, d_fin, fb_al, tr_al, cob, q((fb_al - tr_al) * tasa["valor"]).strip()))
            if df.f_orden.min() >= pd.Timestamp(ini):
                alertas.append("El extracto arranca antes que los cargos de Meta: los primeros días "
                               "del mes se cobraron en el extracto ANTERIOR. Para cerrar el arrastre "
                               "hace falta el extracto del mes previo.")

    js["vista_a_cohorte"]["estado_de_resultados"].update({
        "gastos_fijos_q": fijos,
        "gastos_fijos_detalle": [{"nombre": d["nombre"], "monto_usd": d["monto_usd"],
                                  "categoria": d["categoria"], "mercado": d["mercado"],
                                  "parte": d["parte"]} for d in det_fijos],
        "resultado_neto_q": neto,
        "retiros_personales_q": retiros,
        "retiros_personales_detalle": [{"nombre": d["nombre"], "monto_usd": d["monto_usd"],
                                        "categoria": d["categoria"], "mercado": d["mercado"],
                                        "parte": d["parte"]} for d in det_retiros],
        "cargos_sin_clasificar": [{"nombre": n, "monto_usd": v_} for n, v_ in sin_confirmar],
    })
    L += ["", "  (−) Gastos fijos del negocio            %s" % q(-fijos)]
    for d in sorted(det_fijos, key=lambda x: -x["monto_usd"]):
        L.append("        {:<24} ${:>8,.2f}  {}".format(d["nombre"][:24], d["monto_usd"], d["categoria"]))
    if not det_fijos:
        L.append("        (ninguno confirmado en esta ventana)")
    L += ["      " + "═" * 56,
          "  (=) RESULTADO NETO DEL NEGOCIO          %s" % q(neto),
          "─" * W, ""]

    if det_retiros:
        L += ["RETIROS PERSONALES — salieron de la cuenta pero NO son del negocio.",
              "No reducen la ganancia (no es plata que el negocio gastó en operar);",
              "sí reducen la CAJA disponible. Contablemente es un retiro de socio."]
        for d in sorted(det_retiros, key=lambda x: -x["monto_usd"]):
            L.append("     {:<26} ${:>8,.2f} = {}".format(d["nombre"][:26], d["monto_usd"],
                                                          q(d["monto_usd"] * tasa["valor"])))
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
            L.append("     {:<26} ${:>8,.2f} = {}".format(k[:26], val, q(val * tasa["valor"])))
        L.append("")

    # ── economía unitaria por producto (§4) ──
    L += ["═" * W, "ECONOMÍA UNITARIA — cuánto deja CADA VENTA, por producto", "═" * W, ""]
    js["vista_a_cohorte"]["economia_unitaria"] = r.economia
    for e in r.economia:
        L += ["  %s   (entrega %.1f%% · %d entregadas / %d devueltas)"
              % (e["producto_key"], e["pct_entrega"], e["entregadas"], e["devueltas"]),
              "     Precio de venta (ticket promedio)      %s" % q(e["ticket_promedio_q"]),
              "     − Costo del producto                   %s" % q(-e["costo_producto_q"]),
              "     − Flete                                %s" % q(-e["flete_q"]),
              "     − Devolución amortizada                %s" % q(-e["devolucion_amortizada_q"]),
              "     − Admin y otros                        %s" % q(-e["admin_y_otros_q"]),
              "       " + "·" * 54,
              "     = MARGEN ANTES DE PUBLICIDAD           %s  ← break-even del CPA"
              % q(e["margen_antes_publicidad_q"]),
              "     − CPA real (pauta ÷ ventas)            %s" % q(-e["cpa_real_q"]),
              "       " + "·" * 54,
              "     = GANANCIA POR VENTA                   %s  %s" % (
                  q(e["ganancia_por_venta_q"]),
                  "🔴 PIERDE en cada venta" if e["ganancia_por_venta_q"] < 0 else "✅"),
              ""]

    # ── VISTA B — CAJA (por fecha del movimiento de dinero, §2) ──
    L += ["═" * W, "VISTA B — CAJA (¿cuánto dinero entró de verdad en la ventana?)", "═" * W]
    if car is None:
        js["vista_b_caja"] = None
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
                          and ini <= str(t["fecha"]) <= fin) * tasa["valor"]) if banco else None
        js["vista_b_caja"] = {
            "entradas_ganancia_ordenes_q": entra,
            "n_entradas_ganancia_ordenes": len(e_gan),
            "cobros_devolucion_q": sale_d,
            "n_cobros_devolucion": len(s_dev),
            "otras_salidas_q": sale_o,
            "n_otras_salidas": len(s_otr),
            "neto_acreditado_cartera_q": caja_dropi,
            "personal_y_otros_q": adm_caja,
            "publicidad_cobrada_banco_q": pauta_caja,
        }
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
            js["vista_b_caja"]["gastos_fijos_q"] = fijos
            js["vista_b_caja"]["caja_que_genero_el_negocio_q"] = caja_neg
            js["vista_b_caja"]["retiros_personales_q"] = retiros
            js["vista_b_caja"]["caja_que_quedo_en_la_cuenta_q"] = caja_neg - retiros
            L += ["      " + "═" * 56,
                  "  (=) CAJA QUE GENERÓ EL NEGOCIO              %s" % q(caja_neg)]
            if retiros:
                L += ["  (−) Retiros personales (no son del negocio) %s" % q(-retiros),
                      "      " + "═" * 56,
                      "  (=) CAJA QUE QUEDÓ EN LA CUENTA             %s" % q(caja_neg - retiros)]
            L.append("")
        else:
            js["vista_b_caja"]["caja_antes_de_publicidad_q"] = caja_dropi - adm_caja
            L += ["      " + "═" * 56,
                  "  (=) CAJA ANTES DE PUBLICIDAD                %s" % q(caja_dropi - adm_caja), ""]
        # el arrastre: cuántos movimientos vienen de órdenes de ANTES de la ventana
        prev = e_gan.merge(df[["ID", "f_orden"]], left_on="ORDEN ID", right_on="ID", how="left")
        n_prev = int((prev.f_orden < pd.Timestamp(ini)).sum())
        d_prev = float(prev[prev.f_orden < pd.Timestamp(ini)]["MONTO"].sum())
        js["vista_b_caja"]["arrastre"] = {
            "n_acreditaciones_previas": n_prev,
            "n_acreditaciones_total": len(e_gan),
            "monto_previo_q": d_prev,
        }
        js["vista_b_caja"]["cohorte_vs_caja_q"] = {
            "cohorte_margen_contribucion_q": m_contr,
            "caja_antes_de_publicidad_q": caja_dropi - adm_caja,
        }
        L += ["  ARRASTRE: %d de las %d acreditaciones (%s) vienen de órdenes tomadas ANTES"
              % (n_prev, len(e_gan), q(d_prev)),
              "  del %s. Eso es exactamente lo que la vista de COHORTE no ve: se vendió un" % ini,
              "  mes y se cobró al siguiente.", ""]
        L += ["  COHORTE vs CAJA en esta ventana: %s vs %s"
              % (q(m_contr), q(caja_dropi - adm_caja)),
              "  No tienen por qué coincidir y ninguna está mal: miden cosas distintas.", ""]

    js["alertas"] = list(alertas)

    if alertas:
        L += ["─" * W, "NOTAS"] + ["  ⚠ " + x for x in alertas] + [""]

    # ── integridad (§6) ──
    js["integridad"] = {
        "cuadre_dropi": not any("cuadre de Dropi" in x for x in fallos),
        "cuadre_extracto": (not any("extracto" in x for x in fallos)) if banco else None,
        "maduracion": maduro,
    }
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
        js["integridad"]["cruce_cartera"] = {
            "movimientos": len(cr), "descuadres": difs, "sin_orden": huerf, "ok": ok,
        }
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

    js["fallos"] = list(fallos)
    js["ok"] = not fallos

    txt = "\n".join(L) + "\n"
    os.makedirs(AUD, exist_ok=True)
    base_nombre = "_PL_%s_%s" % (ini.replace("-", ""), fin.replace("-", ""))
    out = os.path.join(AUD, base_nombre + ".txt")
    io.open(out, "w", encoding="utf-8").write(txt)

    if quiere_json:
        out_json = os.path.join(AUD, base_nombre + ".json")
        cuerpo_json = json.dumps(js, ensure_ascii=False, indent=2)
        io.open(out_json, "w", encoding="utf-8").write(cuerpo_json + "\n")
        # stdout es SOLO el JSON (el runner de la app lo interpreta como `salida: "json"`):
        # el reporte humano ya quedó en el .txt de arriba, no se duplica acá.
        print(json.dumps(js, ensure_ascii=False))
    else:
        print(txt)
        print("escrito:", out)
    if fallos:
        sys.exit("\n❌ INTEGRIDAD FALLIDA — los números de arriba NO son confiables.")


if __name__ == "__main__":
    main()
