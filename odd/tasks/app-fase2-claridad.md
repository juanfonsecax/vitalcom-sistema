# Feature: app-fase2-claridad

## Objective
The operator reads in one glance where a product is and what to do next. No paragraphs where a
decision line is enough.

## Evidence (exploration 2026-10-05; the operator's app = `iniciar.bat` from SISTEMA = main code)
- Hoy card `TarjetaOrdenDelDia` (app/frontend/src/pantallas/Hoy.tsx:236, 311-313) prints the full
  `bloqueo_fase` sentence from decidir.py:877-901 as "Qué falta para escalar". Same at
  Ordenes.tsx:402-404. Short structured data already exists: `GET /api/productos` (fase,
  nodo_actual, siguiente_ejecutor) is already queried by Hoy (Hoy.tsx:770); `Productos.tsx:79`
  has `bloqueanteEnPalabras` / `quienLoHace` / `tituloDelPasoActual`.
- Fase2.tsx: header 144-146, chip "X de N conceptos listos" 155-159, "Qué hacer ahora" 200-204
  (not at the top). Count = `_DIM_CREATIVOS.csv` rows GENERADO|PUBLICADO (contratos.py:~714, 802);
  N = sum of fase-2 brazo A + B `anuncios_por_conjunto` in `_PARAMETROS_PUBLICACION.csv` (=10).
- CLEARSTEM: 5 GENERADO (RESISTENCIA_INSULINA_SOP, brazo empty, none published), brazo B never
  fabricated. The chip does not say what is missing or who produces it.
- Colors: backend-decided semáforo + Chip tones; operator likes them. Out of scope.

## Scope
Frontend Hoy.tsx, Ordenes.tsx, Fase2.tsx (+ shared helpers in lenguaje.ts if needed), backend
contratos.fase2_detalle / modelos only if a field is missing, and their tests.

## Tasks
- [x] T1 Hoy/Ordenes card: one status line (fase · paso · trabado por · lo hace); long
      `bloqueo_fase` behind a collapsed "¿Por qué?" (route: delegated writer)
- [x] T2 Fase2: "Qué hacer ahora" first, under a one-line phase status; concepts chip says how
      many are missing and who fabricates them (route: delegated writer)

## Checks
TDD on. Frontend: `pnpm --dir app/frontend test` (vitest) + `pnpm --dir app/frontend build`;
backend: `app/backend/.venv/Scripts/python.exe -m pytest -q` on touched test files.

## Progress
- Delegated writer (sonnet), 3 rounds after real-data checks on port 8010. RED observed each round.
  Frontend 181 tests + build OK; backend touched tests 49 passed; Ads/_TOOLS 61 passed;
  verificar_guia_madre clean. Real data: CLEARSTEM "Trabado: faltan 5 conceptos — Lo hace:
  Fábrica de conceptos"; header and Hoy rows no longer contradict the card.
- Added `falta` templates to all 44 FLUJO.json requirements (flujo.texto_falta is the owner).

## Found during verification (out of scope, next tasks)
- `_ESTADO_ANGULOS.csv` stale since 2026-09-30: perfilar_angulos.py is not in ciclo_diario.py,
  so the angle cards' "Orden del motor" disagreed with _DECISIONES.json.
- Daily cycle ROJO since 2026-10-05 09:34: ingerir_lucidsales_control refuses because daily
  files 2026-09-20/22..27 were loaded as rol=CONTROL besides the weekly CONTROL 09-21..27.
