# Task B codebook / 任务 B 标注规则

## Question / 问题

Does the citing sentence mention that the target finding failed to replicate, has mixed or inconsistent evidence, or is controversial?

引用句是否提到目标发现存在“复现失败、证据不一致或争议”？

## Labels / 标签

- `1` — Explicit acknowledgment. Signals include “failed to replicate,” “replication attempts,” “mixed/inconsistent evidence,” “controversial,” “challenged/questioned,” or a cited study that failed to find the effect.
- `0` — No acknowledgment. A normal citation, cautious wording, or hedging alone does not count.
- `9` — The visible sentence is too incomplete or ambiguous to decide.

- `1` — 明确承认问题，例如 failed to replicate、replication attempts、mixed/inconsistent evidence、controversial、challenged/questioned，或明确引用未发现该效应的研究。
- `0` — 未承认问题。正常引用、谨慎措辞或委婉表达本身不算。
- `9` — 句子残缺或歧义过大，无法判断。

The problem must concern the target finding. A general reference to the replication crisis does not count, and a competing theoretical explanation is not evidence of empirical inconsistency unless the sentence says so explicitly.

争议必须指向目标发现。泛泛提及“复现危机”不算；只存在理论解释之争、但没有明确说证据冲突，也不算。
