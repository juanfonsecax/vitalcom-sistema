# HANDOFF — El flujo declarado y el reglamento único

**Fecha:** 2026-09-09 · **Sesión 1 de 2** (la sesión 2 tiene su prompt en
`_OPERADOR/PROMPT_SESION_OPTIMIZACION_2026-09-09.md`) · **Todo verificado con gates, nada por lectura.**

---

## LO QUE SE DECIDIÓ (con el operador, en el chat)

1. El runner **dicta**; la sesión ejecuta en Meta por MCP **solo con confirmación explícita por orden**, y verifica después contra Meta.
2. La pregunta inicial «¿En qué fase estás hoy?» **desaparece**: la fase la deriva la data.
3. **Un solo reglamento**: los umbrales que vivían en prosa (35 % conversación, PD + ~3 días COD, máx 2 pausas, +20 %) pasan a `_PARAMETROS_DECISION.csv` y `decidir.py`; ETAPA-8 consume `_DECISIONES.json`.
4. El worktree viejo de `.claude/worktrees/` se retira (su único diff útil se portó).

## LO QUE SE CONSTRUYÓ

| Pieza | Qué es | Gate que lo cubre |
|---|---|---|
| `DOCTRINA/FLUJO.json` | El grafo declarado: 3 fases, 20 nodos, 1 excepción. Cada nodo con ejecutor (subagente / skill / script / operador / mcp), `requiere`, `produce`, `avisos`; cada fase con gate de entrada y de salida. Los números con dueño se citan (`@param:` / `@publicacion:`), no se copian | `flujo.py --validar` (y el hook lo corre al tocar el JSON) |
| `Ads/_TOOLS/flujo.py` | El recorrido: sitúa cada producto (fase por gate de entrada, nodo = primer paso sin artefactos), lista bloqueantes con dueño, avisos y órdenes del motor. Vocabulario **cerrado** de 16 predicados. Escribe `PRODUCTOS/_FLUJO.json`, `PRODUCTOS/_ESTADO_FLUJO.csv` y registra `TRANSICION_FLUJO` en `_EVENTOS.csv` cuando un producto cambia de nodo | `Ads/_TOOLS/test_flujo.py` — 17 comprobaciones |
| `Ads/_TOOLS/_fixtures/flujo_20260908/` | El caso del 08-sep congelado (solo TINNIDROP, hasta el 07-sep, `ad_id` en blanco). El test exige que los **cuatro hallazgos** salgan solos | idem |
| `Ads/_TOOLS/flujo_html.py` → `VISTAS/FLUJO.html` | La vista «estás acá · esto bloquea · esto sigue» + el grafo en mermaid renderizado desde el mismo JSON. Declarada en `_MANIFIESTO.json` v5 como **vista inicial** de la app | `gen_app.py --verificar` |
| `decidir.py` (reglamento único) | 8 parámetros nuevos en `_PARAMETROS_DECISION.csv`: `min_ventas_ganador`, `min_ventas_escalar`, `rezago_max_dias`, `umbral_conv_clic_enlace_pct`, `min_link_clicks_conv`, `max_pausas_por_dia`, `surfing_pct`, `dias_min_cod_pausa_ventas`. Regla nueva `PAUSAR_CONVERSACION_FLOJA` (sobre `link_clicks` de `_FACT_ENTREGA_ANUNCIO.csv`, nunca sobre los clics totales de LucidSales), guarda COD antes de matar por ventas (`TESTEO_ESPERA_COD`), tope de pausas (`PAUSAR_DIFERIDA`), surfing parametrizado | `test_decidir.py` — 11 casos (5 nuevos) · `verificar_guia_madre.py` — 21 valores verificados (8 nuevos) |
| Hooks | `hook_csv.py`: valida `FLUJO.json` al tocarlo (bloquea), regenera el flujo tras cada CSV o `_PLAN*.json`, y el gate del texto madre también se dispara al tocar `decidir.py` | — |
| `ciclo_hoy.py` | Paso 2 = `flujo.py --todo` (motor → flujo → lanzador → app) | — |

## LO QUE CAMBIÓ EN LA DOCTRINA

- `CLAUDE.md`: sección **ARRANQUE DE SESIÓN — LA FASE LA DICE LA DATA** reemplaza la pregunta inicial; fila del flujo en «cómo corre» y en el MAPA; regla de invocación «correr `flujo.py` antes de cargar una skill»; invariante 13 con la confirmación por orden para MCP.
- Skills `fase-1-angulos`, `fase-2-conceptos`, `fase-3-escalado`: los checklists de «verificación obligatoria» salen de la prosa y quedan como puntero al JSON. Sus `description` ya no citan una pregunta inicial. `ciclo-diario`: los tres nodos del ciclo y `ciclo_hoy.py`.
- `ETAPA-8.md`: consume `_DECISIONES.json`; sin cascada numérica propia; la ejecución es por MCP con confirmación.
- `ETAPA-7.md`: «Umbrales» y «Reglas de decisión» pasan a punteros al motor; conserva integridad, confusión, sangrado, dimensión, saturación.
- `ESCALADO_PLAYBOOK.md` §1.5 y §8: puntero a los valores vigentes del CSV.
- `GUIA_MADRE_PARAMETRIZADA.md`: 5 filas nuevas, 4 actualizadas (surfing una vez al día, C-02).

## LO QUE SE RETIRÓ (nada se borró; todo está en `_ARCHIVO/retirado_20260909/`)

- `decidir_operativo.py` (wrapper sin llamadores), tres `.bak` que vivían junto a la fuente de verdad.
- El worktree `.claude/worktrees/competent-rhodes-3ebc55` (copia completa del repo, rama sin commits): se portó su fix de encoding en `gen_dashboard.py` y se eliminó con su rama.
- `README.md`: 16→17 etapas, 7→10 skills, puntero al flujo.

## LO QUE EL FLUJO DICE HOY (2026-09-09)

| Producto | Fase | Nodo actual | Qué sigue |
|---|---|---|---|
| TINNIDROP | F2 (por VENTA) | `F2.etapa-11` | etapa-11 → CAMBIO_BOT. Avisos: 5/10 conceptos, plan en esquema lean, estructura publicada 5×1 ≠ doctrina, Meta ya gastó $23.61, objetos de F3 sin gate |
| NUSAVA | F2 (histórico ARDOR 130v) | `F2.etapa-11` | idem; ningún concepto generado todavía |
| CLEARSTEM | F2 | `F2.conceptos` | 5/10 GENERADO + 4 PENDIENTE_GENERAR → etapa-9 / etapa-render |
| VARICOSE | PAUSADO | — | reingreso solo por decisión explícita |
| D3+K2 · Repelente · OVULOS | F1 | `F1.congelar_inputs` | falta `costo_q` (y transcripciones en Repelente) |
| SERUM_COLAGENO_BOTOX | F1 | `F1.congelar_inputs` | 0 transcripciones en disco: el paquete se armó sin ellas |

## MEDIDO

- `gen_grafo.py --comparar` contra la línea base de la mañana: arranque en frío **+471 tokens**
  (10 283 → 10 754) por la sección de arranque y las dos filas nuevas; techos por fase F1 +6.3k,
  F2 +8.2k (las skills ahora nombran `publicar-meta` y el modelo de costo cuenta cada doc citado),
  F3 −1.6k, ciclo −3.1k. **No bajó como decía la propuesta**: bajó la prosa de gates, subió la
  prosa de punteros. Recortar más es decisión del operador sobre su doctrina.
- `--estricto` sigue en exit 1 por el mismo hallazgo de siempre: `etapa-render` en `sonnet` (a propósito).

## DEUDAS ABIERTAS

1. **`gen_fase2_lean.py` y `sincronizar_planes.py` producen planes `fase2_lean/1`** (5 conjuntos × 1 concepto, 1 campaña) que contradicen `_PARAMETROS_PUBLICACION.csv` (1-1-5 + 1-1-5 + 1-2-5). El flujo lo canta como aviso en TINNIDROP y CLEARSTEM. Decidir cuál es la doctrina de FASE 2 y retirar el otro: **no se tocó** porque es una decisión de método, no de sistema.
2. `_DIM_PRODUCTOS.fase` sigue escribiéndose a mano (bitácora). La fase vigente es `_ESTADO_FLUJO.csv`. Cuando `gen_lanzador.py` / `gen_dashboard.py` la lean, deberían leer el CSV derivado.
3. El gate «segunda cuenta para la campaña C» y «un solo producto en FASE 2 por semana» siguen en prosa (fase-2): son criterio de portafolio, no cabían en el vocabulario sin un predicado de rango de fechas.
4. El `--todo` corre `verificar_producto.py` y `gen_publicacion.py` por producto (unos segundos). Si molesta en el hook, se puede pasar `--sin-scripts` ahí y dejar los scripts para `ciclo_hoy.py`.
5. Nada se commiteó: el operador no lo pidió. `git status` lo lista todo.
