# -*- coding: utf-8 -*-
"""registrar_transferencia_fx.py — registra los pares «quetzales que salieron de Dropi / dólares que
llegaron al banco» en `PRODUCTOS/_FACT_TRANSFERENCIAS_FX.csv`.

  python Ads/_TOOLS/registrar_transferencia_fx.py [--escribir] [--json]
        # empareja solo: cada retiro TRANSFERENCIA_PROPIA de la billetera contra una ENTRADA del banco
  python Ads/_TOOLS/registrar_transferencia_fx.py --salida <mov_id> --usd 11381.00
        [--fecha-llegada YYYY-MM-DD] [--banco MERCURY] [--confirmado-por operador] [--escribir]
        # par confirmado por el operador (mientras el banco destino no está ingerido)

Sin `--escribir` solo MIRA y no toca disco (DOCTRINA/DATA_PLAYBOOK.md §7).

Emparejado automático: una ENTRADA del banco es candidata de un retiro cuando llegó entre la salida y
`--dias-habiles` días hábiles después, y los dólares dan una tasa dentro de la banda
[`--tasa-min`, `--tasa-max`]. Con exactamente una candidata (que ningún otro retiro reclame) se
empareja; con dos o más, o si dos retiros reclaman la misma entrada, NO se empareja y se lista como
ambiguo. Un retiro que ya tiene par no se toca. El par del operador reemplaza al automático.
"""
import argparse
import datetime
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import csv_hechos  # noqa: E402
import gen_pl      # noqa: E402
import tasa_fx     # noqa: E402

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

COLUMNAS = tasa_fx.COLUMNAS
DESTINO = tasa_fx.RUTA
DIAS_HABILES = 5
BANDA = (6.5, 9.5)


class ErrorFx(Exception):
    """El par pedido no se puede registrar."""


def _plazo(salida, dias_habiles):
    """Último día en que una entrada cuenta como llegada de un retiro que salió el `salida`."""
    d, n = datetime.date.fromisoformat(salida), 0
    while n < dias_habiles:
        d += datetime.timedelta(days=1)
        if d.weekday() < 5:
            n += 1
    return d.isoformat()


def _llave_banco(b):
    return "%s:%s:%s:%s" % (b["banco"], b["cuenta"], b["fecha"], b["monto"])


def _retiros_propios(cartera, reglas):
    return [c for c in cartera if c["categoria"] == "RETIRO"
            and gen_pl.clasificar_retiro(c["concepto_retiro"], reglas) == "TRANSFERENCIA_PROPIA"]


def _par(c, usd, llegada, banco, origen_llegada, confirmado_por):
    return {"fecha_salida": c["fecha"], "monto_q": csv_hechos.monto(c["monto_q"]),
            "fecha_llegada": llegada, "monto_usd": csv_hechos.monto(usd), "banco_destino": banco,
            "origen_salida": c["mov_id"], "origen_llegada": origen_llegada,
            "confirmado_por": confirmado_por}


def parear_automatico(cartera, banco, reglas, existentes, dias_habiles=DIAS_HABILES, banda=BANDA):
    """Propone los pares de los retiros propios que aún no tienen uno. Devuelve
    {pares, ambiguos, sin_par}; no escribe nada."""
    con_par = {e["origen_salida"] for e in existentes}
    llegadas_usadas = {e["origen_llegada"] for e in existentes}
    entradas = [b for b in banco if (b.get("tipo") or "").upper() == "ENTRADA"
                and _llave_banco(b) not in llegadas_usadas]
    pendientes = [c for c in _retiros_propios(cartera, reglas) if c["mov_id"] not in con_par]
    candidatas = {}
    for c in pendientes:
        q, plazo = float(c["monto_q"]), _plazo(c["fecha"], dias_habiles)
        candidatas[c["mov_id"]] = [
            b for b in entradas
            if c["fecha"] <= b["fecha"] <= plazo and float(b["monto"]) > 0
            and banda[0] <= q / float(b["monto"]) <= banda[1]]
    reclamos = {}
    for lista in candidatas.values():
        for b in lista:
            reclamos[_llave_banco(b)] = reclamos.get(_llave_banco(b), 0) + 1
    pares, ambiguos, sin_par = [], [], []
    for c in pendientes:
        lista = candidatas[c["mov_id"]]
        resumen = {"mov_id": c["mov_id"], "fecha": c["fecha"], "monto_q": c["monto_q"]}
        if not lista:
            sin_par.append(resumen)
        elif len(lista) > 1 or reclamos[_llave_banco(lista[0])] > 1:
            ambiguos.append(dict(resumen, candidatas=[
                {"fecha": b["fecha"], "monto_usd": b["monto"], "nombre": b["nombre"]} for b in lista]))
        else:
            b = lista[0]
            pares.append(_par(c, float(b["monto"]), b["fecha"], b["banco"], _llave_banco(b), "auto"))
    return {"pares": pares, "ambiguos": ambiguos, "sin_par": sin_par}


def par_manual(cartera, reglas, salida, usd, fecha_llegada, banco_destino, confirmado_por,
               banda=BANDA):
    """El par que confirma el operador para el retiro `salida` (mov_id de la billetera)."""
    c = next((x for x in cartera if x["mov_id"] == str(salida)), None)
    if c is None:
        raise ErrorFx("la billetera de Dropi no tiene el movimiento %s (ingerir_cartera.py)." % salida)
    clase = (gen_pl.clasificar_retiro(c["concepto_retiro"], reglas) if c["categoria"] == "RETIRO"
             else c["categoria"])
    if clase != "TRANSFERENCIA_PROPIA":
        raise ErrorFx("el movimiento %s es %s: solo una TRANSFERENCIA_PROPIA tiene dólares que llegan "
                      "a la cuenta del operador." % (salida, clase))
    if not usd or usd <= 0:
        raise ErrorFx("--usd debe ser mayor que cero.")
    tasa = float(c["monto_q"]) / usd
    if not banda[0] <= tasa <= banda[1]:
        raise ErrorFx("Q%s / $%.2f da una tasa de %.4f, fuera de la banda %.1f-%.1f: revisá los dólares."
                      % (c["monto_q"], usd, tasa, banda[0], banda[1]))
    return _par(c, usd, fecha_llegada or "", banco_destino, "operador", confirmado_por)


def fusionar(existentes, nuevas):
    """UPSERT por retiro de origen. Devuelve (filas, resumen)."""
    por_salida = {e["origen_salida"]: e for e in existentes}
    res = {"nuevas": 0, "actualizadas": 0, "sin_cambio": 0}
    for n in nuevas:
        previa = por_salida.get(n["origen_salida"])
        if previa is None:
            por_salida[n["origen_salida"]] = n
            res["nuevas"] += 1
        elif all((previa.get(c) or "") == (n.get(c) or "") for c in COLUMNAS):
            res["sin_cambio"] += 1
        else:
            por_salida[n["origen_salida"]] = n
            res["actualizadas"] += 1
    return sorted(por_salida.values(), key=lambda e: (e["fecha_salida"], e["origen_salida"])), res


def registrar(cartera, banco, reglas, destino=DESTINO, salida=None, usd=None, fecha_llegada="",
              banco_destino="MERCURY", confirmado_por="operador", escribir=False,
              dias_habiles=DIAS_HABILES, banda=BANDA):
    existentes = csv_hechos.leer(destino)
    if salida:
        nuevas = [par_manual(cartera, reglas, salida, usd, fecha_llegada, banco_destino,
                             confirmado_por, banda)]
        propuesta = {"pares": nuevas, "ambiguos": [], "sin_par": []}
    else:
        propuesta = parear_automatico(cartera, banco, reglas, existentes, dias_habiles, banda)
        nuevas = propuesta["pares"]
    filas, res = fusionar(existentes, nuevas)
    res.update(propuesta)
    res.update({"transferencias_guardadas": len(filas), "escrito": False})
    if escribir and (res["nuevas"] or res["actualizadas"]):
        csv_hechos.escribir(destino, COLUMNAS, filas)
        res["escrito"] = True
    return res


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--salida", help="mov_id del retiro de la billetera de Dropi (par del operador)")
    ap.add_argument("--usd", type=float, help="dólares que llegaron (con --salida)")
    ap.add_argument("--fecha-llegada", default="", help="YYYY-MM-DD; opcional si no se sabe")
    ap.add_argument("--banco", default="MERCURY", help="banco destino (con --salida)")
    ap.add_argument("--confirmado-por", default="operador")
    ap.add_argument("--dias-habiles", type=int, default=DIAS_HABILES)
    ap.add_argument("--tasa-min", type=float, default=BANDA[0])
    ap.add_argument("--tasa-max", type=float, default=BANDA[1])
    ap.add_argument("--escribir", action="store_true", help="persistir (sin esto solo mira)")
    ap.add_argument("--json", action="store_true", help="imprime solo el resumen en JSON")
    a = ap.parse_args(argv)
    if a.salida and a.usd is None:
        print("BLOQUEANTE: --salida necesita --usd.", file=sys.stderr)
        return 1
    try:
        res = registrar(csv_hechos.leer(os.path.join(gen_pl.P, "_FACT_CARTERA_DROPI.csv")),
                        csv_hechos.leer(os.path.join(gen_pl.P, "_FACT_BANCO.csv")),
                        gen_pl.load("_DIM_RETIROS.csv"), DESTINO, a.salida, a.usd, a.fecha_llegada,
                        a.banco.upper(), a.confirmado_por, a.escribir, a.dias_habiles,
                        (a.tasa_min, a.tasa_max))
    except ErrorFx as e:
        print("BLOQUEANTE: %s" % e, file=sys.stderr)
        return 1
    if a.json:
        print(json.dumps(res, ensure_ascii=False))
        return 0
    for p in res["pares"]:
        print("  par: retiro %s %s Q%s -> $%s (%s) tasa %.4f · %s" % (
            p["origen_salida"], p["fecha_salida"], p["monto_q"], p["monto_usd"],
            p["fecha_llegada"] or "llegada sin fecha", tasa_fx.tasa_de(p), p["confirmado_por"]))
    for x in res["ambiguos"]:
        print("  ⚠ ambiguo (no se empareja): retiro %s %s Q%s · %d candidatas" % (
            x["mov_id"], x["fecha"], x["monto_q"], len(x["candidatas"])))
    for x in res["sin_par"]:
        print("  sin entrada en el banco todavía: retiro %s %s Q%s (usá --salida %s --usd <dólares>)" % (
            x["mov_id"], x["fecha"], x["monto_q"], x["mov_id"]))
    print("nuevos %d · actualizados %d · sin cambio %d" % (res["nuevas"], res["actualizadas"], res["sin_cambio"]))
    print(("escrito: %s (%d transferencias)" % (DESTINO, res["transferencias_guardadas"])) if res["escrito"]
          else "(solo mirar: no se escribió nada; --escribir para persistir)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
