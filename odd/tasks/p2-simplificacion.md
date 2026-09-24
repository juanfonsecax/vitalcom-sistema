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

- [x] T4a — Remove the 3 `expected_fail` etapa-6 evals whose `_PLAN.json` predate the
  22-sep IMAGE-only rule (CLEARSTEM, NusavaB12, TINNIDROP): config + README. etapa-6 keeps
  OVULOS_PURITY. The etapa-4 "cura" and the fused etapa-7 known failures stay (they are not
  pre-22-sep plans). Route: delegated writer W1.
- [x] T4b — DOCTRINA/** + CLAUDE.md cleanup. Route: delegated writer W1 (this pass).
- [x] T4c — .claude/agents + .claude/skills cleanup. Route: delegated writer W3 (after W1+W2).
- [x] T4d — CLOSED 2026-09-24 by the parent. Re-runs on frozen inputs, all asserts PASS:
  etapa-2 OVULOS_PURITY (0_INPUTS_CONGELADOS + 2_DATA lines 1-88; 6 fichas, 12 awareness markers;
  4 of 6 angles match the old fixture, the 2 others vary as a judgment etapa does) · etapa-6
  OVULOS_PURITY (schema + image-only PASS; the harness did not persist the raw output, so the
  saved JSON is a parent skeleton with the checked keys and the long strings elided) · fused
  etapa-7 TINNIDROP (same package as T3; PASSES etapa-7 AND etapa-8 on its own; it replaced the
  pre-fusion fixture and closed that expected_fail in 56a34c4) · etapa-9 TINNIDROP dry run (6
  rows, 3 funnel roles, no concept >2; no writes to PRODUCTOS) · etapa-4 OVULOS_PURITY checked by
  reading (6x3 TEXTO + 3 TITULOS + DESCRIPCION, WhatsApp CTA, price in 2/6, no banned word in ad
  copy). NOT re-run: etapa-5 (prompt unchanged; only the quote column of its template left) and
  guardar-producto (writes disk). Etapas without a fixture (0, 1, 3, 10, 11, render) changed
  prose only and cannot be re-verified. Gates: pytest 42 passed · evals 28/27/1/0 ·
  verificar_guia_madre only the pre-existing `exploracion_n_angulos`.
  Final tokens vs 801f650: f1 289,432->284,165 (-5,267) · f2 377,865->371,192 (-6,673) ·
  f3 232,110->227,457 (-4,653) · ciclo 210,233->206,687 (-3,546) · cold start 8,901->8,859.
  Data findings from the re-runs (operator, not T4): GTR7 delivered $0 on 2026-09-21 (68% of
  TINNIDROP spend) · the TINNIDROP F2 batch has been paused since 08-sep over the SOUTH MOON/sublingual
  creative · _PARAMETROS_PUBLICACION F1 anuncios_por_conjunto=1 vs ETAPA-6 duplicate=2 · tz_offset
  -06:00 applied to Colombia · the OVULOS etapa-4 infographic signs a review with an invented
  name "Laura M." (use the real name or "clienta Hernatura") · CLEARSTEM R1-R4 sitting in
  PENDIENTE_GENERAR since 26-jul.
  T4d as planned — Pruning protocol: the parent re-runs every etapa that has a fixture and whose
  prompt or inherited doctrine changed (2, 4, 5, 6, 7, 9, guardar-producto) on the frozen
  inputs. The new output must pass the same assert. Then run gen_grafo --comparar. Etapas
  without a fixture (0, 1, 1b, 3, 10, 11, render, producto) change prose only and cannot be
  re-verified. This is disclosed, not hidden.
- [ ] T4e — Proposal (read-only): which live products to re-package, with sales/spend data kept.
  Proposal delivered 24-sep. Operator APPROVED re-packaging TINNIDROP and CLEARSTEM (24-sep).
  Not re-running F1 (both products are past it). For each product, after the T4d re-runs finish
  (so their frozen reads are not disturbed): `flujo.py <P>` → the real node `F2.etapa-11`
  (DIAGNOSTICO_CONGRUENCIA) → `etapa-guardar-producto` re-saves the folder to the current contract
  (4 role files, a PROPUESTAS DE VALOR section only if propositions already exist, since etapa-5
  writes them after the 2-of-2 winner). Sales and spend live in the _FACT_* CSVs and are not
  touched. NUSAVA only needs its 9 bot data points; VARICOSE (paused) and OVULOS_PURITY (in F1)
  are out.
  Follow-up (outside T4): `gen_plan.py --validar` should mark F1 plans of products past F1 as
  historical instead of failing them forever.

### T4a — writer W1 evidence (commit 50e0329)

Removed the 3 `expected_fail: true` etapa-6 `FASE 1 todo-en-imagen` tests (CLEARSTEM, NusavaB12,
TINNIDROP) from `evals/promptfooconfig.yaml` and the matching "Fallos conocidos" paragraph +
protocol count in `evals/README.md` (26/30→26/28). Fixtures `fixtures/etapa-6/{CLEARSTEM,NusavaB12,
TINNIDROP}.json` were NOT deleted: they are still consumed by the kept `etapa-6 / esquema _PLAN.json`
schema tests. `python evals/run_baseline.py` → `TOTAL=28 PASS=26 FALLO-CONOCIDO=2 FAIL=0` (exact
match to spec). `python -m pytest Ads/_TOOLS -q` → 42 passed (unchanged baseline).

### T4b — writer W1 evidence (commits bbb0d02, ba72cf7, cf6d1e2, addcdc0)

Route: delegated writer W1 — trigger: 2+ non-trivial files (4 commits, 8 files touched).

Removed archaeology (incident dates, "Historia: … POSTMORTEMS" pointers, "(agregado/decisión
DD-mmm)" tags, mentor-class date tags) while keeping every rule, threshold and number, per file
group:

| Commit | Files | Archaeology removed |
|---|---|---|
| bbb0d02 | DATA_PLAYBOOK.md, CONTABILIDAD.md, MCP_PLAYBOOK.md, PROTOCOLO_FACTURACION.md | ~30 dated asides / Historia-pointer sentences; 1 real-product example (NUSAVA 5-grafías) genericized (E) |
| ba72cf7 | CALENDARIO_ESCALADO.md | 1 full "medido 02-sep" investigation paragraph trimmed to its actionable rule; 4 date tags on headings |
| cf6d1e2 | GUIA_MADRE_PARAMETRIZADA.md, ETAPA-RESEARCH.md | 4 `Historia: _CONOCIMIENTO/POSTMORTEMS/…` pointers stripped from the Justificación column only (Fuente column untouched, per operator decision); 1 dated heading/origin citation trimmed |
| addcdc0 | CLAUDE.md | "absorbida de la extinta etapa-fanpage — T1 p2-simplificacion" / "T3 p2-simplificacion" / "(decisión operador 22-sep-2026)" tags removed from the etapa map and F1-todo-imagen rule; rule text kept identical |

**F anchors preserved verbatim (spot-checked):** `gasto.py` `2026-09-06` cutoff (DATA_PLAYBOOK,
CLAUDE.md), `[REG_MSPAS]`/`[REG_FDA]` values (not touched — file not in this pass), GUIA_MADRE
Fuente column (all 88 rows), CLI canonical examples, all thresholds/formulas ($2.99, $5.98, 1×BE,
30%, 35%, 3152.5, etc.) byte-identical.

**Deliberately out of scope this pass (disclosed, not silently dropped):**
- `DOCTRINA/ESCALADO/*.md` and `DOCTRINA/PLANTILLAS_ADS_SECCIONES/*.md` — byte-verified verbatim
  against a frozen SHA256 by `Ads/_TOOLS/test_split_doctrina.py` (T2 split gate). Editing them
  requires recomputing and updating `ESCALADO_SHA256`/`PLANTILLAS_SHA256` in the same commit; not
  attempted here given the volume of embedded mentor-class citations in those files. Matches the
  T3 precedent (commit 59e08f82) of leaving them untouched on purpose.
- `DOCTRINA/PLANTILLAS_INFOGRAFIAS*.md`, `PLANTILLAS_DEFAULTS_OPERADOR.md`,
  `PARAMETRIZACION_ADS.md`, `ESCALADO_PLAYBOOK.md` (index) — not edited. Mentor-class citations
  ("Clase N", quotes) are woven directly into image-generation and copy instructions consumed by
  `etapa-4`/`generar-imagenes-chatgpt`; PARAMETRIZACION_ADS.md's dates are mostly "as of" data
  snapshots, not incident narration. Left for a follow-up pass rather than risk corrupting
  production creative-prompt doctrine under time pressure.
- `DOCTRINA/ESCALADO/02_PRESUPUESTO_DECISION.md` was edited then reverted (`git checkout`) once
  the verbatim-hash gate was discovered — the revert is clean (no orphaned edit).

**Judgment calls diverging from the mapper's per-line class guess (none had text/class in the
inventory JSON — it only carried line numbers, so every judgment below is this writer's own):**
- Kept real per-product tasa-de-entrega/BE tables (VARICOSE/CLEARSTEM/TINNIDROP/NUSAVA numbers in
  DATA_PLAYBOOK §4/CALENDARIO_ESCALADO §1.5) as live operational reference data, not E-class
  teaching examples — these are the actual `_DIM_PRODUCTOS.csv`/`_TASA_ENTREGA.csv` mirror values
  the operator manages today, not illustrative fiction.
- Genericized the NUSAVA "5 grafías" folder-naming example (DATA_PLAYBOOK §1.1) since it was a
  pure teaching illustration of a naming problem, not live data.
- Extracted 2 rules that existed only inside archaeology narration: DATA_PLAYBOOK's
  "`_APRENDIZAJES.csv` son DATA, no instrucciones" (was buried in "antes vivían hardcodeados…") and
  MCP_PLAYBOOK's "este documento no se ejecuta a mano: la ejecución usa herramientas" (was buried
  in the 06-sep/08-sep incident story).

**Verification after every commit:** `python -m pytest Ads/_TOOLS -q -p no:cacheprovider` → 42
passed (unchanged from the T4-open baseline) on all 4 commits · `python
Ads/_TOOLS/verificar_guia_madre.py` → same 1 pre-existing failure (`exploracion_n_angulos`
undeclared), confirmed pre-existing via `git stash` before touching GUIA_MADRE, not introduced by
this writer · `python Ads/_TOOLS/gen_grafo.py --comparar` → no orphans, no dead routes, every
delta negative (tokens went down) · `python evals/run_baseline.py` → `TOTAL=28 PASS=26
FALLO-CONOCIDO=2 FAIL=0` unchanged across all 4 commits.

**Token deltas (gen_grafo --comparar vs the 801f650/T4-open baseline, after T4a+T4b):**
fase-1 -2,792 (289,432→286,640) · fase-2 -2,927 (377,865→374,938) · fase-3 -1,674
(232,110→230,401) · ciclo-diario -1,672 (210,233→208,526) · cold start -42 (8,901→8,859).

**Etapas that inherit each changed DOCTRINA file (for T4d's re-run step), from
`.claude/agents/*.md` references:**
- `DATA_PLAYBOOK.md` → `etapa-2`
- `MCP_PLAYBOOK.md` → `etapa-6`, `etapa-7`
- `CALENDARIO_ESCALADO.md` → `etapa-4`, `etapa-6`
- `ETAPA-RESEARCH.md` → `etapa-1b`, `etapa-guardar-producto`
- `GUIA_MADRE_PARAMETRIZADA.md` → no agent cites it directly (consumed by
  `Ads/_TOOLS/verificar_guia_madre.py` and human reading only)
- `CONTABILIDAD.md`, `PROTOCOLO_FACTURACION.md` → no agent cites them (operator/finance reference)
- `CLAUDE.md` → the orchestrator itself, loaded every session
Of these, only `etapa-2`, `etapa-4`, `etapa-6`, `etapa-7`, `etapa-guardar-producto` have fixtures
per T4d's list — `etapa-1b` changed prose inheritance (ETAPA-RESEARCH.md) but has no fixture, so
per T4d it "changes prose only and cannot be re-verified" (disclosed, not hidden).

### T4b — writer W2 evidence (commits cce951c, 9f92425, 7c89f72, 938b061, 61a7fbc)

Route: delegated writer W2 — trigger: 2+ non-trivial files (4 docs commits + 1 chore commit,
16 doctrine files touched). Finished the DOCTRINA files W1 deliberately left out: the two
verbatim-hash-gated folders (`DOCTRINA/ESCALADO/*.md`, `DOCTRINA/PLANTILLAS_ADS_SECCIONES/*.md`)
plus their index files, `PLANTILLAS_INFOGRAFIAS*.md`, `PLANTILLAS_FLUJO_BOT.md` and
`ETAPA-RECOLECCION.md`. `.claude/agents` and `.claude/skills` are out of scope for this pass
(reserved for W3/T4c).

**Work unit 1 — `DOCTRINA/ESCALADO/*.md` + `ESCALADO_PLAYBOOK.md` index (commit cce951c).**
Removed date tags, incident narration ("Historia: …POSTMORTEMS…" pointers, "Decisión del
operador (DD-mmm)", "(clase DD-ago)" mentor-class citations, "actualizada DD-mmm-YYYY") from
`00`→`10` section files and the index heading, keeping every rule, threshold and number
identical. The `test_split_doctrina.py` verbatim gate covers these section files (not the
index): recomputed `ESCALADO_SHA256` with the test's own `reconstruir()`/`sha256()` logic and
updated the constant + comment in the same commit, exactly as its docstring requires.

**Work unit 2 — `DOCTRINA/PLANTILLAS_ADS_SECCIONES/*.md` + `PLANTILLAS_ADS.md` index (commit
9f92425).** Same pattern: date tags and origin narration removed from `00_INTRO`,
`01_COMPLIANCE_ANDROMEDA`, `03_CUAL_PROMPT_USAR`, `04_PROMPT_CONTROL_FASE1`, `10_ELEMENTOS_EXTRA`,
`11_DOCTRINA_CREATIVOS_VIDEO_IMAGEN` and the index heading. Recomputed and updated
`PLANTILLAS_SHA256` in the same commit.

**Work unit 3 — `PLANTILLAS_INFOGRAFIAS*.md` (commit 7c89f72).** Removed date tags and origin
narration from `PLANTILLAS_INFOGRAFIAS.md` (§ADAPTACIÓN POR ÁNGULO, §PASO 0, §tipografía) and
`_FLUJO.md`/`_OPCIONALES.md`. Genericized the "Nusava B12 = SIEMPRE 2x1" and "(ej. Nusava: …)"
teaching examples per the E-class rule (kept the numbers/behavior, dropped the product name).
`PLANTILLAS_DEFAULTS_OPERADOR.md` left untouched on purpose: its only 2 inventory hits are the
`[REG_MSPAS]`/`[REG_FDA]` real registry values and their entrega dates — F-anchor, never touched.

**Work unit 4 — `PLANTILLAS_FLUJO_BOT.md` + `ETAPA-RECOLECCION.md` (commits 938b061, 61a7fbc).**
`PLANTILLAS_FLUJO_BOT.md`: dropped the mentor-quote/evidence column from the §0 "LO QUE MANDAN
LAS DOS CLASES DE AGOSTO" rules table (A-L), keeping the rule column verbatim and the `#`/heading
structure untouched (checked `§0` is cross-referenced from `ETAPA-5.md`/`contratos.py`, so the
heading itself was not renamed). Verified first that `gen_flujo_bot.py`/`test_gen_flujo_bot.py`
only parse "## 3. LA PLANTILLA" (the `{{var}}`/`<<BLOQUE:x>>`/`>>` block) — the A-L table lives
outside it, so removing its citation column is safe. Left every `>>` instruction line inside
"## 3. LA PLANTILLA" byte-for-byte untouched, including the ones carrying `(clase 16-ago)` /
`(dato operador 23-sep)` tags (lines 177, 184, 191, 226, 389, 397) — those are parsed template
content, not prose, per the writer's brief. Removed one date tag from a prose paragraph outside
the template (line ~156). `ETAPA-RECOLECCION.md`: genericized the `5. Nusava B12.mp4` filename
example. `DOCTRINA/PARAMETRIZACION_ADS.md` judged and left untouched: re-judged its 2 inventory
hits (`**Fecha:** 2026-09-06`, `## 7. DEUDA ABIERTA (al 2026-09-06)`) as "as of" data snapshots,
not incident/decision narration — same call W1 made, confirmed rather than assumed.

**Verification after every commit:** `python -m pytest Ads/_TOOLS -q -p no:cacheprovider` → 42
passed on all 4 units · `python Ads/_TOOLS/test_split_doctrina.py` → 5/5 PASS after unit 1 and
unit 2 (hash re-frozen) · `python Ads/_TOOLS/test_gen_flujo_bot.py` → TODO PASA after unit 4 ·
`python Ads/_TOOLS/gen_flujo_bot.py --validar` → 2/5 productos pasan, identical shape/blockers
before and after unit 4 (prose-only edit, no template line touched) · `python
Ads/_TOOLS/verificar_guia_madre.py` → same 1 pre-existing failure (`exploracion_n_angulos`
undeclared) on all 4 units · `python Ads/_TOOLS/gen_grafo.py --comparar` → no orphans, no dead
routes, every delta negative, on all 4 units · `python evals/run_baseline.py` → `TOTAL=28
PASS=26 FALLO-CONOCIDO=2 FAIL=0` unchanged across all 4 units. Baseline re-saved with
`--escribir` after unit 4 (commit 61a7fbc).

**Token deltas (gen_grafo --comparar vs the 801f650/T4-open baseline, W1+W2 combined):**
fase-1 −4,739 (289,432→284,693) · fase-2 −5,963 (377,865→371,902) · fase-3 −3,888
(232,110→228,222) · ciclo-diario −3,046 (210,233→207,187) · cold start −42 (8,901→8,859).
Read-only `gen_grafo.py --comparar` immediately after the baseline save confirmed all deltas at
`=` (0), i.e. the saved baseline matches disk exactly.

**Etapas that inherit each file W2 changed (grepped `.claude/agents/*.md` and
`.claude/skills/*/SKILL.md` for the filename):**
- `DOCTRINA/ESCALADO/{02,04,06,08,09,10}_*.md` + index → via `ESCALADO_PLAYBOOK.md`'s own "Quién
  lo lee" column: `etapa-6`, `etapa-7`, `etapa-10`, `etapa-11`, `etapa-guardar-producto`,
  `fase-2-conceptos`, `fase-3-escalado`, `generar-conceptos` (§02 has no agent reader — only
  `decidir.py` over the CSV).
- `DOCTRINA/PLANTILLAS_ADS_SECCIONES/{00,01,03,04,10,11}_*.md` + index → `etapa-2`
  (`11_DOCTRINA_CREATIVOS...`), `etapa-4` (`01_COMPLIANCE_ANDROMEDA`, `04_PROMPT_CONTROL_FASE1`,
  `11_DOCTRINA_CREATIVOS...`), `etapa-9` (`01_COMPLIANCE_ANDROMEDA`, `11_DOCTRINA_CREATIVOS...`).
  `00_INTRO`/`03_CUAL_PROMPT_USAR`/`10_ELEMENTOS_EXTRA` have no direct agent citation (reached
  only via the index/whole-file path).
- `PLANTILLAS_INFOGRAFIAS.md` → `etapa-4`, `etapa-guardar-producto`.
- `PLANTILLAS_INFOGRAFIAS_FLUJO.md`, `PLANTILLAS_INFOGRAFIAS_OPCIONALES.md` → `etapa-4`.
- `PLANTILLAS_FLUJO_BOT.md` → `etapa-5`, `etapa-11`, skills `fase-1-angulos`, `fase-2-conceptos`,
  `fase-3-escalado`, `generar-conceptos`.
- `ETAPA-RECOLECCION.md` → skill `fase-1-angulos`.
Of these, per T4d's fixture list: `etapa-2`, `etapa-4`, `etapa-6`, `etapa-7`,
`etapa-guardar-producto` have fixtures to re-run against; `etapa-5`, `etapa-9`, `etapa-10`,
`etapa-11` are mixed (some have fixtures per T4d's earlier list, `etapa-5`/`etapa-11` do not) —
T4d's own per-etapa list is the source of truth, this is only the file→etapa map for it.

### T4c — writer W3 evidence (commits 05da541, 541fc22, 3c92512, eab196b, a471498)

Route: delegated writer W3 — trigger: 2+ non-trivial files (4 content commits across 17 files +
1 chore commit). Scope: `.claude/agents/*.md` (15 files) and `.claude/skills/*/SKILL.md` (9
files) — the only zones T4b's writers left untouched. Read `arqueologia_inventario.json` from
the mapper's scratchpad (line-numbered per-file hits, no text/class — every judgment below is
this writer's own, re-derived from context, same as W1/W2 report).

**Work unit 1 — ETAPA-2/4/6 creation etapas (commit 05da541).** ETAPA-2.md: dropped the
`(absorbido de ETAPA-FANPAGE, T1 p2-simplificacion)` heading tag, the "idéntico al que producía
antes ETAPA-FANPAGE" narration, `(corregida 02-sep)`/`(agregado 02-sep — M-E06, clase 22-ago)`/
`(regla corregida 19-ago …)` tags, and genericized the TINNIDROP `[APR-008]` example.
ETAPA-4.md: dropped `(22-sep-2026)`/`(19-ago)` decision tags and the "Cambio del 02-sep-2026"
paragraph, keeping only the still-live rule (ángulo+copy fijos en FASE 2, microángulos alimentan
FASE 3/etapa-9). ETAPA-6.md (largest, 20 date hits + 6 product hits): dropped date tags on 3
headings (`BANDA DE EDAD`, `TRES REGLAS…`, `Reglas de la arquitectura de 3 fases`,
`OUTPUT OBLIGATORIO…`), the "(Antes del 15-sep-2026 esta tabla vivía triplicada…)" and "Por qué
existe (caso real 2026-08-01)" incident paragraphs (compressed to the still-true rationale),
M-A10/M-B03 mentor-class date suffixes, and genericized `tinnidrop 6` / `tinnidrop 6 - Copia` to
`producto 6`. **Fixed one stale reference found in passing** (not just archaeology): ETAPA-6.md
line 104 still pointed at the deleted `ETAPA-FANPAGE.md` (T1 removed that file, but this pointer
survived) — repointed to `ETAPA-2.md §ASIGNACIÓN DE FANPAGE`, the current owner. ETAPA-5.md: **no
edits** — its 3 product hits (CLEARSTEM ×2, TINNIDROP ×1) are live operational-status references
("CLEARSTEM y TINNIDROP siguen renderizando mientras se retrocompletan") and a canonical fixture
pointer ("la referencia de largo y tono es la fila de CLEARSTEM"), not archaeology; no date hits.

**Work unit 2 — ETAPA-7/9/GUARDAR-PRODUCTO ops etapas (commit 541fc22).** ETAPA-7.md: dropped the
T3-fusion history paragraph ("Antes esto eran dos etapas… se fusionaron el 24-sep-2026"), 5 more
date/task-tag citations (`g07-cimientos T2, 22-sep-2026`, `desde 25-jul`, `cambió el
2026-07-25`, `auditadas 02-sep…Q2,622`, `decisión del 09-sep-2026`), and genericized 4 examples
(`caso Nusava`, `caso real CLEARSTEM 10-jul`, `TINNIDROP "se corrió" tres veces`, `tinnidrop-1
78%→0v`). Kept the `gasto.py` `2026-09-06` cutoff verbatim (F-anchor) and the `APR-009 en
TINNIDROP` citation (real per-product learning row, not narration). ETAPA-9.md: compressed the
"Por qué existe" origin story (14 subagentes, 8 doctrina, 64 aprendizajes, 15 CSV vs 19
creativos) to the still-actionable benchmark numbers, genericized the TINNIDROP-26-jul PNG
example (kept 8/1/7/26 as numbers), and replaced the M-D06 "clase 16-ago" mentor quote with a
present-tense statement of the technique — verified steps 1-3 below it already carry the full
method, so nothing was lost. ETAPA-GUARDAR-PRODUCTO.md: genericized the `31-jul` NUSAVA
`csv.DictWriter` bug example (kept 20/17 field counts) and replaced the stale "Estado al
2026-09-02: 7 de 8 productos pasan" snapshot (a point-in-time status, not a rule, and one that
predates today) with a dateless, product-generic illustration of the same silent-drift failure
mode.

**Work unit 3 — remaining .claude/agents (0, 1, 3, 10, 11, render, producto) (commit 3c92512).**
ETAPA-0.md: 1 date tag removed. ETAPA-1.md: `UNA SOLA ESCALERA`/`COSTEO_COMPLETO_VITALCOM`/
`GARANTÍA COMO PALANCA` headings de-dated; genericized 3 repeated TINNIDROP/NUSAVA/CLEARSTEM
row-selection worked examples and 2 VARICOSE combo-pricing examples (all numbers kept
byte-identical). ETAPA-3.md: compressed the `etapa-3a`/`etapa-3b` merge-history story to a
present-tense justification (the input/output chaining argument, without the `2026-09-02` merge
date). ETAPA-10.md: dropped `clase 22-ago` and the T3-fusion tag. ETAPA-11.md (7 date hits + 2
product hits — most sensitive file, protected by `test_ab_flujo.py`'s PASO 6/7 token gate):
removed `Decisión del operador (02-sep)`, the `hasta el 16-sep-2026` design-history tag (kept the
GEMELOS evidence table and every protected token untouched), and genericized the VARICOSE
envase-mismatch example in both places it appears (PASO 0 and the Reglas fijas list) so the two
stay consistent. Left the two `17-jul → 01-sep-2026` close-rate measurement windows untouched —
they define the actual evidence window behind the 8.6%/15-20% numbers, not incident narration
(same call as APR-060 tables W1/W2 kept). ETAPA-RENDER.md: removed the 1 incident date
("Pasó el 07-sep-2026 en la primera corrida"). ETAPA-1B.md and ETAPA-PRODUCTO.md: confirmed
clean (0 hits in the mapper inventory, 0 found on a manual date-pattern re-scan).

**Work unit 4 — .claude/skills/*/SKILL.md (commit eab196b).** 8 of 9 skills had hits
(`buscar-producto` had none). `ciclo-diario`: 3 headings de-dated, `caso NusavaB12`/`TINNIDROP
26 días`/`NUSAVA del 31-jul` genericized. `fase-1-angulos`/`fase-2-conceptos`/`fase-3-escalado`:
the shared `## EL FLUJO DICTA (desde el 09-sep-2026)` heading de-dated identically in all three
(not renamed structurally, just the date suffix — none of the three headings are cross-referenced
by name elsewhere); genericized the `5. Nusava B12.mp4` filename example (same pattern W2 used
for `ETAPA-RECOLECCION.md`) and dropped the `T8-4 (23-sep-2026)`/`clase 22-ago` tags.
`generar-conceptos`: 1 decision-date tag removed. `generar-imagenes-chatgpt` (6 hits): compressed
the "Esto costó tres corridas el 08-sep-2026" CN01 incident narrative to its operative rule,
dropped 2 more incident dates, kept the REG_MSPAS/REG_FDA values untouched (F-anchor).
`publicar-meta`: genericized 3 incident examples ($23.46/10 anuncios/$166) to "caso real",
numbers kept. `recopilar-lucidsales` (10 hits, the most in any skill): de-dated 4 headings/labels,
compressed a 5-date calibration list (`06/14/15/16/20-sep-2026`) to its operative percentage
range (0.65-0.75), and de-dated 2 more incident notes. Left the 2 `--fecha 2026-09-0N` CLI
canonical examples untouched (F-anchor).

**Frontmatter cases found:** none. No agent or skill frontmatter (`name`/`description`/`tools`/
`model`) carried a date or archaeology tag in this scope.

**Judgment calls diverging from a literal per-hit read (mapper inventory had no text/class, only
line numbers — every call below is this writer's own):**
- Kept measurement-window evidence with real dates where the dates ARE the definition of the
  measured window (ETAPA-11's `17-jul → 01-sep-2026` close-rate series; ETAPA-7's `APR-060`-style
  evidence is already handled by W1/W2's ESCALADO split). Removed dates that were pure "when this
  was decided/detected/changed" tags layered on top of an already-stated rule.
- Fixed the dead `ETAPA-FANPAGE.md` pointer in ETAPA-6.md (a T1-leftover bug, not just
  archaeology) rather than leaving a broken reference under an archaeology-only mandate.
- Replaced ETAPA-GUARDAR-PRODUCTO.md's stale "Estado al 2026-09-02: 7 de 8 productos pasan"
  status line rather than just stripping its date, since the claim itself is a point-in-time
  snapshot (not a standing rule) that is likely already false 3 weeks later; kept the underlying
  illustration of what silent drift looks like.
- Left ETAPA-5.md fully unedited — its only 3 inventory hits are live operational references, not
  narration, so there was nothing to remove without inventing a change.

**Verification after every commit:** `python -m pytest Ads/_TOOLS -q -p no:cacheprovider` → 42
passed on all 4 commits (unchanged from the T4-open baseline) · `python
Ads/_TOOLS/test_ab_flujo.py` → 0 fallas after the ETAPA-11.md/ETAPA-5.md edits (GEMELOS,
ab_flujo.py, _TESTEOS.csv, test_id all present in PASO 6; old-design phrase absent; ETAPA-5 still
has `gemelo`) · `python Ads/_TOOLS/verificar_guia_madre.py` → same 1 pre-existing failure
(`exploracion_n_angulos`) on all 4 commits · `python Ads/_TOOLS/gen_grafo.py --comparar` → no
orphans, no dead routes, every delta negative or zero, on all 4 commits · `python
evals/run_baseline.py` → `TOTAL=28 PASS=26 FALLO-CONOCIDO=2 FAIL=0` unchanged across all 4
commits · `python Ads/_TOOLS/flujo.py --todo` (read-only, no `--escribir`) → same 5 products, same
node names/gates/sequences before and after every commit (spot-checked OVULOS_PURITY throughout).
Baseline re-saved with `--escribir` in a separate `chore(auditorias)` commit (a471498), matching
W2's pattern.

**Token deltas — T4c-only (gen_grafo --comparar vs the T4-open-after-T4b baseline, i.e. after
W1+W2's `284,693 / 371,902 / 228,222 / 207,187 / 8,859`):**
fase-1 −528 (284,693→284,165) · fase-2 −710 (371,902→371,192) · fase-3 −765 (228,222→227,457) ·
ciclo-diario −500 (207,187→206,687) · cold start = (8,859→8,859, unchanged).

**ABSOLUTE per-phase totals and deltas vs the ORIGINAL 801f650 baseline (f1 289,432 · f2 377,865
· f3 232,110 · ciclo 210,233 · cold start 8,901), computed explicitly as instructed:**

| Phase | 801f650 baseline | Current (end of T4c) | Delta |
|---|---|---|---|
| fase-1-angulos | 289,432 | 284,165 | **−5,267** |
| fase-2-conceptos | 377,865 | 371,192 | **−6,673** |
| fase-3-escalado | 232,110 | 227,457 | **−4,653** |
| ciclo-diario | 210,233 | 206,687 | **−3,546** |
| arranque en frío (cold start) | 8,901 | 8,859 | **−42** |

Zero orphans (`.md sin consumidor: ninguno`), zero dead routes, 15 agentes / 9 skills / 39 CSV
(unchanged inventory shape from T3's close).

## T4d — fixture package for the parent's re-run (this section is data for T4d, not T4d itself)

For each fixture-backed etapa T4c touched, the fixture path(s) and the frozen-input package that
produced them (per `evals/README.md`'s "Protocolo de poda" and the P2 doc's T1-T3 re-run notes):

- **`etapa-2`** — `evals/fixtures/etapa-2/{CLEARSTEM,NusavaB12,OVULOS_PURITY}.txt`. Frozen inputs:
  each product's `2_DATA_PRODUCTO.txt` §ÁNGULOS/§CONJUNTOS sections (T2's own list; unchanged by
  T4c) + `PRODUCTOS/_DIM_FANPAGES.csv` for the FanPage assignment section T4c edited.
- **`etapa-4`** — `evals/fixtures/etapa-4/TINNIDROP.txt` (+ `SOURCE.txt`). Frozen inputs:
  `PRODUCTOS/TINNIDROP/1_HACER_MANUAL.txt` §PARTE 4, same as T2's list — T4c only touched
  ETAPA-4.md's F1/F2 framing prose, not the copy-structure rules the fixture checks.
- **`etapa-6`** — `evals/fixtures/etapa-6/{CLEARSTEM,NusavaB12,TINNIDROP,OVULOS_PURITY}.json` —
  full `_PLAN.json` inputs per product, same as T2's list. T4c edited BANDA DE EDAD, CONVENCIÓN DE
  NOMBRES and the FASE 3 escalado block; the `_PLAN.json` schema/values referenced are unchanged.
- **`etapa-7`** — `evals/fixtures/etapa-7/{TINNIDROP,TINNIDROP_FUSIONADO}.txt` (+ `SOURCE*.txt`).
  Frozen inputs: `PRODUCTOS/_AUDITORIAS/_AUDITORIA_DIARIA_20260908.txt` §PASO 3 (T2's list) for the
  non-fused fixture; the `TINNIDROP_FUSIONADO` fixture is T3's own frozen 2026-09-08 audit excerpt.
  T4c only touched ETAPA-7.md's sourcing/history prose (JERARQUÍA DE FUENTES framing, PASO 1
  callouts) — no PASO 4/5 template wording changed, so both existing asserts (`etapa-7.py`,
  `etapa-8.py` via the fused test) should still apply unchanged.
- **`etapa-9`** — `evals/fixtures/etapa-9/TINNIDROP.csv` (+ `SOURCE.txt`). Frozen inputs:
  `PRODUCTOS/_DIM_CREATIVOS.csv` tanda inputs for TINNIDROP, day 2026-09-06 (T2's list). T4c edited
  the "Por qué existe" rationale and the PASO 2-BIS video-to-image technique framing, not PASO 3's
  delegated-fill contract the assert checks.
- **`etapa-guardar-producto`** — `evals/fixtures/etapa-guardar-producto/{CLEARSTEM,NusavaB12,
  TINNIDROP,OVULOS_PURITY}.json`. Frozen inputs: each product's top-level file manifest (T2's
  list). T4c only touched SALIDA 5's bug-example/status-snapshot prose, not the file-role
  vocabulary or the gate script's behavior.
- **`etapa-5`** — not re-run-relevant: T4c made no edits to ETAPA-5.md.

Etapas T4c edited without a fixture (per T4d's own list, disclosed not hidden): `etapa-0`,
`etapa-1`, `etapa-3`, `etapa-10`, `etapa-11`, `etapa-render`. `etapa-11` additionally has the
non-eval `test_ab_flujo.py` structural gate, which already passed (see Verification above).

## Next step
T4d — the parent re-runs the fixture-backed etapas above on their frozen inputs and confirms the
existing asserts still pass, then runs `gen_grafo.py --comparar` once more for a final sanity
check. After T4d, T4e (read-only re-packaging proposal) is the last open item.
