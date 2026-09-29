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
- [x] D4 Manual CO ingest: data-driven product map in ingerir_meta; EXTERNA spend path; sales
      currency labelled. (writer)
- [x] D5 Costing per market: _DIM_COSTEO/_TASA_ENTREGA keyed by market; costear.py --mercado;
      CO rows from operator's Dropi CO export (pending data). (writer + operator data)
- [x] D6 Doctrine: CLAUDE.md TONALIDAD BASE and stage agents read the product market (tone,
      registry MSPAS/INVIMA, costing). (writer)
- [x] D7 Integration: live-data copy, flujo/decidir parity old vs new, nightly pre/postcheck, Postgres
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

### D4 (2026-09-28, worktree only, nothing committed; no real-data file touched)
- `ingerir_meta.py`: product map now data-driven (`cargar_productos_meta`: producto_key, `clave_campana` parts,
  first word of nombre_display/slug, accent-free; `ALIAS_NOMBRE` keeps only the historical VARICES -> VARICOSE).
  `--producto PK` assigns the whole export (EXTERNA single-product account). Spend currency: export `Divisa`
  column, else `_DIM_PRODUCTOS.moneda`, else the file is rejected (no silent USD); non-USD needs a rate in
  `TASAS_A_USD` (COP 3152.5). EXTERNA rows get `cuenta_alias=EXTERNA`. GT parity: 213 real (campana, conjunto)
  pairs from the FACT CSVs classify identically old vs new (0 differences).
- `ingerir_lucidsales.py`: `--producto PK` / `--mercado M`; EXTERNA products are excluded from the default
  classification (manual only); EXTERNA rows: alias EXTERNA, spend converted from the product currency,
  `moneda_origen` = that currency. No schema change: `total_q` = sale amount in the product's market currency
  (owner `mercado.py`, documented there and in the tool docstring); `venta` table untouched.
- Nightly: `bajar_meta_insights.procesar_cuenta` drops EXTERNA products (counts them as ajenos); accounts come
  from `_DIM_CUENTAS` (no EXTERNA). `bajar_lucidsales` is the single GT store.
- Manifest/app: skipped. No GT action ingests a file (`ciclo.bajar_meta` and the LucidSales button run the API,
  no upload); CO exports are ingested by Claude in the session.
- Skills: "Mercado CO (manual)" in `recopilar-lucidsales`; pointer in `ciclo-diario`.
- Tests: `test_multimercado_d4.py` (12). `pytest Ads/_TOOLS` 53 passed; `hook_csv.py --barrido` exit 0.

### D6 (2026-09-28, worktree only, nothing committed)
- Doctrine follows the product market; values stay in `_DIM_MERCADOS.csv` (persona, registro, transportadoras,
  cobertura, dias_entrega, unidad_geo/unidad_local, moneda) and are pointed to, never copied. `mercado.py` gained
  `--producto PK` (read-only profile; positional form kept) + test in `test_mercado.py`.
- CLAUDE.md: title/intro GT+CO, MAPA row for markets, costeo row (GT table today), TONALIDAD BASE by market with the
  CO manual-mode line, new-product prompt. Agents: ETAPA-1/1B/2/4/5/6/7/11/GUARDAR-PRODUCTO/PRODUCTO/RENDER. Defaults:
  `[REG_INVIMA]` PENDING from operator (no number invented), `[REG_MSPAS]`/`[REG_FDA]` scoped to GT. Infographics,
  generar-imagenes-chatgpt, generar-conceptos, fase-1-angulos, MCP_PLAYBOOK, DATA_PLAYBOOK, CONTABILIDAD §3-bis
  (GT accounting stays Dropi GT; CO accounting pending), ESCALADO 00/03/10, PLANTILLAS_ADS_SECCIONES 04/05/08.
- `test_split_doctrina` ESCALADO/PLANTILLAS hashes re-frozen on purpose. GT-specific evidence, GT price rule
  (labelled as measured in GT), `GUIA_MADRE_PARAMETRIZADA` and evals asserts (GT fixtures) left intact.
- Follow-up (code, not doctrine): `Ads/_TOOLS/armar_prompts_fase2.py` (~:379, `PRECIOS_GT`) hard-codes MSPAS/FDA and
  "Somos de Guatemala: nunca INVIMA"; it must read the market profile before a CO product renders phase-2 prompts.

### D6 follow-up: armar_prompts_fase2 by market (2026-09-28, worktree only, nothing committed)
- `mercado.py` gained `registro_de_perfil` (reads the real numbers from `DOCTRINA/PLANTILLAS_DEFAULTS_OPERADOR.md`:
  `[REG_MSPAS]`+`[REG_FDA]` for GT, `[REG_INVIMA]` for CO; a non-backticked value such as PENDIENTE = missing ->
  `RegistroFaltante`), `formatear_monto` (GTQ `Q179`, COP `$ 41.000`) and `regulador_de`.
- `armar_prompts_fase2.py`: country, persona (voseo OMITILO/REPLICALO vs tuteo OMÍTELO/RÉPLICALO), registry line,
  "nunca <reguladores de otros mercados>", price ladder and CPA symbol come from the market profile. New blockers
  with typed `dato`: `mercado` (no default GT) and `registro_sanitario` (CO without INVIMA: asks the operator for the
  number; never invented, never MSPAS). Nothing is written when it blocks.
- `datos_producto.py`: new item `registro_sanitario` (only when the product has a valid market); no writer action, the
  operator hands the number to Claude, who records it in the doctrine row. `contratos.DATOS_QUE_FRENAN_PROMPTS` lists it,
  so the Fase 2 button shows the plain message (the frontend renders items generically).
- GT byte-identical: CLEARSTEM and TINNIDROP prompt txt+json generated before/after into a temp base (copy of PRODUCTOS,
  fake packshots) and `diff -r` empty; real `Ads/MEDIA_*` untouched.
- Tests: 4 new in `test_armar_prompts_fase2.py` (GT unchanged, CO tuteo/INVIMA/COP, CO sin INVIMA dato=registro_sanitario,
  sin mercado), 2 in `test_mercado.py`, 2 in `test_datos_producto.py`. Existing fixtures now declare `mercado`.
- Not done: `revisar_costo`/`revisar_precio` in `datos_producto.py` still say Q/quetzales (a CO product would read wrong).

### D7 (2026-09-29, live folder, merged)
- Live fix a14415a cherry-picked onto the branch (101845b); conflict in `ingerir_lucidsales.py` `main()` resolved
  keeping both (`forzar, mercado_flag` from D4 and `de_carpeta` from the fix). `pytest Ads/_TOOLS` 53 passed;
  `test_ingerir_lucidsales.py` and `test_multimercado_d4.py` direct runners 0 failures (they use `vitalcom_test`).
- Baseline on the live folder before merge (after the 08:19 catch-up nightly run, exit 0): `decidir.py --json`
  Postgres == csv, `flujo.py --todo` captured.
- Backup: `_RESPALDOS/pg/vitalcom_pre_multimercado_20260929_083144.dump` (pg_dump -Fc, 1.0 MB, 61 TABLE DATA
  entries in `pg_restore --list`). pg_dump needs the credentials from `db/cargar.cargar_env()`; without them it waits
  for a password prompt.
- Merge 9190b8a into `feat/dashboard-visual` (same conflict, branch version taken; tracked code == branch).
- Migration: `psql -f db/schema.sql` exit 0 (`raw.producto`, `core.producto`, `raw.fact_semanal` have
  `mercado`/`moneda`); `db/cargar.py --tomar-csv _DIM_PRODUCTOS.csv` OK; drift guard OK on every table in
  `TABLAS_MIGRADAS_DB`; `mercado.py --avisos` no warnings; `core.producto`: 4 GT + OVULOS_PURITY CO.
- Parity: `decidir.py --json` (Postgres) byte-identical to the pre-merge baseline; `flujo.py --todo` identical;
  `ciclo_diario.postcheck_real()` -> (True, IGUAL). Postgres vs csv JSON differ only in the key order of the
  `fuente_gasto` counts (values equal; the postcheck compares parsed JSON).

### D5 (2026-09-29, minimal by operator request)
- New `PRODUCTOS/_DIM_COSTEO_CO.csv`: same columns as `_DIM_COSTEO.csv`, 19 rows (cost COP 5,000-50,000), values
  from the operator's CO costing sheet (dispatch 90%, returns 20%, ads 20%, expected margin 15%, freight 22,000,
  admin 2,000 incl. AI cost, return 7,200 net of outbound freight). `cpa_base_usd` = cpa_base / 3152.5
  (`tasa_cop_usd`). Ladder 129,900/169,900 set by the operator on the COP 7,500 row (OVULOS_PURITY, cost 7,000);
  other rows `origen_escalera=PENDIENTE`.
- Cross-check against 388 real Dropi CO orders (another product, 15-may..1-jul): delivery 79% of dispatched,
  freight 22,349 avg, return charge 37,677 avg; independent unit economics give BE CPA 28,106 vs table 28,031.
- `costear.py --mercado CO` reads that table (`TABLAS_POR_MERCADO`), prints the market symbol, skips the GT
  start-up rule. GT default untouched: output byte-identical (text and --json) for costs 57 and 100.
- Not changed on purpose: `_DIM_COSTEO.csv`, Postgres `raw.costeo`, the app (`MERCADOS_CON_COSTEO = ["GT"]` in
  NuevoProducto), gen_dashboard.
- INVIMA: operator decision — no system change. OVULOS_PURITY is the only product without INVIMA; when its
  phase-2 prompts are made, the registry line is edited by hand for that product only.
- Verification: `test_costear.py` 0 failures (new case), `test_dueno_cpa_be_q.py` 0 failures,
  `pytest Ads/_TOOLS` 53 passed, `hook_csv.py --barrido` exit 0.

## Next step
Recalculate the CO table assumptions with OVULOS_PURITY's own first ~50 orders.
