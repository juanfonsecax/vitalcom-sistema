# SISTEMA VITALCOM — DOCUMENTO MAESTRO PARA UNA IA NUEVA

> **Para qué sirve este texto.** Está escrito para que una IA que NO tiene acceso a la carpeta del
> proyecto entienda cómo funciona el sistema de punta a punta: el negocio, las piezas, las reglas, el
> flujo de trabajo, los datos y la forma correcta de ayudar al operador. Si leés esto completo, podés
> razonar sobre cualquier producto, fase o decisión del sistema sin haber visto un solo archivo.
>
> **Foto tomada:** 18-oct-2026. Lo estructural (método, fases, reglas, arquitectura) es estable. Lo
> que cambia día a día (estado de cada producto, cifras, cuentas) está marcado como FOTO y puede
> haber envejecido: ante la duda, la verdad está en los CSV y en `flujo.py`, no acá.
>
> **Qué NO es.** No es una copia de los archivos. Cuando el texto dice "dueño: X", significa que
> existe un archivo/script X que manda sobre ese tema; vos no lo tenés, así que si el operador te
> pregunta algo que depende de un dato vivo, pedile el dato en vez de inventarlo.

---

## 1. EL NEGOCIO EN CINCO LÍNEAS

1. El operador (Juan) vende productos de **dropshipping contra entrega (COD)** en **Guatemala (GT)**
   y **Colombia (CO)**. Productos de salud/bienestar de impulso (suplementos, ungüentos, óvulos,
   etc.) y algún gadget.
2. El cliente llega por **anuncios de Meta (Facebook/Instagram) que abren WhatsApp**. En WhatsApp
   un **bot (LucidBot)** presenta el producto, el precio y cierra el pedido.
3. La orden va a **Dropi** (plataforma de dropshipping: proveedor, logística, flete, cobro contra
   entrega). El cliente paga al recibir. Si rechaza el paquete, hay devolución y costo perdido.
4. Las ventas se registran en **LucidSales** (CRM/ventas, tiene API con token `x-token`).
5. **El sistema** (este proyecto) es el "cerebro": decide qué ángulos probar, escribe copys,
   arma el bot, planifica y publica campañas, mide, y ordena pausar o escalar. **El operador son las
   manos**: genera imágenes, configura el bot, confirma las órdenes y aprieta los botones.

**La métrica que manda es el CPA (costo por venta) contra el Break-Even (BE), nunca el ROAS.** En
COD la venta y el cobro no ocurren el mismo día, así que el ROAS de Meta no sirve.

---

## 2. GLOSARIO RÁPIDO

| Término | Significa |
|---|---|
| **COD** | Cash on delivery, pago contra entrega. |
| **Ángulo** | La causa/sub-problema que el producto resuelve ("acné por desequilibrio hormonal" vs "por estrés"). Territorio del PROBLEMA. **Ángulo = por qué duele.** |
| **Concepto** | Cómo se *muestra* el anuncio (formato visual: testimonio, unboxing, beneficios, anti-falsificación…). Ortogonal al ángulo. **Concepto = cómo se muestra.** |
| **Microángulo** | Avatar ultra-específico dentro del ángulo ganador (FASE 4, banco de copy). |
| **Avatar (5 ejes)** | Dolores, deseos, miedos, frustraciones, edad/género + nivel de conciencia (Schwartz). |
| **CPA** | Costo por adquisición = gasto publicitario / ventas. |
| **BE (break-even)** | CPA donde la ganancia es CERO. Es el techo, no un objetivo. Se DERIVA (ver §9). |
| **PD (Presupuesto de Decisión)** | 1× BE gastado en una unidad (ángulo/concepto). Antes de eso, "0 ventas" no es veredicto, es falta de exposición. |
| **ABO / CBO** | El presupuesto vive en el conjunto (ABO) o en la campaña (CBO). |
| **1-1-5** | 1 campaña, 1 conjunto, 5 anuncios. **6-1-1** = 6 conjuntos × 1 anuncio. |
| **Surfing** | Subir presupuesto +20% por día, una vez, en la mañana. |
| **Post ID** | Reusar la publicación (con sus likes/prueba social) en otro conjunto/cuenta para escalar horizontal. |
| **LucidBot** | Plataforma donde se configura el bot de WhatsApp (flujo conversacional). Se configura A MANO; no hay API. |
| **LucidSales** | Fuente de VENTAS. Se baja por API (GT) o export manual (CO). |
| **Dropi** | Logística/proveedor COD. Dueña del costo de producto, flete, entregas y devoluciones reales. |
| **GTR7 / GTR0 / GTR13 / GTR3** | Alias de cuentas publicitarias de Meta. |
| **MCP** | Conector oficial de Meta Ads para crear/leer/editar campañas desde la sesión de IA. |
| **Andrómeda** | El motor de entrega de Meta; su CPM/compliance condiciona el creativo de los ADS (no del bot). |
| **FanPage** | Página de Facebook desde la que se pauta; hay 10, con identidad/tono/edad propios. |

---

## 3. LOS CUATRO PRINCIPIOS QUE EXPLICAN CASI TODO

1. **Un dato, un dueño.** Cada número/regla vive en UN archivo; los demás lo apuntan, no lo copian.
   Si un valor está en un CSV, no se repite en prosa.
2. **Lo determinista vive en código, no en el modelo.** Costos, BE, nombres, presupuestos, gates,
   decisiones de pausar/escalar salen de scripts Python y CSV. Lo que sí depende del modelo es la
   calidad de la escritura (copys, ángulos) y del juicio.
3. **La fase la dicta la data, no el operador.** El sistema nunca pregunta "¿en qué fase estás?":
   la calcula con `flujo.py` leyendo los CSV.
4. **Nada se ejecuta en Meta sin confirmación humana, orden por orden.** Todo nace PAUSED; el
   operador activa; las órdenes de pausar/escalar se ejecutan por MCP solo tras un "sí" explícito.

---

## 4. ARQUITECTURA EN CAPAS

```
OPERADOR (Juan)  ── confirma, genera imágenes, configura LucidBot, activa
     │
SESIÓN DE IA (orquestador) ── lee CLAUDE.md, corre flujo.py, carga la skill de la fase,
     │                         invoca subagentes (etapas), ejecuta órdenes por MCP con confirmación
     │
SKILLS (.claude/skills)  ── procedimiento de cada fase / tarea (fase-1..4, publicar-meta, ciclo-diario…)
ETAPAS (.claude/agents)  ── 15 subagentes especializados (etapa-0 … etapa-render)
     │
HERRAMIENTAS DETERMINISTAS (Ads/_TOOLS/*.py) ── costear, decidir, flujo, gen_*, ingerir_*, verificar_*
     │
DATOS ── CSV en PRODUCTOS/ (dimensiones y hechos) + Postgres (verdad de 5 tablas) + warehouse dbt/DuckDB
     │
DOCTRINA (DOCTRINA/*.md, FLUJO.json) ── el "porqué" y las reglas, leídas por skills y etapas
     │
APP WEB (app/) ── pantalla del operador (FastAPI + React) que lee contratos y dispara ejecutores
```

**Zonas de carpetas:** `DOCTRINA/`, `.claude/`, `PRODUCTOS/`, `Ads/`, `evals/` son las que el
sistema LEE. `VISTAS/` se abre (HTML generados). `_CONOCIMIENTO/`, `_OPERADOR/`, `_ROADMAP/`,
`_SKILLS_FUENTE/`, `INFPRODUCTOS/` son referencia humana: el sistema no las lee. `_RESPALDOS/` está
gitignored.

---

## 5. EL FLUJO DE CUATRO FASES (EL CORAZÓN DEL MÉTODO)

Hay además una **FASE 0** (buscar producto) y un **ciclo diario** post-lanzamiento.

```
FASE 0  BUSCAR PRODUCTO (skill buscar-producto, etapa-producto valida 17 criterios → APTO/NO APTO)
FASE 1  ÁNGULOS    6 ángulos × concepto fijo, todo IMAGEN, 6 conjuntos ABO     ← mide el ÁNGULO
FASE 2  CONCEPTOS  1 ángulo ganador × 10 conceptos (1-1-5 + 1-1-5 + 1-2-5)     ← mide el CONCEPTO
FASE 3  FLUJO      ángulo+concepto fijos, se reescribe el bot (LucidBot)        ← mide el CIERRE
FASE 4  ESCALADO   1-1-7 CBO (ganador ×7) + expansión horizontal                ← compra VOLUMEN
        (+ mini-F1 de exploración de 3 ángulos nuevos en paralelo)
```

### Regla maestra de estructura
> **Presupuesto PROTEGIDO (conjuntos separados) cuando la variable se decide por VENTA.
> Presupuesto LIBRE (1-1-N, Meta reparte) cuando se decide por ENTREGA.**

Por eso el **ángulo** se testea en conjuntos separados (Meta solo ve clics/conversaciones y esa
señal NO predice la venta), y el **concepto** se testea en 1-1-5 (ahí el criterio de Meta —CTR,
CPM, conversación— sí está alineado). **El 1-1-5 va en FASE 2 y en ABO; nunca en FASE 1 ni en CBO**
(en CBO Meta corona un solo anuncio y los demás no reciben entrega).

### FASE 1 — Testeo de ÁNGULOS
- **Inputs congelados** (se deciden UNA vez; si cambian, rerun completo que sobrescribe y sube
  `VERSION`): producto, mercado, costo en su moneda, dosis, imagen del frasco, **≥6 transcripciones
  TXT** de videos de competencia (en `Ads/1.2 Transcripcion videos/<carpeta>/`, transcritas con
  Gemini), y opcionalmente copys de competencia / saturación en la Biblioteca de Anuncios.
- **Los videos de competencia son la FUENTE del ángulo, nunca el creativo.** **FASE 1 corre TODO
  EN IMAGEN** (lo valida `gen_plan.py --validar`, que bloquea cualquier conjunto ≠ IMAGEN). El video
  se testea recién en FASE 2 como un concepto más.
- **Secuencia de etapas:** `etapa-producto` → `etapa-0` → `etapa-1` → `etapa-1b` → `etapa-2` →
  (`etapa-4` ∥ `etapa-5`) → `etapa-6` → `etapa-guardar-producto`.
- **Estructura:** 1 campaña, 6 conjuntos (un `angulo_key` cada uno), 1 anuncio por conjunto, ABO,
  concepto FIJO `C2_BENEFICIOS` variante `ligera`, mismo presupuesto en los 6 (invariante 6): hoy
  **2.99 USD/día por conjunto** (`_PARAMETROS_PUBLICACION.csv`).
- **Testeo en dos etapas:** E1 (días 0-3) descubre y corta los 2-3 peores **por conversación**;
  E2 (día 4+) sube los 3 sobrevivientes al **doble** (5.98) a la vez y decide por **VENTA**.
- **Salida a FASE 2:** hay `angulo_ganador` = ángulo con ≥ `min_ventas_ganador` (5) ventas
  acumuladas y CPA acumulado ≤ BE, **agregando por `angulo_key`** sobre todas las cuentas/semanas
  (nunca un conjunto en una semana: con 1-3 ventas la variación es azar de Poisson).
- **La conversación sirve para CORTAR, nunca para CORONAR** (conjuntos con la conversación más alta
  vendieron cero).

### FASE 2 — Testeo de CONCEPTOS
- Ángulo ganador y **copy único FIJOS**; la única variable es la ejecución visual. 10 conceptos.
- **Estructura:** Campaña A 1-1-5 (conceptos 1-5, cuenta principal) · Campaña B 1-1-5 (conceptos
  6-10, misma cuenta) · Campaña C 1-2-5 (los MISMOS 10, **en OTRA cuenta**, para no competir en la
  subasta). 6.00 USD/día por conjunto. Cada concepto corre **dos veces** en estructuras
  independientes.
- **Regla de replicación:** un concepto es GANADOR si queda arriba en **2 de sus 2** apariciones;
  1 de 2 es RUIDO (se repite); sin entrega = `SIN_ENTREGA`, nunca "perdedor". El empate técnico lo
  fija `margen_empate_cpa_pct` (10%). El PD en F2 se calcula **por `concepto_key` + variante,
  sumando todas sus apariciones**.
- **Nodos:** `F2.etapa-11` (solo DIAGNÓSTICO de congruencia anuncio↔bot, no bloquea) · `F2.conceptos`
  (`etapa-9` fabrica filas en `_DIM_CREATIVOS.csv` como `PENDIENTE_GENERAR`; `etapa-render` produce
  PNG en ChatGPT web; si hay VIDEO se lava con `lavar_videos.sh`) · `F2.plan` (etapa-4 ∥ etapa-5 →
  etapa-6 → guardar; `_PLAN_FASE2.json`) · `F2.publicar` · `F2.activar`.
- Se necesitan **10 conceptos publicables** o la fase no arranca.
- **Salida a FASE 3:** `concepto_2de2` (con ≥ `min_ventas_escalar` = 2 ventas por concepto; nunca
  escalar con 1 venta por azar).

### FASE 3 — Optimización del flujo LucidBot (el CIERRE)
- No se publica estructura nueva en Meta: el concepto ganador sigue corriendo **al mismo
  presupuesto de FASE 2**. La variable es el **flujo del bot**.
- `etapa-11` entrega el brief (diagnóstico + congruencia); `etapa-5` redacta los **BLOQUES DE
  JUICIO** del flujo; **el operador APLICA el cambio en LucidBot a mano** y registra el evento
  `CAMBIO_BOT` (o `EXCEPCION_CAMBIO_BOT` si decide saltárselo) fechado **después** del concepto
  ganador — un `CAMBIO_BOT` viejo no vale.
- Se mide el **cierre** (mensajes → ventas) después del cambio. **Gate duro a FASE 4
  (`PROHIBIDO_ESCALAR_CIERRE_BAJO`):** ≥ `min_mensajes_cierre` (30) mensajes tras el cambio y cierre
  ≥ `cierre_min_escalar_pct` (10%). El benchmark 15-20% es referencia, nunca bloquea. Bajo el piso,
  el producto se queda en FASE 3 para otra iteración; **nunca se sube presupuesto sobre un bot que
  no cierra**. Ante un cierre desplomado, verificar PRIMERO la consistencia física ad ↔ destino.

### FASE 4 — Escalado
- **1-1-7 CBO**: el creativo validado ×7, presupuesto en la campaña, siembra el PISO de la banda
  (15 USD/día) y se sube con +20% diario (surfing). Luego `1-7-7` si el inventario lo permite.
- Palancas: expansión horizontal por **Post ID**, **multicuenta**, **multi-fanpage**, subir precio,
  renovar creativos, microángulos (`etapa-3` produce 8-12 como banco de copy).
- **Exploración en paralelo (mini-F1):** 3 ángulos NUNCA probados, ABO, TODO IMAGEN, 2.99 USD/día
  por conjunto, medido por venta igual que F1. Solo arranca cuando `decidir.py` ya marca ESCALAR con
  volumen mínimo. Un ganador de la exploración entra a F2 por el mismo gate.
- **Reingreso a FASE 1** (excluyendo ángulos ya probados) cuando el ángulo se agota: evento
  `REINGRESO_F1`/`FATIGA_ANGULO`, o solo hay órdenes PAUSAR sin ningún ESCALAR/SEGUIR/RENOVAR.

---

## 6. EL MOTOR DE GRAFO: `flujo.py` + `DOCTRINA/FLUJO.json`

- `FLUJO.json` declara fases → nodos → `ejecutor` (operador / skill / subagente / script / mcp),
  `requiere` (lo necesario para ejecutar el nodo, bloqueante, con dueño) y `produce` (lo que lo da
  por cumplido), más `avisos` (no bloquean) y `salida`/`entrada`/`reingreso` con gates.
- Cada condición es un **predicado de un vocabulario cerrado** (`csv_campo`, `csv`, `glob`,
  `archivo`, `json`, `eventos`, `script`, `angulo_ganador`, `concepto_2de2`, `cierre_post_cambio_bot`,
  `decision`, `data_fresca`, `todos`/`alguno`/`no`…). Si un gate no cabe en ese vocabulario, no es un
  gate sino criterio y vive en el subagente.
- **Nodo cumplido** = todos sus `produce` pasan. **Nodo actual** = el primero que no. Se ejecuta ESE
  nodo y solo ese, con el ejecutor que declara. Los gates **no se reinterpretan en prosa**: si dice
  BLOQUEADO, se produce lo que falta (con el dueño que nombra) y se vuelve a correr.
- Comando de arranque de cada sesión: `python Ads/_TOOLS/flujo.py --todo --escribir` → deriva y
  escribe `PRODUCTOS/_ESTADO_FLUJO.csv`. (`_DIM_PRODUCTOS.fase` es solo bitácora.)
- **Los gates de entrada son candado, no aviso:** `gen_publicacion.py --fase N` y
  `registrar_evento.py --evento LANZAMIENTO` niegan la acción si `flujo.gate_entrada()` dice que el
  gate no se cumple; solo `--excepcion "motivo"` deja proceder y deja una fila `EXCEPCION` en
  `_EVENTOS.csv`.
- **Contrato de CLI:** `flujo.py`, `decidir.py`, `gen_grafo.py` son SOLO LECTURA por defecto. Un
  "mirar" nunca escribe; cada uno necesita `--escribir` explícito.
- Nodos del **ciclo diario** (`ciclo.datos`, `ciclo.motor`, `ciclo.ordenes`) y una excepción
  `PAUSADO` (producto pausado: no se audita ni se ordena nada hasta decisión explícita del operador
  con `cargar_estado.py --estado VIVO --motivo "..."`).

---

## 7. EL MOTOR DE DECISIÓN: `decidir.py`  (INVARIANTE 13)

**Ninguna orden de pausar o escalar se emite sin pasar por `decidir.py`.** Lee ventas (verdad:
`_FACT_VENTAS.csv`), gasto (verdad: Meta Graph API vía `gasto.py`; fallback LucidSales antes de
2026-09-06) y parámetros de `PRODUCTOS/_PARAMETROS_DECISION.csv`. Escribe `PRODUCTOS/_DECISIONES.json`
(solo con `--escribir`).

**Estados:** `ESCALAR` · `PAUSAR` · `RENOVAR` · `SEGUIR_MIDIENDO` (incluye `PAUSAR_DIFERIDA`).

**Reglas clave**
- Calcula el **IC 95% bayesiano del CPA** (distribución gamma). **El intervalo manda en las dos
  direcciones:** si cruza el BE no se apaga ni se sube fuerte; se emite `SEGUIR_MIDIENDO` y se dice
  "faltan ~N ventas" para resolver (tope `horizonte_ventas`=60). Cero parálisis: siempre hay una
  acción de menor riesgo.
- **Tres relojes distintos, nunca uno:** `ventana_dias`=14 (sobre cuántos días se calcula CPA e IC) ·
  `ventana_fatiga_dias`=3 (días recientes contra la ventana; debe ser estrictamente menor) ·
  `duracion_testeo_fase2_dias`=3 (cuánto rueda la 1-1-5). La **tolerancia 1× BE** se mide sobre el
  gasto **ACUMULADO** desde el lanzamiento, no sobre ventana móvil.
  > Lo que un mentor fija en días es **volumen de evidencia**, no tiempo: Calet decide en 3 días
  > porque corre a 15-18 USD/día y saca 20-30 ventas; a 3-6 USD/día esos 3 días son 1-3 ventas.
- **Detector de fatiga:** un ángulo con historia rentable (≥5 ventas acumuladas y CPA ≤ BE) que
  decae en los últimos 3 días → **RENOVAR el concepto**, nunca apagar el ángulo.
- **Matar por conversación:** con 0 ventas, si conversaciones/clic-en-enlace < 35% (con ≥30 clics en
  enlace) → PAUSAR sin esperar el PD. Se mide sobre `link_clicks` de `_FACT_ENTREGA_ANUNCIO.csv`,
  NO sobre clics totales de `_FACT_VENTAS.csv`.
- **Matar por ventas:** solo tras pasar el PD (1× BE) Y ≥3 días de maduración COD.
- **Máximo 2 pausas por producto por corrida** (las de mayor gasto primero); el resto queda
  `PAUSAR_DIFERIDA`. Un enlace caído (hook muerto) nunca se difiere.
- **Surfing:** +20% máximo, una vez por día, en la mañana. Es el tope que respeta quien ejecuta.
- **Frescura de datos:** se cuenta desde el último día CON DATA; si supera `rezago_max_dias` (2) o su
  edad es desconocida, **no se emite ninguna orden de ESCALAR** (bloqueante); PAUSAR sí sale, con aviso.
- **Nunca se sube presupuesto sobre una base inventada:** sin `daily_budget` real en el snapshot de
  Meta, la orden ESCALAR se bloquea.
- **Ejecutar una orden en Meta por MCP exige confirmación explícita del operador, orden por orden.**
  Después se verifica contra Meta y se anexa el evento a `_EVENTOS.csv`.
- `test_decidir.py` congela estas reglas.

---

## 8. LAS 15 ETAPAS (SUBAGENTES) Y LAS SKILLS

Cada etapa es un subagente real (`.claude/agents/ETAPA-*.md`), invocado por Task con su `name`.
14 corren con el modelo que elija el operador (`inherit`); `etapa-render` corre en Sonnet. Cada
subagente recibe SOLO los inputs que necesita (no el historial) y transfiere su output **completo**
a la siguiente (nunca resumido).

| Etapa | Rol |
|---|---|
| `etapa-producto` | Valida si el producto es apto para e-commerce de impulso (17 criterios). Veredicto APTO/NO APTO con score 0-1. Corre primero. |
| `etapa-0` | Clasifica N transcripciones por ángulo; selecciona los 6 mejores (1 por ángulo) por densidad de señales de compra. |
| `etapa-1` | Costeo: ejecuta `costear.py` → P1u/P2u/P3u, CPA objetivo y BE EXACTOS; decide arquitectura de oferta (1u vs 2x1). Las cifras salen del script, nunca de memoria. |
| `etapa-1b` | Analiza ingredientes y mina la VOZ DEL CLIENTE (Reddit, foros, reseñas) con búsqueda web; alimenta `_VOZ_CLIENTE.csv` vía `verificar_voz.py`. |
| `etapa-2` | Construye 6 fichas de ángulo (avatar 5 ejes, dolor, deseo, promesa, saturación, video asignado) y **asigna la FanPage** (reglas F1-F5). Elige además la imagen de referencia `ligera` fija de F1. |
| `etapa-3` | FASE 4: mapa de sub-dolores y 8-12 microángulos (banco de copy de la expansión). |
| `etapa-4` | Copys de Meta (6 en F1; copy único + 3 variaciones en F2; testimonio por microángulo en F4) y prompts de infografías del bot (`INFOGRAFIAS.md`). |
| `etapa-5` | Bloques de juicio del flujo LucidBot (`BLOQUES_BOT.md`): los 4 campos del catálogo, testimonios, audio, M2, FAQ. Bot paraguas en F1; A/B de flujo en F2; reescritura en F3. |
| `etapa-6` | Planificador de lanzamiento (modos F1/F2/F4). Dueño de la CONVENCIÓN DE NOMBRES y de la BANDA DE EDAD. Escribe `_PLAN*.json` (contrato `plan/1`). |
| `etapa-guardar-producto` | Escribe el paquete en `PRODUCTOS/<carpeta>/` y pasa el gate de reconciliación. |
| `etapa-7` | Monitor diario + motor de escalado; lee `_DECISIONES.json`, verifica integridad/confusores, ordena la palanca. **Solo lee y recomienda.** Mide por CPA, nunca ROAS. |
| `etapa-9` | Fábrica de conceptos: ≥6 ejecuciones/día desde 22 blueprints canónicos, balanceadas por rol de embudo; registra en `_DIM_CREATIVOS.csv`; alerta si una pieza `GENERADO` lleva >7 días sin `ad_id`. |
| `etapa-10` | Lector concepto↔métrica: por qué ganó lo que ganó; brief para etapa-9. |
| `etapa-11` | Optimizador de flujo: mide el CIERRE por ángulo, audita congruencia anuncio↔bot, diseña el A/B de flujo. Diagnostica en F2; la reescritura es F3. |
| `etapa-render` | Conduce el Chrome logueado del operador para renderizar imágenes en ChatGPT web (adjunta producto + referencia, descarga PNG con nombre canónico, corre el gate de calidad). |

**Skills (procedimientos):** `buscar-producto` (F0) · `fase-1-angulos` · `fase-2-conceptos` ·
`fase-3-flujo` · `fase-4-escalado` · `publicar-meta` · `recopilar-lucidsales` · `ciclo-diario` ·
`generar-conceptos` (banco de 111 piezas / 22 blueprints) · `generar-imagenes-chatgpt` ·
`reglas-sistema` (se precarga en los subagentes).

---

## 9. COSTEO, PRECIOS Y BREAK-EVEN

- **Nunca inventar cifras de costeo** (invariante 2). Salen de `Ads/_TOOLS/costear.py` sobre
  `PRODUCTOS/_DIM_COSTEO.csv` (GT) / `_DIM_COSTEO_CO.csv` (CO). Regla de fila: la más cercana al
  costo; **en empate, la superior** (conservador); nunca se interpola. En combos (2x1, 4x2) entra el
  costo del PEDIDO COMPLETO (2 frascos de Q45 → se pasa 90).
- **Jerarquía de precios:** 1º `_DIM_PRECIOS.csv` (lo que Dropi cobra de verdad, producto ya
  vendiendo) · 2º `_DIM_COSTEO.csv` vía `costear.py` (producto nuevo) · 3º tablas en prosa (solo
  lectura humana).
- **Derivación del BE:** `CPA_BE = CPA_BASE + UTILIDAD_ESPERADA`; `UTILIDAD_ESPERADA = (precio − suma
  de costos) × (1 − % devoluciones)`; la suma de costos incluye producto + envío + gastos + el CPA.
  El BE vigente (v4) se deriva de `_DIM_PRECIOS.csv` + `_TASA_ENTREGA.csv` con la **tasa de entrega
  PROPIA del producto**, sobre órdenes reales de Dropi; el valor de `_DIM_PRODUCTOS` es solo
  *fallback*. La tasa de entrega se verifica cada mes (ojo: el % de "entregado" de Dropi incluye
  pedidos en tránsito; la devolución importa sobre estados RESUELTOS).
- Escalera típica GT (ej. costo Q40 → 179/239/299). Cada mercado/producto tiene su escalera.
- **Moneda:** GT: costos en quetzales (Q), cuentas Meta en USD, tasa ≈ 7.62. CO: costos y precios en
  COP, tasa ≈ 3152.5 COP/USD (columnas `*_q` de esa fila están en COP).

---

## 10. CONTABILIDAD — «¿ESTOY GANANDO DINERO?» (`DOCTRINA/CONTABILIDAD.md`)

Negocio contra entrega: **cohorte ≠ caja**. Medido sobre ~356 órdenes: venta→entrega mediana 1 día;
venta→devolución confirmada 7 días; entrega→acreditación en cartera Dropi 1 día. La devolución
tarda 7× más, así que un cohorte joven se ve mejor de lo que es.

- **Regla de maduración:** un cohorte con menos de **10 días** es PRELIMINAR y no decide
  (`maduracion_dias`=10).
- **Tres vistas que NUNCA se mezclan:** A) **COHORTE** (por fecha de orden; única válida para decidir
  sobre campañas, siempre con % de maduración) · B) **CAJA** (por fecha del movimiento; libro de
  cartera de Dropi) · C) **COHORTE MADURO** (cierre definitivo mensual).
- **Estado de resultados, orden fijo:** venta bruta entregada − costo de producto − flete =
  **MARGEN LOGÍSTICO** (lo que Dropi llama "Ganancias"; **NO es la ganancia**) − devoluciones −
  personal − otros operativos = margen de contribución − publicidad = **MARGEN OPERATIVO** − gastos
  fijos = resultado neto. Confundir margen logístico con ganancia infla el resultado ~2×.
- Motor `gen_pl.py`; parámetros `PRODUCTOS/_PARAMETROS_FINANZAS.csv`. Hay conciliación contra banco
  y Dropi. (Banco: ver §16.)

---

## 11. DATOS: QUÉ CSV EXISTEN Y QUIÉN ES DUEÑO

Todos en `PRODUCTOS/`. **Los CSV se editan con un escritor CSV real, nunca a mano** (invariante 11;
campos con comas entre comillas). Un hook valida el CSV tras cada Write/Edit. Cinco tablas
(producto, estado_flujo, venta, entrega_conjunto_dia, entrega_anuncio_dia) tienen su verdad en
**Postgres** (`db/`), y el CSV es el espejo regenerado tras el commit; los eventos también se
escriben por Postgres (`raw.evento`). El resto de dimensiones se edita en CSV.

**Dimensiones (`_DIM_*`):** `PRODUCTOS` (llave `producto_key`; estado, fase-bitácora, cuenta, page_id,
moneda, tasa, costo, BE, mercado, campaign_id…) · `CONJUNTOS` (angulo_key, avatar_edad, réplicas) ·
`CREATIVOS` (conceptos y su estado PENDIENTE_GENERAR/GENERADO/PUBLICADO + `ad_id`) · `ANUNCIOS` y
`VOCABULARIO` (5 ejes) · `COSTEO`/`COSTEO_CO` · `PRECIOS` · `MERCADOS` · `FANPAGES` (10 páginas) ·
`CUENTAS` (MCP habilitado sí/no, moneda, solo GTR 7 admite media LOCAL_FILE) · `BANDAS` · `ENVASE`
(identidad física del producto; se DECLARA, nunca se adivina) · `FLUJO_BOT` · `REFERENCIA_F1` ·
`BM`, `TARJETAS`, `GASTOS`, `RETIROS` (finanzas).

**Hechos (`_FACT_*`):** `VENTAS` (LucidSales) · `ENTREGA` (por conjunto) · `ENTREGA_ANUNCIO`
(por anuncio, con los 5 ejes parseados y `link_clicks`) · `ORDENES_DROPI` · `CARTERA_DROPI` · `BANCO` ·
`SALDOS` · `FACTURACION` · `PAUTA_REAL` · `SEMANAL` · `TRANSFERENCIAS_FX`.

**Control y derivados:** `_EVENTOS.csv` (bitácora de todo cambio ejecutado: LANZAMIENTO,
CAMBIO_PRESUPUESTO, PAUSA, CAMBIO_BOT, CAMBIO_CREATIVO, REPLICA_MULTICUENTA, EXCEPCION…; **único
escritor `registrar_evento.py`**) · `_ESTADO_FLUJO.csv` (derivado) · `_DECISIONES.json` (derivado) ·
`_PARAMETROS_DECISION.csv`, `_PARAMETROS_PUBLICACION.csv`, `_PARAMETROS_FINANZAS.csv`,
`_PARAMETROS_OPTIMIZACION.csv` · `_VOZ_CLIENTE.csv` (cita textual + URL verificable, solo `etapa-1b`
vía `--agregar-json`) · `_APRENDIZAJES.csv` (priors VIGENTES con confianza ALTA/MEDIA/BAJA que las
etapas citan por `id`) · `_TESTEOS.csv` (tests declarados con `test_id`) · `_ALIAS_CONJUNTOS.csv`
(nombres viejos; el JOIN es por NOMBRE) · `_TASA_ENTREGA.csv` · `_CORRIDAS_DIARIAS.csv` (semáforo
VERDE/AMARILLO/ROJO de la corrida nocturna).

**Capa analítica:** `warehouse/` (dbt + DuckDB): staging + marts (`fct_gasto_dia`, `fct_conjunto_dia`,
`fct_anuncio_dia`, `dim_conjunto`) con tests de integridad. Lee los CSV; no los escribe.

**Por producto:** `PRODUCTOS/<carpeta>/` con archivos por rol (invariante 8): `1_HACER_MANUAL.txt`
(todo lo que el operador ejecuta a mano; se GENERA con `gen_manual.py`, nunca se tipea),
`2_DATA_PRODUCTO.txt` (memoria del producto), `3_CAMPAÑA_META.txt` (solo IDs de Meta),
`4_PLAN_ESCALADO.txt`, más `_PLAN.json`, `_PLAN_FASE2.json`, `_PLAN_FASE4.json`,
`_PLAN_EXPLORACION.json` (contrato `plan/1` validado por `gen_plan.py`), `BLOQUES_BOT.md`,
`INFOGRAFIAS.md`. La media va a `Ads/MEDIA_<PRODUCTO>/`; todo informe fechado a
`PRODUCTOS/_AUDITORIAS/` (registro histórico: **prohibido sacar métricas de ahí**, salen del CSV).

**`producto_key` es la llave del sistema** (invariante 10): las carpetas se resuelven leyendo
`_DIM_PRODUCTOS.csv`, nunca adivinando por el nombre.

---

## 12. EL BOT (LUCIDBOT) Y LAS INFOGRAFÍAS

- El flujo del bot **se declara, no se escribe**. Layout en `DOCTRINA/PLANTILLAS_FLUJO_BOT.md`;
  valores en `_DIM_FLUJO_BOT.csv` y `_DIM_MERCADOS.csv`; lo renderiza y bloquea
  `Ads/_TOOLS/gen_flujo_bot.py`. Tres notaciones: `{{variable}}` (sale de un CSV; **bloquea con
  exit 1 si falta**) · `<<BLOQUE:x>>` (lo escribe `etapa-5`) · una línea que empieza con `>>` es
  INSTRUCCIÓN y nunca se pega en el bot.
- Texto fijo no se reescribe por producto; los precios se derivan de `_DIM_PRECIOS.csv`; el mercado
  (GT/CO) es variable, no doctrina. Reglas A-G del orden del flujo en la plantilla.
- **Infografías del bot:** Info 1 (beneficios), Info 2 (uso), Info 3 (confianza) + opcionales
  (IMAGEN 4/5/6). Motor compartido en `PLANTILLAS_INFOGRAFIAS*.md`; prompts por producto en
  `INFOGRAFIAS.md` (los escribe `etapa-4`).
- **El bot paraguas** (un bot para los 6 ángulos) es herramienta de TESTEO (F1). A escala, un bot
  incongruente con el anuncio genera efecto rebote; por eso en F3 se reescribe hacia el ganador.
  Hipótesis pendiente de confirmar: el A/B de flujo paraguas-optimizado vs dedicado (`etapa-11`).
- **El cierre es la palanca más grande del sistema.** Dueño: `etapa-11`.

---

## 13. COMPLIANCE: DOS ZONAS CON REGLAS OPUESTAS

- **ADS (creativo + copy que Meta lee):** aplica el compliance de verbos/claims y el CPM de
  Andrómeda (ver `COPYWRITING_ADS.md`, `PLANTILLAS_ADS*.md`). Se cuidan claims, antes/después, sellos
  inventados, promesas de cura.
- **POST-CLIC (flujo LucidBot, audio, infografías del bot, testimonios):** Meta no lo lee. **Aquí la
  prioridad es CONVERSIÓN**: se permiten verbos persuasivos fuertes y las estadísticas del operador;
  NO suavizar. Único límite: no afirmar que cura una enfermedad grave nombrada.
- **Registros sanitarios:** los números de registro (`[REG_MSPAS]` / `[REG_FDA]`, valores en
  `PLANTILLAS_DEFAULTS_OPERADOR.md`) no se inventan. Un producto sin registro (ej. ÓVULOS en CO,
  `EN_TRAMITE`) **no muestra sello ni número** en ninguna pieza (ad, infografía ni bot).
- **Réplica del dispositivo del ganador:** los sellos y cifras del concepto validado se replican
  COMPLETOS; no se filtran.

---

## 14. PUBLICACIÓN EN META (SKILL `publicar-meta`)

- **Todo nace PAUSED.** El lanzamiento es **siempre al día siguiente a las 4 AM (UTC-6)**
  (invariante 7), nunca el mismo día.
- **El CSV no es evidencia del estado de Meta:** antes de crear, `ads_get_ad_entities` y volcar un
  snapshot (`Ads/_INGESTA/META/snapshot_<CUENTA>.json`, de hoy o ayer). Un CSV que dice "sin
  publicar" puede coexistir con una campaña gastando desde hace dos días.
- **Secuencia:** pre-flight (snapshot) → `gen_publicacion.py` regenera el paquete contra ese
  snapshot (deriva nombres, plata, bandas, llamadas; **bloquea** si falta algo) → ejecutar las
  llamadas MCP en orden → `verificar_publicacion.py --escribir` cierra el gate y **escribe los
  `ad_id`** en `_DIM_CREATIVOS.csv`. Después se activa (MCP con confirmación, o a mano) y se anexa el
  evento `LANZAMIENTO` con `registrar_evento.py`. Control D+1 de tracking (Meta vs LucidSales).
- **Reglas fijas** (ver memoria del operador): número de WhatsApp GT fijo, puja de volumen más alto,
  perfil de IG, el error #1815589 del CTA tiene tratamiento conocido. Config fija de cada conjunto en
  `CONFIG_META_FIJA` (`gen_lanzador.py`): objetivo TRAFFIC, optimización CONVERSATIONS, destino
  WHATSAPP, Advantage+ Audience OFF.
- **Cuentas:** la media local (`LOCAL_FILE`) solo sube en **GTR 7**. No todas las cuentas tienen MCP
  (GTR 13 y la cuenta externa de CO se pautan a mano). En FASE 2 el brazo C va en OTRA cuenta.
- **Escritura en Meta por MCP oficial** (no hay token propio de escritura): la app web lee/verifica y
  **avisa solo cuando hace falta Claude** (alerta `requiere_claude`, p. ej. anuncios "- Copia" que
  necesitan renombrarse por MCP).

### Convención de nombres (dueño: `etapa-6`; vale por MCP y a mano; invariante 12)
```
CAMPAÑA:  [CUENTA]_[PRODUCTO]_[FASE]_[YYYYMMDD]        GTR0_TINNIDROP_TEST_20260802
CONJUNTO: [CUENTA]_[PRODUCTO]_[ANGULO]_R[N]             GTR7_VARICOSE_MIEDO-CIRUGIA_R1
ANUNCIO:  [ANGULO]_[FORMATO]_[A|B] ~ [FIRMA]
F2:       campaña ..._CONCEPTOS-[A|B|C]_..., conjunto ..._[A|B|C][1|2], anuncio [CONCEPTO]_[VARIANTE]_[NN]
FIRMA:    [producto]|[angulo]|[concepto].[canonico]|NC[nivel]|[oferta]|[destino]
```
Reglas: (1) ningún parámetro configurable (banda, presupuesto) viaja en el nombre — va a
`_DIM_BANDAS.csv`; (2) el número de réplica `R[N]` **nunca se reutiliza**; (3) se renombra ANTES de
publicar — **prohibido publicar un "- Copia"**. Las réplicas `R[N]` se SUMAN, nunca se comparan. La
FIRMA (generada/parseada por `firma.py`, valores válidos en `_DIM_VOCABULARIO.csv`) lleva los 5 ejes
en el nombre porque el `ad_id` llegó corrupto en 2006/2475 filas históricas y el nombre es lo único
que sobrevive a cualquier export. Un `?` en la firma = eje sin llenar = deuda.

### Banda de edad
Se **deriva del `avatar_edad` del ángulo** (tabla única `bandas_edad.py`), con Advantage+ Audience
OFF, **idéntica entre réplicas** del mismo ángulo (si no, deja de ser réplica y es un experimento no
declarado; se declara en `_TESTEOS.csv`). Sin avatar de edad marcada: 18-65+. Si choca con la edad de
la página, manda la del avatar. Evidencia: banda 45-60 vendió a Q30.6 vs Q473.6 en la amplia.

---

## 15. EL CICLO DIARIO (POST-LANZAMIENTO)

1. **Recolección nocturna automática** (Task Scheduler → `ciclo_diario.py`): baja LucidSales por API
   (`bajar_lucidsales.py`), ingiere a `_FACT_VENTAS.csv` (`ingerir_lucidsales.py`), baja
   gasto/entrega de Meta, corre `ciclo_hoy.py` (dbt + `decidir.py` → `flujo.py --todo` → lanzador →
   app) y deja una fila VERDE/AMARILLO/ROJO en `_CORRIDAS_DIARIAS.csv`.
2. **Auditoría de la mañana** (skill `ciclo-diario`): por cada producto `VIVO` → tabla de
   `decidir.py` (SIEMPRE primero, pegada completa arriba del informe) → `etapa-7` (monitor +
   palancas) → `etapa-10` (por qué ganó) → `etapa-9` (fábrica diaria, en paralelo).
3. **Órdenes:** cada PAUSAR/ESCALAR/RENOVAR se ejecuta por MCP **con confirmación del operador, una
   por una**, se verifica contra Meta y se registra con `registrar_evento.py` (todo ESCALAR deja un
   `CAMBIO_PRESUPUESTO` con `--antes` y `--despues` en USD/día; el sistema rechaza subidas > surfing
   salvo `--forzar`). RENOVAR dispara etapa-10 → etapa-9.
4. **Colombia es MODO MANUAL:** la cuenta es EXTERNA (sin MCP): el operador entrega los exports de
   Meta y de LucidSales (ingesta con `ingerir_meta.py --producto`). Las ventas de la tienda CO pueden
   entrar solas de noche si existe `~/.config/lucidsales/co.env`.

---

## 16. MERCADOS

`PRODUCTOS/_DIM_MERCADOS.csv` + `mercado.py --producto PK` imprime el perfil: país, moneda, símbolo,
**persona** (voseo guatemalteco en GT; **tuteo neutro colombiano en CO**, nunca voseo), registro
sanitario, transportadoras, unidad geográfica. Toda doctrina que varíe por país lee de ahí. El mismo
método vale en ambos mercados; cada producto declara el suyo en la columna `mercado`. La tabla de
`costear.py` por defecto es la de GT; la de CO se carga aparte (`--mercado CO`).

---

## 17. LA APP WEB Y LAS VISTAS

- **`app/`** (backend Python/FastAPI, frontend React + Tailwind/shadcn): la pantalla del operador.
  Lee los contratos y dispara ejecutores declarados en `VISTAS/_MANIFIESTO.json`. Pantallas:
  Hoy, Productos, ProductoDetalle, NuevoProducto, Fase1/2/3/4, Órdenes, Resultados (+mensual),
  Trabajos, Salud, Ajustes, Guía. Fase 2 incluye galería de conceptos, "fabricar conceptos",
  "generar prompts", "marcar como generadas", "verificar publicada" y una tarjeta **"Necesita
  Claude"** que aparece solo cuando una tarea no la puede resolver la app.
- **`VISTAS/APP.html`** es el respaldo generado sin servidor (`gen_app.py`); también `FLUJO.html` y
  `LANZADOR.html`. Los regeneran los hooks. Se abren, no se leen.
- Hooks de `.claude/settings.json`: tras cada Write/Edit valida CSV y regenera dashboard
  (`hook_csv.py`); tras cada Bash corre un barrido; al iniciar sesión archiva auditorías. Otros
  hooks vigilan `FLUJO.json` (`flujo.py --validar`) y la Guía Madre (`verificar_guia_madre.py`, bloquea).

---

## 18. CALIDAD, EVALS Y GUARDAS

- **Pruebas:** casi cada herramienta tiene `test_*.py` que congela sus reglas (decidir, flujo,
  costear, gen_flujo_bot, gen_plan, gate_entrada, cli_solo_lectura, etc.).
- **`verificar_producto.py`** = gate de reconciliación (invariante 9): no se declara un producto
  completo hasta que costo, precio, dosis, proveedores, página y `campaign_id` coinciden entre
  archivos.
- **`verificar_guia_madre.py`:** la Guía Madre parametrizada (`GUIA_MADRE_PARAMETRIZADA.md`) es el
  "texto madre" con los parámetros enseñados en clases; un número de clase es el *envoltorio del
  presupuesto del mentor*: antes de copiarlo, preguntar de qué es envoltorio.
- **`gen_grafo.py`:** detecta huérfanos, rutas muertas y costo en tokens (`--comparar` antes/después).
- **`evals/`:** baseline de evals por etapa (fixtures congelados + asserts deterministas), requisito
  para podar prosa de los `ETAPA-*.md`.
- **Roadmap por compuertas (G0→G4) hacia un SaaS** (stack previsto Agent SDK + DBOS) en curso.

---

## 19. LOS 13 INVARIANTES (EL CÓDIGO LOS CITA POR NÚMERO; NO SE RENUMERAN)

1. El ganador se declara por **VENTA**, agregando por `angulo_key`; la conversación corta, nunca
   corona. No entrar a F2 sin ángulo ganador; a F3 sin concepto ganador 2 de 2; a F4 sin cierre
   ≥ `cierre_min_escalar_pct` medido después del `CAMBIO_BOT`.
2. Nunca inventar cifras de costeo (salen de `costear.py`).
3. Transferir siempre el output completo de cada etapa a la siguiente.
4. Si falta un input requerido: detener, indicando qué dato falta y en qué formato. Nunca asumir.
5. Congelar los inputs antes de arrancar; si cambian, rerun completo que sobrescribe y sube `VERSION`.
6. Mismo presupuesto en todos los conjuntos dentro de cada etapa.
7. Lanzamiento siempre al día siguiente, 4 AM.
8. Un producto = una carpeta con archivos por rol; prohibidos archivos sueltos de reruns.
9. Gate de reconciliación antes de cerrar un producto.
10. `producto_key` es la llave del sistema; las carpetas se resuelven leyendo `_DIM_PRODUCTOS.csv`.
11. Los CSV se editan con un escritor CSV real, nunca a mano.
12. Todo objeto de Meta se nombra con la convención de `ETAPA-6`; prohibido publicar un "- Copia";
    las réplicas `R[N]` se SUMAN.
13. Ninguna orden de pausar/escalar sin pasar por `decidir.py` (IC 95%, tres relojes, frescura de
    data, confirmación humana por orden).

---

## 20. FOTO DEL PORTAFOLIO (18-OCT-2026 — puede haber envejecido)

| Producto | Mercado | Estado | Cuenta | Nota |
|---|---|---|---|---|
| TINNIDROP | GT | VIVO (escalado) | GTR0 | Ganador por Post ID en 4 cuentas; BE ≈ Q93. Pendiente compliance (sellos/clínicos) antes de escalar fuerte. |
| NUSAVA B12 | GT | VIVO (escalado) | GTR7 | Se vende siempre en combo 2x1/4x2; ganadores MEMORIA / ARDOR. |
| CLEARSTEM | GT | VIVO (definición) | GTR13 (sin MCP) | Ángulo ganador por venta (ANTI_FALSIFICACION, RESISTENCIA_INSULINA_SOP); sin concepto 2/2 aún → no entra a F3. Se monitorea por LucidSales. |
| VARICOSE | GT | PAUSADO | GTR7 | Sin gasto desde ago; el envase del proveedor cambió; reingreso solo con decisión del operador y creativo nuevo. |
| ÓVULOS PURITY | CO | PAUSADO en CSV (lanzamiento F1 v2 en preparación) | EXTERNA (GTR3 en CSV) | COP, tuteo, sin registro sanitario → ninguna pieza muestra sello. Publicación manual. |
| GAFAS | CO | NUEVO | EXTERNA | Escalera 1u/2u, envío gratis, sin 3u; modo manual. |

---

## 21. CÓMO DEBE COMPORTARSE UNA IA QUE OPERE ESTE SISTEMA

**Con el método**
- Antes de cualquier skill de fase: correr (o pedir) `flujo.py [producto_key]` y ejecutar SOLO el
  nodo que devuelve. No reinterpretar gates en prosa.
- Si la IA no puede ejecutar código (como vos, sin carpeta), **debe decir qué comando correría y qué
  dato necesita**, y pedirle al operador el resultado. Nunca inventar el resultado de un script.
- Nunca inventar cifras (costos, BE, CPA, ventas). Si falta un dato: detener y pedirlo con su formato.
- Decidir pausar/escalar solo a partir de la salida de `decidir.py`. No juzgar "porque hoy no vendió".
- Un "0 ventas" no es veredicto antes del PD ni antes de ~3 días de maduración COD.
- Antes de tocar Meta: verificar contra Meta (snapshot), no contra el CSV.
- Nada en Meta sin confirmación del operador por cada orden.

**Con el operador (Juan)**
- Responder en español, **corto**: lo mínimo útil, ampliar solo si lo pide. Una pregunta a la vez.
- **Claude decide, el operador ejecuta:** con data suficiente hay que *decidir y recomendar*, no
  devolver la elección. Pero **preguntar no es autorizar**: no lanzar cambios al sistema sin un
  "hacelo" explícito.
- Si dice que una práctica del mentor "no funciona", primero comprobar que llegó a ejecutarse.
- Su terminal es PowerShell 5.1 en Windows: comandos de a uno, sin `&&`, sin rutas `/c/`.
- Si un agente choca un límite de uso, avisar; el operador lo restablece (no cambiar de modelo por
  cuenta propia).
- Convenciones de commits: conventional commits, sin atribución a IA.

**Con las reglas de contenido**
- Persona del texto según el mercado del producto (voseo GT / tuteo CO).
- Nunca sellos/registros inventados; nunca afirmar cura de enfermedad grave.
- En ads: compliance estricto. En bot/infografías del bot: conversión primero.

---

## 22. MAPA MENTAL DE UNA SESIÓN TÍPICA

```
1. Arranque:   flujo.py --todo --escribir  → "producto X está en nodo F2.conceptos, falta: 3 conceptos"
2. Skill:      se carga fase-2-conceptos (la que nombra el nodo)
3. Etapas:     etapa-9 (filas) → etapa-render (PNG en ChatGPT) → etapa-4∥etapa-5 → etapa-6 → guardar
4. Gate:       gen_publicacion.py --fase 2 (bloquea si falta algo) → publicar-meta (todo PAUSED)
5. Operador:   activa a las 4 AM; registrar_evento.py LANZAMIENTO
6. Cada día:   recolección → decidir.py → etapa-7/10/9 → órdenes confirmadas una a una → eventos
7. Transición: flujo.py detecta concepto_2de2 → F3 (reescribir bot → CAMBIO_BOT → medir cierre)
               → cierre ≥ piso → F4 (1-1-7 CBO + exploración) → ... → reingreso a F1 si se agota
```

---

## 23. LÍMITES DE ESTE DOCUMENTO (SÉ HONESTO CON ESTO)

- Resume la arquitectura y las reglas **vigentes al 18-oct-2026**; no incluye el texto íntegro de
  cada etapa, plantilla ni doctrina de mentores (viven en los archivos).
- Los números concretos (presupuestos, umbrales, BE, tasas) son los de esa fecha; sus dueños son
  `_PARAMETROS_*.csv`, `_DIM_*.csv` y `costear.py`. Si el operador te da un valor distinto, manda el
  del operador/CSV.
- Hay mucha historia de decisiones (fechas, incidentes, clases de mentores como Calet y Joaquín) en
  `_CONOCIMIENTO/POSTMORTEMS/`; ninguna etapa la necesita para ejecutar, y acá solo se cita lo que
  explica el porqué de una regla.
- Si algo de este texto contradice lo que te muestra el operador desde el sistema vivo, **gana el
  sistema vivo** y conviene avisarle que este documento quedó desactualizado.

---

## 24. BRIEF DE AUDITORÍA — PARA DECIDIR SI HACE FALTA UNA v2.0

**Qué pide el operador.** Que auditás el sistema completo y concluyas si conviene una versión 2.0
(rediseño/simplificación) o si basta con podar y corregir. Motivo declarado: "hemos trabajado
demasiado" — el sistema creció mucho y se sospecha complejidad acumulada.

**Dimensiones medidas (18-oct-2026)**
- 169 scripts Python en `Ads/_TOOLS/` (75 de ellos tests), 520 commits.
- Mayores: `gen_dashboard.py` 2576 líneas, `flujo.py` 1858, `app_html.py` 1626, `decidir.py` 1169,
  `gen_publicacion.py` 1121, `agrupar_canonicos.py` 1027, `gen_pl.py` 907.
- Doctrina en `DOCTRINA/`: ~377 KB de markdown. Prompts de las 15 etapas: ~228 KB (`ETAPA-6` 41 KB,
  `ETAPA-7` 22 KB, `ETAPA-5` 17 KB, `ETAPA-4` 17 KB, `ETAPA-1B` 16 KB). 49 CSV en `PRODUCTOS/`.
- Coste de contexto heredado (reporte `gen_grafo.py`): los "nodos dios" más pesados son
  `DATA_PLAYBOOK.md` (~14k tokens heredados), `PLANTILLAS_INFOGRAFIAS_FLUJO.md` (~11k),
  `PARAMETRIZACION_ADS.md` (~8k), `PLANTILLAS_FLUJO_BOT.md` (~8k), `COPYWRITING_ADS.md` (~7.5k).
- Hallazgos menores del propio sistema: `_DIM_REFERENCIA_F1.csv` sin consumidor; 2 rutas muertas en
  `test_armar_prompts_fase2.py`; `etapa-render` es la única etapa con modelo fijo (sonnet).

**Tensiones de diseño conocidas (candidatas a revisar, no verdades)**
1. **Fuentes de verdad duales:** 5 tablas con verdad en Postgres y espejo CSV, el resto en CSV
   editado a mano, más un warehouse dbt/DuckDB y varios JSON derivados. ¿Se justifica la mezcla?
2. **Tamaño de los prompts de etapa** (ETAPA-6 en especial) frente al principio "lo determinista va
   en código": ¿cuánta prosa debería migrar a scripts/CSV? Existe `evals/` como requisito previo
   para podar, y el roadmap G0→G4 ya lo prevé.
3. **Mezcla de dos mercados** (GT y CO) sobre una base pensada para GT: tabla de costeo, moneda,
   cuenta externa sin MCP, modo manual en CO. ¿Está bien abstraído o hay ramas especiales?
4. **Gates de FLUJO.json y estados derivados** (`_ESTADO_FLUJO.csv`, `_DIM_PRODUCTOS.fase` como
   bitácora): riesgo de divergencia entre lo que dice la bitácora, el flujo y la realidad en Meta.
5. **Escritura en Meta solo por MCP con confirmación orden por orden:** seguridad vs fricción; la app
   web avisa "Necesita Claude". ¿Se puede automatizar más sin perder control?
6. **Pocos datos por decisión:** presupuestos de 3-6 USD/día dan 1-3 ventas por celda; el diseño
   estadístico (IC bayesiano, agregación por `angulo_key`, replicación 2 de 2) compensa eso. ¿El
   método sigue siendo decidible a ese volumen?
7. **Dependencia de herramientas manuales:** LucidBot sin API, render de imágenes por navegador en
   ChatGPT web, transcripción con Gemini. Son los cuellos de botella operativos.

**Cómo auditar sin romper nada**
- Solo lectura. No proponer cambios a las reglas del §19 (invariantes) sin justificarlo con
  evidencia: el código las cita por número.
- Separar tres tipos de hallazgo: (a) **error o inconsistencia** (corregir ya), (b) **deuda/poda**
  (simplificar sin cambiar el método), (c) **rediseño** (cambia el método o la arquitectura →
  candidato a v2.0).
- Para cada hallazgo: evidencia concreta (archivo/regla), impacto, esfuerzo estimado y riesgo.
- Conclusión esperada: recomendación explícita **"v2.0 sí/no"**, qué conservar intacto (el método de
  4 fases, el motor `decidir.py`, el principio un-dato-un-dueño), qué eliminar y en qué orden.
