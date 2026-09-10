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

QUE ESCRIBE (solo con --escribir)
---------------------------------
`ad_id` en `PRODUCTOS/_DIM_CREATIVOS.csv`, formato `adA;adB`, una fila por creativo_id.
Backup previo, escritor CSV real (regla 11 de CLAUDE.md). Nunca pisa una fila que ya tenga un
`ad_id` distinto sin decirlo.

LO QUE ESTE GATE NO REEMPLAZA
-----------------------------
El **control D+1 de tracking** (`MCP_PLAYBOOK` 7.5). Que el anuncio EXISTA no prueba que
TRACKEE. Un conjunto ciego existe, gasta, trae conversaciones reales y marca 0 ventas para
siempre — y ese cero es un artefacto, no un veredicto (APR-034). Al dia siguiente hay que
cruzar Meta contra LucidSales conjunto por conjunto.

USO
    python Ads/_TOOLS/verificar_publicacion.py --producto TINNIDROP --fase 2 --brazo A \
           --snapshot Ads/_INGESTA/META/snapshot_GTR7.json
    ... --escribir     # ademas escribe los ad_id en _DIM_CREATIVOS.csv
"""
import csv, io, os, sys, json, shutil, datetime

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
                                      "status": o.get("status") or o.get("effective_status", "")}
    return out


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
    prefijo = "%s_%s" % (pq["cuenta_alias"], pk)
    no_declarados = [n for n in meta
                     if n.startswith(prefijo) and n not in declarados
                     and man["campana"].split("_")[2] in n]

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
    if no_declarados:
        print("  NO DECLARADOS (existen en Meta y el manifiesto no los pedia) — se reportan, "
              "NUNCA se borran:")
        for n in no_declarados:
            print("    ? %-56s %s" % (n[:56], meta[n]["id"]))
        print()

    ok = len(filas) - faltan
    print("  RESULTADO: %d de %d objetos declarados existen en Meta." % (ok, len(filas)))

    if faltan:
        print()
        print("  X La secuencia quedo A MEDIAS. NO ACTIVAR.")
        print("    Volve a correr gen_publicacion.py con --snapshot: las llamadas de lo que ya")
        print("    existe se marcan 'omitir' y solo se crea lo que falta. No se republica encima.")
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

    escritas, conflictos = 0, []
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
        nota = (r.get("notas") or "").strip()
        marca = ("|| ad_id escrito por verificar_publicacion.py el %s desde el manifiesto %s"
                 % (datetime.date.today().isoformat(), os.path.basename(ruta_pq)))
        if marca[:40] not in nota:
            r["notas"] = (nota + " " + marca).strip()
        escritas += 1

    with io.open(CREATIVOS, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow(r)

    print()
    print("  ESCRITO: %d fila(s) de _DIM_CREATIVOS.csv con su ad_id (backup .bak_publicacion_%s)"
          % (escritas, stamp))
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
