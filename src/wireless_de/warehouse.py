"""Build a private candidate database; publish only after all dbt tests pass."""
import csv
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import duckdb

from wireless_de.io import atomic_json, current_release
from wireless_de.settings import Settings


def load_candidate(payload):
    settings = Settings(**payload["settings"])
    work, root = Path(payload["work"]), Path(settings.root)
    database = work / "warehouse.duckdb"
    previous = current_release(root)
    if previous:
        shutil.copy2(previous / "warehouse.duckdb", database)
    with duckdb.connect(str(database)) as con:
        con.execute("BEGIN")
        try:
            con.execute("CREATE SCHEMA IF NOT EXISTS raw")
            con.execute("CREATE SCHEMA IF NOT EXISTS ops")
            con.execute("CREATE TABLE IF NOT EXISTS raw.complaints (complaint_id BIGINT PRIMARY KEY, complaint_date DATE, issue_type VARCHAR, method VARCHAR, issue VARCHAR, state VARCHAR, record_sha256 VARCHAR, snapshot_sha256 VARCHAR, ingested_at_utc VARCHAR)")
            con.execute("CREATE TABLE IF NOT EXISTS ops.covered_dates (day DATE PRIMARY KEY)")
            con.execute("CREATE TEMP TABLE incoming AS SELECT * FROM read_parquet(?)", [payload["parquet"]])
            # Window replacement also reconciles deletions within the re-extracted window.
            # Incoming IDs delete old versions even when a source corrects the date.
            con.execute("DELETE FROM raw.complaints WHERE (complaint_date >= ?::DATE AND complaint_date < ?::DATE) OR complaint_id IN (SELECT complaint_id FROM incoming)", [settings.start, settings.end])
            con.execute("INSERT INTO raw.complaints SELECT * FROM incoming")
            con.execute("INSERT OR IGNORE INTO ops.covered_dates SELECT day::DATE FROM generate_series(?::DATE, ?::DATE - INTERVAL 1 DAY, INTERVAL 1 DAY) AS d(day)", [settings.start, settings.end])
            con.execute("COMMIT")
        except Exception:
            con.execute("ROLLBACK")
            raise
    return {**payload, "database": str(database)}


def run_dbt(payload):
    settings = Settings(**payload["settings"])
    project = Path(settings.project) / "dbt"
    target = Path(payload["work"]) / "dbt_target"
    logs = Path(payload["work"]) / "dbt_logs"
    env = dict(os.environ, WDE_DB_PATH=payload["database"], DBT_SEND_ANONYMOUS_USAGE_STATS="false")
    executable = str(Path(sys.executable).parent / "dbt")
    command = [executable, "build", "--project-dir", str(project), "--profiles-dir", str(project),
               "--target-path", str(target), "--log-path", str(logs), "--fail-fast"]
    result = subprocess.run(command, env=env, text=True, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, timeout=180)
    (Path(payload["work"]) / "dbt-console.log").write_text(result.stdout)
    if result.returncode:
        raise RuntimeError(f"dbt quality gate failed (exit {result.returncode}); inspect dbt-console.log")
    run_results = json.loads((target / "run_results.json").read_text())
    statuses = [r["status"] for r in run_results["results"]]
    if not statuses or any(s not in ("pass", "success") for s in statuses):
        raise RuntimeError("dbt did not pass every model and test")
    return {**payload, "dbt_results": {"nodes": len(statuses),
             "tests_passed": sum(s == "pass" for s in statuses), "statuses": statuses}}


def publish(payload):
    settings = Settings(**payload["settings"])
    work, root = Path(payload["work"]), Path(settings.root)
    exports = work / "exports"
    exports.mkdir(exist_ok=True)
    with duckdb.connect(payload["database"], read_only=True) as con:
        raw_count = con.execute("SELECT count(*) FROM raw.complaints").fetchone()[0]
        wireless_count = con.execute("SELECT count(*) FROM analytics.fct_wireless_complaints").fetchone()[0]
        for name in ("daily_wireless_issues", "weekly_wireless_issues", "issue_priorities"):
            cursor = con.execute(f"SELECT * FROM analytics.{name} ORDER BY ALL")
            with (exports / f"{name}.csv").open("w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([d[0] for d in cursor.description])
                writer.writerows(cursor.fetchall())
        priorities = con.execute("SELECT issue, current_complaints, previous_complaints, change_in_complaints, action FROM analytics.issue_priorities ORDER BY current_complaints DESC LIMIT 5").fetchall()
    summary = {"source": "FCC public informal complaint records; allegations not verified by FCC",
               "start": settings.start, "end_exclusive": settings.end,
               "snapshot_sha256": payload["manifest"]["snapshot_sha256"],
               "window_rows_validated": payload["rows"], "warehouse_rows": raw_count,
               "wireless_rows": wireless_count, "cache_hit": payload["cache_hit"],
               "resumability": payload.get("resumability"),
               "dbt": payload["dbt_results"],
               "top_issues": [dict(zip(("issue", "current_complaints", "previous_complaints", "change", "action"), p)) for p in priorities],
               "limits": ["Complaint counts are not churn or failure rates", "No carrier or subscriber denominator", "Self-selected, unverified reports", "No synthetic production rows", "Local single-writer release protocol; not a distributed warehouse"]}
    atomic_json(work / "summary.json", summary)
    lines = ["# Product investigation brief", "", "Use public complaint signals to choose questions for research, not to rank carriers or infer churn.", "",
             f"Validated {payload['rows']:,} real source records for [{settings.start}, {settings.end}).",
             f"Published warehouse: {raw_count:,} records; {wireless_count:,} classified as wireless Phone/Internet complaints.", "",
             "| Issue | Latest complete week | Previous complete week | Change | Action |", "|---|---:|---:|---:|---|"]
    for issue, current, previous, change, action in priorities:
        lines.append(f"| {issue} | {current} | {previous} | {change} | {action} |")
    lines += ["", "Decision: investigate high-volume issues and sustained increases with product/support research. Treat these as hypotheses.",
              "Measure investigation yield and time-to-detection first. A product intervention needs a separate randomized or otherwise justified evaluation with exposure denominators, guardrails, and actual retention outcomes.",
              "", "Partial weeks are excluded from the priority comparison. Missing previous-period issue counts become zero only when all seven days were ingested. No claim of real business uplift is made."]
    (work / "product_brief.md").write_text("\n".join(lines) + "\n")
    atomic_json(work / "READY.json", {"quality_gate": "passed", "snapshot": summary["snapshot_sha256"]})
    release = root / "releases" / work.name
    release.parent.mkdir(parents=True, exist_ok=True)
    work.rename(release)
    atomic_json(root / "CURRENT.json", {"release": str(release.relative_to(root))})
    return {"release": str(release), "summary": summary}
