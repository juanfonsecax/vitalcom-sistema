# -*- coding: utf-8 -*-
"""Siembra PRODUCTOS/_DIM_ANUNCIOS.csv: una fila por ANUNCIO real con gasto.

Por que existe: la parametrizacion del sistema vive hoy en _DIM_CONJUNTOS.csv, que
es grano de CONJUNTO = grano de ANGULO. Pero el 91 % del gasto cae en conjuntos con
mas de un anuncio distinto, y el CONCEPTO vive en el anuncio, no en el conjunto.
Sin esta tabla el sistema puede responder "que angulo vende" y nunca "que concepto vende".

Llave: (producto_key, anuncio_norm). anuncio_norm colapsa las replicas "- Copia N"
porque la regla 12 de CLAUDE.md dice que las replicas SE SUMAN, nunca se comparan.

Modo diagnostico por defecto. Escribe solo con --escribir.
"""
import csv, sys, os, re, collections

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from alias import canonico   # un conjunto renombrado en Meta cruza con su dimension

for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError): pass

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
P    = lambda *a: os.path.join(BASE, "PRODUCTOS", *a)

VENTAS = P("_FACT_VENTAS.csv")
CONJ   = P("_DIM_CONJUNTOS.csv")
CLASIF = P("_CLASIFICACION_ANUNCIOS.csv")
SALIDA = P("_DIM_ANUNCIOS.csv")

# Campos que se llenan a mano (o por clasificacion) y que un re-sembrado NUNCA pisa.
MANUALES = ["concepto_key", "canonico_id", "nivel_conciencia", "oferta_key", "destino_key",
            "estilo_visual", "creativo_id", "test_id", "brazo_key", "pagina_id", "estado", "notas"]

COLS = [
    # identidad
    "producto_key","anuncio_norm","anuncio_ejemplo","ad_ids","conjunto_norm","cuenta_alias","campana",
    # EJE 1-3: lo que se testea
    "angulo_key","concepto_key","canonico_id","nivel_conciencia",
    # EJE 4-5: lo que casi nunca se registra y mueve el CPA
    "oferta_key","lleva_precio","destino_key",
    # covariables: se congelan y se registran, no se testean
    "formato","rol_embudo","tipo_hook","estilo_visual","avatar_edad","avatar_genero","pagina_id",
    # trazabilidad
    "creativo_id","test_id","brazo_key",
    # hechos agregados (denormalizados para lectura rapida; la verdad sigue en _FACT_VENTAS)
    "primera_fecha","ultima_fecha","replicas","spend_usd","ventas","mensajes","clicks","impresiones",
    # gobierno del dato
    "fuente_parametrizacion","confianza","estado","notas",
]

MOJI = {"\ufffd": "-"}

def norm_txt(s):
    s = (s or "").strip()
    for k, v in MOJI.items():
        s = s.replace(k, v)
    s = re.sub(r'\s*[-–]\s*Copia(\s*\d+)?\s*$', '', s, flags=re.I)   # replica: se suma
    s = re.sub(r'\s+', ' ', s).strip(' -"\u201c\u201d')
    return s

def num(x):
    try: return float(x or 0)
    except Exception: return 0.0

def limpio_id(x):
    x = (x or "").strip()
    return "" if (not x or "e+" in x.lower()) else x     # el float cientifico ya perdio digitos

def main():
    escribir = "--escribir" in sys.argv
    V = list(csv.DictReader(open(VENTAS, encoding="utf-8-sig")))
    C = list(csv.DictReader(open(CONJ,   encoding="utf-8-sig")))

    # indice de conjuntos por nombre normalizado -> hereda el ANGULO y sus covariables
    idx = {}
    for r in C:
        idx.setdefault((r["producto_key"], norm_txt(canonico(r["conjunto_meta"]))), r)

    ag = collections.OrderedDict()
    for r in V:
        # BASE suma; CONTROL solapa a proposito para auditar y nunca suma (DATA_PLAYBOOK).
        if (r.get("rol_ventana") or "BASE").strip().upper() != "BASE":
            continue
        an = norm_txt(r["anuncio"])
        if not an:
            continue
        k = (r["producto_key"], an)
        a = ag.setdefault(k, {"ad_ids": set(), "reps": set(), "conj": set(), "cta": set(),
                              "camp": set(), "f": [], "spend": 0.0, "ventas": 0,
                              "msg": 0.0, "clk": 0.0, "imp": 0.0, "ej": r["anuncio"]})
        aid = limpio_id(r["ad_id"])
        if aid: a["ad_ids"].add(aid)
        a["reps"].add(r["anuncio"]); a["conj"].add(norm_txt(canonico(r["conjunto"])))
        a["cta"].add(r["cuenta_alias"]); a["camp"].add(r["campana"])
        a["f"] += [r["ventana_ini"], r["ventana_fin"]]
        a["spend"] += num(r["spend_usd"]); a["ventas"] += int(num(r["ventas"]))
        a["msg"] += num(r["mensajes"]); a["clk"] += num(r["clicks"]); a["imp"] += num(r["impresiones"])

    filas, sin_conj = [], 0
    for (pk, an), a in ag.items():
        cj = sorted(a["conj"])[0] if a["conj"] else ""
        d  = idx.get((pk, cj), {})
        if not d: sin_conj += 1
        filas.append({
            "producto_key": pk, "anuncio_norm": an, "anuncio_ejemplo": a["ej"],
            "ad_ids": "|".join(sorted(a["ad_ids"])), "conjunto_norm": cj,
            "cuenta_alias": "|".join(sorted(x for x in a["cta"] if x)),
            "campana": sorted(a["camp"])[0] if a["camp"] else "",
            "angulo_key": d.get("angulo_key", "SIN_MAPEAR"),
            "concepto_key": "SIN_CLASIFICAR", "canonico_id": "",
            "nivel_conciencia": d.get("nivel_conciencia", ""),
            "oferta_key": "", "lleva_precio": d.get("lleva_precio", ""), "destino_key": "",
            "formato": d.get("formato", ""), "rol_embudo": d.get("rol_embudo", ""),
            "tipo_hook": d.get("tipo_hook", ""), "estilo_visual": "",
            "avatar_edad": d.get("avatar_edad", ""), "avatar_genero": d.get("avatar_genero", ""),
            "pagina_id": "", "creativo_id": d.get("creativo_id", ""), "test_id": "", "brazo_key": "",
            "primera_fecha": min(a["f"]), "ultima_fecha": max(a["f"]),
            "replicas": len(a["reps"]),
            "spend_usd": round(a["spend"], 2), "ventas": a["ventas"],
            "mensajes": int(a["msg"]), "clicks": int(a["clk"]), "impresiones": int(a["imp"]),
            "fuente_parametrizacion": "SEMILLA_DIM_CONJUNTOS" if d else "SIN_HERENCIA",
            "confianza": "HEREDADA" if d else "NULA", "estado": "PENDIENTE_CLASIFICAR", "notas": "",
        })

    # --- MERGE 1: lo que ya estaba en _DIM_ANUNCIOS.csv manda sobre la semilla
    previo = {}
    if os.path.exists(SALIDA):
        for r in csv.DictReader(open(SALIDA, encoding="utf-8-sig")):
            previo[(r["producto_key"], r["anuncio_norm"])] = r
    conservados = 0
    for f in filas:
        p_ = previo.get((f["producto_key"], f["anuncio_norm"]))
        if not p_:
            continue
        for col in MANUALES:
            v = (p_.get(col) or "").strip()
            if v and v not in ("SIN_CLASIFICAR", "SIN_MAPEAR", "PENDIENTE_CLASIFICAR"):
                f[col] = v
                conservados += 1

    # --- MERGE 2: la clasificacion declarada gana sobre todo
    clasif = {}
    if os.path.exists(CLASIF):
        for r in csv.DictReader(open(CLASIF, encoding="utf-8-sig")):
            clasif[(r["producto_key"], r["anuncio_norm"])] = r
    aplicadas = 0
    for f in filas:
        cl = clasif.get((f["producto_key"], f["anuncio_norm"]))
        if not cl:
            continue
        for col in ["concepto_key", "canonico_id", "nivel_conciencia", "oferta_key",
                    "lleva_precio", "rol_embudo", "formato"]:
            if (cl.get(col) or "").strip():
                f[col] = cl[col].strip()
        f["fuente_parametrizacion"] = "CLASIFICADO_" + cl["confianza"]
        f["confianza"] = cl["confianza"]
        f["estado"] = "CLASIFICADO"
        f["notas"] = (cl.get("evidencia", "") + " | " + cl.get("notas", "")).strip(" |")
        aplicadas += 1
    print("campos manuales conservados: %d | clasificaciones aplicadas: %d" % (conservados, aplicadas))

    filas.sort(key=lambda r: (r["producto_key"], -r["spend_usd"]))
    G = sum(r["spend_usd"] for r in filas)
    print("anuncios distintos (replicas colapsadas): %d" % len(filas))
    print("gasto cubierto: $%.2f" % G)
    print("sin herencia de _DIM_CONJUNTOS: %d filas ($%.2f, %.1f%%)"
          % (sin_conj, sum(r["spend_usd"] for r in filas if r["confianza"] == "NULA"),
             100 * sum(r["spend_usd"] for r in filas if r["confianza"] == "NULA") / G))
    print("con ad_id utilizable: %d de %d" % (sum(1 for r in filas if r["ad_ids"]), len(filas)))
    print("\nTOP 12 por gasto:")
    for r in filas[:12]:
        print("  %-10s %-38s $%7.2f  %3dv  ang=%s" %
              (r["producto_key"], r["anuncio_norm"][:38], r["spend_usd"], r["ventas"], r["angulo_key"][:22]))

    if escribir:
        with open(SALIDA, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=COLS); w.writeheader(); w.writerows(filas)
        print("\nESCRITO -> %s" % SALIDA)
    else:
        print("\n(diagnostico: no se escribio nada. Usar --escribir)")

if __name__ == "__main__":
    main()
