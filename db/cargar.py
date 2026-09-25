#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""cargar.py — CSV -> Postgres, idempotente (P1-cimientos T5).

Carga cada CSV de PRODUCTOS/ en su tabla espejo de `core` (ver db/tables.py: mismas columnas,
mismo orden, texto verbatim + tenant_id). Estrategia de idempotencia: TRUNCATE + reinsertar,
TODO en UNA transacción por corrida — si algo falla a mitad, no queda ni una tabla a medio
cargar y las tablas conservan su contenido anterior (ROLLBACK). Una segunda corrida sobre los
mismos CSV deja exactamente el mismo conteo de filas y el mismo contenido: por diseño, nunca por
casualidad.

Nunca toca PRODUCTOS/*.csv (son la fuente de verdad durante P1) ni _DECISIONES.json salvo para
LEERLO. Nunca imprime ni loguea PGPASSWORD.

USO:
    "<venv>/python.exe" db/cargar.py                # carga PRODUCTOS/ real
    "<venv>/python.exe" db/cargar.py --productos-dir X --decisiones-json Y   # para tests/gate
"""
import argparse
import csv
import hashlib
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tables as T  # noqa: E402

# venta_identidad.py es un módulo SIN dependencias externas (a proposito: mapear_ad_id_hist.py
# arrastra pandas via bajar_meta_insights/ingerir_meta, ausente en el venv de psycopg que corre
# este archivo). Ver su docstring.
sys.path.insert(0, os.path.join(T.BASE_DIR, "Ads", "_TOOLS"))
from venta_identidad import asignar_venta_uids  # noqa: E402


def cargar_env(path=None):
    """Lee ~/.config/vitalcom_db/.env (KEY=VALUE, puede traer CRLF) sin nunca imprimirlo."""
    path = path or os.path.join(os.path.expanduser("~"), ".config", "vitalcom_db", ".env")
    env = dict(os.environ)
    if os.path.exists(path):
        with io.open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip().strip("\r")
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                env.setdefault(k.strip(), v.strip())
    return env


def conectar(env=None):
    import psycopg

    env = env or cargar_env()
    return psycopg.connect(
        host=env.get("PGHOST", "localhost"),
        port=env.get("PGPORT", "5432"),
        dbname=env.get("PGDATABASE", "vitalcom"),
        user=env.get("PGUSER", "vitalcom"),
        password=env.get("PGPASSWORD", ""),
        # P3 T3: sin esto, un Postgres inalcanzable (puerto filtrado/caído, no solo "conexión
        # rechazada") puede colgar sin límite en vez de fallar rápido -- descubierto probando el
        # camino "Postgres caído" de los llamadores reales, que deben salir con un mensaje claro,
        # no quedarse esperando para siempre (bloquearía la cadena nocturna completa).
        connect_timeout=10,
    )


def asegurar_base_de_datos(nombre, env=None):
    """Crea la base `nombre` si no existe (P3 T3: aislamiento de pruebas en `vitalcom_test`, nunca
    la base real `vitalcom` — ver db/README.md). Se conecta con las MISMAS credenciales a una base
    de mantenimiento FIJA (`postgres`, o si esa falla, `vitalcom` — NUNCA `env["PGDATABASE"]`: en
    contexto de pruebas esa variable ya apunta a `nombre`, que todavía no existe) porque no se
    puede crear una base estando conectado a ella misma. Devuelve True si la base ya existía o se
    acaba de crear; False si Postgres no fue alcanzable, o si el rol conectado no tiene permiso
    CREATEDB (caso real: un rol de aplicación sin privilegios de superusuario) — en ambos casos el
    llamador debe tratarlo como "no se pudo, salta lo que dependa de esto", nunca como un error
    fatal ni una razón para caer de vuelta a la base real."""
    import psycopg

    env = env or cargar_env()
    for mantenimiento in ("postgres", "vitalcom"):
        try:
            con = psycopg.connect(
                host=env.get("PGHOST", "localhost"), port=env.get("PGPORT", "5432"),
                dbname=mantenimiento, user=env.get("PGUSER", "vitalcom"),
                password=env.get("PGPASSWORD", ""), autocommit=True, connect_timeout=10,
            )
        except Exception:
            continue
        try:
            with con.cursor() as cur:
                cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (nombre,))
                if cur.fetchone():
                    return True
                cur.execute('CREATE DATABASE "%s"' % nombre)
            return True
        except Exception:
            continue
        finally:
            con.close()
    return False


def aplicar_schema(env=None, dbname=None):
    """Aplica db/schema.sql sobre la base indicada (P3 T3: puebla `vitalcom_test` recién creada —
    `CREATE DATABASE` no copia el esquema de ninguna otra base). Idempotente, igual que el propio
    schema.sql (`CREATE ... IF NOT EXISTS`)."""
    env = dict(env or cargar_env())
    if dbname:
        env["PGDATABASE"] = dbname
    schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schema.sql")
    with io.open(schema_path, encoding="utf-8") as f:
        sql = f.read()
    con = conectar(env)
    try:
        with con.cursor() as cur:
            cur.execute(sql)
        con.commit()
    finally:
        con.close()


def sha256_de(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def leer_filas(path):
    with io.open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def ad_id_valido(v):
    """Mismo criterio que Ads/_TOOLS/mapear_ad_id_hist.py:ad_id_valido — solo dígitos, largo>=10."""
    v = (v or "").strip()
    return v.isdigit() and len(v) >= 10


def enriquecer_venta(filas_venta, filas_mapa):
    """Calcula (ad_id_resuelto, metodo_atribucion) por fila de _FACT_VENTAS.csv.

    NUNCA pisa el ad_id original (se reconstruye verbatim aparte): esto solo agrega dos valores
    derivados. Regla (T2/T5, ver odd/tasks/p1-cimientos.md):
      - ad_id original válido               -> metodo='ad_id',                 resuelto=original
      - rol_ventana==BASE, ad_id inválido,
        resuelto por el mapa (verificado)   -> metodo='ad_id_verificado_gasto', resuelto=map.ad_id
      - rol_ventana==BASE, ad_id inválido,
        resuelto por el mapa (solo nombre)  -> metodo='nombre',                 resuelto=None
      - cualquier otro caso (no está en el
        mapa, o no es BASE)                 -> metodo='sin_atribuir',           resuelto=None

    JOIN por `venta_uid` (P1-cimientos T2b, reapertura 23-sep-2026), NO por posición. La llave
    natural del mapa (ventana_ini, cuenta_alias, conjunto, anuncio) se repite en 150 grupos de
    _MAPA_AD_ID_HIST.csv, así que un join posicional (key + cola FIFO) dependía de que el ORDEN de
    _FACT_VENTAS.csv nunca cambiara entre la corrida que generó el mapa y esta. `venta_uid` es un
    hash del contenido COMPLETO de cada fila de venta (ver Ads/_TOOLS/venta_identidad.py):
    sobrevive a un reordenamiento porque no depende de la posición. Se recalcula acá sobre
    `filas_venta` en el orden en que llega la lista — el resultado no cambia si esa lista viene en
    otro orden (test: test_enriquecer_venta_estable_ante_reordenamiento)."""
    mapa_por_uid = {}
    for m in filas_mapa:
        uid = (m.get("venta_uid") or "").strip()
        if uid:
            mapa_por_uid[uid] = m

    uids = asignar_venta_uids(filas_venta)
    resultados = []
    for fila, uid in zip(filas_venta, uids):
        ad_id_orig = (fila.get("ad_id") or "").strip()
        if ad_id_valido(ad_id_orig):
            resultados.append((ad_id_orig, "ad_id"))
            continue
        if (fila.get("rol_ventana") or "").strip() == "BASE":
            m = mapa_por_uid.get(uid)
            if m:
                metodo = (m.get("metodo") or "").strip()
                resuelto = (m.get("ad_id") or "").strip() or None
                if metodo == "ad_id_verificado_gasto":
                    resultados.append((resuelto, "ad_id_verificado_gasto"))
                elif metodo == "nombre":
                    resultados.append((None, "nombre"))
                else:
                    resultados.append((None, "sin_atribuir"))
                continue
        resultados.append((None, "sin_atribuir"))
    return resultados


def cargar_tabla(cur, tenant_id, tabla, archivo, opcional, productos_dir):
    """Carga un CSV verbatim en su tabla espejo de `raw` (T5b: raw ya no tiene columnas extra ni
    casos especiales — el enriquecimiento de venta vive en `core`, ver db/nucleo.py)."""
    path = os.path.join(productos_dir, archivo)
    if not os.path.exists(path):
        if not opcional:
            raise FileNotFoundError("CSV requerido no encontrado: %s" % path)
        pares = []
        filas = []
    else:
        pares = T.columnas_csv_y_sql(tabla, archivo, opcional) if productos_dir == T.PRODUCTOS_DIR \
            else _pares_de(path, tabla)
        filas = leer_filas(path)

    header = [csv_col for csv_col, _ in pares]
    header_sql = [sql_col for _, sql_col in pares]

    cur.execute("TRUNCATE TABLE raw.%s" % tabla)
    if not filas:
        return 0, (sha256_de(path) if os.path.exists(path) else None)

    col_list = ", ".join(['"%s"' % c for c in (["tenant_id"] + header_sql)])
    placeholders = ", ".join(["%s"] * (1 + len(header_sql)))
    sql = "INSERT INTO raw.%s (%s) VALUES (%s)" % (tabla, col_list, placeholders)

    rows_out = [tuple([tenant_id] + [fila.get(c, "") for c in header]) for fila in filas]
    cur.executemany(sql, rows_out)
    return len(filas), sha256_de(path)


def _leer_header_de(path):
    with io.open(path, encoding="utf-8-sig", newline="") as f:
        r = csv.reader(f)
        try:
            return next(r)
        except StopIteration:
            return []


def _pares_de(path, tabla):
    """Igual que T.columnas_csv_y_sql pero leyendo el header de un CSV fuera de PRODUCTOS/ (lo
    usa el gate de paridad, que carga desde una base exportada a un directorio temporal)."""
    renombres = T.COLUMN_RENAMES.get(tabla, {})
    pares = []
    for c in _leer_header_de(path):
        sql = T.nombre_columna_sql(c)
        pares.append((sql, renombres.get(sql, sql)))
    return pares


def cargar_decisiones_json(cur, tenant_id, decisiones_json, incluir_verdad_db=True):
    """Carga el TEXTO VERBATIM de `_DECISIONES.json` en `raw.decisiones_json` (P3 T2). No pasa
    por `cargar_tabla`/`TABLE_SPECS`: ese archivo no tiene columnas propias, es un blob de una
    sola fila por corrida (TRUNCATE + insert, igual patrón que el resto de `raw`).

    `incluir_verdad_db=False` (T2, `cargar_todo`) NO TOCA la tabla: es la tabla DB-truth de
    `_DECISIONES.json`, y una recarga completa la pisaría con el contenido del archivo local,
    perdiendo lo que `db/escribir.reemplazar_decision()` ya haya escrito ahí."""
    if not incluir_verdad_db:
        return
    cur.execute("DELETE FROM raw.decisiones_json WHERE tenant_id = %s", (tenant_id,))
    if decisiones_json and os.path.exists(decisiones_json):
        with io.open(decisiones_json, encoding="utf-8") as f:
            contenido = f.read()
        cur.execute(
            "INSERT INTO raw.decisiones_json (tenant_id, contenido) VALUES (%s, %s)",
            (tenant_id, contenido),
        )


def cargar_todo(productos_dir=None, decisiones_json=None, tenant_id="vitalcom", env=None,
                 incluir_verdad_db=True):
    """Punto de entrada reutilizable (tests, gate de paridad). Carga `raw.*` desde los CSV y, EN
    LA MISMA TRANSACCIÓN, construye `core.*` desde `raw.*` (T5b, db/nucleo.py). Devuelve
    {"raw": {tabla: n_filas}, "core": reporte_de_reconciliacion}.

    `incluir_verdad_db=False` (P3 T2): NO recarga las tablas `raw.*` de `tables.TABLAS_VERDAD_DB`
    (ni `raw.decisiones_json`) desde el CSV/archivo local — quedan intactas, con lo que haya
    escrito `db/escribir.py`. Sigue reportando su conteo actual (consulta, no TRUNCATE) para que
    el reporte de `cargar_todo()` no mienta. Default `True`: mismo comportamiento de siempre PARA
    LAS TABLAS QUE TODAVÍA NO SE CONECTARON a un llamador real (T4 en adelante).

    P3 T3: las tablas de `tables.TABLAS_MIGRADAS_DB` (ya conectadas — `venta`,
    `entrega_conjunto_dia`, `entrega_anuncio_dia`) se saltan de la recarga desde CSV SIEMPRE,
    pase lo que pase con `incluir_verdad_db` — no es opcional, porque una recarga genérica
    (`db/cargar.py` sin flags, el uso más común) jamás debe poder pisar la verdad que ya escribió
    un llamador real. La ÚNICA forma deliberada de recargarlas desde su CSV es `tomar_csv()`
    (bootstrap inicial o recuperación de drift), nunca este camino genérico."""
    import nucleo as N  # import tardío: nucleo importa `cargar.enriquecer_venta`, evita el ciclo

    productos_dir = productos_dir or T.PRODUCTOS_DIR
    decisiones_json = decisiones_json or os.path.join(productos_dir, "_DECISIONES.json")

    conteos_raw = {}
    con = conectar(env)
    try:
        with con:
            with con.cursor() as cur:
                for tabla, archivo, opcional in T.TABLE_SPECS:
                    if tabla in T.TABLAS_MIGRADAS_DB or (
                            not incluir_verdad_db and tabla in T.TABLAS_VERDAD_DB):
                        cur.execute(
                            "SELECT count(*) FROM raw.%s WHERE tenant_id = %%s" % tabla,
                            (tenant_id,),
                        )
                        conteos_raw[tabla] = cur.fetchone()[0]
                        continue
                    n, sha = cargar_tabla(cur, tenant_id, tabla, archivo, opcional, productos_dir)
                    conteos_raw[tabla] = n
                    path = os.path.join(productos_dir, archivo)
                    cur.execute(
                        "INSERT INTO raw.raw_import (tenant_id, archivo, sha256, filas) "
                        "VALUES (%s, %s, %s, %s)",
                        (tenant_id, archivo, sha, n),
                    )
                cargar_decisiones_json(cur, tenant_id, decisiones_json, incluir_verdad_db)
                reporte_core = N.construir_core(cur, tenant_id)
    finally:
        con.close()
    return {"raw": conteos_raw, "core": reporte_core}


def _resolver_tabla_migrada(tabla_o_archivo):
    """Acepta el nombre de TABLA (`venta`) o de ARCHIVO (`_FACT_VENTAS.csv`) y devuelve
    (tabla, archivo, opcional) — solo entre las de `tables.TABLAS_MIGRADAS_DB` (T3): --tomar-csv
    es la recuperación deliberada de una tabla YA migrada, nunca una forma general de recargar
    cualquier CSV (para eso ya está `cargar_todo()`)."""
    for tabla, archivo, opcional in T.TABLE_SPECS:
        if tabla not in T.TABLAS_MIGRADAS_DB:
            continue
        if tabla_o_archivo == tabla or tabla_o_archivo == archivo:
            return tabla, archivo, opcional
    raise ValueError(
        "%r no es una tabla DB-truth MIGRADA (ver tables.TABLAS_MIGRADAS_DB: %s). --tomar-csv "
        "solo aplica a las que P3 ya movio a Postgres." % (tabla_o_archivo,
                                                            sorted(T.TABLAS_MIGRADAS_DB)))


def tomar_csv(tabla_o_archivo, productos_dir=None, tenant_id="vitalcom", env=None):
    """P3 T3/T4 — recuperación DELIBERADA, nunca automática: recarga UNA sola tabla DB-truth ya
    migrada desde su CSV/archivo en disco (bootstrap inicial, cuando `raw.<tabla>` está vacía, o
    recuperación cuando el guardia de drift correspondiente lo detecta). Reconstruye `core`
    ENTERO en la MISMA transacción, igual que el resto de este módulo. Devuelve
    (archivo, n_filas, reporte_core).

    `_DECISIONES.json` (P3 T4) es un caso especial: no tiene fila en `tables.TABLE_SPECS` (no es
    un espejo columna por columna, ver `tables.py`), así que no pasa por `_resolver_tabla_migrada`/
    `cargar_tabla` — se carga con `cargar_decisiones_json()`, el mismo camino que usa
    `cargar_todo()`, y su drift se vigila con `escribir.verificar_decision_sincronizada()`."""
    import nucleo as N  # import tardío, mismo motivo que en cargar_todo()

    productos_dir = productos_dir or T.PRODUCTOS_DIR

    if tabla_o_archivo in ("decisiones_json", "_DECISIONES.json"):
        decisiones_json = os.path.join(productos_dir, "_DECISIONES.json")
        con = conectar(env)
        try:
            with con:
                with con.cursor() as cur:
                    cargar_decisiones_json(cur, tenant_id, decisiones_json, incluir_verdad_db=True)
                    n = 1 if os.path.exists(decisiones_json) else 0
                    cur.execute(
                        "INSERT INTO raw.raw_import (tenant_id, archivo, sha256, filas) "
                        "VALUES (%s, %s, %s, %s)",
                        (tenant_id, "_DECISIONES.json", None, n),
                    )
                    reporte_core = N.construir_core(cur, tenant_id)
        finally:
            con.close()
        return "_DECISIONES.json", n, reporte_core

    tabla, archivo, opcional = _resolver_tabla_migrada(tabla_o_archivo)

    con = conectar(env)
    try:
        with con:
            with con.cursor() as cur:
                n, sha = cargar_tabla(cur, tenant_id, tabla, archivo, opcional, productos_dir)
                path = os.path.join(productos_dir, archivo)
                cur.execute(
                    "INSERT INTO raw.raw_import (tenant_id, archivo, sha256, filas) "
                    "VALUES (%s, %s, %s, %s)",
                    (tenant_id, archivo, sha, n),
                )
                reporte_core = N.construir_core(cur, tenant_id)
    finally:
        con.close()
    return archivo, n, reporte_core


def main():
    ap = argparse.ArgumentParser(description="Carga PRODUCTOS/*.csv a Postgres (raw -> core)")
    ap.add_argument("--productos-dir", default=None, help="default: PRODUCTOS/ del repo")
    ap.add_argument("--decisiones-json", default=None, help="default: <productos-dir>/_DECISIONES.json")
    ap.add_argument("--tenant", default="vitalcom")
    ap.add_argument("--tomar-csv", default=None, metavar="ARCHIVO_O_TABLA",
                     help="P3 T3/T4: recarga SOLO esta tabla DB-truth MIGRADA (tables.TABLAS_MIGRADAS_DB, "
                          "o '_DECISIONES.json'/'decisiones_json', caso especial sin fila en TABLE_SPECS) "
                          "desde su CSV/archivo en disco -- bootstrap inicial o recuperacion de drift, "
                          "nunca automatico -- y sale sin tocar el resto")
    args = ap.parse_args()

    if args.tomar_csv:
        archivo, n, reporte = tomar_csv(args.tomar_csv, args.productos_dir, args.tenant)
        print("tomado desde CSV: %s -> %d fila(s) en raw" % (archivo, n))
        print("\n-- core (reconciliacion) --")
        for tabla_core, m in sorted(reporte["tablas"].items()):
            print("%-32s %6d" % (tabla_core, m))
        return 0

    resultado = cargar_todo(args.productos_dir, args.decisiones_json, args.tenant)
    conteos = resultado["raw"]
    total = sum(conteos.values())
    print("-- raw --")
    for tabla, n in sorted(conteos.items()):
        print("%-32s %6d" % (tabla, n))
    print("-" * 40)
    print("%-32s %6d" % ("TOTAL", total))

    reporte = resultado["core"]
    print("\n-- core (reconciliación) --")
    for tabla, n in sorted(reporte["tablas"].items()):
        print("%-32s %6d" % (tabla, n))
    print("\nFK sin resolver:")
    for k, v in sorted(reporte["fk_sin_resolver"].items()):
        print("  %-32s %6d" % (k, v))
    print("\nConservación raw -> core (hechos):")
    for tabla, c in sorted(reporte["conservacion"].items()):
        print("  %-24s raw=%-6d core=%-6d %s"
              % (tabla, c["raw"], c["core"], "OK" if c["igual"] else "DIFERENCIA"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
