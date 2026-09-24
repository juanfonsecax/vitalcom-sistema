# P1 — Cimientos (platform plan, gate 1 of 6)

## Objective
Leave the data and the eval safety net ready for the CSV -> Postgres migration, with a parity
proof that the migration changes nothing.

## Problem / why
- `_FACT_VENTAS.csv`: only 1291 of 3338 rows carry a valid `ad_id` (Jul 0/1436, Aug 390/994,
  Sep 901/908). Historic rows join by name via `alias.py`.
- 8 of 17 etapas have no eval baseline; pruning (P2) needs them.
- Postgres is the chosen engine (local first, cloud in P5); there is no schema nor loader yet.

## Scope (authorized 2026-09-23 by operator: "dale" to the gated plan)
- Recover historic `ad_id` only where it can be VERIFIED (spend match Meta vs LucidSales).
  Unverified rows stay name-attributed. Nothing is invented.
- Freeze eval fixtures only from REAL past outputs. No synthetic fixtures.
- Postgres local schema + idempotent CSV loader + round-trip parity gate.
- Out of scope: switching writers/readers to Postgres (P3), UI (P4), cloud (P5).

## Constraints
- Meta re-pull for Jul-Aug must NOT enter `_FACT_ENTREGA*.csv`: `gasto.py` owns spend with a
  LucidSales fallback before 2026-09-06; writing old Meta rows would silently change historic
  spend and decisions. The re-pull goes to a staging file used only for the ad_id mapping.
- CSVs remain the source of truth during P1.
- Invariants 10, 11 (CLAUDE.md): real CSV writer, `producto_key` as key.

## Tasks
- [x] T1 — Known eval failures marked as pre-22-sep history. Already done before P1
  (`evals/promptfooconfig.yaml:105-127`, `expected_fail` + reason). No change needed.
- [ ] T2 — Spend-verified historic ad_id map. Route: delegated (writer: new script + test + staging).
  Output: `PRODUCTOS/_MAPA_AD_ID_HIST.csv` (key: ventana_ini, cuenta_alias, conjunto, anuncio ->
  ad_id, metodo = ad_id_verificado_gasto | nombre). Check: unit test + coverage report per month.
- [ ] T3 — Eval fixtures from real outputs for etapas without baseline that already ran
  (candidates: etapa-0, etapa-4, etapa-7, etapa-9, etapa-10). Route: delegated (writer).
  Check: `python evals/run_baseline.py` exit 0, new tests PASS.
- [ ] T4 — Install Postgres locally. BLOCKED: needs operator permission (download + system install).
- [ ] T5 — Schema (tenant_id on every table) + idempotent loader CSV -> Postgres. Route: delegated.
  Check: row counts equal per table; second run inserts 0.
- [ ] T6 — Parity gate: export Postgres -> CSV into a temp base, run `decidir.py` there,
  `_DECISIONES.json` byte-identical to the one from the real CSVs.

## Acceptance
- T2 map exists with per-month verified coverage and zero unverified ad_id claims.
- Eval baseline: more etapas covered, exit 0.
- T6 parity identical.

## Config
- TDD: off (default, same as prior ODD docs). Tests ship with every change.
- RDD: off (`gentle-ai review mode status`: default). Delivery: work-unit commits on
  `feat/p1-cimientos`; operator merges.
- Forecast: ~900 authored lines across T2/T3/T5/T6.

## Progress
- 2026-09-23: data commit `25b67ea` (LucidSales + Meta 20-22 sep) on base branch; branch
  `feat/p1-cimientos` created. T1 found already done.

## Next step
T2 (delegated writer). Ask operator for T4 permission.
