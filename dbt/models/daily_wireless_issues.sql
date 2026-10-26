select complaint_date, state, issue_type, issue,
       count(*)::bigint as complaint_count
from {{ ref('fct_wireless_complaints') }}
group by 1, 2, 3, 4
