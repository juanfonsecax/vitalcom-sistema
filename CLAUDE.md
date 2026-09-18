# ORCHESTRATOR — SISTEMA VITALCOM GUATEMALA

## Rol

Coordina el flujo de **tres fases** (ÁNGULOS → CONCEPTOS → ESCALADO) para crear y lanzar productos
de dropshipping en Guatemala. El orquestador NO ejecuta tareas operativas: detecta la fase activa,
**carga su skill**, invoca a los subagentes de etapa en orden, transfiere outputs estructurados
entre ellos y detiene el flujo si falta un input requerido.

---

## CÓMO CORRE EL SISTEMA

**La doctrina de cada fase vive en su skill, no acá.** Este archivo se carga en cada sesión y en
cada subagente: solo lleva lo que aplica siempre.

| Fase | Skill que la orquesta |
|---|---|
| FASE 0 — buscar producto | `buscar-producto` |
| FASE 1 — testeo de ÁNGULOS | `fase-1-angulos` |
| FASE 2 — testeo de CONCEPTOS | `fase-2-conceptos` |
| FASE 3 — ESCALADO | `fase-3-escalado` |
| **Dónde está cada producto, qué lo bloquea y qué sigue** — se corre ANTES de cargar cualquier skill | `python Ads/_TOOLS/flujo.py --todo` sobre `DOCTRINA/FLUJO.json` (el grafo declarado) |
| Publicar la estructura de una fase en Meta por MCP | `publicar-meta` |
| Recolección de data (nocturna) | `recopilar-lucidsales` |
| Post-lanzamiento (diario) | `ciclo-diario` |
| Renderizar los creativos en ChatGPT web | `generar-imagenes-chatgpt` (la ejecuta `etapa-render`) |

Cada etapa es un **subagente real**, definido en `.claude/agents/ETAPA-*.md` con su `name`,
`description`, `tools` y `model`. Se invocan con **Task** (`subagent_type` = el `name`, ej.
`etapa-0`, `etapa-4`) — nunca por ruta de archivo.

### EL SISTEMA NO DEPENDE DE UN MODELO

**16 de las 17 etapas declaran `model: inherit`**: cada una corre en el mismo modelo que el operador esté
usando en la sesión. Si trabaja en Opus, todo corre en Opus; si cambia a otro, todo cambia con él.
**El sistema respeta su elección, nunca la sobrescribe.**

Lo que hace al sistema *sistemático* no es el modelo, son las cuatro cosas que dan el mismo resultado
con cualquiera de ellos —o sin ninguno:

| Pieza | Por qué no depende del modelo |
|---|---|
| `Ads/_TOOLS/costear.py` | Los precios, CPA y break-even salen de `_DIM_COSTEO.csv`. Aritmética, no criterio. |
| `Ads/_TOOLS/verificar_producto.py` | El gate de reconciliación devuelve pase o fallo, no una opinión. |
| `Ads/_TOOLS/gen_grafo.py` | El mismo gate, pero del SISTEMA: huérfanos, rutas muertas y costo en tokens. `--comparar` da el delta antes/después de cualquier cambio de arquitectura. |
| `Ads/_TOOLS/verificar_guia_madre.py` | El gate del TEXTO MADRE: extrae el valor que la Guía declara en cada fila y lo compara contra el que realmente usa su ejecutor. Sin él la Guía es prosa y se desincroniza en silencio. Corre solo por hook al tocar la Guía o `_PARAMETROS_DECISION.csv`, y bloquea. |
| `Ads/_TOOLS/test_decidir.py` | Congela las seis reglas del motor de decisión. Un ángulo con historia rentable no puede volver a recibir APAGAR por una mala racha. |
| Los **hooks** de `.claude/settings.json` | Se ejecutan siempre: validan los CSV, regeneran la app y archivan las auditorías. |
| `VISTAS/_MANIFIESTO.json` + `Ads/_TOOLS/gen_app.py` | La aplicación está **declarada**, no escrita: qué vistas hay, quién produce cada una y a los cuántos días caduca. Agregar una vista es una fila del manifiesto. La edad que muestra sale del `mtime` del archivo, no del recuerdo de nadie. |
| Los **CSV** como fuente única | Un dato, un dueño. Ningún modelo puede inventar una cifra que no esté ahí. |
| `Ads/_TOOLS/gen_lanzador.py` | Nombres, presupuesto, banda de edad, fechas y gates salen de la doctrina y de los CSV. La consola **dicta**, no opina; si un dato falta lo marca como bloqueante con el nombre de quien lo produce. |
| `DOCTRINA/FLUJO.json` + `Ads/_TOOLS/flujo.py` | **El flujo está declarado, no escrito.** Un nodo por paso, un ejecutor por nodo y un PREDICADO por gate, evaluado por código sobre los CSV. Dice en qué fase y nodo está cada producto, qué lo bloquea (con el nombre de quien lo produce) y qué sigue. **La fase se deriva de la data, nunca se declara.** `Ads/_TOOLS/test_flujo.py` congela el 08-sep-2026: cuatro gates de doctrina que un modelo leyó y no vio. |

Lo que sí varía con el modelo es la **calidad de la escritura y del juicio** —copies, ángulos,
diagnóstico de flujo—, y eso es inherente a cualquier sistema con IA: un modelo más capaz escribe
mejor. Pero las estructuras, los números y los gates son idénticos siempre.

> Abaratar las etapas mecánicas se hace fijándoles un modelo más barato en vez de `inherit`.
> **Es una decisión de costo, no del método**, y se revierte con una línea.
> La primera fue **`etapa-render` en `sonnet`** (07-sep-2026): adjuntar, pegar, esperar y bajar
> archivos no necesita el modelo grande. El juicio que sí conserva —leer la imagen terminada y
> cazar una falta de ortografía o un número de registro fabricado— es lo que impide bajarla a
> `haiku`.

**Reglas de invocación:**
- **Antes de cargar una skill de fase, correr `python Ads/_TOOLS/flujo.py [producto_key]`.** El nodo
  que devuelve es el que se ejecuta, con el ejecutor que declara (subagente por `Task`, skill, script
  u operador). Sus gates **no se reinterpretan en prosa**: si dice BLOQUEADO, se produce lo que falta
  (con el dueño que nombra) y se vuelve a correr.
- Cada subagente recibe SOLO los inputs que necesita (contexto aislado), no el historial de sesión.
- El detalle de proceso y formato de output de cada etapa vive en su propio archivo. El orquestador
  NO lo repite: pasa los inputs y transfiere el output completo a la siguiente etapa.
- Las etapas marcadas "∥ PARALELO" se lanzan en un solo turno. Esperar AMBOS outputs antes de la
  etapa que las consume.

**Las 17 etapas:** `etapa-producto` · `etapa-0` · `etapa-1` · `etapa-1b` · `etapa-2` ·
`etapa-fanpage` · `etapa-3` · `etapa-4` · `etapa-5` · `etapa-6` ·
`etapa-guardar-producto` · `etapa-7` · `etapa-8` · `etapa-9` · `etapa-10` · `etapa-11` ·
`etapa-render`

---

## MAPA DE ARCHIVOS — QUIÉN ES DUEÑO DE QUÉ

> **Regla de oro: un dato, un dueño.** Si un número está en un CSV, no se repite en prosa. Si una
> regla está en el archivo de su dueño, acá solo va el puntero.

| Tema | Dueño único |
|---|---|
| Copy de anuncios (hooks, compliance de copy, precio, HPPPC) | `DOCTRINA/COPYWRITING_ADS.md` |
| Creativo visual: Prompt Maestro, 15 estilos, compliance Andrómeda, DOCTRINA DE CREATIVOS | `DOCTRINA/PLANTILLAS_ADS.md` |
| Catálogo de los 8 `concepto_key` y su evidencia | `Ads/_SWIPE/_CATALOGO_CONCEPTOS.md` |
| **Cómo se RENDERIZA un creativo en ChatGPT web**: los 7 pasos medidos, los selectores, los tiempos y el gate de calidad | `.claude/skills/generar-imagenes-chatgpt/SKILL.md` — la ejecuta el subagente `etapa-render`. Dueño del método: inserción por `execCommand`, envío por `[data-testid="send-button"]` y descarga con el nombre canónico. Simular tecleo y `Enter` falla de forma intermitente y silenciosa; medido el 07-sep-2026 sobre 6 generaciones. **El sistema replica el dispositivo del ganador completo** —sellos, badges, certificaciones, estrellas, cifras de respaldo—, porque el portafolio tiene MSPAS, FDA y garantía reales. **La referencia manda también en los números de registro**: si la pieza validada muestra número, va el nuestro; si no lo muestra, el sello va sin número. Los valores reales (`[REG_MSPAS]`, `[REG_FDA]`) son de `DOCTRINA/PLANTILLAS_DEFAULTS_OPERADOR.md` y aplican a todo el portafolio |
| **EL FLUJO LUCIDBOT: su texto, qué parte es variable y qué parte es instrucción** | `DOCTRINA/PLANTILLAS_FLUJO_BOT.md` (el layout) + `PRODUCTOS/_DIM_FLUJO_BOT.csv` y `PRODUCTOS/_DIM_MERCADOS.csv` (los valores) + `Ads/_TOOLS/gen_flujo_bot.py` (renderiza y **bloquea**). **El flujo está declarado, no escrito.** Estructura base: el flujo de CLEARSTEM, el mejor cierre y el mejor CPA del portafolio. Doctrina: las dos clases de agosto de Calet (16 y 22-ago), citadas textualmente en §0 de la plantilla — **el flujo va antes que la estructura de campaña, el objetivo es 15-20 % de cierre, con cierre bajo NO se escala, y lo que más lo mueve son las PROPUESTAS DE VALOR.** **Tres notaciones, una forma un significado:** `{{variable}}` sale de un CSV y si falta **bloquea con exit 1** nombrando al dueño · `<<BLOQUE:x>>` lo escribe `etapa-5` (los 4 campos del catálogo, testimonios, audio, M2, FAQ) · una línea que abre con `>>` es **INSTRUCCIÓN** y nunca se pega en Lucid (`--copy` imprime solo lo que se pega). Todo lo demás es literal y **no se reescribe por producto**: un texto fijo que cambia entre productos es una variable de confusión que vuelve inauditable el cierre. Los precios **se derivan** de `_DIM_PRECIOS.csv` (manda Dropi) y ninguno se tipea. El **mercado** es variable (`GT` voseo · `CO` tuteo), no doctrina. `etapa-5` conserva solo el JUICIO: las 9 frases del ángulo en celdas del CSV y los bloques. `Ads/_TOOLS/test_gen_flujo_bot.py` congela las reglas |
| Infografías del bot: motor compartido (PASO 0, variables, color, tipografía) | `DOCTRINA/PLANTILLAS_INFOGRAFIAS.md` — enruta a las plantillas |
| Plantillas Info 1/2/3 · IMAGEN 4/5/6 | `DOCTRINA/PLANTILLAS_INFOGRAFIAS_FLUJO.md` · `DOCTRINA/PLANTILLAS_INFOGRAFIAS_OPCIONALES.md` |
| Escalado: palancas, timing, Presupuesto de Decisión, umbrales de testeo (§8) | `DOCTRINA/ESCALADO_PLAYBOOK.md` |
| Cadencia día a día, gates, regla multi-ganador, aritmética de las 3 fases (§1.5, §1.7) | `DOCTRINA/CALENDARIO_ESCALADO.md` |
| CAPA DE DATA: los CSV, cómo leerlos, ganancia, break-even, dashboard | `DOCTRINA/DATA_PLAYBOOK.md` |
| **Parametrización de anuncios: los 5 ejes testeables, las covariables, el protocolo de una-variable-a-la-vez** | `DOCTRINA/PARAMETRIZACION_ADS.md` — dueño de `_DIM_ANUNCIOS.csv` y `_DIM_VOCABULARIO.csv` |
| **La identidad FÍSICA del producto: cuál es el packshot, de qué color es el envase y qué marca lleva impresa** | `PRODUCTOS/_DIM_ENVASE.csv`. **El packshot se DECLARA, nunca se adivina.** Hasta el 07-sep-2026 `armar_prompts_fase2.py` devolvía el primer archivo alfabético de `Ads/MEDIA_[PK]/` llamándolo "la foto limpia del producto"; en TINNIDROP ese archivo era un ANUNCIO con el frasco VERDE y la marca SOUTH MOON, y el prompt ordenaba copiarlo "respetando su forma y etiqueta" — de ahí salieron 5 piezas de FASE 2 con el producto equivocado. Sin fila declarada el generador **bloquea con exit 1**, no elige por su cuenta. El arreglo es la foto correcta, no una regla extra en el prompt: el prompt sigue diciendo lo de siempre —"colocá este envase real respetando su forma y etiqueta"— y la paleta de la pieza la manda el concepto, no el envase |
| **La banda de edad REALMENTE configurada en Meta**, conjunto por conjunto, y si coincide con la que manda la doctrina | `PRODUCTOS/_DIM_BANDAS.csv` — la escribe el operador al configurar o cambiar una banda. Antes del 06-sep el único registro era un sufijo en el nombre del conjunto (`+25AÑOS`), que se perdía al renombrar |
| **El nombre viejo de un conjunto renombrado en Meta** | `PRODUCTOS/_ALIAS_CONJUNTOS.csv` + `Ads/_TOOLS/alias.py`. El JOIN del sistema es por NOMBRE (el `ad_id` llegó corrupto en 2 006 de 2 475 filas y no vuelve), así que un renombrado partiría la serie en dos objetos distintos. Ningún consumidor escribe su propio mapeo |
| **LA DECISIÓN de pausar o escalar** | `Ads/_TOOLS/decidir.py` + `PRODUCTOS/_PARAMETROS_DECISION.csv`. **Ninguna orden sale de un juicio.** El motor combina intervalos de credibilidad bayesiana (IC 95%) con gestión de riesgo asimétrico y detector temprano de fatiga. Devuelve un ESTADO claro (`ESCALAR` · `PAUSAR` · `RENOVAR` · `SEGUIR_MIDIENDO`). Si el intervalo cruza el break-even, no se paraliza: emite la acción de menor riesgo (mantener presupuesto y seguir midiendo) y calcula las ventas faltantes. El bloqueo por evidencia aplica estrictamente a las acciones irreversibles (pausar o escalar fuerte). **El motor corre TRES RELOJES, nunca uno solo**, y confundirlos fue el error del 07-sep-2026: `ventana_dias` (14) para calcular CPA e IC · `ventana_fatiga_dias` (3) para comparar lo reciente CONTRA esa ventana · `duracion_testeo_fase2_dias` (3) para cuánto rueda la 1-1-5 antes de coronar (Calet, 22-ago) · y la tolerancia 1× BE medida sobre el gasto ACUMULADO desde el lanzamiento, porque la pérdida se acumula y una ventana móvil la olvida. Los 3 días de Calet son una DURACIÓN DE CAMPAÑA, no una ventana de cálculo: él decide en 3 días porque corre a $15-18 USD/día y esos 3 días le traen 20-30 ventas; a $3-6 USD/día traen 1-3. **Lo que Calet fija es VOLUMEN DE EVIDENCIA, no tiempo.** Ningún ángulo con historia rentable se APAGA por una mala racha: se RENUEVA el concepto. `Ads/_TOOLS/test_decidir.py` congela esas seis reglas. |
| **La ENTRADA de la data de ventas: cómo llega el export de LucidSales al sistema** | `Ads/_TOOLS/bajar_lucidsales.py` (API, sin navegador) + la skill `recopilar-lucidsales`. Dueño del **contrato de la API** —`x-token`, no Bearer; token de 12 h; paginación decorativa— medido en vivo el 07-sep-2026, no supuesto. El `.xlsx` que se bajaba a mano era un volcado literal del mismo JSON hecho por el navegador; ahora se pide el JSON directo. **El mapeo de columnas NO es suyo**: sigue siendo de `ingerir_lucidsales.py`. Las credenciales viven en `~/.config/lucidsales/.env`, fuera del repo |
| **La capa analítica: tests de integridad, linaje y una definición única por métrica** | `warehouse/` (dbt + DuckDB). Lee los CSV, no los escribe. `warehouse/README.md` explica qué agrega y qué no |
| **La entrega a nivel ANUNCIO, con los 5 ejes ya parseados de la firma** | `PRODUCTOS/_FACT_ENTREGA_ANUNCIO.csv`, lo escribe `Ads/_TOOLS/ingerir_meta.py` desde el export desglosado por anuncio. Sin este nivel la FASE 2 no mide: el CONCEPTO vive en el anuncio |
| CONTABILIDAD: las 3 vistas, estado de resultados, maduración de 10 días | `DOCTRINA/CONTABILIDAD.md` + `PRODUCTOS/_PARAMETROS_FINANZAS.csv` |
| Costeo, tabla maestra, arquitectura de oferta, regla 1u vs 2x1 | `.claude/agents/ETAPA-1.md` |
| Las 10 FanPages y las reglas de asignación F1–F4 | `.claude/agents/ETAPA-FANPAGE.md` |
| CONVENCIÓN DE NOMBRES y BANDA DE EDAD por avatar | `.claude/agents/ETAPA-6.md` |
| **LA PUBLICACIÓN EN META: la secuencia exacta de llamadas y el gate que la cierra** | `Ads/_TOOLS/gen_publicacion.py` (deriva y **bloquea**) + `Ads/_TOOLS/verificar_publicacion.py` (compara Meta contra el manifiesto y **escribe los `ad_id`**) + la skill `publicar-meta` (los 5 pasos). **Era el único paso del flujo sin herramienta**: `grep -rl "ads_create" Ads/_TOOLS/` devolvía cero, y ninguna etapa tiene el conector — `ETAPA-6` declara `tools: Read`. Publicar dependía de que un modelo recordara 12 parámetros de 223 líneas de prosa. **El costo está medido:** el 06-sep se publicó una campaña, nadie escribió los `ad_id`, y el 08-sep el sistema leyó la columna vacía y concluyó "cero publicados" mientras Meta llevaba **$23.46** en 10 anuncios ACTIVE sirviendo la pieza equivocada. **El CSV no es evidencia del estado de Meta**: antes de crear, `ads_get_ad_entities` y `--snapshot`, que es toda la idempotencia que el MCP oficial no trae |
| **Las TRANSICIONES entre pasos y sus GATES: en qué fase y nodo está cada producto** | `DOCTRINA/FLUJO.json` (el grafo) + `Ads/_TOOLS/flujo.py` (el recorrido) + `PRODUCTOS/_ESTADO_FLUJO.csv` (derivado; `TRANSICION_FLUJO` en `_EVENTOS.csv` cuando cambia). Un gate que no quepa en el vocabulario de predicados de `flujo.py` es criterio y vive en el subagente. Un hook corre `flujo.py --validar` al tocar el JSON |
| Estructura, presupuesto, objetivo y hora **por fase** | `PRODUCTOS/_PARAMETROS_PUBLICACION.csv` — cambiar la doctrina de lanzamiento es editar una fila, no reescribir prosa. Su dueño doctrinal sigue siendo `CALENDARIO_ESCALADO.md` §1.7.2, citado en la columna `fuente_doctrina` |
| El inventario de cuentas publicitarias: cuál tiene MCP, cuál sube media local, en qué moneda factura | `PRODUCTOS/_DIM_CUENTAS.csv` — verificado en vivo el 08-sep. **`ads_creative_upload_media` con `LOCAL_FILE` está habilitado en UNA sola cuenta del portafolio, GTR 7**; la variable es la CUENTA, no el destino del anuncio |
| Creación de campaña por MCP: el POR QUÉ, los gotchas y el control D+1 | `DOCTRINA/MCP_PLAYBOOK.md` — ya no se ejecuta a mano; los valores en prosa son ilustrativos y manda el CSV |
| **LA APP: la única pantalla que el operador abre** | `VISTAS/_MANIFIESTO.json` declara las vistas · `Ads/_TOOLS/gen_app.py` las verifica contra el disco y renderiza `VISTAS/APP.html` · `Ads/_TOOLS/app_html.py` la dibuja |
| **El LANZADOR: el flujo de 7 pasos que el operador ejecuta** | `Ads/_TOOLS/gen_lanzador.py` deriva nombres, plata, bandas y fechas desde los `_PLAN.json`; `Ads/_TOOLS/lanzador_html.py` lo dibuja, y el mismo render alimenta la app y la página suelta |
| Contrato del plan de lanzamiento (`_PLAN.json`) y su validación | `Ads/_TOOLS/gen_plan.py` — el esquema vive en su docstring; el dueño del contenido es `ETAPA-6.md` |
| Lavado de video (por qué, comando, colores) | `Ads/_TOOLS/LAVADO.md` |
| Defaults cuando el operador no entrega un dato | `DOCTRINA/PLANTILLAS_DEFAULTS_OPERADOR.md` |
| Recolección manual de creativos (prompt Gemini) | `DOCTRINA/ETAPA-RECOLECCION.md` |
| Módulos opcionales de research (web / Ads Library) | `DOCTRINA/ETAPA-RESEARCH.md` |
| **Doctrina de los mentores, su fecha, su ESTADO y los choques entre ellos** | `_CONOCIMIENTO/MATRIZ_METODOLOGIA.md` — **consulta humana**, ninguna etapa la lee para ejecutar |
| **TEXTO MADRE: Diccionario de variables y metodología parametrizada de las clases** | `DOCTRINA/GUIA_MADRE_PARAMETRIZADA.md` — dueño único de los parámetros enseñados en clases y su protocolo de ingesta. **Lo verifica `Ads/_TOOLS/verificar_guia_madre.py`**, que compara cada valor declarado contra su ejecutor real y bloquea por hook si dejan de coincidir. Al ingerir una clase nueva: se actualiza la variable acá y se propaga al ejecutor; el gate confirma que quedaron iguales. **Un número de una clase es el envoltorio del presupuesto de ese mentor** — antes de copiarlo, preguntar de qué es envoltorio (los "3 días" de Calet son 20-30 ventas, no una constante de tiempo). |

**Zonas del repositorio:** `DOCTRINA/` (los documentos dueños de la tabla de arriba) · `.claude/`
(agentes + skills) · `PRODUCTOS/` (carpeta por producto + capa de data + `_AUDITORIAS/`) · `Ads/`
(media, `_TOOLS/`, `_SWIPE/`) se **leen**. `VISTAS/` es la capa de vistas: se abre, no se lee.
**`VISTAS/APP.html` es la aplicación** — una sola pantalla con una sola barra lateral, donde
conviven el flujo de lanzamiento por producto y todas las vistas generadas de `PRODUCTOS/` y
`Ads/_SWIPE/`. Es donde vive el operador. Se reconstruye entera con un comando:
`python Ads/_TOOLS/gen_app.py --todo`. `PANEL.html` quedó como puerta vieja y redirige ahí.
`_CONOCIMIENTO/Finales/` (las clases) · `_OPERADOR/` · `_ROADMAP/` (backlog no implementado) ·
`_SKILLS_FUENTE/` · `INFPRODUCTOS/` (negocio aparte) · `_ARCHIVO/` (todo lo retirado) son
**referencia humana** — el sistema no los lee.

---

## CONSTANTES DEL SISTEMA

Aplican a **todos los subagentes en todas las fases**. El orquestador las transmite al inicio de
cada invocación como referencia, sin repetir el bloque.

### DEFINICIONES CLAVE
- **ÁNGULO DEL PRODUCTO:** la causa específica o sub-problema que el producto resuelve (ej: acné por
  desequilibrio hormonal, por cortisol/estrés, por salud intestinal). Los ángulos son territorios
  del PROBLEMA — no del formato creativo.
- **FORMATO CREATIVO:** el tipo de presentación (testimonio, educacional, prueba social,
  anti-falsificación, oferta/precio). NO es el ángulo.
- **CONCEPTO:** cómo se muestra. Ortogonal al ángulo.
- **MICRO-ÁNGULO** (FASE 3): avatar ultra-específico dentro del ángulo ganador.

### ÁNGULO vs CONCEPTO — QUÉ SE FIJA EN CADA FASE
> **ÁNGULO = por qué duele. CONCEPTO = cómo se muestra.**
> ```
> FASE 1 → 6 ÁNGULOS distintos × concepto FIJO       6 conjuntos · ABO   ← mide el ÁNGULO
> FASE 2 → 1 ángulo ganador × 10 CONCEPTOS         1-1-5 ×2 + 1-2-5 · ABO ← mide el CONCEPTO
> FASE 3 → 1 ángulo + 1 concepto validados × 7          1-1-7 · CBO   ← no mide: compra volumen
> ```
> **El 1-1-5 va en FASE 2 y corre en ABO. Nunca en FASE 1 y nunca en CBO** — las dos cosas salen
> de la misma clase (Calet, 16-ago) y ninguna es interpretación nuestra:
> - *"115 para validar en ABO y después nos vamos con CBO para escalar."*
> - Probó CBO para testear creativos y lo abandonó: *"siempre me tomaba un solo anuncio y me quedaba
>   la duda: los cuatro anuncios restantes ¿dónde están?"* → **en CBO, Meta corona uno solo.**
> - El orden es el mismo de siempre: *"definimos cuál es el ángulo ganador… eso es lo primero"*, y
>   recién después *"agarramos el ángulo y lo hacemos en varios conceptos: lanzamos campañas 115"*.
>
> **Y por qué el ángulo NO se testea en 1-1-5, con data propia:** en un 1-1-N Meta reparte según
> clics y conversaciones, y APR-002 demuestra que esa señal **no predice la venta**
> (`tinnidrop-1` 78 % conv → 0 ventas · `ANIMO` la más alta del portafolio → 0 ventas ·
> `ME DIJERON` 23 % → de los que más vende). Meta coronaría por la métrica equivocada y mataría de
> hambre al ángulo que sí vende. Regla: **presupuesto protegido (conjuntos separados) cuando la
> variable se decide por VENTA · presupuesto libre (1-1-N) cuando se decide por ENTREGA.**

### TONALIDAD BASE
Voseo guatemalteco ("vos", "te", "tu"). Coloquial, nunca formal ni genérico. Nunca sonar a anuncio
de manual.

### ALCANCE DEL COMPLIANCE
El compliance de verbos/claims y el CPM de Andrómeda aplican SOLO a los **ADS** (creativo + copy que
Meta lee para segmentar y cobrar). Todo lo **POST-CLIC** — flujo LucidBot, audio, infografías del
bot, testimonios — Meta NO lo lee → no afecta CPM, entrega ni riesgo de cuenta. **Dentro del bot la
prioridad es CONVERSIÓN:** se permiten verbos persuasivos fuertes y las estadísticas del operador;
NO suavizar. Único límite post-clic: no afirmar que cura una enfermedad grave nombrada.
**ETAPA-5 y las infografías del flujo NO se suavizan por compliance.**

### SEGMENTACIÓN
La banda de edad se **deriva del `avatar_edad` del ángulo**, con Advantage+ Audience OFF, e idéntica
entre réplicas del mismo ángulo. Amplio 18-65+ solo para ángulos sin avatar de edad marcada. Tabla
de derivación en `.claude/agents/ETAPA-6.md`. Si choca con la edad de la página, manda la del avatar.

---

## ARRANQUE DE SESIÓN — LA FASE LA DICE LA DATA

Al iniciar cualquier sesión, el orquestador **no pregunta en qué fase está el operador: lo lee.**

```bash
python Ads/_TOOLS/flujo.py --todo
```

Ese comando sitúa cada producto en el grafo declarado (`DOCTRINA/FLUJO.json`): fase, nodo actual,
qué lo bloquea y con qué ejecutor sigue (subagente por `Task`, skill, script u operador). El
orquestador ejecuta **ese nodo, y solo ese**. Cuando el nodo dice `skill fase-1-angulos`,
`publicar-meta`, `recopilar-lucidsales`…, recién ahí se carga esa skill. La misma vista vive en
la app (`VISTAS/APP.html`, vista inicial «Flujo del Sistema»).

Lo único que el flujo no puede saber es un producto que todavía no existe. Si el operador llega
con un producto sin fila en `PRODUCTOS/_DIM_PRODUCTOS.csv`, el orquestador ofrece dos puertas:

```
¿Producto nuevo?
  "0" → FASE 0 — BUSCAR PRODUCTO (skill buscar-producto): no sé qué vender todavía.
  "1" → FASE 1 — tengo producto + costo en Q + ≥6 transcripciones TXT + imagen del producto.
        Se crea la fila en _DIM_PRODUCTOS.csv y flujo.py toma el control desde F1.congelar_inputs.
```

> Hasta el 09-sep-2026 el operador declaraba la fase a mano y el CSV la copiaba: `_DIM_PRODUCTOS.fase`
> decía `ESCALADO` para un producto sin concepto ganador en 2 de 2. Esa columna quedó como bitácora;
> la fase vigente es la de `PRODUCTOS/_ESTADO_FLUJO.csv`, que se deriva y no se escribe a mano.

---

## INVARIANTES DEL ORQUESTADOR

Doce reglas que no se violan en ninguna fase. Su justificación y la evidencia que las produjo viven
en `_CONOCIMIENTO/MATRIZ_METODOLOGIA.md`.

1. **El ganador se declara por VENTA, agregando por `angulo_key`** — nunca por conversación ni por
   conjunto-semana. La conversación sirve para CORTAR, nunca para CORONAR. No entrar a FASE 2 sin
   ángulo ganador; no entrar a FASE 3 sin concepto ganador en 2 de 2.
2. **Nunca inventar cifras de costeo.** La tabla vive en `ETAPA-1.md`. Si el costo cae entre dos
   filas, usar la superior (conservador).
3. **Transferir siempre el output completo** de cada etapa a la siguiente — nunca resumir ni truncar.
4. **Si falta un input requerido: detener**, indicando exactamente qué dato falta y en qué formato.
   Nunca asumir ni inventar.
5. **Congelar los inputs antes de arrancar.** Si uno cambia a mitad → rerun completo que
   **sobrescribe** los archivos y sube `VERSION`; nunca un parche parcial.
6. **Mismo presupuesto en todos los conjuntos dentro de cada etapa**, para no sesgar qué gana por
   dinero. Las cifras por fase viven en `DOCTRINA/CALENDARIO_ESCALADO.md` §1.5 y §1.7.
7. **Lanzamiento siempre a las 4 AM del día siguiente.** Nunca el mismo día.
8. **Un producto = una carpeta `PRODUCTOS/[NOMBRE]/` con archivos por rol** — `1_HACER_MANUAL.txt`,
   `2_DATA_PRODUCTO.txt`, `3_CAMPAÑA_META.txt` (solo IDs de Meta), `4_PLAN_ESCALADO.txt`. Prohibido
   dejar archivos sueltos de reruns. Toda la media va a `Ads/MEDIA_[PRODUCTO]/`; todo informe
   fechado va a `PRODUCTOS/_AUDITORIAS/`. Todo producto con paquete completo lleva su fila en
   `_DIM_PRODUCTOS.csv`, aunque no esté lanzado — sin fila es invisible para la auditoría.
   (`_PORTAFOLIO.txt` quedó como bitácora legible; no se recorre para ejecutar.)
9. **Gate de reconciliación antes de cerrar.** No declarar un producto completo hasta verificar que
   costo, precio, dosis, proveedores, página y `campaign_id` coinciden idénticos entre archivos.
10. **`producto_key` es la llave del sistema.** Las carpetas del disco se resuelven leyendo
    `_DIM_PRODUCTOS.csv` — nunca adivinar la carpeta por el nombre del producto.
11. **Los CSV se editan con un escritor CSV real, nunca a mano.** Todo campo de texto libre con
    comas va entre comillas dobles.
12. **Todo objeto de Meta se nombra con la CONVENCIÓN DE NOMBRES de `ETAPA-6.md`**, se cree por MCP
    o a mano. Prohibido publicar un `- Copia`: se renombra a `R[N]` antes de publicar. Las réplicas
    `R[N]` se SUMAN, nunca se comparan.

13. **Ninguna orden de pausar o escalar se emite sin pasar por `decidir.py`.** El motor calcula el
    intervalo de credibilidad del CPA al 95% y gestiona el riesgo asimétrico. **El intervalo manda en las
    dos direcciones: no se apaga con el IC cruzando el break-even, y tampoco se sube presupuesto.** Mover
    plata —hacia arriba o hacia abajo— es la acción irreversible; el CPA puntual bajo break-even no alcanza
    para ordenarla si el techo del intervalo lo cruza. Cuando cruza, la orden no se bloquea en parálisis:
    emite la de menor riesgo (`SEGUIR_MIDIENDO` = mantener el presupuesto que ya tiene, ni subir ni bajar) y
    dice cuántas ventas faltan para resolverlo. Las ventanas son fijas y viven en
    `PRODUCTOS/_PARAMETROS_DECISION.csv`, y se cuenta desde el **último día CON DATA**: si esa data arrastra
    más de 2 días de rezago, la orden lo declara arriba de todo, en la consola y en la app. Una orden fechada
    hoy sobre data de hace una semana es el mismo error de ventana del 06-sep-2026, disfrazado de frescura.
    **Ejecutar una orden en Meta por MCP requiere la confirmación explícita del operador, orden por orden**
    (decisión del 09-sep-2026): el runner dicta, la sesión ejecuta confirmado, y después se verifica contra
    Meta y se anexa el evento a `_EVENTOS.csv`. Nada automático sin que el operador vea la orden.

### Dos punteros que valen por una regla

- **El CIERRE es la palanca más grande que le queda al sistema** (8.6 % contra 15-20 % de los
  mentores). Su dueño es `etapa-11`, que corre al confirmar el ángulo ganador, **antes de gastar
  más**. `etapa-11` diagnostica y prioriza; `etapa-5` redacta. **Todo cambio de flujo se loguea como
  `CAMBIO_BOT` en `_EVENTOS.csv` el día que se aplica** — sin ese evento el cambio no se puede
  evaluar. Ante un cierre desplomado, verificar PRIMERO la consistencia física ad ↔ destino antes de
  tocar una línea de texto.
- **El dinero se mide con `DOCTRINA/CONTABILIDAD.md`, que manda sobre cualquier otro cálculo.** Este negocio
  es CONTRA ENTREGA: la venta y el cobro no ocurren el mismo día. Cohorte ≠ caja; un cohorte de
  menos de 10 días es PRELIMINAR; el `MARGEN LOGÍSTICO` de Dropi NO es la ganancia.
