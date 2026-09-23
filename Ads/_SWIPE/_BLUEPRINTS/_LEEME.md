# SISTEMA DE REPLICACIÓN DE CREATIVOS GANADORES v1.0

> Autoría: operador, 2026-08-19. Bajado a disco el mismo día.
> **Reemplaza a `_SISTEMA_CREATIVOS_TESTEO.md`** (fuera del repo desde el 22-sep-2026, T9 — queda
> en el historial de git), que usaba prompts en
> prosa — exactamente el modo que este sistema identifica como fallido.

---

## La idea

Todo creativo ganador tiene dos capas. **La estructura es lo que factura; el contenido es lo que
cambia.** Cuando le pasás una imagen a un modelo y le decís "adaptá esto", el modelo no sabe cuál
capa es cuál: copia lo literal (el amarillo, el doctor) y pierde lo abstracto (la jerarquía, el
ritmo, los pesos). El blueprint es la estructura extraída a JSON con el contenido en `{{}}`.

**Regla de oro: el LLM nunca escribe el prompt de imagen. Llena variables.**

```
CAPA 1  BLUEPRINTS   4 JSON fijos, versionados, nunca se editan
CAPA 2  LLENADOR     blueprint + ficha -> el mismo JSON con {{}} resueltos
CAPA 3  RENDER       2-4 imágenes con rol declarado + envoltorio fijo + el JSON pegado literal
```

---

## Los 4 blueprints y su llave de medición

`blueprint_id` es la identidad de **producción** (qué estructura se renderiza).
`concepto_key` es la identidad de **medición** (cómo se lee en el CSV). Son capas distintas y
ambas viven: la histórica tiene 93 filas ya clasificadas por `concepto_key` y cambiar esa
taxonomía rompería la serie.

| `blueprint_id` | Referencia | `concepto_key` · variante | Brazo T01 |
|---|---|---|---|
| `A_autoridad_medica` | Candida Cleanse | `C2_BENEFICIOS` · colage-sintomas | A |
| `B_editorial_limpio` | Oftalmiel | `C2_BENEFICIOS` · ligera | B |
| `C_dolor_maximalista` | NeuraZenx | `C2_BENEFICIOS` · densa | C |
| `D_transformacion_temporal` | Astaxanthin | `C8_PROGRESION` | D |

Las 4 referencias del documento son **las mismas 4** que ya estaban confirmadas en
`PRODUCTOS/_TESTEOS.csv`. No hay que reelegir nada.

---

## Regulatorio en Guatemala: **MSPAS**

Ministerio de Salud Pública y Asistencia Social. Es el equivalente local del INVIMA colombiano.
Aplicado en los 4 blueprints. **Prohibido INVIMA (Colombia) y FDA (EEUU) en pauta guatemalteca.**

> **Y el sello solo va si el producto lo tiene de verdad.** El propio system prompt del llenador
> lo dice: *"Nunca inventes claims regulatorios, certificaciones ni sellos que no estén en la
> ficha."* Si el array `sellos` de la ficha está vacío, la zona se omite y se declara en
> `_faltantes`. Es la diferencia entre un creativo y un baneo.

---

## Los 5 choques con lo que ya estaba congelado

Detectados al bajar el documento. Los tres primeros cambian decisiones.

### 1. Formato — los blueprints dicen `1:1`, el test dice `4:5`
El swipe respalda el 1:1 (64 % de los ganadores contra 17 % de 4:5) y por eso el documento lo fija.
Pero `_TESTEOS.csv` congeló `formato_fijo: IMAGEN 4:5`, y el ME DIJERON que ya vendió corrió en 4:5.
Si T01 sale en 1:1, cambia formato **y** dispositivo a la vez y nada es atribuible.
**Resolución:** T01 corre 4:5 vía override en la ficha. El formato es su propio test (pendiente #5
del handoff), no un cambio a ciegas.

### 2. Arquitectura de precio — cada blueprint trae la suya
`A` un precio · `B` precio + tachado · `C` **2 tiers** · `D` **3 tiers**.
Dejados nativos, los 4 brazos difieren en precio además de en dispositivo. Es el mismo error que
el "brazo B sin precio", pero más grande. Además rompe la verificación de coherencia copy↔bot
(el bot arranca en Q178 · 1 unidad) y pisa al dueño de la oferta, que es `ETAPA-1.md`.
**Resolución:** bloque de precio idéntico en los 4, por override. La arquitectura nativa de cada
blueprint pertenece a FASE 2 / escalado, donde se optimiza conversión, no se mide.

### 3. El documento dice que D **no** aplica a TINNIDROP
PARTE 2, "Cuándo NO usarlo": *problemas no visualizables anatómicamente*. El tinnitus es
exactamente eso — no hay órgano que mostrar en tres estados. Y `regla_progresion` pide que el
estado 1 muestre el problema y el 3 el resultado: eso **es** un antes/después y viola compliance.
**Resolución:** D corre en **MODO DEGRADADO** (timeline por momento de uso) y queda **registrado
como degradado**, para que una derrota de D no se lea como "C8_PROGRESION no funciona".

### 4. "No correr los 4 conceptos" (PARTE 3) contra T01, que corre 4
El documento recomienda 2 conceptos por producto para no canibalizar el aprendizaje. T01 corre 4.
**Resolución:** manda el cálculo de potencia, que es más específico que la heurística — 25 ventas
por brazo detectan un 2×, y a presupuesto parejo eso llega en ~24 días. Se queda en 4.

### 5. Nombres de conjunto
Sigue vigente lo de `_SISTEMA_CREATIVOS_TESTEO.md`: el concepto va en el nombre del conjunto,
porque la convención de `ETAPA-6.md` asume que varía el ángulo y acá varía el concepto.
```
GTR0_TINNIDROP_MEDIJERON-C2LIGERA_R1
```
Si los 4 se llaman `..._MEDIJERON_R1..R4`, la regla 23 los suma como réplicas.

---

## Cómo se corre

1. Llenar la ficha del producto (`ficha_[slug].json`). 5 minutos.
2. Elegir concepto con la tabla de selección — o los 4, si es un test de concepto.
3. **Capa 2:** pasarle al LLM el blueprint + la ficha + el system prompt del llenador.
   Devuelve el mismo JSON con los `{{}}` resueltos y, si falta contenido, una clave `_faltantes`.
   **No inventa para rellenar.**
4. Leer los textos del JSON lleno. 30 segundos.
5. **Capa 3:** envoltorio fijo + el JSON pegado literal + las imágenes con su rol declarado.
6. QA con el checklist. Lo que falla se regenera.

**Roles de imagen:** `IMAGEN_1` = layout únicamente · `IMAGEN_2` = producto exacto ·
`IMAGEN_3` = identidad (solo A y C) · `IMAGEN_4` = paleta (opcional).

---

## QA — bloqueantes

1. Tildes y signos de apertura correctos
2. Precio exacto dígito por dígito
3. Empaque intacto, sin texto inventado
4. **Ningún sello ni certificación que no esté en la ficha**
5. Ningún bloque de texto superpuesto

De concepto: jerarquía visual comparada lado a lado con el ganador (entrecerrar los ojos: las
manchas de peso caen en los mismos lugares) · densidad contra `espacio_libre_objetivo` ·
`reglas_duras` cumplidas.

---

## Mantenimiento

- **Blueprint nuevo:** solo cuando un creativo facture 30+ días con estructura distinta a las 4.
- **Modificar uno existente:** solo si un cambio estructural ganó en test controlado. Sube versión.
- **Nunca** editar un blueprint para que quepa un producto. Si no calza, va en otro concepto —
  o corre en modo degradado y se registra como tal.
- Los ajustes por test van en `_OVERRIDES_TEST_*` de la **ficha**, nunca en el blueprint.


---

## Dos reglas que costaron una ronda de imagenes (19-ago)

### 1. Un override que contradice una zona SE ESCRIBE EN LA ZONA, nunca como nota al pie

En la ronda 1 el bloque `_override_T01` decia *"tiers ANULADO"*, pero la zona seguia diciendo
`"tiers": 2` y `"tiers": 3`. **Las imagenes C y D salieron con 2 y 3 precios.** El modelo de
imagen ejecuta la zona; una nota al final que la contradice pierde.

> Si el override cambia lo que se dibuja: **reescribir la zona y borrar las claves sobrantes**
> (`tier_2`, `tier_3`). La ausencia estructural es la instruccion mas fuerte que existe.
> El bloque `_override_T01` queda solo para lo que NO se dibuja (por que se cambio, modo degradado).

### 2. Nada de negaciones que nombren texto dibujable

Los modelos de imagen leen mal las negaciones. Escribir *"NO pongas MEJOR OFERTA"* mete ese
texto en el prompt y a veces lo dibuja igual. Toda restriccion se enuncia en **positivo**:

| Mal | Bien |
|---|---|
| `"NO generar 2 ni 3 niveles, ni MEJOR OFERTA / MAYOR AHORRO"` | `"Una sola card de precio, sin etiquetas comparativas de valor."` |
| `"No usar FDA ni INVIMA"` | `"El unico sello regulatorio es REGISTRO MSPAS, con bandera de Guatemala."` |
| `"NO incluir badge de FORMULA IMPORTADA"` | `"Sin badge premium de ningun tipo en la esquina superior."` |

---

## Convenciones de marca (operador, 19-ago)

| Tema | Regla |
|---|---|
| **Unidad** | El producto se llama **TRATAMIENTO**, nunca "frasco". |
| **Origen** | Todos los productos son de **ORIGEN AMERICANO** → bandera de **Estados Unidos**. |
| **Regulatorio** | **REGISTRO MSPAS** → bandera de **Guatemala**. |
| **Las dos banderas** | No se mezclan: EEUU = origen · Guatemala = registro y disponibilidad local. |
| **Garantia** | Siempre en **DORADO `#D4A017`**, resaltada. Nunca en el color de la paleta. |
| **Precio** | Siempre con precio de anclaje tachado. TINNIDROP: **Q178** hoy contra **Q298** antes. |
| **Verbos** | Sin restriccion (decision del operador). Sigue escrita en `CLAUDE.md`, `COPYWRITING_ADS.md` y `ETAPA-4.md` — actualizar alli o esos agentes la reimponen. |
