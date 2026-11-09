# Executed experiment record

- Analysis date: November 9, 2026.
- Development: 2025 Q4 Ookla mobile tiles; replication: 2026 Q1. Census boundaries and population context: 2024 vintage.
- Sources: full source hashes, URLs, retrieval metadata and exact committed-subset hashes in `results/source_manifest.json`.
- Unit and exclusions: tile centroids assigned to Colorado counties; invalid metrics and out-of-interior centroids excluded and counted. Five-tile/25-test support gate gives 51 development counties and 45 later counties.
- Protocol: `experiment_plan.json`; hash stored with selection. K candidates 2,3,4,5, 30 initializations, minimum five counties per cluster. No replication data select K or preprocessing.
- Selected model: K=2, silhouette 0.419799, sizes 14/37. Log1p network features and development StandardScaler; density is context only.
- Resampling: 200 within-county tile bootstraps, refit scaler and K at fixed selected K, Hungarian alignment, conditional ARI and membership frequency.
- Other evidence: single-profile reference; Ward clustering; equal-tile and minimum-test-tile aggregation with frozen primary model; frozen temporal and matched-tile assignments.
- Execution: full study ran on Linux/Python 3.12.14 in approximately 15 seconds excluding installation and ingestion. Exact environment and elapsed time in `results/execution.json`.
- Verification: eight scientific integrity tests; executed explanatory notebook; six visually inspected scientific figures and exact CSV data; a complete repeated fit compared for identical CSV hashes in `results/reproducibility_check.json`.
- macOS: installation/run commands provided. Local full-model macOS execution is not claimed. Hosted integrity checks are distinct from training the entire model on macOS.
- Interpretation: conditional source-sample segmentation. No population coverage, carrier ranking, causal effect, churn or employer outcome is measured.

Preserve this protocol, source subset and results when exploring extensions. A changed support threshold, spatial bootstrap or feature definition requires a new experiment and later evaluation evidence.
