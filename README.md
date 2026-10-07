# Measurement choices in longitudinal citation language comparisons around replication projects

**Current analysis code is directly below, at the repository root.** This project
accompanies the manuscript by Dongdong Guo and Jiaxuan Li. The reproduction
commands use saved derived inputs; no API key, model inference, GPU or data
download is needed once Python dependencies are installed.

## Run from the repository root

Use Python 3.12 with the published dependency versions:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python run_all.py
```

Generated tables and verification receipts go to `results/`. Numerical checks
use 1e-12 absolute/relative tolerance for floating-point fields and exact matching
for text and integers. Different numerical-library builds can change final
floating-point digits; the optional original byte check is available with
`python reproduce_retention.py --strict-bytes`. The statistical calculations
and published reference files are unchanged.
To list commands without running them, use `python run_all.py --list`.
To run one component, use `python run_all.py --only retention` (or `scores`,
`literal`, `selection`, `external`).

| Code at the repository root | What it reproduces |
| --- | --- |
| [analyze_scores.py](analyze_scores.py), [analysis_core.py](analysis_core.py) | Saved-score comparisons and specified sensitivity analyses |
| [precision_simulation.py](precision_simulation.py) | Explicitly hypothetical model-scale precision scenarios |
| [analyze_literal_counts.py](analyze_literal_counts.py), [literal_features.py](literal_features.py) | Fixed literal-word indicators, retained/excluded counts and matched filter contrasts |
| [staunton_selected_sensitivity.py](staunton_selected_sensitivity.py) | Separately labeled 106-source scope sensitivity |
| [analyze_selection_decomposition.py](analyze_selection_decomposition.py) | Exact selection accounting, conditional uncertainty and influence checks |
| [reproduce_retention.py](reproduce_retention.py), [benchmark_core.py](benchmark_core.py) | Frozen year/length-matched artificial-retention references |
| [reproduce_external_linkage.py](reproduce_external_linkage.py) | Bounded external-linkage descriptive counts |
| [verify_results.py](verify_results.py) | Comparison with published numerical tables |

## Inputs, papers and historical material

- [data/](data/): frozen derived inputs, reference tables and component explanations.
- [releases/researchsquare-v3-20261007/](releases/researchsquare-v3-20261007/): manuscript, supplementary information, original resource ZIPs, LaTeX source and Figure 1 exports.
- [Versioned GitHub release](https://github.com/lijiajia3/claim-drift/releases/tag/researchsquare-v3-20261007): the unchanged publication snapshot and downloadable assets.
- [archive/legacy/](archive/legacy/): previous collection, API-scoring, annotation and analysis files, preserved for traceability.
- [docs/CODE_PROVENANCE.json](docs/CODE_PROVENANCE.json): exact source mapping and the input/output-path changes used to expose the current code here.

You do not need to extract a supplement ZIP to run the root-level commands.
Original standalone ZIPs remain available for reproducing their full auxiliary
workflows, source-criterion clarifications, figure/report builders and independent
checks. Original component documents refer to their original layout; use this
README for the reorganized repository.

## What the results support

The exploratory baseline contains **105 source papers from four replication
projects**, **15,280 within-source deduplicated text units**, and **8,427 retained
empirical restatements**. The paired comparison uses the same 72 eligible sources.
Filtering changes the between-group pre–post replication-word contrast by
**−1.55 percentage points** (conditional source-bootstrap 95% interval −3.03 to
−0.24). Retention matched on year and length reproduces −0.65 points. The observed
shift lies near the simulation-envelope boundary; the remaining −0.90 points is
descriptive, not an identified mechanism. Adverb/modal contrasts lie inside every
reference envelope. Omitting the largest project or narrowing the window yields
filter-shift intervals including zero.

Literal words do not establish semantic acknowledgment or belief updating. The
model score remains secondary because its mixed rubric and reused development
data limit interpretation. Reproduction verifies arithmetic conditional on the
archive; it does not add semantic validation or causal identification.

## Preprint and rights

[Research Square rs-10681663](https://www.researchsquare.com/article/rs-10681663/latest).
Revision 3 was submitted on 7 October 2026; support processing/posting has been
requested. Public posting of v3 has not yet been confirmed. This repository
update is not evidence of journal acceptance.

MIT covers the authors' original code only. It does not relicense article
excerpts, third-party data, the manuscript or publisher templates. Component
attribution and rights notices remain in the data and original resource packages.
Current public packages exclude private annotation-export metadata and credentials.
