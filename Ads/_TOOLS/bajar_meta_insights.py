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
  spend -> spend_usd · inline_link_clicks -> link_clicks · ad_id -> ad_id · el resto, nombres
  identicos. "ad_name"/"campaign_name"/"adset_name" reemplazan a "name" (que en el MCP viaja
  por nivel).
  `mensajes` YA NO se deriva de clics (22-sep-2026, g07-cimientos T1 — RETIRADO el estimado que
  vivia aca: mensajes = tasa_conv_whatsapp x link_clicks, doctrina que sigue viva SOLO para el
  camino xlsx de ingerir_meta.py, que no tiene "actions"). Esta API SI trae conversaciones reales
  de mensajeria en el campo "actions": ver mensajes_de() mas abajo para el action_type exacto.
  No se pide "results"/"cost_per_result": son columnas derivadas de Ads Manager segun el
  optimization_goal, y con "actions" ya resuelto no hacen falta.
  `ad_id` se pide y se escribe en _FACT_ENTREGA_ANUNCIO.csv (COLS_AD, dueno unico en
  ingerir_meta.py): permite el JOIN con _FACT_VENTAS.csv por id en vez de por nombre exacto,
  que se rompe con cada renombrado (evidencia g06, 22-sep-2026).

VENTANA DE LIQUIDACION (T1, 22-sep-2026): el gasto de Meta/LucidSales a veces llega CONGELADO a
mitad de dia (medido: 06/14/15/16/20-sep con 0.65-0.75 del gasto real; 07-11 y 17-19 en 1.000).
Con el ingestor viejo (append + dedupe) un dia parcial quedaba mal PARA SIEMPRE: la corrida
siguiente encontraba la misma llave y la descartaba como duplicado. Ahora, sin --fecha explicito,
la corrida por defecto RE-CONSULTA los ultimos upsert_fact.SETTLEMENT_WINDOW_DIAS dias (hoy 3,
ver esa constante) y REEMPLAZA por llave en vez de anexar (upsert_fact.upsert) — un dia que se
corrige en el panel de Meta se corrige tambien aca la noche siguiente, sin re-cargar el historico
entero. `--fecha` sigue trayendo UN dia puntual (uso manual); `--desde/--hasta` trae un tramo,
consultando la API UN DIA A LA VEZ (Graph API onsite no agrega bien un rango multi-dia a nivel
anuncio) y aplicando el mismo upsert por cada dia.

El upsert por LLAVE sola no alcanza cuando la identidad de la fila CAMBIA entre corridas
(medido en vivo: un backfill viejo sin `ad_id` convivio con el re-pull nuevo con `ad_id` —
llaves distintas, nunca colisionan, gasto por anuncio duplicado). Por eso el upsert de
`_FACT_ENTREGA.csv` y `_FACT_ENTREGA_ANUNCIO.csv` pasa `particion=(fuente, ventana_ini,
ventana_fin, cuenta_id)`: declara ese re-pull como la verdad completa de esa cuenta ese dia,
y una fila vieja de la misma cuenta/dia que no vino en la respuesta se ELIMINA, no convive.
Una cuenta-dia que fallo no aporta ninguna fila (ver el aislamiento de fallas en `main()`),
asi que su particion nunca se toca.

CREDENCIALES — nunca en el repo, nunca en git, nunca en la linea de comandos.
  Se leen de la variable de entorno META_SYSTEM_USER_TOKEN, y si no esta, de un .env local
  (default ~/.config/meta/.env, permisos 600). Este script NO imprime jamas el token.
  El token debe ser de un System User con permiso ads_read UNICAMENTE sobre las cuentas activas.

Uso:
    python Ads/_TOOLS/bajar_meta_insights.py                 # ventana de liquidacion (D-1..D-N)
    python Ads/_TOOLS/bajar_meta_insights.py --fecha 2026-09-15
    python Ads/_TOOLS/bajar_meta_insights.py --desde 2026-09-14 --hasta 2026-09-16
    python Ads/_TOOLS/bajar_meta_insights.py --dry-run

CODIGO DE SALIDA (T1b, 22-sep-2026) — una falla parcial NO debe tumbar la cadena nocturna completa:
    0 = todas las cuentas (y todos los dias pedidos) respondieron OK.
    2 = PARCIAL: al menos un intento cuenta-dia OK y al menos uno fallo. Las filas de los intentos
        que si respondieron ya se escribieron en _FACT_ENTREGA/_FACT_ENTREGA_ANUNCIO. El llamador
        nocturno (app/backend/vitalcom_app/workflows.py, paso "ciclo.bajar_meta") trata este codigo
        como AVISO: registra el detalle y sigue con el resto de la cadena.
    1 = todos los intentos fallaron, o no hay ninguna cuenta ACTIVE con metodo de pago, o un error
        fatal antes de procesar cuentas. Este codigo SI detiene la cadena nocturna.
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
import upsert_fact as uf    # UPSERT/migracion de esquema compartida (ver su docstring)

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROD = os.path.join(BASE, "PRODUCTOS")
DIMCU = os.path.join(PROD, "_DIM_CUENTAS.csv")
FACT, FACT_AD, BKDIR = im.FACT, im.FACT_AD, im.BKDIR

# P3 T3: mismo camino de escritura que ingerir_meta.py (db/escribir.py, Postgres es la verdad).
sys.path.insert(0, os.path.join(BASE, "db"))
import cargar as db_cargar      # noqa: E402
import escribir as db_escribir  # noqa: E402

TENANT_ID = im.TENANT_ID

API_VERSION = "v21.0"
API = f"https://graph.facebook.com/{API_VERSION}"
ENV_DEFAULT = os.path.join(os.path.expanduser("~"), ".config", "meta", ".env")
TIMEOUT = 60

# Nombres reales de la Graph API (nivel "ad"). "name" del MCP -> "ad_name" aca.
FIELDS = ["ad_id", "ad_name", "campaign_name", "adset_name", "spend", "impressions",
          "clicks", "inline_link_clicks", "cpm", "ctr", "frequency", "reach", "actions"]

RATE_LIMIT_CODES = {4, 17, 32, 613}

# action_type de "actions" para conversaciones de mensajeria iniciadas (Messenger/WhatsApp).
# REGLA (22-sep-2026, g07 T1): se prefiere la variante con ventana de atribucion de 7 dias
# (la que usa el reporte estandar de Ads Manager); si Meta no la trae para ese anuncio se acepta
# la variante sin sufijo "_7d" si esta presente. Si NINGUNA aparece, mensajes = 0 — ya no se
# deriva de clics (ese estimado queda retirado de este camino; sigue vivo solo en el xlsx, ver
# docstring del modulo).
ACTION_TYPE_MENSAJES = "onsite_conversion.messaging_conversation_started_7d"
ACTION_TYPE_MENSAJES_ALT = "onsite_conversion.messaging_conversation_started"


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


def mensajes_de(actions):
    """"actions" (lista de {"action_type","value",...} de la Graph API) -> conteo de
    conversaciones de mensajeria iniciadas. Ver ACTION_TYPE_MENSAJES para la regla completa."""
    if not actions:
        return 0
    por_tipo = {a.get("action_type"): a.get("value") for a in actions if isinstance(a, dict)}
    v = por_tipo.get(ACTION_TYPE_MENSAJES)
    if v is None:
        v = por_tipo.get(ACTION_TYPE_MENSAJES_ALT)
    return int(num(v))


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
            "ad_id": r.get("ad_id") or "",
            "mensajes": mensajes_de(r.get("actions")), "clicks_totales": int(num(r.get("clicks"))),
            "link_clicks": int(num(r.get("inline_link_clicks"))),
            "impresiones": int(num(r.get("impressions"))),
            "spend_usd": round(sp, 2), "pct_conv_clic_enlace": 0.0,
            "fuente": "MetaAPI-directo", "firma": firma, **ejes,
        })
    return propios, gasto_excl, n_excl


def agregar_a_conjunto(ads):
    """Suma las filas de anuncio al grano conjunto. Agrupa por la MISMA llave natural del hecho
    (`_clave_conjunto`: fuente, ventana, cuenta, campaña, conjunto): un tramo de varios días
    trae filas de cada día, y un día nunca se suma dentro de otro."""
    agg = {}
    for d in ads:
        k = _clave_conjunto(d)
        a = agg.setdefault(k, {**d, "clicks_totales": 0, "link_clicks": 0,
                                "impresiones": 0, "spend_usd": 0.0, "mensajes": 0})
        for c in ("clicks_totales", "link_clicks", "impresiones", "spend_usd", "mensajes"):
            a[c] += d[c]
    for a in agg.values():
        a["spend_usd"] = round(a["spend_usd"], 2)
    return [{c: a[c] for c in im.COLS} for a in agg.values()]


def _rango_fechas(ini, fin):
    d0, d1 = datetime.date.fromisoformat(ini), datetime.date.fromisoformat(fin)
    if d1 < d0:
        raise SystemExit(f"Rango invertido: {ini} > {fin}")
    out, d = [], d0
    while d <= d1:
        out.append(d.isoformat())
        d += datetime.timedelta(days=1)
    return out


def _clave_conjunto(fila):
    return (fila["fuente"], fila["ventana_ini"], fila["ventana_fin"], fila["cuenta_id"],
            fila["campana"], fila["conjunto"])


def _clave_anuncio(fila):
    """(fuente, ventana, cuenta, ad_id) — o la FIRMA cuando Meta no trae ad_id para ese anuncio
    (cuenta vieja, o el nombre no llego a tener firma). Documentado en g07-cimientos T1: es la
    llave natural del hecho de entrega por anuncio, la misma que usa el UPSERT."""
    return (fila["fuente"], fila["ventana_ini"], fila["ventana_fin"], fila["cuenta_id"],
            fila.get("ad_id") or fila.get("firma") or fila.get("anuncio") or "")


def main():
    hoy = datetime.date.today()
    p = argparse.ArgumentParser(description="Baja la entrega de Meta por Graph API directa.")
    p.add_argument("--fecha", help="dia YYYY-MM-DD puntual. Default: ventana de liquidacion")
    p.add_argument("--desde", help="inicio de un tramo YYYY-MM-DD (con --hasta)")
    p.add_argument("--hasta", help="fin de un tramo YYYY-MM-DD (con --desde)")
    p.add_argument("--env", default=ENV_DEFAULT)
    p.add_argument("--dry-run", action="store_true")
    a = p.parse_args()

    if a.desde or a.hasta:
        if not (a.desde and a.hasta):
            raise SystemExit("--desde y --hasta van juntos.")
        fechas = _rango_fechas(a.desde, a.hasta)
    elif a.fecha:
        fechas = [a.fecha]
    else:
        # Ventana de liquidacion (T1): re-consulta D-1..D-N reemplazando por llave, no un
        # solo dia anexado. N = upsert_fact.SETTLEMENT_WINDOW_DIAS.
        ayer = hoy - datetime.timedelta(days=1)
        desde = ayer - datetime.timedelta(days=uf.SETTLEMENT_WINDOW_DIAS - 1)
        fechas = _rango_fechas(desde.isoformat(), ayer.isoformat())

    for f in fechas:
        if datetime.date.fromisoformat(f) >= hoy:
            print(f"AVISO: {f} es hoy o futuro. La doctrina manda traer siempre dias cerrados.")

    token = token_de(a.env)
    cuentas = leer_cuentas_activas()
    if not cuentas:
        raise SystemExit("_DIM_CUENTAS.csv no tiene ninguna cuenta ACTIVE con tiene_metodo_pago=SI.")

    dim, _ = im.leer_dim()
    todos, gasto_excl_tot, n_excl_tot = [], 0.0, 0
    fallidas, intentos = [], 0
    for fecha in fechas:
        print(f"-- {fecha} --")
        for c in cuentas:
            intentos += 1
            print(f"  {c['cuenta_alias']:10} ({c['cuenta_id']}) ...", end=" ")
            try:
                propios, gx, nx = procesar_cuenta(c, fecha, token, dim)
            except (SystemExit, Exception) as e:
                # Aislamiento de fallas: una cuenta que no responde (permiso denegado, red caida) no
                # tumba a las demas ni a los demas dias. Se reporta y se sigue; el codigo de salida
                # queda en 1 o 2 al final segun cuantos intentos fallaron.
                msg = str(e) or repr(e)
                print(f"FALLO: {msg}")
                print(f"ERROR en cuenta {c['cuenta_alias']} ({c['cuenta_id']}) fecha {fecha}: {msg}",
                      file=sys.stderr)
                fallidas.append((fecha, c["cuenta_alias"], msg))
                continue
            gasto_excl_tot += gx
            n_excl_tot += nx
            todos.extend(propios)
            print(f"{len(propios)} anuncios propios · {nx} ajenos/sin-DIM excluidos (${gx:.2f})")

    print(f"\ngasto ajeno excluido: ${gasto_excl_tot:.2f} en {n_excl_tot} anuncios")
    if fallidas:
        detalle = ", ".join(f"{alias}@{fecha}" for fecha, alias, _ in fallidas)
        print(f"INTENTOS CON ERROR ({len(fallidas)} de {intentos}): {detalle}", file=sys.stderr)
    # Contrato de salida (22-sep-2026, T1b): 0 = todo OK · 2 = parcial (al menos un intento
    # cuenta-dia OK y al menos uno fallo; las filas de los que si respondieron ya se escriben) ·
    # 1 = todos los intentos fallaron (o error fatal). El llamador nocturno (workflows.py) trata
    # 2 como aviso que NO detiene la cadena; 1 si la detiene. Ver skill recopilar-lucidsales/SKILL.md.
    if not fallidas:
        resultado = 0
    elif len(fallidas) < intentos:
        resultado = 2
    else:
        resultado = 1

    if not todos:
        print("Sin anuncios propios en la ventana pedida.")
        return resultado

    conjuntos = agregar_a_conjunto(todos)

    if a.dry_run:
        print(f"\n[dry-run] {len(conjuntos)} filas conjunto · {len(todos)} filas anuncio "
              f"listas para UPSERT — no se escribio nada.")
        return resultado

    # `particion` = (fuente, ventana_ini, ventana_fin, cuenta_id): exactamente el ambito de
    # un intento cuenta-dia (T1, segunda vuelta). Declara ese re-pull como la VERDAD COMPLETA
    # de esa cuenta ese dia: una fila vieja de la MISMA cuenta/dia que no vino en esta
    # respuesta se elimina (cierra el caso real del backfill sin ad_id que duplicaba el
    # gasto por anuncio, ver docstring de upsert_fact.py). Una cuenta-dia que fallo no
    # aporta filas a `todos`/`conjuntos` (ver el `continue` en el bucle de mas arriba), asi
    # que su particion nunca aparece aca y nunca se toca lo que ya habia.
    #
    # P3 T3: mismo camino de Postgres que ingerir_meta.py -- db/escribir.upsert() acepta
    # `particion` con la misma semantica que upsert_fact.upsert() (fusionar() es compartida).
    PARTICION = ("fuente", "ventana_ini", "ventana_fin", "cuenta_id")
    # El directorio de escritura sale de FACT/FACT_AD (nunca de la constante PROD): ver el mismo
    # comentario en ingerir_meta.py -- las pruebas monkeypatchean FACT/FACT_AD a un directorio
    # temporal, y escribir sobre PROD igual pisaria PRODUCTOS/ real.
    prod_dir_conjunto = os.path.dirname(FACT)
    prod_dir_anuncio = os.path.dirname(FACT_AD)
    try:
        con = db_cargar.conectar()
    except Exception as exc:
        print(f"\n⛔ Postgres no disponible: no se pudo escribir _FACT_ENTREGA*.csv (nunca se "
              f"escribe el CSV directo). Detalle: {exc}", file=sys.stderr)
        return 1
    try:
        db_escribir.verificar_csv_sincronizado(con, "entrega_conjunto_dia", prod_dir_conjunto,
                                                tenant_id=TENANT_ID)
        reemp_c, nuevas_c, sc_c, elim_c = db_escribir.upsert(
            con, "entrega_conjunto_dia", conjuntos, key=_clave_conjunto, particion=PARTICION,
            prod_dir=prod_dir_conjunto, bkdir=BKDIR, tenant_id=TENANT_ID)
        print(f"\n_FACT_ENTREGA.csv: {reemp_c} reemplazadas · {nuevas_c} nuevas · "
              f"{elim_c} eliminadas (superadas por el re-pull) · {sc_c} sin cambio "
              f"(Postgres es la verdad)")
        db_escribir.verificar_csv_sincronizado(con, "entrega_anuncio_dia", prod_dir_anuncio,
                                                tenant_id=TENANT_ID)
        reemp_a, nuevas_a, sc_a, elim_a = db_escribir.upsert(
            con, "entrega_anuncio_dia", todos, key=_clave_anuncio, particion=PARTICION,
            prod_dir=prod_dir_anuncio, bkdir=BKDIR, tenant_id=TENANT_ID)
        print(f"_FACT_ENTREGA_ANUNCIO.csv: {reemp_a} reemplazadas · {nuevas_a} nuevas · "
              f"{elim_a} eliminadas (superadas por el re-pull) · {sc_a} sin cambio "
              f"(Postgres es la verdad)")
    except db_escribir.ErrorEscritura as exc:
        print(f"\n⛔ {exc}", file=sys.stderr)
        return 1
    finally:
        con.close()
    return resultado


if __name__ == "__main__":
    sys.exit(main())
