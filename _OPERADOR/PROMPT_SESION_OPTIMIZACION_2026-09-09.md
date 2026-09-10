# PROMPT — SESIÓN 2: LA CAPA DE OPTIMIZACIÓN CONTINUA POR DATA

> Copiá desde la línea siguiente hasta el final y pegalo como primer mensaje de una sesión nueva de
> Claude Code abierta en la carpeta `SISTEMA/` (el mismo repo). La sesión hereda `CLAUDE.md` sola.

---

Sos la **sesión 2** de un trabajo dividido en dos. La **sesión 1** está construyendo, en paralelo, el
**FLUJO DECLARADO** del sistema (`DOCTRINA/FLUJO.json` + `Ads/_TOOLS/flujo.py`, **ya implementado**): el grafo de pasos y
gates de las 3 fases, evaluado por código sobre los CSV. Su diseño está en
`_ARCHIVO/roadmap_cumplido/PROPUESTA_FLUJO_DECLARADO_2026-09-09.md` — **leelo primero**, §3.6 define la interfaz entre
las dos sesiones. Corré `python Ads/_TOOLS/flujo.py --todo` para ver el estado real de cada producto. **No toques `DOCTRINA/FLUJO.json`, `flujo.py` ni las skills de fase** sin proponerlo primero: son de la sesión 1. Leé también `PRODUCTOS/_AUDITORIAS/HANDOFF_2026-09-09_FLUJO_DECLARADO.md` (lo hecho, lo medido y las deudas).

Tu trabajo es **exclusivamente la capa de optimización continua basada en data**: el mecanismo por el
cual, después de lanzar, el sistema mide cada ángulo/concepto con su historial propio, escala lo que
funciona, renueva lo que se cansa, apaga lo que no vende, y **genera variantes nuevas** para que el
portafolio nunca dependa de un solo público. Todo decidido por data, nada por criterio.

## 1. QUÉ EXISTE YA — no lo rediseñes, construí encima

Leé `CLAUDE.md` (se carga solo), `DOCTRINA/DATA_PLAYBOOK.md`, `DOCTRINA/CONTABILIDAD.md`,
`DOCTRINA/ESCALADO_PLAYBOOK.md`, `DOCTRINA/PARAMETRIZACION_ADS.md` y `warehouse/README.md` antes de
proponer nada. Lo que ya está resuelto:

| Pieza | Qué hace | Dónde |
|---|---|---|
| Motor de decisión | ESCALAR · PAUSAR · RENOVAR · SEGUIR_MIDIENDO con intervalo de credibilidad bayesiano del CPA (posterior Jeffreys Gamma-Poisson, IC 95 %), tres relojes, tolerancia 1×BE acumulada, detector de fatiga, agregación por `angulo_key` | `Ads/_TOOLS/decidir.py` · parámetros en `PRODUCTOS/_PARAMETROS_DECISION.csv` · reglas congeladas en `Ads/_TOOLS/test_decidir.py` · salida `PRODUCTOS/_DECISIONES.json` |
| Los 5 ejes testeables de un anuncio y su vocabulario cerrado | `angulo_key`, `concepto_key`/`canonico_id`, `nivel_conciencia`, `oferta_key`, `destino_key` (+ covariables: `rol_embudo`, `tipo_hook`, `estilo_visual`, `avatar_edad`, `avatar_genero`, `lleva_precio`) | `DOCTRINA/PARAMETRIZACION_ADS.md` · `PRODUCTOS/_DIM_VOCABULARIO.csv` · `_DIM_ANUNCIOS.csv` · `Ads/_TOOLS/validar_parametros.py` |
| Linaje creativo → anuncio | cada pieza con su blueprint JSON de origen (`canonico_id`), ángulo, concepto, rol de embudo, sellos, `ad_id` | `PRODUCTOS/_DIM_CREATIVOS.csv` · `Ads/_SWIPE/_BLUEPRINTS/CANONICOS/*.json` · `_DIM_CONJUNTOS.csv` |
| Hechos | ventas por ventana/conjunto/anuncio (LucidSales, fuente de verdad) · entrega por anuncio con los 5 ejes parseados (Meta export) · entregas reales (Dropi) · eventos (lanzamiento, pausa, cambio de bot, cambio de presupuesto) | `_FACT_VENTAS.csv` · `_FACT_ENTREGA_ANUNCIO.csv` · `_FACT_ENTREGA.csv` · `_TASA_ENTREGA.csv` · `_EVENTOS.csv` |
| Capa analítica | dbt + DuckDB: staging tipado, `dim_conjunto`, `fct_conjunto_dia`, `fct_anuncio_dia`, 29 tests de integridad, una definición por métrica | `warehouse/` |
| Memoria de patrones | 85 aprendizajes con `evidencia_n`, `confianza`, `estado`, `revisar_despues_de`, `consumido_por` | `PRODUCTOS/_APRENDIZAJES.csv` |
| Lector concepto ↔ métrica | descomposición por atributo con piso de evidencia (≥5 ventas, ≥2 creativos por nivel), matriz ángulo × concepto | `.claude/agents/ETAPA-10.md` (prosa, subagente) |
| Fábrica diaria de conceptos | ≥6 ejecuciones/día desde 22 blueprints, ciclo de vida de la pieza | `.claude/agents/ETAPA-9.md` + skill `generar-conceptos` |
| Optimizador del cierre post-clic | mide cierre (mensajes → ventas) por ángulo, audita congruencia anuncio ↔ bot | `.claude/agents/ETAPA-11.md` |
| Gates deterministas | `verificar_producto.py`, `gen_grafo.py --comparar` (costo en tokens y huérfanos del sistema), `verificar_guia_madre.py`, hooks que validan todo CSV escrito | `Ads/_TOOLS/` · `.claude/settings.json` |

## 2. LAS RESPUESTAS QUE OTRA INVESTIGACIÓN PIDIÓ — ya están, no las vuelvas a preguntar

- **Stack:** Claude Code (skills + 17 subagentes por `Task` + hooks) orquesta; ~50 scripts Python
  deterministas hacen números y gates; **conector MCP oficial de Meta** dentro de la app (no hay
  token propio; se eligió a propósito). No hay n8n, no hay backend, no hay LangGraph.
- **Dónde vive la data:** CSV en `PRODUCTOS/` (fuente única, un dato un dueño) + `warehouse/`
  (dbt + DuckDB, solo lee). Nada en Sheets ni Airtable.
- **LucidSales:** API con `x-token` (12 h), bajada diaria por `Ads/_TOOLS/bajar_lucidsales.py`
  (skill `recopilar-lucidsales`). **No hay webhook ni tiempo real**: la granularidad es el día cerrado.
- **La métrica que decide:** **CPA en quetzales contra el break-even del producto** (`cpa_be_q` en
  `_DIM_PRODUCTOS.csv`, derivado de `_DIM_PRECIOS` + `_TASA_ENTREGA`), con IC 95 %. **Nunca ROAS**
  (memoria del sistema: negocio contra entrega, cohorte ≠ caja). La conversación CORTA, nunca CORONA.
- **Cuántos brazos corren a la vez:** FASE 1 = 6 ángulos (1 conjunto c/u, presupuesto PROTEGIDO,
  ABO) · FASE 2 = 10 conceptos en 1-1-5 + 1-1-5 + 1-2-5 (ABO) · FASE 3 = 1 ganador × 7 réplicas
  (CBO). A $2.99-6 USD/día por conjunto: **1-3 ventas/día por celda**.
- **¿Ejecuta o recomienda?** El runner **dicta**; la sesión ejecuta en Meta por MCP **solo con
  confirmación explícita del operador, orden por orden** (decidido el 09-sep-2026), y verifica
  después con `verificar_publicacion.py --snapshot` y un evento en `_EVENTOS.csv`. Tu política tiene
  que emitir ÓRDENES verificables (qué celda, qué acción, cuánto), nunca ejecutar sola.

## 3. EL PROBLEMA REAL QUE TENÉS QUE MODELAR (lo que un bandit de libro no cubre)

1. **Recompensa retrasada y censurada.** La venta se registra el día del pedido, pero el cobro llega
   al entregarse (~10 días, `maduracion_dias`) y solo se entrega el 70-95 % (`_TASA_ENTREGA.csv`,
   por producto). Un brazo "gana" hoy y se confirma en 10 días. Diseñá el descuento explícito.
2. **Volumen bajo.** 1-3 ventas/día por celda. El motor ya calcula "faltan ~N ventas". Tu política
   tiene que operar **con** esa incertidumbre, no fingir que no existe.
3. **Meta castiga la reasignación continua.** Mover > 20 %/día resetea el aprendizaje del conjunto.
   La política es **diaria, ±20 %, una vez** (surfing). Ningún algoritmo que reasigne cada hora.
4. **La señal de Meta no predice la venta** (APR-002 en `_APRENDIZAJES.csv`). Por eso FASE 1 usa
   presupuesto protegido. Un bandit sobre conversaciones repite el error corregido; sobre VENTAS
   agregadas por `angulo_key` es legítimo.
5. **Un ángulo con historia rentable no se apaga por una mala racha: se RENUEVA el concepto**
   (regla congelada en `test_decidir.py`). Tu ciclo de vida tiene que respetar eso.
6. **El JOIN es por NOMBRE, no por `ad_id`** (llegó corrupto en 2 006 de 2 475 filas). La
   parametrización viaja en la firma de 5 ejes del nombre del anuncio. Tu esquema no puede depender
   de un id que no vuelve.

## 4. LO QUE TENÉS QUE DISEÑAR

### 4.1 Modelo de "perfil de ángulo" con ciclo de vida
Una entidad con identidad propia e historial acumulado por combinación
`producto_key × angulo_key × nivel_conciencia × concepto_key (× avatar, rol_embudo, tipo_hook, dolor)`,
con estados explícitos (`en_prueba → escalando → sostenido → en_declive → renovado → apagado`, o
los que justifiques) y **cada transición disparada por un predicado sobre data**, nunca por juicio.
Decidí qué grano es la entidad (el ángulo, o el ángulo × concepto) y por qué. Tiene que ser un CSV
en `PRODUCTOS/` con dueño único (propuesta: `_ESTADO_ANGULOS.csv`, lo escribe un script tuyo), y
sus estados tienen que ser leíbles por `flujo.py` de la sesión 1 como predicado `csv_campo`.

### 4.2 Política de asignación y de transición
Evaluá, con justificación y contra la data real del repo, las tres opciones — y podés recomendar
una combinación:
- reglas de umbral (lo que ya hace `decidir.py`);
- **Thompson Sampling** sobre el posterior que `decidir.py` ya calcula (muestrear de
  `Gamma(k+0.5, 1)` por brazo, rankear, asignar el +20 % diario a los primeros, explorar con
  probabilidad acotada). Son ~30 líneas con `scipy`, que ya está instalado;
- bandit contextual (contexto = nivel de conciencia, rol de embudo, dolor) — decí honestamente si
  hay volumen para que aporte algo o si es aspiracional.

Mostrá el resultado de tu política **corrida en retrospectiva** sobre `_FACT_VENTAS.csv` +
`_FACT_ENTREGA_ANUNCIO.csv` de jul-sep 2026 (TINNIDROP, CLEARSTEM, NUSAVA): qué habría escalado,
qué habría pausado, en qué fecha, y compará contra lo que `decidir.py` dice hoy y contra lo que se
hizo (`_EVENTOS.csv`). Sin ese backtest, es opinión.

### 4.3 Generación continua de variantes (explorar vs explotar)
El sistema no debe depender de que un humano piense ángulos nuevos. A partir de los perfiles que
ganan, definí la regla que dispara: (a) variante del mismo ángulo con gancho/concepto distinto
(`etapa-9` ya produce; vos decidís **cuándo y cuál**), (b) ángulo adyacente no probado (nuevos
sub-dolores de `etapa-3`, nuevo avatar), (c) el balance explorar/explotar en presupuesto (qué % del
gasto diario va a brazos nuevos). Todo como parámetros en un CSV con `dueno` y `por_que`, al estilo
de `_PARAMETROS_DECISION.csv`.

### 4.4 Causalidad, no solo resultado
Qué atributo (dolor, nivel de conciencia, concepto, avatar, rol de embudo) correlaciona con el CPA
bajo, con piso de evidencia y sin solape de intervalos — `ETAPA-10.md` ya lo describe en prosa;
definí si se convierte en script (`Ads/_TOOLS/atribuir.py` ya existe: leelo y decidí si se extiende
o se reemplaza) y cómo su salida alimenta 4.3 y `_APRENDIZAJES.csv`.

### 4.5 Integración de fuentes
Meta (`_FACT_ENTREGA_ANUNCIO.csv`, vía `ingerir_meta.py`) + LucidSales (`_FACT_VENTAS.csv`) +
Dropi (`_FACT_ENTREGA.csv`, `_TASA_ENTREGA.csv`) hacia tu esquema, **sin duplicar ninguna tabla**.
Si el warehouse dbt necesita un mart nuevo (por ejemplo `fct_angulo_dia` con entrega descontada),
proponelo ahí, con tests.

## 5. INVESTIGACIÓN — profundizá, pero criticá

Buscá en GitHub, documentación oficial, blogs técnicos, Reddit (r/PPC, r/FacebookAds,
r/MachineLearning) y X: qué hacen en producción los que optimizan creativos de Meta con
conversión retrasada/offline (COD, leads, WhatsApp). Puntos de partida ya evaluados por la sesión 1
en `_ARCHIVO/roadmap_cumplido/PROPUESTA_FLUJO_DECLARADO_2026-09-09.md` §2 — leé esa crítica antes de repetirla:
- `langchain-ai/langgraph`: idea correcta (estados, transiciones), librería descartada (re-plataforma).
- `kinosal/optimizer`: demo Flask de un autor, sin mantenimiento. No cumple "adopción real".
- `SMPyBandits`, `fidelity/mabwiser`: librerías de investigación; el posterior ya existe en
  `decidir.py`. Justificá una dependencia nueva solo si aporta algo que 30 líneas no dan.
- `coreyhaines31/marketingskills` y catálogos de skills (`anthropics/skills`, `ComposioHQ`,
  `VoltAgent`): **no instales nada**. Regla registrada: ninguna skill global; toda skill pesa tokens
  en cada sesión y `gen_grafo.py --comparar` lo mide. Si una pieza sirve, citala y proponé qué se
  adapta a la doctrina propia, que ya está parametrizada en `DOCTRINA/GUIA_MADRE_PARAMETRIZADA.md`.

Priorizá lo que tenga adopción real, mantenimiento y trazabilidad. Reportá también lo que
**descartaste y por qué**: eso vale tanto como lo que recomendás.

## 6. RESTRICCIONES (no negociables)

- Los 13 invariantes de `CLAUDE.md`. En especial: el ganador se declara por VENTA agregando por
  `angulo_key` (1); ninguna orden de pausar/escalar sin `decidir.py` (13); los CSV se escriben con
  `csv.DictWriter`, nunca a mano (11); un dato, un dueño.
- Parámetros y constantes **separados** de la lógica: un CSV con `parametro, valor, unidad, dueno,
  por_que`, y una fila en `DOCTRINA/GUIA_MADRE_PARAMETRIZADA.md` por cada uno, para que
  `verificar_guia_madre.py` los cubra.
- No reescribas `decidir.py`: extendelo, o escribí un script que consuma su `--json`. Si tocás sus
  reglas, `test_decidir.py` tiene que seguir en verde y vos agregás tests para lo nuevo.
- Todo script nuevo va en `Ads/_TOOLS/` con docstring que diga QUÉ, POR QUÉ y DE DÓNDE SALE CADA
  DATO, como los existentes. Toda vista nueva se declara en `VISTAS/_MANIFIESTO.json`, no se escribe.
- Antes y después de cualquier cambio de arquitectura: `python Ads/_TOOLS/gen_grafo.py --comparar`.
- Si algo del sistema actual te parece ineficiente o innecesario, decilo con evidencia (qué archivo,
  qué línea, qué mide) **antes** de tocarlo. Nada se borra sin avisar.
- Español, voseo guatemalteco en lo que lea el operador.

## 7. ENTREGABLES

1. `_ROADMAP/PROPUESTA_OPTIMIZACION_CONTINUA_[fecha].md` con: esquema del perfil de ángulo y su
   ciclo de vida; especificación de las reglas de transición y de la política de asignación
   (con el backtest de 4.2); plan de integración de las tres fuentes; lista de repos/librerías que
   se reutilizan y las que se descartaron, con el porqué; preguntas abiertas.
2. Los parámetros nuevos como CSV (esquema arriba) y su fila en la Guía Madre.
3. Si implementás: el script en `Ads/_TOOLS/`, sus tests, y la fila del manifiesto. Con
   `gen_grafo.py --comparar` antes/después y `verificar_guia_madre.py` en verde.
4. Un handoff fechado en `PRODUCTOS/_AUDITORIAS/` con lo hecho, lo verificado y lo que queda.

Si tenés dudas sobre qué se quiere, **preguntá antes de asumir**. Si la duda es sobre cómo está
construido algo, leé el archivo dueño (la tabla MAPA DE ARCHIVOS de `CLAUDE.md`) antes de preguntar.
