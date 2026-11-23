# Builder's guide: defend the policy, not just the model

## What this teaches

Churn risk answers who is likely to leave. Uplift asks whose outcome changes because of an assignment. Project 1 could not identify the second question: there were no randomized offers. This project deliberately switches to an observed randomized-source advertising benchmark. The method can inform how to design a wireless retention study; its visit contrasts cannot substitute for retention evidence. Infrastructure is small so that the difficult work stays visible: eligibility, identification, independent model choice, counterfactual evaluation and uncertainty.

The main hypothesis, declared before test access, is that a T-learner at a hypothetical 20% assignment capacity improves released-benchmark visit contrast over random and response ranking. The evidence supports the random comparison, not superiority over the response baseline. That distinction is the central result, rather than an inconvenience to remove.

## Two-hour guided entry

| Minutes | Action and question to answer |
|---|---|
| 0–15 | Read DATA_CARD and protocol. Explain why assignment, exposure and visit have different roles. Explain why original-population causal effects remain unavailable. |
| 15–35 | Open the notebook audit. Reconcile train/validation/test counts, two arms and visit counts. Inspect treatment balance and why identical profiles stay grouped. |
| 35–55 | Trace `source.py` from URL to hash, chunk sample and profile split. Explain why ordinal sampling does not create a temporal backtest. |
| 55–75 | Trace four candidate pairs in `run.py`. Explain the fitting boundary and why validation selects policy value rather than classification AUC. |
| 75–95 | Recompute IPW contributions for one treated visitor, one control visitor and a nonvisitor. Reproduce the paired random comparison in notebook. |
| 95–110 | Read capacity, decile and estimator plots. Say what each interval conditions on and what uncertainty it omits. |
| 110–120 | State the product decision in three sentences; identify the experiment needed before a carrier application. |

Run installation/download outside the walkthrough if your network is slow. Tests can run immediately after installing dependencies against committed outputs. Use the main README commands for full training; a notebook rendering alone is not a full replication.

## Architecture and file responsibilities

`protocol.json` is the scientific contract, not an application configuration to casually tune against test outcomes. `source.py` owns retrieval, the pinned correction version, SHA256, schema, deterministic row sample and group boundary. The source gzip is 311 MB; pandas chunks prevent loading 14 million rows at once. The cached sample is local trusted pickle for speed, not a distributable model artefact.

`run.py` owns the experiment: set single-thread environment variables before numerical imports; fit four separate treated/control pairs; fit assignment diagnostic; calculate validation objective; freeze a winner; predict test once; save policy contributions, paired uncertainty, sensitivity and figures. No exposure, conversion or treatment indicator enters the baseline feature matrix. The assignment diagnostic uses treatment as its target, not a policy predictor. `top()` implements an outcome-blind batch capacity and deterministic tie breaking.

`results/splits.csv.gz` records source row IDs, feature-profile hashes and all partitions; it is sufficient to audit separation without publishing raw covariates. `predictions.csv.gz` records holdout assignments/outcomes, four uplift scores, response score, nuisance predictions, propensity, IPW contribution and two primary policy allocations. These allow independent metric recomputation. `source.json` identifies bytes and retrieval; `experiment.json` identifies environment, choice and diagnostics. Small CSVs are exact plot data, not hand-transcribed numbers. Scientific figure provenance is in `results/FIGURES.md`.

`notebook.py` constructs and executes the explanatory notebook. It exposes actual tables and recomputes core metrics; it does not hide full model fitting behind a display cell. `test_integrity.py` checks frozen evidence without needing 311 MB in CI. `requirements.txt` pins direct dependencies; `requirements-lock.txt` pins the 51 direct and transitive study dependencies from the execution environment. `results/environment.txt` records those study versions and the actual platform, excluding unrelated host packages. The lock file is the portable installation contract. The recorded notebook executed actual cells through in-process IPython because this host blocks Jupyter kernel sockets; normal Jupyter execution remains available on a Mac.

## Statistical choices and alternatives

**Why a grouped three-way split?** There are no dates or experiment IDs. Temporal validation would be fictional. Identical baseline profiles are conservatively kept together so a duplicate-like profile cannot cross fitting and evaluation. Hashing gives approximately 50/20/30 train/validation/test; it cannot protect against unknown advertiser dependence. An independent test justifies a small validation search without full nested cross-validation. Four candidates is a deliberately bounded search, not proof of optimality.

**Why a T-learner?** It makes the causal-versus-predictive distinction inspectable: fit visit probability in each assignment arm, then subtract. It can waste information when the control arm is much smaller and can give poorly calibrated effects. S-learners with treatment interactions, honest causal forests, cross-fitted DR learners or X-learners are defensible extensions, not automatic improvements. They require a fresh evaluation plan. A response classifier can win when visit risk and treatment responsiveness align; this study retains that possibility.

**Why IPW first?** Its evaluation does not rely on the uplift learner's own predicted outcomes. With p from training, each observed visitor contributes positive weight if assigned and negative weight if held out. Under the working assignment assumptions, multiplying by the policy selects whose treatment effect contributes. DR sensitivity augments this with training-only outcome predictions. Neither removes unidentified publisher selection. A treatment-prediction AUC near 0.5 does not establish causal identification. A conditional propensity model can change weighting, but absent known assignment probabilities it is not a recovered experiment protocol.

**Why paired uncertainty?** Policies are evaluated on the same people. Subtract their contributions before resampling; separate confidence-interval overlap is not a valid paired test. Profile Poisson multipliers share weight across identical profiles and normalize by resampled size. We condition on fitted scores and chosen test batch, not the training algorithm's future performance. Refitting everything and repeating grouped outer splits would address additional instability at considerable cost, but still would not address unknown experiment clusters or privacy selection. No dependent-fold t-test or individual causal-effect coverage claim appears here.

**Why not report Qini as the only result?** A ranking area can hide whether a relevant capacity beats a cheap business baseline. We report a prespecified 20% policy contrast, paired differences, a capacity curve and exploratory deciles. The curve is an uplift-style cumulative gains diagnostic, not a calibrated treatment-effect probability. Additional comparisons are not independent confirmatory discoveries. Costs and capacity are assumptions; there is no observed profit measurement.

## Common errors and recovery

Checksum mismatch: delete only an incomplete download and re-download the pinned URL; never bypass the guard or silently switch to v1. Schema failure: inspect publisher revision before changing expectations. Memory pressure: keep chunk size fixed or implement a verified equivalent sampler; do not take only the first rows. Missing kernel: install/register ipykernel in the active environment, then regenerate the notebook. Reproduction differences: first compare source/protocol hashes, dependency versions, split assignments and floating-point output tolerance; gzip container timestamps can differ even when decompressed tables match.

Never add exposure to improve performance: it is post-assignment. Never optimize capacity or the model from these test charts and still call the result confirmatory. Do not relabel visits as retained subscribers or convert a benchmark contrast into revenue without observed economics. Do not infer a treatment assignment date from row order. Do not erase a losing model or negative comparison.

## Seven daily ownership experiments, about two hours each

1. Recompute every policy metric from saved predictions in your own code. Check the denominator and reproduce the random policy analytically. Write down why 20% random is not the same as observed control visits.
2. In a new versioned experiment, compare a Hájek normalized policy contrast with IPW. Declare the estimand and selection metric first. Inspect finite-sample assignment imbalance and preserve the original result.
3. Repeat the whole declared protocol with a different outcome-blind sample hash salt and fresh evaluation split. Compare selection stability; do not choose the most flattering repeat. Quantify how often logistic versus boosted T-learners win.
4. Implement a cross-fitted DR learner using only training folds for nuisance fitting. Predeclare hyperparameters and compare on a newly reserved split. Explain the orthogonality argument and where privacy selection still breaks population identification.
5. Refit bootstrap training samples as well as test clusters on a smaller declared sample. Compare this wider uncertainty question to the conditional intervals here. Keep the computational budget and convergence evidence.
6. Define hypothetical per-assignment costs on a clearly labelled sensitivity grid. Derive when an incremental contrast would justify assignment. Avoid calling arbitrary costs measured profit; separate benchmark utility from deployable economics.
7. Draft a real wireless experiment protocol without using company data: eligibility, randomized assignment, retention horizon, interference risk, guardrails, sample-size assumptions, costs and held-out policy evaluation. Specify which new observations would actually identify retention uplift.

## Interview defense

Be ready to derive IPW, explain why randomization plus unknown outcome-dependent subsampling is insufficient for original-population effects, distinguish intent-to-treat assignment from exposure, justify keeping same-profile groups together, explain the small independent selection budget, defend the response baseline, and describe exactly what the bootstrap omits. The honest answer to “Did uplift beat response ranking?” is “This held-out comparison did not establish that.” The stronger engineering/science judgment is knowing when a sophisticated policy has not earned deployment.
