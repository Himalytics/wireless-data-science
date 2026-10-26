# Series charter

Owner: Himanshu Jadaun. Scope: personal learning in senior data engineering for retail wireless product questions. Week 1 starts October 26, 2026. Subsequent builds are intended for Monday mornings in America/Denver; the saved automation is the source of truth for scheduling status.

## Delivery contract

Each release must contain a new working project/module with a standalone entry point, complete code, a public-data download path, a builder's guide, measured verification evidence, and a LinkedIn draft. Reuse and improve shared infrastructure. The platform must grow in capability rather than restart with disconnected toy notebooks.

LinkedIn deliverables must follow [the storytelling standard](../posts/STORYTELLING_STANDARD.md): quantified findings and engineering results, a coherent narrative, and a mobile-readable PDF/PNG carousel with reproducible charts, source data, and alt text. A stack summary alone is insufficient.

Every project must demonstrate ingestion, contracts/validation, transformation, persistent storage, quality gates, orchestration, recovery/failure handling, documentation, and a product decision with a proposed measurement plan. At least three senior engineering practices and a named new technique must be explicit.

Use observed public data as the analytical foundation. Record publisher, dataset identifier, authoritative source link, licence, retrieval method, extraction bounds, and checksums/version information. Public does not automatically mean observed: fictional/synthetic benchmark sources must be labelled and cannot serve as the sole real-data foundation. Simulations may augment a real source only when clearly labelled in code, documentation, outputs, and posts. Test fault injection is labelled separately and excluded from product results.

Use no EchoStar / Boost Mobile internal data, code, dashboards, customer data, or proprietary designs; do not imitate internal systems. Keep all public writing framed as personal learning on public sources. Never infer measured employer impact from portfolio outputs.

Build and run before claiming success. Record environment, executed commands, input scope, actual counts, data-quality results, runtime, failures discovered, and limits. If access or runtime blocks a check, say so; do not invent results. Mac-tested means execution on macOS, not merely Mac installation instructions. A prepared CI workflow is not a passing remote run.

The two-hour first session should cover running and understanding the project. The advanced track then provides roughly 8-12 hours of deeper implementation, experiments, and a design defense across the week. Include concepts, architecture, file responsibilities, alternatives, common errors, extension exercises, and interview talking points.

## Advanced difficulty gate

Himanshu found the initial baseline easy and requested more depth. Each subsequent release must tackle a substantial state, correctness, recovery, scaling, deployment, or consumer-compatibility problem. A new connector, a notebook, a tool substitution, or another group-by does not constitute a complete weekly increment.

Include explicit acceptance criteria, adversarial checks at meaningful process/network/transaction boundaries, measured engineering behavior, a justified architecture decision with rejected alternatives, and a hands-on ownership challenge. Provide complete reference code while distinguishing assistant-generated implementation from work Himanshu has independently reproduced or changed. Do not claim enterprise readiness or five years of expertise from repository polish.

The first advanced reference is [the crash-recovery protocol](../docs/ADVANCED_CHALLENGE.md). Do not repeat that implementation as Week 2; extend it with observed change history and backfill reconciliation. Constraints and unresolved guarantees must remain explicit.

Choose tools because the workload benefits. Introduce dbt, Dagster/Airflow, DuckDB/Polars, Spark, Delta/Iceberg, Kafka, Docker, and a cloud warehouse progressively. Explain the engineering capability, portability, and complexity trade-offs. Verify any claim about current market demand; do not rank tools by unsupported popularity.

## Publication rules

GitHub account: **Himalytics**. Configured repository: **Himalytics/wireless-data-engineering** (https://github.com/Himalytics/wireless-data-engineering). Himanshu created this destination after reviewing the Week 1 package and requesting GitHub publication. Week 1 source and evidence are included here. Do not use an unrelated repository as a workaround.

The user previously required explicit approval for the specific repository push and specific LinkedIn post. Preserve that rule until clearly changed. Package tested work and present the exact proposed repository operation and post draft for review. A connection alone is not approval to publish an unreviewed release. Do not merge, force-push, or publish LinkedIn content without the applicable approval.

No direct LinkedIn publishing connection was found during setup. Deliver the complete draft to Himanshu in chat/files. Do not claim it was posted.

## Persistent continuity

Keep a versioned series state, release evidence, and the next-week plan. Use the latest approved GitHub state when it exists, otherwise the most recent saved project archive. Never rely on a transient working directory surviving until the next scheduled run. Read authoritative current state before deciding the next week. If a prior release is incomplete, repair it first and explain the dependency; do not skip evidence gates to maintain a fictional cadence.
