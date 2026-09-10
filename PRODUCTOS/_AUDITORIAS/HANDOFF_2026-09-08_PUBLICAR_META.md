# HANDOFF — Publicar los creativos de FASE 2 en Meta por MCP

**Fecha:** 2026-09-08 · **Reescrito el 08-sep tras verificar contra Meta** · **Estado verificado en Meta, no en el CSV**

---

## EL DIAGNÓSTICO DE LA MAÑANA ERA EQUIVOCADO

La versión anterior de este handoff decía **"10 creativos generados y CERO publicados"**, leyendo la
columna `ad_id` vacía de `_DIM_CREATIVOS.csv`. Falso.

**TINNIDROP ya estaba publicado y gastando.** La campaña `GTR0_TINNIDROP_F2-CONCEPTOS_20260907`
(`120257730530160595`) se creó el **06-sep 22:39**, arrancó el **07-sep 05:10** y llevaba **$23.46**
gastados en 10 anuncios ACTIVE cuando esta sesión la encontró.

> **La lección, que vale más que el caso:** el CSV no es evidencia del estado de Meta. Es una
> anotación que alguien tiene que escribir, y nadie la escribió. **Antes de publicar, preguntarle
> a Meta qué existe** — `ads_get_ad_entities` a nivel campaña cuesta una llamada. Publicar sobre
> el diagnóstico del CSV habría duplicado una campaña que ya estaba viva.

---

## LO QUE ESTA SESIÓN ENCONTRÓ Y HIZO

### 1. Las 5 piezas del 08-sep en disco están BIEN ✅

Verificadas una por una con `Read`. Frasco **AZUL/BLANCO marca SANARTE**, vía **ótica**,
MSPAS `NS02026-GT3147` y FDA `30045469041` correctos, precios 179/239/299 correctos.

### 2. Pero Meta NO estaba sirviendo esas piezas ❌

Los 10 anuncios vivos servían **la versión del 06-sep**: frasco marca **SOUTH MOON** y el texto
**"Fórmula Sublingual"**, en un producto que es spray **ÓTICO** marca **SANARTE**.

**Cómo se comprobó, sin inferirlo:**
- `ads_get_ad_preview` del anuncio vivo `120257730530170595` → devolvió la imagen SOUTH MOON.
- `ads_get_ad_images` → los 5 hashes de la biblioteca con esos nombres tienen
  `created_time = 06-sep 22:21`. Los PNG buenos en disco tienen `mtime = 08-sep 10:39–11:18`.
  **Mismo nombre de archivo, contenido distinto.**

### 3. El defecto también está en el COPY ⚠️ — no se arregla solo con la imagen

Los 10 anuncios comparten un copy que dice literal:

> *"Es una **fórmula botánica sublingual** diseñada para calmar la hiperexcitabilidad del nervio auditivo"*

Le está diciendo al cliente que se tome por la boca un spray que va en el oído. **Contradice al
frasco, al bot y al producto físico.**

### 4. Acciones ejecutadas

| Qué | Estado |
|---|---|
| **Pausar los 5 conjuntos** (decisión del operador) | ✅ Hecho — `effective_status: PAUSED` verificado en los 5. Gasto cortado. |
| **Escribir los `ad_id` reales en `_DIM_CREATIVOS.csv`** | ✅ Hecho — 5 filas, formato `adA;adB`. Backup en `.bak_20260908`. |
| **Registrar la pausa en `_EVENTOS.csv`** | ✅ Hecho — evento `PAUSA` del 08-sep con el motivo completo. |
| `validar_parametros.py` | ✅ Corre limpio: *"ningún valor fuera del vocabulario"*. |

**Nota sobre la pausa y el invariante 13:** no pasó por `decidir.py` **a propósito**. El invariante
gobierna las decisiones de CPA; esta no lo es. Es un defecto de producto — marca y vía de
administración equivocadas en el anuncio. `decidir.py` no tiene nada que decir sobre eso.

---

## LOS `ad_id` (ya escritos en el CSV)

Cada concepto corre en 2 anuncios idénticos (A y B) dentro de su conjunto.

| Concepto | Conjunto | `ad_id` (A;B) |
|---|---|---|
| CN05_LISTA_BENEFICIOS | `..._C1-CN05_R1` `120257730530360595` | `120257730530170595;120257730653480595` |
| CN01_ANTES_DESPUES | `..._C2-CN01_R1` `120257730644580595` | `120257730644650595;120257730663970595` |
| CN02_TIMELINE_PROGRESION | `..._C3-CN02_R1` `120257730644640595` | `120257730644590595;120257730709910595` |
| CN10_PRUEBA_SOCIAL | `..._C4-CN10_R1` `120257730644610595` | `120257730644620595;120257730726010595` |
| CN04_ESCALERA_PRECIOS | `..._C5-CN04_R1` `120257730644630595` | `120257730644600595;120257730716350595` |

Campaña: `120257730530160595` · Cuenta GTR0 `1665221077707961` · Página `498977893288095`.

---

## EL BLOQUEO QUE QUEDA — subir la media

**`ads_creative_upload_media` con `LOCAL_FILE` está deshabilitado para GTR0.** Devuelve:

> *"Local file upload is not available for ad account 1665221077707961. Use ... `upload_source=URL`"*

Y `URL` exige una URL pública — hostear los creativos en un servicio externo, que no se hace sin
pedirlo. **Así que la subida la hace el operador a mano**, en la biblioteca de medios de GTR0.

> ⚠️ **Al subirlos, NO reusar el nombre viejo.** Meta ya tiene 5 imágenes llamadas
> `TINNIDROP_F2_CNxx_ACCESIBILIDA.png` que son las malas. Subir con **sufijo `_V2`**
> (`TINNIDROP_F2_CN05_ACCESIBILIDA_V2.png`) para que el hash nuevo sea inconfundible. El bug de
> esta semana fue exactamente ese: dos contenidos distintos bajo el mismo nombre.

### Después de que el operador suba: los creativos son INMUTABLES

`ads_update_entity` **no puede cambiar el creativo de un anuncio existente**. La secuencia real es:

1. `ads_get_ad_images` → leer los 5 hashes nuevos (los `_V2`).
2. `ads_create_creative` ×5 — con el copy **corregido** de abajo, `page_id 498977893288095`,
   `call_to_action_type: WHATSAPP_MESSAGE`.
3. `ads_create_ad` ×10 (2 por concepto) **dentro de los 5 conjuntos que ya existen**.
   → Esto además cumple la **regla anti-ceguera** del `MCP_PLAYBOOK`: los conjuntos ya tienen
   `destination_type=WHATSAPP` + `promoted_object` y ya trackean. No crear conjuntos de cero.
4. Los 10 anuncios viejos quedan PAUSED y se archivan. **No borrarlos**: son la evidencia del
   gasto de $23.46 y el `ad_id` del CSV apunta a ellos.
5. Reescribir los `ad_id` del CSV con los nuevos.
6. **Control D+1 obligatorio** (`MCP_PLAYBOOK` §7.5) al día siguiente de reactivar.

### El copy corregido — usar este, no el que está vivo

Un solo cambio de fondo (`sublingual` → `de aplicación ótica`), lo demás intacto:

```
De dar vueltas en la cama con ese pitido agudo... a volver a dormir en silencio profundo 🛌✨

Quien no tiene zumbido en los oídos no entiende la desesperación de acostarse y escuchar ese
timbre constante que no te deja en paz.

Tinnidrop no es otra pastilla genérica. Es una fórmula botánica de aplicación ótica: actúa
directo en el oído, sin pasar por el estómago, para calmar la hiperexcitabilidad del nervio
auditivo.

🌙 ANTES: Noches en vela, dolor de cabeza y fatiga mental todo el día.
☀️ DESPUÉS: Silencio progresivo, descanso reparador y tranquilidad en tus días.

🔴 APROVECHÁ LA PROMO: 2 frascos por Q239 con Envío Gratis.

Pedilo hoy por WhatsApp y pagás en efectivo cuando el mensajero llegue a tu puerta 🏠👇
```

---

## DEUDAS ABIERTAS (no bloquean, pero están medidas)

1. **Los nombres de anuncio no llevan la FIRMA de 5 ejes** de `ETAPA-6.md`. Son
   `TINNIDROP_F2_CN01_ACCESIBILIDA A`, sin el ` ~ producto|angulo|concepto.canonico|NC|oferta|destino`.
   `validar_parametros.py` lo cobra: `canonico_id` ciego en **89.3% del gasto**, `destino_key` en
   **100%**. Al crear los 10 anuncios nuevos, ponerles la firma completa y esa deuda baja sola.

2. **La estructura publicada no es la que manda la doctrina.** Corre como **5 conjuntos × 1
   concepto**, que es forma de FASE 1. `CALENDARIO_ESCALADO` §1.7.2 pide **1-1-5 + 1-1-5 + 1-2-5**,
   y la campaña C en **otra cuenta** para no competirse a sí misma en la subasta. Además el
   `concepto_key` va en el nombre del **anuncio**, no del conjunto.

3. **Solo hay 5 conceptos y la doctrina pide 10.** Regla **R3F-13**: *"FASE 2 necesita 10 conceptos
   publicables o no arranca. No se monta con 8."* Con 5 no hay replicación "gana en 2 de 2", que es
   lo que corona un concepto. **Lo que hoy corre no puede coronar nada.**

4. **`PRODUCTOS/TINNIDROP/_PLAN_FASE2.json` está obsoleto y contradice lo publicado.** Declara 5
   conceptos (`CN02_TESTIMONIO_CHAT`, `CN08_TABLA_COMPARATIVA`, `CN11_BODEGA_OFERTA`,
   `CN10_SELLO_SEGURIDAD`) que **no son** los que se generaron, y sus `canonico_id` significan cosas
   distintas a las de `_DIM_CREATIVOS.csv` (ahí `CN10` es `PRUEBA_SOCIAL`, en el plan es
   `SELLO_SEGURIDAD`). **Hay dos catálogos de canónicos en circulación.** Reconciliarlos antes del
   próximo lanzamiento o el eje concepto queda ambiguo para siempre.

5. **La data de ventas está rezagada 2 días** — última ventana en `_FACT_VENTAS.csv`: **06-sep**.
   La campaña arrancó el 07-sep, así que **el control D+1 de tracking nunca se pudo correr**. Bajar
   el 07-sep con la skill `recopilar-lucidsales` antes de emitir cualquier veredicto sobre esta tanda.

---

## CLEARSTEM — sin tocar en esta sesión

Sigue como estaba: 3 piezas listas, 2 con defecto de ortografía (`Desinfilaman`, `RESISTENCUA` +
paleta rosa contra avatar masculino), y `CLEARSTEM_R1`–`R4` en `PENDIENTE_GENERAR` desde el 26-jul.
**Verificar contra Meta antes de publicar** — el mismo error de asumirlo desde el CSV aplica igual.
