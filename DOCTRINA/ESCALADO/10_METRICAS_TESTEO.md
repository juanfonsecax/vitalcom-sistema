## 8. MÉTRICAS DE EVALUACIÓN DE TESTEO (umbrales canónicos — fuente única)

> **Los valores vigentes viven en `PRODUCTOS/_PARAMETROS_DECISION.csv` y los ejecuta `Ads/_TOOLS/decidir.py`**
> (`umbral_conv_clic_enlace_pct`, `min_link_clicks_conv`, `max_pausas_por_dia`, `dias_min_cod_pausa_ventas`,
> `factor_tolerancia_pd`, `surfing_pct`). Este texto es la doctrina que los justifica; si difieren, manda el CSV
> y `verificar_guia_madre.py` lo canta. Ninguna etapa recalcula estos umbrales en prosa.

> **Este archivo es el dueño**: `etapa-6`, `etapa-7` y `etapa-8` leen los umbrales de acá, no los duplican. Sirven para diagnosticar por qué un ángulo gana o falla; el orquestador las interpreta antes de activar `etapa-3`. El operador entrega los datos de los 6 conjuntos en estos términos.

**Métrica 1 — % Conversación por Clic en Enlace** *(la más importante)* — `Conversaciones ÷ Clics × 100`
- < 35% → problema en el flujo del bot o incoherencia anuncio-bot (revisar `etapa-5`)
- 35–49% → bueno / escalable
- ≥ 50% (50–70%) → excelente y súper escalable

(Clase 7 + Clase 15, Joaquín)

**Métrica 2 — % Conversación por Impresión** — `Conversaciones ÷ Impresiones × 100`
- 1.5% malo · 2.5% bueno · 3.5% excelente · 4.5%+ extraordinario

**Métrica 3 — CPA real** — `Gastado ÷ Ventas confirmadas`. Comparar contra el CPA Break Even (`DOCTRINA/DATA_PLAYBOOK.md` §4). Si CPA real > CPA Break Even → ángulo no rentable.

**Métricas de atención (CPM / CPC / Frecuencia)** *(referencia de mercado, no umbral duro)*
- CPM (Colombia/COP): bueno 6,000–10,000 · ~10,000 menos saturado (trabajable) · 17,000–20,000+ ángulo saturado/competido. Varía por ticket: ticket bajo (<100k) → CPM más bajo. (Clase 7 + 15 + 22, Joaquín)
- CPC (Colombia/COP): ~150–250. (Clase 15 actualiza a ~150; Clase 7 daba 200–250.) Ecuador y USA mucho más caros.
- Frecuencia: ≥1.9 → fatiga creativa (renovar creativo, Clase 4) · 2–3 con CPM/CPC caro → apagar (Clase 7).

> ⚠️ Estos números son de **Colombia (COP)**. El sistema mide en la moneda local de cada mercado (GT: **Quetzales**, mercado nuevo y más barato, Clase 15). Usar como referencia cualitativa, no como umbral fijo en moneda local. Las métricas % (conversación por clic/impresión) y el CPA contra Break Even sí son la base de decisión.

**Diagnóstico rápido:**

| Síntoma | Causa probable | Dónde actuar |
|---|---|---|
| Muchos clics, pocos chats | Anuncio o plantilla de inicio de conversación | `etapa-4` / config. del chat |
| Muchos chats, pocas ventas | Incoherencia anuncio-bot o flujo débil | `etapa-5` |
| CPM muy alto | Ángulo saturado o copy similar a competencia | `etapa-2` / nuevo ángulo |
| % conversación por clic < 35% | Llegan al chat pero no escriben | Revisar plantilla de inicio preescrita |
