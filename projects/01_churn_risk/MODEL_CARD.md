# Model card · conservative calibrated gradient boosting

Version: Project 1, October 26, 2026. Purpose: educational source-sample churn ranking and probability evaluation, not a live carrier decision system.

## Model and data

Histogram gradient boosting behind a training-fold scaler/encoder. Three independently tuned base learners are sigmoid-calibrated on separate grouped calibration folds and averaged. Features: the 11 conservative fields defined in `study.py`; Status, Customer Value, row position, profile-group metadata and target are excluded. Fit source: 2,511 development records from UCI Iranian Churn. See `DATA_CARD.md` for CC BY 4.0 attribution, sampling and target-window limits.

Selection used three outer grouped development folds, calibration inside outer training and tuning inside calibration training. Objective: minimum pooled OOF Brier among eligible prior, logistic and boosting candidates. Final evaluation: 639 disjoint held-out records / 103 churn labels / 571 profile groups.

## Measured performance

- AP 0.9298; conditional 95% profile-cluster bootstrap interval 0.8808–0.9664.
- ROC-AUC 0.9824; Brier 0.03721; log loss 0.13466.
- Top 64 reviews: 63/103 churn labels; queue precision 63/64. Point estimates, not promises.
- Matched raw ensemble Brier 0.03608; sigmoid calibration did not improve this score.
- Sensitivity with all 13 fields: AP 0.9415, Brier 0.03558; ineligible for primary selection.

The intervals condition on fitted models and this source sample. No external, chronological, U.S. carrier or employer validation exists. Subgroups with too few churn labels are flagged; no fairness conclusion is supported. Age-related predictors are included for this educational comparison; lawful and appropriate use would require a separate deployment review.

## Appropriate and unsupported uses

Appropriate: learn nested validation, evaluate ranking and probability scores, reproduce the audit, design a prospective follow-up. Unsupported: claim prevented churn, assign retention offers from inferred uplift, estimate revenue impact, generalize to Boost Mobile/U.S. subscribers, or deploy without current target-domain evidence.

## Reproduction and persistence

Use the pinned environment and `run_study.py`. Final hyperparameters for every submodel are in `results/fit_trace.json`. The fitted object is written locally to `artifacts/models/selected_model.joblib` and ignored by git; code, source hash, protocol, splits, predictions and metrics are versioned. Load only a joblib file produced by your trusted local run, using this pinned environment. The `study` module must be importable when loading it.

There is no model server, production monitoring or treatment-effect model in this release. The deliberate product outcome is a bounded evidence decision and an experimental validation plan.
