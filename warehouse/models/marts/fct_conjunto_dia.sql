-- El hecho diario por conjunto: gasto, mensajes y VENTAS en la misma fila.
-- La venta manda (LucidSales); Meta solo aporta entrega. Un dia sin fila aqui es un dia sin gasto.
select
    v.fecha,
    v.producto_key,
    v.cuenta_alias,
    v.conjunto,
    d.angulo_key,
    d.replica,
    d.en_convencion,
    d.banda_configurada,
    d.banda_coincide,
    sum(v.ventas)     as ventas,
    sum(v.mensajes)   as mensajes,
    sum(v.spend_usd)  as spend_usd,
    sum(v.total_q)    as total_q
from {{ ref('stg_ventas') }} v
left join {{ ref('dim_conjunto') }} d
       on d.conjunto = v.conjunto and d.cuenta_alias = v.cuenta_alias
group by 1,2,3,4,5,6,7,8,9
