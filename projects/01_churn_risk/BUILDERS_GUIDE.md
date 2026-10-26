# Builder’s guide · from a churn question to a defensible decision

## What this project actually is

This is **applied Data Science with supervised machine learning**. The observed target is a binary churn label. Logistic regression estimates a regularized linear log-odds relationship; histogram gradient boosting learns nonlinear combinations of predictors through an ensemble of trees. Both estimators learn directly from the observed public predictors and churn labels.

The science is deciding what can be learned from the observations: what the target means, whether evaluation is contaminated by repeated profiles, how a nonlinear model compares with a simpler alternative, whether probabilities improve after calibration, how uncertainty qualifies the result, and what decision is justified. The scripts, data contract, tests and versioned outputs make that science reproducible. A feature store or API would add infrastructure without answering these questions.

The central technique is **nested group-aware probability calibration**. Other substantive practices are a held-out test set, proper-score model selection, paired profile-cluster uncertainty, feature-availability sensitivity, supported subgroup analysis, and development-only threshold selection. Complexity alone does not demonstrate seniority; being able to justify these choices and their limits does.

## A two-hour first walkthrough

| Time | Work | Evidence you should be able to explain |
|---|---|---|
| 0–20 min | Create the Python 3.12 environment and run `run_study.py`. Read the data card. | Publisher, licence, source hash, target horizon, missing calendar dates. |
| 20–40 min | Execute `analysis.ipynb`; inspect repeated profiles and split assignments. | Why identical profiles cannot cross an evaluation boundary; why this is not customer-ID or temporal validation. |
| 40–70 min | Read `GroupTunedClassifier`, `fit_calibrated` and the outer loop. | Which observations each fit, tuning search and sigmoid calibration sees. |
| 70–95 min | Read the prediction table, AP/Brier comparisons and calibration plot. | Ranking differs from probability quality; calibration can fail to improve a score. |
| 95–115 min | Recalculate the top-64 queue and a cost scenario. | Observed label capture differs from prevented churn or money saved. |
| 115–120 min | Defend the findings against the report. | Each reported number has a traceable result and a bounded interpretation. |

Installation time depends on the machine. The full nested study ran in roughly 51 seconds in the recorded Linux environment. These timings are observations and a suggested study plan, not promises about a Mac.

## Reproduce and check success

Follow `README.md` for the exact Mac commands. Main outputs are `results/metrics.json`, `results/test_predictions.csv`, `results/split_assignments.csv`, and a local model at `artifacts/models/selected_model.joblib`. Run the six tests, regenerate the visuals, then execute the notebook. No API key is needed. Pinned dependencies target Python 3.12; a different major Python version may lack compatible wheels.

Successful execution means the publisher bytes match the hash; source/schema checks pass; groups never overlap across evaluated boundaries; probabilities are valid; the saved metrics reproduce from predictions; model selection and thresholds reproduce using development data alone; and all scientific plots render correctly. It does not mean the result is ready for deployment.

## How the files fit together

| File | Responsibility |
|---|---|
| `experiment_plan.json` | Records the prespecified protocol, source identity, split policy, candidates and interpretation limits. It documents the design; some supported settings are explicit constants in `study.py`, so changing this JSON alone is not a general experiment engine. |
| `study.py` | Downloads/verifies the real source; creates tracking metadata; constructs grouped folds, pipelines and nested calibrated estimators; evaluates; calculates uncertainty/queues/costs/slices; saves evidence. |
| `run_study.py` | Calls the complete study with `study` importable, also making the saved estimator loadable in this module namespace. |
| `analysis.ipynb` / `execute_notebook.py` | An executed explanation and independent calculation walkthrough over the locked artifacts. It uses only development data to calculate the constant-prior baseline. |
| `results/selection_locked_before_test.json` | Records eligible candidates and the development-only choice before final evaluation. It is a local audit record, not independent preregistration. |
| `results/development_oof.csv` | Out-of-fold development probabilities for model and threshold selection. Each row is predicted by a model that did not fit that row. |
| `results/test_predictions.csv` | Probabilities, labels and source row positions used for held-out evidence, including matched raw probabilities for calibration diagnostics. |
| `results/split_assignments.csv` | Every source row’s development/test assignment, profile group, target and outer fold. Row numbers are not subscriber identifiers. |
| `results/fit_trace.json` | Phase, model, row-count/hash and best inner parameters for 48 tuned submodels. Runtime assertions additionally check row exclusion. |
| `results/metrics.json` | Recorded environment, source audit, selection, scores, intervals, review and cost results, slices and caveats. |
| `build_figures.py` / `figures/` | Creates exact scientific plots, figure CSVs and provenance hashes. It consumes evaluated outputs and does not refit models. |
| `tests/test_integrity.py` | Checks source/protocol identity, nested grouping, metric reproduction, decision provenance, tie handling and metadata exclusion. |
| `DATA_CARD.md`, `MODEL_CARD.md`, `RESULTS_REPORT.md` | Source/target audit, intended/unsupported uses, measured results and decision limits. |

## Understand the validation boundaries

Start with 3,150 real rows. Group identical **conservative predictor vectors**, without consulting the target when constructing groups. There are 2,826 groups. Keep all observations because repeated rows do not prove duplicate customers; some identical profiles have conflicting labels. Grouping is a conservative dependence safeguard, not an identification claim.

Use the first fold of a seeded five-fold stratified group partition as the final holdout: 639 rows / 103 churn labels. Leave it outside model selection. The remaining 2,511 rows enter three outer development folds.

For one outer fold, split its training portion into three grouped calibration folds. For each calibration fold:

1. Take only the other two calibration folds as the base learner’s data.
2. Inside that portion, run a three-fold grouped search. Fit standardization and category encoding separately inside each search training fold.
3. Choose parameters by inner Brier score and refit the pipeline on that calibration-training portion.
4. Use the unseen calibration fold to fit a sigmoid transformation of the base learner’s scores.
5. Average predictions from the three calibrated submodels, then score the completely unseen outer evaluation fold.

If tuning were done once on all outer-training data before calibrating on its subfolds, the supposedly held-out calibration labels could already have influenced parameter selection. The custom estimator moves tuning inside each calibration-training fit to avoid that indirect reuse.

Pooled outer predictions select between prior, conservative logistic and conservative boosting. Then fit the chosen architecture using development data only, again with nested tuning/calibration. The all-field candidates are sensitivity analyses and are never eligible for primary selection. The final holdout is scored after this selection is written to disk.

The final-test labels can be used for uncertainty and descriptive diagnostics after evaluation. They must not then tune the model while retaining the same test’s status as independent evidence. The raw/calibrated result here remains a diagnostic; changing the winner after observing that result would change the study.

## Why these models and metrics?

The prior baseline predicts the development prevalence for everyone. At threshold 0.5 it predicts no churn. Its high accuracy exposes why class imbalance matters. Logistic regression is the interpretable, regularized simple comparator. Histogram boosting tests whether nonlinear relationships improve prediction with a small, explicit search budget. Neither needs synthetic oversampling; oversampling can alter probability interpretation unless corrected and validated.

**Average precision** measures positive-class ranking across thresholds, using the non-interpolated definition from scikit-learn. It depends on prevalence; 0.930 in this sample cannot be compared uncritically across populations. It is not accuracy, precision at 10%, or trapezoidal PR area.

**Brier score** is mean squared probability error. It is a proper score and the prespecified selection objective, but it combines reliability and resolution. A lower value alone cannot establish better calibration. **Log loss** is another proper score, especially sensitive to confidently wrong predictions. **ROC-AUC** is useful supporting ranking context but does not describe review workload under low prevalence.

Reliability curves bin predictions and compare mean predicted risk with observed churn fractions. Eight fixed bins are used, with counts saved. A line close to the diagonal can still be unstable if bins have little support. Sigmoid calibration maps scores through a fitted logistic form; it can improve, do little or hurt. Here Brier slightly worsened from 0.03608 to 0.03721. Keep that finding instead of presenting calibration as an automatic upgrade.

## Uncertainty, sensitivity and errors

Bootstrap complete held-out profile groups, keeping all rows of a sampled profile together. Use the same resample for each model to obtain a paired Brier difference. Five hundred resamples provide approximate conditional intervals; increasing them reduces Monte Carlo noise, not data or domain uncertainty. These intervals condition on the trained models. They do not capture the variability of refitting across new development samples, unknown customer dependence, source selection or market transfer.

Do not t-test three outer-fold scores as independent measurements. They share training observations. Do not interpret overlapping AP intervals as a formal paired hypothesis test. The paired Brier interval is the explicitly paired comparison provided here.

Status and Customer Value are excluded from primary features because their construction/operational interpretation needs verification. UCI nevertheless states that predictors cover months 1–9. Exclusion is a conservative availability sensitivity, not a leakage accusation. All-field performance is reported to show how much the conclusion changes.

Error slices contain n, positive counts, observed prevalence, mean probability and Brier. The support flag requires at least 50 rows and at least ten of each class. It is a reporting heuristic, not a power calculation or fairness certification. The tariff-plan-2 slice has just two positives; its low aggregate error cannot justify a favorable treatment or fairness claim.

## From probabilities to a product question

At 10% requested review capacity, ceil(639 × 0.10) = 64 records. The selected model’s queue contains 63 of the 103 churn labels. Queue precision is 63/64; recall is 63/103; the random-review expected recall is 64/639. Ties use a seeded, label-independent hash, so source row order cannot decide the favorable result.

The model has predicted observed risk. It has not measured responsiveness to an offer. A customer can be high-risk and impossible to retain, while a lower-risk customer could respond strongly. Estimating that difference requires suitable treatment/outcome data and a causal design, ideally a prospective randomized offer experiment after target-domain validation.

The false-negative cost scenarios use 5, 10 or 20 hypothetical units against false-positive cost 1. Choose thresholds from development OOF probabilities, then evaluate once on the holdout. The resulting costs are normalized classification penalties, not dollars or retention ROI. Offer policy economics require treatment benefit, customer value, costs and guardrails beyond these labels.

## Common errors and diagnosis

| Symptom | Likely cause and action |
|---|---|
| Source hash fails | Publisher bytes changed or download was interrupted. Inspect the file and source metadata; do not simply replace the expected hash to make a test pass. Remove a known incomplete local download and retry. |
| `python3.12` missing | Install/use Python 3.12, then create a fresh venv. Confirm the interpreter before installing pinned wheels. |
| `ModuleNotFoundError` | Activate the environment and use `python -m pip`, ensuring installation and execution use the same interpreter. Notebook packages are a separate requirements file. |
| Notebook dependencies missing | Install `requirements-notebook.txt` into the active venv and run `execute_notebook.py` with that interpreter. The Python-only walkthrough executes in-process through IPython, capturing rich displays without a kernel server or network ports. |
| Pipeline learns from `row_id` | Tracking fields must be dropped by the explicit ColumnTransformer. The metadata-invariance test checks this behavior. |
| Scores differ in another environment | Compare source/protocol hashes, split file, Python/library versions, thread settings and seed before interpreting the difference. CSV rounding permits tiny numerical tolerance. |
| Very high subgroup precision | Check positive counts and queue sizes. Small-source results and rare groups can look deceptively certain. |
| Temptation to call it temporal validation | There are no real snapshot dates. A month-nine feature window does not supply a rolling-origin panel. Do not invent timestamps or sort by tenure. |
| A new model wins on this test set | Treat it as exploratory. Select it on development data and obtain a fresh independent evaluation before making a confirmatory claim. |

## Deeper study and ownership

For the rest of the week, spend about two hours a day on a substantive extension rather than repeatedly optimizing this holdout. Create a new experiment directory; preserve this protocol and outputs.

1. **Calibration study:** within development data only, compare no calibration, sigmoid and a justified alternative using the same outer folds and matched base learners. Freeze a selection rule before scoring. Report OOF probability scores and sparse-bin behavior; do not use this already-inspected holdout to certify the chosen alternative.
2. **Split robustness:** repeat development-only grouped evaluation for five prespecified seeds. Quantify how the model comparison changes, keeping the original holdout excluded. Explain why that variability is different from the conditional test bootstrap.
3. **Dependence sensitivity:** compare the retain-all policy with an explicitly defined profile-weighted objective using development data. Preserve conflicting labels and explain what population each weighting estimates. Do not silently drop contradictory records.
4. **Decision study:** choose review capacities before evaluation and calculate sensitivity to target prevalence and hypothetical error costs. Keep simulated/assumed values labelled and separate from observed source outcomes.

Save the exact change, motivation, measured comparison, uncertainty and what you would do differently. Be able to reproduce the three central numerical findings and explain the calibration result without reading the report.

## Interview defense

- **Why isn’t this a basic churn notebook?** The model family is ordinary; the contribution is the defensible experiment: dependence-aware splits, tuning inside calibration training, untouched model selection/evaluation, honest uncertainty and a bounded decision.
- **Why not remove duplicate rows?** Their customer identity is unknown, and profiles can conflict in target. Grouping controls cross-boundary profile reuse while preserving the observed distribution; alternative weighting remains a sensitivity question.
- **Why select Brier rather than AP?** The primary question includes probability quality. AP describes ranking, while Brier is a proper probability score. Both are reported because the queue and risk estimate have different objectives.
- **Why keep a slightly worse calibrated result?** That was the prespecified candidate. A negative diagnostic should change the next experiment, not silently rewrite the current evaluation after observing its test set.
- **What would justify deployment?** Verified feature timing/construction, current permitted target-domain data, a genuine temporal/prospective validation, workload and probability monitoring, and a separate experiment if an offer effect is claimed.
