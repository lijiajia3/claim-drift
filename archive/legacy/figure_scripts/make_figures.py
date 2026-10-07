# -*- coding: utf-8 -*-
"""make_figures.py — 生成 SciAdv 两张主图(矢量 PDF + 预览 PNG)。
数据源:../out_runall_v2/summary.json 与 ../seeds_data/scored2_<seed>.jsonl。
可在跑批未完成时先渲染(缺的种子自动跳过),跑完重跑本脚本即为终图。
用法:python3.13 make_figures.py [example_seed]   # 默认 h_pylori,缺则自动挑 R² 最高者
"""
import json, math, os, sys, statistics
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SUMMARY = os.path.join(ROOT, "out_runall_v2", "summary.json")
DATADIR = os.path.join(ROOT, "seeds_data")

BLUE, VERM = "#0072B2", "#D55E00"   # Okabe-Ito pair, validated (ΔE≥91 all CVD)
INK, MUTED, GRID = "#1a1a1a", "#555555", "#d9d9d9"
plt.rcParams.update({
    "font.family": "Helvetica", "font.size": 7.5,
    "axes.linewidth": 0.6, "axes.edgecolor": INK,
    "xtick.color": INK, "ytick.color": INK,
    "pdf.fonttype": 42,
})

def load_summary():
    if not os.path.exists(SUMMARY): return []
    return json.load(open(SUMMARY)).get("seeds", [])

def load_scored(name):
    p = os.path.join(DATADIR, f"scored2_{name}.jsonl")
    rows = []
    if os.path.exists(p):
        for line in open(p, encoding="utf-8"):
            try:
                o = json.loads(line)
                if o.get("year") and o.get("assert") == 1 and o.get("s") is not None:
                    rows.append((o["year"], o["s"]))
            except Exception: pass
    return sorted(rows)

def yearbins(rows, minbin=8):
    bins, cur = [], []
    by = {}
    for y, s in rows: by.setdefault(y, []).append(s)
    for y in sorted(by):
        cur.extend((y, s) for s in by[y])
        if len(cur) >= minbin: bins.append(cur); cur = []
    if cur and bins: bins[-1] += cur
    elif cur: bins = [cur]
    return [(statistics.mean(y for y, _ in b), statistics.mean(s for _, s in b), len(b)) for b in bins]

# ---------------- Figure 1 ----------------
def fig1(example="h_pylori"):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.2, 2.6))
    # A: geometric hardening curves, sequential blues (magnitude of beta), direct labels
    blues = ["#b3cde3", "#6baed6", "#2171b5", "#08306b"]
    s0, G = 0.4, 60
    ends = []
    for b, c in zip((0.01, 0.03, 0.06, 0.12), blues):
        g = list(range(G + 1))
        s = [1 - (1 - s0) * (1 - b) ** x for x in g]
        ax1.plot(g, s, color=c, lw=1.6)
        ends.append([b, s[-1]])
    # 端标防碰撞:自下而上强制最小间距
    ends.sort(key=lambda e: e[1])
    for i in range(1, len(ends)):
        if ends[i][1] - ends[i-1][1] < 0.055:
            ends[i][1] = ends[i-1][1] + 0.055
    for b, y in ends:
        ax1.text(G + 1, y, f"$\\beta$={b}", color=INK, fontsize=7, va="center")
    ax1.set_xlim(0, G + 14); ax1.set_ylim(0.3, 1.02)
    ax1.axhline(1.0, color=GRID, lw=0.6, ls=":")
    ax1.set_xlabel("Citation generation $g$"); ax1.set_ylabel("Expected stated certainty $\\mathbb{E}[s_g]$")
    ax1.set_title("A", loc="left", fontweight="bold", fontsize=9)
    # B: example claim trajectory
    seeds = {r["name"]: r for r in load_summary() if r.get("beta") is not None}
    name = example if example in seeds else (max(seeds, key=lambda k: seeds[k].get("r2") or 0) if seeds else None)
    if name:
        rows = load_scored(name)
        pts = yearbins(rows)
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]; ns = [p[2] for p in pts]
        ax2.scatter(xs, ys, s=[max(10, min(40, n)) for n in ns], color=BLUE, zorder=3,
                    edgecolors="white", linewidths=0.5)
        beta = seeds[name]["beta"]
        y0 = xs[0]; m0 = min(ys[0], 0.95)
        fx = [y0 + t * (xs[-1] - y0) / 80 for t in range(81)]
        fy = [1 - (1 - m0) * (1 - beta) ** (x - y0) for x in fx]
        ax2.plot(fx, fy, color=VERM, lw=1.6, zorder=2)
        ax2.text(0.03, 0.92, name.replace("_", " ") + f"  ($\\beta$={beta:+.3f})",
                 transform=ax2.transAxes, fontsize=7, color=MUTED)
        ax2.set_xlabel("Year of citing paper"); ax2.set_ylabel("Mean stated certainty $\\bar{s}$")
    else:
        ax2.text(0.5, 0.5, "awaiting v2 data", ha="center", transform=ax2.transAxes, color=MUTED)
    ax2.set_title("B", loc="left", fontweight="bold", fontsize=9)
    for ax in (ax1, ax2):
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(axis="y", color=GRID, lw=0.4, alpha=0.7); ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "fig1.pdf")); fig.savefig(os.path.join(HERE, "fig1_preview.png"), dpi=160)
    plt.close(fig); print("fig1 done", "| example:", name)

# ---------------- Figure 2 ----------------
def fig2():
    seeds = [r for r in load_summary() if r.get("beta") is not None and r.get("arm") in ("stable", "reversed")]
    if not seeds:
        print("fig2 skipped: no fitted seeds yet"); return
    stable = sorted([r for r in seeds if r["arm"] == "stable"], key=lambda r: r["beta"])
    revsd  = sorted([r for r in seeds if r["arm"] == "reversed"], key=lambda r: r["beta"])
    order = revsd + stable
    ys = range(len(order))
    fig, ax = plt.subplots(figsize=(4.6, 0.28 * len(order) + 1.1))
    ax.axvline(0, color=GRID, lw=0.8)
    for i, r in zip(ys, order):
        st = r["arm"] == "stable"
        ax.scatter(r["beta"], i, s=34, marker="o" if st else "D",
                   color=BLUE if st else VERM, edgecolors="white", linewidths=0.5, zorder=3)
        ax.text(-0.002 if r["beta"] >= 0 else 0.002, i, r["name"].replace("_", " "),
                ha="right" if r["beta"] >= 0 else "left", va="center", fontsize=6.5, color=MUTED)
    for grp, col in ((revsd, VERM), (stable, BLUE)):
        if grp:
            m = statistics.mean(r["beta"] for r in grp)
            lo = min(ys) if grp is revsd else len(revsd)
            hi = len(revsd) - 1 if grp is revsd else len(order) - 1
            ax.vlines(m, lo - 0.4, hi + 0.4, color=col, lw=1.8, alpha=0.85)
    if stable and revsd:
        ax.axhline(len(revsd) - 0.5, color=GRID, lw=0.6, ls=":")
    ax.set_yticks([]); ax.set_xlabel("Hardening rate $\\beta$ (per year)")
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.grid(axis="x", color=GRID, lw=0.4, alpha=0.7); ax.set_axisbelow(True)
    from matplotlib.lines import Line2D
    ax.legend(handles=[
        Line2D([0], [0], marker="o", ls="", color=BLUE, label="Robust (replicated)", markersize=5),
        Line2D([0], [0], marker="D", ls="", color=VERM, label="Refuted (failed replication)", markersize=4.5)],
        frameon=False, fontsize=6.5, loc="lower right")
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "fig2.pdf")); fig.savefig(os.path.join(HERE, "fig2_preview.png"), dpi=160)
    plt.close(fig); print(f"fig2 done | robust n={len(stable)} refuted n={len(revsd)}")

if __name__ == "__main__":
    fig1(sys.argv[1] if len(sys.argv) > 1 else "h_pylori")
    fig2()
