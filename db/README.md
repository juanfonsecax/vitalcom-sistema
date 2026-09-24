# db/ — Postgres local para VITALCOM (P1-cimientos T5/T6)

Espejo de `PRODUCTOS/*.csv` en Postgres, schema `core`. **Los CSV siguen siendo la fuente de
verdad durante P1** (CLAUDE.md, invariantes 10/11): esto no cambia ningún lector ni escritor real
todavía (eso es P3). Lo que entrega P1 es la base + el loader + el exportador + la prueba de que
ir y volver no cambia nada de lo que `decidir.py` decide.

## Cómo correr

Requiere Postgres 18 local (rol/db `vitalcom`, credenciales en
`~/.config/vitalcom_db/.env`: `PGHOST/PGPORT/PGDATABASE/PGUSER/PGPASSWORD`) y el intérprete del
venv de `SISTEMA-app` (ya tiene `psycopg`; no instala nada nuevo):

```
# 1. Aplicar el esquema (idempotente: CREATE TABLE/SCHEMA IF NOT EXISTS)
"C:\Program Files\PostgreSQL\18\bin\psql.exe" -f db/schema.sql

# 2. Cargar PRODUCTOS/*.csv -> Postgres
"..\SISTEMA-app\app\backend\.venv\Scripts\python.exe" db/cargar.py

# 3. Exportar Postgres -> CSV (reconstruye el layout de PRODUCTOS/)
"..\SISTEMA-app\app\backend\.venv\Scripts\python.exe" db/exportar.py --out C:\ruta\salida

# 4. Pruebas (puras + integración; la de integración se salta sola sin Postgres)
"..\SISTEMA-app\app\backend\.venv\Scripts\python.exe" -m pytest db/test_db.py -q
```

`cargar.py` es **idempotente por TRUNCATE + reinserción, en una sola transacción por corrida**:
si algo falla a mitad, `ROLLBACK` completo — nunca queda una tabla a medio cargar. Dos corridas
seguidas sobre los mismos CSV dejan el mismo conteo de filas y el mismo contenido (probado en
`test_db.py::test_cargar_es_idempotente_en_conteo_de_filas`).

## Qué hay en cada tabla

Regla general (ver `db/tables.py`, fuente única de la lista): **cada tabla es un espejo verbatim
de su CSV** — mismas columnas, mismo orden, texto tal cual (sin cast), más `tenant_id` (single
tenant `'vitalcom'`; RLS no habilitado en P1) y un `id BIGSERIAL`. Por qué texto y no tipado: el
único lector real de estos datos (`Ads/_TOOLS/decidir.py`, vía `gasto.py`/`alias.py`) hace su
propio `try_cast` sobre el CSV al leerlo — tipar en Postgres sería una segunda fuente de verdad
para el mismo número, y el requisito duro de P1 es que el viaje ida-vuelta no cambie ni un solo
carácter de lo que ese lector ve.

Tablas con una regla propia (no son un espejo plano):

- **`venta`** (`_FACT_VENTAS.csv`) — agrega dos columnas que NO existen en el CSV:
  `ad_id_resuelto` y `metodo_atribucion` (`ad_id` | `ad_id_verificado_gasto` | `nombre` |
  `sin_atribuir`), calculadas por `cargar.enriquecer_venta()` cruzando cada fila con
  `PRODUCTOS/_MAPA_AD_ID_HIST.csv` (T2). La columna `ad_id` original queda **intacta y verbatim**
  — nunca se pisa (invariante: "no overwrite a valid original ad_id") — y es la que
  `exportar.py` vuelve a escribir en el CSV reconstruido. `ad_id_resuelto`/`metodo_atribucion`
  son un enriquecimiento de la base, no parte de `_FACT_VENTAS.csv`, así que `exportar.py` las
  omite del archivo exportado.

  Detalle no obvio: la llave natural del mapa (`ventana_ini, cuenta_alias, conjunto, anuncio`)
  **no es única** en `_MAPA_AD_ID_HIST.csv` — 150 grupos la repiten, porque varias ventas BASE
  distintas caen en la misma ventana+conjunto+anuncio. `mapear_ad_id_hist.py` escribe una fila
  del mapa por cada venta sin `ad_id` válido (mismo conteo, 1394) y las ordena con un **sort
  estable** por esa llave, así que dentro de cada grupo repetido el orden relativo coincide con
  el de las ventas que las originaron. Por eso `enriquecer_venta()` hace un join **llave + cola
  FIFO**, no un `dict` simple: un `dict` de última-fila-gana pierde 1 de 1394 correspondencias
  cuando la llave se repite (se comprobó: da 671/723 en vez de los 670/724 reales de T2).

- **`decision`** — no viene de un CSV. Una fila por carga con el `payload` completo de
  `PRODUCTOS/_DECISIONES.json` en `JSONB` (`fecha` = su campo `generado`). `exportar.py` puede
  reconstruir `_DECISIONES.json` a partir de ella, aunque el gate de paridad (T6) no lo necesita:
  corre `decidir.py` de cero sobre la base exportada en vez de leer este snapshot.

- **`raw_import`** — auditoría de carga: un renglón por archivo por corrida
  (`archivo, sha256, filas, loaded_at`). Permite responder "¿con qué versión exacta del CSV se
  cargó esto?" sin abrir el CSV.

- **`aprendizajes`** — `_APRENDIZAJES.csv` trae su propia columna `id` (el id del aprendizaje,
  no el `id` bigserial de Postgres). Se renombra a `id_csv` en SQL
  (`db/tables.py:COLUMN_RENAMES`); `exportar.py` la vuelve a escribir como `id` en el CSV.

- **`core.angulo`** — **VISTA**, no tabla. Sus columnas (`angulo_key`, `avatar`, `dolor_nucleo`,
  `emocion_dominante`, `avatar_edad`, `avatar_genero`, `nivel_conciencia`, más `deseo` siempre
  `NULL` — no hay columna fuente para ese dato todavía) ya viven 1:1 en `conjunto`
  (`_DIM_CONJUNTOS.csv` trae esas columnas por fila). No se creó como tabla física en P1 porque
  ningún lector real la necesita separada todavía (eso es P3, fuera de alcance); duplicarla sin
  uso habría sido una segunda fuente del mismo dato. `cargar.py`/`exportar.py` no la tocan
  (una vista no se carga ni se exporta).

### Fuera de alcance en P1 (con evidencia, no por omisión)

- **`catalogo_concepto`**: su dueño real es `Ads/_SWIPE/_CATALOGO_CONCEPTOS.md` — prosa, no CSV.
  No hay una fila-por-concepto que copiar sin inventar una estructura que el `.md` no declara.
  Queda fuera de P1; si un futuro consumidor necesita esta tabla, su carga sale de parsear ese
  `.md` explícitamente, no de este loader genérico CSV→tabla.
- **`_VOZ_CLIENTE.csv`** (`voz_cliente`): el archivo hoy no existe en este repo (su dueño,
  `Ads/_TOOLS/verificar_voz.py`, todavía no tiene filas verificadas). La tabla existe en
  `schema.sql` con el esquema documentado en el docstring de ese script; `cargar.py` la deja
  vacía (0 filas) en vez de fallar, `exportar.py` no escribe el archivo si no hay columnas que
  reconstruir.

## El gate de paridad (T6)

`test_db.py::test_parity_gate_decidir_exportado_igual_a_real`:

1. Carga (`cargar_todo()`).
2. Exporta a un directorio temporal (`exportar_todo(tmp)`).
3. Corre `Ads/_TOOLS/decidir.py --json` **dos veces, en un subproceso aparte**: una vez sin
   variables de entorno (lee `PRODUCTOS/` real) y otra con `DECIDIR_PROD_DIR=<tmp>` (lee la base
   exportada).
4. Compara ambos JSON, ignorando solo la clave `generado` (fecha de hoy — igual en las dos
   corridas de todos modos). Cualquier otra diferencia es `FAIL`, no se enmascara.

**Por qué subproceso y no import directo:** `decidir.py` importa `scipy` y `duckdb`, que no
viven en el venv de `psycopg` (y no está autorizado instalar nada). El intérprete `python` del
PATH sí trae `scipy`+`duckdb` (confirmado: 3.14, scipy 1.18, duckdb 1.5) pero no `psycopg`. El
gate corre `cargar.py`/`exportar.py` con el venv de `psycopg` y `decidir.py` con ese otro
intérprete, comunicados por archivos (la base exportada) y variables de entorno — nunca por un
`import` en el mismo proceso.

**`DECIDIR_PROD_DIR`** es el único cambio en `Ads/_TOOLS/decidir.py` para este gate: un override
de módulo, mínimo y retro-compatible (sin la variable, comportamiento idéntico al de siempre —
ver `test_decidir_prod_dir_override_es_retrocompatible`). `flujo.py` ya monkey-parcha las mismas
constantes de módulo desde un proceso vivo para correr el motor sobre un fixture
(`Entorno.motor()`); esta variable es el equivalente para cuando no hay un proceso Python vivo
que monkey-parchear porque hay que cruzar de intérprete.

## Qué NO hace esto todavía (fuera de alcance de P1)

- Ningún lector ni escritor real (decidir.py, flujo.py, gen_*.py, etc.) lee de Postgres: siguen
  leyendo los CSV. Cambiar eso es P3.
- No hay Row-Level Security ni más de un tenant: `tenant_id='vitalcom'` es un valor fijo, no una
  política.
- No hay `UPDATE`/`upsert` incremental: cada carga es un reemplazo completo. Para un dataset de
  este tamaño (~7700 filas totales) es más simple y más fácil de auditar que un upsert parcial;
  se puede revisar si P3 necesita cargas incrementales de verdad.
