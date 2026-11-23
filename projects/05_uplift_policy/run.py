"""Execute the locked, source-domain uplift study. No employer data or simulation."""
import os
for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']: os.environ[key]='1'
from pathlib import Path
import hashlib
import json
import platform
import sys
import time
import textwrap
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score
from source import ROOT, FEATURES, load, sha

R = ROOT/'results'; F=R/'figures'
SEED=20261123

def top(score, capacity):
    """Outcome-blind batch allocation; deterministic row-order tie break."""
    result=np.zeros(len(score)); n=int(np.ceil(capacity*len(score)))
    result[np.argsort(-np.asarray(score),kind='stable')[:n]]=1
    return result

def ipw(y,t,p): return t*y/p-(1-t)*y/(1-p)

def dr(y,t,p,m0,m1): return m1-m0+t*(y-m1)/p-(1-t)*(y-m0)/(1-p)

def interval(values, groups, seed=SEED, reps=500):
    """Poisson cluster bootstrap; frozen fitted models, policy and propensity."""
    values=np.asarray(values)
    if values.ndim==1: values=values[:,None]
    _,g=np.unique(groups,return_inverse=True)
    counts=np.bincount(g); total=np.zeros((len(counts),values.shape[1]))
    for j in range(values.shape[1]): total[:,j]=np.bincount(g,weights=values[:,j])
    rng=np.random.default_rng(seed); boot=[]
    while len(boot)<reps:
        weights=rng.poisson(1,len(counts))
        if weights@counts==0: continue
        boot.append(weights@total/(weights@counts))
    return np.quantile(boot,[.025,.975],axis=0)

def classifier(kind,param):
    if kind=='logistic': return make_pipeline(StandardScaler(),LogisticRegression(C=param,max_iter=600,random_state=SEED))
    return HistGradientBoostingClassifier(max_leaf_nodes=param,max_iter=100,min_samples_leaf=100,
        l2_regularization=10,early_stopping=False,random_state=SEED)

def csv(frame,name): frame.to_csv(R/name,index=False,float_format='%.10g')

def main():
    started=time.time(); R.mkdir(exist_ok=True);F.mkdir(exist_ok=True)
    d=load(); train=d[d.split=='train']; val=d[d.split=='validation']; test=d[d.split=='test']
    assert not set(train.profile)&set(val.profile) and not set(train.profile)&set(test.profile) and not set(val.profile)&set(test.profile)
    audit=[]
    for (s,t),g in d.groupby(['split','treatment']):
        audit.append(dict(split=s,treatment=int(t),n=len(g),visits=int(g.visit.sum()),rate=g.visit.mean(),profiles=g.profile.nunique()))
    csv(pd.DataFrame(audit),'audit.csv')
    csv(d[['row_id','profile','split']],'splits.csv.gz')
    p=train.treatment.mean()
    X=train[FEATURES]; t=train.treatment.to_numpy(); y=train.visit.to_numpy()
    vt=val.treatment.to_numpy(); vy=val.visit.to_numpy(); tt=test.treatment.to_numpy(); ty=test.visit.to_numpy()
    assignments=classifier('logistic',1).fit(X,t)
    e=np.clip(assignments.predict_proba(test[FEATURES])[:,1],.05,.95)
    balance=[]
    for col in FEATURES:
        a=train.loc[train.treatment==1,col]; b=train.loc[train.treatment==0,col]
        balance.append(dict(feature=col,smd=(a.mean()-b.mean())/np.sqrt((a.var()+b.var())/2)))
    csv(pd.DataFrame(balance),'balance.csv')
    fits={}; search=[]
    # All preprocessing and both potential-outcome learners fit ONLY on train.
    for kind,params in [('logistic',[.1,1.]),('boosted',[7,15])]:
        for param in params:
            name=f'{kind}_{param}'; models=[]
            for arm in [0,1]: models.append(classifier(kind,param).fit(X[t==arm],y[t==arm]))
            v=[m.predict_proba(val[FEATURES])[:,1] for m in models]
            score=v[1]-v[0]; allocation=top(score,.2)
            objective=np.mean(allocation*ipw(vy,vt,p))*1000
            search.append(dict(model=name,validation_ipw_per_1000=objective,fit_rows=len(train),validation_rows=len(val)))
            fits[name]=models
    search=pd.DataFrame(search); csv(search,'selection.csv')
    selected=str(search.sort_values('validation_ipw_per_1000',ascending=False,kind='stable').iloc[0].model)
    print('Validation locked selected model:',selected,flush=True)
    # No refit after selection: the test outcomes have never entered a fit/choice.
    predictions={name:[m.predict_proba(test[FEATURES])[:,1] for m in models] for name,models in fits.items()}
    selected_score=predictions[selected][1]-predictions[selected][0]
    response_score=predictions['logistic_1.0'][1]
    selected_policy=top(selected_score,.2);response_policy=top(response_score,.2)
    nuisance=predictions['boosted_7']
    scores={'IPW':ipw(ty,tt,p),'DR':dr(ty,tt,p,*nuisance),
        'IPW_p085':ipw(ty,tt,.85),'IPW_covariate':ipw(ty,tt,e)}
    w=scores['IPW']; groups=test.profile.to_numpy()
    policies={'treat_none':np.zeros(len(test)),'random_20':np.full(len(test),.2),
        'response_20':response_policy,'uplift_20':selected_policy,'treat_all':np.ones(len(test))}
    values=np.column_stack([a*w for a in policies.values()])*1000
    ci=interval(values,groups); policies_table=[]
    for j,(name,a) in enumerate(policies.items()):
        mask=a==1
        policies_table.append(dict(policy=name,allocated_fraction=a.mean(),incremental_per_1000=values[:,j].mean(),
            low=ci[0,j],high=ci[1,j],selected_rows=int(mask.sum()),treated_selected=int(tt[mask].sum()),
            control_selected=int((1-tt[mask]).sum()),treated_visits=int((ty[mask]*tt[mask]).sum()),
            control_visits=int((ty[mask]*(1-tt[mask])).sum())))
    csv(pd.DataFrame(policies_table),'policies.csv')
    comparisons=[]
    for name,a in [('random_20',np.full(len(test),.2)),('response_20',response_policy)]:
        delta=(selected_policy-a)*w*1000; lo,hi=interval(delta,groups)[:,0]
        comparisons.append(dict(comparator=name,difference_per_1000=delta.mean(),low=lo,high=hi))
    csv(pd.DataFrame(comparisons),'paired_comparisons.csv')
    capacity=[]
    for q in [.1,.2,.4,.6,.8,1.]:
        for name,score in [('uplift',selected_score),('response',response_score),('random',None)]:
            a=np.full(len(test),q) if score is None else top(score,q)
            v=a*w*1000; lo,hi=interval(v,groups)[:,0]
            capacity.append(dict(capacity=q,policy=name,value=v.mean(),low=lo,high=hi,n=len(test)))
    csv(pd.DataFrame(capacity),'capacity.csv')
    sens=[]
    for name,w_s in scores.items():
        v=(selected_policy-.2)*w_s*1000;lo,hi=interval(v,groups)[:,0]
        sens.append(dict(estimator=name,advantage_over_random=v.mean(),low=lo,high=hi))
    csv(pd.DataFrame(sens),'sensitivity.csv')
    deciles=[]; order=np.argsort(-selected_score,kind='stable')
    for k,idx in enumerate(np.array_split(order,10)):
        v=w[idx]*1000; lo,hi=interval(v,groups[idx])[:,0]
        deciles.append(dict(decile=k+1,n=len(idx),treated=int(tt[idx].sum()),control=int((1-tt[idx]).sum()),
            mean_predicted_per_1000=selected_score[idx].mean()*1000,observed_ipw_per_1000=v.mean(),low=lo,high=hi))
    csv(pd.DataFrame(deciles),'deciles.csv')
    out=test[['row_id','profile','treatment','visit']].copy()
    for name,(m0,m1) in predictions.items(): out[f'{name}_uplift']=m1-m0
    out['response_score']=response_score;out['m0']=nuisance[0];out['m1']=nuisance[1];out['propensity']=e
    out['ipw']=w;out['policy_uplift_20']=selected_policy;out['policy_response_20']=response_policy
    csv(out,'predictions.csv.gz')
    experiment=dict(seed=SEED,platform=platform.platform(),python=sys.version,selected_model=selected,
        train_assignment_share=p,treatment_auc_test=roc_auc_score(tt,e),max_abs_training_smd=max(abs(b['smd']) for b in balance),
        min_test_propensity=float(e.min()),max_test_propensity=float(e.max()),sample_rows=len(d),test_rows=len(test),
        test_profiles=int(test.profile.nunique()),repeated_profile_rows=int(d.duplicated('profile',keep=False).sum()),
        fits=9,fit_explanation='8 outcome fits + 1 assignment audit fit; no resampled model refitting',
        scope='Released privacy-altered advertising benchmark; no original population ITT or telecom effect',
        bootstrap_reps=500,protocol_sha256=sha(ROOT/'protocol.json'),source_sha256=json.loads((R/'source.json').read_text())['sha256'],
        seconds=round(time.time()-started,2))
    (R/'experiment.json').write_text(json.dumps(experiment,indent=2)+'\n')
    figures()
    print(json.dumps(experiment,indent=2),flush=True)

def figures():
    plt.rcParams.update({'font.size':12,'axes.spines.top':False,'axes.spines.right':False,'figure.dpi':140})
    def finish(name,caption):
        caption='Criteo v2.1 test n=210,123. '+caption
        plt.figtext(.02,.01,textwrap.fill(caption,115),fontsize=8.5);plt.tight_layout(rect=(0,.10,1,1));plt.savefig(F/name);plt.close()
    a=pd.read_csv(R/'audit.csv'); a=a[a.split=='test']
    plt.figure(figsize=(8,5)); plt.bar(['Control','Assigned advertising'],a.rate*100,color=['#d37955','#187c80'])
    plt.ylabel('Observed visits per 100 released users');plt.title('Observed visit rates are not individual treatment effects')
    for i,r in enumerate(a.itertuples()): plt.text(i,r.rate*100+.15,f'n={r.n:,}\nvisits={r.visits:,}',ha='center',fontsize=10)
    plt.ylim(0,a.rate.max()*100+1.7)
    finish('01_arm_rates.png','Criteo v2.1; held-out grouped sample. No event dates; nonuniform publisher subsampling.')
    c=pd.read_csv(R/'capacity.csv');plt.figure(figsize=(8,5))
    for name,g in c.groupby('policy'):
        plt.plot(g.capacity*100,g.value,marker='o',label=name);plt.fill_between(g.capacity*100,g.low,g.high,alpha=.12)
    plt.xlabel('Hypothetical assignment capacity (%)');plt.ylabel('Incremental visit contrast / 1,000 eligible');plt.legend();plt.title('Budget changes the policy comparison')
    finish('02_capacity.png','Criteo v2.1 test; IPW. Shading: pointwise conditional 95% profile multiplier intervals.')
    p=pd.read_csv(R/'policies.csv');p=p[p.policy.isin(['random_20','response_20','uplift_20'])]
    plt.figure(figsize=(8,5));plt.errorbar(p.incremental_per_1000,p.policy,xerr=[p.incremental_per_1000-p.low,p.high-p.incremental_per_1000],fmt='o',capsize=5,color='#187c80')
    plt.xlabel('Incremental visit contrast / 1,000 eligible');plt.title('20% capacity: compare against useful alternatives')
    finish('03_policy.png','Criteo v2.1 test; IPW, conditional 95% profile intervals. Random = expected random policy.')
    d=pd.read_csv(R/'deciles.csv');plt.figure(figsize=(8,5));plt.errorbar(d.decile,d.observed_ipw_per_1000,yerr=[d.observed_ipw_per_1000-d.low,d.high-d.observed_ipw_per_1000],fmt='o',capsize=4,label='Observed IPW contrast')
    plt.plot(d.decile,d.mean_predicted_per_1000,label='Model prediction');plt.axhline(0,c='grey',lw=1);plt.legend();plt.xlabel('Predicted-uplift decile (1 = highest)');plt.ylabel('Contrast / 1,000 in decile');plt.title('Ranking quality does not establish effect calibration')
    finish('04_deciles.png','Exploratory deciles; conditional 95% profile intervals, no multiple-comparison claims.')
    s=pd.read_csv(R/'sensitivity.csv');plt.figure(figsize=(8,5));plt.errorbar(s.advantage_over_random,s.estimator,xerr=[s.advantage_over_random-s.low,s.high-s.advantage_over_random],fmt='o',capsize=5);plt.axvline(0,c='grey');plt.xlabel('Uplift minus random / 1,000 eligible');plt.title('Does the result depend on the evaluation estimator?')
    finish('05_sensitivity.png','Frozen 20% policy. DR = training-only nuisance models; benchmark scale, not original ITT.')

if __name__=='__main__':main()
