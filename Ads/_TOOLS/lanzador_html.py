# -*- coding: utf-8 -*-
"""lanzador_html.py — el render de VISTAS/LANZADOR.html.

Separado de gen_lanzador.py a proposito: aquel calcula, este dibuja. Toda la logica
de negocio vive alla; aca no se decide nada, solo se muestra el modelo que llega.

Los tokens de color son los mismos de APP.html y _DASHBOARD.html para que el sistema
se lea como una sola aplicacion.
"""
import json

TOKENS = """
:root{
  --ground:#F4F6FA; --surface:#FFFFFF; --line:#DDE2EC; --line-soft:#EBEEF5;
  --ink:#1A2338; --ink-2:#5A657F; --ink-3:#8892A8;
  --accent:#3B4E8C; --accent-soft:#EDF0F9;
  --good:#1F7A4D; --good-bg:#E6F2EA;
  --warn:#8A6100; --warn-bg:#F7EFDC;
  --crit:#AE3A31; --crit-bg:#F8E8E6;
  --radius:10px;
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
:root[data-theme="light"]{
  --ground:#F4F6FA; --surface:#FFFFFF; --line:#DDE2EC; --line-soft:#EBEEF5;
  --ink:#1A2338; --ink-2:#5A657F; --ink-3:#8892A8;
  --accent:#3B4E8C; --accent-soft:#EDF0F9;
  --good:#1F7A4D; --good-bg:#E6F2EA;
  --warn:#8A6100; --warn-bg:#F7EFDC;
  --crit:#AE3A31; --crit-bg:#F8E8E6;
}
"""

# ─────────────────────────────────────────────────────────────────────────────
# LAS PIEZAS, Y POR QUE ESTAN PARTIDAS
#
# La misma logica de render alimenta DOS carcasas:
#   VISTAS/LANZADOR.html   la pagina suelta      (la arma HTML(), aca abajo)
#   VISTAS/APP.html        la app unificada      (la arma app_html.py)
#
# Por eso el CSS y el JS estan partidos en CHROME (la barra lateral y el grid del
# body: lo unico que cambia entre carcasas) y CUERPO/NUCLEO (las tarjetas, los
# campos copiables, los 7 pasos: identico en las dos). app_html.py importa
# CSS_CUERPO y JS_NUCLEO y pone su propia carcasa encima.
#
# CSS y JS siguen existiendo como la suma de sus dos partes, asi que la pagina
# suelta no cambio de comportamiento.
# ─────────────────────────────────────────────────────────────────────────────

CSS_CHROME = """
*{box-sizing:border-box}
html,body{margin:0;height:100%}
body{background:var(--ground);color:var(--ink);font-family:var(--sans);font-size:14.5px;
  line-height:1.55;-webkit-font-smoothing:antialiased;display:grid;
  grid-template-columns:250px 1fr;height:100vh;overflow:hidden}

/* ── lateral ───────────────────────────────────────────── */
aside{background:var(--surface);border-right:1px solid var(--line);
  display:flex;flex-direction:column;min-height:0;overflow-y:auto}
.marca{padding:17px 16px 14px;border-bottom:1px solid var(--line-soft)}
.marca h1{font-family:var(--serif);font-size:18px;margin:0;font-weight:600;letter-spacing:-.015em}
.marca .sub{color:var(--ink-3);font-size:11.5px;font-family:var(--mono);margin-top:3px}
.grupo{padding:13px 9px 4px}
.grupo .lbl{font-family:var(--mono);font-size:10px;letter-spacing:.11em;color:var(--ink-3);
  padding:0 7px 7px;font-weight:600}
button.nav{width:100%;text-align:left;background:none;border:0;border-radius:8px;
  color:var(--ink-2);font:inherit;padding:8px 10px;cursor:pointer;display:block;
  border-left:2px solid transparent;margin-bottom:1px}
button.nav:hover{background:var(--accent-soft);color:var(--ink)}
button.nav.on{background:var(--accent-soft);color:var(--ink);border-left-color:var(--accent)}
button.nav .rot{display:flex;align-items:center;gap:7px;font-size:13.5px;font-weight:600}
button.nav .sb{display:block;font-size:11px;color:var(--ink-3);font-weight:400;margin-top:1px}
.punto{width:7px;height:7px;border-radius:50%;flex:none}
.p-listo{background:var(--good)}.p-bloq{background:var(--crit)}.p-sin{background:var(--ink-3)}
.p-vivo{background:var(--accent)}

"""

CSS_CUERPO = """
/* ── principal ─────────────────────────────────────────── */
main{overflow-y:auto;min-height:0;padding:26px 30px 90px}
.contenedor{max-width:920px}
h2.tit{font-family:var(--serif);font-size:25px;margin:0 0 3px;font-weight:600;letter-spacing:-.02em}
p.baja{color:var(--ink-2);margin:0 0 22px;font-size:13.5px}
.card{background:var(--surface);border:1px solid var(--line);border-radius:var(--radius);
  margin:0 0 16px;overflow:hidden}
.card>header{padding:13px 17px;border-bottom:1px solid var(--line-soft);
  display:flex;align-items:center;gap:10px}
.card>header h3{margin:0;font-size:14px;font-weight:650;letter-spacing:.005em}
.card>header .n{font-family:var(--mono);font-size:11px;color:var(--ink-3);
  background:var(--accent-soft);border-radius:5px;padding:2px 7px;font-weight:600;flex:none}
.card .cuerpo{padding:15px 17px}
.card .cuerpo>*:first-child{margin-top:0}
.card .cuerpo>*:last-child{margin-bottom:0}

table{width:100%;border-collapse:collapse;font-size:13.5px}
th,td{padding:9px 12px;text-align:left;border-bottom:1px solid var(--line-soft);vertical-align:top}
thead th{font-size:11px;color:var(--ink-3);font-weight:650;text-transform:uppercase;
  letter-spacing:.05em;border-bottom:1px solid var(--line)}
tbody tr:last-child td{border-bottom:0}
tbody tr.clic{cursor:pointer}
tbody tr.clic:hover{background:var(--accent-soft)}
.num{text-align:right;font-variant-numeric:tabular-nums;font-family:var(--mono);font-size:12.5px}

.mono{font-family:var(--mono);font-size:12.5px}
.tenue{color:var(--ink-3)}
.chip{display:inline-block;font-family:var(--mono);font-size:10.5px;font-weight:650;
  padding:2px 7px;border-radius:5px;letter-spacing:.03em;white-space:nowrap}
.c-good{background:var(--good-bg);color:var(--good)}
.c-warn{background:var(--warn-bg);color:var(--warn)}
.c-crit{background:var(--crit-bg);color:var(--crit)}
.c-neutro{background:var(--accent-soft);color:var(--ink-2)}

/* ── el campo copiable: la pieza central de la app ─────── */
.campo{display:flex;align-items:stretch;gap:0;border:1px solid var(--line);
  border-radius:8px;overflow:hidden;margin:7px 0;background:var(--ground)}
.campo .et{flex:none;width:118px;padding:9px 11px;font-size:11px;font-weight:650;
  color:var(--ink-3);text-transform:uppercase;letter-spacing:.05em;
  background:var(--surface);border-right:1px solid var(--line);display:flex;align-items:center}
.campo .val{flex:1;padding:9px 12px;font-family:var(--mono);font-size:12.5px;
  word-break:break-word;white-space:pre-wrap;display:flex;align-items:center;min-width:0}
.campo .val.largo{white-space:pre-wrap;font-size:12px;line-height:1.6;max-height:250px;
  overflow-y:auto;display:block;font-family:var(--sans)}
.campo button.cp{flex:none;border:0;border-left:1px solid var(--line);background:var(--surface);
  color:var(--ink-2);font:inherit;font-size:11.5px;font-weight:650;padding:0 14px;cursor:pointer;
  letter-spacing:.02em}
.campo button.cp:hover{background:var(--accent-soft);color:var(--accent)}
.campo button.cp.hecho{background:var(--good-bg);color:var(--good)}

/* ── checklist ─────────────────────────────────────────── */
ul.chk{list-style:none;margin:0;padding:0}
ul.chk li{display:flex;gap:10px;align-items:flex-start;padding:8px 0;
  border-bottom:1px solid var(--line-soft);font-size:13.5px}
ul.chk li:last-child{border-bottom:0}
ul.chk input{margin:3px 0 0;flex:none;width:15px;height:15px;accent-color:var(--accent);cursor:pointer}
ul.chk li.ok label{color:var(--ink-3);text-decoration:line-through}
ul.chk label{cursor:pointer}
ul.chk .por{display:block;font-size:12px;color:var(--ink-3);margin-top:1px;text-decoration:none!important}

.aviso{border-left:3px solid var(--warn);background:var(--warn-bg);color:var(--warn);
  padding:11px 14px;border-radius:0 8px 8px 0;margin:12px 0;font-size:13px}
.aviso.malo{border-color:var(--crit);background:var(--crit-bg);color:var(--crit)}
.aviso.bien{border-color:var(--good);background:var(--good-bg);color:var(--good)}
.aviso b{font-weight:700}

.barra{display:flex;gap:3px;margin:0 0 20px}
.barra span{height:4px;flex:1;background:var(--line);border-radius:2px}
.barra span.on{background:var(--accent)}

.pasos{display:flex;gap:6px;flex-wrap:wrap;margin:0 0 20px}
.pasos button{border:1px solid var(--line);background:var(--surface);color:var(--ink-2);
  font:inherit;font-size:12.5px;font-weight:600;padding:6px 12px;border-radius:20px;cursor:pointer}
.pasos button:hover{border-color:var(--accent);color:var(--accent)}
.pasos button.on{background:var(--accent);border-color:var(--accent);color:#fff}
.pasos button.done{border-color:var(--good);color:var(--good)}
.pasos button.done.on{background:var(--good);border-color:var(--good);color:#fff}

.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(132px,1fr));gap:11px;margin:0 0 18px}
.kpi{background:var(--surface);border:1px solid var(--line);border-radius:var(--radius);padding:13px 15px}
.kpi .v{font-size:21px;font-weight:680;letter-spacing:-.02em;font-variant-numeric:tabular-nums}
.kpi .k{color:var(--ink-3);font-size:11.5px;margin-top:2px;line-height:1.35}

.toast{position:fixed;bottom:22px;left:50%;transform:translateX(-50%) translateY(80px);
  background:var(--ink);color:var(--ground);padding:9px 18px;border-radius:20px;
  font-size:13px;font-weight:600;opacity:0;transition:.2s;pointer-events:none;z-index:50}
.toast.ver{opacity:1;transform:translateX(-50%) translateY(0)}

.pie{margin:34px 0 0;padding-top:16px;border-top:1px solid var(--line);
  font-size:12px;color:var(--ink-3);line-height:1.7}
.pie code{font-family:var(--mono);font-size:11.5px;background:var(--accent-soft);
  padding:1px 5px;border-radius:4px}
a{color:var(--accent)}
@media(max-width:860px){
  body{grid-template-columns:1fr;grid-template-rows:auto 1fr}
  aside{max-height:190px}
  main{padding:18px 14px 70px}
  .campo{flex-wrap:wrap}.campo .et{width:100%;border-right:0;border-bottom:1px solid var(--line)}
}
"""

# el rstrip evita que la costura entre las dos mitades meta una linea en blanco
# que el archivo original no tenia: asi la pagina suelta sale byte a byte igual.
# el [:-1] se come el salto de linea que la costura entre las dos mitades
# agregaria de mas: asi el CSS de la pagina suelta sale byte a byte igual.
CSS = CSS_CHROME[:-1] + CSS_CUERPO

JS_NUCLEO = r"""
const D = JSON.parse(document.getElementById('datos').textContent);
const G = {vista:'portafolio', pk:null, paso:0};

const esc = s => String(s==null?'':s).replace(/[&<>"]/g, c =>
  ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const q  = n => (n==null? '—' : n);

/* el tope de la vista: en la app unificada el scroller es #vista, no <main> */
const scrollArriba = () => {
  document.querySelectorAll('main,#vista').forEach(el => { el.scrollTop = 0; });
};


/* ── memoria de progreso: sobrevive al refresh ───────────────── */
const KEY = 'lanzador/v1';
let mem = {};
try { mem = JSON.parse(localStorage.getItem(KEY) || '{}'); } catch(e) { mem = {}; }
const guardar = () => { try { localStorage.setItem(KEY, JSON.stringify(mem)); } catch(e){} };
const marcado = id => !!mem[id];
const marcar  = (id, v) => { if(v) mem[id]=1; else delete mem[id]; guardar(); };

/* ── copiar ──────────────────────────────────────────────────── */
function toast(t){ const el=document.getElementById('toast'); el.textContent=t;
  el.classList.add('ver'); clearTimeout(el._t); el._t=setTimeout(()=>el.classList.remove('ver'),1400); }

document.addEventListener('click', ev => {
  const b = ev.target.closest('[data-copiar]');
  if(!b) return;
  const txt = b.parentElement.querySelector('.val').innerText;
  navigator.clipboard.writeText(txt).then(()=>{
    b.classList.add('hecho'); b.textContent='copiado';
    toast('copiado'); if(b.dataset.id) marcar(b.dataset.id, true);
    setTimeout(()=>{ b.textContent='copiar'; }, 1600);
  }).catch(()=>toast('no se pudo copiar'));
});

document.addEventListener('change', ev => {
  const c = ev.target.closest('input[type=checkbox][data-id]');
  if(!c) return;
  marcar(c.dataset.id, c.checked);
  c.closest('li').classList.toggle('ok', c.checked);
  pintarPasos();
});

/* ── piezas ──────────────────────────────────────────────────── */
function campo(etiqueta, valor, opts){
  opts = opts||{};
  if(valor==null || valor==='') return '';
  const cls = opts.largo ? 'val largo' : 'val';
  const id  = opts.id ? ' data-id="'+esc(opts.id)+'"' : '';
  return '<div class="campo"><div class="et">'+esc(etiqueta)+'</div>'+
         '<div class="'+cls+'">'+esc(valor)+'</div>'+
         '<button class="cp" data-copiar'+id+'>copiar</button></div>';
}
function chk(id, texto, porque){
  const on = marcado(id);
  return '<li class="'+(on?'ok':'')+'"><input type="checkbox" data-id="'+esc(id)+'"'+
    (on?' checked':'')+'><label>'+texto+
    (porque? '<span class="por">'+porque+'</span>':'')+'</label></li>';
}
function card(titulo, cuerpo, n){
  return '<section class="card"><header>'+(n?'<span class="n">'+esc(n)+'</span>':'')+
    '<h3>'+titulo+'</h3></header><div class="cuerpo">'+cuerpo+'</div></section>';
}

/* ── vista portafolio ────────────────────────────────────────── */
function vistaPortafolio(){
  const P = D.productos;
  const vivos = P.filter(p=>p.estado==='VIVO').length;
  const listos = P.filter(p=>p.tiene_plan && !p.plan.bloqueantes.length).length;
  const bloq = P.filter(p=>p.tiene_plan && p.plan.bloqueantes.length).length;
  const sin = P.filter(p=>!p.tiene_plan).length;

  let h = '<h2 class="tit">Portafolio</h2>'+
    '<p class="baja">Datos al '+esc(D.generado)+' · el punto de color dice si el producto se puede lanzar hoy</p>'+
    '<div class="kpis">'+
      '<div class="kpi"><div class="v">'+vivos+'</div><div class="k">vivos</div></div>'+
      '<div class="kpi"><div class="v">'+listos+'</div><div class="k">listos para lanzar</div></div>'+
      '<div class="kpi"><div class="v">'+bloq+'</div><div class="k">con plan pero bloqueados</div></div>'+
      '<div class="kpi"><div class="v">'+sin+'</div><div class="k">sin plan de lanzamiento</div></div>'+
    '</div>';

  let filas = '';
  P.forEach(p => {
    let est, cls;
    if(!p.tiene_plan){ est='sin plan'; cls='c-neutro'; }
    else if(p.plan.bloqueantes.length){ est=p.plan.bloqueantes.length+' bloqueante'+(p.plan.bloqueantes.length>1?'s':''); cls='c-crit'; }
    else { est='listo'; cls='c-good'; }
    const cpa = p.cpa_acumulado_q, be = p.cpa_be_q;
    let cpaCls = '';
    if(cpa && be) cpaCls = cpa < be ? 'c-good' : 'c-crit';
    filas += '<tr class="clic" data-ir="'+esc(p.producto_key)+'">'+
      '<td><b>'+esc(p.nombre)+'</b><br><span class="tenue mono" style="font-size:11.5px">'+
        esc(p.producto_key)+'</span></td>'+
      '<td>'+esc(p.estado||'—')+'<br><span class="tenue" style="font-size:12px">'+
        esc(p.fase_csv||'—')+'</span></td>'+
      '<td class="num">'+(be? 'Q'+be.toFixed(2):'—')+'</td>'+
      '<td class="num">'+(cpa? '<span class="chip '+cpaCls+'">Q'+cpa.toFixed(2)+'</span>':'—')+'</td>'+
      '<td class="num">'+(p.historial? p.historial.ventas:'—')+'</td>'+
      '<td><span class="chip '+cls+'">'+esc(est)+'</span></td></tr>';
  });
  h += card('Estado de lanzamiento por producto',
    '<table><thead><tr><th>Producto</th><th>Estado</th><th class="num">Break-even</th>'+
    '<th class="num">CPA acumulado</th><th class="num">Ventas</th><th>Lanzamiento</th></tr></thead>'+
    '<tbody>'+filas+'</tbody></table>');

  h += '<div class="aviso"><b>Cómo se lee el CPA acumulado.</b> Es todo el histórico de '+
    '<code>_FACT_VENTAS.csv</code> dividido por sus ventas, no la semana. Verde = por debajo del '+
    'break-even. La decisión real es semanal y se toma en el dashboard, no acá: esta pantalla es para '+
    '<b>lanzar</b>, no para optimizar.</div>';

  h += '<div class="pie">Generado por <code>Ads/_TOOLS/gen_lanzador.py</code> · '+
    'los planes salen de <code>PRODUCTOS/[X]/_PLAN.json</code> · '+
    'costo por conversación del portafolio: $'+D.usd_por_conversacion_portafolio+
    ' → presupuesto derivado con la fórmula de CALENDARIO_ESCALADO §1.5</div>';
  return h;
}

/* ── vista producto ──────────────────────────────────────────── */
const PASOS = ['Gate','Creativos','Campaña','Conjuntos','Copies','Publicar','Después'];

function vistaProducto(){
  const p = D.productos.find(x=>x.producto_key===G.pk);
  if(!p) return '<p>no encontrado</p>';
  if(!p.tiene_plan) return sinPlan(p);
  const L = p.plan;

  let h = '<h2 class="tit">'+esc(p.nombre)+'</h2>'+
    '<p class="baja">'+esc(L.fase_nombre)+' · mide '+esc(L.fase_mide)+' · <b class="mono">'+
    esc(L.fase_notacion)+'</b> · '+esc(L.fase_forma)+
    ' · lanza <b>'+esc(L.lanzamiento.legible)+' a las '+esc(L.lanzamiento.hora)+'</b></p>';

  h += '<div class="pasos">'+PASOS.map((t,i)=>{
    const done = pasoCompleto(L, i);
    return '<button data-paso="'+i+'" class="'+(G.paso===i?'on ':'')+(done?'done':'')+'">'+
      (i+1)+'. '+t+'</button>';
  }).join('')+'</div>';

  h += [gate, creativos, campana, conjuntos, copies, publicar, despues][G.paso](L, p);
  return h;
}

document.addEventListener('click', ev => {
  const b = ev.target.closest('[data-paso]');
  if(!b) return;
  G.paso = +b.dataset.paso; pintar(); scrollArriba();
});

function idsDelPaso(L, i){
  const pk = L.producto_key, ids = [];
  if(i===0) return ['gate/'+pk+'/revisado'];
  if(i===1) L.conjuntos.forEach(c=>ids.push('prompt/'+pk+'/'+c.n));
  if(i===2) ids.push.apply(ids, L.campanas.map((c,j)=>'camp/'+pk+'/'+j));
  if(i===3) L.conjuntos.forEach(c=>ids.push('conj/'+pk+'/'+c.n));
  if(i===4) L.conjuntos.forEach(c=>ids.push('copy/'+pk+'/'+c.n));
  if(i===5) ids.push.apply(ids, CHECK_PUBLICAR.map((x,j)=>'pub/'+pk+'/'+j));
  if(i===6) return [];
  return ids;
}
function pasoCompleto(L, i){
  const ids = idsDelPaso(L, i);
  return ids.length>0 && ids.every(marcado);
}
function pintarPasos(){
  const p = D.productos.find(x=>x.producto_key===G.pk);
  if(!p || !p.tiene_plan) return;
  document.querySelectorAll('[data-paso]').forEach(b=>{
    b.classList.toggle('done', pasoCompleto(p.plan, +b.dataset.paso));
  });
}

/* PASO 1 · GATE */
function gate(L, p){
  let h = '';
  if(L.bloqueantes.length){
    h += '<div class="aviso malo"><b>No se puede publicar todavía.</b> '+
      L.bloqueantes.length+' cosa'+(L.bloqueantes.length>1?'s':'')+' falta'+
      (L.bloqueantes.length>1?'n':'')+'. El sistema no las inventa — al lado va quién las produce.</div>';
    h += card('Bloqueantes', '<table><thead><tr><th>Qué falta</th><th>Quién lo produce</th></tr></thead><tbody>'+
      L.bloqueantes.map(b=>'<tr><td><b>'+esc(b.que)+'</b></td><td class="tenue">'+esc(b.quien)+'</td></tr>').join('')+
      '</tbody></table>');
  } else {
    h += '<div class="aviso bien"><b>Verde.</b> No hay bloqueantes: cuenta, página y break-even están. '+
      'Podés seguir al paso 2.</div>';
  }

  const e = L.economia, pr = L.presupuesto;
  h += '<div class="kpis">'+
    '<div class="kpi"><div class="v">Q'+q(e.cpa_be_q&&e.cpa_be_q.toFixed(2))+'</div>'+
      '<div class="k">CPA break-even<br><span class="tenue">arriba de esto se pierde plata</span></div></div>'+
    '<div class="kpi"><div class="v">Q'+q(e.cpa_base_q&&e.cpa_base_q.toFixed(2))+'</div>'+
      '<div class="k">CPA objetivo</div></div>'+
    '<div class="kpi"><div class="v">$'+pr.por_conjunto_usd.toFixed(2)+'</div>'+
      '<div class="k">por conjunto/día</div></div>'+
    '<div class="kpi"><div class="v">$'+pr.total_dia_usd.toFixed(2)+'</div>'+
      '<div class="k">total/día · '+L.conjuntos.length+' conjuntos</div></div>'+
    '<div class="kpi"><div class="v">'+q(pr.dias_a_pd)+' d</div>'+
      '<div class="k">hasta el Presupuesto de Decisión</div></div>'+
    '</div>';

  h += card('De dónde sale el presupuesto',
    '<p style="margin:0 0 10px">El presupuesto no es un número elegido: sale de la fórmula de '+
    '<code style="font-family:var(--mono);font-size:12px">CALENDARIO_ESCALADO §1.5</code> — '+
    '<b>7 × (costo por conversación observado)</b>, con piso $'+D.constantes.piso_presupuesto+
    ' y techo $'+D.constantes.techo_presupuesto+'. Para este producto: <b>'+esc(pr.por_que)+'</b>.</p>'+
    '<div class="aviso"><b>Qué significan los '+q(pr.dias_a_pd)+' días.</b> Antes de ese día, '+
    'un conjunto con <b>0 ventas no perdió</b> — todavía no gastó lo suficiente para que un cero '+
    'signifique algo. Apagarlo antes es tirar una moneda. Después de ese día, el cero sí es veredicto.</div>');

  h += card('Por qué esta estructura y no otra',
    '<table style="margin:-6px 0 12px"><thead><tr><th>Fase</th><th>Estructura</th>'+
    '<th>Presupuesto</th><th>Decide por</th></tr></thead><tbody>'+
    [1,2,3].map(f=>{
      const e = D.estructura[f], aca = (f===L.fase);
      return '<tr'+(aca?' style="background:var(--accent-soft)"':'')+'>'+
        '<td>'+(aca?'<b>':'')+esc(e.nombre)+(aca?'</b> ←':'')+'</td>'+
        '<td class="mono">'+esc(e.notacion)+'</td>'+
        '<td><span class="chip '+(e.presupuesto==='PROTEGIDO'?'c-warn':'c-neutro')+'">'+
          esc(e.presupuesto)+'</span></td>'+
        '<td class="tenue">'+esc(e.decide)+'</td></tr>';
    }).join('')+'</tbody></table>'+
    '<p style="margin:0 0 10px"><b>La regla que reparte:</b> presupuesto <b>protegido</b> '+
    '(conjuntos separados) cuando la variable se decide por <b>VENTA</b> · presupuesto '+
    '<b>libre</b> (1-1-N, Meta reparte) cuando se decide por <b>ENTREGA</b>.</p>'+
    '<p style="margin:0 0 10px">'+esc(L.fase_por_que)+'</p>'+
    '<div class="aviso"><b>Lo que esta fase NO es.</b> '+esc(L.fase_no_es)+'</div>');

  if(L.faltantes.length){
    h += card('Huecos del plan (no bloquean, pero degradan la lectura)',
      '<ul class="chk">'+L.faltantes.map(f=>'<li><span class="tenue">·</span><label>'+esc(f)+'</label></li>').join('')+'</ul>');
  }
  h += card('Confirmar', '<ul class="chk">'+
    chk('gate/'+L.producto_key+'/revisado', 'Revisé los bloqueantes y el presupuesto derivado',
        'Marcalo cuando entendiste con qué plata vas a correr y hasta qué día no se decide nada.')+
    '</ul>');
  return h;
}

/* PASO 2 · CREATIVOS */
function creativos(L){
  let h = '<div class="aviso"><b>Cómo se hace cada imagen.</b> Copiá el prompt, abrilo en Gemini Pro '+
    'o ChatGPT, <b>adjuntá la foto del producto</b> y generá. Guardá el archivo con el nombre exacto '+
    'que dice la ficha, en <code>Ads/MEDIA_'+esc(L.producto_key)+'/</code>. El nombre importa: es la '+
    'llave con la que después se lee qué creativo vendió.</div>';
  L.conjuntos.forEach(c=>{
    let b = campo('archivo', c.archivo_creativo);
    b += campo('carpeta', 'Ads/MEDIA_'+L.producto_key+'/');
    if(c.prompt_imagen){
      b += campo('prompt', c.prompt_imagen, {largo:true, id:'prompt/'+L.producto_key+'/'+c.n});
    } else {
      b += '<div class="aviso malo">Sin prompt. Este conjunto corre en '+esc(c.formato)+
           ' — el archivo tiene que existir ya en la carpeta de media.</div>';
    }
    h += card(esc(c.angulo_titulo||c.angulo_key)+
      (c.lleva_precio? ' <span class="chip c-warn">con precio</span>':' <span class="chip c-neutro">sin precio</span>'),
      b, 'conjunto '+c.n);
  });
  return h;
}

/* PASO 3 · CAMPAÑA */
function campana(L){
  let h = '';
  if(L.campanas.length>1){
    h += '<div class="aviso"><b>Son '+L.campanas.length+' campañas, no una.</b> Cada concepto tiene que '+
      'correr <b>dos veces</b> en estructuras independientes: es lo que hace posible la regla '+
      '"gana en 2 de 2". Una sola aparición no alcanza para coronar nada.</div>';
  }
  L.campanas.forEach((c,i)=>{
    let b = campo('nombre', c.nombre, {id:'camp/'+L.producto_key+'/'+i});
    b += campo('objetivo', c.objetivo);
    b += campo('presupuesto', c.presupuesto);
    b += campo('programar', L.lanzamiento.legible+' · '+L.lanzamiento.hora);
    b += '<div class="aviso"><b>Nunca lanzar el mismo día.</b> Siempre programada para las 4 AM del '+
      'día siguiente. Y verificá <b>"Maximizar conversaciones"</b> justo antes de publicar: Meta lo '+
      'revierte solo a "maximizar clics en el enlace" con cada cambio que hacés.</div>';
    h += card('Campaña '+esc(c.rol), b, i+1);
  });
  return h;
}

/* PASO 4 · CONJUNTOS */
function conjuntos(L){
  let h = '<div class="aviso"><b>Mismo presupuesto en todos.</b> Si un conjunto corre con más plata, '+
    'gana por plata y no por ángulo, y el testeo no mide nada. Y <b>Advantage+ Audience OFF</b>: '+
    'sin eso Meta ignora la banda de edad y vuelve a lo amplio.</div>';

  let t = '<table><thead><tr><th>#</th><th>Ángulo</th><th>Banda</th><th class="num">$/día</th>'+
    '<th>Precio</th></tr></thead><tbody>';
  L.conjuntos.forEach(c=>{
    t += '<tr><td class="num">'+c.n+'</td><td>'+esc(c.angulo_titulo||c.angulo_key)+'</td>'+
      '<td class="mono">'+esc(c.banda_edad)+'</td>'+
      '<td class="num">$'+c.presupuesto_usd.toFixed(2)+'</td>'+
      '<td>'+(c.lleva_precio?'<span class="chip c-warn">sí</span>':'<span class="tenue">no</span>')+'</td></tr>';
  });
  t += '</tbody></table>';
  h += card('Los '+L.conjuntos.length+' conjuntos', t);

  L.conjuntos.forEach(c=>{
    let b = campo('nombre', c.nombre, {id:'conj/'+L.producto_key+'/'+c.n});
    b += campo('presupuesto', '$'+c.presupuesto_usd.toFixed(2)+' diario  ('+c.presupuesto_centavos+'¢ USD)');
    b += campo('edad', c.banda_edad);
    b += campo('género', c.genero);
    b += '<p class="tenue" style="font-size:12.5px;margin:4px 0 12px">Banda '+esc(c.banda_por_que)+
      '. <b>Advantage+ Audience OFF · sin intereses</b> — el creativo segmenta.</p>';
    b += '<p style="font-size:12.5px;margin:0 0 4px"><b>Los 2 anuncios</b> — el B es copia exacta del A. '+
      'El duplicado interno baja el CPA; nunca lanzar con uno solo.</p>';
    c.anuncios.forEach(a=>{ b += campo('anuncio '+a.letra, a.nombre); });
    h += card(esc(c.angulo_titulo||c.angulo_key), b, 'conjunto '+c.n);
  });

  h += '<div class="aviso"><b>Qué es lo que va después del <code>~</code>.</b> Es la firma: los 5 ejes '+
    'del anuncio metidos en su propio nombre. El <code>ad_id</code> de Meta llegó corrupto en 2.006 de '+
    '2.475 filas del histórico y no se recupera; el <b>nombre</b>, en cambio, viene intacto en cualquier '+
    'export. Con la firma ahí, saber qué concepto vendió deja de depender de que alguien mantenga una '+
    'tabla al día. Un <code>?</code> es un eje sin llenar.</div>';
  return h;
}

/* PASO 5 · COPIES */
function copies(L){
  let h = '<div class="aviso"><b>Dónde va cada cosa.</b> El texto principal va en "Texto principal" '+
    '(podés pegar las variaciones en <i>Agregar opción de texto</i>), los títulos en "Título" y la '+
    'descripción en "Descripción". El precio solo va en los conjuntos marcados.</div>';
  L.conjuntos.forEach(c=>{
    const cp = c.copy||{};
    let b = '';
    (cp.textos||[]).forEach((t,i)=>{
      b += campo('texto '+(i+1), t, {largo:true, id: i===0? 'copy/'+L.producto_key+'/'+c.n : null});
    });
    if(cp.titulos && cp.titulos.length) b += campo('títulos', cp.titulos.join('  /  '));
    if(cp.descripcion) b += campo('descripción', cp.descripcion);
    if(!(cp.textos||[]).length) b += '<div class="aviso malo">Sin copy. Lo produce <b>etapa-4</b>.</div>';
    h += card(esc(c.angulo_titulo||c.angulo_key)+
      (c.lleva_precio? ' <span class="chip c-warn">lleva precio</span>':''), b, 'conjunto '+c.n);
  });
  return h;
}

/* PASO 6 · PUBLICAR */
const CHECK_PUBLICAR = [
  ['Objetivo = <b>Tráfico</b>, no Interacción',
   'Interacción nunca funcionó. Ventas solo como campaña paralela: trae público más calificado pero CPA más alto.'],
  ['<b>"Maximizar conversaciones"</b> verificado justo antes de publicar',
   'Meta lo revierte solo a "maximizar clics en el enlace" con cada cambio que hacés. Es el error más caro y el más fácil de cometer.'],
  ['Presupuesto a nivel <b>CONJUNTO</b> + desmarcar "compartir presupuesto entre conjuntos"',
   'Si queda compartido, un conjunto malo le roba presupuesto a los demás y el testeo no mide el ángulo.'],
  ['Destino <b>manual → WhatsApp</b>, nunca Messenger',
   'Messenger no está entrenado para vender. El número tiene que estar conectado a la fanpage.'],
  ['Desmarcar <b>"anuncios multianunciantes"</b>',
   'Si queda marcado, tu anuncio sale junto a competencia más barata.'],
  ['Desmarcar <b>"incluir personas de WhatsApp cuya edad se desconoce"</b>',
   'Cae a menores y se pierde la impresión.'],
  ['<b>Advantage+ Audience OFF</b> en todos los conjuntos',
   'Sin eso Meta ignora la banda de edad. APR-060: Q473.6/venta a 25+ contra Q30.6 a 45-60, mismo ángulo y mismo creativo.'],
  ['Ningún conjunto ni anuncio se llama <b>"- Copia"</b>',
   'Meta lo agrega al duplicar. Un "- Copia" publicado nace anónimo: no se sabe de qué cuenta, qué ángulo ni qué réplica es.'],
  ['<b>NO</b> aceptar las recomendaciones de Meta',
   'Apaga buenos conjuntos y sugiere subir presupuesto en campañas apagadas.'],
  ['Todo queda <b>programado para las 4 AM</b>, no publicado ya',
   'Nunca lanzar el mismo día.'],
];
function publicar(L){
  let h = '<div class="aviso"><b>Esta lista es el filtro final.</b> Cada punto es un error que ya '+
    'costó plata en este negocio. Van todos marcados antes de darle publicar.</div>';
  h += card('Checklist de publicación', '<ul class="chk">'+
    CHECK_PUBLICAR.map((c,i)=>chk('pub/'+L.producto_key+'/'+i, c[0], c[1])).join('')+'</ul>');
  return h;
}

/* PASO 7 · DESPUÉS */
function despues(L){
  let h = '<div class="aviso"><b>Lo que sigue no lo decidís vos, lo decide la data.</b> Este es el '+
    'calendario con las fechas ya calculadas para este lanzamiento. Lo único que tenés que hacer es '+
    'traer el export el día que dice.</div>';
  let t = '<table><thead><tr><th>Cuándo</th><th>Fecha</th><th>Qué pasa</th><th>Qué traés</th></tr></thead><tbody>';
  L.calendario.forEach(c=>{
    t += '<tr><td><b>'+esc(c.dia)+'</b></td><td class="mono">'+esc(c.fecha)+'</td>'+
      '<td>'+esc(c.que)+'<br><span class="tenue" style="font-size:12.5px">'+esc(c.hace)+'</span></td>'+
      '<td class="tenue">'+esc(c.manda||'—')+'</td></tr>';
  });
  t += '</tbody></table>';
  h += card('Calendario de decisión', t);

  h += card('Cómo se declara el ganador',
    '<p style="margin:0 0 10px"><b>'+esc(L.fase_decide)+'.</b></p>'+
    '<div class="aviso"><b>La conversación corta, nunca corona.</b> Evidencia propia: '+
    '<code>tinnidrop-1</code> hizo 78% de conversación y <b>0 ventas</b>; <code>ANIMO</code> hizo la '+
    'conversación más alta del portafolio (68%) y <b>0 ventas</b>; <code>ME DIJERON</code> hizo 23-25% '+
    'y es de los que más vende. Sirve para apagar el día 3, nunca para elegir el ganador.</div>'+
    '<div class="aviso"><b>Y se agrega por ángulo, no por conjunto.</b> Las ventas por conjunto son '+
    'ruido de Poisson casi puro (índice de dispersión 1.12): un conjunto con 3 ventas y uno con 1 son '+
    'estadísticamente indistinguibles. Agregando por <code>angulo_key</code> la dispersión sube a 2.99 '+
    '— ahí sí hay señal. Por eso el "ganador" de TINNIDROP se corrió tres veces: no cambió el mercado, '+
    'era varianza de muestreo.</div>');
  return h;
}

/* ── producto sin plan ───────────────────────────────────────── */
function sinPlan(p){
  let h = '<h2 class="tit">'+esc(p.nombre)+'</h2>'+
    '<p class="baja">'+esc(p.estado||'')+' · sin plan de lanzamiento</p>';
  h += '<div class="aviso malo"><b>Este producto no tiene <code>_PLAN.json</code>.</b> Sin él la app no '+
    'puede armar el lanzamiento: no hay ángulos, ni prompts, ni copies estructurados. El plan no se '+
    'inventa acá — lo produce la cadena de etapas.</div>';
  h += card('Qué falta y quién lo produce',
    '<table><thead><tr><th>Qué falta</th><th>Quién</th></tr></thead><tbody>'+
    (p.falta_para_plan||[]).map(f=>'<tr><td><b>'+esc(f.que)+'</b></td><td class="tenue">'+esc(f.quien)+'</td></tr>').join('')+
    '</tbody></table>');
  if(p.historial){
    h += card('Lo que sí sabemos de este producto',
      '<div class="kpis" style="margin:0">'+
      '<div class="kpi"><div class="v">$'+p.historial.spend_usd.toFixed(0)+'</div><div class="k">gastado</div></div>'+
      '<div class="kpi"><div class="v">'+p.historial.ventas+'</div><div class="k">ventas</div></div>'+
      '<div class="kpi"><div class="v">'+(p.cpa_acumulado_q? 'Q'+p.cpa_acumulado_q.toFixed(2):'—')+
        '</div><div class="k">CPA acumulado</div></div>'+
      '<div class="kpi"><div class="v">'+(p.historial.cierre_pct!=null? p.historial.cierre_pct+'%':'—')+
        '</div><div class="k">cierre</div></div>'+
      '</div>');
  }
  h += '<div class="pie">Cuando <code>etapa-6</code> escriba <code>'+esc(p.carpeta)+
    '/_PLAN.json</code>, corré <code>python Ads/_TOOLS/gen_lanzador.py</code> y este producto aparece '+
    'acá con su flujo completo.</div>';
  return h;
}

"""

JS_CHROME = r"""
/* ── lateral ─────────────────────────────────────────────────── */
function pintarNav(){
  let h = '<div class="grupo"><div class="lbl">VISTA</div>'+
    '<button class="nav'+(G.vista==='portafolio'?' on':'')+'" data-ir="portafolio">'+
    '<span class="rot">Portafolio</span>'+
    '<span class="sb">'+D.productos.length+' productos · '+
      D.productos.filter(p=>p.tiene_plan).length+' con plan</span></button></div>';
  h += '<div class="grupo"><div class="lbl">LANZAR</div>';
  D.productos.forEach(p => {
    let cls='p-sin', sub='sin plan de lanzamiento';
    if(p.tiene_plan){
      const b = p.plan.bloqueantes.length;
      cls = b? 'p-bloq' : 'p-listo';
      sub = b? (b+' bloqueante'+(b>1?'s':'')) : 'listo para lanzar';
    } else if(p.estado==='VIVO'){ cls='p-vivo'; sub='vivo · sin plan nuevo'; }
    h += '<button class="nav'+(G.pk===p.producto_key?' on':'')+'" data-ir="'+esc(p.producto_key)+'">'+
      '<span class="rot"><span class="punto '+cls+'"></span>'+esc(p.nombre)+'</span>'+
      '<span class="sb">'+esc(sub)+'</span></button>';
  });
  h += '</div>';
  document.getElementById('nav').innerHTML = h;
}

document.addEventListener('click', ev => {
  const b = ev.target.closest('[data-ir]');
  if(!b) return;
  const v = b.dataset.ir;
  if(v==='portafolio'){ G.vista='portafolio'; G.pk=null; }
  else { G.vista='producto'; G.pk=v; G.paso=0; }
  pintar(); scrollArriba();
});

/* ── arranque ────────────────────────────────────────────────── */
function pintar(){
  pintarNav();
  document.getElementById('vista').innerHTML =
    '<div class="contenedor">'+(G.vista==='portafolio'? vistaPortafolio() : vistaProducto())+'</div>';
}
pintar();
"""

JS = JS_NUCLEO[:-1] + JS_CHROME



def HTML(modelo):
    datos = json.dumps(modelo, ensure_ascii=False).replace("</", "<\\/")
    return (
        '<!doctype html><html lang="es"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>Lanzador · VitalCom</title><style>' + TOKENS + CSS + '</style></head><body>'
        '<aside><div class="marca"><h1>Lanzador</h1>'
        '<div class="sub">VitalCom · ' + modelo["generado"] + '</div></div>'
        '<nav id="nav"></nav></aside>'
        '<main><div id="vista"></div></main>'
        '<div class="toast" id="toast"></div>'
        '<script type="application/json" id="datos">' + datos + '</script>'
        '<script>' + JS + '</script></body></html>'
    )
