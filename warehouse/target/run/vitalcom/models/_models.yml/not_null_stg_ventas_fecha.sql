
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select fecha
from "vitalcom"."main"."stg_ventas"
where fecha is null



  
  
      
    ) dbt_internal_test