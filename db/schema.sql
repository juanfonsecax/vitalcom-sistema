-- schema.sql — generado por db/tables.py (2026-10-15). DDL idempotente.
-- schema `raw`: espejo verbatim de cada CSV de PRODUCTOS/, más tenant_id (single
-- tenant 'vitalcom') e id. schema `core`: modelo normalizado/tipado construido A
-- PARTIR de `raw` por db/nucleo.py. Ver tables.py y nucleo.py para el porqué.

-- Migración única T5b: si esta base todavía tiene el `core` de T5 (el espejo
-- verbatim original, antes de que existiera un `raw`), renombrarlo a `raw` en vez
-- de perder su historia/ids. Sin efecto en una base que ya tiene `raw` (incluida
-- una base nueva, donde ninguno de los dos existe todavía).
DO $mig$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_namespace WHERE nspname = 'core')
     AND NOT EXISTS (SELECT 1 FROM pg_namespace WHERE nspname = 'raw') THEN
    EXECUTE 'ALTER SCHEMA core RENAME TO raw';
    -- el `core` de T5 tenía 2 columnas de enriquecimiento en `venta` que `raw`
    -- (verbatim puro, T5b) no debe tener -- ese enriquecimiento ahora vive solo
    -- en el `core` normalizado nuevo (ver nucleo.py).
    EXECUTE 'ALTER TABLE raw.venta DROP COLUMN IF EXISTS ad_id_resuelto';
    EXECUTE 'ALTER TABLE raw.venta DROP COLUMN IF EXISTS metodo_atribucion';
  END IF;
END $mig$;

CREATE SCHEMA IF NOT EXISTS raw;

CREATE TABLE IF NOT EXISTS raw.raw_import (
    id BIGSERIAL PRIMARY KEY,
    tenant_id TEXT NOT NULL DEFAULT 'vitalcom',
    archivo TEXT NOT NULL,
    sha256 TEXT,
    filas INTEGER NOT NULL DEFAULT 0,
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS raw.decisiones_json (
    id BIGSERIAL PRIMARY KEY,
    tenant_id TEXT NOT NULL DEFAULT 'vitalcom',
    contenido TEXT NOT NULL,
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- producto <- PRODUCTOS/_DIM_PRODUCTOS.csv
CREATE TABLE IF NOT EXISTS raw.producto (
    id BIGSERIAL PRIMARY KEY,
    tenant_id TEXT NOT NULL DEFAULT 'vitalcom',
    producto_key TEXT,
    nombre_display TEXT,
    slug_carpeta TEXT,
    estado TEXT,
    fase TEXT,
    cuenta_alias TEXT,
    cuenta_id TEXT,
    page_id TEXT,
    moneda TEXT,
    tasa TEXT,
    costo_q TEXT,
    fila_costeo_q TEXT,
    precio_base_q TEXT,
    cpa_base_q TEXT,
    cpa_be_q TEXT,
    cpa_be_anterior_q TEXT,
    notas TEXT,
    carpeta_videos TEXT,
    carpeta_transcripciones TEXT,
    carpeta_media TEXT,
    carpetas_extra TEXT,
    clave_campana TEXT,
    campaign_id TEXT,
    mercado TEXT,
    registro_sanitario_estado TEXT,
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
ALTER TABLE raw.producto ADD COLUMN IF NOT EXISTS producto_key TEXT;
ALTER TABLE raw.producto ADD COLUMN IF NOT EXISTS nombre_display TEXT;
ALTER TABLE raw.producto ADD COLUMN IF NOT EXISTS slug_carpeta TEXT;
ALTER TABLE raw.producto ADD COLUMN IF NOT EXISTS estado TEXT;
ALTER TABLE raw.producto ADD COLUMN IF NOT EXISTS fase TEXT;
ALTER TABLE raw.producto ADD COLUMN IF NOT EXISTS cuenta_alias TEXT;
ALTER TABLE raw.producto ADD COLUMN IF NOT EXISTS cuenta_id TEXT;
ALTER TABLE raw.producto ADD COLUMN IF NOT EXISTS page_id TEXT;
ALTER TABLE raw.producto ADD COLUMN IF NOT EXISTS moneda TEXT;
ALTER TABLE raw.producto ADD COLUMN IF NOT EXISTS tasa TEXT;
ALTER TABLE raw.producto ADD COLUMN IF NOT EXISTS costo_q TEXT;
ALTER TABLE raw.producto ADD COLUMN IF NOT EXISTS fila_costeo_q TEXT;
ALTER TABLE raw.producto ADD COLUMN IF NOT EXISTS precio_base_q TEXT;
ALTER TABLE raw.producto ADD COLUMN IF NOT EXISTS cpa_base_q TEXT;
ALTER TABLE raw.producto ADD COLUMN IF NOT EXISTS cpa_be_q TEXT;
ALTER TABLE raw.producto ADD COLUMN IF NOT EXISTS cpa_be_anterior_q TEXT;
ALTER TABLE raw.producto ADD COLUMN IF NOT EXISTS notas TEXT;
ALTER TABLE raw.producto ADD COLUMN IF NOT EXISTS carpeta_videos TEXT;
ALTER TABLE raw.producto ADD COLUMN IF NOT EXISTS carpeta_transcripciones TEXT;
ALTER TABLE raw.producto ADD COLUMN IF NOT EXISTS carpeta_media TEXT;
ALTER TABLE raw.producto ADD COLUMN IF NOT EXISTS carpetas_extra TEXT;
ALTER TABLE raw.producto ADD COLUMN IF NOT EXISTS clave_campana TEXT;
ALTER TABLE raw.producto ADD COLUMN IF NOT EXISTS campaign_id TEXT;
ALTER TABLE raw.producto ADD COLUMN IF NOT EXISTS mercado TEXT;
ALTER TABLE raw.producto ADD COLUMN IF NOT EXISTS registro_sanitario_estado TEXT;

-- costeo <- PRODUCTOS/_DIM_COSTEO.csv
CREATE TABLE IF NOT EXISTS raw.costeo (
    id BIGSERIAL PRIMARY KEY,
    tenant_id TEXT NOT NULL DEFAULT 'vitalcom',
    costo_producto TEXT,
    valor_envio TEXT,
    costos_admin TEXT,
    costo_devolucion TEXT,
    total_gastos TEXT,
    cpa_objetivo TEXT,
    cpa_minimo TEXT,
    cpa_real_calc TEXT,
    suma_costos TEXT,
    utilidad TEXT,
    precio_sugerido TEXT,
    precio_establecido TEXT,
    cpa_base TEXT,
    utilidad_esperada TEXT,
    cpa_break_even TEXT,
    pct_ingreso TEXT,
    pct_ingreso_utilidad TEXT,
    cpa_base_usd TEXT,
    precio_2u TEXT,
    precio_3u TEXT,
    origen_escalera TEXT,
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
ALTER TABLE raw.costeo ADD COLUMN IF NOT EXISTS costo_producto TEXT;
ALTER TABLE raw.costeo ADD COLUMN IF NOT EXISTS valor_envio TEXT;
ALTER TABLE raw.costeo ADD COLUMN IF NOT EXISTS costos_admin TEXT;
ALTER TABLE raw.costeo ADD COLUMN IF NOT EXISTS costo_devolucion TEXT;
ALTER TABLE raw.costeo ADD COLUMN IF NOT EXISTS total_gastos TEXT;
ALTER TABLE raw.costeo ADD COLUMN IF NOT EXISTS cpa_objetivo TEXT;
ALTER TABLE raw.costeo ADD COLUMN IF NOT EXISTS cpa_minimo TEXT;
ALTER TABLE raw.costeo ADD COLUMN IF NOT EXISTS cpa_real_calc TEXT;
ALTER TABLE raw.costeo ADD COLUMN IF NOT EXISTS suma_costos TEXT;
ALTER TABLE raw.costeo ADD COLUMN IF NOT EXISTS utilidad TEXT;
ALTER TABLE raw.costeo ADD COLUMN IF NOT EXISTS precio_sugerido TEXT;
ALTER TABLE raw.costeo ADD COLUMN IF NOT EXISTS precio_establecido TEXT;
ALTER TABLE raw.costeo ADD COLUMN IF NOT EXISTS cpa_base TEXT;
ALTER TABLE raw.costeo ADD COLUMN IF NOT EXISTS utilidad_esperada TEXT;
ALTER TABLE raw.costeo ADD COLUMN IF NOT EXISTS cpa_break_even TEXT;
ALTER TABLE raw.costeo ADD COLUMN IF NOT EXISTS pct_ingreso TEXT;
ALTER TABLE raw.costeo ADD COLUMN IF NOT EXISTS pct_ingreso_utilidad TEXT;
ALTER TABLE raw.costeo ADD COLUMN IF NOT EXISTS cpa_base_usd TEXT;
ALTER TABLE raw.costeo ADD COLUMN IF NOT EXISTS precio_2u TEXT;
ALTER TABLE raw.costeo ADD COLUMN IF NOT EXISTS precio_3u TEXT;
ALTER TABLE raw.costeo ADD COLUMN IF NOT EXISTS origen_escalera TEXT;

-- conjunto <- PRODUCTOS/_DIM_CONJUNTOS.csv
CREATE TABLE IF NOT EXISTS raw.conjunto (
    id BIGSERIAL PRIMARY KEY,
    tenant_id TEXT NOT NULL DEFAULT 'vitalcom',
    producto_key TEXT,
    conjunto_meta TEXT,
    cuenta_alias TEXT,
    campana_clave TEXT,
    fase TEXT,
    angulo_key TEXT,
    angulo_nombre TEXT,
    avatar TEXT,
    dolor_nucleo TEXT,
    emocion_dominante TEXT,
    avatar_edad TEXT,
    avatar_genero TEXT,
    formato TEXT,
    concepto_key TEXT,
    tipo_hook TEXT,
    nivel_conciencia TEXT,
    rol_embudo TEXT,
    rol_embudo_origen TEXT,
    lleva_precio TEXT,
    creativo_id TEXT,
    origen_angulo TEXT,
    estado TEXT,
    verificado_en_csv TEXT,
    fecha_alta TEXT,
    notas TEXT,
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
ALTER TABLE raw.conjunto ADD COLUMN IF NOT EXISTS producto_key TEXT;
ALTER TABLE raw.conjunto ADD COLUMN IF NOT EXISTS conjunto_meta TEXT;
ALTER TABLE raw.conjunto ADD COLUMN IF NOT EXISTS cuenta_alias TEXT;
ALTER TABLE raw.conjunto ADD COLUMN IF NOT EXISTS campana_clave TEXT;
ALTER TABLE raw.conjunto ADD COLUMN IF NOT EXISTS fase TEXT;
ALTER TABLE raw.conjunto ADD COLUMN IF NOT EXISTS angulo_key TEXT;
ALTER TABLE raw.conjunto ADD COLUMN IF NOT EXISTS angulo_nombre TEXT;
ALTER TABLE raw.conjunto ADD COLUMN IF NOT EXISTS avatar TEXT;
ALTER TABLE raw.conjunto ADD COLUMN IF NOT EXISTS dolor_nucleo TEXT;
ALTER TABLE raw.conjunto ADD COLUMN IF NOT EXISTS emocion_dominante TEXT;
ALTER TABLE raw.conjunto ADD COLUMN IF NOT EXISTS avatar_edad TEXT;
ALTER TABLE raw.conjunto ADD COLUMN IF NOT EXISTS avatar_genero TEXT;
ALTER TABLE raw.conjunto ADD COLUMN IF NOT EXISTS formato TEXT;
ALTER TABLE raw.conjunto ADD COLUMN IF NOT EXISTS concepto_key TEXT;
ALTER TABLE raw.conjunto ADD COLUMN IF NOT EXISTS tipo_hook TEXT;
ALTER TABLE raw.conjunto ADD COLUMN IF NOT EXISTS nivel_conciencia TEXT;
ALTER TABLE raw.conjunto ADD COLUMN IF NOT EXISTS rol_embudo TEXT;
ALTER TABLE raw.conjunto ADD COLUMN IF NOT EXISTS rol_embudo_origen TEXT;
ALTER TABLE raw.conjunto ADD COLUMN IF NOT EXISTS lleva_precio TEXT;
ALTER TABLE raw.conjunto ADD COLUMN IF NOT EXISTS creativo_id TEXT;
ALTER TABLE raw.conjunto ADD COLUMN IF NOT EXISTS origen_angulo TEXT;
ALTER TABLE raw.conjunto ADD COLUMN IF NOT EXISTS estado TEXT;
ALTER TABLE raw.conjunto ADD COLUMN IF NOT EXISTS verificado_en_csv TEXT;
ALTER TABLE raw.conjunto ADD COLUMN IF NOT EXISTS fecha_alta TEXT;
ALTER TABLE raw.conjunto ADD COLUMN IF NOT EXISTS notas TEXT;

-- creativo <- PRODUCTOS/_DIM_CREATIVOS.csv
CREATE TABLE IF NOT EXISTS raw.creativo (
    id BIGSERIAL PRIMARY KEY,
    tenant_id TEXT NOT NULL DEFAULT 'vitalcom',
    producto_key TEXT,
    creativo_id TEXT,
    archivo TEXT,
    cuenta_destino TEXT,
    angulo_key TEXT,
    concepto_key TEXT,
    bloque_concepto TEXT,
    variante TEXT,
    canonico_id TEXT,
    rol_embudo TEXT,
    densidad TEXT,
    estetica TEXT,
    id_tanda TEXT,
    brazo TEXT,
    estado_entrega TEXT,
    ad_id TEXT,
    formato TEXT,
    estilo_visual TEXT,
    tipo_hook TEXT,
    lleva_precio TEXT,
    tiene_testimonio TEXT,
    tipo_sello TEXT,
    color_dominante TEXT,
    avatar_edad TEXT,
    avatar_genero TEXT,
    badge_regulatorio TEXT,
    fecha_alta TEXT,
    estado TEXT,
    notas TEXT,
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
ALTER TABLE raw.creativo ADD COLUMN IF NOT EXISTS producto_key TEXT;
ALTER TABLE raw.creativo ADD COLUMN IF NOT EXISTS creativo_id TEXT;
ALTER TABLE raw.creativo ADD COLUMN IF NOT EXISTS archivo TEXT;
ALTER TABLE raw.creativo ADD COLUMN IF NOT EXISTS cuenta_destino TEXT;
ALTER TABLE raw.creativo ADD COLUMN IF NOT EXISTS angulo_key TEXT;
ALTER TABLE raw.creativo ADD COLUMN IF NOT EXISTS concepto_key TEXT;
ALTER TABLE raw.creativo ADD COLUMN IF NOT EXISTS bloque_concepto TEXT;
ALTER TABLE raw.creativo ADD COLUMN IF NOT EXISTS variante TEXT;
ALTER TABLE raw.creativo ADD COLUMN IF NOT EXISTS canonico_id TEXT;
ALTER TABLE raw.creativo ADD COLUMN IF NOT EXISTS rol_embudo TEXT;
ALTER TABLE raw.creativo ADD COLUMN IF NOT EXISTS densidad TEXT;
ALTER TABLE raw.creativo ADD COLUMN IF NOT EXISTS estetica TEXT;
ALTER TABLE raw.creativo ADD COLUMN IF NOT EXISTS id_tanda TEXT;
ALTER TABLE raw.creativo ADD COLUMN IF NOT EXISTS brazo TEXT;
ALTER TABLE raw.creativo ADD COLUMN IF NOT EXISTS estado_entrega TEXT;
ALTER TABLE raw.creativo ADD COLUMN IF NOT EXISTS ad_id TEXT;
ALTER TABLE raw.creativo ADD COLUMN IF NOT EXISTS formato TEXT;
ALTER TABLE raw.creativo ADD COLUMN IF NOT EXISTS estilo_visual TEXT;
ALTER TABLE raw.creativo ADD COLUMN IF NOT EXISTS tipo_hook TEXT;
ALTER TABLE raw.creativo ADD COLUMN IF NOT EXISTS lleva_precio TEXT;
ALTER TABLE raw.creativo ADD COLUMN IF NOT EXISTS tiene_testimonio TEXT;
ALTER TABLE raw.creativo ADD COLUMN IF NOT EXISTS tipo_sello TEXT;
ALTER TABLE raw.creativo ADD COLUMN IF NOT EXISTS color_dominante TEXT;
ALTER TABLE raw.creativo ADD COLUMN IF NOT EXISTS avatar_edad TEXT;
ALTER TABLE raw.creativo ADD COLUMN IF NOT EXISTS avatar_genero TEXT;
ALTER TABLE raw.creativo ADD COLUMN IF NOT EXISTS badge_regulatorio TEXT;
ALTER TABLE raw.creativo ADD COLUMN IF NOT EXISTS fecha_alta TEXT;
ALTER TABLE raw.creativo ADD COLUMN IF NOT EXISTS estado TEXT;
ALTER TABLE raw.creativo ADD COLUMN IF NOT EXISTS notas TEXT;

-- voz_cliente <- PRODUCTOS/_VOZ_CLIENTE.csv
CREATE TABLE IF NOT EXISTS raw.voz_cliente (
    id BIGSERIAL PRIMARY KEY,
    tenant_id TEXT NOT NULL DEFAULT 'vitalcom',
    producto_key TEXT,
    voz_id TEXT,
    variable TEXT,
    cita_textual TEXT,
    url TEXT,
    fuente_tipo TEXT,
    fecha_captura TEXT,
    pais TEXT,
    idioma TEXT,
    nivel_conciencia TEXT,
    embudo TEXT,
    angulo_key TEXT,
    estado TEXT,
    verificado_el TEXT,
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
ALTER TABLE raw.voz_cliente ADD COLUMN IF NOT EXISTS producto_key TEXT;
ALTER TABLE raw.voz_cliente ADD COLUMN IF NOT EXISTS voz_id TEXT;
ALTER TABLE raw.voz_cliente ADD COLUMN IF NOT EXISTS variable TEXT;
ALTER TABLE raw.voz_cliente ADD COLUMN IF NOT EXISTS cita_textual TEXT;
ALTER TABLE raw.voz_cliente ADD COLUMN IF NOT EXISTS url TEXT;
ALTER TABLE raw.voz_cliente ADD COLUMN IF NOT EXISTS fuente_tipo TEXT;
ALTER TABLE raw.voz_cliente ADD COLUMN IF NOT EXISTS fecha_captura TEXT;
ALTER TABLE raw.voz_cliente ADD COLUMN IF NOT EXISTS pais TEXT;
ALTER TABLE raw.voz_cliente ADD COLUMN IF NOT EXISTS idioma TEXT;
ALTER TABLE raw.voz_cliente ADD COLUMN IF NOT EXISTS nivel_conciencia TEXT;
ALTER TABLE raw.voz_cliente ADD COLUMN IF NOT EXISTS embudo TEXT;
ALTER TABLE raw.voz_cliente ADD COLUMN IF NOT EXISTS angulo_key TEXT;
ALTER TABLE raw.voz_cliente ADD COLUMN IF NOT EXISTS estado TEXT;
ALTER TABLE raw.voz_cliente ADD COLUMN IF NOT EXISTS verificado_el TEXT;

-- dim_bandas <- PRODUCTOS/_DIM_BANDAS.csv
CREATE TABLE IF NOT EXISTS raw.dim_bandas (
    id BIGSERIAL PRIMARY KEY,
    tenant_id TEXT NOT NULL DEFAULT 'vitalcom',
    cuenta_alias TEXT,
    conjunto_meta TEXT,
    producto_key TEXT,
    angulo_key TEXT,
    banda_configurada TEXT,
    avatar_edad_doctrina TEXT,
    coincide TEXT,
    desde TEXT,
    hasta TEXT,
    fuente TEXT,
    notas TEXT,
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
ALTER TABLE raw.dim_bandas ADD COLUMN IF NOT EXISTS cuenta_alias TEXT;
ALTER TABLE raw.dim_bandas ADD COLUMN IF NOT EXISTS conjunto_meta TEXT;
ALTER TABLE raw.dim_bandas ADD COLUMN IF NOT EXISTS producto_key TEXT;
ALTER TABLE raw.dim_bandas ADD COLUMN IF NOT EXISTS angulo_key TEXT;
ALTER TABLE raw.dim_bandas ADD COLUMN IF NOT EXISTS banda_configurada TEXT;
ALTER TABLE raw.dim_bandas ADD COLUMN IF NOT EXISTS avatar_edad_doctrina TEXT;
ALTER TABLE raw.dim_bandas ADD COLUMN IF NOT EXISTS coincide TEXT;
ALTER TABLE raw.dim_bandas ADD COLUMN IF NOT EXISTS desde TEXT;
ALTER TABLE raw.dim_bandas ADD COLUMN IF NOT EXISTS hasta TEXT;
ALTER TABLE raw.dim_bandas ADD COLUMN IF NOT EXISTS fuente TEXT;
ALTER TABLE raw.dim_bandas ADD COLUMN IF NOT EXISTS notas TEXT;

-- conjunto_nombre_hist <- PRODUCTOS/_ALIAS_CONJUNTOS.csv
CREATE TABLE IF NOT EXISTS raw.conjunto_nombre_hist (
    id BIGSERIAL PRIMARY KEY,
    tenant_id TEXT NOT NULL DEFAULT 'vitalcom',
    nombre_viejo TEXT,
    nombre_nuevo TEXT,
    cuenta_alias TEXT,
    producto_key TEXT,
    desde TEXT,
    motivo TEXT,
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
ALTER TABLE raw.conjunto_nombre_hist ADD COLUMN IF NOT EXISTS nombre_viejo TEXT;
ALTER TABLE raw.conjunto_nombre_hist ADD COLUMN IF NOT EXISTS nombre_nuevo TEXT;
ALTER TABLE raw.conjunto_nombre_hist ADD COLUMN IF NOT EXISTS cuenta_alias TEXT;
ALTER TABLE raw.conjunto_nombre_hist ADD COLUMN IF NOT EXISTS producto_key TEXT;
ALTER TABLE raw.conjunto_nombre_hist ADD COLUMN IF NOT EXISTS desde TEXT;
ALTER TABLE raw.conjunto_nombre_hist ADD COLUMN IF NOT EXISTS motivo TEXT;

-- dim_bm <- PRODUCTOS/_DIM_BM.csv
CREATE TABLE IF NOT EXISTS raw.dim_bm (
    id BIGSERIAL PRIMARY KEY,
    tenant_id TEXT NOT NULL DEFAULT 'vitalcom',
    bm_id TEXT,
    bm_nombre TEXT,
    cuentas_ids TEXT,
    cuentas_alias TEXT,
    moneda TEXT,
    mcp TEXT,
    estado TEXT,
    notas TEXT,
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
ALTER TABLE raw.dim_bm ADD COLUMN IF NOT EXISTS bm_id TEXT;
ALTER TABLE raw.dim_bm ADD COLUMN IF NOT EXISTS bm_nombre TEXT;
ALTER TABLE raw.dim_bm ADD COLUMN IF NOT EXISTS cuentas_ids TEXT;
ALTER TABLE raw.dim_bm ADD COLUMN IF NOT EXISTS cuentas_alias TEXT;
ALTER TABLE raw.dim_bm ADD COLUMN IF NOT EXISTS moneda TEXT;
ALTER TABLE raw.dim_bm ADD COLUMN IF NOT EXISTS mcp TEXT;
ALTER TABLE raw.dim_bm ADD COLUMN IF NOT EXISTS estado TEXT;
ALTER TABLE raw.dim_bm ADD COLUMN IF NOT EXISTS notas TEXT;

-- dim_cuentas <- PRODUCTOS/_DIM_CUENTAS.csv
CREATE TABLE IF NOT EXISTS raw.dim_cuentas (
    id BIGSERIAL PRIMARY KEY,
    tenant_id TEXT NOT NULL DEFAULT 'vitalcom',
    cuenta_alias TEXT,
    cuenta_id TEXT,
    negocio_id TEXT,
    negocio TEXT,
    moneda TEXT,
    min_daily_budget_cents TEXT,
    mcp_habilitado TEXT,
    consultable TEXT,
    tiene_metodo_pago TEXT,
    sube_media_local TEXT,
    estado_cuenta TEXT,
    verificado_el TEXT,
    fuente TEXT,
    notas TEXT,
    mercado TEXT,
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
ALTER TABLE raw.dim_cuentas ADD COLUMN IF NOT EXISTS cuenta_alias TEXT;
ALTER TABLE raw.dim_cuentas ADD COLUMN IF NOT EXISTS cuenta_id TEXT;
ALTER TABLE raw.dim_cuentas ADD COLUMN IF NOT EXISTS negocio_id TEXT;
ALTER TABLE raw.dim_cuentas ADD COLUMN IF NOT EXISTS negocio TEXT;
ALTER TABLE raw.dim_cuentas ADD COLUMN IF NOT EXISTS moneda TEXT;
ALTER TABLE raw.dim_cuentas ADD COLUMN IF NOT EXISTS min_daily_budget_cents TEXT;
ALTER TABLE raw.dim_cuentas ADD COLUMN IF NOT EXISTS mcp_habilitado TEXT;
ALTER TABLE raw.dim_cuentas ADD COLUMN IF NOT EXISTS consultable TEXT;
ALTER TABLE raw.dim_cuentas ADD COLUMN IF NOT EXISTS tiene_metodo_pago TEXT;
ALTER TABLE raw.dim_cuentas ADD COLUMN IF NOT EXISTS sube_media_local TEXT;
ALTER TABLE raw.dim_cuentas ADD COLUMN IF NOT EXISTS estado_cuenta TEXT;
ALTER TABLE raw.dim_cuentas ADD COLUMN IF NOT EXISTS verificado_el TEXT;
ALTER TABLE raw.dim_cuentas ADD COLUMN IF NOT EXISTS fuente TEXT;
ALTER TABLE raw.dim_cuentas ADD COLUMN IF NOT EXISTS notas TEXT;
ALTER TABLE raw.dim_cuentas ADD COLUMN IF NOT EXISTS mercado TEXT;

-- dim_envase <- PRODUCTOS/_DIM_ENVASE.csv
CREATE TABLE IF NOT EXISTS raw.dim_envase (
    id BIGSERIAL PRIMARY KEY,
    tenant_id TEXT NOT NULL DEFAULT 'vitalcom',
    producto_key TEXT,
    packshot TEXT,
    color_envase TEXT,
    color_hex TEXT,
    marca_impresa TEXT,
    formato_envase TEXT,
    verificado_el TEXT,
    fuente TEXT,
    notas TEXT,
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
ALTER TABLE raw.dim_envase ADD COLUMN IF NOT EXISTS producto_key TEXT;
ALTER TABLE raw.dim_envase ADD COLUMN IF NOT EXISTS packshot TEXT;
ALTER TABLE raw.dim_envase ADD COLUMN IF NOT EXISTS color_envase TEXT;
ALTER TABLE raw.dim_envase ADD COLUMN IF NOT EXISTS color_hex TEXT;
ALTER TABLE raw.dim_envase ADD COLUMN IF NOT EXISTS marca_impresa TEXT;
ALTER TABLE raw.dim_envase ADD COLUMN IF NOT EXISTS formato_envase TEXT;
ALTER TABLE raw.dim_envase ADD COLUMN IF NOT EXISTS verificado_el TEXT;
ALTER TABLE raw.dim_envase ADD COLUMN IF NOT EXISTS fuente TEXT;
ALTER TABLE raw.dim_envase ADD COLUMN IF NOT EXISTS notas TEXT;

-- dim_fanpages <- PRODUCTOS/_DIM_FANPAGES.csv
CREATE TABLE IF NOT EXISTS raw.dim_fanpages (
    id BIGSERIAL PRIMARY KEY,
    tenant_id TEXT NOT NULL DEFAULT 'vitalcom',
    pagina_num TEXT,
    pagina_nombre TEXT,
    identidad TEXT,
    rol TEXT,
    tono TEXT,
    logica TEXT,
    edad_orientacion TEXT,
    page_id TEXT,
    productos_nicho TEXT,
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
ALTER TABLE raw.dim_fanpages ADD COLUMN IF NOT EXISTS pagina_num TEXT;
ALTER TABLE raw.dim_fanpages ADD COLUMN IF NOT EXISTS pagina_nombre TEXT;
ALTER TABLE raw.dim_fanpages ADD COLUMN IF NOT EXISTS identidad TEXT;
ALTER TABLE raw.dim_fanpages ADD COLUMN IF NOT EXISTS rol TEXT;
ALTER TABLE raw.dim_fanpages ADD COLUMN IF NOT EXISTS tono TEXT;
ALTER TABLE raw.dim_fanpages ADD COLUMN IF NOT EXISTS logica TEXT;
ALTER TABLE raw.dim_fanpages ADD COLUMN IF NOT EXISTS edad_orientacion TEXT;
ALTER TABLE raw.dim_fanpages ADD COLUMN IF NOT EXISTS page_id TEXT;
ALTER TABLE raw.dim_fanpages ADD COLUMN IF NOT EXISTS productos_nicho TEXT;

-- dim_flujo_bot <- PRODUCTOS/_DIM_FLUJO_BOT.csv
CREATE TABLE IF NOT EXISTS raw.dim_flujo_bot (
    id BIGSERIAL PRIMARY KEY,
    tenant_id TEXT NOT NULL DEFAULT 'vitalcom',
    producto_key TEXT,
    mercado TEXT,
    nombre_tienda TEXT,
    nombre_asesor TEXT,
    producto_display TEXT,
    envase TEXT,
    duracion_1u TEXT,
    dias_resultado TEXT,
    mecanismo_1 TEXT,
    mecanismo_2 TEXT,
    prueba_social TEXT,
    garantia_texto TEXT,
    dolor_angulo TEXT,
    solucion_fallida TEXT,
    recaida TEXT,
    sintoma_superficial TEXT,
    consecuencia_emocional TEXT,
    area_cuidado TEXT,
    verbo_tratar TEXT,
    resultado_sostenido TEXT,
    razon_tier_alto TEXT,
    n_infografias TEXT,
    n_testimonios TEXT,
    fuente_testimonios TEXT,
    vigente_desde TEXT,
    notas TEXT,
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
ALTER TABLE raw.dim_flujo_bot ADD COLUMN IF NOT EXISTS producto_key TEXT;
ALTER TABLE raw.dim_flujo_bot ADD COLUMN IF NOT EXISTS mercado TEXT;
ALTER TABLE raw.dim_flujo_bot ADD COLUMN IF NOT EXISTS nombre_tienda TEXT;
ALTER TABLE raw.dim_flujo_bot ADD COLUMN IF NOT EXISTS nombre_asesor TEXT;
ALTER TABLE raw.dim_flujo_bot ADD COLUMN IF NOT EXISTS producto_display TEXT;
ALTER TABLE raw.dim_flujo_bot ADD COLUMN IF NOT EXISTS envase TEXT;
ALTER TABLE raw.dim_flujo_bot ADD COLUMN IF NOT EXISTS duracion_1u TEXT;
ALTER TABLE raw.dim_flujo_bot ADD COLUMN IF NOT EXISTS dias_resultado TEXT;
ALTER TABLE raw.dim_flujo_bot ADD COLUMN IF NOT EXISTS mecanismo_1 TEXT;
ALTER TABLE raw.dim_flujo_bot ADD COLUMN IF NOT EXISTS mecanismo_2 TEXT;
ALTER TABLE raw.dim_flujo_bot ADD COLUMN IF NOT EXISTS prueba_social TEXT;
ALTER TABLE raw.dim_flujo_bot ADD COLUMN IF NOT EXISTS garantia_texto TEXT;
ALTER TABLE raw.dim_flujo_bot ADD COLUMN IF NOT EXISTS dolor_angulo TEXT;
ALTER TABLE raw.dim_flujo_bot ADD COLUMN IF NOT EXISTS solucion_fallida TEXT;
ALTER TABLE raw.dim_flujo_bot ADD COLUMN IF NOT EXISTS recaida TEXT;
ALTER TABLE raw.dim_flujo_bot ADD COLUMN IF NOT EXISTS sintoma_superficial TEXT;
ALTER TABLE raw.dim_flujo_bot ADD COLUMN IF NOT EXISTS consecuencia_emocional TEXT;
ALTER TABLE raw.dim_flujo_bot ADD COLUMN IF NOT EXISTS area_cuidado TEXT;
ALTER TABLE raw.dim_flujo_bot ADD COLUMN IF NOT EXISTS verbo_tratar TEXT;
ALTER TABLE raw.dim_flujo_bot ADD COLUMN IF NOT EXISTS resultado_sostenido TEXT;
ALTER TABLE raw.dim_flujo_bot ADD COLUMN IF NOT EXISTS razon_tier_alto TEXT;
ALTER TABLE raw.dim_flujo_bot ADD COLUMN IF NOT EXISTS n_infografias TEXT;
ALTER TABLE raw.dim_flujo_bot ADD COLUMN IF NOT EXISTS n_testimonios TEXT;
ALTER TABLE raw.dim_flujo_bot ADD COLUMN IF NOT EXISTS fuente_testimonios TEXT;
ALTER TABLE raw.dim_flujo_bot ADD COLUMN IF NOT EXISTS vigente_desde TEXT;
ALTER TABLE raw.dim_flujo_bot ADD COLUMN IF NOT EXISTS notas TEXT;

-- dim_gastos <- PRODUCTOS/_DIM_GASTOS.csv
CREATE TABLE IF NOT EXISTS raw.dim_gastos (
    id BIGSERIAL PRIMARY KEY,
    tenant_id TEXT NOT NULL DEFAULT 'vitalcom',
    patron TEXT,
    clasificacion TEXT,
    categoria TEXT,
    confirmado_por TEXT,
    fecha TEXT,
    notas TEXT,
    mercado TEXT,
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
ALTER TABLE raw.dim_gastos ADD COLUMN IF NOT EXISTS patron TEXT;
ALTER TABLE raw.dim_gastos ADD COLUMN IF NOT EXISTS clasificacion TEXT;
ALTER TABLE raw.dim_gastos ADD COLUMN IF NOT EXISTS categoria TEXT;
ALTER TABLE raw.dim_gastos ADD COLUMN IF NOT EXISTS confirmado_por TEXT;
ALTER TABLE raw.dim_gastos ADD COLUMN IF NOT EXISTS fecha TEXT;
ALTER TABLE raw.dim_gastos ADD COLUMN IF NOT EXISTS notas TEXT;
ALTER TABLE raw.dim_gastos ADD COLUMN IF NOT EXISTS mercado TEXT;

-- dim_mercados <- PRODUCTOS/_DIM_MERCADOS.csv
CREATE TABLE IF NOT EXISTS raw.dim_mercados (
    id BIGSERIAL PRIMARY KEY,
    tenant_id TEXT NOT NULL DEFAULT 'vitalcom',
    mercado TEXT,
    pais TEXT,
    pais_cobertura TEXT,
    persona TEXT,
    registro_sanitario TEXT,
    moneda TEXT,
    simbolo TEXT,
    unidad_geo TEXT,
    unidad_local TEXT,
    transportadoras TEXT,
    dias_entrega TEXT,
    dias_espera_casa TEXT,
    vigente_desde TEXT,
    notas TEXT,
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
ALTER TABLE raw.dim_mercados ADD COLUMN IF NOT EXISTS mercado TEXT;
ALTER TABLE raw.dim_mercados ADD COLUMN IF NOT EXISTS pais TEXT;
ALTER TABLE raw.dim_mercados ADD COLUMN IF NOT EXISTS pais_cobertura TEXT;
ALTER TABLE raw.dim_mercados ADD COLUMN IF NOT EXISTS persona TEXT;
ALTER TABLE raw.dim_mercados ADD COLUMN IF NOT EXISTS registro_sanitario TEXT;
ALTER TABLE raw.dim_mercados ADD COLUMN IF NOT EXISTS moneda TEXT;
ALTER TABLE raw.dim_mercados ADD COLUMN IF NOT EXISTS simbolo TEXT;
ALTER TABLE raw.dim_mercados ADD COLUMN IF NOT EXISTS unidad_geo TEXT;
ALTER TABLE raw.dim_mercados ADD COLUMN IF NOT EXISTS unidad_local TEXT;
ALTER TABLE raw.dim_mercados ADD COLUMN IF NOT EXISTS transportadoras TEXT;
ALTER TABLE raw.dim_mercados ADD COLUMN IF NOT EXISTS dias_entrega TEXT;
ALTER TABLE raw.dim_mercados ADD COLUMN IF NOT EXISTS dias_espera_casa TEXT;
ALTER TABLE raw.dim_mercados ADD COLUMN IF NOT EXISTS vigente_desde TEXT;
ALTER TABLE raw.dim_mercados ADD COLUMN IF NOT EXISTS notas TEXT;

-- dim_precios <- PRODUCTOS/_DIM_PRECIOS.csv
CREATE TABLE IF NOT EXISTS raw.dim_precios (
    id BIGSERIAL PRIMARY KEY,
    tenant_id TEXT NOT NULL DEFAULT 'vitalcom',
    producto_key TEXT,
    unidades TEXT,
    etiqueta TEXT,
    precio_q TEXT,
    costo_proveedor_total_q TEXT,
    flete_q TEXT,
    flete_fuente TEXT,
    n_ordenes TEXT,
    estado TEXT,
    vigente_desde TEXT,
    notas TEXT,
    precio_antes_q TEXT,
    origen_ancla TEXT,
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
ALTER TABLE raw.dim_precios ADD COLUMN IF NOT EXISTS producto_key TEXT;
ALTER TABLE raw.dim_precios ADD COLUMN IF NOT EXISTS unidades TEXT;
ALTER TABLE raw.dim_precios ADD COLUMN IF NOT EXISTS etiqueta TEXT;
ALTER TABLE raw.dim_precios ADD COLUMN IF NOT EXISTS precio_q TEXT;
ALTER TABLE raw.dim_precios ADD COLUMN IF NOT EXISTS costo_proveedor_total_q TEXT;
ALTER TABLE raw.dim_precios ADD COLUMN IF NOT EXISTS flete_q TEXT;
ALTER TABLE raw.dim_precios ADD COLUMN IF NOT EXISTS flete_fuente TEXT;
ALTER TABLE raw.dim_precios ADD COLUMN IF NOT EXISTS n_ordenes TEXT;
ALTER TABLE raw.dim_precios ADD COLUMN IF NOT EXISTS estado TEXT;
ALTER TABLE raw.dim_precios ADD COLUMN IF NOT EXISTS vigente_desde TEXT;
ALTER TABLE raw.dim_precios ADD COLUMN IF NOT EXISTS notas TEXT;
ALTER TABLE raw.dim_precios ADD COLUMN IF NOT EXISTS precio_antes_q TEXT;
ALTER TABLE raw.dim_precios ADD COLUMN IF NOT EXISTS origen_ancla TEXT;

-- dim_tarjetas <- PRODUCTOS/_DIM_TARJETAS.csv
CREATE TABLE IF NOT EXISTS raw.dim_tarjetas (
    id BIGSERIAL PRIMARY KEY,
    tenant_id TEXT NOT NULL DEFAULT 'vitalcom',
    ultimos4 TEXT,
    marca TEXT,
    bm_nombre TEXT,
    cuentas_vistas TEXT,
    rol TEXT,
    cobros_ok TEXT,
    rechazos TEXT,
    pct_falla TEXT,
    veredicto TEXT,
    visto_desde TEXT,
    visto_hasta TEXT,
    estado TEXT,
    notas TEXT,
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
ALTER TABLE raw.dim_tarjetas ADD COLUMN IF NOT EXISTS ultimos4 TEXT;
ALTER TABLE raw.dim_tarjetas ADD COLUMN IF NOT EXISTS marca TEXT;
ALTER TABLE raw.dim_tarjetas ADD COLUMN IF NOT EXISTS bm_nombre TEXT;
ALTER TABLE raw.dim_tarjetas ADD COLUMN IF NOT EXISTS cuentas_vistas TEXT;
ALTER TABLE raw.dim_tarjetas ADD COLUMN IF NOT EXISTS rol TEXT;
ALTER TABLE raw.dim_tarjetas ADD COLUMN IF NOT EXISTS cobros_ok TEXT;
ALTER TABLE raw.dim_tarjetas ADD COLUMN IF NOT EXISTS rechazos TEXT;
ALTER TABLE raw.dim_tarjetas ADD COLUMN IF NOT EXISTS pct_falla TEXT;
ALTER TABLE raw.dim_tarjetas ADD COLUMN IF NOT EXISTS veredicto TEXT;
ALTER TABLE raw.dim_tarjetas ADD COLUMN IF NOT EXISTS visto_desde TEXT;
ALTER TABLE raw.dim_tarjetas ADD COLUMN IF NOT EXISTS visto_hasta TEXT;
ALTER TABLE raw.dim_tarjetas ADD COLUMN IF NOT EXISTS estado TEXT;
ALTER TABLE raw.dim_tarjetas ADD COLUMN IF NOT EXISTS notas TEXT;

-- dim_vocabulario <- PRODUCTOS/_DIM_VOCABULARIO.csv
CREATE TABLE IF NOT EXISTS raw.dim_vocabulario (
    id BIGSERIAL PRIMARY KEY,
    tenant_id TEXT NOT NULL DEFAULT 'vitalcom',
    eje TEXT,
    valor TEXT,
    etiqueta TEXT,
    tipo_eje TEXT,
    mapea_a TEXT,
    definicion TEXT,
    dueno_del_vocabulario TEXT,
    estado TEXT,
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
ALTER TABLE raw.dim_vocabulario ADD COLUMN IF NOT EXISTS eje TEXT;
ALTER TABLE raw.dim_vocabulario ADD COLUMN IF NOT EXISTS valor TEXT;
ALTER TABLE raw.dim_vocabulario ADD COLUMN IF NOT EXISTS etiqueta TEXT;
ALTER TABLE raw.dim_vocabulario ADD COLUMN IF NOT EXISTS tipo_eje TEXT;
ALTER TABLE raw.dim_vocabulario ADD COLUMN IF NOT EXISTS mapea_a TEXT;
ALTER TABLE raw.dim_vocabulario ADD COLUMN IF NOT EXISTS definicion TEXT;
ALTER TABLE raw.dim_vocabulario ADD COLUMN IF NOT EXISTS dueno_del_vocabulario TEXT;
ALTER TABLE raw.dim_vocabulario ADD COLUMN IF NOT EXISTS estado TEXT;

-- dim_anuncios <- PRODUCTOS/_DIM_ANUNCIOS.csv
CREATE TABLE IF NOT EXISTS raw.dim_anuncios (
    id BIGSERIAL PRIMARY KEY,
    tenant_id TEXT NOT NULL DEFAULT 'vitalcom',
    producto_key TEXT,
    anuncio_norm TEXT,
    anuncio_ejemplo TEXT,
    firma TEXT,
    ad_ids TEXT,
    conjunto_norm TEXT,
    cuenta_alias TEXT,
    campana TEXT,
    angulo_key TEXT,
    concepto_key TEXT,
    canonico_id TEXT,
    nivel_conciencia TEXT,
    oferta_key TEXT,
    lleva_precio TEXT,
    destino_key TEXT,
    formato TEXT,
    rol_embudo TEXT,
    tipo_hook TEXT,
    estilo_visual TEXT,
    avatar_edad TEXT,
    avatar_genero TEXT,
    pagina_id TEXT,
    creativo_id TEXT,
    test_id TEXT,
    brazo_key TEXT,
    primera_fecha TEXT,
    ultima_fecha TEXT,
    replicas TEXT,
    spend_usd TEXT,
    ventas TEXT,
    mensajes TEXT,
    clicks TEXT,
    impresiones TEXT,
    fuente_parametrizacion TEXT,
    confianza TEXT,
    estado TEXT,
    notas TEXT,
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
ALTER TABLE raw.dim_anuncios ADD COLUMN IF NOT EXISTS producto_key TEXT;
ALTER TABLE raw.dim_anuncios ADD COLUMN IF NOT EXISTS anuncio_norm TEXT;
ALTER TABLE raw.dim_anuncios ADD COLUMN IF NOT EXISTS anuncio_ejemplo TEXT;
ALTER TABLE raw.dim_anuncios ADD COLUMN IF NOT EXISTS firma TEXT;
ALTER TABLE raw.dim_anuncios ADD COLUMN IF NOT EXISTS ad_ids TEXT;
ALTER TABLE raw.dim_anuncios ADD COLUMN IF NOT EXISTS conjunto_norm TEXT;
ALTER TABLE raw.dim_anuncios ADD COLUMN IF NOT EXISTS cuenta_alias TEXT;
ALTER TABLE raw.dim_anuncios ADD COLUMN IF NOT EXISTS campana TEXT;
ALTER TABLE raw.dim_anuncios ADD COLUMN IF NOT EXISTS angulo_key TEXT;
ALTER TABLE raw.dim_anuncios ADD COLUMN IF NOT EXISTS concepto_key TEXT;
ALTER TABLE raw.dim_anuncios ADD COLUMN IF NOT EXISTS canonico_id TEXT;
ALTER TABLE raw.dim_anuncios ADD COLUMN IF NOT EXISTS nivel_conciencia TEXT;
ALTER TABLE raw.dim_anuncios ADD COLUMN IF NOT EXISTS oferta_key TEXT;
ALTER TABLE raw.dim_anuncios ADD COLUMN IF NOT EXISTS lleva_precio TEXT;
ALTER TABLE raw.dim_anuncios ADD COLUMN IF NOT EXISTS destino_key TEXT;
ALTER TABLE raw.dim_anuncios ADD COLUMN IF NOT EXISTS formato TEXT;
ALTER TABLE raw.dim_anuncios ADD COLUMN IF NOT EXISTS rol_embudo TEXT;
ALTER TABLE raw.dim_anuncios ADD COLUMN IF NOT EXISTS tipo_hook TEXT;
ALTER TABLE raw.dim_anuncios ADD COLUMN IF NOT EXISTS estilo_visual TEXT;
ALTER TABLE raw.dim_anuncios ADD COLUMN IF NOT EXISTS avatar_edad TEXT;
ALTER TABLE raw.dim_anuncios ADD COLUMN IF NOT EXISTS avatar_genero TEXT;
ALTER TABLE raw.dim_anuncios ADD COLUMN IF NOT EXISTS pagina_id TEXT;
ALTER TABLE raw.dim_anuncios ADD COLUMN IF NOT EXISTS creativo_id TEXT;
ALTER TABLE raw.dim_anuncios ADD COLUMN IF NOT EXISTS test_id TEXT;
ALTER TABLE raw.dim_anuncios ADD COLUMN IF NOT EXISTS brazo_key TEXT;
ALTER TABLE raw.dim_anuncios ADD COLUMN IF NOT EXISTS primera_fecha TEXT;
ALTER TABLE raw.dim_anuncios ADD COLUMN IF NOT EXISTS ultima_fecha TEXT;
ALTER TABLE raw.dim_anuncios ADD COLUMN IF NOT EXISTS replicas TEXT;
ALTER TABLE raw.dim_anuncios ADD COLUMN IF NOT EXISTS spend_usd TEXT;
ALTER TABLE raw.dim_anuncios ADD COLUMN IF NOT EXISTS ventas TEXT;
ALTER TABLE raw.dim_anuncios ADD COLUMN IF NOT EXISTS mensajes TEXT;
ALTER TABLE raw.dim_anuncios ADD COLUMN IF NOT EXISTS clicks TEXT;
ALTER TABLE raw.dim_anuncios ADD COLUMN IF NOT EXISTS impresiones TEXT;
ALTER TABLE raw.dim_anuncios ADD COLUMN IF NOT EXISTS fuente_parametrizacion TEXT;
ALTER TABLE raw.dim_anuncios ADD COLUMN IF NOT EXISTS confianza TEXT;
ALTER TABLE raw.dim_anuncios ADD COLUMN IF NOT EXISTS estado TEXT;
ALTER TABLE raw.dim_anuncios ADD COLUMN IF NOT EXISTS notas TEXT;

-- estado_angulos <- PRODUCTOS/_ESTADO_ANGULOS.csv
CREATE TABLE IF NOT EXISTS raw.estado_angulos (
    id BIGSERIAL PRIMARY KEY,
    tenant_id TEXT NOT NULL DEFAULT 'vitalcom',
    producto_key TEXT,
    angulo_key TEXT,
    estado TEXT,
    desde TEXT,
    estado_anterior TEXT,
    evidencia TEXT,
    estado_motor TEXT,
    accion_codigo TEXT,
    ventas_acum TEXT,
    gasto_acum_q TEXT,
    cpa_acum_q TEXT,
    cpa_be_q TEXT,
    pct_pd TEXT,
    mensajes_acum TEXT,
    cierre_acum_pct TEXT,
    ventas_ventana TEXT,
    gasto_ventana_q TEXT,
    cpa_ventana_q TEXT,
    p_rentable TEXT,
    neto_por_q TEXT,
    perdida_por_q TEXT,
    prioridad_ts TEXT,
    pct_gasto_producto TEXT,
    banda_homogenea TEXT,
    dias_con_gasto TEXT,
    primer_dia TEXT,
    ultimo_dia_gasto TEXT,
    dias_sin_gasto TEXT,
    ventas_control TEXT,
    accion_motor TEXT,
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
ALTER TABLE raw.estado_angulos ADD COLUMN IF NOT EXISTS producto_key TEXT;
ALTER TABLE raw.estado_angulos ADD COLUMN IF NOT EXISTS angulo_key TEXT;
ALTER TABLE raw.estado_angulos ADD COLUMN IF NOT EXISTS estado TEXT;
ALTER TABLE raw.estado_angulos ADD COLUMN IF NOT EXISTS desde TEXT;
ALTER TABLE raw.estado_angulos ADD COLUMN IF NOT EXISTS estado_anterior TEXT;
ALTER TABLE raw.estado_angulos ADD COLUMN IF NOT EXISTS evidencia TEXT;
ALTER TABLE raw.estado_angulos ADD COLUMN IF NOT EXISTS estado_motor TEXT;
ALTER TABLE raw.estado_angulos ADD COLUMN IF NOT EXISTS accion_codigo TEXT;
ALTER TABLE raw.estado_angulos ADD COLUMN IF NOT EXISTS ventas_acum TEXT;
ALTER TABLE raw.estado_angulos ADD COLUMN IF NOT EXISTS gasto_acum_q TEXT;
ALTER TABLE raw.estado_angulos ADD COLUMN IF NOT EXISTS cpa_acum_q TEXT;
ALTER TABLE raw.estado_angulos ADD COLUMN IF NOT EXISTS cpa_be_q TEXT;
ALTER TABLE raw.estado_angulos ADD COLUMN IF NOT EXISTS pct_pd TEXT;
ALTER TABLE raw.estado_angulos ADD COLUMN IF NOT EXISTS mensajes_acum TEXT;
ALTER TABLE raw.estado_angulos ADD COLUMN IF NOT EXISTS cierre_acum_pct TEXT;
ALTER TABLE raw.estado_angulos ADD COLUMN IF NOT EXISTS ventas_ventana TEXT;
ALTER TABLE raw.estado_angulos ADD COLUMN IF NOT EXISTS gasto_ventana_q TEXT;
ALTER TABLE raw.estado_angulos ADD COLUMN IF NOT EXISTS cpa_ventana_q TEXT;
ALTER TABLE raw.estado_angulos ADD COLUMN IF NOT EXISTS p_rentable TEXT;
ALTER TABLE raw.estado_angulos ADD COLUMN IF NOT EXISTS neto_por_q TEXT;
ALTER TABLE raw.estado_angulos ADD COLUMN IF NOT EXISTS perdida_por_q TEXT;
ALTER TABLE raw.estado_angulos ADD COLUMN IF NOT EXISTS prioridad_ts TEXT;
ALTER TABLE raw.estado_angulos ADD COLUMN IF NOT EXISTS pct_gasto_producto TEXT;
ALTER TABLE raw.estado_angulos ADD COLUMN IF NOT EXISTS banda_homogenea TEXT;
ALTER TABLE raw.estado_angulos ADD COLUMN IF NOT EXISTS dias_con_gasto TEXT;
ALTER TABLE raw.estado_angulos ADD COLUMN IF NOT EXISTS primer_dia TEXT;
ALTER TABLE raw.estado_angulos ADD COLUMN IF NOT EXISTS ultimo_dia_gasto TEXT;
ALTER TABLE raw.estado_angulos ADD COLUMN IF NOT EXISTS dias_sin_gasto TEXT;
ALTER TABLE raw.estado_angulos ADD COLUMN IF NOT EXISTS ventas_control TEXT;
ALTER TABLE raw.estado_angulos ADD COLUMN IF NOT EXISTS accion_motor TEXT;

-- estado_flujo <- PRODUCTOS/_ESTADO_FLUJO.csv
CREATE TABLE IF NOT EXISTS raw.estado_flujo (
    id BIGSERIAL PRIMARY KEY,
    tenant_id TEXT NOT NULL DEFAULT 'vitalcom',
    producto_key TEXT,
    fase TEXT,
    nodo_actual TEXT,
    estado TEXT,
    desde TEXT,
    bloqueantes TEXT,
    siguiente_ejecutor TEXT,
    evaluado_el TEXT,
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
ALTER TABLE raw.estado_flujo ADD COLUMN IF NOT EXISTS producto_key TEXT;
ALTER TABLE raw.estado_flujo ADD COLUMN IF NOT EXISTS fase TEXT;
ALTER TABLE raw.estado_flujo ADD COLUMN IF NOT EXISTS nodo_actual TEXT;
ALTER TABLE raw.estado_flujo ADD COLUMN IF NOT EXISTS estado TEXT;
ALTER TABLE raw.estado_flujo ADD COLUMN IF NOT EXISTS desde TEXT;
ALTER TABLE raw.estado_flujo ADD COLUMN IF NOT EXISTS bloqueantes TEXT;
ALTER TABLE raw.estado_flujo ADD COLUMN IF NOT EXISTS siguiente_ejecutor TEXT;
ALTER TABLE raw.estado_flujo ADD COLUMN IF NOT EXISTS evaluado_el TEXT;

-- estado_meta <- PRODUCTOS/_ESTADO_META.csv
CREATE TABLE IF NOT EXISTS raw.estado_meta (
    id BIGSERIAL PRIMARY KEY,
    tenant_id TEXT NOT NULL DEFAULT 'vitalcom',
    cuenta_alias TEXT,
    campana TEXT,
    producto_key TEXT,
    estado TEXT,
    conjuntos_activos TEXT,
    fecha_confirmado TEXT,
    fuente TEXT,
    notas TEXT,
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
ALTER TABLE raw.estado_meta ADD COLUMN IF NOT EXISTS cuenta_alias TEXT;
ALTER TABLE raw.estado_meta ADD COLUMN IF NOT EXISTS campana TEXT;
ALTER TABLE raw.estado_meta ADD COLUMN IF NOT EXISTS producto_key TEXT;
ALTER TABLE raw.estado_meta ADD COLUMN IF NOT EXISTS estado TEXT;
ALTER TABLE raw.estado_meta ADD COLUMN IF NOT EXISTS conjuntos_activos TEXT;
ALTER TABLE raw.estado_meta ADD COLUMN IF NOT EXISTS fecha_confirmado TEXT;
ALTER TABLE raw.estado_meta ADD COLUMN IF NOT EXISTS fuente TEXT;
ALTER TABLE raw.estado_meta ADD COLUMN IF NOT EXISTS notas TEXT;

-- fact_facturacion <- PRODUCTOS/_FACT_FACTURACION.csv
CREATE TABLE IF NOT EXISTS raw.fact_facturacion (
    id BIGSERIAL PRIMARY KEY,
    tenant_id TEXT NOT NULL DEFAULT 'vitalcom',
    fecha TEXT,
    cuenta_id TEXT,
    cuenta_alias TEXT,
    bm_nombre TEXT,
    tipo TEXT,
    monto_origen TEXT,
    moneda_origen TEXT,
    tasa_a_usd TEXT,
    monto_usd TEXT,
    ultimos4 TEXT,
    marca TEXT,
    id_transaccion TEXT,
    fuente TEXT,
    notas TEXT,
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
ALTER TABLE raw.fact_facturacion ADD COLUMN IF NOT EXISTS fecha TEXT;
ALTER TABLE raw.fact_facturacion ADD COLUMN IF NOT EXISTS cuenta_id TEXT;
ALTER TABLE raw.fact_facturacion ADD COLUMN IF NOT EXISTS cuenta_alias TEXT;
ALTER TABLE raw.fact_facturacion ADD COLUMN IF NOT EXISTS bm_nombre TEXT;
ALTER TABLE raw.fact_facturacion ADD COLUMN IF NOT EXISTS tipo TEXT;
ALTER TABLE raw.fact_facturacion ADD COLUMN IF NOT EXISTS monto_origen TEXT;
ALTER TABLE raw.fact_facturacion ADD COLUMN IF NOT EXISTS moneda_origen TEXT;
ALTER TABLE raw.fact_facturacion ADD COLUMN IF NOT EXISTS tasa_a_usd TEXT;
ALTER TABLE raw.fact_facturacion ADD COLUMN IF NOT EXISTS monto_usd TEXT;
ALTER TABLE raw.fact_facturacion ADD COLUMN IF NOT EXISTS ultimos4 TEXT;
ALTER TABLE raw.fact_facturacion ADD COLUMN IF NOT EXISTS marca TEXT;
ALTER TABLE raw.fact_facturacion ADD COLUMN IF NOT EXISTS id_transaccion TEXT;
ALTER TABLE raw.fact_facturacion ADD COLUMN IF NOT EXISTS fuente TEXT;
ALTER TABLE raw.fact_facturacion ADD COLUMN IF NOT EXISTS notas TEXT;

-- fact_facturacion_agregado <- PRODUCTOS/_FACT_FACTURACION_AGREGADO.csv
CREATE TABLE IF NOT EXISTS raw.fact_facturacion_agregado (
    id BIGSERIAL PRIMARY KEY,
    tenant_id TEXT NOT NULL DEFAULT 'vitalcom',
    ventana_ini TEXT,
    ventana_fin TEXT,
    cuenta_id TEXT,
    cuenta_alias TEXT,
    bm_nombre TEXT,
    cobros_usd TEXT,
    rechazos_n TEXT,
    creditos_usd TEXT,
    moneda_origen TEXT,
    fuente TEXT,
    notas TEXT,
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
ALTER TABLE raw.fact_facturacion_agregado ADD COLUMN IF NOT EXISTS ventana_ini TEXT;
ALTER TABLE raw.fact_facturacion_agregado ADD COLUMN IF NOT EXISTS ventana_fin TEXT;
ALTER TABLE raw.fact_facturacion_agregado ADD COLUMN IF NOT EXISTS cuenta_id TEXT;
ALTER TABLE raw.fact_facturacion_agregado ADD COLUMN IF NOT EXISTS cuenta_alias TEXT;
ALTER TABLE raw.fact_facturacion_agregado ADD COLUMN IF NOT EXISTS bm_nombre TEXT;
ALTER TABLE raw.fact_facturacion_agregado ADD COLUMN IF NOT EXISTS cobros_usd TEXT;
ALTER TABLE raw.fact_facturacion_agregado ADD COLUMN IF NOT EXISTS rechazos_n TEXT;
ALTER TABLE raw.fact_facturacion_agregado ADD COLUMN IF NOT EXISTS creditos_usd TEXT;
ALTER TABLE raw.fact_facturacion_agregado ADD COLUMN IF NOT EXISTS moneda_origen TEXT;
ALTER TABLE raw.fact_facturacion_agregado ADD COLUMN IF NOT EXISTS fuente TEXT;
ALTER TABLE raw.fact_facturacion_agregado ADD COLUMN IF NOT EXISTS notas TEXT;

-- fact_pauta_real <- PRODUCTOS/_FACT_PAUTA_REAL.csv
CREATE TABLE IF NOT EXISTS raw.fact_pauta_real (
    id BIGSERIAL PRIMARY KEY,
    tenant_id TEXT NOT NULL DEFAULT 'vitalcom',
    ventana_ini TEXT,
    ventana_fin TEXT,
    dias TEXT,
    cuenta_id TEXT,
    cuenta_alias TEXT,
    spend_trackeado_usd TEXT,
    spend_real_usd TEXT,
    fuente TEXT,
    moneda_origen TEXT,
    notas TEXT,
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
ALTER TABLE raw.fact_pauta_real ADD COLUMN IF NOT EXISTS ventana_ini TEXT;
ALTER TABLE raw.fact_pauta_real ADD COLUMN IF NOT EXISTS ventana_fin TEXT;
ALTER TABLE raw.fact_pauta_real ADD COLUMN IF NOT EXISTS dias TEXT;
ALTER TABLE raw.fact_pauta_real ADD COLUMN IF NOT EXISTS cuenta_id TEXT;
ALTER TABLE raw.fact_pauta_real ADD COLUMN IF NOT EXISTS cuenta_alias TEXT;
ALTER TABLE raw.fact_pauta_real ADD COLUMN IF NOT EXISTS spend_trackeado_usd TEXT;
ALTER TABLE raw.fact_pauta_real ADD COLUMN IF NOT EXISTS spend_real_usd TEXT;
ALTER TABLE raw.fact_pauta_real ADD COLUMN IF NOT EXISTS fuente TEXT;
ALTER TABLE raw.fact_pauta_real ADD COLUMN IF NOT EXISTS moneda_origen TEXT;
ALTER TABLE raw.fact_pauta_real ADD COLUMN IF NOT EXISTS notas TEXT;

-- fact_saldos <- PRODUCTOS/_FACT_SALDOS.csv
CREATE TABLE IF NOT EXISTS raw.fact_saldos (
    id BIGSERIAL PRIMARY KEY,
    tenant_id TEXT NOT NULL DEFAULT 'vitalcom',
    fecha_corte TEXT,
    cuenta_id TEXT,
    cuenta_alias TEXT,
    saldo_sin_facturar_usd TEXT,
    moneda_origen TEXT,
    fuente TEXT,
    estado TEXT,
    notas TEXT,
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
ALTER TABLE raw.fact_saldos ADD COLUMN IF NOT EXISTS fecha_corte TEXT;
ALTER TABLE raw.fact_saldos ADD COLUMN IF NOT EXISTS cuenta_id TEXT;
ALTER TABLE raw.fact_saldos ADD COLUMN IF NOT EXISTS cuenta_alias TEXT;
ALTER TABLE raw.fact_saldos ADD COLUMN IF NOT EXISTS saldo_sin_facturar_usd TEXT;
ALTER TABLE raw.fact_saldos ADD COLUMN IF NOT EXISTS moneda_origen TEXT;
ALTER TABLE raw.fact_saldos ADD COLUMN IF NOT EXISTS fuente TEXT;
ALTER TABLE raw.fact_saldos ADD COLUMN IF NOT EXISTS estado TEXT;
ALTER TABLE raw.fact_saldos ADD COLUMN IF NOT EXISTS notas TEXT;

-- fact_semanal <- PRODUCTOS/_FACT_SEMANAL.csv
CREATE TABLE IF NOT EXISTS raw.fact_semanal (
    id BIGSERIAL PRIMARY KEY,
    tenant_id TEXT NOT NULL DEFAULT 'vitalcom',
    semana_ini TEXT,
    semana_fin TEXT,
    dias_con_data TEXT,
    corte_estimado TEXT,
    producto_key TEXT,
    ventas TEXT,
    facturado_q TEXT,
    pauta_q TEXT,
    contribucion_q TEXT,
    ganancia_q TEXT,
    cpa_q TEXT,
    roas TEXT,
    mercado TEXT,
    moneda TEXT,
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
ALTER TABLE raw.fact_semanal ADD COLUMN IF NOT EXISTS semana_ini TEXT;
ALTER TABLE raw.fact_semanal ADD COLUMN IF NOT EXISTS semana_fin TEXT;
ALTER TABLE raw.fact_semanal ADD COLUMN IF NOT EXISTS dias_con_data TEXT;
ALTER TABLE raw.fact_semanal ADD COLUMN IF NOT EXISTS corte_estimado TEXT;
ALTER TABLE raw.fact_semanal ADD COLUMN IF NOT EXISTS producto_key TEXT;
ALTER TABLE raw.fact_semanal ADD COLUMN IF NOT EXISTS ventas TEXT;
ALTER TABLE raw.fact_semanal ADD COLUMN IF NOT EXISTS facturado_q TEXT;
ALTER TABLE raw.fact_semanal ADD COLUMN IF NOT EXISTS pauta_q TEXT;
ALTER TABLE raw.fact_semanal ADD COLUMN IF NOT EXISTS contribucion_q TEXT;
ALTER TABLE raw.fact_semanal ADD COLUMN IF NOT EXISTS ganancia_q TEXT;
ALTER TABLE raw.fact_semanal ADD COLUMN IF NOT EXISTS cpa_q TEXT;
ALTER TABLE raw.fact_semanal ADD COLUMN IF NOT EXISTS roas TEXT;
ALTER TABLE raw.fact_semanal ADD COLUMN IF NOT EXISTS mercado TEXT;
ALTER TABLE raw.fact_semanal ADD COLUMN IF NOT EXISTS moneda TEXT;

-- mapeo_creativos <- PRODUCTOS/_MAPEO_CREATIVOS.csv
CREATE TABLE IF NOT EXISTS raw.mapeo_creativos (
    id BIGSERIAL PRIMARY KEY,
    tenant_id TEXT NOT NULL DEFAULT 'vitalcom',
    producto_key TEXT,
    anuncio TEXT,
    archivo_media TEXT,
    tipo TEXT,
    metodo TEXT,
    ventas TEXT,
    spend_usd TEXT,
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
ALTER TABLE raw.mapeo_creativos ADD COLUMN IF NOT EXISTS producto_key TEXT;
ALTER TABLE raw.mapeo_creativos ADD COLUMN IF NOT EXISTS anuncio TEXT;
ALTER TABLE raw.mapeo_creativos ADD COLUMN IF NOT EXISTS archivo_media TEXT;
ALTER TABLE raw.mapeo_creativos ADD COLUMN IF NOT EXISTS tipo TEXT;
ALTER TABLE raw.mapeo_creativos ADD COLUMN IF NOT EXISTS metodo TEXT;
ALTER TABLE raw.mapeo_creativos ADD COLUMN IF NOT EXISTS ventas TEXT;
ALTER TABLE raw.mapeo_creativos ADD COLUMN IF NOT EXISTS spend_usd TEXT;

-- parametros_decision <- PRODUCTOS/_PARAMETROS_DECISION.csv
CREATE TABLE IF NOT EXISTS raw.parametros_decision (
    id BIGSERIAL PRIMARY KEY,
    tenant_id TEXT NOT NULL DEFAULT 'vitalcom',
    parametro TEXT,
    valor TEXT,
    unidad TEXT,
    dueno TEXT,
    por_que TEXT,
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
ALTER TABLE raw.parametros_decision ADD COLUMN IF NOT EXISTS parametro TEXT;
ALTER TABLE raw.parametros_decision ADD COLUMN IF NOT EXISTS valor TEXT;
ALTER TABLE raw.parametros_decision ADD COLUMN IF NOT EXISTS unidad TEXT;
ALTER TABLE raw.parametros_decision ADD COLUMN IF NOT EXISTS dueno TEXT;
ALTER TABLE raw.parametros_decision ADD COLUMN IF NOT EXISTS por_que TEXT;

-- parametros_finanzas <- PRODUCTOS/_PARAMETROS_FINANZAS.csv
CREATE TABLE IF NOT EXISTS raw.parametros_finanzas (
    id BIGSERIAL PRIMARY KEY,
    tenant_id TEXT NOT NULL DEFAULT 'vitalcom',
    parametro TEXT,
    valor TEXT,
    unidad TEXT,
    origen TEXT,
    medido_el TEXT,
    n_evidencia TEXT,
    notas TEXT,
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
ALTER TABLE raw.parametros_finanzas ADD COLUMN IF NOT EXISTS parametro TEXT;
ALTER TABLE raw.parametros_finanzas ADD COLUMN IF NOT EXISTS valor TEXT;
ALTER TABLE raw.parametros_finanzas ADD COLUMN IF NOT EXISTS unidad TEXT;
ALTER TABLE raw.parametros_finanzas ADD COLUMN IF NOT EXISTS origen TEXT;
ALTER TABLE raw.parametros_finanzas ADD COLUMN IF NOT EXISTS medido_el TEXT;
ALTER TABLE raw.parametros_finanzas ADD COLUMN IF NOT EXISTS n_evidencia TEXT;
ALTER TABLE raw.parametros_finanzas ADD COLUMN IF NOT EXISTS notas TEXT;

-- parametros_optimizacion <- PRODUCTOS/_PARAMETROS_OPTIMIZACION.csv
CREATE TABLE IF NOT EXISTS raw.parametros_optimizacion (
    id BIGSERIAL PRIMARY KEY,
    tenant_id TEXT NOT NULL DEFAULT 'vitalcom',
    parametro TEXT,
    valor TEXT,
    unidad TEXT,
    dueno TEXT,
    por_que TEXT,
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
ALTER TABLE raw.parametros_optimizacion ADD COLUMN IF NOT EXISTS parametro TEXT;
ALTER TABLE raw.parametros_optimizacion ADD COLUMN IF NOT EXISTS valor TEXT;
ALTER TABLE raw.parametros_optimizacion ADD COLUMN IF NOT EXISTS unidad TEXT;
ALTER TABLE raw.parametros_optimizacion ADD COLUMN IF NOT EXISTS dueno TEXT;
ALTER TABLE raw.parametros_optimizacion ADD COLUMN IF NOT EXISTS por_que TEXT;

-- parametros_publicacion <- PRODUCTOS/_PARAMETROS_PUBLICACION.csv
CREATE TABLE IF NOT EXISTS raw.parametros_publicacion (
    id BIGSERIAL PRIMARY KEY,
    tenant_id TEXT NOT NULL DEFAULT 'vitalcom',
    fase TEXT,
    brazo TEXT,
    estructura TEXT,
    conjuntos TEXT,
    anuncios_por_conjunto TEXT,
    daily_budget_usd TEXT,
    presupuesto_nivel TEXT,
    objetivo TEXT,
    optimization_goal TEXT,
    destination_type TEXT,
    billing_event TEXT,
    buying_type TEXT,
    advantage_audience TEXT,
    hora_lanzamiento TEXT,
    tz_offset TEXT,
    estado TEXT,
    fuente_doctrina TEXT,
    notas TEXT,
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
ALTER TABLE raw.parametros_publicacion ADD COLUMN IF NOT EXISTS fase TEXT;
ALTER TABLE raw.parametros_publicacion ADD COLUMN IF NOT EXISTS brazo TEXT;
ALTER TABLE raw.parametros_publicacion ADD COLUMN IF NOT EXISTS estructura TEXT;
ALTER TABLE raw.parametros_publicacion ADD COLUMN IF NOT EXISTS conjuntos TEXT;
ALTER TABLE raw.parametros_publicacion ADD COLUMN IF NOT EXISTS anuncios_por_conjunto TEXT;
ALTER TABLE raw.parametros_publicacion ADD COLUMN IF NOT EXISTS daily_budget_usd TEXT;
ALTER TABLE raw.parametros_publicacion ADD COLUMN IF NOT EXISTS presupuesto_nivel TEXT;
ALTER TABLE raw.parametros_publicacion ADD COLUMN IF NOT EXISTS objetivo TEXT;
ALTER TABLE raw.parametros_publicacion ADD COLUMN IF NOT EXISTS optimization_goal TEXT;
ALTER TABLE raw.parametros_publicacion ADD COLUMN IF NOT EXISTS destination_type TEXT;
ALTER TABLE raw.parametros_publicacion ADD COLUMN IF NOT EXISTS billing_event TEXT;
ALTER TABLE raw.parametros_publicacion ADD COLUMN IF NOT EXISTS buying_type TEXT;
ALTER TABLE raw.parametros_publicacion ADD COLUMN IF NOT EXISTS advantage_audience TEXT;
ALTER TABLE raw.parametros_publicacion ADD COLUMN IF NOT EXISTS hora_lanzamiento TEXT;
ALTER TABLE raw.parametros_publicacion ADD COLUMN IF NOT EXISTS tz_offset TEXT;
ALTER TABLE raw.parametros_publicacion ADD COLUMN IF NOT EXISTS estado TEXT;
ALTER TABLE raw.parametros_publicacion ADD COLUMN IF NOT EXISTS fuente_doctrina TEXT;
ALTER TABLE raw.parametros_publicacion ADD COLUMN IF NOT EXISTS notas TEXT;

-- tasa_entrega <- PRODUCTOS/_TASA_ENTREGA.csv
CREATE TABLE IF NOT EXISTS raw.tasa_entrega (
    id BIGSERIAL PRIMARY KEY,
    tenant_id TEXT NOT NULL DEFAULT 'vitalcom',
    mes TEXT,
    producto_key TEXT,
    fuente TEXT,
    entregado TEXT,
    devolucion TEXT,
    cancelado TEXT,
    en_transito TEXT,
    total TEXT,
    pct_entrega_resueltos TEXT,
    pct_devolucion_resueltos TEXT,
    pct_devolucion_asumido TEXT,
    costo_devolucion_evento_q TEXT,
    costos_admin_q TEXT,
    otros_gastos_q TEXT,
    notas TEXT,
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
ALTER TABLE raw.tasa_entrega ADD COLUMN IF NOT EXISTS mes TEXT;
ALTER TABLE raw.tasa_entrega ADD COLUMN IF NOT EXISTS producto_key TEXT;
ALTER TABLE raw.tasa_entrega ADD COLUMN IF NOT EXISTS fuente TEXT;
ALTER TABLE raw.tasa_entrega ADD COLUMN IF NOT EXISTS entregado TEXT;
ALTER TABLE raw.tasa_entrega ADD COLUMN IF NOT EXISTS devolucion TEXT;
ALTER TABLE raw.tasa_entrega ADD COLUMN IF NOT EXISTS cancelado TEXT;
ALTER TABLE raw.tasa_entrega ADD COLUMN IF NOT EXISTS en_transito TEXT;
ALTER TABLE raw.tasa_entrega ADD COLUMN IF NOT EXISTS total TEXT;
ALTER TABLE raw.tasa_entrega ADD COLUMN IF NOT EXISTS pct_entrega_resueltos TEXT;
ALTER TABLE raw.tasa_entrega ADD COLUMN IF NOT EXISTS pct_devolucion_resueltos TEXT;
ALTER TABLE raw.tasa_entrega ADD COLUMN IF NOT EXISTS pct_devolucion_asumido TEXT;
ALTER TABLE raw.tasa_entrega ADD COLUMN IF NOT EXISTS costo_devolucion_evento_q TEXT;
ALTER TABLE raw.tasa_entrega ADD COLUMN IF NOT EXISTS costos_admin_q TEXT;
ALTER TABLE raw.tasa_entrega ADD COLUMN IF NOT EXISTS otros_gastos_q TEXT;
ALTER TABLE raw.tasa_entrega ADD COLUMN IF NOT EXISTS notas TEXT;

-- testeos <- PRODUCTOS/_TESTEOS.csv
CREATE TABLE IF NOT EXISTS raw.testeos (
    id BIGSERIAL PRIMARY KEY,
    tenant_id TEXT NOT NULL DEFAULT 'vitalcom',
    test_id TEXT,
    test_nombre TEXT,
    producto_key TEXT,
    variable TEXT,
    hipotesis TEXT,
    angulo_fijo TEXT,
    formato_fijo TEXT,
    fecha_inicio TEXT,
    estado TEXT,
    brazo_key TEXT,
    brazo_nombre TEXT,
    concepto_key TEXT,
    variante TEXT,
    conjuntos_meta TEXT,
    creativo_ref TEXT,
    notas TEXT,
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
ALTER TABLE raw.testeos ADD COLUMN IF NOT EXISTS test_id TEXT;
ALTER TABLE raw.testeos ADD COLUMN IF NOT EXISTS test_nombre TEXT;
ALTER TABLE raw.testeos ADD COLUMN IF NOT EXISTS producto_key TEXT;
ALTER TABLE raw.testeos ADD COLUMN IF NOT EXISTS variable TEXT;
ALTER TABLE raw.testeos ADD COLUMN IF NOT EXISTS hipotesis TEXT;
ALTER TABLE raw.testeos ADD COLUMN IF NOT EXISTS angulo_fijo TEXT;
ALTER TABLE raw.testeos ADD COLUMN IF NOT EXISTS formato_fijo TEXT;
ALTER TABLE raw.testeos ADD COLUMN IF NOT EXISTS fecha_inicio TEXT;
ALTER TABLE raw.testeos ADD COLUMN IF NOT EXISTS estado TEXT;
ALTER TABLE raw.testeos ADD COLUMN IF NOT EXISTS brazo_key TEXT;
ALTER TABLE raw.testeos ADD COLUMN IF NOT EXISTS brazo_nombre TEXT;
ALTER TABLE raw.testeos ADD COLUMN IF NOT EXISTS concepto_key TEXT;
ALTER TABLE raw.testeos ADD COLUMN IF NOT EXISTS variante TEXT;
ALTER TABLE raw.testeos ADD COLUMN IF NOT EXISTS conjuntos_meta TEXT;
ALTER TABLE raw.testeos ADD COLUMN IF NOT EXISTS creativo_ref TEXT;
ALTER TABLE raw.testeos ADD COLUMN IF NOT EXISTS notas TEXT;

-- clasificacion_anuncios <- PRODUCTOS/_CLASIFICACION_ANUNCIOS.csv
CREATE TABLE IF NOT EXISTS raw.clasificacion_anuncios (
    id BIGSERIAL PRIMARY KEY,
    tenant_id TEXT NOT NULL DEFAULT 'vitalcom',
    producto_key TEXT,
    anuncio_norm TEXT,
    concepto_key TEXT,
    canonico_id TEXT,
    nivel_conciencia TEXT,
    oferta_key TEXT,
    lleva_precio TEXT,
    rol_embudo TEXT,
    formato TEXT,
    confianza TEXT,
    evidencia TEXT,
    notas TEXT,
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
ALTER TABLE raw.clasificacion_anuncios ADD COLUMN IF NOT EXISTS producto_key TEXT;
ALTER TABLE raw.clasificacion_anuncios ADD COLUMN IF NOT EXISTS anuncio_norm TEXT;
ALTER TABLE raw.clasificacion_anuncios ADD COLUMN IF NOT EXISTS concepto_key TEXT;
ALTER TABLE raw.clasificacion_anuncios ADD COLUMN IF NOT EXISTS canonico_id TEXT;
ALTER TABLE raw.clasificacion_anuncios ADD COLUMN IF NOT EXISTS nivel_conciencia TEXT;
ALTER TABLE raw.clasificacion_anuncios ADD COLUMN IF NOT EXISTS oferta_key TEXT;
ALTER TABLE raw.clasificacion_anuncios ADD COLUMN IF NOT EXISTS lleva_precio TEXT;
ALTER TABLE raw.clasificacion_anuncios ADD COLUMN IF NOT EXISTS rol_embudo TEXT;
ALTER TABLE raw.clasificacion_anuncios ADD COLUMN IF NOT EXISTS formato TEXT;
ALTER TABLE raw.clasificacion_anuncios ADD COLUMN IF NOT EXISTS confianza TEXT;
ALTER TABLE raw.clasificacion_anuncios ADD COLUMN IF NOT EXISTS evidencia TEXT;
ALTER TABLE raw.clasificacion_anuncios ADD COLUMN IF NOT EXISTS notas TEXT;

-- aprendizajes <- PRODUCTOS/_APRENDIZAJES.csv
CREATE TABLE IF NOT EXISTS raw.aprendizajes (
    id BIGSERIAL PRIMARY KEY,
    tenant_id TEXT NOT NULL DEFAULT 'vitalcom',
    id_csv TEXT,
    fecha_registro TEXT,
    alcance TEXT,
    producto_key TEXT,
    categoria TEXT,
    dimension TEXT,
    valor TEXT,
    regla TEXT,
    evidencia_n TEXT,
    evidencia_metrica TEXT,
    confianza TEXT,
    estado TEXT,
    revisar_despues_de TEXT,
    fuente TEXT,
    consumido_por TEXT,
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
ALTER TABLE raw.aprendizajes ADD COLUMN IF NOT EXISTS id_csv TEXT;
ALTER TABLE raw.aprendizajes ADD COLUMN IF NOT EXISTS fecha_registro TEXT;
ALTER TABLE raw.aprendizajes ADD COLUMN IF NOT EXISTS alcance TEXT;
ALTER TABLE raw.aprendizajes ADD COLUMN IF NOT EXISTS producto_key TEXT;
ALTER TABLE raw.aprendizajes ADD COLUMN IF NOT EXISTS categoria TEXT;
ALTER TABLE raw.aprendizajes ADD COLUMN IF NOT EXISTS dimension TEXT;
ALTER TABLE raw.aprendizajes ADD COLUMN IF NOT EXISTS valor TEXT;
ALTER TABLE raw.aprendizajes ADD COLUMN IF NOT EXISTS regla TEXT;
ALTER TABLE raw.aprendizajes ADD COLUMN IF NOT EXISTS evidencia_n TEXT;
ALTER TABLE raw.aprendizajes ADD COLUMN IF NOT EXISTS evidencia_metrica TEXT;
ALTER TABLE raw.aprendizajes ADD COLUMN IF NOT EXISTS confianza TEXT;
ALTER TABLE raw.aprendizajes ADD COLUMN IF NOT EXISTS estado TEXT;
ALTER TABLE raw.aprendizajes ADD COLUMN IF NOT EXISTS revisar_despues_de TEXT;
ALTER TABLE raw.aprendizajes ADD COLUMN IF NOT EXISTS fuente TEXT;
ALTER TABLE raw.aprendizajes ADD COLUMN IF NOT EXISTS consumido_por TEXT;

-- mapa_ad_id_hist <- PRODUCTOS/_MAPA_AD_ID_HIST.csv
CREATE TABLE IF NOT EXISTS raw.mapa_ad_id_hist (
    id BIGSERIAL PRIMARY KEY,
    tenant_id TEXT NOT NULL DEFAULT 'vitalcom',
    ventana_ini TEXT,
    ventana_fin TEXT,
    cuenta_alias TEXT,
    conjunto TEXT,
    anuncio TEXT,
    ad_id TEXT,
    metodo TEXT,
    motivo TEXT,
    spend_lucid TEXT,
    spend_meta TEXT,
    venta_uid TEXT,
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
ALTER TABLE raw.mapa_ad_id_hist ADD COLUMN IF NOT EXISTS ventana_ini TEXT;
ALTER TABLE raw.mapa_ad_id_hist ADD COLUMN IF NOT EXISTS ventana_fin TEXT;
ALTER TABLE raw.mapa_ad_id_hist ADD COLUMN IF NOT EXISTS cuenta_alias TEXT;
ALTER TABLE raw.mapa_ad_id_hist ADD COLUMN IF NOT EXISTS conjunto TEXT;
ALTER TABLE raw.mapa_ad_id_hist ADD COLUMN IF NOT EXISTS anuncio TEXT;
ALTER TABLE raw.mapa_ad_id_hist ADD COLUMN IF NOT EXISTS ad_id TEXT;
ALTER TABLE raw.mapa_ad_id_hist ADD COLUMN IF NOT EXISTS metodo TEXT;
ALTER TABLE raw.mapa_ad_id_hist ADD COLUMN IF NOT EXISTS motivo TEXT;
ALTER TABLE raw.mapa_ad_id_hist ADD COLUMN IF NOT EXISTS spend_lucid TEXT;
ALTER TABLE raw.mapa_ad_id_hist ADD COLUMN IF NOT EXISTS spend_meta TEXT;
ALTER TABLE raw.mapa_ad_id_hist ADD COLUMN IF NOT EXISTS venta_uid TEXT;

-- entrega_conjunto_dia <- PRODUCTOS/_FACT_ENTREGA.csv
CREATE TABLE IF NOT EXISTS raw.entrega_conjunto_dia (
    id BIGSERIAL PRIMARY KEY,
    tenant_id TEXT NOT NULL DEFAULT 'vitalcom',
    ventana_ini TEXT,
    ventana_fin TEXT,
    dias TEXT,
    producto_key TEXT,
    cuenta_id TEXT,
    cuenta_alias TEXT,
    campana TEXT,
    conjunto TEXT,
    mensajes TEXT,
    clicks_totales TEXT,
    link_clicks TEXT,
    impresiones TEXT,
    spend_usd TEXT,
    pct_conv_clic_enlace TEXT,
    fuente TEXT,
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
ALTER TABLE raw.entrega_conjunto_dia ADD COLUMN IF NOT EXISTS ventana_ini TEXT;
ALTER TABLE raw.entrega_conjunto_dia ADD COLUMN IF NOT EXISTS ventana_fin TEXT;
ALTER TABLE raw.entrega_conjunto_dia ADD COLUMN IF NOT EXISTS dias TEXT;
ALTER TABLE raw.entrega_conjunto_dia ADD COLUMN IF NOT EXISTS producto_key TEXT;
ALTER TABLE raw.entrega_conjunto_dia ADD COLUMN IF NOT EXISTS cuenta_id TEXT;
ALTER TABLE raw.entrega_conjunto_dia ADD COLUMN IF NOT EXISTS cuenta_alias TEXT;
ALTER TABLE raw.entrega_conjunto_dia ADD COLUMN IF NOT EXISTS campana TEXT;
ALTER TABLE raw.entrega_conjunto_dia ADD COLUMN IF NOT EXISTS conjunto TEXT;
ALTER TABLE raw.entrega_conjunto_dia ADD COLUMN IF NOT EXISTS mensajes TEXT;
ALTER TABLE raw.entrega_conjunto_dia ADD COLUMN IF NOT EXISTS clicks_totales TEXT;
ALTER TABLE raw.entrega_conjunto_dia ADD COLUMN IF NOT EXISTS link_clicks TEXT;
ALTER TABLE raw.entrega_conjunto_dia ADD COLUMN IF NOT EXISTS impresiones TEXT;
ALTER TABLE raw.entrega_conjunto_dia ADD COLUMN IF NOT EXISTS spend_usd TEXT;
ALTER TABLE raw.entrega_conjunto_dia ADD COLUMN IF NOT EXISTS pct_conv_clic_enlace TEXT;
ALTER TABLE raw.entrega_conjunto_dia ADD COLUMN IF NOT EXISTS fuente TEXT;

-- entrega_anuncio_dia <- PRODUCTOS/_FACT_ENTREGA_ANUNCIO.csv
CREATE TABLE IF NOT EXISTS raw.entrega_anuncio_dia (
    id BIGSERIAL PRIMARY KEY,
    tenant_id TEXT NOT NULL DEFAULT 'vitalcom',
    ventana_ini TEXT,
    ventana_fin TEXT,
    dias TEXT,
    producto_key TEXT,
    cuenta_id TEXT,
    cuenta_alias TEXT,
    campana TEXT,
    conjunto TEXT,
    anuncio TEXT,
    ad_id TEXT,
    firma TEXT,
    angulo_key TEXT,
    concepto_key TEXT,
    canonico_id TEXT,
    nivel_conciencia TEXT,
    oferta_key TEXT,
    destino_key TEXT,
    mensajes TEXT,
    clicks_totales TEXT,
    link_clicks TEXT,
    impresiones TEXT,
    spend_usd TEXT,
    pct_conv_clic_enlace TEXT,
    fuente TEXT,
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
ALTER TABLE raw.entrega_anuncio_dia ADD COLUMN IF NOT EXISTS ventana_ini TEXT;
ALTER TABLE raw.entrega_anuncio_dia ADD COLUMN IF NOT EXISTS ventana_fin TEXT;
ALTER TABLE raw.entrega_anuncio_dia ADD COLUMN IF NOT EXISTS dias TEXT;
ALTER TABLE raw.entrega_anuncio_dia ADD COLUMN IF NOT EXISTS producto_key TEXT;
ALTER TABLE raw.entrega_anuncio_dia ADD COLUMN IF NOT EXISTS cuenta_id TEXT;
ALTER TABLE raw.entrega_anuncio_dia ADD COLUMN IF NOT EXISTS cuenta_alias TEXT;
ALTER TABLE raw.entrega_anuncio_dia ADD COLUMN IF NOT EXISTS campana TEXT;
ALTER TABLE raw.entrega_anuncio_dia ADD COLUMN IF NOT EXISTS conjunto TEXT;
ALTER TABLE raw.entrega_anuncio_dia ADD COLUMN IF NOT EXISTS anuncio TEXT;
ALTER TABLE raw.entrega_anuncio_dia ADD COLUMN IF NOT EXISTS ad_id TEXT;
ALTER TABLE raw.entrega_anuncio_dia ADD COLUMN IF NOT EXISTS firma TEXT;
ALTER TABLE raw.entrega_anuncio_dia ADD COLUMN IF NOT EXISTS angulo_key TEXT;
ALTER TABLE raw.entrega_anuncio_dia ADD COLUMN IF NOT EXISTS concepto_key TEXT;
ALTER TABLE raw.entrega_anuncio_dia ADD COLUMN IF NOT EXISTS canonico_id TEXT;
ALTER TABLE raw.entrega_anuncio_dia ADD COLUMN IF NOT EXISTS nivel_conciencia TEXT;
ALTER TABLE raw.entrega_anuncio_dia ADD COLUMN IF NOT EXISTS oferta_key TEXT;
ALTER TABLE raw.entrega_anuncio_dia ADD COLUMN IF NOT EXISTS destino_key TEXT;
ALTER TABLE raw.entrega_anuncio_dia ADD COLUMN IF NOT EXISTS mensajes TEXT;
ALTER TABLE raw.entrega_anuncio_dia ADD COLUMN IF NOT EXISTS clicks_totales TEXT;
ALTER TABLE raw.entrega_anuncio_dia ADD COLUMN IF NOT EXISTS link_clicks TEXT;
ALTER TABLE raw.entrega_anuncio_dia ADD COLUMN IF NOT EXISTS impresiones TEXT;
ALTER TABLE raw.entrega_anuncio_dia ADD COLUMN IF NOT EXISTS spend_usd TEXT;
ALTER TABLE raw.entrega_anuncio_dia ADD COLUMN IF NOT EXISTS pct_conv_clic_enlace TEXT;
ALTER TABLE raw.entrega_anuncio_dia ADD COLUMN IF NOT EXISTS fuente TEXT;

-- venta <- PRODUCTOS/_FACT_VENTAS.csv
CREATE TABLE IF NOT EXISTS raw.venta (
    id BIGSERIAL PRIMARY KEY,
    tenant_id TEXT NOT NULL DEFAULT 'vitalcom',
    ventana_ini TEXT,
    ventana_fin TEXT,
    dias TEXT,
    rol_ventana TEXT,
    producto_key TEXT,
    producto TEXT,
    cuenta_id TEXT,
    cuenta_alias TEXT,
    campana TEXT,
    conjunto TEXT,
    anuncio TEXT,
    mensajes TEXT,
    clicks TEXT,
    impresiones TEXT,
    spend_usd TEXT,
    ventas TEXT,
    total_q TEXT,
    moneda_origen TEXT,
    fuente TEXT,
    ad_id TEXT,
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
ALTER TABLE raw.venta ADD COLUMN IF NOT EXISTS ventana_ini TEXT;
ALTER TABLE raw.venta ADD COLUMN IF NOT EXISTS ventana_fin TEXT;
ALTER TABLE raw.venta ADD COLUMN IF NOT EXISTS dias TEXT;
ALTER TABLE raw.venta ADD COLUMN IF NOT EXISTS rol_ventana TEXT;
ALTER TABLE raw.venta ADD COLUMN IF NOT EXISTS producto_key TEXT;
ALTER TABLE raw.venta ADD COLUMN IF NOT EXISTS producto TEXT;
ALTER TABLE raw.venta ADD COLUMN IF NOT EXISTS cuenta_id TEXT;
ALTER TABLE raw.venta ADD COLUMN IF NOT EXISTS cuenta_alias TEXT;
ALTER TABLE raw.venta ADD COLUMN IF NOT EXISTS campana TEXT;
ALTER TABLE raw.venta ADD COLUMN IF NOT EXISTS conjunto TEXT;
ALTER TABLE raw.venta ADD COLUMN IF NOT EXISTS anuncio TEXT;
ALTER TABLE raw.venta ADD COLUMN IF NOT EXISTS mensajes TEXT;
ALTER TABLE raw.venta ADD COLUMN IF NOT EXISTS clicks TEXT;
ALTER TABLE raw.venta ADD COLUMN IF NOT EXISTS impresiones TEXT;
ALTER TABLE raw.venta ADD COLUMN IF NOT EXISTS spend_usd TEXT;
ALTER TABLE raw.venta ADD COLUMN IF NOT EXISTS ventas TEXT;
ALTER TABLE raw.venta ADD COLUMN IF NOT EXISTS total_q TEXT;
ALTER TABLE raw.venta ADD COLUMN IF NOT EXISTS moneda_origen TEXT;
ALTER TABLE raw.venta ADD COLUMN IF NOT EXISTS fuente TEXT;
ALTER TABLE raw.venta ADD COLUMN IF NOT EXISTS ad_id TEXT;

-- evento <- PRODUCTOS/_EVENTOS.csv
CREATE TABLE IF NOT EXISTS raw.evento (
    id BIGSERIAL PRIMARY KEY,
    tenant_id TEXT NOT NULL DEFAULT 'vitalcom',
    fecha TEXT,
    producto_key TEXT,
    cuenta_alias TEXT,
    campana_clave TEXT,
    conjunto_meta TEXT,
    evento TEXT,
    valor_antes TEXT,
    valor_despues TEXT,
    motivo TEXT,
    fuente_decision TEXT,
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
ALTER TABLE raw.evento ADD COLUMN IF NOT EXISTS fecha TEXT;
ALTER TABLE raw.evento ADD COLUMN IF NOT EXISTS producto_key TEXT;
ALTER TABLE raw.evento ADD COLUMN IF NOT EXISTS cuenta_alias TEXT;
ALTER TABLE raw.evento ADD COLUMN IF NOT EXISTS campana_clave TEXT;
ALTER TABLE raw.evento ADD COLUMN IF NOT EXISTS conjunto_meta TEXT;
ALTER TABLE raw.evento ADD COLUMN IF NOT EXISTS evento TEXT;
ALTER TABLE raw.evento ADD COLUMN IF NOT EXISTS valor_antes TEXT;
ALTER TABLE raw.evento ADD COLUMN IF NOT EXISTS valor_despues TEXT;
ALTER TABLE raw.evento ADD COLUMN IF NOT EXISTS motivo TEXT;
ALTER TABLE raw.evento ADD COLUMN IF NOT EXISTS fuente_decision TEXT;

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
-- mercado (GT/CO, _DIM_MERCADOS.csv): una base que ya tenia core.producto no lo recibe por el CREATE.
ALTER TABLE core.producto ADD COLUMN IF NOT EXISTS mercado TEXT;

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


