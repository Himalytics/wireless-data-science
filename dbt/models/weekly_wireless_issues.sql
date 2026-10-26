with coverage as (
    select week_start, count(*) as covered_days
    from {{ ref('dim_covered_dates') }}
    group by 1
), counts as (
    select date_trunc('week', complaint_date)::date as week_start,
           issue, count(*)::bigint as complaint_count
    from {{ ref('fct_wireless_complaints') }}
    group by 1, 2
)
select counts.*, coverage.covered_days,
       coverage.covered_days = 7 as is_complete_week
from counts
join coverage using (week_start)
