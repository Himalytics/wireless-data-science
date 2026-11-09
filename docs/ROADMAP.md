# Twelve-project Data Science roadmap

The series started October 26, 2026. Projects 1-3 were built and evaluated October 26, November 2 and November 9, 2026. The next scheduled build is project 4 on November 16, 2026. Each release must stand on observed data and a defensible scientific question. Future sources remain feasibility gates until their access, licence, fields, and evaluation suitability have been checked.

| Project | Planned date | Scientific question | Main technique and evidence |
|---|---|---|---|
| 1 | Oct 26, 2026 (built) | Can we trust telecom churn-risk probabilities? | UCI Iranian Churn; nested model comparison, calibration, uncertainty, feature-availability sensitivity, capacity/cost assumptions |
| [2](../projects/02_complaint_forecasting/README.md) | Nov 2, 2026 (built) | How predictable are telecom complaint volumes? | Observed FCC wireless phone reports; direct multi-horizon count forecasting, rolling-origin residual intervals, block-bootstrap uncertainty; negative ML result retained |
| [3](../projects/03_network_profiles/README.md) | Nov 9, 2026 (built) | Which observed county network profiles are stable enough to describe? | Ookla mobile 2025 Q4/2026 Q1 with Census 2024 context; conditional bootstrap clustering stability, weighting sensitivity, frozen temporal transfer and sampling limits |
| 4 | Nov 16 | When do forecast uncertainty intervals fail? | Real FCC time periods; conformal or other justified interval methods, coverage by period/group, shift sensitivity |
| 5 | Nov 23 | Which customers respond because of a campaign? | Public randomized Criteo Uplift data; treatment-effect modelling, baseline policy comparison, uncertainty; explicitly a non-telecom method demonstration |
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
