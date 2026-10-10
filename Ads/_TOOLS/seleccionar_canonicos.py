# -*- coding: utf-8 -*-
"""
seleccionar_canonicos.py — elige que canonicos puede usar un producto, y cuales no.

Por que existe: el `cuando_no_usar` de cada canonico es lo que evita producir
piezas que no se sostienen (una escalera de 3 tiers en un producto con 1 sola
presentacion, un antes/despues en un beneficio invisible). Si la seleccion la
hace el modelo a ojo, esos gates se saltan en silencio. Aca son deterministas.

UNA SOLA CAPA DE GATE: APTITUD — ¿este canonico tiene con que armarse en ESTE
producto? Sale de `cuando_no_usar` de las fichas.

EL BANCO DOCUMENTA, NO AUDITA (`_HANDOFF_FICHAS.md` seccion 2 y regla 4 del
esquema de ficha). Este selector NO lleva capa de compliance, y no es un olvido:
las 111 piezas ya se validaron con dinero real en el mercado GT, la ficha
registra lo que la pieza HACE, y aca se replica tal cual. No se marcan riesgos,
no se proponen sustituciones y no se suaviza ninguna familia — CN01_ANTES_DESPUES
incluida, que es la mas grande del banco y se produce como el banco la documenta.

Lo unico que se traduce al replicar es el registro sanitario de pais, porque es
dato de producto y no decision creativa: FDA se mantiene (origen americano),
INVIMA -> MSPAS. Eso vive en la skill, no en el selector.

Uso:
    python Ads/_TOOLS/seleccionar_canonicos.py --perfil perfil.json -n 6
    python Ads/_TOOLS/seleccionar_canonicos.py --plantilla-perfil > perfil.json
"""
import argparse
import json
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Ads/
CANON = os.path.join(RAIZ, "_SWIPE", "_BLUEPRINTS", "CANONICOS")

# El perfil que el producto tiene que declarar. Todo lo que no se declara se
# asume FALSO: es preferible que un canonico quede fuera por dato faltante a que
# entre por optimismo y produzca una pieza que no se puede sostener.
PLANTILLA_PERFIL = {
    "producto": "",
    "angulo_ganador": "",
    "categoria": "dolor",            # dolor | estetica
    "resultado_visible_en_el_cuerpo": False,
    "resultado_fotografiable_sin_montaje": False,
    "es_tratamiento_con_curva": False,
    "tiers_de_oferta": 1,             # 1 | 2 | 3
    "tiene_multiplicador": False,     # 2x1, 3x2, pack
    "activo_estrella_con_dosis": False,
    "mecanismo_localizable_en_el_cuerpo": False,
    "modo_de_uso_no_obvio": False,
    "momento_de_uso_distintivo": False,
    "alternativa_conocida": "",       # "remedio casero", "generico", "falsificacion", ""
    "prueba_social_clientes": 0,
    "testimonios_reales_disponibles": 0,
    "fanpage_con_reconocimiento_local": False,
    "sintomas_reconocibles": 0,
    "gesto_del_dolor_fotografiable": False,
    "beneficios_distintos": 0,
    "frase_con_giro_disponible": False,
    "atributos_de_producto_diferenciales": 0,
    "avatar_fotografiable": False,
    "nivel_conciencia_objetivo": 3,
}

# gate(perfil) -> None si pasa, o el motivo del rechazo.
APTITUD = {
    # Dos caminos, porque la familia tiene dos materiales. Con resultado visible se
    # hace con FOTOGRAFIA (F004, F023, F068). Sin el, se hace con RENDER ANATOMICO
    # — el organo partido con el frasco de bisagra (F097) o el cuerpo partido por la
    # linea que nace del gotero (F103). Exigir solo el camino fotografico dejaba
    # fuera la familia mas grande del banco en todo producto de beneficio interno.
    "CN01_ANTES_DESPUES": lambda p: (
        None if (p["resultado_visible_en_el_cuerpo"] and p["resultado_fotografiable_sin_montaje"])
        or p["mecanismo_localizable_en_el_cuerpo"]
        else "ni resultado visible ni mecanismo localizable: no hay con que armar los dos estados"),
    "CN02_TIMELINE_PROGRESION": lambda p: (
        None if p["es_tratamiento_con_curva"]
        else "no es un tratamiento con curva de resultado: no hay plazos que etiquetar"),
    "CN03_OFERTA_MULTIPLICADOR": lambda p: (
        None if p["tiene_multiplicador"]
        else "sin 2x1 ni pack el numeral no tiene que decir"),
    "CN04_ESCALERA_PRECIOS": lambda p: (
        None if p["tiers_de_oferta"] >= 3
        else "con menos de 3 tiers la escalera se ve incompleta y pierde el mecanismo"),
    "CN05_LISTA_BENEFICIOS": lambda p: (
        None if p["beneficios_distintos"] >= 3
        else "hacen falta al menos 3 beneficios distintos para que la lista tenga cuerpo"),
    "CN06_CHECKLIST_SINTOMAS": lambda p: (
        None if p["sintomas_reconocibles"] >= 3
        else "hacen falta al menos 3 sintomas que la persona reconozca en si misma"),
    "CN07_DOLOR_A_PLENO": lambda p: (
        None if p["gesto_del_dolor_fotografiable"]
        else "el sintoma no tiene una postura reconocible: no hay foto que tomar"),
    "CN08_UGC_CRUDO": lambda p: None,
    "CN09_UGC_PRODUCTO_EN_MANO": lambda p: None,
    "CN10_PRUEBA_SOCIAL": lambda p: (
        None if p["testimonios_reales_disponibles"] >= 3 or p["prueba_social_clientes"] >= 100
        else "sin testimonios reales ni volumen de clientes la vitrina se lee falsa"),
    "CN11_PANTALLA_SIMULADA": lambda p: None,
    "CN12_AVATAR_DESEO": lambda p: (
        None if p["categoria"] == "estetica" and p["avatar_fotografiable"]
        else "el motor de este producto no es aspiracional, o no hay avatar fotografiable"),
    "CN13_ANATOMIA_MECANISMO": lambda p: (
        None if p["mecanismo_localizable_en_el_cuerpo"]
        else "no hay mecanismo que se pueda localizar y dibujar en el cuerpo"),
    "CN14_COMPARACION_DOS_COLUMNAS": lambda p: (
        None if p["alternativa_conocida"]
        else "no hay una alternativa concreta que el publico ya este usando"),
    "CN15_INGREDIENTES_ACTIVO": lambda p: (
        None if p["activo_estrella_con_dosis"]
        else "sin activo con dosis defendible esta familia expone el problema en vez de venderlo"),
    "CN16_EMISOR_COMERCIAL": lambda p: (
        None if p["fanpage_con_reconocimiento_local"]
        else "fanpage sin reconocimiento: no hay autoridad de emisor de donde tirar"),
    "CN17_TITULAR_DOMINANTE": lambda p: (
        None if p["frase_con_giro_disponible"]
        else "sin una frase con giro real queda un cartel vacio"),
    "CN18_CALLOUTS_PRODUCTO": lambda p: (
        None if p["atributos_de_producto_diferenciales"] >= 3
        else "hacen falta al menos 3 atributos diferenciales del producto mismo"),
    "CN19_INSTRUCTIVO_PASOS": lambda p: (
        None if p["modo_de_uso_no_obvio"]
        else "el modo de uso se adivina: el instructivo gasta espacio en algo que nadie pregunta"),
    "CN20_PRECIO_ANCLA": lambda p: (
        None if p["tiers_de_oferta"] <= 2
        else "hay 3 tiers reales: CN04_ESCALERA_PRECIOS rinde mas"),
    "CN21_AVATAR_CARD_BENEFICIOS": lambda p: (
        None if p["avatar_fotografiable"] and p["beneficios_distintos"] >= 3
        else "hace falta avatar fotografiable y al menos 3 beneficios"),
    "CN22_ESCENA_DE_USO": lambda p: (
        None if p["momento_de_uso_distintivo"]
        else "el momento de uso no es parte del beneficio"),
}

# Rotacion canonica de FASE 2 (`_CATALOGO_CONCEPTOS.md` PARTE III seccion 3).
# El orden ES la prioridad: C2 es el control y va siempre.
PRIORIDAD_CONCEPTO = ["C2_BENEFICIOS", "C1_OFERTA", "C4_TRANSFORMACION",
                      "C8_PROGRESION", "C5_PRUEBA", "C3_SINTOMA",
                      "C7_DESEO", "C9_COMPARACION"]

# El slot de C2 lo ocupa el CONTROL, y el control esta definido: C2 variante
# LIGERA (`_CATALOGO_CONCEPTOS.md` PARTE III seccion 2) — pregunta de dolor +
# 3-5 iconos + producto. Sin anclarlo, el desempate por n_miembros se lo lleva
# CN04_ESCALERA_PRECIOS, que tambien cuenta como C2 (sus piezas venian dentro de
# carteles de beneficios) pero es la variante DENSA: entierra el hook bajo veinte
# elementos, y el hook es lo unico que permite comparar entre productos.
CANONICO_CONTROL = "CN05_LISTA_BENEFICIOS"


def cargar_canonicos():
    docs = {}
    for nombre in sorted(os.listdir(CANON)):
        if nombre.startswith("CN") and nombre.endswith(".json"):
            with open(os.path.join(CANON, nombre), encoding="utf-8") as fh:
                d = json.load(fh)
                docs[d["canonico_id"]] = d
    return docs


def concepto_dominante(doc):
    ck = doc["perfil"]["concepto_key"]
    return max(ck.items(), key=lambda kv: kv[1])[0]


def evaluar(perfil, docs):
    aptos, descartados = [], []
    for cid, doc in docs.items():
        gate = APTITUD.get(cid)
        motivo = gate(perfil) if gate else None
        ck = concepto_dominante(doc)
        item = {
            "canonico_id": cid,
            "nombre": doc["nombre"],
            "concepto_key": ck,
            "ficha_referencia": doc["ficha_referencia"],
            "dispositivo": doc.get("dispositivo", ""),
            "n_miembros": doc["n_miembros"],
            "rol_embudo": doc["perfil"]["rol_embudo"],
            "contrato_variables": doc["contrato_variables"],
        }
        if motivo:
            item["motivo_descarte"] = motivo
            descartados.append(item)
        else:
            aptos.append(item)
    return aptos, descartados


def ordenar(aptos, perfil):
    """Prioriza por la rotacion de conceptos; desempata por evidencia (n_miembros)."""
    def clave(it):
        if it["canonico_id"] == CANONICO_CONTROL:
            return (-1, 0)          # el control va siempre primero
        try:
            pr = PRIORIDAD_CONCEPTO.index(it["concepto_key"])
        except ValueError:
            pr = len(PRIORIDAD_CONCEPTO)
        # el 6to slot de la rotacion es condicional a la categoria del producto
        if it["concepto_key"] == "C3_SINTOMA" and perfil["categoria"] != "dolor":
            pr += 10
        if it["concepto_key"] == "C7_DESEO" and perfil["categoria"] != "estetica":
            pr += 10
        return (pr, -it["n_miembros"])
    return sorted(aptos, key=clave)


def seleccionar(perfil, n, ya=()):
    """Los `n` canonicos de la tanda. `ya` son los canonicos YA registrados para este producto+angulo
    (tandas anteriores): no vuelven a elegirse, y sus `concepto_key` cuentan como usados, asi la regla
    «un concepto_key no se repite mientras queden sin usar» vale a traves de TODAS las tandas."""
    ya = set(ya)
    docs = cargar_canonicos()
    aptos, descartados = evaluar(perfil, docs)
    ordenados = ordenar(aptos, perfil)
    candidatos = [it for it in ordenados if it["canonico_id"] not in ya]

    # Un concepto_key no se repite mientras queden conceptos sin usar: la gracia
    # de FASE 2 es medir CONCEPTOS distintos, no ejecuciones del mismo.
    elegidos = []
    usados = {concepto_dominante(docs[c]) for c in ya if c in docs}
    for it in candidatos:
        if len(elegidos) >= n:
            break
        if it["concepto_key"] in usados:
            continue
        usados.add(it["concepto_key"])
        elegidos.append(it)
    # Agotados los concepto_key sin usar, cada repeticion va al concepto_key MENOS usado (empate: el
    # orden de la rotacion). Rellenar en orden de prioridad apilaba todo en C2_BENEFICIOS.
    repiten = []
    veces = {}
    for c in ya:
        if c in docs:
            ck = concepto_dominante(docs[c])
            veces[ck] = veces.get(ck, 0) + 1
    for it in elegidos:
        veces[it["concepto_key"]] = veces.get(it["concepto_key"], 0) + 1
    restantes = [it for it in candidatos if it not in elegidos]
    while len(elegidos) < n and restantes:
        it = min(restantes, key=lambda r: veces.get(r["concepto_key"], 0))
        restantes.remove(it)
        veces[it["concepto_key"]] = veces.get(it["concepto_key"], 0) + 1
        elegidos.append(it)
        repiten.append(it["canonico_id"])

    return {
        "producto": perfil["producto"],
        "angulo_ganador": perfil["angulo_ganador"],
        "solicitados": n,
        "entregados": len(elegidos),
        "seleccion": elegidos,
        "ya_registrados": sorted(c for c in ya if c in docs),
        "repiten_concepto_key": repiten,
        "aptos_no_elegidos": [i for i in candidatos if i not in elegidos],
        "descartados": sorted(descartados, key=lambda i: i["canonico_id"]),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--perfil", help="JSON con el perfil del producto")
    ap.add_argument("-n", type=int, default=6, help="cuantos conceptos (default 6)")
    ap.add_argument("--plantilla-perfil", action="store_true",
                    help="imprime el perfil vacio para llenar")
    args = ap.parse_args()

    if args.plantilla_perfil:
        print(json.dumps(PLANTILLA_PERFIL, ensure_ascii=False, indent=2))
        return 0
    if not args.perfil:
        ap.error("hace falta --perfil (o --plantilla-perfil)")

    with open(args.perfil, encoding="utf-8") as fh:
        dado = json.load(fh)
    perfil = dict(PLANTILLA_PERFIL)
    desconocidas = sorted(set(dado) - set(PLANTILLA_PERFIL))
    if desconocidas:
        print("aviso: claves ignoradas en el perfil: %s" % ", ".join(desconocidas),
              file=sys.stderr)
    perfil.update({k: v for k, v in dado.items() if k in PLANTILLA_PERFIL})

    res = seleccionar(perfil, args.n)
    print(json.dumps(res, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
