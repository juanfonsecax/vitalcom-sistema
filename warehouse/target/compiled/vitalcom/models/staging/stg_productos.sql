-- El registro maestro. producto_key es la llave del sistema (invariante 10).
select
    trim(producto_key)                                as producto_key,
    trim(nombre_display)                              as nombre,
    upper(trim(estado))                               as estado,
    nullif(upper(trim(fase)),'')                      as fase,
    nullif(trim(cuenta_alias),'')                     as cuenta_alias,
    cast(nullif(trim(cpa_be_q),'') as double)         as cpa_be_q,
    cast(nullif(trim(cpa_base_q),'') as double)       as cpa_base_q,
    cast(nullif(trim(precio_base_q),'') as double)    as precio_base_q,
    nullif(trim(page_id),'')                          as page_id,
    nullif(trim(campaign_id),'')                      as campaign_id
from read_csv('../PRODUCTOS/_DIM_PRODUCTOS.csv', header=true, all_varchar=true)
where nullif(trim(producto_key),'') is not null