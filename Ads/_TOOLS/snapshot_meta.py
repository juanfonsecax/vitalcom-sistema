# -*- coding: utf-8 -*-
"""snapshot_meta.py — vuelca desde la Graph API (SOLO LECTURA) las campanas, conjuntos y anuncios
de UNA campana de una cuenta, en el formato que lee `verificar_publicacion.cargar_snapshot`.

POR QUE EXISTE
--------------
El gate de publicacion necesita un snapshot de lo que Meta TIENE. Hasta ahora lo escribia un
ejecutor (Claude por MCP) volcando `ads_get_ad_entities`. Este script hace lo mismo sin sesion de
Claude, con el token de lectura del System User (`META_SYSTEM_USER_TOKEN`, permiso `ads_read`).
Reusa `token_de` y `pedir_json` de `bajar_meta_insights.py`: un solo lugar sabe leer el token.

SOLO LECTURA: este script hace GET y nada mas. Nunca pide ni usa `ads_management`. El token no se
imprime nunca (ni siquiera en los mensajes de error).

USO
    python Ads/_TOOLS/snapshot_meta.py --cuenta 598687956219141 \\
           --campana GTR7_CLEARSTEM_CONCEPTOS-C_20261017 \\
           --salida Ads/_INGESTA/META/snapshot_GTR7_C.json --alias GTR7

FORMATO DE SALIDA
    {"cuenta_alias","cuenta_id","tomado_el","ad_entities":[{"id","nivel","name",
      "effective_status","campaign_id"}]}
    `nivel` es campaign | adset | ad. Solo entran las campanas cuyo nombre CONTIENE --campana y
    los conjuntos/anuncios que cuelgan de ellas.

CODIGOS DE SALIDA
    0 = snapshot escrito.   1 = falta el token, error de la Graph API o sin conexion.
"""
import sys, os, io, json, argparse, datetime, tempfile, urllib.parse

for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError): pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

FIELDS = "id,name,effective_status,campaign_id"
NIVELES = (("campaign", "campaigns"), ("adset", "adsets"), ("ad", "ads"))
MAX_PAGINAS = 200   # tope duro contra un paging.next que nunca termina


class SnapshotError(Exception):
    """Error legible para el operador (nunca lleva el token)."""


_MANTENER = []


def _bmi():
    # Import perezoso: bajar_meta_insights arrastra la capa de datos y tarda ~3 s. Con --help
    # o en los tests con la red simulada no hace falta.
    # ingerir_meta (que arrastra bajar_meta_insights) reemplaza sys.stdout usando .buffer: si el
    # llamador tiene stdout capturado (StringIO) revienta. Se importa con el stdout real y se
    # devuelve el del llamador.
    capturado = sys.stdout
    sys.stdout = sys.__stdout__
    try:
        import bajar_meta_insights as bmi
    finally:
        # El envoltorio nuevo comparte buffer con el stdout real: si se descarta, el GC cierra
        # el buffer y el siguiente print revienta ('I/O operation on closed file').
        _MANTENER.append(sys.stdout)
        sys.stdout = capturado
    return bmi


def pedir(url):
    """UNICA puerta de red del script. Los tests la reemplazan."""
    return _bmi().pedir_json(url)


def _sin_token(texto, token):
    return texto.replace(token, "***") if token else texto


def paginar(url_inicial, token, pedir_fn):
    """Recorre `paging.next` y devuelve la lista completa de `data`."""
    out, url = [], url_inicial
    for _ in range(MAX_PAGINAS):
        resp = pedir_fn(url)
        if not isinstance(resp, dict):
            raise SnapshotError("Respuesta inesperada de la Graph API.")
        if "error" in resp:
            err = resp["error"] if isinstance(resp["error"], dict) else {}
            msg = _sin_token(str(err.get("message", "error sin detalle")), token)
            raise SnapshotError("La Graph API respondio con error (codigo %s): %s"
                                % (err.get("code", "?"), msg))
        out.extend(resp.get("data", []))
        url = (resp.get("paging") or {}).get("next")
        if not url:
            return out
    raise SnapshotError("La Graph API devolvio demasiadas paginas; se corta por seguridad.")


def construir_snapshot(cuenta_id, campana, token, alias="", pedir_fn=None, api=None):
    """Arma el dict del snapshot. `pedir_fn(url)->dict` es inyectable (tests)."""
    pedir_fn = pedir_fn or pedir
    api = api or _bmi().API
    cuenta_id = str(cuenta_id).replace("act_", "")
    por_nivel = {}
    for nivel, borde in NIVELES:
        params = {"fields": FIELDS, "limit": "500", "access_token": token}
        url = "%s/act_%s/%s?%s" % (api, cuenta_id, borde, urllib.parse.urlencode(params))
        por_nivel[nivel] = paginar(url, token, pedir_fn)

    ids_campana = {c["id"] for c in por_nivel["campaign"] if campana in (c.get("name") or "")}
    entidades = []
    for nivel, _ in NIVELES:
        for o in por_nivel[nivel]:
            cid = o["id"] if nivel == "campaign" else o.get("campaign_id")
            if cid in ids_campana:
                entidades.append({"id": o["id"], "nivel": nivel, "name": o.get("name", ""),
                                  "effective_status": o.get("effective_status", ""),
                                  "campaign_id": cid})
    return {"cuenta_alias": alias, "cuenta_id": cuenta_id,
            "tomado_el": datetime.datetime.now().astimezone().isoformat(),
            "ad_entities": entidades}


def escribir_atomico(ruta, datos):
    carpeta = os.path.dirname(os.path.abspath(ruta))
    os.makedirs(carpeta, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=carpeta, prefix=".snapshot_", suffix=".tmp")
    try:
        with io.open(fd, "w", encoding="utf-8", newline="\n") as f:
            json.dump(datos, f, ensure_ascii=False, indent=1)
        os.replace(tmp, ruta)
    except BaseException:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise


def main(argv=None):
    ap = argparse.ArgumentParser(description="Vuelca a JSON una campana de Meta (solo lectura).")
    ap.add_argument("--cuenta", required=True, help="ID de la cuenta publicitaria (sin act_)")
    ap.add_argument("--campana", required=True, help="Texto que debe contener el nombre de la campana")
    ap.add_argument("--salida", required=True, help="Ruta del JSON a escribir")
    ap.add_argument("--alias", default="", help="Alias de la cuenta (ej. GTR7)")
    ap.add_argument("--env", default=None, help="Archivo .env con META_SYSTEM_USER_TOKEN")
    a = ap.parse_args(argv)

    try:
        bmi = _bmi()
        token = bmi.token_de(a.env or bmi.ENV_DEFAULT)
    except SystemExit as e:
        print(str(e.code) if e.code else "Falta el token de Meta (META_SYSTEM_USER_TOKEN).")
        return 1
    try:
        snap = construir_snapshot(a.cuenta, a.campana, token, a.alias)
    except SnapshotError as e:
        print("ERROR: %s" % _sin_token(str(e), token))
        return 1
    except SystemExit as e:   # pedir_json: sin conexion / HTTP sin JSON
        print("ERROR: %s" % _sin_token(str(e.code), token))
        return 1

    escribir_atomico(a.salida, snap)
    n = {k: sum(1 for o in snap["ad_entities"] if o["nivel"] == k) for k, _ in NIVELES}
    print("Snapshot escrito: %s  (%d campana, %d conjuntos, %d anuncios)"
          % (a.salida, n["campaign"], n["adset"], n["ad"]))
    if not n["campaign"]:
        print("AVISO: ninguna campana contiene '%s' en esa cuenta." % a.campana)
    return 0


if __name__ == "__main__":
    sys.exit(main())
