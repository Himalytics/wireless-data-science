# Advanced engineering challenge

The baseline is deliberately no longer the difficulty ceiling. This track is intended for an experienced engineer who wants to demonstrate independent design, failure analysis, and measured trade-offs. Keep a two-hour guided entry path, then budget roughly 8-12 additional hours across the week for implementation, experiments, and a design defense.

The reference implementation below is AI-assisted work. Your ownership evidence comes from the changes you make, experiments you reproduce, and decisions you can explain without the walkthrough. Do not present an assistant-generated patch as proof that you personally solved its design problems.

## Available now: a crash-recoverable extraction protocol

The platform now supports `--resumable`. Each checkpoint transaction stores **both page bytes and the cursor** in SQLite. After an interruption, only committed pages count toward progress. An interrupted session is resumed only if the observed source metadata and count still match its original extraction boundary. Completed sessions can reconstruct immutable bronze files without network access.

The existing contract, Parquet, DuckDB, dbt, and quality-gated publication stages remain in the path. A download checkpoint is not permission to publish a data product.

```bash
wireless-de run --resumable --root data/hardened
wireless-de run --resumable --offline --root data/hardened
python -m pytest tests/test_resumable.py -vv
```

The default source period remains September 2025. Use a separate data root when comparing extraction strategies. Existing baseline commands continue to work.

## Proof required from the reference

| Failure boundary | Required observed behavior |
|---|---|
| SIGKILL before the second page transaction commits | First page remains committed; the second is fetched again; final IDs exactly match the source |
| SIGKILL immediately after the second page commit | Both pages are reused; resume begins after the last committed source ID |
| SIGKILL after extraction completion but before bronze publication | Offline restart reconstructs the snapshot from the completed ledger |
| HTTP 429 and HTTP 500 | The actual Requests retry adapter recovers within a bounded retry budget |
| Source revision changes across interruption | Session becomes INVALID; mixed-version data is not published |
| Page budget exceeded | Committed progress survives; an explicitly larger budget can resume it |
| Committed payload is corrupted | Checksum validation blocks hydration |
| Explicit refresh of incomplete work | Old partial session becomes ABANDONED; it is retained for diagnosis |

Crash tests run real child processes that kill only themselves with SIGKILL. The HTTP fault transport serves 24 attributed observed FCC records on loopback. Errors/revisions are labelled test scenarios. The separate live pipeline run downloads the actual complete source month. Do not claim that a live FCC server was deliberately crashed or altered.

Read [the transaction-boundary decision](adr/0002-checkpoint-transaction-boundary.md), [the source](../src/wireless_de/resumable.py), [the process/HTTP tests](../tests/test_resumable.py), and [the verification report](../reports/HARDENING_VERIFICATION.md).

## Your first two hours

1. Run the crash tests and the resumable pipeline. Inspect a checkpoint ledger with SQLite; identify session status, cursor, page count, row count, and page checksums.
2. Trace why a kill before commit preserves five fixture rows while a kill after commit preserves ten. Explain the transaction boundary without referring to test names.
3. Identify every place a page can be requested more than once. Explain why HTTP replay and a unique committed page are different guarantees.
4. Explain why a completed extraction can be hydrated offline but an interrupted extraction cannot finish offline.
5. Describe a failure that the current tests do not prove safe. Power loss, filesystem failure, lease expiry, and cross-host recovery are valid examples; do not claim they were tested.

## Ownership challenge A: separate payload storage from control state

Move page payloads out of SQLite into content-addressed filesystem objects while keeping the cursor in SQLite. This introduces a real two-store failure boundary that the reference deliberately avoids.

Acceptance criteria:

- A cursor can never refer to a missing or unverified object.
- Killing the process after object persistence but before checkpoint commit leaves a recoverable orphan, not lost data or duplicate rows.
- Resume verifies existing objects; an orphan cleanup policy cannot delete an object referenced by a committed extraction.
- Actual subprocess kills cover both sides of the boundary. Simply raising a Python exception is insufficient.
- Repeated experiments compare ledger size, total bytes written, and elapsed time using the same immutable real input. Label the environment and cache conditions; report distributions rather than advertise a single faster run.
- Write an architecture decision explaining the write order, crash windows, and guarantees you still cannot make.

This is an independently assessable engineering increment. It should require reasoning about durability and referential integrity, not merely swapping a storage library.

## Ownership challenge B: competing workers and stale ownership

The reference uses a local file lock. Design a control-plane protocol that can reject a stale worker after another worker has acquired ownership.

Acceptance criteria:

- Describe the ownership lease and a monotonically increasing fencing token.
- Pause worker A, transfer ownership to B, then resume A. A's stale checkpoint/publication attempt must fail.
- Claiming a lease and committing progress must have an explicit transactional relationship.
- Prove behavior under process pauses, retries, and ownership expiry. Make time deterministic in tests.
- Keep simulated coordination failures distinct from observed public data.
- Explain which guarantees depend on the storage system enforcing the fencing token. A timestamp in an application object alone is not sufficient.

You may prototype locally with transactional state. A cross-host claim requires an actual deployment and test; a local prototype must not be described as distributed production infrastructure.

## Ownership challenge C: history and backfill correctness

The FCC source lacks a transaction snapshot token and the projected records lack authoritative row-update timestamps. Design history around **when this pipeline observed a version**, not an invented original business-effective time.

Acceptance criteria:

- Observe source snapshots and compare source IDs plus normalized record hashes.
- Keep inserted, changed, unchanged, and removed observations distinguishable.
- A deletion is inferred only within a completely and successfully re-extracted scope.
- Corrected complaint dates do not leave conflicting versions in two partitions.
- Repeating the same snapshot does not create another history version.
- Incremental/backfill output reconciles with a full rebuild over the same captured inputs.
- Source-change fault fixtures are labelled tests; if real consecutive captures show no changes, report no changes.

## Ownership challenge D: measured engineering limits

Choose a larger genuine public extraction, subject to publisher limits. Do not duplicate rows and call that a larger observed dataset. If a controlled replay is useful, label it replay and account for unique records separately.

Measure peak memory, request attempts, downloaded bytes, checkpoint commits, warehouse copy volume, rejected rows, end-to-end latency, and recovery rework. Explain which stage dominates and change one design choice. Report the input identity and actual trade-off, including regressions.

## Review gate

One ownership challenge completed well is more valuable than four partially wired technologies. Submit your code diff, passing adversarial checks, measurement output, and decision note. Be ready to explain: what can fail, what state survives, how recovery decides what is true, and which metric justifies the extra complexity.

Cloud deployment, schema-compatible releases, access controls, SLOs, and multi-source integration remain subsequent platform work. This local recovery increment is stronger evidence than the baseline, but does not by itself establish enterprise production readiness.
