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


def test_estructura_por_bloques_no_pierde_ni_mezcla():
    """--json: por bloques, sin perder texto y sin una sola instruccion en lo que se pega."""
    v, faltan, _ = G.resolver("CLEARSTEM")
    if v is None or faltan:
        check("CLEARSTEM resuelve para probar la estructura", False, faltan)
        return
    txt = G.render(v)
    e = G.estructura(txt)
    bloques = [b for s in e["secciones"] for b in s["bloques"]]
    pegado = "\n".join(b["pegar"] for b in bloques)
    check("ningun bloque lleva una linea >>",
          not any(l.lstrip().startswith(">>") for b in bloques for l in b["pegar"].splitlines()))
    # Todo lo que para_pegar() entrega aparece en algun lugar de la estructura: cada linea
    # de copy es un titulo (de flujo, seccion o bloque) o parte de un `pegar`.
    titulos = set(e["encabezado"]["lineas"]) | {s["titulo"] for s in e["secciones"]} | {b["titulo"] for b in bloques}
    lineas_pegado = set(l.strip() for l in pegado.splitlines())
    perdidas = [l for l in G.para_pegar(txt).splitlines()
                if l.strip() and not G.RE_RAYA.match(l) and not G.RE_SECCION.match(l)
                and l.strip() not in titulos and l.strip() not in lineas_pegado]
    check("no se pierde ninguna linea de copy", not perdidas, perdidas[:3])
    instrucciones = [l.lstrip()[2:].strip() for l in txt.splitlines() if G.es_instruccion(l)]
    juntadas = e["encabezado"]["instrucciones"] + [i for s in e["secciones"] for i in s["instrucciones"]] \
        + [i for b in bloques for i in b["instrucciones"]]
    check("todas las instrucciones quedan, aparte", sorted(instrucciones) == sorted(juntadas),
          (len(instrucciones), len(juntadas)))
    int2 = next((b for b in bloques if b["titulo"].startswith("INTERACCIÓN 2")), None)
    check("una linea en mayusculas dentro de un mensaje no abre bloque (OFERTAS HASTA AGOTAR)",
          int2 is not None and "OFERTAS HASTA AGOTAR" in int2["pegar"])
    check("los <<BLOQUE:x>> de etapa-5 quedan marcados como pendientes",
          any("descripcion" in b["pendientes"] for b in bloques))
    reglas = [s for s in e["secciones"] if s["titulo"].startswith("REGLAS")]
    check("las reglas son UN bloque (un solo campo de LucidBot)",
          len(reglas) == 1 and len(reglas[0]["bloques"]) == 1)


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


def _con_datos(datos, fn):
    """Corre fn() con G.leer(nombre) devolviendo datos[nombre] si esta declarado en el dict,
    y los CSV reales del portafolio para cualquier otro nombre. Fixture en memoria: no toca
    disco ni agrega filas a PRODUCTOS/*.csv (T2/T1 no cambian data, solo codigo)."""
    original = G.leer

    def falso(nombre, carpeta=G.PROD):
        if nombre in datos:
            return datos[nombre]
        return original(nombre, carpeta)

    G.leer = falso
    try:
        return fn()
    finally:
        G.leer = original


VOCAB_NIVELES = [
    {"eje": "nivel_conciencia", "valor": "1", "mapea_a": ""},
    {"eje": "nivel_conciencia", "valor": "2", "mapea_a": ""},
    {"eje": "nivel_conciencia", "valor": "3A", "mapea_a": ""},
    {"eje": "nivel_conciencia", "valor": "3B", "mapea_a": ""},
    {"eje": "nivel_conciencia", "valor": "3a", "mapea_a": "3A"},
    {"eje": "nivel_conciencia", "valor": "3", "mapea_a": "REVISAR"},
]


def _conjunto(pk="PROD_X", angulo="ANG_X", fase="FASE2", estado="ACTIVO", nivel="1"):
    return {"producto_key": pk, "angulo_key": angulo, "fase": fase, "estado": estado,
            "nivel_conciencia": nivel}


def test_apertura_nivel_por_cada_nivel():
    """Los cuatro niveles resuelven a su instruccion — texto declarado en NIVELES_APERTURA."""
    for nivel in ("1", "2", "3A", "3B"):
        datos = {"_DIM_CONJUNTOS.csv": [_conjunto(nivel=nivel)],
                 "_DIM_VOCABULARIO.csv": VOCAB_NIVELES}
        resuelto, razon = _con_datos(
            datos, lambda: G.nivel_conciencia_angulo("PROD_X", "ANG_X"))
        check("nivel %s se resuelve sin bloquear" % nivel, resuelto == nivel and razon is None,
              (resuelto, razon))
        check("nivel %s trae su instruccion en NIVELES_APERTURA" % nivel,
              nivel in G.NIVELES_APERTURA and G.NIVELES_APERTURA[nivel])


def test_apertura_nivel_alias_se_normaliza():
    """'3a' (alias sucio) normaliza a '3A' via _DIM_VOCABULARIO.csv, no a mano."""
    datos = {"_DIM_CONJUNTOS.csv": [_conjunto(nivel="3a")],
              "_DIM_VOCABULARIO.csv": VOCAB_NIVELES}
    resuelto, razon = _con_datos(datos, lambda: G.nivel_conciencia_angulo("PROD_X", "ANG_X"))
    check("el alias '3a' normaliza a '3A'", resuelto == "3A" and razon is None, (resuelto, razon))


def test_apertura_nivel_ausente_bloquea():
    """Sin nivel_conciencia declarado en los conjuntos del angulo: bloquea con la razon."""
    datos = {"_DIM_CONJUNTOS.csv": [_conjunto(nivel="")],
              "_DIM_VOCABULARIO.csv": VOCAB_NIVELES}
    resuelto, razon = _con_datos(datos, lambda: G.nivel_conciencia_angulo("PROD_X", "ANG_X"))
    check("nivel ausente bloquea", resuelto is None and razon and "sin nivel_conciencia" in razon,
          (resuelto, razon))


def test_apertura_nivel_ambiguo_3_a_secas_bloquea():
    """'3' a secas mapea a REVISAR (no distingue 3A de 3B): bloquea, no elige por su cuenta."""
    datos = {"_DIM_CONJUNTOS.csv": [_conjunto(nivel="3")],
              "_DIM_VOCABULARIO.csv": VOCAB_NIVELES}
    resuelto, razon = _con_datos(datos, lambda: G.nivel_conciencia_angulo("PROD_X", "ANG_X"))
    check("'3' a secas bloquea por ambiguo", resuelto is None and razon and "ambiguo" in razon,
          (resuelto, razon))


def test_apertura_nivel_en_conflicto_bloquea():
    """Dos conjuntos ACTIVO del mismo angulo con niveles distintos: bloquea, no promedia."""
    datos = {"_DIM_CONJUNTOS.csv": [_conjunto(nivel="1"), _conjunto(nivel="2")],
              "_DIM_VOCABULARIO.csv": VOCAB_NIVELES}
    resuelto, razon = _con_datos(datos, lambda: G.nivel_conciencia_angulo("PROD_X", "ANG_X"))
    check("niveles en conflicto bloquean", resuelto is None and razon and "conflicto" in razon,
          (resuelto, razon))
    datos_pausado = {"_DIM_CONJUNTOS.csv": [_conjunto(nivel="1"),
                                             _conjunto(nivel="2", estado="PAUSADO")],
                      "_DIM_VOCABULARIO.csv": VOCAB_NIVELES}
    resuelto2, razon2 = _con_datos(
        datos_pausado, lambda: G.nivel_conciencia_angulo("PROD_X", "ANG_X"))
    check("un conjunto PAUSADO en conflicto no cuenta", resuelto2 == "1" and razon2 is None,
          (resuelto2, razon2))


def test_es_flujo_dedicado():
    """Dedicado = existe algun conjunto fuera de FASE1 (el producto ya paso F1)."""
    solo_f1 = {"_DIM_CONJUNTOS.csv": [_conjunto(fase="FASE1")]}
    check("solo FASE1 no es dedicado", not _con_datos(solo_f1, lambda: G.es_flujo_dedicado("PROD_X")))
    con_f2 = {"_DIM_CONJUNTOS.csv": [_conjunto(fase="FASE1"), _conjunto(fase="FASE2_ESCALA")]}
    check("con un conjunto FASE2_ESCALA ya es dedicado",
          _con_datos(con_f2, lambda: G.es_flujo_dedicado("PROD_X")))


def test_flujo_paraguas_no_bloquea_ni_lleva_apertura():
    """F1 (paraguas, sin angulo fuera de FASE1): sin instruccion de nivel y sin bloqueo."""
    datos = {"_DIM_CONJUNTOS.csv": [_conjunto(pk="CLEARSTEM", angulo="RESISTENCIA_INSULINA_SOP",
                                               fase="FASE1")]}
    v, faltan, _ = _con_datos(datos, lambda: G.resolver("CLEARSTEM"))
    check("flujo paraguas no bloquea por apertura_nivel",
          not any(k == "apertura_nivel" for k, _ in faltan), faltan)
    if v:
        check("flujo paraguas no lleva instruccion de apertura", v.get("apertura_nivel") == "")
        txt = G.render(v)
        check("el render paraguas no deja el token ni la linea vacia colgando",
              "{{apertura_nivel}}" not in txt and ">> \n" not in txt)


def test_flujo_dedicado_clearstem_renderiza_instruccion():
    """CLEARSTEM (dedicado, angulo ganador en nivel 1) renderiza su instruccion de apertura."""
    v, faltan, _ = G.resolver("CLEARSTEM")
    check("CLEARSTEM no bloquea por apertura_nivel",
          v is not None and not any(k == "apertura_nivel" for k, _ in faltan), faltan)
    if v:
        check("CLEARSTEM lleva la instruccion del NIVEL 1",
              "NIVEL DE CONCIENCIA 1" in v.get("apertura_nivel", ""), v.get("apertura_nivel"))
        txt = G.render(v)
        check("la instruccion aparece antes de ELEMENTO 3",
              "NIVEL DE CONCIENCIA 1" in txt.split("ELEMENTO 3")[0])


def test_propuestas_valor_menos_de_6_bloquea():
    """Fórmula problema->que hace->resultado, pero menos de 6 declaradas: BLOQUEA."""
    texto = "\n".join(["problema %d -> hace X -> resultado" % i for i in range(5)])
    bloqueo, aviso = G.validar_propuestas_valor(texto)
    check("menos de 6 propuestas bloquea", bloqueo is not None and "6" in bloqueo, bloqueo)
    check("un bloqueo no trae aviso a la vez", aviso is None, aviso)


def test_propuestas_valor_6_a_8_pasa():
    """6-8 declaradas: pasa sin bloqueo ni aviso."""
    for n in (6, 7, 8):
        texto = "\n".join(["problema %d -> hace X -> resultado" % i for i in range(n)])
        bloqueo, aviso = G.validar_propuestas_valor(texto)
        check("%d propuestas pasa sin bloqueo ni aviso" % n, bloqueo is None and aviso is None,
              (bloqueo, aviso))


def test_propuestas_valor_arriba_de_20_avisa():
    """Mas de 20 no bloquea, pero avisa que puede saturar las infografias."""
    texto = "\n".join(["propuesta %d" % i for i in range(21)])
    bloqueo, aviso = G.validar_propuestas_valor(texto)
    check("mas de 20 no bloquea", bloqueo is None, bloqueo)
    check("mas de 20 avisa", aviso is not None and "21" in aviso, aviso)


def test_propuestas_valor_no_declaradas_solo_avisa():
    """T2: sin declarar (None) es WARNING, nunca bloqueo — CLEARSTEM/TINNIDROP siguen rindiendo."""
    bloqueo, aviso = G.validar_propuestas_valor(None)
    check("no declaradas nunca bloquea", bloqueo is None, bloqueo)
    check("no declaradas avisa PENDIENTE", aviso is not None and "PENDIENTE" in aviso, aviso)


def test_propuestas_valor_ignora_lineas_vacias_e_instrucciones():
    """Lineas vacias y '>>' no cuentan como propuesta declarada."""
    texto = "p1\n\n>> nota para etapa-5\np2\np3\np4\np5\np6\n"
    n = len(G.propuestas_valor_lineas(texto))
    check("cuenta solo las 6 lineas de propuesta", n == 6, n)


def test_clearstem_tinnidrop_sin_propuestas_no_bloquean():
    """Productos vivos sin propuestas_valor declaradas (sin --propuestas): siguen renderizando."""
    for pk in ("CLEARSTEM", "TINNIDROP"):
        v, faltan, avisos = G.resolver(pk)
        bloqueo, aviso = G.validar_propuestas_valor(None)
        check("%s no bloquea por propuestas_valor sin declarar" % pk,
              v is not None and not faltan and bloqueo is None, (faltan, bloqueo))
        check("%s trae el aviso PENDIENTE cuando se le suma" % pk, aviso is not None)


def test_mensaje_prellenado_anuncio_gt_mspas():
    """T3: el mensaje prellenado del anuncio lleva el producto + 'registro MSPAS' en GT."""
    v, faltan, _ = G.resolver("CLEARSTEM")
    check("CLEARSTEM no bloquea por mensaje_prellenado_anuncio",
          v is not None and not any(k == "mensaje_prellenado_anuncio" for k, _ in faltan), faltan)
    if v:
        check("el mensaje lleva el producto y 'registro MSPAS' (GT)",
              v.get("mensaje_prellenado_anuncio") ==
              "Hola, quiero más información de %s con registro MSPAS" % v["producto_display"],
              v.get("mensaje_prellenado_anuncio"))


def test_mensaje_prellenado_anuncio_co_invima():
    """CO usa 'registro INVIMA': el mercado es variable, no doctrina (mismo dato que persona/transportadoras)."""
    datos = {"_DIM_FLUJO_BOT.csv": [{"producto_key": "PROD_X", "mercado": "CO",
                                      "producto_display": "ProductoX"}]}
    v, faltan, _ = _con_datos(datos, lambda: G.resolver("PROD_X"))
    check("PROD_X (CO) resuelve el mercado", v is not None, faltan)
    if v:
        check("el mensaje lleva 'registro INVIMA' en CO",
              v.get("mensaje_prellenado_anuncio") ==
              "Hola, quiero más información de ProductoX con registro INVIMA",
              v.get("mensaje_prellenado_anuncio"))


def test_mensaje_prellenado_anuncio_sin_registro_bloquea():
    """Mercado sin registro_sanitario declarado: bloquea como cualquier {{variable}} (invariante 4)."""
    fila_gt_sin_registro = {"mercado": "GT", "pais": "Guatemala",
                             "pais_cobertura": "toda Guatemala", "persona": "voseo",
                             "registro_sanitario": "", "simbolo": "Q",
                             "unidad_geo": "municipio y departamento", "unidad_local": "municipio",
                             "transportadoras": "GINTACOM y FORZA",
                             "dias_entrega": "2 a 5 dias habiles", "dias_espera_casa": "5"}
    datos = {"_DIM_MERCADOS.csv": [fila_gt_sin_registro]}
    v, faltan, _ = _con_datos(datos, lambda: G.resolver("CLEARSTEM"))
    check("sin registro_sanitario, mensaje_prellenado_anuncio bloquea",
          any(k == "mensaje_prellenado_anuncio" for k, _ in faltan), faltan)


def test_mensaje_prellenado_anuncio_ausente_del_copy():
    """El mensaje prellenado (se configura a mano en Ads Manager) nunca se pega en LucidBot."""
    v, faltan, _ = G.resolver("CLEARSTEM")
    if v is None or faltan:
        check("CLEARSTEM resuelve para probar --copy", False, faltan)
        return
    txt = G.render(v)
    pegar = G.para_pegar(txt)
    check("el mensaje prellenado del anuncio no aparece en --copy",
          "Hola, quiero más información" not in pegar and "MENSAJE PRELLENADO" not in pegar,
          pegar[:200])
    check("la instruccion SI queda declarada en el render completo (no se pierde)",
          "Hola, quiero más información" in txt and "MENSAJE PRELLENADO DEL ANUNCIO" in txt)


def test_clearstem_tinnidrop_llevan_mensaje_prellenado():
    """Productos vivos: el mensaje prellenado resuelve y lleva su nombre de producto."""
    for pk in ("CLEARSTEM", "TINNIDROP"):
        v, faltan, _ = G.resolver(pk)
        check("%s no bloquea por mensaje_prellenado_anuncio" % pk,
              v is not None and not any(k == "mensaje_prellenado_anuncio" for k, _ in faltan),
              faltan)
        if v:
            check("%s lleva su producto_display en el mensaje prellenado" % pk,
                  v["producto_display"] in v.get("mensaje_prellenado_anuncio", ""))


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
               test_estructura_por_bloques_no_pierde_ni_mezcla,
               test_mercado_es_variable,
               test_apertura_nivel_por_cada_nivel,
               test_apertura_nivel_alias_se_normaliza,
               test_apertura_nivel_ausente_bloquea,
               test_apertura_nivel_ambiguo_3_a_secas_bloquea,
               test_apertura_nivel_en_conflicto_bloquea,
               test_es_flujo_dedicado,
               test_flujo_paraguas_no_bloquea_ni_lleva_apertura,
               test_flujo_dedicado_clearstem_renderiza_instruccion,
               test_propuestas_valor_menos_de_6_bloquea,
               test_propuestas_valor_6_a_8_pasa,
               test_propuestas_valor_arriba_de_20_avisa,
               test_propuestas_valor_no_declaradas_solo_avisa,
               test_propuestas_valor_ignora_lineas_vacias_e_instrucciones,
               test_clearstem_tinnidrop_sin_propuestas_no_bloquean,
               test_mensaje_prellenado_anuncio_gt_mspas,
               test_mensaje_prellenado_anuncio_co_invima,
               test_mensaje_prellenado_anuncio_sin_registro_bloquea,
               test_mensaje_prellenado_anuncio_ausente_del_copy,
               test_clearstem_tinnidrop_llevan_mensaje_prellenado):
        print("\n%s" % (fn.__doc__ or fn.__name__).splitlines()[0])
        fn()
    print("\n%s" % ("TODO PASA" if not FALLAS else "FALLAN %d: %s"
                    % (len(FALLAS), ", ".join(FALLAS))))
    return 1 if FALLAS else 0


if __name__ == "__main__":
    sys.exit(main())
