---
name: fase-4-escalado
description: "FASE 4 — Escalado. Con un concepto ganador en 2 de 2 apariciones, CPA real bajo Break-Even y el cierre del flujo LucidBot validado tras el CAMBIO_BOT (FASE 3), orquesta la compra de volumen: campaña 1-1-7 con el creativo validado ×7, expansión horizontal por Post ID, multicuenta y multi-fanpage, y el plan escrito en 4_PLAN_ESCALADO.txt. Aplica las cuatro reglas duras del escalado. Úsala cuando flujo.py sitúa al producto en un nodo F4.*, o cuando el operador dice \"tengo cierre validado\", \"quiero volumen\", \"escalar\" o \"subir presupuesto\"."
tools: Read, Write, Glob, Grep, Bash, Task
---

# FASE 4 — ESCALADO

## Qué hace esta fase

**No mide nada: compra volumen.** Ángulo, concepto y flujo (cierre) ya están validados.

```
1 ángulo + 1 concepto + 1 flujo, los tres validados × 7 instancias   ← no mide: compra volumen
```

**1-1-7** a **$15-18/día**. Después, expansión horizontal (Post ID, multicuenta, multi-fanpage) y
`1-7-7` si el inventario de creativos lo sostiene.

**Secuencia:** `etapa-3` (banco de copy) → `etapa-6` (FASE 4) →
`etapa-guardar-producto` → ciclo `etapa-7` (monitor + escalado fusionados) / `etapa-10`

---

## EL FLUJO DICTA

`python Ads/_TOOLS/flujo.py [producto_key]` mete al producto en FASE 4 con TRES condiciones, las
tres en `F4.entrada` de `DOCTRINA/FLUJO.json`:

1. `concepto_2de2`: el mismo concepto es el mejor CPA (≥ `min_ventas_escalar` ventas) en **2 de 2**
   campañas de conceptos. Un ganador de 1 de 2 es ruido.
2. Un `CAMBIO_BOT` (la reescritura del flujo hacia el ganador, FASE 3 — nodo `F3.reescribir`, ver
   `.claude/skills/fase-3-flujo/SKILL.md` y `DOCTRINA/PLANTILLAS_FLUJO_BOT.md`) fechado DESPUÉS del
   concepto ganador — o un `EXCEPCION_CAMBIO_BOT` si el operador decide explícitamente saltarse la
   reescritura. **El `CAMBIO_BOT` de la fase 2 (PASO 2 de `fase-2-conceptos`, el A/B paraguas
   vs. dedicado) normalmente NO alcanza**, porque se registra ANTES de que el concepto gane en 2
   de 2: hace falta el `CAMBIO_BOT` de la reescritura final hacia el ganador, posterior a esa fecha.
3. `cierre_post_cambio_bot`: ≥ `min_mensajes_cierre` mensajes recibidos DESPUÉS de ese `CAMBIO_BOT`
   (o `EXCEPCION_CAMBIO_BOT`), con cierre (mensajes → ventas) ≥ `cierre_min_escalar_pct`
   (`PRODUCTOS/_PARAMETROS_DECISION.csv`, doctrina en `DOCTRINA/GUIA_MADRE_PARAMETRIZADA.md`
   `PROHIBIDO_ESCALAR_CIERRE_BAJO`). `cierre_meta_min_pct`/`max_pct` (15-20%) se muestran como
   benchmark, nunca bloquean. Por debajo del 10% el producto se queda en FASE 3 para otra
   iteración del flujo.

Los objetos de escalado que existan sin las tres condiciones se cantan como avisos. Criterio del
operador: flujo de caja para el ciclo COD de 4-7 días.

---

## PASO 0 — Banco de copy para la expansión horizontal

Si `etapa-3` no corrió todavía, corre acá: su output —los 8-12 microángulos del
ángulo ganador— es el banco de copy que alimenta la expansión horizontal de esta fase. Ese es su
único consumidor real.

Inputs: ficha del ángulo ganador + output de `etapa-2`.
Output: mapa de sub-dolores y objeciones + 8-12 microángulos con su frase de apertura.

**`etapa-guardar-producto` tiene que volcar este output en la sección
6b (BANCO DE MICROÁNGULOS) de `4_PLAN_ESCALADO.txt`** (plantilla en `DOCTRINA/ESCALADO/08_PLAN_ENTREGABLE.md §7`).
`flujo.py` verifica en `F4.plan` que ese archivo contenga «MICROÁNGULO»; sin eso, el trabajo de
`etapa-3` no queda con ningún rastro verificable en disco.

---

## PASO 1 — `etapa-6` (FASE 4 — planificador de escalado)

Inputs: concepto ganador (`concepto_key` + variante), ángulo ganador, Post ID si existe, output de
`etapa-1`, microángulos del PASO 0 (banco de copy para la expansión horizontal).

Output: **1-1-7** — una campaña, un conjunto, el creativo validado ×7, **$15-18/día**.

**7 instancias del mismo creativo validado** por conjunto.

---

## Las cuatro reglas duras de la FASE 4

1. **Duplicar al presupuesto INICIAL**, nunca al actual.
2. **+20 % una sola vez al día, en la mañana.** El intradía (varias subidas hasta las 3 PM) está
   **CONGELADO** hasta que la fábrica sostenga ≥6 creativos/día — ver choque C-02 de
   `_CONOCIMIENTO/MATRIZ_METODOLOGIA.md`.
3. **Muere la campaña, no el creativo.** CPA en alza sostenida a 7 días → apagar la campaña y
   relanzar el creativo en otra cuenta, en campaña nueva.
4. **Nunca escalar fuerte sin CPA real confirmado.** Con `omni_purchase` en "Not available", el
   ranking es provisional y no autoriza escalado agresivo.

---

## PASO 2 — `etapa-guardar-producto`

Escribe `4_PLAN_ESCALADO.txt` en `PRODUCTOS/[NOMBRE]/` (plantilla en `DOCTRINA/ESCALADO/08_PLAN_ENTREGABLE.md` §7). Se
sobrescribe cada ciclo y sube `v[N]`.

⚠️ El slot `3_` es **solo** para IDs de Meta. Nunca meter ahí el plan de escalado.

---

## PASO 2b — Exploración paralela de ángulos nuevos (F4.exploracion, P12)

**No bloquea nada de lo de arriba** — corre en paralelo, como `F2.etapa-11`. Arranca solo cuando
`flujo.py` marca el gate propio de `F4.exploracion` cumplido (F4 rentable según `decidir.py`,
DOCTRINA/FLUJO.json). Es un mini-F1 fijo de `exploracion_n_angulos` ángulos nuevos, TODO EN
IMAGEN, medido por VENTA como F1. Detalle completo (gate, parámetros, esquema del plan,
naming): `DOCTRINA/ESCALADO/09_EXPLORACION_PARALELA.md §7b`. Secuencia: `etapa-2` → `etapa-6`
(`_PLAN_EXPLORACION.json`) → `etapa-guardar-producto` → `publicar-meta` con
`Ads/_TOOLS/gen_publicacion.py --fase 4 --brazo EXPLORACION`. Un ángulo ganador de esta
exploración entra a FASE 2 por el mismo gate `angulo_ganador` que cualquier otro.

---

## FIN FASE 4

```
FASE 4 EN CURSO ✓

□ Campaña 1-1-7 creada (PAUSED) y programada 4 AM
□ Concepto ganador ×7 con Post ID (o subido de cero si el objetivo no lo permite)
□ Presupuesto inicial anotado en _EVENTOS.csv (es el valor al que se duplica después)
□ 4_PLAN_ESCALADO.txt escrito en PRODUCTOS/[NOMBRE]/
```
