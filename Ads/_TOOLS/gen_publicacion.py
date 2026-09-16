# -*- coding: utf-8 -*-
"""gen_publicacion.py — EL PAQUETE DE PUBLICACION: el plan de un producto, convertido en la
secuencia EXACTA de llamadas MCP y en el manifiesto contra el que se verifica despues.

POR QUE EXISTE (2026-09-08)
--------------------------
La publicacion era el unico paso del flujo que no tenia herramienta. `costear.py` calcula,
`decidir.py` decide, `gen_lanzador.py` dicta el flujo — pero crear la campana dependia de que
un modelo leyera `DOCTRINA/MCP_PLAYBOOK.md` (223 lineas de prosa) y se acordara de los 12
parametros. Un grep lo dice todo:

    grep -rl "ads_create" Ads/_TOOLS/     ->  cero resultados

Y ninguna etapa tiene siquiera acceso al conector: ETAPA-6 declara `tools: Read`, ETAPA-7 y
ETAPA-8 `Read, Glob, Grep`. La descripcion de ETAPA-7 dice que "Meta MCP aporta senales de
entrega" y no puede llamarlo.

El costo de eso esta medido. El 06-sep se publico una campana de TINNIDROP, nadie escribio el
`ad_id` en `_DIM_CREATIVOS.csv`, y el 08-sep el sistema creia "cero publicados" mientras Meta
llevaba $23.46 gastados en 10 anuncios ACTIVE que servian la pieza equivocada.

QUE HACE Y QUE NO HACE
----------------------
NO llama a Meta. NO gasta. NO decide. Lee el plan y los CSV, DERIVA cada parametro de su dueno
declarado, y emite dos cosas en un solo JSON:

    llamadas[]    la secuencia literal de tool calls del MCP, con todos los argumentos resueltos
    manifiesto{}  lo que TIENE que existir en Meta cuando la secuencia termine

El manifiesto es la mitad que faltaba. Con el, `verificar_publicacion.py` compara Meta contra
lo declarado y escribe los `ad_id` al CSV — que es exactamente lo que nadie hizo el 06-sep.

Si falta un dato, NO lo inventa: lo emite como BLOQUEANTE con el nombre de su dueno y sale
con exit 1 (invariante 4 de CLAUDE.md).

IDEMPOTENCIA
------------
El MCP oficial no tiene ninguna. Con `--snapshot` (un volcado de `ads_get_ad_entities` de la
cuenta), cada llamada cuyo objeto ya existe EN META POR NOMBRE se marca `omitir: true` con el
id que ya tiene. Publicar dos veces deja de duplicar la campana.

UN DATO, UN DUENO — de donde sale cada parametro
------------------------------------------------
    estructura, presupuesto, objetivo, hora     PRODUCTOS/_PARAMETROS_PUBLICACION.csv
                                                (dueno doctrinal: CALENDARIO_ESCALADO.md 1.7.2)
    cuenta_id, moneda, min budget, sube media   PRODUCTOS/_DIM_CUENTAS.csv
    producto, page_id, cpa base y break even    PRODUCTOS/_DIM_PRODUCTOS.csv
    banda de edad                               avatar_edad de _DIM_CONJUNTOS.csv,
                                                derivada por Ads/_TOOLS/bandas_edad.py
                                                (doctrina y evidencia: ETAPA-6.md)
    numero de replica R[N] (fase 1 y 3)         conjunto_meta de _DIM_CONJUNTOS.csv
                                                (siguiente_replica: nunca la posicion del loop)
    piezas, concepto_key, canonico_id           PRODUCTOS/_DIM_CREATIVOS.csv
    la FIRMA de 5 ejes                          Ads/_TOOLS/firma.py (se importa, no se copia)
    angulo ganador, page_id, copy               PRODUCTOS/[X]/_PLAN*.json (dueno: ETAPA-6)
    nombres de campana/conjunto/anuncio         .claude/agents/ETAPA-6.md CONVENCION DE NOMBRES

USO
    python Ads/_TOOLS/gen_publicacion.py --producto TINNIDROP --fase 2 --brazo A --cuenta GTR7
    python Ads/_TOOLS/gen_publicacion.py --producto TINNIDROP --fase 2 --brazo A --cuenta GTR7 \
           --snapshot Ads/_INGESTA/META/snapshot_GTR7.json
    python Ads/_TOOLS/gen_publicacion.py --producto TINNIDROP --fase 2 --brazo A --cuenta GTR7 --json
"""
import csv, io, os, re, sys, json, datetime, importlib.util

for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError): pass

BASE  = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOOLS = os.path.join(BASE, "Ads", "_TOOLS")
P     = lambda *a: os.path.join(BASE, "PRODUCTOS", *a)

if TOOLS not in sys.path:
    sys.path.insert(0, TOOLS)
import bandas_edad  # LA TABLA no se copia aca: Ads/_TOOLS/bandas_edad.py es su dueno unico.

SCHEMA = "publicacion/1"


# ---------------------------------------------------------------- utilidades

def leer(ruta):
    if not os.path.exists(ruta):
        return []
    with io.open(ruta, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def arg(flag, default=None):
    if flag in sys.argv:
        i = sys.argv.index(flag)
        if i + 1 < len(sys.argv):
            return sys.argv[i + 1]
    return default


def flag(f):
    return f in sys.argv


def corto_alias(a):
    """'GTR 7' -> 'GTR7'. El nombre de los objetos de Meta no lleva espacios (ETAPA-6, regla 6)."""
    return (a or "").replace(" ", "").upper()


def extraer_copy(c):
    """Normaliza el copy a (message, headline, description, sobrantes).

    El plan puede traerlo como texto suelto o como el bloque '1 de 5' de Meta
    ({'textos': [...], 'titulos': [...], 'descripcion': '...'}). **Por API va UN texto por
    anuncio**: el '1 de 5' no existe en la Marketing API. Las opciones que sobran no se pierden
    — se devuelven para que el paquete le diga al operador que las agregue a mano."""
    if not c:
        return "", "", "", 0
    if isinstance(c, str):
        return c.strip(), "", "", 0
    if isinstance(c, dict):
        tx = c.get("textos") or []
        ti = c.get("titulos") or []
        if isinstance(tx, str): tx = [tx]
        if isinstance(ti, str): ti = [ti]
        sobrantes = max(0, len(tx) - 1) + max(0, len(ti) - 1)
        return ((tx[0].strip() if tx else ""),
                (ti[0].strip() if ti else ""),
                (c.get("descripcion") or "").strip(),
                sobrantes)
    return "", "", "", 0


def orden_nombre_de(piezas):
    """creativo_id -> numero ESTABLE para el NOMBRE del anuncio (no el bookkeeping interno
    de la corrida, que es orden_global). Agrupa por brazo preservando el ORDEN ORIGINAL del
    CSV dentro de cada grupo — nunca reordena alfabeticamente — para que el brazo B siempre
    numere a partir de donde termina el brazo A sin importar en que orden se publiquen.
    Antes el numero salia de un contador local a la corrida (orden_global): publicar el
    brazo B por separado volvia a numerar 01-05 en vez de continuar 06-10.

    Con un solo brazo (o ninguno declarado, el estado de TODO el portafolio real hoy) el
    agrupado es un no-op y el numero coincide EXACTO con el de antes de este cambio: el
    orden de _DIM_CREATIVOS.csv no se puede alterar sin invalidar nombres ya publicados
    en Meta (el snapshot de idempotencia matchea por nombre)."""
    con_indice = list(enumerate(piezas))
    ordenadas = sorted(con_indice, key=lambda t: ((t[1].get("brazo") or ""), t[0]))
    return {r.get("creativo_id"): i for i, (_, r) in enumerate(ordenadas, 1)}


PATRON_REPLICA = re.compile(r"_R(\d+)$")


def siguiente_replica(filas_conjuntos, pk, angulo, cta):
    """El proximo numero de replica R[N] para este producto+angulo+cuenta.

    Dueno del dato: _DIM_CONJUNTOS.csv, el registro real de lo que ya vive en Meta —
    nunca la posicion del conjunto DENTRO DEL LOOP de la corrida actual. Antes ese 'i'
    local hacia que republicar (una segunda tanda, o una réplica horizontal nueva)
    volviera a nombrar R1, R2... encima de réplicas que ya existian (simulacion
    Turmeric, f71f9ec: hubo que fijarlo a mano a R1 para poder avanzar).

    ETAPA-6.md regla 2: 'el numero de replica no se reutiliza nunca'. Sin historial
    para esta cuenta arranca en R1."""
    maxn = 0
    for r in filas_conjuntos:
        if r.get("producto_key") != pk or r.get("angulo_key") != angulo:
            continue
        if corto_alias(r.get("cuenta_alias")) != cta:
            continue
        m = PATRON_REPLICA.search((r.get("conjunto_meta") or "").strip())
        if m:
            maxn = max(maxn, int(m.group(1)))
    return maxn + 1


def chequear_brazo_ambiguo(piezas, brazo_creativos, brazo_arg):
    """None si no hay ambiguedad; el mensaje de bloqueo si hay mas de un brazo declarado en
    _DIM_CREATIVOS.csv para este angulo y no se eligio con --brazo-creativos cual publicar.
    Sin este chequeo, una corrida sin el flag toma las primeras piezas del CSV sin importar
    el brazo: publicar el brazo B sin --brazo-creativos B republicaria el pool del brazo A."""
    brazos = sorted({(r.get("brazo") or "").strip() for r in piezas if (r.get("brazo") or "").strip()})
    if len(brazos) > 1 and not brazo_creativos:
        return ("hay %d brazos de creativos para este angulo en _DIM_CREATIVOS.csv (%s) y no se "
                "paso --brazo-creativos: sin especificarlo se toman las primeras piezas del CSV "
                "sin importar el brazo, y una corrida para el brazo que no es A publicaria de "
                "nuevo el pool del brazo A." % (len(brazos), ", ".join(brazos)))
    return None


def cargar_firma():
    """Importa Ads/_TOOLS/firma.py. Es el dueno de la firma; aca no se reimplementa."""
    ruta = os.path.join(TOOLS, "firma.py")
    spec = importlib.util.spec_from_file_location("firma_mod", ruta)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------- el generador

EJES_FIRMA = ("angulo_key", "concepto_key", "nivel_conciencia", "oferta_key", "destino_key")
ABIERTO = "(abierto)"


def vocabulario_de_ejes():
    """{eje: (abierto?, dueno)} desde PRODUCTOS/_DIM_VOCABULARIO.csv.

    Un eje esta ABIERTO si su vocabulario declara el valor '(abierto)': es una marca deliberada
    del dueno (hoy solo destino_key, ver PARAMETRIZACION_ADS.md: "abierto: version del flujo
    LucidBot"). Se usa esa marca y no '(vacio)', porque el vocabulario de nivel_conciencia fue
    ingerido de datos historicos y trae '(vacio)', '3a', 'NC1' y '1-2' como si fueran valores
    validos: describe lo que hubo, no lo que se exige. Cuando ETAPA-11 cierre el vocabulario de
    destino, el eje deja de estar abierto y este gate empieza a bloquearlo sin tocar codigo."""
    out = {}
    for r in leer(P("_DIM_VOCABULARIO.csv")):
        eje = (r.get("eje") or "").strip()
        if eje not in EJES_FIRMA:
            continue
        abierto, dueno = out.get(eje, (False, ""))
        out[eje] = (abierto or (r.get("valor") or "").strip() == ABIERTO,
                    dueno or (r.get("dueno_del_vocabulario") or "").strip())
    return out


def verificar_firma(unidades, fmod, pq):
    """GATE: ningun anuncio sale a Meta con un eje de su firma perdido.

    La firma viaja en el NOMBRE del anuncio y es de donde el sistema lee despues los 5 ejes de
    lo que se pauto. Un eje que sale como '?' se pierde PARA SIEMPRE: el nombre ya esta en Meta.
    Hasta el 16-sep-2026 el publicador no lo miraba, y en FASE 2/3 los tres ejes de la oferta
    salian '?' en el 100 % de los anuncios (las piezas son filas de _DIM_CREATIVOS.csv, que no
    tiene esas columnas, y nadie se los pasaba). Simulacion TURMERIC:
        TURMERIC|MANOS_RIGIDAS_AL|C2.CN06|?|?|?

    Un eje vacio BLOQUEA, con el nombre de su dueno. Un eje que el vocabulario declara ABIERTO
    solo AVISA: exigirlo seria inventar una regla que la doctrina todavia no fijo."""
    vocab = vocabulario_de_ejes()
    faltan = {}
    for u in unidades:
        for pieza in u["piezas"]:
            ejes = fmod.parsear(fmod.firma(pieza))
            for eje in EJES_FIRMA:
                if (ejes.get(eje) or fmod.VACIO) == fmod.VACIO:
                    faltan.setdefault(eje, []).append(pieza.get("creativo_id") or pieza.get("archivo") or "?")
    for eje in EJES_FIRMA:
        if eje not in faltan:
            continue
        abierto, dueno = vocab.get(eje, (False, ""))
        cuantos = len(faltan[eje])
        if abierto:
            pq.avisar("la firma sale sin %s en %d anuncio(s): el eje esta declarado ABIERTO en "
                      "_DIM_VOCABULARIO.csv (dueno %s), asi que no bloquea. Se pierde para esos "
                      "anuncios; se empieza a exigir cuando su dueno cierre el vocabulario."
                      % (eje, cuantos, dueno or "sin dueno declarado"))
        else:
            pq.bloquear("la firma sale con %s = '%s' en %d anuncio(s) (%s). Publicado asi, ese eje "
                        "se pierde para siempre: la firma viaja en el nombre del anuncio y el "
                        "sistema la lee de ahi." % (eje, fmod.VACIO, cuantos, ", ".join(faltan[eje][:4])),
                        "%s -> llega al anuncio por el plan de etapa-6" % (dueno or "etapa-6"))


class Paquete(object):
    def __init__(self):
        self.bloqueantes = []
        self.avisos = []
        self.preflight = []

    def bloquear(self, que, dueno):
        self.bloqueantes.append({"falta": que, "lo_produce": dueno})

    def avisar(self, texto):
        self.avisos.append(texto)


def derivar_banda(avatar_edad, pk):
    ae = (avatar_edad or "").strip()
    if not ae:
        return bandas_edad.BANDA_AMPLIA_TUPLA, "SIN avatar de edad marcada -> amplio 18-65 (unica excepcion de ETAPA-6)"
    tup = bandas_edad.banda_tupla(ae)
    if tup:
        return tup, "avatar_edad=%s (_DIM_CONJUNTOS.csv)" % ae
    return None, ae


def nombre_campana(fase, cuenta, producto, brazo, angulo, fecha):
    """CONVENCION DE NOMBRES — ETAPA-6.md. Separador de campos '_', dentro del campo solo '-'."""
    d = fecha.strftime("%Y%m%d")
    if fase == 1:
        return "%s_%s_TEST_%s" % (cuenta, producto, d)
    if fase == 2:
        return "%s_%s_CONCEPTOS-%s_%s" % (cuenta, producto, brazo, d)
    return "%s_%s_ESCALA-%s_%s" % (cuenta, producto, angulo.replace("_", "-"), d)


def nombre_conjunto(fase, cuenta, producto, angulo, brazo, numero):
    """FASE 2: 'numero' es la posicion del conjunto dentro del brazo (A1, A2...).
    FASE 1 y 3: 'numero' es el R[N] YA RESUELTO por el llamador via siguiente_replica() —
    nunca la posicion del loop (ver PATRON_REPLICA / invariante 12)."""
    ang = angulo.replace("_", "-")
    if fase == 2:
        return "%s_%s_%s_%s%d" % (cuenta, producto, ang, brazo, numero)
    return "%s_%s_%s_R%d" % (cuenta, producto, ang, numero)


def nombre_anuncio(fase, cre, orden, angulo, fmt, letra, fmod):
    """FASE 2: [CONCEPTO]_[VARIANTE]_[NN]. Otras fases: [ANGULO]_[FORMATO]_[A|B].
    En las tres, la FIRMA va despues de ' ~ ' — es obligatoria en todo anuncio nuevo.

    El sufijo ' A' / ' B' de la regla del duplicado interno va en LOS DOS anuncios, nunca en
    uno solo: dos objetos con el mismo nombre son indistinguibles en cualquier export y el
    JOIN del sistema es por nombre (asi quedaron 'tinnidrop 6' y 'tinnidrop 6 - Copia')."""
    f = fmod.firma(cre)
    if fase == 2:
        concepto = (cre.get("concepto_key") or "?").replace("_", "-")
        variante = (cre.get("variante") or "BASE").upper().replace("_", "-")
        return "%s_%s_%02d %s ~ %s" % (concepto, variante, orden, letra, f)
    return "%s_%s_%s ~ %s" % (angulo.replace("_", "-"), fmt, letra, f)


def main():
    pk_in   = arg("--producto")
    fase    = arg("--fase")
    brazo   = (arg("--brazo") or "").upper()
    cuenta  = arg("--cuenta")
    lanz    = arg("--lanzamiento")
    ruta_pl = arg("--plan")
    snap    = arg("--snapshot")
    salida  = arg("--salida")

    if not pk_in or not fase:
        print(__doc__)
        return 2
    fase = int(fase)
    pq = Paquete()
    fmod = cargar_firma()

    # ---------- 1. producto ------------------------------------------------
    productos = {r["producto_key"]: r for r in leer(P("_DIM_PRODUCTOS.csv"))}
    pk = pk_in if pk_in in productos else None
    if not pk:
        print("BLOQUEANTE: '%s' no tiene fila en _DIM_PRODUCTOS.csv." % pk_in)
        print("            La llave del sistema es producto_key (invariante 10): la carpeta se")
        print("            resuelve leyendo el CSV, nunca adivinando por el nombre.")
        return 1
    prod = productos[pk]

    # ---------- 2. parametros de la fase ----------------------------------
    if not brazo:
        brazo = "A" if fase == 2 else "UNICO"
    params = [r for r in leer(P("_PARAMETROS_PUBLICACION.csv"))
              if r["fase"] == str(fase) and r["brazo"] == brazo and r.get("estado") == "VIGENTE"]
    if not params:
        print("BLOQUEANTE: no hay fila VIGENTE en _PARAMETROS_PUBLICACION.csv para fase=%s brazo=%s."
              % (fase, brazo))
        return 1
    par = params[0]

    # ---------- 3. cuenta --------------------------------------------------
    cuentas = leer(P("_DIM_CUENTAS.csv"))
    alias_pedido = corto_alias(cuenta or prod.get("cuenta_alias"))
    fila_cta = next((c for c in cuentas if corto_alias(c["cuenta_alias"]) == alias_pedido), None)
    if not fila_cta:
        print("BLOQUEANTE: la cuenta '%s' no existe en _DIM_CUENTAS.csv." % alias_pedido)
        return 1
    if fila_cta["mcp_habilitado"] != "SI":
        pq.bloquear("la cuenta %s NO tiene el MCP habilitado (%s). Publicar por MCP es imposible "
                    "en esta cuenta: o se pauta a mano, o se mueve el producto a una cuenta habilitada."
                    % (alias_pedido, fila_cta.get("notas") or "rollout"), "Meta (rollout)")
    if fila_cta["tiene_metodo_pago"] != "SI":
        pq.bloquear("la cuenta %s no tiene metodo de pago: puede crear, no puede gastar." % alias_pedido,
                    "el operador, en Business Manager")

    moneda = fila_cta["moneda"]
    minimo = int(fila_cta["min_daily_budget_cents"])
    presu_usd = float(par["daily_budget_usd"])
    if moneda != "USD":
        pq.bloquear("la cuenta %s factura en %s y el presupuesto de la doctrina esta en USD. "
                    "El daily_budget va SIEMPRE en la unidad menor de la moneda de la cuenta."
                    % (alias_pedido, moneda), "DOCTRINA/CALENDARIO_ESCALADO.md")
        presu_cents = None
    else:
        presu_cents = int(round(presu_usd * 100))
        if presu_cents < minimo:
            pq.bloquear("presupuesto %d centavos < minimo de la cuenta (%d)" % (presu_cents, minimo),
                        "_DIM_CUENTAS.csv")

    # ---------- 4. plan ----------------------------------------------------
    carpeta = prod.get("slug_carpeta") or pk
    if not ruta_pl:
        cand = [P(carpeta, "_PLAN_FASE%d.json" % fase), P(carpeta, "_PLAN.json")]
        ruta_pl = next((c for c in cand if os.path.exists(c)), None)
    plan = {}
    if ruta_pl and os.path.exists(ruta_pl):
        with io.open(ruta_pl, encoding="utf-8") as f:
            plan = json.load(f)
    else:
        pq.bloquear("no existe _PLAN_FASE%d.json ni _PLAN.json en PRODUCTOS/%s/" % (fase, carpeta),
                    "etapa-6")

    # FASE 1 mide el ANGULO: cada conjunto lleva uno distinto y no hay ganador todavia.
    # FASE 2 y 3 miden otra cosa sobre un angulo YA GANADO: ahi el angulo es uno y es fijo.
    angulo = (plan.get("angulo_ganador") or plan.get("angulo_key") or "").strip()
    if fase in (2, 3) and not angulo:
        pq.bloquear("el plan no declara angulo_ganador. En FASE 2 y 3 el angulo es FIJO y va en el "
                    "nombre del CONJUNTO; sin el, la agregacion por angulo_key se parte.", "etapa-6")

    # page_id: el del plan manda sobre el del producto, porque la pagina depende de la CUENTA
    page_id = str(plan.get("page_id") or prod.get("page_id") or "").strip()
    if not page_id:
        pq.bloquear("no hay page_id", "etapa-fanpage")
    if plan.get("cuenta") and corto_alias(plan["cuenta"]) != alias_pedido:
        pq.avisar("el plan dice cuenta=%s y se esta publicando en %s. La pagina y su WhatsApp tienen "
                  "que estar asignados a la cuenta DONDE SE PUBLICA, no a la del plan. El page_id %s "
                  "viene del plan: confirmalo en el pre-flight antes de crear el primer conjunto."
                  % (plan["cuenta"], alias_pedido, page_id))

    # ---------- 5-6. UNIDADES: que conjunto lleva que angulo, que banda y que piezas -------
    #
    # Las dos formas del sistema, y por que no se pueden tratar igual:
    #   FASE 1  6 conjuntos, un ANGULO DISTINTO en cada uno, concepto FIJO.  La banda sale del
    #           avatar_edad DE CADA ANGULO: son avatares distintos, no una constante de campana.
    #   FASE 2/3  1 angulo ya ganado, fijo en todos los conjuntos. La variable es otra.
    n_conj = int(par["conjuntos"])
    n_ads  = int(par["anuncios_por_conjunto"])
    carpeta_media = prod.get("carpeta_media") or ("MEDIA_" + pk)

    def resolver_archivo(arch):
        if not arch:
            return None
        r = os.path.join(BASE, "Ads", carpeta_media, arch)
        return r if os.path.exists(r) else None

    def banda_de(avatar_edad, contexto):
        b, orig = derivar_banda(avatar_edad, pk)
        if b is None:
            pq.bloquear("%s: avatar_edad='%s' no esta en la tabla de derivacion. No se "
                        "inventa una banda: o se agrega la fila a la tabla, o se corrige el avatar."
                        % (contexto, orig), "Ads/_TOOLS/bandas_edad.py")
            return (None, None), orig
        return b, orig

    unidades = []
    sin_archivo = []
    orden_nombre_por_creativo = {}   # fase 1 no lo usa: el orden del nombre sale del contador local

    if fase == 1:
        plan_conj = plan.get("conjuntos") or []
        if len(plan_conj) < n_conj:
            pq.bloquear("la FASE 1 se monta con %d angulos y el plan trae %d. Se testean 6 angulos "
                        "distintos con el concepto FIJO; con menos, la comparacion entre angulos "
                        "queda incompleta." % (n_conj, len(plan_conj)), "etapa-2 (fichas de angulo)")
        ctrl = plan.get("concepto_control") or {}
        for i, c in enumerate(plan_conj[:n_conj], 1):
            ang = (c.get("angulo_key") or "").strip()
            if not ang:
                pq.bloquear("el conjunto %d del plan no declara angulo_key" % i, "etapa-2")
                ang = "SIN-ANGULO"
            b, orig = banda_de(c.get("avatar_edad"), "conjunto %d (%s)" % (i, ang))
            arch = (c.get("archivo_creativo") or "").strip()
            ruta = resolver_archivo(arch)
            if not ruta:
                sin_archivo.append(arch or "(conjunto %d sin archivo_creativo)" % i)
            unidades.append({
                "angulo": ang, "banda": b, "origen_banda": orig,
                "piezas": [{
                    "creativo_id": os.path.splitext(arch)[0] or ("conj%d" % i),
                    "archivo": arch, "_ruta": ruta,
                    "copy": c.get("copy"),
                    "producto_key": pk, "angulo_key": ang,
                    "concepto_key": ctrl.get("concepto_key"),
                    "canonico_id": ctrl.get("canonico_id"),
                    "nivel_conciencia": c.get("nivel_conciencia"),
                    "oferta_key": (plan.get("oferta") or {}).get("oferta_key"),
                    "destino_key": plan.get("destino_key"),
                    "formato": c.get("formato") or "IMAGEN",
                    "variante": ctrl.get("variante"),
                }],
            })
    else:
        piezas_del_angulo = [r for r in leer(P("_DIM_CREATIVOS.csv"))
                              if r.get("producto_key") == pk and r.get("angulo_key") == angulo]

        orden_nombre_por_creativo = orden_nombre_de(piezas_del_angulo)
        error_brazo = chequear_brazo_ambiguo(piezas_del_angulo, arg("--brazo-creativos"), brazo)
        if error_brazo:
            pq.bloquear(error_brazo, "el operador (pasar --brazo-creativos %s)" % brazo)

        piezas = piezas_del_angulo
        if arg("--brazo-creativos"):
            piezas = [r for r in piezas if r.get("brazo") == arg("--brazo-creativos")]
        # Los tres ejes de la oferta NO viven en _DIM_CREATIVOS.csv: son constantes de la fase y
        # los declara el plan (mismo lugar de donde los toma la FASE 1). Sin esto la firma de toda
        # pieza de FASE 2/3 salia '?|?|?'. Solo se completa lo vacio: si la fila trae valor, manda la fila.
        nc_plan = next((c.get("nivel_conciencia") for c in (plan.get("conjuntos") or [])
                        if (c.get("nivel_conciencia") or "").strip()), None)
        ejes_plan = {"nivel_conciencia": nc_plan,
                     "oferta_key": (plan.get("oferta") or {}).get("oferta_key"),
                     "destino_key": plan.get("destino_key")}
        listas = []
        for r in piezas:
            for eje, valor in ejes_plan.items():
                if not (r.get(eje) or "").strip():
                    r[eje] = valor
            arch = (r.get("archivo") or "").strip()
            ruta = resolver_archivo(arch)
            if ruta:
                r["_ruta"] = ruta
                r.setdefault("copy", "")
                listas.append(r)
            else:
                sin_archivo.append(arch or r.get("creativo_id"))

        necesarias = n_conj * n_ads
        if len(listas) < necesarias:
            pq.bloquear("hacen falta %d piezas para un %s y hay %d con archivo en disco. "
                        "R3F-13: una fase no arranca sin su pool completo — sin el no hay "
                        "replicacion 'gana en 2 de 2', que es lo unico que corona un concepto."
                        % (necesarias, par["estructura"], len(listas)),
                        "etapa-9 (fabrica de conceptos)")

        conjuntos_dim = [r for r in leer(P("_DIM_CONJUNTOS.csv"))
                         if r.get("producto_key") == pk and r.get("angulo_key") == angulo]
        avatar_edad = next((r.get("avatar_edad") for r in conjuntos_dim if r.get("avatar_edad")), "")
        b, orig = banda_de(avatar_edad, "angulo %s" % angulo)
        for i in range(1, n_conj + 1):
            pool = listas[(i - 1) * n_ads: i * n_ads] if n_conj > 1 else listas[:n_ads]
            unidades.append({"angulo": angulo, "banda": b, "origen_banda": orig, "piezas": pool})

    if sin_archivo:
        pq.bloquear("%d pieza(s) declaradas no tienen su archivo en disco: %s. Sin el archivo no "
                    "hay media que subir y el anuncio no se puede crear."
                    % (len(sin_archivo), ", ".join(str(s) for s in sin_archivo[:6])),
                    "etapa-render / el operador")

    # Ningun anuncio sale con un eje de su firma perdido (se pierde para siempre en Meta).
    verificar_firma(unidades, fmod, pq)

    banda = unidades[0]["banda"] if unidades else (None, None)
    origen_banda = unidades[0]["origen_banda"] if unidades else "sin unidades"
    bandas_distintas = len({u["banda"] for u in unidades}) > 1

    # ---------- 7. fecha de lanzamiento -----------------------------------
    hoy = datetime.date.today()
    fecha = datetime.datetime.strptime(lanz, "%Y-%m-%d").date() if lanz else hoy + datetime.timedelta(days=1)
    if fecha <= hoy:
        pq.bloquear("lanzamiento %s no es posterior a hoy (%s). Invariante 7: siempre 4 AM del dia "
                    "SIGUIENTE, nunca el mismo dia." % (fecha, hoy), "CLAUDE.md invariante 7")
    start_time = "%sT%s:00%s" % (fecha.isoformat(), par["hora_lanzamiento"], par["tz_offset"])

    # ---------- 8. snapshot para idempotencia ------------------------------
    existentes = {}
    if snap and os.path.exists(snap):
        with io.open(snap, encoding="utf-8") as f:
            sd = json.load(f)
        objetos = sd if isinstance(sd, list) else sd.get("ad_entities", sd.get("objetos", []))
        if isinstance(objetos, str):
            objetos = json.loads(objetos)
        for o in objetos:
            if o.get("name"):
                existentes[o["name"].strip()] = o.get("id")
    elif snap:
        pq.avisar("--snapshot apunta a un archivo que no existe: %s. Sin snapshot NO hay chequeo de "
                  "idempotencia; el ejecutor tiene que preguntarle a Meta que existe antes de crear "
                  "(fue el error del 08-sep: publicar sobre el diagnostico del CSV)." % snap)

    # ---------- 9. nombres y llamadas --------------------------------------
    cta = corto_alias(fila_cta["cuenta_alias"])
    acct = fila_cta["cuenta_id"]
    camp = nombre_campana(fase, cta, pk, brazo, angulo, fecha)
    cbo = par["presupuesto_nivel"] == "CAMPANA"

    llamadas, manif_conj = [], []
    n = 0

    n += 1
    args_camp = {
        "ad_account_id": acct,
        "campaign_name": camp,
        "objective": par["objetivo"],
        "buying_type": par["buying_type"],
        "special_ad_categories": "[]",
    }
    if cbo and presu_cents:
        args_camp["campaign_daily_budget"] = presu_cents
    llamadas.append({
        "n": n, "tool": "ads_create_campaign", "args": args_camp,
        "guardar_como": "campaign_id",
        "omitir": camp in existentes,
        "id_existente": existentes.get(camp),
        "nota": "ABO: el presupuesto NO va aca, va en el conjunto." if not cbo
                else "CBO: el presupuesto va aca, y los conjuntos NO llevan daily_budget.",
    })

    # R[N] (fase 1 y 3) sale de lo que YA existe en _DIM_CONJUNTOS.csv para este
    # producto+angulo+cuenta, nunca de la posicion del conjunto en este loop — ver
    # siguiente_replica(). En fase 2 el numero sigue siendo la posicion dentro del brazo.
    filas_conjuntos = leer(P("_DIM_CONJUNTOS.csv"))
    base_replica, pos_en_angulo = {}, {}

    orden_global = 0
    for i, uni in enumerate(unidades, 1):
        ang_u = uni["angulo"]
        banda_u = uni["banda"]
        if fase == 2:
            numero_conj = i
        else:
            base_replica.setdefault(ang_u, siguiente_replica(filas_conjuntos, pk, ang_u, cta))
            pos_en_angulo[ang_u] = pos_en_angulo.get(ang_u, 0) + 1
            numero_conj = base_replica[ang_u] + pos_en_angulo[ang_u] - 1
        cj = nombre_conjunto(fase, cta, pk, ang_u, brazo, numero_conj)
        n += 1
        targeting = {
            "geo_locations": {"countries": ["GT"]},
            "age_min": banda_u[0], "age_max": banda_u[1],
            "targeting_automation": {"advantage_audience": int(par["advantage_audience"])},
        }
        args_cj = {
            "ad_account_id": acct,
            "campaign_id": "{{campaign_id}}",
            "ad_set_name": cj,
            "billing_event": par["billing_event"],
            "optimization_goal": par["optimization_goal"],
            "destination_type": par["destination_type"],
            "promoted_object": json.dumps({"page_id": page_id}),
            "targeting": json.dumps(targeting, ensure_ascii=False),
            "start_time": start_time,
        }
        if not cbo and presu_cents:
            args_cj["daily_budget"] = presu_cents
        llamadas.append({
            "n": n, "tool": "ads_create_ad_set", "args": args_cj,
            "guardar_como": "adset_id_%d" % i,
            "omitir": cj in existentes,
            "id_existente": existentes.get(cj),
            "nota": "destination_type=WHATSAPP + promoted_object.page_id son lo que hace que Meta "
                    "enrute por Click-to-WhatsApp y el mensaje llegue con el bloque referral. "
                    "Sin eso el conjunto nace CIEGO: gasta, trae conversaciones y marca 0 ventas "
                    "para siempre (APR-035).",
        })

        ads_conj = []
        for cre in uni["piezas"]:
            orden_global += 1
            orden_nombre = orden_nombre_por_creativo.get(cre.get("creativo_id"), orden_global)
            fmt = (cre.get("formato") or "IMG")[:3].upper()
            an = nombre_anuncio(fase, cre, orden_nombre, ang_u, fmt, "A", fmod)
            copy, titular, descripcion, sobrantes = extraer_copy(cre.get("copy") or plan.get("copy"))
            if not copy:
                pq.bloquear("el anuncio '%s' no tiene copy. El copy vive en el CREATIVO de Meta y no "
                            "se puede cambiar despues: ads_update_entity no reemplaza el creativo de "
                            "un anuncio existente, hay que crear uno nuevo." % an.split(" ~ ")[0],
                            "etapa-4 (copies)")
            if sobrantes:
                pq.avisar("'%s' trae %d opcion(es) extra de texto/titulo. El '1 de 5' NO existe en "
                          "la Marketing API: por MCP va una sola y el resto lo agrega el operador a "
                          "mano en el Administrador." % (an.split(" ~ ")[0], sobrantes))

            n += 1
            llamadas.append({
                "n": n, "tool": "ads_creative_upload_media",
                "args": {"ad_account_id": acct, "upload_source": "LOCAL_FILE"},
                "guardar_como": "image_hash_%d" % orden_global,
                "archivo_local": cre.get("_ruta") or "{{FALTA_ARCHIVO: %s}}" % (cre.get("archivo") or "?"),
                "nombre_en_biblioteca": os.path.splitext(cre.get("archivo") or "SIN_ARCHIVO")[0] + "_V2",
                "omitir": False,
                "nota": "LOCAL_FILE abre un widget donde el operador elige el archivo y SOLO esta "
                        "habilitado en GTR 7 (_DIM_CUENTAS.csv). NUNCA reusar el nombre de una pieza "
                        "vieja: Meta guarda las dos y quedan indistinguibles por nombre — el 08-sep "
                        "se publicaron 10 anuncios con la pieza del 06-sep por eso. Sufijo _V2/_V3."
                        if fila_cta["sube_media_local"] == "SI"
                        else "ESTA CUENTA NO SUBE MEDIA LOCAL: el operador la sube a mano a la "
                             "biblioteca y el ejecutor lee el hash con ads_get_ad_images.",
            })

            n += 1
            llamadas.append({
                "n": n, "tool": "ads_create_creative",
                "args": {
                    "ad_account_id": acct, "page_id": page_id,
                    "name": an.split(" ~ ")[0],
                    "image_hash": "{{image_hash_%d}}" % orden_global,
                    "message": copy or "{{FALTA_COPY}}",
                    "headline": titular,
                    "description": descripcion,
                    "call_to_action_type": "WHATSAPP_MESSAGE",
                },
                "guardar_como": "creative_id_%d" % orden_global,
                "omitir": False,
                "nota": "El link_url del wa.me NO va: con destination_type=WHATSAPP en el conjunto, "
                        "el destino lo enruta el conjunto y el CTA va sin value.link (APR-035).",
            })

            for letra in ("A", "B"):
                nom = nombre_anuncio(fase, cre, orden_nombre, ang_u, fmt, letra, fmod)
                n += 1
                llamadas.append({
                    "n": n, "tool": "ads_create_ad",
                    "args": {
                        "ad_account_id": acct,
                        "ad_set_id": "{{adset_id_%d}}" % i,
                        "ad_name": nom,
                        "creative": json.dumps({"creative_id": "{{creative_id_%d}}" % orden_global}),
                    },
                    "guardar_como": "ad_id_%d%s" % (orden_global, letra),
                    "omitir": nom in existentes,
                    "id_existente": existentes.get(nom),
                    "nota": "2 anuncios identicos por concepto (regla del duplicado interno).",
                })
                ads_conj.append({
                    "nombre": nom, "letra": letra,
                    "creativo_id": cre.get("creativo_id"),
                    "archivo": cre.get("archivo"),
                    "concepto_key": cre.get("concepto_key"),
                    "canonico_id": cre.get("canonico_id"),
                    "firma": fmod.firma(cre),
                    "orden": orden_global,
                })

        manif_conj.append({"nombre": cj, "posicion": i, "angulo": ang_u,
                           "banda_edad": {"age_min": banda_u[0], "age_max": banda_u[1],
                                          "origen": uni["origen_banda"]},
                           "daily_budget_usd": None if cbo else presu_usd,
                           "anuncios": ads_conj})

    # ---------- 10. pre-flight (lo corre el ejecutor, no este script) ------
    pq.preflight = [
        {"paso": 1, "llamada": "ads_get_ad_accounts",
         "verificar": "que %s (%s) tenga is_ads_mcp_enabled=true y is_queryable=true" % (cta, acct)},
        {"paso": 2, "llamada": "ads_get_ad_entities level=campaign",
         "verificar": "PREGUNTARLE A META QUE YA EXISTE antes de crear nada. El CSV no es evidencia "
                      "del estado de Meta: el 08-sep decia 'cero publicados' con $23.46 ya gastados. "
                      "Guardar la respuesta y volver a correr este generador con --snapshot."},
        {"paso": 3, "llamada": "ads_get_user_pages",
         "verificar": "que el page_id %s exista, sea visible para el lanzador y tenga WhatsApp "
                      "conectado en la cuenta %s" % (page_id, cta)},
        {"paso": 4, "llamada": "ads_create_ad_set (el primero)",
         "verificar": "es el test real de la pagina: si el primer conjunto la acepta, esta bien. "
                      "ads_get_ad_account_pages puede tardar en listarla (lag de lectura)."},
    ]

    paquete = {
        "schema": SCHEMA,
        "generado_el": datetime.datetime.now().isoformat(timespec="seconds"),
        "producto_key": pk, "fase": fase, "brazo": brazo,
        "angulo": angulo if fase in (2, 3) else "VARIOS (uno por conjunto — la FASE 1 mide el angulo)",
        "cuenta_alias": cta, "cuenta_id": acct, "moneda": moneda,
        "page_id": page_id,
        "estructura": par["estructura"],
        "presupuesto_nivel": par["presupuesto_nivel"],
        "daily_budget_usd_por_conjunto": None if cbo else presu_usd,
        "daily_budget_cents": presu_cents,
        "banda_edad": {"age_min": banda[0], "age_max": banda[1], "origen": origen_banda},
        "advantage_audience": int(par["advantage_audience"]),
        "start_time": start_time,
        "estado_al_crear": "PAUSED",
        "plan": os.path.relpath(ruta_pl, BASE) if ruta_pl else None,
        "fuente_doctrina": par["fuente_doctrina"],
        "preflight": pq.preflight,
        "bloqueantes": pq.bloqueantes,
        "avisos": pq.avisos,
        "llamadas": llamadas,
        "manifiesto": {
            "campana": camp,
            "conjuntos": manif_conj,
            "total_conjuntos": n_conj,
            "total_anuncios": sum(len(c["anuncios"]) for c in manif_conj),
        },
    }

    if not salida:
        salida = P(carpeta, "_PUBLICACION_F%d%s.json" % (fase, "" if brazo == "UNICO" else brazo))
    with io.open(salida, "w", encoding="utf-8") as f:
        json.dump(paquete, f, ensure_ascii=False, indent=2)

    if flag("--json"):
        print(json.dumps(paquete, ensure_ascii=False, indent=2))
        return 1 if pq.bloqueantes else 0

    # ---------- reporte legible -------------------------------------------
    print("=" * 78)
    print("PAQUETE DE PUBLICACION  ·  %s  ·  FASE %d brazo %s  ·  %s" % (pk, fase, brazo, cta))
    print("=" * 78)
    print("  estructura      %s (%d conjunto(s) x %d concepto(s) x 2 anuncios)"
          % (par["estructura"], n_conj, n_ads))
    print("  presupuesto     %s USD/dia %s  (%s cents)"
          % (presu_usd, "en la CAMPANA (CBO)" if cbo else "por CONJUNTO (ABO)", presu_cents))
    adv = "OFF" if par["advantage_audience"] == "0" else "ON"
    if bandas_distintas:
        print("  banda de edad   una por conjunto (Advantage+ %s):" % adv)
        for c in manif_conj:
            b = c["banda_edad"]
            print("                    %-42s %s-%s" % (c["angulo"][:42], b["age_min"], b["age_max"]))
    else:
        print("  banda de edad   %s-%s  ·  Advantage+ %s  ·  %s"
              % (banda[0], banda[1], adv, origen_banda))
    print("  arranque        %s   (estado al crear: PAUSED)" % start_time)
    print("  pagina          %s" % page_id)
    print("  doctrina        %s" % par["fuente_doctrina"])
    print("  escrito en      %s" % os.path.relpath(salida, BASE))
    print()
    om = sum(1 for l in llamadas if l.get("omitir"))
    print("  LLAMADAS: %d  (%d ya existen en Meta y se OMITEN)" % (len(llamadas), om))
    for l in llamadas:
        marca = "  ~omitir~" if l.get("omitir") else ""
        etiqueta = l["args"].get("campaign_name") or l["args"].get("ad_set_name") \
            or l["args"].get("ad_name") or l["args"].get("name") \
            or os.path.basename(l.get("archivo_local", "")) or ""
        print("    %2d. %-26s %s%s" % (l["n"], l["tool"], etiqueta[:44], marca))
    print()
    if pq.avisos:
        print("  AVISOS:")
        for a in pq.avisos:
            print("    · %s" % a)
        print()
    if pq.bloqueantes:
        print("  BLOQUEANTES (%d) — NO PUBLICAR:" % len(pq.bloqueantes))
        for b in pq.bloqueantes:
            print("    X %s" % b["falta"])
            print("      lo produce: %s" % b["lo_produce"])
        print()
        print("  Invariante 4: si falta un input requerido se DETIENE. No se asume ni se inventa.")
        return 1
    print("  Sin bloqueantes. El paquete esta listo para que la skill publicar-meta lo ejecute.")
    print("  Al terminar: python Ads/_TOOLS/verificar_publicacion.py --producto %s --fase %d --brazo %s"
          % (pk, fase, brazo))
    return 0


if __name__ == "__main__":
    sys.exit(main())
