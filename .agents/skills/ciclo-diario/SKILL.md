---
name: ciclo-diario
description: CICLO DE OPTIMIZACIÓN post-lanzamiento. Recorre PRODUCTOS/_DIM_PRODUCTOS.csv y, por cada producto VIVO, corre `decidir.py` (tabla determinística), el monitor + motor de decisión de escalado fusionados (etapa-7) y la lectura concepto↔métrica (etapa-10); la fábrica de conceptos (etapa-9) corre en paralelo todos los días. Termina regenerando el dashboard. Úsala en la auditoría programada de cada mañana, o cuando el operador dice "auditoría", "cómo van las campañas", "métricas de hoy", "qué pauso", "qué escalo" o pega un export de LucidSales.
tools: Read, Write, Glob, Grep, Bash, Task
---

# CICLO DE OPTIMIZACIÓN — post-lanzamiento

Corre **después de lanzar**, todos los días. Audita **cada producto con `estado=VIVO`** de
`PRODUCTOS/_DIM_PRODUCTOS.csv` (el registro maestro: estado, fase, cuenta, página, tasa, CPA base,
break-even, `clave_campana`, `campaign_id`), no uno solo.

La recolección de datos ya corre sola: Task Scheduler dispara `Ads/_TOOLS/ciclo_diario.py`, que baja
e ingiere ventas y gasto, corre `ciclo_hoy.py` y regenera el dashboard, y deja una fila en
`PRODUCTOS/_CORRIDAS_DIARIAS.csv` (VERDE / AMARILLO / ROJO). Para correrlo a mano:

```bash
python Ads/_TOOLS/ciclo_hoy.py        # motor (dbt + decidir) → flujo.py --todo → lanzador → app
```

El ciclo son tres nodos de `DOCTRINA/FLUJO.json` por producto lanzado: `ciclo.datos` (ventas con
rezago ≤ `rezago_max_dias`), `ciclo.motor` (`_DECISIONES.json` de hoy) y `ciclo.ordenes` (cada
PAUSAR / ESCALAR / RENOVAR ejecutada **con confirmación del operador** y registrada en
`_EVENTOS.csv`; sin evento el nodo no se cierra). `python Ads/_TOOLS/flujo.py --todo` dice cuál falta.

---

## 1. Tabla determinística — SIEMPRE primero

```bash
python Ads/_TOOLS/decidir.py   # sin --json: imprime la tabla
```

Se pega completa arriba del informe del día. Trae por producto el Break-Even y el CPA Objetivo, y por
celda el estado, ventas, mensajes, gasto, CPA real, IC 95 % y `accion_sugerida`. Ninguna etapa la
recalcula ni la reescribe en prosa.

## 2. `etapa-7` — monitor y decisión de escalado

Sobre esa tabla, por cada producto VIVO con campaña activa hace 24 h o más: integridad, confusión,
sangrado, lectura por dimensión y plan de palancas. Solo lee y recomienda. Todo su método está en
`.Codex/agents/ETAPA-7.md`.

## 3. `etapa-10` — lector concepto ↔ métrica

Después de `etapa-7`. Cruza el rendimiento de cada anuncio contra el blueprint que lo originó
(`canonico_id`) y dice **por qué** ganó, con piso de evidencia. Su salida es el brief de `etapa-9`.
`etapa-7` mueve dinero; `etapa-10` mueve el diseño.

## 4. `etapa-9` — fábrica de conceptos (diaria, en paralelo)

Produce **≥6 ejecuciones por día** desde los blueprints canónicos (el llenado lo hace la skill
`generar-conceptos`) y las registra en `_DIM_CREATIVOS.csv`. Antes de producir, audita los atascos:
una pieza `GENERADO` con más de 7 días sin `ad_id` es una alerta (el cuello de botella medido es
publicar, no producir).

`etapa-11` (optimizador de flujo) **no es diaria**: corre al confirmarse el ángulo ganador por venta
(lo dicta `flujo.py`, nodo `F2.etapa-11`).

## 5. Órdenes

Cada orden del motor se ejecuta por MCP **con confirmación explícita del operador, orden por orden**
(o la hace el operador a mano), se verifica contra Meta y se registra con
`python Ads/_TOOLS/registrar_evento.py`, nunca a mano. Todo ESCALAR ejecutado deja un
`CAMBIO_PRESUPUESTO` con `--antes` y `--despues` en USD/día.

## 6. Mercado CO

Las ventas de la tienda de Colombia entran solas de noche si existe `~/.config/lucidsales/co.env`
(pasos opcionales de `ciclo_diario.py`). El gasto de un producto en una cuenta EXTERNA (sin MCP ni
token) no: el operador entrega el export de Ads Manager y se ingiere con `ingerir_meta.py --producto`
(skill `recopilar-lucidsales`, sección «MERCADO CO (MANUAL)»). Después, `decidir.py` por producto
igual que el resto.

## 7. Dónde se escribe

Los informes por producto van a `PRODUCTOS/[carpeta]/`; **todo informe fechado** va a
`PRODUCTOS/_AUDITORIAS/`. Son registro histórico: **prohibido sacar métricas de ahí** (salen del CSV).
El dashboard se regenera solo cuando cambia un CSV de `PRODUCTOS/`; a mano:
`python Ads/_TOOLS/gen_dashboard.py`.
