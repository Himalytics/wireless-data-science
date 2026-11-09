# Builder's guide: segmentation that survives scrutiny

## What was built

An unsupervised ML study that asks whether a county network profile is stable enough to describe. The work includes source ingestion, geospatial validation, county aggregation, a simple reference, prespecified K selection, uncertainty, sensitivity and later-quarter replication. It evaluates a segmentation rather than treating a colored map as the result.

The named technique is **bootstrap-stable segmentation with frozen temporal transfer**. The bootstrap asks whether the same observed location sample supports similar assignments after resampling; temporal transfer asks whether the earlier model assigns later county observations similarly. Neither creates ground-truth market labels.

## Two-hour entry path

| Time | Work | What to explain |
|---|---|---|
| 0-20 min | Read data card and audit; inspect map | Observed tile/test unit, eligible counties, source licence, absence versus coverage |
| 20-40 | Run `python run_study.py`; inspect hashes | Reproducible source subset, real model execution, retained uncertainty |
| 40-60 | Trace county aggregation and transforms | Test weighting versus equal-tile weighting; units; development-only scaling |
| 60-80 | Inspect K selection and one-profile reference | Why support gates matter and inertia alone cannot select a meaningful K |
| 80-100 | Read bootstrap and transition tables | Label alignment, ARI, conditional uncertainty and imbalanced agreement |
| 100-120 | Explain the decision; choose an ownership experiment | Which labels are fragile, what additional observations are needed, what is unsupported |

## Pipeline and file responsibilities

`experiment_plan.json` fixes geography, quarters, support thresholds, candidate K, features, 200 bootstrap replicates, seed and sensitivity design. The selection file saves its hash before replication assignments are examined.

`download_data.py` fetches full authoritative Ookla files and Census bulk context/boundaries. It hashes full file bytes, validates licence text, and retains source metadata. It filters a Colorado bounding box, checks required metrics and unique tile identities, then assigns centroids to county interiors in a shared CRS. It joins population by five-character GEOID, checks all 64 counties match, and commits only the small reproducible geographic subset.

`study.load_snapshot` verifies those four committed input identities. `aggregate` constructs county means and support counts. `matrix` selects only network features and applies log1p. `fit` standardizes on the development set and fits K-means. `align` uses the Hungarian algorithm to remove arbitrary bootstrap label permutations.

`study.main` evaluates K candidates, locks selection, runs conditional tile bootstraps, compares an alternative clustering algorithm, and makes frozen assignments under aggregation changes and the later quarter. It then writes county-level predictions/assignments, exact metrics, support and execution evidence. `run_study.py` provides an offline-subset default plus an authoritative-download option.

`build_figures.py` reads saved evidence and creates six scientific figures, exact CSV sources and a provenance manifest. `execute_notebook.py` executes the Python-only explanatory companion in-process and captures rich outputs. It inspects and recomputes results; complete fitting remains in `study.py`.

Eight tests check source identities, unique geographic joins, weighted-unit arithmetic, development-only scaling, label-permutation handling, membership/support properties, independently recomputed temporal metrics, selection gates and figure data hashes.

## The data question comes before K-means

The target is a county summary of observed mobile speed tests. Ookla tile means describe the tests that happened, with GPS-quality location and cellular connection. They do not cover everyone or every place. Test activity varies with devices, network mixtures, time and motivation to test. Summing devices across tiles does not produce unique subscribers.

A test-weighted average answers a different question from an equal-tile average. The first emphasizes test activity; the second emphasizes sampled locations. Both condition on observed tiles. Population density cannot magically correct missing locations, because it does not identify the probability of a resident or tile appearing in the sample.

The population source is a Census estimate, explicitly labelled as such. It provides context from 2024, not a contemporaneous count of network users. Matching its county identifiers with 2024 boundaries avoids an improvised geographic crosswalk. The network quarters are later, so a claim about a causal density effect would still be unsupported.

The official Census API required a key at execution time. The implemented fallback downloads the agency's bulk population estimate file. It does not guess credentials or manufacture ACS fields. Income and ACS margins of error are absent because that source was not used.

## Geospatial choices and their limitations

Both tile centroids and county boundaries use EPSG:4326 for point-in-polygon assignment, after the boundary file is transformed from its native CRS. GEOIDs remain strings so Colorado's leading zero is retained. A one-to-one validation prevents duplicate population joins. Each tile belongs to at most one county; out-of-interior centroids are excluded and counted.

Centroid assignment is a practical approximation. A tile can cross a county border, and 1:500,000 cartographic boundaries are generalized. The project does not claim precise land-area allocation. A boundary buffer sensitivity is a substantive extension. Filling missing counties with zero network speed would create invented performance, so unsupported counties remain unassigned.

## Model selection and preprocessing

The feature vector has log1p download Mbps, upload Mbps and latency ms. Log transformation reduces scale skew; StandardScaler balances the transformed features. Only development counties fit the scaler. The later quarter uses the stored transform and centroids, which makes it a transfer test rather than a second clustering exercise with interchangeable labels.

K-means minimizes within-cluster squared Euclidean distance in that transformed space. Counties have equal clustering weight, after each county's internal test-weighted summary. This differs from weighting the clustering loss by county population or total tests.

Candidate K values are 2,3,4,5, each with 30 initializations. The minimum-five-counties-per-cluster gate prevents unsupported tiny segments. Only K=2 passes, with sizes 14/37 and silhouette 0.420. A K=3 result with silhouette 0.413 might look comparable, but it creates a four-county group and therefore fails the declared rule.

The one-profile reference records statewide county medians and dispersion. K=1 has no silhouette; do not invent one. Adding clusters reduces training inertia by construction. A lower inertia is not proof of a valid market taxonomy or an out-of-sample gain.

## Bootstrap stability and label alignment

For each of 200 replicates, sample tiles independently with replacement within each original eligible development county. Keep its number of sampled rows constant, recompute weighted means, refit scaling and selected K, then compare its labels with the reference.

Cluster labels are arbitrary. Bootstrap group 0 may correspond to reference group 1 even if the partitions are identical. The Hungarian assignment maximizes county membership overlap before calculating county frequencies. ARI already ignores numeric permutations, so it can be calculated directly on partitions.

Median bootstrap ARI is 0.631, with central conditional range [0.357,0.918]. Twelve counties fall below 80% aligned membership frequency. This frequency describes the resampling procedure; it is not calibrated probability of a true group. The range conditions on the observed tile set, fixed K, support rule and snapshot. Independent tile resampling ignores spatial dependence and within-tile test variability. A small runtime or 200 replicates does not solve those omissions.

The original county eligibility set stays fixed inside bootstrap replicates. Reapplying the eligibility threshold to each replicate would change comparison support and confound membership stability with selection. Resampled test counts may vary, which is part of the defined conditional procedure.

## Temporal transfer and misleading agreement

Fit the development scaler and centroids once, then assign the later quarter. Compare county IDs common to both eligible sets. Thirty-six of 43 counties keep their labels, but this is not supervised accuracy: no true segment labels exist.

The transition table matters. Six of 12 profile-0 counties stay there, while 30 of 31 profile-1 counties stay. Overall 83.7% agreement is dominated by the large profile. ARI of 0.395 reflects weaker partition correspondence. Do not write a post saying the segmentation is '84% accurate'.

The matched-tile diagnostic intersects county and quadkey before aggregating each quarter. It retains 26/31 labels, yet ARI is 0.164. It controls location turnover only partially: tests, device mix and weights can still change within a shared tile. Different county sets also prevent treating 83.7% and 83.9% as a directly paired comparison.

## Sensitivity and the decision

Equal-tile weighting changes seven labels among the original 51 counties. This shows the definition of 'county experience' matters. Keeping only tiles with at least five tests retains 23 eligible counties, with 21 labels unchanged. Its 91.3% rate is not a statewide robustness claim. Ward clustering's ARI 0.843 is useful algorithm sensitivity on the same observations, not an independent replication.

The bounded product decision is to use stable profiles as hypotheses for additional measurement, flag fragile counties and leave unsupported ones unlabelled. A consequential deployment would need later-quarter validation, spatial-block uncertainty, border sensitivity and a sampling design that measures unobserved locations. The study does not identify carrier quality, population coverage, churn impact or an employer outcome.

## Daily ownership experiments

Day 1: reproduce the study and manually reconstruct one county's weighted means. Day 2: perturb the density column and confirm it cannot change the three-feature model matrix. Day 3: permute labels in a toy partition and demonstrate why raw agreement can be wrong without alignment. Day 4: reproduce the temporal transition table and explain the minority profile's movement. Day 5: implement one extension in a preserved new experiment with its own protocol.

Substantive extensions include spatial blocks rather than independent tiles, border-distance filtering, a different support threshold chosen before later-quarter inspection, and robust aggregation such as weighted trimmed means. Do not optimize these choices on the released replication quarter and then call that same quarter an untouched test.

## Common errors and interview defense

| Problem | Explanation or remedy |
|---|---|
| Census endpoint returns HTML | API key requirement; use the implemented public bulk source |
| A fresh run changes source rows | Ookla may reaggregate; committed hashes identify this release's exact subset |
| GEOID becomes `8067` | Preserve it as a string; `08067` is the five-character join key |
| Map appears to show all residents' experience | It shows county labels from observed tiles; unsupported land/users remain unknown |
| More clusters look better | Inertia falls mechanically; use the prespecified support and interpretation gates |
| Bootstrap labels appear reversed | Align them; numeric cluster IDs have no intrinsic meaning |
| Same-profile percentage is called accuracy | It is stability of descriptive assignments; no ground-truth labels exist |
| Model download is slow | Default snapshot rerun avoids the roughly 371 MB full-source download |

**Why use ML here?** To summarize multivariate network-test patterns and test whether that summary survives changes in data and assumptions. The result includes instability, not just attractive group averages.

**What is the biggest limitation?** The sampling frame is self-selected observed test tiles. A statistically stable partition of those observations would still not establish population coverage or subscriber experience.

**Why keep Census outside clustering?** It provides geographic context without letting population density define groups that are then presented as network-only discoveries. Ecological description is still not causation.

**What would make the recommendation stronger?** Consistent later-quarter behavior, spatial-block uncertainty, controlled sample turnover and a purpose-designed follow-up measurement process tied to a separately evaluated decision.
