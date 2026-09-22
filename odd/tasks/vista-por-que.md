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
- [x] T2 — Single product card: phase, current step in plain words, who does it, next concrete step,
      blockers with their owner; no raw node ids as primary text. Done in `Tablero.tsx`
      (`TarjetaProducto`, exported and reusable) and `ProductoDetalle.tsx` (new resumen card at
      top). Phase meaning from `lenguaje.faseEnUnaFrase` (reuses `FASES`); step title prefers the
      matching node's `titulo`, falls back to `flujo.como`; WHO reuses `quienLoHace`; raw node id
      kept as muted/secondary text only. Per-product freshness banner reads
      `flujo.motor.rezago_dias` (untyped `dict` field already in the `Flujo` contract, cast
      locally as `MotorInfo`) — shown when >2 days, same threshold/wording as the existing global
      banner. Tests: `tablero.test.tsx` (+2), new `producto-detalle.test.tsx` (3 tests). Verified:
      `pnpm test` 50/50, `pnpm build` OK. Commit: `da8cbe8`. Route: inline (2 screens + 1 shared
      helper file, already-understood UI wiring; delegating would not have reduced context here).
- [x] T3 — Narrated orders. Done in `Ordenes.tsx` + a new read-only contract field:
      (a) narrated sentence "Cada venta te está costando entre Q{ic0} y Q{ic2}; tu techo es
      Q{be}. {veredicto}" — pure string templating, `{veredicto}` chosen from `orden.estado` via
      `lenguaje.veredictoDeOrden` (a lookup, never a numeric comparison); shown only when the order
      already carries both `ic` (3-tuple) and `break_even_q`.
      (b) progress bar — **not built**, reported as a contract gap below; the existing "faltan ~N
      ventas" text is kept.
      (c) "Cómo mide el motor" panel with the three clocks, sourced from a NEW backend field:
      `contratos.parametros_decision()` (plain `_PARAMETROS_DECISION.csv` read-through, zero
      computation) wired into `OrdenesRespuesta.parametros_motor` (`api_ordenes.py`); OpenAPI
      schema regenerated (`pnpm tipos` against a locally-started backend, then stopped).
      (d) one-liners per estado reusing `glosario.ts` (`GLOSARIO.renovar/pausar/escalar/seguir_midiendo`),
      and the ESCALAR+`bloqueo_fase` headline ambiguity fixed via `lenguaje.tituloDeOrden`
      ("No subir presupuesto todavía…" leads; the motor's original phrase is kept as muted
      context) — matches invariante 13.
      Tests: backend `test_api_ordenes_trae_los_relojes_del_motor` (new); frontend `ordenes.test.tsx`
      (+4, one rewritten for the new headline). Verified: backend 9/9 (`test_sin_aritmetica` +
      `test_ordenes_api`), frontend `pnpm test` 50/50, `pnpm build` OK. Route: inline (one screen +
      one small backend read-through, already-understood; delegating would not have reduced
      context here).
- [x] T4 — Verified in browser (2026-09-22) against real SISTEMA data (backend with
      `VITALCOM_BASE=../SISTEMA`, frontend `pnpm dev`). Engine data runs to 2026-09-20 (rezago 2 d,
      so no per-product rezago banner, correct at threshold >2). TINNIDROP, NUSAVA, CLEARSTEM cards
      match `flujo.py --todo` (F2, F2.etapa-11 / F2.conceptos, executor). Orders: clocks 14/3/3 d
      match `_PARAMETROS_DECISION.csv`; IC/BE sentence matches `_DECISIONES.json`; ESCALAR+bloqueo_fase
      headline shows "No subir presupuesto todavía"; approve buttons disabled. Screenshots delivered
      to the operator (scratchpad t4-*.png). Route: inline.

## Acceptance criteria
- Full backend and frontend suites finish green; test_sin_aritmetica green.
- For TINNIDROP and NUSAVA the card and orders show 21-sep data and match `flujo.py --todo`.

## Progress / evidence
- 2026-09-21: feat/app-web fast-forwarded into production branch by operator (1950e19). Engine tests
  green in SISTEMA: test_flujo 29/29, test_decidir 17/17, flujo.py --validar OK.

## Contract gaps found (T3b)
- No field pairs "current sales" with "sales needed" for a progress bar. `gen_ordenes.py`'s
  `por_que` only exposes the gap (`faltan_ventas`), not the count already achieved nor the total
  target. Deriving the total as `ventas_actual + faltan_ventas` would be arithmetic on business
  concepts that only the engine may compute (`test_sin_aritmetica.py` would correctly flag it if
  done in the backend; doing it in the frontend would just move the same violation client-side).
  `PRODUCTOS/_PARAMETROS_DECISION.csv` has `min_ventas_ganador`/`min_ventas_escalar`, but which one
  applies to a given SEGUIR_MIDIENDO order is a business rule inside `decidir.py`, not something
  the app should infer. If a progress bar is wanted, `gen_ordenes.py` (or `decidir.py`'s celda)
  needs to emit both numbers itself (e.g. `ventas_actual` + `ventas_necesarias`), owned by the
  engine like everything else.

## Audit of c1bd955 / da8cbe8 / 5d377ef + T4 findings (open, not yet authorized)
- A1 (bug, confirmed in browser): `Tablero.tsx` Info termino falls back to `fase_3` for any
  non-F1/F2 phase; VARICOSE (PAUSADO) explains "FASE 3 · se compra volumen".
- A2 (UX contradiction, confirmed): ESCALAR+bloqueo_fase card says "No subir presupuesto" in the
  headline but the chip "Escalar (+20%)", the narrated verdict and the glossary line all say scale.
- A3 (gap, confirmed): `/api/productos/{k}` returns flujo.py `avisos` (e.g. TINNIDROP: Meta already
  spent $32.61; published structure not doctrinal; F3 artefacts without gate) but ProductoDetalle
  and the card never render them.
- A4 (wording): RENOVAR verdict "El ángulo sigue rentable" reads false next to IC [50.6, 250.1] vs
  BE 105.89 (Médicos Fallaron); the engine means "profitable history".
- A5 (wrong ref): ProductoDetalle rezago banner cites "invariante 11"; rezago is invariant 13
  (copied from pre-existing Ordenes.tsx).
- A6 (stale comment/claim): TarjetaProducto doc says ProductoDetalle reuses it; it does not
  (logic and `MotorInfo` type duplicated).
- A7 (comment overclaims): on Windows pytest-timeout uses the thread method, which aborts the whole
  run on timeout rather than failing just that test.
- Pre-existing, out of scope: SEGUIR_MIDIENDO with `faltan_ventas` null renders "Volumen suficiente".

## Next step
Operator decides whether to fix A1–A6 (T5). Feature otherwise complete.
