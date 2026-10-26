# Crash-recovery increment: executed evidence

Executed October 26, 2026 on Linux x86-64, Python 3.12.14. This records the actual local hardening checks; remote platform results are independently available in GitHub Actions.

## Results

| Check | Observed result |
|---|---|
| New recovery/fault tests | 10 passed in 4.94 seconds |
| Complete Python regression suite | 29 passed in 24.86 seconds |
| Full live public FCC extract through the new path | 29,932 real September 2025 records; six committed pages |
| Wireless rows | 17,280 |
| dbt data tests in the live complete pipeline | 19 passed |
| Live complete-pipeline runtime | 18.841 seconds |
| Offline complete-pipeline runtime | 6.141 seconds |
| Offline extraction work | Six committed pages reused; zero data pages downloaded |
| Comparison with the baseline warehouse | Zero missing IDs, zero extra IDs, zero normalized-record hash mismatches |

The runtime values are individual observations, not a controlled benchmark. They must not be compared with the initial release's 67.542 seconds as proof of a speedup: network, caches, and environment conditions differ.

## Actual process-kill checks

The tests start a real child process and use SIGKILL against that child itself. A local HTTP fixture serves 24 attributed observed FCC records in five pages. This transport is used to make exact crash points reproducible; the separate live run above downloads the full real month from the publisher.

- Kill immediately before the second checkpoint commit: five rows from the first page survive. Resume reuses one page, downloads the remaining four pages, and produces exactly the 24 original IDs.
- Kill immediately after the second commit: ten rows survive. Resume reuses two pages, downloads the remaining three pages, and produces exactly the 24 original IDs.
- Kill after extraction becomes COMPLETE but before bronze publication: an offline restart reconstructs all five pages without any HTTP request.

Each killed child returns negative SIGKILL status. Tests verify committed SQLite counters, the first resumed keyset cursor, the exact final ordered ID list, and uniqueness. This is stronger than merely catching an injected Python exception, but does not simulate power loss or disk hardware failure.

## Additional fault checks

The actual Requests retry adapter recovers from deliberately returned HTTP 429 and 500 responses: five successful data pages and two failed attempts are observed. A changed source-revision stamp invalidates a partial session before a mixed-version snapshot is published. Page-budget exhaustion retains progress; a larger explicit budget resumes it. A modified committed BLOB fails checksum verification. Explicit refresh abandons old partial work, and completed sessions replay without a source client.

Injected HTTP errors, metadata revisions, corruption, and process termination are test scenarios, not claims about errors observed in the FCC's production service. The source observations used for the product analysis remain real public records.

## Files and reproduction

- `resumable_pytest.xml`: the ten new tests.
- `hardening_full_pytest.xml`: all 29 Python tests.
- `hardening_live_execution.json`: actual live command configuration and environment.
- `hardening_offline_execution.json`: offline replay configuration and environment.
- `hardening_summary.json`: row counts, source identity, dbt outcomes, and reused-page counts.
- `hardening_reconciliation.json`: equality check against the existing baseline's source IDs and normalized record hashes.

```bash
python -m pytest tests/test_resumable.py -vv
python -m pytest -q
wireless-de run --resumable --root data/hardened
wireless-de run --resumable --offline --root data/hardened
```

## Remaining limits

This is local single-writer recovery. It does not implement cross-host fencing, power-loss testing, distributed exactly-once delivery, a cloud deployment, observed change history, source freshness SLOs, or zero-row-window publication. Matching source metadata/counts remain best effort because the API has no transaction snapshot token. Payloads are retained in both a BLOB ledger and hydrated bronze files; the existing validator still collects all accepted rows in memory, and candidate publication still copies the previous warehouse.

The next scheduled project must address observed history and incremental/backfill correctness instead of repeating this checkpoint implementation. Independent ownership exercises are in `docs/ADVANCED_CHALLENGE.md`.
