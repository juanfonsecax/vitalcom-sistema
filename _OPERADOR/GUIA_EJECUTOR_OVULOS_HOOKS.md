# Guía para el ejecutor — Ganchos directos en los 6 anuncios de FASE 1 de OVULOS_PURITY

Fecha: 2026-09-29 · Decisión del operador: los ganchos nombran el SÍNTOMA y, donde aplica, "candidiasis".
Esta guía está completa: no hay que decidir nada de copy. Solo reemplazar texto exacto y validar.

## Reglas (no negociables)
- Palabras permitidas: mal olor íntimo, olor a pescado, flujo, picazón, ardor, candidiasis.
- Prohibidas en anuncios e imágenes: "infección", "vaginitis", "vagina", "cura/curar", "elimina".
- NUNCA escribir palabras alteradas para esquivar a Meta (ej. "inf3cción", "1nfección"): Meta lo castiga como evasión.
- No tocar nada más: ni precios (los 6 anuncios siguen SIN precio), ni beneficios, ni props, ni el bot.
- No editar CSV a mano. No tocar plantillas, doctrina ni scripts.

## Archivos a editar (solo estos 2)
1. `PRODUCTOS/OVULOS_PURITY/_PLAN.json` — campo `conjuntos[n].prompt_imagen` (bloque 【3】HOOK) y `conjuntos[n].copy.textos[0]` (primera línea).
   Es JSON: editarlo con un script de Python (`json.load` → reemplazar → `json.dump(..., ensure_ascii=False, indent=2)`), nunca con buscar/reemplazar de texto plano (los saltos de línea están escapados como `\n`).
2. `PRODUCTOS/OVULOS_PURITY/1_HACER_MANUAL.txt` — los mismos textos, que aparecen ahí en texto plano (buscar/reemplazar normal).

## Reemplazos exactos

### A. Gancho de la imagen (bloque 【3】HOOK de cada prompt)
En cada prompt hay dos partes que cambian: la frase resaltada en celeste y el texto del gancho.

| n | Buscar (frase resaltada) | Reemplazar por | Buscar (gancho, 2 líneas) | Reemplazar por |
|---|---|---|---|---|
| 1 | `La frase "CON ÉL" va en celeste profundo` | `La frase "DESPUÉS DE ESTAR CON ÉL" va en celeste profundo` | `"¿POR QUÉ VUELVE ESE OLOR` + salto + `DESPUÉS DE ESTAR CON ÉL?"` | `"¿MAL OLOR ÍNTIMO QUE VUELVE` + salto + `DESPUÉS DE ESTAR CON ÉL?"` |
| 2 | `La frase "SIEMPRE VUELVE" va en celeste profundo` | `La palabra "CANDIDIASIS" va en celeste profundo` | `"¿ÓVULOS, CREMAS, PASTILLAS…` + salto + `Y SIEMPRE VUELVE?"` | `"¿CANDIDIASIS QUE VUELVE` + salto + `AUNQUE USES ÓVULOS Y CREMAS?"` |
| 3 | `La frase "Y AUN ASÍ" va en celeste profundo` | `La frase "AUNQUE USES PROTECTOR" va en celeste profundo` | `"¿PROTECTOR TODOS LOS DÍAS` + salto + `Y AUN ASÍ?"` | `"¿FLUJO QUE MANCHA TU ROPA INTERIOR` + salto + `AUNQUE USES PROTECTOR?"` |
| 4 | `La frase "HASTA EN LA ROPA" va en celeste profundo` | (sin cambio) | `"¿POR QUÉ ESE OLOR SE NOTA` + salto + `HASTA EN LA ROPA?"` | `"¿OLOR A PESCADO QUE SE NOTA` + salto + `HASTA EN LA ROPA?"` |
| 5 | `La palabra "SIGUE" va en celeste profundo` | `La frase "MAL OLOR ÍNTIMO" va en celeste profundo` | `"ME LAVO TODO EL DÍA…` + salto + `¿Y POR QUÉ SIGUE?"` | `"¿TE LAVAS TODO EL DÍA` + salto + `Y EL MAL OLOR ÍNTIMO SIGUE?"` |
| 6 | `La frase "POR SEPARADO" va en celeste profundo` | `La frase "8 RAÍCES" va en celeste profundo` | `"¿JABÓN, CREMA Y ÓVULO` + salto + `POR SEPARADO?"` | `"¿OLOR, PICAZÓN Y FLUJO A LA VEZ?` + salto + `8 RAÍCES EN 3 PERLAS"` |

("+ salto +" = el salto de línea que ya existe entre las dos líneas del gancho; se conserva.)

### B. Primera línea del copy (solo la variación 1 de cada ángulo = `copy.textos[0]`)
| n | Buscar (primera línea exacta) | Reemplazar por |
|---|---|---|
| 1 | `Después de estar con él… otra vez ese olor 😔` | `¿Mal olor íntimo que vuelve después de estar con él? 😔` |
| 2 | `Óvulos, cremas, pastillas… y siempre vuelve 😩` | `¿Candidiasis que vuelve aunque uses óvulos y cremas? 😩` |
| 3 | `Protector todos los días… y aun así manchaba la ropa interior 😣` | `¿Flujo que te mancha la ropa interior aunque uses protector? 😣` |
| 4 | `Cuando ese olor se nota hasta en la ropa 😰` | `¿Olor a pescado que se nota hasta en la ropa? 😰` |
| 5 | `Me lavo todo el día… y el olor sigue 😩` | `¿Te lavas todo el día y el mal olor íntimo sigue? 😩` |
| 6 | `Jabón, crema, óvulo, pastilla… ¿y seguía igual? 🤯` | `¿Olor, picazón y flujo a la vez? 🤯` |

## Verificación (correr y pegar el resultado al operador)
1. Cada reemplazo debe ocurrir exactamente 1 vez en `_PLAN.json` y al menos 1 vez en `1_HACER_MANUAL.txt`. Si un texto no aparece, DETENERSE y reportar cuál (no inventar otro).
2. `python Ads/_TOOLS/gen_plan.py --validar PRODUCTOS/OVULOS_PURITY/_PLAN.json` → exit 0.
3. `python Ads/_TOOLS/verificar_producto.py OVULOS_PURITY` → "1/1 pasan el gate".
4. Buscar en ambos archivos que NO aparezcan: `infección`, `vaginitis`, `$84.900` dentro de los prompts de imagen.
5. No commitear.

## Al terminar
El operador genera las 6 imágenes con los prompts actualizados (tabla de nombres de archivo en la sección de prompts de `1_HACER_MANUAL.txt`).
