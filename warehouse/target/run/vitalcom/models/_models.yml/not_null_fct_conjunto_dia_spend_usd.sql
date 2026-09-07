
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select spend_usd
from "vitalcom"."main"."fct_conjunto_dia"
where spend_usd is null



  
  
      
    ) dbt_internal_test