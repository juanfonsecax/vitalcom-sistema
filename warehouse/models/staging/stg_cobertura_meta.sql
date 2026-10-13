-- ESPEJO SQL de Ads/_TOOLS/gasto.py:_cobertura_meta. Si la regla cambia, cambia en los DOS lugares.
--
-- (cuenta_id, dia) que Meta cubre al decidir si LucidSales puede aportar gasto. La API directa se
-- consulta cuenta por cuenta y dia por dia y solo devuelve anuncios con entrega: un dia en que ALGUNA
-- cuenta tiene filas de la API fue consultado para TODAS las cuentas que la API cubre, asi que si una
-- de ellas no tiene filas ese dia, no gasto. Una cuenta que la API nunca consulto no esta cubierta.
-- A eso se suman los dias de cualquier otra fila de Meta vigente (no superada).
with api as (
    select cuenta_id, fecha_ini, fecha_fin
    from {{ ref('stg_entrega_conjunto') }}
    where fuente = 'MetaAPI-directo'
),
cuentas_api as (select distinct cuenta_id from api where cuenta_id <> ''),
dias_api as (
    select distinct cast(unnest(generate_series(fecha_ini, fecha_fin, interval 1 day)) as date) as dia
    from api
),
otras as (
    select distinct cuenta_id,
           cast(unnest(generate_series(fecha_ini, fecha_fin, interval 1 day)) as date) as dia
    from {{ ref('stg_entrega_conjunto') }}
    where fuente in ('MetaAPI-directo', 'AdsManager-export-1d') and not superada_por_api
)
select c.cuenta_id, d.dia from cuentas_api c cross join dias_api d
union
select cuenta_id, dia from otras
