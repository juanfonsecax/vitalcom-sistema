#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""nucleo.py — capa `core`: modelo normalizado y tipado, construido A PARTIR de `raw` (P1-cimientos
T5b, reapertura 23-sep-2026).

POR QUÉ EXISTE. T5 entregó un espejo verbatim de cada CSV (una tabla por CSV, texto tal cual) y
probó la paridad de `decidir.py` SOBRE ESE ESPEJO. Eso prueba el viaje ida-vuelta, pero no que el
modelo aprobado por el operador (producto -> ángulo -> creativo/concepto -> conjunto/anuncio con
historial de nombre -> hechos diarios tipados) sostiene lo que `decidir.py` necesita. Esta reapertura
renombra el espejo verbatim a `raw` (queda como capa de auditoría/staging, intacta) y construye
`core` desde `raw`, con FK reales, casts seguros (texto -> numeric/date/int) y un reporte de
reconciliación honesto en vez de asumir que todo castea.

REGLA DURA: cuando un valor de CSV no puede satisfacer un FK o un tipo, la fila NO se descarta —
se guarda con el FK/tipo en NULL y se cuenta en `construir_core()["reconciliacion"]`. Nunca se
inventa un valor para que un cast o un JOIN "cierre".

Reusa la lógica de join ya expresada en warehouse/ (dbt): el mismo criterio de alias/canónico que
`Ads/_TOOLS/alias.py` (nombre_hist con un salto de indirección, no una cadena recursiva — ver
`conjunto_nombre_hist` más abajo) y el mismo criterio de atribución de venta que `db/cargar.py`
(`enriquecer_venta`, T2b: join por `venta_uid`, no por posición).

ALCANCE: `core` cubre exactamente las entidades del modelo mínimo aprobado MÁS las 9 tablas que
`Ads/_TOOLS/decidir.py` (vía `gasto.py`/`alias.py`) lee directamente — son las que
`exportar.exportar_core_decidir()` reconstruye para el gate de paridad (T6). El resto de los CSV
(_DIM_CREATIVOS.csv con matiz aparte, _EVENTOS.csv, _DIM_CUENTAS.csv, etc.) también tiene su
versión normalizada acá porque son la base estructural (producto/cuenta/angulo/creativo/anuncio)
de las que sí se leen — pero solo esas 9 necesitan ser export-fieles.
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tables as T  # noqa: E402

sys.path.insert(0, os.path.join(T.BASE_DIR, "Ads", "_TOOLS"))
from venta_identidad import asignar_venta_uids  # noqa: E402


# ── DDL ──────────────────────────────────────────────────────────────────────────────────────

CORE_DDL_SQL = r"""
-- ================================================================================================
-- schema `core` — modelo normalizado/tipado (P1-cimientos T5b). Construido desde `raw` por
-- db/nucleo.py:construir_core(), en la MISMA transacción que carga `raw`. Nunca se llena a mano.
-- ================================================================================================

CREATE SCHEMA IF NOT EXISTS core;

CREATE OR REPLACE FUNCTION core.try_numeric(t text) RETURNS numeric AS $$
BEGIN
  IF t IS NULL OR btrim(t) = '' THEN RETURN NULL; END IF;
  RETURN btrim(t)::numeric;
EXCEPTION WHEN others THEN RETURN NULL;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

CREATE OR REPLACE FUNCTION core.try_int(t text) RETURNS integer AS $$
BEGIN
  IF t IS NULL OR btrim(t) = '' THEN RETURN NULL; END IF;
  RETURN round(btrim(t)::numeric)::integer;
EXCEPTION WHEN others THEN RETURN NULL;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

CREATE OR REPLACE FUNCTION core.try_date(t text) RETURNS date AS $$
BEGIN
  IF t IS NULL OR btrim(t) = '' THEN RETURN NULL; END IF;
  RETURN btrim(t)::date;
EXCEPTION WHEN others THEN RETURN NULL;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

CREATE OR REPLACE FUNCTION core.try_bool(t text) RETURNS boolean AS $$
BEGIN
  IF t IS NULL OR btrim(t) = '' THEN RETURN NULL; END IF;
  RETURN lower(btrim(t)) IN ('1','true','si','sí','yes','x','verdadero');
EXCEPTION WHEN others THEN RETURN NULL;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

CREATE TABLE IF NOT EXISTS core.tenant (
  tenant_id TEXT PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS core.producto (
  id BIGSERIAL PRIMARY KEY,
  tenant_id TEXT NOT NULL REFERENCES core.tenant(tenant_id),
  producto_key TEXT NOT NULL,
  nombre_display TEXT,
  slug_carpeta TEXT,
  estado TEXT,
  fase TEXT,
  cuenta_alias TEXT,
  cuenta_id_meta TEXT,
  page_id TEXT,
  moneda TEXT,
  tasa NUMERIC,
  costo_q NUMERIC,
  fila_costeo_q TEXT,
  precio_base_q NUMERIC,
  cpa_base_q NUMERIC,
  cpa_be_q NUMERIC,
  cpa_be_anterior_q NUMERIC,
  notas TEXT,
  carpeta_videos TEXT,
  carpeta_transcripciones TEXT,
  carpeta_media TEXT,
  carpetas_extra TEXT,
  clave_campana TEXT,
  campaign_id TEXT,
  raw_id BIGINT,
  UNIQUE (tenant_id, producto_key)
);

CREATE TABLE IF NOT EXISTS core.cuenta (
  id BIGSERIAL PRIMARY KEY,
  tenant_id TEXT NOT NULL REFERENCES core.tenant(tenant_id),
  cuenta_alias TEXT NOT NULL,
  cuenta_id_meta TEXT,
  negocio_id TEXT,
  negocio TEXT,
  moneda TEXT,
  min_daily_budget_cents NUMERIC,
  mcp_habilitado BOOLEAN,
  consultable BOOLEAN,
  tiene_metodo_pago BOOLEAN,
  sube_media_local BOOLEAN,
  estado_cuenta TEXT,
  raw_id BIGINT,
  UNIQUE (tenant_id, cuenta_alias)
);

CREATE TABLE IF NOT EXISTS core.angulo (
  id BIGSERIAL PRIMARY KEY,
  tenant_id TEXT NOT NULL REFERENCES core.tenant(tenant_id),
  producto_id BIGINT REFERENCES core.producto(id),
  producto_key TEXT,
  angulo_key TEXT NOT NULL,
  angulo_nombre TEXT,
  avatar TEXT,
  dolor_nucleo TEXT,
  emocion_dominante TEXT,
  avatar_edad TEXT,
  avatar_genero TEXT,
  nivel_conciencia TEXT,
  deseo TEXT,
  UNIQUE (tenant_id, producto_key, angulo_key)
);

CREATE TABLE IF NOT EXISTS core.catalogo_concepto (
  id BIGSERIAL PRIMARY KEY,
  tenant_id TEXT NOT NULL REFERENCES core.tenant(tenant_id),
  concepto_key TEXT NOT NULL,
  UNIQUE (tenant_id, concepto_key)
);

CREATE TABLE IF NOT EXISTS core.conjunto_nombre_hist (
  id BIGSERIAL PRIMARY KEY,
  tenant_id TEXT NOT NULL REFERENCES core.tenant(tenant_id),
  producto_id BIGINT REFERENCES core.producto(id),
  producto_key TEXT,
  cuenta_id BIGINT REFERENCES core.cuenta(id),
  cuenta_alias TEXT,
  alias_nombre TEXT NOT NULL,
  nombre_canonico TEXT NOT NULL,
  valid_from DATE,
  valid_to DATE,
  motivo TEXT,
  raw_id BIGINT
);

CREATE TABLE IF NOT EXISTS core.conjunto (
  id BIGSERIAL PRIMARY KEY,
  tenant_id TEXT NOT NULL REFERENCES core.tenant(tenant_id),
  producto_id BIGINT REFERENCES core.producto(id),
  producto_key TEXT,
  angulo_id BIGINT REFERENCES core.angulo(id),
  angulo_key TEXT,
  cuenta_id BIGINT REFERENCES core.cuenta(id),
  cuenta_alias TEXT,
  concepto_id BIGINT REFERENCES core.catalogo_concepto(id),
  concepto_key TEXT,
  conjunto_meta TEXT NOT NULL,
  campana_clave TEXT,
  fase TEXT,
  angulo_nombre TEXT,
  avatar TEXT,
  dolor_nucleo TEXT,
  emocion_dominante TEXT,
  avatar_edad TEXT,
  avatar_genero TEXT,
  formato TEXT,
  tipo_hook TEXT,
  nivel_conciencia TEXT,
  rol_embudo TEXT,
  rol_embudo_origen TEXT,
  lleva_precio TEXT,
  creativo_id TEXT,
  origen_angulo TEXT,
  estado TEXT,
  verificado_en_csv TEXT,
  fecha_alta DATE,
  notas TEXT,
  raw_id BIGINT,
  UNIQUE (tenant_id, producto_key, conjunto_meta)
);

CREATE TABLE IF NOT EXISTS core.creativo (
  id BIGSERIAL PRIMARY KEY,
  tenant_id TEXT NOT NULL REFERENCES core.tenant(tenant_id),
  producto_id BIGINT REFERENCES core.producto(id),
  producto_key TEXT,
  angulo_id BIGINT REFERENCES core.angulo(id),
  angulo_key TEXT,
  concepto_id BIGINT REFERENCES core.catalogo_concepto(id),
  concepto_key TEXT,
  creativo_id_csv TEXT,
  canonico_id TEXT,
  archivo TEXT,
  cuenta_destino TEXT,
  rol_embudo TEXT,
  ad_id TEXT,
  formato TEXT,
  fecha_alta DATE,
  estado TEXT,
  raw_id BIGINT
);

CREATE TABLE IF NOT EXISTS core.anuncio (
  id BIGSERIAL PRIMARY KEY,
  tenant_id TEXT NOT NULL REFERENCES core.tenant(tenant_id),
  producto_id BIGINT REFERENCES core.producto(id),
  producto_key TEXT,
  conjunto_id BIGINT REFERENCES core.conjunto(id),
  conjunto_nombre TEXT,
  cuenta_id BIGINT REFERENCES core.cuenta(id),
  cuenta_alias TEXT,
  creativo_id BIGINT REFERENCES core.creativo(id),
  anuncio_nombre TEXT NOT NULL,
  ad_id TEXT,
  angulo_key TEXT,
  concepto_key TEXT,
  canonico_id TEXT,
  UNIQUE (tenant_id, producto_key, cuenta_alias, conjunto_nombre, anuncio_nombre)
);

CREATE TABLE IF NOT EXISTS core.entrega_conjunto_dia (
  id BIGSERIAL PRIMARY KEY,
  tenant_id TEXT NOT NULL REFERENCES core.tenant(tenant_id),
  producto_id BIGINT REFERENCES core.producto(id),
  producto_key TEXT,
  cuenta_id BIGINT REFERENCES core.cuenta(id),
  cuenta_alias TEXT,
  cuenta_id_meta TEXT,
  conjunto_id BIGINT REFERENCES core.conjunto(id),
  conjunto_nombre TEXT,
  ventana_ini DATE,
  ventana_fin DATE,
  dias INTEGER,
  campana TEXT,
  mensajes INTEGER,
  clicks_totales INTEGER,
  link_clicks INTEGER,
  impresiones INTEGER,
  spend_usd NUMERIC,
  pct_conv_clic_enlace NUMERIC,
  fuente TEXT,
  raw_id BIGINT
);

CREATE TABLE IF NOT EXISTS core.entrega_anuncio_dia (
  id BIGSERIAL PRIMARY KEY,
  tenant_id TEXT NOT NULL REFERENCES core.tenant(tenant_id),
  producto_id BIGINT REFERENCES core.producto(id),
  producto_key TEXT,
  cuenta_id BIGINT REFERENCES core.cuenta(id),
  cuenta_alias TEXT,
  cuenta_id_meta TEXT,
  conjunto_id BIGINT REFERENCES core.conjunto(id),
  conjunto_nombre TEXT,
  anuncio_id BIGINT REFERENCES core.anuncio(id),
  anuncio_nombre TEXT,
  ad_id TEXT,
  ventana_ini DATE,
  ventana_fin DATE,
  dias INTEGER,
  campana TEXT,
  firma TEXT,
  angulo_key TEXT,
  concepto_key TEXT,
  canonico_id TEXT,
  nivel_conciencia TEXT,
  oferta_key TEXT,
  destino_key TEXT,
  mensajes INTEGER,
  clicks_totales INTEGER,
  link_clicks INTEGER,
  impresiones INTEGER,
  spend_usd NUMERIC,
  pct_conv_clic_enlace NUMERIC,
  fuente TEXT,
  raw_id BIGINT
);

CREATE TABLE IF NOT EXISTS core.venta (
  id BIGSERIAL PRIMARY KEY,
  tenant_id TEXT NOT NULL REFERENCES core.tenant(tenant_id),
  producto_id BIGINT REFERENCES core.producto(id),
  producto_key TEXT,
  producto_nombre TEXT,
  cuenta_id BIGINT REFERENCES core.cuenta(id),
  cuenta_alias TEXT,
  cuenta_id_meta TEXT,
  conjunto_id BIGINT REFERENCES core.conjunto(id),
  conjunto_nombre TEXT,
  anuncio_id BIGINT REFERENCES core.anuncio(id),
  anuncio_nombre TEXT,
  ventana_ini DATE,
  ventana_fin DATE,
  dias INTEGER,
  rol_ventana TEXT,
  campana TEXT,
  mensajes INTEGER,
  clicks INTEGER,
  impresiones INTEGER,
  spend_usd NUMERIC,
  ventas INTEGER,
  total_q NUMERIC,
  moneda_origen TEXT,
  fuente TEXT,
  ad_id TEXT,
  ad_id_resuelto TEXT,
  metodo_atribucion TEXT NOT NULL,
  venta_uid TEXT NOT NULL,
  raw_id BIGINT,
  UNIQUE (tenant_id, venta_uid)
);

CREATE TABLE IF NOT EXISTS core.evento (
  id BIGSERIAL PRIMARY KEY,
  tenant_id TEXT NOT NULL REFERENCES core.tenant(tenant_id),
  producto_id BIGINT REFERENCES core.producto(id),
  producto_key TEXT,
  cuenta_id BIGINT REFERENCES core.cuenta(id),
  cuenta_alias TEXT,
  conjunto_id BIGINT REFERENCES core.conjunto(id),
  conjunto_nombre TEXT,
  campana_clave TEXT,
  fecha DATE,
  evento TEXT,
  valor_antes TEXT,
  valor_despues TEXT,
  motivo TEXT,
  fuente_decision TEXT,
  raw_id BIGINT
);

-- No tiene CSV dueño (viene de _DECISIONES.json, no de PRODUCTOS/*.csv): no hay raw.decision que
-- normalizar. Se carga directo, igual que en T5, pero ahora vive únicamente en `core`.
CREATE TABLE IF NOT EXISTS core.decision (
  id BIGSERIAL PRIMARY KEY,
  tenant_id TEXT NOT NULL REFERENCES core.tenant(tenant_id),
  fecha TEXT,
  payload JSONB NOT NULL,
  loaded_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- "Versionado": cada carga es una foto completa (TRUNCATE+INSERT, igual que raw), no un historial
-- append-only -- los CSV fuente no traen columna de versión propia. `version` guarda el momento
-- de ESTA carga como marca de corte; ver README para la limitación honesta.
CREATE TABLE IF NOT EXISTS core.parametro_decision (
  id BIGSERIAL PRIMARY KEY,
  tenant_id TEXT NOT NULL REFERENCES core.tenant(tenant_id),
  parametro TEXT NOT NULL,
  valor TEXT,
  valor_num NUMERIC,
  unidad TEXT,
  dueno TEXT,
  por_que TEXT,
  version TIMESTAMPTZ NOT NULL DEFAULT now(),
  raw_id BIGINT
);

CREATE TABLE IF NOT EXISTS core.parametro_finanzas (
  id BIGSERIAL PRIMARY KEY,
  tenant_id TEXT NOT NULL REFERENCES core.tenant(tenant_id),
  parametro TEXT NOT NULL,
  valor TEXT,
  valor_num NUMERIC,
  unidad TEXT,
  origen TEXT,
  medido_el DATE,
  n_evidencia INTEGER,
  notas TEXT,
  version TIMESTAMPTZ NOT NULL DEFAULT now(),
  raw_id BIGINT
);

-- Leídas directamente por Ads/_TOOLS/decidir.py (DIM_BANDAS_PATH / ESTADO_FLUJO_PATH): necesitan
-- reconstrucción fiel para el gate de paridad (T6), aunque decidir.py no tipa estas columnas.
CREATE TABLE IF NOT EXISTS core.banda (
  id BIGSERIAL PRIMARY KEY,
  tenant_id TEXT NOT NULL REFERENCES core.tenant(tenant_id),
  producto_id BIGINT REFERENCES core.producto(id),
  producto_key TEXT,
  conjunto_id BIGINT REFERENCES core.conjunto(id),
  cuenta_alias TEXT,
  conjunto_meta TEXT,
  angulo_key TEXT,
  banda_configurada TEXT,
  avatar_edad_doctrina TEXT,
  coincide TEXT,
  desde DATE,
  hasta DATE,
  fuente TEXT,
  notas TEXT,
  raw_id BIGINT
);

CREATE TABLE IF NOT EXISTS core.estado_flujo (
  id BIGSERIAL PRIMARY KEY,
  tenant_id TEXT NOT NULL REFERENCES core.tenant(tenant_id),
  producto_id BIGINT REFERENCES core.producto(id),
  producto_key TEXT,
  fase TEXT,
  nodo_actual TEXT,
  estado TEXT,
  desde DATE,
  bloqueantes TEXT,
  siguiente_ejecutor TEXT,
  evaluado_el DATE,
  raw_id BIGINT
);
""".strip() + "\n"


# ── build (raw -> core), en la misma transacción que cargar.cargar_todo() ───────────────────────

CORE_TABLES_EN_ORDEN = [
    "parametro_decision", "parametro_finanzas", "banda", "estado_flujo", "evento", "venta",
    "entrega_anuncio_dia", "entrega_conjunto_dia", "anuncio", "creativo", "conjunto",
    "conjunto_nombre_hist", "catalogo_concepto", "angulo", "cuenta", "producto", "decision",
]


def _vaciar_core(cur, tenant_id):
    """TRUNCATE de todas las tablas core para este tenant (idempotencia: se reconstruye entero en
    cada carga, igual que `raw`). Orden inverso al de construcción para respetar FKs."""
    for tabla in CORE_TABLES_EN_ORDEN:
        cur.execute("DELETE FROM core.%s WHERE tenant_id = %%s" % tabla, (tenant_id,))
    cur.execute(
        "INSERT INTO core.tenant (tenant_id) VALUES (%s) ON CONFLICT (tenant_id) DO NOTHING",
        (tenant_id,),
    )


def _fetchall_dict(cur, sql, params):
    cur.execute(sql, params)
    cols = [d.name for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


def construir_core(cur, tenant_id):
    """Construye `core.*` desde `raw.*` para `tenant_id`, en la MISMA transacción que ya tiene
    abierta `cargar.cargar_todo()`. Devuelve un reporte de reconciliación honesto: conteos por
    tabla, filas con FK sin resolver (con la razón) y conservación raw->core para los hechos.

    P3 T2: ya no recibe una ruta de `_DECISIONES.json` en disco — `core.decision` se arma desde
    `raw.decisiones_json` (texto verbatim, cargado por `cargar.cargar_decisiones_json()` en la
    MISMA transacción antes de llamar acá). `_DECISIONES.json` no tiene CSV dueño, así que esta
    es la única forma de que su verdad viva en Postgres (ver tables.TABLAS_VERDAD_DB) sin volver
    a leer el archivo del disco en cada reconstrucción de `core`."""
    _vaciar_core(cur, tenant_id)
    reporte = {"tablas": {}, "fk_sin_resolver": {}, "conservacion": {}}

    # producto ------------------------------------------------------------------------------
    cur.execute(
        """
        INSERT INTO core.producto (
            tenant_id, producto_key, nombre_display, slug_carpeta, estado, fase, cuenta_alias,
            cuenta_id_meta, page_id, moneda, tasa, costo_q, fila_costeo_q, precio_base_q,
            cpa_base_q, cpa_be_q, cpa_be_anterior_q, notas, carpeta_videos,
            carpeta_transcripciones, carpeta_media, carpetas_extra, clave_campana, campaign_id,
            raw_id
        )
        SELECT tenant_id, producto_key, nombre_display, slug_carpeta, estado, fase, cuenta_alias,
               cuenta_id, page_id, moneda, core.try_numeric(tasa), core.try_numeric(costo_q),
               fila_costeo_q, core.try_numeric(precio_base_q), core.try_numeric(cpa_base_q),
               core.try_numeric(cpa_be_q), core.try_numeric(cpa_be_anterior_q), notas,
               carpeta_videos, carpeta_transcripciones, carpeta_media, carpetas_extra,
               clave_campana, campaign_id, id
        FROM raw.producto WHERE tenant_id = %s AND producto_key IS NOT NULL AND producto_key <> ''
        """,
        (tenant_id,),
    )

    # cuenta --------------------------------------------------------------------------------
    cur.execute(
        """
        INSERT INTO core.cuenta (
            tenant_id, cuenta_alias, cuenta_id_meta, negocio_id, negocio, moneda,
            min_daily_budget_cents, mcp_habilitado, consultable, tiene_metodo_pago,
            sube_media_local, estado_cuenta, raw_id
        )
        SELECT tenant_id, cuenta_alias, cuenta_id, negocio_id, negocio, moneda,
               core.try_numeric(min_daily_budget_cents), core.try_bool(mcp_habilitado),
               core.try_bool(consultable), core.try_bool(tiene_metodo_pago),
               core.try_bool(sube_media_local), estado_cuenta, id
        FROM raw.dim_cuentas
        WHERE tenant_id = %s AND cuenta_alias IS NOT NULL AND cuenta_alias <> ''
        ON CONFLICT (tenant_id, cuenta_alias) DO NOTHING
        """,
        (tenant_id,),
    )

    # angulo (distinct por producto+angulo_key, atributos de _DIM_CONJUNTOS.csv) -------------
    cur.execute(
        """
        INSERT INTO core.angulo (
            tenant_id, producto_id, producto_key, angulo_key, angulo_nombre, avatar,
            dolor_nucleo, emocion_dominante, avatar_edad, avatar_genero, nivel_conciencia, deseo
        )
        SELECT DISTINCT ON (r.tenant_id, r.producto_key, r.angulo_key)
               r.tenant_id, p.id, r.producto_key, r.angulo_key, r.angulo_nombre, r.avatar,
               r.dolor_nucleo, r.emocion_dominante, r.avatar_edad, r.avatar_genero,
               r.nivel_conciencia, NULL::text
        FROM raw.conjunto r
        LEFT JOIN core.producto p ON p.tenant_id = r.tenant_id AND p.producto_key = r.producto_key
        WHERE r.tenant_id = %s AND r.angulo_key IS NOT NULL AND r.angulo_key <> ''
        ORDER BY r.tenant_id, r.producto_key, r.angulo_key, r.id
        """,
        (tenant_id,),
    )

    # catalogo_concepto (distinct, de conjunto + creativo) -----------------------------------
    cur.execute(
        """
        INSERT INTO core.catalogo_concepto (tenant_id, concepto_key)
        SELECT DISTINCT tenant_id, concepto_key FROM (
            SELECT tenant_id, concepto_key FROM raw.conjunto WHERE tenant_id = %s
            UNION
            SELECT tenant_id, concepto_key FROM raw.creativo WHERE tenant_id = %s
        ) u
        WHERE concepto_key IS NOT NULL AND concepto_key <> ''
        """,
        (tenant_id, tenant_id),
    )

    # conjunto_nombre_hist (reemplaza _ALIAS_CONJUNTOS.csv / alias.py) -----------------------
    cur.execute(
        """
        INSERT INTO core.conjunto_nombre_hist (
            tenant_id, producto_id, producto_key, cuenta_id, cuenta_alias, alias_nombre,
            nombre_canonico, valid_from, valid_to, motivo, raw_id
        )
        SELECT r.tenant_id, p.id, r.producto_key, cu.id, r.cuenta_alias, r.nombre_viejo,
               r.nombre_nuevo, core.try_date(r.desde), NULL::date, r.motivo, r.id
        FROM raw.conjunto_nombre_hist r
        LEFT JOIN core.producto p ON p.tenant_id = r.tenant_id AND p.producto_key = r.producto_key
        LEFT JOIN core.cuenta cu ON cu.tenant_id = r.tenant_id AND replace(cu.cuenta_alias, ' ', '') = replace(r.cuenta_alias, ' ', '')
        WHERE r.tenant_id = %s
        """,
        (tenant_id,),
    )

    # conjunto (un hop de alias: si conjunto_meta no matchea, prueba su nombre_canonico) -----
    cur.execute(
        """
        INSERT INTO core.conjunto (
            tenant_id, producto_id, producto_key, angulo_id, angulo_key, cuenta_id, cuenta_alias,
            concepto_id, concepto_key, conjunto_meta, campana_clave, fase, angulo_nombre, avatar,
            dolor_nucleo, emocion_dominante, avatar_edad, avatar_genero, formato, tipo_hook,
            nivel_conciencia, rol_embudo, rol_embudo_origen, lleva_precio, creativo_id,
            origen_angulo, estado, verificado_en_csv, fecha_alta, notas, raw_id
        )
        SELECT r.tenant_id, p.id, r.producto_key, a.id, r.angulo_key, cu.id, r.cuenta_alias,
               cc.id, r.concepto_key, r.conjunto_meta, r.campana_clave, r.fase, r.angulo_nombre,
               r.avatar, r.dolor_nucleo, r.emocion_dominante, r.avatar_edad, r.avatar_genero,
               r.formato, r.tipo_hook, r.nivel_conciencia, r.rol_embudo, r.rol_embudo_origen,
               r.lleva_precio, r.creativo_id, r.origen_angulo, r.estado, r.verificado_en_csv,
               core.try_date(r.fecha_alta), r.notas, r.id
        FROM raw.conjunto r
        LEFT JOIN core.producto p ON p.tenant_id = r.tenant_id AND p.producto_key = r.producto_key
        LEFT JOIN core.cuenta cu ON cu.tenant_id = r.tenant_id AND replace(cu.cuenta_alias, ' ', '') = replace(r.cuenta_alias, ' ', '')
        LEFT JOIN core.angulo a ON a.tenant_id = r.tenant_id AND a.producto_id = p.id
                                AND a.angulo_key = r.angulo_key
        LEFT JOIN core.catalogo_concepto cc ON cc.tenant_id = r.tenant_id
                                            AND cc.concepto_key = r.concepto_key
        WHERE r.tenant_id = %s
        """,
        (tenant_id,),
    )

    # creativo --------------------------------------------------------------------------------
    cur.execute(
        """
        INSERT INTO core.creativo (
            tenant_id, producto_id, producto_key, angulo_id, angulo_key, concepto_id,
            concepto_key, creativo_id_csv, canonico_id, archivo, cuenta_destino, rol_embudo,
            ad_id, formato, fecha_alta, estado, raw_id
        )
        SELECT r.tenant_id, p.id, r.producto_key, a.id, r.angulo_key, cc.id, r.concepto_key,
               r.creativo_id, r.canonico_id, r.archivo, r.cuenta_destino, r.rol_embudo, r.ad_id,
               r.formato, core.try_date(r.fecha_alta), r.estado, r.id
        FROM raw.creativo r
        LEFT JOIN core.producto p ON p.tenant_id = r.tenant_id AND p.producto_key = r.producto_key
        LEFT JOIN core.angulo a ON a.tenant_id = r.tenant_id AND a.producto_id = p.id
                                AND a.angulo_key = r.angulo_key
        LEFT JOIN core.catalogo_concepto cc ON cc.tenant_id = r.tenant_id
                                            AND cc.concepto_key = r.concepto_key
        WHERE r.tenant_id = %s
        """,
        (tenant_id,),
    )

    # anuncio (distinct desde entrega_anuncio_dia: ya trae ad_id/angulo_key/concepto_key) ----
    cur.execute(
        """
        INSERT INTO core.anuncio (
            tenant_id, producto_id, producto_key, conjunto_id, conjunto_nombre, cuenta_id,
            cuenta_alias, creativo_id, anuncio_nombre, ad_id, angulo_key, concepto_key,
            canonico_id
        )
        SELECT DISTINCT ON (r.tenant_id, r.producto_key, r.cuenta_alias, r.conjunto, r.anuncio)
               r.tenant_id, p.id, r.producto_key, co.id, r.conjunto, cu.id, r.cuenta_alias,
               cr.id, r.anuncio, r.ad_id, r.angulo_key, r.concepto_key, r.canonico_id
        FROM raw.entrega_anuncio_dia r
        LEFT JOIN core.producto p ON p.tenant_id = r.tenant_id AND p.producto_key = r.producto_key
        LEFT JOIN core.cuenta cu ON cu.tenant_id = r.tenant_id AND replace(cu.cuenta_alias, ' ', '') = replace(r.cuenta_alias, ' ', '')
        LEFT JOIN core.conjunto_nombre_hist h ON h.tenant_id = r.tenant_id
                                              AND h.producto_key = r.producto_key
                                              AND h.alias_nombre = r.conjunto
        LEFT JOIN core.conjunto co ON co.tenant_id = r.tenant_id AND co.producto_id = p.id
                                   AND co.conjunto_meta = COALESCE(h.nombre_canonico, r.conjunto)
        LEFT JOIN core.creativo cr ON cr.tenant_id = r.tenant_id
                                   AND cr.canonico_id = r.canonico_id AND r.canonico_id <> ''
        WHERE r.tenant_id = %s AND r.anuncio IS NOT NULL AND r.anuncio <> ''
        ORDER BY r.tenant_id, r.producto_key, r.cuenta_alias, r.conjunto, r.anuncio, r.id DESC
        """,
        (tenant_id,),
    )

    # entrega_conjunto_dia --------------------------------------------------------------------
    cur.execute(
        """
        INSERT INTO core.entrega_conjunto_dia (
            tenant_id, producto_id, producto_key, cuenta_id, cuenta_alias, cuenta_id_meta,
            conjunto_id, conjunto_nombre, ventana_ini, ventana_fin, dias, campana, mensajes,
            clicks_totales, link_clicks, impresiones, spend_usd, pct_conv_clic_enlace, fuente,
            raw_id
        )
        SELECT r.tenant_id, p.id, r.producto_key, cu.id, r.cuenta_alias, r.cuenta_id,
               co.id, r.conjunto, core.try_date(r.ventana_ini), core.try_date(r.ventana_fin),
               core.try_int(r.dias), r.campana, core.try_int(r.mensajes),
               core.try_int(r.clicks_totales), core.try_int(r.link_clicks),
               core.try_int(r.impresiones), core.try_numeric(r.spend_usd),
               core.try_numeric(r.pct_conv_clic_enlace), r.fuente, r.id
        FROM raw.entrega_conjunto_dia r
        LEFT JOIN core.producto p ON p.tenant_id = r.tenant_id AND p.producto_key = r.producto_key
        LEFT JOIN core.cuenta cu ON cu.tenant_id = r.tenant_id AND replace(cu.cuenta_alias, ' ', '') = replace(r.cuenta_alias, ' ', '')
        LEFT JOIN core.conjunto_nombre_hist h ON h.tenant_id = r.tenant_id
                                              AND h.producto_key = r.producto_key
                                              AND h.alias_nombre = r.conjunto
        LEFT JOIN core.conjunto co ON co.tenant_id = r.tenant_id AND co.producto_id = p.id
                                   AND co.conjunto_meta = COALESCE(h.nombre_canonico, r.conjunto)
        WHERE r.tenant_id = %s
        """,
        (tenant_id,),
    )

    # entrega_anuncio_dia ---------------------------------------------------------------------
    cur.execute(
        """
        INSERT INTO core.entrega_anuncio_dia (
            tenant_id, producto_id, producto_key, cuenta_id, cuenta_alias, cuenta_id_meta,
            conjunto_id, conjunto_nombre, anuncio_id, anuncio_nombre, ad_id, ventana_ini,
            ventana_fin, dias, campana, firma, angulo_key, concepto_key, canonico_id,
            nivel_conciencia, oferta_key, destino_key, mensajes, clicks_totales, link_clicks,
            impresiones, spend_usd, pct_conv_clic_enlace, fuente, raw_id
        )
        SELECT r.tenant_id, p.id, r.producto_key, cu.id, r.cuenta_alias, r.cuenta_id,
               co.id, r.conjunto, an.id, r.anuncio, r.ad_id, core.try_date(r.ventana_ini),
               core.try_date(r.ventana_fin), core.try_int(r.dias), r.campana, r.firma,
               r.angulo_key, r.concepto_key, r.canonico_id, r.nivel_conciencia, r.oferta_key,
               r.destino_key, core.try_int(r.mensajes), core.try_int(r.clicks_totales),
               core.try_int(r.link_clicks), core.try_int(r.impresiones),
               core.try_numeric(r.spend_usd), core.try_numeric(r.pct_conv_clic_enlace), r.fuente,
               r.id
        FROM raw.entrega_anuncio_dia r
        LEFT JOIN core.producto p ON p.tenant_id = r.tenant_id AND p.producto_key = r.producto_key
        LEFT JOIN core.cuenta cu ON cu.tenant_id = r.tenant_id AND replace(cu.cuenta_alias, ' ', '') = replace(r.cuenta_alias, ' ', '')
        LEFT JOIN core.conjunto_nombre_hist h ON h.tenant_id = r.tenant_id
                                              AND h.producto_key = r.producto_key
                                              AND h.alias_nombre = r.conjunto
        LEFT JOIN core.conjunto co ON co.tenant_id = r.tenant_id AND co.producto_id = p.id
                                   AND co.conjunto_meta = COALESCE(h.nombre_canonico, r.conjunto)
        LEFT JOIN core.anuncio an ON an.tenant_id = r.tenant_id AND an.producto_key = r.producto_key
                                  AND an.cuenta_alias = r.cuenta_alias
                                  AND an.conjunto_nombre = r.conjunto AND an.anuncio_nombre = r.anuncio
        WHERE r.tenant_id = %s
        """,
        (tenant_id,),
    )

    # evento ------------------------------------------------------------------------------------
    cur.execute(
        """
        INSERT INTO core.evento (
            tenant_id, producto_id, producto_key, cuenta_id, cuenta_alias, conjunto_id,
            conjunto_nombre, campana_clave, fecha, evento, valor_antes, valor_despues, motivo,
            fuente_decision, raw_id
        )
        SELECT r.tenant_id, p.id, r.producto_key, cu.id, r.cuenta_alias, co.id, r.conjunto_meta,
               r.campana_clave, core.try_date(r.fecha), r.evento, r.valor_antes, r.valor_despues,
               r.motivo, r.fuente_decision, r.id
        FROM raw.evento r
        LEFT JOIN core.producto p ON p.tenant_id = r.tenant_id AND p.producto_key = r.producto_key
        LEFT JOIN core.cuenta cu ON cu.tenant_id = r.tenant_id AND replace(cu.cuenta_alias, ' ', '') = replace(r.cuenta_alias, ' ', '')
        LEFT JOIN core.conjunto_nombre_hist h ON h.tenant_id = r.tenant_id
                                              AND h.producto_key = r.producto_key
                                              AND h.alias_nombre = r.conjunto_meta
        LEFT JOIN core.conjunto co ON co.tenant_id = r.tenant_id AND co.producto_id = p.id
                                   AND co.conjunto_meta = COALESCE(h.nombre_canonico, r.conjunto_meta)
        WHERE r.tenant_id = %s
        """,
        (tenant_id,),
    )

    # banda / estado_flujo -----------------------------------------------------------------------
    cur.execute(
        """
        INSERT INTO core.banda (
            tenant_id, producto_id, producto_key, conjunto_id, cuenta_alias, conjunto_meta,
            angulo_key, banda_configurada, avatar_edad_doctrina, coincide, desde, hasta, fuente,
            notas, raw_id
        )
        SELECT r.tenant_id, p.id, r.producto_key, co.id, r.cuenta_alias, r.conjunto_meta,
               r.angulo_key, r.banda_configurada, r.avatar_edad_doctrina, r.coincide,
               core.try_date(r.desde), core.try_date(r.hasta), r.fuente, r.notas, r.id
        FROM raw.dim_bandas r
        LEFT JOIN core.producto p ON p.tenant_id = r.tenant_id AND p.producto_key = r.producto_key
        LEFT JOIN core.conjunto co ON co.tenant_id = r.tenant_id AND co.producto_id = p.id
                                   AND co.conjunto_meta = r.conjunto_meta
        WHERE r.tenant_id = %s
        """,
        (tenant_id,),
    )

    cur.execute(
        """
        INSERT INTO core.estado_flujo (
            tenant_id, producto_id, producto_key, fase, nodo_actual, estado, desde, bloqueantes,
            siguiente_ejecutor, evaluado_el, raw_id
        )
        SELECT r.tenant_id, p.id, r.producto_key, r.fase, r.nodo_actual, r.estado,
               core.try_date(r.desde), r.bloqueantes, r.siguiente_ejecutor,
               core.try_date(r.evaluado_el), r.id
        FROM raw.estado_flujo r
        LEFT JOIN core.producto p ON p.tenant_id = r.tenant_id AND p.producto_key = r.producto_key
        WHERE r.tenant_id = %s
        """,
        (tenant_id,),
    )

    # parametro_decision / parametro_finanzas --------------------------------------------------
    cur.execute(
        """
        INSERT INTO core.parametro_decision (tenant_id, parametro, valor, valor_num, unidad,
                                              dueno, por_que, raw_id)
        SELECT tenant_id, parametro, valor, core.try_numeric(valor), unidad, dueno, por_que, id
        FROM raw.parametros_decision WHERE tenant_id = %s
        """,
        (tenant_id,),
    )
    cur.execute(
        """
        INSERT INTO core.parametro_finanzas (tenant_id, parametro, valor, valor_num, unidad,
                                              origen, medido_el, n_evidencia, notas, raw_id)
        SELECT tenant_id, parametro, valor, core.try_numeric(valor), unidad, origen,
               core.try_date(medido_el), core.try_int(n_evidencia), notas, id
        FROM raw.parametros_finanzas WHERE tenant_id = %s
        """,
        (tenant_id,),
    )

    # venta (T2b: join por venta_uid, enriquecimiento en Python vía cargar.enriquecer_venta) ----
    # OJO: venta_uid se calcula SOLO sobre las columnas reales de _FACT_VENTAS.csv, en su mismo
    # orden -- exactamente como lo hizo Ads/_TOOLS/mapear_ad_id_hist.py al generar el mapa. Un
    # `SELECT *` traería también id/tenant_id/loaded_at (no existen en el CSV) y el hash no
    # coincidiría con el venta_uid ya escrito en _MAPA_AD_ID_HIST.csv.
    cols_venta = [c for c, _ in T.columnas_csv_y_sql("venta", "_FACT_VENTAS.csv", False)]
    filas_venta_full = _fetchall_dict(
        cur, "SELECT id, %s FROM raw.venta WHERE tenant_id = %%s ORDER BY id"
        % ", ".join('"%s"' % c for c in cols_venta),
        (tenant_id,),
    )
    filas_venta = [{c: f[c] for c in cols_venta} for f in filas_venta_full]
    ids_raw = [f["id"] for f in filas_venta_full]
    filas_mapa = _fetchall_dict(
        cur, "SELECT * FROM raw.mapa_ad_id_hist WHERE tenant_id = %s", (tenant_id,)
    )
    from cargar import enriquecer_venta  # import tardío: evita el ciclo cargar<->nucleo

    enriquecidas = enriquecer_venta(filas_venta, filas_mapa)
    uids = asignar_venta_uids(filas_venta)

    producto_por_key = {r["producto_key"]: r["id"] for r in _fetchall_dict(
        cur, "SELECT id, producto_key FROM core.producto WHERE tenant_id = %s", (tenant_id,))}
    cuenta_por_alias = {r["cuenta_alias"]: r["id"] for r in _fetchall_dict(
        cur, "SELECT id, cuenta_alias FROM core.cuenta WHERE tenant_id = %s", (tenant_id,))}
    conjunto_por_key = {(r["producto_id"], r["conjunto_meta"]): r["id"] for r in _fetchall_dict(
        cur, "SELECT id, producto_id, conjunto_meta FROM core.conjunto WHERE tenant_id = %s",
        (tenant_id,))}
    hist_por_alias = {(r["producto_key"], r["alias_nombre"]): r["nombre_canonico"]
                      for r in _fetchall_dict(
        cur, "SELECT producto_key, alias_nombre, nombre_canonico FROM core.conjunto_nombre_hist "
             "WHERE tenant_id = %s", (tenant_id,))}
    anuncio_por_key = {
        (r["producto_key"], r["cuenta_alias"], r["conjunto_nombre"], r["anuncio_nombre"]): r["id"]
        for r in _fetchall_dict(
            cur, "SELECT id, producto_key, cuenta_alias, conjunto_nombre, anuncio_nombre "
                 "FROM core.anuncio WHERE tenant_id = %s", (tenant_id,))}

    def _num(v):
        try:
            return float(v) if v not in (None, "") else None
        except (TypeError, ValueError):
            return None

    def _int(v):
        try:
            return int(float(v)) if v not in (None, "") else None
        except (TypeError, ValueError):
            return None

    filas_out = []
    sin_producto = sin_conjunto = sin_anuncio = 0
    for fila, uid, (resuelto, metodo), raw_id in zip(filas_venta, uids, enriquecidas, ids_raw):
        pkey = (fila.get("producto_key") or "").strip()
        pid = producto_por_key.get(pkey)
        sin_producto += 1 if pkey and not pid else 0
        cuenta_alias = (fila.get("cuenta_alias") or "").strip()
        cid = cuenta_por_alias.get(cuenta_alias)
        conjunto_nombre = (fila.get("conjunto") or "").strip()
        canonico = hist_por_alias.get((pkey, conjunto_nombre), conjunto_nombre)
        coid = conjunto_por_key.get((pid, canonico))
        sin_conjunto += 1 if conjunto_nombre and not coid else 0
        anuncio_nombre = (fila.get("anuncio") or "").strip()
        anid = anuncio_por_key.get((pkey, cuenta_alias, canonico, anuncio_nombre))
        sin_anuncio += 1 if anuncio_nombre and not anid else 0
        filas_out.append((
            tenant_id, pid, pkey, fila.get("producto"), cid, cuenta_alias,
            fila.get("cuenta_id"), coid, conjunto_nombre, anid, anuncio_nombre,
            _fecha_valida(fila.get("ventana_ini")), _fecha_valida(fila.get("ventana_fin")),
            _int(fila.get("dias")), fila.get("rol_ventana"), fila.get("campana"),
            _int(fila.get("mensajes")), _int(fila.get("clicks")), _int(fila.get("impresiones")),
            _num(fila.get("spend_usd")), _int(fila.get("ventas")), _num(fila.get("total_q")),
            fila.get("moneda_origen"), fila.get("fuente"), fila.get("ad_id"), resuelto, metodo,
            uid, raw_id,
        ))

    if filas_out:
        cur.executemany(
            """
            INSERT INTO core.venta (
                tenant_id, producto_id, producto_key, producto_nombre, cuenta_id, cuenta_alias,
                cuenta_id_meta, conjunto_id, conjunto_nombre, anuncio_id, anuncio_nombre,
                ventana_ini, ventana_fin, dias, rol_ventana, campana, mensajes, clicks,
                impresiones, spend_usd, ventas, total_q, moneda_origen, fuente, ad_id,
                ad_id_resuelto, metodo_atribucion, venta_uid, raw_id
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                      %s,%s,%s,%s)
            """,
            filas_out,
        )

    reporte["fk_sin_resolver"]["venta.producto_id"] = sin_producto
    reporte["fk_sin_resolver"]["venta.conjunto_id"] = sin_conjunto
    reporte["fk_sin_resolver"]["venta.anuncio_id"] = sin_anuncio

    # decision (snapshot de raw.decisiones_json, si existe) ---------------------------------------
    cur.execute(
        "SELECT contenido FROM raw.decisiones_json WHERE tenant_id = %s ORDER BY id DESC LIMIT 1",
        (tenant_id,),
    )
    fila_decision = cur.fetchone()
    if fila_decision and fila_decision[0]:
        import json
        payload = json.loads(fila_decision[0])
        cur.execute(
            "INSERT INTO core.decision (tenant_id, fecha, payload) VALUES (%s, %s, %s)",
            (tenant_id, payload.get("generado"), json.dumps(payload, ensure_ascii=False)),
        )

    # ── reconciliación ──────────────────────────────────────────────────────────────────────
    for tabla in CORE_TABLES_EN_ORDEN:
        cur.execute("SELECT count(*) FROM core.%s WHERE tenant_id = %%s" % tabla, (tenant_id,))
        reporte["tablas"][tabla] = cur.fetchone()[0]

    for fk_tabla, fk_col in (
        ("conjunto", "producto_id"), ("conjunto", "angulo_id"), ("conjunto", "cuenta_id"),
        ("entrega_anuncio_dia", "conjunto_id"), ("entrega_anuncio_dia", "anuncio_id"),
        ("entrega_conjunto_dia", "conjunto_id"), ("anuncio", "conjunto_id"),
        ("creativo", "producto_id"), ("banda", "conjunto_id"),
    ):
        cur.execute(
            "SELECT count(*) FROM core.%s WHERE tenant_id = %%s AND %s IS NULL"
            % (fk_tabla, fk_col), (tenant_id,),
        )
        reporte["fk_sin_resolver"]["%s.%s" % (fk_tabla, fk_col)] = cur.fetchone()[0]

    for raw_tabla, core_tabla in (
        ("venta", "venta"), ("entrega_anuncio_dia", "entrega_anuncio_dia"),
        ("entrega_conjunto_dia", "entrega_conjunto_dia"),
    ):
        cur.execute("SELECT count(*) FROM raw.%s WHERE tenant_id = %%s" % raw_tabla, (tenant_id,))
        n_raw = cur.fetchone()[0]
        n_core = reporte["tablas"][core_tabla]
        reporte["conservacion"][core_tabla] = {"raw": n_raw, "core": n_core, "igual": n_raw == n_core}

    return reporte


def _fecha_valida(v):
    import datetime
    v = (v or "").strip()
    if not v:
        return None
    try:
        return datetime.date.fromisoformat(v)
    except ValueError:
        return None
