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
import json
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
    extra = T.EXTRA_COLUMNS.get(tabla, [])
    cols_final = header_sql + extra

    cur.execute("TRUNCATE TABLE core.%s" % tabla)
    if not filas:
        return 0, (sha256_de(path) if os.path.exists(path) else None)

    filas_mapa = None
    if tabla == "venta":
        ruta_mapa = os.path.join(productos_dir, "_MAPA_AD_ID_HIST.csv")
        filas_mapa = leer_filas(ruta_mapa) if os.path.exists(ruta_mapa) else []
        enriquecidas = enriquecer_venta(filas, filas_mapa)

    col_list = ", ".join(['"%s"' % c for c in (["tenant_id"] + cols_final)])
    placeholders = ", ".join(["%s"] * (1 + len(cols_final)))
    sql = "INSERT INTO core.%s (%s) VALUES (%s)" % (tabla, col_list, placeholders)

    rows_out = []
    for i, fila in enumerate(filas):
        valores = [fila.get(c, "") for c in header]
        if tabla == "venta":
            resuelto, metodo = enriquecidas[i]
            valores = valores + [resuelto, metodo]
        rows_out.append(tuple([tenant_id] + valores))

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


def cargar_decision(cur, tenant_id, decisiones_json):
    cur.execute("TRUNCATE TABLE core.decision")
    if not os.path.exists(decisiones_json):
        return False
    with io.open(decisiones_json, encoding="utf-8") as f:
        payload = json.load(f)
    fecha = payload.get("generado")
    cur.execute(
        "INSERT INTO core.decision (tenant_id, fecha, payload) VALUES (%s, %s, %s)",
        (tenant_id, fecha, json.dumps(payload, ensure_ascii=False)),
    )
    return True


def cargar_todo(productos_dir=None, decisiones_json=None, tenant_id="vitalcom", env=None):
    """Punto de entrada reutilizable (tests, gate de paridad). Devuelve {tabla: n_filas}."""
    productos_dir = productos_dir or T.PRODUCTOS_DIR
    decisiones_json = decisiones_json or os.path.join(productos_dir, "_DECISIONES.json")

    conteos = {}
    con = conectar(env)
    try:
        with con:
            with con.cursor() as cur:
                for tabla, archivo, opcional in T.TABLE_SPECS:
                    n, sha = cargar_tabla(cur, tenant_id, tabla, archivo, opcional, productos_dir)
                    conteos[tabla] = n
                    path = os.path.join(productos_dir, archivo)
                    cur.execute(
                        "INSERT INTO core.raw_import (tenant_id, archivo, sha256, filas) "
                        "VALUES (%s, %s, %s, %s)",
                        (tenant_id, archivo, sha, n),
                    )
                tiene_decision = cargar_decision(cur, tenant_id, decisiones_json)
                conteos["decision"] = 1 if tiene_decision else 0
    finally:
        con.close()
    return conteos


def main():
    ap = argparse.ArgumentParser(description="Carga PRODUCTOS/*.csv a Postgres (schema core)")
    ap.add_argument("--productos-dir", default=None, help="default: PRODUCTOS/ del repo")
    ap.add_argument("--decisiones-json", default=None, help="default: <productos-dir>/_DECISIONES.json")
    ap.add_argument("--tenant", default="vitalcom")
    args = ap.parse_args()

    conteos = cargar_todo(args.productos_dir, args.decisiones_json, args.tenant)
    total = sum(conteos.values())
    for tabla, n in sorted(conteos.items()):
        print("%-32s %6d" % (tabla, n))
    print("-" * 40)
    print("%-32s %6d" % ("TOTAL", total))
    return 0


if __name__ == "__main__":
    sys.exit(main())
