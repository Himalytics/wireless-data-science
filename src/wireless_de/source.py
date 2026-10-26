"""Bounded, keyset-paginated ingestion of projected FCC public records."""
import json
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from wireless_de.io import atomic_json, read_json, sha256
from wireless_de.settings import Settings

DATASET = "3xyp-aqkj"
ENDPOINT = f"https://opendata.fcc.gov/resource/{DATASET}.json"
METADATA = f"https://opendata.fcc.gov/api/views/{DATASET}.json"
FIELDS = ("id", "date_created", "issue_type", "method", "issue", "state")
REQUIRED_SOURCE_FIELDS = {"id", "date_created", "issue_type", "method", "issue", "state"}


class SourceError(RuntimeError):
    pass


class FccClient:
    def __init__(self):
        self.session = requests.Session()
        retries = Retry(total=3, connect=3, read=3, status=3,
                        backoff_factor=0.5, status_forcelist=[429, 500, 502, 503, 504],
                        allowed_methods=["GET"], respect_retry_after_header=True)
        self.session.mount("https://", HTTPAdapter(max_retries=retries))
        self.session.headers["User-Agent"] = "wireless-data-engineering/0.1 public research"

    def metadata(self):
        response = self.session.get(METADATA, timeout=(10, 45))
        response.raise_for_status()
        source = response.json()
        fields = {c["fieldName"]: c.get("dataTypeName") for c in source["columns"]}
        missing = REQUIRED_SOURCE_FIELDS - fields.keys()
        if missing:
            raise SourceError(f"Source schema changed: missing {sorted(missing)}")
        if fields["id"] != "number" or fields["date_created"] != "calendar_date":
            raise SourceError("Source key/date types changed")
        # Store selected metadata, never download phone-number or address columns.
        return {"dataset": DATASET, "name": source["name"],
                "rows_updated_at": source.get("rowsUpdatedAt"),
                "license": source.get("license"),
                "selected_fields": {k: fields[k] for k in FIELDS}}

    def query(self, params):
        response = self.session.get(ENDPOINT, params=params, timeout=(10, 45))
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, list):
            raise SourceError("Expected a JSON array from FCC")
        return data, response.content


def verify_snapshot(path: Path, settings: Settings):
    manifest = read_json(path / "manifest.json")
    if (manifest["start"], manifest["end"], manifest["dataset"]) != (
            settings.start, settings.end, DATASET):
        raise SourceError("Snapshot does not match requested dataset/window")
    checksum_parts, rows = [], 0
    for entry in manifest["pages"]:
        page = path / entry["file"]
        if page.parent.resolve() != path.resolve():
            raise SourceError("Invalid page filename")
        content = page.read_bytes()
        digest = sha256(content)
        if digest != entry["sha256"]:
            raise SourceError(f"Checksum mismatch in {entry['file']}; use --refresh")
        decoded = json.loads(content)
        if not isinstance(decoded, list) or len(decoded) != entry["rows"]:
            raise SourceError("Page count/type does not match manifest")
        rows += len(decoded)
        checksum_parts.append(digest)
    snapshot_id = sha256((manifest["start"] + manifest["end"] + "".join(checksum_parts)).encode())
    if snapshot_id != manifest["snapshot_sha256"] or rows != manifest["expected_rows"]:
        raise SourceError("Snapshot identity/count mismatch")
    return manifest


def ingest(settings: Settings, client=None):
    partition = Path(settings.root) / "bronze" / f"{settings.start}_{settings.end}"
    pointer = partition / "CURRENT.json"
    if pointer.exists() and not settings.refresh:
        snapshot = partition / read_json(pointer)["snapshot"]
        if snapshot.parent.resolve() != partition.resolve():
            raise SourceError("Invalid cached snapshot pointer")
        manifest = verify_snapshot(snapshot, settings)
        return {"settings": settings.dict(), "snapshot": str(snapshot),
                "manifest": manifest, "cache_hit": True}
    if settings.offline:
        raise SourceError("No verified cached snapshot for this date window")
    client = client or FccClient()
    before = client.metadata()
    where = f"date_created >= '{settings.start}T00:00:00' AND date_created < '{settings.end}T00:00:00'"
    count, _ = client.query({"$select": "count(*) as n", "$where": where})
    expected = int(count[0]["n"])
    if expected == 0:
        raise SourceError("No source rows in this window; choose another closed period")
    work = partition / (".download-" + uuid.uuid4().hex)
    work.mkdir(parents=True, exist_ok=False)
    pages, count_downloaded, last_id = [], 0, -1
    try:
        for index in range(settings.max_pages):
            params = {"$select": ",".join(FIELDS),
                      "$where": where + f" AND id > {last_id}",
                      "$order": "id ASC", "$limit": str(settings.page_size)}
            rows, content = client.query(params)
            if not rows:
                break
            ids = [int(row["id"]) for row in rows]
            if ids != sorted(ids) or ids[0] <= last_id or len(set(ids)) != len(ids):
                raise SourceError("Keyset pagination requires strictly increasing unique IDs")
            last_id = ids[-1]
            filename = f"page-{index:05d}.json"
            (work / filename).write_bytes(content)
            pages.append({"file": filename, "rows": len(rows), "sha256": sha256(content),
                          "query": params})
            count_downloaded += len(rows)
            if len(rows) < settings.page_size:
                break
        else:
            raise SourceError("max_pages reached; refusing to publish a possibly truncated extract")
        after = client.metadata()
        count_after, _ = client.query({"$select": "count(*) as n", "$where": where})
        if before != after or int(count_after[0]["n"]) != expected:
            raise SourceError("Source changed during extraction; retry --refresh")
        if count_downloaded != expected:
            raise SourceError(f"Expected {expected} rows, downloaded {count_downloaded}")
        digest = sha256((settings.start + settings.end + "".join(p["sha256"] for p in pages)).encode())
        manifest = {"dataset": DATASET, "start": settings.start, "end": settings.end,
                    "downloaded_at_utc": datetime.now(timezone.utc).isoformat(),
                    "source_metadata": before, "expected_rows": expected, "pages": pages,
                    "snapshot_sha256": digest, "source_url": ENDPOINT,
                    "snapshot_isolation": "best effort: metadata and count checked before/after; API has no transaction token"}
        atomic_json(work / "manifest.json", manifest)
        destination = partition / digest
        if destination.exists():
            # A refresh must repair a corrupt copy rather than silently reuse it.
            try:
                verify_snapshot(destination, settings)
            except (SourceError, OSError, ValueError, KeyError):
                destination = partition / (digest + "-repaired-" + uuid.uuid4().hex[:8])
        if destination.exists():
            shutil.rmtree(work)
        else:
            work.rename(destination)
        atomic_json(pointer, {"snapshot": destination.name})
        return {"settings": settings.dict(), "snapshot": str(destination),
                "manifest": verify_snapshot(destination, settings), "cache_hit": False}
    except Exception:
        shutil.rmtree(work, ignore_errors=True)
        raise
