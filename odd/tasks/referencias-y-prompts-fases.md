# Feature: referencias-y-prompts-fases (Block A)

## Objective
Make FASE 1 and FASE 2 screens show the real, copyable prompt next to its reference image, and make
phase-blocked ESCALAR orders understandable and actionable for the operator.

## Problem / why
- FASE 2 gallery shows a generic one-line placeholder built in `app/backend/vitalcom_app/contratos.py:441`
  instead of the real prompt already produced by `Ads/_TOOLS/armar_prompts_fase2.py` in
  `Ads/MEDIA_{producto}/FASE2_{angulo}/PAQUETE_CREATIVO_*.json` (which also carries the swipe
  reference image path `foto_base_competidor`). Angle-key mismatch: `_DIM_CREATIVOS.csv` uses
  `RESISTENCIA_INSULINA_SOP`, the paquete folder uses `RESISTENCIA_INSULINA`.
- FASE 1 has no reference image. Doctrine fixes concept `C2_BENEFICIOS` variant `ligera`
  (`DOCTRINA/CALENDARIO_ESCALADO.md:144`, `Ads/_SWIPE/_CATALOGO_CONCEPTOS.md` §2). Operator decision
  (2026-09-28): among the 3 `ligera` references in `Ads/_SWIPE/_BANCO_CREATIVOS/C2_BENEFICIOS/`
  (Camila-Recomienda 15, Camila-Recomienda 25, Tiendas-KetsalStore 14) the AI picks ONE per product;
  it is stored as fixed product data (with reason) and used for all 6 angles.
- Hoy: "Escalar en espera" is amber; operator wants it green (it is a winner). `bloqueo_fase` text
  from `Ads/_TOOLS/decidir.py:858-867` is technical ("rompe el invariante 6"); it must say, in plain
  language, that it is lifted by operator action (finish FASE 2 with a 2-of-2 concept winner + log
  CAMBIO_BOT), not by elapsed time.

## Scope (authorized 2026-09-28)
Frontend `app/frontend`, backend `app/backend`, `Ads/_TOOLS/decidir.py` text + its tests, a product
data owner for the F1 reference choice, and the F1 doctrine step that makes the choice.
Out of scope: 4-phase restructure (Block B, separate branch).

## Constraints
- Frontend never computes business data; engine text comes from the API.
- CSVs edited with a real CSV writer; a data point has one owner.
- Commits: Conventional, English, no Co-Authored-By; only files of the task (never PRODUCTOS/ data
  churn from the nightly run, VISTAS/, LucidSales reports).
- Branch: feat/dashboard-visual (no merge/push).
- TDD: not configured (ordinary checks). Checks: `pnpm test`, `pnpm build`, `pnpm exec playwright test`
  (app/frontend); backend `uv run pytest` (app/backend); `python -m pytest Ads/_TOOLS/test_decidir.py`.

## Tasks
- [x] A1 Hoy: phase-blocked ESCALAR in green + plain-language `bloqueo_fase` from decidir.py
      (route: delegated writer — 2 files across engine + frontend) — commit 61d455d.
      Checks: test_decidir gate 1 passed (3 pre-existing `params` fixture errors), frontend 117/117,
      build ok, backend 176 passed. test_gen_ordenes.py fails identically on clean HEAD
      (pre-existing `I/O operation on closed file`). _DECISIONES.json regenerates on the nightly run.
- [x] A2 FASE 2: API serves real prompt + reference image from PAQUETE_CREATIVO; UI copy prompt / copy image
      (route: delegated writer — backend + frontend) — commit 797fffd.
- [x] A3 FASE 1: fixed per-product reference (1 of 3 C2 ligera), owner data + AI choice step + UI
      (route: delegated writer for mechanism, commit 11b3541; parent made the per-product choice
      after viewing the 3 images, commit d7eb8d1). Checks: test_referencia_f1 17 passed, backend
      fase1/fase2 tests 17 passed, frontend 121/121, build ok, playwright 15/15, hook_csv --barrido
      exit 0. Real data: CLEARSTEM F1 ref served 200; F2 5 paquete + 5 pendiente; traversal 404.

## Acceptance
- CLEARSTEM F2 gallery shows the "Actúa como Director de Arte Senior…" prompt and its swipe image.
- Every product F1 Anuncios shows one reference image + prompt, same for 6 angles.
- Hoy blocked ESCALAR card is green and tells what to do.

## Progress / evidence
- A2 done. `contratos.fase2_detalle()` joins each concept against the real
  `Ads/MEDIA_{producto}/FASE2_{angulo}/PAQUETE_CREATIVO_*.json` produced by
  `armar_prompts_fase2.py` (via `_localizar_carpeta_fase2`, resolving the
  `_DIM_CREATIVOS.csv` `_SOP` suffix mismatch against the real `FASE2_*` folder
  on disk), returning `prompt_origen: "paquete"` + real prompt + `referencia_url`
  when matched, or `prompt_origen: "pendiente"` + the exact
  `armar_prompts_fase2.py <producto> <angulo>` command when not — never a
  fabricated prompt. New read-only `GET /api/swipe/{ruta_imagen:path}` endpoint
  (path-safety mirrors `fase1.ruta_de_media`) serves swipe reference images
  restricted to `Ads/_SWIPE/`. New Pydantic models in `modelos.py`
  (`ConceptoFase2`, `Fase2Detalle`, etc.). Frontend `esquema.d.ts` regenerated
  via `pnpm exec openapi-typescript`; `cliente.ts` types now derive from it;
  `Fase2.tsx` shows the reference image (click-to-enlarge), the real prompt in
  the existing `<pre>`, "Copiar" / "Copiar imagen" (Clipboard API, PNG via
  canvas, download fallback), and an explicit pending panel with the exact
  command when no paquete match exists.
  Files: `app/backend/vitalcom_app/{contratos.py,modelos.py,api_fases.py,main.py}`,
  `app/backend/tests/test_fase2_prompt.py` (new, 10 tests),
  `app/frontend/src/{api/cliente.ts,api/esquema.d.ts,pantallas/Fase2.tsx,pruebas/fase2.test.tsx}`.
  Checks: backend `uv run pytest -q` → 186 passed; frontend `pnpm test` → 119
  passed (15 files); frontend `pnpm build` → ok; `pnpm exec playwright test`
  → 15 passed (F2/F3 specs untouched, text unchanged). Real-data CLEARSTEM
  check: first `_DIM_CREATIVOS.csv` row (no `canonico_id`) is honestly
  `pendiente` with command `python Ads/_TOOLS/armar_prompts_fase2.py CLEARSTEM
  DOLOR_EMOCIONAL_MASCULINO`; the 5 matched concepts (e.g. `CN05_LISTA_BENEFICIOS`)
  resolve `prompt_origen: paquete`, the real "Actúa como Director de Arte
  Senior…" prompt, and `referencia_url:
  /api/swipe/_IMG/Camila_Recomienda/15_1364693855873597.jpg` — confirms the
  `_SOP` angle-key mismatch is fixed. `git status` confirmed no
  `PRODUCTOS/*`, `VISTAS/`, `Ads/_INGESTA/`, `Ads/MEDIA_*`, or `Ads/_SWIPE/`
  files were touched. Not committed (per task instructions).

Engram mirror: PENDING (mem_save refused: multiple active runtime sessions).

## Next step
Block A done. Block B (4 phases) pending operator go-ahead on a separate branch.
Known gap: gen_grafo.py orphan regex ignores digits, flags _DIM_REFERENCIA_F1.csv (not hooked).
