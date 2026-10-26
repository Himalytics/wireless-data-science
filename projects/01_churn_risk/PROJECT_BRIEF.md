# Project 1: can we trust churn-risk probabilities?

Status: specified, not built or evaluated. First scheduled build: November 2, 2026.

## Product question

Can an observed telecom dataset support a churn-risk model whose probabilities are reliable enough to inform a capacity-constrained review queue? Compare ranking quality, probability accuracy, and the sensitivity of a proposed review policy. Do not claim that contacting a high-risk customer prevents churn.

## Real public source

- Dataset: **Iranian Churn**, UCI Machine Learning Repository, ID **563**.
- Authoritative page: https://archive.ics.uci.edu/dataset/563/iranian+churn+dataset
- DOI: https://doi.org/10.24432/C5JW3Z
- Licence stated by UCI: **CC BY 4.0**, with attribution.
- Download route: `ucimlrepo.fetch_ucirepo(id=563)` or the publisher ZIP, implemented in code with source/version details and a checksum.

UCI describes 3,150 customer records with predictors aggregated over the first nine months and churn labels at the end of twelve months. This supplies a documented feature/label gap, not multiple dated customer snapshots for rolling backtests. The source is an Iranian telecom sample; it does not demonstrate current U.S. carrier outcomes or employer impact.

## Prespecified hypotheses

1. A justified nonlinear model may improve ranking over regularized logistic regression; improvement must be measured against uncertainty and a no-skill baseline.
2. Better ranking need not imply better probability estimates; calibration must be evaluated separately.
3. Conclusions may depend on features with unclear construction or operational availability. Audit metadata and perform a conservative feature-set sensitivity analysis without asserting leakage from a name alone.
4. The composition of a review queue may change with capacity and cost assumptions. These are decision scenarios, not measured retention treatment effects.

## Study design

Create a data/feature-availability audit and a reproducible stratified development/test split, subject to an actual duplicate/dependence check. Keep the final test set untouched during model selection. Use nested cross-validation or a justified equivalent within development data for preprocessing, hyperparameter selection, and calibration. Do not invent chronological order.

Compare a no-skill predictor, regularized logistic regression, and at least one justified nonlinear model. Report the search budget, seeds, preprocessing decisions, and class-balance treatment. Choose modelling complexity based on the evidence, not the number of libraries used.

Report precision-recall performance, ROC-AUC as supporting context, Brier score/log loss, calibration behavior, and operating-point precision/recall at explicitly defined review capacities. Use appropriate uncertainty estimates with clear scope. Avoid treating cross-validation folds as independent experimental replicates.

Include model/feature ablations, subgroup/error analysis with support counts, and limitations from geography, historical sampling, and missing longitudinal or treatment data. Explanations describe predictive associations, not causes.

## Required outputs

Working Mac-runnable code and an explanatory notebook; source/data card; saved split/configuration and predictions; measured baseline/model comparisons; calibration, ranking, uncertainty, and error-analysis figures; an experiment record; findings report; model card; builder's guide; and a results-led LinkedIn draft with a verified PDF/PNG carousel.

The product conclusion must identify what the evidence supports, where uncertainty changes the recommendation, and what prospective data or experiment would be required before using a retention intervention. A negative or inconclusive model comparison is an acceptable result.

## Ownership exercise

Reproduce the baseline, change one scientifically important choice, and defend its effect. Examples: a conservative feature set, calibration approach, split sensitivity, or review capacity. Save the actual comparison and explain why the change strengthens or weakens the original conclusion.
