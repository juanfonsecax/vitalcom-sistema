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

Y ninguna etapa tiene siquiera acceso al conector: ETAPA-6 declara `tools: Read`, ETAPA-7
`Read, Glob, Grep`. La descripcion de ETAPA-7 dice que "Meta MCP aporta senales de
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
    numero de replica R[N] (fase 1 y 4)         conjunto_meta de _DIM_CONJUNTOS.csv
                                                (siguiente_replica: nunca la posicion del loop)
    piezas, concepto_key, canonico_id           PRODUCTOS/_DIM_CREATIVOS.csv
    la FIRMA de 5 ejes                          Ads/_TOOLS/firma.py (se importa, no se copia)
    angulo ganador, page_id, copy               PRODUCTOS/[X]/_PLAN*.json (dueno: ETAPA-6)
    nombres de campana/conjunto/anuncio         .claude/agents/ETAPA-6.md CONVENCION DE NOMBRES

F4.exploracion (P12, T12) — `--fase 4 --brazo EXPLORACION`: el mini-F1 de ángulos nuevos que
corre en paralelo al escalado. Mismo `--fase 4` (mismo gate de ENTRADA a F4), pero lee
`_PLAN_EXPLORACION.json` (no `_PLAN_FASE4.json`), arma un conjunto POR ÁNGULO como FASE 1 (no
un ángulo fijo ×7), su fila de `_PARAMETROS_PUBLICACION.csv` es fase=4 brazo=EXPLORACION, y
además del gate de entrada a F4 exige el gate propio de F4.exploracion (F4 rentable según
decidir.py, `flujo.gate_nodo`). La campaña nace `EXPLORA`, no `ESCALA-{angulo}`.

USO
    python Ads/_TOOLS/gen_publicacion.py --producto TINNIDROP --fase 2 --brazo A --cuenta GTR7
    python Ads/_TOOLS/gen_publicacion.py --producto TINNIDROP --fase 2 --brazo A --cuenta GTR7 \
           --snapshot Ads/_INGESTA/META/snapshot_GTR7.json
    python Ads/_TOOLS/gen_publicacion.py --producto TINNIDROP --fase 2 --brazo A --cuenta GTR7 --json
    python Ads/_TOOLS/gen_publicacion.py --producto TINNIDROP --fase 1 --cuenta GTR7 --media biblioteca \
           --imagenes-antes antes.json --imagenes-despues despues.json --json

LA MEDIA — dos modos (--media)
------------------------------
    subida_local  (por defecto) una llamada ads_creative_upload_media con LOCAL_FILE por pieza. Abre
                  un widget donde el operador elige el archivo: solo sirve en una sesion con pantalla
                  y solo en la cuenta que _DIM_CUENTAS.csv marca sube_media_local=SI.
    biblioteca    el operador sube las piezas A MANO a la biblioteca de medios de la cuenta y el
                  paquete lee cada image_hash por NOMBRE (ads_get_ad_images, solo lectura). Es el
                  camino de MCP_PLAYBOOK "Paso C/D" y el unico que corre sin pantalla (la app:
                  spike F, SPIKE_UPLOAD_MEDIA_2026-09-18.md). Decision del operador, 18-sep-2026.
                  Recibe dos volcados de la biblioteca, {"imagenes":[{"hash","name"}]}:
                    --imagenes-antes    tomado ANTES de que el operador suba. De aca sale el nombre
                                        de cada pieza: el primer [base]_V2, _V3... que NO exista.
                                        Un nombre viejo nunca se reusa (08-sep: 10 anuncios con la
                                        pieza equivocada por dos imagenes con el mismo nombre).
                    --imagenes-despues  tomado cuando el operador dice "ya las subi". Cada nombre
                                        tiene que aparecer con UN solo hash.
                  Lo que falta es un bloqueante de ambito 'media': lo resuelve el operador subiendo,
                  no rehaciendo la fase ni tocando la cuenta.
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
import flujo             # gate_entrada: el unico juez de "se cumple el gate de entrada a la fase N"
import mercado           # mercado_de_fila: el mercado del producto (GT/CO), dueno del pais del targeting
import gen_lanzador      # monto_cuenta: el monto en USD expresado en la moneda de la cuenta
import registrar_evento  # registrar_excepcion: el unico escritor de una fila EXCEPCION en _EVENTOS.csv
from gen_lanzador import corto as token_producto  # dueño del token de producto en los nombres

SCHEMA = "publicacion/1"

# Unidades menores por unidad de moneda en el daily_budget de Meta. COP va en pesos
# enteros: el mínimo diario medido de las cuentas COP es 3154 (~1 USD) en
# _DIM_CUENTAS.csv.min_daily_budget_cents.
UNIDAD_MENOR = {"USD": 100, "COP": 1}


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


def fecha_lanzamiento_invalida(fecha, hoy):
    """True salvo que `fecha` sea EXACTAMENTE el dia siguiente a `hoy`.

    Invariante 7 (CLAUDE.md): el lanzamiento es SIEMPRE el dia siguiente a las 4 AM, nunca el
    mismo dia (T8-3, 23-sep-2026: tampoco un dia mas adelante — antes solo se rechazaba
    `fecha <= hoy`, asi que 2, 3 o N dias en el futuro pasaban el gate sin avisar)."""
    return fecha != hoy + datetime.timedelta(days=1)


MODOS_MEDIA = ("subida_local", "biblioteca")
EXT_IMAGEN = (".png", ".jpg", ".jpeg", ".gif", ".webp")


def nombre_normalizado(nombre):
    """Como se compara un nombre de la biblioteca: sin espacios al borde, sin extension de imagen y
    sin distinguir mayusculas. Meta puede guardar el nombre con o sin la extension del archivo."""
    n = (nombre or "").strip()
    if n.lower().endswith(EXT_IMAGEN):
        n = os.path.splitext(n)[0]
    return n.lower()


def leer_listado_de_imagenes(ruta):
    """El volcado de ads_get_ad_images: [{"hash","name"}], o None si todavia no se tomo."""
    if not ruta or not os.path.exists(ruta):
        return None
    with io.open(ruta, encoding="utf-8") as f:
        datos = json.load(f)
    imagenes = datos if isinstance(datos, list) else datos.get("imagenes", [])
    return [{"hash": str(i.get("hash") or "").strip(), "name": str(i.get("name") or "")}
            for i in imagenes if i.get("hash")]


def nombre_nuevo_en_biblioteca(base, ocupados):
    """El primer [base]_V2, _V3... que no esta en 'ocupados' (nombres normalizados). Nunca el nombre
    viejo: Meta guarda las dos imagenes y quedan indistinguibles por nombre (08-sep)."""
    k = 2
    while nombre_normalizado("%s_V%d" % (base, k)) in ocupados:
        k += 1
    return "%s_V%d" % (base, k)


def hash_por_nombre(nombre, listado):
    """(estado, hash, hashes) de 'nombre' en el volcado de despues de subir.
    OK = un solo hash · POR_SUBIR = no esta · REPETIDA = mas de una imagen distinta con ese nombre."""
    hashes = sorted({i["hash"] for i in listado if nombre_normalizado(i["name"]) == nombre_normalizado(nombre)})
    if not hashes:
        return "POR_SUBIR", None, []
    if len(hashes) > 1:
        return "REPETIDA", None, hashes
    return "OK", hashes[0], hashes


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
            pq.bloquear_paquete("la firma sale con %s = '%s' en %d anuncio(s) (%s). Publicado asi, ese eje "
                        "se pierde para siempre: la firma viaja en el nombre del anuncio y el "
                        "sistema la lee de ahi." % (eje, fmod.VACIO, cuantos, ", ".join(faltan[eje][:4])),
                        "%s -> llega al anuncio por el plan de etapa-6" % (dueno or "etapa-6"))


class Paquete(object):
    def __init__(self):
        self.bloqueantes = []
        self.avisos = []
        self.preflight = []

    # Todo bloqueante declara su AMBITO, y no hay un bloquear() generico a proposito: un bloqueo
    # nuevo que no diga de quien es rompe con AttributeError en vez de caer, en silencio, del
    # lado equivocado.
    #
    #   paquete      lo produce una ETAPA de la skill de la fase (plan, pagina, banda, piezas,
    #                archivos, copy, firma). Mientras haya uno, el paquete NO esta cumplido y lo
    #                que se vuelve a ejecutar es la skill de la fase, no publicar-meta.
    #   publicacion  depende de la CUENTA, del CALENDARIO o del operador al publicar (MCP, pago,
    #                moneda, minimo de la cuenta, brazo, fecha). No hace incompleto al paquete:
    #                un paquete perfecto con la cuenta mal configurada sigue siendo un paquete
    #                perfecto, y rehacer la FASE 1 no arregla una cuenta.
    #   media        (solo --media biblioteca) las piezas que el operador todavia no subio a la
    #                biblioteca de la cuenta, o que subio dos veces. Se resuelve subiendo, y el que
    #                espera es el ejecutor: no es un paquete incompleto ni una cuenta mal armada.
    AMBITOS = ("paquete", "publicacion", "media")
    # Los bloqueos que el OPERADOR resuelve cargando un dato llevan ademas una `clave` fija, para que
    # quien los muestre (la app) ofrezca el campo correcto sin interpretar la frase de `falta`:
    #   cuenta   la cuenta del producto no existe en _DIM_CUENTAS.csv   (cargar_cuenta.py)
    #   page_id  no hay page_id                                           (cargar_page_id.py)
    #   piezas   piezas declaradas sin archivo en disco, con `archivos`   (cargar_pieza.py)
    CLAVES = ("cuenta", "page_id", "piezas")

    def _bloquear(self, que, dueno, ambito, clave=None, **extra):
        bloqueo = {"falta": que, "lo_produce": dueno, "ambito": ambito}
        if clave is not None:
            assert clave in self.CLAVES, clave
            bloqueo.update(clave=clave, **extra)
        self.bloqueantes.append(bloqueo)

    def bloquear_paquete(self, que, dueno, clave=None, **extra):
        self._bloquear(que, dueno, "paquete", clave, **extra)

    def bloquear_publicacion(self, que, dueno, clave=None, **extra):
        self._bloquear(que, dueno, "publicacion", clave, **extra)

    def bloquear_media(self, que, dueno):
        self._bloquear(que, dueno, "media")

    def del_ambito(self, ambito):
        return [b for b in self.bloqueantes if b["ambito"] == ambito]

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
    """CONVENCION DE NOMBRES — ETAPA-6.md. Separador de campos '_', dentro del campo solo '-'.

    fase 4 + brazo EXPLORACION (P12, T12): la campaña de la exploración paralela de ángulos
    nuevos NO lleva el token ESCALA (no es escalado, y ESCALA-{angulo} no aplica: la exploración
    trae VARIOS ángulos, no uno fijo) — token propio EXPLORA, mismo patrón que TEST en FASE 1.
    FASE 3 (optimización del flujo del bot) nunca llama esta función: no publica estructura
    nueva en Meta (el ganador de F2 sigue corriendo al mismo presupuesto)."""
    d = fecha.strftime("%Y%m%d")
    if fase == 1:
        return "%s_%s_TEST_%s" % (cuenta, producto, d)
    if fase == 2:
        return "%s_%s_CONCEPTOS-%s_%s" % (cuenta, producto, brazo, d)
    if fase == 4 and brazo == "EXPLORACION":
        return "%s_%s_EXPLORA_%s" % (cuenta, producto, d)
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
    excepcion = (arg("--excepcion") or "").strip()
    # --solo-paquete: la pregunta de F1.paquete en FLUJO.json. ¿Lo que produjeron las ETAPAS
    # alcanza para lanzar? Evalua todo igual, pero sale con exit 1 solo por bloqueantes de ambito
    # 'paquete', no corta si la cuenta todavia no existe, y nunca escribe el paquete canonico.
    solo_paquete = flag("--solo-paquete")
    modo_media = arg("--media") or "subida_local"

    if not pk_in or not fase:
        print(__doc__)
        return 2
    if modo_media not in MODOS_MEDIA:
        print("--media es %s, no '%s'." % (" o ".join(MODOS_MEDIA), modo_media))
        return 2
    biblioteca = modo_media == "biblioteca"
    imagenes_antes = leer_listado_de_imagenes(arg("--imagenes-antes")) if biblioteca else None
    imagenes_despues = leer_listado_de_imagenes(arg("--imagenes-despues")) if biblioteca else None
    ocupados = {nombre_normalizado(i["name"]) for i in (imagenes_antes or [])}
    media_por_archivo = {}   # archivo -> su fila de paquete["media"]["piezas"] (una subida por archivo)
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
    tok = token_producto(prod)
    try:
        pais = mercado.mercado_de_fila(prod)
    except mercado.MercadoError as e:
        pq.bloquear_paquete(str(e), "operador · _DIM_PRODUCTOS.csv columna mercado")
        pais = None

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
    if not fila_cta and not solo_paquete:
        print("BLOQUEANTE: la cuenta '%s' no existe en _DIM_CUENTAS.csv." % alias_pedido)
        return 1
    if not fila_cta:
        # Sin cuenta todavia (los productos de FASE 1 nacen con cuenta_alias=PENDIENTE) el paquete
        # igual se puede juzgar: la cuenta solo aporta moneda y minimo, que son de la publicacion.
        # Cortar aca dejaria trabado en F1.paquete a un producto cuyo paquete esta perfecto.
        pq.bloquear_publicacion("la cuenta '%s' no existe en _DIM_CUENTAS.csv" % alias_pedido,
                                "el operador · _DIM_PRODUCTOS.csv columna cuenta_alias", clave="cuenta")
        # Una fila con TODAS las columnas reales de _DIM_CUENTAS.csv (una columna nueva no rompe
        # esto) y valores neutros: ninguno debe generar un bloqueo, porque ya se declaro arriba el
        # unico que corresponde — que la cuenta no existe.
        columnas = cuentas[0].keys() if cuentas else ()
        fila_cta = dict.fromkeys(columnas, "")
        fila_cta.update({"cuenta_alias": alias_pedido, "cuenta_id": "", "moneda": "USD",
                         "min_daily_budget_cents": "0", "mcp_habilitado": "SI",
                         "tiene_metodo_pago": "SI", "sube_media_local": "SI"})
    if fila_cta["mcp_habilitado"] != "SI":
        pq.bloquear_publicacion("la cuenta %s NO tiene el MCP habilitado (%s). Publicar por MCP es imposible "
                    "en esta cuenta: o se pauta a mano, o se mueve el producto a una cuenta habilitada."
                    % (alias_pedido, fila_cta.get("notas") or "rollout"), "Meta (rollout)")
    if fila_cta["tiene_metodo_pago"] != "SI":
        pq.bloquear_publicacion("la cuenta %s no tiene metodo de pago: puede crear, no puede gastar." % alias_pedido,
                    "el operador, en Business Manager")

    moneda = fila_cta["moneda"]
    moneda_norm = (moneda or "").strip().upper()
    minimo = int(fila_cta["min_daily_budget_cents"])
    presu_usd = float(par["daily_budget_usd"])
    moneda_prod = (prod.get("moneda") or "").strip().upper()
    if moneda_prod and moneda_prod != moneda_norm:
        pq.bloquear_publicacion("la cuenta %s factura en %s y _DIM_PRODUCTOS.moneda de %s dice %s"
                    % (alias_pedido, moneda_norm, pk, moneda_prod),
                    "operador · _DIM_PRODUCTOS.csv columna moneda o la cuenta asignada")
    if moneda_norm not in UNIDAD_MENOR:
        pq.bloquear_publicacion("la moneda %s de la cuenta %s no tiene unidad menor declarada"
                    % (moneda_norm or "?", alias_pedido),
                    "Ads/_TOOLS/gen_publicacion.py UNIDAD_MENOR")
        presu_cents = None
    else:
        crudo_tasa = (prod.get("tasa") or "").strip()
        try:
            tasa_del_producto = float(crudo_tasa) if crudo_tasa else None
        except ValueError:
            tasa_del_producto = None
        valor, _ = gen_lanzador.monto_cuenta(presu_usd, moneda, tasa_del_producto)
        if valor is None:
            pq.bloquear_publicacion("tasa sin declarar: no se puede convertir el presupuesto a %s"
                        % moneda_norm,
                        "operador · _DIM_PRODUCTOS.csv columna tasa")
            presu_cents = None
        else:
            presu_cents = int(round(valor * UNIDAD_MENOR[moneda_norm]))
            if presu_cents < minimo:
                pq.bloquear_publicacion("presupuesto %d centavos < minimo de la cuenta (%d)" % (presu_cents, minimo),
                            "_DIM_CUENTAS.csv")

    # ---------- 4. plan ----------------------------------------------------
    carpeta = prod.get("slug_carpeta") or pk
    exploracion = fase == 4 and brazo == "EXPLORACION"
    if not ruta_pl:
        if exploracion:
            cand = [P(carpeta, "_PLAN_EXPLORACION.json")]
        else:
            cand = [P(carpeta, "_PLAN_FASE%d.json" % fase), P(carpeta, "_PLAN.json")]
        ruta_pl = next((c for c in cand if os.path.exists(c)), None)
    plan = {}
    if ruta_pl and os.path.exists(ruta_pl):
        with io.open(ruta_pl, encoding="utf-8") as f:
            plan = json.load(f)
    elif exploracion:
        pq.bloquear_paquete("no existe _PLAN_EXPLORACION.json en PRODUCTOS/%s/" % carpeta, "etapa-6")
    else:
        pq.bloquear_paquete("no existe _PLAN_FASE%d.json ni _PLAN.json en PRODUCTOS/%s/" % (fase, carpeta),
                    "etapa-6")

    # FASE 1 y la EXPLORACION de F4 (P12) miden el ANGULO: cada conjunto lleva uno distinto y no
    # hay ganador todavia. FASE 2 y 3-ESCALA miden otra cosa sobre un angulo YA GANADO: ahi el
    # angulo es uno y es fijo.
    angulo = (plan.get("angulo_ganador") or plan.get("angulo_key") or "").strip()
    if fase in (2, 3) and not exploracion and not angulo:
        pq.bloquear_paquete("el plan no declara angulo_ganador. En FASE 2 y 3 el angulo es FIJO y va en el "
                    "nombre del CONJUNTO; sin el, la agregacion por angulo_key se parte.", "etapa-6")

    # page_id: el del plan manda sobre el del producto, porque la pagina depende de la CUENTA
    page_id = str(plan.get("page_id") or prod.get("page_id") or "").strip()
    if not page_id:
        pq.bloquear_paquete("no hay page_id", "etapa-2", clave="page_id")
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
            pq.bloquear_paquete("%s: avatar_edad='%s' no esta en la tabla de derivacion. No se "
                        "inventa una banda: o se agrega la fila a la tabla, o se corrige el avatar."
                        % (contexto, orig), "Ads/_TOOLS/bandas_edad.py")
            return (None, None), orig
        return b, orig

    unidades = []
    sin_archivo = []
    orden_nombre_por_creativo = {}   # fase 1 no lo usa: el orden del nombre sale del contador local

    if fase == 1 or exploracion:
        plan_conj = plan.get("conjuntos") or []
        if len(plan_conj) < n_conj:
            if exploracion:
                pq.bloquear_paquete("F4.exploracion se monta con %d angulos nuevos (_PARAMETROS_DECISION.csv "
                            "exploracion_n_angulos) y el plan trae %d." % (n_conj, len(plan_conj)),
                            "etapa-2 (fichas de angulo)")
            else:
                pq.bloquear_paquete("la FASE 1 se monta con %d angulos y el plan trae %d. Se testean 6 angulos "
                            "distintos con el concepto FIJO; con menos, la comparacion entre angulos "
                            "queda incompleta." % (n_conj, len(plan_conj)), "etapa-2 (fichas de angulo)")
        ctrl = plan.get("concepto_control") or {}
        for i, c in enumerate(plan_conj[:n_conj], 1):
            ang = (c.get("angulo_key") or "").strip()
            if not ang:
                pq.bloquear_paquete("el conjunto %d del plan no declara angulo_key" % i, "etapa-2")
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
        error_brazo = chequear_brazo_ambiguo(piezas_del_angulo, arg("--brazo-creativos"), brazo) if fase == 2 else None
        if error_brazo:
            pq.bloquear_publicacion(error_brazo, "el operador (pasar --brazo-creativos %s)" % brazo)

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
            pq.bloquear_paquete("hacen falta %d piezas para un %s y hay %d con archivo en disco. "
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
        pq.bloquear_paquete("%d pieza(s) declaradas no tienen su archivo en disco: %s. Sin el archivo no "
                    "hay media que subir y el anuncio no se puede crear."
                    % (len(sin_archivo), ", ".join(str(s) for s in sin_archivo[:6])),
                    "etapa-render / el operador", clave="piezas", archivos=[str(s) for s in sin_archivo])

    # Ningun anuncio sale con un eje de su firma perdido (se pierde para siempre en Meta).
    verificar_firma(unidades, fmod, pq)

    banda = unidades[0]["banda"] if unidades else (None, None)
    origen_banda = unidades[0]["origen_banda"] if unidades else "sin unidades"
    bandas_distintas = len({u["banda"] for u in unidades}) > 1

    # ---------- 7. fecha de lanzamiento -----------------------------------
    hoy = datetime.date.today()
    manana = hoy + datetime.timedelta(days=1)
    fecha = datetime.datetime.strptime(lanz, "%Y-%m-%d").date() if lanz else manana
    if fecha_lanzamiento_invalida(fecha, hoy):
        pq.bloquear_publicacion("lanzamiento %s no es el dia SIGUIENTE a hoy (%s -> tenia que ser %s). "
                    "Invariante 7: SIEMPRE el dia siguiente a las 4 AM, nunca el mismo dia ni uno "
                    "mas adelante." % (fecha, hoy, manana), "CLAUDE.md invariante 7")
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
    camp = nombre_campana(fase, cta, tok, brazo, angulo, fecha)
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

    def llamada_de_subida_local(n_llamada, cre, orden):
        return {
            "n": n_llamada, "tool": "ads_creative_upload_media",
            "args": {"ad_account_id": acct, "upload_source": "LOCAL_FILE"},
            "guardar_como": "image_hash_%d" % orden,
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
        }

    def media_de_la_pieza(cre):
        """--media biblioteca: la fila de la pieza en paquete["media"], una por ARCHIVO (dos anuncios
        con la misma imagen comparten subida y hash). El nombre sale del volcado de ANTES y queda
        fijo aunque despues el operador suba: por eso no se recalcula contra el de DESPUES."""
        archivo = cre.get("archivo") or ""
        if archivo in media_por_archivo:
            return media_por_archivo[archivo]
        base = os.path.splitext(archivo or "SIN_ARCHIVO")[0]
        fila = {"archivo": archivo, "ruta": os.path.relpath(cre["_ruta"], BASE) if cre.get("_ruta") else None,
                "nombre_en_biblioteca": None, "image_hash": None, "estado": "SIN_LISTADO", "hashes": []}
        if imagenes_antes is not None:
            fila["nombre_en_biblioteca"] = nombre_nuevo_en_biblioteca(base, ocupados)
            ocupados.add(nombre_normalizado(fila["nombre_en_biblioteca"]))
            fila["estado"] = "POR_SUBIR"
            if imagenes_despues is not None:
                fila["estado"], fila["image_hash"], fila["hashes"] = hash_por_nombre(
                    fila["nombre_en_biblioteca"], imagenes_despues)
        media_por_archivo[archivo] = fila
        return fila

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
        cj = nombre_conjunto(fase, cta, tok, ang_u, brazo, numero_conj)
        n += 1
        targeting = {
            # el código de mercado (GT, CO) es el código de país ISO que usa Meta.
            "geo_locations": {"countries": [pais or "{{FALTA_PAIS}}"]},
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
                pq.bloquear_paquete("el anuncio '%s' no tiene copy. El copy vive en el CREATIVO de Meta y no "
                            "se puede cambiar despues: ads_update_entity no reemplaza el creativo de "
                            "un anuncio existente, hay que crear uno nuevo." % an.split(" ~ ")[0],
                            "etapa-4 (copies)")
            if sobrantes:
                pq.avisar("'%s' trae %d opcion(es) extra de texto/titulo. El '1 de 5' NO existe en "
                          "la Marketing API: por MCP va una sola y el resto lo agrega el operador a "
                          "mano en el Administrador." % (an.split(" ~ ")[0], sobrantes))

            if biblioteca:
                image_hash = media_de_la_pieza(cre)["image_hash"] or "{{FALTA_HASH}}"
            else:
                image_hash = "{{image_hash_%d}}" % orden_global
                n += 1
                llamadas.append(llamada_de_subida_local(n, cre, orden_global))

            n += 1
            llamadas.append({
                "n": n, "tool": "ads_create_creative",
                "args": {
                    "ad_account_id": acct, "page_id": page_id,
                    "name": an.split(" ~ ")[0],
                    "image_hash": image_hash,
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

    # ---------- 9b. media de biblioteca: lo que el operador sube a mano -----
    media = None
    if biblioteca:
        piezas_media = list(media_por_archivo.values())
        media = {"modo": "biblioteca", "cuenta_alias": cta, "cuenta_id": acct,
                 "listado_antes": imagenes_antes is not None, "listado_despues": imagenes_despues is not None,
                 "piezas": piezas_media}
        donde = "la biblioteca de medios de la cuenta %s (%s)" % (cta, acct)
        if imagenes_antes is None:
            pq.bloquear_media("falta leer %s antes de elegir los nombres: sin ese volcado no se puede "
                              "garantizar que ningun nombre viejo se reuse." % donde,
                              "publicar-meta (lectura con ads_get_ad_images)")
        else:
            por_subir = [p["nombre_en_biblioteca"] for p in piezas_media if p["estado"] == "POR_SUBIR"]
            repetidas = [p for p in piezas_media if p["estado"] == "REPETIDA"]
            if por_subir:
                pq.bloquear_media("falta subir %d imagen(es) a %s, con estos nombres exactos: %s"
                                  % (len(por_subir), donde, ", ".join(por_subir)),
                                  "el operador (sube a mano y avisa 'ya las subi')")
            for p in repetidas:
                pq.bloquear_media("en %s hay %d imagenes distintas llamadas %s (%s). Con dos contenidos bajo "
                                  "el mismo nombre no se sabe cual es la pieza: borra la que sobra."
                                  % (donde, len(p["hashes"]), p["nombre_en_biblioteca"], ", ".join(p["hashes"])),
                                  "el operador (en la biblioteca de medios)")

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
        "producto_key": pk, "token_producto": tok, "pais": pais, "fase": fase, "brazo": brazo,
        "angulo": angulo if (fase in (2, 3) and not exploracion) else
                  "VARIOS (uno por conjunto — F1/F4.exploracion miden el angulo)",
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
        **({"media": media} if media is not None else {}),
        "manifiesto": {
            "campana": camp,
            "conjuntos": manif_conj,
            "total_conjuntos": n_conj,
            "total_anuncios": sum(len(c["anuncios"]) for c in manif_conj),
        },
    }

    if solo_paquete:
        # Es una verificacion, no una generacion: con una cuenta posiblemente ficticia, escribir el
        # _PUBLICACION_F*.json canonico dejaria en disco un paquete que publicar-meta podria leer.
        if salida:
            with io.open(salida, "w", encoding="utf-8") as f:
                json.dump(paquete, f, ensure_ascii=False, indent=2)
        del_paquete = pq.del_ambito("paquete")
        if flag("--json"):
            print(json.dumps(paquete, ensure_ascii=False, indent=2))
            return 1 if del_paquete else 0
        print("PAQUETE %s · FASE %d — %s" % (pk, fase, "NO LANZABLE" if del_paquete else "LANZABLE"))
        for b in del_paquete:
            print("  BLOQUEANTE %s" % b["falta"])
            print("             lo produce: %s" % b["lo_produce"])
        otros = pq.del_ambito("publicacion")
        if otros:
            print("  (%d bloqueante(s) de la publicacion —cuenta, calendario, operador— no cuentan "
                  "para el paquete: los evalua F1.publicar)" % len(otros))
        return 1 if del_paquete else 0

    # ---------- P5: el gate de entrada a la fase es un CANDADO, no un aviso -------------------
    # (solo aca: --solo-paquete ya volvio arriba y NUNCA emite el paquete canonico).
    ok_gate, obs_gate = flujo.gate_entrada(pk, fase, flujo.Entorno(base=BASE))
    if not ok_gate and not excepcion:
        print("BLOQUEANTE: el gate de entrada a F%d no esta cumplido: %s" % (fase, obs_gate))
        print("            Invariante: la fase se abre por el gate declarado en DOCTRINA/FLUJO.json, "
              "nunca por decision del operador o del modelo.")
        print("            Si es deliberado, repetir con --excepcion \"motivo\": queda una fila "
              "EXCEPCION en _EVENTOS.csv y la publicacion sigue.")
        return 1
    if not ok_gate:
        ok_ev, errores_ev = registrar_evento.registrar_excepcion(
            pk, "F%d.entrada" % fase, "gen_publicacion --fase %d" % fase, excepcion,
            "Ads/_TOOLS/gen_publicacion.py")
        if not ok_ev:
            print("BLOQUEANTE: no se pudo registrar la EXCEPCION:\n  · " + "\n  · ".join(errores_ev))
            return 1
        print("EXCEPCION registrada: F%d.entrada -> gen_publicacion --fase %d (%s)" % (fase, fase, excepcion))

    # ---------- P12: el gate propio de F4.exploracion (F4 rentable) es OTRO candado ------------
    # distinto del gate de entrada a F4 de arriba (concepto 2/2 + CAMBIO_BOT): ese ya esta
    # cumplido para cualquier producto que este viendo nodos de F4. F4.exploracion ademas exige
    # que el escalado sea rentable (decidir.py), gate leido con flujo.gate_nodo (T12), nunca
    # recalculado aca.
    if exploracion:
        ok_expl, obs_expl = flujo.gate_nodo(pk, "F4.exploracion", flujo.Entorno(base=BASE))
        if not ok_expl and not excepcion:
            print("BLOQUEANTE: el gate de F4.exploracion no esta cumplido: %s" % obs_expl)
            print("            P12: la exploracion arranca solo cuando el escalado (F4) es rentable "
                  "segun decidir.py.")
            print("            Si es deliberado, repetir con --excepcion \"motivo\": queda una fila "
                  "EXCEPCION en _EVENTOS.csv y la publicacion sigue.")
            return 1
        if not ok_expl:
            ok_ev, errores_ev = registrar_evento.registrar_excepcion(
                pk, "F4.exploracion", "gen_publicacion --fase 4 --brazo EXPLORACION", excepcion,
                "Ads/_TOOLS/gen_publicacion.py")
            if not ok_ev:
                print("BLOQUEANTE: no se pudo registrar la EXCEPCION:\n  · " + "\n  · ".join(errores_ev))
                return 1
            print("EXCEPCION registrada: F4.exploracion -> gen_publicacion --fase 4 --brazo EXPLORACION (%s)"
                  % excepcion)

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
