# HANDOFF · APP WEB · arranque del HITO 3 · 18-sep-2026

> Para la sesión que sigue. Leer entero antes de tocar nada. Manda `CLAUDE.md`; después
> `_ROADMAP/HOJA_DE_RUTA_APP.md`; después esto. Si algo de acá choca con esos dos, se avisa al
> operador y se detiene.

---

## 1 · Dónde está todo

| Qué | Dónde |
|---|---|
| Código de la app | **worktree `../SISTEMA-app`**, rama `feat/app-web` (se trabaja ACÁ) |
| Carpeta real del sistema | `../SISTEMA` — la app LEE de acá (`VITALCOM_BASE`). Está en la rama vieja `feat/optimizacion-continua-perfil-angulos`: **no tiene la app ni los scripts nuevos**. No cambiarla de rama sin permiso del operador (otras sesiones la usan). |
| Hoja de ruta | `_ROADMAP/HOJA_DE_RUTA_APP.md` |
| Informe de spikes (Hito 0) | `PRODUCTOS/_AUDITORIAS/SPIKE_APP_2026-09-17.md` |
| PRs | #1 y #2 mergeados a `main`. **#3 (Hito 2) abierto, sin mergear**: se mergea solo con confirmación del operador. |

**Hitos hechos:** 0 (spikes A-E), 1 (tablero de solo lectura), 2 (alta de producto + tabla GT).
**Sigue:** Hito 3 — motor de ejecución (cola, scripts, Claude, progreso en vivo).

---

## 2 · Cómo correr todo (esta máquina, Windows)

```bash
# uv NO está en el PATH; pnpm sí.
export PATH="$HOME/AppData/Roaming/Python/Python314/Scripts:$PATH"
export VITALCOM_BASE="C:/Users/juand/Downloads/AGENTES LUCID/Profesional en Eccomerce gestion/SISTEMA"

cd ../SISTEMA-app/app/backend  && uv run --no-sync pytest -q          # 25 pruebas
cd ../SISTEMA-app/app/frontend && pnpm test && pnpm build             # 11 pruebas
cd ../SISTEMA-app/app/frontend && pnpm exec playwright test           # 4 pruebas (levanta su server en :8100)
cd ../SISTEMA-app && for t in Ads/_TOOLS/test_*.py; do python "$t" >/dev/null || echo "FAIL $t"; done   # 15
```

Servidor para mirar: `uv run --no-sync uvicorn vitalcom_app.main:app --port 8000` desde
`app/backend`, en segundo plano. **Queda "corriendo" para siempre: es normal, es un servidor.**

Tipos del frontend: se regeneran del OpenAPI (dump con `app.openapi()` a
`src/api/openapi.json` → `pnpm exec openapi-typescript src/api/openapi.json -o src/api/esquema.d.ts`).

---

## 3 · Trampas ya pisadas (no repetirlas)

1. **`uv sync` con el servidor corriendo lo mata** (exit 4). Parar el servidor antes.
2. **TypeScript fijado en 5.9**: la 7 rompe `openapi-typescript`. `vite.config.ts` importa
   `defineConfig` de `vitest/config`, no de `vite`.
3. **Los scripts nuevos viven en el worktree, no en la carpeta real.** Una prueba que copie un
   script a un fixture lo toma del repo (`Path(__file__).parents[3] / "Ads/_TOOLS"`), no de
   `VITALCOM_BASE`. Ver `app/backend/tests/test_alta_por_la_app.py`.
4. **Un fixture que cambia `VITALCOM_BASE` limpia `config.base.cache_clear()` en un `finally`**;
   si no, las pruebas siguientes leen una carpeta temporal ya borrada.
5. **`costear.py` elige la fila MÁS CERCANA** (empate → superior). Q41 → fila Q40. El invariante
   2 de CLAUDE.md dice "la superior": **decisión pendiente del operador**. La app repite el
   criterio del script; no lo reinterpreta.
6. La consola de Windows imprime acentos mal (cp1252): usar `PYTHONIOENCODING=utf-8`.

---

## 4 · Reglas que la app ya hace cumplir con pruebas (no aflojarlas)

- **La app no calcula** — `tests/test_sin_aritmetica.py` recorre el AST y falla si hay
  aritmética o umbrales sobre CPA, precio, costo, break-even, ventas, etc.
- **La app no escribe: ejecuta al que escribe.** Solo `subidas.py` (temporal del SO) y el
  candado de la cola en `escrituras.py` tocan disco; ambos tienen prueba estructural.
- **Toda escritura pasa por un script de `Ads/_TOOLS/` con su test** y por `with Cola()`.
  `test_los_cambios_pasan_por_un_script_del_motor` tiene la lista blanca de scripts: agregar
  uno nuevo es agregarlo ahí **y** su test en `Ads/_TOOLS/`.
- `flujo.py` en lectura va siempre con `--sin-escribir`; `--todo` solo después de escribir.

---

## 5 · HITO 3 — plan concreto

Texto oficial en la hoja de ruta. Esto es cómo hacerlo con lo que ya se aprendió.

### 5.1 Acciones declaradas
- `VISTAS/_MANIFIESTO.json` v7 con bloque `acciones`: `id`, `comando` (script + args
  con placeholders `{producto_key}`), `ejecutor_tipo` (script | subagente | skill | mcp |
  operador), `requiere_confirmacion`, `escribe: [...]`.
- `gen_app.py` valida el bloque (ids únicos, script existe, `mcp` ⇒ `requiere_confirmacion`)
  **con su test**. Es el único cambio permitido a un script existente en este hito.
- Las acciones de los nodos salen de `DOCTRINA/FLUJO.json` (cada nodo ya declara su ejecutor).
- Endpoint `POST /api/acciones/{id}`: una acción que no está en el manifiesto → **403**.
  Esto reemplaza la lista blanca fija de `escrituras.py`.

### 5.2 `claude.py` — el único punto que invoca Claude Code headless
Todo esto está MEDIDO en el spike A/B (informe §A y §B):
- Binario: `VITALCOM_CLAUDE_EXE` → PATH → `~/.local/bin/claude.exe` → carpeta de la app de
  escritorio (versión más nueva). Al arrancar, `claude auth status`: si `loggedIn` es false,
  la pantalla dice "Claude: sin sesión — abrí una terminal, corré `claude` y `/login`".
- **Falla con mensaje claro si ve `ANTHROPIC_API_KEY` o `CLAUDE_CODE_OAUTH_TOKEN`**: con
  cualquiera de los dos se pierde el conector de Meta y se cobra aparte. Test.
- Flags: `-p <prompt> --output-format stream-json --verbose --include-hook-events
  --permission-mode dontAsk --allowedTools ... --max-budget-usd N`. **Nunca `--bare`** (salta
  los hooks).
- Entorno del subproceso: quitar las variables `CLAUDE*`/`ANTHROPIC*` que hereda de una sesión
  de escritorio (ver `app/spikes/spike_ab.py`).
- `allowedTools` **por herramienta** (`Task`, `Agent`, `Read`, `Bash`, `Write`...), no por
  patrón de comando: `Bash(python x:*)` bloqueó a `etapa-1` porque el subagente antepuso `cd`.
- Meta: el servidor se llama **`claude_ai_META_MCP`** en el CLI. `dontAsk` NO autoriza MCP:
  cada herramienta de Meta va por nombre exacto en `allowedTools`, y solo en acciones `mcp`
  aprobadas. El estado del conector en el evento `init` puede decir `pending`: no decidir
  "no disponible" por el `init`, sino por el resultado de la llamada.
- **GTR 13 no tiene MCP habilitado** (CLEARSTEM está ahí): avisar antes de ofrecer el botón.
- Guardar la salida completa en `PRODUCTOS/_AUDITORIAS/app_runs/` — **por el script/cola, no
  escribiendo desde la app** (o declarar esa carpeta como salida del job y que la escriba el
  runner; decidirlo y dejarlo con test).
- El `costo_usd` del evento `result` es estimación en precio de API; con la suscripción Pro no
  se cobra. Mostrarlo como "equivalente", nunca como gasto.

### 5.3 `workflows.py` — DBOS
Medido en el spike C:
- `DBOS(config={"name": ..., "system_database_url": "sqlite:///<ruta fuera del repo>"})`,
  `DBOS.launch()` en el arranque de FastAPI.
- **Un paso que muere a mitad se ejecuta de nuevo** (al-menos-una-vez). Todo paso que toque
  Meta es idempotente: snapshot antes de crear (lo que ya exige la skill `publicar-meta`).
- **Fijar `application_version`**: si no, un workflow caído no se retoma después de cambiar el
  código. La pantalla Trabajos muestra los PENDING de otra versión.
- La espera de aprobación es `DBOS.recv`; el botón Aprobar hace `DBOS.send`.
- Agregar `dbos` a `pyproject.toml` (instaló bien en Python 3.14.5).

### 5.4 Progreso en vivo y pantalla Trabajos
- SSE (`text/event-stream`) desde el log del job. Pantalla **Trabajos**: lista, estado, log en
  vivo, reintentar.
- Al terminar un job que escribe: `flujo.py --todo` y `hook_csv.py --barrido` (fuera de Claude
  Code los hooks no corren).

### 5.5 Aceptación (de la hoja de ruta)
- acción no declarada → 403;
- dos jobs que escriben se serializan;
- matar el servidor en medio de un job y reiniciar → retoma o queda FALLIDO con rastro, nunca
  a medias sin rastro;
- más el gate §2.6 completo pegado en verde, commit + push en `feat/app-web`, PR a `main`,
  merge **solo con confirmación del operador**.

---

## 6 · Cuándo volver a Opus (decisión del 18-sep-2026)

El operador pasa a Sonnet para ahorrar. Los números y los gates no dependen del modelo (los
dan los scripts y las pruebas), pero hay juicio que sí. **Parar y avisar al operador que
conviene cambiar a Opus antes de:**
1. **Diseñar** el bloque `acciones` y el runner de DBOS (5.1 y 5.3): es la base de los Hitos
   4-6. Implementarlo después con Sonnet está bien.
2. Cualquier paso que **ejecute en Meta** (Hito 4 publicar, Hito 5 órdenes): invariante 13.
3. Cambiar **`DOCTRINA/FLUJO.json`** (Hito 6, transición de fatiga → nuevos ángulos).
4. Cualquier cosa donde la doctrina y el código digan cosas distintas (como el punto 3.5):
   se pregunta, no se elige.

---

## 7 · Cómo hablarle al operador

No programa. Quiere claridad: qué se hizo, qué quedó, qué necesita de él. En español, sin
jerga (y si hay jerga, explicada en una línea). Decidir cuando la data alcanza; no devolverle
elecciones técnicas. Pedir confirmación antes de: mergear, cambiar de rama la carpeta real,
cualquier acción en Meta, borrar algo.
