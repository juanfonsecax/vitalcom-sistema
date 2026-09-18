#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_gen_app.py — GATE de VISTAS/_MANIFIESTO.json.

Hasta el 18-sep-2026 gen_app.py no tenía prueba: la validación de leer_manifiesto() (v6,
vistas) se ejercitaba solo a mano. El handoff del Hito 3 de la app pide "validar con su
test" el bloque `acciones` nuevo (v7), y de paso cubrir la validación que ya existía.

Dos capas:
  1. `problemas_de_manifiesto(m, flujo)` — función pura, sin disco. Cubre la validación de
     vistas (v6, ya existía) y las reglas V1-V19 del bloque `acciones` (v7, nueva).
  2. `leer_manifiesto()` — la que usa el resto de gen_app.py: lee VISTAS/_MANIFIESTO.json y
     DOCTRINA/FLUJO.json de disco y levanta SystemExit si hay problemas. Se prueba con un
     manifiesto real del worktree y con un fixture en un directorio temporal.

USO:  python Ads/_TOOLS/test_gen_app.py     (exit 0 = pasa, 1 = falla)
"""
import copy
import io
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_app  # noqa: E402

fallas = 0

# Rutas de fixture que a propósito NO existen (para probar las ramas de "referencia
# rota" de V5/V7/V14). Partidas en dos literales para que gen_grafo.py — el gate de
# rutas muertas del SISTEMA, que lee el texto crudo de este archivo — no las cuente
# como una referencia real citada desde el código: una fixture inventada no es una
# ruta rota del sistema.
_ADS_TOOLS = "Ads/_TOOLS"
_DOCTRINA = "DOCTRINA"
_PRODUCTOS = "PRODUCTOS"


def check(cond, nombre, detalle=""):
    global fallas
    if cond:
        print("  OK     %s" % nombre)
    else:
        fallas += 1
        print("  FALLA  %s%s" % (nombre, ("\n         " + detalle) if detalle else ""))


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures base: un manifiesto v6 válido y un FLUJO.json de juguete con 2 nodos
# ─────────────────────────────────────────────────────────────────────────────

def manifiesto_v6_valido():
    return {
        "version": 6,
        "app": {"titulo": "x", "subtitulo": "x", "salida": "VISTAS/APP.html",
                 "estado": "VISTAS/_ESTADO.json", "vista_inicial": "flujo"},
        "secciones": [{"id": "decisiones", "titulo": "X"}],
        "vistas": [
            {"id": "flujo", "seccion": "decisiones", "rotulo": "Flujo", "sub": "x",
             "tipo": "iframe", "render": None, "fuente": "VISTAS/FLUJO.html",
             "genera": "python Ads/_TOOLS/flujo.py --todo", "dueno": "flujo.py",
             "caduca": {"ok_dias": 1, "tibia_dias": 3}, "pesada": False},
            {"id": "salud", "seccion": "decisiones", "rotulo": "Salud", "sub": "x",
             "tipo": "nativa", "render": "salud", "fuente": None,
             "genera": "python Ads/_TOOLS/gen_app.py", "dueno": "gen_app.py",
             "caduca": False, "pesada": False},
        ],
    }


FLUJO_JUGUETE = {
    "fases": [
        {"id": "F1", "nodos": [
            {"id": "F1.congelar_inputs", "ejecutor": {"tipo": "operador"},
             "requiere": [{"dato": "fila del producto en _DIM_PRODUCTOS.csv"},
                          {"dato": "COSTO_PROVEEDOR_Q"}]},
            {"id": "F1.paquete", "ejecutor": {"tipo": "skill", "name": "fase-1-angulos"}},
        ]},
    ],
    "ciclo": [
        {"id": "ciclo.motor", "ejecutor": {"tipo": "script",
         "cmd": ["python", "Ads/_TOOLS/gen_decisiones.py"]}},
    ],
}


def accion_base(id_, nodo, ejecutor_tipo, **extra):
    a = {
        "id": id_, "rotulo": "rótulo", "nodo": nodo, "ejecutor_tipo": ejecutor_tipo,
        "name": None, "comando": None, "parametros": {}, "requiere_confirmacion": False,
        "aprobacion": "ninguna", "toca_meta": False, "escribe": [], "idempotente": False,
        "precondicion": "ninguna", "visibilidad": "boton", "habilitada": True,
        "tiempo_max_s": 60,
    }
    a.update(extra)
    return a


def manifiesto_v7_valido():
    m = manifiesto_v6_valido()
    m["version"] = 7
    m["acciones"] = {
        "schema": "acciones/1",
        "reservados": ["run_dir", "tmp", "hoy", "job_id"],
        "tras_escribir": ["sistema.barrido_csv"],
        "lista": [
            accion_base("nodo.F1.congelar_inputs", "F1.congelar_inputs", "operador",
                        datos_del_operador=[
                            {"dato": "fila del producto en _DIM_PRODUCTOS.csv", "accion": None},
                            {"dato": "COSTO_PROVEEDOR_Q", "accion": None},
                        ]),
            accion_base("nodo.F1.paquete", "F1.paquete", "skill", name="fase-1-angulos",
                        requiere_confirmacion=True, escribe=["PRODUCTOS/"],
                        presupuesto_usd=30, tiempo_max_s=5400),
            accion_base("nodo.ciclo.motor", "ciclo.motor", "script",
                        comando=["python", "Ads/_TOOLS/gen_decisiones.py"], salida="texto",
                        escribe=["PRODUCTOS/_DECISIONES.json"], idempotente=True),
            accion_base("sistema.barrido_csv", None, "script",
                        comando=["python", "Ads/_TOOLS/hook_csv.py", "--barrido"],
                        salida="texto", escribe=[_PRODUCTOS + "/.hook_csv_mtimes.json"],
                        idempotente=True, visibilidad="interna"),
        ],
    }
    return m


# ─────────────────────────────────────────────────────────────────────────────
# 1 · la validación de VISTAS que ya existía (v6) — cero cambios de comportamiento
# ─────────────────────────────────────────────────────────────────────────────

def test_vistas_v6():
    ok = gen_app.problemas_de_manifiesto(manifiesto_v6_valido(), None)
    check(ok == [], "un manifiesto v6 válido no tiene problemas", str(ok))

    m = manifiesto_v6_valido()
    del m["secciones"]
    check(any("secciones" in p for p in gen_app.problemas_de_manifiesto(m, None)),
          "falta la llave raíz 'secciones' → problema")

    m = manifiesto_v6_valido()
    del m["app"]["salida"]
    check(any("app.salida" in p for p in gen_app.problemas_de_manifiesto(m, None)),
          "falta app.salida → problema")

    m = manifiesto_v6_valido()
    m["vistas"].append(copy.deepcopy(m["vistas"][0]))
    check(any("dos veces" in p for p in gen_app.problemas_de_manifiesto(m, None)),
          "una vista con id repetido → problema")

    m = manifiesto_v6_valido()
    m["vistas"][0]["seccion"] = "no-existe"
    check(any("no existe" in p for p in gen_app.problemas_de_manifiesto(m, None)),
          "una vista que apunta a una sección inexistente → problema")

    m = manifiesto_v6_valido()
    m["vistas"][0]["tipo"] = "rara"
    check(any("solo vale nativa o iframe" in p for p in gen_app.problemas_de_manifiesto(m, None)),
          "un tipo de vista fuera de nativa/iframe → problema")

    m = manifiesto_v6_valido()
    m["vistas"][0]["fuente"] = None
    check(any("no declara fuente" in p for p in gen_app.problemas_de_manifiesto(m, None)),
          "una vista iframe sin fuente → problema")

    m = manifiesto_v6_valido()
    m["vistas"][1]["render"] = None
    check(any("no declara que funcion" in p for p in gen_app.problemas_de_manifiesto(m, None)),
          "una vista nativa sin render → problema")

    m = manifiesto_v6_valido()
    m["vistas"][0]["campo_falso"] = 1
    check(any("no conoce" in p for p in gen_app.problemas_de_manifiesto(m, None)),
          "una vista con un campo que el contrato no conoce → problema")

    m = manifiesto_v6_valido()
    m["app"]["vista_inicial"] = "no-existe"
    check(any("vista_inicial" in p for p in gen_app.problemas_de_manifiesto(m, None)),
          "una vista_inicial no declarada → problema")

    m = manifiesto_v6_valido()
    check(gen_app.problemas_de_manifiesto(m, FLUJO_JUGUETE) == [],
          "un manifiesto v6 ignora FLUJO.json por completo (nada de acciones aplica bajo v7)")


# ─────────────────────────────────────────────────────────────────────────────
# 2 · leer_manifiesto() contra archivos reales (v6 del worktree + fixture temporal)
# ─────────────────────────────────────────────────────────────────────────────

def test_leer_manifiesto_real():
    m = gen_app.leer_manifiesto()
    check(m.get("version", 0) >= 6, "el manifiesto real del worktree se lee sin levantar SystemExit")


def test_leer_manifiesto_fixture_invalido():
    tmp = tempfile.mkdtemp(prefix="gen_app_")
    os.makedirs(os.path.join(tmp, "VISTAS"))
    os.makedirs(os.path.join(tmp, "DOCTRINA"))
    m = manifiesto_v6_valido()
    del m["secciones"]
    with io.open(os.path.join(tmp, "VISTAS", "_MANIFIESTO.json"), "w", encoding="utf-8") as fh:
        json.dump(m, fh)
    viejo_man, viejo_flujo = gen_app.MANIFIESTO, gen_app.FLUJO_JSON
    gen_app.MANIFIESTO = os.path.join(tmp, "VISTAS", "_MANIFIESTO.json")
    gen_app.FLUJO_JSON = os.path.join(tmp, "DOCTRINA", "FLUJO.json")
    try:
        levanto = False
        try:
            gen_app.leer_manifiesto()
        except SystemExit as e:
            levanto = True
            check("secciones" in str(e), "el mensaje de SystemExit nombra el problema real", str(e))
        check(levanto, "un manifiesto inválido en disco levanta SystemExit")
    finally:
        gen_app.MANIFIESTO, gen_app.FLUJO_JSON = viejo_man, viejo_flujo


# ─────────────────────────────────────────────────────────────────────────────
# 3 · el bloque `acciones` v7 — V1 a V19
# ─────────────────────────────────────────────────────────────────────────────

def _lista(m):
    return m["acciones"]["lista"]


def _problemas_que_empiezan(m, prefijo, flujo=FLUJO_JUGUETE):
    return [p for p in gen_app.problemas_de_manifiesto(m, flujo) if p.startswith(prefijo)]


def test_acciones_v7():
    m = manifiesto_v7_valido()
    check(gen_app.problemas_de_manifiesto(m, FLUJO_JUGUETE) == [],
          "un manifiesto v7 válido, con las 3 acciones de nodo + 1 interna, no tiene problemas",
          str(gen_app.problemas_de_manifiesto(m, FLUJO_JUGUETE)))

    # V1
    m = manifiesto_v7_valido()
    del m["acciones"]
    check(_problemas_que_empiezan(m, "V1:"), "version 7 sin bloque 'acciones' → V1")
    m = manifiesto_v7_valido()
    m["acciones"]["schema"] = "otra/1"
    check(_problemas_que_empiezan(m, "V1:"), "schema distinto de 'acciones/1' → V1")

    # V2
    m = manifiesto_v7_valido()
    _lista(m).append(copy.deepcopy(_lista(m)[0]))
    check(_problemas_que_empiezan(m, "V2:"), "un id de acción repetido → V2")
    m = manifiesto_v7_valido()
    _lista(m)[0]["id"] = "IdMalo sin patron"
    check(_problemas_que_empiezan(m, "V2:"), "un id que no cumple el patrón → V2")

    # V3
    m = manifiesto_v7_valido()
    del _lista(m)[0]["rotulo"]
    check(_problemas_que_empiezan(m, "V3:"), "falta un campo obligatorio ('rotulo') → V3")
    m = manifiesto_v7_valido()
    _lista(m)[0]["campo_inventado"] = 1
    check(_problemas_que_empiezan(m, "V3:"), "un campo que el contrato no conoce → V3")

    # V4
    m = manifiesto_v7_valido()
    _lista(m)[1]["ejecutor_tipo"] = "cualquiera"
    check(_problemas_que_empiezan(m, "V4:"), "un ejecutor_tipo fuera del vocabulario → V4")

    # V5
    m = manifiesto_v7_valido()
    for a in _lista(m):
        if a["id"] == "nodo.F1.paquete":
            a["ejecutor_tipo"] = "subagente"
    check(_problemas_que_empiezan(m, "V5:"),
          "el ejecutor_tipo de la acción no coincide con el de FLUJO.json → V5")
    m = manifiesto_v7_valido()
    for a in _lista(m):
        if a["id"] == "nodo.F1.paquete":
            a["name"] = "otra-skill"
    check(_problemas_que_empiezan(m, "V5:"),
          "el name de la acción no coincide con el de FLUJO.json → V5")
    m = manifiesto_v7_valido()
    for a in _lista(m):
        if a["id"] == "nodo.ciclo.motor":
            a["comando"] = ["python", _ADS_TOOLS + "/otro_script.py"]
    check(_problemas_que_empiezan(m, "V5:"),
          "el comando de un script no coincide con el cmd de FLUJO.json → V5")

    # V6
    m = manifiesto_v7_valido()
    _lista(m).pop(0)  # saca nodo.F1.congelar_inputs
    check(_problemas_que_empiezan(m, "V6:"), "un nodo del flujo sin ninguna acción → V6")
    m = manifiesto_v7_valido()
    dup = copy.deepcopy(_lista(m)[1])
    dup["id"] = "nodo.F1.paquete.2"
    _lista(m).append(dup)
    check(_problemas_que_empiezan(m, "V6:"), "un nodo del flujo con dos acciones → V6")

    # V7
    m = manifiesto_v7_valido()
    for a in _lista(m):
        if a["id"] == "nodo.ciclo.motor":
            a["comando"] = ["python", _ADS_TOOLS + "/no_existe_de_verdad.py"]
    check(_problemas_que_empiezan(m, "V5:") or _problemas_que_empiezan(m, "V7:"),
          "un script que no arranca con python o no existe → V5/V7 (el cmd ya no coincide con FLUJO.json)")
    m = manifiesto_v7_valido()
    for a in _lista(m):
        if a["id"] == "sistema.barrido_csv":
            a["comando"] = ["python", "Ads/_TOOLS/hook_csv.py", "--barrido", "--dangerously-skip-permissions"]
    check(_problemas_que_empiezan(m, "V7:"), "un token prohibido en el comando → V7")

    # V8
    m = manifiesto_v7_valido()
    for a in _lista(m):
        if a["id"] == "nodo.F1.congelar_inputs":
            a["comando"] = ["python", _ADS_TOOLS + "/algo.py"]
    check(_problemas_que_empiezan(m, "V8:"), "un tipo no-script con 'comando' → V8")
    m = manifiesto_v7_valido()
    for a in _lista(m):
        if a["id"] == "nodo.F1.paquete":
            del a["name"]
    check(_problemas_que_empiezan(m, "V3:") or _problemas_que_empiezan(m, "V8:"),
          "una skill sin 'name' → V8 (o V3 si 'name' se trata como obligatorio)")

    # V9
    m = manifiesto_v7_valido()
    for a in _lista(m):
        if a["id"] == "nodo.ciclo.motor":
            a["comando"] = ["python", "Ads/_TOOLS/gen_decisiones.py", "--tag", "{sin_declarar}"]
    check(_problemas_que_empiezan(m, "V9:"), "un {placeholder} sin parámetro declarado → V9")

    # V10
    m = manifiesto_v7_valido()
    for a in _lista(m):
        if a["id"] == "nodo.F1.congelar_inputs":
            a["parametros"] = {"x": {"tipo": "no-existe", "requerido": True}}
    check(_problemas_que_empiezan(m, "V10:"), "un tipo de parámetro fuera del vocabulario → V10")
    m = manifiesto_v7_valido()
    for a in _lista(m):
        if a["id"] == "nodo.F1.congelar_inputs":
            a["parametros"] = {"x": {"tipo": "enum", "requerido": True}}
    check(_problemas_que_empiezan(m, "V10:"), "un enum sin 'valores' → V10")
    m = manifiesto_v7_valido()
    for a in _lista(m):
        if a["id"] == "nodo.F1.congelar_inputs":
            a["parametros"] = {"x": {"tipo": "texto", "requerido": True, "patron": "(("}}
    check(_problemas_que_empiezan(m, "V10:"), "un patrón que no compila → V10")

    # V11
    m = manifiesto_v7_valido()
    for a in _lista(m):
        if a["id"] == "nodo.F1.paquete":
            a["toca_meta"] = True
    check(_problemas_que_empiezan(m, "V11:"),
          "toca_meta sin requiere_confirmacion + aprobacion por_orden → V11")

    # V12
    m = manifiesto_v7_valido()
    for a in _lista(m):
        if a["id"] == "nodo.F1.paquete":
            a["herramientas_meta"] = {"lectura": [], "escritura": ["ads_create_campaign"]}
    check(_problemas_que_empiezan(m, "V12:"), "herramientas_meta con toca_meta false → V12")
    m = manifiesto_v7_valido()
    for a in _lista(m):
        if a["id"] == "nodo.F1.paquete":
            a["herramientas"] = ["mcp__claude_ai_META_MCP__ads_create_campaign"]
    check(_problemas_que_empiezan(m, "V12:"), "una herramienta mcp__ colada en 'herramientas' → V12")

    # V13
    m = manifiesto_v7_valido()
    for a in _lista(m):
        if a["id"] == "nodo.F1.paquete":
            a["toca_meta"] = True
            a["requiere_confirmacion"] = True
            a["aprobacion"] = "por_orden"
            a["herramientas_meta"] = {"lectura": [], "escritura": ["ads_create_campaign"]}
    check(_problemas_que_empiezan(m, "V13:"), "toca_meta habilitada sin 'ordenes' → V13")

    # V14
    m = manifiesto_v7_valido()
    for a in _lista(m):
        if a["id"] == "nodo.F1.paquete":
            a["escribe"] = [_DOCTRINA + "/algo.md"]
    check(_problemas_que_empiezan(m, "V14:"), "una ruta de escribe bajo DOCTRINA/ → V14")
    m = manifiesto_v7_valido()
    for a in _lista(m):
        if a["id"] == "nodo.F1.paquete":
            a["escribe"] = ["/absoluta"]
    check(_problemas_que_empiezan(m, "V14:"), "una ruta de escribe absoluta → V14")

    # V15
    m = manifiesto_v7_valido()
    for a in _lista(m):
        if a["id"] == "nodo.F1.paquete":
            a["escribe"] = []
    check(_problemas_que_empiezan(m, "V15:"), "una skill con 'escribe' vacío → V15")

    # V16
    m = manifiesto_v7_valido()
    for a in _lista(m):
        if a["id"] == "sistema.barrido_csv":
            a["nodo"] = "ciclo.motor"
    check(_problemas_que_empiezan(m, "V16:"), "una acción interna con 'nodo' asignado → V16")

    # V17
    m = manifiesto_v7_valido()
    for a in _lista(m):
        if a["id"] == "nodo.F1.congelar_inputs":
            a["datos_del_operador"] = [{"dato": "un dato que no existe", "accion": None}]
    check(_problemas_que_empiezan(m, "V17:"), "un dato_del_operador que no está en requiere/produce → V17")

    # V17 también rige en un nodo que NO es del operador (F1.publicar se bloquea por la cuenta)
    flujo = copy.deepcopy(FLUJO_JUGUETE)
    flujo["fases"][0]["nodos"][1]["requiere"] = [{"dato": "cuenta publicitaria asignada"}]
    m = manifiesto_v7_valido()
    for a in _lista(m):
        if a["id"] == "nodo.F1.paquete":
            a["datos_del_operador"] = [{"dato": "cuenta publicitaria asignada", "accion": "nodo.ciclo.motor"}]
    check(_problemas_que_empiezan(m, "V17:", flujo) == [],
          "una skill con un dato_del_operador de su requiere y una acción script es válida",
          str(_problemas_que_empiezan(m, "V17:", flujo)))
    for a in _lista(m):
        if a["id"] == "nodo.F1.paquete":
            a["datos_del_operador"] = [{"dato": "un dato que no existe", "accion": None}]
    check(_problemas_que_empiezan(m, "V17:", flujo), "una skill con un dato que no es de su nodo → V17")
    for a in _lista(m):
        if a["id"] == "nodo.F1.paquete":
            a["datos_del_operador"] = [{"dato": "cuenta publicitaria asignada", "accion": "nodo.F1.paquete"}]
    check(_problemas_que_empiezan(m, "V17:", flujo),
          "una skill cuyo dato apunta a una acción que no es script → V17")

    # V18
    m = manifiesto_v7_valido()
    for a in _lista(m):
        if a["id"] == "nodo.F1.paquete":
            a["habilitada"] = False
    check(_problemas_que_empiezan(m, "V18:"), "habilitada=false sin 'motivo' → V18")
    m = manifiesto_v7_valido()
    for a in _lista(m):
        if a["id"] == "nodo.F1.paquete":
            a["habilitada"] = False
            a["motivo"] = "spike pendiente"
    check(not _problemas_que_empiezan(m, "V18:"), "habilitada=false CON 'motivo' no dispara V18")

    # V19
    m = manifiesto_v7_valido()
    m["acciones"]["tras_escribir"] = ["nodo.F1.paquete"]  # no es interna ni idempotente
    check(_problemas_que_empiezan(m, "V19:"), "tras_escribir con una acción que no es interna+idempotente → V19")


def main():
    test_vistas_v6()
    test_leer_manifiesto_real()
    test_leer_manifiesto_fixture_invalido()
    test_acciones_v7()
    total = 41
    print("\n%d de %d comprobaciones pasan." % (total - fallas, total))
    return 1 if fallas else 0


if __name__ == "__main__":
    sys.exit(main())
