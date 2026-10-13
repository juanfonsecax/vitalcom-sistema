-- ESPEJO SQL de Ads/_TOOLS/upsert_fact.py:superar_por_api_directa (T5, 13-oct-2026).
-- Si la regla cambia, cambia en los DOS lugares.
--
-- Para una misma CUENTA y un mismo DIA manda la fuente 'MetaAPI-directo': toda fila de otra fuente
-- (export de Ads Manager, MCP) cuyos dias la API cubre por completo describe el mismo gasto con
-- otro nombre de conjunto o de ventana y queda marcada `superada_por_api`. Una ventana multidia
-- cubierta solo en parte NO se marca (es un agregado, no se parte). Un dia sin filas de la API
-- entre dos dias con filas de la misma cuenta, a menos de 8 dias de distancia (hueco de hasta 7),
-- es un dia sin gasto propio y cuenta como cubierto (MAX_HUECO_DIAS en el script).
--
-- Devuelve la relacion recibida mas la columna booleana `superada_por_api`. Quien SUMA gasto
-- filtra `not superada_por_api`.
{% macro entrega_con_superada(rel) %}
(
    with base0 as (
        select *, row_number() over () as _rid from {{ rel }}
    ),
    -- una fila sin cuenta_id se atribuye por su alias cuando ese alias apunta a UNA sola cuenta
    mapa_alias as (
        select trim(cuenta_alias) as cuenta_alias, min(trim(cuenta_id)) as cuenta_id
        from base0
        where nullif(trim(cuenta_id), '') is not null
        group by 1
        having count(distinct trim(cuenta_id)) = 1
    ),
    base as (
        select b.*, coalesce(nullif(trim(b.cuenta_id), ''), m.cuenta_id) as _cuenta
        from base0 b
        left join mapa_alias m on trim(b.cuenta_alias) = m.cuenta_alias
    ),
    api_dias as (
        select distinct _cuenta as cuenta_id,
               cast(unnest(generate_series(cast(ventana_ini as date), cast(ventana_fin as date), interval 1 day)) as date) as dia
        from base
        where trim(fuente) = 'MetaAPI-directo'
    ),
    api_sig as (
        select cuenta_id, dia, lead(dia) over (partition by cuenta_id order by dia) as sig
        from api_dias
    ),
    api_cubiertos as (
        select cuenta_id, dia from api_dias
        union
        select cuenta_id, cast(unnest(generate_series(dia + 1, sig - 1, interval 1 day)) as date) as dia
        from api_sig
        where sig is not null and sig - dia between 2 and 8
    ),
    filas_dias as (
        select _rid, _cuenta as cuenta_id,
               cast(unnest(generate_series(cast(ventana_ini as date), cast(ventana_fin as date), interval 1 day)) as date) as dia
        from base
        where trim(fuente) <> 'MetaAPI-directo'
    ),
    superadas as (
        select f._rid
        from filas_dias f
        left join api_cubiertos c on c.cuenta_id = f.cuenta_id and c.dia = f.dia
        group by f._rid
        having count(*) = count(c.dia)
    )
    select b.* exclude (_rid, _cuenta), (b._rid in (select _rid from superadas)) as superada_por_api
    from base b
)
{% endmacro %}
