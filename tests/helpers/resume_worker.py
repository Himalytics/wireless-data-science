"""Child process for labelled crash tests. Never targets another process."""
import argparse
import json
import os
import signal
from pathlib import Path

from wireless_de import source
from wireless_de.io import atomic_json
from wireless_de.resumable import ingest_resumable
from wireless_de.settings import Settings

parser = argparse.ArgumentParser()
parser.add_argument("--root", required=True)
parser.add_argument("--project", required=True)
parser.add_argument("--base-url", required=True)
parser.add_argument("--output", required=True)
parser.add_argument("--kill-at", default="none")
parser.add_argument("--kill-page", type=int, default=2)
parser.add_argument("--offline", action="store_true")
args = parser.parse_args()
source.ENDPOINT = args.base_url + "/records"
source.METADATA = args.base_url + "/metadata"
client = source.FccClient()
# The fixture uses loopback HTTP. Apply the same retry adapter used for public HTTPS.
client.session.mount("http://", client.session.adapters["https://"])


def observer(event, info):
    if event == args.kill_at and (args.kill_page == 0 or info["page_number"] == args.kill_page):
        os.kill(os.getpid(), signal.SIGKILL)


settings = Settings(project=args.project, root=args.root, page_size=5, resumable=True, offline=args.offline)
result = ingest_resumable(settings, client=client, on_event=observer)
atomic_json(Path(args.output), result)
