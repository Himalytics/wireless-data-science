select day as complaint_date,
       date_trunc('week', day)::date as week_start
from {{ source('operations', 'covered_dates') }}
