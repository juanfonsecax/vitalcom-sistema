#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_gen_manual.py — CONGELA el armado de 1_HACER_MANUAL.txt desde sus duenos.

gen_manual.py no tipea contenido: copia textual el plan (gen_lanzador), el flujo
(gen_flujo_bot + BLOQUES_BOT.md) y los prompts (INFOGRAFIAS.md). Si falta un dato,
bloquea nombrando que falta y quien lo produce.

USO:  python Ads/_TOOLS/test_gen_manual.py     (exit 0 = pasa, 1 = falla)
"""

import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_manual as GM  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, OSError):
    pass

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FALLAS = []


def check(nombre, cond, detalle=""):
    if cond:
        print("  ok   %s" % nombre)
    else:
        print("  FALLA %s  %s" % (nombre, detalle))
        FALLAS.append(nombre)


def _conjunto(n, con_prompt=True):
    c = {"n": n, "angulo_titulo": "Dolor %d" % n, "formato": "IMAGEN",
         "archivo_creativo": "AD%d.png" % n, "lleva_precio": n == 1,
         "nombre": "CJ%d" % n, "presupuesto_usd": 3.95, "banda_edad": "25-40",
         "genero": "MUJER", "anuncios": [{"letra": "A", "nombre": "AD%d ~ A" % n}],
         "presupuesto_cuenta_texto": "US$3.95",
         "copy": {"textos": ["TEXTO %d-A" % n, "TEXTO %d-B" % n],
                  "titulos": ["TIT %d" % n], "descripcion": "DESC %d" % n}}
    if con_prompt:
        c["prompt_imagen"] = "PROMPT %d COMPLETO" % n
    return c


def _plan_falso(registrado=False):
    return {
        "nombre": "Producto Falso", "fase": 1, "fase_nombre": "FASE 1 · ÁNGULOS",
        "pagina": "Fan Falsa", "page_id": "123", "cuenta": "CUENTAX",
        "bloqueantes": [], "faltantes": [],
        "campanas": [{"nombre": "CAMP1", "objetivo": "Tráfico", "presupuesto": "ABO"}],
        "lanzamiento": {"fecha": "2026-10-01", "legible": "01-oct-2026", "hora": "4:00 AM",
                        "registrado": registrado, "campana_registrada": "CAMP1" if registrado else None},
        "calendario": [{"dia": "Día 0", "fecha": "01-oct", "que": "Lanza",
                        "hace": "nada", "manda": None}],
        "config_meta": ["Ubicación: X · Sin intereses", "NO aceptar recomendaciones de Meta"],
        "presupuesto": {"moneda_cuenta": "USD", "total_dia_cuenta_texto": "US$7.90"},
        "conjuntos": [_conjunto(1), _conjunto(2, con_prompt=False)],
    }


def _datos_falsos(registrado=False):
    return {"pk": "FALSO", "plan": _plan_falso(registrado), "flujo": "FLUJO PEGABLE",
            "infografias": {"1": "INFO UNO", "2": "INFO DOS"},
            "encabezado": "ENCABEZADO CANONICO",
            "mensaje_prellenado": "Hola, quiero info",
            "packshot": "Ads/MEDIA_X/PACK.png",
            "referencia": "Ads/_SWIPE/ref.jpg"}


def test_render_manual_copia_textual_y_ordena_secciones():
    """Todo lo de origen aparece textual y las secciones van A..F en orden."""
    manual = GM.render_manual(_datos_falsos())
    for esperado in ("PROMPT 1 COMPLETO", "TEXTO 1-A", "TEXTO 2-B", "TIT 1", "TIT 2",
                     "DESC 1", "DESC 2", "FLUJO PEGABLE", "INFO UNO", "INFO DOS",
                     "ENCABEZADO CANONICO", "Ads/MEDIA_X/PACK.png", "Ads/_SWIPE/ref.jpg",
                     "Ubicación: X · Sin intereses", "NO aceptar recomendaciones de Meta",
                     "Hola, quiero info"):
        check("copia textual %s" % esperado.split()[0], esperado in manual, manual[-200:])
    check("la primera linea es el encabezado",
          manual.splitlines()[0] == "ENCABEZADO CANONICO", manual.splitlines()[0])
    posiciones = [manual.find(h) for h in ("A. CHECKLIST", "B. CREATIVOS", "C. INFOGRAFÍAS",
                                           "D. FLUJO", "E. ESTRUCTURA", "F. CALENDARIO")]
    check("secciones A..F en orden",
          all(p >= 0 for p in posiciones) and posiciones == sorted(posiciones), posiciones)
    con_reg = GM.render_manual(_datos_falsos(registrado=True))
    check("registrado muestra ya registrado y no el comando",
          "LANZAMIENTO ya registrado" in con_reg and "--evento LANZAMIENTO" not in con_reg)
    check("sin registrar sale el comando",
          "--evento LANZAMIENTO" in manual and "LANZAMIENTO ya registrado" not in manual)


def test_parsear_infografias_lee_y_rechaza():
    """Lee 3 bloques; repetido o fuera de 1..6 lanza ValueError."""
    texto = "<<INFOGRAFIA:1>>\n\nTexto uno.\n\n<<INFOGRAFIA:2>>\nTexto dos.\n<<INFOGRAFIA:3>>\nTres.\n"
    bloques = GM.parsear_infografias(texto)
    check("lee los 3 bloques",
          bloques == {"1": "Texto uno.", "2": "Texto dos.", "3": "Tres."}, bloques)
    for malo, que in (("<<INFOGRAFIA:1>>\na\n<<INFOGRAFIA:1>>\nb\n", "repetido"),
                      ("<<INFOGRAFIA:7>>\ntexto\n", "fuera de rango")):
        try:
            GM.parsear_infografias(malo)
        except ValueError:
            check("%s lanza ValueError" % que, True)
        else:
            check("%s lanza ValueError" % que, False, malo)


def test_render_manual_tolera_opcionales_vacios():
    """Sin prompt_imagen, sin claves nuevas y con manda None el render no falla."""
    datos = {"pk": "FALSO",
             "plan": {"nombre": "X", "conjuntos": [{"n": 1, "anuncios": [], "copy": {}}],
                      "campanas": [], "calendario": [{"dia": "D0", "manda": None}]},
             "flujo": "", "infografias": {}}
    try:
        manual = GM.render_manual(datos)
    except (KeyError, TypeError) as error:
        check("render con opcionales vacios no falla", False, error)
        return
    check("render con opcionales vacios no falla", "AD 1" in manual and "D0" in manual)


def test_ovulos_reune_sin_bloqueos():
    """OVULOS_PURITY (real, solo lectura) reune sin bloqueos."""
    datos, bloqueos = GM.reunir("OVULOS_PURITY")
    check("sin bloqueos", bloqueos == [], bloqueos)
    check("trae plan, flujo e infografias",
          bool(datos["plan"]) and bool(datos["flujo"]) and len(datos["infografias"]) >= 3,
          (bool(datos["plan"]), len(datos["flujo"]), len(datos["infografias"])))


def test_ovulos_manual_trae_todo_textual():
    """El manual trae reglas, infografias y, por conjunto, nombre y prompt."""
    datos, bloqueos = GM.reunir("OVULOS_PURITY")
    if bloqueos:
        check("OVULOS_PURITY reune para el manual", False, bloqueos)
        return
    manual = GM.render_manual(datos)
    check("trae REGLAS CONVERSACIONALES", "REGLAS CONVERSACIONALES" in manual)
    with io.open(os.path.join(BASE, "PRODUCTOS", "OVULOS_PURITY", "2_DATA_PRODUCTO.txt"),
                  encoding="utf-8") as fh:
        primera = fh.readline().rstrip("\n")
    check("la primera linea es el encabezado canonico",
          manual.splitlines()[0] == primera, manual.splitlines()[0])
    check("trae la config fija", "Advantage+ Audience: OFF" in manual)
    check("trae el pais", "Ubicación: Colombia" in manual)
    check("trae el packshot", "OVULOSPURITY_PACKSHOT.png" in manual)
    check("trae la referencia", "ligera__Camila-Recomienda__15_" in manual)
    check("trae el lanzamiento registrado",
          "LANZAMIENTO ya registrado: 2026-09-30" in manual)
    with io.open(os.path.join(BASE, "PRODUCTOS", "OVULOS_PURITY", "INFOGRAFIAS.md"),
                  encoding="utf-8") as fh:
        esperadas = GM.parsear_infografias(fh.read())
    check("son 4 infografias", len(esperadas) == 4, sorted(esperadas))
    for n, texto in esperadas.items():
        check("infografia %s textual" % n, texto in manual, n)
    for c in datos["plan"]["conjuntos"]:
        check("conjunto %s con nombre" % c["n"], c["nombre"] in manual, c["nombre"])
        if c.get("prompt_imagen"):
            check("conjunto %s con prompt" % c["n"], c["prompt_imagen"] in manual, c["n"])


def test_clearstem_bloquea_nombrando_los_duenos():
    """CLEARSTEM (sin archivos nuevos) bloquea por INFOGRAFIAS.md y BLOQUES_BOT.md."""
    try:
        _datos, bloqueos = GM.reunir("CLEARSTEM")
    except (KeyError, TypeError, ValueError) as error:
        check("reunir no lanza excepcion", False, error)
        return
    check("reunir no lanza excepcion", True)
    check("nombra INFOGRAFIAS.md", any("INFOGRAFIAS.md" in b for b in bloqueos), bloqueos)
    check("nombra BLOQUES_BOT.md", any("BLOQUES_BOT.md" in b for b in bloqueos), bloqueos)


def main():
    print("test_gen_manual.py — 1_HACER_MANUAL.txt desde sus duenos\n")
    for fn in (test_render_manual_copia_textual_y_ordena_secciones,
               test_parsear_infografias_lee_y_rechaza,
               test_render_manual_tolera_opcionales_vacios,
               test_ovulos_reune_sin_bloqueos,
               test_ovulos_manual_trae_todo_textual,
               test_clearstem_bloquea_nombrando_los_duenos):
        print("\n%s" % (fn.__doc__ or fn.__name__).splitlines()[0])
        fn()
    print("\n%s" % ("TODO PASA" if not FALLAS else "FALLAN %d: %s"
                    % (len(FALLAS), ", ".join(FALLAS))))
    return 1 if FALLAS else 0


if __name__ == "__main__":
    sys.exit(main())
