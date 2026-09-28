# Feature: cuatro-fases (Block B)

Worktree: `.claude/worktrees/cuatro-fases` · branch `feat/cuatro-fases` (from feat/dashboard-visual d7eb8d1).
The live folder `SISTEMA` keeps running the nightly cycle untouched until merge.

## Objective
Move from 3 to 4 phases:
- F1 ÁNGULOS (unchanged) · F2 CONCEPTOS (unchanged)
- **F3 OPTIMIZACIÓN DE FLUJO LucidBot (new)**: the validated angle + concept keep running at the same
  budget while the bot flow is adapted to that angle (etapa-11 diagnoses, etapa-5 rewrites, operator
  applies and logs CAMBIO_BOT). Doctrine: Clase 22-ago Calet (PALANCA_1 propuestas de valor,
  DIAGNOSTICO_1 congruencia anuncio↔flujo, changes measured in hours).
- **F4 ESCALADO** (= today's F3, incl. F3.exploracion → F4.exploracion).

## Why
Operator decision 2026-09-28. The flow rewrite already exists as the CAMBIO_BOT gate at today's
F3.entrada; making it a phase makes the step visible and enforces the hard rule
PROHIBIDO_ESCALAR_CIERRE_BAJO (no scaling under 10% close), which no script enforces today.

## Gates (operator-approved criterion)
- F3.entrada = today's F2→F3 concept gate (concept winner 2 of 2). No CAMBIO_BOT required to enter.
- F4.entrada = (a) CAMBIO_BOT (or EXCEPCION_CAMBIO_BOT) dated after the concept winner, AND
  (b) ≥ 30 messages received after that CAMBIO_BOT (`min_mensajes_cierre`), AND
  (c) close rate over those messages ≥ 10% (new parameter, owner `_PARAMETROS_DECISION.csv`,
  source GUIA_MADRE PROHIBIDO_ESCALAR_CIERRE_BAJO). 15–20% (`cierre_meta_min_pct`/`max`) is shown as
  benchmark only, never blocks. Below 10% → stays in F3 for another flow iteration.
- decidir.py: F3 joins FASES_EN_TESTEO (no budget raise until F4).

## Constraints
- Deterministic gates in flujo.py/FLUJO.json; decisions via decidir.py; one data owner; CSVs via csv writer.
- Invariant numbers in CLAUDE.md never renumbered (text of #1 updated for the new phase).
- Doctrine states the current rule, no history notes.
- Never commit PRODUCTOS live data churn; `_ESTADO_FLUJO.csv`/`_DECISIONES.json` regenerate after merge.
- Commits: Conventional, English, no Co-Authored-By, one work unit per task.
- TDD: not configured (ordinary checks).

## Tasks
- [x] B1 Engine: FLUJO.json nodes (new F3 flujo, F3→F4 rename), flujo.py predicates + gate_entrada 1-4,
      decidir.py FASES_EN_TESTEO + phase texts, parameters CSVs, gen_publicacion/registrar_evento, tests.
      (route: delegated writer)
- [x] B2 Doctrine: CLAUDE.md, CALENDARIO_ESCALADO.md, GUIA_MADRE rows, skills (new fase-3-flujo,
      fase-3-escalado → fase-4-escalado), affected ETAPA-*.md pointers, verificar_guia_madre green.
      (route: delegated writer)
- [ ] B3 App: backend endpoints (fase3 = flujo, fase4 = escalado), frontend screens/tabs/lenguaje, tests, e2e.
      (route: delegated writer)
- [ ] B4 Integration: run flujo.py/decidir.py read-only against a copy of the live data, full test
      suites, report to operator before merge. (route: parent + per-action workers)

## Acceptance
- flujo.py places CLEARSTEM/NUSAVA/TINNIDROP in F2, OVULOS_PURITY in F1, same as today.
- A product with a 2-of-2 winner enters F3; enters F4 only with the 3 conditions.
- App shows 4 phases; F3 screen shows close rate after the bot change vs the 10% gate and 15-20% benchmark.

## Progress / evidence

### B1 (done, 28-sep-2026)

**FLUJO.json**: new `F3` phase (`titulo`: "FASE 3 · OPTIMIZACIÓN DE FLUJO LUCIDBOT"), entrada =
`concepto_2de2` only (moved from old `F3.entrada`, minus the CAMBIO_BOT requirement). Nodes
`F3.reescribir` (etapa-5 drafts, operator applies CAMBIO_BOT/EXCEPCION_CAMBIO_BOT) and
`F3.medir_cierre` (script `gen_decisiones.py`, no separate gate — the ciclo already recomputes
it). `F3.salida.a = "F4"`, gate = new `cierre_post_cambio_bot` predicate. Old `F3` renamed to `F4`
("FASE 4 · ESCALADO"): nodes `F3.exploracion/plan/publicar` → `F4.exploracion/plan/publicar`.
`F4.entrada` = concepto_2de2 AND (CAMBIO_BOT|EXCEPCION_CAMBIO_BOT posterior al ganador) AND
`cierre_post_cambio_bot` (≥30 mensajes, cierre ≥10%). `F2.etapa-11` untouched (still diagnosis-only
in F2). `flujo.py --validar`: 4 fases, 26 nodos, sin problemas.

**flujo.py**: new predicate `cierre_post_cambio_bot` (registered in `TIPOS`/`_EVALUADORES`) —
counts mensajes/ventas from `_FACT_VENTAS.csv` (`_ventas_base()`, same rows `decidir.py` uses)
filtered to `ventana_ini` strictly after the current CAMBIO_BOT/EXCEPCION_CAMBIO_BOT (new resolver
`_fecha_cambio_bot`, registered in `RESOLVEDORES_FECHA`, itself anchored after `_fecha_concepto_
ganador` so a stale/old CAMBIO_BOT never counts). **Grain: PRODUCTO, not angulo_key** — in F3/F4
the angle+concept are already fixed to a single winner (invariante 1), so a product-level cut
after the CAMBIO_BOT date is the same population the angle-level cut would give; stated explicitly
in the docstring. `TOKEN_FASE` updated: fase "3" has no campaign token (no new structure), fase
"4" keeps `ESCALA`/`EXPLORA`. `gate_entrada(pk, fase)` needed **no code change** — it already
builds `"F%s" % fase` generically, so 1-4/F1-F4 just works once FLUJO.json has F4. `EXCEPCION_
CAMBIO_BOT` semantics made explicit: it skips only the CAMBIO_BOT/reescritura requirement (a); if
used, messages/cierre for (b)/(c) are measured from the exception's own date (same resolver).
`reingreso` (F1) re-checked on both F3 and F4 — unchanged logic, still generic over the fases list.

**Parameters**: `PRODUCTOS/_PARAMETROS_DECISION.csv` — added `cierre_min_escalar_pct,10,porcentaje,
DOCTRINA/GUIA_MADRE_PARAMETRIZADA.md,...` (real `csv.writer`, invariante 11). Added to `decidir.
cargar_parametros()` defaults too. `_PARAMETROS_PUBLICACION.csv` — the two `fase=3` rows (UNICO
1-1-7, EXPLORACION 3-1-1) renumbered to `fase=4`; F3 (flujo) publishes no new structure. Postgres
mirror (`raw.parametros_decision`/`raw.publicacion_...`): these two CSVs are **source-of-truth**,
loaded into Postgres as a full snapshot (TRUNCATE+INSERT) each run — not the other direction (see
`db/README.md` §"gate de paridad" and `db/tables.py` `("parametros_decision", ..., False)`). No
merge-time DB action needed beyond the ordinary next ingest/read; nothing to migrate.

**decidir.py**: `FASES_EN_TESTEO = ("F1","F2","F3")` (F3 now testeo — escalar there would buy
volume before the bot's rewrite is confirmed to close). `aplicar_gate_fase()` gained an optional
`params` arg (default `{}`, backward compatible) to pull `min_mensajes_cierre`/`cierre_min_
escalar_pct` into the bloqueo_fase text instead of hardcoding; call site passes the already-loaded
`params`. New F3 text: unlocked by CAMBIO_BOT + ≥30 mensajes + cierre ≥10%, which moves to F4.
Updated F2 text: unlocked by 2-of-2, moves to F3 (not "F3=escalado" anymore).

**Doctrine touch (minimal, B2 will do the full pass)**: `DOCTRINA/GUIA_MADRE_PARAMETRIZADA.md` —
appended `cierre_min_escalar_pct` to the existing `PROHIBIDO_ESCALAR_CIERRE_BAJO` row's dueño
column (drift gate in `verificar_guia_madre.py` requires every `_PARAMETROS_DECISION.csv` key to
be named somewhere in the doc); did **not** touch CLAUDE.md/CALENDARIO_ESCALADO.md/skills — that's
B2's job per the split above.

**Other files swept for `"F3"`/`fase 3`/`--fase 3` (grep across Ads/_TOOLS, db, warehouse, evals)**:
`gen_publicacion.py` (`fase==4` dispatch, `F4.exploracion`, campaign-name fase-4 branch, docstrings);
`gen_plan.py` (`NOMBRES_PLAN` key `3→4` — filename `_PLAN_FASE3.json` kept as-is, only the internal
`"fase"` value moves to 4 — see note below; `validar()` dispatch `fase in (2,4)`; `F3.exploracion`→
`F4.exploracion` throughout); `gen_lanzador.py` (`ESTRUCTURA` dict key `3→4`, `presupuesto_fase_csv`
docstrings — reads generically from the CSV, no other change needed); `registrar_evento.py` (no
functional change — `resolver_fase()` already reads `flujo.TOKEN_FASE` generically; only docstring
examples updated); `VISTAS/_MANIFIESTO.json` (renamed the 3 action ids `nodo.F3.exploracion/plan/
publicar` → `nodo.F4.*`; added two new action entries `nodo.F3.reescribir` (subagent etapa-5) and
`nodo.F3.medir_cierre` (script `gen_decisiones.py`) so `gen_app.py`'s V6 gate — every FLUJO.json
node needs exactly one action — stays green; kept minimal/mechanical, full UI/UX polish is B3).
`db/` and `warehouse/` had **no** F3/fase-3 hits. `evals/` — left the frozen `etapa-8/TINNIDROP.txt`
fixture untouched (historical record of a past agent output, `etapa-8` doesn't exist anymore per
CLAUDE.md's 15 stages, already marked "histórico" in `promptfooconfig.yaml`); fixed one live
pointer in `evals/README.md` (`F3.plan`→`F4.plan`).

**Known compromise, flagged for B2/B3 review**: the escalado plan file keeps its historical name
`PRODUCTOS/{slug}/_PLAN_FASE3.json` even though it's now FASE 4's plan (only the JSON's internal
`"fase"` field changed 3→4, checked by `FLUJO.json`'s `F4.plan` predicate and `gen_plan.py`).
Renaming the file itself would ripple into more consumers than this task's scope justified;
documented in `FLUJO.json`'s `F4.plan.produce[0].dato` and in `gen_publicacion.py`'s docstring.

**Tests updated** (same file, new/renamed cases, no coverage dropped): `test_gate_entrada.py`
(F3 now passes without CAMBIO_BOT; F4 split into 3 new cases: no-CAMBIO_BOT / CAMBIO_BOT-without-
cierre / CAMBIO_BOT-with-cierre — the last one is the first real exercise of `cierre_post_cambio_
bot`), `test_flujo.py` (H/H2 sections repointed from `F3.entrada` to `F4.entrada`; new section K
asserts F3's node set and its salida→F4; J section renamed F3.exploracion→F4.exploracion), `test_
decidir.py` (`test_gate_fase` gained the F3 case, F2/F4 texts updated, total bumped 30→31),
`test_gen_publicacion.py` (whole F3.exploracion fixture block renamed to F4, `_fixture_f3_
exploracion_base` now also seeds a post-CAMBIO_BOT sales row so `gate_entrada(pk,4)` passes),
`test_registrar_evento.py` (ESCALA/EXPLORA token tests now expect fase "4"), `test_gen_plan.py` /
`test_gen_lanzador.py` (fase 3→4 in fixtures and node names).

**Verification (all green, worktree vs base commit d7eb8d1, compared via a temporary detached
`git worktree` under the scratchpad, since removed)**:
- `python -m pytest Ads/_TOOLS -q` → **48 passed** in both worktrees (was 42 passed/6 failed in
  the worktree before the test-file fixes above; base/untouched HEAD is also 48/48 — the task's
  "known pre-existing failures" (`test_decidir.py` params-fixture errors, `test_gen_ordenes.py`
  I/O-on-closed-file) only appear when pytest is pointed at those files' internal classes/
  functions directly (`pytest file.py::test_x`), not through the canonical `pytest Ads/_TOOLS -q`
  collection used here — reproduced identically on the untouched base, confirmed pre-existing and
  unrelated to this change).
- `python Ads/_TOOLS/flujo.py --validar` → `DOCTRINA/FLUJO.json válido: 4 fases, 26 nodos, 1
  excepciones. Cada ejecutor y cada archivo citado existen.`
- `python Ads/_TOOLS/flujo.py --todo` (read-only) → CLEARSTEM/NUSAVA/TINNIDROP in F2, VARICOSE
  PAUSADO, OVULOS_PURITY in F1 — **byte-identical** to the same command on the base worktree.
- `python Ads/_TOOLS/verificar_guia_madre.py` → `Sin fallas: cada valor declarado coincide con su
  ejecutor y todo puntero existe.`
- `python Ads/_TOOLS/hook_csv.py --barrido` → exit 0, no output.
- Confirmed no PRODUCTOS live-data churn survived: `gen_lanzador.py --json` (run as a smoke test)
  regenerated `PRODUCTOS/_LANZADOR.json`; reverted with `git checkout --` before finishing (per
  the "never commit PRODUCTOS live data churn" constraint). `_ESTADO_FLUJO.csv`/`_EVENTOS.csv`/
  `_DECISIONES.json` were never touched (no `--escribir` flag used anywhere in this session).

**Left for B2**: CLAUDE.md invariant #1 text (still says "FASE 3" for escalado in a few places —
renumber prose, not the invariant number itself), CALENDARIO_ESCALADO.md, new skill `fase-3-flujo`
+ rename `fase-3-escalado`→`fase-4-escalado`, ETAPA-*.md pointers that say "Fase 3" meaning
escalado (ETAPA-2, ETAPA-6, ETAPA-11), ETAPA-5.md pointer for its new F3.reescribir role.

**Left for B3**: app/backend endpoints and app/frontend screens/tabs for the new 4-phase model
(fase3=flujo, fase4=escalado), including the F3 screen showing cierre_post_cambio_bot vs the 10%
gate and the 15-20% benchmark (both already computed/exposed by flujo.py's predicate and decidir.
py's `cierre_meta_min_pct`/`max_pct`); e2e tests.

**Left for B4**: full read-only run against a copy of live data before merge (this session already
did the base-vs-worktree comparison above on the real repo data, not a copy — B4 should still do
its own pass per the plan, especially once B2/B3 land).

### B2 (done, 28-sep-2026)

**Rename `_PLAN_FASE3.json` → `_PLAN_FASE4.json`** (no product had this file yet, confirmed by
grep before renaming): `Ads/_TOOLS/gen_plan.py` (`NOMBRES_PLAN`, docstrings, `descubrir_planes`
docstring — also dropped the now-stale "nombre historico de cuando esta fase era F3" prose since
the file is actually renamed, not just relabeled internally), `gen_publicacion.py`,
`cargar_pieza.py`, `test_gen_plan.py`, `DOCTRINA/FLUJO.json` (`F4.plan.produce`, dropped the
matching stale "nombre de archivo histórico" prose), `app/backend/vitalcom_app/contratos.py` (2
string literals), `evals/asserts/etapa-guardar-producto.py`, `.claude/agents/ETAPA-6.md`. Left
`odd/tasks/g07-cimientos.md` untouched (history) and `evals/fixtures/etapa-guardar-producto/
TINNIDROP.json`'s `_PUBLICACION_F3.json` entry untouched (unrelated filename pattern — a frozen
historical record of what actually existed on disk for that eval snapshot, same category as the
already-frozen `etapa-8` fixture B1 left alone).

**CLAUDE.md**: "tres fases" → "cuatro fases" (ÁNGULOS → CONCEPTOS → FLUJO LUCIDBOT → ESCALADO);
execution table gained FASE 3 (skill `fase-3-flujo`) and renumbered FASE 4 (skill
`fase-4-escalado`); ÁNGULO vs CONCEPTO block gained the F3 row (validated angle+concept, same
budget, variable = bot flow, mide el CIERRE) and MICRO-ÁNGULO pointer moved to (FASE 4); invariant
1 text gained "no entrar a FASE 4 sin cierre ≥ `cierre_min_escalar_pct` medido después del
`CAMBIO_BOT`" (invariant number untouched); the CIERRE pointer paragraph rewritten — diagnosis
stays in FASE 2 (`etapa-11`, `F2.etapa-11`), the rewrite is now its own phase FASE 3
(`F3.reescribir`, `etapa-5`), the gate that buys volume is `F4.entrada`, below the threshold the
product stays in FASE 3 for another iteration; "aritmética de las 3 fases" → "4 fases".

**New skill `.claude/skills/fase-3-flujo/SKILL.md`**: entry gate = today's F2→F3 concept-2de2 gate
(no CAMBIO_BOT required to enter — that's the work done inside this phase, not a precondition);
PASO 1 etapa-11 brief (reused if still fresh for the winner, re-run if not); PASO 2 etapa-5
rewrites the BLOQUES DE JUICIO per `PLANTILLAS_FLUJO_BOT.md` reglas A-G and GUIA_MADRE `PALANCA_1`
(propuestas de valor) / `DIAGNOSTICO_1` (congruencia); PASO 3 operator applies in LucidBot and logs
`CAMBIO_BOT`/`EXCEPCION_CAMBIO_BOT` via `registrar_evento.py` the same day; PASO 4 measures cierre
via the existing daily cycle (`gen_decisiones.py`, no separate script) against
`min_mensajes_cierre`/`cierre_min_escalar_pct`; exit gate = `F4.entrada` (three conditions named by
parameter); below 10% loops back to PASO 1 for another iteration; budget stays flat (`decidir.py`
keeps F3 in `FASES_EN_TESTEO`, confirmed already true from B1).

**Renamed skill `fase-3-escalado` → `fase-4-escalado`** (`git mv`, history preserved): frontmatter
`name`/`description` updated to FASE 4 and its 3-condition entry gate; every `F3.*` node id in the
body → `F4.*` (`F3.exploracion`→`F4.exploracion`, `F3.plan`→`F4.plan` implicitly via the PASO
numbers); `--fase 3 --brazo EXPLORACION` → `--fase 4 --brazo EXPLORACION` (matches
`gen_publicacion.py`'s actual `fase==4` dispatch, confirmed by reading it first); cross-reference
to the FASE 3 rewrite phase and its `F3.reescribir` node added to the entry-gate explanation.

**`fase-2-conceptos/SKILL.md`**: exit wording fixed — the A/B `CAMBIO_BOT` inside FASE 2 is
explicitly NOT the one `F4.entrada` requires; the final rewrite is now named as its own phase
(FASE 3, pointer to `fase-3-flujo/SKILL.md` and `F4.entrada`) instead of "runs before F3"; the
`etapa-3` banco-de-copy pointer moved from "FASE 3" to "FASE 4 (escalado)". Checked
`ciclo-diario/SKILL.md` and `publicar-meta/SKILL.md`: no old-numbering phase references found
(their "escalado" mentions are generic, not tied to F3/F4 node ids) — no changes needed.

**Agents** (`.claude/agents/ETAPA-*.md`, changed phase references only, no doctrine content
touched): `ETAPA-3.md` (description + two body mentions: microángulos now feed FASE 4, not FASE
3), `ETAPA-4.md` (microángulo banco pointer → FASE 4), `ETAPA-5.md` (description and role text
rewritten to name three phases explicitly — FASE 1 paraguas, FASE 2 A/B, FASE 3 final rewrite at
node `F3.reescribir`; `brief_etapa_11` input now marked "FASE 2 y FASE 3" instead of "solo FASE
2"), `ETAPA-6.md` (description clarifies it plans 3 Meta-structure modes — F1/F2/F4, since F3
publishes nothing new; every FASE-3-meaning-escalado occurrence → FASE 4, including the `Input`/
`Output` section headers, the XML tag `<input_fase3>`→`<input_fase4>`, `F3.exploracion`→
`F4.exploracion`, `--fase 3`→`--fase 4`, and the "arquitectura de 3 fases" rule-block header
reframed as "3 fases con estructura Meta (F1, F2, F4)" since F3 doesn't produce campaign
structure), `ETAPA-7.md` (one reference reframed the same way), `ETAPA-11.md` (diagnosis-vs-
rewrite paragraph rewritten: rewrite is FASE 3/`F3.reescribir`, reuses F2's diagnosis if still
fresh or reruns etapa-11 if not), `ETAPA-GUARDAR-PRODUCTO.md` ("Fin de FASE 3" → "Fin de FASE 4"
for the `4_PLAN_ESCALADO.txt`/`F4.plan` trigger; `_DIM_ANUNCIOS.csv` `fase` vocabulary row
FASE3→FASE4, confirmed by grep that the literal string "FASE3" is never actually written by any
script or present in the live CSV — pure doctrine vocabulary, safe to rename). `ETAPA-1.md`,
`ETAPA-2.md` checked: no F3/FASE-3 references found.

**DOCTRINA**: `CALENDARIO_ESCALADO.md` §1.5/§1.7 — "tres"→"cuatro" fases, header "LA ARQUITECTURA
DE 3 FASES"→"DE 4 FASES", §1.7.2 table gained the FASE 3 row (flujo, no new structure, same
budget, gate by mensajes/cierre in hours) and renumbered ESCALADO to FASE 4 (the FASE 2→3
"pasa a FASE 3" line was already correct, left untouched). `DATA_PLAYBOOK.md` "arquitectura de 3
fases" → "4 fases" (generic architecture note, unrelated to the specific F1/F2/F4 campaign
structure count). `DOCTRINA/ESCALADO/04_PALANCAS.md`, `08_PLAN_ENTREGABLE.md` (entregable header,
table row, template header, `fase-3-escalado`→`fase-4-escalado`, `F3.plan`→`F4.plan`),
`09_EXPLORACION_PARALELA.md` (full F3→F4 rewrite: header, gate node id, `--fase 3`→`--fase 4`) —
all three sections of `DOCTRINA/ESCALADO_PLAYBOOK.md` (verbatim-split via
`DOCTRINA/ESCALADO/*.md`). `ESCALADO_PLAYBOOK.md`'s own index table pointers (§8/§9 owner-skill
column) updated to `fase-4-escalado`. `PLANTILLAS_FLUJO_BOT.md` — the "Cuándo diagnostica y
cuándo reescribe" paragraph rewritten: rewrite is its own phase FASE 3 (`F3.reescribir`), gate to
buy volume is `F4.entrada` (not `F3.entrada`), and now explicitly names the cierre condition too,
not just the CAMBIO_BOT date. `GUIA_MADRE_PARAMETRIZADA.md` — checked `verificar_guia_madre.py`
first (confirmed it does not index by the `FASE3_*` key names, only `_PARAMETROS_DECISION.csv`
values and doc pointers), then safely renamed `FASE3_ESTRUCTURA`/`FASE3_PRESUPUESTO_INICIAL`/
`FASE3_OBJETIVO_CAMPANA`/`FASE3_METODO_ESCALADO_1`/`FASE3_METODO_ESCALADO_2` → `FASE4_*`, its
section-8 header, its `fase-3-escalado`→`fase-4-escalado` pointer, `ESTRUCTURA_BOT_ESCALADO` row
("dedicado para escalar (Fase 3)" → "dedicado desde que se reescribe (Fase 3) y sigue así para
escalar (Fase 4)"), and `MARGEN_EMPATE_CPA`'s "entrar a FASE 3 es comprar volumen en CBO" →
"entrar a FASE 4" (the `MINIMO_VENTAS_PARA_ESCALAR` row's "gate de entrada a FASE 3" was already
correct — 2-of-2 does enter FASE 3 now — left untouched after a first wrong edit was caught and
reverted). `verificar_guia_madre.py` re-run after every doctrine edit: stayed green throughout
(89 variables, 35 verified, 54 qualitative, no failures). `MCP_PLAYBOOK.md` checked: no F3/FASE-3
references found, no change needed.

**`Ads/_SWIPE/_CATALOGO_CONCEPTOS.md`**: PARTE III phase table gained the FASE 3 row (mide el
CIERRE del flujo) and renumbered ESCALADO to FASE 4.

**`Ads/_TOOLS/gen_grafo.py`** (not in the original file list, found via the read-only run required
by the verification step): its hardcoded `fases` cost-report tuple still said `"fase-3-escalado"`
after the `git mv`, which silently produced `fase-3-escalado 0 tok` instead of erroring — fixed to
`("fase-1-angulos", "fase-2-conceptos", "fase-3-flujo", "fase-4-escalado", "ciclo-diario")`;
confirmed all four fase skills now report real token costs. `README.md`'s skills-list table row
also had the stale `fase-3-escalado` name (not in the file list either, but a reader-facing stale
pointer worth the one-line mechanical fix): updated to list `fase-3-flujo` and `fase-4-escalado`.

**Left untouched on purpose**: `_CONOCIMIENTO/`, `_OPERADOR/`, `_ROADMAP/` (human reference, per
constraints); `PRODUCTOS/_AUDITORIAS/*.md` and `_LINEA_BASE_SISTEMA.json` (dated historical
audits, still mention `fase-3-escalado` as a true historical fact of what ran on that date);
`evals/fixtures/etapa-8/TINNIDROP.txt` (already frozen by B1, unaffected by B2's scope);
`evals/README.md` (already fixed by B1, re-verified still correct: "ex-`F3.plan`; renombrado por
las cuatro fases, 28-sep-2026").

**Verification (all green)**:
- `python Ads/_TOOLS/verificar_guia_madre.py` → `Sin fallas: cada valor declarado coincide con su
  ejecutor y todo puntero existe.` (89 variables, 35 verified, 54 qualitative — unchanged counts).
- `python Ads/_TOOLS/flujo.py --validar` → `DOCTRINA/FLUJO.json válido: 4 fases, 26 nodos, 1
  excepciones. Cada ejecutor y cada archivo citado existen.` (unchanged from B1 — doctrine text
  edits don't touch node structure).
- `python -m pytest Ads/_TOOLS -q -p no:cacheprovider` → **48 passed** — one failure appeared
  mid-session (`test_split_doctrina.py::test_escalado_playbook_es_verbatim`, expected: editing
  `04_PALANCAS.md`/`08_PLAN_ENTREGABLE.md`/`09_EXPLORACION_PARALELA.md` breaks the frozen verbatim
  hash of the reconstructed `ESCALADO_PLAYBOOK.md`) — re-congealed `ESCALADO_SHA256` in
  `Ads/_TOOLS/test_split_doctrina.py` with a dated comment explaining why the doctrine text changed
  on purpose (per that test's own docstring instructions), confirmed 48/48 green after.
- `python Ads/_TOOLS/gen_grafo.py` (read-only) — no new orphans or dead routes tied to this
  change; the two pre-existing `RUTAS MUERTAS` (`_CORRIDAS_DIARIAS.csv`) and the `_DIM_REFERENCIA_
  F1.csv`/`etapa-render` findings are unrelated and pre-date this task. Found and fixed one real
  regression from the `git mv` (the `fases` cost tuple, see above) before it could ship as a silent
  `0 tok` misreport.
- grep sweep for `_PLAN_FASE3` and `fase-3-escalado` across `*.py`/`*.json`/`*.md`, excluding
  `_CONOCIMIENTO/`, `_AUDITORIAS/`, `odd/tasks/` history and `README.md` (fixed separately) →
  **zero matches**.

**Changed files** (one line each): `Ads/_TOOLS/gen_plan.py` · `gen_publicacion.py` ·
`cargar_pieza.py` · `test_gen_plan.py` · `test_split_doctrina.py` · `gen_grafo.py` ·
`DOCTRINA/FLUJO.json` · `CLAUDE.md` · `DOCTRINA/CALENDARIO_ESCALADO.md` ·
`DOCTRINA/DATA_PLAYBOOK.md` · `DOCTRINA/ESCALADO_PLAYBOOK.md` ·
`DOCTRINA/ESCALADO/04_PALANCAS.md` · `DOCTRINA/ESCALADO/08_PLAN_ENTREGABLE.md` ·
`DOCTRINA/ESCALADO/09_EXPLORACION_PARALELA.md` · `DOCTRINA/PLANTILLAS_FLUJO_BOT.md` ·
`DOCTRINA/GUIA_MADRE_PARAMETRIZADA.md` · `Ads/_SWIPE/_CATALOGO_CONCEPTOS.md` ·
`app/backend/vitalcom_app/contratos.py` · `evals/asserts/etapa-guardar-producto.py` ·
`.claude/agents/ETAPA-3.md` · `ETAPA-4.md` · `ETAPA-5.md` · `ETAPA-6.md` · `ETAPA-7.md` ·
`ETAPA-11.md` · `ETAPA-GUARDAR-PRODUCTO.md` ·
`.claude/skills/fase-2-conceptos/SKILL.md` · `.claude/skills/fase-3-flujo/SKILL.md` (new) ·
`.claude/skills/fase-4-escalado/SKILL.md` (renamed from `fase-3-escalado` via `git mv`, then
edited) · `README.md`.

**Left for B3**: app/backend endpoints and app/frontend screens/tabs for the new 4-phase model.
One concrete finding for B3: `contratos.py`'s `fase3_detalle()` function (the FASE 4 escalado
detail endpoint — its own naming is now stale, `plan_cbo`/1-1-7 content) defaults
`flujo_data.get("fase", "F3")` and filters `entradas` by `e.get("fase") == "F3"` — both need to
become `"F4"` once B3 rewires this endpoint for the new phase split; left untouched here since it's
functional app logic, not a doctrine pointer, and squarely in B3's scope per the task's own split.

## Next step
B3 (app) can now proceed off the doctrine contracts landed in B2, using the concrete
`fase3_detalle()` finding above as its starting point.
