# HANDOFF — CONVERSIÓN DE LAS 111 A FICHAS JSON

> **Para retomar en una sesión nueva.** Estado al 2026-08-22: **las 111 fichas están escritas.**
> La extracción cerró. Lo que sigue son los tres pasos de la sección 6.

---

## 1. QUÉ SE ESTÁ HACIENDO Y POR QUÉ

El operador tiene **111 imágenes favoritas** del mercado GT (`_CLASIF_FAVORITOS.csv`), ya validadas
con dinero real por otros anunciantes. Estaban clasificadas solo por `concepto_key` (C1–C9), sin
estructura extraída.

**El objetivo:** convertir cada una en un **JSON llenable con `{{VARIABLES}}`**, para después pedir
*"dame 10 conceptos para este producto"* y que el sistema devuelva los JSON ya llenos.

Decisiones ya tomadas por el operador (no volver a preguntar):

| Decisión | Elegido |
|---|---|
| Granularidad | **111 fichas** (una por imagen) **+ blueprints canónicos agrupados después** |
| Cobertura | **Las 111**, por tandas de 10, ordenadas por score |
| Vista | **HTML nuevo unificado** imagen ↔ JSON (después de las 111) |
| Motor de lotes | **Skill invocable `/generar-conceptos`** (último paso) |

---

## 2. REGLA MÁS IMPORTANTE — EL BANCO DOCUMENTA, NO AUDITA

**El operador corrigió esto explícitamente.** Estas piezas ya funcionan; la ficha registra **lo que
la pieza hace**, no lo que convendría que hiciera.

- **NO** escribir advertencias de riesgo, de baneo, de política de Meta ni de marca.
- **NO** proponer sustituciones, suavizados ni "versiones seguras".
- **NO** analizar con ojos de compliance. Ellos tienen los registros de las marcas que venden.
- El campo se llama **`sellos_y_claims_observados`** y es un **inventario factual**: qué sellos,
  badges, garantías y claims lleva la pieza, tal como los lleva.

Lo único que se traduce al replicar (por ser dato de producto, no decisión creativa):

| Sello del original | Al replicar |
|---|---|
| **FDA (EEUU)** | **se mantiene** — los productos son de origen americano |
| **INVIMA (Colombia)** | **MSPAS**, el registro local guatemalteco |
| cGMP, GMO free, lab tested, sellos de fábrica | **se mantienen** |

---

## 3. ARCHIVOS Y HERRAMIENTAS

```
Ads/_SWIPE/
├── _CLASIF_FAVORITOS.csv          ← las 111 originales (no se toca)
├── _IMG/                          ← las imágenes
└── _BLUEPRINTS/
    ├── _ESQUEMA_FICHA.md          ← el contrato del JSON. LEER PRIMERO
    ├── _HANDOFF_FICHAS.md         ← este archivo
    ├── blueprint_A..D.json        ← los 4 blueprints previos del operador (no se editan)
    ├── FICHAS/
    │   ├── _MANIFIESTO.csv        ← las 111 ordenadas por score, con su tanda
    │   └── F001.json … F111.json  ← las 111, completas
    └── _datos/
        ├── tanda01.py, tanda01_p2.py, tanda01_p3.py
        ├── … hasta tanda12.py  ← el análisis visual, en dicts de Python

Ads/_TOOLS/
├── gen_manifiesto_fichas.py       ← ya corrió; archivado en _ARCHIVO/retirado_20260922/
└── escribir_fichas.py             ← convierte los _datos/ en los JSON
```

**Comando para escribir una tanda:**
```bash
python Ads/_TOOLS/escribir_fichas.py 10
```
Lee **todos** los módulos `_datos/tanda10*.py` y los fusiona. El bloque `origen` se inyecta desde
`_MANIFIESTO.csv` — nunca se escribe a mano, así una ficha no puede contradecir al CSV.

---

## 4. PROCEDIMIENTO DE UNA TANDA (repetir para 10, 11, 12)

1. **Ver qué toca:**
   ```bash
   awk -F, 'NR==1 || $2==10 {print $1,$3,$4,$5,$6,$11}' Ads/_SWIPE/_BLUEPRINTS/FICHAS/_MANIFIESTO.csv
   ```
2. **Medir formatos reales** (la cosecha reescaló al alto 600 pero conservó el ratio):
   ```bash
   python -c "from PIL import Image; import csv,io; from fractions import Fraction; rows=list(csv.DictReader(io.open('Ads/_SWIPE/_BLUEPRINTS/FICHAS/_MANIFIESTO.csv',encoding='utf-8')));
   [print(r['ficha_id'], Fraction(*Image.open('Ads/_SWIPE/'+r['archivo']).size).limit_denominator(20)) for r in rows[90:100]]"
   ```
3. **Leer las 10 imágenes** con la herramienta Read (5 y 5, en paralelo).
4. **Escribir el análisis** en `_datos/tandaNN.py` (F0x1–F0x5) y `_datos/tandaNN_p2.py` (F0x6–F0y0).
   Usar la herramienta Write, **no heredoc de bash** (falla con archivos largos).
5. **Correr el escritor** y verificar el conteo.
6. **Reportar al operador** los dispositivos nuevos encontrados, sin juicio y sin advertencias.

---

## 5. CÓMO SE ESCRIBE UNA FICHA

Claves obligatorias (orden fijo, ver `_ESQUEMA_FICHA.md`):

`ficha_id` · `schema_version` · `origen` *(automático)* · `clasificacion` · `dispositivo_dominante` ·
`lectura_estrategica` · `fondo` · `paleta` · `sistema_tipografico` · *(`condiciones_de_captura` solo
si es UGC)* · `zonas` · `secuencia_lectura` · `reglas_duras` · `variables_requeridas` ·
`cuando_usar` · `cuando_no_usar` · `sellos_y_claims_observados` · `canonico_id` ·
`blueprint_equivalente`

**Lo que hace buena una ficha:**

- **`dispositivo_dominante`** en MAYÚSCULAS al inicio: la frase que explica por qué esta pieza es de
  este concepto. Es lo que se replica. Ej: *"EL NUMERAL DE CANTIDAD GIGANTE. Un dígito negro ocupa
  ~28% del alto y se lee antes que el producto…"*
- **`lectura_estrategica`**: qué vende y por qué funciona. 3-5 frases. Aquí va la inteligencia.
- **`zonas`**: cada una con `posicion`, `escala`/`contenedor`, `estilo`, `restriccion_palabras` y su
  `{{PLACEHOLDER}}`. Las reglas finas van en claves `regla`, `regla_critica`, `funcion`.
- **`reglas_duras`**: siempre en **positivo** (los modelos de imagen leen mal las negaciones).
- **Nunca el texto literal del anunciante** en las zonas — eso va como `{{VARIABLE}}`. El texto real
  se registra en `sellos_y_claims_observados`.
- Los archivos `_datos/*.py` van **sin tildes** (ASCII) para evitar problemas de encoding; los JSON
  salen en UTF-8.

**Escala de `nivel_conciencia`** (Schwartz): 1 = no sabe que el problema tiene nombre · 2 = conoce el
síntoma, no la solución · 3 = compara soluciones · 4 = busca el producto por nombre · 5 = ya lo vio
y no compró (retargeting).

---

## 6. LO QUE FALTA DESPUÉS DE LAS 111

| Paso | Estado |
|---|---|
| Fichas F001–F111 (las 111) | ✅ |
| **Agrupar en blueprints canónicos** (`CANONICOS/`, llenar `canonico_id`) | ✅ **22-ago — 22 canónicos, cobertura exacta** |
| **Skill `/generar-conceptos`** — selecciona N blueprints, los llena y escribe los prompts | ✅ **`.claude/skills/generar-conceptos/`** |
| **`_BANCO.html`** — grilla de las 111 con imagen + JSON al lado y botón de copiar | **← retomar acá** |

### Lo que quedó del paso de agrupación (23-ago)

**22 canónicos**, cada ficha en uno y solo uno. El mapa vive en `FAMILIAS` dentro de
`Ads/_TOOLS/agrupar_canonicos.py` y **todo lo demás se deriva de las fichas**, así que un
canónico no puede contradecir a sus miembros. Para cambiar una agrupación se edita el mapa y
se vuelve a correr:

```bash
python Ads/_TOOLS/agrupar_canonicos.py --dry-run   # valida cobertura
python Ads/_TOOLS/agrupar_canonicos.py             # escribe CANONICOS/ + canonico_id
```

Tres cosas que salieron de hacerlo y conviene no re-descubrir:

- **`escribir_fichas.py` borraba el `canonico_id`.** Hacía `setdefault(..., None)` y los
  `_datos/tanda*.py` no traen ese campo, así que reescribir cualquier tanda lo perdía. Ahora
  importa `FAMILIAS` y lo asigna desde ahí: la pertenencia tiene un solo dueño.
- **El contrato de variables NO se puede derivar contando.** Cada tanda nombró lo mismo distinto
  (`RETRATO_ANTES` / `FOTO_ANTES` / `IMAGEN_ANTES`), así que en CN01 (14 miembros) ninguna
  variable llega al 60% y el núcleo sale vacío. El contrato está escrito a mano por familia en
  `CONTRATOS`; el conteo se publica aparte como `variables_observadas` (evidencia, no contrato).
- **El selector NO lleva capa de compliance, y es deliberado.** En la primera versión le metí una
  (`CN01_ANTES_DESPUES` desviado a "dividido problema/beneficio" por la regla vieja de
  `PLANTILLAS_ADS.md`). **El operador lo revirtió el 23-ago:** esa regla es anterior al banco, y
  el banco es la evidencia nueva — 111 piezas que ya venden con dinero real en GT. Contradecía
  además la §2 de este mismo archivo. **CN01 se replica como el banco lo documenta**, dos estados
  del mismo sujeto y el producto de bisagra. Lo único que se traduce es INVIMA → MSPAS.

---

## 7. HALLAZGOS ACUMULADOS (para no re-descubrirlos)

- **Los 4 blueprints A/B/C/D del operador están dentro de las 111.** A = F003 (Candida Cleanse),
  B = F002/F007 (Oftalmiel), C = F008/F009 (NeuraZenx), D = F029/F039/F040/F041/F042/F053/F064/F086
  (Astaxanthin). Ninguno era una referencia externa. Declarado en `blueprint_equivalente`.
- **`C2_BENEFICIOS` agrupa cosas estructuralmente incomparables** (41 de 111). Como llave de medición
  sirve; como llave de producción no. Los canónicos la van a partir.
- **Series de plantilla ya detectadas** (misma estructura, una variable cambia):
  · F061-62-63 → cambia la **zona del cuerpo** (misma lámina, mismo titular)
  · F065-66 → cambia la **cantidad** de la oferta
  · F051-52 → cambia el **registro** (claro/argumentativo vs rojo/cierre)
  · F039-40 → cambia el **tipo de label** del timeline (momento de uso vs plazo)
  · F087-88-89 → cambia el **tratamiento del avatar** (a los lados / superpuesto / sin avatar)
  · F083-84-85 → cambia la **profundidad** (escalera / página de producto / familias de ingrediente)
  · F094-95 → cambia el **fenotipo de la modelo** y se retira el panel de prueba (plantilla congelada:
    mismo titular, mismos beneficios, misma card, mismo número de prueba social)
  · F097↔F099 → misma marca y mismo producto, cambia el **registro del antes/después**: crudo sin
    marco + etiqueta que nombra la suciedad + oferta gritada en badge de esquina ↔ enmarcado +
    etiqueta neutra de condición + oferta degradada a módulo de la barra de pie
  · F091-92 → dos piezas **sin una sola palabra** del mismo anunciante: una presta un **rostro**
    (selfie del avatar en su casa), la otra presta un **escenario** (bodegón de lo que ya falló)
  · **F094-95-105-106** (Woman Curves, Aurora GT) → una sola plantilla en cuatro variantes. El eje
    1:1 → 4:5 mueve la **oferta** de card lateral a **banda central bajo el titular** y los sellos
    de columna a fila; dentro de cada formato cambia el **fenotipo** (94↔95) o la **intensidad del
    verbo**, moldea vs realza (105↔106). El `+4,253` es constante en las cuatro.
  · **F107-109-111** (Natures Sunshine, Topishop) → una vitrina de cards doradas en tres variantes.
    Constante: el **bloque de rating decimal**. Cambia la **densidad de argumento** (8 cards con
    subtítulo → 4 sin), el **lado** de la modelo, y en F111 el rating se **apila bajo el rostro**,
    con lo que la nota se lee como la de ella.
  · F097↔F103 → el mismo principio de "un solo cuerpo partido" en dos materiales: **render
    anatómico** (órgano abierto, el frasco en el eje) y **fotografía real** (una sola toma de un
    cuerpo, la línea nace del gotero).
- **`condiciones_de_captura`** se agregó en la tanda 2 para las UGC: ahí lo que se replica no es el
  layout sino **cómo se toma la foto**. El escritor **falla** si una ficha `organico_ugc` no la trae.
- **Distribución final de las 111:** C2=41 · C4=17 · C5=15 · C8=12 · C7=9 · C3=7 · C1=5 · C9=5 ·
  91 cartel / 20 UGC · TOFU 28 / MOFU 61 / BOFU 22.
- **Calibre de redacción** (medido sobre las 111, para que una tanda nueva no se desvíe):
  `dispositivo_dominante` 42–76 palabras (mediana 61) · `lectura_estrategica` 54–108 palabras
  (mediana 90, 3-5 frases). Un chat nuevo tiende a escribir de más: conviene medirlo y comprimir.

---

## 8. QUÉ QUEDA EN LAS TANDAS 10–12

Las doce tandas están escritas. Las tres últimas cerraron los dos conceptos que venían flacos:
**C7_DESEO** pasó de 4 a 9 (Aurora GT, familia Woman Curves) y **C9_COMPARACION** de 3 a 5
(F102 *yo sin / yo con* de Teyra, F110 *vs remedio casero* de Topishop).

Las dos piezas de `C9` son el hallazgo estructural del tramo final, porque el rival que eligen
no es una marca competidora:
- **F102** compara a la persona **contra sí misma** (dos columnas de "Yo", dibujadas a mano).
- **F110** compara contra **lo que ya se hace gratis en la cocina** (vinagre, ajo, limón), y le
  cobra la **fricción** — preparación, olor, practicidad — sin discutir nunca si el remedio sirve.
