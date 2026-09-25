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
- Revised 25-sep at T2 start: writers write to `raw` (verbatim rows), and `core` is rebuilt from
  `raw` by `db/nucleo.construir_core()` in the same transaction, as today. Writing `core`
  directly would duplicate the FK resolution and `venta_uid` enrichment that only exists in
  `nucleo.py`/`cargar.py`. `raw` rows for the DB-truth tables become the truth; the CSV mirror is
  exported from them.
- Writes are key-based (same merge semantics as `upsert_fact.upsert()`, shared, not copied); the
  raw table is rewritten in one transaction to keep row order, which the byte-identical mirror
  requires (~7.7k rows, cheap).
- Operator authorized on 25-sep ("solucioná esos errores… vos decidís") fixing defects found
  along the way; orchestrator decides technical questions without asking.
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
- [x] T2 — Incremental upsert into `core` + CSV mirror regeneration. Checks: idempotent run,
  mirror byte-identical.
  Result: `db/escribir.py` (new) — `upsert()`/`anexar()`/`reemplazar()`/`reemplazar_decision()`,
  all writing `raw.*` inside one transaction with `nucleo.construir_core()`, mirror regenerated
  only after commit (atomic temp+`os.replace`). `Ads/_TOOLS/upsert_fact.py:fusionar()` extracted
  (pure merge mechanics, `upsert()` now a thin disk wrapper over it, same contract). `db/tables.py`
  adds `TABLAS_VERDAD_DB` + `raw.decisiones_json` DDL (no CSV owner for `_DECISIONES.json`).
  `db/nucleo.py:construir_core()` now reads the decision snapshot from `raw.decisiones_json`
  instead of disk. `db/cargar.py` adds `cargar_decisiones_json()` and `cargar_todo(
  incluir_verdad_db=False)` to skip reloading the 7 DB-truth tables from CSV (default `True` keeps
  prior behavior identical). `db/schema.sql` regenerated (`python db/tables.py`).
  Defects found and fixed during T2 (operator authorized fixing along the way, 25-sep):
  (a) regenerating the `_DECISIONES.json` mirror from `core.decision.payload` (`JSONB`) reorders
  top-level keys — Postgres does not guarantee JSONB key order on read back. Fixed: mirror and
  `core.decision` rebuild always read `raw.decisiones_json.contenido` (verbatim text) via
  `escribir.leer_decision_actual()`, never `core.decision.payload`.
  (b) `with conn:` (psycopg3) closes the connection on an exception instead of just rolling back,
  which would break reusing `conn` for the next write or for reading state after a failure. Fixed:
  explicit `conn.commit()`/`conn.rollback()` in `escribir._en_transaccion()`.
  Evidence (25-sep, commit `59a906e`):
  - `"../SISTEMA-app/app/backend/.venv/Scripts/python.exe" -m pytest db/test_db.py -q` → 28 passed
    (Postgres reachable; includes 8 new T2 tests: byte-identity of all 7 DB-truth files, upsert
    idempotency+position, mirror byte-identity vs `upsert_fact`, `particion` deletion, rollback +
    mirror untouched, `incluir_verdad_db=False` leaves DB-truth tables intact, `fusionar()`
    parity, plus the pre-existing 20 including the parity gate — all green, no regressions).
  - `python -m pytest Ads/_TOOLS -q` → 44 passed (same as the 25-sep baseline — `fusionar()`
    extraction is behavior-neutral for `upsert()`).
  Route: delegated writer (trigger: 2+ non-trivial files — `db/escribir.py` new, `db/tables.py`,
  `db/nucleo.py`, `db/cargar.py`, `Ads/_TOOLS/upsert_fact.py`, `db/test_db.py`, `db/schema.sql`,
  `db/README.md` all touched).
- [x] T3 — `ingerir_lucidsales.py` / `ingerir_meta.py` / `bajar_meta_insights.py` write DB then
  mirror. Check: `decidir` parity green on real data.
  CLOSED 25-sep after operator created `vitalcom_test`: `python -m pytest db/test_db.py -q` →
  35 passed; same with SISTEMA-app venv → 35 passed; real `vitalcom` raw counts after tests
  3491/1094/1041 (unchanged); 3 fact CSVs clean vs HEAD.
  Was PARTIAL (orchestrator readback 25-sep): code committed `238a75b`, real-data no-op green,
  `Ads/_TOOLS` 45 passed, but `db/test_db.py` = 18 passed / 17 SKIPPED (includes the T2
  byte-identity tests): database `vitalcom_test` does not exist and role `vitalcom` lacks
  CREATEDB. Blocked on operator running once, as Postgres superuser:
  `CREATE DATABASE vitalcom_test OWNER vitalcom;`. Re-run db tests, then check T3.
  Incident during T3 (writer report, verified by orchestrator): early test runs wrote fixture rows
  into real `vitalcom` raw and overwrote the 3 fact CSVs; CSVs restored from HEAD (they had no
  uncommitted changes), raw re-bootstrapped from them. Readback: 3 fact CSVs have no diff vs
  HEAD, row counts 3491/1094/1041 match the bootstrap; `_EVENTOS.csv` untouched (mtime 24-sep).
  Result: los tres llamadores conectan a `db/escribir.upsert()` (nunca CSV directo). Defecto
  encontrado y corregido en el camino: `ingerir_meta.py` nivel CONJUNTO (`_FACT_ENTREGA.csv`) era
  un `append` crudo, nunca pasaba por `upsert_fact` — ahora entra por la misma llave natural que
  ya usaba para el anti-duplicado. `db/tables.py` agrega `TABLAS_MIGRADAS_DB` (subconjunto de
  `TABLAS_VERDAD_DB` ya conectado — hoy `venta`/`entrega_conjunto_dia`/`entrega_anuncio_dia`);
  `cargar_todo()` ya nunca las recarga desde CSV, con o sin `incluir_verdad_db`.
  `db/escribir.verificar_csv_sincronizado()` (guardia de drift, crítico): aborta si el CSV no es
  byte-idéntico a lo que la base exportaría, o si la tabla/tenant nunca se importó (medido por
  `raw.raw_import`, no por conteo — un tenant nuevo legítimo puede empezar en cero). Recuperación:
  `db/cargar.py --tomar-csv <archivo>` (nuevo, `tables.TABLAS_MIGRADAS_DB` únicamente).
  `db/escribir.upsert()/anexar()/reemplazar()` ganan `bkdir` explícito (mismo patrón/nombrado que
  `upsert_fact.upsert()`) para el backup previo del mirror.
  Aislamiento de pruebas (crítico): `db/test_db.py` y las pruebas de `Ads/_TOOLS` que tocan
  Postgres fuerzan `PGDATABASE=vitalcom_test` y rehúsan conectar a `vitalcom` real
  (`_conectar_seguro()`); `cargar.asegurar_base_de_datos()`/`aplicar_schema()` crean/pueblan
  `vitalcom_test` si hace falta.
  Defecto de entorno encontrado (no resuelto acá, requiere un rol con privilegios): el rol
  `vitalcom` no tiene `CREATEDB`, así que `vitalcom_test` no pudo crearse en este entorno — las
  pruebas que la necesitan se SALTAN limpio (nunca caen a `vitalcom`), documentado en
  `db/README.md` con el comando de una sola vez (`ALTER ROLE vitalcom CREATEDB;`) para
  destrabarlas. Segundo defecto encontrado y corregido: `db/cargar.conectar()`/
  `asegurar_base_de_datos()` no traían `connect_timeout` — un Postgres inalcanzable por puerto
  filtrado (no solo "conexión rechazada") colgaba sin límite en vez de fallar rápido; se agregó
  `connect_timeout=10`.
  Incidente durante el desarrollo (encontrado y corregido, sin daño permanente): una primera
  versión de los tres llamadores usaba la constante `PROD` (en vez de derivar el directorio de
  `FACT`/`FACT_AD`, que las pruebas sí monkeypatchean) para `prod_dir`, y `TENANT_ID` por defecto
  ("vitalcom") sin aislar las pruebas end-to-end — dos corridas de prueba escribieron filas
  ficticias en las tablas `raw` reales de `vitalcom` (`venta`/`entrega_conjunto_dia`/
  `entrega_anuncio_dia`, tenant `vitalcom`) y sobrescribieron brevemente los 3 CSV reales.
  Corregido: los tres llamadores derivan `prod_dir` de `FACT`/`FACT_AD` y exponen `TENANT_ID`
  como constante de módulo; las pruebas usan tenants únicos y `vitalcom_test`. Los 3 CSV se
  restauraron con `git checkout` (evidencia: `git status`/`git diff --stat` vacíos antes y después
  de T3) y las filas ficticias en `raw` se limpiaron como efecto secundario del bootstrap real de
  abajo (`--tomar-csv` hace TRUNCATE+reinserta desde el CSV real, que nunca las tuvo).
  Evidencia (25-sep-2026):
  - `python -m pytest Ads/_TOOLS -q` → 45 passed (44 baseline + `test_db_write_path.py`, nuevo).
  - `"../SISTEMA-app/app/backend/.venv/Scripts/python.exe" -m pytest db/test_db.py -q` → 18
    passed, 17 skipped (skips: `vitalcom_test` no se pudo crear en este entorno, CREATEDB
    faltante — nunca cae a `vitalcom`).
  - Bootstrap real: `python db/cargar.py --tomar-csv _FACT_VENTAS.csv` (3491 filas) /
    `_FACT_ENTREGA.csv` (1094) / `_FACT_ENTREGA_ANUNCIO.csv` (1041) sobre `vitalcom` real.
  - `python Ads/_TOOLS/ingerir_lucidsales.py --dir Ads/_INGESTA/LUCIDSALES` (24 archivos ya
    cargados) → `0 reemplazadas · 0 nuevas · 1061 sin cambio`. `git diff --stat` de los 3 CSV:
    vacío.
  - `Ads/_TOOLS/ingerir_meta.py`: sin archivo `Informe-*.xlsx` disponible en el repo — se saltó,
    documentado (no se llamó la API de Meta).
  - `python Ads/_TOOLS/decidir.py --json` → exit 0, sin `--escribir`.
  - Paridad `decidir.py` real vs. exportado desde `core` (mismo chequeo que el test de paridad,
    corrido a mano contra `vitalcom` real porque el test en sí corre aislado contra
    `vitalcom_test`): `IGUAL`.
  - Conteos `raw.venta`/`entrega_conjunto_dia`/`entrega_anuncio_dia` (tenant `vitalcom`) antes y
    después de correr ambas suites de pruebas: idénticos (3491/1094/1041) — las pruebas no
    tocaron `vitalcom`.
- [ ] T4 — Events, decisions, `_ESTADO_FLUJO`, product onboarding write DB. Check: parity.
- [ ] T5 — `decidir.py` and app backend read from Postgres. Checks: parity, e2e, backend tests.
- [ ] T6 — Daily cycle script + Windows Task Scheduler task. Check: first real run writes its
  parity row.
- [ ] T7 — 7-consecutive-green-days counter. Closes P3.
- [ ] T8 — Defects found during P3: (a) `_DIM_ANUNCIOS.csv` has two full-rewrite writers
  (`sembrar_anuncios.py:188`, `firma.py:174`) — verify whether one clobbers the other and fix;
  (b) Claude task `auditoria-vitalcom-diaria` stops after its first command and its SKILL.md
  still names ETAPA-8 — fixed together with T6.

## Progress
- 2026-09-25: branch created, feature document created.
- 2026-09-25: T1 done.

- 2026-09-25: T2 done.

- 2026-09-25: T3 done (closed after vitalcom_test created; 35 db tests green).

## Next step
T4 — Events, decisions, `_ESTADO_FLUJO`, product onboarding write DB (add `evento`,
`estado_flujo`, `producto` to `tables.TABLAS_MIGRADAS_DB` once their real callers connect).
Check: parity. Also revisit T8(a) (`_DIM_ANUNCIOS.csv` double writer) if not folded into T4.
