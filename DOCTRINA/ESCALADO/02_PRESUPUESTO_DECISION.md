## 1.5 PRESUPUESTO DE DECISIÓN — cuánto debe gastar un conjunto antes de que "0 ventas" cuente

> **Los valores vigentes viven en `PRODUCTOS/_PARAMETROS_DECISION.csv` y los ejecuta `Ads/_TOOLS/decidir.py`**
> (`umbral_conv_clic_enlace_pct`, `min_link_clicks_conv`, `max_pausas_por_dia`, `dias_min_cod_pausa_ventas`,
> `factor_tolerancia_pd`, `surfing_pct`). Este texto es la doctrina que los justifica; si difieren, manda el CSV
> y `verificar_guia_madre.py` lo canta. Desde el 09-sep-2026 ninguna etapa recalcula estos umbrales en prosa.

> **Por qué existe esta sección:** el sistema ya tenía los DÍAS (CALENDARIO) y la regla "gasto > Break-Even y 0 ventas → pausar" (§6), pero no CUANTIFICABA a $1.59 cuánto gasto/días necesita un conjunto para que su "0 ventas" sea un veredicto válido. Sin eso se mata a ganadores sub-testeados. Anclas: **Clase 5** (low-budget → esperar 2-3 días; "no apagar por un mal día, mirar el historial de 15 días"), **Clase 8** (Camilo: "tus productos tienen que venderte el primer día" y "gastó la mitad sin vender → apagar" — pero eso es a PRESUPUESTO ALTO), **Clase 11** (CPA SEMANAL/ponderado, no un día), + el **CPA Break-Even del costeo** (ETAPA-1).

**DOS SEÑALES QUE MADURAN A RITMOS DISTINTOS — no confundirlas:**

1. **CONVERSACIÓN (clics→chats): barata y RÁPIDA.** Confiable desde el **día 1-2** con poquísimo gasto. Es la señal para **matar temprano**: si un conjunto tiene **%conv/clic-enlace muy bajo** o **$/conversación caro** (trae clics pero no chats, o chats-morbo que no escriben) → problema de **anuncio/hook** → se apaga **sin esperar** a que gaste un Break-Even (Clase 20 "CTR bajo + caro → pausar"; Clase 8 "morbo que no vende → apagar").
   > **DEFINICIÓN NUMÉRICA de "conversación floja" (gate del criterio temprano — para que no sea a ojo):** al día 2-3, con **0 ventas**, se apaga por conversación si tiene ≥1 en rojo: (a) **%conv/clic-enlace <35%** 🔴 (el gate firme); (b) **CTR-enlace <1.5%** (hook débil — umbral ya usado en el sistema); (c) **$/conversación > 2× el del MEJOR conjunto de la misma campaña** (caro relativo y computable; no inventa un Q absoluto porque el costo varía por ticket/producto). El (a) es el principal; (b) y (c) refuerzan.

2. **VENTA / CPA: cara y LENTA.** El "0 ventas" **NO es veredicto** hasta que el conjunto acumuló **≥ 1 × CPA Break-Even de GASTO** *y* pasaron los **~3 días de maduración COD** (Guatemala). Debajo de ese umbral, cero ventas es estadísticamente esperable **hasta en un buen conjunto** — matarlo ahí es matar un ganador sub-testeado.

**EL PRESUPUESTO DE DECISIÓN (PD) — la cifra que faltaba:**
- **PD por CONJUNTO (piso para matar-POR-VENTAS) = 1 × CPA Break-Even.** Es el punto donde, si convirtiera al break-even, ya debería haber ≥1 venta. Debajo de eso NO se mata por ventas.
- A **$2.99/día (≈Q22.8)**, un conjunto tarda `Break-Even_Q ÷ 22.8` **días** en llegar a su PD — con 80% de entrega real son **3.3-4.3 días** según producto, lo que hace VÁLIDO el gate del día 3-5 de los mentores. (A $1.59 tardaba 5.0-6.5 días y el gate del día 3 llegaba con solo 46-60% del PD = decidir a ciegas.) Aun así, los perdedores se cortan por **CONVERSACIÓN** en el GATE del día 3 (más rápido y no depende de LucidSales), y solo se mata-por-ventas al que YA gastó su PD y sigue en 0 (el caso "buena conversación, 0 ventas" tipo ANIMO / ARAÑITAS).
- **PD de la CAMPAÑA (gate de definición) = 1 × Break-Even repartido entre los 6 conjuntos** = `Break-Even_Q ÷ (6 × 12.1)` días ≈ **1-3 días** → por eso el **GATE #1 cae en el día 3** (ya en el CALENDARIO): para entonces la campaña gastó ~1 Break-Even colectivo, suficiente para leer conversación + las primeras ventas de los ganadores.

**Tabla de PD por producto (a $2.99/día = Q22.8, tasa 7.62 · vigente desde 25-jul):**

| Producto | CPA Base Q | Break-Even Q (v2) | PD conjunto (1×BE) | Días @ $2.99 (entrega 0.8) | BE v1 (obsoleto) |
|---|---|---|---|---|---|
| VARICOSE 2x1 | 36.9 | **83.0** | Q83 | **4.6 días** | ~~Q79~~ |
| NUSAVA B12 | 31.3 | **76.9** | Q77 | **4.2 días** | ~~Q68.3~~ |
| TINNIDROP | 30.8 | **71.6** | Q72 | **3.9 días** | ~~Q60.5~~ |
| CLEARSTEM | 30.8 | **69.6** | Q70 | **3.8 días** | ~~Q60.5~~ |

> Los valores vivos están en `PRODUCTOS/_DIM_PRODUCTOS.csv` — esta tabla es el espejo legible. Si difieren, manda el CSV.

> ⚠️ **VARICOSE se costea por el PEDIDO, no por la unidad:** vende 2x1 (2 frascos de Q45 = Q90 de
> producto por pedido) → le toca la **fila Q90**, no la Q45. Historia de por qué esta tabla llegó a
> decir otra cosa y por qué el presupuesto subió de $1.59 a $2.99:
> `_CONOCIMIENTO/POSTMORTEMS/ESCALADO_PLAYBOOK_historias.md` §1.5. Aritmética completa del
> presupuesto en `DOCTRINA/CALENDARIO_ESCALADO.md` §1.5.

> **Lectura:** el **ganador se declara solo** vendiendo bajo Base en los primeros días (MA2 de Varicose vendió a Q11.6 con ~$6 de gasto). El **perdedor** se corta por conversación en el día 3; solo se espera a su PD completo si tiene BUENA conversación pero 0 ventas (ahí el problema es cierre/ángulo, no alcance). **Nunca** se mata por el CPA de UN día — siempre semanal/ponderado (Clase 11).

**REGLA OPERATIVA (la que ejecuta el operador y ETAPA-8):**
- **Día 1-2:** no tocar. Solo mirar clics-enlace / conversación.
- **Día 3 (GATE #1):** (a) ganadores = ya venden ≤ Base → optimizar flujo + surfing; (b) perdedores por conversación (%conv/clic-enlace <35% o $/conv caro) → apagar (máx 2); (c) buena conversación + 0 ventas → **seguir hasta 1×BE de gasto** antes de decidir.
- **Matar-POR-VENTAS** solo cuando el conjunto pasó su PD (1×BE) con 0 ventas y ~3 días COD cumplidos.

---

