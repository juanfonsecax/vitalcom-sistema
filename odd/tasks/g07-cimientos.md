# Feature: g07-cimientos

## Objective
Close every open item of the final pre-SaaS audit (22-sep-2026, report
https://claude.ai/artifact/JQQuer5n1skD1u1K9MfJY9, plan P4-P12) plus the findings of the g06 Meta
backfill. The operator's standard (22-sep): fix from the foundations, no temporary patches. The
system must work organically enough to become a SaaS.

## Why (new evidence from g06, 22-sep)
- LucidSales spend is sometimes frozen mid-day. On 06, 14, 15, 16 and 20-sep every ad carries
  0.65-0.75 of Meta spend. On 07-11 and 17-19 the ratio is 1.000 to the cent. It does not depend on
  our download time (06/07/08 were downloaded together and only 06 is off). Ingestion is append-only
  with dedupe, so a partial day is never corrected.
- `bajar_meta_insights.py:214` hardcodes `mensajes: 0` and relies on a doctrine that DERIVES messages
  from clicks. Messages are estimated, not measured. The 06-21 backfill rows carry mensajes=0.
- `_FACT_ENTREGA_ANUNCIO.csv` has no `ad_id`: Meta delivery and LucidSales sales join by ad NAME,
  which renames break.
- 128/710 backfilled ad rows have no `angulo_key` (ads missing from `_DIM_CONJUNTOS`).

## Data ownership decision (derived from existing doctrine, taken by the orchestrator)
CLAUDE.md and ETAPA-7 already say: sales truth = `_FACT_VENTAS.csv` (LucidSales); Meta = delivery.
Spend IS delivery, and Meta is what bills. Therefore:
- spend, impressions, clicks, messaging conversations -> Meta Graph API (`_FACT_ENTREGA*`);
- sales -> LucidSales (`_FACT_VENTAS`);
- joined by `ad_id` (day grain);
- both facts are UPSERTED over a settlement window (re-pull the last N days nightly and replace
  by key), never append-only.
LucidSales spend stays only as a fallback for days without Meta coverage (before 2026-09-06).

## Where work happens
- Code and doctrine: worktree SISTEMA-app (branch feat/app-web). The operator ff-merges into SISTEMA.
  If SISTEMA has data commits, first `git merge --ff-only feat/optimizacion-continua-perfil-angulos`
  inside SISTEMA-app.
- Data (re-pulls, backfills): only in SISTEMA, after the merge, as its own `chore(data)` commit.
- Never edit data CSVs in SISTEMA-app. One Conventional Commit per work unit, tests and docs with
  it, no AI attribution. Delegated writers never spawn task chips: out-of-scope findings are
  reported in text.

## Constraints
- Do not prune `.claude/agents/ETAPA-*.md` prose until evals exist (T11). Pointer-level edits only.
- No Meta writes. Meta reads (Graph API ads_read token) only for ingestion, already authorized for
  P1. New kinds of calls are announced first.
- The operator's terminal is PowerShell 5.1: commands for them go one per line, without `&&`.
- Gates green after every task: `python -m pytest Ads/_TOOLS -q -p no:cacheprovider` (counts
  script FILES), `python Ads/_TOOLS/flujo.py --validar`, `python Ads/_TOOLS/verificar_guia_madre.py`,
  `python Ads/_TOOLS/gen_grafo.py` (restore `_LINEA_BASE_SISTEMA.json` after), backend
  `cd app/backend; uv run pytest -q --ignore=tests/test_meta.py`.

## Mode
- TDD: off (default). Tests ship with every change. RDD: off. Delivery strategy: ask-on-risk.

## Tasks (dependency order)
- [ ] T1 Data layer: Meta facts carry `ad_id` and real messaging conversations (Graph `actions`,
      messaging_conversation_started). Ingestion of Meta and LucidSales becomes an idempotent UPSERT
      over a settlement window (nightly re-pull of D-1..D-3, replace rows by key), not append-only.
      Then re-pull 06-21 in SISTEMA. Check: messages > 0 and close to LucidSales `mensajes`; ad_id
      filled; re-running a day changes nothing (idempotent); partial days get corrected.
- [ ] T2 Spend source of truth: every CPA consumer (decidir.py, flujo.py winner gates, finance
      reports, dbt models) takes spend from Meta facts joined by ad_id, with the LucidSales fallback
      before 2026-09-06. One helper, not N copies. Doctrine owner rows updated (CLAUDE.md map,
      DATA_PLAYBOOK). Check: tests; before/after of `_DECISIONES.json` explained.
- [ ] T3 Unknown ads: ingestion lists ads without a `_DIM_CONJUNTOS` row as a visible pending item
      (not silently dropped or left without angle); the path to register them is declared.
- [ ] T4 (P4) Bot order: F2.etapa-11 becomes a congruence diagnosis (no rewrite gate); the F3 entry
      requires a CAMBIO_BOT dated after the winning concept; `_ev_eventos` supports "after X".
      Doctrine: CLAUDE.md pointer + PLANTILLAS_FLUJO_BOT.md.
- [ ] T5 (P5) Gates are locks: `registrar_evento.py` (LANZAMIENTO) and `gen_publicacion.py --fase N`
      refuse when the phase gate is unmet, unless `--excepcion "reason"` records an EXCEPCION event.
- [ ] T6 (P7) Compute and write are separate: flujo.py, decidir.py, gen_grafo.py get a read-only mode.
      A "read" never writes tracked files.
- [ ] T7 (P8) Tests: costear.py, registrar_evento.py, decidir.py ESCALAR_MODERADO and comparar_cierre.
- [ ] T8 (P10) Hygiene: iniciar.bat refuses an ambiguous base; verificar_publicacion requires
      effective_status=PAUSED; invariant 7 requires exactly the next day; etapa-3 status resolved.
- [ ] T9 (P9) Folders: classes out of the repo, live backups to a gitignored `_RESPALDOS/`, dead
      `_ARCHIVO/` removed, references fixed.
- [ ] T10 (P6) Voice of customer as data: `_VOZ_CLIENTE.csv` + `verificar_voz.py` (re-fetches the
      URL, checks the quote) + the etapa-1b output contract + angle cards cite voz_id.
- [ ] T11 (P11) Frozen evals baseline (promptfoo) over saved real outputs, per stage.
- [ ] T12 (P12) Exploration of new angles while scaling (F3.exploracion). DECIDED by the operator
      22-sep: a fixed mini-F1 of 3 untested angles at the F1 per-adset budget (2.99 USD/day each,
      ~9 USD/day), measured by sale like F1, all-IMAGEN. It starts when the F3 campaign is profitable
      per decidir.py. Parameters live in `_PARAMETROS_PUBLICACION.csv` / `_PARAMETROS_DECISION.csv`
      (new rows, written with a real CSV writer in SISTEMA as a data commit).

## Progress / evidence
- 22-sep: doc created. Base: SISTEMA-app at f268f32.
- 22-sep: T1 implemented (not checked — parent closes it after the live re-pull in SISTEMA).
  - `ad_id` + real messaging: `bajar_meta_insights.py` now requests `ad_id` and `actions` from
    the Graph API (FIELDS). `mensajes_de()` reads action_type
    `onsite_conversion.messaging_conversation_started_7d`, falling back to the variant without
    `_7d` if that one is absent; if neither appears, mensajes=0 (documented in the module
    docstring — no longer derived from clicks on this path). `ad_id` is carried into the ad-level
    row. `COLS_AD` (owner: `ingerir_meta.py`) gained an `ad_id` column, inserted right after
    `anuncio`. The xlsx path (`ingerir_meta.py`, `mensajes = tasa_conv_whatsapp x link_clicks`)
    is untouched — it has no `actions` field to read from; its own docstring paragraph on that
    doctrine is intact. Found one other place deriving messages from clicks:
    `Ads/_TOOLS/ingestar_unificado.py:268` (`mensajes = clicks*0.7` fallback) — a separate,
    undocumented ingestion path (git history: restored by an unwind of an unapproved retirement)
    not referenced by CLAUDE.md's file-ownership map, `warehouse/`, or `app/backend`. Left
    untouched (out of T1 scope) and flagged here for the operator's attention.
  - Shared UPSERT helper: `Ads/_TOOLS/upsert_fact.py` (new). `upsert(path, cols, key, filas, bkdir)`
    reads and migrates the existing CSV to the current column set (`leer_migrado`, missing columns
    -> `""`), replaces rows whose natural key already exists, appends new ones, and rewrites the
    full file with a timestamped backup — same backup pattern as before. `key` accepts either a
    column-name tuple or a `fila -> tupla` callable (needed for "ad_id or firma when empty").
    `SETTLEMENT_WINDOW_DIAS = 3` lives here as the single named constant; both downloaders import
    it.
  - Natural keys (documented in code, at each call site):
    - Meta conjunto fact (`_FACT_ENTREGA.csv`): `(fuente, ventana_ini, ventana_fin, cuenta_id,
      campana, conjunto)`.
    - Meta anuncio fact (`_FACT_ENTREGA_ANUNCIO.csv`): `(fuente, ventana_ini, ventana_fin,
      cuenta_id, ad_id or firma or anuncio)` — `_clave_anuncio()` in `bajar_meta_insights.py`.
    - LucidSales ventas fact (`_FACT_VENTAS.csv`): `clave_natural()` in `ingerir_lucidsales.py`,
      the "AD" identity (sane ad_id) when present, else the "NOM" identity — same precedence
      `llaves()` already documented, but ONE key instead of "matches either of two" (dedupe ->
      upsert). `rol_ventana` travels inside the key, so a CONTROL row can never collide with (and
      therefore never replace) a BASE row of the same day, or vice versa — verified by a new test.
  - `bajar_meta_insights.py`: default (no args) now re-pulls `SETTLEMENT_WINDOW_DIAS` days ending
    yesterday, one Graph API call per day (`_rango_fechas`), upserting once at the end. `--fecha`
    keeps the single-day manual override; `--desde/--hasta` iterates a range day by day (the Graph
    API's ad-level insights don't aggregate cleanly over a multi-day window the way a single day
    does). Exit-code contract (T1b) generalized from "per account" to "per (date, account)
    attempt": 0 all OK, 2 partial, 1 all failed.
  - `bajar_lucidsales.py`: LucidSales' `meta/metrics` endpoint aggregates over the requested date
    range instead of returning one row per day, so a settlement re-pull can't be "one N-day
    request" — it has to be N separate 1-day requests (`procesar_ventana()` extracted and called
    once per day, `--forzar` implied). Default (no args) now issues `SETTLEMENT_WINDOW_DIAS`
    single-day requests ending yesterday. `--fecha`/`--hasta`/`--dias` (manual single-window pull,
    incl. the Monday `--dias 7` weekly control) are unchanged — verified by regression test.
  - `ingerir_lucidsales.py`: dedupe-by-either-of-two-keys (`llaves()`, append-only) replaced by
    `clave_natural()` + `upsert_fact.upsert()`. Within-run duplicate rows (same key across two
    files in one invocation) still collapse (last wins); a row matching a key already on disk now
    REPLACES it instead of being silently skipped. The `sin_dim`/`sin_clasificar` integrity gate
    and the multi-day-overlap guardrail are unchanged (still read the pre-upsert `existentes`
    snapshot).
  - `ingerir_meta.py`'s own `_FACT_ENTREGA_ANUNCIO.csv` writer (xlsx path) switched from a raw
    append to `upsert_fact.upsert()` too — not because its semantics needed to change (its rows
    are already deduped against disk before this point), but because a raw append with a *new*
    `COLS_AD` header against a file still holding the *old* header would misalign columns; routing
    through the shared helper's `leer_migrado()` makes that schema transition safe automatically.
  - `warehouse/models/staging/stg_entrega_anuncio.sql` and
    `warehouse/models/marts/fct_anuncio_dia.sql` now select/group by `ad_id` (passthrough only;
    T2 will do the actual join-by-ad_id work). `_models.yml` column tests weren't touched (they
    don't enumerate full column lists, so nothing there could break).
  - Doctrine: `.claude/skills/recopilar-lucidsales/SKILL.md` — settlement-window section added,
    the "sin argumentos trae AYER" lines updated for both downloaders, the "duplicados
    omitidos"/"anexa sin discutir" language corrected to reflect UPSERT. `DOCTRINA/DATA_PLAYBOOK.md`
    — pointer note under §3 (append-only -> settlement-window UPSERT) and a note under
    `_FACT_ENTREGA.csv` about the new `ad_id` column and where `mensajes` comes from per source.
  - Tests (script-style, `python Ads/_TOOLS/test_x.py`, tmp files only):
    `test_upsert_fact.py` (new — upsert/replace/idempotent/backward-compat-read/callable-key),
    `test_bajar_lucidsales.py` (new — settlement default is N single-day requests, `--dias 7`
    still one multi-day request, `--fecha` unaffected), extended `test_bajar_meta_insights.py`
    (actions parsing incl. `_7d` preference and fallback, ad_id carried, date-range iteration,
    settlement default, re-run idempotency) and `test_ingerir_lucidsales.py` (upsert replaces a
    partial day and is idempotent on re-run; CONTROL never replaces BASE and vice versa).
  - Bugfix found and fixed while writing the idempotency test: `upsert_fact._completar()` was
    comparing in-memory rows (with real int/float values) against disk-round-tripped rows (all
    strings from `csv.DictReader`), so a byte-identical re-run was reporting a spurious
    "reemplazada" every time (functionally harmless — same value ends up written — but it broke
    the "re-running a day changes nothing" idempotency check and would rewrite+backup the file on
    every nightly run for no reason). Fixed by normalizing every value to its CSV text
    representation before comparing/storing.
  - Verification run (SISTEMA-app worktree): `python -m pytest Ads/_TOOLS -q -p no:cacheprovider`
    -> 31 passed. `python Ads/_TOOLS/flujo.py --validar` -> valid (3 fases, 20 nodos). `python
    Ads/_TOOLS/verificar_guia_madre.py` -> sin fallas. `python Ads/_TOOLS/gen_grafo.py` -> ran
    clean (no orphans/dead paths), baseline JSON restored with `git checkout` afterward. `dbt
    parse` -> dbt is not installed in this environment (`dbt: command not found`); not runnable,
    reported rather than skipped silently. Backend `cd app/backend && uv run pytest -q
    --ignore=tests/test_meta.py` -> run in background, result pending at time of writing this
    entry (see the session's final report for the outcome).
  - NOT done in this worktree (by design — see "Where work happens" above): the actual re-pull of
    06-21-sep in SISTEMA. That is the parent's job after merging this branch in; T1's checkbox
    stays unchecked until that live re-pull is confirmed.

## Next step
T1 code is done; parent merges into SISTEMA (`git merge --ff-only`), then re-pulls 06-21-sep there
as a `chore(data)` commit, then checks T1 and moves to T2 (spend source of truth).
