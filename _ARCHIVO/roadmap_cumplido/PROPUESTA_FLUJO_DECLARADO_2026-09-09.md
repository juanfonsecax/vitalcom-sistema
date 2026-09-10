# PROPUESTA — EL FLUJO DECLARADO (`_FLUJO.json` + `flujo.py`)

**Fecha:** 2026-09-09 · **Estado: IMPLEMENTADO el mismo día** (olas A-E). El diseño vive en su archivo
dueño: `DOCTRINA/FLUJO.json` + `Ads/_TOOLS/flujo.py` (la propuesta decía `FLUJO/_FLUJO.json`; se
eligió `DOCTRINA/` para no abrir una zona nueva del repo). Resultado y deudas en
`PRODUCTOS/_AUDITORIAS/HANDOFF_2026-09-09_FLUJO_DECLARADO.md`. Se conserva como registro de la decisión.

---

## 1. EL DIAGNÓSTICO: por qué el sistema "varía"

El operador lo siente como variación. Medido en el repo, es una sola cosa: **las TRANSICIONES entre
pasos y sus GATES viven en prosa, y un modelo las interpreta cada vez.**

Lo que hoy es determinista (no varía con el modelo ni con la sesión):

| Pieza | Qué decide sola |
|---|---|
| `costear.py` | precios, CPA objetivo, break-even |
| `decidir.py` + `_PARAMETROS_DECISION.csv` | ESCALAR · PAUSAR · RENOVAR · SEGUIR_MIDIENDO con IC 95 % |
| `gen_lanzador.py` | nombres, plata, bandas, fechas, bloqueantes |
| `gen_publicacion.py` + `verificar_publicacion.py` | la secuencia de llamadas a Meta y el gate que escribe `ad_id` |
| `verificar_producto.py` · `gen_grafo.py` · `verificar_guia_madre.py` | gates de reconciliación (producto, sistema, texto madre) |
| hooks de `.claude/settings.json` | validación de CSV, regeneración de la app, archivo |
| `_MANIFIESTO.json` + `gen_app.py` | la app está declarada, no escrita |

Lo que hoy es prosa y por eso varía:

| Dónde | Qué dice | Quién lo evalúa |
|---|---|---|
| `CLAUDE.md` → "¿En qué fase estás hoy?" | el operador declara la fase | el operador, de memoria |
| `fase-1-angulos` PASO −1 | "si falta un campo obligatorio → detener" | el modelo, leyendo un bloque de texto |
| `fase-2-conceptos` cabecera | "¿están los 10 conceptos generados y subidos? (si no → etapa-9)" | el modelo |
| `fase-3-escalado` | "un ganador de 1 de 2 es ruido → detener" | el modelo |
| `ETAPA-8.md` §B + `ESCALADO_PLAYBOOK.md` §6/§8 | matar-por-conversación < 35 %, PD 1×BE, surfing +20 % | el modelo — **y no coincide con `decidir.py`**, que no conoce el 35 % |
| `_DIM_PRODUCTOS.fase` | `ESCALADO` / `DEFINICION` / `TESTEO` / vacío | se escribe a mano; CLEARSTEM tuvo "ESCALA" en el nombre de campaña y `DEFINICION` en el CSV |

**La evidencia de que esto cuesta plata es del 08-sep-2026** (`HANDOFF_2026-09-08_PUBLICAR_META.md`).
Cuatro gates que existían en prosa y ninguno se disparó:

1. R3F-13 dice "FASE 2 necesita 10 conceptos o no arranca". Se publicó con 5.
2. `CALENDARIO_ESCALADO` §1.7.2 dice 1-1-5 + 1-1-5 + 1-2-5. Se publicó 5 conjuntos × 1 concepto.
3. `_PLAN_FASE2.json` contradecía lo publicado y nadie lo comparó.
4. El CSV decía "cero publicados" mientras Meta llevaba $23.46 sirviendo la pieza equivocada.

Un `flujo.py` con esos cuatro predicados escritos como código los habría cantado antes de gastar.
**Ese es el criterio de aceptación de esta propuesta:** correr `flujo.py TINNIDROP` sobre la data
del 08-sep tiene que reproducir los cuatro hallazgos sin que nadie los lea.

---

## 2. CRÍTICA A LA INVESTIGACIÓN PARALELA (Perplexity)

Se evaluó contra el repo real, no contra la descripción del sistema.

### LangGraph — idea correcta, capa equivocada
- Lo que aporta (estados explícitos, aristas condicionales, checkpoints, human-in-the-loop) **es
  exactamente lo que falta**. El concepto se adopta entero.
- La librería no. El runtime de este sistema es **Claude Code**: skills, subagentes por `Task`,
  hooks, y el **conector MCP oficial de Meta** que vive en la app (decisión registrada: se eligió el
  conector, no un token propio). LangGraph es un proceso Python que orquesta llamadas a un LLM con
  API key propia: adoptarlo implica reescribir las 17 etapas como nodos Python, perder los hooks,
  perder el conector MCP tal como está y rehacer el costeo de tokens. Es un **re-plataformado**,
  no "el siguiente paso".
- Los dos repos de ejemplo (`luuisotorres/…`, `josephsenior/…`) son demos de patrón. No aportan
  nada que `_MANIFIESTO.json` + `gen_app.py` no muestren ya como patrón propio del sistema.

**Veredicto:** el grafo de estados se implementa como **archivo declarado + runner determinista**,
que es el patrón que este sistema ya usa para la app, el plan y la publicación. Cero dependencias.

### Archify — no aplica
Genera diagramas HTML/SVG. El sistema ya tiene `gen_grafo.py` (grafo del sistema medido en tokens) y
una app declarada. El diagrama del flujo se renderiza desde `_FLUJO.json` en la propia app
(mermaid nativo). Un diagrama que no sale del mismo JSON que ejecuta el runner se desincroniza: es
prosa con flechas.

### Multi-armed bandits — falsa dicotomía "bandit vs reglas"
- `decidir.py` **ya calcula el posterior bayesiano** que un Thompson Sampling necesita:
  `Ventas ~ Poisson(λ)`, posterior Jeffreys `Gamma(k+0.5, 1)`, `CPA = gasto/λ`. Muestrear de ese
  posterior para rankear brazos son ~30 líneas con `scipy`, que ya está instalado. **No se necesita
  `SMPyBandits` ni `MABWiser`**, y `kinosal/optimizer` es una demo Flask de un autor, sin
  mantenimiento: no cumple el propio criterio de Perplexity de "adopción real".
- Lo que un bandit clásico asume y acá **no se cumple**, y que la sesión 2 debe modelar explícito:
  1. **Recompensa retrasada y censurada**: la venta es contra entrega; el cobro llega ~10 días
     después (`maduracion_dias`) y solo el 70-95 % se entrega (`_TASA_ENTREGA.csv`). El brazo
     "ganó" hoy y se sabe de verdad en 10 días.
  2. **Volumen bajo**: 1-3 ventas/día por celda a $3-6 USD/día. Un bandit converge por volumen; acá
     el volumen es lo que Calet compra con $15-18/día. `decidir.py` ya lo resuelve reportando
     "faltan ~N ventas".
  3. **La asignación continua choca con Meta**: mover presupuesto > 20 %/día resetea la fase de
     aprendizaje del conjunto (doctrina de surfing). Un bandit que reasigna cada hora destruye la
     señal que quiere leer. La política tiene que ser **diaria y acotada a ±20 %**.
  4. **FASE 1 usa presupuesto PROTEGIDO a propósito** (APR-002: la conversación no predice la
     venta). Un bandit sobre la métrica de Meta repetiría el error que la doctrina ya corrigió. Un
     bandit sobre VENTAS agregadas por `angulo_key` sí es legítimo.

**Veredicto:** Thompson Sampling como **política de asignación** encima del posterior que ya existe
(qué brazos reciben el +20 %, cuáles se renuevan, cuál se explora), con cadencia diaria, tope ±20 %
y descuento por entrega. No como reemplazo del motor. Dueño: sesión 2.

### Catálogos de skills — con gate, no en bloque
- Regla ya registrada: **no se instalan skills globales**; toda skill pesa tokens en cada sesión y
  `gen_grafo.py --comparar` lo mide. Cualquier skill importada entra por el mismo gate.
- `obra/superpowers`: workflow de desarrollo de software (TDD, worktrees). No es del dominio.
- `coreyhaines31/marketingskills`: frameworks genéricos de CRO/copy. **Riesgo de contradecir la
  doctrina de los mentores** (`GUIA_MADRE_PARAMETRIZADA.md`, `COPYWRITING_ADS.md`) que ya está
  parametrizada y verificada por hook. Se evalúa pieza por pieza contra la matriz de metodología;
  no se instala.
- `anthropics/skills`, `ComposioHQ/awesome-claude-skills`, `VoltAgent/awesome-agent-skills`: son
  índices. Sirven para BUSCAR, no son una recomendación.

### Las 6 preguntas de Perplexity — todas se responden desde el repo
Están respondidas en el prompt de la sesión 2 (`_OPERADOR/PROMPT_SESION_OPTIMIZACION_2026-09-09.md`
§2) para que ninguna sesión las vuelva a preguntar.

---

## 3. EL DISEÑO: `FLUJO/_FLUJO.json` + `Ads/_TOOLS/flujo.py`

### 3.1 Principio
> **El flujo se DECLARA, no se escribe.** Igual que la app (`_MANIFIESTO.json`) y el plan (`_PLAN.json`).
> Un nodo por paso, una arista por condición, un predicado por gate — y todos los predicados los
> evalúa código sobre los CSV, nunca un modelo leyendo prosa.

### 3.2 Qué es un nodo

```json
{
  "id": "F2.publicar",
  "fase": 2,
  "titulo": "Publicar la estructura de FASE 2 en Meta",
  "ejecutor": {"tipo": "skill", "name": "publicar-meta"},
  "requiere": [
    {"dato": "10 conceptos GENERADOS",
     "predicado": {"csv": "_DIM_CREATIVOS", "where": {"producto_key": "{pk}", "estado": "GENERADO"}, "count_gte": 10},
     "dueno": "etapa-9 / etapa-render", "regla": "R3F-13"},
    {"dato": "estructura del plan = doctrina",
     "predicado": {"script": "python Ads/_TOOLS/gen_publicacion.py {pk} --fase 2 --validar", "exit": 0},
     "dueno": "etapa-6", "regla": "CALENDARIO_ESCALADO 1.7.2"},
    {"dato": "Meta no tiene ya esta campaña",
     "predicado": {"script": "python Ads/_TOOLS/verificar_publicacion.py {pk} --snapshot --ausente", "exit": 0},
     "dueno": "operador", "regla": "HANDOFF 08-sep: el CSV no es evidencia de Meta"}
  ],
  "produce": [{"archivo": "PRODUCTOS/{slug}/_PUBLICACION_F2*.json"}],
  "siguiente": [
    {"si": {"script": "python Ads/_TOOLS/verificar_publicacion.py {pk}", "exit": 0}, "a": "POST.esperar_data"},
    {"si_no": "DETENER"}
  ]
}
```

Ejecutores posibles: `subagente` (se invoca por `Task` con su `name`), `skill`, `script`
(comando determinista) y `operador` (paso manual; el nodo dicta qué copiar y qué archivo debe
aparecer para darse por cumplido).

### 3.3 El vocabulario de predicados es CERRADO
Solo estos, y ninguno admite texto libre:

| Predicado | Evalúa |
|---|---|
| `csv` + `where` + `count_gte` / `count_eq` | filas en un CSV de `PRODUCTOS/` |
| `csv_campo` + `no_vacio` / `eq` / `in` | un valor de `_DIM_PRODUCTOS`, `_DIM_CONJUNTOS`, … |
| `archivo_existe` / `glob_min` | disco (transcripciones, media, `_PLAN.json`) |
| `json_campo` | un campo de un `_PLAN.json` / `_PUBLICACION.json` / `_DECISIONES.json` |
| `script` + `exit` / `json_campo` | un verificador o motor existente (`decidir.py --json`, `verificar_*.py`) |
| `edad_max_dias` | frescura de una fuente (mismo criterio que `caduca` en el manifiesto) |

Un gate que no se pueda escribir con esto **no es un gate: es criterio**, y va al subagente que lo
ejerce, no al flujo.

### 3.4 El runner

```
python Ads/_TOOLS/flujo.py TINNIDROP            # dónde está, qué bloquea, qué sigue
python Ads/_TOOLS/flujo.py --todo               # los 8 productos
python Ads/_TOOLS/flujo.py TINNIDROP --json     # para la app
python Ads/_TOOLS/flujo.py TINNIDROP --avanzar  # registra la transición (TRANSICION_FLUJO en _EVENTOS.csv)
python Ads/_TOOLS/flujo.py --validar            # el JSON contra el disco: ejecutores que existen, predicados válidos
```

Salida (ejemplo con la data del 08-sep):

```
TINNIDROP · nodo actual: F2.publicar · desde 2026-09-06
  ✗ 10 conceptos GENERADOS ........ 5 de 10   → etapa-9 / etapa-render   (R3F-13)
  ✗ estructura del plan = doctrina  5×1 ≠ 1-1-5+1-1-5+1-2-5 → etapa-6  (CALENDARIO 1.7.2)
  ✗ Meta no tiene ya esta campaña . 120257730530160595 ACTIVE $23.46 → operador
  → DETENIDO. Siguiente ejecutable: etapa-9 (faltan 5 conceptos).
```

El runner **dicta**. No ejecuta subagentes ni toca Meta: eso lo hace la sesión (con `Task`) o el
operador, y el runner lo comprueba después por sus `produce` y sus predicados.

### 3.5 Dónde vive el estado
- `PRODUCTOS/_ESTADO_FLUJO.csv` — `producto_key, nodo_actual, desde, evidencia, version_flujo`.
  Reemplaza a la columna `fase` de `_DIM_PRODUCTOS.csv` (que pasa a derivarse del nodo).
- `_EVENTOS.csv` — cada transición se loguea (`evento=TRANSICION_FLUJO`, `valor_antes=nodo`,
  `valor_despues=nodo`). Ese es el "checkpoint" de LangGraph, en la tabla que ya existe.
- El nodo actual **nunca se declara a mano**: `flujo.py` lo deriva de la data (el último nodo cuyos
  `produce` existen y cuyos gates de salida pasan). `--avanzar` solo lo confirma y lo registra.

### 3.6 El post-lanzamiento como sub-grafo (la parte que consume `decidir.py`)

```
POST.esperar_data ──edad_max_dias(_FACT_VENTAS)=2──▶ POST.decidir
POST.decidir ── decision=ESCALAR ──▶ POST.surfing_20   (operador/MCP: +20 %, 1 vez/día)
             ── decision=RENOVAR ──▶ POST.brief_renovacion (etapa-10 → etapa-9)
             ── decision=PAUSAR  ──▶ POST.pausar        (operador/MCP)
             ── decision=SEGUIR_MIDIENDO ──▶ POST.esperar_data
POST.* ──▶ SI angulo ganador por VENTA y nodo=F1 ──▶ F2.etapa-11 (PASO 0 de fase-2)
       ──▶ SI concepto gana 2 de 2 y nodo=F2 ──▶ F3.etapa-3
```

Los estados por ángulo (`en_prueba → escalando → sostenido → en_declive → apagado → regenerado`) que
diseña la sesión 2 **son los estados de este sub-grafo**. Interfaz acordada: sesión 2 escribe
`_ESTADO_ANGULOS.csv` (o el nombre que decida) y `decidir.py --json`; `flujo.py` los lee como
predicados `csv_campo` / `json_campo`. Ninguna de las dos sesiones toca el archivo de la otra.

### 3.7 Lo que cambia en las skills y en `CLAUDE.md`
- `fase-1-angulos`, `fase-2-conceptos`, `fase-3-escalado`, `ciclo-diario` quedan **delgadas**: "corré
  `flujo.py [producto]` y ejecutá el nodo que diga". Sus gates en prosa se mueven al JSON. La doctrina
  del **cómo** de cada etapa sigue en su `ETAPA-*.md`, intacta.
- La pregunta inicial "¿En qué fase estás hoy?" **desaparece**: el flujo sabe la fase por la data.
  Queda solo para FASE 0 (producto nuevo sin fila en `_DIM_PRODUCTOS.csv`).
- La app gana una vista `flujo` declarada en `_MANIFIESTO.json` (fuente `PRODUCTOS/_FLUJO_ESTADO.json`,
  generador `flujo.py --todo --json`): "estás acá · esto bloquea · esto sigue", más el grafo en mermaid
  renderizado desde el mismo JSON.

### 3.8 Cómo se congela (para que no vuelva a variar)
- `Ads/_TOOLS/test_flujo.py` — fixtures con la data del 08-sep y los cuatro hallazgos como
  aserciones; y una transición por nodo. Mismo rol que `test_decidir.py`.
- Hook `PostToolUse` sobre `_FLUJO.json` → `flujo.py --validar` (bloquea si un ejecutor no existe o
  un predicado está mal formado).
- `gen_grafo.py --comparar` antes y después: el arranque en frío y el techo por fase tienen que
  **bajar**, porque la prosa de gates sale de las skills.

---

## 4. QUÉ SE ADELGAZA O SE RETIRA (con evidencia)

| Qué | Evidencia | Acción propuesta |
|---|---|---|
| `Ads/_TOOLS/decidir_operativo.py` | wrapper de 15 líneas; `grep -rl` no encuentra ningún llamador fuera de sí mismo | **retirar** a `_ARCHIVO/` |
| `.claude/worktrees/competent-rhodes-3ebc55/` | copia completa del repo (14 MB) dentro de `.claude/`; rama `claude/competent-rhodes-3ebc55` con `gen_dashboard.py` y `settings.local.json` modificados sin commit. Todo `grep -r` del sistema devuelve los hits duplicados | **preguntar**: si no es de una sesión viva, rescatar el diff de `gen_dashboard.py` y `git worktree remove`. Es la "tercera copia" que `gen_grafo` ya cazó dos veces |
| `PRODUCTOS/_DIM_CREATIVOS.csv.bak_20260908` y `.bak2_20260908` | backups a mano junto a la fuente de verdad; git es el respaldo | **retirar** después de commitear el `_DIM_CREATIVOS.csv` actual |
| Umbrales numéricos en prosa de `ETAPA-8.md` §B y `ESCALADO_PLAYBOOK.md` §6/§8 (35 % conv, PD 1×BE, +20 %, "máx 2 pausas") | `decidir.py` no conoce el 35 %; invariante 13 dice que ninguna orden sale sin `decidir.py` → **dos reglamentos** | mover a `_PARAMETROS_DECISION.csv` (con `dueno` y `por_que`), que `decidir.py` los lea, y que `verificar_guia_madre.py` los cubra. ETAPA-8 pasa a **consumir** `_DECISIONES.json` y ordenar palancas, no a recalcular |
| `ETAPA-7.md` (20 KB) | calcula CPA, ranking y fatiga que `decidir.py` + dbt ya calculan; ningún agente lee `_DECISIONES.json` | reducir a lector de **frescura y anomalías de entrega** (lo que el motor no mira) |
| `README.md` | dice "16 etapas / 7 skills"; hay 17 y 10 | corregir al implementar (es el único doc que cuenta a mano) |
| `_DIM_PRODUCTOS.fase` | texto libre escrito a mano | pasa a derivarse de `_ESTADO_FLUJO.csv` |

No se toca: doctrina de los mentores, `decidir.py` (salvo leer los parámetros nuevos), los CSV de
hechos, `gen_publicacion.py`, `gen_lanzador.py`, la app.

---

## 5. PLAN EN OLAS (cada una cierra con `gen_grafo.py --comparar` y tests en verde)

| Ola | Entrega | Cómo se prueba |
|---|---|---|
| **A** | `FLUJO/_FLUJO.json` con los ~30 nodos de las 3 fases + post-lanzamiento, y `flujo.py --validar` | el JSON referencia solo ejecutores y archivos que existen |
| **B** | Predicados + `flujo.py [pk]` / `--todo` / `--json` | `test_flujo.py` reproduce los 4 hallazgos del 08-sep sobre TINNIDROP y el estado real de los otros 7 productos |
| **C** | `_ESTADO_FLUJO.csv`, `--avanzar`, evento `TRANSICION_FLUJO`, vista `flujo` en la app | la app muestra el nodo de cada producto sin que nadie lo escriba |
| **D** | Skills delgadas + `CLAUDE.md` sin la pregunta inicial + umbrales de prosa a `_PARAMETROS_DECISION.csv` | `gen_grafo --comparar` con arranque en frío y techos por fase **menores**; `verificar_guia_madre.py` en verde |
| **E** | Limpieza de la tabla §4 | `gen_grafo --estricto` exit 0 |

La ola B es la que vale: si el flujo no caza el 08-sep solo, el resto es decoración.

---

## 6. PREGUNTAS ABIERTAS (cambian el diseño; no se asumen)

1. **¿El flujo puede EJECUTAR en Meta por MCP cuando el gate pasa** (pausar, +20 %, activar), o
   solo dicta y el operador ejecuta? Hoy `ETAPA-8.md` dice "NUNCA toca entidades vivas", pero
   `publicar-meta` ya crea y el 08-sep se pausó por MCP. Propuesta: el runner dicta; la sesión
   ejecuta por MCP **solo con confirmación explícita por orden**, y toda ejecución la verifica
   `verificar_publicacion.py --snapshot` después. Nada automático sin que el operador vea la orden.
2. **¿Se elimina la pregunta inicial "¿En qué fase estás hoy?"** y el flujo detecta la fase desde
   la data? Propuesta: sí; queda solo para producto nuevo sin fila.
3. **¿Se mueven a `_PARAMETROS_DECISION.csv` los umbrales que hoy viven en prosa** (35 %, PD 1×BE,
   +20 %, máx 2 pausas) y `ETAPA-8` pasa a consumir `_DECISIONES.json`? Es lo que cierra los "dos
   reglamentos". Propuesta: sí, con `verificar_guia_madre.py` cubriéndolos.
4. **El worktree `.claude/worktrees/competent-rhodes-3ebc55/`**: ¿es de una sesión viva? Tiene
   `gen_dashboard.py` modificado sin commit. Si no, se rescata ese diff y se retira.
