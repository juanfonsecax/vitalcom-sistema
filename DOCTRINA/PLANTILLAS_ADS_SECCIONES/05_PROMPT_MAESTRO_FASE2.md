## PROMPT MAESTRO — FASE 2 (rellenar [VARIABLES] y pegar en Gemini Pro / ChatGPT con la foto del producto)

```
Actúa como un diseñador experto en e-commerce, publicidad para Meta Ads y creativos de alta conversión.
Genera un creativo VERTICAL 4:5 (1080x1350 px), fotorrealista, profesional,
listo para pautar en Facebook e Instagram (feed). Debe venderse visualmente en menos de 3 segundos y NO parecer
generado por IA.

[ADJUNTO: FOTO DEL PRODUCTO — [DESCRIPCIÓN_PRODUCTO: forma, color de etiqueta, formato (cápsula/líquido/gotero), potencia]]

DATOS DEL PRODUCTO
- NOMBRE: [NOMBRE_PRODUCTO]
- BENEFICIO PRINCIPAL (del ángulo): [BENEFICIO_ANGULO]
- PROBLEMA QUE RESUELVE (dolor del avatar): [DOLOR_AVATAR]
- PÚBLICO OBJETIVO: [AVATAR: edad, género, situación]
- PAÍS/MERCADO: [pais del mercado del producto — `PRODUCTOS/_DIM_MERCADOS.csv`]
- TONO DE MARCA (de la página asignada): [TONO_IDENTIDAD: clínico-cálido / coach energía alta / confesional]
- OFERTA: [solo si este ad lleva precio según la regla de precio: "[P1u] con envío gratis". Cuando el ad lleva precio/oferta, SUMAR el SELLO DE OFERTA STARBURST (punto 7 de la jerarquía). Si no lleva precio, omitir oferta y sello.]

ESTILO VISUAL (anti-fatiga — elegir UNO distinto al ad anterior): [ESTILO de la lista de 15 abajo]

JERARQUÍA VISUAL (de arriba hacia abajo) — estructura del ad ganador: marca → hook → cuerpo/beneficio → CTA → prueba social → oferta:
1. MARCA VISIBLE (esquina superior, discreta pero legible): logo o nombre de la página [PAGINA_ASIGNADA] / "[NOMBRE_PRODUCTO]". Da confianza y Andrómeda la lee como señal.
2. HOOK (texto grande, máx 2 líneas, con 1 palabra clave en [COLOR_ACENTO]): "[HOOK_DEL_ANGULO]"
3. PRODUCTO PROTAGONISTA y GRANDE: [NOMBRE_PRODUCTO] nítido, bien iluminado, dominante en la composición — el cliente debe "imaginarlo inmenso", nunca chiquito ni perdido entre elementos. Opcional: 2 vistas del producto.
4. BENEFICIO PRINCIPAL (texto mediano): "[BENEFICIO_ANGULO en lenguaje del avatar]"
5. ELEMENTOS DE CONFIANZA (badges pequeños): [ej. "100% VEGANO", "HECHO EN USA", "[POTENCIA]", "PAGÁS AL RECIBIR", "+[N] clientes"]
6. CTA (botón [COLOR_ACENTO] redondeado): "[CTA: Escribinos hoy / Preguntanos cómo te ayudamos 👉]"
7. SELLO DE OFERTA — STARBURST (SOLO en los ads que llevan precio/oferta — regla de precio máx 3/6, ideal 2/6): un sello tipo **estrella de muchas puntas (sunburst/starburst)**, color contrastante y llamativo (rojo #C81E2D con borde amarillo, o amarillo con texto rojo), **tamaño MODERADO en una esquina superior** — que NO tape el producto ni pase del 20% de texto en imagen. Texto adentro, corto, en 2 líneas: si es COMBO → "SOLO HOY" (arriba, chico) + "2X1" (grande); si NO es combo → "MEGA OFERTA" + "SOLO HOY". Objetivo psicológico: que el avatar sienta *"acabo de encontrar algo increíble / esto es de HOY"* — urgencia/escasez (Cialdini), diferencia el ad de un post normal. Es el mismo sello que el lavado de video pone en los creativos de video (`lavar_videos.sh`), ahora también en imagen.
   > ⚠️ **COMPLIANCE ANDRÓMEDA:** es un SELLO DE OFERTA moderado, NO urgencia agresiva de miedo/liquidación ("última oportunidad", "se acaba ya", "al cuello", cuenta regresiva) — eso sube CPMs por baneo silencioso. Tono de oferta atractiva, no de pánico. Render propio y único (no copiar el sello de la competencia).

PALETA: [COLOR_ACENTO + colores derivados de la etiqueta del producto]. Tipografía = [KIT_TIPO_LETRA] del
PRODUCTO — la categoría tipográfica leída de su branding/etiqueta, LA MISMA en este ad, las infografías del bot
y la landing (ver PASO 0 ANÁLISIS DEL PRODUCTO + KIT TIPOGRÁFICO en DOCTRINA/PLANTILLAS_INFOGRAFIAS.md; la IA aproxima
por categoría, no clona la fuente), bold en el hook. Texto mínimo legible a 24pt en celular. Texto total < 20% del área.

COMPLIANCE (obligatorio): NO "cura/trata/elimina". NO antes/después corporal bilateral. NO promesas de
tiempo imposibles. Hablar del dolor del avatar está permitido; afirmar que cura el diagnóstico NO.
[Si el ángulo es médico sensible (diabético, neuropatía, virilidad): usar "apoya / ayuda a la función".]

RESULTADO: un anuncio que detiene el scroll del avatar específico, comunica el beneficio en 3 segundos
y motiva a escribir por WhatsApp. Entregar SOLO en 4:5 (1080x1350). El 9:16 (Reels/Historias) se genera
después, únicamente para los ads que ya ganaron.
```

---

