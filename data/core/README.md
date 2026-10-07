# Scientometrics: cleaned numerical checkpoint

This package provides the revised numerical analysis, editable figures and aggregate measurement results for author review. It contains no citation text, individual human labels, annotation identities, receipt records, private correspondence or signed download links. It is not a claim that the study is ready for publication.

## What the results support

The conservative source-paper baseline has 105 source papers, 15,280 distinct citation-text units and 8,427 model-filtered empirical-language units. The primary comparisons are source-level associations on the frozen model-score scale. They do not establish response to the exact replicated proposition, authors' beliefs or causal self-correction.

Main alignment uses project journal-publication years. Recorded manuscript-upload years are a separate sensitivity; historical timestamps do not certify the contents of every historical results file or author awareness.

Read RESULTS_AND_LIMITATIONS.md, then see outputs/primary_contrasts.csv. Figures are supplied as editable SVG plus PDF and PNG, with captions. The unresolved source cases remain explicit in the ledger and exhaustive label-assignment outputs.

## Offline numerical replay

Python 3.12 and the packages in requirements.txt were used for verification. Once dependencies are installed, no network or model call is needed:

    bash run_all.sh

The main inputs are 8,124 aggregate cells. Each cell contains a frequency and the numeric fields needed to reproduce all score, timing and eligibility rules. They omit text and item hashes. Shared-text dependence is represented only by sets of source-paper identifiers, without the shared text or its hash.

The cleaned representation reproduces the validated main estimates, intervals, timing and label sensitivity tables, trajectories and precision simulations exactly. Source-level identifiers and DOI/title metadata describe published papers, not individual annotators.

## Measurement results and optional local replay

measurement/ contains aggregate reliability, development agreement, calibration and score-repeatability summaries. No raw human annotation file is included.

To recompute human reliability, development ensemble agreement and the main full-run measurement-error interaction, point the script at the unchanged original author archive:

    python src/recompute_measurement_from_original.py --original-archive /path/to/replication_package_2026.10.04-v1 --out measurement_recomputed

The script reads the original key, two rating files, frozen scores and source linkage locally. It writes aggregate results only. It does not read receipt reports or write annotation metadata, text, task IDs or individual labels. This local replay was tested against the original archive and reproduced the reference aggregate results exactly.

Other aggregate summaries supplied here remain descriptive evidence from the same reused labeled sample. None is an independent held-out certainty test, and no new human labels were created.

## Key files

- inputs/analysis_ledger.csv: source IDs, DOI/title, explicit criterion labels, eligibility and date conventions
- inputs/numeric_cells.csv: frequency-weighted numeric cells used in the replay
- outputs/primary_paper_estimates.csv: source-level estimates and eligibility
- outputs/sensitivity_grid.csv: component, date, text-format, window, threshold and project diagnostics
- outputs/ambiguous_label_all_assignments.csv: all allocations of the three unresolved cases
- outputs/precision_and_tost_grid.csv: explicitly illustrative model-scale bounds
- outputs/hypothetical_precision_simulation.csv: stipulated-effect calculations, not achieved power
- figures/figure_captions.json: complete methodological captions
- VALIDATION.json: reproducibility checks for this cleaned representation

This is an author-facing reproducibility checkpoint. Decisions about journal submission, rights and public redistribution remain separate.

## Source metadata version 2.2

The source metadata now separate journal issue dates, verified first-online dates and other publication milestones. RPP first-online remains unverified; its 2015-08-28 milestone is journal publication. Obsolete ML3 campus-only wording has been removed. These metadata corrections leave all analysis IDs, source criteria, inclusion flags, event years, context counts and numerical estimates unchanged. See inputs/project_event_registry_v1.csv for the typed date evidence.

## Supplementary literal-language and source-scope checks

The lexical/ folder adds frozen, narrow literal-word observables and full Qwen-retention accounting. It is supplementary triangulation, not an independent certainty measure or a classifier of target-specific acknowledgment. The original score prompt overlaps with the word list. Read lexical/LITERAL_DIAGNOSTIC.md for exact denominators, source intervals and limits.

The105-source main baseline remains unchanged. A separately defined106-source sensitivity adds only RPP73’s archived Staunton-selected positive contrast. Read lexical/RPP73_SCOPE_SENSITIVITY.md. This is an explicit scope choice; it does not imply the selected statistic is unknown or impose an undisclosed aggregation across sites.

Source metadata are v2.3; the underlying105 numerical estimates remain unchanged.
