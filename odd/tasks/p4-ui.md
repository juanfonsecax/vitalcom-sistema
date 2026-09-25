# P4 — New operator UI (Hoy / Productos / Resultados / Ajustes)

## Objective
Replace the machinery-organized screens (Fase1/2/3, Trabajos, Salud...) with a navigation built
around the operator's questions, so a full day can be operated without opening the chat.

## Problem / why
The current frontend (`app/frontend`) is organized around system internals and uses hand-rolled
Tailwind components. Decided 23-sep-2026 (plan P1→P6, gate P4): shadcn/ui on Base UI primitives +
TanStack Table + shadcn charts, Linear-style (dense, calm, neutral palette, one accent, color
reserved for status: green ESCALAR, red PAUSAR, amber SEGUIR_MIDIENDO), desktop-first but
responsive from day 1. Tremor rejected.

## References (verified 24-sep-2026)
- App shell: satnaing/shadcn-admin (MIT; Vite + TanStack Router + shadcn; still on Radix).
- KPI cards / charts: ui.shadcn.com blocks `dashboard-01`, `sidebar-07`.
- Filterable tables: openstatusHQ/data-table-filters (MIT; Next, table code portable).
- Base UI composition: Kiranism/next-shadcn-dashboard-starter (MIT).

## Scope (authorized 2026-09-24: operator "sí, arranque con el paso 1")
Built in place in `SISTEMA-app` on branch `feat/p4-ui` (from `feat/app-web`). No parallel app.
Old screens stay reachable from Ajustes until their replacement lands. The app never computes or
writes business data: it reads contracts and runs declared executors (existing rule).

## Constraints
- Hoy content is set by the methodology, not preference: (1) stale-data banner when the last day
  with data lags > 2 days (CLAUDE.md invariant 13); (2) `decidir.py` orders, each confirmed one by
  one; (3) per product, the `flujo.py` node, blocker and owner. Money lives in Resultados (cohort
  < 10 days is preliminary, DOCTRINA/CONTABILIDAD.md).
- UI copy in Spanish (existing app language), neutral register.

## Config
- TDD: off (no project/session TDD configuration; source: none). Ordinary checks per task.
- Runners: backend `cd app/backend && uv run pytest`; frontend `cd app/frontend && pnpm test`,
  `pnpm build`, Playwright e2e `app/frontend/e2e`.
- RDD: off (decided by default, `gentle-ai review mode status` 24-sep).
- Delivery strategy: ask-on-risk. Forecast > 400 authored lines across the feature (generated
  shadcn component copies excluded) → chain strategy to be asked before the first PR.
- Chain strategy (operator, 24-sep, after T3 passed ~3k authored lines): `feature-branch-chain`
  targeting `feat/app-web`, one PR per task. Slice boundaries (commits per PR):
  PR1 T1 `bb969d3..b1669fe` · PR2 T2 `f15f419..6774bbe` · PR3 T3 `d81a021..2e7e79e` ·
  PR4 T4 `afa5325..3206053` · PR5 T5 `610de13..2d634b3`. Push/PR creation remains the operator's
  decision.

## Tasks
- [x] T1 — Shell: install shadcn/ui (Base UI), Linear-style tokens (light + dark), sidebar layout
  with Hoy / Productos / Resultados / Ajustes; existing screens mapped under the new nav (legacy
  ones under Ajustes). Route: delegated writer (2+ non-trivial files). Checks: pnpm test, pnpm
  build, e2e smoke, browser check desktop + mobile width.
- [x] T2 — Hoy: stale-data banner · decidir.py orders with per-order confirm · flujo.py next
  step per product. Uses existing endpoints. Route: delegated writer (2+ non-trivial files).
  Checks: pnpm test, pnpm build, Playwright e2e, browser check desktop + 375px.
- [x] T3 — Productos: table + product detail (angles, concepts, results); absorbs Fase1/2/3.
  Scope decided 24-sep: Fase1/2/3 are absorbed NAVIGATIONALLY — the product detail gets tabs
  (Resumen · Fase actual · …) that render the existing phase screens restyled by the tokens; their
  internals (Fase1.tsx is 1469 lines) are not rewritten in T3. Legacy `/producto/$clave/faseN` URLs
  keep working. Route: delegated writer.
- [x] T4 — Resultados: new backend endpoint reading the accounting layer, cohorts < 10 days
  flagged preliminary; KPI cards + charts.
  Decided 24-sep by the methodology (CONTABILIDAD.md rules over any other calculation): the screen
  shows the real P&L from `gen_pl.py` (views A/B/C), never `gen_finanzas.py` attribution (capa 1,
  can be inflated) and never ROAS. `gen_pl.py` needs a manual Dropi export (bank/cartera optional),
  so: T4a — additive read-only `--json` output in `gen_pl.py` (same numbers, test) persisted next
  to its `.txt` report; T4b — upload endpoint (existing `UploadFile` precedent) that runs it, a
  GET that reads the latest persisted result, and the screen with a "Cargar export de Dropi"
  action and the date of the last run. Note: the app runs the tools of the folder it points to;
  the real folder only gets `--json` once this branch reaches its branch.
- [x] T5 — Ajustes: accounts, fanpages; system health, jobs and guide hidden here.

## Acceptance
Operator can run a full day without the chat; every confirmed order lands as an event.

## Progress

### T1 evidence (24-sep-2026)

Commits on `feat/p4-ui`:
- `bb969d3` build(frontend): add shadcn/ui on Base UI with Linear-style tokens
- `54ff860` feat(frontend): sidebar shell with Hoy/Productos/Resultados/Ajustes

**shadcn setup.** `pnpm dlx shadcn@latest init -y -b base -t vite -p nova` (Base UI primitives,
preset Nova/Lucide — the CLI's default since the 2026-03 `cli-v4` changelog; confirmed live via
context7 against `/shadcn-ui/ui` docs, not from training memory). Needed the `@/` alias in
`tsconfig.json` (`baseUrl`+`paths`) and `vite.config.ts` (`resolve.alias`) first — the CLI refuses
to init without one. Added components: `sidebar`, `separator`, `sheet`, `tooltip`,
`dropdown-menu`, `badge` (+ their own deps: `button`, `input`, `skeleton`, `hooks/use-mobile.ts`).
Vendored under `src/components/ui/` and `src/lib/utils.ts` per the CLI's own aliases — English
identifiers there are the shadcn convention, left as generated; app-authored files stay in the
project's Spanish convention (`componentes/`, `pantallas/`).

**Tokens** (`src/estilos.css`): neutral gray background/foreground, one indigo accent
(`--primary`/`--ring`/`--sidebar-primary`), light theme as the base with `.dark` overriding via
class (no forced `color-scheme: dark` anymore). Four semantic status tokens matching
`decidir.py`'s vocabulary: `--estado-escalar` (green), `--estado-pausar` (red), `--estado-seguir`
(amber), `--estado-renovar` (violet) — each exposed as a Tailwind color (`bg-estado-*`,
`text-estado-*-foreground`) via `@theme inline`, not yet consumed by T1 (T2's decidir.py orders
will use them). Compact density via `html { font-size: 87.5% }` (14px root): all of Tailwind's
rem-based spacing/sizing shrinks with it, so it isn't redone per component.

**Nav** (`src/componentes/BarraLateral.tsx`, wired into `Marco()` in `src/main.tsx`): a
`Sidebar collapsible="icon"` with exactly Hoy/Productos/Resultados/Ajustes, a desktop
`SidebarTrigger` + `SidebarRail` to collapse to icons, and shadcn's own mobile behavior (< 768px:
off-canvas `Sheet` via a slim top bar with a menu button — free from the vendored `Sidebar`
component, not custom-built). Active section is computed from the pathname
(`src/componentes/BarraLateral.tsx#claveActiva`): Hoy on `/`, Productos on `/productos` and any
`/producto/$clave/**`, Ajustes on `/ajustes` and every legacy route it now fronts. Theme toggle
(`componentes/tema.ts`, light/dark/system) lives in the sidebar footer, persisted to
`localStorage` wrapped in try/catch. The pending-jobs badge (`api.trabajos`, moved out of the old
`EnlaceDeTrabajos`) now sits on the Ajustes sidebar item and again on the Trabajos card inside
Ajustes.

**Route map** (`src/main.tsx`):
| Route | Component | Notes |
|---|---|---|
| `/` | `Tablero` | Hoy — T2 replaces this |
| `/productos` | `Tablero` | same screen as Hoy for T1; T3 gives it its own |
| `/resultados` | `Resultados` (new) | "en construcción" placeholder |
| `/ajustes` | `Ajustes` (new) | links to the 5 legacy screens below |
| `/ordenes` | `Ordenes` | unchanged, now only reachable from Ajustes |
| `/producto/$clave`, `/fase1`, `/fase2`, `/fase3` | unchanged | "inside" Productos |
| `/salud`, `/guia`, `/nuevo`, `/trabajos`, `/trabajos/$id` | unchanged | reachable from Ajustes |

**Deviations from the brief:** none in scope. Two Playwright specs needed their selectors
updated because the top navbar no longer exists (structural change, not a weakened assertion):
`e2e/guia.spec.ts` now opens Guía from `/ajustes` instead of a navbar link; `e2e/trabajos.spec.ts`
now checks the `Ajustes` sidebar link is visible from `/trabajos` instead of a `Trabajos` navbar
link (Trabajos has no link of its own in the new nav — it's nested under Ajustes). Also added
`src/pruebas/preparar.ts` matchMedia polyfill: jsdom doesn't implement it and shadcn's own
`use-mobile.ts` hook (used internally by `Sidebar`) calls it unguarded, so any test mounting the
sidebar crashed without it — this affects every future frontend test, not just this task's.
Added a `matchMedia`-independent try/catch inside `componentes/tema.ts` itself for the same
reason (belt and suspenders for real browsers that don't support `matchMedia`, e.g. very old
WebViews). Also added an `app-web` entry to this worktree's own `.claude/launch.json` (mirroring
the one already in `SISTEMA/.claude/launch.json`) so the frontend dev server can be previewed
from inside `SISTEMA-app` directly.

**Verification:**
- `cd app/frontend && pnpm test` → 12 files, 66 tests passed (includes the new
  `src/pruebas/barra_lateral.test.tsx`: 4 tests asserting the four nav items render and the
  right one is marked active, including on a child route like `/producto/$clave` that has no nav
  item of its own).
- `cd app/frontend && pnpm build` → `tsc -b && vite build` clean, no type errors.
- Browser check (Chrome via the Browser pane, `pnpm dev` on :5173, no backend running so screens
  show the expected "No pude leer el sistema" error card): confirmed at desktop width — sidebar
  renders, Hoy/Productos/Resultados/Ajustes navigate and highlight correctly, icon-collapse via
  the header trigger and the drag rail both work, light/dark/system theme toggle switches the
  whole page — and at 375×812 (mobile preset) — no horizontal scroll
  (`document.documentElement.scrollWidth === 375`), the top bar's menu button opens the sidebar
  as an off-canvas sheet with all four items.
- Playwright e2e: **not run** — this environment has no installed browser binaries
  (`pnpm exec playwright install` reports Chromium/ffmpeg/headless-shell all missing) and
  installing them means downloading several binaries, which needs the operator's explicit
  go-ahead first (not assumed here). The existing specs were read and reasoned through instead
  (see Deviations above); `e2e/tablero.spec.ts`, `fase1.spec.ts`, `fases_2_3.spec.ts`,
  `ordenes.spec.ts`, `nuevo_producto.spec.ts` don't touch the nav and should be unaffected.
- `cd app/backend && uv run pytest -q` → confirmed unaffected (no backend files touched by T1);
  collection is clean (168 tests). The full run takes past this session's command timeouts
  (DBOS/workflow tests do real waits) and was still running in the background when this task
  closed out — flagging as `pending` rather than claiming a result I didn't see.

### T2 evidence (24-sep-2026)

Commit on `feat/p4-ui`: `f15f419` feat(frontend): Hoy screen with stale-data banner, orders and
next steps.

**Route.** `/` now renders `src/pantallas/Hoy.tsx` (was `Tablero`); `/productos` keeps `Tablero`
unchanged, per T1's plan (T3 redoes it). `e2e/tablero.spec.ts`'s two tests that asserted on `/`
now target `/productos` — same assertions, only the URL moved, per the brief ("move it, don't
weaken it").

**Business-rule reuse, not duplication.** `Ordenes.tsx` had `TONOS_ESTADO`/`TEXTO_ESTADO`/
`GLOSARIO_POR_ESTADO` defined inline. Moved them into `src/lenguaje.ts` as `TONO_ORDEN`,
`TEXTO_ORDEN`, and a new `glosarioDeOrden(estado, bloqueoFase)` helper (encapsulates the
"ESCALAR bloqueado por fase never shows the ESCALAR glosario" rule that used to live as an
inline ternary in `Ordenes.tsx`). `Ordenes.tsx` now imports these instead of redefining them;
its own 15 tests pass unchanged, confirming the refactor is behavior-preserving. `Hoy.tsx` uses
the same helper plus the already-shared pure functions (`tituloDeOrden`, `veredictoDeOrden`,
`ventasFaltantesEnPalabras`, `progresoVentasEnPalabras`) and, for the per-product section, the
same `tituloDelPasoActual`/`quienLoHace` that `Tablero.tsx`'s `TarjetaProducto` uses (via
`componentes/resumen.tsx`). No CPA/break-even/rezago arithmetic added anywhere in the frontend —
every number is read straight from `por_que`/`_DECISIONES.json`/`Requisito`.

**Section 1 — stale-data banner.** Reads `/api/decisiones` (`_DECISIONES.json`): `rezago_dias`
`null` is treated as unknown/stale (never "fresh"), matching the brief. `rezago_dias > 2` renders
a destructive `Alert` (T1's new `components/ui/alert.tsx`) naming the date and day count, with a
button wired to the declared executor: `GET /api/acciones` → `nodo.ciclo.datos` ("Traer las
ventas de LucidSales", the `recopilar-lucidsales` skill's manifest entry) via
`api.pedirAccion(id, {}, false)`; the button is disabled (with the manifest's `motivo` as title)
if the action isn't `habilitada`, and no button is invented if the action is missing from the
manifest. Otherwise a single quiet line: "Datos hasta `<fecha>`."

**Section 2 — orders.** Reads `/api/ordenes` (same contract as `Ordenes.tsx`). Sorted with
`PAUSAR, ESCALAR, RENOVAR` first (fixed priority map, never a numeric comparison) and
`SEGUIR_MIDIENDO` collapsed under `components/ui/collapsible.tsx`, showing only the progress/
remaining-sales text per row. Each actionable order is a `Card` (T1's `components/ui/card.tsx`)
using the new `bg-estado-*`/`text-estado-*` tokens (T1 built them, unused until now) mapped
directly by ESTADO name (`ESCALAR`→`--estado-escalar`, etc. — no more indirection through
`Tono`). Confirm is "exactly as today's Órdenes screen": `Aprobar`/`Rechazar` buttons, disabled
unless `GET /api/acciones` → `nodo.ciclo.ordenes` is `habilitada` AND the order is `ejecutable` —
same as `Ordenes.tsx`, since that screen's buttons aren't wired to a mutation yet either (the
real per-order approval flow lives in `Trabajos.tsx`'s `OrdenParaAprobar`, gated behind a job's
`pendiente.tipo === "aprobacion"`; there was nothing further to reuse there without inventing a
new backend contract, which was out of scope). Empty state: a plain sentence, no empty cards.

**Section 3 — next step per product.** Reads `/api/productos` then, per product,
`/api/productos/{clave}` (`Flujo`) for the full `bloqueantes` list — same N+1-by-design pattern
`Tablero.tsx` already uses via `useQueries`, done here with one `useQuery` per row component
instead (simpler, same caching). Dense list (no TanStack Table — not warranted for 4 columns),
`flex-col` stacking under `sm:grid` for the 375px case. Shows the first blocker with its
`dueno` (falls back to `quienLoHace(ejecutor)` only if the row itself has no `dueno`) and a
"+N más" count; "Sin bloqueantes" when the list is empty. Each row links to `/producto/$clave`.

**New shadcn components added:** `card`, `alert`, `collapsible` (`pnpm dlx shadcn@latest add
card alert collapsible -y`) — no new npm dependencies beyond what T1 already installed.

**Verification:**
- `cd app/frontend && pnpm test` → 13 files, 72 tests passed (6 new in
  `src/pruebas/hoy.test.tsx`: fresh-data line, stale banner with date+days, unknown-rezago
  banner, actionable-before-SEGUIR_MIDIENDO ordering with the collapsed count, empty state, and
  next-step rows with blocker+owner / "Sin bloqueantes").
- `cd app/frontend && pnpm build` → `tsc -b && vite build` clean (waited for the parent's
  Playwright run to finish writing `dist` first, per the concurrency rule — its output file was
  already non-empty by the time this task started reading files).
- `pnpm exec playwright test --reporter=line` → 11 passed, 2 failed. Both failures are
  pre-existing and unrelated to T2 (confirmed against the parent's baseline run from before this
  task started, same two failures): `tablero.spec.ts` → "el estado de OVULOS_PURITY coincide con
  flujo.py" fails because the test calls `flujo.py --sin-escribir`, a flag `flujo.py`'s current
  CLI doesn't have (`unrecognized arguments: --sin-escribir`); `fases_2_3.spec.ts` → FASE 2
  heading not found for TINNIDROP. Neither test touches Hoy/`/productos`/`lenguaje.ts`. The new
  `e2e/hoy.spec.ts` and the two retargeted `tablero.spec.ts` tests pass, against the real
  `_DECISIONES.json` (`rezago_dias: 3` at the time of this run — confirms the stale-banner path
  renders with real data, not just the mock).
- Browser check (Chrome via the Browser pane, `pnpm dev` on :5173, no backend running so all
  three sections show the expected "No pude leer el sistema" error card — acceptable per the
  brief): desktop screenshot confirms sidebar + three sections render in order with correct
  spacing; 375×812 confirms `document.documentElement.scrollWidth === 375` (no horizontal
  scroll) and the sections stack cleanly. Real-data rendering (banner text, order cards, sorted
  states, next-step rows) was confirmed instead through the e2e run above, per the task's
  guidance not to start the real backend from this worktree.
- `cd app/backend && uv run pytest -q -k "ordenes or contratos or espeja"` → 14 passed (backend
  untouched by this task; ran the relevant subset instead of the full suite, which needs several
  minutes for the DBOS/workflow tests per T1's note).

**Deviations from the brief:** none. The parent's earlier Playwright run (using
`app/frontend/dist`) had already finished (10/12 passed, output file non-empty) by the time this
task read it, so no wait loop was needed before running `pnpm build`.

### T3 evidence (24-sep-2026)

Commits on `feat/p4-ui`:
- `d81a021` feat(frontend): products table with TanStack Table
- `44cc6cf` feat(frontend): product detail with URL-driven phase tabs

**`/productos` — the table.** New `src/pantallas/Productos.tsx` replaces `Tablero.tsx` (deleted,
along with `tablero.test.tsx`) as the `/productos` route's component. Installed
`@tanstack/react-table@8` (pinned to v8 on purpose — the current `9.x` on npm ships a different,
subscription-based `useTable` API under a new default export and moves the familiar
`useReactTable`/`getCoreRowModel` API behind a `legacy` entrypoint; v8 is the one that matches the
brief's reference implementation, openstatusHQ/data-table-filters) and the shadcn `table`
component. Columns: Producto (name + key, links to `/producto/$clave`), Fase (short code badge,
full sentence as `title`), Paso actual (human title + raw `nodo_actual`, plus a `rezago` chip when
that PRODUCT's own `flujo.py` motor reports > 2 days — the per-card signal `BannerRezago` used to
give in Tablero, now inline instead of a full banner), Estado, Esto lo frena (first bloqueante +
dueño, reusing the exact phrasing `Hoy.tsx`'s `FilaSiguientePaso` already uses — never recomputed
a second way), Sigue. Sorting via TanStack's own column headers (Fase/Estado etc., not
"bloqueante" — that one has no single sort key); a plain-text filter box matches product key, name,
fase or estado. "Nuevo producto" still links to `/nuevo`. Desktop renders the dense `<table>`;
below 768px it renders stacked `Card`s instead — picked by `useIsMobile()` (the same hook the
shadcn `Sidebar` already uses in T1), a JS decision, not a CSS `hidden`/`md:block` pair: the
Sidebar's own precedent (confirmed by rereading `barra_lateral.test.tsx`) avoids ever having two
copies of the same row in the DOM, which would otherwise break single-match queries in tests and
(as this task's own bug below shows) is worth avoiding for other reasons too.

**A real bug, not just a test artifact: clicks silently hanging on `/productos`.** Getting the
Playwright suite green here took most of this task's time. `pnpm test` and `pnpm build` were clean
early on, but `e2e/tablero.spec.ts`'s glosario test — clicking the `(i)` next to "Paso actual" —
hung for the full 60s test timeout with no error, no console output, nothing in the DOM to explain
it. Bisected with a disposable `e2e/diag.spec.ts` (deleted before finishing, never committed):
- First finding (real, fixed): the `(i)` (`Info`, from `componentes/ui.tsx`) was nested inside the
  column header's own sort-toggle `<button>` — two interactive controls, one inside the other, is
  invalid HTML. Browsers silently reshape the accessibility tree for nested buttons, and
  `getByRole('button', {name:...})` was resolving to the outer sort button wearing the inner one's
  label. Fixed by moving `Info` OUT as a sibling `<span>`, never inside the sortable `<button>`.
  This alone did not fix the hang.
- Second finding (the real bug): `page.mouse.up()` itself — not Playwright's actionability
  checks, not hit-testing (`elementFromPoint` was correct, hover worked, `trial: true` and
  `force: true` clicks both hung identically) — never resolved. A synthetic `dispatchEvent("click")`
  worked instantly; only real mouse-synthesized clicks hung. Bisected by disabling pieces of the
  page one at a time against the real backend (`uv run uvicorn`, `VITALCOM_BASE` pointed at this
  worktree): clicking the **unrelated, untouched** Sidebar's own "Toggle Sidebar" button hung too,
  on `/productos` only — identical code click-tested fine on `/producto/OVULOS_PURITY` and `/`.
  Removing the rendered `<Table>` (forcing the mobile card branch) did **not** fix it. Removing the
  `Input` did **not** fix it. Removing the `useReactTable(...)` call entirely did fix it — isolating
  the cause to the hook itself, independent of what it renders. Root cause:
  `getCoreRowModel()`/`getSortedRowModel()` were being called *inline inside the render* — copied
  straight from the common tutorial pattern — which TanStack Table's own docs warn against
  (it allocates a new row-model function every render); combined with `data` being a freshly
  allocated array every render too (the per-row `useQueries` results were being remapped inline,
  not memoized), a real native mousedown/mouseup sequence into this component reliably left the
  page's input pipeline stuck, though never with a thrown error, a console message, or (usually) an
  actual `page.on("crash")` event — just dead air. Fixed by hoisting both row-model calls to
  module-level constants (`CORE_ROW_MODEL`/`SORTED_ROW_MODEL`, called once) and by genuinely
  memoizing the row array (`useMemo` keyed on `productos.data` and the spread of each per-row
  query's `.data`, not on a fresh array reference every render). Confirmed fixed: the glosario
  test's real click now completes in under a second, live-verified again in the Browser pane
  (tooltip opens correctly), and a full single-worker Playwright run no longer has this failure.
  This is the kind of defect that never shows up in `pnpm test` (jsdom's `fireEvent.click` is
  synthetic and unaffected) — only a real click, in a real browser, finds it.

**`/producto/$clave` — tabs.** `ProductoDetalle.tsx` now renders a header (always visible: name,
fase badge + glossary, current step + owner, first blocker + owner — the exact fields the brief
named) and a shadcn `Tabs` with Resumen / Fase 1 / Fase 2 / Fase 3. Resumen is the screen's former
entire body (avisos, "para pasar de fase", bloqueantes, the node-by-node timeline) — moved
under a tab, not recalculated. Fase1/Fase2/Fase3 render the existing screens unmodified except for
removing their own now-redundant "← portafolio" breadcrumb / "Ver recorrido en el grafo" / "← Volver
a la ficha de {clave}" links (Fase3's "← Ver FASE 2" cross-link stays — `fases_2_3.spec.ts` asserts
it, and it is not chrome duplicated by the tabs). `Fase1.tsx`'s `useParams({from: "/producto/$clave/fase1"})`
became `useParams({strict:false})` — one line, needed so it can mount as the "Fase 1" tab's content
while the actual matched route is the bare `/producto/$clave` (see below); `Fase2`/`Fase3` already
used that pattern. All four `/producto/$clave[/faseN]` routes in `main.tsx` now point at
`ProductoDetalle`.

Active tab: an explicit `/faseN` suffix in the URL always wins; without one, the tab defaults to
the product's current phase (`flujo.py`'s `fase`, mapped F1→Fase 1 etc.), falling back to Resumen
while that query is still loading or for a fase outside F1/F2/F3 (PAUSADO, as VARICOSE). Resumen
has no URL distinct from the bare route, so choosing it explicitly (when the default landed on a
phase tab) needed one bit of local state (`tabManual`) that the URL always overrides the moment it
carries a phase suffix — covered by dedicated tests, not just asserted informally.
**Performance regression caught and fixed before it shipped:** the first version gated Fase1/2/3's
mount behind `ProductoDetalle`'s own `flujo.py` query (`if (flujo.isLoading) return <Cargando/>`
wrapped everything) — this doubled real latency for the legacy `/faseN` URLs (which used to mount
Fase1/2/3 directly, no wrapper query) and broke `fase1.spec.ts`/`fases_2_3.spec.ts`'s 5s heading
timeouts against the real backend. Fixed by only gating the header (a separate `Header` component)
and the Resumen tab's own content — Fase1/2/3 mount and fire their own queries immediately
whenever the URL names their phase, never waiting on the wrapper's query.

**Verification:**
- `cd app/frontend && pnpm test` → 13 files, 79 tests passed (11 new in `productos.test.tsx`:
  per-row fase/paso/estado/sigue text, bloqueante with owner, "Nada lo frena", per-row rezago chip
  with its title, text filter (match + empty state), row and "Nuevo producto" links, the glosario
  button, and a sort-toggle test that reorders two rows by clicking the Fase header once. Extended
  `producto-detalle.test.tsx` in place — same assertions as T2 left them, adapted to open the
  correct tab first — plus 5 new tests for URL-driven vs. default-phase tab selection and
  navigation).
- `cd app/frontend && pnpm build` → `tsc -b && vite build` clean, no type errors.
- `pnpm exec playwright test --reporter=line` (single worker, `--workers=1`, after the multi-worker
  run showed contention flakiness unrelated to this task — `ordenes.spec.ts`/`hoy.spec.ts` failing
  under load and passing alone, confirmed by rerunning them in isolation): **11 passed, 2 failed**,
  both on the pre-existing/known list — `tablero.spec.ts`'s `--sin-escribir` flag test, and
  `fases_2_3.spec.ts`'s FASE 2 test (heading now renders in time; it now times out one assertion
  later, on "Carriles Escalonados", same underlying real-backend-latency root cause the brief
  already named as known). `fase1.spec.ts` and the glosario test — both previously failing during
  this task's own debugging — pass cleanly now.
- Browser check (Chrome via the Browser pane, real backend on a throwaway port against this
  worktree, `pnpm build` output): desktop screenshot confirms the table, sorting, the rezago chip,
  and the glossary tooltip (clicked live, not just via Playwright) all render correctly; 375×812
  confirms `document.documentElement.scrollWidth === 375` (no horizontal scroll) with the mobile
  card layout; `/producto/TINNIDROP` confirms the header, the default "Fase 2" tab (matching its
  real `fase`), and clicking into "Resumen" all render as designed.
- `cd app/backend && uv run pytest` → not run this task (no backend files touched; T1/T2 already
  established the full suite's runtime exceeds this session's command timeouts).

**Authored lines** (`git diff --stat`, both commits, excluding `src/components/ui/*` — the
vendored shadcn `table.tsx`/`tabs.tsx`): 910 insertions, 532 deletions across 11 files (deleting
`Tablero.tsx` + its 187-line test accounts for most of the deletions). This is above the ~400-line
planning heuristic; per its own text this is advisory, not a gate — the two genuine sub-features
(the table, and the tab restructuring) each stayed close to a normal task's size on their own, and
the bulk of the overage is the bug investigation's fix plus the two tests files it required, not
scope creep. Delivery strategy (chain vs. single PR) is the parent orchestrator's call, not this
task's.

**Deviations from the brief:** none in scope. The nested-button and non-memoized-row-model fixes
above were not anticipated by the brief but were required to make the table it asked for actually
work with a real pointer, not just `fireEvent` in jsdom.

### T4 evidence (24-sep-2026)

**Product-decision stop, before any code.** The brief assumed a read-only owner script the
backend could shell out to on demand. Mapping `Ads/_TOOLS/gen_pl.py` (the actual implementation
of CONTABILIDAD.md's three views) and `gen_finanzas.py` found neither fit: `gen_pl.py` needs a
manual Dropi export (`--dropi <xlsx>`, weekly cadence, 60-day moving window, CONTABILIDAD.md §5 —
not an API pull) and had no machine-readable output; `gen_finanzas.py`'s zero-argument path *is*
automatic and already emits a CSV, but its own docstring calls it "CAPA 1 — LucidSales (lo que
los ADS atribuyen)" and warns the number can be inflated versus real cash — not one of the three
CONTABILIDAD.md views, and with no cohort-maturity concept at all. Stopped and asked the parent
instead of guessing. Decision (methodology over any other calculation): option (a), the real P&L
only — never `gen_finanzas.py`/`_FACT_SEMANAL.csv`, never ROAS, split into T4a/T4b.

**T4a** — `afa5325` feat(finanzas): read-only `--json` output for gen_pl.
`Ads/_TOOLS/gen_pl.py` gained a `--json` flag that serializes exactly the numbers already
computed for VISTA A (estado de resultados, economía unitaria) and VISTA B (caja), plus the
`preliminar` flag from the script's own `dias_cohorte_maduro` logic, into
`_AUDITORIAS/_PL_<ini>_<fin>.json` next to the existing `.txt`. No number changes, no new
calculations — every JSON field is a value the script already had a local variable for. With
`--json`, stdout carries only the JSON (needed for the app's `salida: "json"` runner contract,
which does `json.loads(stdout)`); without it, behavior is byte-for-byte as before. New
`Ads/_TOOLS/test_gen_pl.py` (unittest-style, matching `test_respaldo_productos.py`): builds a
synthetic Dropi xlsx with openpyxl, asserts the JSON numbers equal the VISTA A formula recomputed
from the module's own `C_DEVOL`/`C_ADMIN`/`C_OTROS`/`DIAS_MADURO` (never hardcoded), asserts
`preliminar` flips correctly for an old vs. a `today - 2 days` window, and asserts the `.json`
file is absent when `--json` is omitted.

**T4b** — `16ef2ea` + `8dcd2b7` feat(backend), `3206053` feat(frontend).
- `VISTAS/_MANIFIESTO.json`: new action `resultados.cargar_pl` (additive, `visibilidad: interna`,
  `nodo: null`, `precondicion: ninguna` — it isn't tied to any product's `flujo.py` node), comando
  `gen_pl.py --dropi {dropi} --json` plus `--banco`/`--cartera`/`--desde`/`--hasta` as optional
  bandera params. Validated clean against `gen_app.py --validar-manifiesto --json` (all 21 rules).
- `app/backend/vitalcom_app/main.py`: `POST /api/resultados/cargar` (multipart: `dropi` required,
  `banco`/`cartera` optional) saves each upload to its own `subidas.carpeta_temporal()` — never
  the same folder, since `subidas.guardar()` always names the file `subida<ext>` and three xlsx/pdf
  uploads would collide — then runs `resultados.cargar_pl` through the same
  `acciones.validar_parametros` → `workflows.encolar` → `esperar_resultado` path as
  `POST /api/productos` (alta de producto). `GET /api/resultados` serves the latest persisted
  `_PL_*.json` (`contratos.resultados()`, pure `glob`+`sorted`, no arithmetic — verified by the
  existing `test_sin_aritmetica.py` AST gate) as a typed `Resultados` model; 404 (not the generic
  503 `ContratoAusente` handler) when none exists yet, since "nobody uploaded an export" is a
  normal first-run state, not a system failure. `GET /api/resultados/historial` lists every
  persisted period oldest-to-newest for the trend chart — the only new surface beyond the
  original brief, added because `gen_pl.py`'s JSON is single-period and the brief asked for a
  trend chart; each point is a period the operator actually loaded, never an interpolation.
- `openpyxl` added as an `app/backend` **dev** dependency (`uv add --dev`) — the backend's
  runtime deps stay minimal; only the test suite needs to build a synthetic Dropi xlsx.
- New `app/backend/tests/test_resultados_api.py`: same pattern as `test_alta_por_la_app.py` — the
  toy system's real v7 manifest, with the REAL `gen_pl.py` copied over the generic stub and a
  seeded `_PARAMETROS_FINANZAS.csv`. Covers 404 with no prior upload, a full upload → JSON →
  `_AUDITORIAS/*.json`+`*.txt` on disk → `GET` round-trip, a missing-`dropi` 422, and the
  historial endpoint accumulating one entry per upload.
- `app/frontend/src/pantallas/Resultados.tsx`: KPI cards (`dashboard-01` `SectionCards` pattern)
  for venta bruta, margen logístico, margen de contribución and resultado neto, each carrying a
  "Preliminar" badge straight from `vista_a_cohorte.preliminar` (never recomputed); a Recharts
  line chart (`GET /api/resultados/historial`) of margen de contribución / resultado neto by
  period, with an explicit "still one period" note instead of a chart with a single point; a
  TanStack Table of `economia_unitaria` per product — copying `Productos.tsx`'s T3-safe pattern
  (module-level `CORE_ROW_MODEL`/`SORTED_ROW_MODEL`, a real `useMemo`) precisely because that bug
  (inline row-model calls hanging real clicks) is exactly the kind of defect a second table could
  reintroduce; below 768px it renders stacked cards via `useIsMobile()`, same as `Productos.tsx`.
  A permanent "Cargar export de Dropi" card (dropi/banco/cartera file inputs + desde/hasta) is
  always visible, with or without prior data, since `gen_pl.py` never runs on its own. Added 4
  glossary terms (`cohorte_preliminar`, `margen_logistico`, `margen_contribucion`,
  `resultado_neto`, `vista_cohorte`, `vista_caja`) so every money term on screen carries its `(i)`
  explanation, matching the existing glossary convention. Added shadcn `chart` + `label`
  components (Recharts is a new dependency, pulled in by the `chart` component).

**Deviations from the brief:** the `/api/resultados/historial` endpoint (see above) was not in
the original brief; added because the brief's own "chart of the trend by period" requirement had
no data source without it once `gen_finanzas.py` was ruled out. Nothing else added beyond scope.

**Verification:**
- `python -m pytest Ads/_TOOLS -q` → 40 passed before this task's changes (confirmed via
  `git stash`), **41 passed** after (`test_gen_pl.py`'s 3 unittest methods + 1 whole-file
  script-item, net +1 over baseline per pytest's own counting convention — see
  `Ads/_TOOLS/conftest.py`). No leftover `_PL_*.json`/`.txt` files in `PRODUCTOS/_AUDITORIAS/`
  after the run (`git status` clean).
- `cd app/backend && uv run pytest -q tests/test_resultados_api.py` → 4 passed. Also reran the
  gates most likely to catch a mistake in this task: `test_sin_aritmetica.py` (5 passed — the new
  `contratos.resultados()`/`historial_resultados()` do no arithmetic), `test_alta_por_la_app.py` +
  `test_fase1_api.py` (20 passed — the `UploadFile`-to-temp-folder path this task reused is
  unaffected), `test_acciones_api.py` (19 passed — the new manifest action didn't break argv
  resolution for existing ones), `test_workflows.py` (12 passed), `test_config.py` (5 passed).
  Full suite not run (T1's note: DBOS/workflow tests exceed this session's command timeouts).
- `cd app/frontend && pnpm test` → 14 files, **85 passed** (6 new in
  `src/pruebas/resultados.test.tsx`: empty state with a disabled submit button, KPI amounts with
  and without the Preliminar badge, the per-product table's red/green ganancia-por-venta coloring,
  the "needs a second period" chart note, and a real error rendered as `Problema` — never the
  empty state — for a non-404 failure).
- `cd app/frontend && pnpm build` → `tsc -b && vite build` clean, no type errors.
- `pnpm exec playwright test --reporter=line --workers=1` → **12 passed, 2 failed** (new
  `e2e/resultados.spec.ts` passes). Both failures are pre-existing and NOT caused by this task:
  `tablero.spec.ts`'s `--sin-escribir` flag (T2's known failure, unchanged) and
  `fases_2_3.spec.ts`'s FASE 2 test for TINNIDROP (T3's known failure — confirmed pre-existing by
  checking `_ESTADO_FLUJO.csv` at the parent commit `501bf38`, before any T4 change: TINNIDROP was
  already sitting at `F2.etapa-11`, not the FASE 3 the older `fases_2_3.spec.ts` test for it
  expects; unrelated to Resultados). The FASE 3 TINNIDROP sub-test flaked once (real-backend
  latency, same root cause T3 already named) and passed clean on rerun.
  Also fixed one bug in `resultados.spec.ts` itself before it passed: shadcn's `CardTitle` renders
  a `<div>`, not an `<h*>`, so `getByRole("heading", {name: "Cargar export de Dropi"})` never
  matches — switched to `getByText`.
- Browser check (Chrome via the Browser pane, `pnpm dev` on :5173, real backend, no export
  uploaded to this checkout): desktop screenshot confirms the empty-state alert and the upload
  card render correctly; 375×812 confirms `document.documentElement.scrollWidth === 375` (no
  horizontal scroll) via `javascript_tool` (a screenshot at that width tiled oddly in the pane —
  a capture artifact, not a real layout bug, ruled out by the `scrollWidth` check). The
  data-populated KPI/chart/table states are exercised by the unit tests above, not by a live
  upload in the browser (no real Dropi export available in this session).

**Authored lines** (`git diff --stat 501bf38..HEAD`, excluding vendored `chart.tsx`/`label.tsx`,
`esquema.d.ts`, and the two lockfiles): ~1281 insertions across 15 files. Above the ~400-line
heuristic — advisory, not a gate, per its own text — driven by one genuinely new screen (KPI
cards + chart + table + upload form) plus its two test files; no scope creep beyond the
`/historial` addition already explained above.

### T5 evidence (24-sep-2026)

Commits on `feat/p4-ui`:
- `610de13` feat(backend): read-only `/api/fanpages`
- `2d634b3` feat(frontend): Ajustes with accounts, fanpages and system section

**`_DIM_FANPAGES.csv` was absent from this worktree** — confirmed with `ls PRODUCTOS/` before
writing any code: it lives in `SISTEMA` on `feat/p2-simplificacion` (10 rows: `pagina_num`,
`pagina_nombre`, `identidad`, `rol`, `tono`, `logica`, `edad_orientacion`, `page_id`,
`productos_nicho` — read from that branch's real CSV to get the exact schema, never guessed).
Per the brief, the endpoint has to survive that: `contratos.cuentas()` raises `ContratoAusente`
(→ 503) when its CSV is missing, but the new `contratos.fanpages()` checks `ruta(*DIM_FANPAGES
).is_file()` first and returns `[]` instead — the only contract function in the file that
deliberately treats a missing CSV as a normal state rather than a system failure, since T5 is
the first screen expected to run before the operator ever declares that file in this checkout.

**Backend** — `GET /api/fanpages` (`app/backend/vitalcom_app/main.py`), new `FanPage` pydantic
model (`modelos.py`, all 9 CSV columns as `str`, same shape as `Cuenta`). New
`app/backend/tests/test_api_espeja_los_csv.py::test_fanpages_vacio_si_la_carpeta_no_tiene_el_csv`
asserts the empty-list path against this worktree's REAL absence of the file (not a fixture);
`test_fanpages_lista_el_csv_cuando_existe` uses the toy system (new
`sistema_de_juguete.escribir_fanpages()` helper + `COLUMNAS_FANPAGES`, not wired into `crear()`
by default — the toy system's baseline stays fileless too, matching the real default) to prove
rows mirror the CSV once one exists.

**Frontend.** `Ajustes.tsx` rewritten from the T1 link-grid into three `Card` sections:
1. **Cuentas publicitarias** — `GET /api/cuentas`, a plain shadcn `Table` (no TanStack — the
   brief's own call, these lists are small and static-shaped, not sortable/filterable data).
2. **FanPages** — `GET /api/fanpages`; three states: loading (`Cargando`), a real error
   (`Problema`, reused from `componentes/ui.tsx`), and empty (`Todavía no hay FanPages
   declaradas en _DIM_FANPAGES.csv.` — exact copy the brief specified) vs. populated rows.
3. **Sistema** — the same five legacy links T1 built (`Órdenes de hoy`, `Trabajos` with its
   pending-jobs `Badge`, `Salud del sistema`, `Guía`, `Nuevo producto`), plus a monospace
   `Corriendo sobre: <base>` line from `GET /api/sistema` — de-emphasized under its own card so
   it reads as "the machinery", not the screen's main content.
Both tables render twice — a `sm:hidden` stacked-card version and a `hidden sm:table` version —
picked by Tailwind's breakpoint (not `useIsMobile()` like `Productos.tsx`/`Resultados.tsx`):
plain CSS visibility was enough here since neither table has interactive row logic (sorting,
click-to-navigate) that would risk two live copies reacting to the same input; confirmed no
double-firing risk since these rows render nothing but static text.

**Types.** Regenerated `src/api/esquema.d.ts` via `pnpm dlx openapi-typescript` against a
throwaway backend on port 8010 (port 8000 turned out to be occupied by an unrelated app on this
machine, "ViralRadar" — not a SISTEM component; picked a free port instead of touching it) with
`VITALCOM_BASE` forced to this worktree (auto-detection refuses to run from a linked worktree by
design). Diff is purely additive (+64 lines, the new `FanPage` schema + its route/operation
entries) — no existing type changed shape. Added `FanPage` export + `api.fanpages()` to
`cliente.ts`, same pattern as `Cuenta`/`api.cuentas()`.

**Verification:**
- `cd app/backend && uv run pytest -q tests/test_api_espeja_los_csv.py` → 12 passed (2 new).
  Also reran `tests/test_sin_aritmetica.py` (5 passed — `contratos.fanpages()` does no
  arithmetic, just an `is_file()` check and a CSV read).
- `cd app/frontend && pnpm test` → 15 files, 90 passed (5 new in `src/pruebas/ajustes.test.tsx`:
  cuentas rows, FanPages empty state, FanPages rows, the five system links + the base-folder
  line, and the Trabajos badge counting only entries with a non-null `pendiente`). Fixed one
  assertion mid-task: `findByText` on a value that appears in both the mobile-card and the
  desktop-table markup at once (jsdom doesn't hide either by CSS) throws on multiple matches —
  switched to `findAllByText`/`getAllByText` where a value can legitimately appear twice.
- `cd app/frontend && pnpm build` → `tsc -b && vite build` clean, no type errors.
- `pnpm exec playwright test --reporter=line --workers=1` → **13 passed, 2 failed** (new
  `e2e/ajustes.spec.ts` passes; both failures are the same pre-existing ones T2/T3 already
  named: `tablero.spec.ts`'s `--sin-escribir` flag and `fases_2_3.spec.ts`'s "Carriles
  Escalonados" timeout for TINNIDROP). One bug caught and fixed before it passed: `ajustes.spec.ts`
  first used `getByRole("heading", ...)` for the three `CardTitle`s, which shadcn renders as a
  `<div>` — the exact same gotcha T4 already hit and documented for `resultados.spec.ts`; switched
  to `getByText(..., { exact: true })`.
- Browser check (Chrome via the Browser pane, `pnpm dev` on :5173, no backend on that port — same
  accepted state as T1-T4's browser checks): desktop screenshot confirms the three cards render
  in order with the expected `Problema` cards (no backend reachable); 375×812 confirms
  `document.documentElement.scrollWidth === 375` (no horizontal scroll), cards stack cleanly.
  Real-data rendering (cuentas rows, the FanPages empty-state copy, the system links, the base
  line) was confirmed instead through the Playwright run above, against the real backend and this
  worktree's real (fanpages-less) `PRODUCTOS/` — not started as a manual second backend on :8000,
  per the task's instruction not to touch the SISTEM `app-api` launch config or the unrelated
  process already using that port.

**Deviations from the brief:** none. `_DIM_FANPAGES.csv` being absent here was anticipated by the
brief itself ("Check whether the file exists... If an endpoint doesn't exist, add..."); handled
exactly as specified, nothing extra added beyond the read-only endpoint and the three sections.

**Authored lines** (`git diff --stat f6a920f..HEAD`, excluding the generated `esquema.d.ts`
diff): ~330 insertions across 7 files. Within the ~400-line heuristic.

## Next step
P4 feature complete; pending operator decisions: push + PR chain PR1–PR5 into `feat/app-web`,
then merge `feat/app-web` into the main line; acceptance test = operate a full day without the
chat.
