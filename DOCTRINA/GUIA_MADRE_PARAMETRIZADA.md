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
* **Pero el NIVEL 4 manda sobre la clase.** Un mentor enseña con SU presupuesto y SU volumen. Antes de
  copiar un número de una clase hay que preguntar de qué es envoltorio: los "3 días" de Calet son el
  envoltorio de 20-30 ventas, no una constante de tiempo. **Copiar el reloj sin copiar el presupuesto
  copia la forma y tira la señal.** Si la data propia contradice el número, manda la data propia.
* **Normalización de Monedas:**
  * `1 USD = 4,050 COP` (tasa de referencia clases Colombia).
  * `1 USD = 7.62 GTQ` (tasa oficial Guatemala del sistema).

---

# PARTE I — VARIABLES DE INVESTIGACIÓN PROFUNDA, PSICOGRAFÍA Y ÁNGULOS
### (LA CAPA HUMANA: A QUIÉN SE LE HABLA, EL PROBLEMA REAL Y LA CONVERSIÓN)

> **PRINCIPIO FUNDAMENTAL:** *"No se quema el producto, se quema el ÁNGULO."* 
> La gente no compra con la lógica: compra con la emoción (dolor, miedo, anhelo, estatus, identidad) y justifica después con la razón. Si el anuncio demuestra que conocemos el problema de la persona mejor que ella misma, la venta ocurre sola.

---

## 1. VARIABLES DE INVESTIGACIÓN Y MINADO DE VOZ DEL CLIENTE

| Nombre de Variable | Valor / Parámetro Estándar | Unidad / Formato | Fuente Vigente | Justificación y Regla de Calidad | Archivo Ejecutor |
|---|---|---|---|---|---|
| `MINADO_VOZ_CLIENTE_MINIMO` | **8 a 12 frases textuales crudas** | Frases | Clase 12 · Módulo Investigación | Mínimo estadístico para extraer patrones de dolor y anhelo sin sesgos de suposición. | `.claude/agents/ETAPA-1B.md` |
| `ETIQUETA_VOZ_REAL` | `[VOZ-REAL]` (Frase de dolor exacta) | Formato | Doctrina Vitalcom | Copiar tal cual la escribió el usuario (Reddit, foros, reseñas). Prohibido suavizar o parafrasear. | `.claude/agents/ETAPA-1B.md` |
| `ETIQUETA_DESEO_REAL` | `[DESEO-REAL]` (Frase de anhelo exacta) | Formato | Clases 10 y 20 (Joaquín) | El anhelo aspiracional en primera persona convierte tanto o más que el dolor punzante. | `.claude/agents/ETAPA-1B.md` |
| `IDENTIFICACION_ELEFANTE` | **1 Problema Oculto + Consecuencia Emocional** | Hallazgo | Clase 12 ("La mina de oro") | La causa raíz que el avatar sufre pero que la competencia ignora. Quien la nombra primero, domina el mercado. | `DOCTRINA/MODULO_INTELIGENCIA_PRODUCTO.md` |
| `FUENTES_RESEARCH_OBLIGATORIAS` | Reddit, foros de nicho, reseñas 1★ Amazon/Google, blogs | Plataformas | ETAPA-1B / Research | Lugares donde el usuario desahoga su frustración sin filtro comercial ni censura publicitaria. | `.claude/agents/ETAPA-1B.md` |
| `PROHIBICION_INVENTAR_VOZ` | **Estricta (Cero testimonios sintéticos)** | Regla dura | Doctrina Vitalcom | Si no hay señal externa en foros para un dolor, se marca "sin señal externa". Nunca inventar citas. | `.claude/agents/ETAPA-1B.md` |

---

## 2. VARIABLES DE PSICOGRAFÍA DEL AVATAR (LOS 5 EJES + IDENTIDAD)

| Nombre de Variable | Eje / Componente | Definición Parametrizada | Pregunta Guía Obligatoria | Archivo Ejecutor |
|---|---|---|---|---|
| `AVATAR_EJE_1_DOLORES` | **Dolor Activo y Concreto** | Síntoma específico, físico o visible del día a día (no genérico). | *¿Qué molestia exacta o síntoma físico le fastidió hoy al despertar o al trabajar?* | `.claude/agents/ETAPA-2.md` |
| `AVATAR_EJE_2_DESEOS` | **Deseo Específico Medible** | Cómo quiere verse, sentirse o desenvolverse en su rutina. | *¿Cuál es la imagen mental exacta de su vida si este problema desapareciera mañana?* | `.claude/agents/ETAPA-2.md` |
| `AVATAR_EJE_3_MIEDOS` | **Miedo a Futuro / Catástrofe** | Qué teme que pase a mediano/largo plazo si no toma acción hoy. | *¿Qué escenario temido le quita el sueño si el problema sigue empeorando?* | `.claude/agents/ETAPA-2.md` |
| `AVATAR_EJE_4_FRUSTRACIONES` | **Fracasos Previos Acumulados** | Tratamientos, remedios o productos que ya probó y no funcionaron. | *¿En qué botó plata antes y por qué siente que nadie le soluciona el problema?* | `.claude/agents/ETAPA-2.md` |
| `AVATAR_EJE_5_IDENTIDAD` | **Transformación Emocional Oculta** | La herida de identidad o autoestima (quién quiere SER o cómo se siente juzgado). | *¿Qué vergüenza, culpa o pérdida de valor personal le produce este problema en secreto?* | `.claude/agents/ETAPA-2.md` |
| `PARAMETRO_ESPECIFICIDAD_AVATAR` | **"Reconocible en la calle"** | Datos demográficos + situación vital + contexto local (Guatemala 35-65+). | Prohibido "personas con insomnio". Sí: "madre de 45 años en Mixco que despierta a las 2 AM con taquicardia". | `.claude/agents/ETAPA-2.md` |

---

## 3. VARIABLES DE NIVELES DE CONCIENCIA (EUGENE SCHWARTZ)

| Nivel de Conciencia | Estado Mental del Avatar | Tipo de Ángulo Dominante | Tipo de Hook Recomendado | Canal de Cierre |
|---|---|---|---|---|
| **NIVEL 1 — No sabe que tiene el problema** | Siente el síntoma o molestia pero ignora la causa real y la etiqueta médica. | Educativo / Revelación del problema oculto ("El elefante"). | *"Si te arde el estómago al despertar, el problema no es la acidez..."* | Anuncio largo / Explicación bot |
| **NIVEL 2 — Conoce el problema, no la solución** | Sabe con certeza qué padece, pero no sabe cómo solucionarlo de raíz. | Problema - Solución / Mecanismo único innovador. | *"Por qué tomar magnesio genérico no calma tus calambres nocturnos..."* | Prueba de mecanismo / LucidBot |
| **NIVEL 3A — Conoce el producto pero desconfía** | Sabe que este tipo de solución existe, pero desconfía de comprar por internet. | Reducción de fricción: Autoridad, garantía, prueba social, COD. | *"El único tratamiento con registro y pago contra entrega en toda Guatemala."* | Video médico / Testimonios bot |
| **NIVEL 3B — Conoce el producto y compara** | Conoce marcas similares, está listo para comprar, busca la mejor oferta/pack. | Oferta irresistible, paquetes de tratamiento (2x1, 3x1), escasez. | *"Tratamiento completo de 60 días con 40% de descuento solo por hoy."* | Cierre comercial / Oferta WhatsApp |
| **NIVEL 4 — Hiper consciente** | Cliente recurrente o lead fidelizado que ya validó la marca. | Reorden / Upsell / Nuevas aplicaciones del producto. | *"Renueva tu tratamiento mensual con entrega prioritaria."* | WhatsApp Remarketing |

---

## 4. VARIABLES DE ARQUITECTURA DEL EMBUDO (TOFU / MOFU / BOFU)

| Etapa del Embudo | Temperatura de Tráfico | Nivel de Conciencia Asociado | Rol del Creativo / Copy | Elementos Indispensables |
|---|---|---|---|---|
| **TOFU (Top of Funnel)** | Frío (Prospectos masivos) | Niveles 1 y 2 | **Frenar el scroll y generar identificación inmediata.** Abre mercado. | No nombrar el producto en los primeros 3 segundos. Enfocar 100% en el síntoma o dolor agudo. |
| **MOFU (Middle of Funnel)** | Tibio (Consideración) | Niveles 2 y 3a | **Demostrar el mecanismo único y derribar la objeción crítica.** | Historia de transformación, autoridad, respaldo clínico, comparación antes/después. |
| **BOFU (Bottom of Funnel)** | Caliente (Decisión final) | Niveles 3a y 3b | **Cerrar la venta eliminando todo riesgo financiero.** | Tratamiento por semanas (2-4 semanas), garantía total, **pago contra entrega en mano**. |
| `REGLA_COBERTURA_EMBUDO` | Mínimo 1 concepto de cada nivel activo en escalado | Regla | Asegura que la campaña no sature al público caliente y siga sembrando prospectos fríos. | `DOCTRINA/ESCALADO_PLAYBOOK.md` |

---

## 5. VARIABLES DE ANÁLISIS COMPETITIVO (MATRIZ DOFA / FODA)

| Cuadrante DOFA | Variable Analítica | Enfoque de Investigación | Aplicación en el Mensaje Publicitario |
|---|---|---|---|
| **Debilidades (Mercado / Competencia)** | `DOFA_DEBILIDADES_COMPETENCIA` | Qué quejas tienen los clientes de la competencia (pastillas grandes, mal sabor, demoras, sin resultados). | Usar sus defectos como contraste: *"A diferencia de las cápsulas difíciles de tragar..."* |
| **Oportunidades (Nichos Desatendidos)** | `DOFA_OPORTUNIDADES_ANGULOS` | Qué síntomas secundarios o causas nadie está atacando en Meta Ads Library. | Crear ángulos de baja saturación ("océano azul"): abordar el dolor que otros omiten. |
| **Fortalezas (Nuestra Oferta)** | `DOFA_FORTALEZAS_PRODUCTO` | Mecanismo único, pureza de ingredientes, rapidez de absorción, soporte post-compra. | El pilar central de la Promesa y Mecanismo en la estructura HPPPC. |
| **Amenazas (Objeciones del Entorno)** | `DOFA_AMENAZAS_ENTORNO` | Desconfianza de estafas en Guatemala, productos chinos de imitación, miedo a efectos secundarios. | Implementar sellos de garantía, empaque original, soporte WhatsApp humano y pago COD. |

---

## 6. VARIABLES DE DEFINICIÓN, HOOKS (HPPPC) Y RANKING DE ÁNGULOS

| Nombre de Variable | Parámetro / Fórmula | Definición / Requisito | Regla de Oro | Archivo Ejecutor |
|---|---|---|---|---|
| `DIFERENCIA_ANGULO_VS_FORMATO` | **Ángulo = Problema; Formato = Contenedor** | El ángulo es la causa del dolor; el formato es video UGC, imagen estática, infografía, etc. | **Nunca testear 2 variables.** FASE 1 mide ángulo; FASE 2 mide formato/concepto. | `CLAUDE.md` |
| `REGLA_ANGULO_DIRECTO` | **Hiper-segmentado vs Generalizado** | No "mejora tu salud", sí "¿tienes dolor punzante en la rodilla al bajar gradas?". | El copy directo segmenta al algoritmo sin pagar por curiosos que no compran. | `DOCTRINA/COPYWRITING_ADS.md` |
| `ESTRUCTURA_HOOK_HPPPC` | **Hook → Problema → Promesa → Prueba → CTA** | Estructura obligatoria de los primeros segundos del anuncio o copy. | Hook de 3-5s con tensión, negatividad o sorpresa. Jamás dar la solución en el hook. | `.claude/agents/ETAPA-4.md` |
| `PALANCA_NUMEROS_ESTADISTICA` | **Datos reales verificables** | Mínimo 1 de cada 6 ángulos abre con estadística o dato porcentual concreto. | Prohibido inventar fuentes. Credibilidad matemática para avatares escépticos. | `.claude/agents/ETAPA-2.md` |
| `JERARQUIA_RANKING_ANGULOS` | **1. Respaldo Voz-Real / Oculto > 2. Emoción > 3. Baja Saturación > 4. Urgencia > 5. Directo** | Criterio estricto de priorización de ángulos para lanzar primero. | El dolor activo urgente gana sobre el deseo lejano. El ángulo emocional gana sobre el funcional. | `.claude/agents/ETAPA-2.md` |

---

## 7. VARIABLES DE OBJECIONES Y DERRIBO CRÍTICO (OBJECTION KILLING)

| Código | Categoría Universal de Objeción | Frase Típica del Avatar (Voz Mental) | Disolución Obligatoria en Creativo o Bot |
|---|---|---|---|
| `OBJ-01` | **Credibilidad** | *"¿Esto de verdad funciona o es otra estafa más de internet?"* | Prueba social en video, registro sanitario, número de clientes satisfechos. |
| `OBJ-02` | **Idoneidad** | *"¿Esto servirá para mi caso específico o mi edad?"* | Explicación clara del avatar calificado y para quién NO es. |
| `OBJ-03` | **Seguridad** | *"¿Tiene efectos secundarios? ¿Me va a dañar los riñones o el estómago?"* | Ingredientes 100% naturales, certificaciones, sin contraindicaciones severas. |
| `OBJ-04` | **Tiempo** | *"¿Cuánto tarda en hacer efecto? No quiero esperar meses."* | Progresión creíble por semanas (alivio en semana 1, consolidación en semana 4). |
| `OBJ-05` | **Logística / Pago** | *"¿Y si me roban la tarjeta o me cobran y no me mandan nada?"* | **Pago contra entrega (COD): pagas en efectivo en tu puerta al recibir.** |
| `OBJ-06` | **Precio / Valor** | *"Se me hace muy caro comparado con lo que compro en la farmacia."* | Costo por dosis diaria ($0.50/día) vs costo del problema sin resolver. |
| `OBJ-07` | **Cantidad** | *"¿Por qué debería pedir 2 o 3 frascos si apenas voy a probarlo?"* | Los ciclos celulares de regeneración toman mínimo 30-60 días continuos. |
| `OBJ-08` | **Experiencia Previa** | *"Ya probé suplementos parecidos y ninguno me quitó el dolor."* | El mecanismo único: por qué este producto actúa diferente a lo genérico. |
| `OBJECION_CRITICA_NUMERO_1` | **La barrera dominante identificada en foros** | Marcada con `[EXTERNO]` en investigación profunda. | **Debe derribarse en el Creativo 1 y en el primer bloque de respuesta del bot.** |

---

## 8. VARIABLES DE MICROÁNGULOS Y DIVERSIDAD CREATIVA (FASE 3)

| Nombre de Variable | Valor / Requisito | Unidad | Justificación Técnica | Archivo Ejecutor |
|---|---|---|---|---|
| `MICROANGULOS_POR_GANADOR` | **8 a 12 microángulos específicos** | Cantidad | Al escalar, el ángulo ganador no se abandona: se desglosa en sub-dolores ultra específicos. | `.claude/agents/ETAPA-3.md` |
| `REGLA_CONCEPTO_DISTINTO` | **1 Presentación radicalmente distinta por conjunto** | Regla dura | Un cambio de color, fondo o tipografía es penalizado por Meta por fatiga. Se requiere un concepto visual entero nuevo. | `.claude/agents/ETAPA-3.md` |
| `TIMELINE_TRANSFORMACION` | **Progresión por semanas (7 a 30 días)** | Días | Prohibido "resultados en 24 horas" (baneo y nula credibilidad) o "en 4 meses" (intimida). | `DOCTRINA/COPYWRITING_ADS.md` |

---
---

# PARTE II — VARIABLES OPERATIVAS, CAMPAÑAS Y CONTROL FINANCIERO
### (LA CAPA DE NÚMEROS: ESTRUCTURAS, TIEMPOS, PRESUPUESTOS Y DECISIÓN)

---

## 9. VARIABLES DE ESTRUCTURA Y CAMPAÑAS

| Nombre de Variable | Valor Actual | Unidad | Fuente Vigente | Deroga a | Archivo Ejecutor |
|---|---|---|---|---|---|
| `FASE1_ESTRUCTURA` | `1×6×2 ABO` (6 conjuntos, 1 ángulo c/u, 2 anuncios) | Estructura | Joaquín / Mercy | 1×3×2 | `.claude/agents/ETAPA-6.md` |
| `FASE1_PRESUPUESTO_CONJUNTO` | `$2.99 USD` (Q22.80) | USD / día | Calibración GT | $1.48 USD | `.claude/agents/ETAPA-6.md` |
| `FASE1_OBJETIVO_CAMPANA` | `OUTCOME_TRAFFIC` / `OUTCOME_SALES` | Objetivo Meta | Clase 22-ago (Calet) | Tráfico puro | `DOCTRINA/MCP_PLAYBOOK.md` |
| `FASE2_ESTRUCTURA` | `1-1-5 ABO` (1 Campaña · 1 Conjunto · 5 Creativos) | Estructura | **Clase 16-ago (Calet)** | CBO en testeo | `.claude/agents/ETAPA-6.md` |
| `FASE2_TIPO_PRESUPUESTO` | `ABO` (Nivel conjunto, nunca CBO) | Tipo Ppto | **Clase 16-ago (Calet)** | CBO | `.claude/agents/ETAPA-6.md` |
| `FASE2_PRESUPUESTO_DIA` | `$4.00 a $6.20 USD` (Q30 a Q47 / 16k-25k COP) | USD / día | **Clase 16-ago (Calet)** | $2.99 USD | `Ads/_TOOLS/gen_fase2_lean.py` |
| `FASE2_DURACION_TESTEO` | **`3 DÍAS`** (Dejar rodar 3 días para optimización) | Días | **Clase 22-ago (Calet)** | 7 a 14 días | `PRODUCTOS/_PARAMETROS_DECISION.csv` → `duracion_testeo_fase2_dias` |
| `FASE2_CAMPANAS_PARALELO` | `2 a 3 campañas` (1-1-5 A, 1-1-5 B, 1-2-5 C) | Cantidad | **Clase 16-ago (Calet)** | 1 sola campaña | `DOCTRINA/CALENDARIO_ESCALADO.md` |
| `FASE3_ESTRUCTURA` | `1-1-7 CBO` (1 Campaña · 1 Conjunto · 7 Anuncios) | Estructura | **Clase 22-ago (Calet)** | 1-1-1 o 1-7-7 | `.claude/agents/ETAPA-6.md` |
| `FASE3_PRESUPUESTO_INICIAL` | `$15.00 a $18.00 USD` (Q115 a Q140 / 60k-72k COP) | USD / día | **Clase 22-ago (Calet)** | $5.98 USD | `DOCTRINA/ESCALADO_PLAYBOOK.md` |
| `FASE3_OBJETIVO_CAMPANA` | `OUTCOME_SALES` (Maximizar conversaciones WhatsApp) | Objetivo Meta | **Clase 22-ago (Calet)** | Tráfico | `DOCTRINA/MCP_PLAYBOOK.md` |
| `FASE3_METODO_ESCALADO_1` | **Duplicación horizontal al ppto inicial** ($15 USD) | Método | **Clase 22-ago (Calet)** | Escala vertical ciega | `Ads/_TOOLS/decidir.py` |
| `FASE3_METODO_ESCALADO_2` | **Surfing intradía (+20% mañana, +20% mediodía)** | Método | **Clase 22-ago (Calet)** | +20% una vez al día | `Ads/_TOOLS/decidir.py` |

---

## 10. VARIABLES DE TIEMPO Y VENTANAS OPERATIVAS

| Nombre de Variable | Valor Actual | Unidad | Fuente Vigente | Justificación | Archivo Ejecutor |
|---|---|---|---|---|---|
| `VENTANA_EVALUACION_DIAS` | **`14 DÍAS`** | Días | Data propia (NIVEL 4) | Sobre cuántos días se calcula el CPA y el intervalo de credibilidad. **NO es la duración del testeo de Calet.** Calet decide en 3 días porque corre a $15-18 USD/día y esos 3 días le traen 20-30 ventas; a $3-6 USD/día traen 1-3 y el motor queda ciego. Lo que Calet fija es **volumen de evidencia, no tiempo**. Verificado 07-sep-2026: con ventana 3 el motor ordenó apagar un ángulo de 38 ventas rentables. | `PRODUCTOS/_PARAMETROS_DECISION.csv` · `Ads/_TOOLS/decidir.py` |
| `DURACION_TESTEO_FASE2_DIAS` | **`3 DÍAS`** | Días | **Clase 22-ago (Calet)** | Cuánto rueda la campaña 1-1-5 antes de coronar el concepto ganador. Literal: *"de esa campaña de 115 la dejo rodando unos tres días"*. Es una **duración de campaña**, no una ventana de cálculo. | `PRODUCTOS/_PARAMETROS_DECISION.csv` · `.claude/agents/ETAPA-6.md` |
| `TOLERANCIA_BASE` | **`acumulado`** | Modo | Data propia (NIVEL 4) | La regla de pausar por 1× BE se mide sobre el gasto **desde el lanzamiento**, nunca sobre la ventana móvil: la pérdida se acumula. Con ventana móvil de 3 días era inalcanzable (Q22.80/día × 3 = Q68.40 contra BE Q93.41) y no cortaba nunca. | `Ads/_TOOLS/decidir.py` |
| `HORA_LANZAMIENTO_CAMPANA` | `04:00 AM` (Día siguiente) | Hora local | Clase 6 (Mercy) / Sistema | Permite a Meta distribuir el presupuesto completo de 24 horas. | `CLAUDE.md` Invariante 7 |
| `LIMITE_HORA_SURFING` | `15:00 (03:00 PM)` | Hora local | **Clase 22-ago (Calet)** | De las 3 PM en adelante baja el rendimiento; no subir presupuesto tarde. | `DOCTRINA/CALENDARIO_ESCALADO.md` |
| `MADURACION_ENTREGA_COD` | `3 a 10 DÍAS` (3d en GT para cobro) | Días | Doctrina Contable / Forza | Negocio contra-entrega: el pedido no es caja hasta ser entregado. | `DOCTRINA/CONTABILIDAD.md` |
| `VENTANA_FATIGA_DIAS` | `3 DÍAS` | Días | **Clase 22-ago (Calet)** | Días recientes que se comparan **contra** `VENTANA_EVALUACION_DIAS`. Debe ser **estrictamente menor** que ella: si son iguales, la celda se compara consigo misma y `RENOVAR` no se emite nunca. Eso ocurrió con ventana 3 el 07-sep-2026. | `Ads/_TOOLS/decidir.py` |

---

## 11. VARIABLES DE RIESGO Y TOLERANCIA (BANKROLL)

| Nombre de Variable | Valor Actual | Unidad | Fuente Vigente | Justificación | Archivo Ejecutor |
|---|---|---|---|---|---|
| `TOLERANCIA_MAXIMA_TESTEO` | `1.0 × Break-Even (PD)` | Factor BE | Camilo (Clase 8) / Calet | Si un conjunto gasta 1× su BE **acumulado** sin ventas, se corta pérdida. Ver `TOLERANCIA_BASE`. | `Ads/_TOOLS/decidir.py` |
| `GUARDA_GANADOR_HISTORICO` | `≥5 ventas acumuladas y CPA acumulado ≤ BE` | Regla dura | Data propia (NIVEL 4) | Un ángulo con historia de rentabilidad **nunca recibe APAGAR** por una mala racha: cae a `RENOVAR` (rotar concepto). Sin esta guarda, `PAUSAR` se evalúa antes que `FATIGA` y mata ganadores. | `Ads/_TOOLS/decidir.py` · `Ads/_TOOLS/test_decidir.py` |
| `UMBRAL_HOOK_MUERTO_USD` | `$5.00 USD` | USD | Regla Operativa Sistema | Gastar $5 sin ni 1 mensaje indica hook inútil o enlace roto. | `Ads/_TOOLS/decidir.py` |
| `UMBRAL_CPA_DESBORDADO` | `1.4 × Break-Even` | Factor BE | Regla Operativa Sistema | CPA 40% sobre BE destruye rentabilidad de forma confirmada. | `Ads/_TOOLS/decidir.py` |
| `MINIMO_VENTAS_PARA_ESCALAR` | `2 ventas confirmadas` | Ventas | **Clase 22-ago (Calet)** | Nunca escalar con 1 sola venta por azar. | `Ads/_TOOLS/decidir.py` |
| `PORCENTAJE_SURFING_STEP` | `+20%` | Porcentaje | Calet / Joaquín | Máximo incremento para no desoptimizar el aprendizaje. | `Ads/_TOOLS/decidir.py` |
| `NIVEL_CONFIANZA_ESTADISTICA` | `0.95 (95%)` | Proporción | Teoría Bayesiana (Jeffreys) | Evita apagar ganadores con muestra insuficiente. | `PRODUCTOS/_PARAMETROS_DECISION.csv` |
| `ALPHA_CIERRE` | `0.05` | p-valor | Fisher exacto | Umbral para declarar que dos ángulos cierran distinto. **El cierre CORTA, nunca corona** (invariante 1): sirve para descartar, jamás para elegir al ganador. | `Ads/_TOOLS/decidir.py` · `PRODUCTOS/_PARAMETROS_DECISION.csv` |
| `MINIMO_MENSAJES_COMPARAR_CIERRE` | `30 mensajes` | Mensajes | Regla Operativa Sistema | Piso para siquiera comparar dos tasas de cierre. Por debajo, Fisher no distingue nada útil y la comparación es ruido. | `Ads/_TOOLS/decidir.py` · `PRODUCTOS/_PARAMETROS_DECISION.csv` |
| `HORIZONTE_VENTAS_PROYECCION` | `60 ventas` | Ventas | Regla Operativa Sistema | Tope de la proyección al CPA observado con que se calcula el *"faltan ~N ventas"* que ve el operador en `SEGUIR_MIDIENDO`. Si ni con 60 el intervalo se resuelve, el CPA no va a decidir esa celda y hay que mirar el CIERRE. | `Ads/_TOOLS/decidir.py` · `PRODUCTOS/_PARAMETROS_DECISION.csv` |

---

## 12. VARIABLES DE CREATIVOS Y FABRICACIÓN

| Nombre de Variable | Valor Actual | Unidad | Fuente Vigente | Justificación | Archivo Ejecutor |
|---|---|---|---|---|---|
| `CONCEPTOS_POR_ANGULO` | `10 conceptos distintos` | Cantidad | **Clase 16-ago (Calet)** | El ángulo se mantiene fijo; se prueban 10 formas visuales de mostrarlo. | `Ads/_SWIPE/_CATALOGO_CONCEPTOS.md` |
| `BLUEPRINTS_CANONICOS` | `22 blueprints validados` | Cantidad | Auditoría Portafolio GT | Plantillas visuales probadas en Guatemala. | `Ads/_SWIPE/_BLUEPRINTS/` |
| `PRODUCCION_CREATIVA_DIARIA` | `≥ 6 creativos / día` | Piezas | Sistema Fábrica Creativa | Mantener stock fresco para rotar conceptos ante fatiga. | `.claude/agents/ETAPA-9.md` |
| `REGLA_PRECIO_EN_ANUNCIO` | `SIN PRECIO` (Máx 1 de cada 6) | Regla | **Clase 22-ago (Calet)** | El anuncio vende el dolor y la solución; el precio se da en el bot. | `DOCTRINA/COPYWRITING_ADS.md` |
| `REGLA_LONGITUD_TITULO` | `≤ 27 caracteres (2-3 palabras)` | Texto | Clase 14 (Pipe) / Calet | Títulos directos e hiper-legibles para avatares 45+. | `DOCTRINA/COPYWRITING_ADS.md` |
| `FORMATO_CREATIVO_ESCALADO` | `Imágenes tan válidas como Videos` | Formato | **Clases 16 y 22-ago (Calet)** | Las imágenes 1080x1080 escalan a CBO con igual o mejor CPA que video. | `DOCTRINA/PLANTILLAS_ADS.md` |

---

## 13. VARIABLES DE FLUJO Y CONVERSIÓN (LUCIDBOT)

| Nombre de Variable | Valor Actual | Unidad | Fuente Vigente | Justificación | Archivo Ejecutor |
|---|---|---|---|---|---|
| `UMBRAL_CIERRE_MINIMO_BOT` | **`15% a 20%`** | Porcentaje | **Clases 16 y 22-ago (Calet)** | *"Primero el flujo, luego la estructura"*. Bajo 10% no se debe escalar. | `.claude/agents/ETAPA-11.md` |
| `TIEMPO_RESPUESTA_BOT` | `2 a 3 segundos` | Segundos | Clase 22 (Flujo) | Evitar fuga por espera en WhatsApp. | `.claude/agents/ETAPA-5.md` |
| `CONGRUENCIA_ANUNCIO_BOT` | `100% obligatoria` | Regla | **Clases 16 y 22-ago (Calet)** | El hook y la promesa del anuncio deben ser la primera línea del bot. | `CLAUDE.md` · `.claude/agents/ETAPA-11.md` |
| `ESTRUCTURA_BOT_ESCALADO` | `Flujo dedicado al ángulo ganador` | Estructura | Clase 22 / Joaquín | Paraguas para testear (Fase 1); dedicado para escalar (Fase 3). | `.claude/agents/ETAPA-11.md` |

---
---

# PARTE III — PROTOCOLO DE INGESTA DE NUEVA CLASE (PASO A PASO)

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

4. **El gate lo comprueba, no la memoria de nadie:**

   ```bash
   python Ads/_TOOLS/verificar_guia_madre.py --listar
   ```

   Extrae el valor que **esta guía declara en cada fila** y lo compara contra el valor real
   que usa su archivo ejecutor. Si no coinciden, falla y dice cuál fila y cuál archivo.
   También verifica que todo puntero de la columna *Archivo Ejecutor* exista, y avisa si un
   parámetro nuevo aparece en `_PARAMETROS_DECISION.csv` sin fila acá.

   Corre solo: `.claude/settings.json` lo dispara al escribir este archivo o
   `_PARAMETROS_DECISION.csv`, y **bloquea la edición** si quedaron diciendo cosas distintas.

   > Sin este gate, esta guía es prosa. El 07-sep-2026 declaraba VENTANA = 3 DÍAS mientras el
   > docstring de `decidir.py` seguía diciendo 14: tres fuentes, tres respuestas, cero alarmas.
   > Lo que hace parametrizado a un sistema no es escribir las variables en una tabla —
   > es que algo falle cuando la tabla y el código dejan de coincidir.

