# auditoria-tecnica — low-risk fixes from the 2026-09-26 technical audit

## Objective
Apply the audit findings that were verified against the code and carry low regression risk.
Large structural changes (drop DuckDB, collapse operator views, convert agents to scripts,
split CLAUDE.md) are out of scope until real token usage is measured.

## Verified findings in scope
- Reentry gate (F2/F3 -> F1) never evaluates: `DOCTRINA/FLUJO.json:224,309` pass
  `"estado": [list]` and `flujo._ev_decision` wraps it again -> `"/".join` raises.
- Price-in-ad rule contradicts itself: `GUIA_MADRE_PARAMETRIZADA.md:221` says "max 1 of 6",
  the operative owner `COPYWRITING_ADS.md:132` says "max 3 of 6". Data (APR-005) and
  `MATRIZ_METODOLOGIA` M-D16 (`SIN-EVALUAR`) back the operative 3/6. No verifier covers it.
- Nightly task tells the model to read raw fact CSVs (~1.4MB) although `_DECISIONES.json`
  already carries the computed aggregate.

## Out of scope (pending, recorded)
- "Traer las ventas de LucidSales" button runs an LLM skill for two scripts. Coupled to
  `test_claude.py` (fixture), `workflows.py` nightly chain and `FLUJO.json` executor.
- Instrument real token usage per invocation before any bigger pruning.

## Constraints
- TDD: off (no project/session config). Runner: `python Ads/_TOOLS/test_*.py`.
- Route: all tasks inline (1-3 files each, already understood).

## Tasks
- [x] T1 Fix `_ev_decision` list handling + regression test in `test_flujo.py`.
- [x] T2 Align GUIA_MADRE price row with COPYWRITING_ADS and register a verifier.
- [x] T3 Nightly task reads the aggregate; raw facts only by targeted query.
- [x] T4 "Traer las ventas de LucidSales" button runs a script, not an LLM skill. It is the manual
      fallback when the 5 AM automation fails, so it must be deterministic and free.
      Route: delegated (manifest, workflows.py, FLUJO.json, test_claude.py, glosario: 4+ files).
- [x] T5 Measure real token usage per session/subagent from Claude Code transcripts (read-only
      tool). Route: inline (one new file).

## Checks
- `python Ads/_TOOLS/test_flujo.py`
- `python Ads/_TOOLS/verificar_guia_madre.py`
- `python Ads/_TOOLS/flujo.py --todo` shows no "error evaluando decision".

## Progress / evidence
- T1 e151330: RED observed (40/41), GREEN 41/41; live `flujo.py --todo` shows 0 "error evaluando".
- T2 781c37f: `verificar_guia_madre.py` exit 0; simulated drift (1 of 6) fails with exit 1.
- T3: repo copy updated. Profit is derivable from `_DECISIONES.json` (ETAPA-7.md:126), and
  etapa-7 reads the fact CSVs itself, so the session-level raw read was pure duplication.
  The scheduler runs a separate copy at
  `~/.claude/scheduled-tasks/auditoria-vitalcom-diaria/SKILL.md`; synced 2026-09-26 with operator OK
  (diff vs repo body: identical).

- T4: new `Ads/_TOOLS/recopilar_lucidsales.py` (script, no LLM) reuses `ciclo_diario.pasos_lucidsales(hoy)`
  (extracted from `pasos_reales`, single owner) — same argv as the nightly run's LucidSales leg,
  nothing else. Decision: it skips `ciclo_diario.py`'s Postgres preflight/postcheck and the
  `_CORRIDAS_DIARIAS.csv` row on purpose — `ingerir_lucidsales.py` already runs its own drift
  guard (`db_escribir.verificar_csv_sincronizado`) before writing a single row, so a second guard
  here would be redundant, and `_CORRIDAS_DIARIAS.csv` is the summary of one *complete* nightly
  run (T7), not of a partial LucidSales-only fallback. Updated consumers: `VISTAS/_MANIFIESTO.json`
  (`nodo.ciclo.datos` → `ejecutor_tipo: script`, mirrors `nodo.ciclo.motor`'s shape),
  `DOCTRINA/FLUJO.json` (`ciclo.datos` executor → script), `app/backend/vitalcom_app/workflows.py`
  (docstring only — `_PADRES` already routes by `ejecutor_tipo` generically, no special-casing
  needed), `app/backend/tests/test_claude.py` (`test_una_accion_global_no_le_pide_a_flujo_un_producto`
  now builds a `sello` by hand for `nodo.F2.etapa-11` and calls `workflows.prompt_del_nodo`
  directly, since no other enabled skill/subagente action is global — `nodo.ciclo.datos` was the
  only one), `.claude/skills/recopilar-lucidsales/SKILL.md` (one note: the skill stays for manual
  CLI use only). `glosario.ts` line 109 documents the "rezago" doctrine owned by
  `recopilar-lucidsales`'s SKILL.md, not the app button, so left unchanged.
  Checks: `python Ads/_TOOLS/test_flujo.py` 41/41 · `python Ads/_TOOLS/verificar_guia_madre.py`
  exit 0 · `python Ads/_TOOLS/test_ciclo_diario.py` 28/28 (2 new: `pasos_lucidsales` mirrors
  `pasos_reales`'s prefix, Monday control) · `python Ads/_TOOLS/test_gen_app.py` 51/51 (manifest
  still valid) · backend `.venv` pytest: `test_claude.py` 20/20, `test_ciclo_nocturno.py` 2/2,
  `test_workflows.py`+`test_acciones_api.py` 31/31 · `recopilar_lucidsales.py --dry-run` prints
  the 2-step plan (4 on a simulated Monday). Commit: 5836337.

## Next step
Observe the 2026-09-27 07:11 run: message still carries profit, sales and CPA.
- T5: `Ads/_TOOLS/medir_tokens.py` (read-only) + `test_medir_tokens.py` 4/4. Real usage 2026-09-01..26:
  13,230 model calls. ~97% of context is development sessions (principal + general-purpose);
  business stages combined ~3% (largest: etapa-render 41M, etapa-7 27M context tokens, mostly
  cache reads). Cache reads 3,030M vs cache writes 72M vs uncached input 33K: caching dominates.
  Conclusion: the audit's premise (runtime doctrine is the main spend) does not hold on real data.
