# Finite-corpus citation-text retention benchmark

This portable supplement reproduces a bounded, post hoc comparison of a frozen empirical-restatement gate with reference subsets preserving retained volume, publication-year composition and context-length composition. It contains no model API calls, raw citation text or human annotation values.

## Main result

Across the same 72 source papers, the replication-word filter shift is -1.553 percentage points. A reference subset matching retained source-period counts has expectation zero. Matching archived year as well gives -0.503 points; adding the fixed context-length bands gives -0.651 points, leaving an observed-minus-expected residual of -0.902 points.

The most constrained observation lies near the lower reference-envelope boundary. Its nominal outside-envelope flag is sensitive to Monte Carlo endpoint precision and is not strong confirmatory evidence. Matching already reproduces the within-criterion-negative change from a positive all-text trend to a negative retained-text trend. No semantic classification error or causal response follows from these calculations.

## Reproduction

Tested with Python 3.12.14 and NumPy 2.3.5. Run `python reproduce.py`. The script writes `reproduced_results/` and checks all six main analysis CSVs byte-for-byte against the reported versions. Simulation output is also saved as three NumPy arrays. The exact random stream is NumPy PCG64, seed 2026100602, 19,999 draws per scheme. Other NumPy versions may change byte-level simulation behavior.

No data download or credentials are required. The input contains 11,999 text-free rows and 72 source-paper records, with original archived assertion flags, literal-family indicators, years, lengths and provenance hashes. Original text is not included. The existing literal-token function is provided to document the unchanged feature definitions; numerical replay uses the frozen derived indicators.

## Files

- `ANALYSIS_SPECIFICATION.md`: publication-facing method record and interpretation limits
- `inputs/`: text-free row/source data for replay
- `benchmark_core.py`, `reproduce.py`: calculation and portable reproduction entrypoint
- `literal_features.py`: original fixed literal-feature implementation
- `reported_results/`: complete nine-row benchmark, all source/group/project results, support accounting and figure
- `verification/`: independent analytical checks, joint-covariance checks, toy checks and all 18 simulation-endpoint precision brackets
- `MANIFEST.json`: checksums for all included files

The reported source-bootstrap intervals are in their own labeled table. They quantify source resampling conditional on the archived pipeline. The blue intervals in the reference-envelope figure quantify an artificial finite-corpus subsampling distribution. The two must not be interpreted interchangeably.

## Design provenance

The reference-analysis specifications were fixed before its calculations on 2026-10-06, after the original score, literal-family, matched-filter, decomposition and influence results were known. The study is consequently an outcome-informed, transparent post hoc extension, not a preregistration or an independent replication. The publication-facing specification was prepared after calculation and does not purport to be an untouched preregistration record.

Independent verification checked exact rational expectations, joint covariances, source masks and margins, and exhaustive toy selection distributions. All six main numerical tables and three saved simulation arrays reproduced byte-for-byte. Following a borderline reference endpoint, numerical precision brackets were added for both endpoints of every scheme/family combination, with no new seed, extra draws, corpus changes or scientific tests.
