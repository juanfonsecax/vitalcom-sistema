"""etapa-5 — flujo LucidBot: bloques de juicio obligatorios (DOCTRINA/
PLANTILLAS_FLUJO_BOT.md), tono voseo guatemalteco (CLAUDE.md TONALIDAD BASE),
y ninguna claim de cura/eliminación fuera de una nota de compliance."""
from __future__ import annotations

import re

from _util import resultado

BLOQUES_REQUERIDOS = [
    "descripcion", "modo_de_uso", "caracteristicas", "contenido",
    "testimonios", "audio", "m2", "faq_venta", "faq_postventa",
]
BLOQUE_RE = re.compile(r"<<BLOQUE:(\w+)>>")
VOSEO_RE = re.compile(r"(?i)\bvos\b|\b\w+(?:é|á)s\b")
FALSO_VOSEO_RE = re.compile(r"(?i)^despu[eé]s$")
CLAIM_PROHIBIDA_RE = re.compile(r"(?i)\b(cura|elimina)\b")
NEGACION_CERCA_RE = re.compile(r"(?i)nunca|jamás|prohibid")


def _bloques_presentes(output: str) -> set[str]:
    return set(BLOQUE_RE.findall(output))


def _cuenta_voseo(output: str) -> int:
    return sum(1 for m in VOSEO_RE.finditer(output) if not FALSO_VOSEO_RE.match(m.group(0)))


def _claims_no_marcadas(output: str) -> list[str]:
    hallados = []
    for m in CLAIM_PROHIBIDA_RE.finditer(output):
        ventana = output[max(0, m.start() - 40):m.start()]
        if not NEGACION_CERCA_RE.search(ventana):
            hallados.append(m.group(0))
    return hallados


def get_assert(output: str, context: dict) -> dict:
    presentes = _bloques_presentes(output)
    faltantes = [b for b in BLOQUES_REQUERIDOS if b not in presentes]
    if faltantes:
        return resultado(False, f"faltan bloques <<BLOQUE:x>> obligatorios: {faltantes}")

    voseo = _cuenta_voseo(output)
    if voseo < 3:
        return resultado(False, f"tono voseo insuficiente ({voseo} marcador(es) — se esperaban >=3)")

    claims = _claims_no_marcadas(output)
    if claims:
        return resultado(False, f"claim(s) de cura/eliminación sin marcar como prohibida: {claims}")

    return resultado(True, f"{len(BLOQUES_REQUERIDOS)} bloques presentes, {voseo} marcadores de voseo, sin claims prohibidas")
