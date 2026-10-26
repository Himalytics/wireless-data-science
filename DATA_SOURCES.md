# Source attribution and scope

Federal Communications Commission. *CGB – Consumer Complaints Data*. Dataset `3xyp-aqkj`.

- Authoritative catalogue: https://catalog.data.gov/dataset/cgb-consumer-complaints-data
- Publisher landing page: https://opendata.fcc.gov/Consumer/CGB-Consumer-Complaints-Data/3xyp-aqkj
- Metadata: https://opendata.fcc.gov/api/views/3xyp-aqkj.json
- API: https://opendata.fcc.gov/resource/3xyp-aqkj.json
- Licence reported by publisher metadata: **Public Domain U.S. Government**.
- Licence reference: https://www.usa.gov/government-works
- Default requested period: `date_created >= 2025-09-01` and `date_created < 2025-10-01`.
- Observed fields: complaint ID, source creation calendar date, issue type, method, issue, state.

Source caveat: the FCC does not verify facts alleged in the informal complaints, and the data reflects information selected by consumers. Counts cannot be interpreted as subscriber churn, incident rates, carrier market shares, or confirmed service faults.

The small test fixture is an attributed projection of 24 actual records captured from this API. `tests/fixtures/PROVENANCE.json` records its URL, retrieval time, checksum, and scope. Test mutations are labelled fault injection. No synthetic records appear in the published analytical data.

Default-month results are tied to the captured snapshot identity in `reports/VERIFICATION.md`. The publisher may revise historical records; a later fresh download can yield different numbers. Save immutable page bytes and manifests when comparing results across time.
