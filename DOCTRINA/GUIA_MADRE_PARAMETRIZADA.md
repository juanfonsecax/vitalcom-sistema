# GUÍA MADRE PARAMETRIZADA — DICCIONARIO DE VARIABLES Y METODOLOGÍA
# SISTEMA VITALCOM GUATEMALA

> **PROPÓSITO DE ESTE DOCUMENTO:**
> Este es el **TEXTO MADRE** del sistema. Cada regla, estructura, presupuesto, ventana de tiempo y umbral enseñado en las clases de los mentores vive acá **como una variable parametrizada**.
>
> **REGLA DE ORO DE INGESTA:**
> Cuando se reciba una **NUEVA CLASE**, la IA no reescribe el sistema a ciegas:
> 1. Lee la nueva clase.
> 2. Compara contra las variables de este documento.
> 3. Identifica qué variables cambian, cuáles se mantienen y cuáles nacen.
> 4. Actualiza este documento con la nueva fecha y fuente.
> 5. Propaga el cambio a los archivos ejecutores (`_PARAMETROS_DECISION.csv`, `decidir.py`, `ETAPA-6.md`, etc.).

---

## 0. JERARQUÍA DE FUENTES Y REGLA DE RECENCIA

Cuando dos clases dicen cosas distintas, se aplica esta jerarquía estricta:

```
NIVEL 4 │ DATA PROPIA (_FACT_VENTAS, _APRENDIZAJES con muestra n suficiente) -> Manda sobre todo
NIVEL 3 │ Clase 2026-08-22 (Calet — Escalado 1-1-7 CBO, Ventas, Surfing Intradía)  <- VIGENTE
NIVEL 2 │ Clase 2026-08-16 (Calet — Banco de Conceptos y Estructura 1-1-5 ABO)     <- VIGENTE
NIVEL 1 │ Clases 1 a 22 curso base (Joaquín · Camilo · Mercy Pardo)               <- ANTECEDENTE
```

* **Regla de Recencia:** La clase más reciente deroga a la anterior en cualquier parámetro operativo.
* **Normalización de Monedas:**
  * `1 USD = 4,050 COP` (tasa de referencia clases Colombia).
  * `1 USD = 7.62 GTQ` (tasa oficial Guatemala del sistema).

---

## 1. VARIABLES DE ESTRUCTURA Y CAMPAÑAS

| Nombre de Variable | Valor Actual | Unidad | Fuente Vigente | Deroga a | Archivo Ejecutor |
|---|---|---|---|---|---|
| `FASE1_ESTRUCTURA` | `1×6×2 ABO` (6 conjuntos, 1 ángulo c/u, 2 anuncios) | Estructura | Joaquín / Mercy | 1×3×2 | `.claude/agents/ETAPA-6.md` |
| `FASE1_PRESUPUESTO_CONJUNTO` | `$2.99 USD` (Q22.80) | USD / día | Calibración GT | $1.48 USD | `.claude/agents/ETAPA-6.md` |
| `FASE1_OBJETIVO_CAMPANA` | `OUTCOME_TRAFFIC` / `OUTCOME_SALES` | Objetivo Meta | Clase 22-ago (Calet) | Tráfico puro | `DOCTRINA/MCP_PLAYBOOK.md` |
| `FASE2_ESTRUCTURA` | `1-1-5 ABO` (1 Campaña · 1 Conjunto · 5 Creativos) | Estructura | **Clase 16-ago (Calet)** | CBO en testeo | `.claude/agents/ETAPA-6.md` |
| `FASE2_TIPO_PRESUPUESTO` | `ABO` (Nivel conjunto, nunca CBO) | Tipo Ppto | **Clase 16-ago (Calet)** | CBO | `.claude/agents/ETAPA-6.md` |
| `FASE2_PRESUPUESTO_DIA` | `$4.00 a $6.20 USD` (Q30 a Q47 / 16k-25k COP) | USD / día | **Clase 16-ago (Calet)** | $2.99 USD | `Ads/_TOOLS/gen_fase2_lean.py` |
| `FASE2_DURACION_TESTEO` | **`3 DÍAS`** (Dejar rodar 3 días para optimización) | Días | **Clase 22-ago (Calet)** | 7 a 14 días | `PRODUCTOS/_PARAMETROS_DECISION.csv` |
| `FASE2_CAMPANAS_PARALELO` | `2 a 3 campañas` (1-1-5 A, 1-1-5 B, 1-2-5 C) | Cantidad | **Clase 16-ago (Calet)** | 1 sola campaña | `DOCTRINA/CALENDARIO_ESCALADO.md` |
| `FASE3_ESTRUCTURA` | `1-1-7 CBO` (1 Campaña · 1 Conjunto · 7 Anuncios) | Estructura | **Clase 22-ago (Calet)** | 1-1-1 o 1-7-7 | `.claude/agents/ETAPA-6.md` |
| `FASE3_PRESUPUESTO_INICIAL` | `$15.00 a $18.00 USD` (Q115 a Q140 / 60k-72k COP) | USD / día | **Clase 22-ago (Calet)** | $5.98 USD | `DOCTRINA/ESCALADO_PLAYBOOK.md` |
| `FASE3_OBJETIVO_CAMPANA` | `OUTCOME_SALES` (Maximizar conversaciones WhatsApp) | Objetivo Meta | **Clase 22-ago (Calet)** | Tráfico | `DOCTRINA/MCP_PLAYBOOK.md` |
| `FASE3_METODO_ESCALADO_1` | **Duplicación horizontal al ppto inicial** ($15 USD) | Método | **Clase 22-ago (Calet)** | Escala vertical ciega | `Ads/_TOOLS/decidir.py` |
| `FASE3_METODO_ESCALADO_2` | **Surfing intradía (+20% mañana, +20% mediodía)** | Método | **Clase 22-ago (Calet)** | +20% una vez al día | `Ads/_TOOLS/decidir.py` |

---

## 2. VARIABLES DE TIEMPO Y VENTANAS OPERATIVAS

| Nombre de Variable | Valor Actual | Unidad | Fuente Vigente | Justificación | Archivo Ejecutor |
|---|---|---|---|---|---|
| `VENTANA_DECISION_OPERATIVA` | **`3 DÍAS`** | Días | **Clase 22-ago (Calet)** | Tiempo que tarda una campaña 1-1-5 en estabilizar costos y revelar ganador. | `PRODUCTOS/_PARAMETROS_DECISION.csv` · `decidir.py` |
| `HORA_LANZAMIENTO_CAMPANA` | `04:00 AM` (Día siguiente) | Hora local | Clase 6 (Mercy) / Sistema | Permite a Meta distribuir el presupuesto completo de 24 horas. | `CLAUDE.md` Invariante 7 |
| `LIMITE_HORA_SURFING` | `15:00 (03:00 PM)` | Hora local | **Clase 22-ago (Calet)** | De las 3 PM en adelante baja el rendimiento; no subir presupuesto tarde. | `DOCTRINA/CALENDARIO_ESCALADO.md` |
| `MADURACION_ENTREGA_COD` | `3 a 10 DÍAS` (3d en GT para cobro) | Días | Doctrina Contable / Forza | Negocio contra-entrega: el pedido no es caja hasta ser entregado. | `DOCTRINA/CONTABILIDAD.md` |
| `DETECTOR_FATIGA_VENTANA` | `3 DÍAS` | Días | **Clase 22-ago (Calet)** | Ventana corta para comparar rendimiento reciente vs histórico. | `Ads/_TOOLS/decidir.py` |

---

## 3. VARIABLES DE RIESGO Y TOLERANCIA (BANKROLL)

| Nombre de Variable | Valor Actual | Unidad | Fuente Vigente | Justificación | Archivo Ejecutor |
|---|---|---|---|---|---|
| `TOLERANCIA_MAXIMA_TESTEO` | `1.0 × Break-Even (PD)` | Factor BE | Camilo (Clase 8) / Calet | Si un conjunto gasta 1x su BE sin ventas, se corta pérdida. | `Ads/_TOOLS/decidir.py` |
| `UMBRAL_HOOK_MUERTO_USD` | `$5.00 USD` | USD | Regla Operativa Sistema | Gastar $5 sin ni 1 mensaje indica hook inútil o enlace roto. | `Ads/_TOOLS/decidir.py` |
| `UMBRAL_CPA_DESBORDADO` | `1.4 × Break-Even` | Factor BE | Regla Operativa Sistema | CPA 40% sobre BE destruye rentabilidad de forma confirmada. | `Ads/_TOOLS/decidir.py` |
| `MINIMO_VENTAS_PARA_ESCALAR` | `2 ventas confirmadas` | Ventas | **Clase 22-ago (Calet)** | Nunca escalar con 1 sola venta por azar. | `Ads/_TOOLS/decidir.py` |
| `PORCENTAJE_SURFING_STEP` | `+20%` | Porcentaje | Calet / Joaquín | Máximo incremento para no desoptimizar el aprendizaje. | `Ads/_TOOLS/decidir.py` |
| `NIVEL_CONFIANZA_ESTADISTICA` | `0.95 (95%)` | Proporción | Teoría Bayesiana (Jeffreys) | Evita apagar ganadores con muestra insuficiente. | `PRODUCTOS/_PARAMETROS_DECISION.csv` |

---

## 4. VARIABLES DE CREATIVOS Y FABRICACIÓN

| Nombre de Variable | Valor Actual | Unidad | Fuente Vigente | Justificación | Archivo Ejecutor |
|---|---|---|---|---|---|
| `CONCEPTOS_POR_ANGULO` | `10 conceptos distintos` | Cantidad | **Clase 16-ago (Calet)** | El ángulo se mantiene fijo; se prueban 10 formas visuales de mostrarlo. | `_CATALOGO_CONCEPTOS.md` |
| `BLUEPRINTS_CANONICOS` | `22 blueprints validados` | Cantidad | Auditoría Portafolio GT | Plantillas visuales probadas en Guatemala. | `Ads/_SWIPE/_BLUEPRINTS/` |
| `PRODUCCION_CREATIVA_DIARIA` | `≥ 6 creativos / día` | Piezas | Sistema Fábrica Creativa | Mantener stock fresco para rotar conceptos ante fatiga. | `.claude/agents/ETAPA-9.md` |
| `REGLA_PRECIO_EN_ANUNCIO` | `SIN PRECIO` (Máx 1 de cada 6) | Regla | **Clase 22-ago (Calet)** | El anuncio vende el dolor y la solución; el precio se da en el bot. | `DOCTRINA/COPYWRITING_ADS.md` |
| `REGLA_LONGITUD_TITULO` | `≤ 27 caracteres (2-3 palabras)` | Texto | Clase 14 (Pipe) / Calet | Títulos directos e hiper-legibles para avatares 45+. | `DOCTRINA/COPYWRITING_ADS.md` |
| `FORMATO_CREATIVO_ESCALADO` | `Imágenes tan válidas como Videos` | Formato | **Clases 16 y 22-ago (Calet)** | Las imágenes 1080x1080 escalan a CBO con igual o mejor CPA que video. | `DOCTRINA/PLANTILLAS_ADS.md` |

---

## 5. VARIABLES DE FLUJO Y CONVERSIÓN (LUCIDBOT)

| Nombre de Variable | Valor Actual | Unidad | Fuente Vigente | Justificación | Archivo Ejecutor |
|---|---|---|---|---|---|
| `UMBRAL_CIERRE_MINIMO_BOT` | **`15% a 20%`** | Porcentaje | **Clases 16 y 22-ago (Calet)** | *"Primero el flujo, luego la estructura"*. Bajo 10% no se debe escalar. | `.claude/agents/ETAPA-11.md` |
| `TIEMPO_RESPUESTA_BOT` | `2 a 3 segundos` | Segundos | Clase 22 (Flujo) | Evitar fuga por espera en WhatsApp. | `.claude/agents/ETAPA-5.md` |
| `CONGRUENCIA_ANUNCIO_BOT` | `100% obligatoria` | Regla | **Clases 16 y 22-ago (Calet)** | El hook y la promesa del anuncio deben ser la primera línea del bot. | `CLAUDE.md` · `ETAPA-11.md` |
| `ESTRUCTURA_BOT_ESCALADO` | `Flujo dedicado al ángulo ganador` | Estructura | Clase 22 / Joaquín | Paraguas para testear (Fase 1); dedicado para escalar (Fase 3). | `.claude/agents/ETAPA-11.md` |

---

## 6. PROTOCOLO DE INGESTA DE NUEVA CLASE (PASO A PASO)

Cuando asistas a una nueva clase o recibas una transcripción:

1. **Guardar la transcripción:**
   Guardar el archivo como: `_CONOCIMIENTO/Finales/Clase YYYY-MM-DD - Tema (Instructor).txt`.

2. **Ejecutar Ingesta:**
   Pedirle al asistente:
   > *"Por favor analiza la nueva clase `Clase YYYY-MM-DD...txt`, extrae los parámetros nuevos, compáralos contra `DOCTRINA/GUIA_MADRE_PARAMETRIZADA.md` y dime qué variables se actualizan."*

3. **La IA ejecuta las 3 acciones automáticas:**
   * **Acción A (Diff de Variables):** Muestra una tabla comparando: `Variable` | `Valor Anterior` | `Nuevo Valor en Clase` | `Impacto`.
   * **Acción B (Actualización de Guía Madre):** Actualiza el valor y la fuente en este archivo.
   * **Acción C (Propagación en Código):** Si cambia un presupuesto, tiempo o estructura, actualiza automáticamente `_PARAMETROS_DECISION.csv`, `decidir.py` o las etapas en `.claude/agents/`.
