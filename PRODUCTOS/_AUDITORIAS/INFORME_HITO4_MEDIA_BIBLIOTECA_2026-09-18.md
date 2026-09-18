# INFORME · HITO 4 · publicar con las imágenes subidas a mano · 18-sep-2026

Rama `feat/app-web` (worktree `../SISTEMA-app`). Sin tocar Meta, sin mergear, sin cambiar de rama la
carpeta real. Parte de `SPIKE_UPLOAD_MEDIA_2026-09-18.md` (LOCAL_FILE no sirve sin pantalla).

## La decisión (operador, 18-sep-2026)

El operador sube los creativos **a mano** a la biblioteca de imágenes de la cuenta y la app lee cada
`image_hash` con `ads_get_ad_images` (solo lectura). Nada se aloja en internet y no se usa `LOCAL_FILE`.
Es el camino que ya describían `MCP_PLAYBOOK.md` (Paso C/D) y la skill `publicar-meta` para las cuentas
sin subida local.

## Qué cambió

| Pieza | Cambio |
|---|---|
| `gen_publicacion.py` | Modo nuevo `--media biblioteca` con `--imagenes-antes` / `--imagenes-despues`. No emite `ads_creative_upload_media`: cada creativo lleva su hash **literal**. El nombre de cada pieza es el primer `[base]_V2`, `_V3`… que **no** existe en la biblioteca antes de subir (nunca un nombre viejo) y queda fijo después de subir. Lo que falta es un bloqueante de ámbito nuevo, `media`. El modo de siempre (`subida_local`, el de la skill interactiva) da el **mismo paquete byte a byte** (comparado contra la versión anterior en TINNIDROP F2, TURMERIC F1 y OVULOS_PURITY F1). |
| `test_gen_publicacion.py` | 6 pruebas nuevas (sin volcado · nombre libre `_V3` · todo subido · nombre repetido · la skill sigue igual · `--media` inválido). |
| Manifiesto v7 | `publicacion.paquete` corre en modo biblioteca. Ninguna acción declara `ads_creative_upload_media`; las tres `publicar` tienen `ads_get_ad_images` en lectura y las 4 de crear en escritura. **Siguen `habilitada: false`.** |
| `workflows.py` (`wf-2`) | Entre el paquete y la aprobación: leer la biblioteca → elegir nombres → **esperar al operador** (estado `ESPERA_MEDIA`, hasta 24 h) → leer de nuevo → regenerar. Si falta algo, lo vuelve a pedir diciendo qué (hasta 3 vueltas). La lectura recibe **una** herramienta de Meta: `ads_get_ad_images`. Las piezas se copian con su nombre exacto a `subir_a_meta/` dentro de la corrida. La orden a aprobar muestra qué archivo es cada hash. |
| API | `POST /api/trabajos/{id}/media/{vuelta}` («Ya las subí»); 409 si el trabajo no espera esa vuelta. |
| Pantalla Trabajos | Cuadro «Subí estas imágenes a Meta»: cuenta, carpeta lista para arrastrar (con copiar), cada archivo con su estado (falta subir · encontrada · hay dos con este nombre) y el botón. En la orden, la tabla archivo → nombre → hash. |

## Gate

- 19 `test_*.py` de `Ads/_TOOLS/` · `flujo.py --validar` · manifiesto v7 · guía madre · 5/5 productos ·
  `gen_grafo.py --comparar` (rutas muertas: ninguna)
- backend: **132 pruebas** (pytest, con `PYTHONIOENCODING=utf-8`; 9 nuevas en `test_meta.py`: el camino completo, nombre viejo, vuelve a pedir,
  nombre repetido, caducidad, lectura no guardada, 409, solo `ads_get_ad_images`, ninguna acción declara la subida)
- frontend: **22 pruebas** (2 nuevas) + build · Playwright: **7** · tipos regenerados desde el OpenAPI

Visto en pantalla con el servidor de demostración (Meta y Claude falsos): pide `PX_1_V3` porque ya había un
`PX_1_V2` viejo; con una sola subida vuelve a pedir la que falta; con las dos, muestra la orden con los hashes.

## Lo que no se midió todavía (se mide en la primera publicación real)

1. **Qué nombre guarda Meta al subir a mano** (¿con o sin `.png`?). El código acepta los dos. Si Meta le
   pusiera otro nombre, la app no la encuentra y lo dice: no adivina.
2. **Si `ads_get_ad_images` con `name=` busca por «contiene»**, como dice su descripción. La lectura de
   DESPUÉS busca además cada nombre exacto, así que encuentra lo subido en los dos casos. Si fuera exacto, la
   lectura de ANTES no vería un `_V2` viejo y podría elegir ese nombre: el control de «dos imágenes con el
   mismo nombre» lo frena antes de aprobar.
3. **Reintentar después de subir** pide subir otra vez con un nombre nuevo (`_V3`): es trabajo nuevo y la
   lectura de ANTES ya ve lo subido. Seguro, pero deja imágenes de más en la biblioteca.
