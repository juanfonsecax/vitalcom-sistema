---
name: fase-3-flujo
description: "FASE 3 — Optimización de flujo LucidBot. Con el concepto ganador ya confirmado en 2 de 2, ángulo y concepto quedan fijos al mismo presupuesto mientras se reescribe el flujo LucidBot hacia ese ganador: etapa-11 entrega el brief (si no está fresco), etapa-5 redacta los BLOQUES DE JUICIO, el operador aplica el cambio en LucidBot y lo anexa como CAMBIO_BOT, y el ciclo diario mide el cierre en horas. Úsala cuando flujo.py sitúa al producto en un nodo F3.*, o cuando el operador dice \"tengo concepto ganador\", \"hay que reescribir el bot\", \"el bot no cierra\" o \"aplicar el CAMBIO_BOT\"."
tools: Read, Write, Glob, Grep, Bash, Task
---

# FASE 3 — OPTIMIZACIÓN DE FLUJO LUCIDBOT

**Ángulo y concepto ya están fijos por el ganador de FASE 2.** La única variable es el flujo
LucidBot, con el mismo presupuesto que ya venía corriendo; nada nuevo se publica en Meta. Los cambios
de flujo se notan en HORAS, no en semanas.

```
1 ángulo + 1 concepto validados, MISMO presupuesto · la variable es el flujo LucidBot ← mide el CIERRE
```

**Secuencia:** `etapa-11` (brief, si no está fresco) → `etapa-5` (reescribe) → el operador aplica en
LucidBot y registra `CAMBIO_BOT` → el ciclo diario mide el cierre.

---

## Entrada — el flujo dicta

`python Ads/_TOOLS/flujo.py [producto_key]` mete al producto en FASE 3 con `F3.entrada` de
`DOCTRINA/FLUJO.json`: **`concepto_2de2`**, el mismo concepto es el mejor CPA (≥ `min_ventas_escalar`
ventas) en **2 de 2** campañas de conceptos. **No hace falta ningún `CAMBIO_BOT` para entrar**: la
reescritura es lo que se hace dentro de esta fase.

---

## PASO 1 — `etapa-11` (brief, si no está fresco)

`etapa-11` ya diagnosticó el cierre y la congruencia anuncio ↔ bot en FASE 2 (nodo `F2.etapa-11`).
Si ese diagnóstico sigue vigente para el concepto ganador, se reutiliza. Se vuelve a correr acá solo
si no corrió, o si es anterior a un cambio material (nuevo concepto ganador, nueva objeción
detectada). Su output es el brief priorizado de qué cambiar en el flujo.

## PASO 2 — `etapa-5` reescribe los BLOQUES DE JUICIO (nodo `F3.reescribir`)

`etapa-5` redacta los 4 campos del catálogo, testimonios, audio, M2 y FAQ a partir del brief,
empezando por las propuestas de valor y la congruencia anuncio ↔ flujo. Llena las frases del ángulo
en `PRODUCTOS/_DIM_FLUJO_BOT.csv` y los bloques en `PRODUCTOS/[carpeta]/BLOQUES_BOT.md`; el texto fijo
y el orden del flujo no son suyos. Dentro del bot la prioridad es conversión: no se suaviza por
compliance. Cerrar con `python Ads/_TOOLS/gen_flujo_bot.py [producto_key]`.

## PASO 3 — El operador aplica y registra `CAMBIO_BOT`

El operador aplica el cambio en LucidBot y lo registra el **mismo día**:

```bash
python Ads/_TOOLS/registrar_evento.py --producto [PRODUCTO] --evento CAMBIO_BOT --motivo "[qué cambió]" --fuente "etapa-5 [fecha]"
```

Si decide explícitamente saltarse la reescritura, registra `EXCEPCION_CAMBIO_BOT`: misma fecha-ancla
para medir, y deja constancia de que fue una decisión. `_EVENTOS.csv` nunca se edita a mano.

## PASO 4 — Medir el cierre (nodo `F3.medir_cierre`)

El ciclo diario (`Ads/_TOOLS/gen_decisiones.py`, dentro de `ciclo-diario`) recalcula en cada pasada
el cierre posterior al `CAMBIO_BOT` / `EXCEPCION_CAMBIO_BOT`. Umbrales de `PRODUCTOS/_PARAMETROS_DECISION.csv`:
- `min_mensajes_cierre`: mensajes mínimos recibidos después del cambio para que la medición cuente.
- `cierre_min_escalar_pct`: el piso duro. Por debajo, el producto se queda en FASE 3.
- `cierre_meta_min_pct` / `cierre_meta_max_pct`: benchmark de referencia, nunca bloquea.

---

## SALIDA — gate hacia FASE 4 (`F4.entrada`)

Las tres condiciones juntas:
1. `concepto_2de2` (heredado de la entrada).
2. `CAMBIO_BOT` (o `EXCEPCION_CAMBIO_BOT`) fechado DESPUÉS del concepto ganador.
3. `cierre_post_cambio_bot`: al menos `min_mensajes_cierre` mensajes y cierre ≥ `cierre_min_escalar_pct`,
   medidos desde ese cambio.

**Por debajo del piso de cierre, el producto no avanza: vuelve al PASO 1 para otra iteración del
flujo**, con el mismo presupuesto (`decidir.py` cuenta F3 como fase en testeo: no sale ninguna orden
de escalado).

---

## FIN FASE 3

```
FASE 3 EN CURSO ✓ / GANADA ✓

□ Brief de etapa-11 vigente para el concepto ganador
□ Bloques de juicio reescritos por etapa-5, aplicados en LucidBot
□ CAMBIO_BOT (o EXCEPCION_CAMBIO_BOT) registrado en _EVENTOS.csv el mismo día
□ Cierre medido con min_mensajes_cierre desde el CAMBIO_BOT — ≥ cierre_min_escalar_pct para pasar a FASE 4; si no, otra iteración
```
