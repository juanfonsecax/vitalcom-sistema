"""etapa-4 (MODO FASE 1, tarea 1) — contrato de ETAPA-4.md "Tarea 1 — 6 Copies de
testeo": por cada CONJUNTO nuevo el copy trae 3 variaciones de TEXTO PRINCIPAL
(problema-solución / emocional / prueba social), 3 TÍTULOS y 1-2 DESCRIPCIÓN,
el CTA apunta a WhatsApp (nunca "compra ya" ni el nombre del producto como
orden), y el copy nunca usa las palabras que banean (cura/elimina/logra/
transforma en X días — DOCTRINA/COPYWRITING_ADS.md). No mide redacción: mide
que la estructura obligatoria esté completa y que la lista de compliance no se
haya violado.
"""
from __future__ import annotations

import re

from _util import resultado

CONJUNTO_RE = re.compile(r"★\s*CONJUNTO\s+\d+")
TEXTO_RE = re.compile(r"(?ms)^TEXTO\s+[123]\b[^\n]*\n(.+?)(?=^TEXTO\s+[123]\b|^T[IÍ]TULOS:|\Z)")
TITULOS_RE = re.compile(r"(?m)^T[IÍ]TULOS:\s*(.+)$")
DESCRIPCION_RE = re.compile(r"(?m)^DESCRIPCI[OÓ]N:\s*(.+)$")
CTA_WHATSAPP_RE = re.compile(r"(?i)escribinos|mandanos un mensaje|preguntanos")
# Palabras que banean (DOCTRINA/COPYWRITING_ADS.md §PRINCIPIO 7, lista literal):
# "cura", "elimina", "logra", "transforma en [X días]". Con límite de palabra
# para no capturar "recuperá"/"descartar". El compliance aplica al COPY que
# corre en Meta (TEXTO/TÍTULOS/DESCRIPCIÓN) — nunca a notas internas de
# producción (ej. el nombre de planificación de un conjunto), que no son
# lo que el anuncio dice.
PALABRAS_QUE_BANEAN_RE = re.compile(
    r"(?i)\bcura\b|\bcuran\b|\belimina[rd]?\b|\blogra(r)?\b|transforma en \d+ d[ií]as"
)


def _bloques_conjunto(output: str) -> list[str]:
    posiciones = [m.start() for m in CONJUNTO_RE.finditer(output)]
    if not posiciones:
        return []
    posiciones.append(len(output))
    return [output[posiciones[i]:posiciones[i + 1]] for i in range(len(posiciones) - 1)]


def get_assert(output: str, context: dict) -> dict:
    bloques = _bloques_conjunto(output)
    if not bloques:
        return resultado(False, "no se encontró ningún bloque '★ CONJUNTO N' (copy por ángulo)")

    for i, bloque in enumerate(bloques, start=1):
        textos = TEXTO_RE.findall(bloque)
        if len(textos) < 3:
            return resultado(False, f"conjunto {i}: menos de 3 variaciones de TEXTO PRINCIPAL ({len(textos)})")

        m_titulos = TITULOS_RE.search(bloque)
        if not m_titulos:
            return resultado(False, f"conjunto {i}: falta la línea TÍTULOS:")
        n_titulos = len([t for t in m_titulos.group(1).split("·") if t.strip()])
        if n_titulos < 3:
            return resultado(False, f"conjunto {i}: menos de 3 títulos declarados ({n_titulos})")

        m_desc = DESCRIPCION_RE.search(bloque)
        if not m_desc or not m_desc.group(1).strip():
            return resultado(False, f"conjunto {i}: falta la línea DESCRIPCIÓN:")

        if not CTA_WHATSAPP_RE.search(bloque):
            return resultado(False, f"conjunto {i}: ningún TEXTO trae un CTA hacia WhatsApp (escribinos/mandanos un mensaje/preguntanos)")

        # Compliance: solo sobre lo que el ad DICE (los 3 TEXTO + TÍTULOS +
        # DESCRIPCIÓN), nunca sobre el nombre del conjunto en el encabezado
        # "★ CONJUNTO N — ...".
        copy_real = "\n".join(textos) + "\n" + m_titulos.group(1) + "\n" + m_desc.group(1)
        m_baneada = PALABRAS_QUE_BANEAN_RE.search(copy_real)
        if m_baneada:
            return resultado(False, f"conjunto {i}: el copy que corre en Meta usa una palabra que banea ({m_baneada.group()!r})")

    return resultado(
        True,
        f"{len(bloques)} conjunto(s) con 3 TEXTO + 3 TÍTULOS + DESCRIPCIÓN + CTA a WhatsApp, sin palabras que banean",
    )
