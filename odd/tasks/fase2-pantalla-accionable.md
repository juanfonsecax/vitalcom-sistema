# Feature: fase2-pantalla-accionable

## Objective
The Fase 2 screen tells the operator, per angle, what to do next — at the top, as a checklist that ticks
itself off — instead of burying the actionable part (concept gallery) at the bottom.

## Problem / why
Operator feedback 2026-09-29 (CLEARSTEM): the concept gallery is far down and unlabeled (which angle? which
campaign?), the break-even CPA is not visible per angle, losing angles mix with active ones, and "what do I do
now" is unclear. Presentation only: the motor (`decidir.py`), `flujo.py`, the generators and the CSVs stay
untouched; the frontend never computes business numbers (they come from the API).

## Scope (authorized: "si dale", 2026-09-29)
- [x] T1 "Qué hacer ahora" at the top: one card per active angle (winner in test / in queue) with a checklist
      derived from data the API already exposes (concepts generated vs required, published, launched); done
      steps shown ticked.
- [x] T2 Per-angle CPA vs break-even with colour (green below, amber near, red above) and the motor order in
      one line; values from the API (`_ESTADO_ANGULOS.csv` via backend), never computed in the frontend.
- [x] T3 Gallery grouped inside its angle and labelled by campaign: "Campaña A (conceptos 1-5) · Campaña B
      (6-10)" with real counts.
- [x] T4 Switched-off angles at the bottom, collapsed, no action buttons.

## Constraints
Smallest change; no generator/doctrine/CSV/motor changes; UI copy in the existing Spanish style;
code/comments/commits English; Conventional commits without AI attribution; RDD off; TDD not configured.
Known gap left out on purpose: the prompt button yields 5 concepts per angle while F2 needs 10 (A 1-5 +
B 6-10); T1/T3 must show "6-10 pendientes" honestly, not hide it.

## Route
T1-T4: delegated writer (2+ non-trivial files: Fase2.tsx, angulosFase2.tsx, possibly contratos.py/modelos.py).

## Checks
app/frontend `pnpm test`, `pnpm build`; app/backend `VITALCOM_FUENTE=csv uv run pytest -q` if backend changes.

## Progress / evidence
- T1-T4 implemented (delegated writer). Backend: new read-only fields `checklist`, `cpa_*_q`, `cpa_be_q`,
  `semaforo_acum/ventana`, `orden_motor` per angle; `numero`/`campana` per concept; `conceptos_requeridos`
  and `campanas` (from `_PARAMETROS_PUBLICACION.csv` fase 2 brazos A+B). Types regenerated from the app object.
- Semaphore rule lives in new `Ads/_TOOLS/semaforo_be.py` (test_semaforo_be.py), because
  `tests/test_sin_aritmetica.py` forbids CPA thresholds inside the app package.
- Layout: Qué hacer ahora -> gallery (Campaña A/B) -> fatiga -> losers collapsed at the bottom.
- Checks: frontend `pnpm test` 171 passed, `pnpm build` ok; backend subset (angulos, prompt, fases_api,
  sin_aritmetica) 50 passed; first full backend run 236 passed / 1 failed (the arithmetic guard, fixed);
  second full run 237 passed (327.78s). Known gap kept: concepts 6-10 show as pending.
- "Lanzado" step = a LANZAMIENTO/LANZAMIENTO_TEST event whose motivo says FASE 2 (no per-angle launch event exists).

## Next step
Operator review in the browser; concepts 6-10 generator (separate task).
