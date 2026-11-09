# Segmentation model card

## Question and scope

Descriptive county network-experience profiles on observed Colorado mobile-test tiles. This is unsupervised ML, with no ground-truth market-segment labels. It does not estimate customer outcomes, coverage or causal network quality. Intended use is research and planning a follow-up measurement study.

## Model and selection

Development counties need at least five tiles and 25 tests in 2025 Q4. The three features are test-weighted download Mbps, upload Mbps and latency ms. Log1p and StandardScaler fit on development counties only. Census density is excluded from features.

K-means uses 30 initializations and seed 20261109. Candidates K=2,3,4,5 are evaluated using development silhouette, with at least five counties per cluster. K=2 is the only candidate meeting that support gate: silhouette 0.420, 14/37 counties. A threshold of 0.25 is a prespecified interpretability gate, not a proof of true natural groups. The one-profile reference reports dispersion; its silhouette is undefined. Training inertia is not a predictive holdout score.

Readable labels 0/1 sort clusters by increasing download centroid. The locked selection file records scaler means/scales, centroids, features and protocol hash before replication. No K selection or preprocessing uses 2026 Q1.

## Uncertainty, sensitivity and transfer

Two hundred bootstrap replicates resample tiles independently within each eligible development county, recompute summaries and refit preprocessing and K-means at fixed K. Original county eligibility is fixed. Hungarian maximum-overlap alignment supports county membership frequencies; ARI compares partitions independently of numeric label permutations.

The bootstrap is conditional on observed tiles and modelling choices. It ignores spatial dependence, raw within-tile test variability, source revisions and selection of unobserved places. It is not a population uncertainty estimate. Median ARI is 0.631; conditional central 95% replicate range is [0.357,0.918]. Twelve counties have membership frequency below 80%.

Equal-tile aggregation retains 44/51 primary labels (ARI 0.508). Restricting to tiles with five or more tests retains 21/23 labels (ARI 0.547), on a smaller support set. Both use the primary frozen scaler and centroids. Ward hierarchical clustering on the same standardized development matrix has ARI 0.843 against the primary model; it is a same-sample method comparison.

Frozen 2026 Q1 transfer retains 36/43 labels, ARI 0.395. Profile 0 retains 6/12 and profile 1 retains 30/31. Matching tile identities first retains 26/31 labels, ARI 0.164, with 3,294 shared tiles. These are descriptive stability measures, not supervised accuracy or evidence about identical subscribers.

## Decision and failure modes

Treat stable profiles as hypotheses for further measurement. Flag unstable and unsupported counties. The smaller profile's movement and weighting sensitivity argue against hard market tags. Sparse samples, high-volume test locations, source reaggregation, device/network mixtures, within-county heterogeneity and generalized boundaries can change assignments. Check spatial-block stability and later quarters before a consequential deployment.

All numerical findings belong to the observed source sample. This project does not support carrier ranking, resident coverage percentages, churn effects or employer outcomes.
