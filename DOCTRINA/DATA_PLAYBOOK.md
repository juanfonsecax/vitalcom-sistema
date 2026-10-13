# DATA_PLAYBOOK — LA CAPA DE DATA (fuente única)

> **Qué es esto:** cómo está organizada la data del sistema, qué rol cumple cada archivo, cómo se lee
> sin sacar cifras falsas y cómo se calcula la ganancia.
>
> **Regla madre:** los números viven en los CSV. **Prohibido hardcodearlos en un script o en prosa**
> — dos fuentes de verdad para el mismo número = drift garantizado. Por eso este archivo no lista
> cifras vigentes: dice dónde están.

---

## 1. LOS ARCHIVOS Y SU ROL (no confundir)

Todos viven en `PRODUCTOS/`. Siete son **espejo de Postgres** (`_FACT_VENTAS.csv`, `_FACT_ENTREGA.csv`,
`_FACT_ENTREGA_ANUNCIO.csv`, `_EVENTOS.csv`, `_DECISIONES.json`, `_ESTADO_FLUJO.csv`,
`_DIM_PRODUCTOS.csv`): se escriben solo con sus escritores de `Ads/_TOOLS/` y `db/`; un cambio a mano
frena la corrida nocturna (guardia de drift). El resto se edita con un escritor CSV real
(invariante 11).

### `_FACT_VENTAS.csv` — HECHOS DE VENTA (capa máquina)
Solo LucidSales. **La ÚNICA que suma al P&L.** De acá, y SOLO de acá, salen el CPA, la tendencia y la
ganancia. Prohibido reconstruir métricas leyendo auditorías en prosa.
- `rol_ventana` = **BASE** (no solapa con otra BASE → suma) o **CONTROL** (solapa a propósito, ej. un
  export de verificación → solo verifica, **NUNCA suma**). Las BASE no se solapan:
  `ventana_ini = ventana_fin de la última BASE + 1 día`.
- **Sin columnas derivadas:** el CPA y el cierre se CALCULAN siempre, nunca se leen.
- **`ad_id`** — el `adId` de LucidSales, la identidad real de la fila; es lo que prueba que no hay
  doble conteo. Va vacía solo en las filas sintéticas de cuadre.
- **Filas sintéticas de cuadre:** el detalle de LucidSales suma MENOS que su bloque `Resumen` (no
  atribuye toda venta a un ad). La diferencia se carga como filas con `conjunto`/`anuncio` vacíos,
  `spend_usd`=0 y `ad_id` vacío, para que el P&L cuadre con el total real. Son legítimas y NO se les
  inventa un `ad_id`.

### `_FACT_ENTREGA.csv` y `_FACT_ENTREGA_ANUNCIO.csv` — HECHOS DE ENTREGA (capa máquina)
Solo Meta: mensajes, clics, impresiones, gasto, `pct_conv_clic_enlace`. **No tienen columnas de venta:
sumarlas al P&L es imposible, no solo prohibido.**
- El `conjunto` de `_FACT_ENTREGA.csv` viene **sin el prefijo `[CUENTA]_[PRODUCTO]_`** (la cuenta y el
  producto van en sus columnas) y a veces **sin tildes ni eñes**. El mismo objeto de Meta aparece así
  con dos grafías. **La solución NO es normalizar la llave:** es anexar la grafía que falta a
  `_DIM_CONJUNTOS.csv` con el MISMO `angulo_key`.
- **`conjunto = "(campaña completa)"`** es gasto real de una campaña que Meta no desglosó por
  conjunto. **Nunca se le inventa un `angulo_key`:** se excluye del análisis por ángulo y se reporta
  aparte.
- **`_FACT_ENTREGA_ANUNCIO.csv` lleva `ad_id`** para unir con `_FACT_VENTAS.csv` por id y no por
  nombre (un renombrado en Meta rompe el JOIN por nombre). Una fila sin `ad_id` lo trae en `""`, nunca
  inventado. Con fuente `MetaAPI-directo`, `mensajes` sale de las conversaciones reales de mensajería
  (`actions`); la derivación por clics vive solo para los exports de Ads Manager, que no traen `actions`.

### `_FACT_CARTERA_DROPI.csv` — LA BILLETERA DE DROPI (capa máquina)
El libro de caja de Dropi: una fila por movimiento (ID único, UPSERT, quetzales, con el saldo después
del movimiento). Lo escribe solo `Ads/_TOOLS/ingerir_cartera.py` (mira por defecto, `--escribir` para
guardar). Da el costo REAL de cada devolución en los meses que cubre desde su primer día y los retiros
de la billetera, que se clasifican al LEER con `_DIM_RETIROS.csv` (`TRANSFERENCIA_PROPIA`,
`RETIRO_PERSONAL`; lo que ninguna regla calza es `SIN_CLASIFICAR` y se lista, nunca se adivina). Son
movimientos de caja: no tocan el resultado.

### Precedencia por fuente en `_FACT_ENTREGA*.csv`
Para una misma cuenta y un mismo día manda `MetaAPI-directo`: las filas de otras fuentes (export de Ads
Manager, MCP) que la API cubre por completo se eliminan al guardar y no se suman al leer
(`upsert_fact.superar_por_api_directa`, `gasto.py`, espejo en `warehouse/macros/entrega_con_superada.sql`).
`Ads/_TOOLS/reconciliar_entrega.py` la aplica al histórico (`--escribir`). El gasto de LucidSales solo
cuenta donde Meta no llega: una venta cuya ventana Meta cubre entera conserva sus ventas y aporta gasto 0.

### `_FACT_ORDENES_DROPI.csv` y `_FACT_BANCO.csv` — HECHOS DE FINANZAS (capa máquina)
Lo que el estado de resultados mensual lee: las órdenes de Dropi (quetzales, una fila por ID, UPSERT:
el export más nuevo pisa estatus y montos y las órdenes que ya no trae se conservan) y los
movimientos del banco (moneda de la cuenta, salidas y depósitos, dedupe por banco + cuenta + fecha +
nombre + monto + saldo). Se escriben solo con `Ads/_TOOLS/ingerir_dropi.py` e
`Ads/_TOOLS/ingerir_banco.py`, que miran por defecto y necesitan `--escribir`; el banco valida el
extracto contra su propio resumen antes de escribir. No son espejo de Postgres.

### `_DIM_CONJUNTOS.csv` — DIMENSIONES (capa máquina)
Traduce el nombre crudo del conjunto en Meta a la semántica del sistema: `angulo_key`, avatar, dolor,
formato, `tipo_hook`, nivel de conciencia, rol de embudo, si el ad lleva precio. **Es lo que convierte
"cuánto gasté" en "POR QUÉ funciona".**

**Campos de vocabulario CERRADO** — los declara `etapa-2` en su ficha de ángulo y los escribe
`etapa-guardar-producto`:

| Campo | Valores permitidos |
|---|---|
| `avatar_genero` | MUJER · HOMBRE · MIXTO |
| `avatar_edad` | 25-35 · 35-45 · 45-60 · 60+ — el bucket **DOMINANTE**, no el rango completo |
| `emocion_dominante` | MIEDO_FUTURO · VERGUENZA · RESIGNACION · FRUSTRACION_MEDICA · DESCONFIANZA · AGOTAMIENTO · CURIOSIDAD |
| `nivel_conciencia` | 1 · 2 · 3A · 3B (`3` a secas es ambiguo y bloquea `gen_flujo_bot.py`) |
| `concepto_key` | C1_OFERTA · C2_BENEFICIOS · C3_SINTOMA · C4_TRANSFORMACION · C5_PRUEBA · C7_DESEO · C8_PROGRESION · C9_COMPARACION · SIN_CLASIFICAR |

> **Diccionario de emociones:** MIEDO_FUTURO = teme que empeore o sea irreversible · VERGUENZA = lo
> esconde de los demás · RESIGNACION = ya se rindió · FRUSTRACION_MEDICA = pagó especialistas y sigue
> igual · DESCONFIANZA = teme que sea falso o no funcione · AGOTAMIENTO = cansado, sin energía ·
> CURIOSIDAD = no sabía que su problema tenía esa causa (educacional / mecanismo).

- **El ÁNGULO dice por qué duele; el CONCEPTO, cómo se muestra.** Son ortogonales. Dueño del catálogo
  de conceptos: `Ads/_SWIPE/_CATALOGO_CONCEPTOS.md` (no se duplican las definiciones acá).
- **Dónde vive el `concepto_key` según la fase:** en FASE 1 es `C2_BENEFICIOS` en los 6 conjuntos (la
  constante, porque se mide el ángulo) y va en `_DIM_CONJUNTOS.csv`. En FASE 2 el ángulo es constante
  y el concepto distingue **ANUNCIOS**, así que se registra en **`_DIM_CREATIVOS.csv`**. Las filas
  históricas sin clasificar quedan en `SIN_CLASIFICAR`: no se retroclasifican de memoria.
- **Por qué vocabulario cerrado:** el texto libre no se agrega. Con estos campos la investigación de
  avatar se contrasta contra quién compró y se transfiere entre productos (si la vergüenza vende en
  várices, se prueba vergüenza en acné). Con Andrómeda el creativo es el targeting: medir a quién
  retrata es la única forma de saber a quién se le habla.
- **Ejes que NO se guardan como categoría:** `deseo`, `miedos`, `frustraciones` y el banco de tipos
  de ángulo. Cada eje nuevo fragmenta una muestra chica en celdas de 1-3 ventas (ruido). Siguen en
  `2_DATA_PRODUCTO.txt` como prosa para escribir el copy.
- **Llave = `conjunto_meta` EXACTO como quedó en Meta**, sufijos incluidos. No normalizar. Dos nombres
  del mismo ángulo = dos filas con el MISMO `angulo_key`.
- **Agregar SIEMPRE por `angulo_key`**, nunca por `conjunto`.
- La escribe `etapa-guardar-producto` al cerrar cada fase. **El JOIN debe cerrar al 100 %:** una fila
  de datos sin dimensión es un hueco de tracking, se reporta y se corrige — nunca se descarta el dato.

### `_DIM_CREATIVOS.csv` — CREATIVOS Y SU CICLO DE VIDA
Cierra el loop de la fábrica (`etapa-9`) con el lector (`etapa-10`).

| Campo | Valores |
|---|---|
| `estado` | `PENDIENTE_GENERAR` → `GENERADO` (el archivo existe en `Ads/MEDIA_[PRODUCTO]/`) → `PUBLICADO` (existe en Meta con su `ad_id`) → `RETIRADO` |
| `brazo` | A · B · C1 · C2 · (vacío fuera de FASE 2) |
| `id_tanda` | `[PRODUCTO]-T[NN]` — la tanda de 10 conceptos |
| `estado_entrega` | ENTREGADO · **SIN_ENTREGA** · (vacío si no aplica) |
| `rol_embudo` | TOFU · MOFU · BOFU (viene del blueprint) |

- **Una fila en `PENDIENTE_GENERAR` o `GENERADO` por más de 7 días es una alerta**, no una fila
  silenciosa: sin ella la fábrica produce para el disco duro.
- **`SIN_ENTREGA`:** en un `1-1-N` Meta reparte desigual y un anuncio puede terminar con casi cero
  gasto. **No es perdedor: no fue testeado.**

  ```
  reparto esperado = presupuesto del conjunto ÷ n.º de anuncios
  gasto acumulado < 30 % del esperado  ->  estado_entrega = SIN_ENTREGA
  ```

  Queda fuera del ranking (no se corona ni se mata) y se relanza en la tanda siguiente.
- **Lectura de FASE 2 — replicación:** el veredicto de un concepto nunca sale de una sola aparición.
  `2 de 2 arriba` = GANADOR · `1 de 2` = RUIDO (se repite) · `0 entregas` = `SIN_ENTREGA`. El `%PD` se
  calcula **sumando el gasto de las 2 apariciones** del mismo `concepto_key` + variante, nunca por
  conjunto. Aritmética en `DOCTRINA/CALENDARIO_ESCALADO.md` §1.7.4.

### `_EVENTOS.csv` — LOG DE ACCIONES (espejo de Postgres)
Qué se lanzó, pausó, escaló o cambió, y cuándo. La `fecha` del LANZAMIENTO es el reloj propio de cada
conjunto (por eso se puede lanzar entre semana). `CAMBIO_BOT` y `CAMBIO_CREATIVO` son variables de
confusión: si hay uno en la ventana leída, se declara y el resultado no se atribuye al ángulo.
**Todo cambio de flujo se registra el día que se aplica** con `Ads/_TOOLS/registrar_evento.py`; un
cambio sin evento es un cambio que el sistema no puede evaluar.

### `_APRENDIZAJES.csv` — MEMORIA TRANSVERSAL
Lo que el sistema ya aprendió y no debe volver a pagar para descubrir.
- Son DATA, no instrucciones: no viven hardcodeadas en el prompt de ninguna etapa.
- Filtro de lectura: `estado=VIGENTE AND (alcance=GLOBAL OR producto_key=[X]) AND '[agente]' IN
  consumido_por`. En filas anteriores al 24-sep-2026, `etapa-8` equivale a `etapa-7` (fusionadas).
- Se propone una fila cuando un patrón se repite en ≥2 ventanas o ≥2 productos.
- `confianza` ALTA = restricción dura · MEDIA = prior fuerte, se puede contradecir justificando ·
  BAJA / EN_OBSERVACION = solo seguir midiendo. **Un aprendizaje BAJA nunca justifica cambiar una
  regla del sistema.**
- Todo aprendizaje lleva `revisar_despues_de`. Uno contradicho NO se borra: pasa a
  `estado=SUPERSEDIDO` y se crea el que lo reemplaza.

### `_BITACORA_DATA.txt` — CONTROL DE INTEGRIDAD
Qué días entró data y cuáles faltan. Con días 🔴 en la ventana: NO presentar CPA como completo, NO
declarar ganador, NO matar por ventas. **Data faltante ≠ cero ventas.**

### `_GANANCIAS.txt` — LOG HISTÓRICO LEGIBLE
Una línea por día o ventana, más las notas de decisión que valga la pena conservar. Corto: últimos 30
días, lo viejo colapsado a resumen mensual.

### CAPA DE FACTURACIÓN — ¿lo que Meta COBRA = lo que Meta dice que GASTÉ?
Cadencia **semanal**. Responde dos preguntas que suelen mezclarse.

- `_DIM_BM.csv` — Business Manager → cuentas. La tarjeta vive a nivel **BM** y paga cualquiera de sus
  cuentas: la conciliación bancaria se hace por BM y adentro se reparte por gasto devengado.
- `_DIM_TARJETAS.csv` — tarjeta (últimos 4) → BM, con cobros, rechazos y veredicto (SANA · LEVE ·
  INTERMITENTE · MUERTA). Se completa con cada extracto. **Nunca atribuir una tarjeta a una cuenta
  por descarte** (APR-030).
- `_FACT_FACTURACION.csv` — un cargo por fila (COBRO / RECHAZO / CREDITO).
  `_FACT_FACTURACION_AGREGADO.csv` — fallback por ventana cuando solo hay el total por cuenta.
- `_FACT_SALDOS.csv` — saldo gastado y aún NO facturado al corte. Sin él no hay conciliación.
- `_FACT_PAUTA_REAL.csv` — gasto trackeado (LucidSales) vs gasto real (lo que cobra Meta).

**LA ECUACIÓN (única comparación válida):**
```
cobros_del_periodo − saldo_sin_facturar_INICIAL + saldo_sin_facturar_FINAL = gasto_devengado
```
Meta cobra al cruzar umbrales de gasto acumulado o en la fecha fija mensual, no por día: comparar
"gasté del 1 al 15" contra "me cobraron del 1 al 15" **siempre** descuadra y **no es evidencia de
sobrecobro** (APR-025).

**Regla dura de método:** si el saldo inicial es ESTIMADO (despejado de la propia ecuación), la
ecuación cierra por construcción y no verifica nada. Solo verifica con el saldo inicial OBSERVADO en
el corte anterior: por eso se guarda el saldo de cada cuenta en **cada** corte.

| | Pregunta | Qué la responde |
|---|---|---|
| **A** | ¿Meta me cobra de más? | la ecuación de arrastre |
| **B** | ¿Todo lo que me cobran está en mi P&L? | cobertura = gasto trackeado ÷ gasto real |

El riesgo grande suele ser B: gasto que Meta cobra y LucidSales no reporta **infla la ganancia** sin
que se vea. Mientras la cobertura no sea ~100 %, la ganancia está sobreestimada en esa diferencia.

**Corre con:** `python Ads/_TOOLS/conciliar_facturacion.py [ini] [fin]` → escribe
`_AUDITORIAS/_CONCILIACION_[YYYYMMDD].txt`. Ningún número se escribe a mano.

### `_ESTADO_META.csv` — QUÉ ESTÁ ENCENDIDO (declarado, no inferido)
Una fila por campaña: `cuenta_alias · campana · producto_key · estado (ON/OFF) · conjuntos_activos ·
fecha_confirmado · fuente`. **Manda sobre cualquier inferencia:** la data de ventas va días atrás y en
las cuentas sin MCP no hay nada que leer. Sin el archivo, `gen_dashboard.py` cae al fallback de "gastó
en el último día".

### Tablas de referencia
- `_DIM_PRECIOS.csv` — la escalera de precios por producto × unidades (manda Dropi).
- `_TASA_ENTREGA.csv` — parámetros de logística, mensual.
- `_DIM_PRODUCTOS.csv` — break-even, CPA Base, tasa **y el MAPA DE CARPETAS** (§1.1).
- `_DIM_COSTEO.csv` — tabla de costeo de GT; la usa `etapa-1` para costear un producto nuevo.
- `_MAPEO_CREATIVOS.csv` — **HISTÓRICO, congelado.** No lo lee ninguna etapa ni se escribe más; se
  conserva porque es la única fuente que ata media concreta a ventas antes de `_DIM_CREATIVOS.csv`.

---

## 1.1 MAPA DE CARPETAS — `producto_key` ↔ filesystem

El mismo producto vive en varios lugares del disco con nombres distintos. **`_DIM_PRODUCTOS.csv` es
el traductor**: cinco columnas resuelven cualquier ruta desde el `producto_key`.

| Columna | Apunta a |
|---|---|
| `slug_carpeta` | `PRODUCTOS/[X]/` |
| `carpeta_videos` | `Ads/1.1 Videos/[X]/` |
| `carpeta_transcripciones` | `Ads/1.2 Transcripcion videos/[X]/` |
| `carpeta_media` | `Ads/[X]/` (creativos lavados y ads-imagen) |
| `carpetas_extra` | sub-lotes y casos especiales |

- **Nunca adivinar la carpeta de un producto por su nombre** (invariante 10).
- **`producto_key` es la llave y no cambia nunca.**
- La fila la crea `Ads/_TOOLS/alta_producto.py` con las 5 columnas resueltas. Ningún dato de esa fila
  se escribe a mano: cada uno tiene su escritor en `Ads/_TOOLS/` (`cargar*.py`, `cambiar_costo.py`).
- **Las carpetas NO se renombran para "emparejarlas":** los manuales de producto referencian rutas
  `MEDIA_*`; la tabla hace el mismo trabajo sin tocar un byte.

### 1.1b — Y también resuelve la campaña

| Columna | Para qué |
|---|---|
| `clave_campana` | el texto a buscar en los nombres de campaña de Meta |
| `campaign_id` | el `campaign_id` conocido, o `PENDIENTE` / `SIN_MCP` |

> **REGLA DE BÚSQUEDA DE CAMPAÑA:** nunca fijar el `campaign_id` a ciegas. Listar las campañas de la
> cuenta y tomar la ACTIVE cuyo nombre contenga `clave_campana` **con gasto > 0**. El `campaign_id` de
> la tabla es una pista, no la verdad.

---

## 2. LA CAPA HUMANA

La pantalla del operador es la app web (`app/`); su respaldo sin servidor es `VISTAS/APP.html`. El
`_DASHBOARD.html` de `gen_dashboard.py` cubre el mercado GT.
- **Se GENERAN, nunca se escriben a mano:** ningún número está tipeado, por eso no pueden
  desincronizarse de la data. Regenerarlos es el último paso de la corrida nocturna.
- **Todo lo que el operador tenga que EJECUTAR va en la pantalla, no en prosa.** Si una acción se
  repite y el motor no la captura, la regla se agrega al script para que salga sola — nunca se
  escribe a mano en el HTML.

---

## 3. CÓMO LEER LA DATA — REGLAS OBLIGATORIAS

**(a) Solo las filas `rol_ventana = BASE` de `_FACT_VENTAS.csv` suman.** Las CONTROL verifican. Las
tablas de entrega nunca se suman al P&L.

**(b) Agregar por `producto_key`**, nunca por `producto`: el nombre crudo de LucidSales parte el mismo
producto en varios.

**(c) EL GASTO = Meta.** El `spend_usd` de `_FACT_VENTAS.csv` a veces queda congelado por debajo del
gasto real. Todo consumidor de CPA pasa por `Ads/_TOOLS/gasto.py` (regla de join en su docstring) —
nunca lee `spend_usd` directo.

**(d) EL CIERRE SE CALCULA, NUNCA SE LEE — y se agrega por `angulo_key`.**
```
cierre = Σ ventas ÷ Σ mensajes        (filas BASE, agregadas por angulo_key)
```
Es el KPI que gobierna `etapa-11`.
- **Ratio de sumas, nunca promedio de ratios.** Lo mismo para `%conv/clic-enlace`:
  `Σmensajes ÷ Σlink_clicks`.
- **Por `angulo_key`, jamás por conjunto-semana:** con 1-3 ventas el IC de Poisson es ±113-196 %.
  Piso de evidencia de `etapa-11`: ≥60 mensajes y ≥5 ventas por ángulo.
- **Semanal, nunca diario** — igual que el CPA.
- **Cierre ≠ venta cobrada.** Una venta COD que se devuelve no es venta: el cierre y la tasa de
  entrega no se mezclan (`_TASA_ENTREGA.csv` · `DOCTRINA/CONTABILIDAD.md`).

**UN SOLO ESCRITOR por tabla.** La cadena nocturna (`Ads/_TOOLS/ciclo_hoy.py`) es la única tarea
programada que ingiere. No crear una segunda tarea equivalente: la misma noche entraría dos veces.

**VENTANA DE LIQUIDACIÓN, no append-only puro.** El gasto o las ventas de un día a veces llegan
congelados a medio día. `bajar_meta_insights.py` e `ingerir_lucidsales.py` re-consultan los últimos
`upsert_fact.SETTLEMENT_WINDOW_DIAS` días cada noche y hacen **UPSERT** por llave natural
(`Ads/_TOOLS/upsert_fact.py`). `rol_ventana` viaja en la llave: CONTROL nunca reemplaza a BASE ni
viceversa.

---

## 4. FÓRMULA OFICIAL DE GANANCIA (TICKET REAL)

La que manda es `DOCTRINA/CONTABILIDAD.md`; esta es su forma por venta.

```
ganancia = Σ contribución de cada venta − pauta

contribución = TE × (precio − costo proveedor − flete − admin − otros)
             − (1−TE) × costo del evento de devolución
```
La contribución sale del **escalón** en que cayó ese pedido (cuenta quetzales, no ventas: un pedido
de 3 unidades no vale lo mismo que uno de 1).

- **La escalera vive en `_DIM_PRECIOS.csv`** y es flexible por producto: los baratos pueden arrancar
  en 2x1. No forzar 1/2/3/4 para todos.
- **Los parámetros de logística viven en `_TASA_ENTREGA.csv`** (`pct_entrega_resueltos`,
  `costo_devolucion_evento_q`, `costos_admin_q`, `otros_gastos_q`). Se cambian ahí y todo recalcula.
- **La tasa de entrega es POR PRODUCTO:** la columna `producto_key` de `_TASA_ENTREGA.csv`; `GLOBAL`
  es el fallback. Se usa la tasa propia cuando el producto tiene ≥20 órdenes resueltas. La fila
  global vigente se elige por **más órdenes resueltas, no por fecha**. Un producto que devuelve mucho
  **no se escala sin atacar la devolución primero**.
- **La tasa de entrega se calcula sobre estados RESUELTOS.** El % «ENTREGADO» de Dropi es sobre el
  total e incluye pedidos en tránsito: leído como tasa, subestima el negocio.
- **Unidades por pedido = se INFIEREN del ticket**, interpolando sobre la escalera.
- **Nunca presentar la contribución BRUTA como "ganancia"** (sin flete, admin ni devolución).
- El costo de devolución no aparece en la orden de Dropi: se cobra aparte en el estado de cuenta.

### Break-Even
**Se DERIVA de `_DIM_PRECIOS.csv` + `_TASA_ENTREGA.csv`.** El valor de `_DIM_PRODUCTOS.csv` es
fallback; el script recalcula el ponderado real desde el mix vendido. **Las cifras vigentes se leen
del CSV, no de acá.** Los productos en combo se costean por el PEDIDO, no por la unidad.

---

## 4.1 LAS DOS FUENTES DE VENTA — NO SON SUSTITUTOS Y NUNCA SE SUMAN

| | **LUCIDSALES** | **DROPI** |
|---|---|---|
| Qué es | venta **ATRIBUIDA a un ad** | venta **REAL Y COBRADA** + estado de entrega |
| Sirve para | CPA, ranking de ángulos, decidir qué apagar o escalar | P&L, tasa de entrega, economía unitaria |
| No ve | lo orgánico, el recontacto, el remarketing | de qué anuncio vino la venta |
| Grano | fila por `adId` | fila por orden |

Un P&L construido solo sobre LucidSales **subestima** (no ve las ventas sin anuncio atribuido).

- **PROHIBIDO cruzar Dropi con LucidSales día contra día.** La `FECHA` de Dropi es la de CARGA EN LOTE,
  no la de la venta: los días en cero entre lotes no son días sin ventas. Solo se comparan por
  acumulado.
- **La columna `GANANCIA` de Dropi NO es el P&L:** solo se llena en `ENTREGADO` (va días atrasada) y
  es margen bruto, sin admin, devoluciones ni pauta. El P&L válido es el de §4.
- **La demora de carga a Dropi es un costo real:** en contraentrega el cliente se enfría y sube la
  devolución. **Cargar diario.**

## 4.2 AUDITORÍA DE INTEGRIDAD — CÓMO PROBAR QUE NO HAY DOBLE CONTEO

Antes de cargar un export que pueda solapar:

1. **Solapamiento entre BASE:** las ventanas BASE deben ser contiguas y disjuntas. Cualquier solape es
   doble conteo directo.
2. **Filas 100 % idénticas:** revisar. Las ventas sin ad atribuido (conjunto vacío, spend 0, 1 venta)
   se ven idénticas y son legítimas: tienen `adId` distintos.
3. **Llaves repetidas:** LucidSales emite una fila por `adId`. Repetición ≠ duplicado.
4. **Contra un CONTROL más largo:** en cada celda `(producto, conjunto)` el CONTROL solo puede ser ≥
  la suma de las BASE. Si alguna sale al revés, ahí está el doble conteo.

> La columna `ad_id` hace automáticas las pruebas 2 y 3:
> ```
> # 0 resultados = no hay doble conteo
> repetidas = Counter((ventana_ini, ventana_fin, fuente, ad_id) for filas BASE con ad_id)
> comunes   = adIds(fuente=A) & adIds(fuente=B)   # universos disjuntos => ambas suman
> ```

**Todo export que solape con una BASE existente entra como `CONTROL`, nunca como BASE.** Un agregado
de N días no se descompone en sus días: si se necesita un tramo, se pide ese tramo exacto.

---

## 5. CADENCIA Y MONEDAS

**Cadencia:** LucidSales se baja por API cada noche (skill `recopilar-lucidsales`) y Meta por
`bajar_meta_insights.py`, dentro de la cadena nocturna. Colombia corre en modo manual: el operador
entrega los exports (skill `recopilar-lucidsales`, «MERCADO CO (MANUAL)»). La facturación es semanal
y el extracto bancario mensual; al cerrar cada corte se guarda el saldo sin facturar de cada cuenta en
`_FACT_SALDOS.csv` con `estado=OBSERVADO`.

> **Histórico de dos bots:** hasta el 16-ago-2026 inclusive hubo dos cuentas de LucidSales
> (`LucidSales` y `LucidSales_CuentaB`): son universos disjuntos y **ambas suman** (APR-021). No se
> borran ni se fusionan. Al comparar tramos que cruzan esa fecha, declararlo.

**Monedas:** `spend`, `costPerMessage` y `costPerSale` → USD · `total` (venta) → moneda del mercado del
producto (`python Ads/_TOOLS/mercado.py --producto PRODUCTO_KEY`).
> Una cuenta que factura en otra moneda (ej. CP1 en COP) se normaliza a USD en la ingesta, con la tasa
> de su código (`TASA_COP_USD`, APR-028). **Nunca sumar un gasto sin normalizar:** un día en pesos
> leído como dólares infla el gasto y vuelve basura el CPA del portafolio.

---

## 6. LOS TESTS DEL MOTOR — UN SOLO COMANDO

```bash
python -m pytest Ads/_TOOLS            # todos los test_*.py del motor
python -m pytest Ads/_TOOLS -k decidir # uno solo
```

Cada `test_*.py` corre como script y pasa solo si sale con código 0 (`Ads/_TOOLS/conftest.py`). Los
gates que no son tests (`flujo.py --validar`, `verificar_guia_madre.py`, `gen_grafo.py`) se corren
aparte. La app tiene su propia suite: `uv run pytest` en `app/backend` y `pnpm test` en `app/frontend`.

## 7. CONTRATO DE CLI — UN "MIRAR" NUNCA ESCRIBE (T6)

`Ads/_TOOLS/flujo.py`, `Ads/_TOOLS/decidir.py` y `Ads/_TOOLS/gen_grafo.py` por defecto SOLO LEEN.
Cada uno separa el cómputo (función pura) de la escritura (un solo sitio en `main()`, gateado por
`--escribir`):

| Comando | Lee/calcula (default) | Escribe (solo con `--escribir`) |
|---|---|---|
| `flujo.py PRODUCTO` / `--json` / `--validar` / `--grafo` | siempre — nunca escriben | nunca |
| `flujo.py --todo` | fase/nodo/bloqueantes de todos los productos | `_ESTADO_FLUJO.csv` · `_EVENTOS.csv` · `_FLUJO.json` · `VISTAS/FLUJO.html` |
| `decidir.py` (con o sin `--producto`/`--grano`/`--dias`/`--json`) | el portafolio de decisiones | `_DECISIONES.json` |
| `gen_grafo.py` (con o sin `--comparar`/`--estricto`) | el mapa de coherencia del sistema | `_LINEA_BASE_SISTEMA.json` |

`flujo.gate_entrada()` (función de Python que llaman `gen_publicacion.py` y `registrar_evento.py`) es
SOLO LECTURA sin excepción. Piden la escritura explícitamente: la cadena nocturna (`ciclo_hoy.py` →
`gen_decisiones.py --escribir` … → `flujo.py --todo --escribir`), la acción de manifiesto
`sistema.refrescar_flujo` y el arranque de sesión de `CLAUDE.md`. Todo lo demás (`app/backend`, las
skills de fase, los hooks) consulta en modo lectura.
