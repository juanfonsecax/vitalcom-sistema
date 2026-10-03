# PARAMETRIZACIÓN DE ANUNCIOS — dueño único del modelo de ejes

> **Qué responde este archivo:** cuando un anuncio funciona, **qué de él funcionó** — y qué hay que
> mover para averiguarlo. Es el puente entre lo que se produce (`etapa-9`) y lo que se lee
> (`etapa-10`). **Ejes:** 5 testeables + covariables · **Grano:** el ANUNCIO.

---

## 1. POR QUÉ EXISTE

Sin ejes con vocabulario cerrado y registrados por anuncio, el sistema sabe *qué ángulo* vende y nada
más: cada creativo nuevo se diseña desde cero porque el aprendizaje no tiene dónde acumularse.

---

## 2. LOS EJES

### 2.1 EJES TESTEABLES — se mueve UNO a la vez

| # | Eje | Pregunta que contesta | Vocabulario | Dueño |
|---|---|---|---|---|
| 1 | `angulo_key` | **por qué duele** | abierto, nace por producto | `ETAPA-2.md` |
| 2 | `concepto_key` | **cómo se muestra** | cerrado: 8 (`C1`…`C9`) | `_CATALOGO_CONCEPTOS.md` |
| 2b | `canonico_id` | **qué estructura visual exacta** | cerrado: 22 (`CN01`…`CN22`) | `CANONICOS/_INDICE.md` |
| 3 | `nivel_conciencia` | **a quién le habla** | cerrado: `1` `2` `3A` `3B` | `ETAPA-2.md` |
| 4 | `oferta_key` | **qué se le pide comprar** | cerrado: `1U` `2X1` `4X2` `ESCALERA` `COMBO` `SIN_PRECIO` | `ETAPA-1.md` |
| 5 | `destino_key` | **a dónde cae el clic** | abierto: versión del flujo LucidBot | `ETAPA-11.md` |

Un anuncio es ángulo × concepto × *qué oferta muestra* × *a qué flujo manda*. Sin los ejes 4 y 5
registrados, un cambio de bot no declarado le carga la culpa al creativo — y el cierre, la brecha más
grande del negocio, está después del clic.

> **`canonico_id` es el zoom del eje 2, no un eje aparte.** `concepto_key` dice "prueba social";
> `canonico_id` dice si fue `CN10_PRUEBA_SOCIAL` (tarjetas con rating) o `CN08_UGC_CRUDO` (foto que no
> parece anuncio). Los 22 canónicos mapean a los 8 conceptos en `_DIM_VOCABULARIO.csv`; el gate
> verifica que no se contradigan.

### 2.2 COVARIABLES — se registran y se congelan, NUNCA se testean junto al eje

`formato` · `rol_embudo` · `tipo_hook` · `estilo_visual` · `avatar_edad` · `avatar_genero` ·
`lleva_precio` · `cuenta_alias` / `pagina_id`

Son las que **arruinan la lectura si se mueven a la vez**. Registrarlas es lo que permite que
`atribuir.py` diga *"este corte no es atribuible"* en vez de dar un número falso.

### 2.3 El nivel de conciencia está acoplado

El ángulo elige a quién le habla, y el `rol_embudo` se deriva del nivel (1→TOFU, 2→TOFU/MOFU,
3A/3B→BOFU). En la data propia cada nivel quedó en un solo rol de embudo, así que sus diferencias de
CPA no se pueden atribuir a ninguno de los dos. **Hasta que un testeo cruce deliberadamente esas
celdas, el nivel de conciencia es una covariable de diseño, no un eje que el sistema pueda leer.**
`3` a secas es ambiguo (no distingue 3A de 3B) y no es un valor válido.

---

## 3. EL GRANO: el ANUNCIO, no el conjunto

`_DIM_CONJUNTOS.csv` sigue siendo el dueño del **ángulo** — un conjunto es un ángulo. Pero el
concepto vive en la pieza. Por eso existe **`PRODUCTOS/_DIM_ANUNCIOS.csv`**: una fila por anuncio
real con gasto.

| Tabla | Grano | Responde |
|---|---|---|
| `_DIM_CONJUNTOS.csv` | conjunto = ángulo | qué ángulo |
| **`_DIM_ANUNCIOS.csv`** | anuncio pautado | **qué concepto, qué oferta, qué destino** |
| `_DIM_CREATIVOS.csv` | pieza producida | ciclo de vida: generado → publicado |
| `_DIM_VOCABULARIO.csv` | valor válido | qué se puede escribir en cada eje |

**La llave.** `(producto_key, anuncio_norm)`. `anuncio_norm` colapsa las réplicas `- Copia N`,
porque las réplicas **se suman, nunca se comparan** (invariante 12). El `ad_id` es llave secundaria
solo cuando está limpio: un `ad_id` que llegó como float científico (`e+`) perdió dígitos y no se
recupera, por eso el JOIN canónico es por nombre normalizado.

---

## 3.5. LA FIRMA Y EL BANNER

Los 5 ejes se comprimen en **una línea que viaja dentro del nombre del anuncio en Meta**:

```
NUSAVA|ARDOR|C1.CN03|NC2|2X1|BOTv1
producto|ángulo|concepto.canónico|conciencia|oferta|destino
```

**Por qué en el nombre.** El nombre llega intacto en **cualquier** export — Ads Manager, LucidSales,
MCP — y el `ad_id` no siempre. Con la firma en el nombre, la parametrización se reconstruye sola desde
cualquier fuente. Un `?` en cualquier posición = eje sin llenar, y el gate lo cuenta como deuda.

El **banner** es esa firma desplegada con su resultado (ejes, covariables congeladas, gasto, ventas,
CPA con su banda, break-even y cierre):

```bash
python Ads/_TOOLS/firma.py --ficha "NOMBRE_DEL_ANUNCIO"
```

---

## 3.6. LA ARITMÉTICA QUE LIMITA EL PLAN — leer antes de diseñar un testeo

Separar dos CPA que difieren un 20 % con bandas que no se toquen pide **~100 ventas por celda**. Un
test limpio de 4 brazos son ~400 ventas: semanas de todo el volumen del producto más grande. Cinco
ejes en fila serían meses, y para entonces el ángulo ganador ya fatigó. Consecuencias:

1. **No se testean los 5 ejes. Se testea el que tenga mayor tamaño de efecto esperado**, y los otros
   cuatro se registran para leerlos observacionalmente gratis.
2. **El aprendizaje se acumula ENTRE productos, no dentro de uno.** Un concepto que gana en 3 de 4
   productos es una regla utilizable; medido dentro de un solo producto casi nunca alcanza
   significancia. **La parametrización es un activo de PORTAFOLIO.**
3. **Los cortes observacionales sobre CBO tienen sesgo de asignación endógena:** Meta le da más
   presupuesto al que ya convierte. El corte sirve para **generar** hipótesis y el ABO con
   presupuesto igual (invariante 6) para **confirmarlas**. El **cierre** (ventas ÷ mensajes) es la
   métrica más robusta de las tres: es una tasa, no la mueve el presupuesto.

---

## 4. EL PROTOCOLO — cómo se contesta "¿fue el ángulo o el concepto?"

Se fija todo menos una cosa.

```
1. Hay un anuncio que vende barato.          → CPA bajo BE, con ≥1× PD de gasto.
2. Se pregunta CUÁL de sus ejes lo explica.
3. Se elige UN eje. Se CONGELAN los otros 4 + todas las covariables.
4. Se lanzan ≥3 brazos que solo difieren en ese eje, MISMO presupuesto (invariante 6).
5. Se registra el test en _TESTEOS.csv: variable, hipótesis, brazo_key por cada celda.
6. Cada anuncio del test lleva su test_id + brazo_key en _DIM_ANUNCIOS.csv.
7. Se lee con:  atribuir.py --eje <ese> --fijar <lo congelado>
8. Se declara SOLO si el reporte dice "DIFERENCIA REAL".
```

**Los tres frenos que el motor aplica solo:**

| Freno | Regla | De dónde sale |
|---|---|---|
| **No testeado** | celda con gasto < 1 × CPA break-even no se lee: no perdió, no se testeó | `DOCTRINA/ESCALADO/08_PLAN_ENTREGABLE.md` §7 |
| **Empate estadístico** | bandas de CPA (±1σ sobre n ventas) que se tocan → no se declara ganador, y dice cuántas ventas faltan | este archivo |
| **Confounding** | si cada nivel del eje tiene un único valor distinto en otro eje, avisa que **no es atribuible** | este archivo |

---

## 5. EL CICLO, END-TO-END

1. **Leer lo que ya hay:** `atribuir.py --eje angulo_key --producto P`. Si las bandas no se tocan y
   el ángulo ganador recibe menos dinero que otros, la primera decisión es reasignar presupuesto, sin
   producir nada.
2. **Preguntar qué concepto lo vende:** ángulo, formato, oferta y flujo congelados; 4 brazos que
   **solo** difieren en `canonico_id`. Se registra en `_TESTEOS.csv` (`variable = concepto_key`,
   `angulo_fijo`) y cada anuncio en `_DIM_ANUNCIOS.csv` con su `test_id` y `brazo_key`. Piso: 1 × CPA
   break-even por brazo antes de leer nada.
3. **Leer con el ángulo fijado:** `atribuir.py --eje concepto_key --fijar angulo_key=X` y
   `validar_parametros.py`. Tres desenlaces, los tres son información:
   - **"DIFERENCIA REAL"** → el concepto ganó. Entra a `_APRENDIZAJES.csv` con alcance GLOBAL si se
     repite en un segundo producto, y `etapa-9` produce sobre ese canónico.
   - **"EMPATE ESTADÍSTICO, necesita ~N ventas"** → no se declara nada. El concepto **no es la
     palanca** de este producto: se pasa al siguiente eje.
   - **"NO ATRIBUIBLE (confounding con X)"** → el testeo estaba mal armado. Se rehace congelando X.
4. **Cruzar contra el otro eje:** `atribuir.py --matriz angulo_key canonico_id --producto P`. Si el
   canónico ganador gana **también dentro de un segundo ángulo**, es un aprendizaje del CONCEPTO; si
   solo gana en el ángulo original, es una propiedad del ÁNGULO y no se generaliza. Las celdas vacías
   de esa matriz son la agenda de testeo del mes.

**Ninguna deuda de parametrización se resuelve produciendo más creativos:** mientras un eje esté sin
llenar, cada pieza nueva agranda el gasto sin agrandar el aprendizaje. La deuda vigente la cuenta
`validar_parametros.py`; no se lista acá.

---

## 6. COMANDOS

```bash
python Ads/_TOOLS/sembrar_anuncios.py            # diagnóstico; --escribir regenera _DIM_ANUNCIOS
python Ads/_TOOLS/gen_vocabulario.py             # regenera el vocabulario desde el catálogo
python Ads/_TOOLS/validar_parametros.py          # gate: exit 1 si hay valores fuera del vocabulario
python Ads/_TOOLS/atribuir.py --eje X [--fijar A=b] [--producto P]
python Ads/_TOOLS/atribuir.py --matriz X Y [--producto P]
python Ads/_TOOLS/firma.py --ficha "NOMBRE_DEL_ANUNCIO"
```
