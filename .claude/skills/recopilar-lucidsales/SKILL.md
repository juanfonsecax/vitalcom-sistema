---
name: recopilar-lucidsales
description: RECOLECCIÓN de la data de LucidSales. Baja el export por API (sin navegador ni descarga manual), lo ingiere a _FACT_VENTAS.csv y deja el sistema listo para la auditoría. Úsala en la corrida nocturna, cuando el operador dice "bajá la data", "traé las métricas de ayer", "cargá LucidSales", "el export de anoche", cuando falta un día en el CSV, o antes de ciclo-diario si la ventana está desactualizada.
tools: Read, Bash, Glob, Grep
---

# RECOPILAR LUCIDSALES — la data entra sola

**Dueña de la RECOLECCIÓN, nada más.** El mapeo de columnas, la conversión de moneda, la
identidad anti-duplicado y la escritura del CSV tienen dueño desde antes: `ingerir_lucidsales.py`
(el UPSERT en sí vive en `Ads/_TOOLS/upsert_fact.py`, compartido con `bajar_meta_insights.py`). Acá
no se repite ni una de esas reglas.

> **Ventana de liquidación.** El gasto/ventas de LucidSales a
> veces llegan CONGELADOS a medio día (medido en varios días recientes: 0.65-0.75 del gasto real
> de Meta). Por eso `bajar_lucidsales.py` **sin argumentos** ya no trae solo AYER: pide
> `upsert_fact.SETTLEMENT_WINDOW_DIAS` (hoy 3) días **sueltos** terminando ayer, con `--forzar`
> implícito, y `ingerir_lucidsales.py` los carga con **UPSERT** (reemplaza por llave natural en vez
> de anexar) — un día que se corrige en el panel se corrige también acá la noche siguiente. Sigue
> siendo UN pedido por día: la API de LucidSales agrega por rango, así que un tramo multi-día
> (`--dias N`, el control semanal) nunca puede sustituir a N pedidos sueltos. `--fecha`/`--desde`/
> `--hasta` puntuales no activan la ventana de liquidación: siguen trayendo exactamente lo pedido.

```
bajar_lucidsales.py  →  report-<ini>-<fin>.json  →  ingerir_lucidsales.py  →  _FACT_VENTAS.csv
   (API, sin navegador)      (crudo, auditable)         (dueño del mapeo)        (hook regenera app)
```

---

> **La cadena nocturna corre sola (P3 T6):** `Ads/_TOOLS/ciclo_diario.py`, disparado por Task
> Scheduler, ya encadena `bajar_lucidsales.py` → `ingerir_lucidsales.py` → (lunes) el control
> semanal → `bajar_meta_insights.py`. Lo de abajo sigue funcionando igual para una corrida manual
> (un hueco, un `--fecha` puntual, o depurar algo a mano).

> **El botón "Traer las ventas de LucidSales" de la app (T4, 26-sep-2026) ya NO corre esta skill:**
> corre `Ads/_TOOLS/recopilar_lucidsales.py` (`ejecutor_tipo: script`, gratis y determinístico —
> antes gastaba una sesión de Claude para dos comandos que no necesitaban ningún juicio). Esta
> skill sigue viva para el uso manual por CLI de abajo (un hueco, un `--fecha` puntual, depurar).

## LA CORRIDA NOCTURNA (lo normal, o a mano)

```bash
python Ads/_TOOLS/bajar_lucidsales.py && python Ads/_TOOLS/ingerir_lucidsales.py --dir Ads/_INGESTA/LUCIDSALES
```

Sin argumentos, `bajar_lucidsales.py` re-consulta la **ventana de liquidación** (ver arriba,
D-1..D-N sueltos, hoy N=3) y `ingerir_lucidsales.py --dir ...` reemplaza por llave los días que
hayan cambiado — la cadencia que manda `DOCTRINA/DATA_PLAYBOOK.md` (export diario, ahora con
re-pull nocturno de los últimos días para corregir un gasto congelado a medio día).

**Los lunes, además, el control semanal:**

```bash
python Ads/_TOOLS/bajar_lucidsales.py --dias 7 && python Ads/_TOOLS/ingerir_lucidsales.py --dir Ads/_INGESTA/LUCIDSALES --rol CONTROL
```

> ⚠️ El semanal va **siempre con `--rol CONTROL`**. Es verificación cruzada de la maduración COD
> (~3 días), **no se suma** con las diarias: cargarlo como `BASE` duplica la semana entera.

**Después de LucidSales, la ENTREGA de Meta** (impresiones, clics, gasto — la venta sigue siendo
`_FACT_VENTAS.csv`, esto es solo la señal de entrega que usa `etapa-7`):

```bash
python Ads/_TOOLS/bajar_meta_insights.py
```

Sin argumentos re-consulta la misma **ventana de liquidación** (D-1..D-N, hoy N=3) para todas las
cuentas `estado_cuenta=ACTIVE` y `tiene_metodo_pago=SI` de `_DIM_CUENTAS.csv` (no filtra por
`mcp_habilitado`: ese campo es del conector interactivo, no de esta lectura por Graph API). Pide
`ad_id` y `actions` a la Graph API: `ad_id` va en `_FACT_ENTREGA_ANUNCIO.csv`
para el JOIN por id con `_FACT_VENTAS.csv`, y `mensajes` sale de la conversación de mensajería real
(`onsite_conversion.messaging_conversation_started_7d`) — ya no se estima con clics. Hace **UPSERT**
sobre `_FACT_ENTREGA.csv` y `_FACT_ENTREGA_ANUNCIO.csv` (reemplaza por llave, no anexa), con backup
previo, igual que `ingerir_lucidsales.py`. `--fecha`/`--desde`/`--hasta` puntuales siguen trayendo
exactamente lo pedido, sin activar la ventana de liquidación.

Al final imprime un resumen por cuenta y, si alguna falló (permiso denegado, red caída), una línea
`CUENTAS CON ERROR (...)` en stderr con el alias de cada una. **Una cuenta caída no es fatal**: las
demás igual se escriben.

**Código de salida:** `0` todas las cuentas OK · `2` PARCIAL (al menos una OK y
al menos una falló; las filas de las que sí respondieron ya quedaron escritas) · `1` todas las
cuentas fallaron, o error fatal. La cadena nocturna (`app/backend/vitalcom_app/workflows.py`, paso
`ciclo.bajar_meta`) trata `2` como **aviso**: sigue con el resto de la cadena; `1` sí la detiene.
Ante un `2`, revisar la cuenta a mano — no re-correr todo a ciegas.

**Orden de despliegue:** `stg_entrega_anuncio.sql` exige la
columna `ad_id` de `_FACT_ENTREGA_ANUNCIO.csv`. Tras un cambio de esquema, correr este re-pull de
Meta (que migra el header vía `upsert_fact`) ANTES de cualquier `dbt build` manual — la cadena
nocturna (`datos` → `bajar_meta` → `motor`) ya respeta este orden. Ver `DOCTRINA/DATA_PLAYBOOK.md`.

---

## QUÉ LEER EN LA SALIDA — y cuándo NO ingerir

`bajar_lucidsales.py` imprime `filas · ventas · Q · $ · msj` de la ventana. **Miralo antes de
ingerir**, porque el ingestor hace UPSERT sin discutir (una llave que ya existía se REEMPLAZA):

| Señal | Qué significa | Qué hacer |
|---|---|---|
| `CERO filas` | fecha equivocada, o el día no cerró | **NO ingerir.** Revisar la fecha. |
| ventas muy debajo de lo normal | posible ventana a medio cerrar | Confirmar contra el panel antes de cargar. |
| `Ya existe report-…` | ese día ya se bajó (solo aplica a un pedido puntual: la ventana de liquidación siempre se re-baja con `--forzar`) | No re-bajar a mano. Si de verdad hay que rehacerlo: `--forzar`. |
| `⚠ N conjuntos SIN dimensión` | hay conjuntos nuevos en Meta | Darlos de alta en `_DIM_CONJUNTOS.csv`, o el JOIN queda cojo. |
| `N reemplazadas (día corregido)` | el UPSERT encontró la llave y la corrigió | Normal y sano dentro de la ventana de liquidación: así se arregla un día congelado. |
| `duplicados dentro de la misma corrida` alto | dos archivos de esta misma invocación traían la misma llave | Revisar que no se haya pasado el mismo export dos veces por error. |

Ante la duda, `--dry-run` en el ingestor: dice exactamente qué anexaría sin tocar el CSV.

---

## HUECOS: rellenar días que faltan

```bash
python Ads/_TOOLS/bajar_lucidsales.py --fecha 2026-09-03          # un día suelto
python Ads/_TOOLS/bajar_lucidsales.py --fecha 2026-09-01 --hasta 2026-09-05   # un tramo
```

> Un tramo se carga como **una sola fila por anuncio con `dias=5`**, no como cinco días. Para
> reconstruir día por día, hay que bajarlos de a uno — es la única forma de tener serie diaria.

---

## LAS CREDENCIALES — dónde viven y por qué ahí

`~/.config/lucidsales/.env`, **fuera del repo**, permisos `600`:

```
LUCIDSALES_EMAIL=...
LUCIDSALES_PASSWORD=...
LUCIDSALES_TIENDA=PRIMAX GT
```

> **`LUCIDSALES_TIENDA` no es opcional acá.** El usuario tiene DOS tiendas —`PRIMAX` (3703) y
> `PRIMAX GT` (3744)— y el token que sale de `auth/login` **no trae ninguna activa**: sin
> seleccionarla, `meta/metrics` responde `403 No hay una tienda activa seleccionada`.
> **La de este negocio es `PRIMAX GT`.** Se puede pisar por corrida con `--tienda`.

Las escribe el operador una sola vez. **Nunca en el repo, nunca en git, nunca en la línea de
comandos** (el historial de shell las guardaría), **nunca en el chat** (el transcripto las guardaría).
El script las lee del entorno o de ese archivo, y no imprime jamás el token ni la contraseña.

La cuenta es de **solo métricas**: en `PRIMAX GT` su rol es `4` (métricas) y nada más — verificado
en los claims del token, no asumido.

> ⚠️ **`auth/getshopname` devuelve el `apiKey` y el `botApiKey` de cada tienda EN CLARO**, junto al
> nombre. Es una fuga del lado de LucidSales, no del sistema. `bajar_lucidsales.py` extrae solo `id`
> y `Nombre` y descarta el resto sin imprimirlo ni guardarlo. **Nunca volcar esa respuesta completa
> a la consola, a un archivo ni a un chat.** (Conviene rotar esas keys.)

---

## EL CONTRATO DE LA API — medido, no supuesto

Verificado en vivo contra `panel.lucidsales.co`. Vive en el docstring de
`bajar_lucidsales.py`; el resumen operativo:

| Pieza | Valor |
|---|---|
| base | `https://panel.lucidsales.co/b/` |
| login | `POST auth/login` con `{email, password}` → `{ok, token}`. El front hace `trim().toLowerCase()` al email; el script lo replica |
| **tienda** | `POST auth/addShopId {id}` → **token NUEVO** que reemplaza al de login. **Paso obligatorio**: sin él, `meta/metrics` da 403. Los ids salen del claim `uid.idEmpresa`; los nombres de `auth/getshopname {"id":[3703,3744]}` — **lista de enteros**, con el string `"3703,3744"` el servidor tira 500 |
| auth | header **`x-token: <JWT>`**. `Authorization: Bearer` devuelve **401** — no es Bearer |
| vida del token | **12 h**. Por eso cada corrida hace login; no hay sesión que mantener viva |
| data | `GET meta/metrics/1?startDate=YYYY-MM-DD&endDate=YYYY-MM-DD&search=` → `{ok, insights[], count}` |
| paginación | **decorativa** — `page`, `itemsPerPage` y el `1` de la ruta no cambian la respuesta: el backend devuelve el set completo y el front pagina en el cliente. Por eso no hay riesgo de export parcial |

**El `.xlsx` era un intermediario.** Lo armaba el navegador (chunk `excel-exporter`) volcando
literalmente ese mismo `insights`: mismas 22 columnas, cero transformación del servidor. El JSON es
la fuente; el xlsx era una foto de la fuente.

> **Si algún día el bajador falla con 401 o con `ok=false`,** lo primero a sospechar es que
> LucidSales cambió el contrato. Se re-mide abriendo el panel en el navegador y leyendo la petición
> real de `/metricas` — no se adivina el nuevo formato.

---

## LO QUE ESTA VÍA **NO** TRAE

El JSON de la API trae el **detalle por anuncio**, que es lo que alimenta `_FACT_VENTAS.csv`. El
bloque **`Resumen`** que traía el xlsx **lo agregaba el exportador del navegador**, no el servidor.

Consecuencia práctica: las **filas sintéticas de cuadre** que documenta `DATA_PLAYBOOK.md` §
(la diferencia entre el detalle y el total, porque LucidSales no atribuye toda venta a un anuncio)
**no se derivan solas por esta vía**. Si el P&L de un tramo tiene que cuadrar contra el total real,
ese total se confirma en el panel y las filas de cuadre se cargan como siempre: `conjunto`/`anuncio`
vacíos, `spend_usd` = 0, `ad_id` vacío.

---

## MERCADO CO (MANUAL)

Colombia no corre en la cadena nocturna: su cuenta publicitaria es EXTERNA (no está en
`_DIM_CUENTAS.csv`, sin MCP ni API) y su tienda de LucidSales no es la de `LUCIDSALES_TIENDA`. El
operador entrega dos exports y Claude los ingiere con las mismas herramientas:

```bash
# 1. Entrega de Meta: export de Ads Manager (xlsx, desglosado por anuncio) de la cuenta externa
python Ads/_TOOLS/ingerir_meta.py <informe.xlsx> --producto OVULOS_PURITY --dry-run
python Ads/_TOOLS/ingerir_meta.py <informe.xlsx> --producto OVULOS_PURITY
# 2. Ventas: export de LucidSales de la tienda CO (report-<ini>-<fin>.xlsx|json)
python Ads/_TOOLS/ingerir_lucidsales.py <report-...> --producto OVULOS_PURITY --dry-run
python Ads/_TOOLS/ingerir_lucidsales.py <report-...> --producto OVULOS_PURITY
```

Reglas:
- `--producto PK` asigna todo el export a ese producto; `--mercado CO` en `ingerir_lucidsales.py`
  clasifica por nombre entre los productos de Colombia. Sin ninguno de los dos, un producto de cuenta
  EXTERNA no se clasifica (queda `SIN_CLASIFICAR` y la corrida sale en rojo).
- Divisa del gasto: la columna `Divisa` del export; sin ella, `_DIM_PRODUCTOS.moneda`; sin ninguna de
  las dos el archivo se rechaza. `spend_usd` queda en USD; la fila queda con `cuenta_alias=EXTERNA`.
- `total_q` es el monto de la venta en la moneda de venta del mercado del producto (CO: COP);
  el dueño de esa moneda es `mercado.py`. Nunca se suma entre mercados.
- El nombre del conjunto/anuncio en el export sigue la convención de `ETAPA-6.md`; el conjunto se da de
  alta en `_DIM_CONJUNTOS.csv` como cualquier otro.
- `bajar_lucidsales.py` (tienda GT) y `bajar_meta_insights.py` (cuentas `ACTIVE`) nunca traen ni
  clasifican un producto EXTERNA.

Después, `decidir.py` y `flujo.py` corren como siempre, por producto.

---

## DESPUÉS DE INGERIR

El hook `PostToolUse` valida el CSV y regenera la app solo — cubre por barrido de `mtime` lo que
escriben los scripts. No hay que acordarse de nada.

Con la data fresca, sigue **`ciclo-diario`**. Y vale su propia regla: `decidir.py` cuenta desde el
**último día CON DATA**. Si la recolección se saltó días, las órdenes salen fechadas hoy sobre data
vieja — el error clásico de ventana disfrazado de frescura. **Recolectar antes de decidir.**
