# PLANTILLAS INFOGRAFÍAS — SISTEMA VITALCOM GUATEMALA

## INSTRUCCIONES DE USO
Estas 4 plantillas son el sistema de infografías definitivo y validado.
El formato, estructura e instrucciones de cada plantilla son **FIJOS** — no modificar ni resumir.
Solo reemplazar los valores entre `[ ]` con los datos del producto actual.

> **⭐ ADAPTACIÓN POR ÁNGULO EN FASE 2 (regla operador, 08-jul):** cuando el bot es DEDICADO a un solo ángulo (FASE 2, escalado), las infografías del flujo se entregan como **prompts COMPLETOS ya adaptados al ángulo dedicado**, no como deltas ni instrucciones ("cambiá X"). Qué se adapta y qué NO:
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

> **Por qué:** una sola lectura de la imagen del frasco define la identidad visual de TODA la campaña — las 4 infografías Y los ads de Meta. Lo que hace que los ads del proveedor "conecten" no es un truco por pieza: es que todas nacen del mismo ADN visual del producto. Antes existían pasos sueltos (color por un lado, tipografía por otro) que se contradecían; esto los unifica. (Decisión del operador 2026-06-29.)

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
- Si el color primario es blanco o casi blanco → usar el color de la tapa o banda de etiqueta (ej: D3+K2 frasco blanco → tomar el dorado/amarillo de la etiqueta; NeuraZenx → amarillo; NAD+ → azul/negro; Cúrcuma → naranja)
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

**REGLA DURA:** se fija **UNA familia tipográfica por PRODUCTO** (el "kit") y se usa **idéntica en las 4 infografías, en los ads de Meta (PLANTILLAS_ADS.md) y en cualquier landing de ese producto**. No cambiar de fuente entre piezas del mismo producto. Nunca mezclar más de 2 familias en una pieza; nunca serif en cuerpos pequeños (ilegible).

**¿Tipografía de quién? → DEL BRANDING DEL PRODUCTO (decisión del operador, 2026-06-29).** Se extrae la **categoría tipográfica de la etiqueta/branding del frasco** y esa se usa en TODAS las piezas de ese producto. Motivo operativo: el operador lanza muchísimos ads/productos y no puede gestionar una tipografía distinta por fanpage — anclar la fuente al producto es más rápido, escalable y mantiene la coherencia de embudo (ad → bot → landing) donde de verdad importa: **dentro de la secuencia de un mismo producto** (principio de Clase 22 — "misma fuente = una sola marca/secuencia"). Se sacrifica a propósito la consistencia entre productos de una misma fanpage; el operador lo aceptó.

> ⚠️ **Caveat técnico (no negociable):** la IA NO reproduce la fuente con licencia exacta de la etiqueta — aproxima por **CATEGORÍA**. El objetivo es identificar la categoría correcta del frasco (sans geométrica / humanista / serif elegante / display condensada) y repetirla, no "clonar" el .ttf del fabricante.

**ORDEN DE DETECCIÓN (de mayor a menor prioridad):**
1. **Branding / etiqueta del producto** — la categoría tipográfica del frasco manda. Es la fuente del producto y se repite en todas sus piezas.
2. **Tus ads de referencia / campañas que ya funcionaron** (si el operador los pasa) — solo para afinar la categoría si la etiqueta es ambigua.
3. **Identidad de la fanpage asignada** (ETAPA-FANPAGE) — respaldo si el frasco no da una categoría clara.
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

## IMAGEN 1 — BENEFICIOS (6–10, FLEXIBLE)

> ## ⭐ DOCTRINA DE LA IMAGEN DE BENEFICIOS (LEER ANTES DE GENERAR)
> Esta pieza vive DENTRO del flujo del bot (Info 1), después del punto de dolor. **No es el anuncio frío de Meta** — la persona ya está enganchada. Por eso aguanta densidad: Clase 7 (Joaquín) confirma que poner "la imagen con 10-30 beneficios después del punto de dolor sube la conversión de una". Es el momento "vitrina" de carga de valor antes del precio (Clase 1).
>
> **PERO el límite lo pone el UMBRAL COGNITIVO (Clase 22):** *"si saturás UNA imagen con todo, la persona NO la procesa."* La saturación NO viene del número de beneficios — viene de (a) descripciones largas en cada punto, (b) todos los textos del mismo tamaño sin jerarquía, y (c) fondo plano que no deja respirar al producto. Una pieza con 10 beneficios bien jerarquizados se procesa; una con 5 mal jerarquizados, no.
>
> **REGLA DE CONTEO — flexible, no fijo en 10:** usar **entre 6 y 10 beneficios REALES y diferenciados** (default 8-10 si el producto los tiene). **PROHIBIDO rellenar hasta 10 con beneficios débiles, repetidos o genéricos** ("100% vegetariano", "fórmula segura") solo para llegar al número — ese relleno es lo que satura. Si el producto solo tiene 5-6 beneficios fuertes (ej. creatina, magnesio), hacer 5-6 con más aire, como hacen los ads del proveedor. La cantidad sigue a la sustancia, no al revés.
>
> **REGLA DE FONDO (corrección crítica vs versión vieja):** el fondo NUNCA es blanco plano. Es un **fondo de color derivado del producto** ([COLOR_DEGRADADO_PRODUCTO]): degradado o color sólido tomado del frasco/etiqueta, igual que los ads del proveedor que "conectan" (Intimate Rose morado, Magnesium azul, Height dorado-oscuro). Clase 14: *"una mala paleta de colores no detiene el scroll"*; PDF Prompt Maestro lista "fondo degradado moderno" / "oscuro de lujo" — nunca blanco clínico. La micro-textura va ENCIMA de ese fondo de color, no lo reemplaza.
>
> **REGLA DE PRODUCTO HÉROE (Clase 14):** *"la imagen del producto debe ser GRANDE y protagonista"*. Frasco centrado, grande, con iluminación dramática (glow/halo del color del producto), reflejo o pódium sutil. Es lo primero que rompe el scroll, por encima de los beneficios.
> **REGLA DE COMBO (2x1 / 4x2 — operador 08-jul):** si el producto se vende en combo (no por unidad), el héroe muestra **DOS frascos idénticos** juntos (o cuatro para 4x2) + un **banner MODERADO, no muy grande, que diga "MEGA OFERTA 2X1"** (fondo rojo/color del producto, texto blanco bold). Un solo frasco solo si el producto se vende por unidad suelta. Aplica a las piezas con producto héroe (IMAGEN 1, oferta). Nusava B12 = SIEMPRE 2x1 → 2 frascos + banner.
>
> **Test antes de generar:** (1) ¿el fondo es del color del producto, no blanco? (2) ¿el frasco domina la pieza? (3) ¿los títulos de beneficio se leen, sin que las descripciones saturen? (4) ¿cada beneficio es real, no relleno? (5) ¿los íconos de beneficio son ilustrados A COLOR (no de línea gris)? Si alguna falla → corregir.

> ## ⭐ REGLA DE ESTILO DE ÍCONOS DE BENEFICIO — ILUSTRACIÓN 3D DIE-CUT + NÚMERO (obligatoria en IMAGEN 1)
> Cada beneficio se refuerza con DOS elementos juntos: (1) su **NÚMERO** en círculo `[COLOR_CIRCULOS_BENEFICIOS]`, y (2) una **ILUSTRACIÓN 3D DIE-CUT A COLOR** — el `[BENEFICIO_N_ICONO]` se describe literal como **"Ilustración 3D die-cut de [concepto]"** (ej. "Ilustración 3D die-cut de un cerebro rosado", "…de una neurona azul", "…de un rayo amarillo"): objeto ilustrado a color, glossy/semi-3D, con recorte die-cut — NO un ícono de línea plano ni monocromático gris. **⚠️ La frase "Ilustración 3D die-cut de…" rinde mucho mejor que la palabra "sticker" (validado por el operador 08-jul).** **TAMAÑO MODERADO: hacerlas un poco MÁS PEQUEÑAS de lo que la IA genera por defecto** (salen grandes) — que no le quiten protagonismo al frasco ni saturen. Estilo/tamaño uniforme entre todas. Número + ilustración van pegados, uno por beneficio.
> - **Color por concepto, no por producto:** cada ícono lleva el color natural de lo que representa (energía → rayo amarillo/dorado · sangre/circulación → rojo · nervios/mente → rosado o azul · protección → escudo azul · digestión → verde · sueño → morado/índigo · vegano → verde hoja). Los íconos son la **única capa de la pieza que sí es multicolor** — así rompen el escaneo y se leen de un vistazo.
> - **Esto NO contradice la REGLA MAESTRA DE COLOR:** la estructura (fondo, títulos, círculos numerados `[COLOR_CIRCULOS_BENEFICIOS]`, bandas, pie) sigue en `[COLOR_ACENTO_PRODUCTO]`. El color del producto manda en la estructura; los íconos aportan el toque multicolor encima, contenidos en su badge/círculo.
> - **Estilo consistente entre los N íconos:** todos del mismo grosor, misma familia visual (flat con relleno suave o semi-3D ligero), tamaño uniforme. Nunca mezclar íconos de línea con íconos rellenos en la misma pieza.
> - **Legibles a tamaño chico en celular:** símbolo simple y reconocible en <1 seg, sin detalle microscópico.

### VERSIÓN RÁPIDA (usar cuando se necesita brevedad)

FORMATO: 4:5 (1080×1350) por defecto — coherente con el resto del flujo del bot (ELEMENTO 4 de ETAPA-5). Usar 2:3 (1080×1620) solo si los beneficios necesitan más alto. **FONDO DE COLOR DEL PRODUCTO ([COLOR_DEGRADADO_PRODUCTO]) — NUNCA blanco plano.** Degradado o color sólido tomado del frasco/etiqueta (como los ads del proveedor que conectan). Estética premium de bienestar, no clínica-plana.

ENCABEZADO (12%): TÍTULO PRINCIPAL grande y en bold, color [COLOR_BOTON_ENCABEZADO] (o degradado [COLOR_DEGRADADO_ENCABEZADO]): "[HEADLINE_BENEFICIO]" — el dolor/deseo del ángulo, congruente con el anuncio de Meta. Encima o al lado, en etiqueta pequeña: "[KICKER_BENEFICIOS]" (ej: "[N] BENEFICIOS"). Botón [COLOR_BOTON_ENCABEZADO] con texto blanco: "[NOMBRE_PRODUCTO]". [DECORACION_ENCABEZADO] sutiles. NUNCA poner "BENEFICIOS" como título principal.

CENTRO — PRODUCTO HÉROE: Frasco ultra-realista de "[NOMBRE_PRODUCTO]", **grande y protagonista**, con iluminación dramática (glow/halo del color del producto) y reflejo o pódium sutil. Base rodeada de ingredientes naturales compactos: [INGREDIENTES_BASE_BOTELLA].

LOS [N] BENEFICIOS (6–10 reales, sin relleno — Círculos numerados alrededor). **Cada beneficio = NÚMERO en su círculo + una ILUSTRACIÓN 3D DIE-CUT a color (tamaño moderado, un poco más pequeña de lo que sale por defecto)** descrita como "Ilustración 3D die-cut de [concepto]" (cerebro rosado, neurona azul, rayo amarillo, gota de sangre roja…), estilo/tamaño uniforme entre todas (ver REGLA DE ESTILO DE ÍCONOS — ILUSTRACIÓN 3D DIE-CUT + NÚMERO):
Columna Izquierda:
[[BENEFICIO_1_ICONO]] [BENEFICIO_1_TITULO]. [BENEFICIO_1_DESC]
[[BENEFICIO_2_ICONO]] [BENEFICIO_2_TITULO]. [BENEFICIO_2_DESC]
[[BENEFICIO_3_ICONO]] [BENEFICIO_3_TITULO]. [BENEFICIO_3_DESC]
[[BENEFICIO_4_ICONO]] [BENEFICIO_4_TITULO]. [BENEFICIO_4_DESC]
[[BENEFICIO_5_ICONO]] [BENEFICIO_5_TITULO]. [BENEFICIO_5_DESC]

Columna Derecha (resto, hasta completar N):
6. [[BENEFICIO_6_ICONO]] [BENEFICIO_6_TITULO].
7. [[BENEFICIO_7_ICONO]] [BENEFICIO_7_TITULO]. [BENEFICIO_7_DESC]
8. [[BENEFICIO_8_ICONO]] [BENEFICIO_8_TITULO]. [BENEFICIO_8_DESC]
9. [[BENEFICIO_9_ICONO]] [BENEFICIO_9_TITULO].
10. [[BENEFICIO_10_ICONO]] [BENEFICIO_10_TITULO].

PIE DE PÁGINA: Logotipo "sanarte®" (letras #117200, contorno #caec55). Barra [COLOR_BARRA_INFERIOR] abajo. Izquierda: [Escudo] "[FOOTER_TEXTO_IZQ]". Derecha: [[ICONO_FOOTER_DER]] "FÓRMULA SEGURA Y DE ALTA CALIDAD". (SIN SELLOS OFICIALES).

---

### VERSIÓN COMPLETA (usar por defecto — mayor control y calidad)

Un póster de infografía de producto vertical de alta resolución y calidad profesional, recreando fielmente el diseño, texto y elementos de la imagen de referencia, optimizado para una lectura clara y sin saturación.

Estilo y Layout: Un diseño de póster premium y profesional, con estética de bienestar de marca (NO clínica-plana), renderizado con alto nivel de detalle y fidelidad. El layout se organiza en una columna central con un PRODUCTO HÉROE grande y protagonista y diagramas numerados alrededor con aire/espacio entre ellos.

**FONDO (regla crítica — corrige la versión vieja de fondo blanco):** el fondo del póster es un **degradado o color sólido derivado del producto** [COLOR_DEGRADADO_PRODUCTO] (tomado del frasco/etiqueta), al estilo de los ads de proveedor que conectan emocionalmente (morado para fórmula femenina, azul para magnesio, dorado-oscuro para crecimiento, naranja para energía). NUNCA fondo blanco plano ni gris clínico. Sobre ese fondo de color, y SOLO encima de él, se añade una micro-textura abstracta contextual con opacidad de 2% a 5% máximo, seleccionada según la categoría del producto:

- Pérdida de peso / metabolismo:
  Trama diagonal de puntos muy finos, dispersos uniformemente. Apenas perceptible.

- Piel / colágeno / belleza / cabello:
  Curvas horizontales suaves y continuas, como capas de agua quieta. Sin contraste.

- Sueño / relajación / magnesio / estrés:
  Gradiente radial muy suave desde el centro hacia los bordes. Centro más claro,
  bordes levemente más oscuros. Como luz de luna difusa.

- Energía / vitalidad / rendimiento:
  Líneas diagonales muy finas convergiendo desde la esquina superior derecha.
  Como rayos de luz lejanos. Totalmente difuminadas.

- Detox / digestión / hígado:
  Formas circulares difusas muy pequeñas dispersas, como células o burbujas a escala
  microscópica. Sin definición de borde.

- Articulaciones / huesos / dolor / recuperación:
  Patrón hexagonal geométrico muy tenue, tipo estructura molecular. Sin relleno,
  solo contorno de línea finísima.

- Cardiovascular / corazón / presión:
  Ondas horizontales suaves y equidistantes, como un ECG extremadamente diluido.

- Fertilidad / hormonal / femenino:
  Gradiente suave radial con tono cálido muy sutil (rosado o dorado pálido) en el
  centro, completamente transparente hacia los bordes.

- Concentración / memoria / mental:
  Red de líneas punteadas muy finas tipo conexión neuronal. Nodos apenas visibles.
  Opacidad máxima 3%.

REGLA ABSOLUTA: Si la textura es visible a primera vista, es demasiado intensa.
Reducir opacidad hasta que desaparezca del primer plano visual.
La textura existe para enriquecer, no para decorar.

Sección Superior (Encabezado): El encabezado es compacto pero su TÍTULO domina. Estructura de jerarquía (título impactante, no genérico; la gente escanea, lee títulos grandes y palabras resaltadas):
1. **TÍTULO PRINCIPAL** (lo más grande y llamativo del encabezado, en bold, color [COLOR_BOTON_ENCABEZADO] o degradado [COLOR_DEGRADADO_ENCABEZADO]): "[HEADLINE_BENEFICIO]" — el dolor/deseo del ángulo congruente con el anuncio de Meta (ej: "TU APOYO DIARIO PARA UNA VIDA MÁS SALUDABLE", "POTENCIA TU ENERGÍA CADA DÍA"). **PROHIBIDO usar "10 BENEFICIOS" o "BENEFICIOS" como título principal** — eso es genérico y no detiene el escaneo.
2. **KICKER pequeño** encima o al lado del título, en texto chico: "[KICKER_BENEFICIOS]" (ej: "10 BENEFICIOS", "FÓRMULA AVANZADA"). Es secundario, nunca compite con el título.
3. **Botón [COLOR_BOTON_ENCABEZADO]** delgado con texto blanco pequeño: "[NOMBRE_PRODUCTO]".
El bloque de encabezado no ocupa más del ~15% de la altura, pero el TÍTULO debe leerse desde lejos. [DECORACION_ENCABEZADO] pequeñas y discretas decoran sin saturar. El estilo de referencia es el de los ads winner del operador (D3+K2, Cúrcuma, NAD+, NeuraZenx): título grande de promesa/dolor + beneficios con íconos alrededor del frasco.

Elemento Central (Botella) — PRODUCTO HÉROE: Una botella ultra-realista de "[NOMBRE_PRODUCTO]" se sitúa en el centro como protagonista absoluto: **grande y dominante** (Clase 14: "el producto debe ser grande y protagonista; si lo ponés chiquito se ve insignificante"), con iluminación dramática — glow/halo del color del producto, reflejo o pódium sutil que lo hace resaltar contra el fondo de color. Es lo primero que rompe el scroll. Debe quedar aire entre el frasco y los beneficios laterales para que la pieza respire (umbral cognitivo), pero el frasco nunca se achica para ceder ese espacio. La etiqueta de la botella debe ser idéntica, incluyendo la banda [COLOR_BANDA_ETIQUETA] inferior con el texto blanco "[NOMBRE_PRODUCTO]" y "SUPLEMENTO ALIMENTICIO | [CAPSULAS_CANTIDAD] CAPSULAS" en dorado. En la etiqueta de la botella debe figurar la lista de beneficios en español ([BENEFICIOS_ETIQUETA]) en texto pequeño. Un sello dorado en la etiqueta dice "[MILIGRAMOS] MG". Una etiqueta colgante negra con texto dorado "[MILIGRAMOS] MG" cuelga visiblemente del tapón en el lado izquierdo.

Base de la Botella: Dispuesto alrededor de la base de la botella hay una disposición compacta de ingredientes naturales: [INGREDIENTES_BASE_BOTELLA].

> **DISPOSICIÓN DE LOS BENEFICIOS (variable según cantidad — esto SÍ cambia por producto):**
> - **6-10 beneficios → DOS COLUMNAS que FLANQUEAN el frasco** (alrededor: izquierda + derecha, frasco al centro). Es el layout winner de referencia (D3+K2, etc.) y el default.
> - **3-5 beneficios → UNA columna a un lado + tira de íconos de confianza abajo** (estilo proveedor: Magnesium, Creatina). Menos puntos piden más aire, no rellenar para flanquear.
> - **Nunca apilar los beneficios DEBAJO del frasco en bloque** salvo formato muy vertical (2:3) con pocos puntos. El frasco siempre conserva el centro visual.
> Regla: la disposición sigue la CANTIDAD de beneficios reales; el frasco-héroe nunca cede el centro.

Diagramas de Beneficios Numerados (Círculos que rodean la botella): entre **6 y 10 beneficios REALES y diferenciados** (default 8-10 si el producto los tiene; NUNCA relleno genérico para llegar a 10 — el relleno es lo que satura, no el número). Puntos numerados circulares con puntos [COLOR_CIRCULOS_BENEFICIOS] y números blancos, dispuestos en dos columnas con buen espaciado/aire entre ellos. **Cada beneficio lleva un ícono ILUSTRADO A COLOR (estilo flat/moderno multicolor, NO línea gris monocromática), cada uno pintado en el color natural de su concepto (rayo amarillo = energía, corazón rojo = sangre, cerebro rosado = memoria, escudo azul = protección, hoja verde = vegano, etc.), con estilo y grosor uniformes entre todos los íconos.** Los íconos son la única capa multicolor de la pieza; la estructura (círculos, títulos, bandas) sigue en el color del producto. **Jerarquía obligatoria (Clase 14):** el título del beneficio (en MAYÚSCULAS) domina en tamaño y peso; la descripción va en tipografía notablemente más pequeña, delgada y CORTA (máx 1 línea breve). Para mantener el umbral cognitivo bajo, en aproximadamente la mitad de los puntos basta el ícono + título sin descripción (como los ads del proveedor). Todo texto legible en celular (≥24 pts).

Columna Izquierda (1-5):

[BENEFICIO_1_ICONO]. Título: "[BENEFICIO_1_TITULO]". Descripción (letra más pequeña): "[BENEFICIO_1_DESC]"

[BENEFICIO_2_ICONO]. Título: "[BENEFICIO_2_TITULO]". Descripción (letra más pequeña): "[BENEFICIO_2_DESC]"

[BENEFICIO_3_ICONO]. Título: "[BENEFICIO_3_TITULO]". Descripción (letra más pequeña): "[BENEFICIO_3_DESC]"

[BENEFICIO_4_ICONO]. Título: "[BENEFICIO_4_TITULO]". Descripción (letra más pequeña): "[BENEFICIO_4_DESC]"

[BENEFICIO_5_ICONO]. Título: "[BENEFICIO_5_TITULO]". Descripción (letra más pequeña): "[BENEFICIO_5_DESC]"

Columna Derecha (6-10):

[BENEFICIO_6_ICONO]. Título: "[BENEFICIO_6_TITULO]". Descripción (letra más pequeña): "[BENEFICIO_6_DESC]"

[BENEFICIO_7_ICONO]. Título: "[BENEFICIO_7_TITULO]". Descripción (letra más pequeña): "[BENEFICIO_7_DESC]"

[BENEFICIO_8_ICONO]. Título: "[BENEFICIO_8_TITULO]". Descripción (letra más pequeña): "[BENEFICIO_8_DESC]"

[BENEFICIO_9_ICONO]. Título: "[BENEFICIO_9_TITULO]". Descripción (letra más pequeña): "[BENEFICIO_9_DESC]"

[BENEFICIO_10_ICONO]. Título: "[BENEFICIO_10_TITULO]". Descripción (letra más pequeña): "[BENEFICIO_10_DESC]"

Abajo del producto: pon mi logotipo "sanarte®" con las letras color #117200 y el contorno de las mismas en color #caec55. que no sea muy grande

Sección Inferior (Pie de Página): Una barra horizontal más pequeña y estrecha de color [COLOR_BARRA_INFERIOR]. En el lado izquierdo: Un escudo con una marca de verificación. Texto: "[FOOTER_TEXTO_IZQ]". En el lado derecho: Un icono de [ICONO_FOOTER_DER]. Texto: "FÓRMULA SEGURA Y DE ALTA CALIDAD".

TODO EN ESPAÑOL

---

## IMAGEN 2 — PRUEBA DE TRANSFORMACIÓN (evidencia/reseña/UGC/momento) + INGREDIENTES + MODO DE USO

Un póster de infografía de producto vertical, alta resolución, calidad profesional, estilo médico-wellness premium. **Hereda el PASO 0 (color, [KIT_TIPO_LETRA] del producto, render del frasco).** Fondo base blanco roto teñido ≤5% hacia el color del producto (no #FFFFFF plano; ver REGLA DE ZONAS BLANCAS). Las zonas hero (ANTES/DESPUÉS, ingredientes) van en oscuro del producto. Todo el texto en español.

> **REGLA DE UMBRAL COGNITIVO (Clase 22 Joaquín — obligatoria en esta pieza):** esta imagen carga 3 ideas (antes/después, ingredientes, modo de uso) y es la más propensa a saturarse. "Si saturás una imagen con todo, la persona NO la procesa." Por eso: (1) cada zona respira, separada con aire en blanco; (2) **máximo 4-6 ingredientes principales** (NO listar 10-15 en grilla diminuta), 1 línea por ingrediente; (3) **texto legible a ~24pt en celular** — nada de letra microscópica que "la gente no lee", recordando que parte del público es 50-70 años; (4) si el producto tiene muchos ingredientes, mostrar solo los protagonistas del ángulo y mencionar "y más" — la lista completa va en el catálogo/audio, no saturando la imagen.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ZONA 1 — ANTES / DESPUÉS (50% superior del lienzo)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Fondo de esta zona: degradado muy suave de [COLOR_FONDO_OSCURO] a negro puro. Ocupa exactamente la mitad superior del póster.

HEADLINE SUPERIOR:
Texto bold uppercase blanco, tamaño grande, centrado, con una línea delgada de 2px color [COLOR_ACENTO_PRODUCTO] debajo como separador:
"RESULTADOS REALES EN [DIAS_RESULTADO] DÍAS"

> **REGLA DE FRAMING TEMPORAL (Joaquín — análisis del flujo de glúteos: la progresión convierte más que un solo antes/después). Elegir según el producto, NO forzar:**
> - **Progresión por SEMANAS (Semana 1 → 2 → 3 → 4)** cuando la transformación es gradual y visible: peso/medidas, piel/acné, cabello, energía, glúteos/cuerpo. Es la versión preferida del mentor: mostrar la evolución, no solo dos fotos.
> - **Día 1 / Día N** para mejoras de bienestar diario (dolor/movilidad, sueño, ánimo).
> - **Hito (Mes)** para procesos largos: fertilidad ("Mes 1 negativa → Mes 4 positiva"), evidencia clínica ("análisis → 3 meses después").
> - **Sin progresión física** cuando el producto no tiene un cambio corporal visible (absorción, ánimo puro): usar momentos emocionales/situacionales en vez de antes/después corporal.
> Cumplir compliance Andrómeda: la progresión semanal es válida; lo prohibido es el antes/después corporal bilateral en el ANUNCIO (no en esta infografía del bot).

> ## ⭐ REGLA DE CREDIBILIDAD (LEER ANTES DE ELEGIR EL ANTES/DESPUÉS)
> **El error #1 de esta zona es generar por IA "la misma persona" dos veces — sale con cara distinta, plástica, y se siente FALSA.** Los mentores son explícitos: *"las fotos de testimonios deben ser REALES, no usar imágenes de IA que se vean artificiales — no traten de tontos a los clientes"* (Clase 1). Y *"la reseña cuenta el antes/después con tiempo: 'antes me sentía así, desde hace una semana ya no'"* (Clase 10). **Por eso el antes/después NO es por defecto una persona posada: se elige el formato MÁS CREÍBLE según lo que el producto cambia.** El criterio rector: *¿qué prueba se vería real aunque la genere IA?* — un objeto/artefacto siempre se ve más real que un rostro repetido.
>
> **ELEGIR FORMATO POR TIPO DE SOLUCIÓN (en este orden de preferencia):**
>
> **FORMATO A — EVIDENCIA / ARTEFACTO (preferido siempre que exista un objeto medible).** Mostrar el OBJETO antes/después, **sin la persona** — así no hay rostro repetido que delate la IA. Ej: prueba de embarazo negativa → positiva (sola, sobre el lavamanos); resultado de laboratorio fuera de rango → normalizado; número en la pesa; lectura de glucómetro; foto macro de pies/uñas/cabello. *Este es el caso de la prueba de embarazo: la prueba sola se ve más real que la chica.*
>
> **FORMATO B — RESEÑA CON TIEMPO (preferido cuando el cambio es INVISIBLE: energía, ánimo, sueño, absorción, nervios, concentración).** Una o dos tarjetas estilo reseña/captura de WhatsApp que narran la transformación con tiempo. 2 reseñas por imagen (truco de Canva, Clase 10). Ortografía natural humana (no perfecta), nombre + inicial, fecha relativa ("hace 3 semanas"). No inventar capturas que parezcan oficiales de WhatsApp si pueden confundirse con las reales del operador — estilo "reseña de cliente".
>
> **FORMATO C — UGC CANDID (solo cuando el cambio es genuinamente visible y fotografiable: piel/acné, cabello, cuerpo/medidas).** Foto selfie real estilo cámara frontal de teléfono, grano natural, luz de baño, sin filtro. Aun así, para evitar el efecto-IA: preferir UNA foto auténtica + reseña, en vez de dos fotos posadas de la "misma" persona generada.
>
> **FORMATO D — MOMENTO SITUACIONAL (cuando no hay artefacto ni cambio corporal).** Dos momentos del día/situación que cuentan la historia sin pretender ser la misma persona "transformada": reloj 2:47 AM despierto → 6:45 AM descansada; mesa de noche con pastillas regadas → ordenada.
>
> **REGLA DURA:** si dudás entre persona-posada y evidencia/reseña → siempre evidencia/reseña. Nunca dos fotos IA de la misma cara que se vean artificiales.
>
> **OJO — separar dos cosas:** esta zona de IMAGEN 2 es una PRUEBA visual dentro de la pieza informativa. Los **TESTIMONIOS reales** (capturas de WhatsApp con foto del producto recibido, Clase 1) son un elemento APARTE del flujo del bot y los provee el operador de clientes reales — esos NUNCA se generan con IA.

BLOQUE PRUEBA DE TRANSFORMACIÓN — SELECCIONAR ARQUETIPO + FORMATO SEGÚN PRODUCTO:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TABLA DE SELECCIÓN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

| Tipo de producto | Arquetipo | Formato de credibilidad recomendado |
|---|---|---|
| Pérdida de peso / quema grasa / medidas | ARQUETIPO 1 | C (UGC candid) o A (número en la pesa) |
| Acné / piel / manchas / cabello | ARQUETIPO 2 | C (UGC candid) — cambio visible real |
| Fertilidad / regulación hormonal | ARQUETIPO 3 | **A (la prueba sola, sin la persona)** |
| Dolor articular / espalda / movilidad / energía | ARQUETIPO 4 | B (reseña con tiempo) o D (momento) |
| Magnesio / vitaminas / colesterol / glucosa / huesos | ARQUETIPO 5 | **A (laboratorio/glucómetro)** o B (reseña) |
| Sueño / insomnio / estrés / ansiedad / concentración | ARQUETIPO 6 | D (momento situacional) o B (reseña) |

> El arquetipo da el CONTEXTO (qué dolor); el formato da la CREDIBILIDAD (cómo se muestra sin verse falso). Cuando el formato recomendado es A o D, **no se renderiza una persona posada dos veces** — se muestra el artefacto o el momento. El formato C (persona) solo donde el cambio es visible y fotografiable de verdad.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ARQUETIPO 1 — CORPORAL VISIBLE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[EXPRESION_FISICA_ANTES]:
Mujer latina real en sus 30s, contextura con sobrepeso notorio, de pie frente al espejo
de baño. Camiseta ajustada de color claro. Se ve papada pronunciada, brazos con piel
caída, abdomen marcado bajo la tela. Expresión neutra-cansada. Luz de baño amarillenta,
grano de cámara frontal de teléfono.

[EXPRESION_FISICA_DESPUES]:
La misma mujer, mismo espejo, misma camiseta. Notablemente más delgada: papada reducida,
brazos más definidos, abdomen más plano. Sonrisa genuina, postura más erguida. La
diferencia es humana y real, no de revista ni retocada.

[ETIQUETA_ANTES]: DÍA 1 · CUERPO INFLADO Y SIN ENERGÍA
[ETIQUETA_DESPUES]: DÍA 30 · MENOS KILOS, MÁS CONFIANZA

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ARQUETIPO 2 — DERMATOLÓGICO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[EXPRESION_FISICA_ANTES]:
Primer plano selfie de cara de mujer latina real en sus 20s-30s, sosteniendo el teléfono
frente al espejo del baño. Sin maquillaje. Granitos inflamados visibles en frente, mejillas
y mentón. Piel con apariencia grasa y rojiza. Luz de baño directa, sin filtro. Expresión
incómoda, ligeramente avergonzada.

[EXPRESION_FISICA_DESPUES]:
La misma mujer, mismo ángulo, mismo espejo. Sin maquillaje. Piel notablemente más limpia:
granitos casi inexistentes, tono más parejo, menos rojez. No es piel perfecta de modelo —
es piel real mejorada. Sonrisa relajada y genuina.

[ETIQUETA_ANTES]: DÍA 1 · PIEL INFLAMADA Y GRANITOS
[ETIQUETA_DESPUES]: DÍA 45 · PIEL LIMPIA Y UNIFORME

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ARQUETIPO 3 — HITO VITAL (FERTILIDAD)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

VARIANTE A — FORMATO A (EVIDENCIA, recomendada por defecto — la más creíble):
Mostrar SOLO la prueba de embarazo, sin la persona (evita el rostro repetido que delata la IA).

[ANTES]:
Primer plano de una prueba de embarazo con resultado NEGATIVO (una sola línea), apoyada sobre
el borde del lavamanos de un baño doméstico real. Luz natural, grano de cámara de teléfono.
Etiqueta de fecha pequeña sobre la foto.

[DESPUÉS]:
Primer plano de una prueba de embarazo con resultado POSITIVO (dos líneas claras), en el mismo
lavamanos, misma luz. Junto a ella, un detalle cálido opcional (un par de patucos de bebé o
una nota escrita a mano "¡por fin!"). Auténtico, no de stock.

[ETIQUETA_ANTES]: MES 1 · PRUEBA NEGATIVA
[ETIQUETA_DESPUES]: MES 4 · PRUEBA POSITIVA

VARIANTE B — FORMATO C (con persona) — usar solo si el producto se enfoca en vivir el embarazo:

[EXPRESION_FISICA_ANTES]:
Mujer latina real en sus 30s, de pie frente al espejo de baño, vista de perfil, abdomen
plano. Expresión de esperanza contenida. Ropa casual ajustada.

[EXPRESION_FISICA_DESPUES]:
La misma mujer, mismo espejo, vista de perfil. Pancita de embarazo avanzado (5-7 meses)
visible. Ambas manos sostienen suavemente el vientre por debajo. Sonrisa genuina y cálida.

[ETIQUETA_ANTES]: ANTES · BUSCANDO MI BEBÉ
[ETIQUETA_DESPUES]: MES 6 · MI MAYOR LOGRO

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ARQUETIPO 4 — CALIDAD DE VIDA / DOLOR / MOVILIDAD
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[EXPRESION_FISICA_ANTES]:
Mujer latina real en sus 40s-50s, sentada al borde de la cama, encorvada, con una mano
apoyada en rodilla o espalda baja. Ropa de casa. Cara con expresión de dolor contenido o
agotamiento real. Habitación doméstica, luz suave de mañana. Sin posado — genuinamente
incómoda.

[EXPRESION_FISICA_DESPUES]:
La misma mujer, fotografiada en exterior — caminando en parque o sendero, con árboles o
naturaleza de fondo. Postura completamente erguida, paso firme. Camiseta casual similar.
Cara de bienestar genuino, sonrisa natural. Foto estilo acompañante o selfie de brazo
extendido — nada producido.

[ETIQUETA_ANTES]: DÍA 1 · DOLOR QUE ME DETIENE
[ETIQUETA_DESPUES]: DÍA 21 · ME MUEVO SIN DOLOR

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ARQUETIPO 5 — EVIDENCIA CLÍNICA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[EXPRESION_FISICA_ANTES]:
Manos sosteniendo un documento impreso de resultados de laboratorio clínico, enfocado a
primer plano. En el papel se ve un valor marcado en rojo (deficiencia de
[INGREDIENTE_PRINCIPAL]: valor fuera de rango normal). La persona está sentada en sala de
espera médica o escritorio de casa. Expresión preocupada pero calmada.

[EXPRESION_FISICA_DESPUES]:
La misma persona. Selfie de espejo o foto en exterior con buena luz. Cara de alivio y
satisfacción genuina. En una mano, visible pero no protagonista, sostiene un papel doblado
(nuevos resultados). Postura erguida, expresión tranquila y feliz.

[ETIQUETA_ANTES]: ANÁLISIS · DEFICIENCIA DETECTADA
[ETIQUETA_DESPUES]: 3 MESES DESPUÉS · NIVELES NORMALIZADOS

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ARQUETIPO 6 — EMOCIONAL / SUEÑO / MENTAL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[EXPRESION_FISICA_ANTES]:
Foto de noche en habitación oscura. Mujer latina real en sus 30s, acostada en cama pero
despierta, sosteniendo el teléfono sobre su cara. Luz azulada fría iluminando cara con
expresión de cansancio y tensión. Ojeras visibles. Hora en pantalla del teléfono: 2:47 AM.
Ropa de dormir. Todo auténtico y doméstico.

[EXPRESION_FISICA_DESPUES]:
La misma mujer, mismo cuarto, luz de día natural entrando por ventana. Acabando de
despertar — pelo desarreglado naturalmente, sentada en la cama. Ojos despejados, sin
ojeras, sonrisa tranquila. Misma ropa de dormir. Teléfono en mesa de noche mostrando
6:45 AM.

[ETIQUETA_ANTES]: 2:47 AM · SIN PODER DORMIR
[ETIQUETA_DESPUES]: 6:45 AM · DESCANSADA Y RENOVADA

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
INSTRUCCIÓN FINAL DE COMPOSICIÓN (según el FORMATO elegido)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

- **FORMATO A (evidencia):** dos fotos del ARTEFACTO antes/después (prueba, laboratorio, pesa, glucómetro), sin persona. Macro real, grano de teléfono.
- **FORMATO B (reseña):** una o dos tarjetas de reseña con tiempo (texto humano, ortografía natural, nombre + inicial, fecha relativa). Sin foto posada de IA.
- **FORMATO C (UGC candid):** dos fotografías lado a lado, MISMA persona, estilo selfie de cámara frontal — usar solo cuando el cambio sea visible y fotografiable de verdad (piel, cabello, cuerpo).
- **FORMATO D (momento):** dos momentos de la misma situación (reloj/escena), no dos retratos de "la misma persona transformada".

En todos los casos: grano natural de cámara de teléfono, sin filtros, sin retoque, sin actuación exagerada — altamente auténtico (Clase 1: "no traten de tontos a los clientes"). Si la pieza usa persona (Formato C), nunca dejar que el rostro se vea plástico/IA: ante la duda, cambiar a Formato A o B.

Separador central: línea vertical delgada 1px con el logo de la fanpage ([LOGO_MARCA]) pequeño centrado, en su color de marca.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ZONA 2 — INGREDIENTES PRINCIPALES (4-6 PROTAGONISTAS, NO TODA LA FÓRMULA)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Fondo: [COLOR_FONDO_OSCURO], borde superior e inferior de 1px color [COLOR_ACENTO_PRODUCTO].

TÍTULO DE SECCIÓN centrado:
Texto bold uppercase blanco, tamaño mediano:
"LO QUE HAY DENTRO IMPORTA"
Subtítulo regular pequeño, color [COLOR_ACENTO_PRODUCTO]:
"Ingredientes clave con función específica"

GRILLA DE 2 COLUMNAS — **MÁXIMO 4-6 ingredientes principales** (los protagonistas del ángulo, no la fórmula completa). Cada celda compacta y CON AIRE, fondo ligeramente más oscuro que [COLOR_FONDO_OSCURO] (oscurecer un 15%), border-radius suave, padding interno cómodo. Las dos columnas separadas por 12px. (Umbral cognitivo: NO meter 10-15 ingredientes en celdas diminutas — eso satura y la letra se vuelve ilegible.)

ESTRUCTURA DE CADA CELDA:
[Punto circular [COLOR_ACENTO_PRODUCTO] pequeño] [NOMBRE COMPONENTE bold blanco uppercase] → [función, texto regular legible (~24pt en celular) color #e5e7eb blanco, máximo 1 línea]

[LISTA_INGREDIENTES_ACTIVOS — solo los 4-6 principales]

NOTA DE CIERRE debajo de la grilla, centrado, texto italic pequeño color #6b7280:
"Fórmula sinérgica — cada ingrediente potencia al otro." (Si hay más ingredientes, agregar "+ [N] activos más" en vez de listarlos todos.)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ZONA 3 — MODO DE USO + CIERRE (25% inferior del lienzo)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Fondo blanco roto teñido ≤5% hacia el color del producto (no #FFFFFF plano; legibilidad del texto pequeño primero — ver REGLA DE ZONAS BLANCAS). Separado de la zona central por una línea delgada de 1px color [COLOR_ACENTO_PRODUCTO] ancho completo.

TÍTULO DE SECCIÓN:
Texto centrado bold uppercase, color #0a1628, tamaño mediano:
"MODO DE USO"

TRES ÍCONOS HORIZONTALES — en una sola fila centrada, espaciado igual entre los tres, con una flecha delgada color [COLOR_ACENTO_PRODUCTO] apuntando de izquierda a derecha entre ellos.

Ícono 1 — Cápsula 3D blanca realista, render limpio.
Texto: "[CAPSULAS_DOSIS]"
Subtexto: "dosis diaria"

Ícono 2 — Vaso de agua 3D.
Texto: "CON AGUA"
Subtexto: "un vaso lleno"

Ícono 3 — [ICONO_MOMENTO_3D].
Texto: "[MOMENTO_USO_TITULO]"
Subtexto: "[MOMENTO_USO_SUBTEXTO]"

BARRA INFERIOR:
"SIN EFECTOS SECUNDARIOS · 100% NATURAL · ABSORCIÓN CELULAR DIRECTA"

Logo "sanarte®" centrado debajo, pequeño, no protagonista.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
REGLAS GLOBALES DEL DISEÑO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

- Todo el texto en español
- Tipografía: [KIT_TIPO_LETRA] del producto (Paso 0 — misma fuente en las 4 infografías + ads + bot; default sans-serif Inter/Poppins)
- Sin emojis
- Paleta estricta: [COLOR_ACENTO_PRODUCTO] (acento dominante del producto), #117200 (letras logo solo si armoniza), #caec55 (opcional, solo contorno logo si armoniza), #0a1628, #FFFFFF, #6b7280. Ver REGLA MAESTRA DE COLOR.
- Resolución mínima 1080x1350px
- Estilo limpio, médico, premium

---

## IMAGEN 3 — CONFIANZA / CONTRAENTREGA + RESULTADOS

> **PROPÓSITO (ETAPA-5 ELEMENTO 6 + Clase 22 Joaquín):** esta es la imagen que ELIMINA el miedo a comprar online. El reductor de fricción #1 en Guatemala es **PAGÁS AL RECIBIR** — debe ser lo primero/más prominente, por encima de stats y FAQ. La autoridad (doctora) y las estadísticas refuerzan, pero el mensaje dominante es "no arriesgás tu dinero". (Joaquín: "la persona no arriesga el dinero, nosotros arriesgamos mandando el producto" — comunicarlo reduce la objeción que más mata ventas.)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PASO 1 — FOTO BASE (generar primero en IA de imágenes)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Candid iPhone photo, highly realistic UGC style. A real Latina woman doctor in her mid-30s, wearing a clean professional white lab coat, standing in a bright modern clinic with soft natural daylight coming from the left side.

COMPOSICIÓN CRÍTICA: La doctora está posicionada en el lado DERECHO del frame, ocupando desde el centro hasta el borde derecho. El lado IZQUIERDO del frame es espacio negativo limpio — sin objetos, sin personas, solo fondo de clínica desenfocado. Esta distribución es obligatoria para que el texto se superponga en el lado izquierdo sin tapar a la doctora.

La doctora sostiene con ambas manos, a la altura del pecho, un frasco blanco de suplemento con etiqueta [COLOR_ETIQUETA_FRASCO_DOCTORA] y detalles dorados. El frasco tiene un sello de plástico termoencogible transparente y brillante alrededor de la tapa — este detalle debe ser claramente visible.

La doctora mira directo a la cámara con una sonrisa genuina, empática y confiable. Poros naturales de piel visibles, leve grano de cámara iPhone, luz natural suave. Sin filtros. Sin fondos artificiales. Aspecto 100% auténtico y humano.

Aspect ratio 4:5. --style raw

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PASO 2 — DISEÑO EN CANVA (superponer sobre la foto)
Formato 1080 x 1350 px
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

──────────────────────────────────────
CAPA 1 — FOTO DE FONDO (100% del lienzo)
──────────────────────────────────────
La foto de la doctora ocupa todo el lienzo como fondo. Aplicar un degradado oscuro SOLO sobre el lado izquierdo del frame: de [COLOR_FONDO_OSCURO] semitransparente (opacidad 65%) en el borde izquierdo a completamente transparente hacia el centro. El lado derecho donde está la doctora NO recibe degradado — conserva la iluminación natural original sin alteraciones.

──────────────────────────────────────
CAPA 2 — CONTENIDO IZQUIERDO (superpuesto al degradado)
──────────────────────────────────────

HEADLINE SUPERIOR:
Texto bold uppercase blanco, tamaño grande, alineado a la izquierda, máximo 2 líneas:
"[HEADLINE_CLINICO]"
Debajo del headline: línea separadora delgada de 2px color [COLOR_ACENTO_PRODUCTO], ancho 60% del lado izquierdo del frame.

BLOQUE CONTRAENTREGA + GARANTÍA (PROMINENTE — primer elemento bajo el headline, lo más visible del lado izquierdo):
Badge/pastilla grande con fondo [COLOR_ACENTO_PRODUCTO] (o borde grueso del mismo color sobre fondo oscuro), ícono de billete/mano + casa. Texto bold uppercase, alto contraste:
"PAGÁS AL RECIBIR"
Subtexto regular blanco pequeño debajo:
"Envío GRATIS a toda Guatemala · GINTACOM y FORZA · No pagás nada por adelantado"
Inmediatamente debajo, un **sello de garantía** (escudo/medalla con ícono de check, color [COLOR_ACENTO_PRODUCTO]) con texto bold pequeño:
"[GARANTIA_TEXTO]"
Estos dos bloques (contraentrega + garantía) se ven ANTES que las estadísticas — son los reductores de fricción #1 y #2 (responden la objeción "¿y si no me funciona?").
> [GARANTIA_TEXTO] — default compliance-safe: "Garantía de satisfacción · Acompañamiento del equipo". NO prometer "devolución del 100%/reembolso" salvo que el operador confirme esa política real (en COD Guatemala el reembolso es delicado). El operador puede sobrescribir con su garantía real (ej: "30 días de garantía").

ZOOM DE CONFIANZA (elemento gráfico):
Un círculo estilo lupa (borde blanco de 2px, fondo interior negro semitransparente) conectado con una línea delgada blanca recta hacia el frasco de la doctora. Dentro del círculo: acercamiento macro del plástico termoencogible transparente con reflejo especular de luz. Debajo del círculo, texto pequeño color [COLOR_ACENTO_PRODUCTO] italic: "Sellado por sanarte®"

BLOQUE ESTADÍSTICO [PORCENTAJE_1]:
Número "[PORCENTAJE_1]" — fuente bold display, tamaño muy grande, color [COLOR_ACENTO_PRODUCTO] (NO #caec55 forzado; usar blanco si el producto es muy claro y no contrasta). Sin borde, sin caja.
Texto descriptivo debajo, blanco regular, tamaño pequeño, interlineado ajustado:
"[STAT_1_DESCRIPCION]"

BLOQUE ESTADÍSTICO [PORCENTAJE_2]:
Número "[PORCENTAJE_2]" — mismo estilo que [PORCENTAJE_1].
Texto blanco pequeño debajo:
"[STAT_2_DESCRIPCION]"

BLOQUE ESTADÍSTICO [NUMERO_CLIENTES]:
Número "[NUMERO_CLIENTES]" — mismo estilo que los anteriores.
Texto blanco pequeño debajo:
"[CLIENTES_DESCRIPCION]"

Espaciado entre los tres bloques estadísticos: igual y generoso. Los números deben respirar y ser lo primero que el ojo ve al lado izquierdo del frame.

──────────────────────────────────────
TRANSICIÓN FOTO → BLOQUE BLANCO
──────────────────────────────────────
Degradado vertical de transparente a blanco #FFFFFF, altura de 50px, justo encima del borde superior del bloque blanco inferior. La foto se funde suavemente — no se ve un corte brusco en ningún caso.

──────────────────────────────────────
CAPA 3 — BLOQUE FAQ INFERIOR (30% inferior del lienzo)
Fondo blanco roto teñido ≤5% hacia el color del producto (no #FFFFFF plano; ver REGLA DE ZONAS BLANCAS — legibilidad del FAQ primero)
──────────────────────────────────────

TÍTULO DE SECCIÓN:
Texto centrado bold uppercase, color #0a1628, tamaño mediano:
"RESOLVAMOS TUS DUDAS"
Línea separadora delgada 1px color [COLOR_ACENTO_PRODUCTO] ancho completo inmediatamente debajo del título.

TRES COLUMNAS FAQ — espaciado igual, alineación centrada:

COLUMNA 1:
[FAQ_1_ICONO_3D], render limpio sobre fondo blanco, sombra suave y sutil. Sin emoji, sin clipart.
Título bold uppercase muy pequeño, color #0a1628:
"[FAQ_1_PREGUNTA]"
Texto regular muy pequeño, color #6b7280:
"[FAQ_1_RESPUESTA]"

COLUMNA 2:
Reloj análogo 3D minimalista, esfera blanca, agujas negras, caja plateada, render limpio, sombra suave. Sin emoji.
Título bold uppercase muy pequeño, color #0a1628:
"¿EN CUÁNTO TIEMPO FUNCIONA?"
Texto regular muy pequeño, color #6b7280:
"[FAQ_2_RESPUESTA]"

COLUMNA 3:
[FAQ_3_ICONO_3D], render limpio sobre fondo blanco, sombra suave y sutil. Sin emoji, sin clipart.
Título bold uppercase muy pequeño, color #0a1628:
"[FAQ_3_PREGUNTA]"
Texto regular muy pequeño, color #6b7280:
"[FAQ_3_RESPUESTA]"

──────────────────────────────────────
BARRA DE CERTIFICACIONES FINAL
Fondo blanco roto teñido ≤5% hacia el color del producto (no #FFFFFF plano), borde superior 1px color [COLOR_ACENTO_PRODUCTO], altura compacta, parte más baja del lienzo
──────────────────────────────────────

Tres sellos en una fila horizontal con espaciado igual. Cada sello: ícono/escudo arriba + dos líneas de texto debajo. Estilo institucional limpio, sin decoración extra.

SELLO IZQUIERDO:
Escudo institucional del Ministerio de Salud Pública y Asistencia Social de Guatemala — colores verde y blanco, estilo oficial. Tamaño pequeño.
Texto línea 1, bold azul oscuro #0a1628 muy pequeño:
"Ministerio de Salud Pública
y Asistencia Social"
Texto línea 2, uppercase regular #0a1628 muy pequeño:
"REGISTRO SANITARIO GUATEMALA"

SELLO CENTRAL:
Logotipo Registro Mercantil de Guatemala: rectángulo con "RM" en negro bold a la izquierda + texto "Registro MERCANTIL" en negro al lado derecho. Tamaño pequeño.
Texto línea 1, bold #0a1628 muy pequeño:
"Registro Mercantil"
Texto línea 2, uppercase regular #0a1628 muy pequeño:
"EMPRESA LEGALMENTE REGISTRADA"

SELLO DERECHO:
Escudo con los colores rojo, blanco y azul de la bandera de EE.UU., estilo institucional limpio. Tamaño pequeño.
Texto línea 1, bold #0a1628 muy pequeño:
"HECHO EN USA"
Texto línea 2, regular #0a1628 muy pequeño:
"FABRICADO BAJO ESTÁNDARES FDA"
IMPORTANTE: NUNCA escribir "Aprobado FDA" ni "Certificado FDA" — solo "Estándares FDA".

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
REGLAS GLOBALES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

- Todo el texto en español, sin excepción.
- Tipografía: [KIT_TIPO_LETRA] del producto (Paso 0 — misma fuente en infografías + ads + bot; default sans-serif moderna Inter/Poppins). Nunca serif en cuerpos pequeños.
- Sin emojis en ninguna sección.
- Paleta estricta: [COLOR_ACENTO_PRODUCTO] (acento dominante: headline, separadores, **3 números estadísticos**), #117200 (letras logo sanarte® solo si armoniza), #caec55 (opcional, solo contorno logo si armoniza), #0a1628 (texto oscuro/fondos respaldo), #FFFFFF (blanco), #6b7280 (gris descriptivo). Ver REGLA MAESTRA DE COLOR.
- Los tres bloques estadísticos ([PORCENTAJE_1], [PORCENTAJE_2], [NUMERO_CLIENTES]) son el elemento visual dominante del 70% superior — deben verse desde lejos antes que cualquier otro texto, en [COLOR_ACENTO_PRODUCTO].
- La foto de la doctora nunca debe verse recortada, filtrada ni artificial.
- Resolución final mínima: 1080x1350px.

---

## IMAGEN 4 — ANTI-IMITACIÓN / PRODUCTO ORIGINAL

Un póster de advertencia/comparación vertical de alta resolución, calidad profesional, formato 2:3. **Hereda el PASO 0 (color del producto, [KIT_TIPO_LETRA] del producto, render del frasco).** Todo el texto en español. Tipografía: [KIT_TIPO_LETRA] del producto, bold (misma fuente que las otras 3 infografías + ads). Sin emojis. Sin elementos decorativos innecesarios.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BLOQUE 1 — ALERTA SUPERIOR (≈15% del lienzo)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Fondo sólido color [COLOR_DEGRADADO_ENCABEZADO] (color primario del producto), ancho completo.

Esquina superior izquierda: triángulo de advertencia 3D con signo de exclamación negro en su interior, tamaño mediano, sombra suave. Color del triángulo = amarillo de advertencia clásico (#FFC107) o [COLOR_ACENTO_PRODUCTO] si contrasta sobre el fondo — NUNCA forzar lima #caec55 si el producto no es verde.

Texto centrado blanco bold uppercase, tamaño muy grande, interlineado ajustado:
"¡NO TE DEJES
ESTAFAR!"

Inmediatamente debajo, sub-barra ligeramente más oscura del mismo color primario, texto blanco regular pequeño centrado:
"Cuidado con las imitaciones de [NOMBRE_PRODUCTO]."

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BLOQUE 2 — ENCABEZADOS DE COLUMNA (≈8% del lienzo)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Fondo: oscuro del producto sólido [COLOR_FONDO_OSCURO], ancho completo. Dividido visualmente en dos mitades iguales.

Mitad izquierda: texto blanco bold uppercase mediano centrado:
"¡PRODUCTO REAL!"
La palabra "REAL" en color [COLOR_ACENTO_PRODUCTO] para contraste (NUNCA amarillo lima si el producto no es verde — regla maestra de color).

Mitad derecha: texto blanco bold uppercase mediano centrado:
"¡FALSO IMITACIÓN!"

Separador entre mitades: línea vertical delgada blanca 1px.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BLOQUE 3 — SUBTÍTULOS DE COLUMNA (≈5% del lienzo)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Mismo fondo oscuro del producto [COLOR_FONDO_OSCURO].

Mitad izquierda centrada: texto blanco regular pequeño: "Nuestro auténtico:"
Debajo: texto [COLOR_ACENTO_PRODUCTO] bold mediano: "Calidad Garantizada"

Mitad derecha centrada: texto blanco regular pequeño: "Cuidado: Producto"
Debajo: texto rojo #cc0000 bold mediano: "falsificado y de baja calidad"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BLOQUE 4 — CUERPO COMPARATIVO (≈40% del lienzo)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Fondo blanco #FFFFFF. Dividido en dos columnas exactas por una línea divisoria central en forma de rayo/relámpago dentado e irregular, blanco puro, grosor 3px, con un resplandor exterior sutil de [COLOR_ACENTO_PRODUCTO] (glow blur suave de 8px). El rayo va de arriba a abajo en zigzag agresivo — no es recto, es una grieta viva entre lo real y lo falso.

COLUMNA IZQUIERDA — Producto auténtico:

Centro de la columna: frasco/bolsa ultra-realista de [NOMBRE_PRODUCTO], etiqueta color [COLOR_ETIQUETA_FRASCO_DOCTORA] con detalles dorados. Sobre la esquina superior izquierda del producto: sello circular verde con checkmark blanco y texto bold en dos líneas: "REAL / REAL".

A la izquierda del producto, pegada al borde izquierdo de la columna, lista vertical con checkmarks color [COLOR_ACENTO_PRODUCTO]:

✔ [ATRIBUTO_REAL_1]
✔ [ATRIBUTO_REAL_2]
✔ [ATRIBUTO_REAL_3]
✔ [ATRIBUTO_REAL_4]
✔ [ATRIBUTO_REAL_5]
✔ [ATRIBUTO_REAL_6]
✔ [ATRIBUTO_REAL_7]

Texto de cada ítem: #0a1628 pequeño regular. El checkmark es verde [COLOR_ACENTO_PRODUCTO].

COLUMNA DERECHA — Producto falso:

Centro de la columna: bolsa/frasco genérico blanco sin marca definida, etiqueta mal impresa con texto corrido. Debajo del producto texto italic gris pequeño ligeramente torcido: "poor printing".

Sobre el producto falso: calavera con tibias cruzadas en forma de X 3D fotorrealista, color verde tóxico #39ff14, ojos con brillo neón verde, expresión amenazante estilizada. Tamaño prominente — ocupa el espacio sobre el producto.

A la derecha del producto, pegada al borde derecho de la columna, lista vertical con íconos X roja:

✘ [DEFECTO_FALSO_1]
✘ [DEFECTO_FALSO_2]
✘ [DEFECTO_FALSO_3]
✘ [DEFECTO_FALSO_4]

Texto de cada ítem: #6b7280 pequeño regular. La X es roja #cc0000.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BLOQUE 5 — ADVERTENCIA DE PRECIOS (≈10% del lienzo)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Fondo sólido [COLOR_FONDO_OSCURO] (oscuro del producto), ancho completo. Bordes superior e inferior con franja de patrón diagonal alternado del color del producto/negro estilo cinta de precaución industrial.

Extremo izquierdo: triángulo de advertencia 3D con exclamación negro, tamaño mediano. Color = amarillo de advertencia clásico (#FFC107) o [COLOR_ACENTO_PRODUCTO] si contrasta — NUNCA forzar lima #caec55 si el producto no es verde.

Texto centrado blanco bold uppercase pequeño-mediano:
"DESCONFÍA DE PRECIOS DEMASIADO BAJOS,"
"PRODUCTOS BARATOS O DESCUENTOS EXAGERADOS,"
"PUEDEN SER IMITACIONES PELIGROSAS,"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BLOQUE 6 — PROTEGE TU SALUD (≈5% del lienzo)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Fondo sólido [COLOR_ACENTO_PRODUCTO] brillante, ancho completo (lima #caec55 solo si el producto es verde). El texto debe contrastar: negro #0a1628 si el acento es claro, blanco si el acento es oscuro.

Texto centrado bold uppercase grande:
"¡PROTEGE TU SALUD Y TU DINERO!"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BLOQUE 7 — CTA FINAL (≈10% del lienzo)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Fondo blanco #FFFFFF.

Línea 1, centrada, texto #0a1628 bold uppercase mediano:
"COMPRA SOLO EL AUTÉNTICO" [en la misma línea] [NOMBRE_PRODUCTO] en color [COLOR_ACENTO_PRODUCTO] bold.

Línea 2, centrada, texto #0a1628 bold uppercase pequeño:
"¡NO ARRIESGUES CON COPIAS BARATAS Y PELIGROSAS!"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BLOQUE 8 — PIE DE PÁGINA (≈7% del lienzo)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Fondo blanco. Bordes izquierdo y derecho decorados con franjas diagonales alternadas verde [COLOR_ACENTO_PRODUCTO] / negro estilo cinta de precaución, igual que el bloque 5.

Centrado: logo sanarte® — letras color #117200, contorno #caec55. Tamaño mediano, protagonista.
Debajo del logo, texto #0a1628 regular uppercase pequeño centrado: "TIENDA AUTORIZADA"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
REGLAS GLOBALES DE IMAGEN 4
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

- Todo el texto en español.
- Tipografía sans-serif bold estilo Poppins. Nunca serif.
- Sin emojis en ningún bloque.
- Paleta estricta: [COLOR_ACENTO_PRODUCTO] (acento dominante: checkmarks, banda BLOQUE 6, cinta de precaución, "REAL"), #FFC107 (triángulos de alerta — amarillo de advertencia clásico), #117200 (letras logo solo si armoniza), #caec55 (opcional, solo contorno logo si armoniza), #cc0000 (X falso + texto "falsificado"), #0a1628 (texto oscuro), #FFFFFF (blanco), #6b7280 (texto descriptivo columna falso), #39ff14 (calavera tóxica). Ver REGLA MAESTRA DE COLOR — el lima #caec55 NO se fuerza en productos no-verdes.
- Resolución mínima 1080x1350px.
- La calavera 3D es fotorrealista y prominente — no clipart, no emoji.
- El rayo divisor entre columnas debe verse como grieta agresiva, no como línea recta.

---

## IMAGEN 5 — RESERVADA

> Slot reservado para una futura pieza de recuperación **por producto** (hereda el PASO 0 como las demás). Las imágenes de *pedido en reparto* y *reclamar en oficina* NO van acá: son piezas FIJAS (no se adaptan al producto), se generan una sola vez aparte. No usar este slot todavía.

---

## IMAGEN 6 — RECUPERACIÓN DE NOVEDAD

> ## ⭐ DOCTRINA (LEER ANTES DE GENERAR)
> Esta pieza NO es del flujo de venta — se envía DESPUÉS de comprar, cuando la transportadora reporta una **novedad** (nadie en casa, dirección incompleta, cliente no responde) y el pedido está a punto de devolverse. El destinatario ya no es un prospecto frío: es alguien que **ya compró y ahora duda en recibir**. Por eso la pieza ataca las 4 razones reales de rechazo contraentrega documentadas en LATAM: (1) se arrepintió / ya no lo quiere, (2) lo vio más barato o desconfía de que sea original, (3) no tenía el efectivo listo, (4) compró por impulso.
>
> **Reparto de trabajo con el texto de la plantilla:** el TEXTO de novedad carga la parte operativa y la consecuencia (qué pasó, accountability, qué perdés si se devuelve, botón SOLUCIONAR). La IMAGEN carga la **razón para cambiar de opinión**: revalidar el producto (arrepentido), gritar que es 100% original y sellado (desconfía), y recordar que con contraentrega no arriesga nada (efectivo/impulso). No se repiten, se complementan. Una infografía entra mejor al cerebro que el texto solo — por eso se manda imagen + texto siempre que se pueda.
>
> **TRABAJO #1 DE LA IMAGEN — REACTIVAR EL DOLOR/DESEO (corrección validada 2026-07-07):** la mitad de las novedades son *"ya no lo quiero / fue una compra innecesaria"* (arrepentido). El antídoto a eso NO es más logística ni más sellos —eso ataca al desconfiado, no al arrepentido— sino **reconectar a la persona con el dolor/deseo exacto que la hizo comprar**, en su propia voz (ETAPA-2 / ETAPA-1B, frases [VOZ-REAL]), en 2ª persona y compliance-safe (habla del PROBLEMA del avatar, nunca "cura/trata"). La mitad superior útil de la pieza —sub-línea del Bloque 1 + kicker del Bloque 3 + los checkmarks redactados como *problema→respuesta*— debe **gritar ese dolor ANTES de listar features**. Es el mismo principio que rige el resto del sistema: **dolor primero, beneficio como respuesta** (Clase 7, Joaquín: los beneficios convierten *después* del punto de dolor; un feature suelto, no). Fuente del dolor: FASE 1 = dolor del ángulo #1 rankeado / problema paraguas del producto · FASE 2 = dolor exacto del ángulo GANADOR.
>
> **REGLA DE MIEDO CALIBRADO (NO calavera — corrección validada):** la aversión a la pérdida funciona (una pérdida pesa ~2x una ganancia), PERO el miedo solo convierte si viene con una SALIDA fácil (contraentrega, pagás al recibir); miedo sin salida = la persona se defiende o bloquea. Y el miedo fuerte ya lo carga el texto. Por eso esta pieza usa **advertencia controlada** ("lo barato suele ser imitación de mala calidad" + triángulo de alerta) — SIN la calavera tóxica ni el frasco falso de IMAGEN 4. Razones: (a) apilar dos golpes de miedo cae en "exageración de salud" (Clase 18 = baneo silencioso / rechazo de plantilla); (b) la mitad de las novedades no son por desconfianza sino por arrepentimiento, a quien una calavera le resulta agresiva y fuera de tema; (c) como imagen que puede ir en una plantilla proactiva de WhatsApp (revisión de Meta), calavera neón + salud es patrón de rechazo. El golpe de calavera completo se reserva a IMAGEN 4 en chat en vivo.
>
> **Test antes de generar:** (1) ¿la imagen RECONECTA con el dolor/deseo exacto que lo hizo comprar, en voz real y 2ª persona (no features sueltos ni logística)? (2) ¿queda OBVIO que es 100% original y sellado? (3) ¿está la salida (pagás al recibir) visible? (4) ¿el cierre dice "solucioná tu novedad hoy, te lo entregamos mañana" (alineado al botón, no "entrega hoy")? (5) ¿tono cálido-firme, no alarmista? Si alguna falla → corregir.

Un póster de recuperación vertical, alta resolución, calidad profesional, formato 4:5 (1080×1350). **Hereda el PASO 0 (color del producto [COLOR_ACENTO_PRODUCTO]/[COLOR_FONDO_OSCURO]/[COLOR_DEGRADADO_ENCABEZADO], [KIT_TIPO_LETRA] del producto en bold, render ultra-realista del frasco).** Todo el texto en español. Tono cálido-firme, NUNCA alarmista. Sin emojis. Texto en imagen bajo (hook + números + CTA, no párrafos). Legible ≥24pt en celular (público 50-70 años).

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BLOQUE 1 — HEADLINE + REACTIVACIÓN DEL DESEO (≈15%)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Fondo [COLOR_DEGRADADO_ENCABEZADO] (color primario del producto), ancho completo. Texto blanco bold uppercase grande centrado, interlineado ajustado:
"TODAVÍA ESTÁS A TIEMPO"
Sub-línea blanco regular mediano debajo — NO "de recibir tu producto" (eso es logística). Carga el DOLOR/DESEO exacto que lo hizo comprar, en 2ª persona, voz real (ETAPA-2/ETAPA-1B), compliance-safe (problema, nunca "cura"):
"[SUBLINEA_DOLOR_DESEO]"   (ej. Nusava: "de calmar ese hormigueo y volver a tener energía")
(Reabre la puerta al arrepentido reconectándolo con la razón por la que lo pidió — no con la logística. "ORIGINAL" lo grita el Bloque 2, no hace falta acá.)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BLOQUE 2 — SELLO 100% ORIGINAL + CONTRAENTREGA (≈18%)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Fondo [COLOR_FONDO_OSCURO] (oscuro del producto), ancho completo. Escudo/check 3D fotorrealista color [COLOR_ACENTO_PRODUCTO] a la izquierda. Texto blanco bold uppercase grande centrado:
"100% ORIGINAL Y SELLADO"
Debajo, fila de 3 mini-sellos/íconos con etiqueta blanca regular pequeña:
"Sello de seguridad · Control de calidad · Distribuidor autorizado"
Sub-línea [COLOR_ACENTO_PRODUCTO] bold pequeña:
"Recibís exactamente lo que pediste — pagás SOLO cuando lo tenés en tus manos"
(Ataca de frente desconfianza + efectivo no listo + impulso. Es la SALIDA fácil que hace que la advertencia del bloque 4 convierta en acción, no en rechazo.)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BLOQUE 3 — RECUERDO DEL DOLOR + PRODUCTO HÉROE (≈30%)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Fondo blanco roto teñido ≤5% al color del producto (ver REGLA DE ZONAS BLANCAS). Encima del bloque, KICKER corto bold uppercase [COLOR_ACENTO_PRODUCTO] centrado (línea fija — reactiva la motivación de compra, antídoto directo al "ya no lo quiero / fue innecesario"):
"¿TE ACORDÁS POR QUÉ LO PEDISTE?"
Frasco ultra-realista de "[NOMBRE_PRODUCTO]" centrado, **grande y protagonista** (Clase 14), con iluminación dramática (glow/halo de su color, reflejo/pódium sutil), etiqueta idéntica a la real. A un lado, lista vertical con checkmarks color [COLOR_ACENTO_PRODUCTO] — máximo 3 (umbral cognitivo, Clase 22). Cada línea NO es una ficha técnica: se redacta como **PROBLEMA SENTIDO → RESPUESTA** (el dolor en voz real primero, el beneficio como su solución), corta:
✔ [BENEFICIO_DOLOR_1]   (ej. "Ese ardor que no te deja dormir → B12+B1 que SÍ se absorben")
✔ [BENEFICIO_DOLOR_2]   (ej. "Cansancio y falta de ánimo → energía que se sostiene")
✔ [GARANTIA_TEXTO]
(Le recuerda al arrepentido, en su propio lenguaje de dolor, por qué lo pidió. No es la vitrina fría de venta — es un golpe de "esto es lo que buscabas" en el momento de duda.)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BLOQUE 4 — ADVERTENCIA CONTROLADA (≈13%)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Fondo [COLOR_FONDO_OSCURO], bordes superior e inferior con franja diagonal alternada color producto/negro estilo cinta de precaución. Triángulo de alerta 3D con exclamación negro a la izquierda — color amarillo de advertencia clásico #FFC107 o [COLOR_ACENTO_PRODUCTO] si contrasta (NUNCA lima forzado si el producto no es verde). Texto blanco bold uppercase pequeño-mediano centrado:
"LO MÁS BARATO SUELE SALIR CARO:"
"IMITACIONES SIN CONTROL DE CALIDAD."
SIN calavera, sin verde tóxico, sin frasco falso (eso vive en IMAGEN 4, chat en vivo). Solo triángulo + las dos líneas.
(Ataca "lo vi más barato": reframe la ganga en riesgo, calibrado para pasar revisión de plantilla.)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BLOQUE 5 — PRUEBA SOCIAL (≈12%)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Fondo sólido [COLOR_ACENTO_PRODUCTO] brillante, ancho completo. Texto contrastante bold centrado (negro #0a1628 si el acento es claro, blanco si es oscuro):
"+[NUMERO_CLIENTES] personas ya lo recibieron y confiaron"
(Usar el default de PLANTILLAS_DEFAULTS_OPERADOR si el operador no dio la cifra real.)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BLOQUE 6 — CIERRE (≈12%)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Fondo blanco #FFFFFF. Texto bold centrado #0a1628 mediano (alinea con el botón "solucionar novedad" de la plantilla aprobada):
"Solucioná tu novedad hoy"
Debajo, [COLOR_ACENTO_PRODUCTO] bold:
"y te lo entregamos mañana"
Abajo, logo [LOGO_MARCA] (letras [COLOR_LOGO_MARCA], contorno [COLOR_ACENTO_MARCA] solo si armoniza) + texto #0a1628 regular uppercase pequeño: "TIENDA AUTORIZADA".

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
REGLAS GLOBALES DE IMAGEN 6
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

- Todo el texto en español. Tipografía [KIT_TIPO_LETRA] del producto, bold. Nunca serif.
- Sin emojis en ningún bloque.
- Tono cálido-firme, no alarmista. NUNCA calavera, verde tóxico ni frasco falso (eso es IMAGEN 4).
- El acento dominante = [COLOR_ACENTO_PRODUCTO] (color del frasco). No forzar lima #caec55 en productos no-verdes (REGLA MAESTRA DE COLOR).
- Cierre SIEMPRE "solucioná tu novedad hoy → te lo entregamos mañana" (alinea con el botón "solucionar novedad" de la plantilla aprobada; conserva la urgencia hoy→mañana: la novedad resuelta hoy se reprograma para el día siguiente). Nunca "entrega hoy".
- Resolución mínima 1080×1350px.
- El frasco es el protagonista visual; los 3 checkmarks nunca le quitan el centro.
- **Presentación según la oferta (regla V6):** el héroe refleja lo que la persona PIDIÓ, no re-vende una oferta nueva. Si la oferta héroe es **2x1 / multi-frasco**, renderizar los **2 frascos (o el pack como viene) + badge "2X1"** del color del producto, y enmarcar en voz de pertenencia: "los 2 frascos que pediste" / "tu 2X1 completo" (amplifica la pérdida —perdés DOS, no uno— y refuerza el valor que ya lo convenció). Si la oferta es de 1 frasco o escalonada 1/2/3, mostrar **1 frasco protagonista** (no inventar cantidades; opcional renderizar el pack de la unidad más vendida si la data lo respalda). **Nunca precio en Q en IMAGEN 6** (ya compró); el badge "2X1" refuerza el trato, no re-abre el debate de precio.
- **Dolor primero (regla V6):** la sub-línea del Bloque 1, el kicker del Bloque 3 y los checkmarks reactivan el DOLOR/DESEO real del comprador antes que cualquier feature. Voz real, 2ª persona, compliance-safe (problema del avatar, jamás "cura/trata"). El "por qué lo compró" pesa más que el "qué es".
- **Texto controlado:** reactivar el dolor NO significa párrafos. Cada línea ≤6-7 palabras; si al sumar el kicker + los checkmarks la pieza se ve cargada, acortar las descripciones — el texto en imagen sigue bajo (pieza apta para plantilla proactiva de WhatsApp).
