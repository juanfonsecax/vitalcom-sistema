"""etapa-guardar-producto — invariante 8 de CLAUDE.md: "Un producto = una
carpeta PRODUCTOS/[NOMBRE]/ con archivos por rol ... Prohibidos archivos
sueltos de reruns." El fixture es un manifiesto JSON congelado
({"producto_key": ..., "archivos": [...]})  con el listado real de archivos
de nivel superior en PRODUCTOS/<producto>/. El chequeo es puramente
estructural: cada nombre pertenece al vocabulario cerrado de archivos por rol
que ETAPA-GUARDAR-PRODUCTO.md documenta (fijos, o generados por otra etapa
pero igualmente declarados), y los dos archivos obligatorios de todo producto
(1_HACER_MANUAL.txt, 2_DATA_PRODUCTO.txt) están presentes."""
from __future__ import annotations

import json
import re

from _util import resultado

OBLIGATORIOS = {"1_HACER_MANUAL.txt", "2_DATA_PRODUCTO.txt"}

# Vocabulario cerrado de nombres de archivo de nivel superior permitidos en
# PRODUCTOS/<producto>/. Cualquier otro nombre es un "archivo suelto de
# rerun" (invariante 8) hasta que una nueva etapa lo declare acá.
PERMITIDOS_EXACTOS = {
    "1_HACER_MANUAL.txt",
    "2_DATA_PRODUCTO.txt",
    "3_CAMPAÑA_META.txt",
    "4_PLAN_ESCALADO.txt",
    "5_FASE2_CONCEPTOS.txt",
    "0_INPUTS_CONGELADOS.md",
    "FLUJO_LUCIDBOT.md",
    "BLOQUES_BOT.md",
    "INFOGRAFIAS.md",
    "_PLAN.json",
    "_PLAN_FASE2.json",
    "_PLAN_FASE4.json",
    "_PERFIL_CREATIVO.json",
}
PERMITIDOS_PATRON = re.compile(r"^_PUBLICACION_F[0-9A-Z]+\.json$")


def _nombre_permitido(nombre: str) -> bool:
    return nombre in PERMITIDOS_EXACTOS or bool(PERMITIDOS_PATRON.match(nombre))


def get_assert(output: str, context: dict) -> dict:
    try:
        manifiesto = json.loads(output)
    except json.JSONDecodeError as exc:
        return resultado(False, f"manifiesto no es JSON válido: {exc}")

    archivos = manifiesto.get("archivos")
    if not isinstance(archivos, list) or not archivos:
        return resultado(False, "manifiesto sin lista de archivos")

    faltan_obligatorios = OBLIGATORIOS - set(archivos)
    if faltan_obligatorios:
        return resultado(False, f"faltan archivos por rol obligatorios: {sorted(faltan_obligatorios)}")

    sueltos = [a for a in archivos if not _nombre_permitido(a)]
    if sueltos:
        return resultado(False, f"archivo(s) fuera del vocabulario de roles (posible rerun suelto): {sueltos}")

    return resultado(True, f"{len(archivos)} archivo(s), todos dentro del vocabulario de roles, obligatorios presentes")
