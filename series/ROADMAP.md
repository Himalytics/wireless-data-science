# Twelve-project Data Science roadmap

This is a new series starting at project 1. The first scheduled build is November 2, 2026. Each release must stand on observed data and a defensible scientific question. Future sources remain feasibility gates until their access, licence, fields, and evaluation suitability have been checked.

| Project | Planned date | Scientific question | Main technique and evidence |
|---|---|---|---|
| 1 | Nov 2 | Can we trust telecom churn-risk probabilities? | UCI Iranian Churn; nested model comparison, calibration, uncertainty, feature-availability sensitivity, capacity/cost assumptions |
| 2 | Nov 9 | How predictable are telecom complaint volumes? | Public FCC dated reports; rolling-origin probabilistic forecasting, seasonal baselines, interval coverage |
| 3 | Nov 16 | Which markets have distinct network-experience profiles? | Ookla/Census where a valid geographic/vintage join exists; stable clustering, sampling bias, segment interpretation |
| 4 | Nov 23 | When do forecast uncertainty intervals fail? | Real FCC time periods; conformal or other justified interval methods, coverage by period/group, shift sensitivity |
| 5 | Nov 30 | Which customers respond because of a campaign? | Public randomized Criteo Uplift data; treatment-effect modelling, baseline policy comparison, uncertainty; explicitly a non-telecom method demonstration |
| 6 | Dec 7 | How confidently can we evaluate an experiment? | Suitable real randomized data; effect estimates, precision, heterogeneity, and multiple-comparison discipline; no invented event ordering or pre-period fields |
| 7 | Dec 14 | Can repeat purchases and future customer value be forecast? | UCI Online Retail; probabilistic repeat-purchase/value models, temporal holdout, returns/wholesale sensitivity; explicitly retail-method transfer |
| 8 | Dec 21 | Does a recommender beat popularity without leakage? | Observed transaction interactions; temporal ranking evaluation, cold-start analysis, coverage, uncertainty |
| 9 | Dec 28 | Which factors predict geographic network experience? | Real Ookla/Census data; spatially blocked validation, weighted models, error analysis, ecological-inference limits |
| 10 | Jan 4, 2027 | What can review text reliably reveal about dissatisfaction? | A verified public review dataset; classical NLP versus a justified alternative, error taxonomy, calibration, domain limits |
| 11 | Jan 11 | When should a model abstain under distribution shift? | Real held-out domains or periods; confidence/coverage trade-offs, robustness and selective prediction |
| 12 | Jan 18 | Which conclusions are strong enough for a product decision? | A decision-facing capstone integrating validated analyses, uncertainty, evidence gaps, and a proposed follow-up study |

The portfolio may reuse a dataset for a materially different scientific question. It must not repeat a model tutorial with different styling. Each project introduces a named technique, at least three relevant scientific practices, and an ownership exercise.

Public non-telecom experiments or transaction data can teach methods relevant to wireless product decisions. Their measured outcomes remain outcomes of the source domain. Do not label them as carrier retention, wireless purchases, or employer results.

Do not force incompatible datasets into a single customer-level model. In particular, Iranian churn records, U.S. complaint reports, and aggregate network tiles do not share verified subscriber identities. The capstone may present separate evidence streams rather than fabricate a join.
