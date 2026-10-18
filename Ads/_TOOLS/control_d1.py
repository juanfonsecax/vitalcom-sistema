# -*- coding: utf-8 -*-
"""control_d1.py — CONTROL D+1 DE TRACKING (DOCTRINA/MCP_PLAYBOOK.md §7.5), solo lectura.

POR QUE EXISTE
--------------
Un conjunto ciego es indistinguible de un conjunto malo: gasta, trae conversaciones reales y marca
0 ventas. Este control compara, por conjunto lanzado en los ultimos dias y por dia CERRADO, lo que
Meta registro (PRODUCTOS/_FACT_ENTREGA.csv) contra lo que LucidSales registro
(PRODUCTOS/_FACT_VENTAS.csv):

    Meta mensajes > 0 y LucidSales sin mensajes ni ventas   -> CIEGO     (cortar YA, por MCP)
    Meta mensajes > 0 y LucidSales con actividad            -> OK
    gasto bajo el umbral                                    -> SIN_ENTREGA
    gasto sobre el umbral pero Meta 0 mensajes              -> SIN_MENSAJES (no es de tracking)
    el dia de hoy, o un dia que aun no tiene data en ambas  -> EN_CURSO  (nunca alarma)

El veredicto del conjunto es el peor de sus dias cerrados: CIEGO > OK > SIN_MENSAJES >
SIN_ENTREGA > EN_CURSO.

CONTRATO
--------
- Solo LEE. No escribe archivos, no llama a Meta. Los nombres de conjunto renombrados se colapsan
  con alias.py (PRODUCTOS/_ALIAS_CONJUNTOS.csv), nunca con un mapeo propio.
- Cruce: (cuenta_alias, campana, conjunto canonico, dia). Solo filas de un dia
  (ventana_ini == ventana_fin) de _FACT_VENTAS; las ventanas multi-dia se ignoran para no sumar
  dos veces.
- "Dia cerrado" = anterior a --hoy Y con data en AMBAS fuentes (no se puede declarar ciego a un
  conjunto cuyo dia LucidSales todavia no se bajo).
- El id del conjunto se toma, si existe, de Ads/_INGESTA/META/snapshot_<alias>_*.json.
- `requiere_claude` (forma en requiere_claude.py) lleva items SOLO para los CIEGO.

USO
    python Ads/_TOOLS/control_d1.py [--hoy YYYY-MM-DD] [--dias 3] [--json]
CODIGOS DE SALIDA   0 = nada ciego.   1 = hay conjuntos CIEGO.   2 = uso incorrecto.
"""
import sys, os, io, csv, json, glob, argparse, datetime

for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError): pass

_AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _AQUI)
import alias as _alias          # noqa: E402
import requiere_claude as rq    # noqa: E402

BASE = os.path.dirname(os.path.dirname(_AQUI))
ENTREGA = os.path.join(BASE, "PRODUCTOS", "_FACT_ENTREGA.csv")
VENTAS = os.path.join(BASE, "PRODUCTOS", "_FACT_VENTAS.csv")
INGESTA = os.path.join(BASE, "Ads", "_INGESTA", "META")

DIAS_VENTANA = 3
UMBRAL_SPEND_USD = 0.5
MIN_MENSAJES_META = 1
PRIORIDAD = ["CIEGO", "OK", "SIN_MENSAJES", "SIN_ENTREGA", "EN_CURSO"]


def _num(v):
    try:
        return float(str(v).strip() or 0)
    except ValueError:
        return 0.0


def _leer(ruta):
    if not os.path.exists(ruta):
        return []
    with io.open(ruta, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def ids_de_conjuntos(carpeta=INGESTA):
    """{(cuenta_alias, nombre): id} de los snapshots de Meta que existan (mejor esfuerzo)."""
    out = {}
    for ruta in sorted(glob.glob(os.path.join(carpeta, "snapshot_*_*.json"))):
        alias = os.path.basename(ruta)[len("snapshot_"):].split("_")[0]
        try:
            with io.open(ruta, encoding="utf-8") as f:
                d = json.load(f)
            ents = d if isinstance(d, list) else d.get("ad_entities", d.get("objetos", []))
            if isinstance(ents, str):
                ents = json.loads(ents)
        except (OSError, ValueError):
            continue
        for e in ents:
            if e.get("nivel") == "adset" and e.get("name") and e.get("id"):
                out[(alias, e["name"].strip())] = str(e["id"])
    return out


def _veredicto_dia(fecha, hoy, ultima_comun, spend, meta_msg, lucid_msg, lucid_ventas,
                   umbral, min_mensajes):
    if fecha >= hoy or fecha > ultima_comun:
        return "EN_CURSO"
    if spend < umbral:
        return "SIN_ENTREGA"
    if meta_msg < min_mensajes:
        return "SIN_MENSAJES"
    return "CIEGO" if (lucid_msg <= 0 and lucid_ventas <= 0) else "OK"


def evaluar(entrega, ventas, hoy, dias=DIAS_VENTANA, umbral=UMBRAL_SPEND_USD,
            min_mensajes=MIN_MENSAJES_META, canon=None, ids=None):
    """Funcion pura. entrega/ventas: listas de dict (filas de los CSV). hoy: datetime.date.
    Devuelve {"hoy","ultima_fecha_entrega","ultima_fecha_ventas","conjuntos":[...],
    "requiere_claude":[...]}."""
    canon = canon or _alias.canonico
    ids = ids or {}
    meta = {}     # (cuenta, campana, conjunto, dia) -> [spend, mensajes]
    producto = {}
    ult_e = ""
    for r in entrega:
        dia = (r.get("ventana_ini") or "").strip()
        if not dia or dia != (r.get("ventana_fin") or "").strip():
            continue
        k = (r.get("cuenta_alias", ""), r.get("campana", ""), canon(r.get("conjunto", "")), dia)
        acc = meta.setdefault(k, [0.0, 0.0])
        acc[0] += _num(r.get("spend_usd"))
        acc[1] += _num(r.get("mensajes"))
        producto[k[:3]] = r.get("producto_key", "")
        ult_e = max(ult_e, dia)
    luc = {}      # misma llave -> [mensajes, ventas, filas]
    ult_v = ""
    for r in ventas:
        dia = (r.get("ventana_ini") or "").strip()
        if not dia or dia != (r.get("ventana_fin") or "").strip():
            continue
        k = (r.get("cuenta_alias", ""), r.get("campana", ""), canon(r.get("conjunto", "")), dia)
        acc = luc.setdefault(k, [0.0, 0.0, 0])
        acc[0] += _num(r.get("mensajes"))
        acc[1] += _num(r.get("ventas"))
        acc[2] += 1
        ult_v = max(ult_v, dia)
    ultima_comun = min(ult_e, ult_v) if (ult_e and ult_v) else ""

    corte = (hoy - datetime.timedelta(days=dias)).isoformat()
    primer = {}
    for (cta, camp, cj, dia), (spend, _m) in meta.items():
        if spend > 0:
            primer[(cta, camp, cj)] = min(primer.get((cta, camp, cj), "9999"), dia)

    conjuntos, pedidos = [], []
    for (cta, camp, cj), p in sorted(primer.items()):
        if p < corte:
            continue
        filas, vereds = [], []
        fecha = datetime.date.fromisoformat(p)
        while fecha <= hoy:
            d = fecha.isoformat()
            spend, mm = meta.get((cta, camp, cj, d), [0.0, 0.0])
            lm, lv, lf = luc.get((cta, camp, cj, d), [0.0, 0.0, 0])
            v = _veredicto_dia(d, hoy.isoformat(), ultima_comun, spend, mm, lm, lv, umbral,
                               min_mensajes)
            filas.append({"fecha": d, "spend_usd": round(spend, 2), "meta_mensajes": int(mm),
                          "lucid_mensajes": int(lm), "lucid_ventas": int(lv),
                          "lucid_filas": lf, "veredicto": v})
            vereds.append(v)
            fecha += datetime.timedelta(days=1)
        ver = next(x for x in PRIORIDAD if x in vereds)
        cid = ids.get((cta, cj), "")
        conjuntos.append({"cuenta_alias": cta, "campana": camp, "conjunto": cj,
                          "producto_key": producto.get((cta, camp, cj), ""), "conjunto_id": cid,
                          "primer_gasto": p, "veredicto": ver, "dias": filas})
        if ver == "CIEGO":
            donde = " (%s)" % cid if cid else ""
            pedidos.append(rq.item(
                "CONJUNTO_CIEGO", "alta",
                "El conjunto %s gastó y Meta registra conversaciones, pero LucidSales no registra "
                "ninguna: el tracking está ciego." % cj,
                "Pausá por MCP el conjunto %s%s: Meta registra conversaciones y LucidSales ninguna, "
                "el tracking está ciego." % (cj, donde),
                [{"id": cid, "nombre": cj}]))
    return {"hoy": hoy.isoformat(), "ultima_fecha_entrega": ult_e, "ultima_fecha_ventas": ult_v,
            "conjuntos": conjuntos, "requiere_claude": pedidos}


def avisos_claude(hoy=None):
    """Lista `requiere_claude` con los datos reales (para el contrato Hoy de la app). Si falta
    cualquiera de los dos CSV devuelve [] — sin data no hay alarma."""
    res = evaluar(_leer(ENTREGA), _leer(VENTAS), hoy or datetime.date.today(),
                  ids=ids_de_conjuntos())
    return res["requiere_claude"]


def _texto(res):
    out = ["CONTROL D+1 de tracking - hoy %s (data Meta hasta %s, LucidSales hasta %s)"
           % (res["hoy"], res["ultima_fecha_entrega"] or "?", res["ultima_fecha_ventas"] or "?")]
    if not res["conjuntos"]:
        out.append("Ningun conjunto con primer gasto en los ultimos dias.")
    for c in res["conjuntos"]:
        out.append("  %-12s %s / %s  [%s]" % (c["veredicto"], c["cuenta_alias"], c["conjunto"],
                                              c["campana"]))
        for d in c["dias"]:
            out.append("      %s  %-12s gasto $%.2f  Meta msj %d  Lucid msj %d ventas %d filas %d"
                       % (d["fecha"], d["veredicto"], d["spend_usd"], d["meta_mensajes"],
                          d["lucid_mensajes"], d["lucid_ventas"], d["lucid_filas"]))
    for it in res["requiere_claude"]:
        out.append("NECESITA CLAUDE: " + it["pedirle_a_claude"])
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Control D+1 de tracking: Meta vs LucidSales (solo lectura).")
    ap.add_argument("--hoy", help="YYYY-MM-DD (por defecto, hoy)")
    ap.add_argument("--dias", type=int, default=DIAS_VENTANA,
                    help="conjuntos con primer gasto en los ultimos N dias")
    ap.add_argument("--umbral-spend", type=float, default=UMBRAL_SPEND_USD)
    ap.add_argument("--min-mensajes", type=int, default=MIN_MENSAJES_META)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    try:
        hoy = datetime.date.fromisoformat(a.hoy) if a.hoy else datetime.date.today()
    except ValueError:
        print("--hoy debe ser YYYY-MM-DD", file=sys.stderr)
        return 2
    res = evaluar(_leer(ENTREGA), _leer(VENTAS), hoy, a.dias, a.umbral_spend, a.min_mensajes,
                  ids=ids_de_conjuntos())
    print(json.dumps(res, ensure_ascii=False) if a.json else _texto(res))
    return 1 if any(c["veredicto"] == "CIEGO" for c in res["conjuntos"]) else 0


if __name__ == "__main__":
    sys.exit(main())
