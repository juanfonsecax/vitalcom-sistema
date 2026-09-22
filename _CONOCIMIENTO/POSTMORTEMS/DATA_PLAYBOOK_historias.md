# Historias de DATA_PLAYBOOK.md

Consulta humana. La regla vigente vive en `DOCTRINA/DATA_PLAYBOOK.md`; acá vive el incidente que la
produjo, por sección del playbook.

## §1 — LOS ARCHIVOS Y SU ROL

**El split FACT del 25-jul.** Antes `_FACT_VENTAS.csv` y `_FACT_ENTREGA.csv` vivían juntas en
`_HISTORICO.csv`, y sumar el archivo entero inflaba el gasto +27% (Q296 → Q377): las filas de
entrega (mensajes/clics, sin venta) se sumaban como si fueran ventas. El split del 25-jul eliminó
esa clase de error; el archivo viejo quedó en `_ARCHIVO/DATA_MIGRADA/`. Regla que dejó: dos archivos
separados, uno por fuente, y `_FACT_ENTREGA.csv` no tiene columnas de venta — sumarla al P&L es
imposible, no solo prohibido.

**El JOIN del 02-sep.** `_FACT_ENTREGA.csv` llega sin el prefijo `[CUENTA]_[PRODUCTO]_` y sin
tildes ni eñes, así que el mismo objeto de Meta aparecía con dos grafías distintas en
`_FACT_ENTREGA.csv` y `_DIM_CONJUNTOS.csv`. El 02-sep se anexó la grafía que faltaba para 63
conjuntos (`origen_angulo=HEREDADO_JOIN_ENTREGA`): el JOIN pasó de 75% a 100% y devolvió al análisis
por ángulo Q2,622 de pauta, 513 mensajes y 2,043 clics de enlace que estaban invisibles. Regla que
dejó: nunca normalizar la llave — se anexa la grafía que falta a `_DIM_CONJUNTOS.csv` con el mismo
`angulo_key`.

**La auditoría del 02-sep sobre `CAMBIO_BOT`.** En toda la serie 17-jul → 01-sep había un solo
`CAMBIO_BOT` registrado en `_EVENTOS.csv`, y era anterior al primer día de data: era imposible saber
si algún cambio de flujo había servido alguna vez, en el momento en que el cierre era ya la palanca
más grande que le quedaba al sistema. Regla que dejó: todo cambio de flujo se loguea como
`CAMBIO_BOT` el día que se aplica.

**El caso real de `_DIM_CREATIVOS.csv`.** 12 filas llevaban 26 días en `PENDIENTE_GENERAR` cuando en
verdad los 8 PNG ya existían en disco: lo que faltaba no era producir, era publicar. Sin alerta, la
fábrica de creativos produce para el disco duro y nadie lo nota. Regla que dejó: una fila en
`PENDIENTE_GENERAR` o `GENERADO` por más de 7 días dispara una alerta de dashboard.

## §1.1 — MAPA DE CARPETAS

**Por qué `clave_campana` y `campaign_id` se movieron a `_DIM_PRODUCTOS.csv`.** Vivían en
`_PORTAFOLIO.txt`, que las tenía como los únicos 2 datos de sus 10 columnas que `_DIM_PRODUCTOS.csv`
no tenía — el resto (estado, fase, cuenta, tasa, CPA base, CPA BE, notas, producto) ya estaba
duplicado. Era el mismo registro maestro mantenido dos veces, uno en CSV y otro en prosa, y el 79%
de `_PORTAFOLIO.txt` no era la tabla sino narrativa acumulada. Mover las dos columnas cerró el
duplicado y le permitió a la auditoría diaria resolver la campaña de un producto sin leer 27 KB de
prosa.

**El bug de CSV malformado en NUSAVA, 31-jul.** La fila de NUSAVA tenía 20 campos en vez de 17: su
campo `notas` traía comas y no estaba entrecomillado, así que cada coma abría un campo nuevo. El
dashboard no lo notó porque lee columnas anteriores a `notas`, pero cualquier lector estricto rompía
y la nota se truncaba. Regla que dejó: todo campo de texto libre con comas va entre comillas dobles,
y los CSV se editan con un escritor real (`csv.DictWriter`), nunca a mano ni concatenando strings.

## §4 — FÓRMULA OFICIAL DE GANANCIA

**Por qué la fórmula vieja (`ventas × BE fijo − pauta`) quedó deprecada.** Contaba ventas, no
quetzales: un pedido de 3 frascos a Q299 valía igual que uno de 1 frasco a Q179. Medido sobre la
misma ventana: Q2,302 de ganancia con la fórmula vieja contra Q4,799 con la nueva (v2, por
contribución real de cada venta) — la vieja subestimaba la ganancia y hacía invisible todo el upsell
del bot.

## §4.2 — AUDITORÍA DE INTEGRIDAD

**Por qué se agregó la columna `ad_id` (11-ago).** Antes había que volver al xlsx original para
distinguir "dos `adId` gemelos" de "la misma fila cargada dos veces" — las pruebas de duplicado no
se podían automatizar. Con `ad_id` agregado, una corrida sobre 1,490 filas dio 0 llaves repetidas y
0 `adId` en común entre `LucidSales` y `LucidSales_CuentaB`, confirmando que las dos cuentas suman
bien y que ninguna ventana había entrado dos veces.

## §5 — CADENCIA Y MONEDAS

**La corrección de la tasa COP de CP1 (corregido 15-ago, APR-028).** La tasa vieja (4,050) se había
*derivado* comparando campañas hermanas; la nueva (3,152.5) se *midió* emparejando 9 cargos uno a
uno entre el extracto de Meta y el del banco (el código de Meta aparece literal en el banco como
`Facebk *codigo`). La tasa vieja subestimaba el gasto de CP1 en 28.5%.
