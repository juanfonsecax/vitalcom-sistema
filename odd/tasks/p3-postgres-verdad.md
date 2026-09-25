# P3 — Postgres becomes the source of truth (CSV as mirror)

## Objective
Invert the data direction: program writers write to Postgres `core`, and `PRODUCTOS/*.csv` become
a mirror regenerated from the database. Readers (`decidir.py`, app backend) read from Postgres.

## Problem / why
P1 built `raw` + `core` loaded one-way from the CSVs (full TRUNCATE + reload) with a parity gate
(`decidir.py` over exported `core` == over real CSVs). No real reader or writer uses Postgres yet.
Gated plan P1→P6 (engram `plataforma/plan-compuertas`) places the switch of truth in P3.

## Scope (authorized 2026-09-25, operator: "sí, apruebo el plan, arrancá con T1")
Branch `feat/p3-postgres-verdad` from `ac7696f`. Operator's uncommitted files are never touched or
staged: `PRODUCTOS/_EVENTOS.csv`, `.claude/launch.json`, `.claude/settings.local.json`,
`PRODUCTOS/_AUDITORIAS/`.

## Decisions (operator, 25-sep)
- Operator-edited dimension CSVs stay OUT of P3: they keep entering through CSV → `raw` → `core`
  as today. Truth is split during P3 (DB for program-written tables, CSV for hand-edited dims).
- P3b (after P3 closes): app screens to edit those dimensions; then they move to Postgres too.
- Closing criterion: 7 consecutive calendar days with a green daily run, launched by Windows Task
  Scheduler at PC boot ("run as soon as possible after a missed start"). A failed or missing day
  resets the counter. Not "7 nights": the PC is off at night.
- Reason: the Claude scheduled task `auditoria-vitalcom-diaria` reports "succeeded" but stops
  after its first command (~6 s runs on 22/23/24-sep; 20-21 missing; 19 failed by spend limit).
  The deterministic cycle must not depend on it; the Claude task keeps only the written analysis.

## Technical decisions (orchestrator)
- Writers write to `core`; `raw` stays as the entry for operator-edited CSVs.
- Writes become incremental (upsert by key), no longer full reload.
- If Postgres is down during the daily run, the day is red. Never silently fall back to CSV writes.

## Config
- TDD: off (no project/session TDD configuration; source: none). Ordinary checks per task.
- Runners: `db/` tests `..\SISTEMA-app\app\backend\.venv\Scripts\python.exe -m pytest db/test_db.py -q`;
  `Ads/_TOOLS` tests with system `python -m pytest`; backend `cd app/backend && uv run pytest`;
  frontend e2e `app/frontend/e2e`.
- RDD: off (default).
- Delivery strategy: ask-on-risk.

## Tasks
- [x] T1 — Writer inventory: every `PRODUCTOS/*.csv` → who writes it (script, app, operator) →
  moves to DB in P3 or stays on CSV. Includes `_DIM_ENVASE.csv` written by the app's product
  onboarding. Route: delegated mapper (trigger: 40+ files to trace). Output: section
  "P3 — inventario de escritores" in `db/README.md`. Evidence: 3 cited writer lines spot-checked
  (`decidir.py:1010`, `flujo.py:1329`, `ingerir_lucidsales.py:516`); app→`alta_producto.py`
  confirmed in `VISTAS/_MANIFIESTO.json:809`.
  Result: DB set in P3 = `_FACT_VENTAS`, `_FACT_ENTREGA`, `_FACT_ENTREGA_ANUNCIO` (T3, single
  writer `upsert_fact.upsert()`), `_EVENTOS` (5 appenders), `_DECISIONES.json`, `_ESTADO_FLUJO`,
  `_DIM_PRODUCTOS` (T4). Hybrids `_DIM_CREATIVOS`/`_DIM_ENVASE` stay on CSV (hand-edited rule).
  Derived files stay generated. Found: `_DIM_ANUNCIOS` has two full-rewrite writers
  (`sembrar_anuncios.py`, `firma.py`) — out of P3 scope, noted.
- [ ] T2 — Incremental upsert into `core` + CSV mirror regeneration. Checks: idempotent run,
  mirror byte-identical.
- [ ] T3 — `bajar_lucidsales` / `bajar_meta_insights` (+ ingestors) write DB then mirror.
  Check: `decidir` parity green on real data.
- [ ] T4 — Events, decisions, `_ESTADO_FLUJO`, product onboarding write DB. Check: parity.
- [ ] T5 — `decidir.py` and app backend read from Postgres. Checks: parity, e2e, backend tests.
- [ ] T6 — Daily cycle script + Windows Task Scheduler task. Check: first real run writes its
  parity row.
- [ ] T7 — 7-consecutive-green-days counter. Closes P3.

## Progress
- 2026-09-25: branch created, feature document created.
- 2026-09-25: T1 done.

## Next step
T2 — incremental upsert into `core` + CSV mirror for the T3/T4 set.
