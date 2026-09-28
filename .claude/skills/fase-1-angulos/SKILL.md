---
name: fase-1-angulos
description: "FASE 1 — Pre-testeo. Orquesta la secuencia completa que convierte transcripciones de video en una campaña de testeo de 6 ÁNGULOS lista para lanzar: validar producto, clasificar creativos (los videos quedan como FUENTE del ángulo, no como el creativo), costear, minar voz del cliente, construir las 6 fichas de ángulo (etapa-2 también asigna la FanPage), escribir copies e infografías, construir el bot paraguas, planificar la campaña TODO EN IMAGEN y guardar el producto en disco. Úsala cuando flujo.py devuelve el nodo F1.paquete, o cuando el operador dice \"tengo transcripciones\", \"quiero lanzar un producto nuevo\", \"arrancar testeo\" o \"pre-testeo\"."
tools: Read, Write, Glob, Grep, Bash, Task
---

# FASE 1 — PRE-TESTEO (testeo de ÁNGULOS)

## Qué mide esta fase

**Mueve el ÁNGULO. Todo lo demás queda fijo.**

```
6 ÁNGULOS distintos × concepto Y FORMATO FIJOS (IMAGEN, C2_BENEFICIOS)   ← mide el ÁNGULO
```

**En FASE 1 los 6 ad-imagen comparten layout, paleta y estructura**; cambian solo hook,
beneficios, props y avatar. **NO se rotan los 15 estilos anti-fatiga** (son de FASE 2): si la
ejecución visual varía junto con el ángulo, nada es atribuible — y con Andrómeda el creativo pesa
~56 % del resultado, más que el ángulo. Eso no es iteración perezosa: 6 variantes del mismo
concepto son 6 creativos únicos para Meta, que detecta duplicados por huella de contenido, no por
estructura.

> **FASE 1 corre TODO EN IMAGEN.** Los videos de
> competencia que selecciona `etapa-0` siguen siendo la FUENTE del ángulo (transcripciones), pero
> ya no son el creativo de F1: los 6 conjuntos se lanzan con ad-imagen, igual para todos los
> ángulos. El lavado anti-copyright de video (`Ads/_TOOLS/lavar_videos.sh`) ya no corre en esta
> fase — se mueve a FASE 2 (skill `fase-2-conceptos`), donde el video se testea como un concepto
> más. Dueño de la regla: `Ads/_TOOLS/gen_plan.py --validar` bloquea un `_PLAN.json` de F1 con
> cualquier conjunto cuyo `formato` no sea `IMAGEN`.

**Secuencia:** `etapa-producto` → `etapa-0` → `etapa-1` → `etapa-1b` →
`etapa-2` (incluye la asignación de FanPage) → (`etapa-4` ∥ `etapa-5`) → `etapa-6` → `etapa-guardar-producto`

---

## PASO 0 — EL FLUJO DICTA

Esta skill se carga cuando `python Ads/_TOOLS/flujo.py [producto_key]` devuelve `F1.paquete`. Los
gates de entrada (`F1.congelar_inputs`: fila, costo, ≥6 transcripciones, media) y lo que cierra el
paquete están en `DOCTRINA/FLUJO.json`; si el runner dice BLOQUEADO, se produce lo que falta y se
vuelve a correr. Publicar y activar son nodos aparte (`F1.publicar` → skill `publicar-meta`).

---

## PASO −1 — CONGELAR INPUTS (obligatorio, antes de invocar cualquier etapa)

> **Por qué:** correr el flujo con inputs que cambian a mitad de camino (costo, dosis, página,
> proveedores) es lo que genera archivos que se contradicen entre sí. Se decide UNA sola vez y todo
> lo demás se deriva de aquí. Si un input cambia después → **rerun completo** que **sobrescribe**
> los archivos y sube `VERSION`, nunca un parche parcial.

El orquestador fija este bloque y lo repite textual al inicio de cada etapa. Si falta un campo
obligatorio → **detener** y pedirlo (no asumir ni inventar). Los obligatorios que viven en disco los
canta `flujo.py` (`F1.congelar_inputs`) antes de llegar acá:

```
━━━ INPUTS CONGELADOS — [PRODUCTO] · VERSION v1 · [FECHA] ━━━
PRODUCTO (nombre exacto):     [..]
COSTO_PROVEEDOR_Q:            [Q..]              ← define todo el costeo (ETAPA-1)
DOSIS / PRESENTACIÓN:         [ej. 5000 mcg · 1.5 ml sublingual]   ← valor único
PROVEEDORES_DROPY:            [N]
ANUNCIANTES_AD_LIBRARY:       [N o "no provisto"]
IMAGEN_PRODUCTO:              [sí/ruta]          ← obligatoria (análisis visual ETAPA-4/1B)
INGREDIENTES:                 [lista o "pendiente"]
TASA_USD_GTQ:                 [ej. 7.62]
MCP_ACCOUNT_ID / MCP_PAGE_ID / MCP_PIXEL_ID:  [si se creará campaña por MCP]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

> Obligatorios para arrancar: PRODUCTO, COSTO_PROVEEDOR_Q, DOSIS/PRESENTACIÓN, IMAGEN_PRODUCTO,
> ≥6 transcripciones. INGREDIENTES puede quedar "pendiente" hasta `etapa-1b`. Estos valores son la
> **única fuente de verdad** del producto.

### Entrega de transcripciones

**OPCIÓN 1 — Carpetas del proyecto (recomendada, ahorra tokens):**
- Videos descargados → `Ads/1.1 Videos/[PRODUCTO]/`
- Transcripciones `.txt` (generadas con `Ads/Prompt-Gemini.txt` en Gemini) →
  `Ads/1.2 Transcripcion videos/[PRODUCTO]/`
- Mismo nombre y número que el video (`5. NombreProducto.mp4` → `5. NombreProducto.txt`).
- `etapa-0` las detecta ahí automáticamente. El operador solo indica: producto, costo Q e imagen.

**OPCIÓN 2 — Texto en el chat:** pegar el contenido de cada transcripción, identificando cada video
así: `--- NOMBRE_DEL_VIDEO.txt ---`

> La imagen del producto **siempre** se entrega en el chat (adjunta o link) — requiere análisis
> visual (`etapa-4` Director de Arte y `etapa-1b`).
> Detalle de la fase manual de recolección en `DOCTRINA/ETAPA-RECOLECCION.md`.

> **MÓDULOS OPCIONALES DE INVESTIGACIÓN (`DOCTRINA/ETAPA-RESEARCH.md`):** antes de `etapa-0`, el operador
> puede pedir Módulo A (investigación web de ingredientes) o Módulo B (scraping Meta Ads Library,
> requiere APIFY_TOKEN). Si no los menciona, continuar normal (`etapa-1b` ya hace búsqueda web).

---

## PASO 0 — `etapa-producto` (validación del producto)

Corre SIEMPRE primero. Inputs: producto candidato, costo Q (si se tiene), datos de mercado
(proveedores Dropy, anunciantes Ad Library — opcionales).

- **Si NO APTO (rojo):** advertir qué criterio eliminatorio falló y preguntar si cambia de producto
  o continúa igual. No avanzar sin confirmación explícita.
- **Si APTO:** continuar.

### PRE-VALIDACIÓN antes de ETAPA-0

Las ≥6 transcripciones las exige `flujo.py` en `F1.congelar_inputs` (predicado `glob` sobre
`Ads/1.2 Transcripcion videos/[carpeta]/*.txt`). Si llegaron pegadas en el chat (OPCIÓN 2), el
orquestador las guarda primero en esa carpeta: el flujo solo cuenta lo que existe en disco.

---

## PASO 1 — `etapa-0` (selector de fuentes del ángulo)

Inputs: las N transcripciones TXT (de `Ads/1.2 Transcripcion videos/` o pegadas).
Output: tabla de clasificación + los 6 videos seleccionados por ángulo, como FUENTE del ángulo
(evidencia y ganchos para `etapa-1b`/`etapa-2`) — **no como creativo de F1**: el creativo de los 6
conjuntos es siempre ad-imagen (`etapa-4`). El video de cada ángulo queda disponible para su
concepto en FASE 2 (lavado con `Ads/_TOOLS/lavar_videos.sh` recién ahí, ver `fase-2-conceptos`).

---

## PASO 2 — `etapa-1` (costeo)

Inputs: nombre exacto del producto + costo del proveedor en Q.

> La tabla de costeo, la matriz de arquitectura de oferta y la **regla de arranque 1u vs 2x1** viven
> en `.claude/agents/ETAPA-1.md`. Nunca inventar cifras ni calcular múltiplos del costo. Si el costo
> cae entre dos filas, usar la fila superior (conservador).

Output: P1u, P2u, P3u, CPA Objetivo, CPA Break Even.

---

## PASO 2B — `etapa-1b` (componentes + VOZ DEL CLIENTE)

Inputs: nombre del producto, lista de componentes/ingredientes (operador), output de `etapa-0`.

- **Si falta la lista de ingredientes:** pedirla (empaque / ficha Dropy / sitio del fabricante). La
  etapa NO se bloquea: el minado de Voz del Cliente corre igual sobre el problema/categoría.
- **Siempre mina la VOZ DEL CLIENTE primero** (WebSearch en Reddit/foros/reseñas/blogs) — los
  ángulos se construyen sobre el dolor real de la gente, no solo sobre el beneficio teórico del
  ingrediente.

Output: BANCO DE DOLOR REAL ([VOZ-REAL]) + ángulos DESCUBIERTOS/CUBIERTOS. → se transfiere a
`etapa-2`.

**Después de `etapa-1b` (T10):** volcar cada frase [VOZ-REAL]/[DESEO-REAL] con URL a
`_VOZ_CLIENTE.csv` vía `python Ads/_TOOLS/verificar_voz.py --agregar-json hallazgos.json
--escribir`, y correr `python Ads/_TOOLS/verificar_voz.py --producto [PRODUCTO] --escribir`
para que verifique cada URL contra su cita antes de que `etapa-2` construya las fichas.

---

## PASO 3 — `etapa-2` (ángulos + asignación de FanPage)

Se invoca inmediatamente después de `etapa-1b`.

- **`etapa-2`** — Inputs: output de `etapa-0`, `etapa-1`, `etapa-1b` (ángulos descubiertos **+ BANCO
  DE DOLOR REAL**), componentes, nombre del producto, y `<datos_saturacion>` (opcional; si no se
  entrega, marca saturación DESCONOCIDA). Output: 6 fichas de ángulo rankeadas — cada una con su
  **clasificación medible** (`avatar_genero`, `avatar_edad`, `emocion_dominante`, vocabulario
  cerrado de `DOCTRINA/DATA_PLAYBOOK.md` §1) — más `<pagina_asignada>` (Formato A o B), resuelta
  contra `PRODUCTOS/_DIM_FANPAGES.csv` con las reglas F1-F5 (absorbidas de la extinta
  `etapa-fanpage`, T1 p2-simplificacion). Los ángulos con respaldo de voz real rankean por encima de
  los teóricos.
  - ⚠️ Si entrega **Formato B** (sin página ideal): alertar al operador antes de continuar. No
    bloquear, pero marcar como pendiente.
  - **`etapa-2` también elige y registra la imagen de referencia `ligera` fija del producto** (una
    sola, para las 6 fichas) con `python Ads/_TOOLS/referencia_f1.py --elegir ...` — regla completa
    en `.claude/agents/ETAPA-2.md`.

---

## PASO 4 — `etapa-4` ∥ `etapa-5` (PARALELO)

Lanzar ambas en el mismo turno. Esperar AMBOS outputs antes de `etapa-6`.

- **`etapa-4` (FASE 1)** — Inputs: las 6 fichas de `etapa-2` (con formato de creativo asignado),
  producto, P1u, imagen del producto, output de `etapa-1` y `etapa-1b`, `<pagina_asignada>`, datos
  del operador (días de resultado, dosis, momento de uso, estadísticas, FAQs). Output: 6 copies +
  **ad-imagen** (Prompt Maestro) para los 6 ángulos (F1 es TODO IMAGEN) + **3 infografías del
  bot** e IMAGEN 4 opcional.
- **`etapa-5` (FASE 1 — Bot Paraguas)** — Inputs: las 6 fichas (con nivel de conciencia), producto,
  `producto_key`, `<pagina_asignada>`. Output: **las 9 frases del ángulo** para
  `PRODUCTOS/_DIM_FLUJO_BOT.csv` + **los bloques de juicio** (los 4 campos del catálogo,
  testimonios, audio, texto de M2 con su guión de audio testimonio, FAQ), integrando los 6 ángulos
  con **Promesa Integradora**. El texto fijo, el orden de los elementos y las interacciones **no
  son suyos**: los declara `DOCTRINA/PLANTILLAS_FLUJO_BOT.md`.
  Después: `python Ads/_TOOLS/gen_flujo_bot.py [producto_key]` renderiza el flujo completo en
  `PRODUCTOS/[PK]/FLUJO_LUCIDBOT.md`. Si bloquea, produce el dato que nombra y volvé a correrlo.

> **DEFAULTS DE OPERADOR:** cuando el operador no entrega días de resultado, dosis, momento de uso,
> estadísticas, # clientes o FAQs, `etapa-4` y `etapa-5` usan los valores base de
> `DOCTRINA/PLANTILLAS_DEFAULTS_OPERADOR.md` en vez de detenerse. El dato real siempre sobreescribe el default.

---

## PASO 5 — `etapa-6` (FASE 1 — planificador de testeo)

Se activa al recibir outputs de AMBAS.
Inputs: las 6 fichas de `etapa-2`, los ads-imagen de `etapa-4`, `<pagina_asignada>`.
Output: 1 campaña, 6 conjuntos, **2 anuncios por conjunto**, 4 AM día siguiente. Los 6 conjuntos
declaran `formato: IMAGEN` (F1 es TODO IMAGEN, validado por `gen_plan.py --validar`). Incluir al
pie: "FanPage de pauta: [página asignada]".

> **Si el conector Meta Ads está disponible → MODO MCP (`DOCTRINA/MCP_PLAYBOOK.md`):** además del texto, el
> orquestador CREA el esqueleto real **en PAUSED** (campaña Tráfico + 6 conjuntos
> CONVERSATIONS/WHATSAPP, ABO $2.99/conjunto, banda de edad por avatar con Advantage+ OFF, 4 AM).
> **Pre-flight obligatorio:** cuenta `is_ads_mcp_enabled`+`is_queryable`, fanpage asignada con
> WhatsApp conectado, IDs en `2_DATA_PRODUCTO.txt`. Los **anuncios** van en un **2º paso** (el MCP no
> sube media): `etapa-4` deja las 6 imágenes en `Ads/MEDIA_[PRODUCTO]/` +
> `PROMPTS_IMAGENES_[PRODUCTO].txt`. Cuando el operador sube los assets y avisa,
> se crean **2 anuncios/conjunto** y se genera `PRODUCTOS/[NOMBRE]/3_CAMPAÑA_META.txt`.
> **Nada se activa solo.**

### Presupuesto de esta fase

**TESTEO EN DOS ETAPAS:** ETAPA 1 días 0-3 = 6 conjuntos × **$2.99** (se cortan 2-3 por
conversación) → ETAPA 2 días 4-8 = 3 sobrevivientes × **$5.98**. Mismo gasto total, veredicto de
venta ~2× más rápido. Fórmula autoajustable `presupuesto/día = 7 × (costo por conversación
observado)`, **piso $2.99 · techo $3.95**. Detalle en `DOCTRINA/CALENDARIO_ESCALADO.md` §1.5.

**Anuncios por conjunto:** 2, nunca 1. Qué va en el 2º está **EN PRUEBA** (DUPLICADO vs
DOS CONCEPTOS del mismo ángulo). **Default vigente = DUPLICADO.** Diseño del test en
`.claude/agents/ETAPA-6.md`.

---

## PASO 6 — `etapa-guardar-producto` (OBLIGATORIO)

Crear la carpeta `PRODUCTOS/[NOMBRE]/` y ejecutar **Write** para los archivos por rol (nombres
fijos, iguales para todo producto):

- `1_HACER_MANUAL.txt` — **todo lo que el operador ejecuta a mano**, en orden y listo para copiar/pegar.
- `2_DATA_PRODUCTO.txt` — la **memoria del producto**: validación, costeo, componentes, los 6
  ángulos, ángulos descubiertos, página asignada, config MCP y el **REGISTRO DE CONJUNTOS**.
- *(Si hubo MCP)* `3_CAMPAÑA_META.txt` — **llave técnica**: IDs de campaña, conjuntos, anuncios y creativos.
- Además escribe/actualiza `PRODUCTOS/_DIM_CONJUNTOS.csv` (SALIDA 4 de su archivo) y la fila en
  `_PORTAFOLIO.txt`.

Los archivos llevan el **mismo encabezado único** en la primera línea (`PRODUCTO · VERSION · FECHA ·
COSTO · DOSIS · page_id · campaign_id`). Si no existen en disco y no pasan el **gate de
reconciliación**, el paso NO está completo.

---

## ENTREGA INTERACTIVA EN EL CHAT (default — preferencia del operador)

Los TXT SIEMPRE se escriben completos en disco. PERO además, tras cerrar `etapa-guardar-producto`,
el orquestador entrega el contenido de EJECUCIÓN de `1_HACER_MANUAL.txt` **en el chat, parte por
parte**. División del trabajo: el orquestador guarda la data y analiza; el **operador SOLO ejecuta**.

- **Por partes con checkpoint:** (1) prompts de imagen → (2) flujo LucidBot campo por campo →
  (3) subir media → (4) conjuntos + copies + precio → (5) duplicar→WhatsApp + activar 4 AM. Después
  de cada parte, ESPERAR el "listo/check". No volcar todo de golpe.
- **Verbatim y COMPLETO — nunca truncar.** Sin "…", sin "ver el TXT". Si no cabe en un turno,
  partirlo en sub-bloques rotulados, nunca cortarlo a mitad de una frase.
- **Solo lo ejecutable:** en el chat NO va la doctrina ni la data de análisis (eso vive en
  `2_DATA_PRODUCTO.txt`).
- **Prompts de imagen = Prompt Maestro YA RELLENADO** (todas las `[VARIABLES]` resueltas, sin citas
  de clase).
- **NO reescribir las piezas FIJAS/universales del bot:** INTERACCIÓN 3 (datos), 4 (confirmación),
  5 (cierre), mensajes de inactividad y reglas base son IGUALES para todo producto — el operador ya
  las tiene cargadas. En el chat entregar SOLO lo que cambia: catálogo (4 campos), mensaje inicial
  (elementos 1-12), INTERACCIÓN 0/1/2, FAQ del producto y reglas CONDICIONALES. Las fijas se
  mencionan como "las de siempre (sin cambios)". (Siguen completas en `1_HACER_MANUAL.txt` como
  respaldo.)

---

## FIN FASE 1

```
FASE 1 COMPLETADA ✓

□ FanPage asignada (ETAPA-2) → [Número + Nombre] ← confirmar antes de pautar
□ Edad de segmentación recomendada → [XX+] ← configurar en Meta Ads
□ Estructura de campaña de testeo (ETAPA-6) → crear en Meta Ads para 4 AM mañana
□ Creativos: ad-imagen para los 6 ángulos (F1 es TODO IMAGEN, ninguno pausado)
□ 6 copies + 3 infografías del bot (+ IMAGEN 4 opcional) (ETAPA-4)
□ Flujo bot paraguas (ETAPA-5) → configurar en LucidBot antes del lanzamiento
□ Guardado en disco: PRODUCTOS/[NOMBRE]/ con 1_ + 2_ (+ 3_ si hubo MCP) ← gate de reconciliación
□ Fila en PRODUCTOS/_PORTAFOLIO.txt (estado LISTO aunque no esté lanzado)

VERIFICACIÓN DE COHERENCIA COPY ↔ BOT (antes de lanzar):
□ El beneficio principal de los copies aparece en el mensaje inicial del bot
□ Condiciones de entrega ("envío gratis", "pagá al recibir") coinciden entre copy y bot
□ El P1u de los copies con precio (máx 3, ideal 2 de 6) coincide con el P1u del bot
□ El framing de oferta usa "tratamiento de X días" y "la más elegida" para P3u en el bot
□ Cada conjunto tiene 2 anuncios

⚠️ Si ETAPA-2 entregó Formato B en su asignación de FanPage, crear la página antes de lanzar.
⚠️ Identificar el ángulo ganador y volver con métricas para FASE 2.
⚠️ NO continuar con FASE 2 sin datos de testeo confirmados.
⚠️ Al confirmar el ángulo ganador, traer también el EXPORT DE CHATS de LucidBot de la
   ventana de testeo — es el input de ETAPA-11. Sin chats el diagnóstico dice DÓNDE se
   pierde la venta, nunca POR QUÉ.
```
