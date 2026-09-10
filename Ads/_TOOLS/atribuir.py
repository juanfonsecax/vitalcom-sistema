# -*- coding: utf-8 -*-
"""Corta el resultado por EJE y dice si la diferencia es real o es ruido/confounding.

Responde la pregunta que el sistema no podia responder: gano el ANGULO o gano el CONCEPTO.

Uso:
  python atribuir.py --eje concepto_key
  python atribuir.py --eje concepto_key --fijar angulo_key=ARDOR
  python atribuir.py --eje angulo_key --producto TINNIDROP
  python atribuir.py --matriz angulo_key concepto_key --producto TINNIDROP

Reglas que aplica (no son opinion, salen de la doctrina):
  - Se mide por CPA en Q contra el break-even del producto. NUNCA por ROAS.
    (DOCTRINA/ESCALADO_PLAYBOOK.md seccion 8)
  - Una celda con gasto < 1x CPA break-even NO se lee: no perdio, no se testeo.
    (ESCALADO_PLAYBOOK seccion 7 - Presupuesto de Decision)
  - Antes de atribuir a un eje, se reporta el CONFOUNDING: si los niveles del eje
    no comparten los otros ejes, la diferencia no es de ese eje.
"""
import csv, sys, os, math, collections

for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError): pass

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
P = lambda *a: os.path.join(BASE, "PRODUCTOS", *a)

EJES = ["angulo_key", "concepto_key", "canonico_id", "nivel_conciencia",
        "oferta_key", "destino_key", "formato", "rol_embudo", "tipo_hook",
        "estilo_visual", "lleva_precio", "avatar_edad", "cuenta_alias"]


def num(x):
    try: return float(x or 0)
    except Exception: return 0.0


def arg(flag, default=None):
    return sys.argv[sys.argv.index(flag) + 1] if flag in sys.argv else default


def cargar():
    A = list(csv.DictReader(open(P("_DIM_ANUNCIOS.csv"), encoding="utf-8-sig")))
    prods = {r["producto_key"]: r for r in
             csv.DictReader(open(P("_DIM_PRODUCTOS.csv"), encoding="utf-8-sig"))}
    return A, prods


def q(r, prods):
    """spend en Q usando la tasa del producto."""
    tasa = num(prods.get(r["producto_key"], {}).get("tasa")) or 7.62
    return num(r["spend_usd"]) * tasa


def be(pk, prods):
    return num(prods.get(pk, {}).get("cpa_be_q")) or 0.0


def celda(rows, prods):
    g = sum(q(r, prods) for r in rows)
    v = sum(int(num(r["ventas"])) for r in rows)
    m = sum(num(r["mensajes"]) for r in rows)
    c = sum(num(r["clicks"]) for r in rows)
    i = sum(num(r["impresiones"]) for r in rows)
    return {"gasto_q": g, "ventas": v, "cpa": (g / v if v else None),
            "mensajes": m, "cierre": (v / m if m else None),
            "cpc": (g / c if c else None), "ctr": (100 * c / i if i else None),
            "n_ads": len(rows)}


def banda(gasto, v):
    """Banda de CPA del MISMO posterior que usa el motor de decision (09-sep-2026).

    Antes era mas/menos 1 sigma sobre n ventas, que no es un intervalo de credibilidad:
    con 2-3 ventas subestima el ancho y con 0 ventas no existe. Ahora sale de
    decidir.ic_cpa() -> lambda|k ~ Gamma(k+0.5,1), CPA = gasto/lambda, IC al
    nivel_confianza de _PARAMETROS_DECISION.csv. Dos partes del sistema que comparan
    CPA tienen que usar el mismo intervalo, o "las bandas no se tocan" significa una
    cosa en atribuir.py y otra en decidir.py.
    """
    if not v: return None
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from decidir import ic_cpa, cargar_parametros
        conf = float(cargar_parametros().get("nivel_confianza", 0.95))
        lo, _, hi = ic_cpa(v, gasto / 7.62, conf, 7.62)   # ic_cpa toma USD y reconvierte
        return (lo, hi) if hi else None
    except Exception:
        lo, hi = v + math.sqrt(v), max(v - math.sqrt(v), 0.5)
        return (gasto / lo, gasto / hi)


def gate_integridad(A, prods):
    """La tabla que este script lee, contra la fuente de verdad de la que salio.

    _DIM_ANUNCIOS.csv lo siembra sembrar_anuncios.py recorriendo _FACT_VENTAS.csv SIN
    filtrar rol_ventana, y DATA_PLAYBOOK.md es explicito: BASE suma, CONTROL solapa a
    proposito y NUNCA suma (es la prueba anti-doble-conteo de APR-020). Medido el
    09-sep-2026: 904 ventas contra 506 reales, y el inflado NO es parejo entre productos
    (NUSAVA +100 %, VARICOSE +145 %, CLEARSTEM +59 %, TINNIDROP +69 %), asi que tampoco se
    cancela al comparar niveles. Este gate no corrige nada: lo pone a la vista cada vez
    que alguien lee causalidad sobre esta tabla.
    """
    base = collections.defaultdict(float)
    for r in csv.DictReader(open(P("_FACT_VENTAS.csv"), encoding="utf-8-sig")):
        if (r.get("rol_ventana") or "").strip() == "BASE" and (r.get("anuncio") or "").strip():
            base[r["producto_key"]] += num(r.get("ventas"))
    tabla = collections.defaultdict(float)
    for r in A:
        tabla[r["producto_key"]] += num(r.get("ventas"))
    malos = [(pk, tabla[pk], base.get(pk, 0.0)) for pk in sorted(tabla)
             if base.get(pk, 0.0) and abs(tabla[pk] - base[pk]) > 0.5]
    if not malos:
        return
    print("!" * 100)
    print("AVISO DE INTEGRIDAD: _DIM_ANUNCIOS.csv suma ventanas CONTROL, que por doctrina NO suman.")
    print("%-14s %12s %12s %10s" % ("producto", "en la tabla", "BASE real", "inflado"))
    for pk, t, b in malos:
        print("%-14s %12.0f %12.0f %9.0f%%" % (pk, t, b, 100 * (t / b - 1)))
    print("Arreglo: en sembrar_anuncios.py, saltear la fila cuando rol_ventana != 'BASE',")
    print("y re-sembrar con --escribir. Hasta entonces, los CPA de abajo describen una mezcla")
    print("de BASE + CONTROL y su NIVEL no es comparable con el de decidir.py.")
    print("!" * 100)
    print()


def leer_eje(A, prods, eje, fijar=None, producto=None):
    rows = A
    if producto:
        rows = [r for r in rows if r["producto_key"] == producto]
    if fijar:
        k, val = fijar.split("=", 1)
        rows = [r for r in rows if r[k] == val]
    if not rows:
        print("sin filas para ese filtro")
        return

    pks = {r["producto_key"] for r in rows}
    be_ref = sum(be(p, prods) for p in pks) / len(pks)

    grupos = collections.defaultdict(list)
    for r in rows:
        grupos[r[eje] or "(vacio)"].append(r)

    print("=" * 100)
    print("EJE: %s%s%s" % (eje,
          ("   |  fijando %s" % fijar) if fijar else "",
          ("   |  producto %s" % producto) if producto else "   |  TODOS los productos"))
    print("break-even de referencia: Q%.2f   (celda con gasto < Q%.2f = 1x PD: no se lee)"
          % (be_ref, be_ref))
    print("=" * 100)
    print("%-24s %8s %6s %8s %-14s %7s %4s %4s  %s" %
          ("nivel", "gasto Q", "vtas", "CPA Q", "IC 95%", "cierre", "ads", "ang", "veredicto"))
    print("-" * 108)

    filas = []
    for k, rs in sorted(grupos.items(), key=lambda x: -sum(q(r, prods) for r in x[1])):
        c = celda(rs, prods)
        b = banda(c["gasto_q"], c["ventas"])
        if c["gasto_q"] < be_ref:
            ver = "NO TESTEADO (gasto < 1x PD)"
        elif not c["ventas"]:
            ver = "MUERTO (0 ventas con PD gastado)"
        elif c["cpa"] <= be_ref * 0.7:
            ver = "GANA"
        elif c["cpa"] <= be_ref:
            ver = "vive (bajo BE)"
        else:
            ver = "PIERDE (sobre BE)"
        n_ang = len({r["angulo_key"] for r in rs})
        aviso = "  [1 ANGULO: no separable del angulo]" if (n_ang == 1 and eje != "angulo_key"
                                                            and not ver.startswith("NO TESTEADO")) else ""
        print("%-24s %8.0f %6d %8s %-14s %7s %4d %4d  %s%s" % (
            str(k)[:24], c["gasto_q"], c["ventas"],
            ("%.2f" % c["cpa"]) if c["cpa"] else "-",
            ("%.0f-%.0f" % b) if b else "-",
            ("%.1f%%" % (100 * c["cierre"])) if c["cierre"] else "-",
            c["n_ads"], n_ang, ver, aviso))
        filas.append((k, c, b, ver))

    legibles = [f for f in filas if not f[3].startswith("NO TESTEADO")]
    if len(legibles) >= 2:
        print("\nCONTROL DE CONFOUNDING - que MAS cambia junto con este eje:")
        alarma = False
        for otro in EJES:
            if otro == eje:
                continue
            vistos = {k: {r[otro] for r in grupos[k] if r[otro]} for k, _, _, _ in legibles}
            solos = [k for k, s in vistos.items() if len(s) == 1]
            if len(solos) == len(legibles) and len({tuple(vistos[k]) for k in solos}) == len(solos):
                print("   [!] %-18s cada nivel tiene UN valor distinto -> no se puede separar de %s"
                      % (otro, eje))
                alarma = True
        if not alarma:
            print("   ok: los otros ejes estan repartidos entre los niveles. La lectura es atribuible.")

        conv = [f for f in legibles if f[1]["ventas"]]
        conv.sort(key=lambda f: f[1]["cpa"])
        if len(conv) >= 2:
            (k1, c1, b1, _), (k2, c2, b2, _) = conv[0], conv[1]
            print("\nSEPARACION mejor vs segundo:  %s (Q%.2f)  vs  %s (Q%.2f)"
                  % (k1, c1["cpa"], k2, c2["cpa"]))
            g1 = grupos[k1]
            n_ads1, n_ang1 = len(g1), len({r["angulo_key"] for r in g1})
            if n_ads1 == 1 or (n_ang1 == 1 and eje != "angulo_key"):
                print("   NO ATRIBUIBLE: la celda ganadora es %d anuncio(s) en %d angulo(s)."
                      % (n_ads1, n_ang1))
                print("   Ese CPA describe UNA pieza dentro de UN angulo, no el eje %s." % eje)
                print("   Para atribuirlo al eje hace falta el mismo %s en >=2 angulos distintos." % eje)
            elif b1[1] < b2[0]:
                print("   DIFERENCIA REAL: las bandas no se tocan. Se puede decidir.")
            else:
                print("   EMPATE ESTADISTICO: las bandas se solapan. No declarar ganador todavia.")
                print("   Necesita ~%d ventas por celda para separarlos." % (int(c2["ventas"] * 1.5) + 3))


def matriz(A, prods, e1, e2, producto=None):
    rows = [r for r in A if (not producto or r["producto_key"] == producto)]
    pks = {r["producto_key"] for r in rows}
    be_ref = sum(be(p, prods) for p in pks) / len(pks)
    g = collections.defaultdict(list)
    for r in rows:
        g[(r[e1] or "-", r[e2] or "-")].append(r)
    f1 = sorted({k[0] for k in g})
    f2 = sorted({k[1] for k in g})
    print("MATRIZ %s (filas) x %s (columnas) - CPA Q / ventas   BE=Q%.2f" % (e1, e2, be_ref))
    print("%-28s" % "" + "".join("%-16s" % c[:15] for c in f2))
    for a in f1:
        out = []
        for b in f2:
            rs = g.get((a, b))
            if not rs:
                out.append("%-16s" % ".")
            else:
                c = celda(rs, prods)
                out.append("%-16s" % (("Q%.0f/%dv" % (c["cpa"], c["ventas"])) if c["ventas"]
                                      else ("0v Q%.0f" % c["gasto_q"])))
        print("%-28s" % a[:28] + "".join(out))
    huecos = sum(1 for a in f1 for b in f2 if (a, b) not in g)
    print("\nceldas vacias: %d de %d. Cada hueco es una combinacion que el sistema NUNCA probo."
          % (huecos, len(f1) * len(f2)))


def main():
    A, prods = cargar()
    gate_integridad(A, prods)
    if "--matriz" in sys.argv:
        i = sys.argv.index("--matriz")
        matriz(A, prods, sys.argv[i + 1], sys.argv[i + 2], arg("--producto"))
        return
    leer_eje(A, prods, arg("--eje", "angulo_key"), arg("--fijar"), arg("--producto"))


if __name__ == "__main__":
    main()
