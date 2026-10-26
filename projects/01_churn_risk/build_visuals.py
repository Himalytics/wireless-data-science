"""Render all numeric charts and a six-page LinkedIn document from measured results."""
import hashlib
import json
from pathlib import Path

import fitz
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
import numpy as np
import pandas as pd
import reportlab
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

HERE = Path(__file__).resolve().parent
OUT = HERE / "figures"
POST = HERE.parents[1] / "posts/01_churn_risk"
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


def carousel(m):
    POST.mkdir(parents=True, exist_ok=True)
    fonts = Path(reportlab.__file__).parent / "fonts"
    pdfmetrics.registerFont(TTFont("Vera", str(fonts / "Vera.ttf")))
    pdfmetrics.registerFont(TTFont("VeraBold", str(fonts / "VeraBd.ttf")))
    path = POST / "01_churn_risk_carousel.pdf"
    c = canvas.Canvas(str(path), pagesize=(540,675))
    c.setTitle("Churn risk: what the validation changed | Himanshu Jadaun")
    c.setAuthor("Himanshu Jadaun")
    def text(x, y, value, size=13, font="Vera", color=NAVY):
        c.setFont(font, size); c.setFillColor(HexColor(color)); c.drawString(x,y,value)
    def lines(values, y, size=13, leading=20, bold=False, color=NAVY):
        for value in values:
            text(36,y,value,size,"VeraBold" if bold else "Vera",color); y -= leading
    def start(page, title, subtitle):
        c.setFillColor(HexColor(PAPER)); c.rect(0,0,540,675,fill=1,stroke=0)
        c.setFillColor(HexColor(TEAL)); c.rect(36,628,34,4,fill=1,stroke=0)
        text(80,626,"RETAIL WIRELESS DATA SCIENCE / 01",9,"VeraBold",TEAL)
        lines(title,580,31,39,True)
        text(36,482,subtitle,11,color=GRAY)
        c.setStrokeColor(HexColor("#D1D8D5")); c.line(36,58,504,58)
        text(36,39,"HIMANSHU JADAUN  /  PUBLIC-DATA LEARNING",8,"VeraBold",GRAY)
        text(480,39,f"{page} / 6",8,color=GRAY)
        text(36,21,"UCI Iranian Churn (563), CC BY 4.0  |  Analysis: 26 Oct 2026",7.5,color=GRAY)
    def image(name,y,height):
        c.drawImage(ImageReader(str(OUT/(name+".png"))),36,y,width=468,height=height,preserveAspectRatio=True,anchor="c",mask="auto")
    start(1,["83.9% accurate.","Zero churners found."],"An all-no-churn prediction looks accurate on this test set.")
    image("01_test_class_balance",218,244)
    lines(["THE QUESTION", "Can a model prioritize a limited review queue", "and produce defensible risk probabilities?"],188,14,23)
    lines(["3,150 observed source records. 639 held out.","A historical Iranian sample, not U.S. carrier evidence."],104,11,17,color=GRAY)
    c.showPage()
    start(2,["Boosting beat the", "logistic baseline."],"Primary models: the same conservative 11-predictor feature set.")
    image("02_average_precision",210,250)
    lines(["0.930 AP for boosting; 0.772 for logistic.","95% intervals: 0.881–0.966 and 0.694–0.839."],187,13,21,True)
    lines(["300 repeated rows prompted grouped splits at every layer.","Model choice used development OOF Brier, before test scoring.","Intervals: 500 profile-cluster resamples, conditional on fitted models."],123,10.5,17,color=GRAY)
    c.showPage()
    start(3,["Calibration didn't", "improve this result."],"Same base-learner ensemble, with and without sigmoid calibration.")
    image("03_reliability",195,270)
    lines(["Brier: raw 0.0361 to calibrated 0.0372.","Lower is better. Keep the negative finding."],175,13,21,True)
    lines(["8 fixed probability bins; some bins have few observations.","Brier measures probability error, not calibration alone.","The prespecified calibrated model remains the primary result."],116,10.5,17,color=GRAY)
    c.showPage()
    start(4,["64 reviews contained", "63 churn labels."],"At roughly 10% review capacity in the 639-record test set.")
    image("04_review_capacity",196,266)
    lines(["61.2% of the 103 churn labels captured.","Random review would capture about 10% on average."],175,13,21,True)
    lines(["This is ranking and observed label concentration.","It does not establish prevented churn or offer effectiveness.","An intervention needs separate prospective experimental evidence."],116,10.5,17,color=GRAY)
    c.showPage()
    start(5,["More fields require", "an availability check."],"Gradient boosting: primary feature set versus source-field sensitivity.")
    image("05_feature_sensitivity",208,254)
    lines(["Primary excludes Status and Customer Value.","Their operational construction needs verification."],183,13,21,True)
    lines(["The source says predictors cover the first 9 months.","Exclusion is a conservative choice, not proof of leakage.","All-field results were ineligible for primary model selection.","Error bars: conditional 95% profile-cluster bootstrap intervals."],126,10.5,16,color=GRAY)
    c.showPage()
    start(6,["A promising ranking.", "A bounded conclusion."],"The learning: ranking, probability quality, and impact are different.")
    steps = [("01", "Audit before modelling", "Repeated profiles changed the validation design."),
             ("02", "Nest tuning and calibration", "Keep each evaluation fold outside every fit."),
             ("03", "Make the decision conditional", "Validate prospectively before testing an offer.")]
    for y,(number,title,body) in zip([421,326,231],steps):
        text(36,y,number,23,"VeraBold",TEAL)
        text(88,y+3,title,16,"VeraBold")
        text(88,y-22,body,10.5,color=GRAY)
    lines(["NEXT: forecast real, dated telecom complaint volumes.","Code, experiment record, predictions and charts on GitHub:","Himalytics/wireless-data-science"],128,11,20)
    c.showPage(); c.save()
    with fitz.open(path) as pdf:
        for i,page in enumerate(pdf):
            pix = page.get_pixmap(matrix=fitz.Matrix(2,2), alpha=False)
            pix.save(POST / f"slide_{i+1:02}.png")
    return path


if __name__ == "__main__":
    print(carousel(charts()))
