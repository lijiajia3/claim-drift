# Literal wording diagnostic: a supplementary selection check

## What was added and why

This diagnostic counts visible word forms in the frozen 105-source-paper corpus without any new model call or human labeling. Its purpose is to check how the certainty-analysis filter changes a clearly defined textual denominator. It is not a new certainty scale, hedging classifier, validation set, or measure of target-specific failure acknowledgment.

The original archive already contained a broader hedge/booster dictionary. Moreover, the certainty prompt explicitly lists some of these words as low-score cues and assigns special treatment to failed-replication discussion. Agreement between literal cues and that score is partly built into its instructions and cannot independently validate it.

## Fixed observables and units

Rules were written and hashed at 2026-10-05 19:26:08 UTC, before lexical counts or outcome comparisons. The earlier model-score results were already known, so this is a post hoc supplementary analysis, not preregistration. All predefined words and specifications are retained, including sparse or zero results.

- Primary adverb family: exact possibly, perhaps, probably
- Separate replication vocabulary: replicate, replicates, replicated, replicating, replication, replications
- Sensitivity only: originally lowercase may, might, could, with fixed numeric-adjacent may exclusion

Core and replication matching are case-insensitive whole-token rules. Replication possessives are accepted. Tokens are Unicode alphabetic sequences with at most one internal apostrophe; there is no stemming, synonym expansion, normalization, language classifier or semantic parsing. The modal sensitivity deliberately excludes capitalized forms and a fixed ASCII-number adjacency pattern; it still contains permission/ability and nominal uses. Synthetic tests corrected implementation boundary defects without changing the frozen word lists.

A primary observation is a retained exact text unit containing at least one match. Occurrence counts and alphabetic-token denominators are also supplied. A word hit does not determine its scope, polarity, target relevance or semantic function. Replication vocabulary is neither necessary nor sufficient for acknowledgment and provides no lower or upper bound on acknowledgment prevalence. English cue absence does not imply absence of qualification in other words or languages.

## Raw accounting and primary event comparisons

The corpus has 15,280 text units: 8,427 Qwen-positive and 6,853 Qwen-negative. No negative text is assigned certainty zero. The table reports all texts, including those excluded from certainty scoring. Family counts are unique per text, so individual-word text counts can sum to more than the family total.

| Observable | Hit texts | Occurrences | Papers with hit | Positive / negative hit texts | Event difference (pp) | 95% source CI (pp) |
| --- | --- | --- | --- | --- | --- | --- |
| Three adverb tokens | 87 | 90 | 52 | 62 / 25 | -0.23 | [-1.13, +0.67] |
| Replication-word forms | 304 | 348 | 75 | 133 / 171 | -0.68 | [-2.76, +1.21] |
| Lowercase modals (sensitivity) | 1557 | 1744 | 103 | 1124 / 433 | +2.57 | [-1.40, +6.86] |

The three-adverb family occurs in only 87 texts (0.57%) from 52 sources. Within the 85 all-text event-eligible sources, only 72 text units contain a core adverb and 42 sources have no such hit. Within the 72 positive-text event sources, 52 text units contain a core adverb and 41 sources have no hit. These zeros are retained. Such narrow and sparse coverage cannot corroborate a broad conclusion of unchanged certainty. Replication-word forms occur in 304 texts; 171/304 (56.25%) fall outside the Qwen-positive subset. This is a property of the frozen conditional corpus, not an estimate of literature-wide prevalence and not proof that the filter made errors.

The main event estimates use 85 sources (44 criterion-negative, 41 criterion-positive) with at least ten retained texts before and at/after the project journal-publication year. Each source has equal weight. The word-count threshold is never used for eligibility; observed zeros stay in the analysis. Intervals resample sources within criterion groups 19,999 times and condition on fixed retrieval, source criteria, dates and lexical rules.

## Same-source filter comparison

To separate changes in support from changes in the text denominator, both all-text and Qwen-positive rates were recomputed on the identical 72 sources satisfying the positive-text ten-per-period rule.

| Observable | Comparison | Negative / positive n | Difference (pp) | 95% source CI (pp) |
| --- | --- | --- | --- | --- |
| Three adverb tokens | all_event_change | 40 / 32 | -0.33 | [-1.25, +0.55] |
| Three adverb tokens | positive_event_change | 40 / 32 | -0.40 | [-1.56, +0.68] |
| Three adverb tokens | filtered_minus_all_change | 40 / 32 | -0.08 | [-0.72, +0.52] |
| Replication-word forms | all_event_change | 40 / 32 | -0.22 | [-1.87, +1.40] |
| Replication-word forms | positive_event_change | 40 / 32 | -1.77 | [-3.99, +0.26] |
| Replication-word forms | filtered_minus_all_change | 40 / 32 | -1.55 | [-3.03, -0.24] |
| Lowercase modals (sensitivity) | all_event_change | 40 / 32 | +0.37 | [-2.83, +3.90] |
| Lowercase modals (sensitivity) | positive_event_change | 40 / 32 | -0.72 | [-5.21, +4.11] |
| Lowercase modals (sensitivity) | filtered_minus_all_change | 40 / 32 | -1.09 | [-3.33, +1.31] |

For replication-word incidence, restricting to Qwen-positive text changes the criterion-negative-minus-positive event contrast by -1.55 percentage points, with a source-bootstrap interval [-3.03, -0.24]. A sensitivity resampling the 89 connected source groups linked by shared exact text gives [-3.09, -0.30] percentage points for this shift. These intervals do not model unobserved shared citing articles.

This difference shows that the chosen text-function subset can materially change a literal wording comparison. It does not identify a causal effect of filtering, prove that replication discussion was misclassified, or validate the original model score. The criteria group contrast is descriptive; successful/criterion-positive source papers are not an untreated control.

## Every predefined word

| feature | n_texts_with_feature | n_feature_occurrences | n_papers_with_feature |
| --- | --- | --- | --- |
| possibly | 24 | 24 | 23 |
| perhaps | 47 | 50 | 32 |
| probably | 16 | 16 | 14 |
| replicate | 85 | 86 | 37 |
| replicates | 13 | 13 | 12 |
| replicated | 93 | 95 | 48 |
| replicating | 27 | 28 | 20 |
| replication | 93 | 116 | 34 |
| replications | 8 | 10 | 5 |
| may | 970 | 1050 | 99 |
| might | 324 | 345 | 87 |
| could | 328 | 349 | 86 |

## Truncation, timing and other limits

The archive's Qwen call used at most 700 characters and the DeepSeek call at most 1,200. Of the 15,280 retained texts, 112 exceed 700 characters and 54 exceed 1,200. Prefix sensitivity counts only full-text tokens wholly visible within the limit, preventing a cut token from becoming a false cue.

The full-text adverb family appears in 87 contexts, compared with 82 in the first 700 characters and 84 in the first 1,200. Replication-family presence remains 304 under both limits, although token multiplicity changes. This does not establish that every classification-relevant part of those texts was visible to the models.

Recorded manuscript-upload timing, omission of the event year, a symmetric five-year window, latest archived candidate text year, token-density normalization and leave-one-project-out diagnostics are supplied without selecting favorable results. Main journal years are RPP 2015, EERP 2016, ML1 2014 and ML3 2016. Historical upload timestamps do not certify exact historical file content, first evidence or awareness.

The cache is a purposively retrieved set of text strings with uncertain citing-record provenance and date conflicts. The three source cases excluded under the conservative source-level inclusion convention remain outside this fixed 105-paper diagnostic. This is a scope/inclusion decision; it must not be read as a claim that every individual statistic in those cases is unknown. Any Staunton-selected RPP73 extension is reported separately. Local occurrence counts cannot establish scientific correction, author belief, or response to an exact replicated proposition. This addition is suitable as a transparent supplementary limitation/triangulation analysis, not a replacement headline finding or independent measurement validation.

## Published rule basis

- [Kilicoglu and Bergler (2008), Table 1](https://link.springer.com/article/10.1186/1471-2105-9-S11-S10) supplies the three adverb examples and explains modal/context ambiguity. We use literal forms, not its classifier or reported accuracy
- [Morante and Daelemans (2009)](https://aclanthology.org/W09-1304/) distinguishes cue detection from scope and evaluates a simple dictionary baseline
- [Farkas et al. (2010)](https://aclanthology.org/W10-3001/) treats cue recognition and scope as distinct tasks
- [Szarvas et al. (2012), §2.2 and Table 1](https://aclanthology.org/J12-2004.pdf) distinguishes epistemic and other semantic uses of uncertainty-related forms

The exact frozen rules, implementation clarification, aggregate inputs, source-level estimates, all wordwise results and reproducible scripts accompany this note. No raw citation text or individual human annotation is distributed in the cleaned checkpoint.
