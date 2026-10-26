# Dataset card · Iranian Churn

**Attribution:** Iranian Churn [Dataset]. (2020). UCI Machine Learning Repository. https://doi.org/10.24432/C5JW3Z. Licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).

Publisher: https://archive.ics.uci.edu/dataset/563/iranian+churn+dataset. Automated input: https://archive.ics.uci.edu/static/public/563/iranian+churn+dataset.zip. Retrieved October 26, 2026. ZIP SHA-256: `696c3a1812267980751f30d19193a1b430ac4ad76172bb089e664c96813ead66`.

## Population, timing and target

UCI describes randomly collected records from one Iranian telecom company over twelve months. There are 3,150 rows and 13 predictors. The target `Churn` is the customer state at month twelve; predictors aggregate the first nine months. This supplies a documented three-month planning gap, not dated snapshots. Collection calendar dates, company identity and contemporary representativeness are not provided. Donation date (2020) is not the measurement period.

No source customer ID exists in the downloaded CSV despite an ID mention in the metadata prose. `row_id` in saved results is a zero-based source row position, not a person identifier. `profile_group` is derived from identical conservative predictor values and does not establish common customer identity.

## Executed audit

| Check | Observed result |
|---|---:|
| Rows / predictors | 3,150 / 13 |
| Churn / no-churn labels | 495 / 2,655 |
| Missing cells | 0 |
| Repeated full rows after first occurrence | 300 |
| Repeated full predictor vectors after first occurrence | 314 |
| Distinct conservative predictor profiles | 2,826 |
| Conservative profiles with conflicting target labels | 22 |

Retain every observed row. Identical conservative predictor profiles share a group across all split boundaries. Exact repeated rows are not proof that the same customer was recorded more than once. The grouping reduces one source of overly optimistic validation but cannot resolve unknown dependence.

## Features and transformations

Names are normalized to snake_case. Continuous/count predictors use training-fold standardization. Charge amount, age group and tariff plan use training-fold one-hot encoding (status also does in the secondary model). This intentionally treats ordinal fields as flexible categories; alternatives belong in development-only experiments. No imputation, oversampling or synthetic rows are used. Unseen categories are ignored by the encoder.

Primary features: call failures, complaint indicator, subscription length, charge amount, seconds of use, use frequency, SMS frequency, distinct called numbers, age group, tariff plan and age. Age and its grouped representation are related; regularization and the comparison design address prediction, not causal interpretation of age coefficients.

`Status` describes active/non-active state. `Customer Value` is a calculated field whose construction is unspecified. Although UCI says all predictors cover months 1–9, primary models conservatively exclude these two fields pending operational construction/availability checks. This is not a declaration that UCI contains target leakage. All 13 fields appear only in a separately reported sensitivity analysis.

## Access, adaptation and limits

No employer data, simulated customers or fabricated dates are included. Derived split files and predictions identify source row positions and preserve the above attribution. Changes from source: normalized names, profile-group/row-position metadata, deterministic split assignments, fitted-model predictions and aggregate results. Source licence applies to source-derived data.

This historical single-company observational sample cannot validate U.S. market transfer, changes over calendar time, contemporary drift, effects of offers or protected-group fairness. New target-domain and prospective evidence is required.
