# Week 1 builder's guide

## What you are building

You are building a **trusted analytical data product**, not a churn model. The input is a public API; the output is a versioned warehouse, tested aggregates, and a brief supporting product investigation. The interesting engineering question is: **how do we keep downstream results trustworthy when an upstream API changes, a download stops, a record is bad, or a transformation fails?**

The dataset is a real FCC publication. Its complaint allegations are not verified facts. The project does not use internal employer systems or reproduce their architecture.

The new technique is **quality-gated, versioned publication**. It borrows the discipline of a software release: construct a candidate, check it, then promote it. A new file appearing on disk does not automatically make it the current data product.

## Your two-hour first session

| Minutes | Work | What you should be able to explain |
|---|---|---|
| 0–15 | Install and run the default month | The source, extraction window, and resulting files |
| 15–35 | Read `source.py` and the manifest | Keyset pagination, replay, completeness checks |
| 35–55 | Read `contract.py`; run contract tests | Why quarantine blocks publication |
| 55–80 | Read the dbt models and exported CSVs | Grain, conservation, partial periods, missingness |
| 80–105 | Read release code; run reliability tests | Candidate isolation and last-good preservation |
| 105–120 | Explain the product brief aloud | What is actionable and what the data cannot establish |

Spend later sessions modifying a contract, adding a model, and breaking a candidate deliberately. Only describe implementation choices as your own learning once you can defend or modify them.

## Architecture, from source to publication

### 1. Source extraction

`FccClient` uses a Requests session with bounded retries for transient transport failures and HTTP 429/5xx responses. Requests have connect and read timeouts. A retry is appropriate because downloading a page is a read-only operation.

The API query projects six columns. Projection limits unnecessary data collection and gives the boundary a manageable schema. Date predicates define a half-open window: September 1 is included, October 1 is excluded. Adjacent windows therefore meet without sharing a boundary day.

Every page is ordered by numeric complaint ID. The next request asks for IDs greater than the last observed ID. This is **keyset pagination**. Offset pagination can shift when records are inserted or deleted before an offset. Keyset pagination avoids that positional dependency, but is not a substitute for an immutable source snapshot.

The extractor checks metadata and row counts before and after download. It reconciles downloaded count with expected count and verifies increasing IDs. It refuses a run that reaches the page cap. Because the source has no transaction token, equal counts and unchanged metadata are strong operational checks, not a proof that a source never changed mid-request. This limitation belongs in an interview explanation.

### 2. Bronze snapshots

The downloaded page bytes are preserved with SHA-256 hashes. The manifest records the queries, source window, retrieval timestamp, selected metadata, expected count, and combined content identity. A refresh produces a different snapshot when content changes. Replaying an intact snapshot avoids repeating network calls.

The snapshot directory is content-derived. A partition pointer chooses the cached snapshot for a date window. The cache pointer is separate from the **published product pointer**: successfully downloading a source snapshot does not imply its warehouse passed quality gates.

Checksums detect accidental byte changes relative to the manifest. They are not digital signatures and do not protect against someone intentionally editing both the bytes and manifest.

### 3. Boundary contracts and typed storage

`contract.py` validates each projected record. IDs must be positive integers. The date must be a valid source calendar date at midnight and fall inside the requested window. Text fields must actually be text; missing optional text becomes `UNKNOWN`. State is uppercased and must have two letters or the explicit unknown token. This checks shape, not whether every code is a valid U.S. jurisdiction.

Duplicate IDs across pages fail the contract. Unexpected fields fail it. Rejected rows are written to a quarantine file with a reason. The release policy permits **zero rejected rows**. That strict default makes a bad-data incident visible rather than publishing a reduced dataset without acknowledgement.

Polars writes validated records into a typed Parquet file. The data types are explicit, including `Int64` and `Date`. Parquet is the interchange boundary between Python ingestion and SQL loading. A canonical hash of normalized business fields distinguishes record-content identity from snapshot identity and ingestion time.

### 4. Warehouse loading

Before loading, the system copies the last published DuckDB database into a private working directory. New data never mutates the database currently referenced by readers.

Within one DuckDB transaction, the loader replaces the requested date window and inserts the validated source rows. It also removes an old version of an incoming complaint ID if a source corrected its date. The primary key enforces one stored row per source complaint ID.

This provides repeatable **window replacement**, not full CDC. It reconciles deletions only inside re-extracted windows. A deletion in an old unrefreshed period remains unknown until that period is refreshed. At larger scale, copying the whole warehouse and replacing windows become expensive; a versioned lakehouse or warehouse transaction with partition-level publication is a more appropriate next design.

`ops.covered_dates` records dates whose full source extracts passed validation. A day with zero complaints is different from a day never ingested. That distinction is essential to valid comparisons.

### 5. dbt transformations

`stg_complaints` keeps the source row grain: one complaint ID. `fct_wireless_complaints` filters Phone/Internet records whose method begins with `Wireless`. It does not identify a carrier or infer wireless service from geography.

`daily_wireless_issues` groups by complaint date, state, service type, and issue. `weekly_wireless_issues` uses Monday-start weeks and joins explicit coverage counts. The sparse daily table is not a calendar-spined cube: no row is not automatically a zero.

`issue_priorities` finds the latest pair of consecutive weeks where all seven days have been ingested. It compares matching issue counts. Prior-week absence can become zero because the week itself was fully observed. If no eligible pair exists, it emits no priority rows; it does not manufacture a comparison.

The dbt tests cover uniqueness, nullability, allowed values, coverage relationships, and count conservation. Conservation tests matter because a perfectly typed join can silently multiply rows. A row-count equality alone is not enough for every transformation, but it is a useful invariant for these particular aggregates.

### 6. Publication and recovery

The pipeline executes `dbt build` against the candidate database and inspects actual run results. Any failed or skipped node prevents publication. Successful releases contain the database, CSV exports, product brief, source identity, and dbt artifacts.

The candidate directory is renamed into `releases/`, then an atomic JSON pointer replacement updates `CURRENT.json`. Readers resolve the pointer once, open that release read-only, and retain it for their work. A reader that already resolved the previous release can continue using it after promotion.

A process-scoped filesystem lock permits only one writer per data root. macOS and Linux support the `fcntl` mechanism used here. This is a local concurrency protocol, not distributed coordination. An interrupted process releases the lock through the operating system. The presence of the lock file itself does not mean a process holds it.

Failures before pointer replacement leave the old product current. Orphaned work/release directories may remain and require retention cleanup. `os.replace` gives local atomic name replacement; this portfolio implementation is not claiming a power-loss-proof distributed commit protocol.

## File-by-file ownership

| File | What it owns | What to change in an exercise |
|---|---|---|
| `settings.py` | Extraction settings and validation | Enforce a maximum demo window |
| `io.py` | Atomic JSON, hashes, lock, current-release resolution | Add retention-safe release listing |
| `source.py` | FCC API, pagination, snapshots, cache verification | Add an app token via an environment variable without logging it |
| `contract.py` | Record rules, quarantine, typed Parquet | Add a documented state-code reference validation |
| `warehouse.py` | Candidate load, dbt subprocess, promotion, outputs | Add partition refresh diagnostics |
| `assets.py` | Dagster asset graph and stage dependencies | Add a separate observability asset |
| `cli.py` | Terminal interface, writer lifecycle, execution evidence | Add a `history` command |
| `dbt/models/` | Analytical grain and business transformations | Add a complete-week state/issue table |
| `dbt/tests/` | Warehouse invariants | Add a composite-grain uniqueness test |
| `tests/` | Fault injection and end-to-end regression checks | Prove an interrupted extract cannot advance pointers |
| `.github/workflows/ci.yml` | Intended Linux/macOS verification | Review actual remote jobs after publishing |

## Why these technologies

This stack teaches portable engineering responsibilities. DuckDB makes analytical SQL and Parquet inspection practical on a Mac without a paid warehouse. dbt gives transformations a dependency graph, test suite, and lineage artifacts. Dagster gives Python and SQL stages explicit orchestration boundaries. Polars establishes a typed, columnar handoff rather than relying on inferred CSV types. Docker is provided as an optional packaging path.

These are reasons to use the tools for this workload. No unsupported claim is made about a current market-demand ranking. We introduce distributed systems later when their coordination, scaling, or access properties are the subject being learned.

## Design choices you must defend

**Why keep all projected FCC complaints before the wireless filter?** It makes ingestion completeness independently auditable and keeps raw scope distinct from the product definition. It also allows checking how much a method-based filter excludes.

**Why fail on one rejected row?** The first release optimizes for visible correctness. A production system could introduce a tolerated rejection budget, but would need explicit owners, monitoring, and aggregate-impact rules.

**Why use a historical month?** It bounds runtime, gives complete weeks, and makes the first run teachable. A live operational pipeline also needs source-latency measurements and late-arrival policies, which Week 2 adds.

**Why not Kafka or Spark immediately?** The default extract is small enough for one machine. Introducing a cluster would shift the exercise toward infrastructure setup without justifying its cost. The design documents when local copies, locking, and memory become limiting.

**Why not claim exactly once?** API reads, local file publication, and external readers are different boundaries. What is demonstrated is row-idempotent window replay, a transactional candidate load, and one local publication pointer.

## Product interpretation

For the observed default extract, review the generated summary and product brief for actual counts. High billing counts or a portability increase are prompts for investigation, not evidence that one company caused a problem. Complaints are self-selected, lack an exposure denominator, and may reflect publicity or reporting behavior.

An appropriate next step is a product/support research queue. Measure how often flagged themes lead to independently corroborated issues and how long detection takes. A later intervention needs its own evaluation. Keep this personal project independent of employer systems and do not imply measured employer impact.

## Interview questions with defensible answers

1. **How do you prove a download is complete?** Reconcile source counts, verify ordered unique IDs, enforce page bounds, check source metadata before/after, then conserve rows through contracts and SQL. Explain that the API lacks transaction-level snapshot isolation.
2. **How do you rerun safely?** Verify immutable snapshot bytes; replace the extraction window in a candidate transaction; enforce source ID uniqueness; promote only after dbt passes.
3. **What happens when dbt fails?** The candidate remains diagnostic work. The published pointer and database remain unchanged, which an integration test checks.
4. **How do you handle late data?** Refresh historical windows deliberately; Week 1 does not discover every late record automatically. Week 2 adds overlap/checkpoint policies and measures their limits.
5. **How would you scale this?** Move immutable source objects to versioned object storage, partition validated tables, replace full copies with table-format snapshots or warehouse transactions, and use orchestration workers with distributed locking/access controls.
6. **What business impact did you measure?** Data quality, completeness, repeatability, and runtime. Product uplift has not been measured; the output supports research prioritization.
7. **Is a missing row a zero?** Only if the relevant date/domain coverage is known. Complete-week coverage permits specific zero filling; an unobserved period remains unknown.
8. **What is the strongest limitation?** Observed public complaints cannot identify individual churn risk or causal service quality. Source consistency is best effort and local publication is single-writer.

## Extend it yourself

Start by adding a state/issue composite-grain test. Then add a command that lists every release with its source hash and test count. Finally, propose a retention policy that deletes unused historical candidates without removing a release an active reader may still use. Document your trade-offs before changing code.
