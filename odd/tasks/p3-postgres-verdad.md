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
  e2e NOT run: `app/frontend` has no `node_modules` (needs setup) — pending.
- [ ] T6 — Daily cycle script + Windows Task Scheduler task; runs the drift guard before
  `decidir.py`. Check: first real run writes its parity row. Includes T8(b).
- [ ] T7 — 7-consecutive-green-days counter. Closes P3.
- [ ] T8 — Defects found during P3:
  (a) `_DIM_ANUNCIOS.csv` has two full-rewrite writers (`sembrar_anuncios.py:188`, `firma.py:174`)
  — verify whether one clobbers the other and fix;
  (b) Claude task `auditoria-vitalcom-diaria` stops after its first command and its SKILL.md still
  names ETAPA-8 — fix with T6;
  (c) `DOCTRINA/GUIA_MADRE_PARAMETRIZADA.md` doesn't declare `exploracion_n_angulos`, which
  `_PARAMETROS_DECISION.csv` has (since `0d15d0d`); `hook_csv.py` flags it on every edit to
  `decidir.py`/`flujo.py`.

## Next step
T6 — daily cycle script + Windows Task Scheduler (+ T8b). e2e for T5 still pending.
