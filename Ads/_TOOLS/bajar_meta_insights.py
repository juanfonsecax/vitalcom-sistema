#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""bajar_meta_insights.py — trae la ENTREGA de Meta por API directa, sin MCP y sin xlsx.

POR QUE EXISTE (16-sep-2026): el conector MCP de Meta funciona perfecto en sesion interactiva pero
se cuelga indefinidamente dentro de una tarea programada sin supervision — probado 3 de 3 en vivo
esa noche (con el permiso de lectura ya aprobado, y hasta en una sesion recien creada). La
aprobacion de una herramienta MCP remota parece exigir un clic humano en un dialogo que una tarea
sin supervision nunca puede mostrar. La automatizacion nocturna necesita un camino que no dependa
de ese dialogo. Este script pega directo a la Graph API de Meta (el mismo dato que ve el MCP, el
mismo endpoint que usa cualquier herramienta de reporting de Ads) con un token de System User de
SOLO LECTURA (permiso ads_read) — mismo patron que bajar_lucidsales.py: API directa, sin navegador,
sin conector interactivo.

AMBITO: SOLO LECTURA. Este script nunca crea, publica ni modifica nada en Meta. Publicar sigue
siendo 100% MCP, interactivo, con confirmacion del operador orden por orden (invariante 13,
decision del 09-sep-2026). El token que usa este script no debe tener permiso ads_management.

CUENTAS: se leen de PRODUCTOS/_DIM_CUENTAS.csv, filtrando estado_cuenta=ACTIVE AND
tiene_metodo_pago=SI. Hoy son GTR7, GTR0, GTR1, GTR3, GTR13. `mcp_habilitado` describe el conector
INTERACTIVO de Meta (publicar por MCP) — esta lectura es Graph API directa y no lo usa, asi que no
filtra por el (corregido 22-sep-2026: excluia GTR13/CLEARSTEM, que esta ACTIVE y con metodo de pago
pero con MCP en rollout). Agregar o retirar una cuenta es editar esa fila — este script no tiene
ninguna cuenta hardcodeada.

MONEDA: `procesar_cuenta()` convierte COP a USD con `im.TASA_COP_USD` (mismo patron que
ingerir_meta.py) ANTES de sumar nada, asi que una cuenta COP nunca se mezcla en USD sin convertir.
Hoy ninguna cuenta COP pasa el filtro (las dos que existen en el DIM estan RETIRADA o sin metodo de
pago), pero la conversion queda activa por si se da de alta una.

FILTRADO (importante): GTR7 es una cuenta COMPARTIDA de agencia con clientes ajenos a VitalCom
(verificado en vivo 16-sep-2026: conviven ahi DR MELAXIN, MAG, TRULY X1 GT, OLD SCHOOL VENTAS).
Este script NUNCA escribe un anuncio que no clasifique a un producto_key real via
_DIM_CONJUNTOS.csv (misma funcion producto_de() de ingerir_meta.py) — lo excluye y lo cuenta
aparte, nunca lo mezcla en el CSV. Si un conjunto propio nuevo todavia no esta en el DIM, tambien
sale como excluido: revisar el conteo de excluidos si crece de golpe.

MAPEO DE CAMPOS (Graph API real, no el alias del MCP — verificar contra el primer pull real):
  spend -> spend_usd · inline_link_clicks -> link_clicks · el resto, nombres identicos.
  "ad_name"/"campaign_name"/"adset_name" reemplazan a "name" (que en el MCP viaja por nivel).
  No se pide "results"/"cost_per_result": son columnas derivadas de Ads Manager segun el
  optimization_goal: la doctrina ya deriva mensajes = tasa_conv_whatsapp x link_clicks (ver
  ingerir_meta.py), asi que no hacen falta aca.

CREDENCIALES — nunca en el repo, nunca en git, nunca en la linea de comandos.
  Se leen de la variable de entorno META_SYSTEM_USER_TOKEN, y si no esta, de un .env local
  (default ~/.config/meta/.env, permisos 600). Este script NO imprime jamas el token.
  El token debe ser de un System User con permiso ads_read UNICAMENTE sobre las cuentas activas.

Uso:
    python Ads/_TOOLS/bajar_meta_insights.py                 # trae AYER, todas las cuentas activas
    python Ads/_TOOLS/bajar_meta_insights.py --fecha 2026-09-15
    python Ads/_TOOLS/bajar_meta_insights.py --dry-run
"""
import sys, os, csv, json, time, shutil, argparse, datetime, warnings
import urllib.request, urllib.parse, urllib.error

# reconfigure() en vez de reemplazar sys.stdout/stderr por un TextIOWrapper nuevo: este script
# importa ingerir_meta.py, que hace su propio ajuste de encoding, y dos wrappers separados sobre
# el mismo buffer terminan pisandose ("ValueError: I/O operation on closed file", medido 16-sep-2026
# al integrar los dos scripts). reconfigure() ajusta el objeto existente sin crear uno nuevo.
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
warnings.filterwarnings("ignore")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ingerir_meta as im   # reusa parsear_firma, leer_dim, producto_de, COLS, COLS_AD, TASA_COP_USD

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROD = os.path.join(BASE, "PRODUCTOS")
DIMCU = os.path.join(PROD, "_DIM_CUENTAS.csv")
FACT, FACT_AD, BKDIR = im.FACT, im.FACT_AD, im.BKDIR

API_VERSION = "v21.0"
API = f"https://graph.facebook.com/{API_VERSION}"
ENV_DEFAULT = os.path.join(os.path.expanduser("~"), ".config", "meta", ".env")
TIMEOUT = 60

# Nombres reales de la Graph API (nivel "ad"). "name" del MCP -> "ad_name" aca.
FIELDS = ["ad_name", "campaign_name", "adset_name", "spend", "impressions",
          "clicks", "inline_link_clicks", "cpm", "ctr", "frequency", "reach"]

RATE_LIMIT_CODES = {4, 17, 32, 613}


def cargar_env(path):
    """Lee un .env simple (CLAVE=valor). No expande, no ejecuta, no imprime valores."""
    if not os.path.exists(path):
        return {}
    out = {}
    with open(path, encoding="utf-8-sig") as fh:
        for linea in fh:
            linea = linea.strip()
            if not linea or linea.startswith("#") or "=" not in linea:
                continue
            k, v = linea.split("=", 1)
            out[k.strip()] = v.strip().strip('"').strip("'")
    return out


def token_de(env_path):
    tok = os.environ.get("META_SYSTEM_USER_TOKEN")
    if not tok:
        tok = cargar_env(env_path).get("META_SYSTEM_USER_TOKEN")
    if not tok:
        raise SystemExit(
            "FALTA EL TOKEN.\n"
            f"  Pone META_SYSTEM_USER_TOKEN=<token> en {env_path}\n"
            "  (o exportalo como variable de entorno).\n"
            "  Ese archivo va FUERA del repo y con permisos 600.\n"
            "  El token debe ser de un System User con permiso ads_read UNICAMENTE."
        )
    return tok


def pedir_json(url):
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            return json.loads(e.read().decode("utf-8", "replace"))
        except Exception:
            raise SystemExit(f"HTTP {e.code} en la Graph API y el cuerpo no es JSON.")
    except urllib.error.URLError as e:
        raise SystemExit(f"Sin conexion con Meta: {e.reason}")


def insights_de(cuenta_id, fecha, token, reintentos=3):
    params = {
        "level": "ad",
        "time_range": json.dumps({"since": fecha, "until": fecha}),
        "time_increment": "1",
        "fields": ",".join(FIELDS),
        "limit": "500",
        "access_token": token,
    }
    url = f"{API}/act_{cuenta_id}/insights?{urllib.parse.urlencode(params)}"
    filas = []
    for intento in range(reintentos):
        data = pedir_json(url)
        if "error" in data:
            err = data["error"]
            if err.get("code") in RATE_LIMIT_CODES and intento < reintentos - 1:
                espera = 5 * (intento + 1)
                print(f"    ! rate limit, esperando {espera}s...")
                time.sleep(espera)
                continue
            raise SystemExit(f"Graph API error en cuenta {cuenta_id}: {err.get('message', err)}")
        filas.extend(data.get("data", []))
        siguiente = data.get("paging", {}).get("next")
        while siguiente:
            data = pedir_json(siguiente)
            filas.extend(data.get("data", []))
            siguiente = data.get("paging", {}).get("next")
        return filas
    return filas


def num(v, default=0.0):
    try:
        return float(v) if v not in (None, "") else default
    except (TypeError, ValueError):
        return default


def leer_cuentas_activas():
    """Cuentas para LEER entrega por Graph API directa. No filtra por mcp_habilitado: ese campo es
    del conector interactivo de publicacion (ver docstring del modulo), irrelevante para una
    lectura que no pasa por MCP."""
    with open(DIMCU, encoding="utf-8") as fh:
        filas = list(csv.DictReader(fh))
    return [r for r in filas if r.get("estado_cuenta") == "ACTIVE"
            and r.get("tiene_metodo_pago") == "SI"]


def procesar_cuenta(cuenta, fecha, token, dim):
    alias = cuenta["cuenta_alias"].replace(" ", "")   # "GTR 7" -> "GTR7", igual que el resto del sistema
    cuenta_id = cuenta["cuenta_id"]
    moneda = (cuenta.get("moneda") or "USD").strip().upper()
    crudos = insights_de(cuenta_id, fecha, token)

    propios, gasto_excl, n_excl = [], 0.0, 0
    for r in crudos:
        anuncio = r.get("ad_name") or ""
        campana = r.get("campaign_name") or ""
        conjunto = r.get("adset_name") or ""
        pk = im.producto_de(campana, conjunto, dim)
        sp = num(r.get("spend"))
        if moneda == "COP":
            sp = sp / im.TASA_COP_USD
        if pk == "SIN_CLASIFICAR":
            gasto_excl += sp
            n_excl += 1
            continue   # ajeno a VitalCom (cuenta compartida de agencia) o conjunto sin DIM todavia
        firma, ejes = im.parsear_firma(anuncio)
        propios.append({
            "ventana_ini": fecha, "ventana_fin": fecha, "dias": 1,
            "producto_key": pk, "cuenta_id": cuenta_id, "cuenta_alias": alias,
            "campana": campana, "conjunto": conjunto, "anuncio": anuncio,
            "mensajes": 0, "clicks_totales": int(num(r.get("clicks"))),
            "link_clicks": int(num(r.get("inline_link_clicks"))),
            "impresiones": int(num(r.get("impressions"))),
            "spend_usd": round(sp, 2), "pct_conv_clic_enlace": 0.0,
            "fuente": "MetaAPI-directo", "firma": firma, **ejes,
        })
    return propios, gasto_excl, n_excl


def agregar_a_conjunto(ads):
    agg = {}
    for d in ads:
        k = (d["cuenta_alias"], d["campana"], d["conjunto"])
        a = agg.setdefault(k, {**d, "clicks_totales": 0, "link_clicks": 0,
                                "impresiones": 0, "spend_usd": 0.0})
        for c in ("clicks_totales", "link_clicks", "impresiones", "spend_usd"):
            a[c] += d[c]
    for a in agg.values():
        a["spend_usd"] = round(a["spend_usd"], 2)
    return [{c: a[c] for c in im.COLS} for a in agg.values()]


def main():
    hoy = datetime.date.today()
    p = argparse.ArgumentParser(description="Baja la entrega de Meta por Graph API directa.")
    p.add_argument("--fecha", help="dia YYYY-MM-DD. Default: ayer")
    p.add_argument("--env", default=ENV_DEFAULT)
    p.add_argument("--dry-run", action="store_true")
    a = p.parse_args()

    fecha = a.fecha or (hoy - datetime.timedelta(days=1)).isoformat()
    if datetime.date.fromisoformat(fecha) >= hoy:
        print(f"AVISO: {fecha} es hoy o futuro. La doctrina manda traer siempre AYER cerrado.")

    token = token_de(a.env)
    cuentas = leer_cuentas_activas()
    if not cuentas:
        raise SystemExit("_DIM_CUENTAS.csv no tiene ninguna cuenta ACTIVE con tiene_metodo_pago=SI.")

    dim, _ = im.leer_dim()
    todos, gasto_excl_tot, n_excl_tot = [], 0.0, 0
    fallidas = []
    for c in cuentas:
        print(f"  {c['cuenta_alias']:10} ({c['cuenta_id']}) ...", end=" ")
        try:
            propios, gx, nx = procesar_cuenta(c, fecha, token, dim)
        except (SystemExit, Exception) as e:
            # Aislamiento de fallas: una cuenta que no responde (permiso denegado, red caida) no
            # tumba a las demas. Se reporta y se sigue; el codigo de salida queda en 1 al final.
            msg = str(e) or repr(e)
            print(f"FALLO: {msg}")
            print(f"ERROR en cuenta {c['cuenta_alias']} ({c['cuenta_id']}): {msg}", file=sys.stderr)
            fallidas.append((c["cuenta_alias"], msg))
            continue
        gasto_excl_tot += gx
        n_excl_tot += nx
        todos.extend(propios)
        print(f"{len(propios)} anuncios propios · {nx} ajenos/sin-DIM excluidos (${gx:.2f})")

    print(f"\nfecha {fecha} · gasto ajeno excluido: ${gasto_excl_tot:.2f} en {n_excl_tot} anuncios")
    if fallidas:
        print(f"CUENTAS CON ERROR ({len(fallidas)} de {len(cuentas)}): "
              + ", ".join(alias for alias, _ in fallidas), file=sys.stderr)
    resultado = 1 if fallidas else 0

    if not todos:
        print("Sin anuncios propios ese dia.")
        return resultado

    conjuntos = agregar_a_conjunto(todos)

    ads_ex = list(csv.DictReader(open(FACT_AD, encoding="utf-8"))) if os.path.exists(FACT_AD) else []
    llaves_ad = {(r["ventana_ini"], r["ventana_fin"], r["cuenta_alias"], r["campana"],
                  r["conjunto"], r["anuncio"], r["fuente"]) for r in ads_ex}
    nuevos_ads = [d for d in todos if (d["ventana_ini"], d["ventana_fin"], d["cuenta_alias"],
                  d["campana"], d["conjunto"], d["anuncio"], d["fuente"]) not in llaves_ad]

    existentes = list(csv.DictReader(open(FACT, encoding="utf-8"))) if os.path.exists(FACT) else []
    llaves = {(r["ventana_ini"], r["ventana_fin"], r["cuenta_alias"], r["campana"],
               r["conjunto"], r["fuente"]) for r in existentes}
    nuevos_conj = [d for d in conjuntos if (d["ventana_ini"], d["ventana_fin"], d["cuenta_alias"],
                   d["campana"], d["conjunto"], d["fuente"]) not in llaves]

    print(f"{len(nuevos_conj)} filas conjunto nuevas · {len(nuevos_ads)} filas anuncio nuevas "
          f"(duplicados omitidos automaticamente)")

    if a.dry_run:
        print("[dry-run] no se escribio nada.")
        return resultado
    if not nuevos_ads and not nuevos_conj:
        print("nada que escribir (ya estaba cargado).")
        return resultado

    os.makedirs(BKDIR, exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    if nuevos_conj:
        existe = os.path.exists(FACT)
        if existe:
            shutil.copy2(FACT, os.path.join(BKDIR, f"_FACT_ENTREGA_{stamp}.csv"))
        with open(FACT, "a" if existe else "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=im.COLS)
            if not existe:
                w.writeheader()
            for r in nuevos_conj:
                w.writerow(r)
        print(f"escritas {len(nuevos_conj)} filas en {os.path.relpath(FACT, BASE)}")
    if nuevos_ads:
        existe = os.path.exists(FACT_AD)
        if existe:
            shutil.copy2(FACT_AD, os.path.join(BKDIR, f"_FACT_ENTREGA_ANUNCIO_{stamp}.csv"))
        with open(FACT_AD, "a" if existe else "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=im.COLS_AD)
            if not existe:
                w.writeheader()
            for r in nuevos_ads:
                w.writerow({c: r.get(c, "") for c in im.COLS_AD})
        print(f"escritas {len(nuevos_ads)} filas en {os.path.relpath(FACT_AD, BASE)}")
    return resultado


if __name__ == "__main__":
    sys.exit(main())
