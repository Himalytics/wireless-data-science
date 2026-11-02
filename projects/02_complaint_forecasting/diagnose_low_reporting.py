"""Post-evaluation diagnostic; does not alter selection or the primary score."""
from pathlib import Path
import json
import pandas as pd
from study import score

ROOT=Path(__file__).resolve().parent


def main():
    r=ROOT/'results'
    weekly=pd.read_csv(r/'weekly_counts.csv')
    weekly[weekly.all_wireless<100].to_csv(r/'low_reporting_weeks.csv',index=False)
    predictions=pd.read_csv(r/'backtest_predictions.csv')
    subset=predictions[(predictions.split=='test') & (predictions.actual>=100)]
    score(subset).to_csv(r/'low_reporting_score_sensitivity.csv',index=False)
    (r/'low_reporting_diagnostic.json').write_text(json.dumps({
        'type':'Post-hoc source-availability diagnostic, not a prespecified model-selection criterion',
        'threshold':'Observed weekly primary count below 100',
        'interpretation':'Unusually low reporting is not proof of an outage; no causal attribution',
        'primary_test_unchanged':True,'retained_test_weeks':50,
        'limitation':'No retraining or removal of low weeks from training features; only remaining test targets are scored'
    },indent=2)+'\n')


if __name__=='__main__':main()
