
    
    

select
    producto_key as unique_field,
    count(*) as n_records

from "vitalcom"."main"."stg_productos"
where producto_key is not null
group by producto_key
having count(*) > 1


