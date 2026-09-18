# INFORME · HITO 3 · el motor de ejecución · 18-sep-2026

Rama `feat/app-web` (worktree `../SISTEMA-app`). Sin tocar Meta, sin mergear, sin cambiar de rama la
carpeta real. El diseño es `DISENO_HITO3_ACCIONES_DBOS_2026-09-18.md`; esto dice dónde quedó.

## Qué se hizo (puntos 1-10 del diseño §6)

| # | Qué | Dónde |
|---|---|---|
| 1-3 | Bloque `acciones` del manifiesto v7, validado por `gen_app.py` (19 reglas) | `VISTAS/_MANIFIESTO.json`, `Ads/_TOOLS/gen_app.py`, `test_gen_app.py` |
| 4 | Acciones y API con los 403/409/422/428/503 del contrato | `acciones.py`, `api_acciones.py` |
| 5 | Cola de escritura con latido, espera con tope y detección de dueño muerto; bitácora de corridas | `escrituras.py`, `bitacora.py` (`app_runs/` va a `.gitignore`) |
| 6 | Runner DBOS: `wf_unidad`, `wf_script`, `APP_VERSION`, alta migrada al runner | `workflows.py`, `main.py` |
| 7 | Claude Code headless (`claude.py`), `fake_claude.py`, `wf_claude` con preguntas del operador | `claude.py`, `workflows.py` |
| 8 | `wf_meta` completo (aprobación por huella, snapshot fresco, subconjunto de lo aprobado, caducidad, evento sin duplicar), **contra fakes** | `workflows.py`, `tests/meta_falso.py` |
| 9 | API de trabajos, SSE con `Last-Event-ID`, pantalla **Trabajos** (lista, log en vivo, aprobar/rechazar con la orden a la vista, responder, reintentar, cancelar, otra versión) | `trabajos.py`, `api_trabajos.py`, `sse.py`, `Trabajos.tsx` |
| 10 | Este informe + gate completo + commit + push | — |

**Ninguna acción que toque Meta está habilitada** en el manifiesto (una prueba lo exige). Habilitar
publicar, activar y órdenes es del Hito 4-5, en Opus.

## Gate §2.6 — todo en verde

- 16 `test_*.py` de `Ads/_TOOLS/` · `flujo.py --validar` · `gen_app.py --validar-manifiesto` (v7) ·
  `verificar_guia_madre.py` (sin fallas) · `verificar_producto.py --todos` (5/5) ·
  `gen_grafo.py --comparar` (rutas muertas: ninguna)
- backend: **123 pruebas** (pytest) · frontend: **20 pruebas** (vitest) + build · Playwright: **7 pruebas**

Además se miró la pantalla con un servidor de demostración sobre un sistema de juguete (Meta y Claude
falsos): la orden se ve completa, se aprueba, se ejecuta, se verifica, se registra el evento y el trabajo
termina "terminó bien".

## Medido en vivo (no supuesto)

- `claude -p --resume <session_id>` funciona en modo `-p`: misma sesión, recordó la palabra de la primera
  vuelta (costo equivalente ~US$0.10, con la suscripción no se cobra). Cierra el punto 3.5(c) del diseño.

## Desvíos respecto del diseño (todos de forma, ninguno de comportamiento)

1. **DBOS 3.0**: las colas se crean con `DBOS.register_queue(...)` después de `DBOS.launch()`, no con `Queue(...)`.
2. **Reintentar = trabajo nuevo con los mismos parámetros y corrida completa**, no un `fork` de DBOS: el sello
   y una aprobación no se heredan, así que el fork no reutilizaba nada útil, y heredaba la marca de "empezó y no
   terminó". Pasa por las mismas puertas que un pedido (confirmación, nodo listo, sesión de Claude).
3. **El candado de la cola también mira si el dueño sigue vivo** (no solo el latido de 120 s): tras una caída, el
   trabajo retoma en segundos y no a los 2 minutos.
4. Una unidad que se cae a mitad **devuelve** `INTERRUMPIDO` en vez de levantar una excepción (mismo efecto, sin
   pasar excepciones por DBOS).
5. `test_version_de_workflows` guarda una huella por versión en `HUELLAS` (en el test): cambiar los pasos sin
   subir `APP_VERSION` y sin agregar la fila falla.

## Lo que queda (no era de este Hito)

- **Hito 4, en Opus:** habilitar `F1/F2/F3.publicar`. Falta el spike de `ads_creative_upload_media` con
  `LOCAL_FILE` (abre un widget) en headless, y sumar esa herramienta a `herramientas_meta.escritura` de las
  acciones de publicar (el generador la emite y hoy no está declarada; `wf_meta` falla con un mensaje claro si
  una orden usa una herramienta no declarada).
- **Hito 4-5, en Opus:** `F1.activar`, `F2.activar` y `ciclo.ordenes` (faltan `gen_ordenes.py`,
  `verificar_orden.py` y el generador de la orden de activación).
- Spike de `claude-in-chrome` en headless antes de habilitar `F2.conceptos` (`etapa-render`).
- ~~Los escritores de `cuenta_alias`, `page_id` y del costo de un producto con fila~~ — hechos (18-sep, preparación
  del Hito 4): `cargar_cuenta.py`, `cargar_page_id.py` y `cambiar_costo.py` con su test, declarados en el
  manifiesto (`producto.cargar_cuenta` · `producto.cargar_page_id` · `producto.cambiar_costo`, internas) y
  enlazados desde `F1.congelar_inputs` (costo) y `F1.publicar` (cuenta y page_id).
- **Al mergear a `main`** (con confirmación del operador): regenerar la carpeta real. Hasta entonces la app que
  lee `../SISTEMA` ve el manifiesto v6: `GET /api/acciones` vacío y todo `POST` da 403.
- La PR #3 (Hito 2) sigue abierta y sin mergear.

## Cómo verificar

```bash
export PATH="$HOME/AppData/Roaming/Python/Python314/Scripts:$PATH"
export VITALCOM_BASE="<ruta al worktree SISTEMA-app>" PYTHONIOENCODING=utf-8
cd ../SISTEMA-app
for t in Ads/_TOOLS/test_*.py; do python "$t" >/dev/null || echo "FAIL $t"; done
python Ads/_TOOLS/flujo.py --validar && python Ads/_TOOLS/gen_app.py --validar-manifiesto
python Ads/_TOOLS/verificar_guia_madre.py && python Ads/_TOOLS/verificar_producto.py --todos
python Ads/_TOOLS/gen_grafo.py --comparar
cd app/backend  && uv run --no-sync pytest -q            # 123 pruebas, ~3 min
cd ../frontend  && pnpm test && pnpm build && pnpm exec playwright test   # 20 + build + 7
```

Trampa nueva de esta sesión: `test_workflows.py` y `test_claude.py` usan **procesos hijos que mueren de verdad**
(`driver_caida.py`); si una prueba de caída se cuelga, revisar que no quede un `python` huérfano.
