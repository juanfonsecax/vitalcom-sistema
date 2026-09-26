#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""medir_tokens.py — CONSUMO REAL de tokens, leído de los transcripts de Claude Code.

Cualquier cifra de tokens del sistema que no salga de acá es una ESTIMACIÓN (gen_grafo.py mide
bytes de prompt / 3.6). Esta herramienta lee lo que la API efectivamente cobró: el bloque
`usage` de cada respuesta del modelo en `~/.claude/projects/<proyecto>/*.jsonl`, incluidos los
subagentes (`<sesión>/subagents/agent-*.jsonl`, cuyo tipo — `etapa-7`, `Explore`… — viene en el
`.meta.json` vecino).

Qué cuenta cada columna:
  entrada     tokens de entrada sin caché
  cache_esc   tokens escritos a la caché (se cobran más caros que la entrada)
  cache_lec   tokens leídos de la caché (se cobran a una fracción de la entrada)
  salida      tokens generados
  contexto    entrada + cache_esc + cache_lec: lo que el modelo tuvo delante, sumado por llamada

Un mismo mensaje puede aparecer varias veces en el JSONL (streaming): se cuenta UNA vez por
`message.id`, con su última versión.

SOLO LECTURA: nunca escribe. Sin `--desde`, mide los últimos 7 días.

USO:  python Ads/_TOOLS/medir_tokens.py                      (por origen y por agente, 7 días)
      python Ads/_TOOLS/medir_tokens.py --desde 2026-09-20
      python Ads/_TOOLS/medir_tokens.py --por dia             (origen | agente | dia | sesion)
      python Ads/_TOOLS/medir_tokens.py --json
"""

import argparse
import datetime
import glob
import json
import os
import sys
from collections import defaultdict

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, OSError):
    pass

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
COLUMNAS = ("entrada", "cache_esc", "cache_lec", "salida")


def slug_proyecto(ruta):
    """Claude Code nombra la carpeta del proyecto reemplazando todo lo no alfanumérico por '-'."""
    return "".join(c if c.isalnum() else "-" for c in os.path.abspath(ruta))


def carpetas_proyecto(raiz_projects, base=BASE):
    """La carpeta del repo y sus variantes (worktrees, -app): todo lo que empiece con su slug.
    Sin distinguir mayúsculas: en Windows la letra de unidad aparece como 'c--' o 'C--'."""
    slug = slug_proyecto(base).lower()
    return sorted(d for d in glob.glob(os.path.join(raiz_projects, "*"))
                  if os.path.isdir(d) and os.path.basename(d).lower().startswith(slug))


def _agente(ruta_jsonl):
    meta = ruta_jsonl[:-len(".jsonl")] + ".meta.json"
    try:
        with open(meta, encoding="utf-8") as f:
            return json.load(f).get("agentType") or "subagente"
    except (OSError, ValueError):
        return "subagente"


def leer_llamadas(carpetas, desde=None):
    """Una fila por respuesta del modelo: dict con sesion, dia, origen, agente, modelo y usage."""
    vistos = {}
    for carpeta in carpetas:
        archivos = glob.glob(os.path.join(carpeta, "*.jsonl"))
        archivos += glob.glob(os.path.join(carpeta, "*", "subagents", "*.jsonl"))
        for ruta in archivos:
            es_sub = os.path.basename(os.path.dirname(ruta)) == "subagents"
            agente = _agente(ruta) if es_sub else "principal"
            origen_sesion = None
            try:
                f = open(ruta, encoding="utf-8")
            except OSError:
                continue
            with f:
                for linea in f:
                    try:
                        o = json.loads(linea)
                    except ValueError:
                        continue
                    origen_sesion = o.get("entrypoint") or origen_sesion
                    msg = o.get("message") or {}
                    u = msg.get("usage") if o.get("type") == "assistant" else None
                    if not u:
                        continue
                    dia = (o.get("timestamp") or "")[:10]
                    if desde and dia < desde:
                        continue
                    clave = msg.get("id") or "%s:%s" % (ruta, o.get("uuid"))
                    vistos[clave] = {
                        "sesion": o.get("sessionId") or os.path.basename(ruta),
                        "dia": dia,
                        "origen": origen_sesion or "?",
                        "agente": agente,
                        "modelo": msg.get("model") or "?",
                        "entrada": u.get("input_tokens") or 0,
                        "cache_esc": u.get("cache_creation_input_tokens") or 0,
                        "cache_lec": u.get("cache_read_input_tokens") or 0,
                        "salida": u.get("output_tokens") or 0,
                    }
    return list(vistos.values())


def agregar(llamadas, por):
    grupos = defaultdict(lambda: dict({c: 0 for c in COLUMNAS}, llamadas=0, sesiones=set()))
    for ll in llamadas:
        g = grupos[ll[por]]
        g["llamadas"] += 1
        g["sesiones"].add(ll["sesion"])
        for c in COLUMNAS:
            g[c] += ll[c]
    filas = []
    for k, g in grupos.items():
        fila = {por: k, "llamadas": g["llamadas"], "sesiones": len(g["sesiones"])}
        fila.update({c: g[c] for c in COLUMNAS})
        fila["contexto"] = g["entrada"] + g["cache_esc"] + g["cache_lec"]
        filas.append(fila)
    return sorted(filas, key=lambda f: f["contexto"], reverse=True)


def _k(n):
    return "%.1fM" % (n / 1e6) if n >= 1e6 else "%.1fK" % (n / 1e3) if n >= 1e3 else str(n)


def imprimir(filas, por):
    print("%-28s %6s %6s %9s %9s %9s %8s %9s" % (por.upper(), "llam.", "ses.", "entrada",
                                                  "cache_esc", "cache_lec", "salida", "contexto"))
    for f in filas:
        print("%-28s %6d %6d %9s %9s %9s %8s %9s" % (
            str(f[por])[:28], f["llamadas"], f["sesiones"], _k(f["entrada"]), _k(f["cache_esc"]),
            _k(f["cache_lec"]), _k(f["salida"]), _k(f["contexto"])))


def main(argv=None):
    ap = argparse.ArgumentParser(description="Consumo real de tokens desde los transcripts.")
    ap.add_argument("--desde", help="YYYY-MM-DD (por defecto: hace 7 días)")
    ap.add_argument("--por", choices=("origen", "agente", "dia", "sesion"), action="append",
                    help="agrupar por (repetible). Por defecto: origen y agente")
    ap.add_argument("--projects", default=os.path.join(os.path.expanduser("~"), ".claude", "projects"))
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)

    desde = a.desde or (datetime.date.today() - datetime.timedelta(days=7)).isoformat()
    carpetas = carpetas_proyecto(a.projects)
    if not carpetas:
        print("No hay transcripts para este proyecto en %s" % a.projects, file=sys.stderr)
        return 1
    llamadas = leer_llamadas(carpetas, desde)
    grupos = a.por or ["origen", "agente"]
    salida = {por: agregar(llamadas, por) for por in grupos}

    if a.json:
        print(json.dumps({"desde": desde, "llamadas": len(llamadas), "grupos": salida},
                         ensure_ascii=False, indent=1))
        return 0
    print("CONSUMO REAL desde %s · %d llamadas al modelo · %d carpetas de proyecto\n"
          % (desde, len(llamadas), len(carpetas)))
    for por in grupos:
        imprimir(salida[por], por)
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
