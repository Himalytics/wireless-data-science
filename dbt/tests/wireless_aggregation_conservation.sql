select 'wireless aggregation changed total count' as failure
where (select count(*) from {{ ref('fct_wireless_complaints') }})
   <> (select coalesce(sum(complaint_count), 0) from {{ ref('daily_wireless_issues') }})
   or (select count(*) from {{ ref('fct_wireless_complaints') }})
   <> (select coalesce(sum(complaint_count), 0) from {{ ref('weekly_wireless_issues') }})
