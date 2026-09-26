#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests de medir_tokens.py sobre un directorio de transcripts falso (nunca lee los reales)."""

import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import medir_tokens as m  # noqa: E402

FALLAS = []


def check(cond, nombre, detalle=""):
    print("  %-6s %s%s" % ("OK" if cond else "FALLA", nombre, ("  -> " + detalle) if not cond else ""))
    if not cond:
        FALLAS.append(nombre)


def _linea(msg_id, dia, usage, entrypoint="claude-desktop", sesion="S1"):
    return json.dumps({"type": "assistant", "timestamp": dia + "T10:00:00Z", "sessionId": sesion,
                       "entrypoint": entrypoint,
                       "message": {"id": msg_id, "model": "claude-x", "usage": usage}})


def main():
    raiz = tempfile.mkdtemp()
    base = os.path.join(raiz, "REPO")
    # la carpeta en disco empieza en minuscula aunque el slug calculado no
    carpeta = os.path.join(raiz, "projects", m.slug_proyecto(base).lower())
    sub = os.path.join(carpeta, "S1", "subagents")
    os.makedirs(sub)
    u = {"input_tokens": 1, "cache_creation_input_tokens": 10, "cache_read_input_tokens": 100,
         "output_tokens": 5}
    with open(os.path.join(carpeta, "S1.jsonl"), "w", encoding="utf-8") as f:
        # el mismo mensaje dos veces (streaming) cuenta una sola vez
        f.write(_linea("A", "2026-09-20", u) + "\n")
        f.write(_linea("A", "2026-09-20", u) + "\n")
        f.write(_linea("B", "2026-09-01", u) + "\n")
        f.write("no es json\n")
    with open(os.path.join(sub, "agent-x.jsonl"), "w", encoding="utf-8") as f:
        f.write(_linea("C", "2026-09-21", u) + "\n")
    with open(os.path.join(sub, "agent-x.meta.json"), "w", encoding="utf-8") as f:
        json.dump({"agentType": "etapa-7"}, f)
    os.makedirs(os.path.join(raiz, "projects", "otro-proyecto"))

    carpetas = m.carpetas_proyecto(os.path.join(raiz, "projects"), base)
    check(carpetas == [carpeta], "encuentra la carpeta aunque difiera en mayusculas", str(carpetas))

    ll = m.leer_llamadas(carpetas, "2026-09-10")
    check(len(ll) == 2, "dedup por message.id y filtro --desde", str(len(ll)))

    por_agente = {f["agente"]: f for f in m.agregar(ll, "agente")}
    check(set(por_agente) == {"principal", "etapa-7"}, "el subagente toma su tipo del .meta.json",
          str(set(por_agente)))
    check(por_agente["etapa-7"]["contexto"] == 111, "contexto = entrada + cache_esc + cache_lec",
          str(por_agente["etapa-7"]))

    print("\n%d fallas." % len(FALLAS))
    return 1 if FALLAS else 0


if __name__ == "__main__":
    sys.exit(main())
