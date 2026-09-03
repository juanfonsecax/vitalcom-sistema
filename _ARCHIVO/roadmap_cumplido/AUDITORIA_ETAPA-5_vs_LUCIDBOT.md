# AUDITORÍA — Lo que pide LucidBot vs. las clases vs. ETAPA-5

**Objetivo:** que ETAPA-5 entregue un producto **100% listo para pegar en LucidBot**, sin que vos tengás que rellenar nada a mano.
**Regla de validez usada:** clase con número mayor = más reciente = manda. SKOOL 2026 solo cuando ninguna clase lo contradice.
**Fuente del bot viejo:** el flujo "Sanarte / Clearstem / SELERB" que pasaste.

---

## VEREDICTO RÁPIDO

ETAPA-5 **ya cubre ~85%** de lo que pide LucidBot. Los 4 campos de ficha existen, las 5 interacciones existen, casi todas las reglas existen. Pero hay **2 errores reales** (uno tuyo del bot viejo, uno de ETAPA-5) y **3 huecos** que hacen que el producto no salga 100% listo:

| # | Hallazgo | Quién está mal | Severidad |
|---|---|---|---|
| 1 | Temporizador de **15 segundos** entre mensajes | tu bot viejo | 🔴 Alta |
| 2 | El **nombre de la asesora se revela ANTES del audio** (ELEMENTO 11) | ETAPA-5 | 🟠 Media |
| 3 | Falta la **regla de "no tenemos tienda física / centro de distribución"** | ETAPA-5 (hueco) | 🟠 Media |
| 4 | Regla "no repetir >2 veces" sin **escalera de re-enfoque** | ETAPA-5 (incompleto) | 🟡 Baja |
| 5 | Defensa de precio sin el framing **"2ª unidad a mitad de precio"** | ETAPA-5 (mejorable) | 🟡 Baja |

Los 4 campos de catálogo **sí los das** — abajo te confirmo qué dice cada clase para escribirlos bien.

---

## PARTE A — LOS 4 CAMPOS DE LA FICHA DE LUCIDBOT

Estos son los 4 campos que pegás en la **ficha de producto de Lucid** (donde conectás el producto con la campaña de Meta para que trackee). ETAPA-5 **ya los produce** en el BLOQUE J con la nota "se pegan tal cual". Lo que faltaba era que supieras **qué dice la clase para llenar cada uno** — acá está, ordenado por recencia:

### 1. DESCRIPCIÓN
- **Qué manda:** Clase 22 (la más reciente de flujo) + Clase 1.
- **Cómo debe ser:** fórmula **problema + solución + resultado deseado**, emocional, en voseo. Congruente con el dolor que pautaste en Meta (si la ficha dice algo distinto al anuncio → **efecto rebote, se sale** — Clase 22, Bloque 3).
- **Prohibido:** "suplemento natural con múltiples beneficios" (descripción genérica = mata percepción de valor).

### 2. MODO DE USO
- **Qué manda:** Clase 10 (líneas 80, 197, 246).
- **Cómo debe ser:** vender **FACILIDAD** y en **DÍAS, no meses**. "Solo 2 cápsulas a la misma hora." Clase 10: *"prometer modo de uso engorroso"* mata la venta. Clase 12/10: "12-16 días se percibe fácil; 6-10 meses, eterno".

### 3. CARACTERÍSTICAS TÉCNICAS
- **Qué manda:** Clase 22 (Bloque 9) + Clase 10.
- **Cómo debe ser:** **encabezar con BENEFICIOS** (la percepción de valor), NO con ingredientes. Joaquín pone **10-20 propuestas de valor** antes de la lista técnica ("entró por glúteos, pero también: curvas, busto natural, energía, uñas fuertes…"). Recién al final, ingredientes con su mecanismo en 1 línea (los interesados sí quieren saber qué contiene).
- **Fórmula de cada propuesta:** Problema + Solución + Resultado deseado (Clase 22, Bloque 5).

### 4. CONTENIDO DEL PAQUETE
- **Qué manda:** Clase 22 + Clase 17 + Clase 10.
- **Cómo debe ser:** framing **"tratamiento de ~X días"** + cantidad concreta para subir percepción de valor ("180 cápsulas", "tratamiento de 40 días"). Clase 17/10: **nunca liderar con "1 frasco $X"** — el cliente paga la transformación, no el envase.

> **Conclusión Parte A:** ETAPA-5 ya entrega los 4 campos bien calibrados. No es un hueco — es que no sabías que ya estaban. ✅ Lo único: asegurate de que en el output salgan **rotulados exactamente** con los nombres de Lucid (Descripción / Modo de uso / Características técnicas / Contenido del paquete) para copiar-pegar sin pensar. Hoy ya salen así.

---

## PARTE B — EL MENSAJE INICIAL (la secuencia)

Contraste de las tres fuentes:

| Paso | Tu bot viejo | Las clases | ETAPA-5 hoy |
|---|---|---|---|
| Saludo | "Bienvenido a Sanarte… asesora se pondrá en contacto ✨" | SKOOL §33: saludo SIN nombre de asesor | ELEMENTO 1 ✅ igual |
| **Espera** | **15 segundos** | **SKOOL §128 / Clase 22: 2-3 seg** | 2-3 seg ✅ |
| Videos | 2 | Clase 1: 1-2 (autoridad + UGC) | 2 ✅ |
| Infografías | 2-3 | Clase 1: 3 · SKOOL: 1-3 | 1-3 ✅ |
| Transición | "te comparto testimonios 👇🏼" | Clase 1: texto divisorio | ELEMENTO 7 ✅ |
| Testimonios | 2 | Clase 1: 2-4 | 2-4 ✅ |
| Audio | sí (paso 7) | Clase 10: 45-55 seg, SIN precio | ELEMENTO 12 ✅ |
| Nombre asesora + ciudad | **después del audio** (paso 8) | **SKOOL §33/§100: en el AUDIO, al final** | **ELEMENTO 11, ANTES del audio** ❌ |

### 🔴 Hallazgo 1 — El temporizador de 15 segundos (error de tu bot viejo)
Tu bot esperaba **15 segundos**. La doctrina es clara: **2-3 segundos** entre mensajes (SKOOL §128; Clase 22, Bloque 7). El motivo es brutal: *"cuando la persona se sale de tu flujo, Meta la bombardea con publicidad de tu competencia y termina comprando ahí"* (Clase 22). 15 segundos de silencio = ventana para que se vaya.
**Cómo debe ser:** timer en **2-3 seg**. Si querés simular que "una asesora está llegando", como mucho **5 seg en ESE primer beat**, nunca 15, y nunca 15 entre cada elemento.

### 🟠 Hallazgo 2 — Cuándo se revela el nombre de la asesora (error de ETAPA-5)
Tu bot viejo lo hace bien: audio (paso 7) → **luego** "Hola, soy Laura…" (paso 8). El nombre aparece **al final**, que es justo lo que mandan SKOOL §33 y §100: *"el nombre del asesor se revela en el AUDIO, no al inicio — refuerza que un humano tomó la conversación."*

**ETAPA-5 hoy se contradice a sí misma:** el ELEMENTO 1 dice "el nombre aparece hasta el 11/12", pero el **ELEMENTO 11 ya lo revela** ("Hola! Soy [NOMBRE]…") **antes** del audio. Eso rompe la doctrina.

**Cómo debe ser (elegí una):**
- **Opción A (la de tu bot viejo, recomendada):** ELEMENTO 11 = puente SIN nombre ("Te dejo un audio para explicarte mejor 🎧") → audio → y el nombre aparece en un texto **después** del audio + la pregunta de ciudad ("Hola, soy Laura, te atiendo hoy 😊 ¿desde qué municipio nos escribís?").
- **Opción B:** ELEMENTO 11 sin nombre, y la asesora **se nombra dentro del audio** (como hace Mercy).

En ambas, el nombre **nunca** aparece antes del audio.

---

## PARTE C — LAS REGLAS

| Regla de tu bot | ¿La tiene ETAPA-5? | Qué dicen las clases | Acción |
|---|---|---|---|
| **R1** ciudad→cobertura→precios→reconfirmar ciudad→datos | ✅ Sí (Interacciones 0-3) | Clase 1: sí encadenado, 2º sí = ciudad | OK |
| **R2** "centro de distribución, no atención al público" | ❌ **NO** | operativa estándar | **AGREGAR** |
| **R3** si ya mandó datos, no re-preguntar, solo confirmar | ✅ Sí | Clase 1: no mostrar afán | OK |
| **R4** no re-preguntar qué producto quiere | ✅ Sí | — | OK |
| **R5** no repetir misma pregunta >2 veces | ⚠️ Parcial | Clase 1 | **Mejorar:** agregar escalera de re-enfoque |
| **R6** no bajar precio de 1u; recomendar 2u | ⚠️ Parcial | Clase 17: no bajar margen del 1º; el combo/2ª da la motivación | **Mejorar:** framing "2ª a mitad de precio" |
| **R7** audios → "micrófono fallando" | ✅ Sí (textual) | — | OK |
| **RX** empaque discreto (condicional) | ✅ Sí (condicional) | — | OK |
| FAQs del web research | ✅ Sí (FAQ_VENTA desde [VOZ-REAL]) | Clase 1: revisar chats por preguntas frecuentes | OK |

### 🟠 Hallazgo 3 — Falta la regla de "no tenemos tienda física"
Tu bot la tiene; ETAPA-5 **no**. Es una pregunta real y frecuente ("¿dónde están?, ¿puedo pasar a recoger?"). Hay que agregarla como regla estándar:
> *[IMPORTANTE: Si el cliente pregunta por ubicación/tienda física: "Nuestro centro de distribución trabaja solo por envíos y no tenemos atención al público. Hacemos entregas a casi toda Guatemala por GINTACOM y FORZA, según cobertura."]*

### 🟡 Hallazgo 4 — Escalera de re-enfoque en R5
ETAPA-5 dice "no insistir >2 veces" y avanzar. Tu bot es más fino: **cambia el enfoque cada vez** en lugar de solo callarse. Mejor:
> 1ª vez: "Decime tu municipio para confirmarte cobertura."
> 2ª vez: "Con tu municipio te confirmo si te llega con **pago contraentrega**." (re-enfoque hacia el beneficio)
> Después: cambiar de tema, no repetir.

### 🟡 Hallazgo 5 — Defensa de precio
ETAPA-5 defiende con "no manejamos descuentos, pero 2 unidades = envío gratis". Tu bot suma una palanca más fuerte alineada a Clase 17 ("no bajar el margen del primero; la 2ª da la motivación"):
> *"El precio de 1 unidad no lo puedo bajar. Pero si llevás 2, **la segunda te sale casi a mitad de precio** — te sale mucho más conveniente."*
Usalo **solo si la arquitectura de precios de ETAPA-1 lo soporta** (que P2u realmente deje ver ese ahorro).

---

## PARTE D — CAMBIOS CONCRETOS A ETAPA-5.md

Para que el sistema salga 100% listo, ETAPA-5 necesita estos 4 ajustes (en orden de impacto):

1. **Fijar timer 2-3 seg explícito en el output** (ya está como nota; subirlo a instrucción dura y advertir: nunca 15 seg). — Cierra Hallazgo 1.
2. **Corregir el ELEMENTO 11:** quitar el nombre de la asesora del puente; moverlo al audio o a un texto post-audio junto a la pregunta de ciudad. — Cierra Hallazgo 2 (y la contradicción interna).
3. **Agregar la regla "no tienda física"** al bloque REGLAS DEL BOT. — Cierra Hallazgo 3.
4. **Reforzar R5 (escalera de re-enfoque) y R6 (2ª a mitad de precio)** en el bloque de reglas. — Cierra Hallazgos 4 y 5.

Ninguno toca la arquitectura de 13 elementos + 5 interacciones — son ajustes quirúrgicos.
