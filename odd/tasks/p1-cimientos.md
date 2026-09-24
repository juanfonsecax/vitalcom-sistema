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
- [x] T2 — Spend-verified historic ad_id map. Route: delegated (writer: new script + test + staging).
  Output: `PRODUCTOS/_MAPA_AD_ID_HIST.csv` (key: ventana_ini, cuenta_alias, conjunto, anuncio ->
  ad_id, metodo = ad_id_verificado_gasto | nombre). Check: unit test + coverage report per month.
  Done 23-sep-2026. `Ads/_TOOLS/mapear_ad_id_hist.py` + `Ads/_TOOLS/test_mapear_ad_id_hist.py`
  (19 pure-function tests, no network). Staging: `Ads/_INGESTA/META_HIST/` (raw per account/day
  JSON from the Graph API, never touches `_FACT_*.csv`). Network scope: Meta Graph API,
  2026-07-01..2026-09-05, authorized by operator. CP1 (retired account) failed all 31
  account-day pulls with `ads_read` denied — isolated per the same pattern as
  `bajar_meta_insights.main()`, zero rows lost elsewhere.
  Evidence:
  - `python -m pytest Ads/_TOOLS -q` → 41 passed (full suite, includes the 19 new checks).
  - `python evals/run_baseline.py` → exit 0 (`TOTAL=27 PASS=24 FALLO-CONOCIDO=3 FAIL=0`).
  - `git diff --stat` on `_FACT_VENTAS.csv`/`_FACT_ENTREGA.csv`/`_FACT_ENTREGA_ANUNCIO.csv` → empty.
  - Rerun with `--fetch` (cache hit, no new network) produced a byte-identical
    `_MAPA_AD_ID_HIST.csv` (same sha256).
  - Coverage per month (1394 BASE rows without a valid ad_id):
    | Mes | filas | verificado | ambiguo | gasto_no_coincide | sin_candidato | sin_gasto |
    |---|---|---|---|---|---|---|
    | 2026-07 | 783 | 414 | 67 | 257 | 37 | 8 |
    | 2026-08 | 604 | 256 | 12 | 92 | 226 | 18 |
    | 2026-09 | 7 | 0 | 0 | 0 | 3 | 4 |
    (Sep rows in this batch fall outside the authorized 07-01..09-05 network window or predate it
    with no spend; Sep overall already has near-full ad_id coverage per the problem statement.)
  - Commits: `d45dd2d` (script+tests), `03eb58d` (generated map + staging data).
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
- 2026-09-23: T2 done — commits `d45dd2d`, `03eb58d`. See T2 evidence above.

## Next step
T3 (eval fixtures) or T5 (Postgres schema+loader) — delegated writers. T4 still needs operator
permission to install Postgres locally.
