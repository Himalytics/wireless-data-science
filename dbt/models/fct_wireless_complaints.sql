select *
from {{ ref('stg_complaints') }}
where issue_type in ('Phone', 'Internet')
  and lower(method) like 'wireless%'
