-- El hecho diario por ANUNCIO con sus 5 ejes. Es el grano donde vive el CONCEPTO.
-- Solo tiene ENTREGA: la venta no llega a nivel anuncio de forma confiable (el ad_id de
-- _FACT_VENTAS.csv esta corrupto en 2006 de 2475 filas). Sirve para leer entrega por eje,
-- no para declarar ganadores: eso se hace por VENTA agregando por angulo_key.
select
    a.fecha_fin as fecha,
    a.producto_key,
    p.mercado,
    a.cuenta_alias,
    a.conjunto,
    a.anuncio,
    a.ad_id,
    a.firma,
    a.angulo_key,
    a.concepto_key,
    a.canonico_id,
    a.nivel_conciencia,
    a.oferta_key,
    a.destino_key,
    a.tiene_firma,
    sum(a.mensajes)    as mensajes,
    sum(a.link_clicks) as link_clicks,
    sum(a.impresiones) as impresiones,
    sum(a.spend_usd)   as spend_usd
from {{ ref('stg_entrega_anuncio') }} a
left join {{ ref('stg_productos') }} p on p.producto_key = a.producto_key
where not a.superada_por_api   -- precedencia por fuente: ver macros/entrega_con_superada.sql
group by 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15
