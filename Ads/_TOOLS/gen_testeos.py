# -*- coding: utf-8 -*-
"""gen_testeos.py — genera PRODUCTOS/_TESTEOS.html, el registro visual de experimentos.

QUE ES
La bitacora de que se testeo, contra que, y si ya se puede declarar un ganador.
Cada test tiene BRAZOS (uno por concepto/variante) y cada brazo se mide contra el
mismo angulo, formato y precio: lo unico que cambia es la variable declarada.

DE DONDE SALEN LOS NUMEROS  (regla madre: un dato, un dueno)
  · PRODUCTOS/_TESTEOS.csv      -> la DEFINICION de cada test y sus brazos (se edita a mano)
  · PRODUCTOS/_FACT_VENTAS.csv  -> las VENTAS y el GASTO. Fuente unica. Nada se hardcodea.
El JOIN es por `conjuntos_meta` (uno o varios nombres de conjunto separados por |).
Mientras ese campo este vacio, el brazo se muestra como PLANIFICADO y sin numeros.

EL MEDIDOR DE EVIDENCIA
Es la parte importante. Las ventas por conjunto son ruido de Poisson casi puro (regla 6
del orquestador). Declarar ganador con 1-3 ventas es reaccionar al azar. La pagina calcula
cuantas ventas por brazo hacen falta y NO deja coronar hasta llegar:
     ~10 ventas/brazo -> detecta que uno sea 3x mejor
     ~25 ventas/brazo -> detecta que uno sea 2x mejor
     ~80 ventas/brazo -> detecta que uno sea 1.5x mejor
Salen de la potencia para comparar dos tasas de Poisson (alfa 5%, potencia 80%).

USO
    python Ads/_TOOLS/gen_testeos.py
    python Ads/_TOOLS/gen_testeos.py --liviano     # rutas relativas en vez de base64
"""
import csv, io, os, sys, base64, datetime
from collections import defaultdict, OrderedDict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mercado

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(BASE)
PORTABLE = "--liviano" not in sys.argv

TESTEOS = "PRODUCTOS/_TESTEOS.csv"
VENTAS  = "PRODUCTOS/_FACT_VENTAS.csv"
BANCO   = "Ads/_SWIPE/_BANCO_CREATIVOS"
SALIDA  = "PRODUCTOS/_TESTEOS.html"

UMBRALES = [(10, "3x"), (25, "2x"), (80, "1.5x")]
# La tasa USD -> moneda local es la DEL PRODUCTO del test (_DIM_PRODUCTOS.tasa) y la moneda sale de su
# mercado (mercado.py): no hay tasa ni simbolo por defecto. Un test cuyo producto no declara tasa se
# dibuja sin CPA (aviso en stderr); nunca se asume la de GT.


def f(x):
    try:
        return float(x)
    except Exception:
        return 0.0


def img64(rel):
    # Un brazo sin creativo_ref no tiene imagen. Sin este corte, el join daba la
    # carpeta del banco con barra al final, os.path.exists decia True (existe, es
    # un directorio) y el open explotaba: gen_testeos.py no podia regenerarse.
    if not rel:
        return None
    p = os.path.join(BANCO, rel)
    if not os.path.isfile(p):
        return None
    if not PORTABLE:
        return os.path.relpath(p, "PRODUCTOS").replace("\\", "/")
    with open(p, "rb") as fh:
        return "data:image/jpeg;base64," + base64.b64encode(fh.read()).decode("ascii")


# ---------- datos ----------
if not os.path.exists(TESTEOS):
    sys.exit("No existe %s" % TESTEOS)
filas = list(csv.DictReader(io.open(TESTEOS, encoding="utf-8")))

ventas_por_conjunto = defaultdict(lambda: [0.0, 0.0])   # conjunto -> [ventas, spend]
if os.path.exists(VENTAS):
    for r in csv.DictReader(io.open(VENTAS, encoding="utf-8")):
        if r.get("rol_ventana", "").upper() != "BASE":
            continue
        k = r.get("conjunto", "")
        ventas_por_conjunto[k][0] += f(r.get("ventas", 0))
        ventas_por_conjunto[k][1] += f(r.get("spend_usd", 0))

tests = OrderedDict()
for r in filas:
    tests.setdefault(r["test_id"], {"meta": r, "brazos": []})["brazos"].append(r)

with io.open("PRODUCTOS/_DIM_PRODUCTOS.csv", encoding="utf-8-sig", newline="") as _fh:
    _productos = {(p.get("producto_key") or "").strip(): p for p in csv.DictReader(_fh)}


def _moneda_del_test(t):
    """(tasa, simbolo) del producto del test; tasa None si no la declara (aviso, sin CPA)."""
    pk = (t["meta"].get("producto_key") or "").strip()
    fila = _productos.get(pk) or {"producto_key": pk}
    try:
        simbolo = mercado.perfil_de_fila(fila)["simbolo"]
    except mercado.MercadoError as error:
        sys.exit("BLOQUEANTE gen_testeos: %s" % error)
    try:
        return mercado.tasa_de_fila(fila), simbolo
    except mercado.TasaFaltante as error:
        print("AVISO gen_testeos: test %s sin CPA: %s" % (t["meta"].get("test_id"), error), file=sys.stderr)
        return None, simbolo


for t in tests.values():
    t["tasa"], t["simbolo"] = _moneda_del_test(t)
    for b in t["brazos"]:
        v = s = 0.0
        conj = [c.strip() for c in (b.get("conjuntos_meta") or "").split("|") if c.strip()]
        for c in conj:
            v += ventas_por_conjunto[c][0]
            s += ventas_por_conjunto[c][1]
        b["_ventas"], b["_spend"], b["_conj"] = v, s, conj
        b["_cpa"] = (s / v * t["tasa"]) if (v and t["tasa"]) else None


# ---------- html ----------
def card_test(tid, t):
    m = t["meta"]; brazos = t["brazos"]
    tv = sum(b["_ventas"] for b in brazos)
    ts = sum(b["_spend"] for b in brazos)
    minv = min((b["_ventas"] for b in brazos), default=0)
    corr = [b["_cpa"] for b in brazos if b["_cpa"]]

    nivel, alcanzado = None, 0
    for need, eff in UMBRALES:
        if minv >= need:
            nivel, alcanzado = eff, need
    prox = next((n for n, _ in UMBRALES if minv < n), None)
    pct = min(100, int(minv * 100 / prox)) if prox else 100

    if nivel:
        vd = ('<div class="vd ok">Ya se puede leer una diferencia de <b>%s</b> o mas '
              '(minimo %d ventas por brazo)</div>' % (nivel, alcanzado))
    else:
        falta = UMBRALES[0][0] - minv
        vd = ('<div class="vd no">Todavia NO se puede coronar. El brazo mas flojo tiene '
              '<b>%d</b> ventas; hacen falta <b>%d</b> para detectar siquiera un 3x '
              '(faltan %d).</div>' % (minv, UMBRALES[0][0], max(0, int(falta))))

    # aviso si varios brazos comparten concepto_key
    porcpt = defaultdict(list)
    for b in brazos:
        porcpt[b["concepto_key"]].append(b["brazo_nombre"])
    avisos = ""
    rep = {k: v for k, v in porcpt.items() if len(v) > 1}
    if rep:
        det = " · ".join("%s (%s)" % (k, ", ".join(v)) for k, v in rep.items())
        avisos = ('<div class="warn">⚠ <b>%d de %d brazos comparten el mismo <code>concepto_key</code></b> — %s.<br>'
                  'Este test mide <b>variante</b> (cuanta informacion lleva el creativo), no <b>concepto</b>. '
                  'Es una pregunta valida, pero no valida el catalogo.</div>'
                  % (sum(len(v) for v in rep.values()), len(brazos), det))

    filas_b = ""
    for b in sorted(brazos, key=lambda x: x["brazo_key"]):
        src = img64(b.get("creativo_ref", ""))
        thumb = ('<img src="%s" alt="">' % src) if src else '<div class="noimg">sin referencia</div>'
        if b["_ventas"]:
            nums = ('<div class="n"><span>%d</span>ventas</div>'
                    '<div class="n"><span>$%.0f</span>gastado</div>'
                    '<div class="n cpa"><span>%s</span>CPA real</div>'
                    % (b["_ventas"], b["_spend"],
                       ("%s%.0f" % (t["simbolo"], b["_cpa"])) if b["_cpa"] else "sin tasa"))
            barra = ""
            if corr and b["_cpa"]:
                mejor = min(corr)
                ratio = mejor / b["_cpa"]
                barra = '<div class="bar"><i style="width:%d%%"></i></div>' % int(ratio * 100)
        else:
            nums = '<div class="n vacio"><span>—</span>sin datos todavia</div>'
            barra = ""
        conj = ("<div class=\"cj\">conjuntos: %s</div>" % " · ".join(b["_conj"])) if b["_conj"] else \
               "<div class=\"cj pend\">sin conjuntos asignados — asignalos en _TESTEOS.csv</div>"
        filas_b += (
            '<div class="brazo">'
            '<div class="th">%s</div>'
            '<div class="info">'
            '<div class="bk">%s</div><div class="bn">%s</div>'
            '<div class="tags"><span class="tg">%s</span><span class="tg v">%s</span></div>'
            '<div class="nums">%s</div>%s%s'
            '<div class="nt">%s</div>'
            '</div></div>'
        ) % (thumb, b["brazo_key"], b["brazo_nombre"], b["concepto_key"],
             b.get("variante", ""), nums, barra, conj, b.get("notas", ""))

    est = m.get("estado", "").upper()
    return (
        '<section class="test">'
        '<div class="hd"><span class="tid">%s</span><h2>%s</h2><span class="est e-%s">%s</span></div>'
        '<div class="hip">%s</div>'
        '<div class="fijos">'
        '<span><b>producto</b> %s</span><span><b>variable</b> %s</span>'
        '<span><b>angulo fijo</b> %s</span><span><b>formato fijo</b> %s</span><span><b>inicio</b> %s</span>'
        '</div>%s'
        '<div class="ev"><div class="evt">Evidencia acumulada — brazo mas flojo: <b>%d</b> ventas</div>'
        '<div class="prog"><i style="width:%d%%"></i></div>'
        '<div class="hitos"><span>10 = detecta 3x</span><span>25 = detecta 2x</span><span>80 = detecta 1.5x</span></div>'
        '%s</div>'
        '<div class="brazos">%s</div>'
        '<div class="tot">total del test: <b>%d</b> ventas · <b>$%.0f</b> gastado</div>'
        '</section>'
    ) % (tid, m["test_nombre"], est.lower(), est, m.get("hipotesis", ""),
         m.get("producto_key", ""), m.get("variable", ""), m.get("angulo_fijo", ""),
         m.get("formato_fijo", ""), m.get("fecha_inicio", ""), avisos,
         int(minv), pct, vd, filas_b, int(tv), ts)


CSS = """
:root{--bg:#0e1116;--fg:#e6edf3;--mut:#8b98a5;--card:#161b22;--bd:#30363d;--sel:#4f8cff;--ok:#3fb950;--no:#e5534b;--wr:#d29922}
*{box-sizing:border-box}
body{background:var(--bg);color:var(--fg);font:14px/1.5 system-ui,-apple-system,sans-serif;margin:0;padding:22px 22px 60px}
h1{font-size:21px;margin:0 0 4px}
.sub{color:var(--mut);font-size:13px;margin-bottom:22px}
.test{background:var(--card);border:1px solid var(--bd);border-radius:12px;padding:18px 20px;margin-bottom:22px}
.hd{display:flex;align-items:center;gap:11px;margin-bottom:8px;flex-wrap:wrap}
.hd h2{font-size:17px;margin:0;flex:1}
.tid{background:#21262d;color:var(--mut);border-radius:5px;padding:2px 8px;font-size:12px;font-weight:700}
.est{font-size:11px;font-weight:700;padding:3px 9px;border-radius:11px;text-transform:uppercase;letter-spacing:.5px}
.e-planificado{background:#1c2331;color:#79a6ff}
.e-encurso{background:#3d2a10;color:#e3b341}
.e-cerrado{background:#12291c;color:#5fd47f}
.hip{color:var(--mut);font-size:13px;font-style:italic;margin-bottom:12px}
.fijos{display:flex;flex-wrap:wrap;gap:7px;margin-bottom:14px}
.fijos span{background:#0b0d10;border:1px solid var(--bd);border-radius:6px;padding:4px 10px;font-size:11.5px;color:var(--mut)}
.fijos b{color:var(--fg);text-transform:uppercase;font-size:10px;letter-spacing:.5px;margin-right:5px}
.warn{background:#2a1f0a;border:1px solid #6b5117;color:#e3b341;border-radius:8px;padding:10px 13px;font-size:12.5px;margin-bottom:14px;line-height:1.5}
.warn code{background:#0b0d10;padding:1px 5px;border-radius:3px}
.ev{background:#0b0d10;border:1px solid var(--bd);border-radius:9px;padding:13px 15px;margin-bottom:16px}
.evt{font-size:12.5px;color:var(--mut);margin-bottom:8px}
.evt b{color:var(--fg);font-size:15px}
.prog{height:7px;background:#21262d;border-radius:4px;overflow:hidden}
.prog i{display:block;height:100%;background:linear-gradient(90deg,#d29922,#3fb950)}
.hitos{display:flex;justify-content:space-between;color:var(--mut);font-size:10.5px;margin-top:5px}
.vd{margin-top:11px;font-size:12.5px;border-radius:6px;padding:8px 11px;line-height:1.45}
.vd.ok{background:#0f2417;color:#5fd47f}
.vd.no{background:#2a1416;color:#f08d86}
.brazos{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:14px}
.brazo{background:#0b0d10;border:1px solid var(--bd);border-radius:9px;overflow:hidden;display:flex;flex-direction:column}
.th{background:#000;display:flex;align-items:center;justify-content:center;min-height:120px}
.th img{width:100%;height:auto;display:block}
.noimg{color:var(--mut);font-size:11px;padding:36px 0}
.info{padding:11px 12px 12px}
.bk{color:var(--sel);font-size:10.5px;font-weight:700;letter-spacing:1px}
.bn{font-weight:600;margin-bottom:6px}
.tags{display:flex;gap:5px;flex-wrap:wrap;margin-bottom:8px}
.tg{background:#1c2331;color:#79a6ff;border-radius:4px;padding:1px 7px;font-size:10px;font-weight:600}
.tg.v{background:#21262d;color:var(--mut)}
.nums{display:flex;gap:13px;margin-bottom:7px}
.n{font-size:10px;color:var(--mut);text-transform:uppercase;letter-spacing:.4px}
.n span{display:block;font-size:17px;color:var(--fg);font-weight:700;letter-spacing:0;text-transform:none}
.n.cpa span{color:#5fd47f}
.n.vacio span{color:var(--mut)}
.bar{height:5px;background:#21262d;border-radius:3px;overflow:hidden;margin-bottom:7px}
.bar i{display:block;height:100%;background:var(--ok)}
.cj{color:var(--mut);font-size:10.5px;margin-bottom:4px}
.cj.pend{color:var(--wr)}
.nt{color:var(--mut);font-size:11px;line-height:1.4}
.tot{margin-top:13px;padding-top:11px;border-top:1px solid var(--bd);color:var(--mut);font-size:12px}
.tot b{color:var(--fg)}
.nota{background:var(--card);border:1px solid var(--bd);border-radius:9px;padding:13px 16px;color:var(--mut);font-size:12.5px;line-height:1.6}
.nota b{color:var(--fg)}
"""

cards = "".join(card_test(tid, t) for tid, t in tests.items())
HTML = (u'<!doctype html><meta charset="utf-8"><title>TESTEOS - registro de experimentos</title>'
        u'<style>%s</style>'
        u'<h1>REGISTRO DE TESTEOS</h1>'
        u'<div class="sub">%d test(s) · se regenera con <code>python Ads/_TOOLS/gen_testeos.py</code> · %s</div>'
        u'%s'
        u'<div class="nota"><b>Como se lee esta pagina.</b> Cada test fija todo (angulo, formato, precio, pagina) '
        u'menos una variable, y compara los brazos por <b>CPA real en Q</b> — nunca por CTR ni por %% de conversacion: '
        u'evidencia propia dice que un conjunto con 78%% de conversacion puede dar 0 ventas. '
        u'El medidor de evidencia sale de la potencia estadistica para comparar dos tasas de Poisson; '
        u'mientras la barra no llegue, un brazo que va adelante puede ir adelante por azar. '
        u'Los brazos se agregan por <code>concepto_key</code>, y las replicas <code>R[N]</code> se <b>suman</b>, nunca se comparan. '
        u'<br><br>Las ventas y el gasto salen de <code>_FACT_VENTAS.csv</code> (fuente unica) haciendo JOIN por '
        u'<code>conjuntos_meta</code>. La definicion de los tests se edita a mano en <code>_TESTEOS.csv</code>.</div>'
        ) % (CSS, len(tests), datetime.date.today().isoformat(), cards)

io.open(SALIDA, "w", encoding="utf-8").write(HTML)
print("%s escrito (%d KB) — %d test(s), %d brazos"
      % (SALIDA, len(HTML.encode("utf-8")) // 1024, len(tests), len(filas)))
for tid, t in tests.items():
    v = sum(b["_ventas"] for b in t["brazos"])
    print("  %s  %-38s %s  %d brazos  %d ventas"
          % (tid, t["meta"]["test_nombre"][:38], t["meta"]["estado"], len(t["brazos"]), v))
