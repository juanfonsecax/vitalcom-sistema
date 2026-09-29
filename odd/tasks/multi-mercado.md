# Feature: multi-mercado (Block D)

Worktree `.claude/worktrees/multi-mercado` · branch `feat/multi-mercado` (from feat/dashboard-visual b0902b1).
The live folder keeps running the nightly GT cycle until merge.

## Objective
One system, many markets. Every product carries a market tag (GT, CO); currency, symbol, exchange
rate, costing table, tone and sanitary registry derive from `PRODUCTOS/_DIM_MERCADOS.csv`.
Money never mixes across markets. GT stays automated (nightly); CO runs in manual mode (operator
provides Meta Ads Manager + LucidSales exports; account EXTERNA, no MCP).

## Evidence (mapping 2026-09-28)
- No `mercado` column in `_DIM_PRODUCTOS.csv`; `moneda` inconsistent (GT rows "USD" = ad account
  currency, OVULOS "COP"); `tasa` per product is what the engine really uses.
- Per-product tasa already correct: decidir.py (:364, :992), atribuir, firma, flujo (:700),
  gen_lanzador, perfilar_angulos, backtest_politica. Silent fallback 7.62 in decidir.py:197 and others.
- Global GT rate / cross-product sums: gen_dashboard.py (:44, ~40 uses, BE default 60.5),
  gen_finanzas.py (:50, :170, :316), gen_pl.py (:73, :400, Dropi-GT only), gen_testeos.py (:41),
  warehouse marts (total_q next to spend_usd).
- Only market-aware today: `_DIM_FLUJO_BOT.csv` mercado + gen_flujo_bot.py; ETAPA-5.
- Ingest: ingerir_meta.py PROD_KEY hard-coded (:90-93); EXTERNA has no cuenta_id;
  bajar_lucidsales single store; `_FACT_VENTAS.total_q` copied as-is (local currency, unlabeled).
- Costing GT-only: costear.py/_DIM_COSTEO.csv, _TASA_ENTREGA.csv (GLOBAL fallback = GT).
- Frontend hard-coded "Q": Hoy.tsx:320/331, Ordenes.tsx:347/353, angulosFase2.tsx:41/52-53,
  TablaGuatemala.tsx, Resultados.tsx:68-70 (GTQ).
- Postgres: raw.producto (in TABLAS_MIGRADAS_DB → drift guard) has moneda/tasa, no mercado.
- OVULOS_PURITY has no sales/delivery rows today → no pollution yet.

## Tasks
- [x] D1 Market tag: `mercado` column in _DIM_PRODUCTOS (GT×4, CO OVULOS) + Postgres raw.producto /
      stg_productos; shared resolver (mercado → moneda, simbolo, tasa, persona, registro); missing
      market fails loudly; API exposes market + currency per product. (delegated writer)
- [x] D2 App: flag per product, market selector, currency formatting from API everywhere. (writer)
- [x] D3 Per-market rollups: gen_dashboard, gen_finanzas, gen_testeos, gen_pl, warehouse; remove
      silent 7.62 fallbacks (fail loud). Nightly-risk → parity check. (writer)
- [ ] D4 Manual CO ingest: data-driven product map in ingerir_meta; EXTERNA spend path; sales
      currency labelled. (writer)
- [ ] D5 Costing per market: _DIM_COSTEO/_TASA_ENTREGA keyed by market; costear.py --mercado;
      CO rows from operator's Dropi CO export (pending data). (writer + operator data)
- [ ] D6 Doctrine: CLAUDE.md TONALIDAD BASE and stage agents read the product market (tone,
      registry MSPAS/INVIMA, costing). (writer)
- [ ] D7 Integration: live-data copy, flujo/decidir parity old vs new, nightly pre/postcheck, Postgres
      migration plan for raw.producto, merge with operator go-ahead. (parent)

## Constraints
One owner per datum; CSVs via csv writer; frontend never computes business numbers; doctrine states
the current rule; Conventional commits in English without Co-Authored-By; never commit live data
churn; work only inside this worktree; RDD off; TDD not configured.

## Progress / evidence

### D1 (2026-09-28, worktree only, nothing committed; live Postgres untouched)
- `mercado` appended as the LAST column of `_DIM_PRODUCTOS.csv` (csv writer; round-trip of the old
  file was byte-identical first): GT x4 (TINNIDROP, NUSAVA, CLEARSTEM, VARICOSE), CO OVULOS_PURITY.
- `Ads/_TOOLS/mercado.py` (new, owner of the resolution): `mercado_de`, `perfil_mercado`,
  `perfil_de_producto`/`perfil_de_fila`, `avisos_tasa` (read-only, +-20% vs the market reference).
  Blank/unknown mercado or missing product raises `MercadoError` (no GT default). Profile =
  {mercado, pais, moneda, simbolo, persona, registro_sanitario, tasa_moneda_por_usd}; the rate is the
  market reference from `_PARAMETROS_FINANZAS` (`tasa_usd_gtq`, `tasa_cop_usd`, found by the name
  convention `tasa_usd_<moneda>` / `tasa_<moneda>_usd`). Per-product `tasa` stays what the engines
  read (D3 removes the silent fallbacks).
- `moneda` in `_DIM_PRODUCTOS` = AD-ACCOUNT currency (GT rows USD, OVULOS COP); the selling currency
  comes from the mercado. Not changed (rows are correct under that meaning); documented in
  `mercado.py` and in the `--moneda` help of `alta_producto.py`.
- Writers: `alta_producto.py` requires `--mercado` (argparse) and `planear()` rejects blank/unknown
  (the app path goes through it). Manifest `producto.alta` has the new required param `mercado`
  (new param type `mercado`, validated against `_DIM_MERCADOS.csv` in `acciones.py`; added to
  `PARAM_TIPOS_ACCION` in `gen_app.py`). `POST /api/productos` requires the `mercado` form field.
- Postgres mirror (files only): `db/tables.py` is header-driven, so no code change; regenerated
  `db/schema.sql` with `python db/tables.py` (`raw.producto.mercado`) and added `core.producto.mercado`
  (`db/nucleo.py`: `ALTER ... ADD COLUMN IF NOT EXISTS`, filled in `construir_core`). dbt:
  `stg_productos.mercado` + `not_null` test (dbt not installed here, not run). The test database
  `vitalcom_test` was migrated with `cargar.aplicar_schema(dbname="vitalcom_test")`.
- API: `Producto` (list) and `Flujo` (detail) carry `mercado`, `moneda_local`, `simbolo`; new
  `GET /api/mercados`. Missing mercado => 503 naming the product (no default). Frontend: types
  regenerated into `esquema.d.ts` from the app object (the committed `src/api/openapi.json` is a stale
  snapshot and was left alone). Only UI change: `NuevoProducto.tsx` got a required "Mercado de venta"
  select fed by `/api/mercados`, otherwise the alta screen would 422. Everything else is D2.
- Verification (all in the worktree, `VITALCOM_FUENTE=csv` so nothing reads the live Postgres):
  `python -m pytest Ads/_TOOLS -q` 51 passed (baseline 50 + `test_mercado`; three fixtures updated for
  the new column) · `test_mercado.py` and `test_alta_producto.py` direct runners green ·
  `hook_csv.py --barrido` exit 0 · `flujo.py --validar` OK · `flujo.py --todo` byte-identical to a
  detached b0902b1 worktree · `decidir.py` byte-identical to that detached worktree ·
  `gen_app.py --validar-manifiesto` valid · app/backend `uv run pytest -q` 223 passed (5m41s) ·
  app/frontend `pnpm test` 141 passed, `pnpm build` OK.

### Merge-time Postgres migration (run by the parent at D7, with the operator's go-ahead)
The merged code reads `raw.producto` by the CSV header, so the DB must be migrated BEFORE the first
nightly/app run on the merged code. In this order, on the live folder after the merge:
1. Stop anything that writes (nightly cycle, app) and back up: `pg_dump` of database `vitalcom`.
2. Schema: `"C:\Program Files\PostgreSQL8in\psql.exe" -f db/schema.sql` (idempotent; adds
   `raw.producto.mercado` and `core.producto.mercado`). Equivalent minimal SQL:
   `ALTER TABLE raw.producto ADD COLUMN IF NOT EXISTS mercado TEXT;`
   `ALTER TABLE core.producto ADD COLUMN IF NOT EXISTS mercado TEXT;`
   `ALTER TABLE raw.fact_semanal ADD COLUMN IF NOT EXISTS mercado TEXT;`
   `ALTER TABLE raw.fact_semanal ADD COLUMN IF NOT EXISTS moneda TEXT;` (D3: `_FACT_SEMANAL.csv` gained
   both columns; it is loaded as a full snapshot, so the columns must exist before the next load)
3. Load the truth: the merged `PRODUCTOS/_DIM_PRODUCTOS.csv` already has the values, but `raw.producto`
   has them blank, so the mirror is no longer byte-identical: run
   `python db/cargar.py --tomar-csv _DIM_PRODUCTOS.csv` (re-imports the CSV as truth into `raw` and
   rebuilds `core` in one transaction; logs in `raw.raw_import`).
4. Verify the drift guard and parity: `python -c "import sys; sys.path.insert(0,'db'); import cargar, escribir; c=cargar.conectar(); escribir.verificar_csv_sincronizado(c,'producto','PRODUCTOS'); print('sin drift')"`
   (raises `DriftDetectado` otherwise), then `python Ads/_TOOLS/mercado.py --avisos` (no warnings),
   `SELECT producto_key, mercado FROM core.producto ORDER BY 1;` (5 rows, none blank) and the nightly
   parity check `python Ads/_TOOLS/ciclo_diario.py` pre/postcheck (`decidir.py --json` Postgres vs
   `VITALCOM_FUENTE=csv` must be identical).
5. Rollback if needed: restore the dump; the column is additive, so old code keeps working against
   the migrated DB but the CSV header would then differ from `raw.producto` (drift), so roll back the
   CSV too.

### D2 (2026-09-28, worktree only, nothing committed)
- Formatter `app/frontend/src/dinero.ts` (`formatearDinero`: GTQ `Q1,234.50`, COP `$ 41.000` es-CO no decimals;
  unknown currency is never guessed), flags, `filtrarPorMercado`, `contarPorMercado`; UI pieces in
  `componentes/mercado.tsx` (`BanderaMercado`, `SelectorMercado`, `usarMercadoSeleccionado`, localStorage in
  try/catch, key `vitalcom-mercado-v1`, default Todos). All hard-coded "Q"/GTQ replaced (Hoy, Ordenes, angulosFase2,
  TablaGuatemala, Resultados, NuevoProducto, arranque cost fix); `TablaGuatemala` keeps script text byte-for-byte via
  `conSimbolo`.
- Backend (minimal): `OrdenItem`, `Ganador`, `Fase2Detalle` carry `mercado`/`moneda_local`/`simbolo` from
  `contratos.perfil_de_producto` (D1 resolver); the frontend never derives the market from the key.
- Flags next to every product name: Portafolio (table + mobile), Hoy order/medición/next-step rows, Ordenes, ficha header,
  Fase 2. Selector at top of Hoy, Portafolio and Resultados. Hoy counts are per selected market; with Todos a
  per-market count strip is shown (no money is summed in the frontend, so no combined total exists).
- Resultados: labelled Guatemala (flag, GTQ, declared `PERFIL_DEL_PL`); with Colombia selected it shows "Resultados
  de Colombia: pendiente" and no figures/upload (gen_pl.py untouched, D3).
- NuevoProducto: flags in the market select, cost label/symbol from the market; the costing table is requested only for
  markets in `MERCADOS_CON_COSTEO = ["GT"]` (costear.py is GT-only until D5); other markets get an honest note.
- Tests: new `dinero.test.ts`; new cases in hoy/productos/resultados/arranque tests; GT decimals now `Q98.20` (was `Q98.2`)
  in ordenes/fase2 tests; fixtures got the market fields. Backend: 2 new tests in `test_mercado_en_la_api.py`.
- Verification (`VITALCOM_FUENTE=csv`): app/backend `uv run pytest -q` 225 passed (5m36s) · app/frontend `pnpm test`
  165 passed, `pnpm build` OK · `pnpm exec playwright test` 16 passed (e2e backend base = the worktree root, resolved
  `../..` from app/frontend; e2e `nuevo_producto` now selects market GT, `hoy` asserts selector + flag) ·
  `python -m pytest Ads/_TOOLS -q -p no:cacheprovider` 51 passed. `esquema.d.ts` regenerated from the app object.

### D3 (2026-09-28, worktree only, nothing committed)
- Owner of the rule: `mercado.tasa_de_fila` / `TasaFaltante` (per-product `_DIM_PRODUCTOS.tasa`; blank, 0 or text
  raises naming the product). No 7.62/60.5/30.8 GT defaults are left in the money paths.
- Missing `tasa` policy per tool. RAISE (exit 1, `BLOQUEANTE: ... <producto>`): atribuir, firma (--ficha/--generar),
  gen_finanzas, gen_pl, `decidir.ic_cpa` (ValueError). SKIP with a stderr warning: decidir (product listed in
  `omitidos`, key only present when non-empty), perfilar_angulos, backtest_politica, firma --banner (that piece),
  gen_lanzador (no days-to-PD / accumulated CPA for that product), flujo (historical-winner branch skipped, says why),
  gen_testeos (test drawn without CPA, "sin tasa").
- Market grouping: gen_finanzas writes one TOTAL per market (`_FACT_SEMANAL.csv` new columns `mercado`,`moneda`;
  `db/schema.sql` regenerated for `raw.fact_semanal`; the committed CSV got the two columns, GT/GTQ on every row, values
  untouched) and the txt report sections per market; its Dropi+Relay cash check is explicitly GT. gen_pl is explicitly
  GT (`MERCADO_PL`, sales filtered to GT products, header + json `mercado`/`moneda`; no CO accounting). gen_dashboard is
  a single-market board (`MERCADO_DASH="GT"`): other-market products are excluded with a stderr warning and a footer
  note (their money is never added), per-product tasa everywhere, `be_de/base_de` raise instead of 60.5/30.8;
  `PISO_GASTO_Q=60.5` stays as a named GT-board threshold (rules I/J, in Q, not a product default); account-level
  `_FACT_PAUTA_REAL` USD uses the GT market reference rate and drops accounts of other-market products.
  atribuir refuses a cut that mixes markets (use --producto). verificar_monedas filters to GT, rates from mercado.py.
  gen_testeos takes tasa and symbol from each test's product.
- warehouse (dbt not installed, NOT executed): `mercado` carried via `stg_productos` join in `fct_gasto_dia`,
  `fct_conjunto_dia` (+ group by, not_null test) and `fct_anuncio_dia`. The marts are already product-grain (none summed
  across products), so no rollup changed; the column makes any later rollup group by market.
- Known non-determinism (pre-existing): `perfilar_angulos` `prioridad_ts` is Thompson sampling, differs run to run.
- Verification: see the D3 report; GT outputs byte-identical vs a detached 78a6d42 worktree for decidir (text and
  --json), flujo --todo/--validar, gen_lanzador (json+html), gen_testeos, _REPORTE_SEMANAL.txt; gen_dashboard identical
  except the footer market line; _FACT_SEMANAL.csv identical plus the two columns; _ESTADO_ANGULOS.csv identical except
  `prioridad_ts`. `python -m pytest Ads/_TOOLS` 52 passed (new `test_multimercado_d3.py`, 9 cases).

## Next step
D4 (manual CO ingest).
