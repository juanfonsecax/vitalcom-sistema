# -*- coding: utf-8 -*-
import csv,io,os,datetime,html,json
R=list(csv.DictReader(io.open('_ADS.csv',encoding='utf-8')))
R+=list(csv.DictReader(io.open('_BANCO.csv',encoding='utf-8'))) if os.path.exists('_BANCO.csv') else []
def f(x,d=0.0):
    try: return float(x)
    except: return d
def i(x,d=0):
    try: return int(float(x))
    except: return d
seen=set()
R2=[]
for r in R:
    aid=r.get('ad_archive_id')
    if aid in seen: continue
    seen.add(aid)
    if 'copy' not in r:
        r['copy']=' '.join(x for x in (r.get('titulo'),r.get('descripcion'),r.get('texto_principal')) if x)
    if 'rank_impresiones' not in r:
        r['rank_impresiones']=r.get('pos')
    if 'collation_count' not in r:
        r['collation_count']=r.get('replicas')
    R2.append(r)
R=R2
# CONCEPTO + flag de catalogo (de _PRECLASIFICACION.csv, generado por clasificar_conceptos.py).
# Los ads de CATALOGO DINAMICO no son creativos deliberados: son contenedores de feed que Meta
# rota entre SKUs. No tienen hook ni concepto que copiar -> se marcan y quedan FUERA del ranking.
CONC={}
if os.path.exists('_PRECLASIFICACION.csv'):
    for r in csv.DictReader(io.open('_PRECLASIFICACION.csv',encoding='utf-8')):
        CONC[r['ad_archive_id']]=(r.get('concepto_auto','REVISAR_VISUAL'), r.get('es_catalogo','NO'))
for r in R:
    c,cat=CONC.get(r.get('ad_archive_id'),('REVISAR_VISUAL','NO'))
    r['_con']=c
    r['_cat']=(cat=='SI')
for r in R:
    cc=i(r.get('collation_count'),1); rep=i(r.get('replicas_misma_imagen'),1)
    r['_esc']=max(cc,rep)
    r['_d']=i(r.get('dias_corriendo'))
    r['_v']=f(r.get('velocidad'))
    r['_r']=i(r.get('rank_impresiones'),99)
    # SCORE (corregido): la velocidad solo cuenta si el ad ya maduro (>=7d).
    # Sin piso, un ad de 1 dia divide por 1 y explota el ranking: eso es ruido, no senal.
    d=max(r['_d'],7)
    pos=max(11-min(r['_r'],10),1)          # 10 para el #1, 1 del #10 en adelante
    vel=round(pos*30.0/d,1)
    r['_v']=vel
    r['_s']=round(r['_esc']*20 + (15 if r['_d']>=21 else 0) + (vel if r['_d']>=7 else 0),1)
    # los de catalogo no compiten en el ranking de creativos: score forzado al piso
    if r['_cat']: r['_s']=-1
    r['_verde']= 'SIN VEREDICTO' if r['_d']<7 else ''
R.sort(key=lambda x:(x['_cat'], x['_d']<7, -x['_s']))

# ─────────────────────────────────────────────────────────────────────────────
# ETIQUETADO MANUAL (operador). Diseno: SELECCION MULTIPLE -> asignar a grupo.
# La clasificacion AUTOMATICA va OCULTA por defecto: si el operador la ve mientras
# clasifica, deja de ser una segunda opinion independiente y comparar las dos
# pierde sentido. Se revela con el check "ver mi clasificacion auto".
# UGC_NATIVO agregado 2026-08-18 tras deteccion del operador: existe toda una familia
# de creativos con estetica de foto real (selfie de espejo, foto casera, mano sosteniendo
# el producto) que el catalogo original no contemplaba porque se construyo mirando solo
# piezas pulidas de estudio. Verificado en Mi_Camino_al_Bienestar/08 y SupleNat/01.
CONCEPTOS=[('1','TESTIMONIO'),('2','DEMO_USO'),('3','EDUCATIVO'),('4','COMPARACION'),
           ('5','AUTORIDAD'),('6','PRUEBA_SOCIAL'),('7','OFERTA_PRECIO'),('8','AMENAZA'),
           ('9','PRODUCTO_HERO'),('0','CHAT'),('U','UGC_NATIVO')]

def card(r):
    tags=[]
    if r['_cat']: tags.append('<b class="t cat">catalogo dinamico</b>')
    if r['_esc']>=2: tags.append('<b class="t esc">x%d replicas</b>'%r['_esc'])
    if r['_d']>=21: tags.append('<b class="t vet">%dd corriendo</b>'%r['_d'])
    if r['_d']<7: tags.append('<b class="t new">%dd - sin veredicto</b>'%r['_d'])
    auto='' if r['_cat'] else '<b class="t con autocon">auto: %s</b>'%html.escape(r['_con'])
    return ('<figure class="c" data-aid="%s" data-esc="%d" data-d="%d" data-adv="%s" data-con="%s" data-cat="%d" data-r="%d">'
      '<span class="star" title="marcar como favorito">&#9734;</span>'
      '<img loading="lazy" src="%s" alt="">'
      '<figcaption><div class="adv">%s</div><div class="tags">%s%s<b class="t mine"></b></div>'
      '<div class="m">#%d impr &middot; vel %.1f &middot; score %.1f</div>'
      '<div class="cp">%s</div></figcaption></figure>') % (
       html.escape(r.get('ad_archive_id','')), r['_esc'], r['_d'], html.escape(r['anunciante']),
       html.escape(r['_con']), 1 if r['_cat'] else 0, r['_r'],
       html.escape(r['archivo']), html.escape(r['anunciante']),
       ' '.join(tags), auto, r['_r'], r['_v'], r['_s'], html.escape(r['copy'][:90]))

advs=sorted({r['anunciante'] for r in R})
opts=''.join('<option>%s</option>'%html.escape(a) for a in advs)
cons=sorted({r['_con'] for r in R if not r['_cat']})
optc=''.join('<option>%s</option>'%html.escape(c) for c in cons)
optm=''.join('<option value="%s">%s</option>'%(c,c) for k,c in CONCEPTOS)
btns=''.join('<button class="kb" data-k="%s"><i>%s</i>%s</button>'%(c,k,c) for k,c in CONCEPTOS)
n_cat=sum(1 for r in R if r['_cat'])
META={r.get('ad_archive_id',''):[r['anunciante'],r['archivo'],r['_con'],1 if r['_cat'] else 0,r['_d'],r['_esc']] for r in R}

TPL=r'''<!doctype html><meta charset="utf-8"><title>SWIPE FILE GT - Bienestar</title>
<style>
:root{--bg:#0e1116;--fg:#e6edf3;--mut:#8b98a5;--card:#161b22;--bd:#30363d;--sel:#4f8cff}
body{background:var(--bg);color:var(--fg);font:14px/1.45 system-ui,sans-serif;margin:0;padding:20px}
h1{font-size:20px;margin:0 0 4px}.sub{color:var(--mut);margin-bottom:12px;font-size:13px}
.bar{position:sticky;top:0;background:var(--bg);padding:10px 0;border-bottom:1px solid var(--bd);margin-bottom:14px;z-index:9}
.row{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin-bottom:8px}
.row:last-child{margin-bottom:0}
select,button{background:var(--card);color:var(--fg);border:1px solid var(--bd);border-radius:6px;padding:6px 10px;font-size:13px;cursor:pointer}
button:hover{border-color:var(--sel)}
.kb{font-weight:600}
.kb i{display:inline-block;background:#30363d;color:#c9d1d9;border-radius:3px;padding:0 5px;margin-right:5px;font-style:normal;font-size:11px}
.kb:disabled{opacity:.35;cursor:not-allowed}
.g{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:14px}
.c{margin:0;background:var(--card);border:1px solid var(--bd);border-radius:10px;overflow:hidden;cursor:pointer;position:relative}
.c.sel{outline:3px solid var(--sel);outline-offset:-1px}
.star{position:absolute;top:6px;right:8px;z-index:3;font-size:24px;line-height:1;color:#fff;
 text-shadow:0 1px 4px #000;cursor:pointer;user-select:none;opacity:.55}
.star:hover{opacity:1;transform:scale(1.15)}
.c.fav .star{color:#fbbf24;opacity:1}
.c.fav{outline:3px solid #fbbf24;outline-offset:-1px}
.c.fav.sel{outline:3px solid var(--sel)}
.c img{width:100%;display:block;aspect-ratio:1;object-fit:cover}
figcaption{padding:9px}
.adv{font-weight:600;font-size:13px;margin-bottom:5px}
.tags{margin-bottom:5px;min-height:4px}
.t{font-size:10px;padding:2px 6px;border-radius:20px;margin-right:4px;display:inline-block;font-weight:600}
.esc{background:#7c2d12;color:#fed7aa}.vet{background:#14532d;color:#bbf7d0}.new{background:#1e3a5f;color:#bfdbfe}
.cat{background:#4a1d1d;color:#fca5a5}.con{background:#312e81;color:#c7d2fe}
.mine{background:#166534;color:#dcfce7}.mine:empty{display:none}
.autocon{display:none}body.showauto .autocon{display:inline-block}
.c[data-cat="1"]{opacity:.45}
.m{color:var(--mut);font-size:11px}.cp{color:var(--mut);font-size:11px;margin-top:5px;line-height:1.35}
#prog{color:var(--mut);font-size:13px}
#panel{display:none;position:fixed;inset:5% 10%;background:var(--card);border:1px solid var(--bd);border-radius:10px;padding:16px;z-index:99;flex-direction:column}
#panel.on{display:flex}
#panel textarea{flex:1;width:100%;background:#0d1117;color:var(--fg);border:1px solid var(--bd);border-radius:6px;font:12px/1.4 ui-monospace,monospace;padding:10px;margin:10px 0}
label{font-size:13px;color:var(--mut);display:flex;align-items:center;gap:5px}
</style>
<h1>SWIPE FILE &mdash; Bienestar Guatemala</h1>
<div class="sub">__N__ creativos de __A__ anunciantes &middot; __F__ &middot; <b>__NCAT__ de catalogo dinamico</b> (ocultos por defecto)<br>
<b><b>Como etiquetar:</b> clic en las imagenes para seleccionarlas (se marcan en azul), despues aprieta el boton del concepto &mdash; o su numero en el teclado. Esc deselecciona. Se guarda en tu navegador.#9733; Favoritos:</b> clic en la estrella de cada imagen para marcarla (o selecciona varias y aprieta <b>F</b>). Es independiente del concepto.<br><b>Conceptos:</b> clic en las imagenes para seleccionarlas (azul), despues el boton del concepto o su tecla. <b>Esc</b> deselecciona. Todo se guarda en tu navegador.</div>
<div class="bar">
 <div class="row">
  <select id="fa"><option value="">Todos los anunciantes</option>__OPTS__</select>
  <select id="fk"><option value="1">Ocultar catalogo</option><option value="">Mostrar todo</option><option value="2">Solo catalogo</option></select>
  <select id="ff"><option value="">Favoritos: todos</option><option value="1">SOLO favoritos &#9733;</option><option value="0">Sin marcar</option></select>
  <select id="fm"><option value="">Etiquetado: todos</option><option value="__none">SIN etiquetar</option><option value="__done">YA etiquetados</option>__OPTM__</select>
  <select id="fe"><option value="">Cualquier escalado</option><option value="2">Replicados 2+</option><option value="4">Replicados 4+</option></select>
  <select id="fd"><option value="">Cualquier antiguedad</option><option value="21">21+ dias</option><option value="-7">Nuevos (7d o menos)</option></select>
  <select id="fi"><option value="">Cualquier puesto de impresiones</option><option value="1">#1 de su pagina</option><option value="3">Top 3 de su pagina</option><option value="5">Top 5 de su pagina</option><option value="10">Top 10 de su pagina</option></select>
  <select id="fc" style="display:none"><option value="">Cualquier concepto auto</option>__OPTC__</select>
  <span id="n" style="color:var(--mut);font-size:13px"></span>
 </div>
 <div class="row">
  <button id="selall">Seleccionar visibles</button>
  <button id="selnone">Deseleccionar</button>
  <span id="cnt" style="color:var(--sel);font-weight:600"></span>
  <span style="flex:1"></span>
  <label><input type="checkbox" id="showauto"> ver mi clasificacion auto</label>
  <button id="exp">Exportar etiquetas</button>
  <span id="prog"></span>
 </div>
 <div class="row" id="rowbtns"><button id="favsel" style="border-color:#fbbf24;color:#fbbf24">&#9733; marcar favorito</button>__BTNS__<button class="kb" data-k="">borrar etiqueta</button></div>
 <div class="row"><input id="nuevo" placeholder="nombrar un concepto nuevo que veas..." style="background:var(--card);color:var(--fg);border:1px solid var(--bd);border-radius:6px;padding:6px 10px;font-size:13px;min-width:280px"><button id="addc">+ agregar concepto</button><span style="color:var(--mut);font-size:12px">se agrega como boton y queda guardado</span></div>
</div>
<div class="g" id="g">__CARDS__</div>
<div id="panel">
 <b>Etiquetas para pasarle a Claude</b> &mdash; copia todo el texto y pegalo en el chat.
 <textarea id="out" readonly></textarea>
 <div class="row"><button id="dl">Descargar CSV</button><button id="close">Cerrar</button></div>
</div>
<script>
var META=__META__;
var KEY='swipe_tags_v1';
// Chequeo UNICO de almacenamiento. Si el archivo se abre desde un visor que lo sirve
// como data:/sandbox, localStorage esta deshabilitado y el trabajo NO se guarda solo.
// En ese caso se avisa una vez con un banner fijo (no un alert por cada clic) y se
// bloquea el cierre de pestana si hay etiquetas sin exportar.
var OK_LS=(function(){try{localStorage.setItem('__t','1');localStorage.removeItem('__t');return true}catch(e){return false}})();
var T={}; if(OK_LS){try{T=JSON.parse(localStorage.getItem(KEY)||'{}')}catch(e){T={}}}
// migracion: v1 guardaba T[aid]='CONCEPTO' (string). Ahora T[aid]={c:concepto,f:favorito}.
Object.keys(T).forEach(function(a){if(typeof T[a]==='string')T[a]={c:T[a]}});
var EXTRA=[]; if(OK_LS){try{EXTRA=JSON.parse(localStorage.getItem('swipe_extra_v1')||'[]')}catch(e){EXTRA=[]}}
var C=[].slice.call(document.querySelectorAll('.c'));
function save(){if(OK_LS){try{localStorage.setItem(KEY,JSON.stringify(T));
 localStorage.setItem('swipe_extra_v1',JSON.stringify(EXTRA))}catch(e){}}}
function get(a){return T[a]||(T[a]={})}
function limpiar(a){var o=T[a];if(o&&!o.c&&!o.f)delete T[a]}
if(!OK_LS){
 var w=document.createElement('div');
 w.style.cssText='background:#7f1d1d;color:#fecaca;padding:10px 14px;border-radius:8px;margin-bottom:12px;font-weight:600';
 w.innerHTML='&#9888; Este navegador NO esta guardando tus etiquetas (almacenamiento bloqueado).<br>'+
  'Abri el archivo <b>_GALERIA.html</b> directamente desde la carpeta con doble clic, o usa <b>Exportar etiquetas</b> antes de cerrar.';
 document.body.insertBefore(w,document.body.firstChild);
 window.addEventListener('beforeunload',function(e){
  if(Object.keys(T).length){e.preventDefault();e.returnValue=''}});
}
function paint(c){var a=c.dataset.aid,o=T[a]||{};
 c.querySelector('.mine').textContent=o.c?('YO: '+o.c):'';
 c.classList.toggle('fav',!!o.f);
 c.querySelector('.star').innerHTML=o.f?'&#9733;':'&#9734;';}
function prog(){var n=0,f=0;Object.keys(T).forEach(function(a){if(T[a].c)n++;if(T[a].f)f++});
 document.getElementById('prog').textContent=n+' etiquetados / '+f+' favoritos';}
function sels(){return C.filter(function(c){return c.classList.contains('sel')})}
function cnt(){var n=sels().length;document.getElementById('cnt').textContent=n?(n+' seleccionadas'):'';
 [].forEach.call(document.querySelectorAll('.kb'),function(b){b.disabled=!n});
 document.getElementById('favsel').disabled=!n;}
C.forEach(function(c){paint(c);
 c.addEventListener('click',function(){c.classList.toggle('sel');cnt();});
 // la estrella es independiente de la seleccion: marcar favorito de a uno mientras se scrollea
 c.querySelector('.star').addEventListener('click',function(e){
  e.stopPropagation();var a=c.dataset.aid,o=get(a);
  if(o.f){delete o.f}else{o.f=1} limpiar(a);save();paint(c);prog();ap();});});
function asignar(k){var s=sels();if(!s.length)return;
 s.forEach(function(c){var a=c.dataset.aid,o=get(a);
  if(k){o.c=k}else{delete o.c} limpiar(a); c.classList.remove('sel');paint(c);});
 save();prog();cnt();ap();}
function favSel(){var s=sels();if(!s.length)return;
 // si TODAS las seleccionadas ya son favoritas, el boton desmarca
 var todas=s.every(function(c){return (T[c.dataset.aid]||{}).f});
 s.forEach(function(c){var a=c.dataset.aid,o=get(a);
  if(todas){delete o.f}else{o.f=1} limpiar(a); c.classList.remove('sel');paint(c);});
 save();prog();cnt();ap();}
function bindKb(){[].forEach.call(document.querySelectorAll('.kb'),function(b){
 if(b.__b)return; b.__b=1;
 b.addEventListener('click',function(e){e.stopPropagation();asignar(b.dataset.k)});});}
bindKb();
document.getElementById('favsel').onclick=favSel;
document.getElementById('addc').onclick=function(){
 var v=document.getElementById('nuevo').value.trim().toUpperCase().replace(/[^A-Z0-9_ ]/g,'').replace(/ +/g,'_');
 if(!v)return;
 if(EXTRA.indexOf(v)<0){EXTRA.push(v);save();
  var b=document.createElement('button');b.className='kb';b.dataset.k=v;b.textContent=v;
  document.getElementById('rowbtns').insertBefore(b,document.querySelector('.kb[data-k=""]'));
  var o=document.createElement('option');o.value=v;o.textContent=v;document.getElementById('fm').appendChild(o);
  bindKb();cnt();}
 document.getElementById('nuevo').value='';};
EXTRA.forEach(function(v){
 var b=document.createElement('button');b.className='kb';b.dataset.k=v;b.textContent=v;
 document.getElementById('rowbtns').insertBefore(b,document.querySelector('.kb[data-k=""]'));
 var o=document.createElement('option');o.value=v;o.textContent=v;document.getElementById('fm').appendChild(o);});
bindKb();
document.addEventListener('keydown',function(e){
 if(e.target.tagName==='TEXTAREA'||e.target.tagName==='SELECT'||e.target.tagName==='INPUT')return;
 var m={'1':'TESTIMONIO','2':'DEMO_USO','3':'EDUCATIVO','4':'COMPARACION','5':'AUTORIDAD',
  '6':'PRUEBA_SOCIAL','7':'OFERTA_PRECIO','8':'AMENAZA','9':'PRODUCTO_HERO','0':'CHAT','u':'UGC_NATIVO','U':'UGC_NATIVO'};
 if(m[e.key]){asignar(m[e.key])}
 else if(e.key==='f'||e.key==='F'){favSel()}
 else if(e.key==='Escape'){C.forEach(function(c){c.classList.remove('sel')});cnt()}});
document.getElementById('selall').onclick=function(){
 C.forEach(function(c){if(c.style.display!=='none')c.classList.add('sel')});cnt()};
document.getElementById('selnone').onclick=function(){
 C.forEach(function(c){c.classList.remove('sel')});cnt()};
document.getElementById('showauto').onchange=function(){
 document.body.classList.toggle('showauto',this.checked);
 document.getElementById('fc').style.display=this.checked?'':'none';};
function ap(){var a=fa.value,e=+fe.value||0,d=fd.value,cc=fc.value,kk=fk.value,mm=fm.value,vv=ff.value,ii=+fi.value||0,k=0;
 C.forEach(function(c){var ok=true,o=T[c.dataset.aid]||{},t=o.c||'';
  if(a&&c.dataset.adv!==a)ok=false;
  if(ii&&+c.dataset.r>ii)ok=false;
  if(kk==='1'&&c.dataset.cat==='1')ok=false;
  if(kk==='2'&&c.dataset.cat!=='1')ok=false;
  if(vv==='1'&&!o.f)ok=false;
  if(vv==='0'&&o.f)ok=false;
  if(mm==='__none'&&t)ok=false;
  if(mm==='__done'&&!t)ok=false;
  if(mm&&mm.indexOf('__')!==0&&t!==mm)ok=false;
  if(cc&&c.dataset.con!==cc)ok=false;
  if(e&&+c.dataset.esc<e)ok=false;
  if(d==='21'&&+c.dataset.d<21)ok=false;
  if(d==='-7'&&+c.dataset.d>7)ok=false;
  c.style.display=ok?'':'none'; if(ok)k++;});
 document.getElementById('n').textContent=k+' visibles';}
[fa,fe,fd,fc,fk,fm,ff,fi].forEach(function(s){s.onchange=ap});
function csv(){var L=['ad_archive_id,anunciante,archivo,favorito,concepto_manual,concepto_auto,es_catalogo,dias,replicas'];
 Object.keys(T).forEach(function(a){var m=META[a]||['','','',0,0,0],o=T[a];
  L.push([a,'"'+m[0]+'"','"'+m[1]+'"',(o.f?1:0),(o.c||''),m[2],m[3],m[4],m[5]].join(','));});
 return L.join('\n');}
document.getElementById('exp').onclick=function(){
 var n=Object.keys(T).length;
 document.getElementById('out').value=n?csv():'(todavia no etiquetaste nada)';
 document.getElementById('panel').classList.add('on');
 document.getElementById('out').select();};
document.getElementById('close').onclick=function(){document.getElementById('panel').classList.remove('on')};
document.getElementById('dl').onclick=function(){
 var b=new Blob([csv()],{type:'text/csv'}),u=URL.createObjectURL(b),a=document.createElement('a');
 a.href=u;a.download='_ETIQUETAS_MANUALES.csv';a.click();URL.revokeObjectURL(u);};
prog();cnt();ap();
</script>'''

H=(TPL.replace('__N__',str(len(R))).replace('__A__',str(len(advs)))
      .replace('__F__',datetime.date.today().isoformat()).replace('__NCAT__',str(n_cat))
      .replace('__OPTS__',opts).replace('__OPTC__',optc).replace('__OPTM__',optm)
      .replace('__BTNS__',btns).replace('__META__',json.dumps(META,ensure_ascii=False))
      .replace('__CARDS__','\n'.join(card(r) for r in R)))
io.open('_GALERIA.html','w',encoding='utf-8').write(H)
print('galeria: %d creativos, %d anunciantes, %d catalogo'%(len(R),len(advs),n_cat))
