# ✅ EJECUTADO — 2026-07-31 · NO VOLVER A PEGAR EL PROMPT

> **Estado: las 3 tareas ya se aplicaron** (ver tabla ESTADO al final). Este archivo queda como
> **registro histórico**, no como instrucción pendiente. Volver a pegar el PROMPT duplicaría
> ediciones que ya están en los agentes.
>
> **Nada queda abierto.** Los huecos de data de la TAREA 3 se cerraron el 31-jul (detalle en la tabla ESTADO):
> - **3a** — VARICOSE Q319: resuelto. Estuvo vivo hasta el 20-jul (el `2_DATA` decía 09-jul y estaba mal). Fila → HISTORICO, `n_ordenes` 0→6, se mantiene en la escalera.
> - **3b** — NAD+ Selerb X60: cerrado, NO se da de alta. Fue una prueba de landing.
> - **3c** — BODY COACH: cerrado, no entra. Nunca se vendió (confusión con Glute Glow).
> - **3d** — NUSAVA `fila_costeo_q` 70→54 aplicado.
> - **3e** — `otros_gastos_q = Q2.08`: decisión tomada — se conserva como colchón visible. Sin acción hasta identificar el origen.
>
> ⚠️ **Al leer este archivo, ir SIEMPRE a la tabla ESTADO del final.** La lista de tareas del PROMPT
> describe los huecos como estaban al detectarlos, no como quedaron. Leer solo el PROMPT lleva a
> reportar como pendiente algo ya resuelto.
>
> ⚠️ **Nota de rutas (refactor 31-jul):** la doctrina de la CAPA DE DATA ya **no** vive en `CLAUDE.md`.
> Se movió a **`DATA_PLAYBOOK.md`**. Las referencias del prompt de abajo a "CLAUDE.md → CAPA DE DATA"
> corresponden a la ubicación anterior.

---

# HANDOFF PARA CLAUDE CODE — 2026-07-31 (texto original)

Abrí Claude Code sobre `SISTEMA/` y pegá el bloque **PROMPT** de abajo.
Es autocontenido: no necesita la conversación previa.

Este archivo reemplaza a `PARCHE_AGENTES_20260731.md` (lo absorbe entero).

---

## PROMPT PARA PEGAR

````
Sos el mantenedor del SISTEMA VITALCOM. Leé primero `CLAUDE.md` (es la doctrina, ya está
actualizada) y después ejecutá las 3 tareas de abajo, EN ORDEN. Son ediciones quirúrgicas:
no reformatees archivos, no reescribas secciones que no se piden, no toques nada más.
Al terminar cada tarea, verificá con Read que quedó aplicada.

═══════════════════════════════════════════════════════════════════════════
CONTEXTO — QUÉ CAMBIÓ EL 31-JUL (ya está hecho, NO lo repitas)
═══════════════════════════════════════════════════════════════════════════
1. ECONOMÍA UNITARIA REAL. La ganancia se calculaba `ventas × break-even fijo − pauta`:
   contaba ventas, no quetzales, así que un pedido de 3 frascos valía igual que uno de 1.
   Subestimaba la ganancia 73% (Q2,302 → Q4,799 reales). Ahora se calcula por escalón desde
   `PRODUCTOS/_DIM_PRECIOS.csv` (nuevo). Break-even v3 derivado: TINNIDROP Q86.7 · NUSAVA
   Q120.4 · CLEARSTEM Q89.3 · VARICOSE Q111.0.
2. COSTOS VERIFICADOS sobre 102 órdenes reales de Dropi: comisión de plataforma 0% ·
   `flete = Q31.42 + Q2.70 × unidades` · la DISTANCIA no mueve el flete (tarifa casi plana
   nacional) · el costo de devolución (Q27.16) NO sale en la orden, sale en el estado de cuenta.
   Parámetros en `PRODUCTOS/_TASA_ENTREGA.csv`.
3. REGLA DE ARRANQUE 1u vs 2x1, derivada del múltiplo del costo (está en CLAUDE.md, ETAPA-1).
4. TRES EJES MEDIBLES DEL AVATAR agregados a `_DIM_CONJUNTOS.csv` y rellenados en los 54
   conjuntos: `avatar_genero`, `avatar_edad`, `emocion_dominante`.
5. DASHBOARD (`Ads/_TOOLS/gen_dashboard.py`): motor de acciones «Qué tenés que hacer» con
   9 reglas, cortes por producto, tabla maestra de precios. Todo derivado de los CSV.

═══════════════════════════════════════════════════════════════════════════
TAREA 1 — bajar los 3 ejes del avatar a los agentes que los producen
═══════════════════════════════════════════════════════════════════════════
La doctrina ya está en CLAUDE.md (sección CAPA DE DATA → `_DIM_CONJUNTOS.csv`). Falta que los
agentes la ejecuten, porque esos archivos quedaron protegidos en la sesión donde se derivó.

--- 1A. `.claude/agents/ETAPA-2.md` ---
En el bloque "AVATAR" de la ficha de ángulo, JUSTO DESPUÉS de la línea "Nivel de conciencia: [...]",
insertá exactamente esto:

CLASIFICACIÓN MEDIBLE (vocabulario CERRADO — obligatorio, va tal cual a `_DIM_CONJUNTOS.csv`)
avatar_genero: [MUJER / HOMBRE / MIXTO]
avatar_edad: [25-35 / 35-45 / 45-60 / 60+]   ← el bucket DOMINANTE, no el rango completo
emocion_dominante: [MIEDO_FUTURO / VERGUENZA / RESIGNACION / FRUSTRACION_MEDICA / DESCONFIANZA / AGOTAMIENTO / CURIOSIDAD]
> · MIEDO_FUTURO = teme que empeore o sea irreversible · VERGUENZA = lo esconde de los demás
> · RESIGNACION = ya se rindió, cree que no tiene arreglo · FRUSTRACION_MEDICA = pagó especialistas y sigue igual
> · DESCONFIANZA = teme que el producto sea falso o no funcione · AGOTAMIENTO = cansado, sin energía, no aguanta más
> · CURIOSIDAD = no sabía que su problema tenía esa causa (ángulos educacionales / mecanismo único)
>
> **POR QUÉ.** ETAPA-2 produce una ficha rica (perfil, situación, dolor activo, deseo, miedos,
> frustraciones) pero hasta ahora solo sobrevivían `avatar` y `dolor_nucleo` como TEXTO LIBRE —
> 28 y 33 valores distintos en 54 conjuntos, imposibles de agregar. Toda esa investigación se usaba
> para escribir el copy y DESPUÉS SE PERDÍA: nunca se contrastaba contra quién compró. Estos 3
> campos, con vocabulario cerrado, son lo que la vuelve aprendible y TRANSFERIBLE ENTRE PRODUCTOS
> (si la vergüenza vende en várices, se prueba vergüenza en acné).
>
> ⚠️ **ANDROMEDA (2026):** Meta ya NO segmenta por audiencia — el CREATIVO ES EL TARGETING.
> Andromeda lee el anuncio y de ahí deduce a quién mostrárselo; la calidad del creativo explica
> ~56% del resultado (más que segmentación + presupuesto + placement juntos) y el algoritmo IGNORA
> la definición de audiencia si las señales del creativo apuntan a otro lado. El avatar ya no se
> controla desde la cajita de segmentación: se controla desde lo que el creativo DICE y a quién
> RETRATA. Medirlo es lo único que queda para saber a quién le hablás de verdad.
>
> **CONSULTAR ANTES DE PROPONER ÁNGULOS:** abrí `PRODUCTOS/_DASHBOARD.html` → «Por qué funciona —
> cada producto». Trae el CPA real por emoción, género y edad, de este producto y del portafolio.
> Si una emoción ya fracasó 2 veces en la categoría, NO la vuelvas a proponer. Si viene ganando en
> otro producto del mismo nicho, es candidata a probar.

--- 1B. `.claude/agents/ETAPA-GUARDAR-PRODUCTO.md`, SALIDA 4 ---
(a) Reemplazá el bloque de columnas de `_DIM_CONJUNTOS.csv` por este (agrega 3 después de `avatar`):

producto_key, conjunto_meta, cuenta_alias, campana_clave, fase, angulo_key, angulo_nombre,
avatar, avatar_genero, avatar_edad, emocion_dominante, dolor_nucleo, formato, tipo_hook,
nivel_conciencia, rol_embudo, rol_embudo_origen,
lleva_precio, creativo_id, origen_angulo, estado, verificado_en_csv, fecha_alta, notas

(b) En "Vocabularios controlados" agregá:

- `avatar_genero`: MUJER · HOMBRE · MIXTO
- `avatar_edad`: 25-35 · 35-45 · 45-60 · 60+ — el bucket DOMINANTE, no el rango completo
- `emocion_dominante`: MIEDO_FUTURO · VERGUENZA · RESIGNACION · FRUSTRACION_MEDICA · DESCONFIANZA · AGOTAMIENTO · CURIOSIDAD
  Los declara ETAPA-2 en su ficha de ángulo. **Nunca dejarlos vacíos**: si un ángulo viejo no los
  trae, se rellenan leyendo su ficha en `2_DATA_PRODUCTO.txt`. Son lo que convierte la investigación
  de avatar en algo agregable — sin ellos el avatar muere en el copy y no se contrasta nunca contra
  quién compró. Con Andromeda pesan más que antes: el creativo es el targeting, así que el avatar
  solo se puede medir por lo que el creativo dice y retrata.

VERIFICAR: `python Ads/_TOOLS/gen_dashboard.py` debe imprimir `0 filas sin dimension`.

═══════════════════════════════════════════════════════════════════════════
TAREA 2 — diversidad conceptual (Andromeda) y la regla del duplicado
═══════════════════════════════════════════════════════════════════════════
HALLAZGO (investigación web 31-jul + data propia). Meta 2026 premia la diversidad CONCEPTUAL:
el benchmark es 8-12 conceptos conceptualmente distintos por campaña, similarity score <40%,
y las cuentas que testean 20+ anuncios/mes reportan 65% más ROAS que las que testean <10.
Medido sobre las campañas vivas de este sistema, TODAS están debajo:

| campaña                          | conjuntos | anuncios | CONCEPTOS reales |
|----------------------------------|-----------|----------|------------------|
| 🟩 TINIDROP GTR0 - TEST          |     7     |    9     |        5         |
| 2🟦/3🟦/4🟦/5🟦 TINIDROP (réplicas)|    4-6    |   7-8    |        4         |
| TINNIDROP_RENOVACION +25 años    |     5     |    7     |        5         |
| VARICOSE_ESCALA_VERGUENZA        |     4     |    8     |        4         |
| NUSAVAB12_ESCALA_ARDOR           |     8     |   12     |        7         |
| CLEARSTEM - WP - NEW TEST        |     9     |   11     |        6         |

La brecha entre "anuncios" y "conceptos" son los `- Copia`: el duplicado interno infla el conteo
de anuncios pero **no agrega una sola entrada de recuperación** para Andromeda. Es el mismo
anuncio dos veces.

⚠️ **NO HAGAS UN CAMBIO GLOBAL A CIEGAS.** La regla del duplicado viene de Clase 6 (Mercy) y el
sistema afirma que baja el CPA. La hipótesis es que el MECANISMO por el que funciona ("darle
opciones a Meta") se cumple MEJOR con 2 conceptos distintos que con 2 copias — pero eso se testea,
no se decreta. Hacé lo siguiente:

--- 2A. `.claude/agents/ETAPA-6.md` ---
Reemplazá la viñeta que empieza con "**Regla del anuncio duplicado dentro del conjunto:**" por:

- **Regla de los 2 anuncios por conjunto:** Cada conjunto lleva **2 anuncios**, nunca 1. Hay dos
  variantes y la elección se declara explícitamente en el output:
  · **DUPLICADO (default histórico):** el mismo creativo dos veces. Mecanismo de Mercy en Clase 6
    ("darle opciones a Meta"); el sistema lo viene usando y el CPA baja. El porcentaje exacto NO
    aparece en las clases auditadas — no citar un número.
  · **DOS CONCEPTOS (variante en prueba desde 31-jul):** dos creativos conceptualmente distintos
    del MISMO ángulo. Mismo número de anuncios, mismo presupuesto, misma estructura — pero el doble
    de entradas de recuperación para Andromeda, que en 2026 rankea por creativo y no por audiencia
    (la calidad del creativo explica ~56% del resultado y el benchmark es 8-12 conceptos distintos
    por campaña; un duplicado no cuenta como concepto).
  Mientras el test no cierre, el default sigue siendo DUPLICADO. Ver el TEST DE DIVERSIDAD abajo.

--- 2B. Agregá al final de la sección de reglas de `ETAPA-6.md` ---

- **TEST DE DIVERSIDAD CONCEPTUAL (abierto 2026-07-31, leer antes de cerrarlo):** TINNIDROP corre
  4 réplicas equivalentes (2🟦 CP1 · 3🟦 GTR1 · 4🟦 GTR7 · 5🟦) con los mismos ángulos, la misma
  página y el mismo presupuesto. Es un experimento natural que no cuesta pauta extra:
  · **CONTROL** — 2🟦 y 3🟦 se quedan con el duplicado (2 anuncios idénticos por conjunto).
  · **TRATAMIENTO** — 4🟦 y 5🟦 pasan a 2 conceptos DISTINTOS del mismo ángulo por conjunto.
  · No tocar presupuestos ni ángulos durante el test: la única variable que cambia es el 2º anuncio.
  · Leer a nivel de ÁNGULO (nunca por conjunto) cuando ambos brazos hayan cumplido su Presupuesto
    de Decisión (1 × break-even). Métrica de corte: CPA real por LucidSales. Secundaria: CPM y
    frecuencia (si la diversidad funciona, el CPM debería bajar y la frecuencia crecer más lento).
  · ⚠️ Con 4 réplicas y pocas ventas por celda esto NO da significancia estadística sola: es una
    señal direccional. Si el tratamiento gana ≥20% en CPA sostenido 2 ventanas, se cambia el default.
    Si queda a <15%, se declara empate y se mantiene el duplicado.
  · Registrar en `PRODUCTOS/_EVENTOS.csv` una fila `CAMBIO_CREATIVO` por cada réplica que se toque,
    con motivo "test diversidad conceptual brazo TRATAMIENTO" — si no, ETAPA-7 va a leer el cambio
    como si fuera el ángulo.
  · Al cerrarlo, escribir el resultado en `PRODUCTOS/_APRENDIZAJES.csv` (alcance GLOBAL) y actualizar
    esta regla y la de CLAUDE.md nº 9.

--- 2C. `CLAUDE.md` ---
En REGLAS OPERATIVAS FIJAS y en REGLAS DEL ORQUESTADOR nº 9, dejá la regla como "2 anuncios por
conjunto (nunca 1)" y agregá que la variante DUPLICADO vs DOS CONCEPTOS está en prueba, remitiendo
a ETAPA-6. No borres la referencia a Clase 6.

--- 2D. FASE 2 / escalado: aplicar el benchmark completo ---
En ETAPA-6 FASE 2, la campaña de escalado debe salir con **8-12 conceptos distintos**, no 4.
La infraestructura ya existe y está sin usar: `PLANTILLAS_ADS.md` tiene 15 estilos visuales y
`PRODUCTOS/_DIM_CREATIVOS.csv` ya tiene el campo `bloque_concepto`. En FASE 2 el objetivo es
volumen, no atribución, así que acá sí conviene la diversidad máxima.

⚠️ **NO TOQUES FASE 1.** Los 6 conjuntos con 1 creativo cada uno son el instrumento de MEDICIÓN:
si se meten 3 creativos por conjunto se pierde saber qué ángulo ganó. Andromeda premia diversidad,
pero el objetivo de FASE 1 es aprender, no entregar barato. Sacrificar la atribución ahí sale más
caro que el CPM que se ahorra.

═══════════════════════════════════════════════════════════════════════════
TAREA 3 — huecos de data detectados (arreglar o dejar anotado)
═══════════════════════════════════════════════════════════════════════════
a) `PRODUCTOS/_DIM_PRECIOS.csv` tiene una fila `VARICOSE / 3x / Q319` en estado **REVISAR**:
   `2_DATA_PRODUCTO.txt` dice que ese precio se eliminó el 09-jul, pero LucidSales registra 6 de
   las 9 ventas del producto a Q319. Confirmá con el operador si sigue vivo en el bot y ajustá.
b) Producto **NAD+ Selerb X60** (Dropi ID 1646, Q257, 2 unidades, costo Q55/u, margen Q109) está
   vendiendo y NO existe en el sistema: falta escalera completa, costeo, fila en `_PORTAFOLIO.txt`
   y en `_DIM_PRODUCTOS.csv`. Está cargado en `_DIM_PRECIOS.csv` como SIN_REGISTRAR.
c) **BODY COACH**: el operador lo vende 2x1 y 4x2 (costo ~Q35/u). No está en el sistema. Si lo va
   a trackear, pedirle precios y costo y darle de alta.
d) `_DIM_PRODUCTOS.csv` tiene NUSAVA en `fila_costeo_q=70` (venía del supuesto "2 frascos = Q70").
   Dropi confirma que el costo real por unidad de pedido es **Q55** → le corresponde la fila Q54/Q55.
   Cambia poco el CPA objetivo (Q31.3 → Q30.8) pero conviene corregirlo para que la tabla no mienta.
e) `otros_gastos_q = Q2.08` en `_TASA_ENTREGA.csv` es un residuo SIN IDENTIFICAR (era la diferencia
   entre `total_gastos Q10.67` y `admin Q4 + devolución Q4.59` en `_DIM_COSTEO.csv`). Se conserva
   como colchón visible. Si aparece de dónde sale, renombrarlo; si se confirma que no existe, 0.

═══════════════════════════════════════════════════════════════════════════
QUÉ NO TOCAR
═══════════════════════════════════════════════════════════════════════════
· `PRODUCTOS/_FACT_VENTAS.csv` y `_FACT_ENTREGA.csv` — solo los escribe la auditoría nocturna.
· La tarea programada `auditoria-nusavab12-diaria` (8 PM) es la ÚNICA del sistema. No crear otra:
  dos escritores la misma noche = doble conteo real de ventas.
· Ningún número del dashboard se escribe a mano. Si falta una regla, se AGREGA AL SCRIPT
  (`Ads/_TOOLS/gen_dashboard.py`) para que salga sola.
· Los break-even NO se hardcodean en ningún lado: se DERIVAN de `_DIM_PRECIOS.csv` + `_TASA_ENTREGA.csv`.

Al terminar todo: `python Ads/_TOOLS/gen_dashboard.py` y confirmá que imprime
`0 filas sin dimension`. Después resumime en 5 líneas qué quedó hecho y qué quedó pendiente.
````

---

## ESTADO AL 31-JUL

| | |
|---|---|
| ✅ | `_DIM_PRECIOS.csv` creado · escalera flexible por producto |
| ✅ | `_TASA_ENTREGA.csv` con los parámetros de logística medidos |
| ✅ | `_DIM_PRODUCTOS.csv` con break-even v3 |
| ✅ | `_DIM_CONJUNTOS.csv` con los 3 ejes del avatar, 54 conjuntos rellenados |
| ✅ | `gen_dashboard.py` — ganancia por ticket real, motor de 9 acciones, cortes por producto, tabla maestra |
| ✅ | `CLAUDE.md` — toda la doctrina nueva |
| ✅ | Tarea programada consolidada a una sola, 8 PM |
| ✅ | `ETAPA-2.md` (Tarea 1A) — bloque CLASIFICACIÓN MEDIBLE insertado tras "Nivel de conciencia" |
| ✅ | `ETAPA-GUARDAR-PRODUCTO.md` (Tarea 1B) — 3 columnas en SALIDA 4 + vocabularios |
| ✅ | `ETAPA-6.md` (Tarea 2A/2B/2D) — regla de los 2 anuncios, test de diversidad, benchmark 8-12 en FASE 2 |
| ✅ | `CLAUDE.md` (Tarea 2C) — REGLAS OPERATIVAS FIJAS + REGLAS DEL ORQUESTADOR nº 9 |
| ✅ | Tarea 3d — NUSAVA `fila_costeo_q` 70 → 54, `costo_q` 70 → 55, `cpa_base_q` 31.31 → 30.80 |
| ✅ | `gen_dashboard.py` regenerado → `0 filas sin dimension` |
| ✅ | Tarea 3a — VARICOSE Q319: **resuelto**. El operador confirma que estuvo vivo hasta el **20-jul** (el 2_DATA decía 09-jul y estaba mal). Fila → HISTORICO 04-jul→20-jul, `n_ordenes` 0→6, se mantiene en la escalera para no romper la inferencia de unidades. `2_DATA_PRODUCTO.txt` de VARICOSE corregido. |
| ✅ | Tarea 3b — NAD+ Selerb X60: **cerrado, NO se da de alta**. Fue una prueba de landing, no un producto del sistema. Queda SIN_REGISTRAR (excluido del cálculo) con la decisión anotada para que no vuelva a salir como hueco. |
| ✅ | Tarea 3c — BODY COACH: **cerrado, no entra**. El operador nunca lo vendió (confundido con Glute Glow, anterior al sistema). No hay nada que registrar. |
| ➖ | Tarea 3e — `otros_gastos_q = Q2.08`: se conserva como colchón visible, ya documentado en `_TASA_ENTREGA.csv`. Sin acción hasta identificar el origen. |
