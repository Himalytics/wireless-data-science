# FCC dataset card

The FCC Consumer and Governmental Affairs Bureau publishes [CGB Consumer Complaints Data](https://opendata.fcc.gov/Consumer/CGB-Consumer-Complaints-Data/3xyp-aqkj). Metadata ID `3xyp-aqkj` declares U.S. Government public domain (`USGOV_WORKS`). The [frozen input manifest](data/source_manifest.json) records the November 16, 2026 UTC retrieval, source revision indicator, API queries, response hashes, and aggregate CSV SHA-256.

`source.py` requests server-side aggregates only. Filters include `issue_type=Phone` and wireless method labels `Wireless` and `Wireless (cell phone/other mobile device)`. The documented `ticket_created` timestamp sets UTC submission day. `issue` provides an exact Unwanted Calls label for the exclusion sensitivity. Aggregation avoids downloading ticket-level identifiers or geography. A separate distinct-ID count verifies that the total does not include duplicate IDs within scope.

The snapshot reconciles **1,280,589 distinct reports** across **462 complete Monday–Sunday weeks**, January 1, 2018 through November 8, 2026. Eight calendar days with no returned aggregate contribute zero to the as-published count. The presence flag preserves this distinction. A missing day can reflect missing or delayed publication, so the zeros do not establish an absence of complaints.

The publisher does not verify every submitted allegation. Reporting is self-selected, geographic and carrier comparisons lack suitable denominators, and data can be delayed or revised. We have one current snapshot and cannot reconstruct the exact data available on past forecast dates. Neither observed counts nor their intervals measure subscriber churn, population risk, or a carrier's actual support queue.
