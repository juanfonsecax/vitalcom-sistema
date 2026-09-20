# INFORME · HITO 7 · Cierre de la Fase Personal · 19-sep-2026

**Rama:** `feat/app-web` (worktree `../SISTEMA-app`)  
**Fecha:** 19 de septiembre de 2026  
**Autor:** Ejecutor  
**Estado:** Gate §2.6 100% en verde. Cierre formal de la fase personal.

---

## 1. Resumen Ejecutivo

En este hito se completó el cierre de la fase personal de la aplicación web según la hoja de ruta (`_ROADMAP/HOJA_DE_RUTA_APP.md`):

1. **Copia de seguridad automática diaria de `PRODUCTOS/`:**
   - Se construyó el script canónico `Ads/_TOOLS/respaldo_productos.py` con retención estricta de las últimas 30 copias (eliminación automática de las más antiguas).
   - Empaqueta en formato `.zip` fechado (`PRODUCTOS_YYYYMMDD_HHMMSS.zip`) fuera del repositorio.
   - Carpeta acordada con el operador: `C:\Users\juand\Documents\VITALCOM_RESPALDOS` (configurable vía parámetro `--destino` o variable de entorno `VITALCOM_RESPALDOS_DIR`).
   - Soporta `--dry-run`, `--json`, `--limite` y cuenta con suite unitaria completa (`Ads/_TOOLS/test_respaldo_productos.py`).
   - Acción declarada formalmente en `VISTAS/_MANIFIESTO.json` (`sistema.respaldo_productos`) y programada en DBOS (`@DBOS.scheduled("0 3 * * *")`) con función ejecutora durable `ejecutar_respaldo_productos()`.

2. **Actualización Doctrinal en `CLAUDE.md`:**
   - Se incorporó la fila formal de la app web en la tabla *«MAPA DE ARCHIVOS — QUIÉN ES DUEÑO DE QUÉ»*:
     ```markdown
     | **LA APP WEB** | `app/` (lee contratos, dispara ejecutores declarados en `VISTAS/_MANIFIESTO.json`) |
     ```
   - Verificado contra el motor de grafo: `gen_grafo.py --comparar` mantiene un delta de tokens prácticamente nulo (+29 tokens por el texto de la fila en frío, 0% de variación estructural) y confirma 0 rutas muertas, validando que `app/` no se carga en el contexto de los subagentes.

3. **Guía de uso de 1 página dentro de la App Web:**
   - Se diseñó la pantalla interactiva `app/frontend/src/pantallas/Guia.tsx` con vocabulario simple, claro y libre de tecnicismos para el operador.
   - Explica:
     - **Qué hace cada pantalla y botón:** Portafolio, Órdenes de hoy, Nuevo producto, Trabajos, Fases 1-3, Salud y Respaldos.
     - **Qué significa cada estado:** LISTO, BLOQUEADO, SEGUIR MIDIENDO, ESCALAR (+20%), RENOVAR y PAUSAR.
     - **Qué hacer si algo falla:** Reintentos en Trabajos, resolución de bloqueantes, advertencia sobre no tocar nombres directo en Meta y levantamiento del sistema.
   - Integrada en la barra de navegación superior y en el enrutador (`/guia`), con pruebas unitarias (`guia.test.tsx`) y prueba de punta a punta (`guia.spec.ts`) 100% en verde.

4. **Verificación de `iniciar.bat` y Servidor Integrado:**
   - Se comprobó la ejecución del lanzador `iniciar.bat`, que levanta el entorno con `uv run uvicorn`, compila el frontend en `dist/` si no existiera y abre automáticamente `http://localhost:8000`.
   - Se verificó que FastAPI sirve correctamente el SPA en `/`, la guía en `/guia` y la API interna en `/api/*`.

---

## 2. Componentes Construidos y Modificados

### A. Herramientas y Motor (`Ads/_TOOLS/`)
- **`Ads/_TOOLS/respaldo_productos.py`**:
  - Script ejecutable que comprime `PRODUCTOS/` hacia la carpeta externa de respaldos.
  - Gestiona rotación manteniendo las 30 copias más recientes.
  - Salida dual: texto amigable para CLI y JSON estructurado para la API de trabajos.
- **`Ads/_TOOLS/test_respaldo_productos.py`**:
  - 5 pruebas unitarias cubriendo compresión, contenido interno del zip, modo dry-run, poda de 35 a 30 archivos y reporte JSON.

### B. Manifiesto del Sistema (`VISTAS/_MANIFIESTO.json`)
- Registro de la acción `sistema.respaldo_productos`:
  - Ejecutor tipo `script`, comando `["python", "Ads/_TOOLS/respaldo_productos.py", "--json"]`, parámetro opcional `dry_run` tipo bandera, sin tocar Meta y con tiempo límite de 300 segundos.
  - Validado con `gen_app.py --validar-manifiesto` y 51/51 comprobaciones en `test_gen_app.py`.

### C. Backend API & DBOS (`app/backend/`)
- **`vitalcom_app/workflows.py`**:
  - Definición de `CRON_RESPALDO` (por defecto `"0 3 * * *"`).
  - Función `ejecutar_respaldo_productos()`.
  - Disparador `@DBOS.scheduled(CRON_RESPALDO)` activo con `VITALCOM_PROGRAMAR_RESPALDO=1` o `VITALCOM_PROGRAMAR_NOCTURNO=1`.
  - Ajuste de concurrencia en `_pedir_subida` asegurando que el estado `ESPERA_MEDIA` se publique antes del evento pendiente.
- **`tests/test_respaldo_accion.py`**:
  - 3 pruebas unitarias verificando la declaración de la acción en el manifiesto, la resolución del argv y la ejecución mockeada del workflow.
- **`tests/test_sin_aritmetica.py`**:
  - Verificación AST limpia (5/5 comprobaciones, 0 cálculos de negocio en el backend).

### D. Frontend Web (`app/frontend/`)
- **`src/pantallas/Guia.tsx`**:
  - Pantalla única de guía operativa para el operador.
- **`src/main.tsx`**:
  - Enlace «Guía» en el menú superior y ruta `/guia`.
- **`src/pruebas/guia.test.tsx`**:
  - 2 pruebas unitarias de renderizado de secciones y estados.
- **`e2e/guia.spec.ts`**:
  - Prueba Playwright que navega desde el menú hasta la guía y valida encabezados y contenido clave.

### E. Doctrina Central (`CLAUDE.md`)
- Fila agregada en el *Mapa de Archivos* asignando a `app/` la responsabilidad de la app web bajo contratos declarados.

---

## 3. Verificación del Gate §2.6 — 100% en Verde

| Verificación | Comando | Resultado |
|---|---|---|
| **1. Pruebas unitarias de herramientas** | `python Ads/_TOOLS/test_*.py` | **PASS** (100% de suites en verde) |
| **2. Validación de grafo y doctrina** | `python Ads/_TOOLS/flujo.py --validar` | **PASS** (3 fases, 20 nodos, 1 excepciones) |
| **3. Validación del manifiesto v7** | `python Ads/_TOOLS/gen_app.py --validar-manifiesto` | **PASS** (Manifiesto válido versión 7) |
| **4. Gate del texto madre** | `python Ads/_TOOLS/verificar_guia_madre.py` | **PASS** (88 variables | 33 verificadas | 0 fallas) |
| **5. Verificación de productos** | `python Ads/_TOOLS/verificar_producto.py --todos` | **PASS** (5/5 productos reconcilian) |
| **6. Comparación del grafo y tokens** | `python Ads/_TOOLS/gen_grafo.py --comparar` | **PASS** (delta tokens = 0 en contexto, 0 rutas muertas) |
| **7. Suite backend pytest** | `uv run --no-sync pytest -q -p no:cacheprovider` | **PASS** (160 passed, 0 failed) |
| **8. AST libre de aritmética** | `pytest tests/test_sin_aritmetica.py` | **PASS** (5/5 comprobaciones AST limpias) |
| **9. Suite frontend Vitest** | `pnpm test` | **PASS** (10 suites, 41/41 pruebas OK) |
| **10. Compilación frontend** | `pnpm build` | **PASS** (`dist/` generado sin errores) |
| **11. Suite End-to-End Playwright** | `pnpm exec playwright test` | **PASS** (12/12 pruebas E2E en verde) |

---

## 4. Lista de Pull Requests Pendientes de Merge hacia `main`

El trabajo completo de los Hitos 2 al 7 se encuentra consolidado en la rama `feat/app-web`.  
Siguiendo la regla estricta: **el merge es SIEMPRE con confirmación explícita del operador, PR por PR**.

### Estado de ramas:
- `main` se encuentra en el commit `00e310b` (Merge del Hito 1).
- `feat/app-web` contiene linealmente las entregas de los Hitos 2 a 7:
  - **Hito 2:** Alta de producto con tabla de precios de Guatemala (`395d6ee`).
  - **Hito 3:** Motor de ejecución, cola de acciones y runner DBOS (`20f7eb1` a `ea855b5`).
  - **Hito 4:** FASE 1 completa, 7 pestañas, checklist de bloqueantes y publicación Meta (`2032e92` a `5ee4a03`).
  - **Hito 5:** Ciclo diario y pantalla de órdenes literales para Meta (`6d822a8`).
  - **Hito 6:** FASE 2, FASE 3, galería de conceptos y ciclo de fatiga con retorno a F1 (`5712987`).
  - **Hito 7:** Respaldos automáticos diarios, doctrina en `CLAUDE.md`, guía de uso y lanzador `iniciar.bat`.

### Orden recomendado de integración:
1. **Opción A (Recomendada):** Merge directo de la rama completa `feat/app-web` hacia `main` (agrupa de forma limpia y probada los Hitos 2 al 7 con historial preservado).
2. **Opción B:** Si se prefiere por hitos individuales, abrir y mergear secuencialmente:
   - PR Hito 2 → `main`
   - PR Hito 3 → `main`
   - PR Hito 4 → `main`
   - PR Hito 5 → `main`
   - PR Hito 6 → `main`
   - PR Hito 7 → `main`

### Instrucciones obligatorias post-merge (en la carpeta real `../SISTEMA`, solo con su OK):
Una vez realizado el merge a `main`, situarse en `../SISTEMA` y ejecutar para regenerar los archivos derivados:
```bash
python Ads/_TOOLS/gen_app.py --todo
python Ads/_TOOLS/flujo.py --todo
```

---

## 5. Próximos Pasos (Fase SaaS — No Iniciada)

Conforme a la sección 4 de `HOJA_DE_RUTA_APP.md`, lo que viene después queda **únicamente anotado para el futuro**, sin haber tocado nada en esta fase:
- Migración de base de datos de SQLite local a PostgreSQL (DBOS solo requiere cambio de cadena de conexión).
- Módulo de autenticación multi-usuario, roles y aislamiento de datos por cliente/tienda.
- Conexión vía API key de Anthropic en servidor centralizado (reemplazando la suscripción personal local de Claude Code).
- Despliegue en contenedor Docker y servidor en la nube con cobro de suscripción recurrente.
- Extracción de librería `vitalcom_core/` bajo los scripts de `Ads/_TOOLS/`.
