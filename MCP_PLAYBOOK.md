# MCP_PLAYBOOK — Creación de campañas de testeo vía Meta Ads MCP

**Estado:** VERIFICADO en producción (primer caso: NusavaB12 en GTR 7, 2026-06-21).
**Alcance:** este playbook convierte la salida de ETAPA-6 en una campaña **real creada en Meta, en estado PAUSED**, para cualquier producto. El MCP **solo crea en PAUSED y solo lee**; nunca activa ni toca presupuestos de campañas vivas. **El operador publica/activa manualmente.**

> Regla de oro (Andrómeda): el MCP actúa en dos momentos — PREPARACIÓN (crear en PAUSED) y LECTURA (reporting). Nunca cambia presupuesto/estado de algo activo de forma automática.

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
TASA_USD_GTQ   : [tasa del día, ej. 7.62]
```

### Inventario de cuentas (verificado 2026-06-21) — usar solo las habilitadas y consultables
| Cuenta | act_id | Negocio | Moneda | MCP |
|---|---|---|---|---|
| GTR 7 | 598687956219141 | AMG 5 (1207290087231971) | USD | ✅ enabled |
| GTR 3 | 581490137794343 | AMG 3 | USD | ✅ enabled |
| GTR 0 | 1665221077707961 | AMG 2 | USD | ✅ enabled |
| GTR 1 | 824783947334627 | AMG 2 | USD | ✅ enabled |
| GTR 2 / 13 / CP1 | — | — | — | ❌ rollout pendiente |

> Verificar siempre con `ads_get_ad_accounts` que la cuenta tenga `is_ads_mcp_enabled=true` y `is_queryable=true`. `min_daily_budget_cents` de las USD = 100 ($1.00).

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
| daily_budget | **$1.59 = `159`** centavos USD | modo low-budget actual del operador. Convertir si se cambia: `cents = round(USD*100)`. (Equivale a ~Q12.1; el legacy Q54 era el modo anterior.) |
| targeting | `{"geo_locations":{"countries":["GT"]},"age_min":[MIN],"age_max":[MAX],"targeting_automation":{"advantage_audience":0}}` | 🔴 **`age_min`/`age_max` salen del `avatar_edad` del ángulo**, no son 18-65 fijos (corregido 02-sep, APR-060: mismo ángulo y creativo, Q473.6/venta a 25+ contra Q30.6 a 45-60). Tabla de derivación en `ETAPA-6.md` → BANDA DE EDAD. Amplio 18-65 solo si el ángulo no tiene avatar de edad marcada. Advantage+ **siempre** OFF: sin eso Meta ignora la banda. |
| start_time | `[mañana]T04:00:00-06:00` | 4 AM día siguiente, hora Guatemala (UTC-6) |
| status | **PAUSED** (default del MCP) | nunca ACTIVE |

> Moneda: la cuenta es USD; `daily_budget` va en **centavos de USD**. Los umbrales CPA de ETAPA-1 están en Q → al leer (ETAPA-7) se convierte USD→Q con TASA_USD_GTQ.

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
El copy vive en el *creativo*, que necesita `video_id` o `image_hash`. El MCP **no sube media**. Entonces:
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
CPA real (Q) = (amount_spent / actions:omni_purchase) × TASA_USD_GTQ
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
  > ⚠️ **EL `wa.me` NO SUSTITUYE AL DESTINO NATIVO — ES LA CAUSA #1 SOSPECHADA DE LA TANDA CIEGA DEL 27-JUL (APR-035).** El `link_url` solo es válido cuando el **conjunto** ya lleva `destination_type=WHATSAPP` + `promoted_object={"page_id":…}`: ahí Meta enruta por Click-to-WhatsApp y el mensaje entrante llega con el bloque `referral` (`source_id` = ad_id, `ctwa_clid`) que es **lo único que LucidBot usa para atribuir**. Si el conjunto NO tiene ese destino, el `wa.me` abre el WhatsApp correcto y el número funciona perfecto — pero el mensaje llega **sin `referral`** y el conjunto nace **ciego**: gasta, trae conversaciones reales y marca 0 ventas para siempre. **Verificar el destino del CONJUNTO antes de poner el `link_url`, nunca al revés.**
  > 🛡️ **REGLA ANTI-CEGUERA: no crear conjuntos de cero.** DUPLICAR uno que ya trackea y cambiarle solo el creativo — así el destino bueno se hereda. La migración del 12-ago duplicó todo el portafolio y trackea al 100%; la tanda creada de cero el 27-jul (00:11:08–00:11:23, 15 segundos) quedó 100% ciega. Videos: `ads_create_ad` con `object_story_spec.video_data` + `image_url`=miniatura (de `ads_get_ad_videos(fields=["picture"])`); el CTA `WHATSAPP_MESSAGE` va **sin** `value.link` (el destino lo enruta el conjunto). Saltos de línea del copy = `\n`. 2 anuncios idénticos/conjunto.
- **Número de WhatsApp:** no hay tool que lo lea de la página; lo da el operador (Administrador → Destino del anuncio). Formato `502XXXXXXXX`.
- **Actualizar copy:** `ads_update_entity(entity_type="ad", fields={"creative":{...}})` — `creative_id` para imagen, `object_story_spec` para video.
- **BORRADOR no existe por API:** el MCP solo deja PAUSED (publicado, sin gastar). El "1 de 5" (varias opciones de texto/título por anuncio) tampoco por API → 1 texto/anuncio vía MCP, el resto lo agrega el operador a mano.
- **No borrar la campaña en el Administrador:** si se borra, los conjuntos quedan ARCHIVED/DELETED y no se reusan — hay que reconstruir todo.

---

## 7.5 CONTROL D+1 DE TRACKING (obligatorio tras CADA tanda nueva)

> **Por qué existe:** un conjunto ciego es indistinguible de un conjunto malo. Gasta igual, trae conversaciones reales y marca **0 ventas** — y ese cero es un artefacto, no un veredicto (APR-034). La tanda del 27-jul gastó **$166 en 8 conjuntos 100% ciegos** antes de que alguien lo notara, y se llevó puesta la renovación creativa entera de TINNIDROP: 8 hooks que nunca se midieron.

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
