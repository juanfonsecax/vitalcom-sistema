#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_gen_reglas_etapas.py — CONGELA la skill `reglas-sistema` y su precarga.

La skill se GENERA desde CLAUDE.md (gen_reglas_etapas.py --escribir): si alguien
edita CLAUDE.md sin regenerar, este test falla y dice como regenerar. Los 15
subagentes de etapa la precargan con omitClaudeMd + skills en su frontmatter.

USO:  python Ads/_TOOLS/test_gen_reglas_etapas.py     (exit 0 = pasa, 1 = falla)
"""

import glob
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_reglas_etapas as GR  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, OSError):
    pass

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FALLAS = []


def check(nombre, cond, detalle=""):
    if cond:
        print("  ok   %s" % nombre)
    else:
        print("  FALLA %s  %s" % (nombre, detalle))
        FALLAS.append(nombre)


def test_skill_en_disco_igual_a_contenido():
    """La skill en disco es identica a gen_reglas_etapas.contenido()."""
    ruta = os.path.join(BASE, ".claude", "skills", "reglas-sistema", "SKILL.md")
    if not os.path.isfile(ruta):
        check("la skill existe en disco", False, ruta)
        return
    with io.open(ruta, encoding="utf-8") as fh:
        disco = fh.read()
    check("la skill en disco es identica a contenido() "
          "(si falla: python Ads/_TOOLS/gen_reglas_etapas.py --escribir)",
          disco == GR.contenido(), "difiere en %d caracteres" % abs(len(disco) - len(GR.contenido())))


def test_contenido_trae_constantes_e_invariantes():
    """El contenido incluye el angulo-por-que-duele y los invariantes 1 a 13."""
    texto = GR.contenido()
    check("incluye la definicion de angulo", "ÁNGULO = por qué duele" in texto)
    faltan = ["%d. " % n for n in range(1, 14)
              if not any(l.startswith("%d. " % n) for l in texto.splitlines())]
    check("incluye los invariantes 1 a 13", not faltan, "faltan: %s" % faltan)


def test_contenido_no_trae_orquestador():
    """El contenido NO incluye el mapa de archivos ni el arranque de sesion."""
    texto = GR.contenido()
    check("no incluye MAPA DE ARCHIVOS", "MAPA DE ARCHIVOS" not in texto)
    check("no incluye ARRANQUE DE SESIÓN", "ARRANQUE DE SESIÓN" not in texto)


def test_agentes_precargan_la_skill():
    """Los 15 agentes tienen omitClaudeMd: true y reglas-sistema en skills:."""
    archivos = sorted(glob.glob(os.path.join(BASE, ".claude", "agents", "ETAPA-*.md")))
    check("son 15 agentes", len(archivos) == 15, len(archivos))
    for ruta in archivos:
        with io.open(ruta, encoding="utf-8") as fh:
            texto = fh.read()
        nombre = os.path.basename(ruta)
        if not texto.startswith("---"):
            check("%s tiene frontmatter" % nombre, False)
            continue
        frente = texto[3:texto.find("\n---", 3)]
        check("%s omite CLAUDE.md y precarga reglas-sistema" % nombre,
              "omitClaudeMd: true" in frente and "reglas-sistema" in frente, frente[-120:])


def main():
    print("test_gen_reglas_etapas.py — skill reglas-sistema y su precarga\n")
    for fn in (test_skill_en_disco_igual_a_contenido,
               test_contenido_trae_constantes_e_invariantes,
               test_contenido_no_trae_orquestador,
               test_agentes_precargan_la_skill):
        print("\n%s" % (fn.__doc__ or fn.__name__).splitlines()[0])
        fn()
    print("\n%s" % ("TODO PASA" if not FALLAS else "FALLAN %d: %s"
                    % (len(FALLAS), ", ".join(FALLAS))))
    return 1 if FALLAS else 0


if __name__ == "__main__":
    sys.exit(main())
