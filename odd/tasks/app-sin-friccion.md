# Feature: app-sin-friccion (Block C)

## Objective
The operator only acts; the system decides and presents. Remove the places where the app shows
raw commands, concatenated engine strings or jargon, and bring old products up to the current
data contract.

## Evidence (exploration 2026-09-28)
- Doctrine: each winning angle gets its own FASE 2, staggered (~3 days apart, dedicated bot):
  `DOCTRINA/CALENDARIO_ESCALADO.md:25-30`, hard rule line 301. Losing angles: state per angle in
  `PRODUCTOS/_ESTADO_ANGULOS.csv` (perfilar_angulos.py), never read by the backend.
- `contratos.fase2_detalle` (contratos.py:502) uses the concatenated `observado` string of the F2
  gate as "ángulo ganador" and as fallback angle (contratos.py:559/586 → broken `comando_generar`).
  "Carriles escalonados" = ESCALAR/RENOVAR cells, unordered, fixed "~3 días" text.
- `armar_prompts_fase2.py PRODUCTO [ANGULO]` blocks on: `_DIM_ENVASE.csv` packshot (only TINNIDROP,
  OVULOS_PURITY have rows), active `_DIM_PRECIOS.csv` row, `PRODUCTOS/{slug}/_PERFIL_CREATIVO.json`
  (single angle). Not a manifest action; app shows the command as text.
- No packshot/envase writer; no per-product "datos faltantes" check; Resumen header has no image.

## Tasks
- [x] C1 FASE 2 per angle: all F1 angles with verdict; winners ranked #1 (in F2 now) / #2, #3
      (queued, staggered) by engine data; losers "apagado" (días sin gasto) or the engine's order;
      fatigue block shows the engine's concrete order; fix concatenated-string fallback.
      (route: delegated writer)
- [x] C2 Product start card: packshot photo on top of ProductoDetalle with upload (new manifest
      writer `producto.cargar_packshot` → Ads/<carpeta_media>/ + `_DIM_ENVASE.csv` row, declared
      marca/color/formato), and a deterministic "datos faltantes" check (read-only tool in Ads/_TOOLS)
      listing packshot, precio activo, page_id, cuenta, perfil creativo, referencia F1, each with its
      inline fix. (route: delegated writer)
- [ ] C3 "Generar prompts" button: manifest action for armar_prompts_fase2 on the #1 angle; blocking
      reasons in plain Spanish linking to the fix. (route: delegated writer)
- [ ] C4 Bring the 5 products up to date: identify packshots by viewing media, declare envase rows;
      ask operator only for data only they have. (route: parent)

## Constraints
Same as previous blocks: frontend never computes business data; one owner per datum; CSVs via csv
writer; doctrine states current rule; commits Conventional English without Co-Authored-By; never
commit nightly data churn; RDD off; TDD not configured.

## Progress / evidence
- C1 (2026-09-28, route: delegated writer, uncommitted): `flujo.py` now emits `angulos_ganadores`
  (gate `angulo_ganador` claves, ordered by `flujo.ranking_ganadores`; #1 = `armar_prompts_fase2.orden_ganador`,
  rest by ventas_acum desc). `contratos.angulos_de_fase2` joins _DECISIONES cells + _ESTADO_ANGULOS rows into
  `angulos` (roles ganador_activo / ganador_en_fila / perdedor / midiendo); `ganador_obs` no longer used as angle
  key (fallback = #1). Fase2.tsx: hero #1, "En fila", "Ángulos que no funcionaron", engine orders as "Qué hacer",
  gallery grouped by angle (default #1). Checks: pytest 204 passed; pnpm test 128 passed; pnpm build ok;
  playwright 16 passed; test_flujo.py 44/44. Live CLEARSTEM: #1 RESISTENCIA_INSULINA_SOP, #2 ANTI_FALSIFICACION,
  #3 MEDICOS_FALLARON, 3 losers "ya apagado (40-63 días)".
- C2 (2026-09-28, route: delegated writer, uncommitted): `cargar_packshot.py` (upsert `_DIM_ENVASE.csv` via
  upsert_fact; photo -> Ads/<carpeta_media>/<PK>_PACKSHOT.<ext by content>; different existing photo refused
  without --reemplazar, with it the old one is kept as `_ANTERIOR_AAAAMMDD`); manifest `producto.cargar_packshot`
  (+ `escritores_de_bloqueo.packshot`); `datos_producto.py` read-only (packshot, costo, precio ACTIVO, page_id,
  cuenta [EXTERNA is legit], perfil #1 in F2, referencia F1 in F1); `GET /api/productos/{pk}/datos`; header photo +
  "Para arrancar te falta" card (`componentes/arranque.tsx`). Checks: Ads/_TOOLS pytest 50 passed (48 + 2 scripts);
  backend pytest 208 passed; pnpm test 135 passed; pnpm build ok; playwright 16 passed; hook_csv --barrido exit 0;
  gen_app --validar-manifiesto valid. Live missing: TINNIDROP perfil #1 (PERDIDA_AUDITIVA), NUSAVA/CLEARSTEM/VARICOSE
  packshot, OVULOS_PURITY precio + page_id. Note: `python Ads/_TOOLS/gen_app.py` (no flags) regenerates VISTAS by design.

## Next step
C3.
