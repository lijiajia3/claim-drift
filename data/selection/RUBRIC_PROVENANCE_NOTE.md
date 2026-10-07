# Shared human and model scoring rules

This note traces the score-definition issue to the supplied study materials. It contains codebook excerpts and source hashes only; no individual human ratings or citation-corpus text is reproduced.

## Human annotation manual

Source within the original study package: annotation_package/batch01_recut/标注手册.md, section 问题 2, subsection 边界判例, lines 97 and 99.

The manual gives an unqualified negative empirical statement a possible score of 1: “X does not affect Y” 说得斩钉截铁 → 1. It gives the qualified version “X may not affect Y” a score of 0. A separate rule says that “failed to replicate / has been questioned” language normally receives no more than 0.25.

Manual SHA-256: e8a0c68ac6b63d8b591f84fc28ba5c63b8e1a713cff8f8b9ec294ce07de8e87a

## Archived model instruction

Source within the original study package: rescore_primary_certainty.py, PROMPT, lines 36–47, particularly line 45. The instruction likewise normally limits explicit failed replication, challenge or conflicting evidence to 0.25 while allowing a categorical negative claim to receive 1.

Script SHA-256: 1ea632856a05975799a82adb56e406f068a79ee96fab95bb86e037ae752a8b02

## Interpretation

These are documented operational rules, not evidence that a coder or model failed to follow instructions. They combine rhetorical strength with a special treatment of evidential challenge. Agreement between human and model ratings under the aligned rubric therefore does not establish a single monotonic relation between the score and endorsement of, or correction concerning, a replicated target.

Additional ratings under the same rubric could improve estimates of reliability and agreement. They would not by themselves change the score definition or establish which replicated proposition each sentence describes. The revised literal-form analysis does not require treating this operational score as such a semantic measure.
