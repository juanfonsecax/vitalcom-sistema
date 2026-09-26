# P3 — Postgres becomes the source of truth (CSV as mirror)

> Current state only. History (incidents, full evidence logs) lives in git: see the commits
> listed per task and `git show <hash>` / `git log -- odd/tasks/p3-postgres-verdad.md`.

## Objective
Program writers write to Postgres; `PRODUCTOS/*.csv` become a byte-identical mirror regenerated
from the database. Readers (`decidir.py`, app backend) read from Postgres.

## Scope (authorized 2026-09-25)
Branch `feat/p3-postgres-verdad` from `ac7696f`. Never touch or stage the operator's uncommitted
files: `PRODUCTOS/_EVENTOS.csv`, `PRODUCTOS/_DECISIONES.json`, `PRODUCTOS/_AUDITORIAS/`,
`.claude/launch.json`, `.claude/settings.local.json`.

## Decisions
- Operator-edited dimension CSVs stay on CSV → `raw` → `core` during P3. P3b: app screens to edit
  them, then they move to Postgres.
- Closing criterion: 7 consecutive calendar days with a green daily run, launched by Windows Task
  Scheduler at PC boot (run ASAP after a missed start). A failed or missing day resets the counter.
- The Claude task `auditoria-vitalcom-diaria` stops after its first command; the deterministic cycle
  must not depend on it (it keeps only the written analysis).
- Writers write `raw` (verbatim rows); `db/nucleo.construir_core()` rebuilds `core` in the same
  transaction; mirror regenerated after commit (temp + `os.replace`).
- Drift guard `db/escribir.verificar_csv_sincronizado()` aborts a write if the CSV differs from what
  the DB would export. Recovery: `python db/cargar.py --tomar-csv <file>`.
- Postgres down → the run fails (red day). Never silently fall back to CSV.
- Orchestrator decides technical questions and fixes defects found along the way (operator, 25-sep).

## Config
- TDD: off (source: none). Ordinary checks per task.
- Runners (run each once, never two suites at the same time — concurrent backend runs hang via
  orphan `fake_claude.py`):
  - db: `"../SISTEMA-app/app/backend/.venv/Scripts/python.exe" -m pytest db/test_db.py -q`
  - tools: `python -m pytest Ads/_TOOLS -q`
  - backend: `cd app/backend && timeout 900 uv run pytest -q` (~5 min)
- Test isolation: every Postgres test uses `PGDATABASE=vitalcom_test`, unique tenant per file, and
  refuses to connect to real `vitalcom`.
- RDD: off. Delivery strategy: ask-on-risk.

## Postgres-truth tables (`db/tables.TABLAS_MIGRADAS_DB`)
| Table | Mirror | Writer |
|---|---|---|
| venta / entrega_conjunto_dia / entrega_anuncio_dia | `_FACT_VENTAS` / `_FACT_ENTREGA` / `_FACT_ENTREGA_ANUNCIO` | `ingerir_lucidsales.py`, `ingerir_meta.py`, `bajar_meta_insights.py` via `db/escribir.upsert()` |
| evento | `_EVENTOS.csv` | `registrar_evento.anexar()` (single appender) |
| estado_flujo | `_ESTADO_FLUJO.csv` | `flujo.py --escribir` |
| producto | `_DIM_PRODUCTOS.csv` | `alta_producto.py`, `editar_producto.py` |
| raw.decisiones_json | `_DECISIONES.json` | `decidir.py --escribir` |

## Tasks
- [x] T1 — Writer inventory (`db/README.md` "P3 — inventario de escritores"). `c1948eb`
- [x] T2 — Write layer `db/escribir.py` + byte-identical mirror. `59a906e`
- [x] T3 — Fact ingestors write DB then mirror. `238a75b`, `21035b1`
- [x] T4 — Events, decisions, estado_flujo, producto write DB. `8616f1f`, `e3d8773`, `faf0bf3`,
  `cf3a004`, `99af471`, `6610c23`, `e192481`. Checks at `8a455a5`: db 42, tools 45, backend 175.
- [x] T5 — `decidir.py` and app backend read from Postgres. `0f46ab4`, `8251e76`, `0060b49`.
  Route: delegated writer (2+ non-trivial files). `db/leer.py` read API; switch
  `VITALCOM_FUENTE=db|csv` (default `db`); decidir materializes the 5 migrated tables to a temp dir
  only when `PROD` is the real `PRODUCTOS/` (fixtures and `DECIDIR_PROD_DIR` stay on CSV, so
  `flujo.py` needed no change); backend `contratos.py` reads through `db/leer.py`, Postgres down →
  503. Test overrides: `DECIDIR_TENANT_ID`, `VITALCOM_DB_TENANT`; backend conftest forces `csv`.
  Checks (25-sep): db 46 passed · tools 45 passed · backend 176 passed · real
  `decidir.py --json` db vs csv: IGUAL (orchestrator re-ran it) · protected files untouched.
  e2e (25-sep): `pnpm install --frozen-lockfile` + `pnpm build`, then Playwright against the real
  system (all specs read-only; PRODUCTOS md5 + git status identical before/after). Parallel run
  was flaky: Postgres 3 failed, CSV 1 failed; serial 15/15 in both. DB mode costs ~+400 ms per
  flujo.py/decidir.py call (connect + materialize). Fixed `workers: 1` → 15/15 (`1fdad25`).
  Follow-up (not P3): speed up DB-mode reads (reuse a connection, avoid re-materializing).
- [x] T6 — Daily cycle script + Windows Task Scheduler task. Code done: `db4dc1d`, `d5ae1f5`,
  `584d82a`. `Ads/_TOOLS/ciclo_diario.py` (preflight drift guards → bajar/ingerir LucidSales →
  Monday control → bajar_meta_insights → ciclo_hoy → gen_dashboard → postcheck guards + decidir
  db-vs-csv parity; always appends a row to `PRODUCTOS/_CORRIDAS_DIARIAS.csv`, VERDE/AMARILLO/ROJO;
  AMARILLO = Meta PARTIAL, counts as green). `registrar_ciclo_diario.ps1` (daily 05:00 + at logon,
  StartWhenAvailable, `--si-falta-hoy`). Standalone on purpose; backend `workflows.py`
  `PASOS_CICLO_NOCTURNO` models a similar chain inside the app (duplication noted, not refactored).
  T8(b) done in `584d82a` (live task prompt edited outside the repo: read-only, no Bash, etapa-7
  only). Registration: first attempt "Access is denied" (at-logon trigger without `-User` needs
  admin) → fixed `6544862`; operator registered the task 25-sep.
  First real run 25-sep 20:53 → ROJO: `gen_decisiones.py` rewrote `_DECISIONES.json` on disk after
  `decidir.py --escribir` (writer missed by T1) → fixed to write through Postgres `4ad8127` (same
  commit: stage-labelled drift message, single-line run-log rows). `flujo.py` mirror backup went to
  repo-root `backups_csv/` → `_RESPALDOS/backups_csv/` `d04612c`. Recovery: `db/cargar.py
  --tomar-csv _DECISIONES.json`.
  Second real run 25-sep 21:01 → **VERDE, paridad IGUAL**. Checks: tools 46 passed.
- [~] T7 — 7-consecutive-green-days counter. Code done `5b975ec`: `ciclo_diario.racha_verde()`
  (a day is green if its LAST row is VERDE/AMARILLO; missing or ROJO-ending day breaks; today
  without a row keeps yesterday's streak), printed after every run, on `--si-falta-hoy` skip and
  with `--racha`; the Claude audit message shows `RACHA: N/7` (same rule, read from the CSV).
  Checks: runner 26/26, tools 46 passed, real `--racha` → 1/7 (2026-09-25).
  Pending: 7 consecutive green days → earliest 2026-10-01. That closes P3.
- [x] T8 — Defects found during P3:
  (a) DONE `63ea89c`: confirmed clobber — `firma.py --generar` added a `firma` column and
  `sembrar_anuncios.py --escribir` dropped it (fixed column list; real file had 0/56 firmas).
  Seeder is now the single writer and derives `firma`; `firma.py --generar` only prints.
  Checks: seeder on a temp copy → 56/56 with firma, real file md5 unchanged, tools 46 passed.
  Note: 0/56 firmas complete — `destino_key` is empty in every row (data gap, not code);
  (b) DONE with T6 (`584d82a`): Claude audit task read-only, no Bash, etapa-7 only;
  (c) DONE `0060970`: `EXPLORACION_N_ANGULOS` declared in the Guía Madre (section 9) as a system
  rule (P12, 23-sep, operator decision — no mentor class) and registered in
  `verificar_guia_madre.py` so its value is compared against the CSV (34 verified, was 33).
  Checks: checker "Sin fallas"; negative test with 4 on a temp copy → flagged; tools 46 passed.

## Next step
Let the streak run (`python Ads/_TOOLS/ciclo_diario.py --racha`); check on 26-sep that the
scheduled task fired on its own. Only open item: the streak. Follow-up outside P3: DB-mode read speed.
