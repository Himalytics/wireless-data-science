# Builder's guide: defending a negative ML result

## What you built

You are evaluating a forecast system, not merely fitting a regression to a dated CSV. The system has an explicit origin, information set, forecast horizon, model-selection period, final sequential evaluation and separate uncertainty evaluation. Its output is a forecast of submitted FCC report counts. The product decision is whether extra model complexity is justified for a prospective workload study.

The new technique is **direct multi-horizon count forecasting with rolling-origin residual distributions**. At each origin, four different models predict weeks one, two, three and four ahead. This differs from recursively predicting a week, feeding that prediction back as an observation, and repeating. Direct models avoid that feedback chain, but each horizon has fewer eligible training labels and its own estimation error. That is a trade-off, not an automatic improvement.

The substantive result is a negative one: useful baselines can be difficult to beat, and forecast intervals must earn their nominal coverage. A defensible explanation includes why the experiment could have selected ML, what was frozen before final scoring, and what uncertainty prevents you from claiming.

## Two-hour entry path

| Time | Task | Evidence you should be able to explain |
|---|---|---|
| 0-15 minutes | Read README and DATA_CARD; inspect source manifest | Observed unit, target, licence, source identity, no subscriber denominator |
| 15-30 | Open history and issue counts | Why a complaint forecast can be dominated by Unwanted Calls |
| 30-50 | Reproduce with `python study.py --snapshot` | Input hash, actual model fits, saved predictions, environment |
| 50-70 | Walk through `features` and training trace | Exactly why a future target cannot enter an origin's training |
| 70-90 | Recalculate MAE and interval coverage from predictions | Difference between point error, width, coverage and interval score |
| 90-105 | Read sensitivity and conditional bootstrap interval | Dependence, limited support, target definition and non-universal results |
| 105-120 | Explain a decision aloud; choose an ownership experiment | What to retain, what to measure next, and what is not supported |

## Scientific flow and responsibilities

1. `experiment_plan.json` declares target, periods, candidates and metrics. `PROTOCOL_AMENDMENT.md` documents the source-date correction. The code saves the plan hash with selection and execution evidence.
2. `download_data.py` queries the authoritative FCC API for daily issue counts, distinct-ID checks, missing timestamp count and date disagreement count. It retries transient access failures, checks the licence and hashes response bytes. A manifest marks a completed source download.
3. `study.load_data` verifies source identities and aggregate conservation, reconstructs a complete UTC calendar and sums into Monday-Sunday weeks. It records the zero-day assumption instead of silently dropping gaps.
4. `study.features` builds origin-safe lag and rolling summaries with known calendar terms. `run_series` performs the expanding-window fits and creates four horizon-specific forecasts at each origin.
5. `run_series` scores only development targets to lock selection, then evaluates final target weeks sequentially. It uses already observed earlier final weeks for later-origin fits, as a real updating system would, without retuning hyperparameters.
6. `study.interval` collects only errors whose target dates are already observed. `score` evaluates point and interval properties separately. `paired_bootstrap` preserves horizon dependence within an origin and approximate serial dependence across nearby origins.
7. The script repeats the frozen design excluding Unwanted Calls and saves exact predictions, counts, metrics and training traces. It does not swap in a sensitivity winner after looking at final results.
8. `build_figures.py` renders scientific plots from those saved tables and hashes the CSV figure sources. `execute_notebook.py` executes the explanatory Python cells in-process and captures tables and figures. The notebook reads the executed model study's outputs; it does not claim its cells retrain the entire experiment.
9. Eight integrity tests check source conservation, feature perturbation, training/calibration boundaries, non-overlapping final targets, development-only selection, independent metric calculation, interval arithmetic and figure identity.

## Data audit: the important choices

### Why use submission time?

A forecast must be defined around when information becomes observable. The source documents `ticket_created` as submission time. The consumer's alleged incident time is a different concept and may be retrospectively reported. The undescribed `date_created` field disagrees with the submission timestamp's UTC day for 118,111 final-scope records. The audit amendment chooses the documented timestamp and UTC explicitly.

That still does not solve publication availability. A ticket may be added to the open database later or revised. The extract lacks historical vintages. So the correct claim is 'historical backtest on a current source snapshot with protected model-training boundaries'. It is not a certified replay of everything publicly available on each historical Monday. This distinction is central to defending the work.

### Why aggregate at the source?

The forecasting question needs counts, not phone numbers or addresses. SoQL performs day/issue grouping before download. `count(*)` and `count(distinct id)` agree within groups and across the selected scope. That detects repeated ticket IDs in this scope; it does not prove that every report describes a unique incident or customer.

The release commits an anonymous aggregate with an exact hash so it can be rerun after the live source changes. API JSON hashes document original retrieval bytes; the CSV snapshot has a different, separately recorded hash. Do not confuse source-version identity with a URL that always returns the newest data.

### Why retain zero days and Unwanted Calls?

Eight calendar days have no selected rows. Reindexing them to zero preserves a regular modelling calendar, but absence is not proof of zero actual submissions. This is a documented assumption and a reason for a future source-availability study.

The primary question covers all selected wireless phone reports, so all issue categories are retained. Removing Unwanted Calls changes the target. It is useful as a sensitivity because those reports form 61.64% of the historical sample, but it is not a hidden filter designed to improve metrics. The filtered target may still contain other reporting phenomena and should not be relabelled 'verified service failures'.

## Feature construction and leakage boundaries

Let t be the first target week's index and h the horizon in weeks. At origin t, only observations with index less than t are available.

- A one-week lag is y[t-1], not y[t]. A four-week mean uses y[t-4:t], whose right endpoint is excluded by Python slicing.
- Each supervised training row starts at index u and predicts y[u+h-1]. It is eligible only when u+h-1 is less than t. The code constructs this boundary explicitly and asserts it.
- Annual Fourier terms use the known target calendar: sine/cosine at the first and second annual harmonics. Future calendar values are known and are not leakage.
- The ridge scaler is inside the pipeline fitted at each origin. No full-history scaling, random train/test split, target-based feature screening or random early-stopping validation is used.
- For intervals, an earlier origin's residual is eligible only if its actual target week precedes the current origin. An earlier forecast date alone is insufficient: its fourth-week outcome may not yet exist.

The feature-perturbation test replaces every observation from a chosen origin forward with an extreme value. That origin's features must stay identical. This test checks a scientific property rather than mirroring one implementation line.

## Why these model choices?

The recent four-week mean is a useful operational question: does knowing the current level already solve most of the task? It reacts to level changes faster than an annual repeat but smooths isolated shocks. Its four horizon forecasts are identical, so it cannot anticipate a trend within a batch.

The 52-week seasonal naive checks whether annual repetition is sufficient. A 52-week lag is a convenient weekly seasonal benchmark, not a perfect alignment of holidays or dates. A changing report process can make last year's level irrelevant.

Ridge adds regularized relationships between lagged levels, variation and seasonality. Log1p handles nonnegative counts and zero values. Exponentiation without smearing correction is not an unbiased mean estimate. Its strong negative bias is reported rather than silently corrected after final scoring.

Poisson gradient boosting estimates a nonnegative count mean with nonlinear interactions. The objective can be used even when observed counts are overdispersed; it does not license Poisson-distributed prediction intervals. Two leaf budgets are tried, with fixed learning rate, iterations, regularization and seed. The modest sample size and annual features make unrestricted nonlinear search difficult to defend.

The search budget is deliberately finite. Trying dozens of models after final evaluation and reporting the best would turn the test set into development data. If you explore another training window, record a new experiment and reserve a genuinely later evaluation period.

## How to explain the metrics

MAE is the average absolute difference between a predicted and observed weekly complaint total. It has workload units and is the locked primary selection criterion. It weights a 1,000-complaint miss ten times as much as a 100-complaint miss.

WAPE is total absolute error divided by total observed complaints in the evaluation window. A 16.6% WAPE means errors sum to 16.6% of that observed report volume. It is not an error per subscriber or a percentage of customers. It is not identical to the mean of individual weekly percentage errors.

Bias is prediction minus actual. A negative value means underforecasting on average. RMSE emphasizes large misses more strongly than MAE. Neither identifies what caused those misses.

Coverage asks how often an observed count lies inside its stated interval. Width measures the range's size. An interval can cover more simply by becoming unhelpfully wide. The 80% interval score combines width with a penalty of 10 times any amount an actual value falls outside the interval. Lower is better. It makes coverage and sharpness a trade-off.

The main residual interval is nominal, not guaranteed. Its 10th/90th percentiles come from 26 previous eligible errors at the same horizon. A minimum 13 errors avoids presenting two residuals as a meaningful distribution. Residuals are signed, so the interval can be shifted relative to the point forecast; do not redraw it symmetrically for aesthetics.

## What the findings mean

The recent-average baseline's final MAE is 783.6 versus 1,062.5 for the development-selected ML challenger. The latter is 35.6% larger. Both were evaluated on the same 52 target weeks. The aggregate finding alone does not imply a statistically established universal ranking.

There are 13 forecast origins, not 52 independent experiments. Paired circular moving-block resampling keeps four horizons together and resamples three adjacent origins at a time. Its approximate conditional 95% interval for ML-minus-baseline MAE is [-195.6, 787.0]. Because zero is inside, avoid claiming definitive superiority beyond this observed comparison. The data also fail to demonstrate an ML benefit.

Nominal 80% intervals covered only 36 of 52 outcomes for the baseline and 29 for boosting. This is operationally material. Forecast point quality and interval credibility are different release decisions. Undercoverage could reflect changing error distributions, dependence, source processing or other omissions; the experiment does not causally identify a mechanism.

The filtered sensitivity retains the point-accuracy ordering, but boosting has a better interval score despite worse coverage. That is an excellent interview discussion: no single percentage captures every aspect of a probabilistic forecast. You preserve the qualification because the evidence requires it.

## Product decision and prospective experiment

Keep the recent-average system as the reference for a prospective shadow evaluation. Do not present the tested boosting model as a justified deployment improvement. Collect fresh source snapshots so publication lag and revisions become measurable. Evaluate MAE, bias, interval score, width and coverage by horizon on later weeks.

A count of FCC reports is not staffing demand until you know which reports enter an operational queue, handling times, routing and service-level goals. This public project does not have those records. A product recommendation can identify the required next evidence without inventing savings.

## Daily study and ownership experiments

Day 1: reproduce the snapshot, explain the target and manually calculate one origin's lag/mean features. Day 2: trace one horizon's eligible training labels and reconstruct an empirical interval. Day 3: independently recompute all final metrics from predictions and explain why the interval score can disagree with coverage. Day 4: inspect the period and high-volume slices, keeping their small support counts visible. Day 5: implement one extension in a separate experiment directory with a preserved release and a written evaluation plan.

Substantive extensions:

- Compare expanding history with a trailing 104-week training window to study adaptation versus variance. Choose settings using development only.
- Compare fixed residual windows with alternative interval methods on a new evaluation period. Analyze conditional coverage rather than optimizing aggregate coverage alone.
- Save prospective weekly source snapshots, then quantify how revisions alter historical totals and forecasts.
- Study issue-level forecasts and reconciliation only after verifying stable issue labels and adequate per-series support.
- Test multiple block lengths for uncertainty sensitivity, explaining the bias/variance trade-off with only 13 origins.

## Common failures

| Symptom | Likely cause and remedy |
|---|---|
| Live API timeout or rate limiting | Use the committed snapshot for this release; retry source access later rather than inventing replacement data |
| Hash assertion fails after refresh | A source/cache file changed or a download is partial; preserve the release and complete a fresh audited download |
| Package installation fails | Confirm Python 3.12 and activate the project environment; upgrade pip before installing pinned requirements |
| Feature array contains future counts | Review origin indexing and right-exclusive rolling slices; run the perturbation test |
| Calibration has fewer than 13 residuals | Early origins deliberately have no interval; development/final scoring begins after warmup |
| Notebook kernel cannot open network ports | The companion executes Python cells in-process; no TCP kernel is needed |
| Fresh rerun changes results | The public source can revise history; use `--snapshot` to reproduce the committed input exactly |
| Coverage appears precise | Check support: 13 outcomes per horizon gives 7.7-point coverage increments |

## Interview defense

**Why did you build ML when the mean won?** The question was empirical. I implemented plausible alternatives under the same information boundaries, selected before final evaluation, and kept the negative result. Complexity must earn a measurable benefit.

**What is the most serious leakage risk?** Beyond ordinary future-feature leakage, historical source vintages are missing. My fit boundaries are verified, but I qualify the backtest as using a current snapshot. A prospective snapshot archive is the next step.

**Why not a random split?** Nearby weeks share levels and serial dependence. Random splits mix future regimes into training and answer a different question from forecasting unseen later weeks.

**Why not claim a statistically significant win?** The paired conditional interval crosses zero, and only 13 origins support the comparison. The observed ranking is clear, while general superiority remains uncertain.

**What would change your recommendation?** A development-chosen method that beats the frozen baseline on a later prospective period, with acceptable horizon-level interval performance and demonstrated source availability. No result here measures customer retention, carrier quality or business savings.
