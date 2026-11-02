"""Scientific figures and their source tables; no publication administration."""
import hashlib
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
R = ROOT / 'results'
F = ROOT / 'figures'
LABEL = {'recent_mean_4':'Recent 4-week mean','seasonal_naive_52':'Same week last year',
         'ridge_log':'Ridge on log counts','boost_poisson_small':'Poisson boosting (7 leaves)',
         'boost_poisson_deep':'Poisson boosting (15 leaves)'}
INK, TEAL, ORANGE = '#112d40', '#007e87', '#df6c3c'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,
                     'axes.spines.right':False,'axes.labelcolor':INK,'text.color':INK,
                     'axes.titleweight':'bold','figure.facecolor':'white','axes.facecolor':'white'})


def save(fig, name, table):
    fig.savefig(F/f'{name}.png', dpi=180, bbox_inches='tight', facecolor='white')
    table.to_csv(F/f'{name}.csv', index=False)
    plt.close(fig)


def main():
    F.mkdir(exist_ok=True)
    weekly = pd.read_csv(R/'weekly_counts.csv',parse_dates=['week_start'])
    metrics = pd.read_csv(R/'test_metrics.csv')
    pred = pd.read_csv(R/'backtest_predictions.csv',parse_dates=['origin','target_week'])
    selection = json.loads((R/'selection_locked_before_test.json').read_text())
    winner, baseline = selection['selected_ml_candidate'], selection['selected_baseline']
    fig,ax=plt.subplots(figsize=(10,4.7))
    ax.plot(weekly.week_start, weekly.all_wireless,color=TEAL,lw=1.2,label='All wireless phone complaints')
    ax.plot(weekly.week_start, weekly.excluding_unwanted_calls,color=ORANGE,lw=1,alpha=.85,label='Excluding Unwanted Calls')
    ax.axvspan(pd.Timestamp('2025-10-27'),weekly.week_start.max(),color=INK,alpha=.07,label='Final 52-week evaluation')
    ax.set(title='A changing reporting process, not a subscriber rate',ylabel='Submitted complaints per week',xlabel='Week starting Monday')
    ax.legend(fontsize=9,loc='upper left'); ax.grid(axis='y',alpha=.15)
    fig.tight_layout(); save(fig,'01_history',weekly)

    m=metrics.sort_values('mae',ascending=False)
    fig,ax=plt.subplots(figsize=(10,4.5))
    colors=[TEAL if x==winner else '#9aadb9' for x in m.model]
    ax.barh([LABEL[x] for x in m.model],m.mae,color=colors)
    for i,v in enumerate(m.mae): ax.text(v+12,i,f'{v:,.0f}',va='center')
    ax.set(xlabel='Mean absolute error (complaints per week; lower is better)',
           title='Does ML improve on a practical baseline?')
    ax.set_xlim(0,m.mae.max()*1.16); ax.grid(axis='x',alpha=.15)
    fig.text(.99,.015,'52 test weeks | 13 origins | 4 horizons per origin | selection uses earlier data',ha='right',fontsize=9)
    fig.tight_layout(rect=(0,.04,1,1)); save(fig,'02_model_comparison',m)

    chosen=pred[(pred.split=='test') & (pred.model==winner)].sort_values('target_week')
    base=pred[(pred.split=='test') & (pred.model==baseline)].sort_values('target_week')
    fig,ax=plt.subplots(figsize=(10,4.8))
    ax.fill_between(chosen.target_week,chosen.lower80,chosen.upper80,color=TEAL,alpha=.16,label='Nominal 80% residual interval')
    ax.plot(chosen.target_week,chosen.actual,color=INK,lw=1.8,label='Observed count')
    ax.plot(chosen.target_week,chosen.prediction,color=TEAL,lw=1.4,label=LABEL[winner])
    if baseline!=winner: ax.plot(base.target_week,base.prediction,color=ORANGE,lw=1.1,ls='--',label=LABEL[baseline])
    ax.set(title='Forecasts made before each four-week batch',ylabel='Complaints per week',xlabel='Target week starting Monday')
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y')); ax.legend(fontsize=8.5,ncol=2)
    ax.grid(axis='y',alpha=.15); fig.tight_layout();save(fig,'03_test_forecasts',chosen)

    h=pd.read_csv(R/'metrics_by_horizon.csv')
    fig,axs=plt.subplots(1,2,figsize=(10,4.3))
    for name,c in [(winner,TEAL),(baseline,ORANGE)]:
        if name==baseline and name==winner: continue
        g=h[h.model==name]
        axs[0].plot(g.horizon,g.mae,marker='o',color=c,label=LABEL[name])
        axs[1].plot(g.horizon,g.coverage80*100,marker='o',color=c,label=LABEL[name])
    axs[0].set(ylabel='MAE (complaints/week)',title='Error by forecast horizon')
    axs[1].axhline(80,color=INK,ls='--',lw=1,label='Nominal 80%')
    axs[1].set(ylabel='Empirical interval coverage (%)',ylim=(0,103),title='Intervals need their own test')
    for ax in axs: ax.set(xlabel='Weeks ahead',xticks=[1,2,3,4]);ax.grid(axis='y',alpha=.15);ax.legend(fontsize=8)
    fig.text(.99,.015,'13 test predictions per horizon: coverage estimates are coarse',ha='right',fontsize=9)
    fig.tight_layout(rect=(0,.04,1,1));save(fig,'04_horizon_diagnostics',h)

    q=pd.read_csv(R/'metrics_by_quarter.csv')
    q=q[q.model.isin([winner,baseline])]
    fig,ax=plt.subplots(figsize=(10,4.2))
    for name,c in [(winner,TEAL),(baseline,ORANGE)]:
        if name==baseline and name==winner: continue
        g=q[q.model==name]
        ax.plot(g.quarter,g.mae,marker='o',color=c,label=LABEL[name])
    ax.set(title='One aggregate score can hide changing errors',ylabel='MAE (complaints/week)',xlabel='Calendar quarter (partial quarters included)')
    ax.legend(fontsize=9);ax.grid(axis='y',alpha=.15);fig.tight_layout();save(fig,'05_period_errors',q)
    provenance={'source_manifest_sha256':hashlib.sha256((R/'source_manifest.json').read_bytes()).hexdigest(),
                'source':'FCC CGB 3xyp-aqkj; Public Domain U.S. Government',
                'scope':'Submitted wireless phone complaints, UTC ticket_created submission day',
                'test_period':'2025-10-27 through 2026-10-25',
                'figures':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(F.glob('*.csv'))},
                'uncertainty':'Empirical signed residual quantiles from preceding origins; no coverage guarantee'}
    (F/'provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')


if __name__=='__main__': main()
