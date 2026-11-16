# Interval model card

**Intended decision** · Compare safeguards for a forecast-driven workload review. Target is the count of anonymous FCC wireless phone reports submitted during a UTC week. Issue on Monday for the week starting that day or three Mondays later. A recent four-week mean provides the same center for all interval methods. The same-week-prior-year forecast is an additional point baseline.

The score is absolute error of an already-issued point prediction. Once a target closes, its error becomes available the next Monday under the primary availability assumption. For horizons one and four, separate histories avoid pooling different error distributions.

- **Frozen** uses the first 52 eligible errors, collected before the development period, at alpha 0.20.
- **Rolling** uses the latest 52 eligible errors at alpha 0.20.
- **Adaptive** uses the rolling 52 errors, updating alpha by gain × (0.20 − miss) when earlier issued intervals resolve. Alpha is clipped to [0.04, 0.45] and the lower interval endpoint is clipped at zero.

All radii use the order statistic at rank ceil((n+1)(1−alpha)). These are conformal-style online intervals inspired by [Gibbs and Candès (2021)](https://proceedings.neurips.cc/paper_files/paper/2021/hash/0d441de75945e5acbc865406fc9a2559-Abstract.html). The chosen clipping and dependence mean the study claims no exchangeability-based finite sample or arbitrary-shift guarantee.

The gain grid 0.01, 0.03, 0.06 is scored on development weeks available by the earliest evaluation issue date. The chosen gain is 0.01. Earlier outcomes from the evaluation enter the state through the specified arrival rules. No evaluation outcome chooses the gain. Prior project work described some of the same weeks, so this is a retrospective temporal comparison.

The output reports coverage, width, interval score and directional misses. Where coverage is an operational requirement, establish explicit acceptable miss rates and compare against the cost of broad ranges on prospective snapshots. Four-week adaptive estimates were wider than rolling estimates at the same observed coverage. The aggregate coverage target is not a promise for a specific week or period.
