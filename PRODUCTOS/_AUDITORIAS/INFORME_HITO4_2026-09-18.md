# INFORME · HITO 4 · FASE 1 completa en la app · 18-sep-2026

Rama `feat/app-web` (worktree `../SISTEMA-app`). Sin tocar Meta, sin mergear, sin cambiar de rama la
carpeta real.

## Qué se entregó en el Hito 4

| Área | Entregable | Detalle |
|---|---|---|
| Frontend | `Fase1.tsx` (7 pestañas) | **Avance:** 9 pasos de `wf_pasos`, botón «Armar FASE 1» y reintento.<br>**Investigación:** salidas legibles de etapa-1b, etapa-1 y etapa-0.<br>**Avatares y ángulos:** las 6 fichas completas (5 ejes, nivel de conciencia, dolor, deseo, promesa, saturación) con advertencia explícita sobre el embudo sin clasificaciones arbitrarias.<br>**Anuncios:** copy por ángulo, visualización de pieza o aviso de faltante, prompt de imagen con botón Copiar.<br>**Flujo LucidBot:** render de bloques con botón Copiar; las instrucciones `>>` van visualmente aparte y **nunca entran al portapapeles**.<br>**Estructura de campaña:** campaña, conjuntos, presupuesto, bandas y lanzamiento 4 AM.<br>**Checklist:** preflight y bloqueos con escritores integrados (cuenta, page_id, piezas individuales, transcripciones). |
| Enrutamiento | `main.tsx` y `ProductoDetalle.tsx` | Ruta `/producto/$clave/fase1` y enlace directo «Pantalla FASE 1 →» desde el detalle del producto. |
| Backend & API | `main.py`, `modelos.py`, `fase1.py` | Endpoint `GET /api/cuentas` reflejando `_DIM_CUENTAS.csv`. Endpoints `/fase1/corrida`, `/fase1/campana`, `/flujo-bot`, `/checklist`, `/media` y `/cargar`. |
| Pruebas Frontend | `fase1.test.tsx` (Vitest) | 4 pruebas que congelan: instrucciones `>>` excluidas del portapapeles, renderizado de piezas faltantes en checklist, frase requerida sobre embudo y diálogo de confirmación antes de disparar ejecución. |
| Pruebas E2E | `fase1.spec.ts` (Playwright) | Abre `/producto/OVULOS_PURITY/fase1`, recorre las 7 pestañas, valida el contenido y comprueba cero llamadas POST (cero mutaciones). |
| Pruebas Backend | `test_api_espeja_los_csv.py`, `test_fase1_api.py`, `test_cola_y_bitacora.py` | Cobertura de `/api/cuentas`, escritores y bitácora. |

## Gate §2.6 — todo en verde

- **19 scripts de prueba en `Ads/_TOOLS/test_*.py`**: todos en verde.
- `python Ads/_TOOLS/flujo.py --validar`: válido (3 fases, 20 nodos, 1 excepción).
- `python Ads/_TOOLS/gen_app.py --validar-manifiesto`: manifiesto versión 7 válido.
- `python Ads/_TOOLS/verificar_guia_madre.py`: 88 variables declaradas, sin discrepancias.
- `python Ads/_TOOLS/verificar_producto.py --todos`: 5/5 productos reconcilian.
- `python Ads/_TOOLS/gen_grafo.py --comparar`: rutas muertas: ninguna.
- **Backend pytest**: **147 pruebas** pasando (0 fallas, 2 advertencias de librerías deprecadas).
- **Frontend vitest**: **26 pruebas** pasando (5 suites).
- **Frontend build (`pnpm build`)**: compila limpiamente (0 errores).
- **Frontend Playwright (E2E)**: **8 pruebas** pasando.

## Estado de las acciones de Meta

De acuerdo a la **Regla Dura 1**, `nodo.F1.publicar` permanece `habilitada: false` en `VISTAS/_MANIFIESTO.json`. La app prepara el paquete en modo biblioteca con los hashes que el operador sube a mano (según el spike de biblioteca), pero **no dispara llamadas reales a Meta sin autorización explícita**.

## Próximo paso (Hito 5)

Hito 5 de la hoja de ruta: Ciclo diario y pantalla de Órdenes (recolección nocturna, `_DECISIONES.json`, aprobación orden por orden y registro de eventos).
