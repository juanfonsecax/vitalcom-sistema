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
- [x] T3 — Eval fixtures from real outputs for etapas without baseline that already ran
  (candidates: etapa-0, etapa-4, etapa-7, etapa-9, etapa-10). Route: delegated (writer).
  Check: `python evals/run_baseline.py` exit 0, new tests PASS.
  Done 23-sep-2026. Covered 3 of 5 candidates with real, previously-unfound fixtures
  (`evals/README.md`'s own prior "9 of 17 uncovered" table was wrong about these three —
  the outputs exist, just not where the table's original search looked):
  | Etapa | Real fixture | Assert |
  |---|---|---|
  | etapa-4 | `PRODUCTOS/TINNIDROP/1_HACER_MANUAL.txt:305-349` (PARTE 4 copy, 3 new conjuntos) | `evals/asserts/etapa-4.py`: 3 TEXTO + 3 TÍTULOS + DESCRIPCIÓN per conjunto, CTA to WhatsApp, no banned words in the actual ad copy |
  | etapa-7 | `PRODUCTOS/_AUDITORIAS/_AUDITORIA_DIARIA_20260908.txt:58-96` ("Lectura cualitativa (ETAPA-7)" inside a real ciclo-diario run) | `evals/asserts/etapa-7.py`: CPA cited, never ROAS, window integrity, quantified sangrado, per-account/dimension reading |
  | etapa-9 | `PRODUCTOS/_DIM_CREATIVOS.csv`, real tanda (producto_key=TINNIDROP, fecha_alta=2026-09-06, 5 rows) | `evals/asserts/etapa-9.py`: canonico_id required, funnel-role balance (not a single role), max 2 executions per concepto_key |
  Skipped (no real output found on disk, confirmed by a fresh search this session,
  not just the prior README claim): etapa-0 (only session-consumed video ranking
  found; no persisted 3-table ETAPA-0.md output for any product) and etapa-10 (no
  persisted "LECTURA CONCEPTO ↔ MÉTRICA" brief; closest artifact is `atribuir.py`'s
  own attribution rows cited as `fuente` in `_APRENDIZAJES.csv`, which is the tool's
  output, not this etapa's).
  Honest finding, not weakened: the etapa-4 fixture's real TÍTULO
  `"¿Te dijeron que no hay cura?"` uses the word "cura", banned by
  `DOCTRINA/COPYWRITING_ADS.md` §PRINCIPIO 7 — marked `expected_fail: true` with
  the reason in `promptfooconfig.yaml`, same pattern as the pre-existing etapa-6
  cases. The assert was NOT narrowed to hide it.
  Also fixed a latent encoding bug in `Ads/_TOOLS/test_evals_baseline.py`
  (subprocess output was decoded with the Windows default codec instead of
  utf-8, matching the fix `conftest.py` already applies elsewhere) — needed
  because the new fixtures' real emoji/accents exposed it.
  Evidence:
  - `python evals/run_baseline.py` before: `TOTAL=27 PASS=24 FALLO-CONOCIDO=3 FAIL=0`.
    After: `TOTAL=30 PASS=26 FALLO-CONOCIDO(documentado)=4 FAIL=0`, exit 0.
  - Each new assert proven to fail on a deliberately broken copy of its fixture
    in a temp/in-memory scratch (never committed): etapa-4 with a TEXTO variant
    removed → fails "menos de 3 variaciones"; etapa-7 with CPA replaced by ROAS
    → fails "el informe menciona ROAS"; etapa-9 with canonico_id blanked on one
    row → fails "filas sin canonico_id".
  - `python -m pytest Ads/_TOOLS -q` → 41 passed.
  - Commits: `e2f6085` (fixtures + asserts + config + README), `f4449f7` (encoding fix).
- [x] T4 — Install Postgres locally. Done: operator installed Postgres 18.6 (Neon went GA on 18
  2026-05-01, so 18 was kept instead of downgrading to match anything older), created role/db
  `vitalcom`, and left credentials in `~/.config/vitalcom_db/.env`
  (PGHOST/PGPORT/PGDATABASE/PGUSER/PGPASSWORD). Verified: `psql --version` → 18.6; connected and
  ran `db/schema.sql` successfully (see T5).
- [x] T5 — Schema (tenant_id on every table) + idempotent loader CSV -> Postgres. Route: delegated
  (single writer, this session). Done 23-sep-2026.
  - `db/schema.sql` (generated by `db/tables.py`, idempotent `CREATE SCHEMA/TABLE IF NOT EXISTS`):
    one `core.*` table per `PRODUCTOS/*.csv` (37 tables + `raw_import` + `decision`), verbatim
    text columns + `tenant_id` (single tenant `'vitalcom'`, RLS not enabled) + `id BIGSERIAL`.
    `core.angulo` is a VIEW over `conjunto`, not a physical table (its columns already live 1:1 in
    `_DIM_CONJUNTOS.csv`; no real reader needs it separated in P1). `catalogo_concepto` intentionally
    NOT built: its source is `Ads/_SWIPE/_CATALOGO_CONCEPTOS.md` (prose, not a CSV) — out of scope
    per "CSVs remain the source of truth", documented in `db/README.md`.
  - `db/cargar.py`: idempotent via TRUNCATE + reinsert, one transaction per run. `venta` gets two
    extra columns (`ad_id_resuelto`, `metodo_atribucion`) computed from `_MAPA_AD_ID_HIST.csv`
    (T2) without ever touching the original `ad_id` column. Found and fixed during this task: the
    map's natural key (ventana_ini, cuenta_alias, conjunto, anuncio) is NOT unique — 150 groups
    repeat it — so a plain dict join silently mis-assigned 1 of 1394 rows (671/723 instead of the
    real 670/724). Fixed with a key+FIFO-queue join, which matches
    `mapear_ad_id_hist.py:construir_mapa()`'s stable sort exactly (verified against the real CSV).
  - `db/exportar.py`: reconstructs each CSV's original header/columns from the mirrored table,
    ordered by `id` (insertion order = original row order). `venta` writes back the ORIGINAL
    `ad_id` column verbatim, never the enriched one.
  - `Ads/_TOOLS/decidir.py`: added `DECIDIR_PROD_DIR` env override (minimal, backwards-compatible
    — default behavior unchanged, same pattern `flujo.py` already uses via monkeypatching, just
    reachable across a process boundary). Needed for T6 (see below).
  - `db/test_db.py`: pure tests for the CSV<->SQL mapping/enrichment functions, plus an
    integration suite skipped when Postgres isn't reachable.
  Evidence:
  - `"..\SISTEMA-app\app\backend\.venv\Scripts\python.exe" db/cargar.py` run twice: identical
    stdout both times (`diff` empty), total 7721 rows across 38 tables + 1 decision row; each
    table's count equals its CSV's row count minus header (spot-checked venta=3407, producto=5,
    aprendizajes=84, mapa_ad_id_hist=1394 against `wc -l`).
  - `venta.metodo_atribucion`: `ad_id`=1360, `ad_id_verificado_gasto`=670, `nombre`=724,
    `sin_atribuir`=653 — matches T2's coverage table (1394 BASE rows without a valid ad_id =
    670+724) and the non-BASE (CONTROL) rows getting `sin_atribuir`, zero invented ad_id values.
  - `"..\SISTEMA-app\app\backend\.venv\Scripts\python.exe" -m pytest db/test_db.py -q` → 16 passed
    (pure mapping tests + idempotent-load test + venta distribution test + T6 parity test, all
    against the real local Postgres).
  Commit: `0869332`.
- [x] T6 — Parity gate: export Postgres -> CSV into a temp base, run `decidir.py` there, compare
  to the real repo's result. Done 23-sep-2026, same commit as T5 (`0869332`) — implemented and
  verified together since the gate is what proves the loader/exporter are correct.
  - Runs `decidir.py --json` (NEVER `--escribir`, never touches the real `_DECISIONES.json`) as a
    **subprocess** against the real repo and again with `DECIDIR_PROD_DIR` pointed at the
    exported temp base, using a separate interpreter (`python` on PATH: scipy 1.18 + duckdb 1.5) —
    the venv that has `psycopg` doesn't have scipy/duckdb and installing into it was out of scope,
    so the two halves (DB access vs. the decision engine) run in different processes communicating
    only through the exported CSV files and one env var.
  - Compares the two JSON results deep-equal, ignoring only the `generado` key (today's date,
    identical in both runs regardless). Any other difference fails loud — not masked.
  - Evidence: `test_db.py::test_parity_gate_decidir_exportado_igual_a_real` — PASS, both `decidir`
    runs produced byte-identical decision payloads (aside from `generado`) across every product,
    angle, and cell in the current portfolio.

- [x] T2b — DONE 23-sep-2026 (reopening). The historic map joined ventas by key + FIFO row order
  (150 duplicate-key groups); a positional join breaks on any reorder. Added `venta_uid`: a
  sha256 of each venta row's full content (`Ads/_TOOLS/venta_identidad.py`, a dependency-free
  module so `db/cargar.py`, running in the psycopg venv without pandas, can import it without
  pulling `mapear_ad_id_hist.py`'s pandas-based chain), with an occurrence counter for the 9
  groups (22 rows) of byte-identical duplicate rows confirmed to exist in the real CSV.
  `mapear_ad_id_hist.py` emits it as a new column of `_MAPA_AD_ID_HIST.csv` (regenerated from
  cached staging, no network); `db/cargar.py:enriquecer_venta()` joins on it (plain dict, no
  FIFO queue).
  Evidence:
  - Coverage unchanged: 670 verified / 724 nombre / 1360 ad_id / 653 sin_atribuir (3407 rows).
  - Reorder test (both `Ads/_TOOLS/test_mapear_ad_id_hist.py` and `db/test_db.py`): shuffling
    `_FACT_VENTAS.csv` rows leaves every attribution unchanged.
  - `git diff --stat PRODUCTOS/` after regenerating the map: only `_MAPA_AD_ID_HIST.csv` changed
    (new `venta_uid` column), nothing else.
  - Commit: `b7c2136`.
- [x] T5b — DONE 23-sep-2026 (reopened by parent review). T5 delivered a verbatim text mirror
  (one table per CSV); parity over that mirror proved the round trip, not that the approved
  normalized model (producto -> angulo -> creativo/concepto -> conjunto/anuncio with name
  history -> typed daily facts) holds what `decidir.py` needs.
  - Renamed the T5 mirror schema `core` -> `raw` (verbatim, audit/staging layer). `db/schema.sql`
    carries a one-time `DO $mig$` migration block: on a base that still has the old `core` and no
    `raw`, it renames it and drops `venta`'s 2 T5 enrichment columns (that logic now lives only
    in the new `core`). No-op on a fresh base or one already migrated.
  - Built a typed, normalized `core` FROM `raw` (`db/nucleo.py:construir_core()`, same
    transaction as the loader, idempotent DELETE+INSERT per tenant): `tenant`, `producto`,
    `cuenta`, `angulo` (now a physical table, unique per tenant+producto+angulo_key, attributes
    from `_DIM_CONJUNTOS.csv`), `catalogo_concepto` (distinct concepto_key; its full attributes
    stay in `Ads/_SWIPE/_CATALOGO_CONCEPTOS.md`, prose, out of scope same as T5),
    `conjunto_nombre_hist` (replaces `_ALIAS_CONJUNTOS.csv`/`alias.py` semantics; `valid_to`
    stays NULL — `alias.py` resolves by dict, not date range, documented honestly), `conjunto`,
    `creativo`, `anuncio` (distinct from `entrega_anuncio_dia`, which already carries
    ad_id/angulo_key/concepto_key/canonico_id), typed `entrega_conjunto_dia`,
    `entrega_anuncio_dia`, `venta` (numeric/date types, FKs, `metodo_atribucion`, `venta_uid`
    from T2b), `evento`, `decision` (no CSV owner, lives only in core), `parametro_decision`,
    `parametro_finanzas`, `banda`, `estado_flujo` (the last 6 needed because `decidir.py` reads
    their CSVs directly). Unresolvable FKs stay NULL and are counted, never invented — e.g.
    `_DIM_CONJUNTOS.csv` and `_DIM_CUENTAS.csv` disagree on `cuenta_alias` spacing (`"GTR7"` vs
    `"GTR 7"`, join normalizes it) but 19/173 `conjunto` rows still can't resolve `cuenta_id`
    (multi-account composite aliases like `"GTR0/GTR7/GTR13/CP1"`, and `"EXTERNA"` with no
    `_DIM_CUENTAS.csv` row) — documented in `db/README.md`, not papered over.
  - Rewrote `db/exportar.py`: `exportar_raw_todo()` keeps the T5 full audit export (from `raw`);
    new `exportar_core_decidir()` reconstructs, FROM `core`, exactly the 9 CSVs `decidir.py`
    (via `gasto.py`/`alias.py`) reads directly (`_PARAMETROS_DECISION.csv`, `_DIM_PRODUCTOS.csv`,
    `_DIM_CONJUNTOS.csv`, `_DIM_BANDAS.csv`, `_ALIAS_CONJUNTOS.csv`, `_FACT_VENTAS.csv`,
    `_FACT_ENTREGA.csv`, `_FACT_ENTREGA_ANUNCIO.csv`, `_ESTADO_FLUJO.csv` — scoped to exactly
    what decidir's import chain reads, confirmed by reading `decidir.py`'s own path constants and
    its explicit `_gasto.escribir_conjunto_ventana_csv(ruta_ventas=..., ruta_entrega=...)` call,
    which bypasses `gasto.py`'s own hardcoded paths).
  - Parity gate (T6) rebuilt on `core`: `test_db.py::test_parity_gate_decidir_exportado_igual_a_real`
    now calls `exportar_core_decidir()`, never falls back to `raw`.
  Evidence:
  - `"..\SISTEMA-app\app\backend\.venv\Scripts\python.exe" db/cargar.py` run twice: identical
    `raw` counts, identical `core` table counts, identical FK-unresolved counts, identical
    raw->core conservation report both times.
  - Fact conservation: raw vs core row counts equal for `venta` (3407), `entrega_anuncio_dia`
    (955), `entrega_conjunto_dia` (1046) — every raw fact row lands exactly once in core.
    Cent-exact sums verified by direct SQL: `venta.spend_usd` 6978.9473 both sides,
    `entrega_conjunto_dia.spend_usd` 3684.37 both sides, `entrega_anuncio_dia.spend_usd`
    1473.01 both sides, `venta.ventas` 1089 both sides.
  - `core.venta.metodo_atribucion`: ad_id=1360, ad_id_verificado_gasto=670, nombre=724,
    sin_atribuir=653 — matches T2/T2b exactly.
  - Parity: `decidir.py --json` on the real repo vs. on `exportar_core_decidir()`'s output —
    identical JSON except `generado`, verified both via `db/test_db.py` (pytest, Postgres) and a
    manual subprocess run producing a byte-identical diff (0 differences).
  - `"..\SISTEMA-app\app\backend\.venv\Scripts\python.exe" -m pytest db/test_db.py -q` → 21
    passed (pure mapping/reorder tests + idempotency + reconciliation + fact conservation +
    metodo_atribucion + T6 parity + raw audit export, all against the real local Postgres).
  - `python -m pytest Ads/_TOOLS -q` → 41 passed. `python evals/run_baseline.py` → exit 0
    (`TOTAL=30 PASS=26 FALLO-CONOCIDO(documentado)=4 FAIL=0`).
  - `git diff --stat PRODUCTOS/` shows no change from T5b work (only the T2b regenerated
    `_MAPA_AD_ID_HIST.csv`, committed separately in `b7c2136`).

## Acceptance
- T2 map exists with per-month verified coverage and zero unverified ad_id claims. DONE.
- Eval baseline: more etapas covered, exit 0. DONE.
- T6 parity identical — on the NORMALIZED `core` layer, not a verbatim mirror. DONE (T5b).
- T2b: venta attribution is stable under reordering, no more positional dependency. DONE.

## Config
- TDD: off (default, same as prior ODD docs). Tests ship with every change.
- RDD: off (`gentle-ai review mode status`: default). Delivery: work-unit commits on
  `feat/p1-cimientos`; operator merges.
- Forecast: ~900 authored lines across T2/T3/T5/T6; T2b/T5b reopening added ~1250 more
  (db/nucleo.py is the bulk of it — a full typed schema + build + reconciliation).

## Progress
- 2026-09-23: data commit `25b67ea` (LucidSales + Meta 20-22 sep) on base branch; branch
  `feat/p1-cimientos` created. T1 found already done.
- 2026-09-23: T2 done — commits `d45dd2d`, `03eb58d`. See T2 evidence above.
- 2026-09-23: T3 done — commits `e2f6085`, `f4449f7`. See T3 evidence above.

## Progress (cont.)
- 2026-09-23: T4/T5/T6 done — commit `0869332` (db/schema.sql, tables.py, cargar.py, exportar.py,
  test_db.py, decidir.py DECIDIR_PROD_DIR override). See T4/T5/T6 evidence above.
- 2026-09-23: T2b done — commit `b7c2136` (venta_identidad.py, mapear_ad_id_hist.py, cargar.py,
  test_mapear_ad_id_hist.py, regenerated `_MAPA_AD_ID_HIST.csv`). See T2b evidence above.
- 2026-09-23: T5b done — db/nucleo.py (new), db/tables.py, db/cargar.py, db/exportar.py,
  db/test_db.py, db/schema.sql, db/README.md rewritten for the raw/core split. See T5b evidence
  above.

## Next step
P1-cimientos is CLOSED: all tasks (T1-T6, T2b, T5b) are done and the parity gate passes on the
normalized `core` layer, not a verbatim mirror. P2 (pruning against the eval baseline) is next,
whenever the operator starts it.
