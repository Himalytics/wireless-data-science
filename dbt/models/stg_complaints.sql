{{ config(materialized='view') }}
select complaint_id, complaint_date, issue_type, method, issue, state,
       record_sha256, snapshot_sha256, ingested_at_utc
from {{ source('fcc', 'complaints') }}
