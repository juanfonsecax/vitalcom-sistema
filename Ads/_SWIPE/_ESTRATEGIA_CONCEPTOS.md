# AUDITORÍA DE SISTEMA — LA CAPA DE CONCEPTOS
Fecha: 2026-08-18 · Alcance: cómo el sistema testea creativos (ángulo vs concepto), qué mide y qué no · Rol: auditor externo

---

## VEREDICTO EN UNA LÍNEA

El sistema tiene **excelentemente construida la capa de ÁNGULO** (avatar, dolor, deseo, miedo, nivel de conciencia, emoción — todo catalogado y trackeado). Lo que NO tiene es la **capa de CONCEPTO**: existe como doctrina en dos líneas sueltas, pero **no tiene catálogo, no tiene vocabulario cerrado y no se guarda en ningún CSV**. Consecuencia directa: hoy es **imposible responder con data propia "qué tipo de imagen vende"** — exactamente la pregunta que querés contestar. Y hay un problema más grave de diseño experimental: en FASE 1 se varían ángulo, concepto y formato **al mismo tiempo**, así que ningún resultado es atribuible.

---

# PARTE 1 — LA TABLA QUE PEDISTE

Archivo escrito: **`_RANKING_CUENTAS.csv`** (60 filas, abrible en Excel).

### Advertencia metodológica primero (importa)
"Creativos capturados" está **topado en 18 por página** porque ese fue mi límite de extracción. **No es el volumen real.** El volumen real es `ads_activos_reales` (de `_PAGINAS.csv`). Cualquier lectura tipo "esta cuenta tiene más imágenes" tiene que salir de esa columna, no de lo que yo capturé.

### La métrica que de verdad responde tu pregunta
Vos dijiste: *"si una cuenta está pautando muchas imágenes y está escalando con muchas imágenes, le sabe a las imágenes"*. Correcto, pero el volumen solo no lo prueba — una cuenta puede tener 100 ads porque es un bazar con 100 productos. La señal fina es **`intensidad_duplicacion` = instancias Meta (`collation_count`) ÷ creativos distintos**: cuántas veces la cuenta **duplica el mismo creativo**. Duplicar cuesta plata; solo se duplica lo que funciona. Esa es la huella de "encontró algo y lo está martillando".

### TOP por volumen real

| Anunciante | ads activos | intensidad | día más viejo | veredicto |
|---|---:|---:|---:|---|
| Trendora | 109 | 1.19 | 29 | VOLUMEN+ganador |
| VitalBio | 102 | 1.00 | 119 | ⚠️ 82% catálogo — no evaluable |
| Dr. Felipe Flores | 60 | 1.00 | 153 | VOLUMEN+ganador |
| Aranza Glow | 58 | 1.00 | 113 | VOLUMEN+ganador |
| Tiendas KetsalStore | 50 | **2.06** | 13 | volumen + duplica, sin ganador aún |
| Tu oferta Online | 45 | 1.31 | 65 | VOLUMEN+ganador |
| **Camila Recomienda** | 43 | **7.17** | 24 | **ESCALA FUERTE + ganador** |
| RyR Importaciones | 39 | 1.07 | 126 | VOLUMEN+ganador |
| Rincón de las Ventas | 33 | 1.00 | 56 | VOLUMEN+ganador |
| Doctora Patricia Morales | 31 | 2.13 | 6 | duplica, sin ganador |
| Guate compra | 31 | 1.33 | 63 | VOLUMEN+ganador |
| Flor Exprés GT | 29 | 2.36 | 3 | duplica, muy nueva |
| Clickazogt | 21 | 1.00 | 12 | ⚠️ 100% catálogo — no evaluable |

### El hallazgo fuerte: **Camila Recomienda**
**6 creativos distintos → 43 instancias en Meta. Intensidad 7.17.** El siguiente más alto (real) es KetsalStore con 2.06. Es un **outlier de 3.5x**. Traducción: encontró 6 imágenes que le funcionan y las está corriendo en masa en vez de crear nuevas. Uno solo de sus creativos tiene `cc=16` — dieciséis instancias de UNA imagen. **Ese creativo es el activo más validado de todo el banco.** Tu intuición ("Camila Recomienda superbuena") no solo era correcta: era el caso más fuerte de los 95 anunciantes.

### Contraste honesto con tus otras intuiciones
No para llevarte la contraria, sino porque una auditoría que solo confirma no sirve:

| Tu lectura | Lo que dice la data | Interpretación |
|---|---|---|
| Camila Recomienda "superbuena" | intensidad 7.17, 24d | ✅ **Confirmado, el más fuerte** |
| Trendora "superbuena" | 109 activos, 29d | ✅ Confirmado |
| FrezNova "superbuena" | 17 activos, 27d | ✅ Confirmado |
| Tiendas KetsalStore "superbuena" | intensidad 2.06 pero **máx 13 días** | ⚠️ **Testeador de alta velocidad, sin ganador validado aún.** Duplica mucho (por eso lo notaste) pero nada le ha sobrevivido 21 días. Es una cuenta *agresiva*, no una cuenta *probada*. Vale seguirla — si algo suyo cruza 21d, ese sí es oro. |
| Aurora GT "superbuena" | intensidad 1.38, máx 7d | ⚠️ La más débil de las que nombraste |
| Mi Camino al Bienestar "superbuena" | intensidad 1.12, máx 10d | ⚠️ Sin ganador validado |

**Lo que esto te dice de vos como operador:** tu ojo detecta bien la *actividad* (quién se mueve mucho, quién duplica). Lo que el ojo no distingue es *actividad* de *validación*. KetsalStore se ve enérgica porque lo es — pero energía sin permanencia es testeo, no es un ganador. Ese es justamente el filtro que la data agrega a la intuición.

### Filtro obligatorio antes de mirar imágenes
**VitalBio (82% catálogo) y Clickazogt (100% catálogo)** hay que sacarlos del análisis creativo. Sus "ads" son contenedores de feed dinámico — no hay hook, ni concepto, ni composición deliberada que copiar. VitalBio engaña especialmente: 102 ads activos y uno de 119 días se ve como el mejor de la lista, y no aporta nada para tu propósito.

---

# PARTE 2 — QUÉ TIENE Y QUÉ NO TIENE EL SISTEMA

Preguntaste si dolor, deseo, avatar, punto B están en el sistema *"porque si no está, no entiendo por qué"*. **Sí están, y bien.** Ubicación exacta:

| Lo que preguntaste | Dónde vive | ¿Se trackea? |
|---|---|---|
| Puntos de dolor reales (no inventados) | `etapa-1b` → mina Reddit/foros/reseñas → **BANCO DE DOLOR REAL** con frases `[VOZ-REAL]` | `dolor_nucleo` |
| Avatar (quién es específicamente) | `etapa-2` Paso 1 → **5 ejes**: dolores, deseos, miedos, frustraciones, emoción/necesidad oculta | `avatar`, `avatar_edad`, `avatar_genero` |
| Deseos / Punto B | `etapa-2` → "Punto A → Punto B" en la ficha de ángulo | parcial |
| Nivel de conciencia | `etapa-2` 6º eje (Niveles 1, 2, 3a, 3b) | `nivel_conciencia` |
| Emoción dominante | `etapa-2` → **vocabulario cerrado** de 7 valores | `emocion_dominante` |
| Objeciones | `etapa-3a` → 10+ sub-dolores, mín. 3 `[EXTERNO]` | — |

Esto es un sistema de investigación de avatar **muy por encima del promedio**. No hay nada roto ahí.

### El agujero: CONCEPTO

El sistema **sí sabe** que los conceptos importan. Está escrito en dos lugares:

- `ETAPA-2.md` línea 231: *"un ángulo = un CONCEPTO creativo distinto por conjunto — no la misma imagen con otro título/color/fuente. **Las iteraciones murieron, los conceptos reinan**"* (Clase 2)
- `ESCALADO_PLAYBOOK.md` §4: *"Conservar el ángulo, variar el CONCEPTO"* · *"Se copia el POR QUÉ vendió, no el creativo"* (Clase 20)

Pero comparemos cómo trata el sistema a cada dimensión:

| Dimensión | ¿Catálogo cerrado? | ¿Campo en CSV? | ¿Se puede aprender de ella? |
|---|---|---|---|
| Ángulo | ✅ 16 tipos | ✅ `angulo_key` | ✅ sí |
| Emoción | ✅ 7 valores | ✅ `emocion_dominante` | ✅ sí |
| Avatar edad/género | ✅ buckets | ✅ ambos | ✅ sí |
| Nivel de conciencia | ✅ 4 niveles | ✅ `nivel_conciencia` | ✅ sí |
| Rol de embudo | ✅ TOFU/MOFU/BOFU | ✅ `rol_embudo` | ✅ sí |
| Estilo visual | ✅ 15 estilos | ❌ **no se guarda** | ❌ no |
| **CONCEPTO** | ❌ **no existe catálogo** | ❌ **no se guarda** | ❌ **no** |

**El sistema ya vivió este problema exacto y lo resolvió — pero solo para el avatar.** El comentario en `ETAPA-2.md` (líneas 168-174) lo explica textualmente:

> *"ETAPA-2 produce una ficha rica pero hasta ahora solo sobrevivían `avatar` y `dolor_nucleo` como TEXTO LIBRE — 28 y 33 valores distintos en 54 conjuntos, imposibles de agregar. Toda esa investigación se usaba para escribir el copy y DESPUÉS SE PERDÍA: nunca se contrastaba contra quién compró."*

Esa es **exactamente** la enfermedad que hoy tiene el concepto. Se diagnosticó, se curó para el avatar, y **no se aplicó la misma cura a la capa creativa**. Por eso hoy no podés responder "qué tipo de imagen vende": la respuesta nunca se guardó.

---

# PARTE 3 — EL PROBLEMA GRAVE: ÁNGULO Y CONCEPTO ESTÁN CONFUNDIDOS

Esta es la parte importante de la auditoría.

### Cómo testea FASE 1 hoy
6 conjuntos, cada uno con:
- un **ángulo distinto** (por diseño — es lo que se quiere medir)
- un **concepto distinto** (por regla explícita, línea 231 de ETAPA-2)
- un **formato distinto** (VIDEO si hay video que calce, IMAGEN si el ángulo es virgen)

**Tres variables cambian a la vez entre conjuntos.** Cuando el conjunto 3 gana, no hay forma de saber si ganó por el ángulo, por el concepto o porque le tocó video. Es un experimento sin control.

El sistema **ya detectó la mitad de este problema** — `PLANTILLAS_ADS.md` línea 196 habla del *"confound de formato"* y propone mitigarlo. Pero **no vio el confound de concepto, que es más grande**, porque el concepto impacta más que el formato.

Y encima esto choca de frente con la regla 6 del orquestador: las ventas por conjunto tienen dispersión de Poisson (1-3 ventas, IC ±113-196%). O sea: **3 variables confundidas medidas sobre ruido puro.** Estructuralmente no se puede aprender nada a nivel conjunto. Por eso la regla 6 obliga a agregar por `angulo_key` — que es la decisión correcta, pero deja el concepto sin medir para siempre.

### Tu intuición era la correcta
Dijiste: *"la idea sería testear ángulos siempre bajo el mismo concepto para testear los ángulos"*. **Eso es exactamente el principio de diseño experimental correcto:** para medir una variable, se fijan las demás. Es la solución.

### El diseño que propongo

```
FASE 1 — se mide ÁNGULO          FASE 2 — se mide CONCEPTO
─────────────────────────        ─────────────────────────
Variable:  ÁNGULO (6 distintos)  Variable:  CONCEPTO (6-12 distintos)
FIJO:      CONCEPTO (1 control)  FIJO:      ÁNGULO (el ganador)
FIJO:      FORMATO (1 solo)      FIJO:      formato preferente
→ el ganador es del ÁNGULO       → el ganador es del CONCEPTO
```

### La tensión que hay que resolver honestamente
Fijar el concepto en FASE 1 **contradice la letra** de la regla 231 ("diversificación de conceptos es lo que premia Andrómeda"). Esa regla existe por algo real: Meta penaliza creativos duplicados y premia diversidad.

**La salida: "familia de concepto", no "imagen clonada".** Los 6 conjuntos usan el **mismo dispositivo narrativo** (ej. los 6 son TESTIMONIO) pero **cada uno renderizado único** — distinta persona, escena, paleta, testimonio. Para Meta son 6 creativos completamente distintos (su detección es por huella de contenido, según `LAVADO.md`), así que la diversidad de entrega se mantiene. Para vos, la variable "dispositivo" queda fija y el ángulo queda limpio.

Lo que la regla 231 realmente quiere prohibir es la **iteración perezosa** (misma imagen, otro título/color). Eso sigue prohibido. La regla necesita reescribirse para distinguir *concepto* de *iteración*, que hoy mezcla.

---

# PARTE 4 — CATÁLOGO DE CONCEPTOS PROPUESTO (hipótesis a validar)

Tres capas que **hoy se confunden entre sí** y hay que separar con nombre propio:

- **ÁNGULO** = *por qué* le duele (territorio del problema) — ya catalogado, 16 tipos
- **CONCEPTO** = *cómo se muestra* (dispositivo narrativo/visual) — ← **lo que falta**
- **ESTILO** = *con qué piel* (estética: minimalista, oscuro de lujo…) — catalogado, no trackeado

Catálogo candidato, derivado del vocabulario que **ya usa el sistema** (`FORMATO CREATIVO` de CLAUDE.md + §4 de ESCALADO + los 15 estilos) y de lo que se ve en el swipe file:

| # | CONCEPTO | Dispositivo | Se reconoce por |
|---|---|---|---|
| 1 | `TESTIMONIO` | persona real + reseña + producto | burbuja de chat, 5 estrellas, cara |
| 2 | `DEMO_USO` | producto siendo usado | mano aplicando, escena de uso |
| 3 | `EDUCATIVO_MECANISMO` | explica el porqué | diagrama, ingrediente destacado, flecha |
| 4 | `COMPARACION` | con/sin, A vs B | imagen partida (nunca antes/después corporal) |
| 5 | `AUTORIDAD` | figura experta | bata, médico, sello profesional |
| 6 | `PRUEBA_SOCIAL_NUM` | el número manda | "+5,986 clientes", "4.9/5" |
| 7 | `OFERTA_PRECIO` | el precio es protagonista | precio gigante, 2x1, starburst |
| 8 | `AMENAZA_CHOQUE` | el problema crudo en primer plano | ya documentado como "enfoque agresivo" |
| 9 | `PRODUCTO_HERO` | producto limpio, sin persona | fondo de estudio |
| 10 | `CONVERSACION_CHAT` | captura de WhatsApp | pantallazo de chat |

Es **hipótesis, no dogma.** El swipe file (597 creativos) existe precisamente para validarla: si al mirar las imágenes aparece un dispositivo que no está en la lista, entra; si dos nunca se distinguen en la práctica, se fusionan. **El catálogo final tiene que salir de las imágenes reales, no de mi propuesta.**

Regla de tamaño: **8-12 valores máximo.** Si son 30, vuelve a ser texto libre y no se puede agregar (la lección del avatar).

---

# PARTE 5 — DIVISIÓN DE TRABAJO

Propusiste *"yo lo hago manual y tú en automático y después comparamos"*. **Es exactamente el método correcto** — se llama acuerdo entre evaluadores, y es la forma estándar de validar una taxonomía. Donde vos y yo coincidimos, la categoría está bien definida. Donde discrepamos, la categoría es ambigua y hay que arreglarla. **Las discrepancias son el producto valioso, no el error.**

### LO QUE HAGO YO
1. **Pre-clasificar los 597 creativos** por señales de texto (título/descripción/copy). Ej.: `+5,986 clientes` → `PRUEBA_SOCIAL_NUM`; `Contactar a Dr.` → `AUTORIDAD`. Rápido y a escala, pero **es un proxy** — el texto correlaciona con el concepto, no lo determina.
2. **Verificar visualmente una muestra** leyendo las imágenes directamente, para medir cuánto se equivoca el proxy.
3. **Agregar `concepto_key` a `_DIM_CONJUNTOS.csv`** + al output de `etapa-4`, para que de acá en adelante todo creativo nazca etiquetado.
4. **Filtro de catálogo** en `gen_galeria.py` (los 49 dinámicos fuera del ranking).
5. **Reescribir la regla 231** de ETAPA-2 para separar concepto de iteración y permitir el concepto-control en FASE 1.
6. **Especificar el rediseño FASE 1 / FASE 2** con el concepto-control.

### LO QUE HACÉS VOS
1. **Clasificar a ojo una muestra de ~60 creativos** en la galería (podés filtrar por anunciante). Sin ver mi clasificación — si la ves, se contamina y el ejercicio pierde el sentido.
2. **Empezar por Camila Recomienda** (6 creativos, intensidad 7.17). Son los más validados del banco: qué concepto usan es la pregunta más rentable que tenemos.
3. **Decidir el `concepto_control` de FASE 1** — cuál dispositivo va a ser el estándar para validar producto. Es una decisión de negocio, no de data: la data te dice qué funciona en otros, vos decidís qué puede producir tu operación de forma repetible.
4. **Nombrar los conceptos que veas y yo no tenga en la lista.**

### LO QUE HACEMOS JUNTOS
Comparar las dos clasificaciones sobre la misma muestra → medir coincidencia → las discrepancias definen el catálogo final → recién ahí se congela el vocabulario cerrado.

---

## ORDEN RECOMENDADO

1. Yo: filtro de catálogo + pre-clasificación por texto *(sin esto, mirás imágenes contaminadas con 49 ads de feed)*
2. Vos: clasificación manual a ciegas de la muestra
3. Juntos: reconciliar → congelar catálogo
4. Yo: `concepto_key` en el esquema + reescritura de reglas + rediseño FASE 1/FASE 2
5. Primer producto que salga ya corre con concepto-control y con el concepto trackeado

**No empieces por el paso 2 sin el 1.** Mirar 597 imágenes con 59 de catálogo mezcladas es ruido, y el catálogo se concentra justo en las cuentas de más volumen (VitalBio, Clickazogt), que es donde tu ojo va a ir primero.

---

# ANEXO — RESULTADO DEL PASO 1 (ejecutado 2026-08-18)

## A) Filtro de catálogo — HECHO
**59 creativos** marcados `CATALOGO_DINAMICO` sobre 597 (9.9%). En `_GALERIA.html` ahora van atenuados, al final del orden, con etiqueta roja, y hay filtro **"Ocultar catálogo dinámico"** activado por defecto. También se agregó **filtro por concepto**.

## B) Pre-clasificación por texto — HECHA, y el resultado es un hallazgo en sí mismo

| Resultado | Nº | % |
|---|---:|---:|
| **REVISAR_VISUAL** (sin firma textual) | **410** | **68.7%** |
| OFERTA_PRECIO | 69 | 11.6% |
| CATALOGO_DINAMICO | 59 | 9.9% |
| AUTORIDAD | 16 | 2.7% |
| PRUEBA_SOCIAL_NUM | 15 | 2.5% |
| TESTIMONIO | 9 | 1.5% |
| AMENAZA_CHOQUE | 8 | 1.3% |
| EDUCATIVO_MECANISMO | 7 | 1.2% |
| DEMO_USO / AMBIGUO | 4 | 0.7% |

**El texto solo pudo clasificar el 21% de los creativos.** No es un defecto del clasificador: es que **el copy lleva el ÁNGULO y la imagen lleva el CONCEPTO**. Son capas distintas y una no predice a la otra. Esto convierte tu pasada visual de "deseable" a **indispensable** — el 79% restante no existe fuera de las imágenes.

## C) Calibración visual sobre Camila Recomienda — el caso más valioso

Los **6 creativos de Camila** (intensidad 7.17, los más validados del banco) salieron **los 6 en `REVISAR_VISUAL`**. Los leí directamente. Lo que el texto no podía ver:

| Creativo | cc | Lo que la imagen realmente es |
|---|---:|---|
| `01_…074` — OFTALMIEL 2 frascos | **16** | **OFERTA_PRECIO puro.** "2 FRASCOS" gigante + Q209.83 + "MÁS VENDIDO" |
| `12_…693` — Candida Cleanse | 9 | **Híbrido:** AUTORIDAD (médico + sello FDA) + collage de 4 síntomas + precio |
| `25_…403` — carnosidad ocular | 4 | **Híbrido:** hook de pregunta + precio tachado (Q200→Q152.78) + íconos de beneficio |

### Hallazgo 1 — el copy y la imagen hablan de cosas distintas
El copy del creativo #1 es *"Tus ojos arden, se sienten secos…"* (ángulo: dolor ocular). La imagen **no muestra nada de eso**: es un cartel de precio. Angulo y concepto son ortogonales — confirmado con el creativo más duplicado del banco.

### Hallazgo 2 — los ganadores reales son HÍBRIDOS, no conceptos puros
Ninguno de los 3 es un concepto único. Combinan 2-4 dispositivos. **El catálogo necesita una regla de desempate:** `concepto_dominante` = el dispositivo que ocupa más peso visual / lo primero que pega el ojo. Sin esa regla, clasificar híbridos es arbitrario y vos y yo nunca vamos a coincidir.

### Hallazgo 3 — hay un ESQUELETO repetido (esto es lo aprovechable)
Los 3 comparten la misma estructura, cambiando solo el relleno:

```
1. HOOK arriba (pregunta de dolor o promesa)
2. PRODUCTO grande, protagonista
3. Fila de ÍCONOS de beneficio (3-4)
4. PRECIO prominente  ← presente en los 3, SIEMPRE
5. Franja de CONFIANZA abajo (envío gratis · pago contra entrega · país de origen)
```

**El precio visible aparece en el 100% de los creativos más escalados del banco.** Contrastar con la regla actual del sistema: *"precio máx 3 de 6, ideal 2 de 6"*. El mejor performer del mercado guatemalteco hace lo contrario — precio en todos. No es prueba suficiente para cambiar la regla (1 anunciante), pero **sí es una hipótesis que merece un test explícito**, y hoy el sistema no la tiene en el radar.

### Hallazgo 4 — el sistema ya apunta al lugar correcto
Ese esqueleto es casi idéntico a la jerarquía del **PROMPT MAESTRO** (`PLANTILLAS_ADS.md`): marca → hook → producto → beneficio → CTA → prueba social → oferta. **La plantilla del sistema coincide con lo que hace el mejor del mercado.** El problema nunca fue la plantilla: es que no se registra qué versión de ella se usó, así que no se puede aprender cuál gana.

## D) Consecuencia para el reparto de trabajo
Mi pre-clasificación **no te ahorra la pasada visual** — te ahorra el 21% y te deja el catálogo filtrado. Sugerencia de orden, por rentabilidad:
1. Los **6 de Camila** (ya los tenés arriba, úsalos como patrón de referencia)
2. Los `WINNER_CALIENTE` + 21 días con `cc>=2` (los validados)
3. El resto de `REVISAR_VISUAL`

Y la pregunta a responder mientras mirás **no es** "¿qué concepto es este?" sino **"¿qué dispositivo domina y qué esqueleto tiene?"** — el hallazgo 3 sugiere que el esqueleto puede importar más que el concepto.

---

# PARTE 6 — ARQUITECTURA DE PLANTILLAS (propuesta del sistema)

> Responde a la propuesta del operador: *"tener cinco layouts por concepto, por nicho — cinco de testimonio, cinco con precio, cinco de beneficios — y basar todo el sistema en eso"*.

## 6.1 — Dónde discrepo, y por qué

La idea de fondo es correcta: **plantillas fijas en vez de creatividad improvisada.** Es exactamente lo que hace el mejor anunciante del mercado local. Pero el dimensionamiento propuesto rompe el sistema por dos lados.

### Objeción 1 — 5 por concepto × 10 conceptos = 50 plantillas. Es demasiado para aprender.

Volumen real de la operación: 6 conjuntos por producto, unos 2-4 productos por mes → **12-24 conjuntos/mes**. Con 50 plantillas, cada una se vería **menos de una vez cada dos meses**. Nunca se acumularía evidencia suficiente para saber cuál funciona.

Y esto no es teoría: es la **regla 6 del orquestador**, ya medida con data propia. Las ventas por conjunto tienen índice de dispersión 1.12 (azar de Poisson casi puro); recién al agregar por `angulo_key` sube a 2.99 (señal real). **Una dimensión con 50 valores nunca agrega.** Sería repetir con las plantillas el error que el sistema ya corrigió con el avatar.

Con **4-5 plantillas totales**, cada una recibe 3-6 observaciones por mes. En un trimestre son 9-18 cada una. Eso sí es aprendible.

### Objeción 2 — "por nicho" mata la transferibilidad, que es lo más valioso que tiene el sistema

El propio `ETAPA-2.md` lo justifica al explicar el vocabulario cerrado del avatar:

> *"Estos 3 campos, con vocabulario cerrado, son lo que la vuelve aprendible y **TRANSFERIBLE ENTRE PRODUCTOS** (si la vergüenza vende en várices, se prueba vergüenza en acné)."*

La misma lógica aplica acá. Si las plantillas son por nicho, cada nicho aprende solo y desde cero. Si son **transversales**, lo que aprendés en tinnitus lo aplicás en várices el mes siguiente. **Las plantillas tienen que ser cross-producto o no sirven para acumular.**

Lo que sí cambia por nicho no es la plantilla: es **el relleno** (props, paleta, badges, tono).

## 6.2 — La arquitectura que propongo

Dos niveles, no uno:

```
PLANTILLA  (4-5, fijas, cambian lento)     ← es la CONSTANTE que permite aprender
   └─ VARIANTES (infinitas, por producto)  ← es lo que mantiene contento a Meta
```

- **PLANTILLA** = esqueleto espacial + dispositivo dominante. Se nombra, se cataloga, **se guarda en el CSV**.
- **VARIANTE** = el relleno: hook, producto, props, paleta, badges, testimonio. Cambia siempre. **No se cataloga.**

**El punto clave:** Meta detecta duplicados por huella de contenido (`LAVADO.md`), **no por estructura**. Así que 6 anuncios con la misma plantilla y distinto relleno son 6 creativos únicos para Andrómeda — la diversidad de entrega se mantiene — pero para nosotros la variable "plantilla" queda fija y medible.

> **La plantilla es la constante que hace posible aprender; la variante es lo que evita el baneo.** Esa es toda la idea.

## 6.3 — Las 5 plantillas candidatas

⚠️ **Base de evidencia honesta:** salen de 1 análisis profundo (Camila cc=16), 3 imágenes vistas en detalle y el vocabulario que el sistema ya tiene. **Son hipótesis.** Se confirman o se corrigen con tu pasada manual sobre los 538.

Cuatro de las cinco **ya existen parcialmente** en el sistema — esto es adaptación, no reescritura, como pediste.

| # | PLANTILLA | Esqueleto | Rol embudo | ¿Ya está en el sistema? |
|---|---|---|---|---|
| P1 | **TARJETA DE OFERTA** | numeral cantidad → producto → precio dual → franja confianza | **BOFU** | parcial (§7 sello starburst) |
| P2 | **AUTORIDAD CLÍNICA** | figura experta → producto → collage síntomas → credencial | MOFU | parcial (banco de ángulos: autoridad) |
| P3 | **TESTIMONIO / CHAT** | burbuja WhatsApp → producto → beneficio corto | MOFU | **sí** (`PLANTILLAS_ADS.md` §B) |
| P4 | **HOOK DE PROBLEMA** | pregunta de dolor grande → producto → íconos beneficio | **TOFU** | parcial (fórmula de hook) |
| P5 | **CHOQUE / AMENAZA** | amenaza cruda primer plano → producto resolviendo | TOFU | **sí** (enfoque agresivo) |

**P1 es la única validada con data dura** (el creativo más replicado del mercado). Las otras cuatro son observadas pero no medidas.

## 6.4 — El detalle que casi se me pasa: P1 NO sirve para FASE 1

Camila puede usar la Tarjeta de Oferta porque **su audiencia ya conoce el producto** (nivel de consciencia 4). Su anuncio no nombra el problema ni una vez — no le hace falta.

Pero en FASE 1 estamos **validando un producto nuevo**, con audiencia en nivel 1-2 (no sabe que tiene el problema, o lo sabe pero no la solución). Y sobre todo: **FASE 1 mide el ÁNGULO.** Una plantilla que ni menciona el problema es la peor posible para medir qué ángulo resuena — lo entierra.

**Conclusión:**
- **FASE 1 → `concepto_control` = P4 (HOOK DE PROBLEMA).** Es la que pone el ángulo al frente, que es justo lo que se está midiendo. Los 6 conjuntos usan P4 con 6 ángulos distintos y relleno único cada uno.
- **FASE 2 → se abre el abanico.** El ángulo ya está fijo (el ganador); ahora se varían las 5 plantillas para encontrar la mejor ejecución.
- **P1 es arma de escalado, no de validación.** Entra cuando el producto ya vende y hay que exprimir al que compara precio.

Esto **encaja con `rol_embudo`, que ya existe** en `_DIM_CONJUNTOS.csv` y ya está mapeado a TOFU/MOFU/BOFU. No hay que inventar nada: cada plantilla declara su rol y el campo ya está.

## 6.5 — Qué se agrega al esquema

Un solo campo nuevo en `_DIM_CONJUNTOS.csv`:

```
plantilla_key   [P1_OFERTA | P2_AUTORIDAD | P3_TESTIMONIO | P4_HOOK_PROBLEMA | P5_CHOQUE]
```

Con eso, en 3 meses se puede responder por primera vez: *¿qué plantilla trae el CPA más bajo, en qué nicho y con qué emoción?* Hoy esa pregunta no tiene respuesta posible.

## 6.6 — Resumen de la discrepancia

| | Tu propuesta | Mi recomendación | Por qué |
|---|---|---|---|
| Cantidad | 5 por concepto (~50) | **4-5 en total** | con 50 nunca se acumula evidencia (regla 6) |
| Alcance | por nicho | **transversales** | transferibilidad entre productos (principio ya establecido) |
| Variantes | ✅ variar textos/imágenes | ✅ **igual** | acá coincidimos: la variante evita el baneo |
| Uso | todas siempre | **1 fija en FASE 1, abanico en FASE 2** | FASE 1 mide ángulo: hay que fijar lo demás |
