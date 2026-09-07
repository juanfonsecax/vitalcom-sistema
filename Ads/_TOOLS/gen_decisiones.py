#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen_decisiones.py — reconstruye el warehouse, corre el motor y dibuja VISTAS/DECISIONES.html.

Es el unico camino por el que una orden de pausar o escalar llega al operador. Si el motor dice
que no se puede decidir, la vista lo muestra como tal: no hay forma de que una decision bloqueada
se convierta en una orden por el camino de la interfaz.
"""
import os, sys, io, json, html, subprocess, datetime

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, OSError):
    pass

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WH = os.path.join(BASE, "warehouse")
JSON = os.path.join(BASE, "PRODUCTOS", "_DECISIONES.json")
OUT = os.path.join(BASE, "VISTAS", "DECISIONES.html")

COLOR = {
    "ESCALAR":                 ("#0b7a3b", "#e6f5ec", "ESCALAR"),
    "PAUSAR":                  ("#a11", "#fdeaea", "PAUSAR"),
    "SEGUIR_MIDIENDO":         ("#7a5a00", "#fdf4e0", "SEGUIR MIDIENDO"),
    "INDECIDIBLE_ESTRUCTURAL": ("#4a4a6a", "#eeeef6", "EL CPA NO DECIDE"),
    "SIN_DATA":                ("#666", "#f0f0f0", "SIN DATA"),
}


def correr(cmd, cwd, env=None):
    e = dict(os.environ, PYTHONIOENCODING="utf-8", **(env or {}))
    r = subprocess.run(cmd, cwd=cwd, env=e, shell=True,
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def main():
    # Intento opcional de dbt build si existe el warehouse
    rc, log = correr("python -m dbt.cli.main build --no-use-colors", WH, {"DBT_PROFILES_DIR": "."})
    if rc == 0:
        linea = next((l for l in log.splitlines() if "PASS=" in l), "(sin resumen)")
        print("  dbt build ->", linea.strip()[-70:])
    else:
        print("  ! aviso: dbt no corrió o falló; decidir_operativo usará fallback directo sobre CSVs")

    rc, log = correr("python Ads/_TOOLS/decidir.py", BASE)
    if rc != 0:
        print(log[-1500:]); return 1

    rep = json.load(io.open(JSON, encoding="utf-8"))
    e = html.escape
    p = []
    p.append("<style>"
             "body{font:14px/1.5 system-ui,sans-serif;margin:0;padding:20px;background:#fafaf8;color:#1a1a1a}"
             "h1{font-size:19px;margin:0 0 4px}.sub{color:#666;font-size:12px;margin-bottom:18px}"
             "h2{font-size:15px;margin:22px 0 8px;border-bottom:1px solid #ddd;padding-bottom:4px}"
             "table{border-collapse:collapse;width:100%;margin-bottom:6px}"
             "th{text-align:left;font-size:11px;text-transform:uppercase;color:#777;"
             "border-bottom:1px solid #ddd;padding:5px 8px;font-weight:600}"
             "td{padding:7px 8px;border-bottom:1px solid #eee;vertical-align:top}"
             ".n{text-align:right;font-variant-numeric:tabular-nums}"
             ".chip{display:inline-block;padding:2px 8px;border-radius:10px;font-size:11px;font-weight:700}"
             ".por{color:#555;font-size:12px}.acc{color:#1a4a7a;font-size:12px;margin-top:3px}"
             ".al{color:#a11;font-size:11px;margin-top:3px}"
             ".ft{margin-top:24px;padding:12px;background:#f0efe9;border-radius:6px;font-size:12px;color:#444}"
             "</style>")
    p.append("<h1>Decisiones</h1>")
    p.append("<div class=sub>ventana FIJA de %d dias &middot; intervalo de credibilidad %.0f%% &middot; "
             "grano: %s &middot; generado %s<br>"
             "La ventana no se elige al mirar el dato: sale de <code>_PARAMETROS_DECISION.csv</code>."
             "</div>" % (rep["ventana_dias"], rep["nivel_confianza"] * 100, rep["grano"],
                         e(rep["generado"])))
    ordenes = bloq = 0
    for pr in rep["productos"]:
        if pr.get("estado") == "SIN_BREAK_EVEN":
            p.append("<h2>%s</h2><div class=al>%s</div>" % (e(pr["producto_key"]), e(pr["por_que"])))
            continue
        p.append("<h2>%s <span style='font-weight:400;color:#777;font-size:12px'>"
                 "&middot; %s &middot; break-even Q%.2f</span></h2>"
                 % (e(pr["producto_key"]), e(str(pr.get("estado_producto"))), pr["break_even_q"]))
        p.append("<table><tr><th>Celda</th><th class=n>Ventas</th><th class=n>Msj</th>"
                 "<th class=n>Gasto $</th><th>CPA Q [IC 95%]</th><th>Estado</th></tr>")
        orden = {"PAUSAR": 0, "ESCALAR": 1, "INDECIDIBLE_ESTRUCTURAL": 2, "SEGUIR_MIDIENDO": 3}
        for c in sorted(pr["celdas"], key=lambda x: orden.get(x["estado"], 9)):
            fg, bg, txt = COLOR.get(c["estado"], ("#333", "#eee", c["estado"]))
            ic = c.get("ic")
            ictxt = ("<b>%s</b> <span style='color:#888'>[%s &ndash; %s]</span>"
                     % (ic[1] if ic[1] else "&infin;", ic[0], ic[2] if ic[2] else "&infin;")) if ic else "&mdash;"
            extra = "<div class=por>%s</div>" % e(c["por_que"])
            if c.get("accion_sugerida"):
                extra += "<div class=acc>&rarr; %s</div>" % e(c["accion_sugerida"])
            if not c.get("banda_ok"):
                extra += "<div class=al>&#9888; alguna replica corre en banda distinta a la de su avatar</div>"
            if not c.get("nombres_ok"):
                extra += "<div class=al>&#9888; algun conjunto fuera de la convencion de nombres</div>"
            p.append("<tr><td><b>%s</b>%s</td><td class=n>%.0f</td><td class=n>%.0f</td>"
                     "<td class=n>%.2f</td><td>%s</td>"
                     "<td><span class=chip style='color:%s;background:%s'>%s</span></td></tr>"
                     % (e(c["celda"]), extra, c["ventas"], c["mensajes"], c["spend_usd"],
                        ictxt, fg, bg, txt))
            if c["estado"] in ("PAUSAR", "ESCALAR"): ordenes += 1
            elif c["estado"] in ("SEGUIR_MIDIENDO", "INDECIDIBLE_ESTRUCTURAL"): bloq += 1
        p.append("</table>")
    p.append("<div class=ft><b>%d orden(es) emitidas &middot; %d decision(es) bloqueadas.</b><br>"
             "Una decision bloqueada no es una falla: es el motor negandose a responder una pregunta "
             "que la data no puede responder. <b>EL CPA NO DECIDE</b> significa que el CPA observado esta "
             "tan cerca del break-even que ni con %d ventas el intervalo dejaria de cruzarlo; en ese caso "
             "se decide por CIERRE, y el cierre CORTA pero nunca corona.</div>"
             % (ordenes, bloq, rep["horizonte_ventas"]))
    io.open(OUT, "w", encoding="utf-8").write("\n".join(p))
    print("  escrito VISTAS/DECISIONES.html  ·  %d ordenes, %d bloqueadas" % (ordenes, bloq))
    return 0


if __name__ == "__main__":
    sys.exit(main())
