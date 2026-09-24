# PLANTILLAS INFOGRAFÍAS — SISTEMA VITALCOM GUATEMALA

## INSTRUCCIONES DE USO
Estas 4 plantillas son el sistema de infografías definitivo y validado.
El formato, estructura e instrucciones de cada plantilla son **FIJOS** — no modificar ni resumir.
Solo reemplazar los valores entre `[ ]` con los datos del producto actual.

> **⭐ ADAPTACIÓN POR ÁNGULO EN FASE 2:** cuando el bot es DEDICADO a un solo ángulo (FASE 2, escalado), las infografías del flujo se entregan como **prompts COMPLETOS ya adaptados al ángulo dedicado**, no como deltas ni instrucciones ("cambiá X"). Qué se adapta y qué NO:
> - **INFO 1 (beneficios):** título = dolor/deseo del ángulo + el beneficio de ese ángulo pasa a ser el **#1** de la lista.
> - **INFO 2 (transformación + ingredientes + modo de uso):** SOLO la ZONA 1 (antes/después) se adapta al ángulo (reseña o evidencia de ESE dolor→resultado). Las ZONAS 2 (ingredientes) y 3 (modo de uso) NO cambian.
> - **INFO 3 (confianza):** cambia solo el HEADLINE y el 1er bloque estadístico al ángulo; contraentrega, garantía, FAQ y certificaciones NO cambian.
> - **NO cambian por ángulo:** el ADN visual del PASO 0 (color, tipografía, frasco), la IMAGEN 4 (anti-imitación) y la IMAGEN 6 (recuperación). En FASE 1 (bot paraguas) las infografías se mantienen genéricas del producto.

> **PIEZA DE RECUPERACIÓN POST-VENTA POR PRODUCTO (IMAGEN 6 — NOVEDAD):** además de las 4 infografías del flujo de venta (IMAGEN 1-4), existe una pieza de recuperación **que sí se adapta al producto** y se envía cuando el pedido está a punto de devolverse: **IMAGEN 6 — RECUPERACIÓN DE NOVEDAD** (al final del archivo). Hereda el mismo PASO 0 (color, [KIT_TIPO_LETRA], render del frasco) que las otras 4. **IMAGEN 5 queda reservada** para otra pieza per-producto futura.
>
> **OJO — piezas FIJAS de logística NO van en este archivo:** las imágenes de *pedido en reparto* y *reclamar en oficina* **no se adaptan al producto** (misma imagen para todos; los datos del pedido — monto, transportadora, dirección — van en el TEXTO de la plantilla, no en la imagen). Son piezas FIJAS que se generan una sola vez (no por producto; sí por transportadora — Forza / Gintracom con sus colores y sellos), por eso no van acá.

> **Doctrina vs. prompt final:** los bloques citados en formato de cita (`> ...`, con referencia a Clase/mentor) son notas internas de criterio — explican el PORQUÉ de la regla para quien construye o ajusta la plantilla. Esas notas NUNCA se copian al prompt final ni a `1_HACER_MANUAL.txt`. Lo que sí se copia es el texto de la plantilla (fuera de las citas en bloque) con las `[VARIABLES]` ya reemplazadas. Si una cita de mentor aparece SIN el formato de bloque dentro del cuerpo del prompt (ej. "(Clase 22 Joaquín: ...)"), es ruido que se elimina al rellenar — la instrucción funcional se mantiene, solo se quita la referencia a la clase.

> ## ⭐ REGLA MAESTRA DE COLOR (LEER ANTES QUE NADA)
> **El acento dominante de TODA infografía deriva del COLOR DEL PRODUCTO ([COLOR_ACENTO_PRODUCTO]), no de la marca.** Una infografía azul para un producto azul, dorada para uno dorado, naranja para uno naranja. (Clase 14 + PDF Prompt Maestro: "una mala paleta de colores no detiene el scroll"; la paleta debe ser coherente y atractiva, jerarquía por tamaño y contraste.)
>
> **PROHIBIDO forzar el verde lima #caec55 ("verde fosforescente") ni el verde sanarte® #117200 cuando chocan con el color del producto.** El lima neón solo se usa si COMPLEMENTA al producto (salud/detox/verdes). En productos azules, naranjas, dorados, negros, rosados, etc. → el lima se REEMPLAZA por [COLOR_ACENTO_PRODUCTO] en TODOS los elementos: números estadísticos, triángulos de alerta, bandas, separadores, checkmarks.
>
> **Única excepción del lima:** el contorno del logo sanarte® (y solo si se conserva esa marca). Si el verde sanarte® choca con el producto, el logo se parametriza al color de la fanpage (ver PARAMETRIZACIÓN DE MARCA). El logo nunca debe ser el elemento de color más llamativo de la pieza — el protagonista de color es el producto.
>
> **Test rápido antes de generar:** ¿el acento más visible de la pieza es el color del producto? Si lo más llamativo es un verde lima que no está en el frasco → está mal, corregir.

---

## ⭐ PASO 0 — ANÁLISIS DEL PRODUCTO (MOTOR ÚNICO — CORRER ANTES DE TODO)

> **Por qué:** una sola lectura de la imagen del frasco define la identidad visual de TODA la campaña — las 4 infografías Y los ads de Meta. Lo que hace que los ads del proveedor "conecten" no es un truco por pieza: es que todas nacen del mismo ADN visual del producto.

**Analizar la imagen del producto UNA vez y congelar estos 4 ejes. Todo lo demás se deriva de aquí — no se vuelve a decidir por pieza:**

1. **COLOR** → extraer COLOR_PRIMARIO / COLOR_SECUNDARIO / COLOR_OSCURO del frasco/etiqueta (ver INSTRUCCIONES DE EXTRACCIÓN DE COLOR). Define `[COLOR_DEGRADADO_PRODUCTO]` (fondo), `[COLOR_ACENTO_PRODUCTO]` (acentos/números) y toda la paleta. Regla dura: el acento dominante = color del producto; NUNCA fondo blanco plano. (REGLA MAESTRA DE COLOR.)

2. **TIPOGRAFÍA** → leer la **categoría tipográfica de la etiqueta/branding del frasco** y fijar `[KIT_TIPO_LETRA]` (una por producto, idéntica en infografías + ads + landing). La IA aproxima por categoría, no clona la fuente. (Ver KIT TIPOGRÁFICO.)

3. **PRODUCTO HÉROE** → registrar forma, material (plástico/vidrio/gotero/polvo), color de tapa y etiqueta, potencia visible. El frasco se renderiza grande, protagonista, con iluminación dramática (glow/halo de su color, reflejo/pódium). (Clase 14: "producto grande y protagonista".)

4. **TEXTURA DE NICHO** → según la categoría del producto, fijar la micro-textura de fondo (2-5% opacidad) que se usará ENCIMA del fondo de color (ver lista por categoría en IMAGEN 1 VERSIÓN COMPLETA).

> **Documentar el resultado en 1 bloque** (color hex + categoría tipográfica + descripción del frasco + textura) y reusarlo idéntico en cada prompt. Si la imagen del producto cambia → re-correr este Paso 0 completo, nunca parchar una pieza suelta.

---

## MAPA DE VARIABLES POR FUENTE DE DATOS

| Variable | Se extrae de... |
|---|---|
| [NOMBRE_PRODUCTO] | ETAPA-1 |
| [CAPSULAS_CANTIDAD] | Operador / ETAPA-1B |
| [MILIGRAMOS] | Operador / ETAPA-1B |
| [HEADLINE_BENEFICIO] | ETAPA-2 — **TÍTULO IMPACTANTE de dolor/deseo del ángulo, congruente con el anuncio de Meta** (NO la palabra "BENEFICIOS"). Es lo más grande de la pieza. Ej: "TU APOYO DIARIO PARA UNA VIDA MÁS SALUDABLE", "POTENCIA TU ENERGÍA CADA DÍA", "SOPORTE NATURAL PARA TU SISTEMA NERVIOSO". (Clase 22 Joaquín: título impactante, no genérico; la gente escanea títulos.) |
| [KICKER_BENEFICIOS] | Etiqueta pequeña secundaria, ej: "10 BENEFICIOS" o "FÓRMULA AVANZADA". Va pequeña, NUNCA como título principal. |
| [COLOR_DEGRADADO_PRODUCTO] | Imagen del producto — **FONDO de IMAGEN 1**: degradado o color sólido del frasco/etiqueta (ej: "morado profundo a magenta", "azul marino a azul eléctrico", "dorado oscuro a negro cálido"). NUNCA blanco plano. Es el fondo que hace que la pieza "conecte" como los ads del proveedor. |
| [COLOR_DEGRADADO_ENCABEZADO] | Imagen del producto (ej: "azul-verde", "blanco y rosa cálido") |
| [COLOR_BOTON_ENCABEZADO] | Imagen del producto (color primario, ej: "azul", "rosa cálido") |
| [DECORACION_ENCABEZADO] | Relativo al producto (ej: "hojas de menta y rodajas de limón", "pétalos de rosa") |
| [COLOR_BANDA_ETIQUETA] | Imagen del producto (ej: "azul oscuro", "rosa cálido") |
| [BENEFICIOS_ETIQUETA] | ETAPA-2 (resumen de beneficios clave para el texto de la etiqueta) |
| [INGREDIENTES_BASE_BOTELLA] | ETAPA-1B (ingredientes principales en su forma natural visual) |
| [COLOR_CIRCULOS_BENEFICIOS] | Imagen del producto (color primario, ej: "azules", "rosa cálido") |
| [BENEFICIO_N_ICONO] | **Ícono ilustrado A COLOR** relativo al beneficio, estilo flat/moderno multicolor (NO línea monocromática), cada uno en el color natural de su concepto (ej: rayo amarillo = energía, corazón rojo = sangre/circulación, cerebro rosado = memoria, escudo azul = protección, hoja verde = vegano). Descrito como "Ilustración 3D die-cut de [concepto]", tamaño moderado (un poco más pequeña de lo que sale por defecto) + su NÚMERO. Ver REGLA DE ESTILO DE ÍCONOS en IMAGEN 1. |
| [BENEFICIO_N_TITULO] | ETAPA-2 (dolor/deseo en mayúsculas) |
| [BENEFICIO_N_DESC] | ETAPA-2 (descripción corta) |
| [COLOR_BARRA_INFERIOR] | Imagen del producto (color oscuro secundario) |
| [FOOTER_TEXTO_IZQ] | ETAPA-2 (categoría de bienestar, ej: "BIENESTAR CARDIOVASCULAR, TODOS LOS DÍAS.") |
| [ICONO_FOOTER_DER] | Relativo al producto (ej: "hoja de menta", "hoja verde", "gota de agua") |
| [DIAS_RESULTADO] | Operador (tiempo de efecto real del producto) |
| [ETIQUETA_ANTES] | ETAPA-2 (dolor central, ej: "DÍA 1 · FATIGA Y BAJA ENERGÍA") |
| [ETIQUETA_DESPUES] | ETAPA-2 (resultado, ej: "DÍA 21 · ENERGÍA Y BIENESTAR") |
| [EXPRESION_FISICA_ANTES] | ETAPA-2 (cómo se ve el dolor físicamente en la selfie) |
| [EXPRESION_FISICA_DESPUES] | ETAPA-2 (cómo se ve la transformación físicamente en la selfie) |
| [N_INGREDIENTES] | ETAPA-1B (conteo de ingredientes activos) |
| [LISTA_INGREDIENTES_ACTIVOS] | ETAPA-1B — formato: ● NOMBRE → función en 1 línea |
| [CAPSULAS_DOSIS] | Operador (ej: "2 CÁPSULAS") |
| [MOMENTO_USO_TITULO] | Operador (ej: "DE NOCHE", "EN LA MAÑANA") |
| [MOMENTO_USO_SUBTEXTO] | Operador (ej: "30 min antes de dormir", "con el desayuno") |
| [ICONO_MOMENTO_3D] | Relativo al momento (ej: "Luna creciente 3D", "Sol cálido 3D radiante") |
| [HEADLINE_CLINICO] | ETAPA-2 (promesa + días, ej: "RESULTADOS CLÍNICOS EN 30 DÍAS") |
| [PORCENTAJE_1] | Estadística de COMPORTAMIENTO DEL CLIENTE — usar ratio ("4 de cada 5"), puntuación ("4.9/5") o porcentaje ≥98.X% con decimal. NUNCA porcentaje de eficacia clínica entre 70-90%: activa efecto-falla en el consumidor guatemalteco. |
| [STAT_1_DESCRIPCION] | ETAPA-2 — redactar como comportamiento o experiencia del cliente, no como resultado médico |
| [PORCENTAJE_2] | Estadística de VELOCIDAD o RECOMPRA — usar tiempo ("Resultados en 21 días"), ratio de recompra ("9 de cada 10 repiten") o % satisfacción ≥98% con decimal. Evitar porcentajes clínicos de eficacia sin respaldo verificable. |
| [STAT_2_DESCRIPCION] | ETAPA-2 |
| [NUMERO_CLIENTES] | Dato real de la marca (ej: "+12,000") |
| [CLIENTES_DESCRIPCION] | ETAPA-2 (resultado en 1 línea) |
| [GARANTIA_TEXTO] | Operador / default. Sello de garantía en IMAGEN 3 junto al contraentrega. Default compliance-safe: "Garantía de satisfacción · Acompañamiento del equipo". Sobrescribir con la garantía real si existe (ej: "30 días de garantía"). NO prometer reembolso 100% sin política confirmada. |
| [COLOR_ETIQUETA_FRASCO_DOCTORA] | Imagen del producto (color de la etiqueta) |
| [COLOR_FONDO_OSCURO] | COLOR_OSCURO del producto si mantiene legibilidad de texto blanco; de lo contrario #0a1628. Se usa en fondos de ZONA 1 y ZONA 2 de IMAGEN 2 y en el degradado izquierdo de IMAGEN 3. |
| [COLOR_ACENTO_PRODUCTO] | COLOR_PRIMARIO del producto. Acento estructural y visual dominante de las 4 piezas: IMAGEN 2 (separadores, bordes ZONA 2, bullets de ingredientes, flechas de modo de uso), IMAGEN 3 (separador de headline, zoom de confianza, separador FAQ, borde de certificaciones **y los 3 números estadísticos grandes**), IMAGEN 4 (triángulos, bandas, checkmarks). Reemplaza al antiguo #caec55 fijo. Ver REGLA MAESTRA DE COLOR. |
| [FAQ_1_PREGUNTA] | ETAPA-3 Fase 2 / ETAPA-2 Fase 1 (objeción principal) |
| [FAQ_1_RESPUESTA] | ETAPA-3 Fase 2 / ETAPA-2 Fase 1 |
| [FAQ_1_ICONO_3D] | Derivado de la pregunta (ej: "Batería verde 3D cargándose") |
| [FAQ_2_RESPUESTA] | ETAPA-3 Fase 2 / ETAPA-2 Fase 1 |
| [FAQ_3_PREGUNTA] | ETAPA-3 Fase 2 / ETAPA-2 Fase 1 |
| [FAQ_3_RESPUESTA] | ETAPA-3 Fase 2 / ETAPA-2 Fase 1 |
| [FAQ_3_ICONO_3D] | Derivado de la pregunta |
| [ATRIBUTO_REAL_1] … [ATRIBUTO_REAL_7] | Sistema — generado con base en ETAPA-1B (ingredientes verificados, certificaciones, sellado, dosificación, respaldo de marca, autenticidad, garantía de envío). 7 ítems. |
| [DEFECTO_FALSO_1] … [DEFECTO_FALSO_4] | Sistema — generado con base en ETAPA-1B (problemas típicos de imitaciones en la categoría del producto: ingredientes diluidos o adulterados, sin control de calidad, sin garantía, riesgo para la salud). 4 ítems. |
| [COLOR_FONDO_OSCURO] (IMAGEN 4) | Mismo valor que [COLOR_FONDO_OSCURO] de IMAGEN 2 e IMAGEN 3. Se usa en BLOQUE 2, BLOQUE 5 y BLOQUE 8. |
| [LOGO_MARCA] | PARAMETRIZACIÓN DE MARCA — default "sanarte®"; adaptable por fanpage |
| [COLOR_LOGO_MARCA] | PARAMETRIZACIÓN DE MARCA — default #117200 (verde sanarte®) |
| [COLOR_ACENTO_MARCA] | PARAMETRIZACIÓN DE MARCA — default #caec55 (lima); cambiar si choca con el nicho |
| [TIPO_LETRA] / [KIT_TIPO_LETRA] | KIT TIPOGRÁFICO — una sola fuente por PRODUCTO, igual en las 4 infografías + ads + bot + landing. Orden: **etiqueta/branding del producto** → ads de referencia → fanpage → default sans-serif (Inter/Poppins). La IA aproxima por categoría, no clona. Ver PASO 0 + KIT TIPOGRÁFICO. |

---

## INSTRUCCIONES DE EXTRACCIÓN DE COLOR

Antes de rellenar cualquier plantilla, analizar la imagen del producto y definir:

| Variable interna | Qué extraer |
|---|---|
| COLOR_PRIMARIO | Color más dominante del frasco o su etiqueta |
| COLOR_SECUNDARIO | Color de acento o contraste del diseño del frasco |
| COLOR_OSCURO | Versión oscurecida del color primario para fondos y barras |

REGLAS DE SEGURIDAD:
- Si el color primario es muy claro o pastel → usar versión oscurecida al 60% para fondos
- Si el color primario es blanco o casi blanco → usar el color de la tapa o banda de etiqueta (ej: NeuraZenx → amarillo; NAD+ → azul/negro; Cúrcuma → naranja)
- Los fondos oscuros de IMAGEN 2 e IMAGEN 3 nunca deben ser pasteles ni colores claros
- **El acento estructural de las 4 piezas = [COLOR_ACENTO_PRODUCTO] (color del frasco).** Aplica a números estadísticos, triángulos, bandas, separadores, checkmarks. El verde lima #caec55 NO es el acento por defecto: solo se usa si el producto es verde/detox/salud y el lima lo complementa. Ver REGLA MAESTRA DE COLOR arriba.
- El logo sanarte® mantiene sus letras #117200 + contorno #caec55 SOLO si esos verdes armonizan con el producto; si chocan, parametrizar el logo a la identidad de la fanpage (ver PARAMETRIZACIÓN DE MARCA). El logo nunca es el color más llamativo de la pieza.

> **REGLA DE ZONAS BLANCAS (cohesión sin perder legibilidad — aplica a IMAGEN 2 ZONA 3, IMAGEN 3 FAQ/certificaciones, IMAGEN 4 cuerpo comparativo):** las zonas de texto denso pequeño se mantienen claras para que el público (a veces 50-70 años) lea sin esfuerzo (Clase 22: legibilidad ante todo). PERO el blanco puro #FFFFFF se siente desconectado de una campaña de color. Sustituir el #FFFFFF plano por un **blanco roto teñido hacia el color del producto (tinte ≤5%)** — sigue siendo prácticamente blanco, legible, pero hace que la pieza pertenezca a la familia visual. NUNCA saturar esas zonas con color fuerte (eso sí mata la legibilidad del texto pequeño). Legibilidad primero, cohesión segundo.

Aplicar los colores extraídos así:
- [COLOR_DEGRADADO_ENCABEZADO] → degradado de COLOR_PRIMARIO a COLOR_SECUNDARIO
- [COLOR_BOTON_ENCABEZADO] → COLOR_PRIMARIO
- [COLOR_BANDA_ETIQUETA] → COLOR_OSCURO
- [COLOR_CIRCULOS_BENEFICIOS] → COLOR_PRIMARIO
- [COLOR_BARRA_INFERIOR] → COLOR_OSCURO
- [COLOR_ETIQUETA_FRASCO_DOCTORA] → COLOR_PRIMARIO (descripción del color para el prompt)
- [COLOR_FONDO_OSCURO] → COLOR_OSCURO si pasa el test de legibilidad (texto blanco claramente legible sobre él); de lo contrario, usar #0a1628 de respaldo. Se aplica en IMAGEN 2 (fondos ZONA 1 y ZONA 2) e IMAGEN 3 (degradado izquierdo).
- [COLOR_ACENTO_PRODUCTO] → COLOR_PRIMARIO del producto. Es el **acento estructural y visual dominante de las 4 piezas** (separadores, bordes, bullets, flechas, subtítulos, triángulos de alerta, bandas) **y también los 3 números estadísticos de IMAGEN 3.** Ya NO se usa #caec55 fijo para las estadísticas: los números van en [COLOR_ACENTO_PRODUCTO] (o en blanco con contorno del color del producto si el producto es claro). Esto hace que toda la pieza "se sienta" del producto.

Paleta por defecto de marca (sanarte® — ver PARAMETRIZACIÓN DE MARCA para adaptarla por fanpage):
- #117200 → verde letras logo sanarte® → variable: [COLOR_LOGO_MARCA] (adaptable si choca con el producto)
- #caec55 → lima neón → variable: [COLOR_ACENTO_MARCA]. Uso **restringido al contorno del logo** y solo si armoniza con el producto. NO es el acento de las estadísticas ni de los triángulos/bandas: eso lo cubre [COLOR_ACENTO_PRODUCTO]. En productos no-verdes, el lima desaparece de la pieza salvo (opcionalmente) el contorno del logo.
- #0a1628 → texto oscuro y fondos de respaldo
- #FFFFFF → blanco
- #6b7280 → gris descriptivo

---

## KIT TIPOGRÁFICO DE CAMPAÑA (una sola fuente, igual en anuncios + infografías + bot)

> **Por qué (Joaquín, Clase 22):** *"usar la MISMA fuente en los títulos de Meta, el flujo y la landing → se identifica como producto de marca, una secuencia."* La consistencia tipográfica es lo que hace que el cliente sienta que es **una sola marca** de punta a punta. Esto vale tanto o más que el color.

**REGLA DURA:** se fija **UNA familia tipográfica por PRODUCTO** (el "kit") y se usa **idéntica en las 4 infografías, en los ads de Meta (DOCTRINA/PLANTILLAS_ADS.md) y en cualquier landing de ese producto**. No cambiar de fuente entre piezas del mismo producto. Nunca mezclar más de 2 familias en una pieza; nunca serif en cuerpos pequeños (ilegible).

**¿Tipografía de quién? → DEL BRANDING DEL PRODUCTO.** Se extrae la **categoría tipográfica de la etiqueta/branding del frasco** y esa se usa en TODAS las piezas de ese producto. Motivo operativo: el operador lanza muchísimos ads/productos y no puede gestionar una tipografía distinta por fanpage — anclar la fuente al producto es más rápido, escalable y mantiene la coherencia de embudo (ad → bot → landing) donde de verdad importa: **dentro de la secuencia de un mismo producto** (principio de Clase 22 — "misma fuente = una sola marca/secuencia"). Se sacrifica a propósito la consistencia entre productos de una misma fanpage; el operador lo aceptó.

> ⚠️ **Caveat técnico (no negociable):** la IA NO reproduce la fuente con licencia exacta de la etiqueta — aproxima por **CATEGORÍA**. El objetivo es identificar la categoría correcta del frasco (sans geométrica / humanista / serif elegante / display condensada) y repetirla, no "clonar" el .ttf del fabricante.

**ORDEN DE DETECCIÓN (de mayor a menor prioridad):**
1. **Branding / etiqueta del producto** — la categoría tipográfica del frasco manda. Es la fuente del producto y se repite en todas sus piezas.
2. **Tus ads de referencia / campañas que ya funcionaron** (si el operador los pasa) — solo para afinar la categoría si la etiqueta es ambigua.
3. **Identidad de la fanpage asignada** (ETAPA-2) — respaldo si el frasco no da una categoría clara.
4. **Default validado:** sans-serif moderna (Inter/Poppins), bold en titulares.

**PASO WEB OPCIONAL (siguiente nivel):** si se quiere afinar, buscar en internet el logo/estilo de **la fanpage o de marcas de EE.UU. del nicho que facturan** (Clase 19: "mirar marcas de EE.UU. que facturan millones") e identificar su **categoría** tipográfica. ⚠️ Realismo: los generadores de IA NO reproducen una fuente con licencia exacta — aproximan por categoría. Por eso el objetivo es fijar la CATEGORÍA correcta y repetirla, no "clonar" un .ttf.

| Variable del kit | Qué define (se fija una vez por campaña) |
|---|---|
| [KIT_TIPO_LETRA] | Categoría única **del producto** (leída de su etiqueta/branding): sans-serif geométrica (Poppins/Montserrat) · sans-serif humanista (Inter/Open Sans) · serif elegante (solo belleza/lujo) · display/condensada (fitness/energía). Se fija una vez por producto y se repite en todas sus piezas. |
| [KIT_PESO_TITULOS] | Grosor de titulares: bold / extra-bold / black. |
| [KIT_ESTILO] | Sensación: clínico-limpio · premium-elegante · enérgico-deportivo · cálido-cercano. Calibrar a la fanpage (clínico → sans limpia; belleza → serif elegante en titulares; fitness → display de peso alto). |

> Cada prompt de infografía y cada prompt de ad debe nombrar la MISMA [KIT_TIPO_LETRA]. Al entregar una campaña, documentar en 1 línea cuál fue el kit elegido y de dónde salió (etiqueta del producto / ads de referencia / default).

---

## ANÁLISIS DE ADS DE REFERENCIA (cuando el operador los entrega)

Si el operador adjunta imágenes de anuncios de referencia (de la competencia o de campañas que ya funcionaron), analizarlos ANTES de rellenar las plantillas y extraer:
- Paleta de color real que usa la competencia en ese nicho (para diferenciarse o alinearse a propósito).
- Tipografía y jerarquía visual (qué se lee primero).
- Tipo de hook visual y elementos de prueba (sellos, antes/después, números).
- Qué NO hacen (huecos que la pieza puede aprovechar para destacar).

Estos hallazgos calibran la elección de colores, tipografía y composición — sin alterar la estructura fija de las 4 plantillas. Documentar en 3-4 líneas qué se tomó de los ads de referencia y por qué.

---

## PARAMETRIZACIÓN DE MARCA (LOGO Y COLOR DE ACENTO)

Las 4 plantillas nacieron con la marca **sanarte®** (logo verde #117200 + acento lima #caec55) como DEFAULT. Eso sigue siendo el valor por defecto y todas las menciones literales a "sanarte®", #117200 y #caec55 en las plantillas se interpretan como las variables de marca:

| Variable de marca | Default (sanarte®) | Cuándo cambiarla |
|---|---|---|
| [LOGO_MARCA] | "sanarte®" | Si la fanpage/nicho usa otra identidad de marca. |
| [COLOR_LOGO_MARCA] | #117200 (verde) | Adaptar al color de la identidad de la fanpage. |
| [COLOR_ACENTO_MARCA] | #caec55 (lima neón) | Cambiar cuando el lima choca con el nicho (ver regla abajo). |

REGLA DE COHERENCIA DE MARCA POR FANPAGE:
- El lima neón #caec55 funciona bien en nichos de salud/detox/metabolismo, pero CHOCA en belleza & piel, sueño/estrés y temas clínicos sensibles, donde se ve agresivo.
- Para esos nichos, sustituir [COLOR_ACENTO_MARCA] por un acento alineado a la identidad de la fanpage (ej. rosado suave para belleza, lavanda/azul calmo para sueño, azul clínico para metabolismo/virilidad), manteniendo el contraste y la legibilidad.
- El [COLOR_ACENTO_PRODUCTO] (extraído del frasco) y el [COLOR_ACENTO_MARCA] (identidad de marca) son distintos: el del producto da estructura; el de marca da reconocimiento. No confundirlos.
- Cualquiera que sea el acento de marca elegido, se aplica de forma consistente en las 4 plantillas de esa campaña.

> Nota estratégica: "sanarte®" es una marca propia. Para dropshipping puro puede mantenerse como sello de "tienda autorizada" (da confianza y combate imitaciones — ver IMAGEN 4), o parametrizarse por fanpage si se prefiere que cada nicho tenga su propia identidad visual. Ambas vías son válidas; esta parametrización deja la decisión abierta sin romper las plantillas.

---

---

## DÓNDE ESTÁ CADA PLANTILLA

Todo lo de arriba es el **motor compartido**: aplica a las seis imágenes y se lee siempre.
Las plantillas viven en dos archivos, para que cada etapa cargue solo lo que va a usar.

| Archivo | Qué lleva | Quién lo necesita |
|---|---|---|
| `DOCTRINA/PLANTILLAS_INFOGRAFIAS_FLUJO.md` | **IMAGEN 1** beneficios · **IMAGEN 2** transformación + ingredientes + modo de uso · **IMAGEN 3** confianza/contraentrega. Son las 3 que el bot envía como ELEMENTOS 4/5/6. | `etapa-4`, siempre |
| `DOCTRINA/PLANTILLAS_INFOGRAFIAS_OPCIONALES.md` | **IMAGEN 4** anti-imitación · **IMAGEN 5** reservada · **IMAGEN 6** recuperación de novedad. | `etapa-4`, solo si el operador las pide o para retargeting/escalado |

**Dos datos que otras etapas necesitan sin abrir esos archivos:**
- El acento de color de las cuatro infografías es el **color del producto** (REGLA MAESTRA DE
  COLOR, arriba). No forzar el verde lima si el producto no es verde.
- **IMAGEN 3 lleva el SELLO DE GARANTÍA** junto al contraentrega. Lo que se escriba en el flujo
  del bot tiene que ser coherente con eso.

`etapa-5` y `etapa-guardar-producto` se sirven con este archivo: no necesitan las plantillas.
