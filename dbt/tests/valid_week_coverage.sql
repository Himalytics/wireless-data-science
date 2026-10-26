select * from {{ ref('weekly_wireless_issues') }}
where covered_days not between 1 and 7
   or is_complete_week <> (covered_days = 7)
