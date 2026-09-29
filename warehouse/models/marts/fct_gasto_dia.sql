-- ESPEJO SQL de Ads/_TOOLS/gasto.py (g07-cimientos T2, 22-sep-2026; rediseñado tras un defecto de
-- conteo encontrado en review). Ver el docstring completo de gasto.py: esto es la MISMA regla
-- traducida a SQL -- si la regla cambia, cambia en los DOS lugares.
--
-- DISEÑO: el gasto de Meta y las ventas de LucidSales se AGREGAN POR SEPARADO a grano
-- (producto_key, cuenta_id, ventana_ini, ventana_fin, conjunto) y se cruzan con un FULL OUTER
-- JOIN. Nunca se resuelve fila por fila: una versión anterior de este modelo hacía un LEFT JOIN
-- por fila contra el conjunto agregado y, si un conjunto tenía N filas de venta sin match
-- individual a nivel anuncio, el JOIN devolvía N copias del mismo spend_usd agregado -- un
-- SUM(spend_usd) posterior sobre esas N filas multiplicaba el gasto real por N. Agregando cada
-- lado ANTES del join, cada dólar de Meta vive en una sola fila de este modelo sin importar
-- cuántas filas de venta o de Meta lo describan por dentro.
with ventas_agg as (
    select
        producto_key, cuenta_id, cuenta_alias, fecha_ini, fecha as fecha_fin, conjunto,
        sum(ventas)                  as ventas,
        sum(mensajes)                as mensajes,
        sum(spend_usd_lucidsales)    as spend_usd_lucidsales,
        sum(total_q)                 as total_q
    from {{ ref('stg_ventas') }}
    group by 1, 2, 3, 4, 5, 6
),
meta_agg as (
    select
        producto_key, cuenta_id, cuenta_alias, fecha_ini, fecha_fin, conjunto,
        sum(spend_usd) as spend_usd
    from {{ ref('stg_entrega_conjunto') }}
    where fuente in ('MetaAPI-directo', 'AdsManager-export-1d')
    group by 1, 2, 3, 4, 5, 6
)
select
    coalesce(v.producto_key, m.producto_key)   as producto_key,
    coalesce(v.cuenta_id, m.cuenta_id)         as cuenta_id,
    coalesce(v.cuenta_alias, m.cuenta_alias)   as cuenta_alias,
    coalesce(v.fecha_ini, m.fecha_ini)         as fecha_ini,
    coalesce(v.fecha_fin, m.fecha_fin)         as fecha_fin,
    coalesce(v.conjunto, m.conjunto)           as conjunto,
    -- mercado del producto (stg_productos, un producto = una fila): spend_usd es USD pero total_q esta en
    -- la moneda LOCAL del mercado; nunca se suma total_q entre mercados distintos.
    p.mercado                                  as mercado,
    coalesce(v.ventas, 0)                      as ventas,
    coalesce(v.mensajes, 0)                    as mensajes,
    coalesce(v.total_q, 0)                     as total_q,
    -- Meta cubre esta celda -> su suma (contada UNA vez); si no, el fallback de LucidSales ya
    -- agregado del lado de ventas_agg. Full outer join: una celda con gasto de Meta y CERO
    -- ventas sigue apareciendo (spend_usd_lucidsales=0 ahí, coalesce a 0 no pierde el gasto de
    -- Meta porque `m.spend_usd` manda primero).
    coalesce(m.spend_usd, v.spend_usd_lucidsales, 0)   as spend_usd,
    coalesce(v.spend_usd_lucidsales, 0)                as spend_usd_lucidsales,
    case when m.spend_usd is not null then 'MetaAPI-conjunto' else 'LucidSales-fallback' end
                                                as fuente_gasto
from ventas_agg v
full outer join meta_agg m
       on v.producto_key = m.producto_key and v.cuenta_id = m.cuenta_id
      and v.fecha_ini = m.fecha_ini and v.fecha_fin = m.fecha_fin and v.conjunto = m.conjunto
left join {{ ref('stg_productos') }} p
       on p.producto_key = coalesce(v.producto_key, m.producto_key)
