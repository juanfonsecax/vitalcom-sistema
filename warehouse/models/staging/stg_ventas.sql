-- Ventas por dia. FUENTE DE VERDAD de la venta (LucidSales); Meta solo aporta entrega.
with v as (
    select * from {{ source('csv','ventas') }}
)
select
    cast(v.ventana_ini as date)                       as fecha_ini,
    cast(v.ventana_fin as date)                       as fecha,
    trim(v.producto_key)                              as producto_key,
    regexp_replace(trim(v.cuenta_id), '[.]0$', '')    as cuenta_id,   -- exports viejos: '123.0' == '123'
    trim(v.cuenta_alias)                              as cuenta_alias,
    trim(v.campana)                                   as campana,
    coalesce(a.nombre_nuevo, trim(v.conjunto))        as conjunto,
    nullif(trim(v.anuncio),'')                        as anuncio,
    nullif(trim(v.ad_id),'')                          as ad_id,
    cast(v.ventas as double)                          as ventas,
    cast(v.mensajes as double)                        as mensajes,
    cast(v.spend_usd as double)                       as spend_usd_lucidsales,
    cast(nullif(trim(v.total_q),'') as double)        as total_q
from v
left join {{ ref('stg_alias') }} a on trim(v.conjunto) = a.nombre_viejo
where nullif(trim(v.conjunto),'') is not null
  and trim(v.conjunto) <> 'SIN_ATRIBUCION'
  -- BASE suma; CONTROL solapa a proposito para auditar y nunca suma (DATA_PLAYBOOK).
  and upper(coalesce(nullif(trim(v.rol_ventana),''),'BASE')) = 'BASE'
