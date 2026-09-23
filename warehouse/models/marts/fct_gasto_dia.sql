-- ESPEJO SQL de Ads/_TOOLS/gasto.py (g07-cimientos T2, 22-sep-2026). Ver su docstring completo:
-- esto es la MISMA regla traducida a SQL -- si la regla cambia, cambia en los DOS lugares.
--
-- Grano: una fila por fila de stg_ventas (LucidSales), con `spend_usd` reemplazado por el de
-- Meta cuando hay cobertura para esa (cuenta_id, ventana). REGLA, en ese orden (nunca se
-- inventa plata -- invariante 2):
--   1. ad_id exacto contra stg_entrega_anuncio (cuenta_id + ventana + ad_id)
--   2. nombre exacto (cuenta_id + ventana + conjunto + anuncio) contra stg_entrega_anuncio
--   3. grano conjunto (cuenta_id + ventana + conjunto) contra stg_entrega_conjunto -- la MISMA
--      plata real cuando el anuncio individual no aparece en el export de ese dia
--   4. fallback: spend_usd_lucidsales de la propia fila (dias sin pull de Meta, antes de
--      2026-09-06, o un pull fallido)
--
-- Solo cuenta como Meta una fila cuya `fuente` sea MetaAPI-directo o AdsManager-export-1d (ver
-- gasto.FUENTES_META en el espejo Python) -- una siembra manual nunca gana sobre el fallback.
with fuentes_meta as (
    select unnest(['MetaAPI-directo', 'AdsManager-export-1d']) as fuente
),
ventana_ad as (
    select cuenta_id, fecha_ini, fecha_fin, ad_id, sum(spend_usd) as spend_usd
    from {{ ref('stg_entrega_anuncio') }}
    where fuente in (select fuente from fuentes_meta) and ad_id is not null
    group by 1, 2, 3, 4
),
ventana_nombre as (
    select cuenta_id, fecha_ini, fecha_fin, conjunto, anuncio, sum(spend_usd) as spend_usd
    from {{ ref('stg_entrega_anuncio') }}
    where fuente in (select fuente from fuentes_meta)
    group by 1, 2, 3, 4, 5
),
ventana_conjunto as (
    select cuenta_id, fecha_ini, fecha_fin, conjunto, sum(spend_usd) as spend_usd
    from {{ ref('stg_entrega_conjunto') }}
    where fuente in (select fuente from fuentes_meta)
    group by 1, 2, 3, 4
)
select
    v.*,
    coalesce(ad.spend_usd, nom.spend_usd, conj.spend_usd, v.spend_usd_lucidsales) as spend_usd,
    case
        when ad.spend_usd is not null   then 'MetaAPI-ad_id'
        when nom.spend_usd is not null  then 'MetaAPI-nombre'
        when conj.spend_usd is not null then 'MetaAPI-conjunto'
        else 'LucidSales-fallback'
    end as fuente_gasto
from {{ ref('stg_ventas') }} v
left join ventana_ad ad
       on ad.cuenta_id = v.cuenta_id and ad.fecha_ini = v.fecha_ini and ad.fecha_fin = v.fecha
      and ad.ad_id = v.ad_id
left join ventana_nombre nom
       on nom.cuenta_id = v.cuenta_id and nom.fecha_ini = v.fecha_ini and nom.fecha_fin = v.fecha
      and nom.conjunto = v.conjunto and nom.anuncio = v.anuncio
left join ventana_conjunto conj
       on conj.cuenta_id = v.cuenta_id and conj.fecha_ini = v.fecha_ini and conj.fecha_fin = v.fecha
      and conj.conjunto = v.conjunto
