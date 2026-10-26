select 'staging lost or multiplied source rows' as failure
where (select count(*) from {{ ref('stg_complaints') }})
   <> (select count(*) from {{ source('fcc', 'complaints') }})
