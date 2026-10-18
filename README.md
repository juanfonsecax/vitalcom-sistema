# SISTEMA VITALCOM (GUATEMALA Y COLOMBIA) — Mapa del sistema

Sistema de agentes (Claude Code) para crear, lanzar y **escalar** productos de dropshipping contra
entrega (COD) en Guatemala (GT) y Colombia (CO), en **cuatro fases**:
**ÁNGULOS (FASE 1)** → **CONCEPTOS (FASE 2)** → **FLUJO LUCIDBOT (FASE 3)** → **ESCALADO (FASE 4)**,
con un **ciclo de optimización diario** y una **línea de producción de creativos** encima.

| Fase | Qué mide | Estructura | Variable que se mueve |
|---|---|---|---|
| 1 · ÁNGULOS | el ángulo | 6 conjuntos · ABO · todo IMAGEN | el `angulo_key` (concepto fijo) |
| 2 · CONCEPTOS | el creativo | `1-1-5 + 1-1-5 + 1-2-5` · ABO | la ejecución visual (ángulo y copy fijos) |
| 3 · FLUJO LUCIDBOT | el cierre | sin estructura nueva en Meta | el flujo del bot (ángulo y concepto fijos) |
| 4 · ESCALADO | volumen | `1-1-7` CBO → `1-7-7` | ninguna: compra tráfico |

> Empezá siempre por `CLAUDE.md` (el orquestador). Este README solo explica dónde vive cada cosa.
>
> **Para explicarle el sistema completo a una IA que no tiene la carpeta:**
> `_OPERADOR/SISTEMA_COMPLETO_PARA_OTRA_IA.md` (negocio, fases, reglas, datos, auditoría).
>
> **El flujo está DECLARADO**: `DOCTRINA/FLUJO.json` es el grafo de pasos y gates, y
> `python Ads/_TOOLS/flujo.py --todo` dice en qué fase y nodo está cada producto, qué lo bloquea y
> qué sigue. La fase no se pregunta: se deriva de la data. La doctrina de los mentores, con su fecha
> y estado, vive en `_CONOCIMIENTO/MATRIZ_METODOLOGIA.md`.

---

## Cómo se conecta (operador ↔ sistema)

**El sistema es el cerebro (estrategia); el operador son las manos y los ojos.**

1. **El operador da la materia prima:** producto + mercado (GT/CO) + costo en su moneda + dosis + foto
   del frasco + **≥6 transcripciones** en `Ads/1.2 Transcripcion videos/[PRODUCTO]/` (ideal ~20).
2. **El sistema corre FASE 1** y deja el paquete en `PRODUCTOS/[PRODUCTO]/` (`1_HACER_MANUAL.txt` es la
   lista de lo manual). Si la cuenta tiene MCP, publica la estructura en Meta **en PAUSED**.
3. **El operador ejecuta lo manual:** genera/sube las imágenes, configura LucidBot, y **activa a las
   4 AM del día siguiente** (nada se lanza solo).
4. **Cada noche** el sistema baja ventas y gasto, corre el motor de decisión (`decidir.py`) y deja las
   órdenes. **Cada orden de pausar/escalar se ejecuta por MCP solo con la confirmación explícita del
   operador, orden por orden**, y se registra en `_EVENTOS.csv`.
5. **La pantalla del operador es la app web** (`app/`); `VISTAS/APP.html` es el respaldo generado sin
   servidor. `PRODUCTOS/_DASHBOARD.html` sigue generándose desde los CSV, nunca se escribe a mano.

Colombia corre en **modo manual**: el operador entrega los exports de Meta y LucidSales y la cuenta
es externa (sin MCP).

---

## Mapa de carpetas

| Ruta | Qué es | ¿Lo lee el flujo? |
|---|---|---|
| `CLAUDE.md` | **Cerebro / orquestador** + mapa de dueños + los 13 invariantes. Se carga cada sesión: coordina, no guarda doctrina de detalle. | ✅ Siempre |
| `AGENTS.md` | Puntero a `CLAUDE.md` para clientes que buscan ese nombre. | ✅ |
| `.claude/agents/` | Las **15 etapas** `ETAPA-*.md`: `producto`, `0`, `1`, `1B`, `2` (incluye FanPage), `3`, `4`, `5`, `6`, `7` (monitor + escalado), `9`, `10`, `11`, `guardar-producto`, `render`. 14 con `model: inherit`; `render` en sonnet. | ✅ Vía Task |
| `.claude/skills/` | `buscar-producto` (F0) · `fase-1-angulos` · `fase-2-conceptos` · `fase-3-flujo` · `fase-4-escalado` · `publicar-meta` · `recopilar-lucidsales` · `ciclo-diario` · `generar-conceptos` · `generar-imagenes-chatgpt` · `reglas-sistema`. **La doctrina de cada fase vive acá.** | ✅ Al invocar |
| `.codex/` · `.agents/skills/` | Copias de las etapas y skills para el cliente Codex. **La fuente es `.claude/`**; si difieren, manda `.claude/`. `skills-lock.json` declara solo la skill externa `find-skills`. | ❌ |
| `DOCTRINA/` | Los documentos dueños de cada tema (copy, creativos, escalado, calendario, data, contabilidad, flujo del bot, MCP…) + `FLUJO.json`. La tabla «MAPA DE ARCHIVOS» de `CLAUDE.md` dice cuál es cuál. | ✅ Bajo demanda |
| `Ads/` | Insumos y media. `1.2 Transcripcion videos/` por producto · `MEDIA_*/` (assets listos para Meta) · `_INGESTA/` (snapshots de Meta, exports) · `_SWIPE/` (banco de creativos y blueprints) · `_TOOLS/` (scripts y sus tests). | ✅ Por ruta |
| `Ads/_TOOLS/` | Lo **determinista**: `costear.py` · `decidir.py` · `flujo.py` · `gen_lanzador.py` / `gen_publicacion.py` / `gen_plan.py` / `gen_manual.py` / `gen_flujo_bot.py` · `registrar_evento.py` · `ingerir_*` / `bajar_*` · `verificar_*` · `gen_grafo.py`. | ✅ |
| `PRODUCTOS/[NOMBRE]/` | Output por producto: `1_HACER_MANUAL.txt` + `2_DATA_PRODUCTO.txt` + `3_CAMPAÑA_META.txt` + `4_PLAN_ESCALADO.txt` + `_PLAN*.json`, `BLOQUES_BOT.md`, `INFOGRAFIAS.md`. | ✅ Por ruta |
| `PRODUCTOS/*.csv` | **Capa de datos.** `_DIM_*` (dimensiones) · `_FACT_*` (hechos) · `_PARAMETROS_*` · `_EVENTOS` · `_ESTADO_FLUJO` · `_DECISIONES.json`. Roles en `DOCTRINA/DATA_PLAYBOOK.md`. Se editan con un escritor CSV, nunca a mano. | ✅ Diario |
| `PRODUCTOS/_AUDITORIAS/` | Informes fechados (por mes). Registro legible: **las métricas NO se reconstruyen desde acá**, salen del CSV. | 🔎 Consulta |
| `db/` | Postgres local: `raw` (espejo verbatim) y `core` (modelo normalizado). Es la **verdad** de 5 tablas (producto, estado_flujo, venta, entrega_conjunto_dia, entrega_anuncio_dia) y de los eventos y decisiones; el CSV es el espejo. Ver `db/README.md`. | ✅ |
| `warehouse/` | Capa analítica dbt + DuckDB (tests de integridad, linaje, métricas). Lee los CSV, no los escribe. | ✅ |
| `app/` | App web del operador: `backend` (FastAPI) y `frontend` (React). Lee contratos y dispara los ejecutores declarados en `VISTAS/_MANIFIESTO.json`; no escribe CSV. | ✅ |
| `VISTAS/` | HTML generados (`APP.html`, `FLUJO.html`, `HOY.html`, `LANZADOR.html`, `PERFILES.html`) + `_MANIFIESTO.json` / `_ESTADO.json`. Se abren, no se leen. | 👤 Operador |
| `evals/` | Baseline de evals por etapa (requisito para podar prosa de las etapas). Ver `evals/README.md`. | ✅ |
| `odd/tasks/` | Documentos de feature del flujo de desarrollo (tareas, evidencia de commits). | ❌ |
| `_OPERADOR/` | Docs para el humano: `SISTEMA_COMPLETO_PARA_OTRA_IA.md`, `MI_FUNCION_OPERADOR.md`, guías, hojas de ruta, handoffs. | ❌ |
| `_CONOCIMIENTO/` | Matriz de metodología y postmortems. Consulta humana. | ❌ |
| `_ROADMAP/` | Backlog: lo NO implementado. Ver su `README.md`. | ❌ |
| `_SKILLS_FUENTE/` | Fuente y paquetes de las skills propias (3qs, analizador-creativos, monitor-pixel). | ❌ |
| `INFPRODUCTOS/` | Activos del infoproducto «Defienda su Salud EPS». **Negocio aparte.** | ❌ |
| `_RESPALDOS/` | Backups y derivados EN VIVO, gitignored. | ❌ (no versionado) |

---

## Flujo en una mirada

**FASE 0 (opcional) — Buscar producto:** skill `buscar-producto` → candidatos rankeados.

**FASE 1 — Ángulos:** `etapa-producto` → `etapa-0` → `etapa-1` → `etapa-1b` → `etapa-2` (incluye FanPage) →
(`etapa-4` ∥ `etapa-5`) → `etapa-6` → `etapa-guardar-producto` → publicar (PAUSED) → activar 4 AM.
Todo IMAGEN; los videos de competencia son fuente del ángulo, nunca el creativo.

**FASE 2 — Conceptos:** (`etapa-11` diagnostica en paralelo) → `etapa-9` fabrica los 10 conceptos →
`etapa-render` → (`etapa-4` ∥ `etapa-5`) → `etapa-6` → publicar. Gana el concepto que queda arriba en
**2 de 2** apariciones.

**FASE 3 — Flujo LucidBot:** `etapa-5` reescribe los bloques de juicio a partir del brief de `etapa-11`;
el operador aplica el cambio en LucidBot y registra `CAMBIO_BOT`. Se mide el cierre; no se escala
hasta superar `cierre_min_escalar_pct` con ≥30 mensajes.

**FASE 4 — Escalado:** `etapa-3` (microángulos) → `etapa-6` (1-1-7 CBO) → publicar; palancas: Post ID,
multicuenta, multifanpage; exploración de 3 ángulos nuevos en paralelo (mini-F1).

**Ciclo diario:** recolección nocturna (LucidSales + Meta) → `decidir.py` (tabla determinística) →
`etapa-7` (palancas) → `etapa-10` (por qué ganó) → `etapa-9` (≥6 creativos/día) → órdenes confirmadas
una a una → `registrar_evento.py`.

---

## Reglas de oro para mantener el orden

1. **Un dato, un dueño.** Cada regla y cada número viven en UN solo archivo; los demás lo referencian.
2. **Lo determinista va en código y CSV, no en prosa.** Costos, break-even, nombres, presupuestos, gates
   y órdenes salen de scripts; las etapas aportan escritura y juicio.
3. **La fase la dice la data** (`flujo.py`), no el operador ni la bitácora de `_DIM_PRODUCTOS.fase`.
4. **Nada se ejecuta en Meta sin confirmación humana** y todo nace PAUSED; el CSV no es evidencia del
   estado de Meta: se pregunta a Meta (snapshot) antes de crear.
5. **Un producto = una carpeta** con sus archivos por rol; la media va a `Ads/MEDIA_[PRODUCTO]/`.
6. **`producto_key` es la llave.** Las carpetas se resuelven leyendo `_DIM_PRODUCTOS.csv`, nunca por el
   nombre.
7. **Lo retirado se saca del repo (`git rm`)**, no se marca como viejo: el historial de git lo guarda.
8. Antes de borrar algo, verificá que tenga **0 referencias** en `CLAUDE.md`, `.claude/` y
   `DOCTRINA/FLUJO.json` (`python Ads/_TOOLS/gen_grafo.py` canta rutas muertas y huérfanos).
