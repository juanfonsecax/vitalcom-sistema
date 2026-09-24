# -*- coding: utf-8 -*-
"""tables.py — fuente única de la lista de tablas core.* y su CSV dueño (P1-cimientos T5/T6).

Un dato, un dueño (CLAUDE.md): los CSV en PRODUCTOS/ siguen siendo la fuente de verdad durante
P1. Cada tabla es un espejo FIEL de su CSV — mismas columnas, mismo orden, texto verbatim — más
`tenant_id` (single tenant "vitalcom", RLS no habilitado todavía) y un `id` bigserial. No hay
columnas tipadas/derivadas salvo las listadas en EXTRA_COLUMNS, porque el consumidor real
(decidir.py, vía gasto.py y alias.py) hace su propio `try_cast` al leer el CSV — convertir acá
sería una segunda fuente de verdad para el mismo número.

`cargar.py` y `exportar.py` leen el header real de cada CSV en tiempo de ejecución (nunca lo
hardcodean): si el CSV real cambia de columnas, ambos se adaptan solos. `schema.sql` fue
generado una vez a partir de esos mismos headers (ver el bloque al pie de este archivo,
`si __name__ == "__main__"`) y se re-genera corriendo este archivo si un CSV agrega/quita una
columna — no hay una tercera copia de la lista de columnas.

Columnas EXTRA (no vienen del CSV, las calcula `cargar.py` al cargar):
  - venta.ad_id_resuelto      — ad_id recuperado por Ads/_TOOLS/mapear_ad_id_hist.py cuando el
                                 original no es válido. NUNCA pisa el `ad_id` original: ese queda
                                 verbatim en su propia columna para poder reproducir el CSV byte
                                 a byte (exportar.py reconstruye `_FACT_VENTAS.csv` con el `ad_id`
                                 original, nunca con el resuelto).
  - venta.metodo_atribucion   — 'ad_id' | 'ad_id_verificado_gasto' | 'nombre' | 'sin_atribuir'.

Tablas deliberadamente NO creadas en P1 (evidencia, no elegancia):
  - `angulo` como tabla física: sus columnas ya viven 1:1 en `conjunto` (espejo de
    _DIM_CONJUNTOS.csv, que ya trae angulo_key/avatar/dolor_nucleo/etc. por fila). Separarlas en
    una tabla propia sin que ningún lector real lo necesite todavía (P3 está fuera de alcance)
    sería inventar una segunda fuente para el mismo dato. `schema.sql` deja la VIEW
    `core.angulo` (distinct por producto_key+angulo_key) para cuando un consumidor la necesite.
  - `catalogo_concepto`: su dueño real es `Ads/_SWIPE/_CATALOGO_CONCEPTOS.md` (prosa, no CSV).
    No hay CSV que copiar sin inventar estructura que el .md no declara — se deja fuera de P1 y
    se anota en README.md.
"""

import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRODUCTOS_DIR = os.path.join(BASE_DIR, "PRODUCTOS")

# (tabla, archivo_csv, opcional) — opcional=True si el CSV puede no existir todavía (p.ej.
# _VOZ_CLIENTE.csv: su dueño, verificar_voz.py, todavía no tiene filas en este repo).
TABLE_SPECS = [
    ("producto", "_DIM_PRODUCTOS.csv", False),
    ("costeo", "_DIM_COSTEO.csv", False),
    ("conjunto", "_DIM_CONJUNTOS.csv", False),
    ("creativo", "_DIM_CREATIVOS.csv", False),
    ("voz_cliente", "_VOZ_CLIENTE.csv", True),
    ("dim_bandas", "_DIM_BANDAS.csv", False),
    ("conjunto_nombre_hist", "_ALIAS_CONJUNTOS.csv", False),
    ("dim_bm", "_DIM_BM.csv", False),
    ("dim_cuentas", "_DIM_CUENTAS.csv", False),
    ("dim_envase", "_DIM_ENVASE.csv", False),
    ("dim_flujo_bot", "_DIM_FLUJO_BOT.csv", False),
    ("dim_gastos", "_DIM_GASTOS.csv", False),
    ("dim_mercados", "_DIM_MERCADOS.csv", False),
    ("dim_precios", "_DIM_PRECIOS.csv", False),
    ("dim_tarjetas", "_DIM_TARJETAS.csv", False),
    ("dim_vocabulario", "_DIM_VOCABULARIO.csv", False),
    ("dim_anuncios", "_DIM_ANUNCIOS.csv", False),
    ("estado_angulos", "_ESTADO_ANGULOS.csv", False),
    ("estado_flujo", "_ESTADO_FLUJO.csv", False),
    ("estado_meta", "_ESTADO_META.csv", False),
    ("fact_facturacion", "_FACT_FACTURACION.csv", False),
    ("fact_facturacion_agregado", "_FACT_FACTURACION_AGREGADO.csv", False),
    ("fact_pauta_real", "_FACT_PAUTA_REAL.csv", False),
    ("fact_saldos", "_FACT_SALDOS.csv", False),
    ("fact_semanal", "_FACT_SEMANAL.csv", False),
    ("mapeo_creativos", "_MAPEO_CREATIVOS.csv", False),
    ("parametros_decision", "_PARAMETROS_DECISION.csv", False),
    ("parametros_finanzas", "_PARAMETROS_FINANZAS.csv", False),
    ("parametros_optimizacion", "_PARAMETROS_OPTIMIZACION.csv", False),
    ("parametros_publicacion", "_PARAMETROS_PUBLICACION.csv", False),
    ("tasa_entrega", "_TASA_ENTREGA.csv", False),
    ("testeos", "_TESTEOS.csv", False),
    ("clasificacion_anuncios", "_CLASIFICACION_ANUNCIOS.csv", False),
    ("aprendizajes", "_APRENDIZAJES.csv", False),
    ("mapa_ad_id_hist", "_MAPA_AD_ID_HIST.csv", False),
    ("entrega_conjunto_dia", "_FACT_ENTREGA.csv", False),
    ("entrega_anuncio_dia", "_FACT_ENTREGA_ANUNCIO.csv", False),
    ("venta", "_FACT_VENTAS.csv", False),
    ("evento", "_EVENTOS.csv", False),
]

EXTRA_COLUMNS = {
    "venta": ["ad_id_resuelto", "metodo_atribucion"],
}

# {tabla: {columna_csv: columna_sql}} — solo para el choque de nombre con las columnas propias
# de la tabla (`id`, `tenant_id`, `loaded_at`). _APRENDIZAJES.csv trae su propia columna `id`
# (el id de la fila de aprendizaje, no el bigserial de Postgres); se renombra a `id_csv` en SQL,
# el valor viaja intacto y `exportar.py` lo vuelve a escribir bajo el nombre original `id`.
COLUMN_RENAMES = {
    "aprendizajes": {"id": "id_csv"},
}

# Llave natural del mapa histórico (Ads/_TOOLS/mapear_ad_id_hist.py), documentada en
# odd/tasks/p1-cimientos.md T2: ventana_ini + cuenta_alias + conjunto + anuncio -> ad_id, metodo.
MAPA_AD_ID_HIST_KEY = ("ventana_ini", "cuenta_alias", "conjunto", "anuncio")

METODOS_ATRIBUCION = ("ad_id", "ad_id_verificado_gasto", "nombre", "sin_atribuir")


def ruta_csv(nombre_archivo):
    return os.path.join(PRODUCTOS_DIR, nombre_archivo)


def leer_header(nombre_archivo):
    """Header real del CSV, en su orden real. None si el archivo no existe."""
    import csv
    import io

    path = ruta_csv(nombre_archivo)
    if not os.path.exists(path):
        return None
    with io.open(path, encoding="utf-8-sig", newline="") as f:
        r = csv.reader(f)
        try:
            return next(r)
        except StopIteration:
            return []


def nombre_columna_sql(col):
    """snake_case ya viene de los CSV; solo defendemos contra un nombre vacío o raro."""
    c = (col or "").strip().lower()
    if not c or not all(ch.isalnum() or ch == "_" for ch in c):
        raise ValueError("columna de CSV no apta como nombre de columna SQL: %r" % (col,))
    return c


def columnas_csv_y_sql(tabla, archivo, opcional):
    """[(columna_csv_original, columna_sql)] en orden real, sin EXTRA_COLUMNS. Usa
    COLUMN_RENAMES para el único caso de choque conocido (aprendizajes.id)."""
    header = leer_header(archivo)
    if header is None:
        if not opcional:
            raise FileNotFoundError("CSV requerido no encontrado: %s" % archivo)
        header = []
    renombres = COLUMN_RENAMES.get(tabla, {})
    pares = []
    for c in header:
        sql = nombre_columna_sql(c)
        pares.append((sql, renombres.get(sql, sql)))
    return pares


def columnas_tabla(tabla, archivo, opcional):
    """Columnas CSV (verbatim) + EXTRA_COLUMNS, en orden. Si el CSV no existe (opcional=True),
    usa el header congelado la última vez que existió — hoy ninguna tabla opcional lo necesita
    porque _VOZ_CLIENTE.csv aún no tiene ni encabezado; se declara vacío y `cargar.py` no inserta
    filas."""
    header = leer_header(archivo)
    if header is None:
        if not opcional:
            raise FileNotFoundError("CSV requerido no encontrado: %s" % archivo)
        header = []
    renombres = COLUMN_RENAMES.get(tabla, {})
    cols = [renombres.get(nombre_columna_sql(c), nombre_columna_sql(c)) for c in header]
    cols.extend(EXTRA_COLUMNS.get(tabla, []))
    return cols


if __name__ == "__main__":
    # Regenera db/schema.sql a partir de los headers REALES de PRODUCTOS/*.csv. Correr a mano
    # cuando un CSV cambie de columnas; no lo ejecuta cargar.py ni exportar.py (schema.sql es un
    # artefacto versionado, no algo que se reescriba en cada carga).
    import datetime

    out = []
    out.append("-- schema.sql — generado por db/tables.py (%s). DDL idempotente, esquema core."
                % datetime.date.today().isoformat())
    out.append("-- Un dato, un dueño: cada tabla es un espejo verbatim de su CSV en PRODUCTOS/,")
    out.append("-- más tenant_id (single tenant 'vitalcom') e id. Ver tables.py para el porqué.")
    out.append("")
    out.append("CREATE SCHEMA IF NOT EXISTS core;")
    out.append("")
    out.append("CREATE TABLE IF NOT EXISTS core.raw_import (")
    out.append("    id BIGSERIAL PRIMARY KEY,")
    out.append("    tenant_id TEXT NOT NULL DEFAULT 'vitalcom',")
    out.append("    archivo TEXT NOT NULL,")
    out.append("    sha256 TEXT,")
    out.append("    filas INTEGER NOT NULL DEFAULT 0,")
    out.append("    loaded_at TIMESTAMPTZ NOT NULL DEFAULT now()")
    out.append(");")
    out.append("")
    out.append("CREATE TABLE IF NOT EXISTS core.decision (")
    out.append("    id BIGSERIAL PRIMARY KEY,")
    out.append("    tenant_id TEXT NOT NULL DEFAULT 'vitalcom',")
    out.append("    fecha TEXT,")
    out.append("    payload JSONB NOT NULL,")
    out.append("    loaded_at TIMESTAMPTZ NOT NULL DEFAULT now()")
    out.append(");")
    out.append("")

    for tabla, archivo, opcional in TABLE_SPECS:
        cols = columnas_tabla(tabla, archivo, opcional)
        out.append("-- %s <- PRODUCTOS/%s" % (tabla, archivo))
        out.append("CREATE TABLE IF NOT EXISTS core.%s (" % tabla)
        out.append("    id BIGSERIAL PRIMARY KEY,")
        out.append("    tenant_id TEXT NOT NULL DEFAULT 'vitalcom',")
        for c in cols:
            out.append("    %s TEXT," % c)
        out.append("    loaded_at TIMESTAMPTZ NOT NULL DEFAULT now()")
        out.append(");")
        out.append("")

    out.append("-- Vista de conveniencia: ángulos distintos ya presentes en `conjunto`")
    out.append("-- (_DIM_CONJUNTOS.csv). No es una tabla física — nada la carga ni la exporta;")
    out.append("-- ver la nota en tables.py sobre por qué `angulo` no es tabla en P1.")
    out.append("CREATE OR REPLACE VIEW core.angulo AS")
    out.append("SELECT DISTINCT tenant_id, producto_key, angulo_key, angulo_nombre, avatar,")
    out.append("       dolor_nucleo, emocion_dominante, avatar_edad, avatar_genero,")
    out.append("       nivel_conciencia, NULL::text AS deseo")
    out.append("FROM core.conjunto")
    out.append("WHERE angulo_key IS NOT NULL AND angulo_key <> '';")
    out.append("")

    schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schema.sql")
    with open(schema_path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(out) + "\n")
    print("escrito", schema_path)
