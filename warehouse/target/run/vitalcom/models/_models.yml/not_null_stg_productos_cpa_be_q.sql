
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select cpa_be_q
from (select * from "vitalcom"."main"."stg_productos" where estado = 'VIVO') dbt_subquery
where cpa_be_q is null



  
  
      
    ) dbt_internal_test