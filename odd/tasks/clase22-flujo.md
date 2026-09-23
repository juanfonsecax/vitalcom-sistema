# Feature: clase22-flujo — Clase 22 (flow optimization) rules made executable

## Objective
Turn the two Clase 22 rules that the system only states in prose into rules the code enforces:
the avatar's awareness level drives how the dedicated bot flow opens, and the flow declares
6-8 value propositions.

## Problem
Audit 23-sep-2026 (engram `auditoria/clase-22-flujo`): Clase 22 was already ingested (F1·C22,
MATRIZ M-D13 / C-06). The system uses the 10 research aspects well for the AD. Two rules that act
on the POST-CLICK flow are still prose only:
- `nivel_conciencia` is measured per conjunto (`_DIM_CONJUNTOS.csv`, 171/173 filled) but
  `gen_flujo_bot.py` never reads it; ETAPA-5 Paso 3 (L106-113) decides the opening by hand.
- The "6-8 value propositions" rule (PLANTILLAS_FLUJO_BOT.md L175, ETAPA-5 L83) is not counted
  anywhere.

## Why
The close rate (messages -> sales) varies 2.6x across angles in CLEARSTEM (7.9%-20.8%).
Congruence between the winning angle's avatar and the dedicated flow is the lever Clase 22
stresses.

## Scope
- IN: dedicated flow (winning angle known). F1 keeps ONE umbrella bot (operator decision
  23-sep: never two bots in F1, it splits the metrics).
- OUT: flow A/B test (deferred, see Backlog); ad-side changes; income as a variable (rejected:
  price comes from costeo); picking angles by clicks/CPM (rejected by data).

## Constraints
- Code and doctrine are written only in SISTEMA-app (branch feat/app-web). Data is changed only in
  SISTEMA, after the operator's ff-merge.
- CSVs are edited with a real CSV writer. `{{var}}` blocks when missing; `>>` lines are
  instructions and are never pasted.
- Existing live products (CLEARSTEM, TINNIDROP) must not stop rendering because of a
  not-yet-declared new field: missing -> warning/PENDIENTE; declared but invalid -> block.
- TDD: off (default, same as g07). Tests ship with every change.
  Runner: `python -m pytest Ads/_TOOLS -q -p no:cacheprovider`.
- RDD: off. Delivery strategy: ask-on-risk. No push/PR without the operator.

## Tasks
- [x] T1 — Awareness-driven opening. For a dedicated flow, `gen_flujo_bot.py` resolves the winning
  angle's `nivel_conciencia` from `_DIM_CONJUNTOS.csv` (normalized with the `_DIM_VOCABULARIO.csv`
  aliases) and renders a `>>` instruction that states the opening rule for that level
  (1 educate the cause first · 2 pain + "it has a solution" · 3A reduce friction first ·
  3B anchor the offer). Missing, ambiguous or conflicting level -> block with the reason. Umbrella
  flow -> no level instruction. Doctrine: PLANTILLAS_FLUJO_BOT.md + ETAPA-5 Paso 3 point to the
  generator as the owner. Route: delegated (2+ non-trivial files).
- [x] T2 — Value propositions counted. The flow's value propositions exist as text that the code
  reads (formula problem -> what the product does -> result). Fewer than 6 declared -> block;
  none declared yet -> warning (not a block) so live products keep rendering. Doctrine updated
  (template + ETAPA-5 + ETAPA-11 checklist). Route: delegated (same writer).
- [ ] T3 — Prefilled WhatsApp message (product name + MSPAS registration). BLOCKED on an
  operator fact: whether LucidBot routes the chat by the text of the first customer message. The
  Meta MCP `ads_create_creative` has no field for it, so it would be a manual step.

## Acceptance criteria
- T1: a test with a dedicated fixture shows each level's instruction; missing or conflicting
  level blocks; the umbrella flow renders without it; CLEARSTEM/TINNIDROP still pass.
- T2: tests show <6 -> block, 6-8 -> pass, undeclared -> warning only.
- Full suite green.

## Backlog (deferred, not authorized)
- Flow A/B (light vs dense, C-06), run only after F1 is approved, inside F2. C-06 in MATRIZ still
  says T01 decides it, but T01 was CERRADO_SIN_LANZAR on 06-sep.

## Progress
- 23-sep: audit done, feature doc created. Next: T1+T2 delegated writer.
- 23-sep: T1 delivered by delegated writer (route: delegated, trigger: 2+ non-trivial files —
  gen_flujo_bot.py + test_gen_flujo_bot.py + PLANTILLAS_FLUJO_BOT.md + ETAPA-5.md).
  Commit `b734df7` — feat(gen_flujo_bot): derive the flow opening from the winning angle's
  awareness level.
  - Design note: "dedicated flow" has no explicit flag in the data. Defined as
    `es_flujo_dedicado(pk)` = the product has any `_DIM_CONJUNTOS.csv` row with `fase != FASE1`
    (i.e. it already graduated past F1 testing). CLEARSTEM/TINNIDROP both qualify (FASE2_ESCALA/
    FASE3 rows exist). The umbrella (F1-only) path renders no instruction and does not block.
  - `NIVELES_APERTURA` dict lives in `gen_flujo_bot.py`, not in `_DIM_VOCABULARIO.csv`'s
    `definicion` column: that column is owned by ETAPA-2 and describes the AD-facing rule; the
    bot's opening instruction is a distinct, post-click text, so reusing it would misattribute
    ownership.
  - Verification: `python -m pytest Ads/_TOOLS -q -p no:cacheprovider` — 40 passed before and
    after (each `test_*.py` runs as one script-style pytest item per `Ads/_TOOLS/conftest.py`,
    so the item count doesn't grow with new `def test_*` functions inside the file;
    `python Ads/_TOOLS/test_gen_flujo_bot.py` directly showed all 21 checks green, incl. the 8
    new ones). `python Ads/_TOOLS/gen_flujo_bot.py --validar` — 2/5 (unchanged: CLEARSTEM/
    TINNIDROP pass, the other 3 block on pre-existing unrelated missing data).
    `gen_flujo_bot.py CLEARSTEM --json` / `TINNIDROP --json` — both `ok: true`, `faltan: []`.
    `python Ads/_TOOLS/verificar_guia_madre.py` — exit 0, "Sin fallas".
- 23-sep: T2 delivered by delegated writer (route: delegated, same writer). Commit `8c20ed3` —
  feat(gen_flujo_bot): count declared value propositions, block under 6.
  - Design note: `<<BLOQUE:x>>` markers are never persisted back to a re-readable file —
    `FLUJO_LUCIDBOT.md` is fully regenerated from CSV+template every run, and etapa-5's bloques
    (tools: Read only) are pasted straight into LucidBot, not saved in-repo. So the code has no
    channel to read the propositions etapa-5 actually wrote, and a new `PRODUCTOS/*.csv` column
    was explicitly out of scope. Least-invasive alternative: an optional `--propuestas ARCHIVO`
    CLI flag (one proposition per line) that `una()`/`una_json()` validate the same way as
    `prohibiciones()` — under 6 blocks, 6-20 passes, over 20 warns, and omitting the flag leaves
    it PENDIENTE (warning only, never a block), so CLEARSTEM/TINNIDROP keep rendering unchanged.
  - Verification: `python -m pytest Ads/_TOOLS -q -p no:cacheprovider` — 40 passed before and
    after. `python Ads/_TOOLS/test_gen_flujo_bot.py` — all checks green (6 new: <6 blocks,
    6/7/8 pass, >20 warns, undeclared warns only, CLEARSTEM/TINNIDROP unaffected).
    `gen_flujo_bot.py --validar` — 2/5, unchanged. `gen_flujo_bot.py CLEARSTEM --json` — `ok:
    true`, new aviso "propuestas_valor no declaradas todavia... (PENDIENTE, no bloquea)".
    `gen_flujo_bot.py CLEARSTEM --copy --propuestas <5-line file>` — correctly RECHAZADO
    ("5 declarada(s), van 6-8"). `verificar_guia_madre.py` — exit 0, "Sin fallas".
- T3 remains BLOCKED on the operator fact noted above (out of this writer's scope).
