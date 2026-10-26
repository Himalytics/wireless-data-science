# Operations runbook

## Commands

Use an activated project virtual environment and run from the repository root. `--root` isolates all runtime state, so two different roots do not share cached snapshots or databases.

```bash
wireless-de run
wireless-de run --offline
wireless-de run --refresh
wireless-de run --start 2025-10-01 --end 2025-11-01
wireless-de inspect
python -m pytest -q
```

`--offline` requires a previously verified source snapshot for that date window. It still rebuilds the candidate and runs dbt; it is a replay, not a shortcut around tests. Normal runs use an existing matching snapshot and make that cache use visible. `--refresh` deliberately returns to the API.

## Read the current warehouse safely

```python
import json
from pathlib import Path
import duckdb

root = Path('data').resolve()
release = root / json.loads((root / 'CURRENT.json').read_text())['release']
with duckdb.connect(str(release / 'warehouse.duckdb'), read_only=True) as con:
    print(con.execute('select * from analytics.issue_priorities order by current_complaints desc').fetchall())
```

Resolve the pointer once for a consistent reader session. Never open the published database with a writer. The database lives inside a versioned directory, not at `data/warehouse.duckdb`.

## Incidents

| Symptom | Likely cause | Action |
|---|---|---|
| `No module named wireless_de` | Wrong environment or editable install missing | Activate `.venv`; run `python -m pip install --no-deps -e .` |
| `dbt` executable missing | Dependencies installed in another interpreter | Use the locked requirements in the same virtual environment |
| Source timeout / 429 | Publisher slow or throttled | Let bounded retries finish; retry later; use a verified cached snapshot for a replay |
| `max_pages reached` | Window exceeds extraction safety budget | Use a smaller window or explicitly increase `--max-pages`; never treat this as a successful sample |
| Source changed during extraction | Metadata/count mismatch | Retry `--refresh` in a quieter period; previous published release remains current |
| Checksum mismatch | Cached page changed or was damaged | Preserve the damaged copy for investigation; `--refresh` repairs by writing a new physical copy |
| Contract failure | Type/date/schema/duplicate issue | Inspect candidate `quality.json` and `quarantine.jsonl`; correct the mapping or source before re-running |
| dbt gate failure | Transformation or warehouse invariant broke | Inspect `dbt-console.log`, `dbt_logs/`, and `dbt_target/run_results.json`; fix before promotion |
| Another writer is active | A process holds the root lock | Wait for it to finish; use another root for an isolated experiment |
| DuckDB lock error | Another connection opened a candidate for writing | Close that connection; published readers should use read-only mode |
| Empty priorities table | No pair of consecutive fully ingested weeks | Ingest a longer adjacent period; do not fill missing periods with invented counts |

## Failure evidence

Each CLI run writes `data/runs/<run-id>.json`. A failed candidate remains under `data/work/<run-id>/`. A successful candidate moves into `data/releases/<run-id>/`. The current release pointer advances only after gates pass.

The reliability suite explicitly injects byte corruption, invalid source fields, source revisions, deletions, and a dbt-stage failure. These scenarios are labelled tests, not real incident history. The ordinary dataset remains observed public data.

## Recovery and retention

Restarting a run uses a verified completed snapshot if one exists. Week 1 discards incomplete download directories on an ordinary handled exception; it does not resume individual partially downloaded pages. A process crash can leave a `.download-*` directory. Preserve it until investigation is complete; do not interpret it as a valid snapshot.

Do not delete the current release. Retention cleanup is intentionally manual in Week 1: first identify active readers and releases, then remove unused candidates/old versions. Week 2 will introduce checkpoints and more explicit recovery state.

## Source freshness

`complaint_date` is a source-reported calendar date; `downloaded_at_utc` is when this system extracted data. Neither is a guarantee of when a complaint first became available in the public API. The default historical month is for a bounded reproducible exercise. A live refresh policy requires a measured publication-lag distribution and overlap strategy.

## CI and Docker

The supplied GitHub workflow runs tests on Linux and macOS. Those remote jobs only execute after the repository is populated; the verification report distinguishes prepared CI from observed CI results. The local suite needs no network because its transport uses a small attributed capture of observed source records.

Optional Docker:

```bash
docker build -t wireless-de:week01 .
docker run --rm -v "$PWD/data:/app/data" wireless-de:week01 run
```

The bind mount preserves data between containers. Docker is a prepared packaging route, not a claim of tested container execution unless listed as passed in `reports/VERIFICATION.md`.
