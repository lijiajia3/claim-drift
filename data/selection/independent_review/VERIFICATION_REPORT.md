# Independent numerical verification: observable selection decomposition

## Verdict

PASS for the frozen descriptive analysis, with the singleton-project uncertainty limitation explicitly retained. Independent aggregate-data reconstruction passed 5,652 checks; a separate comparison passed 292 checks against the production artifacts, including exact replay of their bootstrap intervals. No numerical correction is required. This is a numerical approval of the specified descriptive accounting, not semantic validation, a causal finding, or evidence of population-wide reproducibility.

The protocol SHA256 is 167f2ce696b06d0f0608b94040a85a22ecb0d2113bd99294db7956e60b42863e, verified unchanged. The conceptual review was sent before new results were inspected: both algebraic identities are sound; empty excluded strata must remain undefined; component resampling must preserve memberships spanning criterion groups; subset contrasts need their own group denominators. Signed allocations should not be turned into causal attribution percentages.

## Independence and reproducibility

- `verify_selection_decomposition.py` reconstructs all estimates from the three frozen input CSVs, without importing or executing the production script. It uses integer counts and exact rational arithmetic for source-level algebra, followed by independently implemented source, project-stratified, and whole-component bootstraps
- `compare_production_outputs.py` compares every eligible source × family × timing cell, the aggregate contrasts, all 216 source-deletion estimates and signed contributions, all project calculations, and the timing counts. Bootstrap endpoints are replayed through frequency-weight matrices using independently reconstructed data, rather than the production code's indexed-array implementation
- `independent_checks.json` and `production_comparison_checks.json` contain machine-readable results. `independent_hashes.json` preserves the input, protocol, archive and independent-script hashes. The comparison report also preserves the audited production script/output hashes
- Both implementations use 19,999 draws and seed 20261006. The standalone reconstruction uses a different deterministic RNG batching order; its Monte Carlo percentile endpoints may differ slightly. The separate stream replay matches every audited production endpoint within 2 × 10⁻¹⁴, eliminating RNG-order differences as an apparent numerical discrepancy
- A copied, isolated standalone bundle reran both verifier scripts successfully with the same 5,652 reconstruction and 292 cross-comparison checks; `standalone_smoke_test.json` records that portability check
- All outputs are aggregate counts or source-summary statistics. No raw text, new markers, human labels, model calls, external contact, or additional corpus decisions were used

## Counts, support and identities

The archived corpus contains 105 sources, 15,280 full-view texts and 8,427 model-positive texts. Per-source full-text and positive counts match the source cohort. Aggregate rows have unique keys, nonnegative integer counts, context-family hits bounded by text denominators, token-family sums equal to the frozen member-word sums, and valid context-union bounds. This review does not independently re-extract lexical matches from raw texts.

The primary comparison has exactly the archived 72 sources and the same identities for all three marker families: 40 criterion-negative and 32 criterion-positive. Every primary source has at least one excluded text in both periods, so the full and nonempty-excluded decomposition subsets coincide. The nondecomposable output is correctly a header-only table. The fixed ten-excluded-per-period sensitivity has 59 sources: 32 negative and 27 positive.

For every eligible source, family and timing configuration, the full-support identity is verified exactly from rational counts. On supported strata, the product identity G = q(p+ − p−) and the symmetric retention-plus-stratum identity are exact. Group identities and shared-resample bootstrap identities agree to numerical precision. Actual data do not exercise an empty excluded cell; source-code inspection verifies NaN rather than zero imputation, and independent rational synthetic edge checks verify that the full-support identity remains defined when an excluded cell is absent.

## All three fixed families

All estimates below are proportions; multiply by 100 for percentage points. Direction is criterion-negative minus criterion-positive. These are production percentile intervals verified independently.

### Full 72-source filter-gap shifts

| feature | n_negative | n_positive | estimate | ci95_low | ci95_high |
| --- | --- | --- | --- | --- | --- |
| epistemic_adverb_tokens | 40 | 32 | -0.000761 | -0.007169 | 0.005316 |
| replication_word_tokens | 40 | 32 | -0.015529 | -0.030437 | -0.002075 |
| lowercase_modal_tokens | 40 | 32 | -0.010933 | -0.033622 | 0.013440 |

The replication-word value reproduces the known −0.015529040486321564 exactly to floating precision. Its source-bootstrap interval is negative, while the other two full-sample intervals include zero.

### Symmetric components, all 72 sources

| feature | metric | estimate | ci95_low | ci95_high |
| --- | --- | --- | --- | --- |
| epistemic_adverb_tokens | retention_component | 0.000737 | 0.000026 | 0.001538 |
| epistemic_adverb_tokens | stratum_distribution_component | -0.001498 | -0.008021 | 0.004549 |
| replication_word_tokens | retention_component | -0.002326 | -0.004104 | -0.000772 |
| replication_word_tokens | stratum_distribution_component | -0.013203 | -0.026872 | -0.000645 |
| lowercase_modal_tokens | retention_component | 0.001675 | -0.002214 | 0.005811 |
| lowercase_modal_tokens | stratum_distribution_component | -0.012608 | -0.035127 | 0.011821 |

For replication words, the retention component is about −0.233 percentage points and the stratum-distribution component about −1.320 percentage points. Their sum is the −1.553-percentage-point filter-gap shift. The stratum-distribution term combines changes in both retained and excluded literal incidence. Neither term is an estimate of filter accuracy, human acknowledgment, target alignment, or a causal mechanism.

### Full-support accounting contributions

| feature | metric | estimate | ci95_low | ci95_high |
| --- | --- | --- | --- | --- |
| epistemic_adverb_tokens | account_retained_weight | -0.000223 | -0.004426 | 0.004300 |
| epistemic_adverb_tokens | account_excluded_incidence | -0.000539 | -0.005690 | 0.003688 |
| replication_word_tokens | account_retained_weight | -0.009211 | -0.020844 | 0.001228 |
| replication_word_tokens | account_excluded_incidence | -0.006318 | -0.018316 | 0.005510 |
| lowercase_modal_tokens | account_retained_weight | -0.004577 | -0.024947 | 0.016141 |
| lowercase_modal_tokens | account_excluded_incidence | -0.006356 | -0.022434 | 0.010236 |

These two alternative accounting contributions sum to each total; they are not the symmetric retention/distribution components and should not receive those names. Individual component interval endpoints need not sum to the interval endpoints of the total, because quantiles are nonlinear. The sampled values, rather than marginal endpoints, are verified to add.

### Ten-excluded-per-period sensitivity

| feature | n_negative | n_positive | estimate | ci95_low | ci95_high |
| --- | --- | --- | --- | --- | --- |
| epistemic_adverb_tokens | 32 | 27 | 0.000999 | -0.003986 | 0.006353 |
| replication_word_tokens | 32 | 27 | -0.014438 | -0.031295 | 0.000359 |
| lowercase_modal_tokens | 32 | 27 | -0.004591 | -0.029601 | 0.021973 |

The replication-word source-bootstrap interval now includes zero. Under the separate frozen-component bootstrap, its total interval remains narrowly negative, but the stratum-distribution interval includes zero. Both uncertainty summaries must be reported without selecting the more favorable one.

## Influence and project structure

Every source-deletion estimate was checked both by direct recomputation and an analytic group-denominator formula. Full signed contributions sum to the full contrast and are distinct from changes caused by deletion, which also renormalizes a group. All top-five contributor identities and deletion extrema match the complete production table.

| feature | min_source_deletion | max_source_deletion |
| --- | --- | --- |
| epistemic_adverb_tokens | -0.001859 | 0.001202 |
| replication_word_tokens | -0.017136 | -0.011882 |
| lowercase_modal_tokens | -0.017004 | -0.008136 |

The replication-word contrast stays negative after deletion of any one source. Its five largest absolute signed contributions are rpp.68, rpp.63, rpp.27, rpp.158, and rpp.52, all RPP sources. The adverb contrast changes sign after at least one source deletion; this is retained in the complete output.

The within-project group sizes are EERP 4/6, ML1 1/4, ML3 4/2, and RPP 31/20 (negative/positive). Replication-word results:

| project | n_negative | n_positive | estimate | ci95_low | ci95_high |
| --- | --- | --- | --- | --- | --- |
| EERP | 4 | 6 | -0.016879 | -0.042073 | 0.007544 |
| ML1 | 1 | 4 | 0.002207 | omitted | omitted |
| ML3 | 4 | 2 | -0.005573 | -0.018133 | 0.003351 |
| RPP | 31 | 20 | -0.020479 | -0.039818 | -0.003438 |

| omitted_project | n_negative | n_positive | estimate | ci95_low | ci95_high |
| --- | --- | --- | --- | --- | --- |
| EERP | 36 | 26 | -0.016461 | -0.032715 | -0.001822 |
| ML1 | 39 | 28 | -0.017192 | -0.032717 | -0.003158 |
| ML3 | 36 | 30 | -0.016625 | -0.032910 | -0.002240 |
| RPP | 9 | 12 | -0.007007 | -0.023896 | 0.009036 |

Dropping RPP reduces the estimate to about −0.701 percentage points and yields an interval crossing zero. Within ML1 the sign is positive, although the negative group has one source. Therefore these results do not justify a claim of uniform project-level evidence or independence from project composition.

The project-standardized replication-word estimates are −0.010181 for equal project weights and −0.017161 for pooled matched-source project weights. Pooled weights are exactly 10/72, 5/72, 6/72 and 51/72 for EERP, ML1, ML3 and RPP. Every project has both groups, so these point estimates are supported. Project-stratified resampling correctly preserves each fixed project × criterion cell, but ML1's negative singleton cannot estimate within-cell variation. Its direct within-project interval is omitted. Following independent review, all manuscript-facing standardized intervals are also suppressed; the original computational intervals remain only in explicitly named audit-conditional columns with a singleton warning. This conservative display correction does not change any point estimate, sample, bootstrap draw or frozen protocol. No four-project random-effects inference is supported.

## Shared-text dependence

The component bootstrap correctly samples the entire frozen graph of 89 connected components jointly, carrying all eligible members of each selected component across criterion groups. It does not split cross-group components. Of the frozen components, 59 contain a primary eligible source and 48 contain a source in the ten-excluded sensitivity. Components with no eligible source remain in the fixed sampling frame. All 19,999 draws have nonempty criterion denominators. The production full replication-word interval is [−0.030842, −0.002927]. The independent weighted-frequency replay matches its endpoints and every total/component summary. This addresses the archived shared-text links only; unknown citing-article dependence remains unresolved. It does not produce a project-level superpopulation interval.

## Timing and eligibility

The primary split is before journal event year versus event year and later. Event omission excludes the event year; the symmetric window includes event−5 through event−1 and event+1 through event+5. The latest-year configuration uses the recorded latest year per aggregate cell. Each configuration independently reapplies the ten-positive-texts-per-period threshold. All pre/post counts, family hits, and eligible source identities match the archived timing tables.

| cohort | n_negative | n_positive | n_sources_also_in_primary72 | n_sources_not_in_primary72 | estimate | ci95_low | ci95_high |
| --- | --- | --- | --- | --- | --- | --- | --- |
| journal | 40 | 32 | 72 | 0 | -0.015529 | -0.030437 | -0.002075 |
| recorded_manuscript_upload_years | 39 | 32 | 71 | 0 | -0.015548 | -0.030199 | -0.002114 |
| omit_event_year | 39 | 31 | 70 | 0 | -0.019661 | -0.035459 | -0.005278 |
| symmetric5_years_omit_event_year | 35 | 26 | 61 | 0 | -0.015227 | -0.034610 | 0.001309 |
| latest_archived_year | 40 | 32 | 72 | 0 | -0.015542 | -0.030421 | -0.002139 |

The alternative configurations retain 71, 70, 61 and 72 sources respectively; all are subsets of the primary 72 with no additions. The five-year interval includes zero. Changes across configurations can reflect both timing and eligibility/sample composition, so they should not be attributed solely to event dating. Full source-overlap membership tables are preserved independently. The named 106-source Staunton sensitivity is untouched and remains separate.

## Scope of numerical approval

The verified result is an observable, source-weighted, post hoc description of how a fixed model-positive filter changes a fixed literal-word comparison, plus exact algebraic allocation and influence diagnostics. It conditions on archived retrieval, criterion assignments, dates, dictionary rules and model decisions. It supplies neither semantic ground truth nor a human-scale validation, and no bootstrap tail fraction is called a null-test p value. Point estimates and signed components should not be presented as causal effects or estimated filter error.
