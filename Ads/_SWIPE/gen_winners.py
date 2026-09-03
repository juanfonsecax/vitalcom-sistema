# -*- coding: utf-8 -*-
"""Genera _WINNERS.html — SOLO los favoritos del operador, ya clasificados por concepto.

Lee  _CLASIF_FAVORITOS.csv  (111 favoritos con concepto_final)
     _ETIQUETAS_MANUALES.csv (el export crudo de la galeria, para el ad_archive_id)
Escribe _WINNERS.html en la misma carpeta (rutas de imagen relativas a _IMG/).

Abrir con DOBLE CLIC desde la carpeta. No depende de localStorage: los favoritos
estan horneados en el HTML.
"""
import csv, io, json, os, sys, base64, datetime
from collections import Counter, defaultdict

BASE = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE)

# --portable : incrusta las imagenes en base64 para que el HTML funcione en CUALQUIER
# carpeta (mandarlo por chat, copiarlo a otra maquina, mail). Pesa ~10 MB en vez de 77 KB.
# Sin la bandera, las imagenes van por ruta relativa a _IMG/ y el archivo DEBE vivir en _SWIPE/.
PORTABLE = "--portable" in sys.argv
SALIDA = "_WINNERS_PORTABLE.html" if PORTABLE else "_WINNERS.html"

_cache = {}
def img_src(p):
    if not PORTABLE:
        return p
    if p not in _cache:
        with open(p, "rb") as f:
            _cache[p] = "data:image/jpeg;base64," + base64.b64encode(f.read()).decode("ascii")
    return _cache[p]

CONCEPTOS = [
    ("C2_BENEFICIOS",    "Beneficios",     "#4f8cff", "pregunta de dolor + columna de iconos"),
    ("C4_TRANSFORMACION","Transformacion", "#a371f7", "antes / despues"),
    ("C5_PRUEBA",        "Prueba",         "#3fb950", "foto cruda, chat, captura, testimonio, unboxing"),
    ("C8_PROGRESION",    "Progresion",     "#f0883e", "3-4 estados en el tiempo"),
    ("C7_DESEO",         "Deseo",          "#db61a2", "el cuerpo deseado, no el enfermo"),
    ("C3_SINTOMA",       "Sintoma",        "#e5534b", "la zona del cuerpo que duele"),
    ("C1_OFERTA",        "Oferta",         "#d29922", "el precio ES el creativo"),
    ("C9_COMPARACION",   "Comparacion",    "#39c5cf", "dos columnas, malo vs bueno"),
]
COLOR = {k: c for k, _, c, _ in CONCEPTOS}
NOMBRE = {k: n for k, n, _, _ in CONCEPTOS}
DESC = {k: d for k, _, _, d in CONCEPTOS}

# La cosecha guardo los nombres sin acentos y de forma inconsistente: "Doa Oferta" y
# "Dona Oferta" son la MISMA pagina partida en dos, lo que subestimaba su repeticion.
# Detectado con difflib (unico par con similitud >= 0.80 en los 111).
# Regla 21 del orquestador: un nombre, una tienda. Si aparece otra grafia, se agrega aca.
ALIAS = {
    "Doa Oferta":                   u"Doña Oferta",
    "Dona Oferta":                  u"Doña Oferta",
    "El Ofertn Guatemala":          u"El Ofertón Guatemala",
    "Flor Expres GT":               u"Flor Exprés GT",
    "Rincon de las Ventas Onlin":   u"Rincón de las Ventas Online",
    "Rincon de las Ventas Online":  u"Rincón de las Ventas Online",
    "Dra.Dra. Sofa Alejandra Mo":   u"Dra. Sofía Alejandra Morales",
    "Dra Sofia Alejandra Morales":  u"Dra. Sofía Alejandra Morales",
    "Andromeda Market":             u"Andrómeda Market",
    "Rincon de las Ventas":         u"Rincón de las Ventas Online",
}

# ---------- datos ----------
clas = list(csv.DictReader(io.open("_CLASIF_FAVORITOS.csv", encoding="utf-8")))
raw = {r["archivo"]: r for r in csv.DictReader(io.open("_ETIQUETAS_MANUALES.csv", encoding="utf-8"))}

items = []
for r in clas:
    a = r["archivo"]
    src = raw.get(a, {})
    items.append({
        "arch": a,
        "aid": src.get("ad_archive_id", ""),
        "anun": ALIAS.get(r["anunciante"], r["anunciante"]),
        "cpt": r["concepto_final"],
        "crudo": r["concepto_crudo"],
        "d": int(r["dias"]),
        "rep": int(r["replicas"]),
    })

# tiendas que repiten en la seleccion del operador
rep_tiendas = Counter(i["anun"] for i in items)
tiendas_rank = sorted(rep_tiendas.items(), key=lambda kv: (-kv[1], kv[0]))
REPETIDAS = {t for t, n in tiendas_rank if n >= 2}

for i in items:
    i["repite"] = 1 if i["anun"] in REPETIDAS else 0
    i["nt"] = rep_tiendas[i["anun"]]

# orden por defecto: concepto (por volumen) -> tienda que repite -> replicas -> dias
orden_cpt = {k: n for n, (k, _, _, _) in enumerate(CONCEPTOS)}
items.sort(key=lambda i: (orden_cpt.get(i["cpt"], 99), -i["nt"], -i["rep"], -i["d"]))

por_cpt = Counter(i["cpt"] for i in items)

# ---------- html ----------
def card(i):
    badges = []
    if i["rep"] >= 2:
        badges.append('<span class="b b-rep">x%d replicas</span>' % i["rep"])
    if i["d"] >= 21:
        badges.append('<span class="b b-old">%dd</span>' % i["d"])
    else:
        badges.append('<span class="b">%dd</span>' % i["d"])
    if i["repite"]:
        badges.append('<span class="b b-store">tienda x%d</span>' % i["nt"])
    lnk = ""
    if i["aid"]:
        lnk = ('<a class="lk" target="_blank" rel="noopener" '
               'href="https://www.facebook.com/ads/library/?id=%s">ver en Ad Library &#8599;</a>' % i["aid"])
    return (
        '<figure class="c" data-cpt="%s" data-anun="%s" data-rep="%d" data-d="%d" data-store="%d">'
        '<div class="ph"><img loading="lazy" src="%s" alt=""></div>'
        '<figcaption>'
        '<div class="cpt" style="--k:%s">%s</div>'
        '<div class="an">%s</div>'
        '<div class="bs">%s</div>'
        '<div class="nt">%s</div>'
        '%s'
        '</figcaption></figure>'
    ) % (i["cpt"], i["anun"].replace('"', "&quot;"), i["rep"], i["d"], i["repite"],
         img_src(i["arch"]), COLOR.get(i["cpt"], "#8b98a5"), NOMBRE.get(i["cpt"], i["cpt"]),
         i["anun"], "".join(badges), i["crudo"].replace("_", " ").lower(), lnk)


chips = "".join(
    '<button class="ch" data-f="%s" style="--k:%s"><i></i>%s <b>%d</b></button>'
    % (k, COLOR[k], NOMBRE[k], por_cpt.get(k, 0))
    for k, _, _, _ in CONCEPTOS if por_cpt.get(k, 0)
)

tiendas_html = "".join(
    '<button class="tb%s" data-t="%s">%s <b>%d</b></button>'
    % (" hot" if n >= 4 else "", t.replace('"', "&quot;"), t, n)
    for t, n in tiendas_rank if n >= 2
)

leyenda = "".join(
    '<li><span class="dot" style="background:%s"></span><b>%s</b> — %s</li>' % (c, n, d)
    for k, n, c, d in CONCEPTOS if por_cpt.get(k, 0)
)

n_rep = sum(1 for i in items if i["rep"] >= 2)
n_old = sum(1 for i in items if i["d"] >= 21)
n_tiendas = len(rep_tiendas)

HTML = u"""<!doctype html><meta charset="utf-8"><title>WINNERS - seleccion de Juan</title>
<style>
:root{--bg:#0e1116;--fg:#e6edf3;--mut:#8b98a5;--card:#161b22;--bd:#30363d;--sel:#4f8cff}
*{box-sizing:border-box}
body{background:var(--bg);color:var(--fg);font:14px/1.45 system-ui,-apple-system,sans-serif;margin:0;padding:20px 22px 60px}
h1{font-size:21px;margin:0 0 4px;letter-spacing:-.2px}
.sub{color:var(--mut);font-size:13px;margin-bottom:16px}
.sub b{color:var(--fg)}
.bar{position:sticky;top:0;background:linear-gradient(var(--bg) 78%,transparent);padding:12px 0 14px;z-index:20;margin-bottom:6px}
.row{display:flex;flex-wrap:wrap;gap:7px;align-items:center;margin-bottom:9px}
.lbl{color:var(--mut);font-size:11px;text-transform:uppercase;letter-spacing:.6px;width:100%;margin:2px 0 -2px}
.ch{background:var(--card);color:var(--fg);border:1px solid var(--bd);border-radius:20px;padding:6px 13px;cursor:pointer;font-size:13px;display:flex;align-items:center;gap:7px;transition:.12s}
.ch i{width:9px;height:9px;border-radius:50%;background:var(--k);flex:none}
.ch b{color:var(--mut);font-weight:600}
.ch:hover{border-color:var(--k)}
.ch.on{background:var(--k);color:#0b0d10;border-color:var(--k);font-weight:600}
.ch.on b{color:#0b0d10;opacity:.65}
.tb{background:transparent;color:var(--mut);border:1px solid var(--bd);border-radius:6px;padding:4px 9px;cursor:pointer;font-size:12px}
.tb b{color:var(--fg)}
.tb.hot{border-color:#d29922;color:#e3b341}
.tb:hover{border-color:var(--sel);color:var(--fg)}
.tb.on{background:var(--sel);color:#0b0d10;border-color:var(--sel)}
.tb.on b{color:#0b0d10}
.tg{background:var(--card);color:var(--fg);border:1px solid var(--bd);border-radius:6px;padding:5px 11px;cursor:pointer;font-size:12.5px}
.tg.on{background:#238636;border-color:#238636;color:#fff}
select{background:var(--card);color:var(--fg);border:1px solid var(--bd);border-radius:6px;padding:5px 9px;font-size:12.5px}
.g{display:grid;grid-template-columns:repeat(auto-fill,minmax(228px,1fr));gap:14px}
.c{margin:0;background:var(--card);border:1px solid var(--bd);border-radius:11px;overflow:hidden;display:flex;flex-direction:column}
.c.hid{display:none}
.ph{background:#0b0d10;display:flex;align-items:center;justify-content:center;min-height:150px}
.ph img{width:100%;height:auto;display:block;cursor:zoom-in}
figcaption{padding:9px 11px 11px;font-size:12px}
.cpt{color:var(--k);font-weight:700;font-size:11px;text-transform:uppercase;letter-spacing:.7px;margin-bottom:3px}
.an{font-weight:600;margin-bottom:6px;line-height:1.25}
.bs{display:flex;flex-wrap:wrap;gap:4px;margin-bottom:5px}
.b{background:#21262d;color:var(--mut);border-radius:4px;padding:1px 6px;font-size:10.5px}
.b-rep{background:#3d2a10;color:#e3b341}
.b-old{background:#12291c;color:#5fd47f}
.b-store{background:#1c2331;color:#79a6ff}
.nt{color:var(--mut);font-size:11px;line-height:1.35}
.lk{display:inline-block;margin-top:6px;color:var(--sel);text-decoration:none;font-size:11px}
.lk:hover{text-decoration:underline}
.leg{background:var(--card);border:1px solid var(--bd);border-radius:9px;padding:11px 15px;margin-bottom:16px}
.leg ul{margin:0;padding:0;list-style:none;columns:2;column-gap:26px}
.leg li{font-size:12px;color:var(--mut);margin-bottom:5px;break-inside:avoid}
.leg b{color:var(--fg)}
.dot{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:7px}
#cnt{color:var(--mut);font-size:12.5px;margin-left:auto}
#lb{position:fixed;inset:0;background:rgba(0,0,0,.93);display:none;align-items:center;justify-content:center;z-index:99;cursor:zoom-out}
#lb img{max-width:94vw;max-height:94vh}
@media(max-width:640px){.leg ul{columns:1}}
</style>

<h1>WINNERS &#9733; seleccion de Juan</h1>
<div class="sub"><b>__N__</b> creativos favoritos &middot; <b>__NT__</b> tiendas &middot; <b>__NREP__</b> con replicas &middot; <b>__NOLD__</b> con 21+ dias corriendo
&nbsp;|&nbsp; clasificados en <b>__NC__</b> conceptos &middot; __F__</div>

<div class="leg"><ul>__LEG__</ul></div>

<div class="bar">
 <div class="row"><span class="lbl">Concepto</span>__CHIPS__
  <button class="tg" id="all">ver todos</button><span id="cnt"></span></div>
 <div class="row"><span class="lbl">Tiendas que repetis en tus favoritos</span>__TIENDAS__</div>
 <div class="row">
  <button class="tg" id="onlyrep">solo con replicas</button>
  <button class="tg" id="onlyold">solo 21+ dias</button>
  <button class="tg" id="onlystore">solo tiendas que repiten</button>
  <select id="ord">
   <option value="cpt">ordenar: por concepto</option>
   <option value="rep">ordenar: mas replicas</option>
   <option value="d">ordenar: mas dias corriendo</option>
   <option value="an">ordenar: por tienda</option>
  </select>
 </div>
</div>

<div class="g" id="g">__CARDS__</div>
<div id="lb"><img></div>

<script>
var G=document.getElementById('g');
var C=[].slice.call(document.querySelectorAll('.c'));
var fc=null, ft=null, onlyrep=false, onlyold=false, onlystore=false;

function ap(){
 var n=0;
 C.forEach(function(c){
  var ok=true;
  if(fc && c.dataset.cpt!==fc) ok=false;
  if(ft && c.dataset.anun!==ft) ok=false;
  if(onlyrep && +c.dataset.rep<2) ok=false;
  if(onlyold && +c.dataset.d<21) ok=false;
  if(onlystore && c.dataset.store!=='1') ok=false;
  c.classList.toggle('hid',!ok); if(ok)n++;
 });
 document.getElementById('cnt').textContent=n+' de '+C.length+' visibles';
}
document.querySelectorAll('.ch').forEach(function(b){
 b.onclick=function(){
  var v=b.dataset.f;
  fc=(fc===v)?null:v;
  document.querySelectorAll('.ch').forEach(function(x){x.classList.toggle('on',x.dataset.f===fc)});
  ap();
 };
});
document.querySelectorAll('.tb').forEach(function(b){
 b.onclick=function(){
  var v=b.dataset.t;
  ft=(ft===v)?null:v;
  document.querySelectorAll('.tb').forEach(function(x){x.classList.toggle('on',x.dataset.t===ft)});
  ap();
 };
});
document.getElementById('all').onclick=function(){
 fc=null;ft=null;onlyrep=false;onlyold=false;onlystore=false;
 document.querySelectorAll('.ch,.tb').forEach(function(x){x.classList.remove('on')});
 document.querySelectorAll('#onlyrep,#onlyold,#onlystore').forEach(function(x){x.classList.remove('on')});
 ap();
};
function tog(id,set){document.getElementById(id).onclick=function(){set();this.classList.toggle('on');ap();};}
tog('onlyrep',function(){onlyrep=!onlyrep});
tog('onlyold',function(){onlyold=!onlyold});
tog('onlystore',function(){onlystore=!onlystore});

document.getElementById('ord').onchange=function(){
 var k=this.value, arr=C.slice();
 arr.sort(function(a,b){
  if(k==='rep') return (+b.dataset.rep)-(+a.dataset.rep) || (+b.dataset.d)-(+a.dataset.d);
  if(k==='d')   return (+b.dataset.d)-(+a.dataset.d);
  if(k==='an')  return a.dataset.anun.localeCompare(b.dataset.anun);
  return 0;
 });
 if(k==='cpt') arr=C.slice();
 arr.forEach(function(c){G.appendChild(c)});
};

var LB=document.getElementById('lb');
G.addEventListener('click',function(e){
 if(e.target.tagName==='IMG'){LB.querySelector('img').src=e.target.src;LB.style.display='flex';}
});
LB.onclick=function(){LB.style.display='none'};
document.addEventListener('keydown',function(e){if(e.key==='Escape')LB.style.display='none'});
ap();
</script>
"""

HTML = (HTML.replace("__N__", str(len(items)))
            .replace("__NT__", str(n_tiendas))
            .replace("__NREP__", str(n_rep))
            .replace("__NOLD__", str(n_old))
            .replace("__NC__", str(len([k for k, _, _, _ in CONCEPTOS if por_cpt.get(k, 0)])))
            .replace("__F__", datetime.date.today().isoformat())
            .replace("__LEG__", leyenda)
            .replace("__CHIPS__", chips)
            .replace("__TIENDAS__", tiendas_html)
            .replace("__CARDS__", "\n".join(card(i) for i in items)))

io.open(SALIDA, "w", encoding="utf-8").write(HTML)

print("%s escrito (%d KB)%s" % (SALIDA, len(HTML.encode("utf-8"))//1024,
      "  [autocontenido: se abre en cualquier carpeta]" if PORTABLE else "  [requiere estar junto a _IMG/]"))
print("  %d creativos | %d tiendas | %d con replicas | %d con 21+ dias" % (len(items), n_tiendas, n_rep, n_old))
print("  tiendas que repiten (>=2 favoritos):")
for t, n in tiendas_rank:
    if n >= 2:
        print("    %2d  %s" % (n, t))
