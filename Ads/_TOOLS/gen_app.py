# -*- coding: utf-8 -*-
"""gen_app.py — arma VISTAS/APP.html, la aplicacion unificada del sistema.

QUE HACE
Es el unico comando de la capa de vistas. Lee VISTAS/_MANIFIESTO.json (el sistema
declarado), verifica contra el disco que cada fuente exista y cuando se produjo,
lee PRODUCTOS/_LANZADOR.json (los productos) y escribe:

    VISTAS/_ESTADO.json   el manifiesto + el estado real de cada vista
    VISTAS/APP.html       la app: una barra lateral, todas las vistas adentro
    VISTAS/PANEL.html     la puerta vieja, redirige a APP.html

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
import sys
import json
import datetime
import subprocess

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(BASE)
sys.path.insert(0, os.path.join(BASE, "Ads", "_TOOLS"))

MANIFIESTO = "VISTAS/_MANIFIESTO.json"
LANZADOR_JSON = "PRODUCTOS/_LANZADOR.json"
GEN_LANZADOR = "Ads/_TOOLS/gen_lanzador.py"
DECISIONES_JSON = "PRODUCTOS/_DECISIONES.json"
GEN_DECISIONES = "Ads/_TOOLS/decidir.py"
CANONICOS_DIR = "Ads/_SWIPE/_BLUEPRINTS/CANONICOS"

HOY = datetime.date.today()

CAMPOS_VISTA = {"id", "seccion", "rotulo", "sub", "tipo", "render", "fuente",
                "genera", "dueno", "caduca", "pesada"}



# ─────────────────────────────────────────────────────────────────────────────
# 1 · EL MANIFIESTO, VALIDADO
# ─────────────────────────────────────────────────────────────────────────────

def leer_manifiesto():
    if not os.path.exists(MANIFIESTO):
        raise SystemExit("no existe %s — es el archivo que declara el sistema." % MANIFIESTO)
    with io.open(MANIFIESTO, encoding="utf-8") as fh:
        m = json.load(fh)

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
        raise SystemExit("MANIFIESTO INVALIDO — %s\n  · %s"
                         % (MANIFIESTO, "\n  · ".join(problemas)))

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

    if problemas:
        raise SystemExit("MANIFIESTO INVALIDO — %s\n  · %s"
                         % (MANIFIESTO, "\n  · ".join(problemas)))
    return m


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
        correr("python %s" % GEN_DECISIONES)
    if not os.path.exists(DECISIONES_JSON):
        return {
            "generado": HOY.isoformat(),
            "motor": "decidir v3 (Síntesis: Intervalos de Credibilidad Bayesiana + Riesgo Asimétrico)",
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
    from app_html import HTML, ALIAS
    app = estado["app"]
    if not os.path.isdir("VISTAS"):
        os.makedirs("VISTAS")

    with io.open(app["estado"], "w", encoding="utf-8") as fh:
        fh.write(json.dumps(estado, ensure_ascii=False, indent=2))
    print("escrito %s" % app["estado"])

    with io.open(app["salida"], "w", encoding="utf-8") as fh:
        fh.write(HTML(estado, lanzador, decisiones, blueprints))
    print("escrito %s" % app["salida"])

    for alias in app.get("alias", []):
        with io.open(alias, "w", encoding="utf-8") as fh:
            fh.write(ALIAS(estado))
        print("escrito %s (redirige a la app)" % alias)


def main():
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

