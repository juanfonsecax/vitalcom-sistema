# SPIKE F · `ads_creative_upload_media` en headless · 18-sep-2026

Pregunta: ¿el paso de subir la imagen de cada anuncio (`ads_creative_upload_media` con
`upload_source=LOCAL_FILE`, que emite `gen_publicacion.py`) funciona cuando lo corre la app, es decir,
Claude Code en modo `claude -p` sin pantalla?

**Respuesta: NO.** `LOCAL_FILE` no sirve en headless. Sin haber llamado a Meta.

## Evidencia

`app/spikes/spike_upload.py` — sesión `claude -p` con `--allowedTools ToolSearch` solamente (ninguna
herramienta de Meta autorizada: aunque el modelo quisiera llamarla, `dontAsk` la niega). Solo cargó la
definición de la herramienta. Crudo en `app/spikes/spikeF.jsonl`.

```
tool_use: ToolSearch select:mcp__claude_ai_META_MCP__ads_creative_upload_media
resultado: success | costo equivalente: US$0.49 (suscripción, no se cobra)
```

La definición que publica Meta, textual:

> Set `upload_source` to `LOCAL_FILE` only when the client supports interactive MCP Apps.
> If the client does not support interactive MCP Apps, use `URL` with `media_type` and a direct,
> publicly accessible `media_url` instead. […] The tool opens the upload app so the user can choose
> a file from their device.

`claude -p` no tiene dónde mostrar esa "upload app" ni quién elija el archivo. Además el `init` de la
misma corrida mostró los conectores que piden una pantalla (Gmail, Calendar) en `needs-auth`: la
sesión headless no abre nada interactivo.

No se hizo la llamada real con `LOCAL_FILE`: es una herramienta de escritura de Meta y requiere la
confirmación del operador. No hace falta para decidir: la propia herramienta dice que no aplica.

## Consecuencia

- Declarar `ads_creative_upload_media` tal como la emite hoy el generador en
  `herramientas_meta.escritura` **no** habilita publicar: el paso M3 la llamaría con `LOCAL_FILE` y
  quedaría esperando un archivo que nadie elige.
- La alternativa `URL` exige que cada imagen esté en una dirección pública de internet. La
  computadora del operador no lo es; habría que subir los creativos a un hosting público.
- La skill `publicar-meta` ya tiene un camino sin widget para las cuentas que no suben media local:
  **el operador sube la imagen a la biblioteca de Meta y el ejecutor lee el hash con
  `ads_get_ad_images`** (solo lectura). `gen_publicacion.py` hoy no lo emite como llamada: emite
  `LOCAL_FILE` para todas las cuentas y solo cambia la `nota`.
