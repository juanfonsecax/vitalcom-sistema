#!/usr/bin/env python3
"""
ingerir_lucidsales.py — carga exports diarios de LucidSales a _FACT_VENTAS.csv

Uso:
    python Ads/_TOOLS/ingerir_lucidsales.py <archivo.xlsx|.json> [<archivo2> ...]
    python Ads/_TOOLS/ingerir_lucidsales.py --dir <carpeta>   (toma report-*.xlsx|.json)
    ... [--rol BASE|CONTROL] [--fuente LucidSales|LucidSales_CuentaB] [--dry-run]

Dos fuentes, misma data: el .xlsx que el operador bajaba a mano del panel, y el .json
que baja `bajar_lucidsales.py` contra la API (el xlsx era un volcado literal de ese
mismo JSON hecho por el navegador). El JSON es el camino automatizable.

Reglas que implementa (DOCTRINA/DATA_PLAYBOOK.md + runbook de la auditoría):
  · header en la FILA 4 (header=3); descarta el bloque "Resumen" (fila sin cuenta NI adId).
  · CONSERVA las ventas ORGANICAS (adId="organico", sin cuenta): son ventas reales.
  · mapeo adSetTitle->conjunto · adTitle->anuncio · sells->ventas · total->total_q · spend->spend_usd.
  · CP1 (1346891653335162) factura en COP -> spend_COP / 3152.5 = spend_USD (APR-028).
  · IDENTIDAD por ad_id Y por nombre (basta que coincida una, ver `llaves()`): el nombre no
    sobrevive a los renombrados y el ad_id historico quedo en notacion cientifica.
  · UPSERT sobre ventana de liquidacion (22-sep-2026, T1): una fila cuya llave natural
    (`clave_natural()`) ya existe en _FACT_VENTAS.csv se REEMPLAZA, no se descarta. Necesario
    porque LucidSales a veces entrega el gasto/ventas de un dia CONGELADO a medio dia (medido
    06/14/15/16/20-sep-2026: 0.65-0.75 del gasto real de Meta) y antes ese dia quedaba mal para
    siempre. `rol_ventana` viaja en la llave: CONTROL nunca reemplaza a BASE ni viceversa. Ver
    `upsert_fact.py` (el helper, compartido con `bajar_meta_insights.py`).
  · La fecha sale del NOMBRE del archivo (report-YYYY-MM-DD-YYYY-MM-DD.xlsx), no del contenido.
  · Escribe con csv writer real (regla 22 de CLAUDE.md). Backup previo en _RESPALDOS/backups_csv/ (ver
    upsert_fact.respaldos_dir()).
  · ad_id se formatea con s_id() (no notación científica cuando se puede).
"""
import sys, io, os, re, csv, json, datetime

# Windows abre la consola en cp1252: un print con un simbolo fuera de ese mapa revienta con
# UnicodeEncodeError y el script sale con exit 1 AUNQUE el trabajo ya se completo. Es el mismo
# bug del 18-ago en gen_dashboard.py; aca lo disparaba el check final del JOIN (03-sep).
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import alias
import upsert_fact   # noqa: E402  (UPSERT sobre ventana de liquidacion, ver su docstring)

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROD = os.path.join(BASE, "PRODUCTOS")
FACT = os.path.join(PROD, "_FACT_VENTAS.csv")
DIMC = os.path.join(PROD, "_DIM_CONJUNTOS.csv")
DIMP = os.path.join(PROD, "_DIM_PRODUCTOS.csv")
DIMCTAS = os.path.join(PROD, "_DIM_CUENTAS.csv")
BKDIR = upsert_fact.respaldos_dir(BASE, "backups_csv")

# P3 T3: la VERDAD de _FACT_VENTAS.csv pasa a vivir en Postgres (raw.venta / core.venta); el CSV
# en PRODUCTOS/ se vuelve el ESPEJO, regenerado por db/escribir.py DESPUES del commit. Nunca se
# cae de vuelta a escribir el CSV a mano si Postgres falla (ver db/escribir.py, punto 4 de su
# docstring). TENANT_ID es un punto de override para pruebas (test_ingerir_lucidsales.py aisla
# cada escenario en su propio tenant dentro de `vitalcom_test`, nunca toca `vitalcom` real).
sys.path.insert(0, os.path.join(BASE, "db"))
import cargar as db_cargar      # noqa: E402
import escribir as db_escribir  # noqa: E402

TENANT_ID = "vitalcom"

# Tasas de conversion a USD por moneda de facturacion (APR-028, medida contra banco).
# La cuenta y su moneda salen de _DIM_CUENTAS.csv; agregar una fila ahi con moneda
# distinta de USD y sin tasa acá bloquea la ingesta en vez de costear mal en silencio.
TASAS_A_USD = {"COP": 3152.5}

COLS = ["ventana_ini","ventana_fin","dias","rol_ventana","producto_key","producto",
        "cuenta_id","cuenta_alias","campana","conjunto","anuncio","mensajes","clicks",
        "impresiones","spend_usd","ventas","total_q","moneda_origen","fuente","ad_id"]


def cargar_productos(path=None):
    """producto_key -> keywords (lower) para reconocer el nombre que manda LucidSales.

    Hasta el 22-sep-2026 el mapeo era un diccionario PROD_KEY cableado a mano en este
    archivo: un producto nuevo (Turmeric, simulación) caía en SIN_CLASIFICAR y perdía
    120 filas / 35 ventas / $165.69 sin una sola alerta, porque nadie agregó su línea.
    Las keywords salen de lo que YA está declarado en _DIM_PRODUCTOS.csv —el propio
    producto_key y la primera palabra de nombre_display/slug_carpeta—, nunca de una
    lista aparte que alguien tiene que recordar mantener sincronizada.
    """
    with open(path or DIMP, newline="", encoding="utf-8") as fh:
        filas = list(csv.DictReader(fh))
    out = {}
    for r in filas:
        pk = (r.get("producto_key") or "").strip()
        if not pk:
            continue
        kws = {pk.lower(), pk.lower().replace("_", " ")}
        for campo in ("nombre_display", "slug_carpeta"):
            v = (r.get(campo) or "").strip()
            if v:
                primera = re.split(r"[\s_]+", v)[0].lower()
                if len(primera) >= 4:      # evita keywords de 1-3 letras, ambiguas
                    kws.add(primera)
        out[pk] = sorted(k for k in kws if k)
    return out


def cargar_cuentas(path=None):
    """cuenta_id -> {alias, moneda} desde _DIM_CUENTAS.csv.

    alias sale de cuenta_alias SIN el espacio ("GTR 7" -> "GTR7"): el resto del
    sistema (_FACT_VENTAS.csv, _DIM_CONJUNTOS.csv, alias.py) siempre usa el formato
    compacto. Antes del 22-sep-2026 era un diccionario ALIAS cableado en este mismo
    archivo — una cuenta nueva quedaba con su id crudo como alias, sin que nadie lo
    notara hasta la auditoría.
    """
    with open(path or DIMCTAS, newline="", encoding="utf-8") as fh:
        filas = list(csv.DictReader(fh))
    out = {}
    for r in filas:
        cid = (r.get("cuenta_id") or "").strip()
        if not cid:
            continue
        out[cid] = {
            "alias": (r.get("cuenta_alias") or cid).strip().replace(" ", ""),
            "moneda": (r.get("moneda") or "USD").strip().upper(),
        }
    return out


_IDS_PERDIDOS = 0  # ad_id/cuenta_id irrecuperables en esta corrida (ver s_id() y el resumen final)
_RE_NOTACION_CIENTIFICA = re.compile(r"[eE][+-]?\d+$")


def reiniciar_ids_perdidos():
    """Solo para pruebas: reinicia el contador global entre corridas simuladas."""
    global _IDS_PERDIDOS
    _IDS_PERDIDOS = 0


def ids_perdidos():
    return _IDS_PERDIDOS


def s_id(v):
    """Formatea un id de Meta (ad_id, cuenta_id) SIN notación científica — nunca un id falso.

    Bug real (21-ago): `repr(float)` emitía notación científica ('1.20e+17') para todo id
    > 1e15, y esa notación quedaba escrita tal cual en _FACT_VENTAS.csv. Corregido 22-sep: un
    id > 2**53 YA perdió precisión en cuanto llegó como float64 (que solo sostiene ~15-17
    dígitos significativos) — reconstruirlo con int()/round() no arregla nada, solo cambia
    una cifra rota por OTRA cifra rota que parece válida. Para ese caso se devuelve "" (nunca
    un id incorrecto) y se cuenta en `_IDS_PERDIDOS`, que `main()` imprime en el resumen.
    """
    global _IDS_PERDIDOS
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return ""
    if isinstance(v, bool):
        return str(int(v))
    if isinstance(v, int):
        return str(v)
    if isinstance(v, float):
        if v != v or v in (float("inf"), float("-inf")):
            return ""
        if abs(v) > 2 ** 53:
            _IDS_PERDIDOS += 1
            return ""
        return str(int(v))
    t = str(v).strip()
    if not t or t.lower() == "nan":
        return ""
    if _RE_NOTACION_CIENTIFICA.search(t):
        # ya venía corrompido en el JSON/xlsx de origen (una corrida vieja, u otro sistema
        # que lo formateó mal antes de llegar acá): no hay como reconstruirlo bien.
        _IDS_PERDIDOS += 1
        return ""
    return t


def s_txt(v):
    """Texto limpio: NaN de pandas y None -> "".

    `str(NaN or "")` devuelve "nan" porque NaN es truthy: sin esto, la fila de venta
    ORGANICA (que no trae adSetTitle ni adTitle) entra al CSV con conjunto="nan" y
    dispara un falso "conjunto SIN dimension".
    """
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return ""
    t = str(v).strip()
    return "" if t.lower() == "nan" else t


def s_num(v, default=0):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return default
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def producto_key(nombre, productos):
    n = (nombre or "").lower()
    for pk, kws in productos.items():
        if any(kw in n for kw in kws):
            return pk
    return "SIN_CLASIFICAR"


def ventana_de_nombre(path):
    """(ini, fin, dias) desde report-<ini>-<fin>.<ext>.

    Antes se leía SOLO la primera fecha y se forzaba dias=1 · ventana_fin=ventana_ini.
    Con el export diario daba igual, pero el CONTROL SEMANAL de los lunes (7 días, que
    manda DATA_PLAYBOOK) entraba etiquetado como un día suelto. Ahora la ventana sale
    entera del nombre; un nombre con una sola fecha sigue siendo 1 día.
    """
    fs = re.findall(r"\d{4}-\d{2}-\d{2}", os.path.basename(path))
    if not fs:
        raise SystemExit(f"No pude leer la fecha del nombre: {path}")
    ini, fin = fs[0], (fs[1] if len(fs) > 1 else fs[0])
    d0, d1 = datetime.date.fromisoformat(ini), datetime.date.fromisoformat(fin)
    if d1 < d0:
        raise SystemExit(f"Ventana invertida en el nombre: {path}")
    return ini, fin, (d1 - d0).days + 1


def fecha_de_nombre(path):
    return ventana_de_nombre(path)[0]


def es_detalle(r):
    """True si la fila es una venta real; False si es del bloque Resumen del export.

    Antes el corte era "accountTitle vacío = Resumen", y eso tiraba a la basura las
    VENTAS ORGÁNICAS: LucidSales las emite con accountTitle vacío y `adId='organico'`
    porque no vienen de ninguna cuenta publicitaria. Medido el 01-sep-2026: Q198 de
    CLEARSTEM (1 de las 9 ventas del día) se perdían en silencio, y el CSV cerraba en
    Q1,650 contra los Q1,848 del panel. Es la subestimación que DATA_PLAYBOOK ya
    advertía ("VARICOSE vendió 5 veces con pauta CERO").

    El corte correcto es: tiene cuenta O tiene adId. Las filas del bloque Resumen
    (totalSales, spend, ctrCount, paidSales…) no tienen ninguno de los dos.
    """
    def lleno(k):
        v = r.get(k)
        # NaN de pandas es truthy y str(NaN) == "nan": sin este chequeo, las filas del
        # bloque Resumen del xlsx pasarían el filtro y entrarían como ventas.
        if v is None or (isinstance(v, float) and pd.isna(v)):
            return False
        return bool(str(v).strip()) and str(v).strip().lower() != "nan"

    return lleno("accountTitle") or lleno("adId")


def registros_xlsx(path):
    # NO se fuerza dtype=str en adId/accountTitle: el xlsx de LucidSales guarda esas celdas como
    # NUMERO (confirmado en enriquecer_adid.py), y openpyxl ya las entrega como float64 ANTES de
    # que pandas pueda aplicar cualquier dtype — la precisión de un id de 17-18 dígitos se pierde
    # en Excel/openpyxl, no en Python. Forzar dtype=str acá solo convertiría ese float YA roto en
    # un string que PARECE un id válido (dígitos finales distintos de los reales) sin disparar la
    # detección de s_id(): sería peor que dejarlo como float, porque s_id() SÍ sabe reconocer un
    # float > 2**53 como irrecuperable y devolver "" en vez de un id falso.
    df = pd.read_excel(path, header=3)
    return [r for r in df.to_dict("records") if es_detalle(r)]


def registros_json(path):
    """JSON crudo de bajar_lucidsales.py (la MISMA data que el xlsx, sin el rodeo).

    La API entrega 'Producto' y 'Test' capitalizados; el exportador de Excel del panel
    los minusculiza. Se normalizan acá para que las dos fuentes carguen idéntico.
    """
    with open(path, encoding="utf-8") as fh:
        crudo = json.load(fh)
    filas = crudo.get("insights", crudo) if isinstance(crudo, dict) else crudo
    out = []
    for r in filas:
        r = dict(r)
        for cap, low in (("Producto", "producto"), ("Test", "test")):
            if cap in r and low not in r:
                r[low] = r.pop(cap)
        if not es_detalle(r):
            continue          # equivalente a las filas de Resumen del xlsx
        out.append(r)
    return out


def leer_export(path, rol, fuente, productos, cuentas):
    fecha, fin_v, dias = ventana_de_nombre(path)
    registros = (registros_json(path) if path.lower().endswith(".json")
                 else registros_xlsx(path))
    filas = []
    for r in registros:
        cuenta_id = s_id(r.get("accountTitle"))
        # accountTitle viene como float grande -> reconstruir el id entero
        if cuenta_id and "." in cuenta_id:
            cuenta_id = str(int(float(cuenta_id)))
        info_cuenta = cuentas.get(cuenta_id, {})
        alias = info_cuenta.get("alias", cuenta_id)
        moneda = info_cuenta.get("moneda", "USD")
        spend = s_num(r.get("spend"))
        if moneda != "USD":
            tasa = TASAS_A_USD.get(moneda)
            if tasa is None:
                raise SystemExit(
                    f"Cuenta {cuenta_id} ({alias}) factura en {moneda} y no hay tasa "
                    f"declarada en TASAS_A_USD (ingerir_lucidsales.py). Agregala antes "
                    f"de ingerir: costear en USD sin tasa es inventar el numero.")
            spend = spend / tasa
        filas.append({
            "ventana_ini": fecha, "ventana_fin": fin_v, "dias": dias, "rol_ventana": rol,
            "producto_key": producto_key(r.get("producto"), productos),
            "producto": s_txt(r.get("producto")),
            "cuenta_id": cuenta_id, "cuenta_alias": alias,
            "campana": s_txt(r.get("campaignTitle")),
            "conjunto": s_txt(r.get("adSetTitle")),
            "anuncio": s_txt(r.get("adTitle")),
            "mensajes": int(s_num(r.get("messages"))),
            "clicks": int(s_num(r.get("clicks"))),
            "impresiones": int(s_num(r.get("impressions"))),
            "spend_usd": round(spend, 4),
            "ventas": int(s_num(r.get("sells"))),
            "total_q": round(s_num(r.get("total")), 2),
            "moneda_origen": moneda, "fuente": fuente,
            "ad_id": s_id(r.get("adId")),
        })
    return filas


def llaves(f):
    """Identidades anti-duplicado de una fila.

    Por `ad_id` cuando lo hay; por nombre siempre.

    POR QUÉ CAMBIÓ (07-sep-2026). La llave era por NOMBRE (conjunto + anuncio), y el
    nombre no es estable: el 06-sep se renombraron conjuntos Y ANUNCIOS a la convención
    de ETAPA-6. Al re-bajar el 01-sep, 24 de 46 filas no encontraron su par —el CSV
    decía "video Clearstem3", el export "ANTI-FALSIFICACION_VID_A ~ …"— y se habrían
    anexado duplicadas: DOBLE CONTEO DE VENTAS en el P&L, en silencio.

    El `ad_id` SÍ sobrevive al renombre: medido, los 45 del 01-sep en el CSV coinciden
    con los 45 de la API. `_ALIAS_CONJUNTOS.csv` cubre conjuntos renombrados, pero no
    existe un alias de ANUNCIOS — y con ad_id no hace falta.

    Beneficio extra: la llave por nombre COLAPSABA filas legítimas distintas, porque
    "LucidSales emite una fila por adId y un mismo anuncio corre con varios"
    (DATA_PLAYBOOK). Esas filas se perdían como falsos duplicados.

    Las ventas orgánicas comparten el literal `adId='organico'`, así que esas caen al
    camino por nombre + producto_key: si dos productos venden orgánico el mismo día,
    son dos filas distintas y deben seguir siéndolo.

    DOS identidades, no una: la fila es duplicada si coincide por CUALQUIERA. Hace falta
    porque ninguna sirve sola —
      · por ad_id: 182 de las 200 filas de julio quedaron con el ad_id en notación
        científica ("1.202566048665706e+17"), con la precisión ya perdida. Esos no
        matchean nunca, y re-ingerir un histórico duplicaría todo.
      · por nombre: no sobrevive a los renombrados del 06-sep.
    Coincidir por cualquiera de las dos NUNCA duplica; a lo sumo descarta una fila
    legítima que comparte nombre, que es el comportamiento que el sistema ya tenía.
    Para un P&L, inflar ventas es peor que perder una fila conocida.
    """
    aid = str(f.get("ad_id") or "").strip()
    sano = aid and aid.lower() != "organico" and "e+" not in aid.lower()
    ks = []
    if sano:
        ks.append(("AD", f["ventana_ini"], f["fuente"], f["rol_ventana"], aid))
    ks.append(("NOM", f["ventana_ini"], f["producto_key"], alias.canonico(f["conjunto"]),
               f["anuncio"], f["fuente"], f["rol_ventana"],
               aid.lower() if aid.lower() == "organico" else ""))
    return ks


def clave_natural(f):
    """UNA identidad por fila para el UPSERT (T1, 22-sep-2026), no las dos de `llaves()`.

    `llaves()` sirve para DEDUPE ("¿ya existe con cualquiera de estas dos identidades?"),
    que es lo que necesitaba un append-only. Un UPSERT necesita reemplazar por UNA llave
    natural: se usa la identidad "AD" (ad_id sano) cuando existe — es la que sobrevive a
    un renombrado — y si no la identidad "NOM" (nombre + producto), exactamente en el
    mismo orden de preferencia que `llaves()` ya documentaba.

    `rol_ventana` viaja en la llave: una fila CONTROL nunca cae en la misma llave que una
    BASE del mismo día, así que el UPSERT nunca puede reemplazar una por la otra — la
    invariante de DATA_PLAYBOOK ("CONTROL solapa a propósito, nunca suma") queda intacta.
    """
    ks = llaves(f)
    return ks[0]


def main():
    args = sys.argv[1:]
    rol, fuente, dry = "BASE", "LucidSales", False
    archivos, de_carpeta = [], set()
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--rol":
            i += 1; rol = args[i]
        elif a == "--fuente":
            i += 1; fuente = args[i]
        elif a == "--dry-run":
            dry = True
        elif a == "--dir":
            i += 1
            d = args[i]
            barridos = sorted(
                os.path.join(d, f) for f in os.listdir(d)
                if f.startswith("report-") and f.endswith((".xlsx", ".json"))
                and not re.search(r"-[0-9a-f]{8}\.xlsx$", f)   # ignora copias con hash
            )
            archivos += barridos
            de_carpeta.update(barridos)
        else:
            archivos.append(a)
        i += 1

    # Un export de RANGO (dias>1) es el control semanal: va SIEMPRE con --rol CONTROL
    # (DATA_PLAYBOOK). La carga BASE que barre la carpeta con --dir lo salta con un aviso en vez
    # de abortar la corrida entera; un archivo nombrado a mano sigue pasando por el guardarraíl.
    if rol == "BASE":
        rangos = [p for p in archivos if p in de_carpeta and ventana_de_nombre(p)[2] > 1]
        for p in rangos:
            print(f"↷ {os.path.basename(p)} cubre varios días: es el control semanal "
                  "(se carga con --rol CONTROL), no entra en la carga BASE.")
        archivos = [p for p in archivos if p not in rangos]

    if not archivos:
        raise SystemExit("Sin archivos. Uso: ingerir_lucidsales.py <xlsx...> | --dir <carpeta>")

    productos = cargar_productos()
    cuentas = cargar_cuentas()

    existentes = []
    if os.path.exists(FACT):
        with open(FACT, newline="", encoding="utf-8") as fh:
            existentes = list(csv.DictReader(fh))

    # Ya NO se compara contra `existentes` acá (22-sep-2026, T1): una fila que coincide con
    # una llave YA EN DISCO no es un duplicado a descartar, es una CORRECCIÓN a aplicar — el
    # UPSERT de mas abajo la reemplaza. Solo se colapsa una colisión DENTRO DE LA MISMA
    # corrida (dos archivos de esta invocación con la misma llave; la última fila gana,
    # igual que el `ya.update()` de antes hacía entre archivos).
    vistas_run, nuevas, dup, resumen = {}, [], 0, {}
    for path in archivos:
        filas = leer_export(path, rol, fuente, productos, cuentas)
        n_ok = 0
        for f in filas:
            k = clave_natural(f)
            if k in vistas_run:
                dup += 1
                nuevas[vistas_run[k]] = f
                continue
            vistas_run[k] = len(nuevas)
            nuevas.append(f)
            n_ok += 1
        d = fecha_de_nombre(path)
        resumen[d] = {
            "filas": n_ok,
            "ventas": sum(x["ventas"] for x in filas),
            "total_q": round(sum(x["total_q"] for x in filas), 2),
            "spend_usd": round(sum(x["spend_usd"] for x in filas), 2),
            "mensajes": sum(x["mensajes"] for x in filas),
        }

    # verificación de JOIN contra _DIM_CONJUNTOS, resolviendo RENOMBRADOS.
    # Sin canonico() en LOS DOS lados, un conjunto renombrado en Meta se reporta como
    # "sin dimensión" aunque su dimensión exista bajo el nombre viejo: falso positivo
    # todas las noches, y un aviso que siempre miente entrena a ignorar los avisos.
    # El mapeo es de alias.py — ningún consumidor escribe el suyo (regla de CLAUDE.md).
    dim = pd.read_csv(DIMC)
    conocidos = {alias.canonico(c) for c in dim["conjunto_meta"].astype(str).str.strip()}
    sin_dim = sorted({f["conjunto"] for f in nuevas
                      if f["conjunto"] and alias.canonico(f["conjunto"]) not in conocidos})

    # GATE DE INTEGRIDAD. Hasta el 22-sep-2026 este chequeo solo imprimía "sin dimensión"
    # o "cierra al 100%" sin mirar SIN_CLASIFICAR: la corrida de Turmeric mostró el
    # verde falso mientras 120 filas / 35 ventas / $165.69 quedaban invisibles para
    # cualquier join por producto_key. Ahora ambos huecos BLOQUEAN la corrida (más abajo).
    sin_clasificar = [f for f in nuevas if f["producto_key"] == "SIN_CLASIFICAR"]

    print(f"archivos: {len(archivos)} · filas nuevas: {len(nuevas)} · "
          f"duplicados dentro de la misma corrida: {dup}")
    if ids_perdidos():
        print(f"⚠ {ids_perdidos()} id(s) irrecuperable(s) (float > 2**53 o notación científica de "
              f"origen): quedaron en \"\" en vez de un ad_id/cuenta_id falso (ver s_id()).")
    for d in sorted(resumen):
        r = resumen[d]
        print(f"  {d}: {r['filas']:>3} filas · {r['ventas']:>3} ventas · "
              f"Q{r['total_q']:>9,.2f} · ${r['spend_usd']:>7,.2f} · {r['mensajes']:>4} msj")
    if sin_dim:
        print(f"\n⚠ {len(sin_dim)} conjuntos SIN dimensión (dar de alta en _DIM_CONJUNTOS.csv):")
        for c in sin_dim:
            print("   -", c)
    if sin_clasificar:
        acumulado = {}
        for f in sin_clasificar:
            r = acumulado.setdefault(f["producto"] or "(sin nombre)",
                                      {"filas": 0, "ventas": 0, "spend_usd": 0.0})
            r["filas"] += 1
            r["ventas"] += f["ventas"]
            r["spend_usd"] += f["spend_usd"]
        print(f"\n⚠ {len(sin_clasificar)} fila(s) SIN_CLASIFICAR "
              f"(producto no reconocido en _DIM_PRODUCTOS.csv):")
        for nombre, r in sorted(acumulado.items()):
            print(f"   - \"{nombre}\": {r['filas']} fila(s) · {r['ventas']} venta(s) · "
                  f"${r['spend_usd']:,.2f} spend — dar de alta la fila en _DIM_PRODUCTOS.csv")
    if not sin_dim and not sin_clasificar:
        print("\n✅ JOIN con _DIM_CONJUNTOS y _DIM_PRODUCTOS cierra al 100%")

    # GUARDARRAÍL DE SOLAPE. Cargar un export de RANGO (dias>1) con el mismo rol que los
    # diarios ya cargados suma la misma venta dos veces: la fila del tramo y la del día.
    # Por eso el control semanal de los lunes va con --rol CONTROL (DATA_PLAYBOOK).
    solapes = []
    for path in archivos:
        ini, fin, dias = ventana_de_nombre(path)
        if dias <= 1:
            continue
        chocan = {e["ventana_ini"] for e in existentes
                  if e["rol_ventana"] == rol and e["fuente"] == fuente
                  and e["dias"] == "1" and ini <= e["ventana_ini"] <= fin}
        if chocan:
            solapes.append((os.path.basename(path), dias, len(chocan), min(chocan), max(chocan)))
    if solapes:
        print()
        for nom, dias, n, d0, d1 in solapes:
            print(f"⛔ {nom} cubre {dias} días y ya hay {n} días sueltos cargados como "
                  f"rol={rol} en ese rango ({d0}..{d1}).")
        print("   Cargarlo así SUMA las mismas ventas dos veces. Si es el control "
              "semanal, va con --rol CONTROL.")
        if not dry:
            raise SystemExit("   Abortado para no duplicar. Revisa el rol o el archivo.")

    if dry:
        print("\n[dry-run] no se escribió nada")
        return

    if nuevas:
        # UPSERT (22-sep-2026, T1) en vez de anexar a ciegas: una llave que ya estaba en
        # _FACT_VENTAS.csv se REEMPLAZA (corrige un día que llegó con el gasto/ventas
        # congelado a medio día — ver evidencia en el docstring del módulo), no se descarta.
        # `clave_natural()` incluye rol_ventana: CONTROL nunca reemplaza a BASE ni viceversa.
        #
        # P3 T3: la escritura pasa por Postgres (db/escribir.py), nunca directo al CSV. El
        # guardia de drift corre PRIMERO: si el CSV en disco no coincide con lo que la base
        # exportaría (o nunca se hizo el bootstrap), aborta sin escribir nada.
        # El directorio de escritura sale de FACT (nunca de la constante PROD): las pruebas
        # monkeypatchean FACT a un directorio temporal (ver `_correr_main` en
        # test_ingerir_lucidsales.py), y escribir sobre PROD igual pisaria PRODUCTOS/ real --
        # exactamente el defecto encontrado en vivo durante T3 (datos ficticios de una prueba
        # mezclados con PRODUCTOS/_FACT_VENTAS.csv real).
        prod_dir = os.path.dirname(FACT)
        try:
            con = db_cargar.conectar()
        except Exception as exc:
            raise SystemExit(
                f"\n⛔ Postgres no disponible: no se pudo escribir _FACT_VENTAS.csv (nunca se "
                f"escribe el CSV directo). Detalle: {exc}")
        try:
            db_escribir.verificar_csv_sincronizado(con, "venta", prod_dir, tenant_id=TENANT_ID)
            reemplazadas, nuevas_disco, sin_cambio = db_escribir.upsert(
                con, "venta", nuevas, key=clave_natural, prod_dir=prod_dir, bkdir=BKDIR,
                tenant_id=TENANT_ID)
        except db_escribir.ErrorEscritura as exc:
            raise SystemExit(f"\n⛔ {exc}")
        finally:
            con.close()
        print(f"\n✅ {reemplazadas} reemplazadas (día corregido) · {nuevas_disco} nuevas · "
              f"{sin_cambio} sin cambio -> _FACT_VENTAS.csv (Postgres es la verdad; espejo "
              f"regenerado en PRODUCTOS/, backup previo en _RESPALDOS/backups_csv/)")

    if sin_clasificar or sin_dim:
        # Se escribe SIEMPRE (perder una venta real es peor que un aviso), pero la
        # corrida sale en rojo: la ingesta nocturna no puede reportarse sana con
        # data invisible para el join por producto o por conjunto.
        raise SystemExit(
            "\n⛔ Ingesta completada pero con huecos de integridad (ver arriba). "
            "No reportar esta noche como limpia hasta resolverlos.")


if __name__ == "__main__":
    main()
