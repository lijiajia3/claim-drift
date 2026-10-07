# Independent verification

## Verified scope

Independent aggregate-data reconstruction and numerical review of the frozen post hoc selection decomposition. No raw text or individual annotations are required. See `VERIFICATION_REPORT.md` for the signed interpretation limits and complete verdict.

## Run in the original workspace

From the workspace root:

```sh
python twenty_hour_revision/no_label_reassessment/independent_review/verify_selection_decomposition.py
python twenty_hour_revision/no_label_reassessment/independent_review/compare_production_outputs.py
python twenty_hour_revision/no_label_reassessment/independent_review/write_verification_report.py
```

## Run in a standalone extension bundle

Both verification scripts accept `--extension-root /absolute/path/to/extension`. It defaults to their parent extension folder. They prefer the bundle's `inputs/` and `previous/` directories. Without those directories they fall back to the original adjacent `scientometrics_analysis/lexical/` layout. Outputs are written to the selected extension's `independent_review/` folder.

The extension root must contain:

- `SELECTION_DECOMPOSITION_PROTOCOL.md`
- `analyze_selection_decomposition.py`
- `inputs/literal_counts_by_source_year.csv`
- `inputs/source_cohort.csv`
- `inputs/shared_text_component_membership.csv`
- `previous/matched_source_filter_estimates.csv`
- `previous/matched_source_filter_comparison.csv`
- `previous/source_estimates_all_predefined_features.csv`
- `previous/analysis_configurations.json`
- The regenerated `selection_outputs/` directory, for cross-comparison

Python 3.10+ and NumPy/Pandas are required. No external network access, model service, API credential, package beyond NumPy/Pandas, or raw-text file is used.

Run the production analysis first, then the independent reconstruction, then the cross-comparison. `write_verification_report.py` optionally rebuilds the narrative report from the tables in its own parent extension folder.

```sh
python /path/to/extension/analyze_selection_decomposition.py
python /path/to/extension/independent_review/verify_selection_decomposition.py --extension-root /path/to/extension
python /path/to/extension/independent_review/compare_production_outputs.py --extension-root /path/to/extension
```

## Output interpretation

- `independent_checks.json`: count, archive-identity, exact-rational algebra, timing, bootstrap-additivity, deletion and weighting checks
- `production_comparison_checks.json`: independent source/summary comparison and exact production-RNG stream replay; also records audited production hashes
- `independent_hashes.json`: frozen input/protocol/archive hashes and independent verifier hash
- `independent_*.csv`: complete reconstructed source estimates, support, influence, timing, and bootstrap outputs
- `verification_run.log`: readable summary from the standalone reconstruction

The standalone reconstruction uses a distinct deterministic draw batching order, and its percentile endpoints can differ slightly despite the same seed and number of draws. `compare_production_outputs.py` independently replays the production ordering through weighted-frequency calculations; this verifies the exact production intervals without importing or executing the production analysis implementation.

In particular, standardized bootstrap intervals are computationally conditional on a singleton ML1 criterion-negative cell and are not fit to display as ordinary manuscript uncertainty intervals. Production outputs correctly retain only an audit-conditional version and suppress the manuscript-facing CI columns.
