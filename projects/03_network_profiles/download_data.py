"""Public authoritative ingestion, full source hashes, and centroid county join."""
from pathlib import Path
from datetime import datetime, timezone
from urllib.request import urlopen, Request
import hashlib
import json
import time
import geopandas as gpd
import pandas as pd
import pyarrow.parquet as pq

ROOT=Path(__file__).resolve().parent
RAW=ROOT/'data/raw'
R=ROOT/'results'
URLS={
 'counties':'https://www2.census.gov/geo/tiger/GENZ2024/shp/cb_2024_us_county_500k.zip',
 'population':'https://www2.census.gov/programs-surveys/popest/datasets/2020-2024/counties/totals/co-est2024-alldata.csv',
 '2025Q4':'https://ookla-open-data.s3.amazonaws.com/parquet/performance/type=mobile/year=2025/quarter=4/2025-10-01_performance_mobile_tiles.parquet',
 '2026Q1':'https://ookla-open-data.s3.amazonaws.com/parquet/performance/type=mobile/year=2026/quarter=1/2026-01-01_performance_mobile_tiles.parquet',
 'ookla_readme':'https://raw.githubusercontent.com/teamookla/ookla-open-data/master/README.md'
}


def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


def download(url,path):
    if path.exists():return {'cached':True}
    for attempt in range(3):
        try:
            partial=path.with_suffix(path.suffix+'.partial')
            with urlopen(Request(url,headers={'User-Agent':'WirelessDataScience/1.0'}),timeout=180) as s, partial.open('wb') as out:
                meta={k:s.headers.get(k) for k in ['ETag','Last-Modified','Content-Length','x-amz-version-id']}
                for block in iter(lambda:s.read(1024*1024),b''):out.write(block)
            partial.replace(path)
            return meta
        except Exception:
            if attempt==2:raise
            time.sleep(2**attempt)


def main():
    RAW.mkdir(parents=True,exist_ok=True);R.mkdir(exist_ok=True)
    manifest={'retrieved_at_utc':datetime.now(timezone.utc).isoformat(),'files':{},
              'ookla_license':'CC BY-NC-SA 4.0','census_license':'U.S. Government public domain',
              'api_fallback':'Census API returned missing-key redirect; official bulk population estimates used instead of ACS. No API key or private source required.'}
    paths={}
    for key,url in URLS.items():
        suffix='.parquet' if key in ['2025Q4','2026Q1'] else '.zip' if key=='counties' else '.csv' if key=='population' else '.md'
        path=RAW/(key+suffix)
        headers=download(url,path)
        paths[key]=path
        manifest['files'][key]={'url':url,'sha256':digest(path),'bytes':path.stat().st_size,'headers':headers}
        print('Downloaded and hashed',key,path.stat().st_size,flush=True)
    assert 'CC BY-NC-SA 4.0' in paths['ookla_readme'].read_text()
    co=gpd.read_file(paths['counties'])
    co=co[co.STATEFP=='08'].to_crs(4326)[['GEOID','NAME','ALAND','geometry']].copy()
    assert len(co)==64 and co.GEOID.is_unique and co.geometry.is_valid.all()
    pop=pd.read_csv(paths['population'],encoding='latin1',dtype={'STATE':str,'COUNTY':str,'SUMLEV':str})
    pop=pop[(pop.STATE=='08')&(pop.SUMLEV=='050')].copy()
    pop['GEOID']=pop.STATE+pop.COUNTY
    co=co.merge(pop[['GEOID','POPESTIMATE2024']],on='GEOID',validate='one_to_one')
    assert len(co)==64 and co.POPESTIMATE2024.gt(0).all()
    co['population_density_km2']=co.POPESTIMATE2024/(co.ALAND/1e6)
    co.to_file(R/'county_boundaries.geojson',driver='GeoJSON')
    co.drop(columns='geometry').to_csv(R/'county_context.csv',index=False)
    bounds=co.total_bounds
    audits={}
    for key in ['2025Q4','2026Q1']:
        cols=['quadkey','tile_x','tile_y','avg_d_kbps','avg_u_kbps','avg_lat_ms','tests','devices']
        f=pq.read_table(paths[key],columns=cols,filters=[('tile_x','>=',bounds[0]),('tile_x','<=',bounds[2]),('tile_y','>=',bounds[1]),('tile_y','<=',bounds[3])]).to_pandas()
        n_bbox=len(f)
        assert f.quadkey.is_unique
        valid=f[cols[1:]].notna().all(axis=1)&f.tests.gt(0)&f.devices.gt(0)&f.avg_d_kbps.ge(0)&f.avg_u_kbps.ge(0)&f.avg_lat_ms.gt(0)
        dropped=int((~valid).sum());f=f[valid].copy()
        points=gpd.GeoDataFrame(f,geometry=gpd.points_from_xy(f.tile_x,f.tile_y),crs=4326)
        joined=gpd.sjoin(points,co[['GEOID','geometry']],predicate='within',how='inner').drop(columns=['geometry','index_right'])
        assert joined.quadkey.is_unique
        joined['quarter']=key
        joined=joined.sort_values(['GEOID','quadkey']).reset_index(drop=True)
        joined.to_csv(R/f'tiles_{key}.csv.gz',index=False,compression={'method':'gzip','mtime':0})
        audits[key]={'bbox_tiles':n_bbox,'invalid_metric_tiles':dropped,'assigned_colorado_tiles':len(joined),
                     'unassigned_after_validation':int(valid.sum()-len(joined)),'tests':int(joined.tests.sum()),
                     'sum_tile_device_counts_not_unique_people':int(joined.devices.sum())}
        print(key,audits[key],flush=True)
    inputs=['county_boundaries.geojson','county_context.csv','tiles_2025Q4.csv.gz','tiles_2026Q1.csv.gz']
    manifest['snapshot_hashes']={name:digest(R/name) for name in inputs}
    (R/'source_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (R/'data_audit.json').write_text(json.dumps(audits,indent=2)+'\n')


if __name__=='__main__':main()
