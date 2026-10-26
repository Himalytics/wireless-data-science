"""Real captured FCC rows over a local HTTP fault transport; no fake product data."""
import copy
import json
import re
import signal
import sqlite3
import subprocess
import sys
import threading
from dataclasses import replace
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pytest

from conftest import PROJECT, RecordedClient
from wireless_de.contract import validate_snapshot
from wireless_de.io import read_json
from wireless_de.resumable import ingest_resumable, ledger_directory
from wireless_de.source import FIELDS, SourceError


@pytest.fixture
def http_fixture(observed_rows):
    state = {"rows": copy.deepcopy(observed_rows), "revision": 1, "queries": [], "failures": []}

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def do_GET(self):
            parsed = urlparse(self.path)
            params = {k: v[0] for k, v in parse_qs(parsed.query).items()}
            state["queries"].append({"path": parsed.path, "params": params})
            if parsed.path == "/metadata":
                result = {"name": "Observed FCC rows - local fault transport", "rowsUpdatedAt": state["revision"],
                          "license": {"name": "Public Domain U.S. Government"},
                          "columns": [{"fieldName": f, "dataTypeName": "number" if f == "id" else ("calendar_date" if f == "date_created" else "text")} for f in FIELDS]}
            elif params.get("$select", "").startswith("count"):
                result = [{"n": str(len(state["rows"]))}]
            else:
                if state["failures"]:
                    code = state["failures"].pop(0)
                    self.send_response(code)
                    self.send_header("Retry-After", "0")
                    self.send_header("Content-Length", "0")
                    self.end_headers()
                    return
                after = int(re.search(r"id > (-?\d+)", params["$where"])[1])
                result = [r for r in state["rows"] if int(r["id"]) > after][:int(params["$limit"])]
            content = json.dumps(result, sort_keys=True).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    state["url"] = f"http://127.0.0.1:{server.server_port}"
    try:
        yield state
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def run_worker(settings, server, **options):
    root = Path(settings.root)
    output = root / "worker-result.json"
    command = [sys.executable, str(PROJECT / "tests/helpers/resume_worker.py"),
               "--root", settings.root, "--project", settings.project,
               "--base-url", server["url"], "--output", str(output)]
    for key, value in options.items():
        command.append("--" + key.replace("_", "-"))
        if value is not True:
            command.append(str(value))
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=45)
    return result, read_json(output) if result.returncode == 0 else None


def ledger_state(settings):
    with sqlite3.connect(ledger_directory(settings) / "ledger.sqlite3") as con:
        con.row_factory = sqlite3.Row
        return dict(con.execute("SELECT * FROM sessions ORDER BY rowid DESC LIMIT 1").fetchone())


def ids_from_result(result):
    rows = []
    for page in result["manifest"]["pages"]:
        rows.extend(json.loads((Path(result["snapshot"]) / page["file"]).read_bytes()))
    return [int(r["id"]) for r in rows]


@pytest.mark.parametrize("point,committed,reused", [
    ("before_checkpoint_commit", 5, 1),
    ("after_checkpoint_commit", 10, 2),
])
def test_actual_sigkill_resumes_without_missing_or_duplicate_ids(settings, observed_rows, http_fixture, point, committed, reused):
    settings = replace(settings, resumable=True)
    killed, _ = run_worker(settings, http_fixture, kill_at=point)
    assert killed.returncode == -signal.SIGKILL
    state = ledger_state(settings)
    assert state["n_rows"] == committed and state["n_pages"] == reused
    assert state["status"] == "WRITING"
    count_before_resume = len(http_fixture["queries"])
    resumed, payload = run_worker(settings, http_fixture)
    assert resumed.returncode == 0, resumed.stderr
    assert payload["resumability"]["pages_reused"] == reused
    assert payload["resumability"]["pages_downloaded"] == 5 - reused
    expected = [int(r["id"]) for r in observed_rows]
    assert ids_from_result(payload) == expected
    assert len(set(ids_from_result(payload))) == 24
    page_requests = [q for q in http_fixture["queries"][count_before_resume:]
                     if "id > " in q["params"].get("$where", "")]
    assert f"id > {state['cursor']}" in page_requests[0]["params"]["$where"]
    assert validate_snapshot(payload, Path(settings.root) / "validated")["rows"] == 24


def test_completed_ledger_survives_sigkill_before_snapshot_publication(settings, observed_rows, http_fixture):
    killed, _ = run_worker(settings, http_fixture, kill_at="after_session_complete", kill_page=0)
    assert killed.returncode == -signal.SIGKILL
    assert ledger_state(settings)["status"] == "COMPLETE"
    assert not list((Path(settings.root) / "bronze").rglob("CURRENT.json"))
    requests_before = len(http_fixture["queries"])
    resumed, payload = run_worker(settings, http_fixture, offline=True)
    assert resumed.returncode == 0, resumed.stderr
    assert len(http_fixture["queries"]) == requests_before
    assert payload["resumability"]["pages_reused"] == 5
    assert ids_from_result(payload) == [int(r["id"]) for r in observed_rows]


def test_http_429_and_500_are_retried_by_the_real_client(settings, http_fixture):
    http_fixture["failures"] = [429, 500]
    result, payload = run_worker(settings, http_fixture)
    assert result.returncode == 0, result.stderr
    assert not http_fixture["failures"]
    page_requests = [q for q in http_fixture["queries"] if "id > " in q["params"].get("$where", "")]
    assert len(page_requests) == 7  # Five data pages and two deliberately failed attempts.
    assert payload["manifest"]["expected_rows"] == 24


def test_source_revision_change_refuses_to_mix_checkpoint_versions(settings, http_fixture):
    killed, _ = run_worker(settings, http_fixture, kill_at="after_checkpoint_commit")
    assert killed.returncode == -signal.SIGKILL
    http_fixture["revision"] += 1  # Explicit source-revision fault scenario.
    result, _ = run_worker(settings, http_fixture)
    assert result.returncode != 0
    assert "Source revision changed" in result.stderr
    assert ledger_state(settings)["status"] == "INVALID"
    assert not list((Path(settings.root) / "bronze").rglob("CURRENT.json"))


def test_page_budget_can_increase_without_throwing_away_committed_work(settings, observed_rows):
    client = RecordedClient(observed_rows)
    with pytest.raises(SourceError, match="max_pages"):
        ingest_resumable(replace(settings, max_pages=2), client)
    assert ledger_state(settings)["n_pages"] == 2
    result = ingest_resumable(replace(settings, max_pages=10), client)
    assert result["resumability"]["pages_reused"] == 2
    assert result["resumability"]["pages_downloaded"] == 3
    assert len(ids_from_result(result)) == len(set(ids_from_result(result))) == 24


def test_offline_refuses_incomplete_checkpoint(settings, observed_rows):
    with pytest.raises(SourceError, match="max_pages"):
        ingest_resumable(replace(settings, max_pages=1), RecordedClient(observed_rows))
    with pytest.raises(SourceError, match="COMPLETE"):
        ingest_resumable(replace(settings, offline=True))


def test_corrupt_committed_blob_is_detected_before_hydration(settings, observed_rows):
    ingest_resumable(settings, RecordedClient(observed_rows))
    with sqlite3.connect(ledger_directory(settings) / "ledger.sqlite3") as con:
        con.execute("UPDATE pages SET content = ? WHERE page_number = 1", [b"corrupt"])
    with pytest.raises(SourceError, match="checksum mismatch"):
        ingest_resumable(replace(settings, offline=True))


def test_explicit_refresh_abandons_old_partial_session(settings, observed_rows):
    with pytest.raises(SourceError, match="max_pages"):
        ingest_resumable(replace(settings, max_pages=1), RecordedClient(observed_rows))
    old_id = ledger_state(settings)["id"]
    result = ingest_resumable(replace(settings, refresh=True), RecordedClient(observed_rows))
    assert result["resumability"]["session_id"] != old_id
    assert result["resumability"]["pages_reused"] == 0
    with sqlite3.connect(ledger_directory(settings) / "ledger.sqlite3") as con:
        assert con.execute("SELECT status FROM sessions WHERE id=?", [old_id]).fetchone()[0] == "ABANDONED"


def test_completed_replay_does_not_need_source_client(settings, observed_rows):
    first = ingest_resumable(settings, RecordedClient(observed_rows))
    replay = ingest_resumable(replace(settings, offline=True))
    assert replay["cache_hit"]
    assert replay["resumability"]["pages_downloaded"] == 0
    assert ids_from_result(replay) == ids_from_result(first)
