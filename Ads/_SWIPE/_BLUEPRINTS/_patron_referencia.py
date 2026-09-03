# -*- coding: utf-8 -*-
"""Alinea los LLENO_T01_*.json con el PATRON REAL de cada imagen de referencia.

Decision del operador (19-ago, ronda 3): cada brazo respeta la arquitectura de precio de SU
referencia. D lleva 3 niveles con MEJOR OFERTA / MAYOR AHORRO, C lleva 2 con AHORRAS, A y B
llevan uno. "Solo cambia eso" respecto de la referencia.

CONSECUENCIA A REGISTRAR: el bloque de precio ya NO es identico entre brazos, asi que T01 deja
de aislar el dispositivo visual puro — cada brazo mezcla dispositivo + arquitectura de oferta.
Se anota en cada JSON para que la lectura del resultado lo tenga en cuenta.

Errores mios corregidos aca, detectados leyendo las 4 referencias:
  1. El banner de ORIGEN AMERICANO existe SOLO en A. Se lo habia puesto a los 4.
  2. En B el tercer item de la barra es "PRODUCTO DISPONIBLE EN GUATEMALA" con bandera de
     Guatemala — es disponibilidad, no origen.
  3. A no tiene precio tachado en la referencia. El tachado existe solo en B.
  4. El badge premium de C dice "FORMULA PREMIUM / MAXIMA ABSORCION", no origen.
"""
import json, io, os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

DORADO = "#D4A017"
P1, P2, P3 = "Q178", "Q239", "Q299"
AHORRO_2 = "Q117"        # 178*2 - 239
TACHADO = "Q298"

NOTA_TEST = ("El bloque de precio sigue la arquitectura NATIVA de cada referencia (decision del "
             "operador 19-ago). Cada brazo mezcla dispositivo visual + arquitectura de oferta, "
             "asi que el ganador no es atribuible al dispositivo puro. Registrarlo al leer T01.")

REGLA_UNIDAD = ("La palabra TRATAMIENTO reemplaza al sustantivo de unidad SOLO donde el layout ya "
                "nombra uno (frasco, unidad, botella). Donde el layout no nombra unidad, va solo "
                "el numero. Nunca se dice 'frasco'.")

REGLA_ORIGEN = ("El banner de ORIGEN AMERICANO con bandera de ESTADOS UNIDOS va SOLO donde la "
                "referencia tiene un sello de origen. La bandera de GUATEMALA acompana la "
                "disponibilidad local y el registro MSPAS. No se mezclan.")


def cargar(L):
    return json.load(io.open("LLENO_T01_%s.json" % L, encoding="utf-8"))


def guardar(L, d):
    d["_reglas_globales"] = {
        "unidad": REGLA_UNIDAD,
        "origen": REGLA_ORIGEN,
        "garantia": "Donde aparezca la garantia va en DORADO %s, resaltada." % DORADO,
        "regulatorio": "REGISTRO MSPAS con bandera de Guatemala.",
        "precio": "Arquitectura de precio segun la referencia de este brazo.",
    }
    d["_nota_lectura_test"] = NOTA_TEST
    json.dump(d, io.open("LLENO_T01_%s.json" % L, "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)


# ═════════ A — 1 precio sin unidad, sin tachado, CON sello de origen ═════════
d = cargar("A")
z = d["zonas"]
o = z["bloque_oferta"]
o["linea_1"] = "OFERTA 1"
o["linea_2"] = "1 x %s" % P1
o.pop("linea_3", None)                       # la referencia no tiene precio tachado
o["nota_unidad"] = "Este layout no nombra la unidad: va solo el numero, como en la referencia."
z["garantias"]["items"] = "['ENVÍO GRATIS', 'PAGÁS AL RECIBIR', 'COMPRA SEGURA']"
z["sello_origen"]["contenido"] = "ORIGEN AMERICANO"
z["sello_origen"]["bandera"] = "bandera de ESTADOS UNIDOS dentro del sello, como en la referencia"
z["sello_autoridad"]["contenido"] = "REGISTRO MSPAS"
z["sello_autoridad"]["bandera"] = "bandera de GUATEMALA dentro del sello"
guardar("A", d)

# ═════════ B — 1 precio CON tachado, tercer item = disponibilidad Guatemala ═════════
d = cargar("B")
z = d["zonas"]
o = z["bloque_oferta"]
o["zona_izquierda"] = "%s.00" % P1
o["zona_derecha"] = "card blanca con '1' + 'TRATAMIENTO' + pildora '60 ML'"
o["linea_inferior"] = "PRECIO NORMAL: %s con tachado" % TACHADO
z["badge_garantia"]["color"] = "DORADO %s solido con estrellas arriba" % DORADO
z["barra_garantias"]["items"] = ("['ENVÍO GRATIS a toda Guatemala', "
                                 "'PAGO CONTRA ENTREGA · pagás cuando lo recibís', "
                                 "'PRODUCTO DISPONIBLE en Guatemala']")
z["barra_garantias"]["regla_item_3"] = ("el tercero lleva bandera de GUATEMALA: es "
                                        "DISPONIBILIDAD LOCAL, no origen del producto")
guardar("B", d)

# ═════════ C — 2 niveles con AHORRAS, badge premium nativo ═════════
d = cargar("C")
z = d["zonas"]
z["badge_premium"]["linea_1"] = "FÓRMULA PREMIUM"
z["badge_premium"]["linea_2"] = "MÁXIMA ABSORCIÓN"
z["badge_premium"].pop("bandera", None)
o = z["bloque_oferta"]
o["tiers"] = 2
o["tier_1"] = "1 TRATAMIENTO - %s" % P1
o["tier_2"] = "2 TRATAMIENTOS - %s + AHORRÁS %s" % (P2, AHORRO_2)
o["badge_central"] = "ENVÍO GRATIS con icono de camion, entre los dos niveles"
o["funcion"] = "el tier 2 debe verse como la decision obvia, igual que en la referencia"
o.pop("prohibido", None)
z["micro_garantias"]["items"] = ("['COMPRA 100% SEGURA', 'PAGO CONTRA ENTREGA', "
                                 "'DEVOLUCIÓN GARANTIZADA']")
guardar("C", d)

# ═════════ D — 3 niveles con MEJOR OFERTA / MAYOR AHORRO ═════════
d = cargar("D")
z = d["zonas"]
p = z["bloque_precios"]
p["tiers"] = 3
p["formato_tier"] = ("card con borde dorado: cantidad arriba, precio Black gigante, "
                     "etiqueta de valor debajo")
p["tier_1"] = "1 TRATAMIENTO - %s" % P1
p["tier_2"] = "2 TRATAMIENTOS - %s - MEJOR OFERTA" % P2
p["tier_3"] = "3 TRATAMIENTOS - %s - MAYOR AHORRO" % P3
p["funcion"] = "anclaje de 3 puntos, empuja al tier medio-alto"
p["regla"] = "el tier 2 lleva la etiqueta mas atractiva, no el 3"
p.pop("prohibido", None)
z["badge_garantia"]["color"] = "DORADO %s, borde doble, como en la referencia" % DORADO
z["barra_garantias"]["items"] = ("['ENVÍOS A TODA GUATEMALA', 'PAGO CONTRA ENTREGA', "
                                 "'COMPRA SEGURA Y GARANTIZADA']")
z["barra_garantias"]["regla_item_3"] = "el tercero lleva bandera de GUATEMALA"
z["_prohibido_en_este_brazo"] = ("Sin badge premium en la esquina superior: la referencia no lo "
                                 "tiene y el elemento diferenciador es la TRANSICION de 3 estados.")
guardar("D", d)

# ═════════ verificacion ═════════
print("--- patron por brazo ---")
for L in "ABCD":
    d = cargar(L)
    z = d["zonas"]
    zn = "bloque_precios" if "bloque_precios" in z else "bloque_oferta"
    tiers = z[zn].get("tiers", 1)
    s = json.dumps(d, ensure_ascii=False)
    print("%s | niveles=%d | tachado=%-5s | origen_US=%-5s | bandera_GT=%-5s | dorado=%s"
          % (L, tiers, TACHADO in s, "ESTADOS UNIDOS" in s, "GUATEMALA" in s.upper(),
             DORADO in s))
