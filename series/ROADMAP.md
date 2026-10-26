# Twelve-week data engineering sequence

This replaces a model-heavy sequence with an engineering-first platform. Every week retains the complete pipeline and adds one substantial capability. Proposed future sources are feasibility gates, not promises that every field, licence, or join already exists. Verify each source before implementation and change the scope transparently if it cannot support the question.

| Week | Date | New project/module | Named technique | Data and product decision |
|---|---|---|---|---|
| 1 | Oct 26, 2026 | Telecom complaint data product | Quality-gated versioned publication | Observed FCC complaint records; prioritize product-research themes |
| 2 | Nov 2 | Incremental ingestion and recovery lab | Checkpointed extraction and bounded overlap reconciliation | Real FCC refreshes; detect changes without losing or duplicating observations |
| 3 | Nov 9 | Geographic reference and market context | Versioned dimensions and geographic-key contracts | Census public geography/population, subject to source checks; contextualize research markets |
| 4 | Nov 16 | Coverage intelligence ingestion | Spatial joins with coverage/completeness accounting | Verified public FCC mobile coverage release; identify areas for coverage investigation |
| 5 | Nov 23 | Network experience lake ingestion | Partition pruning and weighted spatial aggregation | Ookla public quarterly tiles, with licence/attribution checks; prioritize network-experience research |
| 6 | Nov 30 | Warehouse transformation platform | Incremental dbt models and schema evolution | Reuse observed datasets; compare local engine with one approved cloud warehouse; cloud spend optional |
| 7 | Dec 7 | Event transport and replay system | At-least-once delivery with idempotent consumers | Replay real published records through Kafka; label event timing as replay, not original live telemetry |
| 8 | Dec 14 | Lakehouse engineering module | Table snapshots, schema evolution, and compaction | Spark with Delta or Iceberg over real partitions; scale measurements tied to observed volume |
| 9 | Dec 21 | Data reliability and observability | Data SLOs, lineage, and incident recovery | Existing real pipelines; select which data products are fit for use |
| 10 | Dec 28 | Serving and access layer | Version-consistent APIs and reproducible deployment | Existing real marts; API contracts, auth design, Docker, and consumer compatibility |
| 11 | Jan 4, 2027 | Public document ingestion platform | Versioned document provenance and retrieval evaluation | Public carrier/FCC documents subject to terms; deduplication, extraction, citations, and test collections |
| 12 | Jan 11 | Retail wireless intelligence capstone | Cross-pipeline integration and reproducibility audit | Integrated observed sources with valid join grains; one reviewable product-investigation workflow |

Real FCC complaints cannot be joined to individual churn outcomes without a valid additional source. Aggregate network data cannot establish subscriber-level causal effects. Do not fabricate joins, event histories, customer identities, retention offers, or treatment effects to make the capstone seem integrated.

Predictive/causal modelling may be added later only with an appropriate dataset and a justified product question. Data engineering deliverables must stand on their own. A limited single-machine demonstration should describe its production gaps rather than call itself enterprise production infrastructure.
