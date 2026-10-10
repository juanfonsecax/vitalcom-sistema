# FASE 2 prompts: robust concept generation

## Objective
Make FASE 2 concept generation produce correct prompts for any product and any winning angle,
without manual rewrites.

## Problem
1. `armar_prompts_fase2.py` copies the reference ficha's `dispositivo_dominante` verbatim. When the
   reference ad belongs to another niche, that content leaks into the prompt (CN08 / F021 asked
   ChatGPT for "two feet on a clinic bed" for CLEARSTEM, an acne supplement).
2. `_PERFIL_CREATIVO.json` holds texts for a single angle (`angulo_key` + `textos`). When the winner
   changes, the file has to be rewritten and the previous angle's texts are archived by hand.

## Scope
- Canonicals (`Ads/_SWIPE/_BLUEPRINTS/CANONICOS/CN*.json`) get a product-neutral `dispositivo`;
  the prompt uses it before the ficha's text.
- Creative profile holds texts per angle (`textos_por_angulo`); legacy single-angle files keep working.
- Producer docs (skill `generar-conceptos`, etapa-9) add an angle instead of overwriting.
- Migrate `PRODUCTOS/CLEARSTEM/_PERFIL_CREATIVO.json` (both angles) and any other existing profile.

Out of scope: renewing the swipe bank, markets other than the existing ones.

## Constraints
- Use the system Python (`~/AppData/Local/Python/bin/python`), not the backend venv.
- CSV/JSON written by real writers, never by hand-edited strings.
- No archaeology notes in the system files: current rule only.

## TDD
Mode: on (session choice, operator authorized "arreglemos"). Runner:
`~/AppData/Local/Python/bin/python -m pytest Ads/_TOOLS/test_armar_prompts_fase2.py -q`.
Known environmental failure: `test_armar_prompts_fase2` (OSError WinError 6), fails on base.

## Tasks
- [x] T1 App never launches Claude through a `.cmd` wrapper — inline — commit 78cbdb4
- [x] T2 Selector spreads repeated concepto_key to the least used — inline — commit a06c2ae
- [x] T3 Per-angle texts in the creative profile + producer docs + migration — delegated (2+ files) — commit e80b908
- [x] T4 Product-neutral `dispositivo` per canonical, preferred over the ficha — delegated (23 files) — commit efc7926

- [ ] T5 Manual render path: promote IMAGEN rows from PENDIENTE_GENERAR to GENERADO when the PNG
  with its canonical name exists; app button — delegated (script + test + manifest)

## Acceptance
- T3: generating for angle B never needs to delete angle A's texts; missing angle B blocks with
  `dato = perfil_creativo`; legacy file still loads.
- T4: every canonical has a non-empty neutral `dispositivo`; no prompt carries ficha device text
  when the canonical declares one; CLEARSTEM prompts no longer mention another niche.

## Delivery
Strategy: ask-on-risk. Forecast ~300 authored lines. RDD: off (default).

## Progress
- 2026-10-09: T1, T2 committed on `fix/fase2-prompts-robustos`.
- 2026-10-09: T3 (e80b908) and T4 (efc7926) committed. `test_armar_prompts_fase2` and `test_datos_producto` fail only with the environmental OSError; the rest pass (36 and 12). Profiles migrated to perfil_creativo/2: CLEARSTEM, NusavaB12, TINNIDROP. `datos_producto.revisar_perfil` reads `textos_por_angulo`; `agrupar_canonicos.py` owns the canonical `dispositivo` (field `dispositivo_neutro` in FAMILIAS).
- 2026-10-09: parent spot check: 46 passed, 2 environmental failures; `test_datos_producto` also fails on
  base 5e59c38 (confirmed in a detached worktree). CLEARSTEM ANTI_FALSIFICACION package rebuilt with the
  neutral devices for the 10 registered canonicals: no niche leak. Rows committed in 3ffea09.
- 2026-10-09: T5 (cfab103): `marcar_generados.py` + 11 tests, manifest action `producto.marcar_conceptos_generados` (button visibility, no screen wiring yet), FLUJO.json F2.conceptos clause. Backend manifest tests: 69 passed. Frontend placement (backend descriptor + component) still pending.

## Next step
Render the 10 CLEARSTEM concepts with `etapa-render`. Push / PR are the operator's decision.
