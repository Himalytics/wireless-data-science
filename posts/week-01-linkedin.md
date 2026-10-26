# LinkedIn draft - Week 1

Status: draft for Himanshu's review, not published. Pair with [the five-page carousel](assets/week-01/Week01_LinkedIn_Carousel.pdf). Verify the first-person account after your project walkthrough.

---

29,932 public telecom complaint records. Which issues would I investigate first?

That's the question behind Week 1 of my retail wireless data engineering series.

Using real FCC data for September 2025, I built an AI-assisted pipeline that ingests the API, validates records, stores a versioned warehouse, and publishes tested product-investigation tables.

The extract contained 17,280 wireless complaint reports. Comparing two complete weeks - September 15-21 and September 22-28 - revealed three useful findings:

1. Unwanted calls had the highest volume: 2,017 reports in the later week.

2. Billing had the largest absolute increase across all 12 issue categories: 925 to 1,041 reports. That's +116, or 12.5%. Billing accounted for 23.7% of the later week's wireless reports.

3. Number portability rose from 145 to 184 reports: +39, or 26.9%. The larger percentage came from a much smaller base - a useful reminder to show the underlying counts.

Those findings give me two investigation priorities: billing complaint themes and number-transfer friction. They do not establish confirmed service problems, churn, or causes.

An important engineering choice was to compare fully ingested weeks. September's final calendar week was incomplete within this extract, so it was excluded from the comparison.

The pipeline also had to handle failure. In a labelled test, forcing a dbt failure preserved the last successful data product. All 19 dbt data tests and 19 Python reliability tests passed; the initial complete run took about 68 seconds in the Linux test environment.

My learning focus is connecting dependable engineering to a decision someone can assess. The next step would be independent corroboration, with investigation yield and time-to-detection as process measures. Any product-impact claim needs a separate evaluation.

The attached charts follow the question, findings, engineering evidence, and proposed next step.

Next week: checkpointed ingestion and recovery.

Personal learning project, built with AI assistance using public data. No employer data or proprietary systems. FCC complaints are self-selected reports; the FCC does not verify their allegations.

Code and builder's guide: https://github.com/Himalytics/wireless-data-engineering

#DataEngineering #Telecom #AnalyticsEngineering #LearningInPublic
