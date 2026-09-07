
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    

select
    producto_key as unique_field,
    count(*) as n_records

from "vitalcom"."main"."stg_productos"
where producto_key is not null
group by producto_key
having count(*) > 1



  
  
      
    ) dbt_internal_test