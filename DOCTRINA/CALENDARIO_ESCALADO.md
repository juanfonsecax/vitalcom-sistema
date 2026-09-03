# CALENDARIO_ESCALADO — LA CADENCIA DÍA-A-DÍA DEL ESCALADO (fuente única del "cuándo")

> **Qué es esto.** `DOCTRINA/ESCALADO_PLAYBOOK.md` dice **QUÉ** palancas existen y **por qué**. Este archivo dice **CUÁNDO** se jala cada una: el ritmo temporal (Día 0 → 3 → 6 → 9 → semana 2+) con **gates de decisión** — igual que la secuencia de FASE 1, pero para optimizar. ETAPA-7 (lee) y ETAPA-8 (decide) ejecutan este calendario contra la data real. **No inventa nada:** cada ventana está anclada a la clase que la respalda.
>
> **Fuentes (recencia manda):** Clase 22 (flujo, la más reciente) · Clase 20 (réplica del ganador) · Clase 19 (estructura de anuncio) · **Clase 15 (Joaquín — escalado progresivo, Post ID, multicuenta; la más reciente de escalado)** · Clase 8 (Camilo — CPA semanal, duplicación, precio, flujo de caja). Los montos de las clases están en COP; el sistema opera en **Q (Guatemala)** y **$2.99/conjunto en ETAPA 1 · $5.98 en ETAPA 2** (ver §1.5) — el método manda, la cifra no.

---

## 0. LAS DOS ESCUELAS Y CUÁL USA EL SISTEMA

- **PROGRESIVA (Joaquín, Clase 15) = DEFAULT.** "El escalado es VALIDACIÓN PROGRESIVA, no agresividad inmediata. Prefiero validar para durar más en el tiempo." Encaja con COD/WhatsApp, low-budget y protege de Andrómeda (baneo silencioso).
- **AGRESIVA (Camilo/Mercy, Clase 8) = solo con gasolina.** Duplicar fuerte y meter presupuesto rápido **SOLO** cuando hay **CPA real rentable sostenido (semanal) + flujo de caja** (COD retorna en ~3 días en Guatemala; 4-7 en Colombia).
- **Regla madre de ambos:** "se queman los ÁNGULOS, no los productos" + "paso más tiempo mandando a hacer creativos ganadores que mirando el dashboard" (Clase 15).

> **La decisión no es diaria, es SEMANAL.** El error #1 (Camilo, Clase 8) es apagar una campaña porque "hoy no vendió". `CPA ponderado = gasto de la semana ÷ ventas de la semana`. Un anuncio que vende se deja prendido aunque un día suba el CPA. Todo este calendario se lee sobre esa base.

---

## 1. LA REGLA DEL MULTI-GANADOR (lo que de verdad hacen los mentores)

> Cuando el testeo deja **2-3 ángulos rentables** (pasa seguido — Joaquín: "a veces funcionan 2-3 ángulos"), la duda es cómo estructurarlos. **NINGÚN mentor hace "una campaña por ángulo → un solo bot paraguas".** Lo que hacen:

1. **Optimizar el flujo hacia el/los ángulo(s) ganador(es)** (Clase 22): el bot deja de ser paraguas y se apunta al ángulo que Meta marcó con más clics. El **bot paraguas es herramienta de TESTEO (FASE 1), no de escalado** — a escala, un bot que no es congruente con el anuncio genera **efecto rebote** ("si el flujo dice algo distinto a lo pauteado, el cliente se sale", Clase 22).
2. **El ganador se riega HORIZONTAL, no se multiplica en campañas nuevas hacia un bot compartido:** la **campaña ganadora** (con su ángulo) se replica en **multicuenta (4→9), multifanpage y Post ID**. Ese es el vehículo del volumen.
3. **Cada ángulo ganador tiene su propio recorrido de FASE 2** (bot dedicado + microángulos + banco de creativos), **escalonado**, no todos de golpe:
   - **Ganador #1 (mejor CPA semanal):** arranca FASE 2 ya (ETAPA-3→4→5). Bot dedicado de un solo ángulo = máxima congruencia (Clase 22).
   - **Ganador #2 y #3:** entran como **FASE 2 propias escalonadas cada ~3 días**, cada uno con su bot dedicado. No se fusionan en un paraguas a escala.
   - Motivo: Joaquín optimiza el flujo hacia **EL** ángulo, no hacia tres a la vez. La congruencia es la que sostiene la conversión al meter plata.

> **En una línea:** paraguas para descubrir, dedicado para escalar. 2-3 ganadores = 2-3 FASE 2 escalonadas, no 3 campañas a un bot común.

> 🔴 **EJECUTOR ASIGNADO 02-sep: `etapa-11`.** Este principio estaba escrito y nadie lo ejecutaba
> contra data — el paso "dedicar el bot" no tenía dueño, ni método, ni forma de comprobarse.
> Ahora `etapa-11` corre al confirmar el ángulo ganador, mide el cierre y **diseña el A/B** que lo
> pone a prueba. Ver `.claude/agents/ETAPA-11.md`.
>
> ⚠️ **Y el principio está SIN VERIFICAR con data propia — se ejecuta como hipótesis, no como
> hecho.** Medido el 02-sep sobre la serie 17-jul → 01-sep: las campañas de **un solo ángulo**
> cerraron **7.2 %** y las de **≥2 ángulos** cerraron **9.0 %** — al revés de lo que predice el
> principio; y dentro de TINNIDROP, el único producto con ambos regímenes y `n` usable, la
> diferencia es nula (7.96 % vs 8.32 %, Fisher p = 1.000).
> **Eso NO refuta el principio:** `_EVENTOS.csv` no registra ni un `CAMBIO_BOT` para esos
> productos y el checklist de LucidBot de la FASE 2 de NUSAVA quedó sin marcar, así que no hay
> evidencia de que el flujo dedicado se haya cargado alguna vez. Lo medido es "un ángulo apuntando
> al mismo flujo paraguas", que no es la hipótesis.
> **Por eso el brazo B del A/B existe:** para testearlo en serio, una sola vez y bien.
> Detalle: `PRODUCTOS/_AUDITORIAS/_VERIFICACION_BRECHA_CIERRE_20260902.txt`.

---

## 1.5 EL PRESUPUESTO ES LO QUE HACE VÁLIDOS LOS GATES (recalibrado 2026-07-25 con data propia)

> 🔴 **ALCANCE (actualizado 2026-09-02).** Todo lo de esta sección gobierna la **FASE 1 · ÁNGULOS**.
> Desde el 02-sep el sistema tiene **tres** fases, y la FASE 2 (conceptos) tiene su propio
> presupuesto y su propio Presupuesto de Decisión, calculado **por anuncio y no por conjunto**.
> Ver **§1.7**. Las dos reglas duras de abajo (decidir por `angulo_key` · la conversación corta
> pero no corona) siguen valiendo para las tres fases.

> **El hallazgo:** el calendario de los mentores (día 3 podar, día 5 escalar) nació con **Q54/día por conjunto**. El sistema corría **$1.59/día = Q12.12** — 4.5× menos. Con ese presupuesto el día 3 tenía apenas **46-60% del Presupuesto de Decisión**, o sea que *decidir al día 3 era tirar una moneda*. No estaba mal el calendario: estaba mal el presupuesto que lo alimentaba.

**Los dos umbrales que gobiernan todo (no confundirlos):**

| Umbral | Evento que cuenta | Para qué sirve | Cuándo se cumple |
|---|---|---|---|
| **50 conversaciones** (salida de aprendizaje de Meta) | `conversación iniciada` — **es el evento de optimización de la campaña**, no la venta | que Meta deje de explorar y el ranking POR CONVERSACIÓN sea confiable | a $2.99 y $0.478/conv → **44 conv en 7 días** (≈umbral) |
| **Presupuesto de Decisión = 1× Break-Even** | venta COD (LucidSales) | que un "0 ventas" sea veredicto y no falta de exposición | a $2.99 con 80% de entrega real → **día 3.3-4.3** según producto |

**REGLA DE PRESUPUESTO DE TESTEO (autoajustable — reemplaza el número fijo):**
```
presupuesto/día por conjunto = 7 × (costo por conversación observado del producto)
                               piso $2.99  ·  techo $3.95
```
Deriva de la doctrina de Meta: 50 eventos de optimización en 7 días. Con el $0.478/conv medido en el portafolio (MCP, jul-2026) da **$3.41/día**. El rango de los mentores en las clases recientes (**12,000–16,000 COP/día = $2.96–$3.95** a la tasa 4,050) es exactamente este mismo rango — coinciden. Si un producto tiene conversación cara (>$0.42/conv), subir hacia $3.95; nunca bajar de $2.99.

**Días para alcanzar el PD (con factor de entrega real 0.8):**

| Producto | BE | @ $1.59 (viejo) | @ $2.99 (vigente) |
|---|---|---|---|
| TINNIDROP · CLEARSTEM | Q60.5 | 5.0 d | **3.3 d** |
| NUSAVA | Q68.3 | 5.6 d | **3.7 d** |
| VARICOSE | Q79.0 | 6.5 d | **4.3 d** |

### TESTEO EN DOS ETAPAS (concentración de presupuesto)

No se corren 6 conjuntos parejos hasta el final: se corta temprano por conversación y se **concentra el presupuesto en los sobrevivientes**, que es lo que acelera el veredicto de venta sin gastar más.

| Etapa | Días | Estructura | Reloj que decide | Salida |
|---|---|---|---|---|
| **E1 · DESCUBRIR** | 0-3 | 6 conjuntos × $2.99 | **conversación** (%conv/clic-enlace, $/conv) — disponible desde el día 2-3, viene del MCP y no depende de LucidSales | se cortan los 2-3 peores por conversación |
| **E2 · DEFINIR** | 4-8 | 3 sobrevivientes × **$5.98** (2×) | **venta** (CPA real sobre PD alcanzado) | ángulo ganador con ~3× BE acumulado |

Mismo gasto total que correr 6 parejos, pero los sobrevivientes llegan a **3× Break-Even** en vez de 2×, y el veredicto de venta cae ~2× más rápido. El corte de E1 **no necesita que pegues LucidSales** — sale del MCP automático.

### ⚠️ LO QUE EL PRESUPUESTO NO ARREGLA — decidir por ÁNGULO, nunca por conjunto-semana

Medición sobre data propia (42 conjuntos, ventana 7d): las ventas por conjunto tienen **índice de dispersión 1.12** — es decir, la variación entre conjuntos es **casi enteramente azar de Poisson**. Con 1-3 ventas el intervalo de confianza es ±113% a ±196%: un conjunto con 3 ventas y uno con 1 son **estadísticamente indistinguibles**.

```
CONJUNTO-CUENTA .............. dispersión 1.12  ← azar puro, NO decidir acá
CONJUNTO (todas las cuentas) . dispersión 1.89  ← señal débil
ÁNGULO (todas las cuentas) ... dispersión 2.99  ← SEÑAL REAL, acá se decide
```

**Regla dura:** el ganador se declara agregando por `angulo_key` de `_DIM_CONJUNTOS.csv` sobre todas las cuentas y todas las semanas acumuladas — nunca sobre un conjunto en una semana. Esto explica por qué el "ganador" de TINNIDROP se corrió tres veces (Accesibilidad → Pérdida auditiva → ME DIJERON): no cambió el mercado, era varianza de muestreo, y cada reacción movió presupuesto por ruido.

**Y la conversación NO predice la venta** — evidencia propia acumulada: `tinnidrop-1` 78% conv → 0 ventas · `ANIMO` (Nusava) 68% conv, la más alta → 0 ventas · `ME DIJERON` 23-25% conv → de los que más vende · `Médicos Fallaron` (Clearstem) chats más baratos ($0.59/conv) y peor cierre ($9.91/compra). La conversación sirve para **cortar** (E1), nunca para **coronar** (E2).

---

## 1.6 LOS TRES RELOJES Y LA CADENCIA DE INGESTA

> **El problema que resuelve:** el sistema pensaba en "día N de la campaña" mientras el operador lanza martes, miércoles y viernes. La solución no es que el operador se adapte al calendario — es que **las decisiones se disparen por umbral alcanzado, no por día de la semana**.

| Reloj | Fuente | Frecuencia | Latencia | Qué decide |
|---|---|---|---|---|
| **ENTREGA** | Meta MCP | diario, **automático** (el operador no hace nada) | día 2-3 | matar-por-conversación · fatiga (frec/CTR/CPM) · tracking roto |
| **VENTA** | LucidSales | **domingo** (export 7d) **+ el día que se lanza algo nuevo** | conjunto alcanza su PD + ~3d COD | matar-por-ventas · declarar ganador · escalar |
| **APRENDIZAJE** | acumulado (`_DIM_CONJUNTOS.csv`) | mensual | 30d+ | qué hook / formato / avatar / rol de embudo gana en general |

**CADENCIA DE INGESTA (decidida 25-jul):**
- **Domingo** — export LucidSales de 7 días. Es la ingesta principal y la única tarea recurrente del operador.
- **El día que se lanza producto o ángulo nuevo** — export extra, para fijar la **línea base** del lanzamiento y registrar el evento en `_EVENTOS.csv`. Sin esa línea base no se puede separar "el nuevo funciona" de "la semana fue buena".
- **Entre semana no se pide nada.** El reloj de ENTREGA cubre fatiga y matar-por-conversación solo.

**El domingo NO decide sobre todos los conjuntos — decide sobre los que ya maduraron.** Cada conjunto lleva su propia edad (desde `_EVENTOS.csv`) y su propio `%PD`. Un conjunto lanzado el miércoles aparece el domingo como `ESPERANDO · 45% del PD · madura el [fecha]` y no se toca. Así los lanzamientos entre semana dejan de ser un problema de calendario.

---

## 1.7 LA ARQUITECTURA DE 3 FASES (nueva — 2026-09-02)

> **De dónde sale:** clases del **16-ago** y **22-ago-2026** (Calet), destiladas en
> `_CONOCIMIENTO/MATRIZ_METODOLOGIA.md` como M-A06 a M-A13. **Qué la justifica en data propia:**
> la dispersión 1.12 de §1.5 (el testeo por conjunto no mide el creativo) y APR-057 (el techo de
> Q597/día es inventario de creativos, no mercado).

### 1.7.1 · La regla que decide qué estructura va en cada fase

```
presupuesto PROTEGIDO (conjuntos separados)  <=  la variable se decide por VENTA
presupuesto LIBRE     (1-1-N, Meta reparte)  <=  la variable se decide por ENTREGA
```

- **ÁNGULOS → conjuntos separados.** Meta solo ve clics y conversaciones, y APR-002 demuestra que
  esa señal **no predice la venta**. En un 1-1-N, Meta coronaría por la métrica equivocada y
  mataría de hambre al ángulo que vende.
- **CONCEPTOS → 1-1-5.** El ángulo ya está validado; lo que se busca es qué ejecución visual
  entrega más barato. Ahí el criterio de Meta (CTR/CPM/conversación) **sí está alineado** con el
  objetivo, y se puede soltar el presupuesto.

### 1.7.2 · Las tres fases

| Fase | Qué mide | Estructura | Presupuesto | Decide por |
|---|---|---|---|---|
| **1 · ÁNGULOS** | el ángulo | 6 conjuntos × 1 ángulo · **ABO** · concepto **FIJO** (`C2_BENEFICIOS` variante `ligera`) | $2.99 → $5.98 (§1.5, dos etapas) | **VENTA**, agregada por `angulo_key` |
| **2 · CONCEPTOS** | el creativo | **1-1-5 + 1-1-5 + 1-2-5** · ABO · ángulo **FIJO** (el ganador) | $6 + $6 + $12 = **$24/día** | **REPLICACIÓN**: gana en 2 de 2 |
| **3 · ESCALADO** | volumen | **1-1-7 CBO** (el ganador ×7) → `1-7-7` si el inventario lo permite | $15-18/día · +20 % con gate | **CPA semanal** sobre ENTREGADOS |

**La FASE 2 en detalle (10 conceptos, tres campañas):**

```
Campaña A · 1-1-5 · $6/día  ->  conceptos 1-5      (cuenta principal)
Campaña B · 1-1-5 · $6/día  ->  conceptos 6-10     (cuenta principal)
Campaña C · 1-2-5 · $12/día ->  conj.1 = conceptos 1-5 · conj.2 = conceptos 6-10   (OTRA cuenta)
```

Cada concepto corre **dos veces**, en estructuras independientes: dos sorteos del mismo pool. Es
la respuesta directa al problema de dispersión de §1.5 — el sistema no tenía ningún mecanismo de
replicación.

> ⚠️ **Por qué la campaña C va en OTRA cuenta.** A, B y C con los mismos creativos, la misma página
> y la misma audiencia compiten entre sí en la subasta y se suben el CPM mutuamente. Correr C en
> otra cuenta convierte ese confound en la validación multicuenta de `DOCTRINA/ESCALADO_PLAYBOOK.md` §3.6.

### 1.7.3 · REGLA DE LECTURA DE LA FASE 2 — la replicación

| Resultado del concepto | Veredicto |
|---|---|
| Queda arriba en **2 de sus 2** apariciones | **GANADOR** — se corona y pasa a FASE 3 |
| Queda arriba en **1 de 2** | **RUIDO** — no se corona; se repite el test |
| No recibió entrega en ninguna | **`SIN_ENTREGA`** — nunca `PERDEDOR` |

> El "ganador" de TINNIDROP que se corrió tres veces (Accesibilidad → Pérdida auditiva →
> ME DIJERON) **no habría pasado este filtro**. Ese es el valor del mecanismo.

### 1.7.4 · EL PRESUPUESTO DE DECISIÓN EN FASE 2 — es POR CONCEPTO, no por conjunto

Este es el punto donde el 1-1-5 puede salir **peor** que la estructura vieja si se lee mal, así que
va la aritmética completa (factor de entrega real 0.8, BE de TINNIDROP Q60.5 = $7.94):

| Nivel | $/día que recibe | Días para 1× BE | Veredicto |
|---|---|---|---|
| Conjunto en FASE 1 ($2.99) | $2.99 | **3.3 d** | referencia |
| Concepto en **una sola** 1-1-5 ($6 ÷ 5) | $1.20 | **8.3 d** | ❌ demasiado lento para decidir |
| Concepto **sumando sus 2 apariciones** (A/B + C) | **$2.40** | **4.1 d** | ✅ comparable a FASE 1 |

**La conclusión operativa, que es la razón real de la campaña C:** el 1-2-5 no es solo redundancia
estadística — es lo que hace que el Presupuesto de Decisión se alcance en un plazo decidible.
**Una 1-1-5 sola no basta: el concepto no llega a PD antes de que el ángulo se fatigue.**

**Regla dura:** en FASE 2 el `%PD` se calcula **por `concepto_key` + variante, sumando el gasto de
todas sus apariciones**. Nunca por conjunto y nunca por una sola campaña.

### 1.7.5 · GUARDARRAÍL `SIN_ENTREGA` (obligatorio en 1-1-N)

Meta no reparte parejo dentro de un conjunto — `ETAPA-6.md` lo documenta como *"cuando Meta se
enamora de un anuncio"*. Por eso, antes de emitir cualquier veredicto:

```
reparto esperado por anuncio = presupuesto del conjunto ÷ n.º de anuncios
si  gasto acumulado del anuncio  <  30 % del reparto esperado
    -> estado = SIN_ENTREGA   (no entra al ranking, no se corona ni se mata)
```

Un `SIN_ENTREGA` **se vuelve a lanzar** en la siguiente tanda, no se descarta. Sin este
guardarraíl el 1-1-5 mata conceptos que nunca se testearon. Ver choque **C-09** de la matriz.

### 1.7.6 · Dimensionamiento — cuántos productos caben

FASE 2 son **$24/día ≈ Q183/día por producto**. Contra el techo demostrado del portafolio
(**Q597/día**, APR-057) y con productos escalando en paralelo → **cabe UN solo producto en fase de
conceptos a la vez.** No correr FASE 2 de dos productos la misma semana.

### 1.7.7 · Lo que la FASE 2 exige antes de arrancar

- **10 conceptos listos y publicables.** Es el input, no un detalle: sin los 10, las tres campañas
  no se pueden montar. De ahí la meta de producción de ≥6 creativos/día de la fábrica.
- **Ángulo ganador confirmado por VENTA** (no por conversación) y agregado por `angulo_key`.
- **Los 10 conceptos son 10 EJECUCIONES**, etiquetadas con los `concepto_key` del catálogo — no 10
  `concepto_key` nuevos. Si cada ejecución estrena vocabulario, nunca se acumulan observaciones.

---

## 2. EL CALENDARIO — VENTANA POR VENTANA

> Día 0 = lanzamiento de la campaña de testeo (FASE 1 / ETAPA-6), a las **4 AM**. El calendario empieza a contar desde ahí **por conjunto** (no por campaña — ver §1.6). Cada mañana corre **ETAPA-7 (lee) → ETAPA-8 (decide)** — manual o como tarea programada.

### 🟦 VENTANA 0 — DÍA 0 (LANZAMIENTO, 4 AM)
- La campaña de testeo ya está creada (6 conjuntos, 6 ángulos distintos, 2 anuncios/conjunto, **$2.99/conjunto — ETAPA 1, ver §1.5**, **banda de edad derivada del avatar del ángulo**, Advantage+ OFF).
- **Mejora Joaquín (opcional, si hay cuentas):** lanzar la MISMA campaña en las **4 cuentas publicitarias** disponibles con la **misma fanpage** desde el día 1. Cada cuenta segmenta distinto → multiplica la probabilidad de buena data. (Hoy el sistema lanza 1 cuenta por default; la multicuenta día-1 es la versión Joaquín cuando el inventario de cuentas lo permite.)
- **NO se toca nada más hoy.** Nunca lanzar el mismo día; siempre 4 AM del siguiente.

### 🟦 VENTANA 1 — DÍAS 1-2 (DATA, NO VENTAS) · *observar*
- **Objetivo:** que Meta revele **qué ángulo tiene público** (clics en el enlace). NO se buscan ventas todavía.
- **ETAPA-7 cada mañana (solo lectura):** mirar por conjunto los **clics-enlace** y el **%conv/clic-enlace**. Nada de CPA todavía como veredicto.
- **NO pausar. NO escalar. NO renovar creativo.** Meta está en aprendizaje (~50 conversiones para salir). El **CPA alto es NORMAL** porque el flujo aún no está optimizado (bot con muchos ángulos).
- **Única excepción de apagado (Camilo, presupuesto alto):** si se pautó con presupuesto alto y a mediodía ya gastó la mitad **sin una sola venta en ningún anuncio del conjunto** → apagar ese conjunto. **A $2.99 se es paciente igual: esperar al día 3.**
- ETAPA-8 en Día 1-2 **no decide escalado** — solo reporta quién apunta a ganar.
- **PRESUPUESTO DE DECISIÓN (ver §1.5 y `DOCTRINA/ESCALADO_PLAYBOOK.md` §1.5):** a $2.99/día un conjunto alcanza **1 CPA Break-Even (su PD)** recién al día **3.3-4.3** según producto → en el día 1-2 **"0 ventas" NO es señal de matar**. Lo que SÍ se lee ya es la **conversación** (clics→chats), que a $2.99 acumula ~6.3 conv/día: un conjunto con %conv/clic-enlace muy bajo o $/conv caro se corta por ahí (anuncio/hook), sin esperar el PD. Matar-por-ventas es solo para el que ya gastó su PD y sigue en 0.

### 🟨 VENTANA 2 — DÍA 3 (GATE #1: DEFINICIÓN + CORTE DE ETAPA 1) · *optimizar flujo + podar + concentrar*
> Primer punto de decisión real. Se decide por CPA **semanal parcial** + conversación, nunca por el CPA de un día suelto.
> **ACCIÓN #0 — CORTE DE ETAPA 1 → ETAPA 2 (§1.5):** apagar los 2-3 conjuntos peores **por conversación** (%conv/clic-enlace <35% y/o $/conv > 2× la mediana del producto) y **subir los 3 sobrevivientes a $5.98**. El presupuesto liberado se concentra en quienes sí tienen público. Este corte sale del MCP — **no requiere LucidSales**. Es la palanca que acelera el veredicto de venta ~2×.
- **Declarar ángulo(s) ganador(es):** mejor **CPA real (≤ CPA Base)** + **%conv/clic-enlace ≥50%**. Si aún no hay tracking de ventas confiable (`omni_purchase` "Not available") → ganador **PROVISIONAL por conversación** (%conv/clic-enlace + $/conversación), **no oficial, no se escala fuerte**. (Cruzar siempre con LucidSales — es la fuente de verdad de ventas del bot.)
- **ACCIÓN #1 — OPTIMIZAR EL FLUJO (antes de gastar un peso más, Clase 22):** apuntar el bot de Lucid al ángulo ganador. Sube la conversión y baja el CPA sin gastar más ("convertir más sin gastar más"). Título + beneficio + resultado congruentes con el anuncio; reducir fricción (garantía, CTA con beneficio, prueba social); respetar el umbral cognitivo; responder en 2-3 seg.
- **ACCIÓN #2 — PODAR:** **apagar (no eliminar)** los conjuntos de ángulos que no funcionan (gasto > Break Even y 0 ventas) — **máx 2 a la vez** (los demás siguen aprendiendo). Los apagados pueden cerrar ventas rezagadas y se reactivan.
- **ACCIÓN #3 — SURFING (solo si hay ventas confirmadas):** +20% al presupuesto de lo que vendió. Sin ventas confirmadas → **todavía no**.

### 🟨 VENTANA 3 — DÍA 4 (GATE #2: VALIDACIÓN HORIZONTAL) · *validar sin subir presupuesto*
> **Calendario calibrado a Guatemala (entrega COD ~3 días, GINTACOM/FORZA — no los 4-7 de Colombia).** Ya hay un CPA formándose y las primeras entregas empiezan a confirmar. Se valida que el ganador **aguanta** en varias cuentas/fanpages antes de meterle gasolina. En mercados con entrega más lenta esta ventana corre a días 4-6.
- **Arranca FASE 2 del sistema sobre el ganador #1** (ETAPA-3 → 4 → 5): microángulos + **bot dedicado de un solo ángulo** + banco de creativos anti-fatiga (TOFU/MOFU/BOFU). Si hay ganador #2/#3 → sus FASE 2 se **escalonan cada ~3 días** (§1).
- **VALIDAR el ganador en DISTINTAS fanpages/cuentas** (Joaquín): replicar la campaña ganadora en las 4 cuentas/fanpages. **⚠️ En esta fase NO se sube presupuesto** — se valida que funcione a largo plazo (regla explícita Joaquín, Clase 15 Q&A). El +20% es solo para lo ya validado.
- **"Cuando vende en las 4 → SÚPER WINNER"** → habilita el escalado fuerte de la Ventana 4.
- **Empezar el banco de creativos del ganador** (Camilo: la variable #1): mandar a hacer **10-40 creativos** del mismo ángulo, conceptos/formatos distintos, entendiendo POR QUÉ ganó (Clase 20: "se copia el por qué vendió, no el creativo"). Brief lo arma ETAPA-8, lo ejecuta ETAPA-4.

### 🟩 VENTANA 4 — DÍA 5+ (ESCALADO) · *solo con CPA real rentable sostenido + flujo de caja*
> **Gate a DÍA 5 (Guatemala, entrega COD ~3 días).** La cuenta: los pedidos de los días 1-2 entregan ~día 4-5 → el **primer lote de ventas ENTREGADAS confirmadas** ya está para el día 5. No es día 3 porque el pedido debe estar **pedido Y entregado** antes de ser plata confirmada; no hay que esperar día 7 porque en Guatemala se entrega en 3, no en 4-7 (Colombia).
> ⚠️ **Guardarraíl:** día 5 es el gate más TEMPRANO, no automático. Abre solo si el **CPA sobre entregados está confirmado con volumen** (cruzar con LucidSales) **y agregado por `angulo_key`, no por conjunto** (§1.5). Si las entregas vienen flacas (1-2 ventas) → **esperar 1-2 días**, nunca regar horizontal sobre 1-2 ventas: con ese n el IC es ±139%.
> Palancas del `DOCTRINA/ESCALADO_PLAYBOOK.md` §3, en orden, no todas de golpe. Requisito de entrada: **CPA sobre entregados ≤ Base con volumen + caja para sostener ~3 días de retorno COD.**
1. **Surfing +20% diario** a TODO lo que vende (cada mañana; nunca más de 20% → desoptimiza).
2. **Post ID / publicar el creativo en la fanpage** → conservar prueba social → **regar el ganador en 4→9 cuentas** (mejor "publicación existente" que Post ID: Meta a veces borra reacciones al duplicar).
3. **Duplicar el conjunto ganador** (Camilo, agresivo: 16k→32k→64k) — **solo con flujo de caja**. El CPA sube un poco; se compensa con **creativos nuevos**.
4. **Multifanpage:** validar en fanpages sanas. Límite **250 anuncios/fanpage** (4 fanpages ≈ 1,000 anuncios).
5. **Subir el precio gradual** mientras siga vendiendo (va directo al margen; puede sacar competencia).
6. **Renovar creativos del ganador CONTINUAMENTE** — es lo que sostiene el CPA bajo al escalar.

### ♻️ CICLO PERMANENTE (cada mañana, indefinido)
Una vez en escalado, el ritmo diario no para:
- **ETAPA-7 lee → ETAPA-8 decide.** Surfing +20% a lo que vende. **CPA SEMANAL siempre** (no pánico diario).
- **Fatiga** (frecuencia ≥1.9 / CTR cae >20% en 48h) → **renovar creativo del MISMO ángulo**, sin tocar presupuesto ni ángulo.
- **Ventas bajan de golpe** → **Biblioteca de Anuncios** (competencia nueva) → responder con **nuevos creativos/ángulos/oferta**, **NO apagar** (apagar desoptimiza y la competencia te quita clientes; Meta es estable).
- **CPA real sobre ENTREGADOS, no vendidos** (Clase 8): de 100 vendidos → ~70 despachados → ~60 entregados; sumar fletes de falsos/devoluciones. Ahí vive la rentabilidad real.

---

## 3. TABLA RESUMEN — "¿QUÉ DÍA ES Y QUÉ HAGO?"

| Ventana | Días | Etapa | Presup./conj. | Estado | Acción principal | Reloj que decide | Qué NO hacer |
|---|---|---|---|---|---|---|---|
| 0 | Día 0 (4 AM) | E1 | $2.99 | Lanzamiento | Lanzar testeo (opcional: 4 cuentas, misma fanpage) | — | Lanzar el mismo día |
| 1 | 1-2 | E1 | $2.99 | DATA | Observar clics-enlace y conversación por ángulo | ENTREGA | Pausar / escalar / renovar |
| 2 | 3 | **E1→E2** | $2.99 → **$5.98** | DEFINICIÓN | **Cortar 2-3 por conversación + concentrar en los 3 sobrevivientes** · optimizar flujo | ENTREGA | Escalar fuerte sin CPA real |
| 3 | 4 | E2 | $5.98 | VALIDACIÓN | Arrancar FASE 2 del ganador + validar en 4 cuentas/fanpages | VENTA (parcial) | **Subir presupuesto en la validación** |
| 4 | 5+ | E2 | $5.98 | ESCALADO | Surfing 20% → Post ID/multicuenta → duplicar → precio | VENTA (por `angulo_key`) | Duplicar sin flujo de caja / regar sobre 1-2 ventas |
| ♻️ | perm. | — | — | CICLO | CPA semanal · renovar fatiga · responder competencia | los 3 | Apagar por un día malo |

> **Los días son la guía; el gate real es el UMBRAL.** Un conjunto no entra a la Ventana 2 por ser el día 3, sino por tener **≥30 conversaciones acumuladas**; no entra a la Ventana 4 por ser el día 5, sino por tener **≥1× su Break-Even gastado + ~3d COD**. Por eso los lanzamientos entre semana no rompen nada: cada conjunto corre su propio reloj desde su `fecha_lanzamiento` en `_EVENTOS.csv`.

> **Calendario calibrado a Guatemala (entrega COD ~3 días).** El gate de escalado fuerte es **día 5** — lo más temprano que hay un lote de ventas ENTREGADAS confirmadas. En mercados con entrega 4-7 días (Colombia) corre a día 7. **Los días son guía anclada a la entrega, no dogma:** el gate real es **CPA sobre entregados confirmado con volumen + %conv/clic-enlace**. Si el lote viene flaco, se espera o se sube presupuesto; nunca se riega horizontal sobre 1-2 ventas.

---

## 4. GATES DE SEGURIDAD (no saltarse)

1. **Escalado fuerte SOLO con CPA real confirmado (semanal).** Sin tracking de ventas = todo PROVISIONAL por conversación; nada de duplicar/multicuenta agresivo.
2. **En la validación horizontal NO se sube presupuesto** (Ventana 3). El +20% es exclusivo de lo ya validado.
3. **Nunca más de +20%/día.** Más desoptimiza.
4. **Nunca crear/pausar/subir presupuesto por MCP en vivo** (resetea a Andrómeda). ETAPA-7/8 solo leen y recomiendan; **el operador ejecuta**.
5. **Decidir por semana, no por día.** El CPA ponderado semanal es la única vara de rentabilidad.
6. **Fatiga ⇒ creativo nuevo del mismo ángulo,** nunca tocar el ángulo ganador ni el presupuesto por fatiga.
7. **Multi-ganador ⇒ FASE 2 escalonadas con bot dedicado,** nunca 3 campañas a un bot paraguas (§1).
