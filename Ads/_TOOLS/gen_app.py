# -*- coding: utf-8 -*-
"""gen_app.py — arma VISTAS/APP.html, la aplicacion unificada del sistema.

QUE HACE
Es el unico comando de la capa de vistas. Lee VISTAS/_MANIFIESTO.json (el sistema
declarado), verifica contra el disco que cada fuente exista y cuando se produjo,
lee PRODUCTOS/_LANZADOR.json (los productos) y escribe:

    VISTAS/_ESTADO.json   el manifiesto + el estado real de cada vista
    VISTAS/APP.html       la app: una barra lateral, todas las vistas adentro

LA SEPARACION QUE LO HACE SISTEMATICO
    _MANIFIESTO.json   EL SISTEMA     que vistas hay, quien las produce, cuando caducan
    _LANZADOR.json     LOS PRODUCTOS  lo unico que cambia de un lanzamiento a otro
    este script        LOS HECHOS     que existe en disco y desde cuando
    app_html.py        EL DIBUJO      no decide nada, solo muestra

Ningun dato del sistema se escribe dentro del HTML. Agregar una vista es una entrada
en el manifiesto, no una linea de codigo.

USO
    python Ads/_TOOLS/gen_app.py              refresca el portafolio y reescribe la app
    python Ads/_TOOLS/gen_app.py --todo       corre antes TODOS los generadores declarados
    python Ads/_TOOLS/gen_app.py --verificar  no escribe nada: sale 1 si falta una fuente

    La corrida sin banderas siempre refresca PRODUCTOS/_LANZADOR.json, porque esa data
    va incrustada dentro de APP.html. Las vistas de iframe no se tocan: viven aparte y
    la app muestra su edad real, asi que una vieja se ve, no se disfraza.
"""
import io
import os
import re
import sys
import json
import datetime
import subprocess

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(BASE)
sys.path.insert(0, os.path.join(BASE, "Ads", "_TOOLS"))

MANIFIESTO = "VISTAS/_MANIFIESTO.json"
FLUJO_JSON = "DOCTRINA/FLUJO.json"
LANZADOR_JSON = "PRODUCTOS/_LANZADOR.json"
GEN_LANZADOR = "Ads/_TOOLS/gen_lanzador.py"
DECISIONES_JSON = "PRODUCTOS/_DECISIONES.json"
GEN_DECISIONES = "Ads/_TOOLS/decidir.py"
CANONICOS_DIR = "Ads/_SWIPE/_BLUEPRINTS/CANONICOS"

HOY = datetime.date.today()

CAMPOS_VISTA = {"id", "seccion", "rotulo", "sub", "tipo", "render", "fuente",
                "genera", "dueno", "caduca", "pesada"}

# ── el bloque `acciones` (v7, HITO 3 de la app) ────────────────────────────────
ACCION_ID_RE = re.compile(r"^[a-z]+(\.[A-Za-z0-9_-]+)+$")
EJECUTOR_TIPOS_ACCION = {"script", "subagente", "skill", "mcp", "operador"}
PARAM_TIPOS_ACCION = {"producto_key", "cuenta_alias", "mercado", "enum", "texto", "archivo_temporal", "bandera"}
RUTAS_ESCRIBE_PERMITIDAS = ("PRODUCTOS/", "Ads/", "VISTAS/", "warehouse/")
RUTAS_ESCRIBE_PROHIBIDAS = ("DOCTRINA/", ".claude/", "app/")
# V22: marcadores que el runner llena además de los parámetros y los reservados.
MARCADORES_DE_PROMPT_PROPIO = {"ejecutor", "name", "ya_registrados"}
CAMPOS_ACCION_CONOCIDOS = {
    "id", "rotulo", "nodo", "ejecutor_tipo", "name", "comando", "salida", "parametros",
    "requiere_confirmacion", "aprobacion", "toca_meta", "herramientas", "herramientas_meta",
    "ordenes", "escribe", "idempotente", "precondicion", "visibilidad", "habilitada", "motivo",
    "tiempo_max_s", "presupuesto_usd", "datos_del_operador", "pasos", "prompt",
}
CAMPOS_ACCION_OBLIGATORIOS = {
    "id", "rotulo", "nodo", "ejecutor_tipo", "parametros", "requiere_confirmacion",
    "aprobacion", "toca_meta", "escribe", "precondicion", "visibilidad", "habilitada",
    "tiempo_max_s",
}



# ─────────────────────────────────────────────────────────────────────────────
# 1 · EL MANIFIESTO, VALIDADO
# ─────────────────────────────────────────────────────────────────────────────

def leer_flujo():
    """DOCTRINA/FLUJO.json, o None si no existe (un manifiesto v6 no lo necesita)."""
    if not os.path.exists(FLUJO_JSON):
        return None
    with io.open(FLUJO_JSON, encoding="utf-8") as fh:
        return json.load(fh)


def problemas_de_manifiesto(m, flujo):
    """Toda la validación del manifiesto, en una función pura (sin disco, sin excepciones).

    Devuelve la lista de problemas (vacía = válido). Cubre la validación de `vistas` que
    ya existía en v6, y —cuando `version >= 7`— las reglas V1-V21 del bloque `acciones`
    (`validar_acciones`, más abajo). `flujo` es el dict de DOCTRINA/FLUJO.json, o None.
    """
    problemas = []
    # las llaves de arriba, antes de mirar las vistas: sin ellas el resto no se
    # puede ni evaluar, y un KeyError crudo no le dice a nadie que arreglar
    for llave in ("version", "app", "secciones", "vistas"):
        if llave not in m:
            problemas.append("falta la llave de nivel raiz '%s'" % llave)
    for llave in ("titulo", "subtitulo", "salida", "estado", "vista_inicial"):
        if llave not in (m.get("app") or {}):
            problemas.append("falta app.%s" % llave)
    if problemas:
        return problemas  # sin secciones/vistas no se puede seguir validando

    secciones = {s["id"] for s in m.get("secciones", [])}
    vistos = set()
    for v in m.get("vistas", []):
        d = "vista '%s'" % v.get("id", "?")
        if not v.get("id"):
            problemas.append("hay una vista sin id")
            continue
        if v["id"] in vistos:
            problemas.append("%s esta declarada dos veces" % d)
        vistos.add(v["id"])
        if v.get("seccion") not in secciones:
            problemas.append("%s apunta a la seccion '%s', que no existe" % (d, v.get("seccion")))
        if v.get("tipo") not in ("nativa", "iframe"):
            problemas.append("%s tiene tipo '%s' (solo vale nativa o iframe)" % (d, v.get("tipo")))
        if v.get("tipo") == "iframe" and not v.get("fuente"):
            problemas.append("%s es de tipo iframe pero no declara fuente" % d)
        if v.get("tipo") == "nativa" and not v.get("render"):
            problemas.append("%s es nativa pero no declara que funcion la pinta" % d)
        sobra = set(v) - CAMPOS_VISTA
        if sobra:
            problemas.append("%s trae campos que el contrato no conoce: %s"
                             % (d, ", ".join(sorted(sobra))))
    vi = (m.get("app") or {}).get("vista_inicial")
    if vi not in vistos:
        problemas.append("la vista_inicial '%s' no esta declarada" % vi)

    if m.get("version", 0) >= 7:
        problemas.extend(validar_acciones(m, flujo))

    return problemas


def leer_manifiesto():
    if not os.path.exists(MANIFIESTO):
        raise SystemExit("no existe %s — es el archivo que declara el sistema." % MANIFIESTO)
    with io.open(MANIFIESTO, encoding="utf-8") as fh:
        m = json.load(fh)

    flujo = leer_flujo() if m.get("version", 0) >= 7 else None
    problemas = problemas_de_manifiesto(m, flujo)
    if problemas:
        raise SystemExit("MANIFIESTO INVALIDO — %s\n  · %s"
                         % (MANIFIESTO, "\n  · ".join(problemas)))
    return m


def _nodos_de_flujo_por_id(flujo):
    """{id sin prefijo de fase: nodo} — aplana fases[].nodos[] + ciclo[]."""
    out = {}
    for fase in (flujo or {}).get("fases", []) or []:
        for n in fase.get("nodos", []) or []:
            out[n["id"]] = n
    for n in (flujo or {}).get("ciclo", []) or []:
        out[n["id"]] = n
    return out


def _nombres_de_agentes():
    """Los `name:` de .claude/agents/*.md (el nombre con el que se invoca cada etapa por Task)."""
    nombres = set()
    carpeta = os.path.join(".claude", "agents")
    if not os.path.isdir(carpeta):
        return nombres
    for archivo in os.listdir(carpeta):
        if not archivo.endswith(".md"):
            continue
        with io.open(os.path.join(carpeta, archivo), encoding="utf-8") as fh:
            for linea in fh.read().split("\n---", 1)[0].splitlines():
                if linea.startswith("name:"):
                    nombres.add(linea.split(":", 1)[1].strip())
    return nombres


def _problemas_de_pasos(a, nf, bloque, d):
    """V20: los PASOS de una skill que la app corre de a una etapa por llamada.

    Los pasos no son una secuencia nueva: son la `secuencia` de FLUJO.json, agrupada. Aplanados
    tienen que ser idénticos a ella, y cada grupo de más de una etapa tiene que estar declarado
    como paralelo («a ∥ b») en el `como` del nodo. Así la secuencia sigue teniendo un solo dueño.
    """
    problemas = []
    pasos = a.get("pasos")
    if a.get("ejecutor_tipo") != "skill" or nf is None:
        return ["V20: %s declara 'pasos' pero no es la acción skill de un nodo" % d]
    if not isinstance(pasos, list) or not pasos or not all(
            isinstance(g, list) and g and all(isinstance(e, str) and e for e in g) for g in pasos):
        return ["V20: %s: 'pasos' tiene que ser una lista de grupos (listas) de etapas" % d]
    plano = [e for g in pasos for e in g]
    if plano != (nf.get("secuencia") or []):
        problemas.append("V20: %s: los pasos aplanados no son la 'secuencia' de FLUJO.json para %s"
                         % (d, nf.get("id")))
    como = nf.get("como") or ""
    for g in pasos:
        if len(g) > 1 and " ∥ ".join(g) not in como:
            problemas.append("V20: %s: el grupo %s no está declarado como paralelo («%s») en FLUJO.json"
                             % (d, g, " ∥ ".join(g)))
    agentes = _nombres_de_agentes()
    for e in plano:
        if "/" in e:
            if not os.path.exists(e):
                problemas.append("V20: %s: el paso '%s' no existe" % (d, e))
        elif e not in agentes:
            problemas.append("V20: %s: la etapa '%s' no es un agente de .claude/agents" % (d, e))
    prompt = (bloque.get("claude") or {}).get("prompt_paso")
    if not isinstance(prompt, list) or not prompt or not all(isinstance(x, str) for x in prompt):
        problemas.append("V20: %s tiene 'pasos' pero acciones.claude.prompt_paso no es una lista de líneas" % d)
    else:
        texto = "\n".join(prompt)
        for marca in ("{etapa}", "{etapas_dir}", "PASO_ETAPA: {etapa}"):
            if marca not in texto:
                problemas.append("V20: acciones.claude.prompt_paso no trae «%s»" % marca)
    return problemas


def _validar_prompt_propio(a, d, bloque, parametros, reservados):
    """V22: una acción subagente/skill puede traer su propio prompt (`prompt` = clave de
    `acciones.claude`): tiene que existir, ser una lista de líneas y no usar marcadores que el
    runner no sabe llenar (parámetros, reservados y los de MARCADORES_DE_PROMPT_PROPIO)."""
    if a.get("ejecutor_tipo") not in ("subagente", "skill"):
        return ["V22: %s declara 'prompt' pero no es subagente ni skill" % d]
    clave = a.get("prompt")
    lineas = (bloque.get("claude") or {}).get(clave) if isinstance(clave, str) else None
    if not isinstance(lineas, list) or not lineas or not all(isinstance(x, str) for x in lineas):
        return ["V22: %s: acciones.claude.%s no es una lista de líneas" % (d, clave)]
    usados = set(re.findall(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}", chr(10).join(lineas)))
    permitidos = set(parametros) | set(reservados) | MARCADORES_DE_PROMPT_PROPIO
    return ["V22: %s: acciones.claude.%s usa {%s}, que no es parámetro, reservado ni marcador conocido" % (d, clave, m)
            for m in sorted(usados - permitidos)]


def validar_acciones(m, flujo):
    """Las 21 reglas del bloque `acciones` (v7). Ver el diseño del Hito 3, §2.4 (V20-V21: Hito 4).

    No lanza: devuelve la lista de problemas, con el número de regla al frente de cada
    uno ("V5: ..."), para que las pruebas puedan filtrar por regla.
    """
    problemas = []
    bloque = m.get("acciones")
    if not isinstance(bloque, dict) or bloque.get("schema") != "acciones/1" or "lista" not in bloque:
        problemas.append("V1: falta el bloque 'acciones', su schema no es 'acciones/1', o falta 'lista'")
        return problemas

    lista = bloque.get("lista") or []
    nodos_flujo = _nodos_de_flujo_por_id(flujo)
    ids_vistos = set()
    ids_con_nodo = {}

    for a in lista:
        aid = a.get("id", "<sin id>")
        d = "la acción '%s'" % aid

        if aid in ids_vistos:
            problemas.append("V2: %s está repetida" % d)
        ids_vistos.add(aid)
        if not ACCION_ID_RE.match(str(a.get("id", ""))):
            problemas.append("V2: %s no cumple el patrón de id" % d)

        faltan = CAMPOS_ACCION_OBLIGATORIOS - set(a)
        if faltan:
            problemas.append("V3: a %s le faltan los campos %s" % (d, sorted(faltan)))
        sobra = set(a) - CAMPOS_ACCION_CONOCIDOS
        if sobra:
            problemas.append("V3: %s trae campos que el contrato no conoce: %s" % (d, sorted(sobra)))

        ejecutor_tipo = a.get("ejecutor_tipo")
        if ejecutor_tipo not in EJECUTOR_TIPOS_ACCION:
            problemas.append("V4: %s tiene ejecutor_tipo '%s', fuera del vocabulario" % (d, ejecutor_tipo))

        nodo_id = a.get("nodo")
        nf = None
        if nodo_id is not None:
            nf = nodos_flujo.get(nodo_id)
            if nf is None:
                problemas.append("V5: %s apunta al nodo '%s', que no existe en FLUJO.json" % (d, nodo_id))
            else:
                ids_con_nodo.setdefault(nodo_id, []).append(aid)
                ej = nf.get("ejecutor", {}) or {}
                if ej.get("tipo") != ejecutor_tipo:
                    problemas.append("V5: %s declara ejecutor_tipo '%s' pero FLUJO.json dice '%s' para %s"
                                     % (d, ejecutor_tipo, ej.get("tipo"), nodo_id))
                if ej.get("name") != a.get("name"):
                    problemas.append("V5: %s declara name '%s' pero FLUJO.json dice '%s' para %s"
                                     % (d, a.get("name"), ej.get("name"), nodo_id))
                if ejecutor_tipo == "script" and ej.get("cmd") and a.get("comando") != ej.get("cmd"):
                    problemas.append("V5: %s: el comando no coincide con el cmd de FLUJO.json para %s"
                                     % (d, nodo_id))

        comando = a.get("comando")
        if ejecutor_tipo == "script":
            if not comando:
                problemas.append("V7: %s es script pero no declara 'comando'" % d)
            else:
                if comando[0] != "python":
                    problemas.append("V7: %s no arranca con 'python'" % d)
                if len(comando) < 2 or not comando[1].startswith("Ads/_TOOLS/") or not comando[1].endswith(".py"):
                    problemas.append("V7: %s no llama a un script de Ads/_TOOLS/*.py" % d)
                elif not os.path.exists(comando[1]):
                    problemas.append("V7: %s referencia '%s', que no existe" % (d, comando[1]))
                for tok in comando:
                    if any(mala in tok for mala in ("--bare", "--dangerously-skip-permissions", "shell")):
                        problemas.append("V7: %s trae un token prohibido: '%s'" % (d, tok))
        else:
            if comando is not None:
                problemas.append("V8: %s no es script pero declara 'comando'" % d)
            if ejecutor_tipo in ("subagente", "skill"):
                if not a.get("name"):
                    problemas.append("V8: %s es %s pero no declara 'name'" % (d, ejecutor_tipo))
                if a.get("presupuesto_usd") is None:
                    problemas.append("V8: %s es %s pero no declara 'presupuesto_usd'" % (d, ejecutor_tipo))

        parametros = a.get("parametros") or {}
        reservados = set(bloque.get("reservados") or [])
        placeholders = set()
        if comando:
            for tok in comando:
                placeholders |= set(re.findall(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}", tok))
        for ph in placeholders:
            if ph in reservados:
                continue
            p = parametros.get(ph)
            if p is None:
                problemas.append("V9: %s usa {%s} en 'comando' pero no está en 'parametros' ni en 'reservados'"
                                 % (d, ph))
            elif p.get("bandera"):
                problemas.append("V9: %s: el parámetro '%s' tiene 'bandera' pero aparece como {%s} en 'comando'"
                                 % (d, ph, ph))
        if comando is not None:
            for pname, p in parametros.items():
                if not p.get("bandera") and pname not in placeholders:
                    problemas.append("V9: %s: el parámetro '%s' no tiene 'bandera' y no aparece en 'comando'"
                                     % (d, pname))

        for pname, p in parametros.items():
            tipo = p.get("tipo")
            if tipo not in PARAM_TIPOS_ACCION:
                problemas.append("V10: %s: el parámetro '%s' tiene tipo '%s' fuera del vocabulario"
                                 % (d, pname, tipo))
                continue
            if tipo == "enum" and not p.get("valores"):
                problemas.append("V10: %s: el parámetro '%s' es enum sin 'valores'" % (d, pname))
            if tipo == "texto":
                patron = p.get("patron")
                if not patron:
                    problemas.append("V10: %s: el parámetro '%s' es texto sin 'patron'" % (d, pname))
                else:
                    try:
                        re.compile(patron)
                    except re.error:
                        problemas.append("V10: %s: el parámetro '%s' tiene un patrón que no compila" % (d, pname))

        if "prompt" in a:
            problemas.extend(_validar_prompt_propio(a, d, bloque, parametros, reservados))

        requiere_confirmacion = a.get("requiere_confirmacion")
        aprobacion = a.get("aprobacion")
        toca_meta = a.get("toca_meta")
        if (ejecutor_tipo == "mcp" or toca_meta) and (requiere_confirmacion is not True or aprobacion != "por_orden"):
            problemas.append("V11: %s es mcp o toca Meta pero no exige confirmación + aprobación por_orden" % d)

        herramientas = a.get("herramientas") or []
        herramientas_meta = a.get("herramientas_meta")
        if herramientas_meta and not toca_meta:
            problemas.append("V12: %s declara herramientas_meta pero toca_meta es false" % d)
        if toca_meta and not (herramientas_meta or {}).get("escritura"):
            problemas.append("V12: %s toca_meta pero no declara herramientas_meta.escritura" % d)
        for h in herramientas:
            if h.startswith("mcp__") or h == "*":
                problemas.append("V12: %s trae '%s' en 'herramientas' (las de Meta van en herramientas_meta)"
                                 % (d, h))

        ordenes = a.get("ordenes")
        habilitada = a.get("habilitada")
        if toca_meta and habilitada and ordenes is None:
            problemas.append("V13: %s toca Meta, está habilitada, y no declara 'ordenes'" % d)
        if ordenes:
            for campo in ("generador", "verificador"):
                oid = ordenes.get(campo)
                oacc = next((x for x in lista if x.get("id") == oid), None)
                if not oacc or oacc.get("ejecutor_tipo") != "script":
                    problemas.append("V13: %s: ordenes.%s ('%s') no es una acción script declarada"
                                     % (d, campo, oid))

        for ruta in (a.get("escribe") or []):
            if os.path.isabs(ruta) or ".." in ruta:
                problemas.append("V14: %s: la ruta de escribe '%s' es absoluta o sube de carpeta" % (d, ruta))
            elif ruta.startswith(RUTAS_ESCRIBE_PROHIBIDAS):
                problemas.append("V14: %s: la ruta de escribe '%s' toca una carpeta prohibida" % (d, ruta))
            elif not ruta.startswith(RUTAS_ESCRIBE_PERMITIDAS):
                problemas.append("V14: %s: la ruta de escribe '%s' no empieza por PRODUCTOS/, Ads/, VISTAS/ o warehouse/"
                                 % (d, ruta))

        if ejecutor_tipo in ("subagente", "skill") and not (a.get("escribe") or []):
            problemas.append("V15: %s es %s pero 'escribe' está vacío" % (d, ejecutor_tipo))

        if a.get("visibilidad") == "interna" and nodo_id is not None:
            problemas.append("V16: %s es interna pero tiene 'nodo' (un nodo siempre es un botón)" % d)

        # Los datos que el operador carga los declaran los nodos `operador` (F1.congelar_inputs) y
        # los que se BLOQUEAN por un dato suyo aunque los ejecute otro (F1.publicar sin cuenta).
        if ejecutor_tipo == "operador" or a.get("datos_del_operador"):
            datos_nodo = set()
            if nf:
                datos_nodo = {r["dato"] for r in (nf.get("requiere") or [])} | {p["dato"] for p in (nf.get("produce") or [])}
            for item in (a.get("datos_del_operador") or []):
                if item.get("dato") not in datos_nodo:
                    problemas.append("V17: %s: el dato '%s' no coincide con requiere/produce del nodo"
                                     % (d, item.get("dato")))
                escritoras = [item.get("accion")] + list(item.get("alternativas") or [])
                for accion_escritora in escritoras:
                    if accion_escritora is None:
                        continue
                    oacc = next((x for x in lista if x.get("id") == accion_escritora), None)
                    if not oacc or oacc.get("ejecutor_tipo") != "script":
                        problemas.append("V17: %s: la acción escritora '%s' de '%s' no es un script declarado"
                                         % (d, accion_escritora, item.get("dato")))

        if habilitada is False and not a.get("motivo"):
            problemas.append("V18: %s está deshabilitada pero no trae 'motivo'" % d)

        if "pasos" in a:
            problemas.extend(_problemas_de_pasos(a, nf, bloque, d))

    for nid in nodos_flujo:
        asociadas = ids_con_nodo.get(nid, [])
        if len(asociadas) == 0:
            problemas.append("V6: el nodo '%s' de FLUJO.json no tiene ninguna acción declarada" % nid)
        elif len(asociadas) > 1:
            problemas.append("V6: el nodo '%s' tiene más de una acción declarada: %s" % (nid, asociadas))

    ids_por_id = {a.get("id"): a for a in lista}
    for tid in (bloque.get("tras_escribir") or []):
        ta = ids_por_id.get(tid)
        if not ta or ta.get("ejecutor_tipo") != "script" or ta.get("visibilidad") != "interna" or not ta.get("idempotente"):
            problemas.append("V19: tras_escribir '%s' no es una acción script, interna e idempotente" % tid)

    # V21 — quién resuelve cada bloqueo con `clave` de gen_publicacion.py (el checklist de la app)
    escritores = bloque.get("escritores_de_bloqueo")
    if escritores is not None:
        if not isinstance(escritores, dict):
            problemas.append("V21: escritores_de_bloqueo tiene que ser un objeto {clave: acción}")
        else:
            for clave, aid in escritores.items():
                ea = ids_por_id.get(aid)
                if not ea or ea.get("ejecutor_tipo") != "script" or ea.get("visibilidad") != "interna":
                    problemas.append("V21: escritores_de_bloqueo.%s ('%s') no es una acción script interna" % (clave, aid))

    return problemas


# ─────────────────────────────────────────────────────────────────────────────
# 2 · LOS HECHOS: que hay en disco y desde cuando
# ─────────────────────────────────────────────────────────────────────────────

def edad(ruta):
    """Dias entre hoy y la ultima escritura del archivo. None si no existe."""
    if not ruta or not os.path.exists(ruta):
        return None, None
    mt = datetime.date.fromtimestamp(os.path.getmtime(ruta))
    return (HOY - mt).days, mt.isoformat()


def etiqueta_edad(dias):
    if dias == 0:
        return "hoy"
    if dias == 1:
        return "ayer"
    return "hace %dd" % dias


def estado_de(v):
    """Traduce la edad del archivo a la insignia que ve el operador.

    Una vista con caduca=false NO lleva insignia: el banco de creativos y la
    doctrina cambian cuando cambia el metodo, no cuando pasa el dia. Marcarlas
    en rojo por antiguedad seria una alarma falsa, y una alarma falsa entrena
    al operador a ignorar tambien las verdaderas.
    """
    fuente = v.get("fuente")
    if not fuente:
        return {"existe": True, "mtime": None, "edad_dias": None, "clase": "ninguna",
                "etiqueta": "", "detalle": "se calcula al generar la app", "chip": "c-neutro"}

    dias, mt = edad(fuente)
    if dias is None:
        return {"existe": False, "mtime": None, "edad_dias": None, "clase": "falta",
                "etiqueta": "falta", "detalle": "el archivo no existe", "chip": "c-crit"}

    cad = v.get("caduca")
    if not cad:
        return {"existe": True, "mtime": mt, "edad_dias": dias, "clase": "ninguna",
                "etiqueta": "", "detalle": "no caduca · escrita %s" % mt, "chip": "c-neutro"}

    if dias <= cad["ok_dias"]:
        clase, chip = "ok", "c-good"
    elif dias <= cad["tibia_dias"]:
        clase, chip = "tibia", "c-warn"
    else:
        clase, chip = "vieja", "c-crit"
    return {"existe": True, "mtime": mt, "edad_dias": dias, "clase": clase,
            "etiqueta": etiqueta_edad(dias), "chip": chip,
            "detalle": "%s · escrita %s" % (etiqueta_edad(dias), mt)}


def hacia_vistas(ruta):
    """La ruta tal como la tiene que pedir APP.html, que vive en VISTAS/."""
    if not ruta:
        return None
    return os.path.relpath(ruta, "VISTAS").replace("\\", "/")


# ─────────────────────────────────────────────────────────────────────────────
# 3 · LOS PRODUCTOS: lo que el portafolio tiene pendiente
# ─────────────────────────────────────────────────────────────────────────────

def leer_lanzador(refrescar=True):
    """El JSON de productos, la data de las vistas nativas.

    Se refresca SIEMPRE, no solo con --todo, y la razon es la diferencia entre los
    dos tipos de vista: las de iframe muestran un HTML que vive aparte y se puede
    regenerar despues; las NATIVAS llevan su data incrustada dentro de APP.html.
    Si el JSON de productos quedara viejo, la app dictaria presupuestos viejos sin
    ninguna senal de que lo hace. Cuesta poco: son unos CSV.
    """
    if refrescar or not os.path.exists(LANZADOR_JSON):
        correr("python %s" % GEN_LANZADOR)
    if not os.path.exists(LANZADOR_JSON):
        raise SystemExit("no se pudo producir %s — corre %s a mano y mira el error."
                         % (LANZADOR_JSON, GEN_LANZADOR))
    with io.open(LANZADOR_JSON, encoding="utf-8") as fh:
        return json.load(fh)


def pendientes_de(lanzador):
    """Todo lo que le falta al portafolio, en una sola lista con su dueno al lado.

    No se escribe a mano en ningun lado: sale de los bloqueantes que ya calculo
    gen_lanzador.py comparando cada _PLAN.json contra _DIM_PRODUCTOS.csv.
    """
    pend, sin_plan = [], []
    for p in lanzador.get("productos", []):
        if p.get("tiene_plan"):
            L = p["plan"]
            for b in L.get("bloqueantes", []):
                pend.append({"producto": p["nombre"], "que": b["que"],
                             "quien": b["quien"], "bloquea": True})
            for f in L.get("faltantes", []):
                pend.append({"producto": p["nombre"], "que": f,
                             "quien": "etapa-4 / etapa-6", "bloquea": False})
        else:
            sin_plan.append({"producto": p["nombre"], "estado": p.get("estado") or "—",
                             "falta": [f["que"] for f in (p.get("falta_para_plan") or [])],
                             "quien": ", ".join(sorted({f["quien"]
                                     for f in (p.get("falta_para_plan") or [])}))})
    pend.sort(key=lambda x: (not x["bloquea"], x["producto"]))
    return pend, sin_plan


def leer_decisiones(refrescar=False):
    """Carga PRODUCTOS/_DECISIONES.json. Si no existe, corre el motor determinista."""
    if refrescar or not os.path.exists(DECISIONES_JSON):
        correr("python %s --escribir" % GEN_DECISIONES)
    if not os.path.exists(DECISIONES_JSON):
        return {
            "generado": HOY.isoformat(),
            "motor": "decidir v4 (IC Bayesiana + Riesgo Asimétrico + tres relojes separados)",
            "ventana_fatiga_dias": 3,
            "grano": "angulo",
            "ventana_dias": 14,
            "resumen_acciones": {},
            "productos": []
        }
    with io.open(DECISIONES_JSON, encoding="utf-8") as fh:
        return json.load(fh)


def leer_blueprints():
    """Carga los 22 blueprints canónicos desde Ads/_SWIPE/_BLUEPRINTS/CANONICOS/."""
    if not os.path.isdir(CANONICOS_DIR):
        return []
    import glob
    archivos = sorted(glob.glob(os.path.join(CANONICOS_DIR, "CN*.json")))
    lista = []
    for arch in archivos:
        try:
            with io.open(arch, encoding="utf-8") as fh:
                d = json.load(fh)
                embudo_counts = d.get('perfil', {}).get('rol_embudo', {})
                dominant_embudo = max(embudo_counts.items(), key=lambda x: x[1])[0] if embudo_counts else 'MOFU'
                c_counts = d.get('perfil', {}).get('concepto_key', {})
                dominant_concept = max(c_counts.items(), key=lambda x: x[1])[0] if c_counts else 'C2_BENEFICIOS'

                lista.append({
                    'id': d.get('canonico_id', ''),
                    'codigo': d.get('canonico_id', '').split('_')[0],
                    'nombre': d.get('nombre', ''),
                    'dispositivo': d.get('dispositivo_canonico', ''),
                    'cuando_elegirlo': d.get('cuando_elegirlo', ''),
                    'embudo': dominant_embudo,
                    'embudo_dist': embudo_counts,
                    'concepto': dominant_concept,
                    'n_miembros': d.get('n_miembros', 0),
                    'ref': d.get('ficha_referencia', ''),
                    'score_ref': d.get('score_referencia', 0),
                    'reglas': d.get('reglas_duras_referencia', [])[:6],
                    'cuando_usar': d.get('cuando_usar', [])[:5],
                    'cuando_no': d.get('cuando_no_usar', [])[:5],
                    'variables': d.get('contrato_variables', []),
                })
        except Exception:
            pass
    return lista


# ─────────────────────────────────────────────────────────────────────────────
# 4 · CORRER LOS GENERADORES (--todo)
# ─────────────────────────────────────────────────────────────────────────────

def correr(cmd):
    """Corre un generador. Devuelve True si salio bien."""
    partes = cmd.split()
    if partes and partes[0] in ("python", "python3"):
        partes[0] = sys.executable
    try:
        r = subprocess.run(partes, cwd=BASE, capture_output=True, timeout=600)
    except (OSError, subprocess.TimeoutExpired) as e:
        print("  FALLO  %s  (%s)" % (cmd, e))
        return False
    if r.returncode == 0:
        print("  ok     %s" % cmd)
        return True
    cola = (r.stderr or b"").decode("utf-8", "replace").strip().splitlines()
    print("  FALLO  %s  (exit %d) %s" % (cmd, r.returncode, cola[-1] if cola else ""))
    return False


def correr_todo(man):
    """Cada comando distinto del manifiesto, una sola vez, en el orden declarado."""
    vistos, fallos = [], 0
    for v in man["vistas"]:
        cmd = v.get("genera")
        if not cmd or cmd in vistos or cmd.endswith("gen_app.py"):
            continue
        vistos.append(cmd)
        if not correr(cmd):
            fallos += 1
    print("· %d generador(es) corridos, %d con error" % (len(vistos), fallos))
    return fallos


# ─────────────────────────────────────────────────────────────────────────────
# 5 · ARMAR EL ESTADO Y ESCRIBIR
# ─────────────────────────────────────────────────────────────────────────────

def construir(man, lanzador):
    vistas = []
    for v in man["vistas"]:
        w = dict(v)
        w["src"] = hacia_vistas(v.get("fuente"))
        w["estado"] = estado_de(v)
        vistas.append(w)

    pend, sin_plan = pendientes_de(lanzador)
    con_edad = [v for v in vistas if v["estado"]["clase"] in ("ok", "tibia", "vieja")]

    return {
        "generado": HOY.isoformat(),
        "version": man["version"],
        "app": man["app"],
        "vista_inicial": man["app"]["vista_inicial"],
        "secciones": man["secciones"],
        "vistas": vistas,
        "salud": {
            "al_dia": sum(1 for v in con_edad if v["estado"]["clase"] == "ok"),
            "envejecidas": sum(1 for v in con_edad if v["estado"]["clase"] in ("tibia", "vieja")),
            "faltantes": sum(1 for v in vistas if v["estado"]["clase"] == "falta"),
            "pendientes": pend,
            "sin_plan": sin_plan,
        },
    }


def escribir(estado, lanzador, decisiones, blueprints):
    from app_html import HTML
    app = estado["app"]
    if not os.path.isdir("VISTAS"):
        os.makedirs("VISTAS")

    with io.open(app["estado"], "w", encoding="utf-8") as fh:
        fh.write(json.dumps(estado, ensure_ascii=False, indent=2))
    print("escrito %s" % app["estado"])

    with io.open(app["salida"], "w", encoding="utf-8") as fh:
        fh.write(HTML(estado, lanzador, decisiones, blueprints))
    print("escrito %s" % app["salida"])


def _cli_validar_manifiesto(como_json):
    """--validar-manifiesto: solo valida el manifiesto (y FLUJO.json si aplica). No escribe nada."""
    if not os.path.exists(MANIFIESTO):
        problemas, m = ["no existe %s" % MANIFIESTO], {}
    else:
        with io.open(MANIFIESTO, encoding="utf-8") as fh:
            m = json.load(fh)
        flujo = leer_flujo() if m.get("version", 0) >= 7 else None
        problemas = problemas_de_manifiesto(m, flujo)
    ok = not problemas
    if como_json:
        print(json.dumps({"ok": ok, "version": m.get("version"), "problemas": problemas, "avisos": []},
                         ensure_ascii=False))
    elif ok:
        print("· manifiesto válido (version %s)" % m.get("version"))
    else:
        print("MANIFIESTO INVALIDO:")
        for p in problemas:
            print("  · %s" % p)
    return 0 if ok else 1


def main():
    if "--validar-manifiesto" in sys.argv:
        return _cli_validar_manifiesto("--json" in sys.argv)

    man = leer_manifiesto()
    todo = "--todo" in sys.argv
    if todo:
        print("· corriendo los generadores declarados en el manifiesto")
        correr_todo(man)

    # --verificar solo mira el disco: no escribe ni corre nada
    lanzador = leer_lanzador(refrescar=not todo and "--verificar" not in sys.argv)
    decisiones = leer_decisiones(refrescar=todo)
    blueprints = leer_blueprints()
    estado = construir(man, lanzador)
    S = estado["salud"]

    if "--verificar" in sys.argv:
        for v in estado["vistas"]:
            if v["estado"]["clase"] == "falta":
                print("FALTA  %-12s %-34s  la produce: %s"
                      % (v["id"], v["fuente"], v.get("genera")))
        print("· %d al dia · %d envejecidas · %d faltantes · %d pendientes de producto"
              % (S["al_dia"], S["envejecidas"], S["faltantes"], len(S["pendientes"])))
        return 1 if S["faltantes"] else 0

    escribir(estado, lanzador, decisiones, blueprints)
    print("· %d vistas · %d al dia · %d envejecidas · %d faltantes · %d pendientes de producto · %d blueprints cargados"
          % (len(estado["vistas"]), S["al_dia"], S["envejecidas"], S["faltantes"],
             len(S["pendientes"]), len(blueprints)))
    return 0


if __name__ == "__main__":
    sys.exit(main())

