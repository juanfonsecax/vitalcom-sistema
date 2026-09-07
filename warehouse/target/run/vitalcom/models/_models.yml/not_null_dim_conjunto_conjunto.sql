
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select conjunto
from "vitalcom"."main"."dim_conjunto"
where conjunto is null



  
  
      
    ) dbt_internal_test