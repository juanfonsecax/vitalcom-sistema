# MCP_PLAYBOOK — Creación de campañas de testeo vía Meta Ads MCP

**Estado:** VERIFICADO en producción.
**Alcance:** este playbook convierte la salida de ETAPA-6 en una campaña **real creada en Meta, en estado PAUSED**, para cualquier producto.

> 🔧 **ESTE DOCUMENTO YA NO SE EJECUTA A MANO.** Dejar la ejecución en prosa que un modelo tiene
> que leer y recordar entera arriesga que se publique una campaña sin que nadie escriba los
> `ad_id`, y que el sistema crea "cero publicados" mientras Meta ya está gastando.
> Ahora la ejecución tiene herramientas:
>
> | Pieza | Qué hace |
> |---|---|
> | `Ads/_TOOLS/gen_publicacion.py` | Deriva la secuencia EXACTA de llamadas MCP desde los CSV y el `_PLAN.json`. **Bloquea con exit 1 si falta un dato**, con el nombre de su dueño. Emite además el **manifiesto** de lo que debe existir en Meta al terminar. |
> | `Ads/_TOOLS/verificar_publicacion.py` | El gate: compara Meta contra el manifiesto y **escribe los `ad_id` en `_DIM_CREATIVOS.csv`**. Es el paso que, sin este gate, queda sin hacer. |
> | `.claude/skills/publicar-meta/SKILL.md` | El procedimiento de 5 pasos que ejecuta las llamadas. |
> | `PRODUCTOS/_PARAMETROS_PUBLICACION.csv` | Estructura, presupuesto, objetivo y hora **por fase**. Cambiar la doctrina = editar una fila. |
> | `PRODUCTOS/_DIM_CUENTAS.csv` | El inventario de cuentas, machine-readable. |
>
> **Este playbook queda como el POR QUÉ y el catálogo de gotchas.** Los valores que abajo aparecen
> en prosa son ilustrativos: **manda el CSV**. Si los dos discrepan, el CSV tiene razón y esta
> prosa está vieja.

**Qué hace y qué no hace el conector:**

- **Todo lo que crea nace PAUSED.** No hay forma de crear en ACTIVE, y ese es el candado nativo del human-in-the-loop.
- **Sí puede activar.** `ads_activate_entity` existe y funciona. Que active el operador es **política de este sistema, no un límite de la herramienta**.
- **No mueve presupuesto ni estado de algo vivo de forma automática.** Eso sigue en pie, y su dueño es `decidir.py` (invariante 13).
- **No tiene idempotencia ni memoria entre sesiones.** Publicar dos veces duplica. Lo cubre `gen_publicacion.py --snapshot`.

> Regla de oro (Andrómeda): el MCP actúa en dos momentos — PREPARACIÓN (crear en PAUSED) y LECTURA (reporting).

---

## 0. Quién ejecuta esto
Las llamadas MCP las hace **quien tenga el conector Meta Ads conectado** (en Cowork, el orquestador principal). Los subagentes ETAPA-* describen el QUÉ; este playbook es el CÓMO operativo de la parte de creación (ETAPA-6, modo MCP) y de lectura (ETAPA-7).

El perfil conectado al MCP debe ser el **LANZADOR (desechable)**, nunca el contenedor/BM maestro. Todo lo que el MCP cree queda atribuido a ese perfil.

---

## 1. Config por producto (guardar en `PRODUCTOS/[NOMBRE]/2_DATA_PRODUCTO.txt`)
```
MCP_ACCOUNT_ID : [cuenta de anuncios habilitada para MCP, moneda USD]
MCP_PAGE_ID    : [page_id de la fanpage asignada — con WhatsApp conectado]
MCP_PIXEL_ID   : [dataset_id que recibe las Compras offline del WABA — para ETAPA-7]
TASA_MONEDA_POR_USD : [tasa del producto — moneda local por USD; GT: `tasa_usd_gtq`]
```

### Inventario de cuentas — el dueño es `PRODUCTOS/_DIM_CUENTAS.csv`

> La tabla de abajo es un **espejo legible** de la lectura en vivo de las cuentas. El dato que
> el sistema usa sale del CSV, que `gen_publicacion.py` lee para resolver `cuenta_id`, moneda,
> mínimo de presupuesto y si la cuenta sube media local. Una tabla en prosa se desincroniza en
> silencio; un CSV lo cobra un hook.

| Cuenta | act_id | Negocio | Moneda | MCP | **Subir media** |
|---|---|---|---|---|---|
| **GTR 7** | 598687956219141 | AMG 5 (1207290087231971) | USD | ✅ | ✅ **la única** |
| GTR 3 | 581490137794343 | AMG 3 (1632082414095745) | USD | ✅ | ❌ |
| GTR 0 | 1665221077707961 | AMG 2 (523977064022240) | USD | ✅ | ❌ |
| GTR 1 | 824783947334627 | AMG 2 | USD | ✅ | ❌ |
| GTR 13 | 916746367261028 | AMG 9 (941347687954885) | USD | ❌ rollout | — |
| GTR 2 | 1680252426660775 | AMG 2 | USD | ❌ rollout | — |
| CP1 | 1346891653335162 | AMG 8 (515747137534744) | COP | ❌ rollout | — |
| Margarita Perez Carrero | 332010724162945 | (sin negocio) | COP | ✅ | — sin método de pago |

> Verificar siempre con `ads_get_ad_accounts` que la cuenta tenga `is_ads_mcp_enabled=true` y `is_queryable=true`. `min_daily_budget_cents` de las USD = 100 ($1.00); las COP = 3154.

> ⚠️ **CLEARSTEM vive en GTR 13, que NO tiene MCP.** No se puede publicar por MCP en absoluto —
> ni crear campaña, ni conjuntos, ni anuncios. Todo a mano, o se mueve a una cuenta habilitada.

### 🔴 LA SUBIDA DE MEDIA SOLO FUNCIONA EN GTR 7

`ads_creative_upload_media` con `upload_source=LOCAL_FILE` abre un widget donde el operador elige
los archivos y devuelve los hashes. **Está habilitado en una sola cuenta del portafolio.** Probado
con el mismo llamado, sin campaña ni destino de por medio:

```
GTR 7 (598687956219141)  ->  {"result_kind":"LOCAL_FILE", "ui_enabled":true}   ✅
GTR 0 (1665221077707961) ->  "Local file upload is not available for ad account…"  ❌
GTR 1 (824783947334627)  ->  "Local file upload is not available for ad account…"  ❌
GTR 3 (581490137794343)  ->  "Local file upload is not available for ad account…"  ❌
```

**La variable es la CUENTA, no el destino del anuncio.** La hipótesis de que fallaba "porque los
anuncios van a WhatsApp" quedó descartada por este test: la subida es a la biblioteca de la cuenta
y ocurre **antes** de que exista campaña alguna — no sabe si el ad irá a WhatsApp o a una web.

> **Corolario operativo:** no cambiar el destino a `WEBSITE` para intentar destrabar la subida.
> Sería inútil (no es la variable) y **rompería el tracking**: LucidBot atribuye por el bloque
> `referral` del Click-to-WhatsApp (`source_id`, `ctwa_clid`). Un ad a web no genera conversación
> de WhatsApp y el negocio es COD por WhatsApp — ver el gotcha de APR-035 en §7.

**Las dos vías cuando el producto no corre en GTR 7:**
1. El operador sube los assets **a mano** a la biblioteca de la cuenta y avisa; el MCP los lee con
   `ads_get_ad_images` y arma creativos y anuncios normalmente.
2. Se monta la campaña **en GTR 7**, que además es lo que la FASE 2 ya pide para su campaña C
   (`CALENDARIO_ESCALADO` §1.7.2: la C va en OTRA cuenta para no competirse en la subasta).

> ⚠️ **Nunca reusar el nombre de archivo al subir una versión corregida.** Meta guarda las dos y
> quedan indistinguibles por nombre: un PNG regenerado con el mismo nombre que el viejo puede
> terminar publicado en anuncios que debían usar la versión corregida. Usar sufijo `_V2`, `_V3`.

---

## 2. PRE-FLIGHT (antes de crear) — checklist
1. `ads_get_ad_accounts` → la cuenta está `is_ads_mcp_enabled` + `is_queryable`. Anotar `min_daily_budget_cents` y `currency`.
2. `ads_get_user_pages` → la fanpage existe y el **lanzador** la ve. Anotar `page_id`.
3. La fanpage está **asignada a la cuenta de anuncios** y tiene **WhatsApp conectado**. (Si `ads_get_ad_account_pages` no la lista todavía, puede ser lag de lectura — el test real es que el primer ad set la acepte.)
4. Tener la salida de ETAPA-6 (6 conjuntos con nombre, ángulo, formato, hook, precio) y de ETAPA-4 (copies).

Si falta cualquiera → detener y pedirlo. No inventar IDs.

---

## 3. PARÁMETROS FIJOS DE CREACIÓN (validados)
| Parámetro | Valor | Nota |
|---|---|---|
| objetivo campaña | `OUTCOME_TRAFFIC` | campaña de **Tráfico** |
| buying_type | `AUCTION` | |
| presupuesto | **ABO** (en el conjunto) | NO poner presupuesto a nivel campaña |
| optimization_goal | `CONVERSATIONS` | "Maximizar conversaciones" |
| destination_type | `WHATSAPP` | |
| promoted_object | `{"page_id": MCP_PAGE_ID}` | |
| billing_event | `IMPRESSIONS` | |
| daily_budget | **sale de `_PARAMETROS_PUBLICACION.csv`**, por fase y brazo | F1 $2.99 · F2 $6.00/conjunto · F3 $15.00 CBO. Convertir: `cents = round(USD*100)`, y siempre en la **unidad menor de la moneda de la cuenta** (CP1 factura en COP). El dueño único de esta cifra es el CSV, nunca esta prosa. |
| targeting | `{"geo_locations":{"countries":["GT"]},"age_min":[MIN],"age_max":[MAX],"targeting_automation":{"advantage_audience":0}}` | 🔴 **`age_min`/`age_max` salen del `avatar_edad` del ángulo**, no son 18-65 fijos (APR-060: mismo ángulo y creativo, Q473.6/venta a 25+ contra Q30.6 a 45-60). Tabla de derivación en `ETAPA-6.md` → BANDA DE EDAD. Amplio 18-65 solo si el ángulo no tiene avatar de edad marcada. Advantage+ **siempre** OFF: sin eso Meta ignora la banda. |
| start_time | `[mañana]T04:00:00-06:00` | 4 AM día siguiente, hora del huso de la cuenta (cuentas GT: Guatemala, UTC-6) |
| status | **PAUSED** (default del MCP) | nunca ACTIVE |

> Moneda: la cuenta es USD; `daily_budget` va en **centavos de USD**. Los umbrales CPA de ETAPA-1 están en la moneda local del producto (GT: Q) → al leer (ETAPA-7) se convierte USD→moneda local con la `tasa` del producto. El MCP corre solo en cuentas GT; el mercado CO es manual.

---

## 4. SECUENCIA DE CREACIÓN

### Paso A — Campaña (1 llamada)
```
ads_create_campaign(
  ad_account_id = MCP_ACCOUNT_ID,
  campaign_name = "[PRODUCTO]_TEST_[YYYYMMDD-lanzamiento]",
  objective     = "OUTCOME_TRAFFIC",
  buying_type   = "AUCTION",
  special_ad_categories = "[]"
)
```
Guardar `campaign_id`. Verificar que `valid_optimization_goals` incluya `CONVERSATIONS`.

### Paso B — 6 conjuntos (1 llamada por ángulo; el 1º como prueba)
Crear **primero 1** (test de que la página es aceptada). Si OK, crear los **5 restantes en paralelo**.
```
ads_create_ad_set(
  ad_account_id   = MCP_ACCOUNT_ID,
  campaign_id     = campaign_id,
  ad_set_name     = "[ANGULO]_[PRODUCTO]_TEST",   ← llave exacta para ETAPA-7
  billing_event   = "IMPRESSIONS",
  optimization_goal = "CONVERSATIONS",
  destination_type = "WHATSAPP",
  promoted_object = '{"page_id":"MCP_PAGE_ID"}',
  daily_budget    = 159,
  targeting       = '{"geo_locations":{"countries":["GT"]},"age_min":45,"age_max":60,"targeting_automation":{"advantage_audience":0}}',   -- ← ejemplo con avatar 45-60; derivar del ángulo, NO copiar
  start_time      = "[mañana]T04:00:00-06:00"
)
```
Guardar los 6 `ad_set_id`. Todos nacen PAUSED.

### Paso C — STOP. Los ANUNCIOS requieren media (no se pueden crear vacíos)
El copy vive en el *creativo*, que necesita `video_id` o `image_hash`. **El MCP sube media SOLO en
GTR 7** (`ads_creative_upload_media` + `upload_source=LOCAL_FILE`; ver §1). En las demás cuentas la
sube el operador a mano. Entonces:
1. La carpeta `Ads/MEDIA_[PRODUCTO]/` con los videos renombrados por conjunto (`[PRODUCTO]_[N]_[ANGULO].mp4`) **ya existe** — se creó justo después de ETAPA-0 (ver CLAUDE.md PASO 1.5), antes de saber si habría cuenta MCP. Acá solo se completa con las imágenes de los ángulos-imagen (Prompt Maestro de ETAPA-4) y un `PROMPTS_IMAGENES_[PRODUCTO].txt`.
   > Legacy: NusavaB12 (creado vía MCP antes de este fix) usa el nombre con prefijo de cuenta `Ads/MEDIA_GTR7_NUSAVAB12/` — no renombrar retroactivamente. Todo producto nuevo usa `Ads/MEDIA_[PRODUCTO]/` sin prefijo de cuenta, porque la cuenta se asigna después de ETAPA-0.
2. El operador genera las imágenes, sube los assets de `Ads/MEDIA_[PRODUCTO]/` a la **biblioteca de medios** de la cuenta, y avisa "media subida".

### Paso D — Anuncios (2do paso, tras media) — 2 por conjunto
1. `ads_get_ad_videos` / `ads_get_ad_images` → obtener `video_id` / `image_hash` por asset (emparejar por nombre al MAPA).
2. Por conjunto: `ads_create_creative` con `page_id`, el `video_id`/`image_hash`, `message` = copy de ETAPA-4, `headline` = título, `description`, `call_to_action_type = "WHATSAPP_MESSAGE"`, `link_url` del WhatsApp si aplica.
3. `ads_create_ad` **×2 idénticos** por conjunto (Anuncio A y B, mismo creativo — regla del duplicado interno). PAUSED.
4. Precio P1u solo en los conjuntos marcados (máx 3/6, ideal 2/6): va en copy Y en creativo.

### Paso E — MAPA + entrega
Generar `PRODUCTOS/[NOMBRE]/3_CAMPAÑA_META.txt` (ver plantilla abajo) con todos los IDs (campaña, 6 conjuntos), el cruce conjunto↔ángulo↔asset↔copy↔precio, y las instrucciones de subida + activación 4 AM. **Es la llave de unión para ETAPA-7.**

---

## 5. EDICIONES POST-CREACIÓN (seguras solo en PAUSED)
- Cambiar presupuesto/edad/targeting de un conjunto PAUSED: `ads_update_entity(entity_type="ad_set", fields={...})`. Sobre conjuntos PAUSED no resetea aprendizaje.
- **Nunca** `ads_update_entity` de presupuesto/estado sobre algo ACTIVO de forma automática.
- Activar: `ads_activate_entity` lo hace el operador manualmente a las 4 AM (o desde Business Manager).

---

## 6. LECTURA (ETAPA-7) — mapeo de campos del MCP (verificado)
Campos válidos en `ads_get_ad_entities` (level adset/campaign): `amount_spent` (gasto), `impressions`, `clicks`, `actions:omni_purchase` (= **Compras offline / ventas del bot**), `conversions`, `cost_per_result`, `results`, `cpm`, `ctr`, `frequency`, `reach`. Breakdown `age` para el desglose por edad.
```
CPA real (moneda local) = (amount_spent / actions:omni_purchase) × TASA_DEL_PRODUCTO
% conversación por clic = conversaciones ÷ clics (× 100)
```
Comparar contra **CPA Base / CPA Break Even** (ETAPA-1). Zonas: 🟢 ≤ Base · 🟡 ≤ Break Even · 🔴 > Break Even. NUNCA ROAS.

> Nota: la columna personalizada del operador ("CPA LUCIDBOT") no se expone por MCP — ETAPA-7 calcula el CPA desde `amount_spent ÷ omni_purchase`. Confirmar con una llamada de prueba en qué acción cae "Compras" si cambia la config del pixel.

---

## 7. GOTCHAS aprendidos
- `ads_get_ad_account_pages` puede tardar en listar una página recién asignada (lag de lectura). El test real es crear el 1er ad set: si acepta la página, está bien.
- Nombres de campos: es `amount_spent` (no `spend`); las acciones van como `actions:omni_purchase`, `actions:link_click`, etc. (no `actions` suelto).
- `daily_budget` siempre en la **unidad menor de la moneda de la cuenta** (USD → centavos).
- La página debe estar (a) accesible por el lanzador y (b) asignada a la cuenta, con WhatsApp.
- Todo nace PAUSED: es el candado nativo del human-in-the-loop. El doble candado es el `start_time` 4 AM.
- **Anuncios (2º paso, tras media):** imágenes por `ads_create_creative` necesitan `link_url=https://wa.me/<NUMERO>` + CTA `WHATSAPP_MESSAGE`.
  > ⚠️ **EL `wa.me` NO SUSTITUYE AL DESTINO NATIVO (APR-035).** El `link_url` solo es válido cuando el **conjunto** ya lleva `destination_type=WHATSAPP` + `promoted_object={"page_id":…}`: ahí Meta enruta por Click-to-WhatsApp y el mensaje entrante llega con el bloque `referral` (`source_id` = ad_id, `ctwa_clid`) que es **lo único que LucidBot usa para atribuir**. Si el conjunto NO tiene ese destino, el `wa.me` abre el WhatsApp correcto y el número funciona perfecto — pero el mensaje llega **sin `referral`** y el conjunto nace **ciego**: gasta, trae conversaciones reales y marca 0 ventas para siempre. **Verificar el destino del CONJUNTO antes de poner el `link_url`, nunca al revés.**
  > 🛡️ **REGLA ANTI-CEGUERA: no crear conjuntos de cero.** DUPLICAR uno que ya trackea y cambiarle solo el creativo — así el destino bueno se hereda: un conjunto creado de cero puede quedar 100% ciego en cuestión de segundos si el destino no se configuró primero. Videos: `ads_create_ad` con `object_story_spec.video_data` + `image_url`=miniatura (de `ads_get_ad_videos(fields=["picture"])`); el CTA `WHATSAPP_MESSAGE` va **sin** `value.link` (el destino lo enruta el conjunto). Saltos de línea del copy = `\n`. 2 anuncios idénticos/conjunto.
- **Número de WhatsApp:** no hay tool que lo lea de la página; lo da el operador (Administrador → Destino del anuncio). Formato `502XXXXXXXX`.
- **Actualizar copy:** `ads_update_entity(entity_type="ad", fields={"creative":{...}})` — `creative_id` para imagen, `object_story_spec` para video.
- **BORRADOR no existe por API:** el MCP solo deja PAUSED (publicado, sin gastar). El "1 de 5" (varias opciones de texto/título por anuncio) tampoco por API → 1 texto/anuncio vía MCP, el resto lo agrega el operador a mano.
- **No borrar la campaña en el Administrador:** si se borra, los conjuntos quedan ARCHIVED/DELETED y no se reusan — hay que reconstruir todo.

---

## 7.5 CONTROL D+1 DE TRACKING (obligatorio tras CADA tanda nueva)

> **Por qué existe:** un conjunto ciego es indistinguible de un conjunto malo. Gasta igual, trae conversaciones reales y marca **0 ventas** — y ese cero es un artefacto, no un veredicto (APR-034). Una tanda ciega llegó a gastar **$166 en 8 conjuntos 100% ciegos** antes de que alguien lo notara, y se llevó puesta una renovación creativa entera: 8 hooks que nunca se midieron.

**Al día siguiente de lanzar cualquier tanda nueva** (campaña, conjuntos duplicados, anuncios nuevos), antes de mirar rendimiento:

1. Meta → conversaciones/mensajes de **cada conjunto nuevo** (export de Ads Manager o MCP).
2. LucidSales → mensajes atribuidos a **esos mismos conjuntos**.
3. Comparar conjunto por conjunto:

| Resultado | Lectura | Acción |
|---|---|---|
| Meta >0 · Lucid >0 | tracking OK | seguir, medir normal |
| Meta >0 · Lucid **=0** | **conjunto CIEGO** | **cortar YA** — no esperar el día 3. Duplicar un conjunto que sí trackea y reemplazarlo |
| Meta =0 · Lucid =0 | no arrancó | revisar estado/presupuesto, no es tracking |

4. Si la tanda salió ciega, marcar sus creativos **PENDIENTES DE RE-TESTEAR**, nunca "no vendieron" (APR-034).

> **Regla de oro: antes de escribir un veredicto de rendimiento, verificar que el conjunto TENÍA tracking.** Sin tracking no hay veredicto, solo gasto sin medir.

---

## 8. Plantilla del 3_CAMPAÑA_META (resumen de campos)
```
Cuenta / Negocio / Moneda · FanPage (page_id) · Campaña (campaign_id) · Objetivo (Tráfico→CONVERSATIONS→WHATSAPP)
Presupuesto ($/conjunto + cents) · Segmentación · Programación 4 AM · CPA Base/BE (Q) · MCP_PIXEL_ID
Por conjunto: nombre (llave) · ad_set_id · ángulo · formato (video archivo / imagen) · hook · precio · copy
Pendientes: subir media → crear 2 anuncios/conjunto → activar 4 AM
RESULTADOS_TESTEO / ANGULO_GANADOR (los completa ETAPA-7)
```
```
```
