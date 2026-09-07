
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select producto_key
from "vitalcom"."main"."stg_entrega_conjunto"
where producto_key is null



  
  
      
    ) dbt_internal_test