# -*- coding: utf-8 -*-
"""check_huella.py — antes de subir un creativo, verifica que NO se parezca a un anuncio
vivo de la competencia.

POR QUE EXISTE
Meta detecta el reuso por HUELLA DE CONTENIDO, no por estructura (ver Ads/_TOOLS/LAVADO.md).
Un creativo generado a partir de un anuncio de la competencia puede conservar bastante huella
como para que Meta lo lea como duplicado de un ad que ya corre en el mismo mercado. No avisa:
sube el CPM en silencio. Este script pone un numero donde antes habia solo criterio.

COMO SE USA
    python Ads/_TOOLS/check_huella.py <imagen_o_carpeta> [--banco Ads/_SWIPE/_IMG] [--top 5]

QUE MIDE
Tres huellas complementarias, porque cada una atrapa un tipo distinto de parecido:
  · aHash — brillo por zona: atrapa la MISMA foto reencuadrada o recoloreada
  · dHash — gradientes: atrapa la misma COMPOSICION aunque cambien los colores
  · pHash — frecuencias (DCT): la mas robusta a reescalado, compresion y retoque
La distancia es de Hamming sobre 64 bits: 0 = identicas, 64 = opuestas.

UMBRALES (calibrados sobre el banco: ver --calibrar)
  <= 10  ROJO    practicamente la misma imagen. NO SUBIR.
  11-18  AMARILLO misma composicion con relleno distinto. Riesgoso si el original esta VIVO.
  >= 19  VERDE   suficientemente distinta.

Sin dependencias externas: solo Pillow (ya instalado) y la libreria estandar.
"""
import os, sys, argparse

try:
    from PIL import Image
except ImportError:
    sys.exit("Falta Pillow.  Instalar con:  pip install pillow")

EXT = (".jpg", ".jpeg", ".png", ".webp")


# ---------- huellas ----------
def _gris(p, w, h):
    return list(Image.open(p).convert("L").resize((w, h), Image.LANCZOS).getdata())


def ahash(p):
    px = _gris(p, 8, 8)
    m = sum(px) / len(px)
    return sum(1 << i for i, v in enumerate(px) if v > m)


def dhash(p):
    px = _gris(p, 9, 8)
    bits, i = 0, 0
    for y in range(8):
        fila = px[y * 9:(y + 1) * 9]
        for x in range(8):
            if fila[x] > fila[x + 1]:
                bits |= 1 << i
            i += 1
    return bits


def phash(p):
    """DCT-II 2D sobre 32x32, se queda con el bloque 8x8 de baja frecuencia."""
    import math
    N = 32
    px = _gris(p, N, N)
    mat = [px[r * N:(r + 1) * N] for r in range(N)]
    cos = [[math.cos((2 * x + 1) * u * math.pi / (2 * N)) for x in range(N)] for u in range(N)]
    # filas y luego columnas (DCT separable)
    tmp = [[sum(mat[r][x] * cos[u][x] for x in range(N)) for u in range(8)] for r in range(N)]
    dct = [[sum(tmp[r][u] * cos[v][r] for r in range(N)) for u in range(8)] for v in range(8)]
    vals = [dct[v][u] for v in range(8) for u in range(8)]
    med = sorted(vals[1:])[len(vals[1:]) // 2]          # se ignora el DC (vals[0])
    return sum(1 << i for i, v in enumerate(vals) if v > med)


def dist(a, b):
    return bin(a ^ b).count("1")


def huellas(p):
    return (ahash(p), dhash(p), phash(p))


# ---------- banco ----------
def cargar_banco(raiz):
    banco = []
    for root, _, fs in os.walk(raiz):
        for f in fs:
            if f.lower().endswith(EXT):
                p = os.path.join(root, f)
                try:
                    banco.append((p, huellas(p)))
                except Exception:
                    pass
    return banco


def veredicto(d):
    if d <= 10:
        return "ROJO", "practicamente la misma imagen - NO SUBIR"
    if d <= 18:
        return "AMARILLO", "misma composicion, relleno distinto - riesgoso si el original esta VIVO"
    return "VERDE", "suficientemente distinta"


def revisar(img, banco, top):
    h = huellas(img)
    res = []
    for p, hb in banco:
        if os.path.abspath(p) == os.path.abspath(img):
            continue
        da, dd, dp = (dist(h[i], hb[i]) for i in range(3))
        res.append((min(da, dd, dp), da, dd, dp, p))
    res.sort()
    print("\n" + "=" * 78)
    print("CREATIVO: %s" % img)
    if not res:
        print("  banco vacio - nada con que comparar")
        return None
    peor = res[0]
    v, msg = veredicto(peor[0])
    marca = {"ROJO": "[X]", "AMARILLO": "[!]", "VERDE": "[OK]"}[v]
    print("  %s %s  (distancia minima %d)  %s" % (marca, v, peor[0], msg))
    print("\n  los %d mas parecidos del banco:" % min(top, len(res)))
    print("  %-6s %-5s %-5s %-5s  %s" % ("min", "aHash", "dHash", "pHash", "archivo"))
    for mn, da, dd, dp, p in res[:top]:
        print("  %-6d %-5d %-5d %-5d  %s" % (mn, da, dd, dp, os.path.relpath(p)))
    return v


def calibrar(banco):
    """Distancias entre pares del propio banco: da el piso de 'distinto de verdad'."""
    import random
    random.seed(7)
    pares = []
    n = len(banco)
    for _ in range(min(4000, n * (n - 1) // 2)):
        a, b = random.sample(range(n), 2)
        pares.append(min(dist(banco[a][1][i], banco[b][1][i]) for i in range(3)))
    pares.sort()
    print("\nCALIBRACION sobre %d imagenes del banco (%d pares al azar)" % (n, len(pares)))
    for q in (1, 5, 25, 50):
        print("  percentil %2d%%: distancia %d" % (q, pares[int(len(pares) * q / 100)]))
    print("\n  Dos creativos DISTINTOS del mercado real casi nunca bajan del percentil 1.")
    print("  Si tu creativo queda por debajo de ese numero, se parece mas a la competencia")
    print("  de lo que dos anuncios distintos se parecen entre si.")


def main():
    ap = argparse.ArgumentParser(description="Verifica que un creativo no comparta huella con la competencia.")
    ap.add_argument("objetivo", nargs="?", help="imagen o carpeta a revisar")
    ap.add_argument("--banco", default="Ads/_SWIPE/_IMG", help="carpeta del swipe file")
    ap.add_argument("--top", type=int, default=5)
    ap.add_argument("--calibrar", action="store_true", help="mide el piso de distancia del banco y sale")
    a = ap.parse_args()

    if not os.path.isdir(a.banco):
        sys.exit("No existe el banco: %s" % a.banco)
    print("cargando banco desde %s ..." % a.banco)
    banco = cargar_banco(a.banco)
    print("  %d imagenes indexadas" % len(banco))

    if a.calibrar:
        calibrar(banco)
        return
    if not a.objetivo:
        ap.error("falta la imagen o carpeta a revisar")

    objs = []
    if os.path.isdir(a.objetivo):
        for f in sorted(os.listdir(a.objetivo)):
            if f.lower().endswith(EXT):
                objs.append(os.path.join(a.objetivo, f))
    else:
        objs = [a.objetivo]

    vs = [revisar(o, banco, a.top) for o in objs]
    rojos = sum(1 for v in vs if v == "ROJO")
    amar = sum(1 for v in vs if v == "AMARILLO")
    print("\n" + "=" * 78)
    print("RESUMEN: %d revisados - %d ROJO - %d AMARILLO - %d VERDE"
          % (len(vs), rojos, amar, len(vs) - rojos - amar))
    if rojos:
        print("\n  Hay creativos en ROJO. No subirlos: regenerar cambiando composicion,")
        print("  encuadre y tratamiento fotografico, no solo los textos.")
    sys.exit(1 if rojos else 0)


if __name__ == "__main__":
    main()
