# -*- coding: utf-8 -*-
"""gen_lanzador.py — genera VISTAS/LANZADOR.html, la consola de lanzamiento.

QUE ES
La pantalla que convierte el sistema en un flujo ejecutable. El operador entra, elige
el producto, y la app le dicta paso por paso lo que tiene que hacer: que prompt copiar,
como se llama la campana, cuanto presupuesto, que copy pegar en cada anuncio, que dia
volver y con que data. Cada campo tiene su boton de copiar. Nada se escribe a mano.

LA SEPARACION QUE LA HACE SISTEMATICA
    _PLAN.json (etapa-6)     -> CONTENIDO creativo: angulos, prompts, copies
    este script              -> TODO LO DERIVABLE: nombres, plata, bandas, fechas, gates
    los CSV                  -> LOS HECHOS: costos, break-even, historial, estado

Ningun numero se escribe a mano en el HTML. Si un dato no esta, la app lo muestra como
BLOQUEANTE con el nombre de quien lo produce — nunca lo inventa.

DE DONDE SALE CADA COSA (un dato, un dueno)
    nombres de campana/conjunto/anuncio  .claude/agents/ETAPA-6.md  CONVENCION DE NOMBRES
    la firma de 5 ejes                   DOCTRINA/PARAMETRIZACION_ADS.md  seccion 3.5
    presupuesto por conjunto             DOCTRINA/CALENDARIO_ESCALADO.md  seccion 1.5
    estructura por fase                  DOCTRINA/CALENDARIO_ESCALADO.md  seccion 1.7.2
    banda de edad                        Ads/_TOOLS/bandas_edad.py (tabla) — doctrina y
                                          evidencia en .claude/agents/ETAPA-6.md (APR-060)
    break-even y costos                  PRODUCTOS/_DIM_PRODUCTOS.csv
    historial de gasto y ventas          PRODUCTOS/_FACT_VENTAS.csv

USO
    python Ads/_TOOLS/gen_lanzador.py
    python Ads/_TOOLS/gen_lanzador.py --json    # solo el JSON, sin renderizar
"""
import io, os, sys, csv, json, math, re, datetime
from collections import defaultdict

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(BASE)

DIM_PRODUCTOS = "PRODUCTOS/_DIM_PRODUCTOS.csv"
FACT_VENTAS = "PRODUCTOS/_FACT_VENTAS.csv"
DIM_ANUNCIOS = "PRODUCTOS/_DIM_ANUNCIOS.csv"
EVENTOS = "PRODUCTOS/_EVENTOS.csv"
PARAMETROS_PUBLICACION = "PRODUCTOS/_PARAMETROS_PUBLICACION.csv"
SALIDA_JSON = "PRODUCTOS/_LANZADOR.json"
SALIDA_HTML = "VISTAS/LANZADOR.html"

HOY = datetime.date.today()

# ── CONSTANTES DE DOCTRINA (con su dueno al lado; no se tocan aca) ─────────────
PISO_PRESUPUESTO = 2.99      # CALENDARIO_ESCALADO seccion 1.5
TECHO_PRESUPUESTO = 3.95     # idem
FACTOR_ENTREGA = 0.8         # idem, "factor de entrega real"
PRESUPUESTO_E2 = 5.98        # ETAPA 2 del testeo: los sobrevivientes al doble
MAX_CONJUNTOS_CON_PRECIO = 3 # ETAPA-6, regla de precio en creativo (ideal 2)

# La tabla NO se copia aca: Ads/_TOOLS/bandas_edad.py es su dueno unico (G0.5 punto 4.2).
# ETAPA-6.md BANDA DE EDAD sigue siendo el puntero de doctrina y evidencia (APR-060).

ESTRUCTURA = {  # CALENDARIO_ESCALADO seccion 1.7.2 · clases Calet 16-ago y 22-ago
    1: {"nombre": "FASE 1 · ÁNGULOS", "mide": "el ÁNGULO",
        "forma": "6 conjuntos × 1 ángulo · ABO · concepto FIJO",
        "notacion": "6 conjuntos · ABO", "presupuesto": "PROTEGIDO",
        "decide": "VENTA, agregada por angulo_key", "campanas": 1,
        "por_que": ("El ángulo se decide por VENTA, y Meta no ve ventas: ve clics y conversaciones. "
                    "APR-002 lo midió en data propia — tinnidrop-1 hizo 78 % de conversación y 0 "
                    "ventas; ANIMO la conversación más alta del portafolio y 0 ventas; ME DIJERON "
                    "23 % y es de los que más vende. En un 1-1-5 Meta repartiría por la métrica "
                    "equivocada y mataría de hambre al ángulo que sí vende. Por eso cada ángulo "
                    "lleva su propio presupuesto protegido."),
        "no_es": "El 1-1-5 NO va acá. Va en FASE 2, cuando el ángulo ya está validado."},
    2: {"nombre": "FASE 2 · CONCEPTOS", "mide": "el CREATIVO",
        "forma": "1-1-5 + 1-1-5 + 1-2-5 · ABO · ángulo FIJO",
        "notacion": "1-1-5 ×2 + 1-2-5 · ABO", "presupuesto": "LIBRE",
        "decide": "REPLICACIÓN: gana en 2 de 2", "campanas": 3,
        "por_que": ("Acá el ángulo ya está validado y lo que se busca es qué ejecución visual "
                    "entrega más barato. Para eso el criterio de Meta (CTR, CPM, conversación) SÍ "
                    "está alineado con el objetivo, así que se le puede soltar el presupuesto. Es "
                    "el 1-1-5 de la clase del 16-ago: «agarramos el ángulo y lo hacemos en varios "
                    "conceptos, lanzamos campañas 115»."),
        "no_es": ("Corre en ABO, no en CBO. Calet probó CBO para testear creativos y lo abandonó: "
                  "«siempre me tomaba un solo anuncio y me quedaba la duda, los cuatro anuncios "
                  "restantes ¿dónde están?». En CBO Meta corona uno solo; en prueba de creativo "
                  "pueden salir dos o tres ganadores.")},
    4: {"nombre": "FASE 4 · ESCALADO", "mide": "volumen",
        "forma": "1-1-7 CBO (el ganador ×7)",
        "notacion": "1-1-7 · CBO", "presupuesto": "LIBRE",
        "decide": "CPA semanal sobre ENTREGADOS", "campanas": 1,
        "por_que": ("Acá no se mide nada: se compra volumen con lo ya validado. Son 7 veces EL "
                    "MISMO creativo ganador, no 7 creativos distintos. «115 para validar en ABO y "
                    "después nos vamos con CBO para escalar» (clase 16-ago)."),
        "no_es": ("Con un solo conjunto, el CBO es funcionalmente idéntico al ABO — todo el "
                  "presupuesto va a ese conjunto igual. El CBO recién significa algo en el 1-7-7.")},
}


def leer_csv(ruta):
    if not os.path.exists(ruta):
        return []
    with io.open(ruta, encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def num(x, d=0.0):
    try:
        return float(str(x).replace(",", ""))
    except Exception:
        return d


def guion(s):
    """Dentro de un campo del nombre solo va guion medio (ETAPA-6, regla 3)."""
    return (s or "").replace("_", "-").replace(" ", "-")


def corto(prod):
    """El token de PRODUCTO que va en el nombre de campana."""
    clave = (prod.get("clave_campana") or "").split("/")[0].strip()
    if clave and clave.upper() not in ("PENDIENTE", "SIN_MCP"):
        return guion(clave.upper())
    return guion(prod["producto_key"].upper())


# ─────────────────────────────────────────────────────────────────────────────
# 1 · LOS HECHOS: que dicen los CSV de cada producto
# ─────────────────────────────────────────────────────────────────────────────

def hechos_por_producto():
    """Gasto, ventas, mensajes y costo por conversacion observado, por producto."""
    acc = defaultdict(lambda: {"spend": 0.0, "ventas": 0.0, "mensajes": 0.0,
                               "ultima": None, "ventanas": set()})
    for f in leer_csv(FACT_VENTAS):
        k = f.get("producto_key")
        if not k:
            continue
        a = acc[k]
        a["spend"] += num(f.get("spend_usd"))
        a["ventas"] += num(f.get("ventas"))
        a["mensajes"] += num(f.get("mensajes"))
        fin = f.get("ventana_fin")
        if fin:
            a["ventanas"].add(fin)
            if not a["ultima"] or fin > a["ultima"]:
                a["ultima"] = fin
    out = {}
    for k, a in acc.items():
        out[k] = {
            "spend_usd": round(a["spend"], 2),
            "ventas": int(a["ventas"]),
            "mensajes": int(a["mensajes"]),
            "cierre_pct": round(100.0 * a["ventas"] / a["mensajes"], 1) if a["mensajes"] else None,
            "usd_por_conversacion": round(a["spend"] / a["mensajes"], 3) if a["mensajes"] else None,
            "ultima_ventana": a["ultima"],
        }
    return out


def usd_por_conversacion_portafolio(hechos):
    tot_s = sum(h["spend_usd"] for h in hechos.values())
    tot_m = sum(h["mensajes"] for h in hechos.values())
    return round(tot_s / tot_m, 3) if tot_m else 0.478  # 0.478 = medicion jul-2026


def presupuesto_fase_csv(fase, brazo):
    """Todas las fases leen su fila VIGENTE en _PARAMETROS_PUBLICACION.csv; sin fila,
    devuelve None y no inventa."""
    for r in leer_csv(PARAMETROS_PUBLICACION):
        if r.get("fase") == str(fase) and r.get("brazo") == brazo and r.get("estado") == "VIGENTE":
            return num(r.get("daily_budget_usd")), (
                "fijo · fase %s brazo %s · %s" % (fase, brazo, r.get("fuente_doctrina") or "_PARAMETROS_PUBLICACION.csv"))
    return None, "sin fila VIGENTE en _PARAMETROS_PUBLICACION.csv para fase=%s brazo=%s" % (fase, brazo)


def presupuesto_por_fase(fase, usd_conv, brazo="A"):
    """El presupuesto por conjunto sale de la fila VIGENTE de la fase en
    _PARAMETROS_PUBLICACION.csv; sin fila, devuelve None y no inventa. `usd_conv`
    ya no se usa. FASE 2 usa el brazo dado; cualquier otra fase, "UNICO"."""
    if fase == 2:
        return presupuesto_fase_csv(2, brazo)
    return presupuesto_fase_csv(fase, "UNICO")


def monto_cuenta(usd, moneda, tasa):
    """(valor, texto) de un monto en USD expresado en la moneda de la cuenta
    publicitaria (_DIM_PRODUCTOS.moneda).
    USD   -> (usd, "US$2.99")            dos decimales
    otra  -> (round(usd * tasa), "$9.426 COP")   entero, punto de miles, codigo de moneda
    (None, None) si falta la moneda, o si no es USD y falta la tasa."""
    moneda = (moneda or "").strip().upper()
    if not moneda:
        return None, None
    if moneda == "USD":
        return usd, "US$%.2f" % usd
    if not tasa:
        return None, None
    entero = int(round(usd * tasa))
    return entero, "$%s %s" % (format(entero, ",").replace(",", "."), moneda)


def banda_edad(avatar_edad):
    sys.path.insert(0, os.path.join(BASE, "Ads", "_TOOLS"))
    import bandas_edad as be
    ae = (avatar_edad or "").strip()
    if not ae:
        return be.BANDA_AMPLIA_STR, "sin avatar de edad marcada — única excepción de la regla"
    destino = be.banda_str(ae)
    if destino:
        return destino, "derivada del avatar %s" % ae
    return ae, "avatar %s usado tal cual (no está en la tabla de derivación, Ads/_TOOLS/bandas_edad.py)" % ae


# El DESTINO es el 5o eje y era el unico ciego al 100% del gasto (validar_parametros, 06-sep):
# ningun anuncio declaraba a que flujo del bot manda, asi que un cambio de flujo no se podia
# evaluar contra las ventas. La version NO se escribe a mano: sale de contar los CAMBIO_BOT de
# _EVENTOS.csv, que es donde el sistema ya obliga a loguear todo cambio de flujo (CLAUDE.md).
# La numeracion arranca en V1 el 06-sep-2026 porque los cambios anteriores nunca se etiquetaron
# en ningun nombre y no son reconstruibles; el proximo CAMBIO_BOT sube a V2 solo.
DESTINO_DESDE = "2026-09-06"


def destino_actual():
    n = 1
    for r in leer_csv(EVENTOS):
        if (r.get("evento") or "").strip() == "CAMBIO_BOT" and (r.get("fecha") or "") > DESTINO_DESDE:
            n += 1
    return "BOT_V%d" % n


def lanzamiento_registrado(pk, fase):
    """(fecha "YYYY-MM-DD", campana_clave) del ÚLTIMO evento LANZAMIENTO del producto
    para esa fase en _EVENTOS.csv, o None. Un evento es de la fase si su campana_clave,
    en mayúsculas, contiene alguno de los tokens de flujo.TOKEN_FASE para esa fase."""
    sys.path.insert(0, os.path.join(BASE, "Ads", "_TOOLS"))
    import flujo
    toks = flujo.TOKEN_FASE.get(str(fase), ())
    mejor = None
    for r in leer_csv(EVENTOS):
        if (r.get("producto_key") or "").strip() != pk:
            continue
        if (r.get("evento") or "").strip() != "LANZAMIENTO":
            continue
        fecha = (r.get("fecha") or "").strip()
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", fecha):
            continue
        campana = (r.get("campana_clave") or "").strip()
        if not any(t in campana.upper() for t in toks):
            continue
        if mejor is None or fecha > mejor[0]:
            mejor = (fecha, campana)
    return mejor


def firma(producto_key, angulo_key, concepto, canonico, nivel, oferta, destino):
    """La firma NO se reimplementa aca: la construye su dueno, Ads/_TOOLS/firma.py."""
    sys.path.insert(0, os.path.join(BASE, "Ads", "_TOOLS"))
    from firma import firma as firma_canonica
    return firma_canonica({
        "producto_key": producto_key, "angulo_key": angulo_key,
        "concepto_key": concepto, "canonico_id": canonico,
        "nivel_conciencia": nivel, "oferta_key": oferta, "destino_key": destino,
    })


# ─────────────────────────────────────────────────────────────────────────────
# 2 · EL PLAN DERIVADO: nombres, plata, fechas, gates
# ─────────────────────────────────────────────────────────────────────────────

CONFIG_META_FIJA = (
    "Ubicación: %(pais)s · Sin intereses",
    "Advantage+ Audience: OFF (si no, Meta ignora la banda de edad)",
    "Optimización: Maximizar CONVERSACIONES — revisarlo justo antes de publicar: Meta lo revierte a clics con cada duplicado",
    "Destino: WhatsApp (el número conectado a la FanPage, nunca Messenger) · CTA: Enviar mensaje",
    "DESMARCAR «anuncios multianunciantes»",
    "DESMARCAR «incluir personas de WhatsApp cuya edad se desconoce»",
    "Anuncios A y B de una misma pieza: el B es copia exacta del A (misma imagen, mismo copy)",
    "Texto principal: cargar todos los TEXTOS como opciones · Títulos: todos · Descripción: la indicada",
    "Cero «- Copia» en ningún nombre: renombrar antes de publicar",
    "NO aceptar recomendaciones de Meta",
)


def derivar(prod, plan, hechos, usd_conv_portafolio):
    pk = prod["producto_key"]
    cuenta = (prod.get("cuenta_alias") or "").strip()
    cuenta_ok = bool(cuenta) and cuenta.upper() not in ("PENDIENTE", "")
    moneda = (prod["moneda"] or "").strip().upper()
    fase = int(plan.get("fase") or 1)
    est = ESTRUCTURA[fase]

    h = hechos.get(pk, {})
    usd_conv = h.get("usd_por_conversacion") or usd_conv_portafolio
    presup, presup_por_que = presupuesto_por_fase(fase, usd_conv)

    tasa = num(prod.get("tasa"))          # sin tasa no hay be_usd ni CPA en Q: quedan en None, con aviso
    if not tasa or tasa <= 0:
        tasa = None
        print("AVISO gen_lanzador: «%s» no declara `tasa` en _DIM_PRODUCTOS.csv: sin dias de PD ni "
              "CPA acumulado en moneda local (no hay tasa por defecto)." % pk, file=sys.stderr)
    be_q = num(prod.get("cpa_be_q"))
    be_usd = be_q / tasa if be_q and tasa else 0.0
    dias_pd = (be_usd / presup / FACTOR_ENTREGA) if (be_usd and presup) else None

    lanzamiento = HOY + datetime.timedelta(days=1)
    reg = lanzamiento_registrado(pk, fase)
    if reg:
        lanzamiento = datetime.datetime.strptime(reg[0], "%Y-%m-%d").date()
    ymd = lanzamiento.strftime("%Y%m%d")

    # ── bloqueantes: lo que impide publicar ──────────────────────────────────
    bloqueantes = []
    if presup is None:
        bloqueantes.append({"que": "presupuesto por conjunto sin fila VIGENTE (%s)" % presup_por_que,
                            "quien": "PRODUCTOS/_PARAMETROS_PUBLICACION.csv"})
        presup = 0.0
    if not cuenta_ok:
        bloqueantes.append({"que": "cuenta publicitaria sin asignar",
                            "quien": "operador · _DIM_PRODUCTOS.csv columna cuenta_alias"})
    if not (prod.get("page_id") or (plan.get("pagina") or {}).get("page_id")):
        bloqueantes.append({"que": "page_id de la FanPage sin asignar",
                            "quien": "etapa-2 · _DIM_PRODUCTOS.csv columna page_id"})
    if not moneda:
        bloqueantes.append({"que": "moneda de la cuenta publicitaria sin declarar",
                            "quien": "operador · _DIM_PRODUCTOS.csv columna moneda"})
    if moneda and moneda != "USD" and not tasa:
        bloqueantes.append({"que": "tasa sin declarar: no se puede dar el presupuesto en %s" % moneda,
                            "quien": "operador · _DIM_PRODUCTOS.csv columna tasa"})
    if not be_q:
        bloqueantes.append({"que": "break-even sin calcular",
                            "quien": "etapa-1 · Ads/_TOOLS/costear.py"})
    con_precio = sum(1 for c in plan.get("conjuntos", []) if c.get("lleva_precio"))
    if con_precio > MAX_CONJUNTOS_CON_PRECIO:
        bloqueantes.append({"que": "%d conjuntos con precio (el máximo en Guatemala es %d, ideal 2)"
                                   % (con_precio, MAX_CONJUNTOS_CON_PRECIO),
                            "quien": "etapa-6 · regla de precio en creativo"})

    prod_corto = corto(prod)
    cta = cuenta if cuenta_ok else "[CUENTA]"

    sys.path.insert(0, os.path.join(BASE, "Ads", "_TOOLS"))
    import mercado as _mercado
    try:
        pais = _mercado.perfil_de_fila(prod)["pais"]
    except _mercado.MercadoError:
        bloqueantes.append({"que": "mercado del producto sin declarar o inexistente",
                            "quien": "operador · _DIM_PRODUCTOS.csv columna mercado"})
        pais = "[PAÍS]"

    if fase == 1:
        campanas = [{"rol": "única", "nombre": "%s_%s_TEST_%s" % (cta, prod_corto, ymd),
                     "objetivo": "Tráfico (OUTCOME_TRAFFIC) · Maximizar conversaciones · WhatsApp",
                     "presupuesto": "ABO — el presupuesto vive en el conjunto"}]
    elif fase == 2:
        campanas = [
            {"rol": "A · 1-1-5, conceptos 1-5",
             "nombre": "%s_%s_CONCEPTOS-A_%s" % (cta, prod_corto, ymd),
             "objetivo": "Tráfico · Maximizar conversaciones · WhatsApp",
             "presupuesto": "ABO · $6/día"},
            {"rol": "B · 1-1-5, conceptos 6-10",
             "nombre": "%s_%s_CONCEPTOS-B_%s" % (cta, prod_corto, ymd),
             "objetivo": "Tráfico · Maximizar conversaciones · WhatsApp",
             "presupuesto": "ABO · $6/día"},
            {"rol": "C · 1-2-5, LOS MISMOS 10 · OTRA CUENTA",
             "nombre": "[OTRA-CUENTA]_%s_CONCEPTOS-C_%s" % (prod_corto, ymd),
             "objetivo": "Tráfico · Maximizar conversaciones · WhatsApp",
             "presupuesto": "ABO · $12/día"},
        ]
    else:
        campanas = [{"rol": "única · CBO",
                     "nombre": "%s_%s_ESCALA-%s_%s" % (
                         cta, prod_corto,
                         guion((plan.get("concepto_control") or {}).get("concepto_key") or "GANADOR"),
                         ymd),
                     "objetivo": "Tráfico · Maximizar conversaciones · WhatsApp",
                     "presupuesto": "CBO — el presupuesto vive en la campaña"}]

    # ── conjuntos ─────────────────────────────────────────────────────────────
    cc = plan.get("concepto_control") or {}
    oferta = plan.get("oferta") or {}
    conjuntos = []
    presup_cuenta, presup_cuenta_texto = monto_cuenta(presup, moneda, tasa)
    for c in plan.get("conjuntos", []):
        ak = c.get("angulo_key") or "SIN-ANGULO"
        banda, banda_por_que = banda_edad(c.get("avatar_edad"))
        nombre = "%s_%s_%s_R1" % (cta, prod_corto, guion(ak))
        fmt = "IMG" if (c.get("formato") or "IMAGEN").upper() == "IMAGEN" else "VID"
        fir = firma(pk, ak, cc.get("concepto_key"), cc.get("canonico_id"),
                    c.get("nivel_conciencia"),
                    oferta.get("oferta_key") if c.get("lleva_precio") else "SIN_PRECIO",
                    destino_actual())
        anuncios = [{"letra": l, "nombre": "%s_%s_%s ~ %s" % (guion(ak), fmt, l, fir)}
                    for l in ("A", "B")]
        conjuntos.append({
            "n": c.get("n"),
            "angulo_key": ak,
            "angulo_titulo": c.get("angulo_titulo"),
            "nombre": nombre,
            "presupuesto_usd": presup,
            "presupuesto_centavos": int(round(presup * 100)),
            "presupuesto_cuenta": presup_cuenta,
            "presupuesto_cuenta_texto": presup_cuenta_texto,
            "banda_edad": banda,
            "banda_por_que": banda_por_que,
            "genero": c.get("avatar_genero") or "MIXTO",
            "formato": c.get("formato"),
            "lleva_precio": bool(c.get("lleva_precio")),
            "archivo_creativo": c.get("archivo_creativo"),
            "prompt_imagen": c.get("prompt_imagen"),
            "firma": fir,
            "anuncios": anuncios,
            "copy": c.get("copy") or {},
        })

    # ── el calendario de decision, con fechas reales ─────────────────────────
    def f(d):
        return (lanzamiento + datetime.timedelta(days=d)).strftime("%d-%b").lower()

    calendario = [
        {"orden": 0, "dia": "Día 0", "fecha": lanzamiento.strftime("%d-%b").lower(),
         "que": "Lanza a las 4 AM", "hace": "nada — no se toca nada más hoy",
         "manda": None},
        {"orden": 1, "dia": "Días 1-2", "fecha": "%s → %s" % (f(1), f(2)),
         "que": "Meta está en aprendizaje", "hace": "observar clics-enlace y %conv. NO pausar, NO escalar",
         "manda": "nada — el reloj de ENTREGA es automático"},
        {"orden": 3, "dia": "Día 3", "fecha": f(3),
         "que": "GATE 1 · corte por conversación",
         "hace": ("apagar los 2-3 peores por conversación (%conv/clic-enlace) y subir los "
                  "sobrevivientes a $" + ("%.2f" % PRESUPUESTO_E2)),
         "manda": "export de Meta Ads Manager (no hace falta LucidSales)"},
        {"orden": 4, "dia": "Día 4", "fecha": f(4),
         "que": "GATE 2 · validación", "hace": "ya hay CPA formándose; arranca FASE 2 del ganador #1",
         "manda": "export de LucidSales de 7 días"},
        {"orden": (dias_pd if dias_pd else 99),
         "dia": "Día %s" % (round(dias_pd, 1) if dias_pd else "?"),
         "fecha": f(int(math.ceil(dias_pd))) if dias_pd else "—",
         "que": "PRESUPUESTO DE DECISIÓN alcanzado",
         "hace": "recién acá un '0 ventas' es veredicto y no falta de exposición",
         "manda": "export de LucidSales"},
        {"orden": 999, "dia": "Domingo", "fecha": "cada semana",
         "que": "ingesta principal", "hace": "el sistema decide qué se poda y qué se escala",
         "manda": "export de LucidSales de 7 días"},
    ]
    calendario.sort(key=lambda c: c["orden"])

    return {
        "producto_key": pk,
        "nombre": prod.get("nombre_display") or pk,
        "estado": prod.get("estado"),
        "cuenta": cuenta or None,
        "cuenta_ok": cuenta_ok,
        "pagina": (plan.get("pagina") or {}).get("nombre"),
        "page_id": prod.get("page_id") or (plan.get("pagina") or {}).get("page_id") or None,
        "fase": fase,
        "fase_nombre": est["nombre"],
        "fase_mide": est["mide"],
        "fase_forma": est["forma"],
        "fase_notacion": est["notacion"],
        "fase_presupuesto": est["presupuesto"],
        "fase_por_que": est["por_que"],
        "fase_no_es": est["no_es"],
        "fase_decide": est["decide"],
        "economia": {
            "costo_q": num(prod.get("costo_q")) or None,
            "precio_q": num(prod.get("precio_base_q")) or None,
            "cpa_base_q": num(prod.get("cpa_base_q")) or None,
            "cpa_be_q": be_q or None,
            "cpa_be_usd": round(be_usd, 2) if be_usd else None,
            "tasa": tasa,
        },
        "presupuesto": {
            "por_conjunto_usd": presup,
            "por_que": presup_por_que,
            "etapa2_usd": PRESUPUESTO_E2,
            "total_dia_usd": round(presup * len(conjuntos), 2),
            "dias_a_pd": round(dias_pd, 1) if dias_pd else None,
            "moneda_cuenta": moneda or None,
            "por_conjunto_cuenta_texto": presup_cuenta_texto,
            "total_dia_cuenta_texto": monto_cuenta(presup * len(conjuntos), moneda, tasa)[1],
        },
        "historial": h or None,
        "oferta": oferta,
        "concepto_control": cc,
        "lanzamiento": {"fecha": lanzamiento.isoformat(),
                        "legible": lanzamiento.strftime("%d-%b-%Y").lower(), "hora": "4:00 AM",
                        "registrado": bool(reg),
                        "campana_registrada": reg[1] if reg else None},
        "campanas": campanas,
        "conjuntos": conjuntos,
        "config_meta": [linea % {"pais": pais} for linea in CONFIG_META_FIJA],
        "calendario": calendario,
        "bloqueantes": bloqueantes,
        "faltantes": plan.get("_faltantes", []),
        "origen_plan": plan.get("origen"),
    }


# ─────────────────────────────────────────────────────────────────────────────
# 3 · ARMAR EL MODELO COMPLETO
# ─────────────────────────────────────────────────────────────────────────────

def construir():
    productos = leer_csv(DIM_PRODUCTOS)
    hechos = hechos_por_producto()
    usd_port = usd_por_conversacion_portafolio(hechos)

    filas = []
    for prod in productos:
        pk = prod["producto_key"]
        _tasa_prod = num(prod.get("tasa")) or None     # sin tasa: None (el aviso lo da `derivar`)
        carpeta = os.path.join("PRODUCTOS", prod.get("slug_carpeta") or pk)
        ruta_plan = os.path.join(carpeta, "_PLAN.json")
        h = hechos.get(pk)
        base = {
            "producto_key": pk,
            "nombre": prod.get("nombre_display") or pk,
            "estado": prod.get("estado"),
            "fase_csv": prod.get("fase") or None,
            "cuenta": (prod.get("cuenta_alias") or "").strip() or None,
            "cpa_be_q": num(prod.get("cpa_be_q")) or None,
            "historial": h,
            "cpa_acumulado_q": (round(h["spend_usd"] * _tasa_prod / h["ventas"], 2)
                                if h and h["ventas"] and _tasa_prod else None),
            "tiene_plan": os.path.exists(ruta_plan),
            "carpeta": carpeta.replace("\\", "/"),
        }
        if base["tiene_plan"]:
            with io.open(ruta_plan, encoding="utf-8") as fh:
                plan = json.load(fh)
            base["plan"] = derivar(prod, plan, hechos, usd_port)
        else:
            base["plan"] = None
            base["falta_para_plan"] = falta_para_plan(prod, carpeta)
        filas.append(base)

    return {
        "generado": HOY.isoformat(),
        "usd_por_conversacion_portafolio": usd_port,
        "estructura": ESTRUCTURA,
        "constantes": {
            "piso_presupuesto": PISO_PRESUPUESTO, "techo_presupuesto": TECHO_PRESUPUESTO,
            "presupuesto_etapa2": PRESUPUESTO_E2, "factor_entrega": FACTOR_ENTREGA,
            "max_conjuntos_con_precio": MAX_CONJUNTOS_CON_PRECIO,
        },
        "productos": filas,
    }


def falta_para_plan(prod, carpeta):
    """Que le falta a un producto sin _PLAN.json para poder tener uno."""
    f = []
    if not os.path.exists(os.path.join(carpeta, "2_DATA_PRODUCTO.txt")):
        f.append({"que": "no tiene 2_DATA_PRODUCTO.txt", "quien": "etapa-guardar-producto"})
    if not num(prod.get("cpa_be_q")):
        f.append({"que": "sin break-even calculado", "quien": "etapa-1 (costear.py)"})
    if not (prod.get("page_id") or "").strip():
        f.append({"que": "sin page_id de FanPage", "quien": "etapa-2"})
    cta = (prod.get("cuenta_alias") or "").strip().upper()
    if not cta or cta == "PENDIENTE":
        f.append({"que": "sin cuenta publicitaria asignada", "quien": "operador"})
    f.append({"que": "sin _PLAN.json (ángulos, prompts y copies estructurados)",
              "quien": "etapa-6 — es el paso que falta siempre"})
    return f


# ─────────────────────────────────────────────────────────────────────────────
# 4 · RENDER — vive en lanzador_html.py: este script calcula, aquel dibuja
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    modelo = construir()
    with io.open(SALIDA_JSON, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(modelo, ensure_ascii=False, indent=2))
    print("escrito %s" % SALIDA_JSON)
    if "--json" in sys.argv:
        sys.exit(0)
    sys.path.insert(0, os.path.join(BASE, "Ads", "_TOOLS"))
    from lanzador_html import HTML
    if not os.path.isdir("VISTAS"):
        os.makedirs("VISTAS")
    with io.open(SALIDA_HTML, "w", encoding="utf-8") as fh:
        fh.write(HTML(modelo))
    con = sum(1 for p in modelo["productos"] if p["tiene_plan"])
    print("escrito %s  ·  %d productos, %d con plan de lanzamiento"
          % (SALIDA_HTML, len(modelo["productos"]), con))
