# Dataset card

## Publisher, licence and access

- Publisher: Federal Communications Commission, Consumer Inquiries and Complaints Division.
- Dataset: CGB - Consumer Complaints Data; Socrata ID `3xyp-aqkj`.
- [Authoritative landing page](https://opendata.fcc.gov/Consumer/CGB-Consumer-Complaints-Data/3xyp-aqkj).
- [Authoritative metadata/schema](https://opendata.fcc.gov/api/views/3xyp-aqkj.json).
- [Data.gov catalogue and licence](https://catalog.data.gov/dataset/cgb-consumer-complaints-data).
- Licence: Public Domain U.S. Government, metadata ID `USGOV_WORKS`; catalogue links to https://www.usa.gov/government-works. Attribute the FCC as the source.
- Automated access: `download_data.py`, public Socrata resource endpoint; exact URL-encoded SoQL queries, UTC retrieval timestamp, source update metadata and SHA-256 hashes in `results/source_manifest.json`.

## Unit, scope and dates

Source unit: one submitted consumer complaint ticket. Selected scope: `issue_type='Phone'`, with method either `Wireless (cell phone/other mobile device)` or `Wireless`. The latter rare spelling is explicitly included. Other service forms and methods are outside the target. No provider filter, geographic population join or customer join is performed.

Use `ticket_created`, explicitly described by the publisher as submission date, converted to the UTC calendar day. Filter January 1, 2018 00:00 UTC inclusive through October 26, 2026 00:00 UTC exclusive. The one-week buffer before the November 2 analysis reduces immediate recency exposure but is not a validated reporting-lag adjustment. `issue_date` describes the alleged incident and is not used.

The `date_created` calendar field has no source description. It disagrees with the UTC submission day for 118,111 selected records. Disagreement may reflect timezone conventions; no claim is made that these records are incorrect. See the [audit-led protocol amendment](PROTOCOL_AMENDMENT.md).

API output grain: UTC submission day and issue label, with `count(*)` and `count(distinct id)`. The study downloads anonymous counts only. The source's phone numbers, locations and identifiers are not included in the release.

Model unit: one Monday-Sunday UTC week. All issues, including Unwanted Calls, form the primary target. A sensitivity excludes exactly `issue='Unwanted Calls'`; other issue labels remain. It should therefore be called 'excluding Unwanted Calls', not assumed to be a clean service-failure target.

## Measured audit

| Check | Result |
|---|---:|
| Selected distinct complaints | 1,259,229 |
| Daily issue groups | 25,888 |
| Complete calendar weeks | 460 |
| Duplicate ticket IDs in selected scope | 0 |
| Null submission timestamps, all-time selected form/method scope | 0 |
| Absent UTC submission days in selected window | 8 |
| Share labelled Unwanted Calls | 61.64% |

Counts of distinct IDs within daily issue groups and across the selected source scope match row counts. This checks source ticket duplication, not whether multiple tickets represent the same incident or person. Absent days are reindexed to zero; there is no independent ingestion-uptime evidence. No weeks are dropped. The comparison includes all 52 evaluation weeks and all four horizons.

Seven weekly totals are below 100, in January 2019 and October-November 2025. Their cause is unknown; they are not treated as verified changes in consumer experience. A post-hoc score sensitivity excludes the two such target weeks in final evaluation, retaining original training histories and unchanged primary results. This cannot repair unknown reporting availability or revisions.

## Identity and reproduction

The live raw aggregate and audit responses are cached under ignored `data/raw/`. The release commits the anonymous daily aggregate at `results/source_daily_issue_counts.csv` and source audit responses at `results/source_audit.json`. The CSV's SHA-256 is recorded in the source manifest. `study.py --snapshot` validates that hash, reconstructs weekly counts, and repeats the entire modelling study without source access. The CSV representation differs from API JSON bytes; both identities are retained rather than incorrectly equating their hashes.

## Limits

The FCC states that these are consumer-selected reports and it does not verify the alleged facts. The sample is not representative of all wireless subscribers. Reporting propensity, awareness, reporting campaigns, spam and operational changes can alter counts. No denominator, linked subscribers, carrier effects or causality can be inferred.

This extract was retrieved November 2, 2026. It contains historical submission timestamps, but not historical snapshots or reliable record-publication times. Backtests use current revised history. Training-boundary checks do not prove the exact data were available at each historical origin. A prospective snapshot collection process is needed before claiming real-time forecasting performance.
