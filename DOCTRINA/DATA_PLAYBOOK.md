# DATA_PLAYBOOK — LA CAPA DE DATA (fuente única)

> **Qué es esto:** cómo está organizada la data del sistema, qué rol cumple cada archivo, cómo se lee sin sacar cifras falsas y cómo se calcula la ganancia. **Salió de `CLAUDE.md` el 31-jul-2026** (refactor de organización): era el 26% del orquestador y se cargaba en cada sesión aunque no se tocara data.
>
> **Quién lo lee:** `etapa-7` y `etapa-8` (al leer), `etapa-guardar-producto` (al escribir), `etapa-2` y `etapa-4` (aprendizajes, antes de diseñar), y la auditoría nocturna. El orquestador solo necesita saber que existe.
>
> **Regla madre:** los números viven en los CSV. **Prohibido hardcodearlos en un script o en prosa** — dos fuentes de verdad para el mismo número = drift garantizado.

---

## 1. LOS ARCHIVOS Y SU ROL (no confundir)

Todos viven en `PRODUCTOS/`. Creados 24-jul · split FACT 25-jul · DIM_PRECIOS 31-jul.

### `_FACT_VENTAS.csv` — HECHOS DE VENTA (capa máquina)
Solo LucidSales. **La ÚNICA que suma al P&L.** El operador NO la lee. De acá, y SOLO de acá, salen el CPA semanal, la tendencia y la ganancia. Prohibido reconstruir métricas leyendo auditorías en prosa.
- `rol_ventana` = **BASE** (no solapa con otra BASE → suma) o **CONTROL** (solapa a propósito, ej. el export de verificación → solo verifica, NUNCA suma). La regla de ingesta garantiza que las BASE no se solapen: `ventana_ini = ventana_fin de la última BASE + 1 día`.
- **Sin columnas derivadas.** `cpa_q` y `cierre_pct` se eliminaron: el CPA se CALCULA siempre, nunca se lee.
- **`ad_id`** (agregada 11-ago) — el `adId` de LucidSales, la identidad real de la fila. **Es lo que permite probar que no hay doble conteo sin volver al xlsx.** Va vacía solo en las filas sintéticas de cuadre (ver abajo); toda fila con anuncio atribuido la lleva. Al cargar una ventana nueva, poblarla siempre.
- **Filas sintéticas de cuadre:** el detalle del xlsx suma MENOS que el bloque `Resumen` (LucidSales no atribuye toda venta a un ad). La diferencia se carga como filas con `conjunto`/`anuncio` vacíos, `spend_usd`=0 y `ad_id` vacío, para que el P&L cuadre con el total real. Son legítimas y NO se les inventa un `ad_id`. Medido 11-ago: 6 filas en la ventana 03→10-ago (Q1,192) y 8 en 31-jul→02-ago (Q1,921).

### `_FACT_ENTREGA.csv` — HECHOS DE ENTREGA (capa máquina)
Solo Meta MCP: mensajes, clics, impresiones, gasto, `pct_conv_clic_enlace`. **No tiene columnas de venta → sumarla al P&L es imposible, no solo prohibido.**
- ⚠️ **El `conjunto` viene SIN el prefijo `[CUENTA]_[PRODUCTO]_`** que sí lleva el nombre real en Meta y en `_DIM_CONJUNTOS.csv` (la cuenta y el producto ya van en sus propias columnas). Además llega **sin tildes ni eñes** según el exportador. Por eso el mismo objeto de Meta aparece con dos grafías distintas en los dos archivos.
  **La solución NO es normalizar la llave** (la llave sigue siendo el nombre exacto): es **anexar la grafía que falta a `_DIM_CONJUNTOS.csv` con el MISMO `angulo_key`**, como manda la regla de esa tabla. Historia (el fix del 02-sep y su impacto en el JOIN): `_CONOCIMIENTO/POSTMORTEMS/DATA_PLAYBOOK_historias.md` §1.
- **`conjunto = "(campaña completa)"` es una fila legítima de AGREGADO DE CAMPAÑA**, no un hueco de tracking: es gasto real de una campaña que el MCP no desglosó por conjunto. Es la contraparte de las *filas sintéticas de cuadre* de `_FACT_VENTAS.csv`. **Nunca se le inventa un `angulo_key`.** Se excluye del análisis por ángulo y se reporta aparte, igual que las otras.
> Historia (por qué `_FACT_ENTREGA.csv` y `_FACT_VENTAS.csv` se separaron el 25-jul): `_CONOCIMIENTO/POSTMORTEMS/DATA_PLAYBOOK_historias.md` §1.

### `_DIM_CONJUNTOS.csv` — DIMENSIONES (capa máquina)
Traduce el nombre crudo del conjunto en Meta a la semántica del sistema: `angulo_key`, avatar, dolor, formato (VIDEO/IMAGEN), `tipo_hook`, nivel de conciencia, rol de embudo (TOFU/MOFU/BOFU), si el ad lleva precio. **Es lo que convierte la data de "cuánto gasté" en "POR QUÉ funciona".** Sin esta tabla no se puede responder qué ángulo, qué avatar, qué hook ni qué formato gana — ni dentro de un producto ni entre productos.

**Tres campos obligatorios de vocabulario CERRADO** (agregados 31-jul) — los declara `etapa-2` en su ficha de ángulo y los escribe `etapa-guardar-producto`:

| Campo | Valores permitidos |
|---|---|
| `avatar_genero` | MUJER · HOMBRE · MIXTO |
| `avatar_edad` | 25-35 · 35-45 · 45-60 · 60+ — el bucket **DOMINANTE**, no el rango completo |
| `emocion_dominante` | MIEDO_FUTURO · VERGUENZA · RESIGNACION · FRUSTRACION_MEDICA · DESCONFIANZA · AGOTAMIENTO · CURIOSIDAD |

**Cuarto campo cerrado — `concepto_key`** (agregado 18-ago). El ÁNGULO dice *por qué duele*; el **CONCEPTO** dice *cómo se muestra*. Son ortogonales y hasta ahora solo se trackeaba el primero, así que un conjunto podía ganar por su ángulo o por su ejecución visual y no había forma de saber cuál.

| Campo | Valores permitidos |
|---|---|
| `concepto_key` | C1_OFERTA · C2_BENEFICIOS · C3_SINTOMA · C4_TRANSFORMACION · C5_PRUEBA · C7_DESEO · C8_PROGRESION · C9_COMPARACION · SIN_CLASIFICAR |

> **Dueño único del catálogo: `Ads/_SWIPE/_CATALOGO_CONCEPTOS.md`** — ahí viven la firma de cada concepto, su rol de embudo y la evidencia de mercado (**v2: 133 creativos únicos de 39 anunciantes**, cruzando una muestra por supervivencia y otra por variedad visual). No duplicar las definiciones acá.
> ⚠️ Con 8 valores y 12-24 conjuntos/mes cada concepto recibe 1,5-3 observaciones mensuales — **por debajo del umbral de la regla 6**. Por eso la rotación de FASE 2 usa 6 de los 8 por producto (C2 y C1 siempre + 4 rotativos), no los 8. Detalle en el catálogo, última sección.
> **Regla de fase:** FASE 1 fija `concepto_key = C2_BENEFICIOS` en los 6 conjuntos (mide ÁNGULO, así que el concepto es la constante). FASE 2 fija el ángulo ganador y **varía el concepto** — ahí la columna empieza a acumular. Las 93 filas anteriores al 18-ago quedan en `SIN_CLASIFICAR`: no se retroclasifican de memoria.
> 🔴 **Actualizado 2026-09-02 — dónde vive el `concepto_key` según la fase.** Con la arquitectura de
> 3 fases, en FASE 2 el concepto **ya no distingue conjuntos: distingue ANUNCIOS** (5 por conjunto).
> Por eso el `concepto_key` de FASE 2 se registra en **`_DIM_CREATIVOS.csv`**, no en
> `_DIM_CONJUNTOS.csv` — ahí el ángulo es constante en toda la fase. Leer el concepto a nivel de
> conjunto en FASE 2 devuelve un solo valor repetido y no mide nada.

**Quinto y sexto campos cerrados — `brazo` y `estado_entrega`** (agregados 02-sep, para la FASE 2 de conceptos):

| Campo | Valores permitidos | Dónde vive |
|---|---|---|
| `brazo` | A · B · C1 · C2 · (vacío fuera de FASE 2) | `_DIM_CREATIVOS.csv` |
| `id_tanda` | `[PRODUCTO]-T[NN]` — la tanda de 10 conceptos a la que pertenece | `_DIM_CREATIVOS.csv` |
| `estado_entrega` | ENTREGADO · **SIN_ENTREGA** · (vacío si no aplica) | `_DIM_CREATIVOS.csv` |
| `rol_embudo` | TOFU · MOFU · BOFU | `_DIM_CREATIVOS.csv` (viene del blueprint JSON) |

> **`SIN_ENTREGA` es la corrección más importante de este bloque.** En un `1-1-N` Meta reparte
> desigual: un anuncio puede terminar la ventana con casi cero gasto. Ese anuncio **no es
> perdedor — no fue testeado.**
> ```
> reparto esperado = presupuesto del conjunto ÷ n.º de anuncios
> gasto acumulado < 30 % del esperado  ->  estado_entrega = SIN_ENTREGA
> ```
> Un `SIN_ENTREGA` **queda fuera del ranking** (no se corona ni se mata) y **se relanza** en la
> tanda siguiente. Contarlo como perdedor mete un sesgo de supervivencia en todo el aprendizaje
> acumulado de conceptos.

> **REGLA DE LECTURA DE LA FASE 2 — la replicación.** El veredicto de un concepto **nunca** sale de
> una sola aparición. Cada concepto corre dos veces (brazo A o B **y** brazo C):
> `2 de 2 arriba` = GANADOR · `1 de 2` = RUIDO (se repite) · `0 entregas` = `SIN_ENTREGA`.
> Y el `%PD` se calcula **sumando el gasto de las 2 apariciones** del mismo `concepto_key`+variante,
> nunca por conjunto. Aritmética completa en `DOCTRINA/CALENDARIO_ESCALADO.md` §1.7.4.

> **Diccionario de emociones:** MIEDO_FUTURO = teme que empeore o sea irreversible · VERGUENZA = lo esconde de los demás · RESIGNACION = ya se rindió · FRUSTRACION_MEDICA = pagó especialistas y sigue igual · DESCONFIANZA = teme que sea falso o no funcione · AGOTAMIENTO = cansado, sin energía · CURIOSIDAD = no sabía que su problema tenía esa causa (educacional/mecanismo).

- **POR QUÉ:** `etapa-2` produce una ficha rica (perfil, situación, dolor activo, deseo, miedos, frustraciones) pero antes solo sobrevivían `avatar` y `dolor_nucleo` como **texto libre** — 28 y 33 valores distintos en 54 conjuntos, imposibles de agregar. Toda esa investigación se usaba para escribir el copy y **después se perdía**: nunca se contrastaba contra quién compró. Estos 3 campos la vuelven aprendible y **transferible entre productos** (si la vergüenza vende en várices, se prueba vergüenza en acné).
- ⚠️ **Pesan más por ANDROMEDA (2026):** Meta ya NO segmenta por audiencia — **el creativo ES el targeting**. Andromeda lee el anuncio y de ahí deduce a quién mostrárselo; la calidad del creativo explica ~56% del resultado (más que segmentación + presupuesto + placement juntos), y el algoritmo ignora la definición de audiencia si las señales del creativo apuntan a otro lado. El avatar ya no se controla desde la cajita de segmentación: se controla desde lo que el creativo DICE y a quién RETRATA. Medirlo es lo único que queda para saber a quién le estás hablando de verdad.
- **`etapa-2` y `etapa-4` CONSULTAN el dashboard antes de diseñar** (`_DASHBOARD.html` → «Por qué funciona — cada producto»): trae el CPA real por emoción, género y edad, por producto y del portafolio. Si una emoción ya fracasó 2 veces en la categoría, no se vuelve a proponer; si viene ganando en otro producto del mismo nicho, es candidata a probar.
- **Ejes que NO se guardan como categoría** (decisión 31-jul): `deseo`, `miedos` y `frustraciones` de la ficha, y el banco de 15 tipos de ángulo. Motivo: con 117 ventas cada eje nuevo fragmenta la muestra y toda celda queda con 1-3 ventas = ruido de Poisson. Se retoman cuando el portafolio pase de ~10 productos. Siguen en `2_DATA_PRODUCTO.txt` como prosa para escribir el copy.
- **Llave = `conjunto_meta` EXACTO como quedó en Meta**, sufijos incluidos (`- Copia`, `- Copia 2`). No normalizar. Dos nombres del mismo ángulo = dos filas con el MISMO `angulo_key`.
- **Agregar SIEMPRE por `angulo_key`**, nunca por `conjunto`.
- La escribe `etapa-guardar-producto` al cerrar cada fase (esquema y vocabularios en su archivo, SALIDA 4). `etapa-7` hace el JOIN antes de rankear y **anexa** cualquier conjunto que aparezca en datos y falte acá.
- **El JOIN debe cerrar al 100%:** una fila de datos sin dimensión es un hueco de tracking, se reporta y se corrige — nunca se descarta el dato.

### `_EVENTOS.csv` — LOG DE ACCIONES (capa máquina)
Qué se lanzó, pausó, escaló o cambió y cuándo. Sin esto no se puede calcular la EDAD de un conjunto (ni su %PD), ni atribuir un cambio de CPA a una acción. La `fecha` del LANZAMIENTO define el reloj propio de cada conjunto — **es lo que permite lanzar entre semana sin romper el calendario**. Los eventos `CAMBIO_BOT`/`CAMBIO_CREATIVO` son variables de confusión: si hay uno en la ventana leída, `etapa-7` lo declara y no atribuye el resultado al ángulo.
> 🔴 **`CAMBIO_BOT` ES OBLIGATORIO.** **Todo cambio de flujo se loguea el día que se aplica**, lo
> escriba `etapa-11` o lo haga el operador a mano. Un cambio sin evento es un cambio que el sistema
> no puede evaluar. Historia (la auditoría que expuso la columna vacía):
> `_CONOCIMIENTO/POSTMORTEMS/DATA_PLAYBOOK_historias.md` §1.

### `_APRENDIZAJES.csv` — MEMORIA TRANSVERSAL (capa máquina)
Lo que el sistema ya aprendió y no debe volver a pagar para descubrir: qué tipo de hook no vende, qué ángulo ya fracasó en qué producto, qué métrica no predice la venta. **Es lo que hace que el sistema mejore con el tiempo en vez de repetir errores caros.**
- Antes vivían hardcodeados en el prompt de `etapa-7`. Con 4 productos se sostenía; con 20 el agente se vuelve un basurero de excepciones contradictorias. Son DATA, no instrucciones.
- **Lo leen** `etapa-2` y `etapa-4` (al DISEÑAR: no proponer lo que ya fracasó) y `etapa-7`/`etapa-8` (al LEER). Filtro: `estado=VIGENTE AND (alcance=GLOBAL OR producto_key=[X]) AND '[agente]' IN consumido_por`.
- **Lo escribe** `etapa-8` cuando un patrón se repite en ≥2 ventanas o ≥2 productos.
- `confianza` ALTA = restricción dura · MEDIA = prior fuerte, se puede contradecir justificando · BAJA/EN_OBSERVACION = solo seguir midiendo. **Un aprendizaje BAJA nunca justifica cambiar una regla del sistema.**
- Todo aprendizaje lleva `revisar_despues_de` — caducan. Un aprendizaje contradicho NO se borra: pasa a `estado=SUPERSEDIDO` y se crea el que lo reemplaza.

### `_BITACORA_DATA.txt` — CONTROL DE INTEGRIDAD
Qué días entró data y cuáles faltan. ⚠️ Con días 🔴 en la ventana: NO presentar CPA semanal como completo, NO declarar ganador oficial, NO matar por ventas. **Data faltante ≠ cero ventas.**

### `_GANANCIAS.txt` — LOG HISTÓRICO LEGIBLE
Una línea por día/ventana, más las notas de decisión que valga la pena conservar. Ya NO es la vista principal (esa es el dashboard). Mantener CORTO (últimos 30 días; lo viejo colapsado a resumen mensual). Nada de listados de campañas acá.

### CAPA DE FACTURACIÓN — ¿lo que Meta COBRA = lo que Meta dice que GASTÉ? (16-ago)
> Cadencia **semanal, domingos**. Responde dos preguntas que suelen mezclarse; la primera casi siempre da OK y la segunda es donde está la plata.

- `_DIM_BM.csv` — **Business Manager → cuentas publicitarias**. La tarjeta vive a nivel **BM**, no de cuenta: un BM puede tener varias cuentas (AMG 2 tiene GTR0+GTR1+GTR2) y su tarjeta paga cualquiera de ellas. Por eso la conciliación **bancaria** se hace por BM y recién adentro se reparte por cuenta según gasto devengado. Confirmado con data: MC-8931 pagaba GTR1 **y** GTR0, las dos de AMG 2.
- `_DIM_TARJETAS.csv` — tarjeta (últimos 4) → BM, con cobros OK / rechazos / % de falla y veredicto (SANA · LEVE · INTERMITENTE · **MUERTA**). **Se autocompleta con cada extracto** — el extracto de Facturación dice qué tarjeta pagó cada cargo. **Nunca atribuir una tarjeta a una cuenta por descarte** (APR-030).
- `_FACT_FACTURACION.csv` — un **cargo por fila** (COBRO / RECHAZO / CREDITO). Es el hecho atómico. Vacío hasta el primer extracto semanal.
- `_FACT_FACTURACION_AGREGADO.csv` — fallback por ventana cuando solo se tiene el total por cuenta. El script usa el detalle si existe y el agregado si no.
- `_FACT_SALDOS.csv` — **saldo gastado y aún NO facturado** al corte. Es la pieza que hace cerrar la ecuación; sin ella no hay conciliación posible.
- `_FACT_PAUTA_REAL.csv` — gasto **trackeado** (lo que ve LucidSales) vs gasto **real** (lo que cobra Meta), por cuenta y ventana. Alimenta la cobertura.

**LA ECUACIÓN (única comparación válida):**
```
cobros_del_periodo − saldo_sin_facturar_INICIAL + saldo_sin_facturar_FINAL = gasto_devengado
```
Meta cobra al cruzar **umbrales de gasto acumulado** ($25→$50→$100→$250) o en la fecha fija mensual, lo que llegue primero — **no** por día ni por rango. Comparar "gasté del 1 al 15" contra "me cobraron del 1 al 15" **siempre** descuadra y **no es evidencia de sobrecobro** (APR-025).

⚠️ **REGLA DURA DE MÉTODO:** si el saldo inicial es **ESTIMADO** (despejado de la propia ecuación), la ecuación cierra *por construcción* y **no verifica nada**. Solo verifica cuando el saldo inicial fue **OBSERVADO** en el corte anterior. Por eso hay que guardar el saldo de cada cuenta en **cada** corte semanal: de la segunda semana en adelante la conciliación es real. `conciliar_facturacion.py` marca esa diferencia de forma explícita y tiene prohibido disimularla.

**Las dos preguntas, separadas:**
| | Pregunta | Qué la responde | Estado al 15-ago |
|---|---|---|---|
| **A** | ¿Meta me cobra de más? | la ecuación de arrastre | ✅ No hay sobrecobro (cerró al centavo en GTR7/GTR1/GTR0) |
| **B** | ¿Todo lo que me cobran está en mi P&L? | cobertura = trackeado ÷ real | 🔴 **75%** — Q1,899 de gasto real fuera del P&L |

→ El riesgo grande **no** es que Meta cobre de más: es que hay gasto que Meta sí cobra y LucidSales no reporta, y eso **infla la ganancia** del dashboard sin que se vea. Mientras la cobertura no sea ~100%, la ganancia está sobreestimada aproximadamente en la diferencia.

**Corre con:** `python Ads/_TOOLS/conciliar_facturacion.py [ini] [fin]` → escribe `_AUDITORIAS/_CONCILIACION_[YYYYMMDD].txt`. Ningún número se escribe a mano.

### `_ESTADO_META.csv` — QUÉ ESTÁ ENCENDIDO (declarado, no inferido) — 16-ago
Una fila por campaña: `cuenta_alias · campana · producto_key · estado (ON/OFF) · conjuntos_activos · fecha_confirmado · fuente`.
**Manda sobre cualquier inferencia.** El sistema no puede deducir el estado: la data de ventas va 1-3 días atrás (por eso el dashboard llegó a pedir apagar campañas ya pausadas) y en **GTR13 y CP1 no hay MCP**, así que no hay nada que leer. Si el archivo no existe, `gen_dashboard.py` cae al fallback de "gastó en el último día". Actualizarlo cuesta 30 segundos y es lo que hace confiable la lista de acciones.

### Tablas de referencia
- `_DIM_PRECIOS.csv` — la **escalera de precios** por producto × unidades (precio, costo proveedor total, flete observado, n órdenes).
- `_TASA_ENTREGA.csv` — parámetros de logística, mensual.
- `_DIM_PRODUCTOS.csv` — fallback por producto (BE, CPA Base, tasa) **y el MAPA DE CARPETAS** (ver §1.1).
- `_DIM_COSTEO.csv` — tabla de costeo original (de `COSTEOS GT PRO.xlsx`), la usa `etapa-1` para costear un producto NUEVO sin ventas ni escalera.
- `_MAPEO_CREATIVOS.csv` — **HISTÓRICO, congelado. No lo lee ninguna etapa y no se escribe más.**
  62 filas de la era pre-`_DIM_CREATIVOS`: anuncio × archivo de media × ventas × spend_usd, con los
  nombres viejos (`- Copia`, que el invariante 12 hoy prohíbe) y `metodo=AUTO`. Se conserva porque es
  historia real del negocio — la única fuente que ata media concreta a ventas antes de que existiera
  `creativo_id`. Para lecturas nuevas usar `_DIM_CREATIVOS.csv`; para minar el pasado, esto.
- `_DIM_CREATIVOS.csv` — **dimensiones de creativo y el ciclo de vida de cada pieza.** Es el CSV
  que cierra el loop de la fábrica (`etapa-9`) con el lector (`etapa-10`).
  · **Ciclo de estado obligatorio:** `PENDIENTE_GENERAR` → `GENERADO` (el archivo existe en
    `Ads/MEDIA_[PRODUCTO]/`) → `PUBLICADO` (el anuncio existe en Meta con su `ad_id`) → `RETIRADO`.
  · ⚠️ **Alerta de dashboard:** una fila en `PENDIENTE_GENERAR` **o en `GENERADO`** por más de
    **7 días** es una alerta, no una fila silenciosa. Sin esta alerta, la fábrica produce para el
    disco duro. Historia (el caso real que la motivó): `_CONOCIMIENTO/POSTMORTEMS/DATA_PLAYBOOK_historias.md` §1.

---

## 1.1 MAPA DE CARPETAS — `producto_key` ↔ filesystem (31-jul)

**El problema:** el mismo producto vive en 4 lugares del disco con nombres distintos. NUSAVA tenía **cinco grafías**: `producto_key=NUSAVA` · `PRODUCTOS/NusavaB12` · `Ads/1.1 Videos/NUSAVA B12` · `Ads/MEDIA_GTR7_NUSAVAB12` · y el sub-lote `NUSABA B12 ARDOR` (con typo). Con 4 productos se sostiene de memoria; con 20 el JOIN se vuelve adivinanza — el mismo error que agregar por `producto` en vez de `producto_key`.

**La solución: `_DIM_PRODUCTOS.csv` es el traductor.** Cinco columnas resuelven cualquier ruta desde el `producto_key`:

| Columna | Apunta a |
|---|---|
| `slug_carpeta` | `PRODUCTOS/[X]/` |
| `carpeta_videos` | `Ads/1.1 Videos/[X]/` |
| `carpeta_transcripciones` | `Ads/1.2 Transcripcion videos/[X]/` |
| `carpeta_media` | `Ads/[X]/` (creativos lavados y ads-imagen) |
| `carpetas_extra` | sub-lotes y casos especiales (segundo lote, creativos propios) |

**Reglas:**
- **Nunca adivinar la carpeta de un producto por su nombre.** Se resuelve leyendo esta tabla. Si un producto no está, se agrega la fila — no se asume.
- **`producto_key` es la llave y no cambia nunca.** Las carpetas del disco pueden llamarse como sea; lo que las une es esta tabla.

### 1.1b — Y también resuelve la campaña (añadido 2026-09-02)

| Columna | Para qué |
|---|---|
| `clave_campana` | El texto a buscar en los nombres de campaña de Meta (`REGLA DE BÚSQUEDA` de abajo) |
| `campaign_id` | El `campaign_id` conocido, o `PENDIENTE` / `SIN_MCP` |

> Historia (por qué estas dos columnas se movieron acá desde `_PORTAFOLIO.txt`):
> `_CONOCIMIENTO/POSTMORTEMS/DATA_PLAYBOOK_historias.md` §1.1.

> ⚠️ **REGLA DE BÚSQUEDA DE CAMPAÑA (sigue vigente):** nunca fijar el
> `campaign_id` a ciegas. Listar las campañas de la cuenta y tomar la ACTIVE cuyo
> nombre contenga `clave_campana` **con gasto > 0** — el operador pausa, renombra
> y duplica (caso NusavaB12: la campaña viva era un duplicado manual `…- Copia`).
> El `campaign_id` de esta tabla es una pista, no la verdad.
- Al **dar de alta un producto**, `etapa-guardar-producto` escribe su fila con las 5 columnas de carpeta ya resueltas.
- **Las carpetas NO se renombran para "emparejarlas"**: 17 referencias a rutas `MEDIA_*` viven en los `1_HACER_MANUAL.txt`/`2_DATA_PRODUCTO.txt` que el operador usa para ejecutar. Renombrar las rompería a cambio de nada — el alias hace el mismo trabajo sin tocar un byte.

> ⚠️ **CSV malformado — cómo evitarlo.** **Todo campo de texto libre con comas va entre comillas
> dobles.** Al editar estos CSV, escribirlos con un lector/escritor CSV real (`csv.DictWriter`),
> nunca a mano ni concatenando strings. Historia (el bug real que lo expuso):
> `_CONOCIMIENTO/POSTMORTEMS/DATA_PLAYBOOK_historias.md` §1.1.

---

## 2. `_DASHBOARD.html` — LA CAPA HUMANA

**Lo único que el operador abre a diario.** Panel visual: ganancia neta, **PLAN DE ACCIÓN («Qué tenés que hacer»)**, P&L por producto, día a día, ranking por ÁNGULO, sangrado (plata sobre la mesa), cortes por hook/formato/embudo/precio y aprendizajes vigentes. Responsive y con tema claro/oscuro — se lee igual en el celular.

> ⚠️ **CÓMO LEE EL OPERADOR (confirmado 31-jul):** Juan NO lee los TXT ni el informe largo. Su flujo real es: pega la data → cierra el chat → abre el dashboard. Todo lo que él tenga que EJECUTAR va en el dashboard, no en prosa. El chat se mantiene en 3-4 líneas.

**Sección «QUÉ TENÉS QUE HACER» (motor de acciones, arriba de todo).** Se DERIVA de los CSV con 8 reglas del playbook — nunca se escribe a mano:

| | Regla | Disparador |
|---|---|---|
| A | Apagar por ventas | 0 ventas con el PD cumplido |
| B | Apagar por conversación | 0 ventas y conversación en el fondo de su producto, aún sub-PD |
| C | Rebalancear cuenta saturada | mismo `angulo_key` con CPA ≥2× peor en una cuenta que en otra |
| D | Surfing +20% | conjuntos con CPA ≤ CPA Base |
| E | Ganador infra-financiado | mejor CPA del producto con <15% de la pauta |
| F | Renovar creativo | vende pero sobre el BE (el ángulo comunica, el creativo se gastó) |
| G | Producto mudo | VIVO que dejó de gastar |
| H | Huecos de data | — |

Cada fila trae CUÁNDO (hoy / esta semana / cuando puedas), QUÉ y DÓNDE (producto·cuenta·conjunto), POR QUÉ (la cifra exacta), IMPACTO Q/semana y ESTADO («sigue gastando · N días así» = lo que NO se ha hecho).

- **Si una acción se repite y el motor no la captura, la regla se AGREGA AL SCRIPT** para que salga sola — nunca se escribe a mano en el HTML.
- **Se GENERA, nunca se escribe a mano:** `python Ads/_TOOLS/gen_dashboard.py` lo reconstruye entero desde `_FACT_VENTAS.csv` + `_DIM_CONJUNTOS.csv` + `_EVENTOS.csv` + `_APRENDIZAJES.csv` + `_BITACORA_DATA.txt`. **Ningún número está escrito a mano** — por eso no puede desincronizarse de la data.
- **Correrlo es el ÚLTIMO paso de la auditoría nocturna**, después de anexar al CSV. Si el CSV cambió y el dashboard no se regeneró, el operador está leyendo data vieja.
- Los umbrales por producto (BE, CPA Base, tasa) están hardcodeados arriba del script — mover a `_DIM_PRODUCTOS.csv`.

---

## 3. CÓMO LEER EL CSV — 4 REGLAS OBLIGATORIAS (25-jul · regla (d) agregada 02-sep)

El archivo mezcla filas de dos orígenes y agregarlo mal da cifras falsas:

**(a) Filtrar por `fuente` SIEMPRE.** `fuente=LucidSales*` = ventas reales, **la única que suma al P&L**. `fuente=MCP*` = solo entrega (mensajes/clics/impresiones/gasto), con `ventas`/`total_q` VACÍAS y **su gasto YA contado en las filas LucidSales** → NUNCA sumarla.
> Prueba 25-jul: sumar sin filtrar da $377 en vez de $296 (+27% de gasto fantasma, ~Q615 de ganancia borrada).

**(b) Agregar por `producto_key`** (TINNIDROP/VARICOSE/CLEARSTEM/NUSAVA), nunca por `producto` — el nombre crudo de LucidSales parte el mismo producto en varios ("Varicose Veins Ointment" vs "Varicose 2x1 oferta VER").

**(c) Totalizar con `dias=1`.** Las filas `dias=7` (lunes + baseline) son control cruzado: verifican, no suman.

**(d) EL CIERRE SE CALCULA, NUNCA SE LEE — y se agrega por `angulo_key`.**
```
cierre = Σ ventas ÷ Σ mensajes        (filas rol_ventana=BASE, agregadas por angulo_key)
```
Es el KPI que gobierna `etapa-11`. Cuatro trampas, todas medidas:
- **Ratio de sumas, nunca promedio de ratios.** Promediar el cierre de cada fila da un número
  distinto y está mal. Lo mismo vale para el `%conv/clic-enlace`: `Σmensajes ÷ Σlink_clicks`.
- **Por `angulo_key`, jamás por conjunto-semana.** Con 1-3 ventas el IC de Poisson es ±113-196 %.
  Piso de evidencia de `etapa-11`: ≥60 mensajes y ≥5 ventas por ángulo.
- **Semanal, nunca diario** — igual que el CPA.
- **Cierre ≠ venta cobrada.** Una venta COD que se devuelve no es venta: el cierre del bot y la
  tasa de entrega son cosas distintas y no se mezclan (`_TASA_ENTREGA.csv` · `DOCTRINA/CONTABILIDAD.md`).

Referencia vigente (02-sep): portafolio **8.6 %** · mejor ángulo del sistema 18.1 %
(CLEARSTEM/ANTI_FALSIFICACION) · umbral de los mentores 15-20 % (M-F01).

**UN SOLO ESCRITOR.** La tarea programada de **Cowork** es la única auditoría nocturna que escribe al CSV y a la bitácora. No crear una segunda tarea equivalente (Cron del chat u otra sesión): la misma noche entraría dos veces = doble conteo real. Antes de anexar, verificar que (ventana, producto_key, conjunto, fuente) no exista ya.

---

## 4. FÓRMULA OFICIAL DE GANANCIA (v2 — 31-jul, TICKET REAL)

```
ganancia = Σ contribución de cada venta − pauta Q

contribución = TE × (precio − costo proveedor − flete − admin − otros)
             − (1−TE) × costo del evento de devolución
```
La contribución sale del **escalón** en que cayó ese pedido.

> ⚠️ **La versión vieja (`ventas × BE fijo − pauta`) queda DEPRECADA.** Contaba VENTAS, no quetzales: un pedido de 3 frascos a Q299 valía igual que uno de 1 a Q179 → subestimaba la ganancia real y hacía invisible todo el upsell del bot. Historia (la medición que lo probó): `_CONOCIMIENTO/POSTMORTEMS/DATA_PLAYBOOK_historias.md` §4.

- **La escalera vive en `_DIM_PRECIOS.csv`.** Es **FLEXIBLE por producto**: los productos baratos no tienen escalón de 1u — arrancan en 2x1. No forzar 1/2/3/4 para todos.
- **Los parámetros de logística viven en `_TASA_ENTREGA.csv`**: `pct_entrega_resueltos`, `costo_devolucion_evento_q` (Q27.16), `costos_admin_q` (Q4.00), `otros_gastos_q` (Q2.08 sin identificar, colchón visible). Se cambian ahí y todo recalcula solo.

> ### ‼️ LA TASA DE ENTREGA ES **POR PRODUCTO**, NO UNA SOLA (v3 — 11-ago)
> Medido sobre **304 órdenes** de Dropi (01-jul → 07-ago), la entrega NO es homogénea:
> **CLEARSTEM 95.8% · TINNIDROP 90.4% · VARICOSE 74.2% · NUSAVA 71.7%** — 24 puntos de spread contra un global de 86.2%.
> Costear todo con la global movía el break-even real **−19.5% en NUSAVA y +16.3% en CLEARSTEM**, e **invertía el ranking de productos** (NUSAVA pasaba por el más rentable cuando es de los peores).
> · `_TASA_ENTREGA.csv` tiene columna **`producto_key`**; `GLOBAL` es el fallback.
> · Regla del motor: **se usa la tasa propia del producto cuando tiene ≥20 resueltos**; si no, la global.
> · La fila global vigente se elige por **MÁS ÓRDENES RESUELTAS, no por fecha** — si no, una ventana chica y sin madurar (ej. 46 casos al 95.7%) infla la ganancia de todo el portafolio.
> · Un producto que devuelve mucho **no se escala sin atacar la devolución primero**: escalar multiplica la fuga.
- **Unidades por pedido = se INFIEREN del ticket**, interpolando sobre la escalera. Funciona aunque una fila del reporte agrupe varias ventas (Q209 = promedio de un 1u y un 2u) porque las escaleras son lineales.
- **Nunca presentar la contribución BRUTA como "ganancia"** (sin descontar flete, admin ni devolución) — eso sí infla la cifra.

### Hechos de costo verificados (304 órdenes reales de Dropi, 01-jul → 07-ago · act. 11-ago)
- Comisión de plataforma: **0%** (confirmado en las 304)
- `flete = Q31.42 + Q2.70 × unidades` — **validado por escalón**: 1u +0.3% · 2u +1.8% · 3u +0.7% · 4u +4.2% contra el real. Promedio Q35.81/orden sobre 1.51 u/orden. **No se toca.**
- **El tamaño del pedido NO aumenta la devolución**: 1u 86.0% · 2u 83.9% · 3u **94.7%** · 4u 83.3% de entrega. → el upsell del bot se puede seguir empujando sin castigo logístico.
- **La DISTANCIA no mueve el flete** (Guatemala −Q0.33 vs Petén +Q1.15 de residuo; FORZA cobra casi tarifa plana nacional). Lo único que lo mueve es el peso/unidades.
- El costo de devolución **NO aparece en la orden** (ahí sale 0): se cobra aparte en el estado de cuenta como "SALIDA DE COBRO DE DEVOLUCIÓN POR ENTREGA NO EFECTIVA".

### Break-Even
**Se DERIVA de `_DIM_PRECIOS.csv` + `_TASA_ENTREGA.csv`.** El valor en `_DIM_PRODUCTOS.csv` es solo **FALLBACK**: el script recalcula el ponderado real desde el mix efectivamente vendido.
> Los v3 del 31-jul subieron 21-57% vs los v2 porque el v2 asumía un precio único y un flete de Q41-47 (el real es Q35.5). Los v2 se conservan en `cpa_be_anterior_q`. Consecuencia operativa: **podés pagar bastante más por venta de lo que creías**, y el Presupuesto de Decisión (1×BE) sube igual — un conjunto necesita gastar más antes de que su cero cuente como veredicto.
> **Las cifras vigentes se leen del CSV, no de acá** — por eso este archivo no las lista.

- **VARICOSE entra por la fila Q90**, no Q45: vende 2x1 (2 frascos de Q45 = Q90 de producto por pedido a Q249). Los productos en combo se costean por el PEDIDO, no por la unidad.
- **Tasa de entrega** en `_TASA_ENTREGA.csv`, mensual. ⚠️ El % de «ENTREGADO» de Dropi es sobre el TOTAL e incluye pedidos EN TRÁNSITO — leerlo como tasa de entrega subestima el negocio. La cifra válida se calcula sobre estados RESUELTOS (jul-2026: 85.1% entrega / 14.0% devolución vs 17% asumido → supuesto bien calibrado).

---

## 4.1 LAS DOS FUENTES DE VENTA — NO SON SUSTITUTOS Y NUNCA SE SUMAN (11-ago)

| | **LUCIDSALES** | **DROPI** |
|---|---|---|
| Qué es | venta **ATRIBUIDA a un ad** | venta **REAL Y COBRADA** + estado de entrega |
| Sirve para | CPA, ranking de ángulos, decidir qué apagar/escalar | P&L, tasa de entrega, economía unitaria |
| No ve | lo orgánico, el recontacto, el remarketing | de qué anuncio vino la venta |
| Grano | fila por `adId` | fila por orden |

**Medido 11-ago:** Dropi 73 órdenes / Q16,749 contra LucidSales 61 ventas / Q13,541 en el mismo tramo.
**VARICOSE vendió 5 veces con pauta CERO y LucidSales atribuyó 1** → un P&L construido solo sobre LucidSales **subestima**.

> ⛔ **PROHIBIDO cruzar Dropi con LucidSales día contra día.** La columna `FECHA` de Dropi es **la fecha de CARGA EN LOTE**, no la de la venta. Prueba: 33 órdenes creadas en 29 minutos el 05-ago, 21 en 31 min el 07, 19 en **2 minutos** el 11. Los días en cero entre lotes NO son días sin ventas. Solo se comparan por acumulado.
>
> ⚠️ **La columna `GANANCIA` de Dropi NO es el P&L.** Solo se llena en estado `ENTREGADO` (43/44 y 11/11 verificado), o sea que va **~5 días atrasada** e ignora todo lo que está en tránsito. Además es margen bruto: no descuenta admin, ni el evento de devolución, ni el flete de las devueltas, ni **un solo quetzal de pauta**. El P&L válido es el de §4.
>
> 🕐 **La demora de carga a Dropi es un costo real, no un detalle administrativo.** Con carga en lote el pedido puede esperar hasta 4 días antes de salir a ruta; en contraentrega el cliente se enfría y sube la devolución. En julio la carga era casi diaria; en agosto se abrieron huecos de 3-4 días. **Volver a carga diaria.**

## 4.2 AUDITORÍA DE INTEGRIDAD — CÓMO PROBAR QUE NO HAY DOBLE CONTEO (11-ago)

Antes de cargar cualquier export que pueda solapar, correr estas 4 pruebas:

1. **Solapamiento entre BASE** — las ventanas `rol=BASE` deben ser contiguas y disjuntas (`ventana_ini = ventana_fin anterior + 1 día`). Cualquier solape es doble conteo directo.
2. **Filas 100% idénticas** — si dos filas coinciden en *todos* los campos, revisar. Las ventas **sin ad atribuido** (conjunto vacío, spend 0, 1 venta) se ven idénticas y son legítimas: en el xlsx tienen `adId` distintos.
3. **Llaves repetidas** — LucidSales emite **una fila por `adId`** y un mismo anuncio corre con varios. Repetición ≠ duplicado.
4. **Test contra un CONTROL que abarque más período** — ✅ la prueba fuerte. En cada celda `(producto, conjunto)` el CONTROL **solo puede ser ≥ que la suma de las BASE** (cubre más días y tiene más maduración COD). Si alguna celda sale al revés, ahí está el doble conteo.

> **La columna `ad_id` hace automáticas las pruebas 2 y 3:**
> ```
> # 0 resultados = no hay doble conteo
> repetidas = Counter((ventana_ini, ventana_fin, fuente, ad_id) for filas BASE con ad_id)
> comunes   = adIds(fuente=A) & adIds(fuente=B)   # universos disjuntos => ambas suman
> ```
> Historia (por qué hacía falta y la corrida que la validó): `_CONOCIMIENTO/POSTMORTEMS/DATA_PLAYBOOK_historias.md` §4.2.

**Todo export que solape con una BASE existente entra como `CONTROL`, nunca como BASE.** Un agregado de N días **no se puede descomponer** en sus días: si se necesita un tramo, se pide ese tramo exacto.

---

## 5. CADENCIA Y MONEDAS

**Cadencia:** LucidSales se pega **todas las noches con export de 1 SOLO DÍA (ayer)**. Recordatorio 8 PM, auditoría 9 PM. Los lunes además el export de 7 días como control cruzado de maduración COD (~3 días) — se carga con `dias=7` y NO se suma con las diarias (doble conteo), solo verifica.

> ⭐ **CAMBIO 2026-08-16 — SE ACABA LA SEGUNDA CUENTA DE LUCIDSALES.** El 16-ago fue el **último día con dos bots**. Desde el **17-ago** el operador entrega **un solo export por día**, de un único bot.
> · Las ventanas **hasta el 16-ago inclusive** siguen necesitando **las dos** fuentes (`LucidSales` y `LucidSales_CuentaB`) — son universos disjuntos y **ambas suman** (APR-021). No borrar ni fusionar el histórico.
> · Desde el **17-ago** existe una sola `fuente` y la regla de contigüidad por fuente se simplifica a una sola serie.
> · ⚠️ **Al comparar tramos que cruzan el 16-ago, declararlo:** una caída de ventas o de gasto trackeado a partir del 17 puede ser el cambio de estructura de bots y no una caída real del negocio. Verificar contra la **cobertura** de la capa de facturación antes de atribuirlo al rendimiento.

**Cadencia de la capa de FACTURACIÓN (semanal, domingos):** el operador pega el **extracto de Facturación de Meta por cuenta** (las 6) y, cuando aplique, el **export de Ads Manager nivel conjunto de GTR13 y CP1** — las dos cuentas sin MCP, que son las que concentran la fuga de cobertura. El **extracto bancario** va **mensual**: confirma el veredicto pero no lo cambia, y es lo que permite medir la tasa COP real de CP1. Al cerrar cada corrida hay que guardar el **saldo sin facturar de cada cuenta** en `_FACT_SALDOS.csv` con `estado=OBSERVADO` — es lo único que convierte la conciliación de la semana siguiente en una verificación real.

**Monedas:** `spend`/`costPerMessage`/`costPerSale` → USD · `total` (venta) → QUETZALES.
> ⚠️ EXCEPCIÓN: la cuenta **CP1 = 1346891653335162** factura en **COP** → `spend_COP ÷ 3152.5 = spend_USD`. Sin normalizar, contamina el CPA de todo el portafolio.
>
> **La tasa vigente es 3,152.5, no 4,050 (APR-028).** Historia (cómo se midió y por qué la anterior
> estaba mal): `_CONOCIMIENTO/POSTMORTEMS/DATA_PLAYBOOK_historias.md` §5.
> ⚠️ Ojo con el orden de magnitud: un día de CP1 puede venir como `spend = 20,068`. Son pesos (**$6.37 USD**), no dólares. Sumar la columna sin normalizar da un gasto ~125× inflado y el CPA del portafolio se vuelve basura.

---

## 6. LOS TESTS DEL MOTOR — UN SOLO COMANDO

```bash
python -m pytest Ads/_TOOLS            # los 28 test_*.py del motor
python -m pytest Ads/_TOOLS -k decidir # uno solo
```

Cada `test_*.py` corre como script, con el mismo intérprete, y pasa solo si sale con código 0: el mismo
veredicto que da corriéndolo a mano. Lo resuelve `Ads/_TOOLS/conftest.py`; ninguna aserción se reescribió.
Requiere `pytest` en el Python del sistema (`python -m pip install pytest`, una vez). Los gates de
coherencia que no son tests (`flujo.py --validar`, `verificar_guia_madre.py`, `gen_grafo.py`) se siguen
corriendo aparte. La app tiene su propia suite: `uv run pytest` en `app/backend` y `pnpm test` en
`app/frontend`.
