# Week 1 visual story

Five-page PDF: [Week01_LinkedIn_Carousel.pdf](Week01_LinkedIn_Carousel.pdf). Numbered PNG versions have the same content at 1080 x 1350 pixels.

| Page | Story role | Chart or evidence |
|---|---|---|
| 1 | Establish the question and scope | Composition of 29,932 observed source records: 17,280 wireless, 12,652 other |
| 2 | Identify the high-volume issues | Latest complete week: top five source categories and the other seven combined; all 4,401 reports reconcile |
| 3 | Distinguish absolute and relative change | Billing 925 to 1,041; number portability 145 to 184; same count scale |
| 4 | Show the engineering evidence | 19 dbt tests, 19 Python tests, two runtime observations, and an explicitly injected failure |
| 5 | Translate findings into a product question | Research priorities and proposed measures, with evidence limits |

## Scope and mapping

Public source: FCC CGB Consumer Complaints Data, dataset `3xyp-aqkj`; licence: Public Domain U.S. Government. Source catalogue: https://catalog.data.gov/dataset/cgb-consumer-complaints-data.

The monthly extract covers September 1-30, 2025. Wireless means Phone/Internet records whose source method starts with `Wireless`. The week comparison is September 15-21 versus September 22-28, 2025; both are fully ingested. Monthly and weekly totals must not be mixed.

Short labels preserve the original categories: `Number portability` means `Number Portability (keeping your number if you change providers)`; `Availability (incl. rural call completion)` means `Availability (including rural call completion)`. The separate source category `Availability` remains in `Other 7 issue categories` on page 2. Categories are not silently merged or reinterpreted.

`chart_data.json` retains all 12 original issue rows, exact inputs, derived values, runtime observations, source snapshot identity, and input hashes. `render_verification.json` records arithmetic/text/dimension checks. Reports are self-selected and unverified by the FCC; they are not subscriber failure rates, churn outcomes, or causal effects.

## Alt text

1. **Scope:** September 2025 FCC extract contains 29,932 public complaint records. Of these, 17,280, or 57.7%, meet the documented wireless filter; 12,652 are other records. The project asks which issues deserve further product investigation.
2. **Volume:** For September 22-28, 2025, 4,401 wireless reports include unwanted calls 2,017; billing 1,041; equipment 367; availability including rural call completion 291; number portability 184; and all seven other issue categories 501. Billing represents 23.7% of that week's total.
3. **Change:** Between September 15-21 and September 22-28, billing reports increase from 925 to 1,041, or 116 and 12.5%. Number portability rises from 145 to 184, or 39 and 26.9%. Both use the same count scale. Billing has the largest absolute increase across all twelve categories; portability has a smaller base.
4. **Engineering:** Nineteen dbt data tests and nineteen Python reliability tests pass. The initial complete pipeline takes 67.5 seconds and an offline complete replay takes 51.5 seconds in one Linux environment. These are two observations, not a benchmark. A deliberately forced dbt-stage failure preserves the last successful data product.
5. **Decision:** Investigate billing complaint themes and possible number-transfer friction with independent corroboration. Proposed process measures are investigation yield and time-to-detection. A product-impact claim needs a separate evaluation. The underlying complaints are unverified, self-selected reports with no subscriber denominator.

## Rebuild

From the repository root, with Python 3.12 and an activated virtual environment:

```bash
python -m pip install -r requirements-viz.txt
python scripts/build_linkedin_assets.py
```

The renderer reads the committed reports, generates the PDF and PNGs, and checks row totals, comparison dates, arithmetic, text bounds, PDF page count, and selected extracted text. It does not refetch the FCC or rerun the data platform. Captured historical inputs can differ from future publisher revisions.
