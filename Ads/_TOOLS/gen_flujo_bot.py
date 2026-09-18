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
    "angulo_nombre": "_ESTADO_ANGULOS.csv (angulo ganador)",
    "escalera_ofertas": "_DIM_PRECIOS.csv (derivada)",
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
OPCIONALES = ("recaida", "razon_tier_alto")

# Prohibiciones de PLANTILLAS_FLUJO_BOT.md seccion 5, corridas sobre el texto renderizado.
PROHIBIDO = [
    (r"cu[aá]l de estas situaciones se parece",
     "PREGUNTA FILTRO DE DOLOR: el filtrado del avatar ocurre en el ANUNCIO."),
    (r"(?:cura|curar|elimina el|erradica)\b", "VERBO MEDICO PROHIBIDO."),
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


def escalera(pk, fila, simbolo):
    """Construye la escalera de ofertas desde _DIM_PRECIOS.csv.

    La ARQUITECTURA sale del CSV (columna `etiqueta`: 1x/2x/3x, 2X1, 4X2), no de una
    suposicion de 3 unidades iguales: los productos de uso unico no la soportan
    (ETAPA-1 Paso 2). Ningun precio se tipea: el bot en vivo de CLEARSTEM cobra
    Q198/Q289/Q389 —lo que manda Dropi— mientras 1_HACER_MANUAL.txt dice Q199/Q299/Q399.
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
        linea = "%s %s → %s%s + %s ENVÍO TOTALMENTE GRATIS" % (
            num[min(i, 4)], titulo, simbolo, format(int(round(precio)), ","),
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

    # Angulo ganador: el de mas ventas acumuladas con evidencia, nunca declarado a mano.
    cand = [r for r in leer("_ESTADO_ANGULOS.csv") if r["producto_key"] == pk]
    def ventas(r):
        try:
            return float(r.get("ventas_acum") or 0)
        except ValueError:
            return 0.0
    v["angulo_nombre"] = max(cand, key=ventas)["angulo_key"] if cand else ""

    esc, aviso_esc = escalera(pk, fila, v["simbolo"] or "Q")
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
    return v, faltan, avisos


def render(v):
    txt = plantilla()
    for k, val in v.items():
        txt = txt.replace("{{%s}}" % k, val)
    # Limpia lineas que quedaron vacias por variables opcionales ausentes.
    txt = re.sub(r"\n\s*\{\{(?:recaida|razon_tier_alto)\}\}\s*\n", "\n", txt)
    txt = txt.replace(" — {{recaida}}", "").replace("{{razon_tier_alto}}", "")
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


def prohibiciones(txt):
    copy = solo_copy(txt)
    hallados = []
    for patron, motivo in PROHIBIDO:
        if re.search(patron, copy, re.I | re.S):
            hallados.append(motivo)
    plazos = plazos_de_garantia(copy)
    if len(plazos) > 1:
        hallados.append("DOS PLAZOS DE GARANTIA DISTINTOS (%s dias): va UNO solo, igual "
                        "en los tres escalones" % ", ".join(str(p) for p in plazos))
    sueltas = sorted(set(re.findall(r"\{\{(\w+)\}\}", txt)))
    if sueltas:
        hallados.append("VARIABLES SIN RESOLVER en la salida: %s" % ", ".join(sueltas))
    return hallados


def una_json(pk, parcial=False):
    """--json: el flujo por bloques para la app. No escribe. Bloquea igual que el render."""
    v, faltan, avisos = resolver(pk)
    salida = {"producto_key": pk, "ok": False, "parcial": parcial, "avisos": avisos,
              "faltan": [{"variable": k, "lo_produce": d} for k, d in faltan], "prohibiciones": []}
    if v is None or (faltan and not parcial):
        print(json.dumps(salida, ensure_ascii=False, indent=2))
        return False
    for k, d in faltan:
        v[k] = "‹PENDIENTE: %s — %s›" % (k, d)
    txt = render(v)
    salida["prohibiciones"] = prohibiciones(txt)
    if not salida["prohibiciones"]:
        salida["ok"] = True
        salida.update(estructura(txt))
    print(json.dumps(salida, ensure_ascii=False, indent=2))
    return salida["ok"]


def una(pk, escribir=True, parcial=False, copy=False):
    v, faltan, avisos = resolver(pk)
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
    malos = prohibiciones(txt)
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
    pks = [a for a in args if not a.startswith("--")]

    if "--json" in args:
        if len(pks) != 1 or validar or todo or copy:
            print("--json va con UN producto_key y sin --validar / --todo / --copy", file=sys.stderr)
            return 2
        return 0 if una_json(pks[0], parcial=parcial) else 1

    if validar or todo:
        pks = [r["producto_key"] for r in leer("_DIM_FLUJO_BOT.csv")]
    if not pks:
        print(__doc__)
        return 0

    ok = sum(1 for pk in pks
             if una(pk, escribir=not validar, parcial=parcial, copy=copy))
    if not copy:
        print("\n%d/%d producto(s) %s" % (ok, len(pks),
                                          "pasan" if validar else "renderizados"))
    return 0 if ok == len(pks) else 1


if __name__ == "__main__":
    sys.exit(main())
