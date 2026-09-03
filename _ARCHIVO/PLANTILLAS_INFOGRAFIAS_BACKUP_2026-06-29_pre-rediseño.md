# PLANTILLAS INFOGRAFÍAS — SISTEMA VITALCOM GUATEMALA

## INSTRUCCIONES DE USO
Estas 4 plantillas son el sistema de infografías definitivo y validado.
El formato, estructura e instrucciones de cada plantilla son **FIJOS** — no modificar ni resumir.
Solo reemplazar los valores entre `[ ]` con los datos del producto actual.

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

## MAPA DE VARIABLES POR FUENTE DE DATOS

| Variable | Se extrae de... |
|---|---|
| [NOMBRE_PRODUCTO] | ETAPA-1 |
| [CAPSULAS_CANTIDAD] | Operador / ETAPA-1B |
| [MILIGRAMOS] | Operador / ETAPA-1B |
| [HEADLINE_BENEFICIO] | ETAPA-2 — **TÍTULO IMPACTANTE de dolor/deseo del ángulo, congruente con el anuncio de Meta** (NO la palabra "BENEFICIOS"). Es lo más grande de la pieza. Ej: "TU APOYO DIARIO PARA UNA VIDA MÁS SALUDABLE", "POTENCIA TU ENERGÍA CADA DÍA", "SOPORTE NATURAL PARA TU SISTEMA NERVIOSO". (Clase 22 Joaquín: título impactante, no genérico; la gente escanea títulos.) |
| [KICKER_BENEFICIOS] | Etiqueta pequeña secundaria, ej: "10 BENEFICIOS" o "FÓRMULA AVANZADA". Va pequeña, NUNCA como título principal. |
| [COLOR_DEGRADADO_ENCABEZADO] | Imagen del producto (ej: "azul-verde", "blanco y rosa cálido") |
| [COLOR_BOTON_ENCABEZADO] | Imagen del producto (color primario, ej: "azul", "rosa cálido") |
| [DECORACION_ENCABEZADO] | Relativo al producto (ej: "hojas de menta y rodajas de limón", "pétalos de rosa") |
| [COLOR_BANDA_ETIQUETA] | Imagen del producto (ej: "azul oscuro", "rosa cálido") |
| [BENEFICIOS_ETIQUETA] | ETAPA-2 (resumen de beneficios clave para el texto de la etiqueta) |
| [INGREDIENTES_BASE_BOTELLA] | ETAPA-1B (ingredientes principales en su forma natural visual) |
| [COLOR_CIRCULOS_BENEFICIOS] | Imagen del producto (color primario, ej: "azules", "rosa cálido") |
| [BENEFICIO_N_ICONO] | Icono simple 1 línea relativo al beneficio (ej: "Mujer en pose de meditación") |
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
| [FAQ_1_PREGUNTA] | ETAPA-3A Fase 2 / ETAPA-2 Fase 1 (objeción principal) |
| [FAQ_1_RESPUESTA] | ETAPA-3A Fase 2 / ETAPA-2 Fase 1 |
| [FAQ_1_ICONO_3D] | Derivado de la pregunta (ej: "Batería verde 3D cargándose") |
| [FAQ_2_RESPUESTA] | ETAPA-3A Fase 2 / ETAPA-2 Fase 1 |
| [FAQ_3_PREGUNTA] | ETAPA-3A Fase 2 / ETAPA-2 Fase 1 |
| [FAQ_3_RESPUESTA] | ETAPA-3A Fase 2 / ETAPA-2 Fase 1 |
| [FAQ_3_ICONO_3D] | Derivado de la pregunta |
| [ATRIBUTO_REAL_1] … [ATRIBUTO_REAL_7] | Sistema — generado con base en ETAPA-1B (ingredientes verificados, certificaciones, sellado, dosificación, respaldo de marca, autenticidad, garantía de envío). 7 ítems. |
| [DEFECTO_FALSO_1] … [DEFECTO_FALSO_4] | Sistema — generado con base en ETAPA-1B (problemas típicos de imitaciones en la categoría del producto: ingredientes diluidos o adulterados, sin control de calidad, sin garantía, riesgo para la salud). 4 ítems. |
| [COLOR_FONDO_OSCURO] (IMAGEN 4) | Mismo valor que [COLOR_FONDO_OSCURO] de IMAGEN 2 e IMAGEN 3. Se usa en BLOQUE 2, BLOQUE 5 y BLOQUE 8. |
| [LOGO_MARCA] | PARAMETRIZACIÓN DE MARCA — default "sanarte®"; adaptable por fanpage |
| [COLOR_LOGO_MARCA] | PARAMETRIZACIÓN DE MARCA — default #117200 (verde sanarte®) |
| [COLOR_ACENTO_MARCA] | PARAMETRIZACIÓN DE MARCA — default #caec55 (lima); cambiar si choca con el nicho |
| [TIPO_LETRA] / [KIT_TIPO_LETRA] | KIT TIPOGRÁFICO DE CAMPAÑA — una sola fuente por campaña, igual en infografías + ads + bot. Orden: fanpage → ads de referencia → etiqueta → default sans-serif (Inter/Poppins). Ver sección KIT TIPOGRÁFICO. |

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

**REGLA DURA:** se fija **UNA familia tipográfica por campaña/producto** (el "kit") y se usa **idéntica en las 4 infografías, en los ads de Meta (PLANTILLAS_ADS.md) y en cualquier landing**. No cambiar de fuente entre piezas de la misma campaña. Nunca mezclar más de 2 familias en una pieza; nunca serif en cuerpos pequeños (ilegible).

**¿Tipografía de quién?** La de **TU identidad de campaña/fanpage** (Dr. Estrada, sanarte®, etc.), NO la del fabricante del frasco (Nusava, MicroIngredients…). En dropshipping tu marca es tu fanpage; el mentor quiere que *tu* secuencia sea consistente, no clonar al proveedor.

**ORDEN DE DETECCIÓN (de mayor a menor prioridad):**
1. **Identidad de la fanpage asignada** (ETAPA-FANPAGE) — si la fanpage ya tiene una fuente definida, esa manda.
2. **Tus ads de referencia / campañas que ya funcionaron** (las que pase el operador) — extraer su categoría tipográfica para que infografía y anuncio se vean de la misma familia.
3. **Etiqueta del producto** — solo como respaldo/inspiración de categoría si no hay 1 ni 2.
4. **Default validado:** sans-serif moderna (Inter/Poppins), bold en titulares.

**PASO WEB OPCIONAL (siguiente nivel):** si se quiere afinar, buscar en internet el logo/estilo de **la fanpage o de marcas de EE.UU. del nicho que facturan** (Clase 19: "mirar marcas de EE.UU. que facturan millones") e identificar su **categoría** tipográfica. ⚠️ Realismo: los generadores de IA NO reproducen una fuente con licencia exacta — aproximan por categoría. Por eso el objetivo es fijar la CATEGORÍA correcta y repetirla, no "clonar" un .ttf.

| Variable del kit | Qué define (se fija una vez por campaña) |
|---|---|
| [KIT_TIPO_LETRA] | Categoría única de la campaña: sans-serif geométrica (Poppins/Montserrat) · sans-serif humanista (Inter/Open Sans) · serif elegante (solo belleza/lujo) · display/condensada (fitness/energía). |
| [KIT_PESO_TITULOS] | Grosor de titulares: bold / extra-bold / black. |
| [KIT_ESTILO] | Sensación: clínico-limpio · premium-elegante · enérgico-deportivo · cálido-cercano. Calibrar a la fanpage (clínico → sans limpia; belleza → serif elegante en titulares; fitness → display de peso alto). |

> Cada prompt de infografía y cada prompt de ad debe nombrar la MISMA [KIT_TIPO_LETRA]. Al entregar una campaña, documentar en 1 línea cuál fue el kit elegido y de dónde salió (fanpage / ads de referencia / default).

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

## IMAGEN 1 — 10 BENEFICIOS

### VERSIÓN RÁPIDA (usar cuando se necesita brevedad)

FORMATO: 4:5 (1080×1350) por defecto — coherente con el resto del flujo del bot (ELEMENTO 4 de ETAPA-5). Usar 2:3 (1080×1620) solo si los 10 beneficios necesitan más alto. Fondo derivado del producto (no forzar blanco/azul si el producto es de otro color).
Un póster de infografía de producto vertical de alta resolución. Estética limpia, médica/de bienestar.

ENCABEZADO (12%): TÍTULO PRINCIPAL grande y en bold, color [COLOR_BOTON_ENCABEZADO] (o degradado [COLOR_DEGRADADO_ENCABEZADO]): "[HEADLINE_BENEFICIO]" — el dolor/deseo del ángulo, congruente con el anuncio de Meta. Encima o al lado, en etiqueta pequeña: "[KICKER_BENEFICIOS]" (ej: "10 BENEFICIOS"). Botón [COLOR_BOTON_ENCABEZADO] con texto blanco: "[NOMBRE_PRODUCTO]". [DECORACION_ENCABEZADO] sutiles. NUNCA poner "BENEFICIOS" como título principal.

CENTRO: Frasco ultra-realista de "[NOMBRE_PRODUCTO]". Base rodeada de ingredientes naturales compactos: [INGREDIENTES_BASE_BOTELLA].

LOS 10 BENEFICIOS (Círculos alrededor):
Columna Izquierda (1-5):
[[BENEFICIO_1_ICONO]] [BENEFICIO_1_TITULO]. [BENEFICIO_1_DESC]
[[BENEFICIO_2_ICONO]] [BENEFICIO_2_TITULO]. [BENEFICIO_2_DESC]
[[BENEFICIO_3_ICONO]] [BENEFICIO_3_TITULO]. [BENEFICIO_3_DESC]
[[BENEFICIO_4_ICONO]] [BENEFICIO_4_TITULO]. [BENEFICIO_4_DESC]
[[BENEFICIO_5_ICONO]] [BENEFICIO_5_TITULO]. [BENEFICIO_5_DESC]

Columna Derecha (6-10):
6. [[BENEFICIO_6_ICONO]] [BENEFICIO_6_TITULO].
7. [[BENEFICIO_7_ICONO]] [BENEFICIO_7_TITULO]. [BENEFICIO_7_DESC]
8. [[BENEFICIO_8_ICONO]] [BENEFICIO_8_TITULO]. [BENEFICIO_8_DESC]
9. [[BENEFICIO_9_ICONO]] [BENEFICIO_9_TITULO].
10. [[BENEFICIO_10_ICONO]] [BENEFICIO_10_TITULO].

PIE DE PÁGINA: Logotipo "sanarte®" (letras #117200, contorno #caec55). Barra [COLOR_BARRA_INFERIOR] abajo. Izquierda: [Escudo] "[FOOTER_TEXTO_IZQ]". Derecha: [[ICONO_FOOTER_DER]] "FÓRMULA SEGURA Y DE ALTA CALIDAD". (SIN SELLOS OFICIALES).

---

### VERSIÓN COMPLETA (usar por defecto — mayor control y calidad)

Un póster de infografía de producto vertical de alta resolución y calidad profesional, recreando fielmente el diseño, texto y elementos de la imagen de referencia, optimizado para una lectura clara y sin saturación.

Estilo y Layout: Un diseño de póster limpio y profesional, con una estética de infografía médica/de bienestar, renderizado con un alto nivel de detalle y fidelidad. El layout se organiza en una columna central con un producto principal y diagramas numerados alrededor, dando prioridad de espacio a los textos descriptivos. El fondo del póster incorpora una micro-textura abstracta contextual con opacidad de 2% a 5% máximo, seleccionada según la categoría del producto:

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

Elemento Central (Botella): Una botella de plástico blanco ultra-realista de la marca "PREMIUM WELLNESS" para "[NOMBRE_PRODUCTO]" se sitúa en el centro. La botella debe tener un tamaño ligeramente más pequeño en proporción al póster para ceder espacio visual a los laterales. La etiqueta de la botella debe ser idéntica, incluyendo la banda [COLOR_BANDA_ETIQUETA] inferior con el texto blanco "[NOMBRE_PRODUCTO]" y "SUPLEMENTO ALIMENTICIO | [CAPSULAS_CANTIDAD] CAPSULAS" en dorado. En la etiqueta de la botella debe figurar la lista de beneficios en español ([BENEFICIOS_ETIQUETA]) en texto pequeño. Un sello dorado en la etiqueta dice "[MILIGRAMOS] MG". Una etiqueta colgante negra con texto dorado "[MILIGRAMOS] MG" cuelga visiblemente del tapón en el lado izquierdo.

Base de la Botella: Dispuesto alrededor de la base de la botella hay una disposición compacta de ingredientes naturales: [INGREDIENTES_BASE_BOTELLA].

Diagramas de Beneficios Numerados (Círculos que rodean la botella): Aprovechando el amplio espacio disponible gracias al encabezado reducido, estos iconos y sus textos deben ser destacados, bien espaciados y muy fáciles de leer. Puntos numerados circulares con puntos [COLOR_CIRCULOS_BENEFICIOS] y números blancos (del 1 al 10), dispuestos en dos columnas. Jerarquía visual importante: El título principal del beneficio (en MAYÚSCULAS) debe destacar en tamaño, mientras que el texto descriptivo que lo acompaña debe ir en una tipografía notablemente más pequeña, sutil y delgada para no saturar el diseño.

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

## IMAGEN 2 — ANTES/DESPUÉS + INGREDIENTES + MODO DE USO

Un póster de infografía de producto vertical, alta resolución, calidad profesional, estilo médico-wellness premium. Fondo base blanco #FFFFFF. Todo el texto en español.

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

BLOQUE ANTES/DESPUÉS — SELECCIONAR ARQUETIPO SEGÚN PRODUCTO:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TABLA DE SELECCIÓN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

| Tipo de producto | Arquetipo |
|---|---|
| Pérdida de peso / quema grasa / medidas | ARQUETIPO 1 |
| Acné / piel / manchas / cabello | ARQUETIPO 2 |
| Fertilidad / regulación hormonal | ARQUETIPO 3 |
| Dolor articular / espalda / movilidad / energía | ARQUETIPO 4 |
| Magnesio / vitaminas / colesterol / glucosa / huesos | ARQUETIPO 5 |
| Sueño / insomnio / estrés / ansiedad / concentración | ARQUETIPO 6 |

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

VARIANTE A — recomendada por defecto:

[EXPRESION_FISICA_ANTES]:
Mujer latina real en sus 30s, selfie de espejo en baño, sosteniendo visiblemente una prueba
de embarazo con resultado NEGATIVO. Cara de decepción calmada, resignada. Ropa casual de
casa. Fondo de baño doméstico auténtico.

[EXPRESION_FISICA_DESPUES]:
La misma mujer, mismo baño. Sostiene con ambas manos una prueba de embarazo con líneas
POSITIVAS muy visibles, apuntando hacia la cámara. Cara de emoción genuina: ojos brillantes,
sonrisa amplia, mano cubriendo la boca en reacción de sorpresa feliz.

[ETIQUETA_ANTES]: MES 1 · PRUEBA NEGATIVA
[ETIQUETA_DESPUES]: MES 4 · PRUEBA POSITIVA

VARIANTE B — si el producto se enfoca en vivir el embarazo:

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
INSTRUCCIÓN FINAL DE COMPOSICIÓN (aplica a todos los arquetipos)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Dos fotografías rectangulares lado a lado. Misma mujer (o misma situación) en ambas.
Grano natural de cámara frontal de teléfono, sin edición, sin filtros, sin retoques.
Altamente auténtico y creíble. Sin actuación exagerada.

Entre las dos fotos: línea vertical delgada blanca 1px con el logo "sanarte®" pequeño centrado en medio, letras color #117200, contorno #caec55.

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

Fondo blanco #FFFFFF. Separado de la zona central por una línea delgada de 1px color [COLOR_ACENTO_PRODUCTO] ancho completo.

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
- Tipografía: [KIT_TIPO_LETRA] de la campaña (misma fuente en las 4 infografías + ads + bot; default sans-serif Inter/Poppins)
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
Fondo sólido blanco #FFFFFF
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
Fondo blanco, borde superior 1px color [COLOR_ACENTO_PRODUCTO], altura compacta, parte más baja del lienzo
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
- Tipografía: [KIT_TIPO_LETRA] de la campaña (misma fuente en infografías + ads + bot; default sans-serif moderna Inter/Poppins). Nunca serif en cuerpos pequeños.
- Sin emojis en ninguna sección.
- Paleta estricta: [COLOR_ACENTO_PRODUCTO] (acento dominante: headline, separadores, **3 números estadísticos**), #117200 (letras logo sanarte® solo si armoniza), #caec55 (opcional, solo contorno logo si armoniza), #0a1628 (texto oscuro/fondos respaldo), #FFFFFF (blanco), #6b7280 (gris descriptivo). Ver REGLA MAESTRA DE COLOR.
- Los tres bloques estadísticos ([PORCENTAJE_1], [PORCENTAJE_2], [NUMERO_CLIENTES]) son el elemento visual dominante del 70% superior — deben verse desde lejos antes que cualquier otro texto, en [COLOR_ACENTO_PRODUCTO].
- La foto de la doctora nunca debe verse recortada, filtrada ni artificial.
- Resolución final mínima: 1080x1350px.

---

## IMAGEN 4 — ANTI-IMITACIÓN / PRODUCTO ORIGINAL

Un póster de advertencia/comparación vertical de alta resolución, calidad profesional, formato 2:3. Todo el texto en español. Tipografía: [KIT_TIPO_LETRA] de la campaña, bold (misma fuente que las otras 3 infografías + ads; default sans-serif Poppins). Sin emojis. Sin elementos decorativos innecesarios.

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

Fondo: verde oscuro sólido [COLOR_FONDO_OSCURO], ancho completo. Dividido visualmente en dos mitades iguales.

Mitad izquierda: texto blanco bold uppercase mediano centrado:
"¡PRODUCTO REAL!"
La palabra "REAL" en color [COLOR_ACENTO_PRODUCTO] o amarillo lima para contraste.

Mitad derecha: texto blanco bold uppercase mediano centrado:
"¡FALSO IMITACIÓN!"

Separador entre mitades: línea vertical delgada blanca 1px.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BLOQUE 3 — SUBTÍTULOS DE COLUMNA (≈5% del lienzo)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Mismo fondo verde oscuro [COLOR_FONDO_OSCURO].

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

Fondo sólido [COLOR_FONDO_OSCURO] (verde oscuro del producto), ancho completo. Bordes superior e inferior con franja de patrón diagonal alternado verde/negro estilo cinta de precaución industrial.

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
