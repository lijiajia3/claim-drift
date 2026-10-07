from pathlib import Path
import pandas as pd, json
R=Path(__file__).resolve().parents[1]/'results/selection';O=R
d=pd.read_csv(O/'source_bootstrap_components.csv').query("cohort=='nonempty_negative_each_period'")
labels={'epistemic_adverb_tokens':'Three adverbs','replication_word_tokens':'Replication-word forms','lowercase_modal_tokens':'Lowercase modals (sensitivity)'}
rows=[]
for f in labels:
 row={'Observable':labels[f]}
 for k,t in [('filter_shift','Total filter shift'),('retention_component','Retention-share component'),('stratum_distribution_component','Stratum-distribution component')]:
  q=d[(d.feature==f)&(d.metric==k)].iloc[0]
  row[t]=f"{q.estimate*100:+.3f} [{q.ci95_low*100:+.3f}, {q.ci95_high*100:+.3f}]"
 rows.append(row)
pd.DataFrame(rows).to_csv(O/'editorial_decomposition_table_pp.csv',index=False)
text='''# Selection decomposition and scientific use

## Result and contribution

The frozen empirical-restatement filter changes the distribution of visible replication vocabulary in the project-aligned citation-text comparison. Its matched-source difference is not accounted for by the proportion of text retained alone: most of the signed decomposition lies in the changing distribution of replication-word forms between retained and excluded texts. This is an observable property of this archive and filter. It is not a semantic assessment of acknowledgment or a filter-error rate.

The exact comparison is limited to 72 source papers already eligible for the original positive-text event analysis, with 40 criterion-negative and 32 criterion-positive papers. They contribute 4,812 pre-event and 7,187 post-event text units. Every source has at least one excluded text in both periods, so the predeclared symmetric decomposition uses the same 72 papers as the existing matched result. All three previously fixed lexical families are retained.

This adds scientific value by distinguishing two possible sources of a conditional citation-text comparison and checking its concentration. It does not make the original certainty score a measure of target-specific response. Nor is the algebra itself a new method. The defensible contribution is a bounded empirical citation-text case study showing why stability of an overall text-retention rate cannot, by itself, establish stability of the textual material being compared.

## Exact identity and scale

For each source and period, p+ is the literal-family incidence among retained texts, p− is its incidence among excluded texts, q is the excluded proportion, and pall is its incidence among all texts. The positive-minus-all gap is G = p+ − pall = q(p+ − p−). Write d = p+ − p−. Its pre/post change decomposes exactly into:

- Retention-share component: (qpost − qpre) × (dpost + dpre)/2
- Stratum-distribution component: (dpost − dpre) × (qpost + qpre)/2

Their sum is Gpost − Gpre. We compute each source's components first, then equally average them within each criterion group and subtract criterion-positive from criterion-negative. Products of group means are not substituted for source-level products. The components are symmetric algebraic allocations, not causal pathways. Signed components may cancel; do not call their ratios percentages explained.

## Complete component estimates

Values below are percentage points. Brackets are 95% percentile source-bootstrap intervals from 19,999 joint draws, seed 20261006. All fixed labels, dates, text and matching rules are held constant. The previous matched result used seed 20261005; its point estimate is reproduced exactly, and small differences between interval endpoints reflect the documented Monte Carlo stream, not a changed sample or estimator.

| Observable | Total filter shift | Retention-share component | Stratum-distribution component |
|---|---:|---:|---:|
'''
for r in rows:text+='| '+' | '.join(r.values())+' |\n'
text+='''
The main replication-word shift is −1.553 percentage points, comprising −0.233 points from the retention-share component and −1.320 points from the stratum-distribution component. On criterion-negative sources, equal-paper incidence rises from 2.09% to 2.45% across all text but falls from 2.69% to 1.52% among retained text. Excluded-text incidence rises from 1.37% to 3.21%. These are source-weighted descriptive rates, not pooled prevalence estimates or semantic recognition rates.

The three-adverb family remains sparse. Its total filter-shift interval and distribution-component interval include zero. Its small retention-component interval excludes zero under individual-source resampling but includes zero under the known text-sharing component sensitivity; it is not a robust isolated finding. Both modal component intervals include zero. Retaining every family is essential to avoid promoting only a favorable interval.

## Concentration and support

- Deleting any single source leaves the replication-word point estimate negative, ranging from −1.714 to −1.188 percentage points. The most influential single deletion is rpp.68, with a 0.365-point change in the estimate
- RPP supplies 51 of the 72 sources. Omitting it reduces the shift to −0.701 points, with interval −2.390 to +0.904. Omitting EERP, ML1 or ML3 yields respectively −1.646, −1.719 and −1.663 points. All four leave-project analyses are reported
- The RPP within-project estimate is −2.048 points [−3.982, −0.344]. Other projects are small: EERP has 4 negative and 6 positive sources; ML1 1 and 4; ML3 4 and 2. The ML1 point estimate is +0.221 points. No interval is assigned to its singleton negative cell
- Equal-project standardization gives −1.018 points; weighting projects by their pooled share of the 72 sources gives −1.716 points. Manuscript-facing intervals are suppressed because project-by-criterion resampling leaves the ML1 singleton fixed. Conditional computational intervals remain in explicitly labeled audit columns
- Requiring at least ten excluded texts in each period leaves 59 sources (32 negative, 27 positive), with shift −1.444 points [−3.130, +0.036]. Its retention and distribution components are −0.221 and −1.222 points
- Shared exact-text component resampling gives the total replication-word interval [−3.084, −0.293], retention interval [−0.418, −0.074], and distribution interval [−2.728, −0.147] points. It accounts only for known exact-text sharing, not unknown shared citing articles

## Timing checks

Every previously specified timing convention is retained. Recorded manuscript-upload alignment has 71 sources and shift −1.555 points [−3.020, −0.211]. Omitting the event year has 70 sources and −1.966 [−3.546, −0.528]. A symmetric five-year window omitting that year has 61 sources and −1.523 [−3.461, +0.131]. Using the latest archived text year retains 72 sources and gives −1.554 [−3.042, −0.214]. These are alternative corpus partitions, not dates of author exposure or causal responses. The five-year interval and the RPP omission interval spanning zero belong in the main interpretation.

## Manuscript wording proposal

To examine why conditional text comparisons differed, we decomposed each source's retained-minus-all incidence gap into the excluded share and the retained-minus-excluded incidence difference. The symmetric pre–post decomposition used the same 72 sources as the paired comparison. For replication-word forms, the criterion-negative-minus-positive filter shift of −1.55 percentage points comprised a −0.23-point retention-share component and a −1.32-point stratum-distribution component. No single-source deletion reversed its sign, but RPP supplied 51 sources and omitting that project reduced the contrast to −0.70 points with an interval spanning zero. The symmetric five-year-window interval also spanned zero. These results describe the composition of the frozen text subset; they do not establish misclassification, acknowledgment of contrary evidence or a causal effect of replication publication.

## Reporting guardrails

1. Foreground the observable question and full denominator accounting, not the old null model-score result
2. Keep all three fixed families in the main comparison and retain source/project/timing heterogeneity alongside the replication-word estimate
3. Explicitly state that the lexical analysis and its promotion into a main descriptive question are post hoc. The original frozen-score results were known before lexical rules were fixed; no prospective hypothesis claim is justified
4. Retain the score as a secondary policy-defined indicator. Its special failed-replication cap and categorical-rejection exception prevent a single monotonic semantic interpretation. Lexical agreement would be partly induced by those instructions
5. Do not claim that adding this decomposition repairs target alignment, citing-paper provenance, model development reuse, moderate human reliability or project-event causal identification
6. Do not imply that unavailable new raters preclude every honest paper. They preclude the stronger semantic and target-specific claims here. Whether this narrower case study is sufficiently novel for Scientometrics remains an editorial judgment, not an established consequence of these calculations

## Reproduction

Run analyze_selection_decomposition.py with Python, pandas and numpy. It reads only the frozen aggregate inputs from scientometrics_analysis/lexical/inputs and previous matched outputs for identity verification. Results preserve source estimates, every component, all influence checks, five timing configurations, source support, input hashes and protocol hash. No citation text or individual human labels is needed or redistributed. Independent verification passed 5,652 reconstruction checks and 292 production cross-checks, including exact bootstrap endpoint replay. The independent implementation and full verdict are recorded under independent_review. An isolated standalone-bundle smoke test also passed both suites.
'''
(R/'SELECTION_DECOMPOSITION_REPORT.md').write_text(text)
print('Wrote report and editorial table')
