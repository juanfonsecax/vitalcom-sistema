# SISTEMA VITALCOM GUATEMALA — Mapa del sistema

Sistema de agentes (Claude Code) para crear, lanzar y **escalar** productos de dropshipping en Guatemala,
en **tres fases**: **ÁNGULOS (FASE 1)** → **CONCEPTOS (FASE 2)** → **ESCALADO (FASE 3)**, con un
**ciclo de optimización diario** y una **línea de producción de creativos** encima.

| Fase | Qué mide | Estructura | Variable que se mueve |
|---|---|---|---|
| 1 · ÁNGULOS | el ángulo | 6 conjuntos · ABO | el `angulo_key` (concepto fijo) |
| 2 · CONCEPTOS | el creativo | `1-1-5 + 1-1-5 + 1-2-5` · ABO | la ejecución visual (ángulo y copy fijos) |
| 3 · ESCALADO | volumen | `1-1-7` → `1-7-7` | ninguna: compra tráfico |

> Reestructurado el **2026-09-02** a partir de las clases del 16 y 22 de agosto. La doctrina de los
> mentores, con su fecha y su estado, vive en `_CONOCIMIENTO/MATRIZ_METODOLOGIA.md`.

> Empezá siempre por `CLAUDE.md` (el orquestador). Este README solo explica dónde vive cada cosa.
>
> **Desde el 09-sep-2026 el flujo está DECLARADO**: `DOCTRINA/FLUJO.json` es el grafo de pasos y gates,
> `python Ads/_TOOLS/flujo.py --todo` dice en qué fase y nodo está cada producto, qué lo bloquea y qué sigue.
> La fase ya no se pregunta: se deriva de la data.

---

## Cómo se conecta (vos ↔ el sistema)

**El sistema es el cerebro (estrategia); vos las manos y los ojos** (detalle en `_OPERADOR/MI_FUNCION_OPERADOR.md`).

1. **Vos das la materia prima:** producto (un problema/dolor fuerte y específico) + transcripciones en `Ads/1.2 Transcripcion videos/[PRODUCTO]/` (mínimo 6, ideal ~20) + 4 inputs (nombre, costo Q, dosis, foto del frasco).
2. **El sistema corre FASE 1** y te deja el paquete en `PRODUCTOS/[PRODUCTO]/` + (si hay MCP) el esqueleto de campaña real en Meta **en PAUSED**.
3. **Vos ejecutás lo manual** (según `1_HACER_MANUAL.txt`): generás las imágenes, subís los assets a Meta, configurás el LucidBot y **activás la campaña a las 4 AM** (nada se lanza solo).
4. **El sistema se encarga del post-lanzamiento:** cada mañana la tarea programada recorre `PRODUCTOS/_PORTAFOLIO.txt`, lee las métricas y entrega el **PLAN DE ESCALADO** (ETAPA-7). Vos ejecutás; el sistema nunca toca campañas vivas.
5. **Vos leés el `_DASHBOARD.html`** — es la capa humana: ganancia, «Qué tenés que hacer», P&L y ranking por ángulo. Se **genera** desde los CSV, nunca se escribe a mano.

---

## Mapa de carpetas

| Ruta | Qué es | ¿Lo lee el flujo? |
|---|---|---|
| `CLAUDE.md` | **Cerebro / orquestador.** Detecta la fase, invoca los subagentes en orden y transfiere outputs. Se carga cada sesión — por eso se mantiene delgado: coordina, no guarda doctrina de detalle. | ✅ Siempre |
| `.claude/agents/` | Las **17 etapas** `ETAPA-*.md` (PRODUCTO, 0, 1, 1B, 2, **3** microángulos, 4, 5, 6, 7, 8, **9** fábrica de conceptos, **10** lector concepto↔métrica, **11** optimizador de flujo, FANPAGE, GUARDAR-PRODUCTO). Todas con `model: inherit`. | ✅ Vía Task |
| `.claude/skills/` | Las skills: `buscar-producto` (FASE 0) · `fase-1-angulos` · `fase-2-conceptos` · `fase-3-flujo` · `fase-4-escalado` · `ciclo-diario` (auditoría diaria) · `generar-conceptos` · `find-skills`. **La doctrina de cada fase vive acá, no en `CLAUDE.md`.** | ✅ Al invocar |
| `DOCTRINA/` | **Los 15 documentos dueños.** Los agentes los leen **por ruta** durante el flujo. Movidos de la raíz el 2026-09-03; si alguno se mueve otra vez, `python Ads/_TOOLS/gen_grafo.py` canta las referencias que quedaron colgando. | ✅ Bajo demanda |
| ├ `COPYWRITING_ADS.md` | **Dueño único del COPY**: HPPPC, banco de hooks, anti-muro, título/descripción, compliance, precio. La usa ETAPA-4. | ✅ |
| ├ `PLANTILLAS_ADS.md` | **Dueño único del CREATIVO**: Prompt Maestro, 15 estilos anti-fatiga, compliance Andrómeda y la **DOCTRINA DE CREATIVOS** (video vs imagen). | ✅ |
| ├ `PLANTILLAS_INFOGRAFIAS.md` | Infografías del bot (Info 1/2/3 + imagen 4). | ✅ |
| ├ `PLANTILLAS_DEFAULTS_OPERADOR.md` | Valores base cuando el operador no entrega un dato. | ✅ |
| ├ `MCP_PLAYBOOK.md` | Creación de campañas y lectura de métricas vía Meta Ads MCP. | ✅ |
| ├ `ESCALADO_PLAYBOOK.md` | **El QUÉ del escalado**: palancas, timing, Presupuesto de Decisión y los **umbrales de métricas de testeo** (§8). | ✅ |
| ├ `CALENDARIO_ESCALADO.md` | **El CUÁNDO**: ritmo día a día con gates de decisión + regla del multi-ganador. | ✅ |
| ├ `DATA_PLAYBOOK.md` | **El CON QUÉ**: roles de cada CSV, cómo leerlos sin sacar cifras falsas, fórmula de ganancia, break-even, mapa de carpetas y el dashboard. | ✅ |
| ├ `MODULO_INTELIGENCIA_PRODUCTO.md` | El núcleo de investigación, **agnóstico al canal** (avatar, ángulo, voz del cliente). Exportable a otro canal. Lo usa `buscar-producto`. | ✅ |
| ├ `ETAPA-RESEARCH.md` | Módulos opcionales de investigación (web / Ad Library). | ✅ |
| ├ `ETAPA-RECOLECCION.md` | Fase manual de recolección de creativos (prompt de Gemini). | ✅ |
| `Ads/` | **Insumos y media.** `1.1 Videos/` + `1.2 Transcripcion videos/` por producto · `MEDIA_*/` (assets lavados listos para Meta) · `_TOOLS/` (scripts + `LAVADO.md`). | ✅ Por ruta |
| `PRODUCTOS/[NOMBRE]/` | **Output por producto.** `1_HACER_MANUAL.txt` (lo que ejecutás) + `2_DATA_PRODUCTO.txt` (memoria) + `3_CAMPAÑA_META.txt` (IDs de Meta) + `4_PLAN_ESCALADO.txt` (FASE 3). Nada más. | ✅ Por ruta |
| `PRODUCTOS/*.csv` | **Capa de data (máquina).** `_FACT_VENTAS` (la única que suma al P&L) · `_FACT_ENTREGA` · `_DIM_*` · `_EVENTOS` · `_APRENDIZAJES`. Roles y reglas en `DOCTRINA/DATA_PLAYBOOK.md`. | ✅ Diario |
| `PRODUCTOS/_DASHBOARD.html` | **Capa humana.** Lo único que abrís a diario. Se genera con `python Ads/_TOOLS/gen_dashboard.py`. | 👤 Vos |
| `PRODUCTOS/_PORTAFOLIO.txt` | **Registro maestro multi-producto.** La auditoría diaria lo recorre y audita cada producto VIVO. Acá se "agrega un producto al tracking". | ✅ Diario |
| `PRODUCTOS/_AUDITORIAS/` | Informes fechados (auditorías nocturnas, planes multi-producto). Registro legible — **las métricas NO se reconstruyen desde acá**, salen del CSV. | 🔎 Consulta |
| `C:\Users\juand\Documents\VITALCOM_CLASES\` | Clases consolidadas (1–22), **fuera del repo** (T9, 22-sep-2026). Referencia humana para auditar y construir — regla: número mayor = más reciente = manda. No es "base de verdad" del sistema: el sistema no la lee. | 🔎 Consulta (fuera del repo) |
| `_OPERADOR/` | Docs para el humano: `MI_FUNCION_OPERADOR.md` (qué hacés vos), `_PROMPT_AUDITORIA_GENERAL.md`, handoffs ya ejecutados. | ❌ |
| `_ROADMAP/` | **Backlog: lo NO implementado.** Ver su `README.md`. | ❌ |
| `_SKILLS_FUENTE/` | Fuente y paquetes de las 3 skills propias (3qs, analizador-creativos, monitor-pixel). Para instalar/editar, no para el flujo. | ❌ |
| `INFPRODUCTOS/` | Activos del infoproducto "Defienda su Salud EPS" (PDFs, plantillas). **Negocio aparte**, fuera del pipeline de dropshipping. | ❌ |
| `_RESPALDOS/` | Backups y derivados EN VIVO (`backups_csv/`, `procesados/`, ...), gitignored. Reemplaza a `_ARCHIVO/` (retirado del repo el 22-sep-2026, T9; su material histórico queda en el log de git). | ❌ (no versionado) |
| `.agents/` · `skills-lock.json` | Infraestructura de tooling de skills EXTERNAS. Solo puede contener lo declarado en `skills-lock.json` (hoy: `find-skills`, de vercel-labs/skills). **Ninguna skill del sistema vive acá** — las del sistema viven en `.claude/skills/`. Si aparece otra, es un polizón: borrarla. | ❌ |

---

## Flujo en una mirada

**FASE 0 (opcional) — Buscar producto:** skill `buscar-producto` → candidatos rankeados.

**FASE 1 — Pre-testeo:** `etapa-producto` → `etapa-0` → **[PASO 1.5 lavado de videos]** → `etapa-1` → `etapa-1b` → `etapa-2` (incluye la asignación de FanPage) → (`etapa-4` ∥ `etapa-5`) → `etapa-6` → `etapa-guardar-producto`

**FASE 2 — Post-testeo / Escalado:** `etapa-3` → (`etapa-4` ∥ `etapa-5`) → `etapa-6` → `etapa-guardar-producto`

**Ciclo de optimización (diario):** `decidir.py` (tabla determinística) → `etapa-7` (lee métricas y entrega el PLAN DE ESCALADO) → `etapa-10` (por qué ganó lo que ganó → brief) → `etapa-9` (produce ≥6 creativos) → anexar al CSV → **regenerar el dashboard** (último paso siempre).

**Optimización de flujo (al confirmar ángulo ganador, entre FASE 1 y FASE 2):** `etapa-11` mide el **CIERRE** (mensajes → ventas), separa el problema pre-clic del post-clic, audita la congruencia ad ↔ bot, lee los chats y entrega el brief a `etapa-5` + el **A/B de flujo** (paraguas optimizado vs dedicado al ganador, ruteado por Post ID). Es la palanca más grande que le queda al sistema: el cierre va en **8.6 %** contra el **15-20 %** de los mentores.

---

## Reglas de oro para mantener el orden

1. **Un dato, un dueño.** Cada regla y cada número viven en UN solo archivo; los demás lo referencian. Si un número está en un CSV, no se repite en prosa — dos fuentes de verdad para el mismo dato es drift garantizado.
2. **No mover ni renombrar** los docs de referencia de la raíz, ni `Ads/`, ni la estructura de `PRODUCTOS/[NOMBRE]/`: el flujo los cita por nombre/ruta.
3. **Un producto = una carpeta** con los archivos `1_`/`2_`/`3_`/`4_`. Nada de PNG, prompts sueltos ni subcarpetas: la media va a `Ads/MEDIA_[PRODUCTO]/` (Regla 16 de `CLAUDE.md`).
4. **`producto_key` es la llave.** Las carpetas del disco se resuelven leyendo `_DIM_PRODUCTOS.csv`, nunca adivinando por el nombre (el mismo producto tiene nombres distintos en las 4 ubicaciones).
5. **Lo retirado se saca del repo (`git rm`), no se marca como viejo ni se mueve a una carpeta muerta.** Un archivo marcado "SUPERSEDIDO" que se queda en su carpeta sigue costando lecturas y confunde; el historial de git ya guarda el contenido retirado (T9, 22-sep-2026 — antes vivía en `_ARCHIVO/`, hoy fuera del repo).
6. **Recencia:** entre clases, número mayor = más reciente = manda. La doctrina se ancla en las clases nuevas (22/20/19/15).
7. Antes de borrar algo, verificá que tenga **0 referencias** en `CLAUDE.md` y `.claude/agents/`. Lo dudoso se documenta acá como retirado (este README) antes de sacarlo.
