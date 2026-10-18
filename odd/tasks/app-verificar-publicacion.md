# Feature: app-verificar-publicacion

## Objective
The operator runs the whole publish-and-verify loop from the web app, without opening a Claude session.
First deliverable: a button "Ya publique la campana - verificar" that snapshots Meta (read-only Graph API),
runs the publication gate with `--ya-activo --escribir`, and reports the result in the app.

## Problem
On 2026-10-17 the operator published/recreated CLEARSTEM F2 campaign C by hand. The ad ids changed, one ad
was named "- Copia", and two ad sets were missing from `_DIM_CONJUNTOS.csv`. Fixing it needed a Claude session
(Meta MCP to dump the snapshot). `verificar_publicacion.py` now handles all three (commit 71ff412) but is only
reachable internally (`publicacion.verificar`, visibilidad interna, no `--ya-activo`).

## Constraints
- Read-only Meta access only: token `META_SYSTEM_USER_TOKEN` with `ads_read` (doctrine forbids `ads_management`).
- New app action = one entry in `VISTAS/_MANIFIESTO.json` (`acciones.lista`), validated by
  `python Ads/_TOOLS/gen_app.py --validar-manifiesto` (V1-V21). Command is `python Ads/_TOOLS/<script>.py`.
- CSVs are written with a real CSV writer (invariant 11). Spanish voseo in operator-facing text; code in English.
- Work-unit commits, conventional, no AI attribution.

## Authorized scope
Tasks T1-T8. Operator decision 2026-10-18: NO write-scoped Meta token; Meta writes stay on the MCP via Claude. CAMBIO_BOT form remains a proposal, NOT in scope.

## Tasks
- [x] T1 `Ads/_TOOLS/snapshot_meta.py` + test: read campaigns/ad sets/ads of one account via Graph (`ads_read`),
      write `Ads/_INGESTA/META/snapshot_{cuenta}_{brazo}.json` in the shape `verificar_publicacion.cargar_snapshot` reads.
- [x] T2 `Ads/_TOOLS/verificar_campana_publicada.py` + test: wrapper that takes `--producto --fase --brazo`, resolves the
      account from the package, runs T1, then the gate with `--ya-activo --escribir`, prints JSON.
- [x] T3 Manifest action `publicacion.verificar_publicada` (visibilidad boton, tiempo_max_s 120, escribe PRODUCTOS/ +
      Ads/_INGESTA/META/) + manifest validation passes + backend test.
- [x] T4 Frontend button on the Fase2 screen using `api.pedirAccion` + `ProgresoDelTrabajo`, with a vitest test.
- [x] T5 Audit report to the operator (done by two read-only mappers; summarized in chat).
- [x] T6 (accepted change 2026-10-18: writes to Meta stay on the MCP; the app only reads/verifies and warns when Claude is needed)
      `verificar_campana_publicada.py` / the gate: when the result needs a Meta write (e.g. '- Copia' to rename), return a structured
      `requiere_claude` item {motivo, pedirle_a_claude} with the exact Spanish sentence to ask Claude.
- [x] T7 `Ads/_TOOLS/control_d1.py` + test: per ad set launched in the last 3 days, Meta delivery (from _FACT_ENTREGA) vs LucidSales
      activity (from _FACT_VENTAS); flag CIEGO / SIN_ENTREGA with the same `requiere_claude` shape. Read-only. Report honestly any
      limitation (e.g. LucidSales messages null on same-day exports).
- [x] T8 App: show `requiere_claude` items only when present (no noise) on the Hoy screen and in the verify job result; vitest + backend test.

## Acceptance
- Running the button against GTR7 campaign C returns OK for 23/23 objects and no "- Copia".
- Unit tests for T1/T2 pass; `gen_app.py --validar-manifiesto` passes; backend + frontend suites for the touched areas pass.

## Progress
- Route per task: T1-T4 delegated to one writer (2+ non-trivial files); T5 done inline from read-only mapper reports.
- TDD: not enabled (no explicit configuration); functional checks above.
- Commits: T1 0452727 · T2 080692c (+ cbc1666 detalle fix) · T3 c10f2bb · T4 382bf5c · T6 f220113 (shared shape `Ads/_TOOLS/requiere_claude.py`) · T7 b092369 · T8 22e63c2.
- Mirror: Engram topic `odd/app-verificar-publicacion/tasks`.

## Verification evidence
- 2026-10-18 real run against GTR7 (read-only Graph, ads_read): `verificar_campana_publicada.py --producto CLEARSTEM --fase 2 --brazo C --sin-escribir --json` -> ok, 23/23 objects, no '- Copia'.
- Found and fixed in that run: sys.stdout capture closed the real buffer (commit a3e64ce, regression test added).
- Tests: test_snapshot_meta 7 OK, test_verificar_campana_publicada OK, manifest valid, backend 35 + frontend 219 (writer report).

## Next step
Feature complete. Meta writes stay on the MCP via Claude (operator decision 2026-10-18); the app warns with `requiere_claude` only when needed.
