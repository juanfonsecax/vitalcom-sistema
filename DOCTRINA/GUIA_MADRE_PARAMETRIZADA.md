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

> **Precisión sobre `DIFERENCIA_ANGULO_VS_FORMATO` (decisión operador 22-sep-2026):** en FASE 1 el
> formato también queda FIJO en IMAGEN, no solo el concepto — se mide únicamente el ángulo. El
> formato VIDEO se testea recién en FASE 2, como un concepto más. Dueño de la regla:
> `Ads/_TOOLS/gen_plan.py --validar`.

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
| `FASE2_PRESUPUESTO_DIA` | `$4.00 a $6.20 USD` (Q30 a Q47 / 16k-25k COP) | USD / día | **Clase 16-ago (Calet)** | $2.99 USD | `PRODUCTOS/_PARAMETROS_PUBLICACION.csv` |
| `FASE2_DURACION_TESTEO` | **`3 DÍAS`** (Dejar rodar 3 días para optimización) | Días | **Clase 22-ago (Calet)** | 7 a 14 días | `PRODUCTOS/_PARAMETROS_DECISION.csv` → `duracion_testeo_fase2_dias` |
| `FASE2_CAMPANAS_PARALELO` | `2 a 3 campañas` (1-1-5 A, 1-1-5 B, 1-2-5 C) | Cantidad | **Clase 16-ago (Calet)** | 1 sola campaña | `DOCTRINA/CALENDARIO_ESCALADO.md` |
| `FASE3_ESTRUCTURA` | `1-1-7 CBO` (1 Campaña · 1 Conjunto · 7 Anuncios) | Estructura | **Clase 22-ago (Calet)** | 1-1-1 o 1-7-7 | `.claude/agents/ETAPA-6.md` |
| `FASE3_PRESUPUESTO_INICIAL` | `$15.00 a $18.00 USD` (Q115 a Q140 / 60k-72k COP) | USD / día | **Clase 22-ago (Calet)** | $5.98 USD | `DOCTRINA/ESCALADO_PLAYBOOK.md` |
| `FASE3_OBJETIVO_CAMPANA` | `OUTCOME_SALES` (Maximizar conversaciones WhatsApp) | Objetivo Meta | **Clase 22-ago (Calet)** | Tráfico | `DOCTRINA/MCP_PLAYBOOK.md` |
| `FASE3_METODO_ESCALADO_1` | **Duplicación horizontal al ppto inicial** ($15 USD) | Método | **Clase 22-ago (Calet)** | Escala vertical ciega | `Ads/_TOOLS/decidir.py` |
| `FASE3_METODO_ESCALADO_2` | **Surfing +20% una vez al día, en la mañana** (Calet enseña intradía +20% mañana + mediodía; el intradía está **CONGELADO** hasta que la fábrica sostenga ≥6 creativos/día — choque C-02 de `_CONOCIMIENTO/MATRIZ_METODOLOGIA.md`) | Método | **Clase 22-ago (Calet)** | Escala vertical ciega | `Ads/_TOOLS/decidir.py` · `.claude/skills/fase-3-escalado/SKILL.md` |
| `EXPLORACION_N_ANGULOS` | `3 ángulos` | Ángulos (mini-F1 fijo en paralelo al escalado: 1 conjunto ABO por ángulo nunca probado, presupuesto por conjunto de FASE 1, todo en IMAGEN) | Regla Operativa Sistema (P12, 23-sep-2026) — decisión del operador, no de una clase | — | `PRODUCTOS/_PARAMETROS_DECISION.csv` → `exploracion_n_angulos` · `Ads/_TOOLS/gen_plan.py` (`validar_plan_exploracion()`) · `DOCTRINA/ESCALADO/09_EXPLORACION_PARALELA.md` |

---

## 10. VARIABLES DE TIEMPO Y VENTANAS OPERATIVAS

| Nombre de Variable | Valor Actual | Unidad | Fuente Vigente | Justificación | Archivo Ejecutor |
|---|---|---|---|---|---|
| `VENTANA_EVALUACION_DIAS` | **`14 DÍAS`** | Días | Data propia (NIVEL 4) | Sobre cuántos días se calcula el CPA y el intervalo de credibilidad. **NO es la duración del testeo de Calet.** Calet decide en 3 días porque corre a $15-18 USD/día y esos 3 días le traen 20-30 ventas; a $3-6 USD/día traen 1-3 y el motor queda ciego. Lo que Calet fija es **volumen de evidencia, no tiempo**. | `PRODUCTOS/_PARAMETROS_DECISION.csv` · `Ads/_TOOLS/decidir.py` |
| `DURACION_TESTEO_FASE2_DIAS` | **`3 DÍAS`** | Días | **Clase 22-ago (Calet)** | Cuánto rueda la campaña 1-1-5 antes de coronar el concepto ganador. Literal: *"de esa campaña de 115 la dejo rodando unos tres días"*. Es una **duración de campaña**, no una ventana de cálculo. | `PRODUCTOS/_PARAMETROS_DECISION.csv` · `.claude/agents/ETAPA-6.md` |
| `TOLERANCIA_BASE` | **`acumulado`** | Modo | Data propia (NIVEL 4) | La regla de pausar por 1× BE se mide sobre el gasto **desde el lanzamiento**, nunca sobre la ventana móvil: la pérdida se acumula. Con ventana móvil de 3 días era inalcanzable (Q22.80/día × 3 = Q68.40 contra BE Q93.41) y no cortaba nunca. | `Ads/_TOOLS/decidir.py` |
| `HORA_LANZAMIENTO_CAMPANA` | `04:00 AM` (Día siguiente) | Hora local | Clase 6 (Mercy) / Sistema | Permite a Meta distribuir el presupuesto completo de 24 horas. | `CLAUDE.md` Invariante 7 |
| `LIMITE_HORA_SURFING` | `15:00 (03:00 PM)` | Hora local | **Clase 22-ago (Calet)** | De las 3 PM en adelante baja el rendimiento; no subir presupuesto tarde. | `DOCTRINA/CALENDARIO_ESCALADO.md` |
| `MADURACION_ENTREGA_COD` | `3 a 10 DÍAS` (3d en GT para cobro) | Días | Doctrina Contable / Forza | Negocio contra-entrega: el pedido no es caja hasta ser entregado. | `DOCTRINA/CONTABILIDAD.md` |
| `VENTANA_FATIGA_DIAS` | `3 DÍAS` | Días | **Clase 22-ago (Calet)** | Días recientes que se comparan **contra** `VENTANA_EVALUACION_DIAS`. Debe ser **estrictamente menor** que ella: si son iguales, la celda se compara consigo misma y `RENOVAR` no se emite nunca. | `Ads/_TOOLS/decidir.py` |

---

## 11. VARIABLES DE RIESGO Y TOLERANCIA (BANKROLL)

| Nombre de Variable | Valor Actual | Unidad | Fuente Vigente | Justificación | Archivo Ejecutor |
|---|---|---|---|---|---|
| `TOLERANCIA_MAXIMA_TESTEO` | `1.0 × Break-Even (PD)` | Factor BE | Camilo (Clase 8) / Calet | Si un conjunto gasta 1× su BE **acumulado** sin ventas, se corta pérdida. Ver `TOLERANCIA_BASE`. | `Ads/_TOOLS/decidir.py` |
| `GUARDA_GANADOR_HISTORICO` | `≥5 ventas acumuladas y CPA acumulado ≤ BE` | Regla dura | Data propia (NIVEL 4) | Un ángulo con historia de rentabilidad **nunca recibe APAGAR** por una mala racha: cae a `RENOVAR` (rotar concepto). Sin esta guarda, `PAUSAR` se evalúa antes que `FATIGA` y mata ganadores. Es también el **gate de entrada a FASE 2** que evalúa `flujo.py` (`angulo_ganador`): ángulo ganador por VENTA, invariante 1. | `Ads/_TOOLS/decidir.py` · `Ads/_TOOLS/flujo.py` · `Ads/_TOOLS/test_decidir.py` · `PRODUCTOS/_PARAMETROS_DECISION.csv` → `min_ventas_ganador` |
| `UMBRAL_HOOK_MUERTO_USD` | `$5.00 USD` | USD | Regla Operativa Sistema | Gastar $5 sin ni 1 mensaje indica hook inútil o enlace roto. | `Ads/_TOOLS/decidir.py` |
| `UMBRAL_CPA_DESBORDADO` | `1.4 × Break-Even` | Factor BE | Regla Operativa Sistema | CPA 40% sobre BE destruye rentabilidad de forma confirmada. | `Ads/_TOOLS/decidir.py` |
| `MINIMO_VENTAS_PARA_ESCALAR` | `2 ventas confirmadas` | Ventas | **Clase 22-ago (Calet)** | Nunca escalar con 1 sola venta por azar. Es también el piso por concepto de la regla de replicación **2 de 2** (`flujo.py` `concepto_2de2`, gate de entrada a FASE 3). | `Ads/_TOOLS/decidir.py` · `Ads/_TOOLS/flujo.py` · `PRODUCTOS/_PARAMETROS_DECISION.csv` → `min_ventas_escalar` |
| `MARGEN_EMPATE_CPA` | `10%` | Porcentaje | Data propia (NIVEL 4) — sim TURMERIC 15-sep-2026 | **Empate técnico de la regla 2 de 2.** Dentro de una misma campaña, dos conceptos cuyo CPA difiere menos que esto cuentan AMBOS como ganadores. Con 2-3 ventas por concepto la diferencia puntual es ruido. Mismo principio que el invariante 13: un CPA puntual no ordena una acción irreversible, y entrar a FASE 3 es comprar volumen en CBO. **No se usa el IC** para esto: con 2 ventas el intervalo de cada concepto es tan ancho que todos se solapan y el gate se vuelve trivial. Historia (la simulación que expuso la oscilación día a día): `_CONOCIMIENTO/POSTMORTEMS/GUIA_MADRE_PARAMETRIZADA_historias.md` §11. | `Ads/_TOOLS/flujo.py` · `Ads/_TOOLS/test_flujo.py` · `PRODUCTOS/_PARAMETROS_DECISION.csv` → `margen_empate_cpa_pct` |
| `PORCENTAJE_SURFING_STEP` | `+20%` | Porcentaje | Calet / Joaquín | Máximo incremento para no desoptimizar el aprendizaje. **Una vez al día, en la mañana** (el intradía está CONGELADO, choque C-02). Es el número que `decidir.py` escribe en la orden ESCALAR y el tope que la sesión respeta al ejecutar por MCP. | `Ads/_TOOLS/decidir.py` · `PRODUCTOS/_PARAMETROS_DECISION.csv` → `surfing_pct` |
| `NIVEL_CONFIANZA_ESTADISTICA` | `0.95 (95%)` | Proporción | Teoría Bayesiana (Jeffreys) | Evita apagar ganadores con muestra insuficiente. | `PRODUCTOS/_PARAMETROS_DECISION.csv` |
| `ALPHA_CIERRE` | `0.05` | p-valor | Fisher exacto | Umbral para declarar que dos ángulos cierran distinto. **El cierre CORTA, nunca corona** (invariante 1): sirve para descartar, jamás para elegir al ganador. | `Ads/_TOOLS/decidir.py` · `PRODUCTOS/_PARAMETROS_DECISION.csv` |
| `MINIMO_MENSAJES_COMPARAR_CIERRE` | `30 mensajes` | Mensajes | Regla Operativa Sistema | Piso para siquiera comparar dos tasas de cierre. Por debajo, Fisher no distingue nada útil y la comparación es ruido. | `Ads/_TOOLS/decidir.py` · `PRODUCTOS/_PARAMETROS_DECISION.csv` |
| `HORIZONTE_VENTAS_PROYECCION` | `60 ventas` | Ventas | Regla Operativa Sistema | Tope de la proyección al CPA observado con que se calcula el *"faltan ~N ventas"* que ve el operador en `SEGUIR_MIDIENDO`. Si ni con 60 el intervalo se resuelve, el CPA no va a decidir esa celda y hay que mirar el CIERRE. | `Ads/_TOOLS/decidir.py` · `PRODUCTOS/_PARAMETROS_DECISION.csv` |
| `UMBRAL_CONVERSACION_CLIC_ENLACE` | `35 %` | Porcentaje | **Clases 7 y 15 (Joaquín)** | MATAR POR CONVERSACIÓN: con 0 ventas acumuladas y ≥ `MINIMO_LINK_CLICKS_CONVERSACION` clics de enlace, una conversación por clic-enlace bajo esto es problema anuncio→bot y se apaga **sin esperar el PD**. Se mide sobre `link_clicks` de `_FACT_ENTREGA_ANUNCIO.csv` (export de Meta), **nunca** sobre los clics totales de LucidSales, que dan 5-13 % hasta en ganadores. | `Ads/_TOOLS/decidir.py` · `PRODUCTOS/_PARAMETROS_DECISION.csv` |
| `MINIMO_LINK_CLICKS_CONVERSACION` | `30 clics` | Clics de enlace | Regla Operativa Sistema (09-sep-2026) | Piso para juzgar la conversación de una celda: con 30 clics al 35 % se esperan ≥ 10 chats; por debajo la proporción es ruido binomial y matar por conversación sería matar por azar. Mismo rol que `MINIMO_MENSAJES_COMPARAR_CIERRE`. | `Ads/_TOOLS/decidir.py` · `PRODUCTOS/_PARAMETROS_DECISION.csv` |
| `MAX_PAUSAS_POR_DIA` | `2 pausas` | Órdenes / producto / día | ESCALADO_PLAYBOOK §1.5 (GATE #1) / Calet | Como máximo se apagan esta cantidad de celdas por producto por corrida, las de mayor gasto primero; las demás quedan `PAUSAR_DIFERIDA` hasta mañana. *"El problema es cuando la gente apaga todo en un día malo y luego no sabe cuál creativo era el bueno."* Un enlace caído (hook muerto) nunca se difiere. | `Ads/_TOOLS/decidir.py` · `PRODUCTOS/_PARAMETROS_DECISION.csv` |
| `DIAS_MIN_COD_PAUSA_VENTAS` | `3 DÍAS` | Días con data | ESCALADO_PLAYBOOK §1.5 (~3 días COD) | MATAR POR VENTAS solo cuando la celda pasó su PD (1× BE) **y** lleva al menos estos días desde su primer día con data. El "0 ventas" de un conjunto de 2 días no es veredicto: antes se devuelve `TESTEO_ESPERA_COD`. | `Ads/_TOOLS/decidir.py` · `PRODUCTOS/_PARAMETROS_DECISION.csv` |
| `REZAGO_MAXIMO_DATA` | `2 DÍAS` | Días | CLAUDE.md invariante 13 | Si la última fecha con data está a más de esto de hoy, la orden se declara vieja arriba de todo y el flujo (`ciclo.datos`) manda recolectar antes de decidir. Una orden fechada hoy sobre data de hace una semana es el error de ventana del 06-sep-2026 disfrazado de frescura. | `Ads/_TOOLS/decidir.py` · `Ads/_TOOLS/flujo.py` · `PRODUCTOS/_PARAMETROS_DECISION.csv` |

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
| `UMBRAL_CIERRE_MINIMO_BOT` | **`15% a 20%`** (BENCHMARK, no gate) | Porcentaje | **Clases 16 y 22-ago (Calet)** | *"Primero el flujo, luego la estructura"*. Es una referencia de las clases del mentor, no una regla dura: ningún script bloquea por esto — quien sí bloquea es `PROHIBIDO_ESCALAR_CIERRE_BAJO` (bajo 10% no se debe escalar), fila aparte de esta tabla. La app muestra el cierre real (`cierre_pct` de `_DECISIONES.json`) junto a este rango cuando el contrato trae ambos. | `.claude/agents/ETAPA-11.md` · `PRODUCTOS/_PARAMETROS_DECISION.csv` → `cierre_meta_min_pct` · `cierre_meta_max_pct` |
| `TIEMPO_RESPUESTA_BOT` | `2 a 3 segundos` | Segundos | Clase 22 (Flujo) | Evitar fuga por espera en WhatsApp. | `.claude/agents/ETAPA-5.md` |
| `CONGRUENCIA_ANUNCIO_BOT` | `100% obligatoria` | Regla | **Clases 16 y 22-ago (Calet)** | El hook y la promesa del anuncio deben ser la primera línea del bot. | `CLAUDE.md` · `.claude/agents/ETAPA-11.md` |
| `ESTRUCTURA_BOT_ESCALADO` | `Flujo dedicado al ángulo ganador` | Estructura | Clase 22 / Joaquín | Paraguas para testear (Fase 1); dedicado para escalar (Fase 3). | `.claude/agents/ETAPA-11.md` |
| `FLUJO_ANTES_QUE_ESTRUCTURA` | **`El flujo se optimiza PRIMERO`** | Regla dura | **Clase 16-ago (Calet)** | *"al yo tener un flujo de venta, yo puedo colocar cualquier estructura y cualquier estructura me va a vender. Pero si yo tengo un mal flujo o un flujo desoptimizado, cualquier estructura que ustedes coloquen no les va a funcionar. Porque el tráfico va igual."* Ninguna estructura de campaña compensa un flujo malo. | `DOCTRINA/PLANTILLAS_FLUJO_BOT.md` · `.claude/agents/ETAPA-11.md` |
| `PROHIBIDO_ESCALAR_CIERRE_BAJO` | **`No escalar bajo 10 %`** | Regla dura | **Clase 22-ago (Calet)** | *"Uno no puede escalar algo. Si uno tiene un cierre de cinco, uno escala y va a escalar malos resultados… el cierre más bajo, las ventas van a ser bajas, el CPA se va a subir."* Escalar un cierre malo escala el error, no las ventas. | `.claude/agents/ETAPA-7.md` · `.claude/agents/ETAPA-11.md` |
| `PALANCA_1_DEL_CIERRE` | **`PROPUESTAS DE VALOR`** | Regla dura | **Clase 22-ago (Calet)** | Respuesta directa a *«¿en qué te centrás para optimizar el flujo?»*: *"lo que yo más me centro es en las propuestas de valor, en las imágenes, colocarle muchas propuestas de valor, atacando todo, resaltando lo que van a recibir, venderle el resultado."* No los hooks ni los testimonios. Fórmula: problema concreto → qué hace el producto → resultado. | `DOCTRINA/PLANTILLAS_FLUJO_BOT.md` · `.claude/agents/ETAPA-5.md` · `.claude/agents/ETAPA-11.md` |
| `DIAGNOSTICO_1_DEL_CIERRE` | **`Congruencia anuncio ↔ flujo`** | Regla dura | **Clases 16 y 22-ago (Calet)** | *"si tú tienes un cierre bajo, uno empieza a analizar: qué anuncio está llegando, ver si ese anuncio concuerda con lo que tengo en el flujo."* · *"el ángulo del flujo no está muy encaminado al hígado graso… la gente llega y ahí pierde la emoción de comprar."* Se verifica ANTES de reescribir copy. | `.claude/agents/ETAPA-11.md` |
| `VELOCIDAD_CAMBIO_DE_FLUJO` | **`HORAS, no semanas`** | Latencia | **Clase 22-ago (Calet)** | *"optimizás en la mañana y ya al mediodía van a llegar más ventas, el cierre te va a subir."* Por eso todo cambio se anexa como `CAMBIO_BOT` a `_EVENTOS.csv` **el día que se aplica**: sin la fecha no hay forma de saber qué lo movió. | `PRODUCTOS/_EVENTOS.csv` · `.claude/agents/ETAPA-11.md` |
| `TEXTO_FIJO_DEL_BOT` | **`DECLARADO, no escrito`** | Regla dura | Data propia (NIVEL 4) · estructura base CLEARSTEM | El texto idéntico entre productos es **literal en la plantilla y no se reescribe por producto**. Tres notaciones con una forma cada una: `{{variable}}` de CSV (bloquea si falta), `<<BLOQUE:x>>` de `etapa-5`, y `>>` = instrucción que nunca se pega. Un texto fijo que varía entre productos es una variable de confusión que vuelve inauditable el cierre. | `DOCTRINA/PLANTILLAS_FLUJO_BOT.md` · `Ads/_TOOLS/gen_flujo_bot.py` · `Ads/_TOOLS/test_gen_flujo_bot.py` |
| `MERCADO_DEL_FLUJO` | **`GT (voseo) · CO (tuteo)`** | Enum | Data propia — portafolio 16-sep-2026 | El voseo chapín, GINTACOM/FORZA y «municipio y departamento» son del **mercado GT**, no doctrina universal. Un producto que factura en COP corre en tuteo neutro con su propia transportadora. | `PRODUCTOS/_DIM_MERCADOS.csv` · `Ads/_TOOLS/gen_flujo_bot.py` |
| `DIAS_GARANTIA` | **`90 días`** | Días | Operador (17-sep-2026) | Plazo único del portafolio, igual en los tres escalones. **Prohibido escalonar por tier:** dos plazos distintos en el mismo flujo es una oferta que nadie autorizó, y en contraentrega el reembolso no es un detalle de copy. `gen_flujo_bot.py` lo rechaza. | `DOCTRINA/PLANTILLAS_DEFAULTS_OPERADOR.md` · `Ads/_TOOLS/gen_flujo_bot.py` |
| `CIERRE_LO_EXPLICA_EL_ANGULO` | **`variación medida 2.5×`** | Hallazgo | Data propia (NIVEL 4) — `_ESTADO_ANGULOS.csv` | **Con el MISMO bot, el cierre varía por ángulo más que entre productos:** de 20.8 % a 8.2 % dentro de un producto. El texto del bot es constante en esa comparación. **Corolario:** fijar el texto no sube el cierre por sí solo — lo vuelve **medible**, que es la condición para que `UMBRAL_CIERRE_MINIMO_BOT` signifique algo. El mejor ángulo del portafolio ya está dentro del 15-20 %. | `.claude/agents/ETAPA-11.md` · `Ads/_TOOLS/perfilar_angulos.py` |

---

## 14. VARIABLES DE OPTIMIZACIÓN CONTINUA (CICLO DE VIDA DEL ÁNGULO)

> **Qué gobiernan.** `decidir.py` contesta *«¿qué hago hoy con esta celda?»* sobre una ventana
> móvil. Estas variables contestan la otra mitad: *«¿qué ha sido este ángulo a lo largo de su
> vida, en qué punto está, y cuánto cuesta equivocarse al moverle la plata?»*. Las ejecuta
> `Ads/_TOOLS/perfilar_angulos.py`, que **consume** el veredicto del motor y no lo recalcula
> (invariante 13). Sus valores viven en `PRODUCTOS/_PARAMETROS_OPTIMIZACION.csv`.
>
> **La variable que manda sobre todas es `ELASTICIDAD_CPA_SURFING`, y hoy está SIN_MEDIR.**
> Mientras lo esté, el perfil **rankea y no ordena**: la orden sigue saliendo de `decidir.py`.

| Nombre de Variable | Valor Actual | Unidad | Fuente Vigente | Justificación | Archivo Ejecutor |
|---|---|---|---|---|---|
| `ELASTICIDAD_CPA_SURFING` | **`SIN_MEDIR`** | Factor | Backtest 09-sep-2026 · APR-057 | Cuánto empeora el CPA de una celda al subirle el presupuesto +20 %. **`_EVENTOS.csv` tiene 84 eventos y CERO `CAMBIO_PRESUPUESTO`**, así que nadie lo sabe. El backtest mide que con degradación 0 la política de pérdida esperada gana Q786 en 38 días, con +59 % (lo único medido, APR-057) empata, y con +80 % pierde. Sin este número, cambiar de política es apostar. | `PRODUCTOS/_PARAMETROS_OPTIMIZACION.csv` → `elasticidad_cpa_surfing` · `Ads/_TOOLS/backtest_politica.py` |
| `UMBRAL_PERDIDA_ESPERADA_DIA` | **`10 QUETZALES/DÍA`** | Quetzales | Regla operativa 09-sep-2026 | Tope de riesgo de un movimiento de presupuesto: `E[(1 − BE·λ/gasto)+] × Δ`. Es lo que reemplaza a la parálisis del IC — con 6 ventas el intervalo cruza el break-even casi siempre, pero la pérdida esperada puede ser Q3/día contra Q40/día de ganancia. Q10 ≈ 10 % del break-even mediano del portafolio. | `Ads/_TOOLS/perfilar_angulos.py` |
| `PROBABILIDAD_MINIMA_RENTABLE` | **`0.80`** | Proporción | Regla operativa 09-sep-2026 | `P(CPA ≤ BE)` mínima para autorizar subir presupuesto. Deliberadamente más laxa que el 0.975 implícito en el IC 95 % de dos colas: subir 20 % es reversible al día siguiente y su costo está acotado por el umbral de pérdida. Exigirle la evidencia de una decisión irreversible es lo que produce la parálisis. | `Ads/_TOOLS/perfilar_angulos.py` |
| `PROBABILIDAD_MAXIMA_APAGAR` | **`0.20`** | Proporción | Regla operativa 09-sep-2026 | Espejo del anterior: bajo esta probabilidad de ser rentable, el perfil entra en la cola de apagado. **No emite la orden** — pausar sigue saliendo solo de `decidir.py`. | `Ads/_TOOLS/perfilar_angulos.py` |
| `DIAS_SIN_GASTO_DORMIDO` | **`3 DÍAS`** | Días | Caso VARICOSE 03-sep-2026 | Un ángulo sin gasto no rinde mal: no está corriendo, y su CPA viejo contamina el promedio. | `Ads/_TOOLS/perfilar_angulos.py` |
| `DIAS_SIN_GASTO_APAGADO` | **`14 DÍAS`** | Días | `VENTANA_EVALUACION_DIAS` | Se ata al largo de la ventana de evaluación: pasado ese punto la celda ya no aparece en ninguna ventana del motor, así que sostenerla viva declara un estado que ninguna data respalda. | `Ads/_TOOLS/perfilar_angulos.py` |
| `PORCENTAJE_EXPLORACION_GASTO` | **`15 %`** | Porcentaje | Aritmética del sistema 09-sep-2026 | Porción del gasto diario del producto reservada a brazos sin historia. A $2.99-6/día por conjunto, menos del 10 % no alcanza para que un brazo nuevo llegue a su presupuesto de decisión (1×BE) en menos de dos semanas; más del 20 % le saca al ganador el volumen que sostiene la caja. | `Ads/_TOOLS/perfilar_angulos.py` |
| `MINIMO_ANGULOS_VIVOS` | **`2 ÁNGULOS`** | Ángulos | Regla de riesgo de cartera | Perfiles en `ESCALANDO` o `SOSTENIDO` por producto antes de declarar dependencia de un solo público. Con uno solo, su fatiga es la muerte del producto. Dispara generación de variantes **aunque el único ángulo vivo esté rindiendo bien**. | `Ads/_TOOLS/perfilar_angulos.py` |
| `HORIZONTE_EVALUACION_ORDEN` | **`7 DÍAS`** | Días | Clase 11 (CPA semanal) | Ventana posterior con la que se evalúa si una orden de escalado fue correcta. Cubre el ciclo semanal completo (la doctrina lee CPA semanal, nunca de un día suelto) y cabe dentro de los 10 días de maduración COD. | `Ads/_TOOLS/backtest_politica.py` |
| `MINIMO_VENTAS_ATRIBUCION` | **`5 VENTAS`** | Ventas | APR-004 · ETAPA-10 | Piso de evidencia por nivel de un eje para leer causalidad. Bajo 5 ventas el intervalo del CPA es de ±113 % a ±196 % y cualquier ranking es ruido de Poisson. | `PRODUCTOS/_PARAMETROS_OPTIMIZACION.csv` → `min_ventas_atribuir` · `.claude/agents/ETAPA-10.md` |
| `MINIMO_CREATIVOS_ATRIBUCION` | **`2 CREATIVOS`** | Creativos | ETAPA-10 · `atribuir.py` | Mínimo de piezas distintas por nivel para que la lectura sea del EJE y no de una sola pieza. Con un solo creativo, ese CPA describe esa pieza dentro de ese ángulo. | `PRODUCTOS/_PARAMETROS_OPTIMIZACION.csv` → `min_creativos_atribuir` · `.claude/agents/ETAPA-10.md` |

---
---

# PARTE III — PROTOCOLO DE INGESTA DE NUEVA CLASE (PASO A PASO)

Cuando asistas a una nueva clase o recibas una transcripción:

1. **Guardar la transcripción:**
   Guardar el archivo como: `C:\Users\juand\Documents\VITALCOM_CLASES\Clase YYYY-MM-DD - Tema (Instructor).txt`
   (T9, 22-sep-2026: las clases salieron del repo; el protocolo de ingesta no cambia).

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

