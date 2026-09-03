# ANÁLISIS — MENTOR (Calet/Joaquín, 2 clases ago-2026) vs SISTEMA VITALCOM

> **SOLO ANÁLISIS — nada implementado.** Ningún agente lee esta carpeta.
> La decisión de qué se implementa queda para Juan. Fecha: **2026-08-21**.
> Fuentes: 2 transcripciones de clase (estructura 1-1-5 / 1-1-7 / escalado CBO
> + banco de conceptos de 500 marcas USA) + 3 capturas de pizarra.
> Contraste hecho contra: `CLAUDE.md`, `.claude/agents/ETAPA-6.md`,
> `CALENDARIO_ESCALADO.md`, `ESCALADO_PLAYBOOK.md`, `Ads/_SWIPE/_CATALOGO_CONCEPTOS.md`
> y la data real de `PRODUCTOS/` (serie 17-jul → 20-ago, 27 días sin huecos).

---

## 0. TL;DR — EL VEREDICTO EN 6 LÍNEAS

1. **El 1-1-5 se adopta**, pero no por la razón que da la clase. Se adopta porque la data propia
   ya demostró que el testeo de 6 conjuntos **no mide nada** (dispersión 1.12 = azar de Poisson).
2. **El banco de conceptos + generación en lote es el cambio de mayor retorno y menor riesgo.**
   Es el cuello de botella real: 19 creativos distintos para 25 conjuntos.
3. **El escalado intradía (+20% varias veces al día) NO se adopta como default.** La data propia
   (APR-057) dice que el techo se rompe por falta de creativos, no por cadencia de subida.
4. **El objetivo "Ventas" sin CAPI es cosmético.** El cambio real es mandarle a Meta el evento
   de compra, no cambiar el dropdown.
5. **"El flujo antes que la estructura" es correcto y el sistema está reprobando**: cierre 8.2%
   contra el 15-20% que exige la clase.
6. **La palanca más grande del sistema hoy no está en la clase**: es la banda de edad (APR-060).
   Vale ~24 ventas cada 4 días. Más que todo el rediseño de estructura junto.

---

## 1. QUÉ DICE LA CLASE (destilado, separando MÉTODO de CIFRA)

| # | Afirmación del mentor | Cifra dada (COP) | Equivalente USD/Q |
|---|---|---|---|
| M1 | Testeo = **1 campaña · 1 conjunto · 5 anuncios**, ABO, 1 ángulo/concepto por anuncio | 16.000–25.000/día | **$3.95–$6.17** · Q30–47 |
| M2 | No se corre UNA sola 1-1-5: se corren **2-3 campañas 1-1-5 en paralelo** | — | — |
| M3 | ABO en testeo porque **reparte entre los 5 anuncios**; CBO elige uno solo | — | — |
| M4 | Escalado = **1-1-7 CBO**: el ganador 7 veces (Post ID o subido de cero) | 60.000–72.000/día | **$14.8–$17.8** · Q113–136 |
| M5 | Escalado masivo = duplicar conjuntos ×2 y campañas ×4-5 | hasta 500.000/día | **$123/día** · Q940 |
| M6 | **Surfing +20% varias veces AL DÍA**, hasta las 2-3 PM, con gate de CPA bajo | — | — |
| M7 | Duplicar la campaña ganadora **al presupuesto inicial**, no al actual | — | — |
| M8 | Objetivo **Ventas** (maximizar conversaciones) está rindiendo mejor que Tráfico | — | — |
| M9 | **Banco de 500 marcas USA validadas** → Ad Library → swipe de conceptos → adaptar el producto propio con IA (10 conceptos en un prompt) | — | — |
| M10 | **"Primero el flujo, después la estructura"**: con 15-20% de cierre, cualquier estructura vende | 15-20% cierre | — |
| M11 | Del video ganador se extraen los ángulos que menciona el audio → 4 imágenes distintas | — | — |
| M12 | En escalado **no apagar** anuncios: Meta ya optimiza bien | — | — |
| M13 | Multi-cuenta / multi-fanpage / crear fanpage casi a diario | — | — |

> ⚠️ **Ninguna cifra COP se copia.** El sistema opera en Q/USD y Guatemala es mercado más barato
> que Colombia. Se copia el método y se recalcula con la fórmula propia (`CALENDARIO_ESCALADO.md` §1.5).

---

## 2. QUÉ HACE HOY EL SISTEMA (estado verificado 21-ago)

```
FASE 1 (testeo):   1 campaña · 6 conjuntos · 2 anuncios/conjunto (duplicado)
                   ABO $2.99/conjunto = $17.94/día · OUTCOME_TRAFFIC + CONVERSATIONS
                   6 ángulos distintos × concepto FIJO (C2_BENEFICIOS)
                   Etapa 1 días 0-3 → corte por conversación → Etapa 2 días 4-8 a $5.98

FASE 2 (escalado): 1 campaña · 6 conjuntos (microángulos) · 2 anuncios/conjunto
                   ABO · surfing +20% UNA vez al día, solo mañana
                   Post ID · multicuenta · multifanpage
```

**Realidad medida en la ventana 17-20 ago (184 filas BASE, 4 días):**

| Métrica | Valor |
|---|---|
| Campañas vivas | 6 |
| Conjuntos vivos | **25** |
| **Anuncios (creativos) distintos** | **19** |
| Creativos únicos por conjunto | **0.76** ← hay más conjuntos que creativos |
| Mensajes | 487 |
| Ventas | 40 |
| **Tasa de cierre msj→venta** | **8.2 %** |
| Gasto | $276 (Q2.104) |
| CPA | Q52.5 |
| CTR | 3.22 % |
| `_DIM_CREATIVOS.csv` | 12 filas, **las 12 en `PENDIENTE_GENERAR` desde el 26-jul** |

---

## 3. PUNTO POR PUNTO — VEREDICTO CON EVIDENCIA PROPIA

### 3.1 · M1/M2/M3 — LA ESTRUCTURA 1-1-5 → **ADOPTAR, PERO EN LA FASE DE CONCEPTOS**

> 🔴 **CORRECCIÓN 21-ago (posterior a la redacción original de esta sección).** La versión
> original recomendaba migrar la FASE 1 (testeo de ÁNGULOS) a 1-1-5. **Se retira.** Ver §9:
> el 1-1-5 va en el testeo de CONCEPTOS, no en el de ángulos. El análisis de abajo sobre
> aprendizaje y objetos sigue siendo válido — cambia la fase a la que se aplica.

**El argumento de la clase es débil.** "Meta reparte entre los 5 anuncios" es exactamente
lo contrario de lo que el propio `ETAPA-6.md` documenta como el fenómeno *"cuando Meta se
enamora de un anuncio"* (Clase 11): concentra el presupuesto en uno y deja a los demás sin
entrega. En 1-1-5 eso significa que **3 de los 5 ángulos pueden no llegar a testearse nunca**.

**El argumento fuerte es otro, y sale de la data propia.** El sistema fragmenta el presupuesto
en 6 conjuntos para poder atribuir el ángulo — es decir, paga el costo de un diseño experimental.
Pero `CALENDARIO_ESCALADO.md` §1.5 ya midió que **ese experimento no produce señal**:

```
CONJUNTO-CUENTA .............. dispersión 1.12  ← azar de Poisson casi puro
CONJUNTO (todas las cuentas) . dispersión 1.89  ← señal débil
ÁNGULO (todas las cuentas) ... dispersión 2.99  ← la única señal real
```

**Conclusión dura: el sistema está pagando el precio de la atribución sin cobrar el beneficio.**
Si la decisión igual se toma agregando por `angulo_key` a lo largo del tiempo (regla 6 de
`CLAUDE.md` + APR-055), entonces la estructura de 6 conjuntos no aporta nada que el 1-1-5 no dé
más barato y más rápido.

**Y hay un segundo argumento, aritmético, con los números del propio sistema.** Meta necesita
~50 eventos de optimización **por conjunto** para salir de aprendizaje. A $0.478/conversación
(medido en el portafolio, jul-2026):

| Estructura | $/conjunto/día | conv/día por conjunto | Días para 50 conv | Objetos a mantener |
|---|---|---|---|---|
| **Actual** (6 conj × $2.99) | $2.99 | 6.3 | **8.0 días** | 6 conjuntos + 12 anuncios |
| **1-1-5** ($6.17 en un conjunto) | $6.17 | 12.9 | **3.9 días** | 1 conjunto + 5 anuncios |

El conjunto único sale de aprendizaje **2× más rápido** y con **un tercio del gasto diario**.
Con los $17.94/día actuales caben **tres campañas 1-1-5 en paralelo** — que es exactamente lo
que dice M2 ("no hago una sola, hago tres o cuatro") — y eso restituye la redundancia perdida
sin fragmentar el presupuesto dentro de la campaña.

> **Nota conceptual honesta:** esto es un cambio de filosofía, no un ajuste. Se pasa de un
> **experimento controlado** (6 celdas parejas) a un **bandido** (Meta selecciona). Se pierde
> la lectura de los perdedores. Se acepta porque la lectura de los perdedores hoy es ruido.

**GUARDARRAÍLES si se adopta:**
- **G1** — Los 5 anuncios del conjunto llevan `[ANGULO]` en el nombre según la CONVENCIÓN DE
  NOMBRES. Sin eso la atribución se pierde del todo (hoy el nombre de anuncio es `[ANGULO]_[FORMATO]_[A|B]`;
  el campo `anuncio` ya viaja en `_FACT_VENTAS.csv`, así que la infra existe).
- **G2** — El veredicto sigue siendo por `angulo_key` agregado en el tiempo y entre campañas.
  Un ángulo que no recibió entrega se marca **`SIN_ENTREGA`**, nunca `PERDEDOR`. Esa distinción
  no existe hoy y es obligatoria en 1-1-5.

**Presupuesto propuesto:** **$6.00/día** por conjunto 1-1-5 (dentro del rango del mentor
$3.95-$6.17 y por encima del piso $2.99 de la fórmula propia). 3 campañas = $18/día ≈ el gasto
actual de testeo.

---

### 3.2 · M9 — BANCO DE CONCEPTOS + GENERACIÓN EN LOTE → **ADOPTAR YA. ES EL #1.**

**Este es el cambio de mayor retorno de todo el paquete, y el sistema ya tiene el 80% construido
sin usarlo.**

Lo que ya existe en `Ads/_SWIPE/`: 597 creativos cosechados, `_CATALOGO_CONCEPTOS.md` v2
(8 conceptos validados sobre 133 creativos y 39 anunciantes), `_BANCO_CREATIVOS/`, `_BLUEPRINTS/`,
`_ELEMENTOS.csv` (matriz 36×30), `_GALERIA.html`, `_WINNERS.html`. Es más metodología de la que
tiene la clase.

**Lo que NO existe es la línea de producción.** Evidencia:

- **19 creativos distintos para 25 conjuntos.** El benchmark que el propio `ETAPA-6.md` cita
  (Andromeda) es **8-12 conceptos distintos por campaña**. El sistema corre 6 campañas: debería
  tener entre 48 y 72 conceptos vivos. Tiene 19.
- **Las 12 filas de `_DIM_CREATIVOS.csv` llevan 26 días en `PENDIENTE_GENERAR`.**
  > 🔴 **CORRECCIÓN 21-ago — el diagnóstico era peor de lo que parecía, y distinto.** Los 8 PNG de
  > TINNIDROP **sí se generaron** (26-jul, están en `Ads/MEDIA_TINNIDROP/`). Lo que no pasó es que
  > se publicaran: cruzando contra `_FACT_VENTAS.csv`, **solo `TINNIDROP_R1_VIVIRCONESO` llegó a
  > pautarse.** Los otros 7 llevan 26 días en disco sin subir a Meta. **El cuello de botella no es
  > la producción con IA: es la PUBLICACIÓN.** Eso cambia la prioridad — el paso de fábrica (§3.2.1)
  > sigue haciendo falta, pero antes hay que cerrar el loop de publicación y el estado en el CSV.
- Las carpetas `Ads/MEDIA_*` tienen entre 1 y 16 archivos por producto (TINNIDROP, el producto
  principal: 9).

**Y la data propia dice que esto es exactamente lo que está frenando el negocio.** APR-057:

> "PASAR EL TECHO DE GASTO NO COMPRA VENTAS, COMPRA CPA. […] Escalar por encima del techo solo
> funciona si ANTES entró un ángulo o una cuenta nueva que lo sostenga: meterle plata a la misma
> estructura solo sube el precio de la misma venta."

El techo demostrado es **Q597/día**. La ventana 14-16 ago corrió Q974/día y el CPA saltó de
Q47 a Q75. Ese techo **es el inventario de creativos**, no el mercado guatemalteco.

**Qué falta construir (concreto):**
1. **Paso de fábrica en `etapa-4` FASE 2** — dado (ángulo ganador + imagen del producto +
   N conceptos del swipe), emitir N prompts ya rellenados en un solo bloque. El método de la clase
   es literalmente esto: *"utilizá los 10 conceptos de la imagen del producto X y adaptalos al
   producto Y con el título Z"*. 10 conceptos en ~3 minutos.
2. **Cerrar el loop `_DIM_CREATIVOS.csv`** — un creativo `PENDIENTE_GENERAR` a más de 7 días es
   una alerta del dashboard, no una fila silenciosa.
3. **Meta de producción:** ≥10 conceptos nuevos por ángulo ganador y por semana. Sin esa meta,
   el techo Q597 no se mueve.

---

### 3.3 · M10 — "PRIMERO EL FLUJO" → **CORRECTO, Y EL SISTEMA ESTÁ REPROBANDO**

El mentor pone el umbral en **15-20 % de cierre**. Medición propia 17-20 ago:

| Producto | Mensajes | Ventas | Cierre |
|---|---|---|---|
| NUSAVA | 73 | 10 | **13.7 %** |
| TINNIDROP | 312 | 25 | **8.0 %** |
| CLEARSTEM | 102 | 5 | **4.9 %** |
| **Portafolio** | **487** | **40** | **8.2 %** |

**Cuánto vale cerrar esa brecha (mismo gasto, mismos mensajes):**

```
hoy:        487 msj × 8.2 %  = 40 ventas → CPA Q52.5
a 15 %:     487 msj × 15 %   = 73 ventas → CPA Q28.8   (+33 ventas, −45 % de CPA)
```

**Ningún cambio de estructura de campaña se acerca a ese retorno.** El mentor tiene razón y
el sistema tiene la prioridad invertida: hay 8 archivos de doctrina sobre estructura y escalado,
y ninguna etapa que **optimice el flujo contra data**. `etapa-5` construye el bot una vez;
`ESCALADO_PLAYBOOK.md` §3 lista "optimizar el flujo" como palanca #1 pero no dice cómo medirla
ni quién la ejecuta.

**Brecha concreta: falta una `etapa-9` (optimizador de flujo)** que lea cierre por
producto/ángulo/banda de edad y proponga cambios al bot. Y **falta el KPI de cierre en el
dashboard** — hoy se calcula a mano en cada auditoría.

---

### 3.4 · M8 — OBJETIVO VENTAS → **TEST SÍ, PERO EL CAMBIO REAL ES EL CAPI**

`ETAPA-6.md` tiene hoy una regla explícita: *"nunca Ventas en el testeo (Mercy: Interacción
nunca me funcionó)"*. La clase nueva la contradice, y por **regla de recencia** manda la nueva.

**La evidencia propia apoya el diagnóstico del mentor.** Lo que describe — *"tráfico te trae
1.000 personas y a Meta le parece bien, pero no compran"* — es literalmente el patrón que el
sistema tiene documentado en APR-002:

- `tinnidrop-1`: 78 % conversación → **0 ventas**
- `NUSAVA ANIMO`: 68 % conversación, la más alta del producto → **0 ventas**
- `CLEARSTEM Médicos Fallaron`: el chat más barato ($0.59/conv) y el peor cierre ($9.91/compra)
- APR-060: la banda 25+ genera **más conversaciones y cero ventas**

**Pero el cambio de dropdown solo no arregla eso.** Con destino WhatsApp y sin evento de compra
en Meta, "Ventas → maximizar conversaciones" optimiza por **el mismo evento** que
"Tráfico → maximizar conversaciones". La señal no cambia; cambia la subasta en la que entra.

**El bloqueador está identificado hace un mes y sigue abierto:** `omni_purchase` devuelve
"Not available" (nota de NusavaB12 en `_PORTAFOLIO.txt`). Meta **no ve ninguna venta del sistema**.
Mientras eso siga así, todo objetivo de conversión es ciego.

**Veredicto:** (a) correr UNA campaña 1-1-5 con `OUTCOME_SALES` contra una gemela con
`OUTCOME_TRAFFIC`, mismo ángulo/creativo/presupuesto — es barato y cierra la discusión con data
propia; (b) **abrir el frente CAPI LucidBot/LucidSales → Meta como proyecto aparte.** Sin eso,
(a) mide poco.

---

### 3.5 · M4/M5/M6/M7 — ESCALADO CBO E INTRADÍA → **PARCIAL. NO COPIAR LA CADENCIA.**

| Sub-punto | Veredicto | Por qué |
|---|---|---|
| **M4 · 1-1-7 CBO para escalar** | **ADOPTAR** | No contradice al sistema: `ETAPA-6.md` ya dice "CBO solo cuando hay ganador claro". Y el mismo creativo N veces en un conjunto es una forma más limpia de forzar entrega que duplicar conjuntos. |
| **M7 · duplicar al presupuesto INICIAL** | **ADOPTAR** | Detalle fino que el sistema no tiene escrito y evita el error de duplicar a $60 y quemar el aprendizaje. |
| **M6 · +20 % varias veces al día** | **NO como default · SÍ como test acotado** | Choca de frente con el gate 3 de `CALENDARIO_ESCALADO.md` ("Nunca más de +20 %/día"). Y la data propia dice que el problema no es la velocidad de subida: la ventana 14-16 ago subió el gasto +63 % y compró **0.3 ventas más por día** partiendo la ganancia al medio. |
| **M5 · Q940/día por campaña** | **NO HOY** | El techo demostrado del portafolio entero es **Q597/día**. Ir a Q940 ya se probó y salió mal (APR-057). Se re-evalúa cuando el inventario de creativos suba de 19 a ~60. |
| **M12 · "no apagar nada en escalado"** | **PARCIAL** | Correcto a nivel *conjunto* (APR-055: el cero de una réplica es ruido de Poisson). Falso a nivel *cuenta/banda*: GTR0 gastó Q490 para 2 ventas (CPA Q244.8) mientras el mismo ángulo y creativo pagaba Q39.2 en GTR7. |

> **La razón de fondo para no copiar la cadencia:** el mentor escala rápido **porque tiene el
> banco de conceptos alimentando la campaña**. Copiar su velocidad de escalado sin su línea de
> producción de creativos es reproducir el 14-16 de agosto. **El orden importa: primero 3.2, después 3.5.**

---

### 3.6 · M11 — DEL VIDEO GANADOR SALEN 4 IMÁGENES → **ADOPTAR, YA CASI EXISTE**

`etapa-0` ya clasifica transcripciones por ángulo. Lo que falta es el paso inverso:
tomar el **video ganador** (no el pool inicial) y extraer los 3-4 ángulos que menciona su audio
para convertirlos en ads-imagen. Es una extensión pequeña de `etapa-0` + `etapa-4`, y ataca
directo el confound de formato que `PLANTILLAS_ADS.md` ya documenta.

---

### 3.7 · M13 — MULTICUENTA / MULTIFANPAGE → **SIN CAMBIO**

Ya está en `ESCALADO_PLAYBOOK.md` §3.6-3.7, con más matiz que la clase (la advertencia
"páginas vs cuentas: la página NO segmenta"). No tocar.

---

## 4. LO QUE LA CLASE NO DICE Y VALE MÁS QUE TODO LO ANTERIOR

**APR-060 (21-ago) — LA BANDA DE EDAD.** Ventana 17-20, portafolio completo:

| Banda | Pauta Q | Mensajes | Ventas | Cierre | CPA |
|---|---|---|---|---|---|
| **25+** (amplia) | 983 | 228 | 7 | **3.1 %** | **Q140.5** |
| **45-60** | 886 | 220 | 28 | **12.7 %** | **Q31.7** |
| 25-35 | 230 | 39 | 5 | 12.8 % | Q46.1 |

Experimento natural (mismo ángulo, producto y creativo): `PERDIDA_AUDITIVA` en GTR0 a 25+ pagó
**Q473.6/venta**; en GTR7 a 45-60, **Q30.6**. Quince veces.

**Aritmética de la oportunidad:** si los Q983 que corrieron a 25+ hubieran corrido al CPA de la
banda 45-60, serían **31 ventas en vez de 7**. **+24 ventas en 4 días**, sin un peso extra de pauta.

Esto **contradice la segmentación amplia 18-65+ que `CLAUDE.md` declara como constante del sistema**
(justificada por Andrómeda: "el creativo segmenta"). La constante está equivocada para productos
con avatar de edad marcada, y la corrección no está aplicada.

> **Si solo se implementa UNA cosa de todo este documento, es esta — no el 1-1-5.**

---

## 5. PLAN PROPUESTO — ORDEN DE EJECUCIÓN (por retorno, no por facilidad)

| # | Cambio | Archivos que toca | Riesgo | Retorno estimado |
|---|---|---|---|---|
| **1** | **Banda de edad por avatar** (matar 25+ donde el avatar es 45+) | `CLAUDE.md` (constante de segmentación) · `ETAPA-6.md` · `ETAPA-FANPAGE.md` (ya tiene edad por página) | **BAJO** | **+24 ventas / 4 días** medido |
| **2** | **Fábrica de conceptos** (swipe → 10 prompts en lote) + alerta de `PENDIENTE_GENERAR` | `ETAPA-4.md` · `_CATALOGO_CONCEPTOS.md` · `gen_dashboard.py` | BAJO | rompe el techo Q597/día |
| **3** | **Optimizador de flujo** (`etapa-9`) + KPI de cierre en dashboard | agente nuevo · `ETAPA-5.md` · `DATA_PLAYBOOK.md` | MEDIO | 8.2 % → 15 % = −45 % CPA |
| **4** | **Migrar FASE 1 a 1-1-5** ×3 campañas paralelas, $6/día c/u | `CLAUDE.md` (reglas 6, 9) · `ETAPA-6.md` · `CALENDARIO_ESCALADO.md` §1.5 · `MCP_PLAYBOOK.md` | **ALTO** (reescribe el testeo) | −67 % objetos que mantener; aprendizaje 2× más rápido |
| **5** | **1-1-7 CBO + duplicar al presupuesto inicial** en escalado | `ETAPA-6.md` FASE 2 · `ESCALADO_PLAYBOOK.md` §3 | MEDIO | simplifica el escalado |
| **6** | **Test A/B `OUTCOME_SALES`** (1 campaña gemela) | `ETAPA-6.md` · `_EVENTOS.csv` | BAJO | cierra la discusión con data propia |
| **7** | **CAPI LucidSales → Meta** | proyecto aparte | ALTO | desbloquea todo objetivo de conversión |
| **8** | **Video ganador → 4 ads-imagen** | `ETAPA-0.md` · `ETAPA-4.md` | BAJO | ataca el confound de formato |
| — | ~~Escalado intradía +20 % ×3~~ | — | — | **CONGELADO** hasta que #2 esté corriendo |

---

## 6. LO QUE HAY QUE PROTEGER AL MIGRAR (no perder en el rediseño)

El sistema tiene doctrina propia que **no está en las clases** y que se ganó con plata. Si se
migra a 1-1-5 sin cuidarla, se pierde:

1. **Agregar por `angulo_key`, nunca por conjunto** (regla 6 · APR-055). En 1-1-5 pasa a ser
   agregar por **anuncio → ángulo**. La regla sobrevive; el nivel cambia.
2. **La conversación corta, no corona** (APR-002). Sigue vigente y es más importante en 1-1-5,
   donde el conjunto único no da lectura por ángulo hasta que hay ventas.
3. **Presupuesto de Decisión = 1 × Break-Even antes de matar por ventas.** En 1-1-5 el PD pasa a
   ser **por anuncio**, y con 5 anuncios repartiéndose $6/día cada uno tarda MÁS en alcanzarlo
   que un conjunto a $2.99. ⚠️ **Recalcular §1.5 antes de migrar** — es el punto donde el 1-1-5
   puede salir peor que lo actual si se lee mal.
4. **Cobertura de tracking antes de comparar CPA entre cuentas** (APR-056).
5. **Revisar el método de pago antes de culpar al creativo** cuando una cuenta se desploma (APR-058).
6. **CPA semanal/ponderado, nunca diario.**

---

## 7. LA CRÍTICA DE FONDO AL SISTEMA (lo que el operador pidió)

**El sistema está sobre-diseñado del lado del análisis y sub-ejecutado del lado de la producción.**

- **14 subagentes, 8 archivos de doctrina, 64 aprendizajes registrados, 15 CSV** — contra
  **19 creativos distintos vivos** y **12 creativos pendientes de generar hace 26 días**.
- La razón por la que el operador **postergaba crear campañas** no es que el sistema esté mal
  pensado: es que produce **12 objetos de Meta por producto** (6 conjuntos × 2 anuncios) para
  medir una señal que ya se demostró indistinguible del azar. **El 1-1-5 no es una simplificación
  cosmética: elimina trabajo manual que no compraba información.**
- Los aprendizajes de agosto (APR-055 a APR-064) son **casi todos correcciones de la propia
  instrumentación** — el motor mataba por conjunto, el CPA no dividía por cobertura, el `ad_id`
  se rompía en Excel, el MCP veía 48 % del gasto. Eso es señal de un sistema que **gasta más ciclos
  en medirse a sí mismo que en producir creativos**. La clase, con muchísima menos infraestructura,
  produce 10 conceptos en 3 minutos.
- **El desbalance es la conclusión.** No hace falta tirar la capa de data — es buena y ya evitó
  decisiones caras. Hace falta que la mitad del esfuerzo se mude a la línea de producción:
  **conceptos, flujo y banda de edad.**

---

## 8. DECISIONES QUE NECESITAN LA FIRMA DE JUAN

- [ ] ¿Se migra FASE 1 a 1-1-5? (cambia `CLAUDE.md`, `ETAPA-6`, `CALENDARIO_ESCALADO` §1.5)
- [ ] ¿Se corrige la constante de segmentación amplia 18-65+ por banda según avatar?
- [ ] ¿Se abre `etapa-9` (optimizador de flujo) o se extiende `etapa-8`?
- [ ] ¿Se congela el escalado intradía hasta tener el banco de conceptos corriendo?
- [ ] ¿Se abre el frente CAPI como proyecto aparte?

> Cuando algo de acá se implemente, este archivo se mueve a `_ARCHIVO/roadmap_cumplido/` el mismo día.

---

# 9. ARQUITECTURA DE 3 FASES — cerrada con el operador el 21-ago

> Esta sección **reemplaza** la recomendación de §3.1 (migrar FASE 1 a 1-1-5) y responde a la
> lectura que el operador hizo de la pizarra. Su lectura es **correcta** y está confirmada
> textualmente por la transcripción.

## 9.1 · Qué dice la pizarra (verificado contra la transcripción)

```
Testeos  →  1.1.5 - 25K        1 campaña · 1 conjunto · 5 anuncios (conceptos 1-5)
            1.1.5 - 25K        1 campaña · 1 conjunto · 5 anuncios (conceptos 6-10)
            1.2.5 - 50K        1 campaña · 2 conjuntos × 5 anuncios = LOS MISMOS 10
                               ($25K por conjunto, ABO)
```
> *"10 anuncios en total, cinco lo hago en una campaña de 1-1-5 y cinco en otra, y hago una que
> es como la combinación de las dos: 2 conjuntos, meto cinco en un conjunto y los otros cinco en
> otro, y por conjunto son 25 que en total son 50,000."* — transcripción, Q&A con Carlos.

Total: **100.000 COP/día = $24.7**. La cuarta estructura de la pizarra, `(1.7×2.7×2)×4` a
7.000 COP/conjunto (40+ conjuntos), es testeo masivo a la escala de Calet — **fuera de alcance hoy**.

## 9.2 · La corrección: en qué fase va el 1-1-5

**Regla que sale del análisis:**

```
presupuesto PROTEGIDO (conjuntos separados)  ⟸  la variable se decide por VENTA
presupuesto LIBRE     (1-1-N, Meta reparte)  ⟸  la variable se decide por ENTREGA
```

- **Testeo de ÁNGULOS** → se decide por VENTA. Meta solo ve clics y conversaciones, y APR-002
  demuestra que **esa señal no predice la venta** (`tinnidrop-1` 78 % conv → 0 ventas · `ANIMO`
  la más alta → 0 ventas · `ME DIJERON` 23 % → de los que más vende). En 1-1-N, Meta coronaría
  por la métrica equivocada y mataría de hambre al ángulo que vende. **→ conjuntos separados.**
- **Testeo de CONCEPTOS** → el ángulo ya está validado; lo que se busca es qué creativo entrega
  más barato. El criterio de Meta (CTR/CPM/conversación) **sí está alineado** con ese objetivo.
  **→ 1-1-5.** Es lo que dice la clase: *"en prueba de creativo te pueden salir dos o tres
  anuncios ganadores"*.

## 9.3 · El aporte real de la campaña `1-2-5`: REPLICACIÓN

Los mismos 10 creativos corren **dos veces** en estructuras independientes → **dos sorteos del
mismo pool**. Es la respuesta directa al problema de dispersión 1.12 documentado en
`CALENDARIO_ESCALADO.md` §1.5, y el sistema **no tenía ningún mecanismo equivalente**.

**Regla de lectura (nueva, obligatoria si se adopta):**

| Resultado | Veredicto |
|---|---|
| El concepto queda arriba en **2 de sus 2** apariciones | **GANADOR** — se corona |
| Queda arriba en **1 de 2** | **RUIDO** — no se corona, se repite el test |
| No recibió entrega en ninguna | **`SIN_ENTREGA`** — nunca `PERDEDOR` |

> El "ganador de TINNIDROP que se corrió tres veces" (Accesibilidad → Pérdida auditiva →
> ME DIJERON) no habría pasado este filtro. Ese es el valor del mecanismo.

⚠️ **COSTO A CONTROLAR — auto-competencia de subasta.** A, B y C con los mismos creativos, la
misma página y la misma audiencia amplia compiten entre sí: sube el CPM de las tres.
**Mitigación: la campaña C corre en OTRA cuenta.** Convierte el confound en la validación
multicuenta de `ESCALADO_PLAYBOOK.md` §3.6 ("cada cuenta segmenta distinto").

## 9.4 · Lo que NO se adopta de la propuesta

**"5 ángulos × 2 conceptos cada uno"** — ❌ mueve las dos variables a la vez; nada es atribuible.
Es exactamente lo que `CLAUDE.md` prohíbe: *"si la ejecución visual varía junto con el ángulo,
nada es atribuible"*.

**Versión legítima de esa idea** (solo si la FASE 1 deja 2 ángulos ganadores):

```
Campaña A: 1-1-5 → ángulo ganador #1 × 5 conceptos
Campaña B: 1-1-5 → ángulo ganador #2 × 5 conceptos
Campaña C: 1-2-5 → conj.1 = ángulo #1 (5 conceptos) · conj.2 = ángulo #2 (5 conceptos)
```
Cada **conjunto** conserva un solo ángulo → se mantiene la congruencia con el bot dedicado
(REGLA DEL MULTI-GANADOR, `CALENDARIO_ESCALADO.md` §1). Alternativa preferida del sistema:
escalonar los ganadores cada ~3 días en vez de correrlos juntos.

**"10 conceptos distintos"** — ⚠️ no son 10 `concepto_key`. El catálogo tiene **8** y advierte que
con 10 valores nunca se acumulan observaciones. Son **10 EJECUCIONES etiquetadas con los 6
conceptos de la rotación** (PARTE III §3): p.ej. C2 en sus variantes `ligera`/`densa`/
`colage-sintomas` = 3 ejecuciones, 1 `concepto_key`. Así se mide el creativo sin romper el
aprendizaje acumulado.

## 9.5 · La arquitectura resultante

| Fase | Qué mide | Estructura | Presupuesto | Decide por |
|---|---|---|---|---|
| **1 · ÁNGULOS** | el ángulo | 5-6 conjuntos × 1 anuncio · **ABO** · concepto FIJO `C2_BENEFICIOS` variante **ligera** | ~$4/conjunto | VENTA, agregada por `angulo_key` |
| **2 · CONCEPTOS** | el creativo | **1-1-5 + 1-1-5 + 1-2-5** · ABO · ángulo FIJO (el ganador) | $6 + $6 + $12 = **$24/día** | **replicación**: gana en 2 de 2 |
| **3 · ESCALADO** | volumen | **1-1-7** → `1-7-7` · **CBO** · ganador ×7 (Post ID) | $15-18/día · +20 % con gate de CPA | CPA semanal sobre ENTREGADOS |

**Matiz sobre CBO:** el `1-1-7` con un solo conjunto es funcionalmente idéntico a ABO — todo el
presupuesto va a ese conjunto igual. El CBO recién significa algo con más de un conjunto, o sea
en el `1-7-7`. No hay decisión que tomar en el `1-1-7`.

**Dimensionamiento:** la FASE 2 son **$24/día ≈ Q183/día por producto**. Contra el techo
demostrado del portafolio (**Q597/día**, APR-057) → **cabe UN solo producto en fase de conceptos
a la vez** mientras haya otros escalando. No correrla en dos productos la misma semana.

## 9.6 · Lo que esto NO reemplaza

La **banda de edad** (§4) sigue siendo la palanca #1: CPA Q140.5 contra Q31.7 es más plata que
toda esta reestructuración junta, y es un cambio de un campo en Meta. La arquitectura de 3 fases
y la corrección de segmentación son **independientes** — se implementan en paralelo.

## 9.7 · Lo que hay que escribir si se adopta

- `CLAUDE.md` — la secuencia de fases pasa de 2 a **3** (ángulos / conceptos / escalado). Hoy
  "FASE 2" nombra el testeo de microángulos; con esto pasa a ser el testeo de conceptos.
- `.claude/agents/ETAPA-6.md` — tres modos de output en vez de dos.
- `CALENDARIO_ESCALADO.md` §1.5 — gates y Presupuesto de Decisión **por anuncio** en la fase de
  conceptos (5 anuncios repartiéndose $6/día alcanzan el PD más lento que un conjunto a $2.99:
  **recalcular antes de migrar**).
- `Ads/_SWIPE/_CATALOGO_CONCEPTOS.md` PARTE III — agregar la estructura de campaña (hoy define
  qué se fija en cada fase, pero no cómo se pauta).
- `DATA_PLAYBOOK.md` — el campo `replicacion` (A/B/C) en `_DIM_CONJUNTOS.csv` y la regla
  "gana en 2 de 2".
