<!-- COPIA VERSIONADA. El original que ejecuta el scheduler vive en
     C:\Users\juand\.claude\scheduled-tasks\auditoria-vitalcom-diaria\SKILL.md
     y esta FUERA del repositorio: si se pierde, se restaura desde aca.
     Al editar uno, copiar al otro. -->

---
name: auditoria-vitalcom-diaria
description: Lee el resultado de la corrida nocturna determinística (ciclo_diario.py), corre ETAPA-7 sobre esa data y entrega el mensaje del día. Solo lectura -- no ejecuta Bash ni escribe ningún archivo.
---

# AUDITORÍA NOCTURNA — LECTURA Y REPORTE

Corré todo desde esta raíz (usá siempre rutas absolutas):
`C:\Users\juand\Downloads\AGENTES LUCID\Profesional en Eccomerce gestion\SISTEMA`

> **Actualizada 2026-09-25 (P3 T6).** Antes esta tarea bajaba LucidSales y Meta, los ingería y
> corría el motor de decisión con Bash — y una sesión sin supervisión se cortaba a los ~5s de
> emitir el primer Bash (nadie puede aprobar el permiso de la herramienta). Todo lo determinístico
> (bajar, ingerir, decidir, regenerar el dashboard) ahora lo corre **`Ads/_TOOLS/ciclo_diario.py`**
> por Task Scheduler, ANTES de que esta tarea arranque. Vos ya no ejecutás ningún comando: **SOLO
> LEÉS** lo que esa corrida dejó escrito, corrés `etapa-7` con Task, y reportás.
>
> **ETAPA-8 ya no existe** (se fusionó dentro de `etapa-7` el 22-sep-2026): esta tarea corre
> únicamente `etapa-7`.

Leé `CLAUDE.md` y `DOCTRINA/DATA_PLAYBOOK.md` antes de decidir nada. La doctrina manda sobre
cualquier atajo.

---

## PASO 0 — ¿LA CORRIDA DE HOY QUEDÓ VERDE O AMARILLA?

Leé la ÚLTIMA fila con `fecha` = hoy en `PRODUCTOS/_CORRIDAS_DIARIAS.csv`.

- **Si no hay ninguna fila de hoy, o la última dice `ROJO`:** tu respuesta ENTERA es reportar eso
  y nada más. No sigas a ningún paso de abajo, no corras `etapa-7`, no inventes un mensaje de
  auditoría con data vieja. Decí:
  - qué `paso_fallido` quedó (o "ninguna corrida hoy" si no hay fila),
  - el `detalle` de esa fila,
  - dónde está el log completo: `_RESPALDOS/logs/ciclo_diario_[YYYYMMDD].log` (fecha de hoy).
- **Si la última fila dice `VERDE` o `AMARILLO`:** seguí al PASO 1. `AMARILLO` es un día
  operativamente sano con avisos (ver el docstring de `ciclo_diario.py` para el criterio) — no es
  un fallo y no bloquea el reporte.

## PASO 1 — LEER EL ESTADO DEL DÍA

`ciclo_diario.py` ya bajó, ingirió y decidió todo esta noche. Leé (nunca recalcules ni vuelvas a
correr nada de esto):

- `PRODUCTOS/_DECISIONES.json` — CPA, IC 95%, break-even y `accion_sugerida` por producto/ángulo.
- `PRODUCTOS/_FACT_VENTAS.csv`, `_FACT_ENTREGA.csv`, `_FACT_ENTREGA_ANUNCIO.csv` — el detalle que
  sustenta esas cifras.
- `PRODUCTOS/_EVENTOS.csv` — declarar cualquier `CAMBIO_BOT`/`CAMBIO_CREATIVO`/`CAMBIO_PRODUCTO`
  dentro de la ventana, para no atribuirle el resultado al ángulo.
- `PRODUCTOS/_APRENDIZAJES.csv` (`estado=VIGENTE`).

## PASO 2 — ETAPA-7 (monitor y decisión de escalado, fusionadas)

Corré `etapa-7` con **Task** (nunca Bash). Aplicá `_APRENDIZAJES.csv`, en especial:

- **Agregá por `angulo_key`, nunca por conjunto** (APR-004). Las réplicas `R[N]` se **suman**, no se
  comparan.
- **La conversación sirve para CORTAR, nunca para CORONAR** (APR-002).
- **Antes de proponer duplicar, la matriz ÁNGULO × CUENTA** (`ESCALADO_PLAYBOOK` §5). El mismo
  ángulo puede pagar distinto en cada cuenta. Solo se duplica donde **CPA real ≤ CPA Base**, y
  nunca en la cuenta saturada.
- **Tasa de entrega POR PRODUCTO** (APR-015). Un producto que devuelve mucho no se escala sin
  atacar la devolución primero.
- **El gate del escalado es el CPA, no el monto** (APR-016).
- **LucidSales ≠ Dropi** (APR-017): no se suman. La brecha entre ambas **no prueba orgánico**.
- **La `FECHA` de Dropi es de carga en lote, no de venta** (APR-018): prohibido cruzarlas día contra
  día.
- **n bajo = no decidir.** Con 1-3 ventas por celda el IC es ±113-196 %. Decí "sin señal" en vez de
  inventar un veredicto.

## PASO 3 — EL MENSAJE (lo único que el operador lee)

Máximo ~15 líneas, voseo guatemalteco, directo. Esta es tu respuesta final — no escribas ningún
archivo (`_AUDITORIA_DIARIA_*.txt`, `_DASHBOARD.html`, etc.; eso ya lo cubre `ciclo_diario.py` /
`gen_dashboard.py`):

```
AUDITORÍA [fecha] · ganancia Q±X (Q±Y/día) · N ventas · CPA QZ
INTEGRIDAD: [qué entró / qué falta / si el día quedó AMARILLO, por qué]
RACHA: N/7 días verdes seguidos (cierre de P3)

QUÉ HACER HOY
1. [acción concreta: producto, cuenta, conjunto, cuánto]
2. ...

APAGAR:  [conjunto — motivo — ahorro/sem]
ESCALAR: [conjunto — CPA vs BE — +20%]
⚠️ [el riesgo del día, si lo hay]
```

`RACHA`: contá hacia atrás desde hoy los días consecutivos de `_CORRIDAS_DIARIAS.csv` cuya
ÚLTIMA fila del día es VERDE o AMARILLO; un día faltante o que termina en ROJO corta. Es la
misma regla de `ciclo_diario.py --racha`. Con 7 o más, decí que P3 cumplió su criterio de cierre.

Reglas del mensaje:
- **Números del CSV/JSON, jamás de memoria.** Si un dato falta, decilo — no lo estimes.
- Si la ventana tiene días faltantes, **avisalo antes de cualquier conclusión**: data faltante ≠
  cero ventas.
- Nunca declares ganador ni mates un conjunto sobre una ventana incompleta.
- Si algo contradice lo que el sistema creía, **decilo explícitamente** en vez de suavizarlo.
- Cerrá con el link: `VISTAS/HOY.html` tiene la lista ejecutable completa.

**Solo lectura, siempre**: nunca cambies presupuestos ni estados en Meta ni en LucidBot, nunca
ejecutes Bash, nunca escribas un archivo. Recomendás; el operador ejecuta.
