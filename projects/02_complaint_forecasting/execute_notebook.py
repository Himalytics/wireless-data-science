"""Create and execute an explanatory companion to the separately executed study."""
from pathlib import Path
import os
import nbformat as nbf
from IPython.core.interactiveshell import InteractiveShell
from IPython.utils.capture import capture_output

ROOT=Path(__file__).resolve().parent


def main():
    cells=[]
    md=lambda s: cells.append(nbf.v4.new_markdown_cell(s))
    code=lambda s: cells.append(nbf.v4.new_code_cell(s))
    md('''# Can ML forecast wireless complaint workloads better than a baseline?

**Himanshu Jadaun | Project 02 | November 2, 2026**

This notebook explains the executed `study.py` experiment. It reads its saved predictions and independently recomputes results; it does not claim to retrain the models inside notebook cells. Run `python run_study.py` for source ingestion and full fitting, or `python study.py --snapshot` for an exact input-snapshot rerun.

**New technique:** direct multi-horizon count forecasting with rolling-origin residual distributions. We forecast four separate weekly targets from the same origin. A separate model for each horizon avoids feeding invented future observations into later predictions.

**Hypothesis:** a nonlinear count model may outperform a recent-average workload forecast. The prespecified development MAE, not final evaluation performance, decides which candidate is selected.''')
    code('''import json
from pathlib import Path
import numpy as np
import pandas as pd
from IPython.display import display, Image
from study import load_data, score, features
R=Path('results')
weekly,daily,audit,manifest,_=load_data(snapshot=True)
pred=pd.read_csv(R/'backtest_predictions.csv')
selection=json.loads((R/'selection_locked_before_test.json').read_text())
audit''')
    md('''## 1. Audit the unit of analysis before creating features

The observed unit is an FCC complaint ticket, filtered to phone service with a wireless method. The modelling target is a weekly total, not a subscriber rate. Source reports are self-selected and unverified. More complaints can reflect reporting behavior, spam, media attention, service changes, or data processing; the counts do not identify a cause.

`ticket_created` is explicitly documented as the submission timestamp. `date_created` is an undescribed calendar field, and its day can differ from the UTC submission day. The audit amendment records why the study uses UTC submission dates. We never use the consumer-reported incident date to fabricate a prediction timeline.

The source API groups tickets on the server; no phone numbers, addresses, ticket identifiers, or subscriber information are downloaded into the study. Duplicate checks compare aggregate row counts against distinct-ID counts.''')
    code('''display(weekly.describe().round(1))
display(daily.groupby('issue').n.sum().sort_values(ascending=False).head(10).to_frame('complaints'))
display(weekly[weekly.all_wireless<100])
print('Anonymous aggregate hash:',manifest['snapshot_aggregate_sha256'])
display(Image('figures/01_history.png'))''')
    md('''## 2. Define a forecast origin and protect every boundary

An origin is Monday 00:00 UTC. Its newest allowed observed week ends immediately before that origin. Four predictions cover the following four weeks. Origins advance by four weeks, so final evaluation targets do not overlap.

Features: log-transformed lags 1, 2, 3, 4, 8, 13, 26, 52; log means over 4, 13, 26, 52 preceding weeks; log 13-week standard deviation; and two annual Fourier harmonics of the known target calendar. Scaling for ridge is fit on each origin's training data. Labels for horizon h enter training only if their target week precedes the current origin.

Development: 104 weeks, October 30, 2023-October 26, 2025. Final evaluation: 52 weeks, October 27, 2025-October 25, 2026. Final outcomes may enter later-origin training once observed; model choice and hyperparameters stay frozen. This is sequential evaluation of an updating forecast system.''')
    code('''display(pd.crosstab(pred[pred.model=='recent_mean_4'].split,pred[pred.model=='recent_mean_4'].horizon))
trace=pd.read_csv(R/'training_trace.csv')
assert (trace.latest_training_target<trace.origin).all()
assert (trace.latest_feature_observation<trace.origin).all()
print('All',len(trace),'recorded fits have strictly historical training targets.')
y=weekly.all_wireless.to_numpy(float)
altered=y.copy(); altered[300:]=1_000_000
for h in [1,2,3,4]:
    np.testing.assert_array_equal(features(y,weekly.index,h)[248],features(altered,weekly.index,h)[248])
print('Future-value perturbation leaves origin features unchanged.')''')
    md('''## 3. Compare useful alternatives

1. Recent four-week mean: a responsive level baseline, constant within each forecast batch.
2. Seasonal naive: repeat the weekly count from 52 weeks earlier.
3. Ridge regression on log1p counts: regularized linear relationships, training-only scaling, alpha 10. Exponentiation has no mean-bias correction; evaluate it empirically rather than calling it an unbiased count mean.
4. Poisson histogram gradient boosting: nonnegative mean-count objective with seven or fifteen leaves; 100 iterations, learning rate 0.05, L2 penalty 10. These two configurations are the complete nonlinear search budget.

The Poisson loss does not assert that the data follow a Poisson distribution. In particular, this study does not obtain uncertainty by assuming variance equals mean. It estimates forecast intervals from preceding out-of-sample errors.''')
    code('''display(pd.DataFrame(selection['development_metrics']).round(3))
print('Overall selection:',selection['selected_model'])
print('ML challenger:',selection['selected_ml_candidate'])
print('Baseline:',selection['selected_baseline'])''')
    md('''## 4. Evaluate point accuracy and interval quality separately

Each model/horizon obtains a nominal 80% interval by adding the 10th and 90th percentiles of the last 26 available origin errors to its current point prediction, clipping at zero. At least 13 earlier origin errors are required. All calibration targets precede the new origin. Errors are signed, so intervals can be asymmetric around the point forecast. The point forecast need not sit at the interval midpoint.

These are empirical residual prediction intervals. Serial dependence and distribution change mean that there is no finite-sample 80% coverage guarantee. We measure actual coverage, interval width, and the 80% interval score: width + 10 times the amount a missed outcome lies outside the interval. Wider intervals alone cannot automatically win this score.''')
    code('''test=pred[pred.split=='test']
display(score(test).round(3))
display(Image('figures/02_model_comparison.png'))
display(Image('figures/03_test_forecasts.png'))''')
    md('''## 5. Quantify comparison uncertainty without pretending folds are independent

There are 52 test predictions, but only 13 forecast origins. We preserve all four horizons per origin, then resample circular blocks of three origins (12 weeks) for a paired MAE-difference interval. Positive differences mean the ML challenger has larger error than the baseline.

With 13 origins this interval is approximate. It is conditional on the observed snapshot and the frozen forecast sequence. It does not refit the pipeline, represent unknown source revisions, or establish universal superiority.''')
    code('''json.loads((R/'comparison_uncertainty.json').read_text())''')
    code('''display(Image('figures/04_horizon_diagnostics.png'))
display(Image('figures/05_period_errors.png'))
display(pd.read_csv(R/'error_slices.csv').round(3))''')
    md('''## 6. Challenge the target definition

Unwanted Calls may dominate the primary target. The sensitivity repeats the frozen design after removing that issue category. It retains the primary model selection for the comparison and reports every candidate transparently. This is an exploratory sensitivity, not a second opportunity to choose a favorable final-test winner.''')
    code('''display(pd.read_csv(R/'sensitivity_metrics.csv').round(3))
display(pd.read_csv(R/'low_reporting_score_sensitivity.csv').round(3))
print('Primary model choices remain:',selection['selected_ml_candidate'],'versus',selection['selected_baseline'])''')
    md('''## 7. Product decision and ownership

Use the findings report to decide whether added modelling complexity is justified and whether nominal intervals can support workload commitments. A prospective shadow test should measure MAE, upper-tail misses and interval coverage as fresh snapshots arrive. Actual staffing requires internal handling-time, routing and arrival data, which are deliberately absent here. No measured cost saving or customer-retention effect follows from this study.

**Ownership experiment:** preserve this release, then replace the expanding training window with a trailing 104-week window. Choose its settings on development data and evaluate on a genuinely later period. Explain the variance/adaptation trade-off before changing the model.

**Key limitations:** source revisions and reporting delays; eight absent UTC days treated as zero; self-selection; no subscriber denominator; coarse interval estimates; no event or carrier-level causal interpretation. See the builder's guide for the two-hour walkthrough and interview defense.''')
    nb=nbf.v4.new_notebook(cells=cells,metadata={'kernelspec':{'name':'python3','display_name':'Python 3','language':'python'}})
    # Python-only cells run in-process, which also works where TCP kernels are unavailable.
    os.chdir(ROOT)
    shell=InteractiveShell.instance()
    count=0
    for cell in nb.cells:
        if cell.cell_type!='code': continue
        count+=1
        with capture_output(display=True) as captured:
            result=shell.run_cell(cell.source,store_history=False)
        cell.execution_count=count
        cell.outputs=[]
        for name in ['stdout','stderr']:
            value=getattr(captured,name)
            if value: cell.outputs.append(nbf.v4.new_output('stream',name=name,text=value))
        for output in captured.outputs:
            cell.outputs.append(nbf.v4.new_output('display_data',data=output.data,metadata=output.metadata))
        error=result.error_before_exec or result.error_in_exec
        if error: raise error
    nb.metadata['execution_method']='Executed Python cells in an in-process IPython shell; captured rich displays'
    nbf.validate(nb)
    nbf.write(nb,ROOT/'analysis.ipynb')
    print('Executed',sum(c.cell_type=='code' for c in nb.cells),'notebook code cells')


if __name__=='__main__':main()
