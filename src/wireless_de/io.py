import contextlib
import fcntl
import hashlib
import json
import os
import tempfile
from pathlib import Path


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def atomic_json(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(dir=path.parent, prefix=".write-")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(value, f, indent=2, sort_keys=True, default=str)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def read_json(path):
    return json.loads(Path(path).read_text())


@contextlib.contextmanager
def writer_lock(root: Path):
    root.mkdir(parents=True, exist_ok=True)
    with (root / ".writer.lock").open("a+") as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RuntimeError("Another writer is active for this data directory") from exc
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


def current_release(root: Path):
    marker = root / "CURRENT.json"
    if not marker.exists():
        return None
    value = read_json(marker)
    path = (root / value["release"]).resolve()
    if not path.is_relative_to(root.resolve()) or not (path / "READY.json").is_file():
        raise RuntimeError("Invalid published release pointer")
    return path
