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

