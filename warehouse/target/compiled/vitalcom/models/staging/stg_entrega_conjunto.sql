-- Entrega diaria por conjunto. El conjunto llega YA canonizado: cualquier consumidor aguas
-- abajo ve un solo objeto por conjunto real, se haya renombrado o no.
with e as (
    select * from read_csv('../PRODUCTOS/_FACT_ENTREGA.csv', header=true, all_varchar=true)
)
select
    cast(e.ventana_ini as date)                       as fecha_ini,
    cast(e.ventana_fin as date)                       as fecha_fin,
    cast(e.dias as integer)                           as dias,
    trim(e.producto_key)                              as producto_key,
    trim(e.cuenta_alias)                              as cuenta_alias,
    trim(e.campana)                                   as campana,
    coalesce(a.nombre_nuevo, trim(e.conjunto))        as conjunto,
    trim(e.conjunto)                                  as conjunto_crudo,
    cast(e.mensajes as double)                        as mensajes,
    cast(e.link_clicks as double)                     as link_clicks,
    cast(e.impresiones as double)                     as impresiones,
    cast(e.spend_usd as double)                       as spend_usd,
    trim(e.fuente)                                    as fuente
from e
left join "vitalcom"."main"."stg_alias" a on trim(e.conjunto) = a.nombre_viejo