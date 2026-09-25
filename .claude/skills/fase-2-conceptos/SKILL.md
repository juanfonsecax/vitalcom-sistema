---
name: fase-2-conceptos
description: "FASE 2 — Testeo de CONCEPTOS. Con el ángulo ganador ya confirmado POR VENTA, orquesta la secuencia que fija ángulo y copy y mueve solo el creativo: optimizar el flujo del bot, fabricar los 10 conceptos, escribir el copy único y los dos flujos del A/B, y planificar las 3 campañas (1-1-5 + 1-1-5 + 1-2-5). Úsala cuando flujo.py sitúa al producto en un nodo F2.*, o cuando el operador dice \"ya sé qué ángulo vende\", \"testear conceptos\", \"qué creativo lo vende más barato\" o \"tengo el ángulo ganador\"."
tools: Read, Write, Glob, Grep, Bash, Task
---

# FASE 2 — TESTEO DE CONCEPTOS

## Qué mide esta fase

**Mueve el CREATIVO. Ángulo y copy quedan fijos.**

```
1 ángulo (el ganador) × 10 CONCEPTOS distintos        ← mide el CONCEPTO
```

Estructura `1-1-5 + 1-1-5 + 1-2-5` a **$6/conjunto = $24/día**. El `%PD` se calcula **por concepto
sumando sus 2 apariciones** (~4.1 días a 1× BE), nunca por conjunto. Aritmética completa en
`DOCTRINA/CALENDARIO_ESCALADO.md` §1.7.

Catálogo de los 8 conceptos y su evidencia: `Ads/_SWIPE/_CATALOGO_CONCEPTOS.md`. Se registra en
`concepto_key` de `_DIM_CONJUNTOS.csv` (vocabulario en `DOCTRINA/DATA_PLAYBOOK.md` §1).

**Secuencia:** `etapa-11` → `etapa-9` (10 conceptos) → [lavado si algún concepto es VIDEO] →
(`etapa-4` ∥ `etapa-5`) → `etapa-6` → `etapa-guardar-producto`

> **El video pasa a testearse ACÁ, como un concepto más**
> entre los 10 — ya no es el creativo de FASE 1. Cuando `etapa-9` asigna un concepto en formato
> VIDEO, se lava antes de dejarlo `GENERADO`: `bash "Ads/_TOOLS/lavar_videos.sh" "[PRODUCTO]"
> [OFERTA] [COLOR] "Ads/MEDIA_[PRODUCTO]" [MANIFEST]` (detalle técnico y mapa de colores en
> `Ads/_TOOLS/LAVADO.md`). Los conceptos en IMAGEN siguen el camino normal de `etapa-render`.

---

## EL FLUJO DICTA

`python Ads/_TOOLS/flujo.py [producto_key]` decide si el producto está en FASE 2 (gate de entrada:
ángulo ganador **por VENTA** agregando por `angulo_key`) y en qué nodo va: `F2.etapa-11` →
`F2.conceptos` (≥10 `GENERADO`, R3F-13) → `F2.plan` (contrato `plan/1`) → `F2.publicar` (los
`ad_id` escritos) → `F2.activar`. Lo que cierra cada nodo está en `DOCTRINA/FLUJO.json`; acá no se
repite ni se reinterpreta. Sigue siendo criterio del operador al planificar: una **segunda cuenta**
con MCP para la campaña C y **ningún otro producto en FASE 2 esa semana** (techo Q597/día).

---

## PASO 0 — `etapa-11` (optimizador de flujo) — CORRE PRIMERO

Inputs: `producto_key`, el `angulo_key` ganador con su ficha, la ventana de testeo, el export
semanal de chats de LucidBot (si lo hay) y `1_HACER_MANUAL.txt` con el texto real del flujo.

Output: diagnóstico del CIERRE por ángulo + **brief priorizado para `etapa-5`** + **diseño del A/B
de flujo** (brazo A paraguas optimizado ∥ brazo B dedicado, ruteo por Post ID) + las filas para
`_EVENTOS.csv`.

> **Por qué va primero y no después:** optimizar el flujo es la palanca #1 de
> `DOCTRINA/ESCALADO/04_PALANCAS.md` §3 y va **antes de gastar más**. El cierre del portafolio está en 8.6 %
> contra el 15-20 % de los mentores; a mensajes y gasto idénticos, el 15 % son **+324 ventas y CPA
> de Q51.5 a Q29.6**. Ninguna palanca de estructura se acerca. Su brief entra a `etapa-5` en el
> PASO 2, que redacta **los dos flujos** del A/B.

---

> ⚠️ **`etapa-3` NO corre en esta fase.** Los microángulos que produce ya no arman conjuntos: son el
> banco de copy de la FASE 3. En FASE 2 el
> copy es **uno solo y fijo** para los 10 anuncios — es la constante de control.

---

## PASO 1 — `etapa-9` (fábrica de conceptos)

Inputs: ángulo ganador, imagen del producto, data del producto, `_APRENDIZAJES.csv` de creativos.
Output: **10 ejecuciones** (prompt de imagen resuelto + fila en `_DIM_CREATIVOS.csv` con
`concepto_key`, `variante`, `rol_embudo`, `id_tanda`, `brazo`), balanceadas por rol de embudo.

---

## PASO 2 — `etapa-4` ∥ `etapa-5` (PARALELO)

- **`etapa-4` (FASE 2)** — Inputs: ángulo ganador con su ficha de `etapa-2`, producto, P1u,
  `<pagina_asignada>`. Output: **el copy único** de la fase (texto/título/descripción) + sus 3
  variaciones de respaldo. **No** 6 copies distintos: el copy es constante de control.
- **`etapa-5` (FASE 2)** — Inputs: ángulo ganador (con nivel de conciencia), producto,
  `producto_key`, `<pagina_asignada>` y **el brief de `etapa-11`**. El mercado, las transportadoras
  y los precios **no se pasan a mano**: salen de `_DIM_MERCADOS.csv` y `_DIM_PRECIOS.csv`.
  Output: **los DOS brazos del A/B** — brazo A = el paraguas vigente con los cambios del brief
  aplicados; brazo B = las frases del ángulo ganador en `_DIM_FLUJO_BOT.csv` + sus bloques de
  juicio (testimonios, audio, M2 con su guión de audio testimonio, FAQ).

  > **El texto fijo es de `DOCTRINA/PLANTILLAS_FLUJO_BOT.md`; `etapa-5` escribe el JUICIO.**
  > `etapa-11` diagnostica y prioriza; `etapa-5` redacta. Misma división que `etapa-10` → `etapa-9`.
  > El brief entra por las **propuestas de valor primero** (es la palanca #1 del cierre),
  > después fricción, congruencia ad ↔ bot, oferta y FAQ nuevas.
  > Cerrar con `python Ads/_TOOLS/gen_flujo_bot.py [producto_key]` y anexar `CAMBIO_BOT` a
  > `_EVENTOS.csv` el día que se aplica: el efecto se nota en horas.
  >
  > **Este `CAMBIO_BOT` es el del A/B de flujo de esta fase, NO el que exige `F3.entrada`.**
  > El gate de FASE 3 pide un `CAMBIO_BOT` fechado DESPUÉS del
  > concepto ganador en 2 de 2 — la reescritura final hacia ese ganador, que corre cuando termina
  > esta fase, no al arrancarla. Ver `fase-3-escalado/SKILL.md` y `F3.entrada` en
  > `DOCTRINA/FLUJO.json`.

---

## PASO 3 — `etapa-6` (FASE 2 — planificador de conceptos)

Inputs: ángulo ganador, copy único de `etapa-4`, los 10 conceptos de `etapa-9`, cuenta principal +
cuenta réplica, `avatar_edad`, output de `etapa-1`.

Output: **3 campañas** — `1-1-5` (A, conceptos 1-5) + `1-1-5` (B, conceptos 6-10) + `1-2-5` (C, los
mismos 10 en OTRA cuenta), $6/conjunto = **$24/día**, 4 AM día siguiente.

**5 anuncios por conjunto**, uno por concepto, con ángulo y copy fijos.

> **Guardarraíl del 1-1-N:** un anuncio con gasto acumulado < 30 % de su reparto prorrateado se
> marca **`SIN_ENTREGA`**, nunca `PERDEDOR`, y se relanza en la próxima tanda.

---

## PASO 4 — `etapa-guardar-producto`

Correr también al final de FASE 2 para actualizar con el ángulo ganador y los resultados.

---

## FIN FASE 2

```
FASE 2 COMPLETADA ✓

□ Flujo LucidBot (ETAPA-5) → copiar campo por campo en LucidBot
□ 3 campañas de conceptos (ETAPA-6) → crear en Meta Ads para 4 AM mañana
□ 10 creativos subidos y numerados IGUAL en A/B y en C
□ Copy único cargado idéntico en los 10 anuncios
□ Banda de edad = avatar del ángulo · Advantage+ OFF · idéntica en las 3 campañas
□ Filas de los 10 conceptos en _DIM_CREATIVOS.csv con ad_id (lo escribe verificar_publicacion.py --escribir)

□ A/B DE FLUJO corriendo: dos conjuntos GEMELOS del ganador — A → paraguas optimizado ∥ B → dedicado
□ Ruteo por Post ID verificado con una conversación de prueba POR BRAZO
□ CAMBIO_BOT (paraguas) + LANZAMIENTO de cada gemelo anexados a _EVENTOS.csv · test_id en _TESTEOS.csv
□ Fecha de lectura del A/B anotada (n por brazo con Ads/_TOOLS/ab_flujo.py y el cierre REAL del ganador)

Ciclo de optimización (ACTIVO):
□ ETAPA-7 → auditoría de métricas + decisión de creativos y escalado (fusionadas)
□ ETAPA-10 → lectura concepto ↔ métrica (por qué ganó lo que ganó)
□ ETAPA-11 → optimización de flujo (por qué, habiendo escrito, no compran)

⚠️ NO pasar a FASE 3 sin un concepto que gane en 2 de 2. Un ganador de 1 de 2 es ruido.
```
