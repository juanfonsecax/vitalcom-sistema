# -*- coding: utf-8 -*-
"""flujo_html.py — dibuja VISTAS/FLUJO.html a partir de PRODUCTOS/_FLUJO.json.

No decide nada: cada estado, gate y aviso viene calculado por flujo.py. Esta página solo lo
muestra — "estás acá · esto bloquea · esto sigue" — por producto, y el grafo del sistema en
mermaid renderizado desde el MISMO JSON que ejecuta el runner, para que el dibujo no se pueda
desincronizar del flujo.

La declara VISTAS/_MANIFIESTO.json como vista iframe; la escribe `flujo.py --todo`.
"""
import html
import json


def _e(s):
    return html.escape("" if s is None else str(s))


CSS = """
:root{--bg:#0d1117;--panel:#161b22;--line:#30363d;--txt:#e6edf3;--dim:#8b949e;--ok:#3fb950;--warn:#d29922;--bad:#f85149;--info:#58a6ff;--mark:#a371f7}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--txt);font:14px/1.5 -apple-system,Segoe UI,Roboto,sans-serif;padding:20px 24px}
h1{font-size:20px;margin:0 0 4px}h1 small{color:var(--dim);font-weight:400;font-size:13px;margin-left:10px}
.sub{color:var(--dim);margin-bottom:18px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(420px,1fr));gap:14px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:14px 16px}
.card h2{font-size:15px;margin:0 0 2px;display:flex;justify-content:space-between;gap:8px}
.card h2 .est{font-size:11px;padding:2px 8px;border-radius:10px;border:1px solid var(--line);color:var(--dim);white-space:nowrap}
.fase{color:var(--info);font-weight:600;margin:6px 0 8px;font-size:13px}
.nodo{display:grid;grid-template-columns:18px 1fr;gap:6px;padding:3px 0;border-top:1px solid var(--line);font-size:13px}
.nodo:first-of-type{border-top:0}
.nodo .m{text-align:center;font-weight:700}.ok .m{color:var(--ok)}.pend .m{color:var(--dim)}.bloq .m{color:var(--bad)}.listo .m{color:var(--info)}
.nodo.actual{background:rgba(88,166,255,.08);border-radius:6px;padding:6px 6px}
.nodo .t{color:var(--txt)}.nodo .id{color:var(--dim);font-family:ui-monospace,Menlo,monospace;font-size:11px}
.det{color:var(--dim);font-size:12px;margin-left:2px}.det b{color:var(--txt);font-weight:600}
.det .falta{color:var(--warn)}.det .bloq{color:var(--bad)}.det .ej{color:var(--info)}
.aviso{color:var(--warn);font-size:12px;margin:2px 0 0 24px}
.avance{margin-top:10px;padding-top:8px;border-top:1px dashed var(--line);font-size:12px}
.avance .g{font-weight:600}.avance .ok{color:var(--ok)}.avance .no{color:var(--bad)}
.ordenes{margin-top:8px;font-size:12px}.ordenes span{display:inline-block;padding:1px 7px;border-radius:8px;margin:2px 4px 2px 0;border:1px solid var(--line)}
.ordenes .PAUSAR{color:var(--bad)}.ordenes .ESCALAR{color:var(--ok)}.ordenes .RENOVAR{color:var(--mark)}
.excep{color:var(--warn)}
.grafo{margin-top:26px;background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:14px}
.grafo h3{margin:0 0 8px;font-size:14px}
pre.mermaid{background:transparent;overflow-x:auto}
.leyenda{color:var(--dim);font-size:12px;margin-top:10px}
"""

MARCA = {"CUMPLIDO": ("✓", "ok"), "PENDIENTE": ("·", "pend"), "BLOQUEADO": ("✗", "bloq"),
         "LISTO_PARA_EJECUTAR": ("▶", "listo"), "NO_APLICA": ("—", "pend")}


def _nodo(n, actual, estado_prod):
    m, cls = MARCA.get(n["estado"], ("·", "pend"))
    es_actual = (n["id"] == actual) and estado_prod != "AL_DIA"
    partes = ['<div class="nodo %s%s"><div class="m">%s</div><div>' % (cls, " actual" if es_actual else "", m)]
    partes.append('<div class="t">%s <span class="id">%s</span>%s</div>'
                  % (_e(n["titulo"]), _e(n["id"]), ' <span class="id">(fuera de orden: ya existe)</span>' if n.get("fuera_de_orden") else ""))
    if es_actual:
        for x in ([] if n.get("requiere_es_produce") else n.get("produce", [])):
            if not x["ok"]:
                partes.append('<div class="det"><span class="falta">falta</span> <b>%s</b> — %s<br>&nbsp;&nbsp;lo produce: %s%s</div>'
                              % (_e(x["dato"]), _e(x["observado"]), _e(x.get("dueno")),
                                 (" <i>(%s)</i>" % _e(x["regla"])) if x.get("regla") else ""))
        for x in n.get("requiere", []):
            if x["ok"] is False:
                partes.append('<div class="det"><span class="bloq">BLOQUEA</span> <b>%s</b> — %s<br>&nbsp;&nbsp;lo produce: %s%s</div>'
                              % (_e(x["dato"]), _e(x["observado"]), _e(x.get("dueno")),
                                 (" <i>(%s)</i>" % _e(x["regla"])) if x.get("regla") else ""))
        partes.append('<div class="det"><span class="ej">ejecutar:</span> %s</div>' % _e(n["ejecutor"]))
        if n.get("como"):
            partes.append('<div class="det">%s</div>' % _e(n["como"]))
        if n.get("secuencia"):
            partes.append('<div class="det">secuencia: %s</div>' % _e(" → ".join(n["secuencia"])))
    elif n["estado"] == "PENDIENTE" and not n.get("ciclo"):
        for x in n.get("produce", []):
            if not x["ok"]:
                partes.append('<div class="det"><span class="falta">falta</span> %s — %s</div>'
                              % (_e(x["dato"]), _e(x["observado"])))
    partes.append("</div></div>")
    for a in n.get("avisos", []):
        partes.append('<div class="aviso">⚠ %s — %s</div>' % (_e(a["dato"]), _e(a["observado"])))
    return "".join(partes)


def _producto(r):
    H = ['<div class="card">']
    H.append('<h2>%s <span class="est">%s · %s</span></h2>' % (_e(r["producto_key"]), _e(r.get("estado_producto")), _e(r.get("cuenta") or "sin cuenta")))
    H.append('<div class="sub" style="margin-bottom:6px">%s</div>' % _e(r.get("nombre")))
    if r.get("estado") == "EXCEPCION":
        H.append('<div class="fase excep">%s</div><div class="det">%s</div><div class="det">observado: %s</div></div>'
                 % (_e(r.get("nodo_actual")), _e(r.get("mensaje")), _e(r.get("observado"))))
        return "".join(H)
    H.append('<div class="fase">%s</div>' % _e(r.get("fase_titulo")))
    for n in r.get("nodos", []):
        H.append(_nodo(n, r.get("nodo_actual"), r.get("estado")))
    if r.get("estado") == "AL_DIA":
        H.append('<div class="det" style="margin-top:6px;color:var(--ok)">▶ todo cumplido: en ciclo y al día</div>')
    a = r.get("avance")
    if a:
        H.append('<div class="avance"><span class="g">Para pasar a %s:</span> <span class="%s">%s</span> %s<br><span class="det">regla: %s</span></div>'
                 % (_e(a["a"]), "ok" if a["ok"] else "no", "LISTO" if a["ok"] else "todavía no", _e(a["observado"]), _e(a.get("regla"))))
    if r.get("ordenes"):
        m = r.get("motor") or {}
        H.append('<div class="ordenes">Órdenes del motor (data hasta %s, rezago %s d): ' % (_e(m.get("datos_hasta")), _e(m.get("rezago_dias"))))
        for o in r["ordenes"]:
            H.append('<span class="%s" title="%s">%s · %s</span>' % (_e(o["estado"]), _e(o.get("accion")), _e(o["estado"]), _e(o["celda"])))
        H.append("</div>")
    for av in r.get("avisos", []):
        H.append('<div class="aviso">⚠ %s</div>' % _e(av))
    H.append("</div>")
    return "".join(H)


def HTML(estado):
    prods = estado.get("productos", [])
    resumen = {}
    for r in prods:
        resumen[r.get("fase")] = resumen.get(r.get("fase"), 0) + 1
    H = ["<!doctype html><html lang='es'><head><meta charset='utf-8'><title>Flujo del sistema</title>",
         "<style>%s</style></head><body>" % CSS,
         "<h1>Flujo del sistema <small>generado %s · flujo v%s</small></h1>" % (_e(estado.get("generado")), _e(estado.get("flujo_version"))),
         "<div class='sub'>dónde está cada producto, qué lo bloquea y qué sigue — calculado por flujo.py sobre los CSV, nunca escrito a mano · %s</div>"
         % _e(" · ".join("%s: %d" % (k, v) for k, v in sorted(resumen.items(), key=lambda kv: str(kv[0])))),
         "<div class='grid'>"]
    H.extend(_producto(r) for r in prods)
    H.append("</div>")
    H.append("<div class='grafo'><h3>El grafo declarado (DOCTRINA/FLUJO.json)</h3>")
    H.append("<pre class='mermaid'>%s</pre>" % _e(estado.get("grafo_mermaid", "")))
    H.append("<div class='leyenda'>✓ cumplido · ▶ listo para ejecutar · ✗ bloqueado · · pendiente. Los gates son predicados sobre la data; si uno no está en el vocabulario de flujo.py, no es un gate.</div></div>")
    H.append("<script type='module'>import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';"
             "mermaid.initialize({startOnLoad:true,theme:'dark'});</script>")
    H.append("</body></html>")
    return "".join(H)


if __name__ == "__main__":
    import io, os, sys
    base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    with io.open(os.path.join(base, "PRODUCTOS", "_FLUJO.json"), encoding="utf-8") as fh:
        est = json.load(fh)
    with io.open(os.path.join(base, "VISTAS", "FLUJO.html"), "w", encoding="utf-8") as fh:
        fh.write(HTML(est))
    print("escrito VISTAS/FLUJO.html")
