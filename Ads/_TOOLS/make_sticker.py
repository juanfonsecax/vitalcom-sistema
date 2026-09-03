import sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter
# Consola de Windows en cp1252/cp850: sin esto un print con acentos o simbolos
# revienta con UnicodeEncodeError y devuelve exit code 1 con el trabajo ya hecho
# (mismo bug que en gen_dashboard.py, 18-ago).
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass


# Genera el sticker de oferta: TEXTO BLANCO CON CONTORNO DE COLOR, SIN fondo.
# uso: python make_sticker.py "LINEA1" "LINEA2" COLOR salida.png
line1 = sys.argv[1] if len(sys.argv) > 1 else "2X1"
line2 = sys.argv[2] if len(sys.argv) > 2 else "SOLO HOY"
color_key = sys.argv[3] if len(sys.argv) > 3 else "rosa"
out = sys.argv[4] if len(sys.argv) > 4 else "sticker.png"

# color = COLOR DEL CONTORNO de las letras (el relleno siempre es blanco)
PALETAS = {
    "rosa":    (236, 44, 140),   # mujer / belleza
    "rojo":    (222, 32, 32),    # oferta general
    "azul":    (32, 108, 224),   # hombre / tech
    "verde":   (26, 160, 88),    # salud / natural
    "naranja": (240, 122, 12),   # energia / impulso
    "morado":  (140, 55, 210),   # premium / bienestar
}
outline = PALETAS.get(color_key, PALETAS["rosa"])

# Cadena de fuentes: Windows primero (equipo del operador), luego Linux (nube/sandbox).
_FONTS = [
    "C:/Windows/Fonts/ariblk.ttf",   # Arial Black (Windows)
    "C:/Windows/Fonts/arialbd.ttf",  # Arial Bold (Windows)
    "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",  # Arial-compatible (Linux)
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",           # fallback final (Linux)
]
font = None
for _f in _FONTS:
    try:
        font = ImageFont.truetype(_f, 96); break
    except Exception:
        continue
if font is None:
    raise SystemExit("No se encontró una fuente bold (ni Windows ni Linux).")

STROKE = 16      # grosor del contorno de color
MARGIN = 40      # espacio para contorno + sombra

tmp = Image.new("RGBA", (10, 10)); d = ImageDraw.Draw(tmp)
def measure(t):
    b = d.textbbox((0, 0), t, font=font, stroke_width=STROKE)
    return b[2]-b[0], b[3]-b[1]
w1, h1 = measure(line1); w2, h2 = measure(line2)
gap = 6
text_w = max(w1, w2); text_h = h1 + gap + h2
W = text_w + MARGIN*2
H = text_h + MARGIN*2
cx = W // 2
y1 = MARGIN
y2 = y1 + h1 + gap

img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

# sombra suave (legibilidad sobre cualquier fondo)
sh = Image.new("RGBA", (W, H), (0, 0, 0, 0)); sd = ImageDraw.Draw(sh)
for (t, y) in ((line1, y1), (line2, y2)):
    sd.text((cx+4, y+6), t, font=font, fill=(0, 0, 0, 150),
            stroke_width=STROKE, stroke_fill=(0, 0, 0, 150), anchor="ma")
sh = sh.filter(ImageFilter.GaussianBlur(9))
img = Image.alpha_composite(img, sh)
draw = ImageDraw.Draw(img)

# texto: relleno BLANCO + contorno de color (SIN caja de fondo)
for (t, y) in ((line1, y1), (line2, y2)):
    draw.text((cx, y), t, font=font, fill=(255, 255, 255, 255),
              stroke_width=STROKE, stroke_fill=outline+(255,), anchor="ma")

img.save(out)
print(f"OK sticker {W}x{H} -> {out}  contorno={color_key}")
