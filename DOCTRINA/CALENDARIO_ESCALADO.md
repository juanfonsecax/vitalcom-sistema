# CALENDARIO_ESCALADO — LA CADENCIA DE LAS 4 FASES (fuente única del "cuándo")

> **Qué es esto.** `DOCTRINA/ESCALADO_PLAYBOOK.md` dice **QUÉ** palancas existen y **por qué**. Este
> archivo dice **CUÁNDO** se mueve cada cosa: el ritmo de FASE 1 día a día y la aritmética de las
> cuatro fases. Las órdenes de pausar o escalar no salen de acá: las emite `Ads/_TOOLS/decidir.py`
> (invariante 13) con los parámetros de `PRODUCTOS/_PARAMETROS_DECISION.csv`; las transiciones entre
> fases las juzga `Ads/_TOOLS/flujo.py` sobre `DOCTRINA/FLUJO.json`. Los montos de las clases están en
> COP; el sistema opera con los de `PRODUCTOS/_PARAMETROS_PUBLICACION.csv` — el método manda, la
> cifra no.

---

## 0. LAS DOS ESCUELAS Y CUÁL USA EL SISTEMA

- **PROGRESIVA = DEFAULT.** El escalado es validación progresiva, no agresividad inmediata. Encaja con
  COD/WhatsApp y bajo presupuesto, y protege del baneo silencioso de Andrómeda.
- **AGRESIVA = solo con gasolina.** Duplicar fuerte y meter presupuesto rápido **solo** con CPA real
  rentable sostenido + flujo de caja para aguantar el retorno COD.
- **Regla madre de las dos:** se queman los ÁNGULOS, no los productos; el tiempo se va en producir
  creativos ganadores, no en mirar el panel.

> **La decisión no es diaria.** El error #1 es apagar porque "hoy no vendió". El CPA se lee sobre la
> ventana de `ventana_dias` con su intervalo de credibilidad (`decidir.py`): un anuncio que vende se
> deja prendido aunque un día suba el CPA.

---

## 1. LA REGLA DEL MULTI-GANADOR

Cuando FASE 1 deja **2-3 ángulos rentables**, ningún mentor hace "una campaña por ángulo → un solo bot
paraguas":

1. **Paraguas para descubrir, dedicado para escalar.** El bot paraguas es herramienta de TESTEO
   (FASE 1). A escala, un bot que no es congruente con el anuncio genera efecto rebote: el flujo se
   reescribe hacia el ganador en **FASE 3**.
2. **Cada ángulo ganador tiene su propio recorrido** (FASE 2 conceptos → FASE 3 flujo → FASE 4
   escalado), **escalonado, no todos de golpe**: el ganador #1 (mejor CPA por `angulo_key`) arranca
   primero; el #2 y el #3 entran escalonados cada ~3 días, dentro del tope de §1.7.6.
3. **El volumen se riega HORIZONTAL** (FASE 4): la campaña ganadora se replica en multicuenta,
   multifanpage y Post ID.

> `etapa-11` diseña en FASE 2 el A/B de flujo (paraguas optimizado vs dedicado) que pone a prueba el
> punto 1 con data propia — se ejecuta como hipótesis hasta que ese A/B lo confirme.

---

## 1.5 EL PRESUPUESTO ES LO QUE HACE VÁLIDOS LOS GATES

> **ALCANCE:** esta sección gobierna la **FASE 1 · ÁNGULOS**. La FASE 2 tiene su propio presupuesto y
> su propio Presupuesto de Decisión, calculado **por concepto y no por conjunto** (§1.7.4). Las dos
> reglas duras de abajo valen para las cuatro fases.

El calendario de los mentores (día 3 podar, día 5 escalar) nació con presupuestos varias veces más
altos que los del sistema. A poco presupuesto, decidir al día 3 por ventas es tirar una moneda: no
está mal el calendario, está mal el presupuesto que lo alimenta.

**Los dos umbrales que gobiernan todo (no confundirlos):**

| Umbral | Evento que cuenta | Para qué sirve |
|---|---|---|
| **50 conversaciones en 7 días** (salida de aprendizaje de Meta) | `conversación iniciada` — el evento de optimización de la campaña, no la venta | que Meta deje de explorar y el ranking por conversación sea confiable |
| **Presupuesto de Decisión (PD) = 1× Break-Even** | venta COD (LucidSales) | que un "0 ventas" sea veredicto y no falta de exposición |

**El presupuesto por conjunto de FASE 1 sale de `PRODUCTOS/_PARAMETROS_PUBLICACION.csv`** (fila
`fase=1`, `daily_budget_usd`); `gen_lanzador.py` lo lee de ahí. Es el mismo en todos los conjuntos
(invariante 6). El rango de las clases recientes (12.000–16.000 COP/día ≈ 3-4 USD) coincide con ese
orden de magnitud.

### TESTEO EN DOS ETAPAS (concentración de presupuesto)

No se corren 6 conjuntos parejos hasta el final: se corta temprano por conversación y se **concentra
el presupuesto en los sobrevivientes**, que es lo que acelera el veredicto de venta sin gastar más.

| Etapa | Días | Estructura | Reloj que decide | Salida |
|---|---|---|---|---|
| **E1 · DESCUBRIR** | 0-3 | 6 conjuntos al presupuesto de la fila `fase=1` | **conversación** (`%conv/clic-enlace`, $/conv) — viene de Meta, no depende de LucidSales | se cortan los 2-3 peores por conversación |
| **E2 · DEFINIR** | 4+ | los 3 sobrevivientes al **doble** del presupuesto de E1, los tres a la vez | **venta** (CPA real con el PD alcanzado) | ángulo ganador |

Mismo gasto total que correr 6 parejos, pero los sobrevivientes llegan antes a varias veces su
Break-Even. La subida va a los 3 sobrevivientes **a la vez**, nunca a uno solo: si no, el que sube
gana por dinero, no por ángulo.

### LO QUE EL PRESUPUESTO NO ARREGLA — decidir por ÁNGULO, nunca por conjunto-semana

En la data propia, la variación de ventas entre conjuntos es casi enteramente azar de Poisson: con
1-3 ventas el intervalo es ±113 % a ±196 %, y un conjunto con 3 ventas y uno con 1 son
indistinguibles. Agregado por ángulo, sobre todas las cuentas y semanas, sí aparece la señal.

**Regla dura:** el ganador se declara agregando por `angulo_key` de `_DIM_CONJUNTOS.csv` sobre todas
las cuentas y todas las semanas acumuladas — nunca sobre un conjunto en una semana. Reaccionar al
ganador de cada semana mueve presupuesto por ruido.

**Y la conversación NO predice la venta** (APR-002): conjuntos con la conversación más alta del
portafolio vendieron cero y otros con conversación baja están entre los que más venden. La
conversación sirve para **cortar** (E1), nunca para **coronar** (E2).

---

## 1.6 LOS TRES RELOJES

Las decisiones se disparan **por umbral alcanzado, no por día de la semana**: así se puede lanzar
cualquier día.

| Reloj | Fuente | Frecuencia | Qué decide |
|---|---|---|---|
| **ENTREGA** | Meta | cada noche, automático | matar por conversación · fatiga (frecuencia, CTR, CPM) · tracking roto |
| **VENTA** | LucidSales | cada noche, automático (Colombia: export manual del operador) | matar por ventas · declarar ganador · escalar |
| **APRENDIZAJE** | acumulado (`_DIM_CONJUNTOS.csv`, `_DIM_CREATIVOS.csv`) | mensual | qué hook, formato, avatar o rol de embudo gana en general |

**Cada conjunto lleva su propia edad** (desde su LANZAMIENTO en `_EVENTOS.csv`) y su propio `%PD`.
Un conjunto que todavía no maduró aparece como `ESPERANDO · N % del PD` y no se toca. El día que se
lanza algo nuevo se registra el evento: sin esa línea base no se separa "lo nuevo funciona" de "la
semana fue buena".

---

## 1.7 LA ARQUITECTURA DE 4 FASES

### 1.7.1 · La regla que decide qué estructura va en cada fase

```
presupuesto PROTEGIDO (conjuntos separados)  <=  la variable se decide por VENTA
presupuesto LIBRE     (1-1-N, Meta reparte)  <=  la variable se decide por ENTREGA
```

- **ÁNGULOS → conjuntos separados.** Meta solo ve clics y conversaciones, y esa señal **no predice la
  venta** (APR-002). En un 1-1-N Meta coronaría por la métrica equivocada.
- **CONCEPTOS → 1-1-5.** El ángulo ya está validado; se busca qué ejecución visual entrega más barato.
  Ahí el criterio de Meta (CTR, CPM, conversación) **sí está alineado** con el objetivo.

### 1.7.2 · Las cuatro fases

Los valores de estructura, presupuesto, objetivo y hora de cada fila viven en
`PRODUCTOS/_PARAMETROS_PUBLICACION.csv`; acá va el porqué.

| Fase | Qué mide | Estructura | Presupuesto | Decide por |
|---|---|---|---|---|
| **1 · ÁNGULOS** | el ángulo | 6 conjuntos × 1 ángulo · **ABO** · concepto **FIJO** (`C2_BENEFICIOS` variante `ligera`) · todo IMAGEN | el de la fila `fase=1`, en dos etapas (§1.5) | **VENTA**, agregada por `angulo_key` |
| **2 · CONCEPTOS** | el creativo | **1-1-5 + 1-1-5 + 1-2-5** · ABO · ángulo **FIJO** (el ganador) | el de las filas `fase=2` (A, B y C) | **REPLICACIÓN**: gana en 2 de 2 |
| **3 · FLUJO LUCIDBOT** | el cierre | ninguna estructura nueva en Meta: el concepto ganador sigue corriendo | **el mismo de FASE 2**, sin subir | cierre ≥ `cierre_min_escalar_pct` con ≥ `min_mensajes_cierre` mensajes, medido después del `CAMBIO_BOT` — en horas, no días; se itera hasta cumplir |
| **4 · ESCALADO** | volumen | **1-1-7 CBO** (el ganador ×7) → `1-7-7` si el inventario lo permite | la fila `fase=4` (se siembra el piso de la banda; el techo se alcanza con el +`surfing_pct` diario) | **CPA** sobre ENTREGADOS |

**La FASE 2 en detalle (10 conceptos, tres campañas):**

```
Campaña A · 1-1-5  ->  conceptos 1-5      (cuenta principal)
Campaña B · 1-1-5  ->  conceptos 6-10     (cuenta principal)
Campaña C · 1-2-5  ->  conj.1 = conceptos 1-5 · conj.2 = conceptos 6-10   (OTRA cuenta)
```

Cada concepto corre **dos veces**, en estructuras independientes: dos sorteos del mismo pool. Es la
respuesta al problema de dispersión de §1.5.

> **Por qué la campaña C va en OTRA cuenta.** A, B y C con los mismos creativos, la misma página y la
> misma audiencia compiten en la subasta y se suben el CPM. En otra cuenta, ese confound se vuelve la
> validación multicuenta de `DOCTRINA/ESCALADO/04_PALANCAS.md` §3.6.

### 1.7.3 · REGLA DE LECTURA DE LA FASE 2 — la replicación

| Resultado del concepto | Veredicto |
|---|---|
| Queda arriba en **2 de sus 2** apariciones | **GANADOR** — se corona y pasa a FASE 3 |
| Queda arriba en **1 de 2** | **RUIDO** — no se corona; se repite el test |
| No recibió entrega en ninguna | **`SIN_ENTREGA`** — nunca `PERDEDOR` |

La campaña 1-1-5 rueda `duracion_testeo_fase2_dias` antes de coronar; el empate técnico entre
conceptos lo fija `margen_empate_cpa_pct` (`flujo.py`).

### 1.7.4 · EL PRESUPUESTO DE DECISIÓN EN FASE 2 — es POR CONCEPTO, no por conjunto

Con 5 anuncios por conjunto, cada concepto recibe una quinta parte del presupuesto de su conjunto.
En **una sola** 1-1-5 eso es poco más que un tercio de lo que recibe un conjunto de FASE 1: el
concepto tarda más del doble en llegar a 1× Break-Even y el ángulo se fatiga antes. **Sumando sus 2
apariciones** (A o B, más C), el concepto recibe del orden de un conjunto de FASE 1 y llega al PD en
un plazo decidible.

**Una 1-1-5 sola no basta: la campaña C es lo que hace alcanzable el Presupuesto de Decisión.**

**Regla dura:** en FASE 2 el `%PD` se calcula **por `concepto_key` + variante, sumando el gasto de
todas sus apariciones**. Nunca por conjunto y nunca por una sola campaña.

### 1.7.5 · GUARDARRAÍL `SIN_ENTREGA` (obligatorio en 1-1-N)

Meta no reparte parejo dentro de un conjunto. Antes de emitir cualquier veredicto:

```
reparto esperado por anuncio = presupuesto del conjunto ÷ n.º de anuncios
si  gasto acumulado del anuncio  <  30 % del reparto esperado
    -> estado = SIN_ENTREGA   (no entra al ranking, no se corona ni se mata)
```

Un `SIN_ENTREGA` **se vuelve a lanzar** en la tanda siguiente. Sin este guardarraíl el 1-1-5 mata
conceptos que nunca se testearon.

### 1.7.6 · Dimensionamiento — cuántos productos caben

Las tres campañas de FASE 2 suman varias veces el presupuesto de FASE 1 y compiten por el mismo techo
de gasto diario del portafolio (APR-057: el techo es inventario de creativos, no mercado). **Cabe UN
solo producto en fase de conceptos a la vez:** no correr la FASE 2 de dos productos la misma semana.

### 1.7.7 · Lo que la FASE 2 exige antes de arrancar

- **10 conceptos listos y publicables** (`etapa-9`). Sin los 10, las tres campañas no se montan.
- **Ángulo ganador confirmado por VENTA**, agregado por `angulo_key` (invariante 1).
- **Los 10 conceptos son 10 EJECUCIONES** etiquetadas con los `concepto_key` del catálogo — no 10
  `concepto_key` nuevos. Si cada ejecución estrena vocabulario, nunca se acumulan observaciones.

---

## 2. EL CALENDARIO DE FASE 1 — VENTANA POR VENTANA

> Día 0 = lanzamiento, a la hora de `hora_lanzamiento` del día siguiente a armar la campaña
> (invariante 7). Cada conjunto cuenta desde su propio LANZAMIENTO (§1.6). Cada mañana corre el ciclo
> diario: `decidir.py` emite las órdenes y `etapa-7` las lee.

### VENTANA 0 — DÍA 0 · lanzamiento
- 6 conjuntos, 6 ángulos, mismo presupuesto, banda de edad derivada del avatar de cada ángulo,
  Advantage+ OFF, todo en IMAGEN.
- Opcional, si hay cuentas: la misma campaña en varias cuentas con la misma fanpage desde el día 1;
  cada cuenta segmenta distinto y multiplica la probabilidad de buena data.
- **No se toca nada más.**

### VENTANA 1 — DÍAS 1-2 · observar
- Objetivo: que Meta revele **qué ángulo tiene público** (clics en el enlace y conversación).
- **No pausar, no escalar, no renovar creativo.** Meta está en aprendizaje y el CPA alto es normal:
  "0 ventas" todavía no es señal, porque ningún conjunto alcanzó su PD.
- Lo que sí se lee es la **conversación**: un conjunto con `%conv/clic-enlace` bajo el umbral
  (`umbral_conv_clic_enlace_pct`, con al menos `min_link_clicks_conv` clics) tiene un problema de
  anuncio → bot y `decidir.py` lo corta sin esperar el PD.

### VENTANA 2 — DÍA 3 · GATE #1: corte de E1 → E2
- **Cortar los 2-3 peores por conversación** y **subir los sobrevivientes al doble** (§1.5). Sale de
  Meta, no requiere LucidSales. Como máximo `max_pausas_por_dia` pausas por producto y corrida; el
  resto queda diferido.
- **Apagar, no eliminar:** un conjunto apagado puede cerrar ventas rezagadas y se reactiva.
- **Matar por ventas** solo al conjunto que ya gastó su PD y lleva `dias_min_cod_pausa_ventas` de
  maduración COD con 0 ventas.

### VENTANA 3 — DÍA 4 EN ADELANTE · E2: definir el ganador por VENTA
- Los sobrevivientes acumulan venta hasta que un ángulo cumple el gate: ventas ≥ `min_ventas_ganador`
  y CPA acumulado ≤ Break-Even, **agregado por `angulo_key`** (invariante 1). Ahí `flujo.py` abre
  FASE 2.
- Un ganador provisional por conversación nunca es oficial: sin venta confirmada no se pasa de fase.
- **En FASE 1 no se escala.** Surfing, Post ID, duplicar y multicuenta son palancas de FASE 4.

---

## 3. TABLA RESUMEN — "¿QUÉ DÍA ES Y QUÉ HAGO?"

| Momento | Etapa | Acción principal | Reloj que decide | Qué NO hacer |
|---|---|---|---|---|
| F1 · día 0 | E1 | Lanzar los 6 conjuntos | — | Lanzar el mismo día |
| F1 · días 1-2 | E1 | Observar clics-enlace y conversación por ángulo | ENTREGA | Pausar por ventas · escalar · renovar |
| F1 · día 3 | E1 → E2 | Cortar 2-3 por conversación + doblar a los sobrevivientes | ENTREGA | Coronar por conversación |
| F1 · día 4+ | E2 | Acumular venta hasta el gate de ángulo ganador | VENTA (por `angulo_key`) | Escalar dentro de FASE 1 |
| FASE 2 | — | 10 conceptos en 3 campañas; leer por replicación 2 de 2 | VENTA (por concepto, 2 apariciones) | Coronar con 1 de 2 · leer por conjunto |
| FASE 3 | — | Reescribir el flujo hacia el ganador y medir el cierre | CIERRE (después del `CAMBIO_BOT`) | Subir presupuesto |
| FASE 4 | — | 1-1-7 → expansión horizontal → surfing | CPA sobre ENTREGADOS | Duplicar sin caja · regar sobre 1-2 ventas |

> **Los días son la guía; el gate real es el UMBRAL.** Un conjunto no entra a la Ventana 2 por ser el
> día 3 sino por tener la conversación suficiente para juzgarse, y no se declara ganador por ser el
> día 5 sino por cumplir el gate de venta. Por eso los lanzamientos entre semana no rompen nada.

### CICLO PERMANENTE (cada mañana, en cualquier fase)
- **Fatiga** (frecuencia alta, CTR que cae, CPM que sube) → **renovar el creativo del MISMO ángulo**,
  sin tocar presupuesto ni ángulo (`decidir.py` emite `RENOVAR`).
- **Ventas que bajan de golpe** → mirar la Biblioteca de Anuncios (competencia nueva) y responder con
  creativos, ángulos u oferta nuevos — **no apagar**: apagar desoptimiza.
- **El CPA real es sobre ENTREGADOS, no vendidos:** en contra entrega parte de lo vendido no se
  entrega; la maduración la fija `maduracion_dias` (`DOCTRINA/CONTABILIDAD.md`).

---

## 4. GATES DE SEGURIDAD (no saltarse)

1. **Escalar SOLO con CPA real confirmado.** Sin tracking de ventas todo es provisional por
   conversación: nada de duplicar ni multicuenta.
2. **En la validación horizontal no se sube presupuesto.** El +`surfing_pct` es solo para lo ya
   validado.
3. **Nunca más de +`surfing_pct` por día**, una sola vez, en la mañana. Más desoptimiza.
4. **Ninguna orden de pausar o escalar se emite sin pasar por `decidir.py`, y ejecutarla en Meta por
   MCP requiere la confirmación explícita del operador, orden por orden** (invariante 13). Después se
   verifica contra Meta y se registra el evento.
5. **No se decide por un día.** El CPA se lee sobre la ventana con su intervalo.
6. **Fatiga ⇒ creativo nuevo del mismo ángulo,** nunca tocar el ángulo ganador ni el presupuesto.
7. **Multi-ganador ⇒ recorridos escalonados con flujo dedicado,** nunca 3 campañas a un bot paraguas
   (§1).
