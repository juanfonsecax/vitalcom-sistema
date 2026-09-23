-- El diccionario cerrado de los ejes (PRODUCTOS/_DIM_VOCABULARIO.csv, Ads/_TOOLS/gen_vocabulario.py
-- es el unico escritor). Un test que valida un vocabulario cerrado lee de aca -- nunca repite la
-- lista de valores en _models.yml, que seria una segunda version de la misma verdad
-- (g07-cimientos T2, 22-sep-2026: asi se rompio el `accepted_values` de `estado` contra NUEVO).
select
    trim(v.eje)                    as eje,
    trim(v.valor)                  as valor,
    trim(v.etiqueta)               as etiqueta,
    nullif(trim(v.tipo_eje),'')    as tipo_eje,
    nullif(trim(v.mapea_a),'')     as mapea_a
from {{ source('csv','vocabulario') }} v
where nullif(trim(v.eje),'') is not null
