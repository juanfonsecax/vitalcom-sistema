<!-- COPIA VERSIONADA. El original que ejecuta el scheduler vive en
     C:\Users\juand\.claude\scheduled-tasks\auditoria-vitalcom-diaria\SKILL.md
     y esta FUERA del repositorio: si se pierde, se restaura desde aca.
     Al editar uno, copiar al otro. -->

---
name: auditoria-vitalcom-diaria
description: Auditoría nocturna del portafolio VitalCom: baja LucidSales sola por API, pide solo el export de Meta, los ingiere con las herramientas, corre ETAPA-7 + ETAPA-8 y regenera el panel.
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

> **16-sep-2026 — el MCP se descartó para esta tarea, reemplazado por API directa.** Se intentó
> enganchar el conector MCP de Meta Ads acá (ver `_OPERADOR/ENTREGA_DE_DATA.md`). Tres corridas en
> vivo — con el permiso de lectura ya aprobado, y hasta en una sesión recién creada — se quedaron
> colgadas indefinidamente justo después de invocar `ads_get_ad_accounts`, nunca devolvieron nada.
> El conector funciona perfecto en sesión interactiva pero no responde dentro de una tarea sin
> supervisión (aprobar una herramienta MCP remota parece exigir un clic humano que acá no existe).
> **`Ads/_TOOLS/bajar_meta_insights.py` reemplaza a esto**: pega directo a la Graph API con un token
> de System User de solo-lectura (`ads_read`), mismo patrón que `bajar_lucidsales.py`. Publicar
> sigue siendo 100% MCP, interactivo, con confirmación del operador — esto es solo lectura.

## PASO 1 — LA DATA DEL DÍA

> **Cambio del 07-sep-2026: LUCIDSALES YA NO SE PIDE.** Se baja solo, por API, sin abrir el panel
> ni descargar nada. Antes esta tarea pedía DOS archivos al operador; ahora pide UNO.

**1a · LucidSales — automático.** Primero de todo, y sin preguntarle nada al operador:

```bash
python "Ads/_TOOLS/bajar_lucidsales.py"
```

Trae **ayer cerrado** y escribe `Ads/_INGESTA/LUCIDSALES/report-AYER-AYER.json`. Las credenciales
salen de `~/.config/lucidsales/.env`; la tienda es **PRIMAX GT**. El detalle del contrato y los
modos (huecos, control semanal) viven en la skill **`recopilar-lucidsales`** — cargala si algo falla
en vez de improvisar contra la API.

**Leé lo que imprime antes de ingerir.** Si dice `CERO filas`, **no ingieras**: es fecha equivocada
o día sin cerrar. Si dice `Ya existe report-…`, ese día ya se bajó y no se vuelve a bajar.

**1b · Meta Ads Manager — automático, con red de seguridad.** Primero intentá la API directa:

```bash
python "Ads/_TOOLS/bajar_meta_insights.py"
```

Trae **ayer cerrado** de las 4 cuentas ACTIVE con `mcp_habilitado=SI` en `_DIM_CUENTAS.csv`
(GTR7, GTR0, GTR1, GTR3), excluye lo que no sea de VitalCom (GTR7 es cuenta compartida de agencia)
y escribe directo en `_FACT_ENTREGA.csv` / `_FACT_ENTREGA_ANUNCIO.csv` con `fuente=MetaAPI-directo`.
No hace falta `--dry-run` primero: ya excluye lo ajeno y es idempotente por llave.

**Si falla** (imprime `FALTA EL TOKEN` o cualquier error de la Graph API): esto es la red de
seguridad, no un fallo silencioso — pedile al operador el export manual como antes:

| Archivo | Qué es | Sin él no se puede |
|---|---|---|
| `Informe-*.xlsx` (nivel **conjunto**, 1 día) | **Meta Ads Manager** — entrega | separar "el ad no entrega" de "el bot no cierra" |

⚠️ **Los nombres engañan y ya se confundieron una vez:** el que empieza con `report-` es
**LucidSales** (y ahora lo baja el script solo); el que empieza con `Informe-sin-título-` es **Meta**.

Si caíste al camino manual, antes de pedirlo mirá qué falta de verdad: último `ventana_fin` en
`PRODUCTOS/_FACT_ENTREGA.csv`. Pedí **por fecha exacta, una sola vez**. Nunca pidas un rango ya
cargado. Si no falta nada, decilo
y seguí al PASO 3.

**Semanal (lunes):** sumá el export de Dropi de **órdenes** (`ordenes_productos_*.xlsx`, rango 60
días móviles) y el de **cartera** (`historial de cartera-*.xlsx`). No los pidas a diario: la COD
madura ~10 días y un export diario mide un cohorte inmaduro que cambia solo.

**Mensual (día 1-2):** el extracto del banco (`Business-Checking-MES.pdf`).

---

## PASO 2 — CARGA: usá las herramientas, no escribas los CSV a mano

> **Si el PASO 1b funcionó por API directa, `_FACT_ENTREGA*.csv` ya quedó escrito** —
> `bajar_meta_insights.py` no necesita un ingestor aparte. La línea de `ingerir_meta.py` de abajo
> es SOLO para cuando caíste al camino manual (xlsx).

```bash
python "Ads/_TOOLS/ingerir_lucidsales.py" --dir "Ads/_INGESTA/LUCIDSALES"
python "Ads/_TOOLS/ingerir_meta.py" <Informe-*.xlsx>
```

El primero toma el `.json` que dejó el PASO 1a. También acepta un `.xlsx` bajado a mano, si alguna
vez hay que volver al camino viejo: es la misma data y produce la misma carga (verificado el
07-sep celda por celda contra una descarga manual del 01-sep).

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
   **Desde el 07-sep se suma un tercer tipo: las VENTAS ORGÁNICAS** (`ad_id="organico"`, sin cuenta,
   sin conjunto, `spend_usd=0`). Son ventas reales que entraron sin pauta y **antes se descartaban
   en silencio** — el 01-sep se perdían Q198 de 9 ventas. No las trates como huecos ni las sumes al
   costo por venta de ningún ángulo: no tienen anuncio que las haya generado.
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
3. **ÚLTIMO PASO SIEMPRE** — regenerá el panel:
   ```bash
   python "Ads/_TOOLS/gen_dashboard.py"
   ```
   Emite `PRODUCTOS/_DASHBOARD.html` **y** `VISTAS/HOY.html` (la vista de una pantalla). Si el CSV
   cambió y no regeneraste, el operador está mirando data vieja.

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
- Cerrá con el link: `VISTAS/HOY.html` tiene la lista ejecutable completa.

**Solo lectura sobre Meta y LucidBot**: nunca cambies presupuestos ni estados. Recomendás; el
operador ejecuta.
