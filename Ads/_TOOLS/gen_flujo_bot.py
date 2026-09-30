#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen_flujo_bot.py — RENDERIZA el flujo LucidBot desde la plantilla declarada.

  1. Lee la PLANTILLA literal de `DOCTRINA/PLANTILLAS_FLUJO_BOT.md` (seccion 3).
     El texto fijo tiene UN dueno y este script no lo hardcodea.
  2. Resuelve cada `{{variable}}` contra `_DIM_MERCADOS.csv`, `_DIM_FLUJO_BOT.csv` y
     —para la escalera de precios— `_DIM_PRECIOS.csv`.
  3. BLOQUEA (exit 1) nombrando la variable que falta y el dueno del dato. No elige
     por su cuenta.
  4. Corre las prohibiciones de la seccion 5 de la plantilla sobre el texto renderizado.
  5. Escribe `PRODUCTOS/[PK]/FLUJO_LUCIDBOT.md`.

Lo que NO hace: no escribe el audio, los testimonios, el M2 ni las FAQ. Esos son juicio
de `etapa-5`; la plantilla solo declara donde van (`<<BLOQUE:x>>`).

USO
---
  python Ads/_TOOLS/gen_flujo_bot.py CLEARSTEM        renderiza un producto
  python Ads/_TOOLS/gen_flujo_bot.py --todo           todos los que tengan fila
  python Ads/_TOOLS/gen_flujo_bot.py --validar        gate: no escribe, solo verifica
  python Ads/_TOOLS/gen_flujo_bot.py CLEARSTEM --copy
                                                      imprime SOLO lo que se pega en Lucid
  python Ads/_TOOLS/gen_flujo_bot.py CLEARSTEM --parcial
                                                      escribe marcando lo que falta
  python Ads/_TOOLS/gen_flujo_bot.py CLEARSTEM --json [--parcial]
                                                      el flujo POR BLOQUES para la app: en
                                                      cada uno, lo que se pega y sus >> aparte.
                                                      No escribe nada.
  python Ads/_TOOLS/gen_flujo_bot.py CLEARSTEM --propuestas propuestas.txt
                                                      SOBRESCRIBE, solo para esta corrida, las
                                                      propuestas de valor que cuenta el gate (una
                                                      por linea). Uso: probar un archivo antes de
                                                      que etapa-guardar-producto lo persista. Sin
                                                      este flag (el camino normal) el gate lee
                                                      solas las propuestas ya persistidas en
                                                      PRODUCTOS/[carpeta]/2_DATA_PRODUCTO.txt,
                                                      seccion "PROPUESTAS DE VALOR" (la escribe
                                                      etapa-guardar-producto desde el bloque de
                                                      etapa-5). Ninguna de las dos declaradas →
                                                      PENDIENTE (aviso, nunca bloquea). Va con UN
                                                      producto_key, sin --validar/--todo.

LAS TRES NOTACIONES de la plantilla (una forma, un significado):
  {{variable}}        valor de un CSV. Si falta, este script BLOQUEA y nombra al dueno.
  <<BLOQUE:nombre>>   texto largo con juicio. Lo escribe etapa-5.
  >> al inicio        INSTRUCCION al operador o a etapa-5. NUNCA se pega en LucidBot.
Todo lo demas es literal y no se reescribe.
"""

import csv
import datetime
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mercado  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, OSError):
    pass

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROD = os.path.join(BASE, "PRODUCTOS")
PLANTILLA = os.path.join(BASE, "DOCTRINA", "PLANTILLAS_FLUJO_BOT.md")

# Quien produce cada dato. Un bloqueo que no nombra al dueno obliga a adivinar.
DUENO = {
    "pais": "_DIM_MERCADOS.csv", "persona": "_DIM_MERCADOS.csv",
    "simbolo": "_DIM_MERCADOS.csv", "unidad_geo": "_DIM_MERCADOS.csv",
    "transportadoras": "_DIM_MERCADOS.csv", "dias_entrega": "_DIM_MERCADOS.csv",
    "dias_espera_casa": "_DIM_MERCADOS.csv", "pais_cobertura": "_DIM_MERCADOS.csv",
    "unidad_local": "_DIM_MERCADOS.csv",
    "nombre_tienda": "operador (la TIENDA, no la fanpage)",
    "nombre_asesor": "operador",
    "producto_display": "_DIM_PRODUCTOS.csv",
    "envase": "operador",
    "duracion_1u": "operador",
    "dias_resultado": "etapa-1b / PLANTILLAS_DEFAULTS_OPERADOR.md",
    "mecanismo_1": "etapa-1b", "mecanismo_2": "etapa-1b",
    "prueba_social": "operador (cifra trazable CON su unidad)",
    "garantia_texto": "operador (plazo vigente, uno solo)",
    "dolor_angulo": "etapa-5", "solucion_fallida": "etapa-5", "recaida": "etapa-5",
    "sintoma_superficial": "etapa-5", "consecuencia_emocional": "etapa-5",
    "area_cuidado": "etapa-5", "verbo_tratar": "etapa-5",
    "resultado_sostenido": "etapa-5", "razon_tier_alto": "etapa-5",
    "n_infografias": "_DIM_FLUJO_BOT.csv", "n_testimonios": "_DIM_FLUJO_BOT.csv",
    "fuente_testimonios": "_DIM_FLUJO_BOT.csv",
    "angulo_nombre": "_DIM_CREATIVOS.csv (angulo con concepto de FASE 2) / "
                      "_ESTADO_ANGULOS.csv (paraguas F1, mas ventas acumuladas)",
    "escalera_ofertas": "_DIM_PRECIOS.csv (derivada)",
    "apertura_nivel": "_DIM_CONJUNTOS.csv / _DIM_VOCABULARIO.csv (nivel_conciencia del angulo ganador)",
    "mensaje_prellenado_anuncio": "_DIM_MERCADOS.csv (registro_sanitario) + _DIM_PRODUCTOS.csv "
                                   "(producto_display)",
    "video_1": "operador / Ads/MEDIA_[PK]", "video_2": "operador / Ads/MEDIA_[PK]",
    "lista_infografias": "operador / Ads/MEDIA_[PK]",
    "fecha_generacion": "derivada",
}

# Plural explicito de las unidades de duracion. "mes" ya termina en "s", asi que
# pluralizar por sufijo producia "Tratamiento 2 mes (2 frascos)".
PLURAL = {"mes": "meses", "día": "días", "dia": "dias",
          "semana": "semanas", "meses": "meses", "días": "días",
          "dias": "dias", "semanas": "semanas"}

# Nombres de archivo de media: se marcan para declarar, no bloquean (ver resolver()).
MEDIA = ("video_1", "video_2", "lista_infografias")

# Opcionales: la oracion funciona con o sin ellas.
OPCIONALES = ("recaida", "razon_tier_alto", "apertura_nivel")

# ETAPA-5 Paso 3: la apertura del flujo dedicado coincide con el nivel de conciencia del
# angulo ganador (_DIM_CONJUNTOS.csv, vocabulario en _DIM_VOCABULARIO.csv). Este dict es el
# UNICO dueno del texto de la regla — ETAPA-5.md y la plantilla apuntan aca, no la repiten.
NIVELES_APERTURA = {
    "1": ('NIVEL DE CONCIENCIA 1 del angulo ganador (no sabe la causa): el Video 1 y la 1a '
          'infografia EDUCAN — explican la causa del sintoma antes de hablar del producto.'),
    "2": ('NIVEL DE CONCIENCIA 2 del angulo ganador (sabe el problema, no la solucion): '
          'dolor + "eso tiene solucion". El producto es la respuesta.'),
    "3A": ('NIVEL DE CONCIENCIA 3A del angulo ganador (conoce el producto, teme comprar): '
           'reducir friccion desde el arranque — contraentrega, garantia, prueba social.'),
    "3B": ('NIVEL DE CONCIENCIA 3B del angulo ganador (conoce el producto, compara ofertas): '
           'anclar la oferta desde el arranque.'),
}

# Prohibiciones de PLANTILLAS_FLUJO_BOT.md seccion 5, corridas sobre el texto renderizado.
PROHIBIDO = [
    (r"cu[aá]l de estas situaciones se parece",
     "PREGUNTA FILTRO DE DOLOR: el filtrado del avatar ocurre en el ANUNCIO."),
    (r"\b(?:cura|curar|elimina el|erradica)\b", "VERBO MEDICO PROHIBIDO."),
]


RE_GARANTIA = re.compile(
    r"(\d+)\s*d[ií]as?\s+de\s+garant[ií]a|garant[ií]a\s+(?:de\s+)?(\d+)\s*d[ií]as?", re.I)


def plazos_de_garantia(copy):
    """Los plazos de garantia DISTINTOS que aparecen en el copy.

    Va uno solo, igual en los tres escalones. Repetir el mismo plazo es correcto; dos
    plazos distintos en el mismo flujo es una oferta que el operador no autorizo.
    """
    return sorted({int(a or b) for a, b in RE_GARANTIA.findall(copy)})


def leer(nombre, carpeta=PROD):
    ruta = os.path.join(carpeta, nombre)
    if not os.path.exists(ruta):
        return []
    with open(ruta, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def plantilla():
    """Extrae el bloque literal de la seccion 3 de PLANTILLAS_FLUJO_BOT.md.

    Se lee del archivo y no se copia aca a proposito: el texto fijo tiene un dueno.
    """
    if not os.path.exists(PLANTILLA):
        sys.exit("FALTA la plantilla: DOCTRINA/PLANTILLAS_FLUJO_BOT.md")
    texto = open(PLANTILLA, encoding="utf-8").read()
    corte = texto.find("## 3. LA PLANTILLA")
    if corte < 0:
        sys.exit("La plantilla no tiene la seccion '## 3. LA PLANTILLA'")
    bloques = re.findall(r"```\n(.*?)\n```", texto[corte:], re.S)
    if not bloques:
        sys.exit("La seccion 3 no tiene bloque de codigo con el layout")
    return bloques[0]


def escalera(pk, fila, simbolo, moneda="GTQ"):
    """Construye la escalera de ofertas desde _DIM_PRECIOS.csv.

    La ARQUITECTURA sale del CSV (columna `etiqueta`: 1x/2x/3x, 2X1, 4X2), no de una
    suposicion de 3 unidades iguales: los productos de uso unico no la soportan
    (ETAPA-1 Paso 2). Ningun precio se tipea: el bot en vivo de CLEARSTEM cobra
    Q198/Q289/Q389 —lo que manda Dropi— mientras 1_HACER_MANUAL.txt dice Q199/Q299/Q399.
    El separador de miles sale de la moneda del mercado (COP: punto, resto: coma).
    """
    filas = [r for r in leer("_DIM_PRECIOS.csv")
             if r["producto_key"] == pk and r.get("estado", "").upper() == "ACTIVO"]
    if not filas:
        return None, "sin filas ACTIVO en _DIM_PRECIOS.csv"
    filas.sort(key=lambda r: float(r["precio_q"]))

    envase = (fila.get("envase") or "").strip()
    dur = (fila.get("duracion_1u") or "").strip()
    m_dur = re.match(r"^(\d+)\s+(mes|meses|d[ií]a|d[ií]as|semana|semanas)$", dur)

    num = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]
    regalo = ["\U0001f6fb", "\U0001f381", "\U0001f381\U0001f381"]
    lineas, ultimo = [], len(filas) - 1

    for i, r in enumerate(filas):
        etq = (r.get("etiqueta") or "").strip()
        n_u = int(r["unidades"])
        escalar = re.match(r"^(\d+)x$", etq, re.I)
        if escalar and m_dur:
            k, unidad = int(m_dur.group(1)) * n_u, m_dur.group(2).lower()
            if k > 1:
                # "mes" ya termina en "s": pluralizar por sufijo daba "Tratamiento 2 mes".
                unidad = PLURAL.get(unidad, unidad)
            titulo = "Tratamiento %d %s (%d %s%s)" % (
                k, unidad, n_u, envase, "s" if n_u > 1 and envase else "")
        elif escalar:
            titulo = "Tratamiento (%d %s%s)" % (
                n_u, envase, "s" if n_u > 1 and envase else "")
        else:
            titulo = "Oferta %s" % etq if etq else "Opcion %d" % (i + 1)

        precio = float(r["precio_q"])
        miles = "." if moneda == "COP" else ","
        linea = "%s %s → %s%s + %s ENVÍO TOTALMENTE GRATIS" % (
            num[min(i, 4)], titulo, simbolo, format(int(round(precio)), ",").replace(",", miles),
            regalo[min(i, 2)])
        if i == ultimo and len(filas) > 1:
            linea += ("\n   LA MÁS ELEGIDA ⭐ (tratamiento completo) "
                      "— y lo mejor, pagás al recibir \U0001f60a")
        elif i == ultimo - 1 and len(filas) > 2:
            linea += "\n   OFERTA IRRESISTIBLE \U0001f970\U0001f447"
        lineas.append(linea)

    aviso = None
    if not m_dur and dur:
        aviso = ("duracion_1u='%s' no es multiplicable: la escalera se rinde sin dias "
                 "(permitido por ETAPA-5)" % dur)
    return "\n\n".join(lineas), aviso


def es_flujo_dedicado(pk):
    """True si el producto ya paso F1: existe al menos un conjunto con fase != 'FASE1'.

    En F1 el bot es UNICO PARAGUAS (decision operador 23-sep: nunca dos bots en F1). Sin
    ese cruce de fase no hay angulo ganador que abra la conversacion, asi que la apertura
    por nivel de conciencia (ETAPA-5 Paso 3) no aplica todavia.
    """
    return any(r["producto_key"] == pk and r.get("fase") != "FASE1"
               for r in leer("_DIM_CONJUNTOS.csv"))


def nivel_conciencia_angulo(pk, angulo_key):
    """Nivel de conciencia del angulo ganador, normalizado con los alias de _DIM_VOCABULARIO.csv.

    Devuelve (nivel, None) si se resolvio a un unico nivel valido, o (None, razon) si falta,
    es ambiguo ("3" a secas mapea a REVISAR: no distingue 3A de 3B) o los conjuntos del
    angulo no coinciden entre si.
    """
    alias = {r["valor"]: (r["mapea_a"] or r["valor"]) for r in leer("_DIM_VOCABULARIO.csv")
             if r["eje"] == "nivel_conciencia"}
    vistos = set()
    for r in leer("_DIM_CONJUNTOS.csv"):
        if r["producto_key"] != pk or r["angulo_key"] != angulo_key:
            continue
        if (r.get("estado") or "").upper() != "ACTIVO":
            continue
        crudo = (r.get("nivel_conciencia") or "").strip()
        if crudo:
            vistos.add(alias.get(crudo, crudo))
    if not vistos:
        return None, ("sin nivel_conciencia declarado en los conjuntos ACTIVO de %s/%s"
                       % (pk, angulo_key))
    if "REVISAR" in vistos or len(vistos) > 1:
        return None, ("nivel_conciencia ambiguo o en conflicto en %s/%s: %s"
                       % (pk, angulo_key, ", ".join(sorted(vistos))))
    return vistos.pop(), None


def angulo_ganador_f2(pk):
    """El angulo que el flujo DEDICADO debe abrir: el que quedo FIJO en el testeo de
    CONCEPTOS de FASE 2 (doctrina CLAUDE.md "1 angulo ganador x 10 CONCEPTOS"), no el de mas
    ventas historicas.

    Fuente: `_DIM_CREATIVOS.csv`. Una fila con `concepto_key` real (no vacio, no
    SIN_CLASIFICAR) es una pieza de un blueprint de concepto — la FABRICA (etapa-9) solo los
    asigna a un angulo que YA esta en testeo de conceptos o ya lo gano (FASE 2 o su escalado),
    nunca a un angulo todavia en el paraguas de FASE 1. Agrupar esas filas por `angulo_key` da
    el angulo fijo de esa fase sin re-derivarlo de ventas ni de `_DIM_CONJUNTOS.csv` (esa
    columna no distingue FASE2 de su escalado con el mismo criterio en todos los productos:
    ver hallazgo T5).

    Devuelve (angulo, None) con exactamente un angulo distinto · (None, None) si todavia no
    hay ninguna fila asi (el producto sigue en el paraguas de FASE 1: usar el criterio
    historico) · (None, razon) si hay MAS DE UNO (bloquea: un flujo dedicado no puede abrir
    con dos angulos a la vez)."""
    angulos = sorted({
        (r.get("angulo_key") or "").strip()
        for r in leer("_DIM_CREATIVOS.csv")
        if r.get("producto_key") == pk
        and (r.get("concepto_key") or "").strip().upper() not in ("", "SIN_CLASIFICAR")
        and (r.get("angulo_key") or "").strip()
    })
    if not angulos:
        return None, None
    if len(angulos) > 1:
        return None, ("%d angulos distintos con concepto de FASE 2 en _DIM_CREATIVOS.csv "
                       "(%s) — el flujo dedicado necesita UN angulo ganador fijo"
                       % (len(angulos), ", ".join(angulos)))
    return angulos[0], None


def resolver(pk):
    """Devuelve (valores, faltantes, avisos). No escribe nada."""
    flujo = {r["producto_key"]: r for r in leer("_DIM_FLUJO_BOT.csv")}
    if pk not in flujo:
        return None, [("fila completa", "_DIM_FLUJO_BOT.csv")], []
    fila = flujo[pk]

    mercados = {r["mercado"]: r for r in leer("_DIM_MERCADOS.csv")}
    merc = mercados.get((fila.get("mercado") or "").strip())
    if not merc:
        return None, [("mercado '%s'" % fila.get("mercado"), "_DIM_MERCADOS.csv")], []

    v, avisos = {}, []
    v.update({k: (merc.get(k) or "").strip() for k in
              ("pais", "pais_cobertura", "persona", "simbolo", "unidad_geo",
               "unidad_local", "transportadoras", "dias_entrega", "dias_espera_casa")})
    for k in ("nombre_tienda", "nombre_asesor", "producto_display", "envase",
              "duracion_1u", "dias_resultado", "mecanismo_1", "mecanismo_2",
              "prueba_social", "garantia_texto", "dolor_angulo", "solucion_fallida",
              "recaida", "sintoma_superficial", "consecuencia_emocional", "area_cuidado",
              "verbo_tratar", "resultado_sostenido", "razon_tier_alto",
              "n_infografias", "n_testimonios", "fuente_testimonios"):
        v[k] = (fila.get(k) or "").strip()

    # Mensaje prellenado del anuncio Click-to-WhatsApp (operador 23-sep: el enrutamiento del
    # chat al producto es por el ID del anuncio/conjunto, NUNCA por este texto, asi que puede
    # variar libremente). Se declara y deriva, nunca se escribe a mano por producto: nombre del
    # producto + registro sanitario del mercado. El MCP `ads_create_creative` no tiene campo
    # para esto (DOCTRINA/MCP_PLAYBOOK.md / skill `publicar-meta` paso 3): se configura a mano
    # en Ads Manager, por eso va como instruccion `>>`, nunca como campo de LucidBot.
    registro = (merc.get("registro_sanitario") or "").strip()
    v["mensaje_prellenado_anuncio"] = (
        "Hola, quiero más información de %s con %s" % (v["producto_display"], registro)
        if v.get("producto_display") and registro else "")

    # Angulo del flujo: el ganador FIJO de FASE 2 manda (angulo_ganador_f2, arriba). Sin
    # ninguna pieza de concepto de FASE 2 todavia, el producto sigue en el paraguas de FASE 1
    # y se usa el criterio historico (mas ventas acumuladas) que nunca gatea nada mas alla
    # del titulo del flujo. Un empate ambiguo entre varios angulos de FASE 2 BLOQUEA (se
    # agrega a `faltan` mas abajo, junto a la razon completa): nunca se elige por su cuenta.
    angulo_f2, razon_f2 = angulo_ganador_f2(pk)
    if angulo_f2:
        v["angulo_nombre"] = angulo_f2
    elif razon_f2:
        v["angulo_nombre"] = ""
    else:
        cand = [r for r in leer("_ESTADO_ANGULOS.csv") if r["producto_key"] == pk]
        def ventas(r):
            try:
                return float(r.get("ventas_acum") or 0)
            except ValueError:
                return 0.0
        v["angulo_nombre"] = max(cand, key=ventas)["angulo_key"] if cand else "PARAGUAS F1"

    moneda = (merc.get("moneda") or "GTQ").strip()
    esc, aviso_esc = escalera(pk, fila, v["simbolo"] or "Q", moneda)
    v["escalera_ofertas"] = esc or ""
    if aviso_esc:
        avisos.append(aviso_esc)

    v["fecha_generacion"] = datetime.date.today().isoformat()

    # MEDIA: son nombres de archivo, no texto de venta. No bloquean y se marcan.
    # La distincion es deliberada: un nombre de archivo ausente es visible al pegar en
    # Lucid y no puede cambiar el copy en silencio, que es el fallo que este script
    # existe para cerrar. Tampoco se elige el archivo por orden alfabetico: esa fue
    # exactamente la falla de `armar_prompts_fase2.py` del 07-sep-2026.
    for k in MEDIA:
        v[k] = "‹DECLARAR: %s — %s›" % (k, DUENO[k])

    usadas = set(re.findall(r"\{\{(\w+)\}\}", plantilla()))
    faltan = [(k, DUENO.get(k, "sin dueno declarado"))
              for k in sorted(usadas) if not v.get(k)]
    # `recaida` y `razon_tier_alto` son opcionales: CLEARSTEM las usa, TINNIDROP no.
    faltan = [f for f in faltan if f[0] not in OPCIONALES]
    # angulo_nombre ambiguo entre varios angulos de FASE 2: la razon completa (que angulos y
    # cuantos) manda sobre el mensaje generico de DUENO.
    if razon_f2:
        faltan = [f for f in faltan if f[0] != "angulo_nombre"]
        faltan.append(("angulo_nombre", "_DIM_CREATIVOS.csv (angulo de FASE 2) — %s" % razon_f2))

    # Apertura por nivel de conciencia (ETAPA-5 Paso 3): solo aplica al flujo DEDICADO. En
    # F1 (paraguas) no hay angulo ganador todavia y la linea se omite sin bloquear. En
    # dedicado, un nivel ausente/ambiguo/en conflicto SI bloquea (a diferencia de OPCIONALES,
    # que nunca bloquea): se agrega a mano despues del filtro de arriba.
    v["apertura_nivel"] = ""
    if es_flujo_dedicado(pk):
        nivel, razon = nivel_conciencia_angulo(pk, v["angulo_nombre"])
        if nivel:
            v["apertura_nivel"] = NIVELES_APERTURA[nivel]
        else:
            faltan.append(("apertura_nivel", "%s — %s" % (DUENO["apertura_nivel"], razon)))

    return v, faltan, avisos


def render(v):
    txt = plantilla()
    # apertura_nivel vive en su PROPIA linea de instruccion ('>> {{apertura_nivel}}'), a
    # diferencia de recaida/razon_tier_alto que van dentro de una oracion. Si esta ausente
    # (flujo paraguas, sin angulo ganador), la linea entera se quita ANTES de sustituir: el
    # loop de abajo ya reemplazaria el token por "" y dejaria un '>> ' vacio y colgado.
    if not v.get("apertura_nivel"):
        txt = re.sub(r"\n[ \t]*>>[ \t]*\{\{apertura_nivel\}\}[ \t]*\n", "\n", txt)
    # `recaida`/`razon_tier_alto` OPCIONALES: la limpieza corre ANTES de la sustitucion
    # generica de abajo, sobre el token `{{...}}` todavia literal. Corrida despues (como
    # antes), el loop generico ya habia puesto v[k]="" en su lugar y el patron que esta
    # limpieza busca ("{{recaida}}") ya no existia — dejaba "— ." colgando en el INT 2 de
    # un flujo sin recaida (hallazgo T5).
    if not v.get("recaida"):
        txt = txt.replace(" — {{recaida}}", "")
    if not v.get("razon_tier_alto"):
        txt = re.sub(r"\n[ \t]*\{\{razon_tier_alto\}\}[ \t]*\n", "\n", txt)
    for k, val in v.items():
        txt = txt.replace("{{%s}}" % k, val)
    txt = mercado.aplicar_persona(txt, v.get("persona", ""))
    return txt


def es_instruccion(linea):
    """Una linea de INSTRUCCION empieza con '>>'. Nunca se pega en LucidBot.

    Es una de las tres notaciones de la plantilla, y las tres tienen formas que no se
    parecen entre si: `{{variable}}` se sustituye, `<<BLOQUE:x>>` lo escribe etapa-5 y
    `>>` es una nota. Una forma, un significado.
    """
    return linea.lstrip().startswith(">>")


def solo_copy(txt):
    """Deja solo lo que ve el cliente, para correrle las prohibiciones encima.

    Las instrucciones CITAN las frases prohibidas para explicarlas (la pregunta filtro
    A/B/C/D, por ejemplo). Corriendo las prohibiciones sobre el archivo entero, la propia
    advertencia disparaba el rechazo: un gate que se muerde la cola.
    """
    return "\n".join(l for l in txt.splitlines()
                     if not es_instruccion(l)
                     and not re.match(r"\s*[═─]{3,}", l))


def para_pegar(txt):
    """El flujo sin ninguna linea de instruccion: lo que se copia campo por campo."""
    fuera, previa_vacia = [], False
    for l in txt.splitlines():
        if es_instruccion(l):
            continue
        vacia = not l.strip()
        if vacia and previa_vacia:
            continue
        fuera.append(l)
        previa_vacia = vacia
    return "\n".join(fuera).strip() + "\n"


# Los titulos de bloque que declara la plantilla (seccion 3): cada uno abre un campo o un mensaje
# que se pega por separado en LucidBot. Una linea en mayusculas DENTRO de un mensaje («OFERTAS
# HASTA AGOTAR») no es un titulo: por eso la lista es cerrada y no una heuristica de mayusculas.
# Un titulo nuevo que no este aca no pierde texto: su contenido queda dentro del bloque anterior
# (test_gen_flujo_bot.py lo vigila comparando contra para_pegar()).
RE_TITULO_BLOQUE = re.compile(
    r"^(ELEMENTO \S+ — |INTERACCIÓN \d+ — |TEXTO · |TESTIMONIOS \(|AUDIO \(|INFOGRAFÍAS \(|M\d+ — |"
    r"(DESCRIPCIÓN|MODO DE USO|CARACTERÍSTICAS TÉCNICAS|CONTENIDO DEL PAQUETE):$)")
RE_SECCION = re.compile(r"^═+ (.+?) ═+$")
RE_RAYA = re.compile(r"^═+$")
RE_BLOQUE_JUICIO = re.compile(r"<<BLOQUE:(\w+)>>")


def _limpiar_pegar(lineas):
    fuera, previa_vacia = [], True
    for l in lineas:
        vacia = not l.strip()
        if vacia and previa_vacia:
            continue
        fuera.append(l)
        previa_vacia = vacia
    return "\n".join(fuera).strip()


def estructura(txt):
    """El flujo renderizado, partido como se pega: secciones → bloques.

    Cada bloque trae `pegar` (SIN ninguna linea `>>`), `instrucciones` (las `>>`, sin el
    prefijo) y `pendientes` (los <<BLOQUE:x>> que escribe etapa-5). Es la misma regla de
    `para_pegar()`, aplicada por bloque: una forma, un significado.
    """
    encabezado, secciones = {"lineas": [], "instrucciones": []}, []
    seccion = bloque = None
    for linea in txt.splitlines():
        if RE_RAYA.match(linea):
            continue
        m = RE_SECCION.match(linea)
        if m:
            seccion = {"titulo": m.group(1).strip(), "instrucciones": [], "bloques": []}
            secciones.append(seccion)
            bloque = None
            continue
        if seccion is None:
            if es_instruccion(linea):
                encabezado["instrucciones"].append(linea.lstrip()[2:].strip())
            elif linea.strip():
                encabezado["lineas"].append(linea.strip())
            continue
        if not es_instruccion(linea) and RE_TITULO_BLOQUE.match(linea):
            bloque = {"titulo": linea.strip(), "_lineas": [], "instrucciones": []}
            seccion["bloques"].append(bloque)
            continue
        if es_instruccion(linea):
            (bloque or seccion)["instrucciones"].append(linea.lstrip()[2:].strip())
            continue
        if bloque is None:
            if not linea.strip():
                continue
            bloque = {"titulo": seccion["titulo"], "_lineas": [], "instrucciones": []}
            seccion["bloques"].append(bloque)
        bloque["_lineas"].append(linea)
    for s in secciones:
        for b in s["bloques"]:
            b["pegar"] = _limpiar_pegar(b.pop("_lineas"))
            b["pendientes"] = RE_BLOQUE_JUICIO.findall(b["pegar"])
    return {"encabezado": encabezado, "secciones": secciones}


# Clase 22-ago regla D / ETAPA-5 Paso 1: 6-8 propuestas de valor mueven el cierre mas que
# hooks o testimonios. Viven DENTRO de las infografias (imagenes), nunca en el texto que se
# pega en LucidBot — por eso esta cuenta no las lee de _DIM_FLUJO_BOT.csv (un dato ahi
# bloquearia CLEARSTEM/TINNIDROP hasta que el operador declare la columna, y esta tarea no
# toca PRODUCTOS/*.csv) sino de la seccion "PROPUESTAS DE VALOR" que etapa-guardar-producto
# persiste en 2_DATA_PRODUCTO.txt (ver propuestas_persistidas()), con --propuestas ARCHIVO como
# override manual de una sola corrida. Sin ninguna de las dos, la cuenta queda PENDIENTE: nunca
# bloquea.
MIN_PROPUESTAS_VALOR = 6
AVISO_PROPUESTAS_VALOR = 20

# Cabecera de la seccion que persiste etapa-guardar-producto en 2_DATA_PRODUCTO.txt (ARCHIVO 2,
# formato "━━━ TITULO ━━━" — mismo estilo que COSTEO/COMPONENTES en ese archivo). Cierra en la
# proxima linea que abre con "━" o en el fin del archivo: no depende de una longitud fija de raya.
RE_SECCION_PROPUESTAS = re.compile(r"^━+\s*PROPUESTAS DE VALOR\b.*$", re.M)
RE_SECCION_2DATA = re.compile(r"^━+", re.M)


def carpeta_de(pk):
    """slug_carpeta desde _DIM_PRODUCTOS.csv. Invariante 10: la carpeta nunca se adivina por el
    nombre — mismo patron que armar_prompts_fase2.py:carpeta_de()."""
    for r in leer("_DIM_PRODUCTOS.csv"):
        if r.get("producto_key") == pk:
            return (r.get("slug_carpeta") or "").strip() or None
    return None


def propuestas_persistidas(pk):
    """Las propuestas de valor que etapa-guardar-producto ya persistio en
    PRODUCTOS/[carpeta]/2_DATA_PRODUCTO.txt, seccion "PROPUESTAS DE VALOR" (una por linea,
    transcritas verbatim del <<BLOQUE:propuestas_valor>> de etapa-5, invariante 3).

    None si no hay slug_carpeta, no existe el archivo o no existe la seccion — nunca bloquea,
    lo cuenta validar_propuestas_valor() igual que "no declaradas todavia".
    """
    carpeta = carpeta_de(pk)
    if not carpeta:
        return None
    ruta = os.path.join(PROD, carpeta, "2_DATA_PRODUCTO.txt")
    if not os.path.exists(ruta):
        return None
    texto = open(ruta, encoding="utf-8").read()
    m = RE_SECCION_PROPUESTAS.search(texto)
    if not m:
        return None
    resto = texto[m.end():]
    fin = RE_SECCION_2DATA.search(resto)
    return resto[:fin.start()] if fin else resto


def propuestas_valor_lineas(texto):
    """Una propuesta de valor por linea. Vacias y lineas '>>' (instruccion) no cuentan."""
    if not texto:
        return []
    return [l.strip() for l in texto.splitlines() if l.strip() and not es_instruccion(l)]


def validar_propuestas_valor(texto):
    """(bloqueo, aviso). `texto=None` (no declaradas todavia) SIEMPRE aviso, nunca bloqueo:
    los productos vivos sin este dato declarado (CLEARSTEM, TINNIDROP) siguen renderizando."""
    if texto is None:
        return None, ("propuestas_valor no declaradas todavia — etapa-5 Paso 1 escribe 6-8 en "
                       "<<BLOQUE:propuestas_valor>> (PENDIENTE, no bloquea)")
    n = len(propuestas_valor_lineas(texto))
    if n < MIN_PROPUESTAS_VALOR:
        return ("propuestas_valor: %d declarada(s), van 6-8 (ETAPA-5 Paso 1 / clase 22-ago "
                "regla D — lo que mas mueve el cierre)" % n), None
    if n > AVISO_PROPUESTAS_VALOR:
        return None, ("propuestas_valor: %d declaradas, arriba de %d puede saturar las "
                       "infografias" % (n, AVISO_PROPUESTAS_VALOR))
    return None, None


def prohibiciones(txt, persona=""):
    copy = solo_copy(txt)
    hallados = []
    for patron, motivo in PROHIBIDO:
        if re.search(patron, copy, re.I | re.S):
            hallados.append(motivo)
    if persona == "tuteo":
        resto = mercado.voseo_restante(copy)
        if resto:
            hallados.append("VOSEO EN MERCADO DE TUTEO: %s" % ", ".join(resto))
    plazos = plazos_de_garantia(copy)
    if len(plazos) > 1:
        hallados.append("DOS PLAZOS DE GARANTIA DISTINTOS (%s dias): va UNO solo, igual "
                        "en los tres escalones" % ", ".join(str(p) for p in plazos))
    sueltas = sorted(set(re.findall(r"\{\{(\w+)\}\}", txt)))
    if sueltas:
        hallados.append("VARIABLES SIN RESOLVER en la salida: %s" % ", ".join(sueltas))
    return hallados


def una_json(pk, parcial=False, propuestas=None):
    """--json: el flujo por bloques para la app. No escribe. Bloquea igual que el render."""
    v, faltan, avisos = resolver(pk)
    efectivas = propuestas if propuestas is not None else propuestas_persistidas(pk)
    bloqueo_prop, aviso_prop = validar_propuestas_valor(efectivas)
    if aviso_prop:
        avisos.append(aviso_prop)
    salida = {"producto_key": pk, "ok": False, "parcial": parcial, "avisos": avisos,
              "faltan": [{"variable": k, "lo_produce": d} for k, d in faltan], "prohibiciones": []}
    if v is None or (faltan and not parcial):
        print(json.dumps(salida, ensure_ascii=False, indent=2))
        return False
    for k, d in faltan:
        v[k] = "‹PENDIENTE: %s — %s›" % (k, d)
    txt = render(v)
    salida["prohibiciones"] = prohibiciones(txt, v.get("persona", ""))
    if bloqueo_prop:
        salida["prohibiciones"].append(bloqueo_prop)
    if not salida["prohibiciones"]:
        salida["ok"] = True
        salida.update(estructura(txt))
    print(json.dumps(salida, ensure_ascii=False, indent=2))
    return salida["ok"]


def una(pk, escribir=True, parcial=False, copy=False, propuestas=None):
    v, faltan, avisos = resolver(pk)
    efectivas = propuestas if propuestas is not None else propuestas_persistidas(pk)
    bloqueo_prop, aviso_prop = validar_propuestas_valor(efectivas)
    if aviso_prop:
        avisos.append(aviso_prop)
    print("\n─── %s ───" % pk)
    for a in avisos:
        print("  aviso: %s" % a)
    if v is None or (faltan and not parcial):
        print("  BLOQUEADO — falta %d dato(s):" % len(faltan))
        for k, d in faltan:
            print("    · %-24s ← lo produce: %s" % (k, d))
        return False
    if faltan:
        for k, d in faltan:
            v[k] = "‹PENDIENTE: %s — %s›" % (k, d)
        print("  PARCIAL — %d dato(s) marcados como PENDIENTE" % len(faltan))

    txt = render(v)
    malos = prohibiciones(txt, v.get("persona", ""))
    if bloqueo_prop:
        malos.append(bloqueo_prop)
    if malos:
        print("  RECHAZADO por prohibiciones:")
        for m in malos:
            print("    · %s" % m)
        return False

    if copy:
        print(para_pegar(txt))
        return True

    if not escribir:
        print("  PASA (validacion, no se escribio)")
        return True

    dest_dir = os.path.join(PROD, pk)
    if not os.path.isdir(dest_dir):
        print("  BLOQUEADO — no existe la carpeta %s" % dest_dir)
        return False
    dest = os.path.join(dest_dir, "FLUJO_LUCIDBOT.md")
    with open(dest, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(txt)
    print("  escrito %s (%d caracteres)" % (os.path.relpath(dest, BASE), len(txt)))
    return True


def main():
    args = [a for a in sys.argv[1:]]
    parcial = "--parcial" in args
    validar = "--validar" in args
    todo = "--todo" in args
    copy = "--copy" in args

    propuestas = None
    if "--propuestas" in args:
        i = args.index("--propuestas")
        if i + 1 >= len(args):
            print("--propuestas necesita una ruta de archivo (una propuesta por linea)",
                  file=sys.stderr)
            return 2
        with open(args[i + 1], encoding="utf-8") as fh:
            propuestas = fh.read()
        del args[i:i + 2]

    pks = [a for a in args if not a.startswith("--")]

    if "--json" in args:
        if len(pks) != 1 or validar or todo or copy:
            print("--json va con UN producto_key y sin --validar / --todo / --copy", file=sys.stderr)
            return 2
        return 0 if una_json(pks[0], parcial=parcial, propuestas=propuestas) else 1

    if propuestas is not None and (len(pks) != 1 or validar or todo):
        print("--propuestas va con UN producto_key y sin --validar / --todo", file=sys.stderr)
        return 2

    if validar or todo:
        pks = [r["producto_key"] for r in leer("_DIM_FLUJO_BOT.csv")]
    if not pks:
        print(__doc__)
        return 0

    ok = sum(1 for pk in pks
             if una(pk, escribir=not validar, parcial=parcial, copy=copy, propuestas=propuestas))
    if not copy:
        print("\n%d/%d producto(s) %s" % (ok, len(pks),
                                          "pasan" if validar else "renderizados"))
    return 0 if ok == len(pks) else 1


if __name__ == "__main__":
    sys.exit(main())
