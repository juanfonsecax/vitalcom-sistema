# Feature: ordenes-sin-dinero-inventado

## Objective
No Meta order that moves money may be built on an invented budget or on stale data.

## Evidence (exploration 2026-10-05)
- `gen_ordenes.py:393-397`: ESCALAR defaults `daily_budget` to 2.99 when the snapshot lacks it.
  The real snapshot `Ads/_INGESTA/META/snapshot_GTR7.json` carries NO `daily_budget` on any
  object, so every ESCALAR order today is computed on 2.99. In CBO the budget lives on the
  campaign, so an adset never has one.
- `gen_ordenes.py:472-473` and `decidir.py:1082-1086` only print a warning when the data lag
  exceeds `rezago_max_dias` (`_PARAMETROS_DECISION.csv`, 2 days); the calls are still emitted.
- The app executes only `llamadas` (workflows.py:106,365): omitting a call is the effective block.
- Audit claim "ad_id as string in ingestion" is already fixed (`s_id()` in ingerir_lucidsales.py;
  zero e+ ids since 2026-09). The 2006 e+ rows are Jul-Aug history, covered by
  `mapear_ad_id_hist.py`; out of scope here.

## Scope
`Ads/_TOOLS/gen_ordenes.py`, `Ads/_TOOLS/test_gen_ordenes.py`, invariant 13 wording in `CLAUDE.md`
and the `rezago_max_dias` description in `_PARAMETROS_DECISION.csv`.

## Decisions
- ESCALAR without a real positive `daily_budget` in the snapshot → no call, one blocker.
- Lag > `rezago_max_dias` or unknown → ESCALAR blocked (no call, blocker). PAUSAR still emitted
  with a warning: stopping spend on stale data is conservative and reversible; adding spend is not.

## Tasks
- [x] T1 ESCALAR blocks without real daily_budget (route: inline; 2 files, small) — 62d07f7
- [x] T2 Stale or unknown lag blocks ESCALAR, PAUSAR keeps a warning (route: inline) — 62d07f7
- [x] T3 Invariant 13 and parameter description say "blocks escalation" (route: inline) — eee7f05

### Snapshot with real budgets (evidence 2026-10-05, live read of GTR7, read-only)
- Meta READS `daily_budget` as `{"value":"3.99","unit":"USD"}` (major units); ABO campaigns omit it,
  CBO campaigns carry it. `ads_update_entity` WRITES integers in minor units (399) and requires
  `ad_account_id` + `entity_type` (campaign|ad_set|ad). gen_ordenes sent a USD float and neither arg.
- Snapshot shape (workflows.py PROMPT_SNAPSHOT + skill publicar-meta) asks only id/nivel/name/status.
- `verificar_orden.py` compares budgets as floats: breaks on the object format.
- [x] T4 Shared budget parser `presupuesto_meta.py` (UNIDAD_MENOR single owner) (route: delegated writer) — 8af0e37
- [x] T5 gen_ordenes: minor-unit integer, CBO targets the campaign, args carry account + type (delegated) — 8af0e37
- [x] T6 verificar_orden compares in minor units via the parser (delegated) — 8af0e37
- [x] T7 Snapshot shape asks campaign_id, effective_status, daily_budget (prompt + skill) (delegated) — 08434ef

## Checks
TDD on (tests first, RED observed). Runner: `python -m pytest -q Ads/_TOOLS/test_gen_ordenes.py`,
then full `Ads/_TOOLS` suite and `app/backend` tests touching orders.

## Progress
- RED observed: 4 new tests failed on the old code (unittest), baseline green.
- GREEN: `test_gen_ordenes.py` 13/13; `pytest Ads/_TOOLS` 59/59; app `test_ordenes_api.py` +
  `test_api_espeja_los_csv.py` 17/17; `verificar_guia_madre.py` clean; real-data run OK.

- T4-T7 (delegated writer, sonnet): RED observed in test_gen_ordenes/test_presupuesto_meta/
  test_verificar_orden; GREEN 19/5/6; pytest Ads/_TOOLS 60/60 after resyncing reglas-sistema
  (f486c86, desync caused by eee7f05); app suite 231 passed, 6 failed in test_alta_por_la_app.py
  (ModuleNotFoundError upsert_fact in alta_producto.py; files untouched by this branch).

## Next step
`Ads/_INGESTA/META/snapshot_GTR7.json` is from 2026-09-08 in the old shape: ESCALAR blocks until a
fresh snapshot is dumped with the new shape (publicar-meta pre-flight, read-only).
