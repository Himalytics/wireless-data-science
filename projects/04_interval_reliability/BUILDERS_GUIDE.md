# Builder's guide

## Two-hour entry path

| Minutes | Exercise |
|---|---|
| 0–20 | Read the data card and manifest. Reconcile daily totals with the distinct-ticket audit. Inspect the eight absent calendar days. |
| 20–40 | Create the environment and run the replay. Check that 54 target weeks appear for each horizon and method. |
| 40–60 | Trace one four-week record through the issue date, latest feature week, target and score availability. Repeat for the two-week-lag setting. |
| 60–80 | Calculate the 80% radius rank for 52 scores by hand. Find a miss in the predictions and reproduce its interval score. |
| 80–100 | Compare the development gain table, period results and paired block ranges. Explain why the same coverage can come with a worse score. |
| 100–120 | Write a decision for a workload review. Define what new evidence would change it. |

## Architecture and boundaries

`source.py` verifies licence/fields, aggregates through SoQL and compares grouped row totals with distinct IDs before saving the CSV. `protocol.json` fixes the temporal boundaries, method grid and metrics. `run.py` checks the hash, creates whole UTC Monday weeks, issues forecasts, scores intervals, selects gain on development outcomes and writes exact results and the two figures. `test_integrity.py` probes future perturbations, timing, exact support, selected configuration and numeric scoring. `notebook.py` executes the walkthrough with the same environment. `results/execution.json` records the runtime and chart identities.

An origin is a Monday, and the point center uses four fully finished weeks. Horizon four targets the week starting three Mondays later. An earlier forecast still in the queue cannot contribute a residual. The score target must have finished and passed any specified lag. The interval feedback update reads the earlier **issued** lower and upper endpoints, keeping the error signal tied to the actual decision. The gain selector leaves a three-week gap between the last eligible development target period and the first evaluated target date to protect the four-week issue boundary.

The center is deliberately held constant for interval comparisons. Changing it would confound point model gains with uncertainty gains. A static error quantile reveals how old calibration performs, rolling lets the residual sample change, and adaptive additionally changes the effective quantile after misses. A bounded adaptive method can recover slowly, overshoot, or widen without helping coverage. Do not treat clipping as the unmodified theorem.

## Five substantive study sessions

1. Rebuild one Monday issue by hand. Verify that perturbing all future observations leaves earlier bounds fixed. Introduce an off-by-one error in a local branch and observe the integrity test.
2. Replace the symmetric radius with separate directional residual quantiles. Choose settings using earlier outcomes and reserve a new period. Explain the changed interpretation of tail risk.
3. Compare 26-, 52- and 104-score windows in development, then use an independently set future evaluation slice. Record width, coverage and score before considering any improvement.
4. Archive new source vintages by download time. Measure when complete weeks stabilize and compare the replay with actual arrivals. Treat a fixed lag as an assumption until the observed vintages support it.
5. Compare circular and noncircular blocks, and plot residual autocorrelation by horizon. Explain how boundary wraparound and a limited number of independent periods constrain inference.

## Pitfalls and interview defense

If a live refresh changes the hash or exact counts, use the committed snapshot to reproduce the release. Verify the licence and revision, then treat updated data as a new run. Confirm UTC parsing and Monday bins before comparing totals. A width of zero or an out-of-range rank should trigger a configuration check. Overlapping horizons do not create independent observations.

**Why can the narrower reference win the score with worse coverage?** The score balances distance of misses and width on every week. Some missed points are close to the boundary, and widening every interval has a cost in the score.

**Why not present 80% as a guarantee?** The historical residuals are serially dependent and change over time. Calibration is evaluated empirically on this snapshot, and the bounded update differs from the original theoretical setup.

**What changes the operational decision?** Prospective vintage tests, an explicit upper-miss tolerance and a separate measurement of the business consequences of too-wide or too-narrow ranges. FCC report counts alone cannot measure those consequences.
