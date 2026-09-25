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
- [x] T4 — Events, decisions, `_ESTADO_FLUJO`, product onboarding write DB. Check: parity.
  PARTIAL (25-sep-2026): only the events family is connected in this pass; decisions/estado_flujo/
  product onboarding are deferred (see "Next step" below and evidence).
  Result: `registrar_evento.anexar()` is now the single writer of `_EVENTOS.csv` (decision #1) and
  writes DB-first (`db/escribir.anexar()` on `raw.evento`, same drift guard/`TENANT_ID`/`BKDIR`
  override pattern as T3). `flujo.py:escribir_estado()`, `perfilar_angulos.py:registrar_transiciones()`
  and `reingreso_f1.py:anexar_evento()` now call it instead of writing the CSV themselves — the
  other four appenders the inventory found. `flujo.py`/`perfilar_angulos.py` use a LOCAL import
  (inside the function) to avoid a module-level circular import with `registrar_evento.py` (which
  imports `flujo` for `gate_entrada`); `reingreso_f1.py` redirects `registrar_evento`'s
  `BASE/PROD/EVENTOS` globals to its own `base_dir` for fixtures, same pattern as
  `test_registrar_evento.py`. `tables.TABLAS_MIGRADAS_DB` gains `"evento"`.
  Decision #2 (instruction audit): grepped `CLAUDE.md`, `.claude/skills/**`, `.claude/agents/**`,
  `DOCTRINA/**` for instructions telling an agent to append `_EVENTOS.csv` by hand. Redirected to
  the exact `registrar_evento.py` CLI command in 5 files: `.claude/agents/ETAPA-11.md` (PASO 7 —
  was a literal "escribir con csv real" table), `.claude/agents/ETAPA-6.md` (CAMBIO_CREATIVO note),
  `.claude/agents/ETAPA-5.md` (principle 4), `DOCTRINA/PLANTILLAS_FLUJO_BOT.md`,
  `.claude/skills/fase-2-conceptos/SKILL.md` (PASO 0 output + PASO 2 close line). Left descriptive
  (non-instructional) mentions of `_EVENTOS.csv` in `DOCTRINA/GUIA_MADRE_PARAMETRIZADA.md`,
  `DOCTRINA/ESCALADO/04_PALANCAS.md`, `DOCTRINA/CALENDARIO_ESCALADO.md`, `DOCTRINA/DATA_PLAYBOOK.md`,
  `DOCTRINA/FLUJO.json`, `.claude/skills/fase-3-escalado/SKILL.md`, `.claude/skills/publicar-meta/SKILL.md`,
  `.claude/skills/ciclo-diario/SKILL.md` unchanged — they document ownership/gates or already point
  at `registrar_evento.py`, not a hand-write instruction.
  Deferred (not done in this pass, safety-scoped — see "Next step"): decision #3 (`alta_producto.py`
  ordering/consistency for `_DIM_PRODUCTOS.csv` DB write + `_DIM_ENVASE.csv` CSV) — not started,
  because `_DIM_PRODUCTOS.csv` is not connected to DB yet; decision #4 (hooks) — not checked, no new
  hook-triggered DB writer landed in this pass (`flujo.py --escribir`'s CSV write of
  `_ESTADO_FLUJO.csv` itself is unchanged, only its embedded event-transition append moved to
  Postgres); `_DECISIONES.json` (`decidir.py --escribir`) and `_ESTADO_FLUJO.csv`/`_DIM_PRODUCTOS.csv`
  full DB connection (`editar_producto.py`, `alta_producto.py`) are not implemented.
  Why deferred: connecting those three writer families safely requires updating ~8 more existing
  test files (`test_decidir.py`, `test_flujo.py`'s own suite if it starts exercising
  `escribir_estado()`, `test_alta_producto.py`, `test_cambiar_costo.py`, `test_cargar_cuenta.py`,
  `test_cargar_page_id.py`, plus `alta_producto.py`'s two-file (DB `producto` + CSV `_DIM_ENVASE`)
  all-or-nothing ordering/compensation design) for `vitalcom_test` tenant isolation — the same class
  of real-data-corruption risk the T3 incident already demonstrated once. Doing that correctly and
  verifying it needs its own pass; T4 continues in a follow-up rather than risk a rushed connection.
  Evidence (25-sep-2026):
  - `"../SISTEMA-app/app/backend/.venv/Scripts/python.exe" -m pytest db/test_db.py -q` → 35 passed
    (updated `test_tablas_migradas_db_es_subconjunto_de_verdad_db` to expect `evento` in the set).
  - `python -m pytest Ads/_TOOLS -q` → 45 passed (same baseline count as T3; three
    `test_gen_publicacion.py` scenarios that reach `registrar_excepcion()` — F2 gate,
    F3.exploracion gate — updated for `vitalcom_test` tenant isolation/bootstrap;
    `test_reingreso_f1.py::test_ejecucion_real_anexa_evento` and all 21 scenarios of
    `test_registrar_evento.py` likewise updated — none of them previously isolated against
    Postgres, so left unmodified they would have tried to write test fixture rows into the REAL
    `vitalcom` database on the default `PGDATABASE`, the same class of incident as T3's).
  - `python Ads/_TOOLS/flujo.py --todo` (read-only) → exit 0, clean.
  - `python Ads/_TOOLS/decidir.py --json` → exit 0, no `--escribir`.
  - Real-data check (read-only on `PRODUCTOS/_EVENTOS.csv`, per the CAREFUL/HARD RULES sections —
    never ran `registrar_evento.py`/`flujo.py --escribir`/`perfilar_angulos.py --registrar`/
    `reingreso_f1.py` for real): `db/escribir.verificar_csv_sincronizado(con, "evento", "PRODUCTOS",
    tenant_id="vitalcom")` reported already SINCRONIZADO — the session-start
    `flujo.py --todo --escribir` had already reloaded `raw.evento` from the current
    `_EVENTOS.csv` (including the operator's 4 uncommitted rows) today, so no `--tomar-csv`
    bootstrap write was needed or run.
  - `git status --short` / `git diff --stat -- PRODUCTOS/_EVENTOS.csv` before and after every test
    run and every command above: identical (still exactly the same 4-line uncommitted diff as at
    session start). No other `PRODUCTOS/*` file changed.
  - `cd app/backend && uv run pytest -q` → ran (no code in `app/backend` touched by T4's reduced
    scope); see the report for the exact count observed.

- [~] T4 continuation (25-sep-2026, same day) — `estado_flujo` and `_DECISIONES.json` connected.
  STILL PARTIAL: `producto` (`_DIM_PRODUCTOS.csv`) deliberately NOT attempted this pass — see
  "Deferred" below, same risk class the previous pass already flagged.
  Result: `flujo.py:escribir_estado()` no longer writes `_ESTADO_FLUJO.csv` with a direct
  `csv.DictWriter` — it now calls `db/escribir.verificar_csv_sincronizado()` +
  `db/escribir.reemplazar(con, "estado_flujo", filas, prod_dir=..., bkdir=env.base/backups_csv,
  tenant_id=TENANT_ID)`, import LOCAL inside the function (same reason as the existing
  `registrar_evento` import a few lines below it: avoids a module-level import cycle and keeps
  flujo.py's SOLO LECTURA path psycopg-free, since this branch only runs under `--escribir`).
  `decidir.py --escribir` no longer writes `_DECISIONES.json` with a direct `json.dump()` — it
  calls `db/escribir.verificar_decision_sincronizada()` (new) + `db/escribir.reemplazar_decision(
  con, res, prod_dir=..., tenant_id=TENANT_ID)`, import LOCAL inside `main()` under
  `if args.escribir:` (decidir.py's read-only path is still imported psycopg-free by the parity
  gate's subprocess, which never passes `--escribir`). `tables.TABLAS_MIGRADAS_DB` gains
  `"estado_flujo"`. `_DECISIONES.json` has no `TABLE_SPECS` row (blob, not a column-by-column
  mirror), so it can never join `TABLAS_MIGRADAS_DB`/`TABLAS_VERDAD_DB` the generic way; its own
  drift guard is the new `db/escribir.verificar_decision_sincronizada()`, and
  `db/cargar.py --tomar-csv _DECISIONES.json` (or `decisiones_json`) is its special-cased
  bootstrap/recovery inside `tomar_csv()` (no `TABLE_SPECS` row to resolve against).
  Both `TENANT_ID` module constants (`flujo.py`, `decidir.py`) are the only override points for
  test isolation, same pattern as `registrar_evento.py`/`ingerir_lucidsales.py` (T3/T4).
  Deferred (not attempted this pass, same risk class the previous pass flagged for `_DIM_PRODUCTOS.csv`):
  `producto` — `alta_producto.py`/`editar_producto.py` still write `_DIM_PRODUCTOS.csv` directly.
  Read both files in full this pass: `alta_producto.py`'s `aplicar()` is its own all-or-nothing
  sequence (folders + packshot copy + `2_DATA_PRODUCTO.txt` + two CSVs, `_DIM_PRODUCTOS.csv` and
  `_DIM_ENVASE.csv`, with manual rollback on exception) — the two-file DB-write-then-CSV-write
  ordering/compensation design the task called for (write `_DIM_ENVASE.csv` to a temp file first,
  commit the DB write of the product, regenerate the `_DIM_PRODUCTOS.csv` mirror, THEN
  `os.replace` the envase temp into place, with an explicit Spanish recovery message if that final
  replace fails after the DB commit) touches `aplicar()`'s exception/rollback branch directly.
  `editar_producto.py` is a SHARED generic engine (`aplicar_escrituras()`, a single
  `{ruta: bytes}` all-or-nothing writer used by THREE callers — `cambiar_costo.py`,
  `cargar_cuenta.py`, `cargar_page_id.py`) that writes `_DIM_PRODUCTOS.csv` bytes together with
  the product's TXT package files in one `{ruta: bytes}` batch; special-casing just the CSV path
  inside that shared engine to go through Postgres while keeping the TXT files' all-or-nothing
  semantics is a structural change to code three other real writers depend on, not an isolated
  edit. Doing this correctly still needs, per the previous pass's own assessment: updating
  `test_alta_producto.py`/`test_cambiar_costo.py`/`test_cargar_cuenta.py`/`test_cargar_page_id.py`
  for `vitalcom_test` isolation BEFORE connecting (same pattern as this task's
  `test_registrar_evento.py`/`test_cli_solo_lectura.py` changes), confirming the app's
  `alta_producto.py` launcher interpreter (`VISTAS/_MANIFIESTO.json`) has `psycopg`, and deciding
  the exact compensation wording — none of which fits safely alongside T4's other two connections
  in the same reasoning pass without rushing the one part of P3 that writes irreversibly to a
  product's onboarding record. Treating this as its own follow-up (T4 continuation part 2, or
  folded into T5) is a deliberate scope decision, not a tool refusal.
  Evidence (25-sep-2026):
  - `"../SISTEMA-app/app/backend/.venv/Scripts/python.exe" -m pytest db/test_db.py -q` → 42 passed
    (35 baseline + 7 new: `estado_flujo` reemplazar/drift-guard/tomar-csv parity with `venta`'s
    pattern, `reemplazar_decision()`/`verificar_decision_sincronizada()` byte-identity + drift +
    `tomar-csv _DECISIONES.json` bootstrap, `TABLAS_MIGRADAS_DB` assertion updated).
  - `python -m pytest Ads/_TOOLS -q` → 45 passed (same count as the T4-first-pass baseline —
    `test_cli_solo_lectura.py`'s `test_flujo_todo_con_escribir_si_escribe`/
    `test_decidir_con_escribir_si_escribe` were rewritten in place, not added, to bootstrap
    `raw.estado_flujo`/`raw.decisiones_json` in a unique `vitalcom_test` tenant before running the
    real writer, mirroring `test_registrar_evento.py`'s `_bootstrap_evento()` pattern).
  - Real-data bootstrap+writer run (25-sep-2026): drift check against real `vitalcom` found
    `estado_flujo` already SINCRONIZADO (session-start `flujo.py --todo --escribir` had already
    loaded it) and `_DECISIONES.json` never-imported (first run) →
    `python db/cargar.py --tomar-csv _DECISIONES.json` (1 fila) → both guards green → ran the one
    authorized real writer, `python Ads/_TOOLS/decidir.py --escribir` (exit 0) → drift guards for
    both tables green again afterward. `raw` counts for
    `venta`/`entrega_conjunto_dia`/`entrega_anuncio_dia`/`evento`/`estado_flujo` identical
    before/after (3491/1094/1041/89/5). `git diff --stat` shows only `PRODUCTOS/_DECISIONES.json`
    changed (11 lines) plus the pre-existing untouched 4-line `_EVENTOS.csv` diff;
    `_ESTADO_FLUJO.csv`/`_DIM_PRODUCTOS.csv` untouched.
  - `python Ads/_TOOLS/flujo.py --todo` (read-only) → exit 0, no `PRODUCTOS/*` change.
  - `python Ads/_TOOLS/decidir.py --json` (read-only) → exit 0, no `PRODUCTOS/*` change.
  - `cd app/backend && uv run pytest -q` → ran in background (no `app/backend` code touched this
    pass either); see the report for the exact count observed.
  - Unrelated pre-existing defect surfaced by the `hook_csv.py` PostToolUse guard on every edit to
    `decidir.py` in this pass: `DOCTRINA/GUIA_MADRE_PARAMETRIZADA.md` doesn't declare the
    `exploracion_n_angulos` parameter that `_PARAMETROS_DECISION.csv` already has (introduced in
    commit `0d15d0d`, before this session, no uncommitted diff on either file) — out of this
    task's authorized scope (only `decidir.py`/`flujo.py` persistence), left unfixed and flagged
    here rather than silently worked around.
- [ ] T5 — `decidir.py` and app backend read from Postgres. Checks: parity, e2e, backend tests.
- [ ] T6 — Daily cycle script + Windows Task Scheduler task. Check: first real run writes its
  parity row.
- [ ] T7 — 7-consecutive-green-days counter. Closes P3.
- [ ] T8 — Defects found during P3: (a) `_DIM_ANUNCIOS.csv` has two full-rewrite writers
  (`sembrar_anuncios.py:188`, `firma.py:174`) — verify whether one clobbers the other and fix;
  (b) Claude task `auditoria-vitalcom-diaria` stops after its first command and its SKILL.md
  still names ETAPA-8 — fixed together with T6;
  (c) pre-existing defect surfaced by `hook_csv.py` on every edit to `decidir.py`/`flujo.py`:
  `DOCTRINA/GUIA_MADRE_PARAMETRIZADA.md` doesn't declare the `exploracion_n_angulos` parameter that
  `_PARAMETROS_DECISION.csv` already has (introduced in commit `0d15d0d`, before this session, no
  uncommitted diff on either file) — out of P3's authorized scope, flagged during T4 and T4
  continuation, still unfixed.

## Progress
- 2026-09-25: branch created, feature document created.
- 2026-09-25: T1 done.

- 2026-09-25: T2 done.

- 2026-09-25: T3 done (closed after vitalcom_test created; 35 db tests green).
- 2026-09-25: T4 continuation, part 1 — `estado_flujo`/`_DECISIONES.json` connected (commit
  `faf0bf3`); `producto` deferred, see "Next step".
- 2026-09-25: T4 continuation, part 2 — `producto` connected, T4 CLOSED. `db/tables.py` adds
  `"producto"` to `TABLAS_MIGRADAS_DB` (commit `cf3a004`). `alta_producto.py`/`editar_producto.py`
  write `_DIM_PRODUCTOS.csv` through `db/escribir.reemplazar()` with the staged-temp + commit +
  replace ordering the design called for (commit `99af471`). `test_alta_producto.py`/
  `test_cambiar_costo.py`/`test_cargar_cuenta.py`/`test_cargar_page_id.py` isolated against
  `vitalcom_test`, unique tenant per file, failure-injection scenarios rewritten for the new
  two-phase write (commit `6610c23`). Found and fixed during verification (not part of the
  original design, real bug): `app/backend/tests/test_alta_por_la_app.py` copies the real
  `alta_producto.py` into a throwaway toy system with no sibling `db/` package — the import
  crashed 4 previously-passing backend tests (422 instead of 201). Fixed by adding this repo's
  `db/` to `PYTHONPATH` for the subprocess (not by duplicating `db/` into the fixture, which would
  have cascaded into copying its `Ads/_TOOLS` dependencies too — `venta_identidad.py`,
  `upsert_fact.py`) and isolating that test file against `vitalcom_test` the same way (commit
  `e192481`). Confirmed: `config.python_del_sistema()` (what the app uses to launch
  `alta_producto.py`, `VISTAS/_MANIFIESTO.json:809`) resolves to the system `python` on PATH,
  which has `psycopg` in this environment.
  Evidence (25-sep-2026):
  - `"../SISTEMA-app/app/backend/.venv/Scripts/python.exe" -m pytest db/test_db.py -q` → 42 passed
    (same as T4 continuation part 1's baseline — no new db/test_db.py tests needed: the byte-
    identity/drift-guard tests added in T2 already cover all 7 `TABLAS_VERDAD_DB` tables
    generically, `producto` included).
  - `python -m pytest Ads/_TOOLS -q` → 45 passed (same baseline count — the 4 test files were
    rewritten in place, not added).
  - `cd app/backend && uv run pytest -q` → 171 passed, 4 failed (`test_alta_por_la_app.py`, the
    `ModuleNotFoundError` above) before the fix.
  - Orchestrator incident during verification: multiple concurrent full `uv run pytest` runs
    (this writer's own background run plus the orchestrator's own run, started in parallel)
    starved shared resources and left orphaned `fake_claude.py` child processes behind, which is
    what kept a `pytest` process alive after printing its summary — NOT a leak introduced by this
    task's code. Confirmed clean: after killing every stray `python.exe` (checked via
    `Get-CimInstance Win32_Process`, none left, no `pg_stat_activity` rows on `vitalcom`/
    `vitalcom_test` either), the flaky `test_pasos.py::test_cada_paso_recibe_las_rutas_de_lo_
    anterior_y_ninguna_herramienta_de_meta` scenario the orchestrator saw fail passed on its own
    in isolation — confirming it was resource contention, not a regression from `producto`.
  - `timeout 900 uv run pytest -q`, run ONCE and alone (checked `Get-CimInstance Win32_Process`
    for stray `python.exe` first) → **175 passed, 0 failed, exited cleanly on its own** in 307s —
    full baseline restored, no hang.
  - `python Ads/_TOOLS/flujo.py --todo` (read-only) → exit 0, clean.
  - `python Ads/_TOOLS/decidir.py --json` (read-only) → exit 0, clean.
  - Real-data check: session-start `flujo.py --todo --escribir` had NOT bootstrapped
    `raw.producto`; running the required `db/test_db.py` suite triggered
    `_bootstrap_migradas_desde_csv_real()` (now iterating `producto` too, tenant `vitalcom`) as a
    side effect, which is exactly the sanctioned bootstrap (`db/cargar.py --tomar-csv
    _DIM_PRODUCTOS.csv`, run generically). Verified after: `verificar_csv_sincronizado(con,
    "producto", "PRODUCTOS", tenant_id="vitalcom")` → SINCRONIZADO; `raw.producto` row count for
    tenant `vitalcom` = 5, matching `_DIM_PRODUCTOS.csv`'s real row count (5) exactly.
  - `git status --short` / `git diff --stat -- PRODUCTOS/` before and after every test run and
    command above: identical throughout (same 5-file diff as at session start — the pre-existing
    uncommitted `_EVENTOS.csv`/`_DECISIONES.json`/`_AUDITORIAS` changes, untouched; no other
    `PRODUCTOS/*` file changed). Real `vitalcom` `raw.producto` row count for tenant `vitalcom`
    (5) identical before and after both pytest suites.

## Next step
T5 — `decidir.py` and app backend read from Postgres (parity, e2e, backend tests). Also revisit
T8(a) (`_DIM_ANUNCIOS.csv` double writer) if not folded into T4, and T8(c) (the
`exploracion_n_angulos` doc-drift defect flagged during T4, still unfixed).
