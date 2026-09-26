# UI — dark-only mode and text contrast

## Objective
Make every text in the operator app readable. The app runs dark-only for now; light mode is
deferred to the structural UI redesign, where hardcoded colors get replaced by theme tokens.

## Problem / why
- ~390 hardcoded dark-palette classes (`text-zinc-*`, `bg-zinc-*`) mean light mode never worked
  (operator report 26-sep-2026). Fixing light now would touch every screen twice.
- In dark mode, muted text used `text-zinc-500/600` and `text-muted-foreground/70` on near-black:
  measured contrast 1.5–3.8:1 (WCAG AA minimum 4.5:1).
- "Nota de fase" in Hoy used `text-estado-seguir-foreground` (near-black) over a 10% amber tint:
  1.24:1, invisible.
- The `.dark` class was applied after mount, so the first paint was light (active tab flashed
  white-on-white).

## Scope (authorized 26-sep-2026: operator "dejemos la app oscura… hacé eso que dijiste")
Visual only, frontend only. Branch `feat/ui-oscuro-contraste` from `p3b/06-creativos`, isolated
worktree `SISTEMA-ui-oscuro` (the `SISTEMA-app` checkout had same-day commits from another session).
Aprobar/Rechazar stay disabled on purpose for non-executable orders ("Solo informativo").

## Config
- TDD: off (source: p4-ui.md, no project TDD config). Runners: `pnpm test`, `pnpm build`.
- RDD: off.

## Tasks
- [x] T1 — Dark fixed from first paint (`index.html`), theme toggle and `tema.ts` removed.
- [x] T2 — Contrast: `text-zinc-500/600` → `text-zinc-400`, `placeholder:text-zinc-600` →
  `placeholder:text-zinc-500`, `text-muted-foreground/70` → `text-muted-foreground`, Nota de fase
  → `text-estado-seguir`, amber count badge → dark text on `amber-500`.
- [x] T3 — Live contrast re-scan of all routes (12 routes + product tabs + Fase 1 sections): 24
  failing patterns → 3, all at 4.0:1 (white on sky-600 buttons, left as is).

## Checks
- `pnpm test`: 16 files, 95 tests passed. `pnpm build`: OK.
