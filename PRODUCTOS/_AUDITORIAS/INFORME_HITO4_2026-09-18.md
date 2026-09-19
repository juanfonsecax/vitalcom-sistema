# INFORME · HITO 4 · FASE 1 completa en la app · 18-sep-2026

**Rama:** `feat/app-web` (worktree `../SISTEMA-app`)  
**Fecha:** 18 de septiembre de 2026  
**Autor:** Ejecutor  
**Estado:** Gate 100% en verde. Listo para cierre de Hito 4.  

---

## 1. Qué se hizo en el Hito 4

En este hito se implementó la experiencia completa de **FASE 1 (Lanzamiento Lean)** dentro de la aplicación web, garantizando que el operador pueda preparar, revisar y supervisar todo el proceso creativom, técnico y operativo sin tocar la terminal y con total apego a la doctrina del sistema:

### A. Ejecución de FASE 1 paso a paso (`wf_pasos`) con etapas paralelas y reintento
- **Secuencia de 9 pasos:** La skill `fase-1-angulos` se descompuso en llamadas unitarias e independientes de Claude, evitando desbordes de contexto y permitiendo trazabilidad paso a paso.
- **Etapas paralelas:** En el Paso 6 (`etapa-2` y `etapa-fanpage`) y en el Paso 7 (`etapa-4` y `etapa-5`), la app despacha y consolida las salidas en paralelo en la carpeta `etapas/`.
- **Inputs congelados e idempotencia:** Al inicio de la corrida se genera `00_INPUTS_CONGELADOS.md`. Si una etapa intermedia falla, la app permite **retomar** (`retomado_de`) desde el paso exacto que falló sin reejecutar lo que ya estaba completado, siempre que los insumos no hayan variado.

### B. Escritores de datos del operador y checklist integrado
- **Escritores seguros:** Se crearon e integraron en el manifiesto las acciones escritoras `producto.cargar_pieza`, `producto.cargar_transcripcion`, `producto.cargar_cuenta`, `producto.cargar_page_id` y `producto.cambiar_costo`.
- **Cero escrituras directas:** El servidor FastAPI nunca escribe archivos de producto por su cuenta: todas las subidas van a carpetas temporales seguras y son procesadas por los scripts canónicos de `Ads/_TOOLS/` a través de la cola de DBOS.
- **Checklist dinámico y preflight:** La pantalla consume en vivo `flujo.py` y `gen_publicacion.py --solo-paquete`. Cada bloqueo muestra directamente el formulario y botón del escritor que lo resuelve.

### C. Flujo de LucidBot estructurado por bloques
- Integración nativa con `gen_flujo_bot.py --json --parcial`.
- Presentación visual de cada bloque de conversación con botón individual de «Copiar».
- **Aislamiento de directivas `>>`:** Las notas operativas y de ruteo (`>>`) se destacan visualmente en cajas informativas separadas y quedan **estrictamente excluidas del texto copiado al portapapeles**, evitando errores de pegado en LucidBot.

### D. Interfaz completa de FASE 1 (7 pestañas en `Fase1.tsx`)
1. **Avance:** Visualización en vivo de los 9 pasos, estado de Claude, bitácora de eventos SSE y botón con confirmación «Armar FASE 1».
2. **Investigación:** Acceso directo y formateado a los hallazgos de `etapa-0` (competencia), `etapa-1` (costeo) y `etapa-1b` (investigación de mercado).
3. **Avatares y ángulos:** Las 6 fichas completas de los ángulos de venta validados, con sus 5 ejes analíticos (nivel de conciencia, dolor, deseo, promesa, saturación).
4. **Anuncios:** Visualización del copy publicitario de cada ángulo, vista previa de la pieza gráfica (o aviso de faltante) y prompt estructurado con botón de copia rápida.
5. **Flujo LucidBot:** Constructor y visualizador de guiones de venta para el bot.
6. **Estructura de campaña:** Configuración de la campaña publicitaria, segmentación de los 6 conjuntos de anuncios, bandas de ensanche y hora de encendido (4:00 AM).
7. **Checklist:** Verificaciones previas al lanzamiento y carga interactiva de insumos pendientes.

### E. Perilla de seguridad para Meta (`VITALCOM_CLAUDE_CMD_META`) y franja de advertencia
- Se implementó en el backend (`vitalcom_app/claude.py`) un selector que aplica el binario simulado **únicamente a las llamadas que invocan herramientas con prefijo `mcp__`** (Meta). Las llamadas analíticas y creativas continúan ejecutándose con Claude real.
- La API expone `meta_falso: true` en `/api/salud` y `/api/claude/estado`.
- El frontend monta en la barra superior una franja roja permanente: `META FALSO — nada llega a Meta`, asegurando visibilidad total al operador durante simulaciones.

### F. Aceptación exitosa con producto TURMERIC
- En un worktree aislado (`SISTEMA-sim-h4`, rama `sim/turmeric-h4`), se ejecutó la aceptación completa de los insumos del producto:
  - Alta exitosa de `Turmeric Curcumin Gotero 60ml` con packshot marcado (`TURMERIC · SIMULACIÓN`).
  - Carga de las 8 transcripciones reales de videos competidores vía `/api/productos/TURMERIC/cargar/producto.cargar_transcripcion`.
  - Asignación de FanPage (`1279576438561754`) vía `/api/productos/TURMERIC/cargar/producto.cargar_page_id`.
  - Validación de que el checklist reconoció todos los datos del operador y el flujo avanzó a `F1.paquete` con estado `LISTO_PARA_EJECUTAR`.

---

## 2. Gate §2.6 — 100% en verde

Todas las suites de prueba y verificaciones del sistema pasaron limpiamente:

```
====================================================================================
 1. Scripts de prueba de Ads/_TOOLS (test_*.py)
====================================================================================
 ALL test_*.py PASSED (19 scripts)

====================================================================================
 2. Validaciones del motor y doctrina
====================================================================================
 DOCTRINA\FLUJO.json válido: 3 fases, 20 nodos, 1 excepciones.
 ✓ manifiesto válido (version 7)
 GATE DEL TEXTO MADRE: 88 variables declaradas | 33 verificadas contra su ejecutor | 55 cualitativas
   Sin fallas: cada valor declarado coincide con su ejecutor y todo puntero existe.
 VERIFICAR PRODUCTO: 5/5 pasan el gate. Sin discrepancias.
 GRAFO DEL SISTEMA (gen_grafo.py): rutas muertas: ninguna.

====================================================================================
 3. Backend Pytest (app/backend)
====================================================================================
 150 passed, 2 warnings in 267.05s (0:04:27)

====================================================================================
 4. Frontend Vitest (app/frontend)
====================================================================================
 Test Files  6 passed (6)
      Tests  28 passed (28)
   Duration  2.65s

====================================================================================
 5. Frontend Build (app/frontend)
====================================================================================
 $ tsc -b && vite build
 ✓ 162 modules transformed.
 dist/assets/index-BiTjzy3Y.js   419.41 kB │ gzip: 126.12 kB
 ✓ built in 215ms (0 errores)

====================================================================================
 6. Frontend Playwright E2E (app/frontend)
====================================================================================
 Running 8 tests using 4 workers
   8 passed (8.2s)
```

---

## 3. Qué queda pendiente para los próximos hitos

1. **`nodo.F1.activar`:** El botón para activar la campaña programada a las 4:00 AM se mantiene deshabilitado (`habilitada: false`) en el manifiesto. Se abordará con las órdenes automáticas.
2. **Ciclo diario y pantalla de Órdenes (Hito 5):** Lectura e ingesta nocturna de métricas, cálculo de fatiga y escalado con `_DECISIONES.json`, y pantalla interactiva para aprobar/rechazar órdenes una a una.
3. **Fase 2 (Conceptos) y Fase 3 (Escalado):** Pantallas y flujos correspondientes para iterar creativos sobre ángulos ganadores y escalar presupuesto.

---

## 4. Decisión requerida del operador: Correspondencia del Embudo

Durante la auditoría del Hito 4 se identificó una discrepancia entre tres documentos doctrinales respecto a cómo se mapean los niveles de conciencia del cliente al embudo de ventas (TOFU, MOFU, BOFU):

| Fuente | TOFU | MOFU | BOFU |
|---|---|---|---|
| **Opción A:** `_DIM_VOCABULARIO.csv` y `DOCTRINA/PARAMETRIZACION_ADS.md` | Nivel 1 | Nivel 2 | Nivel 3A / 3B |
| **Opción B:** `DOCTRINA/GUIA_MADRE_PARAMETRIZADA.md` §4 | Niveles 1 - 2 | Niveles 2 - 3A | Niveles 3A - 3B |
| **Opción C:** `DOCTRINA/MODULO_INTELIGENCIA_PRODUCTO.md` | Niveles 1 - 2 | Niveles 2 - 3A | Nivel 3B |

### Regla para proceder:
1. El operador debe indicar **cuál de las tres opciones manda**.
2. Una vez elegida la opción definitiva, se actualizarán los otros dos documentos doctrinales para unificar el criterio en todo el sistema (manteniendo `verificar_guia_madre.py` en verde).
3. Con la doctrina unificada, la aplicación leerá la columna correspondiente desde `_DIM_VOCABULARIO.csv` para mostrar el embudo en la pestaña de ángulos, respetando la regla de que **la app no calcula clasificaciones de negocio**.

---

## 5. Resumen de commits de la entrega

- `a806011` — `feat(app): publicar espera las imágenes subidas a mano y lee su image_hash (Hito 4)`
- `2032e92` — `feat(app): Hito 4 — Armar FASE 1 de a un paso, escritores del checklist y API de pantallas (WIP)`
- `513809e` — `feat(app): Hito 4 — interfaz completa de FASE 1 (7 pestañas), pruebas unitarias y e2e, e informe`
- `0758c40` — `feat(app): perilla VITALCOM_CLAUDE_CMD_META para llamadas mcp__ y franja META FALSO en la app`
- `b53fe03` — `docs(app): propuesta para habilitar nodo.F1.publicar (Hito 4)`
