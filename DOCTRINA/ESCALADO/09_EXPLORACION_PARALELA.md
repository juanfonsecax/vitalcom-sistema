## 7b. EXPLORACIÓN DE ÁNGULOS NUEVOS MIENTRAS SE ESCALA (F3.exploracion, P12)

Decisión del operador, 22-sep-2026: escalar el ganador no significa dejar de buscar el próximo.
Mientras F3 escala, corre en PARALELO un mini-F1 FIJO de `exploracion_n_angulos`
(`_PARAMETROS_DECISION.csv`, default 3) ángulos que el producto **nunca probó** — misma
exclusión que `reingreso_f1.py`/`_angulos_probados()` — cada uno en su propio conjunto ABO al
presupuesto por-adset de FASE 1 (`_PARAMETROS_PUBLICACION.csv` fase=3 brazo=EXPLORACION), TODO
EN IMAGEN, medido por VENTA agregando por `angulo_key` exactamente como F1 (invariante 1).

- **Arranca solo cuando F3 es rentable** (decidir.py en ESCALAR con volumen mínimo) — nunca
  antes: explorar sin caja no es prudencia, es apostar el escalado. Gate declarado en
  `DOCTRINA/FLUJO.json`, nodo `F3.exploracion` (`requiere`), evaluado por `flujo.gate_nodo()`.
- **No compite con el escalado ni lo bloquea**: es paralela, como `F2.etapa-11`. No consume el
  presupuesto de la campaña `ESCALA-*`; es una campaña `EXPLORA` propia.
- **Un ganador de la exploración entra a F2 como cualquier otro ganador de F1**: el gate
  F1→F2 (`angulo_ganador`) no distingue de qué conjunto salió la evidencia — no hay un camino
  paralelo nuevo que mantener, solo más conjuntos alimentando el mismo gate.
- Ejecutor: `etapa-2` (fichas de los ángulos nuevos) → `etapa-6` (`_PLAN_EXPLORACION.json`) →
  `etapa-guardar-producto` → `publicar-meta` con `Ads/_TOOLS/gen_publicacion.py --fase 3
  --brazo EXPLORACION`.

---

