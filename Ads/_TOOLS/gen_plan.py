# -*- coding: utf-8 -*-
"""gen_plan.py — construye PRODUCTOS/[X]/_PLAN.json, el CONTRATO DE LANZAMIENTO.

QUE ES
El unico archivo que LANZADOR.html consume para armar un lanzamiento. Contiene SOLO
contenido creativo (angulos, prompts, copies) y los hechos del producto. NO contiene
nombres de campana, presupuestos, bandas de edad ni fechas: todo eso lo DERIVA
gen_lanzador.py desde la doctrina y los CSV. Un dato, un dueno.

    contenido creativo  -> _PLAN.json        (lo escribe etapa-6)
    todo lo derivable   -> gen_lanzador.py   (nombres, plata, fechas, gates)

POR QUE UN JSON Y NO EL TXT
`1_HACER_MANUAL.txt` es prosa: cada producto lo escribio distinto y ninguno se puede
leer con un programa. Mientras el plan viva en prosa, el operador tiene que interpretar
en vez de ejecutar. El JSON hace que el mismo plan se pueda renderizar, validar contra
_DIM_VOCABULARIO.csv y comparar entre productos.

USO
    python Ads/_TOOLS/gen_plan.py --validar            # valida todos los _PLAN.json

ESQUEMA (schema "plan/1") — lo que etapa-6 debe emitir:
{
  "schema": "plan/1",
  "producto_key": "...",            # debe existir en _DIM_PRODUCTOS.csv
  "fase": 1 | 2 | 3,
  "version": "v1",
  "origen": "texto libre: de donde salio este plan",
  "pagina": {"nombre": "...", "page_id": "..." | null},
  "oferta": {"oferta_key": "1U|2X1|4X2|ESCALERA|COMBO|SIN_PRECIO",
             "precio_q": 179, "texto": "2 frascos Q179 - envio gratis"},
  "concepto_control": {"concepto_key": "C2_BENEFICIOS", "variante": "ligera",
                       "canonico_id": "CN05_LISTA_BENEFICIOS"},   # FASE 1: fijo en todos
  "conjuntos": [{
      "n": 1,
      "angulo_key": "CARA_CANSADA",         # MAYUSCULAS, sin espacios, _ como separador
      "angulo_titulo": "Cara cansada que no se quita",
      "avatar_edad": "35-45" | null,        # null -> banda amplia (unica excepcion)
      "avatar_genero": "MUJER|HOMBRE|MIXTO",
      "nivel_conciencia": "1|2|3A|3B" | null,
      "formato": "IMAGEN|VIDEO",
      "lleva_precio": true|false,
      "archivo_creativo": "NOMBRE.jpg",
      "prompt_imagen": "...",               # null si el creativo es un video ya existente
      "copy": {"textos": ["...", "..."], "titulos": ["..."], "descripcion": "..."},
      "origen_angulo": "VOZ_CLIENTE|VIDEO_COMPETENCIA",   # T10 (solo exigido en version>=2)
      "voz_ids": ["V001", "V004"],           # si origen_angulo=VOZ_CLIENTE: voz_id de
                                              # _VOZ_CLIENTE.csv que sostienen el angulo
      "fuente_transcripcion": "NUSAVAB12_2_ARDOR.mp4"  # si origen_angulo=VIDEO_COMPETENCIA:
                                              # el video/transcripcion de ETAPA-0 de origen
  }],
  "_faltantes": ["lo que el plan no pudo llenar"]
}

ORIGEN DEL ANGULO (T10, g07-cimientos, 23-sep-2026) — solo en planes "version" >= 2:
Un angulo candidato puede venir de dos motores (ETAPA-1B/ETAPA-0, ver ese docstring): minado de
VOZ DEL CLIENTE o un video de competencia ya transcrito. Auditoria H5 (22-sep): sin evidencia
citada, un agente puede inventar un dolor y nada lo detecta. Cada conjunto de un plan de FASE 1
declara su `origen_angulo` y cita su evidencia:
  - VOZ_CLIENTE  -> `voz_ids` debe listar >= N voz_id con estado VERIFICADA en
                    PRODUCTOS/_VOZ_CLIENTE.csv para ese producto_key (N =
                    verificar_voz.min_voz_requerido(), default 3, overrideable por la fila
                    `min_voz_verificada_por_angulo` de _PARAMETROS_DECISION.csv).
  - VIDEO_COMPETENCIA -> `fuente_transcripcion` no vacio (el archivo/transcripcion de
                    ETAPA-0 que sostiene el angulo — FASE 1 corre todo en IMAGEN, pero el
                    video sigue siendo la FUENTE del angulo, CLAUDE.md).
Por que solo version>=2: los planes YA EMITIDOS (siempre "version": "v1" hasta esta fecha) no
tenian estos campos porque la regla no existia — exigirlos retroactivamente bloquearia
productos que ya pasaron FASE 1 sin que nadie pueda corregir un plan que ya cumplio su proposito.
"version" es un campo propio del esquema (no una fecha ni el estado en _ESTADO_FLUJO.csv): un
plan nuevo que etapa-6 emita con "version": "v2" (o superior) opta a la regla; el v1 existente
queda grandfathered para siempre, gate deterministico y sin acoplarse a otro CSV.

FASE 2 y 3 — _PLAN_FASE2.json / _PLAN_FASE3.json, el mismo esquema con "fase": 2|3 y dos
campos RAIZ obligatorios, porque ahi el angulo y el copy son constantes de la fase:
  "angulo_ganador": "ANGULO_KEY",         # el mismo en todos los conjuntos
  "copy": {"textos": [...], "titulos": [...], "descripcion": "..."}   # el copy unico de etapa-4
El copy va en la RAIZ, no dentro de cada conjunto: gen_publicacion.py lo lee de ahi y un copy
por conjunto se ignora. La cuenta y el page_id NO van: son de _DIM_PRODUCTOS.csv.
"""
import io, json, os, re, sys, csv

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(BASE)

TOOLS = os.path.dirname(os.path.abspath(__file__))
if TOOLS not in sys.path:
    sys.path.insert(0, TOOLS)
import verificar_voz  # T10: dueño de _VOZ_CLIENTE.csv y del umbral min_voz_requerido()

PRODUCTOS = "PRODUCTOS"
VOCABULARIO = "PRODUCTOS/_DIM_VOCABULARIO.csv"


def leer_csv(ruta):
    if not os.path.exists(ruta):
        return []
    with io.open(ruta, encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


# ─────────────────────────────────────────────────────────────────────────────
# VALIDAR
# ─────────────────────────────────────────────────────────────────────────────

OFERTAS = {"1U", "2X1", "4X2", "ESCALERA", "COMBO", "SIN_PRECIO"}
NIVELES = {"1", "2", "3A", "3B", None}

# Nombres de archivo por fase. En FASE 2/3 el array "conjuntos" no se valida: la
# estructura (1-1-5 + 1-1-5 + 1-2-5, 1-1-7) la arma gen_publicacion.py desde
# _PARAMETROS_PUBLICACION.csv y las piezas de _DIM_CREATIVOS.csv, no desde el plan.
NOMBRES_PLAN = {1: "_PLAN.json", 2: "_PLAN_FASE2.json", 3: "_PLAN_FASE3.json"}


def descubrir_planes(ruta=None):
    """Lista de rutas de plan a validar. Con `ruta` valida SOLO ese archivo (bug del
    22-sep-2026: `--validar` ignoraba cualquier ruta que se le pasara). Sin `ruta`
    escanea PRODUCTOS/*/ buscando los tres nombres posibles, no solo `_PLAN.json`
    (bug hermano: nunca abria `_PLAN_FASE2.json` ni `_PLAN_FASE3.json`)."""
    if ruta:
        return [ruta] if os.path.exists(ruta) else []
    planes = []
    for d in sorted(os.listdir(PRODUCTOS)):
        carpeta = os.path.join(PRODUCTOS, d)
        if not os.path.isdir(carpeta):
            continue
        for nombre in NOMBRES_PLAN.values():
            candidato = os.path.join(carpeta, nombre)
            if os.path.exists(candidato):
                planes.append(candidato)
    return planes


ORIGENES_ANGULO = {"VOZ_CLIENTE", "VIDEO_COMPETENCIA"}
VERSION_MIN_ORIGEN_EVIDENCIA = 2  # T10: version >= esto exige origen_angulo + evidencia citada


def _version_num(v):
    """"v1" -> 1, "v2" -> 2, cualquier otra cosa (ausente, no numerica) -> 1 (legacy, nunca
    se re-castiga retroactivamente — ver docstring del modulo, seccion ORIGEN DEL ANGULO)."""
    try:
        return int(str(v).strip().lower().lstrip("v"))
    except (TypeError, ValueError):
        return 1


def validar_origen_angulo(plan, voz_filas, min_voz):
    """T10: cada conjunto de un plan de FASE 1 en version>=2 cita de donde sale su angulo.
    `voz_filas` son las filas crudas de _VOZ_CLIENTE.csv (dict con producto_key/voz_id/estado);
    `min_voz` es el umbral (verificar_voz.min_voz_requerido())."""
    problemas = []
    producto = plan.get("producto_key")
    verificadas = {
        f.get("voz_id") for f in voz_filas
        if f.get("producto_key") == producto and f.get("estado") == "VERIFICADA"
    }
    todas = {f.get("voz_id") for f in voz_filas if f.get("producto_key") == producto}
    for c in plan.get("conjuntos", []):
        etq = "conjunto %s" % c.get("n")
        origen = (c.get("origen_angulo") or "").strip().upper()
        if origen not in ORIGENES_ANGULO:
            problemas.append("%s: origen_angulo %r fuera de %s (T10: cada angulo declara su "
                             "evidencia — voz del cliente o video de competencia)"
                             % (etq, c.get("origen_angulo"), sorted(ORIGENES_ANGULO)))
            continue
        if origen == "VOZ_CLIENTE":
            citados = [v for v in (c.get("voz_ids") or []) if v]
            desconocidos = [v for v in citados if v not in todas]
            verificados_citados = [v for v in citados if v in verificadas]
            if desconocidos:
                problemas.append("%s: voz_ids %s no existen en _VOZ_CLIENTE.csv para %r"
                                 % (etq, desconocidos, producto))
            if len(verificados_citados) < min_voz:
                problemas.append(
                    "%s: origen VOZ_CLIENTE cita %d voz_id VERIFICADA, se requieren %d "
                    "(_PARAMETROS_DECISION.csv min_voz_verificada_por_angulo, default "
                    "verificar_voz.MIN_VOZ_VERIFICADA_POR_ANGULO=%d)"
                    % (etq, len(verificados_citados), min_voz,
                       verificar_voz.MIN_VOZ_VERIFICADA_POR_ANGULO))
        elif origen == "VIDEO_COMPETENCIA":
            if not (c.get("fuente_transcripcion") or "").strip():
                problemas.append("%s: origen VIDEO_COMPETENCIA sin fuente_transcripcion (el "
                                 "video/transcripcion de ETAPA-0 que sostiene el angulo)" % etq)
    return problemas


def validar_plan_fase1(plan, validos, voz_filas=None, min_voz=None):
    problemas = []
    if plan.get("schema") != "plan/1":
        problemas.append("schema desconocido: %r" % plan.get("schema"))
    if plan.get("oferta", {}).get("oferta_key") not in OFERTAS:
        problemas.append("oferta_key fuera del vocabulario: %r"
                         % plan.get("oferta", {}).get("oferta_key"))
    ck = plan.get("concepto_control", {}).get("concepto_key")
    if "concepto_key" in validos and ck not in validos["concepto_key"]:
        problemas.append("concepto_key fuera del vocabulario: %r" % ck)
    vistos = set()
    for c in plan.get("conjuntos", []):
        etq = "conjunto %s" % c.get("n")
        if c.get("angulo_key") in vistos:
            problemas.append("%s: angulo_key duplicado %r" % (etq, c.get("angulo_key")))
        vistos.add(c.get("angulo_key"))
        if not re.match(r"^[A-Z0-9_]+$", c.get("angulo_key") or ""):
            problemas.append("%s: angulo_key con caracteres invalidos %r"
                             % (etq, c.get("angulo_key")))
        if c.get("nivel_conciencia") not in NIVELES:
            problemas.append("%s: nivel_conciencia %r no es 1/2/3A/3B"
                             % (etq, c.get("nivel_conciencia")))
        # FASE 1 corre TODO EN IMAGEN (decision operador 22-sep-2026): mide solo el ANGULO con
        # el concepto fijo. Los videos de competencia siguen siendo la FUENTE del angulo
        # (transcripciones de etapa-0), no el creativo de F1; el formato VIDEO se testea recien
        # en FASE 2, como un concepto mas.
        if (c.get("formato") or "").strip().upper() != "IMAGEN":
            problemas.append("%s: formato %r != IMAGEN — FASE 1 corre TODO EN IMAGEN (decision "
                             "operador 22-sep-2026: el concepto Y el formato quedan fijos, se "
                             "mide solo el angulo). Regenera el plan con etapa-6."
                             % (etq, c.get("formato")))
    con_precio = sum(1 for c in plan.get("conjuntos", []) if c.get("lleva_precio"))
    if plan.get("fase") == 1 and con_precio > 3:
        problemas.append("%d conjuntos con precio; la regla de Guatemala permite max 3 (ideal 2)"
                         % con_precio)
    if _version_num(plan.get("version")) >= VERSION_MIN_ORIGEN_EVIDENCIA:
        problemas.extend(validar_origen_angulo(
            plan, voz_filas if voz_filas is not None else [],
            min_voz if min_voz is not None else verificar_voz.MIN_VOZ_VERIFICADA_POR_ANGULO))
    return problemas


def validar_plan_fase2o3(plan):
    """Solo los campos RAIZ sin los que gen_publicacion.py bloquea en fase 2/3: angulo_ganador
    y copy. cuenta y page_id no: el publicador los toma de _DIM_PRODUCTOS.csv y bloquea ahi,
    con su dueno. NO valida 'conjuntos' (ver nota de NOMBRES_PLAN)."""
    problemas = []
    if plan.get("schema") != "plan/1":
        problemas.append("schema %r: FASE 2/3 usan el contrato plan/1 (la Guia Madre fija "
                         "1-1-5 ABO; el esquema 5 conjuntos x 1 concepto quedo retirado)"
                         % plan.get("schema"))
    if not (plan.get("angulo_ganador") or "").strip():
        problemas.append("sin angulo_ganador en la raiz del plan: gen_publicacion.py bloquea "
                         "TODOS los anuncios de la fase sin el (invariante 4)")
    copy_val = plan.get("copy")
    copy_ok = bool(copy_val.strip()) if isinstance(copy_val, str) else bool(copy_val)
    if not copy_ok:
        problemas.append("sin 'copy' en la raiz del plan: en FASE 2/3 el copy es FIJO y vive "
                         "en el plan (ETAPA-6); _DIM_CREATIVOS.csv no tiene columna copy, asi "
                         "que sin este campo gen_publicacion.py bloquea cada anuncio con "
                         "{{FALTA_COPY}}")
    return problemas


def validar(ruta=None):
    vocab = leer_csv(VOCABULARIO)
    validos = {}
    for v in vocab:
        eje = (v.get("eje") or "").strip()
        val = (v.get("valor") or "").strip()
        if eje and val:
            validos.setdefault(eje, set()).add(val)

    planes = descubrir_planes(ruta)
    if not planes:
        print("no existe %s" % ruta if ruta else "no hay ningun _PLAN*.json todavia.")
        return 0 if not ruta else 1

    voz_filas = verificar_voz.leer_csv()
    min_voz = verificar_voz.min_voz_requerido()

    errores = 0
    for ruta_plan in planes:
        with io.open(ruta_plan, encoding="utf-8") as fh:
            plan = json.load(fh)
        print("\n%s" % ruta_plan.replace("\\", "/"))
        fase = plan.get("fase")
        if fase == 1:
            problemas = validar_plan_fase1(plan, validos, voz_filas, min_voz)
        elif fase in (2, 3):
            problemas = validar_plan_fase2o3(plan)
        else:
            problemas = ["fase desconocida en el plan: %r" % fase]
        if problemas:
            errores += len(problemas)
            for p in problemas:
                print("  ERROR  %s" % p)
        else:
            print("  ok · %d conjuntos" % len(plan.get("conjuntos", [])))
        for f in plan.get("_faltantes", []):
            print("  falta  %s" % f)
    return 1 if errores else 0


if __name__ == "__main__":
    if "--validar" in sys.argv:
        i = sys.argv.index("--validar")
        ruta_pedida = sys.argv[i + 1] if i + 1 < len(sys.argv) and not sys.argv[i + 1].startswith("--") else None
        sys.exit(validar(ruta_pedida))
    else:
        print(__doc__)
