"""Retrieve and reconcile anonymous UTC-day complaint aggregates."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen

import pandas as pd

ROOT = Path(__file__).resolve().parent
PLAN = json.loads((ROOT / "protocol.json").read_text())
BASE = "https://opendata.fcc.gov"
API = BASE + "/resource/3xyp-aqkj.json"
META = BASE + "/api/views/3xyp-aqkj.json"
COHORT = "issue_type='Phone' AND method in ('Wireless (cell phone/other mobile device)','Wireless')"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def fetch(url):
    with urlopen(url, timeout=60) as response:
        raw = response.read()
    return json.loads(raw), {"url": url, "sha256": sha(raw)}


def query(**parameters):
    return fetch(API + "?" + urlencode({"$" + key: value for key, value in parameters.items()}))


def main():
    metadata, meta_record = fetch(META)
    fields = {column["fieldName"] for column in metadata["columns"]}
    if metadata.get("licenseId") != "USGOV_WORKS" or not {"id", "ticket_created", "issue_type", "method", "issue"} <= fields:
        raise ValueError("Review FCC metadata before continuing")
    where = (COHORT + f" AND ticket_created >= '{PLAN['start']}T00:00:00Z'"
             f" AND ticket_created < '{PLAN['end_exclusive']}T00:00:00Z'")
    day = "date_trunc_ymd(to_floating_timestamp(ticket_created,'UTC'))"
    rows, daily_record = query(select=f"{day} AS day,count(*) AS n,"
                               "sum(case(issue='Unwanted Calls',1,true,0)) AS unwanted",
                               where=where, group=day, order="day", limit=5000)
    audit, audit_record = query(select="count(*) AS n,count(distinct id) AS ids", where=where)
    daily = pd.DataFrame(rows)
    daily["day"] = pd.to_datetime(daily.day).dt.normalize()
    daily[["n", "unwanted"]] = daily[["n", "unwanted"]].astype(int)
    if len(daily) >= 5000 or not daily.day.is_unique or not daily.unwanted.between(0, daily.n).all():
        raise ValueError("Unexpected aggregate shape")
    if int(daily.n.sum()) != int(audit[0]["n"]) or audit[0]["n"] != audit[0]["ids"]:
        raise ValueError("Daily totals or distinct ticket counts failed reconciliation")
    dates = pd.date_range(PLAN["start"], PLAN["end_exclusive"], inclusive="left", name="day")
    if not daily.day.isin(dates).all() or len(dates) % 7:
        raise ValueError("Check downloaded boundaries and complete weeks")
    frame = daily.set_index("day").reindex(dates, fill_value=0)
    frame["source_day_present"] = frame.index.isin(daily.day)
    output = ROOT / "data"
    output.mkdir(exist_ok=True)
    snapshot = frame.to_csv().encode()
    (output / "fcc_daily_counts.csv").write_bytes(snapshot)
    manifest = {"retrieved_at_utc": datetime.now(timezone.utc).isoformat(), "publisher": "FCC Consumer and Governmental Affairs Bureau",
                "dataset_id": "3xyp-aqkj", "licence": "USGOV_WORKS", "source_rows_updated_at": metadata.get("rowsUpdatedAt"),
                "metadata": meta_record, "daily_query": daily_record, "audit_query": audit_record,
                "snapshot_sha256": sha(snapshot), "counts": int(frame.n.sum()), "distinct_tickets": int(audit[0]["ids"]),
                "absent_calendar_days": int((~frame.source_day_present).sum()), "scope": where}
    (output / "source_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
