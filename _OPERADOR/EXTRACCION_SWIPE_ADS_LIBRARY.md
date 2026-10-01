# Extracción del subsistema de scrapeo de Meta Ads Library

> Documento de traspaso. Primero se construye el sistema nuevo con esto; cuando funcione, se
> extrae de SISTEMA. Fecha del relevamiento: 2026-09-28.

---

## 1. Qué es hoy, en una línea

Un pipeline que **cosecha anuncios ganadores de la Biblioteca de Anuncios de Meta**, los
**clasifica** en un vocabulario de conceptos y los **destila** en plantillas reutilizables
(111 fichas → 22 blueprints canónicos) que FASE 2 usa para generar los prompts de imagen de
cada producto.

Son tres capas, y la frontera de la extracción pasa entre la 2 y la 3:

```
CAPA 1 — COSECHA          CAPA 2 — CLASIFICACIÓN         CAPA 3 — CONSUMO (se queda)
_EXTRACTOR.js  ─┐         clasificar_conceptos.py        seleccionar_canonicos.py
bajar2.py       ├─► _BANCO.csv ─► etiquetado manual ─►   armar_prompts_fase2.py
dedup.py        │   _IMG/ (41 MB)   escribir_fichas.py    skill generar-conceptos
Apify Módulo B ─┘                   agrupar_canonicos.py  atribuir.py · ETAPA-9/10
                                    ─► FICHAS/ + CANONICOS/  check_huella.py
```

---

## 2. Cómo se cosecha (Capa 1)

Hay tres caminos. Solo el B construyó el banco.

### A — Manual (sin código)
Por producto nuevo el operador baja 10 videos de Ads Library + 10 de TikTok a
`Ads/1.1 Videos/[PRODUCTO]/` y los transcribe en Gemini con `Ads/Prompt-Gemini.txt` →
`Ads/1.2 Transcripcion videos/[PRODUCTO]/*.txt`. Protocolo: `DOCTRINA/ETAPA-RECOLECCION.md`.
Alimenta FASE 1 (`etapa-0`, `etapa-2`). **No es parte del scraper**: se queda.

### B — Scraper de consola en navegador (construyó el banco)
1. Se abre Ads Library en el navegador con sesión de Facebook (sin cookie, Facebook devuelve 403).
2. Se ejecuta `Ads/_SWIPE/_EXTRACTOR.js` (61 líneas) con `javascript_tool`, pasándole `page_id`s.
3. Hace `fetch()` a
   `facebook.com/ads/library/?active_status=active&ad_type=all&media_type=image_and_meme&sort_data[mode]=total_impressions&view_all_page_id=<PID>`,
   busca en el HTML el JSON embebido `search_results_connection` y extrae por anuncio:
   `ad_archive_id`, `collation_count` (réplicas), `start_date` → días corriendo, `page_name`,
   `title`, `link_description`, `cta_text`, `link_url`, `body.text` y la URL de la primera imagen.
4. Comprime la salida en texto separado por `|` (`window.__M`) → `Ads/_SWIPE/_RAW/masivo/mNN.txt`.
5. `python Ads/_SWIPE/bajar2.py` reconstruye la URL firmada del CDN (la firma `oh` cubre la URL
   entera: no se puede truncar), baja la imagen, deduplica por MD5, asigna `cuadrante` y
   agrega filas a `_BANCO.csv`.
6. `gen_galeria.py` / `gen_winners.py` regeneran las galerías HTML para revisión visual.

### C — Apify (Módulo B de `DOCTRINA/ETAPA-RESEARCH.md`)
Código Python **inline en el doc**, no en un script. Busca por **nombre exacto del producto**
con el actor `apify/facebook-ads-scraper`, lee `ad_creative_bodies` (máx. 50 anuncios, 300
caracteres c/u) y clasifica ángulos como VALIDADO/VIRGEN. Token en la variable de entorno
`APIFY_TOKEN` (nunca en el repo). Lo invocan `etapa-1b` y `fase-1-angulos` como chequeo de
saturación. Solo el resumen clasificado entra a `etapa-2` (`<datos_saturacion>`).

### Criterio de "ganador"
- **Descubrir páginas:** las que publican anuncios nuevos repetidamente (`_PAGINAS.csv.n_apariciones`).
- **Cosechar dentro de la página:** orden por `total_impressions` (es un RANKING; Meta no expone
  impresiones absolutas de anuncios comerciales). Top 8–10 sin filtro + top 5 en 30 días.
- **Descartar** solo lo viejo y abajo: mitad inferior del ranking **y** ≥ 21 días.
- **Réplicas** (misma imagen MD5 en varios `ad_archive_id`) = proxy de gasto/escalado.
- **Score** (`gen_galeria.py`): `escalado*20 + (15 si dias>=21) + velocidad`,
  `velocidad = posicion * 30 / max(dias, 7)` (piso de 7 días para que lo recién nacido no domine).

### Qué NO se baja
Video, landing, comentarios (salvo el copy del Módulo Apify). La imagen sale como máximo en
600×600, que es lo que sirve Ads Library. No hay transcripción de lo scrapeado.

---

## 3. Cómo se clasifica (Capa 2)

```
_BANCO.csv (373) + _ADS.csv (226, legado)
  → clasificar_conceptos.py        pre-clasificación por regex del copy (_PRECLASIFICACION.csv, 598)
                                   solo 5 de 10 conceptos tienen firma textual confiable
  → etiquetado manual               estrellas en la galería → _ETIQUETAS_MANUALES.csv (112)
                                    _codificar.py: 36 piezas × 36 elementos → _ELEMENTOS.csv
                                    (observación humana: NO regenerar automáticamente)
  → _CLASIF_FAVORITOS.csv (111)     los favoritos con su concepto final
  → _BLUEPRINTS/_datos/tandaNN.py   análisis visual manual, de a 10 piezas
  → escribir_fichas.py              → FICHAS/F001…F111.json
  → agrupar_canonicos.py            → CANONICOS/CN01…CN22.json (+ escribe canonico_id en las fichas)
```

### Dos vocabularios, dos capas
| Vocabulario | Valores | Para qué | Dueño |
|---|---|---|---|
| `concepto_key` | 8: `C1_OFERTA, C2_BENEFICIOS, C3_SINTOMA, C4_TRANSFORMACION, C5_PRUEBA, C7_DESEO, C8_PROGRESION, C9_COMPARACION` (+ `SIN_CLASIFICAR` legado; `C6_UNBOXING` retirado → C5) | **Medir**: columna de las tablas de resultados | `Ads/_SWIPE/_CATALOGO_CONCEPTOS.md` §8 (espejo en `DOCTRINA/DATA_PLAYBOOK.md` §1) |
| `canonico_id` | 22: `CN01_ANTES_DESPUES` … `CN22_ESCENA_DE_USO` | **Producir**: la estructura que se llena y se renderiza | `Ads/_SWIPE/_BLUEPRINTS/CANONICOS/` |

### Rotación de FASE 2
10 ejecuciones sobre 6 `concepto_key`: `C2` (control, siempre) + `C1` (BOFU, siempre) + `C4` +
`C8` + `C5` + un 6º rotativo (`C3` si es categoría dolor, `C7` si es estética). `C9` en reserva.

---

## 4. Esquemas de datos

### Cosecha (se van)
- **`_BANCO.csv`** (canónico): `ad_archive_id,page_id,anunciante,pos,total_pos,cuadrante,dias_corriendo,replicas,archivo,titulo,descripcion,cta,destino,texto_principal,fecha_cosecha`
  — `cuadrante` ∈ `GANADOR_ESTABLECIDO | WINNER_CALIENTE | EN_PRUEBA` (`DESCARTE_VIEJO_ABAJO` se filtra).
- **`_ADS.csv`** (legado): `ad_archive_id,page_id,anunciante,rank_impresiones,dias_corriendo,collation_count,velocidad,ads_activos_pagina,ad_mas_viejo_pagina,archivo,copy,fecha_cosecha,replicas_misma_imagen`
- **`_PAGINAS.csv`** (89): `page_id,nombre,nicho,pais_original,carpeta_origen,n_apariciones,url_adlibrary,n_ads_activos,ad_mas_antiguo_dias,fecha_scrape,estado,notas` — `estado` ∈ `COSECHADA|OBSERVAR|VACIA|MUERTA`.
- **`_COPIES.csv`**: `ad_archive_id,pagina_real,replicas,dias,pos_grupo,titulo,descripcion,cta,destino,texto_principal`
- **`_RANKING_CUENTAS.csv`**: `page_id,anunciante,ads_activos_reales,creativos_capturados,instancias_meta_cc,intensidad_duplicacion,dias_ad_mas_viejo,pct_catalogo,veredicto`
- **`_SELECCION_EXTRACCION.csv`**: `n,ad_archive_id,anunciante,dias,replicas,score,archivo`

### Clasificación (se van)
- **`_PRECLASIFICACION.csv`**: `ad_archive_id,anunciante,archivo,dias_corriendo,replicas,es_catalogo,concepto_auto,confianza,texto_muestra`
- **`_ETIQUETAS_MANUALES.csv`**: `ad_archive_id,anunciante,archivo,favorito,concepto_manual,concepto_auto,es_catalogo,dias,replicas`
- **`_CLASIF_FAVORITOS.csv`**: `archivo,concepto_final,concepto_crudo,dias,replicas,anunciante`
- **`_ELEMENTOS.csv`**: 36 columnas binarias/categóricas de elementos visuales (precio tachado, sello, antes/después, rostro, etc.).

### El producto destilado (es el CONTRATO entre los dos sistemas)
- **Ficha `FICHAS/F0xx.json`** (orden de claves fijo, ver `_BLUEPRINTS/_ESQUEMA_FICHA.md`):
  `ficha_id, schema_version, origen{archivo, anunciante, ad_archive_id, dias_activo, replicas, score, en_banco_creativos, mercado}, clasificacion{estetica, formato, densidad, espacio_libre_objetivo, nivel_conciencia, rol_embudo, concepto_key, variante_operador}, dispositivo_dominante, lectura_estrategica, fondo, paleta, sistema_tipografico, [condiciones_de_captura], zonas{…{{PLACEHOLDER}}…}, secuencia_lectura, reglas_duras, variables_requeridas, cuando_usar, cuando_no_usar, sellos_y_claims_observados, canonico_id, blueprint_equivalente`
- **Canónico `CANONICOS/CNxx.json`**:
  `canonico_id, schema_version, nombre, dispositivo_canonico, cuando_elegirlo, ejes_de_variacion[], n_miembros, ficha_referencia, score_referencia, perfil{concepto_key, rol_embudo, estetica, formato, densidad, nivel_conciencia_rango}, contrato_variables[], variables_observadas{nucleo, recurrentes}`

---

## 5. Quién consume qué (lo que NO se puede romper)

| Consumidor (se queda en SISTEMA) | Depende de |
|---|---|
| `Ads/_TOOLS/seleccionar_canonicos.py` | Lee TODO `_SWIPE/_BLUEPRINTS/CANONICOS/*.json` (ruta fija, línea 34) |
| `Ads/_TOOLS/armar_prompts_fase2.py` | `FICHAS/<ficha_referencia>.json` (línea 312) → `origen.archivo` → **la imagen del competidor** en `Ads/_SWIPE/` (línea 320) |
| skill `generar-conceptos` | FICHAS, CANONICOS (vía el selector), `_CATALOGO_CONCEPTOS.md` PARTE III |
| `Ads/_TOOLS/check_huella.py` | **`Ads/_SWIPE/_IMG/` entero** (41 MB): compara hash perceptual del creativo nuevo contra los anuncios de la competencia antes de subirlo |
| `Ads/_TOOLS/atribuir.py`, `etapa-9`, `etapa-10` | Columnas `concepto_key` y `canonico_id` en `_DIM_CONJUNTOS.csv` / `_DIM_CREATIVOS.csv` / `_DIM_ANUNCIOS.csv` |
| `etapa-2`, `DATA_PLAYBOOK.md` §1 | Vocabulario de `concepto_key` (C2 fijo en FASE 1) |
| `etapa-1b`, `fase-1-angulos` | Módulo Apify para saturación |

---

## 6. Frontera propuesta

### Se va al sistema nuevo
- `Ads/_SWIPE/_EXTRACTOR.js`, `bajar2.py`, `dedup.py`, `integrar_copies.py`, `gen_galeria.py`, `gen_winners.py`
- `Ads/_SWIPE/clasificar_conceptos.py`, `_codificar.py`
- `Ads/_TOOLS/escribir_fichas.py`, `Ads/_TOOLS/agrupar_canonicos.py`, `Ads/_SWIPE/_BLUEPRINTS/_datos/`
- Todos los CSV de §4 "Cosecha" y "Clasificación", `_RAW/`, `_IMG/`
- Galerías HTML, `_METODO.md`, `_HANDOFF*.md`, `_AUDITORIA_2026-08-18.md`, `analisis-ad-2026-08-18.md`, `_PENDIENTES/_PROCESADOS/_VISTAS/_LINKS_TANDAS.txt`
- El código del Módulo B de Apify, convertido en script real (hoy vive como texto en un .md)
- `check_huella.py` + el banco de imágenes (o ver alternativa en §7)

### Se archiva, no se migra (muerto o superado)
- `bajar.py` + `_ADS.csv` (legado; `bajar2.py` + `_BANCO.csv` lo reemplazan)
- `_ESTRATEGIA_CONCEPTOS.md` (hipótesis superada por el catálogo)
- `_BLUEPRINTS/blueprint_A…D.json` y `LLENO_T01_*.json` (predecesores de los 22 canónicos)
- `_RAW/1077522192100287.json` (huérfano)

### Se queda en SISTEMA — el "paquete de referencias"
Solo lo que producción lee:
1. `CANONICOS/*.json` (22) — el selector los necesita todos.
2. `FICHAS/*.json` (111) — el generador lee la de referencia de cada canónico.
3. Las imágenes que referencian las fichas vía `origen.archivo` (subconjunto de `_IMG/`, no los 41 MB).
4. El vocabulario de `concepto_key` y la rotación de FASE 2 (PARTE III del catálogo), no las 460 líneas enteras.
5. `seleccionar_canonicos.py`, `armar_prompts_fase2.py`, `atribuir.py`, skill `generar-conceptos`.

---

## 7. Contrato entre los dos sistemas

El sistema nuevo **publica**; SISTEMA **consume**. Nunca al revés.

```
Sistema nuevo  ──exporta──►  SISTEMA/Ads/_REFERENCIAS/
                              ├── VERSION                (entero; sube en cada export)
                              ├── CANONICOS/CN01…CN22.json
                              ├── FICHAS/F001…F111.json
                              ├── IMG/…                  (solo las que citan las fichas)
                              ├── VOCABULARIO.csv        (concepto_key, nombre, rol_embudo, firma, en_rotacion)
                              └── HUELLAS.csv            (archivo, ahash, dhash, phash)
```

Decisiones que el contrato fija:
- **`HUELLAS.csv` reemplaza a `_IMG/` para `check_huella.py`**: el sistema nuevo precalcula los
  tres hashes de cada imagen cosechada; SISTEMA compara contra el CSV. Así los 41 MB se van y la
  protección anti-duplicado se queda.
- **Los esquemas de §4 (ficha y canónico) no cambian** en la migración. Si cambian, sube `schema_version`.
- **Los vocabularios son cerrados**: el sistema nuevo no puede inventar un `concepto_key` ni un
  `canonico_id` sin que SISTEMA lo acepte (romperíamos las columnas históricas de `_DIM_*`).
- Las rutas fijas a mover en SISTEMA: `seleccionar_canonicos.py:34`, `armar_prompts_fase2.py:39,312,320`,
  `check_huella.py:152`.

---

## 8. Plan de extracción

1. **Construir allá** (sin tocar SISTEMA): copiar lo de §6 "Se va", convertir el Módulo Apify en
   script, y escribir el exportador del paquete de §7.
2. **Tests antes de mover** — hoy el único test es `test_armar_prompts_fase2.py`. Faltan:
   `seleccionar_canonicos.py` (las compuertas de aptitud), el exportador, y un test de contrato
   que valide el esquema de fichas/canónicos del paquete.
3. **Primer export** a `SISTEMA/Ads/_REFERENCIAS/` y apuntar las 4 rutas fijas de §7 a esa carpeta.
4. **Verificar en SISTEMA**: correr `test_armar_prompts_fase2.py`, generar los prompts de FASE 2 de
   un producto real y comparar contra la salida actual (deben ser idénticos).
5. **Recién ahí borrar** `Ads/_SWIPE/` de SISTEMA y actualizar el puntero del CLAUDE.md
   (`_CATALOGO_CONCEPTOS.md` → vocabulario del paquete) y `DATA_PLAYBOOK.md` §1.

---

## 9. Pendientes conocidos

- El re-análisis planeado para ~2026-09-01 ("¿sobrevive C8_PROGRESION?") no tiene output en el
  repo: probablemente nunca corrió. Es la primera tarea natural del sistema nuevo.
- `_BANCO.csv` tiene una sola `fecha_cosecha`: no hay historia para medir supervivencia de anuncios.
  El sistema nuevo debería cosechar con fecha repetida para eso.
- La skill `analizador-creativos` (análisis de UN anuncio, usa el MCP `ads_library_search`) es otra
  cosa: no forma parte de este pipeline.
