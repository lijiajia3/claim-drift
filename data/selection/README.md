# Citation text selection composition extension

This standalone extension reproduces a post hoc descriptive analysis of the same frozen 105-source citation-text archive used in the companion Scientometrics revision. It adds an exact decomposition of the previously reported matched-source filter contrast and complete source, project, timing and minimum-support checks. It uses no new model scores or human labels.

The central result concerns literal replication-word incidence. The matched 72-source contrast is −1.553 percentage points, with −0.233 points allocated to the retention-share term and −1.320 points to the changing retained-versus-excluded incidence difference. This is an algebraic description of the text subset, not a causal mechanism or acknowledgment classifier. RPP dominates the eligible sample; omitting RPP, narrowing to five-year windows, or requiring ten excluded texts per period weakens the precision. All three fixed marker families and all specified checks are retained.

Read SELECTION_DECOMPOSITION_REPORT.md for the scientific result, qualifications and proposed manuscript wording. SCIENTIFIC_FEASIBILITY_REVIEW.md explains the narrower contribution and remaining publication risk. The frozen protocol preceded the new decomposition/influence comparisons but followed earlier score and lexical results; it is not preregistration.

## Reproduce

Python 3.12 with numpy 2.3.5 and pandas 2.2.3 was used. In a suitable environment with these dependencies installed, run:

    bash run_all.sh

Or run the listed Python scripts separately. Analysis writes selection_outputs/ and compares its numeric tables against the immutable reference_outputs/. The independent reviewer implementation reconstructs counts and identities separately, without importing the production analysis. Its exact endpoint comparison uses independently reconstructed data and the specified draw streams. Tests cover arithmetic identities, empty excluded strata and minimum positive support. No network, credentials, GPU or model API is required.

## What is included

- inputs/: previously frozen aggregate word counts by source/year/filter decision, source metadata and exact-text-sharing group membership
- previous/: prior source-level aggregate estimates and matched filter results needed for identity and timing cross-checks
- reference_outputs/: verified new estimates, component intervals, source support, every influence and timing result, and hashes
- independent_review/: independent implementation, comparisons and verification report
- external_annotation_feasibility/: metadata-only review of the existing Hardwicke et al. 2021 human-coded data. Its label task and missing linkage prevent a current external evaluation; no label comparisons were conducted. Raw third-party annotation tables and text are not included

No raw citation sentences, individual human annotations or credentials are distributed here. Aggregate input hashes are recorded in reference_outputs/method.json. Source provenance follows the companion source-confirmed study archive. The added code and report do not alter any source criterion, lexical rule, historical score or source text.

## Important interval distinctions

The original lexical analysis used bootstrap seed 20261005. This extension froze seed 20261006 for its jointly resampled component estimates. Point estimates match exactly; small interval-endpoint differences are documented Monte Carlo differences. For standardized project summaries, conditional audit intervals are retained only in explicitly named audit columns. Manuscript-facing intervals are suppressed because one project-criterion cell contains a single source. Read INTERVAL_DISPLAY_CLARIFICATION.md.

## Attribution

The external feasibility review cites Hardwicke et al. (2021), https://doi.org/10.1177/25152459211040837, and their OSF registered archive https://osf.io/gyzbm/ under CC BY 4.0 as stated by the deposit. This extension does not redistribute their row-level labels or publisher quotations. Literal-word rules, source labels, and archived model outputs are inherited unchanged from the companion study materials; the protocol and report make no claim of new semantic validation.

All implementation and independent computational checks were AI-assisted. They are numerical verification, not external human peer review. Human authors remain responsible for the manuscript and submission decisions.
