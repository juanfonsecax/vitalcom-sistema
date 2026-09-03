---
name: etapa-guardar-producto
description: Guarda el producto en disco al final de cada fase. Crea UNA carpeta por producto en PRODUCTOS/[NOMBRE]/ con archivos por rol — 1_HACER_MANUAL.txt (todo lo que el operador ejecuta a mano), 2_DATA_PRODUCTO.txt (memoria del producto para análisis/optimización) y 3_CAMPAÑA_META.txt (IDs reales de Meta, solo si hubo MCP). Obligatorio antes de entregar el paquete final. Pasa un gate de reconciliación antes de cerrar.
tools: Read, Write
---

# ETAPA-GUARDAR-PRODUCTO

## Cuándo se activa
- **Fin de FASE 1** (después de ETAPA-6): crea la carpeta y sus archivos.
- **Fin de FASE 2** (después de ETAPA-6 Fase 2): ACTUALIZA los mismos archivos con el ángulo ganador, microángulos, copies/bot/campaña de escalado, y los resultados del testeo si el operador los entregó. Sube VERSION.

⚠️ Usar el tool **Write** para crear físicamente los archivos. No basta mostrarlos en el chat — si no se escriben en disco, se pierden al cerrar la sesión.

---

## ESTRUCTURA FIJA — una carpeta por producto

```
PRODUCTOS/
  └── [NOMBRE_SIN_ESPACIOS]/
        ├── 1_HACER_MANUAL.txt     ← TODO lo que el operador ejecuta a mano (copiar/pegar)
        ├── 2_DATA_PRODUCTO.txt    ← memoria del producto (análisis / optimización futura)
        └── 3_CAMPAÑA_META.txt     ← IDs reales de Meta (solo si la campaña se creó por MCP)
```

- **Nombres de archivo FIJOS**, iguales para todo producto. El operador siempre abre `1_HACER_MANUAL.txt` para trabajar y adjunta `2_DATA_PRODUCTO.txt` en la próxima sesión.
- **Un rerun SOBRESCRIBE** estos mismos archivos (Write sobre la misma ruta) y sube `VERSION`. **Prohibido** crear `_SIMULACION`, `_COPIES_V2`, `_v3`, etc. — esos archivos sueltos son los que generan contradicciones.
- Si hay archivos viejos del mismo producto sueltos en `PRODUCTOS/` (esquema plano anterior), consolidar su contenido vigente en los 3 oficiales y borrar los viejos.

### ENCABEZADO ÚNICO DE VERDAD
La **primera línea de los 3 archivos** es idéntica. Permite saber sin ambigüedad cuál es la versión vigente y detectar discrepancias:

```
═══ [PRODUCTO] · VERSION [v1] · [FECHA] · COSTO Q[..] · DOSIS [..] · page_id [..] · campaign_id [.. o "sin MCP"] ═══
```

---

## ARCHIVO 1 — `1_HACER_MANUAL.txt` (lo que el operador hace a mano)

> Es el único archivo que el operador abre para ejecutar. Todo verbatim, en orden, listo para copiar y pegar. Acá va lo que el sistema NO puede hacer solo: editar el flujo de LucidBot, subir creativos, generar imágenes.

> **REGLA DE CONTENIDO LIMPIO (obligatoria):** ARCHIVO 1 lleva el contenido FINAL completo — nunca truncado, nunca "ver historial" ni "ver 2_DATA" como sustituto de contenido real. Pero NUNCA lleva doctrina: cero citas de clase/mentor ("Clase 19, Joaquín", "Clase 22", etc.), cero explicación de POR QUÉ existe una regla, cero razonamiento de ranking o metodología. Esas dos cosas (la cita y el porqué) van únicamente en ARCHIVO 2. La prueba: si el operador tuviera que preguntar "¿y esto para qué me sirve?", esa frase no debería estar en ARCHIVO 1. Al copiar texto de `PLANTILLAS_ADS.md` o `PLANTILLAS_INFOGRAFIAS.md`, omitir cualquier paréntesis o nota que cite una clase/mentor — pegar solo la instrucción ya resuelta con sus `[VARIABLES]` reemplazadas.

```
═══ [encabezado único] ═══
HACER MANUAL — [PRODUCTO] | FASE [1/2] | [fecha]
FanPage de pauta: [página + identidad]   ·   Edad de segmentación: [XX+]

── A. CHECKLIST RÁPIDO (lo que tenés que hacer) ──
[ ] Generar las imágenes-ad de los ángulos vírgenes (prompts en sección C)
[ ] Generar las 3 infografías del bot (prompts en sección C)
[ ] Configurar el flujo en LucidBot (sección E, campo por campo)
[ ] Subir creativos a Meta y revisar los anuncios (sección B + D)
[ ] Programar/activar la campaña a las 4 AM (sección F)

── B. CREATIVOS POR CONJUNTO (qué va en cada uno) ──
[tabla: conjunto | formato (VIDEO archivo / IMAGEN) | archivo o prompt | precio en ad sí/no]

── C. PROMPTS DE IMAGEN (copiar y pegar en Gemini/DALL·E) ──
[Prompts completos de los ads-imagen de ángulos vírgenes + los 3 prompts de infografías del bot, con todas las variables reemplazadas]

── D. COPIES POR CONJUNTO (copiar y pegar en Meta) ──
[Los 6 copies COMPLETOS verbatim: 3 textos + 3 títulos + descripción por ángulo, con marca de "lleva precio: sí/no"]

── E. FLUJO LUCIDBOT COMPLETO (copiar y pegar en LucidBot) ──
[El flujo ENTERO verbatim: catálogo, 13 elementos, 5 interacciones, los 3 mensajes de inactividad (texto fijo de M2 + guion del audio testimonio), FAQs, reglas — campo por campo]

── F. CHECKLIST ANTES DE LANZAR ──
[Pasos finales: revisar 12 anuncios, precio donde corresponde, programar 4 AM, etc.]
```

---

## ARCHIVO 2 — `2_DATA_PRODUCTO.txt` (memoria del producto)

> Liviano. Es lo que se carga en la próxima sesión para retomar sin reinvestigar y lo que usa la fase de análisis/optimización (ETAPA-7) para saber qué ángulo ganó, a quién iba y cómo.

```
═══ [encabezado único] ═══
PRODUCTO: [nombre completo]
FECHA_PROCESADO: [fecha]
VERSION: [v1 / v2 ... — subir +1 en cada rerun, nunca dejar dos versiones vivas]
COSTO_PROVEEDOR_Q: [valor]
DOSIS / PRESENTACIÓN: [valor único]
PROVEEDORES_DROPY: [N]   ·   ANUNCIANTES_AD_LIBRARY: [N o "no provisto"]
VALIDACION_PRODUCTO: [score + color + notas de ETAPA-PRODUCTO]
FANPAGE: [Formato A: página asignada + page_id | Formato B: página nueva sugerida + identidad + edad]
MCP_ACCOUNT_ID: [..] · MCP_PAGE_ID: [..] · MCP_PIXEL_ID: [..] · TASA_USD_GTQ: [ej. 7.62]

━━━ COSTEO (ETAPA-1) ━━━
P1u / P2u / P3u / CPA_OBJETIVO / CPA_BREAK_EVEN  (valores exactos) + márgenes por opción.

━━━ COMPONENTES (ETAPA-1B) ━━━
[ingredientes con mecanismo + diferenciador clave]

━━━ ÁNGULOS FASE 1 (6 rankeados — ETAPA-2) ━━━
[por ángulo: nombre, creativo asignado (VIDEO archivo / IMAGEN), dolor, AVATAR (a quién va), nivel de conciencia, saturación, promesa]

━━━ ÁNGULOS DESCUBIERTOS (ETAPA-1B) ━━━
[lista]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
REGISTRO DE CONJUNTOS — LLAVE DE UNIÓN CON META (insumo de ETAPA-7 / optimización)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
> Cada fila usa el NOMBRE EXACTO del conjunto en Meta (de ETAPA-6) como llave. Cuando se lean
> los datos de Meta (CPC, CPA, CPM, conversaciones, impresiones, clics), se unen por ese nombre
> para evaluar cada ángulo contra su CPA objetivo y break even.

CAMPAÑA: [nombre]   ·   FASE: [1 testeo / 2 escalado]   ·   LANZAMIENTO: [fecha 4 AM]
CPA_OBJETIVO: Q[..]   ·   CPA_BREAK_EVEN: Q[..]   ·   PRESUPUESTO/CONJUNTO: $2.99 ETAPA 1 → $5.98 ETAPA 2 [MCP] / Q54 legacy
PD (Presupuesto de Decisión) = 1× Break Even = Q[..]   ·   se alcanza en ~[..] días a $2.99

| NOMBRE_CONJUNTO (llave Meta) | Ángulo | Tipo | Formato | Archivo/Prompt | Precio ad | Avatar | Hook | Estado |
|---|---|---|---|---|---|---|---|---|
[una fila por conjunto]

RESULTADOS_TESTEO: [vacío en FASE 1. Al optimizar, pegar por conjunto:
  conjunto | clics | impresiones | conversaciones | ventas | CPC | CPM | CPA_real | %conv_clic | %conv_impresion ]
ANGULO_GANADOR: [vacío hasta que el operador lo confirme con métricas]
  → al confirmarlo, anotar: conjunto ganador + avatar al que iba + por qué ganó (qué se hizo distinto).

━━━ DATOS DE SATURACIÓN ━━━
[resultado de ETAPA-RESEARCH Módulo B si se corrió, o "no corrido"]

━━━ PRÓXIMA SESIÓN ━━━
- Optimización (ETAPA-7): leer este REGISTRO + datos de Meta, comparar CPA real vs objetivo/break even, indicar qué escalar y qué apagar.
- FASE 2: si hay ángulo ganador confirmado + métricas → ir directo a ETAPA-3A.
- Nuevo testeo del mismo producto: saltar ETAPA-1 y ETAPA-1B (ya están), ir a ETAPA-0 con nuevos videos.
- El detalle copiable (copies, prompts, bot) está en 1_HACER_MANUAL.txt.
```

---

## ARCHIVO 3 — `3_CAMPAÑA_META.txt` (solo si hubo MCP)

> Llave técnica. No se abre a mano; lo usa el sistema para leer métricas por MCP (ETAPA-7).

```
═══ [encabezado único] ═══
MAPA DE CAMPAÑA — [PRODUCTO] | FASE [1/2]
Cuenta: [nombre · act_id · moneda]   ·   Negocio: [nombre · id]
FanPage: [nombre · page_id]   ·   WhatsApp: [número]
Campaña: [nombre · campaign_id]   ·   Objetivo: Tráfico → CONVERSATIONS → WHATSAPP
Presupuesto: ABO $2.99/conjunto (ETAPA 1 · $5.98 en ETAPA 2)   ·   Segmentación: [BANDA del avatar del ángulo] Advantage+ OFF   ·   4 AM [fecha]

[Por conjunto: NOMBRE · ad_set_id · formato · creative_id/video_id · precio · los 2 ad_id]
Lectura ETAPA-7: CPA real = (amount_spent ÷ actions:omni_purchase) × TASA, vs CPA Base / Break Even.

RESULTADOS_TESTEO: [vacío — lo lee ETAPA-7]
ANGULO_GANADOR: [pendiente]
```

---

## SALIDA 4 — anexar a `PRODUCTOS/_DIM_CONJUNTOS.csv` (obligatorio, portafolio-wide)

> **Qué es:** la tabla de DIMENSIONES que traduce el nombre crudo del conjunto en Meta a la semántica del sistema (ángulo, avatar, dolor, formato, tipo de hook, nivel de conciencia, rol de embudo, precio). Sin ella, las tablas de hechos son solo plata y clics: no se puede responder **qué ángulo / qué avatar / qué hook / qué formato funciona**, ni dentro de un producto ni entre productos.
>
> **Por qué es un CSV del portafolio y no una tabla dentro de `2_DATA_PRODUCTO.txt`:** el REGISTRO DE CONJUNTOS del `2_DATA` sigue existiendo (es la vista legible por producto), pero está en prosa y con nombres abreviados — no se puede agregar por él. El CSV es la capa máquina, con la MISMA llave que usan `_FACT_VENTAS.csv` y `_FACT_ENTREGA.csv`.

**Regla dura de la llave:** `conjunto_meta` debe ser el **nombre EXACTO tal como quedó en Meta**, con sufijos incluidos (`- Copia`, `- Copia 2`), copiado de `3_CAMPAÑA_META.txt` o del export. **No normalizar, no abreviar, no corregir mayúsculas.** Si el mismo ángulo corre bajo dos nombres distintos, van **dos filas con el mismo `angulo_key`** — así se agregan juntas sin tocar Meta.

Columnas (orden fijo):
```
producto_key, conjunto_meta, cuenta_alias, campana_clave, fase, angulo_key, angulo_nombre,
avatar, avatar_genero, avatar_edad, emocion_dominante, dolor_nucleo, formato, tipo_hook,
nivel_conciencia, rol_embudo, rol_embudo_origen,
lleva_precio, creativo_id, origen_angulo, estado, verificado_en_csv, fecha_alta, notas
```

Vocabularios controlados (no inventar valores nuevos sin anotarlo):
- `avatar_genero`: MUJER · HOMBRE · MIXTO
- `avatar_edad`: 25-35 · 35-45 · 45-60 · 60+ — el bucket DOMINANTE, no el rango completo
- `emocion_dominante`: MIEDO_FUTURO · VERGUENZA · RESIGNACION · FRUSTRACION_MEDICA · DESCONFIANZA · AGOTAMIENTO · CURIOSIDAD
  Los declara ETAPA-2 en su ficha de ángulo. **Nunca dejarlos vacíos**: si un ángulo viejo no los
  trae, se rellenan leyendo su ficha en `2_DATA_PRODUCTO.txt`. Son lo que convierte la investigación
  de avatar en algo agregable — sin ellos el avatar muere en el copy y no se contrasta nunca contra
  quién compró. Con Andromeda pesan más que antes: el creativo es el targeting, así que el avatar
  solo se puede medir por lo que el creativo dice y retrata.
- `fase`: FASE1 · FASE2
- `formato`: VIDEO · IMAGEN
- `tipo_hook`: MIEDO · EMOCIONAL · TESTIMONIO · EDUCACIONAL · MECANISMO · OFERTA · PRUEBA_SOCIAL · ANTI_FALSIFICACION
- `nivel_conciencia`: 1 · 2 · 3 (admite 3a/3b/1-2 como en ETAPA-2). Vacío si no se declaró — **no inventarlo**.
- `rol_embudo`: TOFU · MOFU · BOFU — `rol_embudo_origen` = **DECLARADO** (lo dijo ETAPA-3B/ETAPA-4) o **DERIVADO_NC** (se dedujo del nivel de conciencia con la regla de abajo).
- `lleva_precio`: SI · NO → refleja lo **EJECUTADO** en Meta, no lo planificado. Si difieren, se anota la discrepancia en `notas`.
- `origen_angulo`: TRANSCRIPCION (ETAPA-0) · VOZ_REAL (ETAPA-1B) · PROBLEMA_OCULTO · GANADOR_PRIOR · MICROANGULO_3B
- `estado`: ACTIVO · PODADO · PAUSADO · NUNCA_ENTREGO
- `verificado_en_csv`: SI si el `conjunto_meta` ya aparece en `_FACT_VENTAS.csv` o `_FACT_ENTREGA.csv` (llave confirmada contra data real) · NO si todavía es solo diseño.

Regla de derivación NC → rol de embudo (doctrina del sistema: el rol se mapea al nivel de conciencia de ETAPA-2):
`NC 1 → TOFU · NC 2 → TOFU · NC 3 → MOFU · tipo_hook=OFERTA → BOFU`. Se marca `rol_embudo_origen=DERIVADO_NC` para no leerlo como dato duro.

**Cuándo se escribe:**
- **FASE 1**, al cerrar: una fila por cada uno de los 6 conjuntos (`verificado_en_csv=NO` hasta que gasten).
- **FASE 2**, al cerrar: una fila por microángulo, con `rol_embudo` DECLARADO por ETAPA-3B.
- **Al leer data** (ETAPA-7): si aparece un `conjunto_meta` que no está acá, se **anexa la fila** y se marca `verificado_en_csv=SI`. Nunca se descarta una fila de datos por falta de dimensión.
- Un rerun **actualiza** las filas del producto; no duplica. Llave única = (`producto_key`, `conjunto_meta`).

---

## SALIDA 5 — fila en `PRODUCTOS/_DIM_PRODUCTOS.csv` (obligatorio al dar de alta un producto)

> **Qué es:** la tabla que traduce el `producto_key` a **dónde vive el producto en el disco**. El mismo producto tiene nombres distintos en las 4 ubicaciones (NUSAVA llegó a tener 5 grafías). Sin esta fila, ningún agente puede encontrar sus videos, transcripciones ni creativos sin adivinar.

Además de los umbrales (`cpa_be_q`, `cpa_base_q`, tasa, cuenta, page_id), rellenar **las 5 columnas de carpeta**:

| Columna | Qué apunta | Ejemplo (NUSAVA) |
|---|---|---|
| `slug_carpeta` | `PRODUCTOS/[X]/` | `NusavaB12` |
| `carpeta_videos` | `Ads/1.1 Videos/[X]/` | `NUSAVA B12` |
| `carpeta_transcripciones` | `Ads/1.2 Transcripcion videos/[X]/` | `NUSAVA B12` |
| `carpeta_media` | `Ads/[X]/` (lavados + ads-imagen) | `MEDIA_GTR7_NUSAVAB12` |
| `carpetas_extra` | sub-lotes / casos especiales | `NUSABA B12 ARDOR = sub-lote sin transcripciones` |

**Reglas:**
- Se escriben con el **nombre EXACTO de la carpeta en disco**, tal como está — no se normaliza ni se corrige. La tabla se adapta al disco, no al revés.
- **Las carpetas NO se renombran para emparejarlas**: los `1_HACER_MANUAL.txt` referencian rutas `MEDIA_*` que el operador usa para ejecutar.
- Si el producto todavía no tiene alguna carpeta (ej. sin videos), se deja vacío y se anota en `carpetas_extra`.
- ⚠️ **Escribir este CSV con un escritor CSV real** (`csv.DictWriter`), nunca a mano: el campo `notas` lleva comas y **debe ir entre comillas dobles**. (Bug real 31-jul: la fila NUSAVA quedó con 20 campos en vez de 17 y la nota se truncaba.)

---

## GATE DE RECONCILIACIÓN (obligatorio antes de cerrar)
> El producto NO está "completo" hasta pasar este gate. Garantiza que el sistema entregue **siempre lo mismo**, sin que un rerun deje datos que se contradicen entre archivos.

Verificar que estos 6 valores son **idénticos** donde aparezcan (encabezado de los 3 archivos + cuerpo) y coinciden con los INPUTS CONGELADOS del orquestador:

| # | Valor | Debe coincidir en |
|---|---|---|
| 1 | COSTO_PROVEEDOR_Q | encabezado · 2_DATA (costeo) |
| 2 | PRECIOS P1u/P2u/P3u | 2_DATA (costeo) · 1_HACER_MANUAL (copies + bot) · 3_CAMPAÑA |
| 3 | DOSIS / presentación | encabezado · 2_DATA (componentes) · 1_HACER_MANUAL (infografías + bot) |
| 4 | PROVEEDORES_DROPY | 2_DATA (un solo número) |
| 5 | FANPAGE (Formato A/B + page_id) | los 3 archivos |
| 6 | campaign_id + 6 ad_set_id | 3_CAMPAÑA · REGISTRO DE CONJUNTOS de 2_DATA |
| 7 | NOMBRE_CONJUNTO de cada conjunto (exacto) | REGISTRO DE CONJUNTOS de 2_DATA · `_DIM_CONJUNTOS.csv` · 3_CAMPAÑA |
| 8 | ángulo · formato · precio_en_ad de cada conjunto | 2_DATA · `_DIM_CONJUNTOS.csv` (mismo valor, sin excepción) |

**Si hay UNA discrepancia → corregir y reescribir; NO entregar.** Reportar al operador qué se reconcilió. Si el operador cambió un input (costo, dosis, página) después de una corrida previa, eso es un **rerun**: subir VERSION y rehacer los archivos completos.

---

## Confirmación al operador
Después de los Write, confirmar:
"✓ Guardé el producto en disco en `PRODUCTOS/[NOMBRE]/`:
 - `1_HACER_MANUAL.txt` — todo lo que ejecutás a mano (copies, prompts, flujo LucidBot, checklist).
 - `2_DATA_PRODUCTO.txt` — la memoria del producto (ángulos, avatares, costeo, registro de conjuntos).
 - `3_CAMPAÑA_META.txt` — los IDs reales de Meta (si hubo MCP).
La próxima sesión, adjuntá `2_DATA_PRODUCTO.txt` y retomamos sin reprocesar; `1_HACER_MANUAL.txt` lo abrís para configurar Meta/LucidBot. Gate de reconciliación: OK."

## Entrega de ejecución en el chat (default — CLAUDE.md regla 19)
Después de escribir los archivos y confirmar el gate, el orquestador NO se queda solo en el TXT: entrega el contenido de EJECUCIÓN de `1_HACER_MANUAL.txt` **en el chat, parte por parte y verbatim (nunca truncado)**, en el orden de ejecución (prompts de imagen → flujo LucidBot campo por campo → subir media → conjuntos + copies + precio → duplicar→WhatsApp + activar 4 AM), esperando el "listo/check" del operador entre cada parte. Solo lo copiable (sin doctrina ni data de análisis — eso vive en `2_DATA_PRODUCTO.txt`). Los prompts de imagen se entregan como el Prompt Maestro YA RELLENADO, un bloque por creativo. El TXT queda como respaldo; el chat es la vía de ejecución del operador.

## Cómo se usa en sesión futura
1. El operador adjunta `2_DATA_PRODUCTO.txt`.
2. Leer el análisis + el REGISTRO DE CONJUNTOS.
3. Tres caminos:
   - **Optimización (ETAPA-7):** traer datos de Meta (o leerlos por MCP), unir por NOMBRE_CONJUNTO, comparar CPA real vs objetivo/break even y % de conversación, e indicar qué escalar y qué apagar.
   - **FASE 2:** ángulo ganador confirmado + métricas → ETAPA-3A.
   - **Nuevo testeo:** saltar ETAPA-1/1B → ETAPA-0 con nuevos videos.
