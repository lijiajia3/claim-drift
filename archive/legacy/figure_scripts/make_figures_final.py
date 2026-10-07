# -*- coding: utf-8 -*-
"""make_figures_final.py — 5 张 SciAdv 主图(对标 Serra-Garcia 2021 规格),矢量 PDF + 预览 PNG。"""
import json, math, os, csv, glob, statistics, random
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import textwrap

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
OUT = os.path.join(HERE, "figs_v3")
BLUE, VERM, INK, MUTED, GRID = "#0072B2", "#D55E00", "#1a1a1a", "#555555", "#d9d9d9"
plt.rcParams.update({"font.family": "Helvetica", "font.size": 7, "axes.linewidth": .6, "pdf.fonttype": 42})

S = json.load(open(os.path.join(ROOT, "out_runall_v3/summary.json")))["seeds"]
D = json.load(open(os.path.join(ROOT, "out_runall_v3/did_result.json")))
CSV = {('v3_' + r['name']): r for r in csv.DictReader(open(os.path.join(ROOT, 'v3_seeds/seeds_v3.csv')))}
OK = [r for r in S if r.get("beta") is not None]
LV = [r for r in S if r.get("mean_s") is not None]

def sentences():
    for f in glob.glob(os.path.join(ROOT, "seeds_data/scored2_v3_*.jsonl")):
        name = os.path.basename(f)[8:-6]; meta = CSV.get(name)
        if not meta: continue
        for L in open(f):
            try:
                o = json.loads(L)
                if o.get("assert") == 1 and o.get("s") is not None:
                    yield meta["arm"], o["year"], o["s"]
            except Exception: pass

def style(ax):
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", color=GRID, lw=.4, alpha=.7); ax.set_axisbelow(True)

def save(fig, name):
    fig.savefig(os.path.join(OUT, name + ".pdf")); fig.savefig(os.path.join(OUT, name + "_p.png"), dpi=140)
    plt.close(fig); print("✓", name)

def panel(ax, letter): ax.set_title(letter, loc="left", fontweight="bold", fontsize=10, pad=6)

# ---------------- Fig 1: 设计 + 量尺 + 修辞面貌 ----------------
def fig1():
    fig = plt.figure(figsize=(7.2, 2.9))
    gs = fig.add_gridspec(1, 3, width_ratios=[1.05, 1.5, 1.15], wspace=.42)
    # A 流程
    ax = fig.add_subplot(gs[0]); panel(ax, "A")
    steps = [("135 original studies", "3 registered replication projects"),
             ("110 claims resolved", "68 refuted / 42 robust"),
             ("15,467 citing sentences", "dated, 1993–2026"),
             ("8,598 assertion sentences", "restate the claim itself"),
             ("85 / 73 claims analyzed", "trend / event analysis")]
    for i, (t1, t2) in enumerate(steps):
        y = 1 - i * .21
        ax.add_patch(FancyBboxPatch((.02, y - .13), .96, .15, boxstyle="round,pad=0.012",
                                    fc="#eef3f8" if i % 2 == 0 else "#fdf1e7", ec=MUTED, lw=.6))
        ax.text(.5, y - .035, t1, ha="center", fontsize=6.6, fontweight="bold", color=INK)
        ax.text(.5, y - .095, t2, ha="center", fontsize=5.8, color=MUTED)
        if i < 4: ax.annotate("", xy=(.5, y - .155), xytext=(.5, y - .128),
                              arrowprops=dict(arrowstyle="-|>", lw=.7, color=MUTED))
    ax.set_xlim(0, 1); ax.set_ylim(-.05, 1.03); ax.axis("off")
    # B 量尺 + 例句
    ax = fig.add_subplot(gs[1]); panel(ax, "B")
    exs = [(0.0, "People might feel farther away from future events with potential negative than positive implications."),
           (0.5, "Recalling failures versus achievements has been shown to alter subjective distance to earlier selves."),
           (1.0, "People who expect to own a good in the future exhibit signs of psychological ownership for it.")]
    ax.axhspan(-.5, .5, xmin=0, xmax=1, color="none")
    for s0, txt in exs:
        ax.scatter(s0, 0, s=46, color=INK, zorder=3, marker="v")
        w = "\n".join(textwrap.wrap(f"“{txt}”", 34))
        ax.annotate(w, xy=(s0, 0), xytext=(s0, -.55 if s0 != 0.5 else .62),
                    ha="center", va="top" if s0 != 0.5 else "bottom", fontsize=5.6, color=MUTED,
                    arrowprops=dict(arrowstyle="-", lw=.5, color=GRID))
    grad = [plt.cm.Blues(.25 + .6 * i / 99) for i in range(100)]
    for i, c in enumerate(grad): ax.axvspan(i / 100, (i + 1) / 100, ymin=.47, ymax=.53, color=c, lw=0)
    for x, lab in ((0, "0\nfully hedged"), (.5, "0.5\nneutral"), (1, "1\ndefinitive / causal")):
        ax.text(x, .28, lab, ha="center", fontsize=6.2, color=INK)
    ax.set_xlim(-.09, 1.09); ax.set_ylim(-1.35, 1.15); ax.axis("off")
    ax.text(.5, 1.06, "Stated certainty $s$", ha="center", fontsize=7.2, color=INK)
    # C 修辞面貌
    ax = fig.add_subplot(gs[2]); panel(ax, "C")
    allS = [s for _, _, s in sentences()]
    ax.hist(allS, bins=21, color="#6baed6", edgecolor="white", lw=.4)
    ax.axvspan(.75, 1.001, color=VERM, alpha=.10); ax.axvspan(-.001, .25, color="#999999", alpha=.12)
    n = len(allS)
    ax.text(.875, ax.get_ylim()[1] * .93, f"definitive\n{sum(1 for s in allS if s>=.75)/n*100:.0f}%",
            ha="center", fontsize=6.2, color=VERM)
    ax.text(.11, ax.get_ylim()[1] * .93, f"cautious\n{sum(1 for s in allS if s<=.25)/n*100:.0f}%",
            ha="center", fontsize=6.2, color=MUTED)
    ax.set_xlabel("Stated certainty $s$"); ax.set_ylabel("Sentences"); style(ax)
    fig.subplots_adjust(left=.03, right=.985, top=.88, bottom=.16)
    save(fig, "fig1_design")

# ---------------- Fig 2: 水平 null ----------------
def fig2():
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(6.4, 2.6), gridspec_kw={'width_ratios': [1, 1.25]})
    panel(a1, "A")
    random.seed(5)
    for j, (arm, c) in enumerate((("refuted", VERM), ("robust", BLUE))):
        vs = [r["mean_s"] for r in LV if r["arm"] == arm]
        xs = [j + random.uniform(-.16, .16) for _ in vs]
        a1.scatter(xs, vs, s=13, color=c, alpha=.6, edgecolors="none")
        m = statistics.mean(vs); a1.hlines(m, j - .26, j + .26, color=c, lw=2.2)
        a1.text(j + .3, m, f"{m:.3f}", va="center", fontsize=6.6, color=c)
    a1.set_xticks([0, 1]); a1.set_xticklabels(["Refuted\n(n=60)", "Robust\n(n=39)"])
    a1.set_ylabel("Mean stated certainty per claim"); a1.set_xlim(-.5, 1.75); style(a1)
    panel(a2, "B")
    for arm, c, ls in (("refuted", VERM, "-"), ("robust", BLUE, "--")):
        vs = sorted(s for a, _, s in sentences() if a == arm)
        ys = [i / len(vs) for i in range(len(vs))]
        a2.plot(vs, ys, color=c, ls=ls, lw=1.5, label=f"{arm.capitalize()} ({len(vs):,} sentences)")
    a2.set_xlabel("Stated certainty $s$"); a2.set_ylabel("Cumulative fraction")
    a2.legend(frameon=False, fontsize=6.4, loc="upper left"); style(a2)
    fig.tight_layout(); save(fig, "fig2_levels")

# ---------------- Fig 3: 漂移 null ----------------
def fig3():
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(6.4, 2.6), gridspec_kw={'width_ratios': [1.25, 1]})
    panel(a1, "A"); random.seed(6)
    for j, (arm, c, mk) in enumerate((("refuted", VERM, "D"), ("robust", BLUE, "o"))):
        vs = [r["beta"] for r in OK if r["arm"] == arm]
        ys = [j + random.uniform(-.14, .14) for _ in vs]
        a1.scatter(vs, ys, s=13, marker=mk, color=c, alpha=.6, edgecolors="none")
        m = statistics.mean(vs); a1.vlines(m, j - .26, j + .26, color=c, lw=2.2)
    a1.axvline(0, color=GRID, lw=.8)
    a1.set_yticks([0, 1]); a1.set_yticklabels(["Refuted\n(n=51)", "Robust\n(n=34)"])
    a1.set_xlabel("Certainty drift $\\beta$ (per year)")
    a1.text(.02, .95, "group difference $+$0.003\n95% CI [$-$0.004, $+$0.010]",
            transform=a1.transAxes, fontsize=6.2, va="top", color=MUTED)
    a1.spines[["top", "right"]].set_visible(False); a1.grid(axis="x", color=GRID, lw=.4, alpha=.7); a1.set_axisbelow(True)
    panel(a2, "B")
    for r in OK:
        pr = CSV.get(r["name"], {}).get("p_rep")
        try: pr = float(pr)
        except Exception: continue
        a2.scatter(min(pr, 1), r["beta"], s=13, marker="D" if r["arm"] == "refuted" else "o",
                   color=VERM if r["arm"] == "refuted" else BLUE, alpha=.65, edgecolors="none")
    a2.axhline(0, color=GRID, lw=.8); a2.axvline(.05, color=INK, lw=.7, ls=":")
    a2.text(.07, a2.get_ylim()[1] * .88, "replication\n$p=0.05$", fontsize=5.8, color=MUTED)
    a2.set_xlabel("Replication $p$-value"); a2.set_ylabel("$\\beta$"); style(a2)
    fig.tight_layout(); save(fig, "fig3_drift")

# ---------------- Fig 4: 事件研究 ----------------
def fig4():
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(6.8, 2.7), gridspec_kw={'width_ratios': [1.6, 1]})
    panel(a1, "A")
    for arm, c in (("refuted", VERM), ("robust", BLUE)):
        pts = sorted((int(t), v[0], v[1]) for t, v in D["event_study"][arm].items())
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        se = [.28 / math.sqrt(p[2]) for p in pts]
        a1.fill_between(xs, [y - 1.96 * e for y, e in zip(ys, se)], [y + 1.96 * e for y, e in zip(ys, se)],
                        color=c, alpha=.14, lw=0)
        a1.plot(xs, ys, color=c, lw=1.5, marker="o" if arm == "robust" else "D", markersize=3.4,
                label=arm.capitalize())
    a1.axvline(0, color=INK, lw=.8, ls="--"); a1.axhline(0, color=GRID, lw=.8)
    a1.annotate("replication published", xy=(0, .075), xytext=(1.2, .082), fontsize=6,
                arrowprops=dict(arrowstyle="-", lw=.5, color=INK), va="center", color=INK)
    a1.set_ylim(-.09, .1)
    a1.set_xlabel("Years relative to replication publication")
    a1.set_ylabel("Stated certainty (claim-demeaned)")
    a1.legend(frameon=False, fontsize=6.4, loc="lower left"); style(a1)
    # B: DiD 总 + 分项目(项目内自举)
    panel(a2, "B")
    import copy
    def proj_of(m):
        j = str(m.get('journal', '')).lower()
        return 'EERP' if ('economic' in j or 'qje' in j) else ('SSRP' if ('science' in j or 'nature' in j) else 'RPP')
    def ry_of(m):
        return {'EERP': 2016, 'SSRP': 2018, 'RPP': 2015}[proj_of(m)]
    cl = {}
    for f in glob.glob(os.path.join(ROOT, "seeds_data/scored2_v3_*.jsonl")):
        name = os.path.basename(f)[8:-6]; m = CSV.get(name)
        if not m: continue
        ry = ry_of(m); pre, post = [], []
        for L in open(f):
            try:
                o = json.loads(L)
                if o.get("assert") == 1 and o.get("s") is not None and o.get("year"):
                    (pre if o["year"] < ry else post).append(o["s"])
            except Exception: pass
        if len(pre) >= 10 and len(post) >= 10:
            cl[name] = (m["arm"], proj_of(m), statistics.mean(post) - statistics.mean(pre))
    def did(names):
        dR = [cl[n][2] for n in names if cl[n][0] == "refuted"]
        dB = [cl[n][2] for n in names if cl[n][0] == "robust"]
        return statistics.mean(dR) - statistics.mean(dB) if dR and dB else None
    random.seed(11)
    rows = []
    for lab, pool in (("Pooled", list(cl)), ("Psychology", [n for n in cl if cl[n][1] == "RPP"]),
                      ("Economics", [n for n in cl if cl[n][1] == "EERP"])):
        R = [n for n in pool if cl[n][0] == "refuted"]; B = [n for n in pool if cl[n][0] == "robust"]
        if len(R) < 3 or len(B) < 3: continue
        bs = []
        for _ in range(999):
            samp = random.choices(R, k=len(R)) + random.choices(B, k=len(B))
            v = did(samp)
            if v is not None: bs.append(v)
        bs.sort(); rows.append((lab, did(pool), bs[int(.025 * len(bs))], bs[int(.975 * len(bs))]))
    for i, (lab, m, lo, hi) in enumerate(rows):
        y = len(rows) - 1 - i
        a2.plot([lo, hi], [y, y], color=INK, lw=1.1)
        a2.scatter(m, y, s=26, color=INK, zorder=3)
        a2.text(-.128, y, lab, ha="left", va="center", fontsize=6.6)
    a2.axvline(0, color=GRID, lw=.9)
    a2.set_yticks([]); a2.set_xlim(-.13, .13)
    a2.set_xlabel("Difference-in-differences (95% CI)")
    a2.spines[["top", "right", "left"]].set_visible(False)
    a2.grid(axis="x", color=GRID, lw=.4, alpha=.7); a2.set_axisbelow(True)
    fig.tight_layout(); save(fig, "fig4_event")

# ---------------- Fig 5: 沉默 ----------------
def fig5():
    ack = json.load(open(os.path.join(ROOT, "out_runall_v3/ack_rate_modelB.json")))
    rate = sum(a for _, a in ack) / len(ack)
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(5.8, 2.5), gridspec_kw={'width_ratios': [1, 1.05]})
    panel(a1, "A")
    a1.bar([0, 1], [1 - rate, rate], color=["#999999", VERM], width=.6)
    n = len(ack); k = sum(a for _, a in ack)
    lo = (k / n) - 1.96 * math.sqrt(k / n * (1 - k / n) / n); hi = (k / n) + 1.96 * math.sqrt(k / n * (1 - k / n) / n)
    a1.errorbar(1, rate, yerr=[[rate - max(lo, 0)], [hi - rate]], color=INK, capsize=3, lw=1)
    for x, v in ((0, 1 - rate), (1, rate)): a1.text(x, v + .04, f"{v*100:.1f}%", ha="center", fontsize=7.4, fontweight="bold")
    a1.set_xticks([0, 1]); a1.set_xticklabels(["Cited as valid,\nfailure unmentioned", "Mentions failure\nor controversy"], fontsize=6.4)
    a1.set_ylabel("Post-refutation restating\nsentences ($n=150$)"); a1.set_ylim(0, 1.14); style(a1)
    panel(a2, "B")
    # 承认 vs 沉默句的确定性
    key = {}
    rows = list(csv.reader(open(os.path.join(ROOT, 'annotation_package/task_B_sentences.csv'), encoding='utf-8-sig')))[1:]
    keyB = {r[0]: r[1] for r in rows}
    s_of = {}
    for f in glob.glob(os.path.join(ROOT, "seeds_data/scored2_v3_*.jsonl")):
        for L in open(f):
            try:
                o = json.loads(L)
                if o.get("s") is not None: s_of[o["ctx"][:80]] = o["s"]
            except Exception: pass
    grp = {0: [], 1: []}
    for rid, a in ack:
        v = s_of.get(keyB.get(rid, "")[:80])
        if v is not None: grp[a].append(v)
    random.seed(8)
    for j, (g, c, lab) in enumerate(((grp[0], "#999999", f"silent (n={len(grp[0])})"), (grp[1], VERM, f"acknowledging (n={len(grp[1])})"))):
        xs = [j + random.uniform(-.13, .13) for _ in g]
        a2.scatter(xs, g, s=14, color=c, alpha=.65, edgecolors="none")
        m = statistics.mean(g); a2.hlines(m, j - .24, j + .24, color=c, lw=2.2)
        a2.text(j + .28, m, f"{m:.2f}", va="center", fontsize=6.6, color=c)
    a2.set_xticks([0, 1]); a2.set_xticklabels(["Failure\nunmentioned", "Failure\nmentioned"], fontsize=6.4)
    a2.set_ylabel("Stated certainty $s$"); a2.set_xlim(-.5, 1.75); style(a2)
    fig.tight_layout(); save(fig, "fig5_silence")

if __name__ == "__main__":
    for f in (fig1, fig2, fig3, fig4, fig5):
        try: f()
        except Exception as e:
            import traceback; traceback.print_exc()
