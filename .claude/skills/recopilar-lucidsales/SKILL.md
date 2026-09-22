---
name: recopilar-lucidsales
description: RECOLECCIÓN de la data de LucidSales. Baja el export por API (sin navegador ni descarga manual), lo ingiere a _FACT_VENTAS.csv y deja el sistema listo para la auditoría. Úsala en la corrida nocturna, cuando el operador dice "bajá la data", "traé las métricas de ayer", "cargá LucidSales", "el export de anoche", cuando falta un día en el CSV, o antes de ciclo-diario si la ventana está desactualizada.
tools: Read, Bash, Glob, Grep
---

# RECOPILAR LUCIDSALES — la data entra sola

**Dueña de la RECOLECCIÓN, nada más.** El mapeo de columnas, la conversión de moneda, la
anti-duplicación y la escritura del CSV tienen dueño desde antes: `ingerir_lucidsales.py`. Acá no se
repite ni una de esas reglas.

```
bajar_lucidsales.py  →  report-<ini>-<fin>.json  →  ingerir_lucidsales.py  →  _FACT_VENTAS.csv
   (API, sin navegador)      (crudo, auditable)         (dueño del mapeo)        (hook regenera app)
```

---

## LA CORRIDA NOCTURNA (lo normal)

```bash
python Ads/_TOOLS/bajar_lucidsales.py && python Ads/_TOOLS/ingerir_lucidsales.py --dir Ads/_INGESTA/LUCIDSALES
```

Sin argumentos, `bajar_lucidsales.py` trae **AYER cerrado** — la cadencia que manda
`DOCTRINA/DATA_PLAYBOOK.md` (export de 1 solo día, todas las noches).

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

Sin argumentos trae **AYER**, todas las cuentas `estado_cuenta=ACTIVE` y `tiene_metodo_pago=SI` de
`_DIM_CUENTAS.csv` (no filtra por `mcp_habilitado`: ese campo es del conector interactivo, no de esta
lectura por Graph API). Anexa a `_FACT_ENTREGA.csv` y `_FACT_ENTREGA_ANUNCIO.csv` con
`fuente=MetaAPI-directo`, con la misma anti-duplicación y backup que `ingerir_lucidsales.py`.

Al final imprime un resumen por cuenta y, si alguna falló (permiso denegado, red caída), una línea
`CUENTAS CON ERROR (...)` en stderr con el alias de cada una. **Una cuenta caída no es fatal**: las
demás igual se escriben.

**Código de salida (T1b, 22-sep-2026):** `0` todas las cuentas OK · `2` PARCIAL (al menos una OK y
al menos una falló; las filas de las que sí respondieron ya quedaron escritas) · `1` todas las
cuentas fallaron, o error fatal. La cadena nocturna (`app/backend/vitalcom_app/workflows.py`, paso
`ciclo.bajar_meta`) trata `2` como **aviso**: sigue con el resto de la cadena; `1` sí la detiene.
Ante un `2`, revisar la cuenta a mano — no re-correr todo a ciegas.

---

## QUÉ LEER EN LA SALIDA — y cuándo NO ingerir

`bajar_lucidsales.py` imprime `filas · ventas · Q · $ · msj` de la ventana. **Miralo antes de
ingerir**, porque el ingestor anexa sin discutir:

| Señal | Qué significa | Qué hacer |
|---|---|---|
| `CERO filas` | fecha equivocada, o el día no cerró | **NO ingerir.** Revisar la fecha. |
| ventas muy debajo de lo normal | posible ventana a medio cerrar | Confirmar contra el panel antes de anexar. |
| `Ya existe report-…` | ese día ya se bajó | No re-bajar. Si de verdad hay que rehacerlo: `--forzar`. |
| `⚠ N conjuntos SIN dimensión` | hay conjuntos nuevos en Meta | Darlos de alta en `_DIM_CONJUNTOS.csv`, o el JOIN queda cojo. |
| `duplicados omitidos` alto | el día ya estaba cargado | Normal y sano: la anti-duplicación hizo su trabajo. |

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
> a la consola, a un archivo ni a un chat.** (Detectado el 07-sep-2026; conviene rotar esas keys.)

---

## EL CONTRATO DE LA API — medido, no supuesto

Verificado en vivo contra `panel.lucidsales.co` el **07-sep-2026**. Vive en el docstring de
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

## DESPUÉS DE INGERIR

El hook `PostToolUse` valida el CSV y regenera la app solo — cubre por barrido de `mtime` lo que
escriben los scripts. No hay que acordarse de nada.

Con la data fresca, sigue **`ciclo-diario`**. Y vale su propia regla: `decidir.py` cuenta desde el
**último día CON DATA**. Si la recolección se saltó días, las órdenes salen fechadas hoy sobre data
vieja — el error de ventana del 06-sep-2026 disfrazado de frescura. **Recolectar antes de decidir.**
