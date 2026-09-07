-- El nombre viejo de un conjunto renombrado en Meta -> su nombre canonico.
-- El JOIN del sistema es por NOMBRE (el ad_id llego corrupto en 2006 de 2475 filas y no vuelve),
-- asi que sin esto un renombrado parte la serie historica en dos objetos distintos.
select
    trim(nombre_viejo) as nombre_viejo,
    trim(nombre_nuevo) as nombre_nuevo
from read_csv('../PRODUCTOS/_ALIAS_CONJUNTOS.csv', header=true, all_varchar=true)
where nullif(trim(nombre_viejo),'') is not null
  and nullif(trim(nombre_nuevo),'') is not null
  and trim(nombre_viejo) <> trim(nombre_nuevo)