---
name: fase-2-conceptos
description: FASE 2 — Testeo de CONCEPTOS. Con el ángulo ganador ya confirmado POR VENTA, orquesta la secuencia que fija ángulo y copy y mueve solo el creativo: optimizar el flujo del bot, fabricar los 10 conceptos, escribir el copy único y los dos flujos del A/B, y planificar las 3 campañas (1-1-5 + 1-1-5 + 1-2-5). Úsala cuando el operador responde "2" a la pregunta inicial, o dice "ya sé qué ángulo vende", "testear conceptos", "qué creativo lo vende más barato" o "tengo el ángulo ganador".
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
`CALENDARIO_ESCALADO.md` §1.7.

Catálogo de los 8 conceptos y su evidencia: `Ads/_SWIPE/_CATALOGO_CONCEPTOS.md`. Se registra en
`concepto_key` de `_DIM_CONJUNTOS.csv` (vocabulario en `DATA_PLAYBOOK.md` §1).

**Secuencia:** `etapa-11` → `etapa-9` (10 conceptos) →
(`etapa-4` ∥ `etapa-5`) → `etapa-6` → `etapa-guardar-producto`

---

## Verificación obligatoria antes de iniciar

- [ ] Ángulo ganador confirmado **por VENTA**, agregado por `angulo_key` (nunca por conversación ni
      por conjunto-semana)
- [ ] Métricas del testeo: CTR, CPA real, mensajes y conversiones por cada uno de los 6 conjuntos
- [ ] **10 conceptos listos y publicables** (los produce `etapa-9`). Con menos de 10 no se arranca
- [ ] Una **segunda cuenta publicitaria** disponible para la campaña C
- [ ] Ningún otro producto corriendo FASE 2 esa semana (techo Q597/día)
- [ ] **`etapa-11` corrió** y su brief está aplicado en los dos flujos del A/B (brazo A optimizado +
      brazo B dedicado), con el **ruteo por Post ID verificado** con una conversación de prueba por brazo

Si falta cualquiera → escribir:

```
No puedo iniciar FASE 2 sin el ángulo ganador confirmado y las métricas del testeo.
Por favor comparte:
1. ¿Cuál ángulo ganó? (angulo_key, confirmado por ventas)
2. Métricas del testeo por conjunto: CTR / CPA real / mensajes / conversiones
3. ¿Están los 10 conceptos generados y subidos? (si no → corre `etapa-9` primero)
```

---

## PASO 0 — `etapa-11` (optimizador de flujo) — CORRE PRIMERO

Inputs: `producto_key`, el `angulo_key` ganador con su ficha, la ventana de testeo, el export
semanal de chats de LucidBot (si lo hay) y `1_HACER_MANUAL.txt` con el texto real del flujo.

Output: diagnóstico del CIERRE por ángulo + **brief priorizado para `etapa-5`** + **diseño del A/B
de flujo** (brazo A paraguas optimizado ∥ brazo B dedicado, ruteo por Post ID) + las filas para
`_EVENTOS.csv`.

> **Por qué va primero y no después:** optimizar el flujo es la palanca #1 de
> `ESCALADO_PLAYBOOK.md` §3 y va **antes de gastar más**. El cierre del portafolio está en 8.6 %
> contra el 15-20 % de los mentores; a mensajes y gasto idénticos, el 15 % son **+324 ventas y CPA
> de Q51.5 a Q29.6**. Ninguna palanca de estructura se acerca. Su brief entra a `etapa-5` en el
> PASO 2, que redacta **los dos flujos** del A/B.

---

> ⚠️ **`etapa-3` NO corre en esta fase.** Los microángulos que produce ya no arman conjuntos: son el
> banco de copy de la FASE 3. Corrían acá por herencia del diseño anterior al 2026-09-02, gastando
> dos invocaciones en el camino crítico para alimentar algo que esta fase no consume. En FASE 2 el
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
  P1u/P2u/P3u, `<costo_envio_cliente>` = Q0, `<pagina_asignada>` y **el brief de `etapa-11`**. País
  Guatemala, transportadoras GINTACOM/FORZA. Output: **los DOS flujos del A/B** — brazo A = el
  paraguas vigente con los cambios del brief aplicados; brazo B = flujo LucidBot de un solo ángulo
  (13 elementos) + texto fijo de M2 y GUION DEL AUDIO TESTIMONIO (voz del avatar ganador), mensaje
  inicial = dolor exacto del ganador.

  > `etapa-5` sigue siendo el **dueño único del texto del flujo**. `etapa-11` diagnostica y
  > prioriza; `etapa-5` redacta. Misma división que `etapa-10` → `etapa-9`.

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
□ Filas de los 10 conceptos en _DIM_CREATIVOS.csv con estado PUBLICADO

□ A/B DE FLUJO corriendo: brazo A (paraguas optimizado) ∥ brazo B (dedicado al ganador)
□ Ruteo por Post ID verificado con una conversación de prueba POR BRAZO
□ CAMBIO_BOT (brazo A) y LANZAMIENTO (brazo B) anexados a _EVENTOS.csv con fecha
□ Fecha de lectura del A/B anotada (n mínimo por brazo — tabla en ETAPA-11.md PASO 6)

Ciclo de optimización (ACTIVO):
□ ETAPA-7 → auditoría de métricas
□ ETAPA-8 → decisión de creativos y escalado
□ ETAPA-10 → lectura concepto ↔ métrica (por qué ganó lo que ganó)
□ ETAPA-11 → optimización de flujo (por qué, habiendo escrito, no compran)

⚠️ NO pasar a FASE 3 sin un concepto que gane en 2 de 2. Un ganador de 1 de 2 es ruido.
```
