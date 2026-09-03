# -*- coding: utf-8 -*-
"""Genera _SISTEMA.html — la vista visual del sistema de creativos.

LEE los JSON de Ads/_SWIPE/_BLUEPRINTS/ y los renderiza. NO duplica su contenido:
si cambias un blueprint o la ficha, se regenera y la pagina lo refleja. Los numeros
y las reglas viven en el JSON; esta pagina solo los muestra.

Uso:
    python Ads/_TOOLS/gen_sistema.py            # imagenes por ruta relativa
    python Ads/_TOOLS/gen_sistema.py --liviano  # idem (por defecto embebe en base64)
"""
import json, io, os, sys, base64, glob, datetime

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(BASE)

BP_DIR = "Ads/_SWIPE/_BLUEPRINTS"
BANCO = "Ads/_SWIPE/_BANCO_CREATIVOS"
SALIDA = "Ads/_SWIPE/_SISTEMA.html"
PORTABLE = "--liviano" not in sys.argv

ORDEN = ["A_autoridad_medica", "B_editorial_limpio",
         "C_dolor_maximalista", "D_transformacion_temporal"]
NOMBRE = {
    "A_autoridad_medica": ("A", "AUTORIDAD MEDICA", "#4f8cff",
                           "Vende credibilidad institucional. El producto es casi secundario: "
                           "el vehiculo es la figura de autoridad y la evidencia visual."),
    "B_editorial_limpio": ("B", "EDITORIAL LIMPIO", "#3fb950",
                           "Vende calidad premium natural. No grita. La persuasion viene del "
                           "orden y del espacio en blanco."),
    "C_dolor_maximalista": ("C", "DOLOR MAXIMALISTA", "#f85149",
                            "Vende alivio de un dolor intenso. El mas agresivo y el mas denso. "
                            "Su motor es la identificacion con sintomas especificos."),
    "D_transformacion_temporal": ("D", "TRANSFORMACION TEMPORAL", "#d29922",
                                  "Vende resultado proyectado en el tiempo. Su elemento unico "
                                  "es la linea de tiempo del tope."),
}
BRAZO_T01 = {"A_autoridad_medica": "A", "B_editorial_limpio": "B",
             "C_dolor_maximalista": "C", "D_transformacion_temporal": "D"}


def img_src(rel):
    p = os.path.join(BANCO, rel)
    if not os.path.exists(p):
        return None
    if not PORTABLE:
        return "_BANCO_CREATIVOS/" + rel.replace("\\", "/")
    with open(p, "rb") as f:
        return "data:image/jpeg;base64," + base64.b64encode(f.read()).decode("ascii")


def esc(s):
    return (unicode(s) if str is bytes else str(s)).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def carga_json(p):
    return json.load(io.open(p, encoding="utf-8"))


def card_concepto(bp):
    letra, nombre, color, lectura = NOMBRE[bp["id"]]
    src = img_src(bp["referencia_visual"])
    img = ('<img src="%s" alt="referencia %s">' % (src, letra)) if src else \
          '<div class="sinimg">referencia no encontrada</div>'
    zonas = bp.get("zonas", {})
    libre = bp.get("espacio_libre_objetivo", "?")
    try:
        pct = int(str(libre).replace("%", ""))
    except ValueError:
        pct = 0
    reglas = "".join("<li>%s</li>" % esc(r) for r in bp.get("reglas_duras", []))
    lista_zonas = "".join(
        '<span class="z">%s</span>' % esc(k) for k in zonas.keys())
    apl = bp.get("aplicabilidad")
    aviso = ""
    if apl:
        aviso = ('<div class="aviso"><b>No usar si:</b> %s</div>'
                 % esc(apl.get("no_usar_si", "")))
    return (
        '<article class="cc" style="--c:%s">'
        '<header><span class="letra">%s</span>'
        '<div><h3>%s</h3><div class="ids"><code>%s</code> · <code>%s</code>%s</div></div>'
        '<span class="brazo">brazo %s de T01</span></header>'
        '<div class="cuerpo"><div class="ref">%s<div class="pie">referencia validada</div></div>'
        '<div class="det">'
        '<p class="lect">%s</p>'
        '%s'
        '<div class="metas">'
        '<div class="meta"><span>densidad</span><b>%s</b></div>'
        '<div class="meta"><span>espacio libre</span><b>%s</b></div>'
        '<div class="meta"><span>formato nativo</span><b>%s</b></div>'
        '<div class="meta"><span>zonas</span><b>%d</b></div>'
        '</div>'
        '<div class="barra"><div class="lleno" style="width:%d%%"></div>'
        '<div class="barlab">%s del frame respira</div></div>'
        '<details><summary>%d zonas del layout</summary><div class="zonas">%s</div></details>'
        '<details><summary>%d reglas duras</summary><ul class="reglas">%s</ul></details>'
        '</div></div></article>'
        % (color, letra, nombre, bp["id"], bp["concepto_key"],
           (" · <code>%s</code>" % bp["variante"]) if bp.get("variante") else "",
           BRAZO_T01[bp["id"]], img, esc(lectura), aviso,
           esc(bp.get("densidad", "?")), esc(libre), esc(bp.get("formato", "?")),
           len(zonas), 100 - pct, esc(libre),
           len(zonas), lista_zonas, len(bp.get("reglas_duras", [])), reglas))


def bloque_ficha(f):
    ov = f.get("_OVERRIDES_TEST_T01", {})
    pd = f.get("producto_data", {})
    filas = [
        ("producto", "%s · %s" % (f.get("producto"), f.get("marca"))),
        ("costo proveedor", "Q%s" % f.get("costo_proveedor_q")),
        ("angulo FIJO", "ME DIJERON QUE NO TIENE CURA"),
        ("hook FIJO", ov.get("hook", "")),
        ("precio FIJO", ov.get("bloque_precio", "")),
        ("formato FIJO", ov.get("formato", "")),
        ("garantia", "%s dias" % f.get("oferta", {}).get("dias_garantia")),
        ("pagina", ov.get("pagina", "")),
        ("paleta", "%s / %s" % (pd.get("empaque_color_dominante"),
                                 pd.get("empaque_color_secundario"))),
        ("sellos", " · ".join(f.get("contenido", {}).get("sellos", [])) or "ninguno"),
    ]
    tabla = "".join('<tr><th>%s</th><td>%s</td></tr>' % (esc(k), esc(v)) for k, v in filas)
    ben = "".join("<li>%s</li>" % esc(b) for b in f.get("contenido", {}).get("beneficios", []))
    notas = f.get("_NOTAS_DE_MARCA", {})
    nl = "".join('<div class="nota"><b>%s</b>%s</div>' % (esc(k), esc(v))
                 for k, v in notas.items())
    return (
        '<div class="ficha"><div><table>%s</table></div>'
        '<div><h4>Los 4 beneficios (iguales en los 4 brazos, mismo orden)</h4>'
        '<ol class="ben">%s</ol>'
        '<div class="degr"><b>Brazo D corre DEGRADADO.</b> %s</div>'
        '</div></div><div class="notas">%s</div>'
        % (tabla, ben, esc(ov.get("brazo_D", "")), nl))


CSS = """
:root{--bg:#0b0d10;--pan:#12161c;--bd:#232a33;--tx:#e6edf3;--mut:#8b949e;--ac:#4f8cff}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--tx);
 font:14px/1.6 -apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;padding:0 0 60px}
.wrap{max-width:1180px;margin:0 auto;padding:0 20px}
h1{font-size:20px;margin:26px 0 4px;letter-spacing:.4px}
.sub{color:var(--mut);font-size:13px;margin-bottom:26px}
h2{font-size:14px;letter-spacing:1.2px;color:var(--mut);text-transform:uppercase;
 margin:38px 0 14px;padding-bottom:8px;border-bottom:1px solid var(--bd)}
.flujo{display:flex;flex-wrap:wrap;gap:10px;align-items:stretch;margin-bottom:8px}
.capa{flex:1 1 240px;background:var(--pan);border:1px solid var(--bd);border-radius:10px;padding:14px 16px}
.capa b{display:block;font-size:12px;letter-spacing:1px;color:var(--ac);margin-bottom:6px}
.capa p{margin:0;font-size:12.5px;color:var(--mut)}
.regla{background:#1a1410;border:1px solid #3d2a10;border-left:3px solid #e3b341;
 border-radius:8px;padding:12px 16px;margin:14px 0;font-size:13px}
.cc{background:var(--pan);border:1px solid var(--bd);border-left:3px solid var(--c);
 border-radius:12px;margin-bottom:16px;overflow:hidden}
.cc header{display:flex;align-items:center;gap:14px;padding:14px 18px;border-bottom:1px solid var(--bd)}
.letra{width:34px;height:34px;flex:0 0 34px;border-radius:9px;background:var(--c);color:#0b0d10;
 font-weight:800;font-size:17px;display:flex;align-items:center;justify-content:center}
.cc h3{margin:0;font-size:15px;letter-spacing:.6px}
.ids{font-size:11px;color:var(--mut);margin-top:2px}
.ids code{background:#0b0d10;padding:1px 6px;border-radius:4px;color:#c9d1d9}
.brazo{margin-left:auto;font-size:11px;color:var(--c);border:1px solid var(--c);
 border-radius:99px;padding:3px 10px;white-space:nowrap}
.cuerpo{display:flex;gap:18px;padding:16px 18px;flex-wrap:wrap}
.ref{flex:0 0 230px}
.ref img{width:100%;border-radius:8px;display:block;border:1px solid var(--bd)}
.sinimg{padding:40px 10px;text-align:center;color:var(--mut);border:1px dashed var(--bd);border-radius:8px}
.pie{font-size:10.5px;color:var(--mut);text-align:center;margin-top:6px}
.det{flex:1 1 380px;min-width:280px}
.lect{margin:0 0 12px;font-size:13.5px}
.aviso{background:#3a1418;border:1px solid #5a2027;border-radius:7px;padding:9px 12px;
 font-size:12.5px;margin-bottom:12px}
.metas{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:12px}
.meta{background:#0b0d10;border:1px solid var(--bd);border-radius:7px;padding:6px 11px}
.meta span{display:block;font-size:10px;color:var(--mut);text-transform:uppercase;letter-spacing:.6px}
.meta b{font-size:13px}
.barra{position:relative;height:22px;background:#0b0d10;border:1px solid var(--bd);
 border-radius:6px;overflow:hidden;margin-bottom:12px}
.lleno{height:100%;background:var(--c);opacity:.32}
.barlab{position:absolute;inset:0;display:flex;align-items:center;padding-left:10px;
 font-size:11px;color:var(--mut)}
details{border-top:1px solid var(--bd);padding-top:8px;margin-top:8px}
summary{cursor:pointer;font-size:12px;color:var(--mut);list-style:none}
summary::-webkit-details-marker{display:none}
summary:before{content:"▸ ";color:var(--c)}
details[open] summary:before{content:"▾ "}
.zonas{display:flex;flex-wrap:wrap;gap:5px;margin-top:9px}
.z{background:#0b0d10;border:1px solid var(--bd);border-radius:5px;padding:3px 8px;
 font-size:11px;font-family:ui-monospace,Consolas,monospace;color:#c9d1d9}
.reglas{margin:9px 0 0;padding-left:18px;font-size:12.5px;color:var(--mut)}
.reglas li{margin-bottom:4px}
.ficha{display:flex;gap:20px;flex-wrap:wrap;background:var(--pan);border:1px solid var(--bd);
 border-radius:12px;padding:18px}
.ficha>div{flex:1 1 340px;min-width:300px}
table{width:100%;border-collapse:collapse;font-size:13px}
th{text-align:left;color:var(--mut);font-weight:400;padding:6px 10px 6px 0;
 vertical-align:top;white-space:nowrap;width:1%}
td{padding:6px 0;border-bottom:1px solid var(--bd)}
h4{font-size:12px;color:var(--mut);text-transform:uppercase;letter-spacing:.8px;margin:0 0 10px}
.ben{margin:0 0 16px;padding-left:20px;font-size:13px}
.ben li{margin-bottom:5px}
.degr{background:#1a1410;border:1px solid #3d2a10;border-radius:8px;padding:11px 13px;font-size:12.5px}
.notas{margin-top:12px;display:flex;flex-wrap:wrap;gap:10px}
.nota{flex:1 1 260px;background:var(--pan);border:1px solid var(--bd);border-radius:9px;
 padding:11px 13px;font-size:12.5px;color:var(--mut)}
.nota b{display:block;color:var(--tx);text-transform:uppercase;font-size:10.5px;
 letter-spacing:.8px;margin-bottom:4px}
.fijo{display:flex;flex-wrap:wrap;gap:10px;margin-bottom:8px}
.fj{background:#0f2e1a;border:1px solid #1c5030;color:#3fb950;border-radius:7px;
 padding:7px 12px;font-size:12px}
.vr{background:#3a1418;border:1px solid #5a2027;color:#f85149;border-radius:7px;
 padding:7px 12px;font-size:12px}
.foot{color:var(--mut);font-size:11.5px;margin-top:30px;border-top:1px solid var(--bd);padding-top:12px}
code.inl{background:#0b0d10;padding:1px 5px;border-radius:3px;font-size:12px}
"""


def main():
    bps = [carga_json(os.path.join(BP_DIR, "blueprint_%s.json" % k)) for k in ORDEN]
    ficha = carga_json(os.path.join(BP_DIR, "ficha_tinnidrop.json"))

    cards = "".join(card_concepto(b) for b in bps)

    html = (
        '<!doctype html><html lang="es"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>SISTEMA DE CREATIVOS</title><style>%s</style></head><body><div class="wrap">'
        '<h1>SISTEMA DE CREATIVOS</h1>'
        '<div class="sub">Vista generada desde <code class="inl">Ads/_SWIPE/_BLUEPRINTS/</code>. '
        'Los blueprints son la fuente; esta pagina solo los muestra. Regenerada %s.</div>'

        '<h2>Como corre</h2>'
        '<div class="flujo">'
        '<div class="capa"><b>CAPA 1 · BLUEPRINTS</b><p>4 JSON fijos. La ESTRUCTURA de cada '
        'concepto ganador, con el contenido en variables. No se editan.</p></div>'
        '<div class="capa"><b>CAPA 2 · LLENADOR</b><p>blueprint + ficha del producto &rarr; el '
        'mismo JSON con las variables resueltas. No disena. Si falta contenido devuelve '
        '<code class="inl">_faltantes</code> en vez de inventar.</p></div>'
        '<div class="capa"><b>CAPA 3 · RENDER</b><p>Imagenes con rol declarado + envoltorio fijo '
        '+ el JSON pegado literal. IMAGEN_1 = layout · IMAGEN_2 = producto · IMAGEN_3 = identidad.</p></div>'
        '</div>'
        '<div class="regla"><b>Regla de oro:</b> el LLM nunca escribe el prompt de imagen — llena '
        'variables. Si el prompt sale como prosa descriptiva ("una imagen publicitaria con fondo '
        'amarillo donde aparece un doctor..."), esta mal: ese es el modo que falla, porque el '
        'modelo no distingue estructura de contenido y copia lo literal perdiendo la jerarquia.</div>'

        '<h2>Los 4 conceptos</h2>%s'

        '<h2>El test T01 — que se fija y que varia</h2>'
        '<div class="fijo">'
        '<span class="vr">VARIA &nbsp;·&nbsp; el dispositivo visual</span>'
        '<span class="fj">FIJO · angulo</span><span class="fj">FIJO · hook</span>'
        '<span class="fj">FIJO · 4 beneficios</span><span class="fj">FIJO · precio</span>'
        '<span class="fj">FIJO · garantia</span><span class="fj">FIJO · formato 4:5</span>'
        '<span class="fj">FIJO · pagina</span>'
        '</div>'
        '<div class="regla">Cada blueprint trae su propia arquitectura de precio '
        '(A: 1 precio · B: precio + tachado · C: 2 tiers · D: 3 tiers) y su propio formato 1:1. '
        'En T01 <b>se anulan las dos cosas por override</b>: si no, los brazos difieren en mas de '
        'una variable y el ganador no es atribuible al concepto. Los overrides viven en la '
        '<b>ficha</b>, nunca en el blueprint.</div>'
        '%s'

        '<h2>Como se lee el resultado</h2>'
        '<div class="regla">Se agrega por <code class="inl">concepto_key</code>, nunca por '
        'conjunto. Las replicas <code class="inl">R[N]</code> se suman, no se comparan. '
        'La conversacion sirve para CORTAR, nunca para CORONAR. Umbrales: <b>10</b> ventas por '
        'brazo detectan un 3x · <b>25</b> un 2x · <b>80</b> un 1.5x. El medidor esta en la '
        'pestana TESTEOS.</div>'

        '<div class="foot">Blueprints: <code class="inl">Ads/_SWIPE/_BLUEPRINTS/</code> &nbsp;·&nbsp; '
        'metodo completo en <code class="inl">_LEEME.md</code> &nbsp;·&nbsp; '
        'regenerar: <code class="inl">python Ads/_TOOLS/gen_sistema.py</code></div>'
        '</div></body></html>'
        % (CSS, datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
           cards, bloque_ficha(ficha)))

    with io.open(SALIDA, "w", encoding="utf-8") as f:
        f.write(html)
    print("OK -> %s  (%.1f KB, %d conceptos)"
          % (SALIDA, os.path.getsize(SALIDA) / 1024.0, len(bps)))


if __name__ == "__main__":
    main()
