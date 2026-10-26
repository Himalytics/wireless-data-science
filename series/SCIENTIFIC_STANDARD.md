# Scientific release standard

## Question and data

- Define the business question, target/outcome, unit of analysis, prediction or evaluation horizon, and intended decision before modelling.
- Separate prespecified hypotheses from exploratory findings. Define primary metrics and comparisons before using the final test set.
- Verify source, licence, provenance, schema, selection process, and availability of predictors at decision time. Record exclusions and their rationale.
- Check duplicates, missingness, target prevalence, implausible values, and observational dependence. Document source limitations and domain mismatch.

## Modelling and validation

- Include a no-skill/business baseline and a justified simple statistical model before more complex alternatives.
- Fit preprocessing, feature selection, imbalance handling, tuning, and calibration inside the appropriate training folds. Never fit them to the full dataset before evaluation.
- Keep an untouched final test set when appropriate. Use grouped/temporal splits only when genuine group/time information supports them; never invent an ordering to claim temporal validation.
- Use nested evaluation or a justified alternative for model selection. Report the search budget and reproducible seeds. Do not treat dependent fold scores as independent experimental observations.
- Report metrics appropriate to the target, class balance, and decision. Ranking, probability accuracy, and a thresholded decision are distinct evaluation questions.
- Quantify uncertainty with a method whose assumptions match the sampling/validation design. State what the interval covers and what it does not.

## Interpretation and robustness

- Include ablations or sensitivity checks that could change the conclusion, along with error/subgroup analysis and support counts.
- Do not interpret feature importance or SHAP values as causal effects. Avoid causal language for predictive associations.
- Causal/uplift projects require an identifiable treatment, appropriate outcome, assumptions, overlap/assignment checks, and an honest evaluation plan. Never invent a retention effect from an ordinary churn dataset.
- Forecasting uses real dates, rolling-origin backtests, simple seasonal/naive baselines, and interval coverage or appropriate probabilistic scores. Complaint counts are not activation or churn rates.
- Reject or qualify unsupported claims. A negative or inconclusive result is a valid scientific outcome.

## Reproduction and release

- Save code, an explanatory notebook, input hashes/version, split definitions, configuration, measured metrics, and chart source data. Include Mac installation/run instructions.
- Execute the main workflow and checks for leakage boundaries, data integrity, metric calculation, and reproducibility. Do not claim execution on an environment that was not actually used.
- Write a findings/decision report and model card that separate empirical results from assumptions, recommendations, and limits.
- Visually inspect exported charts and carousel pages. Labels include scope, dates, units, baselines, and uncertainty where relevant.
- Follow the publication approval rule. A file being generated is not a LinkedIn publication.
