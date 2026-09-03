---
name: fase-3-escalado
description: FASE 3 — Escalado. Con un concepto ganador en 2 de 2 apariciones y CPA real bajo Break-Even, orquesta la compra de volumen: campaña 1-1-7 con el creativo validado ×7, expansión horizontal por Post ID, multicuenta y multi-fanpage, y el plan escrito en 4_PLAN_ESCALADO.txt. Aplica las cuatro reglas duras del escalado. Úsala cuando el operador responde "3" a la pregunta inicial, o dice "tengo concepto ganador", "quiero volumen", "escalar" o "subir presupuesto".
tools: Read, Write, Glob, Grep, Bash, Task
---

# FASE 3 — ESCALADO

## Qué hace esta fase

**No mide nada: compra volumen.** Ángulo y concepto ya están validados.

```
1 ángulo + 1 concepto, ambos validados × 7 instancias   ← no mide: compra volumen
```

**1-1-7** a **$15-18/día**. Después, expansión horizontal (Post ID, multicuenta, multi-fanpage) y
`1-7-7` si el inventario de creativos lo sostiene.

**Secuencia:** `etapa-3` (banco de copy) → `etapa-6` (FASE 3) →
`etapa-guardar-producto` → ciclo `etapa-7` / `etapa-8` / `etapa-10`

---

## Verificación obligatoria antes de iniciar

- [ ] **Concepto ganador en 2 de 2** apariciones de la FASE 2 (regla de replicación)
- [ ] Ángulo ganador con CPA real bajo Break-Even, medido semanal y sobre ENTREGADOS
- [ ] Flujo de caja que aguante el ciclo COD de 4-7 días al nuevo nivel de gasto

Si falta cualquiera → detener. **Un ganador de 1 de 2 es ruido.**

---

## PASO 0 — Banco de copy para la expansión horizontal

Si `etapa-3` no corrió todavía, corre acá: su output —los 8-12 microángulos del
ángulo ganador— es el banco de copy que alimenta la expansión horizontal de esta fase. Ese es su
único consumidor real.

Inputs: ficha del ángulo ganador + output de `etapa-2`.
Output: mapa de sub-dolores y objeciones + 8-12 microángulos con su frase de apertura.

---

## PASO 1 — `etapa-6` (FASE 3 — planificador de escalado)

Inputs: concepto ganador (`concepto_key` + variante), ángulo ganador, Post ID si existe, output de
`etapa-1`, microángulos del PASO 0 (banco de copy para la expansión horizontal).

Output: **1-1-7** — una campaña, un conjunto, el creativo validado ×7, **$15-18/día**.

**7 instancias del mismo creativo validado** por conjunto.

---

## Las cuatro reglas duras de la FASE 3

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

Escribe `4_PLAN_ESCALADO.txt` en `PRODUCTOS/[NOMBRE]/` (plantilla en `DOCTRINA/ESCALADO_PLAYBOOK.md` §7). Se
sobrescribe cada ciclo y sube `v[N]`.

⚠️ El slot `3_` es **solo** para IDs de Meta. Nunca meter ahí el plan de escalado.

---

## FIN FASE 3

```
FASE 3 EN CURSO ✓

□ Campaña 1-1-7 creada (PAUSED) y programada 4 AM
□ Concepto ganador ×7 con Post ID (o subido de cero si el objetivo no lo permite)
□ Presupuesto inicial anotado en _EVENTOS.csv (es el valor al que se duplica después)
□ 4_PLAN_ESCALADO.txt escrito en PRODUCTOS/[NOMBRE]/
```
