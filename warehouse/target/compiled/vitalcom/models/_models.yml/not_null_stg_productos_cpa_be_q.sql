
    
    



select cpa_be_q
from (select * from "vitalcom"."main"."stg_productos" where estado = 'VIVO') dbt_subquery
where cpa_be_q is null


