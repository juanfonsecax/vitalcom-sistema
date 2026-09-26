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

## Next step
Observe the 2026-09-27 07:11 run: message still carries profit, sales and CPA.
