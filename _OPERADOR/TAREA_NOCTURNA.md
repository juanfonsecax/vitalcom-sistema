<!-- COPIA VERSIONADA. El original que ejecuta el scheduler vive en
     C:\Users\juand\.claude\scheduled-tasks\auditoria-vitalcom-diaria\SKILL.md
     y esta FUERA del repositorio: si se pierde, se restaura desde aca.
     Al editar uno, copiar al otro. -->

---
name: auditoria-vitalcom-diaria
description: Auditoría nocturna del portafolio VitalCom: pide los 2 exports del día, los ingiere con las herramientas, corre ETAPA-7 + ETAPA-8 y regenera el panel.
---

# AUDITORÍA NOCTURNA — PORTAFOLIO VITALCOM GUATEMALA

Corré todo desde esta raíz (usá siempre rutas absolutas):
`C:\Users\juand\Downloads\AGENTES LUCID\Profesional en Eccomerce gestion\SISTEMA`

Sos el orquestador. Leé `CLAUDE.md` y `DOCTRINA/DATA_PLAYBOOK.md` (§4, §4.1, §4.2) antes de
decidir nada. La doctrina manda sobre cualquier atajo.

> **Actualizada 2026-09-03.** La versión anterior (11-ago) pedía dos cuentas de LucidSales que ya
> no existen, convertía COP con una tasa que se corrigió el 15-ago, apuntaba a un archivo que se
> movió de carpeta y cargaba los CSV a mano teniendo ingestores. Si algo de abajo choca con lo que
> recordás de esta tarea, manda lo de abajo.

---

## PASO 1 — PEDIR LA DATA DEL DÍA (son DOS archivos, no uno)

La cadencia completa por fuente vive en `_OPERADOR/ENTREGA_DE_DATA.md`. Todas las noches
corresponden **dos** exports, los dos de **un solo día** y los dos de **ayer**:

| Archivo | Qué es | Sin él no se puede |
|---|---|---|
| `report-AYER-AYER.xlsx` | **LucidSales** — ventas atribuidas por anuncio | saber si vendiste: es la única fuente de ventas |
| `Informe-*.xlsx` (nivel **conjunto**, 1 día) | **Meta Ads Manager** — entrega | separar "el ad no entrega" de "el bot no cierra" |

⚠️ **Los nombres engañan y ya se confundieron una vez:** el que empieza con `report-` es
**LucidSales**; el que empieza con `Informe-sin-título-` es **Meta**.

Antes de pedir, mirá qué falta de verdad:
- último `ventana_fin` con `rol_ventana=BASE` en `PRODUCTOS/_FACT_VENTAS.csv` → eso cubre LucidSales
- último `ventana_fin` en `PRODUCTOS/_FACT_ENTREGA.csv` → eso cubre Meta

Pedí **por fecha exacta, una sola vez y todo junto**. Nunca pidas un rango ya cargado. Si no falta
nada, decilo y seguí al PASO 3.

**Semanal (lunes):** sumá el export de Dropi de **órdenes** (`ordenes_productos_*.xlsx`, rango 60
días móviles) y el de **cartera** (`historial de cartera-*.xlsx`). No los pidas a diario: la COD
madura ~10 días y un export diario mide un cohorte inmaduro que cambia solo.

**Mensual (día 1-2):** el extracto del banco (`Business-Checking-MES.pdf`).

---

## PASO 2 — CARGA: usá las herramientas, no escribas los CSV a mano

```bash
python "Ads/_TOOLS/ingerir_lucidsales.py" <report-*.xlsx>
python "Ads/_TOOLS/ingerir_meta.py" <Informe-*.xlsx>
```

Los dos son **idempotentes**: anti-duplicado por llave, backup previo en `_ARCHIVO/backups_csv/`,
y aceptan `--dry-run`. **Corré siempre `--dry-run` primero** y leé lo que reporta antes de escribir.
Pasar dos veces el mismo archivo no duplica nada: lo omite y lo dice.

Las reglas que antes había que aplicar a mano **ya están dentro de los ingestores** — no las
reimplementes:
- rol `BASE` / `CONTROL` y contigüidad de ventanas
- **CP1 (`1346891653335162`) factura en COP → `spend ÷ 3152.5`.** ⚠️ La tasa es **3152.5**, medida
  contra el banco emparejando 9 cargos (APR-028, 15-ago). **NO es 4050**: esa vieja subestimaba el
  gasto de CP1 un 28.5 %.
- escritura con `csv.writer` real (regla 11)
- derivación de `mensajes` en el export de Meta: `round(tasa_conv_whatsapp × link_clicks)`

Lo que SÍ te toca revisar después de cargar:
1. **El JOIN contra `_DIM_CONJUNTOS.csv` tiene que cerrar al 100 %.** El ingestor te lo dice. Un
   conjunto huérfano **se da de alta con su `angulo_key`, nunca se descarta el dato.** Si aparece un
   ángulo que no sale de ningún `2_DATA_PRODUCTO.txt`, marcalo DERIVADO y pedile al operador el
   avatar y el dolor.
2. **Filas legítimas que NO son huecos:** ventas sin conjunto (`spend=0`, sin `ad_id`) son las filas
   sintéticas de cuadre, y `conjunto="(campaña completa)"` es un agregado de campaña. Ninguna se
   inventa ni se descarta: se reportan aparte.
3. Anotá la carga en `PRODUCTOS/_BITACORA_DATA.txt` con cifras y anomalías.

> **Una sola cuenta de LucidSales.** Desde el **17-ago** el operador entrega un solo export por día
> de un único bot. Las ventanas **hasta el 16-ago** siguen necesitando las dos fuentes
> (`LucidSales` y `LucidSales_CuentaB`): son universos disjuntos y ambas suman (APR-021). No borres
> ni fusiones ese histórico.

---

## PASO 3 — ETAPA-7 (monitor) y ETAPA-8 (escalado)

Corré ambos subagentes con Task. Aplicá `_APRENDIZAJES.csv` (`estado=VIGENTE`), en especial:

- **Agregá por `angulo_key`, nunca por conjunto** (APR-004). Las réplicas `R[N]` se **suman**, no se
  comparan.
- **La conversación sirve para CORTAR, nunca para CORONAR** (APR-002). Medido de nuevo el 03-sep
  entre los 5 ángulos de TINNIDROP: la correlación conversación↔cierre es **nula** (r=−0.23).
- **Antes de proponer duplicar, la matriz ÁNGULO × CUENTA** (`ESCALADO_PLAYBOOK` §5). El mismo
  ángulo puede pagar Q29 en una cuenta y Q167 en otra. Solo se duplica donde **CPA real ≤ CPA Base**,
  y nunca en la cuenta saturada.
- **Tasa de entrega POR PRODUCTO** (APR-015). Un producto que devuelve mucho no se escala sin
  atacar la devolución primero.
- **El gate del escalado es el CPA, no el monto** (APR-016).
- **LucidSales ≠ Dropi** (APR-017): no se suman. La brecha entre ambas **no prueba orgánico**.
- **La `FECHA` de Dropi es de carga en lote, no de venta** (APR-018): prohibido cruzarlas día contra
  día.
- **n bajo = no decidir.** Con 1-3 ventas por celda el IC es ±113-196 %. Decí "sin señal" en vez de
  inventar un veredicto.

Si hay un `CAMBIO_BOT`, `CAMBIO_CREATIVO` o `CAMBIO_PRODUCTO` en `_EVENTOS.csv` dentro de la
ventana, **declaralo** y no atribuyas el resultado al ángulo.

---

## PASO 4 — ESCRIBIR Y CERRAR

1. Auditoría en `PRODUCTOS/_AUDITORIAS/_AUDITORIA_DIARIA_[YYYYMMDD].txt`.
2. **Todo cambio que el operador ejecutó hoy va a `_EVENTOS.csv` con la fecha de hoy.** Un cambio
   sin evento es un cambio que después no se puede evaluar. Escribilo con `csv.writer` real.
3. **ÚLTIMO PASO SIEMPRE** — regenerá la app:
   ```bash
   python "Ads/_TOOLS/gen_app.py" --todo
   ```
   Un solo comando corre los 7 generadores declarados en `VISTAS/_MANIFIESTO.json` (dashboard,
   `HOY.html`, testeos, estructura, conceptos, winners, catálogo), refresca el portafolio del
   lanzador y reescribe `VISTAS/APP.html`, que es la única pantalla que el operador abre. Reporta
   cuál falló, si alguno falla. Si el CSV cambió y no regeneraste, el operador está mirando data
   vieja — y la app te lo va a decir con una insignia roja en la vista **Salud**.

---

## PASO 5 — EL MENSAJE (lo único que el operador lee)

Máximo ~15 líneas, voseo guatemalteco, directo:

```
AUDITORÍA [fecha] · ganancia Q±X (Q±Y/día) · N ventas · CPA QZ
INTEGRIDAD: [qué entró / qué falta]

QUÉ HACER HOY
1. [acción concreta: producto, cuenta, conjunto, cuánto]
2. ...

APAGAR:  [conjunto — motivo — ahorro/sem]
ESCALAR: [conjunto — CPA vs BE — +20%]
⚠️ [el riesgo del día, si lo hay]
```

Reglas del mensaje:
- **Números del CSV, jamás de memoria.** Si un dato falta, decilo — no lo estimes.
- Si la ventana tiene días faltantes, **avisalo antes de cualquier conclusión**: data faltante ≠
  cero ventas.
- Nunca declares ganador ni mates un conjunto sobre una ventana incompleta.
- Si algo contradice lo que el sistema creía, **decilo explícitamente** en vez de suavizarlo.
- Cerrá con el link: `VISTAS/APP.html` — abre en **Hoy**, con la lista ejecutable completa.

**Solo lectura sobre Meta y LucidBot**: nunca cambies presupuestos ni estados. Recomendás; el
operador ejecuta.
