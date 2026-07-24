# Published replication failures leave no trace in the language of scientific citation

**Replication package** — code and de-identified data accompanying the manuscript
*"Published replication failures leave no trace in the language of scientific
citation"* (Dongdong Guo & Jiaxuan Li, submitted to *Science Advances*).

## Overview

Does the scientific literature restate a finding more cautiously after a
registered replication fails to reproduce it? This package measures the **stated
certainty** of 15,467 citing sentences for 110 findings whose replication
outcomes were externally adjudicated by three registered replication projects
(Reproducibility Project: Psychology; Experimental Economics Replication
Project; Social Sciences Replication Project).

Each sentence is scored by a large language model in a single two-part judgment:

1. **Assertion filter** — does the sentence restate the finding's claim (as
   opposed to citing the work as a method, paradigm, dataset, or background)?
2. **Certainty score** — for assertion sentences, a continuous score
   *s* ∈ [0, 1] of how definitively the claim is stated (0 fully hedged,
   0.5 neutral, 1 definitive/causal).

Three pre-specified tests — between-group certainty level, multi-year certainty
drift, and a difference-in-differences event study around each refutation's
publication — all return bounded nulls: the language of citation is
statistically indistinguishable between refuted and replicated claims, and only
~4.7% of post-refutation restatements mention the failure. Every result is
reproduced by four independent language models (Qwen2.5-72B-Instruct,
DeepSeek-V3, DeepSeek-V4-Flash, LongCat-2.0).

## Repository structure

```
├── run_all_v3.py              end-to-end pipeline driver (retrieval → scoring → analysis)
├── analysis_v5_did.py         difference-in-differences + event-study estimation
├── rescore_multi.py           multi-model rescoring and cross-scorer report
├── ack_multiscorer.py         4-model acknowledgment-rate robustness (section S8)
├── rule_classify.py, classify.py, verify_drift.py, ...   supporting pipeline stages
│
├── v3_seeds/
│   ├── seeds_v3.csv           110-claim register: claim, project, replication label (arm)
│   └── _raw/                  provenance files from the replication projects' public data
│
├── seeds_data/                sentence-level scores, one JSONL per claim per model:
│                                scored2_v3_<claim>.jsonl      primary scorer (Qwen2.5-72B)
│                                scored_ds_v3_<claim>.jsonl    DeepSeek-V3
│                                scored_dsv4_v3_<claim>.jsonl  DeepSeek-V4-Flash
│                                scored_longcat_v3_<claim>.jsonl LongCat-2.0
│
├── out_runall_v3/             computed results (JSON): group levels, drift, DiD,
│                                event study, survivorship, multi-scorer,
│                                acknowledgment rates, summary.json
│
├── annotation_package/        human validation of the instrument (SI section S1):
│   ├── validation_protocol.md   preregistered-style thresholds and QC gates
│   ├── 标注说明.md / batch01_recut/  codebook and blinded annotation batch
│   ├── students/rater_[A-D].csv  de-identified rater exports (Label Studio)
│   └── score_batch01.py          computes κ, α, and the model–human ρ
│
└── figure_scripts/            regenerate every main-text and SI figure
```

## Data dictionary

Sentence-level records (`seeds_data/*.jsonl`, `strength_scored.jsonl`) have three
fields:

| Field  | Type        | Description                                                        |
|--------|-------------|--------------------------------------------------------------------|
| `year` | int         | Publication year of the citing paper                               |
| `s`    | float\|null | Stated-certainty score in [0, 1]; `null` for non-assertion sentences |
| `ctx`  | string      | The citing sentence (citation context)                              |

Claim-level register (`v3_seeds/seeds_v3.csv`): claim identifier, source project,
replication outcome label (`arm` ∈ {refuted, robust}), and replication statistics
from the projects' public data.

## Reproducing the results

All analyses recompute from the cached scores; **no API access is required**:

```bash
python3 analysis_v5_did.py            # DiD estimate + event-study traces (Fig. 4)
python3 rescore_multi.py --report     # per-scorer between-group nulls (Table S4, fig. S15)
python3 ack_multiscorer.py --report   # acknowledgment-rate robustness (Table S6)
python3 annotation_package/score_batch01.py \
    annotation_package/students/rater_A.csv \
    annotation_package/students/rater_B.csv   # human validation: κ = 0.65, α = 0.60, ρ = 0.42
```

Requirements: Python ≥ 3.9; `numpy` (analysis), `matplotlib` (figures only). The
human-validation script is dependency-free.

Re-scoring sentences from scratch additionally requires SiliconFlow and LongCat
API credentials, read from the environment (`SILICONFLOW_API_KEY`,
`LONGCAT_API_KEY`) or from `~/.siliconflow_key` / `~/.longcat_key`. **No
credentials are stored in this repository.** Scoring is checkpointed per sentence
and resumable; temperature is 0 throughout.

## Scoring instrument

The two-part scoring prompt (assertion + certainty) is identical across all four
models and is reproduced verbatim in the paper's Supplementary Text (S1b), as is
the acknowledgment prompt (S8). The scorer receives only the sentence text — never
the cited claim's identity, its replication status, or the citing paper's year —
so it is blind to group membership by construction.

## Data provenance and licensing

| Component | Source | Terms |
|---|---|---|
| Citing sentences (`ctx`) | [Semantic Scholar Academic Graph](https://www.semanticscholar.org/product/api) | Redistributed with attribution under ODC-BY; sentence excerpts remain subject to their original publishers' copyright |
| Replication outcomes | Public data of OSC (2015), Camerer et al. (2016, 2018), as compiled by Serra-Garcia & Gneezy (2021) | Public research data |
| Analysis code | This repository | MIT License |

## Human-subjects statement

The only human-subjects data are sentence-level ratings produced by trained
annotators during instrument validation (`annotation_package/`). All rater data
are de-identified: files carry arbitrary codes (`rater_A`–`rater_D`) and contain
no names, contact details, demographics, affiliations, or other personal
identifiers.

## Citation

Guo, D. & Li, J. *Published replication failures leave no trace in the language
of scientific citation. Full citation details
will be added upon publication.
