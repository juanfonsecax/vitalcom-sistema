#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_split_doctrina.py — GATE DE VERBATIM (T2, p2-simplificacion, 24-sep-2026).

Por que existe
--------------
T2 partio dos "nodos dios" (`DOCTRINA/ESCALADO_PLAYBOOK.md` y `DOCTRINA/PLANTILLAS_ADS.md`,
9.5k y 8.8k tokens heredados por 6 agentes cada uno) en archivos por seccion, para que cada
consumidor cite solo la seccion que usa. La regla del CLAUDE.md del orquestador es "doctrine
text unchanged, only cut": ninguna palabra se reescribio. Este test es la prueba de eso, no
una opinion: reconstruye cada archivo original concatenando sus secciones EN ORDEN y compara
el resultado, byte a byte, contra el sha256 del original congelado el dia del split (via git
show del commit anterior al split, o contra el snapshot que este archivo trae abajo).

Si algun dia se edita una seccion (doctrina que cambia de verdad, no un split), este test
FALLA a proposito: hay que actualizar el hash congelado en el mismo commit que cambia la
doctrina, nunca antes ni "para que pase".

USO:  python Ads/_TOOLS/test_split_doctrina.py     (exit 0 = pasa, 1 = falla)
"""

import hashlib
import io
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(BASE)

# sha256 del archivo ORIGINAL (monolitico) el 24-sep-2026, antes del split de T2.
# Congelado con: python -c "import hashlib; print(hashlib.sha256(open(p,'rb').read()).hexdigest())"
# ESCALADO_SHA256 y PLANTILLAS_SHA256 re-congelados en T4b (2026-09-24): el operador autorizo
# remover la narracion arqueologica de DOCTRINA/ESCALADO/*.md y DOCTRINA/PLANTILLAS_ADS_SECCIONES/*.md
# manteniendo la regla; el texto cambio a proposito.
# ESCALADO_SHA256 re-congelado (28-sep-2026, cuatro fases B2): 04_PALANCAS.md, 08_PLAN_ENTREGABLE.md
# y 09_EXPLORACION_PARALELA.md pasaron sus referencias de "FASE 3"/F3.* (que ahora es la fase de
# optimizacion de flujo) a "FASE 4"/F4.* (escalado) — cambio de doctrina a proposito.
# ESCALADO_SHA256 y PLANTILLAS_SHA256 re-congelados (multi-mercado D6): la doctrina de escalado y de
# plantillas nombra la moneda y el mercado del producto en vez de asumir Guatemala.
ESCALADO_SHA256 = "965b8716d1cca0bd229046dd08d9c12a89265f74dd1e83d1ea68afbb9e044222"
PLANTILLAS_SHA256 = "ec888fd02f1f38b773fb6ad9491ea1da12fb724d1b07c26d1153c47adf3fa53c"

# Orden EXACTO de reconstruccion — el nombre de archivo ya lo fija (prefijo numerico),
# pero se declara explicito para que un archivo nuevo mal nombrado no se cuele fuera de orden.
ESCALADO_ORDEN = [
    "00_INTRO_FILOSOFIA.md", "01_TIMING.md", "02_PRESUPUESTO_DECISION.md",
    "03_SENALES_DECISION.md", "04_PALANCAS.md", "05_REPLICAR_GANADOR.md",
    "06_SATURACION_CUENTA.md", "07_MATRIZ_DUPLICACION.md", "08_PLAN_ENTREGABLE.md",
    "09_EXPLORACION_PARALELA.md", "10_METRICAS_TESTEO.md",
]
PLANTILLAS_ORDEN = [
    "00_INTRO.md", "01_COMPLIANCE_ANDROMEDA.md", "02_ENFOQUE_AGRESIVO.md",
    "03_CUAL_PROMPT_USAR.md", "04_PROMPT_CONTROL_FASE1.md", "05_PROMPT_MAESTRO_FASE2.md",
    "06_ESTILOS_ANTIFATIGA.md", "07_HOOK_VISUAL.md", "08_MAPA_VARIABLES.md",
    "09_CONEXION.md", "10_ELEMENTOS_EXTRA.md", "11_DOCTRINA_CREATIVOS_VIDEO_IMAGEN.md",
]


def leer(ruta):
    # Sin fin de linea: core.autocrlf decide CRLF o LF al sacar el archivo de git.
    return io.open(ruta, encoding="utf-8", newline="").read().replace("\r\n", "\n")


def reconstruir(carpeta, orden):
    return "".join(leer(os.path.join(carpeta, f)) for f in orden)


def sha256(texto):
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def test_escalado_playbook_es_verbatim():
    reconstruido = reconstruir("DOCTRINA/ESCALADO", ESCALADO_ORDEN)
    assert sha256(reconstruido) == ESCALADO_SHA256, (
        "DOCTRINA/ESCALADO/*.md ya no reconstruye el ESCALADO_PLAYBOOK.md original: "
        "una seccion se reescribio o el orden de reconstruccion no es el original. "
        "Si la doctrina cambio A PROPOSITO, actualizar ESCALADO_SHA256 en este mismo commit.")


def test_escalado_playbook_carpeta_sin_extras():
    """Ningun archivo suelto en la carpeta que test_escalado_playbook_es_verbatim no vea."""
    en_disco = sorted(f for f in os.listdir("DOCTRINA/ESCALADO") if f.endswith(".md"))
    assert en_disco == sorted(ESCALADO_ORDEN), (
        "DOCTRINA/ESCALADO/ tiene archivos que ESCALADO_ORDEN no conoce (o le faltan): %s"
        % (set(en_disco) ^ set(ESCALADO_ORDEN)))


def test_plantillas_ads_es_verbatim():
    reconstruido = reconstruir("DOCTRINA/PLANTILLAS_ADS_SECCIONES", PLANTILLAS_ORDEN)
    assert sha256(reconstruido) == PLANTILLAS_SHA256, (
        "DOCTRINA/PLANTILLAS_ADS_SECCIONES/*.md ya no reconstruye el PLANTILLAS_ADS.md original: "
        "una seccion se reescribio o el orden de reconstruccion no es el original. "
        "Si la doctrina cambio A PROPOSITO, actualizar PLANTILLAS_SHA256 en este mismo commit.")


def test_plantillas_ads_carpeta_sin_extras():
    en_disco = sorted(f for f in os.listdir("DOCTRINA/PLANTILLAS_ADS_SECCIONES") if f.endswith(".md"))
    assert en_disco == sorted(PLANTILLAS_ORDEN), (
        "DOCTRINA/PLANTILLAS_ADS_SECCIONES/ tiene archivos que PLANTILLAS_ORDEN no conoce (o le faltan): %s"
        % (set(en_disco) ^ set(PLANTILLAS_ORDEN)))


def test_indices_son_pequenos():
    """Los archivos raiz son INDICE, no la doctrina: deben quedar chicos (< 3.5k bytes)."""
    for ruta in ("DOCTRINA/ESCALADO_PLAYBOOK.md", "DOCTRINA/PLANTILLAS_ADS.md"):
        tam = os.path.getsize(ruta)
        assert tam < 3500, (
            "%s pesa %d bytes: si volvio a crecer, alguien le pego doctrina de vuelta "
            "en vez de dejarlo como indice." % (ruta, tam))


def main():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    fallos = 0
    for t in tests:
        try:
            t()
            print("PASS", t.__name__)
        except AssertionError as e:
            fallos += 1
            print("FAIL", t.__name__, "-", e)
    print("\n%d/%d pasaron" % (len(tests) - fallos, len(tests)))
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())
