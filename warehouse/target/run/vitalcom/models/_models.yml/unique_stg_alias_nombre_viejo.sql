
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    

select
    nombre_viejo as unique_field,
    count(*) as n_records

from "vitalcom"."main"."stg_alias"
where nombre_viejo is not null
group by nombre_viejo
having count(*) > 1



  
  
      
    ) dbt_internal_test