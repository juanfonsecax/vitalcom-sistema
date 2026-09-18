#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_gen_flujo_bot.py — CONGELA las reglas del layout del flujo LucidBot.

USO:  python Ads/_TOOLS/test_gen_flujo_bot.py     (exit 0 = pasa, 1 = falla)
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_flujo_bot as G  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, OSError):
    pass

FALLAS = []


def check(nombre, cond, detalle=""):
    if cond:
        print("  ok   %s" % nombre)
    else:
        print("  FALLA %s  %s" % (nombre, detalle))
        FALLAS.append(nombre)


def test_pregunta_filtro_se_rechaza():
    """La pregunta filtro de dolor no va en ningun elemento: el filtro es el ANUNCIO."""
    txt = ("ELEMENTO 12 — CIERRE:\n"
           "Para darte la informacion mas util, contame: "
           "¿cual de estas situaciones se parece mas a la tuya?\n"
           "A) hormigueo  B) ciatica  C) animo bajo  D) otro\n")
    malos = G.prohibiciones(txt)
    check("rechaza la pregunta filtro A/B/C/D",
          any("FILTRO" in m for m in malos), malos)


def test_instruccion_no_dispara_el_gate():
    """Una INSTRUCCION que cita la frase prohibida no dispara el gate: no es copy."""
    txt = ("ELEMENTO FINAL — CIERRE:\nHola, soy Laura 😊 ¿de que municipio nos escribis?\n"
           ">> Aca NO va una pregunta de opciones por dolor: ni «cual de estas situaciones "
           "se parece mas a la tuya», ni A/B/C/D.\n")
    check("la instruccion que cita la frase prohibida no dispara el gate",
          not G.prohibiciones(txt), G.prohibiciones(txt))


def test_las_tres_notaciones_son_distinguibles():
    """Una forma, un significado: las tres notaciones son separables por codigo."""
    check("una linea '>>' es instruccion", G.es_instruccion(">> nota para el operador"))
    check("una linea '>>' indentada tambien", G.es_instruccion("   >> nota"))
    check("el copy no es instruccion", not G.es_instruccion("¡Hola! 👋 Bienvenida/o"))
    v, faltan, _ = G.resolver("CLEARSTEM")
    if v and not faltan:
        pegar = G.para_pegar(G.render(v))
        check("--copy no arrastra ninguna linea de instruccion",
              not any(G.es_instruccion(l) for l in pegar.splitlines()))
        check("--copy no deja bloques ni variables sin resolver",
              "{{" not in pegar)


def test_dos_plazos_de_garantia_se_rechazan():
    """Va UN solo plazo de garantia, igual en los tres escalones."""
    txt = ("1️⃣ 1 Tratamiento → Q198 ENVIO GRATIS + Garantía 30 dias\n"
           "2️⃣ 2 Tratamientos → Q289 ENVIO GRATIS + Garantía 90 dias\n")
    malos = G.prohibiciones(txt)
    check("rechaza dos plazos de garantia distintos",
          any("DOS PLAZOS" in m for m in malos), malos)


def test_garantia_unica_se_acepta():
    """El mismo plazo repetido en los tres escalones es correcto y NO bloquea."""
    txt = ("1️⃣ → Q198 + 90 días de garantía\n2️⃣ → Q289 + 90 días de garantía\n"
           "3️⃣ → Q389 + 90 días de garantía\n")
    check("acepta el mismo plazo repetido en los tres escalones",
          not G.prohibiciones(txt), G.prohibiciones(txt))


def test_variable_sin_resolver_bloquea():
    """Invariante 4 de CLAUDE.md: si falta un input, detener. Nunca asumir ni inventar."""
    malos = G.prohibiciones("Bienvenida/o a *{{nombre_tienda}}*\n")
    check("bloquea una variable sin resolver en la salida",
          any("SIN RESOLVER" in m for m in malos), malos)


def test_plural_de_la_duracion():
    """El titulo del escalon pluraliza la duracion: "2 meses", no "2 mes"."""
    fila = {"envase": "frasco", "duracion_1u": "1 mes"}
    esc, _ = G.escalera("CLEARSTEM", fila, "Q")
    check("pluraliza la duracion del escalon",
          esc is not None and "2 meses" in esc and "2 mes " not in esc,
          (esc or "")[:120])


def test_precio_sale_del_csv_no_del_texto():
    """Ningun precio se tipea: la escalera sale de _DIM_PRECIOS.csv (manda Dropi)."""
    fila = {"envase": "frasco", "duracion_1u": "1 mes"}
    esc, _ = G.escalera("CLEARSTEM", fila, "Q")
    ok = esc is not None and all(p in esc for p in ("Q198", "Q289", "Q389"))
    viejos = esc is not None and any(p in esc for p in ("Q199", "Q299", "Q399"))
    check("la escalera usa el precio de _DIM_PRECIOS.csv", ok and not viejos,
          (esc or "")[:200])


def test_escalera_respeta_la_arquitectura_del_csv():
    """La arquitectura de oferta sale del CSV: NUSAVA corre 2X1 y 4X2, no 1x/2x/3x."""
    fila = {"envase": "frasco", "duracion_1u": ""}
    esc, _ = G.escalera("NUSAVA", fila, "Q")
    check("la arquitectura de oferta sale del CSV, no de una suposicion de 3 unidades",
          esc is not None and "2X1" in esc and "4X2" in esc, (esc or "")[:200])


def test_clearstem_pasa_completo():
    """La fila de referencia (CLEARSTEM) renderiza completa y sin bloqueos."""
    v, faltan, _ = G.resolver("CLEARSTEM")
    check("CLEARSTEM resuelve sin faltantes", v is not None and not faltan, faltan)
    if v:
        txt = G.render(v)
        check("CLEARSTEM pasa las prohibiciones", not G.prohibiciones(txt),
              G.prohibiciones(txt))
        check("el saludo lleva la TIENDA a secas",
              "Bienvenida/o a *Sanarte*" in txt)
        check("el saludo NO nombra a la asesora",
              "Laura" not in txt.split("ELEMENTO 2")[0])


def test_mercado_es_variable():
    """El mercado es variable: GT va en voseo y CO en tuteo, con su transportadora."""
    mercados = {r["mercado"]: r for r in G.leer("_DIM_MERCADOS.csv")}
    check("existen los dos mercados", set(mercados) >= {"GT", "CO"}, sorted(mercados))
    if {"GT", "CO"} <= set(mercados):
        check("GT es voseo y CO es tuteo",
              mercados["GT"]["persona"] == "voseo" and
              mercados["CO"]["persona"] == "tuteo")
        check("cada mercado trae su transportadora",
              "GINTACOM" in mercados["GT"]["transportadoras"] and
              "GINTACOM" not in mercados["CO"]["transportadoras"])


def main():
    print("test_gen_flujo_bot.py — reglas del layout del bot\n")
    for fn in (test_pregunta_filtro_se_rechaza,
               test_instruccion_no_dispara_el_gate,
               test_las_tres_notaciones_son_distinguibles,
               test_dos_plazos_de_garantia_se_rechazan,
               test_garantia_unica_se_acepta,
               test_variable_sin_resolver_bloquea,
               test_plural_de_la_duracion,
               test_precio_sale_del_csv_no_del_texto,
               test_escalera_respeta_la_arquitectura_del_csv,
               test_clearstem_pasa_completo,
               test_mercado_es_variable):
        print("\n%s" % (fn.__doc__ or fn.__name__).splitlines()[0])
        fn()
    print("\n%s" % ("TODO PASA" if not FALLAS else "FALLAN %d: %s"
                    % (len(FALLAS), ", ".join(FALLAS))))
    return 1 if FALLAS else 0


if __name__ == "__main__":
    sys.exit(main())
