
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select nombre_viejo
from "vitalcom"."main"."stg_alias"
where nombre_viejo is null



  
  
      
    ) dbt_internal_test