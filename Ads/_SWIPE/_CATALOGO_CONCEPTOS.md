# CATÁLOGO DE CONCEPTOS CREATIVOS — v2

> **Qué es:** el método de extracción de elementos (`_HANDOFF_CONCEPTOS.md` §2) aplicado a
> **dos muestras independientes**: 36 creativos elegidos **por data** (17 anunciantes) + los
> **111 favoritos elegidos a ojo por el operador** (39 anunciantes). Total **133 creativos únicos**.
> **Fecha:** 2026-08-18 · **Base:** `_ELEMENTOS.csv` (matriz 36 × 30) + `_CLASIF_FAVORITOS.csv` (111)
>
> **ÁNGULO = por qué duele. CONCEPTO = cómo se muestra.** Este archivo es el dueño único del CONCEPTO.

---

## ⚡ v2 — QUÉ CAMBIÓ Y POR QUÉ (leer antes que nada)

La v1 salió de una muestra sesgada a **supervivencia** (`días ≥ 21` o `réplicas ≥ 2`). La selección
manual del operador tiene otro sesgo — **variedad conceptual** — y cubre más del doble de anunciantes.
Cruzarlas es la validación que faltaba:

| | Selección por data (36) | Selección a ojo (111) |
|---|---|---|
| días medianos | 57 | **8** |
| ≥ 21 días | 66 % | 24 % |
| anunciantes | 17 | **39** |
| **coinciden** | \multicolumn{2}{c}{**14 creativos**} |

**Resultado del cruce: 76 % de los 111 favoritos caen dentro de los 6 conceptos de la v1.**
Esa es la confirmación de que el catálogo estaba bien dimensionado. El **23 % restante son
conceptos que la muestra por supervivencia no podía ver** — y son el aporte real de esta pasada.

**Tres conceptos nuevos entran al catálogo** (C7, C8, C9) y **dos se fusionan** (C6 UNBOXING y
TESTIMONIO pasan a ser variantes de C5, ahora renombrado **C5 PRUEBA**). El catálogo queda en **8**.

> **Por qué la divergencia no es un error de nadie.** La supervivencia mide *qué ya ganó*; la
> variedad visual mide *qué existe*. Un concepto que el mercado empezó a usar hace 5 días no puede
> tener 21 días de vida — pero sí puede tener réplicas, que es plata ya apostada. Los dos sesgos
> juntos ven lo que ninguno ve solo.

---

## 0. CÓMO SE ELIGIERON LOS 36

Pool de partida: 597 creativos cosechados → filtros en cascada:

| Filtro | Quedan | Por qué |
|---|---|---|
| todos | 597 | |
| − catálogo dinámico (`{{product.name}}` sin resolver) | 538 | no son creativos, son plantillas de feed |
| − páginas BAZAR (Trendora, RyR, Tu oferta Online, Megacomprasgt, Nova Market, Mundohome, Luceselect) | — | otra vertical (herramientas/hogar); contaminan el catálogo de salud |
| **ganador real**: `días ≥ 21` **o** `réplicas ≥ 2` | **155** | sobrevivir 21 días o pagar duplicación = el mercado ya validó |
| top por `score = días + réplicas×25`, **máx 3 por anunciante** | **36** | el tope por anunciante evita retratar el estilo de una sola agencia |

> El tope de 3 es la decisión metodológica que importa: sin él, Dr. Felipe Flores y Aranza Glow
> se llevaban buena parte de los 36 slots y el catálogo describiría a dos agencias, no al mercado.

---

## 1. EL ESQUELETO INVARIANTE (lo que NO diferencia)

Presente en la gran mayoría — **no sirve para distinguir conceptos, sirve como checklist de piso**:

| Elemento | Frecuencia |
|---|---|
| producto visible | **94 %** (34/36) |
| franja/badges de confianza (envío gratis · pago contra entrega · origen) | **72 %** (26/36) |
| menciona el problema en la imagen | **72 %** (26/36) |
| precio prominente | **66 %** (24/36) |
| íconos de beneficio | **52 %** (19/36) |

**Correcciones a la prueba piloto de 6** (hecha con 2 anunciantes; sobredimensionó lo que vio):

- El piloto dio **precio en 6/6**. Con 36 y 17 anunciantes es **66 %**, no 100 %. Alto, pero no universal: **12 ganadores corren sin precio**, incluido el de 197 días.
- El piloto dio **props naturales en 6/6**. Real: **19 %**. Era un rasgo de Camila + Ketsal, no del mercado.
- **Rostro humano 27 %** (el piloto dio 1/6 ≈ 17 %) — sigue siendo minoría clara. Se confirma.

---

## 2. LO QUE SÍ DIFERENCIA — EL DISPOSITIVO DOMINANTE

El piloto propuso dos ejes (apertura × estética). Con 36 creativos ese modelo **no separa**:
`PROMESA_BENEFICIO × ESTUDIO_PULIDO` se come 10 de los 36, y adentro hay cosas incomparables
(una ficha de ingredientes, un antes/después y un combo de 2 SKU).

El eje que sí parte limpio es **qué dispositivo ocupa el peso visual** — qué está mirando el ojo:

| CONCEPTO | n | anunciantes | días medianos | máx días | máx réplicas | menciona problema | lleva precio |
|---|---|---|---|---|---|---|---|
| **C1 OFERTA** | 10 | **7** | 66 | **266** | **x16** | 4/10 | 9/10 |
| **C2 BENEFICIOS** | 7 | **6** | 8 | 197 | x10 | **6/7** | 4/7 |
| **C3 SÍNTOMA** | 4 | 2 | **124** | 124 | x1 | **4/4** | 2/4 |
| **C4 TRANSFORMACIÓN** | 3 | 2 | **102** | 113 | x1 | 3/3 | 2/3 |
| **C5 EVIDENCIA CRUDA** | 3 | 1 | 6 | 6 | x3 | 3/3 | **0/3** |
| **C6 UNBOXING** | 2 | 1 | 7 | 7 | x4 | 2/2 | 2/2 |
| *(ficha de fórmula)* | 2 | 2 | 119 | 119 | x1 | 1/2 | 2/2 |
| *(producto hero)* | 2 | 2 | 151 | 151 | x5 | 0/2 | 0/2 |
| *(escena de vida)* | 2 | 1 | 56 | 56 | x1 | 2/2 | 2/2 |
| *(autoridad clínica)* | 1 | 1 | 24 | 24 | **x9** | 1/1 | 1/1 |

Los cuatro de abajo (en cursiva) **no entran al catálogo como conceptos propios**: n muy bajo y
todos son combinables como relleno de C1/C2. Se documentan en §5 para no perderlos.

**Seis conceptos es el techo correcto**, no una elección estética: con 12-24 conjuntos/mes,
6 valores dan 2-4 observaciones cada uno por mes. Con 10 valores nunca se acumula
(es la **regla 6 del orquestador**, ya medida: dispersión 1.12 por conjunto vs 2.99 por ángulo).

---

## 3. LAS SEIS FICHAS

### C1 — OFERTA
> El precio o la cantidad ES el creativo.

- **Firma:** numeral gigante (`2 FRASCOS`, `LLEVA 3 POR Q300`, `4 frascos al precio de 3`) o precio dominante + múltiples unidades + franja de confianza.
- **Elementos típicos:** `precio_prominente` · `combo_cantidad` · `multiples_unidades` · `badge_importado` · `sello_mas_vendido` · `cta_textual`
- **Rol de embudo:** **BOFU**. Solo 4 de 10 mencionan el problema — le habla a quien ya lo conoce.
- **Evidencia:** el concepto **más transversal (7 anunciantes)**, el **más longevo (Beevana, 266 días)** y el **más replicado (Camila Oftalmiel, x16)**. El único validado por las tres métricas a la vez.
- **Ejemplos:** #1 Camila Oftalmiel · #2 Compra GT Beevana · #7 Zooone · #12 Magnesium · #19 MegaRed 3x1 · #27 NeoCell
- ⚠️ **No usar en FASE 1.** Un creativo que ni nombra el problema entierra la señal del ángulo, que es justo lo que FASE 1 mide.

### C2 — BENEFICIOS
> Pregunta de dolor arriba + columna de íconos con el beneficio explicado.

- **Firma:** apertura en pregunta (`¿Cansada de sentirte pesada?`, `¿Sientes que te falta energía?`) + 3-5 íconos con título y bajada + producto al centro.
- **Elementos típicos:** `iconos_beneficio` · `menciona_problema` · `franja_confianza` · precio opcional
- **Rol de embudo:** **TOFU/MOFU**.
- **Evidencia:** 6 anunciantes distintos, y **6 de 7 nombran el problema** — la proporción más alta del catálogo. El ganador de 197 días (Valle, Ginkgo+Ginseng) **no lleva precio**.
- **Ejemplos:** #3 Camila Oftalmiel x10 · #5 Valle Ginkgo 197d · #6 MegaRed · #21 Ketsal Drenaje x4 · #25 Private Cream
- ✅ **Este es el `concepto_control` de FASE 1** — ver §4.

### C3 — SÍNTOMA
> La zona del cuerpo que duele, señalada.

- **Firma:** foto de la parte afectada (rodilla, pierna con várices, riñones, espalda) con halo rojo o resplandor + producto al lado. Rostro con gesto de dolor cuando hay persona.
- **Elementos típicos:** `cuerpo_afectado` · `rostro_humano` · a veces `sello_mas_vendido`; **poco texto**
- **Rol de embudo:** **TOFU**.
- **Evidencia:** **124 días de mediana — la supervivencia más alta del catálogo.** 4/4 mencionan el problema. Solo 2 anunciantes (Valle Lo Vende, Dr. Felipe Flores) → transversalidad **no confirmada**.
- **Ejemplos:** #9/#10 Valle Glucosamina (rodilla) · #20 Stone Dissolver (riñones) · #22 Varicose Cream (pierna)
- ⚠️ Es lo más cerca que el mercado real llega al *"enfoque agresivo"* de `DOCTRINA/PLANTILLAS_ADS.md`. Nadie usa amenaza cruda: usan la zona señalada.

### C4 — TRANSFORMACIÓN
> Antes / después.

- **Firma:** imagen partida con etiquetas ANTES y DESPUÉS (muslo, abdomen, rostro) + escalera de precios.
- **Elementos típicos:** `antes_despues` · `cuerpo_afectado` · `escalera_precios` · `iconos_beneficio`
- **Rol de embudo:** **MOFU**.
- **Evidencia:** 102 días de mediana. Solo 3 casos, 2 anunciantes.
- **Ejemplos:** #13 Candela (estrías/celulitis) · #17 Liquid Chlorophyll (abdomen) · #36 The Ordinary (rostro/acné)
- 🔴 **Choca con la regla vigente** *"prohibido antes/después bilateral de cuerpo"*. Ver §6.

### C5 — EVIDENCIA CRUDA
> No parece un anuncio.

- **Firma:** o bien **foto clínica sin una sola letra ni producto** (pie con gota sobre camilla, sobre piso de cemento), o bien **captura de una conversación de chat** donde alguien recomienda el producto.
- **Elementos típicos:** `producto_visible = 0` en la variante foto · **cero** badges, precio, íconos y franja
- **Rol de embudo:** **TOFU**.
- **Evidencia:** ⚠️ **NO validado por supervivencia** — 6 días. Pero el anunciante (Doctora Patricia Morales) está pagando **x3 réplicas**, o sea que ya apostó dinero. Un solo anunciante.
- **Ejemplos:** #29 y #31 (pie con gota, sin texto) · #32 (captura iMessage con foto del frasco adentro)
- 💡 **Es el territorio vacío del mercado GT.** 33 de 36 ganadores son cartel publicitario; este es el único que se disfraza de contenido. Candidato natural a ventaja — y el más barato de producir.

### C6 — UNBOXING
> Mano real sosteniendo la caja de envío abierta.

- **Firma:** foto no-estudio, mano/manos sosteniendo el pedido con relleno de papel, unidades múltiples visibles + badges de garantía + stock limitado.
- **Elementos típicos:** `mano_sosteniendo` · `caja_envio` · `multiples_unidades` · `stock_urgencia` · `garantia`
- **Rol de embudo:** **MOFU** (resuelve la objeción "¿de verdad llega?").
- **Evidencia:** ⚠️ **NO validado** — 7 días, un solo anunciante (KetsalStore), pero **x4 réplicas**.
- **Ejemplos:** #23 y #24 KetsalStore Lymphatic Drainage
- **Regla de fusión aplicada:** #23 y #24 se describen con la misma frase estructural → **un solo concepto con distinto relleno**, no dos. (Misma verificación que el piloto hizo con Ketsal #15/#19.)

---

## 4. QUÉ CONCEPTO VA EN CADA FASE

```
FASE 1  → varía el ÁNGULO, fija el CONCEPTO = C2 BENEFICIOS
FASE 2  → fija el ÁNGULO (el ganador), varía el CONCEPTO = los 6
```

**Por qué C2 y no C1:** FASE 1 existe para medir qué ángulo resuena. C1 OFERTA no nombra el
problema en 6 de sus 10 casos — usarlo de control apagaría exactamente la señal que se busca.
C2 es el concepto donde **6 de 7 creativos nombran el problema**, y funciona con o sin precio.

**Corrección respecto de `_ESTRATEGIA_CONCEPTOS.md` §6.4:** ahí el control propuesto era
*"P4 HOOK DE PROBLEMA"*, una plantilla de pregunta grande + producto + íconos. La data la
confirma en lo esencial pero la precisa: **el hook de dolor no es un concepto propio, es la
APERTURA de C2.** No existe en el swipe un ganador que sea solo pregunta + producto sin la
columna de íconos. Lo que gana es la pregunta **con** el desarrollo del beneficio.

**Mapeo con la hipótesis P1-P5 de la estrategia:**

| Hipótesis | Qué dice la data |
|---|---|
| P1 TARJETA DE OFERTA | ✅ confirmada = **C1**. La mejor evidenciada de todas. |
| P2 AUTORIDAD CLÍNICA | ❌ **1 caso de 36.** No alcanza para concepto propio → pasa a variante de C2 |
| P3 TESTIMONIO / CHAT | ⚠️ **1 caso** (#32) → absorbida en **C5** como su variante "captura" |
| P4 HOOK DE PROBLEMA | ⚠️ reformulada = **C2** (el hook es la apertura, no el concepto) |
| P5 CHOQUE / AMENAZA | ❌ **cero casos** de amenaza cruda → lo que existe es **C3 SÍNTOMA**, mucho más suave |
| *(no previstos)* | **C4 TRANSFORMACIÓN**, **C5 EVIDENCIA CRUDA**, **C6 UNBOXING** |

Tres de los seis conceptos reales **no estaban en la hipótesis**. Era esperable: la hipótesis
se armó con 1 análisis profundo y 3 imágenes.

---

## 5. LOS CUATRO QUE NO ENTRARON (y por qué)

No se pierden — se usan como **variante** (relleno) dentro de un concepto, sin ocupar un valor de `concepto_key`:

| Observado | n / días | Se absorbe en | Nota |
|---|---|---|---|
| **Ficha de fórmula** (ingredientes con mg) | 2 / 119d | C2 BENEFICIOS | sustituye los íconos por el desglose. #11 Creatine · #18 NeuraZenx |
| **Producto hero** (producto grande, promesa, sin precio ni problema) | 2 / 151d | C1 OFERTA | es C1 sin la cifra. #8 Alexa · #15 Almohada — ambos fuera del nicho salud |
| **Escena de vida** (persona mayor caminando/durmiendo, producto en el mueble) | 2 / 56d | C2 BENEFICIOS | es un fondo, no un dispositivo. #34 · #35 Rincón |
| **Autoridad clínica** (médico + collage de síntomas + credencial) | 1 / 24d · **x9** | C2 BENEFICIOS | ojo: x9 réplicas. Si aparece en otro anunciante en el re-análisis, **promoverlo a concepto propio** |

---

## 6. CHOQUES CON REGLAS VIGENTES DEL SISTEMA

Medido sobre los 36, no sobre impresión. **No son órdenes de cambiar nada** — son el input para decidir.

| Regla del sistema | Lo que hacen los ganadores | Veredicto honesto |
|---|---|---|
| *"prohibido antes/después bilateral de cuerpo"* | 3 de 36 (8 %) lo hacen, con 102-113 días de vida | **la regla no está refutada**: 8 % es marginal y ninguno tiene réplicas. Convive, no domina |
| *"formato de testeo 4:5 ÚNICO"* | **1:1 en 23 de 36 (64 %)**; 4:5 solo 6 (17 %), 9:16 4, 2:3 3 | **la regla sí está en tensión.** El formato dominante del mercado GT es cuadrado, no vertical |
| *"texto en imagen < 20 %"* | la mayoría lo excede con claridad | tensión real, pero **no medible** con lo que hay — requiere medir área, no ojo |
| *"precio máx 3 de 6, ideal 2 de 6"* | **66 %** lleva precio (no 100 % como dijo el piloto) | tensión moderada. Y hay 12 ganadores sin precio, el más viejo de 197 días |
| *"rostro mirando el producto convierte"* (Clase 4) | **27 %** tiene rostro; el x16 y el de 266 días no lo tienen | la regla **no se sostiene como requisito**. Es opcional |

> El único choque que trataría como accionable ya es el de **formato**: 64 % contra 17 % no es ruido.
> Los demás piden un test, no un cambio de regla.

---

## 7. LÍMITES DE ESTA EVIDENCIA — leer antes de usarla

1. **`días_corriendo` mide supervivencia, no rentabilidad.** Un anuncio puede llevar 266 días activo por inercia del anunciante. Es la mejor señal pública disponible; no es CPA.
2. **`réplicas` mide duplicación, no gasto.** La API pública no expone spend ni engagement de ads comerciales.
3. **C5 y C6 no están validados por supervivencia** (6-7 días). Entran al catálogo por réplicas y por ser territorio distinto, no porque el mercado los haya probado.
4. **C3 y C4 vienen de 2 anunciantes cada uno.** Transversalidad no confirmada.
5. **Sesgo de supervivencia:** solo se ven los ads vivos hoy. Los conceptos que murieron rápido no están en la muestra — se corrige en el re-análisis del ~2026-09-01, cruzando por `ad_archive_id`.
6. **La codificación de `_ELEMENTOS.csv` es observación humana**, no derivación automática. **No se regenera con un script.**

---

## 8. VOCABULARIO CERRADO — `concepto_key`

Valor a registrar en `PRODUCTOS/_DIM_CONJUNTOS.csv`. Cerrado, igual que `emocion_dominante`:

```
C1_OFERTA · C2_BENEFICIOS · C3_SINTOMA · C4_TRANSFORMACION
C5_PRUEBA · C7_DESEO · C8_PROGRESION · C9_COMPARACION
```

Más `SIN_CLASIFICAR` para las filas históricas anteriores a este catálogo.
`C6_UNBOXING` **queda retirado** como valor propio — es variante de C5.

---

# PARTE II — LOS TRES CONCEPTOS NUEVOS (aporte de los 111 favoritos)

## Distribución medida sobre los 111

| CONCEPTO | n | % | anunciantes | días med | ≥21d | réplicas ≥2 |
|---|---|---|---|---|---|---|
| **C2 BENEFICIOS** | 41 | 36 % | **23** | 8 | 9 | 11 |
| **C4 TRANSFORMACIÓN** | 17 | 15 % | 9 | 11 | 7 | 2 |
| **C5 PRUEBA** | 15 | 13 % | 7 | 7 | 1 | 6 |
| **C8 PROGRESIÓN** ⭐ | 12 | 10 % | 5 | 5 | **0** | **7** |
| **C7 DESEO** ⭐ | 9 | 8 % | 3 | 7 | 3 | 1 |
| **C3 SÍNTOMA** | 7 | 6 % | 5 | 24 | 4 | 1 |
| **C1 OFERTA** | 5 | 4 % | 5 | **27** | 3 | 3 |
| **C9 COMPARACIÓN** ⭐ | 5 | 4 % | 4 | 3 | 0 | 2 |

⭐ = nuevo en v2

**Lo primero que salta: C2 BENEFICIOS con 23 anunciantes distintos.** En la muestra por data ya
era el segundo más transversal; acá es el primero por amplio margen. **La decisión de usarlo como
`concepto_control` de FASE 1 queda confirmada por dos muestras independientes**, y esa es la
conclusión más sólida de todo el trabajo.

---

### C7 — DESEO
> El cuerpo que querés tener, no el que te duele.

- **Firma:** modelo de cuerpo entero encarnando el **resultado deseado** (glúteos, silueta, piel, energía), sosteniendo el producto, + íconos de beneficio + prueba social numérica.
- **Diferencia con C3 SÍNTOMA:** C3 muestra la zona **enferma** (rodilla con halo rojo, pierna con várices). C7 muestra el **estado final aspiracional**. Son opuestos exactos y por eso no se pueden mezclar.
- **Rol de embudo:** **TOFU**.
- **Evidencia:** 9 casos pero **solo 3 anunciantes** — Aurora GT lo usa en 6 creativos casi idénticos. Transversalidad débil. 3 llegan a ≥21 días.
- **Ejemplos:** Aurora GT (Woman Curves, ×6) · Aranza Glow Shilajit · Dr. Felipe Flores Dr.Melaxin
- ⚠️ **Riesgo de compliance:** es el concepto que más se acerca al límite de Meta con cuerpo femenino. Aurora GT lo corre sin problema, pero conviene mirar el CPM antes de escalarlo.

### C8 — PROGRESIÓN
> Tres o cuatro estados en el tiempo, no dos.

- **Firma:** secuencia de 3-4 viñetas rotuladas (`SEMANA 0 / 4 / 8`, `ENERO / FEBRERO / MARZO`, `30 min / 6 h / 3 días / 10 días`) mostrando mejora progresiva — órganos ilustrados, rostros dibujados, o **fotos del propio síntoma** (la serie de orina con espuma de KetsalStore).
- **Diferencia con C4 TRANSFORMACIÓN:** C4 es **binario** (antes | después). C8 es **una línea de tiempo** y por eso vende *el mecanismo*, no solo el resultado: explica cuánto tarda y en qué orden pasa.
- **Rol de embudo:** **MOFU**.
- **Evidencia:** ⚠️ **el dato más interesante del catálogo — 12 casos, 5 anunciantes, 7 con réplicas, y CERO con ≥21 días.** Ningún creativo de este concepto lleva tres semanas vivo, pero cinco anunciantes distintos ya están duplicándolo.
- **Ejemplos:** Doña Oferta (rostros ilustrados ×3) · KetsalStore (riñones semana 0/4/8; orina antes/24h/3sem) · Teyra (pulmones semana 0/2/3) · Mi Camino al Bienestar (15 min/2 h/14 días)
- 💡 **Lectura:** esto tiene forma de **tendencia emergente**, no de ganador establecido. La combinación "muchos anunciantes + muchas réplicas + cero antigüedad" es exactamente lo que se ve cuando un formato se está adoptando ahora mismo. **Es la hipótesis número uno a verificar en el re-análisis del ~2026-09-01.**

### C9 — COMPARACIÓN
> Dos columnas: lo malo contra lo bueno.

- **Firma:** pantalla partida vertical con etiquetas contrapuestas (`FALSA | REAL`, `Problemas | Solución`, `Yo SIN :( | Yo CON :)`, `Remedios caseros | Tratamiento`), X rojas de un lado y checks verdes del otro.
- **Rol de embudo:** **MOFU** — trabaja la objeción, no el dolor.
- **Evidencia:** 5 casos, 4 anunciantes. Poco volumen pero **buena dispersión**, y dos variantes de propósito distinto:
  - **anti-falsificación** (Doctora Patricia: original vs imitación de Amazon) — resuelve desconfianza
  - **contra la alternativa** (Topishop: remedios caseros vs tratamiento; Mi Camino: problemas vs solución)
- **Ejemplos:** Doctora Patricia Morales (FALSA/REAL) · Topishop (VS remedios caseros) · Mi Camino al Bienestar y Teyra (`Yo SIN / Yo CON`, dibujado a mano — **el mismo molde en dos anunciantes distintos**, señal de que circula como plantilla)

---

## C5 renombrado: de EVIDENCIA a **PRUEBA**

Con los 111 quedó claro que "no parece un anuncio" y "prueba social" son el mismo dispositivo:
**mostrar realidad en vez de afirmarla**. C5 absorbe ahora cinco variantes, y pasó de 1 anunciante a **7**:

| Variante | Ejemplo |
|---|---|
| foto clínica cruda (sin texto ni producto) | Doctora Patricia (pie con gota) · Megacompras (selfie señora; mesa de noche con pomadas y receta) |
| captura de chat | Doctora Patricia (iMessage) · Vida Natural (burbujas sobre escena casera) |
| **captura falsa de búsqueda de Google** | Megacompras ×2 — una de ellas dentro de un mockup de teléfono |
| selfie / UGC casero con caption tipo IG | Vida Natural (cocina) · Mi Camino al Bienestar |
| testimonios con foto, nombre y ciudad · rating grande | Teyra (3 testimonios) · Topishop (4.95/5 · 1.455 clientes ×3) |
| unboxing (ex-C6) | KetsalStore ×2 |

La **captura falsa de búsqueda de Google** no estaba en ninguna hipótesis previa y es, junto con C8,
lo más distinto que apareció. Cero elementos de anuncio: ni precio, ni badge, ni CTA.

---

## Correcciones a la PARTE I que impone la muestra grande

1. **"P5 CHOQUE/AMENAZA no existe" — era falso, existe pero es rarísimo.** Apareció 1 caso en 133: Topishop invierte el antes/después para mostrar **empeoramiento** (`uña con daño leve → daño avanzado`) con el copy *"no esperes a que cambien más"*. Es amenaza de progresión del daño. Queda como **variante de C4**, no como concepto.
2. **C1 OFERTA baja de 10/36 a 5/111.** Sigue siendo el más longevo (27 días de mediana en esta muestra, 266 en la otra) pero es mucho menos frecuente de lo que sugería la muestra por supervivencia. **Ojo con el sesgo circular:** filtrar por antigüedad favorece justo al concepto que los anunciantes dejan corriendo por inercia.
3. **C6 UNBOXING no ganó respaldo** — sigue en 2 casos y 1 anunciante después de mirar 133 creativos. Por eso se degrada a variante.
4. **Existe una ESTÉTICA EDITORIAL que la v1 no vio.** Mi Camino al Bienestar y Doña Oferta corren creativos **sin badges, sin franja de confianza, sin precio y a veces dibujados a mano**, con aire de post de blog en vez de cartel. Cruza varios conceptos (C8, C9, C5) — es un eje de **estética**, no un concepto. Vale la pena testearla contra la estética "cartel" con el mismo concepto.

---

---

# PARTE III — DECISIONES OPERATIVAS (19-ago, cerradas)

## 1. Qué se fija en cada fase

```
FASE 1 → 6 ÁNGULOS distintos  ×  concepto FIJO C2_BENEFICIOS      ← mide el ÁNGULO
FASE 2 → 1 ángulo (el ganador) × 10 CONCEPTOS distintos           ← mide el CONCEPTO
FASE 3 → 1 ángulo + 1 concepto, ambos validados × 7 instancias    ← compra volumen
```

> 🔴 **Actualizado 02-sep-2026 — la FASE 2 ahora tiene estructura de campaña, no solo un número.**
> Los 10 conceptos corren en **`1-1-5 + 1-1-5 + 1-2-5`**: dos campañas de 5 anuncios cada una (A y B)
> más una tercera (C) que repite **los mismos 10** en dos conjuntos y **en otra cuenta**. Cada
> concepto aparece **dos veces** → se corona por **replicación (gana en 2 de 2)**, no por una
> corrida. Presupuesto $6/conjunto = **$24/día**, y el `%PD` se suma **por concepto entre sus dos
> apariciones** (~4.1 días a 1× BE; leerlo por conjunto daría 8.3 y mataría conceptos por
> impaciencia). Todo en `DOCTRINA/CALENDARIO_ESCALADO.md` §1.7.
>
> **Y los 10 no son 10 `concepto_key` nuevos** — son **10 EJECUCIONES** etiquetadas con los 6
> conceptos de la rotación (§3 de esta parte). Con 8 valores y 12-24 conjuntos/mes, estrenar
> vocabulario en cada tanda es garantizar que ningún concepto acumule observaciones nunca.
> El `concepto_key` de FASE 2 se registra en **`_DIM_CREATIVOS.csv`** (distingue anuncios), no en
> `_DIM_CONJUNTOS.csv` (donde el ángulo es constante y no distingue nada).

**Los 6 creativos de FASE 1 comparten layout, paleta, tipografía y estructura.** Cambian solo:
hook, los 4 beneficios, props y avatar. **No se rota el estilo anti-fatiga** — eso es de FASE 2.

- **Por qué:** con Andrómeda el creativo explica ~56 % del resultado, más que el ángulo. Si ángulo y ejecución se mueven juntos, ningún conjunto ganador es atribuible y el testeo se pierde entero.
- **No es iteración perezosa.** Iteración perezosa = la misma imagen con otro título o color. Seis variantes del mismo concepto, con distinto hook, dolor, props y avatar, son **seis creativos únicos para Meta** — que detecta duplicados por huella de contenido, no por estructura (`Ads/_TOOLS/LAVADO.md`). La diversidad de entrega se mantiene.
- Regla corregida en `.claude/agents/ETAPA-2.md`; prompts en `DOCTRINA/PLANTILLAS_ADS.md`.

## 2. Qué variante de C2 es el control: la **LIGERA**

C2 tiene tres variantes observadas, y el operador las separó a ojo antes de conocer esta clasificación:

| Variante | Qué es | Ejemplo |
|---|---|---|
| **`ligera`** ✅ | pregunta de dolor + 3-5 íconos + producto + precio opcional | Valle Ginkgo **197 d** · Oftalmiel **×10** |
| `densa` | + síntomas + mecanismo + ficha de fórmula + 6 badges + escalera de precios | NeuraZenx 89 d |
| `colage-sintomas` | + rostro de autoridad + fotos de síntomas con check | Candida Cleanse **×9** |

**Va la `ligera`.** El hook tiene que dominar la composición porque **el hook ES el ángulo que se está midiendo**; la variante densa lo entierra bajo veinte elementos. Además es la que sostiene el creativo C2 más longevo del banco (197 días) — y ese corre **sin precio**.

> La separación `ligera` / `densa` la aportó el operador; la clasificación por elementos las tenía a las dos como un solo C2. Es una sub-variante real y vale medirla.

## 3. Los 6 conceptos de la rotación de FASE 2

| # | Concepto | Por qué entra |
|---|---|---|
| 1 | **C2_BENEFICIOS** | el control — va siempre, permite comparar entre productos |
| 2 | **C1_OFERTA** | BOFU. 266 días y ×16, lo mejor evidenciado del banco |
| 3 | **C4_TRANSFORMACION** | 17 casos, 9 anunciantes — el mejor respaldado después de C2 |
| 4 | **C8_PROGRESION** | ⭐ entra **sin estar validado**, para medirlo antes de que sature |
| 5 | **C5_PRUEBA** | el más barato de producir y el territorio más vacío del mercado |
| 6 | *rotativo* | **C3_SINTOMA** si el producto es de dolor · **C7_DESEO** si es de estética |

`C9_COMPARACION` queda en el banco como séptimo, listo para rotar.

## 4. Las tres capas de producción

El precio **no es parte del layout**: es una variable independiente. Hornearlo en la plantilla obliga
a mantener 3 layouts × 3 precios = 9 plantillas, que es el problema de las 50 otra vez.

| Capa | Valores | Cubre |
|---|---|---|
| **LAYOUT** | `L1 CARTEL VERTICAL` · `L2 PARTIDO` · `L3 NATIVO` | L1 → C1, C2, C3, C7 · L2 → C4, C8, C9 · L3 → C5 |
| **BLOQUE DE PRECIO** | `sin precio` · `1 unidad` · `escalera 1/2/3` | se enchufa a cualquier layout |
| **ESTÉTICA** | `cartel` · `orgánico-UGC` | ortogonal al concepto |

`3 × 3 × 2 = 18 combinaciones` con solo 8 piezas que mantener, y `concepto_key` sigue siendo una sola columna medible.

> ⚠️ **El bloque de precio no se decide creativo por creativo.** La arquitectura de oferta (1u vs 2x1, qué precio se muestra) tiene dueño: `.claude/agents/ETAPA-1.md`. Si el ad anuncia el precio de 1 unidad y el bot arranca en 2, se rompe la verificación de coherencia copy↔bot del cierre de FASE 1.

## 5. Banco físico de referencias

`Ads/_SWIPE/_BANCO_CREATIVOS/` — una carpeta por `concepto_key`, 43 referencias con su `_INDICE.csv` y su `_LEEME.md`. **Son referencias para producir, nunca creativos para pautar.**

---

## Nueva tensión: 8 conceptos contra la regla 6

Con 12-24 conjuntos/mes y 8 valores, cada concepto recibe **1,5-3 observaciones por mes** — por
debajo de las 3-6 que justificaban el techo de 6. La salida honesta no es inventar significancia:

- **El vocabulario queda en 8** (hace falta para describir lo que existe).
- **La rotación de FASE 2 usa 6 por producto**, elegidos así: **C2 siempre** (es el control y la referencia cruzada) + **C1 siempre** (BOFU, es la que monetiza) + **4 rotativos** según el nicho.
- **C8 PROGRESIÓN entra en la rotación de los próximos productos aunque no esté validado** — precisamente para medirlo antes de que el mercado lo sature.


---

## 6. Equivalencia con la numeracion de la carpeta del operador (19-ago)

El operador armo a mano una carpeta de 44 referencias agrupadas en 10 familias numeradas
`1..10`. **Esa numeracion NO es el `concepto_key`** y ya causo un malentendido: el `#4` del
operador (UGC) es `C5_PRUEBA`, no `C4_TRANSFORMACION`. Tabla de traduccion:

| # carpeta | Que es | `concepto_key` |
|---|---|---|
| 1 | Candida Cleanse — doctor + collage de sintomas + precio | `C2_BENEFICIOS` · variante **colage-sintomas** |
| 2 | Oftalmiel — pregunta + 5 iconos + producto + precio | `C2_BENEFICIOS` · variante **ligera** |
| 3 | NeuraZenx — sintomas + mecanismo + badges + escalera | `C2_BENEFICIOS` · variante **densa** |
| 4 | GastroPylls — selfie en cocina, caption tipo post | `C5_PRUEBA` (UGC) |
| 5 | Psoriasis — foto grande del sintoma + 3xQ249 | `C3_SINTOMA` |
| 6 | The Ordinary — ANTES / DESPUES partido | `C4_TRANSFORMACION` |
| 7 | Oftalmiel — "2 FRASCOS Q209.83" | `C1_OFERTA` |
| 8 | Lymphatic Drainage — caja abierta en manos | `C2_BENEFICIOS` · estetica organica |
| 9 | Astaxanthin — ANTES / POCO DESPUES / USO CONTINUO | `C8_PROGRESION` |
| 10 | Woman Curves — gluteos | `C7_DESEO` |

> Al hablar de conceptos se usa **siempre el `concepto_key`**, nunca el numero de carpeta.
> Las 44 imagenes son duplicados de `_IMG/`; no se copiaron al repo.

### Los 4 brazos de T01, confirmados por el operador el 19-ago
`#1 colage-sintomas` · `#2 ligera` · `#3 densa` · `#9 progresion` — es decir el diseno original.
Como 1-2-3 comparten `concepto_key`, **T01 corona la mejor VARIANTE del control, no el mejor
concepto**; sirve para elegir con que se testean los angulos, pero no valida el catalogo.
