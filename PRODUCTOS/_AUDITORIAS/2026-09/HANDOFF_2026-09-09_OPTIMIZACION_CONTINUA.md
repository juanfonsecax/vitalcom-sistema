# HANDOFF — La capa de optimización continua

**Fecha:** 2026-09-09 · **Sesión 2 de 2** (la sesión 1 entregó el flujo declarado:
`HANDOFF_2026-09-09_FLUJO_DECLARADO.md`) · **Diseño completo:**
`_ROADMAP/PROPUESTA_OPTIMIZACION_CONTINUA_2026-09-09.md`.

**Todo lo que se afirma acá está medido con un comando que se puede volver a correr.**

---

## LO QUE SE DECIDIÓ, Y POR QUÉ

**El sistema no necesita un bandit todavía. Necesita registrar `CAMBIO_PRESUPUESTO`.**

Se construyó la política de asignación por pérdida esperada + Thompson Sampling, se corrió en
retrospectiva sobre 38 días reales, y **el propio backtest dice que no conviene activarla
todavía**:

| degradación del CPA al subir +20 % | ventaja de la política nueva sobre `decidir.py` |
|---|---|
| 0 % (el supuesto de la doctrina del surfing) | **Q+786** en 38 días |
| **+59 %** — el único punto que el sistema midió (APR-057) | **Q+17** — empate |
| +80 % | **−Q135** — peor |

Y ese parámetro **no se puede medir hoy**: `_EVENTOS.csv` tiene 84 eventos y **cero** de tipo
`CAMBIO_PRESUPUESTO`, aunque el surfing +20 % sea la palanca diaria por default de la doctrina.

Por eso la capa se entrega **rankeando y no ordenando**, con el freno declarado como parámetro
(`elasticidad_cpa_surfing = SIN_MEDIR`). La orden sigue saliendo de `decidir.py` — invariante 13
intacto.

---

## LO QUE SE CONSTRUYÓ

| Pieza | Qué es | Gate que la cubre |
|---|---|---|
| `Ads/_TOOLS/perfilar_angulos.py` | **El perfil de ángulo y su ciclo de vida.** Le da identidad e historial propio a cada `(producto, angulo_key)` y deriva su estado: `EN_PRUEBA · MIDIENDO · ESCALANDO · SOSTENIDO · EN_DECLIVE · RENOVADO · DORMIDO · APAGADO · APAGADO_ABANDONO`. Cada transición es un predicado sobre data. **Consume** el veredicto de `decidir.py`; no lo recalcula | `test_perfilar_angulos.py` — 17 comprobaciones |
| `PRODUCTOS/_ESTADO_ANGULOS.csv` | 17 perfiles, 30 columnas. Derivado, nunca escrito a mano. `flujo.py` lo lee con sus predicados `csv` / `csv_campo` **sin extender su vocabulario cerrado** (probado en vivo, ver abajo) | escrito con `csv.DictWriter` (invariante 11) |
| `Ads/_TOOLS/backtest_politica.py` | Camina día a día y hace decidir a las dos políticas con la data de ESE día, llamando a la propia `decidir.evaluar_celda()`. Evalúa cada orden contra el CPA realizado a 7 días, con curva de sensibilidad | reproducible: `--sensibilidad --eventos` |
| `PRODUCTOS/_PARAMETROS_OPTIMIZACION.csv` | 11 parámetros con `dueno` y `por_que`. Incluye los dos pisos de evidencia que vivían en la prosa de `ETAPA-10.md` | `verificar_guia_madre.py`, extendido para cubrir también este CSV (drift inverso incluido) |
| `DOCTRINA/GUIA_MADRE_PARAMETRIZADA.md` §14 | 11 filas nuevas | 78 variables declaradas · **32 verificadas** (antes 67 · 21) |
| `Ads/_TOOLS/atribuir.py` | Extendido: la banda pasa de `±1σ` al **IC 95 % del propio motor**, y un gate de integridad al frente | corre en cada lectura |
| `VISTAS/PERFILES.html` + `_MANIFIESTO.json` v6 | Vista `perfiles` declarada en la sección «decisiones», justo después de «Decisiones & Fatiga» | `gen_app.py --verificar` |

---

## LO QUE SE MIDIÓ (tres hallazgos de integridad y dos correcciones de método)

### 1. Las ventanas `CONTROL` se están sumando — y por doctrina no suman

`DATA_PLAYBOOK.md`: `BASE` suma, `CONTROL` solapa a propósito y **nunca** suma (APR-020 la usa
como prueba anti-doble-conteo). Cuatro consumidores no filtran:

| Archivo | Dónde | Qué contamina |
|---|---|---|
| `sembrar_anuncios.py` | línea 78 | `_DIM_ANUNCIOS.csv` → toda la lectura de causalidad |
| `flujo.py` | 532 `_angulos_acumulados` | gate de entrada a **FASE 2** |
| `flujo.py` | 587 `_ev_concepto_2de2` | gate de entrada a **FASE 3** |
| `warehouse/models/staging/stg_ventas.sql` | ni selecciona la columna | `fct_conjunto_dia`, `fct_anuncio_dia` |
| `decidir.py` | SQL de `cargar_datos_duckdb` | el acumulado (`ventas_acum`, `%PD`, guarda de ganador) |

Los generadores financieros **sí** filtran, así que el P&L está limpio.

**Tamaño:** 904 ventas contra 506 reales (+79 %), y **desigual**: NUSAVA +100 %, VARICOSE
+145 %, CLEARSTEM +59 %, TINNIDROP +69 % — no se cancela al comparar niveles.

**Lo que NO rompe (para no exagerarlo):** las ventanas `CONTROL` viven solo entre el 21-jul y
el 10-ago y **hay cero dentro de la ventana de decisión vigente**. Se corrió `decidir.py` con y
sin ellas: **las órdenes de hoy son idénticas.**

**Lo que SÍ rompe:** el acumulado, los dos gates de fase y la atribución histórica. Caso
concreto: **`NUSAVA/MEMORIA` tiene 0 filas BASE**; sus 7 ventas son 100 % `CONTROL`, y `flujo.py`
lo lista hoy como ángulo ganador. *(NUSAVA igual entra a FASE 2 por ARDOR, así que el veredicto
de fase no cambia — pero el ángulo que se coronaría sí podría.)*

> **No se tocó nada.** `flujo.py` es de la sesión 1 y `decidir.py` cae bajo el invariante 13.
> Lo que se hizo fue volverlo **visible en el punto de uso**: el gate al frente de `atribuir.py`
> y la columna `ventas_control` del perfil. El arreglo son ~4 líneas — decisión del operador,
> pregunta 1 de la propuesta.

### 2. Un ángulo fantasma: `GTR0_TINNIDROP_NOCHES-SIN-DORMIR_R1`

Aparece en `_FACT_VENTAS.csv` ($17.22, 6 ventas) y **no tiene fila en `_DIM_CONJUNTOS.csv`**
(la grafía con sufijo `+25AÑOS` sí la tiene: el conjunto se renombró y nadie anexó la nueva).
Sus ventas se cuentan como un ángulo aparte en vez de sumar a `NOCHES_SIN_DORMIR` — y `flujo.py`
lo reporta hoy como el tercer «ángulo ganador» de TINNIDROP, mientras `NOCHES_SIN_DORMIR` figura
`DORMIDO`. Un ángulo compitiendo contra sí mismo. `perfilar_angulos.py` lo canta en cada corrida.

### 3. Los cinco ángulos más grandes del portafolio tienen la banda de edad mezclada

`decidir.py` ya calculaba `banda_ok` contra `_DIM_BANDAS.csv`, pero nadie lo estaba leyendo como
propiedad del ÁNGULO. Al perfilar, **6 de 17 perfiles tienen réplicas en bandas distintas**, y son
los de mayor volumen:

| perfil | estado | ventas acum | CPA acum |
|---|---|---|---|
| TINNIDROP · PERDIDA_AUDITIVA | ESCALANDO | 97 | Q62.7 |
| TINNIDROP · DETERIORO_COGNITIVO | SOSTENIDO | 89 | Q51.3 |
| NUSAVA · ARDOR | SOSTENIDO | 69 | Q58.1 |
| CLEARSTEM · RESISTENCIA_INSULINA_SOP | ESCALANDO | 62 | Q36.5 |
| CLEARSTEM · MEDICOS_FALLARON | ESCALANDO | 36 | Q61.2 |
| TINNIDROP · NOCHES_SIN_DORMIR | DORMIDO | 12 | Q57.1 |

APR-060 midió 15× de diferencia de CPA entre bandas en el **mismo** ángulo, producto y creativo, y
la llama «la variable más cara del sistema». Cada uno de esos CPA es el promedio de dos poblaciones
que rinden muy distinto. **No invalida las órdenes** —la bandera ya existía y APR-063 muestra que
el operador la usa—, pero **separar la banda tiene más valor esperado que cualquier refinamiento de
la política de asignación, y a costo cero**: es configuración en Meta, no plata.
`perfilar_angulos.py` lo canta por producto en cada corrida.

### 4. Dos correcciones de método que la medición forzó

- **El «descuento por entrega» no se implementó, y no es un olvido: sería contarlo dos veces.**
  `cpa_be_q` ya está expresado por venta registrada con la tasa de entrega del producto
  descontada. Y el retraso de 10 días es ad→**cobro**, no ad→venta: se midió la correlación
  `gasto(t)` vs `ventas(t+k)` para k=0..5 sobre las 28 fechas con ventana diaria limpia, y **no
  hay lag detectable** (TINNIDROP 0.29 → 0.37 con SE≈0.19; CLEARSTEM y NUSAVA, ruido). Lo que sí
  falta es la tasa de entrega **por ángulo**, que hoy no existe.
- **La banda `±1σ` de `atribuir.py` declaraba ganadores que el IC 95 % no sostiene.** El ejemplo
  que `PARAMETRIZACION_ADS` §5 publica como *«DIFERENCIA REAL»* pasa a **EMPATE ESTADÍSTICO**
  (ACCESIBILIDAD_MEDICO: 32-40 → **29-44**).

---

## LO QUE EL PERFIL DICE HOY (2026-09-09, data hasta 07-sep, rezago 2 d)

```bash
python Ads/_TOOLS/perfilar_angulos.py
```

| Producto | Perfiles | Vivos | Lectura |
|---|---|---|---|
| **TINNIDROP** | 6 | 4 | `PERDIDA_AUDITIVA` se lleva el **51 % del gasto** con `P(ser el mejor) = 0.00`; `ACCESIBILIDAD_MEDICO` tiene el mejor CPA acumulado (Q39.3) con el 21 %. `NOCHES_SIN_DORMIR` DORMIDO hace 6 días |
| **CLEARSTEM** | 6 | 3 | `ANTI_FALSIFICACION` `P(mejor)=0.85` con el 22 % del gasto; `MEDICOS_FALLARON` `P(mejor)=0.00` con el 38 % |
| **NUSAVA** | 1 | **1** | 🔴 **DEPENDENCIA DE UN SOLO PÚBLICO** (ARDOR). Si fatiga, no hay a dónde mover la plata |
| **VARICOSE** | 4 | **0** | Todo `APAGADO_ABANDONO`, consistente con su estado PAUSADO — ahora con evidencia en vez de memoria |

**La plata no está donde está la probabilidad**, y hasta hoy nada lo decía en una pantalla.

---

## VERIFICADO (comandos, no lectura)

| Gate | Resultado |
|---|---|
| `python Ads/_TOOLS/test_perfilar_angulos.py` | **17 de 17** · exit 0 |
| `python Ads/_TOOLS/test_decidir.py` | 11 de 11 · exit 0 (sin cambios: `decidir.py` no se tocó) |
| `python Ads/_TOOLS/test_flujo.py` | 17 de 17 · exit 0 (sin cambios: `flujo.py` no se tocó) |
| `python Ads/_TOOLS/verificar_guia_madre.py` | exit 0 · 78 declaradas, **32 verificadas**. Probado que **muerde**: se desincronizó `min_angulos_vivos` a propósito y falló señalando línea y archivo |
| `python Ads/_TOOLS/gen_app.py --todo` | exit 0 · 6 vistas · 5 generadores, 0 con error |
| `python Ads/_TOOLS/flujo.py --validar` · `validar_parametros.py` | exit 0 |
| `python Ads/_TOOLS/gen_grafo.py --comparar` | **arranque en frío y los 4 techos por fase: idénticos (`=`)**. Inventario 33 → 35 CSV, **cero huérfanos**: los dos nuevos tienen consumidor declarado |
| `python Ads/_TOOLS/backtest_politica.py --sensibilidad --eventos` | 481 decisiones en 38 días; reproducible |
| **Interfaz con la sesión 1** | Probada en vivo contra `flujo.evaluar()`, no supuesta: `{"tipo":"csv","csv":"_ESTADO_ANGULOS.csv","where":{"producto_key":"{pk}","estado":["ESCALANDO","SOSTENIDO"]},"min":2}` devuelve `True 4 filas` (TINNIDROP), `True 3` (CLEARSTEM), `False 1` (NUSAVA), `False 0` (VARICOSE). **Cero cambios al vocabulario cerrado de predicados** |

**Costo en tokens de sesión de toda la capa: cero.** No se agregó prosa a ninguna skill ni a
ningún agente.

---

## LO QUE QUEDA (en orden de importancia)

1. **Registrar `CAMBIO_PRESUPUESTO` en `_EVENTOS.csv`.** Es la deuda que bloquea a todas las
   demás: sin ella no se puede medir `elasticidad_cpa_surfing`, y sin ese número la política de
   asignación no se puede activar ni descartar con data. El esquema del CSV ya sirve
   (`valor_antes` / `valor_despues`); con ~30 eventos alcanza. **Falta decidir quién la escribe**
   (operador a mano vs. la sesión al ejecutar por MCP) — pregunta 2 de la propuesta.
2. **Decidir el arreglo de `rol_ventana = BASE`** en los 4 consumidores. ~4 líneas; cambia el
   acumulado de todos los ángulos y los dos gates de fase. Toca archivos de la sesión 1 y el
   motor: **no se hizo sin autorización**.
3. **Separar la banda de edad** en los 6 perfiles mezclados. Es la acción de mayor valor esperado
   de toda esta lista y **no cuesta plata**: es configuración en Meta más una fila en
   `_DIM_BANDAS.csv`. Mientras siga así, el CPA de los cinco ángulos más grandes promedia dos
   poblaciones que APR-060 midió rindiendo 15× distinto.
4. **Anexar la grafía huérfana** de `GTR0_TINNIDROP_NOCHES-SIN-DORMIR_R1` a `_DIM_CONJUNTOS.csv`
   con el mismo `angulo_key`, o registrarla en `_ALIAS_CONJUNTOS.csv`.
5. **El mart `fct_angulo_dia`** en dbt, con sus 3 tests (SQL propuesto en §9.2). Requiere el
   punto 2 primero, o nace con el doble conteo adentro.
6. **La tasa de entrega por ángulo** (§9.3): depende de si Dropi recibe alguna referencia del
   anuncio desde LucidSales. Es una pregunta para el operador.
7. **Nada se commiteó.** `git status` lista 7 modificados y 7 nuevos.

---

## LO QUE NO SE TOCÓ, A PROPÓSITO

`DOCTRINA/FLUJO.json` · `Ads/_TOOLS/flujo.py` · las skills de fase (son de la sesión 1) ·
`Ads/_TOOLS/decidir.py` y sus reglas (invariante 13) · `sembrar_anuncios.py` ·
`warehouse/models/` · ningún CSV de hechos.
