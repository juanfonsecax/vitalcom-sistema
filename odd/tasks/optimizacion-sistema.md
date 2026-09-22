# Feature: optimizacion-sistema

## Objective
Apply the 21-sep-2026 system audit (Opus auditor session) to SISTEMA: remove dead weight, fix stale or
wrong doctrine, move archaeology out of hot context, turn prose-only rules into code or label them, and
close the one contract gap the app needs. The operator authorized executing the whole backlog in one run
(22-sep-2026); only the items under "Needs the operator" stop for a yes/no.

## Why
CLAUDE.md is ~7.3K tokens loaded in every session AND every one of the 17 subagents, repeats numbers
already owned by CSVs (not covered by any gate) and contains two wrong statements. Doctrine files carry
dated anecdotes next to rules. Two scripts are orphans. The app cannot show a sales progress bar because
the engine does not emit the two numbers.

## Where work happens (same pipeline as vista-por-que)
- Write and commit ONLY in worktree SISTEMA-app (branch feat/app-web). Read real data from ../SISTEMA.
- Delivery: operator runs `git merge --ff-only feat/app-web` in SISTEMA. If SISTEMA has new commits,
  first `git merge feat/optimizacion-continua-perfil-angulos` inside SISTEMA-app, then ff.
- Never edit data CSVs (_FACT_*, _DECISIONES.json, _ESTADO_*, VISTAS/*.html) in SISTEMA-app: they are
  modified live in SISTEMA and would block the ff. Engine code, doctrine .md, parameters only.
- One Conventional Commit per task, tests/docs with the change, no AI attribution lines.

## Constraints
- Do NOT prune `.claude/agents/ETAPA-*.md` prose. Decision 10-sep-2026: output evals must be frozen
  before pruning agent prompts (deterministic tests do not prove a pruned prompt behaves the same).
  Only pointer-level edits there (T4).
- Rules that are LIVE in code stay exactly as they are (verified 21-sep): 6 angles F1, 1-1-5 ABO F2,
  same budget per adset, 2-of-2 to F3, 4 AM, age band (bandas_edad.py), 1x BE tolerance,
  3-day F2, CAMBIO_BOT gate.
- Gates that must stay green after every task: `python Ads/_TOOLS/test_flujo.py`,
  `python Ads/_TOOLS/test_decidir.py`, `python Ads/_TOOLS/flujo.py --validar`,
  `python Ads/_TOOLS/verificar_guia_madre.py`, `python Ads/_TOOLS/gen_grafo.py` (orphans/dead routes;
  use `--comparar` for before/after token cost), app `uv run pytest` (~5 min) and `pnpm test`.
- Memory rule of the operator: the system is executed, not read — the current rule stays, the chronicle
  of the error goes to `_CONOCIMIENTO/POSTMORTEMS/`.

## Mode
- TDD: off (default). RDD: off. Delivery strategy: ask-on-risk.

## Tasks
- [x] T1 — CLAUDE.md slimming. Reuse branch `refactor/poda-tokens` (commit 0b403f8, already -41%,
      stories moved to `_CONOCIMIENTO/POSTMORTEMS/`): cherry-pick or re-apply onto feat/app-web,
      keeping lines added since (the "LA APP WEB" row). On top: header "Doce reglas" -> match the
      real count; invariant 2 must say what costear.py does (nearest row, tie -> upper row; owner
      ETAPA-1.md) or become a pointer; numbers owned by CSVs (ventana_dias 14, fatiga 3, F2 3 days,
      4 AM, 15-20 % closing, 8.6 %) become pointers to their owner. Evidence: gen_grafo --comparar.
- [x] T2 — Doctrine archaeology. In GUIA_MADRE_PARAMETRIZADA.md, ESCALADO_PLAYBOOK.md,
      DATA_PLAYBOOK.md, CALENDARIO_ESCALADO.md, PLANTILLAS_FLUJO_BOT.md, COPYWRITING_ADS.md: move dated
      incident narratives ("medido el...", "hasta el...", one-off anecdotes) to
      `_CONOCIMIENTO/POSTMORTEMS/`, leaving the rule and a one-line pointer. Keep the Recency Rule of
      ESCALADO_PLAYBOOK.md (it arbitrates conflicts). verificar_guia_madre.py must stay green (it parses
      GUIA_MADRE rows — do not alter row format).
- [ ] T3 — Prose-only rules. (a) Closing 15-20 %: label it in GUIA_MADRE as benchmark
      (not a gate) and, if `_DECISIONES.json` or an existing contract already carries closing rate
      per product, show "cierre actual vs meta" in the app product card; if no contract carries it,
      record the gap, do not compute it in the app. (b) Andromeda/compliance: canonical block stays
      in DOCTRINA/PLANTILLAS_ADS.md; ETAPA-4.md restatement becomes a pointer (pointer-level edit only).
- [ ] T4 — Orphans and dead surface. Move `Ads/_TOOLS/gen_clasificacion.py` and
      `Ads/_TOOLS/ingerir_creativos.py` to `_ARCHIVO/` (verify zero callers with rg first). Retire
      `VISTAS/PANEL.html` (pure redirect) and fix any reference. Review the 1-reference scripts
      (check_huella.py, gen_estructura.py, gen_manifiesto_fichas.py, gen_vocabulario.py,
      sincronizar_planes.py): archive only if their single reference is dead. gen_grafo clean.
- [ ] T5 — One command for engine tests: add minimal pytest config so `pytest Ads/_TOOLS` runs all
      test_*.py (they are script-style today; wrap or configure without rewriting assertions).
      Document the command in DOCTRINA/DATA_PLAYBOOK.md or the owner that lists gates.
- [ ] T6 — .gitignore `.atl/` (skill-registry cache). LucidSales ingest JSON stays tracked
      (16 already tracked = project convention).
- [ ] T7 — Engine emits progress numbers. In decidir.py/gen_ordenes.py emit `ventas_actual` and
      `ventas_necesarias` per order (the threshold decidir.py actually applied for that state), with a
      new case in test_decidir.py. Then the app renders the bar "N de M ventas" from those fields only
      (test_sin_aritmetica stays green). Also fix the glossary line for SEGUIR_MIDIENDO that says
      "El motor dice cuántas faltan" when the number is absent.
- [ ] T8 — Close-out: update CLAUDE.md "LA APP" rows so `app/` (web app) is the operator screen and
      VISTAS/APP.html is described as the generated fallback; mark
      `../HANDOFF_AUDITOR_ANTIGRAVITY.md` as superseded (Antigravity no longer used; add a first line,
      do not delete). Final full gate run, screenshots of the progress bar.

## Needs the operator (ask once, one line each, then continue with the rest)
- O1 — Remove worktrees already merged: SISTEMA-worktree-punto3, SISTEMA-worktree-punto4,
  SISTEMA-sim-h4 (its branch is already in feat/app-web), and `.claude/worktrees/poda-tokens` after T1.
- O2 — `chmod 600` on ~/.config/{lucidsales,meta,watch}/.env (operator runs it).
- O3 — Confirm the manifest action `nodo.F1.publicar` (habilitada:true) was authorized by him.
- O4 — Commit the pending live data in SISTEMA (CSVs, VISTAS, ingest JSON, audits moved to
  2026-08/, find-skills deletion) as `chore(data): ...` — give him the exact command.

## Out of scope (decided, not forgotten)
- Moving `_ARCHIVO/Bases` (9 MB course material) out of git: pack is 5.5 MB total, low value now.
- Untracking generated files (VISTAS/*.html, _ESTADO_FLUJO.csv...): the hooks and the app read them;
  revisit when the web app fully replaces VISTAS/APP.html.
- Pruning ETAPA-*.md prose: needs frozen evals first (see Constraints).

## Business next step (not code — tell the operator at the end)
flujo.py puts TINNIDROP and NUSAVA at node F2.etapa-11 (bot closing, the biggest lever). And TINNIDROP
has $32.61 spent on a non-doctrinal concept structure: verify against Meta (read-only) before anything.

## Progress / evidence
- 2026-09-22: plan written by the auditor session from the 21-sep audit.
- Baseline gates (22-sep, before T1): test_flujo 29/29, test_decidir 17/17, flujo --validar ok,
  verificar_guia_madre 0 failures, gen_grafo no orphans/dead routes, app pytest 161 passed, pnpm test 58 passed.
- T1 (route: delegated writer — rewrite of CLAUDE.md + postmortem snapshot): cherry-pick -n 0b403f8, two
  newer rows re-added as pointers; invariant 2 now states costear.py `elegir_fila()` (nearest row, tie ->
  upper); invariant 7 points the hour to `_PARAMETROS_PUBLICACION.csv`; header already count-free.
  gen_grafo --comparar: CLAUDE.md 8180 -> 4829 tok, cold start 11296 -> 7945 tok. All gates green
  (29/29, 17/17, validar ok, guia 0 failures, pytest 161, pnpm 58).
- T2 (route: delegated writer — 6 doctrine docs): stories moved to `_CONOCIMIENTO/POSTMORTEMS/*_historias.md`
  from GUIA_MADRE (6 rows, +28 tok: pointers as long as the stories), ESCALADO_PLAYBOOK (-132 tok) and
  DATA_PLAYBOOK (-304 tok). CALENDARIO_ESCALADO, PLANTILLAS_FLUJO_BOT and COPYWRITING_ADS left intact: their
  dated content is mentor citations or evidence tables the rules derive from, or literal bot template text.
  Gates green: guia 0 failures, 29/29, 17/17, validar ok, gen_grafo clean, pytest 161, pnpm 58.

## Next step
T3.
