"""County segmentation, conditional stability, and frozen-quarter transfer."""
import os
os.environ.setdefault('OMP_NUM_THREADS','1')
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import platform
import time
import numpy as np
import pandas as pd
import sklearn
from scipy.optimize import linear_sum_assignment
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans, AgglomerativeClustering
from sklearn.metrics import silhouette_score, adjusted_rand_score

ROOT=Path(__file__).resolve().parent
R=ROOT/'results'
PLAN=json.loads((ROOT/'experiment_plan.json').read_text())
FEATURES=PLAN['features']


def write(name,value):
    (R/name).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')


def load_snapshot():
    manifest=json.loads((R/'source_manifest.json').read_text())
    for name,h in manifest['snapshot_hashes'].items():
        assert hashlib.sha256((R/name).read_bytes()).hexdigest()==h
    tiles={q:pd.read_csv(R/f'tiles_{q}.csv.gz',dtype={'GEOID':str,'quadkey':str}) for q in ['2025Q4','2026Q1']}
    context=pd.read_csv(R/'county_context.csv',dtype={'GEOID':str})
    for q,f in tiles.items():
        assert f.quadkey.is_unique and f.GEOID.isin(context.GEOID).all()
        assert (f.quarter==q).all()
    return tiles,context


def aggregate(tiles,equal_tiles=False,min_tile_tests=1):
    rows=[]
    for geoid,g in tiles[tiles.tests>=min_tile_tests].groupby('GEOID'):
        w=np.ones(len(g)) if equal_tiles else g.tests.to_numpy(float)
        rows.append({'GEOID':geoid,'tiles':len(g),'tests':int(g.tests.sum()),
                     'device_tile_sum':int(g.devices.sum()),
                     'download_mbps':float(np.average(g.avg_d_kbps,weights=w)/1000),
                     'upload_mbps':float(np.average(g.avg_u_kbps,weights=w)/1000),
                     'latency_ms':float(np.average(g.avg_lat_ms,weights=w))})
    out=pd.DataFrame(rows).set_index('GEOID').sort_index()
    out['eligible']=(out.tiles>=PLAN['minimum_tiles'])&(out.tests>=PLAN['minimum_tests'])
    return out


def matrix(counties):return np.log1p(counties[FEATURES].to_numpy(float))


def fit(counties,k,seed):
    scaler=StandardScaler().fit(matrix(counties))
    x=scaler.transform(matrix(counties))
    model=KMeans(n_clusters=k,n_init=PLAN['initializations'],random_state=seed).fit(x)
    return scaler,model,x


def align(reference,new,k):
    table=np.zeros((k,k),dtype=int)
    np.add.at(table,(reference,new),1)
    a,b=linear_sum_assignment(-table)
    mapping=dict(zip(b,a))
    return np.array([mapping[n] for n in new])


def main():
    started=time.monotonic()
    tiles,context=load_snapshot()
    summaries={q:aggregate(f) for q,f in tiles.items()}
    for q,s in summaries.items():s.to_csv(R/f'county_metrics_{q}.csv')
    dev=summaries['2025Q4'].query('eligible').copy()
    assert len(dev)>=25
    choices=[]
    for k in PLAN['candidates']:
        sc,km,x=fit(dev,k,PLAN['seed'])
        sizes=np.bincount(km.labels_,minlength=k)
        choices.append({'k':k,'silhouette':float(silhouette_score(x,km.labels_)),
                        'min_cluster_counties':int(sizes.min()),'inertia':float(km.inertia_),
                        'allowed':bool(sizes.min()>=5)})
    selection=pd.DataFrame(choices)
    selection.to_csv(R/'k_selection.csv',index=False)
    allowed=selection[selection.allowed].sort_values(['silhouette','k'],ascending=[False,True])
    if allowed.empty:raise ValueError('No candidate satisfies cluster support gate')
    k=int(allowed.iloc[0].k)
    scaler,model,x=fit(dev,k,PLAN['seed'])
    # Fix readable labels using increasing original-unit download centroid.
    original=np.expm1(scaler.inverse_transform(model.cluster_centers_))
    order=np.argsort(original[:,0]);remap={int(old):int(new) for new,old in enumerate(order)}
    ref=np.array([remap[int(z)] for z in model.labels_])
    def predict(frame):return np.array([remap[int(z)] for z in model.predict(scaler.transform(matrix(frame)))])
    selection_record={'selected_k':k,'counties':len(dev),
        'criterion':PLAN['selection'],'selected_silhouette':float(allowed.iloc[0].silhouette),
        'segmentation_gate_passed':bool(allowed.iloc[0].silhouette>=.25),
        'fitted_quarter':'2025Q4','replication_used_for_selection':False,
        'feature_order':FEATURES,'scaler_mean':scaler.mean_.tolist(),'scaler_scale':scaler.scale_.tolist(),
        'centroids_original_units':original[order].tolist(),
        'centroids_standardized':model.cluster_centers_[order].tolist(),
        'protocol_sha256':hashlib.sha256((ROOT/'experiment_plan.json').read_bytes()).hexdigest()}
    write('selection_locked_before_replication.json',selection_record)
    dev['profile']=ref
    assignments=dev.join(context.set_index('GEOID')[['NAME','POPESTIMATE2024','population_density_km2']])
    baseline={'statewide_county_median':dev[FEATURES].median().to_dict(),
              'single_profile_standardized_sse':float(np.sum((x-x.mean(axis=0))**2)),
              'selected_inertia':float(model.inertia_),
              'warning':'In-sample reconstruction falls mechanically with K; not an out-of-sample prediction gain. K=1 silhouette is undefined.'}
    write('single_profile_baseline.json',baseline)
    rng=np.random.default_rng(PLAN['seed'])
    groups={g:f for g,f in tiles['2025Q4'].groupby('GEOID') if g in dev.index}
    boot_records=[];membership=np.zeros((len(dev),k),dtype=int)
    for b in range(PLAN['bootstrap_replicates']):
        sampled=pd.concat([f.iloc[rng.integers(0,len(f),len(f))] for g,f in sorted(groups.items())],ignore_index=True)
        means=aggregate(sampled).loc[dev.index]
        _,bm,_=fit(means,k,PLAN['seed']+b+1)
        labels=align(ref,bm.labels_,k)
        membership[np.arange(len(dev)),labels]+=1
        boot_records.append({'replicate':b,'ari':float(adjusted_rand_score(ref,labels)),
                             'aligned_agreement':float(np.mean(ref==labels))})
    boot=pd.DataFrame(boot_records);boot.to_csv(R/'bootstrap_stability.csv',index=False)
    assignments['bootstrap_membership_frequency']=membership[np.arange(len(dev)),ref]/len(boot)
    for j in range(k):assignments[f'bootstrap_profile_{j}_frequency']=membership[:,j]/len(boot)
    ward=AgglomerativeClustering(n_clusters=k,linkage='ward').fit_predict(x)
    sensitivity=[]
    for name,kwargs in [('equal_tile',{'equal_tiles':True}),('minimum_5_tests_per_tile',{'min_tile_tests':5})]:
        s=aggregate(tiles['2025Q4'],**kwargs)
        common=dev.index.intersection(s[s.eligible].index)
        labels=predict(s.loc[common])
        comparison=assignments.loc[common,'profile'].to_numpy()
        sensitivity.append({'variant':name,'counties':len(common),'same_profile_fraction':float(np.mean(labels==comparison)),
                            'ari':float(adjusted_rand_score(comparison,labels)),
                            'method':'Frozen primary scaler and centroids; changing aggregation, not reselecting K'})
        pd.DataFrame({'GEOID':common,'primary_profile':comparison,'variant_profile':labels}).to_csv(R/f'assignments_{name}.csv',index=False)
    pd.DataFrame(sensitivity).to_csv(R/'aggregation_sensitivity.csv',index=False)
    later=summaries['2026Q1'].query('eligible')
    common=dev.index.intersection(later.index)
    transfer=assignments.loc[common].copy()
    transfer['next_profile']=predict(later.loc[common]);transfer['same_profile']=transfer.profile==transfer.next_profile
    for f in FEATURES:transfer[f'next_{f}']=later.loc[common,f]
    transfer.to_csv(R/'temporal_assignments.csv')
    # Match observed tile identities before aggregating each quarter: isolates sample turnover partially.
    left,right=tiles['2025Q4'],tiles['2026Q1']
    match=left[['GEOID','quadkey']].merge(right[['GEOID','quadkey']],on=['GEOID','quadkey'],validate='one_to_one')
    matched={q:aggregate(f.merge(match,on=['GEOID','quadkey'],validate='one_to_one')) for q,f in tiles.items()}
    matched_ids=dev.index.intersection(matched['2025Q4'].query('eligible').index).intersection(matched['2026Q1'].query('eligible').index)
    matched_labels={q:predict(s.loc[matched_ids]) for q,s in matched.items()}
    pd.DataFrame({'GEOID':matched_ids,'matched_dev_profile':matched_labels['2025Q4'],
                  'matched_next_profile':matched_labels['2026Q1']}).to_csv(R/'matched_tile_assignments.csv',index=False)
    assignments.to_csv(R/'county_profiles.csv')
    profiles=assignments.groupby('profile').agg(counties=('tiles','size'),tiles=('tiles','sum'),tests=('tests','sum'),
        median_download_mbps=('download_mbps','median'),median_upload_mbps=('upload_mbps','median'),
        median_latency_ms=('latency_ms','median'),median_population_density_km2=('population_density_km2','median'),
        median_membership_frequency=('bootstrap_membership_frequency','median'))
    profiles.to_csv(R/'profile_summary.csv')
    metrics={'development_counties':len(dev),'later_eligible_counties':len(later),'selected_k':k,
        'silhouette':float(allowed.iloc[0].silhouette),'bootstrap_ari_median':float(boot.ari.median()),
        'bootstrap_ari_conditional_95pct_range':np.quantile(boot.ari,[.025,.975]).tolist(),
        'counties_membership_frequency_ge_0_8':int((assignments.bootstrap_membership_frequency>=.8).sum()),
        'ward_vs_kmeans_ari':float(adjusted_rand_score(ref,ward)),
        'replication_common_counties':len(common),'replication_same_profile_count':int(transfer.same_profile.sum()),
        'replication_same_profile_fraction':float(transfer.same_profile.mean()),
        'replication_ari':float(adjusted_rand_score(transfer.profile,transfer.next_profile)),
        'matched_tiles':len(match),'matched_tile_counties':len(matched_ids),
        'matched_tile_same_profile_fraction':float(np.mean(matched_labels['2025Q4']==matched_labels['2026Q1'])),
        'matched_tile_ari':float(adjusted_rand_score(matched_labels['2025Q4'],matched_labels['2026Q1'])),
        'bootstrap_scope':'Conditional tile-resampling distribution, not a population confidence interval; spatial dependence and within-tile test variability omitted'}
    write('metrics.json',metrics)
    write('execution.json',{'analysis_date':'2026-11-09','python':platform.python_version(),'platform':platform.platform(),
        'sklearn':sklearn.__version__,'numpy':np.__version__,'pandas':pd.__version__,
        'seed':PLAN['seed'],'elapsed_seconds':round(time.monotonic()-started,2),
        'full_model_execution_os':'Linux','macos_full_execution':False})
    print(json.dumps(metrics,indent=2),flush=True);print(profiles.to_string(),flush=True)


if __name__=='__main__':main()
