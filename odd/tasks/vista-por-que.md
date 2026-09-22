# Feature: vista-por-que

## Objective
Make the app tell the operator (non-programmer), per product and in plain Spanish: current phase and step,
who does it (operator / AI / system), the next concrete step, and WHY the engine keeps, renews or kills each
angle, with the evidence it used.

## Problem
After launch the operator loses the thread. Today the explanation is split across Tablero, ProductoDetalle,
Ordenes and Fase1/2/3. Ordenes shows raw numbers (IC, BE, faltan_ventas) without narrating them; the three
engine clocks and RENOVAR-vs-PAUSAR reasoning are not shown; internal node ids leak (F2.etapa-11).
Also the backend suite hangs (test_meta.py / DBOS teardown), so the closing gate cannot run.

## Constraints
- The app computes nothing: every number comes from `_DECISIONES.json`, `flujo.py --sin-escribir`,
  `_PARAMETROS_DECISION.csv`. `app/backend/tests/test_sin_aritmetica.py` must stay green.
- No Meta mutation paths are added or enabled.
- Development happens in worktree SISTEMA-app (branch feat/app-web) with `VITALCOM_BASE` pointing to
  ../SISTEMA for real data. SISTEMA (production folder) never changes branch; delivery = fast-forward.
- UI copy in neutral Spanish (existing project language).

## Mode
- TDD: off (no project/session configuration found; source: default). Ordinary functional checks run.
  Runners: backend `uv run pytest` (app/backend), frontend `pnpm test` (app/frontend).
- RDD: off (gentle-ai review mode status: default).
- Delivery strategy: ask-on-risk.

## Tasks
- [x] T1 — Backend suite terminates: add pytest-timeout as a per-test safety net. Correction
      (21-sep, confirmed twice): the suite does NOT actually hang — a clean, single-process run
      finishes `160 passed in 290s (0:04:50)`. The earlier "hang" reports were the auditor running
      several overlapping `uv run pytest` invocations in the background without confirming the
      previous one had exited; `tasklist`/`ps` showed 5+ orphaned `python.exe`/`pytest.exe`
      processes still alive from earlier attempts, competing for CPU/DBOS threads on the same
      machine. Killing them and re-running once, alone, with a real timeout (100s) then a
      generous one (up to 28 min) reproduced no hang at any size (3 tests, 12 tests, 26 tests
      excluding one, and the full 160). No DBOS/queue teardown code was touched. Added
      `pytest-timeout>=2.3` (dev dep, `uv sync`'d) and `timeout = 120` under
      `[tool.pytest.ini_options]` in `app/backend/pyproject.toml` as a per-test ceiling only, so a
      genuinely hung test fails with its own traceback instead of ever blocking the suite again.
      Route: inline (mechanical, 1 file + lockfile).
- [ ] T2 — Single product card: phase, current step in plain words, who does it, next concrete step,
      blockers with their owner; no raw node ids as primary text. Route: delegated (writer).
- [ ] T3 — Narrated orders: per order a sentence narrating IC vs break-even, a progress bar of current vs
      needed sales, the three clocks (ventana_dias, ventana_fatiga_dias, duracion_testeo_fase2_dias) read from
      the CSV, why RENOVAR vs PAUSAR, and a data-freshness warning on top. Route: delegated (writer, with T2).
- [ ] T4 — Verify in browser against real SISTEMA data (today's date), screenshots. Route: inline.

## Acceptance criteria
- Full backend and frontend suites finish green; test_sin_aritmetica green.
- For TINNIDROP and NUSAVA the card and orders show 21-sep data and match `flujo.py --todo`.

## Progress / evidence
- 2026-09-21: feat/app-web fast-forwarded into production branch by operator (1950e19). Engine tests
  green in SISTEMA: test_flujo 29/29, test_decidir 17/17, flujo.py --validar OK.

## Next step
T2.
