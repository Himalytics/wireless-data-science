# Public source catalogue

This catalogue supplies starting points. Recheck the current source, licence, access, fields, data grain, and method suitability before each build. Do not treat a proposed future source as already downloaded or analysed.

| Source | Appropriate uses | Important limit |
|---|---|---|
| [UCI Iranian Churn, ID 563](https://archive.ics.uci.edu/dataset/563/iranian+churn+dataset) | Classification and probability evaluation | CC BY 4.0; one telecom sample with an aggregated feature/label gap, not rolling dated customer snapshots |
| [FCC consumer complaints](https://catalog.data.gov/dataset/cgb-consumer-complaints-data) | Dated complaint-count forecasting and descriptive signals | Public government source; self-selected, unverified reports; no subscriber denominator or linked churn outcomes |
| [Ookla public network tiles](https://github.com/teamookla/ookla-open-data) | Geographic network-experience analysis | Aggregated geography, selection and weighting concerns; verify current licence/attribution and quarterly source version |
| [U.S. Census data](https://www.census.gov/data/developers.html) | Geographic population/context covariates | Validate geography, vintage, estimates, and margins of error; aggregate context is not individual behavior |
| [Criteo Uplift, official dataset](https://huggingface.co/datasets/criteo/criteo-uplift) | Experiment and uplift-method demonstrations | Dataset card lists CC BY-NC-SA 4.0; verify terms, assignment/outcome definitions, and eligible predictors; advertising results are not telecom retention effects |
| [UCI Online Retail, ID 352](https://archive.ics.uci.edu/dataset/352/online+retail) | Repeat-purchase/value and recommendation methods | CC BY 4.0; actual UK retail transactions; handle cancellations/returns and customer-selection issues; not wireless transactions |

A review-text source for project 10 will be selected and verified before implementation. Do not fabricate narratives from structured FCC issue labels or assume access to an account-gated dataset.

Historical engineering dataset files and outputs remain in the archive. Their availability does not make them results of a new scientific study.
