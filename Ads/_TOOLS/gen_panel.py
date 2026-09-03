# -*- coding: utf-8 -*-
"""Genera VISTAS/PANEL.html — el punto de entrada UNICO de todo el sistema.

Reemplaza a Ads/_SWIPE/_HUB.html, que solo cubria las 4 vistas de creativos y dejaba
el dashboard de portafolio afuera. Ahora las SEIS vistas viven en un solo menu, agrupadas
por para-que-sirven:

    OPERACION  Panel      -> PRODUCTOS/_DASHBOARD.html    (data viva: ganancia, CPA, acciones)
               Testeos    -> PRODUCTOS/_TESTEOS.html      (que se esta midiendo y con cuanta evidencia)
    METODO     Estructura -> PRODUCTOS/_ESTRUCTURA.html   (la arquitectura de 3 fases)
               Conceptos  -> Ads/_SWIPE/_SISTEMA.html     (los blueprints y sus reglas)
    BANCO      Winners    -> Ads/_SWIPE/_WINNERS.html     (los 111 favoritos, por concepto)
               Catalogo   -> Ads/_SWIPE/_GALERIA.html     (los 597 del swipe completo)

NO duplica la logica de ninguna vista: cada generador sigue siendo el dueno de la suya y el
panel solo las compone en iframes. Por eso las rutas de imagen siguen resolviendo bien (cada
iframe tiene su propia base) y cambiar un generador se refleja aca sin tocar este archivo.

QUE NO ENTRA Y POR QUE:
    Ads/_SWIPE/_WINNERS_PORTABLE.html  -> artefacto de EXPORTACION (10 MB, imagenes en base64)
                                          para mandar por chat. No es una vista del sistema.
    Shopify_Productos/*/Contenido_*.html -> fichas de producto para pegar en Shopify. Otro negocio.

Uso:
    python Ads/_TOOLS/gen_panel.py            # solo escribe el panel
    python Ads/_TOOLS/gen_panel.py --todo     # regenera las 6 vistas y despues el panel

--todo existe por la trampa de CLAUDE.md: si el CSV cambio y la pagina no se regenero, el
operador esta leyendo data vieja. El panel muestra la antiguedad de cada vista en su boton
para que eso se vea sin tener que acordarse.
"""
import io, os, sys, subprocess, datetime

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(BASE)
SWIPE = os.path.join(BASE, "Ads", "_SWIPE")

SALIDA = "VISTAS/PANEL.html"

# (grupo, id, rotulo, subtitulo, ruta real, ruta relativa desde la raiz, generador, cwd)
VISTAS = [
    ("OPERACIÓN", "panel", "Panel", "ganancia, CPA y acciones de hoy",
     "PRODUCTOS/_DASHBOARD.html", "../PRODUCTOS/_DASHBOARD.html",
     ["python", "Ads/_TOOLS/gen_dashboard.py"], BASE),
    ("OPERACIÓN", "testeos", "Testeos", "qué se está midiendo ahora",
     "PRODUCTOS/_TESTEOS.html", "../PRODUCTOS/_TESTEOS.html",
     ["python", "Ads/_TOOLS/gen_testeos.py"], BASE),

    ("MÉTODO", "estructura", "Estructura", "las 3 fases y qué mide cada una",
     "PRODUCTOS/_ESTRUCTURA.html", "../PRODUCTOS/_ESTRUCTURA.html",
     ["python", "Ads/_TOOLS/gen_estructura.py"], BASE),
    ("MÉTODO", "conceptos", "Conceptos", "los blueprints y sus reglas",
     "Ads/_SWIPE/_SISTEMA.html", "../Ads/_SWIPE/_SISTEMA.html",
     ["python", "Ads/_TOOLS/gen_sistema.py"], BASE),

    ("BANCO", "winners", "Winners", "los 111 favoritos, por concepto",
     "Ads/_SWIPE/_WINNERS.html", "../Ads/_SWIPE/_WINNERS.html",
     ["python", "gen_winners.py"], SWIPE),
    ("BANCO", "catalogo", "Catálogo", "los 597 del swipe completo",
     "Ads/_SWIPE/_GALERIA.html", "../Ads/_SWIPE/_GALERIA.html",
     ["python", "gen_galeria.py"], SWIPE),
]


def edad(ruta):
    """Devuelve (texto, clase_css) segun hace cuanto se regenero la vista."""
    if not os.path.exists(ruta):
        return "NO EXISTE", "mala"
    horas = (datetime.datetime.now()
             - datetime.datetime.fromtimestamp(os.path.getmtime(ruta))).total_seconds() / 3600.0
    if horas < 1:
        return "al día", "ok"
    if horas < 24:
        return "hace %dh" % horas, "ok"
    dias = int(horas / 24)
    return "hace %dd" % dias, ("tibia" if dias < 7 else "mala")


def regenerar():
    """Corre los 6 generadores. Devuelve la lista de vistas que NO se regeneraron.

    El exit code no sirve de veredicto: varios de estos scripts terminan en 1 en Windows
    porque imprimen un caracter que no encodea en cp1252, aunque el HTML quedo perfecto.
    Lo unico que decide es si el mtime del archivo AVANZO.
    """
    fallidas = []
    for _g, _vid, rot, _sub, ruta, _rel, cmd, cwd in VISTAS:
        print("  regenerando %s ..." % rot)
        antes = os.path.getmtime(ruta) if os.path.exists(ruta) else 0
        r = subprocess.run(cmd, cwd=cwd, env=dict(os.environ, PYTHONIOENCODING="utf-8"))
        despues = os.path.getmtime(ruta) if os.path.exists(ruta) else 0
        if despues > antes:
            if r.returncode != 0:
                print("    (exit %d, pero el HTML se reescribio — ok)" % r.returncode)
        else:
            print("    FALLO: %s NO se regenero — la vista queda vieja" % ruta)
            fallidas.append(rot)
    return fallidas


# Mismos tokens que _DASHBOARD.html y _ESTRUCTURA.html, para que el chrome del panel y
# esas dos vistas se lean como una sola aplicacion.
CSS = """
:root{
  --ground:#F4F6FA; --surface:#FFFFFF; --line:#DDE2EC; --line-soft:#EBEEF5;
  --ink:#1A2338; --ink-2:#5A657F; --ink-3:#8892A8;
  --accent:#3B4E8C; --accent-soft:#EDF0F9;
  --good:#1F7A4D; --good-bg:#E6F2EA;
  --warn:#8A6100; --warn-bg:#F7EFDC;
  --crit:#AE3A31; --crit-bg:#F8E8E6;
  --serif:ui-serif,Georgia,'Iowan Old Style','Times New Roman',serif;
  --sans:system-ui,-apple-system,'Segoe UI',Roboto,sans-serif;
  --mono:ui-monospace,'SF Mono','Cascadia Code','Roboto Mono',monospace;
}
@media (prefers-color-scheme:dark){
  :root:not([data-theme="light"]){
    --ground:#0E1220; --surface:#161B2C; --line:#2A3145; --line-soft:#212739;
    --ink:#DFE4F0; --ink-2:#9BA5BF; --ink-3:#6E7893;
    --accent:#93A6E0; --accent-soft:#1D2438;
    --good:#5FBF8A; --good-bg:#152A20;
    --warn:#D6A63F; --warn-bg:#2B2415;
    --crit:#E0776C; --crit-bg:#2E1B19;
  }
}
:root[data-theme="dark"]{
  --ground:#0E1220; --surface:#161B2C; --line:#2A3145; --line-soft:#212739;
  --ink:#DFE4F0; --ink-2:#9BA5BF; --ink-3:#6E7893;
  --accent:#93A6E0; --accent-soft:#1D2438;
  --good:#5FBF8A; --good-bg:#152A20;
  --warn:#D6A63F; --warn-bg:#2B2415;
  --crit:#E0776C; --crit-bg:#2E1B19;
}
*{box-sizing:border-box}
html,body{margin:0;height:100%;overflow:hidden}
body{background:var(--ground);color:var(--ink);font-family:var(--sans);font-size:14px;
  line-height:1.5;-webkit-font-smoothing:antialiased;display:grid;
  grid-template-columns:224px 1fr;grid-template-rows:100%}

/* ── barra lateral ─────────────────────────────────────── */
aside{background:var(--surface);border-right:1px solid var(--line);
  display:flex;flex-direction:column;min-height:0;overflow-y:auto}
.marca{padding:16px 16px 13px;border-bottom:1px solid var(--line-soft)}
.marca h1{font-family:var(--serif);font-size:17px;margin:0;font-weight:600;letter-spacing:-.01em}
.marca .sub{color:var(--ink-3);font-size:11.5px;font-family:var(--mono);margin-top:2px}
.grupo{padding:14px 10px 4px}
.grupo .lbl{font-family:var(--mono);font-size:10px;letter-spacing:.11em;color:var(--ink-3);
  padding:0 6px 6px;font-weight:600}
button.tab{width:100%;text-align:left;background:none;border:0;border-radius:8px;
  color:var(--ink-2);font:inherit;padding:8px 10px;cursor:pointer;display:block;
  border-left:2px solid transparent}
button.tab:hover{background:var(--accent-soft);color:var(--ink)}
button.tab.on{background:var(--accent-soft);color:var(--ink);border-left-color:var(--accent)}
button.tab .rot{display:flex;align-items:center;gap:6px;font-size:13.5px;font-weight:600}
button.tab .sb{display:block;font-size:11px;color:var(--ink-3);font-weight:400;
  margin-top:1px;line-height:1.35}
.edad{font-size:9.5px;font-family:var(--mono);padding:1px 6px;border-radius:99px;font-weight:600}
.edad.ok{background:var(--good-bg);color:var(--good)}
.edad.tibia{background:var(--warn-bg);color:var(--warn)}
.edad.mala{background:var(--crit-bg);color:var(--crit)}
.pie{margin-top:auto;padding:12px 16px;border-top:1px solid var(--line-soft);
  font-size:10.5px;color:var(--ink-3);font-family:var(--mono);line-height:1.6}
.pie code{background:var(--accent-soft);padding:1px 4px;border-radius:3px;color:var(--ink-2)}
.pie .aviso{color:var(--crit);display:block;margin-top:6px}

/* ── area de la vista ──────────────────────────────────── */
main{position:relative;min-height:0;min-width:0;background:var(--ground)}
iframe{position:absolute;inset:0;width:100%;height:100%;border:0;display:none;background:var(--ground)}
iframe.on{display:block}
.fb{position:absolute;inset:0;display:none;align-items:center;justify-content:center;padding:40px}
.fb.on{display:flex}
.fb div{max-width:520px;text-align:center;color:var(--ink-2);font-size:13.5px}
.fb b{display:block;color:var(--ink);font-size:15.5px;margin-bottom:10px;font-family:var(--serif)}
.fb a{display:inline-block;margin-top:14px;background:var(--accent);color:var(--surface);
  font-weight:600;padding:9px 18px;border-radius:8px;text-decoration:none}

@media (max-width:820px){
  html,body{overflow:auto}
  body{grid-template-columns:1fr;grid-template-rows:auto 1fr;height:100%}
  aside{border-right:0;border-bottom:1px solid var(--line);overflow-x:auto}
  .grupo{padding:8px 10px 0}
  .pie{display:none}
}
"""

JS = """
var tabs = document.querySelectorAll('button.tab');
var vistas = document.querySelectorAll('iframe');
var fbs = document.querySelectorAll('.fb');

// Red de seguridad: si el navegador no deja montar un iframe local (Firefox lo bloquea en
// algunas configuraciones; Chrome no), el iframe queda en blanco para siempre y la pagina
// pareceria rota. A los 2.5 s sin haber disparado load, mostramos el enlace directo.
function vigilar(i){
  var vista = vistas[i], listo = false;
  vista.addEventListener('load', function(){ listo = true; fbs[i].classList.remove('on'); });
  setTimeout(function(){ if (!listo) fbs[i].classList.add('on'); }, 2500);
}
function ir(id){
  for (var i=0;i<tabs.length;i++){
    var on = tabs[i].dataset.v === id;
    tabs[i].classList.toggle('on', on);
    vistas[i].classList.toggle('on', on);
    if (!on) fbs[i].classList.remove('on');
    // carga diferida: la galeria de 597 solo se monta cuando se la pide
    if (on && !vistas[i].src){ vigilar(i); vistas[i].src = vistas[i].dataset.src; }
  }
  try { localStorage.setItem('panel_vista', id); } catch(e){}
}
for (var i=0;i<tabs.length;i++){
  tabs[i].addEventListener('click', function(){ ir(this.dataset.v); });
}
document.addEventListener('keydown', function(e){
  if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
  var n = parseInt(e.key, 10);
  if (n >= 1 && n <= tabs.length) ir(tabs[n-1].dataset.v);
});
var guardada = null;
try { guardada = localStorage.getItem('panel_vista'); } catch(e){}
var valida = false;
for (var i=0;i<tabs.length;i++) if (tabs[i].dataset.v === guardada) valida = true;
ir(valida ? guardada : tabs[0].dataset.v);
"""


def main():
    os.makedirs(os.path.dirname(SALIDA), exist_ok=True)
    fallidas = regenerar() if "--todo" in sys.argv else []

    menu, frames, faltan = [], [], []
    grupo_actual = None
    for _g, vid, rot, sub, ruta, rel, _cmd, _cwd in VISTAS:
        txt, cls = edad(ruta)
        if txt == "NO EXISTE":
            faltan.append(rot)
        if _g != grupo_actual:
            if grupo_actual is not None:
                menu.append("</div>")
            menu.append('<div class="grupo"><div class="lbl">%s</div>' % _g)
            grupo_actual = _g
        menu.append(
            '<button class="tab" data-v="%s"><span class="rot">%s'
            '<span class="edad %s">%s</span></span><span class="sb">%s</span></button>'
            % (vid, rot, cls, txt, sub))
        frames.append(
            '<iframe data-v="%s" data-src="%s" title="%s"></iframe>'
            '<div class="fb"><div><b>Tu navegador no montó «%s» acá dentro</b>'
            'Algunos navegadores bloquean iframes de archivos locales. La página existe y '
            'está al día — se abre igual por separado.'
            '<a href="%s" target="_blank">abrir %s en otra pestaña</a></div></div>'
            % (vid, rel, rot, rot, rel, rot))
    menu.append("</div>")

    aviso = ('<span class="aviso">falta generar: %s</span>' % ", ".join(faltan)) if faltan else ""

    html = (
        '<!doctype html><html lang="es"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>VitalCom · Panel del sistema</title><style>%s</style></head><body>'
        '<aside>'
        '<div class="marca"><h1>VitalCom</h1><div class="sub">panel del sistema</div></div>'
        '%s'
        '<div class="pie">teclas <code>1</code>–<code>%d</code> para cambiar de vista<br>'
        'regenerar todo:<br><code>python Ads/_TOOLS/gen_panel.py --todo</code>%s</div>'
        '</aside>'
        '<main>%s</main>'
        '<script>%s</script></body></html>'
        % (CSS, "".join(menu), len(VISTAS), aviso, "".join(frames), JS))

    with io.open(SALIDA, "w", encoding="utf-8") as fh:
        fh.write(html)

    print("OK -> %s  (%.1f KB)" % (SALIDA, os.path.getsize(SALIDA) / 1024.0))
    for _g, _vid, rot, _sub, ruta, _rel, _cmd, _cwd in VISTAS:
        txt, _ = edad(ruta)
        print("   %-11s %-34s %s" % (rot, ruta, txt))
    if fallidas:
        print("")
        print("ATENCION: no se regeneraron -> %s" % ", ".join(fallidas))
        sys.exit(1)


if __name__ == "__main__":
    main()
