# FASE 2 images in the app

## Objective
The operator renders FASE 2 creatives by hand and loads each image in the app, on its concept card.
The image stays linked to its concept, its Meta ad and its results, and the app shows it wherever the
system talks about that creative.

## Problem
- Images downloaded from ChatGPT have arbitrary names; renaming by hand breaks the link to the row.
- The FASE 2 gallery shows only "✓ En disco", not the image.
- Results (engine orders, concept ranking) never show which image they refer to.

## Scope
- Per-concept upload on the FASE 2 gallery card: saves `Ads/<carpeta_media>/<archivo>` (the row's
  canonical name), validates PNG/JPEG, marks the row GENERADO through `marcar_generados.py`.
- Thumbnail on each gallery card, served by the existing media endpoint.
- Thumbnail next to results that reference a specific creative (only where the data links to one).

Out of scope: INBOX folder, automatic rendering, Meta publishing.

## Constraints
- Writers: CSV via real writer; product folder resolved via `_DIM_PRODUCTOS.csv`.
- Reuse the packshot upload path (`app/backend/vitalcom_app/subidas.py`, `api_fase1.py`).
- System Python for Ads/_TOOLS; backend venv for app/backend tests.

## TDD
Mode: on (session choice). Runners: backend `app/backend/.venv/Scripts/python -m pytest`,
frontend `vitest run` / `tsc -b` / `vite build` (app/frontend).

## Tasks
- [x] T1 Per-concept upload endpoint + gallery card upload — delegated (backend + frontend) — cb87d1f
- [x] T2 Thumbnail on each gallery card — delegated — 8add244
- [x] T3 Thumbnail next to creative-level results — delegated (map first; report if no link exists) — no change: no result in the app maps to one creative (see Progress)

## Acceptance
- Uploading on a card stores the file under its canonical name and the row becomes GENERADO.
- A non-image upload is rejected; a VIDEO row has no upload button.
- The card shows the image once on disk.
- Where a result names a creative/ad, its thumbnail is visible.

## Progress
- 2026-10-09: document created.
- T1 (cb87d1f): `Ads/_TOOLS/cargar_imagen_concepto.py` (row-canonical name, atomic write, converts to the row's type with Pillow when the upload differs, rejects VIDEO/PUBLICADO/non-image, marks only that row via `marcar_generados.marcar(creativo_id=)`), manifest action `producto.cargar_imagen_concepto`, endpoint `POST /api/productos/{pk}/conceptos/{creativo_id}/imagen`, card control gated by `puede_subir`.
- T2 (8add244): thumbnail with `?v=<mtime>` cache-buster and lightbox; media endpoint falls back to `MEDIA_<pk>` like the gallery.
- T3: engine orders (`_DECISIONES.json`) are per angle, never per creative; `_FACT_ENTREGA_ANUNCIO.csv` is not used by the app and none of its `ad_id` values match `_DIM_CREATIVOS.ad_id` (that field holds several ids joined by `;`). No result maps to exactly one creative, so nothing was added.
- Verification: vitest 195 passed; tsc -b and vite build clean; backend FASE 2 + acciones + fase1 tests 90 passed; Ads/_TOOLS tests for the new writer and marcar_generados pass (only the known WinError 6 wrapper failure).
