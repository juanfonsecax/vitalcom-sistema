# -*- coding: utf-8 -*-
"""requiere_claude.py — forma unica de "esto necesita Claude" (decision del operador, 18-oct-2026).

Toda escritura en Meta (renombrar, activar, pausar, escalar) se hace por el MCP de Meta dentro de
una sesion de Claude: la app web solo LEE y VERIFICA. Cuando una verificacion descubre algo que
exige una escritura, devuelve un item con esta forma y la app lo muestra con una frase lista para
pegarle a Claude. Si no hace falta Claude, la lista va VACIA y la app no muestra nada.

    {"codigo": "RENOMBRAR_COPIA" | "CONJUNTO_CIEGO" | ...,
     "severidad": "alta" | "media",
     "motivo": "<frase corta para el operador>",
     "pedirle_a_claude": "<frase exacta para pegar>",
     "objetos": [{"id": "...", "nombre": "..."}]}

Los productores (verificar_campana_publicada.py, control_d1.py) usan item(); la app y los tests
usan validar().
"""

SEVERIDADES = ("alta", "media")


def item(codigo, severidad, motivo, pedirle_a_claude, objetos=()):
    """Construye un item valido o lanza ValueError (un productor con un item roto es un bug)."""
    it = {"codigo": codigo, "severidad": severidad, "motivo": motivo,
          "pedirle_a_claude": pedirle_a_claude,
          "objetos": [{"id": str(o.get("id") or ""), "nombre": str(o.get("nombre") or "")}
                      for o in objetos]}
    errores = validar_item(it)
    if errores:
        raise ValueError("requiere_claude invalido: " + "; ".join(errores))
    return it


def validar_item(it):
    """Lista de errores de un item (vacia = valido)."""
    if not isinstance(it, dict):
        return ["el item no es un objeto"]
    errores = []
    for campo in ("codigo", "severidad", "motivo", "pedirle_a_claude"):
        v = it.get(campo)
        if not isinstance(v, str) or not v.strip():
            errores.append("falta %s" % campo)
    cod = it.get("codigo")
    if isinstance(cod, str) and cod and not (cod.isupper() and cod.replace("_", "").isalnum()):
        errores.append("codigo debe ser MAYUSCULAS_CON_GUION_BAJO")
    if it.get("severidad") not in SEVERIDADES:
        errores.append("severidad debe ser una de %s" % "/".join(SEVERIDADES))
    objs = it.get("objetos")
    if not isinstance(objs, list):
        errores.append("objetos debe ser una lista")
    else:
        for o in objs:
            if not (isinstance(o, dict) and "id" in o and "nombre" in o):
                errores.append("cada objeto lleva id y nombre")
                break
    return errores


def validar(items):
    """Lista de errores de toda la lista (vacia = valida; una lista vacia es valida)."""
    if not isinstance(items, list):
        return ["requiere_claude debe ser una lista"]
    errores = []
    for i, it in enumerate(items):
        errores.extend("[%d] %s" % (i, e) for e in validar_item(it))
    return errores
