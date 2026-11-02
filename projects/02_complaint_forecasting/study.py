"""A dated, auditable direct multi-horizon forecasting experiment."""
import hashlib
import argparse
import json
import os
os.environ.setdefault('OMP_NUM_THREADS', '1')
from pathlib import Path
import platform
import sys
import time

import numpy as np
import pandas as pd
import scipy
import sklearn
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / 'results'
PLAN = json.loads((ROOT / 'experiment_plan.json').read_text())
MODELS = PLAN['models']


def dump(path, obj):
    path.write_text(json.dumps(obj, indent=2, allow_nan=False) + '\n')


def load_data(snapshot=False):
    rawdir = ROOT / 'data/raw'
    if snapshot:
        manifest = json.loads((RESULTS / 'source_manifest.json').read_text())
        snapshot_file = RESULTS / 'source_daily_issue_counts.csv'
        assert hashlib.sha256(snapshot_file.read_bytes()).hexdigest() == manifest['snapshot_aggregate_sha256']
        daily = pd.read_csv(snapshot_file, keep_default_na=False)
        source_audit = json.loads((RESULTS / 'source_audit.json').read_text())
    else:
        manifest = json.loads((rawdir / 'manifest.json').read_text())
        for key, info in manifest['files'].items():
            assert hashlib.sha256((rawdir / f'{key}.json').read_bytes()).hexdigest() == info['sha256']
        daily = pd.read_json(rawdir / 'daily_issues.json')
        source_audit = {key: json.loads((rawdir / f'{key}.json').read_text())[0]
                        for key in ['audit','missing_dates','date_agreement']}
    daily['day'] = pd.to_datetime(daily['day']).dt.normalize()
    for col in ['n', 'unique_ids']:
        daily[col] = daily[col].astype(int)
    audit = source_audit['audit']
    assert len(daily) < 50000
    assert not daily.duplicated(['day', 'issue']).any()
    assert (daily.n == daily.unique_ids).all()
    assert daily.n.sum() == int(audit['n']) == int(audit['unique_ids']) == int(audit['nonnull_ids'])
    dates = pd.date_range(PLAN['start'], pd.Timestamp(PLAN['end_exclusive']) - pd.Timedelta(days=1), freq='D')
    all_daily = daily.groupby('day').n.sum().reindex(dates, fill_value=0)
    service_daily = daily[daily.issue != 'Unwanted Calls'].groupby('day').n.sum().reindex(dates, fill_value=0)
    weekly = pd.DataFrame({'all_wireless': all_daily.resample('W-MON', closed='left', label='left').sum(),
                           'excluding_unwanted_calls': service_daily.resample('W-MON', closed='left', label='left').sum()})
    assert len(dates) % 7 == 0
    assert weekly.index[0].weekday() == 0
    weekly.index.name = 'week_start'
    missing = source_audit['missing_dates']['n']
    mismatch = source_audit['date_agreement']['n']
    quality = {'observed_complaints': int(daily.n.sum()), 'daily_issue_groups': len(daily),
               'weeks': len(weekly), 'first_week': str(weekly.index[0].date()),
               'last_week': str(weekly.index[-1].date()),
               'zero_count_days': int((all_daily == 0).sum()),
               'duplicate_ids_in_scope': int(audit['n']) - int(audit['unique_ids']),
               'missing_submission_date_all_time_scope': int(missing),
               'date_created_vs_ticket_created_day_mismatches': int(mismatch),
               'unwanted_call_share': float(1 - service_daily.sum() / all_daily.sum()),
               'snapshot_not_vintage': True,
               'missing_days_policy': 'Reindex full calendar; absent days are assumed zero, not proven ingestion uptime'}
    return weekly, daily, quality, manifest, source_audit


def features(y, index, horizon):
    """Row t is computed only from observations strictly before t."""
    rows = []
    for t in range(52, len(y)):
        target = index[t] + pd.Timedelta(weeks=horizon - 1)
        phase = 2 * np.pi * target.dayofyear / 365.25
        rows.append([np.log1p(y[t-lag]) for lag in [1, 2, 3, 4, 8, 13, 26, 52]] +
                    [np.log1p(np.mean(y[t-w:t])) for w in [4, 13, 26, 52]] +
                    [np.log1p(np.std(y[t-13:t])), np.sin(phase), np.cos(phase),
                     np.sin(2*phase), np.cos(2*phase)])
    return np.array(rows)


def model_for(name):
    if name == 'ridge_log':
        return make_pipeline(StandardScaler(), Ridge(alpha=10.0))
    return HistGradientBoostingRegressor(loss='poisson', learning_rate=0.05, max_iter=100,
        max_leaf_nodes=7 if name == 'boost_poisson_small' else 15,
        min_samples_leaf=15, l2_regularization=10, random_state=PLAN['seed'], early_stopping=False)


def interval(point, errors):
    if len(errors) < PLAN['minimum_calibration_origins']:
        return None, None
    lo, hi = np.quantile(errors[-PLAN['residual_window_origins']:], PLAN['interval_quantiles'])
    return max(0., point + lo), max(0., point + hi)


def score(frame):
    records = []
    for name, g in frame.groupby('model'):
        e = np.abs(g.actual - g.prediction)
        valid = g.dropna(subset=['lower80', 'upper80'])
        lo, hi, actual = valid.lower80, valid.upper80, valid.actual
        iscore = hi - lo + 10 * (lo - actual).clip(lower=0) + 10 * (actual - hi).clip(lower=0)
        records.append({'model': name, 'n_forecasts': len(g), 'n_origins': g.origin.nunique(),
                        'mae': float(e.mean()), 'wape': float(e.sum()/g.actual.sum()),
                        'bias': float((g.prediction-g.actual).mean()),
                        'rmse': float(np.sqrt(np.mean((g.prediction-g.actual)**2))),
                        'coverage80': float(((actual >= lo) & (actual <= hi)).mean()),
                        'mean_width80': float((hi-lo).mean()), 'interval_score80': float(iscore.mean()),
                        'n_interval_forecasts': len(valid)})
    return pd.DataFrame(records).sort_values('mae')


def run_series(weekly, column, locked=None):
    y = weekly[column].to_numpy(float)
    index = weekly.index
    xs = {h: features(y, index, h) for h in PLAN['horizons']}
    records, trace = [], []
    dev_start, test_start = pd.Timestamp(PLAN['development_start']), pd.Timestamp(PLAN['test_start'])
    origins = list(range(PLAN['first_origin_index'], len(y)-3, 4))
    test_origins = [o for o in origins if index[o] >= test_start]
    selection = locked
    for origin in origins:
        if origin in test_origins and selection is None:
            dev = pd.DataFrame(records)
            dev = dev[(dev.target_week >= str(dev_start.date())) & (dev.target_week < str(test_start.date()))]
            sm = score(dev)
            best = sm.iloc[0].model
            baseline = sm[sm.model.isin(['recent_mean_4', 'seasonal_naive_52'])].iloc[0].model
            best_ml = sm[~sm.model.isin(['recent_mean_4', 'seasonal_naive_52'])].iloc[0].model
            selection = {'selected_model': best, 'selected_baseline': baseline,
                         'selected_ml_candidate': best_ml,
                         'criterion': 'Lowest MAE over development targets, no final test selection',
                         'development_metrics': sm.to_dict('records'),
                         'last_development_target': str(index[origin-1].date()),
                         'first_test_origin': str(index[origin].date()),
                         'protocol_sha256': hashlib.sha256((ROOT / 'experiment_plan.json').read_bytes()).hexdigest()}
            dump(RESULTS / 'selection_locked_before_test.json', selection)
            print('Locked selection before test:', best, flush=True)
        for h in PLAN['horizons']:
            train_t = np.arange(52, origin-h+1)
            label_indices = train_t + h - 1
            assert label_indices.max() < origin
            xtrain = xs[h][train_t-52]
            target = y[label_indices]
            for name in MODELS:
                if name == 'recent_mean_4':
                    point = y[origin-4:origin].mean()
                elif name == 'seasonal_naive_52':
                    point = y[origin+h-1-52]
                else:
                    model = model_for(name)
                    model.fit(xtrain, np.log1p(target) if name == 'ridge_log' else target)
                    point = float(model.predict(xs[h][[origin-52]])[0])
                    if name == 'ridge_log':
                        point = np.expm1(point)
                    trace.append({'scope': column, 'origin': str(index[origin].date()),
                                  'horizon': h, 'model': name, 'n_train': len(train_t),
                                  'latest_training_target': str(index[label_indices.max()].date()),
                                  'latest_feature_observation': str(index[origin-1].date())})
                point = max(0., float(point))
                past = [r for r in records if r['model'] == name and r['horizon'] == h
                        and r['target_index'] < origin]
                errors = [r['actual'] - r['prediction'] for r in past]
                lower, upper = interval(point, errors)
                ti = origin+h-1
                records.append({'scope': column, 'origin': str(index[origin].date()),
                                'target_week': str(index[ti].date()), 'target_index': ti,
                                'horizon': h, 'model': name, 'actual': y[ti], 'prediction': point,
                                'lower80': lower, 'upper80': upper,
                                'calibration_n': min(len(errors), PLAN['residual_window_origins']),
                                'latest_calibration_target': past[-1]['target_week'] if past else None,
                                'split': 'test' if index[ti] >= test_start else ('development' if index[ti] >= dev_start else 'warmup')})
        if origin % 40 == 36:
            print(column, 'completed origin', index[origin].date(), flush=True)
    return pd.DataFrame(records), pd.DataFrame(trace), selection


def paired_bootstrap(test, selected, baseline):
    # Preserve four horizons within each origin; resample 12-week blocks of origins.
    a = test[test.model == selected].sort_values(['origin','horizon'])
    b = test[test.model == baseline].sort_values(['origin','horizon'])
    ae = np.abs(a.actual.to_numpy()-a.prediction.to_numpy()).reshape(-1,4)
    be = np.abs(b.actual.to_numpy()-b.prediction.to_numpy()).reshape(-1,4)
    n = len(ae)
    rng = np.random.default_rng(PLAN['seed'])
    values = []
    for _ in range(2000):
        starts = rng.integers(0,n,size=int(np.ceil(n/3)))
        ix = np.concatenate([(s+np.arange(3))%n for s in starts])[:n]
        values.append(float(np.mean(ae[ix]-be[ix])))
    return {'comparison': f'{selected} minus {baseline}', 'mae_difference': float(np.mean(ae-be)),
            'conditional_95pct_block_bootstrap_ci': np.quantile(values,[.025,.975]).tolist(),
            'origins': n, 'block_origins': 3, 'resamples': 2000,
            'limitations': 'Small number of origins; conditional on this snapshot and fitted forecasts. No model refitting or data-revision uncertainty; not an IID-fold test.'}


def main(snapshot=False):
    started = time.monotonic()
    RESULTS.mkdir(exist_ok=True)
    weekly, daily, quality, manifest, source_audit = load_data(snapshot)
    daily.to_csv(RESULTS / 'source_daily_issue_counts.csv', index=False)
    manifest['snapshot_aggregate_sha256'] = hashlib.sha256((RESULTS / 'source_daily_issue_counts.csv').read_bytes()).hexdigest()
    dump(RESULTS / 'source_audit.json', source_audit)
    weekly.to_csv(RESULTS / 'weekly_counts.csv')
    daily.groupby('issue', dropna=False).n.sum().sort_values(ascending=False).to_csv(RESULTS / 'issue_counts.csv')
    dump(RESULTS/'data_audit.json', quality)
    dump(RESULTS/'source_manifest.json', manifest)
    primary, trace, selection = run_series(weekly, 'all_wireless')
    primary.to_csv(RESULTS/'backtest_predictions.csv', index=False)
    test = primary[primary.split == 'test'].copy()
    summary = score(test)
    summary.to_csv(RESULTS/'test_metrics.csv', index=False)
    pd.concat([score(g).assign(horizon=h) for h,g in test.groupby('horizon')]).to_csv(RESULTS/'metrics_by_horizon.csv',index=False)
    pd.concat([score(g).assign(quarter=q) for q,g in test.groupby(pd.to_datetime(test.target_week).dt.to_period('Q').astype(str))]).to_csv(RESULTS/'metrics_by_quarter.csv',index=False)
    ci = paired_bootstrap(test, selection['selected_ml_candidate'], selection['selected_baseline'])
    dump(RESULTS/'comparison_uncertainty.json', ci)
    # Diagnostic only: thresholds defined on development actuals, not test quantiles.
    dev_actual = primary[(primary.split == 'development') & (primary.model == 'recent_mean_4')].actual
    cutoff = float(dev_actual.quantile(.9))
    slices = []
    for group, g in test.assign(slice=np.where(test.actual>cutoff,'above_dev_p90','at_or_below_dev_p90')).groupby('slice'):
        slices.append(score(g).assign(error_slice=group,development_p90=cutoff))
    pd.concat(slices).to_csv(RESULTS/'error_slices.csv',index=False)
    sensitivity, st, _ = run_series(weekly, 'excluding_unwanted_calls', locked=selection)
    sensitivity.to_csv(RESULTS/'sensitivity_predictions.csv',index=False)
    score(sensitivity[sensitivity.split=='test']).to_csv(RESULTS/'sensitivity_metrics.csv',index=False)
    pd.concat([trace,st]).to_csv(RESULTS/'training_trace.csv',index=False)
    dump(RESULTS/'execution.json', {'analysis_date':'2026-11-02','platform':platform.platform(),
        'python':sys.version,'numpy':np.__version__,'pandas':pd.__version__,
        'scipy':scipy.__version__,'scikit_learn':sklearn.__version__,
        'elapsed_seconds':round(time.monotonic()-started,2), 'seed':PLAN['seed'],
        'protocol_sha256':hashlib.sha256((ROOT/'experiment_plan.json').read_bytes()).hexdigest(),
        'models_executed':MODELS, 'macos_execution':False})
    print(summary.to_string(index=False), flush=True)
    print(json.dumps(ci,indent=2),flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--snapshot', action='store_true', help='Use the committed anonymous source aggregate without network access')
    main(p.parse_args().snapshot)
