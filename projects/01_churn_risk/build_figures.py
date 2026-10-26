"""Generate scientific figures, exact chart tables and provenance from evaluated results."""
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
OUT = HERE / "figures"
NAVY, TEAL, GRAY, GOLD, PAPER = "#142D36", "#087F83", "#5A6C70", "#BE7A22", "#F5F3ED"


def charts():
    OUT.mkdir(parents=True, exist_ok=True)
    m = json.loads((HERE / "results/metrics.json").read_text())
    d = json.loads((HERE / "results/chart_data.json").read_text())
    pred = pd.read_csv(HERE / "results/test_predictions.csv")
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 12, "axes.spines.top": False,
        "axes.spines.right": False, "axes.labelcolor": NAVY, "text.color": NAVY,
        "xtick.color": GRAY, "ytick.color": GRAY, "axes.edgecolor": GRAY,
        "figure.facecolor": PAPER, "axes.facecolor": PAPER, "savefig.facecolor": PAPER})
    def save(fig, name):
        fig.savefig(OUT / (name + ".png"), dpi=180, bbox_inches="tight", pad_inches=.18)
        plt.close(fig)
    # Chart 1: source is held-out labels, not the entire dataset.
    fig, ax = plt.subplots(figsize=(7.6, 3.7))
    counts = [(pred.target == 0).sum(), pred.target.sum()]
    bars = ax.barh(["No-churn labels", "Churn labels"], counts, color=[GRAY, TEAL], height=.5)
    for b, v in zip(bars, counts):
        ax.text(v + 9, b.get_y() + b.get_height()/2, f"{v}", va="center", weight="bold", fontsize=15)
    ax.set(xlim=(0, 620), xlabel="Observed records in the held-out test set (n = 639)")
    ax.invert_yaxis()
    fig.tight_layout()
    save(fig, "01_test_class_balance")
    pd.DataFrame({"target_label": ["no_churn", "churn"], "count": counts}).to_csv(OUT / "01_test_class_balance.csv", index=False)
    # Chart 2: intervals describe conditional sampling uncertainty, not independent folds.
    names = ["prior", "conservative_logistic", "conservative_gradient_boosting"]
    labels = ["Constant prior", "Logistic regression", "Gradient boosting"]
    fig, ax = plt.subplots(figsize=(7.6, 3.8))
    rows = []
    for i, (name, label) in enumerate(zip(names, labels)):
        point = m["test_metrics"][name]["average_precision"]
        ci = m["test_metric_intervals"][name]["average_precision"]
        ax.errorbar(point, i, xerr=[[point-ci["low"]], [ci["high"]-point]], fmt="o", capsize=6,
                    color=TEAL if i == 2 else GRAY, markersize=9, linewidth=2)
        ax.text(point, i-.22, f'{point:.3f}', ha="center", weight="bold", fontsize=13)
        rows.append({"model": name, "average_precision": point, **ci})
    ax.set(yticks=range(3), yticklabels=labels, xlim=(0, 1.01), ylim=(-.6, 2.6), xlabel="Average precision (AP); higher is better")
    ax.invert_yaxis()
    ax.grid(axis="x", alpha=.15)
    fig.tight_layout()
    save(fig, "02_average_precision")
    pd.DataFrame(rows).to_csv(OUT / "02_average_precision.csv", index=False)
    # Chart 3: same base-learner ensemble, before and after sigmoid recalibration.
    fig, ax = plt.subplots(figsize=(7.6, 4.2))
    ax.plot([0, 1], [0, 1], "--", color=GRAY, alpha=.65, label="Perfect agreement")
    rows = []
    for name, label, color, marker in [("selected_uncalibrated", "Raw ensemble", GRAY, "s"),
              (m["selected_model"], "Sigmoid calibrated", TEAL, "o")]:
        table = pd.DataFrame(d["model_curves"][name]["calibration"])
        ax.plot(table.mean_probability, table.observed_fraction, color=color, marker=marker, label=label, linewidth=2)
        rows.extend([{"variant": label, **r} for r in table.to_dict("records")])
    ax.set(xlim=(0, 1), ylim=(0, 1.03), xlabel="Mean predicted probability", ylabel="Observed churn fraction")
    ax.legend(loc="lower right", frameon=False, fontsize=10)
    ax.grid(alpha=.15)
    fig.tight_layout()
    save(fig, "03_reliability")
    pd.DataFrame(rows).to_csv(OUT / "03_reliability.csv", index=False)
    # Chart 4: cumulative label capture under a ranked review budget.
    fig, ax = plt.subplots(figsize=(7.6, 4.0))
    curve = pd.DataFrame(d["concentration"])
    ax.plot(np.r_[0, curve.review_fraction], np.r_[0, curve.fraction_of_churn_labels], color=TEAL, linewidth=2.8, label="Selected model")
    ax.plot([0, 1], [0, 1], "--", color=GRAY, label="Random review: expected")
    q = m["review_queues"][m["selected_model"]][1]
    x, y = q["reviewed"]/q["test_rows"], q["recall"]
    ax.scatter([x], [y], color=GOLD, s=65, zorder=4)
    ax.annotate(f'64 / 639 reviewed\n63 / 103 churn labels', xy=(x,y), xytext=(.42,.28),
                arrowprops={"arrowstyle": "->", "color": NAVY}, fontsize=12)
    ax.set(xlim=(0, 1), ylim=(0, 1.02), xlabel="Fraction of test records reviewed", ylabel="Fraction of churn labels captured")
    ax.xaxis.set_major_formatter(PercentFormatter(1))
    ax.yaxis.set_major_formatter(PercentFormatter(1))
    ax.legend(loc="lower right", frameon=False, fontsize=10)
    ax.grid(alpha=.15)
    fig.tight_layout()
    save(fig, "04_review_capacity")
    curve.to_csv(OUT / "04_review_capacity.csv", index=False)
    # Chart 5: sensitivity only; not a second model-selection competition.
    fig, ax = plt.subplots(figsize=(7.6, 3.8))
    rows = []
    labels = ["11 predictors\nPrimary feature set", "13 predictors\nSensitivity only"]
    for i, name in enumerate(["conservative_gradient_boosting", "all_gradient_boosting"]):
        value = m["test_metrics"][name]["average_precision"]
        ci = m["test_metric_intervals"][name]["average_precision"]
        ax.bar(i, value, color=TEAL if i == 0 else GRAY, width=.5)
        ax.errorbar(i, value, yerr=[[value-ci["low"]], [ci["high"]-value]], color=NAVY, capsize=6, fmt="none")
        ax.text(i, value+.055, f'{value:.3f}', ha="center", weight="bold", fontsize=14)
        rows.append({"model": name, "average_precision": value, **ci})
    ax.set(xticks=[0, 1], xticklabels=labels, ylim=(0, 1.09), ylabel="Average precision; higher is better")
    ax.grid(axis="y", alpha=.15)
    fig.tight_layout()
    save(fig, "05_feature_sensitivity")
    pd.DataFrame(rows).to_csv(OUT / "05_feature_sensitivity.csv", index=False)
    provenance = {"title": "Churn risk: discrimination, calibration, and decision sensitivity",
        "analysis_date": "2026-10-26", "source": m["audit"]["source"], "dataset_doi": "10.24432/C5JW3Z",
        "license": "CC BY 4.0", "scope": "UCI Iranian telecom sample, 639 held-out records / 103 churn labels; not a chronological test",
        "uncertainty": "95% percentile intervals from 500 held-out profile-cluster bootstrap resamples; conditional on fitted models and this sample",
        "metric_source_sha256": hashlib.sha256((HERE / "results/metrics.json").read_bytes()).hexdigest(),
        "figures": {str(p.name): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(OUT.glob("*.png"))}}
    (OUT / "provenance.json").write_text(json.dumps(provenance, indent=2)+"\n")
    return m



if __name__ == "__main__":
    charts()
    print("Generated scientific figures and provenance:", OUT)
