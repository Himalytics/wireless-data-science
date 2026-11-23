# Twelve-project Data Science roadmap

The series started October 26, 2026. Reconciled November 23: projects 1, 2 and 4 were already integrated on main; project 3 was evaluated November 9 and remains in [its separate draft review](https://github.com/Himalytics/wireless-data-science/pull/2). This release adds evaluated project 5 without duplicating or renumbering that pending study. Next new study: project 6 on November 30. Each release must stand on observed data and a defensible scientific question. Future sources remain feasibility gates until access, licence, fields and suitability have been checked.

| Project | Planned date | Scientific question | Main technique and evidence |
|---|---|---|---|
| 1 | Oct 26, 2026 (built) | Can we trust telecom churn-risk probabilities? | UCI Iranian Churn; nested model comparison, calibration, uncertainty, feature-availability sensitivity, capacity/cost assumptions |
| [2](../projects/02_complaint_forecasting/README.md) | Nov 2, 2026 (built) | How predictable are telecom complaint volumes? | Observed FCC wireless phone reports; direct multi-horizon count forecasting, rolling-origin residual intervals, block-bootstrap uncertainty; negative ML result retained |
| [3](https://github.com/Himalytics/wireless-data-science/pull/2) | Nov 9 (evaluated; separate review pending) | Which markets have distinct network-experience profiles? | Ookla/Census profiles, stability and replication; not integrated on main |
| [4](../projects/04_interval_reliability/README.md) | Nov 16 (evaluated; main) | When do forecast uncertainty intervals fail? | Real FCC periods; rolling/adaptive interval calibration, coverage, width and horizon sensitivity |
| [5](../projects/05_uplift_policy/README.md) | Nov 23 (evaluated; current release) | Does uplift beat random and response policies at a fixed capacity? | Criteo v2.1; grouped selection/test, IPW/DR evaluation, profile uncertainty and sensitivity; non-telecom privacy-altered benchmark only |
| 6 | Nov 30 | How confidently can we evaluate an experiment? | Suitable real randomized data; effect estimates, precision, heterogeneity, and multiple-comparison discipline; no invented event ordering or pre-period fields |
| 7 | Dec 7 | Can repeat purchases and future customer value be forecast? | UCI Online Retail; probabilistic repeat-purchase/value models, temporal holdout, returns/wholesale sensitivity; explicitly retail-method transfer |
| 8 | Dec 14 | Does a recommender beat popularity without leakage? | Observed transaction interactions; temporal ranking evaluation, cold-start analysis, coverage, uncertainty |
| 9 | Dec 21 | Which factors predict geographic network experience? | Real Ookla/Census data; spatially blocked validation, weighted models, error analysis, ecological-inference limits |
| 10 | Dec 28 | What can review text reliably reveal about dissatisfaction? | A verified public review dataset; classical NLP versus a justified alternative, error taxonomy, calibration, domain limits |
| 11 | Jan 4, 2027 | When should a model abstain under distribution shift? | Real held-out domains or periods; confidence/coverage trade-offs, robustness and selective prediction |
| 12 | Jan 11 | Which conclusions are strong enough for a product decision? | A decision-facing capstone integrating validated analyses, uncertainty, evidence gaps, and a proposed follow-up study |

The portfolio may reuse a dataset for a materially different scientific question. It must not repeat a model tutorial with different styling. Each project introduces a named technique, at least three relevant scientific practices, and an ownership exercise.

Public non-telecom experiments or transaction data can teach methods relevant to wireless product decisions. Their measured outcomes remain outcomes of the source domain. Do not label them as carrier retention, wireless purchases, or employer results.

Do not force incompatible datasets into a single customer-level model. In particular, Iranian churn records, U.S. complaint reports, and aggregate network tiles do not share verified subscriber identities. The capstone may present separate evidence streams rather than fabricate a join.
