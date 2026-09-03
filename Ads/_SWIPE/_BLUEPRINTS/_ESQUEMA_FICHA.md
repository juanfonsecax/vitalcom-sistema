# ESQUEMA DE FICHA ESTRUCTURAL — v1.0

> **Qué es una ficha:** un creativo del mercado GT (de los 111 favoritos) con su ESTRUCTURA
> extraída a JSON y su CONTENIDO reemplazado por `{{VARIABLES}}`.
> **Una ficha por imagen.** `FICHAS/F001.json` … `FICHAS/F111.json`.
> Índice y orden de trabajo: `FICHAS/_MANIFIESTO.csv` (`score = dias + replicas*25`).

**Diferencia con los 4 blueprints A/B/C/D:** aquéllos son 4 estructuras canónicas escritas a mano
por el operador. Las fichas son la extracción sistemática de las 111. Cuando una ficha ES la
referencia de un blueprint existente, lo declara en `blueprint_equivalente` — no se duplica doctrina.

---

## Claves obligatorias

| Clave | Qué guarda |
|---|---|
| `ficha_id` | `F001`…`F111`. Ordenado por score descendente. Estable: no se renumera. |
| `schema_version` | versión de ESTE esquema |
| `origen` | archivo, anunciante, `ad_archive_id`, `dias_activo`, `replicas`, `score`. **No se edita a mano** — sale del manifiesto |
| `clasificacion` | `concepto_key` (los 8 del catálogo) · `variante_operador` · `estetica` · `formato` · `densidad` · `espacio_libre_objetivo` · `nivel_conciencia` · `rol_embudo` |
| `dispositivo_dominante` | **la frase que explica por qué este creativo es de este concepto.** Es lo que se replica |
| `lectura_estrategica` | qué vende y por qué funciona. 2-4 frases |
| `fondo`, `paleta`, `sistema_tipografico` | la capa visual, con `{{VARIABLES}}` donde el color deriva del producto |
| `condiciones_de_captura` | **solo en `organico_ugc`.** Cómo se toma la foto: sujeto, ángulo, luz, qué imperfección se conserva y qué NO se hace. Ver abajo |
| `zonas` | el mapa: posición, escala, formato de item, restricción de palabras y el `{{PLACEHOLDER}}` |
| `secuencia_lectura` | el orden en que el ojo recorre las zonas. Define la jerarquía |
| `reglas_duras` | lo que invalida la réplica si se rompe. **Siempre en positivo** (los modelos de imagen leen mal las negaciones) |
| `variables_requeridas` | qué campos de la ficha de producto hacen falta para llenarla |
| `cuando_usar` / `cuando_no_usar` | criterio de selección para el motor de lotes |
| `sellos_y_claims_observados` | **registro factual** de los sellos, badges, garantias y claims que la pieza USA. Es inventario, no auditoria |
| `canonico_id` | a qué blueprint canónico pertenece. `null` hasta la fase de agrupación |
| `blueprint_equivalente` | `A_autoridad_medica`…`D_transformacion_temporal` o `null` |

---

## Reglas de extracción

1. **La ficha describe lo que la imagen HACE, no lo que debería hacer.** Si el original no tiene
   precio, la ficha no inventa una zona de precio.
2. **El contenido siempre va como `{{VARIABLE}}`.** Nunca el texto literal del anunciante:
   copiar su copy es copiar su producto, no su estructura.
3. **Las restricciones de palabras se cuentan sobre el original.** Definen el peso visual del
   bloque: un titular de 8 palabras en un slot de 4 rompe la jerarquía.
4. **El banco documenta, no audita.** Estas piezas ya se validaron con dinero real en el mercado:
   la ficha registra **lo que la pieza hace**, no lo que convendria que hiciera. No se anotan
   advertencias de riesgo, no se proponen sustituciones y no se suaviza nada.
   `sellos_y_claims_observados` es un **inventario**: que sellos, badges, garantias y claims lleva
   la pieza, tal como los lleva.

   Lo unico que se traduce al replicar es el **registro sanitario de pais**, porque es un dato de
   producto y no una decision creativa:

   | Sello del original | Al replicar |
   |---|---|
   | **FDA (EEUU)** | **se mantiene** — los productos son de origen americano |
   | **INVIMA (Colombia)** | **MSPAS**, el registro local guatemalteco |
   | cGMP, GMO free, lab tested, sellos de fabrica | **se mantienen** |

   Las dos banderas conviven: EEUU = origen · Guatemala = registro
   (convencion del operador, `_LEEME.md`).


5. **`formato` es el ratio, no la resolución.** La cosecha reescaló todo al alto 600 conservando
   la proporción.
6. **Estética y concepto son ortogonales** (`_BANCO_CREATIVOS/_LEEME.md`): `estetica` es
   `cartel_publicitario` u `organico_ugc`; `concepto_key` es qué muestra. No se mezclan.

---

## `condiciones_de_captura` — las fichas UGC (agregado en tanda 02)

En `cartel_publicitario` lo que se replica es el **layout**: dónde va cada cosa.
En `organico_ugc` el layout casi no existe — lo que hace ganar la pieza es que **no parezca un
anuncio**. Describirla con `zonas` y posiciones produce exactamente lo contrario: un cartel
disfrazado de foto casera, que es peor que un cartel.

Por eso estas fichas llevan una clave extra que las de cartel no tienen:

```json
"condiciones_de_captura": {
  "sujeto":           "quién y cuánto se ve (mano, dos manos, sin rostro)",
  "angulo":           "cenital, frontal, a la altura del pecho",
  "luz":              "natural de ventana, sin flash ni rebote",
  "que_se_conserva":  "el relleno arrugado, los pliegues, la sombra real",
  "que_NO_se_hace":   "recorte, fondo plano, producto flotando, brillo de estudio",
  "regla":            "si la foto se ve producida, deja de probar y vuelve a ser cartel"
}
```

**Regla del escritor:** una ficha con `estetica: organico_ugc` que no declare
`condiciones_de_captura` **falla al escribirse**. En las de cartel la clave se omite del JSON,
no se escribe vacía.

Las fichas UGC igual llevan `zonas`, porque el texto sobreimpreso sí tiene posición — pero las
zonas son pocas y el peso de la réplica está en las condiciones de captura.
