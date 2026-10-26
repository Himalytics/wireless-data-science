# Experiment record · October 26, 2026

- Protocol: `experiment_plan.json`, SHA-256 `b30cbdddc0ef24d470678fd913b8ac16dec29051be127b7bc0602af447ee9add`. Written before model evaluation; a local protocol, not an independently registered study.
- Source ZIP: `696c3a1812267980751f30d19193a1b430ac4ad76172bb089e664c96813ead66`; observed public input, all 3,150 source rows retained.
- Execution UTC: `2026-10-26T21:17:23.926673+00:00`.
- Runtime: 51.253 seconds for the full study in this environment, excluding installation/notebook/figures.
- Python 3.12.14; NumPy 2.3.5; pandas 2.2.3; scikit-learn 1.8.0; SciPy 1.17.0. OS: Linux. Thread defaults are constrained to one where not already configured.
- Seeds: split/model 42; profile-cluster bootstrap 20261026. Bootstrap iterations: 500.
- Split: 2,511 development / 639 test; zero conservative-profile overlap. Three outer development folds, three calibration folds per outer training set, three inner tuning folds per calibration-training set. All group-aware.
- Search: logistic 3 configurations × inner 3 folds; boosting 4 configurations × inner 3 folds. Four feature/model specifications are evaluated. There are 48 tuned submodels across outer and final fits (216 inner fits for logistic + 288 for boosting, plus 48 refits). Sigmoid calibration adds its held-out calibration fits. No final-test tuning.
- Selection record: `results/selection_locked_before_test.json`, timestamp before final fitting/test scoring. Selected `conservative_gradient_boosting` by development-only pooled OOF Brier.
- Primary result: AP 0.9298, Brier 0.03721. Negative finding: matched raw ensemble Brier 0.03608, slightly better than sigmoid-calibrated Brier.
- Artifact inventory: source/protocol audit; row-level split assignments; development OOF and test predictions; fitted-submodel trace; metric/uncertainty/queue/cost/slice tables; chart data and hashes; locally saved selected model; explanatory executed notebook; reproducible charts.
- Integrity verification: six tests passed. Notebook executed successfully; scientific figure inspection is documented in the release. Mac instructions and a Linux/macOS CI matrix are supplied; local execution is not macOS evidence.
- Deviations: no change to primary candidates, selection rule, feature eligibility, split seed or evaluation method after test evaluation. The raw/calibrated comparison is a prespecified diagnostic, not a post-hoc model replacement. No dates, subscribers, treatment assignments or business impact were invented.

The experiment informs source-sample prediction and follow-up design. It does not establish retention effectiveness or cross-market generalization.
