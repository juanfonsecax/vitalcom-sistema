-- Una cuenta-dia con gasto vigente (no superado) viene de UNA sola fuente de Meta de 1 dia, o de
-- ventanas multidia que no se solapan con otra fuente. Devuelve las cuenta-dia con dos o mas
-- fuentes vigentes: cada fila devuelta es un doble conteo.
with dias as (
    select cuenta_id, cast(unnest(generate_series(fecha_ini, fecha_fin, interval 1 day)) as date) as dia, fuente
    from {{ ref('stg_entrega_conjunto') }}
    where not superada_por_api and fuente in ('MetaAPI-directo', 'AdsManager-export-1d')
)
select cuenta_id, dia, count(distinct fuente) as fuentes
from dias
group by 1, 2
having count(distinct fuente) > 1
