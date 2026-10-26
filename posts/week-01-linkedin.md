# LinkedIn draft — Week 1

Status: draft for Himanshu's review. Verify the story after your walkthrough. This is personal learning work on public data, not employer work.

---

I’m starting a weekly series to get deeper into data engineering for retail wireless products.

For the first project, I used AI assistance to build and test a telecom complaints data platform using real public FCC data.

The question I wanted to explore: how can a product team turn a public API into a trustworthy signal for deciding what to investigate?

The first release covers the full path:

• Paginated API ingestion and source-count reconciliation
• Raw snapshots with checksums and replay
• Data contracts and quarantine
• Typed Parquet and a DuckDB warehouse
• dbt transformations and quality gates
• Dagster orchestration and versioned publication

The reliability behavior is the part I’m spending the most time understanding. Testing included deliberate cache corruption and a forced transformation failure. The pipeline had to detect the problem and preserve the last successful data product.

On the captured September 2025 data, the pipeline processed 29,932 actual complaint records, including 17,280 classified as wireless complaints. All 19 dbt data tests and 19 Python reliability tests passed. The initial complete run took about 68 seconds in the Linux test environment.

One descriptive signal: billing complaints rose from 925 to 1,041 across two consecutive complete weeks. That gives me a research question. It does not establish a churn increase, a carrier's service quality, or a causal effect. These are self-selected complaints, and the FCC does not verify the allegations.

My learning focus this week is quality-gated publication: building a candidate, testing it, and promoting it only when the evidence passes.

Next: checkpointed ingestion, source refreshes, and recovery from partial failures.

This is a personal learning project using public data. It uses no employer data, systems, or proprietary designs.

Repository: https://github.com/Himalytics/wireless-data-engineering

#DataEngineering #Telecom #dbt #Dagster #DuckDB #LearningInPublic
