# Task B human validation labels

This directory contains de-identified human labels for the 150-sentence Task B validation sample used in the manuscript. Task B asks whether a citing sentence explicitly acknowledges a failed replication, mixed or inconsistent evidence, or controversy concerning the cited finding.

## Files

- `rater_A.csv`, `rater_B.csv`, and `rater_C.csv`: one collapsed label per original sentence and rater. The 12 concealed duplicate items are reported separately through `duplicate_check.csv` rather than counted twice.
- `consensus.csv`: the three human labels, the human majority label, the four model labels, and the model majority label for every sentence.
- `duplicate_check.csv`: within-rater agreement on the 12 concealed duplicates.
- `summary.json`: machine-readable validation statistics.
- `calculate_summary.py`: regenerates `consensus.csv` and `summary.json` from the de-identified rater files and the archived model outputs.
- `codebook.md`: the Task B decision rule.

Labels are `0` (no acknowledgment), `1` (acknowledgment), and `9` (unable to decide). Human majority votes exclude `9`; all 150 items retain at least two binary judgments. The model majority requires at least three positive votes among the four models, so a 2–2 tie is coded `0`.

## Reported checks

- Human majority acknowledgment rate: 5/150 (3.3%).
- Four-model majority acknowledgment rate: 7/150 (4.7%).
- Human/model agreement: 146/150 (97.3%), Cohen's kappa = 0.653.
- Complete three-rater agreement: 131/150 (87.3%).
- Fleiss' kappa across the three categories (0/1/9): 0.236.
- Concealed duplicate consistency: 36/36 within-rater pairs (100%).

The rater identifiers are arbitrary and do not encode names, assignment order, or other personal information.
