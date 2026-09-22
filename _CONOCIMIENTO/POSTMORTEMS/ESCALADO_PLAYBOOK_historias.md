# Historias de ESCALADO_PLAYBOOK.md

Consulta humana. La regla vigente vive en `DOCTRINA/ESCALADO_PLAYBOOK.md`; acá vive el incidente que
la produjo, por sección del playbook.

## §1.5 — PRESUPUESTO DE DECISIÓN

**VARICOSE, dos correcciones de Break-Even.** Este archivo decía primero BE ≈ Q159 (el MARGEN BRUTO
del 2x1 sin descontar envío ni RTO), y después Q79 (una derivación a mano que tampoco cerraba). Con
la tabla de costeo v2 el valor correcto resultó Q83.0: VARICOSE vende 2x1, así que se costea por el
PEDIDO (2 frascos de Q45 = Q90 de producto), no por la unidad (Q45) — le toca la fila Q90 de la tabla
de costeo. Regla que dejó: los productos en combo se costean por el pedido completo, nunca por la
unidad suelta.

**Por qué el presupuesto subió de $1.59 a $2.99.** A $1.59/día el gate del día 3 llegaba con apenas
46-60% del Presupuesto de Decisión — decidir ahí era tirar una moneda — y la campaña ni siquiera
salía de aprendizaje en Meta (23 conversaciones en 7 días contra las 50 que pide el algoritmo). A
$2.99/día el gate del día 3-5 vuelve a ser válido. Regla que dejó: el presupuesto de testeo se
recalibra contra el costo por conversación real del producto (ver fórmula vigente en
`DOCTRINA/CALENDARIO_ESCALADO.md` §1.5), no se fija a ojo.

## §5 — SATURACIÓN POR CUENTA

**El caso TINNIDROP, 2026-07-24.** El video "DETERIORO COGNITIVO" dio CPA Q20.7 en las 3 cuentas
réplica y Q82 en la cuenta madre GTR0 — mismo video, mismo ángulo, mismo copy, misma página. La
cuenta madre estaba saturada por frecuencia acumulada; las cuentas frescas lo convertían 4× mejor.
Leído agregado, el ángulo parecía mediocre; leído cuenta por cuenta, era el mejor activo del
producto. Regla que dejó: nunca leer el rendimiento de un ángulo agregado entre cuentas — siempre
matriz ángulo × cuenta, con la clasificación VIAJA / LOCAL / MURIENDO.

## §7 — ENTREGABLE FIJO DE FASE 3

**Diagnóstico del operador, 24-jul-2026:** "FASE 1 está bien, pero FASE 2 y 3 se sienten perdidas."
La causa real no era falta de doctrina — era que el escalado no tenía archivo ni plantilla fija, así
que cada plan salía distinto. FASE 1 ya tenía 9 agentes con output de formato fijo; el escalado
entregaba prosa libre. Regla que dejó: `4_PLAN_ESCALADO.txt` con plantilla obligatoria, que se
sobrescribe en cada ciclo.

**Bug real en TINNIDROP (24-jul-2026):** el plan de escalado se guardó en el slot `3_`, que es
exclusivo para IDs de Meta (`3_CAMPAÑA_META.txt`), y terminó como `3_PLAN_ESCALADO.txt`. Regla que
dejó: el slot `3_` es solo para IDs de Meta; el plan de escalado va siempre en `4_`.
