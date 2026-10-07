# Observable selection decomposition and influence protocol

Frozen 2026-10-06 before new decomposition, influence or project-stratified result calculations. This is a post hoc extension: all existing frozen-score and literal-count results, including the matched 72-source replication-word contrast, were already known. It is not preregistered, a confirmatory test, semantic validation or a causal analysis. Existing feature rules and source assignments remain unchanged.

## Question and scientific scope

How much of the observed difference between all-text and model-positive citation-text comparisons reflects changing filter retention versus changing distribution of the fixed visible word forms across retained and excluded texts? How concentrated is that difference across source papers and replication projects?

The unit is the source paper. The data are the archived 105-source corpus, the fixed literal-rule counts, and the same 72 sources already eligible for model-positive pre/post comparisons. No new labels, lexical choices, model calls, source decisions or corpus retrieval are used. All three existing families are carried through: possibly/perhaps/probably; six replication-word forms; and the existing lowercase-modal sensitivity. Replication words remain literal words, not failure acknowledgment or target alignment.

## Exact estimands

For source i and period t, let N+ and N− be positive/negative text counts, H+ and H− be texts with the literal family, p+=H+/N+, p−=H−/N−, q=N−/(N++N−), and pall=(H++H−)/(N++N−). The filter gap is G=p+−pall=q(p+−p−). The main shift is ΔG=Gpost−Gpre, averaged equally over sources separately in each criterion group; report negative minus positive.

On sources with at least one excluded text in both periods, define d=p+−p−. The symmetric exact decomposition is:
retention component = (qpost−qpre)(dpost+dpre)/2
stratum-distribution component = (dpost−dpre)(qpost+qpre)/2
Their sum is ΔG. These are algebraic allocations, not causal pathways. The second component mixes changes in both selected and excluded literal incidence. The first component is not estimated filter error.

If either negative stratum is empty, p− and this decomposition are unidentified. Such sources remain in the full 72-source total contrast, are individually listed, and are excluded only from the decomposition subset. Report the total contrast for both full and decomposition subsets and their exact group counts. A fixed sensitivity requires at least ten excluded texts in each period. Never fill an undefined p− with zero or infer a semantic label.

As a full-support accounting check, G=(q p+)−H−/(N++N−) is defined for all sources; report Δ(qp+) and −Δ[H−/Nall] and verify they sum exactly to ΔG. These are accounting contributions, not share/composition effects.

## Influence and project composition

For every family, report full-source contrast, each of four leave-one-project-out contrasts, each source-deletion estimate and change from full estimate, and the range of source-deletion estimates. Report all results, including sign changes and intervals containing zero. List per-source signed contributions to the group contrast without selecting favorable cases. Give the five largest absolute contributions for each family for interpretability, retaining the complete table.

Report each project's within-project contrast and group counts. If every project contains both criterion groups, standardize using equal weight to each project and separately using the pooled matched-source project proportions; bootstrap within project × criterion strata. If a group is empty, report lack of support rather than extrapolate or silently omit a project. An interval is omitted for a within-project cell containing fewer than two sources in either group. No random-effects generalization or four-project asymptotic inference is attempted.

## Timing and inclusion

Main alignment is the frozen project journal-publication year. Repeat the same-source shift for the four existing time configurations: recorded manuscript-upload year, event-year exclusion, symmetric five-year windows omitting the event year, and latest recorded text year. In each configuration use its own positive-stratum ten-per-period eligibility, report counts and its source overlap with the primary 72. This tests specification sensitivity, not causal timing. Do not add new windows, markers or eligibility rules after seeing results. The named 106-source Staunton sensitivity remains separate; no new source inclusion decision is made here.

## Uncertainty and verification

Use 19,999 percentile source-bootstrap draws with seed 20261006, independently within criterion groups; reuse the same sampled sources jointly for total and component contrasts. Bootstrap intervals condition on text retrieval, source criteria, dates, dictionary and filter decisions. For project-standardized contrasts resample separately within fixed project × criterion cells. For shared-text dependence repeat total/component summaries using the already frozen source connected-component membership; unknown citing-article dependence remains unresolved. Do not label a bootstrap tail fraction a null-test p value.

Independently verify count conservation, the 72-source/family identity against the prior outputs, equality of new full shift to the archived value, both algebraic identities at source and group levels, missing-stratum handling, source-deletion formulas, and project weights. Preserve hashes of all inputs and this protocol. No manuscript claim is updated until a separate numerical review confirms the analysis.
