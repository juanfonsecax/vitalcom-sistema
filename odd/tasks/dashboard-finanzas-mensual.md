# Monthly finance dashboard by market

## Objective
One visual screen in the app where the operator picks a market (GT now, CO later) and sees, month by
month: Dropi sales delivered, product and freight cost, returns, Meta ad spend, what the bank actually
charged, fixed costs, and the real profit, plus the per-product breakdown.

## Problem
- `gen_pl.py` reads one Dropi export and one bank PDF per run; nothing is stored, so there is no
  history across months (Dropi exports are a rolling window).
- `gen_pl.py` takes ad spend from LucidSales (`_FACT_VENTAS.spend_usd`), but CLAUDE.md makes Meta the
  owner of spend (`Ads/_TOOLS/gasto.py`, `_FACT_ENTREGA.csv`). September: LucidSales $2,114.35 vs
  Meta $2,188.62.
- Fixed costs have no market: LucidBot ($44) + LucidSales ($26) are per market; Proxy-Cheap and
  Anthropic are shared.

## Scope
- Ingest and persist Dropi orders (upsert by order ID, latest status wins) and bank movements (Relay
  now; Mercury later) as fact CSVs under `PRODUCTOS/`.
- Monthly P&L per market computed by the SAME formula as `gen_pl.py` (one formula, no copy).
- Ad spend from Meta via `gasto.py`; LucidSales only as marked fallback.
- Fixed costs carry a market (`GT`, `CO`, `COMPARTIDO`); shared ones split by a parameter.
- App screen with market selector, monthly charts and table, per-product breakdown, preliminary
  flag for cohorts younger than 10 days.

Out of scope now: CO data (selector shows "sin datos"), Mercury ingestion (needs a CSV export and the
card → ad account map), cartera/caja view.

## Constraints
- DOCTRINA/CONTABILIDAD.md is the norm; `_PARAMETROS_FINANZAS.csv` holds parameters.
- CSV via real writer; no hand numbers; missing data reported as missing.
- One writer; work-unit commits; no push.

## TDD
Mode: on (session choice). Runners: `~/AppData/Local/Python/bin/python -m pytest` (Ads/_TOOLS),
`app/backend/.venv/Scripts/python -m pytest` (app/backend), `vitest run`, `tsc -b`, `vite build`.
Known environmental failures: Ads/_TOOLS conftest wrapper items fail with OSError WinError 6.

## Tasks
- [x] T1 Persist Dropi orders and bank movements (ingesters + fact CSVs + tests) — d218469
- [x] T2 Market on fixed costs + shared split parameter; ad spend from Meta in the P&L formula — c623710
- [x] T3 Monthly P&L by market (CLI `--json`) reusing gen_pl's formula — 5dd95a1
- [x] T4 App screen: market selector, monthly charts/table, per-product, preliminary flag — ad704d6

- [x] T5 Meta spend dedupe: `MetaAPI-directo` supersedes other sources for the same account-day
  (CSV + Postgres + gasto.py + dbt mirror); every GT account-month equals live Meta — 7989e11, 37d7c9a
- [x] T6 Ingest Jul-Aug Dropi orders and the Dropi wallet history; classify withdrawals by
  `CONCEPTO DE RETIRO` (own transfer vs personal draw vs unclassified) — 1631d8b
- [x] T7 Dashboard: Jul-Aug months, real return cost from the wallet, withdrawals and transfers
  shown apart from profit, Dropi wallet balance — e6a37df (+ 80af2c3 toy-system fix)

- [x] T8 Effective FX rate: Q withdrawn from Dropi ÷ USD received (pair TRANSFERENCIA_PROPIA wallet
  rows with bank deposits; operator-confirmed pair 2026-10-01 Q90,000 → $11,381 ≈ 7.908). Monthly ad
  spend converts with the weighted rate of recent transfers, else the latest known; parameter 7.62
  only when no transfer exists. Starts after T5–T7 (same files). — 256a758

## Acceptance
- Re-ingesting the same files changes nothing (idempotent).
- September GT: ad spend equals Meta ($2,188.62 incl. GTR13 from `_FACT_ENTREGA`); bank Facebook
  $2,200.68; fixed costs $213.80 split by market rule.
- The dashboard numbers equal the CLI JSON for the same month.

## Progress
- 2026-10-13: Relay parser fixed for signed amounts (3c8d81b). Statements Aug/Sep/Oct-partial of
  #8889 reconcile to their Withdrawals total; #8890 has no movements.
- 2026-10-13: T1-T4 done and verified. Real data persisted: 359 Dropi orders (Sep 1 - Oct 13, the one
  repeated cancelled order counted once) and 207 Relay movements (#8889: Aug 79, Sep 121, Oct 7;
  #8890: 0). Re-ingesting both leaves the CSVs byte-identical.
- Ad spend: gen_pl now reads Meta through `gasto.py` (LucidSales only where Meta has no coverage,
  source split reported). Sep GT: Meta $2,188.04 in `_FACT_ENTREGA.csv` (live Meta says $2,188.62; the
  CSV lags $0.58, GTR7/GTR0/GTR1 last-day pulls), neto Q8,589.28 (was Q9,150.80 on LucidSales $2,114.35).
- Bank by movement date (calendar month): Sep Facebook $2,193.06 (114 charges), Aug $1,871.89. The
  $2,200.68 / $1,894.91 figures are statement totals (the Sep statement holds Sep 2 - Oct 1, the Aug
  one holds Aug 6 - Sep 1). Fixed costs Sep $213.80 = Q1,629.16, all COMPARTIDO, 100% GT while only GT
  is active.
- Route: T1-T3 delegated-direct single writer; T4 backend and frontend by the same writer.
- Checks observed: Ads/_TOOLS unittest (gen_pl, ingerir_dropi, ingerir_banco, gen_pl_mensual) 67 OK;
  backend pytest (finanzas_mensual, resultados, acciones, sin_aritmetica, api_espeja_los_csv,
  mercado_en_la_api) 59 passed; vitest 208 passed; tsc -b and vite build clean; gen_app.py
  --validar-manifiesto valid; flujo.py --validar valid; screen checked live on the real data.
- Not done: the full backend suite (it did not finish in a reasonable time here); gen_finanzas.py and
  gen_dashboard.py still read LucidSales `spend_usd` (they are the tracked-attribution layer, not the P&L).
- 2026-10-13 (T5-T7): the CSV doubled Meta spend because older sources (Ads Manager export, MCP, 4-7
  day windows) describe the same account-day with other conjunto names or windows. Rule: for one
  account and day `MetaAPI-directo` wins (`upsert_fact.superar_por_api_directa`; a window is dropped
  only if the API covers all its days, a gap of up to 7 days without API rows counts as covered).
  Applied on write (bajar_meta_insights, ingerir_meta, Postgres upsert), on read (`gasto.py`) and in
  dbt (`entrega_con_superada` macro); `reconciliar_entrega.py --escribir` cleaned the history
  (637 + 177 rows). Second cause found while checking the P&L: LucidSales windows of 3-8 days and
  float account ids ('123.0') never matched Meta's daily rows, so their spend fell to the fallback on
  top of Meta (about USD 1,900 over Jul-Aug); a sale whose window Meta covers now keeps its sales and
  contributes zero spend. GT account-months equal live Meta (tolerance 0.02) except Oct GTR0
  (2.54 vs 2.62, one day of lag). Remaining LucidSales fallback: USD 61.53 Jul / 37.71 Aug from the
  retired COP account CP1 (no API coverage).
- decidir.py before/after: same actions (RENOVAR 3, ESCALAR 1, SEGUIR_MIDIENDO 3, PAUSAR 0), no order
  changed; accumulated spend per angle fell 8-27% and the CPA in three RENOVAR texts fell (Q57.6 to
  Q42.6, Q65.0 to Q46.9, Q113.6 to Q78.9; BE Q105.9).
- Wallet: 393 movements (2026-09-01 to 2026-10-13), balance chain continuous; Jul-Aug orders 586;
  945 orders total. Return cost is REAL where the wallet covers the month from day 1 (Sep MIXTO 50/51,
  Oct REAL 3/3) and the parameter average for Jul-Aug (flagged in each month).
- Checks observed: Ads/_TOOLS test_gasto, test_upsert_fact, test_reconciliar_entrega,
  test_bajar_meta_insights, test_ingerir_cartera, test_ingerir_dropi, test_gen_pl, test_gen_pl_mensual,
  test_decidir, test_flujo all exit 0; backend pytest (acciones, finanzas_mensual, resultados,
  sin_aritmetica, api_espeja_los_csv, mercado_en_la_api) 63 passed; vitest 214 passed; tsc -b and vite
  build clean; dbt build PASS=36; gen_app --validar-manifiesto and flujo --validar valid. db/test_db.py:
  8 failures all `voz_cliente.producto_key` missing in the local Postgres schema (not from this work).
- 2026-10-13 (T8): pairs live in `_FACT_TRANSFERENCIAS_FX.csv`; the rate is derived on read (Q / USD),
  not stored, so it cannot contradict its two amounts. `registrar_transferencia_fx.py` auto-pairs a
  TRANSFERENCIA_PROPIA wallet row with one bank ENTRADA (arrival within 5 business days, rate band
  6.5-9.5, ambiguous or doubly claimed entries listed, never paired) or takes an operator-confirmed
  pair (`--salida --usd`). Seeded: wallet movement 6450689 (2026-10-01, Q90,000) -> $11,381.00 =
  7.9079, bank MERCURY, arrival date empty (unknown). Rule (CONTABILIDAD.md): USD-weighted rate of
  transfers leaving in the 90 days (`ventana_tasa_fx_dias`) that end on the month's last day; else
  the latest earlier one; else `tasa_usd_gtq`. One formula: `gen_pl.calcular_vista_a(tasa=)` reprices
  ad spend and USD fixed costs; CLI and monthly both use it; `conversion` block per month (rate,
  rule, transfers, conversion cost = USD spend x (rate - 7.62), informational). Real result: Jul, Aug,
  Sep use the parameter 7.62 (the only transfer is after their close), Oct 7.9079 (VENTANA), Oct
  conversion cost Q89, Oct neto Q2,203 (Q2,292 at 7.62: the difference is the Q89 conversion cost; Oct fixed costs are Q0).
- Checks observed: Ads/_TOOLS unittest test_gen_pl 25, test_gen_pl_mensual 36, test_tasa_fx 21,
  test_ingerir_cartera 10 OK; test_multimercado_d3 9/9; backend pytest (finanzas_mensual, resultados,
  acciones, sin_aritmetica, mercado_en_la_api, api_espeja_los_csv) 64 passed; vitest 216 passed;
  tsc -b and vite build clean; gen_app --validar-manifiesto valid; verificar_monedas 6/6.
