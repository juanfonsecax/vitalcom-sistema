# Feature: g06-datos-medibles

## Objective
Apply P1, P2 and P3 of the final pre-SaaS audit (22-sep-2026, report
https://claude.ai/artifact/JQQuer5n1skD1u1K9MfJY9). Goal: the system measures what it claims to
measure: fresh Meta delivery every night, ad ids that survive ingestion, and F1/F2 rows that can
be attributed to angle, format and concept. The operator approved P1-P3 on 22-sep-2026. T1/T2 do not change doctrine;
T3 does (operator decision: F1 all-IMAGEN).

## Why
- Meta delivery (`_FACT_ENTREGA.csv`) stops at 2026-09-05. `bajar_meta_insights.py` (created 16-sep)
  never ingested a row: no `fuente` from it exists. It also filters accounts by `mcp_habilitado=SI`,
  which excludes GTR 13 (CLEARSTEM).
- `ad_id` in `_FACT_VENTAS.csv`: Jul-Aug rows are corrupted (scientific notation, irrecoverable, known
  since 21-ago). Sep rows are clean (0/908). But `s_id()` in `ingerir_lucidsales.py:114` still emits
  `repr(float)`, which is scientific notation for ids > 1e15, if the API ever returns a number.
- In `_DIM_CONJUNTOS.csv` design rows, the angle origin is confounded with the format (VOZ_REAL 12/12
  IMAGEN, TRANSCRIPCION 13/15 VIDEO) and `concepto_key` is SIN_CLASIFICAR in 56/62 rows. F1 does not
  hold the concept fixed and F2 cannot be attributed.

## Where work happens
- Write and commit ONLY in worktree SISTEMA-app (branch feat/app-web). Read real data from ../SISTEMA.
  The operator ff-merges into SISTEMA.
- Never edit data CSVs (_FACT_*, _DECISIONES.json, _ESTADO_*, VISTAS/*.html) here.
- One Conventional Commit per task, tests and docs with the change, no AI attribution lines.

## Constraints
- Do not prune `.claude/agents/ETAPA-*.md` prose (decision 10-sep: evals first). Pointer-level edits only.
- No Meta writes. P1's live run is read-only (Graph API, ads_read token) and needs the operator's
  explicit "yes" before it runs against production SISTEMA.
- Gates that must stay green: `python -m pytest Ads/_TOOLS`, `python Ads/_TOOLS/flujo.py --validar`,
  `python Ads/_TOOLS/verificar_guia_madre.py`, `python Ads/_TOOLS/gen_grafo.py` (no orphans or dead
  routes).

## Mode
- TDD: off (default, no project config). Tests still ship with each change as a functional check.
- RDD: off (default). Delivery strategy: ask-on-risk.

## Tasks
- [x] T1 (P1): Meta nightly ingestion. Code done (T1/T1b), dry-run authorized and verified; stays
      unchecked until the live run in SISTEMA shows max `ventana_fin` >= today-2 (see Next step).
      - `bajar_meta_insights.py`: select accounts by `estado_cuenta=ACTIVE AND tiene_metodo_pago=SI`,
        not by `mcp_habilitado`, so GTR 13 is included.
      - A per-account API failure is reported and skipped, never fatal to the other accounts.
      - Confirm the script appends to `_FACT_ENTREGA`/`_FACT_ENTREGA_ANUNCIO` with its own `fuente`.
      - Wire it into skill `recopilar-lucidsales` after the LucidSales step.
      - Test: the account filter, and failure isolation.
      Route: delegated writer (2+ non-trivial files).
      Check: pytest green; `--dry-run` for yesterday lists GTR 13; after the operator's yes, one live
      run in SISTEMA leaves max `ventana_fin` >= today-2 for the 3 live products.
- [x] T2 (P2): `s_id()` never emits scientific notation. A float id above 2**53 has already lost
      precision: return "" and count it, never a wrong id. Check that every reader of `_FACT_VENTAS`
      inside ingestion keeps `ad_id` as str. Test with an 18-digit id given as a str, an int and a
      float.
      Route: inline if confined to `ingerir_lucidsales.py` plus its test; otherwise delegated.
      Check: pytest green.
- [x] T3 (P3): F1/F2 attribution contract.
      - `gen_plan.py --validar` blocks an F1 plan whose conjuntos have different `formato` or a
        concepto outside the vocabulary.
      - New `_DIM_CONJUNTOS` rows (fecha_alta >= the cutoff date) must carry `formato` and a
        `concepto_key` other than SIN_CLASIFICAR (hook_csv validation). Historical rows stay untouched.
      - DECIDED by the operator 22-sep-2026: F1 runs ALL-IMAGEN. `gen_plan.py --validar` blocks an F1
        plan with any conjunto whose formato != IMAGEN. Competitor videos stay as the angle SOURCE
        (etapa-0 transcripts), not as the F1 creative. Video is tested in F2 as one more concept.
        This is a doctrine change: update the CLAUDE.md phase table and add pointer-level notes in
        ETAPA-0/ETAPA-4/ETAPA-6 plus the fase-1-angulos skill (the video washing step leaves F1).
        No prose pruning.
      Route: delegated writer.
      Check: tests red then green; the existing plans still validate, or the failures are listed.

## Progress / evidence
- T1 code: commit 6ad2add. Account filter now ACTIVE + pago=SI (GTR7/0/1/3/13); per-account failure
  isolated; the script writes fuente "MetaAPI-directo"; wired into recopilar-lucidsales.
  Checks: `python Ads/_TOOLS/test_bajar_meta_insights.py` -> 7 tests OK (parent re-ran);
  `pytest Ads/_TOOLS` -> 28 script files passed; flujo --validar OK; guia madre OK.
  Found: exit 1 on one failed account would halt the app nightly chain -> T1b.
  Note: `pytest Ads/_TOOLS` counts FILES (conftest runs each test_*.py as a subprocess), not tests.
- T1b (delegated writer, with T2): bajar_meta exit contract 0/2/1; the nightly chain continues on 2
  with avisos (precedent workflows.py:447). Live run still pending the operator's yes.
- 22-sep: feature doc created. Branch feat/app-web at e46d8f1.
- Audit correction: H7 overstated. Sep ad_ids are clean; only the latent `s_id` path remains (T2).
- T1b DONE (commit 4ac57dc): `bajar_meta_insights.py` exit contract is now 0/2/1 (all OK / partial /
  all failed), documented in its docstring and in `.claude/skills/recopilar-lucidsales/SKILL.md`.
  `ejecutar_ciclo_nocturno` (app/backend/vitalcom_app/workflows.py) treats a `ciclo.bajar_meta` step
  with codigo_salida==2 as an `aviso` and keeps going to gen_decisiones/flujo/gen_app; codigo_salida==1
  still stops the chain. New backend test `app/backend/tests/test_ciclo_nocturno.py` (2 cases).
  Checks: `python Ads/_TOOLS/test_bajar_meta_insights.py` -> 9 tests OK; `pytest Ads/_TOOLS` -> 28
  files OK; backend `uv run pytest --ignore=tests/test_meta.py` -> 136 passed; flujo --validar OK;
  guia madre OK.
- T2 DONE (commit 2fb738f): `s_id()` in `ingerir_lucidsales.py` never emits scientific notation and
  never reconstructs a wrong id — int/str keep exact digits (a str already in scientific notation ->
  ""), a float is `str(int(v))` only when integral and <= 2**53, otherwise "". Drops are counted in
  `ids_perdidos()` and printed in the run summary. Audited every ad_id/_FACT_VENTAS.csv reader in the
  ingestion path: all use `csv.DictReader` or pandas `dtype=str` already except `registros_xlsx()`,
  which deliberately keeps pandas' float inference for adId/accountTitle (LucidSales' xlsx stores
  those cells as NUMBER, so the precision is already lost in Excel/openpyxl before Python runs;
  forcing dtype=str there would silently stringify the already-wrong float instead of letting
  `s_id()` recognize it as unrecoverable). `ingerir_meta.py` has no ad_id formatter of its own (keys
  by name signature). New test `test_s_id_nunca_notacion_cientifica` in `test_ingerir_lucidsales.py`.
  Follow-up (22-sep): `ingestar_unificado.py` was retired — no caller in `app/`, `.claude/`, hooks or
  `warehouse/`, only a copy button in the static fallback; besides the naive ad_id formatter it
  deduplicated on 3 fields instead of the 6-field key and invented `mensajes` as 70% of link clicks.
  `enriquecer_adid.py` stays: diagnostic by default, hardcoded Jul-Aug map, no caller.
  Checks: `python Ads/_TOOLS/test_ingerir_lucidsales.py` -> 0 fallas; `pytest Ads/_TOOLS` -> 28
  files OK; flujo --validar OK; guia madre OK; `git status --short` clean except this doc.

- T1 live DRY-RUN (operator authorized, 22-sep): `bajar_meta_insights.py --fecha 2026-09-21 --dry-run`
  -> exit 2 (partial), nothing written (git status clean).
  - GTR 0: 2 ads. GTR 1: 9 ads. Both match the LucidSales ad counts of 20-sep (2 and 9-10).
  - GTR 3: 0 ads.
  - GTR 13: Meta error #200 "Ad account owner has NOT grant ads_management or ads_read permission".
    The System User token lacks access; the operator must assign GTR 13 to the System User
    (ads_read) in Business Manager.
  - GTR 7: 0 own ads AND 0 foreign ads, although LucidSales shows GTR7 spend on 20-sep (NUSAVA 8 ads,
    TINNIDROP 10). Suspected a silent empty result.
  - RESOLVED by a second authorized dry-run, `--fecha 2026-09-20 --dry-run`: exit 2. GTR 7: 18 ads,
    matching LucidSales exactly (8 + 10). GTR 0: 2. GTR 1: 9. The API is not failing silently; the
    21-sep zero is real (no GTR7 delivery that day, or Meta not consolidated yet).
  - Remaining for T1: (a) the operator grants GTR 13 to the System User (ads_read) in Business
    Manager; (b) after the ff-merge, one real run in SISTEMA (without --dry-run) for the missing days,
    then check max ventana_fin >= today-2.

- T3 DONE, two commits.
  - Commit A (e139af8): `gen_plan.py` `validar_plan_fase1` now blocks any F1 conjunto whose
    `formato` != IMAGEN (operator decision 22-sep-2026). `hook_csv.py` adds
    `atribucion_conjuntos_invalida()`: a new `_DIM_CONJUNTOS.csv` row (fecha_alta >= 2026-09-23,
    named constant `CUTOFF_ATRIBUCION_CONJUNTOS`, non-HEREDADO `origen_angulo`) must carry
    `formato` in {IMAGEN, VIDEO}, a classified `concepto_key`, and IMAGEN when `fase == FASE1`;
    wired into `main()` next to the generic CSV shape check. `gen_publicacion.py`'s F1 path was
    audited (lines ~570-606): it already defaults `formato` to IMAGEN and resolves creatives by
    file extension, no hidden video-only assumption — no change needed there.
    New/extended tests: `test_gen_plan.py` (+2 cases: F1 plan with a VIDEO conjunto fails, all
    IMAGEN passes) and new `test_hook_csv.py` (6 cases: post-cutoff SIN_CLASIFICAR flagged,
    pre-cutoff not flagged, HEREDADO not flagged regardless of date, FASE1+VIDEO flagged,
    post-cutoff complete row not flagged, unrelated CSV ignored).
    Report requested by T3: `gen_plan.py --validar` against the real PRODUCTOS/*/_PLAN.json now
    fails for 3 already-existing F1 plans that still have VIDEO conjuntos —
    `PRODUCTOS/CLEARSTEM/_PLAN.json` (conjuntos 2,3,4,5), `PRODUCTOS/NusavaB12/_PLAN.json`
    (conjuntos 1,2), `PRODUCTOS/TINNIDROP/_PLAN.json` (conjuntos 1,2,4,6) — these plans were not
    edited (out of scope: they predate the decision). `PRODUCTOS/OVULOS_PURITY/_PLAN.json` (6
    conjuntos, already IMAGEN) still validates OK. `atribucion_conjuntos_invalida()` run against
    the real `PRODUCTOS/_DIM_CONJUNTOS.csv`: 0 flagged rows (every `fecha_alta` in that file is
    before the 2026-09-23 cutoff).
  - Commit B (see hash below): doctrine. `CLAUDE.md` phase table: F1 line now says concept AND
    format fixed (IMAGEN) + a bullet on competitor videos feeding the angle vs. video-as-F2-concept
    (owner: `gen_plan.py --validar`). `DOCTRINA/FLUJO.json`: removed
    `Ads/_TOOLS/lavar_videos.sh` from `F1.paquete.secuencia` (F1 no longer washes video); added it
    to `F2.conceptos.secuencia` (runs when `etapa-9` assigns a VIDEO concept, before
    `etapa-render`). `VISTAS/_MANIFIESTO.json`'s `nodo.F1.paquete.pasos` updated to match (a repo
    test, `test_gen_app.py`, asserts the manifest's flattened steps equal `FLUJO.json`'s
    `secuencia` for that node — it failed until this was fixed, now green).
    `.claude/skills/fase-1-angulos/SKILL.md`: removed PASO 1.5 (video washing) — it's a skill file,
    not an ETAPA-*.md agent, so this is a real edit, not just a pointer; corrected the two
    resulting false statements (ad-imagen only for "vírgenes" angles -> for all 6; etapa-6 marking
    VIDEO/IMAGEN per conjunto -> always IMAGEN). `.claude/skills/fase-2-conceptos/SKILL.md`: added
    the washing step (conditional on a VIDEO concept) to its sequence.
    Pointer-level notes (1-3 lines, no prose pruning) added to `.claude/agents/ETAPA-0.md` (videos
    are the angle source, not the F1 creative), `.claude/agents/ETAPA-4.md` (image ad for all 6
    angles, not only virgins), `.claude/agents/ETAPA-6.md` (F1 plans `formato: IMAGEN`, replaces
    the old "mark VIDEO/IMAGEN per conjunto" and "confound of format" rules going forward).
    Doctrine statements found false by grep and corrected with a pointer:
    `DOCTRINA/PLANTILLAS_ADS.md` line ~8 ("angles with video don't need an ad-image in F1") and its
    "confound de formato" reading note (~line 357); `DOCTRINA/GUIA_MADRE_PARAMETRIZADA.md`
    `DIFERENCIA_ANGULO_VS_FORMATO` row (was ambiguous about format also being fixed in F1).
    `DOCTRINA/CALENDARIO_ESCALADO.md` has no video mentions (checked, nothing to correct).
  - Checks (all green, run in this order after both commits): `python Ads/_TOOLS/test_gen_plan.py`
    and `python Ads/_TOOLS/test_hook_csv.py` (script-style, 0 fallas each); `python -m pytest
    Ads/_TOOLS -q -p no:cacheprovider` -> 29 passed; `python Ads/_TOOLS/flujo.py --validar` -> OK,
    3 fases, 20 nodos; `python Ads/_TOOLS/verificar_guia_madre.py` -> sin fallas (88 variables);
    `python Ads/_TOOLS/gen_grafo.py` -> ninguna ruta muerta, ningún .md/.csv sin consumidor
    (baseline file restored with `git checkout --` right after, per the hard rule); `git status
    --short` clean except this doc.

  - 22-sep, after the operator granted GTR 13 to the System User: `--fecha 2026-09-20 --dry-run`
    -> exit 0. All 5 accounts read. GTR 13: 14 ads, matching LucidSales (14). Remaining for T1: the
    ff-merge, then the real backfill 06..21-sep in SISTEMA.

- T1 CLOSED 22-sep: operator ff-merged (e46d8f1..8cd1a4d). Real backfill in SISTEMA, 06..21-sep day by day:
  exit 0 all 16 days; _FACT_ENTREGA 637->1004, _FACT_ENTREGA_ANUNCIO 177->887; max ventana_fin: CLEARSTEM
  09-21, TINNIDROP 09-21, NUSAVA 09-20 (>= today-2). Data commit in SISTEMA.
  NEW FINDING (inferred): Meta spend exceeds LucidSales spend 06-20 sep by +6.8% TINNIDROP, +8.1% NUSAVA,
  +11.6% CLEARSTEM. decidir.py uses LucidSales spend, so its CPAs may be understated by that much.
  Timezone day-boundary not yet ruled out. 128/710 new ad rows have no angulo_key (ads missing from
  _DIM_CONJUNTOS). Both are follow-ups for the operator, not part of P1.

## Next step
Feature complete (T1-T3). Follow-ups: the spend gap Meta vs LucidSales; 128 ads without angulo_key;
regenerate the OVULOS_PURITY F1 plan all-IMAGEN when F1.paquete runs.
