-- Un renglon por conjunto real de Meta, con su angulo derivado del NOMBRE.
-- El angulo sale del nombre y no de una tabla paralela: es lo unico que llega intacto en
-- cualquier export, y es la razon de ser de la CONVENCION DE NOMBRES de ETAPA-6.
with vistos as (
    select distinct conjunto, cuenta_alias, producto_key from "vitalcom"."main"."stg_ventas"
    union
    select distinct conjunto, cuenta_alias, producto_key from "vitalcom"."main"."stg_entrega_conjunto"
),
parseado as (
    select
        v.conjunto,
        v.cuenta_alias,
        v.producto_key,
        regexp_extract(v.conjunto, '^[A-Z0-9]+_[A-Z0-9]+_([A-Z0-9\-]+)_R[0-9]+$', 1) as angulo_del_nombre,
        regexp_extract(v.conjunto, '_R([0-9]+)$', 1)                                 as replica
    from vistos v
)
select
    p.conjunto,
    p.cuenta_alias,
    p.producto_key,
    nullif(replace(p.angulo_del_nombre, '-', '_'), '') as angulo_key,
    cast(nullif(p.replica,'') as integer)              as replica,
    (nullif(p.angulo_del_nombre,'') is not null)       as en_convencion,
    b.banda_configurada,
    b.banda_doctrina,
    b.coincide                                         as banda_coincide
from parseado p
left join "vitalcom"."main"."stg_bandas" b
       on b.conjunto = p.conjunto and b.cuenta_alias = p.cuenta_alias