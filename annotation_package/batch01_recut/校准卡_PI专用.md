# 校准卡（PI 专用 · 含标准答案 · 勿发标注者）

三人（P2 / P11 / P20）在共同 12 句上的分歧逐条裁定。开校准会时：**一致的句子略过，只过下面这些分歧**，让三人对着"裁定 + 依据"收敛。

标注现状：断言 Fleiss κ=0.70（已达标），确定性 α≈0（样本全是高确定性句所致，需用 `iaa_train/` 那份含 hedged 的 42 句重测）。

---

## A. 有明确规则的分歧 —— 纠正打偏的那个人

### T0001 · 断言（P2 判 1，P11/P20 判 0）
> "**These results suggest that our** automated scoring procedure should not be used…(Levine et al., 2002)"
- **裁定：assert = 0**。这是**本文作者自己的结果**（"our procedure"），不是转述被引研究。
- **依据**：手册 问题1 · 选0 第 3 类"说的是本文作者自己的研究结果"。
- **P2 要改**：看到 "our results / we found / 本文 Experiment" 就归 0。

### T0006 · 确定性（P2 判 1，P11/P20 判 0.75）
> "Fischer et al. (2008) **show that** individuals… engage in more confirmatory processing…"
- **裁定：s = 0.75**。"show that / demonstrate" 是 0.75 档，不是 1。
- **依据**：确定性表 0.75 行 + "最常见错误"提示。
- **P2 要改**。

### T0011 · 确定性（P20 判 0.5 ✓，P2 判 0.75，P11 判 1）
> "Farris et al. (2008) **found that** men were more likely than women…"
- **裁定：s = 0.5**。"found that" 是**中性报告**，就是 0.5。**P20 打对了**。
- **依据**：确定性表 0.5 行（"found that / reported that"）+ "最常见错误"提示。
- **P2、P11 要改**：这是最典型的"往高打"，务必焊死。

### T0007 · 确定性（P2 判 0.5，P11/P20 判 1）
> "Concerns… **contribute directly to** the anxiety that Whites experience…"
- **裁定：s = 0.75–1**。"contribute directly to" 是**无限定的因果现在时**，属高档。**P2 的 0.5 偏低**。
- **依据**：确定性表 1 行"无任何限定的一般现在时断言 / 因果"。

---

## B. 本就两可的分歧 —— 不苛求，接受 ±1 档

这几句是构念本身的模糊地带，三人差 1 档属正常，**不要在会上纠结**，讲清"取折中"原则即可：

- **T0005**（0.75 / 1 / 1）："It is understood that … often fail to adjust" —— "it is understood that" 偏强、"often" 是弱限定 → **0.75 或 1 都可**。
- **T0008**（0.75 / 1 / 0.5）："Statistical learning **occurs** irrespective…; it **has been reported** in…" —— 主句断定（occurs）+ 从句报告（reported）混合 → 手册"既有肯定又有限定，取折中" → **0.5–0.75**。
- **T0012**（0.75 / 0.5 / 1）："…**has been established as** a significant predictor…" —— "established" 偏强但"as a predictor"是报告口吻 → **0.5–0.75**。

---

## C. 残句处理正面例（三人都对，表扬一下）

### T0010 · 三人都判 assert=0 ✓
> "…the money priming effect observed in Experiment 1 in Caruso et al. (2013) **T hi s do cu m en t is co py ri gh te d**…"
- 句子被 PDF 版权水印污染成乱码，且讲的是被引研究的 Experiment 1（当例子提，非转述其结论）→ assert=0 正确。三人处理一致，是残句规则执行到位的好例。

---

## 会上要焊死的三条（一句话版）

1. **"our results / we found / 本文 Experiment X" = assert 0**（不是转述别人）——治 P2
2. **"found that / reported that = 0.5"，"show that / demonstrate = 0.75"，只有无限定断定/因果 = 1**——治"往高打"，P2、P11 都要
3. **两句都对时差 1 档没关系**，别把 0.5 vs 0.75 这种边界当错——别过度校准

会后：三人**全标 `iaa_train/iaa_train_import.csv`（42 句，含 hedged）**，再算一次 κ 和 α；断言 κ 已达标，重点看确定性 α 能否随 range 打开而过 0.6。
