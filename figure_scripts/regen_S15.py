# -*- coding: utf-8 -*-
"""regen_S15.py — 重生成 S15(第二打分器稳健性),标注改为数据实算值:
Spearman rho=0.54 (n=8,364), assertion agreement 86%。样式与 make_figures_v3.py 一致。"""
import json, os
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
OUT = os.path.join(HERE, "figs_v3")
BLUE, VERM, INK, MUTED, GRID = "#0072B2", "#D55E00", "#1a1a1a", "#555555", "#d9d9d9"
plt.rcParams.update({"font.family": "Helvetica", "font.size": 7.5, "axes.linewidth": 0.6,
                     "pdf.fonttype": 42})

pairs = json.load(open(os.path.join(ROOT, "out_runall_v3", "scorer_pairs.json")))
res = json.load(open(os.path.join(ROOT, "out_runall_v3", "second_scorer_result.json")))

fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.9), gridspec_kw={"width_ratios": [1.15, 1]})

ax = axes[0]
ax.scatter([p[0] for p in pairs], [p[1] for p in pairs], s=3, color=INK, alpha=0.04, edgecolors="none")
ax.plot([0, 1], [0, 1], ls="--", lw=1, color=VERM)
ax.text(0.03, 0.95, "Spearman $\\rho$ = 0.54\nassertion agr. 86%", transform=ax.transAxes,
        fontsize=7, va="top")
ax.set_xlabel("Qwen2.5-72B certainty $s$"); ax.set_ylabel("DeepSeek-V3 certainty $s$")
ax.set_xlim(-0.05, 1.05); ax.set_ylim(-0.05, 1.05)
ax.spines[["top", "right"]].set_visible(False)
ax.text(-0.14, 1.02, "A", transform=ax.transAxes, fontsize=11, fontweight="bold")

ax = axes[1]
qwen = {"Refuted": 0.568, "Robust": 0.564}
ds = {"Refuted": res["level_refuted_ds"], "Robust": res["level_robust_ds"]}
x = [0, 1]; w = 0.32
for i, (arm, c) in enumerate((("Refuted", VERM), ("Robust", BLUE))):
    off = (i - 0.5) * w
    vals = [qwen[arm], ds[arm]]
    bars = ax.bar([xx + off for xx in x], vals, width=w * 0.92, color=c, label=arm)
    for xx, v in zip(x, vals):
        ax.text(xx + off, v + 0.015, f"{v:.2f}", ha="center", fontsize=6.5, color=c)
ax.set_xticks(x); ax.set_xticklabels(["Qwen2.5-72B", "DeepSeek-V3"])
ax.set_ylabel("Mean stated certainty"); ax.set_ylim(0, 0.82)
ax.legend(frameon=False, fontsize=6.5, loc="upper left")
ax.spines[["top", "right"]].set_visible(False)
ax.grid(axis="y", color=GRID, lw=0.4, alpha=0.7); ax.set_axisbelow(True)
ax.text(-0.14, 1.02, "B", transform=ax.transAxes, fontsize=11, fontweight="bold")

fig.tight_layout()
fig.savefig(os.path.join(OUT, "S15_secondscorer.pdf"))
fig.savefig(os.path.join(OUT, "S15_secondscorer_p.png"), dpi=130)
print("done S15")
