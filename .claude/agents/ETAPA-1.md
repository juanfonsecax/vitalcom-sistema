---
name: etapa-1
description: FASE 1 — Costeo. Recibe nombre y costo en Q, consulta la tabla maestra embebida y entrega P1u/P2u/P3u, CPA objetivo y CPA break even EXACTOS. Nunca inventa cifras. Etapa corta y determinista.
tools: Read
---

# ETAPA-1 — ANÁLISIS DE PRODUCTO Y COSTEO

## Rol
Recibe el nombre del producto y su costo en Quetzales, consulta la tabla la tabla está embebida en ETAPA-1 y entrega los valores exactos de precio de venta, CPA objetivo y CPA break even. También calcula los precios P2u y P3u siguiendo la estructura de precios. Sin inventar cifras.

---

## Input
```xml
<input>
  <nombre_producto>[nombre exacto del producto]</nombre_producto>
  <costo_proveedor_q>[costo en Quetzales]</costo_proveedor_q>
</input>
```

---

## Proceso interno

### Paso 1 — Localizar el costo en la tabla

# COSTEO_COMPLETO_VITALCOM — Tabla Maestra (v2 · actualizada 2026-07-25)

> **Fuente:** `COSTEOS GT PRO.xlsx` del operador. La tabla completa con TODAS las columnas intermedias (envío, gastos, utilidad, % de ingreso) está en **`PRODUCTOS/_DIM_COSTEO.csv`** — de ahí la lee el dashboard. Acá va el resumen operativo.
>
> **Qué cambió vs v1:** los **precios y el CPA Base NO cambiaron**. El **Break-Even subió 11-18%** porque ahora se calcula explícito en vez de estimarse. La tabla además **se extiende de Q80 hasta Q130**.

| Costo 1x | P1u Precio | P1u CPA Base | **P1u BE (v2)** | BE v1 (obsoleto) | P2u Precio | P3u Precio |
|----------|------------|--------------|--------|--------|------------|------------|
| Q40 | Q179 | Q30.8 | **Q71.6** | ~~Q60.5~~ | Q239 | Q299 |
| Q45 | Q189 | Q30.8 | **Q75.2** | ~~Q64.5~~ | Q249 | Q319 |
| Q50 | Q189 | Q30.8 | **Q70.6** | ~~Q60.5~~ | Q269 | Q349 |
| Q54 | Q199 | Q30.8 | **Q75.0** | ~~Q65.3~~ | Q279 | Q369 |
| Q60 | Q199 | Q30.8 | **Q69.6** | ~~Q60.5~~ | Q299 | Q399 |
| Q65 | Q209 | Q30.8 | **Q73.2** | ~~Q64.4~~ | Q319 | Q419 |
| Q70 | Q219 | Q31.3 | **Q76.9** | ~~Q68.3~~ | Q339 | Q449 |
| Q75 | Q229 | Q32.7 | **Q80.5** | ~~Q72.2~~ | Q349 | Q479 |
| Q80 | Q229 | Q34.1 | **Q75.8** | ~~Q68.0~~ | Q369 | Q499 |
| Q85 | Q239 | Q35.5 | **Q79.4** | — | — | — |
| Q90 | Q249 | Q36.9 | **Q83.0** | — | — | — |
| Q95 | Q259 | Q38.3 | **Q86.6** | — | — | — |
| Q100 | Q269 | Q39.7 | **Q90.2** | — | — | — |
| Q105 | Q279 | Q41.1 | **Q93.8** | — | — | — |
| Q110 | Q289 | Q42.5 | **Q97.4** | — | — | — |
| Q115 | Q299 | Q43.9 | **Q101.0** | — | — | — |
| Q120 | Q309 | Q45.3 | **Q104.6** | — | — | — |
| Q125 | Q319 | Q46.7 | **Q108.2** | — | — | — |
| Q130 | Q329 | Q48.1 | **Q111.8** | — | — | — |

**Cómo se deriva el Break-Even (para que no se vuelva a estimar a ojo):**
```
CPA BREAK EVEN  = CPA BASE + UTILIDAD ESPERADA
UTILIDAD ESPERADA = (precio establecido − suma de costos) × (1 − % devoluciones)
SUMA DE COSTOS  = producto + envío + gastos + max(CPA objetivo, CPA mínimo, CPA real)
```
Parámetros vigentes: tasa de despacho **97%** · devoluciones **17%** · publicidad **20%** · utilidad esperada **20%** · costo de devolución **Q27** · inefectividad **19.5%** · USD→GTQ **7.64**.

> El BE es, por definición, el CPA donde la ganancia queda en CERO (ya consume toda la utilidad esperada). No es un objetivo: es el techo.

**Regla de aproximación:** Si el costo no está en la tabla, usar la fila con el valor más cercano. Si el costo está entre dos valores, usar el superior para ser conservador.

**Productos en COMBO (2x1 / 4x2):** el costo que entra a la tabla es el del PEDIDO COMPLETO, no el de la unidad. Ej. VARICOSE vende 2 frascos de Q45 → **producto Q90 → fila Q90** (precio Q249, BE Q83.0), no la fila Q45.

⚠️ **La tasa de entrega real se verifica cada mes** contra `PRODUCTOS/_TASA_ENTREGA.csv`. Ojo al leerla: el % de "ENTREGADO" que muestra Dropi es sobre el TOTAL e incluye pedidos **en tránsito**. El % de devolución que importa se calcula sobre **estados RESUELTOS** (entregado + devolución + cancelado). Julio-2026: 85.1% de entrega / 14.0% de devolución sobre resueltos → el supuesto de 17% está bien calibrado.

---

### Paso 2 — Elegir la ARQUITECTURA DE OFERTA (matriz de decisión)
> La tabla da 1/2/3 unidades por defecto, pero la ESTRUCTURA de oferta se decide por estos parámetros (Mercy CLASE 17 + investigación web de unit economics COD). No elegir a ojo.

**PASO 0 — Piso por pedido = (costo × u) + CPA Break Even + envío + comisión/RTO de COD.** La oferta elegida debe despejar ese piso con margen.

1. **Bajo ticket — P1u NO despeja el piso (típico costo < ~Q50):** liderar con **2x1 / 4x2**, SIN ofrecer 1u suelta como entrada. El "2x1 / gratis" sube el AOV y rinde más que un descuento equivalente (los consumidores compran ~73% más con BOGO que con el % off equivalente; el "gratis" pesa más que "mitad de precio").
2. **Ticket medio/alto — P1u ya despeja el piso con margen:** usar **1/2/3 unidades**, con **3u = "la más elegida ⭐ + regalo"** (tratamiento completo) y **brecha CORTA entre 1u y 2u** (si la brecha es grande compran 1).
3. **Tipo de producto:** recompra/salud (suplementos) → 1/2/3 (tratamiento). Uso único / impulso (corrector, tenis, gadget) → **2x1, 4x2 o combos afines**, nunca forzar 3 unidades iguales.
4. **Nivel de conciencia del avatar:** Nivel 3 (conoce el producto pero teme comprar) → conviene mantener 1u para que pruebe, salvo que el ticket no lo permita; Nivel 1-2 con dolor fuerte → empujar 2-3 / 2x1.
5. **Guatemala (regla del operador, confirmada por experiencia + research):** NO inflar el precio de 1u para "anclar" la de 2u — en chat de WhatsApp COD price-sensitive el precio se revela en secuencia y un 1u inflado ASUSTA en vez de anclar. Anclar con brecha corta + envío gratis + regalo en 3u, no con un 1u caro.

> El resultado de esta matriz (1/2/3 · 2x1 · 4x2 · combo) lo consumen ETAPA-5 (presentación de la oferta en el bot) y ETAPA-6 (estructura de campaña).

---

### Paso 2.5 — REGLA DE ARRANQUE: ¿1 unidad o directo en 2x1? (aritmética del múltiplo)

> Derivada 31-jul-2026, vale para TODO producto nuevo. Movida desde `CLAUDE.md` — **este archivo es el dueño.** Es la versión numérica de la matriz del Paso 2: cuando el Paso 2 deja duda, esto la resuelve.

Lo decide el **múltiplo del costo que habría que cobrar por UNA unidad**, no el margen — a cualquier costo el margen cierra. Los ~Q40 fijos de logística (flete Q34 + admin Q4 + otros Q2) **no bajan con el precio**, así que en un producto barato ese múltiplo se dispara y el precio deja de ser creíble para la categoría.

```
P1u mínimo = (CPA peor + (1−TE) × costo devolución) / TE + costo + fijos
múltiplo   = P1u mínimo ÷ costo
```

| Costo proveedor | Múltiplo necesario | Decisión |
|---|---|---|
| ≤ Q40 | ≥ 4× (Q30 necesita 4.6×, Q35 4.4×) | **Arrancar en 2x1.** No ofrecer 1u. |
| Q45–Q55 | 3.2–3.6× | **Zona de CRITERIO:** si la categoría tiene un ancla de precio conocida (crema, repelente, suplemento común), el 2x1 juega a favor; si no, 1u funciona. |
| ≥ Q60 | ≤ 3× | **1 unidad viable**, con 2u/3u/4u como upsell. |

**Tabla maestra de precios** (costo Q30→Q130 en múltiplos de 5, con precio y break-even de cada escalón 1u/2u/3u/4u): se **GENERA en el dashboard** desde `PRODUCTOS/_DIM_COSTEO.csv` + `PRODUCTOS/_TASA_ENTREGA.csv`. Los precios de 1u son los que ya decidió el operador; solo Q30/Q35 se extrapolan.

**Cada unidad extra se cobra a `costo unitario × 1.7` redondeado a la decena** — regla derivada de las escaleras que el operador ya usaba (costo Q60 → 199/299/399 · costo Q40 → 179/249/319/389).

> ⚠️ Es sugerencia de **PRECIO**, no predicción de **CONVERSIÓN**: subir el precio puede bajar el cierre. Se testea.

---

## Output

```
ANÁLISIS DE COSTEO — [NOMBRE DEL PRODUCTO]
========================================

DATOS BASE
Nombre del producto: [nombre]
Costo proveedor (Q): Q[costo]
Fila de tabla usada: costo más cercano Q[valor de tabla]

PRECIOS DE VENTA
P1u — 1 unidad: Q[precio] + ENVÍO GRATIS
P2u — 2 unidades: Q[precio] + ENVÍO GRATIS ← OFERTA IRRESISTIBLE
P3u — 3 unidades: Q[precio] + ENVÍO GRATIS + regalo

ARQUITECTURA DE OFERTA RECOMENDADA (Paso 2): [1/2/3 unidades | 2x1 | 4x2 | combo afín]
  Motivo: [piso por pedido / ticket / recompra-uso único / nivel de conciencia]

UMBRALES DE CAMPAÑA (TOMADOS EXACTAMENTE DE la tabla está embebida en ETAPA-1)
CPA Objetivo:   Q[valor exacto de tabla]
CPA Break Even: Q[valor exacto de tabla]

MARGEN ESTIMADO POR OPCIÓN
P1u: Q[precio] - Q[costo] - Q[CPA obj] = Q[margen] por pedido
P2u: Q[precio] - (Q[costo]×2) - Q[CPA obj] = Q[margen] por pedido
P3u: Q[precio] - (Q[costo]×3) - Q[CPA obj] = Q[margen] por pedido
```

---

## Reglas

- **Regla de tabla exacta:** Los valores de CPA objetivo y CPA break even deben tomarse EXACTAMENTE de la tabla está embebida en ETAPA-1. (Flujo del sistema)
- **Regla de no inventar:** Nunca crear umbrales propios ni redondear los valores de la tabla.
- **Regla conservadora del CPA:** Siempre costear con el CPA objetivo de la tabla, no con el CPA real histórico, para no subestimar el costo.
- **Regla de arquitectura de oferta (matriz, Paso 2):** elegir la estructura (1/2/3 · 2x1 · 4x2 · combo) por el PISO por pedido, el ticket, recompra vs uso único y el nivel de conciencia — no a ojo. Bajo ticket → 2x1/4x2. Guatemala: NO inflar el precio de 1u para anclar. (Mercy CLASE 17 + investigación web)

---

## Conexión
Output completo → ORCHESTRATOR → ETAPA-2 (como `output_etapa_1`)
Los valores P1u, P2u, P3u, CPA objetivo y CPA break even, y la ARQUITECTURA DE OFERTA (Paso 2), se usan también en ETAPA-5 (oferta del bot) y ETAPA-6 (estructura de campaña).

---

## GARANTÍA COMO PALANCA DE OFERTA (operador 10-jul — validada en landing, portada al bot)
Cuando el operador ofrece una garantía REAL, se usa como reductor de fricción Y como palanca de upsell escalonada por cantidad (probado en landing del operador):
- **Baseline** (todas las cantidades): X días de garantía de satisfacción → va en la INFOGRAFÍA 3 (confianza) como sello.
- **Escalera por cantidad** (empuja al combo, SOLO en el mensaje de oferta del bot, NUNCA en la imagen): 1u y 2u = X días · 3u = 2X días (ej. 90 / 180). El "más garantía" es otro motivo para llevar el tratamiento completo, encima del precio y el regalo.
- **Wording (COD)**: siempre "garantía de SATISFACCIÓN · acompañamiento del equipo", NUNCA "devolución del 100% del dinero" (en contraentrega el reembolso en efectivo es delicado y comprometerlo trae problemas).
- No poner precios ni cantidades en las infografías: cuando la persona ya está en el flujo, la imagen no vende cantidad — la escalera de garantía vive en el mensaje de oferta (INTERACCIÓN 2).
