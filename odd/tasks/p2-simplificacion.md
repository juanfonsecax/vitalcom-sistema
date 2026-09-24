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
- [x] T1 — `PRODUCTOS/_DIM_FANPAGES.csv` (10 pages: identity, tone, age orientation, page_id,
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
- 2026-09-23: T1 writer pass done (data + absorb + delete + consumers + evals). NOT yet re-run
  against real Claude on frozen CLEARSTEM inputs — that step is the parent's, per Config below.
  Evidence:
  - `PRODUCTOS/_DIM_FANPAGES.csv` created (real csv.DictWriter, invariant 11): 10 rows,
    columns `pagina_num,pagina_nombre,identidad,rol,tono,logica,edad_orientacion,page_id,productos_nicho`.
    Values copied verbatim from the deleted `ETAPA-FANPAGE.md` (no doctrine reworded).
  - `.claude/agents/ETAPA-2.md` absorbed the judgment: new §ASIGNACIÓN DE FANPAGE with reglas
    F1-F5 verbatim, reading `PRODUCTOS/_DIM_FANPAGES.csv` instead of an embedded list, emitting the
    same `<pagina_asignada>` Formato A/Formato B block ETAPA-4/5/6 already consume.
  - `.claude/agents/ETAPA-FANPAGE.md` deleted.
  - Consumers updated: `CLAUDE.md` (16 etapas, owner-map rows), `DOCTRINA/FLUJO.json`
    (secuencia + "como" + page_id "dueno"), `VISTAS/_MANIFIESTO.json` (pasos: etapa-2 alone, no
    longer parallel), `.claude/skills/fase-1-angulos/SKILL.md` (PASO 3 rewritten, checklist),
    `.claude/skills/generar-conceptos/SKILL.md`, `DOCTRINA/PLANTILLAS_ADS.md`,
    `DOCTRINA/PLANTILLAS_INFOGRAFIAS.md`, `DOCTRINA/ETAPA-RECOLECCION.md`, `README.md`,
    `Ads/_TOOLS/{cargar_page_id.py,gen_lanzador.py,gen_publicacion.py,verificar_producto.py,
    LAVADO.md,test_gen_app.py}`, `app/backend/tests/{test_pasos.py,test_fase1_api.py}`,
    `db/tables.py` (+ regenerated `db/schema.sql`). Generated files (`VISTAS/APP.html`,
    `PRODUCTOS/_FLUJO.json`, `_LANZADOR.json`, `VISTAS/_ESTADO.json`) regenerated via
    `python Ads/_TOOLS/gen_app.py --todo`, never hand-edited. `_ROADMAP/`, `_OPERADOR/` and
    historical `PRODUCTOS/<P>/*.txt` / `_AUDITORIAS/` left untouched.
  - Evals: `evals/asserts/etapa-fanpage.py` retargeted to cross-check against
    `PRODUCTOS/_DIM_FANPAGES.csv` (was: doctrina text of the now-deleted agent) — assert not
    weakened, same catalog, same fixture. Documented in `evals/README.md` under a new
    "Retargeting T1" section and in `promptfooconfig.yaml`'s comment for that test.
  - Verification run (see final report to orchestrator for full command output):
    `python -m pytest Ads/_TOOLS -q -p no:cacheprovider` → 41/41 passed.
    `python evals/run_baseline.py` → TOTAL=30 PASS=26 FALLO-CONOCIDO=4 FAIL=0 (unchanged).
    `python Ads/_TOOLS/gen_grafo.py --comparar` → no orphaned .md/.csv; `fase-1-angulos` cost
    -21907 tok (ETAPA-FANPAGE.md no longer inherited); 16 agentes (was 17).
    `python Ads/_TOOLS/flujo.py --todo` → same 5 products, same nodes/gates (only cosmetic
    "como"/secuencia text changed on F1.paquete).
    `python Ads/_TOOLS/verificar_guia_madre.py` → exit 0, same single pre-existing finding
    (`exploracion_n_angulos`), unrelated to this change.
    `uv run pytest tests/test_pasos.py tests/test_fase1_api.py` (app/backend) → 15/15 passed.
  - NOT done (belongs to the parent orchestrator per Config: "Re-running an etapa is done by the
    parent orchestrator"): the actual CLEARSTEM re-run of `etapa-2` against real Claude to confirm
    it reproduces the same page as `evals/fixtures/etapa-fanpage/CLEARSTEM.txt`
    ("Página 4 ✨ Belleza & Piel — Astrid García"). See the writer's final report for the exact
    frozen-inputs package to use for that re-run.

- 2026-09-23: T1 CLOSED by parent. Protocol re-run: etapa-2 (session model) on CLEARSTEM frozen
  inputs (evals/fixtures/etapa-1/CLEARSTEM.txt, 2_DATA_PRODUCTO.txt sections 1 and 3,
  _DIM_FANPAGES.csv, saturacion DESCONOCIDA, no WebSearch) assigned Página 4 Belleza & Piel,
  identical to the old etapa-fanpage fixture. Output kept in
  evals/reruns/2026-09-23_etapa-2_CLEARSTEM_p2-T1.txt (6 fichas + pagina_asignada; the parent
  joined the tone bullets into one line when transcribing; preface/summary table omitted).
  etapa-2 assert PASS (6 fichas, 19 conciencia markers). Found the retargeted etapa-fanpage assert
  was weak (any catalog name anywhere passed: it matched 'Salud Hormonal Femenina', cited only to
  be discarded). Strengthened: parses the assigning line and checks number+name against the CSV.
  Rerun and fixture PASS (#4); wrong number and missing assignment FAIL. Baseline 30/26/4/0,
  test_evals_baseline 6 passed.

## Next step
T2 (split god nodes), delegated writer.
