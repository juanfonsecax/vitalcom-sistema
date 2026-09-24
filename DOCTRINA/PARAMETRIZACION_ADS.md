# PARAMETRIZACIÓN DE ANUNCIOS — dueño único del modelo de ejes

> **Qué responde este archivo:** cuando un anuncio funciona, **qué de él funcionó** — y qué hay que
> mover para averiguarlo. Es el puente entre lo que se produce (`etapa-9`) y lo que se lee
> (`etapa-10`).
>
> **Fecha:** 2026-09-06 · **Ejes:** 5 testeables + 8 covariables · **Grano:** el ANUNCIO.

---

## 1. EL DIAGNÓSTICO QUE OBLIGÓ A ESCRIBIRLO

Medido sobre las 2 475 filas de `_FACT_VENTAS.csv` ($5 604 de gasto real):

| Hecho | Consecuencia |
|---|---|
| `_DIM_CONJUNTOS.csv` tiene **157 filas**, todas con `concepto_key = SIN_CLASIFICAR` | El eje CONCEPTO **nunca se pudo leer**. 100 % del gasto ciego. |
| **91 % del gasto** cae en conjuntos con **más de un anuncio distinto** | La parametrización a nivel de CONJUNTO no puede atribuir nada al creativo. |
| `_DIM_CREATIVOS.csv` tiene **12 filas** contra **54 anuncios** con gasto | La tabla de producción no cruza con la de resultados. Cobertura del JOIN: **0 %**. |
| **2 006 de 2 475** `ad_id` guardados como float científico (`1.2024e+17`) | Los últimos dígitos se perdieron. El JOIN por ID de Meta es **irrecuperable** en esas filas. |
| `nivel_conciencia` con 7 valores distintos (`2`,`3`,`1`,`3a`,`NC2`,`1-2`,vacío) | Ni siquiera el eje que sí estaba poblado era agrupable. |

**Traducción:** el sistema sabía *qué ángulo* vende y no sabía *nada más*. Cada creativo nuevo se
diseñaba desde cero porque el aprendizaje no tenía dónde acumularse.

---

## 2. LOS EJES — no son tres

La pregunta "¿ángulo, concepto y nivel de conciencia, o hay más?" tiene una respuesta con dos
mitades. **Ejes testeables son cinco.** Y hay una segunda categoría que no se testea pero **sí se
registra**, porque sin ella cualquier lectura del primer grupo es mentira.

### 2.1 EJES TESTEABLES — se mueve UNO a la vez

| # | Eje | Pregunta que contesta | Vocabulario | Dueño |
|---|---|---|---|---|
| 1 | `angulo_key` | **por qué duele** | abierto, nace por producto | `ETAPA-2.md` |
| 2 | `concepto_key` | **cómo se muestra** | cerrado: 8 (`C1`…`C9`) | `_CATALOGO_CONCEPTOS.md` |
| 2b | `canonico_id` | **qué estructura visual exacta** | cerrado: 22 (`CN01`…`CN22`) | `CANONICOS/_INDICE.md` |
| 3 | `nivel_conciencia` | **a quién le habla** | cerrado: `1` `2` `3A` `3B` | `ETAPA-2.md` |
| 4 | `oferta_key` | **qué se le pide comprar** | cerrado: `1U` `2X1` `4X2` `ESCALERA` `COMBO` `SIN_PRECIO` | `ETAPA-1.md` |
| 5 | `destino_key` | **a dónde cae el clic** | abierto: versión del flujo LucidBot | `ETAPA-11.md` |

**Por qué 4 y 5 entran y por qué importan más de lo que parece.** El CIERRE del negocio es 8.6 %
contra el 15-20 % de los mentores: **la brecha más grande del sistema no está en el creativo, está
después del clic**. Un ad no se compone solo de ángulo × concepto — se compone de ángulo × concepto
× *qué oferta muestra* × *a qué flujo manda*. Sin los ejes 4 y 5 registrados, un cambio de bot no
declarado le carga la culpa al creativo.

> **`canonico_id` no es un cuarto eje, es el zoom del segundo.** `concepto_key` dice "prueba
> social"; `canonico_id` dice si fue `CN10_PRUEBA_SOCIAL` (tarjetas con rating) o `CN08_UGC_CRUDO`
> (foto que no parece anuncio). Los 22 canónicos mapean a los 8 conceptos en
> `_DIM_VOCABULARIO.csv`; el gate verifica que no se contradigan.

### 2.2 COVARIABLES — se registran y se congelan, NUNCA se testean junto al eje

`formato` · `rol_embudo` · `tipo_hook` · `estilo_visual` · `avatar_edad` · `avatar_genero` ·
`lleva_precio` · `cuenta_alias` / `pagina_id`

No son menos importantes: son las que **arruinan la lectura si se mueven a la vez**. Registrarlas es
lo que permite que `atribuir.py` diga *"este corte no es atribuible"* en vez de dar un número falso.

### 2.3 La advertencia sobre el nivel de conciencia

**El nivel de conciencia no es una variable libre: está acoplada.** El ángulo elige a quién le
habla, y el `rol_embudo` se deriva del nivel (1→TOFU, 2→TOFU/MOFU, 3A/3B→BOFU). Corrido hoy sobre
CLEARSTEM, la matriz lo muestra desnudo:

```
MATRIZ nivel_conciencia x rol_embudo — CLEARSTEM
                    MOFU        TOFU
1                   .           Q40/78v
2                   .           Q64/51v
3                   Q50/66v     .
```

El nivel 3 **solo existe** en MOFU y los niveles 1-2 **solo** en TOFU. La diferencia de Q40 vs Q50
no se puede atribuir a ninguno de los dos: están perfectamente confundidos. **Hasta que exista un
testeo que cruce deliberadamente esas celdas, el nivel de conciencia es una covariable de diseño,
no un eje que el sistema pueda leer.**

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

**La llave.** `(producto_key, anuncio_norm)`. `anuncio_norm` colapsa las réplicas `- Copia N`, porque
la regla 12 de `CLAUDE.md` dice que las réplicas **se suman, nunca se comparan**. `ad_id` va como
llave secundaria cuando está limpio — hoy solo en 10 de 54 filas, por la corrupción del float.

> **Nota sobre `ad_id`.** `enriquecer_adid.py` ya documentó el bug y arregló lo recuperable. Lo que
> llegó como float desde el xlsx **perdió dígitos y no vuelve**. Por eso el JOIN canónico es por
> nombre normalizado, y el `ad_id` solo se usa cuando no trae `e+`.

---

## 3.5. LA FIRMA Y EL BANNER

Los 5 ejes se comprimen en **una línea que viaja dentro del nombre del anuncio en Meta**:

```
NUSAVA|ARDOR|C1.CN03|NC2|2X1|BOTv1
producto|ángulo|concepto.canónico|conciencia|oferta|destino
```

**Por qué en el nombre.** El `ad_id` llegó corrupto en 2 006 de 2 475 filas y no se recupera. El
nombre viene intacto en **cualquier** export — Ads Manager, LucidSales, MCP. Con la firma en el
nombre, la parametrización se reconstruye sola desde cualquier fuente y deja de depender de que
alguien mantenga una tabla paralela. Un `?` en cualquier posición = eje sin llenar, y el gate lo
cuenta como deuda.

El **banner** es esa firma desplegada con su resultado. Una pieza, una pantalla:

```bash
python Ads/_TOOLS/firma.py --ficha "MA6_OFERTA"
```
```
+------------------------------------------------------------------------------+
| MA6_OFERTA                                                                   |
| NUSAVA|ARDOR|C1.CN03|NC2|2X1|?                                               |
+------------------------------------------------------------------------------+
| 1 ANGULO      por que duele        ARDOR                                     |
| 2 CONCEPTO    como se muestra      C1_OFERTA                                 |
|   canonico    que estructura       CN03_OFERTA_MULTIPLICADOR                 |
| 3 CONCIENCIA  a quien le habla     2                                         |
| 4 OFERTA      que le pide comprar  2X1                                       |
| 5 DESTINO     a donde cae el clic  SIN LLENAR                                |
+------------------------------------------------------------------------------+
| covariables congeladas: IMAGEN · BOFU · hook EMOCIONAL · con precio · GTR7   |
+------------------------------------------------------------------------------+
| Q3052 gastados · 80 ventas · 544 mensajes                                    |
| CPA Q38.15  (banda Q34-Q43)   break-even Q92.64                              |
| cierre 14.7% (ventas / mensajes)                                             |
| > GANADOR FUERTE — CPA a 41% del break-even                                  |
+------------------------------------------------------------------------------+
```

> El banner ya pagó su costo el primer día: mostró que `MA6_OFERTA` figuraba como **VIDEO**
> siendo un `.jpg`. El `formato` se heredaba del conjunto, y a nivel de anuncio estaba mal. Con
> el formato corregido, NUSAVA da vuelta su lectura: **IMAGEN Q53 / cierre 9.2 % vs VIDEO Q74 /
> cierre 3.0 %**. Antes ese corte estaba contaminado.

---

## 3.6. LA ARITMÉTICA QUE LIMITA EL PLAN — leer antes de diseñar un testeo

El protocolo de la sección 4 es correcto. **El volumen del negocio no alcanza para aplicarlo a los
cinco ejes de forma secuencial**, y conviene saberlo antes de gastar:

| Producto | ventas acumuladas | ventas/semana aprox. |
|---|---|---|
| TINNIDROP | 470 | ~55 |
| CLEARSTEM | 195 | ~23 |
| NUSAVA | 131 | ~15 |
| VARICOSE | 47 | ~6 |

Separar dos CPA que difieren un 20 % con bandas que no se toquen pide **~100 ventas por celda**.
Un test limpio de 4 brazos = ~400 ventas = **7 semanas de TODO el volumen de TINNIDROP**, el
producto grande. Cinco ejes en fila serían **más de ocho meses**, y para entonces el ángulo
ganador ya fatigó. Consecuencias operativas:

1. **No se testean los 5 ejes. Se testea el que tenga mayor tamaño de efecto esperado**, y los
   otros cuatro se registran para leerlos observacionalmente gratis.
2. **El aprendizaje se acumula ENTRE productos, no dentro de uno.** Los cuatro productos juntos
   suman 843 ventas. Un concepto que gana en 3 de 4 productos es una regla utilizable; el mismo
   concepto medido dentro de un solo producto casi nunca alcanza significancia. **La
   parametrización es un activo de PORTAFOLIO.**
3. **Los cortes observacionales sobre CBO tienen sesgo de asignación endógena.** Meta le da más
   presupuesto al que ya está convirtiendo, así que el ganador "gana" el corte en parte porque
   ganó antes. Por eso el corte sirve para **generar** hipótesis y el ABO con presupuesto igual
   (invariante 6) para **confirmarlas** — y por eso el **cierre** (ventas ÷ mensajes) es la métrica
   más robusta de las tres: es una tasa, no la mueve el presupuesto.

---

## 4. EL PROTOCOLO — cómo se contesta "¿fue el ángulo o el concepto?"

Es exactamente el diseño que el operador describe: se fija todo menos una cosa.

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

## 5. EL EJEMPLO IDEAL, END-TO-END

Con TINNIDROP, tomando los números reales de hoy.

**Día 0 — se lee lo que ya hay.**

```bash
python Ads/_TOOLS/atribuir.py --eje angulo_key --producto TINNIDROP
```
```
ACCESIBILIDAD_MEDICO    Q2 998   84v   CPA Q35.69   banda 32-40   GANA
DETERIORO_COGNITIVO     Q8 330  171v   CPA Q48.71   banda 45-53   GANA
PERDIDA_AUDITIVA        Q7 751  135v   CPA Q57.41   banda 53-63   GANA
→ DIFERENCIA REAL: las bandas no se tocan.
```
El ángulo ganador es `ACCESIBILIDAD_MEDICO` y **el sistema le está dando la tercera parte del
dinero que le da al segundo**. Primera decisión, sin producir nada: reasignar presupuesto.

**Día 1 — se pregunta qué concepto lo vende.** Ángulo congelado, formato congelado, oferta
congelada, mismo flujo. Se lanzan 4 brazos que **solo** difieren en `canonico_id`:

| brazo | canonico_id | concepto_key | lo demás |
|---|---|---|---|
| A | `CN07_DOLOR_A_PLENO` | `C3_SINTOMA` | idéntico |
| B | `CN10_PRUEBA_SOCIAL` | `C5_PRUEBA` | idéntico |
| C | `CN14_COMPARACION_DOS_COLUMNAS` | `C9_COMPARACION` | idéntico |
| D | `CN01_ANTES_DESPUES` | `C4_TRANSFORMACION` | idéntico |

Se escribe la fila en `_TESTEOS.csv` (`variable = concepto_key`, `angulo_fijo =
ACCESIBILIDAD_MEDICO`) y las 4 filas en `_DIM_ANUNCIOS.csv` con su `test_id` y `brazo_key`.
Presupuesto: **1 × CPA break-even por brazo como piso** = Q93.41 × 4 ≈ Q374 antes de leer nada.

**Día 4 — se lee, con el ángulo fijado.**

```bash
python Ads/_TOOLS/atribuir.py --eje concepto_key --fijar angulo_key=ACCESIBILIDAD_MEDICO
python Ads/_TOOLS/validar_parametros.py     # gate: nada fuera del vocabulario
```

Tres desenlaces, y los tres son información:

- **"DIFERENCIA REAL"** → el concepto ganó. Entra a `_APRENDIZAJES.csv` con alcance GLOBAL si se
  repite en un segundo producto, y `etapa-9` produce sobre ese canónico.
- **"EMPATE ESTADÍSTICO, necesita ~N ventas"** → no se declara nada. El concepto **no es la
  palanca** de este producto: se deja de gastar ahí y se pasa al siguiente eje.
- **"NO ATRIBUIBLE (confounding con X)"** → el testeo estaba mal armado. Se rehace congelando X.

**Día 5 — el cruce que cierra el ciclo.** El ganador se valida contra el otro eje:

```bash
python Ads/_TOOLS/atribuir.py --matriz angulo_key canonico_id --producto TINNIDROP
```

Si el canónico ganador gana **también dentro de un segundo ángulo**, es un aprendizaje del
CONCEPTO. Si solo gana dentro del ángulo original, es una propiedad del ÁNGULO y no se generaliza.
Ésa es la diferencia entre un dato y una regla — y las celdas vacías de esa matriz son la agenda de
testeo del mes.

---

## 6. COMANDOS

```bash
python Ads/_TOOLS/sembrar_anuncios.py            # diagnóstico; --escribir regenera _DIM_ANUNCIOS
python Ads/_TOOLS/gen_vocabulario.py             # regenera el vocabulario desde el catálogo
python Ads/_TOOLS/validar_parametros.py          # gate: exit 1 si hay valores fuera del vocabulario
python Ads/_TOOLS/atribuir.py --eje X [--fijar A=b] [--producto P]
python Ads/_TOOLS/atribuir.py --matriz X Y [--producto P]
```

---

## 7. DEUDA ABIERTA (al 2026-09-06)

| Deuda | Tamaño | Qué la cierra |
|---|---|---|
| `concepto_key` + `canonico_id` sin llenar | **54 anuncios, 100 % del gasto** | clasificar cada pieza de `Ads/MEDIA_*` contra los 22 canónicos |
| `oferta_key` y `destino_key` sin llenar | 100 % | leer `2_DATA_PRODUCTO.txt` + `_EVENTOS.csv` (`CAMBIO_BOT`) |
| `nivel_conciencia = 3` ambiguo | 25 conjuntos | desambiguar 3A (teme comprar) vs 3B (compara) — llevan a ads opuestos |
| alias sucios `3a` / `NC2` / `1-2` | 5 anuncios | normalizar en `_DIM_CONJUNTOS.csv` y re-sembrar |
| `ad_id` en float científico | 2 006 filas | irrecuperable en histórico; blindar la ingesta hacia adelante |

**Ninguna de estas deudas se resuelve produciendo más creativos.** Mientras el eje concepto esté
ciego, cada pieza nueva agranda el gasto sin agrandar el aprendizaje.
