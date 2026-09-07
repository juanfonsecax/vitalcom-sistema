
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select nombre_nuevo
from "vitalcom"."main"."stg_alias"
where nombre_nuevo is null



  
  
      
    ) dbt_internal_test