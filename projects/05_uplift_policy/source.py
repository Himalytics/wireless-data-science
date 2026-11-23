"""Pinned publisher-hosted source, bounded-memory deterministic row sampling."""
from pathlib import Path
import datetime as dt
import hashlib
import json
import urllib.request
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
REVISION = '2424920019e49d52d72c13ac1143ec5d53af276b'
URL = f'https://huggingface.co/datasets/criteo/criteo-uplift/resolve/{REVISION}/criteo-research-uplift-v2.1.csv.gz'
FEATURES = [f'f{i}' for i in range(12)]

def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1024*1024), b''): h.update(b)
    return h.hexdigest()

def mix(x):
    with np.errstate(over='ignore'):
        x = np.asarray(x, dtype='uint64') + np.uint64(0x9E3779B97F4A7C15)
        x = (x ^ (x >> np.uint64(30))) * np.uint64(0xBF58476D1CE4E5B9)
        x = (x ^ (x >> np.uint64(27))) * np.uint64(0x94D049BB133111EB)
        return x ^ (x >> np.uint64(31))

def load():
    data = ROOT/'data'; data.mkdir(exist_ok=True)
    raw = data/'criteo.csv.gz'
    if not raw.exists():
        tmp = raw.with_suffix('.partial')
        urllib.request.urlretrieve(URL, tmp)
        tmp.rename(raw)
    digest = sha(raw)
    assert digest == '2716e1bf0fd157a93b5bf86924d9088419dfbac2022c6cd90030220634f616dc', 'Publisher LFS SHA256 mismatch'
    lock = ROOT/'results/source.json'
    if lock.exists():
        assert json.loads(lock.read_text())['sha256'] == digest, 'Input source changed'
    cache = data/'sample.pkl'
    if cache.exists(): return pd.read_pickle(cache)
    rows = 0; sample = []
    for chunk in pd.read_csv(raw, chunksize=250000):
        ids = np.arange(rows, rows+len(chunk), dtype='uint64'); rows += len(chunk)
        mask = mix(ids) % np.uint64(20) == 0
        part = chunk.loc[mask].copy(); part.insert(0,'row_id',ids[mask]); sample.append(part)
    assert rows == 13979592, 'Not the corrected v2.1 source'
    d = pd.concat(sample, ignore_index=True)
    assert list(d.columns) == ['row_id']+FEATURES+['treatment','conversion','visit','exposure']
    assert d.notna().all().all() and np.isfinite(d[FEATURES]).all().all()
    for c in ['treatment','conversion','visit','exposure']: assert set(d[c].unique()) == {0,1}
    d['profile'] = pd.util.hash_pandas_object(d[FEATURES], index=False).astype('uint64')
    bucket = mix(d.profile.to_numpy()) % np.uint64(100)
    d['split'] = np.where(bucket < 50,'train',np.where(bucket < 70,'validation','test'))
    d.to_pickle(cache)
    lock.parent.mkdir(exist_ok=True)
    lock.write_text(json.dumps(dict(publisher='Criteo AI Lab', version='CRITEO-UPLIFT v2.1',
        revision=REVISION,url=URL,sha256=digest,bytes=raw.stat().st_size,source_rows=rows,
        sample_rows=len(d),retrieved_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
        licence='CC BY-NC-SA 4.0',licence_url='https://creativecommons.org/licenses/by-nc-sa/4.0/',
        citation='Diemert, Betlei, Renaudin & Amini (2018), A Large Scale Benchmark for Uplift Modeling, AdKDD',
        source_card='https://huggingface.co/datasets/criteo/criteo-uplift',
        sampling='SplitMix64 zero-based source row ID modulo 20 == 0'),indent=2)+'\n')
    return d
