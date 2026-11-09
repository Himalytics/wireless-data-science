# Source and dataset card

## Authoritative sources and licence

1. [Ookla open-data documentation](https://github.com/teamookla/ookla-open-data): mobile cellular test tiles, GPS-quality location; zoom 16, quarterly aggregates. Licence: [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/). Full source URLs, last-modified metadata, S3 version information where returned, retrieval timestamp and SHA-256 identities appear in `results/source_manifest.json`.
2. [2024 Census cartographic county boundaries](https://www2.census.gov/geo/tiger/GENZ2024/shp/cb_2024_us_county_500k.zip): generalized 1:500,000 county polygons and land area (`ALAND`), U.S. government public domain. Original CRS is transformed to EPSG:4326 before spatial assignment.
3. [Census Vintage 2024 county population estimates](https://www2.census.gov/programs-surveys/popest/datasets/2020-2024/counties/totals/co-est2024-alldata.csv): `POPESTIMATE2024`, Colorado state 08 and county SUMLEV 050. These are official population estimates, not direct subscriber counts; no ACS margins of error are represented. U.S. government public domain.

The API feasibility probe returned a Census missing-key redirect. The implemented download uses the official bulk population file, not an invented estimate or scraped private table. ACS income was not included. Density is background context only.

## Periods, unit and join

Development: 2025 Q4 (October-December 2025). Replication: 2026 Q1 (January-March 2026). Source access: November 9, 2026. Quarterly tile means are observed historical test aggregates, subject to publisher reaggregation. Both are available source files; the project does not claim they are the latest available quarter.

Geography: 64 Colorado counties. 2024 county geometry and population vintage are matched by five-character state/county GEOID. No changed-boundary crosswalk is inferred; all 64 records match one-to-one. Census context predates the network quarters and is treated as background, not a contemporaneous population measurement or individual predictor.

Spatial assignment uses each published tile centroid (`tile_x`,`tile_y`) within a county polygon. Boundary-centroid points that do not fall strictly inside are not assigned. Cartographic generalization and tiles spanning county borders create assignment uncertainty. This is centroid assignment, not exact tile-area allocation. An absent tile does not establish a service gap.

## Fields and audit

| Field | Meaning and use |
|---|---|
| `quadkey` | Published tile identity; string, unique per quarter |
| `tile_x`, `tile_y` | Longitude/latitude centroid; EPSG:4326 |
| `avg_d_kbps`, `avg_u_kbps` | Published tile mean download/upload; divided by 1,000 for Mbps |
| `avg_lat_ms` | Published average latency in milliseconds |
| `tests` | Number of tests in the tile; primary aggregation weight |
| `devices` | Unique contributing devices within that tile; sums across tiles are not unique devices or people |

| Audit | 2025 Q4 | 2026 Q1 |
|---|---:|---:|
| Bounding-box tiles | 7,942 | 7,316 |
| Invalid metric rows excluded | 2 | 2 |
| Valid rows outside strict county interiors | 3 | 2 |
| Assigned Colorado tiles | 7,937 | 7,312 |
| Observed tests | 33,640 | 32,102 |
| Sum of tile device counts, not unique people | 12,572 | 11,622 |
| Counties meeting 5-tile/25-test rule | 51 | 45 |

Validation excludes missing required fields, nonpositive test/device counts, negative speeds and nonpositive latency. Each centroid joins at most one county, and tile identities remain unique. Every included county/quarter's test count conserves the assigned tile totals. Counties below the support gate remain visible as unassigned; no missing performance is filled with zero.

The matched-tile diagnostic intersects `(GEOID,quadkey)` across quarters: 3,294 shared tiles, with 31 counties meeting support in both matched subsets. This does not identify the same tests, devices or people across quarters.

## Aggregation and sampling limits

County features are test-count-weighted averages of published tile means, with source rounding retained. They approximate the distribution of observed test activity. Equal-tile aggregation instead emphasizes sampled locations. Neither estimates a representative resident or subscriber distribution. K-means then gives each eligible county equal weight.

Speedtest participation is self-selected; repeated tests, device capabilities, traffic time, network technology and carrier mixtures are not controlled. The open tile data contain no verified carrier, subscriber, causal treatment or linked churn identity. No Census-based reweighting turns these observations into population coverage.

## Reproducibility and attribution

The full global source files are hashed and cached under ignored `data/raw/`. The exact assigned tile subsets are committed as deterministic gzip CSVs, alongside county context and boundary snapshots. `study.load_snapshot` verifies the four input hashes before fitting. `results/source_manifest.json` retains original download identities separately from subset identities. Live reaggregation can change a fresh source run; use the committed subset for this release.

Based on Himanshu Jadaun's analysis of Speedtest by Ookla Global Fixed and Mobile Network Performance Maps for 2025 Q4 and 2026 Q1, accessed November 9, 2026. Ookla-derived subsets and outputs are shared under CC BY-NC-SA 4.0. Census data are attributed to the U.S. Census Bureau. See `DATA_LICENSE.md`.
