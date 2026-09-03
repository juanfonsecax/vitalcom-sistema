# -*- coding: utf-8 -*-
"""Genera _HUB.html — el punto de entrada UNICO del sistema de creativos.

Una sola pagina con 4 pestanas:
    SISTEMA   -> Ads/_SWIPE/_SISTEMA.html  (los 4 conceptos, sus reglas y la ficha del test)
    TESTEOS   -> PRODUCTOS/_TESTEOS.html   (que se esta midiendo y con cuanta evidencia)
    WINNERS   -> Ads/_SWIPE/_WINNERS.html  (los 111 favoritos, por concepto)
    CATALOGO  -> Ads/_SWIPE/_GALERIA.html  (los 597 del swipe completo)

NO duplica la logica de las tres vistas: cada generador sigue siendo el dueno de la suya
y el hub solo las compone en iframes. Por eso las rutas de imagen de cada vista siguen
resolviendo bien (la galeria contra _IMG/, los testeos contra PRODUCTOS/) y cambiar
cualquier generador se refleja aca sin tocar este archivo.

Uso:
    python Ads/_TOOLS/gen_hub.py            # solo escribe el hub
    python Ads/_TOOLS/gen_hub.py --todo     # regenera las 4 vistas y despues el hub

--todo existe por la trampa de CLAUDE.md: si el CSV cambio y la pagina no se regenero,
el operador esta leyendo data vieja. El hub muestra la antiguedad de cada vista en su
pestana para que eso se vea sin tener que acordarse.
"""
import io, os, sys, subprocess, datetime

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(BASE)

SALIDA = "Ads/_SWIPE/_HUB.html"

# (id, rotulo, subtitulo, ruta real, ruta relativa desde _SWIPE/, generador, cwd)
# OJO: gen_galeria.py abre sus CSV por ruta relativa sin hacer chdir, asi que TIENE que
# correr parado en _SWIPE/. Los otros dos se plantan solos en la raiz.
VISTAS = [
    ("sistema",  "SISTEMA",  "los 4 conceptos y como se producen",
     "Ads/_SWIPE/_SISTEMA.html", "_SISTEMA.html",
     ["python", "Ads/_TOOLS/gen_sistema.py"], BASE),
    ("testeos",  "TESTEOS",  "que se esta midiendo ahora",
     "PRODUCTOS/_TESTEOS.html", "../../PRODUCTOS/_TESTEOS.html",
     ["python", "Ads/_TOOLS/gen_testeos.py"], BASE),
    ("winners",  "WINNERS",  "los 111 favoritos, por concepto",
     "Ads/_SWIPE/_WINNERS.html", "_WINNERS.html",
     ["python", "gen_winners.py"], os.path.join(BASE, "Ads", "_SWIPE")),
    ("catalogo", "CATALOGO", "los 597 del swipe completo",
     "Ads/_SWIPE/_GALERIA.html", "_GALERIA.html",
     ["python", "gen_galeria.py"], os.path.join(BASE, "Ads", "_SWIPE")),
]


def edad(ruta):
    """Devuelve (texto, clase_css) segun hace cuanto se regenero la vista."""
    if not os.path.exists(ruta):
        return "NO EXISTE", "mala"
    horas = (datetime.datetime.now()
             - datetime.datetime.fromtimestamp(os.path.getmtime(ruta))).total_seconds() / 3600.0
    if horas < 1:
        return "recien generada", "ok"
    if horas < 24:
        return "hace %d h" % horas, "ok"
    dias = int(horas / 24)
    return "hace %d d" % dias, ("tibia" if dias < 7 else "mala")


def regenerar():
    """Corre los 4 generadores. Devuelve la lista de vistas que NO se regeneraron.

    El exit code no sirve de veredicto: varios de estos scripts terminan en 1 en Windows
    porque imprimen un caracter que no encodea en cp1252, aunque el HTML quedo perfecto.
    Lo unico que decide es si el mtime del archivo AVANZO — si no, la vista quedo vieja
    por mas que el script "termine bien".
    """
    fallidas = []
    for vid, rot, _sub, ruta, _rel, cmd, cwd in VISTAS:
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


CSS = """
:root{--bg:#0b0d10;--pan:#12161c;--bd:#232a33;--tx:#e6edf3;--mut:#8b949e;--ac:#4f8cff}
*{box-sizing:border-box}
html,body{margin:0;height:100%;overflow:hidden}
body{background:var(--bg);color:var(--tx);
     font:14px/1.5 -apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;
     display:flex;flex-direction:column}
header{border-bottom:1px solid var(--bd);background:var(--pan);flex:0 0 auto}
.top{display:flex;align-items:baseline;gap:12px;padding:10px 18px 0}
.top h1{margin:0;font-size:15px;letter-spacing:.4px}
.top .sub{color:var(--mut);font-size:12px}
nav{display:flex;gap:4px;padding:8px 18px 0}
button.tab{background:none;border:0;border-bottom:2px solid transparent;color:var(--mut);
     font:inherit;font-size:13px;padding:8px 14px 9px;cursor:pointer;display:flex;
     flex-direction:column;gap:2px;align-items:flex-start;border-radius:6px 6px 0 0}
button.tab:hover{color:var(--tx);background:#0b0d10}
button.tab.on{color:var(--tx);border-bottom-color:var(--ac);background:#0b0d10}
button.tab b{font-size:13px;letter-spacing:.5px}
button.tab span{font-size:10.5px;color:var(--mut);font-weight:400}
.edad{font-size:10px;padding:1px 6px;border-radius:99px;margin-left:6px;vertical-align:1px}
.edad.ok{background:#0f2e1a;color:#3fb950}
.edad.tibia{background:#3d2a10;color:#e3b341}
.edad.mala{background:#3a1418;color:#f85149}
main{position:relative;flex:1 1 auto;min-height:0}
iframe{position:absolute;inset:0;width:100%;height:100%;border:0;background:var(--bg);display:none}
iframe.on{display:block}
.fb{position:absolute;inset:0;display:none;align-items:center;justify-content:center;padding:40px}
.fb.on{display:flex}
.fb div{max-width:520px;text-align:center;color:var(--mut);font-size:13px}
.fb b{display:block;color:var(--tx);font-size:15px;margin-bottom:10px}
.fb a{display:inline-block;margin-top:14px;background:var(--ac);color:#0b0d10;font-weight:600;
      padding:9px 18px;border-radius:7px;text-decoration:none}
.hint{padding:6px 18px;font-size:11px;color:var(--mut);border-top:1px solid var(--bd);
      background:var(--pan);flex:0 0 auto}
.hint code{background:#0b0d10;padding:1px 5px;border-radius:3px;color:#c9d1d9}
.hint a{color:var(--ac);text-decoration:none}
"""

JS = """
var tabs = document.querySelectorAll('button.tab');
var vistas = document.querySelectorAll('iframe');
var fbs = document.querySelectorAll('.fb');

// Red de seguridad: si el navegador no deja montar un iframe local (Firefox lo bloquea
// en algunas configuraciones; Chrome no), el iframe queda en blanco para siempre y la
// pagina pareceria rota. A los 2.5 s sin haber disparado load, mostramos el enlace directo.
function vigilar(i){
  var vista = vistas[i];
  var listo = false;
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
  try { localStorage.setItem('hub_tab', id); } catch(e){}
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
try { guardada = localStorage.getItem('hub_tab'); } catch(e){}
var valida = false;
for (var i=0;i<tabs.length;i++) if (tabs[i].dataset.v === guardada) valida = true;
ir(valida ? guardada : tabs[0].dataset.v);
"""


def main():
    fallidas = regenerar() if "--todo" in sys.argv else []

    botones, frames, faltan = [], [], []
    for vid, rot, sub, ruta, rel, _cmd, _cwd in VISTAS:
        txt, cls = edad(ruta)
        if cls == "mala" and txt == "NO EXISTE":
            faltan.append(rot)
        botones.append(
            '<button class="tab" data-v="%s"><b>%s<span class="edad %s">%s</span></b>'
            '<span>%s</span></button>' % (vid, rot, cls, txt, sub))
        frames.append(
            '<iframe data-v="%s" data-src="%s" title="%s"></iframe>'
            '<div class="fb"><div><b>Tu navegador no monto la vista %s aca dentro</b>'
            'Algunos navegadores bloquean iframes de archivos locales. La pagina existe y '
            'esta al dia — se abre igual por separado.'
            '<a href="%s" target="_blank">abrir %s en otra pestana</a></div></div>'
            % (vid, rel, rot, rot, rel, rot))

    aviso = ""
    if faltan:
        aviso = (' &nbsp;·&nbsp; <b style="color:#f85149">falta generar: %s</b>'
                 % ", ".join(faltan))

    html = (
        '<!doctype html><html lang="es"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>HUB DE CREATIVOS</title><style>%s</style></head><body>'
        '<header>'
        '<div class="top"><h1>HUB DE CREATIVOS</h1>'
        '<div class="sub">testeos, favoritos y swipe completo en una sola pagina</div></div>'
        '<nav>%s</nav></header>'
        '<main>%s</main>'
        '<div class="hint">teclas <code>1</code> <code>2</code> <code>3</code> <code>4</code> para cambiar '
        'de vista &nbsp;·&nbsp; el hub debe vivir en <code>Ads/_SWIPE/</code> junto a '
        '<code>_IMG/</code> &nbsp;·&nbsp; regenerar todo: '
        '<code>python Ads/_TOOLS/gen_hub.py --todo</code>%s</div>'
        '<script>%s</script></body></html>'
        % (CSS, "".join(botones), "".join(frames), aviso, JS))

    with io.open(SALIDA, "w", encoding="utf-8") as fh:
        fh.write(html)

    print("OK -> %s  (%.1f KB)" % (SALIDA, os.path.getsize(SALIDA) / 1024.0))
    for vid, rot, _sub, ruta, _rel, _cmd, _cwd in VISTAS:
        txt, _ = edad(ruta)
        print("   %-9s %-34s %s" % (rot, ruta, txt))
    if fallidas:
        print("")
        print("ATENCION: no se regeneraron -> %s" % ", ".join(fallidas))
        sys.exit(1)


if __name__ == "__main__":
    main()
