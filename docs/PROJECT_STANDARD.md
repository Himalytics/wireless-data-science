# Project standard

## Purpose and scope

Build a progressive applied Data Science portfolio around retail wireless questions: prediction, forecasting, statistical uncertainty, experiment analysis and defensible product decisions. When a method requires a suitable public dataset from another industry, identify that domain explicitly and keep the result within its source population.

Each project must introduce a named technique and demonstrate at least three relevant scientific practices. Examples include nested or grouped validation, temporal backtesting, calibration, uncertainty estimation, sensitivity analysis, causal identification, experiment analysis, supported error analysis and robustness under distribution shift. Choose methods that answer the question rather than adding infrastructure to increase the tool count.

## Data and claims

Use observed public data with an authoritative source, licence and attribution, an automated download method, a reproducible input identity, a clear unit of analysis and documented sampling/timing limits. Verify source suitability before implementation. Never invent dates, linked subscribers, treatment histories or business outcomes.

Simulated experiments and hypothetical economics may augment observed data only when labelled in code, tables and findings. They cannot substitute for unavailable evidence. Use no employer data, internal code, dashboards, customer records or proprietary designs. An independent source-sample result does not establish employer impact or transfer to current U.S. wireless subscribers.

## Required scientific package

| Component | Required evidence |
|---|---|
| Question | Target, prediction/evaluation horizon, unit of analysis, prespecified hypothesis and intended decision |
| Source | Dataset card, licence, provenance, automated ingestion, checksum/version and quality audit |
| Analysis | Reproducible exploration, justified baselines/models, appropriate evaluation design and error analysis |
| Integrity | Training boundaries, saved split/configuration, relevant checks and actual execution evidence |
| Results | Measured metrics, support counts, uncertainty, sensitivity and a decision-focused report |
| Figures | Scientific plots, exact underlying chart data, captions/scope and provenance |
| Explanation | Executed notebook, Mac run instructions, dataset/model cards and a detailed builder's guide |
| Ownership | A two-hour entry walkthrough, deeper extensions and an exercise changing a substantive scientific choice |

Use [the scientific standard](SCIENTIFIC_STANDARD.md) as the release gate and [the roadmap](ROADMAP.md) for progression. A negative or inconclusive comparison remains a valid finding. A high score does not establish causal impact, external validity or production readiness.

## Repository conventions

Keep each project self-contained under `projects/NN_short_name/`, with its code, requirements, notebook, cards, findings, tests, results and figures together. Keep series-wide standards in `docs/`, verified source starting points in `sources/`, and reusable scientific report structures in `templates/`.

Version scientific source and reproducibility evidence. Ignore local environments, downloaded raw inputs, caches and fitted-model binaries. Use explicit paths and predictable entry commands. Preserve previous experiment results when extending a study; do not silently overwrite a locked protocol after inspecting its test set.

Maintain [STATE.json](STATE.json) only after the corresponding study and checks have run. Future roadmap sources remain feasibility gates until their access, licence, fields and evaluation suitability are verified.
