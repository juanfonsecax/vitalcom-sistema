# -*- coding: utf-8 -*-
"""
gen_metaads.py — arma `PRODUCTOS/_META_ADS.html`: el creativo que corre, con su
resultado al lado, producto por producto.

Que resuelve: `_DASHBOARD.html` responde CUANTO (numeros por angulo y cuenta).
Este responde CUAL — que pieza es la que esta vendiendo. Hoy para saberlo hay que
cruzar a mano el nombre del anuncio de `_FACT_VENTAS.csv` con un archivo suelto
en `Ads/MEDIA_*`, y por eso nadie lo hace.

EL PROBLEMA DEL VINCULO (leer antes de tocar nada):
El nombre del anuncio en Meta ("tinnidrop 3", "MA6_OFERTA", "imagen nueva - Copia")
NO es el nombre del archivo ("tinnidrop3.mp4", "NUSAVAB12_ARDOR_MA6_OFERTA.jpg").
No hay llave que los una. Este script la infiere por normalizacion + tokens y
persiste el resultado en `PRODUCTOS/_MAPEO_CREATIVOS.csv`, donde:

  metodo=AUTO      lo resolvio el script (se recalcula en cada corrida)
  metodo=MANUAL    lo escribio el operador — NUNCA se pisa
  metodo=PENDIENTE no se pudo resolver; se llena a mano poniendo el archivo
                   y cambiando el metodo a MANUAL

Las carpetas de cada producto salen de `_DIM_PRODUCTOS.csv` (regla 21: nunca
adivinar la carpeta por el nombre del producto).

Uso:  python Ads/_TOOLS/gen_metaads.py
"""
import collections
import csv
import html
import io
import os
import re
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROD = os.path.join(RAIZ, "PRODUCTOS")
ADS = os.path.join(RAIZ, "Ads")
SALIDA = os.path.join(PROD, "_META_ADS.html")
MAPEO = os.path.join(PROD, "_MAPEO_CREATIVOS.csv")

EXT_IMG = (".png", ".jpg", ".jpeg", ".webp")
EXT_VID = (".mp4", ".mov", ".webm")


def leer_csv(ruta):
    with io.open(ruta, encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def num(x, d=0.0):
    try:
        return float(str(x).strip() or d)
    except (TypeError, ValueError):
        return d


# ── vinculo anuncio -> archivo ───────────────────────────────────────────────

def normalizar(s):
    """'tinnidrop 3 - Copia 2' -> 'tinnidrop3'. Las copias son el MISMO creativo."""
    s = (s or "").lower()
    s = re.sub(r"[-–·]\s*copia\s*\d*", " ", s)
    s = re.sub(r"[^a-z0-9]+", "", s)
    return s


def tokens(s):
    """Trozos alfanumericos utiles para casar por partes: MA6, OFERTA, ARDOR."""
    s = re.sub(r"[-–·]\s*copia\s*\d*", " ", (s or "").lower())
    return {t for t in re.split(r"[^a-z0-9]+", s) if len(t) >= 3}


def inventario_media(fila_producto):
    """Todos los archivos de media del producto, con su ruta relativa a PRODUCTOS/."""
    out = []
    carpetas = []
    if fila_producto.get("carpeta_media"):
        carpetas.append(os.path.join(ADS, fila_producto["carpeta_media"]))
    if fila_producto.get("carpeta_videos"):
        carpetas.append(os.path.join(ADS, "1.1 Videos", fila_producto["carpeta_videos"]))
    for extra in (fila_producto.get("carpetas_extra") or "").split(";"):
        if extra.strip():
            carpetas.append(os.path.join(ADS, extra.strip()))

    for base in carpetas:
        if not os.path.isdir(base):
            continue
        for dirpath, _, nombres in os.walk(base):
            for n in nombres:
                if n.lower().endswith(EXT_IMG + EXT_VID):
                    absoluto = os.path.join(dirpath, n)
                    rel = os.path.relpath(absoluto, PROD).replace("\\", "/")
                    out.append({
                        "archivo": n,
                        "rel": rel,
                        "tipo": "video" if n.lower().endswith(EXT_VID) else "imagen",
                        "norm": normalizar(os.path.splitext(n)[0]),
                        "tok": tokens(os.path.splitext(n)[0]),
                    })
    return out


def vincular(anuncio, media):
    """Devuelve (rel, tipo, metodo) o (None, None, 'PENDIENTE')."""
    if not anuncio.strip():
        return None, None, "PENDIENTE"
    na = normalizar(anuncio)
    if not na:
        return None, None, "PENDIENTE"

    # 1. igualdad exacta de la forma normalizada
    for m in media:
        if m["norm"] == na:
            return m["rel"], m["tipo"], "AUTO"
    # 2. contencion (el nombre del archivo lleva prefijo de producto)
    cands = [m for m in media if na in m["norm"] or m["norm"] in na]
    if len(cands) == 1:
        return cands[0]["rel"], cands[0]["tipo"], "AUTO"
    # 3. tokens. Hacen falta DOS coincidencias, no una: el nombre del angulo
    # ("verguenza", "ardor") lo comparten TODOS los creativos de esa familia, asi
    # que con umbral 1 `VERGUENZA_MA2_VESTIDO` se casaba con
    # `VARICOSE_2_VERGUENZA-PIERNAS.mp4`, que es otro creativo. Un vinculo falso
    # es peor que un pendiente: muestra la pieza equivocada al lado de la venta.
    ta = tokens(anuncio)
    if len(ta) >= 2:
        puntuados = sorted(((len(ta & m["tok"]), m) for m in media),
                           key=lambda kv: -kv[0])
        if puntuados and puntuados[0][0] >= 2:
            mejor = puntuados[0][0]
            empatados = [m for p, m in puntuados if p == mejor]
            segundo = max((p for p, _ in puntuados if p < mejor), default=0)
            if len(empatados) == 1 and mejor > segundo:
                return empatados[0]["rel"], empatados[0]["tipo"], "AUTO"
    return None, None, "PENDIENTE"


def cargar_mapeo_previo():
    """Solo interesa conservar lo MANUAL: lo AUTO se recalcula siempre."""
    if not os.path.exists(MAPEO):
        return {}
    previo = {}
    for r in leer_csv(MAPEO):
        if (r.get("metodo") or "").strip().upper() == "MANUAL":
            previo[(r["producto_key"], r["anuncio"])] = r.get("archivo_media") or ""
    return previo


def escribir_mapeo(filas):
    """Con escritor CSV real y quoting completo (regla 22)."""
    with io.open(MAPEO, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, quoting=csv.QUOTE_ALL)
        w.writerow(["producto_key", "anuncio", "archivo_media", "tipo", "metodo",
                    "ventas", "spend_usd"])
        for f in filas:
            w.writerow([f["producto_key"], f["anuncio"], f["rel"] or "", f["tipo"] or "",
                        f["metodo"], f["ventas"], "%.2f" % f["spend_usd"]])


# ── agregacion ───────────────────────────────────────────────────────────────

def agregar_ventas():
    """Por (producto, anuncio) sobre rol_ventana=BASE — la regla de lectura de
    DATA_PLAYBOOK: solo BASE, si no se cuenta dos veces contra los CONTROL."""
    agg = collections.defaultdict(lambda: {
        "ventas": 0, "spend_usd": 0.0, "mensajes": 0, "impresiones": 0,
        "ini": "9999", "fin": "0000", "cuentas": set(), "conjuntos": set()})
    for r in leer_csv(os.path.join(PROD, "_FACT_VENTAS.csv")):
        if (r.get("rol_ventana") or "").strip().upper() != "BASE":
            continue
        k = (r["producto_key"], (r.get("anuncio") or "").strip())
        a = agg[k]
        a["ventas"] += int(num(r.get("ventas")))
        a["spend_usd"] += num(r.get("spend_usd"))
        a["mensajes"] += int(num(r.get("mensajes")))
        a["impresiones"] += int(num(r.get("impresiones")))
        a["ini"] = min(a["ini"], r.get("ventana_ini") or "9999")
        a["fin"] = max(a["fin"], r.get("ventana_fin") or "0000")
        if r.get("cuenta_alias"):
            a["cuentas"].add(r["cuenta_alias"])
        if r.get("conjunto"):
            a["conjuntos"].add(r["conjunto"])
    return agg


CSS = """
*{box-sizing:border-box}
body{margin:0;background:#0f1115;color:#e6e8ee;
     font:14px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif}
header{position:sticky;top:0;z-index:20;background:#151822;border-bottom:1px solid #262b38;
       padding:13px 22px;display:flex;gap:16px;align-items:center;flex-wrap:wrap}
h1{margin:0;font-size:16px;font-weight:650}
.sub{color:#8b93a7;font-size:12px}
.chips{display:flex;gap:6px;flex-wrap:wrap;margin-left:auto}
.chip{background:#1c2130;border:1px solid #2d3446;color:#aab2c5;border-radius:999px;
      padding:4px 11px;font-size:11.5px;cursor:pointer;user-select:none}
.chip:hover{border-color:#4a7cff;color:#e6e8ee}
.chip.on{background:#4a7cff;border-color:#4a7cff;color:#fff;font-weight:600}
main{padding:20px 22px 60px}
.prod{margin-bottom:30px;scroll-margin-top:64px}
.phead{display:flex;gap:12px;align-items:baseline;flex-wrap:wrap;
       border-left:3px solid #4a7cff;padding-left:12px;margin-bottom:5px}
.phead h2{margin:0;font-size:16px;font-weight:650}
.pill{border-radius:999px;padding:2px 9px;font-size:11px;font-weight:600}
.VIVO{background:#14401f;color:#7ee2a8}.LISTO{background:#1d3350;color:#8fb6ff}
.PAUSADO{background:#3d2a12;color:#e0a458}.INCOMPLETO{background:#3a1c22;color:#f09aa6}
.pmeta{color:#8b93a7;font-size:12px;margin:0 0 12px 15px}
.pmeta b{color:#c9d0e0;font-weight:600}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(268px,1fr));gap:14px}
.ad{background:#151822;border:1px solid #262b38;border-radius:11px;overflow:hidden;
    display:flex;flex-direction:column}
.ad.g{border-color:#2f9e5f}.ad.a{border-color:#8a6d2b}.ad.r{border-color:#8a3340}
.thumb{position:relative;background:#0b0d12;height:210px;display:flex;
       align-items:center;justify-content:center;overflow:hidden}
.thumb img,.thumb video{max-width:100%;max-height:210px;display:block}
.sinimg{color:#5c6478;font-size:11.5px;text-align:center;padding:16px;line-height:1.5}
.vbadge{position:absolute;top:7px;left:7px;background:#000a;border-radius:5px;
        padding:2px 7px;font-size:10.5px;color:#c9d0e0}
.nom{padding:8px 11px;border-bottom:1px solid #262b38;font-size:12.5px;
     color:#e6e8ee;font-weight:600;word-break:break-word}
.kpis{display:grid;grid-template-columns:1fr 1fr 1fr;gap:1px;background:#262b38}
.kpi{background:#151822;padding:8px 6px;text-align:center}
.kpi .v{font-size:15px;font-weight:700;display:block;line-height:1.25}
.kpi .l{font-size:10px;color:#8b93a7;text-transform:uppercase;letter-spacing:.4px}
.g .cpa{color:#7ee2a8}.a .cpa{color:#e0a458}.r .cpa{color:#f09aa6}
.pie{padding:7px 11px;font-size:11px;color:#8b93a7;display:flex;
     justify-content:space-between;gap:8px;flex-wrap:wrap}
.aviso{background:#1d1a10;border:1px solid #4a3d1a;color:#e0c084;border-radius:9px;
       padding:11px 14px;margin-bottom:18px;font-size:12.5px;line-height:1.6}
.aviso b{color:#f0d9a8}
.vacio{color:#8b93a7;font-size:12.5px;padding:8px 0 0 15px}
"""

JS = """
let f=null;
const chips=[...document.querySelectorAll('.chip')];
function aplicar(){
  document.querySelectorAll('.prod').forEach(p=>{
    let vis=0;
    p.querySelectorAll('.ad').forEach(a=>{
      const m=!f||a.dataset.sem===f||a.dataset.tipo===f;
      a.style.display=m?'':'none'; if(m)vis++;
    });
    p.style.display=vis?'':'none';
  });
}
chips.forEach(c=>c.addEventListener('click',()=>{
  const v=c.dataset.v;
  if(f===v){f=null;c.classList.remove('on');}
  else{chips.forEach(x=>x.classList.remove('on'));f=v;c.classList.add('on');}
  aplicar();
}));
"""


def main():
    productos = leer_csv(os.path.join(PROD, "_DIM_PRODUCTOS.csv"))
    ventas = agregar_ventas()
    previo = cargar_mapeo_previo()

    e = html.escape
    filas_mapeo, bloques = [], []
    tot_pend = tot_ads = 0

    # productos con data primero, luego el resto; dentro, por ventas
    orden = sorted(productos, key=lambda p: -sum(
        v["ventas"] for (pk, _), v in ventas.items() if pk == p["producto_key"]))

    for p in orden:
        pk = p["producto_key"]
        media = inventario_media(p)
        propios = sorted(((a, v) for (q, a), v in ventas.items() if q == pk),
                         key=lambda kv: -kv[1]["ventas"])
        if not propios:
            continue

        tasa = num(p.get("tasa"), 7.62) or 7.62
        base_q = num(p.get("cpa_base_q"))
        be_q = num(p.get("cpa_be_q"))
        estado = (p.get("estado") or "").strip().upper() or "INCOMPLETO"

        cards = []
        for anuncio, v in propios:
            tot_ads += 1
            clave = (pk, anuncio)
            if clave in previo and previo[clave]:
                rel, metodo = previo[clave], "MANUAL"
                tipo = "video" if rel.lower().endswith(EXT_VID) else "imagen"
            else:
                rel, tipo, metodo = vincular(anuncio, media)
            if metodo == "PENDIENTE":
                tot_pend += 1

            cpa_q = (v["spend_usd"] * tasa / v["ventas"]) if v["ventas"] else None
            if cpa_q is None:
                sem = "r" if v["spend_usd"] > 0 else ""
            elif base_q and cpa_q <= base_q:
                sem = "g"
            elif be_q and cpa_q < be_q:
                sem = "a"
            else:
                sem = "r"

            filas_mapeo.append({"producto_key": pk, "anuncio": anuncio, "rel": rel,
                                "tipo": tipo, "metodo": metodo,
                                "ventas": v["ventas"], "spend_usd": v["spend_usd"]})

            c = ['<div class="ad %s" data-sem="%s" data-tipo="%s">'
                 % (sem, sem or "r", tipo or "sinimg")]
            c.append('<div class=thumb>')
            if rel and os.path.exists(os.path.join(PROD, rel.replace("/", os.sep))):
                if tipo == "video":
                    c.append('<video src="%s" preload=metadata muted></video>' % e(rel))
                    c.append('<span class=vbadge>VIDEO</span>')
                else:
                    c.append('<img loading=lazy src="%s" alt="">' % e(rel))
                if metodo == "AUTO":
                    c.append('<span class=vbadge style="left:auto;right:7px">auto</span>')
            else:
                c.append('<div class=sinimg>sin archivo vinculado<br>'
                         '<span style="color:#4a5266">llenalo en '
                         '_MAPEO_CREATIVOS.csv</span></div>')
            c.append('</div>')
            c.append('<div class=nom>%s</div>' % e(anuncio or "(anuncio sin nombre)"))
            c.append('<div class=kpis>')
            c.append('<div class=kpi><span class="v cpa">%s</span><span class=l>CPA real</span></div>'
                     % ("Q%.0f" % cpa_q if cpa_q else "—"))
            c.append('<div class=kpi><span class=v>%d</span><span class=l>ventas</span></div>'
                     % v["ventas"])
            c.append('<div class=kpi><span class=v>Q%.0f</span><span class=l>gasto</span></div>'
                     % (v["spend_usd"] * tasa))
            c.append('</div>')
            c.append('<div class=pie><span>%s</span><span>%s → %s</span></div>'
                     % (e(" · ".join(sorted(v["cuentas"])) or "—"),
                        e(v["ini"]), e(v["fin"])))
            c.append('</div>')
            cards.append("".join(c))

        b = ['<section class=prod id="%s">' % e(pk)]
        b.append('<div class=phead><h2>%s</h2><span class="pill %s">%s</span>'
                 '<span class=sub>%s</span></div>'
                 % (e(p.get("nombre_display") or pk), e(estado), e(estado),
                    e(p.get("fase") or "")))
        b.append('<p class=pmeta>CPA base <b>Q%.1f</b> · break-even <b>Q%.1f</b> · '
                 'cuenta <b>%s</b> · %d anuncios con data</p>'
                 % (base_q, be_q, e(p.get("cuenta_alias") or "—"), len(propios)))
        b.append('<div class=grid>%s</div></section>' % "".join(cards))
        bloques.append("".join(b))

    escribir_mapeo(filas_mapeo)

    partes = ["<!doctype html><html lang=es><meta charset=utf-8>",
              "<meta name=viewport content='width=device-width,initial-scale=1'>",
              "<title>META ADS — creativo y resultado</title>",
              "<style>%s</style>" % CSS,
              "<header><h1>META ADS</h1>",
              "<span class=sub>%d anuncios con venta · fuente LucidSales (rol BASE)</span>"
              % tot_ads,
              "<div class=chips>"]
    for v, t in [("g", "CPA bajo base"), ("a", "bajo break-even"), ("r", "sobre break-even"),
                 ("video", "video"), ("imagen", "imagen"), ("sinimg", "sin vincular")]:
        partes.append("<span class=chip data-v='%s'>%s</span>" % (v, t))
    partes.append("</div></header><main>")

    if tot_pend:
        partes.append(
            '<div class=aviso><b>%d de %d anuncios no tienen archivo vinculado.</b> '
            'El nombre del anuncio en Meta no coincide con el del archivo, y no hay '
            'llave que los una. Se resolvieron %d automaticamente; el resto queda en '
            '<b>PRODUCTOS/_MAPEO_CREATIVOS.csv</b> con <code>metodo=PENDIENTE</code>: '
            'poné la ruta en <code>archivo_media</code> y cambiá el metodo a '
            '<code>MANUAL</code> — lo MANUAL nunca se pisa al regenerar.</div>'
            % (tot_pend, tot_ads, tot_ads - tot_pend))

    partes.extend(bloques)
    partes.append("</main><script>%s</script></html>" % JS)

    with io.open(SALIDA, "w", encoding="utf-8") as fh:
        fh.write("\n".join(partes))

    print("escrito %s (%.0f KB)" % (SALIDA, os.path.getsize(SALIDA) / 1024))
    print("anuncios con venta: %d · vinculados: %d · pendientes: %d"
          % (tot_ads, tot_ads - tot_pend, tot_pend))
    print("mapeo en %s" % MAPEO)
    return 0


if __name__ == "__main__":
    sys.exit(main())
