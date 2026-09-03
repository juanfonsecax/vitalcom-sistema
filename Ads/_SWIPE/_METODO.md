# SWIPE FILE — MÉTODO DE COSECHA DE CREATIVOS DE COMPETENCIA (GT · bienestar)

> Banco de imágenes ganadoras de competidores en Guatemala. Alimenta `PLANTILLAS_ADS.md`
> vía la skill `analizador-creativos`. NO es fuente de métricas — es referencia creativa.

## Las dos capas (no confundirlas)

**CAPA 1 — detección de anunciantes vivos.** *(hecha: 89 páginas)*
Búsqueda en Ad Library por keyword del nicho, orden **Most recent**, se anotan las páginas
que están publicando anuncios NUEVOS. Los creativos nuevos NO se descargan: no están
validados. Lo que se cosecha es la LISTA de quién tiene presupuesto activo.
Repetir la barrida en días distintos: la página que reaparece en varias sesiones es la
que más invierte. → columna `n_apariciones` de `_PAGINAS.csv` (orden de prioridad).

**CAPA 2 — cosecha de ganadores.** *(dentro de cada página de la lista)*
Ahí sí se descargan imágenes, y solo las que pasan filtro.

## Filtro de cosecha (capa 2)

Los links de `_LINKS_TANDAS.txt` ya abren con `sort_data[mode]=total_impressions`.

- **Pasada A** — orden por impresiones, sin filtro de fecha → **top 8-10**.
  Caballos establecidos.
- **Pasada B** — mismo orden + botón `Filters` → fecha desde hace 30 días → **top 5**.
  Winners calientes: están arriba con una fracción del tiempo = velocidad.
  (Aplicar el filtro desde la UI. Por parámetro de URL no reordena.)
- Si aparece el contador "X ads use this creative" con N ≥ 4 → cosechar aunque esté abajo.
- Días corriendo = **desempate**, no criterio principal.

**Nunca filtrar "de tal fecha para atrás".** Impresiones son ACUMULADAS: premian la
antigüedad y sepultan al winner reciente, que es justo el que hay que copiar.

**Meta NO publica el número de impresiones para ads comerciales** (verificado 2026-08-17).
El dato es la POSICIÓN en la lista, no una cifra.

## Triaje de la página al abrirla

Mirar `~N results` y la fecha activa más antigua:

| Señal | Estado | Acción |
|---|---|---|
| muchos ads + los hay de 2-3 meses | ganador maduro | `COSECHADA` |
| muchos ads, todos del último mes | testeando a ciegas | `OBSERVAR` (+21 días) |
| pocos ads y viejos | estancado | `VACIA` |
| sin ads activos | — | `MUERTA` |

Sin cuota por página: que 30 de 89 den cero está bien. Un banco chico de ganadores
probados vale más que uno grande de indefinidos — creativos sin veredicto contaminan
`PLANTILLAS_ADS.md` con patrones que fracasaron.

## Valor aparte: producto en tendencia

Un ad nuevo no enseña a diseñar, pero sí avisa qué se empieza a mover. **El mismo
producto apareciendo nuevo en 3-4 páginas distintas** = ventana de producto abriéndose.
Anotarlo en `notas` y pasarlo a la skill `buscar-producto` (FASE 0).

## Barrido automatizado (17-ago-2026) — CERRADO

Las 89 paginas se cosecharon por script, sin abrir pestanas a mano. El navegador hace fetch
a la URL de Ad Library y parsea el JSON embebido en el script tag de la pagina, sacando por
cada anuncio: page_name, collation_count, start_date, copy y URL directa de la imagen.
Luego se descarga del CDN. Resultado: 190 creativos unicos de 85 anunciantes.

Hallazgos tecnicos (verificados, no supuestos):

- **El navegador es obligatorio.** Facebook devuelve 403 a curl sin sesion.
- **media_type:** el valor correcto es "image_and_meme". Con "image" la biblioteca
  responde "No ads match your search criteria" aunque la pagina tenga anuncios de imagen.
- **Orden:** sort_data[mode]=total_impressions&sort_data[direction]=desc. Meta NO publica
  el numero de impresiones para ads comerciales — el dato util es la POSICION en la lista.
- **Filtro de fecha por URL no funciona:** start_date[min] se registra en el contador de
  filtros pero no filtra el listado. Por eso el filtro de dias se calcula en el script.
- **Resolucion:** 600x600 es el maximo. Quitar "stp=" de la URL da 403 (la firma "oh"
  cubre la URL completa, no se puede recortar ningun parametro).
- **Dedupe por hash MD5**, no por nombre de archivo: un mismo creativo aparece bajo varios
  ad_archive_id, y ese conteo ES la senal de escalado (columna replicas_misma_imagen).

### SCORE de ranking (en gen_galeria.py)

    score = escalado*20 + (15 si dias >= 21) + velocidad
    velocidad = posicion_en_ranking * 30 / max(dias, 7)

⚠️ **El piso de 7 dias en el denominador es obligatorio.** Sin el, un anuncio de 1 dia
divide por 1 y encabeza el ranking — justo el creativo sin veredicto que NO hay que copiar.
Los de menos de 7 dias se marcan SIN VEREDICTO y van al final de la galeria.

## Archivos

- `_PAGINAS.csv` — 89 páginas, llave `page_id`, ordenadas por `n_apariciones`.
- `_LINKS_TANDAS.txt` — 9 tandas de 10 links, listas para "Open Multiple URLs".
- `_INBOX/` — destino de descarga del navegador; se clasifica después por `ad_archive_id`.
