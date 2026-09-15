# -*- coding: utf-8 -*-
"""gen_plan.py — construye PRODUCTOS/[X]/_PLAN.json, el CONTRATO DE LANZAMIENTO.

QUE ES
El unico archivo que LANZADOR.html consume para armar un lanzamiento. Contiene SOLO
contenido creativo (angulos, prompts, copies) y los hechos del producto. NO contiene
nombres de campana, presupuestos, bandas de edad ni fechas: todo eso lo DERIVA
gen_lanzador.py desde la doctrina y los CSV. Un dato, un dueno.

    contenido creativo  -> _PLAN.json        (lo escribe etapa-6 / este adaptador)
    todo lo derivable   -> gen_lanzador.py   (nombres, plata, fechas, gates)

POR QUE UN JSON Y NO EL TXT
`1_HACER_MANUAL.txt` es prosa: cada producto lo escribio distinto y ninguno se puede
leer con un programa. Mientras el plan viva en prosa, el operador tiene que interpretar
en vez de ejecutar. El JSON hace que el mismo plan se pueda renderizar, validar contra
_DIM_VOCABULARIO.csv y comparar entre productos.

MODOS
  1. ADAPTADOR SERUM  — parsea el unico 1_HACER_MANUAL.txt con formato regular que
     existe hoy (SERUM_COLAGENO_BOTOX). Es de un solo uso: sirve para sembrar el
     sistema con un plan real, no para convertirse en la via de entrada.
  2. VALIDAR          — revisa un _PLAN.json ya escrito y reporta lo que le falta.

USO
    python Ads/_TOOLS/gen_plan.py --adaptar SERUM_COLAGENO_BOTOX
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
      "copy": {"textos": ["...", "..."], "titulos": ["..."], "descripcion": "..."}
  }],
  "_faltantes": ["lo que el plan no pudo llenar"]
}
"""
import io, json, os, re, sys, csv

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(BASE)

PRODUCTOS = "PRODUCTOS"
DIM_PRODUCTOS = "PRODUCTOS/_DIM_PRODUCTOS.csv"
VOCABULARIO = "PRODUCTOS/_DIM_VOCABULARIO.csv"


def leer_csv(ruta):
    if not os.path.exists(ruta):
        return []
    with io.open(ruta, encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def slug_angulo(texto):
    """'Cara cansada que no se quita' -> 'CARA_CANSADA_QUE_NO_SE_QUITA' (recortado)."""
    t = texto.upper()
    for a, b in [("Á", "A"), ("É", "E"), ("Í", "I"), ("Ó", "O"), ("Ú", "U"), ("Ñ", "N")]:
        t = t.replace(a, b)
    t = re.sub(r"[^A-Z0-9 ]", " ", t)
    palabras = [p for p in t.split() if p not in ("QUE", "NO", "SE", "DE", "LA", "EL", "MI",
                                                  "TU", "LOS", "LAS", "UN", "UNA", "Y", "A",
                                                  "ME", "TE", "LE", "SU", "AL", "EN")]
    return "_".join(palabras[:3])


# ─────────────────────────────────────────────────────────────────────────────
# ADAPTADOR — 1_HACER_MANUAL.txt con el formato de SERUM_COLAGENO_BOTOX
# ─────────────────────────────────────────────────────────────────────────────

def adaptar(producto_key):
    prods = {p["producto_key"]: p for p in leer_csv(DIM_PRODUCTOS)}
    if producto_key not in prods:
        sys.exit("producto_key '%s' no existe en _DIM_PRODUCTOS.csv" % producto_key)
    prod = prods[producto_key]
    carpeta = os.path.join(PRODUCTOS, prod["slug_carpeta"])
    fuente = os.path.join(carpeta, "1_HACER_MANUAL.txt")
    if not os.path.exists(fuente):
        sys.exit("no existe %s" % fuente)

    with io.open(fuente, encoding="utf-8") as fh:
        txt = fh.read()
    lineas = txt.split("\n")
    faltantes = []

    # --- cabecera: pagina y oferta -------------------------------------------
    pagina = None
    m = re.search(r"^FanPage de pauta:\s*(.+)$", txt, re.M)
    if m:
        pagina = m.group(1).strip()
    oferta_txt, precio_q, oferta_key = None, None, "SIN_PRECIO"
    m = re.search(r"^Oferta:\s*(.+)$", txt, re.M)
    if m:
        oferta_txt = m.group(1).strip()
        mp = re.search(r"Q\s*(\d+)", oferta_txt)
        if mp:
            precio_q = int(mp.group(1))
        if re.search(r"\b2\s*x\s*1\b", oferta_txt, re.I):
            oferta_key = "2X1"
        elif re.search(r"\b4\s*x\s*2\b", oferta_txt, re.I):
            oferta_key = "4X2"
        elif precio_q:
            oferta_key = "1U"

    # --- seccion B: la tabla de conjuntos ------------------------------------
    conjuntos = {}
    for ln in lineas:
        m = re.match(r"^\|\s*(\d+)\s*\|\s*([^|]+)\|\s*([^|]+)\|\s*([^|]+)\|"
                     r"\s*([^|]*)\|\s*([^|]*)\|", ln)
        if not m:
            continue
        n = int(m.group(1))
        titulo = m.group(3).strip()
        formato = m.group(4).strip().upper()
        precio_col = m.group(6).strip().upper()
        conjuntos[n] = {
            "n": n,
            "angulo_key": slug_angulo(titulo),
            "angulo_titulo": titulo,
            "avatar_edad": None,
            "avatar_genero": "MIXTO",
            "nivel_conciencia": None,
            "formato": "VIDEO" if "VIDEO" in formato else "IMAGEN",
            "lleva_precio": precio_col.startswith("S"),
            "archivo_creativo": None,
            "prompt_imagen": None,
            "copy": {"textos": [], "titulos": [], "descripcion": None},
        }
    if not conjuntos:
        sys.exit("no se encontro la tabla de conjuntos (seccion B)")

    # --- archivos reservados --------------------------------------------------
    for m in re.finditer(r"(%s_(\d+)_[a-z0-9]+\.(?:jpg|png|mp4))" % re.escape(producto_key), txt):
        n = int(m.group(2))
        if n in conjuntos:
            conjuntos[n]["archivo_creativo"] = m.group(1)
    for m in re.finditer(r"[·\s](_(\d+)_[a-z0-9]+\.(?:jpg|png|mp4))", txt):
        n = int(m.group(2))
        if n in conjuntos and not conjuntos[n]["archivo_creativo"]:
            conjuntos[n]["archivo_creativo"] = producto_key + m.group(1)

    # --- seccion C.1: prompts de imagen --------------------------------------
    bloques = re.split(r"^━━━ AD CONJUNTO (\d+) — (.+?) ━━━$", txt, flags=re.M)
    for i in range(1, len(bloques) - 1, 3):
        n = int(bloques[i])
        cuerpo = bloques[i + 2]
        # el prompt termina donde arranca el siguiente separador de seccion
        corte = re.search(r"^(?:━━━|─────)", cuerpo, re.M)
        if corte:
            cuerpo = cuerpo[:corte.start()]
        if n in conjuntos:
            conjuntos[n]["prompt_imagen"] = cuerpo.strip()
            # la edad del avatar viaja dentro de la escena del prompt
            me = (re.search(r"(\d{2})\s*-\s*(\d{2})\s*a[nñ]os", cuerpo)
                  or re.search(r"(?:mujer|hombre|latina|latino)[^\r\n]{0,20}?"
                               r"(\d{2})\s*-\s*(\d{2})", cuerpo, re.I))
            if me:
                conjuntos[n]["avatar_edad"] = "%s-%s" % (me.group(1), me.group(2))
            if re.search(r"\bmujer\b", cuerpo, re.I) and not re.search(r"\bhombre\b", cuerpo, re.I):
                conjuntos[n]["avatar_genero"] = "MUJER"
            elif re.search(r"\bhombre\b", cuerpo, re.I) and not re.search(r"\bmujer\b", cuerpo, re.I):
                conjuntos[n]["avatar_genero"] = "HOMBRE"

    # --- seccion D: copies ----------------------------------------------------
    bloques = re.split(r"^──────── CONJUNTO (\d+) — (.+?) ────────$", txt, flags=re.M)
    for i in range(1, len(bloques) - 1, 3):
        n = int(bloques[i])
        cuerpo = bloques[i + 2]
        corte = re.search(r"^(?:════|────────)", cuerpo, re.M)
        if corte:
            cuerpo = cuerpo[:corte.start()]
        if n not in conjuntos:
            continue
        # variaciones de texto principal
        partes = re.split(r"^Variaci[oó]n \d+[^\n]*:\s*$", cuerpo, flags=re.M)
        textos = []
        for p in partes[1:]:
            fin = re.search(r"^(?:T[IÍ]TULOS?|DESCRIPCI[OÓ]N|Lleva precio)\s*:", p, re.M)
            if fin:
                p = p[:fin.start()]
            p = p.strip()
            if p:
                textos.append(p)
        conjuntos[n]["copy"]["textos"] = textos
        mt = re.search(r"^T[IÍ]TULOS?\s*:\s*(.+)$", cuerpo, re.M)
        if mt:
            conjuntos[n]["copy"]["titulos"] = [
                t.strip().strip('"').strip() for t in mt.group(1).split("/") if t.strip()]
        md = re.search(r"^DESCRIPCI[OÓ]N\s*:\s*(.+)$", cuerpo, re.M)
        if md:
            conjuntos[n]["copy"]["descripcion"] = md.group(1).strip()

    orden = [conjuntos[k] for k in sorted(conjuntos)]

    # --- lo que no se pudo llenar --------------------------------------------
    for c in orden:
        etq = "conjunto %d (%s)" % (c["n"], c["angulo_key"])
        if not c["prompt_imagen"] and c["formato"] == "IMAGEN":
            faltantes.append("%s: sin prompt de imagen" % etq)
        if not c["copy"]["textos"]:
            faltantes.append("%s: sin texto principal" % etq)
        if not c["archivo_creativo"]:
            faltantes.append("%s: sin nombre de archivo de creativo" % etq)
        if not c["avatar_edad"]:
            faltantes.append("%s: sin avatar_edad -> corre en banda amplia 18-65+" % etq)
        if not c["nivel_conciencia"]:
            faltantes.append("%s: sin nivel_conciencia -> la firma sale con ? en NC" % etq)
    if not prod.get("page_id"):
        faltantes.append("producto: page_id SIN ASIGNAR -> no se puede publicar")
    if not prod.get("cuenta_id"):
        faltantes.append("producto: cuenta publicitaria SIN ASIGNAR")

    plan = {
        "schema": "plan/1",
        "producto_key": producto_key,
        "fase": 1,
        "version": "v1",
        "origen": "adaptado de %s por gen_plan.py" % fuente.replace("\\", "/"),
        "pagina": {"nombre": pagina, "page_id": prod.get("page_id") or None},
        "oferta": {"oferta_key": oferta_key, "precio_q": precio_q, "texto": oferta_txt},
        "concepto_control": {"concepto_key": "C2_BENEFICIOS", "variante": "ligera",
                             "canonico_id": "CN05_LISTA_BENEFICIOS"},
        "conjuntos": orden,
        "_faltantes": faltantes,
    }

    salida = os.path.join(carpeta, "_PLAN.json")
    with io.open(salida, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(plan, ensure_ascii=False, indent=2))
    print("escrito %s" % salida.replace("\\", "/"))
    print("  %d conjuntos · %d con prompt · %d con copy" % (
        len(orden),
        sum(1 for c in orden if c["prompt_imagen"]),
        sum(1 for c in orden if c["copy"]["textos"])))
    if faltantes:
        print("  %d faltantes:" % len(faltantes))
        for f in faltantes:
            print("    - %s" % f)
    return plan


# ─────────────────────────────────────────────────────────────────────────────
# VALIDAR
# ─────────────────────────────────────────────────────────────────────────────

OFERTAS = {"1U", "2X1", "4X2", "ESCALERA", "COMBO", "SIN_PRECIO"}
NIVELES = {"1", "2", "3A", "3B", None}

# Nombres de archivo por fase. FASE 2/3 pueden salir en el esquema "fase2_lean/1"
# (gen_fase2_lean.py, 5 conjuntos x 1 concepto) o en un futuro esquema propio — la
# validacion de ESE archivo se limita a los campos raiz que gen_publicacion.py YA lee
# hoy (angulo_ganador, copy, cuenta, page_id). El array "conjuntos" de fase2_lean/1 es
# decorativo para gen_publicacion.py (arma la estructura real desde _DIM_CREATIVOS.csv)
# y su forma exacta es una deuda de doctrina abierta (HANDOFF_2026-09-09, item 1):
# no se valida acá para no blindar un esquema todavia en disputa.
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


def validar_plan_fase1(plan, validos):
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
    con_precio = sum(1 for c in plan.get("conjuntos", []) if c.get("lleva_precio"))
    if plan.get("fase") == 1 and con_precio > 3:
        problemas.append("%d conjuntos con precio; la regla de Guatemala permite max 3 (ideal 2)"
                         % con_precio)
    return problemas


def validar_plan_fase2o3(plan):
    """Solo los campos RAIZ que gen_publicacion.py ya lee para fase 2/3: angulo_ganador,
    copy, cuenta, page_id. NO valida 'conjuntos' (ver nota de NOMBRES_PLAN)."""
    problemas = []
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
    if not (plan.get("cuenta") or "").strip():
        problemas.append("sin 'cuenta' en la raiz del plan")
    if not (plan.get("page_id") or "").strip():
        problemas.append("sin 'page_id' en la raiz del plan")
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

    errores = 0
    for ruta_plan in planes:
        with io.open(ruta_plan, encoding="utf-8") as fh:
            plan = json.load(fh)
        print("\n%s" % ruta_plan.replace("\\", "/"))
        fase = plan.get("fase")
        if fase == 1:
            problemas = validar_plan_fase1(plan, validos)
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
    if "--adaptar" in sys.argv:
        adaptar(sys.argv[sys.argv.index("--adaptar") + 1])
    elif "--validar" in sys.argv:
        i = sys.argv.index("--validar")
        ruta_pedida = sys.argv[i + 1] if i + 1 < len(sys.argv) and not sys.argv[i + 1].startswith("--") else None
        sys.exit(validar(ruta_pedida))
    else:
        print(__doc__)
