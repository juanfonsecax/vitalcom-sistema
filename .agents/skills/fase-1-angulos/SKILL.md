---
name: fase-1-angulos
description: "FASE 1 — Pre-testeo. Orquesta la secuencia completa que convierte transcripciones de video en una campaña de testeo de 6 ÁNGULOS lista para lanzar: validar producto, clasificar creativos (los videos quedan como FUENTE del ángulo, no como el creativo), costear, minar voz del cliente, construir las 6 fichas de ángulo (etapa-2 también asigna la FanPage), escribir copies e infografías, construir el bot paraguas, planificar la campaña TODO EN IMAGEN y guardar el producto en disco. Úsala cuando flujo.py devuelve el nodo F1.paquete, o cuando el operador dice \"tengo transcripciones\", \"quiero lanzar un producto nuevo\", \"arrancar testeo\" o \"pre-testeo\"."
tools: Read, Write, Glob, Grep, Bash, Task
---

# FASE 1 — PRE-TESTEO (testeo de ÁNGULOS)

**Mueve el ÁNGULO. Todo lo demás queda fijo.**

```
6 ÁNGULOS distintos × concepto Y FORMATO FIJOS (IMAGEN, C2_BENEFICIOS)   ← mide el ÁNGULO
```

- Los 6 ad-imagen comparten layout, paleta y estructura; cambian solo hook, beneficios, props y
  avatar. No se rotan estilos (eso es de FASE 2): si la ejecución visual varía junto con el ángulo,
  nada es atribuible.
- **Todo en IMAGEN.** Los videos de competencia que elige `etapa-0` son la FUENTE del ángulo, nunca el
  creativo de F1; el video se testea en FASE 2. `Ads/_TOOLS/gen_plan.py --validar` bloquea un plan de
  F1 con un conjunto que no sea `IMAGEN`.

**Secuencia:** `etapa-producto` → `etapa-0` → `etapa-1` → `etapa-1b` → `etapa-2` (incluye la
asignación de FanPage) → (`etapa-4` ∥ `etapa-5`) → `etapa-6` → `etapa-guardar-producto`

---

## Entrada — el flujo dicta

Esta skill se carga cuando `python Ads/_TOOLS/flujo.py [producto_key]` devuelve `F1.paquete`. Los
gates de entrada (`F1.congelar_inputs`: fila, costo, ≥6 transcripciones, media) y lo que cierra el
paquete están en `DOCTRINA/FLUJO.json`; si dice BLOQUEADO, se produce lo que falta y se vuelve a
correr. Publicar y activar son nodos aparte (`F1.publicar` → skill `publicar-meta`).

### Congelar inputs (antes de invocar cualquier etapa)

El orquestador fija este bloque una sola vez y lo repite textual al inicio de cada etapa. Si un
input cambia después → **rerun completo** que sobrescribe los archivos y sube `VERSION`, nunca un
parche. Si falta un obligatorio → **detener** y pedirlo, nunca asumir.

```
━━━ INPUTS CONGELADOS — [PRODUCTO] · VERSION v1 · [FECHA] ━━━
PRODUCTO (nombre exacto):     [..]
COSTO_PROVEEDOR_Q:            [en la moneda del mercado del producto]  ← define todo el costeo (ETAPA-1)
DOSIS / PRESENTACIÓN:         [ej. 5000 mcg · 1.5 ml sublingual]   ← valor único
PROVEEDORES_DROPY:            [N]
ANUNCIANTES_AD_LIBRARY:       [N o "no provisto"]
IMAGEN_PRODUCTO:              [sí/ruta]          ← obligatoria (análisis visual ETAPA-4/1B)
INGREDIENTES:                 [lista o "pendiente"]
TASA_MONEDA_POR_USD:          [tasa del producto — moneda local por USD; referencia en `_PARAMETROS_FINANZAS.csv`]
MCP_ACCOUNT_ID / MCP_PAGE_ID / MCP_PIXEL_ID:  [si se creará campaña por MCP]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Obligatorios: PRODUCTO, COSTO_PROVEEDOR_Q, DOSIS/PRESENTACIÓN, IMAGEN_PRODUCTO y ≥6 transcripciones.
INGREDIENTES puede quedar «pendiente» hasta `etapa-1b`.

### Transcripciones

- **En disco (recomendado):** videos en `Ads/1.1 Videos/[PRODUCTO]/` y sus `.txt` en
  `Ads/1.2 Transcripcion videos/[PRODUCTO]/`, con el mismo nombre y número que el video
  (`5. NombreProducto.mp4` → `5. NombreProducto.txt`). `etapa-0` las detecta solas.
- **Pegadas en el chat** (`--- NOMBRE_DEL_VIDEO.txt ---` antes de cada una): el orquestador las
  guarda primero en esa carpeta; `flujo.py` solo cuenta lo que existe en disco.
- La imagen del producto siempre se entrega en el chat (adjunta o link).
- Módulos opcionales de investigación antes de `etapa-0` (ingredientes por web, scraping de Ad
  Library): solo si el operador los pide (`DOCTRINA/ETAPA-RESEARCH.md`).

---

## PASO 1 — `etapa-producto` (validación)

Corre SIEMPRE primero. Inputs: producto candidato, costo, datos de mercado (proveedores Dropy y
anunciantes de Ad Library, opcionales).
- **NO APTO:** advertir qué criterio eliminatorio falló y preguntar si cambia de producto o sigue.
  No avanzar sin confirmación explícita.
- **APTO:** continuar.

## PASO 2 — `etapa-0` (fuentes del ángulo)

Inputs: las N transcripciones. Output: clasificación + los 6 videos elegidos por ángulo, como
FUENTE (evidencia y ganchos para `etapa-1b` y `etapa-2`), nunca como creativo de F1.

## PASO 3 — `etapa-1` (costeo)

Inputs: nombre exacto + costo del proveedor. La tabla de costeo, la arquitectura de oferta y la
regla de arranque 1u vs 2x1 son de `.Codex/agents/ETAPA-1.md`; las cifras salen de
`Ads/_TOOLS/costear.py`, nunca de memoria. Output: P1u, P2u, P3u, CPA Objetivo, CPA Break Even y el
**costo del pedido** que usa la oferta (1 unidad o el combo).

## PASO 4 — `etapa-1b` (componentes + VOZ DEL CLIENTE)

Inputs: nombre, ingredientes (si faltan, pedirlos al operador; la etapa no se bloquea) y output de
`etapa-0`. Mina la voz del cliente primero (Reddit, foros, reseñas, blogs). Output: BANCO DE DOLOR
REAL + ángulos descubiertos y cubiertos, que pasan a `etapa-2`.

Después, volcar cada frase con URL y verificarla antes de `etapa-2`:

```bash
python Ads/_TOOLS/verificar_voz.py --agregar-json hallazgos.json --escribir
python Ads/_TOOLS/verificar_voz.py --producto [PRODUCTO] --escribir
```

## PASO 5 — `etapa-2` (ángulos + FanPage)

Inputs: outputs de `etapa-0`, `etapa-1` y `etapa-1b` (con el banco de dolor real), componentes,
nombre y `<datos_saturacion>` (opcional). Output: 6 fichas de ángulo rankeadas con su clasificación
medible + `<pagina_asignada>` (Formato A o B, contra `PRODUCTOS/_DIM_FANPAGES.csv`). La etapa también
elige y registra la imagen de referencia `ligera` del producto con `Ads/_TOOLS/referencia_f1.py --elegir`.
- **Formato B** (sin página ideal): alertar al operador antes de seguir; no bloquea, queda pendiente.

## PASO 6 — `etapa-4` ∥ `etapa-5` (en paralelo)

Lanzar las dos en el mismo turno y esperar AMBOS outputs antes de `etapa-6`. Las dos reciben
`producto_key` y `carpeta_producto` (el `slug_carpeta` de `_DIM_PRODUCTOS.csv`).
- **`etapa-4`** — Inputs: las 6 fichas, producto, P1u, imagen, outputs de `etapa-1` y `etapa-1b`,
  `<pagina_asignada>` y los datos del operador (días de resultado, dosis, momento de uso,
  estadísticas, FAQs; si faltan, la etapa usa sus defaults). Output: 6 copies + 6 ad-imagen. Las 3
  infografías del bot las escribe en `PRODUCTOS/[carpeta_producto]/INFOGRAFIAS.md`.
- **`etapa-5`** (bot paraguas) — Inputs: las 6 fichas (con nivel de conciencia), producto y
  `<pagina_asignada>`. Output: las 9 frases del ángulo para `PRODUCTOS/_DIM_FLUJO_BOT.csv`; los
  bloques de juicio los escribe en `PRODUCTOS/[carpeta_producto]/BLOQUES_BOT.md`.
  Después: `python Ads/_TOOLS/gen_flujo_bot.py [producto_key]` arma el flujo completo. Si bloquea,
  se produce el dato que nombra y se vuelve a correr.

## PASO 7 — `etapa-6` (plan de testeo)

Inputs: las 6 fichas, los ad-imagen de `etapa-4` y `<pagina_asignada>`. Output: `_PLAN.json` con 6
conjuntos `formato: IMAGEN`. Nombres, presupuesto (`PRODUCTOS/_PARAMETROS_PUBLICACION.csv`), banda de
edad y fecha (4 AM del día siguiente) los deriva `Ads/_TOOLS/gen_lanzador.py`. Se valida con
`python Ads/_TOOLS/gen_plan.py --validar`. 2 anuncios por conjunto (default: el mismo creativo
duplicado).

## PASO 8 — `etapa-guardar-producto` (obligatorio)

Escribe en `PRODUCTOS/[carpeta]/` los archivos por rol:
- `2_DATA_PRODUCTO.txt` — la memoria del producto (validación, costeo, componentes, 6 ángulos,
  página, config MCP y REGISTRO DE CONJUNTOS).
- `1_HACER_MANUAL.txt` — lo genera `python Ads/_TOOLS/gen_manual.py [producto_key] --escribir`,
  después de `2_DATA_PRODUCTO.txt`. Si bloquea, nombra qué falta y quién lo produce; nunca se
  completa a mano.
- `3_CAMPAÑA_META.txt` solo si hubo MCP; además `PRODUCTOS/_DIM_CONJUNTOS.csv` y la fila en
  `_PORTAFOLIO.txt`.

Las cifras de costeo del producto (`cpa_be_q` y las demás) entran con
`python Ads/_TOOLS/cargar_costeo.py --producto [producto_key] --costo-pedido [costo del pedido de etapa-1]`
(el gate de FASE 1 exige el break-even). `_DIM_PRODUCTOS.csv` nunca se escribe a mano.

Todos los archivos llevan el mismo encabezado en la primera línea (`PRODUCTO · VERSION · FECHA ·
COSTO · DOSIS · page_id · campaign_id`). Sin el gate de reconciliación, el paso no está completo.

---

## ENTREGA EN EL CHAT (preferencia del operador)

Tras cerrar `etapa-guardar-producto`, el orquestador entrega lo ejecutable de `1_HACER_MANUAL.txt`
en el chat, **por partes con checkpoint**: (1) prompts de imagen → (2) flujo LucidBot campo por
campo → (3) subir media → (4) conjuntos + copies + precio → (5) duplicar → WhatsApp + activar 4 AM.
Después de cada parte, esperar el «listo».
- Verbatim y completo, nunca truncado; si no cabe, sub-bloques rotulados.
- Solo lo ejecutable, sin doctrina; prompts con todas las `[VARIABLES]` resueltas.
- Del bot, solo lo que cambia (catálogo, mensaje inicial, INTERACCIÓN 0/1/2, FAQ y reglas
  condicionales); las piezas fijas se nombran como «las de siempre (sin cambios)».

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
