# ORCHESTRATOR — SISTEMA VITALCOM (GUATEMALA Y COLOMBIA)

## Rol

Coordina el flujo de **cuatro fases** (ÁNGULOS → CONCEPTOS → FLUJO LUCIDBOT → ESCALADO) para crear
y lanzar productos de dropshipping COD en Guatemala (GT) y Colombia (CO): mismo método, cada producto
declara su mercado. El orquestador NO ejecuta tareas operativas: detecta el nodo
activo, **carga su skill**, invoca a los subagentes de etapa en orden, transfiere outputs
estructurados entre ellos y detiene el flujo si falta un input requerido.

> Las historias que produjeron cada regla (fechas, incidentes, citas de mentores) viven en
> `_CONOCIMIENTO/POSTMORTEMS/`. Son consulta humana: ninguna etapa las necesita para ejecutar.

---

## CÓMO CORRE EL SISTEMA

**La doctrina de cada fase vive en su skill, no acá.** Este archivo se carga en cada sesión y en
cada subagente: solo lleva lo que aplica siempre.

| Qué | Ejecutor |
|---|---|
| Dónde está cada producto, qué lo bloquea y qué sigue — **se corre ANTES de cargar cualquier skill** | `python Ads/_TOOLS/flujo.py --todo --escribir` sobre `DOCTRINA/FLUJO.json` |
| FASE 0 — buscar producto | skill `buscar-producto` |
| FASE 1 — testeo de ÁNGULOS | skill `fase-1-angulos` |
| FASE 2 — testeo de CONCEPTOS | skill `fase-2-conceptos` |
| FASE 3 — optimización de flujo LucidBot | skill `fase-3-flujo` |
| FASE 4 — ESCALADO | skill `fase-4-escalado` |
| Publicar la estructura de una fase en Meta por MCP | skill `publicar-meta` |
| Recolección de data (nocturna) | skill `recopilar-lucidsales` |
| Post-lanzamiento (diario) | skill `ciclo-diario` |
| Renderizar creativos en ChatGPT web | skill `generar-imagenes-chatgpt` (la ejecuta `etapa-render`) |

Cada etapa es un **subagente real** en `.claude/agents/ETAPA-*.md`. Se invoca con **Task**
(`subagent_type` = su `name`, ej. `etapa-0`) — nunca por ruta de archivo.

**Las 15 etapas:** `etapa-producto` · `etapa-0` · `etapa-1` · `etapa-1b` · `etapa-2` (incluye la
asignación de FanPage) · `etapa-3` ·
`etapa-4` · `etapa-5` · `etapa-6` · `etapa-guardar-producto` ·
`etapa-7` (monitor de métricas y motor de decisión de escalado, en una sola pasada) · `etapa-9` · `etapa-10` ·
`etapa-11` · `etapa-render`

**Modelo:** 14 etapas declaran `model: inherit` (corren en el modelo que eligió el operador; el
sistema nunca lo sobrescribe). `etapa-render` corre en `sonnet`: es trabajo mecánico, pero necesita
leer la imagen terminada, por eso no baja a `haiku`. Fijar un modelo más barato a una etapa es una
decisión de costo, no del método.

**Lo determinista no depende del modelo** — números, estructuras y gates salen de código:
`costear.py` (precios, CPA, break-even) · `decidir.py` (pausar/escalar) · `flujo.py` (fase y
gates) · `gen_lanzador.py` / `gen_publicacion.py` (nombres, plata, bandas, llamadas a Meta) ·
`verificar_producto.py` (reconciliación) · `verificar_guia_madre.py` (Guía Madre ↔ ejecutores) ·
`gen_grafo.py` (huérfanos, rutas muertas, costo en tokens; `--comparar` antes/después) · los hooks
de `.claude/settings.json` · los CSV como fuente única. Lo que sí varía con el modelo es la
calidad de la escritura y del juicio.

**Reglas de invocación:**
- **Antes de cargar una skill de fase, correr `python Ads/_TOOLS/flujo.py [producto_key]`.** Se
  ejecuta el nodo que devuelve, con el ejecutor que declara. Sus gates **no se reinterpretan en
  prosa**: si dice BLOQUEADO, se produce lo que falta (con el dueño que nombra) y se vuelve a correr.
- **Los gates de entrada de fase son candado, no aviso.** `Ads/_TOOLS/gen_publicacion.py --fase N`
  y `Ads/_TOOLS/registrar_evento.py --evento LANZAMIENTO` niegan la acción si `flujo.gate_entrada()`
  dice que el gate de esa fase no se cumple; solo `--excepcion "motivo"` la deja proceder, y deja
  una fila `EXCEPCION` en `_EVENTOS.csv`.
- **Un "mirar" nunca escribe** (`flujo.py`/`decidir.py`/`gen_grafo.py`, contrato de CLI en
  `DOCTRINA/DATA_PLAYBOOK.md` §7): cada uno necesita su `--escribir` explícito para tocar disco.
- Cada subagente recibe SOLO los inputs que necesita, no el historial de sesión.
- El proceso y el formato de output de cada etapa viven en su archivo; el orquestador no los repite.
- Las etapas marcadas "∥ PARALELO" se lanzan en un solo turno; esperar AMBOS outputs antes de la
  etapa que las consume.

---

## MAPA DE ARCHIVOS — QUIÉN ES DUEÑO DE QUÉ

> **Regla de oro: un dato, un dueño.** Si un número está en un CSV, no se repite en prosa. Si una
> regla está en el archivo de su dueño, acá solo va el puntero.

| Tema | Dueño único |
|---|---|
| Copy de anuncios (hooks, compliance de copy, precio, HPPPC) | `DOCTRINA/COPYWRITING_ADS.md` |
| Creativo visual: Prompt Maestro, 15 estilos, compliance Andrómeda | `DOCTRINA/PLANTILLAS_ADS.md` |
| Catálogo de los 8 `concepto_key` y su evidencia | `Ads/_SWIPE/_CATALOGO_CONCEPTOS.md` |
| Cómo se RENDERIZA un creativo en ChatGPT web (método, selectores, gate de calidad, réplica del dispositivo del ganador, números de registro) | `.claude/skills/generar-imagenes-chatgpt/SKILL.md` · valores `[REG_MSPAS]`/`[REG_FDA]` en `DOCTRINA/PLANTILLAS_DEFAULTS_OPERADOR.md` |
| El flujo LucidBot: su texto, qué parte es variable y qué parte es instrucción. **Declarado, no escrito** | `DOCTRINA/PLANTILLAS_FLUJO_BOT.md` (layout) + `PRODUCTOS/_DIM_FLUJO_BOT.csv` y `_DIM_MERCADOS.csv` (valores) + `Ads/_TOOLS/gen_flujo_bot.py` (renderiza y bloquea). Tres notaciones: `{{variable}}` sale de un CSV y bloquea con exit 1 si falta · `<<BLOQUE:x>>` lo escribe `etapa-5` · una línea `>>` es INSTRUCCIÓN y nunca se pega. Texto fijo no se reescribe por producto; precios se derivan de `_DIM_PRECIOS.csv`; el mercado (`GT`/`CO`) es variable, no doctrina. `test_gen_flujo_bot.py` congela las reglas |
| Infografías del bot: motor compartido | `DOCTRINA/PLANTILLAS_INFOGRAFIAS.md` → `_FLUJO.md` (Info 1/2/3) · `_OPCIONALES.md` (IMAGEN 4/5/6) |
| Bloques de juicio del bot, por producto (los 4 campos del catálogo, testimonios, audio, M2, FAQ) | `PRODUCTOS/[carpeta]/BLOQUES_BOT.md` — lo escribe `etapa-5`; lo inserta `Ads/_TOOLS/gen_flujo_bot.py` |
| Prompts de infografías del bot, por producto | `PRODUCTOS/[carpeta]/INFOGRAFIAS.md` — lo escribe `etapa-4` |
| `1_HACER_MANUAL.txt` de FASE 1: se GENERA, nunca se tipea ni se edita a mano | `Ads/_TOOLS/gen_manual.py` (plan de `gen_lanzador.py` + flujo de `gen_flujo_bot.py` + `INFOGRAFIAS.md`; bloquea nombrando qué falta y quién lo produce) |
| Escalado: palancas, timing, Presupuesto de Decisión, umbrales de testeo | `DOCTRINA/ESCALADO_PLAYBOOK.md` |
| Cadencia día a día, gates, multi-ganador, aritmética de las 4 fases | `DOCTRINA/CALENDARIO_ESCALADO.md` |
| Capa de data: CSV, ganancia, break-even, dashboard | `DOCTRINA/DATA_PLAYBOOK.md` |
| Gasto (spend/impresiones/clicks/mensajes): dueño Meta Graph API vía `Ads/_TOOLS/gasto.py` (ad_id → nombre → conjunto, fallback LucidSales antes de 2026-09-06); ventas: dueño `_FACT_VENTAS.csv` | `Ads/_TOOLS/gasto.py` (espejo dbt: `warehouse/models/marts/fct_gasto_dia.sql`) |
| Parametrización de anuncios: 5 ejes, covariables, una variable a la vez | `DOCTRINA/PARAMETRIZACION_ADS.md` (dueño de `_DIM_ANUNCIOS.csv`, `_DIM_VOCABULARIO.csv`) |
| Identidad física del producto (packshot, color de envase, marca). **Se DECLARA, nunca se adivina**: sin fila, el generador bloquea | `PRODUCTOS/_DIM_ENVASE.csv` |
| Banda de edad realmente configurada en Meta, por conjunto | `PRODUCTOS/_DIM_BANDAS.csv` (la escribe el operador) |
| Nombre viejo de un conjunto renombrado (el JOIN es por NOMBRE) | `PRODUCTOS/_ALIAS_CONJUNTOS.csv` + `Ads/_TOOLS/alias.py` — ningún consumidor escribe su propio mapeo |
| **La decisión de pausar o escalar** | `Ads/_TOOLS/decidir.py` + `PRODUCTOS/_PARAMETROS_DECISION.csv` (ver invariante 13) · `test_decidir.py` congela sus reglas |
| Entrada de ventas desde LucidSales (API, contrato `x-token`) | `Ads/_TOOLS/bajar_lucidsales.py` + skill `recopilar-lucidsales` · el mapeo de columnas es de `ingerir_lucidsales.py` · credenciales en `~/.config/lucidsales/.env` |
| Capa analítica (tests de integridad, linaje, métricas) | `warehouse/` (dbt + DuckDB) — lee los CSV, no los escribe |
| Entrega a nivel ANUNCIO con los 5 ejes parseados | `PRODUCTOS/_FACT_ENTREGA_ANUNCIO.csv` ← `Ads/_TOOLS/ingerir_meta.py` |
| Contabilidad: 3 vistas, estado de resultados, maduración de 10 días | `DOCTRINA/CONTABILIDAD.md` + `PRODUCTOS/_PARAMETROS_FINANZAS.csv` |
| **Mercado del producto** (país, moneda, símbolo, persona voseo/tuteo, registro sanitario, transportadoras, unidad geográfica). Toda doctrina que varíe por país lee de acá, no lo copia. `python Ads/_TOOLS/mercado.py --producto PRODUCTO_KEY` imprime el perfil | `PRODUCTOS/_DIM_MERCADOS.csv` + `Ads/_TOOLS/mercado.py` · columna `mercado` de `PRODUCTOS/_DIM_PRODUCTOS.csv` |
| Costeo, tabla maestra, arquitectura de oferta, regla 1u vs 2x1 (la tabla de `costear.py` es la de GT; la de CO se carga aparte) | `.claude/agents/ETAPA-1.md` |
| **Voz del cliente como dato** (cita textual + URL, verificable, nunca prosa suelta) | `Ads/_TOOLS/verificar_voz.py` GENERA `PRODUCTOS/_VOZ_CLIENTE.csv` (esquema en su docstring; re-descarga la URL y confirma que la cita está ahí). `etapa-1b` es el único que agrega filas, vía `--agregar-json` (nunca a mano); `gen_plan.py --validar` exige que cada ángulo de un `_PLAN.json` en `version >= 2` cite su origen (voz verificada o video de competencia) |
| Datos de las 10 FanPages (identidad, tono, edad de orientación, page_id, productos del nicho) | `PRODUCTOS/_DIM_FANPAGES.csv` |
| El JUICIO de asignación de FanPage (reglas F1–F5) y su output `<pagina_asignada>` | `.claude/agents/ETAPA-2.md` |
| **Imagen de referencia `ligera` fija de FASE 1** (una por producto, para las 6 fichas de ángulo): el JUICIO de cuál de las 3 elegir vive en `etapa-2` (`.claude/agents/ETAPA-2.md`); el dato queda en `PRODUCTOS/_DIM_REFERENCIA_F1.csv`, único escritor `Ads/_TOOLS/referencia_f1.py --elegir` |
| Convención de nombres y banda de edad por avatar | `.claude/agents/ETAPA-6.md` |
| **Publicación en Meta**: secuencia de llamadas y gate de cierre. **El CSV no es evidencia del estado de Meta**: antes de crear, `ads_get_ad_entities` y `--snapshot` | `Ads/_TOOLS/gen_publicacion.py` (deriva y bloquea) + `verificar_publicacion.py` (compara y escribe los `ad_id`) + skill `publicar-meta` |
| Transiciones entre pasos y sus gates | `DOCTRINA/FLUJO.json` + `Ads/_TOOLS/flujo.py` + `PRODUCTOS/_ESTADO_FLUJO.csv` (derivado). Un gate que no quepa en los predicados de `flujo.py` es criterio y vive en el subagente. `flujo.gate_entrada(producto_key, fase)` es el juez único de "¿se cumple el gate de entrada?" (solo lectura) — lo llaman `gen_publicacion.py --fase N` y `registrar_evento.py --evento LANZAMIENTO` para negar la acción salvo `--excepcion "motivo"` (queda un evento `EXCEPCION` en `_EVENTOS.csv`) |
| Estructura, presupuesto, objetivo y hora por fase | `PRODUCTOS/_PARAMETROS_PUBLICACION.csv` (doctrina en `CALENDARIO_ESCALADO.md` §1.7.2) |
| Cuentas publicitarias: MCP, subida de media local, moneda. Media `LOCAL_FILE` solo sube en **GTR 7** | `PRODUCTOS/_DIM_CUENTAS.csv` |
| Creación de campaña por MCP: el porqué, gotchas, control D+1 | `DOCTRINA/MCP_PLAYBOOK.md` (valores ilustrativos; manda el CSV) |
| La app web (la pantalla del operador) | `app/` (backend `app/backend`, frontend `app/frontend`): lee los contratos y dispara los ejecutores declarados en `VISTAS/_MANIFIESTO.json` |
| La vista generada (respaldo sin servidor) | `VISTAS/_MANIFIESTO.json` → `Ads/_TOOLS/gen_app.py` → `VISTAS/APP.html` (dibuja `app_html.py`). La regeneran los hooks; se abre cuando la app web no está corriendo |
| El lanzador de 7 pasos | `Ads/_TOOLS/gen_lanzador.py` + `lanzador_html.py` |
| Contrato de `_PLAN.json` y su validación | `Ads/_TOOLS/gen_plan.py` (esquema en su docstring; contenido de `ETAPA-6.md`) |
| Lavado de video | `Ads/_TOOLS/LAVADO.md` |
| Defaults cuando el operador no entrega un dato | `DOCTRINA/PLANTILLAS_DEFAULTS_OPERADOR.md` |
| Recolección manual de creativos · research opcional | `DOCTRINA/ETAPA-RECOLECCION.md` · `DOCTRINA/ETAPA-RESEARCH.md` |
| Doctrina de mentores, fecha, estado y choques | `_CONOCIMIENTO/MATRIZ_METODOLOGIA.md` — consulta humana |
| **Texto Madre**: parámetros enseñados en clases y protocolo de ingesta | `DOCTRINA/GUIA_MADRE_PARAMETRIZADA.md`, verificado por `verificar_guia_madre.py` (hook, bloquea). Un número de una clase es el envoltorio del presupuesto del mentor: antes de copiarlo, preguntar de qué es envoltorio |
| **Baseline de evals por etapa** (fixtures congelados de outputs reales + asserts deterministas) — requisito para podar prosa de `.claude/agents/ETAPA-*.md` | `evals/` (`promptfooconfig.yaml` · `run_baseline.py` · `fixtures/<etapa>/<producto>` · `asserts/<etapa>*.py`), gate en `Ads/_TOOLS/test_evals_baseline.py` |

**Zonas:** `DOCTRINA/` · `.claude/` · `PRODUCTOS/` · `Ads/` · `evals/` se **leen**. `VISTAS/` se abre, no se
lee; `VISTAS/APP.html` es el respaldo generado de la app web (`python Ads/_TOOLS/gen_app.py --todo`). `_CONOCIMIENTO/` ·
`_OPERADOR/` · `_ROADMAP/` · `_SKILLS_FUENTE/` · `INFPRODUCTOS/` son **referencia
humana** — el sistema no los lee. `_RESPALDOS/` (backups y derivados EN VIVO) está
gitignored: no se versiona ni se lee.

---

## CONSTANTES DEL SISTEMA

Aplican a **todos los subagentes en todas las fases**.

### DEFINICIONES CLAVE
- **ÁNGULO:** la causa específica o sub-problema que el producto resuelve (ej: acné por desequilibrio
  hormonal, por estrés, por salud intestinal). Territorio del PROBLEMA, no del formato.
- **FORMATO CREATIVO:** tipo de presentación (testimonio, educacional, prueba social, oferta). NO es
  el ángulo.
- **CONCEPTO:** cómo se muestra. Ortogonal al ángulo.
- **MICRO-ÁNGULO** (FASE 4): avatar ultra-específico dentro del ángulo ganador.

### ÁNGULO vs CONCEPTO — QUÉ SE FIJA EN CADA FASE
> **ÁNGULO = por qué duele. CONCEPTO = cómo se muestra.**
> ```
> FASE 1 → 6 ÁNGULOS distintos × concepto Y formato FIJOS (IMAGEN)   6 conjuntos · ABO ← mide el ÁNGULO
> FASE 2 → 1 ángulo ganador × 10 CONCEPTOS            1-1-5 ×2 + 1-2-5 · ABO ← mide el CONCEPTO
> FASE 3 → 1 ángulo + 1 concepto validados, mismo presupuesto · la variable es el flujo LucidBot
>          (CAMBIO_BOT) ← mide el CIERRE
> FASE 4 → 1 ángulo + 1 concepto validados × 7        1-1-7 · CBO            ← compra volumen
> ```
> - **El 1-1-5 va en FASE 2 y en ABO. Nunca en FASE 1 y nunca en CBO**: en CBO Meta corona un solo
>   anuncio y los demás no reciben entrega.
> - **El ángulo NO se testea en 1-1-N**: Meta reparte por clics y conversaciones, y esa señal no
>   predice la venta. **Presupuesto protegido (conjuntos separados) cuando la variable se decide por
>   VENTA · presupuesto libre (1-1-N) cuando se decide por ENTREGA.**
> - **FASE 1 corre TODO EN IMAGEN:** los videos de competencia
>   siguen siendo la FUENTE del ángulo (transcripciones de `etapa-0`), nunca el creativo de F1; el
>   formato VIDEO se testea recién en FASE 2, como un concepto más. Dueño de la regla:
>   `Ads/_TOOLS/gen_plan.py --validar` (bloquea un plan de F1 con cualquier conjunto != IMAGEN).

### TONALIDAD BASE
La persona del texto sale del **mercado del producto** (`persona` en `_DIM_MERCADOS.csv`): voseo
guatemalteco en GT, tuteo neutro en CO. Coloquial, nunca formal ni genérico. Nunca sonar a anuncio
de manual. **Colombia corre en modo manual**: el operador entrega los exports de Meta y LucidSales,
la cuenta es EXTERNA y no hay MCP (skill `recopilar-lucidsales`, sección «MERCADO CO (MANUAL)»).

### ALCANCE DEL COMPLIANCE
El compliance de verbos/claims y el CPM de Andrómeda aplican SOLO a los **ADS** (creativo + copy que
Meta lee). Todo lo **POST-CLIC** — flujo LucidBot, audio, infografías del bot, testimonios — Meta no
lo lee. **Dentro del bot la prioridad es CONVERSIÓN**: se permiten verbos persuasivos fuertes y las
estadísticas del operador; NO suavizar. Único límite post-clic: no afirmar que cura una enfermedad
grave nombrada. **ETAPA-5 y las infografías del flujo NO se suavizan por compliance.**

### SEGMENTACIÓN
La banda de edad se **deriva del `avatar_edad` del ángulo**, con Advantage+ Audience OFF, idéntica
entre réplicas del mismo ángulo. Amplio 18-65+ solo para ángulos sin avatar de edad marcada. Tabla
en `.claude/agents/ETAPA-6.md`. Si choca con la edad de la página, manda la del avatar.

---

## ARRANQUE DE SESIÓN — LA FASE LA DICE LA DATA

El orquestador **no pregunta en qué fase está el operador: lo lee.**

```bash
python Ads/_TOOLS/flujo.py --todo --escribir
```

Sitúa cada producto en el grafo: fase, nodo actual, qué lo bloquea y con qué ejecutor sigue. Se
ejecuta **ese nodo, y solo ese**; recién ahí se carga la skill que nombra. La fase vigente es la de
`PRODUCTOS/_ESTADO_FLUJO.csv` (derivada); `_DIM_PRODUCTOS.fase` es solo bitácora.

**Contrato de CLI (T6):** `flujo.py`, `decidir.py` y `gen_grafo.py` son SOLO LECTURA por
defecto — un "mirar" nunca escribe. Cada uno necesita su flag `--escribir` explícito para
persistir en disco (`_ESTADO_FLUJO.csv`/`_EVENTOS.csv`/`_FLUJO.json` · `_DECISIONES.json` ·
`_LINEA_BASE_SISTEMA.json`). El arranque de sesión de arriba SÍ escribe a propósito: el resto
de la sesión lee ese estado derivado.

Si el operador llega con un producto sin fila en `PRODUCTOS/_DIM_PRODUCTOS.csv`:

```
¿Producto nuevo?
  "0" → FASE 0 — BUSCAR PRODUCTO (skill buscar-producto): no sé qué vender todavía.
  "1" → FASE 1 — tengo producto + mercado + costo en su moneda + ≥6 transcripciones TXT + imagen del producto.
        Se crea la fila en _DIM_PRODUCTOS.csv y flujo.py toma el control desde F1.congelar_inputs.
```

---

## INVARIANTES DEL ORQUESTADOR

No se violan en ninguna fase. El código las cita por número: **no renumerar**. Su evidencia vive en
`_CONOCIMIENTO/MATRIZ_METODOLOGIA.md` y `_CONOCIMIENTO/POSTMORTEMS/`.

1. **El ganador se declara por VENTA, agregando por `angulo_key`** — nunca por conversación ni por
   conjunto-semana. La conversación sirve para CORTAR, nunca para CORONAR. No entrar a FASE 2 sin
   ángulo ganador; no entrar a FASE 3 sin concepto ganador en 2 de 2; no entrar a FASE 4 sin cierre
   ≥ `cierre_min_escalar_pct` medido después del `CAMBIO_BOT`.
2. **Nunca inventar cifras de costeo.** Salen de `Ads/_TOOLS/costear.py` sobre `PRODUCTOS/_DIM_COSTEO.csv`:
   fila más cercana al costo; en empate, la superior (conservador). Arquitectura de oferta en
   `.claude/agents/ETAPA-1.md`.
3. **Transferir siempre el output completo** de cada etapa a la siguiente — nunca resumir ni truncar.
4. **Si falta un input requerido: detener**, indicando qué dato falta y en qué formato. Nunca asumir
   ni inventar.
5. **Congelar los inputs antes de arrancar.** Si uno cambia a mitad → rerun completo que
   **sobrescribe** los archivos y sube `VERSION`; nunca un parche parcial.
6. **Mismo presupuesto en todos los conjuntos dentro de cada etapa.** Cifras en
   `DOCTRINA/CALENDARIO_ESCALADO.md` §1.5 y §1.7.
7. **Lanzamiento siempre al día siguiente, a la hora que fija `PRODUCTOS/_PARAMETROS_PUBLICACION.csv`
   (`hora_lanzamiento`, hoy 4 AM).** Nunca el mismo día.
8. **Un producto = una carpeta `PRODUCTOS/[NOMBRE]/` con archivos por rol** — `1_HACER_MANUAL.txt`,
   `2_DATA_PRODUCTO.txt`, `3_CAMPAÑA_META.txt` (solo IDs de Meta), `4_PLAN_ESCALADO.txt`. Prohibidos
   archivos sueltos de reruns. La media va a `Ads/MEDIA_[PRODUCTO]/`; todo informe fechado a
   `PRODUCTOS/_AUDITORIAS/`. Todo producto con paquete completo lleva su fila en
   `_DIM_PRODUCTOS.csv`, aunque no esté lanzado.
9. **Gate de reconciliación antes de cerrar.** No declarar un producto completo hasta verificar que
   costo, precio, dosis, proveedores, página y `campaign_id` coinciden entre archivos.
10. **`producto_key` es la llave del sistema.** Las carpetas se resuelven leyendo
    `_DIM_PRODUCTOS.csv` — nunca adivinar la carpeta por el nombre.
11. **Los CSV se editan con un escritor CSV real, nunca a mano.** Campos de texto con comas van
    entre comillas dobles.
12. **Todo objeto de Meta se nombra con la CONVENCIÓN DE NOMBRES de `ETAPA-6.md`**, por MCP o a mano.
    Prohibido publicar un `- Copia`: se renombra a `R[N]` antes. Las réplicas `R[N]` se SUMAN, nunca
    se comparan.
13. **Ninguna orden de pausar o escalar se emite sin pasar por `decidir.py`.**
    - El motor calcula el IC 95% del CPA. **El intervalo manda en las dos direcciones**: si cruza el
      break-even no se apaga ni se sube presupuesto; se emite `SEGUIR_MIDIENDO` (mantener) con las
      ventas que faltan.
    - Estados: `ESCALAR` · `PAUSAR` · `RENOVAR` · `SEGUIR_MIDIENDO`. Un ángulo con historia rentable
      no se APAGA por una mala racha: se RENUEVA el concepto.
    - Tres relojes distintos, nunca uno: `ventana_dias` (CPA e IC) · `ventana_fatiga_dias` (reciente
      contra ventana) · `duracion_testeo_fase2_dias` (cuánto rueda la 1-1-5). La tolerancia 1× BE se
      mide sobre el gasto ACUMULADO desde el lanzamiento. Lo que fija un mentor en días es volumen
      de evidencia, no tiempo.
    - Las ventanas viven en `PRODUCTOS/_PARAMETROS_DECISION.csv` y se cuentan desde el **último día
      CON DATA**; si esa data supera `rezago_max_dias` (o su edad es desconocida), `gen_ordenes.py`
      no emite ninguna orden de ESCALAR (bloqueante); PAUSAR sí sale, con aviso.
    - **Nunca se sube presupuesto sobre una base inventada**: sin `daily_budget` real en el
      snapshot de Meta, la orden de ESCALAR se bloquea.
    - **Ejecutar una orden en Meta por MCP requiere la confirmación explícita del operador, orden por
      orden.** Después se verifica contra Meta y se anexa el evento a `_EVENTOS.csv`.

### Dos punteros que valen por una regla

- **El CIERRE es la palanca más grande del sistema.** Su dueño es `etapa-11`. El DIAGNÓSTICO y la
  REESCRITURA no corren juntos: `etapa-11` diagnostica el cierre y la congruencia anuncio↔bot en
  **FASE 2** (nodo `F2.etapa-11`, registra `DIAGNOSTICO_CONGRUENCIA`, no bloquea el testeo de
  conceptos) y entrega el brief priorizado. La REESCRITURA es **FASE 3** (nodo `F3.reescribir`):
  `etapa-5` redacta los BLOQUES DE JUICIO del flujo a partir de ese brief, el operador aplica y
  anexa `CAMBIO_BOT` (o `EXCEPCION_CAMBIO_BOT` si decide saltárselo) — nunca uno viejo, siempre
  fechado DESPUÉS del concepto ganador. El gate que compra volumen es `F4.entrada` de
  `DOCTRINA/FLUJO.json`: exige ese `CAMBIO_BOT`/`EXCEPCION_CAMBIO_BOT` MÁS el cierre medido después
  de él por encima de `cierre_min_escalar_pct` (≥30 mensajes). Por debajo del umbral, el producto se
  queda en FASE 3 para otra iteración del flujo — nunca sube presupuesto. Reglas A-G del orden en
  `DOCTRINA/PLANTILLAS_FLUJO_BOT.md`. Ante un cierre desplomado, verificar PRIMERO la consistencia
  física ad ↔ destino.
- **El dinero se mide con `DOCTRINA/CONTABILIDAD.md`**, que manda sobre cualquier otro cálculo. Negocio
  CONTRA ENTREGA: cohorte ≠ caja; un cohorte de menos de 10 días es PRELIMINAR; el `MARGEN LOGÍSTICO`
  de Dropi NO es la ganancia.
