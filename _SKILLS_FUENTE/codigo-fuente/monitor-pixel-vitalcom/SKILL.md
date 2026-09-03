---
name: monitor-pixel-vitalcom
description: >-
  Monitorea la salud del conjunto de datos (dataset/Pixel) de Meta Ads de Vitalcom, con foco
  en los EVENTOS OFFLINE DE COMPRA que tu WABA/LucidBot devuelve a Meta — la señal que
  alimenta tu columna "Compras" y tu CPA. Revisa volumen de eventos, calidad de coincidencia
  (EMQ) y dispara ALERTA si un evento cayó más del 20% en los últimos 7 días vs los 7 previos.
  Para Vitalcom es crítico: si tus compras offline dejan de llegar, tu CPA LucidBot se rompe en
  silencio. Úsala cuando el usuario diga: revisá el pixel/dataset, ¿están llegando mis compras
  a Meta?, salud del pixel, monitorear eventos, calidad de coincidencia, EMQ, caída de eventos,
  o cuando sospeche que el tracking de compras del bot dejó de registrar. Requiere el dataset_id.
---

# Monitor de Pixel / Dataset — Vitalcom

Revisa la salud del conjunto de datos de Meta y avisa cuando algo se rompe. Responde tres
preguntas: ¿están entrando los eventos (sobre todo las **Compras offline** del bot)?, ¿con qué
calidad de coincidencia (EMQ)?, y ¿alguno cayó de forma alarmante esta semana?

> **Por qué importa en Vitalcom:** tu venta vive en LucidBot y vuelve a Meta como conversión
> offline. Si ese flujo WABA→Meta se corta, las "Compras" desaparecen, tu **CPA LucidBot** se
> vuelve falso (parece que no vendés) y podrías pausar conjuntos que en realidad venden. Esta
> skill detecta esa caída antes de que te haga tomar una mala decisión.

Se apoya en el MCP de Meta (`ads_get_dataset_details`, `ads_get_dataset_quality`,
`ads_get_dataset_stats`) y en el script incluido que hace los cálculos (una alerta no puede
depender de sumas a ojo).

## Requisito previo: el dataset_id
La skill necesita el **dataset ID** (ID del Pixel/conjunto de datos que recibe los eventos del
bot). Está en `PRODUCTOS/[PRODUCTO]/2_DATA_PRODUCTO.txt` como `MCP_PIXEL_ID`, o en Meta Events
Manager → tu conjunto de datos → el número bajo el nombre. Si no se dio, pedilo; no lo adivines.

> Nota de moneda: tu cuenta es en USD. Esta skill mide **conteos de eventos y EMQ**, no dinero,
> así que la tasa USD↔Q no aplica acá.

## Flujo de trabajo
Creá una carpeta temporal para guardar las respuestas crudas del conector como `.json` (el
script las lee).

### 1. Ventana y punto de corte (bash)
```
NOW=$(date +%s)
MIDPOINT=$((NOW-604800))     # hace 7 días
START=$((NOW-1209600))       # hace 14 días
```
Consultás una sola ventana de 14 días; el script la parte en dos mitades de 7. `ads_get_dataset_stats` solo mira 28 días atrás, así que entra sin problema.

### 2. Identidad y estado
`ads_get_dataset_details(dataset_id)` → `details.json` (nombre, si está activo, último evento navegador/servidor).

### 3. Calidad de coincidencia (EMQ)
`ads_get_dataset_quality(dataset_id)` → `quality.json` (EMQ por evento y cobertura de cada llave: email, teléfono, external_id…). Para Vitalcom, el **teléfono** del cliente es la llave fuerte de las compras offline — vigilá su cobertura.

### 4. Volumen de eventos — una consulta por evento
De `quality.json` sacá la lista de eventos. Para **cada** evento:
```
ads_get_dataset_stats(dataset_id, aggregation="event", event_name="<EVENTO>",
                      start_time=START, end_time=NOW)
```
Guardá cada respuesta en `ev_<EVENTO>.json`. **`aggregation` debe ser `"event"`** (no `"event_total_counts"`). Una consulta por evento mantiene la respuesta chica y robusta. Prestá atención especial al evento de **compra/purchase offline** — es el que sostiene tu CPA.

### 5. Calcular caídas y alertas
```
python3 <ruta-de-la-skill>/scripts/analyze_pixel.py \
  --stats ev_*.json --midpoint $MIDPOINT \
  --quality quality.json --details details.json \
  --floor 50 --threshold 20
```

### 6. Presentar
Mostrá la salida del script. **Si hay alertas, primero** — y si la alerta es sobre el evento de
compra, decilo de frente: "tus Compras offline cayeron X% — revisá la integración WABA→Meta
antes de tomar decisiones de CPA". 1–2 frases de lectura propia si aportan; no inventes causas.

## La regla de la alerta
Dispara cuando se cumplen **las dos**: (1) caída **>20%** en 7 días vs los 7 previos, y (2) la
ventana previa tuvo **≥50 eventos** (piso de ruido, `--floor`). Un evento que existía y
desaparece (0) cuenta como −100% → alerta fuerte si tenía volumen. Eventos por debajo del piso
se reportan como ⚪ "bajo volumen" sin disparar alerta.

## Cómo leer el EMQ
Puntaje 0–10 por evento: **≥8 excelente, 6–7.9 aceptable, 4–5.9 bajo, <4 crítico**. Lo que más
lo mueve es la cobertura de llaves fuertes (teléfono, email, external_id). `ads_get_dataset_quality`
da solo el EMQ **actual** (foto, sin histórico).

## Uso en tarea programada
Pensada para correr **semanal** automática. Una tarea programada corre sin nadie que conteste,
así que el `dataset_id` **debe venir en el prompt de la tarea**. Recomendado: agendar 1 vez por
semana para que una caída del tracking de compras no pase desapercibida.

## Ejemplos de disparo
- "¿Están llegando mis compras del bot a Meta?" → pedir dataset_id si falta, correr el flujo, encabezar con el evento de compra.
- "Revisame la salud del dataset 642774669816359." → correr directo, destacar EMQ y el evento purchase.
- (Tarea programada semanal) "Ejecuta monitor-pixel-vitalcom para el dataset [ID]." → correr directo, alertas primero.
