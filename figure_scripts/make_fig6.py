# -*- coding: utf-8 -*-
"""fig6_robust — 稳健性四联主图:A 分项目 β,B 分桶敏感性,C 高R²子集,D 断言率分布。"""
import json, math, os, csv, glob, statistics, random
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
BLUE, VERM, INK, MUTED, GRID = "#0072B2", "#D55E00", "#1a1a1a", "#555555", "#d9d9d9"
plt.rcParams.update({"font.family": "Helvetica", "font.size": 7, "axes.linewidth": .6, "pdf.fonttype": 42})

S = json.load(open(os.path.join(ROOT, "out_runall_v3/summary.json")))["seeds"]
CSV = {('v3_' + r['name']): r for r in csv.DictReader(open(os.path.join(ROOT, 'v3_seeds/seeds_v3.csv')))}
OK = [r for r in S if r.get("beta") is not None]
def proj(name):
    j = str(CSV.get(name, {}).get('journal', '')).lower()
    return 'EERP' if ('economic' in j or 'qje' in j) else ('SSRP' if ('science' in j or 'nature' in j) else 'RPP')

def style(ax):
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", color=GRID, lw=.4, alpha=.7); ax.set_axisbelow(True)

def scored(name):
    p = os.path.join(ROOT, "seeds_data", f"scored2_{name}.jsonl"); rows = []
    if os.path.exists(p):
        for L in open(p):
            try:
                o = json.loads(L)
                if o.get("year") and o.get("assert") == 1 and o.get("s") is not None:
                    rows.append((o["year"], o["s"]))
            except Exception: pass
    return sorted(rows)

def bins(rows, mb):
    by = {}; out = []; cur = []
    for y, s in rows: by.setdefault(y, []).append(s)
    for y in sorted(by):
        cur.extend((y, v) for v in by[y])
        if len(cur) >= mb: out.append(cur); cur = []
    if cur and out: out[-1] += cur
    elif cur: out = [cur]
    return [(statistics.mean(y for y, _ in b), statistics.mean(v for _, v in b), len(b)) for b in out]

def wfit(pts, birth):
    if len(pts) < 3 or (pts[-1][0] - pts[0][0]) < 4: return None
    xs = [p[0] - birth for p in pts]; ws = [p[2] for p in pts]
    ys = [math.log(1 - min(p[1], .999)) for p in pts]
    W = sum(ws); mx = sum(w * x for w, x in zip(ws, xs)) / W; my = sum(w * y for w, y in zip(ws, ys)) / W
    den = sum(w * (x - mx) ** 2 for w, x in zip(ws, xs))
    if den == 0: return None
    return 1 - math.exp(sum(w * (x - mx) * (y - my) for w, x, y in zip(ws, xs, ys)) / den)

fig, axes = plt.subplots(1, 4, figsize=(7.2, 2.35))
(aA, aB, aC, aD) = axes
for ax, L in zip(axes, "ABCD"): ax.set_title(L, loc="left", fontweight="bold", fontsize=10, pad=5)

# A 分项目
random.seed(9)
for pi, p in enumerate(("RPP", "EERP")):
    for arm, c, d in (("refuted", VERM, -.17), ("robust", BLUE, .17)):
        vs = [r["beta"] for r in OK if proj(r["name"]) == p and r["arm"] == arm]
        if not vs: continue
        aA.scatter([pi + d + random.uniform(-.07, .07) for _ in vs], vs, s=9, color=c, alpha=.55, edgecolors="none")
        aA.hlines(statistics.mean(vs), pi + d - .12, pi + d + .12, color=c, lw=2)
aA.axhline(0, color=GRID, lw=.8); aA.set_xticks([0, 1]); aA.set_xticklabels(["Psychology", "Economics"])
aA.set_ylabel("$\\beta$ (per year)"); style(aA)

# B 分桶敏感性
for arm, c, mk in (("refuted", VERM, "D"), ("robust", BLUE, "o")):
    ms = []
    for mb in (6, 8, 12):
        bs = []
        for r in OK:
            if r["arm"] != arm: continue
            b = wfit(bins(scored(r["name"]), mb), r.get("birth") or 2010)
            if b is not None: bs.append(b)
        ms.append(statistics.mean(bs) if bs else float("nan"))
    aB.plot((6, 8, 12), ms, mk + "-", color=c, lw=1.3, markersize=4, label=arm.capitalize())
aB.axhline(0, color=GRID, lw=.8); aB.set_xticks((6, 8, 12))
aB.set_xlabel("Min sentences per bin"); aB.set_ylabel("Group mean $\\beta$")
aB.legend(frameon=False, fontsize=6); style(aB)

# C 高 R² 子集
random.seed(10)
hi = [r for r in OK if (r.get("r2") or 0) >= .1]
for j, (arm, c) in enumerate((("refuted", VERM), ("robust", BLUE))):
    vs = [r["beta"] for r in hi if r["arm"] == arm]
    aC.scatter([j + random.uniform(-.12, .12) for _ in vs], vs, s=10, color=c, alpha=.6, edgecolors="none")
    if vs: aC.hlines(statistics.mean(vs), j - .22, j + .22, color=c, lw=2)
aC.axhline(0, color=GRID, lw=.8); aC.set_xticks([0, 1]); aC.set_xticklabels(["Refuted", "Robust"])
aC.set_ylabel("$\\beta$, $R^2\\geq0.1$ subset"); aC.set_xlim(-.55, 1.55); style(aC)

# D 断言率分布
for arm, c in (("refuted", VERM), ("robust", BLUE)):
    vs = [r["n_assert"] / r["n_all"] for r in S if r.get("n_assert") and r.get("n_all") and r["arm"] == arm]
    aD.hist(vs, bins=12, alpha=.5, color=c, label=f"{arm.capitalize()}")
aD.set_xlabel("Assertion-sentence rate"); aD.set_ylabel("Claims")
aD.legend(frameon=False, fontsize=6); style(aD)

fig.tight_layout()
fig.savefig(os.path.join(HERE, "figs_v3/fig6_robust.pdf"))
fig.savefig(os.path.join(HERE, "figs_v3/fig6_robust_p.png"), dpi=140)
print("✓ fig6_robust")

# ---------------- Fig 7: 轨迹画廊 ----------------
def fig7():
    def ry(name):
        return {'EERP': 2016, 'SSRP': 2018, 'RPP': 2015}[proj(name)]
    cand = sorted([r for r in OK if (r.get("n_assert") or 0) >= 60], key=lambda r: -(r.get("n_assert") or 0))
    ref = [r for r in cand if r["arm"] == "refuted"][:4]
    rob = [r for r in cand if r["arm"] == "robust"][:4]
    fig, axes = plt.subplots(2, 4, figsize=(7.2, 3.7), sharey=True)
    for ax, r in zip(axes.flat, ref + rob):
        c = VERM if r["arm"] == "refuted" else BLUE
        pts = bins(scored(r["name"]), 8)
        ax.scatter([p[0] for p in pts], [p[1] for p in pts], s=[max(6, min(26, p[2] * .7)) for p in pts],
                   color=c, edgecolors="white", linewidths=.4, zorder=3)
        b = r["beta"]; y0 = pts[0][0]; m0 = min(pts[0][1], .95)
        fx = [y0 + t * (pts[-1][0] - y0) / 50 for t in range(51)]
        ax.plot(fx, [1 - (1 - m0) * (1 - b) ** (x - y0) for x in fx], color=INK, lw=.9)
        ax.axvline(ry(r["name"]), color=MUTED, lw=.8, ls="--")
        t = CSV.get(r["name"], {}).get("title", r["name"])[:34]
        ax.set_title(t, fontsize=5.6, color=MUTED, pad=3)
        ax.tick_params(labelsize=5.5); style(ax); ax.set_ylim(.25, .95)
        from matplotlib.ticker import MaxNLocator
        ax.xaxis.set_major_locator(MaxNLocator(integer=True, nbins=5))
    axes[0][0].set_ylabel("Refuted\n$\\bar{s}$ per bin", fontsize=6.5, color=VERM)
    axes[1][0].set_ylabel("Robust\n$\\bar{s}$ per bin", fontsize=6.5, color=BLUE)
    fig.text(.5, .01, "Year of citing paper (dashed line: replication published)", ha="center", fontsize=7)
    fig.tight_layout(rect=(0, .03, 1, 1))
    fig.savefig(os.path.join(HERE, "figs_v3/fig7_gallery.pdf"))
    fig.savefig(os.path.join(HERE, "figs_v3/fig7_gallery_p.png"), dpi=140)
    print("✓ fig7_gallery")

# ---------------- Fig 8: 没有发生的纠正 ----------------
def fig8():
    D = json.load(open(os.path.join(ROOT, "out_runall_v3/did_result.json")))
    pts = sorted((int(t), v[0], v[1]) for t, v in D["event_study"]["refuted"].items())
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    se = [.28 / math.sqrt(p[2]) for p in pts]
    fig, ax = plt.subplots(figsize=(4.6, 2.9))
    ax.set_title(" ", loc="left", fontsize=10)
    ax.fill_between(xs, [y - 1.96 * e for y, e in zip(ys, se)], [y + 1.96 * e for y, e in zip(ys, se)],
                    color=VERM, alpha=.15, lw=0)
    ax.plot(xs, ys, color=VERM, lw=1.7, marker="D", markersize=3.6, label="Refuted claims, observed", zorder=4)
    for drop, g in ((-.05, "#666666"), (-.10, "#999999"), (-.20, "#bbbbbb")):
        hy = [0 if x < 0 else drop * (1 - math.exp(-x / 2.0)) for x in xs]
        ax.plot(xs, hy, color=g, lw=1.1, ls="--", zorder=2)
        ax.text(xs[-1] + .25, hy[-1], f"{drop:+.2f}", fontsize=6, color=g, va="center")
    ax.axvline(0, color=INK, lw=.8, ls=":")
    ax.text(.15, .085, "replication\npublished", fontsize=6, color=INK)
    ax.text(4.4, -.155, "hypothetical corrections\n(illustrative)", fontsize=6, color="#888888", ha="center")
    ax.axhline(0, color=GRID, lw=.8)
    ax.set_ylim(-.24, .12); ax.set_xlim(xs[0] - .4, xs[-1] + 1.6)
    ax.set_xlabel("Years relative to replication publication")
    ax.set_ylabel("Stated certainty (claim-demeaned)")
    ax.legend(frameon=False, fontsize=6.4, loc="lower left"); style(ax)
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "figs_v3/fig8_counterfactual.pdf"))
    fig.savefig(os.path.join(HERE, "figs_v3/fig8_counterfactual_p.png"), dpi=140)
    print("✓ fig8_counterfactual")

fig7(); fig8()
