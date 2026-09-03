> ✅ **EJECUTADO 2026-09-02.** `.claude/agents/ETAPA-11.md` creado y cableado (CLAUDE.md, AGENTS.md,
> README, ESCALADO_PLAYBOOK §3, CALENDARIO_ESCALADO §1, DATA_PLAYBOOK §1 y §3, MATRIZ C-10/M-F01/M-F02,
> ETAPA-5 y ETAPA-7).
>
> **Corrección importante al §2.3 de este handoff:** la verificación se corrió y **la hipótesis del
> paraguas quedó SIN TESTEAR, no confirmada ni refutada** — no hay evidencia de que un flujo dedicado
> se haya cargado alguna vez (`_EVENTOS.csv` no tiene `CAMBIO_BOT` para esos productos). Lo que sí
> quedó firme: el ÁNGULO explica 7× más varianza de cierre que el régimen del bot, y esa dispersión
> no es Poisson (p<0.001). Informe: `PRODUCTOS/_AUDITORIAS/_VERIFICACION_BRECHA_CIERRE_20260902.txt`.
>
> **D1-D5 cerradas:** D1 brief (etapa-11) + redacción (etapa-5) · D2 chats semanales · D3 dispara al
> confirmar ángulo ganador, no por caída de cierre · D4 conviven, ruteo por Post ID a productos
> distintos del catálogo LucidBot · D5 A/B real en paralelo.

---

# HANDOFF — CONSTRUIR `etapa-11`: OPTIMIZADOR DE FLUJO

> **Para:** una sesión nueva de Claude Code con acceso a este mismo repositorio.
> **Fecha:** 2026-09-02 · **Escrito por:** la sesión que implementó la arquitectura de 3 fases.
> **Cómo usarlo:** pegá este archivo completo como primer mensaje del chat nuevo.

---

## 0. QUÉ ES ESTE SISTEMA (30 segundos)

`SISTEMA VITALCOM GUATEMALA` — dropshipping COD (contra entrega) en Guatemala, con venta
automatizada por WhatsApp vía **LucidBot**. Meta Ads trae el tráfico al chat; el bot cierra la venta.

- **Entrada obligatoria: `CLAUDE.md`** (el orquestador). Es el mapa de todo.
- 16 subagentes en `.claude/agents/ETAPA-*.md`, invocables con Task.
- Capa de data en `PRODUCTOS/*.csv` — reglas de lectura en `DATA_PLAYBOOK.md`.
- Doctrina de los mentores indexada en **`_CONOCIMIENTO/MATRIZ_METODOLOGIA.md`**.
- **Regla de oro del repo: un dato, un dueño.** Si un número vive en un CSV, no se repite en prosa.
  Si una regla vive en su archivo dueño, en los demás va solo el puntero.

---

## 1. QUÉ ACABA DE CAMBIAR (02-sep-2026) — para no rehacerlo

Se implementó la **arquitectura de 3 fases**, a partir de dos clases nuevas (16 y 22 de agosto):

| Fase | Mide | Estructura | Variable que se mueve |
|---|---|---|---|
| 1 · ÁNGULOS | el ángulo | 6 conjuntos ABO, $2.99→$5.98 | el `angulo_key` (concepto fijo) |
| 2 · CONCEPTOS | el creativo | `1-1-5 + 1-1-5 + 1-2-5`, $24/día | la ejecución visual (ángulo **y copy** fijos) |
| 3 · ESCALADO | volumen | `1-1-7`, $15-18/día | ninguna: compra tráfico |

También se crearon **`etapa-9`** (fábrica de conceptos, ≥6 creativos/día) y **`etapa-10`** (lector
concepto ↔ métrica: por qué ganó lo que ganó), y se corrigió la constante de segmentación a
**banda de edad derivada del avatar** (APR-060).

**Nada de esto hay que tocarlo.** El trabajo nuevo es otro y está abajo.

---

## 2. LA BRECHA — enunciada con precisión

### 2.1 · El síntoma

Los mentores operan con **15-20 % de tasa de cierre** (mensajes → ventas) y afirman que con ese
cierre *"cualquier estructura de campaña vende; con mal cierre, ninguna"*. Es la afirmación **M-F01**
de la matriz, y es la más reciente de las dos clases nuevas.

**Medición propia, ventana 17-20 ago (portafolio completo):**

| Producto | Mensajes | Ventas | Cierre |
|---|---|---|---|
| NUSAVA | 73 | 10 | **13.7 %** |
| TINNIDROP | 312 | 25 | **8.0 %** |
| CLEARSTEM | 102 | 5 | **4.9 %** |
| **Portafolio** | **487** | **40** | **8.2 %** |

**La aritmética de la oportunidad** (mismo gasto, mismos mensajes):

```
hoy:      487 msj × 8.2 %  = 40 ventas  ->  CPA Q52.5
a 15 %:   487 msj × 15 %   = 73 ventas  ->  CPA Q28.8     (+33 ventas · −45 % de CPA)
```

**Ningún cambio de estructura de campaña se acerca a ese retorno.** Es la palanca más grande que
le queda al sistema.

### 2.2 · El diagnóstico del operador (2026-09-02) — es la clave de todo

> *"Ellos tienen esas métricas porque en la FASE 1 nosotros testeamos con un flujo general,
> independiente de los ángulos. Cuando empezamos a descubrir ángulos, debe haber un siguiente
> paso que —ya que descubrimos el anuncio ganador y el ángulo que atrae gente que compra— tome
> el flujo actual, lo analice y lo optimice de acuerdo a ese ángulo, de acuerdo a los anuncios
> que están vendiendo."*

**Esto es correcto y explica una parte del gap que el sistema nunca había escrito.** En FASE 1 el
bot es un **"Bot Paraguas"**: un solo flujo que recibe tráfico de 6 ángulos distintos usando una
"Promesa Integradora". Es un instrumento de medición deliberado — permite testear 6 ángulos sin
construir 6 bots. **Su costo es la congruencia**, y la congruencia es exactamente lo que sostiene
el cierre:

- Clase 22: *"si el flujo dice algo distinto a lo pauteado, el cliente se sale"* → **efecto rebote**.
- Clase 22: *"cuando la persona se sale, Meta la manda a tu competencia"*.
- El sistema ya lo tiene escrito como principio en `CALENDARIO_ESCALADO.md` §1:
  **"paraguas para descubrir, dedicado para escalar"**.

**Entonces el gap real no es doctrinal, es de ejecución: el principio está escrito y no hay ninguna
etapa que lo ejecute contra data.** El paso "optimizar el flujo hacia el ángulo ganador" figura
como **palanca #1** en `ESCALADO_PLAYBOOK.md` §3 — y no dice cómo medirla, ni quién la ejecuta,
ni con qué la compara.

### 2.3 · La advertencia honesta — no todo el gap es el paraguas

⚠️ **Esto hay que verificarlo antes de diseñar, porque cambia el alcance del agente.**

TINNIDROP marcó **8.0 % con 312 mensajes** en esa ventana, y TINNIDROP **ya estaba en escalado con
un ángulo ganador identificado** — no en testeo con paraguas. Si un producto ya dedicado sigue en
8 %, entonces el paraguas explica **una parte** del gap, no todo: hay además un problema de
**calidad del flujo** independiente de la congruencia ángulo↔bot.

**Primera tarea de la sesión nueva: separar los dos efectos con la data real.**

```
cierre de productos en FASE 1 (bot paraguas)      vs
cierre de productos ya dedicados (post-ganador)
```

Si la brecha entre esos dos números es chica, el problema principal **no** es la congruencia y el
agente tiene que atacar otra cosa (propuestas de valor, fricción, precio, velocidad de respuesta).
Si es grande, el diagnóstico del operador queda confirmado y la congruencia es la palanca.

---

## 3. QUÉ YA EXISTE — no duplicar

| Ya existe | Dónde | Qué hace y qué NO hace |
|---|---|---|
| **`etapa-5`** | `.claude/agents/ETAPA-5.md` | **CONSTRUYE** el flujo LucidBot (13 elementos + 5 interacciones + reglas + audio + FAQ). En FASE 1 arma el paraguas; en FASE 2/3 arma el dedicado del ángulo ganador. **Lo construye desde doctrina, a ciegas: nunca lee un solo número de rendimiento.** |
| Principio "paraguas para descubrir, dedicado para escalar" | `CALENDARIO_ESCALADO.md` §1 | Doctrina, sin ejecutor |
| "Optimizar el flujo hacia el ángulo ganador" como palanca #1 | `ESCALADO_PLAYBOOK.md` §3 | Enumerada, sin método ni métrica |
| Cómo se optimiza un flujo (checklist de la Clase 22) | `ESCALADO_PLAYBOOK.md` §3 palanca 1 | Congruencia con el anuncio · reducir fricción (garantía, CTA con beneficio, prueba social con imágenes) · 6-8 propuestas de valor · umbral cognitivo · momentos antes→después · responder en 2-3 seg |
| Hechos operativos de LucidBot | `.claude/agents/ETAPA-5.md` (agregados 02-sep) | La info del producto va en su campo y **NO** en las reglas · el bot queda **DESACTIVADO** al importar de Superbodega · **lo que más mueve el cierre son las PROPUESTAS DE VALOR**, no los hooks ni los testimonios (M-F06, clase 22-ago) |
| Umbrales de métricas | `ESCALADO_PLAYBOOK.md` §8 | Fuente única. `%conv/clic-enlace` 35-70 %, CPA vs Break-Even, etc. |
| Índice de la doctrina de mentores | `_CONOCIMIENTO/MATRIZ_METODOLOGIA.md` | Ver **M-F01 a M-F12** (dominio FLUJO) y el **choque C-10**, que es literalmente esta brecha |

**`etapa-11` no reemplaza a `etapa-5`.** `etapa-5` construye; `etapa-11` diagnostica un flujo que ya
corrió y propone los cambios. Hay que decidir explícitamente si `etapa-11` **entrega el flujo
reescrito** o **entrega el brief y `etapa-5` lo reescribe** (ver §6, decisión D1).

---

## 4. CON QUÉ DATA SE CUENTA (y con cuál no)

### Disponible hoy

| Fuente | Qué aporta |
|---|---|
| **`PRODUCTOS/_FACT_VENTAS.csv`** | 🔑 **la espina dorsal.** Tiene `mensajes` **y** `ventas` **por ANUNCIO** (columnas: `ventana_ini, ventana_fin, dias, rol_ventana, producto_key, producto, cuenta_id, cuenta_alias, campana, conjunto, anuncio, mensajes, clicks, impresiones, spend_usd, ventas, total_q, moneda_origen, fuente, ad_id`). Permite calcular **cierre por anuncio, por conjunto, por ángulo y por producto**. |
| `PRODUCTOS/_DIM_CONJUNTOS.csv` | el `angulo_key`, `avatar`, `dolor_nucleo`, `emocion_dominante`, `nivel_conciencia`, `rol_embudo` de cada conjunto |
| `PRODUCTOS/_DIM_CREATIVOS.csv` | atributos del creativo + `canonico_id` (puente al blueprint JSON) |
| `PRODUCTOS/[PRODUCTO]/1_HACER_MANUAL.txt` | **el texto real del flujo cargado en LucidBot**, campo por campo |
| `PRODUCTOS/[PRODUCTO]/2_DATA_PRODUCTO.txt` | precios, ángulos, break-even, avatar |
| `PRODUCTOS/_APRENDIZAJES.csv` | los `APR-xxx` acumulados |
| `PRODUCTOS/_TASA_ENTREGA.csv` · `CONTABILIDAD.md` | ⚠️ **el cierre no es lo mismo que la venta cobrada.** Ver §5. |

### ❌ NO disponible — es el input que hay que resolver

**No hay ni una sola transcripción de chat en el repositorio.** Sin eso, el agente puede decir
**dónde** pierde el flujo (qué ángulo, qué producto, qué anuncio cierra peor) pero no **por qué**
(en qué mensaje se cae la gente, qué objeción no se resuelve, qué pregunta repiten).

**Decisión de diseño obligatoria (D2 en §6):** o el operador entrega exports de conversaciones de
LucidBot con alguna cadencia, o `etapa-11` se limita al diagnóstico cuantitativo + auditoría del
texto del flujo contra el copy del anuncio. **Ambas versiones sirven, pero son agentes distintos.**
No arrancar a escribir el agente sin cerrar esto.

---

## 5. TRAMPAS DEL DOMINIO — leer antes de escribir una línea

1. **La conversación CORTA, no CORONA** (APR-002). Evidencia propia: `tinnidrop-1` 78 % de
   conversación → **0 ventas**; `ANIMO` la más alta del producto → 0 ventas; `ME DIJERON` 23 % →
   de los que más vende. **Un flujo no se juzga por cuánta gente conversa.**
2. **Ruido de Poisson.** Las ventas por conjunto tienen índice de dispersión **1.12** = azar casi
   puro. Con 1-3 ventas el IC es ±113-196 %. **Se agrega por `angulo_key`, nunca por
   conjunto-semana.** Un "el ángulo X cierra peor" con 3 ventas es una superstición.
3. **CPA y cierre son SEMANALES, nunca diarios.**
4. **Cohorte ≠ caja.** El negocio es COD: la venta y el cobro no ocurren el mismo día, y un cohorte
   de menos de 10 días es PRELIMINAR y se ve optimista. `CONTABILIDAD.md` es el dueño. Si el agente
   va a hablar de plata, tiene que leerlo primero.
5. **Cierre sobre mensajes ≠ cierre sobre entregados.** Una venta COD que se devuelve no es venta.
   El cierre del bot y la tasa de entrega son dos cosas distintas y **no hay que mezclarlas**.
6. **COMPLIANCE — la regla que más se malinterpreta.** El compliance de verbos/claims aplica **SOLO
   a los ADS** (lo que Meta lee). **Todo lo post-clic —el flujo del bot, el audio, las infografías,
   los testimonios— NO se suaviza:** ahí la prioridad es CONVERSIÓN y se permiten verbos
   persuasivos fuertes y las estadísticas del operador. **Un optimizador de flujo que "limpie" el
   bot por compliance estaría destruyendo conversión por una regla que no aplica.** Está en
   `CLAUDE.md` → PRINCIPIO DE ALCANCE DEL COMPLIANCE.
7. **Voseo guatemalteco** en todo texto que vea el cliente.
8. **Los CSV se editan con un escritor CSV real**, nunca a mano (campos con comas entrecomillados).

---

## 6. QUÉ HAY QUE CONSTRUIR

**`.claude/agents/ETAPA-11.md`** — nombre `etapa-11`, el **OPTIMIZADOR DE FLUJO**.

### Disparador
Cuando `etapa-7` confirma un **ángulo ganador por VENTA** — es decir, **entre la FASE 1 y la
FASE 2**. Y después, de forma recurrente, cada vez que el cierre de un producto vivo caiga bajo su
umbral.

### Lo que debería hacer (esqueleto a validar, no a copiar)

1. **Medir el cierre** por producto / ángulo / anuncio desde `_FACT_VENTAS.csv`, con el piso de
   evidencia de Poisson y agregando por `angulo_key`.
2. **Separar el efecto paraguas del efecto calidad** (la verificación de §2.3).
3. **Auditar la congruencia** entre lo que promete el anuncio ganador (copy + creativo) y lo que
   dice el flujo actual (`1_HACER_MANUAL.txt`): promesa, precio, condiciones de entrega, dolor de
   entrada, nivel de conciencia.
4. **Diagnosticar dónde se pierde** — con chats si los hay; si no, por descarte cuantitativo.
5. **Proponer los cambios priorizados**, empezando por las **propuestas de valor** (M-F06: es lo que
   más mueve el cierre según la clase más reciente), luego fricción, luego oferta.
6. **Entregar el flujo optimizado** (o el brief para `etapa-5` — ver D1).
7. **Registrar el cambio** en `_EVENTOS.csv` para poder medir el antes/después. **Sin esto, el
   agente no se puede evaluar a sí mismo y el sistema no aprende si sus cambios sirvieron.**

### Decisiones de diseño abiertas — cerrarlas con el operador ANTES de escribir

- **D1** · ¿`etapa-11` **reescribe** el flujo, o entrega el **brief** y `etapa-5` lo reescribe?
  (un dato, un dueño: hoy `etapa-5` es el dueño del texto del flujo)
- **D2** · ¿Habrá **exports de chats**? ¿Con qué cadencia y en qué formato? Define si el agente es
  cualitativo o solo cuantitativo.
- **D3** · ¿Cuál es el **umbral de disparo**? ¿Cierre bajo 12 %? ¿Bajo el del propio producto la
  semana anterior? ¿Cuántas ventas mínimas antes de tocar nada?
- **D4** · ¿El flujo dedicado **reemplaza** al paraguas o **convive** con él mientras la FASE 1 de
  otro producto sigue corriendo? (LucidBot: ¿un bot por producto, por ángulo, o por página?)
- **D5** · ¿Se mide el antes/después con un **A/B real** (dos flujos en paralelo) o con
  **pre/post** en el tiempo? El A/B es más limpio; el pre/post confunde el cambio con la semana.

### Archivos que probablemente haya que tocar

- **crear** `.claude/agents/ETAPA-11.md`
- `CLAUDE.md` — mapa de subagentes (pasa a 17), mapa de dueños, ciclo de optimización, y la
  secuencia entre FASE 1 y FASE 2
- `AGENTS.md` — **es un espejo exacto de `CLAUDE.md`** con dos sustituciones (`.claude/` → `.Codex/`
  y `Claude Code` → `Codex`). Se regenera, no se edita a mano.
- `ESCALADO_PLAYBOOK.md` §3 palanca 1 — apuntar al nuevo dueño
- `CALENDARIO_ESCALADO.md` §1 — el paso "dedicar el bot" pasa a tener ejecutor
- `DATA_PLAYBOOK.md` — si se agrega un KPI de cierre al dashboard
- `_CONOCIMIENTO/MATRIZ_METODOLOGIA.md` — **actualizar M-F01 y el choque C-10** al implementarse
  (hoy dicen "brecha abierta con dueño vacante")
- `README.md` — conteo de subagentes y ciclo

---

## 7. LO PRIMERO QUE DEBERÍA HACER LA SESIÓN NUEVA

**No escribir el agente todavía.** En orden:

1. Leer `CLAUDE.md`, `.claude/agents/ETAPA-5.md`, `ESCALADO_PLAYBOOK.md` §3 y §8, y
   `_CONOCIMIENTO/MATRIZ_METODOLOGIA.md` (dominio F + choque C-10).
2. **Correr la verificación de §2.3 contra `_FACT_VENTAS.csv`**: cierre de productos con paraguas
   vs cierre de productos ya dedicados, agregado por `angulo_key`, con su `n`. **Ese número decide
   qué agente hay que construir.**
3. Cerrar D1-D5 con el operador.
4. Recién ahí escribir `ETAPA-11.md` y cablearlo.

> Un optimizador de flujo construido sobre el diagnóstico equivocado va a reescribir bots que ya
> estaban bien y a dejar intacto lo que de verdad pierde la venta. **El paso 2 es barato y cambia
> todo el diseño: no saltárselo.**
