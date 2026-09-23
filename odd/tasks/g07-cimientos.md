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
- [x] T3 Unknown ads: ingestion lists ads without a `_DIM_CONJUNTOS` row as a visible pending item
      (not silently dropped or left without angle); the path to register them is declared.
- [x] T4 (P4) Bot order: F2.etapa-11 becomes a congruence diagnosis (no rewrite gate); the F3 entry
      requires a CAMBIO_BOT dated after the winning concept; `_ev_eventos` supports "after X".
      Doctrine: CLAUDE.md pointer + PLANTILLAS_FLUJO_BOT.md.
- [x] T5 (P5) Gates are locks: `registrar_evento.py` (LANZAMIENTO) and `gen_publicacion.py --fase N`
      refuse when the phase gate is unmet, unless `--excepcion "reason"` records an EXCEPCION event.
- [x] T6 (P7) Compute and write are separate: flujo.py, decidir.py, gen_grafo.py get a read-only mode.
      A "read" never writes tracked files.
- [x] T7 (P8) Tests: costear.py, registrar_evento.py, decidir.py ESCALAR_MODERADO and comparar_cierre.
- [x] T8 (P10) Hygiene: iniciar.bat refuses an ambiguous base; verificar_publicacion requires
      effective_status=PAUSED; invariant 7 requires exactly the next day; etapa-3 status resolved.
- [x] T9 (P9) Folders: classes out of the repo, live backups to a gitignored `_RESPALDOS/`, dead
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

- 23-sep: T3 committed `8c90b10`, T4 committed `a2a7fa2` (route: delegated writer for the T4
  fix). Parent review found and fixed a T4 defect before commit: the winner reference date was
  "last day with a sale", which moves forward with every new sale and would flip the F3 gate back
  to false; now a stable first-crossing date (regression check H2). Gates: pytest 33 passed,
  test_flujo 36/36, flujo --validar OK, guia madre OK, gen_grafo clean, backend 136 passed (run
  alone). FINDING (open, backend test harness): pytest finishes in ~3:20 but the process never
  exits (something non-daemon stays alive), so `... | tail` hangs forever; and one flaky failure
  (`_claude_argv.log.candado` lock, test_pasos) appeared only when two runs overlapped.

- 23-sep: T5 committed `1792398`. `flujo.gate_entrada(producto_key, fase, env=None)` (new,
  Ads/_TOOLS/flujo.py) is the single read-only judge of "is fase's entry gate met": it reuses
  `cargar_flujo()`/`contexto()`/`evaluar()` exactly as `situar()` does, never touches
  `_ESTADO_FLUJO.csv` or `_EVENTOS.csv`, and returns `(True, "F1 no declara gate de entrada")`
  for a phase with no gate. `gen_publicacion.py --fase N` calls it right after the
  `--solo-paquete` return (so a readiness check never triggers it — only a real publish does)
  and before writing the canonical `_PUBLICACION_F*.json`; `registrar_evento.py --evento
  LANZAMIENTO` resolves the phase from `--fase` or, failing that, from the `TOKEN_FASE` token
  (TEST/CONCEPTOS/ESCALA) inside `--campana` (new `resolver_fase()`), refusing if neither
  resolves. Both refuse with a non-zero exit and write nothing when the gate is unmet, unless
  `--excepcion "motivo"` is given (an empty string counts as not given) — then the action
  proceeds and exactly one `EXCEPCION` row (`valor_antes`=the refused gate, e.g. `F2.entrada`;
  `valor_despues`=the action that proceeded) is appended through a new
  `registrar_evento.registrar_excepcion()`, which reuses the existing `validar()`/`anexar()`
  pair — no second CSV writer. T4's `EXCEPCION_CAMBIO_BOT` alternative inside F3's own gate
  predicate is untouched, left as its own thing per the task note (not unified with this
  generic `EXCEPCION`, flagged for the operator).
  - Doctrine: CLAUDE.md gained a "Reglas de invocación" bullet and an ownership-map note under
    "Transiciones entre pasos y sus gates"; `.claude/skills/publicar-meta/SKILL.md` step 1
    notes the refusal and the `--excepcion` flag. `.claude/agents/ETAPA-*.md` untouched.
  - Tests (script-style, tmp fixtures only, no data CSV in SISTEMA-app touched): new
    `test_gate_entrada.py` (8 checks: F1 always-ok, F2 angulo_ganador met/unmet reusing
    `test_flujo.fixture_escalar_flaco`, F3 concepto_2de2+CAMBIO_BOT met/unmet reusing
    `test_flujo.fixture_conceptos_al_filo`, unknown product, unknown phase, and a read-only
    check comparing `_ESTADO_FLUJO.csv`/`_EVENTOS.csv` existence before/after); new
    `test_registrar_evento.py` (7 checks: gate met registers plain, gate unmet refuses and
    writes nothing, empty `--excepcion` refuses the same way, gate unmet + `--excepcion`
    registers LANZAMIENTO plus exactly one EXCEPCION row with the right fields, phase from the
    campaign token, missing phase asks for `--fase`, a non-LANZAMIENTO event skips the gate
    entirely); extended `test_gen_publicacion.py` with 4 checks mirroring the same four
    scenarios end-to-end through `gp.main()` (gate met writes the canonical package; gate unmet
    writes nothing; empty exception refuses; gate unmet + exception writes the package and
    exactly one EXCEPCION row) — its `_correr_main()` helper now also monkeypatches
    `registrar_evento.BASE/PROD/EVENTOS` (the same cached module `gen_publicacion` imports),
    since P5 makes the two scripts share that writer.
  - Verification (SISTEMA-app worktree): `python -m pytest Ads/_TOOLS -q -p no:cacheprovider`
    -> 35 passed (33 + the 2 new files). `python Ads/_TOOLS/test_gate_entrada.py`,
    `python Ads/_TOOLS/test_registrar_evento.py`, `python Ads/_TOOLS/test_gen_publicacion.py`
    -> each 0 fallas standalone. `python Ads/_TOOLS/flujo.py --validar` -> valid (3 fases, 20
    nodos). `python Ads/_TOOLS/verificar_guia_madre.py` -> sin fallas. `python
    Ads/_TOOLS/gen_grafo.py` -> clean (no orphans/dead paths), baseline restored with
    `git checkout --` afterward. Backend not run (no `app/` file touched). `git status --short`
    clean after commit.
  - Open question for the operator: `Ads/_TOOLS/ingestar_unificado.py:268` still derives
    `mensajes` from clicks (flagged under T1, unrelated to T5) — untouched here, out of scope.

- 23-sep: T6 committed `854318d`. Write map (before this change):
  - `flujo.py`: `--todo` (only) wrote `_ESTADO_FLUJO.csv`/`_EVENTOS.csv` (`escribir_estado()`) and
    `_FLUJO.json`/`VISTAS/FLUJO.html` (`main()`), gated by a pre-existing opt-out `--sin-escribir`.
    `flujo.py PRODUCTO`, `--json` (without `--todo`), `--validar` and `--grafo` never wrote —
    already read-only. `gate_entrada()` (called as a Python function by `gen_publicacion.py` and
    `registrar_evento.py`, never via CLI) was and remains SOLO LECTURA.
  - `decidir.py`: `main()` wrote `_DECISIONES.json` **unconditionally**, on every invocation
    (bare, `--json`, `--grano`, `--dias` — no opt-out existed). `analizar_portafolio()` itself was
    already pure; only the CLI wrapper wrote. `gen_decisiones.py` is not an independent writer —
    it's an orchestrator that runs `dbt build` then subprocess-calls `decidir.py` (the real
    writer) and patches the same JSON afterward with `capa_analitica`.
  - `gen_grafo.py`: `main()` wrote `_LINEA_BASE_SISTEMA.json` by default, with a pre-existing
    opt-out `--no-guardar`. `analizar()` itself was already pure. No caller anywhere in the repo
    invokes `gen_grafo.py` (confirmed by search across `app/backend`, `.claude/settings.json`,
    `VISTAS/_MANIFIESTO.json`, skills, `Ads/_TOOLS/*.py`) — it's operator/session-run only.
  - **Contract chosen (uniform across the three): reading is the default; `--escribir` is the
    only flag that writes.** Rationale: `decidir.py` had zero opt-out and needed one either way;
    `gen_grafo.py` has no callers so flipping its default is free; `flujo.py`'s `--todo` already
    had a live opt-out (`--sin-escribir`) used by exactly the callers that need the write, so
    inverting it to an opt-in (`--escribir`) with the same call sites updated was no more
    invasive than adding the opt-out was originally. `--sin-escribir` and `--no-guardar` were
    removed (not kept as deprecated aliases) so the CLI has one flag name, one semantics, across
    all three scripts. `flujo.gate_entrada()` needed no change — function-call callers never hit
    `main()`'s argparse at all, so no flag applies to them.
  - **Callers found and updated** (grep across the whole repo for `flujo.py --todo`, `decidir.py`,
    `--sin-escribir`, `--no-guardar`):
    - `Ads/_TOOLS/gen_decisiones.py` → `decidir.py` invocation now `--escribir` (nightly chain).
    - `Ads/_TOOLS/ciclo_hoy.py` → `flujo.py --todo` now `flujo.py --todo --escribir` (nightly chain).
    - `Ads/_TOOLS/gen_app.py:leer_decisiones()` → lazy refresh (`refrescar=True` or file missing)
      now calls `decidir.py --escribir`, otherwise it would generate a `_DECISIONES.json` that
      never lands on disk and the same lazy check would loop forever.
    - `VISTAS/_MANIFIESTO.json` → the `flujo` vista's `"genera"` field and the
      `sistema.refrescar_flujo` action's `"comando"` (whose own declared `"escribe"` list already
      named `_FLUJO.json`/`_ESTADO_FLUJO.csv`/`_EVENTOS.csv`/`FLUJO.html`) both now carry
      `--escribir`.
    - `CLAUDE.md` → the session-start doctrine command (`ARRANQUE DE SESIÓN` and the pointer
      table row) now reads `flujo.py --todo --escribir` — this is the one place a session
      deliberately wants the persisted state, since the rest of the session reads
      `_ESTADO_FLUJO.csv` as ground truth. Added a `DOCTRINA/DATA_PLAYBOOK.md` §7 pointer under
      "Reglas de invocación".
    - `app/backend/vitalcom_app/contratos.py:flujo()` → dropped the now-invalid `--sin-escribir`
      (a single-product query without `--todo` was already read-only regardless of flags; the
      flag would now be a hard argparse error, not a silent no-op).
    - `app/backend/tests/test_api_espeja_los_csv.py` and
      `app/backend/tests/test_sin_aritmetica.py::test_flujo_se_invoca_siempre_sin_escribir` →
      updated to the new contract (the latter now asserts contratos.py names neither `--todo` nor
      `--escribir`, via the same AST-literal helper it already used, so a docstring mention can't
      false-positive it).
  - `DOCTRINA/DATA_PLAYBOOK.md` gained §7 "CONTRATO DE CLI — un mirar nunca escribe" (the table of
    what each script computes vs. persists, and who is allowed to ask for `--escribir`).
  - Tests (script-style, new `Ads/_TOOLS/test_cli_solo_lectura.py`, 14 checks, tmp dirs / tmp
    JSON paths only — the `gen_grafo.py` ones run against the real repo since it always
    `os.chdir()`s to it and has no fixture hook, and restore the real `_LINEA_BASE_SISTEMA.json`
    byte-for-byte in a `finally` regardless of outcome): per script, read mode leaves the target
    file byte-identical or absent, and `--escribir` writes it (flujo.py via its `--base` fixture
    hook reusing `test_flujo.fixture_escalar_flaco()`; decidir.py via monkeypatching
    `decidir.SALIDA_JSON`, matching the existing `PARAMS_PATH`-monkeypatch pattern in
    `test_decidir.py`; gen_grafo.py via subprocess against the live repo); running `flujo.py
    --todo` twice without `--escribir` stays a no-op (idempotent no-write); `analizar_portafolio()`
    never writes under any `SALIDA_JSON` value; and 7 static AST/regex checks that
    `gen_decisiones.py`, `ciclo_hoy.py`, `gen_app.py`, `VISTAS/_MANIFIESTO.json` (both spots) and
    `CLAUDE.md` all pass `--escribir` where they need to, while `contratos.py` never does.
  - Verification (SISTEMA-app worktree): `python -m pytest Ads/_TOOLS -q -p no:cacheprovider` ->
    36 passed (35 + the new file). `python Ads/_TOOLS/test_cli_solo_lectura.py` standalone -> 0
    fallas. `python Ads/_TOOLS/flujo.py --validar` -> valid (3 fases, 20 nodos).
    `python Ads/_TOOLS/verificar_guia_madre.py` -> sin fallas. `python Ads/_TOOLS/gen_grafo.py`
    (default, no flags) -> ran clean, `git status --short` showed no change to
    `_LINEA_BASE_SISTEMA.json` (confirmed read-only by default, no `git checkout` needed for this
    run). Backend `cd app/backend; uv run pytest -q --ignore=tests/test_meta.py` -> see below.
    `git status --short` -> only the intended files touched (no data CSV, no other test file).

- 23-sep: T7 committed `79e06f4`. Route: delegated writer.
  - New `Ads/_TOOLS/test_costear.py` (8 checks, own temp `_DIM_COSTEO.csv` — never the real one):
    exact match; nearest row below; nearest row above; exact tie resolves to the HIGHER row
    (conservative, per `elegir_fila()`'s docstring and ETAPA-1.md); cost above the table's top row
    -> `criterio_de_fila == "TECHO DE TABLA EXCEDIDO"`, an `alerta` string, and `main() --json`
    returns exit 1 (0 on a clean match); escalera 1u/2u/3u equal the row's
    `precio_establecido`/`precio_2u`/`precio_3u` exactly. **Finding (documented via a passing
    test, not fixed — no code owner rule says it should alert):** a cost BELOW the table's
    cheapest row raises no alert, unlike a cost above the ceiling — `elegir_fila()` only guards
    `costo > filas[-1][0]` (the top), there's no symmetric guard against `filas[0][0]` (the
    floor); a cost under the floor silently lands on the cheapest row as if it were a normal
    "nearest" case. Harmless if no product ever costs less than the cheapest row; flagged for the
    operator, not fixed here since it's a scope call, not a defect this task's rule covers.
  - Extended `Ads/_TOOLS/test_registrar_evento.py` (+10 checks, all through non-LANZAMIENTO
    events so `flujo.gate_entrada` is never consulted — a new `_fixture_validacion()` fixture,
    lighter than `_fixture_lanzamiento()`, with only `_DIM_PRODUCTOS.csv` + `_PARAMETROS_DECISION.csv`
    + an empty `_EVENTOS.csv`): unknown `producto_key` refused, `GLOBAL` always accepted; an event
    with a character outside `[A-Z0-9_]` refused (a plain lowercase input doesn't exercise this
    branch — `main()` already `.upper()`s `--evento` before `validar()` runs, so the test uses a
    hyphen to reach the regex check for real); empty `motivo` / `fuente_decision` refused;
    `CAMBIO_PRESUPUESTO` with a non-numeric `--antes` refused; a budget raise within `surfing_pct`
    accepted, one above it refused without `--forzar` and accepted with it; `--dry-run` writes
    nothing even for an otherwise-valid row; a motivo containing a comma round-trips exactly
    through `csv.DictReader` and lands quoted in the raw file (invariante 11).
  - Extended `Ads/_TOOLS/test_decidir.py` (+7 checks): `test_escalar_moderado_frontera()` freezes
    both edges of ESCALAR_MODERADO (regla 6) at a fixed ventas=50 — the OBJ edge (Q30.80 ± 0.05:
    below is `ESCALAR_SURFING`, above is `ESCALAR_MODERADO`; both states are literally "ESCALAR",
    so the test asserts on `accion_codigo`, not `estado`, since the existing CASOS-list runner
    only checks `estado`) and the practical upper edge. **Found while writing this test:** the
    code's literal upper bound is `be_q` (Q93.41), but at any sample size actually reachable the
    Bayesian credible interval (`ic_cpa`'s `ic_bajo_be` gate) breaks BEFORE `cpa_real_q` gets
    anywhere near `be_q` — at ventas=50 the real breakpoint (found by binary search over
    `ic_cpa`, not guessed) is CPA ~Q70.17, not Q93.41. A cpa a cent below that stays
    `ESCALAR_MODERADO`; a cent above it, the IC no longer holds under BE and the celda falls to
    `SEGUIR_MIDIENDO`/`MANTENER_Y_MEDIR` (rule 7) even though `cpa_real_q` is still under `be_q`.
    This isn't a bug — `ic_bajo_be` is explicitly required by rule 6's own condition — but it's
    the actual boundary of the rule in practice, not the number in the docstring/task wording, so
    the test documents it explicitly with the binary-search-derived constant rather than a
    rounder guess that might not actually cross the line. `test_comparar_cierre()` freezes: a
    50%-vs-10%-close case (n=100 each) as significant; identical 20%-vs-20% closes as never
    significant (p=1.0); and that either side having `mensajes<=0` returns `None` (no
    ZeroDivisionError, no invented p-value) — matching the function's own "corta, nunca corona"
    docstring.
  - No bugs required a code fix in this task: the one below-floor gap in `costear.py` is
    ambiguous by design (no owner rule mandates a floor alert) and is reported above, not patched.
  - Verification (SISTEMA-app worktree): `python -m pytest Ads/_TOOLS -q -p no:cacheprovider` ->
    37 passed (36 + the new `test_costear.py` file). `python Ads/_TOOLS/test_costear.py`,
    `python Ads/_TOOLS/test_registrar_evento.py`, `python Ads/_TOOLS/test_decidir.py` -> each 0
    fallas standalone. `python Ads/_TOOLS/flujo.py --validar` -> valid (3 fases, 20 nodos).
    `python Ads/_TOOLS/verificar_guia_madre.py` -> sin fallas (88 variables, 33 verificadas, 55
    cualitativas). `git status --short` -> only the three intended test files, clean after
    commit. Backend not run (no `app/` file touched by this task).

- 23-sep: T8 implemented and checked (all four hygiene items).
  1. **iniciar.bat refuses an ambiguous base.** Previously `VITALCOM_BASE=%~dp0` unconditionally,
     so double-clicking it inside SISTEMA-app (a linked git worktree) silently read that
     worktree's stale, never-updated CSVs. Fixed by comparing `git rev-parse --git-dir` against
     `--git-common-dir` (they differ only in a linked worktree); on a mismatch the script refuses
     with `exit /b 1`, names the main worktree from `git worktree list --porcelain`'s first entry,
     and tells the operator to declare `VITALCOM_BASE` to override on purpose. Also now requires
     `PRODUCTOS\_DIM_PRODUCTOS.csv` to exist (a worktree has `DOCTRINA/FLUJO.json` too — it's
     versioned — but not necessarily live product data).
     - Found the backend has the exact same gap: `app/backend/vitalcom_app/config.py`'s
       auto-detection fallback (`_subiendo()`) walks up looking for `DOCTRINA/FLUJO.json` and
       would accept a linked worktree just like the .bat did, for the same reason (the marker
       file is versioned). Fixed with the same git-dir/git-common-dir comparison, applied only to
       the auto-detected fallback — an explicit `VITALCOM_BASE` env var still overrides, matching
       the .bat's escape valve.
     - Tests: `Ads/_TOOLS/test_iniciar_bat.py` (new, static — asserts the .bat contains the
       git-dir/git-common-dir check, the refusal, the `VITALCOM_BASE` escape valve, and the
       `_DIM_PRODUCTOS.csv` check). `app/backend/tests/test_config.py` (new — builds a real git
       repo + linked worktree under `tmp_path` and asserts `_es_worktree_vinculado()`/
       `_subiendo()` detect and refuse it, while a git-less folder and the main worktree pass).
     - **No behavioral test of iniciar.bat itself** (invoking it with `cmd.exe` and checking the
       exit code): this sandbox's account (`CodexSandboxUsers`) cannot execute ANY `.bat` file —
       confirmed with a trivial one-line `echo hi` test file outside the repo, which failed with
       the same "not recognized as an internal or external command" error `cmd.exe` gives for a
       blocked launch, while `.exe` invocations (`git.exe`, `cmd.exe` builtins) work fine in the
       same directory. Documented in the test file's docstring for whoever runs this on a machine
       where it's not blocked.
  2. **verificar_publicacion.py requires PAUSED.** Extracted `objetos_no_pausados(filas, meta)` —
     of the declared objects that DO exist in Meta, which ones aren't `PAUSED` (empty/missing
     `effective_status` counts as not-PAUSED, never assumed PAUSED by omission). `main()` now
     blocks (exit 1, before or after `--escribir`) and prints each offending object's level, name,
     observed status and id when any exist. Tests (`test_verificar_publicacion.py`): all-PAUSED
     passes, one ACTIVE ad blocks (and only that one is reported), missing `effective_status`
     blocks, and an already-FALTA object isn't double-reported as also "not paused".
  3. **Invariant 7 exactly next day.** `gen_publicacion.py` only checked `fecha <= hoy`, so a
     launch date 2+ days out passed silently. Extracted `fecha_lanzamiento_invalida(fecha, hoy)`
     (`True` unless `fecha == hoy + 1 day`); the two fixtures that used the placeholder
     `"2030-01-01"` now compute tomorrow's real date (`MANANA`) instead, since they weren't
     testing this gate. Tests (`test_gen_publicacion.py`): today blocks, tomorrow passes, day
     after tomorrow blocks, yesterday blocks. Kept the message inline as a string literal at the
     `pq.bloquear_publicacion(...)` call site (not built inside the helper) — the existing
     `test_clasificacion_de_los_bloqueos_no_se_invierte` test statically parses the call's AST to
     classify publicacion-vs-paquete bloqueos by keyword, and a `Name` reference there instead of
     a string literal would have broken that classification.
  4. **etapa-3 status resolved — kept in F3.plan (orchestrator decision).** etapa-3's 8-12
     microángulos never landed anywhere on disk `flujo.py` could check — etapa-6 consumed them
     in-session only. Extended the `archivo` predicate with an optional `contiene` substring
     check (smallest addition to the closed vocabulary, per `flujo.py`'s own docstring rule) and
     added a `F3.plan` produce predicate requiring `PRODUCTOS/{slug}/4_PLAN_ESCALADO.txt` to
     contain "MICROÁNGULO". `ESCALADO_PLAYBOOK.md §7`'s template gained an explicit `6b. BANCO DE
     MICROÁNGULOS` section; `fase-3-escalado/SKILL.md` PASO 0 and `ETAPA-GUARDAR-PRODUCTO.md`
     (which previously didn't mention FASE 3 at all) both point to it. Test: `test_flujo.py`
     gained two `archivo · contiene` cases (found / not found) against the real fixture's
     `4_PLAN_ESCALADO.txt`. Confirmed no real product currently sitting at `F3.plan` breaks: none
     is there yet (`--todo` shows TINNIDROP already past it, flagged as an out-of-gate aviso
     either way).
  - Verification (SISTEMA-app worktree): `python -m pytest Ads/_TOOLS -q -p no:cacheprovider` ->
    38 passed. `python Ads/_TOOLS/flujo.py --validar` -> valid (3 fases, 20 nodos).
    `python Ads/_TOOLS/flujo.py --todo` -> read-only, `git status --short` unchanged by the run.
    `python Ads/_TOOLS/verificar_guia_madre.py` -> sin fallas. `python Ads/_TOOLS/gen_grafo.py`
    -> ran clean, no tracked baseline diff. Backend
    `cd app/backend; uv run pytest -q --ignore=tests/test_meta.py` -> 141 passed, 2 warnings in
    232.66s (0:03:52), exit 0 (includes the 5 new `test_config.py` cases).
  - Commits: iniciar.bat/config.py worktree refusal, verificar_publicacion PAUSED gate,
    gen_publicacion invariant-7 exact-next-day, flujo.py `contiene` + F3.plan microángulos check
    (four separate commits, one per hygiene item).

- 23-sep: T9 done (checked).
  - **Live backups redirected `_ARCHIVO/` -> `_RESPALDOS/` (gitignored):** one shared helper,
    `Ads/_TOOLS/upsert_fact.respaldos_dir(base, *sub)`, replaces four hardcoded paths —
    `ingerir_meta.py` (`BKDIR`), `ingerir_lucidsales.py` (`BKDIR`), `ingestar_unificado.py`
    (`ARCH_DIR`, now importing `upsert_fact` for it), and `bajar_meta_insights.py` (inherits it
    via `im.BKDIR`, unchanged). Docstrings/print messages updated to say `_RESPALDOS/`.
    `gen_grafo.py`'s `ZONAS_MUERTAS` dropped `_ARCHIVO` (gone; `_RESPALDOS` doesn't need it —
    `construir()` only lists direct `.md` children of specific folders, non-recursive, so a
    CSV-only backup dir at repo root is invisible to it either way). `gen_decisiones.py`'s note
    about the retired `DECISIONES.html` view updated to say it's in git history now.
    `verificar_guia_madre.py`'s directory-walk exclusion swapped `_ARCHIVO` for `_RESPALDOS` (same
    reason: skip a large gitignored backup tree during the doctrine-pointer search).
    `.gitignore`: added `_RESPALDOS/`; kept the old `_ARCHIVO/backups_csv|backups_agentes|
    backups_data/pruebas_lavado_20260705` lines rather than deleting them — this worktree has no
    live backup files on disk to worry about, but the main SISTEMA checkout does, and removing the
    ignore lines before the orchestrator physically moves those files would make them show up as
    untracked there. Explained inline in the `.gitignore` comment.
  - **Dead `_ARCHIVO/` tree removed:** `git rm -r _ARCHIVO` — 92 tracked files (`Bases/`,
    `CONTEXTOS_VIEJOS/`, `DATA_MIGRADA/`, `codex_superado_20260902/`, `etapas_fusionadas_20260902/`,
    `handoffs_ejecutados/`, `hub_viejo/`, `limpieza_20260917/`, `planes_fase2_lean_retirado_20260917/`,
    `refactor_20260731_2330/`, `retirado_20260909/`, `retirado_20260922/`, `roadmap_cumplido/`, plus
    loose root files). Checked first: nothing in `Ads/`, `DOCTRINA/`, `.claude/`, `app/`,
    `warehouse/`, `VISTAS/_MANIFIESTO.json`, or `CLAUDE.md` reads a path inside this tree — every
    hit was either a doctrine/backup-path string (fixed above) or a stale pointer in a reference
    doc (fixed below). Content stays in git history.
  - **Classes out of the repo:** `git rm -r _CONOCIMIENTO/Finales` (27 files) — already
    sha1-verified copied by the orchestrator to `C:\Users\juand\Documents\VITALCOM_CLASES\` before
    this worktree started. No live code referenced it by path; only doctrine/reference docs did.
  - **References fixed** (new path, or "moved to git history" where the pointer was to a
    now-removed backup/snapshot file rather than the live classes):
    `DOCTRINA/GUIA_MADRE_PARAMETRIZADA.md` (ingest protocol §III step 1, unchanged otherwise),
    `_CONOCIMIENTO/MATRIZ_METODOLOGIA.md` (§1 fuentes table F0-F5, §6 protocolo, maintenance
    warning — added one `VITALCOM_CLASES/` = full path note instead of repeating the full path 8
    times), `README.md` (file-map table row + rule 5/7 in "reglas de oro", which described the old
    "move to _ARCHIVO/, don't delete" policy — updated to the new "git rm, history keeps it"
    policy this very task follows), `CLAUDE.md` ("Zonas" line: dropped `_ARCHIVO/` from the
    human-reference list, added a sentence for `_RESPALDOS/` being gitignored/unread),
    `_ROADMAP/README.md` (top rule + the 2026-08-01 archived-items header, both pointed at
    `_ARCHIVO/roadmap_cumplido/`), `_OPERADOR/_PROMPT_AUDITORIA_GENERAL.md` (authority rule 1/3 +
    scope line — pointed at both `_CONOCIMIENTO/Finales/` and `_ARCHIVO/Bases/`),
    `_OPERADOR/TAREA_NOCTURNA.md` (backup path in the nightly-ingest description),
    `.claude/agents/ETAPA-7.md`, `Ads/_SWIPE/_HANDOFF_CONCEPTOS.md`, and two files under
    `Ads/_SWIPE/_BLUEPRINTS/` (`_LEEME.md`, `_HANDOFF_FICHAS.md`) — all pointed at a specific
    backup/retired file now only in git history.
  - **Left untouched, with reason** (dated logs/postmortems and one excluded zone, same policy as
    existing dated audits): `PRODUCTOS/_EVENTOS.csv` (one dated 2026-09-02 event row),
    `PRODUCTOS/_PORTAFOLIO.txt` (two dated notes, 25-jul and 2026-07-03), `PRODUCTOS/
    _BITACORA_DATA.txt` (dated bitácora entries), `_CONOCIMIENTO/POSTMORTEMS/*.md` (explicitly a
    frozen-snapshot zone), `_OPERADOR/PROMPT_SESION_OPTIMIZACION_2026-09-09.md` (a dated,
    session-specific prompt pointing at a since-removed roadmap doc), and everything under
    `PRODUCTOS/_AUDITORIAS/**` (excluded by the task's own rg command). `Ads/_TOOLS/gen_publicacion.py`
    matched the search pattern on unrelated identifiers (`SIN_ARCHIVO`, `FALTA_ARCHIVO`), not the
    `_ARCHIVO/` directory — no change needed.
  - **Tests:** two new cases in `Ads/_TOOLS/test_upsert_fact.py` —
    `test_respaldos_dir_resuelve_bajo__RESPALDOS` (unit: the helper never returns an `_ARCHIVO`
    path) and `test_ingestion_a_base_temporal_escribe_su_backup_en_RESPALDOS` (end-to-end: two
    `upsert()` calls against a temp base produce a real backup file under
    `<base>/_RESPALDOS/backups_csv/` and never create an `<base>/_ARCHIVO/`).
  - **Verification (SISTEMA-app worktree, all foreground):**
    `python -m pytest Ads/_TOOLS -q -p no:cacheprovider` -> 38 passed (file count unchanged — this
    harness counts test *files*, and both new cases live inside the existing
    `test_upsert_fact.py`). `python Ads/_TOOLS/test_upsert_fact.py` directly -> 12/12 OK, 0 fallas,
    exit 0. `python Ads/_TOOLS/flujo.py --validar` -> valid (3 fases, 20 nodos, 1 excepción).
    `python Ads/_TOOLS/verificar_guia_madre.py` -> sin fallas (88 variables, 33 verificadas). `python
    Ads/_TOOLS/gen_grafo.py` and `--comparar` -> both clean (ningún huérfano, ninguna ruta muerta);
    `_LINEA_BASE_SISTEMA.json` untouched (`git status` confirmed no diff — the plain/`--comparar`
    runs are read-only without `--escribir`). The `rg -n "Finales|_ARCHIVO" -g '!odd/**'`
    check from item 4 — see "left untouched" above for what legitimately remains. Backend
    `cd app/backend; uv run pytest -q --ignore=tests/test_meta.py` -> 141 passed, 2 warnings in
    229.96s (0:03:49), exit 0. `git status --short` clean after every commit.
  - **Commits:** `eec3735` (redirect `_ARCHIVO/` -> `_RESPALDOS/`, code+doctrine+gitignore),
    `04202c6` (`git rm -r _ARCHIVO`, 92 files), `f9fc6e7` (`git rm -r _CONOCIMIENTO/Finales` +
    all reference fixes + the two new tests, one commit — the reference fixes are only meaningful
    together with the removal they describe, so splitting them would leave an intermediate commit
    with dangling pointers).

## Next step
T1 and T2 code are done; parent merges into SISTEMA (`git merge --ff-only`), re-pulls 06-21-sep
there as a `chore(data)` commit (this also fixes the `ad_id` column `stg_entrega_anuncio` needs),
runs `dbt build` AFTER that re-pull (not before — see the new deployment-order doctrine), confirms
`decidir.py`/the app read the corrected spend and `capa_analitica` on the merged data, then checks
T1 and T2 and moves to T3 (unknown ads: register ads missing a `_DIM_CONJUNTOS` row). T9 (folders)
is now done; T10 (voice of customer as data) is next in dependency order.
