# -*- coding: utf-8 -*-
"""verificar_publicacion.py — EL GATE DE LA PUBLICACION: compara lo que Meta TIENE contra lo
que el paquete DECLARO, y escribe los `ad_id` de vuelta al CSV.

POR QUE EXISTE (2026-09-08)
--------------------------
El 06-sep se publico `GTR0_TINNIDROP_F2-CONCEPTOS_20260907` con 10 anuncios. Nadie escribio los
`ad_id` en `_DIM_CREATIVOS.csv`. El 08-sep el sistema leyo la columna vacia y concluyo "10
creativos generados y CERO publicados" — mientras Meta llevaba **$23.46 gastados** en esos 10
anuncios ACTIVE. El diagnostico de la manana era falso y por poco se duplica una campana viva.

La leccion, que vale mas que el caso: **el CSV no es evidencia del estado de Meta.** Es una
anotacion que alguien tiene que escribir, y nadie la escribio. Este script es ese "alguien",
y ya no depende de que un modelo se acuerde.

QUE COMPARA
-----------
    manifiesto (lo declarado)          snapshot (lo que Meta dice que existe)
    ---------------------------        --------------------------------------
    campana por nombre                 ads_get_ad_entities level=campaign
    conjuntos por nombre               ads_get_ad_entities level=adset
    anuncios por nombre                ads_get_ad_entities level=ad

Tres veredictos por objeto:
    OK           declarado y existe   -> se guarda su id
    FALTA        declarado y no esta  -> la secuencia quedo a medias, NO activar
    NO_DECLARADO existe en la campana y el manifiesto no lo pedia -> alguien creo algo a mano,
                 o una corrida anterior lo dejo. Se REPORTA, nunca se borra.

GATE DE ESTADO (T8-2, 23-sep-2026): ademas de existir, todo objeto declarado tiene que estar
PAUSED en el snapshot (invariante 12: nace PAUSED). Un objeto ACTIVE, o sin `effective_status`
en el snapshot (nunca se asume PAUSED por ausencia), bloquea el gate igual que un FALTA —
`objetos_no_pausados()`.

QUE ESCRIBE (solo con --escribir)
---------------------------------
`ad_id` en `PRODUCTOS/_DIM_CREATIVOS.csv`, formato `adA;adB`, una fila por creativo_id — y junto
con el, `estado = PUBLICADO` (ciclo de vida cerrado de ETAPA-9.md: PENDIENTE_GENERAR -> GENERADO
-> PUBLICADO -> RETIRADO; "PUBLICADO exige ad_id real"). Nunca degrada un `RETIRADO`. No toca
`estado_entrega`: ese campo es ENTREGADO/SIN_ENTREGA segun el gasto (DATA_PLAYBOOK.md) y lo
escribe otro proceso, no este gate. Backup previo, escritor CSV real (regla 11 de CLAUDE.md).
Nunca pisa una fila que ya tenga un `ad_id` distinto sin decirlo.

LO QUE ESTE GATE NO REEMPLAZA
-----------------------------
El **control D+1 de tracking** (`MCP_PLAYBOOK` 7.5). Que el anuncio EXISTA no prueba que
TRACKEE. Un conjunto ciego existe, gasta, trae conversaciones reales y marca 0 ventas para
siempre — y ese cero es un artefacto, no un veredicto (APR-034). Al dia siguiente hay que
cruzar Meta contra LucidSales conjunto por conjunto.

USO
    python Ads/_TOOLS/verificar_publicacion.py --producto TINNIDROP --fase 2 --brazo A \
           --snapshot Ads/_INGESTA/META/snapshot_GTR7.json
    ... --escribir     # ademas escribe los ad_id en _DIM_CREATIVOS.csv y da de alta en
                       # _DIM_CONJUNTOS.csv los conjuntos del manifiesto que falten
    ... --ya-activo    # el operador ya publico/activo la campana (borrador de Ads Manager):
                       # se omite el gate de PAUSED; el de '- Copia' sigue vigente
"""
import csv, io, os, re, sys, json, shutil, datetime

for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError): pass

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
P    = lambda *a: os.path.join(BASE, "PRODUCTOS", *a)
CREATIVOS = P("_DIM_CREATIVOS.csv")


def arg(flag, default=None):
    if flag in sys.argv:
        i = sys.argv.index(flag)
        if i + 1 < len(sys.argv):
            return sys.argv[i + 1]
    return default


def cargar_snapshot(ruta):
    """Devuelve {nombre: {'id':..., 'nivel':..., 'status':...}}. Acepta el JSON crudo del MCP
    (donde ad_entities puede venir como STRING con JSON adentro) o el envoltorio del sistema."""
    with io.open(ruta, encoding="utf-8") as f:
        d = json.load(f)
    objetos = d if isinstance(d, list) else d.get("ad_entities", d.get("objetos", []))
    if isinstance(objetos, str):
        objetos = json.loads(objetos)
    out = {}
    for o in objetos:
        if o.get("name"):
            out[o["name"].strip()] = {"id": o.get("id"), "nivel": o.get("nivel", ""),
                                      "status": o.get("status") or o.get("effective_status", ""),
                                      "campaign_id": o.get("campaign_id", "")}
    return out


def copias_sin_renombrar(meta, campaign_id):
    """Anuncios de la campana declarada cuyo nombre termina en '- Copia' (o '- Copia N'):
    Meta los nombra asi al duplicar y nadie los renombro (invariante 12: prohibido publicar un
    '- Copia'). Con ese nombre el anuncio no matchea el manifiesto: su ad_id no se escribe y su
    gasto y sus ventas quedan sin dimension. Devuelve [(nombre, id)]."""
    return [(n, m["id"]) for n, m in meta.items()
            if re.search(r"\s-\s*Copia(\s*\d+)?$", n, re.I)
            and (not campaign_id or m.get("campaign_id") == campaign_id)]


def filas_alta_conjuntos(man, pq, dim_rows, ya_activo, hoy):
    """Filas nuevas de _DIM_CONJUNTOS.csv para los conjuntos del manifiesto que aun no existen.
    Sin esa fila el JOIN de LucidSales contra la dimension deja el gasto y las ventas del
    conjunto fuera del analisis (y el ciclo nocturno queda amarillo). La plantilla es una fila
    del mismo producto y angulo (atributos HEREDADOS), nunca atributos inventados.
    Devuelve [fila_dict]; vacio si todo ya esta dado de alta."""
    existentes = {r["conjunto_meta"].strip() for r in dim_rows}
    pk, ang = pq["producto_key"], pq["angulo"]
    plantilla = next((r for r in dim_rows
                      if r["producto_key"] == pk and r["angulo_key"] == ang), None)
    if plantilla is None:
        return []
    nuevas = []
    for cj in man["conjuntos"]:
        if cj["nombre"] in existentes:
            continue
        f = dict(plantilla)
        f.update({
            "conjunto_meta": cj["nombre"], "cuenta_alias": pq["cuenta_alias"],
            "campana_clave": man["campana"], "fase": "FASE%d" % pq["fase"],
            "formato": "IMAGEN", "concepto_key": "SIN_CLASIFICAR", "creativo_id": "",
            "estado": "ACTIVO" if ya_activo else "PAUSADO", "verificado_en_csv": "SI",
            "fecha_alta": hoy, "origen_angulo": "HEREDADO_PAQUETE",
            "notas": ("ALTA %s por verificar_publicacion.py desde el paquete de publicacion. "
                      "Atributos HEREDADOS de '%s' (mismo producto y angulo)."
                      % (hoy, plantilla["conjunto_meta"])),
        })
        nuevas.append(f)
    return nuevas


def objetos_no_pausados(filas, meta):
    """De los objetos DECLARADOS que SI existen en Meta (estado=='OK' en `filas`), los que NO
    estan PAUSED. Devuelve (nivel, nombre, id, estado_observado) — `estado_observado` es
    'SIN effective_status' cuando el snapshot no trajo ese campo (nunca se asume PAUSED por
    ausencia: eso seria fallar en silencio, T8-2). Todo objeto que este sistema crea nace PAUSED
    (invariante 12); uno ACTIVE o sin status leido de Meta no pasa el gate."""
    out = []
    for nivel, nombre, estado, oid in filas:
        if estado != "OK":
            continue
        status = (meta.get(nombre) or {}).get("status")
        if status != "PAUSED":
            out.append((nivel, nombre, oid, status or "SIN effective_status"))
    return out


def no_declarados(meta, declarados, campana):
    """Nombres del snapshot que empiezan con cuenta_token_ de la campaña declarada, no
    están en el manifiesto y llevan el token de fase de la campaña. Se reportan, nunca
    se borran."""
    prefijo = "_".join(campana.split("_")[:2]) + "_"
    token_fase = campana.split("_")[2]
    return [n for n in meta
            if n.startswith(prefijo) and n not in declarados and token_fase in n]


def aplicar_ad_ids(rows, ids_por_creativo, ruta_pq):
    """Escribe ad_id + la transicion de estado en las filas de _DIM_CREATIVOS.csv que
    matchean ids_por_creativo (creativo_id -> {'A': ad_id, 'B': ad_id}).

    Ciclo de vida del estado — obligatorio, sin saltos (ETAPA-9.md):
        PENDIENTE_GENERAR -> GENERADO -> PUBLICADO -> RETIRADO
    'PUBLICADO exige ad_id real: es el unico estado que cuenta como inventario vivo' —
    pero nadie escribia esa transicion, y la fila se quedaba en GENERADO con un ad_id ya
    vivo en Meta (el error de fondo que este script existe para cerrar, ver POR QUE EXISTE
    arriba). Nunca degrada un RETIRADO. No toca estado_entrega: ese campo es
    ENTREGADO/SIN_ENTREGA segun el gasto (DATA_PLAYBOOK.md), lo escribe otro proceso mas
    adelante, no este gate.

    Devuelve (rows, escritas, ascendidas, conflictos)."""
    escritas, conflictos, ascendidas = 0, [], 0
    for r in rows:
        cid = r.get("creativo_id")
        if cid not in ids_por_creativo:
            continue
        par = ids_por_creativo[cid]
        nuevo = ";".join(par[l] for l in sorted(par))
        viejo = (r.get("ad_id") or "").strip()
        if viejo and viejo != nuevo:
            conflictos.append((cid, viejo, nuevo))
        r["ad_id"] = nuevo
        if (r.get("estado") or "").strip() != "RETIRADO":
            if (r.get("estado") or "").strip() != "PUBLICADO":
                ascendidas += 1
            r["estado"] = "PUBLICADO"
        nota = (r.get("notas") or "").strip()
        marca = ("|| ad_id escrito por verificar_publicacion.py el %s desde el manifiesto %s"
                 % (datetime.date.today().isoformat(), os.path.basename(ruta_pq)))
        if marca[:40] not in nota:
            r["notas"] = (nota + " " + marca).strip()
        escritas += 1
    return rows, escritas, ascendidas, conflictos


def main():
    pk    = arg("--producto")
    fase  = arg("--fase")
    brazo = (arg("--brazo") or "UNICO").upper()
    snap  = arg("--snapshot")
    ruta_pq = arg("--paquete")
    escribir = "--escribir" in sys.argv

    if not pk or not fase or not snap:
        print(__doc__)
        return 2
    fase = int(fase)

    productos = {r["producto_key"]: r for r in csv.DictReader(
        io.open(P("_DIM_PRODUCTOS.csv"), encoding="utf-8-sig", newline=""))}
    if pk not in productos:
        print("BLOQUEANTE: '%s' no tiene fila en _DIM_PRODUCTOS.csv." % pk)
        return 1
    carpeta = productos[pk].get("slug_carpeta") or pk

    if not ruta_pq:
        ruta_pq = P(carpeta, "_PUBLICACION_F%d%s.json" % (fase, "" if brazo == "UNICO" else brazo))
    if not os.path.exists(ruta_pq):
        print("BLOQUEANTE: no existe el paquete %s." % os.path.relpath(ruta_pq, BASE))
        print("            Corre primero: python Ads/_TOOLS/gen_publicacion.py --producto %s "
              "--fase %d --brazo %s" % (pk, fase, brazo))
        return 1
    if not os.path.exists(snap):
        print("BLOQUEANTE: no existe el snapshot %s." % snap)
        print("            Lo escribe el EJECUTOR volcando ads_get_ad_entities de la cuenta.")
        return 1

    with io.open(ruta_pq, encoding="utf-8") as f:
        pq = json.load(f)
    meta = cargar_snapshot(snap)
    man = pq["manifiesto"]

    filas, faltan, ids_por_creativo = [], 0, {}

    nom = man["campana"]
    hit = meta.get(nom)
    filas.append(("CAMPANA", nom, "OK" if hit else "FALTA", hit["id"] if hit else ""))
    if not hit: faltan += 1

    for cj in man["conjuntos"]:
        hit = meta.get(cj["nombre"])
        filas.append(("CONJUNTO", cj["nombre"], "OK" if hit else "FALTA", hit["id"] if hit else ""))
        if not hit: faltan += 1
        for a in cj["anuncios"]:
            hit = meta.get(a["nombre"])
            filas.append(("ANUNCIO", a["nombre"], "OK" if hit else "FALTA", hit["id"] if hit else ""))
            if not hit:
                faltan += 1
            else:
                ids_por_creativo.setdefault(a["creativo_id"], {})[a["letra"]] = hit["id"]

    declarados = {f[1] for f in filas}
    no_declarados_ = no_declarados(meta, declarados, man["campana"])

    # Todo objeto declarado que SI existe en Meta tiene que estar PAUSED (invariante 12); si el
    # snapshot lo trae ACTIVE ya esta gastando sin confirmacion del operador.
    ya_activo = "--ya-activo" in sys.argv
    no_pausados = [] if ya_activo else objetos_no_pausados(filas, meta)
    copias = copias_sin_renombrar(meta, (meta.get(man["campana"]) or {}).get("id", ""))

    print("=" * 78)
    print("GATE DE PUBLICACION  ·  %s  ·  FASE %d brazo %s  ·  %s"
          % (pk, fase, brazo, pq["cuenta_alias"]))
    print("=" * 78)
    print("  manifiesto  %s" % os.path.relpath(ruta_pq, BASE))
    print("  snapshot    %s" % snap)
    print()
    for nivel, nombre, estado, oid in filas:
        marca = "OK   " if estado == "OK" else "FALTA"
        print("  [%s] %-9s %-52s %s" % (marca, nivel, nombre[:52], oid))
    print()
    if no_declarados_:
        print("  NO DECLARADOS (existen en Meta y el manifiesto no los pedia) — se reportan, "
              "NUNCA se borran:")
        for n in no_declarados_:
            print("    ? %-56s %s" % (n[:56], meta[n]["id"]))
        print()

    ok = len(filas) - faltan
    print("  RESULTADO: %d de %d objetos declarados existen en Meta." % (ok, len(filas)))

    if copias:
        print()
        print("  X %d anuncio(s) con nombre '- Copia' sin renombrar (invariante 12):" % len(copias))
        for n, oid in copias:
            print("    ! %-60s id=%s" % (n[:60], oid))
        print("    Renombra cada uno al nombre declarado en el manifiesto (el que lleva A o B) y")
        print("    vuelve a correr este gate. Con ese nombre su ad_id, su gasto y sus ventas no")
        print("    cruzan con el analisis.")
        return 1

    if faltan:
        print()
        print("  X La secuencia quedo A MEDIAS. NO ACTIVAR.")
        print("    Volve a correr gen_publicacion.py con --snapshot: las llamadas de lo que ya")
        print("    existe se marcan 'omitir' y solo se crea lo que falta. No se republica encima.")
        return 1

    if no_pausados:
        print()
        print("  X %d objeto(s) declarado(s) NO estan PAUSED en Meta:" % len(no_pausados))
        for nivel, nombre, oid, estado_obs in no_pausados:
            print("    ! %-9s %-52s %-12s id=%s" % (nivel, nombre[:52], estado_obs, oid))
        print("    Todo objeto creado por este sistema nace PAUSED (invariante 12). Un objeto")
        print("    ACTIVE o sin effective_status en el snapshot NO pasa el gate: podria estar")
        print("    gastando sin confirmacion del operador. NO ACTIVAR.")
        return 1

    # ---------- escritura de los ad_id ------------------------------------
    if not escribir:
        print()
        print("  Todo declarado existe. Corre de nuevo con --escribir para grabar los ad_id en")
        print("  _DIM_CREATIVOS.csv. Sin eso, el CSV vuelve a decir 'sin publicar' y el sistema")
        print("  vuelve a creerle (el error del 08-sep).")
        return 0

    with io.open(CREATIVOS, encoding="utf-8-sig", newline="") as f:
        rd = csv.DictReader(f)
        cols, rows = rd.fieldnames, list(rd)
    stamp = datetime.datetime.now().strftime("%Y%m%d")
    shutil.copy(CREATIVOS, CREATIVOS + ".bak_publicacion_" + stamp)

    rows, escritas, ascendidas, conflictos = aplicar_ad_ids(rows, ids_por_creativo, ruta_pq)

    # Alta de los conjuntos en _DIM_CONJUNTOS.csv: sin esa fila el JOIN de LucidSales los
    # deja sin dimension y el ciclo nocturno queda amarillo.
    dim_ruta = P("_DIM_CONJUNTOS.csv")
    with io.open(dim_ruta, encoding="utf-8-sig", newline="") as f:
        rd = csv.DictReader(f)
        dim_cols, dim_rows = rd.fieldnames, list(rd)
    altas = filas_alta_conjuntos(man, pq, dim_rows, ya_activo, datetime.date.today().isoformat())
    if altas:
        shutil.copy(dim_ruta, dim_ruta + ".bak_publicacion_" + stamp)
        with io.open(dim_ruta, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=dim_cols)
            w.writeheader()
            for r in dim_rows + altas:
                w.writerow(r)
        print("  ALTA:    %d conjunto(s) nuevos en _DIM_CONJUNTOS.csv: %s"
              % (len(altas), ", ".join(a["conjunto_meta"] for a in altas)))

    with io.open(CREATIVOS, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow(r)

    print()
    print("  ESCRITO: %d fila(s) de _DIM_CREATIVOS.csv con su ad_id (backup .bak_publicacion_%s)"
          % (escritas, stamp))
    print("  ESTADO:  %d fila(s) pasaron a PUBLICADO (ciclo de vida, ETAPA-9.md)" % ascendidas)
    if conflictos:
        print("  OJO — %d fila(s) YA tenian un ad_id distinto y se reemplazo:" % len(conflictos))
        for cid, v, nu in conflictos:
            print("    %s : %s  ->  %s" % (cid, v, nu))
        print("    Los anuncios viejos NO se borran: son la evidencia del gasto que ya ocurrio.")
    print()
    print("  PENDIENTE Y OBLIGATORIO — control D+1 de tracking (MCP_PLAYBOOK 7.5):")
    print("    manana, ANTES de mirar rendimiento, cruzar conjunto por conjunto")
    print("      Meta >0 conversaciones  ·  LucidSales >0 mensajes   -> tracking OK")
    print("      Meta >0                 ·  LucidSales  =0           -> CIEGO, cortar YA")
    print("    Un conjunto ciego es indistinguible de uno malo. Sin tracking no hay veredicto,")
    print("    solo gasto sin medir: la tanda del 27-jul quemo $166 en 8 conjuntos ciegos.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
