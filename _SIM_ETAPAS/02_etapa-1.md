# SALIDA COMPLETA — etapa-1 · TURMERIC · v1 · 2026-09-11 (SIMULACIÓN)

Cifras de `costear.py 60 --json` (exit 0) y `--unidades 4`, fuente `_DIM_COSTEO.csv` (origen_escalera OPERADOR).

DATOS BASE: costo Q60 por unidad (no combo) · fila de tabla Q60 (exacta) · sin fila en _DIM_PRECIOS (no vende todavía) → manda _DIM_COSTEO vía costear.py.

PRECIOS: P1u Q199 + ENVÍO GRATIS · P2u Q299 + ENVÍO GRATIS ← OFERTA IRRESISTIBLE · P3u Q399 + ENVÍO GRATIS + regalo ← "la más elegida ⭐" · (P4u Q499 solo referencia de upsell; probablemente extrapolado ×1.7, confirmar).

ARQUITECTURA DE OFERTA: 1/2/3 unidades.
- Piso por pedido: P1u mínimo Q181.43; Q199 lo supera por Q17.57.
- Regla de arranque (Paso 2.5): múltiplo necesario 3.02× → franja costo ≥Q60 → decisión "1U" (1 unidad viable, 2u/3u/4u como upsell).
- Consumo continuo → vender tratamiento 1/2/3, no 2x1/4x2.
- Si el avatar resulta nivel 1-2 con dolor fuerte, empujar 2-3u con regalo y garantía escalonada, sin inflar P1u.

UMBRALES: CPA Objetivo Q28.51 · CPA Base Q30.8 · CPA Break Even Q69.56 · envío Q43.37 · utilidad esperada Q38.76.
MARGEN (fórmula de formato, sin envío ni devoluciones): P1u Q110.49 · P2u Q150.49 · P3u Q190.49.

HALLAZGOS:
1. costear.py NO tiene modo de escritura; ninguna herramienta escribe fila_costeo_q/precio_base_q/cpa_base_q/cpa_be_q en _DIM_PRODUCTOS.csv. El gate F1.paquete de FLUJO.json exige cpa_be_q y nombra a costear.py como dueño → para un producto nuevo el gate no se cierra con herramientas del sistema. Valores a escribir: fila_costeo_q=60, precio_base_q=199, cpa_base_q=30.8, cpa_be_q=69.56. Arreglo sugerido: costear.py --escribir PRODUCTO_KEY con csv.DictWriter.
2. Tasa: inputs 7.62; parámetros de _DIM_COSTEO usan 7.64 (desfase chico al convertir USD→Q).
3. Q499 de 4u marcado OPERADOR aunque la tabla de ETAPA-1 solo llega a P3u: confirmar antes de publicar.
4. Con dosis 1 ml/día un frasco rinde ~60 días: 3u ≈ 6 meses; ETAPA-5 debería presentar ciclos de 90-180 días.
