#!/usr/bin/env bash
# ============================================================================
# lavar_videos.sh  —  LAVADO ANTI-COPYRIGHT + STICKER DE OFERTA (VITALCOM)
# ----------------------------------------------------------------------------
# Procesa los videos seleccionados de un producto para que Meta NO los detecte
# como contenido reusado (evita el "baneo silencioso" de Andromeda que sube CPMs).
# Cada video sale con: metadata borrada + re-encode + variacion visual unica
# (crop/hue/contraste distintos por video) + sticker de oferta con fade in/out.
#
# USO:
#   ./lavar_videos.sh "PRODUCTO" OFERTA COLOR "OUTDIR" "MANIFEST"
#
#   PRODUCTO  nombre del producto (ej: "NUSAVA B12")
#   OFERTA    2X1 | NORMAL        (define el texto del sticker)
#   COLOR     rosa|rojo|azul|verde|naranja|morado  (auto lo resuelve el orquestador)
#   OUTDIR    carpeta destino, ej: ".../Ads/MEDIA_NUSAVA B12"
#   MANIFEST  archivo de texto, una linea por video:  N<TAB>ANGULO<TAB>RUTA_ORIGEN
#             (RUTA_ORIGEN en formato C:/... con barras normales)
#
# Requisitos: ffmpeg, ffprobe, python con Pillow (todo ya instalado en el equipo).
# ============================================================================
set -euo pipefail

PRODUCTO="${1:?falta PRODUCTO}"
OFERTA="${2:?falta OFERTA (2X1|NORMAL)}"
COLOR="${3:?falta COLOR}"
OUTDIR="${4:?falta OUTDIR}"
MANIFEST="${5:?falta MANIFEST}"

TOOLS="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
mkdir -p "$OUTDIR"

# slug del producto para el nombre de archivo (sin espacios, mayusculas)
SLUG="$(echo "$PRODUCTO" | tr '[:lower:]' '[:upper:]' | tr -cd '[:alnum:]')"

# texto del sticker segun la oferta
if [ "$OFERTA" = "2X1" ]; then L1="2X1"; L2="SOLO HOY"; else L1="MEGA OFERTA"; L2="SOLO HOY"; fi

# genera el sticker UNA vez (mismo para los 6 videos)
STICKER="$OUTDIR/.sticker_${COLOR}.png"
python "$TOOLS/make_sticker.py" "$L1" "$L2" "$COLOR" "$STICKER" >/dev/null

echo "== LAVADO: $PRODUCTO | oferta=$OFERTA | color=$COLOR =="

# helper: numero aleatorio flotante en un rango
rnd(){ awk -v a="$1" -v b="$2" -v s="$RANDOM$RANDOM" 'BEGIN{srand(s);printf "%.3f",a+rand()*(b-a)}'; }

while IFS=$'\t' read -r N ANGULO SRC || [ -n "${N:-}" ]; do
  [ -z "${N// }" ] && continue
  case "$N" in \#*) continue;; esac
  if [ ! -f "$SRC" ]; then echo "  !! no existe: $SRC (conjunto $N) -- SALTADO"; continue; fi

  # mitad del video para arrancar el sticker
  DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$SRC")
  MID=$(awk -v d="$DUR" 'BEGIN{printf "%.2f", d/2}')

  # variacion visual UNICA por video (rompe huella + evita duplicado propio)
  CROP=$(rnd 0.955 0.968)
  HUE=$(rnd 2 6)
  CON=$(rnd 1.030 1.060)
  SAT=$(rnd 1.040 1.090)
  BRI=$(rnd -0.004 0.014)

  OUT="$OUTDIR/${SLUG}_${N}_${ANGULO}.mp4"
  FILT="$OUTDIR/.filter_${N}.txt"

  # fade repetido: 0.35s in / 3s hold / 0.35s out, periodo 13s, desde MID
  cat > "$FILT" <<EOF
[0:v]crop=iw*${CROP}:ih*${CROP},scale=720:1280,eq=contrast=${CON}:saturation=${SAT}:brightness=${BRI},hue=h=${HUE}[base];[1:v]scale=360:-1,format=rgba,geq=r='r(X,Y)':g='g(X,Y)':b='b(X,Y)':a='alpha(X,Y)*gte(T,${MID})*if(lt(mod(T-${MID},13),0.35),mod(T-${MID},13)/0.35,if(lt(mod(T-${MID},13),3),1,if(lt(mod(T-${MID},13),3.35),(3.35-mod(T-${MID},13))/0.35,0)))'[stk];[base][stk]overlay=x=(W-w)/2:y=(H-h)*0.50[v]
EOF

  ffmpeg -y -hide_banner -loglevel error \
    -i "$SRC" -framerate 30 -loop 1 -i "$STICKER" \
    -filter_complex_script "$FILT" -map "[v]" -map 0:a \
    -c:v libx264 -crf 20 -preset medium -pix_fmt yuv420p -c:a aac -b:a 128k -shortest \
    -map_metadata -1 -map_chapters -1 -metadata:s:v:0 handler_name= -metadata:s:a:0 handler_name= \
    -fflags +bitexact -flags:v +bitexact -flags:a +bitexact -movflags +faststart \
    "$OUT"
  rm -f "$FILT"
  echo "  OK conjunto $N -> ${SLUG}_${N}_${ANGULO}.mp4  (crop=$CROP hue=$HUE sat=$SAT)"
done < "$MANIFEST"

rm -f "$STICKER"
echo "== LISTO. Videos lavados en: $OUTDIR =="
