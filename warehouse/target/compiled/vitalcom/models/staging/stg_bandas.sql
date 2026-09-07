-- La banda de edad REALMENTE configurada en Meta, contra la que manda la doctrina.
select
    trim(cuenta_alias)                                as cuenta_alias,
    coalesce(a.nombre_nuevo, trim(b.conjunto_meta))   as conjunto,
    trim(b.producto_key)                              as producto_key,
    trim(b.angulo_key)                                as angulo_key,
    trim(b.banda_configurada)                         as banda_configurada,
    trim(b.avatar_edad_doctrina)                      as banda_doctrina,
    upper(trim(b.coincide)) = 'SI'                    as coincide
from read_csv('../PRODUCTOS/_DIM_BANDAS.csv', header=true, all_varchar=true) b
left join "vitalcom"."main"."stg_alias" a on trim(b.conjunto_meta) = a.nombre_viejo