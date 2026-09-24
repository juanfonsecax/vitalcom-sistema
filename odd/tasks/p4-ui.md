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

## Tasks
- [x] T1 — Shell: install shadcn/ui (Base UI), Linear-style tokens (light + dark), sidebar layout
  with Hoy / Productos / Resultados / Ajustes; existing screens mapped under the new nav (legacy
  ones under Ajustes). Route: delegated writer (2+ non-trivial files). Checks: pnpm test, pnpm
  build, e2e smoke, browser check desktop + mobile width.
- [ ] T2 — Hoy: stale-data banner · decidir.py orders with per-order confirm · flujo.py next
  step per product. Uses existing endpoints.
- [ ] T3 — Productos: table + product detail (angles, concepts, results); absorbs Fase1/2/3.
- [ ] T4 — Resultados: new backend endpoint reading the accounting layer, cohorts < 10 days
  flagged preliminary; KPI cards + charts.
- [ ] T5 — Ajustes: accounts, fanpages; system health, jobs and guide hidden here.

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

## Next step
T2 — Hoy: stale-data banner, decidir.py orders with per-order confirm, flujo.py next step per
product.
