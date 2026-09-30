#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen_reglas_etapas.py — GENERA la skill `reglas-sistema` desde CLAUDE.md.

Por que existe
--------------
Los 15 subagentes de etapa heredaban `CLAUDE.md` entero (orquestador + mapa de
archivos + arranque de sesion). Esta skill les entrega SOLO lo que una etapa
necesita: las CONSTANTES y los INVARIANTES. Los agentes la precargan con
`omitClaudeMd: true` + `skills: [reglas-sistema]` en su frontmatter.

Lo que hace: extrae DOS tramos de `CLAUDE.md` (raiz del repo), sin cambiar ni
una palabra, y los escribe como `.claude/skills/reglas-sistema/SKILL.md`.

Uso (un "mirar" nunca escribe):
    python Ads/_TOOLS/gen_reglas_etapas.py              # compara, no escribe
    python Ads/_TOOLS/gen_reglas_etapas.py --escribir   # escribe la skill
"""

import io
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, OSError):
    pass

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CLAUDE = os.path.join(BASE, "CLAUDE.md")
DESTINO = os.path.join(BASE, ".claude", "skills", "reglas-sistema", "SKILL.md")

ENC_CONSTANTES = "## CONSTANTES DEL SISTEMA"
ENC_ARRANQUE = "## ARRANQUE DE SESIÓN"
ENC_INVARIANTES = "## INVARIANTES DEL ORQUESTADOR"

CABECERA = """---
name: reglas-sistema
description: "Constantes e invariantes del SISTEMA VITALCOM que aplican a toda etapa. Se precarga en los subagentes de etapa; no se invoca a mano."
---

# REGLAS DEL SISTEMA PARA TODA ETAPA

> GENERADO desde `CLAUDE.md` por `Ads/_TOOLS/gen_reglas_etapas.py`. No editar: se edita
> `CLAUDE.md` y se regenera con `--escribir`.

"""


def _tramos():
    """(tramo A, tramo B) desde CLAUDE.md. Falla con SystemExit si falta un encabezado."""
    with io.open(CLAUDE, encoding="utf-8") as fh:
        lineas = fh.read().splitlines()
    i_const = next((i for i, l in enumerate(lineas) if l.startswith(ENC_CONSTANTES)), None)
    i_arr = next((i for i, l in enumerate(lineas) if l.startswith(ENC_ARRANQUE)), None)
    i_inv = next((i for i, l in enumerate(lineas) if l.startswith(ENC_INVARIANTES)), None)
    faltan = [e for e, i in ((ENC_CONSTANTES, i_const), (ENC_ARRANQUE, i_arr),
                             (ENC_INVARIANTES, i_inv)) if i is None]
    if faltan:
        print("FALTA encabezado en CLAUDE.md: %s" % ", ".join(faltan))
        raise SystemExit(1)
    tramo_a = lineas[i_const:i_arr]
    tramo_b = lineas[i_inv:]
    while tramo_a and tramo_a[-1].strip() == "---":
        tramo_a.pop()
    while tramo_b and tramo_b[-1].strip() == "---":
        tramo_b.pop()
    return tramo_a, tramo_b


def contenido():
    """El texto completo de la skill, para escribir o comparar (el test lo usa)."""
    tramo_a, tramo_b = _tramos()
    return CABECERA + "\n".join(tramo_a) + "\n\n" + "\n".join(tramo_b) + "\n"


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    escribir = "--escribir" in args
    try:
        texto = contenido()
    except SystemExit as error:
        return error.code if isinstance(error.code, int) else 1
    if not escribir:
        if not os.path.isfile(DESTINO):
            print("NO EXISTE: %s" % os.path.relpath(DESTINO, BASE))
            return 1
        with io.open(DESTINO, encoding="utf-8") as fh:
            actual = fh.read()
        if actual == texto:
            print("EN SINCRONIA")
            return 0
        print("DESINCRONIZADO: regenerar con --escribir")
        return 1
    os.makedirs(os.path.dirname(DESTINO), exist_ok=True)
    with io.open(DESTINO, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(texto)
    print(os.path.relpath(DESTINO, BASE))
    return 0


if __name__ == "__main__":
    sys.exit(main())
