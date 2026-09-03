# -*- coding: utf-8 -*-
"""Genera PRODUCTOS/_ESTRUCTURA.html — la vista visual de la ARQUITECTURA DE 3 FASES.

Es la unica pagina del sistema que NO depende de ningun CSV: muestra DOCTRINA, no data.
Por eso no se regenera con la carga diaria; se regenera cuando cambia la estructura.

Comparte la paleta de tokens de _DASHBOARD.html a proposito, para que se lean como
la misma aplicacion. El panel enlaza a esta pagina desde su header y viceversa.

Fuente de la doctrina que renderiza:
    _ROADMAP/ANALISIS_MENTOR_CALET_115_vs_SISTEMA_2026-08-21.md  seccion 9
    Ads/_SWIPE/_CATALOGO_CONCEPTOS.md  PARTE III

Uso:
    python Ads/_TOOLS/gen_estructura.py
"""
import io, os, datetime

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(BASE)
SALIDA = "PRODUCTOS/_ESTRUCTURA.html"

HOY = datetime.date.today().isoformat()

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

CSS = """
*{box-sizing:border-box}
body{margin:0;background:var(--ground);color:var(--ink);font-family:var(--sans);
  font-size:15px;line-height:1.55;-webkit-font-smoothing:antialiased}
.wrap{max-width:1180px;margin:0 auto;padding:28px 20px 72px;
  display:flex;flex-direction:column;gap:30px}
header{display:flex;align-items:baseline;gap:14px;padding:14px 18px;
  border:1px solid var(--line);border-radius:12px;background:var(--surface);flex-wrap:wrap}
header h1{font-family:var(--serif);font-size:23px;font-weight:600;margin:0;letter-spacing:-.01em}
header .meta{color:var(--ink-2);font-size:13px;font-family:var(--mono)}
.spacer{flex:1}
a.nav{text-decoration:none;color:var(--accent);border:1px solid var(--line);
  border-radius:99px;padding:5px 13px;font-size:13px;background:var(--accent-soft);white-space:nowrap}
a.nav:hover{border-color:var(--accent)}

.lead{color:var(--ink-2);font-size:15px;max-width:76ch;margin:-12px 0 0}
.lead b{color:var(--ink)}

/* ── la tira de 3 fases ───────────────────────────────── */
.fases{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;align-items:stretch}
@media (max-width:1000px){.fases{grid-template-columns:1fr}}
.fase{background:var(--surface);border:1px solid var(--line);border-radius:var(--radius);
  padding:0;overflow:hidden;display:flex;flex-direction:column;border-top:3px solid var(--c)}
.fase .head{padding:14px 16px 12px;border-bottom:1px solid var(--line-soft)}
.fase .n{font-family:var(--mono);font-size:11.5px;letter-spacing:.09em;color:var(--c);font-weight:700}
.fase h2{font-family:var(--serif);font-size:19px;margin:2px 0 4px;font-weight:600;letter-spacing:-.01em}
.fase .mide{font-size:13px;color:var(--ink-2)}
.fase .mide b{color:var(--ink)}

/* ── diagrama de campañas ─────────────────────────────── */
.diag{padding:14px 16px;display:flex;flex-direction:column;gap:9px;background:var(--accent-soft)}
.camp{border:1px solid var(--line);border-radius:8px;background:var(--surface);padding:8px 10px}
.camp .ct{display:flex;align-items:center;gap:7px;margin-bottom:7px}
.camp .cn{font-family:var(--mono);font-size:11px;font-weight:700;color:var(--c)}
.camp .cd{font-size:11.5px;color:var(--ink-3)}
.conjs{display:flex;gap:7px}
.conj{flex:1;border:1px dashed var(--line);border-radius:6px;padding:6px 5px;text-align:center}
.conj .cl{font-size:9.5px;font-family:var(--mono);color:var(--ink-3);letter-spacing:.06em;
  text-transform:uppercase;display:block;margin-bottom:5px}
.ads{display:flex;gap:3px;justify-content:center;flex-wrap:wrap}
.ad{flex:1 1 0;min-width:0;max-width:32px;min-height:22px;padding:2px 0;border-radius:3px;
  background:var(--c);opacity:.88;display:flex;align-items:center;justify-content:center;
  font-size:9.5px;line-height:1.15;text-align:center;color:#fff;font-weight:700;
  font-family:var(--mono);letter-spacing:-.02em}
.ad.ghost{background:transparent;border:1.5px dashed var(--c);color:var(--c);opacity:.8}
.ad.win{background:var(--good);box-shadow:0 0 0 2px var(--good-bg)}
.hereda{display:inline-flex;align-items:center;gap:5px;margin-top:7px;padding:3px 9px;
  border-radius:99px;background:var(--good-bg);color:var(--good);font-size:11px;font-weight:600;
  font-family:var(--mono)}
.nota{font-size:10.5px;color:var(--ink-3);text-align:center;margin-top:6px;font-style:italic}

.rows{padding:12px 16px 14px;display:flex;flex-direction:column;gap:0;margin-top:auto}
.row{display:flex;gap:10px;padding:6px 0;border-bottom:1px solid var(--line-soft);font-size:13px}
.row:last-child{border-bottom:0}
.row .k{color:var(--ink-3);width:82px;flex:none;font-size:11.5px;text-transform:uppercase;
  letter-spacing:.04em;padding-top:2px;font-family:var(--mono)}
.row .v{flex:1}
.row .v b{font-family:var(--mono);font-size:13px}
.gate{margin:0 16px 16px;padding:9px 11px;border-radius:8px;background:var(--warn-bg);
  border-left:3px solid var(--warn);font-size:12.5px;color:var(--ink)}
.gate b{color:var(--warn)}

/* ── franjas inferiores ───────────────────────────────── */
.split{display:grid;grid-template-columns:1fr 1fr;gap:16px}
@media (max-width:900px){.split{grid-template-columns:1fr}}
.card{background:var(--surface);border:1px solid var(--line);border-radius:var(--radius);padding:16px 18px}
.card h3{font-family:var(--serif);font-size:16.5px;margin:0 0 10px;font-weight:600}
.regla{display:flex;gap:12px;align-items:flex-start;padding:9px 0;border-bottom:1px solid var(--line-soft)}
.regla:last-child{border-bottom:0}
.regla .tag{font-family:var(--mono);font-size:10.5px;font-weight:700;padding:3px 8px;border-radius:99px;
  white-space:nowrap;flex:none;margin-top:1px}
.tag--prot{background:var(--good-bg);color:var(--good)}
.tag--libre{background:var(--accent-soft);color:var(--accent)}
.tag--no{background:var(--crit-bg);color:var(--crit)}
.regla .txt{font-size:13.5px;color:var(--ink-2)}
.regla .txt b{color:var(--ink)}
table{width:100%;border-collapse:collapse;font-size:13.5px}
th{text-align:left;font-size:11px;text-transform:uppercase;letter-spacing:.05em;color:var(--ink-3);
  padding:6px 8px;border-bottom:1px solid var(--line);font-family:var(--mono);font-weight:600}
td{padding:7px 8px;border-bottom:1px solid var(--line-soft);vertical-align:top}
tr:last-child td{border-bottom:0}
code{font-family:var(--mono);font-size:12.5px;background:var(--accent-soft);
  padding:1px 5px;border-radius:4px}
.foot{color:var(--ink-3);font-size:12px;text-align:center;font-family:var(--mono)}
"""


def bloques(rotulos, ghost=False, win=None):
    """Un bloque por rotulo. ghost = contorno punteado (replica). win = rotulo destacado."""
    out = []
    for r in rotulos:
        cls = "ad ghost" if ghost else "ad"
        if win is not None and r == win:
            cls = "ad win"
        out.append('<span class="%s">%s</span>' % (cls, r))
    return "".join(out)


def conj(label, inner):
    return '<div class="conj"><span class="cl">%s</span><div class="ads">%s</div></div>' % (label, inner)


def camp(nombre, detalle, conjuntos, nota=""):
    nota_html = '<div class="nota">%s</div>' % nota if nota else ""
    return ('<div class="camp"><div class="ct"><span class="cn">%s</span>'
            '<span class="cd">%s</span></div><div class="conjs">%s</div>%s</div>'
            % (nombre, detalle, "".join(conjuntos), nota_html))


# ─────────────────────────────────────────────────────────────────────
# FASE 1 — 5 conjuntos, 1 anuncio cada uno, mismo concepto. Gana uno (A2 de ejemplo).
FASE1_DIAG = camp(
    "5 CONJUNTOS &times; 1", "ABO &middot; 1 campa&ntilde;a",
    [conj("%d" % i, bloques(["A%d" % i], win="A2")) for i in range(1, 6)],
    nota="A1&hellip;A5 = &aacute;ngulos distintos &middot; todos con el MISMO concepto")

# FASE 2 — 1-1-5 + 1-1-5 + 1-2-5. Los 10 conceptos son TODOS del angulo ganador.
C_A = ["C1", "C2", "C3", "C4", "C5"]
C_B = ["C6", "C7", "C8", "C9", "C10"]
FASE2_DIAG = (
    camp("1-1-5", "conceptos 1-5 de A2", [conj("1 conjunto", bloques(C_A))]) +
    camp("1-1-5", "conceptos 6-10 de A2", [conj("1 conjunto", bloques(C_B))]) +
    camp("1-2-5", "los MISMOS 10 &mdash; r&eacute;plica",
         [conj("conj 1", bloques(C_A, ghost=True)), conj("conj 2", bloques(C_B, ghost=True))],
         nota="segunda vuelta: confirma cu&aacute;l gan&oacute; de verdad")
)

# FASE 3 — 1-1-7 y 1-7-7. Un solo creativo: el angulo ganador CON el concepto ganador.
GAN = ["A2<br>C7"] * 7
FASE3_DIAG = (
    camp("1-1-7", "el ganador &times;7 &middot; Post ID",
         [conj("1 conjunto", bloques(GAN))],
         nota="siempre el MISMO: &aacute;ngulo A2 + concepto C7") +
    camp("1-7-7", "CBO &middot; cuando ya sostiene",
         [conj("%d" % i, bloques(["A2<br>C7"] * 2, ghost=True)) for i in range(1, 5)])
)

FASES = [
    dict(c="var(--accent)", n="FASE 1", tit="Testeo de &Aacute;NGULOS",
         mide="Mide <b>qu&eacute; dolor engancha</b>"
              '<div class="hereda" style="background:var(--accent-soft);color:var(--accent)">'
              "empieza ac&aacute; &mdash; nada heredado</div>", diag=FASE1_DIAG,
         rows=[("Fija", "el CONCEPTO &mdash; <code>C2_BENEFICIOS</code> variante <b>ligera</b>"),
               ("Var&iacute;a", "el <b>&aacute;ngulo</b> &mdash; 5 dolores distintos, 1 por conjunto"),
               ("Presup.", "<b>$4.00</b>/conjunto &middot; <b>$20/d&iacute;a</b>"),
               ("Cuenta", "GTR1 &mdash; <b>requiere MCP</b> (se lee por conversaci&oacute;n)"),
               ("Creativos", "5 &mdash; mismo layout, paleta y estructura")],
         gate="<b>Sale cuando:</b> un &aacute;ngulo vende bajo el CPA Base con el gasto de 1&times; Break-Even "
              "(en el ejemplo, <b>A2</b>). Se declara agregando por <code>angulo_key</code>, nunca por conjunto suelto. <b>Ese &aacute;ngulo es el &uacute;nico que pasa a la FASE 2.</b>"),
    dict(c="var(--warn)", n="FASE 2", tit="Testeo de CONCEPTOS",
         mide="Mide <b>qu&eacute; creativo entrega</b>"
              '<div class="hereda">&larr; hereda el &aacute;ngulo ganador <b>A2</b></div>',
         diag=FASE2_DIAG,
         rows=[("Fija", "el <b>&Aacute;NGULO</b> ganador &mdash; y el bot dedicado a ese &aacute;ngulo"),
               ("Var&iacute;a", "el <b>concepto</b> &mdash; 10 ejecuciones <b>del mismo &aacute;ngulo</b>, 6 <code>concepto_key</code>"),
               ("Presup.", "<b>$6 + $6 + $12</b> = <b>$24/d&iacute;a</b> &asymp; Q183"),
               ("Cuenta", "A y B en GTR7 &middot; <b>C en GTR1</b> (evita auto-subasta)"),
               ("Creativos", "10 &mdash; cada uno corre <b>2 veces</b>")],
         gate="<b>Se corona por R&Eacute;PLICA:</b> gana en <b>2 de 2</b> apariciones &rarr; ganador. "
              "En 1 de 2 &rarr; ruido, se repite. Sin entrega &rarr; <code>SIN_ENTREGA</code>, nunca perdedor."),
    dict(c="var(--good)", n="FASE 3", tit="Escalado",
         mide="Mide <b>hasta d&oacute;nde aguanta</b>"
              '<div class="hereda">&larr; hereda <b>A2 + C7</b> &mdash; los dos ganadores</div>',
         diag=FASE3_DIAG,
         rows=[("Fija", "&aacute;ngulo <b>y</b> concepto &mdash; ambos ya validados"),
               ("Var&iacute;a", "el <b>volumen</b> &mdash; presupuesto, cuentas, fanpages"),
               ("Presup.", "<b>$15-18/d&iacute;a</b> &middot; +20% diario con gate de CPA"),
               ("Cuenta", "GTR13 / CP1 &mdash; <b>no necesita MCP</b> (se mide por ventas)"),
               ("Creativos", "el ganador replicado &middot; renovaci&oacute;n continua")],
         gate="<b>Techo del portafolio: Q597/d&iacute;a.</b> Arriba de ah&iacute; el CPA se rompe (APR-057). "
              "Solo se pasa si antes entr&oacute; un &aacute;ngulo o una cuenta nueva que lo sostenga."),
]

fases_html = ""
for f in FASES:
    rows = "".join('<div class="row"><span class="k">%s</span><span class="v">%s</span></div>' % (k, v)
                   for k, v in f["rows"])
    fases_html += (
        '<div class="fase" style="--c:%s">'
        '<div class="head"><div class="n">%s</div><h2>%s</h2><div class="mide">%s</div></div>'
        '<div class="diag">%s</div><div class="rows">%s</div><div class="gate">%s</div></div>'
        % (f["c"], f["n"], f["tit"], f["mide"], f["diag"], rows, f["gate"]))

REGLAS = [
    ("tag--prot", "PROTEGIDO",
     "Si la variable se decide por <b>VENTA</b> &rarr; conjuntos separados. Meta solo ve clics y "
     "conversaciones, y esa se&ntilde;al <b>no predice la venta</b> (APR-002): si reparte solo, corona "
     "por la m&eacute;trica equivocada."),
    ("tag--libre", "LIBRE",
     "Si la variable se decide por <b>ENTREGA</b> &rarr; un solo conjunto (1-1-N). El &aacute;ngulo ya "
     "est&aacute; validado; el criterio de Meta (CTR, CPM) <b>s&iacute;</b> coincide con lo que se busca."),
    ("tag--no", "NUNCA",
     "Mover <b>&aacute;ngulo y concepto a la vez</b>. Si la ejecuci&oacute;n visual cambia junto con el "
     "&aacute;ngulo, ning&uacute;n ganador es atribuible y el testeo se pierde entero."),
    ("tag--no", "NUNCA",
     "Comparar <b>r&eacute;plicas</b> entre s&iacute; (<code>R1</code> vs <code>R3</code>). Son id&eacute;nticas "
     "por dise&ntilde;o: la diferencia es ruido de Poisson. Se <b>suman</b>, no se comparan."),
]
reglas_html = "".join(
    '<div class="regla"><span class="tag %s">%s</span><span class="txt">%s</span></div>' % r
    for r in REGLAS)

CUENTAS = [
    ("FASE 1 &middot; &aacute;ngulos", "GTR1", "S&iacute;", "Se decide por conversaci&oacute;n y frecuencia &rarr; necesita lectura autom&aacute;tica"),
    ("FASE 2 &middot; conceptos", "GTR7 + GTR1", "S&iacute;", "A y B en una, la r&eacute;plica C en la otra &rarr; sin auto-subasta"),
    ("FASE 3 &middot; escalado", "GTR13 / CP1", "No", "Se mide por ventas de LucidSales; el MCP no hace falta"),
    ("&mdash;", "GTR0", "&mdash;", "<b>Fuera</b> hasta resolver el cobro <code>UNSETTLED</code> (APR-058)"),
]
cuentas_html = "".join("<tr><td><b>%s</b></td><td><code>%s</code></td><td>%s</td><td>%s</td></tr>" % c
                       for c in CUENTAS)

DOC = """<title>Estructura del sistema &middot; VitalCom</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>%s%s</style>
<div class="wrap">

<header>
  <h1>Estructura del sistema</h1>
  <span class="meta">arquitectura de 3 fases</span>
  <span class="spacer"></span>
  <a class="nav" href="../VISTAS/PANEL.html" target="_top">&uarr; Panel del sistema</a>
  <span class="meta">rev. %s</span>
</header>

<p class="lead">Cada fase mueve <b>una sola variable</b> y deja fija la anterior. Ese es todo el
sistema: primero se encuentra el <b>dolor</b> que engancha, despu&eacute;s la <b>forma</b> de
mostrarlo, y solo entonces se mete plata. Saltarse una fase es escalar algo que nadie valid&oacute;. <b>A2</b> y <b>C7</b> son ejemplos: el &aacute;ngulo y el concepto que hayan ganado en la fase anterior.</p>

<div class="fases">%s</div>

<div class="split">
  <div class="card">
    <h3>La regla que decide la estructura</h3>
    %s
  </div>
  <div class="card">
    <h3>Qu&eacute; cuenta usa cada fase</h3>
    <table>
      <tr><th>Fase</th><th>Cuenta</th><th>MCP</th><th>Por qu&eacute;</th></tr>
      %s
    </table>
  </div>
</div>

<p class="foot">Doctrina: _ROADMAP/ANALISIS_MENTOR_CALET_115_vs_SISTEMA_2026-08-21.md &sect;9
&middot; conceptos: Ads/_SWIPE/_CATALOGO_CONCEPTOS.md PARTE III
&middot; regenerar: python Ads/_TOOLS/gen_estructura.py</p>

</div>
""" % (TOKENS, CSS, HOY, fases_html, reglas_html, cuentas_html)

io.open(SALIDA, "w", encoding="utf-8").write(DOC)
print("escrito:", SALIDA)
