---
name: publicar-meta
description: PUBLICA la estructura de una fase en Meta por el conector MCP, a partir del paquete determinista que emite gen_publicacion.py. Corre el pre-flight, ejecuta las llamadas en orden, vuelca el snapshot de Meta y cierra con el gate que escribe los ad_id en _DIM_CREATIVOS.csv. Úsala cuando el operador dice "publicá la campaña", "subí esto a Meta", "creá la estructura en GTR7", "lanzá la FASE 2" o cuando hay un _PUBLICACION_*.json sin ejecutar. Todo nace PAUSED.
---

# PUBLICAR-META — la publicación deja de depender de la memoria

**Dueña de la EJECUCIÓN, nada más.** Los parámetros, los nombres, la banda de edad y el
presupuesto tienen dueño desde antes: `Ads/_TOOLS/gen_publicacion.py` y los CSV que lee. Acá no se
decide ni un valor. Si esta skill tiene que *elegir* algo, es que el paquete estaba incompleto y el
generador debió haberlo bloqueado.

> **La regla que gobierna todo lo de abajo:** *el CSV no es evidencia del estado de Meta.*
> Antes de crear, **preguntarle a Meta qué existe** — cuesta una llamada. El 08-sep se estuvo a
> punto de duplicar una campaña viva con $23.46 gastados porque el CSV decía "cero publicados".

---

## Los 5 pasos

### 1 · PRE-FLIGHT — preguntarle a Meta, no al CSV

```bash
python Ads/_TOOLS/gen_publicacion.py --producto [PK] --fase [N] --brazo [A|B|C|UNICO] --cuenta [ALIAS]
```

Si el gate de ENTRADA de esa fase (`DOCTRINA/FLUJO.json`, evaluado por `flujo.gate_entrada`) no
está cumplido, `gen_publicacion.py` se niega con exit 1 y nombra el gate: no es un aviso, es un
candado. Si el operador confirma que quiere seguir igual, repetir el mismo comando agregando
`--excepcion "motivo"` — el paquete se genera Y queda una fila `EXCEPCION` en `_EVENTOS.csv`.

Lee el bloque `preflight` del paquete y corré sus llamadas:

1. `ads_get_ad_accounts` → la cuenta tiene `is_ads_mcp_enabled` y `is_queryable`.
2. `ads_get_ad_entities` **level=campaign, adset y ad** sobre esa cuenta → **qué existe YA**.
3. `ads_get_user_pages` → el `page_id` existe y el lanzador lo ve.

Volcá lo del paso 2 a `Ads/_INGESTA/META/snapshot_[ALIAS].json` con esta forma:

```json
{"cuenta_alias":"GTR7","cuenta_id":"598687956219141","tomado_el":"...",
 "ad_entities":[{"id":"...","nivel":"campaign","name":"...","status":"PAUSED"}]}
```

### 2 · REGENERAR el paquete contra ese snapshot

```bash
python Ads/_TOOLS/gen_publicacion.py --producto [PK] --fase [N] --brazo [X] --cuenta [ALIAS] \
       --snapshot Ads/_INGESTA/META/snapshot_[ALIAS].json
```

Las llamadas cuyo objeto ya existe salen con `"omitir": true` y su `id_existente`. **Esa es toda
la idempotencia que el MCP oficial no trae.** Si el generador sale con exit 1, hay bloqueantes:
**parar y pedir el dato que falta con el nombre de su dueño** (invariante 4). No inventarlo.

### 3 · EJECUTAR las llamadas EN ORDEN

Recorré `llamadas[]` de menor a mayor `n`. Por cada una:

- si `omitir` es `true` → **no la llames**; guardá su `id_existente` en la variable de `guardar_como`.
- si no → llamá al `tool` con sus `args` **literales**, sustituyendo cada `{{variable}}` por el id
  que guardaste antes.
- guardá el id devuelto bajo `guardar_como`.
- **leé el campo `nota`**: ahí va la trampa específica de esa llamada, medida en producción.

Tres cosas que no se negocian:

| | |
|---|---|
| **Todo nace PAUSED** | Es el candado nativo del human-in-the-loop. El doble candado es el `start_time` de las 4 AM. |
| **El primer conjunto es el test de la página** | Si `ads_create_ad_set` lo acepta, la página está bien asignada. `ads_get_ad_account_pages` puede tardar en listarla (lag de lectura) y eso **no** es un fallo. |
| **`ads_creative_upload_media` con `LOCAL_FILE` abre un widget** | El operador elige el archivo. Solo funciona donde `_DIM_CUENTAS.csv` dice `sube_media_local=SI`. En el resto, el operador sube a mano y vos leés el hash con `ads_get_ad_images`. **Nunca reusar el nombre de una pieza vieja** — Meta guarda las dos y quedan indistinguibles: el 08-sep se publicaron 10 anuncios con la pieza equivocada exactamente por eso. Sufijo `_V2`, `_V3`. |

Si una llamada falla, **parar ahí**. No seguir con las siguientes: dejan huérfanos. Volvé al paso 1
y regenerá contra un snapshot fresco — se retoma donde quedó, sin duplicar.

### 4 · CERRAR EL GATE — escribir los `ad_id`

Volcá un snapshot nuevo (paso 1.2 otra vez) y corré:

```bash
python Ads/_TOOLS/verificar_publicacion.py --producto [PK] --fase [N] --brazo [X] \
       --snapshot Ads/_INGESTA/META/snapshot_[ALIAS].json --escribir
```

Sale con exit 1 si falta cualquier objeto declarado. **Con exit 1 no se activa nada.**

### 5 · REGISTRAR y avisar

- Evento `LANZAMIENTO` en `PRODUCTOS/_EVENTOS.csv`, con la fecha en que se aplica.
- Decile al operador, textual: **qué quedó PAUSED, a qué hora arranca, y que la activación es de él.**
- Agendá el **control D+1 de tracking** (`MCP_PLAYBOOK` §7.5). Es obligatorio y no lo cubre el gate:
  que el anuncio exista no prueba que trackee.

---

## Lo que esta skill NO hace

- **No activa.** `ads_activate_entity` existe y funciona, pero encender es gastar: lo decide el
  operador. Si alguna vez se automatiza, pasa por `decidir.py` primero (invariante 13).
- **No mueve presupuesto de algo vivo.** Ni arriba ni abajo. Eso es `decidir.py`.
- **No juzga si la campaña debía existir.** Eso lo decidió `etapa-6` y lo validó el generador.
- **No crea conjuntos de cero cuando hay uno que ya trackea.** Regla anti-ceguera del
  `MCP_PLAYBOOK`: si hay un conjunto con `destination_type=WHATSAPP` + `promoted_object` que ya
  trae ventas, se le agregan los anuncios nuevos ahí. La tanda creada de cero el 27-jul quedó
  100% ciega y quemó $166 sin medir nada.
