# Executed experiment record

Date: **2026-11-23**. Environment: Linux x86_64, Python **3.12.14**. Direct plus transitive study dependencies are frozen in `requirements-lock.txt` (51 packages); actual study environment in `results/environment.txt`. No macOS model training is claimed.

## Protocol and inputs

Before test evaluation, `protocol.json` fixed the hypothesis, primary 20% comparison, four-candidate search, source sampling and profile boundaries, excluded post-assignment fields, 500-replicate conditional uncertainty and estimator/capacity sensitivity. SHA256: `365a9eca6a2b2bebbb9f904106aae209d9827214556b28c5bef0f781d44ce3e4`.

Pinned publisher Criteo v2.1 revision and input SHA256 are in `results/source.json`; the digest matches the publisher's LFS metadata. Full 13,979,592-row source scanned to form 699,450 observed sampled rows. Three partitions have 350,077 / 139,250 / 210,123 rows, with zero cross-boundary profile overlap. There were no external employer inputs, simulated observations or fabricated dates.

## Actual execution evidence

- Executed the complete `run.py` workflow twice on the same verified input: four outcome-model pairs plus one assignment diagnostic fit in each full run. The final recorded run took **157.9 seconds** on this host, excluding initial download/full CSV scan; the first source-scan run took 202.3 seconds. Runtime is hardware-dependent.
- All **11 decompressed CSV tables** in the first-versus-repeat comparison were byte-identical, including holdout predictions, split IDs, selection, policy values, conditional intervals and sensitivity. See `results/reproduction.json` for both SHA256s. Gzip container timestamps are deliberately excluded from this semantic comparison.
- Separately refitted the selected treated/control pair; maximum absolute difference from stored rounded uplift predictions was **4.9996e-11**, below **1e-9** tolerance. `verify_refit.py` reproduces that check, the full-record duplicate audit and frozen DR comparisons; evidence in `results/replication.json`.
- Executed all **seven explanatory notebook code cells**, with actual tables, recomputed metrics and image outputs saved in `analysis.ipynb`. Host kernel socket restrictions prevented nbclient startup; real sequential **in-process IPython** execution with captured rich outputs was used and recorded in notebook metadata. This is actual cell execution, not fabricated output or full model training hidden in a notebook display step.
- **11 scientific integrity tests** verify profile isolation, source/protocol identity, validation selection, outcome-blind capacity, metric algebra, paired policy values, finite reproducible multiplier intervals, support, executed cells and DR sensitivity recomputation. Actual output in `results/test_output.txt`.
- Five scientific PNGs were visually inspected; the final labels include test n, source scope, units, baseline, hypothetical capacity and conditional uncertainty where relevant. Exact source tables and mappings are in `results/FIGURES.md`.

The Linux/macOS GitHub workflow runs frozen-output integrity checks rather than full fitting. Its actual run status must be checked on the release PR; this document does not substitute local evidence for a remote check. No negative result was dropped. Original-population ITT, individual causal effects, temporal transport and telecom business outcomes remain unestablished.
