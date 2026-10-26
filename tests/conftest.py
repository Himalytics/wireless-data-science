import json
import re
from pathlib import Path

import pytest

from wireless_de.settings import Settings
from wireless_de.source import FIELDS

PROJECT = Path(__file__).resolve().parents[1]


@pytest.fixture
def observed_rows():
    return json.loads((PROJECT / "tests/fixtures/fcc_24_observed_records.json").read_text())


@pytest.fixture
def settings(tmp_path):
    return Settings(project=str(PROJECT), root=str(tmp_path / "data"), page_size=5)


class RecordedClient:
    """Mock transport over actual FCC records; no generated production observations."""
    def __init__(self, rows):
        self.rows = rows
        self.queries = []

    def metadata(self):
        return {"dataset": "3xyp-aqkj", "name": "Recorded FCC fixture",
                "rows_updated_at": 1, "license": {"name": "Public Domain U.S. Government"},
                "selected_fields": {x: "number" if x == "id" else "text" for x in FIELDS}}

    def query(self, params):
        self.queries.append(params)
        if params["$select"].startswith("count"):
            rows = [{"n": str(len(self.rows))}]
        else:
            after = int(re.search(r"id > (-?\d+)", params["$where"])[1])
            rows = [r for r in self.rows if int(r["id"]) > after][:int(params["$limit"])]
        return rows, json.dumps(rows, sort_keys=True).encode()
