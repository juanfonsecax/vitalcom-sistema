# Historias de GUIA_MADRE_PARAMETRIZADA.md

Consulta humana. La regla vigente vive en `DOCTRINA/GUIA_MADRE_PARAMETRIZADA.md`; acá vive el
incidente que la produjo, por sección de la Guía.

## §10 — VARIABLES DE TIEMPO Y VENTANAS OPERATIVAS

**`VENTANA_EVALUACION_DIAS` (07-sep-2026).** Con la ventana de evaluación puesta en 3 días (copiando
la duración del testeo de Calet en vez de su volumen de evidencia), el motor ordenó apagar un ángulo
que llevaba 38 ventas rentables acumuladas. La ventana de 3 días no le daba suficiente historia para
verlo. Regla que dejó: `VENTANA_EVALUACION_DIAS` = 14 días, separada de `DURACION_TESTEO_FASE2_DIAS`
(3 días, la de Calet).

**`VENTANA_FATIGA_DIAS` (07-sep-2026, mismo día).** Con `VENTANA_FATIGA_DIAS` igual a
`VENTANA_EVALUACION_DIAS` (ambas en 3), el detector de fatiga comparaba la celda consigo misma y
`RENOVAR` no se emitía nunca. Regla que dejó: `VENTANA_FATIGA_DIAS` debe ser estrictamente menor que
`VENTANA_EVALUACION_DIAS`; el gate de coherencia de `verificar_guia_madre.py` lo congela.

## §11 — VARIABLES DE RIESGO Y TOLERANCIA (BANKROLL)

**`UMBRAL_CONVERSACION_CLIC_ENLACE` (hasta 09-sep-2026).** El umbral de 35% para matar por
conversación vivía solo en prosa (ETAPA-8, `ESCALADO_PLAYBOOK.md` §1.5/§8) y el motor (`decidir.py`)
no lo conocía: una celda con clics pero sin chats podía seguir gastando hasta su Presupuesto de
Decisión completo antes de que algo la cortara. Regla que dejó: el umbral pasó a
`_PARAMETROS_DECISION.csv` y `decidir.py` lo aplica directamente, sin esperar el PD.

**`MARGEN_EMPATE_CPA` (simulación TURMERIC, 15-sep-2026).** Antes de fijar un margen de empate, una
simulación mostró que el gate de FASE 3 oscilaba día a día con datos casi idénticos: 25-sep ✗ ·
26-sep ✓ (dos conceptos empatados EXACTO en 1.75, desempatados por orden alfabético) · 27-sep ✗ por
apenas Q0.04 (1.7 %) · 28-sep ✓. El producto entraba y salía de FASE 3 según quién hubiera corrido la
sesión ese día. Regla que dejó: un margen de empate del 10% cuenta a ambos conceptos como ganadores
cuando su CPA difiere menos que eso; no se usa el intervalo de credibilidad para esto porque con 2
ventas por concepto el IC de cada uno es tan ancho que todos se solapan.

## §14 — VARIABLES DE OPTIMIZACIÓN CONTINUA (CICLO DE VIDA DEL ÁNGULO)

**`DIAS_SIN_GASTO_DORMIDO` (caso VARICOSE, 03-sep-2026).** VARICOSE pasó 21 días seguidos en estado
`VIVO` sin gastar un centavo, y el perfil seguía proponiendo reactivarlo todos los días usando su CPA
viejo (que ya no describía nada, porque el ángulo no estaba corriendo). Regla que dejó: un ángulo sin
gasto por 3 días pasa a `DORMIDO` y deja de contaminar el ranking con un CPA que no es de hoy.
