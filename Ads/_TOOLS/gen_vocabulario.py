# -*- coding: utf-8 -*-
"""Genera PRODUCTOS/_DIM_VOCABULARIO.csv: el diccionario cerrado de los ejes."""
import csv, os, re

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SAL = os.path.join(BASE, "PRODUCTOS", "_DIM_VOCABULARIO.csv")
IDX = os.path.join(BASE, "Ads", "_SWIPE", "_BLUEPRINTS", "CANONICOS", "_INDICE.md")

filas = []


def add(eje, valor, etiqueta, tipo, mapea_a="", definicion="", dueno=""):
    filas.append({"eje": eje, "valor": valor, "etiqueta": etiqueta, "tipo_eje": tipo,
                  "mapea_a": mapea_a, "definicion": definicion, "dueno_del_vocabulario": dueno,
                  "estado": "VIGENTE"})


CAT = "Ads/_SWIPE/_CATALOGO_CONCEPTOS.md"

# --- EJE 1: ANGULO (por que duele). Vocabulario ABIERTO: nace por producto en etapa-2.
add("angulo_key", "(abierto)", "se crea por producto", "TESTEABLE", "",
    "La causa o sub-problema que el producto resuelve. Territorio del PROBLEMA, no del formato.",
    ".claude/agents/ETAPA-2.md")

# --- EJE 2: CONCEPTO (como se muestra). Vocabulario CERRADO: 8 tras fusionar C6 en C5.
CONCEPTOS = [
    ("C1_OFERTA", "Oferta", "El precio o el multiplicador de cantidad ES la pieza."),
    ("C2_BENEFICIOS", "Beneficios", "Lo que el producto hace, enumerado o dibujado."),
    ("C3_SINTOMA", "Sintoma", "El dolor o el sintoma ocupa la pieza; no hay promesa aun."),
    ("C4_TRANSFORMACION", "Transformacion", "Dos estados del mismo sujeto: antes y despues."),
    ("C5_PRUEBA", "Prueba", "Evidencia de terceros: UGC, testimonio, unboxing, captura. Absorbe C6."),
    ("C7_DESEO", "Deseo", "La vida o el cuerpo que se quiere, no el problema que se tiene."),
    ("C8_PROGRESION", "Progresion", "Tres o mas estados en fila, cada uno con su plazo."),
    ("C9_COMPARACION", "Comparacion", "Dos columnas enfrentadas: con y sin."),
]
for v, e, d in CONCEPTOS:
    add("concepto_key", v, e, "TESTEABLE", "", d, CAT)
add("concepto_key", "C6_UNBOXING", "Unboxing (RETIRADO)", "TESTEABLE", "C5_PRUEBA",
    "Fusionado en C5_PRUEBA en la v2 del catalogo. No usar en filas nuevas.", CAT)
add("concepto_key", "SIN_CLASIFICAR", "sin clasificar", "TESTEABLE", "",
    "Valor de siembra. Una fila con gasto y este valor es deuda de parametrizacion.", CAT)

# --- canonico_id: la ejecucion visual concreta dentro del concepto. Se lee del indice.
txt = open(IDX, encoding="utf-8").read()
for m in re.finditer(r"\|\s*`(CN\d\d_[A-Z_]+)`\s*([^|]+)\|[^|]*\|[^|]*\|\s*(C\d)[:\d\s C]*\|", txt):
    cn, etiqueta, c = m.group(1), m.group(2).strip(), m.group(3)
    concepto = next((v for v, _, _ in CONCEPTOS if v.startswith(c + "_")), "")
    add("canonico_id", cn, etiqueta, "TESTEABLE", concepto,
        "Estructura visual canonica. Su concepto dominante es %s." % (concepto or c),
        "Ads/_SWIPE/_BLUEPRINTS/CANONICOS/_INDICE.md")

# --- EJE 3: NIVEL DE CONCIENCIA. Cerrado, 4 valores.
NIV = [
    ("1", "No sabe la causa", "Sabe que le pasa algo pero no por que. El ad EDUCA."),
    ("2", "Sabe el problema, no la solucion", "Nombra su problema y busca. El ad OFRECE la solucion."),
    ("3A", "Conoce el producto, teme comprar", "Duda del vendedor o del envio. El ad REDUCE FRICCION."),
    ("3B", "Conoce el producto, compara ofertas", "Compara precio. El ad ANCLA la oferta."),
]
for v, e, d in NIV:
    add("nivel_conciencia", v, e, "TESTEABLE", "", d, ".claude/agents/ETAPA-2.md")
for malo, bueno in [("3a", "3A"), ("3b", "3B"), ("NC2", "2"), ("NC1", "1"), ("1-2", "2"), ("", "2")]:
    add("nivel_conciencia", malo or "(vacio)", "alias sucio", "TESTEABLE", bueno,
        "Valor legado a normalizar a %s." % bueno, ".claude/agents/ETAPA-2.md")
add("nivel_conciencia", "3", "alias sucio AMBIGUO", "TESTEABLE", "REVISAR",
    "3 a secas no distingue 3A (teme comprar -> reducir friccion) de 3B (compara -> anclar "
    "oferta). Llevan a ads opuestos. Requiere criterio, no reemplazo automatico.",
    ".claude/agents/ETAPA-2.md")

# --- EJE 4: OFERTA. Cerrado.
for v, e, d in [
    ("1U", "unidad suelta", "Una unidad al precio base."),
    ("2X1", "dos por uno", "El multiplicador clasico de bajo ticket."),
    ("4X2", "cuatro por dos", "Escalon de volumen."),
    ("ESCALERA", "escalera de 3 tiers", "P1u / P2u / P3u en cards paralelas."),
    ("COMBO", "combo con otro producto", "Bundle cruzado."),
    ("SIN_PRECIO", "sin precio en el ad", "La oferta no aparece; se revela en el bot."),
]:
    add("oferta_key", v, e, "TESTEABLE", "", d, ".claude/agents/ETAPA-1.md")

# --- EJE 5: DESTINO. Vocabulario abierto por version de flujo.
add("destino_key", "(abierto)", "version del flujo LucidBot", "TESTEABLE", "",
    "Version del flujo a la que apunta el ad. Cambia solo con un CAMBIO_BOT en _EVENTOS.csv.",
    ".claude/agents/ETAPA-11.md")

# --- COVARIABLES: se registran y se congelan, no se testean.
for v, e in [("VIDEO", "video"), ("IMAGEN", "imagen estatica")]:
    add("formato", v, e, "COVARIABLE", "", "Se congela dentro de un testeo.", "DOCTRINA/PLANTILLAS_ADS.md")
for v, e in [("TOFU", "tope de embudo"), ("MOFU", "medio"), ("BOFU", "fondo")]:
    add("rol_embudo", v, e, "COVARIABLE", "",
        "Derivado del nivel de conciencia: 1->TOFU, 2->TOFU/MOFU, 3A/3B->BOFU.",
        "DOCTRINA/ESCALADO_PLAYBOOK.md")
for v in ["MIEDO", "EMOCIONAL", "OFERTA", "MECANISMO", "TESTIMONIO", "EDUCACIONAL",
          "ANTI_FALSIFICACION", "DOLOR"]:
    add("tipo_hook", v, v.lower().replace("_", " "), "COVARIABLE", "",
        "Como abre el copy. MECANISMO tiene APR-001 en contra como hook de entrada.",
        "DOCTRINA/COPYWRITING_ADS.md")
for v in ["SI", "NO"]:
    add("lleva_precio", v, v, "COVARIABLE", "", "Si el creativo muestra precio.",
        "DOCTRINA/COPYWRITING_ADS.md")

with open(SAL, "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=["eje", "valor", "etiqueta", "tipo_eje", "mapea_a",
                                       "definicion", "dueno_del_vocabulario", "estado"])
    w.writeheader()
    w.writerows(filas)

print("escrito %s con %d filas" % (SAL, len(filas)))
import collections
print(dict(collections.Counter(f["eje"] for f in filas)))
