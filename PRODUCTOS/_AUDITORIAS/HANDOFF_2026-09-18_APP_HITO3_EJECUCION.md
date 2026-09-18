# HANDOFF · APP WEB · Hito 3, PARTE 2 (el motor de ejecución) · 18-sep-2026

> Para la sesión que sigue. Leer en este orden: `CLAUDE.md` → `_ROADMAP/HOJA_DE_RUTA_APP.md` →
> `PRODUCTOS/_AUDITORIAS/HANDOFF_2026-09-18_APP_HITO3.md` (el traspaso original del Hito 3) →
> `PRODUCTOS/_AUDITORIAS/DISENO_HITO3_ACCIONES_DBOS_2026-09-18.md` (el diseño completo, hecho en
> Opus — es la fuente de verdad del CÓMO; este documento no lo repite, solo dice dónde quedó todo
> y qué sigue) → este documento, completo.
>
> Si algo de acá choca con esos cuatro, se para y se avisa al operador (no programa; español
> simple).

---

## 1 · Dónde está todo

| Qué | Dónde |
|---|---|
| Código de la app | worktree `../SISTEMA-app`, rama `feat/app-web` (se trabaja ACÁ) |
| Carpeta real del sistema | `../SISTEMA` — la app LEE de acá (`VITALCOM_BASE`). Rama vieja, sin la app. No cambiarla de rama sin permiso del operador. |
| Hoja de ruta | `_ROADMAP/HOJA_DE_RUTA_APP.md` |
| Traspaso del Hito 3 (parte 1, arranque) | `PRODUCTOS/_AUDITORIAS/HANDOFF_2026-09-18_APP_HITO3.md` |
| **Diseño completo del Hito 3** (hecho en Opus el 18-sep) | `PRODUCTOS/_AUDITORIAS/DISENO_HITO3_ACCIONES_DBOS_2026-09-18.md` — **léelo entero antes de tocar código**. Tiene el esquema exacto del bloque `acciones`, las 19 reglas de validación, los workflows de DBOS paso a paso, el contrato de `claude.py`, la bitácora, los endpoints y la tabla de pruebas. |
| PRs | #1 y #2 mergeados a `main`. #3 (Hito 2) abierto, sin mergear: se mergea solo con confirmación del operador. |

**Hitos hechos:** 0 (spikes A-E), 1 (tablero de solo lectura), 2 (alta de producto + tabla GT).
**Hito 3:** la PARTE 1 (acciones declaradas) está hecha y verde — ver §2. Sigue la PARTE 2 (el
motor de ejecución): puntos 4 a 10 de la lista de trabajo del diseño, §6.

---

## 2 · Qué se hizo en esta sesión (18-sep-2026, puntos 1-3 de la lista del diseño)

Sin tocar Meta, sin mergear, sin cambiar de rama la carpeta real.

1. **`Ads/_TOOLS/test_gen_app.py`** (archivo nuevo, 41 comprobaciones): cubre la validación de
   `VISTAS/_MANIFIESTO.json` que ya existía (vistas, v6) y las 19 reglas nuevas del bloque
   `acciones` (v7), una por una, con un caso que la dispara y uno que no.
2. **`Ads/_TOOLS/gen_app.py`**: se agregó `problemas_de_manifiesto(m, flujo)` (función pura, sin
   disco — es lo que las pruebas ejercitan directo), `leer_flujo()`, `validar_acciones(m, flujo)`
   (las 19 reglas, V1-V19) y el modo `--validar-manifiesto [--json]` que solo valida y sale 0/1.
   `leer_manifiesto()` (la que usa el resto del script) se refactorizó para llamar a
   `problemas_de_manifiesto()` por dentro; su comportamiento hacia afuera (levanta `SystemExit`
   con el mensaje de siempre) no cambió.
3. **`VISTAS/_MANIFIESTO.json` → versión 7**: se agregó el bloque `acciones` completo, transcrito
   del diseño §2.1 y §2.3 — 22 acciones (los 14 nodos de `DOCTRINA/FLUJO.json` + 8 comandos
   internos del runner). Ninguna acción que toca Meta está habilitada (`habilitada: false` con su
   `motivo`, tal como lo fija el diseño §5, punto 13).

**Gate completo corrido y en verde** (los 16 `test_*.py` de `Ads/_TOOLS/` incluido el nuevo,
`flujo.py --validar`, `verificar_guia_madre.py`, `verificar_producto.py --todos`,
`gen_grafo.py --comparar` con "rutas muertas: ninguna", 25 pruebas de `app/backend` con pytest).

**Sin commitear todavía** (mismo worktree, se ve tal cual al abrir la sesión nueva ahí — no hace
falta ninguna acción de git para heredarlo):
```
M  Ads/_TOOLS/gen_app.py
M  PRODUCTOS/_AUDITORIAS/_LINEA_BASE_SISTEMA.json      (línea base de gen_grafo.py, efecto normal de --comparar)
M  VISTAS/_MANIFIESTO.json
?? Ads/_TOOLS/test_gen_app.py
?? PRODUCTOS/_AUDITORIAS/DISENO_HITO3_ACCIONES_DBOS_2026-09-18.md
```
Decidir con el operador cuándo commitear (la hoja de ruta dice que cada hito cierra con commit +
push + PR; esto es solo un punto intermedio dentro del Hito 3, no hay obligación de commitear
antes de seguir).

---

## 3 · Cómo verificar que sigue todo en verde (antes de escribir una línea)

Windows, desde la carpeta `SISTEMA` (la real; el worktree es su hermano `../SISTEMA-app`):

```bash
export PATH="$HOME/AppData/Roaming/Python/Python314/Scripts:$PATH"
export VITALCOM_BASE="C:/Users/juand/Downloads/AGENTES LUCID/Profesional en Eccomerce gestion/SISTEMA-app"
export PYTHONIOENCODING=utf-8

cd ../SISTEMA-app
for t in Ads/_TOOLS/test_*.py; do python "$t" >/dev/null || echo "FAIL $t"; done   # 16, incluye test_gen_app.py
python Ads/_TOOLS/flujo.py --validar
python Ads/_TOOLS/gen_app.py --validar-manifiesto      # nuevo: sale 0 si el manifiesto v7 es válido
python Ads/_TOOLS/verificar_guia_madre.py
python Ads/_TOOLS/verificar_producto.py --todos
python Ads/_TOOLS/gen_grafo.py --comparar               # "rutas muertas: ninguna"

cd app/backend  && uv run --no-sync pytest -q            # 25 pruebas
cd ../frontend  && pnpm test && pnpm build                # 11 pruebas + build
cd ../frontend  && pnpm exec playwright test               # 4 pruebas (usa VITALCOM_BASE del entorno)
```

Nota: `VITALCOM_BASE` acá apunta al **worktree** (`SISTEMA-app`), no a la carpeta real, porque el
manifiesto v7 y `test_gen_app.py` solo existen ahí. El resto del traspaso original (§2 de
`HANDOFF_2026-09-18_APP_HITO3.md`) usa `VITALCOM_BASE` apuntando a la carpeta real `SISTEMA` para
las pruebas que leen data real de productos (Playwright, `test_alta_por_la_app.py`) — las dos
formas conviven, revisar cada prueba si un camino falla y el otro no.

---

## 4 · Una trampa nueva, pisada en esta sesión (sumarla a las de §3 del handoff original)

**Un literal de ruta falsa en un archivo `.py` (por ejemplo, en un fixture de prueba) puede
disparar una falla real en `gen_grafo.py --comparar`.** `gen_grafo.py` es el gate de rutas
muertas del SISTEMA: escanea el texto crudo de todos los `.py`/`.md` y cualquier cosa entre
comillas con forma de ruta (`"Ads/_TOOLS/algo.py"`, `"DOCTRINA/algo.md"`, etc.) que no exista en
disco sale como "RUTA MUERTA", con el archivo de origen. Si una prueba necesita una ruta que a
propósito NO existe (para probar la rama de "referencia rota" de una validación), hay que partir
el literal en dos concatenados — `"Ads/_TOOLS" + "/no_existe.py"` — para que el escaneo estático
no la lea como una cita completa. Ver `Ads/_TOOLS/test_gen_app.py`, las constantes `_ADS_TOOLS` /
`_DOCTRINA` / `_PRODUCTOS` cerca del inicio del archivo, y su comentario.

---

## 5 · Qué sigue: PARTE 2 del Hito 3 (puntos 4 a 10 de la lista del diseño, §6)

Texto completo del diseño en `DISENO_HITO3_ACCIONES_DBOS_2026-09-18.md`. Resumen de cada punto y
dónde está su detalle:

4. **`app/backend`: `acciones.py` + `GET/POST /api/acciones`**, con los códigos 403/409/422/428/503
   del contrato (diseño §2.5). Todavía SIN DBOS: el POST válido puede devolver 501 hasta el punto 6.
   Mirar §3.1 (responsabilidades de `acciones.py`: carga y tipa el manifiesto, valida parámetros,
   **resuelve el argv** — es el único lugar que sabe qué es una acción).
5. **`escrituras.Cola` con latido y espera** (reemplaza el candado que caduca a los 15 min —
   trampa 2 del handoff original, §3.3 del diseño) + **`bitacora.py`** nuevo (único módulo con
   permiso de escribir bajo `PRODUCTOS/_AUDITORIAS/app_runs/`, prueba estructural igual que
   `subidas.py`, §3.9) + sumar `app_runs/` a `.gitignore`.
6. **`dbos` en `pyproject.toml`** (parar el servidor antes de `uv sync` — trampa 1 del handoff
   original) + `workflows.py` con `wf_unidad` y `wf_script` + `APP_VERSION` y
   `test_version_de_workflows` (§3.2, §3.3, §3.5(a)(b), §3.7) + el `POST /api/acciones` real +
   migrar `alta_producto` y `transcribir` a pasar por el runner.
7. **`claude.py`** (único punto que invoca Claude Code headless, contrato completo en §3.8) +
   `fake_claude.py` (para pruebas, sin tocar Claude real) + `wf_claude` con el manejo de preguntas
   del operador vía `PREGUNTA_OPERADOR:` / `DBOS.recv` (§3.5(c)). Confirmar con una corrida corta
   real si `--resume <session_id>` funciona en modo `-p` (no estaba en el spike original).
8. **`wf_meta` completo, contra fakes únicamente** (§3.5(e)) — el mecanismo entero de aprobación
   por hash, snapshot fresco, comparación de llamadas, `caduca_horas`. **Sin habilitar ninguna
   acción que toque Meta en el manifiesto**: siguen todas en `habilitada: false`.
9. **`sse.py`** + endpoints de trabajos (§3.10) + pantalla **Trabajos** en el frontend (lista,
   estado, log en vivo, aprobar/rechazar con la orden a la vista, responder, reintentar, cancelar,
   trabajos de otra versión). Regenerar los tipos del frontend desde el OpenAPI.
10. **Gate §2.6 de la hoja de ruta completo, commit y push en `feat/app-web`, PR a `main`.**
    Mergear **solo con confirmación del operador**.

Las pruebas que cada punto tiene que dejar en verde están en la tabla del diseño, §4 (una fila por
criterio de aceptación: 403 por acción no declarada, dos escrituras que se serializan, una caída a
mitad de un paso idempotente que retoma solo, una de Claude que queda `INTERRUMPIDO` con rastro,
Meta que nunca ejecuta sin aprobación, una aprobación que caduca, etc.).

---

## 6 · Cuándo parar y avisar al operador

El diseño (Opus) ya resolvió el CÓMO de todo el Hito 3, así que los puntos 4-10 son
**implementación**, y el traspaso original ya autorizó hacerla en Sonnet (handoff §6, punto 1: "
implementarlo después con Sonnet está bien"). Aun así, parar y avisar si:

1. **Algo de lo que se está implementando no calza con lo que el diseño describe** (por ejemplo,
   `--resume` no funciona como se esperaba en el punto 7, o una primitiva de DBOS no existe con el
   nombre que asume el diseño en §3.2 — "si alguna no existe con ese nombre, se reemplaza por su
   equivalente sin cambiar la forma", pero si el reemplazo cambia el comportamiento, se avisa).
2. **Cualquier cosa que termine ejecutando algo de verdad en Meta.** No debería pasar en este
   Hito — todas las acciones que tocan Meta quedan deshabilitadas — pero si en algún punto hiciera
   falta habilitar una para probar, eso es del Hito 4/5, en Opus, con confirmación del operador
   (invariante 13).
3. **La doctrina y el código dicen cosas distintas.** Se pregunta, no se elige.
4. Antes de mergear el PR a `main`, cambiar de rama la carpeta real `SISTEMA`, o pedirle al
   operador que instale/cambie algo en su máquina (por ejemplo, una versión de DBOS).

---

## 7 · Cómo hablarle al operador

No programa. Quiere claridad: qué se hizo, qué quedó, qué necesita de él. Español simple, sin
jerga (y si hay jerga, una línea explicándola). Decidir cuando la data alcanza; no devolverle
elecciones técnicas de implementación. Pedir confirmación antes de: mergear, cambiar de rama la
carpeta real, cualquier acción en Meta, borrar algo, o pedirle instalar/configurar algo nuevo en
su máquina.
