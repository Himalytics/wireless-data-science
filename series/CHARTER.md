# Data Science series charter

Owner: Himanshu Jadaun. Reset date: October 26, 2026. Focus: applied Data Science for retail wireless product questions, with explicitly identified method demonstrations from other industries when an appropriate telecom dataset is unavailable.

## Purpose

Build a progressively stronger portfolio of empirical reasoning: hypotheses, exploratory analysis, statistical modelling, machine learning, honest evaluation, uncertainty, and defensible decisions. Preserve the user's high difficulty standard. A notebook that loads a CSV and fits one classifier is insufficient.

The first guided session should make the project runnable and understandable in about two hours. Provide deeper experiments and an ownership exercise for additional study across the week, fitting roughly two hours a day. Complete reference code and an ownership exercise are required. Public accounts describe actual methods and findings; personal experiences and independent contributions must be accurate.

## Real data and appropriate claims

Every project identifies a specific observed public dataset, authoritative source, licence, automated download method, retrieval/version information, and unit of analysis. Verify feasibility before implementation. Fictional IBM Telco sample data cannot be described as observed customer records. Simulated experiments or assumptions may augment real data only when explicitly labelled in code, reports, charts, and posts.

Use no EchoStar / Boost Mobile internal data, code, dashboards, customer data, or proprietary designs, and do not imitate internal systems. Keep public writing framed as independent personal learning. A real dataset from another geography or industry does not establish outcomes for Boost Mobile or U.S. wireless subscribers.

Do not fabricate dates, customer links, treatment assignments, outcomes, causal effects, or historical observations. In particular, customer tenure is not automatically event-time/censoring data, churn risk is not retention uplift, and aggregate network tiles are not linked individual churn outcomes.

## Scientific depth

Each project names a new technique and demonstrates at least three relevant scientific practices from: leakage-safe evaluation, nested or grouped validation, proper temporal backtesting, calibration, statistical uncertainty, sensitivity/ablation analysis, causal identification, experiment analysis, subgroup/error analysis, or robustness under distribution shift. Choose practices justified by the question and source; do not mechanically apply every method.

Select tools for the analysis. A typical local stack may include Python, pandas/NumPy, scikit-learn, SciPy/statsmodels, and plotting libraries. Specialized libraries are introduced only when needed. The previous requirements for mandatory orchestration, storage platforms, process-kill testing, and infrastructure rotation are retired from the active series.

Use [the scientific quality standard](SCIENTIFIC_STANDARD.md) as a release gate. Actually execute the analysis and relevant checks. Record the environment, input identity, validation split, model settings, actual metrics, and limits. If a method does not beat the baseline, report that finding rather than force a success story.

## Deliverables and communication

Each release includes working code, an explanatory notebook, a builder's guide, a dataset/model card, an experiment record, a results report, reproducible chart data and figures, and a complete LinkedIn draft paired with a visually checked carousel. Use the templates under `templates/` as structures, not as completed evidence.

The findings report states what was learned, how reliable it is, what decision it supports, and what additional evidence is required. Hypothetical costs or benefits must remain labelled assumptions. No claim of measured retention, revenue, or customer impact without supporting outcome evidence.

## Publication and continuity

Configured repository: `Himalytics/wireless-data-science`, renamed for the active Data Science series while preserving repository identity and history. The engineering branch and old package are archives only; do not continue their roadmap or reuse their results as Data Science evidence.

The user previously required approval for specific repository operations and individual LinkedIn publication. Preserve that rule until clearly changed. The cleanup/pivot is authorized in the current conversation; future scheduled releases must respect the applicable publication approval. No direct LinkedIn publishing connection is configured, so deliver drafts and visual assets to Himanshu.

Maintain current project numbering and status in `STATE.json`. The Data Science series starts at project 1; it does not inherit completed engineering weeks. Use current GitHub state as authoritative and avoid reliance on transient local files.
