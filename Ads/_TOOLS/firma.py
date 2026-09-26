# -*- coding: utf-8 -*-
"""LA FIRMA: los 5 ejes comprimidos en una linea que VIAJA DENTRO DEL NOMBRE DEL ANUNCIO.

    NUSAVA|ARDOR|C1.CN03|NC2|2X1|BOTv1

Por que dentro del nombre y no solo en un CSV: el ad_id de Meta llego corrupto en 2006 de
2475 filas (float cientifico, digitos perdidos) y el JOIN por id es irrecuperable en el
historico. El NOMBRE, en cambio, viene intacto en cualquier export de Ads Manager, de
LucidSales o del MCP. Si la parametrizacion viaja en el nombre, el cruce no se puede romper:
no depende de que nadie mantenga una tabla paralela al dia.

Uso:
  python firma.py --generar            # muestra la firma de cada fila (la escribe sembrar_anuncios.py)
  python firma.py --parsear "NUSAVA|ARDOR|C1.CN03|NC2|2X1|BOTv1"
  python firma.py --ficha "MA6_OFERTA" # el BANNER de una pieza, con su resultado
  python firma.py --banner [--producto P]   # el banner de todas, ordenado por gasto
"""
import csv, sys, os, math

for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError): pass

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
P = lambda *a: os.path.join(BASE, "PRODUCTOS", *a)

SEP = "|"
VACIO = "?"


def num(x):
    try: return float(x or 0)
    except Exception: return 0.0


def arg(flag, default=None):
    return sys.argv[sys.argv.index(flag) + 1] if flag in sys.argv else default


def corto(v, n=12):
    """Abrevia un valor largo sin perder de vista cual era."""
    v = (v or "").strip()
    if not v or v in ("SIN_CLASIFICAR", "SIN_MAPEAR"):
        return VACIO
    return v[:n]


def firma(r):
    """Los 5 ejes en una linea. El orden es fijo: producto|angulo|concepto.canonico|NC|oferta|destino."""
    con = corto(r.get("concepto_key"), 20)
    con = con.split("_")[0] if con != VACIO else VACIO          # C1_OFERTA -> C1
    cn = corto(r.get("canonico_id"), 20)
    cn = cn.split("_")[0] if cn != VACIO else ""                # CN03_OFERTA... -> CN03
    concepto = con + ("." + cn if cn else "")
    nc = corto(r.get("nivel_conciencia"), 3)
    return SEP.join([
        corto(r.get("producto_key"), 10),
        corto(r.get("angulo_key"), 16),
        concepto,
        ("NC" + nc) if nc != VACIO else VACIO,
        corto(r.get("oferta_key"), 10),
        corto(r.get("destino_key"), 10),
    ])


def parsear(f):
    p = f.split(SEP)
    campos = ["producto_key", "angulo_key", "concepto+canonico", "nivel_conciencia",
              "oferta_key", "destino_key"]
    out = dict(zip(campos, p + [VACIO] * (6 - len(p))))
    cc = out.pop("concepto+canonico")
    out["concepto_key"] = cc.split(".")[0]
    out["canonico_id"] = cc.split(".")[1] if "." in cc else VACIO
    out["nivel_conciencia"] = out["nivel_conciencia"].replace("NC", "")
    return out


def cargar():
    A = list(csv.DictReader(open(P("_DIM_ANUNCIOS.csv"), encoding="utf-8-sig")))
    pr = {r["producto_key"]: r for r in
          csv.DictReader(open(P("_DIM_PRODUCTOS.csv"), encoding="utf-8-sig"))}
    return A, pr


def metricas(r, pr):
    tasa = num(pr.get(r["producto_key"], {}).get("tasa")) or 7.62
    be = num(pr.get(r["producto_key"], {}).get("cpa_be_q"))
    g = num(r["spend_usd"]) * tasa
    v = int(num(r["ventas"]))
    m = num(r["mensajes"])
    return {"g": g, "v": v, "be": be, "cpa": (g / v if v else None),
            "cierre": (v / m if m else None), "m": m,
            "banda": ((g / (v + math.sqrt(v)), g / max(v - math.sqrt(v), 0.5)) if v else None)}


def veredicto(mt):
    if mt["g"] < mt["be"]:
        return "NO TESTEADO — gasto Q%.0f < 1x PD (Q%.0f)" % (mt["g"], mt["be"])
    if not mt["v"]:
        return "MUERTO — 0 ventas con el PD ya gastado"
    r = mt["cpa"] / mt["be"]
    if r <= 0.5:  return "GANADOR FUERTE — CPA a %.0f%% del break-even" % (100 * r)
    if r <= 0.7:  return "GANA — CPA a %.0f%% del break-even" % (100 * r)
    if r <= 1.0:  return "VIVE — CPA a %.0f%% del break-even, margen corto" % (100 * r)
    return "PIERDE — CPA %.0f%% POR ENCIMA del break-even" % (100 * (r - 1))


def ficha(r, pr, ancho=78):
    mt = metricas(r, pr)
    L = []
    L.append("+" + "-" * ancho + "+")
    L.append("| %-*s |" % (ancho - 2, r["anuncio_norm"][:ancho - 2]))
    L.append("| %-*s |" % (ancho - 2, firma(r)))
    L.append("+" + "-" * ancho + "+")
    ejes = [("1 ANGULO      por que duele", r["angulo_key"]),
            ("2 CONCEPTO    como se muestra", r["concepto_key"]),
            ("  canonico    que estructura", r["canonico_id"] or "— (video: vocabulario de imagen)"),
            ("3 CONCIENCIA  a quien le habla", r["nivel_conciencia"]),
            ("4 OFERTA      que le pide comprar", r["oferta_key"]),
            ("5 DESTINO     a donde cae el clic", r["destino_key"])]
    for k, v in ejes:
        L.append("| %-34s %-*s |" % (k, ancho - 37, (v or "SIN LLENAR")[:ancho - 37]))
    L.append("+" + "-" * ancho + "+")
    cov = "%s · %s · hook %s · %s · %s" % (r["formato"], r["rol_embudo"] or "-",
                                           r["tipo_hook"] or "-",
                                           "con precio" if r["lleva_precio"] == "SI" else "sin precio",
                                           r["cuenta_alias"])
    L.append("| covariables congeladas: %-*s |" % (ancho - 26, cov[:ancho - 26]))
    L.append("+" + "-" * ancho + "+")
    res = "Q%.0f gastados · %d ventas · %d mensajes" % (mt["g"], mt["v"], mt["m"])
    L.append("| %-*s |" % (ancho - 2, res))
    if mt["v"]:
        L.append("| %-*s |" % (ancho - 2, "CPA Q%.2f  (banda Q%.0f-Q%.0f)   break-even Q%.2f"
                               % (mt["cpa"], mt["banda"][0], mt["banda"][1], mt["be"])))
        L.append("| %-*s |" % (ancho - 2, "cierre %.1f%% (ventas / mensajes)" % (100 * mt["cierre"])))
    L.append("| %-*s |" % (ancho - 2, "> " + veredicto(mt)))
    L.append("+" + "-" * ancho + "+")
    if r.get("notas"):
        L.append("  " + r["notas"][:ancho * 2])
    return "\n".join(L)


def main():
    A, pr = cargar()

    if "--parsear" in sys.argv:
        for k, v in parsear(arg("--parsear")).items():
            print("  %-18s %s" % (k, v))
        return

    if "--ficha" in sys.argv:
        q = arg("--ficha").lower()
        hits = [r for r in A if q in r["anuncio_norm"].lower()]
        if not hits:
            print("no hay anuncio que contenga '%s'" % q); return
        for r in hits:
            print(ficha(r, pr)); print()
        return

    if "--banner" in sys.argv:
        p = arg("--producto")
        rows = [r for r in A if (not p or r["producto_key"] == p)]
        rows.sort(key=lambda r: -num(r["spend_usd"]))
        for r in rows[:int(arg("--top", "10"))]:
            print(ficha(r, pr)); print()
        return

    if "--generar" in sys.argv:
        # Solo muestra. La columna `firma` de _DIM_ANUNCIOS.csv la escribe UNICAMENTE
        # sembrar_anuncios.py --escribir: dos escritores de archivo completo se borraban
        # la columna uno al otro.
        for r in A:
            r["firma"] = firma(r)
        completas = sum(1 for r in A if VACIO not in r["firma"])
        print("firmas calculadas: %d   completas (5 ejes llenos): %d" % (len(A), completas))
        print("(no se escribe nada: la columna la persiste sembrar_anuncios.py --escribir)")
        for r in sorted(A, key=lambda x: -num(x["spend_usd"]))[:12]:
            print("   $%7.2f  %s" % (num(r["spend_usd"]), r["firma"]))
        return

    print(__doc__)


if __name__ == "__main__":
    main()
