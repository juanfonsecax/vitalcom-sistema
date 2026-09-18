# HOJA DE RUTA — VITALCOM COMO APLICACIÓN (fase personal, Guatemala)

> Escrita el 17-sep-2026. Es el documento de arranque para la sesión que construye la app.
> Se ejecuta en orden, hito por hito. Ningún hito empieza sin que el anterior cumpla su criterio
> de aceptación. Si algo de acá choca con `CLAUDE.md`, manda `CLAUDE.md` y se avisa al operador.

---

## 0 · LO QUE HAY QUE ENTENDER ANTES DE TOCAR NADA

### 0.1 Qué es la app
Una pantalla **encima** del sistema que ya existe. No lo reemplaza, no lo reescribe y no lo copia.

```
   OPERADOR ── navegador (localhost) ──► APP (app/)
                                          │ lee   contratos JSON/CSV
                                          │ corre scripts declarados (Ads/_TOOLS/*.py)
                                          │ lanza Claude Code headless (etapas y skills)
                                          │ pide aprobación antes de tocar Meta
                                          ▼
                                   MOTOR ACTUAL (intacto)
          flujo.py · decidir.py · costear.py · gen_publicacion.py · gen_flujo_bot.py
          17 etapas en .claude/agents · skills · hooks · PRODUCTOS/*.csv
```

**Regla de oro de la app:** la app **no calcula, no decide y no escribe CSV**. Todo número sale de
un script del motor; toda escritura pasa por un script escritor con su test. Si la app necesita un
dato que ningún script produce, se crea el script (con test) en `Ads/_TOOLS/`, no se calcula en la app.

### 0.2 Lo que el operador pidió (su idea, 17-sep-2026)
1. Arrancar un producto con **tres cosas**: imagen del producto, descripción lo más extensa posible,
   y costo en Q. Con el costo, ver al instante **la tabla de precios de Guatemala** (precio 1u/2u/3u,
   CPA objetivo, break-even).
2. Que desde ahí el sistema **avance solo**: investigación de mercado, avatares, dolores, deseos,
   TOFU/MOFU/BOFU, ángulos, flujo LucidBot, anuncios, lanzamiento.
3. Ver cada FASE como pantalla clara: F1 ángulos → F2 conceptos → F3 escalado → y cuando el ángulo
   se fatiga, volver a F1 con ángulos nuevos para el mismo producto.
4. Que la IA sea Claude, corriendo **en local** a través de Claude Code.
5. Que sea más claro que hoy: el operador siente que hay data técnica que no se entiende.
6. Que no se dañe nada de lo construido.

### 0.3 Correcciones al modelo mental (la app muestra la doctrina VIGENTE, no la de memoria)
Estas diferencias entre lo que el operador recuerda y lo que el sistema hace están verificadas en
los CSV y la doctrina. La app las muestra como están. Cambiarlas es una decisión de doctrina aparte,
no algo que se cambie en la app.

| El operador recuerda | El sistema hace (fuente) |
|---|---|
| FASE 1 con 5 ángulos × el mismo concepto | **6 ángulos × 1 concepto fijo**, estructura `6-1-1`, $2.99/conjunto (`_PARAMETROS_PUBLICACION.csv`) |
| A los 3 días se sabe qué ángulo ganó | El ganador se declara **por VENTA y por volumen de evidencia**, no por días (`decidir.py`, `ventana_dias=14`). A $3-6/día, 3 días dan 1-3 ventas: el motor emite `SEGUIR_MIDIENDO` y dice **cuántas ventas faltan**. Los "3 días" de Calet son la **duración de la campaña 1-1-5 de FASE 2** (`duracion_testeo_fase2_dias`), no un reloj para coronar. |
| FASE 2: a cada ángulo ganador le salen 5 conceptos a la vez | Ganador #1 arranca FASE 2 con **10 conceptos** (`1-1-5` A + `1-1-5` B + `1-2-5` C). Ganadores #2 y #3 entran como **FASE 2 propias, escalonadas cada ~3 días, con bot dedicado** (`CALENDARIO_ESCALADO.md` §1). |
| FASE 3 después de otros 3 días | FASE 3 entra con **concepto ganador en 2 de 2 apariciones y CPA real bajo break-even** (invariante 1). Estructura `1-1-7` CBO. |
| Fatiga → nuevos ángulos | Correcto. `decidir.py` distingue **RENOVAR** (ganador cansado: concepto nuevo) de **PAUSAR** (ángulo fallido). Volver a F1 con ángulos nuevos es el paso siguiente cuando RENOVAR ya no alcanza. |

La app **explica** cada una de estas cosas en lenguaje simple en la pantalla donde aparecen
(por ejemplo: "Ángulo X: 2 ventas, faltan 5 para decidir con seguridad").

### 0.4 Lo que NO va a ir solo (límites honestos)
"Que se vaya solito" se cumple para todo lo que es cálculo y redacción. No se cumple para esto:

| Paso | Por qué necesita al operador | Qué hace la app |
|---|---|---|
| Ejecutar órdenes en Meta (publicar, pausar, subir presupuesto) | Invariante 13: confirmación **orden por orden** (decisión del operador, 09-sep-2026) | Botón **Aprobar / Rechazar** por orden; después ejecuta, verifica contra Meta y registra el evento |
| Pegar el flujo en LucidBot | No hay integración conocida con LucidBot para escribir flujos (verificar en Hito 0) | Muestra el flujo listo con botón **Copiar** (`gen_flujo_bot.py --copy`) |
| Crear FanPage, WhatsApp, cuenta publicitaria | Son cuentas reales de Meta | Checklist con el dato exacto que falta y dónde pegarlo |
| Renderizar creativos | Hoy se hace en ChatGPT web con el Chrome logueado (`etapa-render`) | Botón que lanza `etapa-render`; el Chrome del operador tiene que estar abierto |
| Media local en Meta | Solo GTR 7 sube media local por MCP (`_DIM_CUENTAS.csv`) | La app lo avisa antes de publicar en otra cuenta |

### 0.5 Insumos de FASE 1: las tres cosas del operador + una opcional
Hoy `etapa-0` necesita **≥6 transcripciones de videos** de la competencia: de ahí salen los ángulos
con evidencia y los videos lavados que se usan como creativo de F1. Con solo imagen + descripción +
costo, `etapa-0` no tiene insumo.

**Decisión (la toma la hoja de ruta, no se le devuelve al operador):** la pantalla "Nuevo producto"
pide las tres cosas obligatorias y **una cuarta opcional: videos**.
- **Con videos:** la app los transcribe en local (nuevo script `transcribir_videos.py`, faster-whisper)
  y los deja en `Ads/1.2 Transcripcion videos/[PRODUCTO]/`. Corre el camino actual completo.
- **Sin videos:** F1 va con los 6 ángulos derivados de la investigación (`etapa-1b` + `etapa-2`) y
  creativos IMAGEN (`etapa-4`). Antes hay que confirmar con el operador que ese camino ya es
  doctrina (`fase-1-angulos` y `ETAPA-0.md`). Si no lo es, se agrega como rama declarada en
  `DOCTRINA/FLUJO.json`, con su predicado, **nunca como un if dentro de la app**.

---

## 1 · DECISIONES DE ARQUITECTURA (ya tomadas; no reabrir sin data nueva)

| Tema | Decisión | Por qué |
|---|---|---|
| Backend | **Python 3.12+ · FastAPI · Pydantic v2 · Uvicorn** | El motor entero es Python; la app lo invoca sin traducir nada. FastAPI genera el contrato OpenAPI solo. |
| Trabajos largos y aprobaciones | **DBOS Transact (Python)** sobre **SQLite** local → **Postgres** en la fase SaaS | Stack ya decidido (roadmap G3). Cada paso queda durable: si se cae el proceso a la mitad de una publicación, retoma sin duplicar la llamada. La espera de aprobación es `DBOS.recv`. |
| IA | **Claude Code headless** (`claude -p` / Claude Agent SDK) con `cwd` en la carpeta del sistema | Carga las mismas 17 etapas, skills, `CLAUDE.md` y hooks. No se reescribe ningún prompt. |
| Frontend | **React + TypeScript + Vite · Tailwind CSS + shadcn/ui · TanStack Query + TanStack Router** | Asistente de varios pasos, subida de imagen/video, progreso en vivo y paso a SaaS: es el stack con más ecosistema y el que mejor se mantiene con IA. Reemplaza la propuesta anterior de HTMX, pensada para una sola pantalla de lectura. |
| Tipos compartidos | **openapi-typescript** (u **orval**) genera los tipos del frontend desde el OpenAPI de FastAPI | Un contrato, un dueño: el frontend no redefine a mano ningún campo. |
| Progreso en vivo | **Server-Sent Events (SSE)** | Una sola dirección (servidor → pantalla), más simple que WebSockets. |
| Gráficos | **Recharts** + la skill `dataviz` del proyecto para la paleta | |
| Dependencias | **uv** (Python) y **pnpm** (frontend) | Instalación reproducible con lockfile. |
| Pruebas | **pytest** (backend) · **Vitest** (frontend) · **Playwright** (punta a punta) | |
| Arranque | `iniciar.bat` en la raíz: un doble clic levanta todo y abre `http://localhost:8000` | El operador no escribe comandos. |
| Descartado | Java, Next.js/SSR, LangGraph, Temporal, n8n, Docker en la fase personal | Sin beneficio medible en esta fase; Docker se evalúa en la fase SaaS. |

**Referencias públicas que la sesión debe consultar antes de escribir cada capa** (leer la doc
vigente; no programar de memoria):
- `github.com/fastapi/full-stack-fastapi-template`: estructura FastAPI + React + TS + Vite +
  TanStack, generación de cliente desde OpenAPI y organización de pruebas. **Tomar la estructura,
  no su Postgres/Docker/login** (eso es de la fase SaaS).
- Documentación de DBOS Python (`docs.dbos.dev`): workflows, steps, `send`/`recv`, colas,
  scheduled workflows y el soporte de SQLite.
- Documentación del Claude Agent SDK / Claude Code headless (`docs.claude.com`): autenticación,
  `allowedTools`, salida JSON/stream, `cwd`, y **qué cuenta usa y cómo se factura**.
- `ui.shadcn.com` para componentes y TanStack Query para caché y reintentos.

### 1.1 Dónde vive el código
```
app/
  backend/            FastAPI + DBOS (Python, gestionado con uv)
    vitalcom_app/
      main.py         arranque, rutas, servir el frontend compilado
      contratos.py    lectura tipada de _FLUJO.json, _DECISIONES.json, _LANZADOR.json, CSV
      acciones.py     registro de acciones declaradas (sale de VISTAS/_MANIFIESTO.json)
      workflows.py    DBOS: correr script, correr etapa Claude, esperar aprobación, publicar
      claude.py       único punto que invoca Claude Code headless
      sse.py          progreso en vivo
    tests/
  frontend/           React + TS + Vite (pnpm)
    src/pantallas/    Tablero · Producto · Fase1 · Fase2 · Fase3 · Órdenes · Sistema
iniciar.bat
```
`node_modules/`, `dist/`, la base SQLite de DBOS y `.venv/` van a `.gitignore`.

### 1.2 Dónde corre y dónde se desarrolla (lección medida el 17-sep-2026)
- **La app corre sobre la carpeta real `SISTEMA/`.** Las carpetas `Ads/MEDIA_*` están en
  `.gitignore`: un worktree no las tiene. El 17-sep-2026, `flujo.py --todo` corrido en un worktree
  marcó OVULOS_PURITY como BLOQUEADO ("no existe Ads/MEDIA_OVULOSPURITY") cuando en la carpeta real
  estaba LISTO. La app lee la base desde la variable `VITALCOM_BASE`.
- **El código se desarrolla en un worktree** (`git worktree add ../SISTEMA-app -b feat/app-web`),
  porque otras sesiones trabajan en la misma carpeta. Nunca `git stash`, nunca tocar el staging
  ajeno, `git status` antes y después.
- Los archivos derivados (`_ESTADO_FLUJO.csv`, `_FLUJO.json`, `VISTAS/*`) **no se commitean desde
  el worktree**: se regeneran en la carpeta real después de mergear.

---

## 2 · REGLAS QUE NINGÚN HITO PUEDE ROMPER

1. `Ads/_TOOLS/`, `.claude/`, `DOCTRINA/` y `PRODUCTOS/` **no se modifican para acomodar la app**.
   Si un script necesita `--json` o un modo nuevo, se agrega con su test y sin cambiar la salida
   actual.
2. La app no importa lógica de cálculo; llama a los scripts por subproceso (o, más adelante, a
   `vitalcom_core/`, cuando exista).
3. Toda acción que la app ofrece está **declarada** en `VISTAS/_MANIFIESTO.json` (bloque
   `acciones`): `id`, `comando`, `ejecutor_tipo` (script | subagente | skill | mcp | operador),
   `requiere_confirmacion`, `escribe: [...]`. Un endpoint que corre comandos libres es un defecto.
4. **Un escritor a la vez**: toda acción que escribe pasa por una cola con lock de archivo.
5. Toda acción `mcp` requiere aprobación explícita por orden (invariante 13) y termina con
   verificación contra Meta y `registrar_evento.py`.
6. Cada hito cierra con este gate, en verde, pegado en el mensaje de cierre:
   ```
   python Ads/_TOOLS/test_*.py            (los 13 actuales + los nuevos)
   python Ads/_TOOLS/flujo.py --validar
   python Ads/_TOOLS/verificar_guia_madre.py
   python Ads/_TOOLS/verificar_producto.py --todos
   python Ads/_TOOLS/gen_grafo.py --comparar      (delta de tokens ≈ 0; app/ no se carga en contexto)
   cd app/backend && uv run pytest
   cd app/frontend && pnpm test && pnpm build
   ```
   Si `gen_grafo.py` empieza a contar `app/` en el inventario o en tokens, se excluye `app/` de su
   recorrido **con test**.
7. Nada se agrega sin una razón de fondo medible. La métrica guía de toda la app:
   **pasos del ciclo que hoy obligan a abrir una conversación con Claude** (hoy: todos).

---

## 3 · HITOS

### HITO 0 — Preparación y spike de riesgos (1 sesión)
**Objetivo:** confirmar con evidencia que las piezas críticas funcionan antes de construir.

1. Mergear el PR #1 (`feat/optimizacion-continua-perfil-angulos` → `main`) **con confirmación del
   operador**. Crear el worktree `../SISTEMA-app` en la rama `feat/app-web` desde `main`.
2. Spike A · **Claude headless en esta carpeta**: desde un script Python, invocar Claude Code
   headless con `cwd=SISTEMA/` y pedirle correr `etapa-1` (costeo) sobre un producto de prueba.
   Verificar: (a) carga el subagente y la skill, (b) corren los hooks, (c) la salida llega como
   JSON/stream, (d) **qué autenticación usa y cómo se cobra** (suscripción personal vs API key).
   Para uso personal alcanza el login actual de Claude Code. Para vender el servicio a otros
   (fase SaaS) hay que pasar a API key: dejarlo escrito con la fuente.
3. Spike B · **Meta MCP desde headless**: ¿el conector oficial de Meta (el de claude.ai que eligió
   el operador) está disponible en la sesión headless? Probar solo lectura (`ads_get_ad_accounts`).
   Si no está disponible, las órdenes aprobadas quedan en cola y las ejecuta una sesión interactiva
   de Claude Code (la app muestra "aprobada, pendiente de ejecutar").
4. Spike C · **DBOS + SQLite en Windows**: workflow de 3 pasos con `recv`; matar el proceso en el
   paso 2 y comprobar que retoma sin repetir el paso 1.
5. Spike D · **LucidBot**: ¿hay API para escribir flujos? Si no, queda en "Copiar".
6. Spike E · **faster-whisper** en esta máquina: transcribir un video de `Ads/1.1 Videos/`.

**Aceptación:** un informe `PRODUCTOS/_AUDITORIAS/SPIKE_APP_<fecha>.md` con sí/no y evidencia
(comando + salida) para A-E, y la consecuencia de cada "no" en esta hoja de ruta.

### HITO 1 — Esqueleto y Tablero de solo lectura
**Objetivo:** abrir `localhost:8000` y ver el portafolio más claro que en `VISTAS/APP.html`, sin
que la app escriba nada.

- Backend: `GET /api/productos`, `GET /api/productos/{pk}` (fila de `_DIM_PRODUCTOS` + nodo actual
  de `_ESTADO_FLUJO.csv` + detalle de `flujo.py {pk} --json --sin-escribir`),
  `GET /api/decisiones` (`_DECISIONES.json`), `GET /api/salud` (`VISTAS/_ESTADO.json`: frescura por
  `mtime`). Modelos Pydantic para cada contrato.
- Frontend:
  - **Tablero:** una tarjeta por producto con fase, "estás acá · esto te bloquea · esto sigue" en
    palabras simples, dueño del bloqueo y edad de la data.
  - **Producto:** línea de tiempo F1 → F2 → F3 con el nodo actual resaltado.
  - **Salud:** qué dato está viejo y quién lo produce.
- **Glosario vivo:** cada término técnico (CPA, break-even, IC, ángulo, concepto, 1-1-5, RENOVAR)
  lleva un ícono (i) con la explicación de una línea. Las definiciones viven en un solo archivo
  del frontend, tomadas de `CLAUDE.md` §DEFINICIONES CLAVE.
- `iniciar.bat` levanta el backend y sirve el frontend compilado.

**Aceptación:**
- Test: para cada producto, fase y nodo de la API = `_ESTADO_FLUJO.csv` (sin transformación).
- Test: el paquete `vitalcom_app` no contiene aritmética de negocio (grep de `cpa`, `break`, `*`
  sobre campos monetarios en `contratos.py`: cero cálculos).
- Playwright: el tablero muestra los 5 productos reales y el estado de OVULOS_PURITY coincide con
  `flujo.py --todo`.

### HITO 2 — Nuevo producto (las tres cosas + tabla de Guatemala)
**Objetivo:** el operador carga imagen, descripción y costo, y ve la tabla de precios GT en el acto.

- Script nuevo `Ads/_TOOLS/alta_producto.py` **con test**: crea la fila en `_DIM_PRODUCTOS.csv`
  con escritor CSV real (invariante 11), la carpeta `PRODUCTOS/[NOMBRE]/`, guarda la descripción en
  `2_DATA_PRODUCTO.txt` (sección de insumos), copia la imagen como packshot declarado en
  `_DIM_ENVASE.csv` (el packshot se DECLARA, nunca se adivina) y crea `Ads/MEDIA_[PRODUCTO]/`.
  Rechaza `producto_key` duplicado. Soporta `--dry-run`.
- Script nuevo `Ads/_TOOLS/transcribir_videos.py` **con test** (si el Spike E dio sí): videos →
  TXT en `Ads/1.2 Transcripcion videos/[PRODUCTO]/`, numerados como hoy.
- Pantalla **Nuevo producto** (asistente de 3 pasos):
  1. Imagen (arrastrar y soltar) + nombre.
  2. Descripción extensa (texto libre; sugerencia de qué incluir: ingredientes, dosis, beneficios,
     registro, proveedor, garantía).
  3. Costo en Q → llamada en vivo a `costear.py <costo> --json` → **tabla de Guatemala**: precio
     1u/2u/3u, CPA objetivo, break-even, y la fila de `_DIM_COSTEO.csv` usada (si el costo cae entre
     dos filas, se ve que tomó la superior).
  4. (Opcional) Videos de la competencia.
- Al confirmar: `alta_producto.py` + `flujo.py --todo`. El producto aparece en el Tablero en
  `F1.congelar_inputs` (o `F1.paquete` si ya tiene todo).

**Aceptación:** test de `alta_producto.py` sobre fixture; la tabla mostrada = salida de
`costear.py --json` byte a byte; `verificar_producto.py --todos` sigue en verde; un producto de
prueba se da de alta y se borra en el fixture sin tocar los CSV reales.

### HITO 3 — Motor de ejecución (cola, scripts, Claude, progreso en vivo)
**Objetivo:** cualquier nodo del flujo se ejecuta con un botón y se ve avanzar.

- `VISTAS/_MANIFIESTO.json` v7 con bloque `acciones` (actualizar `gen_app.py` para validarlo y su
  test). Las acciones de los nodos salen de `DOCTRINA/FLUJO.json` (cada nodo ya declara su ejecutor).
- DBOS: un workflow por tipo de ejecutor:
  - `script`: subproceso con `--json`, log en vivo por SSE, código de salida → estado.
  - `subagente` / `skill`: `claude.py` invoca Claude Code headless con el prompt mínimo ("ejecutá
    el nodo X del producto Y según flujo.py") y `allowedTools` acotado; guarda la salida completa
    en `PRODUCTOS/_AUDITORIAS/app_runs/`.
  - `operador`: formulario que llama al script escritor dueño del dato.
- Cola única con lock de archivo; al terminar cada job que escribe: `gen_app.py` (los hooks no
  corren fuera de Claude Code; hoy `hook_csv.py --barrido` cumple ese rol).
- Pantalla **Trabajos**: lista, estado, log en vivo, reintentar.

**Aceptación:** test: una acción no declarada devuelve 403; dos jobs que escriben se serializan;
matar el servidor en medio de un job y reiniciar → el job retoma o queda marcado fallido, nunca a
medias sin rastro.

### HITO 4 — FASE 1 completa dentro de la app
**Objetivo:** del producto recién dado de alta a la campaña de 6 ángulos lista para aprobar.

- Botón **Armar FASE 1** → workflow que recorre `fase-1-angulos` (etapa-producto → etapa-0 →
  etapa-1 → etapa-1b → etapa-2 ∥ etapa-fanpage → etapa-4 ∥ etapa-5 → etapa-6 →
  etapa-guardar-producto), respetando los paralelos que declara la skill.
- Pantallas de resultado **legibles**, no el TXT crudo:
  - **Investigación:** voz del cliente y fuentes (etapa-1b).
  - **Avatares y ángulos:** las 6 fichas (avatar en 5 ejes, nivel de conciencia, dolor, deseo,
    promesa, saturación), con el embudo TOFU/MOFU/BOFU.
  - **Anuncios:** copy + creativo por ángulo.
  - **Flujo LucidBot:** render de `gen_flujo_bot.py`, instrucciones `>>` separadas del texto a pegar,
    botón **Copiar** por bloque.
  - **Estructura de campaña:** nombres, presupuesto, banda de edad y fecha de lanzamiento 4 AM (de
    `gen_lanzador.py` / `_PLAN.json`).
- **Publicar:** `gen_publicacion.py` → pantalla de revisión con cada llamada a Meta → **Aprobar** →
  ejecución (según Spike B) → `verificar_publicacion.py` → `ad_id` escritos → evento.
- Los bloqueos del flujo (falta page_id, falta WhatsApp) se muestran como checklist con el campo
  para cargar el dato.

**Aceptación:** re-correr la cadena sobre los datos de TURMERIC (la simulación de G0.5) desde la
app, sin arreglos a mano, y llegar a la pantalla de aprobación de publicación con 0 bloqueantes,
igual que el 17-sep-2026 por scripts.

### HITO 5 — Ciclo diario y Órdenes
**Objetivo:** cada mañana la app ya trae los datos y las órdenes; el operador solo aprueba.

- Workflow programado de DBOS (nocturno): `recopilar-lucidsales` → `bajar_meta_insights.py` →
  `gen_decisiones.py` → `flujo.py --todo` → `gen_app.py`.
- Pantalla **Órdenes de hoy:** una tarjeta por orden de `_DECISIONES.json` (ESCALAR · PAUSAR ·
  RENOVAR · SEGUIR_MIDIENDO) con: la frase simple ("Subir 20 % al ángulo X"), el porqué (CPA, IC,
  break-even, ventas faltantes), el rezago de la data **arriba de todo si pasa de 2 días**, y
  **Aprobar / Rechazar**. Aprobar → ejecución MCP → verificación → `registrar_evento.py`.
- **Ganadores:** cuando el motor declara un ángulo ganador por venta, la app lo anuncia y ofrece el
  paso siguiente que dice `flujo.py` (etapa-11 → FASE 2), no uno inventado.
- Aviso al celular (opcional, más adelante): notificación cuando hay órdenes por aprobar.

**Aceptación:** una semana de corridas nocturnas sin abrir una conversación; cada orden ejecutada
tiene su evento en `_EVENTOS.csv` y su verificación contra Meta.

### HITO 6 — FASE 2, FASE 3 y el ciclo de fatiga
**Objetivo:** el recorrido completo, incluido volver a F1 con ángulos nuevos.

- **FASE 2:** etapa-11 (cierre del bot) → `generar-conceptos` / etapa-9 → `etapa-render` →
  etapa-4 (copy único) ∥ etapa-5 (flujo dedicado) → etapa-6 (1-1-5 A, 1-1-5 B, 1-2-5 C). Galería de
  los 10 conceptos con su blueprint de origen. Si hay ganadores #2 y #3, la app muestra su FASE 2
  escalonada (~3 días) como carriles separados.
- **FASE 3:** gate "concepto ganador en 2 de 2" visible con su evidencia; plan 1-1-7 CBO;
  expansión por Post ID, multicuenta y multifanpage (etapa-3, etapa-8).
- **Fatiga:** cuando el motor emite RENOVAR para un ganador, la app ofrece conceptos nuevos. Cuando
  el ángulo ya no rinde, ofrece **"Nuevos ángulos para este producto"**: vuelve a F1 sobre el mismo
  producto con los ángulos ya probados excluidos. Si `FLUJO.json` no declara hoy esa transición,
  se agrega al grafo con su predicado y su test (`test_flujo.py`) **antes** de construir el botón.

**Aceptación:** replay con `flujo.py --hoy` sobre TINNIDROP (hoy en F2) muestra el mismo nodo en la
app que en la CLI; test de la transición de fatiga en `test_flujo.py`.

### HITO 7 — Cierre de la fase personal
- Copia de seguridad automática diaria de `PRODUCTOS/` (zip fechado fuera del repo).
- Fila nueva en la tabla de dueños de `CLAUDE.md`: "LA APP WEB → `app/` (lee contratos, dispara
  ejecutores declarados)". Actualizar la memoria del proyecto.
- Guía de uso de una página para el operador (qué botón hace qué), en la propia app.

---

## 4 · DESPUÉS (fase SaaS, no se empieza hasta cerrar el Hito 7)
Postgres en lugar de SQLite (DBOS cambia solo la conexión), usuarios y login, un espacio de datos
por cliente, API key de Anthropic en lugar del login personal, despliegue en servidor, cobro. Antes
de eso sigue pendiente lo del plan general: librería `vitalcom_core/` bajo los scripts, tabla de
tasas de cambio fechada por mercado, pytest + GitHub Actions y evals con promptfoo antes de podar
los prompts de juicio (ETAPA-4, ETAPA-5).

---

## 5 · CÓMO REPORTA CADA SESIÓN
Al cerrar cada hito: qué se hizo, el gate de la sección 2.6 pegado en verde, qué quedó pendiente, y
commit + push en `feat/app-web` (PR hacia `main` al cerrar cada hito, merge con confirmación del
operador).
