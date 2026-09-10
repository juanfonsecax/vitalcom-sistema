# PROPUESTA — LA CAPA DE OPTIMIZACIÓN CONTINUA

**Fecha:** 2026-09-09 · **Sesión 2 de 2** (la sesión 1 construyó el FLUJO DECLARADO) ·
**Estado: parcialmente IMPLEMENTADO el mismo día.** Lo construido está abajo en §8; lo que
queda propuesto y por qué no se implementó está en §9.

> **La conclusión en una línea, para no enterrarla:** el sistema **no necesita un bandit
> todavía**. Necesita registrar `CAMBIO_PRESUPUESTO`. El backtest está en §5 y es la razón.

---

## 1. QUÉ SE PEDÍA Y QUÉ SE ENCONTRÓ

Se pedía diseñar el mecanismo por el cual el sistema, después de lanzar, mide cada
ángulo con su historial propio, escala lo que funciona, renueva lo que se cansa, apaga lo
que no vende y genera variantes — todo por data.

La mitad de ese mecanismo **ya existe y es buena**: `decidir.py` con su posterior Jeffreys,
sus tres relojes y sus reglas congeladas. Lo que faltaba no era un algoritmo mejor. Faltaban
tres cosas concretas, y las tres se midieron:

| Hueco | Medido | Dónde queda |
|---|---|---|
| **Ningún ángulo tiene identidad ni historial propio.** El motor lee una ventana móvil de 14 días; nadie lee la VIDA del ángulo | 20 perfiles reconstruidos sobre 53 días de serie diaria; 8 de ellos llevaban ≥14 días sin gasto figurando como vivos | resuelto: `perfilar_angulos.py` → `_ESTADO_ANGULOS.csv` |
| **La palanca que más se usa no deja rastro.** El surfing +20 % es la acción diaria por default de la doctrina | `_EVENTOS.csv`: **84 eventos, 0 de tipo `CAMBIO_PRESUPUESTO`** | abierto — §9.1, es la primera deuda |
| **La lectura de causalidad corre sobre data con doble conteo** | `_DIM_ANUNCIOS.csv` suma ventanas `CONTROL`: 904 ventas contra 506 reales | visible: gate nuevo en `atribuir.py` — §7 |

---

## 2. EL MODELO: EL PERFIL DE ÁNGULO

### 2.1 El grano es el ÁNGULO — con evidencia propia, no por preferencia

La pregunta era ángulo o ángulo × concepto. Tres razones, en orden de peso:

1. **La data del repo ya lo midió.** APR-004 calculó el índice de dispersión de las ventas:
   `conjunto-cuenta 1.12` (azar de Poisson puro — no hay nada que aprender ahí),
   `conjunto 1.89`, `angulo_key 2.99` (sobredispersión = señal real). El grano con señal
   es el ángulo. Bajar de ahí es modelar ruido.
2. **La regla congelada lo exige.** `test_decidir.py` congela que *un ángulo con historia
   rentable no se apaga por una mala racha: se le RENUEVA el concepto*. Si la entidad fuera
   ángulo × concepto, renovar el concepto **crearía una entidad nueva y borraría la
   historia** — justo lo que la regla protege. El concepto es el **equipamiento** del perfil,
   no su identidad.
3. **El eje concepto está ciego.** 41 de 54 filas de `_DIM_ANUNCIOS.csv` están en
   `SIN_CLASIFICAR` y `canonico_id` está vacío en 48 de 54. Un grano que no se puede leer
   no es un grano.

> **La salvedad que sí importa: la BANDA DE EDAD.** APR-060 midió que el mismo ángulo, mismo
> producto y mismo creativo da CPA Q473.6 a 25+ contra Q30.6 a 45-60 — **15×**. Un perfil cuyas
> réplicas no comparten banda no es una población, son dos. Por eso el perfil publica
> `banda_homogenea` (viene del `banda_ok` que `decidir.py` ya calcula contra `_DIM_BANDAS.csv`)
> y cuando dice `NO`, su CPA no se usa para coronar.
>
> **Corrido hoy, el resultado obliga a leer todo lo demás con cuidado: 6 de los 17 perfiles
> tienen la banda mezclada, y son los cinco de mayor volumen del portafolio.**
>
> | perfil | estado | ventas acum | CPA acum |
> |---|---|---|---|
> | TINNIDROP · PERDIDA_AUDITIVA | ESCALANDO | 97 | Q62.7 |
> | TINNIDROP · DETERIORO_COGNITIVO | SOSTENIDO | 89 | Q51.3 |
> | NUSAVA · ARDOR | SOSTENIDO | 69 | Q58.1 |
> | CLEARSTEM · RESISTENCIA_INSULINA_SOP | ESCALANDO | 62 | Q36.5 |
> | CLEARSTEM · MEDICOS_FALLARON | ESCALANDO | 36 | Q61.2 |
> | TINNIDROP · NOCHES_SIN_DORMIR | DORMIDO | 12 | Q57.1 |
>
> Cada uno de esos CPA es el promedio de dos poblaciones que APR-060 midió rindiendo hasta 15×
> distinto. **No invalida las órdenes** —`decidir.py` ya trae la bandera y APR-063 muestra que el
> operador la usa—, pero sí significa que **separar la banda tiene más valor esperado que
> cualquier refinamiento de la política de asignación**, y a costo cero: es configuración en
> Meta, no plata.

### 2.2 El esquema — `PRODUCTOS/_ESTADO_ANGULOS.csv`

Una fila por `(producto_key, angulo_key)`. Lo escribe `perfilar_angulos.py`; **nadie lo edita
a mano** (dueño único). 30 columnas, agrupadas por rol:

| Grupo | Columnas | Para qué |
|---|---|---|
| identidad | `producto_key` · `angulo_key` | la llave |
| ciclo de vida | `estado` · `desde` · `estado_anterior` · `evidencia` | dónde está y por qué |
| veredicto del motor | `estado_motor` · `accion_codigo` · `accion_motor` | copiado de `decidir.py`, **no recalculado** |
| historia | `ventas_acum` · `gasto_acum_q` · `cpa_acum_q` · `pct_pd` · `mensajes_acum` · `cierre_acum_pct` · `dias_con_gasto` · `primer_dia` | la vida del ángulo |
| ventana | `ventas_ventana` · `gasto_ventana_q` · `cpa_ventana_q` | lo que el motor mira |
| riesgo | `p_rentable` · `neto_por_q` · `perdida_por_q` · `prioridad_ts` · `pct_gasto_producto` | §4 |
| integridad | `banda_homogenea` · `ventas_control` · `ultimo_dia_gasto` · `dias_sin_gasto` | lo que hace la lectura confiable o no |

**`flujo.py` lo lee sin ninguna extensión de su vocabulario cerrado.** Probado en vivo contra
`flujo.evaluar()` el 09-sep-2026, no supuesto:

```json
{"tipo": "csv", "csv": "_ESTADO_ANGULOS.csv",
 "where": {"producto_key": "{pk}", "estado": ["ESCALANDO", "SOSTENIDO"]}, "min": 2}
```
```
TINNIDROP  → True   4 fila(s) · esperado ≥ 2
CLEARSTEM  → True   3 fila(s) · esperado ≥ 2
NUSAVA     → False  1 fila(s) · esperado ≥ 2      ← dispara generación de variante
VARICOSE   → False  0 fila(s) · esperado ≥ 2
```

Y el `csv_campo` para un ángulo puntual:

```json
{"tipo": "csv_campo", "csv": "_ESTADO_ANGULOS.csv",
 "where": {"producto_key": "{pk}", "angulo_key": "PERDIDA_AUDITIVA"},
 "campo": "estado", "in": ["ESCALANDO", "SOSTENIDO"]}     →  True  estado=«ESCALANDO»
```

### 2.3 El ciclo de vida — 9 estados, cada transición un predicado

El **orden de evaluación es la doctrina**: el primer predicado que se cumple manda.

```
                     ┌─────────────┐
  nace ──────────────► EN_PRUEBA   │  gasto acumulado < 1×BE  (no se lee: no perdió, no se testeó)
                     └──────┬──────┘
                            │ gastó su presupuesto de decisión
                     ┌──────▼──────┐
                     │  MIDIENDO   │  PD consumido, sin veredicto
                     └──┬───────┬──┘
        motor: ESCALAR  │       │  ventas_acum ≥ 5 y CPA acum ≤ BE
                 ┌──────▼──┐ ┌──▼─────────┐
                 │ESCALANDO│ │ SOSTENIDO  │
                 └────┬────┘ └──────┬─────┘
                      └──────┬──────┘
                    motor: RENOVAR (fatiga con historia rentable)
                     ┌───────▼──────┐
                     │  EN_DECLIVE  │───► CAMBIO_CREATIVO ───► RENOVADO ──► vuelve a medir
                     └──────────────┘
   sin gasto ≥3 d ─► DORMIDO      sin gasto ≥14 d ─► APAGADO_ABANDONO
   motor: PAUSAR  ─► APAGADO
```

| Estado | Predicado (código, no prosa) | Por qué existe |
|---|---|---|
| `APAGADO_ABANDONO` | `dias_sin_gasto ≥ 14` | Pasada la ventana de evaluación ninguna data lo respalda |
| `APAGADO` | `estado_motor == PAUSAR` | El diagnóstico es del motor (invariante 13) |
| `DORMIDO` | `dias_sin_gasto ≥ 3` | **Un ángulo sin gasto no rinde mal: no está corriendo.** VARICOSE pasó 21 días en VIVO proponiendo reactivación y contaminando el cierre del portafolio |
| `EN_DECLIVE` | `estado_motor == RENOVAR` | La regla congelada: se renueva el concepto, no se apaga el ángulo |
| `ESCALANDO` | `estado_motor == ESCALAR` | Hay orden vigente |
| `SOSTENIDO` | `ventas_acum ≥ min_ventas_ganador` y `cpa_acum ≤ BE` | Historia rentable sin orden vigente. **No es "midiendo": es un activo** |
| `RENOVADO` | `CAMBIO_CREATIVO` hace ≤ `ventana_dias` | Tras renovar, el perfil espera veredicto; no se lee como si nada hubiera cambiado |
| `EN_PRUEBA` | `gasto_acum_q < BE` | Debajo de 1×BE, cero ventas es esperable hasta en un ganador (`ESCALADO_PLAYBOOK` §1.5) |
| `MIDIENDO` | resto | PD consumido, sin veredicto |

Los 10 casos están congelados en `Ads/_TOOLS/test_perfilar_angulos.py` (17 comprobaciones,
en verde).

---

## 3. LO QUE UN BANDIT DE LIBRO NO CUBRE — y qué de eso resultó ser falso

El encargo pedía modelar cuatro cosas. Tres se confirmaron; **una no resistió la medición**,
y decirlo importa más que haberla implementado.

### 3.1 «Recompensa retrasada y censurada» — el descuento por entrega YA ESTÁ, y aplicarlo otra vez sería contarlo dos veces

El razonamiento del encargo es correcto en la premisa y equivocado en la conclusión:

- **Premisa correcta:** el cobro llega al entregarse (~10 días) y solo se entrega el 70-95 %.
- **Pero `cpa_be_q` YA está expresado por venta REGISTRADA con la entrega descontada.**
  `_DIM_PRODUCTOS.csv` lo dice fila por fila: *«Derivado de `_DIM_PRECIOS` + `_TASA_ENTREGA`
  con TASA DE ENTREGA PROPIA DEL PRODUCTO (90.4 %)»*. Comparar `gasto ÷ ventas_registradas`
  contra ese BE ya incorpora la entrega. **Multiplicar las ventas por la tasa otra vez sería
  descontar dos veces.**
- **Y el retraso de 10 días es ad → COBRO, no ad → VENTA.** La venta se registra el día del
  pedido. Se midió el lag ad→venta sobre las 28 fechas con ventana diaria limpia:

  | producto | k=0 | k=1 | k=2 | k=3 | k=4 | k=5 |
  |---|---|---|---|---|---|---|
  | TINNIDROP | 0.29 | 0.37 | 0.25 | 0.27 | 0.21 | −0.14 |
  | CLEARSTEM | 0.12 | −0.23 | 0.19 | −0.25 | −0.20 | −0.41 |
  | NUSAVA | 0.03 | −0.02 | 0.11 | −0.21 | −0.09 | 0.41 |

  Con n=28 el error estándar de la correlación es ≈0.19: **0.29 y 0.37 no se distinguen**, y
  CLEARSTEM y NUSAVA son ruido. **La data no sostiene ningún lag ad→venta**, y desde luego
  nada parecido a 10 días.

**Conclusión:** no se implementa un descuento por maduración sobre el CPA, porque duplicaría
un descuento que ya está en el break-even. **Lo que sí falta es real y es otro problema:** la
tasa de entrega se mide **por producto**, nunca por ángulo (`_TASA_ENTREGA.csv` viene de Dropi,
que no trae conjunto ni anuncio). Un ángulo que atrae compradores que no reciben tiene CPA
bueno y margen negativo, y hoy eso es invisible. Cómo cerrarlo: §9.3.

### 3.2 Volumen bajo — confirmado, y es la restricción que manda

`PARAMETRIZACION_ADS` §3.6 ya lo tenía calculado: separar dos CPA que difieren 20 % con
bandas que no se toquen pide **~100 ventas por celda**; un test limpio de 4 brazos son ~400
ventas = 7 semanas de TODO el volumen de TINNIDROP. Este es el hecho que descarta el bandit
contextual (§4.3).

### 3.3 Meta castiga la reasignación continua — confirmado y con matiz nuevo

Además del ±20 %/día que la doctrina ya tiene, la documentación de plataforma 2026 agrega algo
que el ciclo de vida usa: **cambiar el creativo dentro de un conjunto vivo también resetea el
aprendizaje**; la forma correcta de renovar es **duplicar el conjunto** e introducir el
creativo nuevo en la copia. Eso es exactamente lo que el estado `RENOVADO` supone.

### 3.4 La señal de Meta no predice la venta — confirmado, y el diseño lo respeta

Toda la capa agrega por `angulo_key` sobre VENTAS. Ninguna decisión de este diseño mira
conversaciones para coronar. El JOIN es por NOMBRE en todo momento; ningún esquema nuevo
depende de `ad_id`.

---

## 4. LA POLÍTICA: LAS TRES OPCIONES, EVALUADAS

### 4.1 Reglas de umbral (lo vigente) — se conservan, y siguen mandando

`decidir.py` no se toca. Sus cuatro estados y sus seis reglas siguen siendo el reglamento
único, y el invariante 13 sigue intacto: **ninguna orden sale sin él**.

Su único defecto real es de **tipo de regla, no de calibración**: el IC 95 % es una regla de
*significancia*, y con 1-3 ventas/día por celda casi nunca se resuelve. El motor ya lo maneja
sin paralizarse (emite `SEGUIR_MIDIENDO` + «faltan ~N ventas»), pero eso deja sin ordenar la
pregunta de **a cuál de las celdas rentables se le da el +20 % de hoy**.

### 4.2 Pérdida esperada + Thompson Sampling — RECOMENDADO como capa de RANKING, no de orden

Dos piezas, ambas sobre el posterior que `decidir.py` ya calcula (cero modelos nuevos):

**(a) El quetzal incremental, descompuesto.** Con `λ|k ~ Gamma(k+0.5, 1)` y `CPA = G/λ`:

```
neto por quetzal     = E[BE·λ/G − 1]        = (BE/G)·a − 1
pérdida por quetzal  = E[(1 − BE·λ/G)+]     = F(c;a) − (BE/G)·a·F(c;a+1)
P(rentable)          = P(CPA ≤ BE)          = 1 − F(c;a)          con a=k+0.5, c=G/BE
```

Cerrado, sin Monte Carlo, sin divergencias en `k=0`. Traduce la incertidumbre a **quetzales
por quetzal invertido**, que es una regla de *decisión* y no de significancia: con 6 ventas el
IC cruza el break-even, pero la pérdida esperada puede ser Q3/día contra Q40/día de ganancia,
y eso sí es decidible. Se autoriza mover plata cuando `neto > 0` **y** la pérdida esperada
diaria ≤ `umbral_perdida_q_dia` (Q10) **y** `P(rentable) ≥ 0.80`.

**(b) Thompson Sampling para el orden.** `prioridad_ts` = P(esta celda es la de menor CPA del
producto), por muestreo del mismo posterior (4 000 muestras, semilla fija). No es un ranking
por CPA puntual: una celda con 3 ventas y CPA bajo **pierde** contra una de 30 ventas y CPA
parecido — que es el comportamiento correcto.

Ya está dando lectura el primer día. En TINNIDROP:

| ángulo | CPA acum | % del gasto | P(ser el mejor) |
|---|---|---|---|
| PERDIDA_AUDITIVA | Q62.7 | **51 %** | **0.00** |
| ACCESIBILIDAD_MEDICO | **Q39.3** | 21 % | 0.02 |
| DETERIORO_COGNITIVO | Q51.3 | 20 % | 0.01 |

En CLEARSTEM, `ANTI_FALSIFICACION` tiene `P(mejor)=0.85` con el 22 % del gasto, mientras
`MEDICOS_FALLARON` tiene `P(mejor)=0.00` con el 38 %. **La plata no está donde está la
probabilidad**, y hasta hoy nada lo decía en una sola pantalla.

**Por qué RANKEA y no ORDENA: ver §5.**

### 4.3 Bandit contextual — ASPIRACIONAL, y conviene decirlo sin adornos

El contexto propuesto (nivel de conciencia, rol de embudo, dolor) **no es estimable con este
volumen, y además está confundido por diseño**. `PARAMETRIZACION_ADS` §2.3 lo muestra medido
sobre CLEARSTEM: el nivel 3 **solo** existe en MOFU y los niveles 1-2 **solo** en TOFU — están
perfectamente confundidos, y ninguna cantidad de data los separa sin un testeo que cruce esas
celdas a propósito. Sumado a las ~100 ventas por celda que pide separar un 20 % de diferencia,
un bandit contextual sobre 4 productos y ~55 ventas/semana ajustaría ruido con más parámetros.

**Veredicto: no.** Se retoma cuando exista `fct_angulo_dia` con ≥2 años de historia o el
portafolio pase de ~10 productos.

---

## 5. EL BACKTEST — y por qué cambió la recomendación

`Ads/_TOOLS/backtest_politica.py`, reproducible:

```bash
python Ads/_TOOLS/backtest_politica.py --sensibilidad --eventos
```

**Método.** Camina día a día del 2026-08-01 al 2026-09-07 (38 días, 481 decisiones) sobre la
serie diaria reconstruida por ángulo desde `_FACT_VENTAS` (solo BASE). En cada día, las dos
políticas deciden con la data que existía ESE día. La política A **no se reimplementa**: se
llama a la propia `decidir.evaluar_celda()`. Después, cada orden se evalúa contra el CPA que
la celda realmente tuvo en los 7 días siguientes.

**Qué hizo cada una:**

| | ESCALAR | RENOVAR | SEGUIR_MIDIENDO |
|---|---|---|---|
| A — `decidir.py` | 164 | 32 | 285 |
| B — pérdida esperada | **273** | 32 | 176 |

Difieren en un solo sentido: **109 veces B escala donde A se queda quieto.** B nunca pisa el
diagnóstico: `PAUSAR` y `RENOVAR` son reglas duras del motor y las respeta (una versión
anterior de B las pisaba en 19 casos — el backtest lo cazó y se corrigió).

**Valor realizado, con degradación 0:**

| política | n | peso incremental | margen neto | ROI |
|---|---|---|---|---|
| A | 157 | Q1 807 | **Q+1 881** | +104 % |
| B | 245 | Q3 095 | **Q+2 667** | +86 % |

B agrega **Q+786** en 38 días. Ese es el número que haría recomendarla… si el supuesto se
sostuviera.

**El supuesto, y por qué NO se sostiene.** No existe el contrafactual: nadie sabe qué habría
pasado si al ángulo X se le hubiera subido el 20 % el 12 de agosto. La evaluación asume que
**subir el presupuesto 20 % no cambia el CPA** — el supuesto de la propia doctrina del
surfing. **APR-057 lo contradice con data:** +63 % de gasto llevó el CPA de Q47.1 a Q75.0
(**+59 %**). Con eso, la sensibilidad:

| degradación del CPA | A neto | B neto | **B − A** |
|---|---|---|---|
| +0 % | Q1 881 | Q2 667 | **+786** |
| +20 % | Q1 266 | Q1 707 | +441 |
| +40 % | Q827 | Q1 021 | +194 |
| **+59 %** (APR-057) | Q512 | Q529 | **+17** |
| +80 % | Q242 | Q106 | **−135** |
| +100 % | Q37 | −Q214 | −251 |

**La ventaja de B vive entre 0 % y ~40 % de degradación. En el único punto que el sistema
midió, las dos políticas empatan; por encima, B es peor.** La política actual aguanta hasta
+104 % de degradación antes de perder plata; B aguanta +86 %: A es **más robusta**.

**Contra `_EVENTOS.csv`.** Las dos políticas emitieron 164 y 273 órdenes de escalar en la
ventana. `_EVENTOS.csv` registra **cero** `CAMBIO_PRESUPUESTO`, así que **no se puede saber
cuáles se ejecutaron**. La comparación contra lo que se hizo de verdad es imposible hoy, y no
por falta de método: por falta de registro.

> **Por eso la recomendación es la que es.** El perfil se implementa y rankea; la política de
> asignación queda especificada, medida y **desactivada por parámetro**
> (`elasticidad_cpa_surfing = SIN_MEDIR`). Se activa el día que ese parámetro tenga un número
> observado. Cambiarla antes es apostar a un valor que nadie midió.

---

## 6. GENERACIÓN CONTINUA DE VARIANTES (explorar vs explotar)

Tres disparadores, todos como parámetros en `_PARAMETROS_OPTIMIZACION.csv`:

| Disparador | Regla | Quién produce |
|---|---|---|
| **(a) Mismo ángulo, concepto nuevo** | el perfil entra en `EN_DECLIVE` (el motor ordenó RENOVAR) | `etapa-10` (qué renovar) → `etapa-9` (produce) → `etapa-render` |
| **(b) Ángulo adyacente no probado** | perfiles en `ESCALANDO`+`SOSTENIDO` < `min_angulos_vivos` (2) | `etapa-3` (sub-dolores del ganador) → `etapa-2` (fichas) |
| **(c) Presupuesto de exploración** | `explora_pct_gasto` = 15 % del gasto diario del producto a brazos sin historia | `gen_lanzador.py` al armar la estructura |

**(b) es una regla de RIESGO DE CARTERA, no de rendimiento**, y por eso dispara *aunque el
único ángulo vivo esté rindiendo bien*. Corriendo hoy, ya marca dos productos:

- **NUSAVA: 1 ángulo vivo** (ARDOR, `SOSTENIDO`, 69 ventas a Q58.1). Si ARDOR fatiga, el
  producto se queda sin a dónde mover la plata.
- **VARICOSE: 0 ángulos vivos** (todos `APAGADO_ABANDONO`) — consistente con su estado
  `PAUSADO`, pero ahora visible con su evidencia en vez de por memoria.

El 15 % no es un default: a $2.99-6/día por conjunto, menos del 10 % no alcanza para que un
brazo nuevo llegue a su presupuesto de decisión (1×BE) en menos de dos semanas, y más del 20 %
le saca al ganador el volumen que sostiene la caja. **Se revisa cuando cambie el presupuesto
por conjunto** — está escrito así en la columna `por_que` del CSV.

---

## 7. CAUSALIDAD: `atribuir.py` SE EXTIENDE, NO SE REEMPLAZA

El script existente está bien pensado: aplica el piso de 1×PD, detecta confounding y se niega
a atribuir cuando la celda ganadora es un solo anuncio. Se le agregaron dos cosas:

**(a) El mismo intervalo que el motor.** La banda era `±1σ` sobre n ventas, que no es un
intervalo de credibilidad: con 2-3 ventas subestima el ancho y con 0 no existe. Ahora sale de
`decidir.ic_cpa()` — el mismo posterior y el mismo `nivel_confianza` del CSV. **No es
cosmético:** el ejemplo que `PARAMETRIZACION_ADS` §5 publica como *«DIFERENCIA REAL: las
bandas no se tocan»* pasa, con el IC 95 % correcto, a **EMPATE ESTADÍSTICO**:

| ángulo | banda ±1σ (antes) | IC 95 % (ahora) |
|---|---|---|
| ACCESIBILIDAD_MEDICO | 32-40 | **29-44** |
| ME_DIJERON_NO_CURA | 37-62 | 37-62 |

Dos partes del sistema que comparan CPA tienen que usar el mismo intervalo, o *«las bandas no
se tocan»* significa una cosa en `atribuir.py` y otra en `decidir.py`.

**(b) Un gate de integridad al frente.** Ver §8.2: la tabla que este script lee está inflada,
y ahora lo dice cada vez que alguien la usa.

Los dos pisos de evidencia que vivían en la prosa de `ETAPA-10.md` (`≥5 ventas`, `≥2 creativos
por nivel`) pasan a `_PARAMETROS_OPTIMIZACION.csv` con su fila en la Guía Madre. Es el mismo
patrón de «dos reglamentos» que la sesión 1 cerró con los umbrales de escalado.

---

## 8. LOS DOS HALLAZGOS DE INTEGRIDAD (medidos, no supuestos)

### 8.1 Las ventanas `CONTROL` se están sumando

`DATA_PLAYBOOK.md` es explícito: `BASE` suma, **`CONTROL` solapa a propósito y NUNCA suma** —
APR-020 lo usa justamente como prueba anti-doble-conteo. Cuatro consumidores no lo respetan:

| Archivo | Línea | Qué contamina |
|---|---|---|
| `Ads/_TOOLS/sembrar_anuncios.py` | 78 (`for r in V`) | `_DIM_ANUNCIOS.csv` → **toda la lectura de causalidad** |
| `Ads/_TOOLS/flujo.py` | 532 `_angulos_acumulados` | el gate de entrada a **FASE 2** |
| `Ads/_TOOLS/flujo.py` | 587 `_ev_concepto_2de2` | el gate de entrada a **FASE 3** |
| `warehouse/models/staging/stg_ventas.sql` | — (ni selecciona la columna) | `fct_conjunto_dia`, `fct_anuncio_dia` |
| `Ads/_TOOLS/decidir.py` | SQL de `cargar_datos_duckdb` | el acumulado (`ventas_acum`, `pct_pd`, guarda de ganador) |

Los generadores financieros **sí** filtran (`gen_pl`, `gen_finanzas`, `gen_dashboard`,
`gen_testeos`, `verificar_monedas`), así que el P&L está limpio.

**Tamaño, medido:**

| producto | con CONTROL | solo BASE | inflado |
|---|---|---|---|
| TINNIDROP | 503 v / $3 258 | 282 v / $1 933 | **+69 %** |
| CLEARSTEM | 215 v / $1 378 | 142 v / $865 | +59 % |
| NUSAVA | 139 v / $1 051 | 69 v / $527 | **+100 %** |
| VARICOSE | 47 v / $309 | 13 v / $126 | **+145 %** |
| **total** | **904 v** | **506 v** | **+79 %** |

**Qué NO rompe, y esto es importante para no exagerar:** las ventanas `CONTROL` viven solo
entre el 2026-07-21 y el 2026-08-10, y **hay cero dentro de la ventana de decisión vigente**
(25-ago → 07-sep). Se corrió `decidir.py` con y sin ellas: **las órdenes de hoy son idénticas.**

**Qué SÍ rompe:**
1. El **acumulado**, que gobierna la guarda de ganador histórico y el `%PD` de la tolerancia.
2. El **gate de fase**. Caso concreto: `NUSAVA/MEMORIA` tiene **0 filas BASE** y sus 7 ventas
   son 100 % `CONTROL`; `flujo.py` lo lista hoy como ángulo ganador («MEMORIA histórico 7v CPA
   Q87.7 ≤ BE Q92.6»). Sin las CONTROL, MEMORIA no existe como celda. *(NUSAVA igual entra a
   FASE 2 por ARDOR, así que el veredicto de fase no cambia — pero el ángulo que se coronaría
   sí podría.)*
3. Toda la **atribución histórica**, y de forma **desigual entre productos**, así que tampoco
   se cancela al comparar niveles.

**Arreglo propuesto (no ejecutado):** una condición en `sembrar_anuncios.py`, un `where` en
`stg_ventas.sql`, y un filtro en los dos predicados de `flujo.py`. **No se tocó nada:**
`flujo.py` es de la sesión 1 y `decidir.py` está bajo invariante 13. Lo que sí se hizo es
**volverlo visible en el punto de uso** — el gate de `atribuir.py` y la columna
`ventas_control` del perfil.

### 8.2 Un ángulo fantasma por una grafía sin dimensión

`GTR0_TINNIDROP_NOCHES-SIN-DORMIR_R1` aparece en `_FACT_VENTAS.csv` ($17.22, 6 ventas) y **no
tiene fila en `_DIM_CONJUNTOS.csv`**; la grafía con el sufijo `+25AÑOS` sí la tiene. El
conjunto se renombró y la grafía nueva no se anexó.

Consecuencia: esas 6 ventas se cuentan como un **ángulo separado** en vez de sumar a
`NOCHES_SIN_DORMIR` — y `flujo.py` lo reporta hoy como el tercer «ángulo ganador» de
TINNIDROP. Mientras tanto, `NOCHES_SIN_DORMIR` figura `DORMIDO`. Es un ángulo que compite
contra sí mismo. Arreglo: anexar la grafía con el **mismo** `angulo_key` (nunca normalizar la
llave). `perfilar_angulos.py` ahora lo canta en cada corrida.

---

## 9. INTEGRACIÓN DE LAS TRES FUENTES

Sin duplicar ninguna tabla. Lo implementado lee; lo propuesto también.

```
Meta (_FACT_ENTREGA_ANUNCIO.csv, ingerir_meta.py)  ─┐
LucidSales (_FACT_VENTAS.csv, bajar_lucidsales.py) ─┼─► decidir.py ─► perfilar_angulos.py
Dropi (_FACT_ENTREGA.csv, _TASA_ENTREGA.csv)       ─┘      (motor)      (_ESTADO_ANGULOS.csv)
                                                                              │
                                                                     flujo.py │ csv_campo
                                                                              ▼
                                                                    VISTAS/PERFILES.html
```

### 9.1 La deuda que manda: registrar `CAMBIO_PRESUPUESTO` — PRIMERA PRIORIDAD

`_EVENTOS.csv` ya tiene el esquema exacto (`valor_antes`, `valor_despues`); solo falta
escribir la fila cuando el operador ejecuta el surfing. Con ~30 eventos se puede estimar la
elasticidad comparando el CPA de la celda 7 días antes contra 7 días después, y con eso:

- se llena `elasticidad_cpa_surfing` y **la política de §4.2 se activa o se descarta con data**;
- el backtest pasa a comparar contra lo que se hizo de verdad, no solo contra el motor;
- APR-057, que hoy es una estimación de ventana completa de portafolio (con ángulo y cuenta
  cambiando a la vez), pasa a medirse por celda.

**Sin esto, ninguna capa de optimización puede mejorar — ni esta ni ninguna otra.**

### 9.2 Un mart nuevo en dbt: `fct_angulo_dia`

Hoy `fct_conjunto_dia` es el grano más alto y el ángulo se deriva del nombre en cada
consumidor. Propuesta:

```sql
-- marts/fct_angulo_dia.sql — el hecho diario al grano que TIENE señal (APR-004)
select v.fecha, v.producto_key, d.angulo_key,
       sum(v.ventas) as ventas, sum(v.mensajes) as mensajes, sum(v.spend_usd) as spend_usd,
       count(distinct v.conjunto) as conjuntos,
       bool_and(d.banda_coincide) as banda_homogenea
from {{ ref('stg_ventas') }} v
left join {{ ref('dim_conjunto') }} d on d.conjunto = v.conjunto and d.cuenta_alias = v.cuenta_alias
where d.angulo_key is not null
group by 1,2,3
```

Con tres tests: `not_null` en `angulo_key`, `unique` sobre `(fecha, producto_key, angulo_key)`,
y uno de relación que exija que la suma de ventas por producto **cuadre con `stg_ventas`**
— ese último es el que cazaría el hueco de dimensión de §8.2 solo.

**Requisito previo:** `stg_ventas.sql` tiene que filtrar `rol_ventana = 'BASE'` (§8.1), o el
mart nace con el doble conteo adentro.

### 9.3 La tasa de entrega por ángulo — abierta

Hoy `_TASA_ENTREGA.csv` es por producto/mes porque el export de órdenes de Dropi no trae
conjunto ni anuncio. Mientras siga así, un ángulo que atrae compradores que no reciben tiene
CPA bueno y margen negativo, y es invisible. Cómo cerrarlo: verificar si LucidSales pasa a
Dropi alguna referencia del anuncio en la orden; si la pasa, `ingerir_lucidsales.py` puede
poblar una columna nueva y `_TASA_ENTREGA.csv` gana el grano. **Es una pregunta para el
operador, no una decisión de sistema** — §11.

---

## 10. INVESTIGACIÓN: LO QUE SE REUTILIZA Y LO QUE SE DESCARTÓ

### 10.1 Lo que se adoptó (como IDEA, cero dependencias nuevas)

| Fuente | Qué aporta | Cómo entró |
|---|---|---|
| Vernade, Cappé & Perchet, *[Stochastic Bandit Models for Delayed Conversions](https://arxiv.org/abs/1706.09186)* | El modelo formal de conversión retrasada **y censurada** con ventana de observación | Confirmó el marco, y sirvió para **descartar** aplicarlo: acá la censura es sobre el cobro, no sobre la conversión (§3.1) |
| Wang et al., *[Adaptive Experimentation with Delayed Binary Feedback](https://arxiv.org/abs/2202.00846)* (WWW'22, JD.com) | Estimar el objetivo antes de que se materialice y asignar sobre el estimado | Es la forma correcta del problema; se descartó su maquinaria por volumen (§4.3) |
| *[Thompson Sampling with Unrestricted Delays](https://arxiv.org/abs/2202.12431)* | TS es **más robusto que UCB con retraso largo**, porque la aleatorización amortigua el feedback tardío | Razón para preferir TS sobre UCB en `prioridad_ts` |
| Chapelle & Li, *[An Empirical Evaluation of Thompson Sampling](https://www.microsoft.com/en-us/research/wp-content/uploads/2016/02/thompson.pdf)* | TS con posteriores conjugados funciona bien en producción publicitaria | Sostiene las ~30 líneas sobre el posterior existente |
| *Expected loss / «threshold of caring»* ([varianceexplained](http://varianceexplained.org/r/bayesian-ab-testing/)) | La pérdida esperada convierte incertidumbre en un número de negocio y **permite decidir donde la significancia no llega** | **Es el corazón de §4.2** |
| Documentación de plataforma Meta 2026 (learning phase) | ±20 % es el techo sin reset; **cambiar creativo en un conjunto vivo resetea — hay que duplicar** | Valida el ±20 % y define cómo se ejecuta `RENOVADO` (§3.3) |

### 10.2 Lo que se descartó, y por qué

| Descartado | Razón |
|---|---|
| **`SMPyBandits`, `fidelity/mabwiser`** | Librerías de investigación. El posterior ya existe en `decidir.py` y el ranking son ~30 líneas con `scipy`, que ya está instalado. Una dependencia nueva tendría que aportar algo que esas 30 líneas no dan; ninguna lo hace para 1 brazo × 6 celdas × decisión diaria |
| **`kinosal/optimizer`** | Demo Flask de un autor, sin mantenimiento. No cumple el criterio de adopción real |
| **`bgalbraith/bandits`** | Librería didáctica, sin actividad. Mismo caso |
| **`langchain-ai/langgraph`** | Ya evaluado y descartado por la sesión 1: re-plataformado, no un paso. Nada que agregar |
| **Bandit contextual (cualquier implementación)** | No es un problema de librería: **no hay volumen y el contexto está confundido por diseño** (§4.3) |
| **Catálogos de skills** (`coreyhaines31/marketingskills`, `anthropics/skills`, `ComposioHQ`, `VoltAgent`) | Regla registrada: ninguna skill global. `gen_grafo.py --comparar` mide lo que pesa cada una. Además, frameworks genéricos de CRO **chocarían con la doctrina de los mentores**, que ya está parametrizada y verificada por hook |
| **Reasignación intradía / cada hora** | Contradice el ±20 %/día y destruiría la señal que quiere leer. APR-057 ya lo midió en su versión suave |
| **Descuento explícito por maduración sobre el CPA** | **Sería contar dos veces**: `cpa_be_q` ya descuenta la tasa de entrega. Y el lag ad→venta no es medible en la data (§3.1) |

> **Sobre la búsqueda de prácticas de producción para COD/WhatsApp con conversión offline:** no
> hay literatura ni repos con adopción real. Lo que se publica es genérico de dropshipping COD
> (tasas de entrega, RTO) o bandits académicos sobre clics. **El sistema no está por detrás del
> estado del arte en esto: está por delante de lo que hay publicado**, porque `decidir.py` ya
> combina posterior bayesiano, tolerancia acumulada y detector de fatiga sobre venta real.

---

## 11. PREGUNTAS ABIERTAS (cambian el diseño; no se asumen)

1. **¿Se corrige el filtro `rol_ventana = BASE` en los cuatro consumidores de §8.1?** Es
   ~4 líneas y cambia el acumulado de todos los ángulos, los dos gates de fase de `flujo.py` y
   el warehouse. `flujo.py` es de la sesión 1 y `decidir.py` cae bajo el invariante 13, así que
   **no se tocó nada**. Recomendación: sí, y en el mismo commit, con `test_flujo.py` y
   `test_decidir.py` corridos antes y después.
2. **¿Quién escribe `CAMBIO_PRESUPUESTO`?** ¿El operador a mano al hacer el surfing, o la
   sesión cuando ejecuta la orden por MCP con confirmación? Lo segundo es más confiable y
   encaja con la decisión del 09-sep, pero solo cubre lo que pasa por MCP.
3. **¿La orden de escalado debe pasar a decidirse por pérdida esperada** una vez medida la
   elasticidad, o se queda en el IC 95 % por robustez? El backtest dice que A es **más robusta**
   (aguanta +104 % de degradación contra +86 %) y que B solo gana si la degradación real está
   bajo ~40 %. Es una decisión de apetito de riesgo del operador, no de sistema.
4. **¿Se puede llevar la tasa de entrega al grano del ángulo?** (§9.3) Depende de si Dropi
   recibe alguna referencia del anuncio desde LucidSales. Si no se puede, hay que decidir si el
   sistema acepta ese punto ciego o si se mide por muestreo manual.
5. **El ángulo fantasma de §8.2:** ¿se anexa la grafía a `_DIM_CONJUNTOS.csv` o se registra en
   `_ALIAS_CONJUNTOS.csv`? Las dos funcionan; la segunda es la que `alias.py` ya sabe resolver.

---

## 12. QUÉ QUEDÓ CONSTRUIDO

| Pieza | Qué es | Gate |
|---|---|---|
| `Ads/_TOOLS/perfilar_angulos.py` | El perfil y su ciclo de vida → `PRODUCTOS/_ESTADO_ANGULOS.csv` + `VISTAS/PERFILES.html`. Consume `decidir.py`, no lo recalcula | `test_perfilar_angulos.py` — 17 comprobaciones |
| `Ads/_TOOLS/backtest_politica.py` | La comparación de políticas contra el futuro observado, con curva de sensibilidad | reproducible; es la evidencia de §5 |
| `PRODUCTOS/_PARAMETROS_OPTIMIZACION.csv` | 11 parámetros con `dueno` y `por_que` | `verificar_guia_madre.py`, ahora con drift inverso sobre este CSV también |
| `DOCTRINA/GUIA_MADRE_PARAMETRIZADA.md` §14 | 11 filas nuevas | 78 variables declaradas · **32** verificadas (antes 67 · 21) |
| `Ads/_TOOLS/atribuir.py` | IC 95 % del motor + gate de integridad | corre en cada lectura |
| `VISTAS/_MANIFIESTO.json` v6 | vista `perfiles` declarada | `gen_app.py --verificar` en verde |

**Costo en tokens de sesión: cero.** `gen_grafo.py --comparar`: arranque en frío y los cuatro
techos por fase quedaron **idénticos** (`=`). Los dos CSV nuevos entran al inventario (33 → 35)
sin huérfanos, porque tienen consumidor declarado.
