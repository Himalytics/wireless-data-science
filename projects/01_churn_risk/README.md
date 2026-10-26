# Project 1 · Can we trust churn-risk probabilities?

**Built and evaluated October 26, 2026. Applied Data Science / supervised machine learning.**

A real, observed telecom dataset; a constant-prior baseline, regularized logistic regression and histogram gradient boosting; genuinely nested tuning and sigmoid calibration; identical-profile grouping; conditional bootstrap uncertainty; feature sensitivity; subgroup errors; and capacity/cost decisions with explicit limits.

The new technique is **nested group-aware probability calibration**: tune each base learner inside its own calibration-training fold, then evaluate on an outer fold that neither fitting nor calibration has seen. This prevents tuning from indirectly consuming calibration/evaluation labels.

## Reproduce on a Mac

Use Python **3.12**. From the repository root:

```bash
cd projects/01_churn_risk
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python run_study.py
python -m unittest discover -s tests -v
python build_visuals.py
```

If `python3 --version` reports 3.12, `python3` can replace `python3.12`. The study downloads the publisher's 41 KB ZIP itself and verifies its SHA-256. A changed source fails explicitly rather than silently using different data. Raw inputs and model binaries stay local and are ignored by git. No credentials, paid service, employer access, or Docker are required.

For the executed explanatory notebook:

```bash
python -m pip install -r requirements-notebook.txt
python execute_notebook.py
```

`analysis.ipynb` is already executed and viewable on GitHub. Notebook execution audits saved results and fits the development-only constant prior; it does not rerun the entire nested search. `run_study.py` performs the full training/evaluation workflow.

## Measured result

All primary figures below use **639 held-out rows, including 103 churn labels**, after selecting the model using development-only out-of-fold Brier score.

| Model | Average precision ↑ | Brier error ↓ | ROC-AUC ↑ |
|---|---:|---:|---:|
| Constant training prior | 0.161 | 0.1352 | 0.500 |
| Logistic, 11 predictors | 0.772 | 0.0727 | 0.931 |
| Gradient boosting, 11 predictors | **0.930** | **0.0372** | **0.982** |

The selected model captured **63 of 103 churn labels** in the top **64 of 639 records**. Sigmoid calibration **slightly worsened** Brier error relative to its matched raw ensemble (0.0361 → 0.0372). Both findings are retained.

![Held-out average precision with uncertainty](figures/02_average_precision.png)

This is a historical Iranian source-sample result, not a chronological backtest, U.S. carrier estimate, retention effect, or production approval. See [the complete findings](RESULTS_REPORT.md).

## Read the project

- [Builder's guide and two-hour walkthrough](BUILDERS_GUIDE.md)
- [Executed notebook](analysis.ipynb)
- [Dataset card and attribution](DATA_CARD.md), [model card](MODEL_CARD.md)
- [Prespecified experiment protocol](experiment_plan.json) and [experiment record](EXPERIMENT_RECORD.md)
- [Saved metrics](results/metrics.json), [test predictions](results/test_predictions.csv), [split assignments](results/split_assignments.csv)
- [Plotting/carousel code](build_visuals.py), [chart provenance](figures/provenance.json)
- [Today's LinkedIn draft](../../posts/01_churn_risk/linkedin_post.md), [six-page carousel](../../posts/01_churn_risk/01_churn_risk_carousel.pdf), [captions and alt text](../../posts/01_churn_risk/ASSETS.md)

Actual execution was on Linux / Python 3.12.14. The main study took about 51 seconds in that environment; installation and other machines will vary. Mac instructions are supplied; macOS execution is claimed only if the linked GitHub Actions run passes. Six integrity checks passed locally. No LinkedIn publication has occurred.
