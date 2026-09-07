# -*- coding: utf-8 -*-
"""Gate de PARAMETRIZACION: ningun valor fuera del vocabulario, ninguna deuda invisible.

Verifica _DIM_ANUNCIOS.csv (y opcionalmente _DIM_CONJUNTOS.csv) contra
_DIM_VOCABULARIO.csv y reporta:
  1. valores usados que NO existen en el vocabulario (o que son alias sucios)
  2. canonico_id incoherente con su concepto_key
  3. DEUDA DE PARAMETRIZACION: cuanto gasto real esta en filas sin clasificar

Exit code 1 si hay violaciones duras. Apto para hook de .claude/settings.json.
"""
import csv, sys, os, collections

for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError): pass

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
P = lambda *a: os.path.join(BASE, "PRODUCTOS", *a)

ABIERTOS = {"angulo_key", "destino_key"}   # su vocabulario nace por producto


def num(x):
    try: return float(x or 0)
    except Exception: return 0.0


def main():
    voc = list(csv.DictReader(open(P("_DIM_VOCABULARIO.csv"), encoding="utf-8-sig")))
    validos = collections.defaultdict(set)
    alias = {}
    mapa_cn = {}
    for r in voc:
        if r["estado"] != "VIGENTE":
            continue
        validos[r["eje"]].add(r["valor"])
        if r["eje"] == "canonico_id":
            mapa_cn[r["valor"]] = r["mapea_a"]
        elif r["mapea_a"] and "alias" in r["etiqueta"].lower():
            alias[(r["eje"], r["valor"])] = r["mapea_a"]
        elif r["mapea_a"] and "RETIRADO" in r["etiqueta"]:
            alias[(r["eje"], r["valor"])] = r["mapea_a"]

    A = list(csv.DictReader(open(P("_DIM_ANUNCIOS.csv"), encoding="utf-8-sig")))
    duros, blandos = [], []
    G = sum(num(r["spend_usd"]) for r in A)

    for r in A:
        for eje in validos:
            if eje in ABIERTOS or eje not in r:
                continue
            v = (r[eje] or "").strip()
            if not v:
                continue
            if (eje, v) in alias:
                blandos.append("%-30s %-16s '%s' es alias sucio -> normalizar a '%s'"
                               % (r["anuncio_norm"][:30], eje, v, alias[(eje, v)]))
            elif v not in validos[eje]:
                duros.append("%-30s %-16s '%s' NO existe en el vocabulario"
                             % (r["anuncio_norm"][:30], eje, v))
        cn, ck = r.get("canonico_id", ""), r.get("concepto_key", "")
        if cn and ck and ck != "SIN_CLASIFICAR" and mapa_cn.get(cn) and mapa_cn[cn] != ck:
            duros.append("%-30s canonico %s pertenece a %s, no a %s"
                         % (r["anuncio_norm"][:30], cn, mapa_cn[cn], ck))

    print("=" * 88)
    print("GATE DE PARAMETRIZACION  -  %d anuncios, $%.2f de gasto" % (len(A), G))
    print("=" * 88)

    print("\nDEUDA DE PARAMETRIZACION (gasto que no se puede atribuir a un eje):")
    hay_deuda = False
    for eje in ["concepto_key", "canonico_id", "nivel_conciencia", "oferta_key", "destino_key"]:
        sin = [r for r in A if not (r.get(eje) or "").strip()
               or r.get(eje) in ("SIN_CLASIFICAR", "SIN_MAPEAR")]
        g = sum(num(r["spend_usd"]) for r in sin)
        pct = 100 * g / G if G else 0
        marca = "  <-- eje ciego" if pct > 50 else ""
        if pct > 0:
            hay_deuda = True
        print("   %-18s %3d/%d anuncios   $%8.2f   %5.1f%% del gasto%s"
              % (eje, len(sin), len(A), g, pct, marca))
    if not hay_deuda:
        print("   ninguna. Todos los ejes son legibles.")

    if blandos:
        print("\nALIAS SUCIOS (%d) - no rompen, pero fragmentan el corte:" % len(blandos))
        for b in blandos[:15]:
            print("   " + b)
    if duros:
        print("\nVIOLACIONES DURAS (%d):" % len(duros))
        for d in duros[:20]:
            print("   " + d)
        print("\nFALLO")
        return 1
    print("\nOK: ningun valor fuera del vocabulario.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
