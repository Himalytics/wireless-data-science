# Findings: compare uplift to a strong simple policy

Executed November 23, 2026. Observed Criteo v2.1 advertising benchmark; no employer data. Primary question and search were locked in `protocol.json` before test evaluation. **Hypothesis:** at a hypothetical 20% advertising assignment capacity, a T-learner improves released-sample visit contrast over random allocation and logistic response ranking. The evidence supports the random comparison; it does **not** establish superiority over response ranking.

## Data audit and design

The publisher's corrected source has 13,979,592 anonymous rows. An outcome-blind approximately 5% hash sample retained **699,450** rows: **350,077 train**, **139,250 validation**, **210,123 test**. Identical baseline profiles stay in one partition. There are **11,204 rows belonging to repeated baseline profiles** and **8,263 rows belonging to identical full-record duplicates** in the sampled data. These are member counts, not extra-duplicate counts. They do not prove repeated customer identities. The test contains **208,459 distinct baseline profiles**. No dates, experiment IDs or causal individual labels were invented.

| Holdout assignment arm | Rows | Observed visits | Observed visit rate |
|---|---:|---:|---:|
| Control | 31,048 | 1,178 | 3.794% |
| Assigned advertising | 179,075 | 8,600 | 4.802% |

These marginal observed rates are not an individual treatment-effect model. Training assignment share is **0.850404**. A training-only logistic assignment model scores **0.50874 held-out AUC**; max absolute training feature SMD is **0.04553**; predicted test assignment probabilities range **0.8064–0.9130**. The source is close to balanced on these diagnostics, but not indistinguishable by covariates. No significance or equivalence threshold was prespecified. These checks cannot certify original randomization after privacy subsampling or identify original assignment probabilities.

The four-pair search compared logistic C=0.1/1 and boosted T-learners with 7/15 leaves, selecting on validation IPW policy contrast at 20%. Validation values were **8.697, 8.864, 9.403 and 8.574** visits per 1,000 eligible users, respectively. The selected **7-leaf boosted T-learner** was frozen without train+validation refitting. All preprocessing and nuisance fitting used training observations only; test scores did not change the model, objective or capacity.

## Primary held-out policy comparison

Units: **incremental visit contrast per 1,000 eligible released-benchmark users**, relative to no assignment under the constant-propensity working model. Capacity is hypothetical, not a measured campaign budget. Intervals are conditional 95% profile-cluster Poisson multiplier percentile intervals, 500 replicates. Random allocation is integrated in expectation, not a simulated successful campaign.

| Policy | Assigned fraction | IPW contrast | Conditional 95% interval |
|---|---:|---:|---:|
| No assignment | 0% | 0.00 | 0.00–0.00 |
| Random allocation | 20% | 2.13 | 1.71–2.57 |
| Logistic response ranking | 20% | 10.06 | 7.94–12.18 |
| Selected uplift ranking | 20% | 9.90 | 8.15–11.76 |
| Assign everyone | 100% | 10.65 | 8.53–12.87 |

Each ranked 20% policy assigns **42,025 / 210,123** users (20.00019%, ceil-rounded). Uplift allocation contains **36,284 treated / 5,741 control** rows and **6,005 / 745** respective observed visits; response allocation contains **36,134 / 5,891** rows and **7,795 / 1,055** visits. These selected observed counts do not themselves measure policy incrementality; assignment weighting and the entire eligible denominator matter.

The **paired** uplift-minus-random contrast is **7.77** (95% **6.33–9.30**). Against response ranking it is **−0.16** (**−1.36–1.37**). The latter is inconclusive; it is neither evidence of uplift superiority nor proof of practical equivalence. Separate interval overlap is not used as a paired test. No post hoc test-based model switch is made.

## Robustness that changes the interpretation

| Frozen-policy estimator | Advantage over random / 1,000 | Conditional 95% interval |
|---|---:|---:|
| Primary constant-propensity IPW | 7.77 | 6.33–9.30 |
| Approximate published p=0.85 | 7.83 | 6.38–9.35 |
| Training logistic covariate propensity | 6.06 | 4.54–7.70 |
| DR with independent training-only outcome fits | 4.08 | 2.90–5.48 |

The DR estimate is about **48% smaller** than primary IPW, a material estimator sensitivity rather than a rounding issue. Thus the direction of the benchmark random comparison persists across these declared estimators, while the magnitude is not stable. No estimator is privileged after viewing test results to manufacture a larger gain. With DR, uplift-minus-response is **−0.79** (95% **−1.86–0.46**), also not establishing superiority. Constant-assignment IPW can be sensitive to finite-sample covariate and selected-arm imbalance. DR/covariate weighting introduce their own nuisance assumptions. None recovers unknown privacy-selection probabilities.

The capacity curve retains the same frozen model: it is exploratory, not six independent model-selection trials. At 10%, 40%, 60%, 80% and 100% the ranking trade-offs differ. Do not tune a deployment budget from this test curve and claim a new confirmatory result. Exact values and intervals are in `results/capacity.csv`.

Exploratory deciles show ranking and effect calibration differ. The top decile has IPW contrast **88.75 per 1,000** versus predicted **75.98**; the bottom decile predicts **−19.45**, but its observed contrast is **2.80** (95% **−8.89–15.16**). Individual negative effects have not been demonstrated. Decile intervals are pointwise with no simultaneous-coverage or multiplicity-adjusted claim.

## Product decision and limits

The simple response policy remains a serious comparator. In this benchmark, the uplift model has not earned a stronger claim or the additional deployment complexity solely from the primary comparison. Both ranked policies outperform expected random allocation on the reported working-model contrast; their original-campaign causal value remains unidentified by these released records. A sensible next scientific step is independent replication with known assignment probabilities and a fresh locked evaluation, rather than declaring an advertising or wireless business win.

For a retail wireless product team, this study demonstrates **how to test** a targeting method. A valid retention decision requires a distinct randomized offer experiment with eligibility, pre-treatment features, observed offer assignment, churn/retention horizon, costs, interference assumptions and guardrails. Measure incremental retention or net value on a reserved evaluation population; do not infer it from visit propensity, churn risk or these anonymized advertising observations. No internal data or proprietary designs were used.

Uncertainty here conditions on selected fits, estimated propensity, observed allocation and profile grouping. It omits algorithm-selection/training variation, unknown user/advertiser dependence, unknown privacy sampling, time shift, economic uncertainty and transport to telecom. The source has no authentic temporal holdout. Criteo explicitly says nonuniform privacy subsampling prevents recovering original incrementality. This is a source-domain method benchmark, not original trial ITT, a causal ground truth for each user, employer impact or a current U.S. carrier estimate. Source, version, attribution and CC BY-NC-SA 4.0 terms are in `DATA_CARD.md`.
