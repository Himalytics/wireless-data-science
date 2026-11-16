"""Replay weekly forecast intervals with explicit outcome-availability clocks."""
import hashlib
import json
import platform
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
PLAN = json.loads((ROOT / "protocol.json").read_text())
METHODS = ["frozen", "rolling", "adaptive"]


def load_weekly(exclude_unwanted=False):
    path = ROOT / "data/fcc_daily_counts.csv"
    manifest = json.loads((ROOT / "data/source_manifest.json").read_text())
    if hashlib.sha256(path.read_bytes()).hexdigest() != manifest["snapshot_sha256"]:
        raise ValueError("Source snapshot hash mismatch")
    daily = pd.read_csv(path, parse_dates=["day"]).set_index("day")
    assert daily.index.equals(pd.date_range(PLAN["start"], PLAN["end_exclusive"], inclusive="left", name="day"))
    assert len(daily) % 7 == 0 and daily.unwanted.between(0, daily.n).all()
    assert int(daily.n.sum()) == manifest["counts"] == manifest["distinct_tickets"]
    counts = daily.n - daily.unwanted if exclude_unwanted else daily.n
    return counts.resample("W-MON", label="left", closed="left").sum()


def radius(scores, alpha):
    # Finite-sample order statistic. The clipping range ensures a finite index
    # for the 52-score window. Dependence prevents an exchangeability guarantee.
    rank = int(np.ceil((len(scores) + 1) * (1 - alpha)))
    if not 1 <= rank <= len(scores):
        raise ValueError("Unsupported score window / miscoverage combination")
    return float(np.partition(np.asarray(scores), rank - 1)[rank - 1])


def stream(weekly, horizon, method, gain=0.0, lag=0):
    values = weekly.to_numpy()
    window = PLAN["rolling_window"]
    alpha = PLAN["alpha"]
    pending = []
    resolved = []
    observed = 0
    frozen_scores = None
    rows = []
    for origin in range(52 + lag, len(values) - horizon + 1):
        while observed < len(pending) and pending[observed]["available_index"] <= origin:
            item = pending[observed]
            outcome = values[item["target_index"]]
            resolved.append(abs(outcome - item["point"]))
            if method == "adaptive" and "upper" in item:
                missed = int(outcome < item["lower"] or outcome > item["upper"])
                alpha = float(np.clip(alpha + gain * (PLAN["alpha"] - missed), *PLAN["alpha_bounds"]))
            observed += 1
        target = origin + horizon - 1
        point = values[origin-lag-4:origin-lag].mean()
        item = {"target_index": target, "available_index": target + 1 + lag, "point": float(point)}
        pending.append(item)
        if len(resolved) < window:
            continue
        if frozen_scores is None:
            frozen_scores = resolved[-window:].copy()
        scores = frozen_scores if method == "frozen" else resolved[-window:]
        half_width = radius(scores, alpha)
        item.update(lower=max(0.0, point - half_width), upper=point + half_width)
        scored_index = pending[window - 1 if method == "frozen" else observed - 1]["target_index"]
        rows.append({"origin": weekly.index[origin], "target": weekly.index[target], "horizon": horizon,
                     "method": method, "point": point, "seasonal_point": values[target-52],
                     "lower": item["lower"], "upper": item["upper"], "alpha_used": alpha,
                     "actual": values[target], "latest_feature_week": weekly.index[origin-lag-1],
                     "latest_score_target": weekly.index[scored_index],
                     "latest_score_available": weekly.index[scored_index] + pd.Timedelta(weeks=1+lag),
                     "lag_weeks": lag})
    frame = pd.DataFrame(rows)
    frame["below"] = frame.actual < frame.lower
    frame["above"] = frame.actual > frame.upper
    frame["covered"] = ~(frame.below | frame.above)
    frame["width"] = frame.upper - frame.lower
    frame["score"] = frame.width + 2 / PLAN["alpha"] * (
        (frame.lower - frame.actual).clip(lower=0) + (frame.actual - frame.upper).clip(lower=0))
    return frame


def select_gain(weekly):
    locked_at = pd.Timestamp(PLAN["evaluation_start"]) - pd.Timedelta(weeks=max(PLAN["horizons"])-1)
    rows = []
    for gain in PLAN["adaptive_gains"]:
        candidate = pd.concat([stream(weekly, h, "adaptive", gain) for h in PLAN["horizons"]])
        candidate = candidate[(candidate.target >= PLAN["development_start"]) & (candidate.target < locked_at)]
        rows.append({"gain": gain, "n": len(candidate), "mean_score": candidate.score.mean()})
    return pd.DataFrame(rows).sort_values(["mean_score", "gain"])


def evaluate(weekly, gain, lag=0):
    predictions = pd.concat([stream(weekly, h, m, gain, lag) for h in PLAN["horizons"] for m in METHODS])
    predictions = predictions[predictions.target >= PLAN["evaluation_start"]].copy()
    predicted_split = pd.Timestamp(PLAN["evaluation_start"]) + pd.Timedelta(weeks=26)
    predictions["period"] = np.where(predictions.target < predicted_split, "first_26", "remaining")
    return predictions


def summarize(predictions, groups):
    return predictions.groupby(groups, sort=True).agg(
        n=("covered", "size"), covered=("covered", "sum"), coverage=("covered", "mean"),
        width=("width", "mean"), score=("score", "mean"), upper_misses=("above", "sum"),
        lower_misses=("below", "sum")).reset_index()


def paired_blocks(predictions):
    result = []
    rng = np.random.default_rng(PLAN["seed"])
    for horizon, frame in predictions.groupby("horizon"):
        scores = frame.pivot(index="target", columns="method", values="score")
        for reference in ("frozen", "rolling"):
            difference = (scores.adaptive - scores[reference]).to_numpy()
            n = len(difference)
            for length in PLAN["bootstrap_block_weeks"]:
                starts = rng.integers(0, n, size=(PLAN["bootstrap_draws"], int(np.ceil(n / length))))
                indices = ((starts[..., None] + np.arange(length)) % n).reshape(len(starts), -1)[:, :n]
                low, high = np.quantile(difference[indices].mean(axis=1), [.025, .975])
                result.append({"horizon": horizon, "reference": reference, "weeks": n, "block_weeks": length,
                               "delta_score": difference.mean(), "low95": low, "high95": high})
    return pd.DataFrame(result)


def charts(results, summary, predictions):
    colors = dict(zip(METHODS, ["#697a8b", "#177b83", "#bc512f"]))
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.4), layout="constrained")
    for axis, horizon in zip(axes, PLAN["horizons"]):
        data = summary[summary.horizon == horizon].set_index("method").loc[METHODS]
        axis.bar(METHODS, data.coverage.mul(100), color=list(colors.values()))
        axis.axhline(80, ls="--", color="#202e43")
        for index, row in enumerate(data.itertuples()):
            axis.text(index, row.coverage*100+2, f"{row.covered}/{row.n}", ha="center")
        axis.set(title=f"{horizon}-week horizon", ylabel="Covered target weeks (%)", ylim=(0, 105))
        axis.spines[["right", "top"]].set_visible(False)
    fig.suptitle("Nominal 80% intervals | FCC wireless phone reports")
    fig.savefig(results / "coverage.png", dpi=150)
    plt.close(fig)

    data = predictions[(predictions.horizon == 4) & (predictions.method == "adaptive")]
    fig, axis = plt.subplots(figsize=(9, 4.5), layout="constrained")
    axis.fill_between(data.target, data.lower, data.upper, color="#cfe4e7", label="Adaptive interval")
    axis.plot(data.target, data.actual, color="#202e43", label="Observed reports")
    axis.plot(data.target, data.point, color="#bc512f", label="Recent mean forecast")
    axis.set(ylabel="Weekly complaint reports", xlabel="Target week (UTC)", title="Four-week-ahead replay | FCC reports")
    axis.legend(frameon=False)
    axis.spines[["right", "top"]].set_visible(False)
    fig.savefig(results / "timeline.png", dpi=150)
    plt.close(fig)
    data.to_csv(results / "timeline_chart_data.csv", index=False)


def main():
    results = ROOT / "results"
    results.mkdir(exist_ok=True)
    weekly = load_weekly()
    gains = select_gain(weekly)
    gains.to_csv(results / "development.csv", index=False)
    gain = float(gains.iloc[0].gain)
    (results / "selection.json").write_text(json.dumps({"gain": gain,
        "latest_development_target_exclusive": str((pd.Timestamp(PLAN["evaluation_start"]) -
            pd.Timedelta(weeks=max(PLAN["horizons"])-1)).date()),
        "protocol_sha256": hashlib.sha256((ROOT / "protocol.json").read_bytes()).hexdigest()}, indent=2)+"\n")
    base = evaluate(weekly, gain)
    base.to_csv(results / "predictions.csv", index=False)
    summary = summarize(base, ["horizon", "method"])
    summary.to_csv(results / "overall.csv", index=False)
    summarize(base, ["horizon", "method", "period"]).to_csv(results / "periods.csv", index=False)
    paired_blocks(base).to_csv(results / "paired_blocks.csv", index=False)
    point = base[base.method == "frozen"].assign(
        recent_error=lambda x: abs(x.actual-x.point), seasonal_error=lambda x: abs(x.actual-x.seasonal_point))
    point.groupby("horizon")[["recent_error", "seasonal_error"]].mean().to_csv(results / "point_baselines.csv")
    sensitivity = pd.concat([
        summarize(evaluate(weekly, gain, lag=PLAN["feedback_lag_sensitivity"]), ["horizon", "method"]).assign(variant="two_week_data_lag"),
        summarize(evaluate(load_weekly(True), gain), ["horizon", "method"]).assign(variant="exclude_unwanted_calls")])
    sensitivity.to_csv(results / "sensitivity.csv", index=False)
    charts(results, summary, base)
    files = ["overall.csv", "timeline_chart_data.csv", "coverage.png", "timeline.png"]
    provenance = {"python": platform.python_version(), "platform": platform.platform(),
                  "source_manifest_sha256": hashlib.sha256((ROOT / "data/source_manifest.json").read_bytes()).hexdigest(),
                  "figure_hashes": {name: hashlib.sha256((results/name).read_bytes()).hexdigest() for name in files}}
    (results / "execution.json").write_text(json.dumps(provenance, indent=2)+"\n")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
