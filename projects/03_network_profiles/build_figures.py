"""Scientific figures with exact source tables and attribution."""
from pathlib import Path
import json
import hashlib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import numpy as np
import pandas as pd
import geopandas as gpd

ROOT=Path(__file__).resolve().parent
R=ROOT/'results';F=ROOT/'figures'
INK='#143044';TEAL='#007d83';CORAL='#d86944'
SOURCE='Ookla mobile tiles: 2025 Q4 / 2026 Q1 | Census 2024 | Observed tests, not population coverage'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False,
    'text.color':INK,'axes.labelcolor':INK,'figure.facecolor':'white','axes.titleweight':'bold'})


def save(fig,name,table):
    fig.text(.5,.015,SOURCE,ha='center',fontsize=8,color='#596c77')
    fig.tight_layout(rect=(0,.05,1,1))
    fig.savefig(F/f'{name}.png',dpi=170,bbox_inches='tight')
    table.to_csv(F/f'{name}.csv',index=False);plt.close(fig)


def main():
    F.mkdir(exist_ok=True)
    p=pd.read_csv(R/'county_profiles.csv',dtype={'GEOID':str})
    co=gpd.read_file(R/'county_boundaries.geojson').merge(p[['GEOID','profile','bootstrap_membership_frequency']],on='GEOID',how='left',validate='one_to_one')
    fig,ax=plt.subplots(figsize=(9,6.3))
    co.plot(column='profile',cmap=ListedColormap([CORAL,TEAL]),edgecolor='white',linewidth=.5,
            missing_kwds={'color':'#d8e0e4','label':'Below support threshold'},ax=ax)
    ax.set_title('2025 Q4: Colorado profiles, with unsupported counties unassigned')
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color=CORAL,label='Profile 0 (14 counties)'),Patch(color=TEAL,label='Profile 1 (37 counties)'),
                       Patch(color='#d8e0e4',label='Below support threshold (13)')],loc='lower left',fontsize=9)
    ax.set_axis_off();save(fig,'01_profile_map',co.drop(columns='geometry'))

    fig,axs=plt.subplots(1,3,figsize=(10.5,4.5))
    for ax,col,label in zip(axs,['download_mbps','upload_mbps','latency_ms'],['Download (Mbps)','Upload (Mbps)','Latency (ms)']):
        values=[p.loc[p.profile==j,col] for j in [0,1]]
        ax.boxplot(values,tick_labels=['Profile 0','Profile 1'],patch_artist=True,
                   boxprops={'facecolor':'#d5e9e9'},medianprops={'color':TEAL,'linewidth':2})
        ax.set_ylabel(label);ax.grid(axis='y',alpha=.15)
    fig.suptitle('2025 Q4 profiles: county summaries of sampled tests',fontweight='bold')
    save(fig,'02_network_profiles',p[['GEOID','NAME','profile','download_mbps','upload_mbps','latency_ms']])

    ranked=p.sort_values('bootstrap_membership_frequency')
    fig,ax=plt.subplots(figsize=(10,6))
    shown=ranked.head(18)
    ax.barh(shown.NAME,shown.bootstrap_membership_frequency*100,color=[CORAL if x<.8 else TEAL for x in shown.bootstrap_membership_frequency])
    ax.invert_yaxis();ax.axvline(80,color=INK,ls='--');ax.set_xlim(0,103)
    ax.set(xlabel='Aligned membership frequency across 200 tile resamples (%)',title='2025 Q4: 12/51 counties below 80% membership stability')
    ax.grid(axis='x',alpha=.15);save(fig,'03_membership_stability',ranked[['GEOID','NAME','profile','tiles','tests','bootstrap_membership_frequency']])

    t=pd.read_csv(R/'temporal_assignments.csv')
    table=pd.crosstab(t.profile,t.next_profile).reindex(index=[0,1],columns=[0,1],fill_value=0)
    fig,ax=plt.subplots(figsize=(7,5.4));ax.imshow(table.values,cmap='Blues',vmin=0,vmax=31)
    for i in [0,1]:
        for j in [0,1]:ax.text(j,i,str(table.iloc[i,j]),ha='center',va='center',fontsize=29,color='white' if table.iloc[i,j]>15 else INK,fontweight='bold')
    ax.set(xticks=[0,1],yticks=[0,1],xticklabels=['Profile 0','Profile 1'],yticklabels=['Profile 0','Profile 1'],
        xlabel='2026 Q1: frozen-model assignment',ylabel='2025 Q4 assignment',title='36/43 stayed - but only 6/12 in the smaller profile')
    save(fig,'04_quarter_transfer',t[['GEOID','NAME','profile','next_profile','same_profile']])

    s=pd.read_csv(R/'aggregation_sensitivity.csv')
    rows=pd.DataFrame({'check':['Equal-tile weighting','Tiles with 5+ tests','Next quarter, all tiles','Next quarter, matched tiles'],
                       'same_fraction':[s.iloc[0].same_profile_fraction,s.iloc[1].same_profile_fraction,t.same_profile.mean(),
                           json.loads((R/'metrics.json').read_text())['matched_tile_same_profile_fraction']],
                       'counties':[51,23,43,31]})
    fig,ax=plt.subplots(figsize=(10,4.7));ax.barh(rows.check,rows.same_fraction*100,color=TEAL)
    for i,row in rows.iterrows():ax.text(row.same_fraction*100+1,i,f'{row.same_fraction*100:.1f}% | n={row.counties}',va='center')
    ax.invert_yaxis();ax.set(xlim=(0,120),xlabel='Same-profile fraction (%)',title='Robustness comparisons have different eligible county sets')
    save(fig,'05_sensitivity',rows)

    fig,ax=plt.subplots(figsize=(9,5.3))
    for j,color in [(0,CORAL),(1,TEAL)]:
        g=p[p.profile==j]
        ax.scatter(g.population_density_km2,g.download_mbps,s=40,c=color,label=f'Profile {j}',alpha=.85)
    ax.set_xscale('log');ax.set(xlabel='2024 estimated population / land km² (log axis)',ylabel='County test-weighted download (Mbps)',
        title='Census density is context, not a clustering input')
    ax.legend();ax.grid(alpha=.15);save(fig,'06_population_context',p[['GEOID','NAME','profile','population_density_km2','download_mbps']])
    prov={'source':'Speedtest by Ookla Global Fixed and Mobile Network Performance Maps; CC BY-NC-SA 4.0. Census public-domain 2024 context.',
          'accessed':'2026-11-09','periods':['2025Q4','2026Q1'],'geography':'Colorado counties; tile centroid assignment',
          'uncertainty':'Conditional within-county tile bootstrap; not population confidence or unique-subscriber sampling',
          'csv_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in F.glob('*.csv')}}
    (F/'provenance.json').write_text(json.dumps(prov,indent=2)+'\n')


if __name__=='__main__':main()
