import argparse
import json
import platform
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from dagster import materialize, mem_io_manager

from wireless_de.assets import ALL_ASSETS
from wireless_de.io import atomic_json, current_release, read_json, writer_lock
from wireless_de.settings import Settings


def execute(settings):
    settings.validate()
    root = Path(settings.root)
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S") + "-" + uuid.uuid4().hex[:8]
    work = root / "work" / run_id
    started = time.monotonic()
    with writer_lock(root):
        work.mkdir(parents=True)
        result = materialize(ALL_ASSETS, run_config={"ops": {"fcc_snapshot": {"config": {
            **settings.dict(), "work": str(work)}}}},
            resources={"io_manager": mem_io_manager}, raise_on_error=False)
        evidence = {"run_id": run_id, "success": result.success,
                    "elapsed_seconds": round(time.monotonic() - started, 3),
                    "executed_at_utc": datetime.now(timezone.utc).isoformat(),
                    "python": platform.python_version(), "platform": platform.platform(),
                    "settings": settings.dict(), "dagster_run_id": result.run_id,
                    "failed_steps": [e.step_key for e in result.get_step_failure_events()]}
        atomic_json(root / "runs" / f"{run_id}.json", evidence)
        if not result.success:
            raise RuntimeError(f"Pipeline failed; previous release preserved. Inspect {work} and data/runs/{run_id}.json")
        release = current_release(root)
        atomic_json(release / "execution.json", evidence)
        return {"release": str(release), "execution": evidence, "summary": read_json(release / "summary.json")}


def main():
    parser = argparse.ArgumentParser(description="Real public telecom complaint data platform")
    parser.add_argument("command", choices=["run", "inspect"])
    parser.add_argument("--project", default=str(Path.cwd()))
    parser.add_argument("--root", default="data")
    parser.add_argument("--start", default="2025-09-01")
    parser.add_argument("--end", default="2025-10-01", help="exclusive upper bound")
    parser.add_argument("--page-size", type=int, default=5000)
    parser.add_argument("--max-pages", type=int, default=100)
    parser.add_argument("--refresh", action="store_true")
    parser.add_argument("--offline", action="store_true")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    try:
        if args.command == "inspect":
            release = current_release(root)
            if not release:
                parser.exit(1, "No published release yet. Run the pipeline first.\n")
            print(json.dumps({"release": str(release), "summary": read_json(release / "summary.json")}, indent=2))
        else:
            result = execute(Settings(project=str(Path(args.project).resolve()), root=str(root),
                start=args.start, end=args.end, page_size=args.page_size,
                max_pages=args.max_pages, refresh=args.refresh, offline=args.offline))
            print(json.dumps(result, indent=2))
    except (RuntimeError, ValueError, OSError) as exc:
        parser.exit(1, f"ERROR: {exc}\n")


if __name__ == "__main__":
    main()
