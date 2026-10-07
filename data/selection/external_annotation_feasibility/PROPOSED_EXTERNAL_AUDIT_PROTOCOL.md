# Proposed descriptive external valence audit (approval required)

Future-only proposal, version 1; frozen at the metadata/text-key stage on 2026-10-06. The current-revision decision is to stop at metadata/provenance feasibility, with no new full-text recovery and no label unblinding. No external annotation values have been inspected. This is a proposed retrospective protocol, not a preregistration. **Do not execute label unblinding on the current files.**

## Question and permissible claim

Among archived citation contexts that can be unambiguously linked to independently human-coded Carter/Caruso citing articles, how often does our already-frozen assertion filter retain contexts from each external article-context valence category?

Permissible claim: a limited external descriptive audit of the selection behavior of the frozen assertion filter, stratified by independently coded article-context valence.

Impermissible claims: externally validated certainty; sentence-level stance accuracy; gold labels for the replicated target; unbiased performance on the entire source corpus; causal effects of replication; validation on new human annotations.

## Frozen sources and target mapping

Use registered OSF archive `gyzbm`, not a moving live replacement. Primary external metadata/labels come from `data/processed/d_contentAnalysis.csv` with the downloaded checksum in `text_only_feasibility.json`.

- `carter` → `ml1.12` → original DOI `10.1177/0956797611414726`
- `caruso` → `ml1.13` → original DOI `10.1037/a0029288`

Use the existing frozen local assertion decisions, with no new prompts, no rescoring, no paid API, no model calls, and no new human annotation. Do not read certainty values for this audit.

The external interpretive unit is citing article × original-study case. Preserve article identity across cases; never treat repeated sentences from one article as independent human judgments.

## Stage A: currently blocked provenance recovery

The existing files do not satisfy this stage. If additional recovery is approved, use **only public, legally accessible full text** of the external citing articles, obtained without author contact or new account/subscription. Obtain the full text based on DOI/UT bibliographic identity only, keeping all label/exclusion columns sealed.

1. Enumerate all 95 external article-case identities (91 distinct UT records), rather than choosing records by predicted or known valence
2. Record stable citing DOI or UT, case, title where bibliographically verified, full-text source URL, retrieval timestamp, file checksum, and machine-readable text checksum
3. Accept a DOI association only from the public publisher/repository record for that exact work; do not attach a DOI based solely on approximate title similarity
4. Match each local sentence/context to full text of articles within its pre-mapped source case using the exact normalization below
5. Where full text remains unavailable, text extraction fails, or IDs cannot be established, record this as missing; do not contact authors, infer a label, or substitute an abstract/counterargument excerpt
6. Text-level matching establishes an article provenance link only. It does not locate all citation contexts in the source article or make the external label sentence-specific

### Frozen text matching

Normalization `NFKC_whitespace_casefold_v1`: Unicode NFKC → collapse each run of Unicode whitespace to one ASCII space → trim → casefold. Preserve punctuation, numbers, word order, and all substantive tokens. Do not remove citations or alter hyphens, join OCR fragments, or perform fuzzy matching. Do not introduce extraction fixes based on label values.

Primary accepted link: the complete nonempty normalized local context occurs as one contiguous substring in exactly one candidate full-text article within the matching original-study case, with context length at least 70 normalized characters. For a shorter context, allow only a whole-context equality with an independently supplied general citation-context record carrying article identity; absent such records, mark it ineligible.

A local context matching multiple candidate citing articles is ambiguous and stays unresolved. Identical DOI/UT versions of the same work are a single article identity. Multiple local contexts may link to one article; repeated text within an article does not create extra article observations. Raw trimmed exact matching should be retained as a sensitivity provenance flag, not a competing rule selected by yield. If an article is represented under multiple cases, retain both case rows but preserve the shared citing-article cluster ID.

No minimum number of matches is chosen after seeing labels. Before unblinding, report the entire text-only match manifest, accessibility denominator, ambiguity counts, date agreement, and development exposure. If there is insufficient usable coverage for a meaningful descriptive appendix, stop and report the feasibility result without labels.

## Stage B: leakage and time gates, before unblinding

- Remove every local normalized text overlapping any of the three development annotation text-key files
- Remove all other linked local contexts belonging to a citing article with such overlap, even across the two cases
- Preserve a separate development-exposed manifest for auditability, without labels
- Restrict publication years to 2013 and 2015–2019, based on external `pubYear`. Do not recode publication years to improve alignment
- Check local archived year against external year and flag disagreements. Predeclare the primary descriptive set as exact year agreement; report an additional provenance-only sensitivity set retaining disagreements, if any, without choosing based on outcomes
- Freeze and hash the accepted/excluded/ambiguous manifest, extraction code, source versions, counts, and this protocol before requesting unblinding

## Stage C: proposed external schema mapping, after explicit approval

Use only the external adjudicated `citationClassificationAgreed` field. Retain its four nominal categories unchanged:

- favorable
- equivocal
- unfavorable
- unclassifiable

Case/capitalization normalization of literal schema tokens is allowed; unexpected tokens are reported as unexpected/missing, never silently reinterpreted. Do not inspect primary-coder labels to pick the more favorable result. After unblinding, apply the original `excluded` flag and report its effect on denominators transparently; do not use exclusion reasons to create a new custom cohort. Missing adjudicated labels remain missing. Excluded/unknown rows are not a fifth valence class.

No numeric certainty mapping and no “equivocal = uncertain” conversion. No binary gold assertion mapping is asserted: the two coding tasks have different constructs and units.

## Descriptive output and limits

For each case and each of the four external valence categories, report:

1. Number of uniquely linked, non-development-exposed article-case pairs
2. Number of archived contexts linked to those article-case pairs
3. Number and fraction of these contexts retained by the already-frozen assertion filter
4. Article-balanced mean of each article-case's context retention fraction, keeping zero-retention articles

Keep all four valence categories, including empty cells. Report no classifier accuracy, precision/recall, F1, AUC, correlation with certainty, or model ranking. Do not tune thresholds or filters using these data. Avoid inferential significance tests; two purposively overlapping source papers and an availability-conditioned linkage subset do not justify population-level generalization. If uncertainty intervals are later requested, prespecify a citing-article-cluster method separately before using outcomes.

Keep dates descriptive. Do not run pre/post valence shifts or combine this convenience subset with the main replication-event analysis. A pooled display, if used, must give the two cases equal weight and be accompanied by the case-specific results; it is not a broader population estimate.

## Attribution and release

Cite the 2021 paper and fixed OSF registration. Record CC BY 4.0, link the license, and state that we linked archived contexts to external article-case metadata and calculated new descriptive filter-retention summaries. Release code, hash manifests, provenance IDs, and permitted derived counts. Do not redistribute retrieved full texts or large publisher-owned excerpts merely because OSF metadata advertises a CC BY license for its project.

## Approval needed

Decision 1: approve or decline a separate label-blind public-full-text provenance recovery stage.

Decision 2 (only after a frozen feasible manifest exists): approve this descriptive nominal-valence stratification and label unblinding. Current recommendation: **withhold Decision 2**. No labels should be opened on the basis of the current metadata alone.
