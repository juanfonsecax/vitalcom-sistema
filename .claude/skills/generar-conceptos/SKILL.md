---
name: generar-conceptos
description: FASE 2 (testeo de CONCEPTOS) — Genera N conceptos creativos para un producto a partir del banco de 111 piezas validadas del mercado GT, agrupadas en 22 blueprints canónicos. Selecciona qué estructuras aplican al producto (gates de aptitud), las llena con su data y entrega los prompts de imagen listos + las filas de registro para _DIM_CONJUNTOS.csv. Úsalo cuando el operador dice "dame N conceptos para [producto]", "generar conceptos", "creativos para FASE 2", "necesito los 10 creativos", "conceptos del ángulo ganador" o "usar el banco de creativos". Requiere ÁNGULO GANADOR confirmado.
tools: Read, Glob, Grep, Bash, Write
---

# GENERAR-CONCEPTOS — MOTOR DE LOTES DEL BANCO DE CREATIVOS

## Rol

Convierte el banco de **111 piezas validadas del mercado GT** en N creativos para
un producto propio. Es el motor de la **FASE 2 (testeo de CONCEPTOS)**: el ángulo
ya está fijo y validado por venta, y lo que se mide es qué **ejecución visual** lo
comunica más barato.

**Requiere ángulo ganador confirmado.** Sin él esta skill no corre — sería mover
ángulo y concepto a la vez, que es exactamente lo que `reglas-sistema` prohíbe (nada
sería atribuible).

> ⛔ **No se usa en FASE 1.** En el testeo de ángulos el concepto es FIJO
> (`C2_BENEFICIOS` variante ligera, el mismo layout en los 6 conjuntos). Rotar
> estructuras ahí destruye la atribución del ángulo. Ver `reglas-sistema` →
> "ÁNGULO vs CONCEPTO".

---

## DE DÓNDE SALE CADA COSA (un dato, un dueño)

| Insumo | Dueño |
|---|---|
| Las 111 fichas con su estructura extraída | `Ads/_SWIPE/_BLUEPRINTS/FICHAS/F001–F111.json` |
| Los 22 blueprints canónicos (familias estructurales) | `Ads/_SWIPE/_BLUEPRINTS/CANONICOS/CN*.json` |
| Qué canónico aplica a qué producto (gates) | `Ads/_TOOLS/seleccionar_canonicos.py` |
| Vocabulario de `concepto_key` y rotación de FASE 2 | `Ads/_SWIPE/_CATALOGO_CONCEPTOS.md` PARTE III |
| Prompt Maestro y los 15 estilos anti-fatiga | `DOCTRINA/PLANTILLAS_ADS_SECCIONES/05_PROMPT_MAESTRO_FASE2.md` + `06_ESTILOS_ANTIFATIGA.md` |
| Precios, CPA objetivo, break even | `PRODUCTOS/[X]/2_DATA_PRODUCTO.txt` |
| Tono y edad de la página | `.claude/agents/ETAPA-2.md` §ASIGNACIÓN DE FANPAGE (ya resuelto en `<pagina_asignada>`) |
| **El perfil y los textos del creativo, ya resueltos** | `PRODUCTOS/[X]/_PERFIL_CREATIVO.json` — **lo escribe esta skill** (PASO 1: el `perfil` del producto; PASO 3: agrega los textos de UN ángulo en `textos_por_angulo`) y lo lee `Ads/_TOOLS/armar_prompts_fase2.py`. Si falta, el script bloquea: no inventa |

**Qué nunca se inventa y qué sí:**

- **Nunca: precios ni dosis.** Si faltan en `2_DATA_PRODUCTO.txt`, se piden — no se
  rellenan con un valor plausible.
- **Los ingredientes salen de la investigación** del producto (`2_DATA_PRODUCTO.txt`,
  ETAPA-1B), nunca de una plantilla genérica.
- **La prueba social sí se puede generar**: cifras de clientes, sellos de respaldo,
  "comprobado". **Los números de registro sanitario no son prueba social**: son
  reales y salen de `DOCTRINA/PLANTILLAS_DEFAULTS_OPERADOR.md` — nunca se fabrican.

---

## INPUTS REQUERIDOS

```
PRODUCTO:            [nombre exacto, debe existir en PRODUCTOS/]
ANGULO_GANADOR:      [angulo_key confirmado por VENTA, agregado por angulo_key]
N_CONCEPTOS:         [default 10 — los 10 de la estructura 1-1-5 + 1-1-5 + 1-2-5]
PAGINA_ASIGNADA:     [de ETAPA-2]
```

Si falta el ángulo ganador → **detener** y pedirlo. Si el producto no tiene
carpeta en `PRODUCTOS/` → detener: sin `2_DATA_PRODUCTO.txt` no hay precios ni
componentes con los que llenar nada.

---

## PROCESO

### PASO 1 — Leer el producto y armar su PERFIL

Leer `PRODUCTOS/[X]/2_DATA_PRODUCTO.txt` y construir el perfil que consume el
selector. La plantilla vacía sale de:

```bash
python Ads/_TOOLS/seleccionar_canonicos.py --plantilla-perfil
```

Cada campo se responde **con evidencia del archivo del producto**, no por
intuición. Los que no se puedan sostener se dejan en `false` / `0`: es preferible
que un canónico quede fuera por dato faltante a que entre por optimismo y produzca
una pieza que no se sostiene.

Los tres que más deciden:

- **`resultado_visible_en_el_cuerpo`** — ¿el resultado se fotografía sin montaje?
  Varices y acné sí; tinnitus, memoria y sueño no. Decide **cómo** se arma la familia
  más grande del banco (`CN01_ANTES_DESPUES`): con fotografía si es visible, o con
  render anatómico si el mecanismo se localiza en el cuerpo
  (`mecanismo_localizable_en_el_cuerpo`). Solo sin ninguno de los dos queda fuera.

- **`tiers_de_oferta`** — sale del bloque de precios, no de lo que convendría.
- **`categoria`** (`dolor` | `estetica`) — define cuál concepto ocupa el 6º slot
  de la rotación (C3_SINTOMA o C7_DESEO).

**Guardar el perfil** en el bloque `perfil` de `PRODUCTOS/[X]/_PERFIL_CREATIVO.json`
(`"schema": "perfil_creativo/2"`). Ese archivo es el contrato con
`armar_prompts_fase2.py`: sin él, el script bloquea en vez de adivinar el perfil. Si el archivo ya
existe, el `perfil` y el resto de las claves del producto se actualizan en su lugar y
`textos_por_angulo` no se toca en este paso.

### PASO 2 — Seleccionar los canónicos

```bash
python Ads/_TOOLS/seleccionar_canonicos.py --perfil perfil.json -n 10
```

Devuelve `seleccion`, `aptos_no_elegidos` y `descartados` **con el motivo de cada
descarte**. La selección es determinista: los gates de `cuando_no_usar` no se
saltan a ojo.

**Reportar siempre los descartados al operador**, con su motivo. Que
`CN01_ANTES_DESPUES` (14 piezas, la familia más grande) quede fuera de un producto
es información, no un error a esconder.

Cómo quedan repartidos los 10 slots:

- **Slots 1-6** → los 6 `concepto_key` de la rotación de FASE 2, uno por slot.
  El slot 1 es siempre el **control** (`CN05_LISTA_BENEFICIOS`, C2 variante ligera):
  va en todos los productos y es lo que permite comparar entre ellos.
- **Slots 7-10** → ejecuciones estructuralmente distintas que **reusan
  `concepto_key`** ya presentes. Son 10 ejecuciones etiquetadas con 6 conceptos,
  no 10 conceptos: con 10 valores distintos nunca se acumulan observaciones.

### PASO 3 — Llenar el contrato de variables

Cada canónico trae su `contrato_variables`: lo que hay que producir para armar una
pieza de esa familia. Leer además su `ficha_referencia` completa
(`FICHAS/F0xx.json`) para las `zonas`, `secuencia_lectura` y `reglas_duras` finas.

Reglas al llenar:

1. **Persona del mercado del producto** en todo texto visible (`persona` de `PRODUCTOS/_DIM_MERCADOS.csv`: voseo GT — `vos`, `te`, `tu` — · tuteo CO).
2. **Respetar `restriccion_palabras`** de cada zona. Un titular de 8 palabras en un
   slot de 4 rompe la jerarquía que hacía funcionar la pieza original.
3. **`reglas_duras` siempre en positivo** — los modelos de imagen leen mal las
   negaciones.
4. **Nunca copiar el texto del anunciante original.** La ficha guarda estructura;
   el contenido lo pone el producto propio.
5. **El bloque de precio no se decide creativo por creativo.** La arquitectura de
   oferta tiene dueño (`.claude/agents/ETAPA-1.md`), y la regla de precio es
   **máx 3 de 6 ads con precio, ideal 2 de 6**. Si el ad anuncia el precio de 1
   unidad y el bot arranca en 2, se rompe la coherencia copy↔bot.
6. **Compliance de ADS** (`DOCTRINA/COPYWRITING_ADS.md`): lenguaje de apoyo
   ("apoya / ayuda a / acompaña"), nunca "cura / elimina / logra / trata". Es texto
   del anuncio: Meta lo lee.

**Guardar los textos** del ángulo en `textos_por_angulo[ANGULO_KEY]` del mismo `_PERFIL_CREATIVO.json`
(la clave es idéntica al `angulo_key` de `_DIM_CONJUNTOS.csv`):

```json
"textos_por_angulo": {
  "ANGULO_KEY": {"textos": {...}, "textos_notas": {...}, "compliance_ads": {...}}
}
```

`textos_notas` y `compliance_ads` son opcionales. El perfil es del producto, pero los textos son de
**un** ángulo: esta skill agrega o reemplaza SOLO la entrada del ángulo que está produciendo y nunca
borra las de otros ángulos. Si el ganador cambia y su entrada no existe, el script bloquea (nombrando
los ángulos que sí tienen textos) y esta skill produce la del nuevo.

| Campo | |
|---|---|
| `HOOK_TITULAR`, `SUB_HOOK`, `ACTIVOS_CLAVE` (lista), `GARANTIAS`, `CTA` | **obligatorios**: sin ellos el script bloquea |
| `PRODUCTO`, `DESCRIPTOR`, `SINTOMA_ANTES`, `RESULTADO_DESPUES` | opcionales |

**El texto del bot NO va en este archivo.** El flujo de LucidBot está **declarado** en
`DOCTRINA/PLANTILLAS_FLUJO_BOT.md` y lo renderiza `Ads/_TOOLS/gen_flujo_bot.py` en
`PRODUCTOS/[PK]/FLUJO_LUCIDBOT.md`. Su regla choca con cualquier "adaptación" por ángulo: el
saludo es **FIJO, sin el dolor del ángulo y sin el nombre de la asesora**, y **no hay pregunta de
opciones**. El dolor va en el anuncio. Ningún generador de creativos escribe texto de bot.

### PASO 4 — Replicar el dispositivo tal como el banco lo documenta

**El banco documenta, no audita** (`_HANDOFF_FICHAS.md` §2). Las 111 piezas ya se
validaron con dinero real en el mercado GT: la ficha registra lo que la pieza
**HACE**, y acá se replica eso. No se anotan advertencias, no se proponen
sustituciones y **no se suaviza ninguna familia**.

Esto incluye explícitamente a **`CN01_ANTES_DESPUES`** — la familia más grande del
banco (14 piezas). Se produce como el banco la documenta: dos estados del mismo
sujeto, el producto de bisagra en la costura. No se desvía a "dividido
problema/beneficio" ni a ninguna otra versión atenuada.

Lo único que se traduce al replicar, por ser **dato de producto y no decisión
creativa**, es el registro sanitario de país:

| Sello del original | Al replicar |
|---|---|
| **FDA (EEUU)** | **se mantiene** — los productos son de origen americano |
| Registro sanitario de otro país (INVIMA, MSPAS…) | el registro del **mercado del producto** (`registro_sanitario` de `_DIM_MERCADOS.csv`; GT: MSPAS · CO: INVIMA, con su número pendiente del operador) |
| cGMP, GMO free, lab tested, sellos de fábrica | **se mantienen** |

Lo que sí se respeta es que **los datos sean del producto real**: precios, dosis,
activos, cifra de clientes y testimonios salen del `2_DATA_PRODUCTO.txt`. Eso no
es suavizar el creativo — es no llenar una zona con un número inventado.

### PASO 5 — Escribir los entregables

**(a) Los prompts de imagen** → `Ads/MEDIA_[PRODUCTO]/FASE2_[ANGULO]/PROMPTS_FASE2_[ANGULO].txt`

Un bloque por concepto, con el **Prompt Maestro de `DOCTRINA/PLANTILLAS_ADS_SECCIONES/05_PROMPT_MAESTRO_FASE2.md` YA
RELLENADO** — todas las `[VARIABLES]` resueltas, sin citas de clase y sin
`[PENDIENTE]`. Cada bloque lleva:

```
── C[NN] · [canonico_id] · concepto_key: [CX_...] · ref [F0xx] ──
Archivo destino:  [PRODUCTO]_C[NN]_[ETIQUETA].png
Lleva precio:     [SI/NO]
Estilo anti-fatiga: [uno de los 15, distinto al del concepto anterior]
Dispositivo a replicar: [dispositivo_canonico, en una línea]

[PROMPT COMPLETO, listo para pegar en Gemini/ChatGPT con la foto del producto]
```

**(b) Las filas de registro** para `PRODUCTOS/_DIM_CONJUNTOS.csv`, con
`concepto_key` poblado (nunca `SIN_CLASIFICAR`) y `canonico_id` en `notas`. Sin
esto el test corre y **no se puede leer después**: la columna que mide el concepto
queda vacía.

Escribir el CSV **con un escritor CSV real, nunca a mano** — todo campo de texto
libre con comas va entre comillas dobles (invariante 11 de `reglas-sistema`).

**(c) El plan de campaña** → `PRODUCTOS/[X]/4_PLAN_ESCALADO.txt` (plantilla en
`DOCTRINA/ESCALADO/08_PLAN_ENTREGABLE.md` §7). Se **sobrescribe** y sube `v[N]`. Prohibido dejar
archivos sueltos de reruns.

---

## GUARDARRAÍLES

1. **Sin ángulo ganador confirmado, no corre.** Y el ganador se declara agregando
   por `angulo_key`, nunca por conjunto-semana (invariante 1 de `reglas-sistema`).
2. **Un `concepto_key` no se repite mientras queden conceptos sin usar.** La gracia
   de la fase es medir conceptos distintos, no ejecuciones del mismo.
3. **`concepto_key` sale del vocabulario cerrado de 8** (`_CATALOGO_CONCEPTOS.md`
   §8). No inventar valores nuevos: con más valores nunca se acumulan
   observaciones.
4. **La regla de lectura del resultado es replicación, no ranking:** un concepto
   se corona si queda arriba en **2 de sus 2** apariciones. Arriba en 1 de 2 =
   ruido, se repite. Sin entrega en ninguna = `SIN_ENTREGA`, nunca `PERDEDOR`.
5. **No se cambia el bot en la misma corrida.** Una variable a la vez: si se mueven
   conceptos y flujo juntos, ningún resultado es atribuible.
6. **La banda de edad se hereda del producto, no se reabre acá** (APR-060: es la
   variable más cara del sistema). Si el `2_DATA_PRODUCTO.txt` dice 45-60, es 45-60.
7. **Los prompts se entregan también en el chat**, parte por parte y con
   checkpoint, además de escribirse en disco (preferencia del operador).

---

## SALIDA AL OPERADOR

Cerrar siempre con este resumen, en este orden:

```
CONCEPTOS GENERADOS — [PRODUCTO] · ángulo [ANGULO_GANADOR] · v[N]

| # | canónico | concepto_key | ref | precio | estilo |
|---|---|---|---|---|---|
(N filas)

DESCARTADOS Y POR QUÉ:
(canónico → motivo del gate; incluir los que quedaron aptos pero no entraron)

ARCHIVOS ESCRITOS:
□ PRODUCTOS/[X]/_PERFIL_CREATIVO.json (perfil + textos_por_angulo[ANGULO])
□ Ads/MEDIA_[PRODUCTO]/FASE2_[ANGULO]/PROMPTS_FASE2_[ANGULO].txt
□ filas en PRODUCTOS/_DIM_CONJUNTOS.csv (concepto_key poblado)
□ PRODUCTOS/[X]/4_PLAN_ESCALADO.txt

SIGUIENTE PASO MANUAL: generar las N imágenes con la foto real del producto
adjunta, guardarlas con el nombre exacto de "Archivo destino".
```
