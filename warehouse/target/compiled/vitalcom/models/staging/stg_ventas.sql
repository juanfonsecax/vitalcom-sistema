-- Ventas por dia. FUENTE DE VERDAD de la venta (LucidSales); Meta solo aporta entrega.
with v as (
    select * from read_csv('../PRODUCTOS/_FACT_VENTAS.csv', header=true, all_varchar=true)
)
select
    cast(v.ventana_fin as date)                       as fecha,
    trim(v.producto_key)                              as producto_key,
    trim(v.cuenta_alias)                              as cuenta_alias,
    trim(v.campana)                                   as campana,
    coalesce(a.nombre_nuevo, trim(v.conjunto))        as conjunto,
    nullif(trim(v.anuncio),'')                        as anuncio,
    cast(v.ventas as double)                          as ventas,
    cast(v.mensajes as double)                        as mensajes,
    cast(v.spend_usd as double)                       as spend_usd,
    cast(nullif(trim(v.total_q),'') as double)        as total_q
from v
left join "vitalcom"."main"."stg_alias" a on trim(v.conjunto) = a.nombre_viejo
where nullif(trim(v.conjunto),'') is not null
  and trim(v.conjunto) <> 'SIN_ATRIBUCION'