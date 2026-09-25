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
    )


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
    el reporte de `cargar_todo()` no mienta. Default `True`: comportamiento idéntico a siempre."""
    import nucleo as N  # import tardío: nucleo importa `cargar.enriquecer_venta`, evita el ciclo

    productos_dir = productos_dir or T.PRODUCTOS_DIR
    decisiones_json = decisiones_json or os.path.join(productos_dir, "_DECISIONES.json")

    conteos_raw = {}
    con = conectar(env)
    try:
        with con:
            with con.cursor() as cur:
                for tabla, archivo, opcional in T.TABLE_SPECS:
                    if not incluir_verdad_db and tabla in T.TABLAS_VERDAD_DB:
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


def main():
    ap = argparse.ArgumentParser(description="Carga PRODUCTOS/*.csv a Postgres (raw -> core)")
    ap.add_argument("--productos-dir", default=None, help="default: PRODUCTOS/ del repo")
    ap.add_argument("--decisiones-json", default=None, help="default: <productos-dir>/_DECISIONES.json")
    ap.add_argument("--tenant", default="vitalcom")
    args = ap.parse_args()

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
