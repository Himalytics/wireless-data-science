# Week 1 measured verification

Executed October 26, 2026. Environment: **Linux x86-64, Python 3.12.14**. These are actual execution results, not expected outputs.

| Check | Observed result |
|---|---|
| Live FCC extraction | Passed; September 1–30, 2025 |
| Actual source rows | **29,932** |
| Wireless Phone/Internet rows after documented filter | **17,280** |
| Source pages | 6 at a maximum of 5,000 records per request |
| Rejected source rows | 0 |
| dbt models built | 6 |
| dbt data tests passed | **19** |
| Python reliability tests passed | **19** |
| Initial complete pipeline runtime | **67.542 seconds**, including API and dbt |
| Offline complete replay runtime | **51.498 seconds**, including candidate rebuild and dbt |
| Reliability-suite elapsed time | **169.18 seconds** |
| Rerun row count | Remained 29,932; no append duplicates |
| macOS execution | Not run here; Mac installation instructions and CI job supplied |
| Remote GitHub CI | Prepared; not run before repository publication |
| Docker execution | Not run; Docker engine unavailable in this environment |

Captured source snapshot identity:

```
8eebab81805b090981ea9c74f7525a7b296594dcc75a2b870f45b112294158ca
```

## Commands actually executed

The build environment was an isolated Python 3.12 virtual environment. From the project directory, equivalents of these installed entry points were executed:

```bash
python -m wireless_de.cli run --start 2025-09-01 --end 2025-10-01
wireless-de run --offline
python -m pytest -q --junitxml=reports/pytest.xml
```

The actual binary paths were under a separate `.venv-build` in the workspace. `live_extraction_execution.json` and `offline_replay_execution.json` preserve the exact run configuration and environment. `pytest.xml` records test outcomes; `dbt_run_results.json` records individual transformation and data-test outcomes.

## Failure and recovery evidence

The test suite passed checks for complete/disjoint keyset pages, truncation rejection, offline-cache requirements, replay without network, byte-corruption detection, fresh-download repair, source-revision abort, invalid date/type/state/unexpected-field rejection, explicit missing text, quarantine blocking, concurrent-writer rejection, full dbt publication and idempotent replay, window deletion reconciliation, and preservation of the last good database after an injected dbt-stage failure.

All corruption, deletion, and forced-failure scenarios are **labelled fault injection**. They are not claims that the FCC source had those errors. The tests use a small capture of real source records; production results above use the actual full extracted month.

## Descriptive product observations

The generated priority comparison uses complete weeks starting **September 22, 2025** and **September 15, 2025**. In the captured snapshot, wireless billing complaints increased from **925 to 1,041** (+116, about 12.5%). Number-portability complaints increased from **145 to 184** (+39). These are unadjusted report counts, not subscriber rates or causal effects.

The full month also contains non-wireless complaints, so the source total must not be presented as the wireless count. Complaint allegations are not verified by the FCC. There is no carrier-specific or customer-level churn outcome here.

## Limits of the evidence

Runtime is one observation in this environment, not a performance benchmark or Mac speed promise. Installation time is excluded. A fresh source extraction can change if the publisher revises history. The consistency checks are best effort because the API has no transaction snapshot token. The warehouse release protocol is local and single-writer. It has not been validated for high-availability or distributed workloads.
