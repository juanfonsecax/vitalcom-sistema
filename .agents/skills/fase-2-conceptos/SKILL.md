---
name: fase-2-conceptos
description: "FASE 2 — Testeo de CONCEPTOS. Con el ángulo ganador ya confirmado POR VENTA, orquesta la secuencia que fija ángulo y copy y mueve solo el creativo: optimizar el flujo del bot, fabricar los 10 conceptos, escribir el copy único y los dos flujos del A/B, y planificar las 3 campañas (1-1-5 + 1-1-5 + 1-2-5). Úsala cuando flujo.py sitúa al producto en un nodo F2.*, o cuando el operador dice \"ya sé qué ángulo vende\", \"testear conceptos\", \"qué creativo lo vende más barato\" o \"tengo el ángulo ganador\"."
tools: Read, Write, Glob, Grep, Bash, Task
---

# FASE 2 — TESTEO DE CONCEPTOS

**Mueve el CREATIVO. Ángulo y copy quedan fijos.**

```
1 ángulo (el ganador) × 10 CONCEPTOS distintos        ← mide el CONCEPTO
```

- Estructura `1-1-5 + 1-1-5 + 1-2-5`; presupuesto por conjunto de `PRODUCTOS/_PARAMETROS_PUBLICACION.csv`
  (hoy $6, $24/día en total). El `%PD` se lee **por concepto sumando sus 2 apariciones**, nunca por conjunto.
- Los 10 son ejecuciones de los conceptos de `Ads/_SWIPE/_CATALOGO_CONCEPTOS.md`. El `concepto_key` de
  cada anuncio se registra en **`_DIM_CREATIVOS.csv`**.
- El video se testea acá, como un concepto más. Un concepto en VIDEO se lava antes de quedar
  `GENERADO`: `bash "Ads/_TOOLS/lavar_videos.sh" "[PRODUCTO]" [OFERTA] [COLOR] "Ads/MEDIA_[PRODUCTO]" [MANIFEST]`
  (detalle en `Ads/_TOOLS/LAVADO.md`). Los conceptos en IMAGEN van por `etapa-render`.

**Secuencia:** `etapa-11` → `etapa-9` (10 conceptos) → [lavado si algún concepto es VIDEO] →
(`etapa-4` ∥ `etapa-5`) → `etapa-6` → `etapa-guardar-producto`

`etapa-3` **no corre en esta fase**: sus microángulos son el banco de copy de FASE 4. En FASE 2 el
copy es uno solo y fijo para los 10 anuncios.

---

## Entrada — el flujo dicta

`python Ads/_TOOLS/flujo.py [producto_key]` decide si el producto está en FASE 2 (gate: **ángulo
ganador por VENTA**, agregando por `angulo_key`) y en qué nodo va: `F2.etapa-11` → `F2.conceptos`
(≥10 `GENERADO`) → `F2.plan` → `F2.publicar` (los `ad_id` escritos) → `F2.activar`. Lo que cierra
cada nodo está en `DOCTRINA/FLUJO.json`. Criterio del operador al planificar: una **segunda cuenta**
con MCP para la campaña C y **ningún otro producto en FASE 2 esa semana**.

---

## PASO 1 — `etapa-11` (optimizador de flujo) — corre PRIMERO

Optimizar el cierre es la palanca más grande y va antes de gastar más.

Inputs: `producto_key`, el `angulo_key` ganador con su ficha, la ventana de testeo, el export de
chats de LucidBot (si lo hay) y el texto real del flujo. Output: diagnóstico del CIERRE por ángulo +
**brief priorizado para `etapa-5`** + diseño del **A/B de flujo** (brazo A paraguas optimizado ∥
brazo B dedicado, ruteo por Post ID) + los comandos `registrar_evento.py` listos para correr.

## PASO 2 — `etapa-9` (fábrica de conceptos)

Inputs: ángulo ganador, imagen del producto, data del producto y `_APRENDIZAJES.csv` de creativos.
Output: **10 ejecuciones** (prompt de imagen resuelto + fila en `_DIM_CREATIVOS.csv` con
`concepto_key`, `variante`, `rol_embudo`, `id_tanda`, `brazo`), balanceadas por rol de embudo.

## PASO 3 — `etapa-4` ∥ `etapa-5` (en paralelo)

- **`etapa-4`** — Inputs: ángulo ganador con su ficha, producto, P1u, `<pagina_asignada>`. Output:
  **el copy único** de la fase + 3 variaciones de respaldo. No 6 copies distintos.
- **`etapa-5`** — Inputs: ángulo ganador (con nivel de conciencia), producto, `producto_key`,
  `<pagina_asignada>` y **el brief de `etapa-11`** (mercado, transportadoras y precios salen de los
  CSV, no se pasan a mano). Output: **los dos brazos del A/B**: A = el paraguas vigente con el brief
  aplicado; B = las frases del ángulo ganador en `_DIM_FLUJO_BOT.csv` + sus bloques de juicio.
  El brief entra por las propuestas de valor primero, después fricción, congruencia anuncio ↔ bot,
  oferta y FAQ.

  Cerrar con `python Ads/_TOOLS/gen_flujo_bot.py [producto_key]` y, el día que se aplica, registrar:

  ```bash
  python Ads/_TOOLS/registrar_evento.py --producto [producto_key] --evento CAMBIO_BOT --motivo "[qué cambió]" --fuente "etapa-5 [fecha]"
  ```

  Nunca a mano en `_EVENTOS.csv`. Este `CAMBIO_BOT` es el del A/B de esta fase, **no** el que exige
  `F4.entrada`: la reescritura final hacia el ganador es FASE 3 (skill `fase-3-flujo`), con su propio
  `CAMBIO_BOT` posterior al concepto ganador.

## PASO 4 — `etapa-6` (plan de conceptos)

Inputs: ángulo ganador, copy único, los 10 conceptos, cuenta principal + cuenta réplica,
`avatar_edad`, output de `etapa-1`. Output: **3 campañas**: `1-1-5` (A, conceptos 1-5) + `1-1-5`
(B, conceptos 6-10) + `1-2-5` (C, los mismos 10 en OTRA cuenta), 4 AM del día siguiente. **5
anuncios por conjunto**, uno por concepto, con ángulo y copy fijos.

Un anuncio con gasto acumulado menor a 30 % de su reparto prorrateado es **`SIN_ENTREGA`**, nunca
perdedor: se relanza en la próxima tanda.

## PASO 5 — `etapa-guardar-producto`

Al final de FASE 2, actualiza los archivos del producto con el ángulo ganador y los resultados.

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
