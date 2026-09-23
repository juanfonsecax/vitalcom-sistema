"""etapa-1b — componentes + voz del cliente. Dos reglas mecánicas derivadas de
CLAUDE.md/DOCTRINA/COPYWRITING_ADS.md que aplican tanto a la síntesis de
ingredientes como a la minería de voz real:

1. No hay una claim absoluta de "cura" sin que la propia nota diga que está
   PROHIBIDA (patrón real en TINNIDROP: 'NUNCA "cura/elimina/repara el
   tinnitus"' es la nota de compliance, no una promesa — se acepta solo si
   "cura" aparece precedida de una negación/advertencia cercana).
2. Si el fragmento cita voz real entre comillas, cada cita debe llevar su
   fuente entre paréntesis inmediatamente después (regla del banco de voz:
   una cita sin fuente no es evidencia, es una frase inventada).
"""
from __future__ import annotations

import re

from _util import resultado

CURA_RE = re.compile(r"(?i)\bcura\b")
NEGACION_CERCA_RE = re.compile(r"(?i)nunca|prohibid|jamás")
CITA_CON_FUENTE_RE = re.compile(r'"[^"\n]{4,}"\s*[\[\(][^\)\]\n]{2,80}[\)\]]')
CITA_RE = re.compile(r'"[^"\n]{4,}"')
VOZ_CLIENTE_HEADER_RE = re.compile(r"(?i)voz del cliente|voz-real|voz real")


def _seccion_voz_cliente(output: str) -> str | None:
    """Devuelve solo el tramo del fixture que es banco de voz del cliente
    (citas reales con fuente) — el resto puede tener frases entre comillas
    que son parafraseo de doctrina, no citas a verificar (p.ej. TINNIDROP:
    "apoya/ayuda a reducir" dentro de una nota de compliance)."""
    m = VOZ_CLIENTE_HEADER_RE.search(output)
    return output[m.start():] if m else None


def _cura_es_prohibicion_no_promesa(output: str) -> bool:
    for m in CURA_RE.finditer(output):
        ventana = output[max(0, m.start() - 40):m.start()]
        if not NEGACION_CERCA_RE.search(ventana):
            return False
    return True


def get_assert(output: str, context: dict) -> dict:
    contenido = [l for l in output.splitlines() if l.strip()]
    if len(contenido) < 3:
        return resultado(False, "fragmento demasiado corto para ser un output real de etapa-1b")
    if not _cura_es_prohibicion_no_promesa(output):
        return resultado(False, "aparece 'cura' sin que esté marcada como claim prohibida (posible promesa no permitida)")

    seccion_voz = _seccion_voz_cliente(output)
    if seccion_voz is None:
        return resultado(True, "sin claim de cura no marcada; sin sección de voz del cliente que verificar en este fragmento")

    citas = CITA_RE.findall(seccion_voz)
    if not citas:
        return resultado(False, "hay sección de voz del cliente pero ninguna cita textual entre comillas")
    citas_con_fuente = CITA_CON_FUENTE_RE.findall(seccion_voz)
    if len(citas_con_fuente) < len(citas):
        return resultado(False, f"{len(citas) - len(citas_con_fuente)} cita(s) de voz del cliente sin fuente entre paréntesis/corchetes inmediatamente después")
    return resultado(True, f"sin claim de cura no marcada; {len(citas)} cita(s) de voz del cliente, todas con fuente")
