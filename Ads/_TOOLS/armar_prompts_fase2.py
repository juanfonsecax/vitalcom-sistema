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
import csv
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


def leer_envase(producto_key):
    """Lee la identidad FISICA declarada del producto desde PRODUCTOS/_DIM_ENVASE.csv.

    POR QUE EXISTE (07-sep-2026): esta funcion antes se llamaba buscar_foto_producto() y
    devolvia el PRIMER archivo alfabetico de Ads/MEDIA_[PK]/, llamandolo "la foto limpia del
    producto". En MEDIA_TINNIDROP el primero alfabetico era TINNIDROP_R1_VIVIRCONESO.png, que
    NO es un packshot: es un ANUNCIO entero con el frasco VERDE y la marca SOUTH MOON. El
    prompt le ordenaba al modelo copiar "este envase real respetando su forma y etiqueta", asi
    que las 5 piezas de FASE 2 salieron verdes y de otra marca. El packshot se DECLARA, no se
    adivina: un dato, un dueno.
    """
    ruta = os.path.join(PROD_DIR, "_DIM_ENVASE.csv")
    if not os.path.isfile(ruta):
        return None
    with open(ruta, encoding="utf-8") as f:
        for fila in csv.DictReader(f):
            if fila.get("producto_key", "").strip() == producto_key:
                return fila
    return None


def leer_escalera(producto_key):
    """Arma los tiers con ANTES y AHORA desde PRODUCTOS/_DIM_PRECIOS.csv.

    POR QUE EXISTE (08-sep-2026): los precios estaban hardcodeados por producto dentro de este
    script, contra la regla 'un dato, un dueno'. Y el precio ANCLA ('antes Q...') no existia en
    ningun lado del sistema, asi que el modelo lo completaba solo: en TINNIDROP_F2_CN05 escribio
    'PRECIO NORMAL: Q299.00', que es nuestro precio de TRES frascos presentado como el precio
    normal de UNO. La oferta se declara, no se improvisa.
    """
    ruta = os.path.join(PROD_DIR, "_DIM_PRECIOS.csv")
    if not os.path.isfile(ruta):
        return None
    filas = []
    with open(ruta, encoding="utf-8") as f:
        for x in csv.DictReader(f):
            if x.get("producto_key") == producto_key and x.get("estado") == "ACTIVO":
                filas.append(x)
    if not filas:
        return None
    filas.sort(key=lambda x: int(x["unidades"]))

    tiers, etiquetas = {}, {1: "", 2: " (OFERTA MÁS ELEGIDA ⭐)", 3: " (Tratamiento Completo)"}
    for i, x in enumerate(filas[:3], start=1):
        u = int(x["unidades"])
        ahora = f"Q{float(x['precio_q']):.0f}"
        antes = x.get("precio_antes_q", "").strip()
        txt = f"{u} Frasco{'s' if u > 1 else ''} por {ahora}"
        if antes:
            txt += f" (antes Q{float(antes):.0f})"
        tiers[f"TIER_{i}"] = txt + etiquetas.get(u, "")
    return tiers or None


def requerir_precios_reales(producto_key):
    """La escalera de precios REAL o BLOQUEO — nunca los precios de otro producto.

    Misma clase de bug que buscar_foto_producto() (07-sep): leer_escalera() ya existia
    desde el 08-sep para leer PRODUCTOS/_DIM_PRECIOS.csv, pero cuando devolvia None (sin
    fila ACTIVA para este producto) el llamador caia en silencio a un PRECIOS_GT
    hardcodeado — Q179/Q239/Q299 de TINNIDROP para cualquier producto sin fila propia, o
    Q199/Q299/Q399 de CLEARSTEM en la adaptacion de LucidBot. Invariante 4: si falta un
    input requerido, se detiene con el nombre de quien lo produce — nunca se asume."""
    precios = leer_escalera(producto_key)
    if not precios:
        raise SystemExit(
            f"BLOQUEANTE: {producto_key} no tiene fila ACTIVA en PRODUCTOS/_DIM_PRECIOS.csv.\n"
            f"  Sin la escalera de precios real, no se generan los prompts: caer a los precios "
            f"de otro producto (TINNIDROP Q179/Q239/Q299) fue exactamente el bug que "
            f"leer_escalera() vino a cerrar el 08-sep-2026 — no se reintroduce por la puerta "
            f"de atras con un fallback hardcodeado.\n"
            f"  Agrega la fila de {producto_key} en PRODUCTOS/_DIM_PRECIOS.csv (unidades, "
            f"precio_q, precio_antes_q, estado=ACTIVO) antes de generar."
        )
    return precios


def buscar_foto_producto(producto_key):
    """Devuelve la ruta absoluta del packshot DECLARADO. Falla ruidoso si no lo hay."""
    envase = leer_envase(producto_key)
    if not envase or not envase.get("packshot", "").strip():
        raise SystemExit(
            f"BLOQUEANTE: {producto_key} no tiene packshot declarado en "
            f"PRODUCTOS/_DIM_ENVASE.csv.\n"
            f"  Agregale su fila (packshot, color_envase, marca_impresa) antes de generar.\n"
            f"  No se adivina agarrando un archivo de Ads/MEDIA_{producto_key}/: asi fue como "
            f"TINNIDROP heredo un frasco verde de otra marca."
        )
    ruta = os.path.join(BASE, envase["packshot"].replace("/", os.sep))
    if not os.path.isfile(ruta):
        raise SystemExit(
            f"BLOQUEANTE: {producto_key} declara el packshot '{envase['packshot']}' "
            f"pero el archivo no existe en el disco.\n"
            f"  Ponelo ahi o corregi la fila de PRODUCTOS/_DIM_ENVASE.csv."
        )
    return ruta


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
    foto_prod_rel = os.path.relpath(foto_prod_path, BASE).replace("\\", "/")

    # 2b. Precios REALES — se bloquea ANTES de armar un solo paquete, no se descubre a
    # medio prompt ni se cae a los de otro producto (ver requerir_precios_reales).
    precios_reales = requerir_precios_reales(producto_key)

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
                "GARANTIAS": "Pago Contra Entrega en Toda Guatemala · Envío Gratis · Producto 100% Original Americano",
                "CTA": "PEDÍ EL TUYO POR WHATSAPP AQUÍ"
            }
        elif producto_key.upper() == "TINNIDROP":
            variables_adaptadas = {
                "PRODUCTO": "Tinnidrop Spray Ótico Original (Azul y Blanco)",
                "DESCRIPTOR": "Alivio botánico del zumbido y timbre en los oídos",
                "HOOK_TITULAR": "¿CANSADO DE GASTAR EN CONSULTAS QUE SOLO DICEN 'APRENDÉ A VIVIR CON EL ZUMBIDO'?",
                "SUB_HOOK": "Menos de lo que cuesta una sola consulta con el especialista. Fórmula botánica de aplicación ótica.",
                "SINTOMA_ANTES": "Pitido agudo constante, noches en vela, dolor de cabeza y recetas caras que no quitan el ruido",
                "RESULTADO_DESPUES": "Silencio auditivo, descanso reparador en las noches y tranquilidad sin gastar de más",
                "ACTIVOS_CLAVE": [
                    "Ginkgo Biloba: Estimula la microcirculación en el canal auditivo",
                    "Extractos Botánicos: Calman la hiperexcitabilidad del nervio",
                    "Aplicación Ótica: Actúa directo en el oído, sin pasar por el estómago"
                ],
                "GARANTIAS": "Pago Contra Entrega en Toda Guatemala · Envío Gratis · Producto 100% Original Sellado",
                "CTA": "PEDÍ POR WHATSAPP CON ENVÍO GRATIS AQUÍ"
            }
        else:
            variables_adaptadas = {
                "PRODUCTO": f"{producto_key} Original",
                "DESCRIPTOR": "Fórmula avanzada de alivio",
                "HOOK_TITULAR": f"¡ALIVIO COMPROBADO PARA {angulo.replace('_', ' ')}!",
                "SUB_HOOK": "Fórmula natural importada con respaldo comprobado.",
                "ACTIVOS_CLAVE": ["Extractos botánicos certificados", "Absorción rápida"],
                "GARANTIAS": "Pago Contra Entrega · Envío Gratis",
                "CTA": "PEDÍ EL TUYO POR WHATSAPP AQUÍ"
            }

        # La escalera de precios es SIEMPRE la real (precios_reales, validada al arrancar
        # generar_paquete_multimodal): sale de _DIM_PRECIOS.csv y trae el precio ancla, para
        # que el modelo no invente el "antes". Ningun bloque de arriba la hardcodea ya.
        variables_adaptadas["PRECIOS_GT"] = precios_reales

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
            f"- Garantías en micro-badges: {variables_adaptadas['GARANTIAS']} · Garantía de 30 días\n"
            f"- Registro sanitario (si la IMAGEN 1 muestra un sello regulatorio, va ESTE): "
            f"MSPAS NS02026-GT3147 · FDA 30045469041. Somos de Guatemala: nunca INVIMA ni "
            f"ningún otro regulador extranjero.\n"
            f"- Formato: 4:5 vertical (1080x1350 px), fotorrealista, iluminación comercial de estudio, colores nítidos, texto 100% legible y sin errores ortográficos.\n\n"
            f"REGLA DE PRECEDENCIA — MANDA LA IMAGEN 1:\n"
            f"La IMAGEN 1 es un anuncio que YA está validado en este mercado. Su estructura no es "
            f"una sugerencia: es el concepto que se está replicando. Qué bloques existen, cuántos "
            f"elementos tiene cada bloque y —sobre todo— qué NO aparece, lo decide la IMAGEN 1.\n"
            f"- Si algo de la lista de arriba NO está en la IMAGEN 1, OMITILO. Ejemplo: si la "
            f"IMAGEN 1 muestra un solo precio, va un solo precio, no la escalera de tres.\n"
            f"- Si la IMAGEN 1 tiene un elemento que la lista de arriba no menciona, REPLICALO "
            f"igual, PERO con nuestro dato — nunca con el de la IMAGEN 1.\n"
            f"- Ante cualquier duda entre la lista y la IMAGEN 1, se hace lo que muestra la IMAGEN 1.\n"
            f"La IMAGEN 1 dicta la FORMA. La lista de arriba dicta QUÉ DICE cada parte.\n"
            f"NUNCA se copia de la IMAGEN 1 ningún dato que identifique a SU producto: marca, "
            f"nombre, ingredientes, precios, entidad reguladora, números de registro, nombres o "
            f"ciudades de los testimonios. Todo eso va con NUESTRO dato, que está en la lista de "
            f"arriba. El elemento se replica siempre — lo que cambia es el dato que lleva adentro."
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
            + "\n".join("• " + precios_reales[t] for t in ("TIER_1", "TIER_2", "TIER_3") if t in precios_reales)
            + "\n¿A qué departamento o municipio te lo enviamos?"
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
