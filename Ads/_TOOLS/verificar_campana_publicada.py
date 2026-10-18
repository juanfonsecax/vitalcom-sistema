# -*- coding: utf-8 -*-
"""verificar_campana_publicada.py — "Ya publique la campana": un solo paso que toma el snapshot de
Meta (Graph API, solo lectura) y corre el gate de publicacion con --ya-activo --escribir.

POR QUE EXISTE
--------------
El 17-oct-2026 el operador publico la campana a mano y verificarla exigio una sesion de Claude
(MCP para volcar el snapshot, luego el gate). Este wrapper lo deja en un boton de la app:

    paquete (_PUBLICACION_F<fase><brazo>.json)
      -> snapshot_meta.py  -> Ads/_INGESTA/META/snapshot_<alias>_<brazo>.json
      -> verificar_publicacion.py --ya-activo [--escribir]   (ad_id + alta de conjuntos)

No escribe en Meta. No inventa nada: el veredicto es el del gate; este script solo lo traduce a un
mensaje para el operador.

USO
    python Ads/_TOOLS/verificar_campana_publicada.py --producto CLEARSTEM --fase 2 --brazo C
    ... --sin-escribir   # solo comprueba, no toca los CSV
    ... --json           # salida SOLO JSON (la usa la app)

SALIDA (ultima linea, o unica con --json)
    {"ok","objetos_declarados","objetos_ok","copias":[...],"altas":[...],
     "ad_ids_escritos","mensaje_operador","requiere_claude"} + "detalle" (copia de mensaje_operador,
    para el runner). `requiere_claude` (forma en requiere_claude.py) lista lo que exige una
    escritura en Meta por MCP; va VACIA cuando no hace falta Claude.

CODIGOS DE SALIDA   0 = el gate paso.   1 = no paso (ver mensaje_operador).   2 = uso incorrecto.
"""
import sys, os, io, re, csv, json, argparse, contextlib
from unittest import mock

for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError): pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import verificar_publicacion as vp  # noqa: E402
import snapshot_meta as sm          # noqa: E402
import requiere_claude as rq        # noqa: E402


def ruta_snapshot(alias, brazo):
    return os.path.join(vp.BASE, "Ads", "_INGESTA", "META", "snapshot_%s_%s.json" % (alias, brazo))


def cargar_paquete(producto, fase, brazo):
    """Devuelve (ruta, paquete) o lanza ValueError con un mensaje para el operador."""
    with io.open(vp.P("_DIM_PRODUCTOS.csv"), encoding="utf-8-sig", newline="") as f:
        productos = {r["producto_key"]: r for r in csv.DictReader(f)}
    if producto not in productos:
        raise ValueError("El producto %s no existe en el sistema." % producto)
    carpeta = productos[producto].get("slug_carpeta") or producto
    ruta = vp.P(carpeta, "_PUBLICACION_F%d%s.json" % (fase, "" if brazo == "UNICO" else brazo))
    if not os.path.exists(ruta):
        raise ValueError("No hay paquete de publicacion para %s fase %d brazo %s. Generalo primero "
                         "con gen_publicacion.py." % (producto, fase, brazo))
    with io.open(ruta, encoding="utf-8") as f:
        return ruta, json.load(f)


def tomar_snapshot(cuenta_id, alias, campana, ruta):
    """Corre snapshot_meta y devuelve (rc, texto). Punto de inyeccion para los tests."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = sm.main(["--cuenta", str(cuenta_id), "--campana", campana, "--salida", ruta,
                      "--alias", alias])
    return rc, buf.getvalue()


def correr_gate(producto, fase, brazo, snap, ruta_pq, escribir):
    """Corre verificar_publicacion.main con --ya-activo; devuelve (rc, salida)."""
    argv = ["verificar_publicacion.py", "--producto", producto, "--fase", str(fase),
            "--brazo", brazo, "--snapshot", snap, "--paquete", ruta_pq, "--ya-activo"]
    if escribir:
        argv.append("--escribir")
    buf = io.StringIO()
    with mock.patch.object(sys, "argv", argv), contextlib.redirect_stdout(buf):
        rc = vp.main()
    return rc, buf.getvalue()


def _declarados(man):
    """[(nivel, nombre)] de todo lo que el paquete declara."""
    out = [("CAMPANA", man["campana"])]
    for cj in man["conjuntos"]:
        out.append(("CONJUNTO", cj["nombre"]))
        out.extend(("ANUNCIO", a["nombre"]) for a in cj["anuncios"])
    return out


_COPIA_RE = re.compile(r"\s-\s*Copia(\s*\d+)?$", re.I)
_ANUNCIO_RE = re.compile(r"^(.*) ([A-Z]) ~ (.*)$")


def _clave_anuncio(nombre):
    """(concepto, cola) de 'CONCEPTO LETRA ~ COLA'; None si el nombre no sigue esa forma."""
    m = _ANUNCIO_RE.match(nombre)
    return (m.group(1), m.group(3)) if m else None


def nombres_esperados(copias, declarados, meta):
    """{id_copia: [candidatos]} — a que nombre del paquete debe renombrarse cada '- Copia'.

    Un '- Copia' es el duplicado de un anuncio: sin sufijo es el nombre original (si ese ya no
    esta en Meta) o su hermano de la otra letra (si el original sigue ahi). Los candidatos son los
    anuncios declarados que NO existen en Meta y comparten concepto y cola con el nombre sin
    sufijo. Un candidato unico es la respuesta; varios (o ninguno) se devuelven tal cual para que
    lo resuelva una persona: nunca se adivina."""
    faltan = [n for nivel, n in declarados if nivel == "ANUNCIO" and n not in meta]
    out = {}
    for c in copias:
        base = _COPIA_RE.sub("", c["nombre"]).strip()
        clave = _clave_anuncio(base)
        cands = [n for n in faltan if n == base or (clave and _clave_anuncio(n) == clave)]
        out[c["id"]] = cands
    return out


def _requiere_claude(alias, campana, copias, declarados, meta):
    """Lista `requiere_claude` del resultado: un item RENOMBRAR_COPIA si quedan '- Copia'."""
    if not copias:
        return []
    esperados = nombres_esperados(copias, declarados, meta)
    # Un candidato reclamado por dos copias tampoco es una respuesta unica.
    uso = {}
    for cands in esperados.values():
        for n in cands:
            uso[n] = uso.get(n, 0) + 1
    partes = []
    for c in copias:
        cands = esperados[c["id"]]
        if len(cands) == 1 and uso[cands[0]] == 1:
            partes.append("%s -> %s" % (c["id"], cands[0]))
        else:
            partes.append("%s -> (no es unico, candidatos: %s)"
                          % (c["id"], " | ".join(cands) if cands else "ninguno declarado sin publicar"))
    frase = ("Renombrá en la cuenta %s los anuncios con '- Copia' de la campaña %s a su nombre del "
             "paquete: %s." % (alias, campana, "; ".join(partes)))
    motivo = ("Hay %d anuncio(s) con '- Copia' en Meta. Renombrarlos es una escritura en Meta y se "
              "hace por el MCP desde una sesión de Claude." % len(copias))
    return [rq.item("RENOMBRAR_COPIA", "alta", motivo, frase, copias)]


def _mensaje(ok, declarados, objetos_ok, faltan, copias, bloqueo, escribio):
    if bloqueo:
        return bloqueo
    if copias:
        n = copias[0]["nombre"]
        extra = "" if len(copias) == 1 else " (y %d mas)" % (len(copias) - 1)
        return ("Hay %d anuncio(s) con nombre '- Copia'. Renombrá en Ads Manager «%s»%s al nombre "
                "del manifiesto (el que lleva A o B) y volvé a verificar." % (len(copias), n, extra))
    if faltan:
        muestra = "; ".join(n for _, n in faltan[:3]) + ("..." if len(faltan) > 3 else "")
        return ("Faltan %d de %d objetos en Meta (%s). Revisá que la campana esté completa y volvé "
                "a verificar." % (len(faltan), declarados, muestra))
    if not ok:
        return "El gate no pasó. Mirá el detalle del trabajo."
    return ("Todo en orden: %d de %d objetos existen en Meta y sin '- Copia'. %s"
            % (objetos_ok, declarados,
               "Ya quedaron grabados los ids de los anuncios." if escribio
               else "No se grabó nada (modo solo verificar)."))


def verificar(producto, fase, brazo, escribir=True):
    """Devuelve (resultado_dict, texto_log)."""
    log = []
    res = {"ok": False, "objetos_declarados": 0, "objetos_ok": 0, "copias": [], "altas": [],
           "ad_ids_escritos": 0, "mensaje_operador": "", "requiere_claude": []}
    try:
        ruta_pq, pq = cargar_paquete(producto, fase, brazo)
    except ValueError as e:
        res["mensaje_operador"] = str(e)
        return res, ""
    man = pq["manifiesto"]
    declarados = _declarados(man)
    res["objetos_declarados"] = len(declarados)

    snap = ruta_snapshot(pq["cuenta_alias"], brazo)
    rc, txt = tomar_snapshot(pq["cuenta_id"], pq["cuenta_alias"], man["campana"], snap)
    log.append(txt)
    if rc != 0 or not os.path.exists(snap):
        res["mensaje_operador"] = ("No pude leer Meta: %s"
                                   % (txt.strip().splitlines()[-1] if txt.strip() else "sin detalle"))
        return res, "\n".join(log)

    rc, txt = correr_gate(producto, fase, brazo, snap, ruta_pq, escribir)
    log.append(txt)
    meta = vp.cargar_snapshot(snap)
    faltan = [(n, nm) for n, nm in declarados if nm not in meta]
    copias_raw = vp.copias_sin_renombrar(meta, (meta.get(man["campana"]) or {}).get("id", ""))
    res["objetos_ok"] = len(declarados) - len(faltan)
    res["copias"] = [{"nombre": n, "id": i} for n, i in copias_raw]
    res["ok"] = rc == 0
    res["requiere_claude"] = _requiere_claude(pq["cuenta_alias"], man["campana"], res["copias"],
                                              declarados, meta)
    for linea in txt.splitlines():
        if linea.strip().startswith("ALTA:"):
            res["altas"] = [x.strip() for x in linea.split(":", 2)[2].split(",") if x.strip()]
    if rc == 0 and escribir:
        res["ad_ids_escritos"] = sum(1 for n, nm in declarados if n == "ANUNCIO" and nm in meta)
    bloqueo = next((l.strip() for l in txt.splitlines() if l.strip().startswith("BLOQUEANTE")), "")
    res["mensaje_operador"] = _mensaje(res["ok"], len(declarados), res["objetos_ok"], faltan,
                                       res["copias"], bloqueo, escribir)
    return res, "\n".join(log)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Snapshot de Meta + gate de publicacion (--ya-activo).")
    ap.add_argument("--producto", required=True)
    ap.add_argument("--fase", required=True, type=int)
    ap.add_argument("--brazo", default="UNICO")
    ap.add_argument("--sin-escribir", action="store_true", help="No graba ad_id ni altas en los CSV")
    ap.add_argument("--json", action="store_true", help="Imprime SOLO el JSON final")
    a = ap.parse_args(argv)

    res, log = verificar(a.producto, a.fase, a.brazo.upper(), escribir=not a.sin_escribir)
    if not a.json and log.strip():
        print(log)
    # `detalle` repite el mensaje: el runner de la app lo muestra como motivo cuando el gate no pasa.
    print(json.dumps(dict(res, detalle=res["mensaje_operador"]), ensure_ascii=False))
    return 0 if res["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
