# LAVADO DE VIDEOS — anti-huella + sticker + renombrado por ángulo

> **Qué es esto:** el detalle del **PASO 1.5** del flujo de FASE 1. Corre SIEMPRE, para todo producto, con o sin MCP. **Salió de `CLAUDE.md` el 31-jul-2026** (refactor); allá quedó el comando y las 3 reglas operativas.
>
> **Quién lo ejecuta:** el **orquestador mismo**, vía Bash — `etapa-0` solo tiene tools `Read/Glob/Grep` y no puede escribir archivos.

---

## POR QUÉ SE LAVA (no es opcional)

Los videos vienen de contenido de terceros (biblioteca/competencia). Meta detecta el reuso por **huella de contenido** (perceptual hashing / Rights Manager), **no por metadata** — y aplica **baneo silencioso**: sube los CPMs sin avisar (la dinámica Andrómeda). Subir el video crudo es pagar más caro por el mismo alcance, sin que nada te avise.

**Borrar la metadata SOLO no basta.** El lavado que sí rompe la huella:
- crop 4%
- ajuste de contraste / saturación / hue
- re-encode de video **y** audio
- metadata del origen borrada
- **variación única por video** — cada uno con parámetros distintos, así los 6 creativos nunca son idénticos entre sí (otra regla Andrómeda)

Encima se agrega el **sticker de oferta**: texto blanco con contorno de color, sin fondo, centrado, con fade in/out, pulsando desde la mitad del video. Refuerza la variación y empuja el CTR.

---

## CÓMO SE EJECUTA

El orquestador arma un manifiesto (una línea por video: `N⇥ANGULO⇥RUTA_ORIGEN`, ruta en formato `C:/…`) y corre:

```bash
bash "Ads/_TOOLS/lavar_videos.sh" "[PRODUCTO]" [OFERTA] [COLOR] "Ads/MEDIA_[PRODUCTO]" [MANIFEST]
```

**OFERTA** = `2X1` (sticker "2X1 / SOLO HOY") o `NORMAL` (sticker "MEGA OFERTA / SOLO HOY"). El operador lo indica al arrancar; si no lo dice, default `NORMAL`.

**COLOR = automático** según la FanPage/categoría (la resuelve el orquestador con `<pagina_asignada>` de `etapa-fanpage`, o la categoría del producto):

| Categoría | Color |
|---|---|
| belleza / mujer | `rosa` |
| salud / natural / suplemento | `verde` |
| hombre / tech / gadget | `azul` |
| energía / impulso | `naranja` |
| premium / bienestar | `morado` |
| oferta general / no encaja | `rojo` |

El operador puede sobreescribir el color si lo pide explícito.

> 🔴 **ESTE MAPA ES SOLO DEL STICKER DEL VIDEO. NO ES EL COLOR DEL PRODUCTO.**
> Bug real (21-ago, TINNIDROP): el `verde` de la categoría *salud/natural* se
> copió a los prompts de imagen como si fuera el color del envase, y la IA
> **repintó de verde un frasco que es azul**. Ocho creativos salieron con un
> producto que no existe; uno llegó a pautarse.
> **El color del PRODUCTO sale siempre de su FOTO REAL** — nunca de esta tabla,
> nunca de la categoría, nunca de la FanPage. Esta tabla solo tiñe el sticker
> de oferta que se le pega al video para el lavado anti-copyright.

---

## REGLAS DEL PASO

- **Copiar/lavar, nunca mover in situ.** El original numerado en `Ads/1.1 Videos/[PRODUCTO]/` queda **intacto** — sigue emparejado 1:1 con su transcripción en `Ads/1.2 Transcripcion videos/[PRODUCTO]/` para cualquier re-análisis futuro de `etapa-0`. Lo lavado es una copia nueva en `Ads/MEDIA_[PRODUCTO]/`, nombrada `[PRODUCTO]_[N]_[ANGULO].mp4` (N = conjunto 1-6, ANGULO = slug corto).
- **Los ángulos vírgenes sin video** (creativo = IMAGEN) reservan su slot en la misma carpeta: `[PRODUCTO]_[N]_[ANGULO].jpg`, una vez `etapa-4` genera la imagen (Prompt Maestro). Las imágenes no pasan por el lavado (se generan limpias desde cero).
- **No depende del MCP.** Corre para todo producto, con o sin cuenta/campaña asignada — nunca esperar a que exista `MCP_ACCOUNT_ID`. Si se espera, `1_HACER_MANUAL.txt` y `2_DATA_PRODUCTO.txt` terminan referenciando los nombres numerados crudos de `Ads/1.1 Videos/` en vez del nombre por ángulo (bug detectado y corregido en VITAMINA D3+K2, 2026-06-28).

---

## HERRAMIENTAS

- `Ads/_TOOLS/lavar_videos.sh` — el proceso
- `Ads/_TOOLS/make_sticker.py` — el sticker

Requieren `ffmpeg`/`ffprobe` + `python` con Pillow (ya instalados en el equipo del operador).
