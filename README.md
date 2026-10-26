# Retail Wireless Data Science Lab

**Himanshu Jadaun | Independent projects using real public data**

A progressive applied Data Science series focused on business questions, statistical reasoning, predictive modelling, uncertainty, and decisions relevant to retail wireless. Each project includes executed analysis, a reproducible code package, a detailed builder's guide, and a results-led LinkedIn draft with charts.

The approach was reset on **October 26, 2026**. The former Data Engineering series is [archived](archive/README.md). Its code, test counts, runtime results, posts, and charts are historical engineering work and are not results from this Data Science series.

## Current status

- Data Science projects completed: **1**, built and evaluated **October 26, 2026**.
- First project: **[Churn risk: discrimination, calibration, and decision sensitivity](projects/01_churn_risk/README.md)** — supervised machine learning on observed public telecom data.
- Primary test AP: **0.930** versus **0.772** for logistic regression. Calibration did not improve Brier error; the report retains this finding.
- **[Today’s LinkedIn draft](posts/01_churn_risk/linkedin_post.md)** and **[six-page chart carousel](posts/01_churn_risk/01_churn_risk_carousel.pdf)** are ready for review; they have not been published.
- Next scheduled project: **telecom complaint-volume forecasting, Monday November 2, 2026**, around 9 AM America/Denver.

Read [the first project brief](projects/01_churn_risk/PROJECT_BRIEF.md), [the roadmap](series/ROADMAP.md), and [the quality standard](series/SCIENTIFIC_STANDARD.md).

## The project workflow

1. Define a product question, hypothesis, target, and unit of analysis.
2. Verify a real public dataset, its licence, provenance, and limits.
3. Explore distributions, missingness, selection effects, and relationships.
4. Establish a strong simple baseline and compare justified alternatives.
5. Evaluate with a defensible split, appropriate metrics, and uncertainty.
6. Test robustness, inspect errors, and explain what the model cannot establish.
7. Translate measured findings into a product recommendation or a justified next experiment.

Engineering supports reproducibility and data integrity. Scientific validity and decision usefulness determine the project's success. There is no requirement to add Kafka, dbt, a feature store, a cloud warehouse, or a serving API to every project.

## Every completed project delivers

- Runnable Python code and an explanatory notebook, with Mac environment instructions and pinned dependencies.
- A dataset card, explicit hypotheses, feature/target definitions, and validation design.
- Baseline and model comparisons with actual metrics, uncertainty, and error analysis.
- Reproducible figures, the underlying chart data, and a decision-focused findings report.
- A builder's guide explaining concepts, statistical choices, limitations, extension exercises, and interview questions.
- A first-person LinkedIn draft and a mobile-readable PDF/PNG carousel grounded in the measured findings.

Use [the scientific standard](series/SCIENTIFIC_STANDARD.md) and [the storytelling standard](posts/STORYTELLING_STANDARD.md) as release gates. No invented results, fictional records presented as observed data, or claims of measured employer impact.

## Continuity and publishing

The GitHub repository is now named **[wireless-data-science](https://github.com/Himalytics/wireless-data-science)**. Its identity and history remain intact, with the Data Science series on main. The previous engineering tree is retained on `archive/data-engineering-2026-10-26`.

The existing recurring task is repurposed for Data Science; it must not continue the archived engineering roadmap. Follow [the current state](series/STATE.json) before selecting the next project. LinkedIn content remains a draft for review, with the existing specific-publication approval rules.
