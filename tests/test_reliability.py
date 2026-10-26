import copy
import json
from dataclasses import replace
from pathlib import Path

import duckdb
import pytest

from conftest import RecordedClient
from wireless_de.contract import ContractError, normalize, validate_snapshot
from wireless_de.io import current_release, read_json, writer_lock
from wireless_de.source import SourceError, ingest
from wireless_de.warehouse import load_candidate, publish, run_dbt


def prepare(settings, rows, work="candidate"):
    payload = ingest(settings, RecordedClient(rows))
    return validate_snapshot(payload, Path(settings.root) / "work" / work)


def test_keyset_pages_are_complete_and_disjoint(settings, observed_rows):
    client = RecordedClient(observed_rows)
    result = ingest(settings, client)
    assert result["manifest"]["expected_rows"] == 24
    assert len(result["manifest"]["pages"]) == 5
    assert all("$offset" not in q for q in client.queries)
    assert not any("caller_id_number" in q["$select"] for q in client.queries)


def test_truncation_is_a_hard_failure(settings, observed_rows):
    with pytest.raises(SourceError, match="truncated"):
        ingest(replace(settings, max_pages=1), RecordedClient(observed_rows))
    assert not list(Path(settings.root).rglob("CURRENT.json"))


def test_offline_requires_existing_snapshot(settings):
    with pytest.raises(SourceError, match="No verified"):
        ingest(replace(settings, offline=True))


def test_cached_replay_does_not_access_network(settings, observed_rows):
    first = ingest(settings, RecordedClient(observed_rows))
    second = ingest(replace(settings, offline=True))
    assert second["cache_hit"]
    assert first["manifest"]["snapshot_sha256"] == second["manifest"]["snapshot_sha256"]


def test_page_corruption_is_detected(settings, observed_rows):
    result = ingest(settings, RecordedClient(observed_rows))
    page = Path(result["snapshot"]) / result["manifest"]["pages"][0]["file"]
    page.write_bytes(page.read_bytes() + b" ")  # Explicitly injected byte corruption.
    with pytest.raises(SourceError, match="Checksum mismatch"):
        ingest(replace(settings, offline=True))


def test_refresh_repairs_corrupt_cached_snapshot(settings, observed_rows):
    first = ingest(settings, RecordedClient(observed_rows))
    page = Path(first["snapshot"]) / first["manifest"]["pages"][0]["file"]
    page.write_bytes(b"corrupt")
    repaired = ingest(replace(settings, refresh=True), RecordedClient(observed_rows))
    assert repaired["snapshot"] != first["snapshot"]
    assert ingest(replace(settings, offline=True))["cache_hit"]


def test_source_revision_during_download_aborts(settings, observed_rows):
    class ChangingClient(RecordedClient):
        calls = 0
        def metadata(self):
            self.calls += 1
            return {**super().metadata(), "rows_updated_at": self.calls}
    with pytest.raises(SourceError, match="Source changed"):
        ingest(settings, ChangingClient(observed_rows))


@pytest.mark.parametrize("field,value,reason", [
    ("date_created", "2025-10-01T00:00:00.000", "outside"),
    ("date_created", "2025-09-31T00:00:00.000", "day is out of range"),
    ("id", "-1", "Invalid complaint"),
    ("state", "California", "State must"),
    ("issue", 123, "text"),
    ("caller_id_number", "FAULT_INJECTION", "Unexpected field"),
])
def test_contract_rejects_injected_bad_values(settings, observed_rows, field, value, reason):
    row = {**observed_rows[0], field: value}
    with pytest.raises(ValueError, match=reason):
        normalize(row, settings)


def test_missing_optional_text_becomes_explicit_unknown(settings, observed_rows):
    row = copy.deepcopy(observed_rows[0])
    row.pop("state", None)
    assert normalize(row, settings)["state"] == "UNKNOWN"


def test_quarantine_blocks_candidate(settings, observed_rows):
    rows = copy.deepcopy(observed_rows)
    rows[0]["date_created"] = "invalid"  # Fault injection, not analytical data.
    result = ingest(settings, RecordedClient(rows))
    work = Path(settings.root) / "work" / "bad"
    with pytest.raises(ContractError, match="Rejected 1"):
        validate_snapshot(result, work)
    assert len((work / "quarantine.jsonl").read_text().splitlines()) == 1
    assert not (work / "warehouse.duckdb").exists()


def test_single_writer_lock_fails_fast(settings):
    with writer_lock(Path(settings.root)):
        with pytest.raises(RuntimeError, match="Another writer"):
            with writer_lock(Path(settings.root)):
                pytest.fail("Second writer acquired lock")


def test_full_dbt_release_and_idempotent_replay(settings, observed_rows):
    first = publish(run_dbt(load_candidate(prepare(settings, observed_rows, "one"))))
    second = publish(run_dbt(load_candidate(prepare(settings, observed_rows, "two"))))
    assert first["summary"]["warehouse_rows"] == second["summary"]["warehouse_rows"] == 24
    assert second["summary"]["dbt"]["tests_passed"] >= 15
    assert current_release(Path(settings.root)).name == "two"
    with duckdb.connect(str(Path(second["release"]) / "warehouse.duckdb"), read_only=True) as con:
        assert con.execute("select count(*) from ops.covered_dates").fetchone()[0] == 30
        # The recorded fixture has only first-day complaints; all days were requested.
        assert con.execute("select min(covered_days) from analytics.weekly_wireless_issues").fetchone()[0] == 7


def test_window_replacement_reconciles_source_deletions(settings, observed_rows):
    publish(run_dbt(load_candidate(prepare(settings, observed_rows, "before"))))
    # Explicit source-deletion fault scenario over real rows; no invented behavior data.
    reduced = observed_rows[1:]
    next_settings = replace(settings, refresh=True)
    candidate = load_candidate(prepare(next_settings, reduced, "after"))
    with duckdb.connect(candidate["database"]) as con:
        assert con.execute("select count(*) from raw.complaints").fetchone()[0] == 23
        assert con.execute("select count(*) from raw.complaints where complaint_id = ?", [int(observed_rows[0]["id"])]).fetchone()[0] == 0


def test_failed_dbt_gate_preserves_published_database(settings, observed_rows, monkeypatch):
    from wireless_de import assets
    from wireless_de.cli import execute
    initial = publish(run_dbt(load_candidate(prepare(settings, observed_rows, "good"))))
    marker = (Path(settings.root) / "CURRENT.json").read_bytes()
    def fail(_):
        raise RuntimeError("Injected dbt failure")
    monkeypatch.setattr(assets, "run_dbt", fail)
    with pytest.raises(RuntimeError, match="previous release preserved"):
        execute(replace(settings, offline=True))
    assert (Path(settings.root) / "CURRENT.json").read_bytes() == marker
    assert current_release(Path(settings.root)) == Path(initial["release"])
    with duckdb.connect(str(current_release(Path(settings.root)) / "warehouse.duckdb"), read_only=True) as con:
        assert con.execute("select count(*) from raw.complaints").fetchone()[0] == 24
