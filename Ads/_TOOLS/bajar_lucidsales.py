#!/usr/bin/env python3
"""
bajar_lucidsales.py — baja el export de LucidSales SIN navegador, contra su API.

Uso:
    python Ads/_TOOLS/bajar_lucidsales.py                      # ayer (1 dia)
    python Ads/_TOOLS/bajar_lucidsales.py --dias 7             # control semanal
    python Ads/_TOOLS/bajar_lucidsales.py --fecha 2026-09-05
    python Ads/_TOOLS/bajar_lucidsales.py --fecha 2026-09-01 --hasta 2026-09-06

Escribe Ads/_INGESTA/LUCIDSALES/report-<ini>-<fin>.json (el JSON CRUDO de la API,
sin transformar) y lo deja listo para ingerir_lucidsales.py.

CONTRATO DE LA API  (medido en vivo el 07-sep-2026 contra panel.lucidsales.co)
  base      https://panel.lucidsales.co/b/
  login     POST auth/login   {"email","password"}  -> {"ok":true,"token":<JWT 12h>,...}
            el front hace email.trim().toLowerCase() antes de mandarlo; se replica.
  tienda    POST auth/addShopId {"id":<shopId>} -> {"ok":true,"token":<JWT NUEVO>}
            OBLIGATORIO: el token de login NO trae tienda y meta/metrics responde
            403 "No hay una tienda activa seleccionada". El token que devuelve este
            paso REEMPLAZA al de login (lleva "tiendaActiva" en los claims).
            Los ids del usuario salen del claim uid.idEmpresa ("3703,3744"), y los
            nombres de auth/getshopname {"id":[3703,3744]} — LISTA de enteros; con el
            string "3703,3744" el servidor devuelve 500.
            ⚠ getshopname trae tambien apiKey/botApiKey EN CLARO: se leen solo id y
            Nombre, el resto se descarta sin imprimirlo ni guardarlo.
  auth      header  x-token: <JWT>        (Authorization: Bearer da 401 — NO es Bearer)
  data      GET meta/metrics/1?startDate=YYYY-MM-DD&endDate=YYYY-MM-DD&search=
            -> {"ok":true,"insights":[...22 campos...],"count":N}
  paginacion  DECORATIVA: page / itemsPerPage / el "1" de la ruta NO cambian la
            respuesta — el backend devuelve SIEMPRE el set completo y el front pagina
            en el cliente. Por eso aca no se pagina: no hay export parcial posible.
  xlsx      el .xlsx que bajaba el operador a mano es un volcado literal de "insights"
            hecho por el navegador (chunk excel-exporter). Mismas 22 columnas, misma
            data, cero transformacion del servidor. El JSON es la fuente, el xlsx era
            un intermediario.

CREDENCIALES — nunca en el repo, nunca en git, nunca en la linea de comandos.
  Se leen de las variables de entorno LUCIDSALES_EMAIL / LUCIDSALES_PASSWORD, y si no
  estan, de un .env local (default ~/.config/lucidsales/.env, permisos 600).
  Este script NO imprime jamas el token ni la contrasena.
"""
import sys, io, os, json, base64, argparse, datetime, urllib.request, urllib.error

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SALIDA = os.path.join(BASE, "Ads", "_INGESTA", "LUCIDSALES")
ENV_DEFAULT = os.path.join(os.path.expanduser("~"), ".config", "lucidsales", ".env")
API = "https://panel.lucidsales.co/b/"
TIMEOUT = 60


def cargar_env(path):
    """Lee un .env simple (CLAVE=valor). No expande, no ejecuta, no imprime valores."""
    if not os.path.exists(path):
        return {}
    out = {}
    # utf-8-sig: Notepad en Windows puede dejar BOM al guardar, y con "utf-8" pelado
    # la primera clave quedaria como "﻿LUCIDSALES_EMAIL" y fallaria sin decir por que.
    with open(path, encoding="utf-8-sig") as fh:
        for linea in fh:
            linea = linea.strip()
            if not linea or linea.startswith("#") or "=" not in linea:
                continue
            k, v = linea.split("=", 1)
            out[k.strip()] = v.strip().strip('"').strip("'")
    return out


def credenciales(env_path):
    email = os.environ.get("LUCIDSALES_EMAIL")
    pwd = os.environ.get("LUCIDSALES_PASSWORD")
    if not (email and pwd):
        env = cargar_env(env_path)
        email = email or env.get("LUCIDSALES_EMAIL")
        pwd = pwd or env.get("LUCIDSALES_PASSWORD")
    if not (email and pwd):
        raise SystemExit(
            "FALTAN CREDENCIALES.\n"
            f"  Pone LUCIDSALES_EMAIL y LUCIDSALES_PASSWORD en {env_path}\n"
            "  (o exportalas como variables de entorno).\n"
            "  Ese archivo va FUERA del repo y con permisos 600."
        )
    return email.strip().lower(), pwd


def pedir(url, datos=None, token=None):
    cab = {"Accept": "application/json", "User-Agent": "vitalcom-bajar_lucidsales/1.0"}
    cuerpo = None
    if datos is not None:
        cuerpo = json.dumps(datos).encode("utf-8")
        cab["Content-Type"] = "application/json"
    if token:
        cab["x-token"] = token
    req = urllib.request.Request(url, data=cuerpo, headers=cab,
                                 method="POST" if datos is not None else "GET")
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detalle = e.read().decode("utf-8", "replace")[:300]
        raise SystemExit("HTTP {} en {}\n  {}".format(e.code, url.split("?")[0], detalle))
    except urllib.error.URLError as e:
        raise SystemExit(f"Sin conexion con LucidSales: {e.reason}")


def login(email, pwd):
    r = pedir(API + "auth/login", {"email": email, "password": pwd})
    if not r.get("ok") or not r.get("token"):
        raise SystemExit("Login rechazado por LucidSales (revisa el .env). "
                         "El servidor no devolvio token.")
    return r["token"], r.get("name", "")


def claims(token):
    """Lee los claims del JWT propio (sin verificar firma: solo para saber que tiendas hay)."""
    try:
        p = token.split(".")[1]
        p = p.replace("-", "+").replace("_", "/")
        p += "=" * ((4 - len(p) % 4) % 4)
        return json.loads(base64.b64decode(p).decode("utf-8")).get("uid", {})
    except Exception:
        return {}


def tiendas(token, ids):
    """[(id, Nombre)] de las tiendas del usuario.

    OJO: la respuesta de getshopname trae ademas apiKey y botApiKey EN CLARO. Aca se
    extraen solo id y Nombre y el resto se descarta: no se imprime ni se guarda nunca.
    El endpoint exige una LISTA de enteros; mandarle el string "3703,3744" devuelve 500.
    """
    r = pedir(API + "auth/getshopname", {"id": [int(i) for i in ids]}, token=token)
    if not r.get("ok"):
        return []
    return [(int(s["id"]), str(s.get("Nombre") or "").strip()) for s in r.get("shopName", [])]


def elegir_tienda(token, deseada):
    """Resuelve la tienda por id o por nombre y la ACTIVA (addShopId devuelve token nuevo).

    Sin este paso, meta/metrics responde 403 "No hay una tienda activa seleccionada":
    el token que sale de auth/login todavia no tiene tienda.
    """
    ids = [i.strip() for i in str(claims(token).get("idEmpresa") or "").split(",") if i.strip()]
    if not ids:
        raise SystemExit("El token no declara ninguna tienda (idEmpresa vacio).")

    if deseada and str(deseada).isdigit():
        destino = int(deseada)
        if ids and str(destino) not in ids:
            raise SystemExit(f"La tienda {destino} no esta entre las tuyas: {', '.join(ids)}")
        nombre = ""
    else:
        disponibles = tiendas(token, ids)
        if not deseada:
            if len(disponibles) == 1:
                destino, nombre = disponibles[0]
            else:
                op = " · ".join(f"{n} (id {i})" for i, n in disponibles) or ", ".join(ids)
                raise SystemExit(
                    "Tenes MAS DE UNA TIENDA y no dijiste cual.\n"
                    f"  Opciones: {op}\n"
                    "  Pone LUCIDSALES_TIENDA=<nombre o id> en el .env, o usa --tienda."
                )
        else:
            match = [(i, n) for i, n in disponibles if n.lower() == str(deseada).strip().lower()]
            if not match:
                op = " · ".join(f"{n} (id {i})" for i, n in disponibles)
                raise SystemExit(f"No encontre la tienda '{deseada}'. Tenes: {op}")
            destino, nombre = match[0]

    r = pedir(API + "auth/addShopId", {"id": destino}, token=token)
    if not r.get("ok") or not r.get("token"):
        raise SystemExit(f"LucidSales no me dejo activar la tienda {destino}.")
    return r["token"], (nombre or str(destino))


def bajar(token, ini, fin):
    url = f"{API}meta/metrics/1?startDate={ini}&endDate={fin}&search="
    r = pedir(url, token=token)
    if not r.get("ok"):
        raise SystemExit(f"La API respondio ok=false para {ini}..{fin}")
    return r.get("insights") or []


def num(f, k):
    try:
        return float(f.get(k) or 0)
    except (TypeError, ValueError):
        return 0.0


def main():
    hoy = datetime.date.today()
    p = argparse.ArgumentParser(description="Baja el export de LucidSales por API.")
    p.add_argument("--fecha", help="dia (o inicio) YYYY-MM-DD. Default: ayer")
    p.add_argument("--hasta", help="fin de ventana YYYY-MM-DD (default = --fecha)")
    p.add_argument("--dias", type=int, default=1,
                   help="tamano de ventana hacia atras desde --fecha. Default 1")
    p.add_argument("--tienda", help="nombre o id de la tienda (default: LUCIDSALES_TIENDA del .env)")
    p.add_argument("--salida", default=SALIDA)
    p.add_argument("--env", default=ENV_DEFAULT)
    p.add_argument("--forzar", action="store_true", help="reescribe si ya existe")
    a = p.parse_args()

    fin = datetime.date.fromisoformat(a.fecha) if a.fecha else hoy - datetime.timedelta(days=1)
    if a.hasta:
        ini, fin = fin, datetime.date.fromisoformat(a.hasta)
    else:
        ini = fin - datetime.timedelta(days=a.dias - 1)
    if ini > fin:
        raise SystemExit(f"Ventana invalida: {ini} > {fin}")
    if fin >= hoy:
        print(f"AVISO: la ventana llega a {fin} (hoy o futuro). El dia en curso esta "
              "INCOMPLETO y la doctrina manda exportar AYER cerrado.")

    os.makedirs(a.salida, exist_ok=True)
    destino = os.path.join(a.salida, f"report-{ini}-{fin}.json")
    if os.path.exists(destino) and not a.forzar:
        # Salida 0 A PROPOSITO: "ese dia ya esta bajado" no es un fallo, es no tener nada
        # que hacer. Con exit 1 la rutina nocturna lo leeria como error y abortaria la
        # auditoria entera por una corrida repetida.
        print(f"Ya existe {os.path.basename(destino)}; no hay nada que bajar "
              f"(usa --forzar para reescribir).")
        return

    email, pwd = credenciales(a.env)
    token, quien = login(email, pwd)
    del pwd
    deseada = a.tienda or os.environ.get("LUCIDSALES_TIENDA") or cargar_env(a.env).get("LUCIDSALES_TIENDA")
    token, tienda = elegir_tienda(token, deseada)
    filas = bajar(token, ini.isoformat(), fin.isoformat())

    with open(destino, "w", encoding="utf-8") as fh:
        json.dump({"ventana_ini": ini.isoformat(), "ventana_fin": fin.isoformat(),
                   "dias": (fin - ini).days + 1, "tienda": tienda,
                   "bajado_en": datetime.datetime.now().isoformat(timespec="seconds"),
                   "insights": filas}, fh, ensure_ascii=False, indent=1)

    ventas = sum(int(num(f, "sells")) for f in filas)
    total = sum(num(f, "total") for f in filas)
    spend = sum(num(f, "spend") for f in filas)
    msj = sum(int(num(f, "messages")) for f in filas)
    print(f"sesion: {quien or 'ok'} · tienda: {tienda}")
    print(f"ventana {ini} -> {fin} ({(fin - ini).days + 1}d) · {len(filas)} filas · "
          f"{ventas} ventas · Q{total:,.2f} · ${spend:,.2f} · {msj} msj")
    print(f"escrito: {os.path.relpath(destino, BASE)}")
    if not filas:
        print("OJO: la API devolvio CERO filas. Revisa la fecha antes de ingerir.")


if __name__ == "__main__":
    main()
