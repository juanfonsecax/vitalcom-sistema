#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""sincronizar_planes.py — Construye los _PLAN.json faltantes para TINNIDROP, CLEARSTEM y NUSAVA.

Permite que gen_lanzador.py renderice la consola completa de 1 clic para todo el portafolio,
cerrando la brecha donde solo SERUM_COLAGENO_BOTOX tenía plan y los productos vivos estaban ciegos.
"""

import os
import sys
import io
import json

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROD = os.path.join(BASE, "PRODUCTOS")


def crear_plan_tinnidrop():
    ruta = os.path.join(PROD, "TINNIDROP", "_PLAN.json")
    plan = {
        "schema": "plan/1",
        "producto_key": "TINNIDROP",
        "fase": 1,
        "version": "v1",
        "origen": "Construido desde 2_DATA_PRODUCTO.txt y rendimiento histórico confirmado",
        "pagina": {
            "nombre": "Sanarte Guatemala",
            "page_id": "498977893288095"
        },
        "oferta": {
            "oferta_key": "ESCALERA",
            "precio_q": 179,
            "texto": "1u Q179 · 2u Q239 · 3u Q299 (la más elegida) · Envío gratis · Pagás al recibir"
        },
        "concepto_control": {
            "concepto_key": "C2_BENEFICIOS",
            "variante": "ligera",
            "canonico_id": "CN05_LISTA_BENEFICIOS"
        },
        "conjuntos": [
            {
                "n": 1,
                "angulo_key": "ACCESIBILIDAD_MEDICO",
                "angulo_titulo": "Accesibilidad económica vs médico",
                "avatar_edad": "45-60",
                "avatar_genero": "MIXTO",
                "nivel_conciencia": "3A",
                "formato": "VIDEO",
                "lleva_precio": True,
                "archivo_creativo": "tinnidrop_4.mp4",
                "prompt_imagen": None,
                "copy": {
                    "textos": [
                        "¿Cansado de gastar en consultas que solo te dicen 'aprendé a vivir con el zumbido'? 😮‍💨\n\nEl zumbido en el oído desgasta, roba el sueño y altera los nervios.\n\nTinnidrop es un spray sublingual con extractos botánicos que apoyan la circulación auditiva y relajan la tensión del nervio.\n\n✅ Fácil aplicación 2 veces al día\n✅ Fórmula natural sin químicos agresivos\n✅ Miles de personas ya descansan en paz\n\nPedí hoy con envío gratis y pagás en efectivo al recibir 👉"
                    ],
                    "titulos": ["Alivio para el zumbido", "No gastes de más", "Spray natural para oídos"],
                    "descripcion": "Pagás en efectivo al recibir en casa 🏠"
                }
            },
            {
                "n": 2,
                "angulo_key": "PERDIDA_AUDITIVA",
                "angulo_titulo": "Pérdida auditiva progresiva",
                "avatar_edad": "45-60",
                "avatar_genero": "MIXTO",
                "nivel_conciencia": "2",
                "formato": "VIDEO",
                "lleva_precio": False,
                "archivo_creativo": "tinnidrop_6.mp4",
                "prompt_imagen": None,
                "copy": {
                    "textos": [
                        "Ese pitido constante no es solo molestia… es tu oído pidiendo auxilio.\n\nCon el tiempo el zumbido puede afectar la claridad con la que escuchás a tu familia.\n\nProtegé tu audición a tiempo con la fórmula de Tinnidrop:\n✅ Estimula el microflujo del canal auditivo\n✅ Calma el timbre constante\n✅ Apoya tu bienestar día y noche\n\nConsultá con una asesora por WhatsApp 👉"
                    ],
                    "titulos": ["Cuidá tu audición", "El pitido tiene alivio", "Fórmula botánica"],
                    "descripcion": "+5,000 clientes satisfechos en GT"
                }
            },
            {
                "n": 3,
                "angulo_key": "NOCHES_SIN_DORMIR",
                "angulo_titulo": "Noches sin dormir por el pitido",
                "avatar_edad": "45-60",
                "avatar_genero": "MIXTO",
                "nivel_conciencia": "2",
                "formato": "IMAGEN",
                "lleva_precio": False,
                "archivo_creativo": "TINNIDROP_3_noches.jpg",
                "prompt_imagen": "Diseño publicitario 1080x1080 para Meta Ads, fotorrealista. Escena nocturna en habitación, persona de 50 años despierta en cama mirando el techo con molestia tocándose la oreja. Frasco de spray Tinnidrop en primer plano sobre mesa de noche bien iluminado. Texto claro: '¿El silencio de la noche te hace sonar más el oído?'. Colores azul noche y blanco, badge 'Pagá al recibir'.",
                "copy": {
                    "textos": [
                        "Cuando todo se apaga en la noche… el pitido se vuelve insoportable. 🌑\n\nNo lográs conciliar el sueño y te levantás agotado al día siguiente.\n\nDos aplicaciones de Tinnidrop antes de acostarte ayudan a relajar la tensión auditiva para que vuelvas a descansar.\n\nEscribinos y conocé la oferta especial de hoy 👉"
                    ],
                    "titulos": ["Volvé a dormir en silencio", "Alivio nocturno", "Descanso profundo"],
                    "descripcion": "Envío gratis a toda Guatemala 🇬🇹"
                }
            },
            {
                "n": 4,
                "angulo_key": "DETERIORO_COGNITIVO",
                "angulo_titulo": "Deterioro cognitivo y niebla mental",
                "avatar_edad": "45-60",
                "avatar_genero": "MIXTO",
                "nivel_conciencia": "1",
                "formato": "VIDEO",
                "lleva_precio": False,
                "archivo_creativo": "tinnidrop_3.mp4",
                "prompt_imagen": None,
                "copy": {
                    "textos": [
                        "El zumbido constante no te deja concentrarte ni pensar con claridad.\n\nEsa fatiga mental tiene solución apoyando la microcirculación cerebral y auditiva con Ginkgo Biloba y extractos naturales de Tinnidrop.\n\nMás enfoque, menos ruido de fondo.\nEscribinos hoy mismo 👉"
                    ],
                    "titulos": ["Despejá tu mente", "Menos zumbido, más calma", "Apoyo auditivo"],
                    "descripcion": "Tratamiento 100% natural"
                }
            },
            {
                "n": 5,
                "angulo_key": "ME_DIJERON_NO_CURA",
                "angulo_titulo": "Me dijeron que no tiene cura",
                "avatar_edad": "45-60",
                "avatar_genero": "MIXTO",
                "nivel_conciencia": "3A",
                "formato": "IMAGEN",
                "lleva_precio": True,
                "archivo_creativo": "TINNIDROP_5_medijeron.jpg",
                "prompt_imagen": "Creativo publicitario 1080x1080 px para Meta Ads. Frasco de Tinnidrop en primer plano con fondo médico desenfocado. Hook grande: '¿Te dijeron que tenías que acostumbrarte?'. Badge de oferta '2x1 Q239' y 'Envío gratis'. Estilo editorial limpio de salud.",
                "copy": {
                    "textos": [
                        "\"Aprendé a vivir con eso\"… la frase que nadie quiere escuchar. 💔\n\nAunque no haya soluciones mágicas, no tenés que resignarte al sufrimiento diario.\n\nMiles de guatemaltecos han reducido la intensidad del zumbido con Tinnidrop Spray.\n\n🔴 OFERTA LIMITADA: 2 frascos por Q239 con envío incluido.\nMandanos un mensaje y empezá tu tratamiento 👉"
                    ],
                    "titulos": ["No te resignes al zumbido", "Alivio real garantizado", "Oferta especial 2x1"],
                    "descripcion": "Pagás en efectivo al recibir"
                }
            },
            {
                "n": 6,
                "angulo_key": "INGREDIENTES_NATURALES",
                "angulo_titulo": "Alivio natural sin químicos agresivos",
                "avatar_edad": "45-60",
                "avatar_genero": "MIXTO",
                "nivel_conciencia": "2",
                "formato": "VIDEO",
                "lleva_precio": False,
                "archivo_creativo": "tinnidrop_1.mp4",
                "prompt_imagen": None,
                "copy": {
                    "textos": [
                        "Cuidá tu salud sin someter a tu cuerpo a químicos pesados.\n\nTinnidrop combina Ginkgo Biloba, Ginseng y extractos botánicos puros para el confort del canal auditivo.\n\nFácil de aplicar, suave y efectivo.\nPreguntá por nuestras promociones aquí 👉"
                    ],
                    "titulos": ["Fórmula botánica pura", "Sin químicos agresivos", "Alivio suave y natural"],
                    "descripcion": "Entrega en 24 a 48 horas"
                }
            }
        ]
    }
    with io.open(ruta, "w", encoding="utf-8") as f:
        json.dump(plan, f, ensure_ascii=False, indent=2)
    print(f"  Plan generado: {ruta}")


def crear_plan_clearstem():
    ruta = os.path.join(PROD, "CLEARSTEM", "_PLAN.json")
    plan = {
        "schema": "plan/1",
        "producto_key": "CLEARSTEM",
        "fase": 1,
        "version": "v1",
        "origen": "Construido desde 2_DATA_PRODUCTO.txt y 1_HACER_MANUAL.txt de CLEARSTEM",
        "pagina": {
            "nombre": "Belleza & Piel — Astrid García",
            "page_id": "823825257480758"
        },
        "oferta": {
            "oferta_key": "ESCALERA",
            "precio_q": 199,
            "texto": "1u Q199 · 2u Q299 (oferta irresistible) · 3u Q399 · Envío gratis · Pagás al recibir"
        },
        "concepto_control": {
            "concepto_key": "C2_BENEFICIOS",
            "variante": "ligera",
            "canonico_id": "CN05_LISTA_BENEFICIOS"
        },
        "conjuntos": [
            {
                "n": 1,
                "angulo_key": "RESISTENCIA_INSULINA",
                "angulo_titulo": "Acné hormonal y resistencia a la insulina (SOP)",
                "avatar_edad": "25-35",
                "avatar_genero": "MUJER",
                "nivel_conciencia": "1",
                "formato": "IMAGEN",
                "lleva_precio": False,
                "archivo_creativo": "CLEARSTEM_1_hormonal.jpg",
                "prompt_imagen": "Creativo cuadrado 1080x1080 px para Meta Ads. Mujer latina 28 años mirándose la mandíbula con acné quístico hormonal, luz natural, fondo limpio. Tarro de Clearstem Mindbodyskin en primer plano. Texto: '¿Brotes en la mandíbula que no se van con cremas?'. Badge 'Regula desde adentro'.",
                "copy": {
                    "textos": [
                        "¿Brotes inflamados en la mandíbula y cuello que empeoran antes de tu periodo? 😣\n\nEl acné hormonal no es suciedad exterior: es tu cuerpo pidiendo equilibrio interno (SOP, insulina, estrés).\n\nClearstem Mindbodyskin trabaja desde adentro:\n✅ Regula el exceso de sebo hormonal con DIM y Vitamina A\n✅ Desinflama sin dañar tu estómago\n✅ Piel más limpia y uniforme sin efecto rebote\n\nEscribinos y conocé el tratamiento natural 👉"
                    ],
                    "titulos": ["Acné hormonal en mandíbula", "Regulá desde adentro", "Sin cremas que resecan"],
                    "descripcion": "Tratamiento #1 para acné adulto"
                }
            },
            {
                "n": 2,
                "angulo_key": "ANTI_FALSIFICACION",
                "angulo_titulo": "Cuidado con imitaciones baratas",
                "avatar_edad": "25-40",
                "avatar_genero": "MIXTO",
                "nivel_conciencia": "3A",
                "formato": "VIDEO",
                "lleva_precio": True,
                "archivo_creativo": "Clearstem3.mp4",
                "prompt_imagen": None,
                "copy": {
                    "textos": [
                        "Cuidado con lo que ponés en tu cuerpo. El Clearstem original viene sellado y con lote garantizado.\n\nNo arriesgues tu piel con productos sin registro.\n\n🔴 HOY: Frasco original con envío gratis y pagás al recibir en tus manos por Q199 (o 2 por Q299).\n\nPedí el tuyo directamente con nuestras asesoras autorizadas 👉"
                    ],
                    "titulos": ["Original garantizado", "No compres imitaciones", "Fórmula auténtica"],
                    "descripcion": "Pagás en efectivo al recibir 🏠"
                }
            },
            {
                "n": 3,
                "angulo_key": "MEDICOS_FALLARON",
                "angulo_titulo": "Cuando las cremas y antibióticos fallaron",
                "avatar_edad": "25-40",
                "avatar_genero": "MIXTO",
                "nivel_conciencia": "2",
                "formato": "VIDEO",
                "lleva_precio": False,
                "archivo_creativo": "Clearstem2.mp4",
                "prompt_imagen": None,
                "copy": {
                    "textos": [
                        "Probaste jabones, ácidos, antibióticos y peelings… y a las dos semanas los granos vuelven. 😮‍💨\n\nPorque el acné persistente casi siempre viene del hígado, intestino y hormonas.\n\nClearstem ataca la raíz con antioxidantes y nutrientes específicos que limpian tu organismo desde el interior.\n\nMandanos un mensaje y recuperá la confianza en tu rostro 👉"
                    ],
                    "titulos": ["Atacá la raíz del acné", "Basta de efecto rebote", "Resultados desde adentro"],
                    "descripcion": "Envío a toda Guatemala"
                }
            },
            {
                "n": 4,
                "angulo_key": "DOLOR_EMOCIONAL_MASCULINO",
                "angulo_titulo": "Acné en hombres y mandíbula",
                "avatar_edad": "25-35",
                "avatar_genero": "HOMBRE",
                "nivel_conciencia": "2",
                "formato": "VIDEO",
                "lleva_precio": False,
                "archivo_creativo": "Clearstem13.mp4",
                "prompt_imagen": None,
                "copy": {
                    "textos": [
                        "Tener acné después de los 25 desgasta la seguridad de cualquier hombre.\n\nEvitás fotos, te molesta al afeitarte y las cremas te dejan la cara grasosa.\n\nClearstem se toma en cápsulas y regula la producción de grasa desde el origen. Simple, sin rutinas complicadas de 5 pasos.\n\nConsultanos por WhatsApp de forma privada 👉"
                    ],
                    "titulos": ["Acné masculino adulto", "Sin cremas grasosas", "Firmeza y piel limpia"],
                    "descripcion": "Asesoría privada por WhatsApp"
                }
            },
            {
                "n": 5,
                "angulo_key": "TESTIMONIO_RADICAL",
                "angulo_titulo": "Testimonio radical de transformación",
                "avatar_edad": "30-40",
                "avatar_genero": "MUJER",
                "nivel_conciencia": "3A",
                "formato": "VIDEO",
                "lleva_precio": True,
                "archivo_creativo": "Clearstem10.mp4",
                "prompt_imagen": None,
                "copy": {
                    "textos": [
                        "\"Pensé que a mis 30 años ya no me iba a quitar el acné nunca… hasta que limpié mi organismo por dentro\". ✨\n\nDescubrí por qué miles de personas ya dejaron de ocultarse tras el maquillaje.\n\nLlevate el tratamiento de 2 meses por solo Q299 con envío gratis.\nEscribinos ahora 👉"
                    ],
                    "titulos": ["Testimonio real de cambio", "Piel sana a los 30+", "Promo 2 frascos Q299"],
                    "descripcion": "Garantía de satisfacción"
                }
            },
            {
                "n": 6,
                "angulo_key": "EJE_INTESTINO_PIEL",
                "angulo_titulo": "El eje intestino-piel",
                "avatar_edad": "25-45",
                "avatar_genero": "MIXTO",
                "nivel_conciencia": "1",
                "formato": "IMAGEN",
                "lleva_precio": False,
                "archivo_creativo": "CLEARSTEM_6_intestino.jpg",
                "prompt_imagen": "Infografía visual 1080x1080 px para Meta Ads. Conexión gráfica limpia entre salud digestiva y piel del rostro. Ilustración médica sutil con el frasco de Clearstem. Titular: 'Si tu digestión está inflamada, tu piel también lo estará'.",
                "copy": {
                    "textos": [
                        "¿Sabías que la inflamación intestinal se refleja directo en tu piel como acné y enrojecimiento? 🧬\n\nLos ingredientes digestivos y antioxidantes de Clearstem apoyan tu flora y limpian tu piel al mismo tiempo.\n\nPedí información aquí 👉"
                    ],
                    "titulos": ["Salud intestinal y piel", "Desinflamá desde adentro", "Piel limpia y sana"],
                    "descripcion": "Envío gratis a todo el país"
                }
            }
        ]
    }
    with io.open(ruta, "w", encoding="utf-8") as f:
        json.dump(plan, f, ensure_ascii=False, indent=2)
    print(f"  Plan generado: {ruta}")


def crear_plan_nusava():
    ruta = os.path.join(PROD, "NusavaB12", "_PLAN.json")
    plan = {
        "schema": "plan/1",
        "producto_key": "NUSAVA",
        "fase": 1,
        "version": "v1",
        "origen": "Construido desde 2_DATA_PRODUCTO.txt de NusavaB12",
        "pagina": {
            "nombre": "GTR7 FanPage",
            "page_id": "1218486924672725"
        },
        "oferta": {
            "oferta_key": "2X1",
            "precio_q": 219,
            "texto": "2 frascos Q219 (oferta 2x1) · 4 frascos Q369 · Envío gratis · Pagás al recibir"
        },
        "concepto_control": {
            "concepto_key": "C2_BENEFICIOS",
            "variante": "ligera",
            "canonico_id": "CN05_LISTA_BENEFICIOS"
        },
        "conjuntos": [
            {
                "n": 1,
                "angulo_key": "ARDOR",
                "angulo_titulo": "Ardor y hormigueo en pies y manos (neuropatía)",
                "avatar_edad": "45-65",
                "avatar_genero": "MIXTO",
                "nivel_conciencia": "2",
                "formato": "VIDEO",
                "lleva_precio": True,
                "archivo_creativo": "nusava_ardor.mp4",
                "prompt_imagen": None,
                "copy": {
                    "textos": [
                        "¿Sentís quemazón, pinchazos o adormecimiento en la planta de los pies al caminar o acostarte? 🦶🔥\n\nEse ardor suele ser señal de terminaciones nerviosas desgastadas por falta de Vitamina B12 activa.\n\nNusava B12 Líquida Sublingual entra directo al torrente sanguíneo:\n✅ Calma la sensación de fuego y hormigueo en los pies\n✅ Apoya la regeneración de la mielina nerviosa\n✅ Absorción 5 veces más rápida que las pastillas comunes\n\n🔴 SOLO POR HOY 2X1: 2 frascos por Q219 con envío gratis.\nEscribinos por WhatsApp y te lo enviamos a casa 👉"
                    ],
                    "titulos": ["Ardor y dolor en pies", "Alivio para neuropatía", "Promo 2x1 Nusava B12"],
                    "descripcion": "Pagás en efectivo al recibir en casa 🏠"
                }
            },
            {
                "n": 2,
                "angulo_key": "MEMORIA_NIEBLA",
                "angulo_titulo": "Pérdida de memoria y concentración",
                "avatar_edad": "45-65",
                "avatar_genero": "MIXTO",
                "nivel_conciencia": "2",
                "formato": "VIDEO",
                "lleva_precio": False,
                "archivo_creativo": "nusava_memoria.mp4",
                "prompt_imagen": None,
                "copy": {
                    "textos": [
                        "¿Entrás a una habitación y olvidás a qué ibas? ¿Te cuesta encontrar las palabras? 🧠\n\nNo es solo la edad: el cerebro necesita Vitamina B12 para mantener la agilidad mental y los reflejos.\n\nUn gotero sublingual de Nusava B12 al día te ayuda a recuperar la lucidez y el enfoque que necesitás.\n\nConsultanos aquí 👉"
                    ],
                    "titulos": ["Recuperá tu agilidad mental", "Memoria y enfoque", "B12 líquida sublingual"],
                    "descripcion": "Entrega en 24-48 horas a toda GT"
                }
            },
            {
                "n": 3,
                "angulo_key": "FATIGA_CRONICA",
                "angulo_titulo": "Cansancio extremo y falta de energía",
                "avatar_edad": "35-55",
                "avatar_genero": "MIXTO",
                "nivel_conciencia": "1",
                "formato": "IMAGEN",
                "lleva_precio": True,
                "archivo_creativo": "NUSAVA_3_fatiga.jpg",
                "prompt_imagen": "Creativo para Meta Ads 1080x1080 px. Persona adulta agotada frente al trabajo o volante. Gotero de Nusava B12 con líquido rojo rubí resplandeciente. Titular: '¿Te levantás cansado aunque duermas 8 horas?'. Banner '2x1 Q219'.",
                "copy": {
                    "textos": [
                        "Te levantás sin energía, tomás café tras café y a las 2 de la tarde ya no podés con tu cuerpo.\n\nLa B12 es el combustible que tus células necesitan para producir energía real, no estimulantes pasajeros.\n\nSentí la diferencia desde la primera semana con Nusava B12 sublingual.\n\n🔴 Llevate 2 frascos por Q219 hoy mismo 👉"
                    ],
                    "titulos": ["Energía real todo el día", "Basta de fatiga constante", "Oferta 2x1 Nusava B12"],
                    "descripcion": "Envío gratis y pago contra entrega"
                }
            }
        ]
    }
    with io.open(ruta, "w", encoding="utf-8") as f:
        json.dump(plan, f, ensure_ascii=False, indent=2)
    print(f"  Plan generado: {ruta}")


def main():
    print("Sincronizando planes de lanzamiento a formato _PLAN.json...")
    crear_plan_tinnidrop()
    crear_plan_clearstem()
    crear_plan_nusava()
    print("Todos los productos vivos ahora cuentan con su _PLAN.json oficial.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
