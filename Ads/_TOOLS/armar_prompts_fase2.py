# -*- coding: utf-8 -*-
"""armar_prompts_fase2.py — Generador Automático de Lotes Creativos Multimodales para Fase 2.

QUE HACE:
1. Detecta automáticamente el ÁNGULO GANADOR desde PRODUCTOS/_DECISIONES.json (sin que el operador adivine).
2. Selecciona los 5 Blueprints Canónicos idóneos (vía seleccionar_canonicos.py).
3. Vincula para cada concepto:
   - La Imagen Base del competidor (Layout/Composición) desde Ads/_SWIPE/_IMG/
   - La Foto Real del producto desde Ads/MEDIA_[PRODUCTO]/
   - El JSON parametrizado con variables de dolor, precios en Q e ingredientes reales.
   - El Prompt Multimodal "Director de Arte" listo para pegar en ChatGPT / Gemini Pro.
4. Genera además la adaptación de mensajes para LucidBot (congruencia anuncio -> bot, respetando los 13 elementos).
"""

import os
import sys
import io
import json

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(BASE, "Ads", "_TOOLS"))

import seleccionar_canonicos as sc

PROD_DIR = os.path.join(BASE, "PRODUCTOS")
SWIPE_DIR = os.path.join(BASE, "Ads", "_SWIPE")
DECISIONES_JSON = os.path.join(PROD_DIR, "_DECISIONES.json")


def detectar_angulo_ganador(producto_key):
    """Lee _DECISIONES.json y extrae el ángulo con mejor volumen y CPA en estado ESCALAR."""
    if not os.path.exists(DECISIONES_JSON):
        return None, "No existe _DECISIONES.json"
    
    with io.open(DECISIONES_JSON, encoding="utf-8") as fh:
        data = json.load(fh)
        
    prods = data.get("productos", [])
    p_data = next((p for p in prods if p["producto_key"].upper() == producto_key.upper()), None)
    if not p_data:
        return None, f"Producto {producto_key} no encontrado en decisiones"
        
    celdas = p_data.get("celdas", [])
    # Filtrar por ESCALAR
    escalables = [c for c in celdas if c.get("estado") == "ESCALAR"]
    if not escalables:
        # Fallback al que tenga más ventas
        escalables = sorted(celdas, key=lambda x: x.get("ventas", 0), reverse=True)
        if not escalables:
            return None, "No hay celdas registradas"
            
    # Ordenar por ventas descendente y CPA real ascendente
    ganador = sorted(escalables, key=lambda x: (-x.get("ventas", 0), x.get("cpa_real_q") or 999))[0]
    return ganador["celda"], ganador


def buscar_foto_producto(producto_key):
    """Busca la foto limpia de producto en Ads/MEDIA_[PK]/."""
    media_dir = os.path.join(BASE, "Ads", f"MEDIA_{producto_key}")
    if not os.path.isdir(media_dir):
        return None
    for f in sorted(os.listdir(media_dir)):
        if f.lower().endswith((".png", ".jpg", ".jpeg")) and not f.startswith("."):
            return os.path.join(media_dir, f)
    return None


def obtener_perfil_producto(producto_key, angulo_ganador):
    """Construye el perfil para seleccionar_canonicos.py."""
    p = dict(sc.PLANTILLA_PERFIL)
    p["producto"] = producto_key
    p["angulo_ganador"] = angulo_ganador
    p["tiers_de_oferta"] = 3
    p["prueba_social_clientes"] = 1000

    if producto_key.upper() == "CLEARSTEM":
        p["categoria"] = "dolor"
        p["resultado_visible_en_el_cuerpo"] = True
        p["resultado_fotografiable_sin_montaje"] = True
        p["es_tratamiento_con_curva"] = True
        p["activo_estrella_con_dosis"] = True
        p["mecanismo_localizable_en_el_cuerpo"] = True
        p["sintomas_reconocibles"] = 3
        p["beneficios_distintos"] = 4
    elif producto_key.upper() == "TINNIDROP":
        p["categoria"] = "dolor"
        p["resultado_visible_en_el_cuerpo"] = False
        p["mecanismo_localizable_en_el_cuerpo"] = True
        p["es_tratamiento_con_curva"] = True
        p["sintomas_reconocibles"] = 3
        p["beneficios_distintos"] = 4
    elif producto_key.upper() == "NUSAVA":
        p["categoria"] = "dolor"
        p["resultado_visible_en_el_cuerpo"] = False
        p["mecanismo_localizable_en_el_cuerpo"] = True
        p["es_tratamiento_con_curva"] = True
        p["sintomas_reconocibles"] = 3
        p["beneficios_distintos"] = 4
    else:
        p["resultado_visible_en_el_cuerpo"] = True
        p["sintomas_reconocibles"] = 2
        p["beneficios_distintos"] = 3

    return p


def generar_paquete_multimodal(producto_key, angulo_manual=None):
    # 1. Determinar ángulo ganador por data
    if angulo_manual:
        angulo = angulo_manual
        info_angulo = {"celda": angulo, "ventas": "manual", "cpa_real_q": 0}
    else:
        angulo, info_angulo = detectar_angulo_ganador(producto_key)
        if not angulo:
            raise SystemExit(f"No se pudo detectar ángulo para {producto_key}: {info_angulo}")

    print("=" * 80)
    print(f" 🚀 FÁBRICA CREATIVA MULTIMODAL — FASE 2 LEAN")
    print(f" Producto: {producto_key}")
    print(f" Ángulo Ganador Coronado por Data: {angulo}")
    if isinstance(info_angulo, dict) and "ventas" in info_angulo:
        print(f" Desempeño Histórico: {info_angulo.get('ventas')} ventas | CPA Real: Q{info_angulo.get('cpa_real_q', 0):.2f}")
    print("=" * 80)

    # 2. Foto del producto
    foto_prod_path = buscar_foto_producto(producto_key)
    foto_prod_rel = os.path.relpath(foto_prod_path, BASE).replace("\\", "/") if foto_prod_path else "Ads/MEDIA_" + producto_key + "/packshot.png"

    # 3. Selección de los 5 blueprints canónicos
    perfil = obtener_perfil_producto(producto_key, angulo)
    sel_res = sc.seleccionar(perfil, n=5)
    elegidos = sel_res["seleccion"]

    # 4. Construir los 5 paquetes
    out_dir = os.path.join(BASE, "Ads", f"MEDIA_{producto_key}", f"FASE2_{angulo}")
    os.makedirs(out_dir, exist_ok=True)

    paquetes = []
    prompts_texto = []

    prompts_texto.append(f"══════════════════════════════════════════════════════════════════════════════")
    prompts_texto.append(f" PAQUETE CREATIVO MULTIMODAL — FASE 2 LEAN ({producto_key})")
    prompts_texto.append(f" ÁNGULO GANADOR CORONADO POR DATA: {angulo}")
    prompts_texto.append(f" FOTO DE TU PRODUCTO: {foto_prod_rel}")
    prompts_texto.append(f"══════════════════════════════════════════════════════════════════════════════\n")

    for idx, bp in enumerate(elegidos, 1):
        cid = bp["canonico_id"]
        ref_ficha = bp["ficha_referencia"]
        ficha_path = os.path.join(SWIPE_DIR, "_BLUEPRINTS", "FICHAS", f"{ref_ficha}.json")

        foto_base_rel = "No disponible"
        dispositivo_txt = bp.get("dispositivo", "")
        if os.path.exists(ficha_path):
            with io.open(ficha_path, encoding="utf-8") as fh:
                f_data = json.load(fh)
                orig_file = f_data.get("origen", {}).get("archivo", "")
                foto_base_rel = os.path.join("Ads", "_SWIPE", orig_file).replace("\\", "/")
                dispositivo_txt = f_data.get("dispositivo_dominante", dispositivo_txt)

        # Variables adaptadas al producto y ángulo
        if producto_key.upper() == "CLEARSTEM":
            variables_adaptadas = {
                "PRODUCTO": "Clearstem Mindbodyskin (90 Cápsulas)",
                "DESCRIPTOR": "Tratamiento hormonal de raíz para el acné",
                "HOOK_TITULAR": "¡EL ACNÉ HORMONAL Y LA RESISTENCIA A LA INSULINA NO SE CURAN CON CREMAS!",
                "SUB_HOOK": "Ataca el exceso de sebo, la inflamación y los picos de glucosa desde adentro.",
                "SINTOMA_ANTES": "Rostro con brotes profundos e inflamados en mandíbula, poros obstruidos y textura grasa",
                "RESULTADO_DESPUES": "Piel limpia, calmada, textura lisa y poros cerrados sin manchas rojas",
                "ACTIVOS_CLAVE": [
                    "DIM: Equilibra el exceso hormonal y el sebo",
                    "Glutatión + Vitamina A: Desinflaman y regeneran la piel",
                    "Diente de León: Apoya la desintoxicación hepática"
                ],
                "PRECIOS_GT": {
                    "TIER_1": "1 Frasco (1 Mes) por Q199",
                    "TIER_2": "2 Frascos (2 Meses) por Q299 (OFERTA MÁS ELEGIDA ⭐)",
                    "TIER_3": "3 Frascos (Tratamiento Completo) por Q399"
                },
                "GARANTIAS": "Pago Contra Entrega en Toda Guatemala · Envío Gratis · Producto 100% Original Americano",
                "CTA": "PIDE EL TUYO POR WHATSAPP AQUÍ"
            }
        elif producto_key.upper() == "TINNIDROP":
            variables_adaptadas = {
                "PRODUCTO": "Tinnidrop Spray Sublingual Original (Azul y Blanco)",
                "DESCRIPTOR": "Alivio botánico del zumbido y timbre en los oídos",
                "HOOK_TITULAR": "¿CANSADO DE GASTAR EN CONSULTAS QUE SOLO DICEN 'APRENDÉ A VIVIR CON EL ZUMBIDO'?",
                "SUB_HOOK": "Menos de lo que cuesta una sola consulta con el especialista. Fórmula botánica sublingual.",
                "SINTOMA_ANTES": "Pitido agudo constante, noches en vela, dolor de cabeza y recetas caras que no quitan el ruido",
                "RESULTADO_DESPUES": "Silencio auditivo, descanso reparador en las noches y tranquilidad sin gastar de más",
                "ACTIVOS_CLAVE": [
                    "Ginkgo Biloba: Estimula la microcirculación en el canal auditivo",
                    "Extractos Botánicos: Calman la hiperexcitabilidad del nervio",
                    "Fórmula Sublingual: Absorción rápida directa sin dañar el estómago"
                ],
                "PRECIOS_GT": {
                    "TIER_1": "1 Frasco por Q179",
                    "TIER_2": "2 Frascos por Q239 (OFERTA MÁS ELEGIDA ⭐)",
                    "TIER_3": "3 Frascos por Q299 (Tratamiento Completo)"
                },
                "GARANTIAS": "Pago Contra Entrega en Toda Guatemala · Envío Gratis · Producto 100% Original Sellado",
                "CTA": "PEDÍ POR WHATSAPP CON ENVÍO GRATIS AQUÍ"
            }
        else:
            variables_adaptadas = {
                "PRODUCTO": f"{producto_key} Original",
                "DESCRIPTOR": "Fórmula avanzada de alivio",
                "HOOK_TITULAR": f"¡ALIVIO COMPROBADO PARA {angulo.replace('_', ' ')}!",
                "SUB_HOOK": "Fórmula natural importada con respaldo comprobado.",
                "ACTIVOS_CLAVE": ["Extractos botánicos certificados", "Absorción sublingual rápida"],
                "PRECIOS_GT": {"TIER_1": "1 Unidad por Q179", "TIER_2": "2 Unidades por Q239", "TIER_3": "3 Unidades por Q299"},
                "GARANTIAS": "Pago Contra Entrega · Envío Gratis",
                "CTA": "PIDE EL TUYO POR WHATSAPP AQUÍ"
            }

        nombre_archivo = f"{producto_key}_F2_{cid.split('_')[0]}_{angulo[:12]}.png"

        # Prompt Multimodal listo para copiar en Gemini / ChatGPT
        prompt_ia = (
            f"Actúa como Director de Arte Senior y diseñador de anuncios de alta conversión para Meta Ads en Guatemala.\n"
            f"Te he adjuntado 2 imágenes:\n"
            f"  • IMAGEN 1 (Referencia visual): {foto_base_rel} -> Mantén EXACTAMENTE su distribución espacial, composición geométrica, encuadre de cámara y jerarquía de elementos.\n"
            f"  • IMAGEN 2 (Mi producto real): {foto_prod_rel} -> Coloca este envase/frasco real en la posición del producto hero, respetando su forma y etiqueta.\n\n"
            f"INSTRUCCIONES DE REEMPLAZO Y DISEÑO:\n"
            f"- Dispositivo Canónico: {dispositivo_txt}\n"
            f"- Titular Principal (Top, grande y legible): \"{variables_adaptadas['HOOK_TITULAR']}\"\n"
            f"- Subtitular: \"{variables_adaptadas['SUB_HOOK']}\"\n"
            f"- Beneficios en viñetas/cards: {', '.join(variables_adaptadas['ACTIVOS_CLAVE'])}\n"
            f"- Escalera de Precios: Tier 1: {variables_adaptadas['PRECIOS_GT']['TIER_1']} | Tier 2: {variables_adaptadas['PRECIOS_GT']['TIER_2']} | Tier 3: {variables_adaptadas['PRECIOS_GT']['TIER_3']}\n"
            f"- Franja inferior: Botón verde WhatsApp con texto: \"{variables_adaptadas['CTA']}\"\n"
            f"- Garantías en micro-badges: {variables_adaptadas['GARANTIAS']}\n"
            f"- Formato: 4:5 vertical (1080x1350 px), fotorrealista, iluminación comercial de estudio, colores nítidos, texto 100% legible y sin errores ortográficos."
        )

        item = {
            "slot": idx,
            "canonico_id": cid,
            "nombre_blueprint": bp["nombre"],
            "archivo_salida": nombre_archivo,
            "foto_base_competidor": foto_base_rel,
            "foto_producto_propio": foto_prod_rel,
            "variables_json": variables_adaptadas,
            "prompt_director_de_arte": prompt_ia
        }
        paquetes.append(item)

        prompts_texto.append(f"──────────────────────────────────────────────────────────────────────────────")
        prompts_texto.append(f" CONCEPTO #{idx} · {bp['nombre']} ({cid})")
        prompts_texto.append(f" Guardar archivo generado como: {nombre_archivo}")
        prompts_texto.append(f" [1] FOTO BASE REFERENCIA: {foto_base_rel}")
        prompts_texto.append(f" [2] FOTO TU PRODUCTO:     {foto_prod_rel}")
        prompts_texto.append(f"──────────────────────────────────────────────────────────────────────────────")
        prompts_texto.append(f"{prompt_ia}\n\n")

    # 5. Adaptación de LucidBot para este ángulo (Congruencia extremo a extremo)
    adaptacion_bot = {
        "angulo_ganador": angulo,
        "saludo_inicial_hook": (
            "¡Hola! Vi que te interesó Clearstem para el acné hormonal y la resistencia a la insulina 🌿 "
            "Si sentís que por más cremas que usás los brotes siguen saliendo en la mandíbula o cuello, "
            "es porque el problema viene de adentro (picos de glucosa y exceso de sebo). "
            "¿Hace cuánto tiempo venís lidiando con estos brotes?"
        ),
        "pregunta_calificacion": (
            "Para darte la recomendación exacta: ¿has notado que empeoran antes de tu período, "
            "después de comer carbohidratos/dulces, o cuando estás bajo mucho estrés?"
        ),
        "presentacion_solucion": (
            "Exactamente por eso las cremas comunes no te han funcionado. Clearstem Mindbodyskin trabaja con "
            "DIM natural y Glutatión que regulan las hormonas y el hígado para detener el sebo antes de que tape el poro."
        ),
        "oferta_precio": (
            "Hoy tenemos cobertura completa en Guatemala con PAGO CONTRA ENTREGA (pagás en efectivo al recibir):\n"
            "• 1 Frasco (1 Mes): Q199\n"
            "• 2 Frascos (2 Meses - Tratamiento Recomendado): Q299 (Ahorrás Q99 ⭐)\n"
            "• 3 Frascos (Tratamiento Completo): Q399\n"
            "¿A qué departamento o municipio te lo enviamos?"
        )
    }

    # Guardar archivos
    salida_txt = os.path.join(out_dir, f"PROMPTS_FASE2_{angulo}.txt")
    with io.open(salida_txt, "w", encoding="utf-8") as f:
        f.write("\n".join(prompts_texto))

    salida_json = os.path.join(out_dir, f"PAQUETE_CREATIVO_{angulo}.json")
    with io.open(salida_json, "w", encoding="utf-8") as f:
        json.dump({"producto": producto_key, "angulo": angulo, "conceptos": paquetes, "lucidbot_adaptacion": adaptacion_bot}, f, ensure_ascii=False, indent=2)

    print(f"✅ Generados los 5 paquetes creativos multimodales en:")
    print(f"   📄 {salida_txt}")
    print(f"   📄 {salida_json}")
    print(f"\n✅ Adaptación de LucidBot generada (congruencia anuncio -> bot).")
    return salida_txt, salida_json, paquetes, adaptacion_bot


if __name__ == "__main__":
    pk = sys.argv[1] if len(sys.argv) > 1 else "CLEARSTEM"
    ang = sys.argv[2] if len(sys.argv) > 2 else None
    generar_paquete_multimodal(pk, ang)
