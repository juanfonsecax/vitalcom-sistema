# -*- coding: utf-8 -*-
"""Genera PRODUCTOS/_CLASIFICACION_ANUNCIOS.csv — el trabajo de clasificación, auditable.

Cada fila declara CON QUÉ EVIDENCIA se clasificó. Lo que no tiene evidencia queda
NO_CLASIFICABLE con su razón: inventar un concepto es peor que dejarlo vacío, porque
contamina el aprendizaje acumulado sin dejar rastro.
"""
import csv, os

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SAL = os.path.join(BASE, "PRODUCTOS", "_CLASIFICACION_ANUNCIOS.csv")

COLS = ["producto_key", "anuncio_norm", "concepto_key", "canonico_id", "nivel_conciencia",
        "oferta_key", "lleva_precio", "rol_embudo", "formato", "confianza", "evidencia", "notas"]

F = []


def c(pk, an, con, cn, nc, of, lp, rol, fmt, conf, ev, notas=""):
    F.append(dict(zip(COLS, [pk, an, con, cn, nc, of, lp, rol, fmt, conf, ev, notas])))


# ═══ NUSAVA — ángulo ARDOR. Las 6 piezas se vieron. Confianza ALTA.
c("NUSAVA", "MA6_OFERTA", "C1_OFERTA", "CN03_OFERTA_MULTIPLICADOR", "2", "2X1", "SI", "BOFU",
  "IMAGEN", "ALTA", "imagen leida: Ads/MEDIA_GTR7_NUSAVAB12/NUSAVAB12_ARDOR_MA6_OFERTA.jpg",
  "Starburst MEGA OFERTA 2X1 + 2 tratamientos Q219 + dos frascos + trust badges. El numeral domina.")
c("NUSAVA", "MA4_DEPIE", "C3_SINTOMA", "CN07_DOLOR_A_PLENO", "2", "SIN_PRECIO", "NO", "TOFU",
  "IMAGEN", "ALTA", "imagen leida: NUSAVAB12_ARDOR_MA4_DEPIE.jpg",
  "Hombre mayor agarrandose el pie ocupa media pieza. Burbuja WhatsApp como prueba secundaria.")
c("NUSAVA", "MA2_ARDORNOCHE", "C3_SINTOMA", "CN07_DOLOR_A_PLENO", "2", "SIN_PRECIO", "NO", "TOFU",
  "IMAGEN", "ALTA", "imagen leida: NUSAVAB12_ARDOR_MA2_ARDORNOCHE.jpg",
  "Mujer en cama, pie enrojecido a pleno. Mismo canonico que MA4 con otro avatar.")
c("NUSAVA", "MA5_AZUCAR", "C2_BENEFICIOS", "CN21_AVATAR_CARD_BENEFICIOS", "1", "SIN_PRECIO", "NO",
  "TOFU", "IMAGEN", "ALTA", "imagen leida: NUSAVAB12_ARDOR_MA5_AZUCAR.jpg",
  "Medico con bata sostiene el producto + 3 cards de beneficio + prueba social +8400. "
  "GAP: el canonico no captura AUTORIDAD MEDICA, que es el patron dominante del mercado.")
c("NUSAVA", "MA1_COMPLEJOB", "C9_COMPARACION", "CN14_COMPARACION_DOS_COLUMNAS", "3A", "2X1", "NO",
  "MOFU", "IMAGEN", "ALTA", "imagen leida: NUSAVAB12_ARDOR_MA1_COMPLEJOB.jpg",
  "Blister de pastillas tachado vs gotero liquido. Habla a quien YA probo complejo B.")
c("NUSAVA", "MA3_HORMIGUEO", "C2_BENEFICIOS", "CN13_ANATOMIA_MECANISMO", "1", "SIN_PRECIO", "NO",
  "TOFU", "IMAGEN", "ALTA", "imagen leida: NUSAVAB12_ARDOR_MA3_HORMIGUEO.jpg",
  "Nervios encendidos sobre mano y pie + callouts. Educa la causa.")

# ═══ TINNIDROP — VIDEO. canonico_id VACIO a proposito (ver nota metodologica del doc).
c("TINNIDROP", "tinnidrop 3", "C2_BENEFICIOS", "", "1", "SIN_PRECIO", "NO", "TOFU",
  "VIDEO", "MEDIA", "transcripcion: Ads/1.2 Transcripcion videos/TINNIDROP/tinnidrop3.txt",
  "Hook: animacion 3D del mecanismo cerebral. Formato declarado educacional. "
  "canonico vacio: los 22 canonicos son vocabulario de IMAGEN.")
c("TINNIDROP", "tinnidrop 6", "C3_SINTOMA", "", "2", "SIN_PRECIO", "NO", "TOFU",
  "VIDEO", "MEDIA", "transcripcion: tinnidrop6.txt",
  "Hook: '?Escuchas un pitido aunque todo este en silencio?' + gotero en oreja. Abre por sintoma.")
c("TINNIDROP", "tinnidrop 4", "C5_PRUEBA", "", "3A", "SIN_PRECIO", "NO", "MOFU",
  "VIDEO", "MEDIA", "transcripcion: tinnidrop4.txt",
  "Hook: testimonio en 1a persona + producto en mano. 'Me costo menos que ir al medico'.")

# ═══ CLEARSTEM — VIDEO.
c("CLEARSTEM", "video Clearstem2", "C3_SINTOMA", "", "1", "SIN_PRECIO", "NO", "TOFU",
  "VIDEO", "MEDIA", "transcripcion: Clearstem2.txt",
  "Hook: mapa facial senalando donde se concentra el acne. Diagnostico del sintoma.")
c("CLEARSTEM", "video Clearstem3", "C9_COMPARACION", "", "3A", "SIN_PRECIO", "NO", "MOFU",
  "VIDEO", "BAJA", "transcripcion: Clearstem3.txt",
  "ANTI-FALSIFICACION: 'esto es falso' x4 vs el original. GAP DEL CATALOGO: los 8 conceptos "
  "no tienen categoria anti-falsificacion. Forzado a C9 porque enfrenta dos estados.")
c("CLEARSTEM", "video Clearstem10", "C5_PRUEBA", "", "2", "SIN_PRECIO", "NO", "MOFU",
  "VIDEO", "MEDIA", "transcripcion: Clearstem10.txt",
  "Testimonio a camara + foto del rostro con rosacea severa. Responde a un comentario real.")
c("CLEARSTEM", "video Clearstem13", "C3_SINTOMA", "", "1", "SIN_PRECIO", "NO", "TOFU",
  "VIDEO", "MEDIA", "transcripcion: Clearstem13.txt",
  "Mismo patron que Clearstem2 con avatar masculino: mapa facial del acne hormonal.")

with open(SAL, "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=COLS)
    w.writeheader()
    w.writerows(F)
print("escrito %s con %d filas clasificadas" % (SAL, len(F)))
