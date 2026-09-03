# AUDITORIA — Metodo de barrido del Swipe File
Fecha: 2026-08-18 · Auditor: sesion Claude (rol externo/critico) · Alcance: proceso completo de captura y triage, no el contenido creativo en si.

## Veredicto en una linea
El criterio de "ganador = ad corriendo >=21 dias" es correcto y coincide con el estandar de la industria. **La ejecucion sobre las 22 paginas descartadas fue defectuosa: la decision se tomo con una muestra incompleta (1-4 de cada 4-8 ads activos), no con el dato completo.** Antes de cualquier conclusion de "esta pagina no tiene ganador" hay que volver a consultarla con el extractor completo (N=18, lo mismo que se uso para las 30 paginas grandes). El caso que detecto el operador (Eco Quetzal Shop) confirma el patron, no es un caso aislado.

---

## 1. Que dice la industria (research externo, 2026)

Fuentes: Minea, PiPiADS, Dropispy, AdMapix, Dropship.io, TrendTrack (ver Sources al final).

| Señal | Umbral que usa la industria | Lo que hace nuestro sistema |
|---|---|---|
| Duracion del ad activo sin pausar | **>=14 dias** = winner probable; 21-30d = confianza alta | Usamos **21d** para `GANADOR_ESTABLECIDO` (bien calibrado, lado conservador) |
| N.º de variantes creativas del mismo anunciante | **5+ variantes** = estan escalando activamente | Lo capturamos como `collation_count`/`replicas` (campo `cc`) pero **no lo usamos** como señal de triage — solo miramos dias |
| N.º de anunciantes corriendo el mismo producto/angulo | 8-15 anunciantes = demanda validada sin saturar; <5 = no probado; >25 = saturado | No lo medimos — analizamos pagina por pagina, nunca por producto/angulo cruzado entre paginas |
| Engagement (likes/comments/shares) | >=500 likes, >=100 comments = interes real | **No disponible** vs API publica de Ads Library para ads comerciales (no politicos) — limitacion estructural, no un bug nuestro |
| Impresiones absolutas | >=100k = señal fuerte | **No disponible** — Meta solo expone rango de impresiones para ads politicos/de interes social. Para ads comerciales normales (nuestro caso) la Library no entrega spend ni impresiones absolutas, solo permite *ordenar* por `total_impressions`. Por eso el sistema usa `pos` (posicion relativa dentro de la pagina) como proxy — es razonable, pero hay que ser explicitos en que es un proxy, no el dato real. |

**Conclusion del research:** nuestro criterio central (dias corriendo) esta bien elegido y calibrado de forma conservadora. El problema no es el criterio — es que lo aplicamos con datos incompletos, y que ignoramos una señal que si tenemos disponible (variantes/`collation_count`).

Sources:
- [Facebook Ad Library: Find Winning Dropshipping Products](https://eprolo.com/facebook-ad-library-dropshipping-products)
- [Facebook Ads Library (2026): Find Winning Ads & Competitor Insights — Minea](https://www.minea.com/competitor-analysis/competitor-spy-tools/facebook-ads-library)
- [3 Methods to Find Winning Products Using Facebook in 2026 — Sell The Trend](https://www.sellthetrend.com/blog/dominate-facebook-winning-product-research-with-these-methods)
- [Find winning products on Facebook: complete guide — Dropispy](https://dropispy.com/find-winning-products-on-facebook-the-complete-guide/)
- [Ways To Use Facebook Ad Library To Find & Beat Your Competitors — Dropship.io](https://www.dropship.io/blog/ways-to-use-facebook-ad-library)
- [Find Winning Products on Facebook Ads Library (2026) — AdMapix](https://www.admapix.com/blog/app-going-global/find-winning-products-facebook-ads-library)
- [AdSpy Tool – Find Winning Ads & Products in 2026 — Minea](https://www.minea.com/adspy)
- [Minea vs PiPiAds vs TrendTrack: Best Value in 2026](https://www.trendtrack.io/blog-post/minea-vs-pipiads-vs-trendtrack)

---

## 2. Fallas encontradas en nuestro sistema (por severidad)

### FALLA CRITICA — Triage de las 22 paginas hecho con muestra incompleta
Cuando se decidio "SKIP-testeo" para las 22 paginas chicas, el `max(dias_corriendo)` se calculo sobre los ads que **ya estaban** en `_ADS.csv`/`_BANCO.csv` de un barrido de superficie anterior — **no** se volvio a consultar la pagina con el extractor completo (`N=18`, el mismo que trajo Compra GT con su ganador de 266 dias).

Evidencia puntual (`Eco Quetzal Shop`, `page_id=892576310599899`):
- `ads_activos` real segun `_PAGINAS.csv`: **6**
- Ads muestreados en la superficie original: **2** (posiciones #1 y #3 — la #2 se salto)
- Con esos 2 se concluyo "max 8 dias, sin ganador" → **SKIP**
- Pero nunca se vieron las posiciones #4, #5 y #6. Es matematicamente imposible descartar la pagina con 33%-50% de los datos.

Se repite el mismo patron en **las 22 paginas**, sin excepcion: el numero de ads muestreados en la superficie original fue siempre 1-4, nunca igual al total de `ads_activos` de la pagina (ver tabla de verificacion abajo). La conclusion "sin ganador" para esas 22 paginas **no esta soportada por el dato** — es una extrapolacion sobre una muestra parcial, no una medicion.

Nota a favor: para las 4 paginas donde SI se encontro ganador con esa misma muestra parcial (Ovejita Shop 37d, Ovejitas Lab 27d, GoMarket 23d, Compra GT 266d), el hallazgo es valido — un dato positivo encontrado en una muestra chica sigue siendo un dato real. El problema es solo con los **negativos** (concluir "no hay" cuando no se miro todo).

### FALLA MEDIA — Señal de escalado (`collation_count`/replicas) capturada pero no usada
El campo `cc` (cuantas veces Meta agrupo variantes de un mismo concepto bajo un `ad_archive_id`) es exactamente la señal de "5+ variantes = estan escalando" que usa la industria (Minea). Lo estamos guardando en el CSV desde el principio, pero el triage de esta sesion solo miro `dias_corriendo`. Una pagina con pocos dias pero `cc` alto (muchas variantes activas del mismo concepto en paralelo) tambien es señal de que encontraron algo y lo estan iterando — hoy esa señal se ignora.

### FALLA MEDIA — Ads de catalogo dinamico mezclados sin distincion con creativos manuales
**9% del banco (49 de 542 filas)** son anuncios de **catalogo dinamico** (Advantage+ / feed de productos) — se identifican porque el titulo/descripcion trae literalmente `{{product.name}}`, `{{product.description}}`, `{{product.brand}}` sin rellenar (Meta no resuelve el placeholder cuando el feed no tiene datos completos para ese SKU en el momento del scrape). Estan concentrados: **Clickazogt tiene 16 de sus 18 ads capturados (89%) como catalogo puro.**

Por que importa: un ad de catalogo no es un "creativo" en el sentido que le interesa a este banco — es un contenedor automatizado que Meta rota entre productos de un feed. El "dias corriendo" de ese `ad_archive_id` mide cuanto lleva viva la *campaña de catalogo*, no cuanto lleva probado ese producto/imagen especifico. Contarlo igual que un creativo manual (imagen + copy deliberados) infla el conteo de "profundidad alcanzada" sin aportar el mismo valor de swipe (no hay hook, angulo ni copy que replicar — es generado por feed).

**Recomendacion:** agregar una columna `es_catalogo` (bool) al CSV y excluir esas filas del ranking de "mejores creativos" en `gen_galeria.py`, aunque se dejen archivadas como referencia de que producto/oferta esta corriendo esa tienda.

### FALLA MENOR — El proxy de "posicion" no es impresiones reales
`pos` viene de ordenar por `total_impressions` dentro de la pagina, pero Meta no entrega el numero absoluto para ads comerciales — es un ranking relativo, no una metrica absoluta. Esto ya esta bien documentado en el codigo (`_EXTRACTOR.js`, `bajar2.py`), pero no estaba explicito en `_HANDOFF.md`/`_METODO.md` que esto es una limitacion estructural de la API publica y no algo que se pueda arreglar con mas scraping. Vale dejarlo escrito para que nadie pierda tiempo despues buscando como sacar el numero real.

---

## 3. Verificacion: cobertura real de muestreo en las 22 paginas descartadas

| Pagina | ads_activos | ads muestreados (superficie) | % cubierto | dias max visto |
|---|---:|---:|---:|---:|
| Karen R Quetzaltenango | 8 | 3 | 38% | 3 |
| Salud y Bienestar con Dulet | 8 | 2 | 25% | 5 |
| Natural Vida Sana | 7 | 4 | 57% | 16 |
| Salud y bienestar Guatemala | 7 | 2 | 29% | 13 |
| Verdevital | 6 | 3 | 50% | 2 |
| Eco Quetzal Shop | 6 | 2 | 33% | 8 |
| Dapaju | 6 | 2 | 33% | 10 |
| SupleNat | 6 | 2 | 33% | 18 |
| Andromeda Market | 5 | 3 | 60% | 13 |
| Natura Shoppy Guatemala | 5 | 3 | 60% | 7 |
| Isla Everyday Wellness | 5 | 2 | 40% | 13 |
| Que Chilero | 5 | 2 | 40% | 10 |
| Dra Andrea Sofia Morales | 5 | 2 | 40% | 5 |
| NISTY | 5 | 2 | 40% | 3 |
| Transforma Tu Bienestar | 5 | 2 | 40% | 5 |
| Bienestar digestivo 360 | 5 | 2 | 40% | 5 |
| Medicina Alternativa | 4 | 3 | 75% | 7 |
| Vida Natural | 4 | 3 | 75% | 13 |
| Natural Pro Guatemala | 4 | 3 | 75% | 3 |
| BC Market GT | 3 | 1 | 33% | 4 |
| Body Care Market | 3 | 2 | 67% | 6 |
| A Domicilio | 2 | 1 | 50% | 5 |

**Cobertura promedio: ~45%.** Ninguna pagina fue vista al 100%. Cuatro (Medicina Alternativa, Vida Natural, Natural Pro Guatemala) llegaron a 75%, que es lo mas cerca que estuvimos de una lectura confiable — y aun asi no es completa.

---

## 4. Recomendacion accionable (al momento de escribir la auditoria)

1. **Volver a consultar las 22 paginas con el extractor completo (N=18)**, exactamente el mismo metodo que ya confirmo los 4 ganadores. Costo: ~17 llamadas de browser (2 paginas por llamada), mismo procedimiento ya rodado toda la sesion. Beneficio: elimina el sesgo de muestra y responde la pregunta real ("¿tiene ganador?") con el dato completo en vez de una extrapolacion.
2. **No cambiar el umbral de 21 dias** para `GANADOR_ESTABLECIDO` (esta bien calibrado, lado conservador de industria) — pero al re-consultar, tambien anotar si aparece algun ad con `cc>=3` aunque no llegue a 21 dias, como señal secundaria de escalado activo.
3. **Marcar los ads de catalogo dinamico** (`{{product.*}}` sin resolver) con un flag separado, para que no compitan en el ranking de creativos manuales de `gen_galeria.py`.
4. **Documentar en `_METODO.md`** que "posicion" es un ranking relativo, no impresiones absolutas, y que engagement/spend no estan disponibles vs la API publica de Ads Library para ads comerciales — para que una sesion futura no intente "arreglar" algo que es un limite de la fuente, no del codigo.

## 5. Cierre — resultado de la correccion (2026-08-18, mismo dia)

Se re-consultaron las 22 paginas con el extractor completo (N=18), aplicando la recomendacion #1. Resultado: **con el dato completo, ninguna de las 22 revelo un ganador nuevo** (ningun ad llego a 21+ dias que no se hubiera visto ya). La conclusion original de "sin ganador" resulto correcta en los 22 casos — pero **por resultado, no por metodo**: se llego ahi con una muestra que en promedio cubria menos de la mitad de los ads de cada pagina, y eso segua siendo una apuesta no un hallazgo, incluso si esta vez salio bien.

Dos paginas quedaron cerca del umbral y valen seguimiento en el re-analisis del 15-set:
- **SupleNat**: max 18 dias (pero 5 de 6 ads son catalogo dinamico — bajo valor de swipe aunque llegue a 21d)
- **Natural Vida Sana**: max 16 dias

Banco actualizado tras la correccion: **597 creativos, 95 anunciantes** (de 542/91 antes de re-consultar). El caso puntual que disparo la auditoria (`Eco Quetzal Shop`) quedo confirmado con dato completo: 7/7 ads vistos, max 8 dias — no tenia un ganador oculto, pero la duda del operador fue la correcta a plantear.

Pendiente de las recomendaciones #2, #3 y #4 (no ejecutadas aun): señal `cc>=3`, flag de catalogo dinamico en `gen_galeria.py`, y nota en `_METODO.md` sobre limites estructurales de la API.
