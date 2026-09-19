# INFORME · HITO 6 · FASE 2, FASE 3 y el Ciclo de Fatiga · 19-sep-2026

**Rama:** `feat/app-web` (worktree `../SISTEMA-app`)  
**Fecha:** 19 de septiembre de 2026  
**Autor:** Ejecutor  
**Estado:** Gate 100% en verde. Listo para revisión del operador.

---

## 1. Resumen Ejecutivo

En este hito se completó el recorrido publicitario avanzado del sistema Vitalcom:
1. **FASE 2 (Testeo de Conceptos):** Se integró la visualización del ángulo ganador coronado por ventas reales, los carriles secundarios escalonados (~3 días de cadencia para ángulos #2 y #3 según `CALENDARIO_ESCALADO`), la galería de los 10 conceptos con sus blueprints de origen (`_CATALOGO_CONCEPTOS.md`), chips de embudo TOFU/MOFU/BOFU, prompts multimodales resueltos listos para copiar con un solo clic, y el botón de subida manual de piezas con validación de nombres canónicos y gate de calidad.
2. **FASE 3 (Escalado CBO y Expansión Horizontal):** Se incorporó el semáforo y evidencia del motor para el gate de entrada doctrinal: *«un concepto gana en 2 de 2; un ganador de 1 de 2 es ruido»*, la estructura de campaña 1-1-7 CBO con presupuesto centralizado a nivel campaña, y las estrategias de replicación por Post ID compartido, multicuenta publicitaria y multifanpage.
3. **Ciclo de Fatiga & Retorno a FASE 1:** Se formalizó la transición doctrinal en `DOCTRINA/FLUJO.json` y el motor `flujo.py` para permitir que un producto con ángulo agotado reinicie el ciclo en FASE 1 excluyendo de forma automática todos los ángulos históricos ya probados. Se creó el script canónico `Ads/_TOOLS/reingreso_f1.py` con sus pruebas unitarias, endpoint seguro en el backend y modales de confirmación en la app web.
4. **Spike de Renderizado & Estado de Tokens:** Se documentó formalmente el resultado de la investigación sobre `claude-in-chrome` en modo headless y la situación de consumo de tokens en la cuenta de Claude.

---

## 2. Nota Crítica: Hallazgo sobre Tokens de Claude y `claude-in-chrome`

Siguiendo la instrucción explícita del operador (*«dejemos la nota también de eso que encontramos»*), se deja constancia técnica y operativa de los dos hallazgos del Spike 0:

1. **Agotamiento de cuota de tokens mensual en Claude Code CLI:**
   - Durante la prueba de invocación en vivo vía `claude -p`, la API de Anthropic retornó error `api_error_status: 429`:
     ```json
     {
       "is_error": true,
       "api_error_status": 429,
       "result": "You've hit your monthly spend limit · raise it at claude.ai/settings/usage?from=cc_cli_limit_message · your weekly limit resets Sep 21, 8am (America/Bogota)"
     }
     ```
   - El límite mensual de gasto de la cuenta del operador fue alcanzado, impidiendo que el CLI de Claude ejecute comandos que dependan de llamadas vivas hacia la API de Anthropic hasta que ocurra la recarga o reinicio de ciclo.

2. **Incompatibilidad arquitectónica estructural de `claude-in-chrome` en Windows / Headless:**
   - La herramienta `claude-in-chrome` no es un servidor MCP accesible desde scripts CLI ni modo headless (`claude -p`).
   - Requiere la aplicación de escritorio interactiva de Claude y cuenta con restricción formal *(Mac and WSL only)* para la vinculación desktop-cli en Windows.

3. **Decisión y Solución Operativa Aplicada:**
   - La pantalla de FASE 2 de la app web paquetiza y presenta los **prompts multimodales completos** generados para los 10 conceptos con botón de copiado inmediato.
   - El operador puede tomar el prompt, pegarlo en la interfaz web de su preferencia (ej. ChatGPT Plus con GPT-4o / DALL-E 3 o Midjourney) donde sí cuenta con servicio activo, descargar la imagen resultante y subirla directamente a la app mediante el botón de carga implementado (`producto.cargar_pieza`).
   - El archivo se aloja con su nombre canónico exacto (`{PRODUCTO}_F2_C{XX}.png`), cumpliendo con la auditoría de calidad de medios.

*(Detalle completo en `PRODUCTOS/_AUDITORIAS/SPIKE_CHROME_HEADLESS_2026-09-19.md`).*

---

## 3. Componentes Construidos y Modificados

### A. Doctrina del Grafo y Motor (`DOCTRINA/` y `Ads/_TOOLS/`)
- **`DOCTRINA/FLUJO.json`**:
  - Declaración del bloque `reingreso` en las fases `F2` y `F3` apuntando al nodo destino `F1.etapa-0`.
  - Predicado formal de transición `{"csv": ["PRODUCTOS", "_EVENTOS.csv"], "donde": {"evento": "REINGRESO_F1"}}`.
- **`Ads/_TOOLS/flujo.py`**:
  - Función `_angulos_probados(env, pk)` para extraer el histórico de ángulos corridos en FASE 1 y FASE 2.
  - Actualización de `situar()` para priorizar el evento activo `REINGRESO_F1`, retornando al producto a F1 con la metadata de ángulos excluidos.
  - Actualización de `validar()` para auditar que el nodo destino del reingreso exista en el grafo.
  - Actualización de `generar_mermaid()` para representar la transición de fatiga como línea punteada hacia F1.
- **`Ads/_TOOLS/reingreso_f1.py`**:
  - Script canónico que registra el evento `REINGRESO_F1` en `_EVENTOS.csv` con escritor CSV real y delimitadores canónicos.
  - Soporta `--dry-run`, `--json`, `--motivo` y rechaza productos inexistentes.
- **`Ads/_TOOLS/test_reingreso_f1.py`**:
  - 4 pruebas unitarias cubriendo rechazo de duplicados, dry-run, escritura de evento y extracción de ángulos probados.
- **`Ads/_TOOLS/test_flujo.py`**:
  - Sección G incorporada: 3 pruebas que validan la transición de fatiga, el reposicionamiento en FASE 1 y el reporte de ángulos excluidos. 29 de 29 comprobaciones pasando.

### B. Manifiesto del Sistema (`VISTAS/_MANIFIESTO.json`)
- Registro formal de la acción `producto.reingreso_f1`:
  - Entrada: `producto_key` y `motivo` (con patrón regex `^[A-Za-z0-9ÁÉÍÓÚáéíóúñÑ .,_-]{5,200}$`).
  - Validación con `gen_app.py --validar-manifiesto` y 51/51 comprobaciones en `test_gen_app.py`.

### C. Backend API (`app/backend/vitalcom_app/`)
- **`vitalcom_app/contratos.py`**:
  - Funciones `_angulos_probados()`, `fase2_detalle()`, `fase3_detalle()` y `reingreso_f1()`.
  - Sin aritmética de negocio ni importación de librerías numéricas (pasa `test_sin_aritmetica.py` con 0 infracciones AST).
- **`vitalcom_app/api_fases.py`**:
  - `GET /api/productos/{pk}/fase2`: Resumen de FASE 2, ganador, carriles secundarios, conceptos y fatiga.
  - `GET /api/productos/{pk}/fase3`: Gate 2de2 con evidencia real del motor, estructura 1-1-7 CBO y expansión horizontal.
  - `POST /api/productos/{pk}/reingreso-f1`: Endpoint para ejecutar el retorno a F1 por fatiga.
- **`tests/test_fases_api.py`**:
  - Pruebas de integración sobre los tres endpoints usando `TestClient`.

### D. Frontend Web (`app/frontend/`)
- **`api/cliente.ts`**:
  - Tipos `Fase2Detalle`, `ConceptoFase2`, `CarrilSecundario`, `Fase3Detalle`.
  - Clientes API `api.fase2()`, `api.fase3()`, `api.reingresoF1()`.
- **`pantallas/Fase2.tsx`**:
  - Ganador coronado por ventas.
  - Carriles secundarios con cadencia escalonada (~3 días).
  - Galería de 10 conceptos con blueprints, chips de rol y prompts con botón de copiado.
  - Módulo de subida manual de imágenes.
  - Módulo de fatiga con modal de confirmación mostrando los ángulos excluidos.
  - Banner informativo cuando el reingreso a F1 ya está activo.
- **`pantallas/Fase3.tsx`**:
  - Semáforo del gate 2de2 (cumplido o pendiente) con la evidencia textual de `flujo.py`.
  - Tarjeta de estructura 1-1-7 CBO con presupuesto centralizado.
  - Tarjeta de expansión horizontal (Post ID, multicuenta, multifanpage).
  - Botón de retorno a F1 por agotamiento del escalado.
- **`pantallas/ProductoDetalle.tsx`**:
  - Botones de acceso directo a FASE 1, FASE 2 y FASE 3 en la ficha del producto.
- **Pruebas Frontend**:
  - `src/pruebas/fase2.test.tsx`: 4 pruebas unitarias (100% PASS).
  - `src/pruebas/fase3.test.tsx`: 3 pruebas unitarias (100% PASS).
  - `e2e/fases_2_3.spec.ts`: 2 pruebas Playwright E2E contra backend real (100% PASS).

---

## 4. Replay de Aceptación

Se ejecutó la prueba de replay doctrinal sobre `TINNIDROP`:
```bash
python Ads/_TOOLS/flujo.py TINNIDROP
```
**Resultado del Motor:**
- Estado: `FASE F2 — FASE 2 · TESTEO DE CONCEPTOS`
- Entrada a F2: `✓ PERDIDA_AUDITIVA (histórico 104v CPA Q65.5 ≤ BE Q93.4)`
- Entrada a F3: `✗ 1 campaña(s) de conceptos con data · se necesitan 2 para replicar`
- Nodo actual: `▶ F2.etapa-11 — Optimizar el CIERRE del bot hacia el ángulo ganador`
- Órdenes activas de fatiga: `[RENOVAR] ACCESIBILIDAD_MEDICO` y `[RENOVAR] NOCHES_SIN_DORMIR`

**Resultado en la App Web (`/producto/TINNIDROP/fase2` y `/producto/TINNIDROP/fase3`):**
- Muestra idéntico ángulo ganador, nodo actual `F2.etapa-11`, carriles secundarios para `ACCESIBILIDAD_MEDICO` y `NOCHES_SIN_DORMIR`, semáforo `⚠ GATE PENDIENTE` en FASE 3 con la justificación exacta del motor. Coincidencia del 100% entre CLI y Web.

---

## 5. Verificación del Gate §2.6 — 100% en Verde

| Verificación | Comando | Resultado |
|---|---|---|
| **1. Validación de grafo y doctrina** | `python Ads/_TOOLS/flujo.py --validar` | **PASS** (3 fases, 20 nodos, 1 excepciones) |
| **2. Validación del manifiesto v7** | `python Ads/_TOOLS/gen_app.py --validar-manifiesto` | **PASS** (Manifiesto válido versión 7) |
| **3. Gate del texto madre** | `python Ads/_TOOLS/verificar_guia_madre.py` | **PASS** (88 variables | 33 verificadas | 0 fallas) |
| **4. Verificación de productos** | `python Ads/_TOOLS/verificar_producto.py --todos` | **PASS** (5/5 productos reconcilian) |
| **5. Comparación del grafo** | `python Ads/_TOOLS/gen_grafo.py --comparar` | **PASS** (0 rutas muertas, base consistente) |
| **6. Pruebas unitarias del motor** | `python Ads/_TOOLS/test_flujo.py` | **PASS** (29/29 comprobaciones OK) |
| **7. Pruebas de reingreso F1** | `python Ads/_TOOLS/test_reingreso_f1.py` | **PASS** (4/4 pruebas OK) |
| **8. Suite backend pytest** | `uv run --no-sync pytest -q -p no:cacheprovider` | **PASS** (157 passed, 0 failed) |
| **9. AST libre de aritmética** | `pytest tests/test_sin_aritmetica.py` | **PASS** (5/5 comprobaciones AST limpias) |
| **10. Suite frontend Vitest** | `pnpm test` | **PASS** (9 suites, 39/39 pruebas OK) |
| **11. Compilación frontend** | `pnpm build` | **PASS** (`dist/` generado sin errores) |
| **12. Suite End-to-End Playwright** | `pnpm exec playwright test` | **PASS** (11/11 pruebas E2E en verde) |
