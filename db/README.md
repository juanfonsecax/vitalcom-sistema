# db/ — Postgres local para VITALCOM (P1-cimientos T5/T6/T2b/T5b)

Dos capas en Postgres, construidas desde `PRODUCTOS/*.csv` (que **siguen siendo la fuente de
verdad durante P1** — CLAUDE.md, invariantes 10/11: esto no cambia ningún lector ni escritor real
todavía, eso es P3):

- **`raw`** — espejo VERBATIM de cada CSV: mismas columnas, mismo orden, texto tal cual. Es la
  capa de auditoría/staging. Se llamó `core` en T5; T5b la renombró para dejarle el nombre `core`
  al modelo normalizado.
- **`core`** — modelo NORMALIZADO y TIPADO (producto → ángulo → creativo/concepto →
  conjunto/anuncio con historial de nombre → hechos diarios tipados), construido **desde `raw`**
  por `db/nucleo.py`, en la MISMA transacción que carga `raw`. Nunca se llena a mano.

## Cómo correr

Requiere Postgres 18 local (rol/db `vitalcom`, credenciales en
`~/.config/vitalcom_db/.env`: `PGHOST/PGPORT/PGDATABASE/PGUSER/PGPASSWORD`) y el intérprete del
venv de `SISTEMA-app` (ya tiene `psycopg`; no instala nada nuevo):

```
# 1. Aplicar el esquema (idempotente: CREATE SCHEMA/TABLE IF NOT EXISTS; migra un `core` viejo de
#    T5 a `raw` automáticamente la primera vez, ver "Migración" abajo)
"C:\Program Files\PostgreSQL\18\bin\psql.exe" -f db/schema.sql

# 2. Cargar PRODUCTOS/*.csv -> raw, y construir core -> a partir de raw (todo en una transacción)
"..\SISTEMA-app\app\backend\.venv\Scripts\python.exe" db/cargar.py

# 3a. Exportar raw -> CSV completos (auditoría/staging, T5)
"..\SISTEMA-app\app\backend\.venv\Scripts\python.exe" db/exportar.py --out C:\ruta\salida --modo raw

# 3b. Exportar core -> los 9 CSV que decidir.py lee (lo que usa el gate de paridad, T5b)
"..\SISTEMA-app\app\backend\.venv\Scripts\python.exe" db/exportar.py --out C:\ruta\salida --modo core

# 4. Pruebas (puras + integración; la de integración se salta sola sin Postgres)
"..\SISTEMA-app\app\backend\.venv\Scripts\python.exe" -m pytest db/test_db.py -q
```

`cargar.py` es **idempotente por TRUNCATE + reinserción, en una sola transacción por corrida**
(raw) seguida de la reconstrucción completa de `core` (DELETE + INSERT...SELECT, misma
transacción): si algo falla a mitad, `ROLLBACK` completo — nunca queda una tabla a medio cargar.
Dos corridas seguidas sobre los mismos CSV dejan el mismo conteo de filas en `raw` Y en `core`, y
el mismo reporte de reconciliación (probado en
`test_db.py::test_cargar_es_idempotente_en_conteo_de_filas`). `main()` imprime el reporte
completo: conteos por tabla `core`, FK sin resolver por razón, y conservación raw→core de los 3
hechos (venta, entrega_anuncio_dia, entrega_conjunto_dia).

## Migración T5b (automática, una sola vez)

`db/schema.sql` trae un bloque `DO $mig$` que, si encuentra un schema `core` SIN que exista
todavía un `raw` (es decir: una base que corrió T5 pero no T5b), lo renombra
(`ALTER SCHEMA core RENAME TO raw`) y le quita a `raw.venta` las 2 columnas de enriquecimiento que
tenía el `core` de T5 (`ad_id_resuelto`, `metodo_atribucion` — ese enriquecimiento vive ahora solo
en el `core` normalizado nuevo). En una base nueva, o en una que ya tiene `raw`, este bloque no
hace nada.

## `raw` — espejo verbatim

Ver `db/tables.py` (fuente única de la lista de tablas y su CSV dueño). Regla general: **cada
tabla es un espejo verbatim de su CSV** — mismas columnas, mismo orden, texto tal cual (sin cast),
más `tenant_id` (single tenant `'vitalcom'`; RLS no habilitado en P1) y un `id BIGSERIAL`. Desde
T5b, `raw` NO tiene columnas extra ni casos especiales — ni siquiera `venta` (el enriquecimiento
de venta se calcula al construir `core`, ver abajo). `raw.raw_import` sigue siendo la auditoría de
carga (`archivo, sha256, filas, loaded_at`, una fila por archivo por corrida).

Nota operativa: si un CSV agrega una columna nueva (como pasó con `_MAPA_AD_ID_HIST.csv:venta_uid`
en T2b) sobre una tabla `raw` que ya existía de una corrida anterior, `CREATE TABLE IF NOT EXISTS`
no la habría agregado por sí sola — por eso `schema.sql` emite además un
`ALTER TABLE ... ADD COLUMN IF NOT EXISTS <col> TEXT` por cada columna esperada, siempre seguro de
re-correr.

## `core` — modelo normalizado y tipado (T5b)

Construido por `db/nucleo.py:construir_core()`. Entidades (ver su DDL, `nucleo.CORE_DDL_SQL`,
también volcado al final de `db/schema.sql`):

- **`tenant` / `producto` / `cuenta`** — dimensiones base, con casts numéricos donde aplica
  (`tasa`, `costo_q`, `precio_base_q`, `cpa_*_q`, `min_daily_budget_cents`) y `raw_id` apuntando a
  la fila `raw` de origen.
- **`angulo`** — ahora es una TABLA física (en T5 era una vista sobre `conjunto`): distinct por
  `(tenant_id, producto_id, angulo_key)`, atributos tomados de `_DIM_CONJUNTOS.csv`
  (`angulo_nombre, avatar, dolor_nucleo, emocion_dominante, avatar_edad, avatar_genero,
  nivel_conciencia`); `deseo` sigue `NULL` (no hay columna fuente todavía).
- **`catalogo_concepto`** — distinct de `concepto_key` visto en `conjunto` + `creativo`. Su
  atributo completo (nombre, evidencia) sigue viviendo en `Ads/_SWIPE/_CATALOGO_CONCEPTOS.md`
  (prosa, no CSV) — fuera de alcance normalizarlo, igual que en T5; esta tabla solo le da un FK
  estable a `conjunto`/`creativo`/`anuncio`.
- **`conjunto_nombre_hist`** — reemplaza la semántica de `_ALIAS_CONJUNTOS.csv`/`alias.py`:
  `alias_nombre` (columna `nombre_viejo` del CSV) → `nombre_canonico` (`nombre_nuevo`), con
  `valid_from` (`desde`). `valid_to` queda `NULL`: `alias.py` resuelve por diccionario (nombre →
  nombre canónico "final"), no por rango de fechas, así que no hay una fecha de cierre que
  inventar sin arriesgar un dato falso — se documenta como límite, no se resuelve con una fecha
  adivinada.
- **`conjunto` / `creativo` / `anuncio`** — igual que `raw` pero con FK a
  `producto/angulo/cuenta/catalogo_concepto` (`conjunto`, `creativo`) y a `conjunto` (`anuncio`,
  vía un salto de indirección por `conjunto_nombre_hist` cuando el nombre cambió). `anuncio` se
  construye distinct desde `entrega_anuncio_dia` (ya trae `ad_id`/`angulo_key`/`concepto_key`/
  `canonico_id` por fila).
- **`entrega_conjunto_dia` / `entrega_anuncio_dia`** — hechos diarios TIPADOS (`ventana_ini/fin`
  `DATE`, `dias/mensajes/clicks*/impresiones` `INTEGER`, `spend_usd/pct_conv_clic_enlace`
  `NUMERIC`), con FK a `producto/cuenta/conjunto` (y a `anuncio` en el caso de
  `entrega_anuncio_dia`).
- **`venta`** — hecho tipado + el mismo enriquecimiento de T5 (`ad_id_resuelto`,
  `metodo_atribucion`), MÁS `venta_uid` (T2b, ver más abajo). El join a
  `_MAPA_AD_ID_HIST.csv` se calcula en Python (`cargar.enriquecer_venta`, reusado por
  `nucleo.construir_core`) y se inserta ya resuelto — no hay una segunda copia de esa lógica en
  SQL.
- **`evento` / `decision` / `parametro_decision` / `parametro_finanzas` / `banda` /
  `estado_flujo`** — el resto de lo que `decidir.py` (vía `gasto.py`/`alias.py`) lee directamente,
  con el mismo patrón (copia tipada + FK + `raw_id`). `decision` no tiene CSV dueño (viene de
  `_DECISIONES.json`): vive solo en `core`, no en `raw`.
- **"Versionado" de parámetros**: `parametro_decision`/`parametro_finanzas` traen una columna
  `version` (`TIMESTAMPTZ`, el momento de la carga). Es una limitación honesta, no un historial
  real: los CSV fuente (`_PARAMETROS_DECISION.csv`, `_PARAMETROS_FINANZAS.csv`) no traen una
  columna de versión propia, y cada carga es una foto completa (TRUNCATE+INSERT, igual que `raw`),
  no un append-only. Si P3 necesita un historial real de parámetros, ese es un cambio de alcance,
  no algo que esta tabla ya resuelve.

### Regla dura de reconciliación

Cuando un valor de CSV no puede satisfacer un FK o un tipo, la fila **NO se descarta**: se guarda
con el FK/tipo en `NULL` y se cuenta en el reporte de `construir_core()`. Nunca se inventa un
valor para que un cast o un JOIN "cierre". Hallazgo real, no oculto: `_DIM_CONJUNTOS.csv` usa
`cuenta_alias` sin espacio (`"GTR7"`) y `_DIM_CUENTAS.csv` lo trae con espacio (`"GTR 7"`) — el
join normaliza espacios (`replace(cuenta_alias, ' ', '')`) para no fallar por ese formato, pero
igual quedan sin resolver los `cuenta_alias` compuestos multi-cuenta (`"GTR0/GTR7/GTR13/CP1"`) y
`"EXTERNA"` (no tiene fila en `_DIM_CUENTAS.csv`) — 19 de 173 filas de `conjunto` reportan
`cuenta_id` sin resolver, documentado, no corregido con una cuenta inventada.

## El gate de paridad (T6, sobre `core` desde T5b)

`test_db.py::test_parity_gate_decidir_exportado_igual_a_real`:

1. Carga (`cargar_todo()`: `raw` + `core`).
2. Exporta `core` -> un directorio temporal, pero **solo los 9 CSV que `decidir.py` (vía
   `gasto.py`/`alias.py`) lee directamente**: `_PARAMETROS_DECISION.csv`, `_DIM_PRODUCTOS.csv`,
   `_DIM_CONJUNTOS.csv`, `_DIM_BANDAS.csv`, `_ALIAS_CONJUNTOS.csv`, `_FACT_VENTAS.csv`,
   `_FACT_ENTREGA.csv`, `_FACT_ENTREGA_ANUNCIO.csv`, `_ESTADO_FLUJO.csv`
   (`exportar.exportar_core_decidir()`).
3. Corre `Ads/_TOOLS/decidir.py --json` **dos veces, en un subproceso aparte**: una vez sin
   variables de entorno (lee `PRODUCTOS/` real) y otra con `DECIDIR_PROD_DIR=<tmp>` (lee la base
   exportada desde `core`).
4. Compara ambos JSON, ignorando solo la clave `generado`. Cualquier otra diferencia es `FAIL`, no
   se enmascara. **Nunca cae de vuelta a exportar desde `raw`** si algo en `core` no resuelve: eso
   sería ocultar exactamente lo que este gate existe para probar.

Por qué esto prueba más que T5: en T5 el export salía de un espejo verbatim de los mismos CSV
(`exportar_raw_todo`, que sigue existiendo para auditoría) — el round trip pasaba trivialmente.
Desde T5b el export sale del modelo NORMALIZADO reconstruyendo cada columna desde tablas
separadas con FK y casts tipados: que `decidir.py` dé el mismo resultado byte a byte prueba que
`core` sostiene lo que el motor de decisión necesita, no solo que el archivo vuelve intacto.

**Por qué subproceso y no import directo:** `decidir.py` importa `scipy` y `duckdb`, que no
viven en el venv de `psycopg` (y no está autorizado instalar nada). El intérprete `python` del
PATH sí trae `scipy`+`duckdb` (confirmado: 3.14, scipy 1.18, duckdb 1.5) pero no `psycopg`. El
gate corre `cargar.py`/`exportar.py` con el venv de `psycopg` y `decidir.py` con ese otro
intérprete, comunicados por archivos (la base exportada) y variables de entorno — nunca por un
`import` en el mismo proceso.

**`DECIDIR_PROD_DIR`** es el único cambio en `Ads/_TOOLS/decidir.py` para este gate: un override
de módulo, mínimo y retro-compatible (sin la variable, comportamiento idéntico al de siempre —
ver `test_decidir_prod_dir_override_es_retrocompatible`).

## T2b — identidad estable de fila (`venta_uid`)

El join histórico original entre `_MAPA_AD_ID_HIST.csv` y `_FACT_VENTAS.csv` era por
`(ventana_ini, cuenta_alias, conjunto, anuncio)` + orden de aparición (FIFO): esa llave se repite
en 150 grupos del mapa real, así que la correspondencia dependía de que el ORDEN de
`_FACT_VENTAS.csv` nunca cambiara entre la corrida que generó el mapa y la que lo consume.

`venta_uid` (`Ads/_TOOLS/venta_identidad.py:asignar_venta_uids`) reemplaza esa dependencia
posicional: es un `sha256` del CONTENIDO completo de cada fila de venta (todas sus columnas, en
el orden real del CSV). Sobrevive a un reordenamiento porque no depende de la posición. El único
caso que un hash de contenido no distingue por sí solo son duplicados EXACTOS byte a byte — se
comprobó sobre `_FACT_VENTAS.csv` real: existen 9 grupos así (22 filas de 3407). Para esos casos
se agrega un contador de ocurrencia (0, 1, 2...) según el orden de aparición; como el contenido es
idéntico, las filas gemelas resuelven al MISMO ad_id/método de todos modos, así que el orden en
que se reparte el sufijo no cambia la atribución resultante.

`mapear_ad_id_hist.py` emite `venta_uid` como columna nueva de `_MAPA_AD_ID_HIST.csv` (regenerado
desde el staging ya cacheado, sin red); `db/cargar.py:enriquecer_venta()` la calcula sobre
`_FACT_VENTAS.csv` en el momento de cargar y hace el join por `venta_uid` (dict simple, no
FIFO). Coverage sin cambios: 670 verificados por gasto / 724 por nombre / 1360 con ad_id original
/ 653 sin atribuir, sobre 3407 filas.

## Qué NO hace esto todavía (fuera de alcance de P1)

- Ningún lector ni escritor real (decidir.py, flujo.py, gen_*.py, etc.) lee de Postgres: siguen
  leyendo los CSV. Cambiar eso es P3.
- No hay Row-Level Security ni más de un tenant: `tenant_id='vitalcom'` es un valor fijo, no una
  política.
- No hay `UPDATE`/`upsert` incremental: cada carga es un reemplazo completo (`raw` y `core`). Para
  un dataset de este tamaño (~7700 filas en `raw`) es más simple y más fácil de auditar que un
  upsert parcial; se puede revisar si P3 necesita cargas incrementales de verdad.
- `parametro_decision`/`parametro_finanzas.version` NO es un historial temporal real (ver arriba).
- `conjunto_nombre_hist.valid_to` siempre `NULL` (ver arriba): no reemplaza una consulta "¿qué
  nombre tenía este conjunto en tal fecha?", solo la resolución "¿cuál es su nombre canónico hoy?"
  que ya hacía `alias.py`.
