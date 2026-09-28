---
name: fase-3-flujo
description: "FASE 3 — Optimización de flujo LucidBot. Con el concepto ganador ya confirmado en 2 de 2, ángulo y concepto quedan fijos al mismo presupuesto mientras se reescribe el flujo LucidBot hacia ese ganador: etapa-11 entrega el brief (si no está fresco), etapa-5 redacta los BLOQUES DE JUICIO, el operador aplica el cambio en LucidBot y lo anexa como CAMBIO_BOT, y el ciclo diario mide el cierre en horas. Úsala cuando flujo.py sitúa al producto en un nodo F3.*, o cuando el operador dice \"tengo concepto ganador\", \"hay que reescribir el bot\", \"el bot no cierra\" o \"aplicar el CAMBIO_BOT\"."
tools: Read, Write, Glob, Grep, Bash, Task
---

# FASE 3 — OPTIMIZACIÓN DE FLUJO LUCIDBOT

## Qué hace esta fase

**No mide ángulo ni concepto: ya están fijos por el ganador de FASE 2.** La única variable de esta
fase es el flujo LucidBot — mismo presupuesto que ya venía corriendo, nada nuevo se publica en
Meta. Doctrina de origen: Clase 22-ago (Calet) — `PALANCA_1` (propuestas de valor) y
`DIAGNOSTICO_1` (congruencia anuncio↔flujo) de `DOCTRINA/GUIA_MADRE_PARAMETRIZADA.md`;
`VELOCIDAD_CAMBIO_DE_FLUJO`: los cambios se notan en HORAS, no semanas.

```
1 ángulo + 1 concepto validados, MISMO presupuesto · la variable es el flujo LucidBot ← mide el CIERRE
```

**Secuencia:** `etapa-11` (brief, si no está fresco) → `etapa-5` (reescribe) → operador aplica en
LucidBot y registra `CAMBIO_BOT` → ciclo diario mide el cierre en horas.

---

## EL FLUJO DICTA

`python Ads/_TOOLS/flujo.py [producto_key]` mete al producto en FASE 3 con el mismo gate de entrada
que hoy lleva a FASE 2→3, `F3.entrada` de `DOCTRINA/FLUJO.json`:

- `concepto_2de2`: el mismo concepto es el mejor CPA (≥ `min_ventas_escalar` ventas) en **2 de 2**
  campañas de conceptos. **No hace falta ningún `CAMBIO_BOT` para entrar a FASE 3** — la reescritura
  es justamente lo que se hace DENTRO de esta fase, no un requisito previo.

---

## PASO 1 — `etapa-11` (brief, si no está fresco)

`etapa-11` diagnostica el cierre y la congruencia anuncio↔bot en **FASE 2** (nodo `F2.etapa-11`,
en paralelo al testeo de conceptos, registra `DIAGNOSTICO_CONGRUENCIA`, no bloquea nada). Si ese
diagnóstico ya existe y sigue vigente para el concepto ganador, se reutiliza tal cual — nunca se
repite el trabajo. Si no corrió todavía, o el diagnóstico es anterior a un cambio material (nuevo
concepto ganador, nueva objeción detectada), corré `etapa-11` acá para tener el brief priorizado
antes de reescribir.

Output que consume el PASO 2: brief priorizado de qué cambiar en el flujo (`.claude/agents/ETAPA-11.md`).

---

## PASO 2 — `etapa-5` reescribe los BLOQUES DE JUICIO (nodo `F3.reescribir`)

`etapa-5` redacta los 4 campos del catálogo, testimonios, audio, M2 y FAQ siguiendo:

- **El texto fijo y el orden de los elementos**, que NO son suyos: los declara
  `DOCTRINA/PLANTILLAS_FLUJO_BOT.md` (reglas A-G) y los renderiza `Ads/_TOOLS/gen_flujo_bot.py`.
- **`PALANCA_1` (propuestas de valor)** y **`DIAGNOSTICO_1` (congruencia)** de
  `DOCTRINA/GUIA_MADRE_PARAMETRIZADA.md` — la doctrina de la Clase 22-ago que sostiene esta fase.
- El brief del PASO 1 (qué está fallando y por qué, ya priorizado).

`etapa-5` llena las frases del ángulo en `PRODUCTOS/_DIM_FLUJO_BOT.csv` (notación `{{variable}}`);
lo que va entre `<<BLOQUE:x>>` es lo que esta fase reescribe. Ninguna línea `>>` (instrucción) se
pega en el flujo. **ETAPA-5 no se suaviza por compliance post-clic** (`CLAUDE.md` § ALCANCE DEL
COMPLIANCE): dentro del bot la prioridad es conversión.

---

## PASO 3 — El operador aplica y registra `CAMBIO_BOT`

El operador aplica el cambio directamente en LucidBot (fuera de este sistema) y lo anexa el
**mismo día**, nunca después:

```
python Ads/_TOOLS/registrar_evento.py --producto [PRODUCTO] --evento CAMBIO_BOT \
  --motivo "[qué cambió]" --fuente "etapa-5 [fecha]"
```

Si el operador decide explícitamente saltarse la reescritura, registra `EXCEPCION_CAMBIO_BOT` en
su lugar — mismo efecto de fecha-ancla para el PASO 4, pero deja constancia de que fue una decisión
deliberada, no un olvido. `_EVENTOS.csv` nunca se edita a mano (P3 T4): es un espejo regenerado
desde Postgres.

---

## PASO 4 — Medir el cierre (nodo `F3.medir_cierre`)

El cambio se nota en HORAS, no en días (`VELOCIDAD_CAMBIO_DE_FLUJO`). El ciclo diario
(`Ads/_TOOLS/gen_decisiones.py`, corrido por la skill `ciclo-diario`) ya recalcula el cierre
posterior al `CAMBIO_BOT`/`EXCEPCION_CAMBIO_BOT` en cada pasada — no hace falta un script aparte:

- `min_mensajes_cierre` (`PRODUCTOS/_PARAMETROS_DECISION.csv`, hoy 30): mensajes mínimos recibidos
  DESPUÉS del `CAMBIO_BOT` para que la medición sea evidencia, no ruido.
- `cierre_min_escalar_pct` (`PRODUCTOS/_PARAMETROS_DECISION.csv`, hoy 10%, doctrina
  `PROHIBIDO_ESCALAR_CIERRE_BAJO` en `DOCTRINA/GUIA_MADRE_PARAMETRIZADA.md`): el piso duro. Por
  debajo, el producto se queda en FASE 3.
- `cierre_meta_min_pct`/`cierre_meta_max_pct` (15-20%): benchmark de referencia, **nunca bloquea**.

---

## SALIDA — Gate hacia FASE 4 (`F4.entrada`)

`DOCTRINA/FLUJO.json` exige las tres condiciones juntas antes de comprar volumen:

1. `concepto_2de2` (heredado de la entrada a esta fase).
2. `CAMBIO_BOT` (o `EXCEPCION_CAMBIO_BOT`) fechado DESPUÉS del concepto ganador.
3. `cierre_post_cambio_bot`: ≥ `min_mensajes_cierre` mensajes y cierre ≥ `cierre_min_escalar_pct`,
   medidos desde ese `CAMBIO_BOT`/`EXCEPCION_CAMBIO_BOT`.

**Por debajo del 10 % de cierre, el producto no avanza: vuelve al PASO 1 de esta fase para otra
iteración del flujo.** El presupuesto se mantiene igual mientras tanto — `decidir.py` incluye F3 en
`FASES_EN_TESTEO`, así que ninguna orden de escalado sale de acá.

---

## FIN FASE 3

```
FASE 3 EN CURSO ✓ / GANADA ✓

□ Brief de etapa-11 vigente para el concepto ganador
□ Bloques de juicio reescritos por etapa-5, aplicados en LucidBot
□ CAMBIO_BOT (o EXCEPCION_CAMBIO_BOT) registrado en _EVENTOS.csv el mismo día
□ Cierre medido ≥30 mensajes desde el CAMBIO_BOT — ≥10% para pasar a FASE 4, si no: otra iteración
```
