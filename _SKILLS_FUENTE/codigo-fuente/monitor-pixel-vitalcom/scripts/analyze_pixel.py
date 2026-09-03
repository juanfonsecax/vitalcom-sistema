#!/usr/bin/env python3
"""
analyze_pixel.py — Procesa stats de eventos de un Pixel (dataset) de Meta Ads y
detecta caidas de volumen.

Lee uno o mas archivos JSON de respuestas de ads_get_dataset_stats (aggregation=event)
que cubran una ventana de ~14 dias, parte cada bucket en dos mitades de 7 dias segun su
timestamp, suma por evento, y produce un reporte en Markdown.

Diseno: la skill consulta UN evento por llamada (event_name=...) sobre una ventana de
14 dias. Eso mantiene cada respuesta chica sin importar el volumen del pixel. El script
acepta varios de esos archivos y los acumula.

Uso:
  python3 analyze_pixel.py --stats EV1.json [EV2.json ...] --midpoint <unix_ts> \
      [--quality QUALITY.json] [--details DETAILS.json] [--floor 50] [--threshold 20]

  --stats      Uno o mas archivos de ads_get_dataset_stats. Por-evento o multi-evento;
               el script acumula todos.
  --midpoint   Timestamp Unix que separa la ventana previa (buckets antes) de la
               reciente (buckets en o despues). Normalmente: ahora - 7 dias.
  --quality    Respuesta de ads_get_dataset_quality (opcional).
  --details    Respuesta de ads_get_dataset_details (opcional).
  --floor      Volumen minimo en la ventana previa para que una caida cuente como
               alerta real. Default 50. Una caida del 20% sobre numeros chicos es ruido.
  --threshold  Porcentaje de caida que dispara la alerta. Default 20.
"""

import argparse
import glob
import json
import os
from datetime import datetime


def load(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def to_epoch(ts):
    """Convierte un timestamp ISO (ej '2026-05-14T16:00:00-0700') a epoch Unix."""
    if not ts:
        return None
    s = ts.strip()
    # Algunas versiones de Python necesitan el offset con dos puntos (-07:00).
    if len(s) >= 5 and s[-5] in "+-" and s[-3] != ":":
        s = s[:-2] + ":" + s[-2:]
    for cand in (s, s.replace("Z", "+00:00")):
        try:
            return datetime.fromisoformat(cand).timestamp()
        except Exception:
            continue
    return None


def accumulate(stats_json, midpoint, recent, prior):
    """Reparte los buckets de una respuesta de stats en recent/prior segun timestamp."""
    for bucket in stats_json.get("stats", []):
        ep = to_epoch(bucket.get("timestamp", ""))
        target = recent if (ep is not None and ep >= midpoint) else prior
        for item in bucket.get("data", []):
            ev = item.get("value")
            if ev is None:
                continue
            target[ev] = target.get(ev, 0) + int(item.get("count", 0) or 0)


def emq_label(score):
    if not isinstance(score, (int, float)):
        return "sin dato"
    if score >= 8:
        return "excelente"
    if score >= 6:
        return "aceptable"
    if score >= 4:
        return "bajo"
    return "critico"


def fmt_pct(change):
    return "n/d" if change is None else "{:+.1f}%".format(change)


def fmt_date(epoch):
    return datetime.fromtimestamp(epoch).strftime("%Y-%m-%d %H:%M")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stats", required=True, nargs="+")
    ap.add_argument("--midpoint", required=True, type=float)
    ap.add_argument("--quality")
    ap.add_argument("--details")
    ap.add_argument("--floor", type=int, default=50)
    ap.add_argument("--threshold", type=float, default=20.0)
    args = ap.parse_args()

    midpoint = args.midpoint
    recent, prior = {}, {}
    dsid = "?"
    # Permite pasar globs o un directorio.
    files = []
    for pat in args.stats:
        if os.path.isdir(pat):
            files += sorted(glob.glob(os.path.join(pat, "*.json")))
        else:
            files += sorted(glob.glob(pat)) or [pat]
    for path in files:
        try:
            sj = load(path)
        except Exception:
            continue
        if dsid == "?" and sj.get("dataset_id"):
            dsid = sj.get("dataset_id")
        accumulate(sj, midpoint, recent, prior)

    events = sorted(set(recent) | set(prior))
    rows, alerts = [], []
    for ev in events:
        r = recent.get(ev, 0)
        p = prior.get(ev, 0)
        change = None if p == 0 else (r - p) / p * 100.0
        below_floor = p < args.floor
        is_alert = (change is not None and change <= -args.threshold and not below_floor)
        if is_alert:
            status, emoji = "ALERTA", "\U0001F534"
        elif change is None:
            status, emoji = "nuevo", "\U0001F195"
        elif below_floor:
            status, emoji = "bajo volumen", "⚪"
        elif change <= -10:
            status, emoji = "vigilar", "\U0001F7E1"
        elif change >= 10:
            status, emoji = "subiendo", "\U0001F4C8"
        else:
            status, emoji = "estable", "\U0001F7E2"
        rows.append((ev, p, r, change, status, emoji))
        if is_alert:
            alerts.append((ev, p, r, change))

    # --- metadatos del dataset ---
    name = active = last_fired = server_last_fired = None
    if args.details:
        try:
            d = load(args.details)
            if isinstance(d, dict):
                d = d.get("metadata", d)  # la respuesta real anida bajo "metadata"
                name = d.get("name")
                active = d.get("is_active")
                last_fired = d.get("last_fired_time")
                server_last_fired = d.get("server_last_fired_time")
                dsid = d.get("dataset_id", dsid)
        except Exception:
            pass

    out = []
    out.append("# \U0001F50D Monitor de Pixel — {}".format(name or "Dataset {}".format(dsid)))
    out.append("")
    meta = "**Dataset ID:** {}".format(dsid)
    if active is not None:
        meta += " · **Estado:** {}".format("activo ✅" if active else "INACTIVO ⚠️")
    out.append(meta)
    out.append("**Ventana reciente:** {} → {}".format(
        fmt_date(midpoint), fmt_date(midpoint + 604800)))
    out.append("**Ventana previa:** {} → {}".format(
        fmt_date(midpoint - 604800), fmt_date(midpoint)))
    out.append("")

    # --- alertas ---
    out.append("## \U0001F6A8 Alertas")
    out.append("")
    if alerts:
        out.append("Eventos con caida superior al {:.0f}% (y volumen suficiente para "
                   "descartar ruido):".format(args.threshold))
        out.append("")
        for ev, p, r, change in alerts:
            out.append("- \U0001F534 **{}**: {} → {} ({}) en 7 dias.".format(
                ev, p, r, fmt_pct(change)))
        out.append("")
        out.append("> Posibles causas a revisar: el pixel removido de alguna pagina, un "
                   "cambio en la web o el tag manager, un evento mal disparado, o una "
                   "caida real de trafico/campanas.")
    else:
        out.append("✅ Sin alertas. Ningun evento con volumen relevante cayo mas "
                   "del {:.0f}%.".format(args.threshold))
    out.append("")

    # --- tabla de volumen ---
    out.append("## \U0001F4CA Volumen de eventos (7 dias vs 7 dias previos)")
    out.append("")
    out.append("| Evento | 7d previos | Ultimos 7d | Cambio | Estado |")
    out.append("|---|---:|---:|---:|---|")

    def sort_key(row):
        sev = {"ALERTA": 0, "vigilar": 1}.get(row[4], 2)
        return (sev, -(row[2] or 0))

    for ev, p, r, change, status, emoji in sorted(rows, key=sort_key):
        out.append("| {} | {} | {} | {} | {} {} |".format(
            ev, p, r, fmt_pct(change), emoji, status))
    out.append("")
    out.append("_Piso de ruido: {} eventos en la ventana previa. Eventos por debajo "
               "(⚪) se reportan pero no disparan alerta._".format(args.floor))
    out.append("")

    # --- EMQ ---
    if args.quality:
        try:
            q = load(args.quality)
        except Exception:
            q = None
        if isinstance(q, dict):
            out.append("## \U0001F3AF Calidad de coincidencia de eventos (EMQ)")
            out.append("")
            for channel, evlist in q.items():
                if not isinstance(evlist, list):
                    continue
                out.append("**Canal: {}**".format(channel))
                out.append("")
                out.append("| Evento | EMQ | Lectura | Llaves debiles (<70%) |")
                out.append("|---|---:|---|---|")
                for e in evlist:
                    en = e.get("event_name", "?")
                    emq = e.get("event_match_quality") or {}
                    score = emq.get("composite_score")
                    weak = []
                    for mk in emq.get("match_key_feedback", []) or []:
                        cov = (mk.get("coverage") or {}).get("percentage")
                        if isinstance(cov, (int, float)) and cov < 70:
                            weak.append("{} {:.0f}%".format(mk.get("identifier", "?"), cov))
                    score_txt = "{:.1f}".format(score) if isinstance(score, (int, float)) else "—"
                    out.append("| {} | {} | {} | {} |".format(
                        en, score_txt, emq_label(score), ", ".join(weak) if weak else "—"))
                out.append("")
            out.append("_Escala EMQ 0–10: ≥8 excelente · 6–7.9 aceptable · 4–5.9 bajo · "
                       "<4 critico. Subir la cobertura de email/telefono es lo que mas "
                       "mueve el score._")
            out.append("")

    # --- salud del dataset ---
    out.append("## \U0001FA7A Salud del dataset")
    out.append("")
    if active is not None:
        out.append("- Estado: {}".format(
            "activo" if active else "**INACTIVO** — el pixel no esta recibiendo eventos."))
    if last_fired:
        out.append("- Ultimo evento (navegador): {}".format(last_fired))
        dt = to_epoch(last_fired)
        if dt is not None:
            hours = (datetime.now().timestamp() - dt) / 3600.0
            if hours > 24:
                out.append("  - ⚠️ Hace ~{:.0f} horas. Revisa si el pixel "
                           "dejo de disparar.".format(hours))
    if server_last_fired:
        dt = to_epoch(server_last_fired)
        if dt is not None and datetime.fromtimestamp(dt).year <= 1970:
            out.append("- Eventos de servidor (CAPI): **ninguno**. Sin Conversions API "
                       "el pixel depende solo del navegador y es mas fragil a la perdida "
                       "de senal. Considera activarla.")
        elif server_last_fired:
            out.append("- Ultimo evento de servidor (CAPI): {}".format(server_last_fired))
    out.append("")

    print("\n".join(out))


if __name__ == "__main__":
    main()
