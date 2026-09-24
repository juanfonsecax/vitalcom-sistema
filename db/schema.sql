-- schema.sql — generado por db/tables.py (2026-09-23). DDL idempotente, esquema core.
-- Un dato, un dueño: cada tabla es un espejo verbatim de su CSV en PRODUCTOS/,
-- más tenant_id (single tenant 'vitalcom') e id. Ver tables.py para el porqué.

CREATE SCHEMA IF NOT EXISTS core;

CREATE TABLE IF NOT EXISTS core.raw_import (
    id BIGSERIAL PRIMARY KEY,
    tenant_id TEXT NOT NULL DEFAULT 'vitalcom',
    archivo TEXT NOT NULL,
    sha256 TEXT,
    filas INTEGER NOT NULL DEFAULT 0,
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS core.decision (
    id BIGSERIAL PRIMARY KEY,
    tenant_id TEXT NOT NULL DEFAULT 'vitalcom',
    fecha TEXT,
    payload JSONB NOT NULL,
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- producto <- PRODUCTOS/_DIM_PRODUCTOS.csv
CREATE TABLE IF NOT EXISTS core.producto (
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
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- costeo <- PRODUCTOS/_DIM_COSTEO.csv
CREATE TABLE IF NOT EXISTS core.costeo (
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

-- conjunto <- PRODUCTOS/_DIM_CONJUNTOS.csv
CREATE TABLE IF NOT EXISTS core.conjunto (
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

-- creativo <- PRODUCTOS/_DIM_CREATIVOS.csv
CREATE TABLE IF NOT EXISTS core.creativo (
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

-- voz_cliente <- PRODUCTOS/_VOZ_CLIENTE.csv
CREATE TABLE IF NOT EXISTS core.voz_cliente (
    id BIGSERIAL PRIMARY KEY,
    tenant_id TEXT NOT NULL DEFAULT 'vitalcom',
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- dim_bandas <- PRODUCTOS/_DIM_BANDAS.csv
CREATE TABLE IF NOT EXISTS core.dim_bandas (
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

-- conjunto_nombre_hist <- PRODUCTOS/_ALIAS_CONJUNTOS.csv
CREATE TABLE IF NOT EXISTS core.conjunto_nombre_hist (
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

-- dim_bm <- PRODUCTOS/_DIM_BM.csv
CREATE TABLE IF NOT EXISTS core.dim_bm (
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

-- dim_cuentas <- PRODUCTOS/_DIM_CUENTAS.csv
CREATE TABLE IF NOT EXISTS core.dim_cuentas (
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
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- dim_envase <- PRODUCTOS/_DIM_ENVASE.csv
CREATE TABLE IF NOT EXISTS core.dim_envase (
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

-- dim_flujo_bot <- PRODUCTOS/_DIM_FLUJO_BOT.csv
CREATE TABLE IF NOT EXISTS core.dim_flujo_bot (
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

-- dim_gastos <- PRODUCTOS/_DIM_GASTOS.csv
CREATE TABLE IF NOT EXISTS core.dim_gastos (
    id BIGSERIAL PRIMARY KEY,
    tenant_id TEXT NOT NULL DEFAULT 'vitalcom',
    patron TEXT,
    clasificacion TEXT,
    categoria TEXT,
    confirmado_por TEXT,
    fecha TEXT,
    notas TEXT,
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- dim_mercados <- PRODUCTOS/_DIM_MERCADOS.csv
CREATE TABLE IF NOT EXISTS core.dim_mercados (
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

-- dim_precios <- PRODUCTOS/_DIM_PRECIOS.csv
CREATE TABLE IF NOT EXISTS core.dim_precios (
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

-- dim_tarjetas <- PRODUCTOS/_DIM_TARJETAS.csv
CREATE TABLE IF NOT EXISTS core.dim_tarjetas (
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

-- dim_vocabulario <- PRODUCTOS/_DIM_VOCABULARIO.csv
CREATE TABLE IF NOT EXISTS core.dim_vocabulario (
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

-- dim_anuncios <- PRODUCTOS/_DIM_ANUNCIOS.csv
CREATE TABLE IF NOT EXISTS core.dim_anuncios (
    id BIGSERIAL PRIMARY KEY,
    tenant_id TEXT NOT NULL DEFAULT 'vitalcom',
    producto_key TEXT,
    anuncio_norm TEXT,
    anuncio_ejemplo TEXT,
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

-- estado_angulos <- PRODUCTOS/_ESTADO_ANGULOS.csv
CREATE TABLE IF NOT EXISTS core.estado_angulos (
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

-- estado_flujo <- PRODUCTOS/_ESTADO_FLUJO.csv
CREATE TABLE IF NOT EXISTS core.estado_flujo (
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

-- estado_meta <- PRODUCTOS/_ESTADO_META.csv
CREATE TABLE IF NOT EXISTS core.estado_meta (
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

-- fact_facturacion <- PRODUCTOS/_FACT_FACTURACION.csv
CREATE TABLE IF NOT EXISTS core.fact_facturacion (
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

-- fact_facturacion_agregado <- PRODUCTOS/_FACT_FACTURACION_AGREGADO.csv
CREATE TABLE IF NOT EXISTS core.fact_facturacion_agregado (
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

-- fact_pauta_real <- PRODUCTOS/_FACT_PAUTA_REAL.csv
CREATE TABLE IF NOT EXISTS core.fact_pauta_real (
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

-- fact_saldos <- PRODUCTOS/_FACT_SALDOS.csv
CREATE TABLE IF NOT EXISTS core.fact_saldos (
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

-- fact_semanal <- PRODUCTOS/_FACT_SEMANAL.csv
CREATE TABLE IF NOT EXISTS core.fact_semanal (
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
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- mapeo_creativos <- PRODUCTOS/_MAPEO_CREATIVOS.csv
CREATE TABLE IF NOT EXISTS core.mapeo_creativos (
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

-- parametros_decision <- PRODUCTOS/_PARAMETROS_DECISION.csv
CREATE TABLE IF NOT EXISTS core.parametros_decision (
    id BIGSERIAL PRIMARY KEY,
    tenant_id TEXT NOT NULL DEFAULT 'vitalcom',
    parametro TEXT,
    valor TEXT,
    unidad TEXT,
    dueno TEXT,
    por_que TEXT,
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- parametros_finanzas <- PRODUCTOS/_PARAMETROS_FINANZAS.csv
CREATE TABLE IF NOT EXISTS core.parametros_finanzas (
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

-- parametros_optimizacion <- PRODUCTOS/_PARAMETROS_OPTIMIZACION.csv
CREATE TABLE IF NOT EXISTS core.parametros_optimizacion (
    id BIGSERIAL PRIMARY KEY,
    tenant_id TEXT NOT NULL DEFAULT 'vitalcom',
    parametro TEXT,
    valor TEXT,
    unidad TEXT,
    dueno TEXT,
    por_que TEXT,
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- parametros_publicacion <- PRODUCTOS/_PARAMETROS_PUBLICACION.csv
CREATE TABLE IF NOT EXISTS core.parametros_publicacion (
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

-- tasa_entrega <- PRODUCTOS/_TASA_ENTREGA.csv
CREATE TABLE IF NOT EXISTS core.tasa_entrega (
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

-- testeos <- PRODUCTOS/_TESTEOS.csv
CREATE TABLE IF NOT EXISTS core.testeos (
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

-- clasificacion_anuncios <- PRODUCTOS/_CLASIFICACION_ANUNCIOS.csv
CREATE TABLE IF NOT EXISTS core.clasificacion_anuncios (
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

-- aprendizajes <- PRODUCTOS/_APRENDIZAJES.csv
CREATE TABLE IF NOT EXISTS core.aprendizajes (
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

-- mapa_ad_id_hist <- PRODUCTOS/_MAPA_AD_ID_HIST.csv
CREATE TABLE IF NOT EXISTS core.mapa_ad_id_hist (
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
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- entrega_conjunto_dia <- PRODUCTOS/_FACT_ENTREGA.csv
CREATE TABLE IF NOT EXISTS core.entrega_conjunto_dia (
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

-- entrega_anuncio_dia <- PRODUCTOS/_FACT_ENTREGA_ANUNCIO.csv
CREATE TABLE IF NOT EXISTS core.entrega_anuncio_dia (
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

-- venta <- PRODUCTOS/_FACT_VENTAS.csv
CREATE TABLE IF NOT EXISTS core.venta (
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
    ad_id_resuelto TEXT,
    metodo_atribucion TEXT,
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- evento <- PRODUCTOS/_EVENTOS.csv
CREATE TABLE IF NOT EXISTS core.evento (
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

-- Vista de conveniencia: ángulos distintos ya presentes en `conjunto`
-- (_DIM_CONJUNTOS.csv). No es una tabla física — nada la carga ni la exporta;
-- ver la nota en tables.py sobre por qué `angulo` no es tabla en P1.
CREATE OR REPLACE VIEW core.angulo AS
SELECT DISTINCT tenant_id, producto_key, angulo_key, angulo_nombre, avatar,
       dolor_nucleo, emocion_dominante, avatar_edad, avatar_genero,
       nivel_conciencia, NULL::text AS deseo
FROM core.conjunto
WHERE angulo_key IS NOT NULL AND angulo_key <> '';

