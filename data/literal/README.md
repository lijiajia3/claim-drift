# Frozen literal-wording diagnostic

This supplementary analysis counts predefined literal word forms in the retained conservative 105-source baseline. It requires no model inference or new human labels. Read LITERAL_DIAGNOSTIC.md and the exact RULES_FROZEN.json before interpreting the tables. The separate RPP73_SCOPE_SENSITIVITY.md defines the 106-source extension; it does not replace the primary baseline.

The delivered inputs contain aggregate source/year counts only, with no citation text, text hashes or human annotation rows. The rule file was frozen before lexical outcome comparisons; implementation corrections repaired token-boundary fidelity while retaining its hash and word lists.

From the parent numerical checkpoint, use:

    python lexical/src/analyze_literal_counts.py
    python lexical/src/make_literal_report.py
    python lexical/src/staunton_selected_sensitivity.py
    python -m unittest discover -s lexical/src -p 'test_literal*.py' -v

The clean package's Staunton script uses only the bundled aggregate extension. The preparation script can regenerate counts from an author-supplied original archive and numeric snapshot; those original texts are not distributed here.

Primary literal observables are possibly/perhaps/probably and six replication-word forms. Lowercase modals are a polysemy-sensitive check. Feature presence does not establish semantic hedging, failure acknowledgment, proposition relevance or an author's beliefs. Model prompt overlap prevents treating agreement with the old certainty score as independent validation. Raw denominators, wordwise results, zeros and every predefined sensitivity are retained.

The two supplementary figures are available as editable SVG, PDF and PNG. Captions describe their denominators and conditional uncertainty. A list of all verified inputs and output hashes is provided in VERIFICATION.json and REFERENCE_OUTPUT_HASHES.json.
