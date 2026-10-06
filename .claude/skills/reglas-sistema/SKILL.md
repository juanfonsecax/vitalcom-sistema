---
name: reglas-sistema
description: "Constantes e invariantes del SISTEMA VITALCOM que aplican a toda etapa. Se precarga en los subagentes de etapa; no se invoca a mano."
---

# REGLAS DEL SISTEMA PARA TODA ETAPA

> GENERADO desde `CLAUDE.md` por `Ads/_TOOLS/gen_reglas_etapas.py`. No editar: se edita
> `CLAUDE.md` y se regenera con `--escribir`.

## CONSTANTES DEL SISTEMA

Aplican a **todos los subagentes en todas las fases**.

### DEFINICIONES CLAVE
- **ÁNGULO:** la causa específica o sub-problema que el producto resuelve (ej: acné por desequilibrio
  hormonal, por estrés, por salud intestinal). Territorio del PROBLEMA, no del formato.
- **FORMATO CREATIVO:** tipo de presentación (testimonio, educacional, prueba social, oferta). NO es
  el ángulo.
- **CONCEPTO:** cómo se muestra. Ortogonal al ángulo.
- **MICRO-ÁNGULO** (FASE 4): avatar ultra-específico dentro del ángulo ganador.

### ÁNGULO vs CONCEPTO — QUÉ SE FIJA EN CADA FASE
> **ÁNGULO = por qué duele. CONCEPTO = cómo se muestra.**
> ```
> FASE 1 → 6 ÁNGULOS distintos × concepto Y formato FIJOS (IMAGEN)   6 conjuntos · ABO ← mide el ÁNGULO
> FASE 2 → 1 ángulo ganador × 10 CONCEPTOS            1-1-5 ×2 + 1-2-5 · ABO ← mide el CONCEPTO
> FASE 3 → 1 ángulo + 1 concepto validados, mismo presupuesto · la variable es el flujo LucidBot
>          (CAMBIO_BOT) ← mide el CIERRE
> FASE 4 → 1 ángulo + 1 concepto validados × 7        1-1-7 · CBO            ← compra volumen
> ```
> - **El 1-1-5 va en FASE 2 y en ABO. Nunca en FASE 1 y nunca en CBO**: en CBO Meta corona un solo
>   anuncio y los demás no reciben entrega.
> - **El ángulo NO se testea en 1-1-N**: Meta reparte por clics y conversaciones, y esa señal no
>   predice la venta. **Presupuesto protegido (conjuntos separados) cuando la variable se decide por
>   VENTA · presupuesto libre (1-1-N) cuando se decide por ENTREGA.**
> - **FASE 1 corre TODO EN IMAGEN:** los videos de competencia
>   siguen siendo la FUENTE del ángulo (transcripciones de `etapa-0`), nunca el creativo de F1; el
>   formato VIDEO se testea recién en FASE 2, como un concepto más. Dueño de la regla:
>   `Ads/_TOOLS/gen_plan.py --validar` (bloquea un plan de F1 con cualquier conjunto != IMAGEN).

### TONALIDAD BASE
La persona del texto sale del **mercado del producto** (`persona` en `_DIM_MERCADOS.csv`): voseo
guatemalteco en GT, tuteo neutro en CO. Coloquial, nunca formal ni genérico. Nunca sonar a anuncio
de manual. **Colombia corre en modo manual**: el operador entrega los exports de Meta y LucidSales,
la cuenta es EXTERNA y no hay MCP (skill `recopilar-lucidsales`, sección «MERCADO CO (MANUAL)»).

### ALCANCE DEL COMPLIANCE
El compliance de verbos/claims y el CPM de Andrómeda aplican SOLO a los **ADS** (creativo + copy que
Meta lee). Todo lo **POST-CLIC** — flujo LucidBot, audio, infografías del bot, testimonios — Meta no
lo lee. **Dentro del bot la prioridad es CONVERSIÓN**: se permiten verbos persuasivos fuertes y las
estadísticas del operador; NO suavizar. Único límite post-clic: no afirmar que cura una enfermedad
grave nombrada. **ETAPA-5 y las infografías del flujo NO se suavizan por compliance.**

### SEGMENTACIÓN
La banda de edad se **deriva del `avatar_edad` del ángulo**, con Advantage+ Audience OFF, idéntica
entre réplicas del mismo ángulo. Amplio 18-65+ solo para ángulos sin avatar de edad marcada. Tabla
en `.claude/agents/ETAPA-6.md`. Si choca con la edad de la página, manda la del avatar.

---


## INVARIANTES DEL ORQUESTADOR

No se violan en ninguna fase. El código las cita por número: **no renumerar**. Su evidencia vive en
`_CONOCIMIENTO/MATRIZ_METODOLOGIA.md` y `_CONOCIMIENTO/POSTMORTEMS/`.

1. **El ganador se declara por VENTA, agregando por `angulo_key`** — nunca por conversación ni por
   conjunto-semana. La conversación sirve para CORTAR, nunca para CORONAR. No entrar a FASE 2 sin
   ángulo ganador; no entrar a FASE 3 sin concepto ganador en 2 de 2; no entrar a FASE 4 sin cierre
   ≥ `cierre_min_escalar_pct` medido después del `CAMBIO_BOT`.
2. **Nunca inventar cifras de costeo.** Salen de `Ads/_TOOLS/costear.py` sobre `PRODUCTOS/_DIM_COSTEO.csv`:
   fila más cercana al costo; en empate, la superior (conservador). Arquitectura de oferta en
   `.claude/agents/ETAPA-1.md`.
3. **Transferir siempre el output completo** de cada etapa a la siguiente — nunca resumir ni truncar.
4. **Si falta un input requerido: detener**, indicando qué dato falta y en qué formato. Nunca asumir
   ni inventar.
5. **Congelar los inputs antes de arrancar.** Si uno cambia a mitad → rerun completo que
   **sobrescribe** los archivos y sube `VERSION`; nunca un parche parcial.
6. **Mismo presupuesto en todos los conjuntos dentro de cada etapa.** Cifras en
   `DOCTRINA/CALENDARIO_ESCALADO.md` §1.5 y §1.7.
7. **Lanzamiento siempre al día siguiente, a la hora que fija `PRODUCTOS/_PARAMETROS_PUBLICACION.csv`
   (`hora_lanzamiento`, hoy 4 AM).** Nunca el mismo día.
8. **Un producto = una carpeta `PRODUCTOS/[NOMBRE]/` con archivos por rol** — `1_HACER_MANUAL.txt`,
   `2_DATA_PRODUCTO.txt`, `3_CAMPAÑA_META.txt` (solo IDs de Meta), `4_PLAN_ESCALADO.txt`. Prohibidos
   archivos sueltos de reruns. La media va a `Ads/MEDIA_[PRODUCTO]/`; todo informe fechado a
   `PRODUCTOS/_AUDITORIAS/`. Todo producto con paquete completo lleva su fila en
   `_DIM_PRODUCTOS.csv`, aunque no esté lanzado.
9. **Gate de reconciliación antes de cerrar.** No declarar un producto completo hasta verificar que
   costo, precio, dosis, proveedores, página y `campaign_id` coinciden entre archivos.
10. **`producto_key` es la llave del sistema.** Las carpetas se resuelven leyendo
    `_DIM_PRODUCTOS.csv` — nunca adivinar la carpeta por el nombre.
11. **Los CSV se editan con un escritor CSV real, nunca a mano.** Campos de texto con comas van
    entre comillas dobles.
12. **Todo objeto de Meta se nombra con la CONVENCIÓN DE NOMBRES de `ETAPA-6.md`**, por MCP o a mano.
    Prohibido publicar un `- Copia`: se renombra a `R[N]` antes. Las réplicas `R[N]` se SUMAN, nunca
    se comparan.
13. **Ninguna orden de pausar o escalar se emite sin pasar por `decidir.py`.**
    - El motor calcula el IC 95% del CPA. **El intervalo manda en las dos direcciones**: si cruza el
      break-even no se apaga ni se sube presupuesto; se emite `SEGUIR_MIDIENDO` (mantener) con las
      ventas que faltan.
    - Estados: `ESCALAR` · `PAUSAR` · `RENOVAR` · `SEGUIR_MIDIENDO`. Un ángulo con historia rentable
      no se APAGA por una mala racha: se RENUEVA el concepto.
    - Tres relojes distintos, nunca uno: `ventana_dias` (CPA e IC) · `ventana_fatiga_dias` (reciente
      contra ventana) · `duracion_testeo_fase2_dias` (cuánto rueda la 1-1-5). La tolerancia 1× BE se
      mide sobre el gasto ACUMULADO desde el lanzamiento. Lo que fija un mentor en días es volumen
      de evidencia, no tiempo.
    - Las ventanas viven en `PRODUCTOS/_PARAMETROS_DECISION.csv` y se cuentan desde el **último día
      CON DATA**; si esa data supera `rezago_max_dias` (o su edad es desconocida), `gen_ordenes.py`
      no emite ninguna orden de ESCALAR (bloqueante); PAUSAR sí sale, con aviso.
    - **Nunca se sube presupuesto sobre una base inventada**: sin `daily_budget` real en el
      snapshot de Meta, la orden de ESCALAR se bloquea.
    - **Ejecutar una orden en Meta por MCP requiere la confirmación explícita del operador, orden por
      orden.** Después se verifica contra Meta y se anexa el evento a `_EVENTOS.csv`.

### Dos punteros que valen por una regla

- **El CIERRE es la palanca más grande del sistema.** Su dueño es `etapa-11`. El DIAGNÓSTICO y la
  REESCRITURA no corren juntos: `etapa-11` diagnostica el cierre y la congruencia anuncio↔bot en
  **FASE 2** (nodo `F2.etapa-11`, registra `DIAGNOSTICO_CONGRUENCIA`, no bloquea el testeo de
  conceptos) y entrega el brief priorizado. La REESCRITURA es **FASE 3** (nodo `F3.reescribir`):
  `etapa-5` redacta los BLOQUES DE JUICIO del flujo a partir de ese brief, el operador aplica y
  anexa `CAMBIO_BOT` (o `EXCEPCION_CAMBIO_BOT` si decide saltárselo) — nunca uno viejo, siempre
  fechado DESPUÉS del concepto ganador. El gate que compra volumen es `F4.entrada` de
  `DOCTRINA/FLUJO.json`: exige ese `CAMBIO_BOT`/`EXCEPCION_CAMBIO_BOT` MÁS el cierre medido después
  de él por encima de `cierre_min_escalar_pct` (≥30 mensajes). Por debajo del umbral, el producto se
  queda en FASE 3 para otra iteración del flujo — nunca sube presupuesto. Reglas A-G del orden en
  `DOCTRINA/PLANTILLAS_FLUJO_BOT.md`. Ante un cierre desplomado, verificar PRIMERO la consistencia
  física ad ↔ destino.
- **El dinero se mide con `DOCTRINA/CONTABILIDAD.md`**, que manda sobre cualquier otro cálculo. Negocio
  CONTRA ENTREGA: cohorte ≠ caja; un cohorte de menos de 10 días es PRELIMINAR; el `MARGEN LOGÍSTICO`
  de Dropi NO es la ganancia.
