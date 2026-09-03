---
name: ciclo-diario
description: CICLO DE OPTIMIZACIÓN post-lanzamiento. Recorre PRODUCTOS/_PORTAFOLIO.txt y, por cada producto VIVO, corre el monitor de métricas (etapa-7), el motor de decisión de escalado (etapa-8) y la lectura concepto↔métrica (etapa-10); la fábrica de conceptos (etapa-9) corre en paralelo todos los días. Termina regenerando el dashboard. Úsala en la auditoría programada de cada mañana, o cuando el operador dice "auditoría", "cómo van las campañas", "métricas de hoy", "qué pauso", "qué escalo" o pega un export de LucidSales.
tools: Read, Write, Glob, Grep, Bash, Task
---

# CICLO DE OPTIMIZACIÓN — post-lanzamiento

No va en la secuencia de FASE 1/2/3. Es lo que corre **después de lanzar**, todos los días.

**Recorre `PRODUCTOS/_PORTAFOLIO.txt` y audita CADA producto en ESTADO=VIVO**, no uno solo.

---

## `etapa-7` — Monitor diario de métricas

Cada mañana (campaña ≥24h activa) o como tarea programada: lee los conjuntos, calcula **CPA real
(Q)**, rankea, detecta fatiga e identifica el **ángulo ganador** para iniciar FASE 2. Solo lectura —
nunca toca presupuestos/estados.

- **Robustez de lectura:** no fijar el `campaign_id` a ciegas. El operador pausa/renombra/duplica
  campañas (caso NusavaB12: la campaña viva era un duplicado manual "…- Copia"). Debe **listar las
  campañas de la cuenta y tomar la ACTIVE cuyo nombre contenga el producto**, y verificar gasto > 0.
- **Sin CPA (tracking roto):** si `omni_purchase` sale "Not available", rankear PROVISIONAL por
  eficiencia de conversación y NO declarar ganador oficial.
  `%conv/clic-enlace = conversaciones ÷ clics-en-enlace` (usar `actions:link_click`, NO `clicks`
  totales).

Detalle en `.claude/agents/ETAPA-7.md`; mapeo de campos en `MCP_PLAYBOOK.md` §6; reglas de data en
`DATA_PLAYBOOK.md`.

---

## `etapa-8` — Motor de decisión de ESCALADO

Tras `etapa-7`. No es un reporte de "quién gana": es el **plan de acción para vender más** aplicando
`ESCALADO_PLAYBOOK.md` contra la data real. Ordena las palancas — optimizar flujo hacia el ganador,
**surfing +20% diario**, duplicar conjunto, **Post ID**, **multicuenta**, **multifanpage**, subir
precio, y —variable #1— **renovar/replicar los creativos del ganador entendiendo POR QUÉ ganó**
(brief para `etapa-4`).

Solo lee y recomienda. **Escalado fuerte SOLO con CPA real confirmado.**

---

## `etapa-9` — Fábrica de conceptos (DIARIA)

No espera a la FASE 2: produce **≥6 ejecuciones/día** desde los 22 blueprints canónicos, balanceadas
por rol de embudo, y las registra en `_DIM_CREATIVOS.csv` con su ciclo de vida.

**Audita los atascos antes de producir** — una pieza `GENERADO` que lleva más de 7 días sin `ad_id`
es una alerta, porque el cuello de botella medido no fue producir sino **publicar** (7 de 8 PNG de
TINNIDROP llevaban 26 días en disco).

El llenado lo hace la skill `generar-conceptos`.

---

## `etapa-10` — Lector concepto ↔ métrica

Tras `etapa-7`. Cruza el rendimiento de cada anuncio contra los atributos del blueprint JSON que lo
originó (`canonico_id`) y responde **por qué** ganó: descomposición por atributo con **piso de
evidencia** (≥5 ventas y ≥2 creativos por nivel, sin solape de intervalos de Poisson), cada **rol de
embudo con su propia métrica** (TOFU por costo de conversación · MOFU por %conv/clic · BOFU por
cierre) y la matriz **ángulo × concepto** que dice si un concepto viaja o es de contexto. Su salida
es el **brief de producción** de `etapa-9`. Solo lectura.

> **`etapa-8` mueve dinero; `etapa-10` mueve el diseño.** No se pisan.

---

## `etapa-11` — Optimizador de flujo

No es diaria: corre **al confirmar el ángulo ganador por VENTA**, entre FASE 1 y FASE 2 (ver la
skill `fase-2-conceptos`, PASO 0).

> **`etapa-10` mira el pre-clic (por qué hacen clic); `etapa-11` mira el post-clic (por qué,
> habiendo escrito, no compran).**

---

## Los cuatro archivos de apoyo del ciclo

- 📖 **`ESCALADO_PLAYBOOK.md`** — el **QUÉ**: fases y timing, señales, palancas en orden, cómo
  replicar el creativo ganador, contingencia, árbol de decisión y los umbrales de métricas (§8).
- 🗓️ **`CALENDARIO_ESCALADO.md`** — el **CUÁNDO**: ritmo día-a-día con gates (Ventana 0 lanzamiento ·
  Días 1-2 DATA no ventas · Día 3 GATE #1 podar · Días 4-6 GATE #2 FASE 2 del ganador · Día 7+
  escalado). Incluye la **REGLA DEL MULTI-GANADOR**: el bot paraguas es de TESTEO; a escala cada
  ángulo ganador corre su **FASE 2 dedicada**.
- 🧮 **`DATA_PLAYBOOK.md`** — el **CON QUÉ**: los CSV, cómo leerlos sin sacar cifras falsas, fórmula
  de ganancia, break-even y el dashboard.
- 🗂️ **`PRODUCTOS/_PORTAFOLIO.txt`** — registro maestro de TODOS los productos trackeados.

---

## ÚLTIMO PASO, SIEMPRE

Anexar al CSV → **luego** regenerar el dashboard:

```bash
python Ads/_TOOLS/gen_dashboard.py
```

Si el CSV cambió y el dashboard no se regeneró, el operador está leyendo data vieja.

---

## Dónde se escribe

Los informes por producto van a `PRODUCTOS/[NOMBRE]/`. **Todo informe fechado** (auditorías
nocturnas, planes multi-producto) va a **`PRODUCTOS/_AUDITORIAS/`**, nunca suelto en la raíz. Son
registro histórico legible: **prohibido reconstruir métricas desde ahí** (eso sale del CSV).

**Retención:** se conservan los últimos 30 días sueltos; lo anterior se colapsa a subcarpeta mensual
(`2026-07/`). Nunca se borran.
