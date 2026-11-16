# Experiment record

- Run date: November 16, 2026. Linux with Python and package versions recorded by the execution and dependency files.
- Scientific question and selection rule: `protocol.json`. The historical target window was already partially described in Project 2, so development/evaluation timing is enforced in code without calling it a new untouched study period.
- Data retrieval: authoritative FCC JSON aggregate and distinct-ID audit verified. Snapshot and metadata identities are in `data/source_manifest.json`.
- Fixed model grid: three gains, fixed 52-score window, one frozen reference, one rolling reference. Each of two horizons replayed with delayed outcome resolution. Both sensitivity analyses reuse the selected gain.
- Evidence: 324 primary interval predictions, plus development candidate scores, paired block draws summarized by horizon, period and sensitivity tables, point baseline MAE and two scientific charts with exact data and digests.
- Validation: execute `python run.py`, `python -m unittest -v` and `python notebook.py`. Tests cover time boundaries, perturbations, pairing, counts, score arithmetic, gain selection and figure identity.
- A second full replay reproduced the prediction CSV byte for byte (SHA-256 `61199c70ec7578f191ee3b563a6dc74f336049be392ba48f69b7a3a15f9fd615`). Five tests passed and all five notebook code cells executed.
- Full replay executed on Linux. macOS commands are provided for reproduction.
