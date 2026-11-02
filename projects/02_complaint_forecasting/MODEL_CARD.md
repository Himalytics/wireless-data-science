# Forecast system card

## Intended question and use

Estimate the next four weekly FCC wireless phone complaint totals from prior observed totals. Intended use is a research comparison and prospective workload-monitoring reference. No production deployment, subscriber-risk scoring, carrier ranking or employer application is represented.

## Candidates and features

- Recent four-week average: same forecast for horizons 1-4.
- Seasonal naive: the observation 52 weeks before each target week.
- Ridge: standardized features, alpha 10, log1p count target, inverse transform with expm1 and clipping at zero. No lognormal smearing correction; the inverse-transformed forecast need not estimate an unbiased count mean.
- Histogram gradient boosting: Poisson loss, 100 trees/iterations, learning rate 0.05, L2 10, minimum leaf size 15, either 7 or 15 leaves, fixed seed, no random validation split or automatic early stopping.

Each learned candidate has four separate models, one per horizon. All learned candidates use the same 17 features: eight log-count lags; four log rolling means; one log rolling standard deviation; four target-calendar Fourier terms. Each origin refits from expanding historical training data, using only labels whose target week is earlier than the origin. Ridge scaling is fit on that training matrix.

The Poisson training objective allows nonnegative count-mean forecasts. No Poisson distribution is assumed for prediction intervals; overdispersion and unobserved drivers remain concerns. No demographic or employer features are used.

## Selection and evaluation

Choose the lowest pooled MAE on 104 development target weeks. Record the best ML challenger and practical baseline before scoring the final 52 weeks. Select the recent mean overall, and 15-leaf Poisson boosting as the ML challenger. Search budget: two fixed nonlinear configurations and one fixed ridge configuration, with no extra test-driven tuning.

Origins move in four-week steps; four targets per origin do not overlap. Historical labels can enter later-origin fits after observation, while hyperparameters and selection stay frozen. This is sequential evaluation, not an estimate from one model trained once and frozen for a year.

## Uncertainty

Per model and horizon, the preceding 26 available origin errors supply signed 10th/90th percentiles; at least 13 are required. Add them to the new point prediction and clip at zero. Historical residual targets must precede the origin. Neither exchangeability nor stationarity is guaranteed; nominal 80% coverage must be assessed empirically.

The paired ML-minus-baseline MAE interval uses 2,000 circular moving-block resamples of three adjacent origins, preserving four horizons together. It is conditional on the observed snapshot and frozen forecasts. Only 13 origins support the final comparison; model-fitting and source-revision uncertainty are excluded.

## Performance and limitations

Final MAE: recent mean 783.6, selected ML challenger 1,062.5 complaints/week. WAPE: 16.6% and 22.5%. Nominal 80% coverage: 69.2% and 55.8%. ML-minus-baseline MAE difference: 278.9, conditional approximate 95% interval [-195.6, 787.0]. The data do not demonstrate a reliable ML benefit.

The baseline has negative signed bias (-563.3 complaints/week), and its error increases from 507.8 one week ahead to 1,309.3 four weeks ahead. Failure modes include sustained changes in reporting levels, unobserved shocks, annual-lag mismatch, and residual intervals that adapt too slowly. Historical reporting delays and revisions cannot be evaluated with this snapshot.

Recommendation: retain the baseline as a shadow-study reference; validate future interval coverage and prospective source availability before workload commitments. Collection of processing and routing data would be necessary to translate counts into staffing decisions. All measured results belong to the FCC report sample.
