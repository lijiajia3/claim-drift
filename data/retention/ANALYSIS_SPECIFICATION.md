# Analysis specification and interpretation

This is the publication-facing record of the post hoc retention benchmark, prepared after computation. It preserves the fixed statistical specifications while omitting operational coordination records. Earlier outcome results were known when the reference analysis was designed; it is not preregistered or confirmatory.

## Population and observed quantity

Use the unchanged 72-source matched corpus (40 criterion-negative and 32 criterion-positive source papers), 11,999 archived exact-text units, and 6,650 Qwen-retained texts. Source papers have equal weight within groups. Project-journal alignment years are RPP 2015, EERP 2016, ML1 2014 and ML3 2016. Pre is year less than the event year; post is year at or after it. Keep all sources fixed across reference draws.

Use all three frozen full-text literal-family indicators: possibly/perhaps/probably; replicate/replicates/replicated/replicating/replication/replications; lowercase may/might/could under the established exclusions. No synonyms, semantic labels, word selection, eligibility thresholds or model outputs are newly fitted.

Within each source-period, the filter gap is retained-text incidence minus all-text incidence. Compute its post-minus-pre change, then subtract the mean change in criterion-positive sources from the mean change in criterion-negative sources. This observed differential shift is the estimand, not a causal difference-in-differences parameter.

## Reference selection schemes

Draw uniformly without replacement exactly the observed number retained in every stratum:

1. Source paper x pre/post period
2. Source paper x exact archived year
3. Source paper x exact archived year x pre-existing character-length band: 0-69, 70-350, 351-700, 701-1200, >=1201

The third is the most constrained prespecified benchmark. Keep empty-selection and full-selection strata deterministic. Do not merge small strata or move length boundaries. Each scheme preserves source-period retained denominators. Sample the joint eight-pattern distribution of three binary family indicators, so marker co-occurrence is preserved. Use 19,999 draws per scheme in order, NumPy PCG64 seed 2026100602.

For a stratum with N texts, H marker hits and K retained, the expected retained hits are K H/N; the variance is K(H/N)(1-H/N)(N-K)/(N-1), with zero variance for deterministic strata. Sum expectations within source-period, divide by fixed retained denominators and apply the observed estimator's source/group signs. The volume-only expected shift is exactly zero; the other expectations need not be zero.

## Complete reporting

Report all nine family/scheme rows: observed shift, exact reference expectation, observed-minus-expected residual, simulated central 95% reference envelope and analytical/simulated standard deviations. Retain every family, regardless of its result. Report source and criterion-group pre/post incidences, every project's most-constrained residual and every leave-project-out residual. Report randomizable strata/text/hit support and deterministic cells.

No new significance test, p value, optimal threshold, equivalence claim or favorable family/scheme selection is performed. No percentages are called causally explained shares. The reference envelope is not a confidence interval for the observed residual or a population effect. Retain old source-bootstrap intervals separately and label the different resampling object.

## Simulation precision and substantive limits

After observing a near-boundary endpoint, compute numerical binomial/order-statistic brackets for both endpoints of all nine envelopes from the same saved draws. These brackets assess numerical percentile precision only. The most-constrained replication-word lower-endpoint bracket includes the observed value; the raw outside-envelope flag is therefore not robust evidence of departure.

The most constrained matching already reproduces the within-criterion-negative direction reversal. Residual differences describe association with text features not preserved by the matching margins. They do not show that the gate made semantic errors, that authors ignored contrary evidence, or that replication publication caused a response. Missing citing-article/version identities, purposive source sampling, the retrospective question and limited project support remain limitations.
