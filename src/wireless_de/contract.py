"""Fail-closed row contract; rejected source rows never reach the warehouse."""
import json
import re
from datetime import date
from pathlib import Path

import polars as pl

from wireless_de.io import atomic_json, sha256
from wireless_de.settings import Settings
from wireless_de.source import FIELDS, verify_snapshot


class ContractError(RuntimeError):
    pass


SCHEMA = {"complaint_id": pl.Int64, "complaint_date": pl.Date,
          "issue_type": pl.String, "method": pl.String, "issue": pl.String,
          "state": pl.String, "record_sha256": pl.String,
          "snapshot_sha256": pl.String, "ingested_at_utc": pl.String}


def normalize(row, settings):
    if set(row) - set(FIELDS):
        raise ValueError("Unexpected field: source projection drift")
    if not re.fullmatch(r"[0-9]+", str(row.get("id", ""))):
        raise ValueError("Invalid complaint ID")
    complaint_id = int(row["id"])
    if complaint_id < 1:
        raise ValueError("Complaint ID must be positive")
    raw_date = row.get("date_created")
    if not isinstance(raw_date, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}T00:00:00(?:\.0+)?", raw_date):
        raise ValueError("Expected source calendar date at midnight")
    day = date.fromisoformat(raw_date[:10])
    if not date.fromisoformat(settings.start) <= day < date.fromisoformat(settings.end):
        raise ValueError("Record is outside requested half-open date window")
    values = {}
    for name in ("issue_type", "method", "issue", "state"):
        value = row.get(name)
        if value is not None and not isinstance(value, str):
            raise ValueError(f"{name} must be text or absent")
        values[name] = (value or "").strip() or "UNKNOWN"
    values["state"] = values["state"].upper()
    if values["state"] != "UNKNOWN" and not re.fullmatch(r"[A-Z]{2}", values["state"]):
        raise ValueError("State must be two letters or UNKNOWN")
    canonical = {"complaint_id": complaint_id, "complaint_date": day.isoformat(), **values}
    return {**canonical, "complaint_date": day,
            "record_sha256": sha256(json.dumps(canonical, sort_keys=True).encode())}


def validate_snapshot(payload, work: Path):
    settings = Settings(**payload["settings"]).validate()
    snapshot = Path(payload["snapshot"])
    manifest = verify_snapshot(snapshot, settings)
    work.mkdir(parents=True, exist_ok=True)
    accepted, rejected, seen = [], [], set()
    for page in manifest["pages"]:
        for row in json.loads((snapshot / page["file"]).read_bytes()):
            try:
                clean = normalize(row, settings)
                if clean["complaint_id"] in seen:
                    raise ValueError("Duplicate complaint ID across pages")
                seen.add(clean["complaint_id"])
                accepted.append({**clean, "snapshot_sha256": manifest["snapshot_sha256"],
                                 "ingested_at_utc": manifest["downloaded_at_utc"]})
            except (ValueError, TypeError) as exc:
                rejected.append({"reason": str(exc), "source_row": row})
    atomic_json(work / "quality.json", {"accepted": len(accepted), "rejected": len(rejected),
                "expected": manifest["expected_rows"], "policy": "zero rejected rows"})
    if rejected:
        with (work / "quarantine.jsonl").open("w") as f:
            for row in rejected:
                f.write(json.dumps(row) + "\n")
        raise ContractError(f"Rejected {len(rejected)} rows; inspect quarantine.jsonl")
    if not accepted or len(accepted) != manifest["expected_rows"]:
        raise ContractError("Row conservation failed")
    parquet = work / "validated.parquet"
    pl.DataFrame(accepted, schema=SCHEMA).write_parquet(parquet, compression="zstd")
    return {**payload, "work": str(work), "parquet": str(parquet), "rows": len(accepted)}
