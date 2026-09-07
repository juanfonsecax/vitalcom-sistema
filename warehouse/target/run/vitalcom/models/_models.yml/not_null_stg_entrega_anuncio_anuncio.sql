
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select anuncio
from "vitalcom"."main"."stg_entrega_anuncio"
where anuncio is null



  
  
      
    ) dbt_internal_test