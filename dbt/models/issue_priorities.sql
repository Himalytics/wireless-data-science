-- Compare consecutive complete calendar weeks, not merely adjacent observed rows.
with complete_weeks as (
    select week_start
    from {{ ref('dim_covered_dates') }}
    group by 1 having count(*) = 7
), eligible as (
    select max(a.week_start) as week_start
    from complete_weeks a
    join complete_weeks b on b.week_start = a.week_start - interval 7 day
), issues as (
    select distinct issue from {{ ref('fct_wireless_complaints') }}
), compared as (
    select e.week_start, i.issue,
           coalesce(c.complaint_count, 0)::bigint as current_complaints,
           coalesce(p.complaint_count, 0)::bigint as previous_complaints
    from eligible e cross join issues i
    left join {{ ref('weekly_wireless_issues') }} c
      on c.week_start = e.week_start and c.issue = i.issue
    left join {{ ref('weekly_wireless_issues') }} p
      on p.week_start = e.week_start - interval 7 day and p.issue = i.issue
    where e.week_start is not null
)
select *, current_complaints - previous_complaints as change_in_complaints,
       case when previous_complaints > 0
            then round(100.0 * (current_complaints - previous_complaints) / previous_complaints, 2)
            else null end as change_pct,
       case when current_complaints >= 20 and current_complaints > previous_complaints
            then 'Investigate increase; validate with independent evidence'
            when current_complaints >= 20 then 'Review high-volume issue'
            else 'Monitor; low volume' end as action
from compared
