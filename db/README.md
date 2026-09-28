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

## P3 — inventario de escritores (T1, 2026-09-25)

Qué programa escribe cada archivo de `PRODUCTOS/` y qué destino tiene en P3. Regla que decide la
columna "P3": un archivo que el operador edita a mano **queda en CSV** (entra por `raw` como hoy)
hasta P3b; solo pasa a Postgres lo que escriben exclusivamente los programas. Un archivo
**derivado** (recalculado entero desde otros datos) no es fuente de verdad: sigue siendo un
archivo generado.

### Pasan a Postgres (`core` es la verdad, el CSV es espejo)

| Archivo | Escritor actual | Modo | Tabla `core` | Tarea |
|---|---|---|---|---|
| `_FACT_VENTAS.csv` | `ingerir_lucidsales.py:516` → `upsert_fact.upsert()` | upsert | `venta` | T3 |
| `_FACT_ENTREGA.csv` | `ingerir_meta.py:400` / `bajar_meta_insights.py:405` → `upsert_fact.upsert()` | upsert | `entrega_conjunto_dia` | T3 |
| `_FACT_ENTREGA_ANUNCIO.csv` | `ingerir_meta.py:400` / `bajar_meta_insights.py:409` → `upsert_fact.upsert()` | upsert | `entrega_anuncio_dia` | T3 |
| `_EVENTOS.csv` | `registrar_evento.py:113 anexar()` y `:148 registrar_excepcion()` (la llama `gen_publicacion.py`), `flujo.py:1329`, `perfilar_angulos.py:434` (`--registrar`), `reingreso_f1.py:63` | append (5 escritores sin helper común) | `evento` | T4 |
| `_DECISIONES.json` | `decidir.py:1010` (`--escribir`) | reescritura | `decision` | T4 |
| `_ESTADO_FLUJO.csv` | `flujo.py:1306 escribir_estado()` (`--todo --escribir`) | reescritura | `estado_flujo` | T4 |
| `_DIM_PRODUCTOS.csv` | `alta_producto.py:269` (fila nueva; la dispara la app vía `_MANIFIESTO.json`), `editar_producto.py:141` (lo llaman `cambiar_costo.py`, `cargar_cuenta.py`, `cargar_page_id.py`) | reescritura atómica | `producto` | T4 |

`upsert_fact.upsert()` (`upsert_fact.py:131`) es el único escritor de los tres hechos: es el punto
natural donde cambiar el destino en T3.

### Quedan en CSV durante P3

- **Editados a mano por el operador** (sin escritor en el código): `_DIM_COSTEO`, `_DIM_CONJUNTOS`,
  `_DIM_BANDAS`, `_ALIAS_CONJUNTOS`, `_DIM_BM`, `_DIM_CUENTAS`, `_DIM_FANPAGES`, `_DIM_FLUJO_BOT`,
  `_DIM_GASTOS`, `_DIM_MERCADOS`, `_DIM_PRECIOS`, `_DIM_TARJETAS`, `_ESTADO_META`,
  `_FACT_FACTURACION`, `_FACT_FACTURACION_AGREGADO`, `_FACT_PAUTA_REAL`, `_FACT_SALDOS`,
  `_FACT_SEMANAL`, `_PARAMETROS_DECISION`, `_PARAMETROS_FINANZAS`, `_PARAMETROS_OPTIMIZACION`,
  `_PARAMETROS_PUBLICACION`, `_TASA_ENTREGA`, `_TESTEOS`, `_CLASIFICACION_ANUNCIOS`,
  `_APRENDIZAJES`.
- **Híbridos (mano + programa)**, quedan en CSV por la misma regla:
  - `_DIM_CREATIVOS.csv`: el operador crea las filas y `verificar_publicacion.py:263` reescribe el
    archivo para completar `ad_id`.
  - `_DIM_ENVASE.csv`: `alta_producto.py:275` escribe la fila del producto nuevo y el operador la
    corrige a mano.
- **Derivados** (se recalculan enteros; no son verdad): `_DIM_ANUNCIOS` (`sembrar_anuncios.py --escribir`,
  único escritor; también persiste la columna `firma`, que `firma.py` solo calcula y muestra),
  `_ESTADO_ANGULOS` (`perfilar_angulos.py:424`), `_DIM_VOCABULARIO` (`gen_vocabulario.py:115`),
  `_MAPA_AD_ID_HIST` (`mapear_ad_id_hist.py:315`), `_FLUJO.json` (`flujo.py:1622`).
- **Sin archivo todavía:** `_VOZ_CLIENTE.csv` (escritor `verificar_voz.py` → `upsert_fact`; no
  tiene tabla `core`).
- **Sin uso:** `_MAPEO_CREATIVOS.csv` (solo aparece en `db/tables.py`).
- **Sin fila en `TABLE_SPECS` (deliberado):** `_DIM_REFERENCIA_F1.csv` (escritor
  exclusivo `Ads/_TOOLS/referencia_f1.py --elegir`, upsert por `producto_key`). Agregar una fila sin
  aplicar el `schema.sql` regenerado contra el Postgres real rompería `cargar_todo()` (hace
  `TRUNCATE TABLE raw.<tabla>` incondicional para toda fila de `TABLE_SPECS`, exista o no la
  tabla). No lo necesita ningún guardia automático: `hook_csv.py` valida su estructura como a
  cualquier CSV de `PRODUCTOS/`, y el drift guard de `ciclo_diario.py` solo vigila
  `TABLAS_MIGRADAS_DB`. Si se quiere mirror en Postgres más adelante, agregar la fila a
  `TABLE_SPECS`, regenerar `schema.sql` (`python db/tables.py`) y aplicarlo contra la base real.

El backend de la app no escribe ningún CSV (`app/backend/vitalcom_app/contratos.py:3`): toda
escritura pasa por un ejecutor de `Ads/_TOOLS/` declarado en `VISTAS/_MANIFIESTO.json`.

## P3 T2 — capa de escritura Postgres + espejo CSV (`db/escribir.py`)

Construye el sentido inverso (Postgres -> verdad, CSV -> espejo) para las 7 tablas DB-truth de T1
(`_FACT_VENTAS`, `_FACT_ENTREGA`, `_FACT_ENTREGA_ANUNCIO`, `_EVENTOS`, `_DECISIONES.json`,
`_ESTADO_FLUJO`, `_DIM_PRODUCTOS`). **T2 no conecta ningún llamador real** (`ingerir_*`,
`bajar_*`, `flujo.py`, `decidir.py`, `registrar_evento.py`, `alta_producto.py` siguen escribiendo
CSV directo) — eso es T3/T4. Uso:

```python
import sys
sys.path.insert(0, "db")
import cargar, escribir

con = cargar.conectar()
try:
    # upsert por llave, misma mecánica que Ads/_TOOLS/upsert_fact.upsert() (fusionar(), compartida)
    reemp, nuevas, sin_cambio = escribir.upsert(
        con, "venta", filas_nuevas,
        key=("ventana_ini", "cuenta_alias", "conjunto", "anuncio"),
        prod_dir=PRODUCTOS_DIR,  # regenera PRODUCTOS/_FACT_VENTAS.csv tras el commit
    )

    # append puro (_EVENTOS.csv: nunca reemplaza una fila existente)
    escribir.anexar(con, "evento", filas_evento, prod_dir=PRODUCTOS_DIR)

    # reescritura completa (_ESTADO_FLUJO.csv / _DIM_PRODUCTOS.csv: el escritor real siempre
    # reescribe el archivo entero, no hace merge por llave)
    escribir.reemplazar(con, "estado_flujo", filas_estado, prod_dir=PRODUCTOS_DIR)

    # _DECISIONES.json (sin CSV/tabla raw columna-por-columna propia -- vive en raw.decisiones_json)
    escribir.reemplazar_decision(con, payload_decidir, prod_dir=PRODUCTOS_DIR)
finally:
    con.close()
```

Diseño (ver `odd/tasks/p3-postgres-verdad.md`):
- La verdad vive en `raw.<tabla>` (filas verbatim); cada llamada reconstruye `core` ENTERO desde
  `raw` con `nucleo.construir_core()`, en LA MISMA transacción — nunca se duplica esa lógica.
- El mirror se regenera SOLO después de que el COMMIT ya ocurrió, escrito atómico (`.tmp-escribir`
  + `os.replace`), y es byte-idéntico al que produce hoy el escritor real de ese archivo (CRLF,
  utf-8 sin BOM). Probado por `test_espejo_es_byte_identico_a_los_7_archivos_db_truth` sobre los
  7 archivos reales de `PRODUCTOS/`.
- `_DECISIONES.json` no tiene fila en `tables.TABLE_SPECS` (no es un espejo columna-por-columna):
  vive en `raw.decisiones_json` (texto verbatim, una fila) — `db/cargar.py:cargar_decisiones_json()`
  la carga desde disco, `escribir.reemplazar_decision()` la reescribe. **El mirror y
  `core.decision` NUNCA se regeneran leyendo `core.decision.payload`**: esa columna es `JSONB`, y
  Postgres no garantiza el orden de claves de un objeto JSONB al leerlo de vuelta (defecto real
  encontrado en T2 al comparar bytes) — `escribir.leer_decision_actual()` lee siempre de
  `raw.decisiones_json.contenido`.
- Postgres no disponible, o cualquier paso de la transacción falla -> `escribir.ErrorEscritura`.
  NUNCA cae de vuelta a escribir el CSV a mano. El rollback es EXPLÍCITO (`conn.rollback()`), no
  el `with conn:` de psycopg3: ese context manager deja la conexión CERRADA ante una excepción, lo
  que rompería reusar `conn` para la siguiente escritura o para leer el estado tras el error
  (otro hallazgo de T2, ver `test_escribir_falla_a_mitad_hace_rollback_y_no_toca_el_espejo`).
- `cargar.cargar_todo(incluir_verdad_db=False)` (T2) deja intactas las tablas `raw.*` de
  `tables.TABLAS_VERDAD_DB` (y `raw.decisiones_json`) — necesario para T3/T4, donde `cargar_todo()`
  seguirá recargando el resto de `PRODUCTOS/*.csv` (editados a mano) sin pisar lo que ya escribió
  `db/escribir.py`. Con el default (`True`), el comportamiento es idéntico al de siempre.
- `Ads/_TOOLS/upsert_fact.py:fusionar()` (T2) es la mecánica PURA de merge extraída de
  `upsert_fact.upsert()` — sin I/O, sin backup. `upsert()` es ahora un wrapper delgado de disco
  sobre `fusionar()` (mismo contrato, mismos valores de retorno, probado en
  `Ads/_TOOLS/test_upsert_fact.py`, sin cambios); `db/escribir.upsert()` la reusa tal cual sobre
  `raw.*` en vez de un CSV — un dato, un dueño de la SEMÁNTICA de merge.

## P3 T3 — primeros llamadores reales conectados (`venta`, `entrega_conjunto_dia`, `entrega_anuncio_dia`)

T3 conecta los tres primeros escritores reales del inventario de T1 a `db/escribir.py`:
`Ads/_TOOLS/ingerir_lucidsales.py` (`_FACT_VENTAS.csv` → `venta`) e
`Ads/_TOOLS/ingerir_meta.py` / `Ads/_TOOLS/bajar_meta_insights.py` (`_FACT_ENTREGA.csv` →
`entrega_conjunto_dia`, `_FACT_ENTREGA_ANUNCIO.csv` → `entrega_anuncio_dia`). Desde T3 estos tres
escriben SIEMPRE por `db/escribir.upsert()` (nunca directo al CSV); `PRODUCTOS/_FACT_VENTAS.csv`,
`_FACT_ENTREGA.csv` y `_FACT_ENTREGA_ANUNCIO.csv` son el ESPEJO. `ingerir_meta.py` cambió además de
mecánica: su nivel CONJUNTO era un `append` crudo (nunca pasaba por `upsert_fact`) — ahora entra
por la misma llave natural que ya usaba para el anti-duplicado (`LLAVE_CONJUNTO` en el módulo),
vía `db/escribir.upsert()`.

**`prod_dir` sale de `FACT`/`FACT_AD`, nunca de la constante `PROD`.** Los tres módulos calculan
`prod_dir = os.path.dirname(FACT)` (o `FACT_AD`) dentro de `main()`, no usan la constante `PROD`
directamente en la escritura. Es a propósito: las pruebas monkeypatchean `FACT`/`FACT_AD` a un
directorio temporal (`patch.object(im, "FACT", ...)`), y si el mirror se regenerara sobre `PROD`
igual, escribiría en `PRODUCTOS/` real sin importar el monkeypatch — exactamente el defecto que
apareció en vivo durante el desarrollo de T3 (pruebas con datos ficticios pisando y mezclándose
con `PRODUCTOS/_FACT_ENTREGA*.csv`/`_FACT_VENTAS.csv` reales; corregido, ver
`odd/tasks/p3-postgres-verdad.md` T3 para el detalle completo del incidente y la limpieza).

### `tables.TABLAS_MIGRADAS_DB` — "elegible" vs. "ya conectado"

`tables.TABLAS_VERDAD_DB` (T2) es el conjunto ELEGIBLE completo (las 6 tablas + `decisiones_json`
aparte). `tables.TABLAS_MIGRADAS_DB` (T3, nuevo) es el subconjunto ya CONECTADO a un llamador
real: hoy `{venta, entrega_conjunto_dia, entrega_anuncio_dia, evento, estado_flujo}`; queda
pendiente `producto` para cuando `alta_producto.py`/`editar_producto.py` también escriban por
`db/escribir.py` (ver "P3 T4 (continuación)" abajo). La distinción importa para `db/cargar.py`: una recarga GENÉRICA
(`cargar_todo()`, sin flags — el uso más común) **nunca** vuelve a cargar desde CSV una tabla de
`TABLAS_MIGRADAS_DB`, pase lo que pase con `incluir_verdad_db` (clobbearía la verdad que ya
escribió el llamador real); las tablas `TABLAS_VERDAD_DB` que TODAVÍA no se conectaron siguen el
comportamiento de T2 (gobernado por `incluir_verdad_db`, `True` por defecto = se recargan como en
P1, porque su llamador real sigue escribiendo el CSV directo hasta T4).

### Guardia de drift (`db/escribir.verificar_csv_sincronizado()`)

Antes de CUALQUIER escritura sobre una tabla migrada, los tres llamadores corren este guardia.
Aborta con `escribir.DriftDetectado` (nunca escribe nada) en dos casos:

1. **Nunca se importó.** Se mide por `raw.raw_import` (el log que ya llenaban `cargar_tabla()` y
   ahora también `cargar.tomar_csv()`) filtrando por `(tenant_id, archivo)` — NO por
   `count(*) FROM raw.<tabla> == 0`: un tenant/producto legítimamente nuevo puede empezar con cero
   filas de verdad, y medir por conteo bloquearía para siempre aunque ya se hubiera hecho el
   bootstrap sobre un CSV vacío. Es el caso de la primera corrida real: `raw.venta` está vacía
   porque nadie corrió el bootstrap todavía.
2. **El CSV no es byte-idéntico** a lo que la base exportaría ahora para esa tabla (alguien lo
   editó a mano, o la base quedó desactualizada frente a un cambio externo).

En ambos casos el mensaje trae la recuperación exacta: `python db/cargar.py --tomar-csv <archivo>`.

### `db/cargar.py --tomar-csv <archivo|tabla>`

Recarga UNA sola tabla de `TABLAS_MIGRADAS_DB` desde su CSV en disco — deliberado, nunca
automático. Dos usos: el bootstrap inicial (antes de la primera corrida real de T3, importar el
CSV que hoy YA es la verdad) y la recuperación cuando el guardia de drift aborta. Reconstruye
`core` entero en la misma transacción, igual que `cargar_todo()`. Rechaza con `ValueError`
cualquier tabla que no esté en `TABLAS_MIGRADAS_DB` (no es una forma general de recargar
cualquier CSV — para eso está `cargar_todo()`).

```
"..\SISTEMA-app\app\backend\.venv\Scripts\python.exe" db/cargar.py --tomar-csv _FACT_VENTAS.csv
```

### Backup del mirror (`bkdir`)

`db/escribir.upsert()`/`anexar()`/`reemplazar()` aceptan ahora `bkdir` (opcional, antes solo
`prod_dir`): si se pasa, y hay un cambio que reescribe el mirror, copia el mirror ACTUAL a `bkdir`
justo ANTES de reemplazarlo — mismo patrón y nombrado que `upsert_fact.upsert()`. Es explícito (no
se infiere de `prod_dir`) para que una prueba con `prod_dir` en un directorio temporal no termine
escribiendo en el `_RESPALDOS/` real del repo. Los tres llamadores reales de T3 pasan
`bkdir=BKDIR` (su `_RESPALDOS/backups_csv/` de siempre) para conservar el mismo colchón de
seguridad que tenían con `upsert_fact.upsert()`.

### Aislamiento de pruebas — `vitalcom_test`

Desde T3, `vitalcom` sostiene VERDAD real. Ninguna prueba corre contra ella:

- `db/test_db.py` fuerza `os.environ["PGDATABASE"] = "vitalcom_test"` al importar el módulo
  (antes de que nada intente conectar) y crea/aplica el esquema con
  `cargar.asegurar_base_de_datos("vitalcom_test")` + `cargar.aplicar_schema(dbname="vitalcom_test")`
  si hace falta. `_conectar_seguro()` es el segundo cinturón: rehúsa devolver una conexión cuyo
  `dbname` sea `vitalcom`.
- Las pruebas de `Ads/_TOOLS` que ahora escriben por Postgres (`test_ingerir_lucidsales.py`,
  `test_bajar_meta_insights.py`) hacen lo mismo (mismo override de `PGDATABASE`) y además aíslan
  cada escenario en su propio `TENANT_ID` (los tres llamadores reales exponen ese nombre como
  constante de módulo, sobreescribible), para no interferir entre sí dentro del mismo proceso.
- `cargar.asegurar_base_de_datos(nombre, env=None)` crea la base si no existe (conectando a la
  base de mantenimiento `postgres`, o si falla, a `vitalcom`, con `autocommit=True` — `CREATE
  DATABASE` no puede correr dentro de una transacción). `cargar.aplicar_schema(env=None,
  dbname=None)` aplica `db/schema.sql` completo sobre la base indicada (idempotente, igual que el
  propio archivo).

**Setup único pendiente en este entorno (encontrado en T3, no resuelto acá):** el rol `vitalcom`
de `~/.config/vitalcom_db/.env` NO tiene `CREATEDB` (`SELECT rolcreatedb FROM pg_roles WHERE
rolname='vitalcom'` → `false`) ni es superusuario, así que `asegurar_base_de_datos("vitalcom_test")`
no puede crear la base — devuelve `False` (nunca falla ni cae de vuelta a `vitalcom`) y las
pruebas que dependen de Postgres se SALTAN con mensaje claro, no fallan en falso ni corren contra
la base real. Para que corran de verdad, el operador corre UNA vez, con un rol con privilegios
(`postgres`):
```sql
ALTER ROLE vitalcom CREATEDB;
-- o, equivalente, sin tocar el rol:
CREATE DATABASE vitalcom_test OWNER vitalcom;
```
Después de eso, `db/test_db.py` y las pruebas de `Ads/_TOOLS` que tocan Postgres crean/reusan
`vitalcom_test` solas, sin más intervención.

## P3 T4 — `evento` conectado (`registrar_evento.py`, único escritor de `_EVENTOS.csv`)

T4 conecta el primer escritor de la familia `_EVENTOS.csv`. Antes había CINCO copias
independientes del mismo `csv.DictWriter` con CRLF (`registrar_evento.py:anexar()`/
`registrar_excepcion()`, `flujo.py:escribir_estado()`, `perfilar_angulos.py:registrar_transiciones()`,
`reingreso_f1.py:anexar_evento()`). Ahora `registrar_evento.anexar()` es el ÚNICO escritor: acepta
una fila (dict) o varias (list[dict]) y escribe SIEMPRE por Postgres (`db/escribir.anexar()`), con
el mismo guardia de drift y el mismo patrón `TENANT_ID`/`BKDIR` de override para pruebas que T3.
`flujo.py`, `perfilar_angulos.py` y `reingreso_f1.py` ahora llaman esta función en vez de reescribir
el CSV por su cuenta:

- `reingreso_f1.py:anexar_evento()` redirige temporalmente `registrar_evento.BASE/PROD/EVENTOS` a
  `base_dir` (para fixtures de prueba) y llama `registrar_evento.anexar(fila)`.
- `perfilar_angulos.py:registrar_transiciones()` importa `registrar_evento` de forma LOCAL (dentro
  de la función, no al tope del módulo) y le pasa la lista de filas de transición.
- `flujo.py:escribir_estado()` hace lo mismo (import local) — necesario porque `registrar_evento.py`
  importa `flujo` (para `gate_entrada`); un import a nivel de módulo en `flujo.py` crearía un ciclo.
  Un import diferido dentro de la función es seguro porque para cuando se llama, ambos módulos ya
  terminaron de inicializarse.

`tables.TABLAS_MIGRADAS_DB` suma `"evento"` (T3 tenía solo los tres hechos). `_ESTADO_FLUJO.csv`
(`flujo.py:escribir_estado()`, la reescritura del propio archivo, no el evento de transición que
ya se movió) y `_DIM_PRODUCTOS.csv`/`_DECISIONES.json` **quedan pendientes en este pase** — ver
"P3 T4 (continuación)" abajo para `_ESTADO_FLUJO.csv`/`_DECISIONES.json`, y "P3 T4 (continuación
parte 2)" para `_DIM_PRODUCTOS.csv` (`alta_producto.py`/`editar_producto.py`).

Instrucciones que le decían a un agente que anexara `_EVENTOS.csv` "a mano" (sin pasar por
`registrar_evento.py`) se redirigieron al comando CLI exacto en:
`.claude/agents/ETAPA-11.md`, `.claude/agents/ETAPA-6.md`, `.claude/agents/ETAPA-5.md`,
`DOCTRINA/PLANTILLAS_FLUJO_BOT.md`, `.claude/skills/fase-2-conceptos/SKILL.md` — con el guardia de
drift, un anexo a mano haría abortar la próxima escritura real.

Bootstrap real (25-sep-2026): `PRODUCTOS/_EVENTOS.csv` ya estaba sincronizado con `raw.evento`
(la corrida de sesión `flujo.py --todo --escribir` ya lo había recargado hoy) — verificado con
`db/escribir.verificar_csv_sincronizado()` sin escribir nada; no hizo falta `--tomar-csv`.

## P3 T4 (continuación) — `estado_flujo` y `_DECISIONES.json` conectados

Sigue a la sección anterior: conecta los dos escritores que quedaron pendientes ahí.

- `flujo.py:escribir_estado()` ya no reescribe `_ESTADO_FLUJO.csv` con `csv.DictWriter` directo:
  ahora llama `db/escribir.verificar_csv_sincronizado()` + `db/escribir.reemplazar(con,
  "estado_flujo", filas, prod_dir=..., bkdir=...)` con import LOCAL (mismo motivo que el import
  local de `registrar_evento` en la misma función — evita un ciclo a nivel de módulo y mantiene
  el camino de SOLO LECTURA de `flujo.py` libre de `psycopg`, porque esta rama solo corre bajo
  `--escribir`). `TENANT_ID` (constante de módulo, junto a `CAMPOS_ESTADO`) es el único punto de
  override para pruebas aisladas; el backup del mirror usa `env.base` (nunca el `backups_csv`
  real) para que un fixture jamás lo toque. `tables.TABLAS_MIGRADAS_DB` suma `"estado_flujo"`.
- `decidir.py --escribir` ya no escribe `_DECISIONES.json` con `json.dump` directo: llama
  `db/escribir.verificar_decision_sincronizada()` + `db/escribir.reemplazar_decision(con, res,
  prod_dir=..., tenant_id=...)`, import LOCAL dentro de `main()` — `_DECISIONES.json` no tiene
  fila en `tables.TABLE_SPECS` (es un blob de una sola fila, no un espejo columna por columna),
  así que nunca puede entrar a `TABLAS_MIGRADAS_DB`/`TABLAS_VERDAD_DB` de la forma genérica; su
  propio guardia de drift (`verificar_decision_sincronizada()`) vive aparte, y
  `db/cargar.py --tomar-csv _DECISIONES.json` (o `decisiones_json`) es su recuperación
  deliberada — caso especial en `tomar_csv()`, documentado en su docstring.
  El import es LOCAL a `main()`, nunca al tope del módulo, por la misma razón que T3/T4
  documentan en varios lugares de este archivo: el gate de paridad (`db/test_db.py`) corre
  `decidir.py` en un SUBPROCESO con scipy+duckdb que no tiene `psycopg`, y ese subproceso nunca
  pasa por `--escribir` — un import a nivel de módulo rompería esa separación.
- Aislamiento de pruebas: `Ads/_TOOLS/test_cli_solo_lectura.py` fuerza `PGDATABASE=vitalcom_test`
  y aísla cada escenario de escritura (`test_flujo_todo_con_escribir_si_escribe`,
  `test_decidir_con_escribir_si_escribe`) en su propio tenant único, bootstrapeando primero
  `raw.estado_flujo`/`raw.decisiones_json` (equivalente a `--tomar-csv`) para que el guardia de
  drift no aborte en la primera escritura de la prueba — mismo patrón que
  `test_registrar_evento.py` (T4, primera pasada).

## P3 T4 (continuación parte 2) — `producto` conectado (`alta_producto.py`/`editar_producto.py`)

Cierra la familia `_DIM_PRODUCTOS.csv`: la VERDAD pasa a `raw.producto`/`core.producto`, el CSV es
el espejo. `_DIM_ENVASE.csv` sigue en disco (regla "editado a mano" de T1) y las carpetas/TXT del
paquete también — solo la fila de `_DIM_PRODUCTOS.csv` cambia de almacén.

- `tables.py`: `"producto"` se suma a `TABLAS_MIGRADAS_DB` (ya estaba en `TABLAS_VERDAD_DB` desde
  T2). `--tomar-csv _DIM_PRODUCTOS.csv` funciona sin cambios (genérico vía `_resolver_tabla_migrada`).
- `editar_producto.py` (usado por `cambiar_costo.py`/`cargar_cuenta.py`/`cargar_page_id.py`, los
  tres escritores que completan una fila YA existente): `aplicar_escrituras()` divide el batch
  `{ruta: bytes}` en DOS ALMACENES, sin adivinar por nombre de archivo — `base` (la misma raíz que
  recibió `planear()`) determina la ÚNICA ruta que va a Postgres
  (`ruta_productos_csv(base)`); el resto (TXT del paquete) sigue el `.tmp` + `os.replace()` de
  siempre. ORDEN: (1) valida (ya lo hizo `planear()`); (2) stagea TODOS los archivos que NO son la
  base a `.tmp` — nada real cambia todavía; (3) `db/escribir.verificar_csv_sincronizado()` +
  `db/escribir.reemplazar()` (commit) y regenera el espejo `_DIM_PRODUCTOS.csv`; (4) recién ahí
  `os.replace()` de los `.tmp` restantes. Una falla ANTES del paso 3 no toca Postgres y descarta
  los `.tmp` (nada cambia, como antes). Una falla EN el paso 4 (Postgres YA comiteó) no se
  deshace — sale con `Rechazo` y un mensaje en español que nombra exactamente qué `.tmp` quedó
  pendiente de reemplazar a mano; nunca se pierde el commit ya hecho.
- `alta_producto.py:aplicar()` (fila NUEVA): mismo orden de tres fases — (1) crea carpetas y
  stagea packshot/`2_DATA_PRODUCTO.txt`/`_DIM_ENVASE.csv` a `.tmp`; (2) `_escribir_producto_alta()`
  agrega la fila nueva a las que ya leyó `planear()` y reemplaza `raw.producto` entero (mismo
  contrato que el `escribir_csv()` que reemplazaba antes); (3) `os.replace()` de los tres `.tmp`.
  Una falla en (1)/(2) deshace carpetas/`.tmp` (nada se crea, como antes). Una falla en (3) es
  RECUPERABLE, no un rollback: el producto ya existe en `raw.producto`, y el mensaje nombra los
  archivos `.tmp` pendientes.
- `TENANT_ID` (constante de módulo en `alta_producto.py` y `editar_producto.py`, mismo patrón que
  T3/T4): se referencia por NOMBRE dentro de las funciones (nunca como default de parámetro) para
  que un monkeypatch de módulo surta efecto en la próxima llamada — igual que
  `flujo.py`/`decidir.py`/`registrar_evento.py`.
- Aislamiento de pruebas: `test_alta_producto.py`, `test_cambiar_costo.py`, `test_cargar_cuenta.py`
  y `test_cargar_page_id.py` fuerzan `PGDATABASE=vitalcom_test`, bootstrapean `raw.producto`/
  `raw.raw_import` en un tenant único por archivo de prueba (mismo patrón que
  `test_registrar_evento.py`) y se saltan limpio con aviso si `vitalcom_test` no está disponible.
  Las inyecciones de falla "antes de Postgres" usan una carpeta en el lugar del `.tmp` esperado (en
  vez de parchear `os.replace`, que es el MISMO objeto módulo `os` que usa `db/escribir.py`
  internamente — parchearlo sin filtrar reventaría también el mirror interno); las de "después de
  Postgres" parchean `os.replace` filtrando por el sufijo `.tmp` propio de `editar_producto.py`/
  `alta_producto.py` (nunca el `.tmp-escribir` interno de `db/escribir.py`, que corre ANTES, dentro
  del commit).
- Confirmado (25-sep-2026): el intérprete que la app usa para lanzar `alta_producto.py`
  (`config.python_del_sistema()` → `VITALCOM_PYTHON` o, por defecto, el `python` del PATH — nunca
  el venv de la app) tiene `psycopg` instalado en este entorno (mismo intérprete que ya usan
  `flujo.py`/`decidir.py --escribir` desde T3/T4).

## Lectura desde Postgres (T5)

Hasta T4 los seis escritores reales quedaron conectados a Postgres, pero los dos LECTORES reales
del sistema (`Ads/_TOOLS/decidir.py` y el backend de la app, `app/backend/vitalcom_app/
contratos.py`) seguían leyendo el ESPEJO CSV directo del disco. T5 los conecta a la base — sin
tocar las dimensiones editadas a mano (`_DIM_CONJUNTOS`, `_DIM_BANDAS`, `_ALIAS_CONJUNTOS`,
`_PARAMETROS_DECISION`, `_DIM_CREATIVOS`...), que siguen viniendo del CSV real, tal como hoy.

- **`db/leer.py`** (nuevo): API pública de lectura, reusando lo que ya existía en
  `db/escribir.py` — nunca una segunda implementación del mapeo columna-por-columna.
  `filas(conn, tabla, tenant_id)` es una fachada de `escribir._filas_espejo()` (lo mismo que ya usa
  el guardia de drift); `decision(conn, tenant_id)` delega en `escribir.leer_decision_actual()`;
  `materializar(conn, tablas, out_dir, tenant_id)` escribe el espejo CSV de cada tabla a un
  directorio (para un lector que necesita un ARCHIVO real, como `decidir.py` vía DuckDB
  `read_csv`), byte-idéntico a `escribir._escribir_csv_atomico()`.
- **`Ads/_TOOLS/decidir.py`**: `VITALCOM_FUENTE=db` (default) | `csv` decide de dónde lee las 5
  tablas DB-truth que ya escribe Postgres (`producto`, `estado_flujo`, `venta`,
  `entrega_conjunto_dia`, `entrega_anuncio_dia`). En modo "db",
  `_activar_fuente_db_si_corresponde()` corre UNA vez por proceso, al principio de
  `analizar_portafolio()`: materializa esas 5 tablas a un directorio temporal (`db.leer.
  materializar()`) y rebinda SOLO esas 5 rutas de módulo (`DIM_PROD_PATH`, `ESTADO_FLUJO_PATH`,
  `FACT_VENTAS_PATH`, `FACT_ENTREGA_PATH`, `FACT_ENTREGA_ANUNCIO_PATH`) — `PARAMS_PATH`,
  `DIM_CONJ_PATH`, `DIM_BANDAS_PATH` y `ALIAS_PATH` no se tocan, siguen leyendo `PROD` (el CSV
  real). Se salta la activación (queda en CSV) si `DECIDIR_PROD_DIR` ya redirigió `PROD` a mano, o
  si `flujo.py:Entorno.motor()` ya lo hizo sobre un fixture (comparación exacta contra la ruta real
  `BASE/PRODUCTOS`) — así `flujo.py` corriendo sobre `test_flujo.py` sigue en CSV sin ningún cambio
  en `flujo.py`. Postgres inalcanzable en modo "db" NUNCA cae de vuelta a CSV en silencio: revienta
  con `SystemExit` y un mensaje claro (mismo criterio que `--escribir`). `DECIDIR_TENANT_ID`
  (nuevo, mismo patrón que `DECIDIR_PROD_DIR`) sobreescribe el tenant que lee el modo "db" —
  necesario para el gate de paridad, que corre `decidir.py` en un SUBPROCESO aparte donde
  monkey-parchear `decidir.TENANT_ID` en proceso no alcanza.
- **Backend (`contratos.py`)**: `VITALCOM_FUENTE=db` (default) | `csv`, mismo contrato.
  `TABLA_DB_POR_ARCHIVO` mapea los cuatro CSV con tabla DB-truth que la app lee
  (`_DIM_PRODUCTOS.csv`, `_ESTADO_FLUJO.csv`, `_FACT_VENTAS.csv`, `_EVENTOS.csv`) — `_leer_csv()`
  y `_leer_json()` (para `_DECISIONES.json`) los desvían a `db/leer.py` cuando corresponde; el
  resto de `PRODUCTOS/*.csv` sigue por el camino de siempre. `VITALCOM_DB_TENANT` (nuevo) sobre-
  escribe el tenant fijo `"vitalcom"` — solo para pruebas aisladas contra `vitalcom_test`, nunca
  en producción. Postgres inalcanzable en modo "db" se dice como `ContratoAusente`, que ya mapea a
  HTTP 503 (`main.py:_contrato_ausente`) — nunca un CSV leído en silencio.
  `app/backend/tests/conftest.py` fuerza `VITALCOM_FUENTE=csv` para toda la sesión de pruebas (los
  sistemas de juguete son fixtures CSV sin Postgres detrás); `test_lectura_desde_postgres.py` es la
  única que ejercita el modo "db", con un tenant único bootstrapeado en `vitalcom_test`.
- Verificado con datos reales (25-sep-2026): `python Ads/_TOOLS/decidir.py --json` con
  `VITALCOM_FUENTE=db` (leyendo Postgres real) y con `VITALCOM_FUENTE=csv` (leyendo
  `PRODUCTOS/*.csv` real) dan el MISMO resultado byte a byte (salvo `generado`) — la garantía de
  que el espejo es fiel también se sostiene en el camino de lectura, no solo en el de escritura.

## Qué NO hace esto todavía (fuera de alcance de P1)

- (Vigente hasta P3 T5) Ningún lector real leía de Postgres, solo escritores: `decidir.py` y el
  backend de la app ya leen Postgres por defecto desde T5 (ver "Lectura desde Postgres" arriba);
  `flujo.py`, `gen_*.py` y el resto siguen leyendo los CSV directo.
- No hay Row-Level Security ni más de un tenant: `tenant_id='vitalcom'` es un valor fijo, no una
  política.
- No hay `UPDATE`/`upsert` incremental: cada carga es un reemplazo completo (`raw` y `core`). Para
  un dataset de este tamaño (~7700 filas en `raw`) es más simple y más fácil de auditar que un
  upsert parcial; se puede revisar si P3 necesita cargas incrementales de verdad.
- `parametro_decision`/`parametro_finanzas.version` NO es un historial temporal real (ver arriba).
- `conjunto_nombre_hist.valid_to` siempre `NULL` (ver arriba): no reemplaza una consulta "¿qué
  nombre tenía este conjunto en tal fecha?", solo la resolución "¿cuál es su nombre canónico hoy?"
  que ya hacía `alias.py`.
