"""Crash-recoverable extraction with page bytes and cursor in one SQLite commit.

This is a local single-writer protocol, not distributed exactly-once delivery.
Completed sessions hydrate the existing immutable bronze snapshot interface.
"""
import json
import re
import shutil
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from wireless_de.io import atomic_json, read_json, sha256, writer_lock
from wireless_de.settings import Settings
from wireless_de.source import DATASET, ENDPOINT, FIELDS, FccClient, SourceError, verify_snapshot


def request_identity(settings):
    return {"dataset": DATASET, "fields": list(FIELDS), "start": settings.start,
            "end": settings.end, "page_size": settings.page_size, "protocol": 1}


def ledger_directory(settings):
    key = sha256(json.dumps(request_identity(settings), sort_keys=True).encode())
    return Path(settings.root) / "checkpoints" / key


def _connect(path):
    con = sqlite3.connect(path, isolation_level=None, timeout=5)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA synchronous=FULL")
    con.execute("PRAGMA foreign_keys=ON")
    if con.execute("PRAGMA quick_check").fetchone()[0] != "ok":
        con.close()
        raise SourceError("Checkpoint database failed integrity check")
    con.executescript("""
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY, request_json TEXT NOT NULL,
            metadata_json TEXT NOT NULL, expected_rows INTEGER NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('WRITING','COMPLETE','INVALID','ABANDONED')),
            cursor INTEGER NOT NULL DEFAULT -1, n_pages INTEGER NOT NULL DEFAULT 0,
            n_rows INTEGER NOT NULL DEFAULT 0, started_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS pages (
            session_id TEXT NOT NULL REFERENCES sessions(id),
            page_number INTEGER NOT NULL, cursor_before INTEGER NOT NULL,
            cursor_after INTEGER NOT NULL, row_count INTEGER NOT NULL,
            content BLOB NOT NULL, checksum TEXT NOT NULL, query_json TEXT NOT NULL,
            PRIMARY KEY(session_id, page_number)
        );
        CREATE UNIQUE INDEX IF NOT EXISTS one_writing_session
        ON sessions(status) WHERE status = 'WRITING';
    """)
    return con


@contextmanager
def _transaction(con):
    con.execute("BEGIN IMMEDIATE")
    try:
        yield
        con.execute("COMMIT")
    except BaseException:
        if con.in_transaction:
            con.execute("ROLLBACK")
        raise


def _state(con, session_id):
    return dict(con.execute("SELECT * FROM sessions WHERE id = ?", [session_id]).fetchone())


def _validate_page(content, checksum, cursor_before, cursor_after, count):
    if sha256(content) != checksum:
        raise SourceError("Checkpoint page checksum mismatch; preserve evidence and use --refresh")
    rows = json.loads(content)
    if not isinstance(rows, list) or not rows or len(rows) != count:
        raise SourceError("Checkpoint page row-count/type mismatch")
    if any(not re.fullmatch(r"[0-9]+", str(r.get("id", ""))) for r in rows):
        raise SourceError("Page contains an invalid numeric source key")
    ids = [int(r["id"]) for r in rows]
    if ids != sorted(set(ids)) or ids[0] <= cursor_before or ids[-1] != cursor_after:
        raise SourceError("Checkpoint page is not strictly ordered after its committed cursor")
    return rows


def _verify_ledger_pages(con, session):
    cursor, rows, pages = -1, 0, 0
    for page in con.execute("SELECT * FROM pages WHERE session_id = ? ORDER BY page_number", [session["id"]]):
        if page["page_number"] != pages + 1 or page["cursor_before"] != cursor:
            raise SourceError("Checkpoint page/cursor chain is broken")
        _validate_page(page["content"], page["checksum"], cursor, page["cursor_after"], page["row_count"])
        cursor = page["cursor_after"]
        rows += page["row_count"]
        pages += 1
    if (cursor, rows, pages) != (session["cursor"], session["n_rows"], session["n_pages"]):
        raise SourceError("Checkpoint counters differ from committed page contents")


def _hydrate(con, session, settings):
    _verify_ledger_pages(con, session)
    if session["status"] != "COMPLETE" or session["n_rows"] != session["expected_rows"]:
        raise SourceError("Cannot publish an incomplete extraction session")
    partition = Path(settings.root) / "bronze" / f"{settings.start}_{settings.end}"
    work = partition / (".checkpoint-hydration-" + uuid.uuid4().hex)
    work.mkdir(parents=True)
    entries = []
    try:
        for page in con.execute("SELECT * FROM pages WHERE session_id = ? ORDER BY page_number", [session["id"]]):
            name = f"page-{page['page_number'] - 1:05d}.json"
            (work / name).write_bytes(page["content"])
            entries.append({"file": name, "rows": page["row_count"], "sha256": page["checksum"],
                            "query": json.loads(page["query_json"])})
        digest = sha256((settings.start + settings.end + "".join(p["sha256"] for p in entries)).encode())
        manifest = {"dataset": DATASET, "start": settings.start, "end": settings.end,
                    "downloaded_at_utc": session["started_at"],
                    "source_metadata": json.loads(session["metadata_json"]),
                    "expected_rows": session["expected_rows"], "pages": entries,
                    "snapshot_sha256": digest, "source_url": ENDPOINT,
                    "extraction_session": session["id"],
                    "snapshot_isolation": "best effort: matching source metadata and counts before/after; no source transaction token"}
        atomic_json(work / "manifest.json", manifest)
        destination = partition / digest
        if destination.exists():
            try:
                verify_snapshot(destination, settings)
            except (SourceError, OSError, ValueError, KeyError):
                destination = partition / (digest + "-ledger-repair-" + uuid.uuid4().hex[:8])
        if destination.exists():
            shutil.rmtree(work)
        else:
            work.rename(destination)
        verify_snapshot(destination, settings)
        atomic_json(partition / "CURRENT.json", {"snapshot": destination.name})
        return destination, read_json(destination / "manifest.json")
    except BaseException:
        shutil.rmtree(work, ignore_errors=True)
        raise


def ingest_resumable(settings: Settings, client=None, on_event=None):
    """Resume only committed pages and only when the observed source stamp matches.

    on_event is an optional observer used by process-kill experiments. Production
    code has no environment-variable kill switches or implicit fault injection.
    """
    settings.validate()
    directory = ledger_directory(settings)
    observer = on_event or (lambda event, info: None)
    with writer_lock(directory):
        con = _connect(directory / "ledger.sqlite3")
        downloaded, reused = 0, 0
        try:
            latest = con.execute("SELECT * FROM sessions ORDER BY rowid DESC LIMIT 1").fetchone()
            session = dict(latest) if latest else None
            if session and json.loads(session["request_json"]) != request_identity(settings):
                raise SourceError("Checkpoint request identity mismatch")
            if session and session["status"] == "INVALID" and not settings.refresh:
                raise SourceError("Source revision invalidated this session; use --refresh to start a new one")
            if session and session["status"] == "COMPLETE" and not settings.refresh:
                reused = session["n_pages"]
            else:
                if settings.offline:
                    raise SourceError("Offline resume requires a COMPLETE checkpoint session")
                client = client or FccClient()
                before = client.metadata()
                where = f"date_created >= '{settings.start}T00:00:00' AND date_created < '{settings.end}T00:00:00'"
                count, _ = client.query({"$select": "count(*) as n", "$where": where})
                expected = int(count[0]["n"])
                if expected < 1:
                    raise SourceError("Zero-row extraction windows are not supported by the current downstream contract")
                stamp = json.dumps(before, sort_keys=True)
                if session and session["status"] == "WRITING" and not settings.refresh:
                    if (session["metadata_json"], session["expected_rows"]) != (stamp, expected):
                        con.execute("UPDATE sessions SET status = 'INVALID' WHERE id = ?", [session["id"]])
                        raise SourceError("Source revision changed across interruption; use --refresh")
                    _verify_ledger_pages(con, session)
                    reused = session["n_pages"]
                else:
                    with _transaction(con):
                        con.execute("UPDATE sessions SET status = 'ABANDONED' WHERE status = 'WRITING'")
                        sid = uuid.uuid4().hex
                        con.execute("INSERT INTO sessions(id,request_json,metadata_json,expected_rows,status,started_at) VALUES(?,?,?,?,?,?)",
                                    [sid, json.dumps(request_identity(settings), sort_keys=True), stamp,
                                     expected, "WRITING", datetime.now(timezone.utc).isoformat()])
                    session = _state(con, sid)
                while session["n_rows"] < expected:
                    if session["n_pages"] >= settings.max_pages:
                        raise SourceError("Checkpoint extraction reached max_pages; increase the budget to resume safely")
                    query = {"$select": ",".join(FIELDS), "$where": where + f" AND id > {session['cursor']}",
                             "$order": "id ASC", "$limit": str(settings.page_size)}
                    rows, content = client.query(query)
                    if not rows or len(rows) > settings.page_size:
                        raise SourceError("Unexpected empty/oversized page before the expected source count")
                    last_id = int(rows[-1]["id"])
                    digest = sha256(content)
                    decoded = _validate_page(content, digest, session["cursor"], last_id, len(rows))
                    if decoded != rows or session["n_rows"] + len(rows) > expected:
                        raise SourceError("Page response/count differs from the requested extraction")
                    number = session["n_pages"] + 1
                    event = {"session_id": session["id"], "page_number": number, "rows": len(rows)}
                    with _transaction(con):
                        con.execute("INSERT INTO pages VALUES(?,?,?,?,?,?,?,?)", [session["id"], number,
                                    session["cursor"], last_id, len(rows), content, digest, json.dumps(query, sort_keys=True)])
                        changed = con.execute("UPDATE sessions SET cursor=?,n_pages=n_pages+1,n_rows=n_rows+? WHERE id=? AND cursor=? AND n_pages=? AND status='WRITING'",
                                              [last_id, len(rows), session["id"], session["cursor"], session["n_pages"]]).rowcount
                        if changed != 1:
                            raise SourceError("Checkpoint cursor changed unexpectedly")
                        observer("before_checkpoint_commit", event)
                    downloaded += 1
                    observer("after_checkpoint_commit", event)
                    session = _state(con, session["id"])
                after = client.metadata()
                count_after, _ = client.query({"$select": "count(*) as n", "$where": where})
                if before != after or int(count_after[0]["n"]) != expected:
                    con.execute("UPDATE sessions SET status = 'INVALID' WHERE id = ?", [session["id"]])
                    raise SourceError("Source changed during extraction; invalidated session, use --refresh")
                _verify_ledger_pages(con, session)
                con.execute("UPDATE sessions SET status = 'COMPLETE' WHERE id = ?", [session["id"]])
                session = _state(con, session["id"])
                observer("after_session_complete", {"session_id": session["id"], "page_number": session["n_pages"]})
            destination, manifest = _hydrate(con, session, settings)
            return {"settings": settings.dict(), "snapshot": str(destination), "manifest": manifest,
                    "cache_hit": downloaded == 0,
                    "resumability": {"session_id": session["id"], "ledger": str(directory / "ledger.sqlite3"),
                                     "pages_reused": reused, "pages_downloaded": downloaded,
                                     "total_committed_pages": session["n_pages"], "status": session["status"]}}
        finally:
            con.close()
