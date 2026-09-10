# HANDOFF — Regenerar las 5 piezas de TINNIDROP FASE 2

**Fecha:** 2026-09-07 · **Para:** una sesión nueva · **Ejecuta:** `etapa-render` (Sonnet)

---

## POR QUÉ SE REGENERAN

Las 5 imágenes actuales dicen **"Fórmula Sublingual"** impreso en la pieza. El producto es
**ÓTICO** (spray para el oído), confirmado por el operador el 07-sep-2026.

**El prompt fuente ya está corregido** — tanto en `Ads/_TOOLS/armar_prompts_fase2.py` como en
`PROMPTS_FASE2_ACCESIBILIDAD_MEDICO.txt`. Ahora dicen *"Aplicación Ótica: actúa directo en el
oído, sin pasar por el estómago"*. Solo falta volver a renderizar.

Las 5 filas de `_DIM_CREATIVOS.csv` están marcadas con `REGENERAR` en `notas`.

---

## LO PRIMERO, ANTES DE INVOCAR NADA

**El operador tiene DOS Chrome conectados.** Hay que preguntarle cuál con `AskUserQuestion`
y dejarlo seleccionado con `switch_browser` **en la sesión principal**.

`etapa-render` **no puede hacer esto**: los subagentes no tienen `AskUserQuestion` y se traban.
Una vez seleccionado, la elección persiste y el subagente la hereda. Que **no** llame
`list_connected_browsers`.

El operador debe tener la sesión de **chatgpt.com abierta y logueada** (cuenta JUANESR, plan Go).

---

## LOS 5 CONCEPTOS

Producto: `TINNIDROP` · Ángulo: `ACCESIBILIDAD_MEDICO` · Cuenta: `GTR0`
Destino de todos: `Ads/MEDIA_TINNIDROP/`
Foto del producto (la misma en los 5): `Ads/MEDIA_TINNIDROP/TINNIDROP_R1_VIVIRCONESO.png`

| # | Canónico | Archivo de salida | Imagen de referencia (swipe) |
|---|---|---|---|
| 1 | CN05_LISTA_BENEFICIOS | `TINNIDROP_F2_CN05_ACCESIBILIDA.png` | `Ads/_SWIPE/_IMG/Camila_Recomienda/15_1364693855873597.jpg` |
| 2 | CN01_ANTES_DESPUES | `TINNIDROP_F2_CN01_ACCESIBILIDA.png` | `Ads/_SWIPE/_IMG/Aranza_Glow/08_964174726362714.jpg` |
| 3 | CN02_TIMELINE_PROGRESION | `TINNIDROP_F2_CN02_ACCESIBILIDA.png` | `Ads/_SWIPE/_IMG/Tiendas_KetsalStore/05_1411590777481139.jpg` |
| 4 | CN10_PRUEBA_SOCIAL | `TINNIDROP_F2_CN10_ACCESIBILIDA.png` | `Ads/_SWIPE/_IMG/Teyra/08_1536827234832370.jpg` |
| 5 | CN04_ESCALERA_PRECIOS | `TINNIDROP_F2_CN04_ACCESIBILIDA.png` | `Ads/_SWIPE/_IMG/Valle_Lo_Vende/07_1476571934274805.jpg` |

**Los prompts salen de** `Ads/MEDIA_TINNIDROP/FASE2_ACCESIBILIDAD_MEDICO/PROMPTS_FASE2_ACCESIBILIDAD_MEDICO.txt`
(ya corregidos a ótico). Hay que aplanarlos a un párrafo, pasarlos a ASCII y traducir las rutas
a "la primera adjunta / la segunda adjunta" — todo eso está en la skill.

Sobrescriben los archivos actuales. Presupuestar **~2,5 min por imagen** ≈ 13 minutos.

---

## DATOS DEL OPERADOR YA CONFIRMADOS — no volver a preguntarlos

- **Todos los productos tienen MSPAS, FDA y garantía.** `[REG_MSPAS]` = `NS02026-GT3147` ·
  `[REG_FDA]` = `30045469041`. Viven en `DOCTRINA/PLANTILLAS_DEFAULTS_OPERADOR.md`.
- **Se replica el dispositivo del ganador completo**: sellos, badges, certificaciones, estrellas
  y cifras de respaldo. No poner trabas de compliance sobre elementos del concepto.
- **El número de registro lo decide la referencia**: si la pieza del swipe muestra número, va el
  nuestro; si no lo muestra, el sello va sin número. Nunca uno fabricado.
- Garantía: **30 días**. El escalonado 30/60/90 por tier está en evaluación, no usarlo aún.

---

## DEFECTOS CONOCIDOS A CAZAR EN EL GATE

Todos vistos en la tanda de CLEARSTEM del 07-sep:

1. **Ortografía en palabras largas** — aparecieron `Desinfilaman` y `RESISTENCUA`. Leer la pieza
   palabra por palabra.
2. **Tildes perdidas en MAYÚSCULAS del CTA** — salió `PEDI EL TUYO` con `AQUÍ` bien acentuado.
   Efecto del prompt en ASCII.
3. **Número de registro inventado** — el modelo escribió `No. NS02025-GT2599` por su cuenta,
   incluso con la orden de no inventar.
4. **Voseo** en cierres y CTA.
5. **Paleta contra el avatar** — TINNIDROP es 45-65 mixto; la paleta del banco es VERDE.

---

## CÓMO ARRANCAR EN EL CHAT NUEVO

Pegar esto:

> Leé `PRODUCTOS/_AUDITORIAS/HANDOFF_2026-09-07_RENDER_TINNIDROP.md` y regenerá las 5 piezas
> de TINNIDROP FASE 2 con `etapa-render`.

El resto está acá y en `.claude/skills/generar-imagenes-chatgpt/SKILL.md`.

---

## AL TERMINAR

1. Reportar la tabla `CONCEPTO / ARCHIVO / BYTES / GATE`.
2. **Quitar el aviso `REGENERAR`** de las 5 filas de `_DIM_CREATIVOS.csv` (`creativo_id` que
   empieza con `TINNIDROP_F2`) — con escritor CSV real, nunca a mano (invariante 11).
3. Correr `python Ads/_TOOLS/validar_parametros.py` y confirmar
   *"ningún valor fuera del vocabulario"*.

---

## PENDIENTES QUE NO SON DE ESTE HANDOFF

- `CLEARSTEM_R1`–`R4`: 4 piezas en `PENDIENTE_GENERAR` desde el 26-jul, sin archivo.
- `CLEARSTEM_F2_CN02` dice `Desinfilaman` y `CLEARSTEM_F2_CN04` dice `RESISTENCUA` y salió en
  paleta ROSA contra la doctrina del avatar masculino. Ambas son candidatas a regenerar.
- Los 22 creativos del CSV siguen con `ad_id` vacío: **ninguno se ha publicado en Meta.**
  Ese es el cuello de botella real del sistema, más grande que generar.
