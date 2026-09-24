# PLANTILLAS_ADS — ADS DE TESTEO (PROMPT MAESTRO DE CREATIVOS)

> **Qué es esto:** la plantilla para generar los **anuncios de imagen** que van en la campaña de Meta Ads (stop-scroll). Es lo que se TESTEA. Basado en el "Prompt Maestro de Creativos que Venden" (Comunidad Mercy Pardo, Clase 14 + PDF) y las reglas de Andrómeda (Clase 4, 19).
>
> **NO confundir con `DOCTRINA/PLANTILLAS_INFOGRAFIAS.md`:** ese archivo son las 3 imágenes informativas DENTRO del flujo de WhatsApp (Info 1/2/3) + IMAGEN 4 anti-imitación. Este archivo son los ANUNCIOS que detienen el scroll en el feed.
>
> **Cuándo se usa (ETAPA-4):**
> - **FASE 1:** generar 1 ad-imagen por cada ángulo cuyo creativo asignado sea IMAGEN (ángulos vírgenes/descubiertos sin video). Los ángulos con video usan el video, no necesitan ad-imagen en FASE 1.
>   > **Decisión del operador (22-sep-2026), reemplaza la línea anterior:** FASE 1 corre TODO EN
>   > IMAGEN — se genera 1 ad-imagen para los 6 ángulos, ninguno usa el video como creativo. El
>   > video queda como fuente del ángulo (`etapa-0`) y se testea en FASE 2 como un concepto más.
>   > Dueño de la regla: `Ads/_TOOLS/gen_plan.py --validar`.
> - **FASE 2:** generar el BANCO anti-fatiga (mínimo 1 por microángulo, idealmente muchas variaciones con estilos distintos) para el escalado horizontal. Además del estilo, cada concepto declara su **ROL DE EMBUDO (TOFU/MOFU/BOFU)** según el nivel de conciencia del avatar (ver ETAPA-4 FASE 2 · `DOCTRINA/ESCALADO_PLAYBOOK.md` §4) — el banco cubre las 3 etapas para alimentar el embudo interno de la CBO.
>
> **Doctrina vs. prompt final:** las citas de mentor/clase que aparecen en este archivo (ej. "Clase 19, Joaquín") son criterio interno — explican el PORQUÉ de la regla para quien construye o ajusta esta plantilla. Al rellenar el PROMPT MAESTRO con las `[VARIABLES]` del producto para entregarlo en `1_HACER_MANUAL.txt`, esas citas se OMITEN — el operador solo recibe la instrucción ya resuelta, lista para pegar, sin referencias a clases.

---

## REGLAS DE COMPLIANCE CREATIVO (ANDRÓMEDA) — obligatorias en cada ad

- **Texto en imagen < 20% del área** (más texto = hasta −50% de entrega). Solo hook corto, números y CTA. Nunca párrafos.
- **Prohibido antes/después bilateral** de cuerpo humano. Alternativa: "Semana 1 / Semana 4" sin comparación física directa.
- **Cada ad ÚNICO** (Meta penaliza duplicados propios y de competencia). Variar y quitar metadatos al reusar.
- **Se vende en <3 segundos sin leer el copy.** Jerarquía: hook → producto → beneficio → oferta → CTA.
- **Sin "cura/trata/elimina"** ni promesas de tiempo imposibles. **Nunca usar TES.**
- **Que NO parezca generado por IA** (sin manos deformes, texto ilegible, logos falsos).
- **Formato de producción (testeo) = 4:5 (1080×1350) ÚNICO** (decisión operador 2026-07-14). Producir TODO el banco en 4:5: ocupa ~25% más de pantalla vertical en el feed móvil → más scroll-stop por el mismo esfuerzo, mismo CPM (Meta ya prioriza 4:5 en feed). NO hacer 1:1 en el testeo. El **9:16 (Reels/Historias) se genera DESPUÉS, solo para los ads que ya ganaron**. Mantener hook/CTA/sello centrados y lejos de los bordes por si luego se recorta. Advantage+/Andrómeda auto-expande solo un poco — no fabrica un 9:16 bueno ni respeta el texto/sello, por eso se da el ratio correcto de entrada.

**QUÉ PREMIA ANDRÓMEDA (usar cuando calce el ángulo) — Clase 4:**
- **Rostro mirando el producto / escena de uso real:** el cerebro procesa el estado emocional de otra persona antes que el producto. Una persona del avatar usando o mirando el producto convierte.
- **Prueba social visual:** testimonio + producto en la MISMA imagen (estilo TESTIMONIO de los 15) — da muy buenos resultados.
- **Texto legible:** nunca fondo amarillo con letra blanca; el avatar (a veces 55+) tiene que poder leer. "Las personas que SÍ compran necesitan información" (Clase 19).

---

## ENFOQUE AGRESIVO / DE IMPACTO (variación de choque — validado por data de competencia)

> **Qué es:** una VARIACIÓN del creativo que lidera con la AMENAZA en primer plano y choque visual crudo, en vez
> del estilo limpio/aspiracional. Nace de la data real: en categorías de plaga, miedo, higiene y "problema
> asqueroso", los anuncios más fuertes de la competencia (ej. la rata gigante amenazante de "¡AHUYENTA RATAS Y
> RATONES!") rinden porque el **asco/miedo crudo detiene el scroll más rápido** que una escena bonita. Es la
> misma lógica de Andrómeda ("se vende en <3 segundos") y del hook de dolor de Mercy, llevada al extremo visual.

**Cuándo usarlo (NO en todos los ads):**
- **1 a 2 de los 6 conjuntos por lanzamiento** llevan la variación agresiva — nunca los 6. El resto mantiene los
  15 estilos limpios/diversos. Así se prueba el enfoque de choque SIN sacrificar la diversidad de conceptos que
  premia Andrómeda ni la entrega (el texto grande + escena cargada sube el scroll-stop pero baja un poco la
  entrega por la regla del <20% de texto).
- Aplicar preferentemente al **ángulo amplio/genérico** (abre mercado, TOFU) y a un **ángulo de MIEDO**
  (veneno/niños, incendio por cables, plaga que invade) — son los que mejor aguantan el tono de choque.
- Encaja mejor en nichos de **plaga, higiene, miedo, salud urgente o "problema asqueroso"**; en nichos
  aspiracionales (belleza, fitness) usar con cuidado o no usar.

**Cómo se ve la variación agresiva:**
- **Protagonista de choque en primer plano y grande:** la amenaza real (rata/ratón/insecto/plaga, o el "antes"
  crudo) mostrando el peor momento — cerca de la cámara, con expresión/ángulo amenazante.
- **Ambiente crudo, no limpio:** penumbra, tonos oscuros/grises, suciedad insinuada — nada de blanco de estudio.
- **Titular en MAYÚSCULAS de alto contraste:** blanco + palabra clave en AMARILLO con contorno ROJO de peligro.
- **Producto grande resolviendo la amenaza** (ondas rojas hacia la plaga) + 3 insignias + franja inferior con CTA.

**Guardarraíles OBLIGATORIOS (no negociables):**
- **Compliance igual:** "AHUYENTA / ALEJA / MANTIENE ALEJADAS", NUNCA "elimina / mata / acaba con". Sin timelines
  imposibles. El choque es VISUAL, no una promesa médica exagerada.
- **NO copiar la huella de la competencia:** jamás subir su imagen tal cual (Meta la detecta por huella de
  contenido y sube los CPM en silencio — baneo Andrómeda). El render es PROPIO, con tu marca, composición y
  paleta distintas, y se **varía en cada copia** (cada uno de los ~2 agresivos único entre sí).
- **Calidad:** que no parezca IA (sin deformidades, texto legible). Choque ≠ mala calidad.
- **Marca visible arriba** (misma jerarquía marca→hook→producto→beneficio→CTA que el resto).

> El resto del PROMPT MAESTRO se rellena igual; para la variación agresiva, elegir el ESTILO "e-commerce viral"
> u "oscuro de lujo/dramático" y cargar el hook de choque en el HOOK VISUAL.

---

## ⚠️ CUÁL PROMPT USAR SEGÚN LA FASE (leer antes de generar nada)

| | FASE 1 — TESTEO | FASE 2 — ESCALADO |
|---|---|---|
| Qué se mide | el **ÁNGULO** | el **CONCEPTO** |
| Qué varía entre conjuntos | solo el hook y el dolor | el concepto visual completo |
| Qué está FIJO | **el concepto y el layout: idénticos en los 6** | el ángulo (el ganador) |
| Prompt a usar | **PROMPT DE CONTROL — FASE 1** (abajo) | **PROMPT MAESTRO** + los 15 estilos |
| Estilo anti-fatiga | ❌ **NO rotar** — rotar destruye la medición | ✅ rotar siempre |

> **Los 15 estilos anti-fatiga son de FASE 2.** En FASE 1 rotar el estilo entre los 6 conjuntos hace que cada conjunto varíe ángulo **y** ejecución visual a la vez: cuando uno gana no se puede saber cuál de los dos ganó. Con Andrómeda el creativo explica ~56 % del resultado, así que la ejecución visual pesa **más** que el ángulo — y si las dos se mueven juntas, el testeo no mide nada. (Decisión 19-ago, tras el catálogo de conceptos.)

---

## PROMPT DE CONTROL — FASE 1 (el mismo para los 6 conjuntos)

> **Concepto fijo: `C2_BENEFICIOS`, variante LIGERA.** Dueño de la definición: `Ads/_SWIPE/_CATALOGO_CONCEPTOS.md`.
> **Por qué esta variante y no la densa:** el hook tiene que dominar el creativo porque el hook ES el ángulo que se está midiendo. La variante densa (5 síntomas + 3 mecanismos + 6 badges + escalera de precios) lo entierra bajo veinte elementos.
> **Referencia visual de acabado:** `Ads/_SWIPE/_BANCO_CREATIVOS/C2_BENEFICIOS/ligera__Camila-Recomienda__15_1364693855873597.jpg` (Oftalmiel). Elegido entre 4 finalistas por el operador el 19-ago: es el único que deja el hook sin competencia, usa íconos vectoriales (sirve para problemas invisibles como tinnitus o insomnio, donde no hay foto del síntoma) y se reproduce 6 veces cambiando solo texto. Descartados: collage de síntomas y presentación densa (diluyen el ángulo mostrando 4-5 problemas a la vez), progresión (su dispositivo dominante no cambia entre ángulos).
> **Evidencia:** C2 es el concepto más transversal del mercado GT — **23 anunciantes distintos** sobre 133 creativos auditados, y **6 de cada 7** nombran el problema en la imagen (la proporción más alta del catálogo). El creativo C2 más longevo del banco lleva **197 días** activo y es exactamente esta variante ligera, sin precio.

**REGLA DE USO:** se genera **una sola vez por producto** y se reutiliza para los 6 conjuntos cambiando **únicamente** los 4 campos marcados `↻ CAMBIA POR ÁNGULO`. Todo lo demás —layout, paleta, tipografía, posición de los elementos, badges, franja— queda **idéntico en los 6**. Si un ángulo "pide" otra composición, se ignora: esa es justamente la variación que arruina el testeo.

```
Actúa como director de arte senior especializado en creativos de e-commerce para Meta Ads en
Latinoamérica. Vas a producir UNA pieza de una serie de 6 que deben verse como hermanas: misma
plantilla, mismo acabado, mismo mundo visual. Lo único que cambia entre ellas es el texto.

Formato: 1080x1350 px (4:5), vertical, feed de Facebook e Instagram.
Calidad: fotografía de producto de estudio, nivel catálogo de farmacia premium. NO debe parecer
generado por IA: sin texto deformado, sin manos raras, sin brillos plásticos, sin viñeteado falso.

[ADJUNTO: FOTO DEL PRODUCTO]
Reproducí el producto EXACTAMENTE como está en la foto adjunta: misma etiqueta, mismos colores,
mismo tipo de envase, mismas proporciones. No rediseñes el empaque ni inventes texto sobre él.

════════════════════════════════════════════════════════
MUNDO VISUAL (esto es lo que define la calidad — leelo entero antes de componer)
════════════════════════════════════════════════════════

FONDO: color crema/hueso muy claro derivado del tono más claro de la etiqueta del producto
(NUNCA blanco puro #FFFFFF — el blanco puro se ve barato y desaparece contra el feed).
Textura sutilísima de papel, sin degradados marcados ni destellos.

PALETA: extraída de la etiqueta del producto. Un COLOR PRINCIPAL (el dominante de la etiqueta),
un COLOR ACENTO (el más saturado, para íconos y detalles) y un NEUTRO OSCURO casi negro para
el texto. Tres colores, no más. Todo lo demás son variaciones de esos tres.

ILUMINACIÓN: luz suave de estudio desde arriba a la izquierda, difusa, tipo softbox grande.
Sombra propia del producto corta, suave y hacia abajo-derecha. Sin sombras duras ni
contraluces dramáticos.

════════════════════════════════════════════════════════
COMPOSICIÓN — 5 zonas, de arriba hacia abajo
════════════════════════════════════════════════════════

【1】 EYEBROW (banda superior, centrada)
Texto en MAYÚSCULAS pequeñas, gris oscuro, con letterspacing amplio (tracking generoso),
separado por un punto medio "·". Acompañado a izquierda y derecha por un pictograma diminuto
del ingrediente principal, en línea fina.
    → TEXTO: "[CATEGORIA] · [DESCRIPTOR_PRODUCTO]"

【2】 SELLO DE GARANTÍA (esquina superior derecha, sobre el eyebrow)
Sello CIRCULAR de unos 130px de diámetro, en COLOR ACENTO con acabado metalizado mate
(dorado/bronce si la paleta es cálida, plata azulada si es fría). Borde doble: un aro exterior
fino y otro interior. Adentro, en 2 líneas: el número grande arriba y "DÍAS DE GARANTÍA" abajo
en letra pequeña espaciada. Tres estrellitas diminutas coronando el número.
    → TEXTO: "[N] DÍAS DE GARANTÍA"

【3】 HOOK (zona superior, ocupa a lo ancho, alineado a la izquierda)
EL ELEMENTO MÁS GRANDE DE TODA LA PIEZA. Tipografía sans serif condensada, muy bold,
en el NEUTRO OSCURO. Máximo 2 líneas, interlineado ajustado (0.95). Una sola palabra o
frase corta va en COLOR ACENTO para quebrar el bloque — la palabra que carga la emoción,
no un sustantivo cualquiera. Es una PREGUNTA sobre el problema del lector.
    → TEXTO: "[HOOK]"

【4】 CUERPO — dos columnas que conviven

  4A. COLUMNA DE BENEFICIOS (izquierda, ~42% del ancho)
  Exactamente 4 filas, con aire generoso entre ellas. Cada fila:
     · Ícono LINEAL (solo trazo, sin relleno, grosor uniforme de 2px) dentro de un círculo
       de borde fino en COLOR ACENTO, fondo transparente. Diámetro ~70px.
       Estilo del ícono: minimalista, geométrico, tipo interfaz — NUNCA una foto,
       NUNCA un emoji, NUNCA un ícono 3D.
     · A la derecha del círculo: TÍTULO en mayúsculas, bold, neutro oscuro, 2-4 palabras.
     · Debajo del título: BAJADA de una sola línea, gris medio, tamaño 60% del título.
    → LOS 4 BENEFICIOS: [BENEFICIOS]

  4B. PRODUCTO (derecha, ~58% del ancho) — EL PROTAGONISTA
  El producto grande, nítido, ocupando su zona de arriba a abajo, ligeramente en diagonal
  o de frente según su forma. Si tiene caja, la caja atrás y el envase adelante, superpuestos.
  Apoyado sobre un PEDESTAL circular bajo, de madera clara o piedra mate, que lo levanta del fondo.
  Alrededor de la base, 2 o 3 PROPS del ingrediente principal, frescos y reales, colocados con
  naturalidad (nunca simétricos, nunca flotando): [PROPS].
  Detrás, muy desenfocado y a baja opacidad, una textura orgánica del mismo ingrediente.
  NADA de texto encima del producto.

【5】 PIE — dos franjas

  5A. BLOQUE DE PRECIO (esquina inferior izquierda) — [INCLUIR SOLO SI ESTE AD LLEVA PRECIO]
  Caja rectangular en NEUTRO OSCURO con borde fino en COLOR ACENTO.
  Arriba, en letra pequeña sobre fondo acento: "OFERTA POR TIEMPO LIMITADO".
  Debajo, el precio GIGANTE en blanco, con los centavos en tamaño menor y elevados.
  Al lado derecho, caja separada del mismo alto: la cantidad ("1 FRASCO" grande y "1 UNIDAD"
  chico debajo en una píldora de color acento).
  Bajo el precio, en gris claro y TACHADO con una línea fina: "PRECIO NORMAL: [PRECIO_TACHADO]".
    → [BLOQUE_PRECIO]

  5B. FRANJA DE CONFIANZA (al pie, ancho completo, fondo crema apenas más oscuro que el fondo)
  3 celdas de igual ancho, separadas por filetes verticales finos. Cada celda:
  ícono lineal a la izquierda (camión / mano con billete / bandera de Guatemala) +
  a la derecha TÍTULO bold en mayúsculas y bajada gris de una línea.
    · "ENVÍO GRATIS" / "a toda Guatemala"
    · "PAGO CONTRA ENTREGA" / "pagás cuando lo recibís"
    · "PRODUCTO DISPONIBLE" / "en Guatemala"

════════════════════════════════════════════════════════
TIPOGRAFÍA
════════════════════════════════════════════════════════
Una sola familia sans serif en toda la pieza, con 3 pesos: Black para el hook, Bold para los
títulos, Regular para las bajadas. Categoría tipográfica aproximada a la de la etiqueta del
producto. Nada de serifas, nada de scripts, nada de fuentes decorativas.
Tamaño mínimo legible en celular. Jerarquía sin ambigüedad: hook >> títulos > bajadas > legales.

════════════════════════════════════════════════════════
REGLAS DURAS
════════════════════════════════════════════════════════
· El HOOK es el elemento más grande. Nada compite con él.
· Máximo 4 beneficios. Si sobra espacio, se deja aire, NO se agrega un quinto.
· Texto total < 20% del área de la imagen.
· Un solo problema por pieza. No listar varios síntomas.
· Sin fotos de personas. Sin rostros. Sin antes/después.
· Sin logos de terceros, sin sellos de organismos reales (FDA, INVIMA), sin banderas de países
  que no sean Guatemala.
· COMPLIANCE: prohibido "cura", "trata", "elimina", "acaba con". Prohibido prometer plazos.
  Prohibida la urgencia de pánico. Se habla del problema del lector; NO se afirma curarlo.
  [Si el ángulo es médico sensible: usar "apoya / ayuda a la función / cuidado".]

════════════════════════════════════════════════════════
ENTREGA
════════════════════════════════════════════════════════
Una sola imagen 1080x1350. Ningún elemento cortado por el borde. Márgenes de seguridad de 60px.
```

**Los 4 campos que cambian por conjunto** — todo lo demás se copia y pega:

| Campo | Fuente |
|---|---|
| `[HOOK_DEL_ANGULO]` | `etapa-2`, ficha del ángulo (en forma de **pregunta**) |
| los 4 beneficios | `etapa-2` + `etapa-1b` (BANCO DE DOLOR REAL, en palabras del cliente) |
| props del producto | derivados del ingrediente que ese ángulo destaca |
| `[AVATAR]` | `etapa-2`, ficha del ángulo |

> **Sello starburst en FASE 1:** solo en los conjuntos que llevan precio (regla máx 3/6, ideal 2/6), y **siempre en la misma posición y tamaño** en los que lo lleven. Es una variable más que hay que mantener constante entre creativos que la comparten.

---

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
- PAÍS/MERCADO: Guatemala
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

## LOS 15 ESTILOS ANTI-FATIGA — **SOLO FASE 2** (no repetir estilo en ads consecutivos)

> ⛔ **No usar en FASE 1.** En el testeo el estilo es fijo (ver PROMPT DE CONTROL arriba). Rotar acá destruye la atribución del ángulo.

1. Minimalista premium · 2. Ecommerce viral · 3. Dermocosmético elegante · 4. Fondo tropical ·
5. Oscuro de lujo · 6. Laboratorio/clínico · 7. Tienda online · 8. Collage de beneficios ·
9. Lifestyle con persona real · 10. Textura natural · 11. Degradado moderno · 12. Composición diagonal dinámica ·
13. Dividido problema/beneficio (no antes/después corporal) · 14. Editorial de marca · 15. Enfoque en oferta.

---

## HOOK VISUAL

**Fórmula del hook viral (Clase 14 + PDF Mercy):** PROBLEMA REAL + BENEFICIO DESEADO + CURIOSIDAD. Al menos un elemento (hook, producto o precio) debe generar curiosidad — meta: que el avatar piense *"no sabía que lo necesitaba, pero ahora lo necesito"*.

**Enfoques válidos (elegir 1, basado en el ángulo):**
Dolor del cliente · Deseo aspiracional · Curiosidad · Resultado esperado · Oferta irresistible ·
Problema cotidiano · Transformación visual (no corporal bilateral) · Urgencia · Prueba social · Beneficio emocional.

Estructuras de hook: "¿Sentís que [problema]?" · "Esto es lo que necesitás si [dolor]" ·
"Más [beneficio], menos [problema]" · "[N] de cada 10 [avatar] no saben que [revelación]".

---

## MAPA DE VARIABLES POR FUENTE
- **ETAPA-1 / ETAPA-1B** → `[NOMBRE_PRODUCTO]` `[DESCRIPCIÓN_PRODUCTO]` `[POTENCIA]`
- **ETAPA-2** → `[BENEFICIO_ANGULO]` `[DOLOR_AVATAR]` `[AVATAR]` `[HOOK_DEL_ANGULO]`
- **ETAPA-2** (`<pagina_asignada>`) → `[TONO_IDENTIDAD]` `[COLOR_ACENTO]`
- **Imagen del producto** → colores derivados de la etiqueta
- **Operador / sistema** → `[N]` clientes (prueba social, regla de datos de ETAPA-4) · `[P1u]` solo si el ad lleva precio (regla de precio Guatemala: máx 3/6, ideal 2/6)

---

## CONEXIÓN
- ETAPA-4 lee este archivo para generar los ad-imagen de testeo (FASE 1: ángulos vírgenes; FASE 2: banco anti-fatiga).
- ETAPA-6 ubica cada ad-imagen en su conjunto, marcando "Formato: IMAGEN (Prompt Maestro)".

---

## ELEMENTOS EXTRA DEL AD-IMAGEN (validados operador 10-jul + mentores Clase 4/14/19)

> Estos dos elementos se suman a la jerarquía del Prompt Maestro. Nacen de la práctica del operador (que ya le funcionaba) confirmada contra las clases. Aplican a TODO producto.

### (A) SELLO DE OFERTA COMO EMPUJÓN DE CTR — también en ads SIN precio
El sello starburst (punto 7) NO es solo para los 2-3 ads con precio: sirve como **empujón de oferta/urgencia** en más creativos porque sube el CTR (el "último empujoncito" antes de comprar). Reglas:
- **Moderado** (chico, esquina, no tapa el producto, texto total < 20%) — nunca grande.
- **Sin pánico**: "SÚPER OFERTA / OFERTA ESPECIAL / PROMO / SOLO HOY" sí; "última oportunidad / se acaba ya / antes de que se agote" NO (sube CPM por baneo silencioso Andrómeda).
- **Variado en cada ad** (posición/texto distintos — Meta penaliza creativos idénticos).
- **Calibrado por emoción del ángulo**: en ángulos de dolor/urgencia va el sello de oferta; en ángulos tiernos/esperanza (ej. "me dijeron que no tiene cura") se usa un **sello de PRUEBA SOCIAL** ("+7,000 personas…") en vez de urgencia, para no cheapear el tono.
- En combo/2x1 el sello dice "MEGA OFERTA 2X1 / SOLO HOY" (igual que el lavado de video). En oferta 1/2/3 → "SÚPER/MEGA OFERTA · SOLO HOY".

### (B) TESTIMONIO DENTRO DEL AD-IMAGEN (prueba social visual)
Clase 4: "imágenes de testimonios + producto en la misma imagen dan muy buenos resultados"; Clase 14/19: la estructura ganadora lleva PRUEBA DE CONFIANZA (testimonio/reseña). Cómo aplicarlo:
- **Banner tipo burbuja de chat de WhatsApp** (o tarjeta de reseña con 5 estrellas) PEQUEÑA en la parte inferior.
- **Congruente con el ángulo del ad** (un testimonio distinto por ángulo: de sueño en el ad de "no dormir", del doctor en el de "no tiene cura"). Refuerza el avatar Y mantiene cada creativo único.
- **El testimonio ABSORBE el bloque de prueba social** (reemplaza los badges "+N clientes"), no se suma encima → controla el < 20% de texto. Prioridad: hook · producto · beneficio corto · testimonio · sello oferta chico · CTA.
- **Compliance del testimonio (es AD, Meta lo lee)**: experiencia subjetiva, SIN "me curó", sin números clínicos inventados. "Llevaba 2 años sin dormir, hoy descanso" ✅ · "me curó en 7 días" ❌.

---

## DOCTRINA DE CREATIVOS (VIDEO vs IMAGEN) — regla de asignación

> Movida desde `CLAUDE.md` el 31-jul-2026. **Este archivo es el dueño.** `etapa-2` y `etapa-6` la citan como "DOCTRINA DE CREATIVOS del sistema" y leen el detalle de acá.
>
> "Sistemático" = regla de decisión consistente, **NO** formato uniforme. La asignación es determinista y se aplica igual a todo producto.

**Los ~21 videos por producto cumplen DOS roles:**
1. **DATA primero** — `etapa-0`/`1b`/`2`/`3a` los minan para ángulos, hooks, lenguaje UGC real, señales de compra y objeciones (incluso los videos NO usados como anuncio enriquecen el análisis).
2. **ACTIVO segundo** — los mejores que calzan un ángulo se vuelven el creativo de ese conjunto (UGC validado y gratis; Andrómeda premia el watch-time).

**REGLA DE ASIGNACIÓN (FASE 1, por ángulo) — determinista:**
- Si un video seleccionado en `etapa-0` calza el ángulo → **creativo = VIDEO** (ese archivo).
- Si es ángulo descubierto/virgen sin video → **creativo = IMAGEN** (Prompt Maestro de este archivo).
- **NUNCA pausar ni descartar un ángulo por falta de video.** La imagen lo cubre y se lanza igual.
- FASE 1 = **1 creativo por conjunto** (lean). No generar espejos.

**ESCALADO (FASE 2):** el ángulo ganador se escala con **banco de imágenes anti-fatiga** (50+, los 15 estilos de este archivo) + se **replica el video ganador vía Post ID** (si ganó un video). Acá las imágenes dominan por volumen — no se hacen 50 videos. El banco se organiza además por **ROL DE EMBUDO (TOFU/MOFU/BOFU)** mapeado al nivel de conciencia de `etapa-2`, para alimentar el embudo interno de la CBO (ver `etapa-4` FASE 2 · `DOCTRINA/ESCALADO_PLAYBOOK.md` §4). **Solo FASE 2** — FASE 1 se mantiene lean.

**Nota de lectura (confound de formato):** mezclar video e imagen entre conjuntos mete un sesgo leve (un video validado es un creativo más fuerte que una imagen fría). Mitigación: leer FASE 1 a nivel de **ÁNGULO** con las métricas de conversación (robustas al formato); si los 2 mejores ángulos quedan a <15% entre sí y difieren en formato, FASE 2 los controla probando el ganador en un solo formato. No sobre-optimizar esto en FASE 1.

> **Decisión del operador (22-sep-2026):** este confound ya no puede ocurrir en F1 — los 6
> conjuntos declaran `formato: IMAGEN` fijo (`gen_plan.py --validar` bloquea cualquier otro). La
> nota queda como antecedente histórico de por qué se tomó la decisión.

**Variación AGRESIVA / de impacto** (palanca validada por data de competencia — ver "ENFOQUE AGRESIVO / DE IMPACTO" arriba): en categorías de plaga/miedo/higiene, el creativo de CHOQUE frena el scroll más fuerte que el limpio. Regla: **1-2 de los 6 conjuntos por lanzamiento** la usan (preferente el genérico/amplio + un ángulo de MIEDO), NUNCA los 6 — se mantiene el "1 creativo por conjunto" lean y la diversidad de conceptos y entrega. Guardarraíles: compliance "ahuyenta/aleja" (no "elimina/mata"), render propio y único (no copiar la huella de la competencia = baneo silencioso). `etapa-4` la aplica en su Tarea 2.

**Dos sistemas de creativo distintos (no confundir):**
- **(a) ADS DE TESTEO** = video lavado o imagen Prompt Maestro (este archivo) que van en la campaña de Meta.
- **(b) INFOGRAFÍAS DEL BOT** = 3 imágenes informativas dentro del flujo de WhatsApp (Info 1 beneficios, Info 2 modo de uso/ingredientes, Info 3 confianza) + IMAGEN 4 anti-imitación opcional, todas de `DOCTRINA/PLANTILLAS_INFOGRAFIAS_FLUJO.md` y `DOCTRINA/PLANTILLAS_INFOGRAFIAS_OPCIONALES.md`, sobre el motor compartido de `DOCTRINA/PLANTILLAS_INFOGRAFIAS.md`.
