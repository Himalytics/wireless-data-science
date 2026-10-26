"""Render the Week 1 LinkedIn story from verified project outputs.

No generated observations or hand-entered chart values. The PDF uses vector
marks and embedded fonts; PNG pages are rendered at 1080 x 1350 pixels.
Run from any directory: python scripts/build_linkedin_assets.py
"""
import csv
import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path

import fitz
import reportlab
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "posts/assets/week-01"
W, H = 540, 675
INK = "#142D36"
TEAL = "#087F83"
MUTED = "#5A6C70"
PALE = "#D4DFDC"
PAPER = "#F5F3ED"
ORANGE = "#B8603E"
GRID = "#DBE1DD"

font_root = Path(reportlab.__file__).parent / "fonts"
pdfmetrics.registerFont(TTFont("Story", str(font_root / "Vera.ttf")))
pdfmetrics.registerFont(TTFont("StoryBold", str(font_root / "VeraBd.ttf")))
positions = []


def text(c, x, y, value, size=12, color=INK, bold=False, right=False):
    value = str(value)
    font = "StoryBold" if bold else "Story"
    width = pdfmetrics.stringWidth(value, font, size)
    start = x - width if right else x
    assert start >= 28 and start + width <= W - 28, (value, start, width)
    assert 20 <= y <= H - 20, (value, y)
    c.setFillColor(HexColor(color))
    c.setFont(font, size)
    if right:
        c.drawRightString(x, y, value)
    else:
        c.drawString(x, y, value)
    positions.append({"text": value, "x": start, "y": y, "width": width, "size": size})


def lines(c, x, y, values, size=12, leading=18, color=INK, bold=False):
    for index, value in enumerate(values):
        text(c, x, y - index * leading, value, size, color, bold)


def rect(c, x, y, width, height, color, radius=0):
    c.setFillColor(HexColor(color))
    if radius:
        c.roundRect(x, y, width, height, radius, fill=1, stroke=0)
    else:
        c.rect(x, y, width, height, fill=1, stroke=0)


def base(c, index, section):
    rect(c, 0, 0, W, H, PAPER)
    rect(c, 36, 640, 32, 4, TEAL)
    text(c, 36, 620, f"WEEK 01  /  WIRELESS DATA ENGINEERING  /  {section}", 8.6, MUTED, True)
    c.setStrokeColor(HexColor(GRID))
    c.line(36, 37, 504, 37)
    text(c, 36, 23, "HIMANSHU JADAUN  |  PERSONAL LEARNING ON PUBLIC DATA", 7.8, MUTED)
    text(c, 504, 23, f"{index:02d} / 05", 8.2, MUTED, right=True)
    c.linkURL("https://github.com/Himalytics/wireless-data-engineering", (36, 18, 420, 34))


def title(c, values):
    lines(c, 36, 577, values, 33, 41, bold=True)


def source(c, value):
    text(c, 36, 50, value, 8.2, MUTED)


def make_story():
    OUT.mkdir(parents=True, exist_ok=True)
    reports = ROOT / "reports"
    inputs = {name: (reports / name).read_bytes() for name in (
        "issue_priorities.csv", "week01_summary.json", "live_extraction_execution.json",
        "offline_replay_execution.json", "pytest.xml")}
    summary = json.loads(inputs["week01_summary.json"])
    rows = list(csv.DictReader(inputs["issue_priorities.csv"].decode().splitlines()))
    for row in rows:
        for name in ("current_complaints", "previous_complaints", "change_in_complaints"):
            row[name] = int(row[name])
        row["change_pct"] = float(row["change_pct"])
    by_issue = {r["issue"]: r for r in rows}
    billing = by_issue["Billing"]
    port = by_issue["Number Portability (keeping your number if you change providers)"]
    unwanted = by_issue["Unwanted Calls"]
    total = sum(r["current_complaints"] for r in rows)
    previous_total = sum(r["previous_complaints"] for r in rows)
    assert len(rows) == len(by_issue) == 12
    assert {r["week_start"] for r in rows} == {"2025-09-22"}
    assert all(r["current_complaints"] - r["previous_complaints"] == r["change_in_complaints"] for r in rows)
    assert max(rows, key=lambda r: r["change_in_complaints"])["issue"] == "Billing"
    assert summary["start"] == "2025-09-01" and summary["end_exclusive"] == "2025-10-01"
    py_tests = len(ET.fromstring(inputs["pytest.xml"]).findall(".//testcase"))
    dbt_tests = summary["dbt"]["tests_passed"]
    live = json.loads(inputs["live_extraction_execution.json"])["elapsed_seconds"]
    replay = json.loads(inputs["offline_replay_execution.json"])["elapsed_seconds"]
    monthly_total, monthly_wireless = summary["warehouse_rows"], summary["wireless_rows"]
    wireless_share = 100 * monthly_wireless / monthly_total
    pct = lambda row: 100 * row["change_in_complaints"] / row["previous_complaints"]
    values = {"source_dataset": "FCC CGB Consumer Complaints Data 3xyp-aqkj",
              "source_url": "https://catalog.data.gov/dataset/cgb-consumer-complaints-data",
              "snapshot_sha256": summary["snapshot_sha256"],
              "month": "September 2025", "source_rows": monthly_total,
              "wireless_rows": monthly_wireless, "wireless_share_pct": wireless_share,
              "comparison": {"previous": "2025-09-15 through 2025-09-21",
                             "current": "2025-09-22 through 2025-09-28",
                             "current_total": total, "previous_total": previous_total,
                             "total_change_pct": 100 * (total - previous_total) / previous_total},
              "issues": rows, "runtime_observations_seconds": {"live": live, "offline_replay": replay},
              "dbt_tests_passed": dbt_tests, "python_tests_passed": py_tests,
              "input_sha256": {k: hashlib.sha256(v).hexdigest() for k, v in inputs.items()},
              "limits": ["Unverified self-selected complaint reports", "No subscriber denominator",
                         "No carrier-specific, churn, causal or business-uplift claim",
                         "Runtime observations are not a benchmark"]}
    (OUT / "chart_data.json").write_text(json.dumps(values, indent=2) + "\n")
    pdf = OUT / "Week01_LinkedIn_Carousel.pdf"
    c = canvas.Canvas(str(pdf), pagesize=(W, H), pageCompression=1)
    c.setTitle("From public complaint data to a product investigation | Week 1")
    c.setAuthor("Himanshu Jadaun")
    c.setSubject("Observed FCC complaints, September 2025; personal data engineering project")

    # 1: Scope. A composition bar makes the source-to-product filter explicit.
    base(c, 1, "THE QUESTION")
    title(c, [f"{monthly_total:,} records.", "One product question."])
    lines(c, 36, 475, ["Which wireless issues deserve", "a closer look?"], 23, 31)
    text(c, 36, 358, f"{monthly_wireless:,}", 57, TEAL, True)
    text(c, 36, 329, "wireless complaint reports in September 2025", 13, MUTED)
    fraction = monthly_wireless / monthly_total
    rect(c, 36, 274, 468 * fraction, 22, TEAL)
    rect(c, 36 + 468 * fraction, 274, 468 * (1 - fraction), 22, PALE)
    text(c, 36, 253, f"Wireless: {wireless_share:.1f}%", 11, TEAL, True)
    text(c, 504, 253, f"Other: {monthly_total - monthly_wireless:,}", 11, MUTED, right=True)
    rect(c, 36, 112, 468, 104, "#FFFFFF", 9)
    lines(c, 52, 190, ["A complete API-to-data-product pipeline.",
                       "Built with AI assistance, then tested for", "completeness, replay, and failure recovery."], 13, 22)
    text(c, 36, 78, "Wireless = Phone/Internet records with a Wireless method.", 9.8, MUTED)
    source(c, "Source: FCC public complaints | Sep 1-30, 2025 | Dataset 3xyp-aqkj")
    c.showPage()

    # 2: Volume. Top five original categories; every remaining category is Other.
    base(c, 2, "VOLUME")
    title(c, ["Unwanted calls led.", "Billing came next."])
    text(c, 36, 494, f"{total:,} wireless reports | Sep 22-28, 2025", 13, MUTED)
    ordered = sorted(rows, key=lambda r: r["current_complaints"], reverse=True)
    top = ordered[:5]
    other = sum(r["current_complaints"] for r in ordered[5:])
    labels = {"Availability (including rural call completion)": "Availability (incl. rural call completion)",
              "Number Portability (keeping your number if you change providers)": "Number portability"}
    bars = [(labels.get(r["issue"], r["issue"]), r["current_complaints"]) for r in top]
    bars.append(("Other 7 issue categories", other))
    assert sum(n for _, n in bars) == total
    for i, (label, number) in enumerate(bars):
        y = 448 - 56 * i
        color = TEAL if label == "Billing" else (INK if i == 0 else "#90AAA9")
        text(c, 36, y, label, 11.7, INK, label == "Billing")
        text(c, 504, y, f"{number:,}", 12, color, True, right=True)
        rect(c, 36, y - 22, 468, 12, "#E6EBE6", 3)
        rect(c, 36, y - 22, 468 * number / unwanted["current_complaints"], 12, color, 3)
    rect(c, 36, 82, 468, 43, "#E3EEEA", 7)
    text(c, 50, 99, f"Billing represented {100 * billing['current_complaints'] / total:.1f}% of that week's reports.", 11.3, TEAL, True)
    text(c, 36, 134, "Bars share a zero baseline; lengths show report counts.", 8.8, MUTED)
    source(c, "Source: FCC | Complete week Sep 22-28, 2025 | Counts, not subscriber rates")
    c.showPage()

    # 3: Change. Same count scale for both categories; baselines shown explicitly.
    base(c, 3, "CHANGE")
    title(c, [f"Billing +{billing['change_in_complaints']}.", f"Portability +{port['change_in_complaints']}."])
    text(c, 36, 494, "Two signals. Different baselines.", 17, MUTED)
    rect(c, 36, 459, 9, 9, "#A4B6B7")
    text(c, 52, 459, "Sep 15-21", 10.4, MUTED)
    rect(c, 178, 459, 9, 9, TEAL)
    text(c, 194, 459, "Sep 22-28, 2025", 10.4, MUTED)
    plot_width, scale = 294, 1200
    for i, (label, row) in enumerate((("Billing", billing), ("Number portability", port))):
        y = 408 - i * 147
        text(c, 36, y, label, 14, INK, True)
        for j, (key, color) in enumerate((("previous_complaints", "#A4B6B7"), ("current_complaints", TEAL))):
            yy = y - 30 - j * 26
            value = row[key]
            length = plot_width * value / scale
            rect(c, 36, yy, length, 16, color, 3)
            text(c, 43 + length, yy + 3, f"{value:,}", 11, INK, True)
        text(c, 504, y - 35, f"+{pct(row):.1f}%", 23, TEAL, True, right=True)
        text(c, 504, y - 58, "report count", 10, MUTED, right=True)
    c.setStrokeColor(HexColor(GRID))
    c.line(36, 170, 330, 170)
    for tick in (0, 400, 800, 1200):
        x = 36 + plot_width * tick / scale
        c.line(x, 170, x, 166)
        text(c, x if tick == 0 else x - 8, 151, str(tick), 9, MUTED)
    text(c, 36, 130, "Complaint reports | Same scale for both issues", 9.5, MUTED)
    lines(c, 36, 100, ["Billing had the largest absolute increase across all 12 issues.",
                       "Portability's larger percentage came from a smaller base."], 10.5, 17)
    source(c, "Source: FCC | Consecutive complete weeks | Descriptive comparison only")
    c.showPage()

    # 4: Engineering results. No benchmark or speedup claim from two observations.
    base(c, 4, "ENGINEERING EVIDENCE")
    title(c, ["The findings needed", "a trustworthy pipeline."])
    for x, number, label in ((36, dbt_tests, "dbt data tests"), (276, py_tests, "Python reliability tests")):
        rect(c, x, 390, 228, 106, "#FFFFFF", 8)
        text(c, x + 16, 440, str(number), 36, TEAL, True)
        text(c, x + 16, 410, label + " passed", 10.8, MUTED)
    text(c, 36, 357, "Observed complete-pipeline runtime", 13, INK, True)
    for i, (label, value, color) in enumerate((("Live extraction", live, INK), ("Offline replay", replay, TEAL))):
        y = 322 - i * 66
        text(c, 36, y, label, 11.5, MUTED)
        rect(c, 36, y - 25, 370 * value / 80, 15, color, 3)
        text(c, 504, y - 23, f"{value:.1f} sec", 12, color, True, right=True)
    lines(c, 36, 202, ["Two observations in one Linux environment.", "Installation excluded; these are not benchmark results."], 10.5, 17, MUTED)
    rect(c, 36, 82, 468, 82, "#E3EEEA", 8)
    text(c, 50, 141, "LABELLED FAILURE-INJECTION CHECK", 8.8, TEAL, True)
    lines(c, 50, 117, ["A forced dbt failure left the last", "successful data product available."], 14, 21, INK, True)
    source(c, "Source: Executed project reports | Python 3.12.14 | No model uplift claim")
    c.showPage()

    # 5: Interpretation and a testable next step, not an invented business result.
    base(c, 5, "PRODUCT DECISION")
    title(c, ["Investigate the signal.", "Measure the next step."])
    cards = [
        ("01", "Billing", f"{billing['current_complaints']:,} reports | +{billing['change_in_complaints']} week over week",
         ["Review billing complaint themes;", "seek independent corroboration."]),
        ("02", "Number portability", f"{port['current_complaints']:,} reports | +{port['change_in_complaints']} week over week",
         ["Investigate number-transfer friction;", "keep the smaller base visible."]),
        ("03", "Measure the research process", "Investigation yield + time-to-detection",
         ["Product uplift requires a separate", "evaluation with appropriate denominators."]),
    ]
    for i, (number, heading, evidence, body) in enumerate(cards):
        y = 373 - 123 * i
        rect(c, 36, y, 468, 106, "#FFFFFF", 8)
        text(c, 49, y + 80, number, 10, TEAL, True)
        text(c, 82, y + 80, heading, 14, INK, True)
        text(c, 82, y + 58, evidence, 10.4, TEAL, True)
        lines(c, 82, y + 35, body, 10.4, 16, MUTED)
    lines(c, 36, 94, ["Self-selected reports; allegations are not verified by the FCC.",
                      "No subscriber denominator. No churn or causal conclusion."], 10.2, 17, ORANGE, True)
    source(c, "Personal project | Public FCC data | No employer data or proprietary systems")
    c.showPage()
    c.save()
    doc = fitz.open(pdf)
    assert len(doc) == 5
    names = ["01_scope", "02_volume", "03_change", "04_engineering", "05_decision"]
    for page, name in zip(doc, names):
        page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False).save(OUT / f"{name}.png")
    assert "1,041" in doc[2].get_text()
    assert "29,932" in doc[0].get_text()
    assert "not verified" in doc[4].get_text()
    (OUT / "render_verification.json").write_text(json.dumps({
        "pages": len(doc), "png_dimensions": [1080, 1350], "embedded_fonts": True,
        "text_bounds_checked": len(positions), "source_snapshot": summary["snapshot_sha256"],
        "counts_reconciled": True, "pdf_text_checks_passed": True}, indent=2) + "\n")
    print(json.dumps({"pdf": str(pdf), "pages": len(doc), "rows": monthly_total,
                      "current_week_reports": total, "billing_change_pct": round(pct(billing), 2),
                      "portability_change_pct": round(pct(port), 2)}))


if __name__ == "__main__":
    make_story()
