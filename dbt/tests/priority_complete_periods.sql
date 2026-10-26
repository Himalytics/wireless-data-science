select p.* from {{ ref('issue_priorities') }} p
where (select count(*) from {{ ref('dim_covered_dates') }} d
       where d.week_start = p.week_start) <> 7
   or (select count(*) from {{ ref('dim_covered_dates') }} d
       where d.week_start = p.week_start - interval 7 day) <> 7
