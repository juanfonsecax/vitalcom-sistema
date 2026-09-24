# P2 — Simplificación (platform plan, gate 2 of 6)

## Objective
Fewer pieces with the same result: fold deterministic data out of prompts, split doctrine
files so each etapa reads only its section, and fuse etapa-7 + etapa-8.

## Why
- Token cost per phase measured by `gen_grafo.py`: 268k (ciclo-diario) to 446k (fase-2).
- These tokens become money when the platform moves to API-key billing (agency/SaaS).
- Fewer agents = fewer handoffs that can break.

## Scope (authorized 2026-09-23: operator "arranca con el P2")
- T1 etapa-fanpage -> data table + selection absorbed by etapa-2.
- T2 split "god nodes" (`DOCTRINA/ESCALADO_PLAYBOOK.md`, `DOCTRINA/PLANTILLAS_ADS.md`,
  `CLAUDE.md`) so each consumer reads only its section. Doctrine text unchanged, only cut.
- T3 fuse etapa-7 + etapa-8 into one judgment etapa; the numbers become a deterministic
  table printed by code (interim screen until P4 UI), never prose.
- Out of scope: etapa-3 (no real F3 output yet — pruning it saves zero tokens and has no eval),
  any doctrine change.

## Gate for every prune (evals/README.md "Protocolo de poda")
The baseline asserts run on FROZEN fixtures, so they alone do not prove a pruned prompt still
works. Each prune must also: re-run the changed etapa on the same frozen inputs that produced
its fixture, freeze the new output as a candidate fixture, and pass the same assert. A new
undocumented failure reverts the prune; asserts are never weakened. Plus
`python Ads/_TOOLS/gen_grafo.py --comparar` before/after for the token delta.

## Tasks
- [ ] T1 — `PRODUCTOS/_DIM_FANPAGES.csv` (10 pages: identity, tone, age orientation, page_id,
  niche products) + etapa-2 chooses `pagina_asignada` with rules F1-F5; remove
  `.claude/agents/ETAPA-FANPAGE.md`; update every consumer (FLUJO.json, skills, CLAUDE.md
  etapa list, gen_publicacion/gen_lanzador/verificar_producto, app tests). Route: delegated
  writer (cross-cutting, 10+ files). Check: etapa-2 re-run on CLEARSTEM frozen inputs picks
  the same page as `evals/fixtures/etapa-fanpage/CLEARSTEM.txt`; full test suite + evals green.
- [ ] T2 — Split god nodes by section. Route: delegated writer. Check: gen_grafo --comparar
  shows fewer inherited tokens; re-run of affected etapas with baselines passes.
- [ ] T3 — Fuse etapa-7 + etapa-8. Route: delegated writer. Check: re-run on the frozen
  2026-09-08 audit inputs passes both etapa-7 and etapa-8 asserts.

## Config
- TDD: off (default). RDD: off. Work-unit commits on `feat/p2-simplificacion`.
- Re-running an etapa is done by the parent orchestrator (subagents cannot spawn subagents).

## Progress
- 2026-09-23: P1 fast-forward merged into `feat/optimizacion-continua-perfil-angulos` (2e7ef15).
  Branch `feat/p2-simplificacion` created.

## Next step
T1 (delegated writer).
