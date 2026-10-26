# LinkedIn storytelling standard

Each weekly release must include a results-led post and reproducible visual assets. This standard was requested by Himanshu on October 26, 2026 and applies to the scheduled series.

## Required story

Write a complete first-person draft, usually 250-400 words, with a concrete question, brief relevant build context, two or three quantified findings, the engineering judgment needed to trust them, a defensible product implication, and the next learning step. Tool names support the story rather than occupy most of it. State the dataset period and comparison scope. Use only real measured results and label simulations and fault-injection scenarios.

Do not invent Himanshu's experiences, independent authorship, emotions, incidents, business outcomes, or what he has already learned. Frame unfamiliar concepts as the learning focus, disclose AI assistance appropriately, and mark the account for review after his walkthrough. Keep the project independent of employer systems.

## Required visuals

- A mobile-readable 4-6 page PDF carousel plus numbered PNG pages, normally 1080 x 1350 pixels.
- At least two meaningful charts when the evidence supports them: show findings and measured engineering behavior. Choose forms that fit the data; a reliability or cost project may need different visuals from an analytical project.
- Every page has a takeaway headline and a purpose in the story: question/scope, observed patterns, a comparison or surprise, engineering evidence, and the proposed decision.
- Record source, observation period, units, cohort/filter, comparison dates, and relevant baselines. Explain any aggregation or shortened labels. Separate count growth from rate changes and percentage points.
- Use accurate scales, zero baselines for bars, readable labels, consistent comparison units, restrained colors, and explicit sample/volume context. A large percentage on a small base must show the base.
- Include concise caveats that matter to interpretation. Do not imply causation, churn, customer impact, or current-market conditions from descriptive historical complaints.

## Reproducibility and review

Generate charts in code from validated outputs. Keep the renderer, exact chart data, source/output identities, captions, alt text, and image/PDF exports with the release. Verify arithmetic, reconciliation, dates, filters, and dimensions; render and inspect every page for clipping and readability before delivery. Do not use AI image generation to draw precise data charts.

If empirical findings are unavailable, state that and chart actual engineering results rather than invent a business discovery. Single runtime observations are not performance benchmarks. Distinguish deliberate failure tests from observed upstream incidents.

Present the draft and visual assets together for review. The existing approval rule for specific repository operations and LinkedIn publication remains in force. A generated draft or connection does not mean a LinkedIn post was published.
