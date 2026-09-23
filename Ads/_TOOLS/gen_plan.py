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
      "origen_angulo": "VOZ_CLIENTE|VIDEO_COMPETENCIA",
      "voz_ids": ["V001", "V004"],           # si origen_angulo=VOZ_CLIENTE: voz_id de
                                              # _VOZ_CLIENTE.csv que sostienen el angulo
      "fuente_transcripcion": "NUSAVAB12_2_ARDOR.mp4"  # si origen_angulo=VIDEO_COMPETENCIA:
                                              # el video/transcripcion de ETAPA-0 de origen
  }],
  "_faltantes": ["lo que el plan no pudo llenar"]
}

ORIGEN DEL ANGULO — cada conjunto de un plan de FASE 1 declara `origen_angulo` y cita su
evidencia, salvo que el producto ya haya lanzado FASE 1 de verdad:
  - VOZ_CLIENTE  -> `voz_ids` debe listar >= N voz_id con estado VERIFICADA en
                    PRODUCTOS/_VOZ_CLIENTE.csv para ese producto_key (N =
                    verificar_voz.min_voz_requerido(), default 3, overrideable por la fila
                    `min_voz_verificada_por_angulo` de _PARAMETROS_DECISION.csv).
  - VIDEO_COMPETENCIA -> `fuente_transcripcion` no vacio (el archivo/transcripcion de
                    ETAPA-0 que sostiene el angulo — FASE 1 corre todo en IMAGEN, pero el
                    video sigue siendo la FUENTE del angulo, CLAUDE.md).
  - EXCEPCION: un producto que ya LANZO FASE 1 (`_DIM_CONJUNTOS.csv` tiene un conjunto con
                    `fase=FASE1` y `verificado_en_csv=SI` — ETAPA-GUARDAR-PRODUCTO.md: esa
                    columna es SI solo cuando el conjunto ya aparece en data real de Meta o
                    LucidSales, nunca por diseño) queda exento: su plan ya cumplio su proposito
                    y no se re-castiga retroactivamente. Un producto sin ese registro real —
                    aunque ya tenga un `_PLAN.json` en disco, todavia sin publicar — SI debe
                    cumplir la regla (`ya_lanzo_fase1()`).

FASE 2 y 3 — _PLAN_FASE2.json / _PLAN_FASE3.json, el mismo esquema con "fase": 2|3 y dos
campos RAIZ obligatorios, porque ahi el angulo y el copy son constantes de la fase:
  "angulo_ganador": "ANGULO_KEY",         # el mismo en todos los conjuntos
  "copy": {"textos": [...], "titulos": [...], "descripcion": "..."}   # el copy unico de etapa-4
El copy va en la RAIZ, no dentro de cada conjunto: gen_publicacion.py lo lee de ahi y un copy
por conjunto se ignora. La cuenta y el page_id NO van: son de _DIM_PRODUCTOS.csv.

F3.exploracion (P12, T12, decision operador 22-sep-2026) — _PLAN_EXPLORACION.json, "fase":
"EXPLORACION" (string, no 3: no es el escalado, es el mini-F1 que corre en paralelo). Mismo
esquema que FASE 1 ("conjuntos": un angulo distinto por conjunto, sin angulo_ganador en la
raiz), con DOS reglas propias que valida esta funcion:
  - `exploracion_n_angulos` conjuntos (default 3, _PARAMETROS_DECISION.csv, ver
    verificar_voz.py-style: exploracion_n_angulos_requerido() abajo).
  - cada angulo_key es NUEVO: no puede estar entre los angulos que el producto ya probo
    (misma exclusion que reingreso_f1.angulos_probados() — no se reimplementa).
  - TODO EN IMAGEN, la misma regla dura que FASE 1 (mide el angulo, el formato es constante).
"""
import io, json, os, re, sys, csv

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(BASE)

TOOLS = os.path.dirname(os.path.abspath(__file__))
if TOOLS not in sys.path:
    sys.path.insert(0, TOOLS)
import verificar_voz  # T10: dueño de _VOZ_CLIENTE.csv y del umbral min_voz_requerido()
import reingreso_f1   # dueño de angulos_probados(): la exclusion de F3.exploracion NO se reimplementa

PRODUCTOS = "PRODUCTOS"
VOCABULARIO = "PRODUCTOS/_DIM_VOCABULARIO.csv"
PARAMETROS_DECISION = "PRODUCTOS/_PARAMETROS_DECISION.csv"


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
# "EXPLORACION" no es una fase numerica (F3.exploracion corre DENTRO de fase 3): descubrir_planes()
# solo usa los VALORES de este dict, así que una llave de texto no rompe nada.
NOMBRES_PLAN = {1: "_PLAN.json", 2: "_PLAN_FASE2.json", 3: "_PLAN_FASE3.json",
                "EXPLORACION": "_PLAN_EXPLORACION.json"}

EXPLORACION_N_ANGULOS = 3   # default P12; overrideable por _PARAMETROS_DECISION.csv (ver abajo)


def exploracion_n_angulos_requerido():
    """`exploracion_n_angulos` de _PARAMETROS_DECISION.csv si la fila existe, si no el default
    EXPLORACION_N_ANGULOS — mismo patrón que verificar_voz.min_voz_requerido()."""
    for r in leer_csv(PARAMETROS_DECISION):
        if (r.get("parametro") or "").strip() == "exploracion_n_angulos":
            try:
                return int(float(r.get("valor")))
            except (TypeError, ValueError):
                break
    return EXPLORACION_N_ANGULOS


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
DIM_CONJUNTOS = "PRODUCTOS/_DIM_CONJUNTOS.csv"
# Vocabulario de la columna `fase` de _DIM_CONJUNTOS.csv (dato real en disco: "FASE1"), con
# variantes toleradas por si alguna vez se escribe distinto.
FASE1_DIM_CONJUNTOS = {"FASE1", "F1", "1"}


def ya_lanzo_fase1(producto_key, filas_dim_conjuntos):
    """True si el producto ya LANZO de verdad su FASE 1 — no si solo tiene un `_PLAN.json` en
    disco ni si `_DIM_CONJUNTOS.csv` ya tiene sus 6 conjuntos como DISEÑO.

    Dueño del criterio: ETAPA-GUARDAR-PRODUCTO.md — "`verificado_en_csv`: SI si el
    `conjunto_meta` ya aparece en `_FACT_VENTAS.csv` o `_FACT_ENTREGA.csv` (llave confirmada
    contra data real) · NO si todavía es solo diseño". FASE 1, al cerrar, siempre escribe sus 6
    filas con `verificado_en_csv=NO` (caso real: OVULOS_PURITY, "SIN PUBLICAR" en sus notas) —
    por eso NO basta con que exista la fila; hace falta el SI que solo pone la data real.

    Se rechazó version del esquema del plan como llave (rejected en review):
    nada emite `"version": "v2"` (ni el docstring de este módulo, ni etapa-6), así que la regla
    nunca corría; y la invariante 5 de CLAUDE.md sube `VERSION` en cada rerun de un plan, así
    que el rerun de un producto VIEJO también terminaría en v2 y se re-castigaría, mientras un
    plan nuevo se queda en v1 y escapa — la llave equivocada. `_DIM_CONJUNTOS.csv` es data que
    el sistema ya posee y ya interpreta con este mismo significado en otro lugar (ETAPA-GUARDAR-
    PRODUCTO.md), así que no hay parsing nuevo que inventar ni CSV nuevo que acoplar."""
    for r in filas_dim_conjuntos or []:
        if (r.get("producto_key") or "").strip() != producto_key:
            continue
        if (r.get("fase") or "").strip().upper() not in FASE1_DIM_CONJUNTOS:
            continue
        if (r.get("verificado_en_csv") or "").strip().upper() == "SI":
            return True
    return False


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


def validar_plan_fase1(plan, validos, voz_filas=None, min_voz=None, dim_conjuntos_filas=None):
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
    if not ya_lanzo_fase1(plan.get("producto_key"), dim_conjuntos_filas):
        problemas.extend(validar_origen_angulo(
            plan, voz_filas if voz_filas is not None else [],
            min_voz if min_voz is not None else verificar_voz.MIN_VOZ_VERIFICADA_POR_ANGULO))
    return problemas


def validar_plan_exploracion(plan, angulos_probados, n_requerido=None):
    """F3.exploracion (P12): mismo esquema por-conjunto que FASE 1 (un angulo distinto por
    conjunto, TODO EN IMAGEN), mas la exclusion de angulos ya probados por el producto —
    `angulos_probados` es la lista que ya calcula reingreso_f1.angulos_probados(), nunca
    recalculada aca. NO exige angulo_ganador ni origen_angulo (T10 es una regla de FASE 1)."""
    problemas = []
    n_requerido = n_requerido if n_requerido is not None else exploracion_n_angulos_requerido()
    if plan.get("schema") != "plan/1":
        problemas.append("schema desconocido: %r" % plan.get("schema"))
    conjuntos = plan.get("conjuntos") or []
    if len(conjuntos) < n_requerido:
        problemas.append("F3.exploracion pide %d angulos nuevos y el plan trae %d "
                         "(_PARAMETROS_DECISION.csv exploracion_n_angulos)"
                         % (n_requerido, len(conjuntos)))
    vistos = set()
    probados = set(angulos_probados or [])
    for c in conjuntos:
        etq = "conjunto %s" % c.get("n")
        ak = c.get("angulo_key")
        if ak in vistos:
            problemas.append("%s: angulo_key duplicado %r" % (etq, ak))
        vistos.add(ak)
        if not re.match(r"^[A-Z0-9_]+$", ak or ""):
            problemas.append("%s: angulo_key con caracteres invalidos %r" % (etq, ak))
        if ak in probados:
            problemas.append("%s: angulo_key %r ya fue probado por este producto — F3.exploracion "
                             "mide angulos NUEVOS (misma exclusion que reingreso_f1.py)" % (etq, ak))
        if (c.get("formato") or "").strip().upper() != "IMAGEN":
            problemas.append("%s: formato %r != IMAGEN — F3.exploracion corre TODO EN IMAGEN, "
                             "la misma regla dura de FASE 1 (mide el angulo, el formato es "
                             "constante). Regenera el plan con etapa-6." % (etq, c.get("formato")))
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
    dim_conjuntos_filas = leer_csv(DIM_CONJUNTOS)

    errores = 0
    for ruta_plan in planes:
        with io.open(ruta_plan, encoding="utf-8") as fh:
            plan = json.load(fh)
        print("\n%s" % ruta_plan.replace("\\", "/"))
        fase = plan.get("fase")
        if fase == 1:
            problemas = validar_plan_fase1(plan, validos, voz_filas, min_voz, dim_conjuntos_filas)
        elif fase in (2, 3):
            problemas = validar_plan_fase2o3(plan)
        elif fase == "EXPLORACION":
            angulos_probados = reingreso_f1.angulos_probados(BASE, plan.get("producto_key") or "")
            problemas = validar_plan_exploracion(plan, angulos_probados)
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
