# External human-coded citation corpus: label-blind feasibility

Prepared 2026-10-06. Final scope decision: related-work/provenance feasibility only; no label unblinding and no new full-text corpus will be undertaken for the current revision. Status: metadata and text-key feasibility only; no external row-label values examined, no development human-label values examined, and no outcome comparisons computed.

## Decision

Hardwicke et al. (2021) is a relevant, independently human-coded source with an explicit CC BY 4.0 project license, but it is **not currently a joinable general citation-text validation set for this archive**. The external analysis CSVs provide citing DOI and Web of Science accession IDs, but no general citation-context text field. Our archived contexts provide text and year, but no citing article identifier. The two datasets therefore cannot be directly joined by their available provenance or by general citation text.

Do not report zero overlap: overlap is **not computable from the currently available general-text fields**. Do not unblind external labels or advertise external validation on the basis of this feasibility exercise.

A possible additional, separately approved recovery stage is to obtain publicly accessible full texts for the external citing articles, remain label-blind, and match our existing contexts to those full texts using frozen exact rules. This creates provenance links, not new human annotations. Its yield is unknown. The compatible downstream estimand would be descriptive assertion-filter coverage by human article-context valence, not accuracy of certainty or sentence-specific replicated-target stance.

## Sources and license

- Article: Hardwicke, T. E., et al. (2021), *Citation Patterns Following a Strongly Contradictory Replication Result: Four Case Studies From Psychology*. https://doi.org/10.1177/25152459211040837
- Fixed registered archive: https://osf.io/gyzbm/ ; registered 2021-07-22, according to https://api.osf.io/v2/registrations/gyzbm/
- Live project: https://osf.io/w8h2q/ ; metadata https://api.osf.io/v2/nodes/w8h2q/
- Both metadata records explicitly reference OSF license ID `563c1cf88c5e4a3877f9e96a`, named **CC-By Attribution 4.0 International**. Verified license record: https://api.osf.io/v2/licenses/563c1cf88c5e4a3877f9e96a/
- License URL supplied by OSF: https://creativecommons.org/licenses/by/4.0/legalcode
- Registered processed data codebook: https://osf.io/download/39akn/
- Registered primary-data codebook: https://osf.io/download/60f9a6d69e6829019d39244e/
- Registered processed content-analysis data: https://osf.io/download/hbsz8/
- Registered Carter primary data: https://osf.io/download/60f9a6d0a13c600198b0f041/
- Registered Caruso primary data: https://osf.io/download/8w7dq/

Reuse should identify the authors and source archive, retain the license notice, link the license, and indicate transformations. The project-level license is not a guarantee that the depositors can relicense all publisher-owned quotations or Web of Science material. Prefer releasing code, provenance IDs, hashes, and derived counts rather than republishing full third-party texts. This is a research-data provenance assessment, not legal clearance.

## Annotation unit and task

The published methods describe extraction of all relevant verbatim text surrounding the original-study and replication in-text citations. The valence judgment is made from the collected citation contexts of a citing article. The codebook describes one row per article; operationally the combined dataset is an **article–original-study/case pair**, since an article can occur in multiple cases.

The primary coder assigns valence; a secondary coder checks contexts/classification, and disagreements are discussed, with a third coder when necessary. `citationClassificationOriginal` is the primary-coder judgment; `citationClassificationAgreed` is the adjudicated classification. The latter would be the sole audit stratifier if a later protocol were approved.

Schema definitions, taken from the paper's Method rather than inferred from row values:

- Favorable: citation supports a positive claim about the phenomenon
- Unfavorable: citation supports a negative claim about the phenomenon
- Equivocal: no predominantly favorable or unfavorable position
- Unclassifiable: citation does not endorse or oppose the phenomenon, for example a reference to procedures

The sampling period for qualitative coding is one year before the replication year through 2019, excluding the replication year. Both overlapping cases involve Many Labs 1, whose replication year is 2014. The compatible years are therefore 2013 and 2015–2019, if a later linked audit is undertaken. The 40% sampling restriction described for Baumeister is irrelevant to these two cases.

These labels are not certainty scores, and an article-level valence should never be copied onto every local sentence as a gold stance label. Likewise, `equivocal` is not automatically “uncertain,” and `unclassifiable` is not automatically the negative class of our assertion filter. A favorable citation can confidently report an old result; an unfavorable citation can also confidently state a negative result.

## Field-level availability

The registered Carter and Caruso CSVs share this schema:

`firstCoder, secondCoder, doi, authors, pubYear, excluded, exclusionReason, articleType, citesReplication, citationClassificationOriginal, citationClassificationAgreed, counterArguments, evidenceCounter, evidenceVerbatim, methodsCounter, methodsVerbatim, expertiseCounter, expertiseVerbatim, UT`

The combined `d_contentAnalysis.csv` adds `case` and `timePeriod`.

Crucially, there is no general `citationContext` or equivalent text field. The three verbatim columns hold quotations used to justify selected counterargument categories. They are outcome-selected material, not a complete or representative citation-text corpus, and their values were not used in this feasibility analysis.

The registered `data/primary` (25 files) and `data/processed` (13 files) inventories were fully paginated. The live GitHub-backed inventories also contain 25 primary and 13 processed files, with identical filename sets and no separate context-text dataset visible. This is a metadata/name comparison, not a claim that the archived and live file bytes are identical. The live OSF-storage root is empty. The project has one visible child, the preregistered-protocol component, with a PDF protocol and amended DOCX protocol. Registered manuscript files are R Markdown manuscript and appendix sources; they have not been mined for snippets, and selected illustrative examples there would not fix general citation-text coverage.

On our side, the checked `contexts_*.json` files for both shared sources contain only `year` and `ctx`; their corresponding `meta_*.json` files identify the *cited original paper*, not the citing papers. `primary_sentences.csv` lacks citing DOI/UT as well. `contexts_numeric.csv` supplies deterministic context/item IDs and source IDs but no citing-article identifiers.

## Label-blind population counts and development exposure

All external counts below are row/identity counts **before any external exclusion flag or annotation-based filtering**. They are not counts of usable human judgments.

| Source | Original-study DOI | Local archived contexts | External article-case rows | DOI present | UT present | Development-text overlap, raw exact | Development-text overlap, normalized exact |
|---|---|---:|---:|---:|---:|---:|---:|
| ml1.12 / Carter | 10.1177/0956797611414726 | 127 | 44 | 40 | 44 | 1 | 2 |
| ml1.13 / Caruso | 10.1037/a0029288 | 158 | 51 | 47 | 51 | 4 | 5 |

The two external cases comprise 95 article-case rows, 91 distinct Web of Science accession IDs, and 84 distinct nonmissing DOI strings (87 rows with DOI). Across all five cases the combined external file has 632 rows, 575 nonmissing DOI, and 632 nonmissing UT. These are schema/identity facts only.

Development membership is based on the union of text keys in `batch01_KEY_PI_ONLY.csv`, `students/rater_A.csv`, and `students/rater_B.csv`. Each contains 368 nonblank CSV records and 356 unique trimmed texts. A student file's blank physical lines are ignored. Only text and record identity were projected out; `gold_assert`, `gold_cert`, `assert`, `certainty`, and other annotation fields were not inspected.

The frozen normalization is Unicode NFKC, Unicode-whitespace collapse to one ASCII space, trim, then casefold. It preserves punctuation, numbers, and word order. No fuzzy matching or manual adjudication was used. The seven normalized development-exposed local contexts (two Carter, five Caruso) must be excluded from a clean external audit, along with all other local contexts eventually proven to come from the same citing article.

## Current limits and next decision

1. **Provenance gate fails:** external general citation text and local citing IDs are both absent
2. **Compatibility gate is narrow:** any recovery supports descriptive article-stratified filter coverage only, not a gold sentence-label evaluation
3. **Independence gate needs article recovery:** text-level development exclusion is known; article-level overlap cannot currently be established
4. **No external-label evaluation was run:** labels remain quarantined pending approval of the proposed mapping and a feasible text-only manifest
5. **Do not silently replace missing text with counterargument quotations:** that would select on a related coded outcome and overstate representativeness

Agreed present action: retain this negative feasibility result and the conditional future protocol as related-work/provenance material. No further data collection or label unblinding is authorized or planned for the current revision. A future externally coded audit would first require independently recoverable citing-article provenance, compatible units, frozen development exclusions, and a separately approved label-blind linkage manifest.

## Reproducibility and blinding

- `text_only_feasibility.py` uses explicit column allowlists immediately after parsing CSV records; only safe projections are used downstream
- `text_only_feasibility.json` includes input SHA-256 hashes and aggregate text-key results
- `local_target_text_keys_only.csv` contains hashes and IDs, not label values or sentence text
- `*_identity_only.csv` contain external DOI/authors/year/UT (plus case where available)
- The three raw content-analysis downloads contain labels; their row values should not be printed or loaded outside the approved safe projection until a later unblinding decision
- The initial web retrieval of the published article automatically returned portions of the Results alongside Method. No row-level annotation values were inspected and no external outcome comparison or label-based selection was performed. This is a retrospectively frozen analysis proposal, not a claim of a prospective preregistration or total ignorance of the paper's published findings
