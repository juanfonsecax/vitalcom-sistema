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
      ALSO (found 22-sep while checking T1 with dbt):
      (a) The production `dbt build` fails. `warehouse/models/_models.yml:19` accepts estado
          VIVO/PAUSADO/LISTO/ARCHIVADO, but `_DIM_PRODUCTOS.csv` uses NUEVO (OVULOS_PURITY).
          `gen_decisiones.py:57` degrades to a printed warning, so the analytics layer silently goes
          stale. Fix: a single owner for the product-state vocabulary (the dbt test and flujo.py read
          it, no copies), and a failing dbt build must be visible where the operator looks (orders
          header / app), not only on stdout.
      (b) Deployment order: `stg_entrega_anuncio` needs the `ad_id` column. After the merge, run the
          Meta re-pull (which migrates the CSV header through upsert_fact) BEFORE any dbt build. The
          nightly chain order (datos -> bajar_meta -> motor) already respects it; document it.
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

- 22-sep: T2 implemented (not checked — parent closes it after confirming with a run over the
  merged SISTEMA data, and after T1's live re-pull, which this worktree does not do).
  - Commits: `d9457f5` (helper + Python consumers, v1), `5a62dbd` (dbt mirror, v1), `66493c0`
    (vocabulary single-owner + dbt-failure surfacing), `d0820aa` (doctrine pointers), `6bdf2dc`
    (**fix**: redesign gasto.py after a correctness defect found in review — see below), `290187d`
    (**fix**: mirror the redesign in fct_gasto_dia).
  - **Defect found in review (v1, `d9457f5`/`5a62dbd`) and corrected (`6bdf2dc`/`290187d`):** v1
    resolved spend PER SALES ROW, and when no ad-level match existed it copied the FULL conjunto
    Meta spend onto that row. A conjunto with N sales rows (different ads, "- Copia" replicas)
    with no individual match each got the full conjunto total -> spend multiplied by N when a
    consumer summed those rows. And Meta spend for an ad with zero attributed sales never
    appeared anywhere (lost, not just deferred). The v1 "before/after" table showing NUSAVA/ARDOR
    jumping from CPA Q41.7 to Q73.1 was this bug, not the fix — corrected, its true CPA is Q43.3
    (see below), a small, real difference.
  - **Corrected design (`Ads/_TOOLS/gasto.py`, rewritten):** Meta spend and LucidSales
    sales/messages are aggregated SEPARATELY — never per input row — to a grain where each dollar
    is counted exactly once, then FULL OUTER JOINed on that grain:
    - `gasto_por_conjunto_ventana()`: key = (producto_key, cuenta_id, ventana_ini, ventana_fin,
      conjunto canónico). Meta spend = SUM of `_FACT_ENTREGA.csv` for that key (one source, one
      sum — never split or copied across the sales rows that land in it). Sales/messages = SUM of
      `_FACT_VENTAS.csv` BASE rows for the same key. A key with Meta spend and zero sales rows
      still appears (ventas=0); a key with sales and no Meta coverage falls back to the summed
      LucidSales `spend_usd`, flagged `LucidSales-fallback`. Used by `decidir.py` and
      `flujo.py`'s angle-winner gate (both aggregate by angle, which aggregates by conjunto).
    - `gasto_por_anuncio_ventana()`: key = ad_id when present on both sides, else (cuenta_id,
      ventana, **campaña**, conjunto canónico, anuncio) — campaign is part of the name key on
      purpose: FASE 2 deliberately repeats the same concept/anuncio text across 2-3 campaigns to
      test replication, and without campaign in the key those campaigns would collapse into one
      row and the 2-de-2 gate could never see the second occurrence (caught by a fixture in
      `test_flujo.py`). No conjunto-level fallback at this grain: an ad without an individual
      match keeps the LucidSales fallback, never another ad's or the conjunto's total. Used by
      `flujo.py`'s concept-2-of-2 gate and `sembrar_anuncios.py` (`_DIM_ANUNCIOS.csv` seeder).
    - `escribir_conjunto_ventana_csv()` writes the conjunto aggregate as one synthetic row per
      key (not per original sales row) for a consumer that runs its own SQL/CSV loader over
      `_FACT_VENTAS.csv` (decidir.py). `indice_gasto_por_anuncio()` / `clave_anuncio()` let a
      consumer with its own row-by-row loop (`sembrar_anuncios.py`) look up the already-correct
      aggregate by key — safe because each key's value was computed once, not accumulated again.
  - Consumers converted: `decidir.py` (`cargar_datos_duckdb` feeds its DuckDB query the aggregate
    CSV instead of raw `_FACT_VENTAS.csv`; `COBERTURA_GASTO` exposed as `cobertura_gasto`, now
    counting cells/keys, not rows), `flujo.py` (`_angulos_acumulados` uses the conjunto aggregate;
    `_ev_concepto_2de2` uses the ad aggregate; `_ev_estructura_publicada` keeps the raw
    `_ventas_base` generator — it only checks "spend > 0", a boolean where LucidSales and Meta
    essentially never disagree on sign, so the extra precision isn't needed there),
    `perfilar_angulos.py` (`serie_por_angulo` prorates the conjunto aggregate's cells across their
    window's days, instead of prorating a per-row LucidSales spend value), `sembrar_anuncios.py`
    (`_DIM_ANUNCIOS.csv` seeder, via `indice_gasto_por_anuncio()`).
  - Consumers NOT converted, justified (unchanged from v1's reasoning): `gen_pl.py` and
    `gen_finanzas.py` deliberately compare THREE independent sources (LucidSales attribution /
    Dropi cash / bank statement) to catch systemic errors — collapsing "capa 1" into the same
    Meta number as "capa 3" would remove that independence and defeat the audit's purpose; they
    also need a live `--dropi` xlsx this worktree doesn't have. `gen_dashboard.py` (2000+ lines,
    no test suite) deferred. `atribuir.py` reads `_DIM_ANUNCIOS.csv` (already fixed via
    `sembrar_anuncios.py`), not `_FACT_VENTAS.csv` directly.
  - **Before/after, corrected** (`decidir.py --json`, this worktree's data; saved to the scratch
    dir, tracked `_DECISIONES.json` restored with `git checkout` after each run). Every corrected
    `spend_usd` was independently re-verified straight from `_FACT_ENTREGA.csv` (Meta rows only,
    grouped by angle via `_DIM_CONJUNTOS`, summed over the SAME 14-day window decidir used,
    2026-09-08..21) — matched decidir's number to the cent for all 8 angles below:

    | producto/ángulo | CPA antes (LucidSales) | CPA v1 (bug) | **CPA corregido** | Meta directo (independiente) | estado corregido |
    |---|---|---|---|---|---|
    | NUSAVA/ARDOR | Q41.7 | Q73.1 (bug) | **Q43.3** | $125.13 == decidir $125.13 | ESCALAR (sin cambio) |
    | CLEARSTEM/ANTI_FALSIFICACION | Q31.7 | Q34.4 | **Q38.5** | $101.08 == $101.08 | RENOVAR |
    | CLEARSTEM/MEDICOS_FALLARON | Q104.4 | Q116.5 | **Q174.8** | $91.77 == $91.77 | RENOVAR |
    | CLEARSTEM/RESISTENCIA_INSULINA_SOP | Q32.9 | Q36.3 | **Q39.2** | $144.00 == $144.00 | RENOVAR (was ESCALAR) |
    | TINNIDROP (4 ángulos) | Q69.5-89.7 | Q72.3-93.4 | **Q66.0-95.4** | all match to the cent | SEGUIR_MIDIENDO |

    **NUSAVA/ARDOR explained:** LucidSales reported $125.88 spend / 23 ventas = Q41.7. Meta's
    real spend for the same window is $125.13 (23 ventas in the raw file, decidir's rolling
    window landed on 22 after a one-day boundary shift explained below) — essentially IDENTICAL
    to LucidSales here (-0.6%), unlike the earlier bug's 3x-inflated $73.1. This matches the
    reviewer's own observation: measured Meta-vs-LucidSales spend for NUSAVA in this window
    differs only slightly, so ARDOR correctly stays ESCALAR. **CLEARSTEM/MEDICOS_FALLARON** is
    the angle where Meta and LucidSales genuinely diverge the most here (Q104.4 -> Q174.8, +67%):
    its conjunto has several replicated/renamed ads with no individual Meta match, so before this
    fix LucidSales' own (also potentially under-reported) per-ad spend was being summed instead
    of Meta's true conjunto total — the corrected number is the one independently reproducible
    from `_FACT_ENTREGA.csv` directly, shown in the table.

  - **Review round 2 (22-sep-2026): REJECTED again — a real bug, but not the one suspected.**
    The parent's own from-scratch check (window 2026-09-08..21, matching what my JSON reported)
    got CLEARSTEM/MEDICOS_FALLARON CPA Q116.5 (Meta Q699.3 / 6 sales) against my reported Q174.8,
    and flagged it as "R1 counted twice." **It was not a double count.** Tracing it end to end
    (`gasto_por_conjunto_ventana()` alone on real data -> correct; the temp CSV it writes ->
    correct, 12 rows for R1 summing to exactly $45.83; only `decidir.py`'s own SQL after that
    point showed the inflated number) found the actual bug: the "Observed side effect" from the
    previous round — Meta-only zero-sale days extending `ult` ("último día CON DATA") — was worse
    than documented. `ult` correctly moved to 2026-09-21 (a real Meta-only day, not a phantom:
    confirmed with a real `_FACT_ENTREGA.csv` row), but the window's `win`/`fat` SQL predicates
    only had a LOWER bound (`v.fecha >= ult - N days`) and no UPPER bound — relying on the old
    assumption that `ult` was always the data's true maximum date, which stopped being true once
    Meta-only days could extend `ult` past the last day with an actual sale. The window silently
    grew to 15 days (2026-09-07 through 2026-09-21 both included) for every celda, pulling in one
    extra day's spend without an extra day being dropped, and the extra day happened to be
    CLEARSTEM/MEDICOS_FALLARON's costliest — hence the outlier.
    - **Fix:** (1) `gasto.gasto_por_conjunto_ventana()` now tags each row `tiene_fila_ventas`
      (True only if `_FACT_VENTAS.csv` actually has a row for that key, false for a Meta-only
      synthetic row); `escribir_conjunto_ventana_csv()` writes it as a column. (2) `decidir.py`'s
      `ult` CTE now computes `max(fecha) from ventas_raw where tiene_fila_ventas` — anchored to
      the last day with a REAL LucidSales row, exactly like before gasto.py existed. (3) `win`/
      `fat` gained the missing upper bound (`and v.fecha <= ult`), so a Meta-only day beyond `ult`
      can still be aggregated at the celda level (its spend isn't lost, per the FULL OUTER JOIN
      design) but can never widen the evaluation window past `dias`/`dias_fatiga`.
    - **Verified three ways, all agreeing to the cent:** decidir.py's live output; a from-scratch
      pandas script (`sys.path` only for `alias.canonico`, no other `Ads/_TOOLS` import,
      reproducing the parent's exact method) over window 2026-09-07..20; and the parent's own
      numbers. All 8 angles match exactly:

      | producto/ángulo | CPA (decidir, fixed) | CPA (from-scratch pandas) | CPA (parent's check) |
      |---|---|---|---|
      | CLEARSTEM/ANTI_FALSIFICACION | 34.4 | 34.4 | 34.4 |
      | CLEARSTEM/MEDICOS_FALLARON | 116.5 | 116.5 | 116.5 |
      | CLEARSTEM/RESISTENCIA_INSULINA_SOP | 36.3 | 36.3 | 36.3 |
      | NUSAVA/ARDOR | 44.3 | 44.3 | 44.3 |
      | TINNIDROP/ACCESIBILIDAD_MEDICO | 72.3 | 72.3 | 72.3 |
      | TINNIDROP/DETERIORO_COGNITIVO | 74.8 | 74.8 | 74.8 |
      | TINNIDROP/NOCHES_SIN_DORMIR | 93.4 | 93.4 | 93.4 |
      | TINNIDROP/PERDIDA_AUDITIVA | 93.4 | 93.4 | 93.4 |

      With the window fix, `decidir.py`'s own window for this data is 2026-09-07..20 (rezago 2),
      matching the parent's assumed window exactly — resolving the NUSAVA "Q23 difference"
      question too: it was the same one-day window-edge cause, now gone.
    - **Regression tests added:** `test_gasto.py` ::
      `test_dos_grafias_meta_que_canonicalizan_igual_no_duplican_con_fila_de_anuncio_presente`
      (two `_FACT_ENTREGA.csv` rows with different raw names that canonicalize to the same
      conjunto, plus an unrelated `_FACT_ENTREGA_ANUNCIO.csv` row for that conjunto -> conjunto
      grain sums the two conjunto rows exactly once each, never touches the ad-grain fact).
      `test_decidir.py` :: `test_dia_meta_only_no_corre_la_ventana_de_evaluacion` (a Meta-only day
      two days after the last real sale, `dias=1` -> the window stays on the sale's day; the
      Meta-only day's spend is excluded, not silently inherited into the 1-day window).
  - dbt: `fct_gasto_dia` rewritten to the same aggregate-then-join design (CTEs `ventas_agg` /
    `meta_agg` over `stg_ventas` / `stg_entrega_conjunto`, `full outer join` on the conjunto key);
    `fct_conjunto_dia` sources from it. Builds and its `not_null` tests pass in this worktree.
  - ALSO (a): `PRODUCTOS/_DIM_VOCABULARIO.csv` gained the `estado_producto` axis (NUEVO/VIVO/
    PAUSADO/LISTO/ARCHIVADO), generated by `Ads/_TOOLS/gen_vocabulario.py` (never hand-edited,
    invariant 11). `warehouse/models/_models.yml`'s `accepted_values` on `stg_productos.estado`
    (missing NUEVO, broke the build against OVULOS_PURITY) is replaced by a `relationships` test
    against the new `stg_vocabulario_estado_producto` model — one vocabulary, not two.
    `gen_decisiones.py` writes `capa_analitica: {estado, detalle, generado}` into
    `_DECISIONES.json` after every `dbt build` (OK/FALLO/OMITIDO, previously only stdout);
    `gen_ordenes.py` forwards it and adds an aviso when FALLO; `app/backend` gained
    `Decisiones.capa_analitica` / `OrdenesRespuesta.capa_analitica`.
  - ALSO (b): deployment order documented in `DOCTRINA/DATA_PLAYBOOK.md` and the
    `recopilar-lucidsales` skill — Meta re-pull (migrates `ad_id` into the CSV header via
    `upsert_fact`) before any `dbt build`, since `stg_entrega_anuncio` requires that column.
  - Tests (script-style, rewritten for the corrected design): `test_gasto.py` (18 checks —
    conjunto-grain: N unmatched ads don't multiply spend, Meta-only cell still counted, two
    distinct conjuntos don't mix, alias canonicalization, unrecognized `fuente` excluded, two
    Meta-side name variants that canonicalize to the same conjunto sum once each even with an
    unrelated ad-fact row present (round-2 regression); ad-grain: ad_id beats name,
    scientific-notation ad_id, a renamed ad sharing an ad_id doesn't duplicate, no conjunto-
    fallback inheritance, Meta-only ad still counted, the SAME anuncio text in two campaigns
    doesn't collide; **the required invariant**: `SUM(effective spend) == SUM(Meta spend for
    covered keys) + SUM(LucidSales fallback for uncovered keys)` to the cent, at both grains),
    `test_decidir.py` (+2: `cargar_datos_duckdb()` uses $50 Meta spend over $10 LucidSales for the
    same window; a Meta-only day past the last real sale doesn't widen the window — round-2
    regression), `test_vocabulario_estado.py` (4 checks, unchanged). `test_flujo.py` (29/29,
    including a fixture-driven regression for the campaign-collision fix) and
    `test_perfilar_angulos.py` (17/17) pass.
  - Verification run (SISTEMA-app worktree, after the round-2 fix): `python -m pytest Ads/_TOOLS
    -q -p no:cacheprovider` -> 33 passed. `python Ads/_TOOLS/flujo.py --validar` -> valid (3 fases,
    20 nodos). `python Ads/_TOOLS/verificar_guia_madre.py` -> sin fallas.
    `python Ads/_TOOLS/gen_grafo.py` -> clean (no orphans/dead paths), baseline restored with
    `git checkout` afterward. `dbt build` -> 27 PASS, 1 pre-existing documented ERROR
    (`stg_entrega_anuncio`: `_FACT_ENTREGA_ANUNCIO.csv` predates T1's `ad_id` column in this
    worktree — needs the live re-pull in SISTEMA), 4 cascading SKIPs limited to the ad-level
    models (`fct_anuncio_dia` and its tests); `fct_gasto_dia`/`fct_conjunto_dia` now BUILD and
    PASS (they no longer depend on the broken `stg_entrega_anuncio` — conjunto grain only needs
    `stg_entrega_conjunto`, which already has `ad_id`-independent columns).
    `python Ads/_TOOLS/sembrar_anuncios.py` (diagnostic) -> runs clean, total gasto cubierto
    dropped from the v1-buggy $5257 to a correct $4328 — itself confirming the fix removed
    inflated spend. Backend `cd app/backend && uv run pytest -q --ignore=tests/test_meta.py` ->
    136 passed (re-run after the fix). `git status --short` -> clean after every run.

- 22-sep PARENT REVIEW of T2: rejected twice (1: a per-row conjunto spend multiplied N times;
  2: a Meta-only day widened the decidir window from 14 to 15 days). Accepted at f92c71c: decidir.py
  CPAs match an independent pandas computation to the decimal for all 8 angles (CLEARSTEM 34.4 /
  116.5 / 36.3; NUSAVA 44.3; TINNIDROP 72.3 / 74.8 / 93.4 / 93.4). Consequence: TINNIDROP
  PERDIDA_AUDITIVA sits AT break-even (Q93.4) with Meta spend. T1+T2 close after the merge and the
  live re-pull in SISTEMA.

## Next step
T1 and T2 code are done; parent merges into SISTEMA (`git merge --ff-only`), re-pulls 06-21-sep
there as a `chore(data)` commit (this also fixes the `ad_id` column `stg_entrega_anuncio` needs),
runs `dbt build` AFTER that re-pull (not before — see the new deployment-order doctrine), confirms
`decidir.py`/the app read the corrected spend and `capa_analitica` on the merged data, then checks
T1 and T2 and moves to T3 (unknown ads: register ads missing a `_DIM_CONJUNTOS` row).
