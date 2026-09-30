#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen_manual.py — ARMA 1_HACER_MANUAL.txt desde datos que ya existen.

No tipea contenido: lo copia textual de sus duenos.
  Plan derivado del producto  -> gen_lanzador.construir()["productos"] (clave "plan")
  Flujo del bot               -> gen_flujo_bot: resolver -> render -> insertar_bloques ->
                                 prohibiciones -> para_pegar
  Prompts de infografias      -> PRODUCTOS/<carpeta>/INFOGRAFIAS.md
  Carpeta del producto        -> gen_flujo_bot.carpeta_de(pk)

Un dato, un dueno: si algo falta, bloquea nombrando QUE falta y QUIEN lo produce.
Nunca rellena ni inventa.

USO (un "mirar" nunca escribe):
  python Ads/_TOOLS/gen_manual.py <PK>              imprime el manual (exit 1 si bloquea)
  python Ads/_TOOLS/gen_manual.py <PK> --escribir   ademas escribe 1_HACER_MANUAL.txt
  python Ads/_TOOLS/gen_manual.py <PK> --validar    imprime solo LISTO o los bloqueos
"""

import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, OSError):
    pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_flujo_bot as _bot  # noqa: E402
import gen_lanzador as _lanz  # noqa: E402

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROD = os.path.join(BASE, "PRODUCTOS")

RE_INFOGRAFIA = re.compile(r"^<<INFOGRAFIA:(\d+)>>$")

SEP = "\n\n" + "=" * 72 + "\n\n"


def parsear_infografias(texto):
    """{n (str): texto} de un INFOGRAFIAS.md, sin vacias al inicio ni al final.

    ValueError si un n se repite o no esta entre 1 y 6."""
    bloques, nombre, lineas = {}, None, []

    def cerrar():
        if nombre is not None:
            while lineas and not lineas[0].strip():
                lineas.pop(0)
            while lineas and not lineas[-1].strip():
                lineas.pop()
            bloques[nombre] = "\n".join(lineas)

    for linea in texto.splitlines():
        m = RE_INFOGRAFIA.match(linea)
        if m:
            cerrar()
            nombre = m.group(1)
            if nombre in bloques:
                raise ValueError("infografia repetida: %s" % nombre)
            if nombre not in ("1", "2", "3", "4", "5", "6"):
                raise ValueError("infografia fuera de 1..6: %s" % nombre)
            lineas = []
        elif nombre is not None:
            lineas.append(linea)
    cerrar()
    return bloques


def reunir(pk):
    """Junta las fuentes. Devuelve (datos, bloqueos): `datos` trae "plan", "flujo"
    (texto pegable) e "infografias"; `bloqueos` nombra QUE falta y QUIEN lo produce."""
    bloqueos = []
    datos = {"pk": pk, "plan": None, "flujo": "", "infografias": {}}

    modelo = _lanz.construir()
    fila = next((p for p in modelo["productos"] if p["producto_key"] == pk), None)
    plan = (fila or {}).get("plan")
    if not plan:
        bloqueos.append("_PLAN.json — etapa-6")
    else:
        datos["plan"] = plan
        for b in plan.get("bloqueantes", []):
            bloqueos.append("%s — %s" % (b.get("que"), b.get("quien")))

    v, faltan, _avisos = _bot.resolver(pk)
    if v is None or faltan:
        for k, d in faltan:
            bloqueos.append("%s — %s" % (k, d))
    else:
        try:
            bloques = _bot.bloques_persistidos(pk)
        except ValueError as error:
            bloqueos.append("BLOQUES_BOT.md: %s — etapa-5" % error)
            bloques = None
        if bloques is not None:
            txt = _bot.render(v)
            txt, pendientes = _bot.insertar_bloques(txt, bloques)
            if pendientes:
                bloqueos.append("BLOQUES_BOT.md: %s — etapa-5" % ", ".join(pendientes))
            for hallazgo in _bot.prohibiciones(txt, v.get("persona", "")):
                bloqueos.append(hallazgo)
            datos["flujo"] = _bot.para_pegar(txt)

    carpeta = _bot.carpeta_de(pk)
    ruta_inf = os.path.join(PROD, carpeta, "INFOGRAFIAS.md") if carpeta else None
    if not ruta_inf or not os.path.isfile(ruta_inf):
        bloqueos.append("INFOGRAFIAS.md: falta el archivo — etapa-4")
    else:
        with open(ruta_inf, encoding="utf-8") as fh:
            try:
                infografias = parsear_infografias(fh.read())
            except ValueError as error:
                bloqueos.append("INFOGRAFIAS.md: %s — etapa-4" % error)
                infografias = {}
        datos["infografias"] = infografias
        faltan_inf = [n for n in ("1", "2", "3") if n not in infografias]
        if faltan_inf:
            bloqueos.append("INFOGRAFIAS.md: faltan %s — etapa-4" % ", ".join(faltan_inf))

    return datos, bloqueos


def _lineas(*lineas):
    return [l for l in lineas if l]


def render_manual(datos):
    """Funcion PURA (no lee disco): el texto completo del manual, secciones A..F."""
    plan = datos.get("plan") or {}
    conjuntos = sorted(plan.get("conjuntos") or [], key=lambda c: (c.get("n") is None, c.get("n")))
    infografias = datos.get("infografias") or {}
    flujo = datos.get("flujo") or ""

    encabezado = _lineas(
        "HACER MANUAL — %s | %s" % (plan.get("nombre"), plan.get("fase_nombre")),
        "FanPage: %s (page_id %s) · Cuenta: %s" % (plan.get("pagina"), plan.get("page_id"),
                                                   plan.get("cuenta")),
        "GENERADO por Ads/_TOOLS/gen_manual.py — no editar a mano: se corrige el dato de origen",
        "y se vuelve a generar.",
    )

    sec_a = _lineas(
        "A. CHECKLIST",
        "[ ] 1. Generar las imágenes de los anuncios (sección B)",
        "[ ] 2. Generar las infografías del bot (sección C)",
        "[ ] 3. Armar el flujo en LucidBot (sección D) y probarlo desde otro WhatsApp",
        "[ ] 4. Crear la campaña en Meta (sección E)",
        "[ ] 5. Registrar en el sistema (sección F)",
    )

    sec_b = ["B. CREATIVOS DE LOS ANUNCIOS"]
    for c in conjuntos:
        sec_b.append("AD %s — %s · formato: %s · archivo: %s · precio en el ad: %s"
                     % (c.get("n"), c.get("angulo_titulo"), c.get("formato"),
                        c.get("archivo_creativo"), "SI" if c.get("lleva_precio") else "NO"))
        if c.get("prompt_imagen"):
            sec_b.append(c["prompt_imagen"])

    sec_c = ["C. INFOGRAFÍAS DEL BOT (van dentro del flujo, no en Meta)"]
    for n in sorted(infografias, key=int):
        sec_c.append("INFOGRAFÍA %s:" % n)
        sec_c.append(infografias[n])

    sec_d = ["D. FLUJO LUCIDBOT (copiar cada parte en su campo)", flujo]

    sec_e = ["E. ESTRUCTURA EN META"]
    for camp in plan.get("campanas") or []:
        sec_e.extend(_lineas(
            "Campaña: %s" % camp.get("nombre"),
            "Objetivo: %s" % camp.get("objetivo") if camp.get("objetivo") else None,
            "Presupuesto: %s" % camp.get("presupuesto") if camp.get("presupuesto") else None,
        ))
    lanz = plan.get("lanzamiento") or {}
    if lanz.get("legible"):
        sec_e.append("Lanzamiento: %s a las %s." % (lanz["legible"], lanz.get("hora") or ""))
    for c in conjuntos:
        sec_e.append("%s · presupuesto US$%s/día · edad %s · género %s · %s · %s · precio en el ad %s"
                     % (c.get("nombre"), c.get("presupuesto_usd"), c.get("banda_edad"),
                        c.get("genero"), c.get("formato"), c.get("archivo_creativo"),
                        "SI" if c.get("lleva_precio") else "NO"))
        for a in c.get("anuncios") or []:
            sec_e.append("Anuncio %s: %s" % (a.get("letra"), a.get("nombre")))
        copy = c.get("copy") or {}
        for i, t in enumerate(copy.get("textos") or [], 1):
            sec_e.append("TEXTO PRINCIPAL %d:\n%s" % (i, t))
        for i, t in enumerate(copy.get("titulos") or [], 1):
            sec_e.append("TÍTULO %d:\n%s" % (i, t))
        if copy.get("descripcion"):
            sec_e.append("DESCRIPCIÓN:\n%s" % copy["descripcion"])
    if plan.get("faltantes"):
        sec_e.append("PENDIENTES QUE DECLARA EL LANZADOR:")
        sec_e.extend(plan["faltantes"])

    sec_f = ["F. CALENDARIO Y REGISTRO"]
    for f in plan.get("calendario") or []:
        sec_f.append("%s (%s) — %s · hacer: %s · traer: %s"
                     % (f.get("dia"), f.get("fecha"), f.get("que"), f.get("hace"),
                        f.get("manda") if f.get("manda") is not None else "—"))
    pk = datos.get("pk")
    camp0 = (plan.get("campanas") or [{}])[0]
    sec_f.append('python Ads/_TOOLS/registrar_evento.py --producto %s --evento CAMBIO_BOT '
                 '--motivo "bot cargado en LucidBot" --fuente "operador"' % pk)
    sec_f.append('python Ads/_TOOLS/registrar_evento.py --producto %s --evento LANZAMIENTO '
                 '--fase %s --fecha %s --cuenta %s --campana %s --motivo "lanzamiento" '
                 '--fuente "operador"'
                 % (pk, plan.get("fase"), lanz.get("fecha"), plan.get("cuenta"),
                    camp0.get("nombre")))

    return SEP.join(["\n".join(encabezado), "\n".join(sec_a), "\n".join(sec_b),
                     "\n".join(sec_c), "\n".join(sec_d), "\n".join(sec_e),
                     "\n".join(sec_f)]) + "\n"


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    escribir = "--escribir" in args
    validar = "--validar" in args
    pks = [a for a in args if not a.startswith("--")]
    if len(pks) != 1:
        print(__doc__)
        return 2
    pk = pks[0]

    datos, bloqueos = reunir(pk)
    if bloqueos:
        if validar:
            print("\n".join(bloqueos))
        else:
            print("BLOQUEADO — falta:")
            for b in bloqueos:
                print("  · %s" % b)
        return 1
    if validar:
        print("LISTO")
        return 0
    manual = render_manual(datos)
    if escribir:
        carpeta = _bot.carpeta_de(pk)
        if not carpeta:
            print("BLOQUEADO — falta:")
            print("  · sin slug_carpeta en _DIM_PRODUCTOS.csv — etapa-guardar-producto")
            return 1
        destino = os.path.join(PROD, carpeta, "1_HACER_MANUAL.txt")
        with open(destino, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(manual)
        print("escrito %s" % os.path.relpath(destino, BASE))
        return 0
    print(manual)
    return 0


if __name__ == "__main__":
    sys.exit(main())
