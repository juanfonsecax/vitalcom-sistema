
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select ventas
from "vitalcom"."main"."stg_ventas"
where ventas is null



  
  
      
    ) dbt_internal_test