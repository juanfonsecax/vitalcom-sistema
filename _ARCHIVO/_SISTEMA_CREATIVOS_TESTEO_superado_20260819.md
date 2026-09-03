# SISTEMA DE CREATIVOS DE TESTEO

> **Qué es:** el procedimiento repetible para producir los creativos de un test de concepto,
> igual para TODO producto. Creado 2026-08-19 con el test T01 (TINNIDROP).
>
> **Dueños que no se duplican acá:** el concepto vive en `_CATALOGO_CONCEPTOS.md`, el copy en
> `COPYWRITING_ADS.md`, el acabado visual en `PLANTILLAS_ADS.md`, la oferta en `ETAPA-1.md`.
> Este archivo solo dice **cómo se produce y cómo se nombra**.

---

## 1. La idea en una línea

```
PARTE PERMANENTE  (los 4 dispositivos)   ×   PARTE POR PRODUCTO  (el bloque fijo)
        ↑ no cambia nunca                          ↑ se saca de 2_DATA_PRODUCTO.txt
```

Los **4 dispositivos visuales** son un activo permanente: se escribieron una vez y sirven para
todos los productos que vengan. Lo único que se arma por producto es el **BLOQUE FIJO**.
Por eso el segundo producto cuesta 20 minutos y no una tarde.

---

## 2. Método de generación

Se le pasa a la IA de imagen **tres cosas**:

1. la **imagen de referencia** del brazo (de `_BANCO_CREATIVOS/`),
2. la **foto real del producto**,
3. el **prompt** = BLOQUE FIJO + el dispositivo del brazo.

La instrucción es *"leé esta referencia y creá desde cero una imagen con este mismo formato para
este producto"*. La IA **regenera**, no compone píxeles del original — no hay colisión de huella
perceptual. No hace falta paso intermedio.

> ⚠️ **Lo único que sí hay que vigilar es el TEXTO de la referencia, y es compliance, no huella.**
> Las referencias son ads reales con claims que nosotros no podemos usar. Nunca arrastrar:
> `"elimina"` · `"cura"` · sellos `REGISTRO-FDA US` · porcentajes clínicos · `"desde el primer día"`
> · antes/después corporal. El brazo A de T01 trae los dos primeros y hay que reemplazarlos.

---

## 3. Regla de oro del test: **un solo bloque, cuatro renders**

En un test de concepto **todo está fijo menos el dispositivo visual**: mismo ángulo, mismo hook,
mismos beneficios, mismo precio, misma garantía, misma página, mismo formato.

**El error que arruina el test en silencio** es dejar que se cuele una segunda variable — el caso
típico es el precio, porque la variante `ligera` "se ve mejor" sin él. Si un brazo va sin precio y
los otros con precio, el resultado no dice nada del concepto.

> Si la referencia del brazo no trae precio y el bloque fijo sí, **manda el bloque fijo.**

---

## 4. Los 4 dispositivos (parte permanente — no se toca por producto)

| Brazo | `concepto_key` · variante | Referencia | Dispositivo |
|---|---|---|---|
| **A** | `C2_BENEFICIOS` · colage-sintomas | Candida Cleanse | Rostro de profesional de bata a la derecha. Columna de 3 sellos de confianza a la izquierda. 3-4 recuadros circulares con la zona afectada + check verde. Fondo cálido plano. |
| **B** | `C2_BENEFICIOS` · ligera | Oftalmiel | El hook domina el tercio superior sin competencia. Columna de 4 íconos vectoriales, uno por beneficio. Producto grande a la derecha. Máximo aire, nada más. |
| **C** | `C2_BENEFICIOS` · densa | NeuraZenx | Fondo oscuro. Hook + subhook. Fila de 5 pictogramas de síntomas. Bloque "ACTÚA DESDE LA RAÍZ" con 3 mecanismos. Columna derecha de badges. Denso a propósito. |
| **D** | `C8_PROGRESION` | Astaxanthin | Tres paneles horizontales rotulados por **estado de uso**, producto centrado encima. |

> **Brazo D, cuidado permanente:** la referencia es un antes/después de resultado corporal. Eso
> viola compliance y además es imposible en problemas invisibles (tinnitus, insomnio, memoria).
> La progresión se rotula siempre por **momento de uso** — `PRIMERA SEMANA / USO CONTINUO / DÍA A
> DÍA` — nunca por resultado.

---

## 5. Nombres (choque con la convención — leer antes de crear la campaña)

`ETAPA-6.md` nombra `[CUENTA]_[PRODUCTO]_[ANGULO]_R[N]` porque asume que **el ángulo varía**.
En un test de concepto el ángulo es FIJO y varía el concepto. Nombrar los 4 brazos
`..._MEDIJERON_R1..R4` haría que la **regla 23 los sume como réplicas** y el test quedaría ilegible.

**El concepto entra en el nombre:**

```
conjunto:  [CUENTA]_[PRODUCTO]_[ANGULO]-[CONCEPTO]_R[N]
           GTR0_TINNIDROP_MEDIJERON-C2LIGERA_R1
anuncio:   [ANGULO]-[CONCEPTO]_IMG_[A|B]
           MEDIJERON-C2LIGERA_IMG_A
archivo:   [PRODUCTO]_[TEST]_[BRAZO]_[CONCEPTO].png
           TINNIDROP_T01_B_LIGERA.png
```

`R[N]` recupera su significado real: réplica **dentro de un brazo**, que se suma.
La lectura sale de la columna `concepto_key` de `_DIM_CONJUNTOS.csv`, no del nombre.

---

## 6. Los 7 pasos

1. **Congelar el BLOQUE FIJO** desde `PRODUCTOS/[X]/2_DATA_PRODUCTO.txt` — ángulo ya validado,
   hook, 4 beneficios, precio, garantía, página, avatar. Si el ángulo no está validado por venta
   real, el test no arranca: estarías moviendo dos variables.
2. **Armar los 4 prompts** = bloque fijo + dispositivo. Guardar en
   `Ads/MEDIA_[PRODUCTO]/PROMPTS_T[NN]_CONCEPTOS.txt`.
3. **Generar** las 4 imágenes, una por brazo, con la foto real del producto.
4. **Checklist de compliance** sobre cada una (§7). Rebota una, se regenera esa sola.
5. **Nombrar y guardar** en `Ads/MEDIA_[PRODUCTO]/` con el patrón de §5.
6. **Crear campaña**: 4 conjuntos × **2 anuncios cada uno** (default DUPLICADO = el mismo creativo
   dos veces). Presupuesto **idéntico** en los 4 — si no, el ganador lo decide el dinero.
7. **Registrar**: los nombres exactos en `conjuntos_meta` de `PRODUCTOS/_TESTEOS.csv` y la
   `concepto_key` en `_DIM_CONJUNTOS.csv`. Después `python Ads/_TOOLS/gen_hub.py --todo`.
   Sin el paso 7 el test corre pero nadie lo puede leer.

---

## 7. Checklist de compliance — pasa las 4 antes de subir

```
□ Cero "cura" / "elimina" / "repara" / "trata"      → "apoya" / "ayuda a reducir" / "alivia"
□ Cero sello FDA, REGISTRO-FDA US o similar          → reemplazar por el de garantía
□ Cero porcentajes clínicos y cero "desde el primer día"
□ Cero antes/después corporal
□ El precio aparece IGUAL en las 4 (o en ninguna)
□ El hook es idéntico en las 4
□ Los 4 beneficios son los mismos y en el mismo orden
□ 4:5 (1080×1350)
```

Las últimas cuatro no son de compliance: son **la validez del test**. Una sola que falle y el
resultado no es atribuible al concepto.

---

## 8. Cómo se lee (no re-litigar)

- Se agrega por **`concepto_key`**, nunca por conjunto. Ventas por conjunto son ruido de Poisson.
- Las réplicas `R[N]` se **suman**, no se comparan.
- **La conversación sirve para CORTAR, nunca para CORONAR.** Evidencia propia: tinnidrop-1 tuvo
  78 % de conversación y 0 ventas.
- Umbrales de evidencia: **10** ventas/brazo detecta un 3× · **25** un 2× · **80** un 1.5×.
  El medidor está en la pestaña TESTEOS de `_HUB.html`. No coronar antes de llegar.
- Corte por sangrado a los 10 días (0 ventas con gasto ≥ 2× CPA objetivo) — cortar sí, coronar no.
