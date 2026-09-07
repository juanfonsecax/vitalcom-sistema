-- Entrega diaria por ANUNCIO, con los 5 ejes que viajan en la firma del nombre.
-- Sin este grano el eje CONCEPTO es inobservable y la FASE 2 no mide nada.
with e as (
    select * from read_csv('../PRODUCTOS/_FACT_ENTREGA_ANUNCIO.csv', header=true, all_varchar=true)
)
select
    cast(e.ventana_ini as date)                       as fecha_ini,
    cast(e.ventana_fin as date)                       as fecha_fin,
    trim(e.producto_key)                              as producto_key,
    trim(e.cuenta_alias)                              as cuenta_alias,
    trim(e.campana)                                   as campana,
    coalesce(a.nombre_nuevo, trim(e.conjunto))        as conjunto,
    trim(e.anuncio)                                   as anuncio,
    nullif(trim(e.firma),'')                          as firma,
    nullif(trim(e.angulo_key),'')                     as angulo_key,
    nullif(trim(e.concepto_key),'')                   as concepto_key,
    nullif(trim(e.canonico_id),'')                    as canonico_id,
    nullif(trim(e.nivel_conciencia),'')               as nivel_conciencia,
    nullif(trim(e.oferta_key),'')                     as oferta_key,
    nullif(trim(e.destino_key),'')                    as destino_key,
    cast(e.mensajes as double)                        as mensajes,
    cast(e.link_clicks as double)                     as link_clicks,
    cast(e.impresiones as double)                     as impresiones,
    cast(e.spend_usd as double)                       as spend_usd,
    (nullif(trim(e.firma),'') is not null)            as tiene_firma
from e
left join "vitalcom"."main"."stg_alias" a on trim(e.conjunto) = a.nombre_viejo