-- Valores vigentes del eje estado_producto (NUEVO/VIVO/PAUSADO/LISTO/ARCHIVADO), aislados en su
-- propio modelo para que `relationships` en _models.yml pueda apuntarle directo -- ese test no
-- acepta un WHERE inline sobre el modelo destino (g07-cimientos T2, 22-sep-2026).
select distinct valor
from {{ ref('stg_vocabulario') }}
where eje = 'estado_producto'
