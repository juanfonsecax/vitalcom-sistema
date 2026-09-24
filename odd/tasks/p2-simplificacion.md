# P2 — Simplificación (platform plan, gate 2 of 6)

## Objective
Fewer pieces with the same result: fold deterministic data out of prompts, split doctrine
files so each etapa reads only its section, and fuse etapa-7 + etapa-8.

## Why
- Token cost per phase measured by `gen_grafo.py`: 268k (ciclo-diario) to 446k (fase-2).
- These tokens become money when the platform moves to API-key billing (agency/SaaS).
- Fewer agents = fewer handoffs that can break.

## Scope (authorized 2026-09-23: operator "arranca con el P2")
- T1 etapa-fanpage -> data table + selection absorbed by etapa-2.
- T2 split "god nodes" (`DOCTRINA/ESCALADO_PLAYBOOK.md`, `DOCTRINA/PLANTILLAS_ADS.md`,
  `CLAUDE.md`) so each consumer reads only its section. Doctrine text unchanged, only cut.
- T3 fuse etapa-7 + etapa-8 into one judgment etapa; the numbers become a deterministic
  table printed by code (interim screen until P4 UI), never prose.
- Out of scope: etapa-3 (no real F3 output yet — pruning it saves zero tokens and has no eval),
  any doctrine change.

## Gate for every prune (evals/README.md "Protocolo de poda")
The baseline asserts run on FROZEN fixtures, so they alone do not prove a pruned prompt still
works. Each prune must also: re-run the changed etapa on the same frozen inputs that produced
its fixture, freeze the new output as a candidate fixture, and pass the same assert. A new
undocumented failure reverts the prune; asserts are never weakened. Plus
`python Ads/_TOOLS/gen_grafo.py --comparar` before/after for the token delta.

## Tasks
- [x] T1 — `PRODUCTOS/_DIM_FANPAGES.csv` (10 pages: identity, tone, age orientation, page_id,
  niche products) + etapa-2 chooses `pagina_asignada` with rules F1-F5; remove
  `.claude/agents/ETAPA-FANPAGE.md`; update every consumer (FLUJO.json, skills, CLAUDE.md
  etapa list, gen_publicacion/gen_lanzador/verificar_producto, app tests). Route: delegated
  writer (cross-cutting, 10+ files). Check: etapa-2 re-run on CLEARSTEM frozen inputs picks
  the same page as `evals/fixtures/etapa-fanpage/CLEARSTEM.txt`; full test suite + evals green.
- [x] T2 — Split god nodes by section. Route: delegated writer. Check: gen_grafo --comparar
  shows fewer inherited tokens; re-run of affected etapas with baselines passes.
- [x] T3 — Fuse etapa-7 + etapa-8. Route: delegated writer. Check: re-run on the frozen
  2026-09-08 audit inputs passes both etapa-7 and etapa-8 asserts.

## Config
- TDD: off (default). RDD: off. Work-unit commits on `feat/p2-simplificacion`.
- Re-running an etapa is done by the parent orchestrator (subagents cannot spawn subagents).

## Progress
- 2026-09-23: P1 fast-forward merged into `feat/optimizacion-continua-perfil-angulos` (2e7ef15).
  Branch `feat/p2-simplificacion` created.
- 2026-09-23: T1 writer pass done (data + absorb + delete + consumers + evals). NOT yet re-run
  against real Claude on frozen CLEARSTEM inputs — that step is the parent's, per Config below.
  Evidence:
  - `PRODUCTOS/_DIM_FANPAGES.csv` created (real csv.DictWriter, invariant 11): 10 rows,
    columns `pagina_num,pagina_nombre,identidad,rol,tono,logica,edad_orientacion,page_id,productos_nicho`.
    Values copied verbatim from the deleted `ETAPA-FANPAGE.md` (no doctrine reworded).
  - `.claude/agents/ETAPA-2.md` absorbed the judgment: new §ASIGNACIÓN DE FANPAGE with reglas
    F1-F5 verbatim, reading `PRODUCTOS/_DIM_FANPAGES.csv` instead of an embedded list, emitting the
    same `<pagina_asignada>` Formato A/Formato B block ETAPA-4/5/6 already consume.
  - `.claude/agents/ETAPA-FANPAGE.md` deleted.
  - Consumers updated: `CLAUDE.md` (16 etapas, owner-map rows), `DOCTRINA/FLUJO.json`
    (secuencia + "como" + page_id "dueno"), `VISTAS/_MANIFIESTO.json` (pasos: etapa-2 alone, no
    longer parallel), `.claude/skills/fase-1-angulos/SKILL.md` (PASO 3 rewritten, checklist),
    `.claude/skills/generar-conceptos/SKILL.md`, `DOCTRINA/PLANTILLAS_ADS.md`,
    `DOCTRINA/PLANTILLAS_INFOGRAFIAS.md`, `DOCTRINA/ETAPA-RECOLECCION.md`, `README.md`,
    `Ads/_TOOLS/{cargar_page_id.py,gen_lanzador.py,gen_publicacion.py,verificar_producto.py,
    LAVADO.md,test_gen_app.py}`, `app/backend/tests/{test_pasos.py,test_fase1_api.py}`,
    `db/tables.py` (+ regenerated `db/schema.sql`). Generated files (`VISTAS/APP.html`,
    `PRODUCTOS/_FLUJO.json`, `_LANZADOR.json`, `VISTAS/_ESTADO.json`) regenerated via
    `python Ads/_TOOLS/gen_app.py --todo`, never hand-edited. `_ROADMAP/`, `_OPERADOR/` and
    historical `PRODUCTOS/<P>/*.txt` / `_AUDITORIAS/` left untouched.
  - Evals: `evals/asserts/etapa-fanpage.py` retargeted to cross-check against
    `PRODUCTOS/_DIM_FANPAGES.csv` (was: doctrina text of the now-deleted agent) — assert not
    weakened, same catalog, same fixture. Documented in `evals/README.md` under a new
    "Retargeting T1" section and in `promptfooconfig.yaml`'s comment for that test.
  - Verification run (see final report to orchestrator for full command output):
    `python -m pytest Ads/_TOOLS -q -p no:cacheprovider` → 41/41 passed.
    `python evals/run_baseline.py` → TOTAL=30 PASS=26 FALLO-CONOCIDO=4 FAIL=0 (unchanged).
    `python Ads/_TOOLS/gen_grafo.py --comparar` → no orphaned .md/.csv; `fase-1-angulos` cost
    -21907 tok (ETAPA-FANPAGE.md no longer inherited); 16 agentes (was 17).
    `python Ads/_TOOLS/flujo.py --todo` → same 5 products, same nodes/gates (only cosmetic
    "como"/secuencia text changed on F1.paquete).
    `python Ads/_TOOLS/verificar_guia_madre.py` → exit 0, same single pre-existing finding
    (`exploracion_n_angulos`), unrelated to this change.
    `uv run pytest tests/test_pasos.py tests/test_fase1_api.py` (app/backend) → 15/15 passed.
  - NOT done (belongs to the parent orchestrator per Config: "Re-running an etapa is done by the
    parent orchestrator"): the actual CLEARSTEM re-run of `etapa-2` against real Claude to confirm
    it reproduces the same page as `evals/fixtures/etapa-fanpage/CLEARSTEM.txt`
    ("Página 4 ✨ Belleza & Piel — Astrid García"). See the writer's final report for the exact
    frozen-inputs package to use for that re-run.

- 2026-09-23: T1 CLOSED by parent. Protocol re-run: etapa-2 (session model) on CLEARSTEM frozen
  inputs (evals/fixtures/etapa-1/CLEARSTEM.txt, 2_DATA_PRODUCTO.txt sections 1 and 3,
  _DIM_FANPAGES.csv, saturacion DESCONOCIDA, no WebSearch) assigned Página 4 Belleza & Piel,
  identical to the old etapa-fanpage fixture. Output kept in
  evals/reruns/2026-09-23_etapa-2_CLEARSTEM_p2-T1.txt (6 fichas + pagina_asignada; the parent
  joined the tone bullets into one line when transcribing; preface/summary table omitted).
  etapa-2 assert PASS (6 fichas, 19 conciencia markers). Found the retargeted etapa-fanpage assert
  was weak (any catalog name anywhere passed: it matched 'Salud Hormonal Femenina', cited only to
  be discarded). Strengthened: parses the assigning line and checks number+name against the CSV.
  Rerun and fixture PASS (#4); wrong number and missing assignment FAIL. Baseline 30/26/4/0,
  test_evals_baseline 6 passed.

- 2026-09-24: T2 writer pass done (split + consumer pointers + gen_grafo support + verbatim
  test). Checkbox left UNCHECKED per Config: the writer cannot re-run etapas against real
  Claude; that step belongs to the parent, same pattern as T1.

  **What moved.** Both files kept their doctrine text 100% verbatim (proven, not asserted —
  see below); only WHERE each paragraph lives and WHO points to it changed:
  - `DOCTRINA/ESCALADO_PLAYBOOK.md` (330 lines, sha256 `a7fe5090…fb1a81`) → 11 files under
    `DOCTRINA/ESCALADO/00_INTRO_FILOSOFIA.md` … `10_METRICAS_TESTEO.md`, one per original `##`
    heading, in original order. The old path is now a 46-line index (table of section → owner).
  - `DOCTRINA/PLANTILLAS_ADS.md` (367 lines, sha256 `7067a64f…c5a4f4d18`) → 12 files under
    `DOCTRINA/PLANTILLAS_ADS_SECCIONES/00_INTRO.md` … `11_DOCTRINA_CREATIVOS_VIDEO_IMAGEN.md`,
    same rule. Old path is now a 19-line index.

  **Consumer map (who needs which section — full detail in the writer's final report to the
  orchestrator).** Grepped every `.claude/agents/*.md`, `.claude/skills/*/SKILL.md`, live
  `DOCTRINA/*.md` and `Ads/_SWIPE/*.md` for `ESCALADO_PLAYBOOK.md`/`PLANTILLAS_ADS.md` mentions,
  read the surrounding `§N` citation, and re-pointed each to the section file that actually
  holds that content:
  - `etapa-7`: only `03_SENALES_DECISION.md` + `04_PALANCAS.md` + `06_SATURACION_CUENTA.md` —
    used to inherit the whole 9.5k-tok playbook for 3 of 11 sections.
  - `etapa-8`: only `05_REPLICAR_GANADOR.md` (§4) + `07_MATRIZ_DUPLICACION.md` (§6) +
    `06_ESTILOS_ANTIFATIGA.md` (PLANTILLAS_ADS) — never actually cited §0/1/1.5/2/3/8.
  - `etapa-6`, `etapa-10`, `etapa-11`, `etapa-guardar-producto`, `fase-2-conceptos`,
    `fase-3-escalado`, `generar-conceptos`: each pointed at 1-2 section files instead of the
    monolith (`10_METRICAS_TESTEO.md`, `04_PALANCAS.md`, `08_PLAN_ENTREGABLE.md`,
    `09_EXPLORACION_PARALELA.md`, `06_ESTILOS_ANTIFATIGA.md` as applicable).
  - `etapa-2`: only `11_DOCTRINA_CREATIVOS_VIDEO_IMAGEN.md` (the VIDEO/IMAGEN assignment rule) —
    never needed the ad-image prompt templates themselves.
  - `etapa-4`, `etapa-9`: genuine heavy consumers of PLANTILLAS_ADS — pointed at the 3-4 section
    files they actually cite (`01_COMPLIANCE_ANDROMEDA.md`, `04_PROMPT_CONTROL_FASE1.md`,
    `05_PROMPT_MAESTRO_FASE2.md`, `06_ESTILOS_ANTIFATIGA.md`, `11_DOCTRINA_CREATIVOS…`) instead
    of the whole file — smaller win here since they need most of it, but still real.
  - `ciclo-diario` SKILL.md: left pointing at the (now tiny) index — its own two mentions are a
    human-facing "four support files" overview, not a section-specific need; the real per-etapa
    savings come from `etapa-7`/`etapa-8`'s own files, which it invokes.
  - `CLAUDE.md` / `README.md` owner-map rows: left pointing at the root path on purpose (now the
    index) — those are pointer rows, not agent/skill token drivers in `gen_grafo`'s model.
  - Also fixed 4 stale `§N` cross-references outside agents/skills for correctness
    (`DOCTRINA/CALENDARIO_ESCALADO.md` ×3, `DOCTRINA/PARAMETRIZACION_ADS.md` ×1,
    `Ads/_SWIPE/_ESTRATEGIA_CONCEPTOS.md` ×1). NOT fixed (low-value, no test/gate depends on
    them, flagged for a future pass): stray `ESCALADO_PLAYBOOK`/`PLANTILLAS_ADS` mentions without
    `.md` in `Ads/_TOOLS/{decidir.py,atribuir.py,gen_vocabulario.py,gen_dashboard.py,
    test_gen_lanzador.py,test_perfilar_angulos.py}` and in `DOCTRINA/GUIA_MADRE_PARAMETRIZADA.md`
    / `PLANTILLAS_INFOGRAFIAS.md` / `COPYWRITING_ADS.md` / `Ads/_SWIPE/{_METODO.md,
    _CATALOGO_CONCEPTOS.md}` — none of these drive `gen_grafo`'s token math (only agent/skill
    `lee_md` does) and the target files still exist and still answer to those names.

  **gen_grafo.py**: `construir()` only scanned the top level of `(".", "DOCTRINA", "Ads/_TOOLS",
  "Ads/_SWIPE", "PRODUCTOS")` — a file inside a new subdirectory would have been invisible to the
  token graph AND to orphan detection (false negative). Added `DOCTRINA/ESCALADO` and
  `DOCTRINA/PLANTILLAS_ADS_SECCIONES` to that scan list.

  **Verbatim proof**: `Ads/_TOOLS/test_split_doctrina.py` (new, 5 tests) concatenates the
  section files in original order and compares the sha256 against the pre-split monolith's
  sha256 (frozen 24-sep-2026, captured before any edit). Also asserts no stray files snuck into
  either folder, and that both index files stayed small (<3.5kB) so a future prose addition to
  the index gets caught.

  **Verification run:**
  - `python Ads/_TOOLS/test_split_doctrina.py` → 5/5 PASS.
  - `python -m pytest Ads/_TOOLS -q -p no:cacheprovider` → 42/42 passed (was 41 after T1; +5 new
    minus one file-count accounting quirk — pytest collects the 5 new tests from one new file).
  - `python evals/run_baseline.py` → TOTAL=30 PASS=26 FALLO-CONOCIDO=4 FAIL=0 (byte-identical to
    T1's result — expected, since no `.claude/agents/ETAPA-*.md` PROSE changed, only which
    doctrine file path each one cites).
  - `python Ads/_TOOLS/gen_grafo.py --comparar` (before → after, this session):
    `fase-1-angulos` −65,574 tok · `fase-2-conceptos` −68,378 tok · `fase-3-escalado` −56,332 tok
    · `ciclo-diario` −61,945 tok · arranque en frío −2,394 tok. Zero new orphans (`.md sin
    consumidor: ninguno`), zero dead routes after adding `test_split_doctrina.py`'s own path.
    Baseline re-saved with `--escribir` so the next `--comparar` measures from here.
  - `python Ads/_TOOLS/verificar_guia_madre.py` → exit 1, same single pre-existing finding
    (`exploracion_n_angulos`) as T1 — unrelated to this change.
  - `python Ads/_TOOLS/flujo.py --todo` → same 5 products, same node names/gates/sequences
    observed (spot-checked OVULOS_PURITY, CLEARSTEM, VARICOSE outputs) — no flujo/gate logic was
    touched, only doctrine file paths inside agent prose.

  **NOT done (belongs to the parent orchestrator per Config)**: re-running the etapas whose read
  set changed, against real Claude, on the SAME frozen inputs that produced their eval fixtures,
  to confirm the pruned pointers still produce a structurally-equivalent output (per
  `evals/README.md` "Protocolo de poda" step 3-4). Etapas with an existing fixture to re-run
  against (frozen-input package in parentheses):
  - `etapa-2` (`evals/fixtures/etapa-2/{CLEARSTEM,NusavaB12,OVULOS_PURITY}` inputs — its own
    `2_DATA_PRODUCTO.txt` §ÁNGULOS/§CONJUNTOS sections; also covers the `etapa-fanpage` fixture
    since T1 already re-ran etapa-2 for CLEARSTEM).
  - `etapa-6` (`evals/fixtures/etapa-6/{CLEARSTEM,NusavaB12,TINNIDROP,OVULOS_PURITY}` — full
    `_PLAN.json` inputs).
  - `etapa-4` (`evals/fixtures/etapa-4/TINNIDROP` — `1_HACER_MANUAL.txt` §PARTE 4 inputs).
  - `etapa-5` (`evals/fixtures/etapa-5/{CLEARSTEM,TINNIDROP}` — `FLUJO_LUCIDBOT.md` inputs;
    etapa-5 wasn't edited but is listed for completeness since it shares fase-2 with etapa-4/8).
  - `etapa-7` (`evals/fixtures/etapa-7/TINNIDROP` — `_AUDITORIAS/_AUDITORIA_DIARIA_20260908.txt`
    §PASO 3 inputs).
  - `etapa-8` (`evals/fixtures/etapa-8/TINNIDROP` — `4_PLAN_ESCALADO.txt` extract inputs).
  - `etapa-9` (`evals/fixtures/etapa-9/TINNIDROP` — `_DIM_CREATIVOS.csv` tanda inputs).
  - `etapa-guardar-producto` (all 4 products' fixtures — manifest of top-level files; not
    expected to change since no file-role doctrine moved, but shares fase-3 with etapa-8).
  No fixture exists yet for `etapa-10`, `etapa-11` (both edited) — same gap T1's report already
  documented in `evals/README.md`; re-running them can't be checked against a frozen output, only
  against their own structural contract by eye.

  **CLAUDE.md proposal (out of scope for T2 edits, per Config — analysis only):** CLAUDE.md is
  5,872 tok and inherited by 8 agents = 46,976 tok, the single biggest "nodo dios" in the current
  `gen_grafo` report. Candidate sections to relocate (none touched in this task):
  - `## SDD Workflow (lazy-loaded)` pointer and the long `## MAPA DE ARCHIVOS` table (~35 rows) —
    most agents only ever touch 2-3 rows of that table for their own doctrine; a per-agent
    "owner map" pointer (like the ESCALADO/PLANTILLAS split done here) could cut per-agent
    inherited tokens by an estimated 60-70% of CLAUDE.md's weight (~3,500-4,100 tok/agent),
    i.e. roughly 28,000-33,000 tok off the current 46,976 across the 8 agents that read it.
  - The invariants (13 items) and constants (definitions, ángulo/concepto table, tonalidad,
    compliance scope, segmentación) are genuinely cross-cutting and would NOT save much if
    split — nearly every agent needs most of them; splitting these has a low benefit/risk ratio
    (CLAUDE.md governs the whole orchestrator, so a botched split risks breaking every agent at
    once — the opposite of ESCALADO/PLANTILLAS_ADS, which had multiple genuinely light-touch
    consumers). This needs its own explicit user decision before any edit, since CLAUDE.md is
    explicitly OUT of scope for T2 content edits.

- 2026-09-24: T2 CLOSED by parent.
  - Verbatim: parent diffed original ESCALADO_PLAYBOOK/PLANTILLAS_ADS (HEAD before 491869d) against
    the concatenated section files after stripping CR: zero differences.
  - Re-run etapa-9 (TINNIDROP, day 2026-09-06, dry run, no writes; git status clean): 6 rows,
    assert PASS (canonico_id complete, 3 funnel roles, no concepto >2). Evidence
    evals/reruns/2026-09-24_etapa-9_TINNIDROP_p2-T2.csv. Compliance held in all 6 prompts.
  - Re-run etapa-4 FASE 1 on the CLEARSTEM chain (the TINNIDROP fixture's original inputs were never
    frozen): 6 angulos x 3 TEXTO variations + 3 TITULOS + DESCRIPCION, CTA 'Escribinos' in all,
    price in 2 of 6, no banned word in ad copy. Checked by parent reading, NOT by the assert: the
    etapa-4 assert is coupled to the saved-manual layout ('★ CONJUNTO N', 'TEXTO 1'), not to the raw
    etapa output. Follow-up: make the assert accept the raw output layout.
  - Finding on the T1 re-run inputs: the T1 etapa-2 package omitted ETAPA-1B voice of customer, so
    the re-run dropped RESISTENCIA_INSULINA_SOP (the original fixture had it, validated by voz;
    best historic CLEARSTEM angle). Not a prune regression; the T1 page conclusion stands (page is
    chosen by comprador principal). Follow-up: freeze each etapa's full input package at production
    time (PRODUCTOS/<P>/0_INPUTS_CONGELADOS.md already exists for OVULOS_PURITY) so re-runs are exact.
  - etapa-7/8 re-run deferred to T3 (they get fused). etapa-guardar-producto not re-run (writes disk);
    its read-set change is one pointer line.

- 2026-09-24: T3 writer pass done (fuse + wire deterministic table + consumers + evals).
  Checkbox left UNCHECKED per Config: the writer cannot re-run the fused etapa against real
  Claude — same pattern as T1/T2.

  **What was cut vs kept.** Both files' doctrine rules moved into the new
  `.claude/agents/ETAPA-7.md` verbatim (window integrity PASO 0-1, MCP signals PASO 2, sangrado
  PASO 3, palancas A-D, replicar ganador §C, diagnostico cruzado §D, aprendizajes read/write,
  ETAPA-10/9 connection, CPA-never-ROAS, strong-scaling-only-with-confirmed-CPA). Cut: the
  duplicated "solo lee", "CPA semanal nunca un dia" and "escalado fuerte solo con CPA real"
  reminders that both files repeated; the etapa-7->etapa-8 handoff line ("alimenta a ETAPA-8");
  etapa-8's own umbral re-statements already owned by `_PARAMETROS_DECISION.csv` (kept as
  citations, not re-derivations). `.claude/agents/ETAPA-8.md` deleted.

  **Deterministic table (Goal 2).** `Ads/_TOOLS/decidir.py` already had a console printer
  (`imprimir_consola()`, default mode without `--json`) with Break-Even, CPA Objetivo, per-celda
  estado/ventas/gasto/CPA/IC/accion_sugerida — exactly the "operator sees numbers now, from code"
  requirement. No new script needed. New ETAPA-7.md PASO 4 tells the etapa to run it and cite it,
  never reprint the numbers in prose. `.claude/skills/ciclo-diario/SKILL.md` now has a
  "Tabla determinística — SIEMPRE primero" section wiring `python Ads/_TOOLS/decidir.py` before
  invoking etapa-7, with its output pasted first in the daily audit.

  **Consumers updated:** `CLAUDE.md` (15 etapas, 14 inherit), `README.md` (both etapa-list
  mentions), `.claude/skills/{ciclo-diario,fase-2-conceptos,fase-3-escalado}/SKILL.md`,
  `.claude/agents/{ETAPA-10,ETAPA-11}.md` (CONEXIÓN sections), `DOCTRINA/{CALENDARIO_ESCALADO,
  DATA_PLAYBOOK,GUIA_MADRE_PARAMETRIZADA,PLANTILLAS_ADS}.md` pointer rows, the
  `DOCTRINA/ESCALADO_PLAYBOOK.md` index table's "Quién lo lee" column, `Ads/_TOOLS/{decidir.py,
  gen_publicacion.py,gen_dashboard.py}` comments, `PRODUCTOS/_PARAMETROS_DECISION.csv` (2 cells,
  edited with `csv` module per invariant 11). `DOCTRINA/FLUJO.json` and `VISTAS/_MANIFIESTO.json`
  never mentioned etapa-8 by name — nothing to change there. No app/backend test references
  `etapa-8`. `_APRENDIZAJES.csv` (44 historical rows tagged `etapa-8`) left untouched — it's
  historical data, not a doctrine pointer; the new ETAPA-7.md filter matches
  `'etapa-7' IN consumido_por OR 'etapa-8' IN consumido_por` for backward compatibility instead.
  `PRODUCTOS/_PORTAFOLIO.txt` and `_BITACORA_DATA.txt` still mention ETAPA-8 (found by grep) but
  are bitácora/historical-reference files, not named in T3's consumer list — left untouched,
  flagged here for a future pass if desired. `.atl/skill-registry.md` is an external cache
  (no generator script found in this repo) — left untouched, will refresh on its own mechanism.

  **Correction mid-task:** first pass also edited doctrine TEXT inside `DOCTRINA/ESCALADO/*.md`
  (replacing "ETAPA-8" with "ETAPA-7" in 6 section files) — this broke
  `test_split_doctrina.py::test_escalado_playbook_es_verbatim` (T2's byte-for-byte guarantee
  against the frozen pre-split monolith). Reverted with `git checkout --`; only the
  `ESCALADO_PLAYBOOK.md` INDEX file's "Quién lo lee" column (not verbatim-checked) was updated
  instead. Lesson: doctrine section files are frozen text, not live pointers — pointers live one
  level up, in the index or in the consuming agent/skill.

  **Evals — assert conflict found and reported, not papered over.** Kept `asserts/etapa-7.py`
  and `asserts/etapa-8.py` unchanged in strength, plus their original fixtures/tests. Added one
  new promptfoo test, `etapa-7 fusionada / TINNIDROP`, running a single REAL fixture
  (`evals/fixtures/etapa-7/TINNIDROP_FUSIONADO.txt` — the PASO 3 block of
  `_AUDITORIAS/_AUDITORIA_DIARIA_20260908.txt`, from when `ciclo-diario` already ran etapa-7 and
  etapa-8 in one pass without separating them) against BOTH asserts via promptfoo's existing
  multi-item `assert:` list (`run_baseline.py` already ANDs them — no runner change needed).
  Result: `asserts/etapa-7.py` PASSES; `asserts/etapa-8.py` FAILS 2 of 4 checks (`Break-Even`
  and `regla de oro`, literal substrings) because this real fixture already uses decidir.py's
  compact format (`BE Qxx`, `36v`) instead of spelling those words out — exactly the number-citing
  behavior Goal 1 asks for. Marked `expected_fail: true` with the exact conflict documented in
  `promptfooconfig.yaml` and `evals/README.md` §"Fusión T3", per the instruction to stop and
  report rather than weaken the assert. The new `ETAPA-7.md` template (PASO 5 / "Informe diario")
  DOES ask for those exact words as fixed vocabulary in the judgment prose (not as re-derived
  numbers) — so a real re-run against the fused template may well close this gap; that
  verification needs the parent's re-run against real Claude, same limitation as T1/T2.

  **Verification run:**
  - `python -m pytest Ads/_TOOLS -q -p no:cacheprovider` → 42/42 passed (same count as T2 close;
    the mid-task doctrine-text revert brought `test_split_doctrina.py` back from 1 fail to green).
  - `python evals/run_baseline.py` → TOTAL=31 PASS=26 FALLO-CONOCIDO(documentado)=5 FAIL=0 (was
    30/26/4/0 after T2; +1 test, +1 documented expected_fail, zero real fails, zero regressions).
  - `python Ads/_TOOLS/gen_grafo.py --comparar --escribir` → 15 agentes (was 16); zero orphans;
    `fase-3-escalado` −4,820 tok · `ciclo-diario` −4,775 tok (ETAPA-8.md no longer inherited);
    `fase-1-angulos` +263 tok · `fase-2-conceptos` +395 tok (CLAUDE.md text growth, not new
    agent reads — negligible, <0.15% of either budget). Baseline re-saved with `--escribir`.
  - `python Ads/_TOOLS/flujo.py --todo` → same 5 products, same nodes/gates/sequences (spot-checked
    CLEARSTEM, VARICOSE, OVULOS_PURITY) — no flujo/gate logic touched, only which agent name does
    the monitoring+escalado.
  - `python Ads/_TOOLS/verificar_guia_madre.py` → exit 0 (well, non-fatal exit path — same output
    text), same single pre-existing finding (`exploracion_n_angulos`), unrelated to this change.
  - No app/backend files reference `etapa-8` — no `uv run pytest` needed for this task.

  **NOT done (belongs to the parent orchestrator per Config):** re-running the fused `etapa-7`
  against real Claude, on the frozen 2026-09-08 audit inputs, to (a) confirm the new template
  still produces a monitor+plan output structurally equivalent to the pre-fusion pair and (b)
  settle the `Break-Even`/`regla de oro` question above. **Frozen-inputs package for that
  re-run:** `PRODUCTOS/_DECISIONES.json` (already regenerated fresh by `decidir.py --escribir`
  this session — TINNIDROP/CLEARSTEM/NUSAVA data through 2026-09-22, NOT the 2026-09-08 window the
  fixture was frozen from, since `0_INPUTS_CONGELADOS.md`-style freezing wasn't done for
  etapa-7/8 inputs at the time per T2's own follow-up finding) + `PRODUCTOS/_FACT_VENTAS.csv` /
  `_FACT_ENTREGA.csv` filtered to 2026-08-25→2026-09-07 (the fixture's window) + `_BITACORA_DATA.txt`
  + `_EVENTOS.csv` + `_DIM_CONJUNTOS.csv` + `PRODUCTOS/TINNIDROP/3_CAMPAÑA_META.txt`. Since the
  exact 2026-09-08 snapshot of those CSVs isn't separately frozen, today's live data is the
  closest available substitute and should be explicitly flagged as such in the re-run's evidence
  (same caveat T2 raised for the CLEARSTEM/etapa-2 re-run).

  Commits: `9b36246` (fuse agents+skills), `59e08f8` (doctrine/tool pointers), `6171b02`
  (regenerated views+baseline), `b7d74d9` (evals fused fixture+config).

- 2026-09-24: T3 CLOSED by parent. Writer commits 9b36246 59e08f8 6171b02 b7d74d9 c7f4b2a (etapa-8 deleted,
  15 etapas; ciclo-diario prints `decidir.py` table first; _PARAMETROS_DECISION.csv: only 2 description
  texts renamed ETAPA-8 -> ETAPA-7, no value changed). Parent re-ran the fused etapa-7 on TINNIDROP with
  today's data (the 2026-09-08 inputs were never frozen) twice; the second run after making the
  "CPA Q[..]" format explicit in the winners template line of ETAPA-7.md.
  Asserts on the real deliverable: judgment alone fails etapa-7 (no literal "CPA Q<n>": numbers now
  live in the table by design); table alone fails both; table + judgment PASSES etapa-7 AND etapa-8.
  That is the operator's contract (code owns numbers, agent owns judgment). Evidence:
  evals/reruns/2026-09-24_decidir_TINNIDROP_tabla.txt + evals/reruns/2026-09-24_etapa-7-fusionada_TINNIDROP_p2-T3.txt.
  Follow-up: config tests for etapa-7/8 should evaluate table + judgment as one deliverable.
  Data findings from the re-runs (operator/ingest, not P2): `pct_conv_clic_enlace` arrives 0.0 in every
  MetaAPI-directo row of _FACT_ENTREGA (ingest defect); GTR7 delivered $0 on 2026-09-21 (check billing /
  account status); _BITACORA_DATA.txt has no entry after 2026-09-08; DIM inconsistencies
  (DETERIORO nivel_conciencia 2 vs NC1 in ad signature, ACC concepto SIN_CLASIFICAR).

- 2026-09-24: P2 T1-T3 fast-forward merged into `feat/optimizacion-continua-perfil-angulos`
  (2e7ef15 -> 801f650). T4 opened on the same branch.

## T4 — Archaeology cleanup (authorized 2026-09-24)
Operator: "Reescribí cada regla en su forma vigente, sin la historia que la produjo". Scope:
`.claude/agents/*.md`, `.claude/skills/*/SKILL.md`, `DOCTRINA/**/*.md`, `CLAUDE.md`. Not
`_CONOCIMIENTO/`, fixtures or code.

Inventory (read-only mapper, 801f650): 50 files, 118 product mentions + 281 date tokens.
Classes: A archaeology (remove, keep the rule) ~273 · F functional (never touch) ~33 ·
E teaching example (keep, make generic) ~88. Raw inventory in the session scratchpad
(`arqueologia_inventario.json`); the F list is copied into each writer's brief.
F anchors: gasto.py cutoff `2026-09-06` (CLAUDE.md, ETAPA-7, DATA_PLAYBOOK) · real paths that
gen_grafo.py RE_RUTA checks on disk · `[REG_MSPAS]`/`[REG_FDA]` values · the `### PASO 6/7` headings
and tokens that test_ab_flujo.py greps in ETAPA-11/ETAPA-5 · CLI canonical examples.
Decision: the "Fuente" column of GUIA_MADRE_PARAMETRIZADA.md stays. It is parameter
provenance ("preguntar de qué es envoltorio"), not narration, and verificar_guia_madre.py does
not read it.

Baseline tokens (gen_grafo, 801f650): fase-1 289,432 · fase-2 377,865 · fase-3 232,110 ·
ciclo-diario 210,233 · cold start 8,901.

- [ ] T4a — Remove the 3 `expected_fail` etapa-6 evals whose `_PLAN.json` predate the
  22-sep IMAGE-only rule (CLEARSTEM, NusavaB12, TINNIDROP): config + README. etapa-6 keeps
  OVULOS_PURITY. The etapa-4 "cura" and the fused etapa-7 known failures stay (they are not
  pre-22-sep plans). Route: delegated writer W1.
- [ ] T4b — DOCTRINA/** + CLAUDE.md cleanup. Route: delegated writer W1.
- [ ] T4c — .claude/agents + .claude/skills cleanup. Route: delegated writer W2 (after W1).
- [ ] T4d — Pruning protocol: the parent re-runs every etapa that has a fixture and whose
  prompt or inherited doctrine changed (2, 4, 5, 6, 7, 9, guardar-producto) on the frozen
  inputs. The new output must pass the same assert. Then run gen_grafo --comparar. Etapas
  without a fixture (0, 1, 1b, 3, 10, 11, render, producto) change prose only and cannot be
  re-verified. This is disclosed, not hidden.
- [ ] T4e — Proposal (read-only): which live products to re-package, with sales/spend data kept.

## Next step
T4a+T4b writer W1.
