# Senior data engineering sequence

Himanshu requested a higher difficulty level after finding the baseline easy. Each release must address a substantial correctness, recovery, scaling, deployment, or consumer-contract problem and include measured evidence. A new connector or library alone is insufficient.

Week 1 now includes the original real-data platform and an implemented crash-recovery reference. The next scheduled release must extend that work, not repeat its checkpoints. Keep a two-hour guided entry path and roughly 8-12 further hours of ownership exercises across the week.

| Week | Date | Substantial engineering problem | Required proof |
|---|---|---|---|
| 1 | Oct 26, 2026 | Public FCC data platform plus transactional extraction recovery | Complete real extraction, quality-gated publication, actual SIGKILL recovery, HTTP retries, source-version refusal, replay reconciliation |
| 2 | Nov 2 | Observed version history and incremental/backfill correctness | Real source snapshots; inserted/changed/removed observations; scope-safe deletion handling; corrected-date reconciliation; equivalence to a full rebuild |
| 3 | Nov 9 | Partitioned orchestration, backfills, and competing workers | Bounded concurrency and source request budget; retry safety; stale-owner rejection or an explicitly scoped local prototype; no duplicate publication |
| 4 | Nov 16 | Geographic reference and coverage integration | Verified FCC/Census sources; geographic grain and vintage contracts; unmatched joins, boundary cases, coverage and denominator accounting |
| 5 | Nov 23 | Large public Parquet and spatial query engineering | Real Ookla partitions with licence checks; measured bytes scanned, pruning, weighted aggregation, and a justified execution-plan change |
| 6 | Nov 30 | Lakehouse transactions and physical layout | Delta or Iceberg chosen for a stated workload; snapshot correctness, schema compatibility, compaction trade-offs, and reproducible measurements |
| 7 | Dec 7 | Event delivery, replay, and consumer correctness | Kafka replay of observed public records; explicit replay timestamps; duplicate/out-of-order fault scenarios; idempotent sink and compatible schema changes |
| 8 | Dec 14 | Version-consistent serving and consumer contracts | API/read model with version pinning, access-control checks, release compatibility, and concurrent-reader publication tests |
| 9 | Dec 21 | Reproducible deployment and operational ownership | Container and infrastructure definitions; secrets/config separation; deploy/rollback evidence on accessible infrastructure; optional cloud budget agreed before paid work |
| 10 | Dec 28 | Data SLOs and incident response | Freshness/completeness metrics, actionable alerts, deliberately injected incidents, measured detection/recovery, and a blameless incident report |
| 11 | Jan 4, 2027 | Versioned public-document data infrastructure | Terms-checked public documents; source versions, extraction/deduplication, lineage, incremental reprocessing, and a fixed evaluation set |
| 12 | Jan 11 | Integrated retail wireless data platform | Valid multi-source joins, repeatable deployment, historical backfill reconciliation, an auditable product-investigation workflow, and documented operating cost/limits |

Every week includes a named new technique, at least three demonstrated senior practices, an architecture decision with rejected alternatives, adversarial acceptance checks, and a hands-on ownership challenge. Explain which evidence was assistant-generated reference work and which work Himanshu independently reproduced or changed.

Use observed public data, with publisher, exact source, licence, download code, version/hash, period, grain, and limitations. Proposed future sources remain feasibility gates. Do not manufacture subscriber identities, causal links, original streaming telemetry, or large observed volumes. Simulated fault scenarios and controlled replays must remain labelled.

The projected FCC data lacks a row-level update timestamp and a transactional snapshot token. History must represent when a version was observed, not invented business-effective dates. Deletion inference requires a complete validated re-extraction scope. Aggregate network geography is not linked customer churn.

Prefer bounded, reproducible local and CI work until required infrastructure is actually accessible. A local prototype is not a cross-host deployment; prepared Docker or infrastructure files are not evidence that deployment ran. A single runtime observation is not a benchmark. More tools do not substitute for an engineering argument.
