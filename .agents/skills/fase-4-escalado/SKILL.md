---
name: fase-4-escalado
description: "FASE 4 — Escalado. Con un concepto ganador en 2 de 2 apariciones, CPA real bajo Break-Even y el cierre del flujo LucidBot validado tras el CAMBIO_BOT (FASE 3), orquesta la compra de volumen: campaña 1-1-7 con el creativo validado ×7, expansión horizontal por Post ID, multicuenta y multi-fanpage, y el plan escrito en 4_PLAN_ESCALADO.txt. Aplica las cuatro reglas duras del escalado. Úsala cuando flujo.py sitúa al producto en un nodo F4.*, o cuando el operador dice \"tengo cierre validado\", \"quiero volumen\", \"escalar\" o \"subir presupuesto\"."
tools: Read, Write, Glob, Grep, Bash, Task
---

# FASE 4 — ESCALADO

**No mide nada: compra volumen.** Ángulo, concepto y flujo ya están validados.

```
1 ángulo + 1 concepto + 1 flujo, los tres validados × 7 instancias   ← no mide: compra volumen
```

**1-1-7** con el presupuesto de `PRODUCTOS/_PARAMETROS_PUBLICACION.csv` (hoy $15/día). Después,
expansión horizontal (Post ID, multicuenta, multi-fanpage) y `1-7-7` si el inventario de creativos lo
sostiene.

**Secuencia:** `etapa-3` (banco de copy) → `etapa-4` (copies por microángulo) → `etapa-6` (FASE 4) →
`etapa-guardar-producto` → ciclo diario (`etapa-7` / `etapa-10`)

---

## Entrada — el flujo dicta

`python Ads/_TOOLS/flujo.py [producto_key]` mete al producto en FASE 4 con las tres condiciones de
`F4.entrada` (`DOCTRINA/FLUJO.json`):

1. `concepto_2de2`: el mismo concepto es el mejor CPA (≥ `min_ventas_escalar` ventas) en **2 de 2**
   campañas de conceptos.
2. Un `CAMBIO_BOT` de la reescritura de FASE 3 (skill `fase-3-flujo`, nodo `F3.reescribir`) fechado
   DESPUÉS del concepto ganador, o un `EXCEPCION_CAMBIO_BOT`. El `CAMBIO_BOT` del A/B de FASE 2
   normalmente no alcanza: es anterior al concepto ganador.
3. `cierre_post_cambio_bot`: al menos `min_mensajes_cierre` mensajes después de ese cambio, con
   cierre ≥ `cierre_min_escalar_pct` (`PRODUCTOS/_PARAMETROS_DECISION.csv`). `cierre_meta_min_pct` /
   `cierre_meta_max_pct` son benchmark, nunca bloquean. Por debajo del piso, el producto se queda en
   FASE 3.

Los objetos de escalado que existan sin las tres condiciones se cantan como avisos. Criterio del
operador: flujo de caja para el ciclo COD de 4-7 días.

---

## PASO 0 — `etapa-3` (banco de copy)

Si no corrió todavía, corre acá. Inputs: ficha del ángulo ganador + output de `etapa-2`. Output:
mapa de sub-dolores y objeciones + 8-12 microángulos con su frase de apertura: el banco de copy de la
expansión horizontal.

`etapa-guardar-producto` lo vuelca en la sección **6b (BANCO DE MICROÁNGULOS)** de
`4_PLAN_ESCALADO.txt`; `flujo.py` verifica en `F4.plan` que ese archivo contenga «MICROÁNGULO».

## PASO 0b — `etapa-4` (MODO FASE 4: copies por microángulo)

Inputs: los microángulos del PASO 0, el ángulo ganador, el producto y P1u. Output: un copy
testimonio por microángulo (hasta 6), con precio en máximo 3. Son los copies que `etapa-6`
asigna a cada conjunto de la expansión horizontal.

## PASO 1 — `etapa-6` (plan de escalado)

Inputs: concepto ganador (`concepto_key` + variante), ángulo ganador, Post ID si existe, output de
`etapa-1`, los microángulos del PASO 0 y los copies del PASO 0b. Output: **1-1-7**: una campaña, un conjunto, el creativo
validado ×7.

## Las cuatro reglas duras

1. **Duplicar al presupuesto INICIAL**, nunca al actual.
2. **+20 % una sola vez al día, en la mañana.** El escalado intradía está congelado hasta que la
   fábrica sostenga ≥6 creativos por día.
3. **Muere la campaña, no el creativo.** CPA en alza sostenida a 7 días → apagar la campaña y
   relanzar el creativo en otra cuenta, en campaña nueva.
4. **Nunca escalar fuerte sin CPA real confirmado.** Sin tracking de ventas el ranking es provisional.

## PASO 2 — `etapa-guardar-producto`

Escribe `4_PLAN_ESCALADO.txt` en `PRODUCTOS/[carpeta]/` (plantilla en
`DOCTRINA/ESCALADO/08_PLAN_ENTREGABLE.md` §7). Se sobrescribe cada ciclo y sube `v[N]`. El slot `3_`
es solo para IDs de Meta.

## PASO 2b — Exploración paralela de ángulos nuevos (`F4.exploracion`)

No bloquea nada de lo de arriba. Arranca cuando `flujo.py` marca cumplido el gate de
`F4.exploracion` (F4 rentable según `decidir.py`). Es un mini-F1 de `exploracion_n_angulos` ángulos
nuevos, todo en IMAGEN, medido por venta. Secuencia: `etapa-2` → `etapa-6` (`_PLAN_EXPLORACION.json`)
→ `etapa-guardar-producto` → `publicar-meta` con `Ads/_TOOLS/gen_publicacion.py --fase 4 --brazo EXPLORACION`.
Detalle en `DOCTRINA/ESCALADO/09_EXPLORACION_PARALELA.md` §7b. Un ángulo que gane acá entra a FASE 2
por el mismo gate que cualquier otro.

---

## FIN FASE 4

```
FASE 4 EN CURSO ✓

□ Campaña 1-1-7 creada (PAUSED) y programada 4 AM
□ Concepto ganador ×7 con Post ID (o subido de cero si el objetivo no lo permite)
□ Presupuesto inicial anotado en _EVENTOS.csv (es el valor al que se duplica después)
□ 4_PLAN_ESCALADO.txt escrito en PRODUCTOS/[NOMBRE]/
```
