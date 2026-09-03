# -*- coding: utf-8 -*-
"""Ajustes del operador sobre los LLENO_T01_*.json — ronda 2026-08-19 (tras ver las 4 imagenes).

LECCION DE ESTA RONDA
---------------------
Un override que CONTRADICE a una zona no puede vivir como nota al pie: el modelo de imagen
lee la zona. En la ronda 1 el bloque _override_T01 decia "tiers ANULADO" pero la zona seguia
diciendo "tiers": 2 y "tiers": 3 — y las imagenes C y D salieron con 2 y 3 precios.
Regla nueva: si el override contradice una zona, SE REESCRIBE LA ZONA.

CAMBIOS PEDIDOS
1. Origen: todos los productos son de ORIGEN AMERICANO -> bandera de EEUU, no de Guatemala.
   Ojo: son DOS banderas distintas y no se mezclan.
       bandera de EEUU      -> origen del producto
       bandera de Guatemala -> registro MSPAS y disponibilidad local
2. "FRASCO" -> "TRATAMIENTO" en las 4.
3. Precio tachado de anclaje: Q298 (antes) contra Q178 (hoy). Igual en las 4.
4. La garantia va en DORADO, resaltada (en B salio azul).
5. El sello de registro MSPAS lleva bandera de Guatemala (brazo A).
6. Brazo C: el badge premium no dice "FORMULA IMPORTADA".
7. Brazos C y D: un solo tier de precio, reescrito en la zona.
"""
import json, io, os, copy

os.chdir(os.path.dirname(os.path.abspath(__file__)))

DORADO = "#D4A017"
TACHADO = "Q298"
PRECIO = "Q178"

BANDERAS = ("DOS BANDERAS DISTINTAS, NO SE MEZCLAN: la bandera de ESTADOS UNIDOS acompana "
            "siempre al ORIGEN del producto (origen americano). La bandera de GUATEMALA "
            "acompana solo al registro MSPAS y a la disponibilidad local.")

GAR_DORADA = ("El item de GARANTIA va en DORADO %s, resaltado sobre el resto de la barra. "
              "Nunca en el color de la paleta." % DORADO)


def cargar(letra):
    return json.load(io.open("LLENO_T01_%s.json" % letra, encoding="utf-8"))


def guardar(letra, d):
    json.dump(d, io.open("LLENO_T01_%s.json" % letra, "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)


def texto(d, viejo, nuevo):
    s = json.dumps(d, ensure_ascii=False).replace(viejo, nuevo)
    return json.loads(s)


# ═══════════ comunes a los 4 ═══════════
for L in "ABCD":
    d = cargar(L)
    d = texto(d, "1 FRASCO", "1 TRATAMIENTO")
    d = texto(d, "FRASCO", "TRATAMIENTO")
    d = texto(d, "frascos", "tratamientos")
    d = texto(d, "frasco", "tratamiento")
    d = texto(d, "Frasco", "Tratamiento")
    d = texto(d, "PRODUCTO IMPORTADO", "ORIGEN AMERICANO")
    d = texto(d, "PRODUCTO ORIGINAL IMPORTADO", "ORIGEN AMERICANO")
    d["_reglas_globales"] = {
        "unidad": "El producto SIEMPRE se llama TRATAMIENTO, nunca frasco.",
        "origen": "Producto de ORIGEN AMERICANO. Donde aparezca el origen va la bandera de "
                  "ESTADOS UNIDOS.",
        "banderas": BANDERAS,
        "garantia": GAR_DORADA,
        "precio": "Precio de hoy %s. Precio de anclaje tachado %s. Identicos en los 4 brazos."
                  % (PRECIO, TACHADO),
    }
    guardar(L, d)

# ═══════════ A — sello MSPAS con bandera de Guatemala ═══════════
d = cargar("A")
z = d["zonas"]
z["sello_autoridad"]["contenido"] = "REGISTRO MSPAS"
z["sello_autoridad"]["bandera"] = "bandera de GUATEMALA dentro del sello, junto al texto"
z["sello_autoridad"]["estilo"] = ("sello circular con borde doble DORADO %s, se tiene que leer "
                                  "como certificacion oficial" % DORADO)
z["sello_origen"]["contenido"] = "ORIGEN AMERICANO"
z["sello_origen"]["bandera"] = "bandera de ESTADOS UNIDOS dentro del sello"
z["bloque_oferta"]["linea_3"] = "ANTES %s (tachado, tipo chica, gris)" % TACHADO
guardar("A", d)

# ═══════════ B — precio tachado + garantia dorada ═══════════
d = cargar("B")
z = d["zonas"]
z["badge_garantia"]["color"] = ("DORADO %s solido. NO el azul de la paleta — en la ronda 1 salio "
                                "azul y se perdio contra el fondo." % DORADO)
z["bloque_oferta"]["linea_inferior"] = "PRECIO NORMAL: %s con tachado" % TACHADO
z["barra_garantias"]["regla_item_3"] = ("el tercero es el ORIGEN: bandera de ESTADOS UNIDOS + "
                                        "'ORIGEN AMERICANO'. No bandera de Guatemala.")
guardar("B", d)

# ═══════════ C — UN solo tier + badge sin 'formula importada' ═══════════
d = cargar("C")
z = d["zonas"]
z["badge_premium"]["linea_1"] = "ORIGEN"
z["badge_premium"]["linea_2"] = "AMERICANO"
z["badge_premium"]["bandera"] = "bandera de ESTADOS UNIDOS en el badge"
o = z["bloque_oferta"]
o["tiers"] = 1
o["tier_1"] = "1 TRATAMIENTO - %s   ·   ANTES %s (tachado)" % (PRECIO, TACHADO)
o.pop("tier_2", None)
o["funcion"] = ("UN SOLO PRECIO. Este es un test de concepto: el bloque de precio es identico "
                "en los 4 brazos. NO generar un segundo nivel de precio, ni badge de ahorro, "
                "ni comparacion entre cantidades.")
o["prohibido"] = "2 unidades, 3 unidades, 'AHORRAS Q', cualquier segundo tier."
guardar("C", d)

# ═══════════ D — UN solo tier + sin badge de formula ═══════════
d = cargar("D")
z = d["zonas"]
p = z["bloque_precios"]
p["tiers"] = 1
p["formato_tier"] = ("una sola card con borde DORADO %s: cantidad arriba, precio Black gigante, "
                     "y debajo el precio de anclaje tachado" % DORADO)
p["tier_1"] = "1 TRATAMIENTO - %s   ·   ANTES %s (tachado)" % (PRECIO, TACHADO)
p.pop("tier_2", None)
p.pop("tier_3", None)
p["funcion"] = ("UN SOLO PRECIO. Test de concepto: el bloque de precio es identico en los 4 "
                "brazos. NO generar 2 ni 3 niveles, ni etiquetas MEJOR OFERTA / MAYOR AHORRO.")
p["prohibido"] = "2 unidades, 3 unidades, MEJOR OFERTA, MAYOR AHORRO, cualquier segundo tier."
z["badge_garantia"]["color"] = "DORADO %s, borde doble" % DORADO
z["barra_garantias"]["regla_item_3"] = ("el tercero es el ORIGEN: bandera de ESTADOS UNIDOS + "
                                        "'ORIGEN AMERICANO'. No bandera de Guatemala.")
z["_prohibido_en_este_brazo"] = ("NO incluir badge de 'FORMULA IMPORTADA' ni ningun badge "
                                 "premium: en este brazo el elemento diferenciador es la "
                                 "TRANSICION de 3 estados, y un badge le compite.")
guardar("D", d)

# ═══════════ verificacion ═══════════
print("--- verificacion ---")
for L in "ABCD":
    s = io.open("LLENO_T01_%s.json" % L, encoding="utf-8").read()
    d = json.loads(s)
    tiers = None
    for zn in ("bloque_oferta", "bloque_precios"):
        if zn in d["zonas"] and "tiers" in d["zonas"][zn]:
            tiers = d["zonas"][zn]["tiers"]
    print("%s  frasco:%-5s  tiers:%-4s  tachado:%-5s  americano:%-5s  dorado:%s"
          % (L, "FRASCO" in s.upper(), tiers, TACHADO in s,
             "ORIGEN AMERICANO" in s, DORADO in s))
