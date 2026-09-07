
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select spend_usd
from "vitalcom"."main"."stg_entrega_conjunto"
where spend_usd is null



  
  
      
    ) dbt_internal_test