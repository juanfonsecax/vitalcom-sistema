
    

    create  table
      "vitalcom"."main"."fct_anuncio_dia__dbt_tmp"
  
    
    as (
      -- El hecho diario por ANUNCIO con sus 5 ejes. Es el grano donde vive el CONCEPTO.
-- Solo tiene ENTREGA: la venta no llega a nivel anuncio de forma confiable (el ad_id de
-- _FACT_VENTAS.csv esta corrupto en 2006 de 2475 filas). Sirve para leer entrega por eje,
-- no para declarar ganadores: eso se hace por VENTA agregando por angulo_key.
select
    fecha_fin as fecha,
    producto_key,
    cuenta_alias,
    conjunto,
    anuncio,
    firma,
    angulo_key,
    concepto_key,
    canonico_id,
    nivel_conciencia,
    oferta_key,
    destino_key,
    tiene_firma,
    sum(mensajes)    as mensajes,
    sum(link_clicks) as link_clicks,
    sum(impresiones) as impresiones,
    sum(spend_usd)   as spend_usd
from "vitalcom"."main"."stg_entrega_anuncio"
group by 1,2,3,4,5,6,7,8,9,10,11,12,13
    );
    
  