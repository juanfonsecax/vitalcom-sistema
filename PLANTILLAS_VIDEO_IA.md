# PLANTILLAS_VIDEO_IA — PRODUCCIÓN DE VIDEO UGC CON IA (BORRADOR)

> ⚠️ **ESTADO: BORRADOR — NO INTEGRADO AL FLUJO.** Este archivo existe para que Juan lo refine. **Ninguna etapa lo lee todavía.** No está cableado a la DOCTRINA DE CREATIVOS ni a ETAPA-4/ETAPA-6. La integración (que un ángulo pueda salir como VIDEO-IA en vez de imagen) queda para **después**, y va **junto con el P3 (fanpage/personaje-marca honesto)** — si se crea una fanpage con un personaje, ese personaje necesita contenido de video IA, por eso ambos van conectados.
>
> Origen: análisis del mentor de moda/IA (`_ROADMAP/ANALISIS_MENTOR_JULI_vs_SISTEMA_2026-07-03.md`, §3.1). Aquí se destila SU pipeline y se le pone encima **el compliance de salud/COD del sistema** (que el mentor, al vender moda, no necesita).

---

## 0. PARA QUÉ SIRVE (cuando se integre)

Hoy el sistema tiene dos fuentes de creativo (DOCTRINA DE CREATIVOS en CLAUDE.md):
- Ángulo con video que calza → **video minado** de la biblioteca (ETAPA-0).
- Ángulo virgen sin video → **imagen** (Prompt Maestro de `PLANTILLAS_ADS.md`).

Este pipeline abre una tercera fuente: **producir video UGC propio con IA**, para que un **ángulo virgen** ya no se conforme con imagen fría, sino que salga como **video UGC** (Andrómeda premia el watch-time). También sirve para el **banco del ángulo ganador en FASE 2** (donde se justifica producir 10-40 creativos).

> **Dónde entraría (propuesta, no decidida):** primero como opción en FASE 2 (ángulo ganador, alto valor), y solo después —si el CPA lo justifica— en ángulos vírgenes de FASE 1. No usar en los 6 conjuntos de testeo por defecto: cuesta créditos y tiempo.

---

## 1. EL PIPELINE (destilado del mentor)

**Paso 1 — Rostro base (Pinterest).** Buscar un rostro real como REFERENCIA (no usarlo directo). Query específico del avatar: "mujer guatemalteca 40 años rostro natural", "hombre 50 años cercano luz natural". Sacar captura.

**Paso 2 — JSON de rostro (Gemini).** Un chat que recibe la foto de referencia y devuelve **prompts JSON** para generar rostros NUEVOS (evita usar la cara de otra persona y da variación). Ver plantilla de chat en §3-A.

**Paso 3 — FRAME INICIAL (lo más importante — 80% del realismo).** La **primera foto** y su **iluminación** definen si el video se ve real o "plástico/IA".
- **Regla dura: "luz natural de día".** La luz artificial es lo que delata a la IA. Pedir siempre "luz natural entrando por la ventana", "luz de sol en el rostro".
- Generador: **Nano Banana** o **GPT-Image (ChatGPT imagen)**.
- Encuadre: modelo de cintura para arriba, mirando/presentando el producto, "como tomada desprevenida" (UGC hiperrealista).

**Paso 4 — Video (de la foto inicial parte el movimiento).**
- Herramientas: **Kling** (vía PiAPI / "pmar" — créditos más baratos que Veo3), **Seedance** (el mejor para que la modelo muestre el producto sin deformarlo), **Higgsfield**.
- **Truco "mirad":** empezar cada prompt con la palabra **"mirad"** → fija acento español y evita el bug de ojos; se borra en edición. (Adaptar a voseo guatemalteco si la fanpage es local — ver compliance §2.)
- Dirigir el movimiento: que la modelo gesticule, se aleje/acerque, baje/suba el producto — **no quieta todo el video** (eso se ve IA).

**Paso 5 — Guion (Claude).** Un chat de Claude que **conoce el avatar a la perfección** (mismo avatar de ETAPA-2) genera hooks + guion UGC. Estructura: **identificación con el dolor primero → producto al final (~seg 45)**. Tono informal y local. Ver §3-B.

**Paso 6 — B-rolls.** Escenas lifestyle generadas (uso del producto, día a día) + b-rolls de refuerzo de identificación. El b-roll es lo que hace que la persona se sienta identificada.

**Paso 7 — Edición (CapCut).** Zoom con **curvas de easing** (no lineal), corte de frames, **subtítulos**, música, b-rolls intercalados en las frases clave. La edición sube la retención (= watch-time = Andrómeda).

---

## 2. OVERLAY DE COMPLIANCE — SALUD / COD (lo que el mentor NO necesita y NOSOTROS SÍ)

> El mentor vende moda: "no me marca la barriga" es inocuo. Nosotros vendemos **suplementos de salud** bajo Andrómeda. Estas reglas son **innegociables** y mandan sobre cualquier técnica de arriba:

- **Sin claims médicos:** prohibido "cura / trata / elimina [enfermedad]" y timelines imposibles ("en 7 días"). Usar "apoya / ayuda a / muchos notan que…", plazos creíbles ("desde la semana 2").
- **Testimonio de persona IA = terreno delicado.** Un rostro IA inventado afirmando que un suplemento le curó algo es **testimonio falso + claim médico** → riesgo de baneo y ético. Mantener el UGC en lenguaje de **apoyo y experiencia**, en 3ª persona cuando toque autoridad ("me lo recomendó mi médico"), sin afirmar resultado clínico.
- **Nada de "liquidación al cuello" ni urgencia agresiva** como gancho de video (el método de validación del mentor). En COD/Guatemala el cierre se apoya en **garantía + tratamiento + pago contra entrega**.
- **Voz/acento:** el truco "mirad" fija acento España. Para fanpages guatemaltecas, adaptar a **voseo guatemalteco** (TONALIDAD BASE del sistema) — no dejar acento español si la página es local.
- **Reglas Andrómeda del creativo siguen aplicando:** texto en imagen < 20%, sin antes/después corporal bilateral, que NO parezca IA (manos, texto, logos), marca visible, se vende en <3 seg.

---

## 3. CHATS-PLANTILLA (para armar una sola vez y reutilizar)

### 3-A · Chat "JSON de rostro" (Gemini)
> Sube una foto de referencia (Pinterest) y pide rostros nuevos en JSON.
```
Actúa como generador de prompts JSON para rostros hiperrealistas. Te adjunto una foto de referencia de un rostro. Devuélveme 3 prompts en formato JSON para generar rostros NUEVOS (no copies de este), coherentes con: [avatar: género, edad, rasgos guatemaltecos, expresión cercana]. Cada rostro: primer plano, luz natural de día, mirada a cámara, realismo tipo iPhone. Solo JSON, sin explicación.
```

### 3-B · Chat "Guion UGC" (Claude, alimentado con el avatar de ETAPA-2)
```
Sos experto en guiones UGC de alta conversión para [fanpage/tono]. Conocés a la perfección este avatar: [pegar avatar de ETAPA-2: dolor, deseo, miedo, frustración, emoción oculta, nivel de conciencia]. Escribí un guion UGC de [30-45] seg en voseo guatemalteco que: (1) abra con un HOOK de dolor/identificación en los primeros 3 seg; (2) haga sentir identificada a la persona con su situación actual ANTES de nombrar el producto; (3) introduzca el producto recién ~seg 45 como el vehículo; (4) cierre con CTA a WhatsApp con beneficio. COMPLIANCE: lenguaje de apoyo, sin "cura/trata/elimina", sin plazos imposibles. Dame además 5 hooks alternativos.
```

### 3-C · Chat "Prompt de frame inicial" (Nano Banana / GPT-Image)
```
Generá una imagen UGC hiperrealista: [avatar] en [escena cotidiana], LUZ NATURAL DE DÍA entrando por la ventana, sosteniendo/presentando [producto], mirada a cámara, encuadre de cintura para arriba, calidad tipo iPhone, sin apariencia de IA. La foto se siente tomada desprevenida.
```

### 3-D · Chat "Prompt de video" (Kling / Seedance)
```
mirad — [avatar] en la misma escena de la foto inicial. Analizá el diálogo: [pegar guion]. La modelo se mantiene en el lugar pero gesticula y mueve el cuerpo natural acorde al diálogo; que baje/suba el producto y no lo tenga siempre en la misma posición. Iluminación: solo luz natural de día. Se siente grabado con celular. Aspect ratio 9:16, duración [7-8] seg por escena.
```

### 3-E · Chat "B-roll lifestyle"
```
Prompt de video lifestyle a partir de esta foto: [subir imagen de escena/uso del producto]. Continuá el movimiento natural, luz natural de día, realista. Formato código para copiar/pegar.
```

---

## 4. LOS 15 ESTILOS DE ESCENA
Reutilizar la misma lista de estilos anti-fatiga de `PLANTILLAS_ADS.md` (minimalista premium, lifestyle con persona real, laboratorio/clínico, etc.) para variar las escenas y no fatigar.

---

## 5. PENDIENTES PARA REFINAR (Juan)
- [ ] Confirmar herramientas y costos reales (Kling/PiAPI vs Seedance vs Higgsfield; créditos/mes).
- [ ] Definir dónde entra: ¿solo FASE 2 ganador? ¿ángulos vírgenes FASE 1?
- [ ] Piloto: 1 video sobre un ángulo de un producto vivo (NusavaB12 o D3+K2) y comparar CPA vs la versión imagen actual. **Decisión por data, no por entusiasmo.**
- [ ] Definir cómo se conecta con P3 (fanpage/personaje-marca honesto) — un personaje de marca necesita este pipeline para su contenido.
- [ ] Recién con el piloto validado: cablear a la DOCTRINA DE CREATIVOS + ETAPA-4 + ETAPA-6 (subir VERSION del sistema).
