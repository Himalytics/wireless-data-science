"""Download only anonymous daily issue aggregates from the authoritative FCC API."""
import argparse
import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent
BASE = 'https://opendata.fcc.gov'


def retrieve(url):
    for attempt in range(4):
        try:
            with urlopen(Request(url, headers={'User-Agent': 'WirelessDataScience/1.0'}), timeout=120) as r:
                return r.read()
        except Exception:
            if attempt == 3:
                raise
            time.sleep(2 ** attempt)


def main(refresh=False):
    dest = ROOT / 'data' / 'raw'
    dest.mkdir(parents=True, exist_ok=True)
    if (dest / 'manifest.json').exists() and not refresh:
        return
    plan = json.loads((ROOT / 'experiment_plan.json').read_text())
    where = (f"ticket_created >= '{plan['start']}T00:00:00Z' AND "
             f"ticket_created < '{plan['end_exclusive']}T00:00:00Z' AND "
             "issue_type='Phone' AND method in ('Wireless (cell phone/other mobile device)','Wireless')")
    queries = {
        'daily_issues': {'$select': "date_trunc_ymd(to_floating_timestamp(ticket_created,'UTC')) as day,issue,count(*) as n,count(distinct id) as unique_ids",
                         '$where': where, '$group': 'day,issue', '$order': 'day,issue', '$limit': 50000},
        'audit': {'$select': 'count(*) as n,count(distinct id) as unique_ids,count(id) as nonnull_ids,min(ticket_created) as first,max(ticket_created) as last', '$where': where},
        'missing_dates': {'$select': 'count(*) as n', '$where': "ticket_created is null AND issue_type='Phone' AND method in ('Wireless (cell phone/other mobile device)','Wireless')"},
        'date_agreement': {'$select': 'count(*) as n', '$where': where + " AND date_trunc_ymd(date_created) != date_trunc_ymd(to_floating_timestamp(ticket_created,'UTC'))"},
    }
    manifest = {'retrieved_at_utc': datetime.now(timezone.utc).isoformat(),
                'publisher': 'Federal Communications Commission, Consumer Inquiries and Complaints Division',
                'dataset': 'CGB - Consumer Complaints Data', 'dataset_id': plan['source_id'],
                'license': 'Public Domain U.S. Government (USGOV_WORKS)', 'files': {}}
    for name, params in queries.items():
        url = BASE + '/resource/3xyp-aqkj.json?' + urlencode(params)
        raw = retrieve(url)
        parsed = json.loads(raw)
        if name == 'daily_issues' and len(parsed) >= 50000:
            raise ValueError('API row cap reached; pagination required')
        (dest / f'{name}.json').write_bytes(raw)
        manifest['files'][name] = {'url': url, 'sha256': hashlib.sha256(raw).hexdigest(), 'rows': len(parsed)}
        print(name, len(parsed), flush=True)
    raw = retrieve(BASE + '/api/views/3xyp-aqkj.json')
    metadata = json.loads(raw)
    if metadata.get('licenseId') != 'USGOV_WORKS':
        raise ValueError('Source licence changed: review before use')
    (dest / 'metadata.json').write_bytes(raw)
    manifest['files']['metadata'] = {'url': BASE + '/api/views/3xyp-aqkj.json', 'sha256': hashlib.sha256(raw).hexdigest()}
    manifest['source_rows_updated_at'] = metadata.get('rowsUpdatedAt')
    # Write the cache sentinel last: a partial download is never accepted.
    (dest / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print('Source snapshot downloaded and hashed', flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--refresh', action='store_true')
    main(p.parse_args().refresh)
