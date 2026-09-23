"""etapa-1 — contrato: costeo derivado de la tabla, nunca inventado (ETAPA-1.md,
invariante 2 de CLAUDE.md). El nombre de la oferta varía por producto (P1u/P2u/P3u
escalera, o 2X1/4X2 combo — CLAUDE.md no fija UNA nomenclatura, fija la regla de
no inventar la cifra), así que el chequeo mecánico es:

1. Hay al menos un marcador de oferta reconocible (P1u/P2u/P3u o 2X1/4X2).
2. CPA objetivo y CPA break-even están declarados por su nombre.
3. Cada uno de esos dos, o trae un número (Q.. / $..), o dice PENDIENTE
   explícitamente — nunca vacío, nunca una palabra distinta a esas dos formas.
"""
from __future__ import annotations

import re

from _util import resultado

OFERTA_RE = re.compile(r"\b(P1u|P2u|P3u|2X1|4X2)\b")
CPA_OBJ_RE = re.compile(r"(?i)cpa[ _]?objetivo")
CPA_BE_RE = re.compile(r"(?i)cpa[ _]?break[ _]?even")
VALOR_OK_RE = re.compile(r"(?i)pendiente|[Q$]\s*\d")


def _valor_declarado_o_pendiente(output: str, marcador: re.Pattern) -> bool:
    m = marcador.search(output)
    if not m:
        return False
    ventana = output[m.end():m.end() + 60]
    return bool(VALOR_OK_RE.search(ventana))


def get_assert(output: str, context: dict) -> dict:
    if not OFERTA_RE.search(output):
        return resultado(False, "sin marcador de oferta reconocible (P1u/P2u/P3u/2X1/4X2)")
    if not CPA_OBJ_RE.search(output):
        return resultado(False, "falta CPA objetivo declarado")
    if not CPA_BE_RE.search(output):
        return resultado(False, "falta CPA break-even declarado")
    if not _valor_declarado_o_pendiente(output, CPA_OBJ_RE):
        return resultado(False, "CPA objetivo sin valor numérico ni PENDIENTE explícito (posible cifra inventada u omitida)")
    if not _valor_declarado_o_pendiente(output, CPA_BE_RE):
        return resultado(False, "CPA break-even sin valor numérico ni PENDIENTE explícito")
    return resultado(True, "oferta y CPA objetivo/break-even declarados (número o PENDIENTE)")
