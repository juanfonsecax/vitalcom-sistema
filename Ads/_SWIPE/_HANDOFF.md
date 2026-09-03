# HANDOFF — continuar el barrido del SWIPE FILE

> ⚠️ **EL BARRIDO YA TERMINÓ (2026-08-18).** La fase activa ahora es la construcción del
> **catálogo de conceptos creativos** → arrancar por **`_HANDOFF_CONCEPTOS.md`**.
> Este archivo queda como registro del método de cosecha y para el re-análisis a 15 días.

> Para retomar en un chat nuevo. Modelo recomendado: **Sonnet 5** (el trabajo que queda es
> mecanico y repetitivo). Volver a Opus solo para el analisis final de agrupacion por tipos.

## Que hay hecho

- Las **89 paginas** de `_PAGINAS.csv` estan barridas en superficie (85 con creativos, 4 sin ads).
- **404 imagenes** en `_IMG/[anunciante]/` (88 anunciantes), indexadas entre `_ADS.csv` (225, indice viejo) y `_BANCO.csv` (179, indice nuevo con columna `cuadrante`).
- **35 copies completos** (texto principal + titulo + descripcion + CTA + destino) en `_COPIES.csv`.
- `_BANCO.csv` es el indice nuevo (con columna `cuadrante`); se llena con `bajar2.py`.
- `_GALERIA.html` se regenera con `gen_galeria.py` — **FIX 2026-08-18:** el script solo leia `_ADS.csv` y no veia nada de `_BANCO.csv` (dos indices desincronizados desde que se introdujo `bajar2.py`). Se corrigio para que lea y fusione ambos CSV (dedup por `ad_archive_id`, mapeando `titulo+descripcion+texto_principal`->`copy`, `pos`->`rank_impresiones`, `replicas`->`collation_count`). Verificar que este fix se mantenga si se vuelve a tocar el script.
- **Profundizadas 26 paginas** de `_PENDIENTES.txt` en la sesion del 2026-08-18 (orden: mas ads activos primero), de las 65 totales: Trendora, VitalBio, Dr. Felipe Flores, Aranza Glow, Tiendas KetsalStore, Tu oferta Online, Camila Recomienda, RyR Importaciones, Rincon de las Ventas Online, Guate compra, Doctora Patricia Morales, Flor Expres GT, Valle Lo Vende, Clickazogt, Mi Camino al Bienestar, Topishop, Suplementos Naturales Guatemala, FrezNova, Loopi Colombia, Megacomprasgt, Leyna Dolch Filandro, CasaClick, Roxana Recomienda, Easy Click Store, Aurora GT, Dona Oferta, Valestoreteam, YoHa, Guatestore, Dra Sofia Alejandra Morales, El Oferton Guatemala, Ixchel Store GT, Teyra, Tienda de Don Gato. Marcadas `DONE` en `_PENDIENTES.txt` las que llegaron a su profundidad objetivo, `DONE-agotada` las que ya no tenian mas ads nuevos que ofrecer (todo lo visto era duplicado/prev). `VitalBio`, `Aranza Glow` y `Tiendas KetsalStore` quedaron muy cerca (17/18, 13/18, 17/18) pero no se recortaron mas por rendimientos decrecientes.
  - `1125291077325276` (sin nombre en el CSV) no devolvio datos al consultarla — page_id probablemente vencido/movido. Revisar antes de reintentar.
  - **Nota tecnica de sesion:** el tab `seed` puede perder las funciones `window.__T/__C/__M` inyectadas si se abre o activa otro tab en el Browser pane (p.ej. al enviar un archivo al usuario que se renderiza en un tab nuevo) — hay que re-pegar el extractor completo y apuntar explicitamente `tabId:"seed"` en la llamada siguiente.

- **Triage de las 39 paginas chicas restantes (2026-08-18, criterio del operador):** con ads_activos ya bajo (<=8), la pregunta pasa de "cuantos ads tiene" a "tiene algun ganador real o es solo testeo". Se uso como filtro `dias_corriendo` del anuncio mas viejo ya visto en el barrido de superficie: **>=21 dias = ganador validado, vale la pena profundizar; <21 dias = cuenta chica/nueva sin nada probado, se descarta**.
  - **Profundizadas por tener ganador (4):** Ovejita Shop (37d), Ovejitas Lab (27d, mismo dominio `ovejitashop.com` que Ovejita Shop — posible cuenta hermana), GoMarket (23d), **Compra GT (266d — el ganador mas longevo de todo el banco)**.
  - **Descartadas por SKIP-testeo (33):** quedaron marcadas asi en `_PENDIENTES.txt` con su `max dias` entre parntesis, para que quede el razonamiento a la vista y no se re-litigue en otra sesion. Las 5 BAZAR (Nova Market GT, Mundohome, Luceselect GT) ya estaban resueltas por la regla de bazar, no por este criterio.
  - **1 sin datos:** `1125291077325276` sigue pendiente de revisar (page_id no devuelve resultados).

## Que falta

El barrido queda funcionalmente **completo bajo el criterio de ganador real**: las 30 paginas restantes son SKIP-testeo o BAZAR-superficie (ya resueltas). Si en el re-analisis a 15 dias (~2026-09-01) alguna de las SKIP-testeo desarrolla un ganador (un ad que llega a 21+ dias corriendo), vale la pena volver a esa pagina especifica.

## Procedimiento (repetir por tandas de 2-3 paginas)

1. **Una sola vez por sesion:** navegar el tab `seed` a cualquier URL de Ad Library
   (si no, el fetch falla con "No site is open"), y pegar `_EXTRACTOR.js` en
   `mcp__Claude_Browser__javascript_tool` cambiando `PAGE_ID_1`/`PAGE_ID_2` por los ids reales.
   Si el tab pierde el contexto JS (pasa al cambiar de pestana), re-pegar el extractor completo.
2. Copiar la salida tal cual a `_RAW/masivo/mNN.txt` (heredoc con delimitador entre comillas).
   **Ojo:** el heredoc de Bash se trunca cerca de 20 KB — no meter mas de ~45 lineas por comando.
   Quitar acentos/emojis al escribir (el shell rompe con backticks y comillas).
3. Correr `python bajar2.py` — descarga, deduplica por hash y escribe `_BANCO.csv`.
4. Cada 3-4 tandas: `python gen_galeria.py`.

## Reglas que NO hay que cambiar

- **Filtro de cuadrante:** el unico descarte es *posicion en mitad inferior + 21 dias o mas*.
  Los nuevos de abajo se guardan como `EN_PRUEBA` — son el material del re-analisis.
- **Paginas de bazar** (Trendora, Tu oferta Online, RyR, Megacomprasgt, Nova Market,
  Mundohome, Luceselect): venden de todo, no son del nicho. Solo superficie (5).
- `media_type=image_and_meme` (con `image` la biblioteca devuelve vacio).
- No recortar las URLs del CDN: la firma `oh` cubre todos los parametros, cualquier recorte da 403.
- Facebook devuelve **403 a curl**: el fetch tiene que salir del navegador.

## Re-analisis a 15 dias (aprox. 2026-09-01)

Volver a correr el barrido completo sobre las mismas 89 paginas y comparar por `ad_archive_id`:

- Un `EN_PRUEBA` que sigue activo y subio de posicion  → era bueno. Reclasificar a ganador.
- Un `EN_PRUEBA` que desaparecio                        → murio. Su tipo de anuncio pierde peso.
- Un `GANADOR_ESTABLECIDO` que desaparecio              → se fatigo; anotar cuantos dias duro.

Eso da **tasa de supervivencia por tipo de creativo** — medida, no inferida. Es el dato que
convierte el banco en criterio para lanzar.

## Objetivo final (lo define el operador)

Agrupar manualmente los creativos por **tipo de anuncio** y armar una estructura fija de tipos
validados para lanzar siempre sobre plantillas que ya pagaron su testeo en el mercado real.
La galeria permite filtrar por anunciante, escalado y antiguedad para hacer esa agrupacion.
