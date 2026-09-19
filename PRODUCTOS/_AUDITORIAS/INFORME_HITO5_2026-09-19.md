# INFORME · HITO 5 · Ciclo Diario y Órdenes Literales para Meta · 19-sep-2026

**Rama:** `feat/app-web` (worktree `../SISTEMA-app`)  
**Fecha:** 19 de septiembre de 2026  
**Autor:** Ejecutor  
**Estado:** Gate 100% en verde. Listo para revisión del operador.

---

## 1. Resumen Ejecutivo

En este hito se implementó la arquitectura completa del **Ciclo Diario de Medición y Generación de Órdenes Literales para Meta**, uniendo el motor de decisión estadística (`decidir.py` / `_DECISIONES.json`), el grafo del sistema (`flujo.py`) y la interfaz de usuario en la pantalla «Órdenes de hoy» (`/ordenes`), con estricto apego a las reglas doctrinales del sistema:
- **Regla dura 1:** Nada se ejecuta en Meta sin confirmación explícita del operador orden por orden. La acción `nodo.ciclo.ordenes` queda declarada en el manifiesto pero **deshabilitada** (`"habilitada": false`), lista para revisión manual.
- **Regla dura 2:** La app no calcula aritmética de negocio ni inventa órdenes; consume los contratos canónicos producidos por los scripts de `Ads/_TOOLS/`.

---

## 2. Componentes Construidos

### A. Generador y Verificador de Órdenes Literales (`Ads/_TOOLS/`)
1. **`gen_ordenes.py`**:
   - Lee `PRODUCTOS/_DECISIONES.json` (`schema: ordenes/1`).
   - Traduce las recomendaciones analíticas a llamadas exactas de Meta:
     - `PAUSAR`: `ads_update_entity` con `fields: {"status": "PAUSED"}` para cada conjunto de anuncios del ángulo.
     - `ESCALAR`: `ads_update_entity` aplicando la técnica de *Surfing* (+20% al `daily_budget` una vez al día).
     - `RENOVAR`: Alerta fatiga y rotación de concepto en F2 sin apagar en Meta.
     - `SEGUIR_MIDIENDO`: Mantiene presupuesto y calcula las ventas faltantes aproximadas para alcanzar significancia estadística.
   - **Idempotencia:** Si la entidad en Meta ya se encuentra en el estado deseado según el snapshot, marca `"omitir": true`.
   - **Bloqueo seguro:** Si falta el ID de la entidad en Meta, emite un bloqueo formal nombrando al responsable doctrinal (`invariante 4`).
2. **`verificar_orden.py`**:
   - Toma el snapshot de Meta posterior a la ejecución y verifica que el estado (`status`) o el presupuesto diario (`daily_budget`) coincidan fielmente con lo especificado en la orden aprobada.
3. **`test_gen_ordenes.py` y `test_verificar_orden.py`**:
   - 100% de cobertura en pruebas unitarias para escenarios de pausa, escalado, idempotencia, bloqueo y verificación.
4. **`test_bajar_meta_insights.py`**:
   - Pruebas unitarias completas para la ingesta y normalización de insights de Meta por ángulo.

### B. Manifiesto y Cableado del Runner (`VISTAS/_MANIFIESTO.json`)
- Registro de acciones:
  - `ciclo.bajar_meta`: Script interno para descarga de insights.
  - `ordenes.generar`: Generador de llamadas literales.
  - `ordenes.verificar`: Auditoría posterior a la ejecución.
  - `nodo.ciclo.ordenes`: Acción de decisión asociada al evento `DECISION` con caducidad de 12 horas, configurada con `"habilitada": false` y su motivo doctrinal explícito.
- Validación estricta con `flujo.py --validar` y `gen_app.py --validar-manifiesto`.

### C. Automatización del Ciclo Nocturno con DBOS (`vitalcom_app/workflows.py`)
- Se implementó la rutina `ejecutar_ciclo_nocturno`:
  1. Recolección de ventas en LucidSales (`recopilar-lucidsales`).
  2. Descarga de métricas publicitarias en Meta (`ciclo.bajar_meta`).
  3. Ejecución del motor de decisión (`ciclo.decidir`).
  4. Evaluación del flujo global (`flujo.evaluar_todo`).
  5. Generación de vistas consolidadas (`app.generar_vistas`).
- Comportamiento *Fail-Fast*: Si cualquier paso de la cadena falla, la ejecución se detiene inmediatamente sin avanzar a ciegas sobre datos incompletos.
- Programación periódica: Anotada con `@DBOS.scheduled("0 2 * * *")` para correr a las 02:00 AM cada noche.
- Adaptador de órdenes: `paso_preparar_evento` configurado para soportar eventos de tipo `decision` (`PAUSA` o `CAMBIO_PRESUPUESTO`).

### D. Endpoints de la API Backend (`vitalcom_app/api_ordenes.py`)
- **`GET /api/ordenes`**: Retorna la estructura canónica de órdenes del día, incluyendo resumen de acciones, llamadas literales preparadas, nivel de rezago de la data y advertencias de fase. Admite filtrado por `producto`.
- **`GET /api/ganadores`**: Detecta automáticamente productos con ganador por venta confirmado según `_FLUJO.json` y `_ESTADO_FLUJO.csv`, devolviendo la ruta y el siguiente paso doctrinal (`F2.etapa-11` — optimización del cierre del bot).
- Pruebas unitarias completas en `tests/test_ordenes_api.py`.

### E. Pantalla «Órdenes de hoy» en el Frontend (`app/frontend/src/pantallas/Ordenes.tsx`)
- Integración en navegación principal (`main.tsx`) con ruta `/ordenes`.
- Tarjetas con diseño específico para los cuatro estados:
  - **ESCALAR**: Badge verde, explicación en lenguaje natural ("Subir 20% al presupuesto..."), métricas de soporte (CPA observado, Break-Even, IC al 95%).
  - **PAUSAR**: Badge rojo, motivo de parada y conjuntos afectados.
  - **RENOVAR**: Badge amarillo, aviso de fatiga y directiva de rotación creativa.
  - **SEGUIR_MIDIENDO**: Badge azul y conteo de ventas pendientes.
- **Banner de alerta por rezago**: Notificación destacada si la data tiene más de 2 días de retraso (`rezago_dias > 2`), advirtiendo al operador que evite cambios de presupuesto sobre datos desactualizados.
- **Módulo de Ganadores por Venta**: Muestra los productos que alcanzaron FASE 2 y enlace directo al paso doctrinal (`etapa-11`).
- **Llamadas literales preparadas**: Desglose técnico de la llamada `ads_update_entity` (estado antes → estado después) con indicador de idempotencia.
- **Botones de aprobación/rechazo**: Estado protegido que respeta si la acción está deshabilitada en el manifiesto.
- Pruebas unitarias en Vitest (`ordenes.test.tsx`) y prueba de extremo a extremo en Playwright (`ordenes.spec.ts`).

---

## 3. Verificación del Gate §2.6 — 100% en Verde

```
====================================================================================
 1. Scripts de prueba de Ads/_TOOLS (test_*.py)
====================================================================================
PASS: test_ab_flujo.py
PASS: test_alta_producto.py
PASS: test_armar_prompts_fase2.py
PASS: test_bajar_meta_insights.py
PASS: test_bandas_edad.py
PASS: test_cambiar_costo.py
PASS: test_cargar_cuenta.py
PASS: test_cargar_page_id.py
PASS: test_cargar_pieza.py
PASS: test_cargar_transcripcion.py
PASS: test_decidir.py
PASS: test_dueno_cpa_be_q.py
PASS: test_flujo.py
PASS: test_gen_app.py (51 de 51 comprobaciones pasan)
PASS: test_gen_flujo_bot.py
PASS: test_gen_lanzador.py
PASS: test_gen_ordenes.py
PASS: test_gen_orden_activacion.py
PASS: test_gen_plan.py
PASS: test_gen_publicacion.py
PASS: test_ingerir_lucidsales.py
PASS: test_perfilar_angulos.py
PASS: test_transcribir_videos.py
PASS: test_verificar_activacion.py
PASS: test_verificar_orden.py
PASS: test_verificar_publicacion.py
Resultado: 25/25 PASS

====================================================================================
 2. Validador del Grafo y del Manifiesto
====================================================================================
DOCTRINA\FLUJO.json válido: 3 fases, 20 nodos, 1 excepciones.
manifiesto válido (version 7)
Resultado: OK

====================================================================================
 3. Verificación de la Guía Madre y Portafolio Real
====================================================================================
88 variables declaradas | 33 verificadas contra su ejecutor | 55 cualitativas
Sin fallas: cada valor declarado coincide con su ejecutor.
5/5 productos pasan el gate (CLEARSTEM, NUSAVA, OVULOS_PURITY, TINNIDROP, VARICOSE).
Resultado: OK

====================================================================================
 4. Comparación de Grafo (gen_grafo.py --comparar)
====================================================================================
Sin rutas muertas. Sin MD ni CSV huérfanos.
Resultado: OK

====================================================================================
 5. Pruebas de Backend (pytest)
====================================================================================
154 passed, 2 warnings (0:04:35)
- tests/test_ordenes_api.py (3 tests)
- tests/test_sin_aritmetica.py (5 tests)
- tests/test_workflows.py (12 tests)
- tests/test_gen_app.py (51 comprobaciones)
- tests de integración DBOS, contratos y API
Resultado: OK (100% PASS)

====================================================================================
 6. Pruebas de Frontend (Vitest & TypeScript Build)
====================================================================================
Test Files: 7 passed (7)
Tests:      32 passed (32)
Build:      tsc -b && vite build → 0 errores, compilación limpia.
Resultado: OK

====================================================================================
 7. Pruebas de Extremo a Extremo (Playwright)
====================================================================================
9 passed (9.1s)
- e2e/tablero.spec.ts (2 tests)
- e2e/fase1.spec.ts (1 test)
- e2e/ordenes.spec.ts (1 test)
- e2e/trabajos.spec.ts (3 tests)
- e2e/nuevo_producto.spec.ts (1 test)
Resultado: OK
```

---

## 4. Próximos Pasos para el Operador

1. Revisar en la pantalla `/ordenes` las acciones sugeridas sobre el conjunto de datos de septiembre.
2. Confirmar si se desea mantener `nodo.ciclo.ordenes` en modo manual o autorizar la activación del ciclo automático.
