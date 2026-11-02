# Executed experiment record

- Analysis date: November 2, 2026.
- Protocol: version 1.1; SHA-256 recorded in `results/execution.json` and `results/selection_locked_before_test.json`.
- Source: authoritative FCC CGB complaint aggregate; retrieval timestamp, source update metadata, exact queries and response hashes in `results/source_manifest.json`.
- Source-date amendment: see `PROTOCOL_AMENDMENT.md`. Initial source-calendar diagnostics were discarded when the audit chose the documented UTC submission timestamp; model configurations and evaluation dates were not tuned in response to final results.
- Input: 1,259,229 distinct complaints, 25,888 daily issue groups, 460 weekly targets. Anonymous CSV snapshot and source audit responses are committed for reruns.
- Fitting: expanding-history direct models at 76 four-week origins; three learned candidates times four horizons times two target definitions = 1,824 recorded fits. Two baselines are also evaluated. See `training_trace.csv` for every boundary and training support count.
- Warmup/development/final targets: saved per forecast in `backtest_predictions.csv`; development has 26 origins/104 weeks and final evaluation 13 origins/52 weeks per model.
- Search budget: one fixed ridge configuration and two fixed Poisson boosting configurations. No final-test model or hyperparameter selection.
- Selection: recent four-week mean overall; 15-leaf Poisson boosting as ML challenger. Saved before final scoring in each execution.
- Intervals: previous eligible same-horizon residuals, latest 26 origins, minimum 13; signed empirical 10th/90th quantiles and clipping at zero.
- Comparison uncertainty: 2,000 paired circular moving-block bootstrap resamples with three adjacent origins per block, fixed seed 20261102.
- Sensitivity: repeat all candidates excluding Unwanted Calls, retaining primary model choices for the headline comparison.
- Execution environment: Linux, Python 3.12.14, NumPy 2.3.5, pandas 2.2.3, SciPy 1.17.0, scikit-learn 1.8.0. Full study approximately 70 seconds excluding download and installation; exact elapsed time in execution JSON.
- Checks: eight scientific integrity tests; source-hash and boundary assertions; independent metric calculations; five scientific figures with hashed exact CSV data; explanatory notebook executed in-process. The primary run and frozen-input rerun are compared for identical saved CSV hashes in `results/reproducibility_check.json`.
- macOS: setup commands are provided; the full study was executed locally on Linux. Repository CI can verify saved artifacts on macOS, but is not a claim of full-model macOS execution.

All reported metrics come from saved predictions. Uncertainty is conditional and approximate; the source lacks historical publication vintages. No causal, subscriber-rate, employer-impact or savings claim is supported.
