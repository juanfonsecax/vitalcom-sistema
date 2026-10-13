# CONTABILIDAD — NORMA DEL SISTEMA VITALCOM

> **Para qué existe este archivo.** Para que la pregunta «¿estoy ganando dinero?»
> tenga **una sola respuesta**, calculada siempre igual, sin depender de cómo se
> pregunte ni de quién la conteste. Todo lo de acá es determinista: entra el mismo
> archivo, sale el mismo número. Si un cálculo no está definido en este documento,
> **no se hace** — se agrega la regla acá primero.
>
> **Dueño único.** Los parámetros viven en `PRODUCTOS/_PARAMETROS_FINANZAS.csv`.
> El motor es `Ads/_TOOLS/gen_pl.py`. Ningún número se escribe a mano ni vive
> dentro del código.

---

## 1. EL PROBLEMA QUE RESUELVE: ESTO ES CONTRA ENTREGA (COD)

En un negocio COD, **la venta y el cobro no ocurren el mismo día**. Una orden
tomada el 28-jul puede entregarse el 2-ago y devolverse el 6-ago. Si se mezclan
las fechas, cualquier número sale mal.

**Los tres desfases del negocio, medidos sobre 356 órdenes reales (agosto):**

| Desfase | Mediana | Estado |
|---|---|---|
| Venta → entrega al cliente | **1 día** (p95: 4) | ✅ MEDIDO |
| Venta → devolución confirmada | **7 días** (media 8.1) | ✅ MEDIDO |
| Entrega → acreditación en la cartera de Dropi | **1 día** | ✅ MEDIDO (n=297) |

⚠️ **La devolución tarda 7× más que la entrega.** Esa asimetría es la trampa
central del negocio: cuando mirás un cohorte joven, las entregas ya se
confirmaron pero las devoluciones todavía no, así que **todo se ve mejor de lo
que es**.

**Evidencia (mismo cohorte de agosto, leído a distintas edades):**

| Edad del cohorte | Tasa de entrega aparente |
|---|---|
| 3 días | 86.3% ← optimista |
| 7 días | 85.2% |
| **10 días** | **83.0%** ← se estabiliza |
| 14 días | 83.1% |

→ **REGLA DE MADURACIÓN: un cohorte con menos de 10 días no es concluyente.**
El sistema venía usando 3 días, que es el ciclo de la *entrega*, no el de la
*devolución*. Todo veredicto tomado a 3 días leía ~3.3 puntos optimista.

---

## 2. LAS TRES VISTAS — NUNCA SE MEZCLAN

Cada una responde una pregunta distinta. Usar la equivocada es el error más caro
del sistema: etiquetar como «caja» un cálculo que en realidad es de cohorte.

### VISTA A — COHORTE (por fecha de ORDEN) → *«¿la pauta de esta semana rindió?»*

Toma las órdenes **creadas** en la ventana y las compara contra la pauta gastada
**en esa misma ventana**. Es la única vista válida para **decidir sobre campañas**:
apagar, escalar, coronar un ángulo.

- Alinea causa y efecto: el anuncio del martes y la orden del martes.
- **Siempre se reporta con su % de maduración.** Cohorte < 10 días = PRELIMINAR.
- Es la vista que alimenta el dashboard y el reporte semanal.

### VISTA B — CAJA (por fecha del MOVIMIENTO) → *«¿cuánto dinero entró de verdad?»*

✅ **HABILITADA**, con el **historial de cartera de Dropi**.

Ese archivo es el **libro de caja** del negocio: cada fila es plata que se movió
de verdad, fechada por **cuándo ocurrió**, no por cuándo se tomó la orden.

- `ENTRADA POR GANANCIA EN LA ORDEN` → Dropi acredita la ganancia **neta** de una
  orden entregada (no el recaudo bruto: ya descontó flete y producto).
- `SALIDA DE COBRO DE DEVOLUCIÓN POR ENTREGA NO EFECTIVA` → el costo **real** de
  una entrega fallida. **Es el único lugar donde aparece.**

Trae `ORDEN ID`, así que cruza uno a uno con el export de órdenes — y cruza
**exacto**: 297 de 297 movimientos coinciden al céntimo con la columna `GANANCIA`.

**Dropi acredita en ~1 día** desde la entrega (mediana, n=297).

**El arrastre que esta vista revela y el cohorte no puede ver:** en agosto,
**31 acreditaciones (Q3,650) vinieron de órdenes tomadas en julio**. Se vendió un
mes y se cobró al siguiente. Por eso las dos vistas son necesarias.

### VISTA C — COHORTE MADURO (cierre definitivo) → *«¿cuánto dejó de verdad ese mes?»*

La vista A releída cuando el cohorte ya pasó los 10 días. Es la **única cifra
definitiva**. Se corre una vez al mes, sobre el mes anterior ya cerrado.

---

## 3. EL ESTADO DE RESULTADOS — ORDEN FIJO, SIN EXCEPCIONES

Siempre estas líneas, siempre en este orden. Ninguna se salta, ninguna se agrupa.

```
  (+)  VENTA BRUTA ENTREGADA        lo que el cliente pagó en la puerta
  (−)  Costo de producto            PRECIO PROVEEDOR X CANTIDAD (Dropi)
  (−)  Flete de entrega             PRECIO FLETE (Dropi)
  ────────────────────────────────
  (=)  MARGEN LOGÍSTICO             ← esto es lo que Dropi llama «Ganancias»
  (−)  Costo de devoluciones        n_devueltas × costo_devolucion_evento_q
  (−)  Costo de personal            n_entregadas × costo_admin_q
  (−)  Otros gastos operativos      n_entregadas × otros_gastos_q
  ────────────────────────────────
  (=)  MARGEN DE CONTRIBUCIÓN       lo que queda antes de pagar publicidad
  (−)  Publicidad (Meta)            USD × tasa_usd_gtq  [CP1: COP ÷ tasa_cop_usd]
  ────────────────────────────────
  (=)  MARGEN OPERATIVO             ← el número que dice si el negocio funciona
  (−)  Gastos fijos                 software, suscripciones, herramientas
  ────────────────────────────────
  (=)  RESULTADO NETO               lo que realmente te quedó
```

**Advertencias que van SIEMPRE pegadas al resultado:**

1. `MARGEN LOGÍSTICO` es la cifra que muestra el panel de Dropi. **No es tu
   ganancia**: no descuenta publicidad, devoluciones, personal ni software.
   Confundirla con la ganancia infla el resultado ~2×.
2. El costo de devolución **NO aparece nunca en el export de órdenes** (ahí la
   columna sale Q0 siempre). Se suma **siempre**, una vez por cada orden en
   estado `DEVOLUCION`. Con el historial de cartera se usa el cobro **real** de
   cada orden; sin él, el promedio medido **Q28.02** (n=56 cobros reales).
3. Un gasto solo entra en `Gastos fijos` si el operador **confirmó** que es del
   negocio. **Nunca se atribuye por descarte** (APR-030). Y ojo: un cargo puede
   salir de la cuenta sin ser del negocio — ver §3-ter (gasto vs retiro).

---

## 3-bis. MONEDAS — LA MONEDA LA DICE EL MERCADO DEL PRODUCTO

Cada producto **cobra en la moneda de su mercado** (`moneda` de
`PRODUCTOS/_DIM_MERCADOS.csv`; `python Ads/_TOOLS/mercado.py --producto PRODUCTO_KEY`) y
**paga la publicidad en la moneda de su cuenta** (GT: dólares por Meta). El dinero de
mercados distintos nunca se suma. Un valor convertido de más o de menos se ve
plausible y nadie lo nota: un error de factor 7.62 en la pauta convierte una
ganancia en pérdida sin que ninguna cifra parezca absurda. Por eso la regla está
escrita **y se verifica sola**.

**Alcance de esta contabilidad.** Las tablas de abajo son las del mercado **GT**: su
contabilidad es Dropi GT + banco (`gen_pl.py`). La contabilidad del mercado CO está
pendiente: sus ventas (`total_q`) entran en COP, sin Dropi GT ni banco GT, y no se
mezclan con este estado de resultados.

| De dónde viene | Qué trae | Moneda | Qué le hace el sistema |
|---|---|---|---|
| **Dropi GT** — órdenes | total, flete, costo proveedor, ganancia | **QUETZALES** | nada, entra tal cual |
| **Dropi GT** — historial de cartera | entradas y cobros de devolución | **QUETZALES** | nada, entra tal cual |
| **LucidSales** | `total` — la venta | **moneda del mercado del producto** (GT: quetzales · CO: pesos) | nada, entra tal cual |
| **Meta** (`_FACT_ENTREGA.csv`, vía `gasto.py`) | `spend` — la pauta | **DÓLARES** | × la `tasa` del producto (GT: `tasa_usd_gtq`) |
| **LucidSales** | `spend` — la pauta | **DÓLARES** | solo donde Meta no tiene cobertura (día de producto sin fila de Meta); el reporte dice cuánta pauta vino de cada fuente |
| **Banco GT** (Relay) | cargos de Meta y todo lo demás | **DÓLARES** | × `tasa_usd_gtq` |
| **Cuenta CP1** — única excepción | `spend` de esa cuenta | **COP** | ÷ `tasa_cop_usd` → USD → × `tasa_usd_gtq` |

⚠️ **Dos trampas visuales:**

1. El panel de Dropi muestra sus totales con el símbolo `$`, pero **son
   quetzales**. Leer "$80,521 vendido" como dólares infla el negocio 7.6×.
2. La cuenta de Relay es en dólares, así que **un gasto hecho en Guatemala
   aparece ahí ya convertido a USD**. Para leerlo en quetzales hay que volver a
   multiplicarlo por la tasa. (Ejemplo: `MINIMED GEDIATRIA $901.59` en el
   extracto = **Q6,870** de gasto real.)

**La tasa vive en un solo lugar**, `PRODUCTOS/_PARAMETROS_FINANZAS.csv`. Ningún
script la tiene escrita adentro — antes estaba hardcodeada en dos motores, lo
que garantizaba que algún día dijeran cosas distintas.

⚠️ `tasa_usd_gtq` está marcada **DECLARADA**, no medida: la cuenta es en dólares
y el negocio cobra en quetzales, así que la conversión real solo se puede medir
cuando se cambie divisa. Cuando eso pase, se mide y se actualiza el CSV.

**Verificación automática:** `python Ads/_TOOLS/verificar_monedas.py` comprueba
6 invariantes sobre la data real (no sobre el código) y **sale con error si
alguna falla**: la tasa no hardcodeada, los tickets dentro de la escalera de
precios, el gasto diario plausible en USD, CP1 normalizada, y el ROAS del
portafolio y de cada semana en rango. Corre solo en cada build del dashboard y
su veredicto se muestra ahí.

---

## 3-ter. GASTO DEL NEGOCIO vs RETIRO PERSONAL

Que un cargo salga de la cuenta del negocio **no lo convierte en un gasto del
negocio**. Son dos cosas distintas y confundirlas rompe el resultado:

| | ¿Reduce la GANANCIA? | ¿Reduce la CAJA? |
|---|---|---|
| **Gasto del negocio** (pauta, software, personal) | **SÍ** | sí |
| **Retiro personal** (plata del dueño, gastada en lo suyo) | **NO** | sí |

Un retiro personal es plata que el negocio **ya ganó** y que el dueño saca. No
es un costo de operar, así que no puede restarse de la ganancia — si se restara,
el negocio parecería menos rentable de lo que es y las decisiones de escalar se
tomarían sobre un número falso. Pero sí sale de la cuenta, así que la caja baja.

**Las 4 clasificaciones**, en `PRODUCTOS/_DIM_GASTOS.csv`:

| Clasificación | Qué es | Dónde impacta |
|---|---|---|
| `NEGOCIO_PAUTA` | los cargos de Meta | ya contado en la línea de Publicidad — **no se resta dos veces** |
| `NEGOCIO_FIJO` | software y herramientas (Lucid, etc.) | resta del `RESULTADO NETO` |
| `PERSONAL` | gastos del dueño pagados desde la cuenta | **solo** la caja, nunca el resultado |
| `SIN_CLASIFICAR` | todavía sin confirmar | **nada**: se lista y se pregunta (APR-030) |

**Un cargo nuevo entra como `SIN_CLASIFICAR` por defecto** y ahí se queda hasta
que el operador diga qué es. Nunca se adivina por el nombre del comercio.

**Agosto quedó clasificado al 100% — ningún cargo pendiente:**

| Cargo | Clasificación | Monto | Efecto |
|---|---|---|---|
| Facebook | `NEGOCIO_PAUTA` | $1,871.89 = Q14,264 | ya en la línea de Publicidad |
| Proxy-Cheap | `NEGOCIO_FIJO` | $26.29 = Q200 | resta del resultado |
| Anthropic | `NEGOCIO_FIJO` | $21.53 = Q164 | resta del resultado |
| MINIMED | `PERSONAL` | $901.59 = Q6,870 | **solo caja**, no el resultado |

**Gastos por mercado.** Cada fila de `_DIM_GASTOS.csv` declara su `mercado` (`GT`, `CO` o
`COMPARTIDO`). Un gasto de un mercado va entero a ese mercado; uno `COMPARTIDO` se reparte según
`reparto_gasto_compartido` de `_PARAMETROS_FINANZAS.csv`: `ACTIVOS_IGUAL` = partes iguales entre los
mercados con actividad en el mes (órdenes de Dropi o pauta de Meta), y un mercado sin actividad no
paga. Vale igual para los fijos y para los retiros personales. El banco no dice a qué mercado
pertenece cada cargo, por eso las suscripciones por mercado también van `COMPARTIDO`.

**Retiros de la cartera de Dropi.** Un retiro de la billetera se clasifica por su CONCEPTO con
`PRODUCTOS/_DIM_RETIROS.csv`: `TRANSFERENCIA_PROPIA` (a una cuenta del propio operador, su LLC) o
`RETIRO_PERSONAL` (pagar a la familia o cosas personales). Ninguno es gasto ni toca el resultado: son
movimientos de caja, como el `PERSONAL` del banco, y se muestran aparte. Lo que ninguna regla calza queda
`SIN_CLASIFICAR`: se lista y se pregunta.

**Cierre de agosto:** resultado del negocio **Q16,232** · retiro personal Q6,870
· **caja que quedó en la cuenta Q9,911**.

Las suscripciones Lucid (`THE LUCID HOLDING`, `LUCIDSALES`) también son del
negocio, pero su primer cargo aparece el 01-sep: entran en el cierre de
septiembre (~$114/mes = Q869).

---

## 4. ECONOMÍA UNITARIA — «¿cuánto me deja cada venta?»

Por producto, siempre con esta estructura (el ejemplo del operador: producto de
Q35 vendido a Q200 con Q50 de pauta):

```
  Precio de venta (ticket promedio real)          Q 211.21
  −  Costo del producto                           Q  63.08
  −  Flete                                        Q  35.26
  −  Devolución amortizada                        Q   4.35   ← (1−TE)/TE × costo_evento
  −  Admin y otros                                Q   6.08
  ──────────────────────────────────────────────────────────
  =  MARGEN ANTES DE PUBLICIDAD                   Q 102.44   ← ESTE es el break-even del CPA
  −  CPA real (pauta ÷ ventas)                    Q  58.00
  ──────────────────────────────────────────────────────────
  =  GANANCIA POR VENTA                           Q  44.44
```

**El break-even NUNCA se escribe a mano.** Es el `MARGEN ANTES DE PUBLICIDAD`,
derivado de la escalera de precios y de la tasa de entrega del producto. Si el
CPA real lo supera, ese producto pierde dinero en cada venta.

**La devolución se amortiza sobre las entregadas, no sobre las vendidas:** por
cada venta entregada hay `(1−TE)/TE` devoluciones que alguien tiene que pagar.

---

## 5. QUÉ SE PIDE, CUÁNDO Y PARA QUÉ

| # | Archivo | Frecuencia | Alimenta | Si falta, se rompe |
|---|---|---|---|---|
| 1 | **LucidSales** — export de **1 solo día** (ayer) | diaria | atribución venta↔anuncio | no hay CPA por ángulo; no se puede coronar ni matar |
| 2 | **Ads Manager** — nivel conjunto, desglose por día | diaria/semanal | frecuencia, CTR, fatiga | no se detecta fatiga de creativo |
| 3 | **Dropi — órdenes**, ventana **de 60 días móviles** (no el mes) | semanal | tasa de entrega, fletes, costo de producto | las tasas se desactualizan y el break-even queda mal |
| 4 | **Dropi — historial de cartera** | mensual | **la vista de CAJA** + costo REAL de devolución | no hay caja; la devolución vuelve a ser un promedio |
| 5 | **Extracto bancario** (Relay) | mensual | pauta realmente cobrada + gastos fijos | no hay cierre real; la cobertura no se puede medir |

⚠️ **El export de Dropi debe ser de 60 días móviles, no del mes calendario.** Un
export filtrado por mes calendario no trae las órdenes del mes anterior
entregadas en el mes actual — que es exactamente el arrastre que hay que medir.

⚠️ **El extracto bancario no se concilia por mes calendario** (APR-070). Meta
cobra por umbral y con días de retraso: el extracto de agosto no tenía ningún
cargo del 1 al 8, porque cayeron en el de julio. La conciliación se corre sobre
la **intersección** de las dos series, nunca sobre el mes del extracto.

---

## 6. REGLAS DE INTEGRIDAD (se verifican solas, el script aborta si fallan)

1. **Cuadre de Dropi:** `venta bruta − costo producto − flete` debe dar exacto la
   columna `GANANCIA` del export. Si no cuadra, el export cambió de formato.
2. **Cuadre bancario:** la suma de los movimientos debe dar el `Withdrawals` del
   resumen del extracto. Si no, el parser se rompió.
3. **Una sola fórmula de contribución** en todo el sistema: `gen_pl.py`,
   `gen_finanzas.py` y `gen_dashboard.py` deben dar el mismo total sobre la misma
   ventana. Se verifica en cada corrida.
4. **Cohorte < 10 días ⇒ se marca PRELIMINAR.** No se declara ganador, no se
   manda apagar por ventas, no se reporta como cierre.
5. **Ningún número a mano.** Todo sale de los CSV o de los archivos del operador.

---

## 7. LO QUE HOY NO SE PUEDE RESPONDER (y qué falta para poder)

| Pregunta | Estado | Qué falta |
|---|---|---|
| ¿Cuánta plata entró de verdad este mes? | ✅ sí | — (historial de cartera) |
| ¿Cuánto cuesta realmente una devolución? | ✅ Q28.02 medido | — (n=56 cobros reales) |
| ¿Cuánto tarda Dropi en acreditar? | ✅ 1 día | — (n=297) |
| ¿Rindió la pauta de esta semana? | ✅ sí | — |
| ¿Cuál producto deja más por venta? | ✅ sí | — |
| ¿Meta me cobra de más? | 🟡 parcial | extracto de julio (cerrar el arrastre) |
| ¿MINIMED GEDIATRIA es del negocio? | 🔴 sin confirmar | respuesta del operador |

**Honestidad por diseño:** una fila en 🔴 no se rellena con una estimación
disfrazada de dato. Se reporta como faltante hasta que llegue el archivo.
