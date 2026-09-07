
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    

with all_values as (

    select
        estado as value_field,
        count(*) as n_records

    from "vitalcom"."main"."stg_productos"
    group by estado

)

select *
from all_values
where value_field not in (
    'VIVO','PAUSADO','LISTO','ARCHIVADO'
)



  
  
      
    ) dbt_internal_test