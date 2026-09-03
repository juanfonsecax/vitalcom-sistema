# -*- coding: utf-8 -*-
"""
gen_banco.py — arma `_SWIPE/_BLUEPRINTS/_BANCO.html`: las 111 con la imagen al
lado de su JSON y un boton de copiar, agrupadas por blueprint canonico.

Para que sirve: mirar la pieza y su estructura extraida a la vez. Un JSON suelto
no se puede verificar (¿de verdad el numeral ocupa un cuarto del alto?) y una
imagen suelta no se puede replicar.

Las imagenes se referencian por ruta RELATIVA, no embebidas: las 111 pesan ~40MB
y `_WINNERS_PORTABLE.html` ya demostro que embeber produce un archivo de 10MB que
el navegador arrastra. El precio es que el HTML solo funciona dentro del repo,
que es donde se usa.

Uso:  python Ads/_TOOLS/gen_banco.py
"""
import html
import json
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Ads/
SWIPE = os.path.join(RAIZ, "_SWIPE")
BP = os.path.join(SWIPE, "_BLUEPRINTS")
FICHAS = os.path.join(BP, "FICHAS")
CANON = os.path.join(BP, "CANONICOS")
SALIDA = os.path.join(BP, "_BANCO.html")

CSS = """
*{box-sizing:border-box}
body{margin:0;background:#0f1115;color:#e6e8ee;
     font:14px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif}
header{position:sticky;top:0;z-index:10;background:#151822;border-bottom:1px solid #262b38;
       padding:14px 22px;display:flex;gap:18px;align-items:center;flex-wrap:wrap}
h1{margin:0;font-size:16px;font-weight:650;letter-spacing:.2px}
.sub{color:#8b93a7;font-size:12px}
input[type=search]{background:#0f1115;border:1px solid #2d3446;color:#e6e8ee;
     border-radius:7px;padding:7px 11px;min-width:230px;font-size:13px}
input[type=search]:focus{outline:none;border-color:#4a7cff}
.chips{display:flex;gap:6px;flex-wrap:wrap}
.chip{background:#1c2130;border:1px solid #2d3446;color:#aab2c5;border-radius:999px;
      padding:4px 11px;font-size:11.5px;cursor:pointer;user-select:none}
.chip:hover{border-color:#4a7cff;color:#e6e8ee}
.chip.on{background:#4a7cff;border-color:#4a7cff;color:#fff;font-weight:600}
main{padding:22px}
section{margin-bottom:34px;scroll-margin-top:70px}
.fam{display:flex;align-items:baseline;gap:11px;flex-wrap:wrap;
     border-left:3px solid #4a7cff;padding-left:12px;margin-bottom:6px}
.fam h2{margin:0;font-size:15px;font-weight:650}
.fam .id{color:#4a7cff;font-family:ui-monospace,Menlo,Consolas,monospace;font-size:12px}
.fam .n{color:#8b93a7;font-size:12px}
.disp{color:#b9c0d1;font-size:12.5px;max-width:110ch;margin:0 0 14px 15px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(345px,1fr));gap:16px}
.card{background:#151822;border:1px solid #262b38;border-radius:11px;overflow:hidden;
      display:flex;flex-direction:column}
.card img{width:100%;display:block;background:#0b0d12;max-height:380px;object-fit:contain}
.meta{padding:9px 12px;border-bottom:1px solid #262b38;display:flex;gap:7px;
      align-items:center;flex-wrap:wrap}
.fid{font-family:ui-monospace,Menlo,Consolas,monospace;font-weight:700;color:#4a7cff}
.tag{background:#1c2130;border-radius:5px;padding:2px 7px;font-size:11px;color:#aab2c5}
.tag.ugc{background:#3b2a15;color:#e0a458}
.score{margin-left:auto;color:#8b93a7;font-size:11.5px}
.dev{padding:9px 12px;font-size:12.5px;color:#c9d0e0;border-bottom:1px solid #262b38}
.acts{padding:9px 12px;display:flex;gap:7px}
button{background:#1c2130;border:1px solid #2d3446;color:#c9d0e0;border-radius:7px;
       padding:6px 11px;font-size:12px;cursor:pointer}
button:hover{border-color:#4a7cff;color:#fff}
button.ok{border-color:#2f9e5f;color:#7ee2a8}
pre{margin:0;padding:11px 12px;background:#0b0d12;border-top:1px solid #262b38;
    max-height:330px;overflow:auto;font:11.5px/1.45 ui-monospace,Menlo,Consolas,monospace;
    color:#a8b3c9;white-space:pre-wrap;word-break:break-word;display:none}
pre.open{display:block}
.empty{color:#8b93a7;padding:30px;text-align:center}
"""

JS = """
const q=document.getElementById('q'), chips=[...document.querySelectorAll('.chip')];
let filtro=null;
function aplicar(){
  const t=q.value.trim().toLowerCase();
  document.querySelectorAll('section').forEach(sec=>{
    let vis=0;
    sec.querySelectorAll('.card').forEach(c=>{
      const okT=!t||c.dataset.buscar.includes(t);
      const okF=!filtro||c.dataset.concepto===filtro||c.dataset.estetica===filtro
                 ||c.dataset.embudo===filtro;
      const m=okT&&okF; c.style.display=m?'':'none'; if(m)vis++;
    });
    sec.style.display=vis?'':'none';
  });
}
q.addEventListener('input',aplicar);
chips.forEach(ch=>ch.addEventListener('click',()=>{
  const v=ch.dataset.v;
  if(filtro===v){filtro=null;ch.classList.remove('on');}
  else{chips.forEach(c=>c.classList.remove('on'));filtro=v;ch.classList.add('on');}
  aplicar();
}));
document.addEventListener('click',e=>{
  const b=e.target.closest('button'); if(!b)return;
  const card=b.closest('.card'), pre=card.querySelector('pre');
  if(b.dataset.a==='ver'){ pre.classList.toggle('open');
    b.textContent=pre.classList.contains('open')?'ocultar JSON':'ver JSON'; return; }
  if(b.dataset.a==='copiar'){
    navigator.clipboard.writeText(pre.textContent).then(()=>{
      const o=b.textContent; b.textContent='copiado'; b.classList.add('ok');
      setTimeout(()=>{b.textContent=o;b.classList.remove('ok');},1200);
    });
  }
});
"""


def cargar(directorio, prefijo):
    out = []
    for nombre in sorted(os.listdir(directorio)):
        if nombre.startswith(prefijo) and nombre.endswith(".json"):
            with open(os.path.join(directorio, nombre), encoding="utf-8") as fh:
                out.append(json.load(fh))
    return out


def main():
    canonicos = cargar(CANON, "CN")
    fichas = {d["ficha_id"]: d for d in cargar(FICHAS, "F")}
    if not canonicos:
        print("no hay canonicos: corre antes agrupar_canonicos.py", file=sys.stderr)
        return 1

    e = html.escape
    partes = [
        "<!doctype html><html lang=es><meta charset=utf-8>",
        "<meta name=viewport content='width=device-width,initial-scale=1'>",
        "<title>Banco de creativos — 111 fichas</title>",
        "<style>%s</style>" % CSS,
        "<header><h1>Banco de creativos</h1>",
        "<span class=sub>%d fichas · %d canonicos · mercado GT</span>"
        % (len(fichas), len(canonicos)),
        "<input type=search id=q placeholder='buscar dispositivo, anunciante, ficha...'>",
        "<div class=chips>",
    ]
    for v, etiqueta in [("C1_OFERTA", "C1"), ("C2_BENEFICIOS", "C2"), ("C3_SINTOMA", "C3"),
                        ("C4_TRANSFORMACION", "C4"), ("C5_PRUEBA", "C5"), ("C7_DESEO", "C7"),
                        ("C8_PROGRESION", "C8"), ("C9_COMPARACION", "C9"),
                        ("organico_ugc", "UGC"), ("TOFU", "TOFU"), ("MOFU", "MOFU"),
                        ("BOFU", "BOFU")]:
        partes.append("<span class=chip data-v='%s'>%s</span>" % (v, etiqueta))
    partes.append("</div></header><main>")

    for c in canonicos:
        partes.append("<section id='%s'>" % e(c["canonico_id"]))
        partes.append(
            "<div class=fam><span class=id>%s</span><h2>%s</h2>"
            "<span class=n>%d piezas · ref %s</span></div>"
            % (e(c["canonico_id"]), e(c["nombre"]), c["n_miembros"],
               e(c["ficha_referencia"])))
        partes.append("<p class=disp>%s</p>" % e(c["dispositivo_canonico"]))
        partes.append("<div class=grid>")

        for m in c["miembros"]:
            d = fichas[m["ficha_id"]]
            cl = d["clasificacion"]
            # el HTML vive en _BLUEPRINTS/, las imagenes cuelgan de _SWIPE/
            src = "../" + d["origen"]["archivo"].replace("\\", "/")
            crudo = json.dumps(d, ensure_ascii=False, indent=2)
            buscar = " ".join([m["ficha_id"], d["dispositivo_dominante"],
                               d["origen"].get("anunciante") or "",
                               cl.get("concepto_key") or ""]).lower()
            ugc = cl.get("estetica") == "organico_ugc"

            partes.append(
                "<div class=card data-buscar='%s' data-concepto='%s' data-estetica='%s' "
                "data-embudo='%s'>" % (e(buscar), e(cl.get("concepto_key") or ""),
                                       e(cl.get("estetica") or ""),
                                       e(cl.get("rol_embudo") or "")))
            partes.append("<img loading=lazy src='%s' alt='%s'>" % (e(src), e(m["ficha_id"])))
            partes.append("<div class=meta><span class=fid>%s</span>" % e(m["ficha_id"]))
            partes.append("<span class=tag>%s</span>" % e(cl.get("concepto_key") or "—"))
            partes.append("<span class=tag>%s</span>" % e(cl.get("rol_embudo") or "—"))
            partes.append("<span class=tag>%s</span>" % e(cl.get("formato") or "—"))
            if ugc:
                partes.append("<span class='tag ugc'>UGC</span>")
            partes.append("<span class=score>%s · score %s</span></div>"
                          % (e(d["origen"].get("anunciante") or "—"),
                             e(str(d["origen"].get("score")))))
            partes.append("<div class=dev>%s</div>" % e(d["dispositivo_dominante"]))
            partes.append("<div class=acts><button data-a=ver>ver JSON</button>"
                          "<button data-a=copiar>copiar JSON</button></div>")
            partes.append("<pre>%s</pre></div>" % e(crudo))

        partes.append("</div></section>")

    partes.append("<div class=empty id=vacio></div></main>")
    partes.append("<script>%s</script></html>" % JS)

    with open(SALIDA, "w", encoding="utf-8") as fh:
        fh.write("\n".join(partes))
    kb = os.path.getsize(SALIDA) / 1024
    print("escrito %s (%.0f KB, %d fichas en %d canonicos)"
          % (SALIDA, kb, len(fichas), len(canonicos)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
