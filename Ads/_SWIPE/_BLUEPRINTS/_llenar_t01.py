# -*- coding: utf-8 -*-
"""CAPA 2 ejecutada para T01 / TINNIDROP. Genera los 4 LLENO_T01_*.json.

Parte de los blueprints y solo reemplaza {{}}. No agrega ni quita claves del layout:
lo unico que se suma es el bloque _override_T01, que esta autorizado por la ficha.
"""
import json, io, os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

AC  = "#1B4FA8"   # azul royal del empaque, saturado
CLA = "#EAF0FA"   # 15% saturacion
MED = "#7FA3D8"   # 45% saturacion
OSC = "#0A1A38"   # 20% luminosidad

# Hook IDENTICO en los 4. Se parte distinto porque cada layout tiene slots distintos,
# pero las palabras son las mismas.
L1 = u"¿VIVIR CON EL ZUMBIDO?"
L2 = u"ESO TE DIJERON. NO ES CIERTO."

GAR = u"['ENVÍO GRATIS', 'PAGÁS AL RECIBIR', 'GARANTÍA 90 DÍAS · GUATEMALA']"
PRECIO_FIJO = u"OFERTA · 1 FRASCO · Q178 · ENVÍO GRATIS · PAGÁS AL RECIBIR"


def guardar(bid, fill, extra):
    bp = json.load(io.open("blueprint_%s.json" % bid, encoding="utf-8"))
    s = json.dumps(bp, ensure_ascii=False)
    for k, v in fill.items():
        s = s.replace("{{%s}}" % k, v.replace('"', "'"))
    out = json.loads(s)
    out["formato"] = "4:5 (1080x1350)"
    out["_producto"] = "Tinnidrop 60 ml - South Moon"
    out["_test"] = "T01 brazo %s - angulo ME_DIJERON_NO_CURA (FIJO)" % bid[0]
    out["_override_T01"] = extra
    resto = json.dumps(out, ensure_ascii=False).split("{{")[1:]
    if resto:
        out["_faltantes"] = sorted(set(r.split("}}")[0] for r in resto))
    fn = "LLENO_T01_%s.json" % bid[0]
    json.dump(out, io.open(fn, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("%s -> %-22s faltantes: %s" % (bid[0], fn, out.get("_faltantes", "ninguno")))


guardar("A_autoridad_medica", {
    "PALETA_CLARO": CLA, "PALETA_MEDIO": MED, "PALETA_ACENTO": AC,
    "HOOK": L1, "SUBHOOK": L2,
    "SELLO_REGULATORIO": u"REGISTRO MSPAS · GUATEMALA",
    "ATRIBUTOS[3]": u"['FÓRMULA NATURAL', 'USO DIARIO', 'PRODUCTO IMPORTADO']",
    "FIGURA": u"médico de bata blanca con estetoscopio, latino, 50-55 años, canas, sonriendo, mirando a cámara",
    "CLAIM_CENTRAL": u"Una fórmula NATURAL que actúa donde nace el zumbido, no donde se escucha.",
    "PROBLEMAS[]": (u"[{'label':'ZUMBIDO CONSTANTE','foto':'primer plano de hombre mayor apretándose el oído con gesto de fastidio'},"
                    u"{'label':'NOCHES SIN DORMIR','foto':'persona mayor sentada en la cama de noche, luz de lámpara, con la mano en la sien'},"
                    u"{'label':'CONVERSACIONES PERDIDAS','foto':'mujer mayor inclinando la cabeza hacia quien le habla, gesto de esfuerzo'},"
                    u"{'label':'CANSANCIO TODO EL DÍA','foto':'hombre mayor frotándose los ojos frente a la mesa del desayuno'}]"),
    "OFERTA_LABEL": u"OFERTA 1", "CANTIDAD": u"1 FRASCO", "MONEDA": u"Q", "PRECIO": u"178",
    "GARANTIAS[3]": GAR,
    "SELLO_ORIGEN": u"PRODUCTO ORIGINAL IMPORTADO",
    "BOTANICOS[]": u"['hojas de ginkgo biloba', 'raíz de ginseng', 'hojas de menta fresca']",
}, {
    "formato": "4:5 en vez del 1:1 nativo",
    "titular": "El conteo nativo era L1 3-4 / L2 5-7 palabras. El hook es identico en los 4 brazos por diseno del test: manda el hook.",
    "precio": PRECIO_FIJO,
})

guardar("B_editorial_limpio", {
    "PALETA": CLA, "PALETA_ACENTO": AC,
    "CATEGORIA": u"BIENESTAR AUDITIVO", "SUBCATEGORIA": u"SPRAY ÓTICO NATURAL",
    "DIAS_GARANTIA": u"90",
    "HOOK_L1": L1, "HOOK_L2": u"ESO TE DIJERON.",
    "BENEFICIOS[5]": (u"[{'titulo':'CIRCULACIÓN AL OÍDO','sub':'con Ginkgo Biloba'},"
                      u"{'titulo':'BAJA LA TENSIÓN','sub':'con Ginseng, lo que lo agrava'},"
                      u"{'titulo':'ALIVIA LA IRRITACIÓN','sub':'del canal auditivo'},"
                      u"{'titulo':'FRESCOR INMEDIATO','sub':'se siente al aplicar'},"
                      u"{'titulo':'REGISTRO MSPAS','sub':'producto seguro y confiable'}]"),
    "ELEMENTOS_INGREDIENTE[]": u"['hojas de ginkgo biloba', 'raíz de ginseng cortada', 'ramitas de menta']",
    "CLAIM_SINTOMAS": u"PARA EL ZUMBIDO, EL PITIDO Y LA PRESIÓN EN EL OÍDO",
    "OFERTA_LABEL": u"OFERTA POR TIEMPO LIMITADO",
    "MONEDA": u"Q", "PRECIO_ENTERO": u"178", "PRECIO_DECIMAL": u"00",
    "CANTIDAD": u"1", "UNIDAD": u"FRASCO", "UNIDADES": u"60 ML",
    "PRECIO_TACHADO": u"",
    "GARANTIAS[3]": GAR, "PAIS": u"Guatemala",
}, {
    "formato": "4:5 en vez del 1:1 nativo",
    "precio_tachado": "ANULADO (vacio). El bloque de precio es identico en los 4 brazos.",
    "fondo": "El 'crema/hueso' nativo se resuelve como AZUL HIELO #EAF0FA: el producto es azul fuerte y un crema calido se le pelea.",
    "precio": PRECIO_FIJO,
})

guardar("C_dolor_maximalista", {
    "COLOR_MECANISMO": AC,
    "GANCHO_SCROLL": u"¿EL ZUMBIDO NO TE DEJA DORMIR NI PENSAR?",
    "FOTO_PERSONA_EN_DOLOR": u"hombre latino de 55-60 años apretándose el oído derecho con los ojos cerrados, gesto de fastidio, halo rojo sobre la zona del oído",
    "BADGE_L1": u"FÓRMULA", "BADGE_L2": u"IMPORTADA",
    "TITULAR_L1": L1, "TITULAR_L2_ACENTO": u"ESO TE DIJERON", "TITULAR_L3": u"NO ES CIERTO",
    "CATEGORIZACION_TECNICA": u"SPRAY ÓTICO NATURAL PARA EL ZUMBIDO Y EL PITIDO",
    "SELLOS_CONFIANZA[]": (u"['REGISTRO MSPAS', 'FÓRMULA NATURAL', 'PRODUCTO IMPORTADO', "
                           u"'USO DIARIO SEGURO', 'APTO ADULTOS 18+', 'GARANTÍA 90 DÍAS']"),
    "HEADER_SINTOMAS": u"¿TE IDENTIFICÁS?",
    "SINTOMAS[5]": (u"[{'titulo':'PITIDO QUE NO PARA','sub':'de día y de noche'},"
                    u"{'titulo':'ZUMBIDO EN EL SILENCIO','sub':'peor al acostarte'},"
                    u"{'titulo':'PERDÉS LA CONVERSACIÓN','sub':'pedís que repitan'},"
                    u"{'titulo':'PRESIÓN EN EL OÍDO','sub':'como tapado'},"
                    u"{'titulo':'NO TE CONCENTRÁS','sub':'cansancio constante'}]"),
    "HEADER_MECANISMO": u"ACTÚA DESDE LA RAÍZ",
    "MECANISMOS[3]": (u"[{'titulo':'ABRE LA CIRCULACIÓN','exp':'Ginkgo Biloba lleva sangre al oído interno'},"
                      u"{'titulo':'BAJA LA TENSIÓN NERVIOSA','exp':'Ginseng reduce el cortisol que lo dispara'},"
                      u"{'titulo':'DESINFLAMA EL CANAL','exp':'Regaliz alivia la irritación del conducto'}]"),
    "CLAIM_DOSIS": u"Con GINKGO BILOBA + GINSENG",
    "CLAIM_SECUNDARIO": u"+ Regaliz y Menta · 60 ml",
    "OFERTA_LABEL": u"OFERTA ESPECIAL",
    "CANT_1": u"1 FRASCO", "PRECIO_1": u"178",
    "CANT_2": u"", "PRECIO_2": u"", "AHORRO": u"", "MONEDA": u"Q",
    "CTA_L1": u"ESCRIBINOS POR WHATSAPP", "CTA_L2": u"Y LO RECIBÍS EN TU CASA",
    "GARANTIAS[3]": GAR,
}, {
    "formato": "4:5 en vez del 1:1 nativo",
    "tiers": "ANULADO. El nativo eran 2 tiers; en T01 el bloque de precio es identico en los 4: un solo precio Q178 / 1 frasco. Ignorar tier_2, el badge de ahorro y la funcion 'el tier 2 es la decision obvia'.",
    "precio": PRECIO_FIJO,
})

guardar("D_transformacion_temporal", {
    "PALETA_OSCURA": OSC, "PALETA_MEDIA": MED,
    "TIMELINE[3]": (u"[{'n':'1','label':'PRIMERA SEMANA','desc':'Aplicás dos veces al día','img':'hombre mayor aplicándose el spray en el oído frente al espejo del baño, de noche'},"
                    u"{'n':'2','label':'USO CONTINUO','desc':'Ya es parte de tu rutina','img':'el frasco de Tinnidrop sobre la mesa de luz junto a un vaso de agua, luz de mañana'},"
                    u"{'n':'3','label':'DÍA A DÍA','desc':'Volvés a tus conversaciones','img':'el mismo hombre conversando tranquilo con su esposa en la mesa, ambos sonriendo'}]"),
    "TITULAR": L1, "SUBTITULAR": L2,
    "DIAS_GARANTIA": u"90",
    "PARRAFO": u"Un spray natural que actúa sobre las TRES causas del zumbido: la mala circulación al oído, la tensión nerviosa y la irritación del canal auditivo.",
    "INGREDIENTE": u"GINKGO BILOBA", "DOSIS": u"60 ML",
    "BENEFICIO_RESUMEN": u"apoyo auditivo diario",
    "BENEFICIOS[5]": (u"[{'titulo':'CIRCULACIÓN AL OÍDO','sub':'Ginkgo Biloba lleva sangre al oído interno','img':'foto circular de flujo sanguíneo'},"
                      u"{'titulo':'BAJA LA TENSIÓN','sub':'Ginseng reduce el cortisol que lo agrava','img':'foto circular de terminación nerviosa'},"
                      u"{'titulo':'ALIVIA LA IRRITACIÓN','sub':'Regaliz desinflama el canal auditivo','img':'foto circular de canal auditivo'},"
                      u"{'titulo':'FRESCOR AL APLICAR','sub':'Menta, se siente desde la primera vez','img':'foto circular de hojas de menta'},"
                      u"{'titulo':'ABSORCIÓN DIRECTA','sub':'spray al canal, sin pastillas ni esperas','img':'foto circular del aplicador del spray'}]"),
    "ESCASEZ_L1": u"QUEDAN POCAS UNIDADES", "ESCASEZ_L2": u"Alta demanda esta semana",
    "CANT_1": u"1 FRASCO", "PRECIO_1": u"178",
    "CANT_2": u"", "PRECIO_2": u"", "CANT_3": u"", "PRECIO_3": u"", "MONEDA": u"Q",
    "CTA_L1": u"PEDILO HOY POR WHATSAPP", "CTA_URGENCIA": u"PAGÁS AL RECIBIR",
    "GARANTIAS[3]": GAR, "PAIS": u"Guatemala",
    "BOTANICOS[]": u"['hojas de ginkgo biloba', 'hojas de menta']",
    "IMAGEN_ESTADO": u"ver el campo img de cada estado en estados",
    "LABEL_TEMPORAL": u"ver el campo label de cada estado en estados",
    "DESC_ESTADO": u"ver el campo desc de cada estado en estados",
}, {
    "formato": "4:5 en vez del 1:1 nativo",
    "tiers": "ANULADO. El nativo eran 3 tiers; en T01 un solo precio Q178 / 1 frasco. Ignorar tier_2, tier_3 y las etiquetas MEJOR OFERTA / MAYOR AHORRO.",
    "MODO_DEGRADADO": "El timeline NO muestra el problema ni el resultado corporal: el tinnitus no es visualizable. Los 3 paneles son MOMENTOS DE USO. La regla_progresion nativa NO aplica. Registrar este brazo como DEGRADADO: si pierde, no significa que C8_PROGRESION no funcione.",
    "precio": PRECIO_FIJO,
})
