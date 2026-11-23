"""Additional selected-pair refit and frozen DR comparison, without changing selection."""
import json
import numpy as np
import pandas as pd
import run
from source import load,ROOT

def main():
    r=ROOT/'results';d=load();tr=d[d.split=='train'];test=d[d.split=='test']
    saved=pd.read_csv(r/'predictions.csv.gz');pred=[]
    for arm in [0,1]:
        g=tr[tr.treatment==arm]
        m=run.classifier('boosted',7).fit(g[run.FEATURES],g.visit)
        pred.append(m.predict_proba(test[run.FEATURES])[:,1])
    err=float(np.max(np.abs(pred[1]-pred[0]-saved.boosted_7_uplift)));assert err<1e-9
    p=json.loads((r/'experiment.json').read_text())['train_assignment_share']
    score=run.dr(saved.visit.to_numpy(),saved.treatment.to_numpy(),p,saved.m0.to_numpy(),saved.m1.to_numpy())
    rows=[]
    for name,a in [('random_20',.2),('response_20',saved.policy_response_20.to_numpy())]:
        v=(saved.policy_uplift_20.to_numpy()-a)*score*1000
        lo,hi=run.interval(v,saved.profile.to_numpy())[:,0]
        rows.append(dict(comparator=name,difference_per_1000=float(v.mean()),low=float(lo),high=float(hi)))
    pd.DataFrame(rows).to_csv(r/'dr_comparisons.csv',index=False)
    dup=int(d.duplicated(run.FEATURES+['treatment','conversion','visit','exposure'],keep=False).sum())
    (r/'replication.json').write_text(json.dumps(dict(selected_pair_refitted=True,additional_fits=2,
        max_absolute_prediction_error=err,tolerance=1e-9,full_record_duplicate_member_rows=dup,
        distinct_profiles=int(d.profile.nunique()),python_execution='Linux only'),indent=2)+'\n')
    print('Selected refit matched; maximum absolute difference:',err)

if __name__=='__main__':main()
