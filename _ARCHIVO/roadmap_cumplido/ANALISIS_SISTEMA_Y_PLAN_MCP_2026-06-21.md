# Análisis profundo del Sistema Vitalcom + Plan de integración Meta Ads MCP

**Fecha:** 21 junio 2026 · **Autor:** revisión asistida por Claude · **Estado:** plan aprobado para revisión (no se tocaron archivos del sistema todavía)

Este documento hace tres cosas: (1) deja claro que el sistema actual se entendió a fondo, (2) da un veredicto de cada uno de los 5 skills del mentor con el ajuste exacto que cada uno necesita para tu modelo CPA/WhatsApp, y (3) diseña la integración con el MCP de Meta con *human-in-the-loop* real, sin riesgo de que algo se publique solo.

---

## 1. Cómo entendí tu sistema (para que sepas que estamos en la misma página)

Tu sistema es un **orquestador de dos fases** (Pre-testeo → Post-testeo) que convierte 21 transcripciones de video en una campaña de testeo de 6 ángulos lista para lanzar, y luego escala el ángulo ganador. No ejecuta tareas: detecta la fase, invoca subagentes de etapa en orden, y transfiere outputs completos entre ellos.

La lógica de negocio que lo hace funcionar, y que ningún skill externo debe romper:

- **Se optimiza por conversaciones, se mide por CPA, nunca por ROAS.** El objetivo de campaña es *Tráfico → iniciar conversaciones por WhatsApp* (eso es lo que Meta optimiza). La venta se cierra en **LucidBot**, y tu **WABA/tracker la devuelve a Meta como conversión offline** (columna "Compras"). O sea: Meta **sí ve la venta, pero solo para medir, no para optimizar**. Tu **CPA real = Importe gastado ÷ Compras (offline)** — ya lo tenés automatizado en tu columna personalizada **CPA LUCIDBOT**. Métricas reales: **CPA real** vs **CPA Base** y **CPA Break Even** de la tabla de ETAPA-1, apoyado en **% conversación por clic** y **% conversación por impresión** como termómetro temprano.
- **Reglas operativas fijas (Joaquín/Angi/Mercy):** Q54 por conjunto (ABO, nunca CBO en testeo), lanzamiento a las **4 AM del día siguiente** (nunca el mismo día), **2 anuncios por conjunto** (creativo duplicado interno, baja el CPA hasta 50%), 6 conjuntos = 6 ángulos distintos.
- **Doctrina de creativos:** video donde calza el ángulo, imagen Prompt Maestro donde el ángulo es virgen. Nunca se pausa un ángulo por falta de video.
- **Compliance Andrómeda:** texto en imagen <20%, nada de antes/después bilateral, cada copy/creativo único, sin frases médicas ("cura/trata/elimina") ni timelines imposibles. Andrómeda no banea — sube el CPM en silencio.
- **Trazabilidad:** ETAPA-GUARDAR-PRODUCTO escribe `_CONTEXTO.txt` con un **REGISTRO DE CONJUNTOS** donde el *nombre exacto del conjunto* es la llave de unión con Meta. Esa llave es lo que hace posible leer métricas de vuelta y saber qué número corresponde a qué ángulo.

**Conclusión de lectura:** el sistema ya está maduro y bien razonado. Tu propio `PLAN_EXPANSION_MCP.txt` (v1.0, mayo 2026) ya había diagnosticado los 5 cuellos de botella y diseñado ETAPA-6 expandida + ETAPA-7 (monitor) + ETAPA-8 (biblioteca). Este documento **no reinventa eso: lo confirma, lo actualiza al MCP ya conectado, y le suma el veredicto de los 5 skills nuevos.**

---

## 1.5 Medición — la versión corregida (lo que de verdad usás)

Esta sección reemplaza cualquier referencia anterior a "ROAS" o a "Meta no ve la venta". Es la base sobre la que se calibran ETAPA-7 y la skill de 3 Q's.

### Cómo medís de verdad
1. **La campaña optimiza conversaciones** (objetivo Tráfico/Mensajes a WhatsApp). Eso es lo que Meta busca atraer.
2. **La venta la cierra LucidBot** y tu **WABA** la manda de vuelta a Meta como **conversión offline** → cae en la columna **"Compras"**.
3. Tu **CPA real = Importe gastado ÷ Compras (offline)**, ya calculado en tu columna **CPA LUCIDBOT** dentro de Ads Manager.

### Los dos umbrales que mandan (de la tabla de ETAPA-1, ya costeados con envío + devoluciones + otros gastos)
- **CPA Base** = el CPA que te deja tu **~15% de ganancia esperada** por venta. Es tu objetivo de rentabilidad. (Ej: producto de Q40 → **CPA Base Q30.8**.)
- **CPA Break Even (P1u BE)** = el CPA **máximo** antes de perder dinero, costeado para 1 unidad. (Ej: producto de Q40 → **BE Q60.5**.)

### Zonas de decisión (lo que ETAPA-7 y la skill 3 Q's aplican, en vez de ROAS)
| CPA real (por pedido) | Estado | Acción |
|---|---|---|
| ≤ CPA Base | 🟢 Rentable sano | Candidato a escalar (+20% matutino) |
| > CPA Base y ≤ CPA Break Even | 🟡 Zona de optimización | Mantener; mejorar copy/ángulo; no escalar agresivo |
| > CPA Break Even | 🔴 Perdiendo dinero | Pausar ese conjunto (después del Día 3) |

> **Medir por PEDIDO, no por unidad.** Una venta de 2u/3u es **una sola adquisición** con más margen (el envío se comparte), así que comparar el CPA real contra el **BE de 1 unidad** es deliberadamente **conservador**: si vendés combos, tu rentabilidad real es mejor que lo que muestra esa lectura. Ventaja a tu favor.

> **ROAS = NO USAR.** ROAS es ingreso bruto ÷ gasto; no resta costo de producto, envío ni devoluciones (pesadas en pago contra entrega), y con precios variables y combos da un número confuso. Para tu modelo, CPA-vs-umbrales es estrictamente mejor. Cualquier skill del mentor que hable de ROAS se reconfigura a CPA Base / CPA Break Even.

### ⚠️ Conversión de moneda — tu cuenta de Meta está en USD, tu costeo en Quetzales
La cuenta de anuncios factura en **dólares**; tu tabla de ETAPA-1 está en **Quetzales**. Hay que convertir en cada lado.
- **Tasa de hoy: 1 USD = Q7.62** (`TASA_USD_GTQ` — guardar en el `_CONTEXTO.txt` y actualizar por sesión).
- **Una sola fuente de verdad: la tabla en Q.** Al leer Meta (USD), se convierte a Q para comparar contra los umbrales. Al crear presupuesto en el MCP, se convierte Q→USD.
- Equivalencias de hoy:
  - Presupuesto **Q54 → $7.09** por conjunto (≈ los $7 que ya usás).
  - **CPA Base Q30.8 → $4.04** · **CPA Break Even Q60.5 → $7.94** (para el ejemplo de producto de Q40).

---

## 2. Diagnóstico: lo que está sólido y lo que el MCP debe resolver

### Sólido (no tocar)
La cadena de inteligencia — ETAPA-0 (clasificación de ángulos por video), ETAPA-1 (costeo exacto sin inventar), ETAPA-2 (ángulos + avatar), ETAPA-4 (copies regla Kaleth + compliance), ETAPA-5 (bot paraguas) — es el corazón del sistema y funciona. El MCP **no** debe meterse ahí.

### Los 3 cuellos de botella que el MCP sí ataca

| # | Cuello de botella actual | Solución con MCP |
|---|---|---|
| 1 | **Creación manual de campaña** (20–40 min replicando ETAPA-6 a mano, propenso a errores de nombre/config) | ETAPA-6 crea el esqueleto vía MCP **en PAUSED**: campaña + 6 conjuntos con nombres exactos, Q54 ABO, Conversaciones/WhatsApp, programados 4 AM |
| 2 | **Input manual de métricas** (transcribís a mano los números para iniciar FASE 2) | ETAPA-7 lee métricas directo del MCP y las mapea por nombre de conjunto al REGISTRO DE CONJUNTOS |
| 3 | **Sin monitoreo sistemático de fatiga** (se decide "a ojo"; el creativo decae 15–25%/semana y se detecta 7–14 días tarde) | ETAPA-7 calcula frecuencia, caída de CTR y CPA día a día y marca señales de fatiga |

> Nota importante: los cuellos 2 y 3 (ETAPA-7) son **lectura**, de bajo riesgo. El cuello 1 (creación) es **escritura**, y por eso lleva candados (PAUSED + revisión humana). Esa asimetría de riesgo guía todo el diseño de la Sección 4.

---

## 3. Veredicto de los 5 skills del mentor

Decisión tomada: **mantenerlos como skills sueltos** (los invocás manualmente), con el ajuste mínimo de CPA/moneda donde haga falta. No se convierten en etapas nativas. Aquí el veredicto producto por producto.

### Resumen ejecutivo

| Skill | Veredicto | Por qué | Ajuste necesario |
|---|---|---|---|
| **Analizador de creativos** | ✅ **USAR tal cual** | Inteligencia creativa pura (31 secciones: Schwartz, LF8, NESB). Cero conflicto con CPA. Alimenta ETAPA-2 y ETAPA-4. | Ninguno técnico. Ideal combinarlo con `ads_library_search` para deconstruir creativos de competencia. |
| **3 Q's (análisis de campañas)** | 🟡 **USAR con modificación** | El camino "💬 Interacción/Mensajes" ya mide **costo por conversación**, no ROAS — calza con tu modelo. Sirve como auditoría manual profunda. | Reemplazar umbrales genéricos por tus Q (CPA Obj/Break Even, %conv clic ≥35/48/60). Voseo. Solapa con ETAPA-7 (que es MCP, no CSV). |
| **Monitor de Pixel** | 🟡 **MANTENER condicional** | Bien construido, usa MCP, métrica-agnóstico (no ROAS). Útil **solo si tenés un dataset/Pixel o CAPI con eventos de mensajería**. | Ninguno. Programarlo semanal *si y solo si* existe dataset_id. Si no usás Pixel, queda en reserva. |
| **Excel de Estrategia (Felipe Vergara)** | 🔴 **NO integrar al flujo core** | Choca de frente con tu sistema validado: propone **CBO Advantage+**, embudo Presentación/Evaluación/Conversión/Ascensión, lookalikes y reparto mensual — todo lo contrario a tu ABO Q54 / 6 ángulos / mensajes. Es **otra metodología** (e-commerce ROAS). | Dejarlo en repisa. A lo sumo, canibalizar sus definiciones de públicos de retargeting para una futura capa de ascensión (ver Sección 6). |
| **Sugeridor de productos (DPA)** | 🔴 **NO aplica a tu modelo** | Es para catálogos / Dynamic Ads con muchos SKU y gasto por producto. Vos testeás **un producto a la vez** con conversión en WhatsApp; no hay catálogo ni DPA. | Parquearlo. Solo cobraría sentido si algún día corrés una tienda multi-SKU con catálogo. |

### Detalle de los dos que requieren matiz

**3 Q's — el matiz CPA vs ROAS que pediste.** El skill trae tablas para Ventas (ROAS), Leads (CPL) e **Interacción/Mensajes (costo por conversación)**. Para Vitalcom siempre se usa el camino **Interacción**, y ahí el benchmark ya es "costo por conversación objetivo" — no ROAS. El ajuste correcto:
- Alimentar como objetivo tu **CPA Objetivo** (ej. Q30.8) y marcar 🔴 al superar el **CPA Break Even** (ej. Q60.5).
- Reemplazar el semáforo de "% conversación a mensajes" del skill por **tu** escala validada: **% conversación por clic** 🔴 <35% · 🟡 48–50% · 🟢 60–70%; **% conversación por impresión** 1.5% malo · 2.5% bueno · 3.5% excelente.
- **Salvedad de medición:** tu **CPA real = Importe gastado ÷ Compras (offline)** — la columna "Compras" que alimenta tu WABA, no el "costo por conversación" de Meta (ese es costo por mensaje, un proxy temprano). La skill adaptada calcula CPA con las Compras offline y lo compara contra CPA Base/Break Even en Quetzales (convirtiendo desde USD a 7.62). El "costo por conversación" y los % de conversación se usan solo como termómetro de las primeras horas, antes de que sincronicen las compras offline.
- Es un skill de **CSV** (sin MCP). Tu ETAPA-7 planificada hace lo mismo pero **vía MCP** (sin exportar nada). Por eso: 3 Q's = herramienta de auditoría manual cuando querés un análisis visual profundo de un período; ETAPA-7 = el monitor diario automático. No se pisan, se complementan.

**Monitor de Pixel — el matiz "¿tenés Pixel?".** Tu conversión vive en WhatsApp/LucidBot, así que un Pixel de web no es central a tu operación. Este skill vale **solo si** configuraste un dataset/CAPI que registre eventos de mensajería o de la fanpage. Si lo tenés, es un chequeo de salud semanal valioso (avisa si los eventos caen >20% o si el EMQ está bajo). Si no lo tenés, no fuerces su uso: queda como reserva para cuando montes señales server-side.

---

## 4. Diseño de la integración MCP — esqueleto completo en PAUSED (human-in-the-loop)

Esta es la pieza nueva. Confirmé contra los esquemas reales de las herramientas del MCP que **todo se crea en estado PAUSED por defecto** en los tres niveles (campaña, conjunto, anuncio). Es decir: el *human-in-the-loop* no depende de que yo "me acuerde" de pausar — es el comportamiento nativo de la herramienta. Nada puede gastar hasta que vos lo actives a mano.

### 4.1 La regla de oro (de tu propio PLAN_EXPANSION, confirmada)
El MCP solo actúa en dos momentos: **PREPARACIÓN (crear en PAUSED)** y **LECTURA (reporting)**. **Nunca** modifica presupuesto, bidding o status de un conjunto activo de forma automática — eso resetea la fase de aprendizaje de Andrómeda. Los ajustes sobre campañas vivas los hacés vos a mano siguiendo la recomendación de ETAPA-7.

### 4.2 Qué crea el MCP automáticamente (FASE 1 — testeo)

**Paso A — Campaña** (`ads_create_campaign`):
- `objective = OUTCOME_TRAFFIC` (tu campaña es de **Tráfico**) · `buying_type = AUCTION` · `special_ad_categories = []`
- El objetivo de rendimiento ("Maximizar conversaciones") se fija en el conjunto con `optimization_goal = CONVERSATIONS` (Paso B). OUTCOME_TRAFFIC admite CONVERSATIONS — confirmado en el esquema del MCP.
- Sin presupuesto a nivel campaña → fuerza **ABO** (el presupuesto vive en el conjunto). Esto respeta tu regla "ABO en testeo, nunca CBO".
- Nombre: `[PRODUCTO]_TEST_[YYYYMMDD]` · **se crea en PAUSED**

**Paso B — 6 conjuntos** (`ads_create_ad_set`, uno por ángulo):
- `optimization_goal = CONVERSATIONS` · `destination_type = WHATSAPP` · `billing_event = IMPRESSIONS`
- `promoted_object = {"page_id": <MCP_PAGE_ID de la fanpage asignada>}`
- `daily_budget = 709` (la cuenta es en **USD**: Q54 ÷ 7.62 = $7.09 → 709 centavos de dólar). El presupuesto se fija en la moneda de la cuenta, no en Quetzales.
- `targeting = {"geo_locations":{"countries":["GT"]}, "age_min": <edad del CONTEXTO, ej. 45>}` — targeting amplio, **sin inventar IDs de intereses** (Andrómeda premia lo abierto)
- `start_time = 4 AM del día siguiente` (ISO 8601) — segundo candado: aunque se activara, no entrega antes de las 4 AM
- Nombre: `[ANGULO]_[PRODUCTO]_TEST` ← **idéntico al REGISTRO DE CONJUNTOS** (esta es la llave para ETAPA-7)
- **se crea en PAUSED**

> Antes del Paso B, una llamada a `ads_get_ad_accounts` para leer `min_daily_budget_cents` de la cuenta (GTQ) y confirmar que Q54 está por encima del mínimo. Si no lo está, te aviso antes de crear nada.

### 4.3 El punto donde entra tu mano (el límite real del MCP)

El MCP **no sube videos ni imágenes** (limitación confirmada — es por peso/tokens y por la propia API). Y un anuncio necesita un creativo, que necesita un `video_id` o `image_hash` que **solo existe después de subir el archivo**. Por eso el flujo se parte en dos sesiones, y ese corte *es* el checkpoint humano:

```
SESIÓN 1 (ahora)                          VOS (manual, Business Manager)         SESIÓN 2 (cuando subiste media)
──────────────────────────                ────────────────────────────          ──────────────────────────────
Claude crea vía MCP, todo PAUSED:    →    1. Abrís la campaña PAUSED       →    Claude lee los videos subidos
 · Campaña [PRODUCTO]_TEST                 2. Subís cada video/imagen             (ads_get_ad_videos / ads_get_ad_images),
 · 6 conjuntos (Q54, WA, 4AM)                 al ad account, según el               los empareja por nombre al MAPA,
 · MAPA_CAMPAÑA.txt (qué video                MAPA (video X → conjunto X)           crea creativos + 2 anuncios/conjunto
   va en cada conjunto + copies)           3. Revisás copies                       (duplicado interno), todo PAUSED
                                                                                  ──────────────────────────────
                                                                                  VOS revisás todo y, a las 4 AM,
                                                                                  ACTIVÁS la campaña (ads_activate_entity
                                                                                  o a mano). Recién ahí gasta.
```

En la Sesión 2, por cada conjunto: `ads_create_creative` (con `page_id`, `video_id` del archivo que subiste, `message` = texto principal del copy de ETAPA-4, `headline` = título, `description`, `call_to_action_type = WHATSAPP_MESSAGE`) y luego **dos** `ads_create_ad` idénticos (Anuncio A y Anuncio B, mismo creativo) para cumplir la regla del duplicado interno. Todo nace PAUSED.

### 4.4 Los 3 IDs que el sistema necesita por producto
Para que esto corra, el `_CONTEXTO.txt` de cada producto debe tener (tu PLAN ya lo previó):
```
MCP_ACCOUNT_ID: [cuenta de anuncios]
MCP_PAGE_ID:    [fanpage asignada por ETAPA-FANPAGE]
MCP_PIXEL_ID:   [dataset/pixel, opcional — solo si usás monitor-pixel]
```
Además, la fanpage debe tener el **número de WhatsApp conectado** (sin eso, el destino WHATSAPP falla).

### 4.5 ETAPA-7 (lectura) — cómo cierra el loop sin tocar nada activo
Cada mañana, con la campaña ≥24h activa: ETAPA-7 lee vía MCP (`ads_get_ad_entities` / insights) impresiones, clics, **mensajes iniciados, Compras (offline), gasto, frecuencia**, por conjunto; los mapea por **nombre de conjunto** al REGISTRO. Calcula **CPA real = gasto ÷ Compras** y lo convierte **USD→Q (7.62)** para compararlo contra **CPA Base / CPA Break Even**. Apoyo temprano: **% conversación por clic** y **por impresión** (antes de que sincronicen las compras offline). Aplica **tus** umbrales (no ROAS): zonas 🟢🟡🔴 de la Sección 1.5, señales de fatiga (frecuencia >4, CTR cayendo >20% en 48h, CPA subiendo >25%). Output: informe diario + recomendación. **Decide el operador.** Antes del Día 3 no se pausa nada (Andrómeda necesita ~50 eventos para salir de aprendizaje). Verificar al implementar en qué campo de acción del MCP cae tu evento "Compras" (conversión offline/custom) — se confirma con una llamada de prueba antes de construir.

### 4.6 Mapa de herramientas MCP por etapa

| Etapa | Herramientas MCP | Riesgo |
|---|---|---|
| ETAPA-2 (saturación) | `ads_library_search` (anunciantes activos por ángulo) | Lectura — nulo |
| ETAPA-6 (crear esqueleto) | `ads_get_ad_accounts`, `ads_create_campaign`, `ads_create_ad_set` | Escritura PAUSED — bajo |
| ETAPA-6 sesión 2 (creativos) | `ads_get_ad_videos`, `ads_get_ad_images`, `ads_create_creative`, `ads_create_ad` | Escritura PAUSED — bajo |
| ETAPA-7 (monitor) | `ads_get_ad_entities`, insights | Lectura — nulo |
| monitor-pixel (opcional) | `ads_get_dataset_details/quality/stats` | Lectura — nulo |
| Activación final | `ads_activate_entity` (o manual) | **Solo vos, a las 4 AM** |

---

## 5. Riesgos y candados (para no quemar cuentas con Meta)

1. **Todo nace PAUSED** — comportamiento nativo del MCP en los 3 niveles. Imposible que algo se publique solo.
2. **Doble candado de horario** — `start_time` a las 4 AM significa que, aun activado por error, no entrega antes.
3. **Nunca tocar presupuesto/bidding/status de algo activo vía MCP** — resetea el aprendizaje de Andrómeda. ETAPA-7 solo recomienda; vos ejecutás los ajustes a mano (regla del 20% matutino).
4. **Compliance Andrómeda intacto** — el MCP crea estructura y copies, pero las reglas de creativo (texto <20%, sin antes/después bilateral, sin frases médicas, único por cuenta) las sigue garantizando ETAPA-4. El MCP no relaja nada de eso.
5. **Una cuenta = un punto de falla** — tu MEJORAS_FUTURAS ya apunta a multi-cuenta (3–5 BMs). El MCP puede leer/crear en varias cuentas si el Business Suite tiene acceso; el escalado multi-cuenta se diseña en su propia fase, no en el testeo.

---

## 6. Qué dejo para después (consciente, no olvidado)

- **Excel de Estrategia** → su modelo CBO + embudo de ascensión/retargeting podría aportar **solo** en una futura capa de "ascensión" para productos ganadores con recompra. No antes, y nunca en el flujo de testeo.
- **Sugeridor DPA** → solo si algún día montás catálogo multi-SKU.
- **ETAPA-8 (biblioteca de 100+ creativos)** → es el siguiente salto real una vez que ETAPA-6/7 estén corriendo: con Andrómeda, el creativo explica ~56% del resultado, así que gestionar un banco rankeado por ángulo+performance es donde está el próximo gran ROI. Ya está bien diseñada en tu PLAN_EXPANSION.

---

## 7. Próximos pasos sugeridos (cuando me des luz verde)

1. **Confirmar los 3 IDs** (account, page, pixel) y que la fanpage tiene WhatsApp conectado. Sin esto el MCP no puede crear nada útil.
2. **Test de solo-lectura 2–3 días**: te leo métricas de una cuenta para validar que el MCP responde bien antes de habilitar escritura.
3. **Implementar ETAPA-6 expandida**: reescribir el agente para que, además del texto, genere el esqueleto PAUSED vía MCP + el `MAPA_CAMPAÑA.txt`. (Esto toca archivos del sistema — lo hago cuando aprobés esa edición.)
4. **Implementar ETAPA-7** como monitor diario MCP con tus umbrales CPA.
5. **Adaptar 3 Q's** (umbrales Q + voseo) y dejar **monitor-pixel** programado solo si hay dataset.

> Recordá: por tu decisión, en esta sesión **no edité ningún archivo del sistema**. Este documento es el plan; la implementación de ETAPA-6/7 y los ajustes a los skills se hacen en una sesión aparte cuando confirmes.
